# S805_WA_STOP_LIST_REMOVE — the owner can take a number off the WhatsApp stop list from his page, and put it back (D939, the WhatsApp items, c)

**Before:** a number that replied STOP stayed on the stop list for ever; the only way off was a line typed on the server.

**Now**, on `https://followup.dr-manoj.in/portal/messages` (the doctor's login only):
- each row under **Numbers that said STOP** has a button **Take off the stop list** — two taps, at least 0.7 seconds apart
  and within six seconds, so a slip or a double-tap does nothing;
- a new section **Taken off the stop list by you** lists each number that is off the list now — when, by which login, what
  it had said — with a button **Put back on the stop list** (one tap: the safe direction).

**Rules in the code (`/root/portal/wa_ladder.py` ca0334b4 → cb197293, version S805 1.3):**
- a removal is **recorded, never erased** — table `optout_removed` in the kit's own store `/root/portal/wa_ladder.db`;
- the STOP listener does **not** put the number back for a STOP it had already read (not on `--rescan` either);
- a **new** STOP reply from that number — also one that had arrived and was not read yet — puts it back at the listener's
  next pass (within 5 minutes);
- the taking-off holds the store's write lock from its first read, so the listener cannot slip a STOP in between;
- a number that came from the older, hand-kept opt-out file (`/root/wa/wa_opt_outs.csv`) is taken off the same way; the
  file is untouched. **If that file is changed again later, every number still in it is back on the list** (the safe
  direction; he can take it off again);
- if the store cannot be read or is busy, nothing is taken off and every row stays held (it still fails closed);
- the two new doors `POST /portal/messages/api/unstop` and `.../restop` answer only the doctor's login and only the
  page's own script (header `X-Messages: 1`); without a login they are closed like the page; only a number that was taken
  off here can be put back through the page.
- **Still SHOW ONLY: the file holds no send code** (the walk checks it).

**Walk** 40/40 on made-up stores; the CONTROL red on the live file (7 of 12). S801's own walk on the new file: 39 of 40 —
the one red is its check that the version reads S801. The page run in Chromium at 400 and 1100 px with made-up rows.

**Cold review (a second reader, S439): NOT SAFE on the first build — one must-fix, built:** the taking-off read the
listener's place before it held the write lock (a STOP read in that instant would have been lost). Its should-fixes built:
the older file changed again; the taken-off list shows only numbers that are off now; the minimum gap between the two taps;
the way back (Put back); the listener checked before the install; the walk's missing cases (an unread STOP, the lock, a busy
store). Left as they are: a bad request and a store error both answer 409; if the Inbox store were ever rebuilt with its
message numbers restarted, a taken-off number would need Put back by hand.

**The installer (S801's pattern):** the kit's file is remade on the box from the live bytes and must equal the kit's; walk
and control; the listener must be well before; the page's door read before placing and the same after; both new doors must
be closed without a login; journal; the listener must still say ok; today's counts must still read. Red after placing →
the old file back and the portal restarted.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s805kit && cp -rp /root/deploy/repo/deploy_kits/S805_WA_STOP_LIST_REMOVE /tmp/s805kit && bash /tmp/s805kit/install_S805_WA_STOP_LIST_REMOVE.sh
```
Undo: `bash /tmp/s805kit/install_S805_WA_STOP_LIST_REMOVE.sh --undo`.
