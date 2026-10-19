# REPORT_S601 — S601_PHARMACY_BILLS_READ_BY_CLAUDE (D747) — installed 19-Oct-2026, 17:29 IST

## For the owner

1. **Claude now fills the pharmacy bills** — supplier, bill number, date, total and the item lines — the way it already fills the clinic's
   papers. A handwritten pharmacy challan is read the same way. The next pharmacy scan after 17:29 IST today is the first one Claude fills;
   the chat will read it and tell you.
2. **Sarvam is switched OFF by a setting, not removed.** Your scan-app Admin page now has a card **"Reading the scans — Sarvam"** reading
   **Now: OFF** with a **Switch ON** button, beside the Claude card (whose words now say what it does). Nothing of Sarvam's code is deleted.
3. **If Claude cannot read a paper** (the day's limit, a bad photo) the app tries again by itself three times over the next two hours; a paper
   still unread shows in the "could not read" count on your Claude card. Staff see nothing new; the paper opens as it always has, to be typed in.
4. Nothing changes on any pharmacy or staff page: the paper still links to Marg's bill by supplier + number + total. A few more "which
   supplier is this?" questions may reach reception's choice at first (Claude spells a name slightly differently from Sarvam's learnt
   spellings); each is learnt once, as before.
5. It is installed, tested and working: the scan app restarted once at 17:29:28 IST, healthz 200, every page gated as before, the test walk
   14 of 14 green on the box and the same walk red on the old files, and all fourteen earlier scan-app walks green on the new files.

## For the chat

**Kit:** `deploy_kits/S601_PHARMACY_BILLS_READ_BY_CLAUDE/` (make_s601.py · walk_s601.py · install_s601.sh · rehearse_s601.sh · 29 PIN files ·
KIT_ID.txt · README.md · SUMS.md5). Installed from `/tmp/s601kit/S601_PHARMACY_BILLS_READ_BY_CLAUDE` (a tar of the kit folder; `md5sum -c
SUMS.md5` 0 failures before the run) with `S601_KITS_DIR=/root/deploy/repo/deploy_kits` for the earlier kits; after publishing, the clone's
copy is verified byte-identical (`git pull`, `md5sum -c SUMS.md5`) — see the end of this report.

**Live files, FROM → TO, read back on the box after placing (install log [12] and the proof run at 17:32:54 IST):**

| file | FROM | TO (read back) | edits |
|---|---|---|---|
| `/root/assetapp/asset_register.py` | `c39c084eabf52daa0da9cc6720fc7aa7` | `f29ee51561ef73b837a25e56651108ac` | 14 anchored, each anchor once |
| `/root/assetapp/claude_reread.py` | `d9b75e784c4a806e941f3d1a243990e1` | `ed7023d22e725b5f4e0a700494059e2b` | 2 anchored, each anchor once |

Read only, pinned, unchanged before and after (the installer STOPs on a moved one, and re-reads them after placing): `claude_reader.py
3894dc23`, `sorting_desk.py 110335ea`, `clinic_papers.py 6db07c12`, `batteries.py 775471e6`, `stationery.py 18268ff0`, `xray_costs.py
22e59f5a`, `asset_machine.py 7d4fdffc`, `scanner_widget.js 10a8bb29`, `/root/shared/sarvam_ocr.py b1cc567b`, `/root/finance/packs.py
e46264b8`. The six Sanjeevni files printed at the open and proven unmoved after placing: `purchase_app.py 60f2d846`, `scan_register.py
904f07b1`, `item_check.py 6f3faf89`, `amir_day.py 3af992d9`, `porders.py e5a5c4d4`, `order_sheet.py 1f1e85c1`. The crontab (84 lines, 0
`claude_reread` lines — expected) unchanged.

**The service environment** carries only `SARVAM_API_KEY`: `ASSETS_DB`, `ASSETS_UPLOADS` and `SCANAPP_ANTHROPIC_KEY_FILE` are absent from
the unit, so the app runs on the modules' defaults (`/root/assetapp/assets.db`, `/root/assetapp/uploads`, `/root/.scanapp_secrets/anthropic.key`);
the installer reads the unit and falls back to those (stated in its log [1]). At the open: the key file present (never shown),
`claude_reader.state = on`, `read.claude_model = claude-sonnet-5-5`, `calls_today = 0`, `cap = 400`.

