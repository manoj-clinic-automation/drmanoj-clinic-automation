#!/usr/bin/env python3
"""walk_s772.py -- S772_XRAY_FILM_DATE walked on a SCRATCH database (a made-up one, or a scratch copy of the live finance.db):
the walk's own days (2001-03..) and IDs (9093xx), stub Drive folders (RECORDS_DRIVE_STUB). Asserts only about the rows it made.
The 09-Nov case in small: pictures re-added on a later day (their file time that day) for X-rays taken days before.
  A  ID, one open X-ray day, no film date            -> filed on that day (the ID rule); its older wrong-ID parked copy -> dup
  B  ID, two open days, no film date                 -> stays; with the film's date on one of them -> filed on that day
  C  two views re-added; two older no-ID copies       -> both filed (K/S two films); both older copies -> dup
  D  first upload filed to another patient (mistyped) -> corrected copy filed; the wrong copy hidden + dup
  E  the film's date is none of the ID's X-ray days    -> stays for a person
  F  no ID, the film's date, one name match that day  -> filed by name on the film's date
  G  guards: another patient's parked picture of the same name with ITS ID on the list -> untouched;
     the wrongly-filed patient shares a word of the name -> untouched; more old copies than corrected ones -> none moved
  H  the mailbox reports: 'file' rows done, 'dup' rows dup; a dup not yet reported is offered again next run
usage: walk_s772.py <dir holding records.py> <scratch db> [--control]
  --control: the same walk against the LIVE records.py must go RED at the first S772 check (prints CONTROL: ...)."""
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
            print("CONTROL: red at check %d (%s) -- the live file has no S772 day" % (N[0], name))
            sys.exit(0)
        print("WALK RED %d: %s %s" % (N[0], name, extra))
        sys.exit(1)


stub = tempfile.mkdtemp(prefix="s772stub_")
os.environ["RECORDS_DRIVE_STUB"] = stub
os.environ["FINANCE_CRON_TOKEN"] = "walk-cron-token"
INBOX, TEST, CHECK = "walkINBOX771001", "walkTEST7710001", "walkCHECK771001"
READD = "2001-03-01"


def put(fid, files):
    json.dump(files, open(os.path.join(stub, "list_%s.json" % fid), "w"))


def utc(day, hhmm):
    return (dt.datetime.fromisoformat("%sT%s:00" % (day, hhmm)) - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


sys.path.insert(0, app_dir)
spec = importlib.util.spec_from_file_location("records_s772walk", os.path.join(app_dir, "records.py"))
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
rec.ensure(con)
rec.xray_ensure(con)
con.execute("CREATE TABLE IF NOT EXISTS xray_filmdate(src_id TEXT PRIMARY KEY, dates TEXT, ids TEXT, how TEXT, read_at TEXT)")
PEOPLE = {"909301": "ALPHA KUMAR", "909302": "BETA DEVI", "909303": "GAMMA SINGH", "909304": "DELTA RANI", "909305": "EPSILON PAL",
          "909306": "ZETA LAL", "909307": "ETA BANO", "909308": "THETA DEVI", "909309": "THETA KUMARI", "909310": "IOTA PRASAD",
          "909311": "KAPPA NATH", "909312": "LAMBDA SHAH", "909313": "LAMBDA KHAN", "909314": "MU RANI", "909315": "NU DEVI",
          "909316": "XI LAL", "909317": "RHO VERMA", "909318": "NU KHAN", "909319": "OMEGA RAJ", "909320": "SUNIL KUMAR",
          "909321": "SIGMA DEVI", "909322": "CHI NATH", "909323": "TAU SEN", "909324": "PSI GOEL", "909325": "PHI RAJ",
          "909326": "VARUN SOOD"}
IDS = tuple(PEOPLE)
q = ",".join("?" * len(IDS))


def tidy():
    con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE clinic_id IN (%s))" % q, IDS)
    con.execute("DELETE FROM slip WHERE clinic_id IN (%s)" % q, IDS)
    for t in ("patient_ref", "record_file"):
        con.execute("DELETE FROM %s WHERE clinic_id IN (%s)" % (t, q), IDS)
    con.execute("DELETE FROM xray_filing WHERE src_id LIKE 'walk771%' OR src_id LIKE 'walkD771%'")
    con.execute("DELETE FROM xray_filmdate WHERE src_id LIKE 'walk771%'")
    con.execute("DELETE FROM record_check WHERE key LIKE 'xf:walk771%'")
    con.commit()


