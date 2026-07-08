# HANDOFF RUNBOOK — 08 July 2026 — Session 125 — v59
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: BUILD (live code changed). Supersedes v58.**

---

## §0 — WHAT HAPPENED THIS SESSION

Session 124 closed with the `CALLHOOK_SECRET_MISMATCH_403` detector **specced and unbuilt**, the clinic running on the old 12-character `@` secret, and three open questions. Session 125 built the detector, ran it, used it to answer two of the three questions, and then closed the hole in the receiver that made the outage invisible.

### The recovered thread

This session began mid-forensics. A previous Cowork window had frozen after establishing that the `.env` `CALLHOOK_SECRET` had held a value hashing to `7e17f7` before the 07-Jul 16:25 edit — a label matching nothing MyOperator had ever sent. The user carried forward only `callhook_watchdog.py`, a file that previous session had written and that had never been run.

### What was verified, in order

1. **`callhook_watchdog.py` read and audited before use.** Compiles clean; 37/37 offline selftest, both in the sandbox and on the VPS interpreter (Python 3.9). Confirmed read-only: it opens the access logs and the raw-log directory, and writes nothing unless `--state` is passed. It cannot take the clinic down. It was already on the VPS at `/root/wa/call-hook/callhook_watchdog.py` (25,042 bytes) — the frozen session had landed it.

2. **First real run, 08 Jul 14:11 IST.** `115 accepted (200) / 635 rejected (403) / 0 other`. Last 403 at 10:28:02, last 200 at 13:53:58 — independently confirming the S124 fix timestamp from the access log, without being told it. Severity WARN, `CALLHOOK_403_EARLIER_TODAY`. Not currently failing.

3. **The decisive line: `keys seen : key_271f88 (115 ok / 635 rejected)`.** **One key label, both accepted and rejected.** MyOperator sent the identical key string all day. Nothing about the sender changed at 10:28; only the value on the VPS did. `CALLHOOK_MULTIPLE_KEYS` did not fire, and it would have.

