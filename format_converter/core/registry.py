"""转换器注册表与统一的执行入口（GUI 与 CLI 共用，不依赖 Qt）。"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable

from ..errors import ConversionError, DependencyMissingError

# import 名 -> pip 包名
_PIP_NAMES = {"docx": "python-docx", "fitz": "PyMuPDF"}


@dataclass(frozen=True)
class ConverterTask:
    """一个转换方向。convert 函数按需懒加载，缺依赖时不影响程序启动。"""

    key: str
    title: str
    tag: str
    desc: str
    src_ext: str
    tgt_ext: str
    module: str
    func: str

    def file_filter(self) -> str:
        return f"{self.src_ext.upper().lstrip('.')} 文件 (*{self.src_ext})"

    def load(self) -> Callable[..., str]:
        mod = importlib.import_module(f"format_converter.converters.{self.module}")
        return getattr(mod, self.func)

    def convert(self, src: str, dst: str | None = None) -> str:
        return self.load()(src, dst)


CONVERTERS: tuple[ConverterTask, ...] = (
    ConverterTask(
        "md2docx", "Markdown → Word", "MD → DOCX",
        "把 Markdown 转为排版规整的 Word 文档，支持 LaTeX 公式、表格、代码块与超链接。",
        ".md", ".docx", "md_to_docx", "convert_md_to_docx"),
    ConverterTask(
        "docx2md", "Word → Markdown", "DOCX → MD",
        "把 Word 文档转为 Markdown，保留标题、粗斜体、列表、表格与超链接。",
        ".docx", ".md", "docx_to_md", "convert_docx_to_md"),
    ConverterTask(
        "md2pdf", "Markdown → PDF", "MD → PDF",
        "把 Markdown 转为 A4 版式的 PDF，支持中英文混排与自动分页。",
        ".md", ".pdf", "md_to_pdf", "convert_md_to_pdf"),
    ConverterTask(
        "pdf2md", "PDF → Markdown", "PDF → MD",
        "从 PDF 提取文本为 Markdown，自动识别标题、格式与表格结构。",
        ".pdf", ".md", "pdf_to_md", "convert_pdf_to_md"),
)


def find_task(src_ext: str, tgt_ext: str) -> ConverterTask | None:
    src, tgt = src_ext.lower(), tgt_ext.lower()
    for t in CONVERTERS:
        if t.src_ext == src and t.tgt_ext == tgt:
            return t
    return None


@dataclass
class ConversionResult:
    """转换结果，便于在 UI 线程中处理。"""

    success: bool
    output_path: str = ""
    error: str = ""
    converter: str = ""


def run_conversion(task, file_path: str, out_path: str) -> ConversionResult:
    """执行转换，捕获所有异常并返回结构化结果（可在后台线程调用）。"""
    name = getattr(task, "title", None) or type(task).__name__
    try:
        result = task.convert(file_path, out_path)
        return ConversionResult(True, output_path=str(result) if result else out_path, converter=name)
    except FileNotFoundError:
        return ConversionResult(False, error=f"源文件不存在: {file_path}", converter=name)
    except PermissionError:
        return ConversionResult(False, error=f"权限不足，无法写入: {out_path}", converter=name)
    except DependencyMissingError as e:
        return ConversionResult(
            False, error=f"缺少依赖库 ({e.package}): 请运行 pip install {e.package}", converter=name)
    except ModuleNotFoundError as e:
        pkg = _PIP_NAMES.get(e.name or "", e.name)
        return ConversionResult(False, error=f"缺少依赖库 ({pkg}): 请运行 pip install {pkg}", converter=name)
    except Exception as e:  # noqa: BLE001 - 需要把任意错误展示给用户
        return ConversionResult(False, error=f"{type(e).__name__}: {e}", converter=name)


__all__ = [
    "CONVERTERS", "ConverterTask", "ConversionResult", "ConversionError",
    "find_task", "run_conversion",
]
