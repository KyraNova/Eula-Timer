"""Engine Pengatur Timer dan Pengecekan Jadwal Sholat."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set

from .config import load_config, save_config
from .notifier import (
    notify_break_ended,
    notify_prayer_advance,
    notify_prayer_time,
    notify_work_ended,
)
from .prayer import get_next_prayer, get_prayer_times


class TimerMode(Enum):
    WORK = "Belajar / Fokus"
    SHORT_BREAK = "Istirahat Pendek"
    LONG_BREAK = "Istirahat Panjang"


class TimerEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config: Dict[str, Any] = config or load_config()

        self.city: str = self.config.get("city", "Jakarta")
        self.country: str = self.config.get("country", "Indonesia")
        self.method: int = self.config.get("method", 20)

        self.work_duration_minutes: int = int(self.config.get("work_duration_minutes", 25))
        self.break_duration_minutes: int = int(self.config.get("break_duration_minutes", 5))
        self.long_break_duration_minutes: int = int(self.config.get("long_break_duration_minutes", 15))
        self.long_break_interval: int = int(self.config.get("long_break_interval", 4))

        self.sound_enabled: bool = bool(self.config.get("sound_enabled", True))
        self.notify_enabled: bool = bool(self.config.get("notify_enabled", True))
        self.advance_reminder_minutes: int = int(self.config.get("advance_prayer_reminder_minutes", 5))

        self.mode: TimerMode = TimerMode.WORK
        self.is_running: bool = False
        self.remaining_seconds: int = self.work_duration_minutes * 60
        self.completed_pomodoros: int = 0

        # Prayer data
        self.prayer_timings: Dict[str, str] = {}
        self.is_online: bool = False
        self.next_prayer_name: str = "Subuh"
        self.next_prayer_target: Optional[datetime.datetime] = None
        self.next_prayer_diff: int = 0

        self.notified_advance: Set[str] = set()
        self.notified_exact: Set[str] = set()

        self.log_messages: list[str] = []
        self._last_day: datetime.date = datetime.date.today()

        # Inisialisasi awal jadwal sholat
        self.refresh_prayer_times()

    def log(self, msg: str) -> None:
        """Menambahkan pesan status / event."""
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{now_str}] {msg}")
        if len(self.log_messages) > 30:
            self.log_messages.pop(0)

    def refresh_prayer_times(self, force: bool = False) -> None:
        """Mengambil ulang jadwal sholat."""
        try:
            self.prayer_timings, self.is_online = get_prayer_times(
                self.city, self.country, self.method, force_refresh=force
            )
            self._update_next_prayer()
            status = "online (Kemenag)" if self.is_online else "offline/cache"
            self.log(f"Jadwal sholat {self.city} diperbarui ({status}).")
        except Exception as e:
            self.log(f"Gagal memuat jadwal sholat: {e}")

    def _update_next_prayer(self) -> None:
        """Menghitung waktu sholat berikutnya."""
        if not self.prayer_timings:
            return
        now = datetime.datetime.now()
        name, dt, diff = get_next_prayer(self.prayer_timings, now)
        self.next_prayer_name = name
        self.next_prayer_target = dt
        self.next_prayer_diff = diff

    def toggle_pause(self) -> None:
        """Toggle status jalan/pause timer."""
        self.is_running = not self.is_running
        status = "berjalan" if self.is_running else "dijeda (pause)"
        self.log(f"Timer {status}.")

    def reset(self) -> None:
        """Reset waktu ke durasi awal dari mode saat ini."""
        self.is_running = False
        if self.mode == TimerMode.WORK:
            self.remaining_seconds = self.work_duration_minutes * 60
        elif self.mode == TimerMode.SHORT_BREAK:
            self.remaining_seconds = self.break_duration_minutes * 60
        else:
            self.remaining_seconds = self.long_break_duration_minutes * 60
        self.log(f"Timer direset ke durasi awal ({self.remaining_seconds // 60}m).")

    def skip(self) -> None:
        """Melewati sesi saat ini ke sesi berikutnya."""
        if self.mode == TimerMode.WORK:
            self.completed_pomodoros += 1
            if self.completed_pomodoros % self.long_break_interval == 0:
                self.mode = TimerMode.LONG_BREAK
                self.remaining_seconds = self.long_break_duration_minutes * 60
                self.log("Sesi belajar dilewati -> Istirahat Panjang.")
            else:
                self.mode = TimerMode.SHORT_BREAK
                self.remaining_seconds = self.break_duration_minutes * 60
                self.log("Sesi belajar dilewati -> Istirahat Pendek.")
        else:
            self.mode = TimerMode.WORK
            self.remaining_seconds = self.work_duration_minutes * 60
            self.log("Istirahat selesai/dilewati -> Sesi Belajar.")

    def adjust_work_duration(self, delta_minutes: int) -> None:
        """Menambah/mengurangi durasi sesi belajar."""
        new_val = max(1, self.work_duration_minutes + delta_minutes)
        diff = (new_val - self.work_duration_minutes) * 60
        self.work_duration_minutes = new_val
        self.config["work_duration_minutes"] = new_val
        save_config(self.config)
        if self.mode == TimerMode.WORK:
            self.remaining_seconds = max(1, self.remaining_seconds + diff)
        self.log(f"Durasi belajar diatur ke {new_val} menit.")

    def adjust_break_duration(self, delta_minutes: int) -> None:
        """Menambah/mengurangi durasi sesi istirahat pendek."""
        new_val = max(1, self.break_duration_minutes + delta_minutes)
        diff = (new_val - self.break_duration_minutes) * 60
        self.break_duration_minutes = new_val
        self.config["break_duration_minutes"] = new_val
        save_config(self.config)
        if self.mode == TimerMode.SHORT_BREAK:
            self.remaining_seconds = max(1, self.remaining_seconds + diff)
        self.log(f"Durasi istirahat diatur ke {new_val} menit.")

    def toggle_sound(self) -> None:
        """Toggle suara peringatan."""
        self.sound_enabled = not self.sound_enabled
        self.config["sound_enabled"] = self.sound_enabled
        save_config(self.config)
        status = "Aktif" if self.sound_enabled else "Nonaktif"
        self.log(f"Suara alert: {status}.")

    def toggle_notify(self) -> None:
        """Toggle notifikasi desktop."""
        self.notify_enabled = not self.notify_enabled
        self.config["notify_enabled"] = self.notify_enabled
        save_config(self.config)
        status = "Aktif" if self.notify_enabled else "Nonaktif"
        self.log(f"Notifikasi desktop: {status}.")

    def set_city(self, new_city: str) -> None:
        """Mengubah lokasi kota untuk jadwal sholat."""
        new_city = new_city.strip()
        if not new_city:
            return
        self.city = new_city
        self.config["city"] = self.city
        save_config(self.config)
        self.notified_advance.clear()
        self.notified_exact.clear()
        self.refresh_prayer_times(force=True)
        self.log(f"Kota diubah ke: {self.city}.")

    def tick(self) -> None:
        """Dipanggil setiap 1 detik oleh runner/event loop."""
        now = datetime.datetime.now()

        # Deteksi pergantian hari (reset cache harian notifikasi)
        if now.date() != self._last_day:
            self._last_day = now.date()
            self.notified_advance.clear()
            self.notified_exact.clear()
            self.refresh_prayer_times(force=True)

        # 1. Update perhitungan sholat
        self._update_next_prayer()
        today_str = now.date().isoformat()
        advance_key = f"{today_str}:{self.next_prayer_name}:adv"
        exact_key = f"{today_str}:{self.next_prayer_name}:exact"

        # Notifikasi pengingat sebelum sholat (misal 5 menit sebelumnya)
        adv_threshold = self.advance_reminder_minutes * 60
        if 0 < self.next_prayer_diff <= adv_threshold:
            if advance_key not in self.notified_advance:
                self.notified_advance.add(advance_key)
                min_left = max(1, self.next_prayer_diff // 60)
                notify_prayer_advance(
                    prayer_name=self.next_prayer_name,
                    minutes_left=min_left,
                    city=self.city,
                    sound_enabled=self.sound_enabled,
                    notify_enabled=self.notify_enabled,
                )
                self.log(f"Pengingat: Waktu sholat {self.next_prayer_name} dalam {min_left} menit!")

        # Notifikasi waktu sholat tepat tiba
        if self.next_prayer_diff <= 0:
            if exact_key not in self.notified_exact:
                self.notified_exact.add(exact_key)
                notify_prayer_time(
                    prayer_name=self.next_prayer_name,
                    city=self.city,
                    sound_enabled=self.sound_enabled,
                    notify_enabled=self.notify_enabled,
                )
                self.log(f"Waktu sholat {self.next_prayer_name} telah tiba!")

        # 2. Update timer belajar / istirahat
        if self.is_running:
            self.remaining_seconds -= 1
            if self.remaining_seconds <= 0:
                self._handle_timer_completion()

    def _handle_timer_completion(self) -> None:
        """Dipanggil saat countdown mencapai 0."""
        if self.mode == TimerMode.WORK:
            self.completed_pomodoros += 1
            if self.completed_pomodoros % self.long_break_interval == 0:
                self.mode = TimerMode.LONG_BREAK
                self.remaining_seconds = self.long_break_duration_minutes * 60
                duration = self.long_break_duration_minutes
            else:
                self.mode = TimerMode.SHORT_BREAK
                self.remaining_seconds = self.break_duration_minutes * 60
                duration = self.break_duration_minutes

            notify_work_ended(
                break_minutes=duration,
                sound_enabled=self.sound_enabled,
                notify_enabled=self.notify_enabled,
            )
            self.log(f"Sesi belajar selesai! Istirahat {duration} menit dimulai.")
        else:
            # Mode sebelumnya adalah BREAK atau LONG_BREAK
            self.mode = TimerMode.WORK
            self.remaining_seconds = self.work_duration_minutes * 60
            notify_break_ended(
                sound_enabled=self.sound_enabled,
                notify_enabled=self.notify_enabled,
            )
            self.log("Istirahat selesai! Mari kembali belajar.")
