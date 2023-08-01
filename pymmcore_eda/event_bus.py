
from useq import MDASequence, MDAEvent
from datastore import DataStore
from pymmcore_plus import CMMCorePlus
import sys
import multiprocessing

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

class EventBus:

    def __init__(self, datastore: DataStore, event_queue: multiprocessing.Queue = multiprocessing.Queue(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_queue = event_queue
        self.listener = self
        self.datastore = datastore

        mmcore.mda.events.sequenceStarted.connect(self.on_sequence_start)
        self.datastore.frame_ready.connect(self.on_frame_ready)

    def on_frame_ready(self, idx: int, shape: tuple, event:MDAEvent):
        self.event_queue.put({"name": "frame_ready", "buffer_idx": idx, "shape": shape,
                              "index": event.index})

    def on_sequence_start(self, sequence: MDASequence):
        self.event_queue.put({"name": "sequence_started", "dict": sequence.dict()})


if __name__ == "__main__":

    event_bus = EventBus()

    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 10}, {"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 1, "loops": 5},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
    event_bus.show()
