"""界面组件：转换卡片、状态条、日志面板。"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout,
)

from ..core.registry import ConverterTask


def _repolish(w) -> None:
    w.style().unpolish(w)
    w.style().polish(w)


class ConverterCard(QFrame):
    """一个转换方向。点击 / 回车选择文件，或把文件拖进来。"""

    activated = Signal(object)          # task
    file_dropped = Signal(object, str)  # task, path
    drop_rejected = Signal(object, str)

    def __init__(self, task: ConverterTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAcceptDrops(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 16)
        lay.setSpacing(10)

        row = QHBoxLayout()
        tag = QLabel(task.tag)
        tag.setObjectName("tag")
        row.addWidget(tag)
        row.addStretch()
        lay.addLayout(row)

        title = QLabel(task.title)
        title.setObjectName("card_title")
        lay.addWidget(title)

        desc = QLabel(task.desc)
        desc.setObjectName("card_desc")
        desc.setWordWrap(True)
        lay.addWidget(desc, 1)

        hint = QLabel(f"点击选择 {task.src_ext} 文件，或拖入此处  →")
        hint.setObjectName("card_hint")
        lay.addWidget(hint)

    # -- 交互 --
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.task)
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.activated.emit(self.task)
        else:
            super().keyPressEvent(event)

    def _first_local_file(self, event) -> str:
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        return urls[0].toLocalFile() if urls else ""

    def _set_drop(self, on: bool) -> None:
        self.setProperty("drop", "true" if on else "false")
        _repolish(self)

    def dragEnterEvent(self, event):
        path = self._first_local_file(event)
        if path and os.path.splitext(path)[1].lower() == self.task.src_ext:
            event.acceptProposedAction()
            self._set_drop(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_drop(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_drop(False)
        path = self._first_local_file(event)
        if path and os.path.splitext(path)[1].lower() == self.task.src_ext:
            event.acceptProposedAction()
            self.file_dropped.emit(self.task, path)
        elif path:
            self.drop_rejected.emit(self.task, path)


class StatusBar(QFrame):
    """方块状态灯 + 文本 + 忙碌进度条 + “打开所在文件夹”按钮。"""

    open_folder_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("status_bar")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.pip = QLabel()
        self.pip.setObjectName("pip")
        self.text = QLabel("就绪 · 选择一个转换方向")
        self.text.setObjectName("status_text")
        self.open_btn = QPushButton("打开所在文件夹")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self.open_folder_clicked)
        row.addWidget(self.pip)
        row.addWidget(self.text, 1)
        row.addWidget(self.open_btn)
        lay.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        lay.addWidget(self.progress)
        self.set_state("idle", self.text.text())

    def set_state(self, state: str, message: str, *, show_open: bool = False) -> None:
        self.pip.setProperty("state", state)
        _repolish(self.pip)
        self.text.setText(message)
        self.progress.setVisible(state == "busy")
        self.open_btn.setVisible(show_open)


class LogPanel(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log")
        self.setReadOnly(True)
        self.setMaximumBlockCount(500)
        self.setPlaceholderText("转换记录会显示在这里")

    def add(self, line: str) -> None:
        self.appendPlainText(line)
