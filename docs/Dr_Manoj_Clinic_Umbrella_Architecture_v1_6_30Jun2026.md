# Dr. Manoj Agarwal Clinic — Umbrella Architecture
**Advanced Orthopaedic Surgery Centre, Bareilly**
Version 1.6 · 30 June 2026 (Session 19) · Owner: Dr. Manoj Agarwal · Maintained with: Claude (per session)

> **What this document is.** The single reference for the whole clinic-automation system — the shape, the rules, the modules, the policies, and the rollout order. Everything we build hangs off this. When in doubt, this document wins. It is a *living* document: update it as decisions evolve, and keep one copy in **Notion (“Clinic HQ”)** and one in the **handoff kit**.
>
> **Who it is for.** Dr. Manoj (owner), Shavez (operations), and whichever AI/engineer continues the build.

---

## 1. Vision in one paragraph

Unify every clinic system — IVR calls, WhatsApp, the EMR’s nightly data, pharmacy and lab revenue, recordings, and staff workflows — into **one coherent operations hub** for an orthopaedic practice serving an older, Hindi-first, semi-urban base. The hub does three things at once: **cares** (timely, clinically-honest follow-up and safety nudges), **holds accountable** (verified call outcomes, evidence on demand), and **learns** (dropout, channel, and demographic patterns that refine outreach over time). The relationship — thirty years of trust — is the real asset; the technology exists only to protect and scale that, never to replace it.

---

## 2. Core principles (the spine — do not violate)

1. **Modules talk through DATA, not through each other.** A module never calls another module directly; it reads and writes the shared data layer. This is what guarantees isolation: if one module snags, only that module snags — the others keep working on the last good data.
2. **One universal join key: the Clinic ID.** Docterz, Sanjeevni, Labmate, the document index, revenue — every source must carry **Clinic ID + name**. A source that cannot carry the Clinic ID cannot join the system. This single discipline is what lets calls, visits, pharmacy, lab, documents, and revenue all resolve to one patient.
3. **One writer per table.** Each data table has exactly one module that writes it. (The tracker owns the worklist; the dashboard owns outcomes; each ingester owns its own feed.) No two modules write the same cells. This eliminates the silent race conditions that corrupt shared systems.
4. **Every module degrades to a fallback, never a crash.** A missing tab → an empty section, not an error. A skipped nightly run → yesterday’s list, not a blank screen. The manual workflow always remains as the ultimate fallback.
5. **Tiered verification — cheap signal everywhere, expensive proof only where contested.** Free metadata (did the call connect, how long) flags suspicion automatically; paid transcription (Sarvam) is spent only on flagged or disputed calls.
6. **Secrets and PHI never enter Git or Notion.** Code goes to Git; knowledge goes to Notion; secrets live only on the VPS `.env` (and Apple Notes); patient data lives only in the Sheet/Drive/local device with access control.
7. **Care-first ethics.** Every automated patient touch must read as *the clinic caring*, never as a call centre or marketing. Clinical nudges stay strictly clinical and within the orthopaedic lane.
8. **Ship one lane at a time.** Because modules are independent and share a spine, the system can grow in any order with no big-bang. The architecture *is* the rollout-safety mechanism. Finish and stabilise one lane before opening the next.

---

## 3. The shape: hub-and-spoke (data is the hub)

```
                 ┌─────────────────────────────────────────┐
                 │            DATA BANKS  (the hub)          │
                 │  Google Sheet      — live operational     │
                 │  Local mini-PC     — PHI master + docs    │
                 │  Google Drive      — recordings + backups │
                 │  Git               — code only            │
                 │  Notion            — human knowledge      │
                 │  NotebookLM        — reasoning over corpus │
                 └─────────────────────────────────────────┘
            ▲      ▲       ▲       ▲       ▲       ▲       ▲
   ┌────────┘  ┌───┘   ┌───┘   ┌───┘   ┌───┘   ┌───┘   └────────┐
┌──┴───┐  ┌────┴───┐ ┌─┴────┐ ┌┴─────┐ ┌┴──────┐ ┌┴────────┐ ┌──┴─────┐
│Brain │  │ Call   │ │ WABA │ │Evid. │ │ 360°  │ │Document │ │Revenue │
│tracker│ │console │ │ send │ │Sarvam│ │ query │ │  repo   │ │  MIS   │
└──────┘  └────────┘ └──────┘ └──────┘ └───────┘ └─────────┘ └────────┘
     + HR lane (attendance/salary)      + Supervisor (doctor.py watches all)
```

