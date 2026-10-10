"""Titik Masuk Utama (Main CLI Entrypoint) untuk Eula Timer."""

from __future__ import annotations

import argparse
import sys

from .config import load_config, save_config
from .engine import TimerEngine
from .prayer import get_next_prayer, get_prayer_times
from .ui import EulaTimerUI

__version__ = "1.0.0"


def print_prayer_schedule(city: str) -> None:
    """Mencetak jadwal sholat langsung ke terminal (mode CLI)."""
    timings, is_online = get_prayer_times(city)
    status_str = "Online (Kemenag RI)" if is_online else "Offline / Cache"
    print(f"\n❄️  Jadwal Sholat untuk {city} [{status_str}]")
    print("=" * 40)
    for name, t_str in timings.items():
        print(f"  {name:<10} : {t_str}")
    print("=" * 40)
    next_name, next_dt, diff = get_next_prayer(timings)
    h = diff // 3600
    m = (diff % 3600) // 60
    s = diff % 60
    if h > 0:
        time_left = f"{h} jam {m} menit"
    else:
        time_left = f"{m} menit {s} detik"
    print(f"  Sholat Berikutnya : {next_name} ({next_dt.strftime('%H:%M')}) - {time_left} lagi\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="eula-timer",
        description="Eula Timer: Pengingat Waktu Belajar (Pomodoro) & Jadwal Sholat Kemenag untuk Arch Linux.",
    )
    parser.add_argument(
        "-c", "--city",
        type=str,
        help="Nama kota untuk jadwal sholat (contoh: Jakarta, Bandung, Surabaya)",
    )
    parser.add_argument(
        "-w", "--work",
        type=int,
        help="Durasi waktu belajar dalam menit (default: 25)",
    )
    parser.add_argument(
        "-b", "--break-time",
        dest="break_time",
        type=int,
        help="Durasi waktu istirahat dalam menit (default: 5)",
    )
    parser.add_argument(
        "--no-sound",
        action="store_true",
        help="Matikan suara notifikasi chime",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Matikan desktop notification",
    )
    parser.add_argument(
        "-s", "--schedule",
        action="store_true",
        help="Tampilkan jadwal sholat hari ini lalu keluar (mode ringkas)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    config = load_config()

    if args.city:
        config["city"] = args.city
    if args.work:
        config["work_duration_minutes"] = max(1, args.work)
    if args.break_time:
        config["break_duration_minutes"] = max(1, args.break_time)
    if args.no_sound:
        config["sound_enabled"] = False
    if args.no_notify:
        config["notify_enabled"] = False

    if args.city or args.work or args.break_time or args.no_sound or args.no_notify:
        save_config(config)

    if args.schedule:
        print_prayer_schedule(config.get("city", "Jakarta"))
        sys.exit(0)

    # Jalankan TUI Interaktif
    engine = TimerEngine(config=config)
    ui = EulaTimerUI(engine)
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\nEula Timer ditutup. Selamat beraktivitas!")


if __name__ == "__main__":
    main()
