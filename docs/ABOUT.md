# About

## 📦 文档格式互转工具箱 (Format Converter Toolkit)

一个跨平台的文档格式转换桌面应用，使用 Python + PySide6 (Qt6) 构建。

### 🎯 项目目标

让用户能够轻松地在 **Markdown**、**Word (.docx)** 和 **PDF** 三种常用文档格式之间进行转换，特别针对中文用户优化，支持 LaTeX 数学公式渲染。

### ✨ 核心功能

1. **Markdown → Word** (`md_to_docx.py`)
   - 完整支持 Markdown 语法（标题、列表、表格、代码块、引用块等）
   - LaTeX 行内/块级公式自动转换为 Unicode 符号
   - 中文字体统一优化
   - 代码块灰色背景 + 语言标签

2. **Word → Markdown** (`docx_to_md.py`)
   - 智能识别标题层级（Heading 1~6）
   - 保留行内格式（粗体、斜体、代码）
   - 有序/无序列表转换
   - Word 表格 → Markdown 表格
   - 超链接保留

3. **Markdown → PDF** (`md_to_pdf.py`)
   - A4 纸张自动分页
   - 中英文混排优化
   - 智能折行
   - 代码块、表格、引用块美化

4. **PDF → Markdown** (`pdf_to_md.py`)
   - 逐页转换，页间分隔
   - 基于字号智能识别标题
   - 粗体/斜体格式保留
   - 简易表格检测与转换

### 🛠️ 技术栈

- **GUI 框架**: PySide6 (Qt6)
- **Word 处理**: python-docx
- **PDF 处理**: PyMuPDF (fitz)
- **LaTeX 转换**: 内置 `_simplify_tex()` 引擎

### 📦 依赖安装

```bash
pip install PySide6 python-docx PyMuPDF
```

### 📜 许可

MIT License

### 👨‍💻 作者

[2077fake](https://github.com/2077fake)

---

*最后更新: 2026-06-05*
