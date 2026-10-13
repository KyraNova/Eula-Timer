# ❄️ Eula Timer

> *"Vengeance will be mine! ...Tapi jangan lupa istirahat dan sholat tepat waktu."*  
> — Eula Lawrence

**Eula Timer** adalah aplikasi pengatur waktu belajar (Pomodoro) dan pengingat jadwal sholat fardhu (Kemenag RI) berbasis terminal (TUI) interaktif yang dirancang khusus untuk Linux (Arch Linux).

---

## 🌟 Fitur Utama

- **TUI Dashboard Interaktif (Curses)**: Tampilan visual bertema *Cryo / Spindrift Knight* dengan font angka digital besar, indikator progress bar, dan status sesi.
- **Jadwal Sholat Fardhu Akurat**: Menggunakan kalkulasi resmi Kementerian Agama RI (Kemenag) via Aladhan API dengan sistem cache offline lokal (`~/.config/eula-timer/prayer_cache.json`).
- **Pengingat Sholat Otomatis**:
  - Peringatan awal 5 menit sebelum waktu sholat tiba (persiapan wudhu).
  - Peringatan tepat waktu saat adzan / jadwal masuk.
- **Siklus Pomodoro Pintar**: Sesi belajar fokus, istirahat pendek (5 menit), dan istirahat panjang (15 menit) setiap 4 sesi.
- **Pengingat Jam Tidur Disiplin (Bedtime Reminder)**:
  - Jam tidur standar jam 10 malam (`22:00`) yang dapat dikustomisasi.
  - Notifikasi berkala saat mendekati jam tidur: 30 menit, 20 menit, 10 menit, dan 5 menit sebelum waktu tidur.
  - Peringatan tegas saat tepat jam tidur dan teguran jika masih begadang lewat jam tidur.
- **Pengingat Jadwal Selesai Belajar (Study End Reminder)**:
  - Target jam selesai belajar standar jam 5 sore (`17:00`) yang dapat dikustomisasi.
  - Peringatan berkala menjelang sesi belajar berakhir: 30 menit, 15 menit, dan 5 menit sebelum waktu selesai.
  - Notifikasi dan alarm tepat pukul 17:00 untuk menyudahi belajar dan mulai beristirahat.
  - Peringatan lembur jika pengguna masih memaksa belajar melewati batas waktu yang ditentukan.
- **Desktop & Audio Alerts**:
  - Mengirim notifikasi visual sistem melalui `notify-send`.
  - Membunyikan nada chime ramah telinga melalui `paplay` (PulseAudio/PipeWire) atau `mpv`.
- **Dukungan CLI Fleksibel**: Periksa jadwal sholat secara langsung dengan argumen CLI tanpa membuka TUI.

---

## ⌨️ Kontrol / Hotkeys di TUI

| Tombol | Aksi |
| :--- | :--- |
| `[Spasi]` | Mulai (Start) / Jeda (Pause) timer |
| `r` / `R` | Reset timer ke durasi awal mode saat ini |
| `s` / `S` | Lewati (Skip) sesi saat ini ke sesi berikutnya |
| `+` / `=` | Tambah 1 menit durasi belajar |
| `-` | Kurang 1 menit durasi belajar |
| `b` / `]` | Tambah 1 menit durasi istirahat |
| `B` / `[` | Kurang 1 menit durasi istirahat |
| `c` / `C` | Ganti kota / lokasi jadwal sholat (contoh: Jakarta, Bandung, Surabaya) |
| `t` | Atur jam tidur (format `HH:MM`, ketik `off` untuk mematikan) |
| `T` | Toggle aktif / nonaktif pengingat jam tidur |
| `e` | Atur jam selesai belajar (format `HH:MM`, ketik `off` untuk mematikan) |
| `E` | Toggle aktif / nonaktif pengingat jadwal selesai belajar |
| `f` / `F` | Muat ulang paksa (force refresh) jadwal sholat dari internet |
| `m` / `M` | Matikan / nyalakan suara alert (Mute toggle) |
| `n` / `N` | Matikan / nyalakan notifikasi desktop (Notify toggle) |
| `q` / `Q` | Keluar dari aplikasi |

---

## 🚀 Cara Menjalankan

Aplikasi sudah terpasang langsung di `~/.local/bin/eula-timer`, sehingga bisa langsung dipanggil dari terminal mana saja:

```bash
# Menjalankan Dashboard TUI Interaktif
eula-timer

# Menjalankan dengan kota tertentu
eula-timer -c Bandung

# Mengatur durasi belajar 30 menit dan istirahat 10 menit
eula-timer -w 30 -b 10
# Melihat jadwal sholat & jam tidur hari ini secara ringkas (CLI mode)
eula-timer -s

# Mengatur target jam tidur ke jam 22:00 atau jam lainnya
eula-timer -t 22:00

# Mengatur jadwal selesai belajar ke jam 17:00 atau jam lainnya
eula-timer -e 17:00

# Menonaktifkan pengingat selesai belajar
eula-timer --no-study-end

# Menonaktifkan pengingat jam tidur
eula-timer --no-bedtime
```

---

## ⚙️ Lokasi Konfigurasi & Cache

- **Konfigurasi**: `~/.config/eula-timer/config.json`
- **Cache Jadwal Sholat**: `~/.config/eula-timer/prayer_cache.json`
