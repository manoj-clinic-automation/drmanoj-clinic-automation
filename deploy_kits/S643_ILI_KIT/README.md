# S643_ILI_KIT — an injection listed without items takes the injection group's items (Shavez's morning screen)

**Why.** The owner, 06:43 IST 25-Oct-2026, on Kit 3's live read: *"opened page, opened item, nowhere option to delete or move it to
procedures"* — "ILI KNEE" sits under "Other" on his rate page (`https://followup.dr-manoj.in/finance/clinic/sheets`) with no items, and
that page (the parent's `owner_sheets.py`, read: no group edit) cannot move a procedure between groups. Board `_numbers` v659 → v660
(kit S643). Built in the Scan App chat, session 346.

**What changes.** On *Kal ke procedures* (`https://followup.dr-manoj.in/scanapp/procroom/morning`), a procedure that reads as an
injection (ILI) by its group or its name, and has no items of its own on his rate page, takes the items of the first procedure of his
injection (ILI) group that has any — the injection, one of two (Loftypred 80 mg / Viracort 40), and the Surgiwear D600 drape tick. Its
gloves were already 1 pair. His rate page is untouched; an item he later adds to ILI KNEE there is used instead.

**Files and pins (FROM → TO).** `/root/assetapp/procroom.py` `ad0815e1` (S637's) → `7b936d6f`, the kit's whole file. No other file; no data step.
Read only, pinned: as S637 (`sorting_desk.py ca9fda74`, `asset_register.py 068440f7`, `clinic_papers.py 89a3cd0a`, `claude_reader.py
10118909`, `claude_reread.py ed7023d2`, `asset_machine.py 7dbd5e0c`, `stationery.py b6ce217a`, `batteries.py bb082b4c`, `xray_costs.py
5823bae2`).

**Kit.** `make_s643.py` · `procroom.py` · `walk_s643_app.py` (every S637 check, plus N15; `--expect-red` on S637's file: only A0 and N15
red) · `install_s643.sh` · `rehearse_s643.sh` (R1–R7) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S643_ILI_KIT/install_s643.sh`

**UNDO (one line):** `\cp -p /root/assetapp/procroom.py.bak_S643_ad0815e1 /root/assetapp/procroom.py && systemctl restart assetapp`
