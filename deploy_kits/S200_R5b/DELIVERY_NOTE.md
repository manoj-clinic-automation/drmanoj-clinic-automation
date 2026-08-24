# S200_R5b — the settings page accepts -1 (derive) for the Sunday weight

## The fault (mine, caught by the validator doing its job)
R5 shipped `sunday_weight_override` with -1 as the documented "derive from the shift" sentinel —
but the settings validator refuses ANY negative number, so the whole settings form (including
setting ENFORCE FROM = 2026-07) could not be saved. Blocked exactly at the go-live switch.

## The fix
ONE file: `/root/staff_register/salary_policy.py`
`4521f1a6320893ac24039dce5861131f` → `260944bf8493783ec102cbdd286db8c6`

`save_settings` now treats `sunday_weight_override` specially: **-1 (derive) or 0..1 (forced)**;
anything else refuses with its own message. Every other numeric key still refuses negatives.

## A second fault caught DURING this build, worth its own line
The first draft of the new selftest exercised the save path against the REAL settings file and
would have left `sunday_weight_override = 0.5` FORCED on the box — silently killing the derived
weights (Pravesh 0.56, Darpan 0.524). Rewritten: the test snapshots the settings file and
restores it byte-for-byte in a finally-block, proven by a residue check.
**Lesson: a selftest that writes a live store is itself a live event — snapshot and restore, or
don't touch it.**

## Install
    cd /root/deploy/repo && git pull
    bash /root/deploy/repo/deploy_kits/S200_R5b/INSTALL_S200_R5b.sh

Then the settings page again: everything as you had it, ENFORCE FROM = 2026-07 → Save — it will
take this time. Then the flow → approve both sheets → LOCK.
