from qtpy import QtWidgets, QtCore
from functools import wraps


class QLabeledSlider(QtWidgets.QWidget):
    """Slider that shows name of the axis and current value."""
    valueChanged = QtCore.Signal([int], [int, str])
    sliderPressed = QtCore.Signal()
    sliderMoved = QtCore.Signal()
    sliderReleased = QtCore.Signal()
    play = QtCore.Signal(bool)

    def __init__(self, name: str = "", orientation=QtCore.Qt.Horizontal , *args, **kwargs):
        # super().__init__(self, *args, **kwargs)
        super().__init__()
        self.name = name

        self.label = QtWidgets.QLabel()
        self.label.setText(name)
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

        self.play_btn = QtWidgets.QPushButton("play")
        self.play_btn.clicked.connect(self.play_clk)

        # self.layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.play_btn)
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.slider)
        self.layout().addWidget(self.current_value)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.slider.valueChanged.connect(self.handle_valueChanged)
        self.slider.sliderPressed.connect(self.sliderPressed)
        self.slider.sliderMoved.connect(self.sliderMoved)
        self.slider.sliderReleased.connect(self.sliderReleased)
        self.playing = False


    def handle_valueChanged(self, value):
        self.current_value.setText(f"{str(value)}/{str(self.slider.maximum())}")
        if self.name == "":
            self.valueChanged[int].emit(value)
        else:
            self.valueChanged[int,str].emit(value, self.name)

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
            self.play_btn.setText("play")
        else:
            self.play_btn.setText("stop")
        self.playing = not self.playing
        self.play.emit(self.playing)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = QLabeledSlider("", orientation=QtCore.Qt.Horizontal)
    w.show()
    # w.valueChanged.connect(lambda x: print(x))
    sys.exit(app.exec_())