# S439_SCANS_SMS_SCROLL — the scan matcher reads what OCR writes · the bank-SMS door reads what the phone sends · an Approve keeps the Days section in its place (F-660 · F-661)

**Sanjeevni project · session 283 · 30-Sep-2026 · brief `claude_code_briefs/S439_SCANS_SMS_SCROLL.md` · runs after S437 (live 28-Sep 23:09 IST).**
Owner's pages, English. One parent's file, one anchored change (declared in the brief). The asset app is READ ONLY here.

## What the owner said (30-Sep)
"Yesterday reception scanned all medical bills of September (101), but the system is showing very few — check." "SMS from MacroDroid
doesn't appear on the Sanjeevni page; only the bank statement is seen." "My Sanjeevni page — the Days section scrolls back to the top on
any Approve; make it stay there."

## What was found on the box (read-only, 30-Sep 12:49–13:20 IST)
- **Scans.** `assets.db bills` holds ids 1–101 with no gap: 101 is the stamp on the LAST paper (B-0101), not the count of medicine bills.
  17 papers are older (14-Aug → 28-Sep, the clinic lane); on 29-Sep 84 were scanned — 79 pharmacy (77 captured + 2 the duplicate guard
  rejected), 3 lab, 2 clinic. The web server's log for 17:25–19:35 IST that evening has 83 `POST /scanapp/intake/scan_submit`, every one
  answered 200, and 83 rows were made in that window: **nothing was refused and nothing was lost.** (`bills.created_at` is UTC — the
  brief's "12:30–14:00 IST" is 18:03–19:07 IST.) Of the 77 captured, 26 were linked and 51 were not — as the brief read.
- **SMS.** The macro posts to `…/finance/api/bank-sms?{sms_message}={sms_message}`: the SMS is the bare query string of the address — it
  is its own field name — with no body. The door read only a field called `text`, so every post since S405 was refused with an empty
  text (7 by 30-Sep 07:13), and the posts of 18–24 Sep were dropped by the pre-S405 door without a trace. The brief's list of field
  names would not have caught this shape; the bare query is read too. Because the text travelled in the address, the web server's access
  log still holds every post: they are **retrievable** (the brief assumed they were not) and are replayed once.
- **Scroll.** Two causes, found by running the page in a real browser (headless Edge over a local harness, crafted days of 2099).
  (1) Each month's table sits in its own scroll box (`.tblwrap{max-height:430px;overflow:auto}`): every redraw of Days rebuilt it and its
  scroll returned to ITS top, so the day just approved, further down the month, went out of sight — this alone reproduces "scrolls back to
  the top on any Approve", and replacing `load()` by `loadDays()` would not have cured it. (2) `approve()` called `load()` (every card
  emptied and redrawn), and a month whose last day was approved closed by itself.

