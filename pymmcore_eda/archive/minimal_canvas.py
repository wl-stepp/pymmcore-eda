import sys
from vispy import scene
from vispy import app, color
import numpy as np
from qtpy import QtWidgets, QtCore

SIZE = 2048
FRAMES = 40

import time

from pymmcore_eda.local_datastore import QLocalDataStore
import copy
# Set up a viewbox to display the image with interactive pan/zoom


# Create the image

# Set 2D camera (the camera will scale to the contents in the scene)

# view.camera.zoom(0.1, (2048, 2048))
class Canvas(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.datastore = QLocalDataStore([FRAMES, 2, 1, SIZE, SIZE])
        self.canvas = scene.SceneCanvas(keys='interactive')
        self.canvas.size = (2048, 2048)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        # flip y-axis to have correct aligment
        self.view.camera.flip = (0, 1, 0)


        self.img_data = np.zeros((FRAMES, 2, 1, SIZE, SIZE)).astype(np.uint16)
        self.image = scene.visuals.Image(self.img_data[0, 0, 0, :, :], interpolation='linear',
                            parent=self.view.scene, method='subdivide', cmap=color.Colormap([[0, 0, 0], [1, 1, 0]]), clim=(0,500))
        self.image2 = scene.visuals.Image(self.img_data[0, 1, 0, :, :], interpolation='linear',
                            parent=self.view.scene, method='subdivide', cmap=color.Colormap([[0, 0, 0], [0, 1, 1]]), clim=(0, 500))
        self.image2.set_gl_state('additive', depth_test=False)
        self.view.camera.set_range()
        self.timer = app.Timer()
        self.timer.connect(self.on_timer)

        self.frame = 0
        self.t0 = time.perf_counter()

        self.play_btn = QtWidgets.QPushButton("play")
        self.layout().addWidget(self.play_btn)
        self.play_btn.clicked.connect(self.on_play)
        self.playing = False

    def on_play(self):
        # self.datastore.listener.quit()
        self.img_data = self.datastore.array
        if self.playing:
            self.timer.stop()
            self.play_btn.setText("play")
        else:
            self.timer.start(0.01)
            self.play_btn.setText("stop")
        self.playing = not self.playing


    def on_timer(self, event):
        print(round(1/(time.perf_counter()-self.t0)))
        self.t0 = time.perf_counter()
        # self.image.set_data(self.img_data[:, :,1, 0, self.frame % FRAMES])
        # self.image2.set_data(self.img_data[:, :,0, 0, self.frame % FRAMES])
        self.image.set_data(self.img_data[self.frame % FRAMES, 1, 0, :, :])
        self.image2.set_data(self.img_data[self.frame % FRAMES, 0, 0, :, :])
        self.frame += 1
        self.canvas.update()





if __name__ == '__main__' and sys.flags.interactive == 0:
    qt_app = QtWidgets.QApplication(sys.argv)
    canvas = Canvas()
    canvas.show()
    from useq import MDASequence
    from pymmcore_plus import CMMCorePlus
    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 1}, {"config": "DAPI", "exposure": 1}],
    time_plan={"interval": 0.3, "loops": 40},)
    mmcore = CMMCorePlus.instance()
    mmcore.loadSystemConfiguration()
    mmcore.setProperty("Camera", "OnCameraCCDXSize", SIZE)
    mmcore.setProperty("Camera", "OnCameraCCDYSize", SIZE)
    mmcore.run_mda(sequence)

    qt_app.exec_()