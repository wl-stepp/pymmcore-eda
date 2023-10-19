from qtpy import QtWidgets, QtCore, QtGui
import time

class QLabeledSlider(QtWidgets.QWidget):
    """Slider that shows name of the axis and current value."""
    valueChanged = QtCore.Signal([int], [int, str])
    sliderPressed = QtCore.Signal()
    sliderMoved = QtCore.Signal()
    sliderReleased = QtCore.Signal()

    def __init__(self, name: str = "", orientation=QtCore.Qt.Horizontal , *args, **kwargs):
        # super().__init__(self, *args, **kwargs)
        super().__init__()
        self.name = name

        self.label = QtWidgets.QLabel()
        self.label.setText(name.upper())
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.slider = QtWidgets.QSlider(orientation)
        for function in ["blockSignals", "setTickInterval","setTickPosition", "tickInterval",
                         "tickPosition", "minimum", "maximum", "setTracking", "value"]:
            func = getattr(self.slider, function)
            setattr(self, function, func)

        self.current_value = QtWidgets.QLabel()
        self.current_value.setText("0")
        self.current_value.setAlignment(QtCore.Qt.AlignLeft)
        self.current_value.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.play_btn = QtWidgets.QPushButton("▶")
        self.play_btn.setStyleSheet("QPushButton {padding: 2px;}")
        self.play_btn.setFont(QtGui.QFont("Times", 14))
        self.play_btn.clicked.connect(self.play_clk)

        # self.layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.play_btn)
        self.layout().addWidget(self.slider)
        self.layout().addWidget(self.current_value)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.slider.valueChanged.connect(self.on_drag_timer)
        self.slider.sliderPressed.connect(self.sliderPressed)
        self.slider.sliderMoved.connect(self.sliderMoved)
        self.slider.sliderReleased.connect(self.sliderReleased)
        self.playing = False


        self.play_timer = QtCore.QTimer(interval=10)
        self.play_timer.timeout.connect(self.on_play_timer)

        self.drag_timer = QtCore.QTimer(interval=10)
        self.drag_timer.timeout.connect(self.on_drag_timer)

    def _start_play_timer(self, playing):
        if playing:
            self.play_timer.start(0.01)
        else:
            self.play_timer.stop()

    def on_play_timer(self, _=None):
        value = self.value() + 1
        value = value % self.maximum()
        self.setValue(value)

    # def handle_valueChanged(self, value):
    #     self.current_value.setText(f"{str(value)}/{str(self.slider.maximum())}")
    #     if self.name == "":
    #         self.valueChanged[int].emit(value)
    #     else:
    #         self.valueChanged[int,str].emit(value, self.name)

    def setMaximum(self, maximum: int):
        self.current_value.setText(f"{str(self.value())}/{str(maximum)}")
        self.slider.setMaximum(maximum)

    def setRange(self, minimum, maximum):
        self.current_value.setText(f"{str(self.value())}/{str(maximum)}")
        self.slider.setMaximum(maximum)

    def setValue(self, value):
        self.current_value.setText(f"{str(value)}/{str(self.maximum())}")
        self.slider.setValue(value)

    def play_clk(self):
        if self.playing:
            self.play_btn.setText("▶")
            self.play_timer.stop()
        else:
            self.play_btn.setText("■")
            self.play_timer.start()
        self.playing = not self.playing

    def on_slider_press(self):
        self.slider.valueChanged.disconnect(self.on_drag_timer)
        self.drag_timer.start()

    def on_slider_release(self):
        self.drag_timer.stop()
        self.slider.valueChanged.connect(self.on_drag_timer)

    def on_drag_timer(self):
        self.valueChanged[int, str].emit(self.value(), self.name)

if __name__ == "__main__":
    import sys
    import time
    app = QtWidgets.QApplication(sys.argv)
    w = QLabeledSlider("", orientation=QtCore.Qt.Horizontal)
    w.show()
    # w.valueChanged.connect(lambda x: print(x))
    sys.exit(app.exec_())