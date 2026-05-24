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
    "font_family": "Microsoft YaHei UI",
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

FONT_OPTIONS = [
    ("Microsoft YaHei UI",      "📝 微软雅黑 (默认)"),
    ("SimSun",                  "📜 宋体"),
    ("SimHei",                  "🖌️ 黑体"),
    ("KaiTi",                   "🖋️ 楷体"),
    ("DengXian",                "📏 等线"),
    ("Microsoft JhengHei UI",   "🇹🇼 微軟正黑體"),
    ("Segoe UI",                "🔤 Segoe UI"),
    ("Arial",                   "🔤 Arial"),
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

        # 自适应相关存储
        self._desc_labels = []       # 卡片描述 Label
        self._card_frames = []       # 卡片 Frame 引用
        self._icon_labels = []       # 图标 Label
        self._name_labels = []       # 卡片标题 Label
        self._main_frame = None

        self._build_ui()
        # 窗口大小变化监听
        self.root.bind("<Configure>", self._on_window_resize, add="+")

    def _scale(self) -> float:
        """根据当前窗口宽度返回缩放倍数，以 780 为基准"""
        w = max(self.root.winfo_width(), 600)
        ratio = w / 780.0
        return max(0.7, min(1.4, ratio))

    @property
    def _font(self) -> str:
        """返回用户配置的界面字体"""
        return self.config.get("font_family", "Microsoft YaHei UI")

    def _on_window_resize(self, event=None):
        """窗口大小变化时自适应调整字体/图标/折行"""
        if not hasattr(self, '_desc_labels') or not self._desc_labels:
            return
        if event and event.widget != self.root:
            return

        s = self._scale()
        f = self._font

        # 1) 标题
        if hasattr(self, '_heading_label') and self._heading_label:
            sz = max(14, min(24, int(18 * s)))
            self._heading_label.configure(font=(f, sz, "bold"))

        # 2) 副标题
        if hasattr(self, '_subtitle_label') and self._subtitle_label:
            sz = max(8, min(13, int(10 * s)))
            self._subtitle_label.configure(font=(f, sz))

        # 3) 卡片
        pad = max(10, min(24, int(16 * s)))
        for i in range(len(CONVERTERS)):
            if i < len(self._icon_labels):
                sz = max(14, min(26, int(18 * s)))
                self._icon_labels[i].configure(font=("Segoe UI", sz))
            if i < len(self._name_labels):
                sz = max(9, min(16, int(12 * s)))
                self._name_labels[i].configure(font=(f, sz, "bold"))
            if i < len(self._desc_labels):
                sz = max(7, min(12, int(9 * s)))
                cw = self._canvas.winfo_width() - 80 if self._canvas.winfo_width() > 80 else 300
                wrap = max(200, min(800, int(cw)))
                self._desc_labels[i].configure(font=(f, sz), wraplength=wrap)

        for card in self._card_frames:
            try:
                card.configure(padding=(pad, pad))
            except Exception:
                pass

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

        self._heading_label = ttk.Label(header, text="📦 文档格式互转工具箱",
                                        font=(self._font, 18, "bold"))
        self._heading_label.pack(side=LEFT)

        right = ttk.Frame(header)
        right.pack(side=RIGHT)

        ttk.Label(right, text="v2.2 · Desktop",
                  font=("Segoe UI", 9),
                  foreground="#999").pack(side=LEFT, pady=(8, 0), padx=(0, 8))

        ttk.Button(right, text="⚙️ 设置",
                   command=self._open_settings,
                   bootstyle="outline-secondary",
                   padding=(8, 2)).pack(side=RIGHT)

        self._subtitle_label = ttk.Label(main, text="选择一个转换方向，选取文件即可一键转换",
                                         font=(self._font, 10),
                                         foreground="#666")
        self._subtitle_label.pack(anchor=W, pady=(0, 16))

        # ---- 可滚动卡片区（支持水平+垂直滚动）----
        sf = ttk.Frame(main)
        sf.pack(fill=BOTH, expand=YES)

        self._canvas = tk.Canvas(sf, highlightthickness=0,
                                 bg=self.root.style.colors.bg)
        v_sb = ttk.Scrollbar(sf, orient=VERTICAL, command=self._canvas.yview)
        h_sb = ttk.Scrollbar(sf, orient=HORIZONTAL, command=self._canvas.xview)
        cc = ttk.Frame(self._canvas)
        cc.bind("<Configure>",
                lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.cc_window = self._canvas.create_window(
            (0, 0), window=cc, anchor=NW, tags="c")
        self._canvas.configure(yscrollcommand=v_sb.set, xscrollcommand=h_sb.set)

        # 滚轮：纵向（检查 canvas 存活，避免关闭弹窗后报错）
        def _scroll_y(event, c=self._canvas):
            if c.winfo_exists():
                c.yview_scroll(-int(event.delta / 120), "units")
        self._canvas.bind_all("<MouseWheel>", _scroll_y)

        # Shift + 滚轮：横向
        def _scroll_x(event, c=self._canvas):
            if c.winfo_exists():
                c.xview_scroll(-int(event.delta / 120), "units")
        self._canvas.bind_all("<Shift-MouseWheel>", _scroll_x)

        # 清空列表（防止 _rebuild 重复添加）
        self._desc_labels.clear()
        self._card_frames.clear()
        self._icon_labels.clear()
        self._name_labels.clear()

        for i, task in enumerate(CONVERTERS):
            card = self._make_card(cc, task)
            card.grid(row=i, column=0, pady=5)

        self._canvas.grid(row=0, column=0, sticky=NSEW)
        v_sb.grid(row=0, column=1, sticky=NS)
        h_sb.grid(row=1, column=0, sticky=EW)
        sf.grid_rowconfigure(0, weight=1)
        sf.grid_columnconfigure(0, weight=1)

        # ---- 底部状态 ----
        self.status_var = tk.StringVar(value="💡 点击上方卡片开始转换")
        self.status_lbl = ttk.Label(main, textvariable=self.status_var,
                                    font=(self._font, 9),
                                    bootstyle="secondary", padding=(14, 10))
        self.status_lbl.pack(fill=X, pady=(12, 0))

    def _make_card(self, parent, task):
        card = ttk.Frame(parent, padding=16, bootstyle="light", cursor="hand2")

        # 标题行
        row = ttk.Frame(card)
        row.pack(fill=X)

        icon_lbl = ttk.Label(row, text=task.icon, font=("Segoe UI", 18))
        icon_lbl.pack(side=LEFT)
        self._icon_labels.append(icon_lbl)

        name_lbl = ttk.Label(row, text=task.name,
                             font=(self._font, 12, "bold"),
                             foreground="#1a1a2e")
        name_lbl.pack(side=LEFT, padx=(8, 0))
        self._name_labels.append(name_lbl)

        ttk.Label(row, text="→", font=("Segoe UI", 12),
                  foreground="#1a56db").pack(side=RIGHT)

        # 描述行
        desc_lbl = ttk.Label(card, text=task.desc,
                             font=(self._font, 9),
                             foreground="#6b7280",
                             padding=(0, 6, 0, 0),
                             wraplength=550,
                             anchor=W)
        desc_lbl.pack(fill=X)
        self._desc_labels.append(desc_lbl)
        self._card_frames.append(card)

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

        # 所有设置项使用统一左对齐
        def section_title(parent, text):
            ttk.Label(parent, text=text,
                      font=("Microsoft YaHei UI", 12, "bold")
                      ).pack(anchor=W, pady=(0, 8))

        # ---- 主题选择（按亮/暗分组）----
        section_title(f, "🎨 主题")
        theme_var = tk.StringVar(value=self.config.get("theme", "flatly"))

        # 亮色组
        light_frame = ttk.LabelFrame(f, text="亮色主题")
        light_frame.pack(fill=X, pady=(0, 6))
        for tid, tl in [t for t in THEME_OPTIONS if t[0] in ("flatly", "litera", "pulse")]:
            ttk.Radiobutton(light_frame, text=tl, variable=theme_var,
                            value=tid, bootstyle="info"
                            ).pack(anchor=W, padx=10, pady=1)

        # 暗色组
        dark_frame = ttk.LabelFrame(f, text="暗色主题")
        dark_frame.pack(fill=X, pady=(0, 6))
        for tid, tl in [t for t in THEME_OPTIONS if t[0] in ("darkly", "cyborg", "superhero", "solar")]:
            ttk.Radiobutton(dark_frame, text=tl, variable=theme_var,
                            value=tid, bootstyle="info"
                            ).pack(anchor=W, padx=10, pady=1)

        ttk.Separator(f, bootstyle="secondary").pack(fill=X, pady=12)

        # ---- 字体选择（2 列网格，整齐对齐）----
        section_title(f, "🔤 界面字体")
        font_var = tk.StringVar(value=self._font)
        ff = ttk.Frame(f)
        ff.pack(fill=X)
        for i, (fn, fl) in enumerate(FONT_OPTIONS):
            ttk.Radiobutton(ff, text=fl, variable=font_var,
                            value=fn, bootstyle="info"
                            ).grid(row=i // 2, column=i % 2, sticky=W, padx=(0, 20), pady=2)
        ff.columnconfigure(0, weight=1)
        ff.columnconfigure(1, weight=1)

        ttk.Separator(f, bootstyle="secondary").pack(fill=X, pady=12)

        # ---- 窗口尺寸（纵向紧凑排列）----
        section_title(f, "📐 窗口尺寸")
        size_var = tk.StringVar(value=self.config.get("window_size", "medium"))
        ssf = ttk.Frame(f)
        ssf.pack(fill=X)
        for sid, sl in [("small", "📱 小 (600×480)"),
                        ("medium", "💻 中 (780×620)"),
                        ("large", "🖥️ 大 (960×760)")]:
            ttk.Radiobutton(ssf, text=sl, variable=size_var,
                            value=sid, bootstyle="info"
                            ).pack(anchor=W, pady=2)

        ttk.Separator(f, bootstyle="secondary").pack(fill=X, pady=12)

        # ---- 底部按钮（居中）----
        bf = ttk.Frame(f)
        bf.pack(fill=X, pady=(4, 0))

        def apply():
            nt = theme_var.get()
            ns = size_var.get()
            nf = font_var.get()
            changed_theme = nt != self.config.get("theme")
            changed_size = ns != self.config.get("window_size")
            changed_font = nf != self.config.get("font_family")

            self.config["theme"] = nt
            self.config["window_size"] = ns
            self.config["font_family"] = nf
            if ns in SIZE_PRESETS:
                self._win_w, self._win_h = SIZE_PRESETS[ns]
            save_config(self.config)
            win.destroy()

            rebuild = changed_theme or changed_font
            if changed_theme:
                self.root.style.theme_use(nt)
            if rebuild:
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
        ww, wh = 580, 520
        wx = self.root.winfo_x() + (self._win_w - ww) // 2
        wy = self.root.winfo_y() + (self._win_h - wh) // 2
        win.geometry(f"{ww}x{wh}+{wx}+{wy}")
        win.minsize(480, 380)

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
