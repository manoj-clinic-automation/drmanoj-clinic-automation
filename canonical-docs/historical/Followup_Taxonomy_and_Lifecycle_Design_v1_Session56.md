# Follow-Up Taxonomy & Lifecycle Design — v1 (Session 56)

**Author context:** Dr. Manoj Agarwal Clinic, Bareilly — solo orthopaedic practice, older Hindi-first semi-urban patient base.
**Status:** DESIGN document (no code). To be *validated* against one month of real follow-up data in the next session.
**Supersedes:** the abstract T1/T2/T3 sketch in the Session 55 lifecycle proposal (P1).

---

## 0. What this document is

Two distinct pieces of work were completed in Session 56, both design-level, no code:

1. **The caller-ID root-cause fix** — why follow-up calls go unanswered, and the confirmed no-code SOP that fixes it.
2. **The follow-up taxonomy & lifecycle model** — a three-axis model (Diagnosis × Status × Clinical Phase) that drives how hard the system chases each patient, replacing the crude tier sketch.

This document is the canonical reference the *next* session (data analysis) builds on.

---

## PART A — The Caller-ID Root-Cause Fix (SORTED)

### A.1 The problem (root cause)

When the clinic calls a patient for follow-up, the patient's phone shows the **outbound DID: 8065293652** — a number they have never seen. Older patients do not answer unknown numbers → the call is logged as "no answer" → the system wrongly treats them as unreachable and keeps chasing. A large share of "no answers" are likely **unrecognised-caller-ID**, not genuine non-contact.

### A.2 The confirmed number architecture

| Number | Role | Patient experience |
|---|---|---|
| **9358008080 ("93")** | Public/WhatsApp (WABA) number. Postpaid SIM kept idle for **number continuity & ownership**. All calls to it **divert to 8047947130**. | The number patients know / dial |
| **8047947130** | Panel primary / inbound landing line (where 93 diverts). Admin-type use. | Receives inbound calls |
| **8065293652** | **The single outbound DID** — caller ID for ALL clinic→patient calls (MyOperator DID page confirms only one outbound DID). | **What patients SEE when the clinic calls them** |

**Key fact:** inbound and outbound numbers are **different**. Saving the number a patient *dials in on* does NOT make an *outbound* follow-up call recognised. Only saving **8065293652** fixes recognition.

### A.3 The fix (no code, no new template, staff-assisted)

1. Staff asks the patient to **give a call to 93 (9358008080)** — a number they already know; reinforces the correct public number.
2. The call diverts and **triggers the existing WABA post-call template** on the patient's WhatsApp (many patients already have it). No new template built.
3. Staff **assists the patient to tap `save.dr-manoj.in`** in that message → the vCard saves.
4. The vCard contains **8065293652** (the outbound DID) + 9358008080 → future follow-up calls now show **"Dr Manoj Agarwal Clinic"** → patient answers.
5. **Bonus:** the patient is now a **WABA opt-in** → free session messages (disease-specific branded forwards) possible within the 24-hour window.

### A.4 The one mistake to avoid

**Do NOT let the patient merely save the 93 number they dialled.** The clinic calls out from a *different* number (8065293652). The save must go through **`save.dr-manoj.in`** (the vCard), or the fix fails silently.

### A.5 Rejected approaches (and why)

- **Reception-mobile forwards the contact card** — REJECTED: forwarding exposes the reception/admin mobile number to patients, who may then bypass the IVR. Admin number must stay private.
- **WABA auto-reply sends a native contact card** — NOT POSSIBLE: MyOperator WABA sends templates + session text only; no "contact" message type (confirmed from API docs, Link Generator panel, and Custom Message tab).
- **QR-only save** — LOW ADOPTION: contact QRs are ignored; UPI QRs are scanned reflexively, but that only fixes the *timing*, not the save method.

### A.6 Coverage

- **New patients:** run the 3 steps at checkout, daily.
- **Existing base:** opportunistically at next visit (Option 2 chosen in-session — reach the active follow-up pipeline, not just future patients).

---

## PART B — The Follow-Up Taxonomy & Lifecycle Model

### B.1 The core realisation

Tier (how hard to chase) **cannot** come from the diagnosis label alone. It is driven by **three axes**:

| Axis | Source | Nature |
|---|---|---|
| **1. Standardized Diagnosis** (27 categories) | Docterz periodic fill → normalisation (**already live**) | Automatic |
| **2. Diagnosis Status** (Confirmed / Suspected) | Already in taxonomy file (`?`/`U/O` logic) | Automatic |
| **3. Clinical Phase** (active / remission / stable / relapse) | **Clinician-set, per-patient, dynamic** (updated at visits) | **Manual — clinical judgement only** |

The third axis is new this session. It means the **same diagnosis** can require **different follow-up behaviour** depending on where the patient is in their disease course.

**Worked example — Inflammatory Arthritis:**

| Diagnosis | Phase | Correct follow-up |
|---|---|---|
| Inflammatory Arthritis | Initial / active flare | Chase hard — compliance-critical (behaves like T1) |
| Inflammatory Arthritis | Remission / stable | Light touch — periodic nudge only (behaves like T3) |

A model that tiers on diagnosis alone would over-chase a stable-remission patient — the exact over-chasing flagged at the start of the session ("shouldn't look to be chasing").

### B.2 The normalisation pipeline (already live + the small extension)

```
Docterz CSV (raw free-text diagnosis)
   → [LIVE] normalise → Standardized_Diagnosis (1 of 27)   [Normalization_Rules sheet]
   → [LIVE] status → Confirmed / Suspected
   → [NEW, small] map Standardized_Diagnosis → Tier/Track
   → [NEW, manual] clinician sets Clinical Phase per patient
   → [NEW, the flowchart] Track + Phase drive: cycles, interval, stop rule, escalation
```