**Backups made (before the restart and the data step):** `/root/assetapp/asset_register.py.bak_S601_c39c084e` (300320 bytes),
`/root/assetapp/claude_reread.py.bak_S601_d9b75e78` (7336 bytes), `/root/assetapp/assets.db.bak_S601_20261019_172831` (573440 bytes, the
backup API, mode 600).

**Service restarted:** `assetapp` only, once, at **2026-10-19 17:29:28** (the box's clock). `/healthz` 200; `/admin` 302 and `/bills` 302 to
a plain curl (the login gate, expected); journal clean since the restart (the only two lines matching "ERROR" are gunicorn's own
"Worker was sent SIGTERM" at 17:29:28 — the restart itself). Re-checked at 17:32:54: healthz 200, the unit active.

**The data step:** `settings read.sarvam = off` written at **2026-10-19 17:29:30** (one INSERT OR REPLACE, rehearsed on the scratch copy
first; read back `off` at 17:32:54). No DDL, no new table. No `filled` / `read_retry` audit row exists yet (no scan has come in since;
max bill id 191, as before).

**The install-day state (the walk's `--state`, the owner's Admin page rendered on a copy by a walk-only login):**
- before (the live files): `Claude: ON · today 0 limit 400 · read so far 173 · could not read 3; Sarvam: no card; 'Sarvam key configured' line present`
- the NEW files on the same copy: `Claude: ON · … ; Sarvam: OFF; 'Sarvam key configured' line absent`
- after (the live files, a fresh copy, the setting written): `Claude: ON · today 0 limit 400 · read so far 173 · could not read 3; Sarvam: OFF; 'Sarvam key configured' line absent`
- a caution on the "Sarvam: OFF" of those two renders: the walk's scratch carries no `SARVAM_API_KEY`, so `sarvam_ocr.available()` is False
  there and the card reads OFF whatever the setting — the render proves the card's presence and words, not the setting. That the card
  follows the setting is C10 (the stub); that the live setting is `off` is the read-back at 17:29:30 and again at 17:32:54.
- pharmacy papers by ocr_status: `read=148` before and after; pharmacy papers with a good Claude reading: 140 before and after.

### The walk and the negative control (on the box, a scratch copy of the live database; made-up rows; never the key; no API call)

Install log [7]: `control (the live files, must be red): 14 checks: 3 GREEN, 11 RED (W2, G1, C1, C2, C3, C4, C5, C7, C8, C9, C10)` ·
`CONTROL must-be-red: W2, G1, C1, C2, C3, C4, C5, C7, C8, C9, C10 -- all RED` · `CONTROL structural (green on both, named): W1 GREEN, C6
GREEN, C11 GREEN` · `walk (the built files): 14 checks: 14 GREEN, 0 RED`. The same two runs repeated after the install against a fresh copy
of the live database (the OLD files = the `.bak_S601` backups; the NEW = the live files): OLD exit 0 (all must-red RED), NEW `14 checks: 14
GREEN, 0 RED`. Verbatim from that NEW run (the brief's controls 1–4, 6, 8, 10, 11; the counts lines are the walk's own print):

```
G1 counts: {'beside thread': 0, 'def _sarvam_setting': 1, 'read.sarvam': 2, '"filled"': 1, '"read_retry"': 1, '_S601_TRIES =': 1, 'def _s601_asked': 1, '_s601_asked( uses': 2, 'Sarvam key configured': 0, 'ocr_key': 0, 'reread pharmacy exclusion': 0, 'ten-digit run': 0}
C1 counts: _bg_extract -> 'read'; the stub's calls [(193, 'read_bill')]; vendor 'Made-Up Pharma Walk 2031' bill_no 'W601-C1' date '2026-10-12' total 1250.0; items 2; ocr_status 'read'; `filled` rows [('filled', {'by': 'claude', 'items': 2})]; audit actions ['filled', 's441_question']; dup_flag None; queued 0
GREEN C1 a pharmacy paper (lane pharmacy, kind Pharmacy, empty header) through _bg_extract with the Claude stub answering a header (date 12-10-2026 -> stored 2026-10-12 through _norm_date) and two items: vendor, bill_no, bill_date, total and 2 bill_items written, ocr_status 'read', ONE bill_audit row filled {by: claude, items: 2}; _dup_after_ocr and S441's pass ran on the filled data (no exception, no dup mark on a fresh paper); the stub asked through read_bill, not a beside thread
C2 counts: -> 'read'; vendor 'Made-Up Pharma Walk 2031'; kind 'Challan' doc_kind 'challan' challan_state 'awaiting'; items 2; `filled` [('filled', {'by': 'claude', 'items': 2})]; in the Sanjeevni listing before False after False
GREEN C2 a pharmacy challan (kind Challan, doc_kind challan, lane pharmacy) is filled the same way on NEW: vendor, number, date and the items written, the `filled` row; challan_state 'awaiting' before and after; kind stays Challan; the Sanjeevni register's asset_scans query (kind='Pharmacy' AND status='captured') does not list it before or after
C3 counts: setting off + Claude cannot read: Sarvam calls 0, -> 'failed', ocr_status 'failed', vendor None; setting absent + Claude off: Sarvam calls 1, -> 'read', ocr_status 'read', vendor 'Made-Up Sarvam Vendor 2031', `filled` [('filled', {'by': 'sarvam', 'items': 0})]
GREEN C3 Sarvam OFF by the setting: with read.sarvam = off and the Claude stub answering nothing (no claude_reading row with ok=1), the counting Sarvam stub is NEVER called (0) and the paper reads `failed`; with the setting absent and read.claude = off the Sarvam stub IS called (absent = today) and fills the paper (filled {by: sarvam})
C4 counts: first call -> 'failed', ocr_status 'failed', queued [(600, True, True, (197, '/tmp/s601kit/proof/w1/uploads/w601_p4.pdf'))], read_retry [('read_retry', {'try': 1, 'in_min': 10})]; after the first drain -> 'failed', ocr_status 'failed', queued [(1800, True, True, (197, '/tmp/s601kit/proof/w1/uploads/w601_p4.pdf'))], read_retry [('read_retry', {'try': 1, 'in_min': 10}), ('read_retry', {'try': 2, 'in_min': 30})]; after the second drain -> 'read', ocr_status 'read', vendor 'Made-Up Pharma Walk 2031', queued [], `filled` [('filled', {'by': 'claude', 'items': 2})], _S601_TRIES[bid] 2
C4b counts: delays run [600, 1800, 5400], calls 4, read_retry [('read_retry', {'try': 1, 'in_min': 10}), ('read_retry', {'try': 2, 'in_min': 30}), ('read_retry', {'try': 3, 'in_min': 90})], ocr_status 'failed', queued after the fourth call 0, _S601_TRIES[bid] 3
C4c counts (read as empty): ('failed', 'failed', 0, [], [(1,)], None); C4d counts (stopped): ('failed', 'failed', 0, [], [], None)
GREEN C4 the retry: the Claude stub answers nothing twice and a reading the third time -> after the first call ocr_status 'failed', ONE queued daemon Timer of 10 min (600 s) on _bg_extract(bid, path), one read_retry {try: 1, in_min: 10} row; the queue drained AFTER the call returned -> 'failed', a 30-min Timer, read_retry {try: 2}; drained again -> filled, 'read', the `filled` row, _S601_TRIES[bid] == 2. A stub that always answers nothing -> exactly 3 retries (10, 30, 90 min), then 'failed' and nothing queued on the fourth call. A paper read as EMPTY (an ok=1 reading of nothing) -> 'failed', NO retry, no read_retry row. read.claude = stopped:… -> 'failed' at once, no retry, the stub not asked
C5 counts: {'c5a': ('read', ['Made-Up Pharma Walk 2031', 'W601-C5A', '2026-10-12', 333.0], 2, ['s441_question'], [['filled', {'by': 'claude', 'items': 2}]]), 'c5b': ('read', ['Made-Up Pharma Walk 2031', 'W601-C5B', '2026-10-12', 444.0], 2, ['s441_question'], [['filled', {'by': 'claude', 'items': 2}]])}; OLD's results given True, equal on header / items / audit (filled apart) True
C6 counts: {'c6a': ('failed', [], None, 0, [], None), 'c6b': ('failed', [], None, 0, [], None), 'c6c': ('failed', [], None, 0, [], None), 'c6d': ('failed', [], None, 0, [], None)}
GREEN C6 the exclusions unchanged: other_doc, personal, resume and patient_paper papers (no Sarvam module) -> the Claude stub never called (as OLD), nothing written, `failed`, and (R1-B2) zero read_retry rows and nothing queued
C7 counts: -> 'read'; vendor 'Typed By Reception 2031' bill_no 'W601-TYPED' total 500.0 date '2026-10-12'; items 1; `filled` [('filled', {'by': 'claude', 'items': 2})]
C8 counts: to_fill {'pharmacy captured empty': True, 'pharmacy approved': False, 'other_doc': False, 'clinic draft': True}; _run's SELECT on the copy: 9 papers, pharmacy papers with a good reading 145, selected among them 0
GREEN C8 the reread: claude_reread.to_fill on a captured, empty pharmacy row -> True (OLD: False); on an approved pharmacy row -> False (the SELECT still reads it: the reading is kept aside); on other_doc -> False (never selected); a clinic draft -> True; _run's own SELECT (the file's text, run on the copy) selects NONE of the pharmacy papers that already have a good reading -- the 140 stored readings are applied by nothing (by design)
C9 counts: Claude on (200, True, True, 0, ['read_bill'], [None]); Claude off + Sarvam (200, True, True, 1, []); both off (200, True, True, False, []); the form's words (off, on, old words) (True, True, False, False); the re-read with no reader: 302 ['No reader is on — enter the bill manually. The scan is attached.']
C10 counts: Sarvam card before (['ON'], True, True, True, True); the Claude card's words (True, True, False, False, ['ON']); the switch POST 302 ['Sarvam reading the scans is now OFF.'] -> setting off; after (['OFF'], True); set_read_claude -> off, the Claude card ['OFF']; Hindi words []; the old key line False; CLAUDE=None -> (Sarvam card, Claude card) (True, False); no key -> (['no key on the server'], False)
GREEN C10 the admin page as the owner: the Claude card's new words (the retry, the pharmacy's papers; the old 'kept aside' and 'Sarvam carries on' gone); the Sarvam card 'Reading the scans -- Sarvam' with Now: ON and Switch OFF before the setting; set_read_sarvam writes read.sarvam = off, flashes, and the card reads Now: OFF with Switch ON; set_read_claude unchanged; 'Sarvam key configured' absent from the page; no Hindi on the two cards; with CLAUDE = None the Sarvam card still renders (its own variable); with no Sarvam key the card says 'no key on the server' and offers no switch
C11 counts: the Sanjeevni listing before 135 after 144 (the walk's own pharmacy bills 9; the challan listed False); link words in the S601 block []; staff pages dumped 9 (codes {'owner desk': 200, 'owner bills': 200, 'owner paper': 200, 'manager desk': 200, 'manager bills': 200, 'manager paper': 200, 'reception desk': 403, 'reception bills': 200, 'reception paper': 200}); OLD's dump given True, byte-equal True
GREEN C11 nothing else moved: the Sanjeevni register's asset_scans query on the copy lists, after the walk, exactly what it listed before plus the walk's own pharmacy bills (never the challan); the S601 block opens no finance table (the link table is not touched); the sorting desk, the bills list and the typed pharmacy paper's page for the owner, a manager and a scanning login (the desk refuses that login) rendered BEFORE the controls -- byte-equal to the OLD files' (--old-dump; --dump on the OLD run)
```

Notes on the controls: (a) the paper ids in the counts (193, 197) are the scratch copy's own made-up rows, removed with the copy; `W601-…`
stamps, a made-up supplier, no person; (b) C5 compares header, items and the audit rows (action, detail) OLD vs NEW through the dump — equal;
the `s441_question` row on both is S441's own after-check on a fresh made-up supplier (the same on OLD); (c) C6 is the structural "as OLD"
control — green on both, as named; (d) the walk's `read` stub (OLD's beside-thread target) is exercised only on the OLD run — the control's
C1 is red there because the paper stays empty (SARVAM None) and the stub is asked through `read`, not `read_bill`.

