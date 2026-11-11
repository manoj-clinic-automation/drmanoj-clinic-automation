# S782 walk: a made-up day (15-Jan-2030) inside a copy of the real database (live shape); five pictures, five verdicts.
# Run with the new records.py -> all PASS; with the live (old) one -> the CONTROL goes red.
import sys, types, sqlite3, shutil, json, os
fl = types.ModuleType("flask")
class BP:
    def __init__(s, *a, **k): pass
    def route(s, *a, **k): return lambda f: f
    def __getattr__(s, n): return lambda *a, **k: (lambda f: f)
fl.Blueprint = BP
for n in ("Response", "jsonify", "redirect", "request"): setattr(fl, n, None)
sys.modules["flask"] = fl
sys.path.insert(0, sys.argv[1]); dbsrc = sys.argv[2]; CONTROL = "--control" in sys.argv
os.environ["RECORDS_NOW"] = "2030-01-20T10:00:00"
import records as R
work = dbsrc + ".s782w"; shutil.copy(dbsrc, work)
con = sqlite3.connect(work); con.row_factory = sqlite3.Row
D = "2030-01-15"
def slip(series, cid, name, studies):
    cur = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, name_seen, state) VALUES (?,?,?,?,?,'ok')", (series, "W"+cid, D, cid, name))
    for s in studies:
        con.execute("INSERT INTO slip_item(slip_id, kind, name) VALUES (?,?,?)", (cur.lastrowid, "xray", s))
slip("xp", "99901", "QALPHA ROOPWALK", ["Knee AP"])          # X-ray patient
slip("opd", "987", "QOMEGA TEJWALK", [])                    # a visitor whose ID is three digits
slip("xp", "99903", "QDELTA MANWALK", ["Wrist AP/Lat"])     # X-ray patient, one film, photo filed
slip("xp", "99904", "QZETA PALWALK", ["Hand AP"])           # X-ray patient whose ID a film prints
slip("xp", "99905", "QEPSILON VEERWALK", ["Knee studies (K/S)"])  # two films, one photo filed
def park(sid, name, dates, ids):
    con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, day, state, verdict, planned_at) VALUES (?,?,?,?,?,?,?,?)",
                (sid, name, D + " 10:00:00", "check", D, "check", "in the check folder", D + " 10:00:00"))
    con.execute("INSERT INTO xray_filmdate(src_id, dates, ids, how) VALUES (?,?,?,?)", (sid, json.dumps(dates), json.dumps(ids), "walk"))
def filed(sid, name, cid, dates, ids):
    cur = con.execute("INSERT INTO record_file(clinic_id, kind, day, drive_id, file_name, source, source_ref, state) VALUES (?,?,?,?,?,?,?, 'ok')",
                      (cid, "xray", D, "DEST" + sid, name, "xray_inbox", sid))
    con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, clinic_id, day, state, verdict, file_id) VALUES (?,?,?,?,?,?,?,?,?)",
                (sid, name, D + " 09:00:00", "file", cid, D, "done", "matched", cur.lastrowid))
    con.execute("INSERT INTO xray_filmdate(src_id, dates, ids, how) VALUES (?,?,?,?)", (sid, json.dumps(dates), json.dumps(ids), "walk"))
filed("WALKDONE0003", "QDELTA MANWALK.jpg", "99903", [D], ["99903"])
filed("WALKDONE0005", "QEPSILON VEERWALK.jpg", "99905", [D], ["99905"])
park("WALKPARK000A", "QALPHA ROOPWALK 3.jpg", [D], [])           # (a) photo number -> files on 99901 by name
park("WALKPARK000B", "QGAMMA NOORWALK 987.jpg", [D], [])         # 987 came that day: kept as an ID -> not filed, not touched
park("WALKPARK000C", "QDELTA MANWALK.jpg", [D], ["99903"])      # (b) second upload -> duplicates
park("WALKPARK000D", "QDELTA MANWALK.jpg", [D], ["99904"])      # wrong-patient probe: the film prints ANOTHER X-ray patient's ID -> never dup, never filed by the name
park("WALKPARK000E", "QEPSILON VEERWALK.jpg", [D], ["99905"])    # a film still without its photo -> never dup
park("WALKPARK000F", "QDELTA MANWALK 2.jpg", [D], ["99903"])    # review 2: a second VIEW, named apart -> never sent to duplicates
park("WALKPARK000G", "QBAD DATEWALK 5.jpg", ["2030-02-30"], [])  # review 3: a film date that is no calendar date -> no crash
con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, day, state, verdict, planned_at) VALUES (?,?,?,?,?,?,?,?)",
            ("WALKPARK000H", "QALPHA ROOPWALK 7.jpg", D + " 10:00:00", "check", D, "check", "in the check folder", D + " 10:00:00"))
                                                               # review 4: its film not read yet -> the 7 is never stripped
