# S536_AMIR_BOARD_D712 — brief for Claude Code (v2 — after one independent read, `R1_S536_read.md`: 0 blockers, 5 corrections taken in)

*Written 12-Oct-2026 by the Sanjeevni chat (session 310). Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (v1.1) and `CLAUDE.md` first; `BUILD_NORM_v1` applies. This is a small follow-up to S533_AMIR_DAY_PAGE (live 05:48 IST 12-Oct), from the chat's live read of 06:0x IST: two lines S533 left standing. Kit shape: S533's (`deploy_kits/S533_AMIR_DAY_PAGE/` — make / walk / state / install / README / KIT_ID / PINS / SUMS); no data step. **Line numbers are the live bytes of 12-Oct 05:48 (S533's TOs).***

## 0 · For the owner

1. **Amir's board stops showing the reception-tap line (D712).** His board's section 4 *Baaki kaam* still prints *"KNEE IMMOBILIZER UNISON L — bill entry baaki: YUVIKA SURGICALS 01-10-2026 — maal aa gaya, Marg mein bill abhi nahi"* from reception's arrival tap. D712 says a line on Amir's screen rests on the scan, never on a tap; S533 took it off his card, this kit takes it off his board. The arrival without a scan stays **your** Needs-you line (S533's, unchanged).
2. **"Live orthotic ordering can start" waits until it is true.** Your Needs-you shows it today because the renames were all verified this morning, while voucher 29 still holds stage A open. After this kit it appears only once the count has passed the orthotic stages (stage C or done), for two days from the moment it did.

**The state on the day of install:** stage A, 7 of 8 (voucher 29 open), renames 23 of 23. After this kit: Amir's board section 4 shows no arrival line (the Sunday and fixes rows as today; *"Aaj kuch nahi — sab upar hai."* when nothing is left); your Needs-you no longer carries *"live orthotic ordering can start"*; your D712 line *"Goods tapped as arrived on 01-10 from YUVIKA SURGICALS …"* stays. **If voucher 29 is entered and proven before the install** (R1-4), the count reaches stage C on the first read, the release row is written, and the line shows after the install dated that day — correct; the installer prints which state it found.

## 1 · Numbers and pins

- Kit **S536** (claimed 06:2x IST 12-Oct, board `_numbers` v373 → v374). Rulings: D712, D708. Faults: F-864 (the tap line) — its last staff place; the second line has no F-number (named in the report).
- **Live files, FROM pins (read first; a different byte = STOP that file, report):**
  - `/root/finance/stock_app.py` **c626a46a** — one anchored edit in `_amir_board_light` 8624–
  - `/root/finance/stock_amir.html` **8dd65e64** — one anchored edit in `restCard` 157–
  - `/root/finance/amir_day.py` **262b0b81** — one anchored edit in `needs_you_lines` 2434–
- **Read only:** `stock_watch.py` c960f6c8 (`amir_view` still returns `bill_pending`; amir_day's D712 owner line reads it there, and the cron at 1824 prints it — both stay), `stock_hub.html`, `purchase_app.py` 147201dd, `stockmatch.py` 10e30d28, the DUTY_MAP (v11 69b8f56b — no duty moves), everything else.
- Services: `clinic-finance` restarted once. Scratch: `_scratch\S536_AMIR_BOARD_D712\` and the server's `/tmp`. The build lock as `CLAUDE.md`. No `.json` in the kit. No number of a person or patient (F-185).

## 2 · The edits

### 2.1 stock_app.py — `_amir_board_light` (charter 2, 9; D712)
Lines 8677–8683: `rest = dict(plan=None, bill_pending=[], fixes=[])` and `rest = dict(plan=W.get("plan"), bill_pending=[dict(item=…, text_hi=…) for x in (W.get("bill_pending") or [])], fixes=[…])`. **Drop the `bill_pending` key from both** (the second spans two lines, 8681–8682 — anchor both together; R1-1 of the read) (`rest = dict(plan=None, fixes=[])`; `rest = dict(plan=W.get("plan"), fixes=[…])`), each anchor exactly once. The board payload for EVERY login (the owner's board too) loses it — the arrival is the owner's Needs-you line (S533 §2.6.3), one place. Nothing else in the function moves.

### 2.2 stock_amir.html — `restCard` (charter 9)
Line 163: `(W.bill_pending||[]).forEach(x=>{ n++; h+='<div class="row">…maal aa gaya, Marg mein bill abhi nahi…'; });` — **removed whole** (the anchor: the line exactly, once); and the header comment at line 17 that still lists *bill entry baaki* among the board's sections is reworded to drop it (anchor once — R1-2). The rest of `restCard` (the Sunday rows, the fixes, the empty sentence) as today.

### 2.3 amir_day.py — `needs_you_lines`, the "ordering can start" line
Lines 2476–2478 today:
```
            bat = (st.get("B") or {}).get("verified_at")
            if bat and _days_since(bat) is not None and _days_since(bat) <= 2:
                out.append(dict(cls="warn", target="stock", text="Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)" % (st["count_id"], _dm_hm(bat, time=False))))
```
Replace with: the line only when `st.get("stage") in ("C", "done")`, and its moment = **the first stage-C release of the root** — `SELECT MIN(at) FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release'` (stock_app's `amir_stage` releases the first medicine lot on the very read that first finds stages A and B passed, 7785–7786, so that event IS the moment the orthotics cleared), falling back to `B.verified_at` when there is no release row (a count with no medicine batches goes straight to `done`); shown while `_days_since(<moment>) <= 2`; the text unchanged, its date the moment's. One anchored edit (the three lines exactly, once). The query runs inside **its own small try** (an error drops this one line only — `needs_you_lines` holds every later owner line in one try; R1-3). It reads `stock_stage_event` only, on the same connection after `state()` has called `amir_stage` (so a release written on that very read is seen); amir_day still writes no stage event. Known edge, accepted: a count with no medicine batches dates the line from `B.verified_at`, which may be more than two days before stage `done` — then the line does not show (R1-6; root 1 has 30 medicine batches, not affected).

## 3 · The walk (`walk_s536.py` — S533's shape: scratch copies by the backup API, fresh-process probes per side, the walk-only portal session, every control red on the OLD files, rows by key)

1. **Board, D712:** on a copy with one arrival tapped 5 days ago and no spine purchase (made-up `purchase_order_line` + vendor, as S533's walk 5) → `GET /finance/stock/api/pad/amir/<root>` as amir and as the owner: no `bill_pending` key in `rest`; the rendered board (the page's JS run, or the HTML grep plus the payload) carries no *"maal aa gaya"*; the owner's Needs-you still carries the D712 line for that arrival. **Control (old):** the payload carries the row and the board prints *"maal aa gaya, Marg mein bill abhi nahi"*.
2. **The ordering line** (each case on its OWN copy — a made-up root becomes the root amir_day reads; R1-10): (a) the install-day copy (stage A, B verified today) → no *"ordering can start"* (the control goes red on the old file only while `B.verified_at` is within 2 days — if the install is later, set `B`'s verified moment to today on the copy first; R1-9); (b) a copy where stage reaches C (the made-up root's orthotic batches entered and proven, as S524/S528's walks make it; or the A-pending line cleared and the proof `done` on a copy) → the first read writes the C release event, Needs-you carries the line dated that day; (c) the same copy with the earliest release event's `at` set three days back → no line (assert on `MIN(at)` — back-dating can trigger a second release on the next read; R1-10); (d) a made-up root with no medicine batches reaching `done` → the line from `B.verified_at`. **Control (old):** (a) prints the line.
3. **Not broken:** the light board JSON for the same copy byte-equal old vs new except the dropped key; the board page renders as amir and as the owner (sections 1–4, the Sunday buttons when a plan is open); the hub, Needs-you shapes, steps 1–7 as amir 200; `stock_watch.amir_view` still returns `bill_pending` (the owner's D712 line needs it).
4. **Greps** on the NEW bytes: `bill_pending` in `stock_amir.html` → 0 and `bill entry baaki` → 0; in `stock_app.py` → **0** (the old file has 2 — the control; R1-5); `py_compile` both pythons; the board payload as amir < 100 KB.

## 4 · Install, publish, report

S533's installer order: gates → the three FROM pins → the spine's `spine_state.json` passed and fresh (charter 1b) → compile → walk on scratch copies (DRY stops here) → `.bak_S536_<from8>` beside each file → place by rename → md5 read-back → ONE restart `clinic-finance` → `/finance/healthz` 200 → the state before/after (the board's section 4 rows as amir; the owner's Needs-you lines naming stage / orthotic / arrival) → on red restore the three files. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` when the kit is final (CLAUDE.md), install from the kit folder copied to the server, write `claude_code_briefs/REPORT_S536.md` (3–6 plain lines on top; FROM → TO read back; the walk with each control red; the state before/after; Charter — retired: the board's arrival row and the `bill_pending` key of the board payload; seen, not touched: `stock_watch.py`'s three places that still call the arrival a line on Amir's board (the settings hint 101, the docstring 862, the header 22–23 — R1-1), `_amir_board_light` still calling `amir_view` which computes `bill_pending` it no longer sends (R1-11), the release time being the first read after the orthotics cleared rather than the clearing itself (R1-7), and whatever else the build finds), publish again. **Do not pull `/root/deploy/repo` during the install** — nothing in this kit needs the clone.

**NEVER RUN:** `deploy_kits\S488_DATES_AND_WAITS\deliver_S488.ps1`. **NEVER ADD TO:** Amir's *Aaj ka kaam* list (D690).
