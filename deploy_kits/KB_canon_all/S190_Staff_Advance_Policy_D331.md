# The Staff Advance Policy — every staff member, one rule (D331 candidate · S190)

**Design drafted at S190 on the owner's rulings, surveyed against the LIVE ledger bytes
(`staff_ledger.py` `92665b64…` — the service-verified pin, 2,607 lines, read before
designing; F-137's rule). **Status: SIGNED AND EXECUTED at S190** — kits `S190_SL2`
(ledger, 190 → 212) and `S190_F2` (finance, 542 → 547), both GREEN to their projections
on the box. §5.3 answered by the installer from the box's own CSV: base ₹20,000 →
ceiling ₹15,000 at 75%. Companion to D330 (the Sanjeevni side).**

---

## 1 · The owner's rulings, restated

1. **Every staff member**, when taking an advance, sees **inline**: the total advance
   already taken this calendar month, and the **maximum permissible** beside it.
2. The maximum = **50% of salary, rounded to the last ₹100**. **Darpan's exception: 75%**
   (75% × ₹20,000 base = ₹15,000 — the same figure D330 enforces on the Sanjeevni side).
3. **Above the maximum it is a SPECIAL advance.** Special advances include the
   **instalment-repayable** kind — and that kind requires a **written application,
   uploaded**.

## 2 · What the live engine already has (surveyed, not assumed)

- **`ADVANCE_ISSUE` exists** for makers and checkers alike, and interest-free advances
  already enter the **D250 waterfall**: at every monthly close, recovery =
  `min(head-of-waterfall instalment, everything owed)`, interest first, tranche to
  tranche — **workbook-exact, proven live at the July close to the rupee.**
- **Instalment-repayable advances already exist as a class**: `interest=True` loans,
  **checker-only to issue**, with a named instalment (min ₹1,000), flat ₹1,000/month
  interest, Skip (2/FY, ₹1,000 capitalises). *The owner's "special advance repaid in
  instalments" maps onto machinery that already runs — nothing new to invent there.*
- **Base salary is already the ledger's own data**: `staff_bases()` reads
  `staff_master.csv` (`base_salary` per active staff). The ceiling can derive from a file
  the engine already reads — no new source, no second copy (F-136).
- The approve path is one function (`decide()`); an approval gate slots in one place.
- **What does NOT exist**: any month-to-date advance display, any ceiling, any notion of
  "special", and **any attachment mechanism at all** — the ledger stores JSONL + CSVs and
  has never held a file.

## 3 · The design

### 3a · The ceiling — derived, per staff, one rule

- `ceiling(staff) = floor(base_salary × pct(staff) ÷ 100 ÷ 100) × 100` — pct default
  **50**, per-staff overrides in a small `advance_pct.json` beside `users.json`
  (seeded `{"Darpan": 75}`). Base comes from `staff_master.csv` as it already does.
  *Why not a new staff_master column: that CSV is authored on the attendance side; the
  ledger should not write to a file another system owns.*
- **Month-to-date** = all APPROVED + PENDING `ADVANCE_ISSUE` rows for that staff in the
  calendar month, **wherever the cash came from** — a Sanjeevni drawer advance reaches
  this ledger as an `ADVANCE_ISSUE` row (that is the pipeline), so one book carries one
  total and Darpan's ₹15,000 medical draw and any direct advance count against the same
  ₹15,000. **The two systems agree by construction, not by synchronisation.**
- Shown **inline in the entry form the moment `ADVANCE_ISSUE` is selected**, before any
  amount is typed: *"Taken this month ₹X of ₹Y max."*

### 3b · Within the ceiling — nothing else changes

An ordinary advance at or under the ceiling behaves exactly as today: maker or checker
enters it, checker approves, the waterfall recovers it. No new ceremony.

### 3c · Above the ceiling — SPECIAL, and the engine refuses to let it be ordinary

- The save computes `mtd + amount > ceiling` → the row **must** carry `special=true` or
  it is refused with both figures in the message (F-140: a check that can fail says why).
- **RULED (S190): a MAKER may draft a special advance** — the maker–checker chain, not
  checker-only. The maker must **upload the written application, signed by Dr Manoj or
  Dr Bhawna**, against the row; the checker approves only after it is on file.
- **RULED (S190): EVERY above-ceiling advance requires the written application** —
  instalment-repayable or not. *"Any advance beyond 50% needs written approval on
  application."* The instalment-repayable kind remains the existing `interest=True`
  loan — no new category; its issue stays checker-side as the engine already enforces.
- Approval, not entry, is the gate — the application is scanned after the row is
  drafted, the same save-then-attach-then-File shape D330 uses. `decide(approve=True)`
  on ANY `special=true` row refuses without the application on file. No escape hatch.

### 3d · The written application — the ledger's first attachment

- Reuse the **shared scan widget** (`/root/assetapp/scanner_widget.js` — camera AND
  gallery, verified on the box at S190): a host page + upload endpoint in
  `staff_ledger.py`, files under `LEDGER_DIR/applications/`, one per advance row id,
  sha256-recorded in the row itself (`application_sha`).
- `decide(approve=True)` on **any `special=true`** `ADVANCE_ISSUE` **refuses** if no
  application is attached: *"An above-ceiling advance needs the signed application
  uploaded first."* No escape hatch — mirroring D330's evidence rule.
- The statement view shows a 📄 marker on rows carrying an application.

### 3e · Month attribution — an advance "against <month> salary" (RULED S190)

The device that keeps the ceiling honoured across a month boundary, minted by the owner
for the 17 Aug ₹5,000: an `ADVANCE_ISSUE` row carries an **`against_month`** (default:
the entry's own calendar month). The advance **counts against THAT month's ceiling**
and is recovered at that month's close. **This DOES need one small engine touch** —
checked against the code, not assumed: `close_month()` snapshots `open_advances()`,
which takes every APPROVED `ADVANCE_ISSUE` regardless of month, so a September-
attributed advance approved in August would be recovered a month early. The close
therefore gains an eligibility filter: a row with `against_month` later than the
closing month is skipped (and its ceiling weight likewise sits in its own month). The
waterfall's order and arithmetic stay byte-untouched; only who is eligible to enter
the snapshot changes.

So: Darpan's ₹5,000 of 17 Aug is posted **against September** — August stays at exactly
₹15,000, September opens with ₹5,000 consumed, and the Sanjeevni portal may give him
only **₹10,000** in September. The owner's alternative framing ("he is deferring the
August instalment to September salary") collapses into the same mechanism: attribution
decides which month's quota and which close recovers it.

**The cross-system plumbing this needs** (the "extra plumbing for Darpan on the salary
side"): the Sanjeevni ceiling gate must know what the LEDGER has attributed to the
month. `finance_app.py`'s `advance_month_to_date_p()` gains a read-only, fail-soft read
of the ledger's JSONL (the exact D283/D322 pattern `clinic_holidays()` already uses on
the attendance DB): month-to-date = finance rows + ledger `ADVANCE_ISSUE` rows for the
month. **Refined at build (the double-count question): only FORWARD-attributed ledger
rows are counted (`against_month` ≠ the row's own entry month)** — a drawer draw is
never forward-attributed, so the same rupee can never sit in both counts; this is the
double-count the retired D329 LINK machinery existed to prevent, solved structurally.
Known, documented blind spot: a same-month direct-pipeline advance is not netted from
the drawer limit (rare by flow; the checker sees both books). Fail-soft: if the ledger
file is unreadable, the finance gate degrades to its own rows and NEVER crashes — the
inline line then says "(Sanjeevni book only — salary ledger unreachable)" so the
degradation is visible, not silent.

### 3f · What this does NOT touch

The D250 close engine's **arithmetic and waterfall order** — proven to the rupee — are
not modified. The one recovery-side change is the §3e eligibility filter (a future-
attributed row waits for its month); skips, interest, capitalisation and the tranche
order are byte-untouched. The ceiling itself gates **entry and approval**, never
recovery amounts. The Sanjeevni side (D330) is
already live and needs nothing from this build.

## 4 · Build plan (after the owner's OK — nothing is built yet)

| kit | contents |
|---|---|
| `SL2` (ledger) | `staff_ledger.py`: `advance_pct.json` + `ceiling()` + mtd helper · inline display in the entry form · the over-ceiling refusal + `special` flag (maker may draft; application gates approval) · `against_month` on ADVANCE_ISSUE · the application upload (host page, endpoint, `LEDGER_DIR/applications/`, sha in the row) · the approve gate · statement markers · selftest checks, delta-disciplined |
| `F2` (finance, small) | `advance_month_to_date_p()` reads the ledger JSONL read-only fail-soft (D283 pattern) so the Sanjeevni inline line and refusal count ledger-attributed advances for the month; degradation visible in the label |

Two kits, one per system, ledger first — the D317 chain throughout. Rehearsed offline against a JSONL
store carrying the live file's SHAPE (F-140) — including a staff member mid-waterfall
with skips used, and a store where the month is already at ceiling.

## 5 · Open before signature

1. ~~Non-instalment special advances~~ **RULED: yes — every advance beyond the ceiling
   needs the signed written application.**
2. ~~Who issues~~ **RULED: maker drafts and uploads the application (signed by Dr Manoj
   or Dr Bhawna); checker approves.**
3. **STILL OPEN — Darpan's base in `staff_master.csv`.** The ledger ceiling reads that
   file; D330's finance ceiling reads settings (₹20,000 × 75%). If the CSV does not say
   ₹20,000 the two systems disagree about the same man. One look on the box before the
   build: `grep -i darpan /root/attendance/staff_master.csv` *(path to be confirmed
   from `_att()` at build time — this command is a starting point, not a claim).*
4. ~~Effective date~~ **RULED: applies from AUGUST.** August is already compliant by
   construction — ₹15,000 in August, the ₹5,000 attributed to September (§3e). Nothing
   to back-mark.

---

*Design S190 · becomes D331 on the owner's OK · builds as one staff-ledger kit.
Companion executed contract: D330. Next free after: D332 · F-141 (ruling pending).*
