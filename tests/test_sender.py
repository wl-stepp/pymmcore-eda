from pymmcore_eda.event_sender import EventSender
from pymmcore_eda.buffered_datastore import BufferedDataStore
from pymmcore_plus import CMMCorePlus
from useq import MDASequence
import multiprocessing

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

sequence = MDASequence(
    time_plan={"interval": 0, "loops": 2},
)

def test_events():
    datastore = BufferedDataStore(create=True)
    queue = multiprocessing.Queue()
    sender = EventSender(datastore, queue)
    mmcore.run_mda(sequence, block=True)
    assert not queue.empty()
    assert queue.get()["name"] in ["frame_ready", "sequence_started"]