tidy()
for cid, nm in PEOPLE.items():
    con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", (cid, nm))
for k, v in (("xray_inbox_id", INBOX), ("xray_test_id", TEST), ("xray_check_id", CHECK), ("xray_live_from", "2001-02-01")):
    con.execute("INSERT INTO record_setting(key, value, set_at) VALUES (?,?,'walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
SLIPNO = [953000]


def slip(cid, day, views=("Knee AP",)):
    SLIPNO[0] += 1
    sid = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, name_seen, state, logged_at) VALUES ('xp',?,?,?,?,'ok',?)",
                      (SLIPNO[0], day, cid, PEOPLE[cid], day + " 12:00:00")).lastrowid
    for i, v in enumerate(views):
        con.execute("INSERT INTO slip_item(slip_id, kind, name, side, sort) VALUES (?,'xray',?,'',?)", (sid, v, i))


slip("909301", "2001-02-10")
slip("909302", "2001-02-12")
slip("909302", "2001-02-14")
slip("909303", "2001-02-15", ("Knee studies (K/S)",))
slip("909304", "2001-02-20")
slip("909305", "2001-02-20")
slip("909306", "2001-02-22")
slip("909307", "2001-02-25")
slip("909308", "2001-02-21")
slip("909309", "2001-02-21")
slip("909310", "2001-02-26")
slip("909311", "2001-02-23")
slip("909312", "2001-02-24")
slip("909313", "2001-02-24")
slip("909314", "2001-02-18")          # M: the slip a day after the film's date
for _c in ("909315", "909316", "909317", "909318", "909320"):
    slip(_c, "2001-02-19")
slip("909319", "2001-02-05")          # R: OMEGA RAJ's open day -- a mistyped 909319 on SIGMA DEVI's picture must never land here
slip("909321", "2001-02-28")
slip("909322", "2001-02-27")          # T: CHI NATH; TAU SEN that day has ONE photo for ONE film (copy-pasted name?) -> never voided
slip("909323", "2001-02-27")
slip("909324", "2001-02-16")          # U: PSI GOEL, film not read yet -> waits
slip("909325", "2001-02-20")          # V: PHI RAJ and VARUN SOOD both X-rayed 20-Feb; "VARUN SOOD 909325.jpg" (mistyped), film 909326
slip("909326", "2001-02-20")
con.commit()


def filed(cid, day, fid, orig, src):
    """A picture filed before S772 (the mailbox's 'done' row and its record)."""
    r = con.execute("INSERT INTO record_file(clinic_id, kind, day, drive_id, file_name, source, source_ref, added_by, added_at, state) "
                    "VALUES (?,?,?,?,?,?,?,?,?,'ok')", (cid, "xray", day, fid, "%s · %s · X-ray 1.jpg" % (day, cid), "xray_inbox", src,
                                                       "walk", day)).lastrowid
    con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, clinic_id, day, new_name, dest_id, file_id, state, verdict, "
                "planned_at, done_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (src, orig, day + " 11:00:00", "file", cid, day, "x", fid, r, "done", "matched", day + " 17:40:00", day + " 17:41:00"))


filed("909305", "2001-02-20", "walkD771own05xx", "EPSILON PAL 909305.jpg", "walk771S05own")        # D: the patient's own picture
filed("909305", "2001-02-20", "walkD771wrong04", "DELTA RANI 909305.jpg", "walk771S04wrong")       # D: a mistyped ID, filed to 909305
filed("909309", "2001-02-21", "walkD771th09xxx", "THETA DEVI 909309.jpg", "walk771S09th")          # G: filed to THETA KUMARI (shares 'theta')
filed("909323", "2001-02-27", "walkD771tau23xx", "CHI NATH 909323.jpg", "walk771S23tau")           # T: TAU SEN's only photo, a CHI NATH name
con.commit()

