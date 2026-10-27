# S668_EXPIRY_START_OF_DAY — the expiry watch takes off the Batch Stock's own day's sales · project Sanjeevni · session 359 · 27-Oct-2026

**For the owner, in two lines.** VOM L's last 3 strips were sold on 26-Oct, but the expiry list still showed them after S665, because the list never took off the sales made on the Batch Stock's own day. A Batch Stock taken before the shop opens is now counted as the stock at the start of that day, as everywhere else in the system (your ruling D740).

## Why
The owner, 27-Oct-2026 11:58 IST, about VOM L. S665 (installed today) makes the list in the day; its run of 12:20 IST read sales to 26-Oct and still listed VOM L C1235 at 3:0 (his page, read in his Chrome, read only, 14:5x IST).
**The cause.** `expiry_watch.compute` takes off the spine's sale lines with `date > as_on`, where `as_on` is the date Marg prints on the Batch Stock. The 26-Oct Batch Stock was taken at 05:38 on 26-Oct, before the day's first sale, so it is the stock at the START of 26-Oct. The five VOM L sales of 26-Oct (30 tablets = the 3 strips) were dated 26-Oct and were never taken off. The estate already has the rule, `stock_figure.end_day` (push_expected's capture-hour rule): a same-day print before 09:00 stands for the day before, a print after 22:00 or for an earlier day stands for its own day, and a print in shop hours cannot tell. The watch did not use it.

## Files
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/finance/expiry_watch.py` | Sanjeevni | fed23760 | 7ba3b0bc | 3 edits: new `_sales_after(R)` (`stock_figure.end_day` on the stamp in the file's own name; the printed day when the rule says None, or on any failure); `compute()` takes off the sales, reads *bought since*, and runs the written-off check from that day. Nothing else in the file moves. |

No crontab change (S665's line stays). Restarts `clinic-finance` (the screens import the module; they read runs, never compute). After placing, the watch is made once now, as the 23:57 line makes it.

## Proven (`walk_s668.py`)
Offline (the device VM, the 27-Oct bundle and database copy; no spine off the box): **6 of 6 green**, control **2 S668 red · 0 older red · 4 green**. A 05:38 print stands for the day before. A 22:30 print, an in-hours print, a print for an earlier day and a name with no stamp keep the printed day, as before. `compute()` uses the cut-off in all three places.
On the box, two checks on copies of the live database and spine are added (live shape). The whole list is made from a whole-shop Batch Stock. **No batch whose own sales since its Batch Stock's start reach its printed stock is still on the near or expired list** (today: VOM L C1235). That gives **8 of 8**, and the control **3 · 0 · 5**. The installer stops before placing if either is not so.
The installer was rehearsed on a made-up server three ways: red after placing put the file back; green placed it, restarted, made one good run, and walked green; a second run said ALREADY INSTALLED.

## Install (on the server, after the publish; window 08:02–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s668kit && cp -rp /root/deploy/repo/deploy_kits/S668_EXPIRY_START_OF_DAY /tmp/s668kit && bash /tmp/s668kit/install_S668_EXPIRY_START_OF_DAY.sh
```
## Undo
```
\cp -p /root/finance/expiry_watch.py.bak_S668_fed23760 /root/finance/expiry_watch.py && systemctl restart clinic-finance
```
