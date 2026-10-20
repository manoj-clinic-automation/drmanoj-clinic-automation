# REPORT S604_PAY_SHEET_FIXES — 20-Oct-2026

## For the owner

1. **The payment page now asks for the month-end reports and confirms them.** At the top of September's vendor-payment page:
   *Supplier-wise statement — Received 11-Oct 10:32 · 01–30 Sep · 86 bills · its total ₹4,31,016 agrees with the sheet*;
   *Bill-wise statement — Received 11-Oct 10:32 · 86 bills*; *Item lines — Received 20-Oct 10:01 · 01–30 Sep*. A refused report shows
   as one plain line. A missing report says exactly which Marg report to export as a TEXT file, with its FROM / TO dates.
2. **This morning's report with the L.K. returns:** **accepted.** The medical PC took the new reader at 09:53, offered this morning's refused report again by itself, and the server received it at **10:01** (193 item lines). September's item lines now add up to ₹4,31,016 — Marg's own total.
3. **Bass Pharma's bill 14538 is counted once.** September now adds up to ₹4,31,016 — Marg's own total — and the cheque lane owes ₹1,597,
   not ₹3,194. Nothing was deleted; the bank file did not change.
4. **The lock now asks for the three reports and an agreeing cross-check.** **September is ready to lock now** — the card shows the green line *"All three reports are in and agree — the month can be locked."* You lock it yourself. April, May and June
   (never locked) now wait for their supplier-wise statements; July is ready as before. No month was locked by this build.
5. **The two boxes:** "Carried in" takes a minus on a phone; a figure that cannot be read is refused with a message (never saved blank); after a
   save the row says *Saved 20-Oct hh:mm by manoj — payable now ₹…*; a note is never wiped. Agarwal's line is untouched (−400 / 400).

---

## For the chat

### Pins, read back on the box and on Drive

