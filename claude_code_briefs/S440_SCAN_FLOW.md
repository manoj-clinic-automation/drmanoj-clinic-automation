# Claude Code brief — S440_SCAN_FLOW (the scan flow finished for staff: one "Scan ka kaam" list with a tap for everything a person must decide; BACK at the top and an up-arrow on every page; the camera first)

Written 30-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S440 · decision D640 · fault F-662** (claimed on the System
Board). Runs AFTER S439 (live 30-Sep 13:42 IST). **Staff pages Hindi (Roman), owner pages English.** Touches `porders.py` / `porders.html`
(S403, Sanjeevni), `purchase_app.py` (S439's TO, Sanjeevni) and — **DECLARED, the parent's** — the asset app's intake page, its Purchases list
and its base layout (`/root/assetapp/`, S409/S435 files: read live). Restarts `clinic-finance` and `assetapp`. **S438_COUNT_BOOK stays HELD.**

## 1 · The owner's words (30-Sep)
"Whatever needs to be done should be clearly mentioned in the staff scan app — as with 'Bill scan karo' and then 'Scan' and there they tap
'scanned'. The scans with no readable supplier should be flagged the same way." "A back-to-top float on long pages, a prominent BACK button at
the top for good navigation, and easy flow." The BACK button reads **← BACK** (English, on every page, staff and owner). "I need this system
working properly to shift to it."

## 2 · What the chat read on the live pages (30-Sep, F-662) — REPORT first, then fix
- **Reception's Purchase orders** (`/finance/porders`): "Bill scans pending (17)" still lists the SIX bills whose scan exists and is a
  near-match (SAISUN IP006767 · KEDAR 189 · A.A. 416 · ESSENTIAL EP002243 · L.K. 78354 · L.K. 75904) — the S439 "probably this scan" note is on
  the owner's Scan links page only; and KEDAR 163 twice (Marg's double entry `A000163` / `a000163`). No back button, no top float, ~4 screens.
- **The asset app's intake** (`/intake`, the reception's Scan): three paragraphs, the kind drop-down and the month drop-down come BEFORE the
  camera — on a phone the camera button is below the fold; the only "← back" is inside the scanner block; after Save the staff stay on the
  intake under the Asset Register's own menu (Dashboard · Assets · Renewals · Drafts · Staff · Vendors · Admin) with no way back to the list
  and no sign that the bill they came for is done. "Recent stamped submissions" says "captured · open" for every row — nothing a staff
  member can act on.
- **The asset app's Purchases list** (`/bills`): 103 rows on one page (~7 screens), drafts first (B-0005/B-0008 with no vendor, one dated
  2026-11-10 by a misread), no default to the login's own lane, no back-to-top.
- **A misread scan has no correction**: #100 read "BAAS PLASMA DISTRIBUTORS · GST/2023-24/412 · 20-May-2023" — the paper is BASS PHARMA, the
  GST line was taken as the bill number and its year as the date. Not scan quality: the reader picked the wrong line. Nobody can fix it today
  except by re-scanning.
- **Owner's Scan links page**: three long tables, the hub strip at the top, no back-to-top.

## 3 · The build (D640)

### 3.1 "Scan ka kaam" — ONE list on reception's Purchase orders page, a tap per line
The section **"Scan ka kaam (N)"** replaces "Bill scans pending"; every line shows the supplier, bill number, date, amount, the days waiting,
and — where a scan exists — a thumbnail of the scan (tap = the PDF). Five kinds of line, each with its own buttons and nothing else:
1. **Scan karo** — a Marg bill with no scan and no near-match: **📷 Scan** (the S403 pre-filled intake, unchanged). Marg's double entries
   (same number in two cases, same supplier, date, amount) show ONCE with "Marg mein do baar — Amir ko batao" and go on Amir's corrections list.
2. **Yahi bill hai?** — a near-match (S439 `purchase_scan_state` reason "bill number differs" / "amount differs" with a likely bill): the scan's
   reading and Marg's bill side by side; **Haan, yahi hai** links it (audited "reception confirmed", grade CONFIRMED, `scan_bill_id` set) and
   the line disappears; **Nahi** clears the hint and the bill goes back to Scan karo. These six leave "Scan karo" at install.
3. **Supplier chuno** — a captured scan whose vendor is unknown/unread (#54, #79, #100 today): a drop-down of the supplier list (S403 list +
   `purchase_scan_alias`), the scan's number and amount shown; **Yeh supplier hai** stores the choice as a learned alias for that scan's OCR
   text (`purchase_scan_alias`, audited) and re-matches at once; if still no bill, the line becomes "Marg ka intezaar" (kind 5).
