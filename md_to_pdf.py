"""
Markdown 转 PDF 工具（支持 LaTeX 公式）
用法: python md_to_pdf.py input.md [output.pdf]

功能：
- 标题层级 # ~ ######
- 段落文本，保留 **粗体** / *斜体* / ***粗斜体*** / `行内代码`
- 有序/无序列表、嵌套列表
- 表格
- 代码块（深色背景 + 等宽字体）
- 引用块（左侧灰条 + 斜体）
- 水平分割线
- LaTeX 数学公式（$...$ 行内 + $$...$$ 块级）
- 超链接
- 图片占位
- 自动分页
"""

import re
import sys
import os


def _check_fitz():
    """检查 PyMuPDF 是否安装"""
    try:
        import fitz
        return fitz
    except ImportError:
        print("❌ 需要安装 PyMuPDF: pip install PyMuPDF")
        sys.exit(1)


# ==================== 全局样式配置 ====================

PAGE_WIDTH = 595.28   # A4 宽度 (pt)
PAGE_HEIGHT = 841.89  # A4 高度 (pt)
MARGIN_LEFT = 72      # 左边距 (pt) ≈ 1 inch
MARGIN_RIGHT = 72
MARGIN_TOP = 72
MARGIN_BOTTOM = 72

FONT_CJK = 'china-s'            # 中文字体（含英文）
FONT_MONO = 'cour'              # 等宽字体（代码/数学）
FONT_EN = 'helv'                # 纯英文回退

# 字号 (pt)
SIZE_H1 = 24.0
SIZE_H2 = 18.0
SIZE_H3 = 14.0
SIZE_H4 = 12.5
SIZE_BODY = 11.0
SIZE_CODE = 9.0
SIZE_SMALL = 9.0

# 颜色 (RGB)
COLOR_BLACK = (0, 0, 0)
COLOR_DARK = (0.13, 0.13, 0.13)
COLOR_HEADING = (0.1, 0.34, 0.86)
COLOR_CODE_BG = (0.94, 0.94, 0.94)
COLOR_QUOTE_BORDER = (0.8, 0.8, 0.8)
COLOR_QUOTE_TEXT = (0.4, 0.4, 0.4)
COLOR_LINK = (0.1, 0.34, 0.86)
COLOR_CODE_TEXT = (0.8, 0.15, 0.1)
COLOR_TABLE_BORDER = (0.6, 0.6, 0.6)
COLOR_TABLE_HEADER_BG = (0.93, 0.93, 0.93)
COLOR_HR = (0.8, 0.8, 0.8)

LINE_SPACING = 1.4
PARA_SPACING = 6.0

# ==================== LaTeX 简化 ====================

_LATEX_TO_UNICODE = [
    (r'\\frac\{([^}]*)}\{([^}]*)\}', r'(\1)/(\2)'),
    (r'\\sqrt\{([^}]*)\}', r'√(\1)'),
    (r'\\sum', 'Σ'), (r'\\prod', 'Π'), (r'\\int', '∫'),
    (r'\\infty', '∞'), (r'\\partial', '∂'),
    (r'\\alpha', 'α'), (r'\\beta', 'β'), (r'\\gamma', 'γ'),
    (r'\\delta', 'δ'), (r'\\epsilon', 'ε'), (r'\\theta', 'θ'),
    (r'\\lambda', 'λ'), (r'\\mu', 'μ'), (r'\\pi', 'π'),
    (r'\\sigma', 'σ'), (r'\\omega', 'ω'), (r'\\Omega', 'Ω'),
    (r'\\Delta', 'Δ'), (r'\\Gamma', 'Γ'), (r'\\Lambda', 'Λ'),
    (r'\\approx', '≈'), (r'\\equiv', '≡'), (r'\\neq', '≠'),
    (r'\\leq', '≤'), (r'\\geq', '≥'), (r'\\ll', '≪'), (r'\\gg', '≫'),
    (r'\\pm', '±'), (r'\\mp', '∓'), (r'\\times', '×'), (r'\\cdot', '·'),
    (r'\\div', '÷'), (r'\\circ', '°'),
    (r'\\parallel', '∥'), (r'\\perp', '⊥'),
    (r'\\rightarrow', '→'), (r'\\Rightarrow', '⇒'),
    (r'\\leftarrow', '←'), (r'\\Leftarrow', '⇐'),
    (r'\\leftrightarrow', '↔'), (r'\\longrightarrow', '→'),
    (r'\\mapsto', '↦'), (r'\\to', '→'),
    (r'\\in', '∈'), (r'\\notin', '∉'),
    (r'\\subset', '⊂'), (r'\\supset', '⊃'),
    (r'\\subseteq', '⊆'), (r'\\cup', '∪'), (r'\\cap', '∩'),
    (r'\\emptyset', '∅'), (r'\\forall', '∀'), (r'\\exists', '∃'),
    (r'\\nabla', '∇'), (r'\\propto', '∝'),
    (r'\\sim', '∼'), (r'\\cong', '≅'),
    (r'\\cdots', '⋯'), (r'\\vdots', '⋮'), (r'\\ddots', '⋱'),
    (r'\\therefore', '∴'), (r'\\because', '∵'),
    (r'\\angle', '∠'), (r'\\triangle', '△'), (r'\\square', '□'),
]


