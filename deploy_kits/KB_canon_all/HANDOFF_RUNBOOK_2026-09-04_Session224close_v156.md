# HANDOFF RUNBOOK — S224 close · 04-Sep-2026 · v156

*Supersedes v155 (S223 close). Tier 0.*

---

## §0 · WHAT HAPPENED

**The Marg lane closed in one sitting: 07:15 to midday IST on 04-Sep, on the tail of S223.**
It opened with the 10-minute pull already asleep and closed with the purchase pipeline live on the
VPS end to end, five smaller kits installed from one line, and the owner at the screens for the
whole second half.

1. **Phase 0, and F-310** — the wall-card pin re-pinned backwards at S213 (`dd018563…` is the
   pre-S205 page; the true S205 page is `3a11a49a…`), corrected of record in the manifest; **the
   page on the wall beside the medical PC needs reprinting.**
2. **A1 — the returns signature.** `SALE_RETURN / SUMMARY` taught; **197 credit notes, ₹68,099**
   rescued from `_REFUSED`; the end marker derived from the file (`T o t a l`), not copied.
3. **The clubbed list and the owner's Marg-first order** — *"A2 first … all of B4 operational as a
   test phase … the C pipeline built now … a new Marg Purchases tile at my portal."*
4. **A2** — `push_expected.py` dates purchase lines from BILL WISE too (0 undated, was 28); the
   baseline moved 02-09 → 03-09 by the assistant's call. **Bill-wise is the export that dates every
   line.**
5. **The five-kit build**: `S224_MARG_PURCHASES` (tables · ingest door · hub, month, scans, orders ·
   FINALISE · the tile) + the manojz legs (`push_purchases.py`, `PUSH_STOCK_NIGHTLY.bat` v2, the
   pull watchdog, F-235 variant naming live). Then `S224_DIFFS_ROLE_FIX`, `S224_STOCK_ANCHOR_FIX`,
   `S224_BANK_MPR_STATUS`, `S224_DOCTERZ_TILE_NAMES`, `S224_DAY_REVENUE_PDF` — **one installer line**.
6. **The owner's seven screen rulings** (§S224 §8): all-English staff pages (D369) · the diffs
   buttons by role · **supplier-wise is FINAL and returns are normal (D368)** · the Vaapsi anchor box,
   in capitals · the bank-MPR line · the Docterz tile names · the Day Revenue PDF to WhatsApp.
7. **Rev 2 → rev 5 of `purchase_app.py`** on his finds: gross where net was the figure (F-312), links
   without their mount (F-313), the ₹10,641 ghost bill (F-317), *"and such lines also"*.
8. **The sleeping pull explained** — every scheduled task had been created *start only on AC* (F-314).
9. **Ten pins read back from the box by the owner at ~11:40**; the manojz pins hashed at the close and
   captured in `S224_LIVE_TOOLS`.
10. **The staff purchase-order flow dictated** — `S224_PURCHASE_ORDER_STAFF_FLOW_SPEC`, S225 by his
    word (D370).

**New fault codes: F-310 … F-319.** New decisions: **D368 · D369 · D370**. Next free
**F-320 · D371 · S225.**

**SOP change:** none. **Surveillance scope:** unchanged.

---

## §1 · MENTAL MODELS THAT EARNED THEIR PLACE THIS SESSION

**A task created by `schtasks` starts only on AC** (F-314). The default nobody cleared put the Marg
pull to sleep three times in a month and explained a 46-minute sleep recorded at S219 as a mystery.
Every registration line clears the battery flags; the watchdog judges the pull against the PC being
awake.

**The first screen the owner sees is the walk nobody can script.** Three of the five defects found
after install were his — gross where net was the figure, a link without its mount, a count box with
no bill anchor — behind 133, 115 and 99 green checks. A test asserts what its author believed; the
owner reads what is there.

**`bp.url_prefix` is None when the prefix is given at register time** (F-313). A blueprint carries
its own mount as a module-level value set in `init()`, and the render test refuses any own href
without it.

