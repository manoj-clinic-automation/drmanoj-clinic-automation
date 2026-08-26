# S201 — THE MARG CAPTURE PIPELINE: audit, verified state, and the rebuild in eight parts

**25-Aug-2026 · Session 201 · analysis only, nothing in this doc is built yet except Part 0.**
Three parallel audits were run: the **code as it actually is** (read line by line off manojz), the
**documentation** (every Marg doc in project knowledge), and the **health surface** (what the VPS can
and cannot see). This document is the reconciliation of the three, and the work plan that follows
from it.

**Design constraint throughout:** the same pipeline must serve the **Lab PC / Labmate ERP** next.
Every part below is specified source-agnostically — a new source must attach by adding a *profile*
and a *signature*, never by copying a script.

---

## 0 · A CORRECTION I OWE, FIRST

Earlier today I told the owner, and wrote into `medical_inventory.py`'s own docstring, that *"the
router re-files a report into its proper folder when a new signature teaches it the type, but never
corrects the index row."*

**That is false. There is no re-filing code path anywhere.** The router blacklists a file by content
md5 the instant it is indexed:

```python
# marg_router.py
219     seen[row.get("md5", "")] = row        # load_index
249     if digest in seen:
250         out("  = already indexed, skipping: %s" % ...); return None
```

`process()` returns **before** `open_sheet()`, before `identify()`, before any archiving. And
`append_index()` opens `index.csv` in `"a"` mode with no update path. So a file indexed once can
never be re-examined, whatever the registry later learns, and its row can never be corrected.

**What actually happened:** the two July purchase reports in `PURCHASE_BILLWISE/` and
`PURCHASE_SUPPLIERWISE/` are **hand-made copies placed out-of-band** when the purchase signatures
were added on 23-Aug — byte-identical duplicates, no `.txt` sidecar, mtimes matching the minute the
type folders were created rather than the `copy2`-preserved source mtimes. The originals are still
sitting in `_UNKNOWN/`.

This matters beyond the correction: the real fault is **worse** than the one I described, and it is
the single highest-value fix in this plan (Part 2).

---

## 1 · VERIFIED STATE — what is true, with evidence

### Works, confirmed
- **Capture → route → archive → Drive offsite** runs automatically and correctly for `.xls`/`.xlsx`
  arriving in `D:\MARGERP\users`. Proven live today: the 22-Aug report was captured 10:37, routed
  10:40, VERIFIED, archived, offsited.
- **Arithmetic verification is real** for sale reports — day totals, grand total, bill count,
  truncation marker, money parsed as integer paise. A day that does not reconcile is refused.
- **The health page works.** Read from the box at 11:00 today: five red rows, correct content,
  working doors. It is red for true reasons. `F-c` is **disproved** — the freshness check did not
  die into its `except`.
- **The transport leg now exists** (built today): `marg_gate.py` drains `_outbox`, gated on a real
  HTTP 200 with an affirmative body, wired into the 10-minute task, with a heartbeat.

