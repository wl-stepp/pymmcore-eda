from pymmcore_eda.canvas import Canvas
import multiprocessing
from pymmcore_eda.event_receiver import QEventReceiver
from pymmcore_eda.buffered_datastore import BufferedDataStore
from pymmcore_eda.event_sender import EventSender
from pymmcore_eda.local_datastore import QDataStore, QLocalDataStore
from pymmcore_plus import CMMCorePlus
import time
from useq import MDASequence
from qtpy import QtCore

sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 10}, {"config": "FITC", "exposure": 10}],
    time_plan={"interval": 0.5, "loops":20},
    axis_order="tpcz",
    )
mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

def run_acquisition(queue: multiprocessing.Queue, out_conn: multiprocessing.Pipe):
    remote_datastore = BufferedDataStore(create=True)
    out_conn.send(remote_datastore._shm.name)
    event_sender = EventSender(remote_datastore, queue)
    time.sleep(2)
    mmcore.run_mda(sequence, block=True)


def test_remote(qtbot):
    queue = multiprocessing.Queue()
    receiver = QEventReceiver(queue)
    out_conn, in_conn = multiprocessing.Pipe()
    p = multiprocessing.Process(target=run_acquisition, args=([queue, out_conn]))
    p.start()
    name = in_conn.recv()
    datastore = QDataStore(receiver, name, shape=[10, 10, 10, 512, 512])
    canvas = Canvas(receiver, datastore)
    if qtbot:
        with qtbot.waitSignal(receiver.listener.sequence_started, timeout=5000):
            pass
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass
    assert canvas.images[0]._data.shape == (512, 512)
    assert canvas.images[0]._data.flatten()[0] != 0


def test_local(qtbot):
    datastore = QLocalDataStore(shape=[20, 1, 2, 512, 512])
    canvas = Canvas(mmcore, datastore)
    canvas.show()
    qtbot.addWidget(canvas)
    mmcore.run_mda(sequence)
    if qtbot:
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass
    assert canvas.images[0]._data.shape == (512, 512)
    assert canvas.images[0]._data.flatten()[0] != 0
    assert canvas.images[1]._data.shape == (512, 512)
    assert len(canvas.channel_boxes) == 5
    assert len(canvas.sliders) > 1

    qtbot.wait(1000)

    qtbot.mouseMove(canvas, QtCore.QPoint(500, 500))
    qtbot.wait(500)
    qtbot.mouseMove(canvas, QtCore.QPoint(200, 200))
    qtbot.wait(1000)
    assert canvas.info_bar.text() != ""