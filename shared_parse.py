"""Shared Markdown parsing logic reused by md_to_docx and md_to_pdf.

Functions:
- _merge_display_math: 跨行 $$...$$ 合并为单行
- parse_markdown:       解析 Markdown → 结构化元素列表
"""

import re


def _merge_display_math(lines: list) -> list:
    """跨行 $$...$$ 合并为单行"""
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
