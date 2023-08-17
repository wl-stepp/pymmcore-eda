from qtpy import QtWidgets, QtCore

class IndexSlider(QtWidgets.QSlider):
    """Slider that gets an index when created and transmits it when value changes."""
    valueChanged = QtCore.Signal(int, str)
    def __init__(self, **kwargs):
        self.index = kwargs['index']
        kwargs.pop('index')
        super().__init__(**kwargs)
        super().valueChanged.connect(self.orig_valueChanged)

    def orig_valueChanged(self, value):
        print("change in indexslider")
        self.valueChanged.emit(value, self.index)

    def _visibility(self, settings):
        if not settings['index'] == self.index:
            return
        if settings['show']:
            self.show()
        else:
            self.hide()
        self.setRange(0, settings['max'])


class LabeledIndexSlider(QtWidgets.QWidget):
    """IndexSlider that shows name of the axis and current value."""
    def __init__(self, *args, **kwargs):
        # super().__init__(self, *args, **kwargs)
        super().__init__()
        self.label = QtWidgets.QLabel()
        self.label.setText(kwargs['index'])
        self.slider = IndexSlider( *args, **kwargs)
        self.slider.installEventFilter(self)
        # self.label.setAlignment(QtCore.Qt.AlignRight)
        # self.label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.slider = IndexSlider(index, *args, **kwargs)
        # self.current_value = QtWidgets.QLabel()
        # self.current_value.setText("0")
        # self.current_value.setAlignment(QtCore.Qt.AlignLeft)
        # self.current_value.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # self.layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.label, 0)
        # self.layout().addWidget(self.widget, 1)
        self.layout().addWidget(self.slider, 1)
        # self.layout().addWidget(self.current_value)
        # self.valueChanged.connect(self.orig_valueChanged)

    def eventFilter(self, source, event):
        if event.type() == 5:
            print(event.type())

            print("Event in LabeledIndexSlider")
        return QtWidgets.QWidget.eventFilter(self, source, event)

    def orig_valueChanged(self, value):
        print("Slider touched")
        # self.current_value.setText(f"{str(value)}/{str(self.maximum())}")
        # super().orig_valueChanged(value)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = LabeledIndexSlider(index="z", orientation=QtCore.Qt.Horizontal)
    w.show()
    # w.valueChanged.connect(lambda x: print(x))
    sys.exit(app.exec_())