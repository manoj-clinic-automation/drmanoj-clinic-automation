# S820_ORDER_CARRY_ON_TAP — an undelivered medicine goes to the dealer only on "Dobara order karo" (13-Nov-2026, Sanjeevni session 451)

**The owner, 18:13 IST 13-Nov:** today's supplier WhatsApp orders also carried the old orders that will not be delivered, without any confirmation. **His "Go", 18:15 IST**, on: an undelivered medicine is no longer added to the dealer's next order by itself (S619's carry, his 22-Oct ruling, revised); it waits in the red *Purane order* box at the top of reception's order screen (S778) and goes to the dealer only when the staff tap *Dobara order karo*; *Ab nahi milta* as before.

**The kit** (five files, rebuilt on the box from the live bytes by `make_s820.py`, exact anchors that occur once):
1. `/root/finance/order_sheet.py` (53abf461 → TO) — a setting `order.carry_on_card` (0 = the box only, now; 1 = the old way), on his settings card; `entries()` puts the open carries on a card only at 1. The screen, the WhatsApp text and the printed sheet all read `entries()`, so all three change together.
2. `/root/finance/order_s778.py` (819f60ff → TO) — with the setting at 0 an undelivered line is in the box at once (it is known not to have come), not only after three working days as a late order is.
3. `/root/finance/porders_s454.py` (21bf0abc → TO) — the settings card accepts 0 / 1 for it.
4. `/root/finance/order_track.py` (6f4746c5 → TO) — the words follow the setting: a short line on the order list, Darpan's line (Kal ka hisaab) and the owner's Needs-you line no longer say "back on the next order by itself"; they say it waits in the Purane order box for *Dobara order karo*.
5. `/root/finance/order_track_page.py` (4e6bd715 → TO) — the order list's short section: the same, instead of "nothing to do".

No database change. The box and its two buttons are as they were; only the sentences that promised "by itself" change.

**Proof before it left the bench.** `walk_s820.py` 15/15 GREEN on the rebuilt files (a copy of the 13-Nov database, made-up rows only), its control on the live files red (9 of 15) · the red box rendered with the rebuilt files on the copy (16 lines, as live) · Darpan's line on 10-12 Nov read with the new words · `rehearse_s820.sh` 7/7 on a stand-in root. **Cold review by a second reader:** SAFE AFTER FIXES — no other way for an undelivered line to reach a card, the WhatsApp or the print; its own end-to-end test on the database copy (all 11 open carries in the box, none on a card; *Dobara* → the order → the carry closed, nothing twice); ONE must-fix, built: four sentences (order list, its short section, Darpan's line, the owner's Needs-you line) still said "by itself / nothing to do" — they now follow the setting (G7). Left, said so: a line 0 days old shows "0 din"; a *Dobara*'d line's WhatsApp text no longer adds "pichhle order se baaki (dd-mm)".

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s820kit && cp -rp /root/deploy/repo/deploy_kits/S820_ORDER_CARRY_ON_TAP /tmp/s820kit && bash /tmp/s820kit/install_S820_ORDER_CARRY_ON_TAP.sh

**Undo:** the installer prints the one line (the three backups back, clinic-finance restarted); or set `order.carry_on_card` to 1 on his settings card.
