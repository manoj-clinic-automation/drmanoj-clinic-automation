# Kit S187_M1a — B5: the pushed Marg export (D325)

**Session 187 · 18 Aug 2026 · reception produces the record; the checker alone moves it into the books.**

## What ships

| file | md5 | what |
|---|---|---|
| `finance_app_M1a.py` | `81c26653cda7e4651fc737e4dea16599` | 3 new routes: `/finance/api/marg-push` (scoped `FINANCE_MARG_TOKEN`, stage-only, file deleted in-request), `/marg-push/list` + `/marg-push/apply` (checker-only, replays staged CSVs through the same guarded ingest). Built on the box-verified `d04167a8…` bytes. Purely additive. |
| `finance_workbench_M1a.html` | `420f82c2846bc49d0d12ab5040d8c542` | the "Pushed Marg reports — awaiting your check" card with per-push Apply. |
| `SEND_TO_CLINIC.bat` | — | the medical-PC sender: dependency-free (certutil + Windows curl), scans `D:\MARGERP\users\*\report\REPORT_1.XLS`, keeps dated copies (Marg overwrites the file each run — S180 recon), sent-hash log so double-sending is harmless, never writes inside `D:\MARGERP`, plain Hindi+English verdicts, every send logged. |
| `live_pins_M1a.txt` | `3eec35dd…` | regenerated from Register v5.14; exactly the two shipped files' pins moved. PENDING until the close. |
| `KB_Register_v5_14_S187.md` | `abf87e9d…` | the Register these pins came from (provenance; canonical at the close). |

## Proof before delivery

Offline selftest **359/369 = baseline 335/345 + 24 new checks, ZERO failures added** (F-87 differential;
the 10 remaining fails are seed-state artifacts, byte-identical to baseline, and passed on the live
store at S186 with the same invocation). Three F-106-family bugs found and fixed in our own tests
before shipping. The parser is not re-proved here — `marg_report`'s own selftest owns it (38/38 on
real exports); these tests stub it and drive the real ingest. Installer rehearsed: the RED path fired
on the seeded store and **restored both files byte-perfect, exit 1, pin list untouched**.

## Expected on the box

Gates OK → live selftest **~375/375** → token created (full value written ONLY to
`/root/deploy/MARG_TOKEN_S187.txt`, console shows last-4) → service restarted + answering → pin check
**42 / 0 / 0, AMBER (pending)**. A selftest failure restores everything and leaves the running service
untouched.

## After install — the medical PC (owner, once)

Copy `SEND_TO_CLINIC.bat` into a folder there (e.g. `Desktop\SendToClinic\`), paste the token from
`MARG_TOKEN_S187.txt` into its `TOKEN=` line, delete that file on the VPS, and show reception:
**run the BILL WISE report in Marg, then double-click SEND TO CLINIC.** Apply appears on your workbench.

## Owed / named, not hidden

Folding the push route's duplicated parse guards into a shared helper with `marg-upload` (deliberate
additive-only choice this kit) · the `marg_push_staging` DDL lives in code (`_marg_staging`), documented
in Register v5.14 · Hindi label review for the sender's messages · the CLI driver's own F-113 flag is
still owed (backlog 7).
