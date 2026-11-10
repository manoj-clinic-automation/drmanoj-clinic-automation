#!/usr/bin/env python3
"""walk_s776.py -- S776_XRAY_FEWER_LEFT walked on a SCRATCH database: own days (2001-04..) and IDs (9xxxxx, apart by two digits or more unless a neighbour is meant), stub Drive.
Each case is a picture re-added on 20-Apr whose film was read (xray_filmdate) for an X-ray of 10-Apr.
  W1 R1  no ID on the file; the film's ID; the name shares a whole word; no neighbour ID that day      -> filed to the film's ID
  W2     the same, but another X-ray patient that day has an ID one keystroke off                       -> stays
  W3 R2  no ID anywhere; ONE X-ray patient of the day shares a whole word; his photo missing             -> filed to him
  W4     the one match already has his photo                                                             -> stays
  W5     two X-ray patients that day share a word                                                        -> stays
  W6 R3  the film's ID came that day (OPD slip) with no X-ray billed; a whole word shared                -> filed to him
  W7 R3  no ID on the film; the name word for word ONE patient who came that day, no X-ray billed        -> filed to him
  W8     a child's picture                                                                               -> stays
  W9     the film not read yet                                                                           -> stays
  W10    the file's ID a keystroke off ONE X-ray patient whose first name it has                         -> filed to him
  W11    the file's ID IS another X-ray patient of the film's day                                        -> stays (never the file's ID)
  W12    prefix only (SUNITA / SUNIL): no whole word                                                     -> stays
usage: walk_s776.py <dir holding records.py> <scratch db> [--control]"""
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


def check(name, cond, extra=""):
    N[0] += 1
    if not cond:
        if CONTROL:
            print("CONTROL: red at check %d (%s) -- the live file has no S776 rules" % (N[0], name))
            sys.exit(0)
        print("WALK RED %d: %s %s" % (N[0], name, extra))
        sys.exit(1)


stub = tempfile.mkdtemp(prefix="s776stub_")
os.environ["RECORDS_DRIVE_STUB"] = stub
os.environ["FINANCE_CRON_TOKEN"] = "walk-cron-token"
INBOX, TEST, CHECK = "walkINBOX775001", "walkTEST7750001", "walkCHECK775001"
READD, D = "2001-04-20", "2001-04-10"
sys.path.insert(0, app_dir)
spec = importlib.util.spec_from_file_location("records_s776walk", os.path.join(app_dir, "records.py"))
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
rec.ensure(con)
rec.xray_ensure(con)
con.execute("CREATE TABLE IF NOT EXISTS xray_filmdate(src_id TEXT PRIMARY KEY, dates TEXT NOT NULL DEFAULT '[]', ids TEXT NOT NULL DEFAULT '[]', "
            "how TEXT NOT NULL DEFAULT '', secs REAL NOT NULL DEFAULT 0, read_at TEXT NOT NULL DEFAULT '')")
P = {"978787": "DINESH SHARMA", "989898": "PRIYA SHARMA", "913131": "SUNIL YADAV", "911111": "OMI KAUR", "922222": "BHOLA NATH", "933333": "PRIYA VERMA", "933343": "ZORAWAR KHAN", "944444": "RAKESH KUMAR",
     "955555": "MOHAN LAL", "966666": "NIRMALA DEVI", "977777": "GITA RANI", "988888": "HARI OM GUPTA", "999999": "SURESH CHAND",
     "912121": "KAMAL NAYAN", "923232": "VIMLA SHARMA", "934343": "SUNIL KUMAR", "945454": "JAYA PRADA", "956565": "JAYA LAKSHMI",
     "967676": "TARUN BOSE"}
IDS = tuple(P)
q = ",".join("?" * len(IDS))


def tidy():
    con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE clinic_id IN (%s))" % q, IDS)
    con.execute("DELETE FROM slip WHERE clinic_id IN (%s)" % q, IDS)
    for t in ("patient_ref", "record_file"):
        con.execute("DELETE FROM %s WHERE clinic_id IN (%s)" % (t, q), IDS)
    con.execute("DELETE FROM xray_filing WHERE src_id LIKE 'walk776%'")
    con.execute("DELETE FROM xray_filmdate WHERE src_id LIKE 'walk776%'")
    con.commit()


tidy()
for cid, nm in P.items():
    con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", (cid, nm))
for k, v in (("xray_inbox_id", INBOX), ("xray_test_id", TEST), ("xray_check_id", CHECK), ("xray_live_from", "2001-04-01")):
    con.execute("INSERT INTO record_setting(key, value, set_at) VALUES (?,?,'walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
NO = [954000]


def slip(cid, series="xp"):
    NO[0] += 1
    sid = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, name_seen, state, logged_at) VALUES (?,?,?,?,?,'ok',?)",
                      (series, NO[0], D, cid, P[cid], D + " 12:00:00")).lastrowid
    if series == "xp":
        con.execute("INSERT INTO slip_item(slip_id, kind, name, side, sort) VALUES (?,'xray','Knee AP','',0)", (sid,))


