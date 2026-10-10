"""Modul Notifikasi Desktop dan Audio Alert.
Mengirimkan notifikasi via notify-send dan memutar suara chime menggunakan paplay/mpv.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

SOUND_MAP = {
    "break_start": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
    "break_end": "/usr/share/sounds/freedesktop/stereo/complete.oga",
    "prayer": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
    "prayer_advance": "/usr/share/sounds/freedesktop/stereo/dialog-information.oga",
    "bell": "/usr/share/sounds/freedesktop/stereo/bell.oga",
}


def _get_audio_player() -> Optional[str]:
    """Mendeteksi pemutar audio yang tersedia di sistem Arch."""
    if shutil.which("paplay"):
        return "paplay"
    if shutil.which("mpv"):
        return "mpv"
    return None


def play_sound(sound_type: str = "bell", enabled: bool = True) -> None:
    """Memutar suara peringatan di latar belakang tanpa memblokir thread utama."""
    if not enabled:
        return

    sound_path = SOUND_MAP.get(sound_type, SOUND_MAP["bell"])
    if not os.path.exists(sound_path):
        # Fallback ke bell jika file tidak ditemukan
        sound_path = "/usr/share/sounds/freedesktop/stereo/bell.oga"
        if not os.path.exists(sound_path):
            return

    player = _get_audio_player()
    if not player:
        return

    try:
        if player == "paplay":
            subprocess.Popen(
                ["paplay", sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif player == "mpv":
            subprocess.Popen(
                ["mpv", "--no-video", "--really-quiet", sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


def send_notification(
    title: str,
    message: str,
    urgency: str = "normal",
    icon: str = "appointment-soon",
    enabled: bool = True,
) -> None:
    """Mengirim desktop notification menggunakan notify-send."""
    if not enabled:
        return

    if not shutil.which("notify-send"):
        return

    try:
        cmd = [
            "notify-send",
            "-a",
            "Eula Timer",
            "-u",
            urgency,
            "-i",
            icon,
            title,
            message,
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def notify_work_ended(break_minutes: int, sound_enabled: bool = True, notify_enabled: bool = True) -> None:
    """Dipanggil ketika sesi belajar/kerja selesai dan saatnya istirahat."""
    send_notification(
        title="Waktunya Istirahat!",
        message=f"Sesi belajar selesai! Istirahat sejenak {break_minutes} menit, regangkan badan dan jangan berlebihan.",
        urgency="critical",
        icon="alarm",
        enabled=notify_enabled,
    )
    play_sound("break_start", enabled=sound_enabled)


def notify_break_ended(sound_enabled: bool = True, notify_enabled: bool = True) -> None:
    """Dipanggil ketika durasi istirahat selesai dan saatnya belajar kembali."""
    send_notification(
        title="Istirahat Selesai!",
        message="Waktu istirahat sudah usai. Mari mulai sesi belajar kembali dengan fokus!",
        urgency="normal",
        icon="appointment-soon",
        enabled=notify_enabled,
    )
    play_sound("break_end", enabled=sound_enabled)


def notify_prayer_time(prayer_name: str, city: str, sound_enabled: bool = True, notify_enabled: bool = True) -> None:
    """Dipanggil tepat saat waktu sholat wajib tiba."""
    send_notification(
        title=f"Waktu Sholat {prayer_name} Telah Tiba!",
        message=f"Sudah masuk waktu sholat {prayer_name} untuk daerah {city}. Luangkan waktu untuk sholat terlebih dahulu.",
        urgency="critical",
        icon="clock",
        enabled=notify_enabled,
    )
    play_sound("prayer", enabled=sound_enabled)


def notify_prayer_advance(
    prayer_name: str,
    minutes_left: int,
    city: str,
    sound_enabled: bool = True,
    notify_enabled: bool = True,
) -> None:
    """Dipanggil beberapa menit sebelum waktu sholat tiba (persiapan)."""
    send_notification(
        title=f"Peringatan: {prayer_name} Dalam {minutes_left} Menit",
        message=f"Waktu sholat {prayer_name} ({city}) akan segera tiba dalam {minutes_left} menit.",
        urgency="normal",
        icon="clock",
        enabled=notify_enabled,
    )
    play_sound("prayer_advance", enabled=sound_enabled)
