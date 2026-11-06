#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proof_s722.py -- S722: OLD against NEW on real data, READ ONLY.  What owner_notice would say at every hour of the last DAYS days
(08:00-23:00), by the live file and by the rebuilt one, on the same database opened read-only, with no medical-PC note present: the
two must be the same, line for line (S722 adds only the medical PC's two messages, which need the door's note).

    python3 -B proof_s722.py <old finance dir> <new finance dir> <database> [days]

Writes nothing; sends nothing (collect never sends).  Prints one last line: "PROOF S722: CLEAN -- N moments, old = new" or a difference.
"""
import datetime as dt
import os
import subprocess
import sys


def run(d, db, when, py):
    env = dict(os.environ, S722_SEEN_FILE="/nonexistent/s722_proof_no_note.json", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([py, "-B", os.path.join(d, "owner_notice.py"), "collect", "--db", db, "--now", when],
                       cwd=d, env=env, capture_output=True, text=True, timeout=120)
    return r.stdout.strip().splitlines()


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    old, new, db = argv[:3]
    days = int(argv[3]) if len(argv) > 3 else 3
    py = sys.executable
    today = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date()
    n = said = 0
    for back in range(days, -1, -1):
        day = today - dt.timedelta(days=back)
        for h in range(8, 24):
            when = "%sT%02d:05" % (day.isoformat(), h)
            a, b = run(old, db, when, py), run(new, db, when, py)
            n += 1
            said += max(0, len(a) - 1)
            if a != b:
                print("at %s the old says:\n  %s\nthe new says:\n  %s" % (when, "\n  ".join(a), "\n  ".join(b)))
                print("PROOF S722: DIFFERS at %s" % when)
                return 1
            if not a or not a[-1].startswith("collect:"):
                print("PROOF S722: collect did not run at %s (%s)" % (when, (a or ["no output"])[-1][:160]))
                return 1
    print("PROOF S722: CLEAN -- %d moments, old = new (%d message line(s) in all)" % (n, said))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
