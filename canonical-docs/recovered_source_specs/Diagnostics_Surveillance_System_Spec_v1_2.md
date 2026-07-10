# Diagnostics & Surveillance System Spec — v1.2 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward everything in v1.1 unchanged. Session 53 promotes the first planned check from "designed" to **LIVE**: the follow-up **stale-list sentinel**. This is the founding piece of the Diagnostics module.

---

## §NEW — FIRST LIVE CHECK: `FOLLOWUPS_LIST_STALE` (Category 1 — process liveness)

**File:** `Diagnostics.gs` (new, in the dashboard Apps Script project).
**Function:** `checkFollowupListFresh` — **time-triggered, 2–3 PM daily** (before the 3 PM calling window).
**Answers:** "Did today's follow-up list actually reach the dashboard?"

**Detection (two failure modes, distinguished):**
- **GENERATION MISSING** — today's `Staff_Action_Today_<yyyy-mm-dd>.xlsx` not found in Drive (searched by exact filename via `DriveApp.getFilesByName`). Message: *check the tracker.*
- **NOT PUSHED** — the file exists but the live `Followups_Today` tab's **newest Due Date** is older than today (dates stored as `DD-Mon-YYYY`; parsed deterministically). Message: *run `python push_followups_today.py --push`.*
- **Fresh** = newest Due Date ≥ today (future "upcoming" rows count). No alert.

**Alert routing:** **email always** (`CFG.EMAIL_TO`, or a `SENTINEL_ALERT_EMAIL` Script Property) + **ntfy phone-push** if a `NTFY_TOPIC_URL` Script Property is set. **No patient data** — counts and dates only.

**Fallback protocol / safety:**
- **Read-only** — writes nothing, touches no writer; reuses `fuSheet_`, `fuReadObjects_`, `dateVal_`, `FU_TAB_TODAY`, `CFG`.
- **Degrade-safe** — if Drive scope isn't granted, the generation check is skipped but the (primary) stale-push check still works from the sheet alone.
- **Fails loud** — if the check itself errors, it emails a "Sentinel could not run" alert; a silent guard is worse than none.
- **Known rare false-positive** — a day with genuinely zero due-today AND zero upcoming rows (only overdue carry-forward, or an empty list) reads as "stale." Accepted trade: cry-wolf occasionally rather than ever miss a real stale list. A future refinement (a push-written freshness stamp) removes it.

**Verified live:** test alert delivered 03 Jul 2026 **2:37:54 PM**; daily trigger armed. Editor test entry point: `testSentinelAlert`.

**Register entry:** `FOLLOWUPS_LIST_STALE` → detection: daily freshness of `Followups_Today` vs today's generated file → owner alert (email + ntfy) → manual fix: `push_followups_today.py --push`.

## Note on the Maintenance/SOP project precondition
The spec's precondition ("Maintenance project is created after `Diagnostics.gs` is live ≥1 real clinic day") has now **started its clock** — the first Diagnostics check is live as of 03 Jul.

## CHANGELOG
| v1.2 | 03 Jul 2026 (Session 53) | First live check: `FOLLOWUPS_LIST_STALE` (`Diagnostics.gs::checkFollowupListFresh`), armed + tested. Diagnostics module founded. |
| v1.1 | (prior) | As previously recorded (fault codes, detection architecture, fallback protocols). |