4. **`7e17f7` resolved — and it identified a two-session error in our own record.** The pre-repair backup `/root/wa/.env.bak_20260707_162509` holds a `CALLHOOK_SECRET` value of **61 characters**, non-alphanumeric characters `@ _ _ =` in that order. `strip()` changes nothing, so it is not a trailing-whitespace smudge, and it is not a third key.

   KB v1.48 §94 already had the answer, in a paragraph nobody had re-read in fourteen sessions: the §94.1 damage was **a lost newline** merging `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment. It reconstructs to the byte — `12 (@ key) + 17 ("FU_UPLOAD_SECRET=") + 32 (alnum fragment) = 61`, and the non-alphanumerics fall out in exactly the observed order. Found by a routine secrets sweep of the cold kit, which matched on `FU_UPLOAD_SECRET` in a file nobody had opened.

   **Therefore: `sed -i '17s'` did not create the run-on. It removed it.** It was S94's *repair*. The incident report v1 said the opposite; so did this assistant, mid-session. Both are retracted. See §0 "Corrections".

5. **The encoding trap, and a hypothesis that nearly cost the night.** The live `.env` value labels as `key_db8972`; the access log labels the same key as `key_271f88`. Two possibilities: benign percent-encoding of the `@`, or `.env` and the running worker had **silently diverged again** — a second dormant outage, armed and counting down to the next respawn. Resolved by test, not by assumption: `urllib.parse.quote()` of the `.env` value reproduces the access-log label exactly. Benign. The Go client sends `%40`; Flask decodes it before the gate compares.

6. **`call_hook_capture.py` v2 written, tested offline (43/43), installed, restarted 14:49:12 IST.** An AST diff confirms `extract_record`, `record_to_row`, `upsert`, `_connect_store`, `store_handle`, `raw_log`, `to_ist_iso`, `_find_sa_key`, `_load_env` and `home` are byte-identical to v1. Only `call_hook()` changed. Startup line read `secret gate: ON  current=key_db8972  previous=(unset)`, no corruption warning, Sheet connected with 139 rows indexed.

7. **The hole proved closed.** A keyless local probe returned 403 and wrote exactly one line to `call_hook_rejects/2026-07-08.jsonl`: timestamp, `"reason": "no_key_supplied"`, `"key_label": "key_absent"`, `127.0.0.1`, `"n_today": 1`. No key, no body. That line is the thing that did not exist for three clinic days.

### What was built

**`call_hook_capture.py` v2** — three changes, all inside the secret gate.

The gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared in constant time. A delivery arriving on the previous key logs a WARN naming the masked label. A rejected request is written to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** it is refused — metadata only, throttled to full detail for the first 500 refusals per day and then one in a hundred, so a 403 storm stays visible without being able to fill the disk. Plus a startup sanity check that warns if the configured secret contains whitespace, an `=`, or exceeds 40 characters.

**`callhook_watchdog.py` v1.0** — the detector specced in S94, respecced in S124, finally built. Reads the access log, which is the only place a rejected delivery is visible. Six fault codes, four severities, masked keys, offline selftest. Read-only.

### New fault codes minted

`CALLHOOK_RAWLOG_MISSING` · `CALLHOOK_403_EARLIER_TODAY` · `CALLHOOK_MULTIPLE_KEYS` · `CALLHOOK_NO_ACCEPTED_TODAY` · `CALLHOOK_SILENT`. All raised by `callhook_watchdog.py`. `CALLHOOK_SECRET_MISMATCH_403` (minted S94) is now, at last, actually detectable.

### Decisions: D162 · D163 · D164 · D165

See §4.

### Corrections to the record — four of them, and this is the important part of the session

**The outage was TWO faults, not one.** The 4,449 rejections span two windows separated by four accepted deliveries on the evening of 07 Jul. v1 of the incident report treated them as one continuous event and therefore had to explain the whole span with a single mechanism, which forced the wrong answer.

- **Window 1 (06 Jul 13:41 → 07 Jul 16:28).** Cause: the 61-character run-on line in `.env`. **Dormant** until a worker respawn re-read the file at 13:41 on 06 Jul. Nothing human selected that moment.
- **Window 2 (07 Jul ~16:35 → 08 Jul 10:28).** Cause: after S94's repair *worked* (four × 200 at 16:28–16:35), the panel and the VPS came apart again within minutes. **How, is still unknown.**

**The `sed` was the repair, not the cause.** Incident v1 §6 said the fix deliberately avoided *"`sed` by line number, which is what created §94.1's run-on line."* Inverted. KB §94 records `sed -i '17s|.*|CALLHOOK_SECRET=<clean key>|'` as the S94 *fix* that deleted the run-on. The run-on came from a lost newline and pre-dates it. **This assistant repeated the inverted version earlier in this very session, and retracts it.** `awk`+`ENVIRON` is still the better instrument — it cannot mangle escapes and does not depend on a line number staying put — but it was chosen against a hazard that had not actually occurred.

**S124 §3.2** recorded the `.env` as *"exactly one line, no run-on — **not** the §94.1 corruption."* True of the morning of 08 Jul; false of 07 Jul 16:25. The inspection came *after* the repair. Both observations are true of their own moments.

**S124 §4** concluded *"the VPS was correct throughout; the vendor panel was not."* The VPS was **not** correct throughout — for Window 1 it was the sole cause. The panel-reverted hypothesis survives only for Window 2, and remains unproven there.

**And one more, smaller.** Early in this session, on the strength of the single-key finding, this assistant stated that the encoding defect "didn't bite." It had bitten; it was invisible until the labels disagreed. Same shape as the fault itself: a mismatch that produces no symptom until something forces it into the open.

> Every one of these errors was discoverable in this project's own knowledge base. They were found by a `grep` for leaked secrets, run mechanically over the cold-kit archive, which matched on `FU_UPLOAD_SECRET` in a file nobody had opened in fourteen sessions.

---

## §1 — STATE / MENTAL MODELS

### Track 2 live systems

- **`call_hook_capture.py` v2 — LIVE** since 14:49:12 on 08-Jul. Dual-key gate, armed but idle (`previous=(unset)`, no rotation started). Still serving the **old 12-char `@` secret**, label `key_db8972`.
- **`callhook_watchdog.py` v1.0 — on the VPS, manual runs only.** Not scheduled. Two known defects (§2). Trust today's output; do not trust `--date` on past days.
- `call-hook.service` — LIVE, gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`.
- `verdict_review.py` (Stage 3b) — LIVE, on demand. md5 `af6622e4edc3f454cf0bfed128c4f76b`.
- `call_verdict.py` (Stage 3 judge) — LIVE, unchanged. md5 `8c8ae1656056d8d1b2dec1b4776fe5c9`. Carries the D158 join defect.
- `Dashboard.html` v18.19 — LIVE (D156). Gate fails open on couldn't-measure.
- Stage 1 (02:00) + Stage 2 (03:00) LIVE + healthy; Drive OAuth token fresh.
- WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup; key rotations still overdue.

