# S409_SCAN_LANES — whoever holds the paper scans it: five lanes, a duplicate guard, late bills, pharmacy scans from 01-Sep

**Session 283 · 26-Sep-2026 · decision D625 · fault F-633. OWNER OF THIS KIT: PARENT (the asset app, `/root/assetapp`).**
Two edits on the Sanjeevni side (`purchase_app.py`, `porders.py`: the scan-from date) are Sanjeevni's and are declared below.
Fourth of the five-brief paste, after S407 and before S408 (S408 reads the lanes).

## What the owner asked for (26-Sep)
"Medicine purchase, lab bill purchase, my expense files are all planned to be scanned; any bill or document arriving at reception is
scanned by reception and gets a number they write on it. X-ray films may go to the staff directly; lab ones to Sukhveer; some bills
arrive late. Should Sukhveer, Shavez and I scan too — and what if a bill is scanned twice?" Agreed: **whoever holds the paper scans it
at once and writes the number on it; a paper already carrying a B-number is never scanned again; each person's drop-down opens on
their own head; the server catches duplicates; late bills file by their own date; Sanjeevni purchase bill scanning starts from 1st
September.**

## What was built (asset_register.py, from its live bytes)
1. **Five lanes**, one select on the same intake (`/scanapp/intake`), stored in the new column `bills.lane` (backfilled: kind Pharmacy →
   `pharmacy`, everything else → `clinic`):
   | lane | label the staff see | kind | status | goes to |
   |---|---|---|---|---|
   | clinic | Clinic bill — asset or consumable | Consumable | draft | the checker's approval queue → spend / assets / expiries (as today) |
   | pharmacy | Pharmacy purchase — Sanjeevni | Pharmacy | captured | the Marg match (as today; S403's pre-fill still lands) |
   | lab_purchase | Lab purchase — NK Pathology | Lab | captured | filed; S408's lab bundle |
   | owner_expense | Dr MK expense | Expense | captured | filed; S408's expense bundle |
   | other_doc | Other document — not a bill | Document | captured | filed |
   Only `clinic` enters the approval queue, the spend and the expiries: every `/purchases` query filters `status='approved'` and a
   captured row can never be approved (`bill_approve` refuses anything but a draft) — S219's reasoning, unchanged and asserted in the walk.
   **Per-user default lane:** table `user_lane_default` (seeded sukhveer → lab_purchase, awdhesh → clinic, darpan → pharmacy,
   manoj → owner_expense; everyone else clinic; the app falls back to the same list); the owner edits it on **`/scanapp/lanes`**
   (linked from the Purchases list). The select opens on it; the basic upload and the scanner's upload fields carry it.
2. **Duplicate guard at capture, two layers.**
   (a) **Image fingerprint** `bills.fp`: the app's python has no Pillow, so the flattened first page is rendered small and grey by
   `pdftoppm` (PDF) or ImageMagick `convert` (image) and a 64-bit **perceptual difference hash (dHash)** is computed in pure Python —
   a true perceptual hash, not a text one — two of them: `fp` fine (17×16 grid, 256 bits) and `fpc` coarse (9×8, 64 bits). Against the
   bills of the last 90 days: **fine within 8 bits = the same capture again** (a double tap, the same file) → the new bill is `rejected`,
   `dup_of` the first, `reject_reason` "duplicate of B-nnnn", its own stamp kept (void-pair); **coarse within 6 bits = a straight re-scan
   of the same paper** (a PDF of it, a second flatten, a re-crop) → amber `maybe` for the checker's two taps. **What the image layer
   does NOT see, measured on the box (26-Sep):** a re-shot with a visible tilt of even 0.5–2° lands at 9–13 coarse bits, the same
   distance as unrelated papers, so it is not flagged by the image — the OCR triple (b) is what catches it (same vendor, bill number and
   amount → rejected). Said plainly here because the brief asked. `dup_why` records which layer spoke; an image amber whose bill number
   the OCR then reads as different from its candidate's clears itself (a second bill on the same printed form is not a duplicate). The
   **stamp slip** says, in Hindi, **"Yeh bill pehle B-0123 par scan ho chuka hai — wahi number likho"** with the first number large; a
   clean slip polls `/intake/slip/<id>?json=1` for 30 s so a verdict that arrives with the OCR replaces it. A file the tools cannot read
   carries `fp` NULL and only layer (b) guards it.
   (b) **After the OCR** (`_bg_extract`, also on re-read): vendor + bill number + total (case- and punctuation-free) against bills of
   the last 90 days → exact hit `rejected` / `dup_of`; same vendor and total with the bill number unreadable on either side →
   `dup_flag='maybe'` (`dup_cand`), **amber** on the checker's list and the bill view with two taps **Duplicate** / **Not duplicate**
   (`POST /bills/<id>/dup`). **Approving** a bill whose triple matches an approved one is refused, naming the stamp.
   `purchase_app._scans()` now skips rejected rows, so a pharmacy duplicate never reaches the Marg match; S408's bundles read only
   non-rejected rows.
3. **Re-lane, one tap** (owner / manager; `POST /bills/<id>/lane`, a select on the list and the bill view): into clinic = draft; out
   of it = captured; an approved bill never leaves clinic; audited in the new `bill_audit` (who, when, from → to).
4. **Late bills:** `bills.late_for = <YYYY-MM>` when the bill_date's month is earlier than the scan's month — set at capture (the
   pre-filled date), after the OCR fills the date, and when the checker corrects it. S408 files these under "Late — belongs to <month>";
   the Marg match is unaffected.
5. **Pharmacy scans from 01-Sep-2026:** setting `porders.scan_from = 2026-09-01` in finance.db (seeded); `porders.unscanned_bills`
   ("Bill scan karo") and `purchase_app.page_scans` (the owner's scan-links page and its red list) count purchase bills from that date.
   Older bills are neither listed nor red.
6. **Monthly count per lane** on the owner's `/purchases` page, one line: "Scans this month — clinic N · pharmacy N · lab N · expense N ·
   other N (late N, duplicates caught N)". S408's checklist reads the same numbers.
Reception's reach is unchanged (`RECEPTION_OK`: the intake routes only); the tile is already everywhere it should be; no portal / grants
change. The intake stays at `https://followup.dr-manoj.in/scanapp/intake`. `scanner_widget.js` untouched.

## Pins (FROM read on the box 26-Sep-2026 09:08 IST, after S407 → TO; built by `make_s409.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/assetapp/asset_register.py (PARENT; S403's TO) | 30b26d280c6cdf373774a94aae59f339 | df8c0e198d66b06645a2a389ce5bae1e |
| /root/finance/purchase_app.py (Sanjeevni, declared; S407's TO) | fdec7ec01d2ceb449aaa0a62956a7a0f | cdd4e9c069bc8ab78160349a11a4a4c7 |
| /root/finance/porders.py (Sanjeevni, declared; S403's) | 78d1712a69324a06c2894c19158cd834 | d08f59e2fb4e42e173f135f06da28787 |

Restarts `assetapp` and `clinic-finance`. Both databases are backed up first (`assets.db.bak_S409_<stamp>`, `finance.db.bak_S409_<stamp>`).
The new columns (`lane`, `fp`, `dup_of`, `dup_flag`, `dup_cand`, `late_for`), the backfill and the two tables (`user_lane_default`,
`bill_audit`) are made by the app's own `migrate()` at start. The seed adds one finance setting and the four lane defaults.

## Proof
`walk_s409.py` — the REAL asset app over a SCRATCH copy of assets.db (crafted bill images made on the box with ImageMagick, the guard's
own tool; crafted logins through the app's own `login_required`) and the REAL finance app over a scratch finance.db: the backfill ·
the five lanes' kind/status · only clinic in the approval queue · a ₹99,999.50 lab row never in the owner's spend · each login's default
lane, the owner's card sets shavez → pharmacy · the fingerprint: same image = same hash, the re-shot (2° tilt, 4% crop) within 8 bits,
a different paper far · the same image twice → rejected, dup_of, its own stamp kept; the re-shot caught; the slip's Hindi line names
the first stamp; the slip JSON; a PDF of the same paper caught through pdftoppm · the OCR triple rejects; the near-miss goes amber with
the two taps; Not duplicate / Duplicate store and audit · approve of a triple already approved refused, naming the stamp · re-lane both
ways, audited; an approved bill refuses to leave clinic; reception refused · late_for on a July date, cleared when corrected · S403's
pre-fill still lands on pharmacy; nonsense dropped · reception's reach unchanged · the lane line · the Sanjeevni side: a 25-Aug bill is
neither on "Bill scan karo" nor on the scan-links page, a 02-Sep one is. **Negative controls** on the box as it is: two drafts with two
stamps for the same image, no /lanes, no re-lane route, no Hindi line; the old finance side lists the 25-Aug bill. Then **S407's,
S406's, S405's, S404's, S403's, S400's and S402's own walks re-run** on the patched files (S403's with the new asset app as its "new").

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S409_SCAN_LANES/install_S409_SCAN_LANES.sh
```
Undo: put back the three `.bak_S409_<from8>` files, `systemctl restart assetapp clinic-finance`, asset login 200, healthz 200. The new
columns, tables and rows are data and harmless (every old query ignores them); the database backups are used only if the owner says so.
