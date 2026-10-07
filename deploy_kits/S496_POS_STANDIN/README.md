# S496_POS_STANDIN — the POS machine's UPI total, when the bank's statement has not come

Session 300 (parent), 07-Oct-2026. The owner's eleven decisions of 07-Oct 12:17 IST, relayed by the Sanjeevni chat
(its session 299) and pasted by him as "URGENT, BUILD TODAY".

## What it does

| who | where (no new screen) | what |
|---|---|---|
| Darpan | his *Kal ka hisaab* form, inside the "कितना cash दिया?" card | ONE optional figure — yesterday's UPI total read from the POS machine — in its own tinted box. Shown only while that day's bank statement is missing **after the bank's expected time**. |
| reception | the counter sheet and the morning-match card | the same one figure, Roman Hindi. Same condition. |
| the owner | *Clinic money* (`/finance/clinic/money`) for the clinic and NK Pathology; *Approvals → Kal ka hisaab* for Sanjeevni | one line — who typed it, which date, the figure — with **Confirm** / **Reject**; his own typing (no second confirmation); the two settings. |

- A typed figure changes **nothing** until he confirms it.
- After his confirm it stands in for the bank on that day, always marked *provisional — POS total, bank not in*, and
  the day is worked again on it (the clinic's match and flags; Sanjeevni's expected cash and decision).
- The bank's own statement replaces it **by itself** the moment its row exists. A difference beyond the tolerance is
  one line for him (date, typed, bank, difference). The typed row is kept — nothing is ever deleted from `bank_standin`.
- If the statement never comes the figure keeps standing, marked *bank statement never received*, as one quiet line.
- **No money row is written**: no `day_entry`, `cash_movement`, `upi_statement`, `upi_txn` row is created, changed or removed.
- Units are read from the statement store (`upi_statement`, `finance_upi.MIDS`): clinic, medical, lab today. The lab has no
  daily page of its own, so its figure is the owner's own typing on Clinic money.

## Settings (table `setting`; both on screen)

| key | default | meaning |
|---|---|---|
| `bank_mpr.expect_hhmm` | `10:00` | the bank's statement for a day is expected on the box by this time (IST) the next morning. `bank_mpr_status.py` reads the same key: WAITING becomes NOT RECEIVED at this time, and staff are offered the field only after it. Replaces the stale 11:15 / 12:20 of S217 (66 of the 91 statements since 01-Sep were in before 10:00). |
| `bank_standin.tolerance_p` | `10000` (₹100) | a bank-vs-typed difference beyond it is one line for the owner; a POS-vs-Docterz difference beyond it is one flag on the staff card. |
| `bank_standin.on` | `1` | `0` hides the field from staff; the owner's own typing stays. |
| `bank_standin.owner` | `manoj` | the one login whose word confirms. |

## Files

| file | on the box | from → to |
|---|---|---|
| `bank_standin.py` | `/root/finance/bank_standin.py` | NEW `a35d04f1` |
| `bank_mpr_status.py` | `/root/finance/bank_mpr_status.py` | `a0e740ce` → `e1a72305` |
| `clinic_money.py` | `/root/finance/clinic_money.py` | `c56d3331` → `683f7511` |
| `darpan_kal.py` | `/root/finance/darpan_kal.py` | `c45bb343` → `fd799a56` *(the Sanjeevni chat's; edited with its agreement)* |
| `darpan_kal.html` | `/root/finance/darpan_kal.html` | `ec8b64ae` → `f5e279eb` *(the Sanjeevni chat's)* |
| `finance_approvals.html` | `/root/finance/finance_ui/finance_approvals.html` | `8edc44c5` → `b32da7ff` *(the Sanjeevni chat's)* |
| `walk_s496.py` | not placed | the live-shape walk the installer runs on the box before placing anything |
| `install_S496_POS_STANDIN.sh` | not placed | pin-gated, walked, backed up, restored on red; `DRY=1` places nothing |

`finance_app.py` is not touched (drift stays 4): the new module is reached from the two modules already mounted.
Backups: `<file>.bak_S496_<first 8 of its old md5>` beside each file.

## Install (the VPS; one line)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S496_POS_STANDIN/install_S496_POS_STANDIN.sh

## Undo

Put the five `.bak_S496_*` files back over their originals, remove `/root/finance/bank_standin.py`, restart `clinic-finance`.
The table `bank_standin` and the three `setting` rows may stay; nothing reads them once the files are back.

## For the Sanjeevni chat

- `darpan_kal.compute_day` now answers three more keys — `online_source` (`bank` | `pos` | `marg`), `marg_online_p`, `standin` —
  and `online_provisional` stays 1 on a stand-in day. `_refresh_if_needed` re-decides a day when a confirmed figure differs from
  the `online_p` it was decided on, exactly as it re-decides when the bank lands.
- `api/owner` puts a waiting POS total first in `items` (`kind: pos_typed`, counted in `count`) — so the Approvals page's own
  "needs you" line (`sanjeevni_approvals.needs_you`, not touched) already leads him to the card; its words still say "his word and
  the data differ". If you want it to name the POS total, that file is yours.
- S486's pins for `darpan_kal.py`, `darpan_kal.html` and `finance_ui/finance_approvals.html` are stale from this install.
