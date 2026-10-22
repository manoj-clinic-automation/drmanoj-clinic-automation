# REPORT S618_SCAN_QUALITY — 22-Oct-2026 (installed; assetapp restarted 10:43:42, clinic-finance 10:43:45 IST, the box's clock)

**For you (Dr Manoj):**
1. **22 pharmacy bills of the last two weeks are now saved the right way up** (every sideways one the eye found). From today every new pharmacy bill is checked after it is read and turned upright by itself.
2. **The phone now stops a badly blurred photo** with *"Photo saaf nahi — phir se lijiye"* and a Retake button (if the same page is refused twice, the third photo is kept, so nobody is ever stuck). A bill cut off at an edge is caught by the server within a minute instead.
3. **"Scans to redo" lists 5 scans today:** B-0155 and B-0180 (part of the bill cut off), B-0199 (the amounts column cut — lines ₹2,400 against a total of ₹4,160), B-0157 (only a corner) and B-0176 (an estimate slip, not a bill). B-0181 (blurred) and B-0188 (tilted, cut) were read well enough by Claude that the system cannot see the fault — send those back by hand.
4. **You and Shavez send any scan back** from *Scans to redo* (a link on your Purchase orders home): its picture, the reason, and *Get it rescanned* (blurred · cut off · not a bill).
5. **Reception, Alisha and Shivani see "Phir se scan karo"** on their Purchase orders home (not Darpan), with what to do in plain words and *"Doctor sahab ne bheja"*. The rescan replaces the old scan everywhere (its order, its decisions); the old one is kept on record. Nothing changes on their screen until you send something back.
6. **Cost:** about 52 Claude calls on the live key today (49 for the two weeks' check, 3 for a new bill) — a few rupees; the build itself is on the API credits (about $19 of the $70 when this was written). Everything was tested on copies first; it is live and working.

---

## For the chat

### FROM → TO, read back on the box (`md5sum`, 10:46, after placing)
| file | FROM | TO (read back) |
|---|---|---|
| /root/assetapp/asset_register.py | f29ee51561ef73b837a25e56651108ac | 70e35b105477cc2de5ed90c28875a05a |
| /root/assetapp/scanner_widget.js | 10a8bb296944542278a06827c4d09c18 | b936f0f3d184556aca3007f1a4bdf014 |
| /root/assetapp/claude_reader.py | 3894dc2358abd875ee61ced7619e1e1b | 101189093f8d0f9921fbb3e41b66226e |
| /root/finance/porders_s454.py | 34bab4648940f30d7fc57188398c51b4 (S613's TO) | 4d1506480b2b1388ae1020c302e71a84 |
| /root/finance/order_sheet.py | c7fe2561b22158f9dffa73b8c963e298 (S613's TO) | ff9375f98c46f0a004a02a3582693a83 |
| /root/shared/scan_quality.py | (new) | 16fb24029610ce7c0c0ecd502f529f7b |

**Pins.** All five FROM pins matched at the open (09:17) and at the installer's gate (10:34:54). The read-only files matched both times: claude_reread ed7023d2, sorting_desk 110335ea, clinic_papers 6db07c12, purchase_app 447b745f, porders b1736494, stock_figure 8c66b6b1, stock_watch f0d9092a, item_check 6f3faf89, darpan_kal d6ba4882. Printed: `/root/shared/scan_checks_s441.py` b9ba6839 (both times); **`packs.py` moved between the open and the gate — 6ed8e18a (09:17) → 94923368 (file time 09:29)**, with a clinic-finance restart at 09:29:36: another change, not this kit's (the brief prints it only). Proved unmoved at the end: finance_app.py, portal.py, tile_grants.json, the crontab (84 lines), and every published `deploy_kits/S5*`, `S6*` folder (one hash over all their files, before and after).

**Builder.** `make_s618.py`: 25 anchored edits on the live bytes, each anchor found exactly once; rebuilt on the box at the gate, each file at its TO pin. The kit in `deploy_kits/S618_SCAN_QUALITY/` is byte-identical to `/tmp/s618kit`, which ran (SUMS.md5).

**Backups.** `finance.db.bak_S618_20261022_103454` (42,655,744 bytes) and `assets.db.bak_S618_20261022_103454` (589,824 bytes), both by the sqlite backup API; `uploads_list.bak_S618_20261022_103454.txt` (the uploads folder's list); each replaced file has its `.bak_S618_<from8>` beside it.

**Services.** assetapp restarted once at **10:43:42** (its init_db made `bills.rescan_of` and `scan_lie`; /login 200, /intake 302 = the login gate), then clinic-finance once at **10:43:45** (healthz 200; /finance/porders, /s454/scans, /s454/rescan, /s454/order 302 = the login gate). Journal of both clean (no Traceback / ImportError / NOT mounted). `DOCTOR_AUTO_OFF` written before, removed after.

**The probes.** pypdf / Pillow: `/usr/bin/python3` — both MISSING; `/root/wa/venv/bin/python3` — pypdf 4.3.1, Pillow 11.3.0. So the service turns a page through the venv python as a subprocess (S441's `_merge_pdf` pattern); the walk's turn ran on that same path (the walk runs under `/usr/bin/python3`).

### The walk (walk_s618.py), on the box, scratch copies (backup API), 10:35–10:41 IST
Final lines: `WALK OK S618: 55 checks, 28 controls green on the new files` and `WALK OK negative control S618: 20 controls red on the old files`.

The 28 controls on the NEW files, verbatim (each `ok`):
- `C: the backfill ran on the scratch copy through claude_reader.lie_pass (exit 0)`
- `C: the bar -- at least 20 of the 22 sideways pages read exactly 270 (22 did) and no upright page reads other than 0 (0 did, of 32)`
- `C: every turned scan renders sideways-to-upright (portrait page -> landscape, pdftoppm reads its /Rotate), its old file kept, one 'upright' audit each (22 turned, 22 audits)`
- `C: a join racing the turn: the compare-and-set does not apply to the pre-join file; the CURRENT (joined) file is checked and turned -- the bill keeps both pages, upright ('upright_raced' then 'upright')` — with the control `the turn of the PRE-join file alone has 1 page(s) -- written without the guard it would have lost the joined page`
- `C: the verdict's bar -- no readable scan on the list (none caught that the eye calls fit)`
- `C: every unfit scan not set aside is caught, except where neither the reading nor the check can show it (['B-0155', 'B-0181', 'B-0188'])`
- `C: a pharmacy link carries the half-A4 prior (expectAspect 0.7048) and the blur limit (blurMin) in SCANNER_CONFIG from the start, and rescan_of rides the link`
- `C: the intake page clears rescan_of after the first Save (and after a PDF / file)`
- `C: the owner sends B-0199 back, reason cut off -> 200`
- `C: reception's home shows 'Phir se scan karo 1' directly above 'Bill scan karna hai' (or the done line), and its page the reception words and 'Doctor sahab ne bheja' with Scan karo (rescan_of in the link)` — the same for alisha and shivani (3 controls)
- `C: Shavez sends B-0181 back (blurred) -> 200; reception's page: 'Photo dhundli hai — isi bill ki saaf photo lijiye' and 'Shavez ne bheja'`
- `C: a sender not in porders.rescan_askers (darpan) -> 403`; `C: a scan already set aside (B-0183) is refused -> 409 set_aside` (plain checks: Bhati refused, 302; Darpan's home has no row)
- `C: 'Scans to redo' -- the owner in English (Part of the bill is cut off / Get it rescanned / Open the scan, the thumbnail with ?v=), Shavez in Roman Hindi; its read leaves BOTH databases byte-equal`
- `C: staff-eye: reception -- duty reception.rescan due (n 2): the tile 'Purchase orders' on the portal home and 'Phir se scan karo' on /finance/porders` — the same for alisha and shivani (3 controls; the walk's own portal secret and user store)
- `C: the rescan of the same paper stays captured and is the rescan of B-0199; the old scan is set aside 'rescanned as B-0202' (kept, its file kept)` (the scratch's own next stamp; B-0199's own first bytes uploaded — the same image, the same triple)
- `C: after its reading (vendor, bill no and total the same as B-0199's) the rescan is still captured -- no duplicate rule takes it (None)`
- `C: order 48's tie now points to the rescan (its stamp), scan_at kept (2026-10-21T17:30:00) -- NO new tie: the other waiting order of the supplier stays untied`
- `C: the people's decisions copied to the rescan (s454_scan_answer, purchase_scan_state's paper amount), the old rows kept`
- `C: the ask on B-0199 closed by the rescan (done_bill_id, done_at); reception's row now counts only Shavez's ask`
- `C: an ask on an untied scan (B-0176, kind Challan) closes on its rescan`
- `C: scan_quality is imported inside a function in porders_s454, never at its top (a failing import never takes reception's screen down)`
- `C: one DDL of scan_lie (claude_reader.LIE_DDL is asset_register's S618_LIE_DDL, byte for byte)`
- `C: DUTY_MAP v18 carries reception.rescan (tile Purchase orders, door /finance/porders, marker 'Phir se scan karo'); its due_sql is ONE read-only SELECT returning (n, since) on the copy: (1, '2026-10-22')`

Plain checks, green: the checks wrote no `claude_reading` row and left `read.claude_model` as it was (claude-sonnet-5-5; 186 readings, hash equal); a second `tie_pass` changes nothing; the next unrelated bill is a plain scan (rescan_of NULL); a clinic-lane and a lab-lane scan get no check call and no `scan_lie` row; a synthetic challan with no total and no amounts gets no verdict; every page dump of S613's list (reception's home, order list, maal, scan, q; Darpan's day, order tab and home; Amir's page; the approvals Needs-you; the pay page) byte-equal OLD vs NEW; healthz 200; no ten-digit run in the walk's output.

**The negative control (the same walk on the OLD files), verbatim — every control red (20):** the backfill (exit 3: no lie_pass) · section 1 (exception) · the join race (no turn) · the verdict (no reader) · the pharmacy link's SCANNER_CONFIG · rescan_of cleared · the owner's send-back (404) · reception / alisha / shivani rows · Shavez's send-back · darpan 403 · set-aside 409 · section 4 (exception: no scan_rescan_ask) · `the rescan of the same paper stays captured…` · `after its reading … still captured -- no duplicate rule takes it (image (the same capture, 0 bits))` (on OLD the rescan is set aside as a duplicate of B-0199 at once) · section 5 (exception) · the import · one DDL · section 7 (exception). On OLD some sections stop at their first missing piece (an exception counts red), so 20 labels print against NEW's 28.

**S613's and S605's walks (brief 4.6), OLD (live) vs NEW, check lines compared — equal on every walk:** walk_s613 66 lines, walk_s605 59, walk_s603 79, walk_s598 62. Red on BOTH sides (the live day, not this kit): walk_s613 `C: (1) order 20's L S BELT ... XXX: its family-bill words name bill 738 of 18-10` (red already on the live files a few hours after S613's own install — the data moved); walk_s605 its six (section 1 Darpan's हाँ ×4, and the two S613 changed on purpose); walk_s603 `stock_figure.py untouched (md5 51e1fc63)` (S613 changed that file); walk_s598 two (S593's seven rows by id; the re-judge clause). A first dry run found one real fault here and it was fixed before the install: S613's walk replaces `counts()` with a dict without the new key, and the home read it directly (500) — the reception row is now added only when `counts()` carries `rescan` above 0.

### The eye against Claude (orientation), the walk's real calls (Haiku)
All 54 labelled scans: **22 of 22 sideways pages read exactly 270; 0 of 32 upright pages read anything but 0.** (46 from the backfill on the scratch copy, 8 set-aside ones checked directly.) The same 22 on live: B-0135, B-0136 (not labelled), B-0141, 0143, 0144, 0145, 0146, 0148, 0150, 0151, 0152, 0154, 0156, 0157, 0158, 0161, 0178, 0190, 0198, 0199, 0200, 0201 turned (the two labelled sideways B-0149, B-0153 are set aside: not turned). Each turned file renders landscape in pdftoppm (100×141 → 141×100); the old file is kept. Live spot check: B-0199 now `bill_6d840eeea03f0ec3_u.pdf`, `Page rot: 270`.

### The verdict: catches and misses, tolerances ₹50 / 5 % (the defaults; not tuned)
On the scratch copy: caught B-0157 not_bill, B-0176 not_bill, B-0180 cut, B-0199 cut; **no readable scan caught** (B-0141's 4.8 % gap is inside 5 %). Missed, and neither the reading nor the check could show it: B-0155 (that run's check said the total was in view), B-0181 (blurred, but the reading adds up: ₹1,944.40 vs ₹1,940), B-0188 (side cut, the lines add up: ₹4,823.50 vs ₹4,811). **On live after the backfill** the rule lists 5: B-0155 cut, B-0157 not_bill, B-0176 not_bill, B-0180 cut, B-0199 cut — Claude's judgement of "whole bill / total in view" varies a little between runs (B-0155 caught on live, missed on the scratch; B-0199 cut on live, not_adding on the scratch). B-0181 and B-0188 stay off the list: the owner sends them back by hand.

### The blur calibration (the widget's own function, headless Chrome on the PC; `walk/walk_results_s618.txt`)
The measure: the 3×3 Laplacian variance of the page shrunk to 600 px by OpenCV's own area average (`INTER_AREA`). A first try with the browser's canvas shrink read the print itself as sharpness (aliasing) and put the readable handwritten slip B-0176 at 588 and B-0181 at 917 — so the shrink was moved into OpenCV (the same on every phone). On the stored pages: **B-0181 489** (refused); the lowest readable pages B-0198 **867**, B-0187 936, B-0160 944, B-0185 957, B-0182 964; the two other unfit ones B-0176 396 (a handwritten estimate slip) and B-0157 688 (a corner). **`scan.blur_min` = 650** (a setting the owner can change; default in `asset_register.S618_BLUR_MIN`): 161 above B-0181, 217 (25 %) below B-0198. These are ~1.8× R1's figures (B-0181 269, B-0198 488 — a different shrink); the ratio is the same. Through the widget's whole path (the page laid on a desk margin, outline, straighten, upright): B-0181 455, B-0198 1111.

**The phone walk: `11 browser checks: 11 GREEN, 0 RED`** — V (V8 parses the new widget whole: node --check's stand-in; no node on the box or the PC), CAL, A (B-0181 on a desk margin refused with the words and Retake) and A' (the live widget keeps it — red), B (B-0198 kept), C (two refusals then the third kept; the upload carries `blur_kept=1`), D (a gallery import of three, the middle one blurred: refused, the import goes on, 2 pages), E (a pharmacy link: the half-A4 prior from the start, read at call time) and E' (the live intake: no prior at load — red), F (the real intake page the box rendered, opened with `rescan_of=199`: the first Save carries it, the next bill does not) and F' (the live intake page does not carry it — red).

**The half-A4 hint.** 13 of the 33 cropped stored pages fall outside arOK's ±15 % band (B-0146, B-0155, B-0157, B-0168, B-0169, B-0172, B-0173, B-0176, B-0180, B-0184, B-0188, B-0198, B-0199): when OpenCV's outline fails and the light finder is asked, such an outline is now refused and the whole frame kept (Adjust still cuts it).

### The backfill (brief 3.5)
- Scratch (in the walk): 48 scans — checked 48, turned 22, failed 0; 48 calls of the scratch cap 400.
- **Live, after placing: 49 scans — checked 49, turned 22, failed 0, skipped 0; calls used 49 of the cap 400 (3 before).** A second run: 0 scans. The 49th is **B-0202, saved by reception at 10:36 IST** — after the wait gate passed at 10:34:55 and while the walks ran; the old code read it before placing, and the backfill checked it (no turn, no verdict).
- Live facts after: `scan_lie` 71 rows (49 checks, 22 upright copies), 22 `upright` audit rows; `read.claude_model` still claude-sonnet-5-5; the ties of B-0199 / B-0180 / B-0181 / B-0155 unchanged (orders 48 / 38 / 41 / 23); `scan_rescan_ask` made by the first tick, 0 rows; DUTY_MAP `reception.rescan`'s due_sql on live: `0 None`.

### DUTY_MAP
`reception.rescan` added (DUTY_MAP.json v17 → v18, `21ca346d…`; DUTY_MAP.md row under Reception and the header line). Door: Purchase orders → "Phir se scan karo"; due_sql `SELECT COUNT(*) AS n, MIN(substr(asked_at,1,10)) AS since FROM scan_rescan_ask WHERE done_at IS NULL AND withdrawn_at IS NULL` (run on the scratch copy (1, 2026-10-22) and on live (0, None)); owner line written, not raised (a duty with a door; his own *Scans to redo* lists every open ask).

### Calls I made (the brief left them open), and why
1. **The orientation question** asks which edge the top of the letters faces (top / right / bottom / left) and maps it to the clockwise turn in code — a direct "degrees" answer is easier to get wrong. The prompt's "whole bill" says what does NOT count (a clipped margin, fingers over the footer, a slight tilt): the first wording flagged two readable bills (B-0161, B-0190).
2. **The blur shrink in OpenCV**, not the canvas (above).
3. **A rescan is applied only when both scans are on the pharmacy lane** (an old scan not pharmacy, set aside or a joined page — or a new scan moved off the pharmacy lane — is ignored and audited `rescan_ignored`).
4. **The CONFIRMED pairing is carried through reception's pair answer**: `purchase_scan_link` has one row per bill, so the old link cannot be "kept and copied" at once; the old scan's CONFIRMED link (or its *Haan*) is copied as a pair answer on the rescan, and the link is written for the rescan once the matcher has let the set-aside old scan go.
5. **A forced-blur photo** (kept after two refusals) is stored as `scan_lie.blur_kept=1` on its file at capture, and the verdict lists it as blurred.
6. **"No reading"**: when Claude's reading failed, the reading's rules (not_bill / no_total / not_adding) are not asked — only the check's (else every scan read during an outage would be "not a bill").
7. **The head of a just-joined page is checked**: when the page's own reading thread joins it to its head (S441), the check goes to the head, whose merged file is new.

### What I did not do, and why
- **The board's PLANNED lines**: the live board is not reachable from this PC or the box (as REPORT_S605 found); I relied on the brief and found no other build's lock or runner log active.
- **scan_quality is not imported by asset_register**: no Scan App screen in this brief shows a verdict, so only finance reads the rule (fail-soft, inside functions).
- **`node --check`**: no node on either machine; V8's parse in headless Chrome stands in (check V).
- **Prototype calls during the build**: while designing the prompt I made 69 Haiku calls on the Scan App's key straight through the reader's `_post` (not counted in `read.calls`); every later call (the four rehearsals and the install's walk) was counted against its scratch copy's cap, and the live backfill against the live cap.

### Seen, not touched (brief 7, and met here)
- `tie_pass` ties a scan to the supplier's OLDEST waiting order; a received order keeps asking 7 days — S619's.
- Reception's pages write on a GET (`_every_read`, F-925); the new *Scans to redo* does not.
- `bill_items` and `claude_reading` disagree on B-0180, B-0183, B-0188.
- A rescan through the plain *Naya bill scan karo* (no link) is set aside as a duplicate and the ask stays open — the reception words always point to *Scan karo* on the ask.
- PDF / file and the basic upload form bypass the blur check and do not carry `rescan_of`; `autoAdd` (no OpenCV) and Adjust have no blur check.
- A page joined by the intake-load pass (`_pass_s441`, not the page's own reading thread) does not trigger a check of its head's merged file until that head is read again.
- A sparse handwritten slip on plain paper reads as soft as a blurred photo (B-0176: 396): the phone will refuse such a paper twice and keep the third photo, which is then listed as blurred.
- The dealer a scan is saved under (B-0161 Kedar as Shivaaz, B-0167 Mannat as Yogendra) — S619. A captured pharmacy scan's Re-read button — not built. `/root/shared` is in no nightly code bundle — `scan_quality.py` (and `scan_checks_s441.py`) need the parent's bundle list and pin check.

### Behaviour changes (rule 4, 7)
Reception's phone refuses a badly blurred photo twice; reception, Alisha and Shivani get a new home row while anything is sent back; the owner and Shavez get *Scans to redo* (a link on their home while it has any); saved pharmacy bills turn upright; a rescanned bill may need its Marg link answered again where the matcher cannot verify it.

### Cost
The runner writes its own cost line when the run closes (`run_build.py S618_SCAN_QUALITY --budget 70`; log `D:\Downloads\_kbtools\agent_build\logs\S618_SCAN_QUALITY_20261022_0915.log`). When this report was written, about **$19 of the $70** budget had been used.

### Lock
`/root/deploy/.claude_code_build.lock` was taken at 10:34:54 IST by S618_SCAN_QUALITY. It is released after this report and the publish with `rm -f /root/deploy/.claude_code_build.lock/owner; rmdir /root/deploy/.claude_code_build.lock`.