The hard part (normalisation) is **already done and flowing through** — confirmed: the Callback Tracker's `Followup_Escalations` tab carries the `Diagnosis` column using the standardized taxonomy verbatim. Diagnosis coverage is **partial but self-healing** — each periodic Docterz fill back-fills blank rows.

### B.3 Tier/Track model — WITH clinical corrections (Session 56)

The design moved from **tier-first** to **track-first** (clinical pathway is the primary branch; the 27 diagnoses feed into a handful of tracks). Corrections locked this session:

**Dropped from hard-chase:**
- **Infection / Osteomyelitis** and **Tumor / Suspected Tumor** — removed from T1. Rationale: "80% effort, 20% outcomes." These are rare and high-touch → **manual / doctor-handled exception path**, not the automated tier engine.

**T2 — prolonged-but-intermittent:**
- Chronic conditions needing prolonged management that **surface intermittently**. Follow-up must expect gaps and re-touch — a gap is NOT failure. (Degenerative joint/spine, radiculopathy, inflammatory arthritis/spondyloarthropathy/gout, osteoporosis, deformity, pediatric.)

**T3 — "the noise":**
- After **2–3 weeks** → move to a **historical / nurture bucket**. Mostly satisfied, loyal patients. Not active follow-up targets — kept warm with **occasional WhatsApp nudges** to preserve the link. (Mechanical spine, soft-tissue/elbow/hand/wrist, foot/heel, general MSK pain.)

**Fractures are a spectrum, not one tier:**
- **Undisplaced / OPD-treated** (the majority) — standardisable, own cadence.
- **Post-surgical** — cluster into groups, each with its own review schedule.
- → "Trauma / Fracture" must **split** into at least these two sub-tracks.

**Severity as a sub-axis:**
- e.g. **Radiculopathy — mild vs moderate/severe** need different follow-up intensity. Severity is a modifier *within* a diagnosis, not captured by the label alone. (Severity data source: TBD — likely clinician-set, same as phase.)

**Prevalence weighting:**
- Design effort should follow volume — inflammatory arthritis %, spondyloarthropathy % etc. are relevant. To be quantified from the one-month data analysis.

### B.4 Which diagnoses need clinical phases (clinician-set)

Phase tracking is **not** needed for every diagnosis — only where the disease course meaningfully changes follow-up behaviour:

| Diagnosis group | Needs phase tracking? | Phases that matter |
|---|---|---|
| Inflammatory Arthritis / Spondyloarthropathy / Gout | **Yes** | Active flare → Remission → Relapse |
| Post-Operative Follow-Up | **Yes** | Early post-op → Rehab → Discharged-stable |
| Trauma / Fracture | **Yes** | Acute → Healing → United/discharged |
| Post-Traumatic Rehab | **Yes** | Active rehab → Plateau/discharge |
| Degenerative (OA knee/hip/shoulder, spondylosis) | **Partial** | Symptomatic → Controlled (mostly intensity, not true remission) |
| Radiculopathy | **Partial** | via severity (mild/moderate/severe) more than phase |
| Osteoporosis / Metabolic | **Light** | On-treatment → Maintained |
| Mechanical spine / soft-tissue / heel / general MSK | **No** | Self-limiting → exits to nurture bucket |

### B.5 Flowchart structure (agreed shape, not yet drawn)

- **Structure: track-first (Option B).** Primary branch = clinical pathway; diagnoses feed into tracks; tier is a coarse label on top of tracks.
- The flowchart itself is **deferred** to after the data pass — because the data should shape the branches (real return-rates, real cycles-to-settle), not guesswork.

---

## PART C — Next-Session Agenda (defined, carried forward)

These items could NOT be done in Session 56 (require live/PHI data and clinician action):

1. **[Owner: Manoj/Shavez] Run the Docterz periodic fill** — so the Callback Tracker `Diagnosis` column is near-complete before analysis. Analysis on stale, partially-blank data would skew the tier picture.
2. **[Next session] One-month follow-up data analysis** — aggregate only. Measure, by diagnosis:
   - return-rate / re-surfacing frequency (this IS the empirical tier)
   - cycles-to-settle (real cycle lengths, not guessed)
   - outcome-mix (settled / not-interested / treatment-elsewhere / already-visited)
   - T3 "noise" rate and true 2–3-week exit point
   - effort-vs-outcome by category (validate the Infection/Tumor 80/20 drop)
   - prevalence weighting per diagnosis
   - **blank-diagnosis bucket size** after the fresh fill
3. **PHI-access method to be chosen** before the analysis: **PHI-stripped export** (recommended — honours "patient data NOT in this project") vs connector read (aggregate-only). *Note flagged in-session: the Drive connector CAN pull patient names + mobiles via contentSnippet — treat with care.*
4. **After data:** finalise tier/track assignments against real behaviour, then **draw the track-first flowchart**.
5. **Later:** define the clinician-set phase/severity capture mechanism (workflow step at visits).

---

## Appendix — Confirmed facts locked this session

- Outbound DID = **8065293652** (single outbound caller ID; MyOperator DID page).
- Inbound ≠ outbound number (the reason saving-the-dialled-number doesn't fix pickups).
- 93 (9358008080) diverts to 8047947130; kept idle for continuity/ownership; also WABA/WhatsApp.
- WABA can send templates + session text only — **no native contact card** (3 independent confirmations).
- Diagnosis normalisation is **live** and flows to `Followup_Escalations.Diagnosis`.
- Clinical phase source = **clinician** (not system-inferred).
- Follow-up structure = **track-first**.
