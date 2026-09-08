# S232_MORNING_DIGEST — one push a morning

**BUILT AND PROVEN OFFLINE. NOT INSTALLED, and it should not be installed yet:**
`S232_NOTIFICATION_LAYER_PLAN` §6 puts the digest at **⭐6, after the WABA rotation.** It is
finished and waiting, which is the point — when the rotation clears, this is one line.

## What it is

**An assembler, not a sensor.** It creates no instrumentation and measures nothing itself. Every
figure is read from something that already runs:

| block | source | already exists because |
|---|---|---|
| **1 · NEEDS YOUR WORD** | `/root/staff_ledger/ledger.jsonl`, rows with `status == PENDING` | the maker–checker chain has worked this way since S155 |
| **2 · STOPPED OR STALE** | `/root/finance/freshness.json` | the 08:05 job writes it every morning (S230) |
| **3 · WAITING ON SOMEONE ELSE** | `/root/finance/digest_waiting.txt` | a file the owner edits; no deploy |
| **4 · ALL FRESH — n ✓** | `freshness.json` again | his own ask, S231: *"better if it lists all it checks with check marks"* |

## What it looks like — the two mornings that matter

**The ordinary one, and the title alone answers the question:**

```
Clinic 08:15 - nothing needs you, 26 of 26 fresh
```

**The one worth opening:**

```
Clinic 08:15 - 3 need you, 24 of 26 fresh

NEEDS YOUR WORD
  - Surendra - advance issue Rs 13000 [SPECIAL]
  - Darpan - advance issue Rs 15000
  - Shavez - night duty Rs 600
  https://followup.dr-manoj.in/ledger/

STOPPED OR STALE
  - clinic day revenue ingest: stale, 4 days 2 hours
  - Marg purchase feed: never, never seen
  https://followup.dr-manoj.in/finance/freshness

WAITING ON SOMEONE ELSE
  - Ms Khushi Jain, MyOperator - do the old and new WABA tokens overlap?
  ...

FRESH - 24 of 26 (the other 2 are above)
  [x] clinic state backup (off-box)
  ...
```

## Six decisions taken rather than asked

1. **08:15, not 08:05.** `freshness` runs at `5 8 * * *`. A digest at 08:05 races it and reports
   **yesterday's** result about half the time, silently. Ten minutes later it reports the run that
   just happened. Cron: `45 2 * * *` UTC.
2. **The topic is NOT in this kit's conf.** It is read from `freshness.conf`, so the box keeps
   exactly one copy of it (**F-358**).
3. **IST is fixed in code, not taken from the box.** A rebuilt or relocated server cannot silently
   retime his morning.
4. **A missing source is NAMED in the push, never omitted.** *"could not read the ledger"* goes out.
   A digest that quietly drops a block it could not read re-creates the exact fault the daily-green
   line was built to end: **quiet meaning healthy and quiet meaning never-ran, indistinguishable.**
5. **"ALL FRESH" only when it is all of them** — otherwise *"FRESH — 24 of 26 (the other 2 are
   above)"*. Saying "ALL FRESH — 24 of 26" is the small kind of wrong that teaches a reader to stop
   trusting the heading.
6. **Plain text, no markup, ASCII title.** ntfy sends Title as an HTTP header and a non-ASCII header
   breaks the push. And his stated fallback — *"I copy the message and share it with you in a
   chat"* — has to work with nothing built. It does.

## Proof

- **selftest 29/29.** Fixtures cover: nothing present · a quiet morning · a busy morning · a
  malformed ledger line · an APPROVED row that must NOT appear · the once-a-day guard on and off ·
  and IST across the UTC date line.
- ✎ **One check was rewritten because it could not fail.** It read `hhmm(x) == hhmm(x)` — true on
  any machine in any zone. It now compares against constants, and **it failed on its first run**
  (wrong year in the fixture) before it passed. *A selftest that cannot fail is not a test.*
- **Live-shape walk:** run against a fixture carrying **the real 26 leg names** from
  `S230_FRESHNESS/legs.json`, with `clinic day revenue ingest` stale at 4 days (its real S231
  reading) and a `NEVER` leg. Both mornings above are that walk's actual output, read and not
  assumed. **Two wording defects were found by looking at it** — `"1 need you"`, and `"ALL FRESH"`
  over a number that was not all of them.
- `py_compile`: OK.

## To install, when ⭐4 clears

```
\cp /root/deploy/repo/deploy_kits/S232_MORNING_DIGEST/morning_digest.py /root/finance/morning_digest.py
```

then the conf and the waiting file from the two `.sample` files, then one cron line at `45 2 * * *`.
**Run it once with `--dry-run` first and read it** — the title is the product, and it is the only
part of this that cannot be judged from code.

## The two-week trial it is built for

Exactly **one** scheduled push a day. Unscheduled pushes only for *something stopped* or *a WhatsApp
message arrived*. **The number to watch is unscheduled pushes per day: above roughly three, the
thresholds are wrong — not the idea.** Priority levels, never new topics: every extra topic is
another subscription that can silently go dark, which is what happened to four devices at S231
(**F-367**). **And the real test is behavioural: if he is still opening it in week two, it stays.**

---
*S232_MORNING_DIGEST · built 08-Sep-2026 · staged, not installed · ⭐6 in the build order.*