Each spoke only reads/writes the hub. The **dashboard** is the single human **cockpit** that surfaces the operational spokes; the **VPS** is the **engine room** that runs the always-on services; the **tracker** is the **brain** that decides who to contact and why.

---

## 4. Data bank charter (each bank has one job)

| Bank | Holds | Must **never** hold |
|---|---|---|
| **Google Sheet** (Clinic Callback Tracker) | Live operational state: worklists, outcomes, statuses, rosters | Bulk PHI, secrets, large history |
| **Local mini-PC** | PHI master, the brain (tracker), the document repository (lab/X-ray/MRI) | Anything without a verified backup |
| **Google Drive** (clinic account) | Call recordings (auto from MyOperator), exported reports, document backups | Code, secrets |
| **Git** (`drmanoj-clinic-automation`) | Code only | Secrets, PHI, service-account keys, patient data |
| **Notion** (“Clinic HQ”) | Human knowledge: this doc, runbooks, decisions, SOPs, the maintenance manual | Live patient data, secrets |
| **NotebookLM** (planned) | A reasoning surface over the Notion/runbook corpus + de-identified insights | Identifiable PHI |

**Backups (non-negotiable):** the local mini-PC holds irreplaceable records, so it follows **3-2-1** — the local copy, plus an encrypted offsite/cloud copy, with at least one copy off-site. A single device is a single point of failure.

---

## 5. The three feedback loops + the truth model

**Three layers of truth about any follow-up call** (ascending cost):
1. **Claimed truth** — what the agent marked. Free, self-reported, fallible.
2. **Metadata truth** — the call log (connected? how long?). Already polled, effectively free.
3. **Content truth** — the Sarvam transcript (what was actually said). Expensive — used sparingly.

**The three loops that run on this:**
- **Outcome loop:** ledger → contact (call/WhatsApp) → outcome → back to ledger → tomorrow’s worklist + dropout detection.
- **Verification loop:** a metadata-flagged or disputed outcome → on-demand transcript → verdict (Confirmed / Corrected) → corrects the ledger + creates an accountability record. *This is the dispute-settler.*
- **Insight loop:** de-identified transcripts → intent clusters → better templates, IVR routing, and call scripts; dropout/channel/demographic patterns → cadence tuning.

---

## 6. Modules (spokes) — inventory

Status key: **LIVE** (running) · **BUILT** (coded/tested, not wired) · **PLANNED** (agreed, not built).

