# S206_F216_DISPOSITION — staged, not published

Built 27-Aug-2026 in an attended session on manojz. **Nothing here is installed.**
Nothing was written to the VPS, the medical PC, or `H:\My Drive\...\ToMedical\`.

## What is in this folder

| file | what it is | state |
|---|---|---|
| `DISPOSITION_85.md` | Q3 finished: per-file disposition for **all 85** untracked VPS files | **measured** |
| `live_pins_IGNORE_block.txt` | the 23 IGNORE rows, in the real TSV syntax | **syntax verified** against `S187_V1a/verify_live_pins.py` |
| `VERIFY_KB_CANON.bat` + `.ps1` | Phase 0 Lite step 1 **on Windows** — `md5sum` is not a Windows command | **UNTESTED ON WINDOWS** |
| `EOL_CENSUS_F214.txt` | Q4: line-ending census of every `.bat`/`.cmd`/`.vbs`/`.ps1` | **measured** |

## How the dispositions were decided

Not by reading filenames. An md5 index of all **2,038** files in the repository working
tree was built, and every one of the 85 census md5s was looked up in it. `CAP` means no
identical bytes exist anywhere in git — measured, not assumed.

## The one thing to run first

Double-click `VERIFY_KB_CANON.bat`. It is read-only and it replaces the Phase 0 command
that does not work at a Windows prompt. **It has never been run on Windows** — if it is
wrong, it is wrong on its first run, which is why it is staged and not written into the
runbook yet.

---
**Renamed S206:** `live_pins_IGNORE_block.tsv` → `.txt`. `.gitignore:40 *.tsv` sits
under the PATIENT-DATA block, so the F-100 gate refused to publish this kit while
it carried that extension. The file is a config block destined to be pasted into
`live_pins.txt` — which is already `.txt` — so the extension was wrong, not the
gate. **The gate was left strict (S205 ruling); the file moved instead.**
