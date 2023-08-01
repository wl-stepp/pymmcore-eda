from leb.kpal.buffer import BufferedArray, _bytes_needed
from pymmcore_plus import CMMCorePlus
# from event_bus import EventBus
import numpy as np
from useq import MDASequence, MDAEvent
import copy
from psygnal import Signal

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

DIMENSIONS = ["c", "z", "t", "p", "g"]


class DataStore(BufferedArray):

    frame_ready = Signal(int, tuple, MDAEvent)

    def __new__(self, create: bool = True, *args, **kwargs):
        return super().__new__(DataStore, capacity=int(10E8), dtype=np.uint16, create=create, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__()
        mmcore.mda.events.frameReady.connect(self.new_frame)

    def new_frame(self, img: np.ndarray, event: MDAEvent):
        idx = self._write_idx
        self.put(img)
        self.frame_ready.emit(idx, img.shape, event)

    def get_frame(self, width, height, index):
        index1 = index + width*height
        return np.reshape(self[index:index1], [width, height])

    def complement_indices(self, event):
        indeces = dict(copy.deepcopy(event.index))
        for i in DIMENSIONS:
            if i not in indeces:
                indeces[i] = 0
        return indeces