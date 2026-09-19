# S324_SLIP_LOG — the OPD & X-ray/Proc slip tile

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S324_SLIP_LOG/install_S324_SLIP_LOG.sh
```

## What he asked for, 19-Sep-2026

The plan he wrote with the assistant (`Chamber_Slip_Log_Plan.pdf`, session 271), plus two inputs after it:

- a person with **no clinic ID** (someone accompanying a patient who wants an X-ray) must be loggable — rare, but it happened recently;
- the screen: **Back to the portal at the top**, sections **collapsed, only the top one open**, so a flow completes on one screen — the scrolling Manoj Bhati suffers on his own page.

## What it installs

| file | change |
|---|---|
| `/root/finance/slip_log.py` | NEW — the tile `/finance/slips`, the room ticks, the report `/finance/slips/report/<day>` |
| `/root/finance/finance_app.py` | patched on the box: unit `slips` in `_unit_for_path`, guarded mount |
| `/root/portal/portal.py` | the tile **OPD & X-ray/Proc Slips**, section Clinic, roles doctor |
| `/root/portal/tile_grants.json` | v20 — the tile to shavez, alisha, shivani, bhati, awdhesh |
| finance.db | unit `slips`: makers shavez, alisha, shivani, bhati, awdhesh · checkers manoj, bhawna; tables `slip_book`, `slip`, `slip_item` on first use |

## The screen

- **OPD parchi** (open on top for the chamber): the next slip number is filled in; type the clinic ID — a known patient's name appears, a new ID reads *NAYA*, an ID far above the highest known asks for a re-check; *ID nahi hai* takes a name instead.
- **X-ray / Proc parchi**: the number filled in; the patient picked from today's OPD in one tap; the X-ray list and the procedure list are separate, from his rate page, each with *Other*; up to 6 X-rays and 3 procedures; R / L / Both where the line asks a side.
- **Room: Paid / Done** (open on top for Awdhesh): UPI · Cash · Done per slip, tap again to undo. Nothing waits on it; older open ticks show as one reminder line.
- **Aaj ki list**: the day in slip order; a skipped number asks Radd / Kharab / Baad mein; *Hatao* takes a wrong entry off (a reason is needed unless it is your own entry the same day).
- **Book**: the two books' ranges; the first use of each book asks for the day's first number.

## The report (English, the doctors)

`https://followup.dr-manoj.in/finance/slips/report` — the day's problems first, then OPD in slip order, then X-ray & Procedures in slip order, then Docterz entries with no slip. It runs **alongside** the current report; nothing old is touched. It names the 18-Sep kind of error directly: a consultation above the usual fee, for a patient with an X-ray slip and no Docterz X-ray line, reads *"the ₹… extra looks like the X-ray/procedure money booked as consultation"*.

## Proof

`walk_s324.py` — the real patched `finance_app.py` over a scratch copy of the real `finance.db`: 79 checks, green offline on the 19-Sep 01:35 bundle's own bytes and again by the installer on the box before a file is placed. Phone-width render checked at 390×844: the OPD, X-ray/Proc and Room flows reach Save without scrolling.
