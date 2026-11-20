# S894_ASKED_COUNT_BACK — an asked count reaches the owner; Amir balances ZIBON EXTRA and GEMCAL XT (session 490, the Sanjeevni chat, 20-Nov-2026)

**Why:** on 14-Nov the owner asked Darpan to count ZIBON EXTRA and GEMCAL XT (F-1401). Darpan counted them on 18-Nov (10:59 and 11:06), on a later day's list (the requests were *carried* from 16-Nov). The owner heard nothing: an asked count reaches only Darpan's page and the Loss desk, and the ask closes only for the roster row it was first tied to — a carried row never closed it (asks 2, 3, 4 stayed open). The owner's word 14:44 IST: "1 – to be done through Amir. He will enter stock vouchers for the same to balance their quantities. 2,3 – ok".

**What changes:** `/root/finance/stock_watch.py` f0d9092a → 1a8c98c6 (make_s894.py, four exact anchors + three new functions: `_s894_text`, `_s894_asked_back`, `_s894_refix`). When Darpan answers an item the owner asked for (the morning list, or *Stock batao*), every open ask for that item closes and ONE Needs-you line is written (notice kind `asked_count`, 7 days, one per item per day): *Darpan counted ZIBON EXTRA (you asked): 20 strips + 6 tabs -- Marg (closing 18-11-2026) 35 strips + 9 tabs -- 15 strips + 3 tabs fewer than Marg* (warn; *matches Marg* shows as info). The line is written first and the ask closed after it; a same-day "Galat likha? Badlo" rewrites the line; Marg read by its closing date. Fail-soft: the count is stored first and is never stopped.

**Data (s894_job.py):** two tap jobs on Amir's card — *ZIBON EXTRA — STOCK ISSUE 15:3* and *GEMCAL XT TABLETS — STOCK ISSUE 0:4* (Darpan's 20:6 and 15:12 against Marg's 35:9 and 16:1; no sale of either 16–18 Nov) — refused if Marg's newest closing no longer stands above the count; and the asks Darpan has since answered closed (ANKLE BINDER L BAMBOO 0 = Marg 0, ZIBON EXTRA, GEMCAL XT).

**Install:** his publish, then one server line:

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s894kit && cp -rp /root/deploy/repo/deploy_kits/S894_ASKED_COUNT_BACK /tmp/s894kit && bash /tmp/s894kit/install_S894_ASKED_COUNT_BACK.sh

**Undo:** `bash /root/deploy/repo/deploy_kits/S894_ASKED_COUNT_BACK/undo_s894.sh` (the file back, clinic-finance restarted, the two jobs off Amir's card if still open).

**Proof:** `synth_s894.py` 11/11 on a copy of the 20-Nov database with the new file; the live file (control) 3/11 — red. On the box the installer runs both on copies of the live database. `rehearse_s894.sh` 7/7 (dry, red rollback, install, again, undo, tamper, drift).
