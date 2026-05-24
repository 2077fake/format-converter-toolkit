# 📝 文档格式互转工具箱

一键在 Markdown、Word、PDF 三种格式之间自由转换。

## 🔁 转换方向

| 工具 | 方向 | 命令 |
|------|------|------|
| `md_to_docx.py` | Markdown → Word | `python md_to_docx.py input.md` |
| `docx_to_md.py` | Word → Markdown | `python docx_to_md.py input.docx` |
| `md_to_pdf.py` | Markdown → PDF | `python md_to_pdf.py input.md` |
| `pdf_to_md.py` | PDF → Markdown | `python pdf_to_md.py input.pdf` |

## 🖥️ 桌面应用

提供图形化界面，一键转换更方便：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动桌面程序
python main.py
```

> 界面支持 4 种转换方向的点选式操作，后台异步执行不卡顿。

---

# ① md_to_docx — Markdown 转 Word

将 Markdown（`.md`）文件一键转换为格式精美的 Word（`.docx`）文档，**完整支持 LaTeX 数学公式**。

## ✨ 特性

- 🚀 **零依赖图片渲染** — LaTeX 公式转为 Unicode 符号 + Cambria Math 字体，无需 matplotlib / LaTeX 引擎
- 📐 **完整 Markdown 支持** — 标题、段落、粗体、斜体、行内代码、链接、图片占位
- 📋 **列表与表格** — 有序/无序列表、嵌套列表、Markdown 表格
- 🧮 **LaTeX 公式** — `$...$` 行内公式 + `$$...$$` 块级公式，自动转换为可读纯文本
  - 希腊字母：`\alpha`→α, `\beta`→β, `\pi`→π ...
  - 运算符：`\times`→×, `\cdot`→·, `\pm`→± ...
  - 关系符：`\leq`→≤, `\geq`→≥, `\approx`→≈ ...
  - 下标合并：`R_{out}`→Rout, `V_{DD}`→VDD
- 🎨 **中文字体优化** — 默认微软雅黑，全局字体统一不跳跃
- 💻 **代码块** — 围栏式代码块带灰色背景 + 语言标签
- 📊 **表格** — 自动识别 Markdown 表格，带 Word 内置样式
- 💬 **引用块** — 左侧灰色边框 + 斜体引用样式

## 📦 安装

```bash
pip install -r requirements.txt
```

依赖仅需两个库：

| 库 | 用途 |
|---|---|
| [python-docx](https://python-docx.readthedocs.io/) | Word 文档读写 |
| [PyMuPDF](https://pymupdf.readthedocs.io/) | PDF 文本提取 |

## 🚀 使用

```bash
python md_to_docx.py input.md [output.docx]
```

### 示例

```bash
# 自动生成同名 .docx
python md_to_docx.py readme.md

# 指定输出文件名
python md_to_docx.py 笔记.md 整理好的笔记.docx
```

## 📄 Markdown 编写建议

### 公式编写

行内公式用 `$...$`，块级公式用 `$$...$$`：

```markdown
增益公式为 $A_v = -g_m R_D$，其中：

$$g_m = \sqrt{2 \mu_n C_{ox} \frac{W}{L} I_D}$$
```

> ⚠️ 复杂 LaTeX 环境（如 `\begin{cases}`）会自动降级为可读文本。

### 下标命名

推荐用花括号包裹多字符下标，转换后会自动拼接：

| LaTeX | 转换结果 |
|-------|---------|
| `$V_{in}$` | Vin |
| `$R_{out}$` | Rout |
| `$V_{DD}$` | VDD |

---

# ② docx_to_md — Word 转 Markdown

将 Word（`.docx`）文档转为 Markdown（`.md`），保留结构和格式。

## ✨ 特性

- 📐 **标题识别** — 自动识别 Word 标题样式（Heading 1~6 / 标题1~6）→ `# ~ ######`
- 🔤 **行内格式** — 粗体 → `**text**`、斜体 → `*text*`、粗斜体 → `***text***`
- 💻 **代码块** — 等宽字体段落自动识别为代码块（Consolas 等）
- 📋 **列表** — 有序/无序列表自动转换
- 📊 **表格** — Word 表格 → Markdown 表格
- 🔗 **超链接** — 保留 `[text](url)` 格式
- 🖼️ **图片占位** — 标记图片位置

## 🚀 使用

```bash
python docx_to_md.py input.docx [output.md]
```

### 示例

```bash
# 自动生成同名 .md
python docx_to_md.py 报告.docx

# 指定输出文件名
python docx_to_md.py 论文.docx 论文笔记.md
```

---

# ③ pdf_to_md — PDF 转 Markdown

