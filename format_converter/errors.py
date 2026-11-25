"""转换流程中使用的异常类型。"""

from __future__ import annotations


class ConversionError(Exception):
    """包装转换过程中产生的异常，保留转换器名称与原始异常。"""

    def __init__(self, converter_name: str, original_exc: Exception):
        self.converter_name = converter_name
        self.original_exc = original_exc
        super().__init__(str(original_exc))


class DependencyMissingError(Exception):
    """缺少可选依赖库（如 PyMuPDF）。"""

    def __init__(self, package: str, module: str | None = None):
        self.package = package
        self.module = module or package
        super().__init__(f"缺少依赖库 {package}")
