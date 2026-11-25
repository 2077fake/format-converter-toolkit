"""用户配置：保存在用户目录，而不是源码目录。"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_CONFIG: dict = {
    "theme": "light",
    "open_folder_after": False,
}
_MAX_BYTES = 64 * 1024


def config_path() -> Path:
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return Path(base) / "format-converter-toolkit" / "config.json"


def load_config(path: Path | None = None) -> dict:
    path = path or config_path()
    cfg = dict(DEFAULT_CONFIG)
    try:
        if path.exists() and path.stat().st_size <= _MAX_BYTES:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update({k: data[k] for k in DEFAULT_CONFIG if k in data})
    except (OSError, ValueError):
        pass
    if cfg["theme"] not in ("light", "dark"):
        cfg["theme"] = "light"
    return cfg


def save_config(cfg: dict, path: Path | None = None) -> None:
    path = path or config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
