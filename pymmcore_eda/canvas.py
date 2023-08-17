from vispy import app, scene
from pymmcore_plus import CMMCorePlus
from useq import MDASequence, Channel
import sys
from qtpy import QtWidgets, QtCore

from event_receiver import QEventConsumer, QEventReceiver
import numpy as np
import copy
import time
from pathlib import Path
from event_bus import EventBus
from datastore import DataStore
from pymmcore_eda.utility.index_slider import QLabeledSlider
from pymmcore_eda.utility.range_slider import RangeSlider


app.use_app("pyqt6")

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

DIMENSIONS = ["c", "z", "t", "p", "g"]


class Canvas(QEventConsumer):
    """A canvas to follow MDA acquisitions"""
    _slider_settings = QtCore.Signal(dict)
    _new_channel = QtCore.Signal(int, str)

    def __init__(self, event_receiver: QEventReceiver|EventBus|None = None, *args, **kwargs):
        super().__init__(event_receiver)

        self._clim = 'auto'
        self.display_index = {dim: 0 for dim in DIMENSIONS}

        self.setLayout(QtWidgets.QVBoxLayout())
        self.construct_canvas()
        self.layout().addWidget(self._canvas.native)

        self.info_bar = QtWidgets.QLabel()
        self.info_bar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.layout().addWidget(self.info_bar)

        self._create_sliders()
        self.listener.sequence_started.connect(self.on_sequence_start)
        self.listener.frame_ready.connect(self.on_frame_ready)

        self._new_channel.connect(self._handle_chbox_visibility)
        self.images = []

    def construct_canvas(self):
        self._clims = "auto"
        self._canvas = scene.SceneCanvas(keys="interactive", size=(512, 512), parent=self)
        self._canvas._send_hover_events = True
        self._canvas.events.mouse_move.connect(self.on_mouse_move)
        self.view = self._canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.flip = (0, 1, 0)
        self.view.camera.set_range()
        self._canvas.show()

    def on_sequence_start(self, sequence: MDASequence):
        self.sequence = sequence
        self.handle_sliders(sequence)
        self.handle_channels(sequence, self.datastore)
        self.view.camera.rect = ((0, 0, 512, 512))

    def handle_channels(self, sequence: MDASequence, array: np.ndarray):
        nc = sequence.sizes['c']
        self.images = []
        cmaps = ['reds', 'cool', 'viridis']
        for i in range(nc):
            image = scene.visuals.Image(np.zeros(self._canvas.size).astype(array.dtype),
                                        parent=self.view.scene, cmap=cmaps[i], clim=[0,1])
            image.set_gl_state(preset="additive")
            self.images.append(image)
            self.current_channel = i
            self._new_channel.emit(i, sequence.channels[i].config)

    def _handle_chbox_visibility(self, i: int, name: str):
        self.channel_boxes[i].show()
        self.channel_boxes[i].show_channel.setText(name)
        self.channel_boxes[i].channel = name
        self.channel_boxes[i].mousePressEvent(None)

    def _handle_channel_choice(self, channel: str):
        for idx, channel_box in enumerate(self.channel_boxes):
            if channel_box.channel != channel:
                channel_box.setStyleSheet("ChannelBox{border: 1px solid}")
            else:
                self.current_channel = idx

    def _handle_channel_clim(self, low, high, channel: int, set_autoscale=True):
        self.images[channel].clim = (low, high)
        if self.channel_boxes[channel].autoscale.isChecked() and set_autoscale:
            self.channel_boxes[channel].autoscale.setCheckState(QtCore.Qt.Unchecked)
        self._canvas.update()

    def _handle_channel_visibility(self, state, channel: int):
        self.images[channel].visible = self.channel_boxes[channel].show_channel.isChecked()
        self._canvas.update()

    def _handle_channel_autoscale(self, state, channel: int):
        if state == 0:
            slider = self.channel_boxes[channel].slider
            self._handle_channel_clim(slider.low(), slider.high(), channel, set_autoscale=False)
        else:
            clim = (np.min(self.images[channel]._data), np.max(self.images[channel]._data))
            self._handle_channel_clim(clim[0], clim[1], channel, set_autoscale=False)

    def handle_sliders(self, sequence: MDASequence):
        for dim in DIMENSIONS[:3]:
            if sequence.sizes[dim] > 1:
                self._slider_settings.emit({"index": dim,
                                            "show": True,
                                            "max": sequence.sizes[dim] - 1})
            else:
                self._slider_settings.emit({"index": dim,
                                            "show": False,
                                            "max": 1})

    def _create_sliders(self,):
        self.sliders = []
        for dim in DIMENSIONS:
            if dim == 'c':
                self.channel_row = QtWidgets.QWidget()
                self.channel_row.setLayout(QtWidgets.QHBoxLayout())
                self.channel_row.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                               QtWidgets.QSizePolicy.Fixed)
                self.layout().addWidget(self.channel_row)
                continue
            slider = LabeledVisibilitySlider(dim,  orientation=QtCore.Qt.Horizontal)
            slider.valueChanged[int, str].connect(self.on_slider_change)
            self._slider_settings.connect(slider._visibility)
            self.layout().addWidget(slider)
            slider.hide()
            self.sliders.append(slider)

        self.channel_boxes = []
        for i in range(5):
            channel_box = ChannelBox(Channel(config="empty"))
            channel_box.show_channel.stateChanged.connect(lambda state, i=i: self._handle_channel_visibility(state, i))
            channel_box.autoscale.stateChanged.connect(lambda state, i=i: self._handle_channel_autoscale(state, i))
            channel_box.slider.sliderMoved.connect(lambda low, high, i=i: self._handle_channel_clim(low, high, i))
            channel_box.clicked.connect(self._handle_channel_choice)
            channel_box.mousePressEvent(None)
            channel_box.hide()
            self.current_channel = i
            self.channel_boxes.append(channel_box)
            self.channel_row.layout().addWidget(channel_box)

    def on_mouse_move(self, event):
        transform = self.images[self.current_channel].get_transform('canvas', 'visual')
        p = [int(x) for x in transform.map(event.pos)]
        if p[0] < 0 or p[1] < 0:
            info = f"[{p[0]}, {p[1]}]"
            self.info_bar.setText(info)
            return
        try:
            info = f"[{p[0]}, {p[1]}] = {self.images[self.current_channel]._data[p[1], p[0]]}"
            self.info_bar.setText(info)
        except IndexError:
            info = f"[{p[0]}, {p[1]}]"
            self.info_bar.setText(info)
            pass

    def on_slider_change(self, value, index):
        self.display_index[index] = value
        for c in range(self.sequence.sizes['c']):
            frame = self.datastore.get_frame(self.width, self.height,
                                                    (self.width * self.height * max(1,c) *
                                                     max(1, self.display_index['z']) *
                                                     max(1, self.display_index['t'])))
            self.display_image(frame, c)

    def on_frame_ready(self, buffer_pos: int, shape: tuple, index):
        self.width, self.height = shape
        indices = self.complement_indices(index)
        img = self.datastore.get_frame(shape[0], shape[1], buffer_pos)
        self.display_image(img, indices["c"])
        self._set_sliders(indices)
        print("Checkpoint")
        slider = self.channel_boxes[indices["c"]].slider
        slider.setRange(min(slider.minimum(), img.min()), max(slider.maximum(), img.max()))
        if self.channel_boxes[indices["c"]].autoscale.isChecked():
            slider.setLow(min(slider.minimum(), img.min()))
            slider.setHigh(max(slider.maximum(), img.max()))

    def _set_sliders(self, indices: dict):
        for slider in self.sliders:
            slider.blockSignals(True)
            slider.setValue(indices[slider.name])
            slider.blockSignals(False)

    def display_image(self, img: [scene.visuals.Image], channel=0):
        self.images[channel].set_data(img)
        if self.channel_boxes[channel].autoscale.isChecked():
            clim = (np.min(img), np.max(img))
            self.images[channel].clim = clim
            # else:
            # clim = (self.channel_boxes[channel].slider.low(), self.channel_boxes[channel].slider.high())
        self._canvas.update()

    def complement_indices(self, index):
        indeces = dict(copy.deepcopy(dict(index)))
        for i in DIMENSIONS:
            if i not in indeces:
                indeces[i] = 0
        return indeces


