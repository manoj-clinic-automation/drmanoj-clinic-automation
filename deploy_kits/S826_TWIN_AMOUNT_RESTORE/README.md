# S826_TWIN_AMOUNT_RESTORE — two amounts are two papers; the owner's Restore of a pharmacy scan set aside as a duplicate (14-Nov-2026, the Scan App chat's session 410)

**F-1378, the scan side** (the Sanjeevni chat's S455; the owner said go). Janta's revised bill JP21965 (B-0271, Rs 3,205 = the first paper Rs 4,450 less a Rs 1,245 return) was set aside on 08-Nov as "duplicate of B-0118" — the amounts were 28% apart, and it was set aside only because a person answered "same paper" to the twin question. The pharmacy side's repair (S824_REVISED_BILL_SETASIDE, live 08:11 IST 14-Nov) is the Sanjeevni chat's and is not touched.

**The kit** (two files, rebuilt on the box from the live bytes by `make_s826.py`; exact anchors that occur once):
1. `/root/shared/scan_checks_s441.py` (59d5cb1c → TO) — no twin question when both scans' amounts are read and differ by more than 2% (a true double carries the same amount; an amount not read is not a difference). A twin question already open on such a pair is settled *different* by the server's next pass (recorded on the scan as `not_duplicate`, how "S826"). A *same* answer on such a pair keeps both. The sure-double rule (supplier + bill-number tail + amount within 2%) and the forgotten-page rule are unchanged.
2. `/root/assetapp/asset_register.py` (74043cdb → TO) — on the owner's own bill page, a pharmacy scan set aside as a duplicate carries **Restore — not a duplicate** (one tap, one confirm). It goes back to Filed (captured), `dup_of` cleared, marked not a duplicate, the stamp number kept; recorded in `bill_audit` as `restore_s826` (who, when, what it was a duplicate of, why it was set aside). The owner's only; a joined page, a clinic-lane paper or a paper rejected by hand is refused unchanged. The pharmacy side then reads it as any captured scan.

Nothing on reception's or Shavez's screens changes. The finance app only reads the questions and is not restarted.

**Proof.** `walk_s826.py` on the real scan app with a made-up database: 26/26 GREEN on the rebuilt files; its control on the live files: every S826 check red (14 of 14), every other check green. S754's and S750's walks on the rebuilt files: 0 failed (as on the live files). `rehearse_s826.sh` 8/8 on a made-up root (dry · real · again · the undo line · a red at [4/6] and at [5/6] · a changed live file · the lock held).

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s826kit && cp -rp /root/deploy/repo/deploy_kits/S826_TWIN_AMOUNT_RESTORE /tmp/s826kit && bash /tmp/s826kit/install_S826_TWIN_AMOUNT_RESTORE.sh

**Undo:** the installer prints the one line (the two backups `*.bak_S826_<old md5>` back, assetapp restarted).

**Known and accepted:** a true double scan whose total the reader misread by more than 2% is no longer asked about — both stay filed and the pharmacy side shows the extra scan unpaired, where it is set aside by hand.
