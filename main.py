"""
📦 格式转换工具箱 — Qt (PySide6) 桌面应用 v4.0
现代化界面，卡片式布局，支持主题切换，拖拽转换，批量处理
"""

import sys
import os
import json
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QMessageBox,
    QFileDialog, QDialog, QGridLayout, QProgressBar, QListWidget,
    QListWidgetItem, QCheckBox, QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor, QFont, QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt, Signal, QThread, QObject, QCoreApplication

# ==================== 配置管理 ====================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conversion_history.json")

DEFAULT_CONFIG = {
    "theme": "light",
    "font_family": "Microsoft YaHei UI",
    "window_size": "medium",
    "auto_open_folder": True,
    "batch_mode": False,
}

THEME_LIGHT = {
    "bg": "#f3f3f3",
    "card_bg": "#ffffff",
    "header_bg": "#ffffff",
    "text": "#1a1a1a",
    "text_secondary": "#666666",
    "accent": "#1677ff",
    "accent_hover": "#0958d9",
    "accent_light": "#e6f4ff",
    "border": "#e0e0e0",
    "hover": "#f5f5f5",
    "success": "#52c41a",
    "error": "#ff4d4f",
    "warning": "#faad14",
    "card_shadow": "rgba(0,0,0,0.06)",
    "code_bg": "#f6f8fa",
    "input_bg": "#ffffff",
}

