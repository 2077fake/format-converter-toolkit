"""Unit tests for Markdown parsing functions."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from md_to_docx import (
    parse_markdown as parse_md_docx,
    _merge_display_math as merge_math_docx,
)
from md_to_pdf import (
    parse_markdown as parse_md_pdf,
    _merge_display_math as merge_math_pdf,
    _parse_inline as parse_inline_pdf,
    _emit_plain_segments as emit_plain_pdf,
)


class TestMergeDisplayMath:
    def test_single_line(self):
        assert merge_math_docx(["$$E = mc^2$$"]) == ["$$E = mc^2$$"]

    def test_multiline(self):
        r = merge_math_docx(["text", "$$", "E=mc^2", "$$", "text2"])
        assert len(r) == 3 and "E=mc^2" in r[1]

    def test_no_math(self):
        assert merge_math_docx(["a", "b"]) == ["a", "b"]

    def test_inline_unaffected(self):
        assert merge_math_docx(["$x+y$"]) == ["$x+y$"]

    def test_empty_display(self):
        r = merge_math_docx(["$$", "x + y", "$$"])
        assert len(r) == 1 and "x + y" in r[0]

    def test_leading_trailing_ws(self):
        r = merge_math_docx(["  $$E=mc^2$$  "])
        assert r == ["$$E=mc^2$$"]


class TestParseMarkdownDocx:
    def _run(self, parser, name=""):
        assert parser([]) == [], f"[{name}] empty"

        e = parser(["# H1", "## H2", "### H3"])
        assert len(e) == 3
        assert e[0] == {'type': 'heading', 'level': 1, 'text': 'H1'}
        assert e[1] == {'type': 'heading', 'level': 2, 'text': 'H2'}
        assert e[2] == {'type': 'heading', 'level': 3, 'text': 'H3'}

        e = parser(["$$E=mc^2$$"])
        assert e[0] == {'type': 'display_math', 'tex': 'E=mc^2'}

        e = parser(['```python', "print('hi')", '```'])
        assert e[0]['type'] == 'code_block'
        assert e[0]['lang'] == 'python'

        e = parser(["---"])
        assert e[0]['type'] == 'hr'
        e = parser(["***"])
        assert e[0]['type'] == 'hr'

        e = parser(["- a", "- b"])
        assert e[0]['type'] == 'ul' and len(e[0]['items']) == 2

        e = parser(["1. a", "2. b"])
        assert e[0]['type'] == 'ol' and len(e[0]['items']) == 2

        e = parser(["> quote"])
        assert e[0]['type'] == 'blockquote'

        # Table: parser only collects lines containing |, separator line has no |
        e = parser(["| H1 | H2 |", "|---|---|", "| A | B |"])
        assert e[0]['type'] == 'table'
        assert len(e[0]['rows']) == 2  # header + data; separator row is skipped

        e = parser(["Hello world"])
        assert e[0]['type'] == 'paragraph' and e[0]['text'] == 'Hello world'

        e = parser(["First", "", "Second"])
        assert len(e) == 2

        e = parser(["###### H6"])
        assert e[0]['level'] == 6

        e = parser(["* star", "+ plus", "- dash"])
        assert e[0]['type'] == 'ul' and len(e[0]['items']) == 3

        e = parser(["", "", "content", "", ""])
        assert len(e) == 1 and e[0]['type'] == 'paragraph'

        e = parser(['```', 'code', '```'])
        assert e[0]['lang'] == ''

    def test_docx(self):
        self._run(parse_md_docx, "docx")

    def test_pdf(self):
        self._run(parse_md_pdf, "pdf")


class TestParseInlinePdf:
    def test_plain(self):
        types = [s[0] for s in parse_inline_pdf("hello world")]
        assert types == ['text']

    def test_bold(self):
        assert 'bold' in [s[0] for s in parse_inline_pdf("**bold**")]

    def test_italic(self):
        assert 'italic' in [s[0] for s in parse_inline_pdf("*italic*")]

    def test_bold_italic(self):
        assert 'bold_italic' in [s[0] for s in parse_inline_pdf("***bi***")]

    def test_code(self):
        assert 'code' in [s[0] for s in parse_inline_pdf("`c`")]

    def test_link(self):
        assert 'link' in [s[0] for s in parse_inline_pdf("[l](u)")]

    def test_image(self):
        assert 'image' in [s[0] for s in parse_inline_pdf("![a](i)")]

    def test_math(self):
        assert 'math' in [s[0] for s in parse_inline_pdf("$x$")]

    def test_mixed(self):
        t = [s[0] for s in parse_inline_pdf("**b** and *i*")]
        assert 'bold' in t and 'italic' in t

    def test_math_replacement(self):
        segs = parse_inline_pdf("val of $x$ end")
        types = [s[0] for s in segs]
        assert types == ['text', 'math', 'text']


class TestConsistency:
    def test_parser_same(self):
        sample = [
            "# T", "Para", "- a", "- b",
            "$E$", "$$f$$",
            "```p", "c", "```",
            "> q", "---",
        ]
        r1 = parse_md_docx(sample)
        r2 = parse_md_pdf(sample)
        assert len(r1) == len(r2), f"DocX:{len(r1)} PDF:{len(r2)}"
        for i, (d, p) in enumerate(zip(r1, r2)):
            assert d == p, f"Idx {i}: {d} != {p}"

    def test_merge_same(self):
        assert merge_math_docx(["$$", "x", "$$"]) == merge_math_pdf(["$$", "x", "$$"])

    def test_emit_same(self):
        r1, r2 = [], []
        emit_plain_pdf("t", r1, [])
        emit_plain_pdf("t", r2, [])
        assert r1 == r2
