from dataclasses import dataclass

from loguru import logger
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)
from qfluentwidgets import Action, BodyLabel, CommandBar
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (InfoBar, InfoBarPosition, LineEdit, ListWidget,
                            MessageBoxBase, PushButton,
                            SingleDirectionScrollArea, SubtitleLabel,
                            TitleLabel, VBoxLayout, setFont)

from FluentPython.core.config import CFG, FluentPyVersion


@dataclass
class CreateEnvironmentResults:
    name: str
    interpreter_path: str


class CreateEnvironmentDialog(MessageBoxBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('新建 Python 环境')

        self.nameEdit = LineEdit()
        self.nameEdit.setPlaceholderText('新建的环境名称')
        self.nameEdit.setClearButtonEnabled(True)

        self.interpreterPathEdit = LineEdit()
        self.interpreterPathEdit.setPlaceholderText('要使用的 Python 解释器（不填为默认）')
        self.interpreterPathEdit.setClearButtonEnabled(True)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameEdit)
        self.viewLayout.addWidget(self.interpreterPathEdit)

        self.widget.setMinimumWidth(350)

    def compile(self):
        return CreateEnvironmentResults(
            name=self.nameEdit.text().strip(),
            interpreter_path=self.interpreterPathEdit.text().strip())


class PageVersions(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setObjectName("Versions")

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
        act = Action(FIF.ADD, '创建环境')
        act.triggered.connect(lambda: self.create_env())
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
                f"Versions ({self.version_list.count()})")
        else:
            self.subtitle_label.setText("Versions (no versions)")

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

            titleLabel = TitleLabel(f'修改环境 {ver.name}', self.editing_frame)
            lo.addWidget(titleLabel)

            lo.addSpacing(10)

            subtitleLabel = SubtitleLabel(
                f'环境版本 {".".join(map(str, ver.version))}', self.editing_frame)
            lo.addWidget(subtitleLabel)

            lo.addSpacing(20)

            envDirView = LineEdit()
            envDirView.setText(str(ver.envdir))
            envDirView.setReadOnly(True)
            envDirView.setCursorPosition(0)
            # envDirView.addAction(Action(FIF.COPY, '复制'),
            #                      QLineEdit.ActionPosition.TrailingPosition)
            lo.addWidget(envDirView)

            lo.addStretch()

            removeBtn = PushButton(FIF.DELETE, '移除环境', self.editing_frame)
            removeBtn.clicked.connect(lambda: self.remove_version(ver))

            lo.addWidget(removeBtn)

    def remove_version(self, ver):
        try:
            logger.info(f"remove version: {ver.name}")
            CFG.remove_environment(ver)
            self.reload_versions()

            InfoBar.success(title='成功！',
                            content=f"已移除版本 {ver.name}",
                            isClosable=True,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=1500,
                            parent=self.topLevelWidget())
        except FileNotFoundError:
            InfoBar.error(title='出错啦！',
                          content="版本已不存在",
                          isClosable=True,
                          position=InfoBarPosition.TOP_RIGHT,
                          duration=1500,
                          parent=self.topLevelWidget())
        except Exception as e:
            logger.exception(e)
            InfoBar.error(title='出错啦！',
                          content=f"移除版本 {ver.name} 失败：{e}",
                          isClosable=True,
                          position=InfoBarPosition.TOP_RIGHT,
                          duration=1500,
                          parent=self.topLevelWidget())

    def create_env(self):
        dialog = CreateEnvironmentDialog(self)
        btn_res = dialog.exec()
        if not btn_res:
            InfoBar.info(title='已取消',
                         content="创建环境已取消",
                         orient=Qt.Orientation.Horizontal,
                         isClosable=True,
                         position=InfoBarPosition.TOP_RIGHT,
                         duration=1500,
                         parent=self.topLevelWidget())
            return

        res = dialog.compile()

        if res.name:
            try:
                logger.info(f"create environment: {res.name}")
                ver = CFG.create_environment(res.name, res.interpreter_path
                                             or None)
                logger.debug(f"created version: {ver}")
                self.reload_versions()
                InfoBar.success(
                    title='成功！',
                    content=
                    f"已创建版本 {'.'.join(map(str, ver.version))} 的环境 {ver.name}",
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=1500,
                    parent=self.topLevelWidget())
            except Exception as e:
                logger.exception(e)
                InfoBar.error(title='出错啦！',
                              content=f"创建环境 {res.name} 失败：{e}",
                              isClosable=True,
                              position=InfoBarPosition.TOP_RIGHT,
                              duration=1500,
                              parent=self.topLevelWidget())
        else:
            InfoBar.warning(title='警告！',
                            content="环境名称不能为空（但是解释器路径可以）",
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP_RIGHT,
                            duration=1500,
                            parent=self.topLevelWidget())
