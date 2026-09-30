# REPORT S439 — S439_SCANS_SMS_SCROLL (F-660 · F-661) · installed 30-Sep-2026 13:42 IST · published (see the foot)

## For the owner
- **Scans: 26 of the 51 unlinked scans are now linked** — 52 of the 77 medicine scans of 29-Sep are linked to their Marg bill. 4 more
  were second scans of a bill that already had one (marked "already scanned", not counted twice). **21 are still open, each with its reason
  on the page** (list below): 10 are bills of 25–29 Sep that Marg has not sent yet — they will link by themselves after Amir's next export;
  5 where the bill number was misread and 3 where the amount was misread (the page names the likely bill beside each); 3 where no vendor
  could be read.
- **Nothing went missing on 29-Sep.** "101" is the number stamped on the last paper (B-0101), not the count of medicine bills: 17 papers
  are older clinic bills (14-Aug to 28-Sep); on 29-Sep 84 were scanned — 79 medicine, 3 lab, 2 clinic. Every upload that evening was
  accepted (83 of 83) and made its row; 2 were the same bill scanned again at once and were set aside as duplicates.
- **SMS: yes, accepted.** The phone was sending each SMS inside the web address with no name on it, and the door only looked for a field
  called "text" — so every one was refused. The door now reads it the way the phone sends it; nothing on the phone has to change. The 15
  earlier SMS were found in the web server's own log and read again: **10 ICICI settlement SMS (mornings of 18–24 Sep, 29 and 30 Sep —
  8 Sanjeevni, 2 clinic) now show on the Bank SMS page, and every one equals the bank's own report to the rupee.** The first the live door
  takes by itself will be tomorrow morning's.
- **Days section:** an Approve now leaves the list exactly where you were — the month's list no longer jumps back to its top, and the month
  stays open after its last day is approved.
- Worth your eye: 4 of the new links were made on vendor + bill number although the amount on the scan differs from Marg's — KEDAR 185
  (scan ₹16,760, Marg ₹18,700), GUNINA 71226 (₹1,52,618 / ₹14,908), GUNINA 72975 (₹25,578 / ₹8,526), SHIVAAZ 3290 (₹1,885 / ₹1,108).
  Either OCR misread the total or Marg's entry is wrong; they are marked PROBABLE.

**The 21 scans still open (scan number · what OCR read · why):**
- *No bill on the server yet (10) — Marg's bills here end at 25-Sep:* #91 KEDAR 195 · #92 DEEPAM (the licence number read as the bill number) · #93 GUNINA 74915 ·
  #94 ESS KAY 8053 · #95 SHIVAAZ 3378 · #96 ESSENTIAL 2517 · #97 RADHA 17967 · #98 SCIENTIFIC & MEDICAL AID 5302 · #99 YUVIKA 823 ·
  #101 MANNAT 393.
