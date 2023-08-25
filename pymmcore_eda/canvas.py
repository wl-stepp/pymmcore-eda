from vispy import app, scene, color, gloo
# from vispy.app import timer
from pymmcore_plus import CMMCorePlus
from useq import MDASequence, Channel
import sys
from qtpy import QtWidgets, QtCore, QtGui
import time

from pymmcore_eda.event_receiver import QEventConsumer, QEventReceiver
import numpy as np
import copy
from pymmcore_eda.archive.event_bus import EventBus

from pymmcore_eda.utility.index_slider import QLabeledSlider
from pymmcore_eda.utility.range_slider import RangeSlider
from pymmcore_eda.utility.color_picker import QColorComboBox


app.use_app("pyqt6")

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

DIMENSIONS = ["c", "z", "t", "p", "g"]
AUTOCLIM_RATE = 1 #Hz   0 = inf
CMAPS = [color.Colormap([[0, 0, 0], [1, 1, 0]]), color.Colormap([[0, 0, 0], [1, 0, 1]]),
         color.Colormap([[0, 0, 0], [0, 1, 1]]), color.Colormap([[0, 0, 0], [1, 0, 0]]),
         color.Colormap([[0, 0, 0], [0, 1, 0]]), color.Colormap([[0, 0, 0], [0, 0, 1]])]

