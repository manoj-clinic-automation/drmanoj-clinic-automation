# SCAN APP SYSTEM BOOK — v1 — what the scan app is, where it lives, how it is changed

*Written at S305 (the parent), 11-Oct-2026, as part of the scan app's starter pack (D689 item 3). Read from the live
code in the 11-Oct 01:35 nightly bundle and the pinned Register (`live_pins_S304close.txt`). This Book is the scan-app
project's own record; the parent's Runbook describes the estate. No patient number, no person's figure and no secret is
in this file.*

## 1 · What it is, in one paragraph

Every paper that enters the clinic — a supplier's bill, a challan, a handwritten slip, a warranty card, a document that
is not a bill — is photographed on a phone by whoever holds it, in the **scan app**. Each scan gets a **stamp number at
once** (written on the paper), becomes one PDF, is read in the background (Sarvam OCR), and lands in a **lane**. The
pharmacy lane hands the bill to the Sanjeevni side (Amir's purchase pages, the bill register). The clinic lane's papers
are sorted on the **papers page** into the clinic-consumables groups. The owner's own purchases go to the **Dr MK
expense** lane, where a warranty can be kept and reminded. Everything is found again by month, by group, by supplier.

## 2 · Where it lives

| part | where | notes |
|---|---|---|
| the app | `/root/assetapp/asset_register.py` | Flask under gunicorn (2 workers, `127.0.0.1:8030`), service `assetapp`, **the system `python3`, not the venv** (F-53). Served at `https://followup.dr-manoj.in/scanapp` (the prefix of S222; the vhost forwards `/scanapp`). Pinned `e774be89…` (S465). About 4,100 lines. |
| the papers page | `/root/assetapp/clinic_papers.py` | D664, kits S464 → S465 → S466. Mounted by one guarded `init(ar)` from `asset_register.py`; every template hook sits behind `is defined`. Pinned `5e21f491…`. |
| the database | `/root/assetapp/assets.db` (env `ASSETS_DB`) | SQLite: `bills`, `bill_items`, `vendors`, `vendor_contacts`, assets, staff, files. A bill's `lane`, `kind`, `status`, month, sub-group and warranty live on its row. |
| the scanner | `/root/assetapp/scanner_widget.js` (served at `/scanapp/scan/widget.js`) | v2 since S219; S441's no-wait flow. **Seven live surfaces: the scan app's intake (2) and the finance app (5 — day scan, non-cash, expense, clinic day, clinic expense).** Both apps version its URL by the file's mtime, so a swap busts every browser cache. Pinned `e2bca602…`. |
| the reading | `/root/shared/sarvam_ocr.py` | the one OCR module; the key is in the service environment, never in code. |
| the checks | `/root/shared/scan_checks_s441.py` | S441: a forgotten page joined, a sure double set aside (never an approved bill), a near match flagged. Pinned `b9ba6839…`. |
| the backup | `/root/state_backup/assetapp_backup.py` | S286/S287: a verified archive nightly, off-site to Drive slots `assetapp_nightly.tar.gz` / `assetapp_monthly.tar.gz`. Pinned `b816504c…`. |
| the doors in | the portal's tiles (`/root/portal/portal.py`, `tile_grants.json` — the parent's) | the *Scan* tile opens `/scanapp`, the intake tile `/scanapp/intake`. |
| the service unit | `assetapp.service` | a repository copy is pinned SHORT `cd84cdc2` (S255). |

## 3 · The pages (routes under `/scanapp`)

- **Intake:** `/intake` (the scanner; doc mode; the fallback photo/PDF upload inside a fold) · `/intake/scan_submit` ·
  `/intake/submit` · `/intake/slip/<id>` and `/intake/slip/last` (the big stamp number to write on the paper).
- **Bills:** `/bills` · `/bills/<id>` with `approve`, `reject`, `reread`, `edit`, `delete`, `dup`, `lane`, `month`,
  `file`, `thumb`, `s441` · `/bills/<id>/subgroup` (D664) · `/bills/extract` · `/bills/new` · `/drafts`.
- **The papers page (D664):** `/papers` (the clinic papers to sort, each with a suggestion: Yes / Change / Skip) ·
  `/papers/<id>` · `/papers/month` (clinic consumables for a month, by group) · `/papers/<id>/join` and `/unjoin` (one
  purchase = one PDF, with an undo that names the papers) · `/papers/<id>/warranty` (what it is, warranty till, remind
  30 / 7 days before or never). All owner/checker only.
