#!/usr/bin/env python3
"""walk_s752.py -- S752_XRAY_CHECK_RETRY walked on a SCRATCH database (a made-up one, or a scratch copy of the live
finance.db): the walk's own day (2001-02-01) and IDs (9092xx), stub Drive folders (RECORDS_DRIVE_STUB). Asserts only about
the rows it made. Prints IDs and counts, never a real name. Covers the cold review's cases (S404): a name-only picture is
filed only once its day is over and only when no other patient of the day shares a word of its name; 'baby of'; a failing
re-try never undoes the run's inbox rows; numbering counts the rows on their way; a folder that could not be read sweeps
nothing; a re-try whose picture left by another road is swept after a day; the ID box comes first (Enter = the ID).
usage: walk_s752.py <dir holding records.py> <scratch db> [--control]
  --control: the same walk against the LIVE records.py must go RED at the first S752 check (prints CONTROL: ...)."""
import datetime as dt
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile

A = [x for x in sys.argv[1:] if not x.startswith("--")]
CONTROL = "--control" in sys.argv
app_dir, dbp = os.path.abspath(A[0]), os.path.abspath(A[1])
assert dbp.startswith("/tmp") or "scratch" in dbp or "walk" in dbp, "refusing a non-scratch database"
N = [0]
S752_FROM = [0]


def check(name, cond, extra=""):
    N[0] += 1
    if not cond:
        if CONTROL and S752_FROM[0]:
            print("CONTROL: red at check %d (%s) -- the live file has no S752 re-try" % (N[0], name))
            sys.exit(0)
        print("WALK RED %d: %s %s" % (N[0], name, extra))
        sys.exit(1)


DAY = "2001-02-01"
stub = tempfile.mkdtemp(prefix="s752stub_")
os.environ["RECORDS_DRIVE_STUB"] = stub
os.environ["FINANCE_CRON_TOKEN"] = "walk-cron-token"
INBOX, TEST, CHECK = "walkINBOX752001", "walkTEST7520001", "walkCHECK752001"


def at(s):
    os.environ["RECORDS_NOW"] = s


def put(fid, files):
    json.dump(files, open(os.path.join(stub, "list_%s.json" % fid), "w"))


def utc(day, hhmm):
    return (dt.datetime.fromisoformat("%sT%s:00" % (day, hhmm)) - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def f(fid, name, hhmm):
    return {"id": fid, "name": name, "mimeType": "image/jpeg", "modifiedTime": utc(DAY, hhmm), "md5Checksum": "m-" + fid}


sys.path.insert(0, app_dir)
spec = importlib.util.spec_from_file_location("records_s752walk", os.path.join(app_dir, "records.py"))
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
rec.ensure(con)
rec.xray_ensure(con)
PEOPLE = {"909201": "RAMKALI DEVI", "909202": "SHYAM SUNDAR GUPTA", "909203": "PREMWATI", "909204": "PREMWATI DEVI",
          "909205": "NASREEN BANO", "909206": "KAMLESH", "909207": "VIJAY PAL", "909208": "RAMESH YADAV", "909209": "NEWONE TEST",
          "909210": "GULSHAN ARA", "909211": "SALIM KHAN", "909212": "SALIM AHMED", "909213": "REKHA DEVI", "909214": "DEEPAK",
          "909215": "KAMLESH DEVI", "909216": "SITA DEVI", "909217": "OM PRAKASH", "909218": "ASLAM BEGUM", "909219": "SHYAM"}
IDS = tuple(PEOPLE)
q = ",".join("?" * len(IDS))


def tidy():
    con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE day=?)", (DAY,))
    con.execute("DELETE FROM slip WHERE day=?", (DAY,))
    con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE day='2001-01-31' AND clinic_id LIKE '9092%')")
    con.execute("DELETE FROM slip WHERE day='2001-01-31' AND clinic_id LIKE '9092%'")
    for t in ("patient_ref", "record_file"):
        con.execute("DELETE FROM %s WHERE clinic_id IN (%s)" % (t, q), IDS)
    con.execute("DELETE FROM record_check WHERE key LIKE 'xf:walk75%' OR key LIKE 'xm:2001-02-01:%'")
    con.execute("DELETE FROM xray_filing WHERE src_id LIKE 'walk75%'")
    con.commit()


