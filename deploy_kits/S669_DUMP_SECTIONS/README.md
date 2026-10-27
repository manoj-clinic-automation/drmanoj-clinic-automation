# S669_DUMP_SECTIONS — orthotics no longer land under "Medicines and others" in the dump · project Sanjeevni · session 359 · 28-Oct-2026

**For the owner, in three lines.** Three orthotics sat under *Medicines and others* in the expiry watch's dump. The fault is ours, not Marg's and not the spine's: your own section ruling on the shoulder immobiliser was missed because Marg's Batch Stock prints the name two letters longer than the closing stock it was ruled on, and the two cast shoes were filed as consumables by the seeding rule in September (the word CAST) and never corrected. Both are fixed; the list is made again at install.

## Why
The owner, 28-Oct-2026 05:09 IST: *"few items in dump stock listed in medicines are actually orthotics items, why this error? Rectification required from source of error, is it from marg, or our stock spine, or just listed wrongly here."*
**Read (his page in his Chrome, read only, and the 28-Oct database copy).** Three of the 33 are orthotics: BLING ELASTIC SHOULDER IMMOB S, CAST SHOE S TYNOR, PRIME CAST SHOE S. (CREPE BANDAGE and LEUKOBAND are consumables: *others* is their place by design, D777.)
1. **BLING ELASTIC SHOULDER IMMOB S.** He ruled it *Orthotics* on 18-Sep (`stock_item_section`, source owner). The ruling is keyed on the name as the closing stock printed it, 28 letters (*… IMMOB*). The Batch Stock prints 30 (*… IMMOB S*). `expiry_watch.ortho_of` looked the name up by exact key and missed; the word list has IMMOBIL, not IMMOB; so: medicine. Seven more orthotics on the Batch Stock have such a width twin (L S BELT … UNIS / UNISON, TYNOR WRIST SPL … ELASTI / ELASTIC, KNEE SUPPORT XXL HINGED UNISON, FINGER EXTENSION SPLINT PERFEC); the word list happened to carry them.
2. **CAST SHOE S TYNOR, PRIME CAST SHOE S.** The S268 seed classed them *Consumables*: CAST is a consumable word (plaster) and consumables are tested first. Nobody corrected the two rows. The expiry watch puts every non-orthotic in *Medicines and others*.
Marg: the names are Marg's, printed at the width each report allows; no section is Marg's. The spine: not read for sections. So: *listed wrongly here* (1) and *our section table* (2).

## Files
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/finance/expiry_watch.py` | Sanjeevni | 7ba3b0bc | 23e0a5bf | 1 edit in `ortho_of` + `_twin()`: when the exact key misses, the ONE table key that is a prefix of the name or that the name is a prefix of, the shorter at least 12 letters, stands for it; two candidates = none (the word list decides, as before). `TWIN_MIN = 12`. |
| `finance.db` · `stock_item_section` | Sanjeevni (the owner's rulings) | 2 rows seed Consumables | 2 rows owner Orthotics | the data step, by the installer: CAST SHOE S TYNOR, PRIME CAST SHOE S → Orthotics, source owner, by_user *manoj (28-Oct-2026, S359)*. Every screen that reads sections (the count rounds, the piles, the statement grouping) follows. |

Restarts `clinic-finance`; the watch made once now. `section_map.py` is not touched (its lists are a record, S268; a change there is its own kit).

## Proven (`walk_s669.py`, on the 28-Oct database copy and the 26-Oct Batch Stock; the device VM)
**11 of 11 green**; the control **2 S669 red · 0 older red · 9 green**; after the data step on a copy **12 of 12**. The shoulder immobiliser is an orthotic under both spellings. A short name borrows no twin. Two candidate rows: none taken. A medicine's twin ruling keeps it a medicine. Over all 238 names on the Batch Stock a twin is used for exactly 8, every one a width-spelling of the same item, never over an exact row. The two cast shoes read seed Consumables before and owner Orthotics after; the other 7 owner rows are untouched.
The installer was rehearsed four ways on a made-up server: red before the data step restores the file; red after it restores the file AND the two rows; green places, restarts, changes the rows, makes one run and walks 12 of 12; a second run says ALREADY INSTALLED.

## Install (on the server, after the publish; window 04:00–23:30 IST, clear of the night’s jobs)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s669kit && cp -rp /root/deploy/repo/deploy_kits/S669_DUMP_SECTIONS /tmp/s669kit && bash /tmp/s669kit/install_S669_DUMP_SECTIONS.sh
```
## Undo (the installer prints it)
```
\cp -p /root/finance/expiry_watch.py.bak_S669_7ba3b0bc /root/finance/expiry_watch.py && /usr/bin/python3 -c "import sqlite3; c=sqlite3.connect('/root/finance/finance.db'); c.execute(\"UPDATE stock_item_section SET section='Consumables', source='seed', by_user='manoj', at='2026-09-18T07:03:44' WHERE item_key IN ('CAST SHOE S TYNOR','PRIME CAST SHOE S') AND source='owner' AND by_user LIKE 'manoj (28-Oct-2026%'\"); c.commit()" && systemctl restart clinic-finance
```
