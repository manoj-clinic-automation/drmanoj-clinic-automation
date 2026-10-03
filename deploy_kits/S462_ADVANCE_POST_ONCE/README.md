# S462_ADVANCE_POST_ONCE — a pharmacy salary advance reaches the Staff Ledger once (session 292, 03-Oct-2026)

At the owner's word of 03-Oct-2026 ("Do these"). F-706; source: S291 whole read, lead 3 — and a second road to the
same fault found while proving the first.

**One file changes:** `/root/finance/finance_app.py` `26a532a6` (S461) → `27a162e6`. `/root/staff_ledger.py` is not touched.

| | before | after |
|---|---|---|
| approving a day with two advances, the second of which fails | the first was already in the Staff Ledger, its stamp rolled back; every retry posted it again | every row is checked, and the ledger's own month ceiling asked for the day's total, before any row is posted; if a post still fails part-way, what the ledger took keeps its stamp and the refusal says so |
| correcting an APPROVED day | the save deleted and re-inserted the expense rows, the stamp was lost, re-approval posted the advance a second time | the stamp and the ledger row's id survive the correction (matched by uid, else by amount) |
| changing or removing an advance the ledger already holds | accepted; the ledger then held the old amount and the new | refused — "reverse it in the Staff Ledger first" — unless the ledger has reversed it (rejected, or an approved contra) |

## Files
- `apply_s462.py` — 5 exact anchors, each found once, or nothing is written.
- `walk_s462.py` — 40 checks, old file and new, with the box's own `staff_ledger.py` posting into an empty ledger in a scratch folder. The child refuses to post if the ledger folder is not the scratch one or a notification address is set; the live ledger's md5 is read before and after.
- `report_s462.py` — read-only: says whether the live Staff Ledger already holds a pharmacy advance twice. The installer runs it once; it need not be run by hand.
- `install_S462_ADVANCE_POST_ONCE.sh` — gates → build lock → pin → apply on scratch → walk → backup `.bak_S462_26a532a6` → rename into place → restart → door and journal checks → restore on red. `DRY=1` places nothing.

The owner's one line is in `deploy_kits/S463_ROLE_LOCKS/README.md` (it runs this kit, then S463).
