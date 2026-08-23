# Marg Report Router — content-based identification, renaming, archive, upload
**S195 · 21 Aug 2026 · design for approval (not built yet)**

Owner's requirement (verbatim intent): Marg dumps EVERY report type — sale, stock,
purchase, … — into the same per-login folder with the same meaningless names
(`REPORT_1.XLS`, `REPORT_2.XLS`). The system must decide the report type **from the
file contents**, rename it by the **date(s) of the data it contains**, archive it in a
proper folder on the local PC, keep it available for upload, and **verify integrity at
source — mandatory**.

## 1. Evaluation of Marg's export naming (evidence, not assumption)
Verified against 8 real exports:
- Path: `D:\MARGERP\users\<login>\report\REPORT_<N>.XLS`. `<N>` is a **slot number**,
  not an identity. Every report type shares the folder and the naming.
- **The filename carries zero information** — no type, no date, no variant. Proof: two
  different files in this sample set are both named `REPORT_1.XLS`, one containing
  01-Aug data, the other 19-Aug.
- **Slots are reused, so exports overwrite silently.** An un-archived report can be
  destroyed by the next export.
- Save-time stamps are not business dates (the S193 sender already warned of this).
- BUT every export has a rigid, parseable preamble:
  - row 0-2 company / address / phone
  - **row 3 = TITLE + PERIOD** — `BILL WISE SALES STATEMENT AS ON DD-MM-YYYY`
    or `... FROM DD-MM-YYYY TO DD-MM-YYYY`
  - **row 4 = COLUMN HEADER** — e.g. `BILL NO. | DESCRIPTION | D.R. | GROSS AMT. |
    DISCOUNT | TAX | DR/CR | NET AMT. | CASH`
  - row 5+ = data, grouped by date
Conclusion: content-based identification is not only possible, it is the **only**
sound method. (D188: a file is not identified by its name.)

## 2. Design — the Router
A single tool on the medical PC (`marg_router.py` + a .bat/Task Scheduler entry),
run on a schedule AND fired by the AHK macro immediately after each export.

### 2.1 Identify — two independent signals, both must agree
A **signature registry** (data, not code) maps each known report to:
`{ title_regex, expected_header_columns, type_code, variant }`
- Title matches **and** header matches → identified.
- Title matches, header does not → **REFUSE** (layout changed, or wrong variant such
  as the CASH-less `Summary-1`). Never parse on a partial match.
- Nothing matches → **UNKNOWN** → quarantine, keep the file, alert. Never guess.

Seeded with the one type we know cold:
`SALE_BILLWISE` variants `DETAIL` / `SUMMARY1` (from `marg_report.py`, the live server
parser). STOCK / PURCHASE / others are added once samples exist (see §5).

### 2.2 Extract the data dates
From the title (`AS ON` → single day; `FROM..TO` → range), then **cross-check against
the data rows' own date groups**. Title and body must agree or the file is refused —
this is verification at source, not a rename convenience.

### 2.3 Verify integrity AT SOURCE (mandatory)
Before anything is archived or made uploadable:
- **Completeness** — the file must end with its terminal marker (`GRAND TOTAL :` for
  sale reports). Absence = truncated export, the defect that bit 15-Aug. Refuse loudly.
- **Arithmetic** — bills sum to DAY TOTAL, days sum to GRAND TOTAL, footer bill count
  matches rows read (`marg_report.py` already does exactly this).
- **Variant sanity** — e.g. a sale report without a CASH column can never be used for
  the cash/UPI split; refuse rather than ingest a half-truth.
- Every file gets a recorded verdict: `VERIFIED` or `REFUSED + reason`.
For an as-yet-unparsed type (stock/purchase), verification is limited to structural
checks (title/header agreement, non-empty, clean end) until a parser exists — and the
file is archived but marked `UNVERIFIED`, never auto-uploaded.

