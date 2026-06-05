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
                # 检查 numId 对应的编号格式是 bullet 还是 number
                # 通过查看文档的 numbering 部件判断
                try:
                    numbering_part = paragraph.part.numbering_part
                    if numbering_part is not None:
                        num_xml = numbering_part._element
                        num_def = num_xml.find(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}num[@{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}numId="{numId.get(qn("w:val"))}"]')
                        if num_def is not None:
                            abstract_num_id = num_def.find(qn('w:abstractNumId'))
                            if abstract_num_id is not None:
                                abs_id = abstract_num_id.get(qn('w:val'))
                                abs_num = num_xml.find(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}abstractNum[@{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}abstractNumId="{abs_id}"]')
                                if abs_num is not None:
                                    lvl_elem = abs_num.find(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}lvl[@{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}ilvl="{level}"]')
                                    if lvl_elem is not None:
                                        num_fmt = lvl_elem.find(qn('w:numFmt'))
                                        if num_fmt is not None:
                                            fmt_val = num_fmt.get(qn('w:val'), '')
                                            if fmt_val in ('bullet', 'hybridBullet'):
                                                return ('ul', level)
                                            else:
                                                return ('ol', level)
                except (AttributeError, KeyError, ValueError):
                    pass
                return ('ol', level)
    # 手动词头检测
    text = paragraph.text.strip()
    if re.match(r'^[-*+]\s', text):
        return ('ul', 0)
    if re.match(r'^\d+[.)]\s', text):
        return ('ol', 0)
    return (None, 0)


# ==================== 行内格式提取 ====================

def _extract_run_text(run, para_text: str, runs_processed: set = None, doc=None) -> str:
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

    # 检查超链接（通过 relationship ID 查找真实 URL）
    hyperlink_url = None
    parent = run._element.getparent()
    if parent is not None and parent.tag == qn('w:hyperlink'):
        r_id = parent.get(qn('r:id'))
        if r_id and doc is not None:
            try:
                hyperlink_url = doc.part.rels[r_id].target_ref
            except (KeyError, AttributeError):
                hyperlink_url = r_id

    # 格式标记（标题文本不加粗，避免 # **Title** 的问题）
    prefix = ''
    suffix = ''

    if run.bold and run.italic:
        prefix, suffix = '***', '***'
    elif run.bold:
        prefix, suffix = '**', '**'
    elif run.italic:
        prefix, suffix = '*', '*'

    # 等宽字体 → 行内代码（浅色背景或小型文本不误判）
    font_name = (run.font.name or '').lower()
    if font_name in ('consolas', 'courier new', 'monospace', 'source code pro'):
        prefix, suffix = '`', '`'

    # 超链接
    if hyperlink_url:
        return f'[{text}]({hyperlink_url})'

    return f'{prefix}{text}{suffix}'


