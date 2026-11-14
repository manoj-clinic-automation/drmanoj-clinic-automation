# S410 — Procedure room page: the owner's FINAL specification (14-Nov-2026 14:40 IST)

The mock-up is the specification: artifact "Procedure Room — simplified page (mock-up)", v4 (version 1794647330-5ffc),
https://claude.ai/artifact/WFkBPm1Twt7NVM6gTuiUoM — the owner's word "Final" 14:40 IST. Build follows it line by line.
Live base: /root/assetapp/procroom.py e51c00a1 (S656), the owner's page /scanapp/procroom (owner only). Staff screens unchanged.

## What the page becomes (top to bottom)
1. Title + month picker (as today).
2. TILES (each a link to its section): Spent this month (Rs, counted dealer challans) · Procedure revenue (total; ILI and
   others apart) · Procedures done (casts/slabs · ILI · other) · FIBRECAST IN STOCK TODAY (5", 4", 3", 2" with rolls; red
   under the reorder level; "after your first count" until a count exists) · Waiting for you (dealer challans on the desk with
   no saved lines + month photos unread/unsaved) · Morning screen (patient slips still to fill).
3. START HERE strip, 3 steps with state: 1 Opening count (done / not done, products without a count) · 2 Purchases (the
   waiting dealer challans by stamp, the month photo) with "Open on the desk" and "Yuvika's month photo" · 3 Used (morning
   screen on/off, days to fill) with "Open Kal ke procedures".
4. EXPENSES AND REVENUE — the financial year, X-ray page style (xray_costs.py S633 FY table): one row per month, each a
   <details>: Month · Bought Rs · Procedures · ILI revenue Rs · Other procedures Rs · Revenue less bought Rs; Year-so-far row.
   NO per-procedure column (the owner: misleading). Inside a month:
   a) What was bought — dealer challans and bills: challan (stamp, dealer), date, item, qty, rate, amount (counted_rows, place proc).
   b) Procedures done — one row per PATIENT SLIP with a procedure (the slip book, finance.db slip / slip_item READ ONLY, as the
      morning screen reads it): date, patient slip no., patient, procedure, fee, items used (editable qty, + add an item);
      "not filled yet" rows; one Save for the month's edits -> the morning screen's own save (save_morning per day: a slip's earlier
      record voided, kept). Totals ILI / others.
   Revenue = the fees on those patient slips (ILI apart). Procedures counted from 1-Oct (the morning screen's floor).
5. STOCK NOW: Product · Your count (input) · + Bought since · − Used since · Stock now · Order when below (input, his reorder
   level) · Day of the count · Save the counts. GLOVES IN PAIRS, NEVER A DECIMAL: a box = 100 gloves = 50 pairs (setting
   proc.gloves_box = 50, set live 12:0x IST 14-Nov); show "8 pairs", stock "2 boxes + 14 pairs". Gloves line: 2 pairs a cast/slab,
   0 an ILI (his word: 0 is right), box of 100 gloves (50 pairs).
6. MORE, folded: Month-end match · Dealer challans and their rates (was "Slips and their rates") · Orders and deliveries ·
   + Add a dealer challan from a photo by hand · Product list and allowances.
7. A fixed "↑ Top" button.

## Wording rule
"Slip" alone means the PATIENT slip the clinic issues. Yuvika's papers are "dealer challans" everywhere on this page
(his word 12:08 IST).

## Answers recorded
Gloves per ILI = 0 (intended). Box = 100 pieces = 50 pairs. Reader key replaced (the old key expired 13-Nov).
