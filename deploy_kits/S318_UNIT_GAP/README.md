# S318_UNIT_GAP

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S318_UNIT_GAP/install_S318_UNIT_GAP.sh
```

## Why

S317's first live run (18-Sep, 19:50 IST) read every `*.wants` enable symlink on the box. Eleven
enabled units matched none of the bundle's four patterns, so their unit files were **in no store at
all** — including `staff-register.service` and `assetapp.service`, whose *code* the bundle has carried
for months, and the two `call-*` **timers** whose services were already carried.

## What it does — two parts

**1 · Carries the estate's other units.** A **second** entry for `etc/systemd/system`, never an edit to
the first, so nothing carried today can stop being carried (the file's own S273 precedent):

```
call-*.timer · staff-*.service · assetapp.service · attlistener.service · attendance-*.service
```

Seven more files: both `call-*` timers, the staff register, the staff ledger, the asset app, the
attendance listener and the attendance dashboard. Masking is untouched, and the selftest proves a
**newly** carried unit's `Environment=` value is masked rather than shipped (F-518).

**2 · The gap reports itself.** `unit_state.txt` gains a section naming every enabled unit **of ours**
that the bundle does not carry:

```
[enabled, ours, and NOT carried by this bundle: N]
```

After this kit it reads the four units awaiting the owner's ruling (`email-agent.timer`,
`fitlog.service`, `gutlog.service`, `rxguard.service`) and then zero once those are ruled on. The
morning anyone adds a service without telling the bundle, it reads one. Only ours are named — a
nightly list of the hosting panel's forty-one would be wallpaper inside a week (the S195 ruling) —
and the rest are counted.

## Proof

`selftest_s318.py`, on a **copy of the live file** against a fake root shaped like the real box:
**28 checks**. Among them: the original patterns are still there and there are now two entries, each
of the six new kinds is carried where it was not before, nothing previously carried was dropped, a
newly carried unit's secret is masked and `BUNDLE_INFO` names what was masked without the value, the
gap section names the unit of ours that no pattern matches and does **not** name the one that is not
ours while still counting it, and the tarball verifies against its own manifest.

Three negative controls: the widening removed (the staff register is not carried **and** the gap
section names it), `OURS` emptied (the gap can name nothing).

**Live-shape walk.** The 18-Sep 01:35 bundle unpacked as a root, with the box's real 66 enable
symlinks recreated from S317's own output: carried units **20 → 27**, and the gap section reads
exactly the four awaiting a ruling, with "41 other enabled unit(s) are not ours".
