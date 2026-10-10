"""TUI (Terminal User Interface) untuk Eula Timer menggunakan Curses."""

from __future__ import annotations

import curses
import datetime
import time
from typing import Optional

from .engine import TimerEngine, TimerMode

# Glyphs font angka 3 baris
DIGITS_3X3 = {
    "0": ["█▀▀█", "█  █", "█▄▄█"],
    "1": [" ▄█ ", "  █ ", " ▄█▄"],
    "2": ["█▀▀█", " ▄▀ ", "█▄▄█"],
    "3": ["█▀▀█", "  ▀▄", "█▄▄█"],
    "4": ["█  █", "█▀▀█", "   █"],
    "5": ["█▀▀█", "▀▀▄ ", "█▄▄█"],
    "6": ["█▀▀█", "█▀▀▄", "█▄▄█"],
    "7": ["▀▀▀█", "  █ ", "  █ "],
    "8": ["█▀▀█", "█▀▀█", "█▄▄█"],
    "9": ["█▀▀█", "▀▀▀█", "█▄▄█"],
    ":": [" ", "■", "■"],
    " ": ["    ", "    ", "    "],
}


class EulaTimerUI:
    def __init__(self, engine: TimerEngine):
        self.engine = engine
        self.input_mode: bool = False
        self.input_buffer: str = ""
        self.input_prompt: str = ""

    def run(self) -> None:
        """Menjalankan interface curses."""
        curses.wrapper(self._main_loop)

    def _init_colors(self) -> None:
        curses.start_color()
        curses.use_default_colors()

        # Pair ID definitions
        # 1: Cyan / default (Theme Utama Eula / Cryo)
        # 2: White / default (Teks normal)
        # 3: Blue / default (Sub-aksen)
        # 4: Yellow / default (Sholat alert / peringatan)
        # 5: Green / default (Istirahat)
        # 6: Red / default (Fokus / Belajar aktif)
        # 7: Magenta / default (Statistik / Tombol)
        # 8: Black / Cyan (Header banner)
        try:
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_WHITE, -1)
            curses.init_pair(3, curses.COLOR_BLUE, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_GREEN, -1)
            curses.init_pair(6, curses.COLOR_RED, -1)
            curses.init_pair(7, curses.COLOR_MAGENTA, -1)
            curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_CYAN)
        except Exception:
            pass

    def _safe_addstr(self, stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
        max_y, max_x = stdscr.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            available = max_x - x
            if available > 0:
                truncated = text[:available]
                try:
                    stdscr.addstr(y, x, truncated, attr)
                except curses.error:
                    pass

    def _draw_box(self, stdscr: curses.window, y: int, x: int, height: int, width: int, title: str = "", attr: int = 0) -> None:
        max_y, max_x = stdscr.getmaxyx()
        if y + height > max_y or x + width > max_x or height < 2 or width < 2:
            return

        # Garis atas
        top_str = "┌" + "─" * (width - 2) + "┐"
        self._safe_addstr(stdscr, y, x, top_str, attr)
        if title:
            title_text = f" {title} "
            self._safe_addstr(stdscr, y, x + 2, title_text, attr | curses.A_BOLD)

        # Garis sisi
        for r in range(1, height - 1):
            self._safe_addstr(stdscr, y + r, x, "│", attr)
            self._safe_addstr(stdscr, y + r, x + width - 1, "│", attr)

        # Garis bawah
        bot_str = "└" + "─" * (width - 2) + "┘"
        self._safe_addstr(stdscr, y + height - 1, x, bot_str, attr)

    def _draw_progress_bar(self, current: int, total: int, width: int) -> str:
        if total <= 0:
            return "[" + "─" * width + "]"
        ratio = max(0.0, min(1.0, current / total))
        filled = int(ratio * width)
        empty = width - filled
        return "━" * filled + "─" * empty

    def _main_loop(self, stdscr: curses.window) -> None:
        curses.curs_set(0)
        stdscr.timeout(150)  # Polling setiap 150ms untuk responsivitas input
        self._init_colors()

        last_tick_time = time.time()

        while True:
            now = time.time()
            if now - last_tick_time >= 1.0:
                self.engine.tick()
                last_tick_time = now

            self._render(stdscr)

            try:
                ch = stdscr.getch()
            except curses.error:
                ch = -1

            if ch != -1:
                if self.input_mode:
                    if ch in (10, 13):  # Enter
                        val = self.input_buffer.strip()
                        if val:
                            self.engine.set_city(val)
                        self.input_mode = False
                        self.input_buffer = ""
                        curses.curs_set(0)
                    elif ch == 27:  # ESC
                        self.input_mode = False
                        self.input_buffer = ""
                        curses.curs_set(0)
                    elif ch in (curses.KEY_BACKSPACE, 127, 8):
                        self.input_buffer = self.input_buffer[:-1]
                    elif 32 <= ch <= 126:
                        self.input_buffer += chr(ch)
                else:
                    if ch in (ord("q"), ord("Q")):
                        break
                    elif ch == ord(" "):
                        self.engine.toggle_pause()
                    elif ch in (ord("r"), ord("R")):
                        self.engine.reset()
                    elif ch in (ord("s"), ord("S")):
                        self.engine.skip()
                    elif ch in (ord("+"), ord("=")):
                        self.engine.adjust_work_duration(1)
                    elif ch in (ord("-"), ord("_")):
                        self.engine.adjust_work_duration(-1)
                    elif ch in (ord("b"), ord("]")):
                        self.engine.adjust_break_duration(1)
                    elif ch in (ord("B"), ord("[")):
                        self.engine.adjust_break_duration(-1)
                    elif ch in (ord("m"), ord("M")):
                        self.engine.toggle_sound()
                    elif ch in (ord("n"), ord("N")):
                        self.engine.toggle_notify()
                    elif ch in (ord("c"), ord("C")):
                        self.input_mode = True
                        self.input_buffer = ""
                        self.input_prompt = "Masukkan Nama Kota: "
                        curses.curs_set(1)
                    elif ch in (ord("f"), ord("F")):
                        self.engine.refresh_prayer_times(force=True)

    def _render(self, stdscr: curses.window) -> None:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        if max_y < 18 or max_x < 55:
            self._safe_addstr(stdscr, 1, 2, "Perbesar terminal Anda (Min: 55 kolom x 18 baris).", curses.color_pair(4))
            stdscr.refresh()
            return

        c_cyan = curses.color_pair(1)
        c_white = curses.color_pair(2)
        c_blue = curses.color_pair(3)
        c_yellow = curses.color_pair(4)
        c_green = curses.color_pair(5)
        c_red = curses.color_pair(6)
        c_mag = curses.color_pair(7)
        c_hdr = curses.color_pair(8)

        # 1. Header Banner
        header_text = "  ❄️  EULA TIMER • Spindrift Knight Companion  ❄️  "
        self._safe_addstr(stdscr, 0, (max_x - len(header_text)) // 2, header_text, c_hdr | curses.A_BOLD)

        # Sub-status bar
        sound_status = "ON" if self.engine.sound_enabled else "OFF"
        notify_status = "ON" if self.engine.notify_enabled else "OFF"
        clock_str = datetime.datetime.now().strftime("%H:%M:%S")
        status_line = (
            f" Lokasi: {self.engine.city} ({'Online' if self.engine.is_online else 'Offline'}) | "
            f"Suara: {sound_status} [m] | Notif: {notify_status} [n] | Jam: {clock_str} "
        )
        self._safe_addstr(stdscr, 1, 2, status_line, c_cyan)

        # Layout Split:
        # Kiri: Timer & Pomodoro Box
        # Kanan: Jadwal Sholat Box
        right_panel_width = 32
        left_panel_width = max_x - right_panel_width - 4
        panel_y = 3
        panel_height = max(13, max_y - 8)

        # Box Kiri: Timer Belajar
        self._draw_box(stdscr, panel_y, 2, panel_height, left_panel_width, "Sesi Pomodoro", c_cyan)

        # Mode Indicator
        mode_str = f" [ {self.engine.mode.value.upper()} ] "
        mode_attr = (
            (c_red | curses.A_BOLD)
            if self.engine.mode == TimerMode.WORK
            else (c_green | curses.A_BOLD)
        )
        self._safe_addstr(stdscr, panel_y + 2, 5, mode_str, mode_attr)

        # State jalan / pause
        run_status = "▶ BERJALAN" if self.engine.is_running else "⏸ DIJEDA (PAUSE)"
        run_attr = (c_green | curses.A_BOLD) if self.engine.is_running else (c_yellow | curses.A_BOLD)
        self._safe_addstr(stdscr, panel_y + 2, 5 + len(mode_str) + 2, run_status, run_attr)

        # Waktu format MM:SS
        mins = self.engine.remaining_seconds // 60
        secs = self.engine.remaining_seconds % 60
        time_formatted = f"{mins:02d}:{secs:02d}"

        # Big ASCII clock jika muat
        clock_y = panel_y + 4
        if left_panel_width >= 36:
            lines = ["", "", ""]
            for ch in time_formatted:
                glyph = DIGITS_3X3.get(ch, ["    ", "    ", "    "])
                for row in range(3):
                    lines[row] += glyph[row] + "  "

            color_clock = c_cyan | curses.A_BOLD if self.engine.is_running else c_white
            for i, line in enumerate(lines):
                self._safe_addstr(stdscr, clock_y + i, 6, line, color_clock)
            bar_y = clock_y + 4
        else:
            self._safe_addstr(stdscr, clock_y, 6, f"WAKTU: {time_formatted}", c_cyan | curses.A_BOLD)
            bar_y = clock_y + 2

        # Total duration target for progress bar
        if self.engine.mode == TimerMode.WORK:
            total_dur = self.engine.work_duration_minutes * 60
        elif self.engine.mode == TimerMode.SHORT_BREAK:
            total_dur = self.engine.break_duration_minutes * 60
        else:
            total_dur = self.engine.long_break_duration_minutes * 60

        elapsed = max(0, total_dur - self.engine.remaining_seconds)
        bar_len = max(10, min(36, left_panel_width - 12))
        pct = int((elapsed / max(1, total_dur)) * 100)
        p_bar = self._draw_progress_bar(elapsed, total_dur, bar_len)
        self._safe_addstr(stdscr, bar_y, 6, f"Progress: [{p_bar}] {pct}%", c_blue)

        # Info sesi pomodoro
        stats_y = bar_y + 2
        pomo_icons = "⚔ " * self.engine.completed_pomodoros
        self._safe_addstr(
            stdscr,
            stats_y,
            6,
            f"Selesai: {self.engine.completed_pomodoros} sesi ({pomo_icons})",
            c_mag,
        )
        self._safe_addstr(
            stdscr,
            stats_y + 1,
            6,
            f"Pengaturan: Belajar {self.engine.work_duration_minutes}m | Istirahat {self.engine.break_duration_minutes}m",
            c_white,
        )

        # Box Kanan: Jadwal Sholat
        rx = 2 + left_panel_width + 1
        self._draw_box(stdscr, panel_y, rx, panel_height, right_panel_width, "Jadwal Sholat", c_blue)

        fard_list = [
            ("Subuh", "04:16"),
            ("Terbit", "05:34"),
            ("Dzuhur", "11:40"),
            ("Ashar", "14:43"),
            ("Maghrib", "17:46"),
            ("Isya", "18:56"),
        ]

        py_row = panel_y + 2
        for s_name, _ in fard_list:
            t_val = self.engine.prayer_timings.get(s_name, "--:--")
            is_next = s_name == self.engine.next_prayer_name

            if is_next:
                row_attr = c_yellow | curses.A_BOLD
                marker = "◄ NEXT"
            else:
                row_attr = c_white
                marker = "      "

            self._safe_addstr(stdscr, py_row, rx + 3, f"{s_name:<8} : {t_val}  {marker}", row_attr)
            py_row += 1

        # Countdown sholat berikutnya
        py_row += 1
        self._safe_addstr(stdscr, py_row, rx + 3, "─" * (right_panel_width - 6), c_blue)
        py_row += 1

        if self.engine.next_prayer_diff > 0:
            p_hours = self.engine.next_prayer_diff // 3600
            p_mins = (self.engine.next_prayer_diff % 3600) // 60
            p_secs = self.engine.next_prayer_diff % 60
            if p_hours > 0:
                cd_text = f"{p_hours}j {p_mins}m lagi"
            else:
                cd_text = f"{p_mins}m {p_secs}s lagi"
            self._safe_addstr(stdscr, py_row, rx + 3, f"Menuju {self.engine.next_prayer_name}:", c_yellow)
            py_row += 1
            self._safe_addstr(stdscr, py_row, rx + 3, f">> {cd_text}", c_yellow | curses.A_BOLD)
        else:
            self._safe_addstr(stdscr, py_row, rx + 3, f"Waktu {self.engine.next_prayer_name} Tiba!", c_yellow | curses.A_BOLD)

        # Status log di bawah panel
        log_y = panel_y + panel_height
        if log_y < max_y - 2:
            latest_msg = self.engine.log_messages[-1] if self.engine.log_messages else "Eula Timer siap."
            self._safe_addstr(stdscr, log_y, 2, f"Info: {latest_msg}", c_white)

        # Input Prompt Dialog jika dalam input mode
        if self.input_mode:
            prompt_y = max_y - 2
            self._safe_addstr(
                stdscr,
                prompt_y,
                2,
                f"{self.input_prompt}{self.input_buffer}█ (Enter untuk simpan, ESC batalkan)",
                c_yellow | curses.A_BOLD,
            )
        else:
            # Petunjuk Tombol (Hotkeys)
            help_y = max_y - 2
            help_text = (
                "[Spasi] Mulai/Jeda  [r] Reset  [s] Skip  [+/-] Durasi Belajar  "
                "[b/B] Istirahat  [c] Ganti Kota  [f] Refresh  [q] Keluar"
            )
            self._safe_addstr(stdscr, help_y, 2, help_text, c_mag)

        stdscr.refresh()
