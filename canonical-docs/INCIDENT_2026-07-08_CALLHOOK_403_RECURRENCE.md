# INCIDENT REPORT — `CALLHOOK_SECRET_MISMATCH_403` (RECURRENCE) — **v2**
**Dr. Manoj Agarwal Clinic · Bareilly · 08 July 2026 · Sessions 124 + 125 · Decisions D159, D162–D165**

> **v2 supersedes v1 (Session 124).** v1 was written before the detector existed. Session 125 built the detector, read the access log with it, and recovered evidence that **corrects two findings and closes one open question**. Changed material is marked **[S125]**. Where v1 was wrong, v1's text is quoted before it is corrected — the error is part of the record.

| | |
|---|---|
| **Fault code** | `CALLHOOK_SECRET_MISMATCH_403` (minted S94; detector built S125) |
| **Lane** | ASSISTED (Lane 2) — detect + escalate; no auto-fix |
| **Severity** | 🔴 High — staff could not record any follow-up outcome |
| **Onset** | 06 Jul 2026, ~13:41 IST |
| **Detected** | 08 Jul 2026, ~10:00 IST — **by a receptionist**, not by any system |
| **Resolved** | 08 Jul 2026, 10:28:32 IST (service restart); first accepted delivery 10:29:17 |
| **Time to detect** | ~44 hours |
| **Time to fix after diagnosis** | ~6 minutes |
| **Data loss** | Two clinic days of follow-up outcome data (see §5) |
| **Recurrence prevented** | **[S125]** Dual-key acceptance (D162) + rejection logging (D163), live 08 Jul 14:49:12 |

---

## 1. Symptom

Staff dashboard follow-up tiles stuck on **"⌛ Checking the call… the outcome unlocks once it connects"** indefinitely, after genuinely connected calls, **surviving a page refresh**. The outcome dropdown never unlocked, so no outcome could be filed.

## 2. Timeline

