import sys
import pyglet
import pyglet.window
#from PyQt5 import QtGui
#from PyQt5 import QtCore, QtWidgets
#from PyQt5.QtOpenGL import QGLWidget as OpenGLWidget
from PyQt6 import QtGui
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtOpenGLWidgets import QOpenGLWidget as OpenGLWidget
from pyglet.gl import glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
import random
import numpy as np


"""An example showing how to use pyglet in QT, utilizing the OGLWidget.

   Since this relies on the QT Window, any events called on Pyglet Window
   will NOT be called.

   This includes mouse, keyboard, tablet, and anything else relating to the Window
   itself. These must be handled by QT itself.

   This just allows user to create and use pyglet related things such as sprites, shapes,
   batches, clock scheduling, sound, etc.
"""

class MainWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Pyglet and QT Example")
        self.shapes = []
        self.my_size = 512
        width, height = self.my_size, self.my_size
        self.opengl = PygletWidget(width, height)
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.opengl)
        self.setLayout(mainLayout)


class PygletWidget(OpenGLWidget):
    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.setMinimumSize(width, height)
        self.my_size = width
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._pyglet_update)
        self.timer.setInterval(50)
        self.timer.start()
        # pyglet.clock.schedule_interval(self._pyglet_update, 1/60)

    def _pyglet_update(self):
        # Tick the pyglet clock, so scheduled events can work.
        print("update")
        pyglet.clock.tick()
        size = self.my_size
        array = np.random.randint(0, 255, (10, size, size, 3), dtype=np.uint8)


        pImg = pyglet.image.ImageData(size,size,'RGB',np.ctypeslib.as_ctypes(array[0].ravel())
                                      ,pitch=size*3)

        sprite = pyglet.sprite.Sprite(img=pImg)
        # pImg.create_texture()
        pImg.blit(255, 255)
        sprite.draw()
        self.update() # self.updateGL() for pyqt5

    def initializeGL(self):
        """Call anything that needs a context to be created."""
        self.batch = pyglet.graphics.Batch()
        size = self.size()
        w, h = size.width(), size.height()
        from pyglet.math import Mat4
        self.projection = Mat4.orthogonal_projection(0, w, 0, h, -255, 255)




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    ui = MainWidget(window)
    ui.show()  # Calls initializeGL. Do not do any GL stuff before this is called.
    app.exec() # exec_ in 5.
