# Session 125 — GitHub commit notes (dual-key acceptance; the 403 blind spot closed)
Date: 08 July 2026 · Master KB = v1.48 (v1.49 pending, see `canonical-docs/KB_APPEND_Session125.md`)

## What changed this session

A build session. The `CALLHOOK_SECRET_MISMATCH_403` detector — specced in S94, respecced in S124, and never built while the fault recurred twice — is now built. The receiver was then changed so that the fault it detects can no longer cause an outage at all.

## Is there anything to commit?

**Yes. Two code files, four documents.**

### Code

- **`call-hook/call_hook_capture.py`** — v1 → v2. The repo's v1 (md5 `3c79f9be39f0ae83f43ce05a631f471e`, 15,617 B, 03-Jul) is confirmed byte-identical to the VPS copy that was replaced, so the git history is a genuine rollback point.

  Three changes, **all inside the secret gate**. An AST diff confirms `_load_env`, `raw_log`, `to_ist_iso`, `_find_sa_key`, `extract_record`, `record_to_row`, `_connect_store`, `store_handle`, `upsert` and `home` are byte-identical to v1. Only `call_hook()` differs. The 403 response body and status are unchanged — MyOperator's behaviour depends on them.

  1. The gate accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared with `hmac.compare_digest`. (D162)
  2. A delivery arriving on the previous key logs a WARN naming the masked label.
  3. Every refusal is written to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** it is refused — metadata only, throttled to the first 500/day then 1 in 100. (D163)
  4. Startup warns if the secret contains whitespace, an `=`, or exceeds 40 characters. (D164)

- **`call-hook/callhook_watchdog.py`** — new, 25,042 B. Read-only detector. Reads the OpenLiteSpeed access log, the only place a rejected delivery is visible, and separates *"nobody called"* from *"we refused everyone."* Six fault codes. Writes nothing unless `--state` is passed.

### Documents

- `canonical-docs/HANDOFF_RUNBOOK_2026-07-08_Session125_v59.md` — new (supersedes v58).
- `canonical-docs/Diagnostics_Surveillance_System_Spec_v1_7.md` — new (supersedes v1.6; v1.6 retained).
- `canonical-docs/INCIDENT_2026-07-08_CALLHOOK_403_RECURRENCE.md` — **rewritten in place.** v1 stays in git history. Two findings corrected, one root cause downgraded.
- `canonical-docs/KB_APPEND_Session125.md` — the pending v1.49 material as an append block. **Temporary.** Delete it once it is folded into `Clinic_Master_KB_SystemsRegister_v1_49.md`.
- `canonical-docs/README_CANONICAL_SET.md` — refreshed; it was stale by five KB versions.

### Not committed, deliberately

`.env`, `.env.bak_*`, `call_hook_logs/`, `call_hook_rejects/`, `drive_token.json`, service-account JSON. All confirmed blocked by `.gitignore` via `git check-ignore`. The reject log holds no secrets, but it does hold source IPs.

## Verification before pushing

    python3 -m py_compile call-hook/call_hook_capture.py call-hook/callhook_watchdog.py
    python3 call-hook/call_hook_capture.py --selftest    # 43/43
    python3 call-hook/callhook_watchdog.py --selftest    # 37/37
    git diff --cached | grep -iE 'CALLHOOK_SECRET *=|key=[A-Za-z0-9@]{6,}'   # must print nothing

The last line must print nothing. If it prints, do not commit.

## What the detector proved, on its first run

```
access log : 115 accepted (200) / 635 rejected (403) / 0 other
keys seen  : key_271f88 (115 ok / 635 rejected)
```

**One key label, carrying both the rejections and the acceptances.** MyOperator sent the identical string across all 750 requests on 08-Jul. Nothing about the sender changed at 10:28; only the value on the VPS did. No second webhook subscription was delivering — `CALLHOOK_MULTIPLE_KEYS` did not fire, and it would have.

## The record is corrected in this commit

The outage was **two faults, not one.**

- **Window 1** (06-Jul 13:41 → 07-Jul 16:28): a 61-character run-on line in `.env`, **dormant** until a gunicorn worker respawned and re-read the file. `-w 1` with no `--preload` means the worker reads `.env` once, at import. Nothing human selected that moment.
- **Window 2** (07-Jul ~16:35 → 08-Jul 10:28): S94's repair demonstrably **worked** — four deliveries returned 200 at 16:28–16:35 — and then the panel and the VPS came apart again within minutes. **How, is still unknown.**

And `sed -i '17s'` **did not create** the run-on. It removed it. It was S94's *repair*. KB v1.48 §94 records the run-on as a lost newline that merged `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment; it reconstructs to the byte — `12 + 17 + 32 = 61`, non-alphanumerics `@ _ _ =` in exactly that order. The incident report v1 §6 had the causal direction inverted, and so did the assistant, mid-session. Both retracted.

That correction was found by a `grep` for leaked secrets, run mechanically over the cold-kit archive, which matched on `FU_UPLOAD_SECRET` in a paragraph nobody had opened in fourteen sessions.

> S124 §1: *"The runbook is not evidence. Re-derive from the data before building on a recorded number."* It was written about someone else's numbers.

## Known defects shipped in this commit

- `callhook_watchdog.py` reports *"MyOperator is not delivering at all"* for any date its access log does not cover. **It commits the absence-of-evidence error it was written to catch.** `--date` on past days is untrustworthy. Do not schedule it until this is fixed.
- `mask_key()` hashes the wire form (`%40`); the receiver hashes the literal form (`@`). Same key, different labels. `unquote()` before hashing. (D165)
- 115 accepted deliveries on 08-Jul against 114 raw-log lines. One delivery returned 200 and wrote nothing. Off by exactly one. Unexplained.

## Open, and urgent

The key in `.env` is exposed in a chat transcript and must be rotated. Rotation is now four restarts with no possible downtime; the procedure is in the header of `call_hook_capture.py` and in Runbook v59 §5. Choose a key with **no `@`**.