tidy()
for cid, nm in PEOPLE.items():
    con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", (cid, nm))
for k, v in (("xray_inbox_id", INBOX), ("xray_test_id", TEST), ("xray_check_id", CHECK), ("xray_live_from", DAY)):
    con.execute("INSERT INTO record_setting(key, value, set_at) VALUES (?,?,'walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
SLIPNO = [952000]


def slip(cid, views, logged="19:30"):
    SLIPNO[0] += 1
    sid = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, name_seen, state, logged_at) VALUES ('xp',?,?,?,?,'ok',?)",
                      (SLIPNO[0], DAY, cid, PEOPLE[cid], "%s %s:00" % (DAY, logged))).lastrowid
    for i, v in enumerate(views):
        con.execute("INSERT INTO slip_item(slip_id, kind, name, side, sort) VALUES (?,'xray',?,'',?)", (sid, v, i))
    con.commit()
    return sid


def st(sid):
    r = rec._rows(con, "SELECT * FROM xray_filing WHERE src_id=?", (sid,))
    return r[0] if r else {}


# --- RUN 1 (17:40): the pictures arrive BEFORE the evening's slips -------------------------------------------------
at("2001-02-01T17:40:00")
for cid, v in (("909202", ["Wrist AP"]), ("909203", ["Knee AP"]), ("909204", ["Knee AP"]), ("909205", ["Hip AP"]),
               ("909206", ["Ankle AP"]), ("909207", ["Spine AP", "Spine Lateral"]), ("909210", ["Knee AP"]),
               ("909211", ["Knee AP"]), ("909212", ["Knee AP"]), ("909213", ["Knee AP"])):
    slip(cid, v, "12:00")
R2DAY = "2001-01-31"                                         # the cold review R2's cases, on the day before (one patient each)
for cid, nm in (("909215", "KAMLESH DEVI"), ("909216", "SITA DEVI"), ("909217", "OM PRAKASH"), ("909218", "ASLAM BEGUM"), ("909219", "SHYAM")):
    SLIPNO[0] += 1
    _s = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, name_seen, state, logged_at) VALUES ('xp',?,?,?,?,'ok',?)",
                     (SLIPNO[0], R2DAY, cid, nm, R2DAY + " 12:00:00")).lastrowid
    con.execute("INSERT INTO slip_item(slip_id, kind, name, side, sort) VALUES (?,'xray','Knee AP','',0)", (_s,))
con.commit()
con.execute("INSERT INTO record_file(clinic_id, kind, day, drive_id, file_name, source, source_ref, added_by, added_at) "
            "VALUES ('909207','xray',?,'walkD752pre0001','pre · 909207 · X-ray 1.jpg','xray_inbox','walk752pre','walk',?)", (DAY, DAY))
con.commit()
INB = [f("walk752F01xxxxx", "RAMKALI 909201.jpg", "16:10"),        # slip comes at 19:30 -> parked
       f("walk752F02xxxxx", "SHYAM SUNDAR.jpg", "16:20"),          # name only -> parked
       f("walk752F03xxxxx", "PREMWATI.jpg", "16:30"),              # name only, two Premwatis -> parked
       f("walk752F04xxxxx", "NASREEN 909025.jpg", "16:40"),        # ID one keystroke (two digits swapped) off 909205 -> parked
       f("walk752F05xxxxx", "KAMLESH KUMAR.jpg", "16:50"),         # name only -> parked; answered 'not an X-ray'
       f("walk752F06xxxxx", "STRANGER PERSONX.jpg", "17:00"),      # nobody -> parked
       f("walk752F07xxxxx", "VIJAY PAL.jpg", "17:05"),             # name only, 909207 already has one picture -> parked
       f("walk752F08xxxxx", "RAMESH 909208.jpg", "17:10"),         # slip later, then cancelled
       f("walk752F11xxxxx", "GULSHAN.jpg", "17:15"),               # one word vs a two-word name: words only, never filed
       f("walk752F12xxxxx", "SALIM.jpg", "17:20"),                 # SALIM KHAN and SALIM AHMED that day: never filed
       f("walk752F13xxxxx", "BABY OF REKHA.jpg", "17:25"),         # a child's picture: never filed by name
       f("walk752F14xxxxx", "DEEPAK 909214 b.jpg", "17:30")]       # slip later; its first picture comes by the inbox