- **Lanes and purchases:** `/lanes` · `/purchases` (the owner's page: rate drift, expiry soon, consumption) · `/vendors`.
- **Assets and renewals:** `/assets` (by location, collapsible) · `/assets/<id>` with `edit`, `service`, `delete` ·
  `/renewals` (warranty / AMC / consumable expiry; since S466 a Dr MK expense's warranty too) · `/api/due` · `/staff`.
- **House:** `/healthz` · `/login`, `/logout` (the portal's SSO cookie; portal role doctor → owner, staff → reception) ·
  `/admin` · `/account`.

## 4 · The lanes (S409, D625) and the groups (D664)

Five lanes on the one intake, each login with its own default (`LANE_DEFAULTS`); a staff member can send a pharmacy scan
to another lane with *Galat lane*:

| lane key | label | kind · status at intake |
|---|---|---|
| `clinic` | Clinic bill — asset or consumable | Consumable · draft |
| `pharmacy` | Pharmacy purchase — Sanjeevni | Pharmacy · captured → the Sanjeevni side |
| `lab_purchase` | Lab purchase — NK Pathology | Lab · captured |
| `owner_expense` | Dr MK expense | Expense · captured |
| `other_doc` | Other document — not a bill | Document · captured |

**The clinic-consumables groups (D664, the owner's ruling of 03-Oct):** *Procedure room* (fibre cast, roller bandage,
cotton, tape, betadine) · *X-ray films* (then one more tap: small film or 11 x 14) · *Others* (stationery and the rest).
The sub-group is optional at scanning; Shavez or the owner sets it later; the system suggests it from the supplier and
the items, one tap to confirm or skip. **Yuvika supplies both sides** (orthotics on printed bills for the pharmacy,
procedure-room goods on handwritten slips), so the supplier alone never decides the lane.

**His rulings that bind every change here:** one purchase = one PDF (bill and warranty cards together) · a Dr MK expense
keeps its warranty and the renewals list reminds him · pathology purchases have their own lane · **the split between
clinic expenses and MK expenses is not finalised — never guess it** (electrical, plumbing and similar papers come as
bills, estimates, challans and handwritten slips, mostly MK) · the 61 test scans stay (S468, his word) · staff flows
never make staff wait or confirm twice.

## 5 · What is NOT the scan app (and is often confused with it)

- **Patient papers** — outside X-ray / MRI / CT reports, discharge papers, blood reports, the *Check karein* list — are
  the finance app's records (`/root/finance/records.py`, `records_inbox/`, the parent's; kits S333 … S346). The word
  "papers" there means a patient's papers, not the clinic's.
- **The pharmacy bill's life after the scan** — paired with its Marg bill (`/root/finance/scan_register.py`), Amir's
  steps, *Scan ka kaam* on Purchase orders (S440's server half), the month's bill register — the Sanjeevni chat's.
- **The working-paper shelf** (`D:\Downloads\_kbtools\PAPERS.bat`) — the estate's record-keeping, the parent's.

## 6 · How a change is made here

1. Take the kit number on the board before the folder is named; a PLANNED line first if the change touches
   `scanner_widget.js` (seven surfaces, two apps) or any file the parent or the Sanjeevni chat owns.
2. Read the live file from the newest bundle and hash it against its pin; **read `asset_register.py` whole before its
   next patch once its drift reaches 5.** The Register records it at 6 after S466, then **0 — read whole after D664's
   three slices, no kit since**; `clinic_papers.py` 0 (S466 replaced it whole). Count from there.
3. Build by `BUILD_NORM_v1.md`: exact counted edits; a walk on made-up rows in a scratch copy of the app and its
   database; a negative control that must go red; the installer's order (gates → pins → walk → backups `.bak_<kit>_<from8>`
   → place → `systemctl restart assetapp` only → `/scanapp/healthz` → the data step → the undo line).
4. The publish is his double-click; the server line is one line with its own pull.
5. After the install: the pins read back from the box (the installer prints them), DECLARED-PENDING until the next
   nightly bundle; the page read by a sub-agent as the person who will use it (reads only).

## 7 · Kit history (the scan app's)

S175/S177 (the asset register v1.11, the intake, Sarvam) · S195 (the non-cash scan) · S207 → S219 (scanner v2, finalised
on seven surfaces) · S222 (the app inside the portal PWA; the `/scanapp` prefix) · S286/S287 (the backup and its Drive
leg) · S409 (five lanes) · S435 (the bill's month asked at intake; the person's month beats the OCR's date) · S440 (the
Sanjeevni chat's *Scan ka kaam*, with declared edits here) · S441 (no waiting, no questions; the after-the-fact checks;
the rate page) · S464 / S465 / S466 (D664 in three slices: the papers to sort and the three groups; join with undo; the
Dr MK expense warranty on the renewals page). Each kit's README in `deploy_kits/` carries its own undo line.

## 8 · Open at the branch

- **D689 item 1** — the papers page gets four sections: *Resumes*, *Miscellaneous documents*, *Construction work*,
  *Personal* (there is no Personal section today; *Dr MK expense* is the nearest).
- **D689 item 2** — the challan flow: goods on a challan, the bill later; a challan kept as *goods received, bill
  awaited*, joined to its bill when the bill is scanned, deletable once the bill has come. Medicine suppliers' challans
  are the Sanjeevni chat's side.
- **Not built:** a warranty date offered from the scan's reading (S466 left it to a person).
- **His, open:** the clinic / MK expense split (D664) — not to be guessed.
- **Drift:** `asset_register.py` 0 and `clinic_papers.py` 0 at the branch (§6 step 2).

---
*SCANAPP_SYSTEM_BOOK — v1 · S305 (the parent), 11-Oct-2026 · the scan-app project's Book from its first session on;
each scan-app close that changes the app writes the next version into `deploy_kits/KB_canon_all/`.*
