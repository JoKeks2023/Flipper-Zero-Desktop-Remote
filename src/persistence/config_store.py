from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persistence.paths import ensure_app_dirs


class ConfigStore:
    def __init__(self, app_name: str) -> None:
        self.app_name = app_name
        self.base_dir = ensure_app_dirs(app_name)
        self.settings_file = self.base_dir / "settings.json"
        self.macros_file = self.base_dir / "macros.json"

    def load_settings(self) -> dict[str, Any]:
        default_settings: dict[str, Any] = {
            "last_port": "",
            "expert_mode": False,
            "theme": "dark",
            "accent": "orange",
            "density": "comfort",
            "start_module": "System",
        }
        return self._load_json(self.settings_file, default_settings)

    def save_settings(self, settings: dict[str, Any]) -> None:
        self._save_json(self.settings_file, settings)

    def load_macros(self) -> dict[str, list[str]]:
        default_macros: dict[str, list[str]] = {
            "Status": ["device_info", "storage list /"],
            "Quick Reboot": ["power reboot"],
        }
        raw = self._load_json(self.macros_file, default_macros)
        normalized: dict[str, list[str]] = {}
        for key, value in raw.items():
            if isinstance(key, str) and isinstance(value, list):
                normalized[key] = [str(line).strip() for line in value if str(line).strip()]
        return normalized or default_macros

    def save_macros(self, macros: dict[str, list[str]]) -> None:
        self._save_json(self.macros_file, macros)

    def _load_json(self, path: Path, fallback: dict) -> dict:
        if not path.exists():
            return fallback.copy()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            return fallback.copy()
        except Exception:
            return fallback.copy()

    def _save_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
