"""转换器注册表、CLI 与配置的测试。"""

import json

import pytest

from format_converter import cli
from format_converter.core.registry import CONVERTERS, find_task, run_conversion
from format_converter.errors import DependencyMissingError
from format_converter.ui.config import DEFAULT_CONFIG, load_config, save_config


class TestRegistry:
    def test_four_directions_unique_keys(self):
        assert len(CONVERTERS) == 4
        assert len({t.key for t in CONVERTERS}) == 4

    def test_find_task(self):
        assert find_task(".md", ".docx").key == "md2docx"
        assert find_task(".PDF", ".md").key == "pdf2md"
        assert find_task(".docx", ".pdf") is None

    @pytest.mark.parametrize("task", CONVERTERS, ids=lambda t: t.key)
    def test_converter_functions_resolve(self, task):
        assert callable(task.load())

    def test_dependency_missing_message(self):
        class T:
            title = "t"

            def convert(self, *a):
                raise DependencyMissingError("PyMuPDF", "fitz")

        r = run_conversion(T(), "a", "b")
        assert not r.success and "pip install PyMuPDF" in r.error

    def test_module_not_found_maps_pip_name(self):
        class T:
            def convert(self, *a):
                raise ModuleNotFoundError("x", name="docx")

        assert "python-docx" in run_conversion(T(), "a", "b").error


class TestCli:
    def test_md_to_docx_roundtrip(self, tmp_path, capsys):
        pytest.importorskip("docx")
        src = tmp_path / "a.md"
        src.write_text("# 标题\n\n正文 **粗体**，公式 $x^2$。\n\n- 一\n- 二\n", encoding="utf-8")
        assert cli.main(["convert", str(src), "--to", "docx"]) == 0
        out = tmp_path / "a.docx"
        assert out.exists() and out.stat().st_size > 0
        back = tmp_path / "b.md"
        assert cli.main(["convert", str(out), "--to", "md", "-o", str(back)]) == 0
        assert "标题" in back.read_text(encoding="utf-8")

    def test_missing_file(self, tmp_path):
        assert cli.main(["convert", str(tmp_path / "nope.md"), "--to", "docx"]) == 1

    def test_unsupported_direction(self, tmp_path):
        src = tmp_path / "a.md"
        src.write_text("x", encoding="utf-8")
        assert cli.main(["convert", str(src), "--to", "md"]) == 1

    def test_directory_requires_from(self, tmp_path):
        assert cli.main(["convert", str(tmp_path), "--to", "docx"]) == 2


class TestConfig:
    def test_defaults_when_missing(self, tmp_path):
        assert load_config(tmp_path / "c.json") == DEFAULT_CONFIG

    def test_roundtrip_and_invalid_theme(self, tmp_path):
        p = tmp_path / "c.json"
        save_config({"theme": "dark", "open_folder_after": True}, p)
        assert load_config(p) == {"theme": "dark", "open_folder_after": True}
        p.write_text(json.dumps({"theme": "neon"}), encoding="utf-8")
        assert load_config(p)["theme"] == "light"

    def test_corrupt_file_falls_back(self, tmp_path):
        p = tmp_path / "c.json"
        p.write_text("{not json", encoding="utf-8")
        assert load_config(p) == DEFAULT_CONFIG
