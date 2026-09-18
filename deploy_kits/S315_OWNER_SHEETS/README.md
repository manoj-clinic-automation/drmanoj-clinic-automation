# S315_OWNER_SHEETS

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S315_OWNER_SHEETS/install_S315_OWNER_SHEETS.sh
```

The owner asked for the procedure → consumables sheet and the X-ray price list "somewhere I can work — the tile". This is that place: a doctor-only page at `/finance/clinic/sheets`, reached from a new portal tile **Procedures & prices**.

**What he sees.** Two sheets. Each one lists what he has already named, and under it **every amount his own Docterz days actually carry** for that section in the last 180 days — with how many times and when it was last billed — so naming a price is one box and one tap, not a typing job. A procedure then takes its consumables from the pharmacy's own item list (tap from the list, quantity, unit). Anything never billed can be added by hand.

**What it is careful about.** Two tables of its own (`owner_service`, `owner_service_item`), made on first use. `clinic_day_line` and the pharmacy item master are read, never written — the walk proves the row counts are unchanged. Doctor only: the clinic unit's checker **and** a name in `OWNER_SHEET_USERS` (default `manoj`); the tile is doctor-only too. `/finance/clinic/sheets/api/services` is the read-back door for the chamber screen that comes next — one authored source, no second copy.

**Proof:** `walk_s315.py` 25 checks through the real module over a scratch copy of the live `finance.db` (the seed really is ₹500 X-ray from the store; a duplicate name, a bad price, a zero quantity, consumables on an X-ray and a non-doctor login are all refused; the read-back door and the hidden-line rule check out). Negative controls red at 24, 12 and 14. Both patchers are anchored on text read from the live files and are idempotent; the installer restores all three files on any red.
