"""
This module contains the definiton of a pyglet widget for a
PySide application: QPygletWidget
It also provides a basic usage example.
"""
import sys
import pyglet
pyglet.options['shadow_window'] = False
pyglet.options['debug_gl'] = False
from pyglet import gl
from qtpy import QtCore, QtOpenGLWidgets, QtWidgets
import numpy as np
import time
from OpenGL.GL import *

class QPygletWidget(QtOpenGLWidgets.QOpenGLWidget):
    """
    A simple pyglet widget.
    User can subclass this widget and implement the following methods:
        - on_init: called when open gl has been initialised
        - on_update: called every dt.
        - on_draw: called when paintGL is executed
        - on_resize: called when resizeGL is executed
    """

    update_me = QtCore.Signal()

    def __init__(self, parent=None,
                 clear_color=(0.0, 0.0, 0.0, 1.0),
                 frame_time=32,
                 dt=16):
        """
        :param clear_color: The widget clear color
        :type clear_color: tuple(r, g, b, a)
        :param frame_time: The desired frame time [ms]
        :type: frame_time: int
        :param dt: The desired update rate [ms]
        :type: dt: int
        """
        super().__init__()

        # init members
        self._clear_color = clear_color
        self._dt = dt
        self.update_timer = QtCore.QTimer()
        self.draw_timer = QtCore.QTimer()


        # configure draw and update timers
        self.update_timer.setInterval(dt)
        self.update_timer.timeout.connect(self._update)
        self.draw_timer.setInterval(frame_time)
        self.draw_timer.timeout.connect(self.update)

        # start timers
        self.update_timer.start()
        self.draw_timer.start()

    def _update(self):
        """
        Calls on_update with the choosen dt
        """
        self.on_update(self._dt)

    def on_init(self):
        """
        Lets the user initialise himself
        """
        pass

    def on_draw(self):
        """
        Lets the user draw his scene
        """
        pass

    def on_update(self, dt):
        """
        Lets the user draw his scene
        """
        self.paintGL()
        pass

    def on_resize(self, w, h):
        pass

    def initializeGL(self):
        """
        Initialises open gl:
            - create a mock context to fool pyglet
            - setup various opengl rule (only the clear color atm)
        """
        glEnable(GL_TEXTURE_2D)
        self.on_init()

    def resizeGL(self, w, h):
        """
        Resizes the gl camera to match the widget size.
        """
        self.on_resize(w, h)

    def paintGL(self, _=0):
        """
        Clears the back buffer than calls the on_draw method
        """
        print(round(1/(time.perf_counter()-self.t0)), self.frame)
        self.t0 = time.perf_counter()

        glClear(GL_COLOR_BUFFER_BIT)

        glEnable(GL_TEXTURE_2D)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.my_size, self.my_size, 0, GL_RGB, GL_UNSIGNED_BYTE,  np.ctypeslib.as_ctypes(self.array[self.frame].ravel()*self.frame))
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindTexture(GL_TEXTURE_2D, texture)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(-1, -1)
        glTexCoord2f(1, 0)
        glVertex2f(1, -1)
        glTexCoord2f(1, 1)
        glVertex2f(1, 1)
        glTexCoord2f(0, 1)
        glVertex2f(-1, 1)
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        self.frame += 1
        self.frame = self.frame % (self.frames - 1)


class MyPygletWidget(QPygletWidget):
    def on_init(self):
        super().__init__()
        self.setMinimumSize(QtCore.QSize(1028, 1028))
        self.frames = 255
        self.my_size = 1028
        number_of_bytes = self.frames*self.my_size*self.my_size*3
        image_size = self.my_size*self.my_size*3

        self.array = np.random.randint(0, 255, (self.frames, self.my_size, self.my_size, 3), dtype=np.uint8)
        self.array = np.ones((self.frames, self.my_size, self.my_size, 3), dtype=np.uint8)
        self.frame = 0
        self.t0 = 0
        # self.on_update = self.paintGL


    def on_draw(self, _=0):
        pass
        # self.update()

    def get_image(self):
        # print(max(self.array[self.frame].ravel()*(self.frame/255)))

        return

class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.widget = MyPygletWidget()
        self.setCentralWidget(self.widget)
        self.widget.update_me.connect(self.update)
        # self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        # self.layout().addWidget(self.slider)




def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()