R2 = [dict(f("walk752R%dxxxxxx" % i, n, "11:00"), modifiedTime=utc("2001-01-31", "11:00"))
      for i, n in enumerate(("KAMLESH KUMAR.jpg", "SITA RAM.jpg", "MOHD ASLAM.jpg", "RAM PRAKASH.jpg", "SHYAM LAL.jpg"), 1)]
INB = INB + R2
put(INBOX, INB)
put(TEST, [])
put(CHECK, [])
items, notes = rec.xray_actions(con)
check("run 1: all seventeen parked (no slip yet / no ID)", len(items) == 17 and all(i["action"] == "check" for i in items), json.dumps(items)[:400])
rec.xray_done(con, [{"id": i["id"], "action": "check"} for i in items])
check("run 1: seventeen rows in state check", len(rec._rows(con, "SELECT 1 FROM xray_filing WHERE src_id LIKE 'walk752%' AND state='check'")) == 17)
# the mailbox moved them to the check folder; the evening's slips come in; one picture answered 'not an X-ray'
put(INBOX, [f("walk752F09xxxxx", "NEWONE 909209.jpg", "18:00"), f("walk752F15xxxxx", "DEEPAK 909214.jpg", "17:29")])
put(CHECK, INB)
slip("909201", ["Knee AP"])
slip("909209", ["Chest PA"], "17:55")
slip("909214", ["Knee AP"], "19:35")
s208 = slip("909208", ["Elbow AP"])
con.execute("INSERT INTO record_check(key, kind, clinic_id, answer, note, answered_by, answered_at) VALUES "
            "('xf:walk752F05xxxxx','xray_file','','not_xray','','walk',?)", (DAY + " 18:10:00",))
con.commit()

# --- RUN 2 (20:00 the same day, after the slips) ----------------------------------------------------------------
at("2001-02-01T20:00:00")
S752_FROM[0] = 1
items, notes = rec.xray_actions(con)
by = {i["id"]: i for i in items}
check("run 2: the inbox pictures are filed as before (NEWONE 909209 Chest PA; DEEPAK 909214 Knee AP)",
      by.get("walk752F09xxxxx", {}).get("action") == "file" and "Chest PA" in by["walk752F09xxxxx"]["name"]
      and "Knee AP" in by.get("walk752F15xxxxx", {}).get("name", ""), json.dumps(items)[:300])
check("run 2: RAMKALI 909201 -- parked before its slip -- now filed under 909201 with its study",
      by.get("walk752F01xxxxx", {}).get("action") == "file" and "909201" in by["walk752F01xxxxx"]["name"]
      and "Knee AP" in by["walk752F01xxxxx"]["name"] and by["walk752F01xxxxx"]["path"] == ["X-ray", "Feb 2001", "01-Feb"], json.dumps(items)[:400])
check("run 2: RAMESH 909208 filed (its slip came)", by.get("walk752F08xxxxx", {}).get("action") == "file" and "909208" in by["walk752F08xxxxx"]["name"])
check("run 2: DEEPAK's parked second picture numbered past the inbox one on its way -- two different names",
      by.get("walk752F14xxxxx", {}).get("action") == "file" and "909214" in by["walk752F14xxxxx"]["name"]
      and by["walk752F14xxxxx"]["name"] != by["walk752F15xxxxx"]["name"] and "X-ray 2" in by["walk752F14xxxxx"]["name"],
      json.dumps([by.get("walk752F14xxxxx"), by.get("walk752F15xxxxx")]))
check("run 2: name-only pictures wait while the day is not over (SHYAM SUNDAR, VIJAY PAL)",
      "walk752F02xxxxx" not in by and "walk752F07xxxxx" not in by)
check("run 2: nothing else filed", sorted(by) == sorted(["walk752F01xxxxx", "walk752F08xxxxx", "walk752F09xxxxx", "walk752F14xxxxx", "walk752F15xxxxx"]), str(sorted(by)))
# --- RUN 3: the next morning -- the day is over -----------------------------------------------------------------
at("2001-02-02T10:00:00")
items, notes = rec.xray_actions(con)
by = {i["id"]: i for i in items}
check("run 3: SHYAM SUNDAR (no ID) filed under the day's one Shyam Sundar 909202",
      by.get("walk752F02xxxxx", {}).get("action") == "file" and "909202" in by["walk752F02xxxxx"]["name"], json.dumps(items)[:400])
