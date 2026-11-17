# S860_WA_APPROVE_PARKED — the old WhatsApp approvals service switched off and kept (the parent, S478, 17-Nov-2026) — F-1364, D964

**The gap.** `wa-approve` (the oldest tick-and-send WhatsApp approvals page, port 8101) still runs although S816 retired its
tile; two tools still expect it: `clinic-doctor` lists it (`/root/deploy/clinic_doctor.py`:70 — it would restart it) and
the key swap names it a reader (`/root/wa/swap_key_s701.py`:51).

**The change.** Those two rows out (each file otherwise byte-identical; a comment says why), then `wa-approve` **stopped and
disabled**. Its unit file, code (`/root/wa/wa_approve.py`) and settings stay on disk — kept, not removed (Undo starts it again).
clinic-doctor's `--auto` already leaves a stopped-and-disabled part alone and the key swap already skips a service that is not
running; this removes the expectation itself. Nothing on any page changes.

**Proof.** `walk_s860.py` parses both files (nothing imported or run): the doctor's list is the live list less that one row,
every other row identical and in order; READERS is `clinic-portal, wa-send-api`; nothing else differs; both compile (8/8).
Control: the live files in the kit's place go red. The installer keeps both old files, places, compiles, stops and disables,
reads back `inactive / disabled` and the unit file still there; any red puts the files back and enables and starts the
service again. Rehearsed with a stand-in systemctl.

**Install** (after the publish): the S478 combined line, or alone:
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s860kit && cp -rp /root/deploy/repo/deploy_kits/S860_WA_APPROVE_PARKED /tmp/s860kit && bash /tmp/s860kit/install_S860_WA_APPROVE_PARKED.sh`
Undo: `bash /tmp/s860kit/install_S860_WA_APPROVE_PARKED.sh --undo`.
