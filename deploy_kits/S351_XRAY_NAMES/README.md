# S351_XRAY_NAMES

**The X-ray test page read 0 of 9 staff files as matched** (20-Sep-2026). The staff write the clinic ID at the
END of the file name — `NAME 1234.jpg`, a second view as `NAME 1234 ..jpg`, sometimes no number on the second
file — while `xray_plan()` read it only at the START. Six of the nine trailing numbers were real clinic IDs with
X-ray slips on 19-Sep. This kit teaches the read-only test page the staff's real shape; nothing is filed, renamed
or moved.

- the ID is the **one** standalone run of 1–8 digits anywhere in the name (start or end);
- **two** such runs → check folder (*which is the clinic ID?*), never a guess;
- a file with **no** number takes the ID of a same-day sister file with the same name stem, and the verdict says
  so; no sister, or two sisters with two IDs → check folder.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S351_XRAY_NAMES/install_S351_XRAY_NAMES.sh
```

Pins: `records.py` `8cdd334f…` (S346) → `4c2f38b9eabca883944b32e987600963` (full file; `make_s351.py` shows the
three anchored edits it was made by) · `finance_app.py` `29819879…` (S349) checked, unchanged. Walk: 32 checks on a
scratch copy of finance.db, the walk's own rows only (F-581), the LIVE `records.py` as the negative control.
Restarts clinic-finance. Touches no Sanjeevni file, none of `finance_app.py` / `portal.py` / `tile_grants.json`.