- *Bill number differs (5) — same supplier, same amount, the number misread; the likely bill:* #33 → L.K. 75904 (₹4,440) · #42 → L.K. 78354
  (₹1,199) · #48 → ESSENTIAL EP002243 (₹2,415) · #88 → SAISUN IP006767 (₹8,479) · #41 → L.K. 783473 (₹841), which already has scan #29
  (so #41 is a second scan).
- *Amount differs (3) — the buyer's name was read as the vendor, the bill found by its number:* #80 → A.A. 416 (scan ₹2,304, Marg ₹2,195) ·
  #82 → KEDAR 189 (₹7,668 / ₹7,008) · #78 → YUVIKA 634 (₹10,786 / ₹5,235; that bill already has scan #75).
- *Vendor unknown (3):* #54 and #79 (the buyer's own name read as the vendor, the number on no bill) · #100 BAAS PLASMA DISTRIBUTORS, a
  2023 bill of a firm that is not a supplier on the server.
- *Already scanned (4, not in the 21):* #44 (YOGENDRA 15496, linked to #45) · #46 (JANTA 19139, #27) · #51 (KEDAR 175, #23) · #68 (SHIVAAZ 3173, #31).
- September bills that have no scan at all (10): DEEPAM 545 · JANTA 18108 · KEDAR 160, 162, A000163 · L.K. 75707 · YOGENDRA 14928 ·
  SHIVAAZ 2888 · RAVI 7617 · A.A. 415.

https://followup.dr-manoj.in/finance/approvals
https://followup.dr-manoj.in/finance/purchase/page/scans  (the "without scan" page: Scan links)
https://followup.dr-manoj.in/finance/bank-sms

## For the chat
**Kit** `deploy_kits/S439_SCANS_SMS_SCROLL/` (8 files: `make_s439.py`, `purchase_block_s439.py`, `replay_s439.py`, `walk_s439.py`,
`install_S439_SCANS_SMS_SCROLL.sh`, `README.md`, `KIT_ID.txt`, `SUMS.md5`). Ran on the box from `/tmp/s439kit` — byte-identical to the
repository kit (`diff -r` after the publish, the foot). Build lock `/root/deploy/.claude_code_build.lock` taken 13:24:31 IST (owner
S439_SCANS_SMS_SCROLL), held through seven dry runs, the install and this report.

**What was read first (read-only, from 12:49:15 IST, before the lock) — the brief's facts, confirmed or corrected**
- Pins at the brief's values: `bank_sms.py` a70d6d96 (S405's TO), `finance_approvals.html` 9d1eddc8 (S428's TO), `purchase_app.py`
  9c40d13e (read live). No lock held. The three services active, healthz 200.
- Scans: as the brief read — 86 rows since 28-Sep, 79 pharmacy (77 captured, 2 rejected), 26 linked, 51 unlinked. **Corrected:** the "15
  that never arrived" are bills 1–15 of the register (14-Aug to 25-Sep, clinic lane): `bills` holds ids 1–101 with no gap and B-0101 is
  the last stamp. **`bills.created_at` is UTC** (the row of 12:34:44 has its audit line at 18:05 IST; the files' mtimes are 17–19h): the
  scanning ran 18:03–19:07 IST, not 12:30–14:00. The asset app's journal has no line in that window (gunicorn logs no requests and raised
  no error); the web server (LiteSpeed) log for 17:25–19:35 IST has `POST /scanapp/intake/scan_submit` 200 × 83, no other status, and
  83 rows were made in that window; all 84 rows of the day have their stored file. Nothing to name for the parent in the asset app.
- SMS: **corrected.** The refused posts were not "different field names" and not a raw body: the macro's address is
  `…/api/bank-sms?{sms_message}={sms_message}` — the SMS is the query string, its own field name, no body (seen in the web log; two posts
  of 17-Sep and 23-Sep carry the unfilled `{sms_message}` itself). The brief's field list alone would not have accepted a single real
  post; the bare query is read too. **The raw texts ARE retrievable** — from the web server's access log (the live file and one rotated
  `.gz`), back to 17-Sep — so they were replayed (below). 7 refused rows by then, not 5 (two more on 30-Sep 07:05 / 07:13).
- Scroll: **corrected** (found in a real browser before the install, see Proof). Each month's table is inside a 430px scroll box
  (`.tblwrap{max-height:430px;overflow:auto}`); any redraw of Days rebuilds it and the box returns to its own top. That alone reproduces
  the owner's words, and the brief's prescription (loadDays instead of load, restore `pageYOffset`) leaves it uncured: the first build of
  this kit did exactly that and the harness showed the approved row still jumping. `daysKeep()` now also restores each box's scroll.
- "Matching runs only at intake": the push door already re-matched (`_rematch_after_push`, S225) — with the same strict grades, and by
  deleting and recomputing every link. The hook is kept; what it calls is new.

