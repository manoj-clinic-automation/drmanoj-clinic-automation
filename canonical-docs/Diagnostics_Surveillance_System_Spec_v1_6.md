# Diagnostics & Surveillance System Spec — v1.6 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward v1.5 unchanged (S63 response model, daily health report, maintenance-job family). Session 124 adds: the **`CALLHOOK_SECRET_MISMATCH_403` recurrence and why nothing detected it**, the **detector spec** (now the top diagnostics task), a new **fail-open requirement** for any check that sits near a human's workflow, and a hardened **verification standard**.

---

## §NEW-D — THE SILENT-FAILURE CLASS (S124, learned the hard way)

`CALLHOOK_SECRET_MISMATCH_403` was named in Session 94, its detection rule was written down, and it was never built. **It recurred within thirty-six hours** and cost two clinic days of outcome data.

**Why nothing noticed. Three separate blind spots, all in one path:**
1. `call_hook_capture.py` returns **403 before `raw_log()` is called**. A rejected delivery writes no raw-log line.
2. The 403 path prints **nothing** to the journal (`log()` is never reached).
3. Therefore the *only* evidence of 4,449 rejected deliveries across three days lived in the **OpenLiteSpeed access log**, which no system reads.

Absence of `call_hook_logs/YYYY-MM-DD.jsonl` is **ambiguous**: it means "MyOperator sent nothing" *or* "MyOperator sent everything and we rejected it". Those are different faults with different fixes, and the file cannot distinguish them.

**The generalisation — a new detection category:**

> **CATEGORY 5 — REJECTED-AT-THE-DOOR.** Any component that authenticates an inbound request must *count and log its rejections*. A gate that refuses silently is indistinguishable from a world that never called. Silence is not evidence of health; it is evidence of nothing.

---

## §NEW-E — DETECTOR: `CALLHOOK_SECRET_MISMATCH_403` (SPEC — build next)

**Lane: ASSISTED (Lane 2).** Never auto-fixed — the procedure touches a secret and, potentially, the MyOperator panel. Detect + escalate only.

**Two parts, both small.**

**Part 1 — make the receiver speak.** In `call_hook_capture.py`, the secret gate must increment an in-process counter and `log()` the rejection (masking the key), and expose a `/healthz` returning `{ok, rejected_403, accepted, last_accept_ist, last_reject_ist}`. Rate-limit the log line so a retry storm cannot fill the journal. **The 403 response body and status must not change** — MyOperator's behaviour depends on it.

**Part 2 — make the watchdog look.** Two checks, both cheap:
- **Freshness:** on a clinic day, if `call_hook_logs/<today>.jsonl` does not exist (or has not grown) **by 11:00 IST**, alert.
- **Rejection:** if `/healthz` reports `rejected_403 > 0` since the last check, alert **immediately** — this is unambiguous and fires within minutes of a key mismatch, long before the freshness check would.

**Alert copy must name the ambiguity:** *"No call webhook bodies today"* is a different message from *"Call webhook deliveries are being REJECTED (403) — the panel's key does not match the receiver's."*

**Procedure (for the Fault → Action Register):**
1. `ls -lt /root/wa/call-hook/call_hook_logs/ | head -3` — is today's file present and growing?
2. `grep -h "mo-callhook" /home/*/logs/*access* | sed -E 's/key=[^& ]+/key=<masked>/g' | tail -20` — is MyOperator delivering, and with what status?
3. Counts by date + status: pipe through `sed -E 's/.*\[([0-9]{2}\/[A-Za-z]{3}\/[0-9]{4}).*" ([0-9]{3}) .*/\1 \2/' | sort | uniq -c` — this dates the onset.
4. Compare keys **by hash, never by printing**: md5 the decoded `?key=` from today's access log against the `.env` value; compare lengths too. Watch for URL-encoding (`%40` = `@`).
5. Local probe (writes nothing, no raw-log line): `curl --get --data-urlencode "key=$K" --data-urlencode "challenge=ping" http://127.0.0.1:8098/mo-callhook`.
6. **Prefer aligning the VPS to the panel over editing the panel** — whatever rewrites the panel cannot rewrite `/root/wa/.env`. Use the `awk`+`ENVIRON` recipe, then assert: exactly one matching line, only the value changed, identical line count. Restart. Re-verify.

