# S525_SPINE_RED_FAST — the spine's red on the health page within the hour (F-849)

Kit of session 305 (the parent), 11-Oct-2026. Numbers claimed on the System Board (`_numbers` v352): kit S525, F-849.

## Why

The Marg item spine's gate failed on **08-Oct 09:10** and kept failing (the Sanjeevni chat found it on 11-Oct; its kit
S524 repairs the spine itself). The health page's leg for it *did* go red — the portal's "33 of 34 feeds fresh" was this
leg — but **two days late**: the leg judged only the age of the last good build against 26 hours, and the collector ran
once a day at 08:05, so the failure was 23 hours old (green) at 09-Oct 08:05 and first shouted on 10-Oct 08:05.

## What it does

1. The leg *Marg spine gate (S331)* also reads the state file's own `last_failure_iso`. When that is newer than
   `last_success_iso` — the newest build failed — the leg is red at once, and the words on the page, in the table and in
   the phone message say *newest build FAILED; last good … ago*. Any other state-file leg can opt in the same way (`fail_field`); none else does yet.
2. The collector (`freshness.py --shout`) also runs at **:35 every hour, 09:00–23:00**. The page and the portal's line
   are then never more than an hour old in clinic hours. Its phone message stays **once per leg per calendar day**.

| file | from | to |
|---|---|---|
| `/root/finance/freshness.py` | `66d93a631c6c46ebb6536620450efa74` | `83865d94df3d9c1f1550964f7840f253` |
| `/root/finance/freshness_legs.json` (in the kit: `freshness_legs.json.kit`, since the repository ignores `*.json`) | `716734aef3bcacdef54d0172a00440e2` | `9df66934e0df2bf3771ffeb517312674` |
| root crontab | — | one line added, tagged `S525_FRESH_HOURLY` |

Not touched: the spine and its state file (only read), every other leg, the ntfy address (the conf is never opened by the
walk), any service (nothing restarts).

## Proven before the publish

- `walk_s525.py`, on the 11-Oct bundle's 34 legs: **48 checks** — the old and new collectors read every leg alike except the
  one that names its failure field; made-up state files for each case (the newest run failed an hour after a good one →
  red now, and the old file calls the same state green; no failure recorded; an unreadable value → ERROR; a leg that does
  not opt in; an old success). Two negative controls red (the judgment taken out; the legs file without the field).
- The installer rehearsed on a made-up root: dry, green, pasted twice, a wrong pin, red after placing (both files and the
  cron line put back).

## Independent review

One fresh reader: nothing blocking. Taken in: the FAILED words now reach the page, the table and the phone message (they
were only in the JSON); the crontab is written from a file copy of itself and put back from that same file, never
through a pipe that could empty it; the collector's one run at install waits out its own minutes (08:05, :35).
Noted, not changed: a half-done install (files new, no cron line) is refused with the pin message — paste the undo line
first; and the daily all-green message can now come in the afternoon after a red morning (still once a day).

## Install

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S525_SPINE_RED_FAST/install_S525_SPINE_RED_FAST.sh
```

`DRY=1` before `bash` runs every gate and the walk and writes nothing. Pasted twice, it says ALREADY INSTALLED.

## Undo

```
\cp -p /root/finance/freshness.py.bak_S525_66d93a63 /root/finance/freshness.py && \cp -p /root/finance/freshness_legs.json.bak_S525_716734ae /root/finance/freshness_legs.json && crontab -l > /root/finance/crontab.undo_S525 && grep -v '# S525_FRESH_HOURLY$' /root/finance/crontab.undo_S525 > /root/finance/crontab.undo_S525.new && crontab /root/finance/crontab.undo_S525.new
```
