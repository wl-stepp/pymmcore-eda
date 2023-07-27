from leb.kpal.buffer import BufferedArray, _bytes_needed
from pymmcore_plus import CMMCorePlus
# from event_bus import EventBus
import numpy as np
from useq import MDASequence, MDAEvent
import copy

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

DIMENSIONS = ["c", "z", "t", "p", "g"]

class DataStore(BufferedArray):

    def __new__(self, event_bus, sequence: MDASequence, *args, **kwargs):
        exp_shape = sequence.sizes
        dt_n = mmcore.getImageBitDepth()
        dt = np.uint16 if dt_n == 16 else print("WARNING: bit depth not supported")
        width = mmcore.getImageWidth()
        height = mmcore.getImageHeight()
        n_ints = width * height * max(exp_shape['c'], 1) * max(exp_shape['z'], 1) * max(exp_shape['t'], 1)

        return super().__new__(DataStore, capacity=n_ints*dt_n//8, dtype=dt, create=True)

    def __init__(self, event_bus, sequence):
        super().__init__()
        self.event_bus = event_bus
        mmcore.mda.events.frameReady.connect(self.new_frame)

    def new_frame(self, img: np.ndarray, event: MDAEvent):
        self.put(img)

    def get_frame(self, width, height, index):
        index0 = width*height*(sum(index))
        index1 = index0 + width*height
        return np.reshape(self[index0:index1], [width, height])

    def complement_indices(self, event):
        indeces = dict(copy.deepcopy(event.index))
        for i in DIMENSIONS:
            if i not in indeces:
                indeces[i] = 0
        return indeces