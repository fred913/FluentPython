import json
import os
import subprocess
import threading
import time
from datetime import datetime

from loguru import logger
from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar, InfoBarPosition, PushButton


class ConsoleExecutionPage(QWidget):
    terminalUpdated = Signal(str)

    def __init__(self, cmd: list[str], tipbar: str, parent=None):
        super().__init__(parent)

        self._parent = parent
        self.setObjectName('PythonConsole')

        self.text_edit = QTextEdit(self)
        self.text_edit.setFont(QFont('Consolas', 12))
        self.text_edit.setTextColor(QColor(255, 255, 255))
        self.text_edit.setStyleSheet(
            "QTextEdit { background-color: rgb(45, 45, 45); border-radius: 8px; padding: 6px; }"
        )
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText("[Runner] Not started yet")

        self.idle_text = "State: Ready, click 'Start' to run \"" + (
            tipbar or "<program>").strip() + "\""
        self.status_label = QLabel(self.idle_text, self)
        self.status_label.setFont(QFont('MiSans', 14))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignTop
                                       | Qt.AlignmentFlag.AlignLeft)

        self.button_start = PushButton(FIF.PLAY, "Start", self)
        self.button_start.clicked.connect(self.start_program)

        self.button_end = PushButton(FIF.PAUSE, "Stop", self)
        self.button_end.clicked.connect(self.stop_program)

        self.buttons = [self.button_start, self.button_end]
        for button in self.buttons:
            button.setFont(QFont('MiSans', 10))

        self.reposition()

        self.child = None
        self.stopping = False
        self.cmd = cmd

    def updateStatus(self, status: str):
        self.status_label.setText(f"State: {status}")

    def reposition(self):
        sz = self.size()
        window_width, window_height = sz.width(), sz.height()

        button_width = 180
        button_height = 42
        for i, button in enumerate(self.buttons):
            button.setGeometry(window_width - button_width - 10,
                               i * (button_height + 10) + 10, button_width,
                               button_height)

        self.text_edit.setGeometry(10, 10,
                                   window_width - button_width - 10 - 10 - 10,
                                   window_height - 70)

        self.status_label.setGeometry(10, window_height - 60 + 20,
                                      window_width - 150, 30)

    def resizeEvent(self, event):
        self.reposition()

    def start_program(self, event):
        self.child = subprocess.Popen(
            self.cmd,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            cwd=os.getcwd(),
        )

        def _():
            assert self.child is not None
            assert self.child.stdout is not None

            while self.child.poll() is None:
                try:
                    line = self.child.stdout.readline().decode('utf-8').strip()
                except UnicodeDecodeError:
                    line = self.child.stdout.readline().decode('gbk').strip()

                self.updateTerminal(line)

                if not self.stopping:
                    self.updateStatus("Running")

            self.updateTerminal(
                f"[Runner] Program stopped with code {self.child.returncode}")
            self.updateStatus(self.idle_text)

            self.child = None
            self.stopping = False

        threading.Thread(target=_, daemon=True).start()

    def stop_program(self, event):
        if self.child is not None:
            if self.stopping:
                InfoBar.warning(title="请稍等片刻",
                                content="程序已经进入中止中的状态",
                                orient=Qt.Orientation.Horizontal,
                                isClosable=True,
                                position=InfoBarPosition.TOP_RIGHT,
                                duration=1500,
                                parent=self.topLevelWidget())
                return

            self.stopping = True
            self.updateStatus("Stopping...")
            self.updateTerminal("Stopping program...")
            InfoBar.info(
                title='正在停止程序...',
                content=
                "有时 JupyterLab 会无法中止，您可以直接在左侧选择其他 Tab，开启新的 Session。（持续优化中）",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=1500,
                parent=self.topLevelWidget())

            self.child.terminate()
            time.sleep(0.5)
            self.child.kill()
            self.child.wait()

    def updateTerminal(self, text: str):
        text = text.rstrip() + '\n'

        self.text_edit.append(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {text}")
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

        # logger.debug(text)

        # Emit the terminalUpdated signal
        self.terminalUpdated.emit(text)

    def __del__(self):
        if self.child is not None:
            self.child.kill()
