> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 by `MARG_AND_MEDICAL_PC_MASTER_REFERENCE_v3.md` §3.3 and §3.4**
> (md5 `579ea885e440e76af73de3ecc4542d71`) — §3.3 for how the agent actually starts (and the
> trap that `Stop-Process -Name python,pythonw` kills the supervisor, which only returns at logon),
> §3.4 for how to deliver a change to the medical PC — with the current pins in **§3.2**, measured on
> the machine on 26-Aug.
> **Every manojz and medical-PC pin in this record is superseded**; `medical_agent.py` moved again on
> 26-Aug. The 10:37 watcher-death timeline is history and stays here.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S201 Part 1 — capture everything, and make the medical PC report in · LIVE RECORD

**25-Aug-2026 · recorded as it moved (F-97). manojz side COMPLETE and tested; medical side
PARTIALLY installed — see §5.**

---

## 1 · THE INCIDENT THAT SET THE PRIORITY

**The medical-PC capture watcher died at 10:37 and was discovered at 14:49, by accident.**

The survey run at 14:49 reported `NO python process is running. THE WATCHER IS DOWN`. Working
backwards: `_captured` held the 08:16 and 08:27 exports, so the watcher was alive then. At
**10:37:00** the owner saved `REPORT_2.XLS` (the 22-Aug report) and it is **not** in `_captured`.
At 10:37:41 Marg wrote `marg_system_shutdown…tmp`. Nothing was captured after that.

**That day's report survived on redundancy, not on design.** manojz's 10-minute pull reads
`\\medical\MARGERP\users` directly, so it collected `REPORT_2.XLS` at 10:40 without the watcher.
Two independent paths existed and one of them worked — and *nothing told anyone the other had
failed*. This is blind spot (a) from the S201 audit: watcher death, no coverage, unbounded latency.

It also proves the audit's structural claim: every server-side health check watches **arrival at
the VPS**. Nothing there can see the medical PC. The pipeline must report in.

---

## 2 · THE DELIVERY CHANNEL — proven both directions

Google Drive for Desktop is installed on the medical PC (streaming mode, `F:\My Drive`). The
`ToMedical` folder created at S195 had been a dead drop since 23-Aug: its own `READ ME` describes a
relay Drive → manojz → medical `FROM_CLINIC` that was **disabled at S195** when the SMB write
returned ERROR 5. Drive-on-medical makes that relay unnecessary.

```
Cowork  --device_commit_files-->  H:\My Drive\...\ToMedical      -> syncs down to medical F:\
medical --writes-->              F:\My Drive\...\FromMedical     -> syncs up to H:\ and Cowork
```

Both legs tested live: a probe file reached medical; `SURVEY.txt` and `heartbeat.txt` came back and
were read from here. **No inbound access to the medical PC is required for either direction.**

Routes explored and ruled out: **Tailscale SSH** — server is Linux/macOS only, Windows support is an
open feature request. **Writable SMB share** — viable (one permission change on medical) and still
worth doing. **PowerShell Remoting over Tailscale** — the real control layer, not yet built.
**Cowork app on medical** — a session binds to one device, so it cannot replace manojz.

---

## 3 · WHAT WENT LIVE ON MANOJZ (complete, tested)

| file | md5 | change |
|---|---|---|
| `MargPull/marg_router.py` | `d63045b15011a51cd5e86757c06fbbb9` | PDFs get their own path (`process_pdf`): `%PDF` header check, **`%%EOF` truncation check**, dated by file mtime, archived to `DOCUMENT_PDF/<YYYY-MM>/`, never uploadable. **And the scan filter widened** — `main()`'s walk only looked for `.xls/.xlsx`, so a captured PDF would never have been handed to `process()` at all. Two filters decide what is seen; both must agree. Selftest OK, +4 PDF checks. |
| `MargPull/marg_watch.py` | `aa55cdb51521c796a9167ee7d27a368f` | accepts `.pdf`; magic bytes now checked **per extension**, so a PDF renamed `.xls` is refused at the watcher instead of failing downstream as an unreadable spreadsheet. |
| `MargPull/signatures.json` | `78ef009d01cb2a74073a799b5178f627` | + `STOCK_CLOSING / TOTALS` (Part 0) |
| `MargPull/marg_gate.py` | `ca8b2af9c60879b9d764c9df0454a3bf` | outbox sender (Part 0 session work) |
| `MargPull/marg_rescan.py` | `481d567bae762ebd5a504d3721c60df8` | quarantine rescue (Part 0) |
| `MargPull/PULL_FROM_MEDICAL.bat` | `d4af22f608a6362da720ee42e10acb7c` | drains the outbox each cycle + `_last_pull.txt` heartbeat |

