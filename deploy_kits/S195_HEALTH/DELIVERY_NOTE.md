# S195_HEALTH — is anything wrong right now?

On 21-08-2026 the Marg push started failing at 20:51 (HTTP 401). Nobody noticed for
over an hour: the sender printed REFUSED on a screen no one was watching, and the Hub
looked perfectly normal. This closes that gap.

## What it adds
- **`/finance/health`** — a one-screen status page (checker only).
- **`/finance/api/health`** — the same as JSON.
- **The portal tile tells you.** When a check is red, the checker's tile subtitle on
  the portal home is replaced with the warning — so it reaches your first screen
  **without any change to the portal app**.

## The five checks
| Check | Red when |
|---|---|
| Marg report | nothing received for >36 h (warn at >26 h); also shows pushes waiting for your Apply |
| Days filed | a weekday in the last 7 is not filed (Sundays skipped); warns if filed but not approved |
| Cash position | books vs the last physical count; warns if the count is >45 days old |
| Flags (30 days) | any raised — a note, not an alarm |
| Backup | newest verified copy older than 36 h |

Read-only. No schema change. Cheap enough to run on every tile render.

## Install
```
cd /root/deploy/repo && git pull
cd deploy_kits/S195_HEALTH && bash install_s195_health.sh
```
Currency-gated to `f25ed489…`; backs up, compiles, runs `--selftest` (all-green and
not shrunk), restarts, rolls back on any red. New md5: `218cf977cc678f28706bf14b0e293201`.

## Owed
Selftest checks for the new endpoints were NOT added (built late at night; the
installer's existing gate protects the deploy). Worth adding next session so the smoke
count grows with the feature, per the project's usual discipline.
