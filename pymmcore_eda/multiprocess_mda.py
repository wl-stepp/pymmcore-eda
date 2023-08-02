from multiprocessing import Process, Queue
from qtpy import QtWidgets
from event_bus import EventBus
import sys
from pymmcore_plus import CMMCorePlus
from useq import MDASequence
from datastore import DataStore
import time
from event_receiver import QEventReceiver
from canvas import Canvas
from saver import Saver


mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()





def check_buffer(name, event_queue: Queue):
    datastore = DataStore(sequence, create=False, name=name)
    while True:
        print(event_queue.get(timeout=500))
        print(datastore[0])

def check_receiver(queue: Queue, buffer_name: str):
    app = QtWidgets.QApplication(sys.argv)
    event_receiver = QEventReceiver(queue, buffer_name)
    canvas = Canvas(event_receiver)
    canvas.show()

    sys.exit(app.exec_())

def check_saver(queue: Queue, buffer_name: str):
    app = QtWidgets.QApplication(sys.argv)
    event_receiver = QEventReceiver(queue, buffer_name)
    saver = Saver(event_receiver)
    saver.show()

    sys.exit(app.exec_())



if __name__ == "__main__":

    event_queue = Queue()
    datastore = DataStore(create=True, name="test_buffer")
    p = Process(target=check_receiver, args=([event_queue, "test_buffer"]))
    p.start()
    time.sleep(7)
    event_bus = EventBus(datastore, event_queue = event_queue)
    sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 100}, {"config": "FITC", "exposure": 100}],
    time_plan={"interval": 0.5, "loops":5},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
