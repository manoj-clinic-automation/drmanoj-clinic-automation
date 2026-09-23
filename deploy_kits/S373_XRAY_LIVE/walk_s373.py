#!/usr/bin/env python3
"""walk_s373.py -- the X-ray LIVE filing, walked over a SCRATCH COPY of the real finance.db with the walk's own day
(2001-01-01) and IDs (9090xx): stub Drive folders (RECORDS_DRIVE_STUB), the plan, the mailbox's report, Check karein
(the check-folder picture, the missing file), the staff's ID answer, the next run filing it, the patient page gallery.
Asserts ONLY about the rows it made (F-581). Prints IDs and counts, never a real name.
Usage: FINANCE_DB=<scratch copy> python3 walk_s373.py <app dir with records.py> [<live records.py = negative control>]"""
import datetime as dt, importlib.util, json, os, sqlite3, sys, tempfile
N = [0]
DAY = "2001-01-01"
IDS = ("909001", "909002", "909003", "909006", "909007")
def check(name, cond, extra=""):
    N[0] += 1
    if not cond:
        print("WALK RED %d: %s %s" % (N[0], name, extra)); sys.exit(1)
def load(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def utc(day, hhmm):
    return (dt.datetime.fromisoformat("%sT%s:00" % (day, hhmm)) - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
def f(fid, name, hhmm, md5=None):
    return {"id": fid, "name": name, "mimeType": "image/jpeg", "modifiedTime": utc(DAY, hhmm), "md5Checksum": md5 or ("m-" + fid)}

app_dir = os.path.abspath(sys.argv[1]); old = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else ""
dbp = os.environ["FINANCE_DB"]
assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
stub = tempfile.mkdtemp(prefix="s373stub_"); os.environ["RECORDS_DRIVE_STUB"] = stub
os.environ["RECORDS_NOW"] = "2001-01-02T10:00:00"
os.environ["FINANCE_CRON_TOKEN"] = "walk-cron-token"
INBOX, TEST, CHECK = "walkINBOX000001", "walkTEST0000001", "walkCHECK000001"
def put(fid, files):
    json.dump(files, open(os.path.join(stub, "list_%s.json" % fid), "w"))
sys.path.insert(0, app_dir)
rec = load(os.path.join(app_dir, "records.py"), "records_s373")
con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row
rec.ensure(con)
# the walk's own world
con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE day=?)", (DAY,)); con.execute("DELETE FROM slip WHERE day=?", (DAY,))
con.execute("DELETE FROM patient_ref WHERE clinic_id IN (%s)" % ",".join("?" * len(IDS)), IDS)
con.execute("DELETE FROM record_file WHERE clinic_id IN (%s)" % ",".join("?" * len(IDS)), IDS)
for cid in IDS:
    con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", (cid, "WALK " + cid))
SAVED = {r["key"]: r["value"] for r in con.execute("SELECT key, value FROM record_setting WHERE key IN ('xray_inbox_id','xray_test_id','xray_check_id','xray_live_from')")}
for k, v in (("xray_inbox_id", INBOX), ("xray_test_id", TEST), ("xray_check_id", CHECK), ("xray_live_from", DAY)):
    con.execute("INSERT INTO record_setting(key, value, set_at) VALUES (?,?,'walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
n = 0
for cid, views in (("909001", ("Wrist AP",)), ("909002", ("Knee AP", "Knee Lateral")), ("909003", ("Ankle AP",)), ("909007", ("Hip AP",))):
    n += 1
    sid = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_at) VALUES ('xp',?,?,?,'ok',?)", (900000 + n, DAY, cid, DAY + " 16:00:00")).lastrowid
    for i, v in enumerate(views):
        con.execute("INSERT INTO slip_item(slip_id, kind, name, side, sort) VALUES (?,'xray',?,'',?)", (sid, v, i))
con.commit()
put(INBOX, [f("walkF01xxxxxxxx", "AAAA 909001.jpg", "16:10"), f("walkF02xxxxxxxx", "BBBB.jpg", "16:20"),
            f("walkF03xxxxxxxx", "AAAB 909001.jpg", "16:11", md5="m-walkF01xxxxxxxx"), dict(f("walkF04xxxxxxxx", "notes.txt", "16:30"), mimeType="text/plain")])
put(TEST, [f("walkF05xxxxxxxx", "CCCC 909002.jpg", "16:40"), f("walkF06xxxxxxxx", "CCCC 909002 l.jpg", "16:41")])
put(CHECK, [])

items, notes = rec.xray_actions(con)
by = {i["id"]: i for i in items}
check("plan: 5 actions (text file left alone)", len(items) == 5 and "walkF04xxxxxxxx" not in by, str(sorted(by)))
check("plan: 909001 filed with its study, in X-ray/Jan 2001/01-Jan", by["walkF01xxxxxxxx"]["action"] == "file"
      and by["walkF01xxxxxxxx"]["path"] == ["X-ray", "Jan 2001", "01-Jan"] and "909001" in by["walkF01xxxxxxxx"]["name"]
      and "Wrist AP" in by["walkF01xxxxxxxx"]["name"])
check("plan: the same picture twice -> dup", by["walkF03xxxxxxxx"]["action"] == "dup")
check("plan: no ID, no sister -> check", by["walkF02xxxxxxxx"]["action"] == "check")
check("plan: the test folder is read too; two views -> two files", by["walkF05xxxxxxxx"]["action"] == "file" and by["walkF06xxxxxxxx"]["action"] == "file"
      and "Knee AP" in by["walkF05xxxxxxxx"]["name"] and "Knee Lateral" in by["walkF06xxxxxxxx"]["name"])
check("plan: nothing filed before the mailbox reports", not rec._rows(con, "SELECT 1 FROM record_file WHERE clinic_id IN ('909001','909002')"))
rep = [{"id": "walkF01xxxxxxxx", "action": "file", "dest_id": "walkD01xxxxxxxx", "name": by["walkF01xxxxxxxx"]["name"]},
       {"id": "walkF05xxxxxxxx", "action": "file", "dest_id": "walkD05xxxxxxxx", "name": by["walkF05xxxxxxxx"]["name"]},
       {"id": "walkF06xxxxxxxx", "action": "file", "dest_id": "walkD06xxxxxxxx", "name": by["walkF06xxxxxxxx"]["name"]},
       {"id": "walkF02xxxxxxxx", "action": "check"}, {"id": "walkF03xxxxxxxx", "action": "dup"},
       {"id": "bad id!", "action": "file", "dest_id": "x"}]
check("done: 5 stored, the bad row ignored", rec.xray_done(con, rep) == 5)
check("done: again -> no second record_file", rec.xray_done(con, rep) == 5 and len(rec._rows(con, "SELECT 1 FROM record_file WHERE source='xray_inbox' AND source_ref LIKE 'walkF0%'")) == 3)
fr = rec._rows(con, "SELECT * FROM record_file WHERE clinic_id='909001'")
check("done: 909001 has its X-ray on the patient, kind xray, the COPY's Drive id", len(fr) == 1 and fr[0]["kind"] == "xray" and fr[0]["drive_id"] == "walkD01xxxxxxxx" and fr[0]["day"] == DAY)
# the mailbox moved them: inbox now empty of those, the check folder holds BBBB.jpg
put(INBOX, [dict(f("walkF04xxxxxxxx", "notes.txt", "16:30"), mimeType="text/plain")]); put(TEST, []); put(CHECK, [f("walkF02xxxxxxxx", "BBBB.jpg", "16:20")])
items, notes = rec.xray_actions(con)
check("run 2: nothing to do", items == [])
ck = [i for i in rec.check_items(con) if i["key"].startswith(("xf:walk", "xm:%s:9090" % DAY))]
keys = sorted(i["key"] for i in ck)
check("Check karein: the check-folder picture + 909003 (slip X-ray, no file) + 909007 (no file)",
      keys == ["xf:walkF02xxxxxxxx", "xm:%s:909003" % DAY, "xm:%s:909007" % DAY], str(keys))
check("Check karein: 909001 and 909002 are NOT asked (files arrived)", not any(i["key"].endswith(("909001", "909002")) for i in ck))
# the staff answer through the real screen
from flask import Flask
app = Flask("walk373")
def dbg():
    c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row; return c
def req(*roles, **kw):
    return ({"user": "shavez", "roles": ["maker"]}, None)
rec.init(app, dbg, req)
c = app.test_client()
page = c.get("/finance/checks").get_data(as_text=True)
check("screen: the picture's item carries the ID box", "BBBB.jpg" in page and 'name="new_id"' in page)
r = c.post("/finance/checks/answer", data={"key": "xf:walkF02xxxxxxxx", "a": "id_fixed", "new_id": "123456789"})
check("screen: a nonsense ID is refused", "dobara" in (r.headers.get("Location") or ""))
r = c.post("/finance/checks/answer", data={"key": "xf:walkF02xxxxxxxx", "a": "id_fixed", "new_id": "909007"})
check("screen: 909007 accepted", r.status_code == 303 and "Ho" in (r.headers.get("Location") or ""))
c.post("/finance/checks/answer", data={"key": "xm:%s:909003" % DAY, "a": "not_done"})
items, notes = rec.xray_actions(con)
check("run 3: the answered picture is filed under 909007", len(items) == 1 and items[0]["id"] == "walkF02xxxxxxxx" and items[0]["action"] == "file"
      and "909007" in items[0]["name"] and items[0]["path"] == ["X-ray", "Jan 2001", "01-Jan"], json.dumps(items))
rec.xray_done(con, [{"id": "walkF02xxxxxxxx", "action": "file", "dest_id": "walkD02xxxxxxxx", "name": items[0]["name"]}])
put(CHECK, [])
rec.xray_actions(con)
ck = [i for i in rec.check_items(con) if i["key"].startswith(("xf:walk", "xm:%s:9090" % DAY))]
check("after: every walk item closed (909003 answered 'not done', 909007 filed)", ck == [], str([i["key"] for i in ck]))
pg = c.get("/finance/records/p/909002").get_data(as_text=True)
check("patient page: two X-ray pictures side by side", pg.count('class="xg"') == 2 and "(next step)" not in pg)
check("cron doors: no token -> 401", c.get("/finance/records/api/xray-plan").status_code == 401 and c.post("/finance/records/api/xray-done", json={}).status_code == 401)
check("cron doors: the token -> 200", c.get("/finance/records/api/xray-plan", headers={"X-Finance-Cron": "walk-cron-token"}).get_json()["ok"])
if old:
    o = load(old, "records_live_neg")
    app2 = Flask("neg"); o.init(app2, dbg, req)
    check("negative control: the live records.py has no xray-plan door", app2.test_client().get("/finance/records/api/xray-plan").status_code == 404)
    olds = {r.rule for r in app2.url_map.iter_rules()}; news = {r.rule for r in app.url_map.iter_rules()}
    check("routes: +2, none lost", news - olds == {"/finance/records/api/xray-plan", "/finance/records/api/xray-done"} and not (olds - news))
# tidy the walk's own rows
for t, col in (("record_file", "clinic_id"), ("patient_ref", "clinic_id")):
    con.execute("DELETE FROM %s WHERE %s IN (%s)" % (t, col, ",".join("?" * len(IDS))), IDS)
con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE day=?)", (DAY,)); con.execute("DELETE FROM slip WHERE day=?", (DAY,))
con.execute("DELETE FROM xray_filing WHERE src_id LIKE 'walk%'"); con.execute("DELETE FROM record_check WHERE key LIKE 'x_:%walk%' OR key LIKE 'xm:2001%'")
con.execute("DELETE FROM record_setting WHERE key IN ('xray_inbox_id','xray_test_id','xray_check_id','xray_live_from')")
for k, v in SAVED.items():
    con.execute("INSERT INTO record_setting(key, value, set_at) VALUES (?,?,'restored')", (k, v))
con.commit()
print("WALK OK %d/%d checks" % (N[0], N[0]))
