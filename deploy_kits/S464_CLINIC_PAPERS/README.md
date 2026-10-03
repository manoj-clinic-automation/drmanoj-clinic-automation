# S464_CLINIC_PAPERS — D664, slice 1 of 3: the clinic papers to sort, the groups, the month (session 292, 03-Oct-2026)

At the owner's word of 03-Oct-2026: "build." — after he had seen the five mock-ups ("look okay to me").

**The owner's ruling (D664):** papers scanned at reception that are not pharmacy purchases need their own home.
*Clinic consumables* is the main group, with three sub-groups — **Procedure room**, **X-ray films** (small film / 11 x 14)
and **Others** (stationery and the rest). The sub-group is optional at scanning; Shavez or he sets it later; the system
suggests it from the supplier **and** the items, one tap to confirm or skip. The supplier alone never decides (Yuvika
sells orthotics to the pharmacy on printed bills and procedure-room goods on handwritten slips). Goods like the inverter
battery belong to the *Dr MK expense* lane.

## What this slice adds
| address | what |
|---|---|
| `/scanapp/papers` | the clinic papers with no group yet, newest first, each with a suggestion: **Yes / Change / Skip** |
| `/scanapp/papers/<id>` | one paper: the three groups (X-ray films then asks the size), clear, and "not a clinic consumable? move it" |
| `/scanapp/papers/month` | clinic consumables for a month by group, with the unsorted and the other lanes named apart |
| `POST /scanapp/bills/<id>/subgroup` | sets or clears the group; one line in the bill's audit trail |

Owner and manager only. Two links appear on the Purchases page and one line on a clinic bill's page.

## What changes on the box
- **NEW** `/root/assetapp/clinic_papers.py` — everything above lives here.
- **EDIT** `/root/assetapp/asset_register.py` `446c671d` → `6dd5f3ab`: one guarded import at the foot, two links, one line — the links and the line are behind `is defined`, so with `clinic_papers.py` absent the app is the old app (walked).
- **DATABASE** one additive column, `bills.subgroup`. A copy of `assets.db` is kept beside it first.
- **Not touched:** the lanes and how each lands, the intake, `scanner_widget.js`, `shared/scan_checks_s441.py`, the pharmacy hand-over, every finance file. A move between lanes goes through the app's own `/bills/<id>/lane`.

## How a suggestion is made (worked out when the page is shown; stored nowhere)
1. battery / inverter / UPS / warranty words → *Dr MK expense* (a lane move, not offered on an approved bill);
2. X-ray / film words → *X-ray films*, with the size when `11x14` or `8x10` / `10x12` is read, else two buttons;
3. fibre cast, bandage, cotton, tape, betadine, lignocaine … → *Procedure room*;
4. brace, belt, knee cap, collar … → no tap: "looks like orthotics — a pharmacy purchase";
5. paper, register, toner … → *Others*;
6. Agarwal Surgicals or Yuvika with no item read → *Procedure room*, saying it is from the supplier only.

Each word list grows from the app's `settings` table (`d664.words.<name>`, comma-separated) with no new kit.

## Files
- `built/clinic_papers.py` — the module.
- `apply_s464.py` — three exact anchors, each found once, or nothing is written.
- `walk_s464.py` — 63 checks on three scratch copies (old, new, new without the module), each on an empty database with made-up papers.
- `figure_s464.py` — read-only: opens every new page on a **copy** of the box's own `assets.db`; prints counts only.
- `install_S464_CLINIC_PAPERS.sh` — gates → build lock → pins → apply on scratch → walk → the real-papers check → backups → rename into place → restart `assetapp` → door, mount, column and journal checks → restore on red. `DRY=1` places nothing.

## Still to come (each its own kit)
2. joining separately scanned papers (a bill and its warranty cards) into one PDF, undoable;
3. *Dr MK expense*: what it is, warranty till, and its reminder on the Renewals row.

## The owner's line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S464_CLINIC_PAPERS/install_S464_CLINIC_PAPERS.sh
```
