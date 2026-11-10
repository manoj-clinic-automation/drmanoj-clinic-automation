#!/usr/bin/env python3
"""walk_s772_filmdate.py -- xray_filmdate.py on a made-up root: a made-up finance.db (xray_filing only), records_drive.py's own
stub mode and films drawn here (white text on black). Proves: each parked picture is read once and its printed date stored
(only dates in the 120 days before it was first seen); a film with no date gets '[]' and is not read again; a picture that is
not parked ('done', 'planned') is never read; the switch stops the run; nothing else in the database is touched.
CONTROL: with no OCR tool the run does nothing and says so (red on purpose for the date checks).
usage: walk_s772_filmdate.py <xray_filmdate.py> <records_drive.py>  [env WALK_PY_RAPID=<python with rapidocr>]"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

SCRIPT, HELPER = sys.argv[1], sys.argv[2]
root = tempfile.mkdtemp(prefix="walk771fd_")
stub = os.path.join(root, "drive")
os.makedirs(stub)
dbp = os.path.join(root, "finance.db")
ok = [0]


def check(name, cond, extra=""):
    if not cond:
        print("WALK RED: %s %s" % (name, extra))
        sys.exit(1)
    ok[0] += 1


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p) and not os.environ.get("WALK_NO_DEJAVU"):
            return ImageFont.truetype(p, sz)
    try:
        return ImageFont.load_default(size=sz)          # Pillow 10.1+: a scalable built-in font (the server may have no fonts)
    except TypeError:
        return ImageFont.load_default()


def film(fid, top):
    im = Image.new("L", (1800, 2200), 18)
    d = ImageDraw.Draw(im)
    d.ellipse((500, 600, 1300, 1700), fill=150)
    d.text((40, 30), top, fill=235, font=font(44))
    im.convert("RGB").save(os.path.join(stub, fid), "JPEG", quality=90)


c = sqlite3.connect(dbp)
c.execute("CREATE TABLE xray_filing(src_id TEXT PRIMARY KEY, orig_name TEXT, file_time TEXT, action TEXT, clinic_id TEXT, day TEXT, "
          "new_name TEXT, dest_id TEXT, file_id INTEGER, state TEXT, verdict TEXT, planned_at TEXT, done_at TEXT)")
c.execute("CREATE TABLE other(x)")
c.execute("INSERT INTO other VALUES (1)")
P = [("walkFD0000001", "check", "2026-11-09 19:10:00", "TESTNAME A   12/10/2026  10:42"),
     ("walkFD0000002", "check", "2026-11-09 19:11:00", "TESTNAME B   Date: 05-Nov-2026"),
     ("walkFD0000003", "check", "2026-11-09 19:12:00", "TESTNAME C   no date here"),
     ("walkFD0000004", "check", "2026-11-09 19:13:00", "TESTNAME D   01/02/2025"),       # outside the 120 days
     ("walkFD0000005", "done", "2026-11-09 19:14:00", "TESTNAME E   12/10/2026"),        # filed: never read
     ("walkFD0000006", "planned", "2026-11-09 19:15:00", "TESTNAME F   12/10/2026")]     # planned: never read
for sid, stt, ft, top in P:
    film(sid, top)
    c.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, state, day, planned_at) VALUES (?,?,?,?,?,?,?)",
              (sid, sid + ".jpg", ft, "check", stt, ft[:10], ft))
c.commit()
c.close()


def run(py, control=False, off=None):
    env = dict(os.environ, FINANCE_DB=dbp, S772_HELPER=HELPER, S772_HELPER_PY=sys.executable, RECORDS_HELPER_STUB=stub,
               S772_OFF=off or os.path.join(root, "no_switch"))
    if control:
        env["PATH"] = "/nonexistent"
    p = subprocess.run([py, "-B", SCRIPT], env=env, capture_output=True, text=True, timeout=900)
    return p.returncode, p.stdout + p.stderr


def rows():
    c = sqlite3.connect(dbp)
    try:
        return {r[0]: (json.loads(r[1]), r[2]) for r in c.execute("SELECT src_id, dates, how FROM xray_filmdate")}
    except sqlite3.Error:
        return {}
    finally:
        c.close()


def body(py, label, no_tess=False):
    c = sqlite3.connect(dbp)
    c.execute("DROP TABLE IF EXISTS xray_filmdate")
    c.commit()
    c.close()
    sw = os.path.join(root, "OFF")
    open(sw, "w").close()
    rc, out = run(py, control=no_tess, off=sw) if no_tess else run(py, off=sw)
    check(label + ": the switch stops the run", "switched off" in out and not rows(), out)
    os.remove(sw)
    rc, out = run(py, control=no_tess)
    r = rows()
    check(label + ": ran", rc == 0, out)
    check(label + ": 12/10/2026 read", r.get("walkFD0000001", ([], ""))[0][:1] == ["2026-10-12"], str(r.get("walkFD0000001")))
    check(label + ": 05-Nov-2026 read", r.get("walkFD0000002", ([], ""))[0] == ["2026-11-05"], str(r.get("walkFD0000002")))
    check(label + ": no date -> []", r.get("walkFD0000003", (None, ""))[0] == [])
    check(label + ": a date outside the 120 days -> []", r.get("walkFD0000004", (None, ""))[0] == [])
    check(label + ": filed / planned pictures never read", "walkFD0000005" not in r and "walkFD0000006" not in r)
    rc, out = run(py, control=no_tess)
    check(label + ": a second run reads nothing again", "read " not in out, out)
    c = sqlite3.connect(dbp)
    check(label + ": nothing else touched", c.execute("SELECT COUNT(*) FROM other").fetchone()[0] == 1
          and c.execute("SELECT COUNT(*) FROM xray_filing WHERE state='check'").fetchone()[0] == 4)
    c.close()


body(sys.executable, "this python's OCR")
if os.environ.get("WALK_PY_RAPID"):
    body(os.environ["WALK_PY_RAPID"], "rapidocr", no_tess=True)
c = sqlite3.connect(dbp)
c.execute("DROP TABLE IF EXISTS xray_filmdate")
c.commit()
c.close()
rc, out = subprocess.run([os.environ.get("WALK_PY_PLAIN", "/usr/bin/python3"), "-B", SCRIPT], env=dict(os.environ, FINANCE_DB=dbp, S772_HELPER=HELPER, RECORDS_HELPER_STUB=stub,
                         PATH="/nonexistent", S772_OFF=os.path.join(root, "x")), capture_output=True, text=True).returncode, ""
check("CONTROL: no OCR tool -> nothing read", not rows())
shutil.rmtree(root, ignore_errors=True)
print("WALK OK %d/%d -- xray_filmdate.py" % (ok[0], ok[0]))
