import sys
import pyglet
from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QMainWindow, QOpenGLWidget
from qtpy.QtCore import QTimer
import numpy as np

size = 100
array = np.random.randint(0, 255, (10, size, size, 3), dtype=np.uint8)


class PygletOpenGLWidget(QOpenGLWidget):
    def initializeGL(self):
        self.pyglet_window = pyglet.window.Window(
            width=self.width(),
            height=self.height(),
            config=pyglet.Config(double_buffer=True),
            resizable=True
        )

    def paintGL(self):
        self.pyglet_window.switch_to()
        self.pyglet_window.dispatch_events()
        self.pyglet_window.clear()
        # Add your Pyglet rendering code here
        self.pyglet_window.flip()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt with Pyglet OpenGL")
        self.setGeometry(100, 100, 800, 600)  # Set your desired size

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        self.opengl_widget = PygletOpenGLWidget(self.central_widget)
        layout.addWidget(self.opengl_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())