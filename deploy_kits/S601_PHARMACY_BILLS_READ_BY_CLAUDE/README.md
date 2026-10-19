# S601_PHARMACY_BILLS_READ_BY_CLAUDE — Claude fills the pharmacy bills; Sarvam behind the owner's setting (D747)

**Why.** The owner, 15:41 IST 19-Oct-2026 (ruling **D747**): *"Start Claude to read the pharmacy bills. Keep Sarvam switched off in settings
so that the code is made once."* Until now Sarvam filled every pharmacy bill and Claude read the same scan beside it, the reading kept aside
and used by nothing — every pharmacy bill paid for twice (`claude/S332_SCAN_READING_ASSESSMENT.md`: both readers about equal on the header,
Claude four times better on the item lines). The brief: `claude_code_briefs/S601_PHARMACY_BILLS_READ_BY_CLAUDE.md` (v2), read whole with its
independent review `03_WORKING_PAPERS/S332/S601_R1_REVIEW.md` (2 blockers, 19 corrections — all folded into v2, which governs). Board
`_numbers` v529 → v530. No F number.

**What changes.**
1. **Claude fills the pharmacy bills** — supplier, bill number, date, total and the item lines — the way it already fills the clinic's papers
   (`_s550_claude`: the pharmacy "beside" branch is deleted; a pharmacy paper, a **challan included**, takes the clinic lanes' path,
   `CLAUDE.read_bill`). Only what is empty is filled; the after-checks (the month, the double guard, S441's pass, the way home) run as before.
   The pharmacy lane's date rule (S566 item 5, `_norm_date`) is unchanged.
2. **Sarvam is switched OFF by a setting, not removed.** `_sarvam_on()` now also asks **`_sarvam_setting()`** — the ONLY reader of the
   settings row `read.sarvam` (`off` → False; absent or `on` → True; a database error → True). The installer's data step writes `off` (the
   owner's word). The admin page gains a second card **"Reading the scans — Sarvam"** (Now: ON / OFF / no key on the server; the Switch
   button only when the key is on the server; `set_read_sarvam` is the ONLY writer). The separate "Sarvam key configured" line and `ocr_key=`
   are retired into it (one fact, one place). The Claude card's words are rewritten (the retry, the pharmacy's papers).
