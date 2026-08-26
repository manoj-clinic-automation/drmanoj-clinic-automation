# S201 — PARKED BACKLOG

**25-Aug-2026. Everything open at the end of S201, parked in one place so nothing lives only in a
chat scroll.** Ordered within each section by (money at risk × silence).

Two references were written this session and supersede scattered predecessors:
**`MARG_PIPELINE_REFERENCE_v1.md`** (capture + transport) and
**`MARG_INGESTION_REFERENCE_v1.md`** (server-side ingestion).

---

## A · OWNER ACTIONS — nobody else can do these

| # | item | why it matters | age |
|---|---|---|---|
| **A1** | **Rotate `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`** | Both transited chat on 21-Aug. **Three copies of the Marg token exist** — the systemd unit, the medical PC, and the manojz cache; a rotation from any one breaks the others (all three listed in the pipeline reference §4). The cron token also lives in GAS "UPI Reconciliation" Script Properties. | **open since 21-Aug — the project's oldest and highest-severity item** |
| **A2** | **Run `INSTALL_AGENT.bat` on the medical PC** | Installs PDF capture. Everything else on that machine is live and reporting in. Kit is in `ToMedical`, self-verifying, with a failsafe that restores the working watcher if anything fails. | 25-Aug |
| **A3** | **Decide `ingest.min_confidence` for Marg** | Default 0.70 was tuned for **OCR**, where an unreadable scan looks like an anonymous one. A structured Marg export's only uncertainty is a missing ID. Loosening it for Marg shrinks the review queue at the cost of some wrong attributions. **A business judgement, not a code decision.** | 25-Aug |
| **A4** | **Look once at the 21-Aug report** | 16 of 37 bills fell below the confidence bar — **43%**, against ~25% on other days. Possibly a formatting cause worth knowing. | 25-Aug |
| **A5** | Sync the repo's `vps_deploy.sh` to the live one | The live `/root/deploy/vps_deploy.sh` is correct; the copy shipped in `deploy_kits/S182_C1a/deploy/` is stale (lowercase `install_*.sh` glob). A rebuild from the repo would reintroduce the old one. | 25-Aug |

---

## B · DESIGNED, NOT BUILT — kits ready to be written

All buildable now that the **offline smoke harness** is reproducible (recipe in
`S201_A1FIX_Live_Pin_Record.md`), so every kit's `+N exactly` can be **measured** before it touches
the box.

