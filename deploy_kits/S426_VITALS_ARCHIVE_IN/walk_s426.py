#!/usr/bin/env python3
"""walk_s426.py -- the walk for kit S426_VITALS_ARCHIVE_IN. No network. A throwaway VITALS_DIR; the engine is
stood in (only its presence is needed at import). usage: walk_s426.py <dir holding the new vitals_portal.py>
Prints WALK OK n/n."""
import os
import shutil
import sys
import tempfile
import types

APP = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TMP = tempfile.mkdtemp(prefix="s426walk_")
os.environ["PORTAL_VITALS_DIR"] = os.path.join(TMP, "vitals")
cw = types.ModuleType("clinic_writer")
cw.VITALS_COLS, cw.PLAN_COLS = ["a"], ["b"]
sys.modules["clinic_writer"] = cw
sys.path.insert(0, APP)
import vitals_portal as vp                                     # noqa: E402
from flask import Flask                                        # noqa: E402
import io                                                      # noqa: E402

N = [0, 0]


def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1
        print("  ok  %s" % name)
    else:
        print("  RED %s %s" % (name, extra))


ALLOW = {"on": True}


def guard(f):
    def w(*a, **k):
        if not ALLOW["on"]:
            return "login", 302
        return f(*a, **k)
    w.__name__ = f.__name__
    return w


app = Flask("walk")
vp.register(app, guard, lambda: "manoj")
c = app.test_client()
PDF1 = b"%PDF-1.4\n walk one \n%%EOF"
PDF2 = b"%PDF-1.4\n walk two \n%%EOF"
NM1, NM2 = "2026-07-06_P-2026-1_patient.pdf", "2026-07-06_P-2026-1_physio.pdf"


def post(folder, files):
    data = {"folder": folder, "pdf": [(io.BytesIO(b), n) for n, b in files]}
    return c.post("/portal/vitals/archive", data=data, content_type="multipart/form-data")


print("[1] the gate and the page")
ALLOW["on"] = False
check("without login: GET and POST both refused by the portal's own gate",
      c.get("/portal/vitals/archive").status_code == 302 and post("2026/ABCD1234", [(NM1, PDF1)]).status_code == 302)
check("... and nothing written", not os.path.exists(vp.ARCHIVE_ROOT))
ALLOW["on"] = True
g = c.get("/portal/vitals/archive")
check("with login: the page, one file input, posting to its own address",
      g.status_code == 200 and b'type="file"' in g.data and b'"/portal/vitals/archive"' in g.data)

print("[2] placing")
r = post("2026/ABCD1234", [(NM1, PDF1), (NM2, PDF2)]).get_json()
st = [x["status"] for x in r["results"]]
check("two sheets placed into <year>/<UID>, archive count 2", st == ["placed", "placed"] and r["pdfs"] == 2, str(r))
t1 = os.path.join(vp.ARCHIVE_ROOT, "2026", "ABCD1234", NM1)
check("bytes exact, file 0600, folder 0700", open(t1, "rb").read() == PDF1 and (os.stat(t1).st_mode & 0o777) == 0o600
      and (os.stat(os.path.dirname(t1)).st_mode & 0o777) == 0o700)
import hashlib                                                 # noqa: E402
check("md5 returned is the file's", r["results"][0]["md5"] == hashlib.md5(PDF1).hexdigest())
r = post("pending/NA_NA", [(NM1, PDF1)]).get_json()
check("pending/NA_NA accepted", r["results"][0]["status"] == "placed" and r["pdfs"] == 3, str(r))

print("[3] never overwrites")
r = post("2026/ABCD1234", [(NM1, PDF1)]).get_json()
check("the same file again -> 'same', count unchanged", r["results"][0]["status"] == "same" and r["pdfs"] == 3, str(r))
r = post("2026/ABCD1234", [(NM1, PDF2)]).get_json()
check("different bytes under an existing name -> 'kept (differs)', the original untouched",
      r["results"][0]["status"] == "kept (differs)" and open(t1, "rb").read() == PDF1, str(r))

print("[4] refusals")
cases = [("../../etc", NM1, PDF1, "folder"), ("2026/abc", NM1, PDF1, "folder"), ("2026/ABCD1234/x", NM1, PDF1, "folder"),
         ("2026/ABCD1234", "evil.pdf", PDF1, "name"), ("2026/ABCD1234", "../" + NM1, PDF1, None),
         ("2026/ABCD1234", "2026-07-06_P-2026-9_patient.pdf", b"<html>", "not a PDF"),
         ("2026/ABCD1234", "2026-07-06_P-2026-9_patient.pdf", b"%PDF-" + b"x" * (5 * 1024 * 1024), "not a PDF")]
for folder, name, data, why in cases:
    res = post(folder, [(name, data)]).get_json()["results"][0]
    if why is None:          # a path in the name is reduced to its basename: lands as the plain name, which exists
        check("a '../' in the file name is reduced to the base name (never escapes)", res["status"] in ("same", "kept (differs)"), str(res))
    else:
        check("refused: %s (%s)" % (why, folder if why == "folder" else name[:24]), res["status"].startswith("refused") and why.split()[0] in res["status"], str(res))
walked = sorted(os.path.relpath(os.path.join(a, f), vp.ARCHIVE_ROOT) for a, _, fs in os.walk(vp.ARCHIVE_ROOT) for f in fs)
check("after all of it, exactly the three placed files exist, no temp left",
      walked == sorted([os.path.join("2026", "ABCD1234", NM1), os.path.join("2026", "ABCD1234", NM2),
                        os.path.join("pending", "NA_NA", NM1)]), str(walked))
h = c.get("/portal/vitals/health").get_json()
check("the health route counts them", h["pdfs"] == 3, str(h))
shutil.rmtree(TMP, ignore_errors=True)
print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
