# S224 BUILD BRIEF — the one document to read before S225

*04-Sep-2026. Eleven papers replaced by one. If you read nothing else about S224, read this.*

---

## WHAT S224 WAS

**The Marg lane, closed in one sitting — 07:15 to midday IST on the tail of S223.** It opened
with the 10-minute pull asleep and closed with the purchase pipeline live on the VPS end to end,
five smaller kits installed from one line, and the owner at the screens for the whole second half.
**Three of the five defects found after install were his finds**, behind 133, 115 and 99 green
checks.

---

## WHAT IS LIVE, AND ITS PINS (read back from the box by the owner, ~11:40 IST — A0)

| file | pin | what it is |
|---|---|---|
| `/root/finance/purchase_app.py` rev 5 | `6366edb5bb42797d31ce5d73b1cf6598` | **NEW** — `/finance/purchase`: hub · month (bills by supplier, scan beside the Marg amount, Correct/Wrong, **FINALISE doctor-only**) · scans · orders (PROVISIONAL until the stock feed has 28 days); the machine door `api/push · vendors · feed · healthz` |
| `/root/finance/finance_app.py` | `0aa211fb4c04041d85cbf58c6825eb42` | mounts purchase, day-PDF and MPR (`1a79f7c0` → `44bf7b50` → this) |
| `/root/portal/portal.py` | `d28038047d81abd290d58ed15f9a1482` | 📦 Marg Purchases tile; Docterz Revenue · Docterz daily collection renamed |
| `/root/portal/tile_grants.json` v7 | `578702a5a10e1487e0f320c6f1b75755` | the tile → doctor, amir, shavez, darpan, alisha, shivani |
| `/root/finance/stock_app.py` | `a61af74a1be41b879771af8977d2d9a5` | `_has_role` (F-316); `/api/open` carries `you` and reasons |
| `/root/finance/stock_diffs.html` | `fb3726553d4aec43b6b231014aba5a55` | buttons by role — viewer text only |
| `/root/finance/returns_desk.py` | `dface15bd886774c59d5c88034619650` | spot count refuses without the bill anchor (400) |
| `/root/finance/returns_desk.html` | `77e754e9b072eb78033affd5e8505b2a` | **आख़िरी सेल बिल नंबर (Marg)** box |
| `/root/finance/clinic_day_pdf.py` | `518affe983e02a266f943bced48e9c35` | **NEW** — A4 PDF + Android share; bookmark `https://followup.dr-manoj.in/finance/clinic/share` |
| `/root/finance/bank_mpr_status.py` | `a0e740ce745230bcd7cada69e0428648` | **NEW** — `/finance/clinic/bank/mpr/<date>`: APPLIED · LATE · REJECTED · WAITING · NOT RECEIVED |

**On manojz** (hashed at the close; captured in `deploy_kits/S224_LIVE_TOOLS/`): `push_expected.py`
`47641a93…` (dates from BILL WISE too) · `marg_router.py` `fb32045c…` and `marg_rescan.py` `36a0db97…`
(F-235 closed — variants ORTHOTICS / SUBSET / EXPIRED / NEAR / MIXED, `index.csv` `notes` column) ·
`signatures.json` `c0a37268…` (`SALE_RETURN / SUMMARY`) · `PUSH_STOCK_NIGHTLY.bat` v2 (three steps) ·
`PUSH_STOCK_DAILY.bat` (baseline **03-09-2026**) · `pull_watchdog.py` + `PULL_WATCHDOG.bat` ·
`PUSH_PURCHASES_NOW.bat`. Scheduled tasks, all as the owner's account, **battery flags cleared**:
*Marg pull from medical* every 10 min · *MargPullWatchdog* every 15 min · *Clinic stock nightly* 22:30.

`healthz` `exports=16`. **Tonight, 05-Sep 22:30, OUR first computed stock figure** — the first sale
export after the 03-09 baseline.

---

## THE OWNER'S RULINGS (04-Sep, 07:40 and 10:30–11:45)

- **Marg first, the whole lane, one session** — *"A2 first … all of B4 operational as a test phase …
  the C pipeline built now … a new Marg Purchases tile at my portal."*
- **D368 — supplier-wise is FINAL for month-end; Marg reports purchase returns like this only.** A
  return is labelled and counted, never asked about, never blocks. *"Avoid such confusing lines."*
- **D369 — staff pages may be all-English.** *"This much English should be OK."*
- ***"And such lines also"*** — no per-type counts on a card he reads. Three plain lines.
- **The Vaapsi stock check needs the last-sale-bill box** (ALL CAPS) — done, on page and server.
- **The bank MPR must say applied / waiting clearly** — done as its own line; the Day Revenue page
  waits on a pin.
- **Docterz tiles named Docterz**; *collection*, not *takings*; *Reception's* day totals.
- **The Day Revenue as PDF from the phone through WhatsApp** — done.
- **Share the PWA** — yes.
- **D370 — the staff purchase-order flow** is the S225 build, in the spec's §8 order.

---

## THE TEN FINDINGS

| | |
|---|---|
| **F-310** | the wall-card pin re-pinned backwards at S213 — the true S205 page is `3a11a49a…`; corrected of record; **the wall copy needs reprinting** |
| **F-311** | port 8106 quoted as 8099 from a stale repo map — F-299 in a new coat |
| **F-312** | **gross summed where net was the figure** — the owner's find on the first screen |
| **F-313** | links without the mount prefix — `bp.url_prefix` is None at register time — his find on the second |
| **F-314** | **every scheduled task created "start only on AC"** — the pull slept 06:40 → 08:37; explains S219's 46 minutes |
| **F-315** | the S221 spot count stored a quantity without its bill anchor — his find, in capitals |
| **F-316** | `_may_decide` read the broker role and denied the owner his own decision buttons |
| **F-317** | Marg re-keyed an August bill between exports — the **+₹10,641 ghost**; contained-period exports now supersede |
| **F-318** | two kit files edited after summing; the gate refused — edit, then sum |
| **F-319** | the F-235 "category filter" skip wording is wrong for equal-sized duplicates — still owed VPS-side |

---

## THE S225 SPEC

**`S224_PURCHASE_ORDER_STAFF_FLOW_SPEC.md`** (this folder and project knowledge), in its §8 order:
staff order page (three columns; rounding to 10 strips then ×10; WhatsApp one-tap; call; A4 PDF) →
phone book (two numbers; bank fields server-side, owner-verified) → arrival flow (acknowledge ·
supplied qty · Short · contextual scan) → nightly cross-verification + in-transit stock → new-items
log → salt-corrections page → stock snapshot on capture. **Nothing in it is built.**

---

## THE THREE THINGS OWED

1. **The pin-capture paste from S223** — four DECLARED-PENDING S223 files and five S221 prefixes;
   the one line is in `START_HERE_SESSION_225`. The bank-MPR line on the Day Revenue page waits
   behind it.
2. **The drawer count** — `clinic_register.py` `93a31e68…`, built at S223, not published, not installed.
3. **The F-235 skip wording VPS-side**; the tracker-side parser fix; the S182 tiles ruling; the
   wall card reprinted (F-310).

---
*Next free: **D371 · F-320 · Session 225**.*
