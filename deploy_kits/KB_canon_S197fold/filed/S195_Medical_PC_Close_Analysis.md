# S195 medical-PC leg — independent verification + way forward (21 Aug 2026)

Reviewed the `S195_MARG` kit produced by the medical-PC Claude session, verified
independently from the manojz side (md5s, functional run of the guard against the
kit's own sample with the vendored xlrd).

## VERIFIED GOOD (checked, not taken on trust)
- **`guard_and_send.py` = `6c248d5712731256c576722ad85f3ef1`** — byte-identical to
  the canonical build.
- **`marg_report.py` = `28b47d447cfd966411742055717a5c56`** — byte-identical to the
  LIVE server parser (`finance/marg_report.py`). So the guard's verdict on a file
  **is** the server's verdict. This was the central integrity claim; it holds.
- **Guard runs correctly on the vendored xlrd 1.2.0** (no pip needed): GREEN on the
  bundled `_setup_sample.xls` (2026-08-20, 1 bill, NET 100.00) exit 0; REFUSED with
  the correct reason + exit 2 when pinned to a wrong date. Fail-visible behaviour intact.
- **Macro is genuinely calibrated** (maximised Marg, medical PC):
  Daily Sale `1804,941` · Report Type `1132,850` · With Item Deta `984,992` ·
  View `641,1414` · Excel `1391,1254`. Hotkeys: `Ctrl+Alt+C` capture ·
  `Ctrl+Alt+G` run · `Esc` quit (F9/F10 also bound; `Ctrl+Alt+R` alternate).
- **Export-only test PASSED** on the box; `SETUP_CHECK.bat` GREEN on portable
  Python 3.11.9. `RunGuard := false` — so it currently exports and sends NOTHING.
- Good engineering added by that session: Python auto-detect that **skips the
  MS-Store stub**, vendored `xlrd/`, a one-click `SETUP_CHECK.bat`, and a portable
  Python kept OUT of the public repo (D320) with reproduce steps in the README.
- No VPS code touched, no canon pin moved, no D/F minted. Correct scope.

## THE ONE REAL BLOCKER — REPORT_1 vs REPORT_2 (filename/login mismatch)
The automation does not yet join up end-to-end:

| Piece | Looks at / writes |
|---|---|
| AHK macro (`ReportFile`) | `D:\MARGERP\users\61376\report\**REPORT_2.XLS**` |
| `GUARD_AND_SEND.bat` | scans every user dir for `**REPORT_1.XLS**` only |
| `SEND_TO_CLINIC.bat` (live, S193) | matches `**REPORT_1.XLS**` only |

On disk today: `users/50018/report/REPORT_1.XLS` and
`users/61376/report/REPORT_2.XLS` — **different files in different user dirs**.
So the macro's fresh output (REPORT_2) is never seen by the guard or the sender;
the guard would instead inspect 50018's REPORT_1, which by then is the *previous*
run. It **fails safe** (the guard's date check refuses a stale file rather than
sending it), but it will never complete a real run until this is reconciled.

Substantive note carried from the earlier analysis: the 50018 `REPORT_1` reads
**all `.CASH`**, while 61376's `REPORT_2` carries the **UPI reclassification**
(19-Aug: same ₹44,120 day, cash 18,790 / non-cash 25,330). The SENT archive files
reception actually pushes match the all-CASH shape. Which login the automation
runs under therefore decides **which version of the truth reaches the books** —
this is a money question, not just a filename question.

## WAY FORWARD (in order)
1. **Decide the single source (Dr Manoj, at the Marg GUI).** Either
   (a) run the automated export under the login whose file lands as `REPORT_1.XLS`
   (nothing else changes — the proven sender path stays byte-identical), or
   (b) keep 61376/`REPORT_2` and widen `GUARD_AND_SEND.bat` to scan `REPORT_2.XLS`
   too. (b) is a ~2-line change and safe, because the wrapper passes an EXPLICIT
   path to `SEND_TO_CLINIC.bat` (which uploads it as `filename=REPORT_1.XLS` and
   dedups by MD5). Risk of (b): if a stale `REPORT_1` and a fresh `REPORT_2` both
   pass the date check, the same day could be pushed twice — so if we take (b),
   scan ONE filename, not both.
   **Recommended: (a) if the 61376 login can be made to write REPORT_1; else (b)
   scanning REPORT_2 only.** Confirm which login carries the correct UPI split.
2. **Flip `RunGuard := true`** in `marg_export_macro_v2.ahk`.
3. **One supervised end-to-end run**: `Ctrl+Alt+G` → Marg generates yesterday's
   Detail export → guard validates → `SEND_TO_CLINIC` stages → verdict
   `ACCEPTED-FOR-REVIEW` → **Dr Manoj alone applies** at the Hub (D325 intact).
4. **Task Scheduler**: `GUARD_AND_SEND.bat any AUTO` at a chosen morning time.
   Caveat: coordinate-driven AHK needs the medical session **logged in and
   unlocked**; an RDP disconnect can lock the session and freeze mouse
   automation. Plan a console session that stays logged in.
5. Manual workflow stays the fallback throughout.

## Not blocking
Marg `.dbf` decryption stays RETIRED (thorough negative — see
`S195_Marg_decrypt_partial_key.md`). The report-export path already yields
bill-wise sales **with item lines**, which is what the Marg-independent dashboard
needs.
