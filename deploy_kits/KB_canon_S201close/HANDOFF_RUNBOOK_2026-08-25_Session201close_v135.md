# HANDOFF RUNBOOK — v135 (Session 201 · THE MARG PIPELINE MADE WHOLE · 25 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 201 — FULL build EOS)

Opened on one missing report — *"i made a marg sale report this morning… it is not in
`/finance/approvals#margCard` yet, and i cant find it in my local margsync folder too"* — and closed
every hole in the chain that carries Sanjeevni's pharmacy revenue.

1. **F-179, the root cause: a queue with no consumer.** `marg_router.py` stamped every verified
   report *"queued for upload"* into `MargArchive\_outbox`. **Nothing read `_outbox`.** The only
   uploader was a manual double-click on the medical PC, last pressed 22-Aug. **Eleven verified
   reports** (2 purchase · 6 closing stock · 2 expiry · 1 scrap) sat correct, hashed and undelivered
   while capture, routing and archiving all reported success. Closed by `marg_gate.py` on manojz,
   driven by the existing 10-minute pull.
2. **Three kits live, three projections written before measurement, three landing exactly:**
   `S201_A1FIX` (680→**683**) closing **AF-2**, dead since S195 because `days_payload` never carried
   `business_date` · `S201_HEALTH` (683→**690**) making the month row comparable and naming the
   parked bills · `S201_UI` (690→**693**). Final pin `finance_app.py` **`3f72e9ad16d915fe5ced45c4e28a2248`**.
