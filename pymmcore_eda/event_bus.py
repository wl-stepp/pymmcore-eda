from qtpy import QtCore, QtWidgets
from useq import MDASequence, MDAEvent
from datastore import DataStore
from pymmcore_plus import CMMCorePlus
import numpy as np
import sys

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

class EventBus(QtCore.QObject):

    sequence_started = QtCore.Signal(MDASequence, DataStore)
    frame_ready = QtCore.Signal(MDAEvent)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.datastores = []

        mmcore.mda.events.sequenceStarted.connect(self.on_sequence_start)
        mmcore.mda.events.frameReady.connect(self.on_frame_ready)

    def on_frame_ready(self, img: np.ndarray, event: MDAEvent):
        self.frame_ready.emit(event)

    def on_sequence_start(self, sequence: MDASequence):
        datastore = DataStore(self, sequence)
        self.datastores.append(datastore)
        print("Datastore created")
        self.sequence_started.emit(sequence, datastore)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    event_bus = EventBus()

    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 10}, {"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 1, "loops": 5},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
    event_bus.show()
    sys.exit(app.exec_())