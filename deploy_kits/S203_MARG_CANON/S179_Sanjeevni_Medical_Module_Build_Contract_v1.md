> ## ⚠ STATUS UNCERTAIN — DO NOT ACT ON THIS DOCUMENT AS CURRENT DESIGN
> **Classified RETIRE by `S203_MARG_RETIREMENT_LIST.md` §1 row 12 on the strength of "superseded whole
> by v2, which says so" — and that supersession is UNVERIFIED.**
> Checked on 26-Aug-2026: **no `S179_Sanjeevni_Medical_Module_Build_Contract_v2` exists anywhere in
> this repository** (searched by filename across the whole tree; the only match is this v1). The
> retirement list's own §4 #1 records that this document **was never read from project knowledge**,
> and its §1 row 12 carries the caveat that its §7 ICICI merchant-statement identification must be
> confirmed present in v2 before removal. **No successor document and no successor md5 can be named
> here honestly.**
> **Treat as KEEP until a v2 is produced and hashed.** It is a DRAFT-for-sign-off from S179; nothing
> in it is measured, so do not read it as current design either. The nearest current documents are
> `S179_Finance_LIVE_State` (md5 `54cb25a88adc5692360341113a87a43e`, authoritative on D313 and the
> design invariants, out of date on state) and `MARG_INGESTION_REFERENCE_v1.md`
> (md5 `4d603b727a91a7c782992f092fc949e3`).
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# SANJEEVNI (MEDICAL) MODULE — BUILD CONTRACT v1

**Session 179 · Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre, Bareilly**
**Parent analysis:** `S179_Finance_Revenue_Migration_Analysis_v1.md`
**Status:** DRAFT for sign-off. **No code written yet. Nothing live touched.**
Candidate numbers if adopted: **D313** (architecture) · **F-84** free.

---

## §0 — WHAT YOU DIRECTED (read back to you, so we agree before I build)

Your words, turned into requirements. If any line below is not what you meant, say so and I will fix
the contract before writing a single line of code.

| # | You said | I will build |
|---|---|---|
| 1 | *"build a vps only system from form entry by pharmacy onwards"* | The whole chain lives on the VPS: pharmacy enters on a phone → data, scans, ledger, approval, reports all on the VPS. Google Forms retired after a clean parallel run. **The paper register stays the fallback** — that never changes. |
| 2 | *"populate data"* | Import all 122 existing medical rows (Apr 1 → Aug 13 2026), **as recorded** |
| 3 | *"provisions for deposit to dr manoj, dr bhawna, and back, and deposit to bank"* | Cash movements with a **party** (Bank · Dr Manoj · Dr Bhawna) and a **direction** (out of drawer / back into drawer). Covers hand-over and return in one clean model. |
| 4 | *"expenses logging with one fixed option of salary advance, and rest are free text"* | Expense row = amount + category. Category `Salary advance` is a fixed option **with a staff picker**; everything else is free text. |
| 5 | *"make form error proof from typos"* | Numeric-only fields (letters cannot be typed — kills the `O` → `#VALUE!` fault), sanity bounds, UPI ≤ total, computed opening read-only, negative closing hard-blocked, duplicate date blocked. |
| 6 | *"structure date as selectable"* | Date picker only. No typing. No future dates. No year `0026`. |
| 7 | *"in app scanner"* | The same scanner widget already proven in the asset app (A-D24) — camera → straighten → PDF → upload, inside the page. |
| 8 | *"import of existing data to be done"* | See §5. |
| 9 | *"pharmacy is under darpan, and biometric attendance populate his absent days when a reserve person handles pharmacy"* | Each day carries **who manned the pharmacy**. Default Darpan, auto-filled from biometric attendance; if biometric shows him absent, the form **requires** you to name the reserve person before submit. |
| 10 | *"monthly totals are computed"* | Month view, all totals derived, never typed. |
| 11 | *"missing dates are loudly flagged"* | Red on the month grid + a WhatsApp nudge next morning + a doctor alert if still missing at 24 h. |
| 12 | *"all upi transactions land as an email attachment the next day in my email automatically forwarded to clinic email"* | **Found and identified — see §7.** It is the ICICI Merchant Solutions MPR, a daily **`.xlsx`**, already split into a separate file for **Sanjeevni Medicos** and one for the **clinic**. Reconciliation will be exact, not OCR-approximate. |
| 13 | *"pdf to upload are days sale report, manual copy page of that day, and orthotics copy of that day"* | Three attachments per day, named exactly that. **Note this changes today's practice** — you currently upload *medicine copy* + *implant copy* (2). New set is **3**. |

