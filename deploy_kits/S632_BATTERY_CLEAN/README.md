# S632_BATTERY_CLEAN — the battery page made clean (D766)

**The owner, 19:51–19:52 IST 22-Oct-2026:** *"I feel all such extra useless data needs to be deleted, and the page and all its content should be made relevant"* · *"thoroughly analyze the battery page … give me a clean battery page which has all the relevant scans and fields filled in properly."*

Built in the Scan App chat, session 341 (no API runner — D765). Kit claimed on the board `_numbers` v616 → v617.

## What was found on the live page (read 20:3x–20:4x IST 22-Oct, the owner's session, GETs; nine papers read by a sub-agent)

- A saved battery could not be corrected or removed — no door. Wrong or missing make, warranty months, price and supplier stayed as first typed.
- B-0104 (B.L. Computers' statement: one invoice carries the Lab PC's UPS battery of 06-07-2026, another the three UPS batteries of 01-08-2026, NK Pathology's set) could be the bill of only one battery. Linked, the statement's whole total showed as the battery's cost.
- `B.L.Computers` (no space) was not matched to the place's supplier `B.L. Computers`, so its papers were not offered.
- The bill photos kept on the linked machine records (Generator, Wagon R, Bike, Home inverter, Scooty, FDR) were nowhere on the battery page; the battery in use read "no bill (old battery)".
- The X-ray detector's lithium battery sat under *Online UPS* with a UPS backup-check upkeep. The page had no door for the group or the upkeep.
- "yours only" was printed twice in an owner-only place's header.

## What the kit changes — `/root/assetapp/batteries.py` only, b2cbb41e → bb082b4c (20 counted edits, `make_s632.py`)

1. **Correct a battery entry** (the owner only, server-side; `POST /batteries/fitfix`) on each place's page. It changes a saved battery's fitted / taken-out dates, supplier, make · type, Ah, set, warranty months, price and old-battery amount. **Entered by mistake — remove** keeps the row (`voided_at`), never deletes it; the battery before it is in use again. A new fitted date keeps the entries' order, and the previous battery's taken-out date moves with it. Linked papers are never written (D664).
2. One paper may be the bill of more than one battery (a statement). A fitting with no price shows the paper's total as *"(the whole bill)"*.
3. `B.L.Computers` = B.L. Computers.
4. A fifth group, **Machine batteries**. **Change this place** takes the group and the upkeep (none / UPS backup check / inverter water / generator start, every N months). A form without those fields keeps what the place had.
5. The place page lists **Scans on the machine record** (the owner only). The battery in use with no paper links to that scan. "yours only" is printed once.

No database change: the new door writes S571's own columns. Restarts `assetapp` only.

## Proof

- `walk_s632_app.py` — the REAL app (all six parts) on a COPY of the database, made-up rows dated 2029–2031, the switch `batteries.on` ON so a manager passes the gate and the door itself must refuse: **19 green** on the TO file. Control on the FROM file: **14 red** where it must be. Three mutants are caught: the owner check taken out (B9 red); removal without reconnecting the neighbouring entries (B5, B15, B16, B17 red); the neighbour chosen by date and not by the page's order (B18 red, two batteries fitted the same day).
- S624's real-app walk on the TO file: 8 green.
- `rehearse_s632.sh` on a made-up root: 7 of 7 (dry, install, again = ALREADY INSTALLED, FROM moved, foreign lock, red health → restored, a read-only file moved).
- Independent cold review K1 (a sub-agent given the code, not the conclusion): 1 blocker and 6 corrections. Fixed in this kit: removing or re-dating an entry can no longer leave a place with nothing in use or overlapping entries; a field missing from a POST keeps its value; the walk's manager test now reaches the door; the two `confirm()` texts read from data attributes; a new Machine-batteries place gets no Jasoria / 54-month default; a paper shared by places of two payers pre-selects nothing on the desk. K1's second read found one more blocker, introduced by the first fix: removing the earlier of two batteries fitted the same day left nothing in use. Fixed: the neighbouring entries are taken by the page's own order (newest first), never by date alone; B18 walks it.

## Install — the owner's one line on the server, after his publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S632_BATTERY_CLEAN/install_s632.sh
```

## Undo

```
\cp /root/assetapp/batteries.py.bak_S632_b2cbb41e /root/assetapp/batteries.py
```
```
systemctl restart assetapp
```

## After the install (the chat, through the page's own doors in the owner's browser — data only)

The fittings filled from their bills. FDR battery moved to *Machine batteries*, with no upkeep. B-0104 linked as NK Pathology's bill too, with the two prices set. The Scooty fitting's supplier. Each change is in the desk's audit book (`battery_fit_corrected`, `battery_fit_voided`, `battery_place_changed`).
