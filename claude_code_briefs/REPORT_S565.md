# REPORT S565_DARPAN_SMS_AND_CLAUDE_BILLS — Darpan's day draws the bank's SMS; Claude vs Sarvam on the medicine bills

**Part A is installed and working.** When the bank's morning SMS stands in for the MPR mail, Darpan's *Kal ka hisaab* now says *"बैंक SMS 07:02 से — bank की report बाकी"*. Your view of the same day says *"provisional — bank SMS 07:02, MPR not in"* (or *"MPR never received"*). A day Darpan has already posted is worked again when the SMS arrives. Your switch on the bank-SMS page is still **OFF**, so today his page looks exactly as before until you switch it on.

**Part B (a sample; nothing was changed).** I compared 102 medicine bills, all of them already read by both Sarvam and Claude, against Marg using the same rules for both:
- **Better:** Claude got more bills fully right (11 against Sarvam's 5), more totals right (94 against 91) and dates about level (78 against 77). It made far fewer quantity mistakes (8 against 32) and expiry mistakes (15 against 37).
- **Worse:** Claude did less well on the supplier (78 against 87) and the bill number (78 against 88). Part of that is because the bill-to-Marg matches were built from Sarvam's own readings. Also, on 16 bills Claude read a different number printed on the paper.
- **Still weak for both:** batch numbers are wrong on about half the item lines, and most item lines still have some fault (183 of 231 for Claude).
- **Cost:** a fresh Claude reading costs about **1.7 US cents per bill** (5 bills read today for $0.09 in total).

---

## For the chat — the proof

**Times (IST, read from the box):** brief pins read 16:54:36 · build lock taken 17:12 (before the rehearsal, whose first backup stamp is 17:12:53) · install 17:13:52 → 17:14:17 · `clinic-finance` restarted 17:14:11 · read-back 17:14:33 · part B 17:14:44 → 17:15.
Installed from `/tmp/s565kit`. After publishing, `/root/deploy/repo/deploy_kits/S565_DARPAN_SMS_AND_CLAUDE_BILLS` was pulled (459247f): `md5sum -c` passed 7 of 7, and `diff -r` against `/tmp/s565kit` was empty.

### Pins FROM → TO (md5 read back on the box after placing)
| file | FROM (brief = live) | TO (read back) | counted edits |
|---|---|---|---|
| `/root/finance/darpan_kal.html` | `f5e279eb26e7f24827f29b79f95b2769` | `75d5a5b51b017abd5ad3aa408609a1ff` | 4 |
| `/root/finance/darpan_kal.py` | `a8e11c31b9c80c1b01e63e948418d4a4` | `8128598f745fca48a08472905f47da97` | 1 |

**Read-only files at install:**
- `bank_standin.py` `fd635862` = the brief.
- `bank_sms.py` **`aa5278403ec85c898d808486e4c3cde3`**, not the brief's `053d4ccb`. S564 (16:45 today) moved it, its owner-only key fold, which is that kit's TO pin. Part A only reads the SMS table's definition from it. I pinned the live md5 in the installer and carried on.
- `purchase_app.py` `147201dd288d291323023a764df3411e` (md5 read at the open).
- `item_check.py` `6f3faf89`.
- `claude_reader.py` `3894dc23` = the brief. S563 had not moved it. `read(path, bid=None, db_path=None)` and `to_bill(data)` were checked by signature.

**The edits:**
- html (1): the `smsAt` helper, once.
- html (2): Darpan's row, with the `"sms"` case first.
- html (3): the owner's note in `ownerPos`, with `bank\'s` escaped.
- html (4): the owner's row, with `"sms"` first: `', MPR never received'` when `c.standin.never`, else `', MPR not in'`.
- The `"pos"` and Marg branches are byte for byte.
- py: `_refresh_if_needed`'s third condition, `== "pos"` → `in ("pos", "sms")`, with an S565 comment. Nothing else changed.

**Backups:** `/root/finance/finance.db.bak_S565_20261015_171352` (backup API, 0600), `darpan_kal.html.bak_S565_f5e279eb`, `darpan_kal.py.bak_S565_a8e11c31`.

**Restarted:** `clinic-finance` only, once.
- After the restart: `clinic-finance` and `clinic-portal` both active.
- `/finance/healthz` 200, locally and publicly (`https://followup.dr-manoj.in/finance/healthz`).
- `/finance/darpan/kal` 302 without a login: the login gate, which is expected.
- Journal clean.

**Page look after placing:** I copied the placed files and the live database and used the real clock. `/finance/darpan/kal` as darpan returned 200 (43 KB), with the helper present once and the script lexing clean. `api/day` returned 200 as darpan and 200 as manoj (kind `owner`).

**Install-day state (Charter 7):** the switch `bank_sms.standin_on` = **0**, so nothing changes on any screen until the owner switches it on.
- Sanjeevni 14-Oct: an SMS row and the MPR are both in. Darpan's day is `open`, provisional 1, and the existing MPR rule re-decides it.
- 13-Oct and 12-Oct: complete.

**DUTY_MAP:** unchanged. No duty was added, moved or removed. The door `/finance/darpan/kal` keeps all five of its duties' markers, as the staff-eye section shows.

### The walk (`walk_s565.py`): 29 checks green, then all 7 controls red on the old files
**How it draws the page:** the page draws itself in the browser, and the box has neither a browser nor node. Java 8's `jjs` cannot parse the page's arrow functions or async code. So the walk takes the page **as served** and runs, in `jjs`, the exact expressions that draw the online rows, verbatim from the served page:
- Darpan's row, the owner's row, `ownerPos` and `smsAt`.
- They run on the day's JSON exactly as the page receives it.
- The walk also lexes the whole `<script>`: strings, regex literals, comments, brackets and stray backslashes.

**The made-up data:** Sanjeevni days in April–May 2027, each checked empty by its key before use, with the walk's own SMS, MPR and POS rows.

**1 — an SMS day:**
- `compute_day` gives `'sms'`, ₹1,234, label "बैंक SMS 07:02".
- Darpan's row drew *"− Online (UPI / card) बैंक SMS 07:02 से — bank की report बाकी ₹1234"*: one rupee figure, no difference, and no `sms_diff`/`mpr_p` in his JSON.
- The owner's row drew *"provisional — bank SMS 07:02, MPR not in"* with no Devanagari. His note: *"UPI total from the bank's settlement SMS of 07:02 — the MPR mail is not in yet."*

**2 — a posted day worked again:**
- Posted on Marg's ₹500 (the handover API refuses a future day, so the walk writes the row the API writes and calls the same `_decide`).
- The SMS ₹600 lands, and a page read re-decides the day to ₹600, still provisional.
- A made-up MPR ₹610 lands and re-decides it again: not provisional, `statement_in`.
- A further read changes nothing (no loop).

**3 — POS, late SMS, a "never" day, parsing:**
- His POS total with the switch off: the three `pos` rows are drawn byte-identically by the new and old pages.
- An SMS received two days late reads *"provisional — bank SMS 28-Apr 07:02, MPR not in"*.
- A "never" day reads *"provisional — bank SMS 07:02, MPR never received"*. Darpan's row on it has no English "never" and one figure.
- The whole script lexes clean. The lexer can fail: `Marg\'s` unescaped is caught. An unescaped apostrophe on the new note line is caught by the lexer and by `jjs` (JSERROR).

**S — staff-eye:**
- Darpan's and manoj's "Kal ka hisaab" tiles are on their portal homes (the real `portal.py` and grants file, with a walk-only secret).
- All 5 duties at `/finance/darpan/kal` answer 200, and the marker of the one that is due (`manoj.cash_received`) is shown.
- Every Darpan read was under 100 KB and under 2 s (11 reads).
- The walk's output holds no run of 10 digits.

**Negative control (the same walk on the old files): all 7 `C:` checks red (7 of 28 checks red).** Old Darpan row: *"bank की report बाकी"* (the brief's control 1). Old owner row: *"Marg modes; bank not in"*. The SMS step did not re-decide the posted day (control 2). The helper, the note, the late line and the never line were all absent.

**Real browser render (builder, kit time):** headless Chrome on the PC rendered the walk's made-up days with the served pages, with `fetch` stubbed to the day JSON.
- New page: Darpan *"बैंक SMS 07:02 से — bank की report बाकी ₹1,234"*. Owner *"provisional — bank SMS 07:02, MPR not in ₹1,234"* plus the note. *"…28-Apr 07:02…"* and *"…MPR never received"* as expected. The POS rows are identical to the old page's.
- No JS error on any of the 14 renders.
- Old page: the plain lines.

**Rehearsal (`rehearse_s565.sh`, a made-up root, stub systemctl/journal):**
1. A forced red after placing put both files back byte-identically (exit 1).
2. The green run placed both files and gave PAGE OK.
3. The second run said ALREADY INSTALLED.
4. The live files were untouched throughout.

**Gates:** both pythons compile every kit file and the built `darpan_kal.py`. SUMS passed. `NO_PHONE_NUMBERS.py` was clean on all 8 kit files, and the publish gate was clean on 10. The kit ships no `.json`.

### Part B (`claude_vs_sarvam_s565.py`): read only, run once at 17:14:44
**Copies:** the script worked on copies under `/tmp/s565b` (finance.db ×3, assets.db ×4, all by the backup API), and removed them at the end.
- `purchase_app._s446_compare_one` was called as it is (no monkeypatch), with `/root/finance` on the path and `sqlite3.Row` on both connections.
- The learnt-name helper `item_check.learnt_line` imports, and `_s454_ic() is item_check`.
- Nothing was installed, scheduled or restarted. No screen, no Marg and no stored bill changed.

**The sample:** **102** `purchase_scan_link` rows (not 94: links were added since the brief). All 102 have their scan on disk, all are PDF, none is missing, all are `captured`, and none is a non-PDF/photo failure.

**The sort — my call, and why:** every one of the 102 has a `claude_reading ok=1` row, all dated 14-Oct. Taken literally, the brief's rule would put all 102 out of the side-by-side. But they were **not read at capture**:
- All 102 were captured between 29-Sep 12:33 and 13-Oct 08:30, before S550 existed. The rows come from S550's background re-read of older scans.
- S550's own README says it *"never writes anything on a pharmacy paper … the reading is kept aside. Sarvam fills the paper as before"*.
- The data agrees: the stored header equals Claude's reading on only 54 of 102 bills (vendor 79, bill number 77, total 85).

So the stored readings are Sarvam's (or a person's), and all 102 are side by side. **Read at capture: 0.**

**Hand corrections:** `bill_audit` on the sample shows only duplicate, lane and S441 question/answer actions (33 rows) and no edit-type action. So the data shows **no hand correction**. The scan app keeps no edit log of the header fields, so a correction made without an audit row cannot be seen.

**Gate:** the reader is `on` on the copy, with daily cap 400, 1 call today and 399 left (≥ 94), on model `claude-sonnet-5-5`.

**Claude's readings:** 102 came from existing rows, with no call.
- **My call:** 5 bills (the lowest ids) were read **fresh** on their own copy, only to measure the cost, because no stored reading carries usage.
- 5 calls, all HTTP 200 on `claude-sonnet-5-5`: 11,160 tokens in and 6,329 out, **USD 0.0856** at $2 / $10 per MTok. The prices were checked against the published table.
- That is **USD 0.0171 per bill**: 1.0 call, about 2,232 tokens in and 1,265 out. Cap $12, none refused, no failure.
- The fresh readings scored the same as the stored Claude readings of those 5 bills, except for one supplier.
- These calls were counted on the copy's counter, not the live one (the reader counts where `db_path` points).

**Result, on the same 102 bills with the same compare** (Sarvam scored fresh now; its stored rows give identical figures):

| | Sarvam | Claude |
|---|---|---|
| supplier right | 87 | 78 |
| bill number right | 88 | 78 |
| date right | 77 | 78 |
| total right | 91 | **94** |
| bills fully right (header + every line) | 5 | **11** |
| item lines read | 235 | 231 |
| item lines with any fault | 199 | **183** |
| — name | 45 | 44 |
| — qty | 32 | **8** |
| — rate | 37 | 31 |
| — batch | 122 | 109 |
| — expiry | 37 | **15** |
| bills with every item line right | 8 | **17** |

**Bills only one of the two got right:**

| field | Sarvam only | Claude only |
|---|---|---|
| supplier | 11 | 2 |
| bill number | 12 | 2 |
| date | 11 | 12 |
| total | 6 | 9 |
| fully right | 2 | 8 |

Claude read no item line on 1 bill.

**Fairness — the comparison leans towards Sarvam on supplier and bill number:**
- The 102 links were themselves made from the stored Sarvam readings: on the bill number for 82, the supplier for 94 and the amount for 95 (15 by reception or auto).
- The supplier check knows 11 spellings learnt from Sarvam's misreadings (`purchase_scan_alias`). 15 of Sarvam's 87 supplier passes need one of them, or the chosen supplier.
- The item check knows 54 printed names learnt from Sarvam's readings.
- On 24 bills Claude's bill number is not Marg's: 16 of them are letter-prefixed numbers (e.g. `A000…`, `RT-…`, `JP…` where Marg has a short number), and 8 have nothing read. On 18 of the 24, Claude's total is right, so it read the right paper and probably a different printed number (a serial or order number).

The scan papers themselves would settle this. I did not open them.

**Per-bill detail:** `_scratch\S565_DARPAN_SMS_AND_CLAUDE_BILLS\claude_vs_sarvam_detail.csv` (git-ignored, 102 rows). It has no `vendor_phone` or `vendor_email` column at all, 0 runs of 10 digits, Marg's supplier and bill number, and both sides' flags and fault counts.

### Decisions I made where the brief is silent or its premise did not hold
1. **All 102 side by side**, as explained above: S550 kept Claude's pharmacy readings aside, and every bill predates S550.
2. **5 fresh reads, for the cost only.** With every bill already read, the brief's rule needed no call, but it asks for the cost per bill.
3. **The page is drawn in `jjs`** from the served page's own expressions, plus a lexer and a real Chrome render at kit time. The box has no node or browser, and `jjs` (Java 8) cannot run the whole page. The installer refuses to run without `jjs`.
4. **`bank_sms.py` pinned at its live S564 md5** (read only), as noted above.
5. **Darpan's row on an SMS day whose label has no time** (an SMS whose `received_at` cannot be read) would read *"बैंक SMS  से — …"*, and the owner's *"bank SMS , MPR not in"*. These are the brief's exact strings. Not reachable from the door today, which always stamps the time.

### Charter
- **Retired:** nothing. No second copy of a figure was added: the SMS label is still built once, in `darpan_kal.py`, and the English owner line is the page's own, as the brief orders.
- **Left out:** nothing.
- **Seen, not touched:**
  - (a) With the switch OFF, a posted day keeps the SMS figure until the MPR comes. The brief already saw this.
  - (b) On a "never" SMS day the owner's row says *"MPR never received"*, but his note under it still says *"the MPR mail is not in yet"*. These are the brief's words; a later kit could pick "never" there.
  - (c) `claude_reader` counts calls only in the database it is given, so a read on a copy is not on the live daily counter.
  - (d) The Sarvam trial's supplier aliases and learnt item names come from Sarvam's readings, so any future Claude-vs-Sarvam score inherits that lean.
  - (e) The scan app keeps no audit row for a header edit, so hand corrections cannot be counted.
- **The dependency at install:** the switch was OFF. Sanjeevni's Marg day for 14-Oct is applied (Darpan's row exists) and its MPR is in.

