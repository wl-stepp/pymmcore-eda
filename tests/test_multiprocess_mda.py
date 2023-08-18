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


mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()





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



if __name__ == "__main__":

    event_queue = Queue()
    datastore = BufferedDataStore(create=True)
    p = Process(target=check_receiver, args=([event_queue]))
    p.start()
    time.sleep(7)
    event_bus = EventBus(datastore, event_queue = event_queue)
    sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 100}, {"config": "FITC", "exposure": 100}],
    time_plan={"interval": 0.5, "loops":5},
    axis_order="tpcz",
    )
    mmcore.run_mda(sequence)
