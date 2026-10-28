# S676_SECTIONS_BY_FAMILY — every Marg name has its section the day it lands; your ruling on one size reaches its sisters · project Sanjeevni · session 362 · 28-Oct-2026

**For the owner, in three lines.** The section table (Medicines / Orthotics / Consumables) was filled once on 18-Sep and never again, so 24 names Marg has added since had no section at all — every page that groups by section (the dump, the count rounds, the statement, the order engine's orthotics list) fell back to the old word lists for them. And when you rule a section on one size, the other sizes did not follow: three cast-shoe sizes were still "consumables" after S669 moved the two you named. Both are closed: a closing-stock export now seeds its new names the moment it lands, and a name takes the section you ruled for its sisters (the same product in another size, pack or brand) before the word rule is consulted.

## Why (F-1035's residue; the owner's "All three", 12:37 IST 28-Oct)
- `section_map.seed()` was run once (S313, 18-Sep, 372 names). Nothing called it again. On the 27-Oct copy the 26-Oct closing prints 386 names; 24 have no row (ANKLE BINDER M FLAMINGO, KNEE IMMOBILIZER M TYNOR, LINVIZ 600 6T, RANIMIG 150, TYNOR WRIST SPL RT M ELASTI …).
- S669 moved CAST SHOE S TYNOR and PRIME CAST SHOE S to Orthotics by your word; CAST SHOE L TYNOR, CAST SHOE L UM and CAST SHOE M TYNOR stayed Consumables (seed) — nobody named them. S671 moved the nine crepe sizes one by one; a tenth size Marg adds would be a consumable again.
- The S268 word lists inside `stock_app.py` are count #1's own record (your word: the count untouched) and are NOT changed; they retire at rung 5. `section_map`'s copy of them is unchanged too — only the ORDER changes: your ruling on a family first, the word rule second.

## The family rule
A name's **family** is the name cut at its first size or number word that comes after a product word of three letters or more: `CAST SHOE L UM` → CAST SHOE · `LEUKOCREPE 10CM*4IN` → LEUKOCREPE · `L S BELT XL CONT GRAY UNIS` → L S BELT · `G DRESS 10` → G DRESS · `GLOCREPE` → GLOCREPE (its own family). A family in which every row YOU ruled (source `owner`) is in one section decides every sister that is not yours (source `seed`, `rename`, `family`); a family you ruled in two sections decides nothing. Applied in three places: when a new name is seeded, when you tap a section on the sections page (the sisters follow at once; the message says how many), and once by this installer.

## Files
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/finance/section_map.py` | Sanjeevni | abef2baf | 0e705ca1 | `family()`, `owner_families()`, `rule_of()`, `sweep_families()`, `on_closing()`; `seed()` writes `source='family'` with the word rule kept in `seeded_as`; `set_section()` sweeps the sisters after your tap. `LIST_VERSION` says so. |
| `/root/finance/stock_app.py` | Sanjeevni | 8413ee55 | 764e55fa | ONE counted edit in `api_snapshot`: after the closing and its feed rows are committed, `section_map.on_closing(items, by_user='closing <as_on>')` — never for the computed feed (`push_expected`), fail-soft (a fault in the map never refuses a closing). |
| `finance.db` · `stock_item_section` | Sanjeevni (your rulings) | 397 rows | +24, 3 moved | the installer's data step: the newest closing's names seeded; the family sweep (on the box: the three cast shoes → Orthotics, as CAST SHOE S TYNOR). The table is copied to `/root/deploy/s676_section_before_<stamp>.json` first; the undo puts it back whole. |

## Proven (`walk_s676.py`, the device VM, on the 27-Oct database copy with the box's S669/S671 rows written in)
**31 of 31 green**; the control on the live files **20 S676 red · 0 older red · 10 green**; after the data step **30 of 30**. The sweep on the box's state moves exactly the three cast shoes and nothing else; a second sweep moves nothing; your rows are untouched. A new CAST SHOE size seeds Orthotics (family), a new LEUKOCREPE size Medicines; a name of no ruled family takes the word rule as before; a row that exists is never overwritten. Your tap on one size moves its sister; a second ruling on the sister splits the family and nothing else moves. The closing's door (`api_snapshot` on a copy, the marg token): a new name has its row by the time the closing is stored; the computed feed seeds nothing; a broken map never refuses the closing. The older behaviour (classify, is_orthotic, inherit, summary/rows/items_in, stock_app's own lists) unchanged.
The installer was rehearsed four ways on a made-up server: DRY; the install (24 added, 3 moved; walk 30/30 after); ALREADY INSTALLED; a red after placing restores both files byte-exact; a red after the data step restores both files AND the table (397 rows) — nothing of the kit left behind, the lock released.
Independent cold review (a fresh agent, the kit files only): 0 blockers, 4 corrections, 9 notes — every correction built in before placing: the walk stands on its own WALK-prefixed rows (the box’s real moves are listed, never asserted), the printed undo restores the files only (the table self-heals at the next closing), a run cut between the two placements is named at [2/8], the hook sits wholly inside its try. Verdict SAFE TO INSTALL; the walk, the control and the four rehearsals were re-run on the corrected kit.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s676kit && cp -rp /root/deploy/repo/deploy_kits/S676_SECTIONS_BY_FAMILY /tmp/s676kit && bash /tmp/s676kit/install_S676_SECTIONS_BY_FAMILY.sh
```
## Undo (the installer prints the exact line)
Both files back from `*.bak_S676_<from8>`, the table back from `/root/deploy/s676_section_before_<stamp>.json`, `systemctl restart clinic-finance`.