**Track 1 / PC-local:** `processor.py` at D148 (md5 `171a090645da130a4f4cbb0c0b102f22`); Vitals & Plan Step 5 complete; Step 7 not started; Hindi spelling task open.

### Mental models — new or reinforced this session

**A secret that lives in two places must be rotatable without a synchronised cutover.** This is the whole lesson. The panel and the VPS each hold `CALLHOOK_SECRET`. Change one and the other is wrong. Worse, the wrongness is *dormant*: gunicorn `-w 1` with no `--preload` means the worker reads `.env` once, at import. The disagreement only becomes an outage at the next worker respawn — hours or days later, with nothing linking cause to effect. On 06-Jul that respawn came at 13:41 and the door slammed. Dual-key acceptance is what makes the disagreement harmless.

**Absence of coverage is not absence of events.** The receiver returned 403 before it raw-logged and before it journalled, so 4,449 refusals produced no evidence anywhere the clinic's systems look. The watchdog exists to correct that error — and then commits the same error itself, reporting *"MyOperator is not delivering at all"* when its own access log simply doesn't reach back to the date it was asked about. The error is not a bug in one program. It is a habit of mind.

**Two labels of the same key can disagree, and both be right.** Wire format (`%40`) and literal format (`@`) hash differently. Any comparison across sources must normalise first (D165). This cost roughly an hour and briefly looked like a live second outage.

**Test the alarming hypothesis before you act on it, and before you reassure.** The `key_db8972` vs `key_271f88` mismatch had a benign explanation and a frightening one. Both were stated plainly; the benign one was *proven*, not assumed. The frightening one — a re-armed dormant mismatch — would have meant the next respawn killed the clinic again.

**Restart at a moment you choose.** The 14:49 restart performed exactly the operation that took the clinic down on 06-Jul: a worker respawned and re-read `.env`. The difference was that `.env` and the running worker were known to agree, the moment was chosen, and the process printed the key label it loaded. Deliberate exposure to a known hazard, under observation, is not the same act as being ambushed by it.

**`.env` is not edited by line number (D164) — but not for the reason we thought.** The `sed` did not create the run-on; it removed it. The rule stands anyway, on its own merits: a line-number edit is position-dependent, unverifiable after the fact, and mangles escapes. `awk`+`ENVIRON` or `printf` to append. Related, and a *real* instance of the same class: WinSCP transfers of `.env` and of any `.py` must be **Binary**, never Text — Text mode appends `\r` to every line. Verify: `file` says `ASCII text`, `grep -c $'\r'` says `0`.

**A dormant fault has no cause you can see.** Window 1's corruption may have sat in `.env` for days. It broke the clinic at 13:41 on 06 Jul because a worker respawned, and for no other reason. When something breaks with no preceding change, look for the last thing that *read* a file, not the last thing that wrote one.

**Carried from S124, all still true:** no verification mechanism may stand between a staff member and recording what a patient said · one successful call does not verify a fix · the panel can revert, so align the VPS to the panel · a safety flag is a clinical signal about a patient, never a statement about staff accuracy · **the runbook is not evidence** (applied to S124 itself this session) · 0 cards refereed, so every accuracy claim is agreement, not accuracy.

---

## §2 — BACKLOG (what to pick up next)

### 🔴 TOP — do this before anything else

1. **Rotate `CALLHOOK_SECRET`.** The key is exposed in a chat transcript. Rotation is now a four-restart, zero-downtime procedure, documented in the header of `call_hook_capture.py` and in §5 below. It cannot hurt you any more, which is precisely why it must not be allowed to drift.

2. **Fix the two watchdog defects.** (a) **Coverage guard:** refuse to judge a date the access log does not span — currently zero lines is read as zero traffic and reported CRITICAL as *"MyOperator is not delivering at all"*, a confident wrong diagnosis pointing away from the real cause. Bail with exit 3 instead. (b) **`unquote()` before hashing** in `mask_key()`, consistently, so labels compare across sources (D165). Until (a) lands, `--date` on past days is untrustworthy.

