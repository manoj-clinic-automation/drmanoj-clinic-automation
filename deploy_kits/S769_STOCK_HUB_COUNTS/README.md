# S769_STOCK_HUB_COUNTS — the Stock check page lists every count

**Session 420 (the Sanjeevni chat), 10-Nov-2026. The owner, 07:26 IST (the mock approved 09:32):** integrate the stock check page — the 06-Sep count collapsed with its information line and all its flow; future counts from a template; the orthotics count shown there; a Cancel; and a switch to let Amir and other staff count with Darpan's counting access.

| file | from → to | what |
|---|---|---|
| `/root/finance/stock_hub.html` | `a710a98a` → TO | the top: *Start a new count* (Orthotics shelf, Whole shop), *Counts in progress* (Open, two-tap Cancel, the correction → Send to Amir), *Who may count*; the 06-Sep count as one line with *Show the full flow*; steps 4 (37 of 37 vouchers) and 6 (nothing waiting) read done |
| `/root/finance/section_count.py` | `305dd037` → TO | v1.1: `GET /api/hub` (the doctor's), `POST /api/access` (one `unit_role` row per person in the unit `stockcount`, maker); a plain page for a login not switched on |
| `/root/finance/section_count.html` | `c51a328e` → TO | the doctor's Cancel while counting; the crumb back to Stock check; a cancelled count reads plainly |
| `/root/finance/stockmatch.py` | `d80523b6` → TO | a login without Stock milaan rights is sent to the count page (never Darpan's page) |
| `/root/portal/tile_grants.json` | `e486f3de` → TO | **the parent's file (PLANNED on the board, D646):** v45 — the *Stock milaan* tile for alisha, amir, shavez, shivani; the portal re-reads it, no restart |

**Access:** a person switched on is a maker of the unit `stockcount` only: the counting page (start, enter, save, send). Never the correction, Send to Amir, marks, Cancel, the hub list, or Darpan's own Stock milaan cards. Switched off, the tile shows *You are not switched on for counting right now.*

**Proofs:** `walk_s769.py` 56/56 green (S768's 41 checks + 15 for the hub, the switch, the redirect, the tile); the CONTROL on the live files red. `rehearse_s769.sh` 5/5 (the portal file restored on a red). `proof_s769.py` on the device's copy of the 10-Nov database: the Orthotics template 75 items, 4 staff offered, `unit_role` in the shape the switch writes. The screens read on a preview at PC and phone width by a sub-agent; its findings built in.

**Install (the owner's paste):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s769kit && cp -rp /root/deploy/repo/deploy_kits/S769_STOCK_HUB_COUNTS /tmp/s769kit && bash /tmp/s769kit/install_S769_STOCK_HUB_COUNTS.sh
```
**Undo:** the installer prints the one line (five backups back, finance restarted).
