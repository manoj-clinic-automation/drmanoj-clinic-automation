"""walk_s931.py FILE -- S931's walk on a MADE-UP staff register: reception asks a pause, Shavez / a doctor approves.
Prints PASS/FAIL lines and 'WALK n/m' last."""
import datetime as dt, importlib.util, json, os, shutil, sys, tempfile
SRC = os.path.abspath(sys.argv[1])
tmp = tempfile.mkdtemp(prefix="w931_")
shutil.copy(SRC, os.path.join(tmp, "staff_register.py"))
spec = importlib.util.spec_from_file_location("sr_w931", os.path.join(tmp, "staff_register.py"))
SR = importlib.util.module_from_spec(spec); spec.loader.exec_module(SR)
res = []
def chk(name, ok, why=""):
    res.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + ("" if ok else " -- " + str(why)[:200]))
TODAY = SR._today()
SR.DB_PATH = os.path.join(tmp, "t.db"); SR.init_db()
con = SR.get_db()
for i, n in enumerate(["Alisha", "Shavez", "Vikki", "Darpan"], 1):
    con.execute("INSERT INTO staff(staff_id,name,join_date,base_salary,allowed_offs,minutes_exempt,cover_eligible,outstation_eligible,active) "
                "VALUES(?,?,?,?,?,?,?,?,1)", (i, n, "2026-01-01", 1, 2, 0, 0, 0))
    for it in ("uniform", "icard"):
        con.execute("INSERT INTO issuance(staff_id,item_type,issued_date,status) VALUES(?,?,'2000-01-01','approved')", (i, it))
con.commit(); con.close()
SR.SR_LOCAL_USERS = {"manoj": {"pw": SR._pw_hash("x"), "role": "override"}, "shavez": {"pw": SR._pw_hash("x"), "role": "checker"},
                     "alisha": {"pw": SR._pw_hash("x"), "role": "maker"}}
SR.app.secret_key = b"w931"
P = SR.APP_PREFIX
ca = SR.app.test_client(); ca.post(P + "/login", data={"user": "alisha", "password": "x"})
cs = SR.app.test_client(); cs.post(P + "/login", data={"user": "shavez", "password": "x"})
cm = SR.app.test_client(); cm.post(P + "/login", data={"user": "manoj", "password": "x"})
h = ca.get(P + "/staff/3").get_data(as_text=True)
chk("A1 reception's button reads 'Ask for a pause'", "Ask for a pause" in h and "Start pause" not in h)
r = ca.post(P + "/pause/add", data={"sid": "3", "item": "uniform", "from_date": TODAY, "reason": "lost"})
chk("A2 reception's pause is an ask (message says so)", r.status_code in (302, 303) and "asked" in r.headers.get("Location", ""), r.headers.get("Location"))
con = SR.get_db()
pid = con.execute("SELECT id FROM issuance_pause WHERE staff_id=3").fetchone()[0]
chk("A3 stored as 'requested'", con.execute("SELECT status FROM issuance_pause WHERE id=?", (pid,)).fetchone()[0] == "requested")
chk("A4 the fine NOT paused while asked", SR.issuance_ok(con, 3, "uniform", TODAY))
con.close()
r = ca.post(P + "/pause/decide", data={"pid": str(pid), "act": "approve"})
con = SR.get_db()
chk("A5 reception cannot approve its own ask", con.execute("SELECT status FROM issuance_pause WHERE id=?", (pid,)).fetchone()[0] == "requested", r.status_code)
con.close()
hl = cs.get(P + "/staff").get_data(as_text=True)
chk("B1 staff list shows PAUSE ASKED for Vikki", "PAUSE ASKED" in hl and "uniform" in hl)
hr = cs.get(P + "/review").get_data(as_text=True)
chk("B2 Pending review shows the ask card to Shavez", "pause asks" in hr and "Vikki" in hr)
j = json.loads(cs.get(P + "/review/counts").get_data(as_text=True))
ja = json.loads(ca.get(P + "/review/counts").get_data(as_text=True))
chk("B3 the portal count includes the ask for an approver, not for reception", j["to_approve"] >= 1 and ja["to_approve"] == 0, (j, ja))
hp = cs.get(P + "/staff/3").get_data(as_text=True)
chk("B4 Shavez sees Approve / Reject and 'not counted yet'", "not counted yet" in hp and 'value="approve"' in hp and 'value="reject"' in hp)
r = cs.post(P + "/pause/decide", data={"pid": str(pid), "act": "approve", "back": "review"})
con = SR.get_db()
chk("C1 Shavez approves -> 'open' and the fine paused", con.execute("SELECT status FROM issuance_pause WHERE id=?", (pid,)).fetchone()[0] == "open"
    and not SR.issuance_ok(con, 3, "uniform", TODAY), r.headers.get("Location"))
chk("C2 back to Pending review with a message", "/review?m=" in (r.headers.get("Location") or ""))
con.close()
r = cs.post(P + "/pause/decide", data={"pid": str(pid), "act": "reject"})
con = SR.get_db()
chk("C3 a decided ask cannot be decided again", con.execute("SELECT status FROM issuance_pause WHERE id=?", (pid,)).fetchone()[0] == "open")
con.close()
ca.post(P + "/pause/add", data={"sid": "4", "item": "icard", "from_date": TODAY, "reason": "lost"})
con = SR.get_db(); pid2 = con.execute("SELECT id FROM issuance_pause WHERE staff_id=4").fetchone()[0]; con.close()
cm.post(P + "/pause/decide", data={"pid": str(pid2), "act": "reject"})
con = SR.get_db()
chk("D1 the doctor rejects -> 'rejected', fine stays", con.execute("SELECT status FROM issuance_pause WHERE id=?", (pid2,)).fetchone()[0] == "rejected"
    and SR.issuance_ok(con, 4, "icard", TODAY))
con.close()
r = cs.post(P + "/pause/add", data={"sid": "1", "item": "uniform", "from_date": TODAY, "reason": "damaged"})
con = SR.get_db()
chk("E1 Shavez's own pause starts at once", con.execute("SELECT status FROM issuance_pause WHERE staff_id=1").fetchone()[0] == "open"
    and not SR.issuance_ok(con, 1, "uniform", TODAY) and "started" in (r.headers.get("Location") or ""))
con.close()
r = cm.post(P + "/pause/add", data={"sid": "2", "item": "icard", "from_date": TODAY, "reason": "lost"})
con = SR.get_db()
chk("E2 the doctor's own pause starts at once", con.execute("SELECT status FROM issuance_pause WHERE staff_id=2").fetchone()[0] == "open")
con.close()
# F: S929's auto-close leaves an ask alone
ca.post(P + "/pause/add", data={"sid": "2", "item": "uniform", "from_date": "2026-11-01", "reason": "lost"})
SR.add_issuance(2, "uniform", "", TODAY, "alisha", "L 38", "Shirts 2")
con = SR.get_db(); iid = con.execute("SELECT MAX(id) FROM issuance").fetchone()[0]; con.close()
SR.approve_issuance(iid, "shavez")
con = SR.get_db()
chk("F1 a re-issue approval leaves a reception ask open (not counted, not closed)",
    con.execute("SELECT status, to_date FROM issuance_pause WHERE staff_id=2 AND item_type='uniform'").fetchone()[:] == ("requested", None))
con.close()
chk("F2 the register's daily page still answers", cm.get(P + "/").status_code == 200)
shutil.rmtree(tmp, ignore_errors=True)
print("WALK %d/%d" % (sum(res), len(res)))
