# KB APPEND BLOCK — Session 126 → `Clinic_Master_KB_SystemsRegister_v1.49.md`

**Read §0 before pasting. This block SUPERSEDES `KB_APPEND_Session125.md`, which is truncated and must never be pasted.**

---

## §0 — HOW TO USE THIS BLOCK

`Clinic_Master_KB_SystemsRegister_v1.48.md` is 107 KB. It is **not** re-emitted as a full file. Two reasons.

The project protocol is *full-file replacements, never diffs to hand-edit*. That rule exists for **code**, where a partial file is a broken program. For a 107 KB canonical document the calculus inverts: re-emitting from a summary risks silent, unnoticeable loss of material with no other home. **Session 125 shipped five truncated close-out documents.** That is not a hypothetical risk.

Second, and decisive: in this session the KB was reachable only through the assistant's read interface, **not through the shell**. A full rewrite could not be mechanically diffed against its source, byte-counted, or verified by anything except reading it — the exact verification that failed five times in S125. **A file that cannot be verified should not be emitted.**

**`KB_APPEND_Session125.md` is TRUNCATED.** It ends mid-sentence inside its §3, at *"…it currently reports 'MyOperator is not delivering at all' for any date"*. Its §1 (the §S125 section) and §2 (D162–D165) are intact; its third §12 replacement, its one §12 addition, and its changelog line are gone. **Quarantine it. Do not paste it.**

**This block re-carries everything from S125 that was intact, in §1A, so that nothing is lost.** Paste this block alone and the KB reaches v1.49 complete.

**Six paste operations, all additive. Nothing is deleted except the §12 lines named explicitly in §4.**

If you want a true full-file v1.49, say so at the start of Session 127 **and place `Clinic_Master_KB_SystemsRegister_v1.48.md` in the uploads folder** so the shell can read it. It will then be built from the source directly, with a byte count and a last-section assertion before and after.

---

## §1A — RE-CARRIED FROM THE TRUNCATED S125 BLOCK: append at the end of the session-sections series

### §S125 — Dual-key acceptance, rejection visibility, and the end of the 403 blind spot
**08 July 2026 · Build session · Closes the S124 top task**

Session 124 closed with the `CALLHOOK_SECRET_MISMATCH_403` detector **specced and unbuilt**. Session 125 built it, ran it, used it to finish the forensics S124 could not, and then removed the fault's ability to cause an outage at all.

**The detector, at last.** `callhook_watchdog.py` v1.0 lives at `/root/wa/call-hook/callhook_watchdog.py`. It reads the OpenLiteSpeed access log — the only place a rejected webhook delivery is visible — and answers the question the raw log cannot: *did nobody call, or did we refuse everyone?* Read-only; it writes nothing unless `--state` is passed. Six fault codes, four severities, keys handled only as opaque `key_<md5[:6]>` labels with no unmask flag. 37/37 offline selftest on the VPS interpreter.

**What it proved in one line.** Run at 14:11 on 08 Jul: `115 accepted (200) / 635 rejected (403)`, and `keys seen : key_271f88 (115 ok / 635 rejected)`. **One key label, carrying both the rejections and the acceptances.** MyOperator sent the identical string across all 750 requests. Nothing about the sender changed at 10:28 — only the value on the VPS did. The second-webhook-subscription theory, S124's leading suspicion, is dead for 08 Jul: `CALLHOOK_MULTIPLE_KEYS` did not fire, and it would have.

**The `7e17f7` anomaly.** `/root/wa/.env.bak_20260707_162509` holds a `CALLHOOK_SECRET` value of **61 characters**, non-alphanumerics `@ _ _ =` in that order, with `strip()` changing nothing. Not a smudge, not a third key. It is the 12-character `@` key with a `FU_UPLOAD_SECRET=<32-char value>` fragment attached: `12 + 17 + 32 = 61`, to the byte. Found by a routine secrets sweep of the cold kit, matching on `FU_UPLOAD_SECRET` in a file nobody had opened in fourteen sessions.

> **[S126 CORRECTION]** S125 attributed this to a **lost newline**. That is retracted. See §S126 and **D166**. The composition above is settled; the **mechanism is UNKNOWN**.

