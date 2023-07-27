from pymmcore_widgets import MDAWidget
from qtpy.QtWidgets import QApplication
from pymmcore_plus import CMMCorePlus
import numpy as np

mmcore = CMMCorePlus.instance()
mmcore.loadSystemConfiguration()


if __name__ == '__main__':
    app = QApplication([])
    zeros = np.zeros([512, 512, 30])

    mda = MDAWidget(include_run_button=True)

    mda.show()

    app.exec_()