**The chain of earlier walks on the NEW files (install log [9]):** S585 11/11 · S582 14/14 · S575 8/8 · S571 12/12 · S568 14/14 · S566
12/12 · S563 17/17 (its tidy fetch: 102 answers each, differing none) · S560 37/37 · S560 pack 9/9 · S548 8/8 · S559 43/43 · S557 41/41 ·
S555 19/19 · S551 87/87 — all green; asserted, not assumed (R1's note that they filter `bill_audit` by action and baseline only the
intake / reception / machine pages holds).

**Rehearsal (BUILD_NORM §3) on a made-up root under `/tmp/s601reh` with a stand-in service, a made-up key file, the restart = true (before
the install; its log carries no clock, so no time is quoted): REHEARSAL GREEN** — a fresh install green (the two files placed, their backups beside them, the database backed up first and equal to the
database before, ONLY `read.sarvam = off` added, the lock kept); ALREADY INSTALLED; a forced red after placing restored both files with the
setting NOT written; `/admin` 404, `/admin` 200 (a login gate open), `/bills` 404 and a forced red data step each restored (302 only); a moved
`asset_register.py`, a moved read-only file (`claude_reader.py`), `read.claude = off` and an empty key file each REFUSED before anything was
placed; the live scan app's, finance folder's and /root/shared's program files read back unchanged. Before the rehearsal, a DRY=1 run of
the installer on the box was green on every gate, the build, both walks and the chain (nothing placed, no lock).

