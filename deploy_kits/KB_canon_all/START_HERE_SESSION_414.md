# START HERE — SESSION 414 — written at the S412 close (the Sanjeevni chat), 09-Nov-2026 (07:5x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **Kit S756_SUMMARY_DEALER_WA was INSTALLED at S412 (07:46 IST):** the awaited dealers of an ended month get one WhatsApp a day from the reception phone (his Hindi words, 11:30 IST, Sundays too, D876); the snapshot sits at the top of the purchase check; row 7 counts every dealer (F-1208); owner_notice's morning summaries line runs at last (F-1207). **His word at the close: "Do EOS here and the build in a fresh session"** — this session builds the hub.

**⚠ THE S412 CLOSE'S CANON IS NOT YET PLACED.** The device shell was down at the close ("Failed to create bridge sockets", F-1197). Its parts are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S412\close_parts\` (close.json and the parts, written for Register v5.246 · Archive v1.243 · Fault v2.230 §7.163 · Runbook v326 · `START_HERE_SESSION_414` · Book v1.54 · `live_pins_S412close.txt`). **First work of this session, before anything else:** read the manifest's CURRENT rows; if another chat closed after the parent's S404 (the parent's 413 was open), renumber every part and `close.json` onto the next free versions and rename what changes; then `python D:\Downloads\_kbtools\close_build.py <close.json>`, read the table, fix any STOP in the parts, `--place`; the board's READY line for S412; the publish named to him (`D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`).

1. **The open:** `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - If the device shell fails, work as S412 did: stage the newest bundle (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`) into the cloud — code only, never a database (D656) — build there, place by the file tools, read back by hash. The canon placing above needs the shell (`close_build.py` reads 885 MB of canon).
   - In the device VM: `TMPDIR=/tmp/s414w`; `pip3 install --no-cache-dir --target /tmp/s414w/pylib flask`, `PYTHONPATH=/tmp/s414w/pylib`. A background job dies with the call that started it — run walks in the foreground, a pair at a time.
   - **The pins:** S756's three DECLARED-PENDING (`scan_register.py` 9262c5dc · `purchase_app.py` 8424e05b · `owner_notice.py` 537b7c32) until a bundle newer than 07:46 IST 09-Nov — the 10-Nov bundle should confirm them.
   - **Remind him once of the packs page** (D713) **and F-1133** (D837) — one line each.
2. **Check S756's first day (read only, a sub-agent for screens):** the 11:30 batch (`supplier_msg` kind `summary`, ref `20261109` — expected 5 sent, Bass *number nahi*); the morning line `summaries:2026-10:2026-11-09` in `owner_notice`; the snapshot's *Last reminder* column; the tick's log line (`/root/finance/owner_notice.log`, `summary_wa`). Any dealer messaged whose summary had come is a RED — the undo line is in the S412 install output (`03_WORKING_PAPERS\S412\`) and the kit's README.
3. **The rules:** the charter v1.1 (`claude/S307_BUILD_CHARTER_v1_1.md`) beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `03_WORKING_PAPERS\S412\close_parts\` — copy it, change what changed.
4. **The papers:** the brief `S412_BUILD_BRIEF.md`; the mocks on the Design canvas:

```
https://claude.ai/artifact/8JhQwrXJ56WAtdCZGUUHN1
```

   Page *Hub page*: `Hub.dc.html`, `GoTo.dc.html`. Page *Returns*: `Main.dc.html` (approved, D873), `Batch.dc.html`, `Phone.dc.html`. Page *Summaries*: `Snapshot.dc.html`, `Reminder.dc.html` (approved, D876; built as S756). Read the canvas and its comments first.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).* **414 is RESERVED for the Sanjeevni chat at this close.** The NK Pathology chat's 365 and the parent's 413 are open; the Scan App chat's 410 reserved. Re-read `_numbers` just before every pinned write (read with `out_dir`, write with `file_path`) — the parent took F-1201 … F-1206 minutes after S412 assumed F-1201.

**The S756 kit is the pattern to copy now** (`deploy_kits\S756_SUMMARY_DEALER_WA\`): makers with anchored edits on the live bytes · the walk on S755's made-up fixture with a CONTROL · the earlier walks compared · the proof on the live databases (a writer tried on a COPY) · the cron shape run as a FILE · a sender held off from [5/7] to [7/7] · the rehearsal on a made-up root (setup/dry/real/again/red) · cold reviews until SAFE · the screens read live by a sub-agent as manoj. **A close's pin rows are `| path | full md5 | state |`** (F-1198).

---

## 0 · THE WORK — in order

**A · THE OPEN** — the S412 canon placed (above); the board; the day's checks; the four numbers; the two reminders; S756's first day.

**B · THE WORK**
1. **THE HUB BUILD** (D873; the canvas is the spec) — `https://followup.dr-manoj.in/finance/approvals` (tile *Sanjeevni Medicos*; `finance_ui/finance_approvals.html` served by `finance_app.py`; data from `sanjeevni_approvals.py`; the Returns card from `/finance/darpan/api/cn-detail?month=` with `returns_kinds`). The Returns card as approved (newest first; F-1200 the rounding badge; the batch check as a count; Reject on the questioned amount; can't-be-checked; months folded; history); Needs you grouped (red first; *arrived but not in Marg* by dealer; information folded); the Go to panel with live counts (Amir's step page left out — its GET writes); Cash and Bank as figures; **F-1199** (one figure, one name, one count). Read each file whole first; the mock is approved before code for any part he has not settled; **a PLANNED line on `board/_numbers` before touching `finance_app.py`** (the parent's, D646). His own page: PC first, the Fold phone second (D853).
2. **F-802's permanent fix** — its own small kit (D867 / D868; `START_HERE_SESSION_411` B1).
3. **The order-list kit**, on his "go", the mock first (`S402_ORDER_LIST_PLAN.md`).
4. **Small / his / staff / parked / not ours:** as `HANDOFF_RUNBOOK` v326 §2B items 5 – 8 (F-1209 first among the small).
5. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER** (whole, as `START_HERE_SESSION_412` listed), plus: change S756's wording without him (D876); queue a message without a withdrawal on every path; install a sender without the hold.

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_412` listed them, plus **D876** (the dealer reminder).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat. English to him.** **ALL-CAPS = urgent.** **"Only answer" / "do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first.**
6. **Never put a technical choice to him** — decide, say it in one line. **A screen for staff or for him: the mock first.** **His own pages: PC first, the Fold phone second (D853).**