## What was built
**3.1 The matcher — `purchase_app.py`** (the S439 block `purchase_block_s439.py`, appended verbatim by `make_s439.py`; `_rematch` is
re-defined there, S263's idiom; four anchored edits in `page_scans`).
- *Bill tail*: the digit runs of the bill number, zeros dropped, a financial-year suffix ("2026-27") set aside; the LAST run is the number,
  an earlier run of 3+ digits stays as a second candidate ("GPPL-26-64906" → 64906; "A000166" → 166; "18112 (NOT015878)" → 15878, then 18112).
- *Vendor*: resolved once per scan to a supplier on Marg's bills — Marg's own names, both sides of the owner's S263 links (read only), the
  spellings learned here, then a token-set similarity ≥ 0.70 that must lead the next supplier by 0.10 (upper case, letters only, initials
  joined, PVT / LTD / M/S / EXTN / the city dropped; a trade word — PHARMA, AGENCIES, MEDICOS — weighs 0.3 and a NAME word must pair at
  0.80, so "JANTA PHARMACEUTICALS" is never "GUNINA PHARMACEUTICALS"). A link made through similarity learns the spelling
  (`purchase_scan_alias`, audited `alias_learn` "S439 learned from scan <id>"). SANJEEV* in any spelling, or a bare MEDICOS*, is the buyer:
  vendor unknown, bill tail + amount only.
- *Dates*: a year outside this and last financial year is not believed (never blocks; its day and month still break ties);
  vendor + date + amount takes ±3 days.
- *Grades*, strongest first: EXACT `vendor+bill+amount` (S403's) · EXACT `bill_tail+vendor+amount~2%` · PROBABLE `bill+amount~2%` (S403's) ·
  PROBABLE `bill_tail+amount~2%` · PROBABLE `bill_tail+vendor` · PROBABLE `vendor+date+amount` (S403's, the date now ±3 days).
- *The pass* `_rematch(con, who)`: a stored link STAYS while its scan and bill are still there and still match (before: every link was
  deleted and recomputed on each run); every captured, unlinked pharmacy scan is then tried, the strongest rule first; a bill takes ONE
  scan — a scan whose best bill already has one is a second scan of the same paper: `dup_cand` / `dup_bill` in `purchase_scan_state`
  (audited `scan_dup`), never a second link. Every link written is audited (`scan_link`: scan, grade, rule). A second run links 0.
  It runs at every Marg purchase push (`_rematch_after_push`, the hook S225 put there — the brief read the matching as intake-only; the
  hook existed but recomputed with the same strict grades), when the scans change (`_rematch_if_changed`), nightly at 23:59 (one root cron
  line: `purchase_app.py rematch`) and once at install.
- *WHY*: every scan still open carries its reason in `purchase_scan_state` and on the owner's scan-links page (new column "Why it is not
  linked"): no bill on the server yet · vendor unknown · amount differs · no digits read — and two more: **bill number differs** (the same
  supplier has a bill of this amount within 60 days; the number did not match, so it is NOT linked, the likely bill is named) and
  **already scanned**. The list "Marg bills with no scan" gains "A scan already here?": the open scan that is probably this bill.

**3.2 The SMS door — `bank_sms.py`** (`APP_VERSION` stays S405's — its walk pins it; `S439_REV` beside it).
- `read_post()`: the SMS from any of `text, message, msg, body, sms, content, v1`, the sender from `sender, from, number, address, v2` —
  JSON, form or query, any letter case; else the raw body (a broken JSON, `message=…` sent as plain text, or the SMS itself); else the bare
  query string (`?<SMS>` or the phone's `?<SMS>=<SMS>`: one copy kept). The first candidate that reads as a bank SMS wins.
- A refused post keeps the **field names it carried** (`bank_sms_ignored.fields`: "message,from,ts", "(bare query, no field name)",
  "(raw body, text/plain)", "(empty post)") beside its masked text; the Ignored card shows the column. The key is cut out of anything kept.
- `take(con, text, sender, stamp, fields)`: the door's reading and storing apart from the HTTP request (the same statements as before).
- The phone-setup card on `/finance/bank-sms` gains one line naming the accepted field names — the brief said "the S407 phone-setup page":
  S407's page (`supplier_msg.py`) is the reception phone's WhatsApp macro; the bank-SMS macro's card is in `bank_sms.py`, so the line is
  there and `supplier_msg.py` is not touched.
- `replay_s439.py` (run once at install, marked by setting `bank_sms.s439_replay`): every post the door answered 200 in the web server's
  access log (the live file and its rotated ones, read only) goes through `take()` with the time the phone posted it; the refused note of
  the same second, kept with no text, is replaced by what the door now makes of the post. It prints outcomes only — never a text, an
  amount, an account or the key.

**3.3 The Days section — `finance_ui/finance_approvals.html`** (PARENT'S; ONE anchored change: approve()'s success line, with the four
small functions it needs — `daysMonKey`, `daysHold`, `daysKeep`, `daysStay` — inserted right after approve()). `approve()` calls `daysStay()` instead of `load()`: Days, the Needs-you strip and
the Cash card are read again (the trio `logSend` already uses; the old queue too if it was opened — an approve made from it must leave
it), and `daysKeep()` puts back what the draw loses: the months that were open, each month box's own scroll, and the page's offset
(`daysHold` makes the put-back instant — the page's stylesheet scrolls smoothly). If the Needs-you strip above then loses a line, the
Days card is held where it was on the screen.

## Calls made where the brief left room (each is in the report)
- **`dup_cand` and the reasons live in finance.db** (`purchase_scan_state`), not on the scan row: the brief keeps assets.db READ ONLY.
- **The learned spellings live in `purchase_scan_alias`, not in `purchase_vendor_alias`.** That table is the owner's S263 link from a bill's
  name to the bank-account row it is paid into (`_vendor_bank`, the bank advice); an OCR misreading written there could one day lend a
  NEFT lane to a supplier that merely looks alike. The matcher READS it and the walk proves it untouched.
- **A fifth and sixth reason** beside the brief's four (bill number differs · already scanned).
- **The web log replay includes the posts before S405** (18–24 Sep): the same fault, the same log.
- **The Cash card is re-read after an approve** as well as Days and the Needs-you strip (an approval moves the day's cash to the pool).

## Pins (FROM read on the box 30-Sep-2026 12:49 IST → TO; built by `make_s439.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py (read live; last placed 27-Sep 04:51 IST) | 9c40d13ed222addeadf97d3f352f359a | ebe38c681f323782f0a211d1d0879b24 |
| /root/finance/bank_sms.py (S405's TO) | a70d6d96e700380d08b8e379ea0720e5 | 7cdd0ac9ca64921507bd0c65ab6a0e99 |
| /root/finance/finance_ui/finance_approvals.html (PARENT'S; S428's TO) | 9d1eddc8f96856674e1dc3638490bbeb | 8edc44c51b46e7d7643840b485715c85 |

One root cron line (crontab backed up first): `59 23 * * * … purchase_app.py rematch >> /root/finance/scan_rematch.log 2>&1 # S439_SCANS_SMS_SCROLL`.
New tables, made by the code on first use (F-303): `purchase_scan_state`, `purchase_scan_alias`; new column `bank_sms_ignored.fields`;
new setting `bank_sms.s439_replay`. Restarts `clinic-finance` only. READ ONLY: `/root/assetapp/*`, `assets.db`, the web server's log.

## Proof
`walk_s439.py` — the REAL finance_app over scratch copies of finance.db and assets.db; its own rows keyed W439 (bills under its own
export md5 with suppliers whose names carry WALK, scans stamped W439-nn, SMS of its own amounts / from W439-SENDER), dates from today,
the door opened with the walk's own key file, the push door with the walk's own token: the forms of the real scans link by the named
rule; "43918112 (NOT04315878)" links by its last run while the bill numbered by the first run stays unscanned; year-off dates never
block; the buyer as vendor links by tail + amount; the misspelt vendor links and is learned once; `purchase_vendor_alias` untouched; a
second scan is marked and never linked; every link audited; the second run links 0; the six reasons on the page word for word and the
probable scan beside its bill; the push of a bill links the scan made before it; the command line; assets.db byte-identical · the door:
message/from, body/number (JSON), a raw body, the phone's `?<SMS>=<SMS>`, upper-case names, text/sender, the key in the address — all
stored; an OTP refused with "message,from,ts" kept; the key in no row; the page; the replay (its own log lines: stored with the log's
time, the empty note replaced, the macro's test post and a 401 line skipped, once only) · the page's script read as text: approve() calls
daysStay(), daysKeep() records → draws → restores in that order, ONE line left the parent's page. **Negative controls** on the box as it
is: none of the forms link, no reason column, the push links nothing, no command line; the old door refuses message/from, the raw body
and the bare query with an empty text and no field names; the old approve() calls load(). Then **S405's walk (29/29) and S403's walk
(52/52) re-run UNCHANGED** on the patched files, each against its own pre-kit control — S403's on the finance backup of 26-Sep 17:45
(S417's declaration) and, new here, the assets backup of 28-Sep 10:37: since reception's scanning every YUVIKA bill of September has a
real scan, so on today's assets.db that frozen walk picks another vendor's bill and goes red on the unpatched files too.
The scroll was also proven in a real browser before the install (headless Edge, a local harness serving the built page and the live
one over crafted days): 12 approvals down a month — new: the approved row stays where it was on the screen every time and the month
stays open; old: the row jumps (the month box back at its top) and the month closes after its last approval.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S439_SCANS_SMS_SCROLL/install_S439_SCANS_SMS_SCROLL.sh
```
Undo: put back the three `.bak_S439_<from8>` files, `crontab /root/finance/crontab.bak_S439_<stamp>`, `systemctl restart clinic-finance`,
healthz 200. The links, the two tables, the `fields` column and the replayed SMS rows are data an older file ignores or reads as before
(the older matcher recomputes its own links on its next run); `finance.db.bak_S439_<stamp>` only if the owner asks for them to be
reversed — say so first.