| # | kit | what it does |
|---|---|---|
| **B1** | **Health: month-vs-Marg, honestly** | Compare books against the Marg report's **own net** (now in the staged payload after S201_A1FIX) so the check *can* go green; report the review queue as a queue — *"₹X across N bills held for patient attribution"* — at **`info`, not `bad`**, so it stops driving the portal tile; and append **"and N more"** to the truncated differing-day list. |
| **B2** | **Part 6: the pipeline heartbeat checks** | The VPS cannot see the medical PC, manojz, the archive or Drive — **four of seven failure modes are invisible there**. manojz already writes a heartbeat; this adds the endpoint that receives it and the checks that read it: pull-task liveness, outbox depth/age, watcher liveness + captures today, ignored-file counter, per-day coverage gap, push-rejection counter (the Diagnostics spec's own Category 5 rule, never applied to this door), offsite lag. Plus a **never-fired witness** — any check with zero lifetime firings renders `info: never fired since <date>`, which would have surfaced AF-2 on day two. |
| **B3** | **Deep verification for purchase and stock** | Sale reports get arithmetic reconciliation; the others get structure only. Natural first check: **`PURCHASE_BILLWISE` and `PURCHASE_SUPPLIERWISE` both total ₹476,393 for July** — two independently generated reports agreeing to the rupee. |
| **B4** | **One parser, not three** | The medical guard runs `marg_report 28b47d44` (S180) while the server runs `6411a57d` (S193) — two builds apart, while both claim byte-identity. The guard should load the server's parser **by hash or refuse to run**, and must never send when it cannot verify (today it sends anyway if Python is missing). |
| **B5** | **Outbox / spool lifecycle** | Nothing is ever removed. The spool doubles as the watcher's dedupe memory, so tidying it re-imports everything — move that memory into the index. Delivered files should leave `_outbox`. `_spool` and `_outbox` are excluded from the Drive offsite, so **the pending-send queue has no offsite copy**. |
| **B6** | **Offsite verification** | Compare the newest archive file against the newest file in the Drive mirror. Closes the "Drive silently stopped" blind spot the Diagnostics spec parked as un-buildable. |

---

## C · FAULTS FOUND, NOT FIXED — for the F-register

| ref | fault |
|---|---|
| **C1** | **The month check compares incomparable things** — whole-day revenue vs attributed-only lines. Permanently red at `bad`. (Fixed by B1.) |
| **C2** | **`days_differing[:5]` truncates silently** — no "and N more", unlike the sibling line above it. 24-Aug was hidden. (Fixed by B1.) |
| **C3** | **The approvals WALK-IN warning is wrong twice** — it uses `marg_report`'s id count, which `finance_ingest` can overrule, and names WALK-IN when the destination is review. |
| **C4** | **Two parsers look for a clinic ID** (`marg_report` and `split_clinic_id`). The same class `marg_net_sql` was created to end. |
| **C5** | **The medical guard cannot run at all** — its bundled Python (3.11.9) has neither `xlrd` nor `openpyxl`. `xlsx_stdlib.py` (written this session, stdlib-only) would fix it; not yet placed on that machine. |
| **C6** | **A re-apply wipes that day's review queue** (`DELETE FROM sale_item_review WHERE ingest_batch_id=?`). Any resolution must be recorded somewhere that survives a re-import, or re-loading an old day discards it. **Matters directly to the Docterz plan.** |
| **C7** | **No PC-side live pins.** `verify_live_pins.py` runs on the VPS and cannot reach either PC — which is how C4's two-build drift went unnoticed. |
| **C8** | **AF-1 still armed on the medical sender.** `SEND_TO_CLINIC.bat` decides success from a response file curl does not overwrite on failure, then blacklists the hash. `marg_gate.py` fixed this for manojz; the medical icon path is unchanged. |
| *(retracted)* | *"`vps_deploy.sh` cannot find any installer since S196_HLT3" — **disproven live**. The live copy already carries a case-insensitive glob; I had read the stale repo copy. Recorded in `S201_A1FIX_Live_Pin_Record.md` §"A fault I reported that was NOT real".* |

---

## D · BLOCKED ON SOMETHING ELSE

| # | item | blocked on |
|---|---|---|
| **D1** | **The review queue (49 bills, ₹51,868)** | The **Docterz EMR migration to the VPS**. The queue holds exactly the matchable set — every parked bill has a name, most have a phone last-4. Match key will be `bill_date + patient_name + phone_last4`; the phone is **last-4 only** (F-86), so design for that. Follow-up tracker still runs on the owner's PC. |
| **D2** | **Lab PC / Labmate** | A survey of that machine. Nothing is documented: Python? Tailscale? where does Labmate export, in what format? And `S181` warns revenue arithmetic is **inverted** between medical and clinic/lab — *"the single most dangerous copy-paste in the build"*. **Do not assume replication.** Attach a source as a *profile + signatures*, never a copied script. |
| **D3** | Purchase Portal (D335) | Its prerequisite item-wise purchase export. Flagship, unbuilt after S199 and S200 both went elsewhere. |

---

## E · FROM THE AUDITOR, STILL UNTRIAGED

| ref | item |
|---|---|
| **AF-3** | A failed approval can leave a posted staff-ledger advance behind, and the retry posts it again. **Close-adjacent** — the August close is the first full run of this machinery. The duplicate-scan command is in `AUDIT_RUN_2026-08-24_slice1.md` §Commands 2. |
| **AF-4** | Five checker-grade routes unscoped — any medical-unit login can pull month totals, day-wise closings, drawings and patient names by URL. Neither maker page calls them, so scoping breaks nothing. |
| **AF-6** | `finance_entry.html`'s live bytes exist nowhere as a file; derivable only via a two-step recipe documented nowhere as the recovery path. |

---

## F · KB HYGIENE OWED AT THE NEXT FOLD

- **KB Register live-file table:** `/root/finance/finance_app.py` → **`d930b6b5bca59e7f52ce46f6b88332fd`**, smoke **683**.
- **Mint F-numbers** for AF-2 (born-dead check + a fixture that mirrored the reader) and for C1–C8 above.
- **`live_pins.txt`** regeneration.
- **`CANONICAL_MANIFEST.md`** rows for the S201 documents.
- **Retire `S180_Marg_Feed_Transport_Design`** — it still advocates a route abandoned at S195, and ranks the one that was built as "do not build".
- **`SYSTEM_DOC_COVERAGE_MAP_S147`** has no row for clinic-finance, Marg capture, the medical PC, manojz or the Lab PC. It predates the whole estate.
- **Correct `S195_Medical_Watcher_LIVE_Reference`** or mark it superseded by `MARG_PIPELINE_REFERENCE_v1`.
- **`ToMedical/READ ME — how this folder works.txt`** describes a relay disabled at S195; the folder now works by Drive syncing directly to the medical PC.

---
*S201 parked backlog · nothing here is in flight; each item names what it waits on.*
