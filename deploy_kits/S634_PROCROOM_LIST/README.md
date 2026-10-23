# S634_PROCROOM_LIST — the procedure-room product list, each slip line's place, his rates (D773 Kit 1)

**Why.** The owner's rulings D773 (S342, 04:39–06:32 IST 23-Oct-2026): one product list for the procedure-room goods, his; every slip
line in its own place; the rates his only, never on a staff screen; history from April 2026 from his WhatsApp photos. His "okay to start"
on the S345 mock-ups (`https://claude.ai/artifact/3Doc4wew9qUonpFxZtDD7W`, artboards 1 and 3), 08:31 IST 23-Oct-2026. Board `_numbers`
v631 → v632 (kit S634). Built in the Scan App chat, session 345.

**What changes.**
1. **His list** — new part `procroom.py`: 30 products written once by the installer's data step (S342 table A, his names; X-ray films,
   Marker and the OT gloves are not on it; Primecast is a brand of Fibrecast, not a product). Each product: name (what and size), unit,
   how it is counted (per patient / month-end match / allowance), state (in use / rarely used / retired), brands, other spellings (the
   reader's misreadings map to it), reorder level. Edited in place on his page; a product with lines is retired, never deleted.
2. **The sorting desk** (him and Shavez) — with *Procedure room* chosen, a box **Procedure room lines**: each line read from the paper,
   pre-chosen from the list by its words or other spellings (a suggestion; nothing is saved without Save), its quantity, its brand and
   its **place**: Procedure room · Home use (Dr MK) · Clinic equipment · OT (surgery cases) · Sanjeevni (orthotics — an orthotic word
   pre-places the line there, flagged for him). A Procedure room line needs a product, or **"Not on the list — for Dr Manoj"** (it waits
   on his page); a line kept elsewhere may carry its name only. Only the owner sees **"+ Add to the list"**. **No rupee and no rate** in
   the box or in what the desk sends to a manager's browser for a Procedure room paper — one in Procedure room, suggested to it, or Yuvika's (its stationery panel, which carries the paper's printed rates, is not sent either); a paper not yet sorted and not suggested still carries the stationery panel as before (its printed rate is the one on the paper in his hand); the rate read from a printed paper is kept unseen on the line. A re-save replaces
   the paper's lines (the old ones voided, kept); a paper re-sorted out of Procedure room has its lines voided. The desk stays in
   English, as the rest of the desk is (the mock-up's Roman Hinglish words are kept for Shavez's own next-morning screen, Kit 3).
3. **Counted when read** (stationery.py's rule, S568 FIX1, for the group *procedure*): a paper's lines count only while it is a live
   paper in Procedure room or a challan / estimate joined into one; a bill only when no challan / estimate is joined into it. A photo
   slip's lines count while the slip is not voided.
4. **His page — "Procedure room"** (the one menu, the owner only; `https://followup.dr-manoj.in/scanapp/procroom`): this month or the
   financial year; *Worth a look* (a rate changed against the last one for that product and brand; orthotics on clinic slips; lines
   without a rate; lines waiting for his list); **By product** (bought, spent, last rate and brand, the rates by brand); **By month**
   for the financial year (slips, scanned, only a photo, Procedure room, all places); **Kept elsewhere**; **Slips and their rates** —
   every slip with a rate box per line (his rate; the read rate in grey until he types one); **+ A slip from a photo** (date, supplier,
   up to 8 lines; or, with *Scanned as B-xxxx*, the lines onto that scanned paper); **Rarely used and retired**; **Your list and
   allowances** (examination gloves: 2 pairs a cast or slab, 1 an ILI, the box size blank until he says).
5. Not in this kit: the order scan and order ↔ delivery, the month-end WhatsApp check (Kit 2); Shavez's next-morning screen, use, stock
   and *Order now* (Kit 3).

**Files and pins (FROM → TO).** `/root/assetapp/sorting_desk.py` `377adbca` → `43658394` (10 counted edits) · `asset_register.py`
`2bb28600` → `068440f7` (2) · **new** `procroom.py` (absent → `a641f640`). Read only, pinned: `clinic_papers.py 89a3cd0a`,
`asset_machine.py 7dbd5e0c`, `stationery.py b6ce217a`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`, `claude_reader.py 10118909`,
`claude_reread.py ed7023d2`. Every edit is an anchor found exactly once in the live bytes (`make_s634.py`). `scanner_widget.js` is not
touched; no file of the parent's or of the Sanjeevni chat's is touched. **Data step** (after the database backup): the three tables
`proc_item`, `proc_slip`, `proc_line` (additive, also made by the part's own `ensure()` at mount) and the list of 30, once (settings key
`procroom.seed_s634`; a second run writes nothing). No rate, phone, account or vendor figure is in the kit (F-185): the April–September
history is entered after the install through his own page.

**Kit.** `make_s634.py` · `procroom.py` · `walk_s634_app.py` (A0–A1, B1–B3, C1–C6, D1–D10, E1–E2, F1–F3, G1 and the old pages R1–R3;
`--expect-red` = the control on the live files: every new check red, R1–R3 green) · `walk/browser_desk_s634.py` (headless Chromium:
the desk's panel end to end as a manager, his page at 390 px and 1280 px; not run on the box) · `install_s634.sh` · `rehearse_s634.sh`
(R1–R8) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Proof (23-Oct-2026, in the Scan App chat, on the 23-Oct bundle's code with a fresh made-up database):** the walk 30 green / 0 red; the
control on the FROM files 27 red, AS IT MUST BE (R1–R3 green); the browser walk 5 green (its control red as it must be); the rehearsal
8 green. On the box the installer runs the walk and the control again on a COPY of the live database before placing.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S634_PROCROOM_LIST/install_s634.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/sorting_desk.py.bak_S634_377adbca /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/asset_register.py.bak_S634_2bb28600 /root/assetapp/asset_register.py && mv -f /root/assetapp/procroom.py /root/assetapp/procroom.py.off_S634 && systemctl restart assetapp`
— then `/healthz` 200 and the md5s back at the FROM pins. The three new tables stay (unread by the old files); the database backup
`assets.db.bak_S634_<stamp>` is needed only if their rows must be removed — say so before using it.
