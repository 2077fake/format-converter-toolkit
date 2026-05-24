"""
PDF 转 Markdown 工具
用法: python pdf_to_md.py input.pdf [output.md]

功能：
- 提取文本内容并按页组织
- 自动检测标题（基于字号/加粗）
- 保留加粗、斜体等格式
- 页间分隔标记
- 基本表格检测
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
    """文本块（同一行的连续文字）"""
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
    def y0(self):
        return self.bbox[1]

    @property
    def x0(self):
        return self.bbox[0]


# ==================== PDF 解析 ====================

def _extract_blocks(fitz, page) -> list:
    """从页面提取文本块，保留格式信息"""
    blocks = []
    # 使用 dict 模式获取详细信息
    text_dict = page.get_text('dict')
    for block in text_dict.get('blocks', []):
        if block.get('type') == 0:  # 文本块
            spans = []
            for line in block.get('lines', []):
                for span in line.get('spans', []):
                    font_name = span.get('font', '')
                    font_size = span.get('size', 11)
                    flags = span.get('flags', 0)
                    is_bold = bool(flags & 2) or 'Bold' in font_name or 'bold' in font_name.lower()
                    is_italic = bool(flags & 1) or 'Italic' in font_name or 'italic' in font_name.lower()
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
                blocks.append(TextBlock(
                    spans=spans,
                    bbox=block.get('bbox', (0, 0, 0, 0)),
                    block_type=0
                ))
        elif block.get('type') == 1:  # 图片块
            blocks.append(TextBlock(
                spans=[TextSpan(text='[图片]', size=10, italic=True)],
                bbox=block.get('bbox', (0, 0, 0, 0)),
                block_type=1
            ))
    return blocks


def _detect_heading(block: TextBlock, base_size: float) -> int:
    """检测文本块是否为标题，返回标题级别（0=非标题）"""
    text = block.text.strip()
    if not text or len(text) > 150:
        return 0

    avg = block.avg_size

    # 字号启发式：明显大于正文 → 标题
    if avg >= base_size * 1.6:
        return 1
    if avg >= base_size * 1.4:
        return 2
    if avg >= base_size * 1.2 and block.is_bold:
        return 3

    # 短句 + 加粗 → 可能是小标题
    if len(text) < 60 and block.is_bold and avg >= base_size:
        return 3

    # 纯数字编号开头 → 可能是小标题
    if re.match(r'^[\d.]+\s+\S', text) and block.is_bold:
        return 3

    return 0


def _span_to_md(span: TextSpan) -> str:
    """将文本片段转为 Markdown 行内格式"""
    t = span.text
    if not t.strip():
        return t

    if span.bold and span.italic:
        return f'***{t}***'
    elif span.bold:
        return f'**{t}**'
    elif span.italic:
        return f'*{t}*'
    return t


def _block_to_md(block: TextBlock) -> str:
    """将文本块转为 Markdown 文本"""
    if block.block_type == 1:
        return '[图片]'
    return ''.join(_span_to_md(s) for s in block.spans)


def _merge_adjacent_blocks(blocks: list) -> list:
    """合并属于同一段落但被拆分的相邻块"""
    if not blocks:
        return blocks

    merged = []
    current = blocks[0]

    for blk in blocks[1:]:
        # 同一段落判断：y 坐标相近
        if abs(blk.y0 - current.y0) < 5:
            current.spans.extend(blk.spans)
            # 更新 bbox
            x0 = min(current.bbox[0], blk.bbox[0])
            y0 = min(current.bbox[1], blk.bbox[1])
            x1 = max(current.bbox[2], blk.bbox[2])
            y1 = max(current.bbox[3], blk.bbox[3])
            current.bbox = (x0, y0, x1, y1)
        else:
            merged.append(current)
            current = blk
    merged.append(current)
    return merged


# ==================== 表格检测（简易） ====================

def _detect_table_region(blocks: list) -> list:
    """检测表格区域，将表格行分组"""
    if len(blocks) < 2:
        return blocks

    # 简单策略：不处理复杂表格，交给用户手动调整
    # 这里只做基本的列对齐检测
    return blocks


def _is_table_row(blocks_slice: list) -> bool:
    """判断一组块是否构成表格行"""
    if len(blocks_slice) < 2:
        return False
    # 检查是否有规律的空格/制表符分隔
    texts = [b.text.strip() for b in blocks_slice]
    # 简单判断：多个短文本块在同一行
    return all(len(t) < 80 for t in texts) and len(texts) >= 2


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
    total_blocks = 0
    all_sizes = []

    # 第一遍：收集字号统计
    for page_num in range(doc.page_count):
        page = doc[page_num]
        blocks = _extract_blocks(fitz, page)
        for b in blocks:
            if b.block_type == 0:
                all_sizes.extend(s.size for s in b.spans if s.size > 0)

    # 估算正文字号（取中位数）
    base_size = 11.0
    if all_sizes:
        all_sizes.sort()
        base_size = all_sizes[len(all_sizes) // 2]
        # 常见正文字号范围 9-14pt
        base_size = max(9, min(14, base_size))

    print(f"📐 检测正文字号: {base_size:.1f}pt")

    # 第二遍：转换
    md_lines.append(f'# {os.path.splitext(os.path.basename(input_path))[0]}')
    md_lines.append('')
    md_lines.append(f'> 由 PDF 自动转换 · 共 {doc.page_count} 页')
    md_lines.append('')

    for page_num in range(doc.page_count):
        page = doc[page_num]
        blocks = _extract_blocks(fitz, page)
        blocks = _merge_adjacent_blocks(blocks)
        total_blocks += len(blocks)

        if page_num > 0:
            md_lines.append('')
            md_lines.append('---')
            md_lines.append(f'<!-- 第 {page_num + 1} 页 -->')
            md_lines.append('')

        # 跟踪连续表格行
        pending_table_rows = []
        prev_y = -100

        for blk in blocks:
            text = blk.text.strip()
            if not text:
                if pending_table_rows:
                    md_lines.extend(_render_simple_table(pending_table_rows))
                    pending_table_rows = []
                md_lines.append('')
                prev_y = -100
                continue

            # 标题检测
            h_level = _detect_heading(blk, base_size)
            if h_level > 0:
                if pending_table_rows:
                    md_lines.extend(_render_simple_table(pending_table_rows))
                    pending_table_rows = []
                prefix = '#' * h_level
                md_lines.append(f'{prefix} {_block_to_md(blk)}')
                md_lines.append('')
                prev_y = blk.y0
                continue

            # 图片
            if blk.block_type == 1:
                if pending_table_rows:
                    md_lines.extend(_render_simple_table(pending_table_rows))
                    pending_table_rows = []
                md_lines.append('![图片](image-placeholder)')
                md_lines.append('')
                prev_y = -100
                continue

            # 列表检测（以 - · • 等开头）
            if re.match(r'^[-·•▪▸►✓✔☑☐◦‣⁃➢➤]\s', text):
                if pending_table_rows:
                    md_lines.extend(_render_simple_table(pending_table_rows))
                    pending_table_rows = []
                clean = re.sub(r'^[-·•▪▸►✓✔☑☐◦‣⁃➢➤]\s+', '', text, count=1)
                md_lines.append(f'- {_block_to_md(blk) if clean == text else clean}')
                prev_y = blk.y0
                continue

            # 有序列表
            if re.match(r'^[\d]+[.)]\s', text):
                if pending_table_rows:
                    md_lines.extend(_render_simple_table(pending_table_rows))
                    pending_table_rows = []
                clean = re.sub(r'^[\d]+[.)]\s+', '', text, count=1)
                md_lines.append(f'1. {_block_to_md(blk) if clean == text else clean}')
                prev_y = blk.y0
                continue

            # 表格行检测
            if '\t' in text or '  |  ' in text:
                pending_table_rows.append(blk)
                prev_y = blk.y0
                continue

            # 可能的表格行（多个短列）
            if _is_table_row([blk]):
                pending_table_rows.append(blk)
                prev_y = blk.y0
                continue

            # 普通段落
            if pending_table_rows:
                md_lines.extend(_render_simple_table(pending_table_rows))
                pending_table_rows = []

            md_lines.append(_block_to_md(blk))
            md_lines.append('')
            prev_y = blk.y0

        # 页面末尾 flush 表格
        if pending_table_rows:
            md_lines.extend(_render_simple_table(pending_table_rows))

    doc.close()

    result = '\n'.join(md_lines)
    # 清理多余空行
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"📊 共处理 {total_blocks} 个文本块")
    print(f"✅ 已生成: {output_path}")
    return output_path


def _render_simple_table(blocks: list) -> list:
    """将文本块列表渲染为 Markdown 表格"""
    if not blocks:
        return []

    # 提取每行的列（通过连续空格分割）
    rows = []
    for blk in blocks:
        text = blk.text.strip()
        # 尝试用多个空格 / tab 分割
        if '\t' in text:
            cols = [c.strip() for c in text.split('\t')]
        else:
            cols = re.split(r'\s{2,}', text)
        rows.append([c for c in cols if c])

    if not rows:
        return []

    max_cols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < max_cols:
            r.append('')

    lines = []
    lines.append('| ' + ' | '.join(rows[0]) + ' |')
    lines.append('|' + '|'.join([' --- '] * max_cols) + '|')
    for row in rows[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')

    return lines


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