**Therefore the outage was TWO faults, not one — and `sed` was the repair, not the cause.**

*Window 1 (06 Jul 13:41 → 07 Jul 16:28).* The corrupted line. **Dormant** — real and asleep — until a worker respawn re-read `.env` at 13:41 on 06 Jul. No restart, no reboot, no journal entry; nothing human selected that moment.

*Window 2 (07 Jul ~16:35 → 08 Jul 10:28).* S94's `sed -i '17s'` **removed** the run-on and installed a clean alphanumeric key; the panel was edited; **four deliveries returned 200 at 16:28–16:35. The fix worked.** Then the two ends came apart again within minutes. **How, is still unknown.** A second webhook subscription is disproven for 08 Jul; that the 16:28 panel edit never saved is not excluded.

> **[S126]** The journal shows **no worker respawn between `07 Jul 16:28:04` and `08 Jul 10:28:33`** — the whole of Window 2. The worker held one secret in memory throughout, so the VPS side could not have changed. This points hard at the panel. **Not proven:** `tail -3` did not rule out an unprinted respawn. See §S126 and backlog item 5.

**Retractions (S125).** Incident v1 §6 stated the fix avoided *"`sed` by line number, which is what created §94.1's run-on line"* — the causal direction is **inverted**. S124 §3.2's *"exactly one line, no run-on"* inspected `.env` **after** the repair. S124 §4's *"the VPS was correct throughout"* is false for Window 1. And a mid-session assistant claim that the encoding defect "didn't bite" was wrong: it had bitten, invisibly.

**The encoding trap.** The live `.env` value labels as `key_db8972`; the access log labels the same key as `key_271f88`. Two hypotheses were live: benign percent-encoding of the `@`, or `.env` and the running worker had **diverged again**, arming a second dormant outage. Resolved by test, not assumption — `urllib.parse.quote()` of the `.env` value reproduces the access-log label exactly. Benign. Recorded as **D165**.

