# S201 Parts 2, 3, 4 (partial) — integrity, learning, and the silent stalls · LIVE RECORD

**25-Aug-2026 · manojz · installed, tested, no regressions. Companion to the Part 0 and Part 1
records.**

---

## PART 3 · Truncation is now detected for every report type

**The fault.** `ends_with()` returns `True` when a signature declares no `end_marker`, and only
`SALE_BILLWISE/DETAIL` declared one. So a purchase or stock export that stopped mid-print was filed
`VERIFIED "structural"` and looked perfectly healthy. A partial stock count is worse than none.

**Evidence first.** Every archived report of each type was opened and its tail read. Every Marg
report ends with a totals row before the advertisement line:

| type | last data row | marker adopted |
|---|---|---|
| PURCHASE_BILLWISE | `TOTAL │ 476393 │ - │ 476393` | `TOTAL` |
| PURCHASE_SUPPLIERWISE | `GRAND TOTAL │ 476393 │ - │ 476393` | `GRAND TOTAL` |
| STOCK_CLOSING (both variants) | `TOTAL │ │ 76 │` | `TOTAL` |
| STOCK_EXPIRY | `TOTAL │ │ │ 832` | `TOTAL` |

**Checked before applying, not after.** Every archived file of those types was tested against the
proposed marker first: **16 would pass, 0 would be refused.** Then applied, then every archived
report re-verified against the new registry: **26 still VERIFIED, no regressions.**

`SALE_BILLWISE/SUMMARY1` deliberately still has **no** marker — no sample of that variant exists to
derive one from, and the signature now says so in a note rather than carrying a guess. A guessed
marker would refuse real reports.

**Worth recording:** `PURCHASE_BILLWISE` totals **476,393** and `PURCHASE_SUPPLIERWISE` totals
**476,393** for the same July period. Two independently generated reports agreeing to the rupee is a
genuine cross-report integrity check, and a natural basis for the deep purchase verification Part 3
still owes.

## PART 3 · A range export now covers every day inside it *(my own bug)*

`build_picture()` and the send logic both keyed a report by `date_to` alone. A catch-up export
covering 01→15 Aug would have counted as **15-Aug only**, with the other fourteen days reading
`MISSING` — and if a newer single-day export existed for the 15th, the range file would have been
marked `superseded` and its earlier days **never sent at all**.

It never bit because the only range export we have spans a Sunday.

Fixed with `covered_days()` / `span_key()`:
- a report covers `[from..to]`, Sundays excluded;
- **the DATA range wins over the title range** where it exists — the reason Part 0 added
  `data_from`/`data_to`. A title reading `FROM 23-08 TO 24-08` over a file holding only 24-Aug rows
  describes what was *asked for*, not what arrived;
- a delivered range delivers **every** day inside it;
- a report is sent unless **every** day it covers already has a delivery at least as new — one
  uncovered day is reason enough to send the whole report;
- "newest wins" now compares within a coverage span, so a range is never collapsed onto a day.

Selftest **39 → 49**, including reversed dates, Sunday exclusion, and partial-coverage sending.

## PART 4 · The spool is routed whenever it holds anything

`marg_watch.py` routed only when *that run* captured something (`if do_route and new:`). A routing
run that died — a failed index write, a copy that raised — left its files in the spool, and **no
later run would touch them** until an unrelated new file happened to arrive. Reports could sit
unrouted indefinitely with nothing saying so.

Now: route if the spool holds anything at all. The router skips whatever is already indexed, so
routing an idle spool is cheap and idempotent.

## PART 2 · The registry now learns by itself

Adding a signature used to rescue nothing. `marg_router` blacklists a file by md5 the moment it is
indexed, so every already-quarantined example of a newly-taught type stayed frozen until a human
remembered to re-run the rescue. **Nobody did — for two purchase reports and eight stock exports.**

`marg_rescan.py --if-signatures-changed --apply` now runs inside the 10-minute task. It compares
`signatures.json`'s md5 against `MargArchive/_signatures_seen.md5` and **does nothing at all** unless
the registry has actually changed.

Proven live: silent when unchanged → fires when a signature is edited → re-arms afterwards.

## PART 5 (partial) · The manual-upload surface stops going stale

`_UPLOAD_NOW` and `MARG_PICTURE.txt` are refreshed by the pull every cycle, not only when a human
runs `MARG_STATUS.bat`. The surface that says *"someone must upload this by hand"* was stale exactly
when it mattered: a failed send was retried silently and nothing told anyone to step in.

---

## What the 10-minute task now does, end to end

```
stamp START -> pull + capture from medical -> route the spool (always, if it holds anything)
 -> re-judge quarantine IF the registry changed -> send anything the server lacks
 -> mirror medical's logs -> mirror MARG REPORTS -> offsite to Drive
 -> refresh the picture + manual-upload folder -> stamp END
```

## Live pins on manojz

| file | md5 |
|---|---|
| `marg_router.py` | `bbc50f9172211925755eeaa25920d1cf` |
| `marg_watch.py` | `2076fe1d8d145524be16ae857b3d838d` |
| `xlsx_stdlib.py` | `bbe11a8953f66c27126c48e773cfbe35` |
| `marg_gate.py` | `f09cfe61d052d5dc8dd402d2e3a85422` |
| `marg_rescan.py` | `ae92e3316efa07360c884c7c67379957` |
| `medical_inventory.py` | `3ee927f023f68dd4a0c5c8b28b0037b4` |
| `signatures.json` | `3e9cbba02ffb4e0f131738eee7a465f7` |
| `PULL_FROM_MEDICAL.bat` | `090c553aa37c6397ce3ecd03b4092103` |

Selftests: router **OK** · watcher **OK** · gate **49/49** · rescan **12/12**. All compile.
Picture: every trading day 17→24 Aug has a report and the server has it; 0 missing, 0 unsent.
Backups kept: `.before_S201`, `.before_S201_pdf`, `.before_S201_markers`, `.before_S201_stall`.

## Still owed in these parts

- **Deep verification for purchase and stock** — the arithmetic reconciliation sale reports get.
  The 476,393 cross-report agreement above is the natural first check.
- **One parser, not three** — the medical guard still runs its own copy and cannot verify anything
  because that Python has no reader at all.
- **Outbox and spool lifecycle** — nothing is ever removed; the spool doubles as the watcher's
  dedupe memory, so tidying it re-imports everything.
- **Token rotation** — three copies (systemd unit, medical PC, manojz cache). Owner action, and the
  oldest open item in the project.
- **Part 6 (health checks)** needs VPS access; **Part 8 (Lab PC)** needs the lab survey.

---
*S201 Parts 2/3/4 · no patient identifiers reproduced; no tokens read or printed.*
