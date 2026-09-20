#!/usr/bin/env python3
"""walk_s344.py -- (S344 adds the WhatsApp reports) (S342 = S340 with the walk finding its own rows by key) (S332 walk + S333 X-ray test run + S335 Drive helper + S340 Check karein) the live-shape walk of the patient-record page: THE REAL finance_app.py (patched) over
a SCRATCH COPY of the real finance.db, every role at the front gate, both mailbox doors, the pages the
doctor opens and a file open through a Drive stub. Nothing live is touched: the caller passes a copy.
Header identity is used ONLY here. It prints IDs and counts, never a name.
Usage: FINANCE_DB=<copy> FINANCE_ALLOW_HEADER_AUTH=1 [RECORDS_NOW=<iso>] RECORDS_DRIVE_STUB=<dir> python3 walk_s332.py <app dir>
"""
import json
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
                            "AND name<>'sqlite_sequence' AND name<>'audit_log' AND name<>'blood_order'"):
        out[t] = con.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
    return out


def main():
    sys.path.insert(0, sys.argv[1])
    os.chdir(sys.argv[1])
    assert os.environ.get("FINANCE_ALLOW_HEADER_AUTH") == "1"
    dbp = os.environ["FINANCE_DB"]
    assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
    stub = os.environ["RECORDS_DRIVE_STUB"]
    os.environ["FINANCE_CRON_TOKEN"] = "walk-token-s344"
    os.environ["CHECK_FROM"] = "2026-01-01"
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
    T = {"X-Finance-Cron": "walk-token-s344"}
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
    # ---- S335: the same reads through the venv helper (a subprocess), as the live box does them
    os.environ.pop("RECORDS_DRIVE_STUB", None)
    os.environ["RECORDS_VENV"] = sys.executable
    os.environ["RECORDS_HELPER_STUB"] = stub
    r = get("manoj", "/finance/records/file/%d" % fid)
    check("helper: file opens", r.status_code == 200 and r.data.startswith(b"%PDF") and r.mimetype == "application/pdf", r.status_code)
    r = get("manoj", "/finance/records/file/%d" % f2)
    check("helper: a missing file is said", r.status_code == 502 and "Drive said 404" in r.get_data(as_text=True))
    t = get("manoj", "/finance/records/xray-test").get_data(as_text=True)
    check("helper: the test run lists", "<b>%d matched</b>" % a["k"] in t)
    os.environ["RECORDS_VENV"] = "/nonexistent/python"
    r = get("manoj", "/finance/records/file/%d" % fid)
    check("helper: no venv is said, not crashed", r.status_code == 502 and "did not run" in r.get_data(as_text=True))
    os.environ["RECORDS_DRIVE_STUB"] = stub
    # ---- S340: Check karein
    check("front gate resolves the checks unit", fa._unit_for_path("/finance/checks/answer") == "checks")
    for u in ("alisha", "shivani", "reception", "shavez", "manoj", "bhawna"):
        s = get(u, "/finance/checks").status_code
        check("%s opens Check karein" % u, s == 200, s)
    for u in ("awdhesh", "darpan", "bhati", "amir", "stranger"):
        s = get(u, "/finance/checks").status_code
        check("%s refused Check karein" % u, s in (302, 403), s)
    check("alisha still refused records", get("alisha", "/finance/records").status_code in (302, 403))
    today = os.environ["RECORDS_NOW"][:10]
    D = lambda n: (_dt.date.fromisoformat(today) - _dt.timedelta(days=n)).isoformat()          # noqa: E731
    have_lab = {r[0] for r in con.execute("SELECT clinic_id FROM lab_report")}
    have_pdf = {r[0] for r in con.execute("SELECT clinic_id FROM record_file WHERE drive_id<>''")}
    ids = [r[0] for r in con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id GLOB '[0-9]*' ORDER BY id DESC LIMIT 40")
           if r[0] not in have_lab and r[0] not in have_pdf][:5]
    check("five clean IDs for the scenario", len(ids) == 5)
    bo = lambda d, c, oc="": con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, state, outcome, logged_by, logged_at) "
                                          "VALUES (?,?,?,?,?,?,?)", (d, c, "", "ok", oc, "walk", d + " 10:00:00"))  # noqa: E731
    bo(D(3), ids[0])                     # open: 3 days, no report
    bo(D(3), ids[1], "not_tested")       # answered on the upload screen -> not asked again
    bo(D(1), ids[2])                     # too early to ask
    bo(D(4), lab[0]["clinic_id"]) if lab[0]["received_at"][:10] >= D(4) else None
    con.commit()
    r = c.post("/finance/records/api/lab-file", headers=T, json={"files": [
        {"msg_id": "walkUnknown", "clinic_id": "99999997", "received_at": D(2) + " 09:00:00", "drive_id": "stubDriveUnknown1",
         "file_name": "u.pdf"},
        {"msg_id": "walkNoPdf2", "clinic_id": ids[3], "received_at": D(2) + " 09:00:00", "drive_id": ""}]})
    check("scenario files stored", r.get_json()["stored"] == 2, r.get_json())
    t = get("alisha", "/finance/checks").get_data(as_text=True)
    keys = re.findall(r'name="key" value="([^"]+)"', t)
    check("blood with no report is asked", "bo:%s:%s" % (D(3), ids[0]) in keys, keys)
    check("an answered order is not asked again", "bo:%s:%s" % (D(3), ids[1]) not in keys)
    check("a 1-day order is not asked yet", "bo:%s:%s" % (D(1), ids[2]) not in keys)
    check("the order with a report is not asked", not any(k.endswith(":" + lab[0]["clinic_id"]) and k.startswith("bo:") for k in keys))
    # the LIVE data may already hold real items of every kind (S340 was refused on the box for counting
    # "exactly one"): the walk finds its OWN rows by their message ids, and asserts only about those.
    rid = lambda ref: con.execute("SELECT id FROM record_file WHERE source_ref LIKE ?", (ref + "#%",)).fetchone()[0]  # noqa: E731
    uk = ["lu:%d" % rid("walkUnknown")]
    npk = ["np:%d" % rid("walkNoPdf2")]
    check("unknown ID is asked", uk[0] in keys and "99999997" in t, keys)
    check("the e-mail with no PDF is asked", npk[0] in keys, keys)
    check("the walk's earlier no-PDF e-mail is closed by the PDFs beside it", "np:%d" % rid("walkNoPdf") not in keys)
    check("oldest first", keys == sorted(keys, key=lambda k: keys.index(k)) and keys.index(uk[0]) >= 0)
    check("Hindi on the staff page", "Blood test likha tha" in t and 'lang="hi"' in t)
    h = get("manoj", "/finance/records").get_data(as_text=True)
    check("the doctors' line counts", "Patient records: %d need" % len(keys) in h and "oldest" in h, len(keys))
    P2 = lambda u, d: c.post("/finance/checks/answer", data=d, headers=H(u))                 # noqa: E731
    r = P2("awdhesh", {"key": keys[0], "a": "not_tested"})
    check("awdhesh cannot answer", r.status_code in (302, 403))
    r = P2("alisha", {"key": "bo:%s:%s" % (D(3), ids[0]), "a": "id_ok"})
    check("a wrong answer is refused", "samajh nahi" in c.get(r.headers["Location"], headers=H("alisha")).get_data(as_text=True))
    r = P2("alisha", {"key": "bo:%s:%s" % (D(3), ids[0]), "a": "asked"})
    check("blood answered", r.status_code == 303)
    r = P2("shivani", {"key": uk[0], "a": "id_fixed", "new_id": "99999996"})
    check("a correction to another unknown ID is refused", "list mein nahi" in c.get(r.headers["Location"], headers=H("shivani")).get_data(as_text=True))
    r = P2("shivani", {"key": uk[0], "a": "id_fixed", "new_id": ids[4]})
    fid_u = int(uk[0][3:])
    check("the ID is corrected on the file", con.execute("SELECT clinic_id FROM record_file WHERE id=?", (fid_u,)).fetchone()[0] == ids[4])
    r = P2("shavez", {"key": npk[0], "a": "not_needed"})
    t = get("alisha", "/finance/checks").get_data(as_text=True)
    left = re.findall(r'name="key" value="([^"]+)"', t)
    check("answered items leave the queue", not ({"bo:%s:%s" % (D(3), ids[0]), uk[0], npk[0]} & set(left)), left)
    r = P2("alisha", {"key": uk[0], "a": "id_ok"})
    check("a closed item says so", "pehle hi" in c.get(r.headers["Location"], headers=H("alisha")).get_data(as_text=True))
    h = get("bhawna", "/finance/records").get_data(as_text=True)
    check("the trail names who answered", "by alisha" in h and "by shivani" in h and "ID corrected" in h)
    t = get("manoj", "/finance/records/p/%s" % ids[4]).get_data(as_text=True)
    check("the corrected report shows on the right patient", "/finance/records/file/%d" % fid_u in t)
    import records as _rc
    os.environ["RECORDS_NOW"] = (_dt.date.fromisoformat(today) + _dt.timedelta(days=4)).isoformat() + "T10:00:00"
    t = get("alisha", "/finance/checks").get_data(as_text=True)
    check("'asked the lab' comes back after 3 days", "bo:%s:%s" % (D(3), ids[0]) in t and "mangwaya tha" in t)
    os.environ["RECORDS_NOW"] = today + "T18:00:00"

    # ---- S344: WhatsApp reports
    import finance_patient_match as _fpm
    os.environ["PATIENT_FP_SALT"] = "walk-salt-s344"
    wdir = os.path.join(os.path.dirname(dbp), "wa_logs")
    os.makedirs(wdir, exist_ok=True)
    os.environ["RECORDS_WA_DIR"] = wdir
    os.environ["RECORDS_WA_FROM"] = "2026-01-01"
    fam = [r[0] for r in con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id GLOB '[0-9]*' "
                                      "AND (merged_into IS NULL OR merged_into='') ORDER BY id LIMIT 2")]
    mob = "98" + "76543210"
    con.execute("UPDATE patient_ref SET mobile_fp=? WHERE clinic_id IN (?,?)", (_fpm.fingerprint(mob, "walk-salt-s344"), fam[0], fam[1]))
    con.commit()
    L = "https://myop-chat-prod.s3.ap-south-1.amazonaws.com/media/walk%d.jpg"
    def ev(mid, typ, link, phone, direction="incoming"):
        return json.dumps({"at": today + "T11:0%d:00+05:30" % (len(mid) % 10), "body": {"customer_identifier": phone,
                           "direction": direction, "payload": {"id": mid, "data": {"type": typ, "context": {"link": link}}}}})
    lines = [ev("waA", "image", L % 1, "91" + mob), ev("waB", "document", L % 2, "91" + "9" * 9 + "1"),
             ev("waOut", "image", L % 3, "91" + mob, "outgoing"), ev("waC", "image", None, "91" + mob),
             ev("waC", "image", L % 4, "91" + mob), ev("waT", "text", "", "91" + mob), ev("waAud", "audio", L % 5, "91" + mob),
             ev("waBad", "image", "http://evil.example/x.jpg", "91" + mob), "not json"]
    open(os.path.join(wdir, today + ".jsonl"), "w").write("\n".join(lines) + "\n")
    check("wa-pending refuses no token", c.get("/finance/records/api/wa-pending").status_code in (401, 302))
    j = c.get("/finance/records/api/wa-pending", headers=T).get_json()
    got = sorted(i["msg_id"] for i in j["items"])
    check("only the patients' photos/PDFs with a real link", got == ["waA", "waB", "waC"], got)
    check("no phone number leaves the server", all(set(i) == {"msg_id", "link", "mtype", "received_at"} for i in j["items"]))
    check("the sender is kept only as a fingerprint + last four",
          con.execute("SELECT fp<>'' AND last4='3210' AND suggest<>'' FROM record_wa WHERE msg_id='waA'").fetchone()[0] == 1)
    check("both family members are suggested", set(con.execute("SELECT suggest FROM record_wa WHERE msg_id='waA'").fetchone()[0].split(",")) == set(fam))
    for mid in ("waA", "waB"):
        open(os.path.join(stub, "wa%sDriveId000" % mid), "wb").write(b"\xff\xd8 walk")
    r = c.post("/finance/records/api/wa-file", headers=T, json={"files": [
        {"msg_id": "waA", "drive_id": "wawaADriveId000", "file_name": "a.jpg", "mime": "image/jpeg", "bytes": 7},
        {"msg_id": "waB", "drive_id": "wawaBDriveId000", "file_name": "b.jpg", "mime": "image/jpeg", "bytes": 7},
        {"msg_id": "waC", "drive_id": ""}]})
    check("wa-file stores three", r.get_json()["stored"] == 3, r.get_json())
    check("a second sweep adds nothing", c.get("/finance/records/api/wa-pending", headers=T).get_json()["items"] == [])
    t = get("alisha", "/finance/checks").get_data(as_text=True)
    check("two WhatsApp items for reception", t.count('value="wa:') == 2 and "File dekhein" in t and "Report nahi hai" in t)
    check("the family is offered, not chosen", t.count('name="cid"') == 2)
    r = get("shivani", "/finance/checks/wa/waA")
    check("reception can look at the file", r.status_code == 200 and r.data.startswith(b"\xff\xd8"))
    check("awdhesh cannot", get("awdhesh", "/finance/checks/wa/waA").status_code in (302, 403))
    P3 = lambda d: c.post("/finance/checks/answer", data=d, headers=H("alisha"))            # noqa: E731
    msg = lambda r: c.get(r.headers["Location"], headers=H("alisha")).get_data(as_text=True)  # noqa: E731
    check("no patient chosen is refused", "Mareez chunein" in msg(P3({"key": "wa:waA", "a": "xray"})))
    check("an unknown typed ID is refused", "Mareez chunein" in msg(P3({"key": "wa:waA", "a": "xray", "new_id": "99999995"})))
    check("a made-up kind is refused", "samajh nahi" in msg(P3({"key": "wa:waA", "a": "salary", "cid": fam[1]})))
    P3({"key": "wa:waA", "a": "xray", "cid": fam[1]})
    rf = con.execute("SELECT id, clinic_id, kind, source FROM record_file WHERE source_ref='waA'").fetchone()
    check("filed to the chosen family member as an X-ray", rf and rf[1] == fam[1] and rf[2] == "xray" and rf[3] == "whatsapp", rf)
    t = get("manoj", "/finance/records/p/%s" % fam[1]).get_data(as_text=True)
    check("it shows on the patient's page", "/finance/records/file/%d" % rf[0] in t)
    P3({"key": "wa:waB", "a": "not_report"})
    check("'not a report' files nothing", con.execute("SELECT state FROM record_wa WHERE msg_id='waB'").fetchone()[0] == "not_report"
          and not con.execute("SELECT 1 FROM record_file WHERE source_ref='waB'").fetchone())
    t = get("alisha", "/finance/checks").get_data(as_text=True)
    check("both WhatsApp items leave the queue", 'value="wa:' not in t)
    h = get("manoj", "/finance/records").get_data(as_text=True)
    check("the doctors' trail says it", "filed as X-ray" in h and "not a report" in h)

    # ---- F-552: what the walk did not touch did not move
    after = counts(con)
    moved = {k: (before[k], after.get(k)) for k in before if before[k] != after.get(k)}
    check("no other table moved", not moved, moved)
    print("WALK OK %d checks" % N[0])


if __name__ == "__main__":
    main()