# the check folder: (id, name, first seen day, hh:mm)
PARK = [("walk771A1new", "ALPHA KUMAR 909301.jpg", READD, "18:10"),      # A re-added
        ("walk771A0old", "ALPHA KUMAR 909391.jpg", "2001-02-10", "11:00"),  # A first upload, wrong ID (not on the list)
        ("walk771B1new", "BETA DEVI 909302.jpg", READD, "18:12"),        # B
        ("walk771C1new", "GAMMA SINGH 909303.jpg", READD, "18:14"),      # C view 1
        ("walk771C2new", "GAMMA SINGH 909303 ..jpg", READD, "18:15"),    # C view 2
        ("walk771C1old", "GAMMA SINGH ..jpg", "2001-02-14", "17:00"),    # C first uploads, no ID
        ("walk771C2old", "GAMMA SINGH ...jpg", "2001-02-14", "17:01"),
        ("walk771D1new", "DELTA RANI 909304.jpg", READD, "18:16"),       # D corrected copy
        ("walk771E1new", "ETA BANO 909307.jpg", READD, "18:18"),         # E film date conflicts
        ("walk771F1new", "IOTA PRASAD ..jpg", READD, "18:20"),           # F no ID, film date 26-Feb
        ("walk771G1new", "ZETA LAL 909306.jpg", READD, "18:22"),         # G corrected copy for 909306 (one open day)
        ("walk771G1oth", "ZETA LAL 909311.jpg", "2001-02-22", "11:00"),  # G: same name, ITS ID 909311 is an X-ray patient of 22-Feb? no -> see below
        ("walk771H1new", "THETA DEVI 909308.jpg", READD, "18:24"),       # G: the wrongly-filed patient shares a word -> untouched
        ("walk771K1new", "LAMBDA SHAH 909312.jpg", READD, "18:26"),      # G: one corrected copy, two old copies -> none moved
        ("walk771K1old", "LAMBDA SHAH ..jpg", "2001-02-24", "11:00"),
        ("walk771K2old", "LAMBDA SHAH ...jpg", "2001-02-24", "11:05"),
        ("walk771M1new", "MU RANI 909314.jpg", READD, "18:28"),          # M: film 17-Feb, slip 18-Feb -> 18-Feb
        ("walk771N1old", "NU DEVI ..jpg", "2001-02-19", "11:00"),        # N: no ID; NU KHAN that day too; the film prints 909315
        ("walk771O1old", "XI LAL 909399.jpg", "2001-02-19", "11:10"),    # O: a mistyped ID; the film prints 909316
        ("walk771P1old", "PI SHARMA ..jpg", "2001-02-19", "11:20"),      # P: the film's ID is RHO VERMA's -- no word shared
        ("walk771R1new", "SIGMA DEVI 909319.jpg", READD, "18:30"),       # R: mistyped ID (OMEGA RAJ's), no film date -> stays
        ("walk771S1old", "SUNITA ..jpg", "2001-02-19", "11:30"),         # S: the film's ID misread as SUNIL KUMAR's -> stays (strict)
        ("walk771T1new", "CHI NATH 909322.jpg", READD, "18:32"),         # T
        ("walk771U1new", "PSI GOEL 909324.jpg", READD, "18:34"),         # U: no film row yet
        ("walk771V1new", "VARUN SOOD 909325.jpg", READD, "18:36")]       # V: the file's ID is another X-ray patient of the film's day
slip("909311", "2001-02-22")          # G: 909311 IS an X-ray patient of 22-Feb, so its own parked picture is not ours to judge
con.commit()
for sid, name, day, hm in PARK:
    con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, clinic_id, day, state, verdict, planned_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (sid, name, "%s %s:00" % (day, hm), "check", rec.xray_id(name)[0], day, "check",
                                               "parked", "%s %s:00" % (day, hm)))
FILM = {"walk771A1new": ([], ["909301"]), "walk771A0old": (["2001-02-10"], ["909301"]), "walk771B1new": ([], []),
        "walk771C1new": ([], []), "walk771C2new": ([], []), "walk771C1old": (["2001-02-15"], []), "walk771C2old": (["2001-02-15"], []),
        "walk771D1new": ([], ["909304"]), "walk771E1new": (["2001-02-05"], []), "walk771F1new": (["2001-02-26"], []),
        "walk771G1new": ([], []), "walk771G1oth": ([], []), "walk771H1new": ([], []), "walk771K1new": ([], []),
        "walk771K1old": ([], []), "walk771K2old": ([], []), "walk771M1new": (["2001-02-17"], ["909314"]),
        "walk771N1old": (["2001-02-19"], ["909315"]), "walk771O1old": (["2001-02-19"], ["909316"]),
        "walk771P1old": (["2001-02-19"], ["909317"]), "walk771R1new": ([], []), "walk771S1old": (["2001-02-19"], ["909320"]),
        "walk771T1new": ([], ["909322"]), "walk771V1new": (["2001-02-20"], ["909326"])}                  # U: no row -- the film not read yet