Backups: `.before_S201`, `.before_S201_pdf`.

**PDF path tested end to end on the real router**, dry run, on manojz:
- a complete PDF → `VERIFIED · DOCUMENT_PDF` with the honest reason recorded in the index:
  *"captured and archived. A PDF cannot be read into the books — if these figures are needed, run
  the same report again and save it as Excel."*
- a truncated PDF → `REFUSED · TRUNCATED — no %%EOF at the end`.

**Capturing a PDF is not the same as being able to use it.** No figures can be read out of one on
these machines. It is kept, hashed, dated and offsited so it stops being invisible; it does not
become data. That distinction is written into the index row, not just into this doc.

---

## 4 · THE MEDICAL AGENT

`medical_agent.py` (S201.4) — stdlib only; the bundled python is 3.11.9 with **no third-party
packages at all** (`xlrd` and `openpyxl` both absent — see §6).

- **Supervises the watcher** as a child process. Checks every 30s; restarts within a minute of a
  death and counts the restarts. What happened at 10:37 becomes a logged, self-healing event.
- **Heartbeat every 5 minutes** into `FromMedical`: watcher alive/pid/restarts, what it is
  *actually* watching (read from the running configuration), captures today, **the installed
  watcher's own md5**, the kit folder's status, Marg's report slots, disk free, and —
- **`IGNORED`: files in the watched folders the watcher cannot take.** The PDF blind spot made
  countable. A report the pipeline skips now appears by name instead of being invisible while a
  downstream alarm blames the network.
- **Applies allowlisted updates** from `ToMedical/_kit`: compile-checked, backed up, and
  **verified by hash after writing**. The agent never updates itself — a process overwriting its
  own running code is how an unreachable machine is lost.

---

## 5 · WHAT IS NOT DONE

**The medical PC is still running the OLD watcher** (`25126388…`, `EXTS = (".xls", ".xlsx")`).
Confirmed from the manojz mirror of `\\medical\SendToClinic`, not inferred.

Installer v2 failed: it copied the new watcher to a temp file, compile-checked it, then tried to
`move` it over `marg_watch.py` **while the watcher was still running** → *Access is denied* → the
temp file `_kit_marg_watch.py` was left behind and the original never changed. **And it printed
`UPDATED` anyway**, because the move's failure did not stop the script.

Installer **v3** (in Drive, awaiting a run) fixes both: everything is stopped *before* any file is
touched, the read-only flag is cleared, and the installed file is **hash-compared against the
source** — printing `UPDATED and VERIFIED` or `***NOT UPDATED***`, never a guess.

Also pending: `openpyxl` on the medical python (§6); the live PDF test; PowerShell Remoting.

---

## 6 · FAULTS FOUND — for the register

- **F-### · The `.xlsx` time bomb.** manojz reads `.xlsx` only because its Python predates 3.9;
  `xlrd 1.2.0` lost `.xlsx` support there (`ElementTree.getiterator` removed). The day manojz's
  Python is upgraded, **every `.xlsx` Marg export becomes "not a readable .xls"** — and it will look
  like a refusal, not a breakage. Marg does emit `.xlsx`. Fix: `openpyxl` for `.xlsx`, `xlrd` for
  OLE2 `.xls` only.
- **F-### · The medical guard cannot run at all.** `guard_and_send.py` needs `xlrd`; the bundled
  python has neither `xlrd` nor `openpyxl`. The S195 setup doc says to `pip install xlrd==1.2.0`,
  which was never done against the portable interpreter — and on 3.11 it would not give `.xlsx`
  support anyway.
- **F-### · Watcher death is unmonitored** (closed by §4, once v3 is installed).
- **F-### · `NEEDS_UPLOAD` and `FROM_CLINIC` do not exist** on the medical PC. The guard's
  failure-parking folder was never created.

### Faults I introduced this session, recorded because they are the same classes we are fixing
1. **`log()` wrote to stdout before the log file.** Under `pythonw.exe` there is no console and
   `sys.stdout` is `None`, so the agent died on its first line leaving no trace of why — inside the
   tool built to end silent failures. Fixed: file first, console if present, plus a crash handler
   that writes a traceback locally and to Drive.
2. **Installer v2 reported success it never verified** — the same fault as AF-1's sender, which this
   session criticised that morning.
3. **A large PowerShell paste was reordered by the console**, leaving it stuck in continuation mode.
   Delivery moved to a double-clicked `.bat`; a file that is *run* cannot be reordered by a terminal.

---
*S201 Part 1 · manojz complete and tested; medical awaiting installer v3. No patient identifiers
reproduced; no tokens read or printed.*
