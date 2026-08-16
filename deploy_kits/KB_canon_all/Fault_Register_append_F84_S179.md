# FAULT / ACTION REGISTER — APPEND (F-84 · Session 179)

*Append artefact, not a canonical row. Merge into `Fault_Action_Register` at next apply → v2.17
carries F-82 + F-83 (S177 append) **and** this F-84. Full narrative also in Archive §S179.*

---

## F-84 — Three self-found security faults in the finance module: the offline-testing shortcut was the vulnerability (OPEN → FIXED, S179)

**Severity:** high (auth bypass reachable in production for ~2 min on an unpublicised path; header
identity was full control, not a leak). **Status:** all three FIXED and installed this session; the
installer auto-rolls-back if the epoch check fails. Recorded as a lesson to carry, not an open risk.

**Owner did not flag these — I found them after the first install, on my own review.** All three had
the **same shape:** something that made development or offline testing easier, carried into
production without asking "what does this let a stranger do?"

1. **Reads were ungated.** Identity was checked only on writes, so `/finance/api/tile`, `/month`,
   `/day` and the patient lines were readable by anyone with the URL.
   *Fixed:* a **fail-closed `before_request` gate** over an allow-list (`PUBLIC_PATHS`), so a route
   added later is protected without anyone remembering to gate it.

2. **Identity came from spoofable HTTP headers in production.** `X-Clinic-User` / `X-Clinic-Role`
   were an offline-testing convenience that reached prod; `curl -H "X-Clinic-Role: checker"` would
   have approved days and run the cutover. That is control, not a leak.
   *Fixed:* the real `clinic_sso` signed cookie is authoritative; header auth is off unless
   `FINANCE_ALLOW_HEADER_AUTH=1` (the systemd unit states in plain words why it must never be set).
   Tightened further: *signed in ≠ entitled* — a valid clinic login with **no `unit_role` row on
   `medical`** gets 403, so the manager cannot read the pharmacy's cash.

3. **The epoch was never checked.** `verify_token` ran with `current_epoch=None`, so **"Sign out
   everywhere" revoked sessions in the portal, ledger and asset app but NOT here** — a revoked token
   still opened the books. Found only because a stale epoch threw a 403 on `/portal/users` and the
   diagnosis exposed the asymmetry.
   *Fixed:* read the epoch from `clinic_users.get_epoch(clinic_users.DEFAULT_STORE)` on **every**
   request (never cached — a cached epoch keeps revoked sessions alive for the cache's life) and
   **fail closed** if it cannot be read, exactly as the portal does. `healthz` exposes
   `sso_epoch_ok` so a lockout is diagnosable without a cookie, and the installer rolls back
   automatically if that flag is false after restart.

**THE LESSON WORTH KEEPING:** *the offline testing shortcut was the vulnerability.* Anything that
grants identity for convenience must be **opt-in**, and the production default must be **closed**.

**A fourth, smaller lesson (a test defect, not a prod fault):** one install was rolled back by its
own gate because a *test asserted an environment accident* ("the epoch is unreadable here") rather
than a behaviour. Tests must assert what the code **does**, not what the machine happens to look
like. The replacement forces the epoch to be unreadable and **requires refusal** — deterministic on
any box.

**Prevention now standing:** fail-closed `before_request` allow-list on every new Flask surface;
identity only from the signed SSO cookie in prod; per-unit entitlement is the sole authority (broker
role grants nothing); epoch read live and fail-closed; `healthz` surfaces `sso_epoch_ok`; installer
gates on it. Extends F-63 (route-gate testing) and F-68 (same-origin serving).

*Fault append — F-84 · Session 179. Next free finding: F-85.*