for _s, (_d, _i) in FILM.items():
    con.execute("INSERT INTO xray_filmdate(src_id, dates, ids, how, read_at) VALUES (?,?,?,'walk','walk')", (_s, json.dumps(_d), json.dumps(_i)))
con.commit()
put(INBOX, [])
put(TEST, [])
put(CHECK, [{"id": sid, "name": name, "mimeType": "image/jpeg", "modifiedTime": utc(READD, "19:10"), "md5Checksum": "m-" + sid}
            for sid, name, day, hm in PARK])


def st(sid):
    r = rec._rows(con, "SELECT * FROM xray_filing WHERE src_id=?", (sid,))
    return r[0] if r else {}


def run(hhmm):
    os.environ["RECORDS_NOW"] = "%sT%s:00" % (READD, hhmm)
    items, notes = rec.xray_actions(con)
    return {i["id"]: i for i in items}, notes


# --- RUN 1 (20:25 on the re-add day) -----------------------------------------------------------------------------
it, notes = run("20:25")
check("the re-try ran without an error", not notes, str(notes))
a = st("walk771A1new")
check("A: the re-added picture is planned on the ID's one open day", a.get("state") == "planned" and a.get("day") == "2001-02-10"
      and a.get("action") == "file", str(a))
check("A: the reason names the ID's only open day", "only X-ray day with no photo" in (a.get("verdict") or ""), a.get("verdict"))
check("A: it is a mailbox item to file", it.get("walk771A1new", {}).get("action") == "file"
      and it["walk771A1new"].get("path") == rec._xray_path("2001-02-10"))
check("A: its older wrong-ID parked copy is held (not filed beside it, not moved yet)", st("walk771A0old").get("state") == "check"
      and "walk771A0old" not in it, str(st("walk771A0old")))
check("B: two open days and no film date -> stays", st("walk771B1new").get("state") == "check" and "walk771B1new" not in it)
c1, c2 = st("walk771C1new"), st("walk771C2new")
check("C: both re-added views filed on 15-Feb", c1.get("day") == c2.get("day") == "2001-02-15" and c1.get("state") == c2.get("state") == "planned")
check("C: both older no-ID copies held", st("walk771C1old").get("state") == st("walk771C2old").get("state") == "check"
      and "walk771C1old" not in it and "walk771C2old" not in it)
d = st("walk771D1new")
check("D: the corrected copy filed for 909304 on 20-Feb", d.get("day") == "2001-02-20" and d.get("clinic_id") == "909304" and d.get("state") == "planned")
check("D: nothing voided before the corrected copy is filed", rec._rows(con, "SELECT state FROM record_file WHERE drive_id='walkD771wrong04'")[0]["state"] == "ok")
check("E: a film date that is none of the ID's X-ray days -> stays", st("walk771E1new").get("state") == "check" and "walk771E1new" not in it)
f1 = st("walk771F1new")
check("F: no ID, the film's date, one name match -> filed by name on 26-Feb", f1.get("state") == "planned" and f1.get("day") == "2001-02-26"
      and f1.get("clinic_id") == "909310", str(f1))
check("F: the reason names the film's date", "printed on the film" in (f1.get("verdict") or ""))
check("G: another patient's picture whose ID is on that day's list -> never a duplicate (S752 files it to its own ID)",
      st("walk771G1oth").get("action") != "dup" and st("walk771G1oth").get("clinic_id") == "909311")
check("G: the corrected ZETA LAL copy filed for 909306 on 22-Feb", st("walk771G1new").get("day") == "2001-02-22" and st("walk771G1new").get("state") == "planned")
check("G: a filed patient sharing a word of the name -> untouched",
      rec._rows(con, "SELECT state FROM record_file WHERE drive_id='walkD771th09xxx'")[0]["state"] == "ok" and "walkD771th09xxx" not in it)
check("G: more old copies than corrected ones -> none moved to duplicates (they file as the corrected copy's sisters)",
      st("walk771K1old").get("action") != "dup" and st("walk771K2old").get("action") != "dup")
m1 = st("walk771M1new")
check("M: the film's date a day before the slip -> the slip's day", m1.get("day") == "2001-02-18" and m1.get("state") == "planned", str(m1))
n1 = st("walk771N1old")
check("N: no ID on the picture, the film's ID one X-ray patient of the day -> filed to it", n1.get("clinic_id") == "909315"
      and n1.get("state") == "planned" and "printed on the film" in (n1.get("verdict") or ""), str(n1))