def _simplify_tex(tex: str) -> str:
    """将 LaTeX 公式转为可读的纯文本"""
    t = tex.strip()
    for pat, repl in _LATEX_TO_UNICODE:
        t = re.sub(pat, repl, t)
    t = re.sub(r'_\{([^}]+)\}', r'\1', t)
    t = re.sub(r'\^\{([^}]+)\}', r'^\1', t)
    t = re.sub(r'_([a-zA-Z0-9])', r'\1', t)
    t = re.sub(r'\^([a-zA-Z0-9])', r'^\1', t)
    t = re.sub(r'\\displaystyle\s*', '', t)
    t = re.sub(r'\\text\{([^}]*)\}', r'\1', t)
    t = re.sub(r'\\textrm\{([^}]*)\}', r'\1', t)
    t = re.sub(r'\\begin\{cases\}', '{', t)
    t = re.sub(r'\\end\{cases\}', '', t)
    t = re.sub(r'\\\\', ' | ', t)
    t = re.sub(r'\\qquad', '    ', t)
    t = re.sub(r'\\quad', '  ', t)
    t = re.sub(r'\\[;,]', ' ', t)
    t = re.sub(r'\\!', '', t)
    t = re.sub(r'\\left\s*', '', t)
    t = re.sub(r'\\right\s*', '', t)
    t = re.sub(r'\\big[lr]?\s*', '', t)
    t = re.sub(r'\\Big[lr]?\s*', '', t)
    t = re.sub(r'\\[a-zA-Z]+', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# ==================== Markdown 解析 ====================

def _merge_display_math(lines: list) -> list:
    """跨行 $$...$$ 合并"""
    result = []
    in_math = False
    buf = []
    for line in lines:
        s = line.strip()
        if s.startswith('$$') and not in_math:
            if s.endswith('$$') and len(s) > 4:
                result.append(s)
                continue
            in_math = True
            buf = [s]
        elif s.endswith('$$') and in_math:
            buf.append(s)
            in_math = False
            merged = '$$' + '\n'.join(l.strip('$') for l in buf).strip() + '$$'
            result.append(merged)
        elif in_math:
            buf.append(s)
        else:
            result.append(line)
    return result


def parse_markdown(lines: list) -> list:
    """解析 Markdown → 结构化元素"""
    merged = _merge_display_math(lines)
    elements = []
    i = 0
    while i < len(merged):
        line = merged[i]
        s = line.strip()

        if not s:
            i += 1
            continue

        if s.startswith('$$') and s.endswith('$$') and len(s) > 4:
            elements.append({'type': 'display_math', 'tex': s[2:-2].strip()})
            i += 1
            continue

        if s.startswith('```'):
            lang = s[3:].strip()
            code_lines = []
            i += 1
            while i < len(merged) and not merged[i].strip().startswith('```'):
                code_lines.append(merged[i])
                i += 1
            i += 1
            elements.append({'type': 'code_block', 'code': '\n'.join(code_lines), 'lang': lang})
            continue

        if re.match(r'^[-*_]{3,}\s*$', s):
            elements.append({'type': 'hr'})
            i += 1
            continue

        hm = re.match(r'^(#{1,6})\s+(.+)', s)
        if hm:
            elements.append({'type': 'heading', 'level': len(hm.group(1)), 'text': hm.group(2)})
            i += 1
            continue

        lm = re.match(r'^(\s*)[-*+]\s+(.+)', s)
        if lm:
            items = []
            indent = len(re.match(r'^(\s*)', merged[i]).group(1))
            while i < len(merged):
                cm = re.match(r'^(\s*)[-*+]\s+(.+)', merged[i])
                if cm and len(cm.group(1)) == indent:
                    items.append(cm.group(2))
                    i += 1
                elif merged[i].strip() == '':
                    i += 1
                    if i < len(merged):
                        nm = re.match(r'^(\s*)[-*+]\s+(.+)', merged[i])
                        if nm and len(nm.group(1)) == indent:
                            items.append(nm.group(2))
                            i += 1
                            continue
                        i -= 1
                    break
                else:
                    break
            elements.append({'type': 'ul', 'items': items})
            continue

        om = re.match(r'^(\s*)\d+\.\s+(.+)', s)
        if om:
            items = []
            while i < len(merged):
                dm = re.match(r'^(\s*)\d+\.\s+(.+)', merged[i])
                if dm:
                    items.append(dm.group(2))
                    i += 1
                elif merged[i].strip() == '':
                    i += 1
                    if i < len(merged) and re.match(r'^(\s*)\d+\.\s+(.+)', merged[i]):
                        continue
                    i -= 1
                    break
                else:
                    break
            elements.append({'type': 'ol', 'items': items})
            continue

        qm = re.match(r'^>\s?(.*)', s)
        if qm:
            qlines = []
            while i < len(merged):
                mm = re.match(r'^>\s?(.*)', merged[i])
                if mm:
                    qlines.append(mm.group(1))
                    i += 1
                elif merged[i].strip() == '':
                    i += 1
                    if i < len(merged) and re.match(r'^>\s?(.*)', merged[i]):
                        continue
                    i -= 1
                    break
                else:
                    break
            elements.append({'type': 'blockquote', 'text': '\n'.join(qlines)})
            continue

        if '|' in s and i + 1 < len(merged) and re.match(r'^[\|\-:\s]+$', merged[i + 1].strip()):
            tlines = [s]
            i += 2
            while i < len(merged) and '|' in merged[i]:
                tlines.append(merged[i].strip())
                i += 1
            rows = [[c.strip() for c in tl.strip('|').split('|')] for tl in tlines]
            if rows:
                elements.append({'type': 'table', 'rows': rows})
            continue

        plines = [s]
        i += 1
        while i < len(merged) and merged[i].strip() and \
              not re.match(r'^(#{1,6}\s|```|[-*_]{3,}|[-*+]\s|\d+\.\s|>\s|\$\$)',
                           merged[i].strip()) and '|' not in merged[i]:
            plines.append(merged[i].strip())
            i += 1
        elements.append({'type': 'paragraph', 'text': ' '.join(plines)})

    return elements


# ==================== 行内格式解析 ====================

def _parse_inline(text: str) -> list:
    """将行内文本解析为 (type, content) 片段列表
    支持: **bold**, *italic*, ***bold-italic***, `code`, $math$, [link](url), ![img](url)
    """
    segments = []
    math_items = []

    def _save_math(m):
        math_items.append(m.group(1))
        return f'[MATH{len(math_items) - 1}]'

    text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', _save_math, text)

    pattern = (
        r'(\*\*\*(.+?)\*\*\*|'
        r'___\s*(.+?)\s*___|'
        r'\*\*(.+?)\*\*|'
        r'__\s*(.+?)\s*__|'
        r'\*(.+?)\*|'
        r'_\s*(.+?)\s*_|'
        r'`(.+?)`|'
        r'!\[(.*?)\]\((.+?)\)|'
        r'\[(.+?)\]\((.+?)\))'
    )

    last = 0
    for m in re.finditer(pattern, text):
        start, end = m.span()
        if start > last:
            _emit_plain_segments(text[last:start], segments, math_items)
        last = end

        if m.group(2) and m.group(0).startswith('***'):
            segments.append(('bold_italic', m.group(2)))
        elif m.group(3) and m.group(0).startswith('___'):
            segments.append(('bold_italic', m.group(3)))
        elif m.group(4):
            segments.append(('bold', m.group(4)))
        elif m.group(5):
            segments.append(('bold', m.group(5)))
        elif m.group(6):
            segments.append(('italic', m.group(6)))
        elif m.group(7):
            segments.append(('italic', m.group(7)))
        elif m.group(8):
            segments.append(('code', m.group(8)))
        elif m.group(9):
            segments.append(('image', m.group(9)))
        elif m.group(11):
            segments.append(('link', m.group(11)))

    if last < len(text):
        _emit_plain_segments(text[last:], segments, math_items)

    return segments


def _emit_plain_segments(text: str, segments: list, math_items: list):
    """拆分纯文本，还原数学占位符"""
    parts = re.split(r'(\[MATH(\d+)\])', text)
    i = 0
    while i < len(parts):
        part = parts[i]
        if not part:
            i += 1
            continue
        if part.startswith('[MATH') and i + 1 < len(parts):
            idx = int(parts[i + 1])
            if idx < len(math_items):
                segments.append(('math', _simplify_tex(math_items[idx])))
            i += 2
        else:
            if part.strip():
                segments.append(('text', part))
            i += 1


# ==================== PDF 渲染引擎 ====================

class PDFRenderer:
    """基于 PyMuPDF 的 PDF 渲染器，负责排版和输出。
    使用 CJK 内置字体渲染中文，通过 faux bold（重叠渲染）模拟加粗。
    """

    def __init__(self, fitz, output_path: str):
        self.fitz = fitz
        self.doc = fitz.open()
        self.page = None
        self.y = MARGIN_TOP
        self.page_num = 0
        self._new_page()

    def _content_width(self) -> float:
        return PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

    def _new_page(self):
        self.page = self.doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        self.y = MARGIN_TOP
        self.page_num += 1

    def _check_space(self, needed: float):
        if self.y + needed > PAGE_HEIGHT - MARGIN_BOTTOM:
            self._new_page()

    def _advance(self, dy: float):
        self.y += dy
        if self.y > PAGE_HEIGHT - MARGIN_BOTTOM:
            self._new_page()

    def _text_width(self, text: str, fontsize: float) -> float:
        return self.fitz.get_text_length(text, fontname=FONT_CJK, fontsize=fontsize)

    def _wrap_text(self, text: str, fontsize: float, max_width: float) -> list:
        """逐字折行（中英文混排）"""
        if not text:
            return ['']
        lines = []
        cur = ''
        for ch in text:
            if self._text_width(cur + ch, fontsize) > max_width and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
        return lines

    def _draw_text(self, x: float, y: float, text: str, fontsize: float,
                   color=COLOR_DARK, bold=False):
        """绘制文本，bold=True 时用 faux bold（重叠渲染模拟加粗）"""
        if not text:
            return
        if bold:
            # faux bold: 同位置多写一次，x 偏移 0.5pt
            self.page.insert_text((x, y), text, fontname=FONT_CJK,
                                  fontsize=fontsize, color=color)
            self.page.insert_text((x + 0.5, y), text, fontname=FONT_CJK,
                                  fontsize=fontsize, color=color)
        else:
            self.page.insert_text((x, y), text, fontname=FONT_CJK,
                                  fontsize=fontsize, color=color)

    def _draw_rect(self, x0, y0, x1, y1, fill=None, stroke=None):
        rect = self.fitz.Rect(x0, y0, x1, y1)
        if fill:
            self.page.draw_rect(rect, color=fill, fill=fill)
        if stroke:
            self.page.draw_rect(rect, color=stroke)

    def _draw_line(self, x0, y0, x1, y1, color=COLOR_HR, width=1.0):
        self.page.draw_line((x0, y0), (x1, y1), color=color, width=width)

    # ==================== 各元素渲染 ====================

    def render_heading(self, text: str, level: int):
        sizes = {1: SIZE_H1, 2: SIZE_H2, 3: SIZE_H3, 4: SIZE_H4, 5: 11.5, 6: 11}
        fs = sizes.get(level, SIZE_BODY)
        lh = fs * 1.4
        space_before = 14 if level <= 2 else 8

        self._check_space(lh + space_before + 4)
        self._advance(space_before)

        # 去除行内格式标记
        plain = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
        plain = re.sub(r'`(.+?)`', r'\1', plain)
        plain = re.sub(r'\$(.+?)\$', r'\1', plain)

        # 标题加粗 + 彩色
        x = MARGIN_LEFT
        y_base = self.y + fs * 0.85
        self._draw_text(x, y_base, plain, fs, color=COLOR_HEADING, bold=True)
        self._advance(lh + 2)

    def render_paragraph(self, text: str, indent: float = 0,
                         fontsize: float = SIZE_BODY):
        """渲染段落（纯文本，行内格式标记保留）"""
        if not text.strip():
            return
        lh = fontsize * LINE_SPACING
        max_w = self._content_width() - indent

        # 去除内联格式标记获得纯文本
        clean = text
        clean = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', clean)
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)
        clean = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1', clean)
        clean = re.sub(r'`(.+?)`', r'\1', clean)
        clean = re.sub(r'\$([^$]+)\$', r'\1', clean)
        clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean)

        lines = self._wrap_text(clean, fontsize, max_w)
        for line_text in lines:
            self._check_space(lh + 2)
            self._draw_text(MARGIN_LEFT + indent,
                            self.y + fontsize * 0.85,
                            line_text, fontsize)
            self._advance(lh)

    def render_code_block(self, code: str, lang: str = ''):
        lh = SIZE_CODE * 1.25
        code_lines = code.split('\n')
        total_h = lh * (len(code_lines) + 2) + 8
        self._check_space(total_h + 6)

        x = MARGIN_LEFT + 6
        # 背景
        self._draw_rect(MARGIN_LEFT, self.y,
                        MARGIN_LEFT + self._content_width(),
                        self.y + total_h, fill=COLOR_CODE_BG)

        self._advance(6)
        for cl in code_lines:
            # 使用 CJK 字体渲染（兼容中文代码），等宽效果用间距模拟
            self.page.insert_text((x, self.y + SIZE_CODE * 0.85), cl,
                                  fontname=FONT_CJK, fontsize=SIZE_CODE,
                                  color=COLOR_CODE_TEXT)
            self._advance(lh)

        if lang:
            self.page.insert_text((x, self.y + SIZE_SMALL * 0.85),
                                  f'({lang})', fontname=FONT_CJK,
                                  fontsize=SIZE_SMALL, color=(0.55, 0.55, 0.55))
            self._advance(lh)

        self._advance(6)

    def render_list(self, items: list, ordered: bool = False):
        lh = SIZE_BODY * LINE_SPACING
        max_w = self._content_width() - 24

        for idx, item in enumerate(items):
            # 去除行内格式标记
            clean = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', item)
            clean = re.sub(r'`(.+?)`', r'\1', clean)
            clean = re.sub(r'\$(.+?)\$', r'\1', clean)
            clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean)

            prefix = f'{idx + 1}.' if ordered else '•'
            full_text = f'{prefix} {clean}'

            self._check_space(lh + 2)
            lines = self._wrap_text(full_text, SIZE_BODY, max_w)
            for li, line_text in enumerate(lines):
                if li > 0:
                    self._advance(lh)
                    self._check_space(lh)
                indent_x = MARGIN_LEFT + 14 if li == 0 else MARGIN_LEFT + 22
                self._draw_text(indent_x, self.y + SIZE_BODY * 0.85,
                                line_text, SIZE_BODY)
                self._advance(lh)

    def render_blockquote(self, text: str):
        lh = SIZE_BODY * 1.3
        max_w = self._content_width() - 22
        clean = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
        clean = re.sub(r'`(.+?)`', r'\1', clean)
        clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean)
        lines = self._wrap_text(clean, SIZE_BODY, max_w)
        total_h = lh * len(lines) + 10

        self._check_space(total_h + 4)
        self._advance(4)

        # 左侧灰条
        self._draw_rect(MARGIN_LEFT, self.y,
                        MARGIN_LEFT + 3, self.y + total_h,
                        fill=(0.75, 0.75, 0.75))

        for line_text in lines:
            self.page.insert_text(
                (MARGIN_LEFT + 10, self.y + SIZE_BODY * 0.85),
                line_text, fontname=FONT_CJK, fontsize=SIZE_BODY,
                color=COLOR_QUOTE_TEXT
            )
            self._advance(lh)

        self._advance(6)

    def render_hr(self):
        self._check_space(14)
        self._advance(6)
        self._draw_line(MARGIN_LEFT, self.y,
                        MARGIN_LEFT + self._content_width(), self.y,
                        COLOR_HR, 1.2)
        self._advance(10)

    def render_table(self, rows: list):
        if not rows:
            return
        num_cols = max(len(r) for r in rows)
        col_w = self._content_width() / num_cols
        lh = SIZE_BODY * 1.35
        pad = 4

        # 计算每行高度
        row_heights = []
        for row in rows:
            max_ln = 1
            for ci in range(min(len(row), num_cols)):
                txt = row[ci] if ci < len(row) else ''
                ln = len(self._wrap_text(txt, SIZE_BODY, col_w - pad * 2))
                max_ln = max(max_ln, ln)
            row_heights.append(max_ln)

        total_h = sum(h * lh + 4 for h in row_heights)
        self._check_space(total_h + 8)
        self._advance(4)

        row_y = self.y
        for ri, row in enumerate(rows):
            rh = row_heights[ri] * lh + 4

            # 表头背景
            if ri == 0:
                self._draw_rect(MARGIN_LEFT, row_y,
                                MARGIN_LEFT + self._content_width(),
                                row_y + rh, fill=COLOR_TABLE_HEADER_BG)

            for ci in range(num_cols):
                txt = row[ci] if ci < len(row) else ''
                cx = MARGIN_LEFT + ci * col_w + pad
                cw = col_w - pad * 2
                lines = self._wrap_text(txt, SIZE_BODY, cw)
                for li, lt in enumerate(lines):
                    cy = row_y + pad + li * lh + SIZE_BODY * 0.85
                    self._draw_text(cx, cy, lt, SIZE_BODY,
                                    bold=(ri == 0))

                # 列分隔线
                if ci < num_cols - 1:
                    bx = MARGIN_LEFT + (ci + 1) * col_w
                    self._draw_line(bx, row_y, bx, row_y + rh,
                                    COLOR_TABLE_BORDER, 0.4)

            # 行分隔线
            self._draw_line(MARGIN_LEFT, row_y + rh,
                            MARGIN_LEFT + self._content_width(),
                            row_y + rh, COLOR_TABLE_BORDER, 0.4)
            row_y += rh

        # 外框
        self._draw_rect(MARGIN_LEFT, self.y,
                        MARGIN_LEFT + self._content_width(), row_y,
                        stroke=COLOR_TABLE_BORDER)
        self.y = row_y + 6

    def render_display_math(self, tex: str):
        clean = _simplify_tex(tex)
        lh = SIZE_BODY * 1.5
        self._check_space(lh + 12)
        self._advance(6)

        w = self._text_width(clean, SIZE_BODY)
        x = MARGIN_LEFT + max(0, (self._content_width() - w) / 2)

        self._draw_rect(x - 6, self.y, x + w + 6, self.y + lh,
                        fill=(0.97, 0.97, 0.97))
        self.page.insert_text((x, self.y + SIZE_BODY * 0.9), clean,
                              fontname=FONT_MONO, fontsize=SIZE_BODY,
                              color=(0.15, 0.15, 0.15))
        self._advance(lh + 6)