**Build lock:** taken 2026-10-19 17:28:32 IST by `S601_PHARMACY_BILLS_READ_BY_CLAUDE`, held through this report — **and still held: see
"Publish and the clone" at the end** (its removal from my shell was refused by the permission list; one line for the chat is given there).

### What was NOT done, and why
- **The other lanes' handwritten challans** — the Scan App chat's (told on the board); not in this brief.
- **A cron for `claude_reread.py`** — none, by design (one-shot; D747 did not ask for it; the crontab is not touched).
- **The 140 stored pharmacy readings are not applied** — by design: `_run`'s SELECT takes only papers with no good reading (C8 proves it on
  the copy), and approved / already-filled papers are never overwritten. The first real pharmacy scan after 17:29 IST is the first Claude fill.
- **The Sanjeevni "Sarvam check" page's name** (`purchase_sarvam_check`, S446) now judges Claude's lines; renaming it is a Sanjeevni small-kit
  item — named, not done here (no Sanjeevni file is touched).
- **No real paper was read by the installer** (no API call; `calls_today` 0 before and after).
- **A memory note for Claude Code's own use** (the PC-side gotchas met today) could not be written: the memory folder is denied by the
  permission settings here. Not part of the kit; named as CLAUDE.md asks.
- **No staff duty added, moved or removed**: `DUTY_MAP.md` / `DUTY_MAP.json` untouched; no staff screen changes (C11 proves the desk, the
  bills list and a pharmacy paper's page byte-equal for the owner, a manager and a scanning login).

### Calls made without asking (the rulebook: never pause)
- The installer keeps the build lock on success (CLAUDE.md: until the report is written) rather than releasing it at its end as the brief's
  §5 line reads; the brief's §6 order (publish, verify the clone, release) is followed.
- The Sanjeevni six are pinned and printed; the installer STOPs only for the ten read-only files the walk was proven on, and re-reads all
  sixteen after placing (restore if any moved) — the brief's "print their md5s, place nothing" read as: warn at the open, prove unmoved after.
- The service unit carries no `ASSETS_DB` / `ASSETS_UPLOADS` / `SCANAPP_ANTHROPIC_KEY_FILE`: the installer falls back to the modules' own
  defaults and says so, rather than refusing.
- `_s601_retry` is a fifth function in the tail block (the brief's four plus it): the retry's body lives there, and `_bg_extract`'s call
  site is one line after `_set_ocr_status(bid, "failed")` — R1-B1's order kept, the inline edit small.
- The walk's `--state` renders the Admin card with a made-up key file (so `key_present()` answers True on the copy) — the installer checks the
  live key file's presence and `claude_reader.state` separately, in-process, printing only the state.
- Three faults found and fixed during the build, none in the brief: the walk's made-up papers first shared one scan minute (S441's page-join
  paired two of them — a day apart now); the walk first expected the re-read's SELECT to skip an approved paper (it reads it, the reading kept
  aside — the assertion corrected); two of my own docstrings named the grep-proof words (reworded: the proof counts hold).

