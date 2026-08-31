# S212_LIVE_TOOLS — the reinstall repair kit

**31-Aug-2026. STAGED, NOT INSTALLED. Nothing on either machine was touched.**

## Why this exists

`S205_LIVE_TOOLS` is the reinstall kit for both Windows machines. Measured
today against the running machines:

**manojz would rebuild, with one silent defect.** 18 of its 19 files are
byte-exact. The one that is not is `signatures.json` — kit has **7** report
signatures, live has **8**, and the missing one is **`PURCHASE_ITEMWISE`**, the
signature installed on 27-Aug and called at the time *"the biggest single
unlock — five months of item-level purchase data quarantined."* A rebuild would
run, pass all six of its own proof checks, and quietly route every item-wise
purchase report to `_UNKNOWN`. None of the six checks looks at signature count.

**The medical PC would NOT rebuild correctly.** Three files drifted and four
exist in no kit at all.

| file | kit | live | consequence of restoring the kit |
|---|---|---|---|
| `medical_agent.py` | `7b9a76f2` S203.3 | `70d5c4e3` **S205.1** | loses `_win_norm`, `_dest_ok`, `manifest_files`, `_kit_gate_ok` — the whole kit-install gate that stops the agent writing a file to the wrong place |
| `SEND_TO_CLINIC.bat` | `e19a8a77` **v3** | `fdaf7100` **v4** | **re-arms AF-1 / F-206** — see below |
| `GUARD_AND_SEND.bat` | `c393bcc3` v1 | `957a5f16` **v2** | v1 trusts the filename; v2 looks inside every `REPORT*.XLS` for a genuine complete report. v1 is the version that said "NO REPORT FOUND" on 21-Aug with a good file sitting there. **This is the icon reception uses.** |
| `marg_export_macro_v3.ahk` | — | `ab792eb8` | **in no kit.** No export macro at all after a rebuild. |
| `marg_macro_calib.txt` | — | `37806b73` | **in no kit, and unreproducible** — screen coordinates calibrated against Marg's own UI on that machine. |
| `find_sale_report.ps1` | — | `5b5e6162` | **in no kit.** Helper in the send path. |
| `xlrd/` | — | 11 files | **in no kit and nowhere in git.** Without it the machine cannot read `.xls`, which is the only format Marg writes. |

### AF-1 / F-206 — the one that matters most

The kit's v3 decides success from the reply **body alone**:

    findstr /c:"ACCEPTED-FOR-REVIEW" "%RESP%"

It does not delete the previous reply first and never reads the HTTP code. So a
timeout leaves **yesterday's body** on disk, `findstr` finds `ACCEPTED-FOR-REVIEW`
in it, the script prints ACCEPTED, and **the report's md5 is written into
`sent_hashes.txt` — permanently blacklisting a sale report that was never sent.**

The live v4 requires **both**:

    if "%HTTP%"=="200" findstr /c:"ACCEPTED-FOR-REVIEW" "%RESP%" >nul 2>&1 && set "VERDICT=ACCEPTED"

and deletes `last_response.txt` / `last_http.txt` before curl runs.

**`REINSTALL_MEDICAL.md` §8 still describes AF-1 as unfixed.** It was fixed on
27-Aug at 01:12. After a rebuild from `S205_LIVE_TOOLS`, that document would be
true again.

## The root cause, and it was predicted

`S205_LIVE_TOOLS/MANIFEST.md` says, in its own words: *"These are the bytes as
at the S205 open… the moment the S205 kits are installed, two of these 24 files
are stale."* They were installed **that same night, 27-Aug 01:12 and 01:21.**
Three files went stale within hours of capture, and **no re-capture has happened
in the five sessions since** — while `SUMS.md5` verified green throughout,
because it hashes the kit against itself.

That is F-215, one generation on. A gate that compares a thing to itself cannot
detect drift.

## What this kit contains

Only the drifted and the missing. The 18 manojz files that already match are
deliberately not duplicated — one live-and-editable copy per file (D202/F-201).

    manojz/signatures.json          the live 8-signature registry
    manojz/xlrd/                    33 files, vendored, absent from git
    medical/medical_agent.py        S205.1
    medical/SEND_TO_CLINIC.bat      v4, AF-1 fixed
    medical/GUARD_AND_SEND.bat      v2
    medical/marg_export_macro_v3.ahk
    medical/marg_macro_calib.txt    machine-specific, unreproducible
    medical/find_sale_report.ps1
    medical/xlrd/                   11 files, vendored, absent from git

**Not included, deliberately:** `token.txt` (a secret, never in the repo),
`AutoHotkey64.exe` (1.27 MB third-party runtime), and all state and log files.

## The verification that matters

`VERIFIED_AGAINST_LIVE.md` records every file's md5 **measured against the live
source today**, not against this kit's own `SUMS.md5`. Both gates are green;
only the first one proves anything about the machines.

## What is still owed after this

1. **Correct `REINSTALL_MEDICAL.md` §8** — record AF-1 as fixed at S205.
2. **Add a numbered re-capture step to the close routine.** A capture step that
   is not numbered is one that gets forgotten — which is exactly what happened.
3. **Make the re-capture verify against the live source**, never against itself.
4. `AutoHotkey64.exe` — decide whether a third-party runtime belongs in the
   repo, or is fetched at rebuild time.

---
*S212 · 31-Aug-2026 · captured from live, verified against live, installed nowhere.*