| file | FROM (read at the open) | TO (read back) |
|---|---|---|
| `/root/finance/purchase_app.py` | `60f2d846155659c4eddc33e4a0d42b39` | `447b745f16c81ef62d389900d1d8ae13` (md5sum after placing, `[12/12]`) |
| Drive `H:\My Drive\Clinic Data Archive\ToMedical\_kit\marg_txt.py` | `a59a222faf32a72ccc19c8635955cf8d` | `e8a60d9df79ed9fb763e2be4c4f23d4f` (placed 09:52:14, read back) |
| Drive `…\_kit\KIT_MANIFEST.txt` | `0bf248e43381bd27f6d011648b8405ee` | `ddd0eadb169f9f1a78c7befa5a550aaa` (placed 09:52:14, read back; only the reader's md5 changed, CRLF kept) |
| Drive `…\_kit\marg_watch.py` (read only) | `39fa27739757ff8e9c8731f77d07b40b` | unchanged (read after the placing) |

Read-only md5s at the open, all exact (installer `[2/12]`): amir_day 1169a3d6, stock_app 40f2c922, stock_watch f0d9092a, amir_salts fc5c1d16,
marg_purchase_rows 41d68148, supplier_msg 6366ed0f, packs e46264b8, bank_sms aa527840, export_watch f6845ec5, reports_tile 535b5790, marg_door
dc5c1e36. Proved unmoved after placing: finance_app.py, portal.py, tile_grants.json, the crontab (84 lines), spine.db's and finance.db's schemas
(`[11/12]`). The spine was green at the open (13/13, last success 09:40:51).

Drive backups beside the files, read back: `marg_txt_S546.py.superseded` a59a222f, `KIT_MANIFEST_S546.txt.superseded` 0bf248e4.
Server backups: `/root/finance/purchase_app.py.bak_S604_60f2d846`, `/root/finance/finance.db.bak_S604_20261020_094936` (backup API, 41,164,800 bytes).
Service restarted: `clinic-finance` only, once, at **2026-10-20 09:51:30** (the box's clock); healthz 200; pay/hub/month/amir/reports-aaj 302
without a login (the login gate, expected); journal clean. DOCTOR_AUTO_OFF written before and removed after.

### The data step (§3.3), on the live database
`DATA S604: DONE -- audit twin_merge 542<-579 written` (audit id 1114, 2026-10-20T09:51:30). Bill 542 now carries `sw_md5 5307d3e5…,
sw_amount_p 159700`; bill 579 `sw_md5 NULL, sw_amount_p NULL, reason 'twin of bill 542 (supplier-wise clipped the name; S604)'`, kept, not
effective. Undo: `python3 -B data_s604.py --db /root/finance/finance.db --undo` (from the audit JSON) — not used.

### The archived XLS (§3.3) — the overflow IS the cause
`D:\Downloads\margsync\MargArchive\PURCHASE_SUPPLIERWISE\2026-09\PURCHASE_SUPPLIERWISE_DEFAULT__2026-09-01_to_2026-09-30__20261011-102927__5307d3e5.XLS`,
row 11: `'BASS PHARMA DISTRIBUTORS PVT' | 'LTD29-09-2026' | 14538.0 | '-' | 1597.0`. The 32-letter name ran into the DATE cell and
`marg_purchase_rows.iso_date`'s overflow rule (`^[A-Z]{0,8}(\d{2}[-/]\d{2}[-/]\d{4})$`) dropped "LTD". The rule is named, not changed; the next
case on the store is bill 581, A015712 (15-Oct, LTD, bill-wise only) — the new join rule will take October's supplier-wise copy onto it.

### The walk (server), the negative control, and S603's walk
Installer `[6/12]`: **`WALK OK S604: 77 checks, 42 controls green on the new file`**; **`WALK OK negative control S604: 42 controls red on the old
file`** (every `C:` control red on 60f2d846). The same walk result in the DRY run started 09:42:37 (the box's clock) and in the install run
(scratch `s604_inst_20261020_094936`).
S603's walk, whole, on the NEW and the OLD file: **79 check lines identical on both sides**, 4 FAIL lines on both — see "Outside the brief".

Controls, verbatim from the walk on the new file:

**§4.1 (server side)** — `ok (1) the kit's reader takes this morning's text, L.K.'s block (line 177) 'returns inside'` (279 rows, sheet md5
15b9d64a; payload 193 rows, 2026-09-01..30, pushed through `/api/push`: stored, new).

**§4.2 returns counted**
- `ok C: (2) 2026-04 item-wise is R1's figure 38217400` · `ok C: (2) 2026-05 … 36804635` · `ok C: (2) 2026-07 … 47639296`
- `ok C: (2) September item-wise = 43,101,647 paise (Marg's GRAND TOTAL)` · `ok C: (2) September's returns bucket is empty`
- `ok C: (2) signed = the three L.K. bills with Marg's minus sign` ([573, 574, 577])
- `ok C: (2) each L.K. return reads 'a purchase return ... counted as a return' on the sheet, and no 'needs correcting'`
- `ok C: (2) 2026-04 / 2026-05 / 2026-07: no return is flagged 'may be an entry that needs correcting'`
- `ok C: (2) September's month page: the L.K. returns read 'agrees' with the return words`
- item-wise OLD → NEW where it moved: April 39089756 → 38217400, May 37212433 → 36804635, July 47739566 → 47639296; August (FINAL) untouched.

**§4.3 the twin**
- `ok C: (3a) no new row; bill 542 gains the supplier-wise md5; one twin_joined audit row naming both keys`
- `ok C: (3b) a second supplier-wise push of the clipped name after the join: still one row, the real bill takes the new md5`
- `ok C: (3c) a supplier-wise push after the data step: 579 stays not effective, 542 takes the md5`
- `ok (3d) MANNAT / DEEPAM 502 (18-Aug, both Rs 10,641): a supplier-wise push of both stays two rows, no join`
- `ok (3e) a clipped name with a different amount stays two rows (a new row, no join)`
- `ok (3f) the data step: September 86 bills, Rs 4,31,016, the cross-check agrees, the cheque lane owes Rs 1,597 (was Rs 3,194); the NEFT lane unmoved`
  (before: 87 bills, ₹4,32,613, Bass cheque 319400; after: 86, 43101600, verify True, 159700; NEFT 42901900 → 42901900)
- `ok (3f) run twice: nothing changes, one twin_merge audit row`

**§4.4 the card**
- `ok C: (4) the quiet copy: the card is at the top of September's page`
- `ok C: (4) supplier-wise received 11-Oct 10:32, 01-30 Sep, 86 bills, its total Rs 4,31,016 against the sheet`
- `ok C: (4) bill-wise received 11-Oct 10:32, 01-30 Sep, 86 bills`
- `ok C: (4) item lines received, with 7 bills missing and the export to make`
- `ok C: (4) this morning's refusal (08:06, line 177) is shown once under the card`
- `ok C: (4) after the push of this morning's lines: 1 bill still missing (Bass's twin 14538)`
- `ok C: (4) the refusal line is gone once a covering item report arrived after it`
- `ok C: (4)(5) with the push and the data step: the green line, and the lock gate open`
- `ok C: (4) with 5307d3e5 removed: 'Not yet -- export from Marg as a TEXT file: SUPPLIER WISE PURCHASE STATEMENT, FROM 01-09-2026 TO 30-09-2026'`
- `ok C: (4) a supplier-wise statement ending on the 28th: 'Not yet' on the card and the cross-check says 'No supplier-wise ...' (the old -28 rule took it)`
- `ok C: (4) a reader-stop refusal received after 30-Sep and after the covering exports: one plain line under the card` · `ok C: (4) gone once a covering item report is received after it`
- `ok (4) another refusal reason: 'The medical PC refused a purchase report at hh:mm: <its first clause>.'`
- `ok (4) staff-eye: Shavez, opening the payment page, sees the same English card` · `ok (4) staff-eye: the owner's and Shavez's portal homes render`

**§4.5 the lock**
- `ok C: (5) _month_summary, _pay_rows, _advice_rows_s265, _verify_statement and the gate return on every month April-October (no recursion)`
- `ok (5) every money reader equal OLD vs NEW on every month April-October: Marg total, bills, every vendor's payable and lane, the advice lines`
- `ok C: (5) with 5307d3e5 removed the gate is closed with the supplier-wise reason` · `ok C: (5) ... and the month page shows no FINALISE button, the reason listed`
- `ok C: (5) api/finalise refuses September while the supplier-wise statement is missing (409, the reason named)` (OLD: 200 final — red)

**§4.6 the boxes**
- `ok C: (6) carry_fwd '−400' (U+2212) is stored -40000, payable 0 in the reply, the vendor absent from the advice`
- `ok C: (6) '4OO' answers 400 malformed with words, the row unchanged`
- `ok C: (6) carry_fwd '–400' is read as -40000` · `'-400/-' is read as -40000` · `'400/-' is read as 40000`
- `ok C: (6) a stored note, then a post without the note key: the note is kept`
- `ok C: (6) the sheet: no inputmode="numeric" on any Carried-in box; Paid keeps its keypad`
- `ok C: (6) the sheet: 'Saved dd-Mon hh:mm by manoj -- payable now Rs 0' under Agarwal, and the note under the vendor that has one`
- `ok C: (6) the page's script shows 'Saved -- payable now' beside the box before the reload`
- `ok (6) Paid typed moves no payable, advice line, NEFT portion, cheque register line`

**§4.7 nothing else moved** — `ok every page dump (the pay pages of Aug/Sep/Oct minus the card, the saved rows and the cf_ keypad; Aug's month
page; Sep's letter; the packs; the cheque registers; Amir's day; Shavez's reports and pay page) is byte-equal to the OLD file's (0 differ)`;
the hub's August, September and October rows byte-equal; May, June and July's rows change only as §3.2/§3.5 say. `ok C: (7)` one gate, one
arrival reader, the note rule; healthz 200.

### The medical-PC half (§3.1)
`proof_s604_reader.py` on manojz before delivery — **`PROOF OK S604 READER: 0 failure(s)`**:
- `ok 1 --selftest: SELFTEST OK, every S604 check OK (10)` — made-up blocks shaped as L.K. and KEDAR: returns inside taken; the same bytes every
  time; the returns TOTAL ±0.02 refused; another TOTAL −100 refused; +0.02 taken; an unexplained excess refused; a 41-line block refused without
  hanging (the whole selftest 0.1 s); a non-positive line refused; a GRAND TOTAL off the printed TOTALs refused.
- This morning's two texts (08:05:56 cbdca80d, 08:06:12 405e52bb): `taken by S604, L.K.'s block (line 177) 'returns inside'`; `refused by S546 at
  line 177 (the negative control)` — S546: *"line 177: a supplier's TOTAL (9728.09) is not the sum of its lines (17695.21)"*.
- The real text altered: `L.K.'s TOTAL (line 177) +0.02 / -0.02: refused by S604`; `KEDAR's TOTAL -100: refused by both readers at its own
  TOTAL line 161`; `KEDAR's TOTAL +0.02: accepted by both (S546 goes on to its own refusal at line 177; S604 takes the text)`; L.K.'s TOTAL −37.11 refused.
- Every kept text (`_captured_txt` and `_captured_txt\refused`): **216 texts — 124 the same bytes, 90 refused by both with the same words, 2 newly
  taken (this morning's two)**, 0 different, 0 lost.

**The delivery and the bounded wait** (read every 60 s from 09:52:14; clocks as printed):
- Heartbeat `FromMedical\heartbeat.json`, `written_at 2026-10-20T09:53:03`: `marg_txt.py {"in_kit": true, "kit_md5": "e8a60d9df79ed9fb763e2be4c4f23d4f",
  "installed_md5": "e8a60d9df79ed9fb763e2be4c4f23d4f", "matches": true}` — the agent installed it; no refusal by the agent.
- Watcher log `FromMedical\marg_watch_log.txt` (copied to Drive at the 10:19 census): `2026-10-20 09:53:17  reader changed (marg_txt e8a60d9d):
  3 text(s) refused in the last 3 days offered again, 1 taken` (the two SUPPLIER/ITEM WISE copies give the same sheet — one taken, the other
  "already taken"; the third is the 09:28 'SANJEEVNI MEDICOS' text, not a report the reader knows).
- Server `purchase_export`: `ITEMWISE 2026-09-01 2026-09-30 20261020-095317 2026-10-20T10:01:16 193 46328016 live 15b9d64a` — the same sheet md5
  the walk produced from the text.
- Census `FromMedical\marg_text_census.txt` (`2026-10-20 10:19:28`): **not seen as TAKEN** — it still lists `C:\Users\Public\MARG\17476\report.txt`
  and `user_aa1773209943.txt` as `NOT TAKEN: the reader refused it: line 177`. Reason (S556 `marg_watch.py` 961–1008): the re-offer takes the
  kept copy in `_captured_txt\refused` and clears only its verdict; the census reports the source path's cached verdict, which nothing resets.
  The log and the server row prove the take. I stopped the wait at 10:21 instead of 10:52 since the census line cannot change by the code;
  left placed — not red. (A finding for the chat: the census misreports a text taken at a reader change.)
- The card on the live page after it (state read at 10:08:40 on a fresh copy of the live database):
  *Item lines — Received 20-Oct 10:01 · 01–30 Sep* · *All three reports are in and agree — the month can be locked.*

### The lock gate, April–October, on the live data (installer `[7/12]` before, `[11/12]` after)
| month | before (OLD, 09:51:28) | after (NEW, live, 09:51:35) |
|---|---|---|
| April | open | closed — the supplier-wise statement for 01–30 Apr has not reached the server |
| May | open | closed — the supplier-wise statement for 01–31 May has not reached the server |
| June | open | closed — the supplier-wise statement for 01–30 Jun has not reached the server |
| July | open | **open** |
| August | FINAL | FINAL (not asked, untouched) |
| September | closed (7 bills no lines) | closed at 09:51:35 (6 bills no item lines); **OPEN at 10:08:40** after this morning's report landed (state read on a fresh copy: 86 bills, Marg 43101600, item-wise 43101647, signed [573, 574, 577]) |
| October | closed | closed (a Wrong bill, 4 bills no lines, and the three month-end reports not yet — the month is not over) |

### What I did NOT do, and why
- **No month was locked** (the brief: the owner locks September himself).
- **S603's walk is not green on the NEW file** — nor on the untouched live files: on today's copy it fails the same 4 checks on both sides
  ("(4 i)", "(4 ii)", "(4 iv)", "(4 v)" — the live copy carries real open visit days 16-, 17- and 18-Oct whose real "never reached the server" /
  "re-export owed" lines sit beside its synthetic ones). The brief asks for it "on NEW green"; I gated instead on its 79 check lines being
  **identical OLD vs NEW** (S603's own way with S598's walk), which proves this kit moves nothing S603 sees. The installer says so in `[6/12]`.
- The reader's selftest uses made-up blocks shaped as L.K. and KEDAR (a real report's lines are not embedded in the medical PC's file); the real
  L.K./KEDAR controls ran in `proof_s604_reader.py` on the real text.
- The manifest got only the reader's new md5 (the brief: "nothing else changed") — no S604 comment line was added there (S546 had added three).
- The cost of the run: the runner's log `D:\Downloads\_kbtools\agent_build\logs\S604_PAY_SHEET_FIXES_20261020_0922.log` was 0 bytes when read at
  the open; the run's own cost line is the runner's to write — I cannot read it from inside the session.

### Calls I made (the brief left them open)
- The pay sheet's text for a signed bill is kept as the row's *flag* (as the old return flag was), so the "flagged" count does not move; its
  words are the brief's, with no "needs correcting". The month page's chip reads *"agrees — a purchase return — Marg prints its lines as a purchase;
  counted as a return"* (R1: the chip becomes "agrees"; the brief: the return words) — both.
- The refusal line shows *hh:mm* as the brief writes it, and adds *"on dd-Mon"* only when the refusal is not from today.
- When a month is not over yet the card adds one line: *"The month is not over yet — export these after <last day>."*
- `_lock_gate`'s item-lines reason reads *"the item lines for 01–31 Oct have not reached the server"*.
- The saved line under a vendor reads *"Saved 20-Oct 09:50 by manoj — payable now ₹0"* (with the day, since a line can be days old).
- An unreadable figure answers *"That figure could not be read: Carried in “4OO”. Type a number such as 400 or -400; nothing was saved."*
- The data step refuses (and the installer would have restored) unless 542/579 are exactly the rows the brief read; it is skipped when the audit
  row exists and has not been undone.

### Outside the brief, noticed
- **S603's walk is data-dependent** (above): its scenarios (4 i/ii/iv/v) assume no real open visit day carries an export-wait line. It is red on
  the live files as they stand today, independent of S604. A fix is the chat's (a new kit number).
- **Amir's real export-wait lines are live today** in the owner's Needs-you: "Amir's purchase export of 17-10 never reached the server …" and
  "Amir entered a bill at 09:35 on 18-10 after that day's export … re-export owed" (read from the walk's output on today's copy).
- The hub's months list shows only the six newest months, so April's changed figure is visible on its own month page, not the hub.
- `/finance/amir` answered 303 for amir in the walk's header session (the S603 page redirects) — unchanged OLD vs NEW.

### Duty map
No staff duty is added, moved or removed (the card is on the owner's page; Shavez sees it only if he opens it). `DUTY_MAP.md` / `.json`
unchanged; the walk rendered the owner's and Shavez's portal homes (200) and the pay page as Shavez (200, the card seen).

### Lock, publish
- `NO_PHONE_NUMBERS.py` clean over the 11 kit files and over this report and the brief.
- `PUBLISH_ALL.bat`: **PUBLISHED AND VERIFIED - origin HEAD = aaada6a** (the kit and the brief); this report followed in a second publish.
- The server clone `/root/deploy/repo` pulled to aaada6a: 10 of the kit's 11 files are byte-identical to the copy the installer ran from
  (`/tmp/s604kit`), `md5sum -c SUMS.md5` OK for them. **`KIT_MANIFEST.txt` differs by its line endings only**: the repository's
  `.gitattributes` (`* text=auto`) stores the CRLF manifest as LF — S546's kit shows the same `FAILED` on its manifest in the clone. The
  manifest is the Drive file (delivered from the CRLF working copy, ddd0eadb on Drive); the server installer never reads it, but run from the
  clone its SUMS gate would refuse. A `.gitattributes` line (`KIT_MANIFEST.txt -text`) is the repository's, outside this brief — for the chat.
- The build lock `/root/deploy/.claude_code_build.lock` (taken by the installer at 09:49) released after this report with the two commands
  of CLAUDE.md (`rm -f …/owner; rmdir …`).
