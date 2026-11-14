#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s828.py -- S828_BATCH_NOTICE_TRUE (14-Nov-2026, Sanjeevni session 457): makes /root/finance/owner_notice.py from its LIVE bytes by
exact, counted replacements; refuses any other starting file.
    python3 -B make_s828.py <live owner_notice.py> <out file>
THE FAULT (the owner, 09:34 IST 14-Nov): his phone said 'Batch fixes: 0 done today, 18 left' while Amir's card said 8 fixed, 5 left. The
message went at ~09:01, when Amir's purchase reports came; the Batch Stock had been read at 07:0x but its Issues could be judged only once
the day's sales were in -- that came at the 09:05 run. And it counted every voucher line ever open, not what Amir's card shows.
THE CHANGE (in _part_amir only): (1) while a batch row waits for the day's sales ('issue pending'), the 'Amir's work' message waits too --
at most owner_notice.batch_hold_min minutes (180, a setting) after his reports; past that it goes and says the check is still waiting;
(2) the counts are Amir's card's own: fixed in the last 24 hours, and the rows judged in the last 24 hours still to do
(expiry_watch.fixes_rows) -- in words: 'Batch fixes: 8 fixed, 5 still to do (as on his card)'. Nothing else changes."""
import hashlib
import sys

FROM = "471859b3848eab1b2057f3b2af378242"

R = [
('''    ("owner_notice.amir_missing_hhmm", "23:40", "S702: on an Amir day, what is still missing of his three exports is said at this time"),''',
 '''    ("owner_notice.amir_missing_hhmm", "23:40", "S702: on an Amir day, what is still missing of his three exports is said at this time"),
    ("owner_notice.batch_hold_min", "180", "S828: Amir's message waits up to this many minutes after his reports for the batch check "
                                           "against the day's sales"),'''),
('''        body = "Item-wise ✓ · Bill-wise ✓ · Batch Stock ✓ — in by %s" % last[11:16]
        if _table(con, "stock_batch_fix"):
            try:
                done = con.execute("SELECT COUNT(*) FROM stock_batch_fix WHERE status='done' AND substr(COALESCE(done_at,''),1,10)=?",
                                   (day,)).fetchone()[0]
                left = con.execute("SELECT COUNT(*) FROM stock_batch_fix WHERE status IN ('open','receive_only','issue_only')").fetchone()[0]
                if done or left:
                    body += "\\nBatch fixes: %d done today, %d left" % (done, left)
            except sqlite3.Error:
                pass''',
 '''        body = "Item-wise ✓ · Bill-wise ✓ · Batch Stock ✓ — in by %s" % last[11:16]
        if _table(con, "stock_batch_fix"):
            try:                                              # S828: Amir's card's own counts (expiry_watch.fixes_rows), not a raw tally
                since24 = (now.replace(tzinfo=None) - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
                done = con.execute("SELECT COUNT(*) FROM stock_batch_fix WHERE status='done' AND substr(COALESCE(done_at,''),1,19)>=?",
                                   (since24,)).fetchone()[0]
                pend = con.execute("SELECT COUNT(*) FROM stock_batch_fix WHERE status IN ('open','receive_only','issue_only') "
                                   "AND substr(COALESCE(judged_at,''),1,19)>=?", (since24,)).fetchone()[0]
                waiting = con.execute("SELECT COUNT(*) FROM stock_batch_fix WHERE status IN ('open','receive_only','issue_only') "
                                      "AND COALESCE(note,'') LIKE 'issue pending%'").fetchone()[0]
                if waiting:                                   # the Issues wait for the day's sales: the message waits with them
                    try:
                        hold = int(str(setting(con, "owner_notice.batch_hold_min")).strip() or 180)
                    except ValueError:
                        hold = 180
                    if now.replace(tzinfo=None) < dt.datetime.strptime(last[:16], "%Y-%m-%d %H:%M") + dt.timedelta(minutes=hold):
                        return []
                    body += "\\nBatch fixes: still being checked — the day's sales are not in yet (Amir's card will show it)"
                elif done or pend:
                    body += "\\nBatch fixes: %d fixed, %d still to do (as on Amir's card)" % (done, pend)
            except (sqlite3.Error, ValueError):
                pass'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    b = open(src, "rb").read()
    h = hashlib.md5(b).hexdigest()
    if h != FROM:
        print("make_s828: the live file is %s, not %s -- STOP" % (h[:8], FROM[:8]))
        return 2
    t = b.decode("utf-8")
    for i, (old, new) in enumerate(R, 1):
        n = t.count(old)
        if n != 1:
            print("make_s828: replacement %d found %d times -- STOP" % (i, n))
            return 2
        t = t.replace(old, new, 1)
    nb = t.encode("utf-8")
    open(out, "wb").write(nb)
    print("make_s828: %s -> %s" % (FROM[:8], hashlib.md5(nb).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
