# S897_TRACKER_SEED_REPLAY — the tracker's move, session 2: the seed, Replay 2 on the box, the red line, the Docterz-reports door (the parent, S493, 20-Nov-2026)

Plan: `claude/S492_TRACKER_TO_SERVER_PLAN_FINAL.md` (his OK 15:31 IST 20-Nov; "continue your work in next session" 16:48). Session 2 of four.
**Nothing switches:** `/root/followup_tracker/OFF` stays; the clinic PC still makes the list. The switch evening is session 3's, on his word.

## What it places
- **The seed, both halves.** `seed_pack.py` runs in the assistant's device VM against the PC's own folders (no step of his) and
  writes `TRACKER_SEED_<stamp>.zip` + `.sha256` into the tracker's Drive-synced `outputs\` — the twelve ledgers and their meta,
  `.secret_key`, the snapshots since 19-Oct (Replay 2's month), every input the state names (`uploads\`), the archive (state,
  index, console log, the KIND folders), `feed_url.txt`, the pre-S777 engine (replay only). `seed_take.py` on the box fetches the
  newest seed from the Drive folder with the box's own read-only credential (docterz_ingest's), checks the sha256 and the
  manifest, translates the PC's paths in `_pickup_state.json` (`seen[].archived`, `days[].input`) and `index.csv` to the box's,
  refuses when any does not resolve, and places `data/` (700/600), `uploads/`, `archive/`, `feed_url.txt`, `replay/`; `SEEDED_AT`.
  It refuses while `SWITCHED_AT` exists or `OFF` is absent; a second seed needs `--again` and sets the first aside whole.
- **Replay 2** — `replay2_s897.py`, S492's harness pointed at the seeded folder with the venv's Python: the last run of each day
  since 19-Oct against the workbook the PC uploaded that evening (the receiver's inbox), the data files against the next
  snapshot. Report `logs/REPLAY2_REPORT.txt`; counts on the screen.
- **The red line** — `pc_upload_watch.py` (cron every 10 min, not gated by OFF) + one leg in `freshness_legs.json`
  (`clinic PC still sending after the switch`, S830's state_json/fail_field shape): green 'not switched yet' until
  `SWITCHED_AT` exists; red when the receiver's `.last_pc_upload` is newer than the switch (26 h window); red when the watcher stops.
- **The door** — `/root/finance/docterz_door.py`, the owner page `/finance/console/docterz-reports` (the console's gate),
  mounted from `owner_console.py` beside the off-days page, with one console line that opens it. Any Docterz CSV, recognised by
  its columns: a consultation report cut into business days through `docterz_pickup.take` (the box's reader, S443/S868 rules), a
  follow-up log and a clinical data report whole, a patient list kept by its bytes (`docterz_exports/patientlist/`, absorbed in
  a later session). Counts back; the four 'reaches' lines; every export of every road listed. No dialogs (F-1464).

## Install (server, one line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s897kit && cp -rp /root/deploy/repo/deploy_kits/S897_TRACKER_SEED_REPLAY /tmp/s897kit && bash /tmp/s897kit/install_S897_TRACKER_SEED_REPLAY.sh
```
Undo: `bash /tmp/s897kit/install_S897_TRACKER_SEED_REPLAY.sh --undo` (the seed is never deleted by an undo).
The seed alone, later: `FUT_ROOT=/root/followup_tracker /root/wa/venv/bin/python3 -B /root/followup_tracker/seed_take.py`

## Proof
`walk_s897.py` 60/60 on a made-up root against the LIVE reader (controls red 5 on the patched files); `pc_upload_watch --selftest` 0; cold review 1 MUST + 8 SHOULD built in -> second look by the walk's new checks;
`rehearse_s897.sh` 30/30 on a made-up box (dry, install, again, undo ×2, red rollback, tampered kit, seed + replay, seed survives
an undo, moved live file, switch flag, OFF absent); the number gate clean (15 files).
