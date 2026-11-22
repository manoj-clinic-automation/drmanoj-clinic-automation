"""walk_s929.py FILE -- S929's walk on a MADE-UP staff register (never the live one). FILE = the staff_register.py to test.
Prints PASS/FAIL lines and 'WALK n/m' last."""
import datetime as dt, importlib.util, os, shutil, sqlite3, subprocess, sys, tempfile
SRC = os.path.abspath(sys.argv[1])
HERE = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix="w929_")
shutil.copy(SRC, os.path.join(tmp, "staff_register.py"))
os.environ.setdefault("SR_DB_PATH", os.path.join(tmp, "x.db"))
spec = importlib.util.spec_from_file_location("sr_w929", os.path.join(tmp, "staff_register.py"))
SR = importlib.util.module_from_spec(spec); spec.loader.exec_module(SR)
res = []
def chk(name, ok, why=""):
    res.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + ("" if ok else " -- " + str(why)[:200]))
TODAY = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date().isoformat()
YEST = (dt.date.fromisoformat(TODAY) - dt.timedelta(days=1)).isoformat()
SR.DB_PATH = os.path.join(tmp, "t.db")
SR.init_db()
con = SR.get_db()
names = ["Alisha", "Amir Sohail", "Awdhesh", "Darpan", "Ranjeet", "Sandip", "Shavez", "Shivani", "Sukhveer", "Surendra", "Vikki"]
for i, n in enumerate(names, 1):
    con.execute("INSERT INTO staff(staff_id,name,join_date,base_salary,allowed_offs,minutes_exempt,cover_eligible,outstation_eligible,active) "
                "VALUES(?,?,?,?,?,?,?,?,1)", (i, n, "2026-01-01", 10000, 2, 0, 0, 0))
    for it in ("uniform", "icard"):
        con.execute("INSERT INTO issuance(staff_id,item_type,issued_date,status) VALUES(?,?,'2000-01-01','approved')", (i, it))
con.execute("INSERT INTO staff(staff_id,name,join_date,base_salary,allowed_offs,minutes_exempt,cover_eligible,outstation_eligible,active) "
            "VALUES(99,'Pravesh','2025-01-01',9000,2,0,0,0,0)")
sid = {n: i for i, n in enumerate(names, 1)}
for n, f in (("Alisha", "2026-08-20"), ("Alisha", "2026-10-07"), ("Shivani", "2026-10-19"), ("Vikki", "2026-10-07"), ("Vikki", "2026-10-07")):
    con.execute("INSERT INTO issuance_pause(staff_id,item_type,from_date,to_date,reason,status) VALUES(?,?,?,NULL,'lost','open')", (sid[n], "uniform", f))
for n, d in (("Alisha", "2026-10-07"), ("Shivani", "2026-09-25"), ("Shivani", "2026-11-01")):
    con.execute("INSERT INTO issuance(staff_id,item_type,issued_date,status) VALUES(?,?,?,'draft')", (sid[n], "uniform", d))
con.commit()
chk("A1 before: Alisha, Shivani, Vikki paused today", all(not SR.issuance_ok(con, sid[n], "uniform", TODAY) for n in ("Alisha", "Shivani", "Vikki")))
con.close()
L = os.path.join(HERE, "s929_load.py")
r = subprocess.run([sys.executable, L, SR.DB_PATH], capture_output=True, text=True)
chk("B1 dry run says WOULD, 5 pauses", "WOULD" in r.stdout and "close 5 open" in r.stdout, r.stdout + r.stderr)
r = subprocess.run([sys.executable, L, SR.DB_PATH, "--apply"], capture_output=True, text=True)
chk("B2 apply", "APPLIED" in r.stdout and "5 pauses closed" in r.stdout and "3 pending entries superseded" in r.stdout and "5 assets" in r.stdout, r.stdout + r.stderr)
con = SR.get_db()
chk("B3 every staff member's uniform OK today (Amir untouched OK)", all(SR.issuance_ok(con, sid[n], "uniform", TODAY) for n in names))
chk("B4 the pause still covers its own past days (Alisha 20-Oct, Vikki 01-Nov)",
    not SR.issuance_ok(con, sid["Alisha"], "uniform", "2026-10-20") and not SR.issuance_ok(con, sid["Vikki"], "uniform", "2026-11-01"))
chk("B5 pauses closed to yesterday", {r[0] for r in con.execute("SELECT to_date FROM issuance_pause")} == {YEST})
cur = con.execute("SELECT size, pieces FROM issuance WHERE staff_id=? AND issued_date=? AND status='approved'", (sid["Alisha"], TODAY)).fetchone()
chk("B6 Alisha's current set: XL 40 · Blazer 1 · Shirts 2 · White T 2", cur and cur["size"] == "XL 40" and cur["pieces"] == "Blazer 1 · Shirts 2 · White T 2", dict(cur) if cur else None)
chk("B7 drafts superseded, none pending", con.execute("SELECT COUNT(*) FROM issuance WHERE status='draft'").fetchone()[0] == 0 and
    con.execute("SELECT COUNT(*) FROM issuance WHERE status='superseded'").fetchone()[0] == 3)
