import multiprocessing

from pymmcore_eda.event_bus import EventBus
from pymmcore_plus import CMMCorePlus
from pymmcore_eda.datastore import DataStore
from useq import MDASequence

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 0, "loops":2},
    axis_order="tpcz",
    )

def test_datastore():
    datastore = DataStore()
    assert datastore[0] == 0
    mmcore.run_mda(sequence, block=True)
    assert datastore[0] != 0


def test_event_bus():
    datastore = DataStore()
    queue = multiprocessing.Queue()
    event_bus = EventBus(datastore, queue)
    mmcore.run_mda(sequence, block=True)
    assert not queue.empty()