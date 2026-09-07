# S230_FRESHNESS — the freshness collector

**A green pipeline that cannot state its age is not green, it is unmeasured.**

One script reads the last-success time of every automated leg on the box, compares each
to a window, and says — once a day, in one place — what has stopped.

## Why it exists

Nothing in this estate reports its own age. Two measured examples:

* a pipeline step failed on **69 consecutive ten-minute cycles across eleven hours**,
  printing one word into a log nobody reads, while the pipeline around it went on
  reporting `ok`. Nobody knew until somebody went looking;
* a "weekly backup" has sat in cron for months and **has never in its life produced a
  single file**. The cron lines still sit there looking perfectly healthy.

This is not a dashboard and it is not a monitoring system. It is one sentence a day:
*anything that has stopped says so, the same day, in one place.*

## What it is, and what it deliberately is not

| it does | it deliberately does not |
|---|---|
| read the last-success time of each declared leg | judge whether the work was *correct* — only whether it happened |
| compare that time to a window and give a verdict | restart, repair, re-run or nudge anything, ever |
| write one JSON, one HTML page, one summary line, one state file | write to, move, truncate or signal any other service's files |
| push ONE consolidated message when something is not fresh | push again about the same leg the same day |
| keep going when a leg is unreadable | stop the other forty because one is broken |
| watch itself | pretend it is watching legs nobody declared — see `legs.json` |

**It is strictly read-only against everything it watches.** Databases are opened
`file:...?mode=ro` with `uri=True` and `PRAGMA query_only`. Logs and files are stat'ed.
The only paths it ever writes are its own: the state file, the summary log, the JSON and
the HTML. There is no mode, flag or code path in which it touches a watched file.

## The verdicts

| verdict | what it means | what to do |
|---|---|---|
| **OK** | it succeeded inside its window | nothing |
| **STALE** | it ran once, but not recently enough | look at that job's own log |
| **NEVER** | there is no sign it has EVER run — no file, no rows, no state | the cron line is fiction: fix the job, or delete the line and the leg |
| **ERROR** | the collector could not read the target — bad JSON, a missing table, a mis-declared leg | fix the leg's declaration, or the file it points at |

`NEVER` and `STALE` are never merged. "It stopped last Tuesday" and "it has never worked"
are different problems and want different mornings.

## How to add a leg — this is config, never code

Edit **`legs.json`** on the box (`/root/finance/freshness_legs.json` after install) and add
one object to the `legs` list. Nothing else changes; `freshness.py` is never edited to
learn about a new job:

```json
{ "name": "vendor csv push", "group": "Marg lane", "kind": "log_mtime",
  "target": "/root/marg/push.log", "max_age_h": 26,
  "note": "shown under the name on the page" }
```

Fields: `name` (unique), `group` (the page heading), `kind`, `target`, `max_age_h`,
optional `note`, optional `"disabled": true` to **park** a leg without deleting it — a
parked leg is not read, and is listed on the page under "Parked" so it cannot be
forgotten. `{STATE_FILE}` in a target expands to the collector's own state file.

The five kinds, and no more:

| kind | target | extra fields | reads |
|---|---|---|---|
| `state_json` | a JSON state file | `field` (default `last_success_iso`) | the ISO timestamp in that field |
| `file_mtime` | one file | — | its mtime |
| `log_mtime` | one log file | — | its mtime (a log written every run is a heartbeat) |
| `glob_newest` | a glob | — | the mtime of the newest match |
| `sqlite_max` | a database file | `table`, `column` | `SELECT max(column) FROM table`, read-only |

After editing, prove the file before it matters: `freshness.py list` re-reads the
declarations, prints them, and touches nothing at all.

**Windows.** 26 h = a daily job with slack for a late start. 50–74 h = something allowed
to be quiet over a closed Sunday. 200 h = weekly. 4400 h = the twice-yearly restore drill.
Every window on a leg whose cadence was not confirmed on the box carries a `note` saying
so: after one week of the page, widen whatever cries wolf and tighten whatever hid a real
stop. A window that is too wide still catches the failure the same week; a window that is
too tight trains everyone to ignore the message, which is where we started.

