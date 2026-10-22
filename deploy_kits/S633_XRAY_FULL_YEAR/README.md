# S633_XRAY_FULL_YEAR — the X-ray costs page, the whole year (D767)

**The owner, 22:11 IST 22-Oct-2026:** *"the xray page, it lists expenses from july, but all from April needed there, to get the full picture of xray expenses, and film size wise incremental procurement with dates, so that the xray revenue can be analysed properly, films are regular consumables. Amc needs to be assessed monthly, fdr battery, xray online ups battery also need to be appropriately accounted for, for a better assessment of xray costs."*

Built in the Scan App chat, session 341 (no API runner — D765). Kit and D767 claimed on the board `_numbers` v618 → v619.

## What was found on the live page (22:1x IST, the owner's session, GETs)

- The head line said "since July 2026". The film bills of March–July sit only as Jugnu records on the Machines list. They are ticked for X-ray, but a machine's purchase price is never counted, so films started in August.
- The FDR AMC counted its whole year in July; the FDR battery its whole price in August.
- No view by film size, and no running totals.

## What the kit changes — `/root/assetapp/xray_costs.py` only, 22e59f5a → 5823bae2 (21 counted edits, `make_s633.py`)

1. **This financial year** (open at the top): April to the current month (or March), one row per month — films, AMC and service, batteries, papers marked, total — and the year's total. The head line reads "this month · this financial year (from April)".
2. **AMC spread:** an AMC, CMC or insurance cover with a cost is spread evenly over its months (from-day to till-day; the last month takes the paise left over). Any other cover still counts on its from-date; service and repair spends on their date.
3. **Batteries spread:** a battery's price, less what the old battery fetched, is spread evenly over its place's usual life (the "Usual life" on the battery place).
4. **Film purchases by size:** every film bill of the year, oldest first — the date, size, boxes, rupees, and the running boxes and rupees of that size — with a size summary (boxes, rupees, rupees per box). The desk's film papers come by The month's own rule, with sizes and boxes from their read item lines. The film bills kept on the Machines list come once their lines are typed.
5. **Film bills kept on the Machines list** (owner only, new door `POST /xray/film`): each record that looks like a film bill takes its lines (size, boxes, the amount with tax). It then counts with the films of its date. A line can be removed (kept, voided). A record that is also a film paper on the desk counts there, once.

assets.db: ADDITIVE — one new table `xray_film_line`, made by the part's own `ensure()` at mount. Nothing else is written. Restarts `assetapp` only.

## Proof

- `walk_s633_app.py` — the REAL app (all six parts, batteries.py at S632's TO) on a COPY of the database, made-up rows dated 2030–2031: **11 green** on the TO file. Control on the FROM file: **6 red** where it must be (C1–C5, C8). Three mutants are caught: a spread cover's paper claimed by every share (C9); the desk twin counted again (C4); a film record's own bill counted again under Papers marked (C4).
- S632's real-app walk with this file: 19 green.
- `rehearse_s633.sh` on a made-up root: 7 of 7.
- Independent cold review K1: SAFE TO INSTALL with 7 corrections. Folded into this kit:
  - a film line read with no amount gives its size no per-box price;
  - a film record's own bill, marked for X-ray, counts once;
  - the desk twin is matched by the record's bill link first, by its lines or its price, and only when The month really counts that paper;
  - The month's selection is read once per section and month;
  - the current month's row is bold;
  - a battery taken out early is spread only to its taken-out month;
  - a cover with a cost and no till-day says "not spread".
  Not changed (minor): sizes written in centimetres; film records with no purchase date are not flagged.

## Install — the owner's one line on the server, after his publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S633_XRAY_FULL_YEAR/install_s633.sh
```

## Undo

```
\cp /root/assetapp/xray_costs.py.bak_S633_22e59f5a /root/assetapp/xray_costs.py
```
```
systemctl restart assetapp
```

## After the install (the chat, through the page's own door in the owner's browser — data only)

The film lines of the Jugnu bills kept on the Machines list, read from their photos.
