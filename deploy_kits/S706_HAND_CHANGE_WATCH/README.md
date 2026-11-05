# S706_HAND_CHANGE_WATCH — S386 (Sanjeevni), 05-Nov-2026 · D828

**The owner (05-Nov 10:05–10:36 IST):** the stock differences point to changes made in Marg without his knowledge; *"make it tell me the next
morning, naming the item and the day and the quantities shifted"*; the table *"goes to my stock expiry page as a section on top, collapsed, with an
alert so I open when needed."*

| file | from | to | what |
|---|---|---|---|
| `/root/finance/owner_notice.py` | 2bc96912 | ca5cd443 | the `hand:` message (08:00–21:00; one per finding run; opens the Expiry watch); the phone line says the clinic Wi-Fi is fine |
| `/root/finance/expiry_watch.py` | 15417df5 | 1ed95b6c | the top section, collapsed, red "N new" and "N open"; renames apart; put right / explained for 30 days |
| `/root/finance/marg_hand_change.py` | — | 8d69c55d | NEW: the finder (spine.db + Amir's filed vouchers read-only; its own table `marg_hand_change`) |

**How a hand change is told apart:** per item, Marg minus the spine's balance minus Amir's filed vouchers, closing by closing. A step is a shift.
Not a hand change: a purchase (or a purchase return) the system holds that Marg's closing did not have yet (owed, paid by Marg's catch-up); a
step undone within three closings; a same-quantity swap between two names with the same letters (a rename -- paired even when one half is not
judged yet). A step is judged only when the accepted sale exports cover every day of its window (Sundays too); a closing printed with under 90% of
its neighbours' items is skipped. A fall is told the next morning, except one whose window holds an Amir day (only he keys purchases and returns):
that waits for the purchase reports, as every rise does. Amir's vouchers on file but unreadable: the refresh stops and writes nothing. Told only:
open rows, found after the first fill, whose change is at most ten days old; a row's message key is its own (found inside 08:00-21:00: its
time; outside: the next morning's 08:00 batch), so nothing is told twice. The first fill is
the history: on the page, never announced, never "new". The owner's 05-Nov notes explain only the shifts up to 4-Nov.

Cold review R1 (NOT SAFE: B1 explained rows still told, B2 returns/renames told as falls, B3 voucher read failing open, B4 Sunday exempt) -- all
built, with S1, S2, S4, S5, S6, S7 (per-day cover), S8 and the overnight batching. Cold review R2 (NOT SAFE until N1: a daytime message
told again at the next 08:00) -- N1 built with a two-day walk check, N2 (ten days), N3 (the dry run prints the Amir days read), N4 (the
voucher count by the reader's own rule). Walk 33 ok, control 21 red, 14 of 14 mutants caught.

**Install (one server line, after the publish):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s706kit && cp -rp /root/deploy/repo/deploy_kits/S706_HAND_CHANGE_WATCH /tmp/s706kit && bash /tmp/s706kit/install_S706_HAND_CHANGE_WATCH.sh

Gates before placing: SUMS, KIT_ID, the window, the live pins, the rebuild from live bytes to the TO pins, the walk (33 ok) on the rebuilt files, the
control (21 red) on the live files, the finder READ-ONLY on the live spine (must find CARTILOX SACHET 3 → 0; at most 40 rows; judged to within 3 days). Restarts
clinic-finance. Undo is printed. OFF: the setting `hand.on = off`, or `/root/finance/_off/ALL_OFF`.
