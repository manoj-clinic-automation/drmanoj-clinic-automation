# Clinic Master KB — Systems Register · v1.39 (DELTA over v1.38)

**Applies over:** `Clinic_Master_KB_SystemsRegister_v1_38.md` (consolidated master).
**Session:** 75 · 2026-07-05 · **CODE CHANGED.** **KB wins on any conflict.**

This delta records the Track-1 Step-4 build (`clinic_writer.py`) and the three
architecture pivots that simplify Track-1 hosting. Everything in v1.38 not amended here
stands verbatim.

---

## §75 — SESSION 75: PC-local write-path built (Track 1, Step 4)

### §75.1 — Three pivots (context for the decisions)
1. **PC-local, not VPS.** The plan+vitals write-path tool runs on the **clinic PC**. The
   two source CSVs (`patient_master.csv`, `patient_diagnosis.csv`) already live on the
   clinic PC — the follow-up tracker writes them there and Google Drive syncs them out.
   Hosting the writer where the data already is means no patient data spreads to a
   second machine, and it honours the earlier no-VPS-hosting lean. (D136)
2. **Staff BP-only page retired.** Owner: *"I only enter the vitals in my PC; staff hand
   me a physical vitals record."* The second front door has no user. (D135)
3. **PDF/ledger storage home = clinic PC**, then Drive sync. Archive structure unchanged.
   (D137)

### §75.2 — `clinic_writer.py` — the PC-local single writer (BUILT + INSTALLED)
One self-contained Python module on the clinic PC (`C:\clinic_writer\`). Three jobs +
one read-only helper:
- **`write_vitals(...)`** — appends one row to `vitals_ledger.csv`; computes BMI /
  BMI_Category (Indian cut-offs <18.5/<23/<27.5/else) / Waist_Height_Ratio for EVERY
  row itself (mirrors the plan-tool compute() exactly); assigns next `Vitals_ID`;
  normalises Sex → M/F; stamps IST. 20-col locked schema (§67.3).
- **`write_plan(...)`** — appends one row to `plan_ledger.csv`; assigns next `Plan_ID`;
  links `Vitals_ID_Used`; stamps IST. 14-col locked schema (§67.3, D134).
- **`archive_pdf(...)`** — renders a text-faithful PDF via **reportlab** (D138) and files
  it at the D132 path (`plan_archive/<year>/<Patient_UID>/…`; new patients → `pending/`).
- **`lookup_uid_by_clinic_id(...)`** — read-only resolve of Clinic_Specific_Id →
  Patient_UID from `patient_master.csv`. NEVER writes the source CSVs.

**ID formats:** `V-YYYY-NNNNNN` / `P-YYYY-NNNNNN` — per-year running counter, 6-pad,
gap-safe (scans existing IDs for the year, takes max+1).

**Invariants obeyed:** append-only; one-writer-per-file; never writes the two read-only
source CSVs; no network / no Drive / no VPS calls (Drive sync is Drive's own job on the
folders); IST timestamps explicit.

**Verification (both machines):**
- Sandbox (Py 3.12.3): `py_compile` clean; `--selftest` 20/20 PASS; real PDF (valid
  `%PDF-`) filed correctly.
- **Clinic PC (Py 3.14.5): owner ran `--selftest` → 20/20 PASS; certutil md5 =
  `d4e20a51ead1aada8c07bead2b504100` (matches). INSTALLED + CONFIRMED 2026-07-05.**

**Status:** this is the WRITE-PATH LIBRARY. No front-end wired yet (Step 5 next). Manual
fallback (browser print, no archive) unchanged until the front-end is live.

**Repo demarcation (kit correction, same session):** `clinic_writer.py` lives in its OWN
top-level Git folder **`clinic_writer/`** — kept deliberately separate from
`followup-tracker/` because they are two distinct systems (matching `C:\clinic_writer\`
on the PC). A `README.md` in the folder documents the split. Code md5 unchanged; only the
repo location was corrected from the first S75 kit.

### §75.3 — Amendments to earlier Track-1 decisions
- **D121 (host as VPS Flask+OLS)** — AMENDED by D136: this tool is **PC-local**, not on
  the VPS. (Other portal tools on the VPS are unaffected.)
- **D122 (canonical CSV folder)** — RESOLVED by D136: canonical source is the **clinic-PC
  local `data/` folder** the tracker writes (Drive folder id
  `1aRKh1ecJVpVmPJMMupnNKGiabrKfsF1C` is its Drive mirror). Newest-by-date rule stands.
- **D124/D127 (two front doors / staff BP page)** — the STAFF-PAGE portion is RETIRED by
  D135. The single vitals writer + one-vitals-ledger design stands (one front door now:
  the doctor).
- **D133 (storage home VPS)** — AMENDED by D137: storage home is the **clinic PC**, then
  Drive sync. Archive structure (D132) and schema (D134) unchanged.

### §75.4 — Decisions (D135–D138)
- **D135** — Staff BP-only page RETIRED from Track-1 build (only the doctor enters vitals).
- **D136** — Track-1 write-path = PC-LOCAL; reads clinic-PC local `data/` CSVs; amends
  D121, resolves D122.
- **D137** — PDF + ledger storage home = clinic PC, then Drive sync; amends D133;
  archive structure unchanged.
- **D138** — PDF engine = reportlab (pure-Python, text-faithful; durable one-command
  Windows install), over HTML-render engines.

**Reserved:** D83–D92 (P1–P10). **Next free: D139.**

---

## DECISIONS INDEX — additions
- **D135** Staff BP-only page retired (doctor-only vitals entry).
- **D136** Track-1 write-path PC-local; clinic-PC `data/` CSVs canonical (amends D121, resolves D122).
- **D137** PDF/ledger storage home = clinic PC → Drive sync (amends D133; structure unchanged).
- **D138** PDF engine = reportlab (pure-Python text-faithful archive).

## SURVEILLANCE REGISTER — forward note
When the Step-5 front-end goes live on the PC it becomes a local service — at that point
add a liveness/freshness row (local app up; ledgers + `plan_archive/` writable + syncing).
Not yet applicable (no live service added this session; the writer is a library).
