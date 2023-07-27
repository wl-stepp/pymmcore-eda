from vispy import app, scene
from pymmcore_plus import CMMCorePlus
from useq import MDASequence
import sys
from qtpy import QtWidgets, QtCore

import tifffile
from pymmcore_widgets import MDAWidget
import numpy as np
import copy


app.use_app("pyqt6")

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

from pymmcore_plus._logger import logger as mmlog
mmlog.level('TRACE')

DIMENSIONS = ["c", "z", "t", "p", "g"]


class Canvas(QtWidgets.QWidget):
    """A canvas to follow MDA acquisitions"""
    _slider_settings = QtCore.Signal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._clim = 'auto'

        self.array = None
        self.display_index = {dim: 0 for dim in DIMENSIONS}

        self.setLayout(QtWidgets.QVBoxLayout())
        self.construct_canvas()
        self.layout().addWidget(self._canvas.native)
        self._create_sliders()
        self.save_button = QtWidgets.QPushButton("Save")
        self.layout().addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_array)

        mmcore.mda.events.frameReady.connect(self.new_frame)
        mmcore.mda.events.sequenceStarted.connect(self.on_sequence_start)

    def construct_canvas(self):
        self._clims = "auto"
        self._canvas = scene.SceneCanvas(keys="interactive", size=(512, 512), parent=self)
        self._canvas.show()
        self.view = self._canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.flip = (0, 1, 0)
        self.view.camera.set_range()
        self.image : scene.visuals.Image / None = None
        self.image2 : scene.visuals.Image / None = None

    def on_sequence_start(self, sequence: MDASequence):
        self.array = self._array_for_sequence(sequence)
        self.handle_sliders(self.array)
        self.handle_channels(sequence, self.array)

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

    def handle_sliders(self, array: np.ndarray):
        for dim in DIMENSIONS[:3]:
            if array.shape[DIMENSIONS.index(dim) + 2] > 1:
                self._slider_settings.emit({"index": dim,
                                            "show": True,
                                            "max": array.shape[DIMENSIONS.index(dim) + 2] - 1})
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

    def _array_for_sequence(self, sequence: MDASequence):
        "Construct a numpy array to hold the data for the sequence"
        exp_shape = sequence.sizes
        dt = mmcore.getImageBitDepth()
        dt = np.uint16 if dt == 16 else print("WARNING: bit depth not supported")
        width = mmcore.getImageWidth()
        height = mmcore.getImageHeight()
        return np.zeros([width,
                        height,
                        max(exp_shape['c'], 1),
                        max(exp_shape['z'], 1),
                        max(exp_shape['t'], 1)]).astype(dt)

    def on_slider_change(self, value, index):
        self.display_index[index] = value
        for c in range(self.array.shape[2]):
            self.display_image(self.array[:, :,
                                        c,
                                        self.display_index['z'],
                                        self.display_index['t']],
                              c)

    def new_frame(self, img: np.ndarray, event):
        if sum(event.index.values()) == 0:
            self.view.camera.set_range(margin=0)
        indices = self.complement_indices(event)
        self.array[:, :, indices["c"], indices["z"], indices["t"]] = img
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

    def complement_indices(self, event):
        indeces = dict(copy.deepcopy(event.index))
        for i in DIMENSIONS:
            if i not in indeces:
                indeces[i] = 0
        return indeces

    def save_array(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self, 'Open file',
        'c:\\',"TIF files (*.tif)")
        tifffile.imwrite(fname[0],
                         np.moveaxis(self.array, [0, 1, 2, 3, 4], [3, 4, 2, 1, 0]),
                         imagej=True)


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

if __name__ == "__main__":
    gui = QtWidgets.QApplication(sys.argv)
    w =Canvas()
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