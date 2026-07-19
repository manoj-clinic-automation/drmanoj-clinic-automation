# NEXT SESSION PROMPT — Session 127

Copy everything below the line into a fresh Cowork window.

---

Session 127. Rotate CALLHOOK_SECRET — for real this time.
I'm Dr. Manoj Agarwal, Dr. Manoj Agarwal Clinic, orthopaedic surgeon, Bareilly.

Read the KB, KB_APPEND_Session126.md, and HANDOFF_RUNBOOK_2026-07-08_Session126_v60.md
first. Confirm before doing anything.

THREE INTEGRITY CHECKS BEFORE YOU SAY A WORD ABOUT ROTATION:

1. The runbook must end with the line "END OF RUNBOOK v60 — §7 is the last section."
   KB_APPEND_Session126.md must end with "END OF KB APPEND BLOCK — Session 126. §6 is
   the last section." The incident addendum must reach "## 14." If any of those is
   missing, you have a truncated copy. STOP and tell me. Do not reconstruct anything
   from memory — S125 shipped five truncated documents and S126 found the fifth.

2. KB_APPEND_Session125.md is TRUNCATED and QUARANTINED. If you find it in project
   knowledge, do not read it as authoritative and never paste it. Everything intact
   in it is re-carried in KB_APPEND_Session126.md §1A and §2A. If you cannot see
   §1A in the S126 block, the S126 block is truncated too — STOP.

3. The next free decision number is D170. It comes from KB_APPEND_Session126.md §2B,
   not from the KB file, which stops at D160 and claims D161 is next. D161 is
   unaccounted for in both. If you think the next number is D166, the S126 append
   block did not load — STOP and tell me.

WHERE WE ARE:
- call_hook_capture.py v2 on disk since S126: 31,490 bytes, 701 lines, md5
  beafccafbf7e81aa5f2736be939b2bbb, 43/43 selftest on the INSTALLED file.
- The RUNNING WORKER STILL EXECUTES THE PRE-21:55 BYTES. It imported at 14:49:13 on
  08-Jul and has not respawned. The new file loads at rotation step 1. This is
  deliberate and is the same dormancy that caused the outage — induced on purpose,
  with a chosen resolution time.
- Dual-key gate armed but idle: previous=(unset). NO ROTATION STARTED.
- The clinic still runs on the OLD 12-character key containing an '@'. It is exposed
  in a chat transcript. That is why this session exists — for the second time.
- Rollback: two byte-identical v2 copies on the box (bak_20260708_144241 and
  .LIVE_v2_s126_20260708_212453, both 30,749 bytes). v1 is NOT on the box.
- .env: 1416 bytes, 32 lines, mode 600, last written 08-Jul 10:28. Untouched by S126.
- callhook_watchdog.py v1.0, manual runs only, two known defects.

DO THE ROTATION. Runbook v60 §5. Nothing else first — S126 spent its whole evening on
housekeeping and never reached the key. Housekeeping is DONE. Do not re-audit it.

CONSTRAINTS (standing protocol):
  - ONE step at a time. Wait for my explicit confirmation before the next.
  - Plain language. Full-file replacements only, never diffs I hand-edit.
  - Never print the old key or the new key. Masked md5[:6] labels only.
  - Generate the new key ON THE VPS (`openssl rand -hex 12`). It must never enter this
    chat, and must contain NO '@' and no character that percent-encodes — that removes
    the D165 encoding trap at source.
  - Edit .env with `awk`+ENVIRON or `printf` to append. Never `sed -i '<N>s'`.
  - Before every restart: file / grep -c $'\r' / py_compile / --selftest (43/43).
  - `grep -c` EXITS 1 WHEN THE COUNT IS 0. Never chain it with `&&`; use `;`. It
    silently truncated one of my verification commands in S126.
  - After every restart: read the startup line and confirm the key label is the one we
    intended. A fix verified by probing the server with the key you just wrote to it
    proves nothing — that is how S94 died in seven minutes.
  - Startup lines, verified against the source (not the runbook):
      step 1 → previous=SAME AS CURRENT (rotation not started; harmless)
      step 2 → ROTATION IN PROGRESS
      step 3 → no restart; the signal is the WARN lines STOPPING
      step 4 → previous=(unset)
  - A selftest WARN naming key_96e7ef is a TEST FIXTURE, not my key.
  - Nothing already live is rebuilt without my explicit OK. Manual workflow stays.
  - VPS python is /root/wa/venv/bin/python3. On my PC I use `python`, and git exists
    ONLY inside GitHub Desktop (not on PATH).
  - If you write any file for me, verify it by asserting its LAST section is present.
    Never by hash. A hash proves two files match; it cannot prove either is complete.
  - Bracketed paste eats multi-line blocks in my SSH session. One command at a time,
    or a script whose actions are nested inside the guard.
  - Do not record a cause for anything unless the evidence rules out the alternatives.
    D166. Three explanations have already been written for one 61-character line and
    two of them were wrong.

TIMING — THIS IS THE PART S126 GOT RIGHT AND YOU MUST NOT UNDO:
  Steps 1 and 2 are zero-downtime and safe at any hour.
  Step 3 (the MyOperator panel) needs a CLINIC DAY WITH HOURS IN FRONT OF IT:
  one real call AND a re-check at least an hour later on the SAME clinic day.
  An incident is closed by a successful re-test, not a successful test.
  Do not touch the MyOperator panel until step 3, and tell me exactly what to click.

IF ANYTHING LOOKS WRONG, run this first — it is read-only:
    /root/wa/venv/bin/python3 /root/wa/call-hook/callhook_watchdog.py; echo "exit=$?"
  Read the `keys seen` line. It is a WIRE-format label (key_271f88 = the same key as
  .env's key_db8972). One label = one webhook subscription. Two labels = either a
  second subscription or the D165 encoding trap; rule out the trap first.

AFTER THE ROTATION, if there is time, in this order:
  1. ANTHROPIC_API_KEY (len=111) is sitting unrecorded in /root/wa/.env, added inside
     the outage window by something nobody has identified, and loaded into the
     call-webhook worker's environment. Rotate it. Move it out. Find what wrote it.
  2. Window 2's cause is ONE read-only command away — widen the journal window and
     count EVERY service start, not just lines matching "secret gate". If no respawn
     occurred between 07-Jul 16:28:04 and 08-Jul 10:28:33, the VPS side could not have
     changed and the panel must have. Do NOT close S94's question on the `tail -3` I
     already ran; it did not rule out an unprinted respawn.
  3. The watchdog's two defects: the coverage guard, and unquote() before hashing.

Connected sources: Google Drive, Gmail, Notion ("Clinic HQ"), GitHub
(drmanoj-clinic-automation). ClickUp is parked (D17) — do not check it.

Read the KB + runbook, confirm, then start at rotation step 1.
