"""Konfigurasi Eula Timer.
Menangani file konfigurasi di ~/.config/eula-timer/config.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".config" / "eula-timer"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_FILE = CONFIG_DIR / "prayer_cache.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "city": "Jakarta",
    "country": "Indonesia",
    "method": 20,  # 20: Kemenag RI (Kementerian Agama RI)
    "work_duration_minutes": 25,
    "break_duration_minutes": 5,
    "long_break_duration_minutes": 15,
    "long_break_interval": 4,  # Setiap 4 sesi belajar, beri long break
    "sound_enabled": True,
    "notify_enabled": True,
    "advance_prayer_reminder_minutes": 5,  # Pengingat 5 menit sebelum waktu sholat
}


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> Dict[str, Any]:
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            # Gabungkan dengan nilai default jika ada kunci baru
            merged = dict(DEFAULT_CONFIG)
            merged.update(user_config)
            return merged
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(config: Dict[str, Any]) -> None:
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Gagal menyimpan konfigurasi: {e}")