o1 = st("walk771O1old")
check("O: a mistyped ID on the picture, the film's ID -> filed to the film's ID", o1.get("clinic_id") == "909316" and o1.get("state") == "planned", str(o1))
check("P: the film's ID whose patient shares no word of the name -> stays", st("walk771P1old").get("state") == "check")
check("R: a mistyped ID whose patient is another (no film date) -> stays", st("walk771R1new").get("state") == "check" and "walk771R1new" not in it)
check("S: the film's ID read one digit off, a loose name only -> stays", st("walk771S1old").get("state") == "check" and "walk771S1old" not in it)
check("V: the film's ID differs and the file's ID is X-rayed that day too -> stays (never to the file's ID)",
      st("walk771V1new").get("state") == "check" and "walk771V1new" not in it, str(st("walk771V1new")))
check("U: the film not read yet -> waits", st("walk771U1new").get("state") == "check" and "walk771U1new" not in it)
check("T: CHI NATH's corrected copy filed on 27-Feb", st("walk771T1new").get("day") == "2001-02-27" and st("walk771T1new").get("state") == "planned")
check("no picture filed twice for one study", len([1 for x in it.values() if x.get("action") == "file"]) == len({x["id"] for x in it.values() if x.get("action") == "file"}))

# --- the mailbox reports (RUN 1's items) ------------------------------------------------------------------------
rep = []
for k, x in it.items():
    if x["action"] == "file":
        rep.append({"id": k, "action": "file", "dest_id": "walkD771dst" + k[-6:], "name": x["name"]})
    elif x["action"] == "dup":
        rep.append({"id": k, "action": "dup"})
n = rec.xray_done(con, rep)
check("H: the mailbox's report applied", n == len(rep))
check("H: A filed: a record on 909301 for 10-Feb", rec._rows(con, "SELECT COUNT(*) n FROM record_file WHERE clinic_id='909301' AND day='2001-02-10' AND state='ok'")[0]["n"] == 1)
put(CHECK, [{"id": sid, "name": name, "mimeType": "image/jpeg", "modifiedTime": utc(READD, "19:10"), "md5Checksum": "m-" + sid}
            for sid, name, day, hm in PARK if st(sid).get("state") in ("check", "planned")])
it2, _ = run("21:25")
check("H/A: after the corrected copy is filed, its older copy -> duplicates", it2.get("walk771A0old", {}).get("action") == "dup"
      and st("walk771A0old").get("state") == "planned", str(st("walk771A0old")))
check("H/C: both older copies -> duplicates", it2.get("walk771C1old", {}).get("action") == "dup" and it2.get("walk771C2old", {}).get("action") == "dup")
w = rec._rows(con, "SELECT state FROM record_file WHERE drive_id='walkD771wrong04'")[0]
check("H/D: the copy filed to 909305 under the mistyped ID is voided", w["state"] == "void")
check("H/D: and goes to duplicates by the mailbox", it2.get("walkD771wrong04", {}).get("action") == "dup")
check("H/D: 909305's own picture untouched", rec._rows(con, "SELECT state FROM record_file WHERE drive_id='walkD771own05xx'")[0]["state"] == "ok")
check("H/T: TAU SEN's only photo (one film) is never voided", rec._rows(con, "SELECT state FROM record_file WHERE drive_id='walkD771tau23xx'")[0]["state"] == "ok"
      and "walkD771tau23xx" not in it2)
rep2 = [{"id": k, "action": "dup"} for k, x in it2.items() if x["action"] == "dup" and k != "walk771C2old"]
rec.xray_done(con, rep2)
check("H: the dups reported are dup", st("walk771A0old").get("state") == "dup" and st("walkD771wrong04").get("state") == "dup")
it3, _ = run("22:25")
check("H: the dup not yet done is offered again", it3.get("walk771C2old", {}).get("action") == "dup")
check("H: nothing filed twice on a later run", not any(x.get("action") == "file" and st(k).get("state") == "done" for k, x in it3.items()))
check("Check karein no longer lists the filed or moved pictures",
      not any(i.get("key") in ("xf:walk771A1new", "xf:walk771A0old", "xf:walk771C1old") for i in rec.xray_items(con)))
tidy()
con.execute("DROP TABLE IF EXISTS xray_filmdate") if dbp.endswith("walk_new.db") else None
con.commit()
print("WALK OK %d/%d -- S772: the film's date, the ID's one open day, the clean-up" % (N[0], N[0]))
