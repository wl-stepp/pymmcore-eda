from pymmcore_eda.buffered_datastore import BufferedDataStore
from pymmcore_plus import CMMCorePlus
from useq import MDASequence
from unittest.mock import Mock

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()

sequence = MDASequence(
    time_plan={"interval": 0, "loops": 2},
)

def test_production():
    datastore = BufferedDataStore(create=True)
    assert datastore[0] == 0
    mmcore.run_mda(sequence, block=True)
    assert datastore[0] != 0

def test_consumation():
    mmcore.setProperty("Camera", "OnCameraCCDXSize", 1024)
    mmcore.setProperty("Camera", "OnCameraCCDYSize", 1024)
    datastore = BufferedDataStore(create=True)
    assert datastore[0] == 0
    mmcore.run_mda(sequence, block=True)
    assert datastore.get_frame([0, 0, 1]).flatten()[0] != 0
    assert datastore.get_frame([0, 0, 1]).shape == (1024, 1024)


def test_event():
    datastore = BufferedDataStore(create=True)
    mock_sender = Mock()
    datastore.frame_ready.connect(mock_sender)
    mmcore.run_mda(sequence, block=True)
    assert mock_sender.call_count == 2

    mock_sender2 = Mock()
    sequence2 = MDASequence(
        time_plan={"interval": 0, "loops": 10},
    )
    datastore.frame_ready.connect(mock_sender2)
    mmcore.run_mda(sequence2, block=True)
    assert mock_sender2.call_count == 10
    assert mock_sender.call_count == 12