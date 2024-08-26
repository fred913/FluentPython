from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)
from qfluentwidgets import (SingleDirectionScrollArea, SubtitleLabel,
                            TitleLabel, VBoxLayout, setFont)

from FluentPython.gui._utils import get_greeting_message


class PageHome(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setObjectName("Home")

        self.main_layout = VBoxLayout(self)

        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSizeConstraint(
            QVBoxLayout.SizeConstraint.SetFixedSize)

        self.title_label = TitleLabel("Welcome to Fluent Python")
        self.main_layout.addWidget(self.title_label)

        self.subtitle_label = SubtitleLabel(get_greeting_message())
        self.subtitle_label.setContentsMargins(0, 10, 0, 0)
        self.main_layout.addWidget(self.subtitle_label)