3. **Schedule the watchdog.** Only after item 2. Note it exits 1 on WARN, so a naive `OnFailure` will fire all day on already-fixed 403s.

### 🟠 OPEN QUESTION — evidence may be expiring

4. **115 vs 114.** On 08-Jul the access log recorded 115 accepted deliveries; `2026-07-08.jsonl` holds 114 lines. One delivery returned 200 and wrote nothing. That is the receiver accepting and not writing — the failure mode `CALLHOOK_RAWLOG_MISSING` finding 3 exists to catch — and it is off by exactly one. Benign explanations exist (a health probe, a line written after the count). Unexplained.

5. **What reverted the panel in S94 is still unknown.** Today's single-key evidence covers 08-Jul only. Re-reading the 06–07 Jul access logs would settle it, subject to log retention — and requires item 2(a) first, or the answer will be wrong.

### OWNER TASK (no build, ~20 min) — everything downstream depends on it

6. **Referee the 32 cards in `Verdict_Review`.** Zero are done. This is the only thing that converts "the AI agrees with staff 80% of the time" into "the AI is right N% of the time", and it is the ground truth for the autonomous judge and the voice-bot KB.

### STAGE-3 FOLLOW-THROUGH

7. **Fix `call_verdict.py`: agent + Clinic ID from the CALL record, not the claim.** 21/27 cards say "(not recorded)" — including a conduct complaint against the doctor. Clinic ID is blank on 100% of rows, which **blocks the doctor console entirely**.
8. **Fix the D158 join defect** — an incoming call must never absorb a later outgoing call's claim.
9. **Systemd timer** for `call_verdict.py` (~03:30 IST) + `verdict_review.py` (~03:45 IST).
10. **`verdict_review.py` v1.1** — the de-identified `Verdict_Training_KB` export. Needs the Stage-4 de-identifier (unbuilt) and refereed rows (item 6).

### THE STAFF-FACING PROGRAMME (designed S124, not built)

11. **Reduce the staff vocabulary to 4–5 "what next" choices**; the AI supplies the 11-code "what happened" from the transcript. Owner to supply the wording (Hindi where it helps).
12. **Ask at hang-up, one tap, optional note.**
13. **Never show staff the AI.** Corrective action reaches them from the doctor, about the patient.
14. **Measure staff on completion, never on accuracy.** (15 of 36 outgoing calls — 42% — got no outcome at all.)
15. **Background reconciler** (claim → call, the reverse join). Must read `Call_Feed`, NOT `Call_Recordings`. Three verdicts that must never be collapsed: *no attempt* · *attempt, not connected* (**blameless**) · *connected but nothing asked*.
16. **Doctor-only review console.** Blocked on item 7 (Clinic ID). `WebApp.gs` stays sealed.
17. **Diarisation (Stage 2).** Sarvam includes it at ₹30/hour. Cheapest high-leverage change.
18. **Voicemail outcome code** — dissolves if item 11 lands first.

### Track 2 live backlog (carried)

🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate `WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · **arm the timer-freshness checker** · maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy-rotate `FU_UPLOAD_SECRET` (D145) · **empty-transcript guard** (3 empty on 06-Jul; they land in Unclear looking like AI failures) · **VPS Python 3.9 is past EOL** (google-auth warns on every run).

### Track 1 backlog (unchanged)

Hindi SPELLING corrections in `vitals_page.html` LIB strings · Step 7 new-patient reconciliation · Living Clinic Data Map (§66.6).

### Documentation

- **DONE this EOS:** Runbook v59 · Diagnostics_Surveillance_Spec v1.7 · incident report v2 · KB append block (S125) · git kit · cold kit · Notion updated live.
- **Notion WAS updated this session** — the connector was authorised, unlike S124. Two Tech & Systems Register rows created, plus a Clinic HQ decisions page for D162–D165.
- **KB v1.49 was NOT re-emitted as a full file.** See §6.

---

## §3 — KEY PATHS / FACTS (Session-125 additions in **bold**)

- **Call webhook receiver:** `/root/wa/call-hook/call_hook_capture.py` — **v2, dual-key**. gunicorn `-w 1` (no `--preload`) on `127.0.0.1:8098`, unit **`call-hook.service`**, route `POST /mo-callhook?key=…`, proxied by `followup.dr-manoj.in` (`/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf:126`).
- **The worker reads `.env` once, at import.** A change to `.env` takes effect at the next respawn, not at the edit. This is the mechanism of the whole incident. Dual-key acceptance is what makes it harmless. Do not remove it.
- A row reaches `Call_Durations` only when `category == "obd"` **and** `client_ref_id` is present — i.e. only for calls placed through the dashboard dialer. A hand-dialled call can never unlock the gate.
- **Reject log: `/root/wa/call-hook/call_hook_rejects/YYYY-MM-DD.jsonl`** (dir 700, files 600). Metadata only — never the key, never the body. Throttle: full detail for the first 500 refusals per day, then 1 in 100. Env override `CALLHOOK_REJECT_DIR`.
- **Watchdog: `/root/wa/call-hook/callhook_watchdog.py`** (25,042 bytes). `--selftest` (37/37, offline) · bare run (today) · `--json` · `--date YYYY-MM-DD` (**untrustworthy until the coverage guard lands**) · `--state <path>` (the only thing it ever writes). Exit 0 OK / 1 WARN / 2 CRITICAL / 3 could-not-run.
- **Key labels are md5[:6], prefixed `key_`.** `mask_key()` is deliberately identical in the receiver and the watchdog. **But the watchdog hashes the wire form (`%40`) and the receiver hashes the literal form (`@`).** The same key therefore labels as `key_271f88` in the access log and `key_db8972` in `.env`. Compare like with like. `urllib.parse.quote()` bridges them.
- **Current secret:** 12 characters, contains one `@`, literal label `key_db8972`, wire label `key_271f88`. **Exposed in a chat transcript. Rotate.**
- **Access-log forensics** (the only place a 403 storm is visible), glob `/home/*/logs/*access*`:
  `grep -h "mo-callhook" /home/*/logs/*access* | sed -E 's/key=[^& ]+/key=<masked>/g' | tail -20`
- **VPS python is `/root/wa/venv/bin/python3`** (3.9, past EOL — google-auth warns on every run). System `python3` lacks gspread.
- **WinSCP transfers of `.py` and `.env` must be Binary, not Text.** Verify after any upload: `file <path>` should say `ASCII text`, not `with CRLF line terminators`; `grep -c $'\r' <path>` must be `0`.
- **Bracketed paste:** pasting a multi-line block into this shell can leak `[200~` and swallow the command. Type commands one line at a time, or `printf '\e[?2004l'` once.

---

## §4 — DECISIONS ADDED THIS SESSION

**D162 — Dual-key acceptance is mandatory for any shared-secret gate.** A secret held in two places must be rotatable without a synchronised cutover. The receiver accepts `CALLHOOK_SECRET` or `CALLHOOK_SECRET_PREV`. A stale worker and a fresh worker both work; the panel and the VPS may disagree indefinitely; the disagreement surfaces as a WARN line naming the key in use, rather than as a receptionist reporting stuck tiles. Generalises to `WA_APPROVE_KEY`, `FU_UPLOAD_SECRET`, and every future shared secret.

**D163 — A gate must write down its refusals before it refuses.** The implementation of Diagnostics Spec Category 5. Metadata only: timestamp, reason, masked key label, key length, source IP, method, path. Never the key, never the body. Throttled so a refusal storm is visible without being able to fill the disk. A gate that refuses silently is indistinguishable from a world that never called.

**D164 — `.env` is never edited by line number, and its contents are validated at startup.** `sed -i '<N>s|…'` is prohibited: position-dependent, unverifiable after the fact, mangles escapes. Use `awk` + `ENVIRON` or `printf` to append. **Correction to the original rationale:** the `sed` did *not* create the 61-character run-on — that was a lost newline, and the `sed` was S94's repair. The rule survives on its own merits, not on that story. WinSCP transfers of `.env` and `.py` must be **Binary**, never Text — a real instance of the same invisible-character class. The receiver now warns at startup if its secret contains whitespace, an `=`, or exceeds 40 characters, which would have caught the run-on the moment a worker read it.

**D165 — Masked key labels must be encoding-normalised before comparison.** An md5 label of a wire-format key and of the same key in literal form are different strings. Any tool comparing labels across sources must `unquote()` first. Recorded because it will otherwise be rediscovered at 2