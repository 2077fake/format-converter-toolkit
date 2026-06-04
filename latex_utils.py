"""
LaTeX 公式简化工具 — 将 LaTeX 数学公式转为可读的 Unicode 纯文本
被 md_to_docx.py 和 md_to_pdf.py 共享使用

注意：映射表中更长的模式必须排在更短的模式之前，
     以避免部分匹配（如 \\longrightarrow 在 \\rightarrow 之前）。
"""

import re

# LaTeX 命令 → Unicode 符号映射
_LATEX_TO_UNICODE = [
    # 分数和根号
    (r'\\frac\{([^}]*)}\{([^}]*)\}', r'(\1)/(\2)'),
    (r'\\sqrt\{([^}]*)\}', r'√(\1)'),
    # 求和/积分
    (r'\\sum', 'Σ'), (r'\\prod', 'Π'), (r'\\int', '∫'),
    (r'\\infty', '∞'), (r'\\partial', '∂'),
    # 希腊字母
    (r'\\alpha', 'α'), (r'\\beta', 'β'), (r'\\gamma', 'γ'),
    (r'\\delta', 'δ'), (r'\\epsilon', 'ε'), (r'\\theta', 'θ'),
    (r'\\lambda', 'λ'), (r'\\mu', 'μ'), (r'\\pi', 'π'),
    (r'\\sigma', 'σ'), (r'\\omega', 'ω'), (r'\\Omega', 'Ω'),
    (r'\\Delta', 'Δ'), (r'\\Gamma', 'Γ'), (r'\\Lambda', 'Λ'),
    # 关系符
    (r'\\approx', '≈'), (r'\\equiv', '≡'), (r'\\neq', '≠'),
    (r'\\leq', '≤'), (r'\\geq', '≥'), (r'\\ll', '≪'), (r'\\gg', '≫'),
    # 运算符
    (r'\\pm', '±'), (r'\\mp', '∓'), (r'\\times', '×'), (r'\\cdot', '·'),
    (r'\\div', '÷'), (r'\\circ', '°'),
    (r'\\parallel', '∥'), (r'\\perp', '⊥'),
    # 箭头 — 长箭头必须在短箭头之前，避免 \rightarrow 部分匹配 \longrightarrow
    (r'\\longrightarrow', '→'), (r'\\Longrightarrow', '⇒'),
    (r'\\longleftarrow', '⟵'), (r'\\Longleftarrow', '⟸'),
    (r'\\leftrightarrow', '↔'), (r'\\Leftrightarrow', '⇔'),
    (r'\\Rightarrow', '⇒'), (r'\\Leftarrow', '⇐'),
    (r'\\rightarrow', '→'), (r'\\leftarrow', '←'),
    (r'\\mapsto', '↦'), (r'\\to', '→'),
    # 集合
    (r'\\in', '∈'), (r'\\notin', '∉'),
    (r'\\subset', '⊂'), (r'\\supset', '⊃'),
    (r'\\subseteq', '⊆'), (r'\\cup', '∪'), (r'\\cap', '∩'),
    (r'\\emptyset', '∅'), (r'\\forall', '∀'), (r'\\exists', '∃'),
    # 其他符号
    (r'\\nabla', '∇'), (r'\\propto', '∝'),
    (r'\\sim', '∼'), (r'\\cong', '≅'),
    (r'\\cdots', '⋯'), (r'\\vdots', '⋮'), (r'\\ddots', '⋱'),
    (r'\\therefore', '∴'), (r'\\because', '∵'),
    (r'\\angle', '∠'), (r'\\triangle', '△'), (r'\\square', '□'),
]


def simplify_tex(tex: str) -> str:
    """将 LaTeX 公式转为可读的纯文本"""
    t = tex.strip()
    # LaTeX → Unicode
    for pat, repl in _LATEX_TO_UNICODE:
        t = re.sub(pat, repl, t)
    # 上标下标简化：_{...} 和 _X 直接拼接, ^{...} 和 ^X 保留 ^
    t = re.sub(r'_\{([^}]+)\}', r'\1', t)
    t = re.sub(r'\^\{([^}]+)\}', r'^\1', t)
    # 无花括号的单字符下标/上标
    t = re.sub(r'_([a-zA-Z0-9])', r'\1', t)
    t = re.sub(r'\^([a-zA-Z0-9])', r'^\1', t)
    # 移除结构命令
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
    # 残留 \command → 移除
    t = re.sub(r'\\[a-zA-Z]+', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t