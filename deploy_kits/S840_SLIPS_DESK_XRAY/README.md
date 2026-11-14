# S840_SLIPS_DESK_XRAY — the slips desk: X-ray uploads and the name search (the parent; built S465, rebuilt S467, 14-Nov-2026)

**What changes (D979 item 4, A-D55)** — `/root/finance/parchi_desk.py` 5ec8aebc → the TO pin in `TO_PINS.md5`, replaced whole (made by `apply_s840.py` from the 14-Nov bundle's bytes, read whole):
- The green strip at the top also says **"X-ray upload baaki N"** — N is Check karein's own count (`check_screens.day_strip`, S836), never a copy of the due rule.
- A box **"X-ray, pichhle 7 din"** under the day's skipped numbers: per day, how many X-rays, how many filed, and each one not yet filed by name and state (photo baaki / abhi samay hai / photo atki / file ho rahi / X-ray nahi hua). Open when something is pending.
- The three clinic-ID boxes (OPD, X-ray / Proc, Blood) take a **name** too: "Clinic ID ya naam". Three or more letters bring a list under the box — ID · name · the mobile's last four · "aaj/kal aaya" — from a NEW door `GET /finance/slips/desk/api/find?q=&day=` (`check_screens.find_people`; never a merged patient, never a full mobile). A tap fills the ID.
- **A name is never saved as a clinic ID**: the page refuses to save a box holding a letter (one match is picked and the next Save saves it; otherwise "pick from the list"); the save and blood doors refuse a clinic ID with a letter that the master does not know. (The 14-Nov copy held 8 slips since 29-Sep whose "clinic ID" is a name.)
- The list closes on a save and on Escape, hides when the box loses focus, and a changed box drops the old list at once; an ID picked from the list is never taken for a name (a master ID may hold a letter). Cold review: SAFE TO INSTALL; its three page points built in and walked (B11, B12); its fourth (a lone "Ram" or "Kumar" finds nothing -- `find_people` drops those words) answered by the wording "type the full name or the clinic ID".

**Proof:** `walk_s840.py` 25 / 25 on a copy of the live database with made-up patients (January 2027) — the page, its scripts parsed by node and `idFor` run in node, the name door, the save and blood doors; the control on the live 5ec8aebc red 18 of 25; S654's and S667's walks identical old vs new.

**Install (one server line):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s840kit && cp -rp /root/deploy/repo/deploy_kits/S840_SLIPS_DESK_XRAY /tmp/s840kit && bash /tmp/s840kit/install_S840_SLIPS_DESK_XRAY.sh
```
**Undo:** `bash /root/deploy/repo/deploy_kits/S840_SLIPS_DESK_XRAY/install_S840_SLIPS_DESK_XRAY.sh --undo` (refuses if a later change is on the file).
No patient name, no number, no secret in this kit (F-185).