def _process_paragraph_text(paragraph, doc=None) -> str:
    """提取段落的 Markdown 文本（含行内格式）"""
    runs = paragraph.runs
    if not runs:
        return paragraph.text

    parts = []
    for run in runs:
        parts.append(_extract_run_text(run, paragraph.text, doc=doc))

    return ''.join(parts)


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
    """判断段落是否为代码块（综合背景色 + 字体 + 字号判断）"""
    runs = [r for r in paragraph.runs if r.text.strip()]
    if not runs:
        return False

    # 1) 检查是否所有非空 run 都是等宽字体
    mono_fonts = {'consolas', 'courier new', 'monospace', 'source code pro',
                  'fira code', 'jetbrains mono', 'cascadia code', 'liberation mono',
                  'dejavu sans mono', 'menlo', 'monaco', 'sf mono', 'inconsolata',
                  'ubuntu mono', 'droid sans mono', 'pt mono', 'noto mono'}
    mono_count = sum(1 for r in runs if (r.font.name or '').lower() in mono_fonts)
    if mono_count == len(runs):
        return True

    # 2) 检查段落背景色（浅灰通常表示代码块）
    pPr = paragraph._element.find(qn('w:pPr'))
    if pPr is not None:
        shd = pPr.find(qn('w:shd'))
        if shd is not None:
            fill = shd.get(qn('w:fill'), '')
            if fill:
                try:
                    r, g, b = int(fill[0:2], 16), int(fill[2:4], 16), int(fill[4:6], 16)
                    # 浅灰背景（非纯白）+ 等宽字体比例 > 一半
                    if r >= 0xC0 and g >= 0xC0 and b >= 0xC0 and (r, g, b) != (0xFF, 0xFF, 0xFF):
                        if mono_count >= len(runs) * 0.5:
                            return True
                except (ValueError, IndexError):
                    pass

    # 3) 检查字号是否明显小于正文字号（代码块通常用更小字号）
    if runs:
        avg_size = sum(r.font.size.pt if r.font.size else 11 for r in runs) / len(runs)
        if avg_size <= 9.5:  # 代码块通常 ≤ 9.5pt
            if mono_count >= len(runs) * 0.3:  # 有部分等宽字体即可
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

    for block in _iter_block_items(doc):
        if isinstance(block, Paragraph):
            para = block
            text = para.text.strip()
            style_name = para.style.name if para.style else ''

            # === 代码块状态机（优先检查，确保代码块及时关闭）===
            is_code = _is_code_block_paragraph(para)
            if is_code and not in_code_block:
                # 进入代码块
                code_text = para.text
                # 分离语言标签（末行如（python））
                code_lines = code_text.split('\n')
                if code_lines and re.match(r'^[（(]\w+[）)]$', code_lines[-1].strip()):
                    lang = code_lines[-1].strip().strip('（）()')
                    code_lines = code_lines[:-1]
                    md_lines.append(f'```{lang}')
                else:
                    md_lines.append('```')
                for code_line in code_lines:
                    md_lines.append(code_line)
                in_code_block = True
                prev_blank = False
                continue
            elif not is_code and in_code_block:
                # 离开代码块
                md_lines.append('```')
                md_lines.append('')
                in_code_block = False
                prev_blank = True
                # 不要 continue——让这个段落继续按普通逻辑处理

            # 空段落
            if not text:
                if not prev_blank:
                    md_lines.append('')
                    prev_blank = True
                continue

            # 标题（去除加粗格式，因为 Word 标题样式自带加粗）
            h_level = _get_heading_level(para)
            if h_level > 0:
                prefix = '#' * h_level
                t = _process_paragraph_text(para, doc)
                # 去除标题中多余的加粗标记（Word 标题样式自带加粗）
                t = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', t)
                t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
                t = re.sub(r'\*(.+?)\*', r'\1', t)
                md_lines.append(f'{prefix} {t}')
                md_lines.append('')
                prev_blank = True
                continue

            # 列表
            list_type, list_level = _is_list_item(para)
            if list_type == 'ul':
                indent = '  ' * list_level
                item_text = _process_paragraph_text(para, doc)
                item_text = re.sub(r'^[-*+]\s+', '', item_text, count=1)
                md_lines.append(f'{indent}- {item_text}')
                prev_blank = False
                continue
            elif list_type == 'ol':
                indent = '  ' * list_level
                item_text = _process_paragraph_text(para, doc)
                item_text = re.sub(r'^\d+[.)]\s+', '', item_text, count=1)
                md_lines.append(f'{indent}1. {item_text}')
                prev_blank = False
                continue

            # 普通段落
            md_lines.append(_process_paragraph_text(para, doc))
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
            if p.text.strip() or (p.style and p.style.name and p.style.name.startswith('Heading')):
                yield p
            else:
                # 空段落作为分隔
                yield p
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


# ==================== 入口 ====================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('📝 Word → Markdown 转换工具')
        print(f'用法: python {os.path.basename(__file__)} <input.docx> [output.md]')
        print(f'      python {os.path.basename(__file__)} <input_dir> --batch')
        print('示例:')
        print('  python docx_to_md.py 报告.docx')
        print('  python docx_to_md.py 报告.docx 报告.md')
        print('  python docx_to_md.py ./docx_files/ --batch')
        sys.exit(0)

    input_path = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == '--batch':
        import glob
        input_dir = input_path
        if not os.path.isdir(input_dir):
            print(f"❌ 目录不存在: {input_dir}")
            sys.exit(1)
        docx_files = glob.glob(os.path.join(input_dir, '*.docx'))
        if not docx_files:
            print(f"❌ 目录中未找到 .docx 文件: {input_dir}")
            sys.exit(1)
        print(f"📦 批量转换 {len(docx_files)} 个文件...")
        success = 0
        for f in docx_files:
            try:
                convert_docx_to_md(f)
                success += 1
            except Exception as e:
                print(f"❌ 转换失败 {f}: {e}")
        print(f"✅ 批量完成: {success}/{len(docx_files)}")
    else:
        convert_docx_to_md(input_path, sys.argv[2] if len(sys.argv) > 2 else None)
        sys.exit(0)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    convert_docx_to_md(input_file, output_file)
