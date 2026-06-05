# 📦 文档格式互转工具箱

> 基于 Qt (PySide6) 构建的现代化文档格式转换工具，支持 Markdown、Word、PDF 三种格式之间的无缝转换。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://doc.qt.io/qtforpython-6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 更新日志 (v3.0)

- 🎨 **全新 Qt GUI 界面** — 基于 PySide6 重构，现代化卡片式设计
- 🌗 **亮色/暗色主题切换** — 一键切换主题，支持持久化配置
- 🖱️ **交互式卡片布局** — 悬停高亮、点击即转，视觉反馈更直观
- 📱 **自适应窗口大小** — 支持多种窗口尺寸，界面自动适配
- 🚀 **异步转换** — 后台线程执行，GUI 永不卡顿

---

## 🔁 转换方向

| 工具 | 方向 | 描述 |
|------|------|------|
| `md_to_docx.py` | Markdown → Word | 支持 LaTeX 公式、表格、代码块的完整转换 |
| `docx_to_md.py` | Word → Markdown | 保留标题、格式、列表、表格和超链接 |
| `md_to_pdf.py` | Markdown → PDF | A4 排版精美的 PDF 文档，支持中文混排 |
| `pdf_to_md.py` | PDF → Markdown | 智能识别标题、格式和表格结构 |

---

## 🖥️ 快速开始

### 安装依赖

```bash
pip install PySide6 python-docx PyMuPDF
```

### 启动桌面应用

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

---

## 📸 界面预览

```
┌─────────────────────────────────────────────────┐
│  📦 文档格式互转工具箱              v3.0 · Qt  │
│                                      [⚙️ 设置] │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  📝➜📄  Markdown → Word                  │ │
│  │  将 Markdown 转为精美的 Word 文档...      │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │  📄➜📝  Word → Markdown                  │ │
│  │  将 Word 文档转为 Markdown 格式...        │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │  📝➜📑  Markdown → PDF                   │ │
│  │  将 Markdown 转为 A4 排版精美的 PDF...    │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │  📑➜📝  PDF → Markdown                   │ │
│  │  将 PDF 提取为 Markdown 文本...           │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  💡 点击上方卡片开始转换                        │
└─────────────────────────────────────────────────┘
```

---

## 🎯 核心特性

### md_to_docx — Markdown 转 Word

- ✅ 完整 Markdown 支持（标题、列表、表格、代码块等）
- ✅ LaTeX 数学公式自动转为 Unicode 符号
- ✅ 中文字体优化，全局字体统一
- ✅ 代码块带灰色背景和语言标签
- ✅ 引用块左侧灰色边框样式

### docx_to_md — Word 转 Markdown

- ✅ 自动识别标题层级（Heading 1~6）
- ✅ 保留行内格式（粗体、斜体、代码）
- ✅ 有序/无序列表转换
- ✅ Word 表格 → Markdown 表格
- ✅ 超链接和图片占位保留

### md_to_pdf — Markdown 转 PDF

- ✅ A4 纸张自动分页
- ✅ 中英文混排优化
- ✅ 代码块、表格、引用块美化
- ✅ LaTeX 公式渲染
- ✅ 智能折行

### pdf_to_md — PDF 转 Markdown

- ✅ 逐页转换，页间分隔
- ✅ 基于字号智能识别标题
- ✅ 粗体/斜体格式保留
- ✅ 简易表格检测与转换

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

## ⚙️ 设置

点击右上角 **⚙️ 设置** 按钮，可自定义：

- 🎨 **主题**：亮色 / 暗色
- 🔤 **字体**：多种中文字体可选
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
