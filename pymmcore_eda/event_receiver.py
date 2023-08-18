import multiprocessing
from _queue import Empty
from pymmcore_eda.buffered_datastore import BufferedDataStore
from pymmcore_eda.archive.event_bus import EventBus
from qtpy import QtWidgets, QtCore
from useq import MDASequence, MDAEvent
import time
import yaml

class QEventReceiver(QtCore.QObject):

    stop_thread = QtCore.Signal()

    def __init__(self, queue: multiprocessing.Queue):
        super().__init__()
        self.queue = queue
        self.event_thread = QtCore.QThread()
        self.listener = QEventListener(self, self.queue)
        self.listener.moveToThread(self.event_thread)
        self.event_thread.started.connect(self.listener.start)

        self.event_thread.start()

    def stop(self):
        pass

    def closeEvent(self):
        self.stop_thread.emit()

class QEventListener(QtCore.QObject):
    sequence_started = QtCore.Signal(MDASequence)
    frame_ready = QtCore.Signal(MDAEvent)
    def __init__(self, receiver: QEventReceiver,
                 queue: multiprocessing.Queue):
        super().__init__()
        self.receiver = receiver
        self.queue = queue
        self.stop_requested = False
        self.receiver.stop_thread.connect(self.stop)

    def start(self):
        self.event_loop()

    def event_loop(self):
        while True:
            try:
                event = self.queue.get(timeout=0.5)
            except Empty:
                if self.stop_requested:
                    break
                else:
                    continue
            match event["name"]:
                case "stop":
                    print("STOP EventListener")
                    break
                case "frame_ready":
                    print("FRAME READY in Listener")
                    seq_dict = yaml.load(event["yaml"], Loader=yaml.FullLoader)
                    self.frame_ready.emit(MDAEvent().model_validate(seq_dict))
                case "sequence_started":
                    seq_dict = yaml.load(event["yaml"], Loader=yaml.FullLoader)
                    self.sequence_started.emit(MDASequence().model_validate(seq_dict))

    def stop(self):
        self.stop_requested = True


class QEventConsumer(QtWidgets.QWidget):
    def __init__(self, event_receiver: QEventReceiver|EventBus|None = None, *args, **kwargs):
        super().__init__()
        self.event_receiver = QEventReceiver() if event_receiver is None else event_receiver
        # self.datastore = self.event_receiver.datastore
        self.listener = event_receiver.listener

    def closeEvent(self, event):
        self.event_receiver.closeEvent()
        time.sleep(1)
        self.hide()
        super().closeEvent(event)


if __name__ == "__main__":
    from pymmcore_plus import CMMCorePlus
    mmcore = CMMCorePlus.instance()
    mmcore.loadSystemConfiguration()
    sequence = MDASequence(
        channels=[{"config": "DAPI", "exposure": 10}],
        time_plan={"interval": 0, "loops":2},
        axis_order="tpcz",
        )

    datastore = BufferedDataStore(create=True)
    queue = multiprocessing.Queue()
    # event_bus = EventBus(datastore, queue)
    receiver = QEventReceiver(queue)
    # assert datastore._shm.name == receiver.datastore._shm.name
    mmcore.run_mda(sequence)

    time.sleep(2)
    assert queue.empty() # Should have been received and popped by the EventReceiver
    # assert receiver.datastore[0] != 0
    datastore.close()