**The structural fix.** `call_hook_capture.py` **v2**, live 08 Jul 14:49:12. Three changes, all inside the secret gate; an AST diff confirms `extract_record`, `record_to_row`, `upsert`, `_connect_store`, `store_handle`, `raw_log`, `to_ist_iso`, `_find_sa_key`, `_load_env` and `home` are byte-identical to v1. The gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV` in constant time (**D162**); a delivery on the previous key logs a WARN naming the masked label; a refusal is written to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** it is refused (**D163**), metadata only, throttled to the first 500 per day then 1 in 100; and startup warns if the secret contains whitespace, an `=`, or exceeds 40 characters (**D164**). 43/43 offline selftest. Proven live by a keyless probe: 403, and exactly one reject-log line.

**Why the fault was dormant, which is the heart of it.** `gunicorn -w 1` with no `--preload`: the worker reads `.env` once, at import. An edit takes effect at the next respawn — hours or days later, with no restart, no reboot, no journal entry linking cause to effect. On 06 Jul that respawn came at 13:41. **This was never a careless-edit problem. It was a system that permitted a careless edit to remain invisible for 44 hours.** A perfect edit applied to only one of the two places the secret lives would have produced the same outage.

**Still open at S125 close:** rotate `CALLHOOK_SECRET` · the watchdog's two defects · 115 accepted vs 114 raw-log lines · what if anything reverted the panel in S94.

---

## §1B — NEW SECTION: append immediately after §S125

### §S126 — The housekeeping that broke the record five times
**08 July 2026 · Build session (code changed; no restart, no key touched) · Rotation still unstarted**

Session 126 was convened to rotate `CALLHOOK_SECRET`. **The key was not touched. `.env` was not written. Nothing was restarted.** The session ran the six data-safety measures Runbook v59 placed before the rotation, and five recorded facts failed against the disk.

**A fifth truncated document.** `KB_APPEND_Session125.md` ends mid-sentence inside its §3. The runbook (v59) and the incident report (v2) are intact. The procedure was not reconstructed from memory. **A numbering gap surfaced:** KB v1.48 carries D121–D160 and says *"next free: D161"*; the S125 append is headed *"append after D161"*. **D161 exists in neither.**

**The record was wrong by one byte, and had been for sessions.** The live `call_hook_capture.py` was **30,749** bytes, not 30,750. 690 lines, final byte `\n` (confirmed by `od -c`), so the file terminated properly and no newline was missing. Because the repo's `31,100` came from the same record, the claimed 350-byte delta was unverified in both directions. Measured, not trusted: **the true delta is 351 bytes, 5 lines.**

**The "lost newline" explanation is dead.** `/root/wa/.env.bak_20260707_162509` (1327 bytes, 29 lines, mode 600) shows `CALLHOOK_SECRET len=61` **and** `FU_UPLOAD_SECRET len=32` — the latter present, on its own intact line. **A lost newline merges two lines; it consumes the second. That line survived.** The 61 characters therefore arrived by **duplication: text inserted, nothing deleted.**

Composition remains settled — `12 (@ key) + 17 ("FU_UPLOAD_SECRET=") + 32 (alnum value) = 61`, non-alphanumerics `@ _ _ =` in that order. **Mechanism is UNKNOWN.** A `sed` overrun, a stray append, an editor, a botched heredoc paste all produce insertion-without-deletion; the evidence distinguishes none of them. This is the **third** explanation offered for these characters: `sed` (incident v1, retracted S125), lost newline (S125, retracted S126), duplication-of-unknown-origin (S126, and it is a *class*, not a mechanism). Both retracted causes were plausible, written down with confidence, and survived because nobody opened the file. **See D166. Record no third cause.**

**A prediction failed and is recorded rather than dropped.** The assistant predicted the forensic backup at ~1465 bytes, *larger* than the live 1416. It is 1327 — smaller by 89. The sign was wrong (a lost newline removes a byte; it does not add bulk), and the method was worse: it compared the sizes of two files differing in several places and attributed the difference to the one line under discussion. The `12+17+32=61` reconstruction rests on the value's length and character order, not on file size, and is unaffected.

**An unrecorded secret was found in the live `.env`.** `ANTHROPIC_API_KEY len=111`. Absent from the 07-Jul backup, therefore added between `07 Jul 16:25` and `08 Jul 10:28` — **inside the outage window** — by something nobody has identified. Mode 600, so not an emergency. But the gunicorn call-webhook worker now loads an Anthropic credential it has no use for, and no document mentions it. **Rotate it; move it out of that worker's environment; find out what wrote it.** The census that found it is now standard: **D169**.

**Six bytes are unaccounted.** `1416 − 1327 = +89`. `ANTHROPIC_API_KEY` line (+130), two blank lines (+2), `CALLHOOK_SECRET` 61→12 (−49) = **+83**. Every other key name and value length is identical across both files. Probably line termination. Logged, not waved off.

**The 115-vs-114 gap resolved into something smaller.** At 14:11: 115 accepted / 114 raw-log lines. At 21:20: **133 accepted / 132 lines.** Eighteen further deliveries, eighteen further lines, **offset still exactly one.** An ongoing defect would have widened it. **One historical event, not a mechanism that is still running.** Bounded and low-priority; benign explanations exist (a health probe; a line counted before it was flushed).

**Window 2, nearly settled, deliberately left open.** `journalctl … | grep "secret gate" | tail -3` returned three startup lines: `07 Jul 16:28:04`, `08 Jul 10:28:33`, `08 Jul 14:49:13`. Window 2 sits entirely inside the first gap. **The worker held one secret in memory across the whole of it** — `.env` could have been rewritten a hundred times and the worker would never have known. The VPS side could not have changed. The four 200s at 16:28–16:35 prove the worker's key matched the panel; the 403s from ~16:35 prove it stopped matching; the worker did not move. **This points hard at the panel.** It is **not recorded as proven**: `tail -3` did not rule out an unprinted respawn, and it is not established that v1 printed `secret gate` on every start path. One read-only command settles it, and it no longer depends on the watchdog's coverage guard or on log retention.

**The `.env` and the worker provably agree.** `cp -a` preserved the backup's mtime: `.env` was last written `08 Jul 10:28`, and the worker respawned at `10:28:33` — one deliberate act, the S124 repair, thirty-one seconds after `last 403 : 10:28:02`. Established three independent ways: the startup label (`key_db8972`, literal), the wire label (`key_271f88`, access log), and the mtime.

**Two rollback points, not zero.** Runbook v59 §7 warned the S125 `.bak` was "a copy of v2, not v1" and therefore "not a rollback point." True, and understated: it is a **valid rollback point to v2**. `cmp` proves `call_hook_capture.py.bak_20260708_144241` and `call_hook_capture.py.LIVE_v2_s126_20260708_212453` byte-identical, both 30,749. **v1 is not on the box** — GitHub and the cold kit only.

**A git trap, found armed.** The clinic PC had `core.autocrlf=true` with `.gitattributes` set to `* text=auto`: LF in the repository, **CRLF written into the working tree at every checkout**. A `git clone` followed by the Binary WinSCP upload that D164 mandates would have delivered **701 carriage returns** to the VPS, faithfully. **Binary mode prevents WinSCP from *adding* CRs; it does nothing about CRs git already wrote.** Unfired only because the working copy had arrived by some route other than a checkout. Closed at source: `core.autocrlf false` (repo-local) and `*.py text eol=lf` in `.gitattributes`, which travels with the repo and overrides any user's config. **See D167.**

**The upload was stopped because the repo's docstring was also wrong.** The repo candidate's header read *"run onto the end of it by a lost newline"* — disproven forty minutes earlier. The live header read *"the exact signature of a `sed -i` line-number edit"* — disproven in S125. Runbook v59 §2 states the rotation procedure is *"documented in the header of `call_hook_capture.py`"*; that header is a canonical document. Installing the candidate would have swapped one retracted causal story for another, in a canonical document, on the live box, on the evening the second one was disproven. **A corrected full file was written instead.**

**And the diff was read, hunk by hunk, for the first time.** Three hunks: a docstring, one `log()` string, one trailing blank line. `2→12`, `2→2`, `+1`. `690 + 11 = 701`; `30749 + 741 = 31490`. Nothing hidden. **The long-repeated claim "executing code is identical" is now verified rather than asserted.**

**Installed 21:55 IST via candidate path, never by overwriting** (**D168**): upload to a distinct filename → `diff` against running code → `py_compile` on the VPS interpreter → `--selftest` → validate the rollback point with `cmp` **immediately before** the atomic `mv` → re-verify the *installed* file. Final: **31,490 bytes, 701 lines, `CR = 0`, final byte `\n`, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43 selftest on the installed file.** Last section asserted by reading it.

**The running worker still executes the pre-21:55 bytes.** It imported at `14:49:13` and will not notice the swap. The new header becomes real at the next respawn — **rotation step 1**. The same dormancy that took the clinic down on 06-Jul, deliberately induced, known, with a chosen resolution time.

**Not one of these findings came from reasoning.** Every one came from looking at the disk. Five recorded facts failed; a sixth — the byte count — had been repeated across sessions unchallenged.

**Still open at close:** rotate `CALLHOOK_SECRET` (unstarted; the key is still exposed in a chat transcript) · `ANTHROPIC_API_KEY` unaccounted in `.env` · the watchdog's two defects · Window 2's cause, one read-only command away · six unexplained bytes · D161 unaccounted · 133 vs 132.

---

## §2A — RE-CARRIED FROM THE TRUNCATED S125 BLOCK: D-SERIES, append after D161

**D162 — Dual-key acceptance is mandatory for any shared-secret gate.**
*08 Jul 2026, S125.* A secret held in two places must be rotatable without a synchronised cutover. The call-webhook receiver accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared in constant time. A stale worker and a fresh worker both work; the panel and the VPS may disagree indefinitely; the disagreement surfaces as a WARN line naming the key in use, rather than as a receptionist reporting stuck tiles. **Generalises to `WA_APPROVE_KEY`, `FU_UPLOAD_SECRET`, and every future shared secret** — any secret read once at import in a single-worker process is a mine with an unknown fuse.

**D163 — A gate must write down its refusals before it refuses.**
*08 Jul 2026, S125.* The implementation of Diagnostics Category 5. `call_hook_rejects/YYYY-MM-DD.jsonl`, dir 700, files 600. Metadata only: timestamp, reason, masked key label, key length, source IP, method, path. **Never the key, never the body.** Throttled — full detail for the first 500 refusals per day, then 1 in 100 — so a refusal storm is visible without being able to fill the disk. A gate that refuses silently is indistinguishable from a world that never called.

**D164 — `.env` is never edited by line number, and its contents are validated at startup.**
*08 Jul 2026, S125.* `sed -i '<N>s|…'` is prohibited: position-dependent, unverifiable after the fact, mangles escapes. Use `awk` + `ENVIRON` or `printf` to append.
**Correction to the rationale this rule was first given.** The `sed` did **not** create the 61-character run-on; `sed -i '17s'` was S94's repair, which removed it. The rule stands on its own merits, not on that story — and the story is now on the record as an example of how a plausible causal claim survived two sessions and one incident report unchallenged. *(S126: the replacement story — a lost newline — is also retracted. See D166.)*
**WinSCP transfers of `.env` and of any `.py` must be Binary, never Text** — Text mode appends `\r` to every line. Verify after any upload: `file <path>` says `ASCII text`; `grep -c $'\r' <path>` says `0`. *(S126: necessary but insufficient — see D167.)* The receiver warns at startup if its secret contains whitespace, an `=`, or exceeds 40 characters, which would have caught the run-on the moment a worker read it, in Window 1, before any clinic day was lost.

**D165 — Masked key labels must be encoding-normalised before comparison.**
*08 Jul 2026, S125.* An md5 label of a wire-format key and of the same key in literal form are different strings. The Go client percent-encodes `@` as `%40`; Flask decodes it before the receiver compares. The same key labels as `key_271f88` in the access log and `key_db8972` in `.env`. Any tool comparing labels across sources must `urllib.parse.unquote()` first. Cost roughly an hour on 08 Jul and briefly presented as a live second outage.

---

## §2B — NEW D-SERIES: append after D165

> **Note on numbering.** KB v1.48 records D121–D160 and states *"next free: D161."* No D161 exists in v1.48 or in the S125 append block, which is headed *"append after D161."* **D161 is unaccounted for.** D162–D165 (S125) and D166–D169 (S126) are correct and unaffected. **Next free decision number for new work: D170.**

**D166 — No cause is recorded unless the evidence distinguishes it from its rivals. `UNKNOWN` is a valid, and sometimes the only honest, entry.**
*08 Jul 2026, S126.* The 61-character `.env` value has had three explanations. `sed` overrunning its delimiter (incident report v1 — retracted S125, because `sed -i '17s'` was S94's *repair*). A lost newline (S125 — retracted S126, because `FU_UPLOAD_SECRET len=32` survives on its own intact line in `.env.bak_20260707_162509`, and a lost newline consumes the line it merges). And "a duplication" — which is not a mechanism but a *class* of them: a `sed` overrun, a stray append, an editor, a botched heredoc paste all fit equally. **The evidence chooses none.** Both retracted causes were plausible, were written down with confidence, and survived because nobody opened the file. A knowledge base that cannot say `UNKNOWN` will fill the gap with the most recent guess and then defend it. **Composition may be recorded (`12 + 17 + 32 = 61`, non-alphanumerics `@ _ _ =` in that order). Mechanism may not.**

**D167 — A control that guards one path into a hazard is not a control on the hazard.**
*08 Jul 2026, S126.* D164 mandates WinSCP **Binary** transfers for `.py` and `.env`, to stop WinSCP appending `\r`. Correct, and insufficient. The clinic PC had `core.autocrlf=true` with `.gitattributes` set to `* text=auto`: LF in the repository, **CRLF written into the working tree at every checkout**. A `git clone` followed by the Binary upload the runbook prescribes would have delivered 701 carriage returns to the VPS, faithfully. **Binary mode prevents WinSCP from *adding* CRs; it does nothing about CRs git already wrote.** Fixed at source: `core.autocrlf false` (repo-local, clinic PC) and `*.py text eol=lf` in `.gitattributes`, which travels with the repo and overrides any user's config. **Generalises: when a rule names a tool, ask what else can produce the same byte.**

**D168 — Live code is never overwritten to be tested. Candidate path → diff → compile → selftest → atomic `mv`.**
*08 Jul 2026, S126.* Upload to a distinct filename beside the live file. `diff` it against the *running* code and **read every hunk** — "the difference is only a docstring" had been believed for sessions and had never once been checked; when it finally was, it was true, and it was also about to install a retracted causal claim into a canonical header. `py_compile` and `--selftest` on the VPS interpreter, not the author's. Validate the rollback point with `cmp` **immediately before** the `mv` that destroys the file it would roll back to — a backup you have not compared at the moment of use is a belief about the past. `mv` on one filesystem is atomic; there is no instant of a half-written file. Then **re-verify the installed file**: compiling a candidate and installing something are two different acts. **Verify by reading the file's last section. Never by hash alone — a hash proves two files match; it cannot prove either is complete.**

**D169 — Secrets are inventoried by name and value length, never by value.**
*08 Jul 2026, S126.* Run at every EOS, against `.env` and every `.env.bak_*`:
```
awk '/^[A-Za-z_][A-Za-z0-9_]*=/ { n=index($0,"="); printf "  %-24s len=%d\n", substr($0,1,n-1), length($0)-n }' <envfile>
```
A complete census with nothing secret on the screen, in a transcript, or in a scrollback buffer. It is how `ANTHROPIC_API_KEY len=111` was found sitting unrecorded in the call-webhook worker's environment, added during the outage window by something nobody has identified. It is how `CALLHOOK_SECRET len=61` was confirmed *alongside* an intact `FU_UPLOAD_SECRET len=32`, which is what killed the lost-newline theory. **An unknown secret in a live process's environment is a fault, whether or not it has caused one yet.** Also: every `.env.bak_*` holds a real key. `chmod 600`, never delete the forensic ones, treat all of them as secrets.

---

## §3 — MENTAL MODELS: append to the running list

**A cause is not a story that fits. It is a story the evidence prefers over its rivals.** Three explanations, two wrong, both plausible, both confident, both surviving because nobody opened the file.

**A rule can be correct, necessary, and still not sufficient.** "WinSCP must be Binary" is right, and would not have saved you: `core.autocrlf=true` puts the carriage returns in before WinSCP sees the file.

**Verify the rollback point before you destroy the thing it rolls back to.**

**A constant offset is not a rate.** 115/114 looked like a receiver silently dropping deliveries. 133/132, eighteen deliveries later, says one historical event.

**Read the diff. Somebody has to, once.** Thirty seconds; caught a retracted causal claim about to enter a canonical document.

**The record is not the disk, and the record loses.** Five recorded facts failed in one evening, including a byte count repeated across sessions.

**`grep -c` exits 1 when the count is 0.** Never chain it with `&&`. It will silently truncate the rest of your verification.

---

## §4 — §12 (STATE): replacements and additions

**REPLACE** the `call-hook.service` line with:

> **`call-hook.service` — LIVE.** `call_hook_capture.py` **v2 (dual-key)**. File on disk replaced 08-Jul **21:55**: 31,490 bytes, 701 lines, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43 selftest on the installed file. **The running worker still executes the pre-21:55 bytes** (imported 14:49:13); the new file loads at the next respawn — deliberately, at rotation step 1. gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`. Gate accepts `CALLHOOK_SECRET` or `CALLHOOK_SECRET_PREV`; refusals written to `call_hook_rejects/YYYY-MM-DD.jsonl` before they are refused. Still serving the **old 12-char `@` secret** (literal label `key_db8972`, wire label `key_271f88`) — **exposed in a chat transcript.** `previous=(unset)`: **no rotation started.** Rollback: two byte-identical v2 copies, `call_hook_capture.py.bak_20260708_144241` and `.LIVE_v2_s126_20260708_212453` (both 30,749 bytes). v1 is not on the box.