class LabeledVisibilitySlider(QLabeledSlider):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def _visibility(self, settings):
        if not settings['index'] == self.name:
            return
        if settings['show']:
            self.show()
        else:
            self.hide()
        self.setRange(0, settings['max'])

class ChannelBox(QtWidgets.QFrame):
    """Box that represents a channel and gives some way of interaction."""

    clicked = QtCore.Signal(str)

    def __init__(self, channel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = channel.config
        self.setLayout(QtWidgets.QGridLayout())
        self.show_channel = QtWidgets.QCheckBox(channel.config)
        self.show_channel.setChecked(True)
        self.show_channel.setStyleSheet("font-weight: bold")
        self.layout().addWidget(self.show_channel, 0, 0)
        self.autoscale = QtWidgets.QCheckBox("Auto")
        self.autoscale.setChecked(True)
        self.layout().addWidget(self.autoscale, 0, 1)
        self.slider = RangeSlider(QtCore.Qt.Horizontal)
        self.layout().addWidget(self.slider, 1, 0, 1, 2)
        self.setStyleSheet("ChannelBox{border: 1px solid}")

    def mousePressEvent(self, event):
        self.setStyleSheet("ChannelBox{border: 3px solid}")
        self.clicked.emit(self.channel)



if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    datastore = DataStore(name="canvas")
    event_bus = EventBus(datastore)
    w = Canvas(event_bus)
    w.show()
    # mmcore.setExposure(100)
    # w.setFixedSize(1024, 1024)
    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 10}, {"config": "DAPI", "exposure": 10}, {"config": "Cy5", "exposure": 10}],
    time_plan={"interval": 1, "loops": 3},
    # z_plan={"range": 2, "step": 1},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
    sys.exit(app.exec_())