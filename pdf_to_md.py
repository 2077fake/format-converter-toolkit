"""
PDF 转 Markdown 工具
用法: python pdf_to_md.py input.pdf [output.md]

功能：
- 提取文本内容并按页组织
- 自动检测标题（基于字号/加粗，抑制误判）
- 保留加粗、斜体等行内格式
- 自动识别并渲染表格
- 智能合并跨行段落
- 页间分隔标记
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


# ==================== 文本块结构 ====================

class TextSpan:
    """文本片段（同一格式的连续文字）"""
    __slots__ = ('text', 'font', 'size', 'bold', 'italic', 'color', 'bbox')

    def __init__(self, text='', font='', size=0, bold=False, italic=False, color=0, bbox=None):
        self.text = text
        self.font = font
        self.size = size
        self.bold = bold
        self.italic = italic
        self.color = color
        self.bbox = bbox or (0, 0, 0, 0)


class TextBlock:
    """文本块"""
    __slots__ = ('spans', 'bbox', 'block_type')

    def __init__(self, spans=None, bbox=None, block_type=0):
        self.spans = spans or []
        self.bbox = bbox or (0, 0, 0, 0)
        self.block_type = block_type  # 0=text, 1=image

    @property
    def text(self):
        return ''.join(s.text for s in self.spans)

    @property
    def avg_size(self):
        if not self.spans:
            return 0
        return sum(s.size for s in self.spans) / len(self.spans)

    @property
    def is_bold(self):
        return any(s.bold for s in self.spans)

    @property
    def is_italic(self):
        return any(s.italic for s in self.spans)

    @property
    def y0(self):
        return self.bbox[1]

    @property
    def y1(self):
        return self.bbox[3]

    @property
    def x0(self):
        return self.bbox[0]

    @property
    def x1(self):
        return self.bbox[2]

    @property
    def height(self):
        return self.bbox[3] - self.bbox[1]


# ==================== PDF 解析（按行提取） ====================

def _extract_lines(fitz, page) -> list:
    """
    从页面按行提取文本块。每个 PDF 行 → 一个 TextBlock。
    同一 y 坐标、不同 x 坐标的多行 → 各自独立的 TextBlock（表格单元格候选）。
    """
    lines = []
    text_dict = page.get_text('dict')
    for block in text_dict.get('blocks', []):
        if block.get('type') == 0:
            for line in block.get('lines', []):
                spans = []
                for span in line.get('spans', []):
                    font_name = span.get('font', '')
                    font_size = span.get('size', 11)
                    flags = span.get('flags', 0)
                    is_bold = bool(flags & (1 << 4)) or 'Bold' in font_name or 'bold' in font_name.lower()
                    is_italic = bool(flags & (1 << 1)) or 'Italic' in font_name or 'italic' in font_name.lower()
                    spans.append(TextSpan(
                        text=span.get('text', ''),
                        font=font_name,
                        size=round(font_size, 1),
                        bold=is_bold,
                        italic=is_italic,
                        color=span.get('color', 0),
                        bbox=span.get('bbox', (0, 0, 0, 0))
                    ))
                if spans:
                    lines.append(TextBlock(
                        spans=spans,
                        bbox=line.get('bbox', (0, 0, 0, 0)),
                        block_type=0
                    ))
        elif block.get('type') == 1:
            lines.append(TextBlock(
                spans=[TextSpan(text='[图片]', size=10, italic=True)],
                bbox=block.get('bbox', (0, 0, 0, 0)),
                block_type=1
            ))
    return lines


# ==================== 行分组与表格检测 ====================

def _group_lines_by_y(lines: list, y_tolerance: float = 3.0) -> list:
    """
    将 lines 按 y 坐标分组为"行组"。
    同一 y 上的多个 line → 同一行组（表格行候选）。
    返回: [[line, line, ...], [line], ...]
    """
    if not lines:
        return []
    sorted_lines = sorted(lines, key=lambda b: (b.y0, b.x0))
    groups = []
    current = [sorted_lines[0]]
    current_y = sorted_lines[0].y0
    for ln in sorted_lines[1:]:
        if abs(ln.y0 - current_y) <= y_tolerance:
            current.append(ln)
        else:
            groups.append(sorted(current, key=lambda b: b.x0))
            current = [ln]
            current_y = ln.y0
    if current:
        groups.append(sorted(current, key=lambda b: b.x0))
    return groups


def _is_table_row(line_group: list) -> bool:
    """判断一个行组（同一 y 的多个 line）是否构成表格行"""
    if len(line_group) < 2:
        return False
    if any(b.block_type != 0 for b in line_group):
        return False
    texts = [b.text.strip() for b in line_group]
    if any(len(t) > 60 for t in texts):
        return False

    # 排除列表项：首个 cell 是 bullet 或数字编号
    first = texts[0]
    if re.match(r'^[-·•▪▸►✓✔☑☐◦‣⁃➢➤]$', first):
        return False
    if re.match(r'^\d+[.)]$', first):
        return False

    # x 坐标间有合理间距
    for i in range(len(line_group) - 1):
        gap = line_group[i + 1].x0 - line_group[i].x1
        if gap < 5:
            return False
    return True


def _is_list_item(text: str) -> bool:
    """判断是否列表项"""
    return bool(re.match(r'^[-·•▪▸►✓✔☑☐◦‣⁃➢➤]\s', text))


def _is_ordered_list_item(text: str) -> bool:
    """判断是否有序列表项"""
    return bool(re.match(r'^\d+[.)]\s', text))


def _merge_paragraphs(line_groups: list, base_size: float) -> list:
    """
    将行组合并为段落。
    连续的单行组、同缩进、同字号、间距近 → 合并为一个段落。
    表格行组、列表行组不合并。
    返回: list of (TextBlock | {'type':'table_row','cells':[...]} | {'type':'list_row','cells':[...]})
    """
    result = []
    i = 0
    while i < len(line_groups):
        group = line_groups[i]

        # 表格行组
        if _is_table_row(group):
            result.append({'type': 'table_row', 'cells': group, 'y0': group[0].y0})
            i += 1
            continue

        # 列表行组（bullet/number + 内容 在同一 y）
        if len(group) == 2:
            t0 = group[0].text.strip()
            t1 = group[1].text.strip()
            if (re.match(r'^[-·•▪▸►✓✔☑☐◦‣⁃➢➤]$', t0) or
                    re.match(r'^\d+[.)]$', t0)):
                result.append({'type': 'list_row', 'cells': group, 'y0': group[0].y0})
                i += 1
                continue

        # 单行组
        if len(group) == 1:
            blk = group[0]
            text = blk.text.strip()

            # 空行
            if not text:
                result.append(None)
                i += 1
                continue

            # 列表项（单行即有前缀）：不合并
            if _is_list_item(text) or _is_ordered_list_item(text):
                result.append(blk)
                i += 1
                continue

            # 标题候选：不合并
            if _detect_heading(blk, base_size) > 0:
                result.append(blk)
                i += 1
                continue

            # 尝试合并连续单行组为段落
            para_blocks = [blk]
            i += 1
            while i < len(line_groups):
                ng = line_groups[i]
                if len(ng) != 1:
                    break
                nb = ng[0]
                nt = nb.text.strip()
                if not nt:
                    break
                if _is_list_item(nt) or _is_ordered_list_item(nt):
                    break
                if _detect_heading(nb, base_size) > 0:
                    break
                # 不合并：格式突变（非粗→全粗，或全粗→非粗）且新行较短
                prev_all_bold = all(s.bold for s in blk.spans if s.text.strip())
                curr_all_bold = all(s.bold for s in nb.spans if s.text.strip())
                if prev_all_bold != curr_all_bold and len(nt) < 60:
                    break
                # 合并条件：x0 相近、字号相近、y 间距 < 2x 行高
                prev_y1 = para_blocks[-1].y1
                curr_y0 = nb.y0
                line_h = max(blk.height, nb.height, base_size * 1.4)
                if (abs(nb.x0 - blk.x0) < 30 and
                        abs(nb.avg_size - blk.avg_size) < 1.5 and
                        (curr_y0 - prev_y1) < line_h * 2.0):
                    para_blocks.append(nb)
                    i += 1
                else:
                    break

            if len(para_blocks) == 1:
                result.append(para_blocks[0])
            else:
                merged = _merge_blocks(para_blocks)
                result.append(merged)
            continue

        # 多行组但非表格非列表 → 按首个处理
        result.append(group[0])
        i += 1

    return result


def _merge_blocks(blocks: list) -> TextBlock:
    """合并多个 TextBlock，文本用空格连接"""
    if len(blocks) == 1:
        return blocks[0]
    all_spans = []
    for i, blk in enumerate(blocks):
        if i > 0:
            ref_size = blk.spans[0].size if blk.spans else 11
            all_spans.append(TextSpan(text=' ', size=ref_size))
        all_spans.extend(blk.spans)
    x0 = min(b.bbox[0] for b in blocks)
    y0 = min(b.bbox[1] for b in blocks)
    x1 = max(b.bbox[2] for b in blocks)
    y1 = max(b.bbox[3] for b in blocks)
    return TextBlock(spans=all_spans, bbox=(x0, y0, x1, y1))


# ==================== 标题检测 ====================

def _detect_heading(block: TextBlock, base_size: float) -> int:
    """检测是否标题，返回级别 1~3，0=非标题。改进版：抑制误判"""
    text = block.text.strip()
    if not text or len(text) > 150:
        return 0
    avg = block.avg_size
    if avg <= 0:
        return 0

    # 条件1：字号显著大于正文
    if avg >= base_size * 1.55:
        return 1
    if avg >= base_size * 1.35:
        return 2

    # 条件2：字号略大 + 加粗 + 短文本（< 50 字符）
    if avg >= base_size * 1.12 and block.is_bold and len(text) < 50:
        return 3

    # 条件3：加粗 + 中文编号开头（一、/ 1.）+ 短文本
    if block.is_bold and len(text) < 60 and avg >= base_size * 0.95:
        if re.match(r'^[\d一二三四五六七八九十]+[.)、]\s*\S', text):
            return 3
        if re.match(r'^第[一二三四五六七八九十\d]+[章节部分条]\s', text):
            return 3

    # 条件4：全大写短标题（英文）
    if block.is_bold and 5 < len(text) < 50 and text.isupper() and avg >= base_size * 1.05:
        return 3

    return 0


# ==================== 格式输出 ====================

def _span_to_md(span: TextSpan, strip_format: bool = False) -> str:
    """span → Markdown 行内文本"""
    t = span.text
    if not t.strip():
        return t
    if strip_format:
        return t
    if span.bold and span.italic:
        return f'***{t}***'
    elif span.bold:
        return f'**{t}**'
    elif span.italic:
        return f'*{t}*'
    return t


def _block_to_md(block, strip_format: bool = False) -> str:
    """block → Markdown 文本"""
    if isinstance(block, dict):
        return ''
    if block.block_type == 1:
        return '[图片]'
    return ''.join(_span_to_md(s, strip_format) for s in block.spans)


# ==================== 表格渲染 ====================

def _render_table_rows(table_rows: list) -> list:
    """连续的表格行 → Markdown 表格"""
    if not table_rows:
        return []
    max_cols = max(len(row['cells']) for row in table_rows)
    md_rows = []
    for row in table_rows:
        cells = [blk.text.strip() for blk in row['cells']]
        while len(cells) < max_cols:
            cells.append('')
        md_rows.append(cells)
    if not md_rows:
        return []
    lines = ['| ' + ' | '.join(md_rows[0]) + ' |',
             '|' + '|'.join([' --- '] * max_cols) + '|']
    for row in md_rows[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    return lines


# ==================== 主转换 ====================

def convert_pdf_to_md(input_path: str, output_path: str = None) -> str:
    """主转换函数"""
    fitz = _check_fitz()

    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.md'

    doc = fitz.open(input_path)
    print(f"📖 已读取: {input_path} ({doc.page_count} 页)")

    md_lines = []
    all_sizes = []

    # 第一遍：收集字号
    for page_num in range(doc.page_count):
        page = doc[page_num]
        for b in _extract_lines(fitz, page):
            if b.block_type == 0:
                all_sizes.extend(s.size for s in b.spans if s.size > 0)

    base_size = 11.0
    if all_sizes:
        all_sizes.sort()
        base_size = all_sizes[len(all_sizes) // 2]
        base_size = max(9, min(14, base_size))

    print(f"📐 检测正文字号: {base_size:.1f}pt")

    md_lines.append(f'# {os.path.splitext(os.path.basename(input_path))[0]}')
    md_lines.append('')
    md_lines.append(f'> 由 PDF 自动转换 · 共 {doc.page_count} 页')
    md_lines.append('')

    total_blocks = 0

    for page_num in range(doc.page_count):
        page = doc[page_num]
        lines = _extract_lines(fitz, page)
        line_groups = _group_lines_by_y(lines)
        elements = _merge_paragraphs(line_groups, base_size)
        total_blocks += len([e for e in elements if e is not None])

        if page_num > 0:
            md_lines.append('')
            md_lines.append('---')
            md_lines.append(f'<!-- 第 {page_num + 1} 页 -->')
            md_lines.append('')

        pending_table = []
        prev_blank = False

        for elem in elements:
            # 空行标记
            if elem is None:
                if not prev_blank:
                    md_lines.append('')
                    prev_blank = True
                continue

            # 表格行：收集
            if isinstance(elem, dict) and elem.get('type') == 'table_row':
                pending_table.append(elem)
                prev_blank = False
                continue

            # flush 表格
            if pending_table:
                md_lines.extend(_render_table_rows(pending_table))
                md_lines.append('')
                pending_table = []

            # 列表行（bullet + 内容分离的情况）
            if isinstance(elem, dict) and elem.get('type') == 'list_row':
                cells = elem['cells']
                if len(cells) >= 2:
                    bullet = cells[0].text.strip()
                    content = cells[1]
                    if re.match(r'^\d+[.)]$', bullet):
                        md_lines.append(f'1. {_block_to_md(content)}')
                    else:
                        md_lines.append(f'- {_block_to_md(content)}')
                else:
                    md_lines.append(f'- {_block_to_md(cells[0])}')
                prev_blank = False
                continue

            blk = elem
            text = blk.text.strip()

            if not text:
                if not prev_blank:
                    md_lines.append('')
                    prev_blank = True
                continue

            # 图片
            if blk.block_type == 1:
                md_lines.append('![图片](image-placeholder)')
                md_lines.append('')
                prev_blank = True
                continue

            # 标题
            h_level = _detect_heading(blk, base_size)
            if h_level > 0:
                md_lines.append(f'{"#" * h_level} {_block_to_md(blk, strip_format=True)}')
                md_lines.append('')
                prev_blank = True
                continue

            # 无序列表
            if re.match(r'^[-·•▪▸►✓✔☑☐◦‣⁃➢➤]\s', text):
                clean = re.sub(r'^[-·•▪▸►✓✔☑☐◦‣⁃➢➤]\s+', '', text, count=1)
                md_lines.append(f'- {_block_to_md(blk) if clean == text else clean}')
                prev_blank = False
                continue

            # 有序列表
            if re.match(r'^\d+[.)]\s', text):
                clean = re.sub(r'^\d+[.)]\s+', '', text, count=1)
                md_lines.append(f'1. {_block_to_md(blk) if clean == text else clean}')
                prev_blank = False
                continue

            # 普通段落
            md_lines.append(_block_to_md(blk))
            md_lines.append('')
            prev_blank = True

        # 页末 flush 表格
        if pending_table:
            md_lines.extend(_render_table_rows(pending_table))
            md_lines.append('')

    doc.close()

    result = '\n'.join(md_lines)
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"📊 共处理 {total_blocks} 个元素")
    print(f"✅ 已生成: {output_path}")
    return output_path


# ==================== 入口 ====================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python pdf_to_md.py input.pdf [output.md]')
        print('示例: python pdf_to_md.py 报告.pdf')
        print('      python pdf_to_md.py 报告.pdf 报告.md')
        sys.exit(0)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert_pdf_to_md(input_file, output_file)
