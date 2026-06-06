"""
格式转换工具箱 — Qt (PySide6) 桌面应用
现代化界面，卡片式布局，支持主题切换
双击运行或: python main.py
"""

import sys
import os
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QMessageBox,
    QFileDialog, QDialog, QFormLayout, QDialogButtonBox,
    QGridLayout, QLineEdit, QComboBox
)
from PySide6.QtGui import QPainter, QPalette, QColor, QFont, QPaintEvent
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QPoint, QEasingCurve, QSize

# ==================== 配置管理 ====================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")

DEFAULT_CONFIG = {
    "theme": "light",
    "font_family": "Microsoft YaHei UI",
    "window_size": "medium",
}

THEME_LIGHT = {
    "bg": "#f5f7fa",
    "card_bg": "#ffffff",
    "text": "#1a1a2e",
    "text_secondary": "#6b7280",
    "accent": "#1a56db",
    "border": "#e5e7eb",
    "hover": "#f0f4ff",
    "success": "#10b981",
    "error": "#ef4444",
}

THEME_DARK = {
    "bg": "#1a1a2e",
    "card_bg": "#16213e",
    "text": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "accent": "#3b82f6",
    "border": "#2d3748",
    "hover": "#1e3a8a",
    "success": "#10b981",
    "error": "#f87171",
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


# ==================== 样式工具类 ====================

class StyleHelper:
    @staticmethod
    def get_theme_colors(theme_name: str) -> dict:
        if theme_name == "dark":
            return THEME_DARK
        return THEME_LIGHT

    @staticmethod
    def apply_global_stylesheet(app: QApplication, theme_name: str):
        colors = StyleHelper.get_theme_colors(theme_name)
        app.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['bg']};
            }}
            QLabel {{
                color: {colors['text']};
                font-family: 'Microsoft YaHei UI';
            }}
            QPushButton {{
                background-color: {colors['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Microsoft YaHei UI';
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {QColor(colors['accent']).darker(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(colors['accent']).darker(120).name()};
            }}
            QDialog {{
                background-color: {colors['bg']};
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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
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
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)


# ==================== 卡片组件 ====================

class ConverterCard(QFrame):
    clicked = Signal(object)

    def __init__(self, task: ConverterTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)

        icon_label = QLabel(self.task.icon)
        icon_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        icon_label.setStyleSheet(f"color: {'#1a56db' if self.parent() and hasattr(self.parent(), 'theme_colors') else '#1a56db'};")
        title_layout.addWidget(icon_label)

        name_label = QLabel(self.task.name)
        name_label.setFont(QFont("Microsoft YaHei UI", 13, QFont.Weight.Bold))
        name_label.setObjectName("converter_name")
        title_layout.addWidget(name_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 描述
        desc_label = QLabel(self.task.desc)
        desc_label.setFont(QFont("Microsoft YaHei UI", 9))
        desc_label.setObjectName("converter_desc")
        desc_label.setWordWrap(True)
        desc_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(desc_label)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f4ff;
                border-radius: 12px;
                border: 2px solid #1a56db;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.task)
        super().mousePressEvent(event)


# ==================== 设置对话框 ====================

class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("⚙️ 设置")
        self.setFixedSize(500, 320)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 主题选择
        theme_label = QLabel("🎨 主题")
        theme_label.setFont(QFont("Microsoft YaHei UI", 11, QFont.Weight.Bold))
        layout.addWidget(theme_label)

        theme_layout = QHBoxLayout()
        self.light_radio = QPushButton("☀️ 亮色")
        self.light_radio.setCheckable(True)
        self.dark_radio = QPushButton("🌙 暗色")
        self.dark_radio.setCheckable(True)
        if self.config.get("theme") == "light":
            self.light_radio.setChecked(True)
        else:
            self.dark_radio.setChecked(True)
        theme_layout.addWidget(self.light_radio)
        theme_layout.addWidget(self.dark_radio)
        layout.addLayout(theme_layout)

        layout.addSpacing(10)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_theme(self) -> str:
        if self.light_radio.isChecked():
            return "light"
        return "dark"


# ==================== 主窗口 ====================

class ConversionError(Exception):
    """包装转换过程中产生的异常，保留错误信息。"""

    def __init__(self, converter_name: str, original_exc: Exception):
        self.converter_name = converter_name
        super().__init__(str(original_exc))
        self.original_exc = original_exc


class _ConversionResult:
    """Worker 返回值，用于在主线程中处理结果。"""
    def __init__(self, success: bool, output_path: str = "", error: str = "", converter: str = ""):
        self.success = success
        self.output_path = output_path
        self.error = error
        self.converter = converter


def _run_conversion(task: ConverterTask, file_path: str, out_path: str) -> _ConversionResult:
    """在后台线程中运行转换，捕获所有异常并返回结构化结果。"""
    converter_name = getattr(task, 'name', type(task).__name__)
    try:
        result_path = task.convert(file_path, out_path)
        return _ConversionResult(True, output_path=str(result_path) if result_path else out_path, converter=converter_name)
    except FileNotFoundError:
        return _ConversionResult(False, error=f"源文件不存在: {file_path}", converter=converter_name)
    except PermissionError:
        return _ConversionResult(False, error=f"权限不足，无法写入: {out_path}", converter=converter_name)
    except ModuleNotFoundError as e:
        return _ConversionResult(False, error=f"缺少依赖库 ({e.name}): 请运行 pip install {e.name}", converter=converter_name)
    except Exception as e:
        return _ConversionResult(False, error=f"{type(e).__name__}: {e}", converter=converter_name)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.current_theme = self.config.get("theme", "light")
        self.theme_colors = StyleHelper.get_theme_colors(self.current_theme)
        self._converting = False
        self.setWindowTitle("📦 文档格式互转工具箱")
        self.setMinimumSize(700, 550)
        self.setup_ui()
        StyleHelper.apply_global_stylesheet(QApplication.instance(), self.current_theme)

    def _is_converting(self) -> bool:
        return self._converting

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_label = QLabel("📦 文档格式互转工具箱")
        title_label.setFont(QFont("Microsoft YaHei UI", 20, QFont.Weight.Bold))
        title_label.setObjectName("converter_name")
        header_layout.addWidget(title_label)

        version_label = QLabel("v3.0 · Qt Edition")
        version_label.setFont(QFont("Segoe UI", 9))
        version_label.setObjectName("converter_desc")
        header_layout.addStretch()
        header_layout.addWidget(version_label)

        settings_btn = QPushButton("⚙️ 设置")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(settings_btn)

        main_layout.addLayout(header_layout)

        # 副标题
        subtitle = QLabel("选择一个转换方向，选取文件即可一键转换")
        subtitle.setFont(QFont("Microsoft YaHei UI", 10))
        subtitle.setObjectName("converter_desc")
        main_layout.addWidget(subtitle)

        # 可滚动卡片区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        scroll.setWidget(content_widget)

        layout = QVBoxLayout(content_widget)
        layout.setSpacing(16)

        # 卡片网格（垂直排列）
        for task in CONVERTERS:
            card = ConverterCard(task)
            card.clicked.connect(self.handle_conversion)
            layout.addWidget(card)

        layout.addStretch()
        main_layout.addWidget(scroll)

        # 底部状态
        self.status_label = QLabel("💡 点击上方卡片开始转换")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.status_label.setObjectName("converter_desc")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_theme = dialog.get_theme()
            if new_theme != self.current_theme:
                self.current_theme = new_theme
                self.theme_colors = StyleHelper.get_theme_colors(self.current_theme)
                StyleHelper.apply_global_stylesheet(QApplication.instance(), self.current_theme)
                self.config["theme"] = self.current_theme
                save_config(self.config)
                self.status_label.setText("⚙️ 主题已切换")

    def handle_conversion(self, task: ConverterTask):
        if self._is_converting():
            QMessageBox.warning(self, "请稍候", "正在转换中，请等待当前任务完成。")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择源文件 — {task.name}",
            os.path.expanduser("~\\Desktop"),
            f"{task.file_filter()};;所有文件 (*.*)"
        )
        if not file_path:
            return

        default_path = os.path.splitext(file_path)[0] + task.target_ext
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            f"保存为 {task.target_ext}",
            default_path,
            f"{task.target_ext.upper()} 文件 (*{task.target_ext});;所有文件 (*.*)"
        )
        if not out_path:
            return

        self._converting = True
        self.status_label.setText(f"⏳ 正在转换: {os.path.basename(file_path)} ...")
        self.status_label.setStyleSheet("color: #1a56db;")

        def worker():
            result = _run_conversion(task, file_path, out_path)
            # 使用 invokeMethod 确保在主线程中回调
            QMetaObject.invokeMethod(
                self, "_on_conversion_done",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(object, result)
            )

        threading.Thread(target=worker, daemon=True).start()

    def _on_conversion_done(self, result: _ConversionResult):
        """转换完成后的主线程回调"""
        self._converting = False

        if result.success:
            self.status_label.setText("✅ 转换成功！")
            self.status_label.setStyleSheet("color: #10b981;")
            QMessageBox.information(
                self, "转换成功",
                f"✅ 文件已保存到:\n{result.output_path}"
            )
        else:
            self.status_label.setText("❌ 转换失败")
            self.status_label.setStyleSheet("color: #ef4444;")
            detail = f"转换器: {result.converter}\n错误: {result.error}"
            QMessageBox.critical(self, "转换失败", detail)


# ==================== 入口 ====================

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 9))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
