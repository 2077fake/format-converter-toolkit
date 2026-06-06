# About

## 📦 Format Converter Toolkit

一个基于 Qt (PySide6) 的文档格式转换桌面应用，支持 Markdown、Word (.docx)、PDF 三种格式之间的相互转换，特别优化中文支持与 LaTeX 数学公式。

### 转换方向

| 方向 | 文件 | 说明 |
|------|------|------|
| Markdown → Word | `md_to_docx.py` | 完整 Markdown 支持，LaTeX 公式转 Unicode，可点击超链接 |
| Word → Markdown | `docx_to_md.py` | 保留标题层级、行内格式、列表、表格、代码块 |
| Markdown → PDF | `md_to_pdf.py` | A4 排版，中英文混排，LaTeX 行内/块级公式 |
| PDF → Markdown | `pdf_to_md.py` | 智能识别标题（基于字号）、粗体/斜体、表格 |

### GUI 功能

- 卡片式桌面应用，亮色/暗色双主题
- 文件拖拽转换，批量模式 + 进度条
- 转换历史记录

### 技术栈

- **GUI**: PySide6 (Qt6)
- **Word**: python-docx
- **PDF**: PyMuPDF (fitz)
- **LaTeX**: 内置 simplify_tex() 引擎

### 依赖

```bash
pip install PySide6 python-docx PyMuPDF
```

### 许可

MIT License

### 作者

[2077fake](https://github.com/2077fake)

---

*最后更新: 2026-06-06*
