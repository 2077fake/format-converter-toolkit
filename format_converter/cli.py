"""命令行入口。

    python -m format_converter                       # 打开桌面应用
    python -m format_converter convert a.md --to docx
    python -m format_converter convert docs/ --from md --to pdf   # 批量
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._version import __version__
from .core.registry import CONVERTERS, find_task, run_conversion

_FORMATS = sorted({t.src_ext.lstrip(".") for t in CONVERTERS} | {t.tgt_ext.lstrip(".") for t in CONVERTERS})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="format_converter", description="Markdown / Word / PDF 互转")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("gui", help="打开桌面应用（默认）")
    c = sub.add_parser("convert", help="命令行转换单个文件或整个目录")
    c.add_argument("input", help="源文件，或目录（需配合 --from）")
    c.add_argument("--to", required=True, choices=_FORMATS, dest="target", help="目标格式")
    c.add_argument("--from", choices=_FORMATS, dest="source", help="源格式（输入为目录时必填）")
    c.add_argument("-o", "--output", help="输出路径（仅单文件）")
    return p


def _convert_one(src: Path, source_ext: str, target_ext: str, out: str | None) -> bool:
    task = find_task(source_ext, target_ext)
    if task is None:
        print(f"不支持的转换: {source_ext} → {target_ext}", file=sys.stderr)
        return False
    dst = out or str(src.with_suffix(target_ext))
    result = run_conversion(task, str(src), dst)
    if result.success:
        print(f"OK   {src.name} → {result.output_path}")
    else:
        print(f"FAIL {src.name}: {result.error}", file=sys.stderr)
    return result.success


def _run_convert(args) -> int:
    target_ext = "." + args.target
    path = Path(args.input)
    if path.is_dir():
        if not args.source:
            print("输入是目录时必须指定 --from", file=sys.stderr)
            return 2
        source_ext = "." + args.source
        files = sorted(path.glob(f"*{source_ext}"))
        if not files:
            print(f"目录中未找到 {source_ext} 文件: {path}", file=sys.stderr)
            return 1
        ok = sum(_convert_one(f, source_ext, target_ext, None) for f in files)
        print(f"完成: {ok}/{len(files)}")
        return 0 if ok == len(files) else 1
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1
    return 0 if _convert_one(path, path.suffix.lower(), target_ext, args.output) else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "convert":
        return _run_convert(args)
    from .ui.app import run_gui
    return run_gui()
