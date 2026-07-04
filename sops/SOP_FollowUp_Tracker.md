# SOP — Follow-Up Tracker
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Source of truth: Master KB v1.30 · Runbook Session 62 (v42). KB wins on any conflict.**

> **What this SOP is.** The operational guide for the daily patient follow-up pipeline —
> how the day's call list gets built and lands on the dashboard, and what to do when it
> doesn't. This is the system that empties into an empty list if it silently fails, so it
> has the most surveillance around it.

---

## 1. What the follow-up tracker does

Every day it produces the list of patients staff should call — pulled from the Docterz EMR
exports, normalised into the clinic's diagnosis taxonomy, filtered to who is actually due,
and pushed into the `Followups_Today` tab that the dashboard shows. Staff call, record an
outcome; the system verifies it; the doctor decides terminal states.

**Design principle (important):** for older Hindi-first patients, gentle and well-timed
beats aggressive chasing. "Tune it down" is the standing instruction. Caller-ID recognition
(the patient seeing the clinic's number) is a prerequisite for answer rates.

---

## 2. How the list is built and delivered (current architecture — VPS-native, S60)

As of Session 60 the push is **VPS-native and watcher-free** — the old fragile "clinic-PC
watcher on At-log-on trigger" is no longer the delivery path.

| Piece | Where | Role |
|---|---|---|
| `push_followups_today.py` | VPS `/root/wa` | Builds the day's list, writes `Followups_Today`. |
| `clinic-followup-push` (timer) | VPS | Fires the push at **22:00 / 07:00 / 11:00 IST**. Replace-only / safe to re-run. |
| `clinic-followup-receiver` (:8100) | VPS | Catcher that receives the workbook from the clinic PC. |
| PC hook | Clinic PC | Sends the Docterz workbook up to the catcher. |
| `push_patient_mirror.py` | VPS | Keeps `Patient_Master` mirror fresh. |

**Heartbeat (S62):** the push timer now stamps `/root/wa/heartbeats/followup-push.hb` after
each run, so a silently-missed run can be detected (see `SOP_VPS_Services.md` §3).

---

## 3. What "healthy" looks like

- `Followups_Today` has today's rows after the morning run (by ~07:00, refreshed 11:00).
- `cat /root/wa/heartbeats/followup-push.hb` shows a recent timestamp.
- The dashboard follow-up list is populated and **no red stale-list banner** is showing.
- Normalised diagnoses are flowing (visible in `Followup_Escalations`).
- The daily stale-list sentinel email (2–3 PM) either doesn't fire, or confirms fresh.

---

## 4. The surveillance around this system (three layers)

This is the most-watched pipeline because a silent failure = empty call list.

1. **Apps Script stale-list sentinel** (`Diagnostics.gs::checkFollowupListFresh`) — daily
   2–3 PM trigger; emails if `Followups_Today` looks stale. Also drives the dashboard's
   top-bar stale banner.
2. **Timer-freshness heartbeat** (S62) — `followup-push.hb`; the checker (being armed) alerts
   `FOLLOWUPS_PUSH_MISSED_RUN` (CRITICAL) if the push misses a slot + 2h grace.
3. **The watchman** (S61) — keeps the catcher service (:8100) alive.

---

## 5. Known failure modes & fix paths

### The follow-up list is empty this morning
1. Check the heartbeat: `cat /root/wa/heartbeats/followup-push.hb` — old/missing = the push
   didn't run.
2. Re-run it (safe — replace-only): `systemctl start clinic-followup-push.service`.
3. Confirm: heartbeat updates → `Followups_Today` fills → dashboard shows the list.
4. If it re-runs but the list is still empty, the **input** is missing — did the clinic PC
   send the Docterz workbook to the catcher? Check `clinic-followup-receiver` (:8100) is up
   and that Shavez ran the daily Docterz export.

### List loads but dates look wrong / patients repeat
- Historical bugs to recognise: a push that never read outcomes made settled patients
  reappear (D59, fixed); malformed due-dates (`FOLLOWUPS_DATE_MALFORMED`). If patients who
  were settled reappear, confirm the outcome-reading logic is intact before anything else.

### Stale-list sentinel emailed you
- The list is stale. Follow "empty list" steps above. The sentinel is doing its job — treat
  the email as the early warning it is.

### The old PC watcher comes up in conversation
- It is **superseded** by the VPS-native push (S60). The "At log on" trigger reliability
  problem (which recurred twice) no longer sits on the critical path. Do not reintroduce the
  watcher as the primary delivery route.

---

## 6. The daily human step (does not automate away)

- **Shavez** runs the daily **Docterz CSV export** — this is the raw input. No Docterz API
  exists; the export is manual. If the export doesn't happen, the freshest data won't flow,
  even though the push still runs. This is the one human dependency in the pipeline.

---

## 7. Manual fallback (pipeline down)

- Staff work from the **last good** `Followups_Today` list (yesterday's, if today's failed).
- The doctor can re-run the push by hand once the cause is fixed (`systemctl start
  clinic-followup-push.service`).
- Worst case, the list can be read/filtered directly from the Sheet tabs.

---

## 8. Emergency contacts

| For | Who |
|---|---|
| Daily Docterz export | Shavez (operations/admin) |
| VPS push / catcher / services | Owner (with Claude) — see `SOP_VPS_Services.md` |
| Sheet / dashboard side | Owner (build project) |

---

## 9. On the horizon (context, not current gaps)

- One-month **data analysis pass** on follow-up data (pending fresh Docterz fill + PHI-strip decision).
- **Follow-up taxonomy redesign** (three-axis: Standardized Diagnosis × Diagnosis Status ×
  Clinical Phase) — track-first, clinician-set phase.
- Three-strike WhatsApp nudge; 2 PM list-generation shift (D65); D78 sticky cross-day counter.

---

*Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update in the same session
the push architecture, schedule, or surveillance changes (KB discipline).*
