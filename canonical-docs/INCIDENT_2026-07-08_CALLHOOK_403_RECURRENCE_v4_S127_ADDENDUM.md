# INCIDENT ADDENDUM v4 — `CALLHOOK_SECRET_MISMATCH_403` — Session 127
**09 July 2026 · Appends to v3 (S126). v1 is SUPERSEDED. v2 is the main report.**
**Fault code: `CALLHOOK_SECRET_MISMATCH_403` · Severity: CRITICAL (2) · Status: MITIGATED, rotation in progress**

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
