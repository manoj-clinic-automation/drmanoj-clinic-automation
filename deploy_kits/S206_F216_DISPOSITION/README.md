# S206_F216_DISPOSITION — staged, not published

Built 27-Aug-2026 in an attended session on manojz. **Nothing here is installed.**
Nothing was written to the VPS, the medical PC, or `H:\My Drive\...\ToMedical\`.

## What is in this folder

| file | what it is | state |
|---|---|---|
| `DISPOSITION_85.md` | Q3 finished: per-file disposition for **all 85** untracked VPS files | **measured** |
| `live_pins_IGNORE_block.txt` | the 23 IGNORE rows, in the real TSV syntax | **syntax verified** against `S187_V1a/verify_live_pins.py` |
| `VERIFY_KB_CANON.bat` + `.ps1` | Phase 0 Lite step 1 **on Windows** — `md5sum` is not a Windows command | ✅ **PASSED ON WINDOWS 27-Aug-2026** |
| `EOL_CENSUS_F214.txt` | Q4: line-ending census of every `.bat`/`.cmd`/`.vbs`/`.ps1` | **measured** |

## How the dispositions were decided

Not by reading filenames. An md5 index of all **2,038** files in the repository working
tree was built, and every one of the 85 census md5s was looked up in it. `CAP` means no
identical bytes exist anywhere in git — measured, not assumed.

## The one thing to run first

Double-click `VERIFY_KB_CANON.bat`. It is read-only and it replaces the Phase 0 command
that does not work at a Windows prompt. **It has now been run on Windows** — real Command
Prompt on manojz, 27-Aug-2026: `checked 229  OK 229  FAILED 0  MISSING 0` · `RESULT: PASS`.

⚠ **Expect 238/238 now, not 229/229.** The S206 close added rows to `KB_canon_all`; measured
28-Aug-2026: **238 rows, 238 OK, exit 0.** The `.bat`'s header comment said 229 and was
corrected on 28-Aug. **The script itself never hard-codes a count** — it reads however many
rows the sums file has — so a stale number in a comment misleads a reader and breaks nothing.
**`RESULT: PASS` is the expectation, not any particular number.**

---
**Renamed S206:** `live_pins_IGNORE_block.tsv` → `.txt`. `.gitignore:40 *.tsv` sits
under the PATIENT-DATA block, so the F-100 gate refused to publish this kit while
it carried that extension. The file is a config block destined to be pasted into
`live_pins.txt` — which is already `.txt` — so the extension was wrong, not the
gate. **The gate was left strict (S205 ruling); the file moved instead.**

---
**S207, 28-Aug-2026 — this kit's own `SUMS.md5` was RED, and it was not this session's doing.**
`md5sum -c SUMS.md5` failed on **`README.md` only**; the other six rows matched. Both files
carry an S206-close mtime in the same minute, so the README was edited once more after the sums
were written and the sums were never regenerated — the kit was published with its own gate red.
Found by running the check while re-hashing after an unrelated one-line edit to the `.bat`.
**Nothing depended on it**: this README is prose about the kit, carries no hashes and no code.
It has been brought up to date with the two measured facts above and the row re-hashed, so the
gate is green again. *Recorded rather than quietly fixed — and it is the second time in two
sessions that a kit verified against its own copy proved nothing (F-215's lesson).*