check("run 3: VIJAY PAL (no ID) filed under 909207 as its second picture",
      by.get("walk752F07xxxxx", {}).get("action") == "file" and "909207" in by["walk752F07xxxxx"]["name"]
      and "X-ray 2" in by["walk752F07xxxxx"]["name"], json.dumps(by.get("walk752F07xxxxx")))
check("run 3: PREMWATI (two Premwatis) NOT filed", "walk752F03xxxxx" not in by)
check("run 3: NASREEN 909025 (one keystroke off) NOT filed by itself", "walk752F04xxxxx" not in by)
check("run 3: KAMLESH (answered 'not an X-ray') NOT touched", "walk752F05xxxxx" not in by)
check("run 3: STRANGER NOT filed", "walk752F06xxxxx" not in by)
check("run 3: GULSHAN (one word against GULSHAN ARA) NOT filed", "walk752F11xxxxx" not in by)
check("run 3: SALIM (SALIM KHAN and SALIM AHMED that day) NOT filed", "walk752F12xxxxx" not in by)
check("run 3: BABY OF REKHA (a child's picture) NOT filed on REKHA DEVI", "walk752F13xxxxx" not in by)
check("run 3 (R2): KAMLESH KUMAR / SITA RAM / MOHD ASLAM / RAM PRAKASH / SHYAM LAL NOT filed on the day's Kamlesh Devi / Sita Devi / "
      "Aslam Begum / Om Prakash / Shyam", not any(("walk752R%dxxxxxx" % i) in by for i in range(1, 6)), str(sorted(by)))
check("run 3: the earlier re-tries come again with the same names (the mailbox had not reported)",
      all(by.get(k, {}).get("name") for k in ("walk752F01xxxxx", "walk752F08xxxxx", "walk752F14xxxxx")))
check("run 3: the re-tried rows are planned with an S752 verdict", all(st(k)["state"] == "planned" and st(k)["verdict"].startswith("S752")
      for k in ("walk752F01xxxxx", "walk752F02xxxxx", "walk752F07xxxxx", "walk752F08xxxxx")))
check("run 3: the others still in the check list", all(st(k)["state"] == "check" for k in
      ("walk752F03xxxxx", "walk752F04xxxxx", "walk752F05xxxxx", "walk752F06xxxxx", "walk752F11xxxxx", "walk752F12xxxxx", "walk752F13xxxxx")))
names3 = {k: by[k]["name"] for k in by}
# --- 909208's slip cancelled before the mailbox filed it -> back to the check list ---------------------------------
con.execute("UPDATE slip SET state='cancelled' WHERE id=?", (s208,))
con.commit()
items4, _ = rec.xray_actions(con)
by4 = {i["id"]: i for i in items4}
r8 = st("walk752F08xxxxx")
check("run 4: a re-try that no longer places goes back to the check list", "walk752F08xxxxx" not in by4 and r8["state"] == "check"
      and r8["clinic_id"] == "909208", json.dumps(r8))
check("run 4: the same names again (stable)", all(by4.get(k, {}).get("name") == names3[k] for k in ("walk752F01xxxxx", "walk752F02xxxxx", "walk752F07xxxxx")))
# --- the mailbox files them --------------------------------------------------------------------------------------
done = [{"id": k, "action": "file", "dest_id": "walkD" + k[7:], "name": by4[k]["name"]}
        for k in ("walk752F01xxxxx", "walk752F02xxxxx", "walk752F07xxxxx", "walk752F14xxxxx")]
done += [{"id": "walk752F09xxxxx", "action": "file", "dest_id": "walkD752F09xxx", "name": "n9.jpg"},
         {"id": "walk752F15xxxxx", "action": "file", "dest_id": "walkD752F15xxx", "name": "n15.jpg"}]
