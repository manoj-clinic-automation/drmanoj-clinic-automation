# S727_FLOW_LOCKED_QUIET — a locked month never asks to be approved again · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** October, already locked and paid, no longer says its sheets need approving again; only a month that is still open is held to its figures.

## Why
Read live through the owner's login right after S724 went in (16:06 IST): October's flow page said its approvals of 5-Oct no longer hold — true of the figures, but October is locked (06-Nov 07:19) and paid, so the line could only confuse.

## What it changes — `/root/staff_register/staff_register.py` ffbe8db2 (S724) → 18973ca9 (make_s727.py: 4 counted edits on the live bytes)
`_month_locked(ym)` reads `locked_run`; for a locked month the flow page, the two sheet pages and the lock desk show the approvals as they are, without the fingerprint test. Unlocked months: exactly as S724.

## Proven
`walk_s727.py` **21 of 21** — S724's 18 checks, then a locked month (its flow page and sheet page show the approval, no *approve again*), and an unlocked month still told when its approval no longer holds. Control (the live S724 file): **2 red**. The installer rebuilds the file from the box's own bytes first.

## Install (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s727kit && cp -rp /root/deploy/repo/deploy_kits/S727_FLOW_LOCKED_QUIET /tmp/s727kit && bash /tmp/s727kit/install_S727_FLOW_LOCKED_QUIET.sh
```
## Undo
```
bash /tmp/s727kit/install_S727_FLOW_LOCKED_QUIET.sh --undo
```
