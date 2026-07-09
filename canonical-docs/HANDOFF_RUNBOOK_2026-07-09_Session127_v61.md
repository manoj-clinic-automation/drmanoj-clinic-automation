# HANDOFF RUNBOOK — 09 July 2026 — Session 127 — v61
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: BUILD (`.env` written · service restarted twice · new VPS script). Supersedes v60.**

> **Session 127 spans two calendar days.** The chat froze on 08-Jul immediately after rotation step 1 and was recovered on 09-Jul from the disk. Nothing was lost, because nothing had been trusted to the chat.

---

## §0 — WHAT HAPPENED THIS SESSION

Sessions 125 and 126 were both convened to rotate `CALLHOOK_SECRET`. Both spent themselves on documentation. **Session 127 moved it.**

The key is not dead. It is now *killable at leisure*, with no outage available to it. That is the difference between this session and the two before it.

### The KB bump — attempted, and correctly refused

`Clinic_Master_KB_SystemsRegister_v1_48.md` was placed in uploads so the shell could read it, exactly as `KB_APPEND_Session126.md` §0 required for a mechanical, verifiable bump.

The shell read it. Then it read the **target**. `KB_APPEND_Session126.md` §4 names three lines to REPLACE inside `§12`. **None of the three is in `§12`.** §12 occupies lines 48–80 of v1.48 and is the verbatim `v1.38` base — its own heading says *"UNCHANGED since Session 64 close"*, and it has been true to that. It carries no `call-hook.service` line, no rotation backlog line, no surveillance-layer line.

The §12 that §4 was written against exists only in an author's mental model, assembled from the runbook's §1 and §2, which do carry all three. **This is the same failure the entire S125–S126 arc is about: a document described from memory of what it should contain, and nobody opened it.**

Executing §4 would have required *choosing* where three lines go. That is a judgement, and per **D166** a judgement is not made silently inside a canonical document. `KB_SWAP_BLOCKER_S127.md` was written instead. It decided nothing. **It has now been resolved — see §3 below — and is retired.**

What the blocker established, by measurement rather than by quoting the record:

- `v1.48` is **107,061 bytes / 1,327 lines / CR = 0**, no evidence of truncation. First verification of the long-repeated "107 KB."
- **`D161` never existed.** Two occurrences in the whole file, both forward-looking. Reserved and skipped, not lost.
- **`D155`–`D160` are orphaned** at lines 1132–1137, outside a DECISIONS INDEX whose heading claimed `D121–D160` while its body stopped at `D154`.
- **Line 1 read `v1.47`** in a file that is `v1.48` throughout its header, changelog and filename.
- An early `grep` miscounted and was about to report a duplicated `D121–D145` block inside the index. **The claim was checked before it was stated.** It was wrong. Same class as D166.

### Rotation step 1 — 08-Jul 23:38:00

`CALLHOOK_SECRET_PREV` appended equal to `CALLHOOK_SECRET`, by `printf`, never `sed` (D164). Backup `.env.bak_s127_pre_rotation_20260708_232229`.

`.env` now held the same key twice, so **no key the panel could send could be refused.** That is what made a restart at 23:30 safe.

Gates before the restart, all green: `ASCII text executable` · CR `0` · **31,490 bytes / 701 lines / md5 `beafccafbf7e81aa5f2736be939b2bbb`** · `py_compile` clean · **43/43 selftest** · `__pycache__` cleared.

The journal came back with a **fresh timestamp**:

```
[call_hook_capture] Phase B receiver v2 (dual-key).
secret gate: ON  current=key_db8972  previous=SAME AS CURRENT (rotation not started; harmless)
Listening at: http://127.0.0.1:8098
connected to 'Call_Durations' — 139 rows known
```

**The 21:55 bytes were finally executing.** The dormancy induced deliberately on 08-Jul at 21:55 — the same mechanism that took the clinic down on 06-Jul, this time understood, with a chosen resolution time — ended at 23:38:00.

The chat froze here.

### Recovery, 09-Jul morning

