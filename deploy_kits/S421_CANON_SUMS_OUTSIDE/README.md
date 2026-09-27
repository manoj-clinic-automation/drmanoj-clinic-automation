# S421_CANON_SUMS_OUTSIDE — F-596 closed · session 284 · 27-Sep-2026

**A record kit. Nothing to install — the assistant placed it on manojz itself** (`D:\Downloads\_kbtools\canon_sums.py` 8ad03ef4 → 6e52ed09; the old one kept as `canon_sums.py.bak_S421_8ad03ef4`).

**The fault (F-596):** every nightly run of `canon_sums.py --fix` copied `MD5SUMS_ALL.txt` to a `.bak_<stamp>` file *inside* `KB_canon_all`, gave that backup a row, and rewrote the sums file even when nothing had changed. Canon changed itself every night; 41 backups had piled up by S277, and one more (26-Sep) stood at this open.

**Now:** the backup goes to `D:\Downloads\_kbtools\canon_sums_backups\` (outside canon, no row; a backup folder inside canon is refused); `--fix` writes nothing when the sums file already covers canon exactly. `CANON_SUMS.bat` is unchanged — it keeps calling `--fix`; the default backup folder does the rest.

**Proven on a scratch copy of canon:** stale backup's row dropped (739 rows); a second run wrote nothing and took no backup; a new file gained its row with the backup outside; a backup folder inside canon refused (exit 3, nothing created). **Then on the real canon:** 740 → 739 rows, 739/739 OK, no `.bak` in canon. The removed backup is at `D:\dr-manoj-git\_to_delete_S284\` with `WHY_SAFE.txt`.
