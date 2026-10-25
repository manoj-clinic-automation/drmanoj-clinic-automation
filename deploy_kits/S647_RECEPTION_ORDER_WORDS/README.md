# S647_RECEPTION_ORDER_WORDS — reception's late-order line says what it counts (kit S647, session S349, 25-Oct-2026)

**Why.** The owner, 25-Oct-2026 07:55 IST, *"do both"* — yes to the wording *Order ka maal nahi aaya — supplier ko call kijiye*.
Since the Sanjeevni chat's S619 (22-Oct) the duty `reception.order_arrival` counts orders whose goods have NOT come; its line
still read *Maal aaya hai: supplier ka bill scan kijiye*. Reception's panel was never saved, so the seed's words are hers.

**What changes.** `/root/finance/aaj_seed.py` 2df0d3a9 (S645's TO) → 98f63364, one counted edit (`make_s647.py`): that line's
`hi` and `en`. Nothing else; no data step; restarts clinic-finance.

**Proven.** `walk_s647.py` 4/4 on the 25-Oct database copy: her line reads the new words, is still a job line in *Jab aaye*, her
list has no unread line, every other line of every person's list (section, kind, words) is as before. `--old`: 2 S647 red, 0 older.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s647kit && cp -rp /root/deploy/repo/deploy_kits/S647_RECEPTION_ORDER_WORDS /tmp/s647kit && bash /tmp/s647kit/install_S647_RECEPTION_ORDER_WORDS.sh
```
## Undo
```
\cp -p /root/finance/aaj_seed.py.bak_S647 /root/finance/aaj_seed.py; systemctl restart clinic-finance
```