| Module | Status | Job | Reads | Writes | If it fails |
|---|---|---|---|---|---|
| **Brain — Follow-Up Tracker** | LIVE (clinic PC) | Nightly: Docterz CSVs → ledger (Due/Grace/Missed/Dropout, priority A–D, smart remarks), revenue, vacation, emits `Staff_Action_Today.xlsx`. **Auto-push (S19):** a folder watcher mirrors each new workbook to the Sheet automatically (D22). | Docterz CSVs, prior outcomes | Workbook, ledgers, `Followups_Today`/`Followups_Settled` | Dashboard shows yesterday’s list; manual `--push` fallback |
| **Follow-up call console** | BUILT (ingest proven) / wiring next | Live worklist with one-tap calling + outcome capture | Followups_Today | Followup_Outcomes | Falls back to the Excel |
| **WABA send arm** | BUILT (ready) | Maps status → approved `drmanoj_*` templates, sends with dedupe/opt-out/cap/window rails | Ledger, contact log | Messages log, contact log | Calls/console unaffected |
| **Evidence — recordings + Sarvam** | PARTLY (Drive auto; Sarvam pipeline built) | On-demand transcription for flagged/disputed calls | Drive recordings | Transcripts, verdicts | Transcription pauses only |
| **360° patient query** | BUILT (server fn) / card UI pending | Find patient by Clinic ID / mobile / name → visits, diagnosis, follow-up, (later: revenue, docs). `lookupPatient360` live in WebApp.gs; Dashboard.html card UI still to build + deploy | All patient tabs | — (read-only) | Search empty, nothing else affected |
| **Document repository** | PLANNED | Lab PDF / X-ray JPG / MRI report, tagged Clinic ID + date | — | Local files + Sheet index | Independent lane |
| **Revenue Reconciler (pharmacy/lab → ledger)** | **LIVE** (clinic PC) | Ingest Marg (pharmacy) + Labmate (lab) Excel; match each bill to a patient; matched → /finance, doubtful/unmatched → held review queue | Marg/Labmate Excel, visit spine, master | `revenue_ledger.csv` (matched), `revenue_pending_review.csv` (held) | Manual /lab form stays as fallback |
| **HR lane — attendance/salary** | PARTLY (salary engine exists) | Punctuality, uniform+I-card, leaves → bonus/increment | HR inputs | HR records | Fully separate trust class |
| **Insight — de-id clustering** | PARTLY (pipeline exists) | Periodic de-identified transcript analysis → system improvement | De-id transcripts | Insight reports | Offline, batch |
| **Supervisor — doctor.py** | PLANNED | Watches all modules, alerts humans, daily “all good” ping | Health checks | Alerts (ntfy/WhatsApp) | (Is itself the watchdog) |
| **Launcher portal** | BUILT (S19) / deploy pending | One door to all tools (phone + laptop). Phase-1 doctor-only: PIN + device-trust cookie, 11 tiles (6 live links + 5 held labels). `portal.py` Flask :8090 at `/portal`. Phase-2 staff RBAC deferred. (D23) | — (links only) | — | Tools remain reachable by their own URLs |

**Already-live foundation (the cockpit + engine):** the Apps Script **dashboard (build v17.x)** (callbacks, WhatsApp feed/thread/reply incl. inbound images, click-to-call, per-agent server-bound keys, sheet-driven roster) and the **VPS relays** (inbound WhatsApp receiver `wa-receiver.service` on gunicorn :8095, WhatsApp send relay, OBD click-to-call relay on port 8097, ntfy notifier `wa-notifier.service`). These are LIVE and not to be rebuilt. **Session 16: the FULL 11-file Apps Script project is now captured in Git/handoff** (previously only WebApp.gs + Dashboard.html), and the inbound-media two-push bug is fixed (see D13).

---

## 7. The refined follow-up outcome model (supersedes the old dropdown)

**Principle:** the system derives what it can; staff capture only the human nuance; the doctor adjudicates the edges. Self-reported, gameable fields are removed.

- **Removed** (the call log already knows): *NOT PICK*, *SWITCH OFF*. The agent records an outcome **only when they actually spoke**.
- **Auto-settled from evidence (no staff action):**
  - Patient appears in the day’s consultation CSV → **Returned / Done.**
  - Medicine bought **here** → verified against **Sanjeevni** sale report (Clinic-ID matched).
- **Spoke-to outcomes (capture the nuance → drive a next action):**
  - **Coming / out of town** → record expected date (“kab dikhayenge”) → re-surface then.
  - **On medication — here** (auto-verify Sanjeevni) / **outside** (+ how many days’ supply).
  - **“Dikha chuke”** → dashboard shows last-visit date alongside; if it doesn’t reconcile → **escalate to Doctor + Shavez and persist until resolved.**
  - **Problem / needs attention** → escalate.