check("done: six stored", rec.xray_done(con, done) == 6)
put(INBOX, [])
LEFT = [x for x in INB if x["id"] not in ("walk752F01xxxxx", "walk752F02xxxxx", "walk752F07xxxxx", "walk752F14xxxxx")]
put(CHECK, LEFT)
items5, _ = rec.xray_actions(con)
check("run 5: nothing more filed by itself", [i for i in items5 if i["action"] == "file"] == [], json.dumps(items5)[:300])
check("run 5: 909201, 909202 have one picture; 909207 and 909214 two",
      [rec._rows(con, "SELECT COUNT(*) n FROM record_file WHERE kind='xray' AND clinic_id=? AND day=?", (c, DAY))[0]["n"]
       for c in ("909201", "909202", "909207", "909214")] == [1, 1, 2, 2])
# --- Check karein: the suggestions --------------------------------------------------------------------------------
ck = {i["key"]: i for i in rec.check_items(con) if i["key"].startswith(("xf:walk752", "xm:%s:" % DAY))}
check("Check karein: NASREEN 909025 -> 909205 in the box (one keystroke off)", ck.get("xf:walk752F04xxxxx", {}).get("suggest") == "909205",
      json.dumps(ck.get("xf:walk752F04xxxxx")))
check("Check karein: GULSHAN -> 909210 in words only (a loose match is never in the box)",
      "suggest" not in ck.get("xf:walk752F11xxxxx", {"suggest": 1}) and "909210" in ck.get("xf:walk752F11xxxxx", {}).get("why", ""))
check("Check karein: BABY OF REKHA -> never in the box", "suggest" not in ck.get("xf:walk752F13xxxxx", {"suggest": 1}))
check("Check karein: SALIM (two Salims) and PREMWATI (two) have no suggestion",
      "suggest" not in ck.get("xf:walk752F12xxxxx", {"suggest": 1}) and "Shayad" not in ck.get("xf:walk752F12xxxxx", {}).get("why", "")
      and "suggest" not in ck.get("xf:walk752F03xxxxx", {"suggest": 1}))
check("Check karein (R2): none of the five is pre-filled", all("suggest" not in ck.get("xf:walk752R%dxxxxxx" % i, {"suggest": 1})
      for i in range(1, 6)), json.dumps([ck.get("xf:walk752R%dxxxxxx" % i) for i in range(1, 6)])[:400])
check("Check karein: STRANGER has no suggestion", "suggest" not in ck.get("xf:walk752F06xxxxx", {"suggest": 1}))
check("Check karein: KAMLESH (answered) is closed", "xf:walk752F05xxxxx" not in ck)
check("Check karein: 909201 / 909202 / 909207 / 909214 not asked as missing", not any(k.endswith(("909201", "909202", "909207", "909214")) for k in ck))
from flask import Flask  # noqa: E402
app = Flask("walk752")


def dbg():
    c = sqlite3.connect(dbp)
    c.row_factory = sqlite3.Row
    return c


def req(*roles, **kw):
    return ({"user": "alisha", "roles": ["maker"]}, None)


rec.init(app, dbg, req)
c = app.test_client()
page = c.get("/finance/checks").get_data(as_text=True)
check("screen: the suggestion is in the box (one tap)", 'value="909205"' in page and "Shayad ID 909205" in page)
check("screen: an item with no suggestion has an empty box", 'maxlength="8" value="">' in page)
frm = page[page.find("xf:walk752F04xxxxx"):]
frm = frm[:frm.find("</form>")]
check("screen: the ID button comes before 'Yeh X-ray nahi' (Enter in the box = the ID)",
      0 <= frm.find('value="id_fixed"') < frm.find('value="not_xray"'), frm[:300])
r = c.post("/finance/checks/answer", data={"key": "xf:walk752F04xxxxx", "a": "id_fixed", "new_id": "909205"})
check("screen: the one tap is accepted", r.status_code == 303 and "Ho" in (r.headers.get("Location") or ""))
items6, _ = rec.xray_actions(con)
by6 = {i["id"]: i for i in items6}
check("run 6: the answered picture is filed under 909205 (the S373 road)", by6.get("walk752F04xxxxx", {}).get("action") == "file"
      and "909205" in by6["walk752F04xxxxx"]["name"], json.dumps(items6)[:300])
# --- a failing re-try never stops, and never undoes, the inbox's work --------------------------------------------
real = rec._s752_retry