**REPLACE** the `Rotate CALLHOOK_SECRET` backlog line with:

> 🔴 **Rotate `CALLHOOK_SECRET`** — both ends, still unstarted after S126. **Four-restart, zero-downtime** procedure (D162), documented in the header of `call_hook_capture.py` and in Runbook v60 §5. Generate on the VPS (`openssl rand -hex 12`), **no `@`**, nothing that percent-encodes — removes the D165 encoding trap at source. **Steps 1–2 are safe at any hour; step 3 (the panel) needs a clinic day with hours in front of it** — one real call AND a re-check ≥1 hour later on the same day.

**REPLACE** the Diagnostics surveillance-layer line with:

> **Rejected-at-the-door (Category 5) — IMPLEMENTED** in the receiver (D163), live 08-Jul 14:49. **`callhook_watchdog.py` v1.0 — BUILT**, on the VPS, manual runs only. Blocked on two defects before scheduling: **(a)** a coverage guard — it currently reports *"MyOperator is not delivering at all"* for any date the access log does not span, a confident wrong diagnosis pointing away from the real cause; bail with exit 3 instead. **(b)** `unquote()` before hashing in `mask_key()`, so labels compare across sources (D165). Until (a) lands, `--date` on past days is untrustworthy. It exits 1 on WARN, so a naive `OnFailure` will fire all day on already-fixed 403s.

