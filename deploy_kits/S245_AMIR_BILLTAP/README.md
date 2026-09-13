# S245_AMIR_BILLTAP — SUPERSEDED by S246_AMIR_LIST_REOPEN

**Do not run this installer.** It refuses, correctly, and touches nothing.

## What happened, plainly

This kit was built and published as the one-tap bill screen, and **installed** on 13-Sep-2026:

```
/root/finance/amir_day.py   aad400fa…  ->  79eb701f…
```

Minutes later the owner added a second ruling for the same screen (the settlement line, and
flagged bills staying until they are cleared). The kit folder was rebuilt **in place** rather than
given a new name — so the published folder no longer matched the file that was already live. The
installer's pin gate caught it exactly as designed:

```
!! RED -- live amir_day.py 79eb701f… already carries the S245_AMIR_BILLTAP mark
   but is NOT this kit's file (d5d485dd…) -- a different build is live; NOTHING changed
```

Nothing was damaged. **The lesson, and it is now a rule: a kit that has been published is
immutable. If it may already be installed, the next change gets the next kit number, never a
rebuild of the same folder.**

## Where the work went

Everything this folder carried — plus the reopen work the same day — is in:

```
deploy_kits/S246_AMIR_LIST_REOPEN/
```

built against `79eb701f…`, the file that is actually live. Read that README.

## What is left here

The files are kept as published, for the record. `SUMS.md5` covers them, so the folder is
self-consistent; the installer will still refuse on the pin, which is the right answer.