4. **Amount milao** — the scan and Marg disagree on the amount (S439's 4 PROBABLE `bill_tail+vendor` links + the 3 "amount differs"): the
   two figures shown; the staff types the amount ON THE PAPER (digits only, one box); equal to the scan → **Marg galat** → one row on
   Amir's corrections list (the S371 WRONG path: "bill <no> <supplier>: paper Rs X, Marg Rs Y"), the link stays; equal to Marg → **Scan galat
   padha** → the link becomes EXACT and the scan's amount is corrected in `purchase_scan_state` (never in assets.db); neither → "Dr sahab ko
   dikhao" (Needs-you line for the owner).
5. **Marg ka intezaar** — a scan of a bill not in Marg yet (the 25–29 Sep ones): no button, "Amir ke entry ke baad khud jud jayega"; one line
   per scan, collapsed under a count. **Galat lane** on every scan line (kinds 2–5): moves the paper out of the pharmacy lane (the S409 re-lane,
   as the intake does), audited.
The counts feed the tile line ("Scan ka kaam 9") and the owner's Scan links page, which shows the same five groups read-only, plus its tables.

### 3.2 BACK and the up-arrow — every page of the flow, both apps
- A **sticky top bar** on: Purchase orders, the asset app's intake, its Purchases list, its bill page, Scan lanes, and the owner's Scan links:
  left a large button **← BACK** (44px tall, full-width tap area on a phone) that goes to the page the staff came from (`?from=` carried by
  every link in this flow; else the portal's tile hub `/portal`); right the page's name. Nothing else in the bar.
- A **floating ↑** (bottom-right, 48px, appears after one screen of scroll, smooth scroll to top) on every page above.
- The asset app's menu stays for the owner/admin logins; for reception/darpan/sukhveer the intake, list and bill pages show the BACK bar
  instead of the register menu (role read from the S409 lane table's login list; everyone else keeps the menu).

### 3.3 The intake — camera first (the asset app, PARENT'S, declared)
Order on the page: the BACK bar · one line **"Pharmacy purchase · September 2026 — badlo"** (kind and month pre-set from the login's lane and
today, the two drop-downs open only on "badlo") · **📷 Open camera** and **Choose photo** as the first thing visible · the note box · the
explanation folded under **"Kaise? ▾"** (the existing text, unchanged). When the intake was opened from a Scan karo line, the bar shows that
bill ("DEEPAM 545 · Rs 14,442") and the vendor/number/amount pre-fill stays as S403 built it.
**After Save**: a full-width green card **"Ho gaya — B-0103 · bill par likh do"** with two big buttons: **Agla bill scan karo** (the intake
again, same lane) and **← BACK to the list** (Purchase orders, the line already gone). "Recent stamped submissions" moves below the card,
limited to today's, with the status in staff words (3.4).

### 3.4 The Purchases list (the asset app, PARENT'S, declared) — for the scanning logins
Opens on **my lane · this month**, 25 rows, **"aur dikhao"** for more; the filters stay. A **Status** column in staff words from
`purchase_scan_state` / `purchase_scan_link` (read through finance's read door `/finance/purchase/api/scan-status?ids=` — new, token-less
inside the same login gate, read-only): *Marg se mil gaya* · *Marg ka intezaar (Amir)* · *Aapka jawab chahiye → Scan ka kaam* · *Doosri
baar scan (B-00xx)*. Drafts and rejected rows are collapsed under **"purane drafts (4) ▾"**. The owner's view of the list is unchanged.

### 3.5 Settings — none new. The lane→login list of S409 is the role source; no new table beyond `purchase_scan_state` columns (`confirmed_by`,
`paper_amount`, `chosen_vendor`) — additive.

## 4 · Pins — read live after S439: porders.py 78d1712a (S403's TO unless moved — read live) / porders.html, purchase_app.py ebe38c68 (S439),
sanjeevni_approvals.py (the Needs-you line via its existing hook), the owner's Scan links page (S439's); PARENT'S, declared: the asset app's
intake template, bills list template, base layout and `asset_register.py` 1f80773b (S435's TO — read live; the re-lane and the Save card).
assets.db: READ ONLY for links; the re-lane writes as the S409 intake already does. Restarts `clinic-finance` and `assetapp`.

## 5 · Walk (scratch copies of finance.db and assets.db; rows keyed W440*; the real apps through Flask's test client)
Scan ka kaam: each of the five kinds renders exactly its buttons and no other; Haan links (audited, `scan_bill_id` set) and the bill leaves
Scan karo; Nahi clears the hint; Supplier chuno learns the alias once and re-matches; Amount milao's three outcomes (Marg wrong → the
corrections row; scan wrong → EXACT + corrected amount; neither → Needs-you); Galat lane moves the row and it vanishes from the pharmacy list;
Marg's double entry shows once; the six real near-matches are gone from Scan karo at install (the count reads 10 + the double); the tile
count and the owner's page agree with the list · BACK bar and ↑ present on every named page (the rendered HTML contains the bar once, the
button text "← BACK", the `?from=` honoured, the hub fallback); the register menu absent for a scanning login and present for the owner ·
intake: the camera buttons precede the drop-downs in the DOM, the kind/month line pre-set, "Kaise?" folded, the Save card with its two
buttons; the pre-fill of S403 intact · the list: 25 rows, my lane, this month, the status column's four words, drafts collapsed · S439 55/55,
S403 52/52, S409's walk re-run green (assertions on the intake's order adjusted, each named); negative control (old files: no bar, camera
below the drop-downs, the six still in Bill scans pending); dates from today.

## 6 · Done means
Kit `deploy_kits\S440_SCAN_FLOW\` · installed · published · `claude_code_briefs\REPORT_S440.md` — owner lines first: what reception sees on
opening Purchase orders (the five counts today), the intake in three lines, the six near-matches gone, where BACK goes on each page; ending
with `https://followup.dr-manoj.in/finance/porders`, `https://assets.dr-manoj.in/intake` and `https://followup.dr-manoj.in/finance/purchase/page/scans`.