**ADD** to §12:

> **`.env` (`/root/wa/.env`)** — 1416 bytes, 32 lines, mode 600, last written `08 Jul 10:28` (worker respawned `10:28:33`; not written since). Inventory by name and length only (D169). Contains **`ANTHROPIC_API_KEY len=111`, unaccounted** — absent from the 07-Jul backup, therefore added inside the outage window by something unidentified, and loaded into a gunicorn worker that has no use for it. **Rotate it; move it out; find what wrote it.** Forensic backup `/root/wa/.env.bak_20260707_162509` (1327 bytes, mode 600) is irreplaceable and contains a real old key — never delete. Session backup `/root/wa/.env.bak_s126_20260708_212316` (mode 600) contains the live key.

> **Clinic PC git** — `D:\dr-manoj-git\drmanoj-clinic-automation`. Git exists **only bundled inside GitHub Desktop** (`%LOCALAPPDATA%\GitHubDesktop\app-3.6.1\resources\app\git\cmd\git.exe`); it is not on PATH and there is no standalone install. **`core.autocrlf` is now `false` (repo-local); `.gitattributes` pins `*.py text eol=lf`** (D167). Before S126 a fresh checkout would have written CRLF into every `.py`, which a Binary WinSCP upload then delivers intact to the VPS.

