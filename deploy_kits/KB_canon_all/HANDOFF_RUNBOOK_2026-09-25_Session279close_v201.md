# HANDOFF RUNBOOK — v201 · written at the S279 close (the parent), 25-Sep-2026

*Supersedes v200 (the Sanjeevni S280 close) as the current runbook. Same shape: §0 where things stand · §1 the mental models · §2 the backlog in the owner's order · §3 what is live and where · §4 the rules that bind · §5 what to read first.*

## 0 · WHERE THINGS STAND

**Five days, fourteen kits live, every one from the owner's own line.** The Callback Tracker opens signed in from the Clinic app (S364); the caller's name reaches the staff phone as it rings, by Web Push (S366 → S369 → S370); the slip number leads the day report and the Parchi runs as the physical register does (S372, S379); X-rays are filed by the system (S374) and the Callback Tracker follows the morning exports within five minutes (S376); *Report baaki* gives the pathology desk, reception and Shavez one list of blood reports not yet mailed and X-rays with no film (S382 → S384); a consent's Hindi spelling is corrected once, everywhere (S385); the lab's mails with no clinic ID are joined by name only when certain (S391, S392); and Bhati's book refuses a repeated tap and tells him in Hindi what it saved (S394). Two kits went RED and were frozen (S373, S383), one was published and carried whole by its successor (S393), one was handed to the Sanjeevni chat unbuilt (S377).

**Settled with him at the close, not built:** the contacts plan (D614) — the next chat builds it, first.

**Two things over the line:** drift 5 on `slip_log.py` and on `portal.py` — read both whole before either is patched again (the next session's first half-hour, unless he waives it in one line). **One RED:** the 25-Sep nightly did not run (F-630).

## 1 · TEN MENTAL MODELS (v200's nine, parent-side, plus one)

1. **The board is the lock.** Every kit claimed before its folder was named; the one collision (S380) caught in scratch.
2. **A kit is a kit.** Scratch, walked on a fresh copy of the live database, gated, his double-click, his one line, read back, pinned.
3. **A clock time is read, never estimated.**
4. **The PC shell works again** (25-Sep) — and still no git in it.
5. **Full-file replacements, or anchored patches proven in scratch — and a file with five anchored patches is read whole before the sixth.**
6. **The Sanjeevni chat's files are its own.** S377 was his pasting into the wrong chat; the right move was to stop, hand over on the board, build nothing.
7. **A placed module is proven by importing it; a token-gated door behind the finance gate is probed for *locked* (302 or 401), never one code (F-621).**
8. **A post-place check names itself, and reads only its own restart's journal (F-622).**
9. **When the screen cannot be seen, make the page report its own state (F-623).**
10. **NEW · A feed that cannot parse something says so where a person reads it (F-624), and a walk replays the real feeder's order (F-625).**

## 2 · THE BACKLOG, IN HIS ORDER

0. **Read `slip_log.py` and `portal.py` whole** (drift 5 each) — or his one-line waiver.
1. **The contacts build (D614)** — `S279_BUILD_BRIEF.md` §2 is the plan, step by step. His two exports are `D:\Downloads\contacts bocbareilly.csv` and `D:\Downloads\contacts drmka.ortho.csv`; the patient master is the Callback Tracker's `Patient_Master` tab (read through Drive). Numbers never leave `finance.db` / `_config` / the scratch workspace (F-185).
2. **F-630** — why the 25-Sep nightly's catch-up did not fire: read the scheduled task's history on manojz from the PC shell.
3. **F-631** — widen `code_bundle.py`'s allow-list to carry the five files and two data files.
4. **D590 steps 2–3** — the caller card's outcome buttons and per-person counts.
5. **The rest of D589's order** — Block C remainder, Block B (the mail flood), Block A (the tiles), F-595 half 2, F-596's durable fix, Vitals & Plan to the VPS (F-598).
6. **Owed to the Sanjeevni chat, named by it:** F-607 fname mask in `api_yesbank_statement`, F-606 format string, F-599 resync on statement arrival.

## 3 · WHAT IS LIVE AND WHERE — the parent's files that moved (pins in Register v5.121 §S279)

`/root/portal/portal.py 80d6dc44` · `tracker_pass.py 97ac975a` · `ring_hook.py a3cd0466` · `ring_common.py 4344b592` · `portal_push.py 576ae269` · `portal_sw.js ab728b08` · `http_ece.py 8ed4b672` · `ring_setup.py 03ff5891` · `ring_agents_build.py 4f32d4bd` · `/etc/systemd/system/ring-hook.service 9cc46b3b` · `tile_grants.json 7d195476` (v25) · `casepack_portal.py cbbd392d` · `/root/wa/casepack/casepack_page.html 08807cdf` · `/root/finance/records.py 6492135c` · `slip_log.py ffb629c1` · `slip_lookup.py 46e67c65` · `finance_clinic_day.py f6729d83` · `clinic_day_pdf.py 150192e2` · `petty_book.py 698c988e` · `/root/wa/fu_push_on_arrival.sh 76502193` (cron `*/5`) · Apps Script `VPS_Lab_Files.gs` (sha256 `2cd99234…`) and the Callback Tracker's `WebApp.gs` / `Dashboard.html` (in `GAS_CURRENT`). Tables `pend_mark`, `lab_noid` NEW; `blood_order` four columns added. Backups `.bak_S3xx_<from8>` beside each placed file.

## 4 · THE RULES THAT BIND — unchanged, plus this session's

Everything in v200 §4 stands. Added: **every walk starts from a fresh copy of the nightly database and removes its own rows** (F-627); **a screen change is read at phone size by a second reader before it is named to him** (F-628); **a money form proves it saved by saying what it saved, in the user's language** (F-626); **Apps Script changes are placed in his signed-in browser and hashed back after a reload** (D577, re-proven S374 and S391).

## 5 · WHAT TO READ FIRST AT THE NEXT OPEN

`START_HERE_SESSION_282.md` · `S279_BUILD_BRIEF.md` · the Archive v1.118 §S279 (D614's full text) · the Fault Register v2.106 §7.40.

---
*HANDOFF_RUNBOOK v201 · S279 close · 25-Sep-2026 · every pin read from the installers' output and the 25-Sep 01:35 bundle; every time read from a clock.*
