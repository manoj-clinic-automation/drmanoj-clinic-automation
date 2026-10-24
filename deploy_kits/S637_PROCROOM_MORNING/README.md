# S637_PROCROOM_MORNING — Shavez's next-morning screen, used and in stock, Order now, the month-end match (D773 Kit 3)

**Why.** The owner's rulings D773 and D774 (S342, 23-Oct-2026; the plan's C 6–9): Awdhesh's room work moves to Shavez — the
procedures done are the X-ray/Proc slips confirmed by Docterz's procedure lines; Shavez enters each one's consumables next morning,
pre-filled with the procedure's usual kit; a slip with no Docterz line is skipped as *not done*; the gloves by his allowance (2 pairs a
cast or slab, 1 an ILI); his page shows used, stock, *Order now* under the reorder level and a month-end rough match. F-1011 (the
consumables were defined on his rate page but no use was ever recorded). The mock-up (`https://claude.ai/artifact/3Doc4wew9qUonpFxZtDD7W`,
artboard 2) accepted "okay to start" 08:31 IST 23-Oct-2026; his "start it" for Kit 3, 21:45 IST 24-Oct-2026. Board `_numbers` v645 →
v646 (kit S637). Built in the Scan App chat, session 346.

**What changes.**
1. **Kal ke procedures** — `https://followup.dr-manoj.in/scanapp/procroom/morning` — Roman Hinglish, as the mock-up. Installed
   **SWITCHED OFF for the staff**: the owner sees it first (in his menu, with a note), and switches it on from his Procedure room page
   (*Switch on for Shavez*); then it is in Shavez's menu. Yesterday's X-ray/Proc slips that carry a procedure, read from the parent's
   slip book **read only** (the finance database: `slip`, `slip_item`, `owner_service`, `owner_service_item`, `clinic_day_line`,
   `clinic_day_revenue`, `patient_ref` — as `scan_checks_s441` already reads it); the slips Docterz confirms (a procedure line for that
   clinic ID that day) are to fill, the others are shown greyed as *nahi hua*; before Docterz's report comes, every slip is shown. Each
   procedure's kit is his rate page's: Fibrecast, Roller bandage and Cast padding by size × count, Stockinette a tick, the injection one of
   two, the D600 drape a tick (on casts and slabs too) — each on his product list where it is one. His rate page stores no usual quantity,
   so each line is **pre-filled from the last time that procedure was entered** (blank the first time). The gloves by his allowance, by
   themselves, per procedure (two casts on one slip, two allowances; the clavicle bandage is neither, his ruling). *+ Saamaan jodein*
   for anything else. The same procedure twice on a slip (R and L) has its own lines for each. **One Save** for the day — only the slips that page showed (a slip written into the book after the page was opened is told
   back: *page dobara kholein*); an unchanged slip is not written again; a slip's earlier
   record is voided, kept. The last week's days still to fill are offered. No rupee, no rate.
2. **His page — Procedure room** — a card for the morning screen (on / off, *Open it*); **Used and in stock** — used in the period (the
   morning screen), his last shelf count, the stock now (count + bought after it − used after it; gloves used in pairs, bought in boxes
   of his box size), **Order now** under the reorder level he sets on his list (and in *Worth a look*), a count to type for each product;
   **Month-end match** — casts and slabs, injections and other procedures done, and each month-end product bought per ten procedures
   against the year's figure.
3. Nothing of the parent's is changed: the slip book, Awdhesh's ticks and the rate page stay as they are (retiring Awdhesh's Paid/Done
   reminder is the parent's D775). No patient detail is stored by the scan app: a saved slip keeps the slip book's own id and the slip
   number only.

**Files and pins (FROM → TO).** `/root/assetapp/procroom.py` `1ccd1e03` (Kit 2's) → `ad0815e1`, the kit's whole file. No other file.
Read only, pinned: `sorting_desk.py ca9fda74`, `asset_register.py 068440f7`, `clinic_papers.py 89a3cd0a`, `claude_reader.py 10118909`,
`claude_reread.py ed7023d2`, `asset_machine.py 7dbd5e0c`, `stationery.py b6ce217a`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`.
assets.db ADDITIVE: `proc_use_slip`, `proc_use`, `proc_count` (made by the part's own `ensure()` at mount). One setting the owner
writes from his page: `proc.morning` (absent = off). No rate, phone, account or vendor figure in the kit (F-185).

**Kit.** `make_s637.py` · `procroom.py` · `walk_s637_app.py` (A0–A1, N1–N14, S1–S4, K1, R2 — on a COPY of the live database and a
MADE-UP slip book, never the real finance database; `--expect-red` = the control on Kit 2's file: every new check red, K1 and R2 green) ·
`walk/browser_morning_s637.py` (headless Chromium: Shavez at 390 px fills and saves, the same slip at 1366 px, his page at 390 px; not run
on the box) · `install_s637.sh` · `rehearse_s637.sh` (R1–R7) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Independent cold review (K1):** round 1 NOT SAFE — two blockers (the same procedure twice on a slip shared its fields; one Save
rewrote slips the page had not shown) and five corrections (a slip saved before Docterz's report, then not in it, still counted; the
clavicle bandage counted as a cast; gloves per slip, not per procedure; the page's old words; an unreadable finance database as an error
page) — all fixed, walk checks N10–N13 (a saved slip Docterz later does not have is left out of every count and named in Worth a look);
round 2 NOT SAFE — one blocker left (a slip with the same procedure on both sides, reopened and saved, took the first side's
values for both) — fixed: each saved line keeps its own place on the slip; walk check N14 (red on the round-2 file, green on the fix);
round 3 below.

**Proof (24-Oct-2026, in the Scan App chat, on the 24-Oct bundle's code + Kit 2):** the walk 22 green / 0 red; the control 20 red, AS IT
MUST BE; Kit 2's walk on the new file 32 green and Kit 1's 29 green, each with only its own version check red; the browser walk 4 green
(control 3 red); the rehearsal 7 green.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S637_PROCROOM_MORNING/install_s637.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/procroom.py.bak_S637_1ccd1e03 /root/assetapp/procroom.py && systemctl restart assetapp`
— then `/healthz` 200 and the md5 back at `1ccd1e03`. The three new tables and the setting stay (unread by Kit 2's file).
