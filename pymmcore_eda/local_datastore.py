from qtpy import QtCore
import numpy as np
import numpy.typing as npt
from pymmcore_eda.buffered_datastore import complement_indices
from useq import MDAEvent
from pymmcore_plus import CMMCorePlus
from pymmcore_eda.event_receiver import QEventReceiver, QEventConsumer
from pymmcore_eda.buffered_datastore import BufferedDataStore

from logging import getLogger
from copy import deepcopy

log = getLogger(__name__)

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

class QDataStore(QEventConsumer):
    """Datastore that receives events from the eventreiceiver from a BufferedDataStore from a
    different process. It copies it into a numpy array, emits a signal when it's ready to be
    displayed."""
    frame_ready = QtCore.Signal(MDAEvent)

    def __init__(self, event_receiver: QEventReceiver, remote_datastore_name: BufferedDataStore,
                 shape: tuple, dtype: npt.DTypeLike = np.int16, *args, **kwargs):
        super().__init__(event_receiver, *args, **kwargs)
        self.dtype = np.dtype(dtype)
        self.array = np.ndarray(shape, dtype=self.dtype, *args, **kwargs)

        self.listener.frame_ready.connect(self.new_frame)
        self.remote_datastore = BufferedDataStore(name=remote_datastore_name, create=False)
        setattr(self, "complement_indices", complement_indices)
        setattr(self, "correct_shape", correct_shape)

    def new_frame(self, event: MDAEvent, shape: tuple, index: int):
        print("NEW FRAME IN LOCAL STORE", event.index)
        indices = self.complement_indices(event)
        id_list = [indices["c"], indices["z"], indices["t"]]
        try:
            index1 = index + shape[0]*shape[1]
            self.array[:, :, *id_list] = deepcopy(np.reshape(self.remote_datastore[index:index1],
                                                             [shape[0], shape[1]]))
        except IndexError:
            self.correct_shape(indices)
            self.new_frame(event)
            return
        self.frame_ready.emit(event)

    def get_frame(self, key):
        return self.array[:, :, *key]

def correct_shape(self, indices: tuple) -> None:
    "The initialised shape does not fit the data, extend the array."
    min_shape = [indices['c'], indices['z'], indices['t']]
    diff = [x - y for x, y in zip(min_shape, self.array.shape[2:])]
    for i, app in enumerate(diff):
        if app >= 0:
            if i == 2: # handle time differently, double the size
                app = self.array.shape[4]
            append_shape = [*self.array.shape[:i+2], app + 1, *self.array.shape[i+3:]]
            self.array = np.append(self.array, np.zeros(append_shape, self.array.dtype),
                                    axis=i+2)
            print("new shape", self.array.shape)


class QLocalDataStore(QtCore.QObject):
    """DataStore that connects directly to the mmcore frameReady event and saves the data for
    a consumer like Canvas to show it."""
    frame_ready = QtCore.Signal(MDAEvent)
    def __init__(self, shape: tuple, dtype: npt.DTypeLike = np.int16, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dtype = np.dtype(dtype)
        self.array = np.ndarray(shape, dtype=self.dtype, *args, **kwargs)
        setattr(self, "complement_indices", complement_indices)

        self.listener = self.EventListener()
        self.listener.start()
        self.listener.frame_ready.connect(self.new_frame)
        setattr(self, "correct_shape", correct_shape)

    class EventListener(QtCore.QThread):
        "Receive events in a separate thread"
        frame_ready = QtCore.Signal(np.ndarray, MDAEvent)
        def __init__(self):
            super().__init__()
            mmcore.mda.events.frameReady.connect(self.on_frame_ready)

        def on_frame_ready(self, img: np.ndarray, event: MDAEvent):
            self.frame_ready.emit(img, event)

    def new_frame(self, img: np.ndarray, event: MDAEvent):
        self.shape = img.shape
        indices = self.complement_indices(event)
        img = img*(indices["t"] + 1)//10
        try:
            self.array[:, :, indices["c"], indices["z"], indices["t"]] = img
        except IndexError:
            self.correct_shape(indices)
            self.new_frame(img, event)
            return
        self.frame_ready.emit(event)

    def get_frame(self, key):
        return self.array[:, :, *key]
