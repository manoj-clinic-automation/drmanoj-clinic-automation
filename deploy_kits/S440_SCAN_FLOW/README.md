# S440_SCAN_FLOW — "Scan ka kaam": one list, a tap per line · BACK and the up-arrow on every page of the scan flow · the intake camera-first (D640 · F-662)

**Sanjeevni project · session 283 · 30-Sep-2026 · brief `claude_code_briefs/S440_SCAN_FLOW.md` · runs after S439 (live 30-Sep 13:42 IST).**
Staff pages in Hindi (Roman script), the owner's in English. The asset app (`/root/assetapp/asset_register.py`) is the PARENT'S — declared
in the brief: its intake, stamp slip, Purchases list, bill page, Scan lanes and base layout are changed here. S438_COUNT_BOOK stays held.

## What the owner said (30-Sep)
"Whatever needs to be done should be clearly mentioned in the staff scan app — as with 'Bill scan karo' and then 'Scan' and there they tap
'scanned'. The scans with no readable supplier should be flagged the same way … a back-to-top float on long pages, a prominent BACK button
at the top for good navigation, and easy flow. I need this system working properly to shift to it."

## What was built
**3.1 Scan ka kaam — `porders.py` (the block `porders_block_s440.py`, appended) · `porders.html` · `purchase_app.py`.**
Section 3 of Purchase orders is "Scan ka kaam (N)". `porders.scan_work(con)` sorts every unscanned Marg bill and every open pharmacy scan
into exactly one of five groups; `state()` carries them as `kaam` (S403's own `scans` list stays, unchanged — the month-end checklist and
the earlier walks read it).
1. **Scan karo** — a Marg bill with no scan and no near-match waiting on it: 📷 Scan (S403's pre-filled intake; the link now ends
   `from=/finance/porders`). Marg's double entry (the same number in two cases, the same supplier, date, amount) shows ONCE with "Marg mein
   do baar — Amir ko batao"; its extra row is marked WRONG, "should be ₹0", by "S440 rule" — the S371 mark, so it stands on the month page
   and the pay sheet and holds the month open until Amir removes it in Marg (audited `double_entry`, once; lifted when the twin is gone).
2. **Yahi bill hai?** — the matcher's likely bill for a scan (S439's "bill number differs" / "amount differs" / "no amount read", now kept
   as `likely_bill`). **Haan, yahi hai** links it: grade CONFIRMED, "reception confirmed", `scan_bill_id` set, audited `scan_link`. When
   that bill ALREADY has a scan the line says so and Haan marks the paper a second scan of it (never a second link; audited
   `scan_dup_confirmed`). **Nahi** keeps the refusal (`hint_no`): that bill is never offered to that scan again and returns to Scan karo.
