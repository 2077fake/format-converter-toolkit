"""主窗口。转换在线程池中执行，结果通过信号回到界面线程。"""

from __future__ import annotations

import os
import time

from PySide6.QtCore import Qt, QObject, QRunnable, QStandardPaths, QThreadPool, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .._version import __version__
from ..core.registry import CONVERTERS, ConversionResult, ConverterTask, run_conversion
from .config import load_config, save_config
from .settings_dialog import SettingsDialog
from .theme import build_stylesheet
from .widgets import ConverterCard, LogPanel, StatusBar


class _Signals(QObject):
    done = Signal(object)  # ConversionResult


class _Worker(QRunnable):
    def __init__(self, task: ConverterTask, src: str, dst: str):
        super().__init__()
        self.task, self.src, self.dst = task, src, dst
        self.signals = _Signals()

    def run(self) -> None:
        self.signals.done.emit(run_conversion(self.task, self.src, self.dst))


class MainWindow(QMainWindow):
    def __init__(self, config: dict | None = None):
        super().__init__()
        self.config = config if config is not None else load_config()
        self._busy = False
        self._last_output = ""
        self._pool = QThreadPool.globalInstance()
        self._workers: set[_Worker] = set()

        self.setWindowTitle("格式转换工具箱")
        self.setMinimumSize(860, 660)
        self._build_ui()
        self.apply_theme()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(16)

        head = QHBoxLayout()
        head.setSpacing(12)
        mark = QLabel("FC")
        mark.setObjectName("mark")
        mark.setFixedSize(38, 38)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand = QLabel("格式转换工具箱")
        brand.setObjectName("brand")
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("version")
        settings = QPushButton("设置")
        settings.clicked.connect(self.open_settings)
        head.addWidget(mark)
        head.addWidget(brand)
        head.addWidget(ver)
        head.addStretch()
        head.addWidget(settings)
        outer.addLayout(head)

        sub = QLabel("Markdown · Word · PDF 互转。选一个方向，点击或拖入文件即可。")
        sub.setObjectName("subtitle")
        outer.addWidget(sub)

        sec = QLabel("CONVERT · 转换方向")
        sec.setObjectName("section")
        outer.addWidget(sec)

        grid = QGridLayout()
        grid.setSpacing(14)
        self.cards: list[ConverterCard] = []
        for i, task in enumerate(CONVERTERS):
            card = ConverterCard(task)
            card.activated.connect(self.start_with_dialog)
            card.file_dropped.connect(self.start_with_file)
            card.drop_rejected.connect(self._on_drop_rejected)
            grid.addWidget(card, i // 2, i % 2)
            self.cards.append(card)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        outer.addLayout(grid, 1)

        self.status = StatusBar()
        self.status.open_folder_clicked.connect(self._open_output_folder)
        outer.addWidget(self.status)

        self.log = LogPanel()
        self.log.setFixedHeight(110)
        outer.addWidget(self.log)

    def apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(build_stylesheet(self.config.get("theme", "light")))

    # ---------- 设置 ----------
    def open_settings(self) -> None:
        dlg = SettingsDialog(self.config, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.config.update(dlg.values())
            save_config(self.config)
            self.apply_theme()
            self.status.set_state("idle", "设置已保存")

    # ---------- 转换流程 ----------
    def start_with_dialog(self, task: ConverterTask) -> None:
        if self._busy:
            self.status.set_state("busy", "正在转换，请等待当前任务完成")
            return
        desktop = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)
        src, _ = QFileDialog.getOpenFileName(
            self, f"选择源文件 — {task.title}", desktop,
            f"{task.file_filter()};;所有文件 (*.*)")
        if src:
            self.start_with_file(task, src)

    def start_with_file(self, task: ConverterTask, src: str) -> None:
        if self._busy:
            self.status.set_state("busy", "正在转换，请等待当前任务完成")
            return
        default = os.path.splitext(src)[0] + task.tgt_ext
        dst, _ = QFileDialog.getSaveFileName(
            self, f"保存为 {task.tgt_ext}", default,
            f"{task.tgt_ext.upper().lstrip('.')} 文件 (*{task.tgt_ext});;所有文件 (*.*)")
        if not dst:
            return
        self._busy = True
        self._t0 = time.monotonic()
        self.status.set_state("busy", f"正在转换 {os.path.basename(src)} …")
        self.log.add(f"▶ {task.tag}  {src}")
        worker = _Worker(task, src, dst)
        worker.signals.done.connect(lambda r, w=worker: self._on_done(r, w))
        self._workers.add(worker)
        self._pool.start(worker)

    def _on_done(self, result: ConversionResult, worker: _Worker) -> None:
        self._workers.discard(worker)
        self._busy = False
        cost = time.monotonic() - getattr(self, "_t0", time.monotonic())
        if result.success:
            self._last_output = result.output_path
            self.status.set_state("ok", f"转换成功 · {os.path.basename(result.output_path)} · {cost:.1f}s",
                                  show_open=True)
            self.log.add(f"✔ {result.output_path}")
            if self.config.get("open_folder_after"):
                self._open_output_folder()
        else:
            self.status.set_state("err", "转换失败")
            self.log.add(f"✘ {result.converter}: {result.error}")
            QMessageBox.critical(self, "转换失败", f"转换器: {result.converter}\n错误: {result.error}")

    def _on_drop_rejected(self, task: ConverterTask, path: str) -> None:
        self.status.set_state("err", f"{task.title} 只接受 {task.src_ext} 文件")

    def _open_output_folder(self) -> None:
        if self._last_output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self._last_output)))
