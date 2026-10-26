# S664_PAY_AND_NAMES — the session-335 small list, its code part · project Sanjeevni · session 359 · 26-Oct-2026

**For the owner, in three lines.** On the Vendor payments page, the backup **Bhejo** now asks first when a payment message was already handed to the reception phone, because it may still go from there; tapping Cancel sends nothing. The NEFT total that the bank SMS is matched against now counts only suppliers with something to pay, just as the bank advice file does. The scanner-check page and your Needs-you line say *Scan reading* instead of *Sarvam*, since Claude reads the bills now.

## Why
The owner, 26-Oct-2026 18:04 IST: *"Do all 5"*. The S335 list (`START_HERE_SESSION_335` item 6, `_338` item 5) has fourteen named items. S662 settled two of them (`staff_send` and its `_wa_text`; `order.lead_days`). This kit is the three that are code and safe now. The other nine are decided in the S359 records: closed without a build, one tap for Shavez, parked until the buying switch, or named to the Scan App chat.

## Files — FROM → TO (`make_s664.py` rebuilds the TO bytes from the live FROM bytes and stops on any other md5)
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/finance/supplier_msg.py` | Sanjeevni | f208d2b5 | bdfe4ce7 | 3 edits: `messages()` also reads `handed_at` (never `to_number`, never `body`). A pending message that was handed to the phone gets a Bhejo carrying its question (`data-handed`, English for the doctor and Roman Hindi for a sender), and `msgSend407` confirms before it sends. A new helper `_s664_handed` is appended. (F-702's residue) |
| `/root/finance/bank_sms.py` | Sanjeevni | 4ddbdd16 | b357ec1c | 1 edit: `neft_portion_p` counts NEFT lines with `payable_p > 0`, as `_advice_rows_s265` does |
| `/root/finance/purchase_app.py` | Sanjeevni | 82654e0c (S662) | da04d546 | 4 edits: the S446 page's title, heading and cell note, and the Needs-you line, say *Scan reading* (D747). The counter, `purchase_sarvam_check`, its setting and its trial date are unchanged. |

No data step. No crontab change. Restarts `clinic-finance` only.

## Proven (`walk_s664.py`, on the 26-Oct bundle + S662, and the 26-Oct database copy, offline in the device VM)
**11 of 11 green.** The control (the live files under test) gives **7 S664 checks red · 0 older red · 4 green**.
- A, on the walk's own two rows (F-998): the handed message's Bhejo asks first in English for the owner and in Roman Hindi for Shavez. A message never handed is unchanged. The script confirms before it sends. No number or message text is ever carried. On the live rows, the two waiting September messages (A.A. Pharmaceuticals, Deepam) carry their hand-out time.
- B: a month with a negative NEFT line counts only the payable lines. On the finalised months (Sep, Aug) the figure equals the advice lines, so nothing moves.
- C: the page and the Needs-you line read *Scan reading*. The page still counts the same bills.

## Install (on the server, after the publish; the install window is 08:02–23:49 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s664kit && cp -rp /root/deploy/repo/deploy_kits/S664_PAY_AND_NAMES /tmp/s664kit && bash /tmp/s664kit/install_S664_PAY_AND_NAMES.sh
```
## Undo (the installer prints it with the exact backup names)
```
for f in finance/supplier_msg.py finance/bank_sms.py finance/purchase_app.py; do b=$(ls /root/$f.bak_S664_* | head -1); \cp -p "$b" /root/$f; done; systemctl restart clinic-finance
```