3. **D347 — the medical-PC pipeline architecture.** Drive for Desktop is the bidirectional channel;
   Tailscale is a read-only **D:-only** view and NOT load-bearing (it cannot see Marg's second output
   tree on `C:\Users\Public\MARG\`, which is exactly where the blind spot was); the agent supervises
   the watcher and auto-applies kit files but **never updates itself — it reports its own drift**
   (F-180). The manual sender stays as the fallback and is never removed.
4. **D348 — the owner's own naming.** These are **sale bills where the salesman did not enter a
   clinic ID at the till**. They count in sales IN FULL and are parked for the Docterz cross-match.
   ***Variance* and *low confidence* are retired.** `ingest.min_confidence` (0.70) is **closed by
   measurement, not by owner judgement**: across 192 bills / seven days every bill scores 0.95+ or
   0.50 and nothing between — it is a has-ID switch imported from OCR into a path with no OCR.
5. **Identifier capture measured: 73% of bills; ₹54,547 (28.3% of turnover) unidentified.**
   21-Aug 57% against 92% on 22-Aug — **staff behaviour, not a formatting fault.**
6. **F-181** nested `<a>` broke a health row while both counting tests passed — found in the owner's
   own saved copy of the SERVED bytes. **F-182** `/finance/health` was in no design register at all.
   **F-183 OPEN by choice** (the backwards `0.60` tier + single-digit clinic IDs, left for their own
   kit). Agent **S201.1 → S201.11**; the `.xlsx` dependency **deleted** rather than managed; the
   10-minute popup fixed with no GUI step by the owner; 7.6 MB parked, nothing deleted; census 78
   report-shaped files on the medical PC, **0 not in the archive**. No incident.

**Recorded, not softened — three assistant faults this session:** the server does NOT deduplicate
marg-push by content (asserted from expectation, a second 24-Aug copy staged) · `vps_deploy.sh` was
reported broken for six kits **from the stale repo copy — D188 broken while quoting D188**, retracted
in the record · installer v2 printed "UPDATED" without verifying, **AF-1's exact shape**, criticised
by the assistant that same morning.

---

## §1 — MENTAL MODELS (added this session)

- **A queue with no consumer is not a queue, it is a hole.** Eleven correct reports sat in one for
  three days and every component reported success. Assert the DRAIN, not the enqueue.
- **A dependency you cannot maintain on the machine that needs it is a scheduled outage** — delete
  it rather than install it (`xlsx_stdlib.py` replaced `openpyxl` on the medical PC).
- **Reading what the server SENT is a distinct check from reading what builds it.** Twice in one
  session the owner's own saved HTML caught what the source side could not.
- **When a count is right but the shape is wrong, no counting test will ever see it** — assert
  something the change did not preserve.
- **A component that must not self-update must self-report.** Safety and visibility are different
  problems and deserve different answers.
- **A threshold imported from another problem domain measures nothing here** — measure the
  distribution before tuning the knob.
- **A number that is never zero tells you nothing on the day it should have been three.**
- **The owner's own words are the better label.** *Variance* and *low confidence* were both ours and
  both wrong.
- **Mixing a behaviour change into a labelling fix makes a rollback hard to reason about.**
- **A register that only checks what it lists must be asked, separately, what it does NOT list**
  (F-182 — F-107's shape, one register over).

---

## §2 — THE LIVE BACKLOG

> **The maintained copy is `OWNER_TODO_LIVE.md` (project knowledge, un-manifested by design — it
> edits as we work, and is refreshed at EVERY close as step A10). The list below is the close-time
> snapshot.**

**⭐0 — owner actions (before the August close):**

- **TOKEN ROTATION** (`FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`) — aging since 21-Aug, highest
  severity. **THREE copies of the Marg token exist** (the systemd unit · the medical PC ·
  the manojz cache) — all listed in `MARG_PIPELINE_REFERENCE_v1.md` §4. **Never hand-copy between
  machines**: a hand-copy went stale and answered 401 for five days.
- **Darpan's ₹20,000 SPECIAL** `0cc0b26b38c5` · **Pravesh exits 31-Aug** · **July cash top-ups
  ₹4,519** · **Surendra ₹516** · **Arjun's actual-paid figure** · **Shivani's two August items**.
- The correction-checklist day + 4 UPI/bank days · auditor triage (AF-3 before the close).
- Staff comms: comparison PDF → Forms · INTEREST-terms acceptance · staff-phone PWA installs.
- **Copy `live_pins_S201close.txt` → `/root/deploy/live_pins.txt`** and run the checker.

**⭐0a — Marg pipeline (S201):** agent S201.11 installed ✓ · the tidy scripts when convenient
(`CLEANUP_DRIVE.bat` on manojz · `CLEANUP_MEDICAL.bat` on the medical PC · empty
`D:\Downloads\margsync\_to_delete\`) · sync the stale repo `vps_deploy.sh` to the live one.

**⭐1 — builder queue:**

1. **B2 — pipeline heartbeat checks** *(and it is the prerequisite for `/ops`, below)*. The VPS
   cannot see medical, manojz, the archive or Drive; four of seven failure modes are invisible there.
   Cheap version: manojz posts a small status JSON at the end of each 10-minute pull.
2. **`/ops` — the runbook surface** (ideated S201, **parked for priority next session**):
   symptom-indexed, owner-only, each fault a dropdown decision tree, **served from the repo, never
   uploaded**, linked as a **second door** from every `/finance/health` row (a `HEALTH_RUNBOOK` map
   parallel to `HEALTH_LINKS`). **Rule: a runbook page never states a hash, version, count or path
   inline; it reads them live** — otherwise it is a delta doc, which D202 forbids.
3. **F-183** — the backwards `0.60` tier + single-digit clinic IDs, in their own kit.
4. **Identifier capture on the health page** — 73% this week, 57%–92% by day; today it is visible
   only when someone goes looking, and every missed ID is a Docterz match that was not needed.
5. B3 deep verification (purchase/stock) · B4 one parser not three · B5 outbox/spool lifecycle ·
   B6 offsite verification · B7 a local `MEDICAL_RECENT` that runs ON the medical PC (the current
   one scans the D: share and therefore cannot see Marg's C: tree).
6. Ledger kit (cover/OT auto-detect · retire old `/ledger/settings` · cover-duty rate from settings)
   · **F-178** punch-sequence surfacing · Staff Console Phase 0 (D347-candidate rulings owed) ·
   काम task board · PWA holdouts · **Purchase Portal (D335)** stands as the other flagship.
   · Verify R9 on the box (grouped Advances page).

**⭐2 — THE AUGUST CLOSE = the first fully LIVE, ENFORCED run.** A leaver (Pravesh) · Darpan's
SPECIAL + ₹3.55L schedules · three auto-recoveries · Shivani's two items · the first suspended-charge
cancel/collect cycle · **AF-3's duplicate-advance scan**. Watch, don't assume.

**⭐3 — blocked, not forgotten:** the no-clinic-ID bills (49, ₹51,868) → the **Docterz migration**
(match key `bill_date + patient_name + phone_last4`, **last-4 only**, F-86; and **a re-apply wipes
that day's parked list**, so resolutions need somewhere that survives a re-import) · Lab PC /
Labmate (survey first; S181 warns the revenue arithmetic is INVERTED between medical and clinic/lab;
**and ask where Labmate writes — Marg had two output trees on two drives**) · **AF-1 still armed on
the medical sender**, kept deliberately as the only medical-side fallback.

---

## §3 — INSTALL DISCIPLINE (updated)

The standing chain holds (hash-verified bases · offline pre-flight · currency gates · projections
before measuring · `bash -n` installers · probes print never judge · hashes transcribed never typed ·
route-200 selftests on whole-function Flask edits · data migrations with counts+backup · the
followup vhost is APPEND-MANAGED · selftests that touch a live store snapshot-and-restore · kits
carry code only · one full copy-paste block per VPS command · publish BEFORE pull).

**Added at S201:**

- **Verify against the LIVE file, never the repo copy.** The repo's `deploy/` mirror is stale by
  design; a finding read off it is not a finding (D188 — and it was broken this session while being
  quoted).
- **An installer prints what it VERIFIED, never what it attempted.** `move` can fail with Access
  Denied under a running process and still leave a success message on screen (AF-1's shape).
- **Stop everything BEFORE touching files on Windows**, clear the read-only attribute, then
  hash-compare.
- **A supervisor never overwrites its own running file** — it reports drift by md5 instead.
- **Deliver one double-click `.bat`, never a long console paste.** A large PowerShell paste was
  reordered by the console this session and left it in continuation mode; the owner's standing
  instruction is that GUI-step sequences are too cumbersome to be a delivery method.
- **Always give the COMPLETE path, and say which machine it is on.**

---

## §4 — THE EOS AUTOMATION BOUNDARY (held)

The assistant executed the builds and the full close (Archive/Register/Fault appends with mechanical
proofs, manifest, A8 pin list, A9 Notion, **A10 the owner to-do**, project swaps). **Owner residual:
one `PUBLISH_ALL.bat`, then on the box copy `live_pins_S201close.txt` → `/root/deploy/live_pins.txt`
and run `verify_live_pins.py`.**

---

*HANDOFF_RUNBOOK v135 · Session 201 close · supersedes v134. If §0, §2 or this end-marker is absent,
this file is truncated and must not be used as canonical.*
