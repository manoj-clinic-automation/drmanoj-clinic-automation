# S295_FOUR_ITEMS

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S295_FOUR_ITEMS/install_S295_FOUR_ITEMS.sh
```

**A — staff attendance tile.** A new portal tile *Meri attendance* opens `/register/me`: that staff member's own punch for today, *Mark me present*, *Mark my exit*. It is given by **role** (staff, manager), so every staff login has it now and every new staff login gets it the day it is created — nothing else to switch on. The physiotherapist is masked (not on the biometric). The owner-view *Attendance* tile stays masked for staff. At the end the installer prints, read-only, which logins open their page and which staff have no login yet.

**B — SMS where staff look.** While the bank's MPR file has not arrived, the morning match says *"Bank SMS this morning: ₹… credited — the early figure; the bank file (MPR) has not arrived yet, so the match waits for it."* and Darpan's day card shows *5a · Bank ka SMS — ₹… aaya*. Once the MPR comes, both return to the MPR exactly as before.

**C — petty photos off the box.** `petty_backup.py` tars `/root/finance/petty_uploads` nightly at 02:40, verifies it, and ships it with the asset register's proven Drive code to two owner-owned slots (`petty_uploads_nightly.tar.gz`, `petty_uploads_monthly.tar.gz`, created at S265). Log `/root/backups/petty_backup.log`, one line a night.

**D — Docterz reader.** The two June workbooks on Drive (11-Jun, 13-Jun) were made before the tracker wrote a *Day Revenue* sheet; the reader now remembers them (`/root/finance/docterz_nosheet.json`) instead of downloading and failing them every ten minutes.

**Proof:** `walk_s295.py` 16 checks over a scratch copy of the real finance.db (negative controls: old clinic_money red at 5, old darpan_app red at 8) · `petty_backup.py --selftest` 6 checks (negative control red at 1) · `test_docterz_s295.py` 8 checks (negative control red at 1) · portal tile visibility read from the real portal module for staff, manager, bhati and the doctor · installer rehearsed.
