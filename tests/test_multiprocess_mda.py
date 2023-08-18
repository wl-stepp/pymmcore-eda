from multiprocessing import Process, Queue
from qtpy import QtWidgets
from pymmcore_eda.archive.event_bus import EventBus
import sys
from pymmcore_plus import CMMCorePlus
from useq import MDASequence
from pymmcore_eda.buffered_datastore import BufferedDataStore
import time
from pymmcore_eda.event_receiver import QEventReceiver
from pymmcore_eda.canvas import Canvas
from pymmcore_eda.saver import Saver
from pymmcore_eda.event_sender import EventSender

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()


sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 100}, {"config": "FITC", "exposure": 100}],
    time_plan={"interval": 0.5, "loops":5},
    axis_order="tpcz",
    )


def check_buffer(name, event_queue: Queue):
    datastore = BufferedDataStore(sequence, create=False, name=name)
    while True:
        print(event_queue.get(timeout=500))
        print(datastore[0])

def check_receiver(queue: Queue):
    app = QtWidgets.QApplication(sys.argv)
    event_receiver = QEventReceiver(queue)
    # canvas = Canvas(event_receiver)
    # canvas.show()

    sys.exit(app.exec_())

def check_saver(queue: Queue, buffer_name: str):
    app = QtWidgets.QApplication(sys.argv)
    event_receiver = QEventReceiver(queue, buffer_name)
    saver = Saver(event_receiver)
    saver.show()

    sys.exit(app.exec_())


def run_acquisition(queue: Queue):
    datastore = BufferedDataStore(create=True)
    event_sender = EventSender(datastore, queue)
    mmcore.run_mda(sequence, block=True)


def receiver():
    queue = Queue()

    receiver = QEventReceiver(queue)
    p = Process(target=run_acquisition, args=([queue]))
    p.start()





if __name__ == "__main__":

    receiver()