### Charter (v1.1)
- **Retired:** the pharmacy "beside" read (a second paid reading nothing used); Sarvam as the pharmacy filler (by the setting; the code kept at
  the owner's word); the admin page's separate "Sarvam key configured" line and `ocr_key=` (into the Sarvam card — one place).
- **One fact, one place:** which reader filled a paper — the `filled` audit row; Sarvam on/off — `read.sarvam`, read by `_sarvam_setting()`
  only, written by `set_read_sarvam` only; Claude on/off — `read.claude` as before; which papers Claude is asked to read — `_s601_asked()`.
- **Left (named):** `claude_reread.py` one-shot, no cron; the retry timers per gunicorn worker (`-w 2`), not surviving a restart (the paper
  stays `failed`, counted on the card); the daily cap 400 against ~300 papers a month; the Haiku model as the reader's own fall-back (a
  Sonnet-vs-Haiku shadow trial is the chat's later work); the other lanes' handwritten challans; `bill_extract`'s synchronous read against
  gunicorn's 30 s worker timeout (Sarvam's 180 s poll has the same shape today — accepted, stated: the fill lands by the thread even when the
  page times out).
- **Behaviour changes (rules 4, 7):** a pharmacy paper's header and items come from Claude; a failed read is retried by the app (three times,
  never for an excluded or read-as-empty paper); Sarvam reads nothing anywhere while the setting is `off` — the `other_doc` / person papers,
  never sent to Claude, are then typed in (as when no key was set); the Sanjeevni resolver (`order_sheet.py:1440–1441`) learns supplier
  spellings from the filled `vendor` — Claude's spellings may differ from Sarvam's learnt ones, so a few more "reception's choice" questions at
  first, each learnt once (R1-20); `order_sheet.unread()` calls a `failed` paper unread at once — with the retry the header may arrive up to
  2 h later after an S454 question was asked; it resolves on the next read as any late fill does (named, not changed).