class Canvas(QEventConsumer):
    """A canvas to follow MDA acquisitions started by MDASequence events. Works for remote and local
    datastores. QEventCosumer handles the connection to the correct events for each version."""
    _slider_settings = QtCore.Signal(dict)
    _new_channel = QtCore.Signal(int, str)

    def __init__(self, event_receiver: QEventReceiver|EventBus|None = None,
                 datastore = None, *args, **kwargs):
        super().__init__(event_receiver, datastore=datastore)
        self._clim = 'auto'
        self.display_index = {dim: 0 for dim in DIMENSIONS}

        self.setLayout(QtWidgets.QVBoxLayout())
        self.construct_canvas()
        self.layout().addWidget(self._canvas.native)

        self.info_bar = QtWidgets.QLabel()
        self.info_bar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.layout().addWidget(self.info_bar)

        self.play_timer = app.Timer()
        # self.play_timer.setInterval(20)
        self.play_timer.connect(self.on_play_timer)

        self._create_sliders()

        self.events.sequence_started.connect(self.on_sequence_start)
        self.events.frame_ready.connect(self.on_frame_ready)

        self._new_channel.connect(self._handle_chbox_visibility)
        self.images = []

        self.display_timer = app.Timer(interval=0.02, connect=self.on_display_timer)
        self.t0 = 0
        # self.display_timer.connect(self.on_display_timer)

        self.frame = 0

        self.clim_timer = QtCore.QTimer()
        self.clim_timer.setInterval(int(1000 // AUTOCLIM_RATE))
        self.clim_timer.timeout.connect(self.on_clim_timer)

    def construct_canvas(self):
        self._clims = "auto"
        self._canvas = scene.SceneCanvas( size=(512, 512), parent=self,
                                         autoswap=False, vsync=True, keys=None)
        # self._canvas.context.set_depth_func('lequal')
        self._canvas._send_hover_events = True
        self._canvas.events.mouse_move.connect(self.on_mouse_move)
        self.view = self._canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.flip = (0, 1, 0)
        self.view.camera.set_range()
        # self._canvas.show()

    def on_sequence_start(self, sequence: MDASequence):
        self.sequence = sequence
        self.handle_sliders(sequence)
        self.handle_channels(sequence, self.datastore)

    def handle_channels(self, sequence: MDASequence, array: np.ndarray):
        nc = sequence.sizes['c']
        print("CHANNEL", nc)
        self.images = []
        for i in range(nc):
            image = scene.visuals.Image(np.zeros(self._canvas.size).astype(array.dtype),
                                        parent=self.view.scene, cmap=CMAPS[i], clim=[0,1],
                                         interpolation="nearest")
            if i > 0:
                print("Image", i, "additive")
                image.set_gl_state('additive', depth_test=False)
            self.images.append(image)
            self.current_channel = i
            self._new_channel.emit(i, sequence.channels[i].config)

    def _handle_chbox_visibility(self, i: int, name: str):
        self.channel_boxes[i].show()
        self.channel_boxes[i].autoscale.setChecked(True)
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

    def _handle_channel_cmap(self, my_color, channel: int):
        my_color = [x//255 for x in my_color.getRgb()[:3]]
        self.images[channel].cmap = color.Colormap([[0, 0, 0], my_color])
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
            slider.valueChanged[int, str].connect(self.on_display_timer)
            slider.play.connect(self._start_play_timer)
            slider.sliderPressed.connect(self.on_slider_press)
            slider.sliderReleased.connect(self.on_slider_release)
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
            channel_box.color_choice.selectedColor.connect(lambda color, i=i: self._handle_channel_cmap(color, i))
            channel_box.color_choice.setColor(i)
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

    def on_slider_press(self):
        for slider in self.sliders:
            slider.valueChanged[int, str].disconnect()
        self.display_timer.start()
        self.clim_timer.start()

    def on_slider_release(self):
        self.display_timer.stop()
        self.clim_timer.stop()
        self.on_display_timer()
        self.on_clim_timer()
        for slider in self.sliders:
            slider.valueChanged[int, str].connect(self.on_display_timer)

    def on_display_timer(self, _=None):
        print(1/(time.perf_counter() - self.t0))
        self.t0 = time.perf_counter()
        old_index = self.display_index.copy()
        for slider in self.sliders:
            self.display_index[slider.name] = slider.value()
        if old_index == self.display_index:
            return

        for c in range(self.sequence.sizes['c']):
            frame = self.datastore.get_frame([self.display_index['t'], c, self.display_index['z']])

            self.display_image(frame, c)
        self.images[0].update()

    def _start_play_timer(self, playing):
        if playing:
            self.play_timer.start(0.01)
        else:
            self.play_timer.stop()


    def on_play_timer(self, _=None):
        print(1/(time.perf_counter() - self.t0))
        self.t0 = time.perf_counter()
        self.frame += 1
        self.frame = self.frame % self.sequence.sizes['t']
        # for c in range(self.sequence.sizes['c']):
        self.images[0].set_data(self.datastore.array[self.frame, 0, self.display_index['z'], :, : ])
        self.images[1].set_data(self.datastore.array[self.frame, 1, self.display_index['z'], :, : ])
        self._canvas.update()

    def on_frame_ready(self, event):
        indices = self.complement_indices(event.index)
        img = self.datastore.get_frame([indices["t"], indices["c"], indices["z"]])
        shape = img.shape
        self.width, self.height = shape
        if sum(indices.values()) == 0:
            self.view.camera.rect = ((0, 0, *shape))
        self.display_image(img, indices["c"])
        self._set_sliders(indices)
        slider = self.channel_boxes[indices["c"]].slider
        slider.setRange(min(slider.minimum(), img.min()), max(slider.maximum(), img.max()))
        if self.channel_boxes[indices["c"]].autoscale.isChecked():
            slider.setLow(min(slider.minimum(), img.min()))
            slider.setHigh(max(slider.maximum(), img.max()))
        self.on_clim_timer(indices["c"])

    def _set_sliders(self, indices: dict):
        for slider in self.sliders:
            slider.blockSignals(True)
            slider.setValue(indices[slider.name])
            slider.blockSignals(False)

    def display_image(self, img: np.ndarray, channel=0):
        self.images[channel].set_data(img)
        # self.images[channel].update()

    def on_clim_timer(self, channel=None):
        channel_list = list(range(len(self.channel_boxes))) if channel is None else [channel]
        for channel in channel_list:
            if self.channel_boxes[channel].autoscale.isChecked() and self.images[channel].visible:
                clim = np.percentile(self.images[channel]._data, [0, 100])
                self.images[channel].clim = clim

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
        self.color_choice = QColorComboBox()
        for cmap in CMAPS:
            self.color_choice.addColors([list(cmap.colors[-1].RGB[0])])

        # self.color_choice.setStyle(QtWidgets.QStyleFactory.create('fusion'))
        self.layout().addWidget(self.color_choice, 0, 1)
        self.autoscale = QtWidgets.QCheckBox("Auto")
        self.autoscale.setChecked(False)
        self.layout().addWidget(self.autoscale, 0, 2)
        self.slider = RangeSlider(QtCore.Qt.Horizontal)
        self.layout().addWidget(self.slider, 1, 0, 1, 3)
        self.setStyleSheet("ChannelBox{border: 1px solid}")

    def mousePressEvent(self, event):
        self.setStyleSheet("ChannelBox{border: 3px solid}")
        self.clicked.emit(self.channel)





if __name__ == "__main__":
    size = 2048
    from pymmcore_eda.local_datastore import QLocalDataStore

    mmcore.setProperty("Camera", "OnCameraCCDXSize", size)
    mmcore.setProperty("Camera", "OnCameraCCDYSize", size)
    mmcore.setProperty("Camera", "StripeWidth", 0.7)
    qapp = QtWidgets.QApplication(sys.argv)

    datastore = QLocalDataStore([40, 2, 1, size, size])
    w = Canvas(mmcore, datastore=datastore)
    w.show()

    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 1}, {"config": "DAPI", "exposure": 1}],
    time_plan={"interval": 0.5, "loops": 20},
    axis_order="tpcz", )


    mmcore.run_mda(sequence)
    qapp.exec_()
