# S648_PROCROOM_OPEN_DOOR — the count door for Shavez's list, and Baaki din back to 01-10-2026

**Why.** The parent's ask on the board (message `parent_S349_1`, 25-Oct-2026 07:5x IST), taken by the S346 close as the first work of
session 352 (START_HERE_SESSION_352 B1): Shavez's *Aaj ka kaam* (the parent's) is to carry a line for *Kal ke procedures* — it needs a
read-only count to fetch — and *Baaki din* is to cover all of October for his backfill, not one week. Board `_numbers` v677 → v678
(kit S648). Built in the Scan App chat, session 352.

**What changes.**
- **New, read only:** `GET https://followup.dr-manoj.in/scanapp/procroom/morning/api/open` (the app's own path
  `/procroom/morning/api/open`). The owner always; a manager (Shavez) only while *Kal ke procedures* is switched on for the staff.
  Answers `{"ok": true, "open": <days still to fill>, "slips": <slips>, "text": "Kal ke procedures: <n> din baaki (<m> parchi)",
  "from": "2026-10-01"}`; when nothing waits `open` is 0 and the text reads *Kal ke procedures: koi din baaki nahi*. A signed-out call
  (401), a refused login (403), the screen switched off for the staff (200) or the slip book unreadable (503) answer `{"ok": false,
  "why": …}` with **no `open` field** — never read as "nothing waits". GET only; `Cache-Control: no-store`; it writes nothing.
- *Kal ke procedures* (`https://followup.dr-manoj.in/scanapp/procroom/morning`): **Baaki din** lists every day from the floor to
  yesterday with slips still to fill (oldest first), not the last 7 days. Its links open those days even past the 60-day window, back
  to the floor.
- His Procedure room page: the *Worth a look* line counts the same slips — "<n> procedure slips since 01-10-2026 not filled on
  Shavez's morning screen yet (<d> days)".
- **One computation** (`open_days`) for the door, Baaki din and his line: the same rule as before (X-ray/Proc slips, state ok, at least
  one procedure; Docterz's *nahi hua* left out once his report for the day has come; a slip already saved left out), one read of the
  slip book for the whole span. The walk proves it equal, day by day, to the old per-day rule.
- **The floor** is the setting `proc.morning_from` in the scan app's settings (none set = 01-10-2026). No data step: the install writes
  no setting.
- `not_done_refs` is left whole on purpose: bounding it by the floor would let a slip saved before the floor, that Docterz later did
  not have, be counted as used.

**Files and pins (FROM → TO).** `/root/assetapp/procroom.py` `7b936d6f` (S643's) → `f6578535`, the kit's whole file (12 counted
edits, `build_s648.py` in the session's working papers). No other file; no data step; the parent's `finance.db` read only, as before.
Read only, pinned: as S643 (`sorting_desk.py ca9fda74`, `asset_register.py 068440f7`, `clinic_papers.py 89a3cd0a`, `claude_reader.py
10118909`, `claude_reread.py ed7023d2`, `asset_machine.py 7dbd5e0c`, `stationery.py b6ce217a`, `batteries.py bb082b4c`, `xray_costs.py
5823bae2`).

**Kit.** `make_s648.py` · `procroom.py` · `walk_s648_app.py` (every S643 and S637 check, plus O1–O12, made-up slips only; `--expect-red`
on S643's file: only A0 and O1–O12 red) · `install_s648.sh` (after the restart it calls the new door signed out and needs the
signed-out answer with no count) · `rehearse_s648.sh` (R1–R7) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S648_PROCROOM_OPEN_DOOR/install_s648.sh`

**UNDO (one line):** `\cp -p /root/assetapp/procroom.py.bak_S648_7b936d6f /root/assetapp/procroom.py && systemctl restart assetapp`
