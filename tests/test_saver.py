from pymmcore_eda.local_datastore import QLocalDataStore
from pymmcore_eda.saver import Saver
from pymmcore_plus import CMMCorePlus
from useq import MDASequence
from pathlib import Path
import os
import shutil
import tifffile

sequence = MDASequence(
    channels=[{"config": "DAPI", "exposure": 10}, {"config": "FITC", "exposure": 10}],
    time_plan={"interval": 0.5, "loops":10},
    )
mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

folder = Path("./data")
for content in folder.glob("*"):
    shutil.rmtree(content)
    print(content, "cleared")

def test_local(qtbot):
    datastore = QLocalDataStore(shape=[512, 512, 2, 1, 10])
    saver = Saver(mmcore, datastore=datastore)
    mmcore.run_mda(sequence)
    if qtbot:
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass
        with qtbot.waitSignal(datastore.frame_ready, timeout=5000):
            pass
    qtbot.wait(5_000)
    saver.save_array(Path("./data/test_save"))

    assert os.path.isfile("./data/test_save/images.ome.tif")
    assert os.path.isfile("./data/test_save/mm_data.txt")
    array = tifffile.imread("./data/test_save/images.ome.tif")
    assert array.shape == (10, 2, 512, 512)
    saver.close()