# HANDOFF RUNBOOK — 12 Jul 2026 · Session 140 close · v78
*(v78 amended same day at close: +§0.6 git-commit verification; md5 in START_HERE_SESSION_141 is the canonical hash.)*

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Companion set at this close (md5 table in START_HERE_SESSION_141):** KB **v1.66** · Umbrella **v1.52** ·
Console Spec **v2.4** · Audit **v1.9** · Frontend Doc **v4** · API Quick-Ref Card (S137) ·
`WABA_Approved_Templates_v1_S137.md` · Diagnostics **v2.1** · Maintenance SOP **v1.1** — last four unchanged.
**Live files this session:** `Dashboard.html` **v18.28f** (`d528e666b258d1faf958e890e691d68a`) ·
`Callconsole.gs` **v1.7** (1,224 lines, `b1d49c6227ba16d0e7a57340a03d1a31`) · `call_hook_capture.py`
**v3.1** (894 lines, `b8a1a293c54dfb6528e04fdf31f8d3e6`) · NEW `call_pipeline_worker.py` (313 lines,
`3c8be7f0f6f5960103fb1ed586c48cce`) · NEW `call-pipeline.service` (`273c578cf5ce4b2988d62e47cd0ddeec`) ·
NEW `callhook_write_probe.py` (258 lines, `705bd4a1d82068b1ccc74a2567e2ac67`) · `call_verdict.py` **v2**
(1,102 lines, `b7dc12613ae24afee41fdc8bd6910480`) · `verdict_review.py` **v2** (1,550 lines,
`13e7618e563202b236659249fdacdeee`). Backups `.bak_s139` on the VPS.

---

## §0 — WHAT HAPPENED (Session 140, Sunday 12 Jul, FULL EOS — one Apps Script deploy, five VPS installs, ALL live-verified same day)

**§0.1 Phase 0 clean** (all 10 canonical docs md5-exact against START_HERE_SESSION_140). Owner's directive:
close **ALL** S139 call-lifecycle gaps (G-1…G-6) **today**, three passes. AKEY_14 parked again. The
staff-buzz/ntfy notification idea permanently **DROPPED (D232)** — the tracker IS the surface. The build
chat compacted twice; EOS ran in a fresh chat from `SESSION_140_NOTES_for_EOS.md`.

**§0.2 PASS 1 — K-2 incoming one-tap LIVE (G-1 CLOSED), owner-verified "all good".** Unknown connected
callers = high-value **NEW LEADS** with a 7-button set (D225; button 1 "Appointment booked", button 7
पुराने मरीज़ — नया नंबर → `inIdentity('existing_new_number')`). Lead **TTL 3 days** (D226; `enquiry_only`
NOT terminal; death by conversion / terminal outcome / expiry; escalated leads live in the escalation
queue). **One miss-counter rule, both directions (D227).** ⚡ one-tap **defaults ON** (D228; toggle removed
at >42 %×5 days). 🚨 `surgery_enquiry` = instant doctor push. Shipped: **Callconsole v1.7** —
`cc_outcomeScan_()` does ONE `Followup_Outcomes` read per bundle → `missTotals`+`kLogged`+`newLeads`
(**Block-C read-merge DONE**), `cc_patientMap_` memoised, bundle emits `newLeads` (cap 30);
**Dashboard v18.28f** — K-1 buttons on known-patient incoming tiles, 7 lead buttons for unknowns, `KIN_PAT`
on the F-10 `dref` pattern, 🌱 New-leads band, K-path→`saveKOutcome`, **L-path→frozen WebApp
`saveIncomingOutcome` (D34 respected)**. Missed incoming keep the old dropdown (F-10 verify Monday).

**§0.3 PASS 2 — VPS verdict layer v2 LIVE (G-3 + G-4 + F-18 CLOSED).** `call_verdict.py` v2 (selftest
42/42): K-era **CLAIM_EQUIV/CLAIM_PARTIAL** tables (D229); `verdict_review.py` v2 (selftest 121/121):
**D153 RETIRED (D230)** — incoming no-claim+AI → SEC_AI_ONLY, a real gap now; SUSPECT only for legacy
outgoing codes on incoming; review does NOT alias `k_coming`. **Historical catch-up: 480 judged / 0
failed** — K-equivalence proven live; incoming calls judged for the first time. **03:40 nightly cron
armed** = the guaranteed floor; the at-hangup worker is the fast path (D231). D185 read-budget satisfied.

**§0.4 PASS 3 — D200 at-hangup pipeline + G-6 probe INSTALLED, VERIFIED LIVE (G-5 + G-6 CLOSED).**
Base live==repo verified first (D188). Hook **v3.1**: one change — `pipeline_kick()` after `raw_log`,
kicks on `call.end`/`call.summary` only, wholly degrade-safe, gate/capture/upsert byte-identical to
v3.0.1; selftest 61/61. **`call_pipeline_worker.py`** under systemd (`call-pipeline.service`, enabled
--now): 15-s poller, coalesces kicks under flock, runs the three UNCHANGED --date-scoped stages, ONE
+600 s retry per fresh burst, retries never spawn retries (D234), **QUIET 01:55–04:05 IST** (D233);
selftest 14/14. **`callhook_write_probe.py`** (F-38 cure): signed synthetic `call.end` (NO PHI) through
the PUBLIC URL, FAILs on non-200 / F-38 deferred case / stale read-back; selftest 10/10, first manual run
**PASS**, cron 08:45 armed. Crontab double-append caught and deduped. **Live proof: one console call →
kick consumed → stages ran → verdict landed in minutes.** Owner at EOS: "Pass-3 install verified live."

