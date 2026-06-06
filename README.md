# 📦 格式转换工具箱

基于 Qt (PySide6) 的文档格式转换桌面应用，支持 Markdown、Word、PDF 三种格式之间的转换。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://doc.qt.io/qtforpython-6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 安装

```bash
pip install PySide6 python-docx PyMuPDF
```

## 桌面应用（推荐）

```bash
python main.py
```

## 命令行

```bash
# Markdown → Word
python md_to_docx.py input.md [output.docx]

# Word → Markdown
python docx_to_md.py input.docx [output.md]

# Markdown → PDF
python md_to_pdf.py input.md [output.pdf]

# PDF → Markdown
python pdf_to_md.py input.pdf [output.md]
```

### 批量转换

```bash
python md_to_docx.py ./input_dir/ --batch
python md_to_pdf.py ./input_dir/ --batch
python docx_to_md.py ./input_dir/ --batch
python pdf_to_md.py ./input_dir/ --batch
```

## 转换方向

| 工具 | 方向 | 说明 |
|------|------|------|
| `md_to_docx.py` | Markdown → Word | 支持 LaTeX 公式、表格、代码块、超链接 |
| `docx_to_md.py` | Word → Markdown | 保留标题、格式、列表、表格 |
| `md_to_pdf.py` | Markdown → PDF | A4 排版，支持中文混排和 LaTeX 公式 |
| `pdf_to_md.py` | PDF → Markdown | 智能识别标题、格式和表格 |

## LaTeX 公式

支持行内 `$...$` 和块级 `$$...$$` 公式，例如：

| LaTeX | 结果 |
|-------|------|
| `$\alpha + \beta = \gamma$` | α + β = γ |
| `$\int_0^\infty e^{-x^2} dx$` | ∫₀^∞ e⁻ˣ² dx |

## 项目结构

```
format-converter-toolkit/
├── main.py              # GUI 桌面应用主入口
├── md_to_docx.py        # Markdown → Word
├── docx_to_md.py        # Word → Markdown
├── md_to_pdf.py         # Markdown → PDF
├── pdf_to_md.py         # PDF → Markdown
├── latex_utils.py       # LaTeX 公式简化工具
├── shared_parse.py      # 共享 Markdown 解析模块
├── requirements.txt     # Python 依赖
└── tests/               # 单元测试
```

## License

[MIT](LICENSE)
