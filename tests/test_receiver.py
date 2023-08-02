import multiprocessing
import time

from pymmcore_eda.event_bus import EventBus
from pymmcore_plus import CMMCorePlus
from pymmcore_eda.datastore import DataStore
from useq import MDASequence
from pymmcore_eda.event_receiver import QEventReceiver

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 0, "loops":2},
    axis_order="tpcz",
    )

def test_receiver(qtbot):
    datastore = DataStore(name="testing_buffer")
    queue = multiprocessing.Queue()
    event_bus = EventBus(datastore, queue)
    receiver = QEventReceiver(queue, datastore.name)
    mmcore.run_mda(sequence)
    with qtbot.waitSignal(receiver.listener.sequence_started, timeout=5000):
        pass
    with qtbot.waitSignal(receiver.listener.frame_ready, timeout=5000):
        pass
    time.sleep(2)
    assert queue.empty() # Should have been received and popped by the EventReceiver
    assert receiver.datastore[0] != 0
    datastore.close()