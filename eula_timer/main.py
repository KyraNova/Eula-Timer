"""Titik Masuk Utama (Main CLI Entrypoint) untuk Eula Timer."""

from __future__ import annotations

import argparse
import sys

from .config import load_config, save_config
from .engine import TimerEngine
from .prayer import get_next_prayer, get_prayer_times
from .ui import EulaTimerUI

__version__ = "1.0.0"


def print_prayer_schedule(
    city: str,
    study_end: str = "17:00",
    study_end_enabled: bool = True,
    bedtime: str = "22:00",
    bedtime_enabled: bool = True,
) -> None:
    """Mencetak jadwal sholat langsung ke terminal (mode CLI)."""
    timings, is_online = get_prayer_times(city)
    status_str = "Online (Kemenag RI)" if is_online else "Offline / Cache"
    print(f"\n❄️  Jadwal Sholat & Waktu Tidur untuk {city} [{status_str}]")
    print("=" * 45)
    for name, t_str in timings.items():
        print(f"  {name:<12} : {t_str}")
    print("=" * 45)
    next_name, next_dt, diff = get_next_prayer(timings)
    h = diff // 3600
    m = (diff % 3600) // 60
    s = diff % 60
    if h > 0:
        time_left = f"{h} jam {m} menit"
    else:
        time_left = f"{m} menit {s} detik"
    print(f"  Sholat Berikutnya : {next_name} ({next_dt.strftime('%H:%M')}) - {time_left} lagi")
    if study_end_enabled:
        print(f"  Target Selesai    : {study_end} (Pengingat Aktif)")
    else:
        print(f"  Target Selesai    : Nonaktif")
    if bedtime_enabled:
        print(f"  Target Jam Tidur  : {bedtime} (Pengingat Aktif)\n")
    else:
        print(f"  Target Jam Tidur  : Nonaktif\n")

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
        "-e", "--study-end",
        dest="study_end",
        type=str,
        help="Waktu jadwal selesai belajar (format HH:MM, default: 17:00)",
    )
    parser.add_argument(
        "--no-study-end",
        action="store_true",
        help="Matikan pengingat jadwal selesai belajar",
    )
    parser.add_argument(
        "-t", "--bedtime",
        type=str,
        help="Waktu jam tidur (format HH:MM, default: 22:00)",
    )
    parser.add_argument(
        "--no-bedtime",
        action="store_true",
        help="Matikan pengingat jam tidur",
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
    if args.study_end:
        config["study_end_time"] = args.study_end
        config["study_end_enabled"] = True
    if args.no_study_end:
        config["study_end_enabled"] = False
    if args.bedtime:
        config["bedtime"] = args.bedtime
        config["bedtime_enabled"] = True
    if args.no_bedtime:
        config["bedtime_enabled"] = False

    if (
        args.city
        or args.work
        or args.break_time
        or args.no_sound
        or args.no_notify
        or args.study_end
        or args.no_study_end
        or args.bedtime
        or args.no_bedtime
    ):
        save_config(config)

    if args.schedule:
        print_prayer_schedule(
            config.get("city", "Jakarta"),
            study_end=config.get("study_end_time", "17:00"),
            study_end_enabled=config.get("study_end_enabled", True),
            bedtime=config.get("bedtime", "22:00"),
            bedtime_enabled=config.get("bedtime_enabled", True),
        )
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
