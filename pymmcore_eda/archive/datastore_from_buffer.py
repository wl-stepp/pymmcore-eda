class DataStore(QtCore.QObject):
    frame_ready = QtCore.Signal(int, tuple, MDAEvent)
    """Store to have the data ready for a canvas to display."""
    def __init__(self, shape: tuple, datastore: None|BufferedDataStore = None,
                 dtype: npt.DTypeLike = np.int16, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dtype = np.dtype(dtype)
        self.array = np.ndarray(shape, dtype=self.dtype, *args, **kwargs)
        setattr(self, "complement_indices", complement_indices)
        #Connect to the datastore if passed or directly to the core
        if datastore is None:
            self.listener = self.EventListener()
            self.listener.start()
            self.listener.frame_ready.connect(self.new_frame)
        else:
            self.datastore = datastore
            self.datastore.frame_ready.connect(self.new_frame_buffer)

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
        img = img*indices["t"]//10
        try:
            self.array[:, :, indices["c"], indices["z"], indices["t"]] = img
        except IndexError:
            self.correct_shape(indices)
            self.new_frame(img, event)
            return
        self.frame_ready.emit(0, self.shape, event)

    def new_frame_buffer(self, idx: int, shape: tuple, event: MDAEvent):
        self.shape = shape
        indices = self.complement_indices(event)
        id_list = [indices["c"], indices["z"], indices["t"]]
        try:
            self.array[:, :, *id_list] = deepcopy(self.datastore.get_frame([*id_list]))
        except IndexError:
            self.correct_shape(indices)
            self.new_frame_buffer(idx, shape, event)
            return
        self.frame_ready.emit(0, self.shape, event)

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

    def get_frame(self, key):
        return self.array[:, :, *key]