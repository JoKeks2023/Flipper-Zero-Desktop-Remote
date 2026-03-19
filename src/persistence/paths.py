from __future__ import annotations

import os
import platform
from pathlib import Path


def _slugify_app_name(app_name: str) -> str:
    return app_name.lower().replace(" ", "-")


def get_config_dir(app_name: str) -> Path:
    normalized = _slugify_app_name(app_name)
    system = platform.system().lower()

    if system == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    if system == "linux":
        root = os.getenv("XDG_CONFIG_HOME")
        if root:
            return Path(root) / normalized
        return Path.home() / ".config" / normalized

    return Path.home() / f".{normalized}"


def ensure_app_dirs(app_name: str) -> Path:
    config_dir = get_config_dir(app_name)
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
