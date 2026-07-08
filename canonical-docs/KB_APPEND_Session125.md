# KB APPEND BLOCK — Session 125 → `Clinic_Master_KB_SystemsRegister_v1.49.md`

**Read §0 before pasting.**

---

## §0 — WHY THIS IS AN APPEND BLOCK AND NOT A FULL FILE

The project protocol is *full-file replacements, never diffs to hand-edit*. That rule exists for **code**, where a partial file is a broken program and a hand-edit is a corruption waiting to happen. Session 125 is, in fact, a case study in exactly that.

`Clinic_Master_KB_SystemsRegister_v1.48.md` is **107 KB**. Re-emitting it from a summary would risk silently dropping material that has no other home — a worse and far less visible failure than a paste. So this is an append block, and the honest thing is to say so rather than hand over a file that *looks* complete.

**Four paste operations, all additive. Nothing is deleted except the three §12 lines named explicitly in §3.**

If you would rather have a true full-file v1.49, say so at the start of Session 126 and it will be built from the v1.48 source directly, with a byte count before and after.

---

## §1 — NEW SECTION: append at the end of the session-sections series

### §S125 — Dual-key acceptance, rejection visibility, and the end of the 403 blind spot
**08 July 2026 · Build session · Closes the S124 top task**

Session 124 closed with the `CALLHOOK_SECRET_MISMATCH_403` detector **specced and unbuilt**. Session 125 built it, ran it, used it to finish the forensics S124 could not, and then removed the fault's ability to cause an outage at all.

**The detector, at last.** `callhook_watchdog.py` v1.0 lives at `/root/wa/call-hook/callhook_watchdog.py`. It reads the OpenLiteSpeed access log — the only place a rejected webhook delivery is visible — and answers the question the raw log cannot: *did nobody call, or did we refuse everyone?* Read-only; it writes nothing unless `--state` is passed. Six fault codes, four severities, keys handled only as opaque `key_<md5[:6]>` labels with no unmask flag. 37/37 offline selftest on the VPS interpreter.

**What it proved in one line.** Run at 14:11 on 08 Jul: `115 accepted (200) / 635 rejected (403)`, and `keys seen : key_271f88 (115 ok / 635 rejected)`. **One key label, carrying both the rejections and the acceptances.** MyOperator sent the identical string across all 750 requests. Nothing about the sender changed at 10:28 — only the value on the VPS did. The second-webhook-subscription theory, S124's leading suspicion, is dead for 08 Jul: `CALLHOOK_MULTIPLE_KEYS` did not fire, and it would have.

**The `7e17f7` anomaly, resolved — by this KB, in a paragraph nobody had re-read in fourteen sessions.** `/root/wa/.env.bak_20260707_162509` holds a `CALLHOOK_SECRET` value of **61 characters**, non-alphanumerics `@ _ _ =` in that order, with `strip()` changing nothing. Not a smudge, not a third key. §94 above already says what it is: a **lost newline** merging `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment. It reconstructs to the byte — `12 (@ key) + 17 ("FU_UPLOAD_SECRET=") + 32 (alnum fragment) = 61`, non-alphanumerics falling out in exactly the observed order. Found by a routine secrets sweep of the cold kit, matching on `FU_UPLOAD_SECRET` in a file nobody had opened.

**Therefore the outage was TWO faults, not one — and `sed` was the repair, not the cause.**

*Window 1 (06 Jul 13:41 → 07 Jul 16:28).* The run-on line. **Dormant** — real and asleep — until a worker respawn re-read `.env` at 13:41 on 06 Jul. No restart, no reboot, no journal entry; nothing human selected that moment.

*Window 2 (07 Jul ~16:35 → 08 Jul 10:28).* S94's `sed -i '17s'` **removed** the run-on and installed a clean alphanumeric key; the panel was edited; **four deliveries returned 200 at 16:28–16:35. The fix worked.** Then the two ends came apart again within minutes. **How, is still unknown.** A second webhook subscription is disproven for 08 Jul; that the 16:28 panel edit never saved is not excluded.

**Retractions.** Incident v1 §6 stated the fix avoided *"`sed` by line number, which is what created §94.1's run-on line"* — the causal direction is **inverted**. S124 §3.2's *"exactly one line, no run-on"* inspected `.env` **after** the repair. S124 §4's *"the VPS was correct throughout"* is false for Window 1. And a mid-session assistant claim that the encoding defect "didn't bite" was wrong: it had bitten, invisibly.

**The encoding trap.** The live `.env` value labels as `key_db8972`; the access log labels the same key as `key_271f88`. Two hypotheses were live: benign percent-encoding of the `@`, or `.env` and the running worker had **diverged again**, arming a second dormant outage. Resolved by test, not assumption — `urllib.parse.quote()` of the `.env` value reproduces the access-log label exactly. Benign. Recorded as **D165** because it will otherwise be rediscovered at 2am, and nearly was.

**The structural fix.** `call_hook_capture.py` **v2**, live 08 Jul 14:49:12. Three changes, all inside the secret gate; an AST diff confirms `extract_record`, `record_to_row`, `upsert`, `_connect_store`, `store_handle`, `raw_log`, `to_ist_iso`, `_find_sa_key`, `_load_env` and `home` are byte-identical to v1. The gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV` in constant time (**D162**); a delivery on the previous key logs a WARN naming the masked label; a refusal is written to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** it is refused (**D163**), metadata only, throttled to the first 500 per day then 1 in 100; and startup warns if the secret contains whitespace, an `=`, or exceeds 40 characters (**D164**). 43/43 offline selftest. Proven live by a keyless probe: 403, and exactly one reject-log line.

