import socket
import subprocess
from dataclasses import dataclass

from loguru import logger
from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)
from qfluentwidgets import Action, BodyLabel, CommandBar
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (FluentWindow, InfoBar, InfoBarPosition, LineEdit,
                            ListWidget, MessageBox, MessageBoxBase, PushButton,
                            SingleDirectionScrollArea, SubtitleLabel,
                            TitleLabel, VBoxLayout, setFont)

from FluentPython.core.config import CFG, FluentPyVersion
from FluentPython.gui.console import ConsoleExecutionPage


def select_first_unused_port_from(start_port: int):
    p = start_port

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', p))
                return p
            except OSError:
                p += 1


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

        self.clipboard = QApplication.clipboard()

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

            colabBtn = PushButton("启动 Colab 本地运行时")
            colabBtn.clicked.connect(lambda: self.start_colab(ver))
            lo.addWidget(colabBtn)

    def start_jupyter_lab(self, ver: FluentPyVersion):
        # test if jupyterlab is installed
        installed = False
        try:
            subprocess.check_output(
                [ver.py_executable, "-m", "jupyterlab", "--version"])
            logger.info("JupyterLab is already installed")
            installed = True
        except subprocess.CalledProcessError:
            pass

        if not installed:
            w = MessageBox("警告", "JupyterLab 未安装，是否现在安装？（确认后请等候一下，完成后对话框自动关闭）",
                           self.topLevelWidget())

            if w.exec():
                InfoBar.info(title='安装中',
                             content="正在安装 JupyterLab，请等待...",
                             orient=Qt.Orientation.Horizontal,
                             isClosable=True,
                             position=InfoBarPosition.BOTTOM_LEFT,
                             duration=100,
                             parent=self.topLevelWidget())

                cmd = [
                    ver.py_executable, "-m", "pip", "install", "jupyterlab",
                    "--index", "https://pypi.tuna.tsinghua.edu.cn/simple"
                ]
                logger.debug(f"Running command: {cmd}")
                subprocess.check_output(cmd)

                InfoBar.success(title='安装成功',
                                content="JupyterLab 安装成功，将启动 Jupyter Lab...",
                                orient=Qt.Orientation.Horizontal,
                                isClosable=True,
                                position=InfoBarPosition.BOTTOM_LEFT,
                                duration=1500,
                                parent=self.topLevelWidget())
            else:
                InfoBar.info(title='已取消',
                             content="已取消安装，请手动安装 JupyterLab 后再试。",
                             orient=Qt.Orientation.Horizontal,
                             isClosable=True,
                             position=InfoBarPosition.BOTTOM_LEFT,
                             duration=2000,
                             parent=self.topLevelWidget())
                return

        cmd = [ver.py_executable, "-m", "jupyter", "lab"]
        logger.debug(f"Running command: {cmd}")

        win = ConsoleExecutionPage(
            cmd,
            tipbar=f"JupyterLab[{ver.name}, {'.'.join(map(str, ver.version))}]",
            parent=self.topLevelWidget())

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

    def start_colab(self, ver: FluentPyVersion):
        # test if jupyterlab is installed
        installed = False
        try:
            subprocess.check_output(
                [ver.py_executable, "-m", "jupyterlab", "--version"])
            logger.info("JupyterLab is already installed")
            installed = True
        except subprocess.CalledProcessError:
            pass

        if not installed:
            w = MessageBox("警告", "JupyterLab 未安装，是否现在安装？（确认后请等候一下，完成后对话框自动关闭）",
                           self.topLevelWidget())

            if w.exec():
                InfoBar.info(title='安装中',
                             content="正在安装 JupyterLab，请等待...",
                             orient=Qt.Orientation.Horizontal,
                             isClosable=True,
                             position=InfoBarPosition.BOTTOM_LEFT,
                             duration=100,
                             parent=self.topLevelWidget())

                cmd = [
                    ver.py_executable, "-m", "pip", "install", "jupyterlab",
                    "--index", "https://pypi.tuna.tsinghua.edu.cn/simple"
                ]
                logger.debug(f"Running command: {cmd}")
                subprocess.check_output(cmd)

                InfoBar.success(title='安装成功',
                                content="JupyterLab 安装成功",
                                orient=Qt.Orientation.Horizontal,
                                isClosable=True,
                                position=InfoBarPosition.BOTTOM_LEFT,
                                duration=1500,
                                parent=self.topLevelWidget())
            else:
                InfoBar.info(title='已取消',
                             content="已取消安装，请手动安装 JupyterLab 后再试。",
                             orient=Qt.Orientation.Horizontal,
                             isClosable=True,
                             position=InfoBarPosition.BOTTOM_LEFT,
                             duration=2000,
                             parent=self.topLevelWidget())
                return

        port = select_first_unused_port_from(8888)

        cmd = [
            ver.py_executable, "-m", "jupyter", "notebook",
            "--NotebookApp.allow_origin='https://colab.research.google.com'",
            f"--port={port}", "--no-browser"
        ]
        logger.debug(f"Running command: {cmd}")

        win = ConsoleExecutionPage(
            cmd,
            tipbar=f"ColabRt[{ver.name}, {'.'.join(map(str, ver.version))}]",
            parent=self.topLevelWidget())

        win.setObjectName("ColabRt-tmp123")

        tlw = self.topLevelWidget()
        assert isinstance(tlw, FluentWindow), "Invalid top level widget"
        tlw.addSubInterface(win, FIF.CODE, "[TMP] Colab Local Runtime")
        tlw.switchTo(win)

        tlw.stackedWidget.currentChanged.connect(lambda: cleanup())

        win.updateTerminal("【提示】启动后，复制连接地址到 Google Colab 即可连接本地运行时。")
        win.updateTerminal("【提示 2.0】运行时就绪后会出现一条通知，自动复制连接地址。提示出现后放心粘贴即可。")

        def _termhandler(data: str):
            logger.debug(f"Terminal output: {data}".strip())
            if data.startswith("http://localhost:") and "?token=" in data:
                data = data.replace("/tree", "/")
                data = data.replace("/lab", "/")
                self.clipboard.setText(data)
                InfoBar.success(title='启动成功',
                                content="连接成功，连接地址已复制到剪贴板。",
                                orient=Qt.Orientation.Horizontal,
                                isClosable=True,
                                position=InfoBarPosition.BOTTOM_LEFT,
                                duration=1500,
                                parent=self.topLevelWidget())
                win.updateTerminal("【提示】连接成功，连接地址已复制到剪贴板。")

        win.terminalUpdated.connect(_termhandler)

        def cleanup():
            win.stop_program(None)

            tlw.stackedWidget.view.removeWidget(win)
            tlw.navigationInterface.removeWidget(win.objectName())
