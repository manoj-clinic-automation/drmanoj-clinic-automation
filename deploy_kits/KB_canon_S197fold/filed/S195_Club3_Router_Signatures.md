# S195 — Club 3 progress: router signatures (23-Aug)

## Proven end to end today

The owner generated stock, expiry and purchase reports on the medical PC and let Marg save
them the usual way. Within one 10-minute cycle each, the puller captured them; the router
filed the datable ones in `_UNKNOWN` and refused the undatable ones **with written
reasons** — nothing guessed, nothing lost. The capture pipeline works for arbitrary new
report types.

## Signatures added (data edits + one small code change)

| type | matched by | dated by | note |
|---|---|---|---|
| `STOCK_CLOSING/DEFAULT` | `CLOSING STOCK AS ON` (store-agnostic — the store name precedes the phrase) | the AS ON date in its own title | sample: SCRAP STORE 01-07-2026 |
| `STOCK_EXPIRY/DEFAULT` | `EXP. BEFORE` | **its own file time** — new `dating: file_mtime` signature field | the file's only content dates are FUTURE expiries |
| `PURCHASE_SUPPLIERWISE/DEFAULT` | `SUPPLIER WISE PURCHASE STATEMENT` | the FROM..TO range in its own title | header `SUPPLIER NAME · DATE · BILL NO. · CASH · CREDIT`; **feeds the NEFT pre-fill eventually**. Sample: 01-07..31-07-2026, VERIFIED on dry-run |

All: `structural` verify, `uploadable: false` (archive only — nothing goes to the VPS yet).

**Code change** (`marg_router.py`, process()): a signature may declare
`dating: file_mtime`; used only when content dating fails. Pre-flighted: `py_compile`,
`pyflakes`, the router's own `--selftest`, then `--dry-run` against the **real captured
files → VERIFIED** with correct types and dates. Backups beside the originals
(`.before_S195_stock`).

Samples tidy-copied into `STOCK_CLOSING/2026-07/`, `STOCK_EXPIRY/2026-08/`,
`PURCHASE_SUPPLIERWISE/2026-07/` under canonical names; index rows keep their honest
original verdicts as history.

## The overwrite hole — CLOSED (medical-side resident watcher)

The owner correctly challenged the capture design: Marg reuses slot names (REPORT_1.XLS…),
so anything that looks on a schedule loses an export overwritten between looks.
`marg_watch.py` was *designed* event-driven for exactly this — but was **deployed only in
`--once` mode** on the manojz 10-minute task: a real up-to-10-minute loss window. This
morning's captures survived it by luck (writes straddled pull boundaries).

**Fix shipped:** the watcher now runs **resident on the medical PC itself** —
kernel-notified (ReadDirectoryChangesW), captures to `D:\SendToClinic\_captured` within
seconds of Marg writing, dedup by content, never writes inside MARGERP. Its own selftest
proves three same-slot overwrites all survive. Kit (`INSTALL_WATCHER.bat` +
`START_MARG_WATCHER.bat` + `marg_watch.py`) delivered via the ToMedical pipe to
`FROM_CLINIC`; owner double-clicks INSTALL once (logon task, no admin). manojz's pull
sweeps `_captured` too (bat patched, backup `.before_S195_captured`).
**On-medical-PC confirmation point:** generate any report → a copy appears in
`D:\SendToClinic\_captured` within ~10 seconds.

## Repo mirror

`margpull/` in the repo now carries router `e5418830…`, **signatures `e216fad8…`**
(4 types), watcher, pull bat, README + `margpull/medical_watcher/` (the medical kit).
Publish with PUBLISH_ALL. Original repo-gap finding stands for the Auditor: these existed
only on manojz until today.

## Docterz — three exports characterised (from D:\Downloads, access granted)

| file | shape |
|---|---|
| `consultation_report_YYYY-MM-DD.csv` | per-visit billing: patient id/demographics (PHI), bill/collected/pending, per-head amounts + discounts, payment mode, collector, time-of-day |
| `clinical_data_report_YYYY-MM-DD.csv` | **NEW export** — everything above PLUS prescriptions (drugs, dosages, durations) and payment splits |
| `followup_logs.csv` | appointment id, mobile, patient, followup text/date, doctor |

CSVs on manojz — different ingestion path from the Marg router; ingest design belongs with
the VPS clinic-side work. Headers on record. **PHI present — mask in all outputs.**

## Still awaited for Club 3

- **Bill-wise purchase** export — the supplier-wise one arrived and is signed; the
  bill-wise one either fell to a same-slot overwrite (the last ever to be lost, if so) or
  was not generated. **Re-export once the watcher is installed** — from then on even
  back-to-back same-slot exports are all safe.
- **Labmate** export — lab PC.
