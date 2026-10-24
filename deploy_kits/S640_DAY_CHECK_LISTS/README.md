# S640_DAY_CHECK_LISTS — the day's corrections on the staff's lists (kit S640, session S347, 24-Oct-2026 · D776 stage 3)

**Why.** D776 (the owner, 23/24-Oct-2026): the corrections reach Shivani, Alisha and Shavez on their own lists, by name;
*"The Docterz re export of the day is possible only thru my Docterz login currently, and it should overwrite the old export"*.

**What changes.**
1. `/root/finance/day_check.py` `f223cbf6` → `332bc8d4` (4 counted edits, `make_s640.py`): a door
   `/finance/clinic/check/api/mine` gives each login its own open lines of the last 7 days, named (Docterz lines for Shivani,
   Alisha, Shavez; parchi lines for Shavez, Bhati) and `/finance/clinic/check/mine` opens the oldest such day. A line ticked
   and waiting is not theirs to do; when the Docterz file of that day comes in AFTER the tick and still shows the line, the
   tick no longer counts: the card says *"Theek nahi hua"* and the line is back on their list as *"Phir se"*. When every
   Docterz line of a day is ticked, his line reads *"Re-export <day> from Docterz"*.
2. `/root/finance/aaj_seed.py` `a97cd07b` → `ab6e4b14`: two lines, *"Din ki galtiyan: Docterz mein theek kijiye"*
   (Reception) and *"Din ki galtiyan: Docterz aur parchi theek kijiye"* (Shavez). On his saved panel they arrive **OFF**,
   marked new — his switch.
3. `/root/finance/aaj_duties.json` `fa5cfac5` → `1c49af35`: the two lines are read from the day check's door (shipped as
   `aaj_duties.json.kit`; `.gitignore` blocks `*.json`).
4. `/root/finance/aaj_kaam.html` `b58d8f76` → `9f8fb9df`: a door's line may carry its own words — the list names the
   patients instead of a fixed sentence.

**Proven.** `walk_s640.py` 17/17 on S636's made-up days (`--old` on the live files: 15 S640 red, 0 older red); on the
24-Oct database on manojz: Shivani 9 lines over 5 days, Shavez 14, Bhati 5, each named.

**No data step.** One restart of `clinic-finance`.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s640kit && cp -rp /root/deploy/repo/deploy_kits/S640_DAY_CHECK_LISTS /tmp/s640kit && bash /tmp/s640kit/install_S640_DAY_CHECK_LISTS.sh
```
## Undo
```
for f in day_check.py aaj_seed.py aaj_kaam.html aaj_duties.json; do \cp -p /root/finance/$f.bak_S640 /root/finance/$f; done; systemctl restart clinic-finance
```
