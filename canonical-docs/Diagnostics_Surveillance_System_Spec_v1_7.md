# Diagnostics & Surveillance System Spec — v1.7 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward v1.6 unchanged (S124's Category 5, the fail-open requirement, the hardened verification standard). Session 125 adds: the **detector, actually built**; **five new fault codes**; **Category 6 — absence of coverage is not absence of events**, learned from a defect in the detector itself; and the **dual-key structural fix** that means this fault class can no longer cause an outage even when it recurs.

---

## §NEW-D — THE SILENT-FAILURE CLASS (S124) — *carried forward, unchanged*

`CALLHOOK_SECRET_MISMATCH_403` was named in Session 94, its detection rule was written down, and it was never built. It recurred within thirty-six hours and cost two clinic days of outcome data.

Three blind spots in one path: the receiver returns **403 before `raw_log()`**; the 403 path prints **nothing** to the journal; therefore the only evidence of 4,449 rejected deliveries lived in the **OpenLiteSpeed access log**, which no system reads.

> **CATEGORY 5 — REJECTED-AT-THE-DOOR.** Any component that authenticates an inbound request must *count and log its rejections*. A gate that refuses silently is indistinguishable from a world that never called. Silence is not evidence of health; it is evidence of nothing.

**Status: IMPLEMENTED (S125, D163).** See §NEW-I.

---

## §NEW-E — DETECTOR: `CALLHOOK_SECRET_MISMATCH_403` — **BUILT (S125)**

**Lane: ASSISTED (Lane 2).** Never auto-fixed — the procedure touches a secret and, potentially, the MyOperator panel. Detect + escalate only.

Both parts of the S124 spec are now built, though not exactly as specced.

**Part 1 — make the receiver speak.** Built as `call_hook_capture.py` v2 (D163). The gate now writes each refusal to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** returning 403. Metadata only: timestamp, reason, masked key label, key length, source IP, method, path. Never the key, never the body. Throttled: full detail for the first **500** refusals per day, then **1 in 100** — a retry storm stays visible without being able to fill the disk. **The 403 response body and status are unchanged**, as required; MyOperator's behaviour depends on them.

*Deviation from spec:* `/healthz` was **not** built. A JSON reject log on disk is strictly more useful than an in-process counter — it survives a worker respawn, which an in-memory counter does not, and a respawn is precisely the event at the centre of this fault. If a `/healthz` endpoint is wanted later for the daily health report, it should read the reject log, not a counter.

**Part 2 — make the watchdog look.** Built as `callhook_watchdog.py` v1.0, `/root/wa/call-hook/callhook_watchdog.py`. Read-only: it opens the access-log glob and the raw-log directory, and writes nothing unless `--state` is passed. It cannot take the clinic down. Offline selftest, 37 checks. Keys are handled only as opaque `key_<md5[:6]>` labels; there is no flag to unmask.

**Not yet scheduled.** Two defects must land first (§NEW-H). Note that it exits **1** on WARN, so a naive `OnFailure=` will fire all day on already-fixed 403s.

---

## §NEW-F — FAIL-OPEN REQUIREMENT FOR HUMAN-FACING CHECKS (D156) — *carried forward, unchanged*

A detection or verification mechanism that sits on a human's critical path is not a safety feature — it is a new failure mode. Any check that can block a staff action must have a **terminal state**, **fail open** into it, and be **reconciled in the background** afterwards. A check that fails *closed* is acceptable only where it has **measured** a negative, not where it merely failed to observe.

---

## §NEW-G — VERIFICATION STANDARD (hardened, S124) — *carried forward, unchanged*

> A fix to a webhook, secret, timer, or gate is verified only after (a) one real call, **AND** (b) a re-check at least one hour later on the same clinic day.

**An incident is not closed by a successful test. It is closed by a successful re-test.**

---

## §NEW-H — CATEGORY 6: ABSENCE OF COVERAGE IS NOT ABSENCE OF EVENTS (S125)

The detector built to correct an absence-of-evidence error **commits the same error.**

`callhook_watchdog.py` folds the access log into counts. If the log does not span the date it was asked about — rotation, retention, a glob that misses the file, a permissions error on one path — `collect()` returns zeros. `evaluate()` then reports **CRITICAL**:

> *"No raw log, and no requests of any kind in the access log. MyOperator is not delivering at all — check the panel subscription, not the secret."*

A confident, specific, wrong diagnosis, pointing the reader **away from** the real cause. Reproduced in the sandbox by feeding it an empty log for 06-Jul.