### Housekeeping and permissions
**Removed on the box:** `/tmp/s565b` (by the script), `/tmp/s565b_out`, `/tmp/s565dev`, and the installer's scratch (by the installer). `/tmp/s565kit` and `/tmp/s565probe` were removed with the lock.

**The lock:** held from 17:12 until this report was written. It was removed at **17:17:53 IST** (read back), and nothing named `s565` is left in `/tmp`.

**One refusal by the permission list:** a `Remove-Item -Recurse -Force` of the builder's own scratch on the PC was refused, and I did not respell it. The PC's `_scratch\S565_DARPAN_SMS_AND_CLAUDE_BILLS\` (git-ignored) therefore still holds:
- `dump.json` and `chrome\`: the walk's made-up days as the app served them on a copy, which also carry that copy's open owed rows, order sheet and supplier claims. No phone number and no patient.
- The probes' outputs: Marg supplier names and bill numbers for the 25 disagreeing bills.
- The CSV.

Delete the folder by hand when the chat has copied the CSV.

### Undo (one line, on the server)
```
\cp -p /root/finance/darpan_kal.html.bak_S565_f5e279eb /root/finance/darpan_kal.html && \cp -p /root/finance/darpan_kal.py.bak_S565_a8e11c31 /root/finance/darpan_kal.py && systemctl restart clinic-finance
```
Then check `/finance/healthz` 200 and read the md5s back (`f5e279eb…`, `a8e11c31…`). No data step was taken, so the database backup is not needed for an undo.
