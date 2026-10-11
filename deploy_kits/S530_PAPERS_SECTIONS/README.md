# S530_PAPERS_SECTIONS — the four sections · sorted = accepted · where each paper stands (D710, D689 item 1)

*Scan App project, S306, 11-Oct-2026. The owner's rulings of 11:41 IST on `claude/SCANAPP_FLOW_PROPOSAL_v1.md` ("1 ok,
2 yes, 3 yes") and his word on the mock-up. Built by BUILD_NORM_v1 (D704). One file replaced whole: `clinic_papers.py`
(drift 0 at the branch; read whole in S306). `asset_register.py` is read, not edited.*

## The real cause
The scan app's database (the 11-Oct backup): 26 of the 29 live clinic papers were still *draft*, 1 to 47 days old, 18
without a group, only 3 ever approved — nothing downstream reads a draft. Three papers addressed to the clinic itself
(letters, not bills) sat among them. The "Other document" lane had nowhere to go. The second tap (approve) after the
first (group) was the stall.

## What the kit does
- **Four sections** beside the clinic consumables, in the same column `bills.subgroup`: `construction` Construction work ·
  `resume` Resumes · `misc` Miscellaneous documents · `personal` Personal. A paper on the Clinic, Other-document or
  Dr MK expense lane can take a section; the consumable groups stay the clinic lane's own; Personal is the owner's
  alone (set, opened, listed, counted by him only — a manager gets 403 on the paper and no Personal row).
- **The papers-to-sort list** (`/scanapp/papers`, now *Papers to sort*) also shows the Other-document lane's papers.
  Suggestions: a resume from its words (two or more, no bill number, no amount); Construction work from its words or
  a hardware/paint/electricals/sanitary supplier; a paper addressed to the clinic itself gets the note "not a
  supplier's bill — Personal or Miscellaneous, your call".
- **Sorted = accepted** (D710): one tap on a clinic *draft* sets its group AND accepts it by the app's own approve
  rules — the same-vendor-number-amount duplicate check (then it is sorted but NOT accepted, and the page says so),
  the vendor book, the asset back-fill; audit rows `d710_accepted` / `d710_not_accepted`. The approve / reject doors
  stay. **The backlog heals at every start** (`heal()` in `init()`, idempotent): a clinic draft that already has a
  group is accepted the same way — 8 on the box today.
- **Where each paper stands** — one collapsed fold at the top of the papers page, owner only: this month's scans by
  lane (pharmacy handed on · clinic sorted / in a section / waiting with the oldest age · other documents · lab · Dr MK
  expense with warranties noted).
- **The month page** gets an *Other sections* card (Construction work with money and "clinic / MK not decided",
  Resumes, Miscellaneous, Personal for the owner); a sectioned paper never counts under Clinic consumables.
- Staff screens: unchanged. No column, no table: `subgroup` takes four more values; the heal writes `status`,
  `approved_by`, `approved_at` and audit rows only.

## Files
| file | FROM (pinned) | TO |
|---|---|---|
| `/root/assetapp/clinic_papers.py` | `5e21f491` (S466.1) | `PIN_TO_clinic_papers.txt` (S530.1) — backup `.bak_S530_5e21f491` |
| `/root/assetapp/asset_register.py` | `d3f1b64e` (S523) | read only; the installer refuses on any other |
| `/root/assetapp/assets.db` | — | backed up `assets.db.bak_S530_<stamp>` before the restart (the heal writes rows) |

## Proof
`walk_s530.py` — the app with the built file on a copy of the real database, made-up rows dated 2031: **33 of 33 green**
(the heal 8 → 0 and nothing on a second start; the list, the suggestions, the picker for owner and manager, one tap =
sorted + accepted with audit and vendor book, the duplicate rule, a section on an Other-document and a Dr MK paper
keeping its status, a consumable group refused off the clinic lane, Personal refused to a manager and hidden from him,
the month page and its totals, every old door still answering, the live database untouched). On the LIVE file: 24 red
(the control). Three owner pages read at phone width by an independent agent: nothing wrong in the kit. The installer
rehearsed on a made-up root: DONE · ALREADY INSTALLED · drift refused · red-after-placing restored.

## Install (the owner's one line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S530_PAPERS_SECTIONS/install_s530.sh
```
## Undo (one line)
```
cp -p /root/assetapp/clinic_papers.py.bak_S530_5e21f491 /root/assetapp/clinic_papers.py && systemctl restart assetapp
```
Papers the heal accepted stay accepted (as a tap would have); the database backup stands beside the live one.