**Live files, FROM → TO (md5 read back on the box after placing, 13:42:46 IST)**
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py (anchored + the S439 block appended) | 9c40d13ed222addeadf97d3f352f359a | ebe38c681f323782f0a211d1d0879b24 |
| /root/finance/bank_sms.py (anchored) | a70d6d96e700380d08b8e379ea0720e5 | 7cdd0ac9ca64921507bd0c65ab6a0e99 |
| /root/finance/finance_ui/finance_approvals.html (PARENT'S, one anchored change) | 9d1eddc8f96856674e1dc3638490bbeb | 8edc44c51b46e7d7643840b485715c85 |

Pins checked before touching (12:49, and by the installer at 13:41). Restarted `clinic-finance` only (active since 13:42:00 IST).
**Cron:** one root line added (crontab 78 → 79 lines):
`59 23 * * * cd /root/finance && FINANCE_DB=/root/finance/finance.db /root/wa/venv/bin/python3 -B /root/finance/purchase_app.py rematch >> /root/finance/scan_rematch.log 2>&1 # S439_SCANS_SMS_SCROLL`.
READ ONLY: `/root/assetapp/*`, `assets.db`, the web server's access log. `porders.py`, `supplier_msg.py`, `finance_app.py`, the portal: not touched.

**Backups:** `finance.db.bak_S439_20260930_134133` (backup API, 27,828,224 bytes), `crontab.bak_S439_20260930_134133`, and beside each
file `purchase_app.py.bak_S439_9c40d13e`, `bank_sms.py.bak_S439_a70d6d96`, `finance_ui/finance_approvals.html.bak_S439_9d1eddc8` (each
read back at its FROM md5).

**Health after placing (13:42–13:44 IST):** local and public `/finance/healthz` 200; `/finance/purchase/page/scans`, `/finance/bank-sms`,
`/finance/approvals`, `/finance/porders` 302 (login gate, expected); the SMS door without a key 401; journal since the restart: only
gunicorn's two "Worker was sent SIGTERM" lines of the restart itself, no traceback, nothing "NOT mounted". The pages rendered from a copy
of the live files over a scratch copy of the live database (13:43:35): scan-links 200 — "52 links stored · 25 scans with no Marg bill ·
17 Marg bills with no scan", both new columns, reasons on 10 + 3 + 3 + 5 + 4 rows, 6 "is probably this bill" notes; bank-sms 200 — 10
"matches MPR" cells, 0 "differs", Last SMS received 2026-09-30 07:13:06, Ignored (2) with the Fields column and the setup line;
approvals 200 with `daysStay` / `daysKeep`; the purchase hub 200; reception's Purchase orders state 200.

**The first pass on the live database (13:42:07 IST, `purchase_app.py rematch --list`, who "install S439"):**
`26 new link(s) · 52 links stored · 77 pharmacy scans · 25 still open (amount differs 3 · already scanned 4 · no bill on the server yet 10 ·
bill number differs 5 · vendor unknown 3)`. Links now: EXACT 30, PROBABLE 22; by rule — vendor+bill+amount 11 · bill_tail+vendor+amount~2%
19 · bill+amount~2% 1 · bill_tail+amount~2% 3 · bill_tail+vendor 4 · vendor+date+amount 14 (the 26 stored links all stayed). The 26 new:
- EXACT bill_tail+vendor+amount~2% (19): #35→KEDAR 166 · #38→GUNINA 65194 · #40→JUBILEE 15521 · #43→AGARWAL SURGICALS 4430 · #49→ESS KAY 7234 ·
  #50→GUNINA 67093 · #55→SHIVAAZ 3051 · #57→GUNINA 67925 · #62→KEDAR 182 · #64→KEDAR 184 · #85→GUNINA 73098 · #87→KEDAR 190 · #90→JANTA 21054 ·
  #89→ESS KAY 8012 · #67→JANTA 19968 · #36→GUNINA 64906 · #61→JANTA 19460 · #47→JUBILEE 15878 ("18112 (NOT015878)", by its last run) · #53→KEDAR 171.
- PROBABLE bill_tail+amount~2% (3, the buyer or a letterhead read as the vendor): #34→DRUG DEAL 5207 · #73→DRUG DEAL 5620 · #72→DEEPAM 601.
- PROBABLE bill_tail+vendor (4, the amount differs — the owner's line above): #83→SHIVAAZ 3290 · #76→KEDAR 185 · #77→GUNINA 71226 · #86→GUNINA 72975.
Audit (who "install S439"): scan_link 26 · scan_dup 4 · alias_learn 9 · rematch 1. Nine spellings learned into `purchase_scan_alias`
(KEDAR PHAMACEUTICAL, KEEDAR, KEDAR PHALAMACEUTICAL, KEDAR PHARMA CEUTICAL → KEDAR PHARMACEUTICAL; SUNINA, CUNINA → GUNINA; JUBLEE →
JUBILEE; SHIVAZ → SHIVAAZ; AGARWAL SURGICAL & MEDICALS → AGARWAL SURGICALS AND MEDICALS). `purchase_vendor_alias`: 14 rows, untouched.
September bills: 52 with a scan, 17 without (6 of them with a probable open scan named on the page).
Against the brief's expectation (≈ 30 of 51): 26 linked + 4 recognised as second scans = 30.

**The replay on the live database (13:42:07 IST, `replay_s439.py`, once — setting `bank_sms.s439_replay`):** 17 posts with status 200 in
the log, 15 replayed, 2 skipped as the macro's own unfilled test posts, the 7 empty refused notes replaced.
- ICICI settlement stored, read strict, 10: received 18-Sep 07:06:23 (medical, business day 17-Sep) — **the first accepted row** · 19-Sep ·
  20-Sep · 22-Sep ×2 (clinic, medical) · 23-Sep · 24-Sep · 29-Sep 07:01:36 · 30-Sep 07:05:54 (clinic) · 30-Sep 07:13:06 (medical). Each
  keeps the time the phone posted it, one copy of the text, and equals `upi_txn` (the bank's MPR) for its unit and business day to the
  rupee: 10 of 10.
- Yes Bank: 3 posts of 28-Sep stored as "other debit" (2 rows, one seen twice); 26-Sep 06:40 and 29-Sep 17:14 ignored with their masked
  text and the reason "Yes Bank text without a debit or credit word" (a balance SMS, a feedback SMS). No NEFT debit among them, no event made.
- A live SMS since the install: none by 13:44:30 IST (the next ICICI SMS is due about 07:00 tomorrow); the walk's posts in the phone's
  exact shape are the proof until then.

**The walk (`walk_s439.py`, in the install at 13:41): `WALK_S439 GREEN -- 55 of 55 passed`** on scratch copies of finance.db and assets.db,
the real finance_app through Flask's test client; its own rows keyed W439 (16 bills under its own export md5 with suppliers whose names
carry WALK, 20 scans stamped W439-01..20, SMS of its own amounts), every date from today, the door's own key file, the push door's own token.
- Matcher (14): the forms of the real scans over the walk's digits — "A0439166", "GPPL-26-43964906", "NOT043915521", "SF 004393051",
  "A04397234", "G-4394430" each EXACT `bill_tail+vendor+amount~2%` with misspelt / punctuated vendors and years 2036 / 2024 / 2028 / 2018;
  "T004395620" under a letterhead and "A000439601" under the buyer's name PROBABLE `bill_tail+amount~2%`; "43918112 (NOT04315878)" to the bill
  of its LAST run while the bill numbered by its first run (same vendor, same amount) stays unscanned; the licence number as bill number with
  the date 2 days off PROBABLE `vendor+date+amount`; the exact scan EXACT `vendor+bill+amount`; vendor misspelt and amount misread PROBABLE
  `bill_tail+vendor`; the tails of the brief's own examples and the buyer in three spellings.
- One scan a bill, learning, audit, idempotence (7): the same paper again → `dup`, dup_cand = the first scan, audited once, no second link;
  the spelling learned ONCE (one row, one audit "S439 learned from scan <id>") and resolved as learned afterwards; `purchase_vendor_alias`
  14 rows before and after; all 13 links audited with scan, grade and rule; `scan_bill_id` set; the second run: 0 new links, 0 new audits,
  the same links.
- WHY (7): no bill yet · vendor unknown · amount differs (hint bill named) · no digits read · bill number differs (NOT linked) — each on the
  page word for word, the two new columns, the probable scan beside its bill.
- Re-match (4): a scan made before its bill waits with "no bill on the server yet" and the push of the bill links it at once (audited by
  "push"); the command line exits 0 with its line and list; stored links stay, the hub and reception's screen answer 200; assets.db
  byte-identical after every pass.
- SMS door (14): wrong key 401; message/from (form), body/number (JSON), a raw body, **the phone's `?<SMS>=<SMS>`** (one copy kept),
  MESSAGE/From, text/sender, the key in the address — all stored; an OTP refused with "message,from,ts" kept and masked; the key in no row
  ("[key]" where a body carried it); the page; the replay over the walk's own log lines (stored with the log's time, the empty note
  replaced, the test post and a 401 line skipped, nothing of the text printed, once only); APP_VERSION still S405's.
- Scroll (5, the page's script read as text): approve() no longer calls load(); daysKeep() records → draws → restores in that order;
  daysStay() draws through it; it re-reads only Days, Needs-you, Cash and the old queue; ONE line left the parent's page.
**Negative control (4, the unpatched files over the same crafted rows):** the old matcher links 0 of the 12 forms (only the exact scan);
no reason column, the push links nothing, no command line; the old door refuses message/from, the raw body and the bare query with an
EMPTY text and no field names (only text/sender stored); the old approve() calls load() and there is no daysStay().

**Earlier walks re-run on the patched files, UNCHANGED, each against its own pre-kit control (in the install):** S405 `29/29` · S403 `52/52`.
No assertion of either was adjusted (APP_VERSION was deliberately left at S405's string so that S405's walk stays as written).
One declared change of data, in the installer: S403's walk runs on the finance backup of 26-Sep 17:45 (S417's declaration) and now on
`assets.db.bak_S435_20260928_103702`. Measured on the box before the install (a diagnosis run that placed nothing): on the UNPATCHED live files over a copy of today's assets.db that walk is
`RED -- 2 of 52` (every YUVIKA bill of September now has a real scan, so it picks DEEPAM 545 and its crafted scan links PROBABLE); on the
28-Sep assets backup it is `GREEN -- 52/52`. Nothing to do with S439.

**The scroll in a real browser (before the install; local, scratch, not in the kit):** a small harness served the built page and the
live one with crafted days of 2099 (three months, a backlog to approve); headless Edge ran 12 approvals down a month, scrolling to each
day first. New page: the approved row's position on the screen unchanged every time (386 → 386 px; 384 on the last), the page offset
unchanged, the month still open after its last day. Old page: the row jumped on 7 of 12 (386 → 423…717 px: the month box back at its top)
and the month closed after its last approval. The Browser pane could not run this (the app window was not drawn, so no scrolling).

**Dry runs before the install (DRY=1 from /tmp/s439kit, under the lock), seven.** What they changed, none a change to what the owner
asked for: (1) the walk's first vendor names CONTAINED real ones ("…YUVIKA SURGICALS") and S403's vendor rule matches a contained name —
its own scan matched a real bill; the walk's suppliers were renamed; its push token is set where the front gate reads it; a comment said
"load()" inside approve(). (2) the push case was linkable by the old date rule — its scan got a year-off date so the control is a control.
(3) on the full bill list the reasons named April and June bills as "likely" (the same number "1", the same amount) — a likely bill must
now be within 60 days of the scan, and a scan dated after Marg's last bill reads "no bill on the server yet"; the replay read only the
live log — the rotated file holds 17–28 Sep. (4) the macro's test posts showed the real shape `?X=X`: one copy is kept. (5)–(7) the month
box's own scroll (found in the browser), the instant put-back, `INSERT OR IGNORE` on a link (the cron and a page at the same moment).

**Calls made where the brief left room**
- `dup_cand` and the reasons are in finance.db (`purchase_scan_state`), not on the scan row: the brief keeps assets.db READ ONLY.
- The learned spellings are in a new table `purchase_scan_alias`, NOT in `purchase_vendor_alias` as the brief said. That table is the
  owner's S263 link from a bill's name to the bank-account row it is paid into (`_vendor_bank`, the advice); an OCR misreading written
  there could lend a NEFT lane to a supplier that merely looks alike. The matcher reads it (both sides) and never writes it.
- Two reasons beside the brief's four: "bill number differs" and "already scanned". "No digits read" has no scan today.
- The phone-setup line is on the Bank SMS page's own setup card in `bank_sms.py`; S407's phone-setup page (`supplier_msg.py`) is the
  reception phone's WhatsApp macro and was not touched.
- The replay took every post in the log, including 18–24 Sep (before S405).
- After an approve the Cash card is re-read too (the day's cash moves to the pool), and the old queue if it was opened.
- The old `_rematch` stays in the file as `_rematch_before_s439` (S263's idiom: re-defined at the end, nothing in the middle rewritten).

**Outside the brief — noticed, not touched**
- **The SMS travels in the web address**, so the web server's access log keeps every bank SMS in plain text (balances, account tails).
  The door now also reads a body (`text` or `message`, form or JSON): moving the SMS from the address to the body is one change in each
  macro on the phone. Until then the log is what it is (it was also what made the replay possible).
- **Macro 2 forwards every Yes Bank SMS**, not only the Sanjeevni account's: two other account tails (mutual-fund SIP debits), a balance
  SMS, a feedback SMS. With the door mended these appear on the owner's page as "other debit" rows or in Ignored. Narrowing the trigger,
  or telling the door which account tail is Sanjeevni's, is the owner's call.
- **Reception's "Bill scan karo" list** (`porders.py`, not in the brief) still asks for 17 bills; 6 of them have an open scan that is
  probably theirs (L.K. 75904, 78354 · ESSENTIAL EP002243 · A.A. 416 · KEDAR 189 · SAISUN IP006767). The owner's page says so; reception's
  does not. A one-tap "this scan is this bill" for the owner would close such pairs for good.
- **Opening or closing a day row, and Log cash, still send the month box to its top** (`dayToggle`, `logSend`, `bhatiMove` → `renderDays()`):
  the same cause. `daysKeep(function(){ renderDays() })` in those three is the whole cure; the brief allowed one change in the parent's page.
- KEDAR bill A000163 of 03-Sep is on the server twice (`A000163` and `a000163`: the key is case-sensitive).
- OCR that finishes after the last scan of a session was not re-tried until the next scan or push (the fingerprint is count + max id);
  the nightly pass now covers it within the day.
- `PUBLISH_ALL` published everything pending, as it does: beside this kit, the chat's own `S438_COUNT_BOOK.md`, `S438_COUNT_MOCK_06SEP.html`
  and this brief (the gate read all 11 files: clean). S438 itself was not built.
- No command was refused by the permission list in this session.
- The kit's README says the first reading ran "12:49–13:20 IST": 12:49:15 is read; the 13:20 is not a read time (the reading ended before
  the lock at 13:24:31). The kit is published and frozen, so it is said here.
- Not done: nothing of the brief was left out.

**Undo:** the three `.bak_S439_<from8>` files back, `crontab /root/finance/crontab.bak_S439_20260930_134133`, `systemctl restart
clinic-finance`, healthz 200, md5s read back. The 26 links, the two new tables, the `fields` column and the replayed SMS rows are data the
older files ignore or read as before (the older matcher recomputes its own links on its next run);
`finance.db.bak_S439_20260930_134133` only if the owner asks for them to be reversed — say so first.

**After the publish (13:44–13:47 IST):** repository published with `PUBLISH_ALL.bat` (gate clean over 11 files, commit `cdde529` on main, origin verified);
on the box `git pull --ff-only` → HEAD cdde529 (13:44:28); `deploy_kits/S439_SCANS_SMS_SCROLL/` SUMS.md5 7 of 7 OK; `diff -r` repo kit vs `/tmp/s439kit`
(what ran): byte-identical; the repository's own installer run from `/root/deploy/repo`: "ALREADY INSTALLED: the three files are at the kit's
pins; cron line 1; clinic-finance active; healthz 200"; public healthz 200; the build lock released 13:47:15 IST. This report is published
in a second commit.