**Also confirmed by you this session:** `Old Balance` = **yesterday's closing cash (carry-forward)**
· import **as recorded, variances preserved** · **pharmacy enters, doctor-only approval** (no middle
checker).

---

## §1 — THE ONE DESIGN RULE THAT FIXES EVERYTHING

Because you confirmed `Old Balance` is meant to be **carry-forward**, every one of the 36 mismatches
is by definition an **unexplained adjustment**, not a legitimate figure.

So the new ledger works like this:

```
opening(today)  =  closing(yesterday)          ← COMPUTED. Read-only. Cannot be typed. Ever.
closing(today)  =  opening
                 + cash sales      (total − UPI)
                 − expenses
                 − cash out        (bank / Dr Manoj / Dr Bhawna)
                 + cash back in    (from Dr Manoj / Dr Bhawna / injection)
                 ± adjustment      ← must be an explicit row, with a reason and your approval
```

There is no cell anywhere that lets a person overwrite the running balance. That is the whole fix.
An adjustment is still possible — the drawer is real, and real drawers have surprises — but it is a
**visible, dated, reasoned, doctor-approved row**, not a silent overwrite. The ₹1,84,285 problem
cannot recur in this shape.

---

## §2 — SCREENS

### 2.1 Pharmacy — "Aaj ki entry" (phone, Hindi-first labels)

One page, top to bottom, thumb-friendly:

1. **Date** — picker, defaults to yesterday. Future blocked. Already-entered date opens that day for
   correction instead of creating a duplicate.
2. **Manned by** — pre-filled *Darpan* from biometric. If biometric says absent → the field turns
   red and a reserve-person picker becomes mandatory.
3. **Opening cash** — shown big, greyed, **read-only**, with "kal ka closing" beneath it.
4. **Total sale (₹)** — numeric keypad only.
5. **UPI received (₹)** — numeric keypad only. Blocked if greater than total sale.
   → **Cash sale** auto-computes and displays.
6. **Expenses** — "+ add" repeater. Each row: amount + category. Category = `Salary advance`
   (→ staff picker) or free text.
7. **Cash given out** — "+ add" repeater. Each row: amount + party (**Bank · Dr Manoj · Dr Bhawna**)
   + optional slip scan.
8. **Cash received back** — "+ add" repeater. Same parties, opposite direction.
9. **Closing cash** — computed, shown big. **If negative, the submit button is disabled** with a
   plain-Hindi reason.
10. **Scans** — three tiles, each opening the in-app scanner:
    **Day's sale report · Manual copy page · Orthotics copy**. Submit blocked until all three are
    attached (a "reason for missing scan" escape hatch exists and flags the day).
11. **Submit** → status `submitted`, waiting for your approval.

### 2.2 Doctor — approval + Sanjeevni tile

- **Tile on the portal:** today's sale · cash/UPI split · cash in hand (computed) · days awaiting
  approval · missing days this month · month-to-date vs last month.
- **Approve screen:** the day's figures, the three scans side by side, the OCR-read total from the
  sale report vs the typed total, the UPI-email total vs the typed UPI, who manned the pharmacy, and
  any adjustment awaiting your reason. One **Approve** button; approval locks the day.
- **Month grid:** every date of the month as a cell. Green = approved · amber = submitted, awaiting
  you · **red = missing** · grey = declared closed. Monthly totals computed at the foot.

---

## §3 — DATA MODEL (medical instance of the estate-wide model)