Service `active`. PIDs **867880 / 867881** — the identical master and worker that booted at 23:38. **No respawn in nine hours.** `call_hook_logs/2026-07-09.jsonl` present, 62,761 bytes, growing. `call_hook_rejects/2026-07-09.jsonl` **absent**. Step 1 verified under nine hours of real clinic traffic.

**A `0` that meant nothing.** `journalctl --since "23:30 yesterday"` printed `Failed to parse timestamp` and emitted **nothing**; `grep -c` counted the `PREVIOUS key` lines in that nothing and returned `0`. **A check that cannot fail is not a check.** It is precisely the watchdog's own coverage defect (backlog item 4a), reproduced by hand in a shell. Re-run with an absolute timestamp and a `wc -l` coverage guard in front of it: **58** journal lines · **0** PREV-key acceptances · `exit=1`, which is `grep -c`'s normal zero-count signal and the reason these are chained with `;` and never `&&`.

### `rotate_callhook.sh` — written because the human was the bottleneck

The owner's objection was the design input, and it was correct:

> *"again i am doing lot of un ending cmd job, despite so much documentation in the kb"*

Roughly forty commands across two sessions, each requiring him to read output and judge whether `exit=1` was the good kind — and it frequently was. **Every one of those judgements is mechanisable, and a script that refuses is strictly safer than a human who approves.** See **D171**.

`/root/wa/rotate_callhook.sh` — four subcommands:

| Command | What it does |
|---|---|
| `status` | Read-only. Service · port · both key labels · calls accepted today · refusals today · PREV-key WARN count in the last 30 min, **with a coverage guard** that prints `journal EMPTY - cannot judge` rather than a lying `0`. |
| `stage` | Generates the key **on the VPS**, builds `.env.candidate_s127` by `awk`+`ENVIRON`, runs **eleven guards**. Never touches `.env`. **Deletes its own candidate on any failure.** |
| `install` | Re-runs all guards · `cmp`-validates the rollback point **at the instant before** the atomic `mv` · swaps · clears bytecode · restarts · reads back the startup line. |
| `rollback` | Restores the backup, restarts, prints the startup line. |

Keys appear only as `key_<md5[:6]>` labels. The key never entered the chat, a shell echo, or a transcript.

### Two predictions, two misses, both caught by the check

Expected **12** function definitions; the file returned **11**. The pattern `^[a-z_]*(){` excludes digits, and `since2()` has one. Expected **3** startup branches; `grep` returned **4**.

Neither file was defective. **Both times the expectation was asserted from memory of having authored the thing being checked.** Same class as `30,750` bytes repeated across five sessions and never measured. **D172.**

### And the fourth branch mattered

Reading twenty-six lines of `_startup_connect()` — instead of trusting the runbook's quoted phrase — answered three questions in one command:

1. `-> ROTATION IN PROGRESS` is the **real** string. The runbook was right this time. It has been wrong five times in three days on this file, so it was read anyway.
2. A **fourth branch** exists — `current=(unset!)  previous=…` — recorded in no document.
3. **Line 545 reads `if SECRET and SECRET_PREV:`.** An empty string is falsy in Python. So `CALLHOOK_SECRET_PREV=` with nothing after it behaves **identically to an absent line**. Step 4's open question — budgeted for a whole session — cost one `sed -n`. **D170.**

### Rotation step 2 — 09-Jul 09:05:58

Key generated on the VPS (`openssl rand -hex 12` → 24 hex chars; no `@`, nothing that percent-encodes — the **D165 encoding trap removed at source**). Eleven guards green. Backup `.env.bak_s127_step2_20260709_085801`, `cmp`-verified byte-identical *at the instant before* the `mv`.

```
secret gate: ON  current=key_ea20dd  previous=key_db8972
  -> ROTATION IN PROGRESS. Clear CALLHOOK_SECRET_PREV when the panel is updated
     and the WARN lines stop.
```

**Then the thing that had never been tested.** Until 09:05 both `.env` variables held the same value, so every delivery matched `CALLHOOK_SECRET` on the first comparison and **the previous-key acceptance branch had never accepted a real webhook.** It had passed 43/43 offline. That is not the same thing.