THEME_DARK = {
    "bg": "#1e1e1e",
    "card_bg": "#2a2a2a",
    "header_bg": "#2a2a2a",
    "text": "#e8e8e8",
    "text_secondary": "#a0a0a0",
    "accent": "#1677ff",
    "accent_hover": "#4096ff",
    "accent_light": "#1a2a3a",
    "border": "#404040",
    "hover": "#333333",
    "success": "#49aa19",
    "error": "#dc4446",
    "warning": "#d89614",
    "card_shadow": "rgba(0,0,0,0.3)",
    "code_bg": "#2a2a2a",
    "input_bg": "#1e1e1e",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            if os.path.getsize(CONFIG_FILE) > 64 * 1024:
                return dict(DEFAULT_CONFIG)
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    cfg.setdefault(k, v)
                return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            pass
    return []


def save_history(history: list):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history[-100:], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ==================== 转换器定义 ====================

class ConverterTask:
    def __init__(self, name: str, icon: str, desc: str,
                 source_ext: str, target_ext: str, convert_func):
        self.name = name
        self.icon = icon
        self.desc = desc
        self.source_ext = source_ext
        self.target_ext = target_ext
        self.convert = convert_func

    def file_filter(self) -> str:
        return f"{self.source_ext.upper()} 文件 (*{self.source_ext})"


from md_to_docx import convert_md_to_docx
from docx_to_md import convert_docx_to_md
from pdf_to_md import convert_pdf_to_md
from md_to_pdf import convert_md_to_pdf

CONVERTERS = [
    ConverterTask("Markdown → Word", "📝➜📄",
                  "将 Markdown 转为精美的 Word 文档，支持 LaTeX 公式、表格、代码块等完整 Markdown 语法",
                  ".md", ".docx", convert_md_to_docx),
    ConverterTask("Word → Markdown", "📄➜📝",
                  "将 Word 文档转为 Markdown 格式，保留标题、格式、列表、表格和超链接",
                  ".docx", ".md", convert_docx_to_md),
    ConverterTask("Markdown → PDF", "📝➜📑",
                  "将 Markdown 转为 A4 排版精美的 PDF 文档，支持中文混排",
                  ".md", ".pdf", convert_md_to_pdf),
    ConverterTask("PDF → Markdown", "📑➜📝",
                  "将 PDF 提取为 Markdown 文本，智能识别标题、格式和表格结构",
                  ".pdf", ".md", convert_pdf_to_md),
]


# ==================== 转换工作线程（线程安全） ====================

class ConversionWorker(QObject):
    finished = Signal(str, bool, str)  # output_path, success, message
    progress = Signal(str)

    def __init__(self, task: ConverterTask, input_path: str, output_path: str):
        super().__init__()
        self.task = task
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit(f"⏳ 正在转换: {os.path.basename(self.input_path)} ...")
            self.task.convert(self.input_path, self.output_path)
            self.finished.emit(self.output_path, True, "✅ 转换成功！")
        except Exception as e:
            self.finished.emit(self.output_path, False, f"❌ 转换失败: {str(e)}")


# ==================== 拖拽标签组件 ====================

class DropLabel(QLabel):
    file_dropped = Signal(str)

    def __init__(self, theme_colors: dict, parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.setAcceptDrops(True)
        self.setText("📁 拖拽文件到此处\n或点击卡片选择文件")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        self._apply_style(False)

    def _apply_style(self, active: bool):
        c = self.theme_colors
        if active:
            self.setStyleSheet(f"""
                QLabel {{
                    border: 2px dashed {c['accent']};
                    border-radius: 12px;
                    padding: 20px;
                    color: {c['accent']};
                    background: {c['accent_light']};
                    font-size: 13px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QLabel {{
                    border: 2px dashed {c['border']};
                    border-radius: 12px;
                    padding: 20px;
                    color: {c['text_secondary']};
                    background: transparent;
                    font-size: 13px;
                }}
            """)

    def update_theme(self, theme_colors: dict):
        self.theme_colors = theme_colors
        self._apply_style(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._apply_style(True)

    def dragLeaveEvent(self, event):
        self._apply_style(False)

    def dropEvent(self, event: QDropEvent):
        self._apply_style(False)
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self.file_dropped.emit(file_path)


# ==================== 卡片组件 ====================

class ConverterCard(QFrame):
    clicked = Signal(object)
    drop_file = Signal(object, str)

    def __init__(self, task: ConverterTask, theme_colors: dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.theme_colors = theme_colors
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(True)
        self._setup_ui()
        self._apply_shadow()

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(self.theme_colors["card_shadow"]))
        self.setGraphicsEffect(shadow)

    def _setup_ui(self):
        c = self.theme_colors
        self._apply_card_style(c)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)

        icon_label = QLabel(self.task.icon)
        icon_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        icon_label.setFixedWidth(50)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"color: {c['accent']}; background: transparent;")
        title_layout.addWidget(icon_label)

        name_label = QLabel(self.task.name)
        name_label.setObjectName("name_label")
        name_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {c['text']}; background: transparent;")
        title_layout.addWidget(name_label)
        title_layout.addStretch()

        # 方向标签
        direction_label = QLabel(f"{self.task.source_ext.upper()} → {self.task.target_ext.upper()}")
        direction_label.setObjectName("direction_label")
        direction_label.setFont(QFont("Microsoft YaHei UI", 9))
        direction_label.setStyleSheet(f"""
            color: {c['accent']};
            background-color: {c['accent_light']};
            padding: 4px 12px;
            border-radius: 10px;
            font-weight: bold;
        """)
        title_layout.addWidget(direction_label)

        layout.addLayout(title_layout)

        # 描述
        desc_label = QLabel(self.task.desc)
        desc_label.setObjectName("desc_label")
        desc_label.setFont(QFont("Microsoft YaHei UI", 10))
        desc_label.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        desc_label.setWordWrap(True)
        desc_label.setMinimumHeight(40)
        layout.addWidget(desc_label)

        # 拖拽提示
        drop_hint = QLabel("💡 拖拽文件到此处或点击选择")
        drop_hint.setObjectName("hint_label")
        drop_hint.setFont(QFont("Microsoft YaHei UI", 8))
        drop_hint.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        drop_hint.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(drop_hint)

    def _apply_card_style(self, c=None):
        c = c or self.theme_colors
        self.setStyleSheet(f"""
            ConverterCard {{
                background-color: {c['card_bg']};
                border-radius: 16px;
                border: 1px solid {c['border']};
            }}
        """)

    def update_theme(self, theme_colors: dict):
        self.theme_colors = theme_colors
        c = theme_colors
        self._apply_card_style(c)
        self._apply_shadow()
        # 更新子组件颜色
        for child in self.findChildren(QLabel):
            obj_name = child.objectName()
            if obj_name == "desc_label" or obj_name == "hint_label":
                child.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
            elif obj_name == "name_label":
                child.setStyleSheet(f"color: {c['text']}; background: transparent;")
            elif obj_name == "direction_label":
                child.setStyleSheet(f"""
                    color: {c['accent']};
                    background-color: {c['accent_light']};
                    padding: 4px 12px;
                    border-radius: 10px;
                    font-weight: bold;
                """)
            else:
                child.setStyleSheet(f"color: {c['accent']}; background: transparent;")

    def enterEvent(self, event):
        c = self.theme_colors
        self.setStyleSheet(f"""
            ConverterCard {{
                background-color: {c['hover']};
                border-radius: 16px;
                border: 1.5px solid {c['accent']};
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        c = self.theme_colors
        self.setStyleSheet(f"""
            ConverterCard {{
                background-color: {c['card_bg']};
                border-radius: 16px;
                border: 1px solid {c['border']};
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.task)
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(self.task.source_ext):
                    event.acceptProposedAction()
                    c = self.theme_colors
                    self.setStyleSheet(f"""
                        ConverterCard {{
                            background-color: {c['accent_light']};
                            border-radius: 16px;
                            border: 2px dashed {c['accent']};
                        }}
                    """)
                    return

    def dragLeaveEvent(self, event):
        self._apply_card_style()

    def dropEvent(self, event: QDropEvent):
        self._apply_card_style()
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(self.task.source_ext):
                self.drop_file.emit(self.task, file_path)


# ==================== 历史记录对话框 ====================

class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 转换历史")
        self.setMinimumSize(600, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("📋 最近转换记录")
        title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setWordWrap(True)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ 清除历史")
        clear_btn.clicked.connect(self._clear_history)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        self._refresh()

    def _refresh(self):
        self.list_widget.clear()
        history = load_history()
        if not history:
            self.list_widget.addItem("暂无转换记录")
            return
        for h in reversed(history):
            ts = h.get("time", "")
            src = h.get("source", "")
            dst = h.get("target", "")
            status = h.get("status", "✅")
            text = f"{status} [{ts}] {os.path.basename(src)} → {os.path.basename(dst)}"
            item = QListWidgetItem(text)
            item.setToolTip(f"源文件: {src}\n目标文件: {dst}")
            self.list_widget.addItem(item)

    def _clear_history(self):
        save_history([])
        self._refresh()


# ==================== 关于对话框 ====================

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 关于")
        self.setMinimumSize(460, 320)
        self.resize(520, 380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel("📦 文档格式互转工具箱")
        title.setFont(QFont("Microsoft YaHei UI", 17, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel("v4.0 · Qt Edition")
        version.setFont(QFont("Segoe UI", 11))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #6b7280;")
        layout.addWidget(version)

        layout.addSpacing(8)

        desc = QLabel(
            "一个跨平台的文档格式转换桌面应用。\n"
            "支持 Markdown、Word (.docx) 和 PDF 三种\n"
            "常用文档格式之间的无缝转换。\n\n"
            "🛠️ 技术栈: PySide6 + python-docx + PyMuPDF\n"
            "📝 开源协议: MIT"
        )
        desc.setFont(QFont("Microsoft YaHei UI", 10))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


# ==================== 设置对话框 ====================

class SettingsDialog(QDialog):
    def __init__(self, config: dict, theme_colors: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.theme_colors = theme_colors
        self.setWindowTitle("⚙️ 设置")
        self.setMinimumSize(480, 340)
        self.resize(520, 380)
        self._setup_ui()

    def _setup_ui(self):
        c = self.theme_colors
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("⚙️ 设置")
        title.setFont(QFont("Microsoft YaHei UI", 15, QFont.Weight.Bold))
        layout.addWidget(title)

        # 主题选择
        theme_group = QFrame()
        theme_group.setStyleSheet(f"""
            QFrame {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
        """)
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(8)
        theme_layout.setContentsMargins(12, 8, 12, 8)

        theme_label = QLabel("🎨 主题")
        theme_label.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Bold))
        theme_layout.addWidget(theme_label)

        theme_btn_layout = QHBoxLayout()
        theme_btn_layout.setSpacing(8)
        self.light_radio = QPushButton("☀️ 亮色主题")
        self.light_radio.setCheckable(True)
        self.light_radio.setMinimumHeight(36)
        self.light_radio.setStyleSheet(f"""
            QPushButton {{ padding: 6px 14px; border-radius: 6px; font-size: 12px; min-height: 28px; }}
            QPushButton:checked {{ background: {c['accent']}; color: white; border: none; font-weight: bold; }}
            QPushButton:!checked {{ background: {c['hover']}; color: {c['text']}; border: 1px solid {c['border']}; }}
        """)
        self.dark_radio = QPushButton("🌙 暗色主题")
        self.dark_radio.setCheckable(True)
        self.dark_radio.setMinimumHeight(36)
        self.dark_radio.setStyleSheet(f"""
            QPushButton {{ padding: 6px 14px; border-radius: 6px; font-size: 12px; min-height: 28px; }}
            QPushButton:checked {{ background: {c['accent']}; color: white; border: none; font-weight: bold; }}
            QPushButton:!checked {{ background: {c['hover']}; color: {c['text']}; border: 1px solid {c['border']}; }}
        """)

        self.light_radio.setChecked(self.config.get("theme") != "dark")
        self.dark_radio.setChecked(self.config.get("theme") == "dark")

        theme_btn_layout.addWidget(self.light_radio)
        theme_btn_layout.addWidget(self.dark_radio)
        theme_layout.addLayout(theme_btn_layout)
        layout.addWidget(theme_group)

        # 选项
        options_group = QFrame()
        options_group.setStyleSheet(f"""
            QFrame {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
        """)
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(8)
        options_layout.setContentsMargins(12, 8, 12, 8)

        options_label = QLabel("⚡ 其他选项")
        options_label.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Bold))
        options_layout.addWidget(options_label)

        self.auto_open_cb = QCheckBox("转换后自动打开文件所在文件夹")
        self.auto_open_cb.setChecked(self.config.get("auto_open_folder", True))
        options_layout.addWidget(self.auto_open_cb)

        layout.addWidget(options_group)
        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("✅ 保存")
        ok_btn.setMinimumHeight(34)
        ok_btn.setStyleSheet(f"padding: 6px 24px; font-size: 12px;")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(34)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 6px 24px; font-size: 12px;
                background: {c['hover']}; color: {c['text']};
                border: 1px solid {c['border']}; border-radius: 6px;
            }}
            QPushButton:hover {{ background: {c['border']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_theme(self) -> str:
        return "light" if self.light_radio.isChecked() else "dark"

    def get_auto_open(self) -> bool:
        return self.auto_open_cb.isChecked()


# ==================== 样式工具类 ====================

class StyleHelper:
    @staticmethod
    def get_theme_colors(theme_name: str) -> dict:
        return THEME_DARK if theme_name == "dark" else THEME_LIGHT

    @staticmethod
    def apply_global_stylesheet(app: QApplication, theme_name: str):
        colors = StyleHelper.get_theme_colors(theme_name)
        app.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['bg']};
            }}
            QDialog {{
                background-color: {colors['card_bg']};
            }}
            QFrame#settingGroup, QFrame#optionGroup {{
                background: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
            }}
            QLabel {{
                color: {colors['text']};
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }}
            QPushButton {{
                background-color: {colors['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {QColor(colors['accent']).darker(120).name()};
            }}
            QPushButton:disabled {{
                background-color: {colors['border']};
                color: {colors['text_secondary']};
            }}
            QProgressBar {{
                border: none;
                border-radius: 6px;
                background-color: {colors['border']};
                height: 10px;
                text-align: center;
                font-size: 9px;
            }}
            QProgressBar::chunk {{
                background-color: {colors['accent']};
                border-radius: 6px;
            }}
            QListWidget {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                color: {colors['text']};
                outline: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {colors['accent_light']};
                color: {colors['accent']};
            }}
            QListWidget::item:hover {{
                background-color: {colors['hover']};
            }}
            QCheckBox {{
                color: {colors['text']};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
                border: 2px solid {colors['border']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border-color: {colors['accent']};
            }}
            QScrollBar:vertical {{
                background-color: {colors['bg']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QScrollBar:horizontal {{
                background-color: {colors['bg']};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {colors['border']};
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors['text_secondary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
        """)


# ==================== 主窗口 ====================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.current_theme = self.config.get("theme", "light")
        self.theme_colors = StyleHelper.get_theme_colors(self.current_theme)
        self.current_workers = []
        self.recent_files = load_history()

        self.setWindowTitle("📦 文档格式互转工具箱")
        self.setMinimumSize(800, 650)
        self._setup_window_size()
        self._setup_ui()
        StyleHelper.apply_global_stylesheet(QApplication.instance(), self.current_theme)

    def _setup_window_size(self):
        sizes = {"small": (700, 550), "medium": (900, 700), "large": (1100, 850)}
        size_name = self.config.get("window_size", "medium")
        w, h = sizes.get(size_name, (900, 700))
        self.resize(w, h)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._setup_header(main_layout)

        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(32, 24, 32, 24)
        body_layout.setSpacing(16)

        self._setup_subtitle(body_layout)
        self._setup_cards(body_layout)
        self._setup_status_bar(body_layout)

        main_layout.addWidget(body_widget)

    def _setup_header(self, parent_layout):
        header = QFrame()
        c = self.theme_colors
        header.setStyleSheet(f"""
            QFrame {{
                background: {c['header_bg']};
                border-bottom: 1px solid {c['border']};
            }}
        """)
        header.setFixedHeight(64)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)

        title_label = QLabel("📦 文档格式互转工具箱")
        title_label.setFont(QFont("Microsoft YaHei UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {c['text']}; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        version_label = QLabel("v4.0")
        version_label.setFont(QFont("Segoe UI", 10))
        version_label.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        header_layout.addWidget(version_label)

        for text, slot in [("📋 历史", self.open_history),
                           ("ℹ️ 关于", self.open_about),
                           ("⚙️ 设置", self.open_settings)]:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {c['text']};
                    border: 1px solid {c['border']};
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-weight: normal;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: {c['hover']};
                    border-color: {c['accent']};
                    color: {c['accent']};
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            header_layout.addWidget(btn)

        parent_layout.addWidget(header)

    def _setup_subtitle(self, parent_layout):
        subtitle_layout = QHBoxLayout()

        subtitle = QLabel("选择一个转换方向，选取文件或拖拽到卡片即可一键转换")
        subtitle.setFont(QFont("Microsoft YaHei UI", 11))
        subtitle.setStyleSheet(f"color: {self.theme_colors['text_secondary']};")
        subtitle_layout.addWidget(subtitle)
        subtitle_layout.addStretch()

        self.batch_mode_btn = QPushButton("📂 批量模式")
        self.batch_mode_btn.setCheckable(True)
        self.batch_mode_btn.setChecked(self.config.get("batch_mode", False))
        self.batch_mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.batch_mode_btn.toggled.connect(self._on_batch_mode_toggled)
        subtitle_layout.addWidget(self.batch_mode_btn)

        parent_layout.addLayout(subtitle_layout)

    def _on_batch_mode_toggled(self, checked):
        self.config["batch_mode"] = checked
        save_config(self.config)

    def _setup_cards(self, parent_layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        scroll.setWidget(content_widget)

        grid_layout = QGridLayout(content_widget)
        grid_layout.setSpacing(16)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        self.cards = []
        for idx, task in enumerate(CONVERTERS):
            card = ConverterCard(task, self.theme_colors)
            card.clicked.connect(self.handle_conversion)
            card.drop_file.connect(self.handle_drop_file)
            row = idx // 2
            col = idx % 2
            grid_layout.addWidget(card, row, col)
            self.cards.append(card)

        # 全局拖拽区域
        drop_area = DropLabel(self.theme_colors)
        drop_area.file_dropped.connect(self.handle_global_drop)
        self.drop_area = drop_area
        grid_layout.addWidget(drop_area, (len(CONVERTERS) + 1) // 2, 0, 1, 2)

        parent_layout.addWidget(scroll, stretch=1)

    def _setup_status_bar(self, parent_layout):
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet(f"""
            QFrame {{
                background: {self.theme_colors['card_bg']};
                border-radius: 12px;
                border: 1px solid {self.theme_colors['border']};
                padding: 4px;
            }}
        """)

        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(16, 8, 16, 8)

        self.status_icon = QLabel("💡")
        self.status_icon.setFont(QFont("Segoe UI", 14))
        status_layout.addWidget(self.status_icon)

        self.status_label = QLabel("点击上方卡片或拖拽文件开始转换")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.status_label.setStyleSheet(f"color: {self.theme_colors['text_secondary']}; background: transparent;")
        status_layout.addWidget(self.status_label, stretch=1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedSize(120, 8)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        parent_layout.addWidget(self.status_frame)

    # ==================== 转换逻辑 ====================

    def handle_conversion(self, task: ConverterTask):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择源文件 — {task.name}",
            os.path.expanduser("~\\Desktop"),
            f"{task.file_filter()};;所有文件 (*.*)"
        )
        if file_path:
            self._start_conversion(task, file_path)

    def handle_drop_file(self, task: ConverterTask, file_path: str):
        self._start_conversion(task, file_path)

    def handle_global_drop(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        for task in CONVERTERS:
            if task.source_ext == ext:
                self._start_conversion(task, file_path)
                return
        QMessageBox.warning(self, "不支持的文件",
                            f"不支持的文件格式: {ext}\n\n支持的格式: .md, .docx, .pdf")

    def _start_conversion(self, task: ConverterTask, file_path: str):
        if self.config.get("batch_mode", False):
            self._start_batch_conversion(task, file_path)
            return

        default_name = os.path.splitext(os.path.basename(file_path))[0] + task.target_ext
        default_path = os.path.join(os.path.dirname(file_path), default_name)

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            f"保存为 {task.target_ext.upper()} 文件",
            default_path,
            f"{task.target_ext.upper()} 文件 (*{task.target_ext});;所有文件 (*.*)"
        )
        if out_path:
            self._run_single_conversion(task, file_path, out_path)

    def _start_batch_conversion(self, task: ConverterTask, first_file: str):
        folder = os.path.dirname(first_file)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            f"选择多个 {task.source_ext.upper()} 文件",
            folder,
            f"{task.file_filter()};;所有文件 (*.*)"
        )
        if not files:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "选择输出文件夹", folder)
        if not output_dir:
            return

        self.status_icon.setText("⏳")
        self.status_label.setText(f"⏳ 批量转换 {len(files)} 个文件中...")
        self.progress_bar.setRange(0, len(files))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QCoreApplication.processEvents()

        def batch_worker():
            success_count = 0
            for i, f in enumerate(files):
                try:
                    name = os.path.splitext(os.path.basename(f))[0] + task.target_ext
                    out = os.path.join(output_dir, name)
                    task.convert(f, out)
                    success_count += 1
                except Exception:
                    pass
                finally:
                    self.progress_bar.setValue(i + 1)
                    self.status_label.setText(f"⏳ 批量转换中... ({i + 1}/{len(files)})")
                    QCoreApplication.processEvents()

            self.progress_bar.setVisible(False)
            msg = f"✅ 批量转换完成！共 {success_count} 个文件"
            self.status_label.setText(msg)
            self.status_icon.setText("✅")
            self._add_to_history(files[0], output_dir, True, f"批量转换 {success_count} 个文件")
            if self.config.get("auto_open_folder", True):
                try:
                    os.startfile(output_dir)
                except Exception:
                    pass

        threading.Thread(target=batch_worker, daemon=True).start()

    def _run_single_conversion(self, task: ConverterTask, file_path: str, out_path: str):
        self.status_icon.setText("⏳")
        self.status_label.setText(f"⏳ 正在转换: {os.path.basename(file_path)} ...")
        self.status_label.setStyleSheet(f"color: {self.theme_colors['accent']}; background: transparent;")
        self.progress_bar.setVisible(True)
        QCoreApplication.processEvents()

        # 使用 QThread + Worker 确保线程安全
        self.thread = QThread()
        self.worker = ConversionWorker(task, file_path, out_path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_conversion_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_conversion_finished(self, output_path: str, success: bool, message: str):
        self.progress_bar.setVisible(False)

        if success:
            self.status_icon.setText("✅")
            self.status_label.setText(message)
            self.status_label.setStyleSheet(
                f"color: {self.theme_colors['success']}; background: transparent;")
            self._add_to_history(output_path, output_path, True, "")

            reply = QMessageBox.question(
                self, "✅ 转换成功",
                f"文件已保存到:\n{output_path}\n\n是否打开所在文件夹？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.startfile(os.path.dirname(output_path))
                except Exception:
                    pass
        else:
            self.status_icon.setText("❌")
            self.status_label.setText("❌ 转换失败")
            self.status_label.setStyleSheet(
                f"color: {self.theme_colors['error']}; background: transparent;")
            self._add_to_history(output_path, output_path, False, message)
            QMessageBox.critical(self, "❌ 转换失败", f"错误详情:\n\n{message}")

    def _add_to_history(self, source: str, target: str, success: bool, note: str = ""):
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "target": target,
            "status": "✅" if success else "❌",
            "note": note,
        }
        self.recent_files.append(entry)
        save_history(self.recent_files)

    # ==================== 对话框 ====================

    def open_settings(self):
        dialog = SettingsDialog(self.config, self.theme_colors, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_theme = dialog.get_theme()
            new_auto_open = dialog.get_auto_open()

            if new_theme != self.current_theme:
                self.current_theme = new_theme
                self.theme_colors = StyleHelper.get_theme_colors(self.current_theme)
                StyleHelper.apply_global_stylesheet(QApplication.instance(), self.current_theme)
                self._update_all_widgets_theme()
                self.config["theme"] = self.current_theme

            self.config["auto_open_folder"] = new_auto_open
            save_config(self.config)
            self.status_icon.setText("⚙️")
            self.status_label.setText("⚙️ 设置已保存")
            self.status_label.setStyleSheet(
                f"color: {self.theme_colors['text_secondary']}; background: transparent;")

    def _update_all_widgets_theme(self):
        c = self.theme_colors
        for card in self.cards:
            card.update_theme(c)
        self.drop_area.update_theme(c)
        self.status_frame.setStyleSheet(f"""
            QFrame {{
                background: {c['card_bg']};
                border-radius: 12px;
                border: 1px solid {c['border']};
                padding: 4px;
            }}
        """)
        self.status_label.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")

    def open_history(self):
        dialog = HistoryDialog(self)
        dialog.exec()

    def open_about(self):
        dialog = AboutDialog(self)
        dialog.exec()


# ==================== 入口 ====================

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 9))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
