"""
Word (.docx) 转 Markdown 工具
用法: python docx_to_md.py input.docx [output.md]

功能：
- 标题 → # ## ### 等
- 段落文本，保留粗体/斜体/行内代码
- 有序/无序列表
- 表格
- 图片占位
- 超链接
"""

import re
import sys
import os
from docx import Document
from docx.oxml.ns import qn


# ==================== 样式映射 ====================

def _get_heading_level(paragraph) -> int:
    """从段落样式中提取标题级别"""
    style_name = paragraph.style.name if paragraph.style else ''
    # 匹配 "Heading 1", "Heading 2" 等
    m = re.match(r'Heading\s+(\d+)', style_name, re.IGNORECASE)
    if m:
        return min(int(m.group(1)), 6)
    # 中文样式 "标题 1"
    m = re.match(r'标题\s*(\d*)', style_name)
    if m:
        return int(m.group(1)) if m.group(1) else 1
    m = re.match(r'^\d+', style_name)
    if m:
        return min(int(m.group(0)), 6)
    return 0


def _is_list_item(paragraph) -> tuple:
    """判断是否为列表项，返回 (type, level) 或 (None, 0)"""
    style_name = paragraph.style.name if paragraph.style else ''
    if 'List Bullet' in style_name:
        return ('ul', 0)
    if 'List Number' in style_name:
        return ('ol', 0)
    # 检查 numPr（编号属性）
    pPr = paragraph._element.find(qn('w:pPr'))
    if pPr is not None:
        numPr = pPr.find(qn('w:numPr'))
        if numPr is not None:
            ilvl = numPr.find(qn('w:ilvl'))
            numId = numPr.find(qn('w:numId'))
            level = int(ilvl.get(qn('w:val'), '0')) if ilvl is not None else 0
            if numId is not None:
                return ('ol', level)
    # 手动词头检测
    text = paragraph.text.strip()
    if re.match(r'^[-*+]\s', text):
        return ('ul', 0)
    if re.match(r'^\d+[.)]\s', text):
        return ('ol', 0)
    return (None, 0)


# ==================== 行内格式提取 ====================

def _extract_run_text(run, para_text: str, runs_processed: set = None) -> str:
    """提取单个 run 的文本，附加 Markdown 格式标记"""
    if runs_processed is None:
        runs_processed = set()
    run_id = id(run)
    if run_id in runs_processed:
        return ''
    runs_processed.add(run_id)

    text = run.text
    if not text:
        return ''

    # 检查超链接
    hyperlink = None
    parent = run._element.getparent()
    if parent is not None and parent.tag == qn('w:hyperlink'):
        hyperlink = parent.get(qn('r:id'))

    # 格式标记
    prefix = ''
    suffix = ''

    if run.bold and run.italic:
        prefix, suffix = '***', '***'
    elif run.bold:
        prefix, suffix = '**', '**'
    elif run.italic:
        prefix, suffix = '*', '*'

    # 等宽字体 → 行内代码
    font_name = (run.font.name or '').lower()
    if font_name in ('consolas', 'courier new', 'monospace', 'source code pro'):
        prefix, suffix = '`', '`'

    # 超链接
    if hyperlink:
        return f'[{text}]({hyperlink})'

    return f'{prefix}{text}{suffix}'


def _process_paragraph_text(paragraph) -> str:
    """提取段落的 Markdown 文本（含行内格式）"""
    runs = paragraph.runs
    if not runs:
        return paragraph.text

    parts = []
    for run in runs:
        parts.append(_extract_run_text(run, paragraph.text))

    result = ''.join(parts)
    # 去除可能的空标记残留
    result = re.sub(r'\*\*\*\*\*\*', '', result)
    result = re.sub(r'\*\*\*\*', '', result)
    result = re.sub(r'\*\*', '', result)  # 不做，上面已经处理了... 实际上我们需要更聪明的方法
    # 简化：直接返回拼接结果
    result = ''.join(parts)
    return result


# ==================== 表格提取 ====================