```
day_entry        id · unit='medical' · business_date · manned_by_staff_id
                 · manned_source(biometric/manual) · status(draft/submitted/approved/locked)
                 · entered_by · entered_at · approved_by · approved_at
                 UNIQUE(unit, business_date)

day_line         day_entry_id · kind(sale_total) · mode(cash/upi) · amount
                 (narrow by design: adding 'card' or a new revenue head later = a row, not a migration)

day_expense      day_entry_id · amount · category_fixed(salary_advance|NULL)
                 · staff_id(NULL unless salary_advance) · category_text · note

cash_movement    day_entry_id · direction(out/in) · party(bank|dr_manoj|dr_bhawna|other)
                 · amount · reference · slip_attachment_id

cash_adjustment  day_entry_id · amount(signed) · reason · source(legacy_import|manual)
                 · approved_by · approved_at

cash_ledger      (DERIVED VIEW — never a typed table) date · opening · receipts · payments · closing

attachment       day_entry_id · doc_type(sale_report|manual_copy|orthotics_copy|deposit_slip)
                 · path · sha256 · uploaded_by · uploaded_at

ocr_extract      attachment_id · engine('sarvam') · extracted_total · confidence
                 · match_status(match|mismatch|unreadable)

upi_statement    business_date · source_email_id · attachment_path · parsed_total
                 · txn_count · match_status(match|mismatch|missing)

audit_log        table · row_id · action · before · after · by_whom · at
```

**Two invariants enforced in code, not convention:** (a) nothing derivable is ever stored as typed
input; (b) one writer per store (D235).

---

## §4 — THE THREE CROSS-CHECKS (this is what a spreadsheet can never do)

| Check | Source A (typed) | Source B (independent) | On mismatch |
|---|---|---|---|
| **Day total** | pharmacy types total sale | **Sarvam OCR** reads the day's sale-report scan | day flagged amber on your approval screen, both numbers shown |
| **UPI** | pharmacy types UPI received | **ICICI merchant `.xlsx` for Sanjeevni**, parsed next morning (§7) | day flagged, difference shown to the rupee |
| **Cash in hand** | — | computed ledger vs any physical count you order | variance becomes a named, reasoned adjustment |

Today the scans are a filing habit nobody reads. After this they are *evidence that argues back*.

---

## §5 — IMPORT OF EXISTING DATA (as recorded — your instruction)

- All **122 medical rows**, Apr 1 → Aug 13 2026, imported with `source='legacy_sheet'` and the
  original Drive link for both existing PDFs preserved on the row.
- Because `Old Balance` = carry-forward, each of the **36 breaks becomes a `cash_adjustment` row**,
  signed, dated, `source='legacy_import'`, reason `"unexplained — imported from sheet, awaiting
  doctor's reason"`. Net effect: **the imported ledger reconciles perfectly and the entire ₹1,84,285
  of drift becomes 36 named, dated, clickable line items** you can work through with the pharmacy at
  your own pace. Nothing is silently corrected; nothing is silently lost.
- The `#VALUE!` row (07 Apr, expense typed `O`) imports with expense = **unknown**, flagged — not
  guessed as zero.
- The duplicate 21 May imports as one day plus one flagged correction.
- The 12 missing Sundays + Mon 04 May + Wed 27 May import as **missing**, red on the month grid,
  pending your ruling on whether Sundays count as closed (§7 Q3).
- **Legacy days are imported as `approved`/locked** — history is not put in your approval queue.

---

## §6 — WHERE IT LIVES + BUILD ORDER

**Placement:** new app `/root/finance/finance_app.py` · own systemd `clinic-finance.service` · own
store `finance.db` · SSO via the existing broker (D261) · portal tile (D285 roles) · scanner widget
and `/root/shared/sarvam_ocr.py` reused as-is · WhatsApp nudges via the shared canonical sender
(D310) · added to `clinic_watchdog.py`. Install discipline per Runbook §3 — `.new` files, one
&&-chained block, md5 gate, smoke gate, auto-rollback.

**Build order (one step at a time, each ends with your OK):**

