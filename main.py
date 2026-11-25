"""双击运行或 `python main.py` 打开桌面应用；等价于 `python -m format_converter`。"""

import sys

from format_converter.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
