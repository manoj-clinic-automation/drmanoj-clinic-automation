#!/usr/bin/env python3
"""walk_s435.py -- S435: THE asset app file of this kit, over a SCRATCH COPY of assets.db (or a fresh one), crafted logins (current_user
patched, walk only), one crafted bill image. Usage: walk_s435.py <kit dir> <scratch dir> <scratch assets.db>. Last line WALK OK / WALK RED."""
import io, os, shutil, sqlite3, subprocess, sys
KIT, W, ADB = sys.argv[1:4]
assert "walk" in W or W.startswith("/tmp"), "refusing a non-scratch folder"
for f in ("asset_register.py", "scanner_widget.js"):
    src = os.path.join(KIT, f) if os.path.exists(os.path.join(KIT, f)) else os.path.join(os.environ.get("ASSETS_LIVE", "/root/assetapp"), f)
    shutil.copy(src, W)
up = os.path.join(W, "uploads"); os.makedirs(up, exist_ok=True)
os.environ.update(ASSETS_DB=ADB, ASSETS_UPLOADS=up); os.environ.pop("SARVAM_API_KEY", None)
sys.path.insert(0, W); os.chdir(W)
import asset_register as ar
from werkzeug.datastructures import FileStorage
bad = []
def check(n, c, info=""):
    print(("  PASS " if c else "  FAIL ") + n + ("" if c else "  -- %s" % (info,)))
    if not c: bad.append(n)
USERS = {"manoj": {"id": 1, "username": "manoj", "display_name": "Dr Manoj", "role": "owner", "active": 1, "password_hash": ""},
         "sukhveer": {"id": None, "username": "sukhveer", "display_name": "Sukhveer", "role": "reception", "active": 1}}
CUR = {"u": "sukhveer"}
ar.current_user = lambda: USERS[CUR["u"]]
with ar.app.app_context():
    try:
        ar.init_db(seed=False)
    except TypeError:
        ar.init_db()
c = ar.app.test_client()
CUR["u"] = "sukhveer"
r = c.get("/intake")
html = r.get_data(as_text=True)
months = ar._month_choices()
check("the intake page asks the bill's month (%s first)" % months[0], r.status_code == 200 and 'id=intake_month' in html and months[1] in html, r.status_code)
img = os.path.join(W, "w435.jpg")
subprocess.run(["convert", "-size", "600x800", "xc:white", "-fill", "black", "-pointsize", "30", "-draw", "text 40,400 'W435 walk bill'", img], check=False)
if not os.path.exists(img):
    open(img, "wb").write(b"\xff\xd8\xff\xe0" + b"0" * 2000)
with open(img, "rb") as fh:
    data = {"lane": "lab_purchase", "bill_month": months[1], "note": "W435 walk",
            "bill_file": (io.BytesIO(fh.read()), "w435.jpg")}
r = c.post("/intake/submit", data=data, content_type="multipart/form-data")
db = sqlite3.connect(ADB); db.row_factory = sqlite3.Row
b = db.execute("SELECT * FROM bills WHERE notes='W435 walk' ORDER BY id DESC LIMIT 1").fetchone()
check("a scanned bill carries the month the person chose (%s)" % months[1], b is not None and b["bill_month"] == months[1], b and dict(b))
check("... and is marked late for that month (scanned this month)", b is not None and b["late_for"] == months[1], b and b["late_for"])
if b:
    db.execute("UPDATE bills SET bill_date='2016-09-12' WHERE id=?", (b["id"],)); db.commit()
    with ar.app.app_context():
        d2 = ar.get_db(); ar._set_late(d2, b["id"]); d2.commit()
    b2 = db.execute("SELECT bill_month, late_for FROM bills WHERE id=?", (b["id"],)).fetchone()
    check("an OCR misread (2016) does not move it: the person's month wins", b2["bill_month"] == months[1] and b2["late_for"] == months[1], dict(b2))
    CUR["u"] = "manoj"
    r = c.get("/bills/%d" % b["id"])
    check("the bill page shows the month and the correction", r.status_code == 200 and "bill_month_set" not in r.get_data(as_text=True) and "/month" in r.get_data(as_text=True), r.status_code)
    r = c.post("/bills/%d/month" % b["id"], data={"bill_month": months[0]})
    b3 = db.execute("SELECT bill_month, late_for FROM bills WHERE id=?", (b["id"],)).fetchone()
    check("the checker moves it to %s in one tap (no longer late)" % months[0], b3["bill_month"] == months[0] and b3["late_for"] is None, dict(b3))
    r = c.post("/bills/%d/month" % b["id"], data={"bill_month": "2031-01"})
    b4 = db.execute("SELECT bill_month FROM bills WHERE id=?", (b["id"],)).fetchone()
    check("a month outside the last year is refused", b4["bill_month"] == months[0], dict(b4))
    CUR["u"] = "sukhveer"
    r = c.post("/bills/%d/month" % b["id"], data={"bill_month": months[1]})
    check("reception cannot change a month", r.status_code == 403, r.status_code)
    db.execute("DELETE FROM bill_audit WHERE bill_id=?", (b["id"],)); db.execute("DELETE FROM bills WHERE id=?", (b["id"],)); db.commit()
print("WALK OK -- the month is asked at the scan, kept against a wrong OCR date, and correctable by the checker" if not bad
      else "WALK RED -- %d check(s) failed: %s" % (len(bad), "; ".join(bad)))
sys.exit(1 if bad else 0)
