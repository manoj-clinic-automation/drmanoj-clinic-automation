# INCIDENT REPORT — `CALLHOOK_SECRET_MISMATCH_403` (RECURRENCE) — v5 (CONSOLIDATED)
**Dr. Manoj Agarwal Clinic · Bareilly · 06–09 July 2026 · Sessions 124, 125, 126, 127**
**Decisions D159, D162–D165. Consolidated 09 July 2026, Session 131.**
**Supersedes v1, v2, v3 and v4 entirely. There is no addendum chain.**

> **Why this file exists.** This incident was stored as four files. v1 was superseded and kept.
> v2 held §1–§9. v3 held §10–§14 and opened with an instruction to append it to v2. v4 held
> §15–§16 and opened with an instruction to append it to v3. **The section numbers ran
> continuously from 1 to 16 across three files** — which is the tell: it was always one document,
> stored in pieces. **All sixteen sections are below, verbatim, in order.**
>
> **And v4's status line was wrong.** It read *"Status: MITIGATED, rotation in progress."* The
> rotation was **PARKED by the owner in Session 128** and has been parked since. A document that is
> confidently wrong about live state is worse than a document that is merely old. **Corrected
> below.**

---

## STATUS — CURRENT, AS OF SESSION 131

| | |
|---|---|
| **Fault code** | `CALLHOOK_SECRET_MISMATCH_403` (minted S94; detector built S125) |
| **Severity** | 🔴 CRITICAL (2) |
| **Outage status** | **CLOSED.** Resolved 08 Jul 2026, 10:28:32 IST. |
| **Recurrence prevention** | **LIVE.** Dual-key acceptance (D162) + rejection logging (D163), since 08 Jul 14:49:12. |
| **Rotation status** | ⏸️ **PARKED by the owner (Session 128).** Steps 1–2 done and verified; **Step 3 (MyOperator panel, Lokesh) OPEN; Step 4 BLOCKED on Step 3.** |
| **The one command** | **Step 4 must not be issued** until the panel is confirmed updated. Clearing `CALLHOOK_SECRET_PREV` while the panel still holds the old key refuses **every** delivery. See §16. |

> **A note on the `key_…` strings in this report.** They are **fingerprint labels** printed by the
> receiver's own log line (`secret gate: ON current=… previous=…`), **not secrets.** The report says
> so explicitly in §3.8. They are reproduced verbatim and must not be mistaken for key material, nor
> redacted out of the record by a future reader who has not read this note. *(D178 — a label must
> state what it contains.)*

---

## ORIGINAL FRONTMATTER (v2, Sessions 124 + 125) — preserved

| | |
|---|---|
| **Lane** | ASSISTED (Lane 2) — detect + escalate; no auto-fix |
| **Severity** | 🔴 High — staff could not record any follow-up outcome |
| **Onset** | 06 Jul 2026, ~13:41 IST |
| **Detected** | 08 Jul 2026, ~10:00 IST — **by a receptionist**, not by any system |
| **Resolved** | 08 Jul 2026, 10:28:32 IST (service restart); first accepted delivery 10:29:17 |
| **Time to detect** | ~44 hours |
| **Time to fix after diagnosis** | ~6 minutes |
| **Data loss** | Two clinic days of follow-up outcome data (see §5) |

> **v2 superseded v1 (Session 124).** v1 was written before the detector existed. Session 125 built the detector, read the access log with it, and recovered evidence that **corrects two findings and closes one open question**. Changed material is marked **[S125]**. Where v1 was wrong, v1's text is quoted before it is corrected — **the error is part of the record.**

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


---

## 10. **[S126]** THE SECOND RETRACTION — AND WHY THERE MUST NOT BE A THIRD

v1 of this report said the 61-character `CALLHOOK_SECRET` line was created by `sed -i '17s'` running past its closing delimiter. **Retracted in S125:** that `sed` was Session 94's *repair*; it removed the run-on.

