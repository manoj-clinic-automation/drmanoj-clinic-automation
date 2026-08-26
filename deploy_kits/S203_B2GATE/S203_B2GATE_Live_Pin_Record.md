# S203_B2GATE — B2 HAD NEVER REPORTED. LIVE PIN RECORD.

| file | machine | was | now |
|---|---|---|---|
| `finance_app.py` | VPS `clinic-finance`, `/root/finance/` | `50ac4c86a3985bf82269d650d5e46f0f` | **`374a0b82803068bb52e43ab9a921c1e9`** |

Applied 26-Aug-2026 18:51 IST. Smoke **719/719 before and after** — unchanged, correctly,
because a path was added to an exemption and no test was added. Backup
`finance_app.py.bak_S203_B2GATE_20260826185148`. Service restarted, `active`.

**Proven from the server itself:** a POST to `/finance/api/pipeline-status` carrying the
server's own `FINANCE_MARG_TOKEN` returned `HTTP 401 not_signed_in` before, and
`HTTP 200 {"ok":true,"received_at":"2026-08-26T18:52:00"}` after.

> **`verify_live_pins.py` will now report drift 1 on `finance_app.py`, and it is right.**
> The Register still pins `50ac4c86…`; updating it is a close action.

## What was wrong

`_gate()` is a `before_request` that FAILS CLOSED and hands out exactly three token
exemptions, each naming **one literal path**: the cron token (any path), `MARG_TOKEN` for
`/finance/api/marg-push`, and `RENEWALS_TOKEN` for `/finance/api/renewals-push`.

**`/finance/api/pipeline-status` was added at S202 and never added to that list.** So every
real post from manojz was refused 401 by the gate before `api_pipeline_status()` ran. The
route's own token check — correctly written, defence in depth — was **unreachable dead
code**. B2 was built so the clinic server could see the two Windows machines, and it has
**never once reported**.

Fix: the marg-push clause now names both paths. Same token, same header, and the route
still touches nothing but its own append-only table.

## WHY THE SMOKE SUITE PASSED — the part worth keeping

The suite does test this route, and it does send the header:

    _r = c.post("/finance/api/pipeline-status", json=_pl,
                headers={"X-Finance-Marg": _B2TOK})
    check("B2: a good post is accepted", _r.status_code == 200 ...)

**But `c` is a SIGNED-IN test client.** So `_gate()` let the request through on the
**session**, never on the token, and the token path was never exercised. The real caller
has no session at all.

The check above it is worse: *"an unauthenticated pipeline post is REFUSED"* passes with
401 — but from the **route's** token check, not the gate, because the session had already
carried it past the gate. **Both checks passed for reasons other than the ones they name.**

And the token substitution is only half applied: the test sets
`os.environ["FINANCE_MARG_TOKEN"]`, while `_gate()` reads the module-level `MARG_TOKEN`
bound at import. So even a signed-out client would not have exercised the real path.

**RULE: a test must post the way the caller posts. A signed-in client testing a
token-authenticated route proves nothing about the token.** This is the S202 family —
a monitor wired so it could only report success — one layer further in, and the third
instance of AF-2's shape.

## How it surfaced

Only because `S203_R2` gave the pull a log twenty minutes earlier. The error had printed
on every pull since S202 and gone to a console the hidden launcher discarded.
**Three faults, one chain, each visible only because the one before it was fixed.**

## Owed

A selftest check that posts with the token header and **no session**, against the module
`MARG_TOKEN` — the test that would have caught this at S202. Drafted, not yet applied.

---

## FINAL STATE, 26-Aug-2026 19:05 IST

`finance_app.py` moved **twice** tonight. Both recorded as they moved (F-97):

| step | md5 | what |
|---|---|---|
| was | `50ac4c86a3985bf82269d650d5e46f0f` | S202 close |
| B2 gate fix | `374a0b82803068bb52e43ab9a921c1e9` | `pipeline-status` added to `_gate()`'s exemption |
| B2 test added | **`7948cee0e00494bbee30de1c51d03d74`** | smoke 719 → **721** |

Verified at 19:05: md5 matches, the gate lists **both** paths, and a live POST with the
server's own token returns **HTTP 200**. Backups kept:
`finance_app.py.bak_S203_B2GATE_20260826185148` and `...B2TEST_20260826190026`.

**`verify_live_pins.py` will report drift 1 on `finance_app.py`. It is right** — the
Register still pins `50ac4c86…`. Updating it is a close action.

## TWO OF MY OWN FAULTS, RECORDED

**1. The added test does not bite.** Reverting the gate and re-running gave **721/721** —
the two new checks passed against code that was broken. The projection said one should
fail; it did not. Most likely the smoke suite stubs authentication globally, so there is
no anonymous client inside it — **which is also why the original S202 test passed on an
unreachable route.** The check is therefore *green and meaningless*, and is recorded as
such rather than left looking like coverage.

**OWED: read how the suite establishes auth, then write a check that genuinely exercises
the token path with no session.** Until that exists, this class can still ship unreachable.
`check()` counting +2 is not evidence; the red-proof is, and it failed.

**2. `trap restore EXIT` was pasted into an interactive shell**, where it fires only when
the session closes — not when the commands finish. So the reverted file sat on disk while
I believed it had been restored. The service was never restarted, so nothing broke, but a
restart in that window would have loaded the broken gate. **RULE: a rollback in an
interactive paste must be an explicit command, never a trap.**

---

## PROVEN END TO END FROM THE REAL CALLER — 26-Aug-2026 19:17

Not a curl from the server. The actual 10-minute pull on manojz, in its own console log:

    pipeline_status: post failed (HTTP Error 401: Unauthorized)   <- before 18:51
    pipeline_status: 200 (token from medical PC (live))
    pipeline_status: 200 (token from medical PC (live))
    pipeline_status: 200 (token from medical PC (live))

Three consecutive successes, including the **scheduled** runs at 19:10 and 19:17 — so it
is the task, not a hand-run. Outcome log: `18:59 ok · 19:00 ok · 19:10 ok · 19:17 ok`.

**The clinic server can now see the two Windows machines.** That was B2's entire purpose,
built at S202, and until 18:51 today it had never once delivered.

Incidentally settled: the ten-minute scheduled task fires normally. An earlier gap in the
log was simply the interval, not a stopped scheduler — recorded because "the task may not
be running" was a live worry for twenty minutes and the log disproved it.

## The chain, which is the session's real result

1. The pull kept **no log**, so nothing could be seen — S203_R2, 18:38.
2. Its **first** log ended with a 401 that had printed on every pull since S202 and been
   discarded every time — visible 18:44.
3. That traced to `_gate()` naming `marg-push` and never being told about
   `pipeline-status` — fixed 18:51, HTTP 200.
4. And it shipped broken because the smoke suite tested the route **with a session**,
   while the real caller sends a **token header** — a shape no test exercised.

**Each fault was only visible because the one before it was fixed.** Three faults, one
root cause: nothing was watching the watcher.
