from qtpy import QtWidgets, QtCore
from event_receiver import QEventConsumer, QEventReceiver
from useq import MDASequence
from datastore import BufferedDataStore
from pathlib import Path
import tifffile
import os
import numpy as np

from pymmcore_plus import CMMCorePlus
mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

class Saver(QEventConsumer):
    """Save the array"""
    def __init__(self, event_receiver: QEventReceiver|None = None, *args, **kwargs):
        super().__init__(event_receiver, *args, **kwargs)
        self.settings = QtCore.QSettings("MM", self.__class__.__name__)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_array)
        self.layout.addWidget(self.save_button)
        self.catch_next_idx = False

        self.save_location = self.settings.value("save_location", "C:\\")
        self.listener.sequence_started.connect(self.on_sequence_started)
        self.listener.frame_ready.connect(self.on_frame_ready)

    def on_sequence_started(self, sequence: MDASequence):
        print("SEQUENCE INFORMATION RECEIVED IN SAVER")
        self.width = mmcore.getImageWidth()
        self.height = mmcore.getImageHeight()
        self.sequence = sequence
        self.catch_next_idx = True

    def on_frame_ready(self, idx, *_):
        if self.catch_next_idx:
            self.catch_next_idx = False
            self.start_idx = idx

    def save_array(self):
        fname = Path(QtWidgets.QFileDialog.getSaveFileName(self,
                                                           'Open file',self.save_location)[0])
        os.makedirs(fname)
        n_values = (max(self.sequence.sizes['c'], 1) * max(self.sequence.sizes['z'], 1) *
                    max(self.sequence.sizes['t'], 1) * self.width * self.height)
        array = self.datastore[self.start_idx:self.start_idx + n_values].reshape(
            [self.width, self.height, max(self.sequence.sizes['c'], 1),
             max(self.sequence.sizes['z'], 1),
             max(self.sequence.sizes['t'], 1)],
                                       order = "F")
        tifffile.imwrite(fname/'images.ome.tif',
                         np.moveaxis(array, [0, 1, 2, 3, 4], [4, 3, 2, 1, 0]),
                         imagej=True)
        mmcore.saveSystemState(str(fname/'mm_data.txt'))
        self.save_location = str(fname.parent)

    def closeEvent(self, e):
        self.settings.setValue("save_location", self.save_location)
        super().closeEvent(e)