- **(unknown date, before 06 Jul)** — **[S125]** a lost newline merges `CALLHOOK_SECRET` and `FU_UPLOAD_SECRET` onto one 61-character line in `/root/wa/.env`. **The clinic does not break.** The running gunicorn worker already holds the correct secret in memory. The fault is real and dormant.
- **06 Jul 13:41** — **the worker respawns and re-reads `.env`.** Last accepted webhook delivery. 111 × HTTP 200, then 1,074 × HTTP 403. **← WINDOW 1 OPENS.** No restart, no reboot, no journal entry.
- **07 Jul** — 2,744 × 403.
- **07 Jul 16:25:09** — **[S125]** `.env` backed up immediately before the S94 repair. **That backup preserves the 61-character `CALLHOOK_SECRET` line, non-alphanumeric characters `@ _ _ =` in that order.** It is the only surviving artefact of the corruption. See §3.7.
- **07 Jul ~16:25** — `sed -i '17s|.*|CALLHOOK_SECRET=<new clean key>|'` **removes** the run-on and installs a fresh plain-alphanumeric key (Option B, chosen to drop the `@`). The panel is edited to match.
- **07 Jul 16:28:03** — `call-hook.service` restarted. **Four × 200 at 16:28–16:35. The fix works. ← WINDOW 1 CLOSES.**
- **07 Jul ~16:35** — 403s resume. **← WINDOW 2 OPENS.** The two ends have come apart again. **How, is still unknown.**
- **08 Jul 00:00–10:28** — 635 × 403, **zero** × 200. No `2026-07-08.jsonl`. *(v1 said 631; the watchdog's own count from the full access log is 635. **[S125]**)*
- **08 Jul ~10:00** — owner reports stuck tiles.
- **08 Jul 10:28:02** — **[S125]** last 403, per the access log, read independently by the watchdog.
- **08 Jul 10:28:32** — `call-hook.service` restarted with the realigned secret.
- **08 Jul 10:29:17** — first HTTP 200. `2026-07-08.jsonl` created. `Call_Durations` rows 101–107 written with real `bridged / answered / talk=37,23,26,15`.
- **08 Jul 13:53:58** — **[S125]** last accepted delivery before the S125 audit; 115 × 200 on the day.
- **08 Jul 14:49:12** — **[S125]** `call_hook_capture.py` v2 installed and live. Dual-key gate, rejection logging.
- **08 Jul 14:50:25** — **[S125]** deliberate keyless probe → 403 → **one line written to the reject log.** The blind spot is closed.

## 3. Diagnosis chain

Steps 1–6 as recorded in v1 and unchanged. Step 7 is **substantially revised**.

1. `call-hook.service` **up and healthy** — not a dead service.
2. **[S125 — CORRECTED]** v1 recorded: *"`/root/wa/.env` `CALLHOOK_SECRET`: 24 chars, alphanumeric, **exactly one line, no run-on**. **Not** the §94.1 `.env` corruption."*
   That inspection was performed on the morning of **08 Jul — after the 07 Jul 16:25 edit.** The backup taken immediately *before* that edit proves the line **was** corrupted: 61 characters, containing `@`, two underscores, and a stray `=`, with `strip()` changing nothing. **Both statements are true of their own moments.** The §94.1 corruption was real and was present on the VPS at least until 07 Jul 16:25.
   v1's own caveat was sound and should have been pressed harder: *"the initial `grep -c '^CALLHOOK_SECRET'` check was **useless** — the §94.1 damage appends junk *to* that line, so it still counts as one."*
3. No `2026-07-08.jsonl`. **Ambiguous by design** — the secret gate returns 403 **before** `raw_log()` is called, so a rejected delivery leaves no raw-log line and no journal entry.
4. **The web-server access log settled it.** `13.126.78.76`, `Go-http-client/2.0`, continuous `POST /mo-callhook?key=…` → **403**, 33-byte body — the exact length of the receiver's own `{"ok":false,"error":"forbidden"}`. MyOperator was delivering; we were rejecting.
5. Reverse-proxy config intact (`…/followup.dr-manoj.in/vhost.conf:126 → 127.0.0.1:8098`).
6. Local probe with the `.env` key: **200**. Keyless: **403**. The running process held the `.env` value.
7. **[S125 — REVISED]** v1 recorded: *"The panel's key was URL-encoded, decoding to 12 characters containing an `@` — the **old** secret, the exact one Session 94 rotated away from (Option B was chosen specifically to remove the `@`)."*
   **[S125]** The `callhook_watchdog.py` run at 14:11 on 08 Jul, reading the full access log, reports:

   ```
   access log : 115 accepted (200) / 635 rejected (403) / 0 other
   keys seen  : key_271f88 (115 ok / 635 rejected)
   ```

   **One single key label, carrying both the rejections and the acceptances.** MyOperator sent the identical string across all 750 requests. Nothing about the sender changed at 10:28 — only the value on the VPS did. `CALLHOOK_MULTIPLE_KEYS` did not fire, and it would have.

## 3.7 — **[S125]** THE `7e17f7` ANOMALY, RESOLVED

The frozen Session-125 window had established that `.env` held a value hashing to `key_7e17f7` before the 07-Jul 16:25 edit — a label matching nothing MyOperator has ever sent. Two hypotheses: a genuine third key (a fourth actor in the file), or run-on corruption from `sed -i '17s'`.

Read-only inspection of `/root/wa/.env.bak_20260707_162509`, printing only hashes and non-alphanumeric characters:

```
raw      key_7e17f7  len=61
stripped key_7e17f7  len=61
non-alnum chars present: @__=
```

`strip()` changes nothing, so it is **not** a trailing-whitespace smudge. The value is 61 characters where the key is 12. It contains the `@` — so the key itself is in there — plus two underscores and a stray `=`, the shape of another `VAR_NAME=` welded onto the end.

**Verdict: not a third key. Not a fourth actor.** It is the correct 12-character `@` key with a second environment variable run onto the end of it.

**[S125 — and this identifies which variable.]** KB v1.48 §94 already records the answer, and it reconstructs to the byte. The §94.1 damage was *a lost newline* that merged `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment. Test:

```
12 ("@" key)  +  17 ("FU_UPLOAD_SECRET=")  +  32 (alphanumeric fragment)  =  61
non-alphanumeric characters, in order:  @ _ _ =      observed:  @__=
```

The two underscores are the ones in `FU_UPLOAD_SECRET`. The `=` is its assignment. The `@` precedes both, exactly as it must if the old key came first. **Exact match, in order.** (KB §94 also notes that a *second, clean* `FU_UPLOAD_SECRET` on the next line was the one actually in force — last-definition-wins — which is why only calls broke and the follow-up upload catcher kept working.)

### **[S125 — CAUSAL DIRECTION CORRECTED]**

The `sed` did **not** create the run-on. **It removed it.**

v1 of this report stated the fix was made *"**not** `sed` by line number, which is what created §94.1's run-on line."* The parenthetical is wrong. KB §94 records the S94 fix as `sed -i '17s|.*|CALLHOOK_SECRET=<new clean key>|'` — a whole-line replacement that *deleted* the run-on junk and installed a fresh plain-alphanumeric key (Option B, chosen to remove the `@`).

The run-on therefore **pre-dates** the `sed` and pre-dates Session 94. Its origin is a lost newline, cause unknown, still unknown. The backup at 07-Jul **16:25:09** was taken three minutes before the `call-hook.service` restart at **16:28:03** that v1 identifies as the S94 fix — so the backup captures the *pre-fix* state, and that state is the corrupted line. Every observation is consistent.

**This correction was itself produced by exactly the discipline it corrects.** A routine secrets sweep of the cold kit matched on the string `FU_UPLOAD_SECRET` inside KB v1.48, in a paragraph nobody had re-read in fourteen sessions. The KB had the answer the whole time.

> The runbook is not evidence. Neither, it turns out, is the incident report. Re-derive from the data.

## 3.8 — **[S125]** THE ENCODING TRAP

The live `.env` value labels as `key_db8972` (12 chars, one `@`). The access log labels the delivered key as `key_271f88`. **These disagree, and both are correct.**

Two hypotheses were live, and the difference mattered enormously:

- **(A)** The Go client percent-encodes `@` as `%40`. The wire string is 14 characters and hashes differently from the 12-character literal. Benign.
- **(B)** `.env` and the running worker had **diverged again** since the 10:28 fix. Everything works because the worker holds the good secret in memory; the next respawn kills the clinic. A second dormant outage, armed.

Resolved by test, not assumption:

```
as-is key_db8972
quote key_271f88   ← matches the access log exactly
target: key_271f88
```

**(A).** `urllib.parse.quote()` of the `.env` value reproduces the access-log label. The file, the worker and the panel all agree. **[Decision D165 records the trap.]**

## 4. Root cause — **[S125: TWO DISTINCT OUTAGES, NOT ONE]**

This is the substantive revision. The 4,449 rejections are **not one fault**. They are two, with different causes, separated by four accepted deliveries on the evening of 07 Jul. v1 treated them as a single continuous event and therefore had to explain the whole span with one mechanism.

### Window 1 — 06 Jul 13:41 → 07 Jul 16:28. Cause: the run-on line, plus a dormant fuse.

`/root/wa/.env` held `CALLHOOK_SECRET=<12-char @ key>FU_UPLOAD_SECRET=<32-char fragment>` — 61 characters on one physical line, a lost newline of unknown origin, pre-dating Session 94. The receiver read that whole 61-character string as its secret. It could never match anything.

**But the clinic did not break when the line was corrupted.** `gunicorn -w 1` with no `--preload`: the worker reads `.env` **once, at import**. The corruption was **dormant** — real, and asleep — until a worker respawn re-read the file. That respawn came at **13:41 on 06 Jul**. No restart, no reboot, no journal entry. Nothing whatever to connect the effect to a cause that may have been days old.

### Window 2 — 07 Jul ~16:35 → 08 Jul 10:28. Cause: the panel and the VPS disagreed after the S94 fix.

At 16:25:09 on 07 Jul the `.env` was backed up; at ~16:25 `sed -i '17s|.*|CALLHOOK_SECRET=<new clean key>|'` replaced the corrupted line with a fresh plain-alphanumeric key (Option B, chosen to remove the `@`); at 16:28:03 the service restarted. The panel was edited to match. **Four deliveries returned 200, at 16:28–16:35.** The fix worked.

Then the 403s resumed and ran for eighteen hours, and on 08 Jul the panel was demonstrably sending the **old `@` key** — the pre-S94 secret.

So the two ends came apart again, some time after 16:35 on 07 Jul. **How is still unknown**, and this is where v1's conclusion — *"the panel reverted"* — remains the leading hypothesis and remains **unproven**. What can now be said:

- It is **not** a second webhook subscription, at least not one that was delivering on 08 Jul. `callhook_watchdog.py` saw **one** key label across all 750 requests; `CALLHOOK_MULTIPLE_KEYS` did not fire, and it would have.
- The VPS was not touched between 16:28 on 07 Jul and 10:28 on 08 Jul. The panel is therefore the only end that can have moved — *unless* the 16:28 panel edit never saved, and the four 16:28–16:35 successes were served by something else. That alternative has not been excluded.
- Settling it means re-reading the 06–07 Jul access logs, which requires the watchdog's coverage guard (§8) first, or the answer will be confidently wrong.

### What v1 got wrong, and why it matters

v1 §3.2 recorded the `.env` as *"exactly one line, no run-on — **not** the §94.1 corruption."* True of the morning of 08 Jul; false of 07 Jul 16:25. The inspection came *after* the repair.

v1 §6 stated the fix used `awk`, *"**not `sed` by line number, which is what created §94.1's run-on line**."* **The causal direction is inverted.** The `sed` was S94's *repair*; it deleted the run-on. The run-on came from a lost newline and pre-dates it. `awk`+`ENVIRON` is still the better instrument — it cannot mangle escapes and does not depend on a line number staying put — but it was chosen against a hazard that had not actually occurred.

v1 §4 concluded *"The VPS was correct throughout; the vendor panel was not."* The VPS was **not** correct throughout: for Window 1 it was the sole cause.

### The contributing cause — unchanged, and still the only one that matters

The receiver rejects **before** it raw-logs and **before** it journals. 4,449 rejections produced **zero** evidence anywhere the clinic's own systems look. The Session-94 detection rule for this exact fault code was written and never built.

> None of this was a careless-edit problem. Window 1 was a system that let a *dormant* corruption sleep for an unknown period and then fire at a moment no human action selected. Window 2 was a system in which two copies of a secret could drift apart with no alarm. Both were invisible for the same reason: a door that refuses people without saying so. **A perfect edit, applied to only one of the two places the secret lives, would have produced Window 2 exactly as it happened.**

## 5. Consequential damage

The duration gate (D77/D82) blocks the outcome dropdown until a `Call_Durations` row proves the call connected. No webhook → no row → **no staff member could file any follow-up outcome for two clinic days.** The recordings and `Call_Feed` still hold the truth of what happened; only the staff's own account of each call is missing.

## 6. Fix

**Immediate (S124, 08 Jul 10:28).** Aligned the VPS to the panel, not the panel to the VPS — whatever rewrites the panel cannot rewrite `/root/wa/.env`. Backup; decode the panel's key from the access log (never printed); rewrite only the value with `awk` + `ENVIRON` (**not** `sed` by line number); three guards before installing (exactly one matching line, only the value changed, identical line counts); `chmod 600`; restart; verify.

**Structural (S125, 08 Jul 14:49).** `call_hook_capture.py` **v2**:

1. **Dual-key acceptance (D162).** The gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared in constant time. A stale worker and a fresh worker both work. The panel and the VPS may disagree indefinitely without service loss.
2. **Previous-key WARN.** A delivery on the old key logs a line naming the masked label — the signal that one side of a rotation is unfinished. The warning that never existed.
3. **Rejections written down before they are refused (D163).** `call_hook_rejects/YYYY-MM-DD.jsonl` — timestamp, reason, masked key label, key length, source IP, method, path. No key, no body. Throttled: full detail for the first 500 refusals per day, then 1 in 100.
4. **Startup corruption sniffer (D164).** Warns if the secret contains whitespace, an `=`, or exceeds 40 characters.

Verification: 43/43 offline selftest on the VPS interpreter; AST diff proving `extract_record`, `upsert`, `_connect_store`, `raw_log` and six others byte-identical to v1; `file` and `grep -c $'\r'` clean; startup line `secret gate: ON  current=key_db8972  previous=(unset)`; live keyless probe → 403 → exactly one reject-log line.

**Detector (S125).** `callhook_watchdog.py` v1.0, read-only, reads the access log — the only place a rejected delivery is visible. Six fault codes. 37/37 offline selftest. On the VPS, run manually; not yet scheduled.

## 7. What changed as a result

- **D156** (S124) — the duration gate **fails open** when it cannot *measure* a call. A verification mechanism may never again stop a staff member from recording what a patient said. (`Dashboard.html` v18.19, deployed.)
- **D159** (S124) — VPS realigned to the panel; the clinic runs on the old 12-char `@` secret as a deliberate temporary trade.
- **D162** (S125) — dual-key acceptance is mandatory for any shared-secret gate. Generalises to `WA_APPROVE_KEY`, `FU_UPLOAD_SECRET`, and every future shared secret.
- **D163** (S125) — a gate must write down its refusals before it refuses. Implementation of Diagnostics Category 5.
- **D164** (S125) — `.env` is never edited by line number. WinSCP transfers Binary, never Text.
- **D165** (S125) — masked key labels must be encoding-normalised before comparison.
- **Diagnostics Spec v1.6 → v1.7** — Category 5 implemented; five new fault codes; §NEW-H on absence-of-coverage.
- **Verification standard hardened** (S124) — one real call **and** a re-check ≥1 hour later on the same clinic day. **An incident is closed by a successful re-test, not a successful test.**

## 8. Still open

- 🔴 **`CALLHOOK_SECRET` rotation, both ends.** The key is exposed in a chat transcript. Now a four-restart, zero-downtime procedure (D162). Choose a new key with **no `@`** — that removes the encoding trap at source, which was the right instinct in S94; only the execution was wrong.
- 🟠 **Watchdog defect 1 — the coverage guard.** If the access log does not span the requested date, the watchdog reports zero traffic and raises CRITICAL *"MyOperator is not delivering at all — check the panel subscription, not the secret."* A confident wrong diagnosis pointing away from the real cause. **The detector built to correct an absence-of-evidence error commits the same error.** Until fixed, `--date` on past days is untrustworthy — including for settling §4.
- 🟠 **Watchdog defect 2 — `unquote()` before hashing** (D165).
- 🟠 **115 vs 114.** On 08 Jul the access log recorded 115 accepted deliveries; the raw log holds 114 lines. One delivery returned 200 and wrote nothing. Off by exactly one. Benign explanations exist. Unexplained.
- 🟠 **What opened Window 2 is still unknown.** After the S94 repair worked (four × 200 at 16:28–16:35 on 07 Jul), the panel and the VPS came apart again within minutes. v1's suspicion of a **second webhook subscription** is **disproven for 08 Jul** — one key label across 750 requests, and `CALLHOOK_MULTIPLE_KEYS` would have fired. It is untested for 06–07 Jul. The competing hypothesis — that the 16:28 panel edit never saved, and the four successes were served by something else — has not been excluded either. **Do not close this as "the panel reverted" until one of them is shown.**
- 🟠 **Where the lost newline came from is unknown, and always was.** KB §94 records the run-on; nothing records how it got there. It may never be recoverable. The dual-key gate makes it survivable; the startup corruption-sniffer makes it loud; neither explains it.
- **Schedule the watchdog.** Only after the two defects land. Note it exits 1 on WARN, so a naive `OnFailure` fires all day on already-fixed 403s.
- **Re-verify across a full clinic day** per the hardened standard, on the morning of 09 Jul.

## 9. **[S125]** WHAT THIS INCIDENT WAS ACTUALLY ABOUT

Three properties turned two ordinary faults into two lost clinic days. **None of them is "someone was careless,"** and the report spent a session and a half believing otherwise.

**A secret that lives in two places, with nothing checking that they agree.** Window 2, entire. Change one end and the other is silently wrong.

**A change that takes effect at a moment no human action selects.** `gunicorn -w 1` with no `--preload`: only the worker reads `.env`, once, at import. Window 1's corruption slept — for an unknown period, possibly days — and then fired at 13:41 on 06 Jul when a worker happened to respawn. No restart. No reboot. No journal entry. Nothing at all to connect the effect to a cause that was already cold.

**A door that refuses people without saying so.** 4,449 refusals produced no evidence anywhere the clinic's systems look. Absence of `YYYY-MM-DD.jsonl` cannot distinguish *"nobody called"* from *"we rejected everybody."* This is the only property common to both windows, and the only reason either lasted more than an hour.

A receptionist found it, three clinic days later, by noticing that the tiles were stuck.

The fix was never "edit more carefully." It is that the two copies of a secret are now *allowed* to disagree, and that a door which refuses someone says so out loud.

### A note on how this report was corrected

v1 was written in good faith, from the runbook, hours after a two-day outage. It named the wrong instrument (`sed`), inverted a causal direction, and merged two faults into one. Every one of those errors was **discoverable in the project's own knowledge base**, in a paragraph written fourteen sessions earlier and never re-read.

It was found by a `grep` for leaked secrets, run mechanically over a backup archive, which matched on the string `FU_UPLOAD_SECRET` in a file nobody had opened.

> S124 §1 recorded: *"The runbook is not evidence. Re-derive from the data before building on a recorded number."* It was written about someone else's numbers. It applies here.

