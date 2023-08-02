from vispy import app, scene
from pymmcore_plus import CMMCorePlus
from useq import MDASequence
import sys
from qtpy import QtWidgets, QtCore
from event_receiver import QEventConsumer, QEventReceiver
import numpy as np
import copy
import time
from pathlib import Path
from event_bus import EventBus
from datastore import DataStore

app.use_app("pyqt6")

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

DIMENSIONS = ["c", "z", "t", "p", "g"]


class Canvas(QEventConsumer):
    """A canvas to follow MDA acquisitions"""
    _slider_settings = QtCore.Signal(dict)

    def __init__(self, event_receiver: QEventReceiver|None = None, *args, **kwargs):
        super().__init__(event_receiver)

        self._clim = 'auto'
        self.display_index = {dim: 0 for dim in DIMENSIONS}

        self.setLayout(QtWidgets.QVBoxLayout())
        self.construct_canvas()
        self.layout().addWidget(self._canvas.native)

        self.info_bar = QtWidgets.QLabel()
        self.layout().addWidget(self.info_bar)

        self._create_sliders()
        self.listener.sequence_started.connect(self.on_sequence_start)
        self.listener.frame_ready.connect(self.on_frame_ready)

    def construct_canvas(self):
        self._clims = "auto"
        self._canvas = scene.SceneCanvas(keys="interactive", size=(512, 512), parent=self)
        self._canvas._send_hover_events = True
        self._canvas.events.mouse_move.connect(self.on_mouse_move)
        self._canvas.show()
        self.view = self._canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.flip = (0, 1, 0)
        self.view.camera.set_range()
        self.image : scene.visuals.Image / None = None

    def on_sequence_start(self, sequence: MDASequence):
        self.width = mmcore.getImageWidth()
        self.height = mmcore.getImageHeight()
        self.sequence = sequence
        self.handle_sliders(sequence)
        self.handle_channels(sequence, self.datastore)
        self.view.camera.rect = ((0, 0, self.width, self.height))

    def handle_channels(self, sequence: MDASequence, array: np.ndarray):
        nc = sequence.sizes['c']
        self.images = []
        cmaps = ['reds', 'cool', 'viridis']
        for i in range(nc):
            image = scene.visuals.Image(np.zeros([*array.shape[:2]]).astype(array.dtype),
                                        parent=self.view.scene, cmap=cmaps[i], clim=[0,1])
            image.set_gl_state(preset="additive")
            image.opacity = 0.5
            self.images.append(image)

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
            slider = IndexSlider(dim, QtCore.Qt.Horizontal)
            slider.valueChanged.connect(self.on_slider_change)
            self._slider_settings.connect(slider._visibility)
            self.layout().addWidget(slider)
            slider.hide()
            self.sliders.append(slider)

    def on_mouse_move(self, event):
        info = f"[{event.pos[0]}, {event.pos[1]}] = {self.images[0]._data[event.pos[1], event.pos[0]]}"
        self.info_bar.setText(info)

    # def _array_for_sequence(self, sequence: MDASequence):
    #     "Construct a numpy array to hold the data for the sequence"
    #     exp_shape = sequence.sizes
    #     dt = mmcore.getImageBitDepth()
    #     dt = np.uint16 if dt == 16 else print("WARNING: bit depth not supported")
    #     width = mmcore.getImageWidth()
    #     height = mmcore.getImageHeight()
    #     array =
    #     return np.zeros([width,
    #                     height,
    #                     max(exp_shape['c'], 1),
    #                     max(exp_shape['z'], 1),
    #                     max(exp_shape['t'], 1)]).astype(dt)

    def on_slider_change(self, value, index):
        self.display_index[index] = value
        for c in range(self.sequence.sizes['c']):
            frame = self.datastore.get_frame(self.width, self.height,
                                                    (self.width * self.height * max(1,c) *
                                                     max(1, self.display_index['z']) *
                                                     max(1, self.display_index['t'])))
            self.display_image(frame, c)

    def on_frame_ready(self, buffer_pos: int, shape: tuple, index):
        indices = self.complement_indices(index)
        img = self.datastore.get_frame(512, 512, buffer_pos)
        self.display_image(img, indices["c"])
        self._set_sliders(indices)

    def _set_sliders(self, indices: dict):
        for slider in self.sliders:
            slider.blockSignals(True)
            slider.setValue(indices[slider.index])
            slider.blockSignals(False)

    def display_image(self, img, channel=0):
        self.images[channel].set_data(img)
        if self._clim == 'auto':
            clim = (np.min(img), np.max(img))
        self.images[channel].clim = clim
        self._canvas.update()

    def complement_indices(self, index):
        indeces = dict(copy.deepcopy(index))
        for i in DIMENSIONS:
            if i not in indeces:
                indeces[i] = 0
        return indeces


class IndexSlider(QtWidgets.QSlider):
    """Slider that gets an index when created and transmits it when value changes."""
    valueChanged = QtCore.Signal(int, str)
    def __init__(self, index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        super().valueChanged.connect(self.orig_valueChanged)

    def orig_valueChanged(self, value):
        self.valueChanged.emit(value, self.index)

    def _visibility(self, settings):
        if not settings['index'] == self.index:
            return
        if settings['show']:
            self.show()
        else:
            self.hide()
        self.setRange(0, settings['max'])


class InfoBar(QtWidgets.QLabel):
    """Indicate information about the current position of sliders and mouse"""
    def __init__(self, datastore: DataStore, canvas: Canvas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText("InfoBar")




if __name__ == "__main__":
    gui = QtWidgets.QApplication(sys.argv)
    datastore = DataStore()
    event_bus = EventBus(datastore)

    # saver = Saver(event_bus)
    # saver.show()
    w = Canvas(event_bus)
    w.show()
    # mda = MDAWidget(include_run_button=True)
    # mda.show()
    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 10}, {"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 1, "loops": 5},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
    app.run()