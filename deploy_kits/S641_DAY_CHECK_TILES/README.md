# S641_DAY_CHECK_TILES — the bank part for everyone, Morning match tidied, two tiles (kit S641, session S347, 24-Oct-2026)

**Why.** The owner, 24-Oct-2026 22:35–22:40 IST: *"design a way where all can see the bank arrival part as it was existing
and confusing parts are no longer populated"* · *"I should also get this as a tile in my PWA. Where I can myself do the entries
etc. And for the slip work, which I need to do from my chamber, myself when the other staff is on leave, also should have a tile"*.

**What changes.**
1. `/root/finance/clinic_money.py` (5 counted edits, `make_s641.py`): with day_check.py beside it, Morning match no longer
   raises the counter-vs-Docterz total as a flag to explain in words — a note points to the day check, which names it patient
   by patient — and no longer guesses "almost certainly <patient>'s" for bank money rung as cash. Its verdict never says the
   records agree while they differ. Every bank flag (never reached the bank, arrived with no entry, MPR missing / refused, SMS
   or POS difference) is unchanged. New `bank_part()`: the bank words as Morning match shows them. Without day_check.py the
   file behaves exactly as before. On 1–22 Oct, the only flags that change are the six total-difference flags.
2. `/root/finance/day_check.py`: the bank part under the cards, the same for staff and the owner, each bank flag with
   *Answer on Morning match*; his tile lands on the oldest day of the week that still has lines.
3. `/root/finance/aaj_seed.py`: Morning match off reception's list (Din ki galtiyan does that job); the page stays.
4. `/root/finance/owner_console.py`: the new verdict reads "see the day check".
5. `/root/portal/portal.py`: two doctor tiles — **Day check** (Docterz & clinic day) and **Parchi desk** (Patients).

**Proven.** `walk_s641.py` 14/14 on S636's made-up days (`--old`: 10 S641 red, 0 older red); on the 24-Oct database on
manojz, 22-Oct: Morning match keeps exactly one flag (₹500 never reached the bank) and its bank line reads as before.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s641kit && cp -rp /root/deploy/repo/deploy_kits/S641_DAY_CHECK_TILES /tmp/s641kit && bash /tmp/s641kit/install_S641_DAY_CHECK_TILES.sh
```
## Undo
```
for f in /root/finance/clinic_money.py /root/finance/day_check.py /root/finance/aaj_seed.py /root/finance/owner_console.py /root/portal/portal.py; do \cp -p $f.bak_S641 $f; done; systemctl restart clinic-finance clinic-portal
```