def boom(*a, **k):
    con.execute("UPDATE xray_filing SET verdict='half-work' WHERE src_id='walk752F06xxxxx'")
    raise RuntimeError("walk")


rec._s752_retry = boom
put(INBOX, [f("walk752F10xxxxx", "NEWONE 909209 b.jpg", "18:05")])
items7, notes7 = rec.xray_actions(con)
rec._s752_retry = real
check("a failing re-try: the inbox still files, and a note says so", any(i["id"] == "walk752F10xxxxx" for i in items7)
      and any("S752 re-try skipped" in n for n in notes7), json.dumps([items7, notes7])[:300])
check("a failing re-try: the inbox row is KEPT and the mailbox's report is stored",
      st("walk752F10xxxxx").get("state") == "planned"
      and rec.xray_done(con, [{"id": "walk752F10xxxxx", "action": "file", "dest_id": "walkD752F10xxx", "name": "x.jpg"}]) == 1)
check("a failing re-try: its own half-work is rolled back", st("walk752F06xxxxx").get("verdict") != "half-work")
put(INBOX, [])
# --- a check folder that could not be read sweeps nothing ----------------------------------------------------------
real_list = rec.drive_list
rec.drive_list = lambda fid: (None, "walk: Drive did not answer") if fid == CHECK else real_list(fid)
rec.xray_actions(con)
rec.drive_list = real_list
check("an unreadable check folder: no parked picture marked gone", all(st(k)["state"] == "check"
      for k in ("walk752F03xxxxx", "walk752F06xxxxx", "walk752F11xxxxx", "walk752F12xxxxx", "walk752F13xxxxx")))
# --- a re-try whose picture left the folder by another road is swept after a day -----------------------------------
at("2001-02-02T11:00:00")
slip("909208", ["Elbow AP"])
items8, _ = rec.xray_actions(con)
check("RAMESH re-planned (a new slip)", any(i["id"] == "walk752F08xxxxx" for i in items8) and st("walk752F08xxxxx")["state"] == "planned")
put(CHECK, [x for x in LEFT if x["id"] != "walk752F08xxxxx"])
rec.xray_actions(con)
check("left the folder an hour ago: still planned (the mailbox may report late)", st("walk752F08xxxxx")["state"] == "planned")
at("2001-02-03T12:00:00")
rec.xray_actions(con)
check("left the folder over a day ago: swept to gone", st("walk752F08xxxxx")["state"] == "gone")
# the helpers
check("one keystroke: swap / change / drop / add", rec._s752_one_off("3812", "3821") and rec._s752_one_off("4071", "4971")
      and rec._s752_one_off("306", "3056") and rec._s752_one_off("8559", "8359") and not rec._s752_one_off("8291", "8282")
      and not rec._s752_one_off("1234", "1234"))
check("names: whole words only", rec._s752_name_match(["sunita"], ["sunita"]) and not rec._s752_name_match(["sunita"], ["sunita", "verma"])
      and rec._s752_name_match(["shyam", "sundar"], ["shyam", "sundar", "gupta"]) and not rec._s752_name_match(["mohan"], ["mohanlal"])
      and not rec._s752_name_match(["pushpa"], ["pushpendra"]) and not rec._s752_name_match(["rajesh"], ["rajeshwari"]))
check("names (R2): the name-part words count when filing", not rec._s752_name_match(rec._s752_strict_tokens("KAMLESH KUMAR"), rec._s752_strict_tokens("KAMLESH DEVI"))
      and not rec._s752_name_match(rec._s752_strict_tokens("RAM PRAKASH"), rec._s752_strict_tokens("OM PRAKASH"))
      and rec._s752_name_match(rec._s752_strict_tokens("SHYAM SUNDAR.jpg"), rec._s752_strict_tokens("SHYAM SUNDAR GUPTA")))
check("names: a child's picture", rec._s752_child("BABY OF REKHA") and rec._s752_child("MASTER AMAN") and not rec._s752_child("REKHA DEVI"))
tidy()
if CONTROL:
    print("CONTROL: NOT red -- the walk passed on the file given as the live one")
    sys.exit(1)
print("WALK OK %d/%d" % (N[0], N[0]))