### 2.4 Canonical rename
`<TYPE>_<VARIANT>__<dates>__<exportstamp>__<hash8>.xls`
- single day: `SALE_BILLWISE_DETAIL__2026-08-19__20260821-0623__a1b2c3d4.xls`
- range: `SALE_BILLWISE_DETAIL__2026-08-01_to_2026-08-15__…`
Keeping the export stamp + content hash is deliberate: **the same business day gets
re-exported after corrections, and we want every version kept** (see §4).

### 2.5 Archive layout (local PC)
```
D:\MargArchive\
  SALE_BILLWISE\2026-08\<canonical>.xls
  STOCK\...              PURCHASE\...
  _UNKNOWN\              <- unidentified; kept, alerted, awaits a signature
  _REFUSED\              <- failed verification + a .txt beside it saying why
  index.csv              <- append-only ledger, the spine
```
`index.csv` columns: `seen_at, type, variant, date_from, date_to, export_stamp,
md5, verdict, reason, archived_path, source_path, uploaded_at`.
This ledger is what makes the monthly compare and any audit trivial.

### 2.6 Availability for upload
Only `VERIFIED` sale reports become eligible. The router places/links them in
`D:\SendToClinic\Outbox\`; `GUARD_AND_SEND.bat` sends from there by explicit path
(the S195b explicit-path mode already supports exactly this). Maker/checker (D325)
is untouched: the sender stages; **Dr Manoj alone applies**.

### 2.7 Idempotence
Content-MD5 keyed. A hash already in `index.csv` is never re-archived and never
re-sent — mirroring `SEND_TO_CLINIC.bat`'s existing dedup. Safe to run every 10
minutes, and safe to run twice.

## 3. Why this is strategically the right layer
The owner's goal is a **dashboard free of Marg, fed by several Marg reports**. This
router is that intake layer: identification + verification + archive + a ledger,
independent of any one report type. The daily sale flow becomes its first consumer;
stock and purchase attach later by adding a signature and a parser, with no change to
the plumbing. It also fixes the silent-overwrite hazard, because content is captured
and hashed promptly rather than trusted to survive in a reused slot.

## 4. Ties into the monthly correction check (owner's decision, 21 Aug)
Decision: **monthly compare + flag only** (no auto re-push), framed as a check on the
**quality of Amir's work**. Window: to be tuned once we see real data.
Because the archive keeps EVERY export of a day, the monthly job can show:
- the FIRST export of each day (what the books were given), vs
- the LATEST export of that day (Marg's corrected truth), vs
- what the books actually hold,
and flag every day where the cash/UPI split moved, by how much, and when it was
changed. That is a direct, evidence-based quality measure — impossible today because
nothing keeps the earlier versions.

## 5. What is needed to finish (from Dr Manoj)
**One sample export of each other report type** into that folder — stock, purchase,
and any other in routine use. Each sample lets me add an exact signature. Until a type
has a signature it lands in `_UNKNOWN` (kept and flagged, never guessed at, never
uploaded).

## 6. Build order (proposed)
1. Router core: identify → verify → rename → archive → `index.csv`, with the
   SALE_BILLWISE signature only. Dry-run mode first (reports what it *would* do).
2. Point it at the existing archive of real exports to prove classification on
   history before it touches anything live.
3. Wire the Outbox + the macro trigger; the daily flow then runs end to end.
4. Add STOCK / PURCHASE signatures as samples arrive.
5. Monthly compare job (§4) once the archive has a few weeks of versions.

## 7. Open risks
- **Signature drift**: a Marg update could change a title or header. Mitigated by
  refusing on mismatch (never silently mis-parsing) and by the `_UNKNOWN` quarantine.
- **Overwrite race**: if the router runs rarely, a slot can be overwritten before
  capture. Mitigated by the macro firing the router immediately after each export,
  plus a short schedule interval.
- **Unknown types accumulating**: harmless but needs a periodic look at `_UNKNOWN`.