- **Medicine-safety nudge (targeted, utility, evidence-triggered ONLY):** when a patient’s own record shows *last visit long ago + still on the same drug*, send a single, personal, clinical note (“doctor ko dikhaye bina yahi dawa itne din… dikkat/nuksan ho sakti hai”). **Not** a broad broadcast.
- **Doctor authority — “Close follow-up · treatment complete”:** the doctor can remove selected patients from the follow-up loop when their record shows the major treatment is over (the point at which many patients naturally stop coming). This keeps the dropout signal **clinically honest** — natural recovery is not dropout.

---

## 8. Identity & access tiers

| Tier | Who | Sees |
|---|---|---|
| **Doctor** | Dr. Manoj | Everything, including transcripts, revenue-per-patient, verification verdicts |
| **Operations** | Shavez | Operational worklists + verification + 360° view; on-demand transcription |
| **Staff** | Reception / callers | Their worklist only — no revenue, no transcripts |
| **HR lane** | (separate) | Attendance/salary data — kept apart from all patient data |

The **calling roster** = the IVR members (dashboard v15 Agents tab). On-demand transcription access = **Doctor + Shavez only**.

---

## 9. Messaging policy (WABA)

- **Targeted utility messages** (tied to one patient’s own record) are the default — clinically strong and safe under Meta’s rules. The **medicine-safety nudge** and **comorbidity reminders** are of this kind.
- **Comorbidity reminders** (diabetes / HTN / thyroid) stay **recovery-contextual** — e.g. “controlled sugar helps bone/joint healing” — never generic disease management (that is the patient’s physician’s lane). Low-frequency, high-warmth.
- **Broad educational broadcasts** are *marketing* under Meta: opt-in, marketing-category templates, STOP honoured, **very conservative cadence** (a couple of times a year at most). Lead with targeted, use broad sparingly.
- **Cadence for an older base:** call is primary (voice reaches the elder); WhatsApp complements (reaches the family caretaker, nudges app use). A **shared contact log** prevents call + WhatsApp double-touch in the same window.
- **Channel-of-acquisition** is captured **mandatorily at first contact** (GMB / patient-referral / doctor-referral / hoarding / app / walk-in / family) — it cannot be reconstructed later, and it reveals which channels convert to surgery and which referrers to nurture.

---

## 10. Evidence & transcription policy

- **First month:** auto-transcribe **all flagged (metadata-mismatch) calls** to establish deterrence — **announced to staff** (deterrence works because the check is known, not secret; this also protects morale). The month calibrates the flagging logic and sets a baseline.
- **After:** transcription is **on-demand only**, **frictionless**, restricted to **Doctor + Shavez**.
- **Retention & access:** transcripts viewable by Doctor/Shavez only; set a retention window (e.g. 90 days then purge); **de-identify** for any aggregate/insight use.
- **Recordings** auto-archive to the clinic Google Drive (MyOperator). On-demand transcription fetches the specific call only.

---

## 11. The Supervisor — `doctor.py` (watch, don’t fix)

A small scheduled module whose only job is to watch the others and alert the right human. It **never repairs** — it **reports**.

Checks each run:
- Tracker produced today’s workbook? Ingest pushed to the Sheet?
- VPS relays (call / send / receive) answering health checks?
- Recordings synced to Drive? Sarvam quota/balance healthy?
- Escalations unactioned > N hours (e.g. “dikha chuke” mismatches)?
- Last night’s PHI/document backup completed?

Alerts go to **Doctor + Shavez** via a trusted channel (ntfy / WhatsApp). A daily **“all systems normal”** ping is mandatory — silence is ambiguous; a green ping proves the watchdog itself is alive. Alert design rule: **rare, specific, named owner, clear action** — alert fatigue kills watchdogs faster than bugs.

---

## 12. Maintenance ownership manual (living — refine as needed)

