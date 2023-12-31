import multiprocessing
from _queue import Empty
from pymmcore_eda.buffered_datastore import BufferedDataStore
from pymmcore_eda.archive.event_bus import EventBus
from pymmcore_plus import CMMCorePlus
from qtpy import QtWidgets, QtCore
from useq import MDASequence, MDAEvent
import time
import yaml

class QEventReceiver(QtCore.QObject):

    stop_thread = QtCore.Signal()

    def __init__(self, queue: multiprocessing.Queue, auto_start: bool = True):
        super().__init__()
        self.queue = queue
        self.event_thread = QtCore.QThread()
        self.listener = QEventListener(self, self.queue)
        self.listener.moveToThread(self.event_thread)
        self.event_thread.started.connect(self.listener.start)

        if auto_start:
            self.event_thread.start()

    def stop(self):
        pass

    def closeEvent(self):
        self.stop_thread.emit()

class QEventListener(QtCore.QObject):
    sequence_started = QtCore.Signal(MDASequence)
    frame_ready = QtCore.Signal(MDAEvent, tuple, int)
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
                    seq_dict = yaml.load(event["yaml"], Loader=yaml.FullLoader)
                    my_event = MDAEvent().model_validate(seq_dict)
                    print("FRAME READY in Listener", my_event.__class__)
                    self.frame_ready.emit(my_event, tuple(event["shape"]), int(event["index"]))
                case "sequence_started":
                    seq_dict = yaml.load(event["yaml"], Loader=yaml.FullLoader)
                    self.sequence_started.emit(MDASequence().model_validate(seq_dict))

    def stop(self):
        self.stop_requested = True


class QEventConsumer(QtWidgets.QWidget):
    def __init__(self, event_receiver: QEventReceiver|EventBus|CMMCorePlus|None = None, *args,
                 datastore = None, **kwargs):
        super().__init__()
        self.events = QtCore.QObject()
        if isinstance(event_receiver, CMMCorePlus):
            self.listener = event_receiver.mda.events
            self.event_receiver = datastore.listener
            self.events.sequence_started = self.listener.sequenceStarted
            self.events.frame_ready = self.listener.frameReady
        else:
            self.event_receiver = event_receiver
            self.event_receiver = QEventReceiver() if event_receiver is None else event_receiver
            self.listener = event_receiver.listener
            self.events.sequence_started = self.listener.sequence_started
            self.events.frame_ready = self.listener.frame_ready
        print("DATASTORE", datastore)
        if datastore is not None:
            print("Datastore set")
            self.datastore = datastore
            self.events.frame_ready = self.datastore.frame_ready

    def closeEvent(self, event):
        self.event_receiver.closeEvent(event)
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