con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, day, state, verdict, planned_at) VALUES (?,?,?,?,?,?,?,?)",
            ("WALKGONE000I", "QOLD DUPWALK.jpg", D + " 10:00:00", "dup", D, "planned", "S782 \u00b7 a second upload", "2030-01-18 10:00:00"))
                                                               # review 1: sent to duplicates, gone from the folder -> state dup
con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, day, state, verdict, planned_at) VALUES (?,?,?,?,?,?,?,?)",
            ("WALKPARK000J", "QTHETA NOWALK.jpg", D + " 10:00:00", "dup", D, "planned", "S782 \u00b7 a second upload", "2030-01-19 10:00:00"))
con.execute("INSERT INTO xray_filmdate(src_id, dates, ids, how) VALUES (?,?,?,?)", ("WALKPARK000J", json.dumps([D]), json.dumps([]), "walk"))
                                                               # review 2/1: a planned duplicate the rule no longer finds -> back to the list
con.commit()
files = [{"id": s, "name": n, "mimeType": "image/jpeg", "modifiedTime": R._s752_utc(D + " 10:00:00")} for s, n in
         con.execute("SELECT src_id, orig_name FROM xray_filing WHERE src_id LIKE 'WALKPARK%'")]
try:
    out = {o["id"]: o for o in R._s752_retry(con, files, "2030-01-20 10:00:00", True)}
    ran = True
except Exception as ex:                                  # the old file stops on the made-up bad film date
    con.rollback(); out, ran = {}, False
    print("the re-try stopped: %s" % type(ex).__name__)
try:
    out2 = {o["id"]: o for o in R._s752_retry(con, files, "2030-01-20 10:15:00", True)}
except Exception:                                        # noqa: BLE001
    con.rollback(); out2 = {}   # the next run, the mailbox not yet done
row = lambda s: dict(con.execute("SELECT * FROM xray_filing WHERE src_id=?", (s,)).fetchone())
checks = [
    ("the re-try ran through", ran),
    ("CONTROL (a) the photo number dropped: ALPHA 3 filed on 99901", out.get("WALKPARK000A", {}).get("action") == "file" and row("WALKPARK000A")["clinic_id"] == "99901"),
    ("(a) the verdict says it was a photo number", "photo's number" in (row("WALKPARK000A")["verdict"] or "")),
    ("(a) a 3-digit number that came that day is kept: GAMMA 987 not filed", "WALKPARK000B" not in out and row("WALKPARK000B")["state"] == "check"),
    ("CONTROL (b) the second upload goes to duplicates", out.get("WALKPARK000C", {}).get("action") == "dup" and row("WALKPARK000C")["state"] == "planned"),
    ("(b) its row names the copy already filed", "99903" in (row("WALKPARK000C")["verdict"] or "")),
    ("probe: another ID on the film -> not dup, not filed on 99903", "WALKPARK000D" not in out and row("WALKPARK000D")["state"] == "check"),
    ("probe: a film still without its photo -> not dup", out.get("WALKPARK000E", {}).get("action") != "dup"),
    ("the next run asks again for the waiting duplicate", out2.get("WALKPARK000C", {}).get("action") == "dup"),
    ("the next run does not file A twice", out2.get("WALKPARK000A", {}).get("action") in (None, "file") and con.execute("SELECT COUNT(*) FROM xray_filing WHERE clinic_id='99901' AND state='planned'").fetchone()[0] == 1),
    ("review 2: a second view named apart is never sent to duplicates", out.get("WALKPARK000F", {}).get("action") != "dup" and row("WALKPARK000F")["action"] != "dup"),
    ("review 3: a film date that is no calendar date stops nothing", "WALKPARK000A" in out),
    ("review 4: a film not read yet -- its number not stripped", "WALKPARK000H" not in out and "photo's number" not in (row("WALKPARK000H")["verdict"] or "")),
    ("review 1: a duplicate gone from the folder is closed", row("WALKGONE000I")["state"] == "dup"),
    ("review 2/1: a planned duplicate no longer one goes back to the check list", row("WALKPARK000J")["state"] == "check"),
    ("nothing planned to be filed again on 99903 (its photo is there)", con.execute("SELECT COUNT(*) FROM xray_filing WHERE clinic_id='99903' AND state='planned' AND action='file' AND src_id IN ('WALKPARK000C','WALKPARK000E')").fetchone()[0] == 0),
]
bad = 0
for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name); bad += (not ok)
con.close(); os.remove(work)
if CONTROL:
    print("CONTROL: red (%d of %d fail on this file)" % (bad, len(checks)) if bad else "CONTROL: NOT red")
    sys.exit(0 if bad else 1)
print("WALK OK %d/%d" % (len(checks), len(checks)) if not bad else "WALK RED %d of %d" % (len(checks) - bad, len(checks)))
sys.exit(1 if bad else 0)
