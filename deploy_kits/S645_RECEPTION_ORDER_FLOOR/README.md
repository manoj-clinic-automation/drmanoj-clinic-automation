# S645_RECEPTION_ORDER_FLOOR — reception's list whole again, and the order lines counted (kit S645, session S349, 25-Oct-2026)

**Why.** The owner, 25-Oct-2026 07:04 IST, *"1 ok"* — to fixing reception's *Aaj ka kaam* (F-1024). Since 22-Oct her list
showed *"Poori list abhi nahin khul paayi"* and left out her late-order line: the Sanjeevni chat's S619_ORDER_TRACKER rewrote
the order duties' SQL in DUTY_MAP.json, and the parent's floor rule for that line (aaj_seed.REWRITE) no longer fitted, so the
line was UNREAD — fail-closed, as designed. Building the fix found a second fault under it: the staff connection's floored view
of purchase_order_line keeps only lines whose goods ARRIVED on or after the floor, and the order duties look for lines where
nothing came — so, even fitted, her line would have read 0 with 2 orders late; Shavez's follow-up read 1 with 3; reception's
bill scan could drop an order with one missing and one awaited line.

**What changes.** `/root/finance/aaj_seed.py` 2f9ab396 → 2df0d3a9, one counted edit (`make_s645.py`, every piece cut from
DUTY_MAP.json v20's own bytes): the REWRITE table — `reception.order_arrival` refitted and `shavez.order_followup` added (the
floor on the CTE o beside its own order.track_since; L reads main.purchase_order_line), `reception.bill_scan` added (its four
line reads from main.purchase_order_line; it keeps its own date limits). DUTY_MAP.json is read, never changed. No data step.

**Proven.** `walk_s645.py` 16/16 on the 25-Oct database copy (read-only; the made-up rows only in a throwaway copy):
reception's list has no unread line; on the real books each of the three counts what the whole books count (2 = 2, 3 = 3,
2 = 2); two made-up orders count on both lists and the floor takes the older off; a made-up received order with one missing
and one awaited line stays on the bill scan; every other line of every person reads as before (49). `--old` on the live file:
10 S645 red, 0 older red (Shavez 1 against 3; the made-up orders 0 against 2; the bill scan 0 against 1).

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s645kit && cp -rp /root/deploy/repo/deploy_kits/S645_RECEPTION_ORDER_FLOOR /tmp/s645kit && bash /tmp/s645kit/install_S645_RECEPTION_ORDER_FLOOR.sh
```
## Undo
```
\cp -p /root/finance/aaj_seed.py.bak_S645 /root/finance/aaj_seed.py; systemctl restart clinic-finance
```