### Broken or absent, confirmed
| # | Fault | Evidence |
|---|---|---|
| **A** | **`D:\MARG REPORTS` is watched by nothing.** The resident watcher is started with `--watch "D:\MARGERP\users"` only. | `START_MARG_WATCHER.bat` L23. The canonical `S195_Medical_Watcher_LIVE_Reference.md` states it *is* watched — **the sole reference doc is wrong on its own diagram.** |
| **B** | **A signature added never rescues an already-indexed file.** | `marg_router.py` L249-250. Live casualties: `633a54d3`, `fbea55de` (stock-expiry, would match today's registry) frozen in `_REFUSED`; `1beac275`, `df20b4d2` (July purchase) frozen as UNKNOWN. |
| **C** | **One header variant kills a whole report family, permanently.** Six real closing-stock exports refused for `['S.No.','Description','Total Stock','Unit']`. | `index.csv`; `identify()` L164-166 demands an exact prefix match. |
| **D** | **PDF/CSV are structurally invisible, and silently so.** No log line is written when a file is rejected. | `EXTS = (".xls",".xlsx")` L45 + magic gate L62; `capture()` returns `False` with no output. Five real Marg PDFs sit in `marg_reports_mirror/` today. |
| **E** | **Truncation is only checked for sale reports.** `ends_with()` returns `True` when `end_marker` is absent, and only SALE_BILLWISE/DETAIL declares one. | L136-143. A purchase export that stopped mid-print is filed `VERIFIED "structural"`. |
| **F** | **Only SALE_BILLWISE is `uploadable`.** No purchase or stock report can reach the server at all. | `signatures.json`; `marg_router.py` L314. By design — but it means "reached the archive" ≠ "reached the clinic". |
| **G** | **A multi-day range export is credited to `date_to` only.** A 01→15 Aug catch-up counts as 15-Aug; the other fourteen days read as MISSING. | `marg_gate.py` `build_picture()` — my code, my bug. Did not bite today only because 23-Aug is a Sunday. |
| **H** | **The spool doubles as the dedupe memory, and nothing is ever cleaned up.** Emptying `_spool` (which grows forever, so tidying is likely) re-captures everything. | `prime_captured()` L108-118; no delete exists anywhere except `_UPLOAD_NOW`. |
| **I** | **Routing only runs if something new was captured.** A routing run that dies leaves files in the spool that no later run will pick up. | `marg_watch.py` L201-203, `if do_route and new:`. |
| **J** | **The guard sends anyway when Python is missing.** | `GUARD_AND_SEND.bat` L72, L92-96 — jumps to `:nopython` and sends with only a printed note. |
| **K** | **The guard runs a different parser than the server** while claiming byte-identity. PC `28b47d44…` (S180) vs server `6411a57d…` (S193). | AF-5; `KB_Register_v5_45`. An `.xlsx` the server accepts is refused locally with *"file poori/theek nahi hai"*. |
| **L** | **`TOTAL_VS_MARG` has never fired once.** Reader wants `business_date`/`net_p`; writer stores `date`/`expect`/`lines_csv`/`items_csv`. | AF-2, executed against the real code. |
| **M** | **No PC-side live pins exist.** `verify_live_pins.py` runs on the VPS and cannot reach either PC. | Doc audit §6.4. This is how K's two-build parser drift went unnoticed. |

### Monitoring coverage — 4 of 7 failure modes have none
| Failure | Coverage | Latency |
|---|---|---|
| Medical watcher process dead | **NONE** | unbounded |
| manojz pull task dead | **NONE** | unbounded |
| Generated but never sent | Marg push freshness, warn 26h / bad 36h | 26–36h **+ time until someone opens the portal** |
| Sent but rejected (401/500) | Silence only — no reject counter | rejection never identified |
| Exported as PDF | **NONE** — and the alarm that eventually fires names the wrong cause | — |
| Mid-month day never generated | **NONE** while later days keep arriving | — |
| Drive offsite failing | **NONE** — the VPS cannot see Drive | unbounded |

**The structural fact:** every server-side check watches *arrival at the VPS*. It cannot see the
medical PC, manojz, the archive, or Drive. Four of seven failures are on the blind side of that line,
and no amount of server-side work will fix that — **the pipeline must report in.**

---

## 2 · THE REBUILD, IN EIGHT PARTS

Ordered by (money at risk × silence), not by convenience.

### PART 0 — Rescue what is stranded · *smallest, do first*
A `--rescan` mode for the router: re-evaluate every file in `_UNKNOWN` and `_REFUSED` against the
current registry, and **rewrite** its `index.csv` row instead of appending a contradiction. Removes
the md5 blacklist for quarantined files only — a VERIFIED file is still never re-processed.
**Recovers:** 2 purchase reports, 2 stock-expiry, 6 closing-stock. **Closes:** B, and the index/disk
disagreement.

### PART 1 — Capture everything, and never reject in silence
1. Extend accepted types to `.pdf` and `.csv`, each with its own magic check.
2. Add `D:\MARG REPORTS` to the resident watcher's watch list — and **fix the reference doc**, which
   claims it already is.
3. **A rejects log.** Every file seen and not captured gets a line: path, size, why. Silence is the
   fault, not the rejection.
4. **Print capture.** Do *not* parse `.SPL` spool files — they are printer-language, deleted after
   printing unless "keep printed documents" is on, and would be a permanent maintenance tax. Instead
   set a **virtual PDF printer** as Marg's report printer, auto-saving to a watched folder. What the
   user prints then becomes a real captured document, and (1) makes it visible.
**Closes:** A, D. **Enables:** the purchase and print pipelines the owner asked for.

### PART 2 — Identification that can learn
1. Add the missing closing-stock header variant (**C**).
2. Signature changes trigger an automatic rescan (Part 0's mode, run on `signatures.json` mtime
   change).
3. `index.csv` becomes updatable — one row per md5, rewritten on re-classification.
4. **Per-type `uploadable` targets**, so purchase reports can have a destination when the Purchase
   Portal (D335) lands, rather than a hard-coded sale-only gate (**F**).

### PART 3 — Integrity that covers every type
1. An `end_marker` for **every** signature; refuse a type that declares none (**E**).
2. Deep verification for purchase and stock, mirroring the sale reader's arithmetic.
3. Fix the range-export day credit (**G**) — a range covers *every* day in it.
4. **One parser, not three.** The guard must load the server's parser by hash, or refuse to run
   (**K**), and must never send when it cannot verify (**J**).

### PART 4 — Storage, transport, retention
1. Lifecycle for `_spool`, `_outbox`, `_UNKNOWN`, `_REFUSED` — delivered files move out of the
   outbox; the dedupe memory moves from folder contents into the index (**H**).
2. Route the spool on every run, not only when something new arrived (**I**).
3. Offsite verification — compare newest archive file against newest Drive file.
4. **Token inventory.** Three copies exist (systemd unit, medical PC, manojz). No doc lists all
   three, so a rotation from any one breaks the others. Rotation is the oldest open item in the
   project (21-Aug, "highest severity"). Document, then rotate.

### PART 5 — The manual fallback chain, as specified by the owner
The documented order when automation fails:
**manojz local path → if absent, the medical PC → if absent there, regenerate in Marg.**
1. `_UPLOAD_NOW` refreshed by the **pull**, not only by a human running status.
2. Every path written into a one-screen card the owner can follow without this chat.
3. The folder pinned to Quick Access so the portal's Choose File lands there. *(A web page cannot set
   the OS file dialog's folder — this is the honest substitute.)*

### PART 6 — Health wired to catch the maximum
Nine additions. Six ride one **heartbeat POST from `PULL_FROM_MEDICAL.bat`**, which is what makes the
blind side visible at all:
1. Pipeline heartbeat — warn > 60 min, bad > 6h *(closes: pull task dead)*
2. Outbox depth/age — warn any file > 2h, bad > 12h *(catches an unsent report at the source, not 26h later)*
3. Watcher liveness + today's capture count — bad watcher unseen > 4h *(closes: watcher dead)*
4. Ignored-file counter — files the watcher skipped *(closes: the PDF blind spot, and names the true cause)*
5. Per-day Marg coverage gap over 30 days *(closes: the mid-month hole freshness cannot see)*
6. Push rejection counter by status code *(the Diagnostics spec's own Category 5 rule, never applied to this door)*
7. Offsite lag *(closes: Drive failing)*
8. **Never-fired witness** — any check with zero lifetime firings renders `info: never fired since <date>`. This alone would have surfaced **L** on day two instead of never.
9. **Selftests for both health endpoints** — the debt named at the S195 close. Every fault in this
   subsystem lived in the gap it left.

*Severity discipline (S195 ruling): 1, 2, 3, 5, 6, 7 are `warn`/`bad` — normally silent, so eligible
for the tile. 4 and 8 are `info` unless paired with a zero-capture day, or the tile becomes
wallpaper.*

### PART 7 — Documentation rebuilt
The audit found the sole reference doc **wrong on its own diagram**, the router design and signature
schema **unreachable** (compacted out of project knowledge, and `margpull/` is outside the GitHub
sync filter), **no spec at all** for the upload contract, and the coverage map dated S147 — before
this estate existed.
1. One authoritative `MARG_PIPELINE_REFERENCE`, replacing five scattered docs.
2. The upload contract written down: request shape, auth header, response strings, status codes.
3. **PC-side live pins** — the F-97 protection class is entirely absent on the two machines this
   pipeline runs on.
4. An operational runbook: what to do when a day does not arrive.
5. Retire `S180_Marg_Feed_Transport_Design`, which still advocates a route abandoned at S195.

### PART 8 — Generalise to Lab PC / Labmate
Nothing is documented for the lab beyond one-line intentions, and `S181` gives a live reason not to
assume replication (revenue arithmetic **inverted** between medical and clinic/lab — *"the single
most dangerous copy-paste in the build"*).
1. A **source profile**: machine, share, watch folders, spool, python path, signatures, upload target.
   The medical PC becomes profile #1 by writing down what already exists.
2. Survey the lab PC before designing: Python? Tailscale? where does Labmate export, in what format?
3. Only then add signatures. Attaching a source must be a data edit, never a new script.

---

## 3 · SEQUENCING

**Today:** Part 0 (rescue the stranded files) — small, self-contained, recovers real data.
**This week:** Part 1 (capture everything) + Part 6 checks 1–3 (the heartbeat), because those two
together convert the whole blind side into something observable.
**Before the August close:** Part 4.4 (token inventory + rotation) — oldest open item in the project.
**Then:** Parts 2, 3, 5, 7 in that order. Part 8 after the lab survey.

**One rule proposed for all of it:** every part ships with the check that proves it, in the same kit.
Five of the last eight faults in this subsystem were faults in the *monitoring*, not the data path —
built without selftests, wired to nothing, or reading keys nobody writes. This plan should not add a
ninth.

---
*S201 · Read-only audit; the only thing built today is the outbox sender, its heartbeat, and this
plan. No patient identifiers reproduced; no tokens read or printed.*