v2 (and S125's correction throughout the project record) said the line was created by a **lost newline** merging `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment. **Retracted in S126.**

The forensic backup was opened and read — by name and value length, never by value:

```
/root/wa/.env.bak_20260707_162509   (1327 bytes, 29 lines, mode 600, mtime 07 Jul 16:25:09)

  CALLHOOK_SECRET          len=61
  FU_UPLOAD_SECRET         len=32
```

**`FU_UPLOAD_SECRET` is present, on its own intact line.**

A lost newline *merges* two lines: it consumes the second. That line survived. Therefore the 61 characters did not arrive by deletion of a newline. **They arrived by duplication — text inserted, nothing removed.**

### What is settled

The composition. `12 (the @ key) + 17 ("FU_UPLOAD_SECRET=") + 32 (the alnum value) = 61`, and the non-alphanumeric characters fall out in exactly the observed order `@ _ _ =`. `strip()` changes nothing. Not whitespace, not a third key.

### What is not settled

**The mechanism.** "Duplication" is a *class*, not a cause. A `sed` overrun, a stray append, a text editor, a botched heredoc paste — every one of them inserts without deleting. **The evidence distinguishes none of them.**

### Why this matters more than the answer would have

Three explanations have now been recorded for these 61 characters. Two were wrong. Both were plausible. Both were written with confidence, into an incident report and into a knowledge base. Both survived — one of them for two sessions and one incident report — **because nobody opened the file.**

The file was on the VPS the whole time. Reading it took thirty seconds.

**Recorded as D166: no cause is recorded unless the evidence distinguishes it from its rivals. `UNKNOWN` is a valid entry, and writing it takes more discipline than writing a guess.**

---

## 11. **[S126]** WINDOW 2 — NEARLY SETTLED, DELIBERATELY LEFT OPEN

`journalctl -u call-hook.service --no-pager | grep -i "secret gate" | tail -3` returned exactly three startup lines:

```
Jul 07 16:28:04   [call_hook_capture] secret gate: ON
Jul 08 10:28:33   [call_hook_capture] secret gate: ON
Jul 08 14:49:13   [call_hook_capture] secret gate: ON  current=key_db8972  previous=(unset) …
```

**Window 2 (07 Jul ~16:35 → 08 Jul 10:28) sits entirely inside the gap between the first two.**

`gunicorn -w 1`, no `--preload`: the worker reads `.env` once, at import. Across the whole of Window 2 the worker held **one secret in memory, unchanged**. `.env` could have been rewritten a hundred times and the worker would never have known.

Therefore **the VPS side could not have changed during Window 2.**

The four deliveries that returned 200 at 16:28–16:35 prove the worker's key matched what the panel was sending. The 403s that begin at ~16:35 prove it stopped matching. **The worker did not move. Something at the other end did.**

This is the strongest evidence yet for the panel-reverted hypothesis — and **it is not proof.**

- `tail -3` truncated the list. No respawn *appears* between `16:28:04` and `10:28:33`. None was *ruled out*.
- `grep "secret gate"` only catches respawns that printed that string. The v1 startup line is shorter, and it has not been established that it printed on every start path.

**Do not close §4's root-cause question on this.** It is an argument, not a demonstration, and it is one read-only command away from being either.

That command — widening the journal window and counting *every* service start, not only the ones matching a string — is now the cheapest route to an answer. It does **not** require the watchdog's coverage guard, and it does **not** depend on access-log retention. It was the expensive path in v2 §8 and it is no longer.

---

## 12. **[S126]** CORRECTIONS TO THIS REPORT'S OWN FACTS

- **The live `call_hook_capture.py` was 30,749 bytes, not 30,750.** Off by one, repeated across sessions. 690 lines. Final byte confirmed `\n` by `od -c`, so nothing was missing from the end — **the record was simply wrong.** The repo figure `31,100` came from the same record, so the long-quoted 350-byte delta was unverified in both directions. Measured: **351 bytes, 5 lines.**
- **`.env` and the running worker provably agreed throughout S126.** `cp -a` preserved the mtime: `.env` last written `08 Jul 10:28`; worker respawned `10:28:33`; `last 403` at `10:28:02`. One deliberate act. Confirmed three independent ways (startup label, wire label, mtime).
- **The 115-vs-114 raw-log gap is bounded.** At 21:20 it was **133 accepted / 132 lines**. Eighteen further deliveries, eighteen further lines, **offset still exactly one.** An ongoing defect widens; this did not. **One historical event, not a running mechanism.** Reclassify from "the receiver is silently dropping data" to "one anomalous 200 on 08 Jul, unexplained, low priority."
- **An unrecorded secret was in `.env` during the incident.** `ANTHROPIC_API_KEY len=111`, absent from the 07-Jul backup, therefore written between `07 Jul 16:25` and `08 Jul 10:28` — **inside the outage window** — by something nobody has identified. It is loaded into the environment of the gunicorn worker that serves this webhook. Mode 600. **Rotate; relocate; find the writer.** Whether it is related to this incident is unknown; that it appeared during it, unrecorded, in the file at the centre of it, is a fact worth staring at.
- **Six bytes between `.env` (1416) and the forensic backup (1327) are unaccounted** after `ANTHROPIC_API_KEY` (+130), two blank lines (+2), and `CALLHOOK_SECRET` 61→12 (−49) = +83. Probably line termination. Logged.

---

## 13. **[S126]** A LATENT FAULT OF THE SAME CLASS, FOUND ELSEWHERE

The clinic PC had **`core.autocrlf = true`**, with `.gitattributes` reading only `* text=auto`.

LF in the repository. **CRLF written into the working tree on every checkout.**

`git clone`, then a WinSCP upload in **Binary** mode — precisely what D164 mandates — would have delivered **701 carriage returns** into a `.py` on the VPS. Binary mode stops WinSCP from *adding* `\r`. It is powerless against `\r` that git wrote before WinSCP ever saw the file.

This never fired only because the working copy had arrived by some route other than a checkout.

**The rule was correct and insufficient.** Closed at source: `core.autocrlf false` (repo-local) and `*.py text eol=lf` in `.gitattributes`, which travels with the repo and overrides any user's configuration. Recorded as **D167: a control that guards one path into a hazard is not a control on the hazard.**

The same sentence describes the original incident. A gate that refuses silently is indistinguishable from a world that never called; a transfer rule that guards one tool is indistinguishable from safety, until a second tool writes the same byte.

---

## 14. **[S126]** STATUS

**The rotation has not started.** `.env` was not written. Nothing was restarted. `previous=(unset)`.

`call_hook_capture.py` on disk was replaced at 21:55 (31,490 bytes, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43 selftest on the installed file), by candidate path and atomic `mv`, never by overwriting the live file (**D168**). **The running worker still executes the pre-21:55 bytes.** The new file loads at the next respawn, which is rotation step 1 — the same dormancy that caused this incident, this time induced deliberately, understood, and with a chosen resolution time.

The 12-character `@` key remains exposed in a chat transcript. **That is why rotation is item 1.**

---

**END OF INCIDENT ADDENDUM v3 (S126). §14 is the last section. If §14 is absent, this file is truncated.**


---

## 15. **[S127]** THE ROTATION MOVES — STEPS 1 AND 2

Two sessions were convened to rotate the exposed key and both spent themselves on documentation. This one rotated it halfway, verified each half on live traffic, and stopped exactly where stopping is safe.

### Step 1 — 08 Jul 2026, 23:38:00 IST

`CALLHOOK_SECRET_PREV` appended to `/root/wa/.env` **equal to** `CALLHOOK_SECRET`, by `printf`, never `sed` (D164). Backup: `.env.bak_s127_pre_rotation_20260708_232229`, mode 600.

`.env` then held the same key twice. **Whichever key the panel sent, the gate accepted it — on `CALLHOOK_SECRET` or on `CALLHOOK_SECRET_PREV`, identical values. No mismatch this restart could produce.** That is what made a restart at 23:30, with no vendor reachable, a safe act rather than a gamble.

Pre-restart gates on the installed file, all green: `ASCII text executable` · CR `0` · **31,490 bytes / 701 lines / md5 `beafccafbf7e81aa5f2736be939b2bbb`** · `py_compile` clean · **43/43 selftest** · `__pycache__` cleared.

The journal returned a **fresh** timestamp:

```
Jul 08 23:38:00  [call_hook_capture] Phase B receiver v2 (dual-key).
Jul 08 23:38:00  secret gate: ON  current=key_db8972  previous=SAME AS CURRENT
                 (rotation not started; harmless)
Jul 08 23:38:00  Listening at: http://127.0.0.1:8098
Jul 08 23:38:02  connected to 'Call_Durations' — 139 rows known
```

**This is the moment the v2 dual-key code first executed.** It had been on disk since 21:55 that evening, dormant inside a worker that imported at `14:49:13` and would never notice the swap. That dormancy is the *precise mechanism* of this incident — a change taking effect at a moment no human action selects. Here it was induced deliberately, understood, held for two hours, and discharged at a chosen time with a validated rollback in hand.

**No verification request was sent to the server.** Sending it the key we had just written to it would have proved only that we could read our own file. **The startup line is the evidence.**

The chat froze immediately afterwards. **Nothing was lost, because nothing had been trusted to the chat.**

### Recovery — 09 Jul, morning

Nine hours of real clinic traffic had passed unattended.

- Service `active`; PIDs **867880 / 867881** — the identical master and worker that booted at 23:38. **No respawn.**
- `call_hook_logs/2026-07-09.jsonl` present, 62,761 bytes, last written 08:42. Deliveries arriving and accepted.
- `call_hook_rejects/2026-07-09.jsonl` **absent.** Not one refusal at the door.
- **58** journal lines in the window; **0** deliveries on the previous key — expected, both variables being identical.

### A `0` that meant nothing — recorded because it is this incident in miniature

`journalctl --since "23:30 yesterday"` printed `Failed to parse timestamp` and emitted **nothing**. `grep -c` then counted the `PREVIOUS key` lines in that nothing and returned **`0`**.

A reassuring number, produced by a check that had not run.

**This is the watchdog's own coverage defect** (v2 report §8, backlog item 4a) — *zero lines read as zero traffic* — reproduced by hand, in a shell, by the person who wrote the backlog item. It was caught only because the count was re-run with a `wc -l` coverage guard in front of it.

> **A check that cannot fail is not a check.** Absence of coverage is not absence of events. This is the same property, in a third costume, that let 4,449 refusals pass unseen.

### Step 2 — 09 Jul 2026, 09:05:58 IST

Executed by `rotate_callhook.sh install`, not by hand (**D171**).

New key generated **on the VPS**: `openssl rand -hex 12` → 24 hex characters. **No `@`. Nothing that percent-encodes.** The **D165 encoding trap is removed at source** — the same instinct S94 had, with an execution that survives it.

Eleven guards, all green: backup `cmp`-verified byte-identical · key 24 chars · hex-only charset · differs from old · candidate built by `awk`+`ENVIRON` · line count unchanged (33) · CR `0` · exactly one `CALLHOOK_SECRET` line · exactly one `CALLHOOK_SECRET_PREV` line · **exactly two diff lines** (one out, one in) · variable names identical.

The rollback point was revalidated with `cmp` **at the instant before** the atomic `mv` destroyed the file it would roll back to (**D168**). *A backup you have not compared at the moment of use is a belief about the past.*

```
secret gate: ON  current=key_ea20dd  previous=key_db8972
  -> ROTATION IN PROGRESS. Clear CALLHOOK_SECRET_PREV when the panel is updated
     and the WARN lines stop.
```

### What had never been tested, and now has

**Until 09:05:58 the previous-key acceptance branch had never accepted a real webhook.**

Both `.env` variables held the same value, so every delivery matched `CALLHOOK_SECRET` on the first comparison and the branch was dead code in production. It had passed **43/43** in an offline selftest. That is not the same thing.

Step 2 armed it. The panel kept sending `key_db8972`, which now matched only `CALLHOOK_SECRET_PREV`. If that path were wrong, the clinic would have been refusing **every** webhook from 09:05:58 — this incident, rebuilt by hand, from a position of safety.

At **09:35**, on live clinic traffic:

```
accepted today        64 calls
refused today         none
on PREVIOUS key/30min 12
```

**Twelve real webhooks fell through to the previous key and were accepted. Zero refusals.** The branch is verified in production. (**D174** — *a selftest is not a production verification. Any code path that only fires during an exceptional state is unverified until that state is entered on live traffic.*)

### The WARN line is the instrument, not the fault

Each of those twelve deliveries logged `WARN: request accepted on the PREVIOUS key (key_db8972)`. Earlier sessions would have read that as an alarm.

It is the opposite. It says: **the new key took, and the panel has not caught up.** Its *appearance* proves step 2 landed. Its *disappearance* will prove step 3 landed. The signal for step 3 is negative — nothing to watch for except a silence.

---

## 16. **[S127]** STATUS AT CLOSE — AND THE ONE COMMAND THAT MUST NOT BE ISSUED

```
Step 1 — dual-key gate armed          DONE   08-Jul 23:38:00
Step 2 — new key installed            DONE   09-Jul 09:05:58, verified on 12 live calls
Step 3 — MyOperator panel updated     OPEN   parked by the owner
Step 4 — clear CALLHOOK_SECRET_PREV   BLOCKED ON STEP 3
```

**Step 4's command is deliberately absent from `rotate_callhook.sh`, from the KB, from the runbook, and from this report.**

Clearing `CALLHOOK_SECRET_PREV` while the MyOperator panel still holds the old key refuses **every** delivery. That is this incident, reconstructed by hand, by someone who has read this report. **Parking step 3 parks step 4. They are one unit.** (**D173**.)

Its mechanics are nevertheless settled, and cost one command rather than the session that had been reserved for them. `_startup_connect()` line 545 reads `if SECRET and SECRET_PREV:` — an empty string is falsy in Python, so `CALLHOOK_SECRET_PREV=` behaves identically to an absent line (**D170**). The same read surfaced a fourth startup branch, `current=(unset!)  previous=…`, recorded in no document.

**The old 12-character `@` key `key_db8972` remains live and remains exposed in a chat transcript.** It dies at step 4 and nowhere earlier.

What steps 1 and 2 bought is not the key's death. It is that **the key can now be killed at leisure, with no outage available to it** — where before, killing it required a synchronised cutover with a vendor whose panel has already reverted once, unannounced.

### Step 3, when a clinic day allows it

1. Read the key off the VPS. It never passes through a chat: `grep '^CALLHOOK_SECRET=' /root/wa/.env | cut -d= -f2`
2. Paste into the panel's Call-webhook `?key=` field. Nothing else in the URL changes. No spaces. 24 characters.
3. `clear` the terminal.
4. One real call → `bash /root/wa/rotate_callhook.sh status`. Wanted: `refused today: none`; `on PREVIOUS key/30min` falling toward `0` (it counts a 30-minute window, so it drains rather than drops).
5. **Re-check ≥1 hour later, same clinic day.** `0` and `none`.

**An incident is closed by a successful re-test, not a successful test.** In S94 the panel edit survived exactly one verification call — four successful deliveries at 16:28–16:35 on 07-Jul — and then reverted, unnoticed, for 44 hours. Step 5 exists because of those 44 hours.

If anything refuses: put the old key back in the panel (the VPS needs no touching), or `bash /root/wa/rotate_callhook.sh rollback`. **The clinic cannot be stuck while `PREV` holds the old key.**

---

**END OF INCIDENT ADDENDUM v4 (S127). §16 is the last section. If §16 is absent, this file is truncated.**


---

## CHANGELOG

| Version | Date | Change |
|---|---|---|
| **v5** | **09 Jul 2026 (Session 131)** | **CONSOLIDATED, SELF-CONTAINED.** v2 (§1–§9), v3 (§10–§14) and v4 (§15–§16) merged verbatim into one file; the addendum chain and the superseded v1 are retired. **v4's status line — *"MITIGATED, rotation in progress"* — was false: the rotation was PARKED in Session 128.** Corrected. Added a standing note that the `key_…` strings are the receiver's fingerprint labels, not secrets, so that no future reader redacts the record or panics at it. **No finding, correction or retraction was altered.** |
| v4 | 09 Jul 2026 (Session 127) | §15 the rotation moves — steps 1 and 2. §16 status at close, and the one command that must not be issued. |
| v3 | 08 Jul 2026 (Session 126) | §10 the second retraction. §11 Window 2, deliberately left open. §12 corrections to this report's own facts. §13 a latent fault of the same class, found elsewhere. §14 status. |
| v2 | 08 Jul 2026 (Sessions 124 + 125) | §1–§9. Supersedes v1. The detector built; the access log read; two findings corrected and one open question closed. Two distinct outages, not one. |
| v1 | 08 Jul 2026 (Session 124) | Written before the detector existed. **Superseded. Retired from the working set at Session 131.** |

---

**END OF INCIDENT REPORT v5 — the CHANGELOG is the last section. If it is absent, this file is truncated.**