chk("B8 history rows with their dates (13)", con.execute("SELECT COUNT(*) FROM issuance WHERE note LIKE 'Shavez''s sheet%'").fetchone()[0] == 13)
a = {(r["staff_id"], r["asset_type"]) for r in con.execute("SELECT * FROM asset_issue WHERE status='issued'")}
chk("B9 mobiles Shavez/Darpan/Surendra/Ranjeet, cycle Sandip", a == {(sid["Shavez"], "mobile_phone"), (sid["Darpan"], "mobile_phone"),
    (sid["Surendra"], "mobile_phone"), (sid["Ranjeet"], "mobile_phone"), (sid["Sandip"], "bicycle")}, a)
chk("B10 i-cards untouched", all(SR.issuance_ok(con, sid[n], "icard", TODAY) for n in names))
con.close()
r = subprocess.run([sys.executable, L, SR.DB_PATH, "--apply"], capture_output=True, text=True)
chk("B11 a second apply says ALREADY DONE", "ALREADY DONE" in r.stdout, r.stdout)
# C. the code's own rule: approving a re-issue closes the open pause
SR.add_pause(sid["Darpan"], "uniform", "2026-11-10", "damaged", "alisha")
SR.add_pause(sid["Darpan"], "icard", "2026-11-10", "lost", "alisha")
SR.add_issuance(sid["Darpan"], "uniform", "", "2026-11-15", "alisha", "XL 40", "Shirts 2")
con = SR.get_db(); iid = con.execute("SELECT MAX(id) FROM issuance").fetchone()[0]
chk("C1 a new issue keeps size and pieces", tuple(con.execute("SELECT size,pieces,status FROM issuance WHERE id=?", (iid,)).fetchone()) == ("XL 40", "Shirts 2", "draft"))
con.close()
SR.approve_issuance(iid, "shavez")
con = SR.get_db()
p = con.execute("SELECT to_date, status FROM issuance_pause WHERE staff_id=? AND item_type='uniform' AND from_date='2026-11-10'", (sid["Darpan"],)).fetchone()
chk("C2 approving it closed the uniform pause to 14-Nov", tuple(p) == ("2026-11-14", "closed"), tuple(p))
q = con.execute("SELECT to_date FROM issuance_pause WHERE staff_id=? AND item_type='icard'", (sid["Darpan"],)).fetchone()
chk("C3 the i-card pause untouched", q[0] is None)
con.close()
SR.add_pause(sid["Ranjeet"], "uniform", "2026-11-20", "lost", "alisha")
SR.add_issuance(sid["Ranjeet"], "uniform", "", "2026-11-12", "alisha")
con = SR.get_db(); iid2 = con.execute("SELECT MAX(id) FROM issuance").fetchone()[0]; con.close()
SR.approve_issuance(iid2, "shavez")
con = SR.get_db()
chk("C4 an issue OLDER than the pause does not close it", con.execute("SELECT to_date FROM issuance_pause WHERE staff_id=? AND from_date='2026-11-20'", (sid["Ranjeet"],)).fetchone()[0] is None)
con.close()
# D. the page
SR.SR_LOCAL_USERS = {"manoj": {"pw": SR._pw_hash("x"), "role": "override"}, "shavez": {"pw": SR._pw_hash("x"), "role": "checker"}}
SR.app.secret_key = b"w929"
c = SR.app.test_client(); c.post(SR.APP_PREFIX + "/login", data={"user": "manoj", "password": "x"})
h = c.get(SR.APP_PREFIX + "/staff/%d" % sid["Alisha"]).get_data(as_text=True)
chk("D1 record page 200 with Size / What was given", "What was given" in h and "XL 40" in h and "Blazer 1 · Shirts 2 · White T 2" in h)
chk("D2 the seed row reads 'before the register'", "before the register" in h and ">2000-01-01<" not in h)
chk("D3 superseded shown, no Approve left for Alisha", "superseded" in h and 'action="%s/issuance/approve"' % SR.APP_PREFIX not in h)
chk("D4 the form asks size and what was given", 'name="size"' in h and 'name="pieces"' in h)
h2 = c.get(SR.APP_PREFIX + "/staff").get_data(as_text=True)
chk("D5 the staff list shows PAUSED only for this walk's own two new pauses", h2.count("PAUSED") == 2, h2.count("PAUSED"))
h3 = c.get(SR.APP_PREFIX + "/staff/%d" % sid["Shavez"]).get_data(as_text=True)
chk("D6 Shavez's page lists the clinic mobile", "Clinic mobile" in h3 and "Mobile phone" in h3)
r = c.post(SR.APP_PREFIX + "/issuance/add", data={"sid": str(sid["Vikki"]), "item": "uniform", "season": "", "issued_date": TODAY, "size": "M 36", "pieces": "Hoodie 1"})
con = SR.get_db()
chk("D7 the form's Issue saves size and pieces", r.status_code in (302, 303) and con.execute("SELECT 1 FROM issuance WHERE staff_id=? AND pieces='Hoodie 1' AND size='M 36'", (sid["Vikki"],)).fetchone())
con.close()
shutil.rmtree(tmp, ignore_errors=True)
print("WALK %d/%d" % (sum(res), len(res)))
