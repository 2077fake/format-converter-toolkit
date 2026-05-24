"""
格式转换工具箱 — Windows 11 桌面应用
基于 tkinter + ttkbootstrap 现代主题
双击运行或: python main.py
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import tkinter as tk


# ==================== 转换器定义（可扩展） ====================

class ConverterTask:
    """转换任务定义。添加新格式：在这里加一行即可。"""

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


# 导入现有转换函数
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


# ==================== 应用主窗口 ====================

class ConverterApp:
    def __init__(self):
        self.root = ttk.Window(themename="flatly")
        self.root.title("📦 文档格式互转工具箱")
        self.root.geometry("680x560")
        self.root.minsize(600, 480)
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 680, 560
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill=BOTH, expand=YES)

        # ---- 标题 ----
        header = ttk.Frame(main)
        header.pack(fill=X, pady=(0, 4))

        ttk.Label(header, text="📦 文档格式互转工具箱",
                  font=("Microsoft YaHei UI", 18, "bold")).pack(side=LEFT)

        ttk.Label(header, text="v2.1 · Desktop",
                  font=("Segoe UI", 9),
                  foreground="#999").pack(side=RIGHT, pady=(8, 0))

        ttk.Label(main, text="选择一个转换方向，选取文件即可一键转换",
                  font=("Microsoft YaHei UI", 10),
                  foreground="#666").pack(anchor=W, pady=(0, 16))

        # ---- 可滚动卡片区 ----
        scroll_frame = ttk.Frame(main)
        scroll_frame.pack(fill=BOTH, expand=YES)

        canvas = tk.Canvas(scroll_frame, highlightthickness=0,
                           bg=self.root.style.colors.bg)
        scrollbar = ttk.Scrollbar(scroll_frame, orient=VERTICAL,
                                  command=canvas.yview)
        cards_container = ttk.Frame(canvas)

        cards_container.bind("<Configure>",
                             lambda e: canvas.configure(
                                 scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=cards_container,
                             anchor=NW, tags="container")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _scroll(event):
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", _scroll)

        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            "container", width=e.width))

        # 创建卡片
        for i, task in enumerate(CONVERTERS):
            card = self._make_card(cards_container, task)
            card.grid(row=i, column=0, sticky=EW, pady=5)
            cards_container.columnconfigure(0, weight=1)

        canvas.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

        # ---- 底部状态 ----
        self.status_var = tk.StringVar(value="💡 点击上方卡片开始转换")
        self.status_lbl = ttk.Label(main, textvariable=self.status_var,
                                    font=("Microsoft YaHei UI", 9),
                                    bootstyle="secondary",
                                    padding=(14, 10))
        self.status_lbl.pack(fill=X, pady=(12, 0))

    def _make_card(self, parent, task: ConverterTask) -> ttk.Frame:
        card = ttk.Frame(parent, padding=16, bootstyle="light",
                         cursor="hand2")

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

        # 卡片点击
        for w in [card] + list(card.winfo_children()):
            if isinstance(w, ttk.Frame):
                for c in w.winfo_children():
                    c.bind("<Button-1>", lambda e, t=task: self._convert(t))
            w.bind("<Button-1>", lambda e, t=task: self._convert(t))

        return card

    def _convert(self, task: ConverterTask):
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

    def _done(self, path: str):
        self._status("✅ 转换完成！", "success")
        if messagebox.askyesno("转换成功",
                               f"✅ 文件已保存到:\n{path}\n\n是否打开所在文件夹？"):
            os.startfile(os.path.dirname(path))

    def _fail(self, err: str):
        self._status("❌ 转换失败", "danger")
        messagebox.showerror("转换失败", f"❌ 错误:\n\n{err}")

    def _status(self, text: str, style: str = "secondary"):
        self.status_var.set(text)
        clr = {"info": "#1a56db", "success": "#065f46",
               "danger": "#991b1b", "secondary": "#6b7280"}
        self.status_lbl.configure(foreground=clr.get(style, "#6b7280"))

    def run(self):
        self.root.mainloop()


# ==================== 入口 ====================

def main():
    ConverterApp().run()


if __name__ == "__main__":
    main()