---

## §5 — CHANGELOG LINE

Append to the KB header block:

> **v1.49** (08 Jul 2026) — Adds **§S125** (dual-key acceptance, rejection visibility, the 403 blind spot closed; D162–D165) and **§S126** (the housekeeping that broke the record five times; D166–D169). **Retracts two causal claims about the 61-character `.env` value: it was neither `sed` nor a lost newline; the mechanism is UNKNOWN (D166).** Records an unaccounted `ANTHROPIC_API_KEY` in the live `.env` (D169), a `core.autocrlf=true` line-ending trap on the clinic PC (D167), and the candidate-path install discipline (D168). `call_hook_capture.py` at 31,490 bytes, md5 `beafccafbf7e81aa5f2736be939b2bbb`. **`CALLHOOK_SECRET` rotation remains UNSTARTED.** `KB_APPEND_Session125.md` was truncated and is quarantined; its intact content is re-carried here. **D161 is unaccounted for. Next free decision number: D170.**

---

## §6 — WHAT TO DO WITH THE OLD APPEND BLOCK

Move `KB_APPEND_Session125.md` into `_QUARANTINE_TRUNCATED_S125\`, beside the four documents already quarantined. **It must never be pasted.** Everything intact within it is re-carried above in §1A and §2A.

---

**END OF KB APPEND BLOCK — Session 126. §6 is the last section. If §6 is absent, this file is truncated and must not be pasted.**
