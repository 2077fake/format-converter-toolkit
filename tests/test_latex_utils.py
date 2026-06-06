"""Unit tests for latex_utils."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from latex_utils import simplify_tex, _LATEX_TO_UNICODE


class TestSimplifyTexBasic:
    def test_empty_string(self):
        assert simplify_tex("") == ""

    def test_plain_text(self):
        assert simplify_tex("hello world") == "hello world"

    def test_single_greek_letter(self):
        assert simplify_tex(r"\alpha") == "α"
        assert simplify_tex(r"\beta") == "β"
        assert simplify_tex(r"\pi") == "π"

    def test_greek_capital_letters(self):
        assert simplify_tex(r"\Delta") == "Δ"
        assert simplify_tex(r"\Gamma") == "Γ"
        assert simplify_tex(r"\Omega") == "Ω"
        assert simplify_tex(r"\Lambda") == "Λ"


class TestSimplifyTexOperators:
    def test_fraction(self):
        assert simplify_tex(r"\frac{a}{b}") == "(a)/(b)"

    def test_sqrt(self):
        assert simplify_tex(r"\sqrt{x}") == "√(x)"

    def test_summation(self):
        assert simplify_tex(r"\sum") == "Σ"
        assert simplify_tex(r"\prod") == "Π"
        assert simplify_tex(r"\int") == "∫"

    def test_relations(self):
        assert simplify_tex(r"\approx") == "≈"
        assert simplify_tex(r"\equiv") == "≡"
        assert simplify_tex(r"\neq") == "≠"
        assert simplify_tex(r"\leq") == "≤"
        assert simplify_tex(r"\geq") == "≥"

    def test_arrows(self):
        assert simplify_tex(r"\rightarrow") == "→"
        assert simplify_tex(r"\longrightarrow") == "→"
        assert simplify_tex(r"\leftarrow") == "←"
        assert simplify_tex(r"\mapsto") == "↦"

    def test_arrow_ordering(self):
        for pat, _ in _LATEX_TO_UNICODE:
            pass
        assert simplify_tex(r"\longrightarrow") == "→"
        assert simplify_tex(r"\rightarrow") == "→"


class TestSimplifyTexSubscripts:
    def test_braced_subscript(self):
        assert "xi" == simplify_tex(r"x_{i}")

    def test_braced_superscript(self):
        assert "^" in simplify_tex(r"x^{2}")

    def test_single_char_subscript(self):
        assert "xi" == simplify_tex(r"x_i")

    def test_single_char_superscript(self):
        assert simplify_tex(r"x^2") in ("x^2", "^2")


class TestSimplifyTexDisplayCommands:
    def test_displaystyle_removed(self):
        assert r"\displaystyle" not in simplify_tex(r"\displaystyle x")

    def test_text_preserves_content(self):
        assert simplify_tex(r"\text{hello}") == "hello"

    def test_cases_environment(self):
        result = simplify_tex(r"\begin{cases} a & b \\ c & d \end{cases}")
        assert "a" in result and "b" in result

    def test_quadr_spacing(self):
        assert simplify_tex(r"a\quad b") == "a b"

    def test_unknown_command_removed(self):
        assert "foo" not in simplify_tex(r"\foo bar")

    def test_brackets_removed(self):
        result = simplify_tex(r"\left( x \right)")
        assert "left" not in result and "right" not in result


class TestSimplifyTexComplex:
    def test_integral_formula(self):
        result = simplify_tex(r"\int_0^\infty e^{-x} dx")
        assert "∫" in result and "∞" in result

    def test_quadratic_formula(self):
        result = simplify_tex(r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}")
        assert "±" in result and "√" in result

    def test_fractions_and_greek(self):
        result = simplify_tex(r"\frac{\alpha + \beta}{\gamma}")
        assert "/" in result


class TestSimplifyTexEdgeCases:
    def test_multiple_spaces_collapsed(self):
        assert "  " not in simplify_tex(r"\alpha    \beta    \gamma")

    def test_trailing_whitespace_stripped(self):
        result = simplify_tex("  \alpha  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_dots(self):
        assert simplify_tex(r"\cdots") == "⋯"
        assert simplify_tex(r"\vdots") == "⋮"
        assert simplify_tex(r"\ddots") == "⋱"

    def test_reasoning_symbols(self):
        assert simplify_tex(r"\therefore") == "∴"
        assert simplify_tex(r"\because") == "∵"

    def test_geometry(self):
        assert simplify_tex(r"\angle") == "∠"
        assert simplify_tex(r"\triangle") == "△"
        assert simplify_tex(r"\square") == "□"

    def test_exists_forall(self):
        assert simplify_tex(r"\forall") == "∀"
        assert simplify_tex(r"\exists") == "∃"
