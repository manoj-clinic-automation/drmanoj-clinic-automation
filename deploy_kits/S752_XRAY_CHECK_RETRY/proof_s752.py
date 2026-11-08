#!/usr/bin/env python3
"""proof_s752.py -- what S752 would do with the pictures parked in the X-ray check folder TODAY, read from a database
(the live one or a copy). READ-ONLY on that database: it works on a throw-away copy in /tmp and deletes it.
The check folder is taken from xray_filing (state 'check' -- the pictures the server knows are parked there).
Prints counts and the last four digits of IDs only; never a name.
usage: proof_s752.py <dir holding the NEW records.py> <finance.db>"""
import datetime as dt
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

app_dir, src = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
tmpd = tempfile.mkdtemp(prefix="s752proof_")
os.chmod(tmpd, 0o700)
dbp = os.path.join(tmpd, "copy.db")
try:
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dbp)
    s.backup(d)
    s.close()
    d.close()
    os.environ["RECORDS_DRIVE_STUB"] = tmpd                     # no Drive call from the proof
    sys.path.insert(0, app_dir)
    spec = importlib.util.spec_from_file_location("records_s752proof", os.path.join(app_dir, "records.py"))
    rec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rec)
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    rec.xray_ensure(con)
    m = lambda c: ".." + str(c)[-4:]                            # noqa: E731

    def pending(month):
        out = []
        for r in con.execute("SELECT DISTINCT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.series='xp' "
                             "AND s.state='ok' AND i.kind='xray' AND s.clinic_id<>'' AND s.day LIKE ?", (month + "%",)):
            if con.execute("SELECT 1 FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? AND day=?", (r[1], r[0])).fetchone():
                continue
            if con.execute("SELECT 1 FROM pend_mark WHERE kind='xray' AND key=? AND act='not_done'", ("xm:%s:%s" % (r[0], r[1]),)).fetchone():
                continue
            planned = con.execute("SELECT 1 FROM xray_filing WHERE clinic_id=? AND day=? AND state='planned'", (r[1], r[0])).fetchone()
            out.append((r[0], r[1], bool(planned)))
        return out

    months = sorted({r[0][:7] for r in con.execute("SELECT day FROM xray_filing WHERE state='check' AND day<>''")})
    before = {mo: len(pending(mo)) for mo in months}
    answered = {r[0] for r in con.execute("SELECT key FROM record_check WHERE key LIKE 'xf:%'")}
    files = []
    for r in con.execute("SELECT * FROM xray_filing WHERE state='check'"):
        if "xf:" + r["src_id"] in answered:
            continue
        t = (r["file_time"] or "")[:19]
        try:
            u = dt.datetime.fromisoformat(t) - dt.timedelta(hours=5, minutes=30)
        except ValueError:
            continue
        files.append({"id": r["src_id"], "name": r["orig_name"], "mimeType": "image/jpeg",
                      "modifiedTime": u.strftime("%Y-%m-%dT%H:%M:%S.000Z")})
    print("parked in the check folder (unanswered): %d pictures" % len(files))
    items = rec._s752_retry(con, files, rec._stamp())
    by_id = by_name = 0
    for i in items:
        v = con.execute("SELECT verdict FROM xray_filing WHERE src_id=?", (i["id"],)).fetchone()[0]
        if "its name is that of" in v:
            by_name += 1
        else:
            by_id += 1
    print("S752 would FILE: %d pictures -- %d because their ID is now on the day's X-ray list, %d by name (word for word, the day over, no other patient sharing a word)"
          % (len(items), by_id, by_name))
    sug = box = 0
    cache = {}
    for r in con.execute("SELECT * FROM xray_filing WHERE state='check'").fetchall():
        if "xf:" + r["src_id"] in answered:
            continue
        c, w, pre = rec._s752_suggest(con, dict(r), cache)
        if c:
            sug += 1
            box += 1 if pre else 0
    left = len(files) - len(items)
    print("left in the check list: %d pictures -- %d with a 'Shayad ID ...' suggestion (%d of them already in the box: one tap), "
          "%d for a person to look at" % (left, sug, box, left - sug))
    for mo in months:
        after = pending(mo)
        still = [x for x in after if not x[2]]
        print("%s: 'photo baaki' %d before -> %d after (%d now 'photo mil gayi -- file ho rahi hai')"
              % (mo, before[mo], len(still), len(after) - len(still)))
    oc = [x for x in pending("2026-10") if not x[2]]
    print("October still baaki: %s" % ", ".join("%s %s" % (x[0][8:], m(x[1])) for x in oc))
    print("PROOF DONE")
finally:
    shutil.rmtree(tmpd, ignore_errors=True)