**Why the fault was dormant, which is the heart of it.** `gunicorn -w 1` with no `--preload`: the worker reads `.env` once, at import. An edit takes effect at the next respawn — hours or days later, with no restart, no reboot, no journal entry linking cause to effect. On 06 Jul that respawn came at 13:41. **This was never a careless-edit problem. It was a system that permitted a careless edit to remain invisible for 44 hours.** A perfect edit applied to only one of the two places the secret lives would have produced the same outage.

**Corrections to the record.** S124 §3.2 recorded `.env` as *"exactly one line, no run-on — not the §94.1 corruption"*; that inspection happened on 08 Jul, **after** the 07-Jul 16:25 edit, and the pre-edit backup proves the line **was** corrupted. Both are true of their own moments. S124 §4's root cause ("the panel reverted") is **contradicted for 08 Jul** and remains unproven for 06–07 Jul. Also: a mid-session assistant claim that the encoding defect "didn't bite" was **wrong and is retracted** — it had bitten, invisibly, which is the same shape as the fault itself.

**Still open at close:** rotate `CALLHOOK_SECRET` (the key is exposed in a chat transcript; now a four-restart, zero-downtime procedure) · the watchdog's two defects, coverage guard and `unquote()` · 115 accepted deliveries vs 114 raw-log lines, off by exactly one, unexplained · what if anything reverted the panel in S94.

---

## §2 — D-SERIES: append after D161

**D162 — Dual-key acceptance is mandatory for any shared-secret gate.**
*08 Jul 2026, S125.* A secret held in two places must be rotatable without a synchronised cutover. The call-webhook receiver accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared in constant time. A stale worker and a fresh worker both work; the panel and the VPS may disagree indefinitely; the disagreement surfaces as a WARN line naming the key in use, rather than as a receptionist reporting stuck tiles. **Generalises to `WA_APPROVE_KEY`, `FU_UPLOAD_SECRET`, and every future shared secret** — any secret read once at import in a single-worker process is a mine with an unknown fuse.

**D163 — A gate must write down its refusals before it refuses.**
*08 Jul 2026, S125.* The implementation of Diagnostics Category 5. `call_hook_rejects/YYYY-MM-DD.jsonl`, dir 700, files 600. Metadata only: timestamp, reason, masked key label, key length, source IP, method, path. **Never the key, never the body.** Throttled — full detail for the first 500 refusals per day, then 1 in 100 — so a refusal storm is visible without being able to fill the disk. A gate that refuses silently is indistinguishable from a world that never called.

**D164 — `.env` is never edited by line number, and its contents are validated at startup.**
*08 Jul 2026, S125.* `sed -i '<N>s|…'` is prohibited: position-dependent, unverifiable after the fact, mangles escapes. Use `awk` + `ENVIRON` or `printf` to append.
**Correction to the rationale this rule was first given.** The `sed` did **not** create the 61-character run-on. §94 records the run-on as a *lost newline*, and the `sed` as the repair that deleted it. The rule stands on its own merits, not on that story — and the story is now on the record as an example of how a plausible causal claim survived two sessions and one incident report unchallenged.
**WinSCP transfers of `.env` and of any `.py` must be Binary, never Text** — Text mode appends `\r` to every line. This *is* a real instance of the invisible-character class. Verify after any upload: `file <path>` says `ASCII text`, not `with CRLF line terminators`; `grep -c $'\r' <path>` says `0`. The receiver now warns at startup if its secret contains whitespace, an `=`, or exceeds 40 characters — which would have caught the run-on the moment a worker read it, in Window 1, before any clinic day was lost.

**D165 — Masked key labels must be encoding-normalised before comparison.**
*08 Jul 2026, S125.* An md5 label of a wire-format key and of the same key in literal form are different strings. The Go client percent-encodes `@` as `%40`; Flask decodes it before the receiver compares. The same key labels as `key_271f88` in the access log and `key_db8972` in `.env`. Any tool comparing labels across sources must `urllib.parse.unquote()` first. Cost roughly an hour on 08 Jul and briefly presented as a live second outage.

---

## §3 — §12 (STATE): three replacements, one addition

**REPLACE** the `call-hook.service` line with:

> **`call-hook.service` — LIVE.** `call_hook_capture.py` **v2 (dual-key)** since 08-Jul 14:49:12. gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`. Gate accepts `CALLHOOK_SECRET` or `CALLHOOK_SECRET_PREV`; refusals written to `call_hook_rejects/YYYY-MM-DD.jsonl` before they are refused. Still serving the **old 12-char `@` secret** (literal label `key_db8972`, wire label `key_271f88`) — **exposed in a chat transcript, rotation is the top task.** `previous=(unset)`: no rotation started.

**REPLACE** the `Rotate CALLHOOK_SECRET` backlog line with:

> 🔴 **Rotate `CALLHOOK_SECRET`** — both ends. Now a **four-restart, zero-downtime** procedure (D162), documented in the header of `call_hook_capture.py` and in Runbook v59 §5. Choose a key with **no `@`** — that removes the encoding trap at source. This was the right instinct in S94; only the execution was wrong.

**REPLACE** the Diagnostics surveillance-layer line with:

> **Rejected-at-the-door (Category 5) — IMPLEMENTED** in the receiver (D163), live 08-Jul 14:49. **`callhook_watchdog.py` v1.0 — BUILT**, on the VPS, manual runs only. Blocked on two defects before scheduling: a coverage guard (it currently reports "MyOperator is not delivering at all" for any date 