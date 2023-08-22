from qtpy import QtWidgets, QtCore
from useq import MDASequence
from pymmcore_eda.event_receiver import QEventConsumer, QEventReceiver
from pymmcore_eda.buffered_datastore import BufferedDataStore
from pathlib import Path
import tifffile
import os
import numpy as np

from pymmcore_plus import CMMCorePlus
mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

class Saver(QEventConsumer):
    """Save the array"""
    def __init__(self, event_receiver: QEventReceiver|None = None, *args,
                 datastore=None, **kwargs):
        super().__init__(event_receiver, datastore=datastore, *args, **kwargs)
        self.settings = QtCore.QSettings("MM", self.__class__.__name__)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_to_location)
        self.layout.addWidget(self.save_button)
        self.catch_next_idx = False

        self.save_location = self.settings.value("save_location", "C:\\")

    def save_to_location(self):
        fname = Path(QtWidgets.QFileDialog.getSaveFileName(self, 'Open file',self.save_location)[0])
        self.save_array(fname)

    def save_array(self, fname: Path = None):
        if fname is None:
            fname = Path(self.save_location) / "FOV"
        os.makedirs(fname, exist_ok=True)
        array = self.datastore.array
        tifffile.imwrite(fname/'images.ome.tif',
                         np.moveaxis(array, [0, 1, 2, 3, 4], [4, 3, 2, 1, 0]),
                         imagej=True)
        mmcore.saveSystemState(str(fname/'mm_data.txt'))
        self.save_location = str(fname.parent)

    def closeEvent(self, e):
        self.settings.setValue("save_location", self.save_location)
        super().closeEvent(e)


if __name__ == "__main__":
    from pymmcore_eda.local_datastore import QLocalDataStore
    import sys
    app = QtWidgets.QApplication(sys.argv)
    datastore = QLocalDataStore([512, 512, 2, 1, 10])
    saver = Saver(mmcore, datastore=datastore)
    saver.show()
    sequence = MDASequence(
        channels=[{"config": "FITC", "exposure": 1}, {"config": "DAPI", "exposure": 1}],
        time_plan={"interval": 0.5, "loops": 10},
        z_plan={"range": 5, "step": 1},
    )
    mmcore.run_mda(sequence)
    app.exec_()