# ==================== 主转换 ====================

def convert_md_to_pdf(input_path: str, output_path: str = None):
    """主转换函数"""
    fitz = _check_fitz()

    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.pdf'

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    print(f"📖 已读取: {input_path} ({len(lines)} 行)")

    elements = parse_markdown(lines)
    print(f"🔍 解析出 {len(elements)} 个元素")

    renderer = PDFRenderer(fitz, output_path)

    # 标题页
    title = os.path.splitext(os.path.basename(input_path))[0]
    renderer.render_heading(title, 1)
    renderer._advance(8)

    for el in elements:
        t = el['type']

        if t == 'heading':
            renderer.render_heading(el['text'], el['level'])

        elif t == 'paragraph':
            renderer.render_paragraph(el['text'])

        elif t == 'code_block':
            renderer.render_code_block(el['code'], el.get('lang', ''))

        elif t == 'ul':
            renderer.render_list(el['items'], ordered=False)

        elif t == 'ol':
            renderer.render_list(el['items'], ordered=True)

        elif t == 'blockquote':
            renderer.render_blockquote(el['text'])

        elif t == 'hr':
            renderer.render_hr()

        elif t == 'table':
            renderer.render_table(el['rows'])

        elif t == 'display_math':
            renderer.render_display_math(el['tex'])

    # 保存
    renderer.doc.save(output_path)
    renderer.doc.close()

    print(f"📊 共 {renderer.page_num} 页")
    print(f"✅ 已生成: {output_path}")
    return output_path


# ==================== 入口 ====================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("📝 Markdown → PDF 转换工具 (支持 LaTeX 公式)")
        print(f"用法: python {os.path.basename(__file__)} input.md [output.pdf]")
        print()
        print("示例:")
        print(f"  python {os.path.basename(__file__)} readme.md")
        print(f"  python {os.path.basename(__file__)} readme.md 输出.pdf")
    else:
        convert_md_to_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
