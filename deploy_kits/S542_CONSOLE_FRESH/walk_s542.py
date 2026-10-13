#!/usr/bin/env python3
"""walk_s542.py -- kit S542 (session 313, 13-Oct-2026). READ-ONLY against the live database (it works on a copy of a copy).
    python3 -B walk_s542.py <folder holding owner_console.py + .html> --fin <folder of the app's modules> --db <a COPY of finance.db>
                            [--expect-red]
It makes the morning the owner saw: yesterday's Docterz day read, the counter sheet NOT yet filled (on its own copy only), then
runs the console's own builder from <folder> exactly as the service does (a separate process, --build) and holds the reading:
the clinic's day must read Docterz's day total -- the Docterz Revenue page's number -- never Rs 0. It also holds the page: a
fresh reading is asked for on opening and on coming back. --expect-red runs the same on the OLD files: they must fail.
Prints 'WALK OK ...'; exit 1 on any failure."""
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FAILS, RUN = [], [0]


def ok(c, what):
    RUN[0] += 1
    if not c:
        FAILS.append(what)


def inr(p):
    p = int(p)
    r, ps = divmod(abs(p), 100)
    s = str(r)
    if len(s) > 3:
        head, tail, parts = s[:-3], s[-3:], []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return "₹" + s + ((".%02d" % ps) if ps else "")


def main(a):
    folder = a[0]
    fin = a[a.index("--fin") + 1]
    db = a[a.index("--db") + 1]
    red = "--expect-red" in a
    html = open(os.path.join(folder, "owner_console.html"), encoding="utf-8").read()
    ok("load(true); loadFills(); loadSwitch();   // S542" in html, "the page does not ask for a fresh reading when opened")
    ok("if(!document.hidden){tries=0; load(true);" in html, "the page does not ask for a fresh reading when he comes back")
    tmp = tempfile.mkdtemp(prefix="walk_s542_")
    try:
        copy = os.path.join(tmp, "w.db")
        shutil.copyfile(db, copy)
        con = sqlite3.connect(copy)
        yday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
        row = con.execute("SELECT total_amount_p FROM clinic_day_revenue WHERE business_date=?", (yday,)).fetchone()
        nlines = con.execute("SELECT COUNT(*) FROM clinic_day_line WHERE business_date=? AND section IN ('consult','xray','proc')",
                             (yday,)).fetchone()[0]
        if row is None or not nlines:                                    # yesterday not read yet on this box: a made-up day
            con.execute("DELETE FROM clinic_day_revenue WHERE business_date=?", (yday,))
            info = list(con.execute("PRAGMA table_info(clinic_day_revenue)"))
            cols = [r[1] for r in info]
            vals = dict((r[1], ("walk" if "TEXT" in (r[2] or "").upper() else 0) if r[3] else None) for r in info)
            vals.update(business_date=yday, total_amount_p=432100, total_count=1, cons_count=1, cons_amount_p=432100,
                        xray_count=0, xray_amount_p=0, proc_count=0, proc_amount_p=0, tender_json='{"Cash": 432100}')
            con.execute("INSERT INTO clinic_day_revenue (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))),
                        [vals[c] for c in cols])
            con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode, shift) "
                        "VALUES (?, 'consult', 1, 'WALK', 'W0', 432100, 'Cash', 'Morning')", (yday,))
            want, how = 432100, "made-up"
        else:
            want, how = int(row[0] or 0), "real"
        con.execute("DELETE FROM clinic_register_day WHERE business_date=?", (yday,))   # the counter sheet not yet filled
        con.commit()
        con.close()
        out = os.path.join(tmp, "reading.dat")
        env = dict(os.environ, PYTHONPATH=fin, PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run([sys.executable, "-B", os.path.join(folder, "owner_console.py"), "--build", "--db", copy, "--out", out,
                            "--lock", os.path.join(tmp, "lock")], env=env, cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=170)
        ok(p.returncode == 0 and os.path.exists(out), "the builder did not write a reading: %s" % p.stdout.decode("utf-8", "replace")[-300:])
        if os.path.exists(out):
            s = json.load(open(out, encoding="utf-8"))
            ok(s.get("clinic_day") == yday, "the reading is for %s, not yesterday %s" % (s.get("clinic_day"), yday))
            ok("money" not in (s.get("failed") or []), "the Money section was not read: %s" % (s.get("sections", {}).get("money", {}).get("why")))
            t = s.get("tile") or {}
            ok(t.get("clinic") == inr(want), "the tile reads %s for the clinic's day, Docterz says %s" % (t.get("clinic"), inr(want)))
            first = ((s.get("sections", {}).get("money") or {}).get("lines") or [{}])[0]
            ok(first.get("b") == "Clinic " + inr(want), "the Money line reads %r, Docterz says %s" % (first.get("b"), inr(want)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if red:
        if FAILS:
            print("WALK OK (negative control: the old files fail %d of %d checks, e.g. %s)" % (len(FAILS), RUN[0], FAILS[0][:90]))
            return 0
        print("WALK RED: the negative control passed on the old files -- the walk proves nothing")
        return 1
    if FAILS:
        print("WALK RED: %d of %d checks failed" % (len(FAILS), RUN[0]))
        for f in FAILS:
            print("  - " + f)
        return 1
    print("WALK OK: %d checks green (yesterday %s, %s Docterz day %s, the counter sheet taken out on the walk's own copy)"
          % (RUN[0], yday, how, inr(want)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