3. **A paper Claude cannot read is tried again by the app itself** — `_s601_retry`, called by `_bg_extract` right AFTER `_set_ocr_status(bid,
   "failed")` (R1-B1): when Claude is on, the paper is one Claude is asked to read (`_s601_asked` — every lane but Other document, never a
   person's paper) and no `claude_reading` row with `ok=1` exists for it (a paper read as empty is not tried again, R1-B2), one more
   `_bg_extract` is timed with a daemon `threading.Timer` for 10, then 30, then 90 minutes later — three in all, never more; each audited as
   `read_retry {try, in_min}` through its own short connection. `_S601_TRIES` counts retries timed per paper — per gunicorn worker (`-w 2`),
   lost on a restart (the paper stays `failed`, counted on the owner's card). A reader stopped or off: `failed` at once, as today.
4. **Which reader filled a paper is recorded** — one `bill_audit` row `filled {by: claude | sarvam, items: N}` per fill, inside the open
   transaction right after the header/items write (F-949's remedy). `items` = what the reader gave, even when nothing was written (non-clobber).
5. **The checker's "Auto-fill from a scanned bill" form** (`bill_extract`): Claude first (`bid=None` — nothing recorded in `claude_reading`,
   the call counted), then Sarvam exactly as today, else *"No reader is on — enter the bill manually. The scan is attached."* The form's words
   are reader-neutral; the Re-read button's no-reader flash says the same line. (A synchronous read inside a request against gunicorn's 30 s
   worker timeout — the same shape as Sarvam's 180 s poll today; the fill lands by the thread even when the page times out. Accepted, stated.)
6. **`claude_reread.py`:** `to_fill()` no longer excludes the pharmacy lane (only `other_doc`); the docstring's line follows. Nothing else:
   one-shot, the lock file, not on any cron. The 140 stored pharmacy readings are applied by nothing (its SELECT takes only papers with no
   good reading) — by design: approved / already-filled papers are never overwritten; the first real scan after the install is the first fill.

**Files and pins (FROM → TO).** `/root/assetapp/asset_register.py` **`c39c084e` → `f29ee515`** (14 anchored edits — `make_s601.py`; the
`# --- S601_PHARMACY_BILLS_READ_BY_CLAUDE begin … S601 end ---` block before `main` holds `_S601_TRIES`, `_S601_DELAYS`, `_s601_asked`,
`_sarvam_setting`, `_s601_retry`, `_s601_sarvam_card`; inline edits marked `# S601`). `/root/assetapp/claude_reread.py` **`d9b75e78` →
`ed7023d2`** (2 anchored edits). The only two files changed. Read only, pinned, STOP if moved: `claude_reader.py 3894dc23`, `sorting_desk.py
110335ea`, `clinic_papers.py 6db07c12`, `batteries.py 775471e6` (S582's TO), `stationery.py 18268ff0` (S585's TO), `xray_costs.py 22e59f5a`,
`asset_machine.py 7d4fdffc`, `scanner_widget.js 10a8bb29`, `/root/shared/sarvam_ocr.py b1cc567b`, the parent's `/root/finance/packs.py
e46264b8`. The Sanjeevni files `purchase_app.py 60f2d846`, `scan_register.py 904f07b1`, `item_check.py 6f3faf89`, `amir_day.py 3af992d9`,
`porders.py e5a5c4d4`, `order_sheet.py 1f1e85c1`: printed at the open, never placed, proven unmoved after placing. **`assets.db`: no DDL, no
new table.** ONE data step after health: `settings read.sarvam = off` (rehearsed on the scratch copy first; NOT written on a red). The
database is backed up (`assets.db.bak_S601_<stamp>`, the backup API) BEFORE the restart. Restarts **assetapp only**, once. No staff screen
changes; no duty added, moved or removed (`DUTY_MAP` untouched). The owner's English only on the admin cards.

**Kit.** `make_s601.py` (the patcher) · `walk_s601.py` (W1, W2, G1 the grep proof, C1–C11; `--expect-red` = the control on the OLD files,
which also writes `--dump`; the NEW run compares with `--old-dump`; `--state` = the install-day state) · `install_s601.sh` (S585's shape +
the Sanjeevni gates: the window 08:00–23:49 IST, SUMS, KIT_ID, the pins; the build lock; `claude_reader.state` = on and the key file present
or STOP; the crontab read; the walk OLD → NEW; the data step rehearsed; S585's chain of earlier walks — S585, S582, S575, S571, S568, S566,
S563 with its tidy fetch, S560 + pack, S548, S559, S557, S555, S551; DRY stops; the state before; backups; the two files staged and renamed
in ONE command; one restart; `/healthz` 200, `/admin` 302, `/bills` 302; journal clean; the data step; the state after; nothing else moved;
md5 read-back) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`. The walk never makes a real API call and never reads the key: `asset_register.CLAUDE`
is a stub (read_bill per control; read is OLD's thread target; everything else to the real `claude_reader` on the copy), SARVAM is None or a
counting stub, `threading.Timer` queues and runs nothing — the queue is drained after `_bg_extract` returns.

**Proof (19-Oct-2026, on the box in /tmp only):** `claude_code_briefs/REPORT_S601.md`.

**Install (on the box, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S601_PHARMACY_BILLS_READ_BY_CLAUDE/install_s601.sh`
(`DRY=1` in front stops before placing: every gate, the build, every walk.) The build lock stays held until the report is written.

**UNDO (one line):**
`\cp -p /root/assetapp/asset_register.py.bak_S601_c39c084e /root/assetapp/asset_register.py && \cp -p /root/assetapp/claude_reread.py.bak_S601_d9b75e78 /root/assetapp/claude_reread.py && systemctl restart assetapp`
— then `/healthz` 200 and the two files back at `c39c084e` / `d9b75e78`. The setting `read.sarvam = off` stays (the old file ignores it; the
owner's new card is the door to switch it, and the old page has no such card). The audit rows `filled` / `read_retry` stay (records, never
deleted). The database backup `assets.db.bak_S601_<stamp>` is needed only if the data change itself must be reversed — say so before using it.

**Charter.** Retired: the pharmacy "beside" read; Sarvam as the pharmacy filler (by the setting, the code kept at the owner's word); the admin
page's separate "Sarvam key configured" line. One fact, one place: which reader filled a paper — the `filled` row; Sarvam on/off —
`read.sarvam` read by `_sarvam_setting()` only; Claude on/off — `read.claude` as before; which papers Claude is asked to read —
`_s601_asked()`. Left, named: `claude_reread.py` one-shot (no cron — the crontab is not touched; D747 did not ask for it); the retry timers per
worker and not surviving a restart; the daily cap 400 against ~300 papers a month; the Haiku model as the reader's own fall-back (a shadow
trial is the chat's later work); the other lanes' handwritten challans (the Scan App chat's); `bill_extract`'s synchronous read against the
30 s worker timeout; the Sanjeevni "Sarvam check" page's name (it now judges Claude's lines; a Sanjeevni small-kit item). Behaviour changes:
a pharmacy paper's header and items come from Claude; a failed read is retried by the app (three times, never for an excluded or
read-as-empty paper); Sarvam reads nothing anywhere while the setting is `off` (the `other_doc` / person papers, never sent to Claude, are then
typed in — as when no key was set); the Sanjeevni resolver (`order_sheet.py:1440–1441`) learns supplier spellings from the filled `vendor` —
Claude's spellings may differ from Sarvam's learnt ones, so a few more "reception's choice" questions at first, each learnt once;
`order_sheet.unread()` calls a `failed` paper unread at once — with the retry the header may arrive up to 2 h later after an S454 question
was asked; it resolves on the next read as any late fill does.
