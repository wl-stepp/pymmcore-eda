import multiprocessing
import time
from qtpy import QtWidgets
import sys
from unittest.mock import Mock

from pymmcore_plus import CMMCorePlus
from pymmcore_eda.buffered_datastore import BufferedDataStore
from useq import MDASequence
from pymmcore_eda.event_receiver import QEventReceiver
from pymmcore_eda.event_sender import EventSender

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 0, "loops":2},
    axis_order="tpcz",
    )

def test_receiver(qtbot):
    datastore = BufferedDataStore(create=True)
    queue = multiprocessing.Queue()
    event_sender = EventSender(datastore, queue)
    receiver = QEventReceiver(queue)
    mmcore.run_mda(sequence)
    with qtbot.waitSignal(receiver.listener.sequence_started, timeout=5000):
        pass
    with qtbot.waitSignal(receiver.listener.frame_ready, timeout=5000):
        pass
    time.sleep(2)
    assert queue.empty() # Should have been received and popped by the EventReceiver
    assert datastore[0] != 0
    datastore.close()


def run_acquisition(queue: multiprocessing.Queue):
    datastore = BufferedDataStore(create=True)
    event_sender = EventSender(datastore, queue)
    mmcore.run_mda(sequence, block=True)


def test_multiprocess(qtbot):
    queue = multiprocessing.Queue()
    # app = QtWidgets.QApplication(sys.argv)
    receiver = QEventReceiver(queue)

    p = multiprocessing.Process(target=run_acquisition, args=([queue]))
    p.start()
    with qtbot.waitSignal(receiver.listener.sequence_started, timeout=5000):
        pass
    with qtbot.waitSignal(receiver.listener.frame_ready, timeout=5000):
        pass
    with qtbot.waitSignal(receiver.listener.frame_ready, timeout=500):
        pass


    assert queue.empty() # Should have been received and popped by the EventReceiver
