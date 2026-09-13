# S254_SHEET_PHONE — the counter sheet on a regular Android phone

**The owner, 13-Sep-2026, after checking it on his phone:** *"The entry boxes appear so small that the typed
amount is not visible in total. And secondly, it is a long scroll including all the optional sections. Make
extra sections collapsible so that on a regular day it is less scroll and easy submit, expandable once opened
as required, with their text written on the expandable boxes."*

Two files, patched from exact live pins (`patch_s254.py`, every anchor once): `clinic_register.py` `92136a97`
(S251) and `clinic_money.py` `da9122e0` (S253 — **install S253 first**). No data change, no portal, no grants.

| | before | now |
|---|---|---|
| the entry table | label + three boxes on one row: each box a fifth of a 412-px screen; four digits cut | **each head on its own row, the three boxes on the row beneath — a third of the screen each**; five digits readable |
| the optional parts | always open: other-UPI box, float, the eleven-row hand-over count, the three-records table — one long scroll | **four folded boxes**, closed on a plain day, each with its line: *ICICI UPI not working? → Paid to another UPI* · *Float — alag rakho 5 × ₹200, 10 × ₹100, 10 × ₹50 · hand over ₹3,800* · *End of day — cash handed over · ₹3,800 to hand over* · *The three records, side by side · [verdict]* |
| when something is there | — | the fold opens by itself: a payment on another UPI (*· ₹2,050 recorded*), a short float or a change asked, a count made but not yet confirmed (*· counted ₹3,700*) |

On a plain day the whole sheet — twelve boxes, the physio row, Save — is one screen, and the rest is four lines.

## Proof — `EVIDENCE_S254.txt`
`patch_s254.py --selftest` GREEN (patch(live) == kit, both files). `walk_s254.py` — **152 checks, 152 ok** —
the S253 walk plus: five label rows / five box rows and no empty first column; the four folds closed on a
plain day; the sheet itself never a fold; the other-UPI fold open with its line once a payment is recorded;
the float fold's line carrying the instruction and the hand-over figure, opening by itself on a short day;
the hand-over fold's line saying *to hand over* then *counted*. Mock install GREEN; re-run ALREADY INSTALLED.
The sheet rendered at 412 px and read.

## Install — ONE line on the VPS, after S253 and the owner's publish
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S254_SHEET_PHONE/install_S254_SHEET_PHONE.sh
```
