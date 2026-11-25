"""设置对话框：主题与完成后行为。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(440, 260)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)

        sec = QLabel("THEME · 主题")
        sec.setObjectName("section")
        lay.addWidget(sec)

        row = QHBoxLayout()
        self._light = QPushButton("Paper 浅色")
        self._dark = QPushButton("Ink 深色")
        group = QButtonGroup(self)
        group.setExclusive(True)
        for b in (self._light, self._dark):
            b.setCheckable(True)
            group.addButton(b)
            row.addWidget(b)
        (self._dark if config.get("theme") == "dark" else self._light).setChecked(True)
        lay.addLayout(row)

        sec2 = QLabel("BEHAVIOR · 行为")
        sec2.setObjectName("section")
        lay.addSpacing(6)
        lay.addWidget(sec2)
        self._open_after = QCheckBox("转换成功后自动打开所在文件夹")
        self._open_after.setChecked(bool(config.get("open_folder_after")))
        lay.addWidget(self._open_after)

        lay.addStretch()
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("取消")
        ok = QPushButton("保存")
        ok.setObjectName("primary")
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)

    def values(self) -> dict:
        return {
            "theme": "dark" if self._dark.isChecked() else "light",
            "open_folder_after": self._open_after.isChecked(),
        }