**A map built from a stale repo copy is F-299 wearing a new coat** (F-311). Port 8106, not 8099. A
live fact comes from the live file or the running box, never from a copy.

**Edit, then sum. Never sum, then edit** (F-318). `SUMS.md5` is generated last, from inside the
folder, and verified there before the kit is named to the owner. The gate refusing its author is
the gate working.

**Net is the figure; gross is the noise** (F-312). When Marg's report sits beside a sum of ours, the
test asserts the report's total, not our arithmetic.

**Marg edits its past** (F-317). An export supersedes every older live export of its type whose
period it *contains* — not only the one with the same period.

**A count is a count wherever it is taken** (F-315). Any surface that records a stock quantity
carries the last-sale-bill anchor, refused on page and server.

---

## §2 · THE LIVE BACKLOG

**⭐0 — FIRST ACTION AT S225, before any build — still owed from S223:**

1. **The pin-capture paste** — the five DECLARED-PENDING S223 files (`tile_grants.json` is now v7
   and read back; the other four stand: `finance_clinic_day.py`, `docterz_day.py`,
   `docterz_ingest.py`, `clinic_upi_check.py`) **plus the five S221 8-char prefixes still outstanding**
   (`finance_ingest.py`, `darpan_card.html`, `stock_finding.html`, `stock_drift.html`,
   `cards_registry.json` — `push_snapshot.py` was promoted at S224 by a manojz hash, the two
   `returns_desk.*` at S222). The one line is in
   `START_HERE_SESSION_225`. **The bank-MPR line on the Day Revenue page waits on
   `finance_clinic_day.py`'s pin** — a two-line anchor-guarded patch, buildable the moment the pin
   is read (`S224_BANK_MPR_STATUS` §5).
2. **Publish and install the drawer count** — `clinic_register.py` `93a31e68…`, built at S223, 89/89
   green, still not published and not installed.
3. **The finding page's decision buttons — read back live once, first time ever** (F-316): open
   `/finance/stock/page/finding` as the owner; *write off / recover / no loss* should now appear.

