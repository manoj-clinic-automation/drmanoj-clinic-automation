# Call Pipeline Audit — Evidence & Future Plan
**Dr. Manoj Agarwal Clinic · Advanced Orthopaedic Surgery Centre, Bareilly**
**Date: 02 July 2026 · Sessions 37–45 · Compiled at EOS Session 45**

This is the standalone evidence document requested at EOS. It covers: what we found, the verified numbers, what it means, and the ordered future plan. Cross-references to the Master KB (D53–D61) and Handoff Runbook v29 for full context.

---

## PART 1 — THE AUDIT

### What triggered it
After deploying v18.2 (Doctor's Outcome Review Console), the console showed "no recording / no transcript / logged at 20:56 (no call matched)" on outcome rows. The doctor asked for an irrefutable audit before any further action.

### What we examined
| Source | What it holds | Rows examined |
|---|---|---|
| MyOperator panel export (12 .xls files) | Ground truth of all clinic calls | 225 raw → **167 deduplicated** (30 Jun – 2 Jul) |
| Call_Recordings (Google Sheet archive tab) | Nightly archive of all connected calls | 138 rows |
| Call_Feed (Google Sheet) | VPS-written call log | 2,913 rows |
| Followup_Outcomes (Google Sheet) | Staff-filed outcomes | 270 rows |
| Patient_Master (Google Sheet) | Phone → patient name/ID lookup | 6,495 rows |

---

## PART 2 — THE SIX FINDINGS (irrefutable, with evidence)

### Finding 1 — Archive matches the MyOperator panel perfectly ✅

**Test:** 79 connected calls matched between panel and archive by phone + date.

| Gap (archive time minus panel time) | Count |
|---|---|
| Exactly 0 minutes | 65 of 79 (82%) |
| Within 2 minutes | 71 of 79 (90%) |
| More than 5 minutes | 7 of 79 (all explained: same patient called twice, archive matched later call) |

**Verdict:** The nightly archive (02:00 IST) is a faithful, real-time mirror. No data loss. No systematic lag.

**Corollary — Call_Feed is unreliable:**

| Day | Panel connected | Archive | Call_Feed |
|---|---|---|---|
| 30 Jun | 56 | 56 | 41 (miss rate 27%) |
| 01 Jul | 23 | 24 | 8 (miss rate 65%) |
| 02 Jul | 9 | 0 (archive runs at 02:00 — tonight) | 0 (stale) |

**Decision D55:** Archive is the authoritative internal record. Call_Feed must not be used for matching or analysis.

---

### Finding 2 — Staff call exclusively through MyOperator ✅

**Test:** Cross-checked three days of panel data against outcome-filing times.

- **30 Jun:** 56 connected outgoing calls in panel. 56 recordings in archive. **100% match.**
- **01 Jul:** 23 connected outgoing calls in panel. 24 in archive. **Essentially 100%** (one duplicate call logged differently).
- **02 Jul:** 20 calls made 08:51–09:18. 13 outcomes filed 09:56–09:58. Gap = 41–63 minutes. **Calls came first, batch outcome-filing came after.**

Earlier hypothesis (staff using personal mobiles) was eliminated. Staff call only through the clinic IVR system.

**Outcome filing pattern:**

| Lag after call | Count | % |
|---|---|---|
| Within 5 minutes | 43 of 57 | 75% |
| 5–60 minutes | 6 of 57 | 11% |
| More than 1 hour | 8 of 57 | 14% |

The 41–63 minute batch is normal: staff finish their calling session, then sit down and log all outcomes. This is not a delay problem.

---

### Finding 3 — 75% of outgoing missed calls received fabricated outcomes ⚠️ KEY FINDING

**Test:** All 63 outgoing missed calls cross-checked against Followup_Outcomes by phone + date.

| Day | Missed outgoing | Given an outcome | No outcome |
|---|---|---|---|
| 30 Jun | 42 | 34 (81%) | 8 |
| 01 Jul | 10 | 9 (90%) | 1 |
| 02 Jul | 11 | 4 (36%) | 7 |
| **Total** | **63** | **47 (75%)** | **16** |

**Outcome codes filed on missed (no answer) calls:**

| Code | Count | What it claims |
|---|---|---|
| coming | 20 | Patient said they'll come |
| not_interested | 17 | Patient said not interested |
| on_medication | 15 | Patient said on medication |
| dikha_chuke | 14 | Patient said already visited |
| out_of_town | 6 | Patient said out of town |
| treatment_elsewhere | 3 | Patient said going elsewhere |
| close_followup | 2 | Treatment complete |
| problem | 1 | Patient has a problem |

Every one of these codes implies a conversation. None of them had one — the patient never picked up.

**Why this matters:**
- These outcomes have no recording (no call connected)
- These outcomes have no transcript (nothing to transcribe)
- The review console correctly shows "no call matched" for all 47 — it is reporting accurately
- When Stage-3 AI verdict layer is built, these rows will be unflagable and will corrupt the AI's training signal
- Some patients marked "not interested" or "treatment elsewhere" are probably still interested — they just didn't pick up

**Decision D57:** No outcome dropdown on outgoing missed calls. Two escape-valve codes only: "No answer — will retry" and "No answer — removing". Ring duration is available for display (confirmed: MyOperator exports it for missed calls).

---

### Finding 4 — The 20:56 call (…8885, 1 July) — closed ✅

**Panel record:** One entry for …8885 on 1 July: **incoming missed, 7 seconds, at 15:44.**

**Outcome log entry:** `2026-07-01 20:56 | outcome: in_no_action | section: Incoming | by: Dr Manoj Agarwal`

**Gap:** 5 hours 12 minutes.

**Verdict:** The 15:44 missed call is the real MyOperator record. The 20:56 outcome was filed by the doctor — almost certainly for a conversation that happened via WhatsApp, direct call back, or in person. The number (1206138885) has a '120' STD prefix (Bareilly landline range), not in Patient_Master. The system reported correctly: no recording exists because no call connected through the IVR at 20:56.

---

### Finding 5 — 90% of settled patients reappear on the next day's list ⚠️ KEY FINDING

**Test (Session 34 audit):** 150 patients who received 'settle' or 'escalate' outcomes on prior days cross-checked against today's Followups_Today tab.

| Settle type | Prior patients | Reappearing today |
|---|---|---|
| settle | 108 | 86 (80%) |
| escalate | 82 | 48 (59%) |
| retry | 2 | 1 |
| **Total** | **150** | **135 (90%)** |

Real examples reappearing: "dikha_chuke" patients (already visited), "close_followup — treatment complete" patients, "not_interested" and "treatment_elsewhere" patients.

**Why:** `push_followups_today.py` explicitly does not read `Followup_Outcomes` — it rebuilds the worklist fresh each morning from the tracker. This is correct by the one-writer-per-table principle, but it means the loop is open: outcomes are recorded but never act on tomorrow's list.

**Decision D59:** Suppression must happen at the source. A new step in `push_followups_today.py` (or a companion script) reads APPROVED outcomes from `Followup_Outcomes` and excludes matching phones from the next day's push.

---

### Finding 6 — Ring duration for missed calls is recorded ✅

**Test:** Checked MyOperator's `Duration (in seconds)` field on missed-call rows.

Sample missed-call ring durations from the panel: 7s, 10s, 17s, 18s, 25s, 34s, 40s, 46s, 49s, 51s, 52s, 54s, 56s, 61s, 63s.

This is ring duration (time until voicemail/cut-off), not talk time — no talk happened on these calls.

**Decision D57b:** Each attempt on a missed-call tile can show "📵 Missed — rang for Xs" with the real ring duration from the archive/feed.

---

## PART 3 — WHAT THE SYSTEM IS DOING CORRECTLY

Worth recording so these are not "fixed":

1. The review console's "no call matched" message is **accurate** — it correctly identifies rows where no connected call exists.
2. The archive is **working perfectly** — every connected call that goes through MyOperator is captured.
3. The transcription pipeline is **81% healthy** (114/140 succeeded; 26 failed with the same Sarvam error — needs a retry pass).
4. Staff **are** using the system — the panel confirms all calls go through MyOperator IVR.
5. The Clinic ID (D51/D52) now shows correctly on both call-console and follow-up rows.

---

## PART 4 — THE FUTURE PLAN (ordered)

### Immediate (Session 46)
**v18.3 — two known defects:**
- Fix band default-open (ol: prefix issue)
- Add last-visit date to outcome rows (spec §7.3)
- Add "📵 missed — no recording" chip on rows with no call match
- Dashboard.html only

### Short-term (Sessions 46–48)
**Missed-call outcome blocker (D57/D60):**
- Remove outcome dropdown from outgoing missed-call tiles on staff dashboard
- Add attempt-history tile: each attempt shows time · agent · ring duration (Xs)
- Two only allowed codes: "No answer — will retry" / "No answer — removing"
- Retry button places a new OBD call and adds a new attempt line
- Tile stays until a call connects or doctor dismisses
- Requires live call-status feed to drive tile state

**Unified doctor console + Escalations fold-in (D58):**
- All outcomes (not just escalated ones) flow to the doctor review console
- Old Escalations widget merged into the outcome bands
- Doctor approves → permanently logged; sends back → staff revisit

**Loop-closing suppression (D59):**
- New step in push_followups_today.py reads APPROVED rows from Followup_Outcomes
- Matching phones excluded from the next morning's push
- Test: 90% reappearance rate should drop to near 0% for approved outcomes

### Medium-term (Sessions 48–52)
- **Staff "sent back" tile** — staff see doctor's "send back" action and the note, with a re-call prompt
- **Step 3 — Doctor's Escalation/Resolve console** (Call_Console_Evolution_Spec §7)
- **Step 4 — Staff Flagged Calls tab** (§8) + Flagged_Queue / Flagged_Calls_Archive
- **Stage 3 — AI verdict layer** (Haiku overnight batch, ~₹200–350/month; metadata gate for missed/sub-30s calls)
- **Call_Feed VPS writer investigation (D61)** — why does it under-report 27% and go stale?

### Standing (not yet scheduled)
- **Service-account key rotation (A1)** — critically overdue; patient data flows through exposed key
- **Transcript retry pass** — 26 Sarvam failures with identical error; batch retry should recover most
- **call_transcription.py GitHub commit** — still VPS-only
- **Diagnostics.gs** — after Stage 4 complete
- **NotebookLM corpus** — needs de-identified transcript volume first
- **DPDP Act 2026 compliance** — 90-day auto-purge (D30) + de-identify step

---

## PART 5 — THE DELIVERABLE FROM THIS AUDIT

`MyOp_Clean_Reconciled_2026-07-02.csv` — 167 rows, one per deduplicated MyOperator call (30 Jun – 2 Jul), showing:

| Column | Description |
|---|---|
| Date, Time | Panel timestamp |
| Phone (last-4) | Masked patient number |
| Patient Name | From Patient_Master lookup |
| Direction | Outgoing / Incoming |
| Status | Connected / Missed |
| Duration (s) | Ring duration (missed) or talk duration (connected) |
| Agent (answered) | Staff member who took/made the call |
| Missed By | Staff who missed it (if applicable) |
| Via | Appointments / Emergency / blank |
| In Archive | YES / NO / OTHER DATE (whether our archive holds this call) |
| Outcome on file | Outcome code + date + staff name from Followup_Outcomes |

This CSV is the single reconciled view of the clinic's 3-day call activity. It can be re-run any time by re-running the audit script from the session transcript.

---

*End of evidence document. Cross-reference: Master KB v1.18 §37–45, D53–D61. Runbook v29 §2 for ordered backlog.*