> **CATEGORY 6 — COVERAGE.** Any check that reasons from the *absence* of records must first prove that it was *looking somewhere records would have been*. A zero must be distinguishable from a blind spot. Where it cannot be, the check must refuse to answer (exit ERROR), never guess.

**Required fix, before the watchdog is scheduled:**
- Assert that at least one parseable `mo-callhook` line exists in the access log whose timestamp falls on `target_date`, **or** that the log's time span brackets `target_date`. If neither holds, exit **3 (ERROR)** with *"access log does not cover \<date\>"* — do not evaluate.
- Until this lands, `--date` on any past day is untrustworthy, including for settling the open question of what happened on 06–07 Jul.

**Second required fix — encoding normalisation (D165).** `mask_key()` hashes the raw `?key=` string as it appears on the wire. The Go client percent-encodes `@` as `%40`; Flask decodes it before the receiver compares. **The same key therefore labels differently in the two tools** — `key_271f88` in the access log, `key_db8972` in `.env`. This produced an hour of alarm on 08 Jul, and could produce a false `CALLHOOK_MULTIPLE_KEYS` on a single subscription. Fix: `urllib.parse.unquote()` before hashing, consistently, everywhere.

---

## §NEW-I — THE STRUCTURAL FIX: DUAL-KEY ACCEPTANCE (D162, D163, D164)

Detection was never sufficient. The fault could still cause an outage; it would simply be found sooner. Session 125 also removed its ability to cause one.

**D162 — dual-key acceptance.** A secret that lives in two places must be rotatable without a synchronised cutover. The receiver accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared in constant time (`hmac.compare_digest`). A stale worker and a fresh worker both work. The panel and the VPS may disagree for as long as they like. The disagreement surfaces as a **WARN line naming the key in use**, instead of as a receptionist reporting stuck tiles.

**Why the disagreement was dormant, and why that is the heart of the fault.** `gunicorn -w 1` with no `--preload`: the worker reads `.env` **once, at import**. An edit to `.env` therefore takes effect at the next worker respawn — an unpredictable moment, hours or days later, with no restart, no reboot, and no journal entry to connect cause to effect. On 06 Jul that respawn came at 13:41.

> **Generalise this.** Any shared secret read at import, in a single-worker process, is a mine with an unknown fuse. `WA_APPROVE_KEY` and `FU_UPLOAD_SECRET` have the same shape and should get the same treatment when they are next touched.

**D163 — refusals are recorded before they are refused.** The implementation of Category 5.

**D164 — `.env` is never edited by line number.** `sed -i '<N>s|…'` produced a 61-character run-on line: the correct key with ~49 characters of the shell command welded onto it. Use `awk` + `ENVIRON`, or `printf` to append. WinSCP transfers of `.env` and `.py` must be **Binary**, never Text — Text mode appends `\r` to every line, the same class of invisible-trailing-character fault. The receiver now emits a startup WARNING if its secret contains whitespace, an `=`, or exceeds 40 characters.

---

## FAULT CODES — `call-hook` family (S125)

| Code | Severity | Meaning | What to do |
|---|---|---|---|
| `CALLHOOK_SECRET_MISMATCH_403` | CRITICAL (2) | Rejections within the last 30 minutes. Failing **now**. Duration data is being lost. | Compare key labels — **normalised**. Align the VPS to the panel. Never print the key. |
| `CALLHOOK_RAWLOG_MISSING` | CRITICAL (2) | Clinic day, past 11:00 IST, no raw log. The detail line distinguishes *arriving and refused* / *not delivering at all* / *accepting and not writing*. | Read the detail line before acting; the three cases have different fixes. |
| `CALLHOOK_403_EARLIER_TODAY` | WARN (1) | Rejections today, none in the last 30 min. Signature of a fault already fixed. | Confirm the fix time. Re-check ≥1h later (§NEW-G). |
| `CALLHOOK_MULTIPLE_KEYS` | WARN (1) | More than one distinct key delivered today → more than one webhook subscription. | **First rule out the encoding trap (D165).** Then check the panel. Escalate to Lokesh. |
| `CALLHOOK_NO_ACCEPTED_TODAY` | WARN (1) | Raw log has lines; access log shows zero 200s. Timestamps disagree. | Do not trust either source until reconciled. |
| `CALLHOOK_SILENT` | WARN (1) | Nothing at all today. **Explicitly not a pass.** | Place one dialler call to disambiguate. |

Exit codes: **0** OK · **1** WARN · **2** CRITICAL · **3** the watchdog itself could not run.

**Procedure (for the Fault → Action Register)** — steps 1–6 as in v1.6, with these amendments:

