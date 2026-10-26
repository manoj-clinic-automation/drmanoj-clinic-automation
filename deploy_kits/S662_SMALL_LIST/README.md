# S662_SMALL_LIST — four small fixes from the Sanjeevni small list · project Sanjeevni · session 359 · 26-Oct-2026

**For the owner, in three lines.** A bill already marked *Marg galat* that reception scans again at the same amount now simply stays on Amir's list; it no longer lands on yours. The old *Order medicines* page can no longer send a WhatsApp order, so every order goes from the one order list. DYNAPAR QPS PLUS is counted as a medicine, not a Dyna support, and a dealer's delivery time is learnt from at least three of his orders, not one.

## Why
The owner, 26-Oct-2026 18:04 IST: *"Do all 5"* — the small list of `START_HERE_SESSION_359` B.3: F-987's residual, `staff_send`, `order.lead_days`, the S335 list, F-1023. This kit is the four that are code. The S335 list is fourteen named items; its triage is in the S359 records, not here.

## Files — FROM → TO (every edit anchored; `make_s662.py` rebuilds the TO bytes from the live FROM bytes and stops on any other md5)
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/finance/porders.py` | Sanjeevni | 3209d0a2 | 8326dfc5 | 2 edits in `api_scan_amount`: the bill's `wrong_amount_p` read with it; a new branch before *the owner's*: verdict WRONG and the typed paper amount = that WRONG amount (within ₹1) → `amount_state = marg_wrong`, nothing written to the bill, audited `stands: true`, message *"Marg galat hai — yeh bill pehle se Amir ki list par hai."* (F-987's residual) |
| `/root/finance/purchase_app.py` | Sanjeevni | 447b745f | 82654e0c | 3 edits: `POST /finance/purchase/api/order` action `staff_send` → 409 `send_via_order_list` (English to the doctor, Roman Hindi to staff); the *Order medicines* page (`/page/staff`) loses its *Send on WhatsApp* button (Call stays) and its sentence now names the order list. The function `_staff_send` is unchanged — `order_rules.send_proposal` and `porders.api_send_med` call it directly. |
| `/root/finance/order_rules.py` | Sanjeevni | 8a116cbd | 5e8330b3 | 1 edit: `lead_learned` returns *(none, 0)* below `LEAD_MIN_N = 3` orders. Read only by `reseed()`, which runs on the 1st (next: 1-Nov 05:30). |
| `/root/finance/section_map.py` | Sanjeevni | 9bf9b98f | abef2baf | 2 edits: `"DYNA"` → `" DYNA "` in `_ORTHOTIC_WORDS` (names are padded with spaces, so this is a whole word); `LIST_VERSION` says so (F-1023) |
| `/root/finance/stock_app.py` | Sanjeevni | 40f2c922 | 8413ee55 | 1 edit: the same word in its twin `_ORTHOTIC_WORDS` (`_BRAND_WORDS` is token-based and unchanged) |

No data step. No crontab change. Restarts `clinic-finance` only. The portal, the medical PC and manojz: nothing.

**What the lead change does on 1-Nov:** under the old rule nine dealers would have gone to a 2-day lead on 1-Nov, five of them on one order. Under the new rule only Deepam, Janta and L.K. Drug House move to 2 days, each on three orders with a median of 2 days. The owner's ruling D626 (*"1 … 2 where a supplier's own record shows later"*) is unchanged. `order.deliver_days` (2, the owner's 22-Oct late line) is a different setting and stays: a 2-day lead is still on time. Nothing on any staff screen changes. `order.source` stays `marg_sheet`.

## Proven (`walk_s662.py`, on the 26-Oct bundle and the 26-Oct database copy, offline in the device VM)
**19 of 19 green.** The control (the live files under test) gives **9 S662 checks red · 0 older red · 10 green**.
- A, on the walk's own four bills (F-998): the rescan stands with the verdict and leaves the bill as it was. Unchanged: a first WRONG, *the owner's* for a different amount, *scan galat* when paper = Marg, and 409 when the scan is already settled.
- B: `staff_send` gets 409 and writes no order. The page has no Send button. `_staff_send` is still there for the order list. The door's other actions still reach their code.
- C: every learnt lead now stands on three or more orders, or on none, and a supplier with three still learns. On the 1-Nov reseed a lead moves to 2 only on three orders. No "learned from 1 order" wording. Offline, the walk stands in the rules' own rhythm for the spine; on the box it reads the live spine.
- D: DYNAPAR is a medicine in both lists, and the Dyna orthotics stay orthotics. All 397 seeded items classify as seeded. Over all 475 item names in the database, only DYNAPAR QPS PLUS changes section.

## Install (on the server, after the publish; the install window is 08:02–23:49 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s662kit && cp -rp /root/deploy/repo/deploy_kits/S662_SMALL_LIST /tmp/s662kit && bash /tmp/s662kit/install_S662_SMALL_LIST.sh
```
## Undo (the installer prints it with the exact backup names)
```
for f in finance/porders.py finance/purchase_app.py finance/order_rules.py finance/section_map.py finance/stock_app.py; do b=$(ls /root/$f.bak_S662_* | head -1); \cp -p "$b" /root/$f; done; systemctl restart clinic-finance
```