将 PDF 文件转为 Markdown（`.md`），智能识别文档结构。

## ✨ 特性

- 📄 **逐页转换** — 按页组织，页间用 `---` 分隔
- 📐 **标题检测** — 基于字号/加粗自动识别标题层级
- 🔤 **格式保留** — 粗体、斜体自动转为 Markdown 标记
- 📊 **简易表格** — 检测对齐文本并尝试转为 Markdown 表格
- 🖼️ **图片标记** — 嵌入图片以占位符标记
- 📏 **字号感知** — 自动统计全文正文字号，智能判断标题

## 🚀 使用

```bash
python pdf_to_md.py input.pdf [output.md]
```

### 示例

```bash
# 自动生成同名 .md
python pdf_to_md.py 论文.pdf

# 指定输出文件名
python pdf_to_md.py 合同.pdf 合同文本.md
```

> ⚠️ **注意**：PDF 转换效果取决于 PDF 本身的结构化程度。扫描版 PDF（纯图片）无法提取文字，请先用 OCR 工具处理。

---

# ④ md_to_pdf — Markdown 转 PDF

将 Markdown（`.md`）文件一键转换为排版精美的 PDF 文档。

## ✨ 特性

- 📄 **完整 Markdown 支持** — 标题、段落、粗体、斜体、行内代码、链接、图片占位
- 📋 **列表与表格** — 有序/无序列表、Markdown 表格（表头深色背景）
- 💻 **代码块** — 灰色背景 + 等宽字体渲染，自动识别语言标签
- 💬 **引用块** — 左侧灰色边框 + 斜体引用样式
- 🧮 **LaTeX 公式** — `$...$` 行内公式 + `$$...$$` 块级公式
- ➖ **水平分割线**
- 📐 **A4 排版** — 自动分页、智能折行、中英文混排

## 🚀 使用

```bash
python md_to_pdf.py input.md [output.pdf]
```

### 示例

```bash
# 自动生成同名 .pdf
python md_to_pdf.py readme.md

# 指定输出文件名
python md_to_pdf.py 笔记.md 整理好的笔记.pdf
```

---

## 🏗️ 项目结构

```
文档互转工具箱/
├── main.py              # 🖥️ 桌面应用入口
├── md_to_docx.py        # Markdown → Word
├── docx_to_md.py        # Word → Markdown
├── md_to_pdf.py         # Markdown → PDF
├── pdf_to_md.py         # PDF → Markdown
├── requirements.txt     # 依赖清单
├── README.md            # 本文件
└── 测试示例.md          # 测试用 Markdown
```

---

## 🔧 技术架构（md_to_docx）

```
Markdown 文件
    │
    ▼
parse_markdown()        ← 解析为结构化元素（标题/段落/列表/表格/公式/代码块）
    │
    ▼
_simplify_tex()         ← LaTeX → Unicode 符号转换
    │
    ▼
process_inline_text()   ← 行内格式处理（粗体/斜体/代码/链接/$公式$）
    │
    ▼
add_elements_to_doc()   ← 写入 python-docx Word 文档
    │
    ▼
.docx 输出
```

## 📋 支持的 Markdown 元素

| 元素 | 语法 | 支持 |
|------|------|:--:|
| 标题 | `# H1` ~ `###### H6` | ✅ |
| 粗体 | `**text**` | ✅ |
| 斜体 | `*text*` | ✅ |
| 粗斜体 | `***text***` | ✅ |
| 行内代码 | `` `code` `` | ✅ |
| 链接 | `[text](url)` | ✅ |
| 图片 | `![alt](url)` | 占位文字 |
| 无序列表 | `- item` | ✅ |
| 有序列表 | `1. item` | ✅ |
| 代码块 | ` ```lang ``` ` | ✅ |
| 引用块 | `> quote` | ✅ |
| 水平线 | `---` | ✅ |
| 表格 | `\| col \| col \|` | ✅ |
| 行内公式 | `$...$` | ✅ |
| 块级公式 | `$$...$$` | ✅ |

## ➕ 添加新转换格式

在 `main.py` 的 `CONVERTERS` 列表中添加一行即可在桌面应用中注册新的转换器：

```python
ConverterTask(
    "HTML → Markdown",       # 显示名称
    "\U0001f310\u27a1\U0001f4dd",  # emoji 图标
    "将 HTML 文件转为 Markdown",    # 描述
    ".html", ".md",           # 源/目标扩展名
    html_to_md_function       # 你的转换函数(input_path, output_path)
)
```

然后在 `md_to_docx.py` 中复用 `parse_markdown()` 解析器、`_simplify_tex()` 公式引擎等核心模块。

## 📜 许可

MIT License
