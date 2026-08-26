# S201 Part 1 (addendum) — the `.xlsx` time bomb defused by removing the dependency

**25-Aug-2026 · manojz · installed and proven. Companion to `S201_Part1_Capture_And_Agent_Record.md`.**

## The fault

The pipeline read `.xlsx` through **xlrd 1.2.0**, which lost `.xlsx` support at **Python 3.9** —
`ElementTree.getiterator()` was removed there. manojz reads `.xlsx` today *only because its Python
predates that*.

The day manojz's Python is upgraded, **every `.xlsx` Marg export becomes "not a readable .xls"**.
It would present as a refusal, not a breakage — the files would quietly pile into `_REFUSED` and the
day would look like an operator error. Marg does emit `.xlsx` (`ITEM DUMP STOCK 9 AUG 2026.xlsx`).

The medical PC is already past that line: its bundled python is **3.11.9**, and has **neither
`xlrd` nor `openpyxl`** installed at all.

## Why not just install openpyxl

Because that means pip on every clinic PC, including a bundled interpreter with no packages and no
reliable way to add them — and the Lab PC after that. **A dependency that must be installed on every
machine is a dependency that will be missing on one of them.** The S195 setup doc already told
someone to `pip install xlrd==1.2.0`; it was never done against the portable interpreter, which is
why the medical guard has never been able to run.

## What was done instead

An `.xlsx` is a zip of XML, and the standard library can open a zip and parse XML. **`xlsx_stdlib.py`
reads it directly — no third-party package, nothing to pin, works on any Python 3.**

`MargPull/xlsx_stdlib.py` = `bbe11a8953f66c27126c48e773cfbe35`

Deliberately not a general library: it returns cell values as text and numbers, which is all the
Marg parsers ever ask of it. Numbers come back as floats exactly as xlrd returned them, so nothing
downstream sees a different shape.

`marg_router.open_sheet()` now routes `.xlsx` to it, keeping `xlrd` as a fallback for an odd file
and for OLE2 `.xls`, which xlrd still handles correctly on every Python.

## Proof, not assertion

1. **Cross-validated against `openpyxl`** on a real Marg export
   (`SALE BOOK FORMAT.xlsx`, `9bf5c008`): **170 cells compared, 0 mismatches**, same sheet name,
   same dimensions.
2. **Proven on a Python where xlrd fails.** Run in a Python 3.10 shell:
   - `xlrd` → `'ElementTree' object has no attribute 'getiterator'`
   - `marg_router.open_sheet()` → 33 rows × 4 cols, title
     `MAIN STORE CLOSING STOCK AS ON 09-08-2026`, header
     `['S.No.', 'Description', 'Total Stock', 'Unit']`
3. **Every `.xlsx` in the archive** — 9 files — read with the standard library alone.

## Also closed in this pass

- **`_UPLOAD_NOW` and `MARG_PICTURE.txt` are now refreshed by the 10-minute pull**, not only when a
  human runs `MARG_STATUS.bat`. The surface that says *"someone must upload this by hand"* was
  stale exactly when it mattered: a failed send was retried silently and nothing told anyone to
  step in. (Audit gap G10.)
- **`medical_inventory.py` now tracks the watcher's extension list** (`.xls`, `.xlsx`, `.pdf`) and
  reads `.xlsx` without xlrd. The census must never again grade the pipeline's homework with the
  pipeline's own answers — that circularity is what produced the false "0 not captured" earlier
  today.

## Live pins on manojz after this pass

| file | md5 |
|---|---|
| `marg_router.py` | `bbc50f9172211925755eeaa25920d1cf` |
| `marg_watch.py` | `aa55cdb51521c796a9167ee7d27a368f` |
| `xlsx_stdlib.py` | `bbe11a8953f66c27126c48e773cfbe35` |
| `marg_gate.py` | `ca8b2af9c60879b9d764c9df0454a3bf` |
| `marg_rescan.py` | `481d567bae762ebd5a504d3721c60df8` |
| `signatures.json` | `78ef009d01cb2a74073a799b5178f627` |
| `PULL_FROM_MEDICAL.bat` | `ddd9b88e0faf51cbfa7da7e9ead50b05` |

Selftests after the change: router **OK** · gate **39/39** · rescan **12/12** · watcher **OK**.
The picture: every trading day 17→24 Aug has a report and the server has it; 0 missing, 0 unsent.

## Still owed

`xlsx_stdlib.py` is not yet on the medical PC. It is not needed there today — the watcher does not
parse — but it becomes required the moment any verification runs on that machine, and it is the
thing that would let `guard_and_send.py` work there at all. Add it to the `_kit` allowlist when
that step is taken.

---
*S201 Part 1 addendum · no patient identifiers reproduced; no tokens read or printed.*