3. **Supplier chuno** — a scan whose vendor nobody could read: the supplier list (every supplier on Marg's live bills), the scan's number
   and amount. **Yeh supplier hai** keeps the choice for that scan (`chosen_vendor`), learns the spelling once in `purchase_scan_alias`
   (audited `alias_learn` "S440 <login> chose for scan <id>") and runs the matcher at once; "List mein nahi hai" sends the line to group 5.
4. **Amount milao** — a linked scan whose amount is more than 2% (and ₹1) off Marg's: both figures, one box for the amount ON THE PAPER.
   = Marg → **Scan galat padha**: the link becomes EXACT ("paper amount = Marg (reception)"), the paper amount is kept in
   `purchase_scan_state` — never in assets.db. = the scan → **Marg galat**: the bill is marked WRONG with the paper's amount and the reason
   "bill <no> <supplier>: paper Rs X, Marg Rs Y (Scan ka kaam, <login>)" (the S371 path; audited `verdict`, via "Scan ka kaam"); the link
   stays. Neither (or the bill already carries a verdict, or its month is final) → **Dr sahab ko dikhao**: a Needs-you line for the owner
   ("Scan amount to settle: bill … — the paper reads …, Marg …") through the hook `sanjeevni_approvals.py` already calls.
5. **Marg ka intezaar** — a scan of a bill Marg has not sent: no button, "Amir ke entry ke baad khud jud jayega", folded under its count.
**Galat lane** on every scan line (groups 2–5): a plain form to the asset app's re-lane. Each scan line carries a thumbnail (tap = the PDF).
The matcher (`purchase_app._rematch`) now KEEPS what a person decided: it used to delete `purchase_scan_state` and write it again, so the
decisions ride in eight additive columns (`likely_bill, confirmed_by, confirmed_at, paper_amount, chosen_vendor, hint_no, amount_state,
dup_ok`), a CONFIRMED link is never re-judged, a refused bill is never matched or hinted again, and a linked scan keeps its row.
The counts: `GET /finance/porders/api/summary` gains `scan_kaam`; the owner's Scan links page shows the same five groups read-only above
its tables. The read door `GET /finance/porders/api/scan-status?ids=` (inside the unit's login gate, read-only) answers in staff words.

**3.2 BACK and the up-arrow.** One sticky bar — "← BACK" (44px, the wide tap area on a phone) to the page the person came from (`?from=`,
a path inside the site only; else the portal's hub `/portal`), the page's name on the right — and a floating 48px up-arrow after one
screen of scroll (smooth to the top), on: Purchase orders, the owner's Scan links, and in the asset app the intake, the stamp slip, the
Purchases list, a bill, Scan lanes. A scanning login sees the bar INSTEAD of the register's menu; owner and manager keep the menu.

**3.3 The intake, camera first.** The bar · one line "Pharmacy purchase · September 2026 — badlo" · the scanner (Open camera / Choose
photo) · the note · "Kaise? ▾" with the three existing paragraphs word for word · the basic upload · today's scans. The two drop-downs sit
AFTER the scanner in the DOM, in a box that opens only on "badlo" (shown right under the line). Opened from a Scan karo line the bar names
the bill; S403's pre-fill is untouched. **After Save** the slip is a green card "Ho gaya — B-0103 · bill par likh do" with
**Agla bill scan karo** (the intake again, the same lane) and **← BACK to the list**; today's scans below it, the status in staff words.

**3.4 A scanning login's list** (`/bills` for role `reception`): what it scanned itself, its own lane, this month, 25 rows, "aur dikhao";
the search and the two filters stay; Status in staff words — *Marg se mil gaya · Marg ka intezaar (Amir) · Aapka jawab chahiye → Scan ka
kaam* (a link) *· Doosri baar scan (B-00xx)*; rejected scans and drafts of an earlier month under "purane drafts (N) ▾". Its bill page is
read-only. The owner's and the manager's list and bill page are unchanged but for the bar and the arrow.

## Calls made where the brief left room (each is in the report)
- **The read door is `/finance/porders/api/scan-status`, not `/finance/purchase/api/…`**: the scanning logins hold a role on the Purchase
  orders unit and none on `/finance/purchase`; the gate (`finance_app.py`) is not in the brief. The asset app asks it server-side, over the
  loopback, with the person's own portal cookie; when it cannot be asked the list says "Scan ho gaya".
- **"A scanning login" = the asset app's role `reception`** (every portal staff login), not the S409 lane table: that table also lists the
  owner, and leaves out reception staff who scan daily. Owner and manager keep the menu.
- **A-D21 is widened narrowly** (the parent's rule that reception reaches only the intake): a scanning login may read the list of what it
  scanned ITSELF and those bills; see the picture of any live pharmacy scan (the line on Purchase orders shows it); and move a CAPTURED
  PHARMACY scan to clinic / lab purchase / other document. Everything else stays 403 — the walk proves each.
- **More than the brief's three columns** on `purchase_scan_state` (eight, all additive): the refusal, the second-scan answer, the owner's
  pending amount and the likely bill have to survive a pass too.
- **The buyer's own name is never learned as a supplier's spelling**: the choice is kept for that scan only.
- **A near-match whose bill already has a scan** is asked as "yeh wahi kaagaz hai?" rather than hidden.
- **The tile line**: the portal's Purchase orders tile is a fixed text in `portal.py` (the clinic side's file, not in the brief). The count
  is served (`scan_kaam` in the summary) and shown on the section, the owner's page and Needs you; the tile itself is not touched.
- **Amir's corrections list** is the S371 WRONG mark (month page, pay sheet, the month's "marked Wrong and not yet resolved" reason);
  `amir_day.py` is not in the brief and is not touched.

## Pins (FROM read on the box 30-Sep-2026 20:06 IST → TO; built by `make_s440.py` from the live bytes, every anchor exactly once)
| file | FROM | TO |
|---|---|---|
| /root/finance/porders.py (read live — the brief's 78d1712a had moved) | 64465af0835bdc5583ae7468cacc8c16 | e43adfb03f11b1b658805553b8441ae5 |
| /root/finance/porders.html | 124c4d41b9491203899f324b8a194763 | 792aebbacc377198f7081b6129429f6f |
| /root/finance/purchase_app.py (S439's TO) | ebe38c681f323782f0a211d1d0879b24 | a51fe90eaa2922ba4e2b4db6388f797a |
| /root/assetapp/asset_register.py (PARENT'S; S435's TO) | 1f80773b85583d0f9e3344b74b313389 | 0deaa531a412979d523ae0d4fd000946 |

Not changed: `sanjeevni_approvals.py` (its existing hook carries the new Needs-you line), `scanner_widget.js`, `finance_app.py`, `portal.py`,
`tile_grants.json`, crontab. Data: eight additive columns on `purchase_scan_state` (made by the first pass). assets.db: no schema change.
Restarts `clinic-finance` and `assetapp`.

## Proof
`walk_s440.py` — the REAL finance app and the REAL asset app in one process over scratch copies of finance.db and assets.db; its own rows
keyed W440 (14 bills under its own export md5 of suppliers whose names carry WALK, 36 scans stamped W440-nn, two crafted papers), dates
from today; 66 checks: the five groups and each line's fields; each group's buttons and no other; a non-sender may read and not answer;
Haan / Nahi / the second scan; the supplier learned once, the buyer never learned; the three amount outcomes; the decisions after two
more passes; the double entry once, marked once; the six real near-matches, found by supplier and number, all in "Yahi bill hai?" and
none in Scan karo; the list, the summary and the owner's page agree; the bar once and the arrow once on every named page, `?from=`
honoured, another host refused; the menu; the intake's order in the DOM; the pre-fill; a real save through the intake's route, its Save
card, and the bill gone from Scan karo; the list (25, my lane, this month, the four words, the fold); what stays shut; Galat lane.
**Negative controls** on the box as it is: no `kaam`, the near-match bills still asked for, the six still in "Bill scans pending", no bar
anywhere, the camera below the drop-downs, the list and the bill refused, no thumbnail route, the old slip.
Then, on the patched files, each against its own pre-kit control: **S439's walk 55/55 UNCHANGED** (on the finance backup S439 took: its
negative control asserts the old SMS door has no `fields` column, which S439 itself added to the live database), **S403's walk 52/52
UNCHANGED** (on the backups S439 declared), **S435's walk UNCHANGED**, and **S409's walk 24/24 with TWO assertions adjusted**, each named
in `walk_s409_s440.py`: A1 "reception reaches only its routes: /bills 403 … a bill view 403" → its own list and own bill are 200;
A2 the same fact in the closing negative control. (The brief expected assertions on the intake's order to need adjusting; none did —
S409 asserts the selected lane and the "never scanned again" text, both kept.)
The pages were also run in a real browser before the install (headless Edge in real time, a local harness over the built files): the bar
stays at the top while the page scrolls; a real scroll shows the arrow, a tap takes the page to the top and hides it; Haan / Nahi / the
supplier / the amount post what the doors expect and the page stays where it was; a missing thumbnail hides itself; on the intake
"badlo" opens the two drop-downs under the line and above the scanner, and the line follows the choice.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S440_SCAN_FLOW/install_S440_SCAN_FLOW.sh
```
Undo: put back the four `.bak_S440_<from8>` files, `systemctl restart clinic-finance assetapp`, healthz 200, read the md5s back. The
additive columns, the CONFIRMED links, the learned spellings and the WRONG marks are data: the older matcher re-judges a CONFIRMED link by
its own rules on its next pass and ignores the columns. `finance.db.bak_S440_<stamp>` / `assets.db.bak_S440_<stamp>` only if the owner
asks for the answers themselves to be reversed — say so first.
