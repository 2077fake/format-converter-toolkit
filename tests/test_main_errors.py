"""Tests for conversion error handling in core.registry."""


import pytest
from format_converter.core.registry import run_conversion, ConversionResult, ConversionError


class TestConversionResult:
    def test_success(self):
        r = ConversionResult(True, output_path="/out.pdf")
        assert r.success is True
        assert r.output_path == "/out.pdf"
        assert r.error == ""

    def test_failure(self):
        r = ConversionResult(False, error="test error", converter="md→pdf")
        assert r.success is False
        assert r.error == "test error"
        assert r.converter == "md→pdf"


class TestRunConversion:
    """Test run_conversion error classification."""

    def test_file_not_found(self):
        """Nonexistent input file should give a FileNotFoundError result."""
        class FakeTask:
            def convert(self, *a, **kw):
                raise FileNotFoundError("no such file: /no/such/file.md")

        result = run_conversion(FakeTask(), "/no/such/file.md", "/out.pdf")
        assert result.success is False
        assert "不存在" in result.error
        assert result.converter == "FakeTask"

    def test_permission_error(self):
        """PermissionError should be caught and reported."""
        class FakeTask:
            def convert(self, *a, **kw):
                raise PermissionError("access denied")

        result = run_conversion(FakeTask(), "/in.md", "/no/write/out.pdf")
        assert result.success is False
        assert "权限" in result.error

    def test_generic_exception(self):
        """Generic exceptions are caught and reported."""
        class FakeTask:
            def convert(self, *a, **kw):
                raise ValueError("bad input")

        result = run_conversion(FakeTask(), "/in.md", "/out.pdf")
        assert result.success is False
        assert "ValueError" in result.error
        assert "bad input" in result.error

    def test_empty_error_message(self):
        """Ensure error string doesn't crash even with empty message."""
        class FakeTask:
            def convert(self, *a, **kw):
                raise RuntimeError("")

        result = run_conversion(FakeTask(), "/in.md", "/out.pdf")
        assert result.success is False
        assert result.error == "RuntimeError: "


class TestConversionError:
    """Test the ConversionError wrapper."""

    def test_preserves_name(self):
        e = ConversionError("md→pdf", ValueError("test"))
        assert e.converter_name == "md→pdf"
        assert str(e) == "test"

    def test_preserves_original(self):
        orig = KeyError("missing")
        e = ConversionError("docx→md", orig)
        assert e.original_exc is orig
