# INCIDENT — F‑44 · Recording‑gap detectors mislabelled missed calls as "never recorded"

**Dr. Manoj Agarwal Clinic, Bareilly.** Session 145 · 14 Jul 2026.
**Fault code:** F‑44. **Severity:** data‑quality (no outage; no data loss). **Status:** RAISED + FIXED same session.

---

## 1. Symptom (owner‑reported)

The 21:30 digest of 13 Jul flagged a "missing recording." The call behind it — 09:37, an incoming number, "talked 40s, no recording" — was shown in the MyOperator panel as a **missed call**. A missed call correctly has no recording, so the alert was a false alarm. The owner asked whether this mislabelling occurred anywhere else.

## 2. Cause

MyOperator counts a call's clock from the first ring — menu time, hold, and ringing all count — so a **missed** call can still show tens of "talk" seconds. Two Python consumers judged "a real conversation happened" from those seconds (and the customer leg's `result`) while **ignoring MyOperator's own top‑level `status`** (`bridged` / `missed` / `voicemail`), which the receiver stores truthfully. Contained to exactly two files:

- **`flag_investigator.py`** — `is_lost_candidate()` never read `status`; `diagnose()` routed provider Search‑Logs `status "2"` (missed) into the `never_recorded` bucket. This inflated the "42 never‑recorded / 7 days" count and raised a **false escalate‑to‑Lokesh** flag.
- **`daily_digest.py`** — `classify_pending()` produced "⚠ talked Xs, no recording" on duration alone, with no `status` check. This was the exact line the owner saw.

**Verified clean (no change):** the receiver (`call_hook_capture.py`) stores raw truth; the archiver only pulls `status "1"` + filename (missed calls never enter `Call_Recordings`); transcription and the verdict layer only ever see recorded calls, so a missed call cannot reach them; all Apps Script already gates on `status == "bridged"`. The "no content" verdicts (`cant_communicate`) are genuinely connected calls with no substance — an accurate label, not this fault.

## 3. Fix

- **`flag_investigator.py` v1.1 → v1.2** (md5 `a9baa6ca22055bb188d5c65b93c47ba1`, 51/51 selftest): `is_lost_candidate()` drops any row whose top‑level `status` is `missed`/`voicemail`; `diagnose()` adds a `missed_no_conversation` outcome for Search‑Logs `status "2"` and restricts `never_recorded` to `status "1"` + blank filename (the genuine provider gap).
- **`daily_digest.py` v1.3 → v1.4** (md5 `f7e05ed2a79670667fda170f3b70b9d1`, 75/75 selftest): `classify_pending()` labels a `missed`/`voicemail` row "missed — no recording expected" (not an alert) before the duration checks.

Both installed via WinSCP → md5 match on VPS → `py_compile` → selftest, per D188. No cron change (the scripts are already scheduled; the next run uses the new files).

## 4. Re‑baseline result (proof)

After install, the Investigator's results file was backed up (`…pre_f44.json`) and rebuilt with v1.2:

- **`never_recorded_7d`: 42 → 0** · **`escalate_lokesh`: True → False**.
- Breakdown of the old 42 (from the backup's `detail` text): **42 / 42 were `missed (status 2)`; 0 were genuine `status 1` connected‑no‑recording.**
- **Conclusion:** the entire "42 never‑recorded" figure was missed calls. MyOperator was not losing recordings; the detector was miscounting. **The standing "take the 42 to Lokesh" action is VOID — a false alarm, no provider conversation required.**

## 5. Timeline

| Time (IST, 14 Jul) | Event |
|---|---|
| — | Owner reports the confusing 21:30 digest line (missed call shown as missing recording). |
| S145 | Full‑repo sweep: root cause isolated to two consumer files; rest of the call chain verified clean. |
| S145 | `flag_investigator.py` v1.2 built offline (51/51), installed, md5‑verified on VPS. |
| S145 | Investigator re‑baselined: 42 → 0; the 42 proven to be 42 missed calls. |
| S145 | `daily_digest.py` v1.4 built offline (75/75), installed, md5‑verified, dry‑run clean. |

## 6. Decisions minted

- **D244** — recording‑gap detection keys off the provider's top‑level `status` (bridged vs missed/voicemail), not talk‑duration alone. A missed call is never a "lost recording."

## 7. Lesson

A call's duration is not its talk time — MyOperator's clock includes ring/hold. The connected‑vs‑missed truth is the top‑level `status`, which the receiver already stores; the Apps Script already keyed on it, but two Python consumers didn't. **When a detector's number looks alarming, check that its input signal means what the detector assumes it means** — here, "40 seconds" was ring time on a missed call, not a conversation.

---

**END OF INCIDENT F‑44.**
