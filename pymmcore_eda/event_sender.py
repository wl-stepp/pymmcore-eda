from useq import MDASequence, MDAEvent
from pymmcore_eda.buffered_datastore import BufferedDataStore
from pymmcore_plus import CMMCorePlus
import sys
import multiprocessing
from psygnal import Signal

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

class EventSender:
    """An event bus that can be used as a hub for pymmcore driven applications with the possibility
    to have an event_receiver in another process that communicates via an event queue.
    """

    def __init__(self, datastore: BufferedDataStore, event_queue: multiprocessing.Queue = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datastore = datastore
        self.event_queue = event_queue

        # Connect events to be transmitted to EventReceiver
        mmcore.mda.events.sequenceStarted.connect(self.on_sequence_start)
        self.datastore.frame_ready.connect(self.on_frame_ready)

    def on_frame_ready(self, event:MDAEvent, shape: tuple, index: int):
        self.event_queue.put({"name": "frame_ready", "yaml": event.yaml(), "shape": shape,
                              "index": index})

    def on_sequence_start(self, sequence: MDASequence):
        self.event_queue.put({"name": "sequence_started", "yaml": sequence.yaml()})

    def closeEvent(self):
        pass



if __name__ == "__main__":
    event_bus = EventSender()
    sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 10}, {"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 1, "loops": 5},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
