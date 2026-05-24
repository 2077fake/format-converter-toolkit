# 📝 md2docx — Markdown 转 Word 文档工具

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

依赖仅需一个库：

| 库 | 用途 |
|---|---|
| [python-docx](https://python-docx.readthedocs.io/) | 生成 Word 文档 |

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

## 🏗️ 项目结构

```
md2docx/
├── md_to_docx.py      # 主程序
├── requirements.txt    # 依赖清单
├── README.md           # 本文件
└── 测试示例.md         # 测试用 Markdown
```

## 🔧 技术架构

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

## 📜 许可

MIT License
