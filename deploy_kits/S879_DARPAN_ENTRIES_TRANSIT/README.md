# S879_DARPAN_ENTRIES_TRANSIT

**Session 483 (the Sanjeevni chat), 18-Nov-2026.** His word 16:57: "do 1 to 4 now".

1. **F-1468 — Darpan's Kal ka hisaab.** His expected cash now reads the owner's own entries of the day (hub_cash.py's
   `owner_day_entry`, read through `hub_cash.entries` — the one store): money paid into another account never reached the
   drawer, cash taken out on a doctor's word left it; both lower what Darpan hands over. His card shows one row under the
   existing adjustment row — **"− डॉक्टर साहब की entry (drawer से बाहर)"** with the amount only (no party, no purpose);
   the doctor's own view of the page shows "− your day entries". A stored day whose expected moved because of those
   entries (or an entry removed) is re-decided the next time the page is opened on it — 14-Nov's ₹5,580 short then reads
   even. A day is re-decided only when the entries' figure it was decided with moves (a small side table, `darpan_kal_s879`, remembers it) — never for any other change in its books — and never when its handover was recorded as paying for other days too. The doctor's own card refreshes the days the entries touch. While a day stands on Marg's own modes (bank and POS not in), a payment into another account is left out — Marg keyed it as UPI already. Fail-soft: no table or module → the old figure. *(Cold review: SAFE; its three SHOULDs built in.)*
2. **S825's open note — the tables fallback.** `purchase_app._in_transit` leaves out a scan-tied order line that its
   dealer's scanned bill does not carry (`stock_figure.s825_bill_judged`, read only); such a line stays on order and is no
   longer also counted in transit. Only the fallback engine (`order.engine_source = tables`) and the old plan read this;
   the live engine (spine) is untouched. Any failure → the old reading.

| file | from | to |
|---|---|---|
| /root/finance/darpan_kal.py | d27ed062 | 5b055ed8 (4 anchors + helpers) |
| /root/finance/darpan_kal.html | b7d2d61e | 1d873251 (2 rows) |
| /root/finance/purchase_app.py | c15bc1c5 | 453d842a (2 anchors) |

## Install (after his publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s879kit && cp -rp /root/deploy/repo/deploy_kits/S879_DARPAN_ENTRIES_TRANSIT /tmp/s879kit && bash /tmp/s879kit/install_S879_DARPAN_ENTRIES_TRANSIT.sh
```
## Undo
```
bash /root/deploy/repo/deploy_kits/S879_DARPAN_ENTRIES_TRANSIT/undo_s879.sh
```