**Escalate to Lokesh only if** the panel is sending a key nobody recognises, or a second webhook subscription exists.

---

## §NEW-F — FAIL-OPEN REQUIREMENT FOR HUMAN-FACING CHECKS (D156)

A detection or verification mechanism that sits on a human's critical path is not a safety feature — it is a new failure mode. The duration gate proved this: a vendor-side webhook fault stopped the clinic from recording what patients said, twice in three days.

**Rule.** Any check that can block a staff action must:
- have a **terminal state** (a "cannot determine" answer, reached by a clock anchored to the *event*, never to a page load or a poll start);
- **fail open** into that terminal state, recording the outcome as unverified rather than refusing it;
- and be **reconciled in the background** afterwards, where its failure costs nothing.

A check that fails *closed* is only acceptable where it has **measured** a negative (e.g. a call the system *observed* was never answered), not where it merely failed to observe.

---

## §NEW-G — VERIFICATION STANDARD (hardened)

Session 94 recorded the 403 outage as *"Verified end-to-end. Outage closed."* on the strength of **one call placed immediately after the fix**. The fix was dead seven minutes later; the panel had reverted.

> **A fix to a webhook, secret, timer, or gate is verified only after (a) one real call, AND (b) a re-check at least one hour later on the same clinic day.** An immediate success distinguishes nothing.

Corollary: **an incident is not closed by a successful test. It is closed by a successful re-test.**

---

## SURVEILLANCE LAYERS (updated)
- VPS service watchman (S61) — Lane-1 responder.
- Timer-freshness family (S62) — **still unarmed.**
- Apps Script sentinel (v1.2) — follow-up-list freshness.
- Daily health report (S63) — positive confirmation, 08:00.
- **Rejected-at-the-door (S124, Category 5) — SPECCED, NOT BUILT. Top task.**

## Growth path (next diagnostics sessions, one at a time)
1. **Build the `CALLHOOK_SECRET_MISMATCH_403` detector (§NEW-E).** It has now fired twice with zero machine detection.
2. Arm the timer-freshness checker (S62's parked step).
3. Build the maintenance jobs (disk → token-age → log-prune → backup), feeding the report.
4. Then Patient_Master mirror freshness, Call_Feed freshness, revenue reconciler freshness.
5. **Empty-transcript guard** — 3 of 32 transcripts on 06-Jul were 0 bytes. They surface as AI "Unclear" verdicts when they are recording/transcription faults. Count them; alert on a rising rate.

## CHANGELOG
| v1.6 | 08 Jul 2026 (Session 124) | `CALLHOOK_SECRET_MISMATCH_403` **recurred in 36 hours, undetected** — 4,449 silent 403s. New **Category 5: rejected-at-the-door** (a gate that refuses silently is indistinguishable from a world that never called; the receiver 403s before it raw-logs and before it journals). Detector **specced** (§NEW-E) and made the top diagnostics task. New **fail-open requirement** for any check on a human's critical path (D156). **Verification standard hardened**: one real call AND a re-check ≥1h later, same clinic day — an incident is closed by a successful *re*-test. +empty-transcript guard on the growth path. |
| v1.5 | 04 Jul 2026 (Session 63) | Response model locked (two lanes, D112; watchman = Lane-1 responder, D113; Fault→Action Register = brain, D114). Daily health report BUILT + LIVE (D115). Maintenance-job family DESIGNED not built. |
| v1.4 | 04 Jul 2026 (Session 62) | Timer-freshness family (Category 2). |
| v1.3 | 04 Jul 2026 (Session 61) | VPS service watchman. |
| v1.2 | 03 Jul 2026 (Session 53) | First live check: `FOLLOWUPS_LIST_STALE`. |
| v1.1 | (prior) | Fault codes, detection architecture, fallback protocols. |