| Owner | Cadence | Responsibilities |
|---|---|---|
| **Diagnostics system (automated)** | Continuous (30s poll) + periodic (30min watchdog, 7AM deep check) | Fault detection, auto-diagnosis, incident banner with fallback protocols, doctor escalation after 15min unresolved, auto-resolution confirmation. `System_Health` tab is the incident record. |
| **Supervisor (automated)** | Continuous | Health checks, backup verification, quota warnings, daily all-good ping |
| **Shavez (human-daily)** | Daily | Confirm the morning ingest ran, clear escalations, action the worklist |
| **Doctor (human-periodic)** | Weekly / monthly | Review flagged-call verdicts, close completed follow-ups, review dropout/channel/demographic patterns and adjust cadence |
| **Claude (AI, per session)** | As needed | Build changes/new modules, run periodic de-identified analysis, keep this doc + Notion current |

This table is the **maintenance manual** from now on; expand its rows as new modules go live.

---

## 13. Demographics lens (what makes this uniquely ours)

- **Risk-weight the chase** by clinical need × dropout likelihood — not uniformly. Trauma/post-op must be chased (time-critical healing); chronic-OA fades once pain eases. The “close follow-up” control + condition tags make this possible.
- **Two audiences per patient:** the elder (reached by voice) and the family caretaker (reached by WhatsApp). Flag shared-number/family cases.
- **Seasonality is real:** sowing/harvest, festivals, weddings, daily-wage cash cycles all spike “bahar gaye / baad mein aayenge”. Over a year the data shows the pattern; cadence should bend to it, not nag through it.
- **Relationship is the asset.** Patients answer because of thirty years of trust. Every automated touch must reinforce that, never dilute it.

---

## 14. Rollout order (each lane shippable alone, no big-bang)

1. **Follow-up call + verification loop** — console (ingest proven) → outcomes → tracker loop → on-demand Sarvam dispute-settle. Includes the refined outcome model and the doctor’s “close follow-up” control. *Highest leverage: patient safety + revenue retention + accountability in one.*
2. **WABA send arm into the cockpit** — shared contact log, demographics-aware cadence, Review & Send.
3. **360° patient query box** — build now on current data; widens automatically as new banks join (because Clinic ID is honoured).
4. **Move the brain + schedulers to the VPS** — 24×7; clinic-PC double-click kept as fallback.
5. **Parallel lanes, pulled in as needed:** document repository (with 3-2-1 backup) · revenue MIS (Sanjeevni/Labmate/Marg) · HR attendance/salary · insight (periodic de-identified clustering).

**Foundations locked from day one:** Clinic-ID join key · one-writer-per-table · degrade-to-fallback · access tiers · record backups · secrets-never-in-Git/Notion.

---

## 15. Decisions log (locked)