- **Charter: seen, not touched:** none new beyond the brief's own list.
- **Dependency state at install:** S585 live (`stationery.py 18268ff0`), S582 live (`batteries.py 775471e6`, `xray_costs.py 22e59f5a`), the
  Claude key present, `read.claude = on`, `read.claude_model = claude-sonnet-5-5`, `calls_today 0 / cap 400`.

### Undo
`\cp -p /root/assetapp/asset_register.py.bak_S601_c39c084e /root/assetapp/asset_register.py && \cp -p /root/assetapp/claude_reread.py.bak_S601_d9b75e78 /root/assetapp/claude_reread.py && systemctl restart assetapp`
— then `/healthz` 200 and the files back at `c39c084e` / `d9b75e78`. The setting `read.sarvam = off` stays (the old file ignores it). The
database backup `assets.db.bak_S601_20261019_172831` is used only if the data change must be reversed — say so before using it.

### Publish and the clone
- **Published** by `PUBLISH_ALL.bat`: the gate `NO_PHONE_NUMBERS` clean over the 34 staged files (numbers and credentials); commit
  `4744a858110e7dbac1bfdbbe1e686158a95e180d` "publish: pending kits and files (PUBLISH_ALL)"; origin HEAD verified = local. (This
  section's lines are a second, small publish of the report alone.)
- **The clone** `/root/deploy/repo` pulled fast-forward to `4744a858` at 17:36:14 IST; `md5sum -c SUMS.md5` in the clone's kit folder: 0
  failures; `diff -rq` clone kit vs `/tmp/s601kit/…` (the copy that installed): identical; the live files read back again `f29ee515…` /
  `ed7023d2…`; healthz 200. No `__pycache__` in the clone's kit.
- **`/tmp` on the box cleaned:** `/tmp/s601kit`, `/tmp/s601kit.tar`, `/tmp/s601probe`, `/tmp/s601probe1.sh`, `/tmp/s601reh` and the six
  `/tmp/s601_install_*` scratch folders of the rehearsal removed; `ls -d /tmp/s601*` empty.
- **The build lock is NOT released — one line for the chat (or the owner):** the lock `/root/deploy/.claude_code_build.lock` (owner line
  `S601_PHARMACY_BILLS_READ_BY_CLAUDE 2026-10-19 17:28:32`) must be removed now that this report is written, but `rm -rf
  /root/deploy/.claude_code_build.lock` over ssh was refused by the permission list here (an `rm -rf` under /root), and the rulebook says
  not to try another spelling. Until it is removed, the next kit's installer on this server refuses with "another build holds the lock".
  The line, on the box:
  ```bash
  rm -rf /root/deploy/.claude_code_build.lock
  ```
  (CLAUDE.md allows deleting a lock older than 3 hours whose owner's report shows it finished — this report does.)
- **The memory note** for Claude Code's own PC-side gotchas was refused too (the memory folder is denied) — nothing of the kit depends on it.