**⭐1 — `S224_PURCHASE_ORDER_STAFF_FLOW_SPEC` in its §8 order (S225, by the owner's word — D370):**

1. The staff order page — three columns (Item · Stock now · Order qty); units in the item's own
   pack, rounded up to 10 strips then multiples of 10; WhatsApp one-tap per stockist (header line +
   `Item — qty unit` lines, nothing else); `tel:` call; A4 PDF (the S224 writer reused).
2. The stockist phone book — manoj · darpan · shavez; two numbers per supplier; bank fields on the
   new-supplier form, **server-side only, verified by the owner alone**; every change audited.
3. The arrival flow — acknowledge in one tap; per-line supplied quantity; *Short* carries into the
   next order; the scan button at its contextual places, pre-filled.
4. Nightly cross-verification (scan-link re-match unattended) + received-not-yet-in-Marg as
   stock-in-transit for the reorder engine.
5. The new-items log and the owner's *"N new items this month"*.
6. Amir's salt-corrections page — `.xlsx` download and A4, for amir and manoj.
7. Push the stock snapshot on capture, not only at 22:30.

**Then the S223 dawn specifications, in his order** (Runbook v155 §2 ⭐1, unchanged): the two scoped
logins (Manoj Bhati · Awdhesh) · the physio revenue view · Awdhesh's pre-listed X-ray film screen ·
procedures with contextual consumables · the printer counter and refill reminder · the image
worklist · the Docterz capture moved to the reception PC.

**⭐2 — owed technical work:**

- **Push the stock snapshot on capture** (also §8 item 7 above — *"latest stock report doesn't seem
  to be applied"*). OUR first computed stock figure appears **05-Sep 22:30**, the first sale export
  after the 03-09 baseline.
- **The tracker-side parser fix** — proven offline at S223, not installed; until it lands each day's
  splits need `push_day_tenders.py` re-run.
- **The F-235 skip wording VPS-side** (`push_snapshot.py`, `S207_STOCK_VPS`) — *duplicate*, not
  *category filter*, for equal-sized identical sets (F-319).
- **The S182 "Daily Collection" / "Clinic" tiles** — counter-fed, not Docterz; rename, retire or leave
  is his ruling.
- **August item-wise coverage**: nothing item-wise covered 22–27 Aug until his full-month export; the
  hub now shows the month with one purchase return (bill 148). **The PROVISIONAL hold on August
  purchase is his to lift on the month page** — FINALISE, doctor only.
- Reconcile the Docterz reader against `S211_DAYREVENUE`'s 67-workbook rehearsal; the nine split-gap
  days (S223 ⭐2, unchanged).
- The spot-count anchor is a point, not a pair — bill-at-open and bill-at-submit, and the anchor shown
  on the owner's finding, are the next step (`S224_STOCK_ANCHOR_FIX` §6 item 5).

**⭐3 — rulings owed by the owner:**

- **Reprint the wall card** beside the medical PC from `D:\Downloads\margsync\MARG_WALL_CARD.html`
  (F-310 — the printed page is the pre-S205 one).
- **`darpan_app.py` divergent copies — awaiting his ruling since the S210 close, load-bearing.**
- **Five one-word answers on `S223_PROCEDURES_DRAFT_FOR_OWNER`** — HBK · POP · undercast padding ·
  the draft quantities · ILI consumables.
- S214 / S215 / S216 candidate sets — recorded, not minted; the four Docterz candidates.
- The Darpan tile mask (`USER_TILE_MASK["darpan"]`, S222 ⭐0-5).

**Parked by the owner:** the advances build · the spot-count bridge (D3 — until the drift log has a
month) · batch-wise stock (Marg has no such export) · the medical→VPS direct leg (E1, designed at
S202/D350, not built).

**Standing holds:** the NEFT portal WAITS · the hub's shape is not reopened.

---

## §3 · INSTALL DISCIPLINE — what S224 added

- **One installer line for a multi-kit day** — `S224_INSTALL_ALL/install_all.sh`: kits in order, each
  behind its own pin guard and self-rollback, stopping at the first that does not land. The owner
  pastes one line and reads one verdict.
- **The dynamic-pin caveat for chained patches on one file.** Two kits anchoring on the same line of
  `finance_app.py` cannot both carry a predicted after-pin; whichever installs second is **handed
  the NEW pin the first printed**. The installer passes it; a human never re-types it.
- **`SUMS.md5` is written LAST and verified from inside the folder** (F-318). Any edit after summing
  re-sums.
- **A port or mount is read from the box** (F-311). Discovery maps carry their source, and a
  repo-derived line is labelled as such until the box confirms it.
- **The render test drives the page's own JS with live-shaped logins** (F-316) — `role` from the
  broker, unit roles in `roles`, one fixture per real person.
- **`schtasks` lines clear the battery flags** (F-314).
- All of S223's rules stand: mount touches nothing (F-303); the gated installer is the only writer
  (F-302); `systemctl is-active` after every restart, self-restore on failure; slice edits assert
  their bounds (F-304).

---

## §4 · THE BOUNDARY

- **The publish is the owner's double-click**: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
- **Patient data is not in this project. No patient number in the repository (F-185).** Vendor
  phones live in `D:\Downloads\margsync\_config\` and in `finance.db`; supplier bank details, when
  they come, server-side only and verified by the owner alone (D370).
- **Nothing here ever writes to Marg, sends to a bank or a vendor, or leaves the server** (D325). The
  WhatsApp order of D370 is the staff member's own tap in their own WhatsApp.
- Nothing live is rebuilt without his explicit OK; the manual workflow stays as fallback.
- **ClickUp is parked (D17).**

---
*v156 · S224 close · 04-Sep-2026. Written before the manifest, as the routine requires.*