- **Step 0 (new).** Run `callhook_watchdog.py`. It answers steps 1–4 in one command, without printing a secret. Trust it for *today*; do not trust `--date` on past days until §NEW-H lands.
- **Step 4 (amended).** Compare keys by hash, never by printing — and **`unquote()` before hashing**. The access log holds the wire form (`%40`); `.env` holds the literal (`@`). Comparing them raw will show a mismatch that does not exist, or hide one that does.
- **Step 6 (unchanged).** Prefer aligning the VPS to the panel. Use `awk` + `ENVIRON`. Assert exactly one matching line, only the value changed, identical line count. Restart. Re-verify — and **re-verify again an hour later**.
- **Step 7 (new).** After any `.env` edit, read the startup line from the journal and confirm the key label is the one you intended. The receiver prints it. Do not skip this: on 07 Jul a fix was declared verified by probing the server with the key the session had just written to it, which of course returned 200.

**Escalate to Lokesh only if** the panel is sending a key nobody recognises (after normalisation), or a second webhook subscription genuinely exists.

---

## SURVEILLANCE LAYERS (updated)

- VPS service watchman (S61) — Lane-1 responder.
- Timer-freshness family (S62) — **still unarmed.**
- Apps Script sentinel (v1.2) — follow-up-list freshness.
- Daily health report (S63) — positive confirmation, 08:00.
- **Rejected-at-the-door (Category 5) — IMPLEMENTED in the receiver (D163).** Reject log live 08 Jul 14:49.
- **`callhook_watchdog.py` (Category 5 + 6) — BUILT, manual runs only.** Blocked on two defects before scheduling.

## Growth path (next diagnostics sessions, one at a time)

1. **Fix the two watchdog defects (§NEW-H), then schedule it.** It currently gives a wrong, confident answer for any date its log does not cover.
2. Arm the timer-freshness checker (S62's parked step).
3. Build the maintenance jobs (disk → token-age → log-prune → backup), feeding the report. **Add reject-log pruning** to that family.
4. Then Patient_Master mirror freshness, Call_Feed freshness, revenue reconciler freshness.
5. **Empty-transcript guard** — 3 of 32 transcripts on 06-Jul were 0 bytes. They surface as AI "Unclear" verdicts when they are recording/transcription faults. Count them; alert on a rising rate.
6. **Apply D162 to the other shared secrets** — `WA_APPROVE_KEY`, `FU_UPLOAD_SECRET`. Same shape, same mine, same fuse.

## CHANGELOG

| v1.7 | 08 Jul 2026 (Session 125) | Detector **BUILT** (`callhook_watchdog.py` v1.0, read-only, 37/37 offline) and Category 5 **IMPLEMENTED** in the receiver (`call_hook_capture.py` v2, reject log, 43/43 offline, live 14:49:12). **Five new fault codes.** New **Category 6 — absence of coverage is not absence of events**, learned from a defect in the detector itself: it reports "MyOperator is not delivering at all" when its own access log simply doesn't reach the date. New **§NEW-I structural fix**: dual-key acceptance (D162) means a panel/VPS secret disagreement can no longer cause an outage, only a WARN line. `.env` never edited by line number (D164). Key labels must be encoding-normalised before comparison (D165) — wire `%40` and literal `@` hash differently and nearly cost a night. `/healthz` **deliberately not built**: a disk reject log survives the worker respawn that an in-memory counter does not, and the respawn is the whole fault. |
| v1.6 | 08 Jul 2026 (Session 124) | `CALLHOOK_SECRET_MISMATCH_403` **recurred in 36 hours, undetected** — 4,449 silent 403s. New **Category 5: rejected-at-the-door**. Detector **specced** (§NEW-E) and made the top diagnostics task. New **fail-open requirement** for any check on a human's critical path (D156). **Verification standard hardened**: one real call AND a re-check ≥1h later, same clinic day. +empty-transcript guard on the growth path. |
| v1.5 | 04 Jul 2026 (Session 63) | Response model locked (two lanes, D112; watchman = Lane-1 responder, D113; Fault→Action Register = brain, D114). Daily health report BUILT + LIVE (D115). Maintenance-job family DESIGNED not built. |
| v1.4 | 04 Jul 2026 (Session 62) | Timer-freshness family (Category 2). |
| v1.3 | 04 Jul 2026 (Session 61) | VPS service watchman. |
| v1.2 | 03 Jul 2026 (Session 53) | First live check: `FOLLOWUPS_LIST_STALE`. |
| v1.1 | (prior) | Fault codes, detection architecture, fallback protocols. |
