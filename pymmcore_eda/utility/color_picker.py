#from https://stackoverflow.com/questions/64497029/a-color-drop-down-selector-for-pyqt5

from qtpy import QtCore, QtWidgets, QtGui


class QColorComboBox(QtWidgets.QComboBox):
    ''' A drop down menu for selecting colors '''

    # signal emitted if a color has been selected
    selectedColor = QtCore.Signal(QtGui.QColor)

    def __init__(self, parent = None, enableUserDefColors = False):
        ''' if the user shall not be able to define colors on its own, then set enableUserDefColors=False '''
        # init QComboBox
        super(QColorComboBox, self).__init__(parent)

        # enable the line edit to display the currently selected color
        self.setEditable(True)
        # read only so that there is no blinking cursor or sth editable
        self.lineEdit().setReadOnly(True)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # text that shall be displayed for the option to pop up the QColorDialog for user defined colors
        self._userDefEntryText = 'New'
        # add the option for user defined colors
        if (enableUserDefColors):
            self.addItem(self._userDefEntryText)

        self._currentColor = None

        self.activated.connect(self._color_selected)
        # self.setStyleSheet("QComboBox:drop-down {image: none; background: red; border: 1px grey;}")


    def addColors(self, colors):
        ''' Adds colors to the QComboBox '''
        for a_color in colors:
            # if input is not a QColor, try to make it one
            if (not (isinstance(a_color, QtGui.QColor))):
                try:
                    a_color = QtGui.QColor(a_color)
                except TypeError:
                    if max(a_color) < 2:
                        a_color = [int(x*255) for x in a_color]
                    a_color = QtGui.QColor(*a_color)

            # avoid dublicates
            if (self.findData(a_color) == -1):
                # add the new color and set the background color of that item
                self.addItem('', userData = a_color)
                self.setItemData(self.count()-1, QtGui.QColor(a_color), QtCore.Qt.BackgroundRole)

    def addColor(self, color):
        ''' Adds the color to the QComboBox '''
        self.addColors([color])

    def setColor(self, color):
        ''' Adds the color to the QComboBox and selects it'''
        if isinstance(color, int):
            self.setCurrentIndex(color)
            self._currentColor = self.itemData(color)
            self.lineEdit().setStyleSheet("background-color: "+self._currentColor.name())
        else:
            self._color_selected(self.findData(color), False)

    def getCurrentColor(self):
        ''' Returns the currently selected QColor
            Returns None if non has been selected yet
        '''
        return self._currentColor

    def _color_selected(self, index, emitSignal = True):
        ''' Processes the selection of the QComboBox '''
        # if a color is selected, emit the selectedColor signal
        if (self.itemText(index) == ''):
            self._currentColor = self.itemData(index)
            if (emitSignal):
                self.selectedColor.emit(self._currentColor)

        # if the user wants to define a custom color
        elif(self.itemText(index) == self._userDefEntryText):
            # get the user defined color
            new_color = QtWidgets.QColorDialog.getColor(self._currentColor
                                                        if self._currentColor else QtCore.Qt.white)
            if (new_color.isValid()):
                # add the color to the QComboBox and emit the signal
                self.addColor(new_color)
                self._currentColor = new_color
                if (emitSignal):
                    self.selectedColor.emit(self._currentColor)

        # make sure that current color is displayed
        if (self._currentColor):
            self.setCurrentIndex(self.findData(self._currentColor))
            self.lineEdit().setStyleSheet("background-color: "+self._currentColor.name())



if __name__ =="__main__":
    app = QtWidgets.QApplication([])
    combo = QColorComboBox()
    combo.addColors(['red', 'green', 'blue'])
    combo.show()
    app.exec_()