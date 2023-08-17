from leb.kpal.buffer import BufferedArray
from pymmcore_plus import CMMCorePlus
import numpy as np
from useq import MDAEvent
import copy
from psygnal import Signal

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

DIMENSIONS = ["c", "z", "t", "p", "g"]
CAPACITY = int(10E8)

def complement_indices(event):
    indeces = dict(copy.deepcopy(dict(event.index)))
    for i in DIMENSIONS:
        if i not in indeces:
            indeces[i] = 0
    return indeces


class BufferedDataStore(BufferedArray):

    frame_ready = Signal(int, tuple, MDAEvent)

    def __new__(self, create: bool = True, *args, **kwargs):
        try:
            self.name = kwargs['name']
        except:
            pass
        return super().__new__(BufferedDataStore, capacity=CAPACITY, dtype=np.uint16, create=create,
                               *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__()
        setattr(self, "complement_indices", complement_indices)
        #TODO: This limits the sizes of the axes
        self.indeces_to_idx = np.ndarray([3,1,1000, 3], np.uint64)
        mmcore.mda.events.frameReady.connect(self.new_frame)

    def new_frame(self, img: np.ndarray, event: MDAEvent):
        idx = self._write_idx
        indices = self.complement_indices(event)
        try:
            self.indeces_to_idx[indices['c'], indices['z'], indices['t']] = (int(img.shape[0]),
                                                                            int(img.shape[1]),
                                                                            int(idx))
        except IndexError:
            shape_now = self.indeces_to_idx.shape
            new_min_shape = [indices['c'], indices['z'], indices['t']]
            diff = [x - y for x, y in zip(new_min_shape, shape_now)]
            for i, app in enumerate(diff):
                self.indeces_to_idx.append(i, app)
        self.put(img)
        self.frame_ready.emit(idx, img.shape, event)

    def get_frame(self, indeces: list):
        width, height, index = self.indeces_to_idx[*indeces]
        index1 = index + width*height
        return np.reshape(self[index:index1], [width, height])



    # def __getitem__(self, key):
    #     print(key)
    #     idxs = self.indeces_to_idx[key]
    #     print(idxs)
    #     return self.get_frame(idxs[0], idxs[1], idxs[2])


if __name__ == "__main__":
    from useq import MDASequence
    import time
    mmcore.setProperty("Camera", "OnCameraCCDXSize", 1024)
    mmcore.setProperty("Camera", "OnCameraCCDYSize", 1024)
    database = BufferedDataStore()
    mmcore.run_mda(MDASequence(time_plan={"interval": 1, "loops": 3}))
    time.sleep(3)
    print(database.get_frame([0, 0, 1]).shape)