#!/usr/bin/env python3
"""walk_s333.py -- (S332 walk + the S333 X-ray test run) the live-shape walk of the patient-record page: THE REAL finance_app.py (patched) over
a SCRATCH COPY of the real finance.db, every role at the front gate, both mailbox doors, the pages the
doctor opens and a file open through a Drive stub. Nothing live is touched: the caller passes a copy.
Header identity is used ONLY here. It prints IDs and counts, never a name.
Usage: FINANCE_DB=<copy> FINANCE_ALLOW_HEADER_AUTH=1 [RECORDS_NOW=<iso>] RECORDS_DRIVE_STUB=<dir> python3 walk_s332.py <app dir>
"""
import os
import re
import sqlite3
import sys

N = [0]


def check(name, cond, extra=""):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s %s" % (N[0], name, extra))
        sys.exit(1)


def counts(con):
    out = {}
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'record_%' "
                            "AND name<>'sqlite_sequence' AND name<>'audit_log'"):
        out[t] = con.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
    return out


def main():
    sys.path.insert(0, sys.argv[1])
    os.chdir(sys.argv[1])
    assert os.environ.get("FINANCE_ALLOW_HEADER_AUTH") == "1"
    dbp = os.environ["FINANCE_DB"]
    assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
    stub = os.environ["RECORDS_DRIVE_STUB"]
    os.environ["FINANCE_CRON_TOKEN"] = "walk-token-s333"
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    if not os.environ.get("RECORDS_NOW"):          # the latest day of the copy with a real list of slips
        d = con.execute("SELECT day FROM slip WHERE state='ok' AND clinic_id<>'' GROUP BY day "
                        "HAVING COUNT(DISTINCT clinic_id)>=3 ORDER BY day DESC LIMIT 1").fetchone()
        os.environ["RECORDS_NOW"] = (d[0] if d else "2026-09-19") + "T18:00:00"
    before = counts(con)
    import finance_app as fa
    for b in ("records", "slip_log", "petty_book", "owner_sheets", "clinic_day"):
        check("%s mounted" % b, b in fa.app.blueprints)
    check("front gate resolves the records unit", fa._unit_for_path("/finance/records/p/1") == "records"
          and fa._unit_for_path("/finance/records") == "records" and fa._unit_for_path("/finance/slips") == "slips")
    c = fa.app.test_client()
    H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}          # noqa: E731
    T = {"X-Finance-Cron": "walk-token-s333"}
    get = lambda u, p: c.get(p, headers=H(u))                        # noqa: E731
    # ---- gate: the doctors only
    for u in ("stranger", "shavez", "alisha", "shivani", "reception", "awdhesh", "bhati", "darpan", "amir"):
        s = get(u, "/finance/records").status_code
        check("%s refused" % u, s in (302, 403), s)
        s = get(u, "/finance/records/p/100").status_code
        check("%s refused patient page" % u, s in (302, 403), s)
    for u in ("manoj", "bhawna"):
        r = get(u, "/finance/records")
        check("%s opens records" % u, r.status_code == 200, r.status_code)
    check("shavez still opens the slip tile", get("shavez", "/finance/slips").status_code == 200)
    check("manoj still opens the clinic day", get("manoj", "/finance/clinic/day").status_code in (200, 302))
    # ---- the doors
    check("reader without token 401", c.get("/finance/records/api/reader").status_code in (401, 302))
    r = c.get("/finance/records/api/reader", headers=T)
    check("reader with token answers", r.status_code == 200 and "email" in r.get_json(), r.status_code)
    check("lab-file without token refused", c.post("/finance/records/api/lab-file", json={}).status_code in (401, 302))
    check("lab-file wrong token refused", c.post("/finance/records/api/lab-file", json={},
                                                 headers={"X-Finance-Cron": "nope"}).status_code in (401, 302))
    lab = [dict(r) for r in con.execute("SELECT msg_id, clinic_id, received_at FROM lab_report ORDER BY received_at LIMIT 3")]
    check("the scratch copy has lab reports", len(lab) >= 2, len(lab))
    files = []
    for i, x in enumerate(lab):
        did = "stubDriveId%05d" % i
        open(os.path.join(stub, did), "wb").write(b"%PDF-1.4 walk stub " + did.encode())
        files.append({"msg_id": x["msg_id"], "clinic_id": x["clinic_id"], "received_at": x["received_at"],
                      "drive_id": did, "file_name": "walk %d.pdf" % i, "mime": "application/pdf", "bytes": 20})
    files.append({"msg_id": "walkNoPdf", "clinic_id": lab[0]["clinic_id"], "received_at": lab[0]["received_at"],
                  "drive_id": "", "file_name": ""})
    files.append({"msg_id": "walkBad", "clinic_id": "12", "received_at": "yesterday", "drive_id": "x"})
    files.append({"msg_id": "walkBad2", "clinic_id": "12", "received_at": "2026-09-19 10:00:00", "drive_id": "../etc"})
    r = c.post("/finance/records/api/lab-file", json={"files": files}, headers=T)
    j = r.get_json()
    check("lab-file stores", r.status_code == 200 and j["stored"] == len(lab) + 1 and j["refused"] == 2, j)
    r = c.post("/finance/records/api/lab-file", json={"files": files}, headers=T)
    check("lab-file is idempotent", r.get_json()["stored"] == 0, r.get_json())
    # ---- home
    t = get("manoj", "/finance/records").get_data(as_text=True)
    today_ids = [r[0] for r in con.execute("SELECT DISTINCT clinic_id FROM slip WHERE day=? AND state='ok' AND clinic_id<>''",
                                           (os.environ["RECORDS_NOW"][:10],))]
    check("the scratch day has slips", len(today_ids) >= 3, len(today_ids))
    for cid in today_ids:
        check("today lists %s" % cid[-4:], "/finance/records/p/%s" % cid in t)
    check("filed reports listed", "Blood reports filed" in t and "/finance/records/p/%s" % lab[0]["clinic_id"] in t)
    r = get("manoj", "/finance/records?q=%s" % lab[0]["clinic_id"])
    check("a typed ID opens the patient", r.status_code == 303 and r.headers["Location"].endswith("/p/%s" % lab[0]["clinic_id"]))
    nm = con.execute("SELECT name FROM patient_ref WHERE clinic_id=?", (today_ids[0],)).fetchone()
    if nm and len(nm[0]) >= 4:
        t = get("manoj", "/finance/records?q=%s" % nm[0][:4]).get_data(as_text=True)
        check("a name search finds the patient", "/finance/records/p/%s" % today_ids[0] in t)
    t = get("manoj", "/finance/records?q=%3Cscript%3E").get_data(as_text=True)
    check("search text is escaped", "<script>alert" not in t and "&lt;script&gt;" in t)
    # ---- the patient page, the one with a filed report
    cid = lab[0]["clinic_id"]
    t = get("manoj", "/finance/records/p/%s" % cid).get_data(as_text=True)
    for sec in ("Timeline", "Visits", "X-rays &amp; reports", "Pharmacy", "Procedures", "Hospital &amp; surgery"):
        check("section %s" % sec, sec in t)
    check("sections closed until tapped", "<details class=\"sec\" id=\"tl\">" in t and " open" not in re.findall(r"<details[^>]*>", t)[0])
    fid = con.execute("SELECT id FROM record_file WHERE clinic_id=? AND drive_id LIKE 'stubDriveId%' ORDER BY id LIMIT 1", (cid,)).fetchone()[0]
    check("the report has an Open link", "/finance/records/file/%d" % fid in t)
    check("the no-PDF e-mail is said", "e-mail had no PDF" in t)
    # ---- a patient with pharmacy + return against the bill (the richest ID in the copy)
    row = con.execute("""SELECT p.clinic_id, COUNT(*) n FROM sale_item s JOIN patient_ref p ON p.id=s.patient_ref_id
        WHERE s.service='pharmacy_return' AND p.clinic_id NOT LIKE 'WA%%' GROUP BY 1 ORDER BY n DESC LIMIT 1""").fetchone()
    if row:
        t = get("manoj", "/finance/records/p/%s" % row[0]).get_data(as_text=True)
        check("pharmacy bills shown", 'class="bill' in t)
        check("a return is shown (against a bill or alone)", "Return " in t)
    wa = con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id LIKE 'WA%' LIMIT 1").fetchone()
    if wa:
        t = get("manoj", "/finance/records?q=%s" % wa[0]).get_data(as_text=True)
        check("a walk-in code is not an ID jump", "Patient records" in t)
    t = get("manoj", "/finance/records/p/99999999").get_data(as_text=True)
    check("an unknown ID says so", "Name not known yet" in t and "Nothing on record yet" in t)
    check("a junk ID goes home", get("manoj", "/finance/records/p/%3Cx%3E").status_code in (303, 404))
    # ---- opening a file
    r = get("manoj", "/finance/records/file/%d" % fid)
    check("file opens inline", r.status_code == 200 and r.data.startswith(b"%PDF") and "inline" in r.headers["Content-Disposition"])
    check("no-store", "no-store" in r.headers.get("Cache-Control", ""))
    check("shavez cannot open the file", get("shavez", "/finance/records/file/%d" % fid).status_code in (302, 403))
    lo = con.execute("SELECT who, ok FROM record_open WHERE file_id=? ORDER BY id", (fid,)).fetchall()
    check("the open is logged once, by manoj", [tuple(x) for x in lo] == [("manoj", 1)], lo)
    check("unknown file 404", get("manoj", "/finance/records/file/999999").status_code == 404)
    os.remove(os.path.join(stub, "stubDriveId00001"))
    f2 = con.execute("SELECT id FROM record_file WHERE drive_id='stubDriveId00001'").fetchone()[0]
    r = get("bhawna", "/finance/records/file/%d" % f2)
    check("a Drive failure is said, not crashed", r.status_code == 502)
    check("a failed open is logged too", con.execute("SELECT ok FROM record_open WHERE file_id=?", (f2,)).fetchone()[0] == 0)
    # ---- S333: the X-ray test run
    check("folders door refuses no token", c.post("/finance/records/api/folders", json={}).status_code in (401, 302))
    fids = {"root_id": "walkRootFolder01", "blood_id": "walkBloodFolder1", "xray_test_id": "walkXrayTest0001",
            "xray_inbox_id": "walkXrayInbox001", "xray_check_id": "walkXrayCheck001"}
    r = c.post("/finance/records/api/folders", json=dict(fids, junk="x", xray_test_id_bad="../"), headers=T)
    check("folders door stores five", r.status_code == 200 and r.get_json()["stored"] == 5, r.get_json())
    t = get("manoj", "/finance/records/xray-test").get_data(as_text=True)
    check("empty test folder is said", "The folder is empty" in t)
    check("shavez refused the test run", get("shavez", "/finance/records/xray-test").status_code in (302, 403))
    xs = con.execute("""SELECT s.day, s.clinic_id, s.logged_at, COUNT(i.id) k FROM slip s JOIN slip_item i ON i.slip_id=s.id
        WHERE s.series='xp' AND s.state='ok' AND s.clinic_id<>'' AND i.kind='xray' GROUP BY s.id ORDER BY k DESC, s.id""").fetchall()
    check("the copy has X-ray slips", len(xs) >= 2, len(xs))
    import datetime as _dt, json as _json
    def utc(lg, mins):
        return (_dt.datetime.fromisoformat(lg) + _dt.timedelta(minutes=mins) - _dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    a, b = xs[0], xs[1]
    L = []
    for i in range(a["k"]):
        L.append({"id": "fa%d" % i, "name": "%s%s.jpg" % (a["clinic_id"], "" if i == 0 else " (%d)" % (i + 1)),
                  "mimeType": "image/jpeg", "md5Checksum": "m-a-%d" % i, "modifiedTime": utc(a["logged_at"], 10 + i)})
    for i in range(b["k"] + 1):
        L.append({"id": "fb%d" % i, "name": "%s_%d.JPG" % (b["clinic_id"], i), "mimeType": "image/jpeg",
                  "md5Checksum": "m-b-%d" % i, "modifiedTime": utc(b["logged_at"], 5 + i)})
    L.append({"id": "fc", "name": "99999999.jpg", "mimeType": "image/jpeg", "md5Checksum": "m-c", "modifiedTime": utc(a["logged_at"], 3)})
    L.append({"id": "fd", "name": "copy of it.jpg", "mimeType": "image/jpeg", "md5Checksum": "m-a-0", "modifiedTime": utc(a["logged_at"], 3)})
    L.append({"id": "fe", "name": "scan.jpg", "mimeType": "image/jpeg", "md5Checksum": "m-e", "modifiedTime": utc(a["logged_at"], 3)})
    L.append({"id": "ff", "name": "notes.txt", "mimeType": "text/plain", "md5Checksum": "m-f", "modifiedTime": utc(a["logged_at"], 3)})
    _json.dump(L, open(os.path.join(stub, "list_walkXrayTest0001.json"), "w"))
    t = get("manoj", "/finance/records/xray-test").get_data(as_text=True)
    check("matched count", "<b>%d matched</b>" % a["k"] in t, a["k"])
    check("counts-differ numbered", "%d numbered" % (b["k"] + 1) in t and "X-ray %d" % (b["k"] + 1) in t)
    check("two to the check folder", "2 to the check folder" in t)
    check("duplicate kept once", "1 duplicate(s)" in t and "kept once" in t)
    check("not a picture left alone", "1 not pictures" in t)
    check("clock agrees", "clock agrees" in t)
    st = con.execute("SELECT i.name FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.day=? AND s.clinic_id=? AND i.kind='xray' "
                     "ORDER BY i.sort, i.id LIMIT 1", (a["day"], a["clinic_id"])).fetchone()
    check("proposed name carries the study", "%s \u00b7 %s \u00b7" % (a["day"], a["clinic_id"]) in t and (st[0] or "X-ray").replace("&", "&amp;") in t)
    check("read-only said", "Nothing in Drive is renamed" in t)
    # ---- F-552: what the walk did not touch did not move
    after = counts(con)
    moved = {k: (before[k], after.get(k)) for k in before if before[k] != after.get(k)}
    check("no other table moved", not moved, moved)
    print("WALK OK %d checks" % N[0])


if __name__ == "__main__":
    main()
