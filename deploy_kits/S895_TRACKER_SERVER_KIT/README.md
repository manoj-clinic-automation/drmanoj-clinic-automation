# S895_TRACKER_SERVER_KIT — the Follow-up Tracker's engine on the server, installed OFF (the parent, S492, 20-Nov-2026)

Plan: `claude/S492_TRACKER_TO_SERVER_PLAN_FINAL.md` (his OK 15:31 IST 20-Nov). Session 1 of four: Replay 1 passed on his PC
(30 of 30 runs since 21-Oct identical cell for cell; `REPLAY1_REPORT_S492.txt`), this kit built and walked. Nothing runs
after the install: `/root/followup_tracker/OFF` is present. The seed, Replay 2 on the box and the readers' switch are sessions 2–3.

## What it places
- `/root/followup_tracker/` — the PC's own tracker code byte for byte (`processor.py f1c02736`, `docterz_pickup.py ddbed001` with
  S892, `revenue.py 5d8f2a71` the PC's newer one, the pushers) + `server_runner.py` (IST pinned; a flat `intake/` of the box's
  stored exports under the PC's own file names; the sends to the receiver on this box with `X-FU-Origin: server`; OFF switches).
- `/root/finance/docterz_ingest.py` — the box's `followup_tracker/outputs` read FIRST; a date the box made is never overwritten from Drive.
- `/root/wa/push_followups_vps.py` — the PC's `push_followups_today.py` (74122185) with the box's two paths: the **Do_Not_Call filter
  is back** (the box's copy had lost it; the Sheet tab was rewritten unfiltered within 5 minutes of every PC push).
- `/root/wa/followup_receiver.py` — logs who uploaded (`.uploads.log`), marks `.last_pc_upload` for any upload not the server's (the red line).
- cron: the runner every 5 min and the 08:00 Patient_Master mirror — both gated by `/root/followup_tracker/OFF`.

## Install (server, one line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s895kit && cp -rp /root/deploy/repo/deploy_kits/S895_TRACKER_SERVER_KIT /tmp/s895kit && bash /tmp/s895kit/install_S895_TRACKER_SERVER_KIT.sh
```
Undo: `bash /tmp/s895kit/install_S895_TRACKER_SERVER_KIT.sh --undo` (a seeded data folder is never deleted by an undo).

## Proof
`walk_s895.py` 12/12 on a made-up root (control: the live ingest goes red on the same scene); `server_runner.py --selftest` 13/13;
`rehearse_s895.sh` on a made-up root: install green, install again refused, undo, red rollback (receiver silent), tampered kit refused.
