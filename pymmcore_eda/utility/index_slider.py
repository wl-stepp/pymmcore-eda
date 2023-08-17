from qtpy import QtWidgets, QtCore

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
        # if name == "":
        #     self.valueChanged = QtCore.Signal(int)
        # else:
        #     self.valueChanged = QtCore.Signal(int, "str")

        self.label = QtWidgets.QLabel()
        self.label.setText(name)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.slider = QtWidgets.QSlider(orientation)
        self.current_value = QtWidgets.QLabel()
        self.current_value.setText("0")
        self.current_value.setAlignment(QtCore.Qt.AlignLeft)
        self.current_value.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # self.layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.slider)
        self.layout().addWidget(self.current_value)

        self.slider.valueChanged.connect(self.handle_valueChanged)
        self.slider.sliderPressed.connect(self.sliderPressed)
        self.slider.sliderMoved.connect(self.sliderMoved)
        self.slider.sliderReleased.connect(self.sliderReleased)

    def handle_valueChanged(self, value):
        self.current_value.setText(f"{str(value)}/{str(self.slider.maximum())}")
        if self.name != "":
            self.valueChanged[int].emit(value)
        else:
            self.valueChanged[int,str].emit(value, self.name)

    def setRange(self, minimum, maximum):
        self.slider.setRange(minimum, maximum)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = QLabeledSlider("", orientation=QtCore.Qt.Horizontal)
    w.show()
    # w.valueChanged.connect(lambda x: print(x))
    sys.exit(app.exec_())