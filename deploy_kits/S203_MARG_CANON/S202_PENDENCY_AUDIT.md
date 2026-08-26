# S202 — COMPLETE PENDENCY AUDIT

**25-Aug-2026, Session 202 open. A point-in-time sweep, NOT a rival live list.**

> **`OWNER_TODO_LIVE.md` remains the living truth** (step A10 of the close-out routine). This file
> is a one-time reconciliation: every backlog source read end to end, cross-matched, and the gaps
> BETWEEN them named. Where this file and `OWNER_TODO_LIVE.md` disagree, the live list wins on
> status; this file wins on completeness, because it carries items no list was carrying.

**Sources swept, each read in full, none from memory:** `OWNER_TODO_LIVE.md` ·
`HANDOFF_RUNBOOK v135 §2` · `START_HERE_SESSION_202` · `Fault_Action_Register v2.39` (all 134
indexed findings parsed by status) · `S201_PARKED_BACKLOG.md` · `CANONICAL_MANIFEST.md` (all rows) ·
`MARG_PIPELINE_REFERENCE_v1` · `MARG_INGESTION_REFERENCE_v1` · `README_VERIFY.md` ·
`SYSTEM_DOC_COVERAGE_MAP_S147` · the live repo bytes.

---

## SECTION 1 · OWNER ACTIONS — nobody else can do these

Ordered by (money or exposure at risk × how quietly it fails).

| # | item | detail | clock |
|---|---|---|---|
| **O1** | **ROTATE BOTH TOKENS** | `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`. Both transited chat 21-Aug. **THREE copies of the Marg token exist** — the systemd unit, `D:\SendToClinic\token.txt` on the medical PC, and the manojz cache. Rotating one breaks the others. The cron token also lives in GAS "UPI Reconciliation" Script Properties. **Never hand-copy between machines** — a hand-copy went stale and answered 401 for five days. All three listed in `MARG_PIPELINE_REFERENCE_v1` §4. | **oldest + highest severity in the project — open since 21-Aug** |
| **O2** | **Copy the pin list on the VPS** | `cp /root/deploy/repo/deploy_kits/KB_canon_all/live_pins_S202open.txt /root/deploy/live_pins.txt` then run the checker. **Path changed at this open** — see §6 N12. | now |
| **O3** | **Darpan's ₹20,000 SPECIAL** `0cc0b26b38c5` | Scan + upload the signed application → approve → enter 17-Aug ₹20,000 in the Staff Ledger (re-verify the S198 drawer figure at entry). | **before the August close** |
| **O4** | **Pravesh exits 31-Aug** | Check his advance position now; full & final at exit. | **31-Aug, hard** |
| **O5** | **July cash top-ups ₹4,519** | Shavez 1068 · Sandip 797 · Awdhesh 707 · Alisha 666 · Pravesh 569 · Ranjeet 449 · Vikki 170 · Sukhveer 93 (CASH SETTLEMENT tab). | before the close |
| **O6** | **Surendra held** | Verify the ₹516 advance gap from papers → settle his ₹855. | before the close |
| **O7** | **Arjun** | Give his July actual-paid figure → his top-up. | before the close |
| **O8** | **Shivani (August)** | Recover ₹3,724.55 + handle the parked ₹3,000 advance. | before the close |
| **O9** | **AF-3 duplicate-advance scan** | A failed approval can leave a posted ledger advance behind and the retry posts it again. Command in `AUDIT_RUN_2026-08-24_slice1.md` §Commands 2. | **before the August close** |
| **O10** | **UPI / bank** | The correction-checklist day + the 4 disagreement days. | before the close |
| **O11** | **Verify R9 on the box** | `/ledger/advances` shows ONE expandable card per staff. Delivered S200, box-GREEN never confirmed. | now |
| **O12** | **F-173 — the April-2025 NEFT advice file** | Its account-number column is SHIFTED against its names; **payments that month may have gone to wrong accounts.** Check that month's bank statement. **This is the only open item on the list where money may already have left for the wrong party.** | open since S198 |
| **O13** | **Publish** | Today's housekeeping is committed to your local repo only. `PUBLISH_ALL.bat` (D328 — repo-write credentials never transit chat). | now |