for c in ("989898", "913131", "911111", "922222", "933333", "933343", "944444", "955555", "966666", "999999", "912121", "923232", "934343", "945454", "956565"):
    slip(c)
for c in ("977777", "988888"):
    slip(c, "opd")                                   # came that day, no X-ray billed
con.execute("INSERT INTO record_file(clinic_id, kind, day, drive_id, file_name, source, source_ref, added_by, added_at, state) "
            "VALUES ('966666','xray',?,'walkD775nirmala','x.jpg','xray_inbox','walk776Snirm','walk',?,'ok')", (D, D))
con.commit()
PARK = [("walk776W01", "OMI SANDHU ..jpg", [D], ["911111"]),
        ("walk776W02", "PRIYA SAINI ..jpg", [D], ["933333"]),
        ("walk776W03", "RAKESH ..jpg", [D], []),
        ("walk776W04", "NIRMALA ..jpg", [D], []),
        ("walk776W05", "JAYA ..jpg", [D], []),
        ("walk776W06", "GITA ..jpg", [D], ["977777"]),
        ("walk776W07", "HARI OM GUPTA ..jpg", [D], []),
        ("walk776W08", "BABY OF RAKESH ..jpg", [D], []),
        ("walk776W09", "MOHAN ..jpg", None, None),
        ("walk776W10", "SURESH 999989.jpg", [D], []),
        ("walk776W11", "KAMAL 923232.jpg", [D], []),
        ("walk776W12", "SUNITA ..jpg", [D], []),
        ("walk776W13", "DINESH SHARMA 978787.jpg", [D], []),     # the reviewer's case: the file's ID is DINESH SHARMA (no slip)
        ("walk776W14", "ANIL YADAV ..jpg", [D], []),             # a surname alone shared with SUNIL YADAV
        ("walk776W15", "RAKESH ..jpg", [], [])]                  # no date read on the film
for sid, name, ds, ids in PARK:
    con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, clinic_id, day, state, verdict, planned_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (sid, name, READD + " 18:00:00", "check", rec.xray_id(name)[0], READD, "check", "parked", READD + " 19:25:00"))
    if ds is not None:
        con.execute("INSERT INTO xray_filmdate(src_id, dates, ids, how) VALUES (?,?,?,'walk')", (sid, json.dumps(ds), json.dumps(ids)))
con.commit()
utc = (dt.datetime.fromisoformat(READD + "T18:00:00") - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
for fid in (INBOX, TEST):
    json.dump([], open(os.path.join(stub, "list_%s.json" % fid), "w"))
json.dump([{"id": s, "name": n, "mimeType": "image/jpeg", "modifiedTime": utc, "md5Checksum": "m" + s} for s, n, _, _ in PARK],
          open(os.path.join(stub, "list_%s.json" % CHECK), "w"))
os.environ["RECORDS_NOW"] = READD + "T20:25:00"
items, notes = rec.xray_actions(con)
it = {i["id"]: i for i in items}


def st(sid):
    r = rec._rows(con, "SELECT * FROM xray_filing WHERE src_id=?", (sid,))
    return r[0] if r else {}


def filed_to(sid, cid):
    r = st(sid)
    return r.get("state") == "planned" and r.get("action") == "file" and r.get("clinic_id") == cid and r.get("day") == D and sid in it


def stays(sid):
    return st(sid).get("state") == "check" and sid not in it


check("the re-try ran without an error", not notes, str(notes))
check("W1 R1: the film's ID, a whole word shared, no neighbour -> filed to it", filed_to("walk776W01", "911111"), str(st("walk776W01")))
check("W2: a neighbour ID that day -> stays", stays("walk776W02"), str(st("walk776W02")))
check("W3 R2: one X-ray patient shares a word, photo missing -> filed", filed_to("walk776W03", "944444"), str(st("walk776W03")))
check("W3: the reason says so", "S776" in (st("walk776W03").get("verdict") or ""))
check("W4: the one match already has his photo -> stays", stays("walk776W04"))
check("W5: two share a word -> stays", stays("walk776W05"))
check("W6 R3: the film's ID came that day, no X-ray billed -> filed", filed_to("walk776W06", "977777"), str(st("walk776W06")))
check("W7 R3: the name word for word one visitor -> filed", filed_to("walk776W07", "988888"), str(st("walk776W07")))
check("W8: a child's picture -> stays", stays("walk776W08"))
check("W9: the film not read -> stays", stays("walk776W09"))
check("W10: a typo ID, one X-ray patient shares a word -> filed to him", filed_to("walk776W10", "999999"), str(st("walk776W10")))
check("W11: the file's ID is another X-ray patient that day -> stays", stays("walk776W11"), str(st("walk776W11")))
check("W12: SUNITA / SUNIL -- a prefix only -> stays", stays("walk776W12"))
check("W13: the file's ID is another patient (no slip); a shared surname with an X-ray patient -> stays", stays("walk776W13"), str(st("walk776W13")))
check("W14: a surname alone shared -> stays", stays("walk776W14"))
check("W15: no date read on the film -> R2 never runs", stays("walk776W15"))
tidy()
print("WALK OK %d/%d -- S776: fewer pictures left for a person" % (N[0], N[0]))
