
from useq import MDASequence, MDAEvent
from pymmcore_eda.datastore import DataStore
from pymmcore_plus import CMMCorePlus
import sys
import multiprocessing
from psygnal import Signal


mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

class EventBus:
    """An event bus that can be used as a hub for pymmcore driven applications with the possibility
    to have an event_receiver in another process that communicates via an event queue.
    """

    def __init__(self, datastore: DataStore, event_queue: multiprocessing.Queue = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datastore = datastore

        if event_queue is None:
            self.listener = self.Listener(datastore)
        else:
            self.event_queue = event_queue
            mmcore.mda.events.sequenceStarted.connect(self.on_sequence_start)
            self.datastore.frame_ready.connect(self.on_frame_ready)

    def on_frame_ready(self, idx: int, shape: tuple, event:MDAEvent):
        self.event_queue.put({"name": "frame_ready", "buffer_idx": idx, "shape": shape,
                              "index": event.index})

    def on_sequence_start(self, sequence: MDASequence):
        self.event_queue.put({"name": "sequence_started", "dict": sequence.dict()})

    def closeEvent(self):
        pass


    class Listener:
        sequence_started = Signal(MDASequence)
        frame_ready = Signal(int, tuple, dict)

        def __init__(self, datastore):
            self.datastore = datastore
            mmcore.mda.events.sequenceStarted.connect(self.sequence_started)
            self.datastore.frame_ready.connect(self.on_frame_ready)

        def on_frame_ready(self, idx: int, shape: tuple, event: MDAEvent):
            print("Frame ready in EventListener")
            self.frame_ready.emit(idx, shape, event.index)


if __name__ == "__main__":

    event_bus = EventBus()

    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 10}, {"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 1, "loops": 5},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
    event_bus.show()
