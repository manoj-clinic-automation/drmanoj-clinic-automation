# INCIDENT REPORT — `CALLHOOK_SECRET_MISMATCH_403` (RECURRENCE)
**Dr. Manoj Agarwal Clinic · Bareilly · 08 July 2026 · Session 124 · Decision D159**

| | |
|---|---|
| **Fault code** | `CALLHOOK_SECRET_MISMATCH_403` (minted S94, detection never built) |
| **Lane** | ASSISTED (Lane 2) — detect + escalate; no auto-fix |
| **Severity** | 🔴 High — staff could not record any follow-up outcome |
| **Onset** | 06 Jul 2026, ~13:41 IST |
| **Detected** | 08 Jul 2026, ~10:00 IST — **by a receptionist**, not by any system |
| **Resolved** | 08 Jul 2026, 10:28:32 IST (service restart); first accepted delivery 10:29:17 |
| **Time to detect** | ~44 hours |
| **Time to fix after diagnosis** | ~6 minutes |
| **Data loss** | Two clinic days of follow-up outcome data (see §5) |

---

## 1. Symptom
Staff dashboard follow-up tiles stuck on **"⌛ Checking the call… the outcome unlocks once it connects"** indefinitely, after genuinely connected calls, **surviving a page refresh**. The outcome dropdown never unlocked, so no outcome could be filed.

## 2. Timeline
- **06 Jul 13:41** — last accepted webhook delivery. 111 × HTTP 200, then 1,074 × HTTP 403.
- **07 Jul** — 2,744 × 403. **Four × 200 at 16:28–16:35**: Shavez's Session-94 verification call, immediately after the panel was edited. The panel then reverted.
- **07 Jul 16:28:03** — `call-hook.service` restarted (the S94 fix).
- **08 Jul 00:00–10:28** — 631 × 403, **zero** × 200. No `2026-07-08.jsonl`.
- **08 Jul ~10:00** — owner reports stuck tiles.
- **08 Jul 10:28:32** — `call-hook.service` restarted with the realigned secret.
- **08 Jul 10:29:17** — first HTTP 200. `2026-07-08.jsonl` created. `Call_Durations` rows 101–107 written with real `bridged / answered / talk=37,23,26,15`.

## 3. Diagnosis chain (read-only until the fix)
1. `call-hook.service` **up and healthy** — not a dead service.
2. `/root/wa/.env` `CALLHOOK_SECRET`: 24 chars, alphanumeric, **exactly one line, no run-on**. **Not** the §94.1 `.env` corruption. (Note: the initial `grep -c '^CALLHOOK_SECRET'` check was **useless** — the §94.1 damage appends junk *to* that line, so it still counts as one.)
3. No `2026-07-08.jsonl`. **Ambiguous by design** — the secret gate returns 403 **before** `raw_log()` is called, so a rejected delivery leaves no raw-log line and no journal entry.
4. **The web-server access log settled it.** `13.126.78.76`, `Go-http-client/2.0`, continuous `POST /mo-callhook?key=…` → **403**, 33-byte body — the exact length of the receiver's own `{"ok":false,"error":"forbidden"}`. MyOperator was delivering; we were rejecting.
5. Reverse-proxy config intact (`/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf:126 → 127.0.0.1:8098`).
6. Local probe with the `.env` key: **200**. Keyless: **403**. The running process held the `.env` value.
7. The panel's key was **URL-encoded**, decoding to **12 characters containing an `@`** — the **old** secret, the exact one Session 94 rotated away from (Option B was chosen specifically to remove the `@`). Single distinct key in flight (631 × length 14 encoded), md5 of the decoded value later confirmed identical to the realigned `.env` value.

## 4. Root cause
**The MyOperator panel's Call-webhook `?key=` reverted to the pre-S94 secret.** The Session-94 panel edit survived exactly one verification call and then was overwritten, reverted, or applied to only one of several webhook entries. The VPS was correct throughout; the vendor panel was not.

**Contributing cause (the reason it went unseen for 44 hours):** the receiver rejects before it raw-logs and before it journals. 4,449 rejections produced **zero** evidence anywhere the clinic's own systems look. The Session-94 detection rule for this exact fault code was written and never built.

## 5. Consequential damage
The duration gate (D77/D82) blocks the outcome dropdown until a `Call_Durations` row proves the call connected. No webhook → no row → **no staff member could file any follow-up outcome for two clinic days.** The recordings and `Call_Feed` still hold the truth of what happened; only the staff's own account of each call is missing.

## 6. Fix
Aligned the **VPS to the panel**, not the panel to the VPS — whatever rewrites the panel cannot rewrite `/root/wa/.env`, so this direction is the stable one.

1. `cp -a /root/wa/.env /root/wa/.env.bak.<timestamp>`
2. Decoded the panel's key from the access log (`urllib.parse.unquote`), verified charset, **never printed**.
3. Rewrote only the value: `awk '/^CALLHOOK_SECRET=/{print "CALLHOOK_SECRET=" ENVIRON["NEWKEY"]; next} {print}'` — **`ENVIRON`, not `awk -v`**, so no escape mangling; **not `sed` by line number**, which is what created §94.1's run-on line.
4. **Three guards before installing:** exactly one matching line (`grep -c` → 1); only the value changed (`diff` of key names → empty); identical line counts (32 → 32).
5. `\cp -f`, `chmod 600`, `systemctl restart call-hook.service`.
6. Verified: service `active`; local probe 200; **via-proxy** probe 200; access log 200s; `2026-07-08.jsonl` created; `Call_Durations` rows landing with real talk-times.

**The clinic is now running on the OLD 12-character `@` secret.** This is a deliberate, temporary trade — service restored in minutes without depending on a vendor UI that has already reverted once. Proper rotation, on **both** ends, verified across a full clinic day, is on the backlog.

## 7. What changed as a result
- **D156** — the duration gate now **fails open** when it cannot *measure* a call. A verification mechanism may never again stop a staff member from recording what a patient said. (`Dashboard.html` v18.19, deployed and confirmed.)
- **Diagnostics Spec v1.6, Category 5 — "rejected-at-the-door".** Any component that authenticates an inbound request must count and log its rejections. A gate that refuses silently is indistinguishable from a world that never called.
- **Verification standard hardened.** One real call **and** a re-check ≥1 hour later on the same clinic day. Session 94's "verified end-to-end" rested on a single immediate call and was dead in seven minutes. **An incident is closed by a successful re-test, not a successful test.**
- **Detector specced** (Diagnostics Spec §NEW-E) and made the top diagnostics task.

## 8. Still open
- The detector is **not built**. The next 403 will also be found by a receptionist.
- **Nobody knows what reverted the panel.** Leading suspicion: more than one Call-webhook subscription, only one of which was updated in S94. Must be checked.
- `CALLHOOK_SECRET` rotation, both ends, verified across a clinic day.
- Re-check the webhook **≥1 hour** after the 08-Jul fix, and again on the morning of 09-Jul.