At **09:35**, on live clinic traffic:

```
accepted today        64 calls
refused today         none
on PREVIOUS key/30min 12
```

Twelve real webhooks matched nothing in `CALLHOOK_SECRET`, fell through to `CALLHOOK_SECRET_PREV`, and were **accepted**. Zero refusals. **D174.**

### Steps 3 and 4 — open, and step 4 deliberately withheld

The owner parked the MyOperator panel update. **Nothing is pending on him.** Both keys work, indefinitely; that is the entire purpose of the gate.

**The step-4 command exists in no document, including this one.** Clearing `CALLHOOK_SECRET_PREV` while the panel still sends the old key refuses **every** delivery — the 06-Jul outage, reconstructed by hand from a position of safety. Parking step 3 parks step 4. **They are one unit. D173.**

**Not one finding this session came from reasoning. Every one came from looking at the disk.**

---

## §1 — STATE / MENTAL MODELS

### Track 2 live systems — call-hook family

- **`call-hook.service` — LIVE and healthy.** `call_hook_capture.py` v2 (dual-key), 31,490 bytes, 701 lines, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43. **Running the v2 bytes since 08-Jul 23:38:00.** gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`. Restarted again 09-Jul 09:05:58 for step 2.
- **`.env` — 33 lines, CR 0, mode 600.** `CALLHOOK_SECRET len=24` (`key_ea20dd`, new) · `CALLHOOK_SECRET_PREV len=12` (`key_db8972`, old, still accepted).
- **Backups, all mode 600, all containing live or historical secrets — treat as secrets, do not delete:**
  `.env.bak_20260707_162509` (forensic, pre-repair, 1327 bytes) · `.env.bak_s126_20260708_212316` · `.env.bak_s127_pre_rotation_20260708_232229` · `.env.bak_s127_step2_20260709_085801` (**the live rollback point**, referenced by `/root/wa/.rotate_s127_state`).
- **`rotate_callhook.sh` — NEW**, `/root/wa/rotate_callhook.sh`. **Known cosmetic defect:** `status` looks back only two minutes for the startup line, so it prints a blank unless a restart has just happened. Harmless in `install`; misleading in `status`. **A blank that looks like a fault is the thing this project exists to eliminate.** Fix on next touch.
- **`callhook_watchdog.py` v1.0** — built, manual runs only, **two defects open** (coverage guard; `unquote()` before hashing). Not scheduled: it exits 1 on WARN.

### Carried, all still true

The worker reads `.env` **once, at import**, so a disagreement is dormant until respawn · absence of coverage is not absence of events · **a check that cannot fail is not a check** · two labels of the same key can disagree and both be right (wire vs literal, D165) · `grep -c` exits 1 on a zero count — never chain with `&&` · restart at a moment **you** choose · a dormant fault has no cause you can see · **one successful call does not verify a fix** · **the runbook is not evidence** · install by candidate path, never overwrite the live file to test it · verify the rollback point *at the moment of use* · read the diff, somebody has to, once · a constant offset is not a rate · **the record is not the disk, and the record loses** · the correct entry is sometimes `UNKNOWN` · a control on one path into a hazard is not a control on the hazard · a safety flag is a clinical signal about a patient, never a statement about staff accuracy · 0 cards refereed, so every accuracy claim is agreement, not accuracy.

**New this session:** a check's expected value must come from the artefact, never from memory of it (**D172**) · a selftest is not a production verification (**D174**) · a procedure walked by hand twice should be walked by a script the third time, with the human's guards written into it (**D171**) · before reserving a session to *decide* how a program behaves, spend one command *reading* how it behaves (**D170**).

---

## §2 — BACKLOG (what to pick up next)

### 🔴 TOP — finish what Session 127 started

1. **Rotation step 3 — update the MyOperator panel.** Needs a clinic day with hours in front of it. Read the key off the VPS (`grep '^CALLHOOK_SECRET=' /root/wa/.env | cut -d= -f2`), paste into the panel's Call-webhook `?key=` field, `clear` the terminal. Place one real call → `bash /root/wa/rotate_callhook.sh status` → `on PREVIOUS key/30min` heading to `0`, `refused today: none`. **Then re-check ≥1 hour later, same clinic day.** *An incident is closed by a successful re-test, not a successful test* (S94: the panel edit survived exactly one verification call, then reverted, and cost two clinic days).

2. **Rotation step 4 — clear `CALLHOOK_SECRET_PREV`.** 🔴 **DO NOT ISSUE BEFORE STEP 3 IS RE-VERIFIED.** Mechanics are known and cheap (D170: empty ≡ absent). One `.env` edit, one restart, startup returns to `previous=(unset)`. **The old exposed key `key_db8972` dies here and nowhere earlier.**

3. **`ANTHROPIC_API_KEY` in `.env`.** 111 characters. Added inside the outage window; recorded nowhere; loaded into a gunicorn worker that has no use for it. Confirmed still present at S127 close. **Rotate it. Find out what wrote it. Move it out.**

4. **Fix the two watchdog defects.** (a) **Coverage guard** — refuse to judge a date the access log does not span; zero lines currently reads as zero traffic and reports CRITICAL *"MyOperator is not delivering at all"*, a confident wrong diagnosis pointing away from the real cause. Bail with exit 3. (b) **`unquote()` before hashing** in `mask_key()` (D165). Until (a) lands, `--date` on past days is untrustworthy.

5. **Fix `rotate_callhook.sh status`'s startup-line window.** Two minutes → look back to the last service start. Cosmetic, but it prints a blank where a reassurance belongs.

6. **Schedule the watchdog.** Only after item 4. It exits 1 on WARN, so a naive `OnFailure` fires all day on already-fixed 403s.

### 🟠 OPEN QUESTIONS — unchanged, cheap

7. **What changed in Window 2 — one read-only command away.** Widen the journal window and count *every* worker start, not just those matching `secret gate`. If no respawn sits between `07 Jul 16:28:04` and `08 Jul 10:28:33`, the VPS side could not have changed and S94's panel question is answered. **Do not close it on `tail -3`.**

8. **115 vs 114, now 133 vs 132.** Offset constant at exactly one across 18 further deliveries. **One historical event, not an ongoing defect.** Bounded, unexplained, low priority.

9. **Six unexplained bytes** between `.env` (1416 at S126) and `.env.bak_20260707_162509` (1327). Probably line termination. Trivial, logged.

10. **`D158` — the D150 join defect is NOT fixed.** The phone-keyed forward-window join can bind an outgoing call's staff claim to an earlier incoming call from the same number. Display-mitigated only, in `verdict_review.py`.

### OWNER TASK (no build, ~20 min) — everything downstream depends on it

11. **Referee the 32 cards in `Verdict_Review`.** Zero are done. Until some are, every accuracy claim about the AI judge is *agreement*, not *accuracy*.

### Longer-running

12. `wa_approve.py` → systemd service (currently hand-run via nohup; dies on SSH close).
13. AKEY_14 (Alisha) rotation · service-account key rotation (Tier A1, needs Lokesh).
14. Stage 4 — doctor portal UI surface at `followup.dr-manoj.in/portal`, port 8099.
15. Track 1 — Hindi **spelling** corrections in `vitals_page.html` LIB strings (`name_hi` / `instr_hi`). Content and rendering are correct; spelling only.

---

## §3 — THE KB SWAP BLOCKER IS RESOLVED

All four judgements from `KB_SWAP_BLOCKER_S127.md` §6 were taken by the owner's instruction to update the KB, and executed **additively**, from the shell, with byte counts and a deletion audit on both sides.

| Judgement | Resolution | Decision |
|---|---|---|
| 1 — where do §4's three lines go, given §12 contains none of them? | **§12 is frozen as a historical artefact.** Its heading already declares it so. A new **`§12A CURRENT LIVE STATE`** is inserted immediately after it and **wins wherever they disagree.** Nothing rewritten. | **D175** |
| 2 — where does the D-series append, given the index stops at D154? | A **continuation block** is appended after `D154`, carrying `D155`–`D175`. | **D175** |
| 3 — is D155–D160's orphaning fixed or logged? | **Re-homed by reference, not by movement.** The continuation block points to where they physically sit (`§123.7`). Nothing is cut and re-pasted inside a canonical document. | **D175** |
| 4 — is line 1 corrected, and an EOF assertion added? | **Both.** Line 1 read `v1.47` in a `v1.48` file. The KB was the only canonical document without an end-of-file assertion, and the only one that could not be verified any other way. | **D175** |

**Verification of the bump, from the shell:**

- Before: `107,061` bytes · `1,327` lines · CR `0`. Nine source anchors asserted by line number **before** a single byte was written.
- After: **`150,172` bytes · `1,549` lines · CR `0` · md5 `979da26c61227208cd46d022daddfdce`.**
- **Deletion audit: exactly 3 of 1,327 original lines are absent from v1.49** — the `v1.47` title, the `D121–D160` index heading, and `Next free: D161`. All three are the intended replacements. **Every other line survives verbatim.**
- **`D121`–`D175`: all 55 present.**

`KB_SWAP_BLOCKER_S127.md` is **retired**. Remove it from project knowledge.
`KB_APPEND_Session126.md` is **consumed**. Remove it from project knowledge.
`KB_APPEND_Session125.md` was **truncated** and remains quarantined. It must never be pasted.

---

## §4 — THE ROTATION PROCEDURE (D162) — current position

Four steps, four restarts, no downtime possible. **At no point can a mismatch stop the clinic** — until step 4, which is why step 4 waits.

1. ✅ **DONE 08-Jul 23:38:00.** `PREV` = current. Both accepted. `previous=SAME AS CURRENT`.
2. ✅ **DONE 09-Jul 09:05:58.** New key into `CALLHOOK_SECRET`. Deliveries arrive on the old key, each logging `WARN: request accepted on the PREVIOUS key`. `ROTATION IN PROGRESS`. **Those WARN lines are the instrument, not a fault.**
3. ⬜ **OPEN.** Update the **MyOperator panel**. **No restart.** The signal is *negative*: the WARN lines stop. Verify per the S124 hardened standard — one real call **and** a re-check ≥1 hour later, **same clinic day.**
4. ⬜ **BLOCKED ON 3.** Clear `CALLHOOK_SECRET_PREV`. Restart. `previous=(unset)`. Rotation complete.

**Before every restart:** `file` · `grep -c $'\r'` (must be `0`; chain with `;` not `&&`) · `py_compile` · `--selftest` (43/43). **`rotate_callhook.sh` does all of this for you.**

**Rollback, any time:** `bash /root/wa/rotate_callhook.sh rollback`. Or simply put the old key back in the panel — the VPS needs no touching.

---

## §5 — SESSION HYGIENE NOTES

- **The new key never entered a chat transcript, a shell echo, or a scrollback buffer.** It was generated on the VPS, moved into a candidate file by `awk`+`ENVIRON`, and read once by the owner off `grep '^CALLHOOK_SECRET=' /root/wa/.env | cut -d= -f2` for safekeeping. Both parties saw only `key_ea20dd`.
- **`key_db8972` — the old 12-character `@` key — is still live and still exposed in a chat transcript.** It dies at step 4. This is why step 3 is item 1.
- **`/root/wa/.rotate_s127_state`** (mode 600) holds the path of the current rollback backup. `rollback` reads it. Do not delete it before step 4 completes.
- **`.env.candidate_s127` no longer exists** — `install` consumed it with an atomic `mv`. If it ever reappears, a `stage` was run and not installed; it contains a live key; treat it as a secret.
- **`__pycache__` is cleared on every `install`.** gunicorn imports this module; a stale `.pyc` is one more thing that can be out of step with its source, and this project has lost three clinic days to *"a file and the thing reading it disagreed and nothing said so."*
- **This session wrote `.env` twice and restarted `call-hook.service` twice.** Both restarts were at a moment chosen while the clinic was reachable, with a `cmp`-validated rollback in hand.

---

**END OF RUNBOOK v61 — §5 is the last section. If §5 is absent, this file is truncated.**
