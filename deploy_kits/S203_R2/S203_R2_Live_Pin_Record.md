# S203_R2 — LIVE PIN RECORD

Recorded as they moved (F-97).

| file | machine | was | now |
|---|---|---|---|
| `PULL_FROM_MEDICAL.bat` | manojz, `D:\Downloads\margsync\MargPull\` | `92f03999d0a14d00b7f552dbb4d44c05` | **`cfb8b13d028a3bdc69a70701056392ec`** |
| `PULL_HIDDEN.vbs` | manojz, same folder | `9a3ba9ba3bb7376bd166f12624d282c3` | **`084fc4523b0e855c8d29b54c144bb60b`** |

Installed by the owner **26-Aug-2026 18:38 IST**. All seven gates passed, including the two
that are real runs: a live pull that wrote `END 26-08-2026 18:38:33.33 -- ok`, and the
hidden launcher, which produced a **41,120-byte** console log. Both files re-hashed after
install and verified independently afterwards.

## What it fixed

`-- ok` was written unconditionally on a straight-line path with no error test above it.
`pipeline_status.py:122` computes `ended_ok` as *"a line starts with END and ends with
ok"* and posts that to the clinic server — **so the server was told the pipeline was
healthy by a word that was always written.** On 26-Aug the feed was dark for 8h40m and this
said `ok` every ten minutes. The word is now earned; a failed step writes
`-- PROBLEM: capture=1` and names itself. `pipeline_status.py` was deliberately not
touched — it stops reporting `ok` by itself, because the word is gone.

And the pull kept **no log at all**: the hidden launcher discarded every line it printed.
Now `_logs\pull_YYYY-MM.log` (one outcome line per run) and
`_logs\pull_console_YYYY-MM.log` (everything), monthly.

## IT PAID FOR ITSELF IN ONE RUN — F-194 candidate

The first console log this pull has ever produced ends with:

    pipeline_status: post failed (HTTP Error 401: Unauthorized) - the pull is unaffected

**B2 — built at S202 so the clinic server could see the owner's machines — is being
rejected by the server.** In the *same run*, `marg_gate.py send` posted successfully with
the *same token*, resolved by the *same function*, in the *same header*:

| | endpoint | result |
|---|---|---|
| `marg_gate.py` | `POST /finance/api/marg-push` | **accepted** |
| `pipeline_status.py` | `POST /finance/api/pipeline-status` | **401 Unauthorized** |

Both send `X-Finance-Marg: <token>` to `followup.dr-manoj.in`, and `pipeline_status.py`
calls `marg_gate.resolve_token()` — D349's one-token rule. **The only difference is the
path.** 401 rather than 404 means the route exists and its own auth check refuses the
token.

**This message has been printed on every pull since B2 was installed and thrown away every
time**, because the launcher discarded stdout. Whether B2 has *ever* posted successfully is
**not established** — and if it has not, this is the third instance of AF-2's shape: a
monitor that was born dead and showed nothing wrong because nothing could read it.

**Not fixable from manojz.** It needs the VPS route's auth check read. Owed.
