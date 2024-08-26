from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (FluentWindow, NavigationItemPosition,
                            SubtitleLabel, setFont)

from FluentPython.gui.home import PageHome
from FluentPython.gui.jupyter import PageJupyter
from FluentPython.gui.versions import PageVersions


class FluentPythonMainWindow(FluentWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.homeInterface = PageHome(self)
        self.versionsInterface = PageVersions(self)
        self.jupyterInterface = PageJupyter(self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.versionsInterface, FIF.BOOK_SHELF,
                             'Versions')

        self.addSubInterface(self.jupyterInterface, FIF.PLAY, 'Jupyter')

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('Fluent Python')


def start_gui():
    app = QApplication()
    w = FluentPythonMainWindow()
    w.show()
    app.exec()