| # | Decision | Date |
|---|---|---|
| D1 | Transcription: 1-month announced auto-transcribe of flagged calls for deterrence; then on-demand, frictionless, Doctor + Shavez only | 28 Jun 2026 |
| D2 | Accountability operational first; incentive planned later (reward patient outcomes, not raw call counts) | 28 Jun 2026 |
| D3 | Call is primary, WhatsApp complements; shared contact log prevents double-touch; cadence bends to demographics/seasonality | 28 Jun 2026 |
| D4 | Console + Sheet become primary; Excel stays as fallback until ~2 weeks of clean running, then cutover | 28 Jun 2026 |
| D5 | Outcome model refined: drop NOT PICK / SWITCH OFF; auto-settle from evidence (consultation CSV + Sanjeevni); staff capture conversation only; doctor closes completed follow-ups | 28 Jun 2026 |
| D6 | Medicine-safety nudge is targeted/utility/evidence-triggered only — never a broad broadcast | 28 Jun 2026 |
| D7 | Comorbidity reminders stay recovery-contextual, low-frequency | 28 Jun 2026 |
| D8 | Maintenance ownership is a living manual (§12) | 28 Jun 2026 |
| D10 | Incoming high-intent collapses to ONE "Doctor/urgent" path (surgery/fracture/accident/severe-pain): reception does not triage clinically; it always escalates AND captures outcome, fires an instant ntfy push (incl. patient number — accepted privacy tradeoff for fast call-back, no clinical text), and staff also call the doctor immediately. Terminology is "patient", never "lead". | 28 Jun 2026 |
| D11 | Revenue reconciliation: map maximum CORRECT external revenue (pharmacy/lab) from 1 April; NEVER drop a rupee; doubtful rows -> per-patient review list; truly unmatchable -> "Unclassified" (still counted). Two eras: Clinic-ID-suffix (clean, 20-Jun-on Marg / suffix-era Labmate) vs pre-suffix historical (name + bill-date<->visit-date fuzzy match). Never force-assign to the wrong patient. The tracker's /finance views already exist; the real goal is reaching them from the phone (migration lane). | 28 Jun 2026 |
| D11a | Revenue Reconciler GO-LIVE (Session 16): proven on the real Labmate file (200 bills / ₹3,50,130 → 148 matched / ₹2,58,560 · 52 held / ₹91,570). Only MATCHED bills enter the live ledger; REVIEW + UNCLASSIFIED are held in `revenue_pending_review.csv` and enter the ledger ONLY after manual promote at /revenue/review. Date-match window ±3 days. The combined Apr–Jun consultation report MUST stay in `…/followup_tracker/uploads/` so April/May bills can date-match (its absence silently drops matches to "held"). | 29 Jun 2026 |
| D12 | Full-source-of-truth discipline: the COMPLETE Apps Script project (all 11 files) must be captured in Git + handoff, not just the two edited files. Half-captured projects caused half-blind debugging. `CallField.gs.gs` / `Probe.gs.gs` keep their doubled `.gs` names to mirror the live project exactly. After ANY Dashboard.html change, publish a **New version** (Manage deployments → Edit → Version) or `/exec` keeps serving old code. | 29 Jun 2026 |
| D13 | Inbound WhatsApp media arrives as TWO pushes with the SAME message id: 1st has `context.link=null` (S3 not ready), 2nd (~2–7s later) carries the real link. Any consumer must allow a later push to FILL a blank media cell rather than discarding it as a duplicate. Receiver is `wa-receiver.service` (gunicorn :8095) — distinct from `wa-notifier.service` (ntfy watcher). Always run VPS python via `/root/wa/venv/bin/python3` (only the venv has gspread). | 29 Jun 2026 |
| D15 | Diagnostics & Surveillance System — continuous self-monitoring: dual detection (client 30s poll + server 30min watchdog + 7AM deep check), auto-diagnosis on fault detection, three-layer incident banner (what broke + keep working now + fix steps), 15-min escalation to doctor with pre-packaged context, auto-resolution when fault clears. Spec: `Diagnostics_Surveillance_System_Spec_v1.0`. Build sequence: Step 3a core checks → 3b banner → 3c alerting. | 30 Jun 2026 |
| D16 | Maintenance & SOP project — third Claude project created AFTER `Diagnostics.gs` is live and has run for at least one real clinic day. Not before. Spec: `Maintenance_SOP_System_Spec_v1.0`. Drive folder structure: `Clinic Automation / Specs & Architecture / SOPs / Incident Reports / Code Exports / Handoff Kits /`. | 30 Jun 2026 |
| D17 | ClickUp parked — subscription not renewed. Notion + Drive + Runbook §2 sufficient for backlog and task tracking. Revisit only if genuine gap emerges. | 30 Jun 2026 |
| D18 | Connector hierarchy — Drive + Notion = primary (connected, stable, high value). Gmail = backup alert channel. Chrome = specific justified tasks only (e.g. Docterz export automation). Claude Code = VPS operations in Maintenance project only, doctor-approved actions, never automatic for live system changes. | 30 Jun 2026 |
| D19 | Parallel build+diagnostics discipline — every new or changed file gets a `FAILURE MAP` comment block documenting external dependencies, fault codes, fallback behaviours inline. `Diagnostics.gs` Step 3 emerges from Steps 1+2 naturally. Build-first-monitor-later is retired. | 30 Jun 2026 |
| D20 | Follow-Up Tracker single-point-of-failure eliminated — core code in GitHub (`followup-tracker/`, 42 files), data in Google Drive continuous sync (confirmed 30 Jun). VPS migration is next step. `.gitignore` hardened with explicit folder blocks. | 30 Jun 2026 |
| D21 | Google storage — `drmka.ortho@gmail.com` has 5TB via Koo promo until ~13 May 2027. This is the clinic data backup home. Review storage plan by 1 April 2027 before expiry. OneDrive connector not needed. | 30 Jun 2026 |
| D22 | Follow-up auto-push is AUTOMATIC via a local folder watcher + Windows Startup auto-start (interim home until the VPS migration). The watcher polls the tracker `outputs\` folder (polling, not OS events — Drive sync churn would create false triggers), dedups on name\|size\|mtime, and calls the proven `push_followups_today.py --push`. Manual fallback (`--push`) always remains. The proper long-term home is still the VPS migration. | 30 Jun 2026 |
| D23 | Unified launcher = phased. Phase 1 = doctor-only launcher (`portal.py`, PIN + indefinite device-trust cookie, NOT biometric — a PIN survives device repair/factory-reset that would wipe WebAuthn passkeys). Phase 2 = staff role-based access (the 3–6 month build), deferred. The launcher links to existing tools; it never rebuilds them. Tiles flip held→live by editing one config line. | 30 Jun 2026 |
| D24 | Fix at the data PRODUCER, not the live CONSUMER, when both could solve a bug. The "2001" due-date bug (yearless dates from the tracker, mis-yeared by the dashboard) was fixed in the push script (`to_full_date()` normaliser) rather than by editing the live Apps Script dashboard — lower blast radius, the clinic's primary tool stays untouched, and the data is correct for every downstream reader. | 30 Jun 2026 |

---

## 16. Infrastructure reference (identifiers only — NOT secrets)

- MyOperator: Company ID `68384350414b9847` · WABA ID `2101222617483538` · Phone Number ID `1090067637530949` · IVR DID `8065293652` · WABA number `9358008080`.
- VPS: `followup.dr-manoj.in` (`93.127.195.49`), CyberPanel + OpenLiteSpeed + gunicorn, work dir `/root/wa`.
- Google Sheet (spine): `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`. Service account: `patient-mirror@…` (key on the local device / VPS only).
- Dashboard: Apps Script `/exec`, build v17.x (full 11-file project in Git). GitHub: `drmanoj-clinic-automation`. Notion: “Clinic HQ”.
- VPS services: `wa-receiver.service` (inbound webhook receiver, gunicorn 127.0.0.1:8095) · `wa-notifier.service` (ntfy watcher) · OBD relay :8097 · WhatsApp send relay. Run VPS python via `/root/wa/venv/bin/python3`.
- **Secrets** (WhatsApp Bearer, OBD x-api-key/secret, public IVR id, Logs token, Sarvam key, relay gate secrets, service-account JSON) live **only** in `/root/wa/.env` (chmod 600), the local device, and Apple Notes — **never in this document, Git, or Notion.**

---

## 17. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 28 Jun 2026 | First umbrella architecture: principles, hub-and-spoke, data-bank charter, three loops, module inventory, refined outcome model, access tiers, messaging & evidence policy, supervisor spec, maintenance manual, demographics lens, rollout order, decisions log |
| 1.1 | 28 Jun 2026 | Added decision D10 (incoming "Doctor/urgent" path); corrected §16 dashboard build to v17.1. |
| 1.2 | 28 Jun 2026 (Session 14) | Added decision D11 (revenue reconciliation strategy). Confirmed the tracker's /finance views already exist (trapped on C: drive) -> the goal is phone-reachability, not rebuild. Noted the C-drive->structured migration lane (M1-M6) and that the 360 patient lookup server fn is built (card UI pending). See Master KB v1.2 §14 for all verified specifics. |

| 1.3 | 29 Jun 2026 (Session 16) | Revenue Reconciler flipped PLANNED→LIVE (D11a); added D12 (full Apps Script project capture + New-version publish discipline) and D13 (inbound WhatsApp two-push media handling; wa-receiver vs wa-notifier; venv python). Updated §6 module statuses (360° = BUILT/card pending), dashboard v15→v17.x, and §16 infra (VPS services list). See Master KB v1.4 §16 for all verified Session-16 specifics. |

| 1.5 | 30 Jun 2026 (Session 18) | Added decisions D15–D21 (Diagnostics & Surveillance system, Maintenance project timing, ClickUp parked, connector hierarchy, parallel build+diagnostics discipline, tracker single-point-of-failure eliminated, Google storage decision). Added Diagnostics system row to §12 maintenance manual. Added §18 Surveillance & Maintenance Architecture. Updated §16 infra (repo now includes `followup-tracker/`). |

| 1.6 | 30 Jun 2026 (Session 19) | Added decisions D22 (follow-up auto-push via local folder watcher + Startup auto-start), D23 (phased unified launcher — doctor-only Phase 1, PIN+device-trust not biometric), D24 (fix at the data producer not the live consumer). Updated §6 module inventory: Brain row notes auto-push; new Launcher portal row (BUILT/deploy pending). See Master KB v1.7 §19 for verified Session-19 specifics. |

*End of document. Keep one copy in Notion “Clinic HQ” and one in the handoff kit. Update the decisions log and module inventory as the system evolves.*

---

## 18. Surveillance & Maintenance Architecture (Session 18)

### 18.1 The monitoring stack

The system now has a defined self-monitoring layer sitting above all operational modules:

```
DETECTION (continuous)
  Client poll every 30s → anomaly detection → fires runFullDiagnostics()
  Server watchdog every 30min → lightweight critical checks
  7AM daily → full deep diagnostic suite