| Step | Deliverable | Touches live? |
|---|---|---|
| **B1** | Schema + importer + reconciliation report, run offline on a copy | **No** |
| **B2** | Pharmacy entry page + ledger engine + all validations | New app, nothing existing touched |
| **B3** | In-app scanner + 3 attachments + Sarvam OCR cross-check | No |
| **B4** | Attendance link (Darpan / reserve person) + missing-day watchdog + nudges | Reads attendance, writes nothing there |
| **B5** | Doctor approval screen + Sanjeevni portal tile + month grid | One portal tile added |
| **B6** | UPI email ingester + reconciliation | Reads Gmail only |
| **B7** | 7-day parallel run → retire the Google Form | — |

---

## §7 — THE UPI EMAIL: FOUND AND IDENTIFIED (no sample needed)

I searched your mailbox rather than asking you. The daily statement you described is:

| | |
|---|---|
| **Sender** | `merchantsolutions@icici.bank.in` |
| **Subject** | `MerchantStatement-DD-MON-YYYY` (e.g. `MerchantStatement-14-AUG-2026`) |
| **Arrives** | daily, roughly 08:00–09:40 IST, for the previous day |
| **Attachment** | **`.xlsx`** — machine-readable. *(A second mail with the same data as `.zip` arrives ~1 h later.)* |

**And it is already split by business, which is a gift:**

| Merchant ID | Attachment name pattern | This is |
|---|---|---|
| `100000000312505` | `..._MSSANJEEVNI_MEDICOS_DDMMYYYY_ICICI_POS_CD.xlsx` | **Sanjeevni Medicos** — the pharmacy |
| `100000000306941` | `..._MSDR_MANOJ_AGARWAL_CLINIC_DDMMYYYY_ICICI_POS_CD.xlsx` | **Dr Manoj Agarwal Clinic** |

**Why this matters more than you may realise.** I had assumed the UPI cross-check would need OCR on
a PDF — approximate, confidence-scored, arguable. It doesn't. It is a **spreadsheet, per business,
per day, with a merchant ID**. The Sanjeevni UPI figure can be reconciled **to the rupee,
transaction by transaction, automatically, every morning, with no one typing anything.** And the
clinic module later gets the identical treatment for free.

Each mail also lands twice (once to `drmanojkragarwal@`, once to `drmanojhuf@`) — the ingester will
deduplicate on merchant ID + date, so a re-send or a forward can never double-count.

**One thing I could not verify from here:** whether `ICICI_POS_CD` covers *all* the pharmacy's
digital collection, or only ICICI QR/POS — if some customers pay to a PhonePe/Paytm/personal UPI
handle, that portion will not be in this file and the reconciliation would show a permanent
shortfall. I'll confirm this on the first live day by comparing a real statement total against the
typed figure, and report the answer rather than assume it (F-66 discipline). **No action needed
from you.**

## §8 — WHAT I STILL NEED FROM YOU BEFORE B1

**Q1 · Which mailbox should the VPS read?** The ingester needs its own credential. Options: the
clinic email (`drmka.ortho@…`, which already receives the forwards), or read your main mailbox
directly. **My recommendation: the clinic email** — it keeps a clinic system out of your personal
inbox, and a filter there is easy to audit.

**Q2 · Salary advance — does it post to the Staff Ledger?** D258 made the Staff Ledger the single
home for all staff money. If a salary advance is logged here **and** in the ledger, it gets counted
twice. Options: (a) finance records it and pushes it to the Staff Ledger automatically, (b) finance
records it as cash-out only and you keep entering it in the ledger as today, (c) finance is the only
place and the ledger pulls from it. **My recommendation: (a)** — one entry by the pharmacy, one
truth in the ledger.

**Q3 · Sundays.** The pharmacy was open on some Sundays in Apr–Aug and closed on 12. Should Sunday
default to **closed** (so a missing Sunday is silent) with a "we were open" toggle, or **open** (so
every missing Sunday shouts)?

---

*S179 · Sanjeevni Medical Module Build Contract v1 · DRAFT, not canonical, no manifest row.*
*No patient data, no numbers, no secrets in this document.*
