# REPORT S440 — S440_SCAN_FLOW (D640 · F-662) · installed 30-Sep-2026 21:00 IST · published (see the foot)

## For the owner
- **Purchase orders now opens on "Scan ka kaam (25)"** — one list, a tap per line. Tonight it reads: **Scan karo 10** (bills nobody has
  scanned) · **Yahi bill hai? 8** (a scan is already here; staff tap "Haan, yahi hai" or "Nahi") · **Supplier chuno 3** (pick the supplier
  from a list) · **Amount milao 4** (type the amount printed on the paper) · **Marg ka intezaar 13** (nothing to do — they join by
  themselves after Amir's entry). Each scan line shows a small picture of the paper; tap it to open the scan.
- **The six bills reception was wrongly asked to scan again are gone from "Scan karo"** (L.K. 75904, 78354 · ESSENTIAL EP002243 ·
  SAISUN IP006767 · A.A. 416 · KEDAR 189). They now sit under "Yahi bill hai?" with one tap to confirm.
- **The scan page is camera-first:** one line on top ("Pharmacy purchase · September 2026 — badlo"), then Open camera / Choose photo, then
  the note; the explanation is folded under "Kaise?". After Save a green card says **"Ho gaya — B-0103 · bill par likh do"** with two big
  buttons: "Agla bill scan karo" and "← BACK to the list".
- **A big "← BACK" bar stays at the top and a round ↑ appears after one screen** on Purchase orders, the scan page, the stamp slip, the
  scan list, a bill, Scan lanes and your Scan links page. BACK returns to the page the person came from; opened on its own it goes to the
  portal's home. Staff see this bar instead of the register's menu; you and the manager keep the menu.
- **Two things for you to know.** (1) KEDAR bill A000163 is entered twice in Marg: it now shows once, and the extra entry is on the Wrong
  list for Amir (September will wait for him to remove it). (2) **"Scan ka kaam" opens for Alisha, Darpan, Shavez, Shivani and you — not
  for the shared login "reception"**, which has never had the Purchase orders page; 62 of the 82 medicine scans were made under that
  login. If reception should work this list under that login, say so and the chat gives it the page (one line).
- It works: every tap was tested on a copy of today's records, and the pages were run in a real browser before going live.

https://followup.dr-manoj.in/finance/porders
https://assets.dr-manoj.in/intake
https://followup.dr-manoj.in/finance/purchase/page/scans

## For the chat
**Kit** `deploy_kits/S440_SCAN_FLOW/` (11 files: `make_s440.py`, `porders_block_s440.py`, `purchase_block_s440.py`, `asset_block_s440.py`,
`walk_s440.py`, `walk_s409_s440.py`, `figures_s440.py`, `install_S440_SCAN_FLOW.sh`, `README.md`, `KIT_ID.txt`, `SUMS.md5`). Ran on the
box from `/tmp/s440run` — byte-identical to the repository kit (`diff -r` after the publish, the foot). Build lock
`/root/deploy/.claude_code_build.lock` taken 20:59:28 IST (owner S440_SCAN_FLOW), held through the install and this report. S438 was not built.

**What was read first (read-only, 20:06:44 IST, no lock held, services active, healthz 200)**
- `porders.py` is 64465af0, not the brief's 78d1712a ("unless moved" — it had; read live). `porders.html` 124c4d41, `purchase_app.py`
  ebe38c68 (S439's TO), `asset_register.py` 1f80773b (S435's TO), `sanjeevni_approvals.py` 3999c4ce, `scanner_widget.js` 4ae2d29a.
- The state S439 left: 80 pharmacy scans, 52 links, 28 open (amount differs 3 · already scanned 4 · no bill yet 11 · no digits 2 · bill
  number differs 5 · vendor unknown 3); 17 unscanned September bills, 6 with a near-match; KEDAR A000163 / a000163 twice (ids 503, 198).
- The asset app is one file with its templates inline; staff reach it as `/scanapp/…` on the followup site (the prefix is stripped) and the
  owner also on `assets.dr-manoj.in`. A portal staff login is the asset role `reception`, limited to the intake and its slip (A-D21).
- `unit_role`: the Purchase orders unit has makers alisha, darpan, shavez, shivani and checker manoj. The login `reception` has roles on
  `clinic` and `checks` only.

**Live files, FROM → TO (each md5 read back on the box after placing; verify at 21:00:57 IST)**
| file | FROM | TO |
|---|---|---|
| /root/finance/porders.py (5 anchored edits + the S440 block appended) | 64465af0835bdc5583ae7468cacc8c16 | e43adfb03f11b1b658805553b8441ae5 |
| /root/finance/porders.html (anchored) | 124c4d41b9491203899f324b8a194763 | 792aebbacc377198f7081b6129429f6f |
| /root/finance/purchase_app.py (the S440 block inserted + 10 anchored edits) | ebe38c681f323782f0a211d1d0879b24 | a51fe90eaa2922ba4e2b4db6388f797a |
| /root/assetapp/asset_register.py (PARENT'S; the S440 block inserted + anchored edits) | 1f80773b85583d0f9e3344b74b313389 | 0deaa531a412979d523ae0d4fd000946 |

Pins checked before touching (20:06, 20:38, under the lock at 20:59:28, and by the installer). Not changed, read back at their md5s:
`sanjeevni_approvals.py` 3999c4ce, `finance_app.py` ac24fc5e, `portal.py` 626838cd, `tile_grants.json` df73b84a, `scanner_widget.js`
4ae2d29a. Crontab not touched. **Restarted `clinic-finance` and `assetapp`** (both active since 21:00:22 IST); `clinic-portal` untouched
(active since 27-Sep 08:12).

**Backups:** `finance.db.bak_S440_20260930_205934` (backup API, 27,901,952 bytes), `assets.db.bak_S440_20260930_205934` (backup API,
188,416 bytes), and `porders.py.bak_S440_64465af0`, `porders.html.bak_S440_124c4d41`, `purchase_app.py.bak_S440_ebe38c68`,
`asset_register.py.bak_S440_1f80773b` — each read back at its FROM md5.

**Health after placing (21:00–21:02 IST):** local and public `/finance/healthz` 200; `/finance/porders`, `/finance/purchase/page/scans`,
the read door `/finance/porders/api/scan-status`, `/scanapp/intake`, `/scanapp/bills`, a thumbnail, `assets.dr-manoj.in/intake` — 302
without a login (the gate, expected); the asset app's login page 200. Journals since the restart: finance — only gunicorn's two "Worker
was sent SIGTERM" lines of the restart itself, nothing "NOT mounted"; assetapp — no traceback.

**The first pass and what reception sees (live database, 21:00:30 IST, who "install S440"; read again 21:01:52)**
`0 new link(s) · 52 links stored · 80 pharmacy scans · 28 still open` — the pass made the eight additive columns and named each scan's
likely bill. `Scan ka kaam (25): Scan karo 10 · Yahi bill hai? 8 · Supplier chuno 3 · Amount milao 4 · Marg ka intezaar 13 · second scans 4`.
- *Scan karo (10):* the September bills with no scan and no near-match waiting on them; KEDAR a000163 / A000163 shown ONCE.
- *Yahi bill hai? (8):* B-0033 (reads KT-475964) → L.K. 75904 · B-0042 (RT-47834) → L.K. 78354 · B-0048 (EP012243) → ESSENTIAL EP002243 ·
  B-0088 (6387) → SAISUN IP006767 · B-0080 (0000416, ₹2,304.50) → A.A. 416 (₹2,195) · B-0082 (A000189, ₹7,668) → KEDAR 189 (₹7,008) — the
  brief's six — and two whose bill already has a scan, asked as "yeh wahi kaagaz hai?": B-0041 → L.K. 783473 (has B-0029) · B-0078 →
  YUVIKA 634 (has B-0075).
- *Supplier chuno (3):* B-0054, B-0079, B-0100 (the brief's #54, #79, #100).
- *Amount milao (4):* B-0076 → KEDAR 185 (scan ₹16,760, Marg ₹18,700) · B-0077 → GUNINA 71226 (₹1,52,618 / ₹14,908) · B-0083 → SHIVAAZ
  3290 (₹1,885 / ₹1,108) · B-0086 → GUNINA 72975 (₹25,578 / ₹8,526) — S439's four PROBABLE links. The brief's "+ the 3 amount differs" are
  not linked yet, so they are asked "Yahi bill hai?" first (two of them above, the third is B-0078); once confirmed with amounts apart
  they arrive here.
- *The six near-matches:* 6 found · 0 in Scan karo · 6 in Yahi bill hai? · 0 linked (nobody has tapped yet: 0 decisions by a person).
- *The double entry:* bill id 503 (A000163) marked WRONG, wrong amount ₹0, by "S440 rule", reason "Marg mein do baar: bill a000163 aur
  A000163 (KEDAR PHARMACEUTICAL, 03-09-2026) -- ek entry hatao", audited `double_entry` once; id 198 (a000163) is the row shown. It is the
  only WRONG bill. The mark lifts by itself when the twin leaves Marg's exports.
- Audit since the install: `rematch` (install S440) 1 · `double_entry` (S440 rule) 1. No W440 row in either live database.

**The walk (`walk_s440.py`, in the install): `WALK_S440 GREEN -- 66 of 66 passed`** — the real finance app and the real asset app in one
process over scratch copies of finance.db and assets.db (backup API); 14 bills under its own export md5 of suppliers whose names carry
WALK, 36 scans stamped W440-01..36, two crafted papers (a PDF and a photo); every date from today; rows found by key.
- *The five groups (12):* each W440 bill or scan in exactly one group; the line's fields (supplier, number, date, amount, days waiting,
  the pre-filled link ending `from=%2Ffinance%2Fporders`; the scan's reading beside Marg's bill with thumbnail and PDF; the first scan's
  stamp on a second scan); the supplier list sorted; the count is groups 1–4; **each group renders exactly its buttons** (the page's
  script, group by group: 1 Scan only · 2 Haan / Nahi · 3 the drop-down · 4 the amount box · 5 none; Galat lane on 2–5); the answers
  redraw the list in place.
- *Yahi bill hai? (5):* a login of the unit that is not a sender reads but gets 403 "view_only" on all three doors; an answer naming
  another bill 409; Haan → CONFIRMED "reception confirmed", `scan_bill_id` set, audited with grade and rule; Nahi → the refusal kept, the
  bill back in Scan karo, the scan in group 5, audited; Haan on a scan whose bill has a scan → `dup`, the first scan named, no second link.
- *Supplier chuno (7):* a name off the list 400; the chosen supplier learned ONCE (one `purchase_scan_alias` row "S440 darpan chose for
  scan <id>", one `alias_learn`, one `scan_vendor_chosen`) and linked at once; the other scan with the same misspelling links without
  being asked; the buyer's own name never learned (kept for that scan, links); "List mein nahi hai" → group 5; a second answer 409.
- *Amount milao (5):* letters 400; = Marg → EXACT "paper amount = Marg (reception)", the paper amount in `purchase_scan_state`, assets.db
  still holding what OCR read; = the scan → WRONG by darpan with "bill 440912 YUVIWALK SURGICALS: paper Rs 2,500.39, Marg Rs 2,000.39",
  the link stays, audited `verdict` via "Scan ka kaam"; neither → "owner", nothing marked, the Needs-you line in the module and in the
  strip's API; an answered line 409.
- *Every pass keeps them (2):* after the Re-match button and the command line the CONFIRMED link, the EXACT-by-paper link, the refusal,
  the second scan, the paper amounts and the "not on the list" choice stand; the groups are the same.
- *Double entry, the real six, the counts (5):* A440202 / a440202 once, the extra row WRONG ₹0 by "S440 rule", audited once however often
  the list is read; **the six real near-matches, found by supplier and number: 6 found, 6 in "Yahi bill hai?", 0 in Scan karo**; the list
  = the summary's `scan_kaam` = the owner's page, group by group; the five groups once on the owner's page; the read door's three words.
- *BACK, the arrow, the menu (5):* the bar once, "← BACK" once, the arrow once on Purchase orders, Scan links, and 12 renderings of the
  asset app's intake / list / bill / Scan lanes; `?from=` honoured; `https://evil…` and `//evil…` refused → `/portal`; from the assets
  host the hub is the followup site's; the slip carries the bar; the menu absent for darpan and sukhveer, present for owner and manager.
- *Intake, Save card, pre-fill (8):* in the DOM the line, THE SCANNER, then the two drop-downs (a box hidden until "badlo"), the note,
  "Kaise?", the basic upload; the line pre-set; the three paragraphs word for word; opened from a Scan karo line the bar names the bill
  and S403's fields ride the scanner; a real save through `/intake/submit` lands Pharmacy / captured with the pre-filled fields and goes
  to the slip; the card ("Ho gaya", the stamp, "bill par likh do", the two buttons, still polling); today's scans below; the saved paper
  linked EXACT at once and its bill left Scan karo.
- *The list and what stays shut (11):* my lane, this month, 25 rows, "aur dikhao"; only own scans; rejected and old drafts folded; the
  four words (with the link); "Scan ho gaya" when the door cannot be asked; the owner's list unchanged; the staff bill page read-only;
  another person's bill, a clinic paper's picture, a rejected scan's picture, /lanes, /purchases, approve, the duplicate taps, the month —
  403 each; any live pharmacy scan's picture open (PDF and photo → PNG); **Galat lane** moves a captured pharmacy scan to clinic, audited
  (who, from → to, "via Scan ka kaam"), gone from the list and from Scan ka kaam; into pharmacy / the owner's lane, a non-pharmacy or a
  rejected paper — 403; the three counts agree at the end.
**Negative control (6, the unpatched files over the same crafted rows):** no `kaam`, the near-match bills asked for again, the double
twice; **the six real near-matches all still in "Bill scans pending"**; no bar or arrow on Purchase orders / Scan links, no read door
(404), no confirm door; the old intake — no bar, the header shown to a scanning login, the camera BELOW the drop-downs and the note, no
"Kaise?"; the list and the bill 403, no thumbnail route, the slip says "Scan another"; the owner's old pages carry the header, no bar.

**Earlier walks re-run on the patched files, each against its own pre-kit control (in the install):**
S439 `55 of 55` UNCHANGED · S403 `52/52` UNCHANGED · S435 `WALK OK` UNCHANGED (not asked by the brief; it is the last kit on the same
file) · **S409 `24/24` with TWO assertions adjusted**, each named in `walk_s409_s440.py` (S409's folder is not edited: its walk is copied
to scratch and two anchored replacements are made on the copy):
- A1 "reception reaches only its routes: /bills 403, /lanes 403, /intake 200, a bill view 403" → `[200, 403, 200, 200]` (its own list and
  its own bill are readable since S440).
- A2 the closing control "the old app's reception gate … and stays so" → the old app `[403, 200]` as it was; the new app's /bills 200.
- The brief expected "assertions on the intake's order" to need adjusting: none did (S409 asserts the selected lane and the "never
  scanned again" text; both are kept). Its refusal of a reception re-lane (403 on a clinic paper) also stands unadjusted.
Declared data for those walks: S403's on the two backups S439 declared; **S439's on `finance.db.bak_S439_20260930_134133`** — the first
dry run showed its negative control red 1 of 55 ("the old door keeps no field names" asserts the `fields` column absent, and S439's own
install added it to the live database). Nothing to do with S440; on that backup it is 55 of 55.

**In a real browser before the install (local, scratch, not in the kit):** headless Edge in real time over a harness serving the built
files. Purchase orders (a saved state of the scratch copy): the bar stays at the top while scrolled (top 0), BACK 44px high; `?from=`
honoured, `//evil…` → `/portal`; a real scroll fires the listener and shows the 48px arrow; a tap scrolls smoothly to the top and hides
it; Haan / Nahi / a supplier / an amount post `{scan, bill, yes}` / `{scan, vendor}` / `{scan, paper}` and the page offset does not move
(1691 → 1691); nothing chosen or "12a" gives the Hindi message and no post; a missing thumbnail hides itself; the old page has no bar.
The asset app (the built file over an empty scratch database, a crafted scanning login): the scanner is the first thing under the line
(top 145px; the note 429, "Kaise?" 499); "badlo" opens the drop-downs under the line and ABOVE the scanner while they follow it in the
DOM; changing the kind or the month rewrites the line and the scanner's fields; the list shows 25 rows and "aur dikhao"; the owner's
list keeps its header under the bar. Virtual-time headless does not make frames, so the scroll parts were run in real time. The Browser
pane refused the local address, so it was not used. **No page was opened under a real login** (no password is entered from here).

**Dry runs before the install (DRY=1, no lock needed — nothing placed), two.** (1) red at S439's re-run for the reason above → its scratch
is S439's own backup. (2) green throughout; the figures on a fresh scratch copy equal the live figures above. Before them, three runs of
this kit's walk alone on scratch, two (the first 59 of 66, the second 66 of 66): every miss was the walk's own — a confirm left in the
common part ran on the new side too; "bhati" has no role on the unit (the view-only case is now a maker taken off the senders list);
`unscanned_bills` rounds the amount to the rupee; the slip's card carries its own "← BACK to the list" — and one in the build: the
page's comment contained "← BACK" (the bar's text must occur once), reworded.

**Calls made where the brief left room**
- **The read door is `/finance/porders/api/scan-status`**, not `/finance/purchase/api/scan-status`: the scanning logins hold a role on the
  Purchase orders unit and none on `/finance/purchase` (the gate resolves the unit from the path; `finance_app.py` is not in the brief).
  The asset app asks it server-side over the loopback with the person's own portal cookie (3s, fail-soft: "Scan ho gaya").
- **"A scanning login" is the asset role `reception`** (every portal staff login) — not the S409 lane table, which lists the owner and
  leaves out Alisha and Shivani, who scan. Owner and manager keep the menu.
- **A-D21 widened, narrowly** (the parent's rule): a scanning login may read its OWN list and OWN bills, see the picture of any live
  pharmacy scan, and move a captured pharmacy scan to clinic / lab purchase / other document. Nothing else; the walk proves each refusal.
- **Eight additive columns**, not three: `likely_bill, confirmed_by, confirmed_at, paper_amount, chosen_vendor, hint_no, amount_state, dup_ok`.
- **The drop-downs follow the scanner in the DOM** (the brief's walk line) and are shown under the line when opened (CSS order).
- **The buyer's own name is never learned** as a supplier's spelling. **A near-match whose bill already has a scan** is asked, not hidden.
- **"No amount read, the same number"** (S439's no-digits reason with a likely bill) is asked as "Yahi bill hai?" too; none today.
- **The extra row of a double entry is the one without a scan link**, else the later id; marked only when it carries no verdict and its
  month is not final.
- **The supplier list** is every supplier on Marg's live bills (their `supplier_key`), sorted.
- **"Marg galat" is refused into "Dr sahab ko dikhao"** when the bill already carries a verdict or its month is final (S371 refuses a
  verdict on a final month).

**Not done, and why**
- **The portal's tile line ("Scan ka kaam 9").** The Purchase orders tile's text is fixed in `portal.py` (the clinic side's, not in the
  brief). The count is served (`scan_kaam` in `/finance/porders/api/summary`) and shown on the section, the owner's page and Needs you;
  wiring the tile is one small change in `portal.py` for a brief that names it.
- **Amir's own page.** "Amir's corrections list" is the S371 WRONG mark (month page, pay sheet, the month's open reason); `amir_day.py`
  is not in the brief and lists no WRONG bills.
- **S403's Needs-you line "Bill scan pending on N purchase bills"** still counts every bill with no link (17), as does the month-end
  checklist (`packs.py` reads `unscanned_bills`): S403's walk pins the line and the brief does not name it. Scan karo reads 10.

**Outside the brief — noticed, not touched**
- **The shared login `reception` has no role on the Purchase orders unit** (`unit_role`: clinic, checks). 62 of the 82 pharmacy scans
  and 22 of the 28 open ones are its. Under that login: Purchase orders does not open (before and after this kit); the scan list shows
  "Scan ho gaya" instead of the four words; and "← BACK to the list" on a pharmacy slip opened without `?from=` leads to a page it cannot
  open. One `unit_role` row (porders · reception · maker) and its name in `porders.senders` cures all three; the owner's call.
- **The scanner widget draws its own small "← back"** inside the scanner card (to the last slip; `scanner_widget.js`, not in the brief).
  With the bar above it there are now two; the widget's could go in a brief that names it.
- **The asset app's checker routes redirect to `request.form["back"]` unchecked** (`bill_lane`, `bill_month_set`, `bill_dup` for owner /
  manager — existing code). The new staff path and both bars accept a path inside the site only.
- **A thumbnail is made on each request** (pdftoppm / ImageMagick, about 47–81 KB; cached by the browser for a day). 28 lines today; if
  the list grows large a stored thumbnail would be kinder to the box.
- **One command was refused by the permission list:** a single PowerShell line that bundled a local edit script (its text carried the
  installer's own `rm -rf "$WALK"`), the kit upload and an `ssh` that removed one scratch file on the server. It was not re-spelt: the
  edit was made with the file editor, the upload and the read ran as separate commands, and the removal was left out.
- `PUBLISH_ALL` published everything pending: this kit and the chat's brief `S440_SCAN_FLOW.md` (the gate read 12 files: clean).
- The kit's README says its reading was at "20:06 IST": read 20:06:44.

**Undo:** the four `.bak_S440_<from8>` files back, `systemctl restart clinic-finance assetapp`, healthz 200, md5s read back. The eight
columns, any CONFIRMED link, learned spelling and the WRONG mark on bill 503 are data; the older matcher ignores the columns and
re-judges a CONFIRMED link by its own rules on its next pass. The mark on bill 503 is lifted by hand on the month page ("Correct") or by
`finance.db.bak_S440_20260930_205934` — the database backup only if the owner asks for the answers to be reversed; say so first.

**After the publish (21:01–21:05 IST):** repository published with `PUBLISH_ALL.bat` (gate clean over 12 files, commit `24829c5` on main,
origin verified); on the box `git pull --ff-only` → HEAD 24829c5 (21:01:50); `deploy_kits/S440_SCAN_FLOW/` SUMS.md5 10 of 10 OK; `diff -r`
repo kit vs `/tmp/s440run` (what ran): byte-identical; the repository's own installer run from `/root/deploy/repo`: "ALREADY INSTALLED:
the four files are at the kit's pins; clinic-finance active · assetapp active · healthz 200"; public healthz 200; no `__pycache__` in the
repository's kits; the build lock released 21:04:44 IST (the four md5s and healthz read once more with it); the build's scratch in the
server's /tmp (the walk's copies of the two databases, the kit copies) removed 21:04:55. This report is published in a second commit.
