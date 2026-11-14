# S842_XRAY_SHEET_PHOTO — a Photo column on his X-ray sheet (the parent, S467, 14-Nov-2026)

**What changes (D979 item 5)** — `/root/finance/clinic_lists.py` 92aca69e → the TO pin in `TO_PINS.md5`, replaced whole (made by `apply_s842.py` from the 14-Nov bundle's bytes, read whole). His page `https://followup.dr-manoj.in/finance/slips/lists/xray` only:
- A **Photo** column between Films and Paid, per patient and day (every line of that patient-day says the same): **Filed ↗** (opens the photo, `/finance/records/file/<id>`) · **Pending** with its due day · **Issue** (a picture of his parked — opens his X-ray check page) · **Being filed** · **Not due yet** · **X-ray not done** · "—" with no clinic ID.
- The states are Check karein's own (`check_screens.day_strip`, S836; S834's due rule; a photo that day or the two after counts) — never a copy. If they cannot be read the column shows "—" and the sheet is as before.
- Under the totals: the photos counted per patient and day, and a switch **"Not filed only (N)"** / **"Show all"**; the Excel download follows the screen and carries the Photo column.
- Cold review: SAFE TO INSTALL; its three LOW points built in (the switch keeps only rows with a state, as its count says; "could not be read" said in words; no day cap).
- The Procedures tab, the gate (his login only) and every other column are unchanged. Nothing is written.

**Proof:** `walk_s842.py` 18 / 18 on a copy of the live database with made-up patients (January 2027); the control on the live 92aca69e red 14 of 18; S691's walk (the real finance app mounted) 44 / 44 on old and new alike.

**Install (one server line):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s842kit && cp -rp /root/deploy/repo/deploy_kits/S842_XRAY_SHEET_PHOTO /tmp/s842kit && bash /tmp/s842kit/install_S842_XRAY_SHEET_PHOTO.sh
```
**Undo:** `bash /root/deploy/repo/deploy_kits/S842_XRAY_SHEET_PHOTO/install_S842_XRAY_SHEET_PHOTO.sh --undo`.
No patient name, no number, no secret in this kit (F-185).