def _extract_table(table) -> str:
    """将 Word 表格转为 Markdown 表格"""
    rows = []
    for row in table.rows:
        cells = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
        rows.append(cells)

    if not rows:
        return ''

    # 确保每行列数一致
    max_cols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < max_cols:
            r.append('')

    lines = []
    # 表头
    lines.append('| ' + ' | '.join(rows[0]) + ' |')
    # 分隔线
    lines.append('|' + '|'.join([' --- '] * max_cols) + '|')
    # 数据行
    for row in rows[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')

    return '\n'.join(lines) + '\n'


# ==================== 文档转换 ====================

def _is_code_block_paragraph(paragraph) -> bool:
    """判断段落是否为代码块（基于背景色或字体）"""
    pPr = paragraph._element.find(qn('w:pPr'))
    if pPr is not None:
        shd = pPr.find(qn('w:shd'))
        if shd is not None:
            fill = shd.get(qn('w:fill'), '')
            if fill and fill.upper() in ('F0F0F0', 'F5F5F5', 'EFEFEF', 'FAFAFA', 'E8E8E8'):
                return True
    # 检查 run 字体
    for run in paragraph.runs:
        font = (run.font.name or '').lower()
        if font in ('consolas', 'courier new', 'monospace', 'source code pro'):
            return True
    return False


def convert_docx_to_md(input_path: str, output_path: str = None) -> str:
    """主转换函数"""
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.md'

    doc = Document(input_path)
    print(f"📖 已读取: {input_path}")

    md_lines = []
    in_code_block = False
    prev_blank = True  # 前一行是否为空

    # 获取文档中的所有 body 元素（段落 + 表格）
    body = doc.element.body

    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 'p':
            # 段落
            # 需要从 doc.paragraphs 中找到对应的 paragraph 对象
            # 简化：遍历所有段落来匹配... 实际上我们可以用另一种方法
            pass

    # 更可靠的方法：遍历 doc.paragraphs 和 doc.tables
    # 但 python-docx 的迭代不是按文档顺序的
    # 我们用 iter_block_items 模式

    for block in _iter_block_items(doc):
        if isinstance(block, Paragraph):
            para = block
            text = para.text.strip()
            style_name = para.style.name if para.style else ''

            # 空段落
            if not text:
                if not prev_blank:
                    md_lines.append('')
                    prev_blank = True
                continue

            # 标题
            h_level = _get_heading_level(para)
            if h_level > 0:
                prefix = '#' * h_level
                md_lines.append(f'{prefix} {_process_paragraph_text(para)}')
                md_lines.append('')
                prev_blank = True
                continue

            # 代码块（背景色检测）
            if _is_code_block_paragraph(para) and not in_code_block:
                md_lines.append('```')
                md_lines.append(para.text)
                in_code_block = True
                prev_blank = False
                continue
            elif not _is_code_block_paragraph(para) and in_code_block:
                md_lines.append('```')
                md_lines.append('')
                in_code_block = False
                prev_blank = True

            # 列表
            list_type, list_level = _is_list_item(para)
            if list_type == 'ul':
                indent = '  ' * list_level
                # 去除手动词头
                clean = re.sub(r'^[-*+]\s+', '', text, count=1)
                md_lines.append(f'{indent}- {_process_paragraph_text(para) if clean != text else clean}')
                prev_blank = False
                continue
            elif list_type == 'ol':
                indent = '  ' * list_level
                clean = re.sub(r'^\d+[.)]\s+', '', text, count=1)
                md_lines.append(f'{indent}1. {_process_paragraph_text(para) if clean != text else clean}')
                prev_blank = False
                continue

            # 普通段落
            md_lines.append(_process_paragraph_text(para))
            md_lines.append('')
            prev_blank = True

        elif isinstance(block, Table):
            # 关闭可能打开的代码块
            if in_code_block:
                md_lines.append('```')
                md_lines.append('')
                in_code_block = False
            md_lines.append(_extract_table(block))
            md_lines.append('')
            prev_blank = True

    # 关闭残留代码块
    if in_code_block:
        md_lines.append('```')
        md_lines.append('')

    # 写入文件
    result = '\n'.join(md_lines)
    # 清理多余空行（最多连续两个空行）
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"✅ 已生成: {output_path}")
    return output_path


# ==================== 按文档顺序迭代块 ====================

from docx.document import Document as DocType
try:
    from docx.oxml.table import CT_Tbl
except ImportError:
    from docx.oxml.table import CT_Tbl
try:
    from docx.oxml.text.paragraph import CT_P
except ImportError:
    from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph


def _iter_block_items(parent):
    """按文档顺序迭代段落和表格"""
    if isinstance(parent, DocType):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Unsupported document type")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            p = Paragraph(child, parent)
            # 跳过空段落（但保留结构）
            if p.text.strip() or p.style.name.startswith('Heading'):
                yield p
            else:
                # 空段落作为分隔
                yield p
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


# ==================== 入口 ====================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python docx_to_md.py input.docx [output.md]')
        print('示例: python docx_to_md.py 报告.docx')
        print('      python docx_to_md.py 报告.docx 报告.md')
        sys.exit(0)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert_docx_to_md(input_file, output_file)