## The conf — `/root/finance/freshness.conf`, chmod 600

| key | needed | default | what it is |
|---|---|---|---|
| `LEGS_FILE` | no | `legs.json` beside the script | the declarations |
| `STATE_FILE` | no | `/root/finance/freshness.state.json` | its own age, and the shout record |
| `JSON_OUT` | no | `/root/finance/freshness.json` | every leg, machine-readable |
| `HTML_OUT` | no | `/root/finance/freshness.html` | the owner-facing page |
| `SUMMARY_FILE` | no | `/root/finance/freshness.summary.log` | one line per run |
| `NTFY_URL` | for `--shout` | none | **the private topic URL — a secret.** It lives here on the box, never in git, never in `legs.json`, never in chat (F-185). Without it, `--shout` says what it *would* have sent and pushes nothing |
| `NTFY_TITLE` | no | `Clinic freshness` | the push title |
| `SHOUT_MAX_LINES` | no | `12` | lines per message; the rest are "and N more on the page" |

## Modes

```
freshness.py            # check: read every leg, write the outputs, print the table
freshness.py --shout    # check, and push ONE message if anything is not fresh
freshness.py list       # print the declarations. Reads no target, writes no file.
```

Exit codes: `0` every leg inside its window · `1` something is STALE / NEVER / ERROR ·
`2` usage · `11` the legs file is missing or unreadable.

## The cron

```
5 8 * * * /root/wa/venv/bin/python3 /root/finance/freshness.py --shout >> /root/finance/freshness.log 2>&1
```

**08:05**, five minutes after the 08:00 health report, so one morning message covers the
whole estate. Once a day is the point: the suppression record in the state file is keyed
by leg **and calendar day**, so running it more often (by hand, or on a tighter cron) can
never produce a second message about the same leg the same day. A leg that recovers and
goes stale again tomorrow shouts again tomorrow.

## Rollback

```
crontab -l | grep -v 'freshness.py' | crontab -
```

That is the whole rollback. Nothing else on the box was changed by this kit, so nothing
else has to be undone; the files can stay where they are, inert.

## It watches itself

The last leg in `legs.json` is the collector reading its own state file. That row shows
the **previous** run — state is written after the reading is done, which is the only order
in which the row can ever be honest. If the collector itself dies, its own row goes STALE
on the page, and the page's "generated" line stops moving. A freshness checker that has
quietly stopped is the worst possible failure of this design, so it is on the page like
everything else.

## Two things to expect on the first run

* **A lot of NEVER.** That is not a bug in this kit — it is the estate answering the
  question for the first time. Each NEVER is either a job to fix or a cron line to delete.
* **The two Marg legs** read `stock_feed.received_at` and `purchase_feed.at` in
  `finance.db`. Both tables are created lazily by the stock and purchase apps on first
  use; if either has not been created on this box yet, its row reads `ERROR: no such
  table` — park it with `"disabled": true` until the app has run once. If you would rather
  watch arriving purchase exports than the pull's heartbeat, `purchase_export.received_at`
  is the alternative column, and changing to it is an edit to `legs.json`.

## Proof

`WALK_freshness.py` builds a fixture estate in a temp directory — real state files (fresh,
stale, malformed, missing-field, empty-field), logs with mtimes set to the hour, a glob of
several files, a real sqlite database, a parked leg, an unreadable path — and drives the
real functions through it. No network: the push is stubbed and the walk asserts on exactly
what would have been sent. **115 checks, all green**, including: every kind reads
correctly; each verdict comes only from the condition that must produce it; one bad leg
does not stop the rest; the parked leg is skipped; the once-a-day suppression holds across
two runs and releases the next day; a failed push is not recorded as sent and is retried;
the page names every leg and references no external asset; the state file records the run's
own timestamp; the watched database is byte-identical after the run.

```
python -B WALK_freshness.py
```

*S230_FRESHNESS v1 · built offline, not installed. No patient data, no numbers, no ids, no
tokens, no key paths in any file of this kit (F-185).*
