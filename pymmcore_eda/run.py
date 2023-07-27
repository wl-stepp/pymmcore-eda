import numpy as np
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda.eda_runner import EDARunner
from useq import MDAEvent, MDASequence, Channel
import time
from threading import Timer
# see https://pymmcore-plus.github.io/useq-schema/api/


sequence = MDASequence(
    channels=[{"config": "FITC", "exposure": 50}],
    time_plan={"interval": 1, "loops": 2},
    # z_plan={"range": 4, "step": 0.5},
    axis_order="tpcz",
)

mmc = CMMCorePlus.instance()
mmc.set_mda(EDARunner)


mmc.loadSystemConfiguration()  #  load demo configuration

# connect callback using a decorator

@mmc.mda.events.frameReady.connect
def new_frame(img: np.ndarray, event: MDAEvent):
    print(time.perf_counter() - t0)

def restart():
    print("RESUME")
    mmc.mda.toggle_pause()
    print(mmc.mda._paused_time)

@mmc.mda.events.frameReady.connect
def my_frame(img: np.ndarray, event: MDAEvent):
    if event.global_index > 5:
        return
    new_event = MDAEvent(index={'t': mmc.mda.acq_events[-1].index["t"] + 1, 'c': 0},
                     channel=mmc.mda.acq_events[-1].channel,
                     exposure=50.0,
                     min_start_time= mmc.mda.acq_events[-1].min_start_time + 3.0,
                     global_index=mmc.mda.acq_events[-1].global_index + 1)
    mmc.mda.acq_events.append(new_event)


# or connect callback using a function
def on_start(sequence: MDASequence):
    print(f"now starting sequence {sequence.uid}!")


mmc.mda.events.sequenceStarted.connect(on_start)

# run the sequence in a separate thread
t0 = time.perf_counter()
mmc.run_mda(sequence)