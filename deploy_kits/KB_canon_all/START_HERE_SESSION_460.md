# START HERE — SESSION 460 — written at the S458 close (the parent), 14-Nov-2026 16:1x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz. *FIRST ACT: take session 460 from `board/_numbers` (RESERVED for the parent at the S458 close) by a pinned write of ONE SHORT line (under 400 characters) below the `session_note` digest.* Counters at this close: **D981 · F-1404 · A-D47 · kit S830 · session 461** (the other chats move them; read the board — `_numbers` is small again since the S458 trim, a plain read is cheap).

1. Follow `OPEN_ROUTINE_v1` (from the clone). **The first device call is `cat` of the routine and NOTHING else.** Then `echo ok`; `/sessions` was 100 % full — work from `/tmp` (`TMPDIR=/tmp TZ=Asia/Kolkata`). One helper at a time in the device VM (F-1382). Every file committed to the PC is read back by hash before use (F-1395).
2. **If the shell is dead:** say so in one line and do not wait (F-1375); the cloud route (A-D38).
3. Read `claude/S458_CLOSE_REPORT.md` and the Runbook's §2A (v367, from the clone; `OWNER_TODO_LIVE.md` and the pin list from the clone too — F-1354).

## A · At the open
- **The Sanjeevni chat's S457 close was HELD at the build (12:1x IST 14-Nov) and re-bases on this S458 close.** Read the board: if its READY line is missing, do not place anything into canon before it — its 459 open places it.
- **The day page** (first session of 15-Nov runs it whole). **The parent's DECLARED-PENDING 3** against the 15-Nov bundle: `/root/finance/pc_kits.py` 45d6f15d, `/root/deploy/repo_pull_s822.sh` 17ce188f (or "not in the bundle"), `/root/staff_ledger.py` 0086a952.
- **The first night of S822:** `D:\Downloads\_kbtools\PC_KITS_CURRENT_LATEST.txt` (15-Nov 03:18) — expected `medical_agent.py d91fa79a -> b94434dc` REPACKED, the seven August files listed; tell the Sanjeevni chat which the PC still has.
- **S811_FEED_ON_ARRIVAL's evenings and mornings since 13-Nov 21:45 — not looked at for three sessions.** Read what the bundle shows; ask him nothing.
- **Attendance (F-1402):** read `https://attendance.dr-manoj.in` (how many in today) — the machine went to the vendor on 14-Nov; until the silence alert is live, the count is read at every open. The reminders: the packs page (D713), BL Computers.

## B · Then the build — APPROVED (D979, D980, A-D46), in this order, each its own kit
The specification is the approved mock-up `https://claude.ai/artifact/W5TAwHRWP5zFBpN9HtqFhB` (seven boards; read with `read_file` on `project/*.dc.html`), `S450_XRAY_LAB_FILING_STUDY.md` §I and the S458 Archive §3–5 (the code facts verified on the 14-Nov bundle with file:line). Each kit: read the live files whole from the newest bundle FIRST (F-472) · build in `/tmp` · walk with a CONTROL that goes red · cold review by a second reader · `NO_PHONE_NUMBERS.py` · placed into `deploy_kits\S###_NAME\` · his publish + one server line. Staff screens in Hindi as the code has them; his screens in English.
1. **S8xx_ATT_SILENCE_ALERT (F-1402, small, first):** no machine contact for 30 min in clinic hours (`/root/attlistener_sources.jsonl`, its `t` field) or no punch by 10:00 on a working day (Sunday off) → one push to him (the portal's push, as S811's alert) + a console line; a repeated / lagging machine time → a clock warning. `/root/attlistener_v2.py` NOT touched.
2. **The due rule** (`xray_photo_nudge.py`, `slip_log.py`, `records.py`; DUTY_MAP `alisha.xray_photo` — SHARED: a PLANNED line on the board first, F-1024's REWRITE fit): morning X-ray due 3 pm the same day, evening 3 pm the next, by `clinic_day_line.shift`; a slip with no Docterz line uses its own time; a photo within 2 days counts; 7 days back.
3. **Check karein** (`check_screens.py`, `records.py`): the date strip; reception's "Kal ki X-ray"; "Kya yeh photo inki hai?"; "Muft X-ray" everywhere the payment-gap wording is (incl. `owner_console.py` 601–613 and `/finance/records/xray-check`); lab no-ID suggestions without the 7-day drop.
4. **The slips desk** (`parchi_desk.py`): the link's counts, the 7-day section, the search by name (masked mobiles).
5. **His X-ray sheet** (`clinic_lists.py`): the Photo column and the "Not filed" filter.
6. **The messages** (9:30 am; ~7 pm; the 3 / 6 pm notice counts only what is due): counts on the lock screen.
7. **Slips with no Docterz entry (D980):** the "Sirf X-ray" tick (a slip-table change — read the slip schema and every reader of it first); the X-ray-only lane; the OPD-miss card and the next-visit banner; **the "X-ray only" line in his daily revenue — find where the day's revenue is made (console, packs, the day check `slip_log.match_day`) before writing a word about it (F-1384).**

## C · After the build
The two switches' mock-up (D963) · the three small kits (D964) · one kit of the second readers' notes · the ticket's material (D938) · Step 3 of the follow-up feed.

**Standing rules:** as in `START_HERE_SESSION_458.md` and before, plus — **say a record is written only after the write returned (F-1403)** · **a database copy stays in the device VM and is removed at the close.**

**Standing owner rulings:** as before, plus **D979** (the filing mock-up approved, 14-Nov 16:08) and **D980** (slips with no Docterz entry).

*Written at the S458 close, 14-Nov-2026.*
