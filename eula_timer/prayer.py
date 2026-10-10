"""Modul Penjadwalan Sholat.
Mengambil data jadwal sholat harian dari API Aladhan (metode Kemenag RI),
didukung caching offline lokal dan perhitungan waktu sholat berikutnya.
"""

from __future__ import annotations

import datetime
import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from .config import CACHE_FILE, ensure_config_dir

PRAYER_NAMES_MAPPING = [
    ("Fajr", "Subuh"),
    ("Sunrise", "Terbit"),
    ("Dhuhr", "Dzuhur"),
    ("Asr", "Ashar"),
    ("Maghrib", "Maghrib"),
    ("Isha", "Isya"),
]

# Sholat wajib yang memicu notifikasi waktu sholat
FARD_PRAYERS = {"Subuh", "Dzuhur", "Ashar", "Maghrib", "Isya"}


def clean_time_str(val: str) -> str:
    """Membersihkan format waktu seperti '04:16 (WIB)' menjadi '04:16'."""
    m = re.search(r"(\d{1,2}:\d{2})", val)
    return m.group(1) if m else val.strip()


def load_cache() -> Dict[str, Any]:
    ensure_config_dir()
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache_data: Dict[str, Any]) -> None:
    ensure_config_dir()
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def fetch_prayer_times_api(city: str, country: str = "Indonesia", method: int = 20) -> Optional[Dict[str, str]]:
    """Mengambil jadwal sholat dari API Aladhan."""
    params = urllib.parse.urlencode({
        "city": city,
        "country": country,
        "method": str(method),
    })
    url = f"https://api.aladhan.com/v1/timingsByCity?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "EulaTimer/1.0 (Arch Linux)"})
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("code") == 200 and "data" in data:
                timings_raw = data["data"]["timings"]
                cleaned: Dict[str, str] = {}
                for api_key, ind_key in PRAYER_NAMES_MAPPING:
                    if api_key in timings_raw:
                        cleaned[ind_key] = clean_time_str(timings_raw[api_key])
                return cleaned
    except Exception:
        return None
    return None


def get_prayer_times(city: str, country: str = "Indonesia", method: int = 20, force_refresh: bool = False) -> Tuple[Dict[str, str], bool]:
    """
    Mengambil jadwal sholat hari ini.
    Mengembalikan tuple: (jadwal_dict, is_online).
    """
    today_str = datetime.date.today().isoformat()
    cache_key = f"{city.strip().lower()}_{today_str}"
    cache = load_cache()

    if not force_refresh and cache_key in cache:
        return cache[cache_key], True

    # Coba ambil via online API
    online_data = fetch_prayer_times_api(city, country, method)
    if online_data:
        cache[cache_key] = online_data
        save_cache(cache)
        return online_data, True

    # Fallback ke cache hari sebelumnya jika offline
    for k, v in reversed(list(cache.items())):
        if k.startswith(city.strip().lower()):
            return v, False

    # Fallback perkiraan Jakarta default jika internet mati & tidak ada cache
    default_timings = {
        "Subuh": "04:16",
        "Terbit": "05:34",
        "Dzuhur": "11:40",
        "Ashar": "14:43",
        "Maghrib": "17:46",
        "Isya": "18:56",
    }
    return default_timings, False


def get_next_prayer(timings: Dict[str, str], now: Optional[datetime.datetime] = None) -> Tuple[str, datetime.datetime, int]:
    """
    Menemukan waktu sholat berikutnya.
    Mengembalikan (nama_sholat, waktu_target, sisa_detik).
    """
    if now is None:
        now = datetime.datetime.now()

    today = now.date()

    for name in ["Subuh", "Dzuhur", "Ashar", "Maghrib", "Isya"]:
        time_str = timings.get(name)
        if not time_str:
            continue
        hour, minute = map(int, time_str.split(":"))
        target_dt = datetime.datetime(today.year, today.month, today.day, hour, minute, 0)
        if target_dt > now:
            diff = int((target_dt - now).total_seconds())
            return name, target_dt, diff

    # Jika semua sholat hari ini sudah lewat, sholat berikutnya adalah Subuh besok
    tomorrow = today + datetime.timedelta(days=1)
    subuh_str = timings.get("Subuh", "04:16")
    hour, minute = map(int, subuh_str.split(":"))
    tomorrow_subuh = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minute, 0)
    diff = int((tomorrow_subuh - now).total_seconds())
    return "Subuh", tomorrow_subuh, diff
