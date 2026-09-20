# HANDOFF RUNBOOK — v196 — S276 CLOSE (the parent), 20-Sep-2026

*Supersedes v195 (S273 close, the parent). The Sanjeevni thread's own record is v194 (S274 close).*

## §0 · WHAT HAPPENED
The X-ray test folder was empty, so the carried backlog was taken. Four kits, all live from the owner's lines the same day: `S347_SPINE_BACKUP` (the pharmacy spine into both nightly stores — it had been in none), `S348_DAILY_REPORT_ATTENDANCE` (the Daily Clinic Report's attendance line, dead since 02-Aug because it read a machine's mail that stopped on 01-Aug; repointed to the clinic server's own day-summary mail, placed in the owner's browser), `S349_WATCHER_FRESHNESS` (the health card's watcher row goes red in clinic hours when the medical PC falls silent — D554 delivered; `/finance/freshness` serves the collector's table, F-540 closed) and `S350_FRESHNESS_CLOCK` (the banner's clock, found live two minutes after S349). Two unattended reports that existed only in project knowledge were rescued. `finance_app.py` was read whole before it was patched. Decisions D578–D581; findings F-585–F-591. No SOP change for staff.

## §1 · MENTAL MODELS
- **A folder is not backed up until a kit names it to both nightly stores** (F-585). The code bundle's `root/finance` entries are non-recursive by design.
- **A pin row exists to the generator only in the two-column shape, in the newest section** (F-586).
- **A daily surface that prints its fallback line for a week is a fault to read at its source, not a backlog line** (F-588).
- **A parser is tested on the bytes its runtime hands it** (F-589) — the Gmail API's rendering is not `getPlainBody()`.
- **A walk that supplies the very input a defect could live in proves nothing about it** (F-590) — one check on the real clock, path or row, always.
- **Read whole before the fifth patch** — the drift rule, honoured this session with a sub-agent's whole read (`WHOLE_READ_finance_app_7866b1ee.md`).

## §2 · THE LIVE BACKLOG
See `S276_BUILD_BRIEF.md §2` and `OWNER_TODO_LIVE.md`. Still first when the staff files arrive: the live X-ray filing (`S273_BUILD_BRIEF §2`). Then: `gas_export.py`'s `REPO_COPY` onto the current photograph (F-591) · the unattended lane's proposal (c) and the trigger's prompt (v8 → v10), both his one line · the phonebook from the two exports · the last four units into the bundle (D555, his ruling) · fault injection for `backup`/`outbox` (D525) · Bhati's petty-book layout (offered) · Docterz uploads stop on his word · bank-SMS PARKED.

## §3 · INSTALL DISCIPLINE — added this session
- An Apps Script placement is done **inside the page** (anchored replacements run in the editor; the live text and its secrets never leave the browser); the masked hash before must equal the repository photograph and after must equal the kit's masked file; a read-only function is run in the editor as the live proof (D577 widened).
- A kit that changes a **cron-only file** restarts nothing and proves itself with the job's own read-only mode (`preflight`, a `gather()` with no write).
- Every walk keeps one check on the real thing it would otherwise fake (F-590).
- The record kit (S348) is a legitimate shape: no installer, the photograph plus the edit scripts as run.

## §4 · THE BOUNDARY
The VPS needs the owner (one line each; four today). Apps Script needs only his sign-in (drmka.ortho, `/u/1/`). manojz: `device_bash` works; the file tools read and write all three roots. The Sanjeevni chat (S275 reserved) writes the same canon folder: list `KB_canon_all\` before writing (F-534). `finance_app.py` moved `7866b1ee → 29819879` today — a Sanjeevni kit touching it takes `29819879` as its FROM. Next free after this close: **D582 · F-592 · A-D25 · kit S351 · Session 278** (mirror; `board/_numbers` is the source).
