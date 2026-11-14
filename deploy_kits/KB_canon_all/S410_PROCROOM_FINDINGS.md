# S410 — Procedure room page: findings (14-Nov-2026, read-only)

Read: procroom.py e51c00a1 (14-Nov bundle, = pin) + the live pages as manoj (a read-only helper, GET only, 08:0x IST).

## How the page computes (as built, S634/S635/S637)
- BOUGHT = lines SAVED on the sorting desk's Procedure-room panel of a paper in Clinic lane / group Procedure room (proc_line), + photo slips. Lines only READ by the reader count nothing until Save.
- USED = Shavez's morning screen "Kal ke procedures" (proc_use). ON. Oct: Fibrecast 5" 4, 4" 9, gloves 22 pairs, roller 6" 18. Nov: Fibrecast 5" 5, gloves 8 pairs, roller 6" 7. 13-Nov: 6 slips not filled.
- STOCK NOW = last shelf count + bought after it - used after it. NO shelf count exists for any of 31 products -> every Stock cell "—".
- MONTH END = Yuvika's WhatsApp photos (/procroom/month), read, matched to the scans, his Save puts his rates.

## Why it is not operational
1. No opening shelf count -> no stock anywhere (the start point).
2. Oct and Nov: 0 slips, Rs 0. B-0176 (Yuvika challan 16-10, Clinic / Procedure room) sits Waiting on the desk: lines read (5" plaster, zig-zag cotton, gloves/23 No blade) with no product/qty, never Saved.
3. B-0318 (scanned 13-11 11:57 by Alisha; likely the 1-Nov challan): read failed, group not sorted, no lines. Nothing saved for November.
4. B-0304 Yuvika SUMMARY dated 31-10, Rs 5,940, scanned 08-11, filed in the PHARMACY lane as Summary (S754 recognition) — probably the October statement; not on the Procedure room month end. Yuvika also bills orthotics to the pharmacy (B-0262 YS/0803 Rs 1,380; B-0272 its second scan, read with qty swapped, Rs 1,410, set aside by S441) — a statement may cover both.
5. Gloves box size blank (gloves stock cannot be computed); gloves per ILI stored 0 (default 1); reorder level blank on all 31 -> no "Order now".
6. Month-end match lists 6 of 17 month-end products (only those with FY purchases).
7. The page has 10 sections and no "where to start" — the owner could not find the path.

## Proposal (for his word; mock-up first)
- A "Start here" strip at the top: 1 Opening count (once) · 2 Purchases (desk Save / month-end photo) · 3 Used (morning screen) -> Stock now; each with a tick and a count of what is pending.
- Stock table first and open; the rest collapsed.
- A Yuvika paper in the pharmacy lane whose lines are procedure goods, and every Yuvika summary, shown to him on the Procedure room page ("Yuvika papers elsewhere") with one tap to bring it over.
- The opening count may be taken by Shavez on a staff screen (no rupees) — his choice.
