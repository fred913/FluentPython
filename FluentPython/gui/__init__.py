from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (FluentWindow, NavigationItemPosition,
                            SubtitleLabel, setFont)

from FluentPython.gui._models import Widget


class FluentPythonMainWindow(FluentWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.homeInterface = Widget('Home', self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets')


def start_gui():
    app = QApplication()
    w = FluentPythonMainWindow()
    w.show()
    app.exec()
