# 📦 格式转换工具箱 v4.0

> 基于 Qt (PySide6) 构建的现代化文档格式转换桌面应用，支持 Markdown、Word、PDF 三种格式之间的无缝转换。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://doc.qt.io/qtforpython-6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ v4.0 新特性

### 🎨 全新界面设计
- **WorkBuddy 风格扁平化设计** — 干净平整的顶部栏，告别花哨渐变
- **双主题统一** — 浅色/深色主题采用同一设计语言，切换无缝衔接
- **卡片式布局** — 精致阴影 + 悬停高亮，交互更流畅

### 🖱️ 交互增强
- **拖拽转换** — 支持将文件直接拖拽到卡片或全局拖拽区
- **批量模式** — 一键切换，一次转换多个文件，带实时进度条
- **转换历史** — 自动记录所有转换，支持查看和清除历史

### 🛠️ 技术改进
- **线程安全** — 使用 QThread + Signal 机制，彻底解决 GUI 卡顿
- **主题感知组件** — 所有对话框、卡片、标签都跟随主题变化
- **智能代码块检测** — Word 转 Markdown 代码块识别更准确
- **可点击超链接** — Markdown 转 Word 生成真实超链接
- **CLI 批量处理** — 命令行支持 `--batch` 参数批量转换目录

---

## 🔁 转换方向

| 工具 | 方向 | 描述 |
|------|------|------|
| `md_to_docx.py` | Markdown → Word | 支持 LaTeX 公式、表格、代码块、可点击超链接 |
| `docx_to_md.py` | Word → Markdown | 保留标题、格式、列表、表格和代码块 |
| `md_to_pdf.py` | Markdown → PDF | A4 排版精美的 PDF 文档，支持中文混排 |
| `pdf_to_md.py` | PDF → Markdown | 智能识别标题、格式和表格结构 |

---

## 🖥️ 快速开始

### 安装依赖

```bash
pip install PySide6 python-docx PyMuPDF
```

### 启动桌面应用（推荐）

```bash
python main.py
```

### 命令行使用

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

### 命令行批量转换

```bash
# 批量转换目录下所有 .md 文件
python md_to_docx.py ./markdown_files/ --batch
python md_to_pdf.py ./markdown_files/ --batch

# 批量转换目录下所有 .docx 文件
python docx_to_md.py ./docx_files/ --batch

# 批量转换目录下所有 .pdf 文件
python pdf_to_md.py ./pdf_files/ --batch
```

---

## 🎯 核心特性

### md_to_docx — Markdown 转 Word
- ✅ 完整 Markdown 支持（标题、列表、表格、代码块等）
- ✅ LaTeX 数学公式自动转为 Unicode 符号
- ✅ 中文字体优化，全局字体统一
- ✅ 代码块带灰色背景和语言标签
- ✅ **可点击超链接**
- ✅ 引用块左侧灰色边框样式

### docx_to_md — Word 转 Markdown
- ✅ 自动识别标题层级（Heading 1~6）
- ✅ 保留行内格式（粗体、斜体、代码）
- ✅ 有序/无序列表智能识别
- ✅ Word 表格 → Markdown 表格
- ✅ 代码块自动检测（背景色 + 字体 + 字号综合判断）

### md_to_pdf — Markdown 转 PDF
- ✅ A4 纸张自动分页
- ✅ 中英文混排优化，智能折行
- ✅ LaTeX 行内/块级公式
- ✅ 代码块深色背景 + 等宽字体
- ✅ 表格渲染，表头加粗
- ✅ 引用块左侧灰条
- ✅ 超链接蓝色显示

### pdf_to_md — PDF 转 Markdown
- ✅ 逐页转换，页间分隔
- ✅ 基于字号智能识别标题（多种模式匹配）
- ✅ 粗体/斜体格式保留
- ✅ 简易表格检测与转换
- ✅ 列表项自动识别

---

## 🧮 LaTeX 公式支持

支持行内公式 `$...$` 和块级公式 `$$...$$`：

| LaTeX | 转换结果 |
|-------|---------|
| `$\alpha + \beta = \gamma$` | α + β = γ |
| `$\int_0^\infty e^{-x^2} dx$` | ∫₀^∞ e⁻ˣ² dx |
| `$R_{out} = \frac{V_{out}}{I_{out}}$` | Rout = Vout / Iout |

> ⚠️ 复杂 LaTeX 环境会自动降级为可读文本。

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| GUI 框架 | PySide6 (Qt6) |
| Word 处理 | python-docx |
| PDF 处理 | PyMuPDF (fitz) |
| LaTeX 转换 | 内置 `simplify_tex()` 引擎 |

---

## 📂 项目结构

```
format-converter-toolkit/
├── main.py              # GUI 桌面应用主入口
├── md_to_docx.py        # Markdown → Word
├── docx_to_md.py        # Word → Markdown
├── md_to_pdf.py         # Markdown → PDF
├── pdf_to_md.py         # PDF → Markdown
├── latex_utils.py       # LaTeX 公式简化工具
├── app_config.json      # 应用配置（自动生成）
├── conversion_history.json  # 转换历史（自动生成）
├── requirements.txt     # Python 依赖
├── README.md            # 本文件
└── 资源/                # 测试文件
```

---

## 📝 License

[MIT](LICENSE)
- 📐 **窗口尺寸**：小 / 中 / 大

配置自动保存到 `app_config.json`。

---

## 🏗️ 项目结构

```
format-converter-toolkit/
├── main.py              # 🖥️ Qt 桌面应用入口 (PySide6)
├── md_to_docx.py        # Markdown → Word 核心逻辑
├── docx_to_md.py        # Word → Markdown 核心逻辑
├── md_to_pdf.py         # Markdown → PDF 核心逻辑
├── pdf_to_md.py         # PDF → Markdown 核心逻辑
├── latex_utils.py       # LaTeX 公式简化工具
├── requirements.txt     # 依赖清单
├── README.md            # 项目文档
└── 测试示例.md          # 测试用 Markdown
```

---

## 📦 依赖

| 库 | 版本 | 用途 |
|---|---|---|
| PySide6 | >= 6.5.0 | Qt GUI 框架 |
| python-docx | >= 1.1.0 | Word 文档读写 |
| PyMuPDF | >= 1.23.0 | PDF 文档处理 |

安装依赖：

```bash
pip install -r requirements.txt
```

---

## ➕ 添加新转换格式

在 `main.py` 的 `CONVERTERS` 列表中添加一行即可注册新的转换器：

```python
ConverterTask(
    "HTML → Markdown",             # 显示名称
    "🌐➜📝",                      # emoji 图标
    "将 HTML 文件转为 Markdown",    # 描述
    ".html", ".md",                # 源/目标扩展名
    html_to_md_function            # 转换函数(input_path, output_path)
)
```

---

## 📜 许可

MIT License — 详见 [LICENSE](LICENSE) 文件。
