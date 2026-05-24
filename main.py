"""
格式转换工具箱 — Windows 11 桌面应用
基于 tkinter + ttkbootstrap 现代主题
支持亮色/暗色主题切换和窗口尺寸调节
双击运行或: python main.py
"""

import sys
import os
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import tkinter as tk


# ==================== 配置管理 ====================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_config.json")

DEFAULT_CONFIG = {
    "theme": "flatly",
    "window_size": "medium",
}

THEME_OPTIONS = [
    ("flatly",     "☀️ 亮色 (flatly)"),
    ("litera",     "📖 亮色 (litera)"),
    ("pulse",      "💜 亮色 (pulse)"),
    ("darkly",     "🌙 暗色 (darkly)"),
    ("cyborg",     "🤖 暗色 (cyborg)"),
    ("superhero",  "🦸 暗色 (superhero)"),
    ("solar",      "🌅 暗色 (solar)"),
]

SIZE_PRESETS = {
    "small":  (600, 480),
    "medium": (780, 620),
    "large":  (960, 760),
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    cfg.setdefault(k, v)
                return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ==================== 转换器定义 ====================

class ConverterTask:
    def __init__(self, name: str, icon: str, desc: str,
                 source_ext: str, target_ext: str, convert_func):
        self.name = name
        self.icon = icon
        self.desc = desc
        self.source_ext = source_ext
        self.target_ext = target_ext
        self.convert = convert_func

    def file_filter(self) -> str:
        return f"{self.source_ext.upper()} 文件 (*{self.source_ext})"


from md_to_docx import convert_md_to_docx
from docx_to_md import convert_docx_to_md
from pdf_to_md import convert_pdf_to_md
from md_to_pdf import convert_md_to_pdf

CONVERTERS = [
    ConverterTask("Markdown → Word", "\U0001f4dd\u27a1\U0001f4c4",
                  "将 Markdown 转为精美的 Word 文档",
                  ".md", ".docx", convert_md_to_docx),
    ConverterTask("Word → Markdown", "\U0001f4c4\u27a1\U0001f4dd",
                  "将 Word 文档转为 Markdown 格式",
                  ".docx", ".md", convert_docx_to_md),
    ConverterTask("Markdown → PDF", "\U0001f4dd\u27a1\U0001f4d1",
                  "将 Markdown 转为 A4 排版 PDF",
                  ".md", ".pdf", convert_md_to_pdf),
    ConverterTask("PDF → Markdown", "\U0001f4d1\u27a1\U0001f4dd",
                  "将 PDF 提取为 Markdown 文本",
                  ".pdf", ".md", convert_pdf_to_md),
]


# ==================== 主窗口 ====================

class ConverterApp:
    def __init__(self):
        self.config = load_config()
        theme = self.config.get("theme", "flatly")
        self.root = ttk.Window(themename=theme)
        self.root.title("📦 文档格式互转工具箱")
        self.root.minsize(600, 480)

        size_name = self.config.get("window_size", "medium")
        if size_name in SIZE_PRESETS:
            self._win_w, self._win_h = SIZE_PRESETS[size_name]
        else:
            self._win_w, self._win_h = 780, 620
        self.root.geometry(f"{self._win_w}x{self._win_h}")
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self._win_w) // 2
        y = (sh - self._win_h) // 2
        self.root.geometry(f"{self._win_w}x{self._win_h}+{x}+{y}")

    def _rebuild(self):
        self._win_w = self.root.winfo_width()
        self._win_h = self.root.winfo_height()
        for w in self.root.winfo_children():
            w.destroy()
        self._build_ui()
        self._center_window()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill=BOTH, expand=YES)

        # ---- 标题栏 ----
        header = ttk.Frame(main)
        header.pack(fill=X, pady=(0, 4))

        ttk.Label(header, text="📦 文档格式互转工具箱",
                  font=("Microsoft YaHei UI", 18, "bold")).pack(side=LEFT)

        right = ttk.Frame(header)
        right.pack(side=RIGHT)

        ttk.Label(right, text="v2.2 · Desktop",
                  font=("Segoe UI", 9),
                  foreground="#999").pack(side=LEFT, pady=(8, 0), padx=(0, 8))

        ttk.Button(right, text="⚙️ 设置",
                   command=self._open_settings,
                   bootstyle="outline-secondary",
                   padding=(8, 2)).pack(side=RIGHT)

        ttk.Label(main, text="选择一个转换方向，选取文件即可一键转换",
                  font=("Microsoft YaHei UI", 10),
                  foreground="#666").pack(anchor=W, pady=(0, 16))

        # ---- 可滚动卡片区（支持水平+垂直滚动）----
        sf = ttk.Frame(main)
        sf.pack(fill=BOTH, expand=YES)

        canvas = tk.Canvas(sf, highlightthickness=0,
                           bg=self.root.style.colors.bg)
        v_sb = ttk.Scrollbar(sf, orient=VERTICAL, command=canvas.yview)
        h_sb = ttk.Scrollbar(sf, orient=HORIZONTAL, command=canvas.xview)
        cc = ttk.Frame(canvas)

        cc.bind("<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=cc, anchor=NW, tags="c")
        canvas.configure(yscrollcommand=v_sb.set, xscrollcommand=h_sb.set)

        # 滚轮：纵向（检查 canvas 存活，避免关闭弹窗后报错）
        def _scroll_y(event, c=canvas):
            if c.winfo_exists():
                c.yview_scroll(-int(event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", _scroll_y)

        # Shift + 滚轮：横向
        def _scroll_x(event, c=canvas):
            if c.winfo_exists():
                c.xview_scroll(-int(event.delta / 120), "units")
        canvas.bind_all("<Shift-MouseWheel>", _scroll_x)

        for i, task in enumerate(CONVERTERS):
            card = self._make_card(cc, task)
            card.grid(row=i, column=0, sticky=EW, pady=5)
            cc.columnconfigure(0, weight=1)

        canvas.grid(row=0, column=0, sticky=NSEW)
        v_sb.grid(row=0, column=1, sticky=NS)
        h_sb.grid(row=1, column=0, sticky=EW)
        sf.grid_rowconfigure(0, weight=1)
        sf.grid_columnconfigure(0, weight=1)

        # ---- 底部状态 ----
        self.status_var = tk.StringVar(value="💡 点击上方卡片开始转换")
        self.status_lbl = ttk.Label(main, textvariable=self.status_var,
                                    font=("Microsoft YaHei UI", 9),
                                    bootstyle="secondary", padding=(14, 10))
        self.status_lbl.pack(fill=X, pady=(12, 0))

    def _make_card(self, parent, task):
        card = ttk.Frame(parent, padding=16, bootstyle="light", cursor="hand2")
        row = ttk.Frame(card)
        row.pack(fill=X)
        ttk.Label(row, text=task.icon, font=("Segoe UI", 18)).pack(side=LEFT)
        ttk.Label(row, text=task.name,
                  font=("Microsoft YaHei UI", 12, "bold"),
                  foreground="#1a1a2e").pack(side=LEFT, padx=(10, 0))
        ttk.Label(row, text="→", font=("Segoe UI", 12),
                  foreground="#1a56db").pack(side=RIGHT)
        ttk.Label(card, text=task.desc,
                  font=("Microsoft YaHei UI", 9),
                  foreground="#6b7280",
                  padding=(28, 6, 0, 0),
                  wraplength=550).pack(anchor=W)

        def bind_recursive(w):
            w.bind("<Button-1>", lambda e, t=task: self._convert(t))
            for c in w.winfo_children():
                bind_recursive(c)
        bind_recursive(card)
        return card

    # ==================== 设置弹窗 ====================

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("⚙️ 设置")
        win.resizable(True, True)
        win.transient(self.root)
        win.grab_set()

        # --- 可滚动的设置内容（水平+垂直） ---
        canvas = tk.Canvas(win, highlightthickness=0,
                           bg=self.root.style.colors.bg)
        v_sb = ttk.Scrollbar(win, orient=VERTICAL, command=canvas.yview)
        h_sb = ttk.Scrollbar(win, orient=HORIZONTAL, command=canvas.xview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=NW, tags="sf")

        canvas.configure(yscrollcommand=v_sb.set, xscrollcommand=h_sb.set)
        # 滚轮绑定（检查 canvas 存活避免关闭后报错）
        def _scroll_y(event, c=canvas):
            if c.winfo_exists():
                c.yview_scroll(-int(event.delta / 120), "units")
        def _scroll_x(event, c=canvas):
            if c.winfo_exists():
                c.xview_scroll(-int(event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", _scroll_y)
        canvas.bind_all("<Shift-MouseWheel>", _scroll_x)

        canvas.grid(row=0, column=0, sticky=NSEW)
        v_sb.grid(row=0, column=1, sticky=NS)
        h_sb.grid(row=1, column=0, sticky=EW)
        win.grid_rowconfigure(0, weight=1)
        win.grid_columnconfigure(0, weight=1)

        f = ttk.Frame(scroll_frame, padding=24)
        f.pack(fill=BOTH, expand=YES)

        # ---- 主题选择 ----
        ttk.Label(f, text="🎨 主题",
                  font=("Microsoft YaHei UI", 13, "bold")).pack(anchor=W)

        theme_var = tk.StringVar(value=self.config.get("theme", "flatly"))

        # 亮色主题组
        ttk.Label(f, text="  亮色主题",
                  font=("Microsoft YaHei UI", 10),
                  foreground="#0a7e3d").pack(anchor=W, pady=(6, 4))
        tf_light = ttk.Frame(f)
        tf_light.pack(fill=X, padx=(8, 0))
        for i, (tid, tl) in enumerate([t for t in THEME_OPTIONS if t[0] in ("flatly", "litera", "pulse")]):
            ttk.Radiobutton(tf_light, text=tl, variable=theme_var,
                            value=tid, bootstyle="info").grid(
                row=0, column=i, sticky=W, padx=(0, 24))

        # 暗色主题组
        ttk.Label(f, text="  暗色主题",
                  font=("Microsoft YaHei UI", 10),
                  foreground="#7c3aed").pack(anchor=W, pady=(10, 4))
        tf_dark = ttk.Frame(f)
        tf_dark.pack(fill=X, padx=(8, 0))
        for i, (tid, tl) in enumerate([t for t in THEME_OPTIONS if t[0] in ("darkly", "cyborg", "superhero", "solar")]):
            ttk.Radiobutton(tf_dark, text=tl, variable=theme_var,
                            value=tid, bootstyle="info").grid(
                row=0, column=i, sticky=W, padx=(0, 24))

        ttk.Separator(f).pack(fill=X, pady=16)

        # ---- 窗口尺寸 ----
        ttk.Label(f, text="📐 窗口尺寸",
                  font=("Microsoft YaHei UI", 13, "bold")).pack(anchor=W)

        size_var = tk.StringVar(value=self.config.get("window_size", "medium"))
        ssf = ttk.Frame(f)
        ssf.pack(fill=X, pady=(8, 0))

        size_options = [
            ("small",  "📱 小 (600×480)"),
            ("medium", "💻 中 (780×620)"),
            ("large",  "🖥️ 大 (960×760)"),
        ]
        for sid, sl in size_options:
            ttk.Radiobutton(ssf, text=sl, variable=size_var,
                            value=sid, bootstyle="info").pack(anchor=W, pady=3)

        ttk.Separator(f).pack(fill=X, pady=16)

        # ---- 底部按钮 ----
        bf = ttk.Frame(f)
        bf.pack(fill=X, pady=(4, 0))

        def apply():
            nt = theme_var.get()
            ns = size_var.get()
            changed_theme = nt != self.config.get("theme")
            changed_size = ns != self.config.get("window_size")

            self.config["theme"] = nt
            self.config["window_size"] = ns
            if ns in SIZE_PRESETS:
                self._win_w, self._win_h = SIZE_PRESETS[ns]
            save_config(self.config)
            win.destroy()

            if changed_theme:
                self.root.style.theme_use(nt)
                self._rebuild()
            elif changed_size:
                self.root.geometry(f"{self._win_w}x{self._win_h}")
                self._center_window()
            else:
                self._status("⚙️ 设置已应用", "info")

            self._status("⚙️ 设置已应用", "info")

        ttk.Button(bf, text="✅ 应用", command=apply,
                   bootstyle="primary", padding=(24, 8)).pack(side=LEFT, padx=(0, 12))
        ttk.Button(bf, text="取消", command=win.destroy,
                   bootstyle="secondary", padding=(16, 8)).pack(side=LEFT)

        # 设置弹窗大小 & 居中
        win.update_idletasks()
        ww, wh = 560, 420
        wx = self.root.winfo_x() + (self._win_w - ww) // 2
        wy = self.root.winfo_y() + (self._win_h - wh) // 2
        win.geometry(f"{ww}x{wh}+{wx}+{wy}")
        win.minsize(480, 320)

    # ==================== 转换逻辑 ====================

    def _convert(self, task):
        f = filedialog.askopenfilename(
            title=f"选择源文件 — {task.name}",
            initialdir=os.path.expanduser("~\\Desktop"),
            filetypes=[(task.file_filter(), f"*{task.source_ext}"),
                       ("所有文件", "*.*")]
        )
        if not f:
            return
        default = os.path.splitext(f)[0] + task.target_ext
        out = filedialog.asksaveasfilename(
            title=f"保存为 {task.target_ext}",
            initialdir=os.path.dirname(default),
            initialfile=os.path.basename(default),
            filetypes=[(f"{task.target_ext.upper()} 文件", f"*{task.target_ext}"),
                       ("所有文件", "*.*")]
        )
        if not out:
            return
        self._status(f"⏳ 正在转换: {os.path.basename(f)} ...", "info")

        def worker():
            try:
                task.convert(f, out)
                self.root.after(0, lambda: self._done(out))
            except Exception as e:
                self.root.after(0, lambda: self._fail(str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _done(self, path):
        self._status("✅ 转换成功！", "success")
        if messagebox.askyesno("转换成功",
                               f"✅ 文件已保存到:\n{path}\n\n是否打开所在文件夹？"):
            os.startfile(os.path.dirname(path))

    def _fail(self, err):
        self._status("❌ 转换失败", "danger")
        messagebox.showerror("转换失败", f"❌ 错误:\n\n{err}")

    def _status(self, text, style="secondary"):
        self.status_var.set(text)
        clr = {"info": "#1a56db", "success": "#065f46",
               "danger": "#991b1b", "secondary": "#6b7280"}
        self.status_lbl.configure(foreground=clr.get(style, "#6b7280"))

    def run(self):
        self.root.mainloop()


def main():
    ConverterApp().run()


if __name__ == "__main__":
    main()