**§0.5 The register is empty.** G-1…G-6 ALL CLOSED (G-2 was S139). F-18 closed; F-21's 106-session loop
closed by D200's implementation. **F-37 remains open** (not touched). Decisions **D225–D234**.

**§0.6 POST-CLOSE ADDENDUM — the git commit, hash-verified from the repo itself (D188).** The owner
committed all 8 S140 code files by revisiting the build chat; verified at EOS by pulling the `main`
tarball (codeload) and md5-checking every file: `call-hook/call_hook_capture.py` · `call-hook/
callhook_write_probe.py` · `recordings-archive/call_pipeline_worker.py` · `call-pipeline.service` ·
`call_verdict.py` · `verdict_review.py` · `dashboard/Dashboard.html` (stamp v18.28f · S140 confirmed) ·
`dashboard/CallConsole.gs` — **all 8 match the as-built manifest exactly, line counts included.**
**For the S140 files, repo == live.** D160 stands as the rule; today there is nothing between them.
Minor tidy noted (→ §2 B): `dashboard/` carries both `CallConsole.gs` (current) and version-named
snapshots `Callconsole_v1.6.js`/`Callconsole_v1.7.js` — identical today, but one naming convention
should be decided so a future reader knows which is canonical.

---

## §1 — MENTAL MODELS (what Session 141 must hold)

1. **Two button sets, one table, two write paths.** Known-patient incoming tiles → K buttons →
   `saveKOutcome` (Callconsole). Unknown connected incoming → 7 L buttons → the **frozen** WebApp
   `saveIncomingOutcome` (D34 untouched). Both land in `Followup_Outcomes`; the bundle's ONE
   `cc_outcomeScan_()` read derives `missTotals`, `kLogged`, AND `newLeads` from it.
2. **A lead is a row-derived state, not a tab.** Alive = a lead-ish outcome in the last 3 days, no
   conversion, no terminal code; `enquiry_only` keeps it alive. Nothing new writes anywhere.
3. **The verdict layer now understands K.** `call_verdict.py` aliases `k_coming`→`coming` and holds the
   D229 equivalence tables; `verdict_review.py` deliberately does NOT alias — that asymmetry is what makes
   SUSPECT mean "legacy code on an incoming call" and nothing else. D153 is retired; SEC_AI_ONLY is a real
   gap to read, not an excuse.
4. **Two clocks own the pipeline.** At-hangup worker = minutes-fast path (kick queue, flock, one retry);
   03:40 cron = guaranteed floor. QUIET 01:55–04:05 IST belongs to the nightly batches. Neither replaces
   the other (D231/D233/D234).
5. **The probe is the F-38 answer:** liveness green no longer implies write-success — a synthetic signed
   call traverses the whole public path daily at 08:45 and reads its own row back.
6. **Standing:** one deploy = New version on the EXISTING deployment · WebApp.gs frozen (D34) · expected
   values from the artefact (D172) · live beats repo (D160) · an audit finds (D180) · never print a
   secret (D176).

---

## §2 — OPEN BACKLOG (ordered)

**A — Ready builds (owner picks; one per session):**
- **A8 (Pass 6). Portal gist tile (D223)** — NEXT: the consolidated bird's-eye tile on `/portal`; every
  pass this session produced data it can consume without rework (leads band, verdicts both directions,
  pipeline freshness, probe status).
- **A3. D205/D213 seen-today WABA** — relay half LIVE; remaining = Docterz seen-today trigger + send loop
  (VPS scope).
- **Docterz clinical-data export migration** — build ready; blocked on ONE owner decision (follow-up
  column handling).

**B — Standing / carried:** CALLHOOK Steps 3–4 with Lokesh (**Monday**: panel update → clear PREV) ·
service-account key rotation (highest-standing risk; Lokesh) · AKEY_14 · Hindi spellings in
`vitals_page.html` (Track 1) · **F-37** health-mail stale watchman window · Notion orphans · panel-tidy
(Lokesh) · **K-1/K-2 toggle-removal watch:** one-tap usage >42 % × 5 consecutive clinic days → remove the
⚡ toggle (D228). · **Repo tidy (new, S140 post-close):** decide one convention for
`dashboard/CallConsole.gs` vs the version-named `Callconsole_vX.Y.js` snapshots (identical today).
**Watch items (Monday 13-Jul, the first live morning):** K-1 first real staff tap · F-10 incoming tap on
missed calls · first natural `IN-` row through v3.1 (**kick in journalctl**) · pipeline live proof on a
natural call (call → verdict in minutes) · write-probe first scheduled PASS ~08:45 · D212 WA tile ·
D183 digest tonight = exactly ONE · quota mail second baseline point.

**C — Explicitly parked:** AI review layer (two-phase gate, workbook with owner) · ClickUp (D17) ·
Maintenance & SOP project (owner may green-light any session; Diagnostics.gs still not live).
