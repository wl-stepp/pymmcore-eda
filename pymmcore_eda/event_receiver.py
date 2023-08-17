import multiprocessing
from _queue import Empty
from pymmcore_eda.datastore import BufferedDataStore
from pymmcore_eda.event_bus import EventBus
from qtpy import QtWidgets, QtCore
from useq import MDASequence
import time


class QEventReceiver(QtCore.QObject):

    stop_thread = QtCore.Signal()

    def __init__(self, queue: multiprocessing.Queue, buffer_name: str):
        super().__init__()
        self.queue = queue
        self.datastore = BufferedDataStore(create=False, name=buffer_name)
        self.event_thread = QtCore.QThread()
        self.listener = QEventListener(self, self.queue, self.datastore)
        self.listener.moveToThread(self.event_thread)
        self.event_thread.started.connect(self.listener.start)

        self.event_thread.start()

    def stop(self):
        pass

    def closeEvent(self):
        self.stop_thread.emit()

class QEventListener(QtCore.QObject):
    sequence_started = QtCore.Signal(MDASequence)
    frame_ready = QtCore.Signal(int, tuple, dict)
    def __init__(self, receiver: QEventReceiver,
                 queue: multiprocessing.Queue, datastore: BufferedDataStore):
        super().__init__()
        self.receiver = receiver
        self.queue = queue
        self.datastore = datastore
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
                    print("EventListener Timeout")
                    continue
            print(event)
            match event["name"]:
                case "stop":
                    print("STOP")
                    break
                case "frame_ready":
                    print("EVENTRECEIVER", event["buffer_idx"])
                    self.frame_ready.emit(event["buffer_idx"], event["shape"], dict(event["index"]))
                case "sequence_started":
                    print(event["dict"])
                    self.sequence_started.emit(MDASequence(time_plan = event["dict"]["time_plan"],
                                                    channels = event["dict"]["channels"],
                                                    axis_order = event["dict"]["axis_order"]))

    def stop(self):
        self.stop_requested = True


class QEventConsumer(QtWidgets.QWidget):
    def __init__(self, event_receiver: QEventReceiver|EventBus|None = None, *args, **kwargs):
        super().__init__()
        self.event_receiver = QEventReceiver() if event_receiver is None else event_receiver
        self.datastore = self.event_receiver.datastore
        self.listener = event_receiver.listener

    def closeEvent(self, event):
        self.event_receiver.closeEvent()
        time.sleep(1)
        self.hide()
        super().closeEvent(event)