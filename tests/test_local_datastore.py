import multiprocessing
import time
from qtpy import QtWidgets, QtCore

from pymmcore_plus import CMMCorePlus
from pymmcore_eda.buffered_datastore import BufferedDataStore
from useq import MDASequence
from pymmcore_eda.event_receiver import QEventReceiver
from pymmcore_eda.event_sender import EventSender
from pymmcore_eda.local_datastore import QDataStore
import sys
from logging import getLogger

log = getLogger(__name__)

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 10}],
    time_plan={"interval": 1, "loops":5},
    axis_order="tpcz",
    )

def run_acquisition(queue: multiprocessing.Queue, out_conn: multiprocessing.Pipe):
    remote_datastore = BufferedDataStore(create=True)
    out_conn.send(remote_datastore._shm.name)
    log.warning(f"Datastore name: {remote_datastore._shm.name}")
    event_sender = EventSender(remote_datastore, queue)
    time.sleep(2)
    mmcore.run_mda(sequence, block=True)


def test_receive_from_remote(qtbot):
    # Make the receiving side of the queue comms
    queue = multiprocessing.Queue()
    receiver = QEventReceiver(queue)

    # Start the acquisition process in a second process and pass a pipe to wait for the datastore
    out_conn, in_conn = multiprocessing.Pipe()
    p = multiprocessing.Process(target=run_acquisition, args=([queue, out_conn]))
    p.start()

    # Get the datastore name from the second process and generate the local variant of it
    name = in_conn.recv()
    datastore = QDataStore(receiver, name, shape=[10, 10, 10, 512, 512])

    if qtbot:
        with qtbot.waitSignal(receiver.listener.sequence_started, timeout=5000):
            pass
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass

    assert queue.empty() # Should have been received and popped by the EventReceiver
    assert datastore.get_frame([0,0,0]).flatten()[0] != 0


    print(datastore.get_frame([0,0,2]).shape)


if __name__ == "__main__":
    app= QtWidgets.QApplication([])
    test_writing(None)
    app.exec_()
