import multiprocessing

from pymmcore_eda.event_sender import EventSender
from pymmcore_plus import CMMCorePlus
from pymmcore_eda.buffered_datastore import BufferedDataStore
from useq import MDASequence

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 0, "loops":2},
    axis_order="tpcz",
    )

def test_datastore():
    datastore = BufferedDataStore(create=True)
    assert datastore[0] == 0
    mmcore.run_mda(sequence, block=True)
    assert datastore[0] != 0


def test_event_bus():
    datastore = BufferedDataStore(create=True)
    queue = multiprocessing.Queue()
    event_bus = EventSender(datastore, queue)
    mmcore.run_mda(sequence, block=True)
    assert not queue.empty()