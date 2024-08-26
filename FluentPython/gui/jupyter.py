import subprocess
from dataclasses import dataclass

from loguru import logger
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)
from qfluentwidgets import Action, BodyLabel, CommandBar
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (FluentWindow, InfoBar, InfoBarPosition, LineEdit,
                            ListWidget, MessageBoxBase, PushButton,
                            SingleDirectionScrollArea, SubtitleLabel,
                            TitleLabel, VBoxLayout, setFont)

from FluentPython.core.config import CFG, FluentPyVersion
from FluentPython.gui.console import ConsoleExecutionPage


class PageJupyter(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setObjectName("JupyterLab")

        self.main_layout = VBoxLayout(self)

        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSizeConstraint(
            QVBoxLayout.SizeConstraint.SetDefaultConstraint)

        self.subtitle_label = SubtitleLabel("Versions")
        self.subtitle_label.setContentsMargins(0, 0, 0, 10)
        self.main_layout.addWidget(self.subtitle_label)

        self.toolbar = CommandBar(self.main_layout.widget())
        self.toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        act = Action(FIF.SYNC, "刷新")
        act.triggered.connect(self.reload_versions)
        self.toolbar.addAction(act)

        self.main_layout.addWidget(self.toolbar)

        self.h_layout = QHBoxLayout()
        self.main_layout.addLayout(self.h_layout)

        self.version_list = ListWidget()
        self.version_list.setMinimumWidth(260)
        self.version_list.setSizePolicy(QSizePolicy.Policy.Fixed,
                                        QSizePolicy.Policy.Expanding)
        self.version_list.currentItemChanged.connect(self.on_selecting_version)
        self.h_layout.addWidget(self.version_list)

        self.editing_frame = QFrame()

        self.h_layout.addWidget(self.editing_frame)

        self.reload_versions()

    def reload_versions(self):
        self.version_list.clear()

        for ver in CFG.list_versions():
            self.version_list.addItem(
                f"{ver.name} [{'.'.join(map(str, ver.version))}]")

        if self.version_list.count() > 0:
            self.subtitle_label.setText(
                f"Jupyter 环境 ({self.version_list.count()} versions)")
        else:
            self.subtitle_label.setText("Jupyter 环境 (no versions)")

    def on_selecting_version(self, current, previous):
        selected_item = self.version_list.currentItem()
        if selected_item:
            version_token = selected_item.text()
            # Implement the logic to edit the selected version
            # print(f"Editing version: {version_name}")
            version_name = " [".join(version_token.split(" [")[0:-1])
            version_version = tuple(
                filter(int,
                       version_token.split(" [")[-1][:-1].split(".")))
            assert len(version_version) == 3, "Invalid version format"
            logger.info(
                f"edit version: name={version_name}, version={version_version}"
            )

            ver = CFG.get_version(version_name)

            assert ver is not None, "Version not found"

            logger.debug(f"got version: {ver}")

            lo = self.editing_frame.layout()
            if lo is None:
                self.editing_frame.setLayout(QVBoxLayout())
                self.editing_frame.layout().setSizeConstraint(
                    VBoxLayout.SizeConstraint.SetDefaultConstraint)

            lo = self.editing_frame.layout()
            assert lo is not None, "Failed to create layout"
            assert isinstance(lo, QVBoxLayout), "Invalid layout type"

            for idx in range(lo.count()):
                lo.itemAt(idx).widget().deleteLater()

            # draw right panel
            jupyterLabBtn = PushButton("启动 Jupyter Lab")
            jupyterLabBtn.clicked.connect(lambda: self.start_jupyter_lab(ver))
            lo.addWidget(jupyterLabBtn)

    def start_jupyter_lab(self, ver: FluentPyVersion):
        cmd = [ver.py_executable, "-m", "pip", "install", "jupyterlab"]
        logger.debug(f"Running command: {cmd}")
        subprocess.check_output(cmd)

        cmd = [ver.py_executable, "-m", "jupyter", "lab"]
        logger.debug(f"Running command: {cmd}")
        win = ConsoleExecutionPage(cmd, parent=self.topLevelWidget())

        win.setObjectName("JupyterLab-tmp123")

        tlw = self.topLevelWidget()
        assert isinstance(tlw, FluentWindow), "Invalid top level widget"
        tlw.addSubInterface(win, FIF.CODE, "[TMP] Jupyter Lab")
        tlw.switchTo(win)

        def cleanup():
            win.stop_program(None)

            tlw.stackedWidget.view.removeWidget(win)
            tlw.navigationInterface.removeWidget(win.objectName())

        tlw.stackedWidget.currentChanged.connect(lambda: cleanup())