## SECTION 1a · Marg tidy — nothing deletes, do when convenient

| # | item |
|---|---|
| **O14** | `D:\Downloads\margsync\MargPull\CLEANUP_DRIVE.bat` (on manojz) |
| **O15** | `F:\My Drive\Clinic Data Archive\ToMedical\CLEANUP_MEDICAL.bat` (on the medical PC) |
| **O16** | Review and empty `D:\Downloads\margsync\_to_delete\` — 7.6 MB parked |
| **O17** | Sync the repo's stale `deploy_kits/S182_C1a/deploy/vps_deploy.sh` to the live one. *(The LIVE `/root/deploy/vps_deploy.sh` is fine — the S201 "broken" report was read off the stale repo copy and retracted.)* |

## SECTION 1b · Staff communication & phones

| # | item |
|---|---|
| **O18** | Upload `Salary_New_System_July_Comparison.pdf` to portal Forms; show it beside the old Google sheet; get staff acceptance of the INTEREST terms |
| **O19** | Staff phones: `followup.dr-manoj.in/portal` → sign in → Add to Home screen |
| **O20** | Forms tile: upload the clinic forms (PDF prints best) |

## SECTION 1c · Accountant / data pipeline

| # | item |
|---|---|
| **O21** | Club-4: the accountants' emails · the Tally export source + due day |
| **O22** | Club-3 samples still owed into margsync: **purchase-register · Labmate · Docterz** (purchase, supplier-wise, stock and PDF reports are ✓ done) |

---

## SECTION 2 · BUILDER QUEUE — what Claude builds next

**You prioritised the first two for S202.**

| # | item | note |
|---|---|---|
| **B2** | **Pipeline heartbeat checks — FIRST** | `/ops`'s honest prerequisite. The VPS cannot see medical, manojz, the archive or Drive; **four of seven failure modes are invisible there.** Cheap version: manojz posts a small status JSON at the end of each 10-minute pull. Full version adds pull-task liveness, outbox depth/age, watcher liveness + captures today, ignored-file counter, per-day coverage gap, push-rejection counter, offsite lag, and a **never-fired witness** (any check with zero lifetime firings renders `info: never fired since <date>` — which would have surfaced AF-2 on day two). |
| **OPS** | **`/ops` — the runbook surface** | Symptom-indexed, owner-only, each fault a dropdown decision tree, linked as a **second door** from every `/finance/health` row (a `HEALTH_RUNBOOK` map parallel to `HEALTH_LINKS`). **Two rulings already made and binding:** served from the repo, **never uploaded**; and **a runbook page never states a hash, version, count or path inline — it reads them live** (D202). First content = `MARG_PIPELINE_MAINTENANCE_FLOW_v1`. |
| **F-183** | The two latent attribution faults, in their own kit | (a) the `0.60` tier parks a bill that HAS a clinic ID but no name — backwards, the ID is the strongest identifier; (b) single-digit clinic IDs are not recognised (the pattern needs 2+ digits, your numbering started at 1). Neither occurs in the 192 bills measured. |
| **IDCAP** | Identifier capture as a daily figure on the health page | 73% this week; 57%–92% by day. Visible today only if someone goes looking. Every missed clinic ID is a Docterz match that would not have been needed. |
| **B3** | Deep verification for purchase and stock | Sale reports get arithmetic reconciliation; the others get structure only. Natural first check: `PURCHASE_BILLWISE` and `PURCHASE_SUPPLIERWISE` both total ₹476,393 for July. |
| **B4** | One parser, not three | The medical guard runs `marg_report 28b47d44` (S180); the server runs `6411a57d` (S193) — two builds apart while both claim byte-identity. The guard should load the server's parser **by hash or refuse to run**, and must never send when it cannot verify (today it sends anyway if Python is missing). |
| **B5** | Outbox / spool lifecycle | Nothing is ever removed. The spool doubles as the watcher's dedupe memory, so tidying it re-imports everything — move that memory into the index. Delivered files should leave `_outbox`. **`_spool` and `_outbox` are excluded from the Drive offsite, so the pending-send queue has no offsite copy.** |
| **B6** | Offsite verification | Compare the newest archive file against the newest file in the Drive mirror. Closes the "Drive silently stopped" blind spot the Diagnostics spec parked as un-buildable. |
| **B7** | A local `MEDICAL_RECENT` that runs ON the medical PC | The current one scans the D: share and therefore cannot see Marg's second output tree on `C:\Users\Public\MARG\`. |
| **LED** | Ledger kit (ordered) | cover/OT AUTO-DETECT queue · retire/link the old `/ledger/settings` · cover-duty rate from settings |
| **F-178** | Mid-duty punch-gap surfacing | Every punch is kept; the day computation uses only `first` and `last`, so 09:00-in / 11:00-out / 15:00-in / 18:00-out reads as a punctual full day, and **no screen renders the sequence**, so it cannot be noticed. Honest limit: only punches that happen can be seen — the walk-out without punching is what the selfie-GPS punch would close. |
| **SC0** | **Staff Console Phase 0** | Blocked on **your four rulings**: leaver hold+pot · probation numbers · task-media retention · managers-create-tasks Y/N. D349 candidate. |
| **KAAM** | काम task board (voice-first) → money views → requests → selfie-GPS punch | |
| **PWA** | PWA holdouts: the bare Attendance tile + the Assets domain | |
| **D335** | **Purchase Portal — the other flagship** | Signed at S198; **unbuilt after S199 and S200 both went elsewhere.** The 14-state workflow table IS the spec. Blocked on its item-wise purchase export prerequisite. |

---

## SECTION 3 · THE AUGUST CLOSE — the first fully live, ENFORCED run

**Watch, don't assume.** Pravesh's exit · Darpan's SPECIAL + ₹3.55L schedules · three auto-recoveries
· Shivani's two items · the first suspended-charge cancel/collect cycle · AF-3's duplicate-advance
scan run beforehand.

---

## SECTION 4 · BLOCKED, NOT FORGOTTEN

| # | item | blocked on |
|---|---|---|
| **X1** | **The no-clinic-ID sale bills — 49 bills, ₹51,868 this month** | The **Docterz EMR migration to the VPS**. The parked list already holds exactly the matchable set (every parked bill has a name; most have a phone last-4). Match key will be `bill_date + patient_name + phone_last4` — **the phone is last-4 ONLY (F-86), so design for that.** And **a re-apply wipes that day's parked list**, so resolutions need somewhere that survives a re-import. |
| **X2** | **Lab PC / Labmate** | A survey of that machine — Python? Tailscale? where does Labmate export, in what format? **S181 warns the revenue arithmetic is INVERTED between medical and clinic/lab** — *"the single most dangerous copy-paste in the build"*. Attach a source as a *profile + signatures*, never a copied script. **And ask where Labmate writes** — Marg turned out to have two output trees on two drives. |
| **X3** | **AF-1 still armed on the medical sender** | `SEND_TO_CLINIC.bat` can report ACCEPTED for a report that never left, then blacklist its hash. **Kept deliberately** as the only medical-side fallback; `marg_gate.py` on manojz is the safe path. |

---

## SECTION 5 · OPEN FINDINGS IN THE FAULT REGISTER (19, parsed by status from v2.39)

| F-# | since | one line |
|---|---|---|
| **F-81** | S171 | Duplicate call rows in the live log — same phone/time/duration twice |
| **F-82** | S172 | **VENDOR** — MyOperator WhatsApp Developer API returns HTTP 500 on ALL authenticated calls |
| **F-83** | S176 | *(mitigated)* Asset-app intake OCR thread is fire-and-forget — dies on restart, skips non-draft bills |
| **F-91** | S181 | *(behavioural)* **UPI recorded as Cash at Docterz entry — ₹17,900 over six weeks.** Invisible to any ledger-internal check |
| **F-92** | S181 | **Discount capture stopped 18 Jun 2026** — ₹1,33,720 up to that date, then zero, while concessions continue |
| **F-93** | S181 | The concession parser swallows the Docterz footer, manufacturing three fake "patients" a day in the staff-facing sheet |
| **F-99** | S182 | A missing-day alarm anchored on `MIN(business_date)` cannot see a unit that never filed a first day |
| **F-103** | S183 | *(structural)* UPI reconciles against ICICI; **there is NO cash-deposit reconciliation against Yes Bank** |
| **F-104** | S183 | *(owner chose the fix)* The S183 backfill fed identity-less legacy bills through attribution |
| **F-107** | S185 | *(structural)* **Phase 0 is blind to a document that was never listed.** The inverse check exists as a habit, not a step |
| **F-108** | S185 | *(structural)* Findings in the Register's index were never applied to the Fault Register — see §6 N1, it just recurred |
| **F-130** | S188 | A page-only kit preserving every id is invisible to an id-based test — fix specified, 3 lines per page |
| **F-133** | S188 | The cash-custody feature exists since S179 and has never once been used — **code is not what is broken** |
| **F-136** | S189 | The manifest keeps its own copy of a value it says the Register owns, and nothing checks the copy |
| **F-146** | S190 | A refusal that looks like a save — rule adopted, **no code fix specified yet** |
| **F-168** | S195 | Every "push to medical" feature assumed a write the OS forbids; owner path chosen (Drive-for-Desktop) |
| **F-173** | S198 | **The April-2025 NEFT advice file's account column is SHIFTED — owner review owed** *(= O12)* |
| **F-178** | S200 | The mid-duty punch blindsight — build queued |
| **F-183** | S201 | Two latent clinic-ID attribution faults — OPEN by choice, own kit queued |

**Plus 29 findings carrying NO status marker at all** (F-51…F-76 era, F-87, F-89, F-97). Most read as
absorbed lessons, but **nothing in the register says so** — they are neither OPEN nor CLOSED. Some are
live operational hazards, e.g. **F-75** (`portal_console.py --build` is window-scoped and
atomic-from-scratch; a small `--days` scheduled run silently destroys the wide-window layers every
fire). **A status pass over those 29 is owed.**

---

## SECTION 6 · WHAT THIS SWEEP FOUND THAT NO LIST WAS CARRYING

These are the reconciliation results — items that existed in one document and in no backlog.

| # | gap | evidence |
|---|---|---|
| **N1** | **Six faults documented at S201 were never minted into the Fault Register.** `S201_PARKED_BACKLOG.md` §F says *"Mint F-numbers for AF-2 and for C1–C8"*. The close minted F-179…F-183, which cover different things. **C3** (the approvals WALK-IN warning is wrong twice), **C4** (two parsers look for a clinic ID), **C5** (the medical guard cannot run at all — its bundled Python has no spreadsheet reader), **C6** (a re-apply wipes that day's review queue — **matters directly to the Docterz plan**), **C7** (no PC-side live pins), **C8** (AF-1 armed on the medical sender) have **no register entry**. C1/C2 were fixed by `S201_HEALTH`. **This is F-108's exact shape, recurring.** | grep of v2.39 returns 0 for each |
| **N2** | **The AF-# series has no bridge to the F-# register.** `AF-1`, `AF-2`, `AF-3`, `AF-4`, `AF-6` appear **zero times** in the Fault Register. Two parallel finding systems, no reconciliation step, and **AF-5 is unaccounted for in any document I can reach.** | grep of v2.39 returns 0 for all five |
| **N3** | **Two canonical rows contradict each other.** `MARG_PIPELINE_REFERENCE_v1` opens *"Supersedes `S195_Medical_Watcher_LIVE_Reference.md`"*; the manifest still labels that row **"SOLE reference for the Marg capture pipeline"**. Both are Tier-1 CURRENT. One must be relabelled. | manifest rows, read side by side |
| **N4** | **`MARG_INGESTION_REFERENCE_v1` §9 item 5 contradicts D348.** It calls `ingest.min_confidence` *"an owner decision, not a code one"*; **D348, minted hours later the same session, retires exactly that** — closed by measurement, 192 bills, every one 0.95+ or 0.50. Filed as delivered rather than silently edited (F-23); **your ruling owed.** | both read in full |
| **N5** | **`S201_PARKED_BACKLOG.md` items A3 and A4 are stale.** A3 is the same retired min_confidence question; A4 (look at the 21-Aug report) was answered in-session — 57% capture, **staff behaviour, not a formatting fault**. The doc needs a status pass or it will keep re-raising closed questions. | vs the S201 close record |
| **N6** | **`SYSTEM_DOC_COVERAGE_MAP_S147` has NO row for clinic-finance, Marg capture, the medical PC, manojz or the Lab PC.** It predates the entire estate. The manifest's own footnote already admits a clinic-finance row is owed. **The document whose job is "where is the reference for tool X" cannot answer for the systems you use daily.** | 23 rows, zero matches on finance/marg/medical |
| **N7** | **`S180_Marg_Feed_Transport_Design` still advocates a route abandoned at S195** and ranks the one that was actually built as "do not build". Retire it. | S201 §F, still owed |
| **N8** | **`ToMedical/READ ME — how this folder works.txt`** describes a manojz relay disabled at S195. The folder works today for a different reason (Drive syncs directly to medical). | pipeline reference §2 |
| **N9** | **`END_OF_SESSION_PROMPT` v8 / step A8b is owed at this close** — a numbered step that executes `README_VERIFY`'s inverse check and refuses the close on a mismatch. Without it, F-184 recurs. | F-184, this open |
| **N10** | **The cold kit is DUE** — 4 of 3–5 since S197. Take it at the S202 close. **This is the cadence whose lapse permanently lost three canonical documents (F-89).** | manifest |
| **N11** | **`gen_live_pins.py` header says v1.1; the manifest pins it as v1.2.** A file's own claim about itself disagreeing with the register — small, but it is the F-45 family and D188's own subject. | file header vs manifest row |
| **N12** | **The pin-list path changed at this open.** `OWNER_TODO_LIVE.md` item 1 still points at `KB_canon_S201close/live_pins_S201close.txt`. The correct source is now **`KB_canon_all/live_pins_S202open.txt`** — and `KB_canon_all` is the ONLY folder the checker can prove a source from (F-184). | this open |
| **N13** | **The later Daily Flow v2 stages have no status anywhere.** D326's signed contract lists D-R returns · the D327 `counter` role · 360 wiring · orthotics purchase side · **D5** feeds · **D6**. D1 (S187) and D2 (S188) are live; **nothing since S189 records what happened to the rest.** Neither open nor closed. | contract vs every close doc after S189 |

---

## SECTION 7 · WHAT WAS CLOSED AT THIS OPEN (S202 housekeeping)

- **F-184 appended and repaired** — three instances, one root. Twelve absent canonical documents filed
  into `KB_canon_all`, `MD5SUMS_ALL.txt` and `KIT_ID.txt` regenerated last. The folder's own
  verification command now exits 0 with 201 rows OK and the inverse check clean.
- **The S201 F-107 condition CLOSED** — `MARG_PIPELINE_REFERENCE_v1` (`d34d0616…`),
  `MARG_INGESTION_REFERENCE_v1` (`4d603b72…`), `S201_UI_Health_Redesign_Record` (`800e51ad…`) filed
  and pinned with real hashes.
- **Fault Register v2.38 → v2.39** and **KB Register v5.46 → v5.47**, both reverse-application-proven.
- **Two stale clauses on the Register's §How-to-use line corrected visibly** (it pointed at
  `END_OF_SESSION_PROMPT` **v5** while v7 is current, and trailed *"next free F-170"*).
- **No live code moved · no live data changed · no pin moved.** Next free **D349 · F-185 · A-D25**.

---
*S202 pendency audit · every item traced to the document that states it · nothing carried from memory.*