DIAGNOSIS (automatic, seconds after fault)
  5 check categories → named fault code → plain description
  Specific cause identified before any human sees the banner

INFORM (all staff simultaneously, <30s after fault)
  System_Health tab → dashboard reads on every poll
  Red banner: Layer 1 (what broke) + Layer 2 (keep working now) + Layer 3 (fix steps)

ESCALATE (15min after fault if unresolved)
  ntfy push → doctor with pre-packaged context
  Drive incident report auto-created

RESOLVE (automatic)
  Next watchdog pass confirms fix → banner clears → incident closed
```

### 18.2 The three-project structure

| Project | Purpose | Contains |
|---|---|---|
| **Systems & Automation** | Build new modules | Code, VPS, APIs, GitHub |
| **Clinic & Growth** | Non-code operations | Website, GMB, HR, strategy |
| **Maintenance & SOP** (to create) | Monitor and fix live systems | SOPs, incident history, KB, Drive + GitHub connected |

The Maintenance project is created AFTER `Diagnostics.gs` is live. It opens with a complete picture of a running system, real incidents to reference, and proven fallback protocols.

### 18.3 Connector hierarchy (D18)

| Connector | Role | Status |
|---|---|---|
| Google Drive | Document home, session close deposits, incident reports | ✅ Active |
| Notion | Live updates during session close, decisions, module register | ✅ Active |
| GitHub | Code reading during sessions | ✅ Active (read-only) |
| Gmail | Backup alert channel if ntfy quota exceeded | Available |
| Chrome | Specific justified tasks only (Docterz export, MyOperator panel monitoring) | Future |
| Claude Code | VPS operations, doctor-approved only, never automatic | Future (Maintenance project) |
| ClickUp | Parked (D17) | Not active |

