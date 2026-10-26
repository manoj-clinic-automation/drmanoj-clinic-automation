# S658_UNREAD_NIGHTLY — each person's UNREAD "Aaj ka kaam" lines, counted every night (F-1024's carry)

**A RECORD, NOT AN INSTALLER. Nothing here needs to be run.** The two files were placed on manojz by the assistant at
S357 (26-Oct-2026, ~06:5x IST) through the file tools and read back by hash; this folder keeps their bytes in git.

| file | where it lives | md5 |
|---|---|---|
| `unread_lists.py` | `D:\Downloads\_kbtools\unread_lists.py` (NEW) | `d9252aaad8f21076666d7d943d3040ed` |
| `NIGHTLY.bat` | `D:\Downloads\_kbtools\NIGHTLY.bat` (was `76335f66`, kept beside it as `NIGHTLY.bat.bak_S357_76335f66`) | `b166080d114d26181edb373d93a428fe` |

**What it does.** Step 3b of the 03:10 nightly (after the canon gate; it never changes the run's exit code). From
`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz` it takes the server's own `aaj_kaam.py`, `aaj_seed.py` and
`aaj_duties.json` (each checked against the bundle's `MANIFEST.md5`), unzips `finance_nightly.db.gz` into the scratch
`D:\Downloads\_r658\`, takes the repository's `claude_code_briefs\DUTY_MAP.json`, and builds every staff list exactly as
the server does (`aaj_kaam.Reader` → `person_list`, read-only, `mode=ro`). It writes
`D:\Downloads\_kbtools\UNREAD_LISTS_LATEST.txt`: per person lines / UNREAD, and for each unread line its duty id and
the reason. **OK** = 0 unread on lists switched on · **WARN** = an unread line, or a source older than 30 h · **FAIL** =
could not count (a source missing, a server file disagreeing with its MANIFEST row, the lists not built).
The scratch holds a database copy (patients): it never leaves the PC and is removed every run, pass or fail.
The report names duty ids and counts only.

**The walk (S357, in manojz's VM, python3, on the 26-Oct bundle and database copy):**
- W1 the real sources → OK; amir off 0 · bhati 5 · darpan 0 · reception 14 · shavez 10 · sukhveer 1 lines; UNREAD 0; scratch removed.
- W2 CONTROL — a copy of DUTY_MAP with `reception.order_arrival`'s SQL changed (F-1024's own shape) → WARN, reception
  UNREAD 1, naming `reception.order_arrival`: *the floor's own piece of this duty's SQL no longer fits the duty*.
- W3 the database missing → FAIL. W4 the database 72 h old → WARN (STALE). W5 a bundle whose `aaj_seed.py` disagrees
  with its MANIFEST row → FAIL. A scratch left by a cut run is removed first. Every run left no scratch behind.
- **Not yet proven: the first run under Windows python (3.14) — tonight's 03:10.** The next open reads its report.
