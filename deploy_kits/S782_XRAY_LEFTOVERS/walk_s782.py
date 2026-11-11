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
slip("xp", "99906", "QSUNEETA KAMWALK", ["Shoulder AP"])  # (d) X-ray patient, no photo yet
slip("xp", "99907", "QRAMESHWAR PALWALK", ["Hip AP"])      # (d) two near-twins: one X-rayed ...
slip("opd", "99908", "QRAMESHWER PALWALK", [])             #     ... one only seen -> never filed by spelling
slip("xp", "99910", "QSUNIL YADWALK", ["Knee AP"])         # (d) ANIL is never SUNIL
slip("opd", "99909", "QKAVITHA MEHWALK", [])               # screen: a visitor whose name is the picture's but for the spelling
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
MOB = "9" + "8" * 4 + "0" * 4 + "6"                     # a made-up mobile, put together at run time
con.execute("INSERT INTO patient_ref(clinic_id, name, phone_last4, mobile) VALUES (?,?,?,?)", ("99906", "QSUNEETA KAMWALK", MOB[-4:], MOB))
slip("xp", "99911", "QSARITA DEVWALK", ["Wrist AP"])      # review: SAVITA is not SARITA
con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", ("99916", "QOTHER PERSONWALK"))   # a real patient one digit off 99906
slip("xp", "99913", "QVINITA BAIWALK", ["Ankle AP"])      # review: VANITA is not VINITA
slip("xp", "99912", "QMINA LALWALK", ["Elbow AP"])         # review: an X-ray patient with the picture's exact name ...
con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", ("45", "QMEENA LALWALK"))   # ... and old patient 45, spelt another way
park("WALKPARK000S", "QVANITA BAIWALK.jpg", [D], [])      # review probe: A/I apart -> never filed on VINITA
park("WALKPARK000T", "QMINA LALWALK 45.jpg", [D], [])     # review probe: 45 is HER ID (the name but for the spelling) -> kept, never filed on 99912
park("WALKPARK000Q", "QSAVITA DEVWALK.jpg", [D], [])      # review probe: a consonant apart -> never filed on SARITA
park("WALKPARK000R", "QSUNITA KAMWALK 99916.jpg", [D], [])   # review probe: its ID is one digit off 99906 but a REAL patient -> not on 99906
park("WALKPARK000K", "QSUNITA KAMWALK.jpg", [D], [])      # (d) one X-ray patient's name but for the spelling -> 99906
park("WALKPARK000L", "QRAMESHVAR PALWALK.jpg", [D], [])   # (d) wrong-patient probe: two people alike -> not filed
park("WALKPARK000P", "QANIL YADWALK.jpg", [D], [])        # (d) wrong-patient probe: a surname alone shared -> not filed
park("WALKPARK000M", "QKAVITA MEHWALK.jpg", [D], [])      # screen: the visitor listed first
con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, day, state, verdict, planned_at) VALUES (?,?,?,?,?,?,?,?)",
            ("WALKPARK000N", "QOLDPIC NAMEWALK.jpg", "2030-01-02 10:00:00", "check", "2030-01-02", "check", "in the check folder", "2030-01-02 10:00:00"))
                                                               # 7 days: an older parked picture -- the owner's and Shavez's only
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
try:
  import check_screens as CS                             # the S782 screens, on the same made-up day
  CS.attach(R)
  fresh = sqlite3.connect(work); fresh.row_factory = sqlite3.Row
  staff_ids = {r["src_id"] for r in CS._parked(fresh, recent=True)}
  all_ids = {r["src_id"] for r in CS._parked(fresh)}
  mrow = dict(fresh.execute("SELECT * FROM xray_filing WHERE src_id='WALKPARK000M'").fetchone())
  pl = CS.pick_list(fresh, mrow, {})
  f_mob = CS.find_people(fresh, MOB, D)
  f_name = CS.find_people(fresh, "QSUNITA KAMWALK", D)
  f_id = CS.find_people(fresh, "99906", D)
  f_none = CS.find_people(fresh, "XYZQ PLOVERDINE", D)
  fresh.close()
except Exception as ex:                                  # the live file has no S782 screens: every screen check fails
  print("the screens stopped: %s" % type(ex).__name__)
  staff_ids, all_ids, pl, f_mob, f_name, f_id, f_none = set(), set(), [], [], [], [], [None]
checks += [
    ("(d) one X-ray patient's name but for the spelling files on him", out.get("WALKPARK000K", {}).get("action") == "file" and row("WALKPARK000K")["clinic_id"] == "99906" and "but for the spelling" in (row("WALKPARK000K")["verdict"] or "")),
    ("(d) wrong-patient probe: two people alike -> not filed", "WALKPARK000L" not in out and row("WALKPARK000L")["state"] == "check"),
    ("(d) wrong-patient probe: ANIL is never SUNIL -> not filed", "WALKPARK000P" not in out and row("WALKPARK000P")["state"] == "check"),
    ("7 days: an older picture is off the reception's list", "WALKPARK000N" not in staff_ids and "WALKPARK000B" in staff_ids),
    ("7 days: the owner and Shavez still see it", "WALKPARK000N" in all_ids),
    ("screen: the spelling-alike visitor is listed first, tagged", bool(pl) and pl[0]["id"] == "99909" and pl[0]["tag_en"] in ("Similar name", "Name partly matches")),
    ("search: a full mobile number finds the patient, and shows the number in full", bool(f_mob) and f_mob[0]["id"] == "99906" and f_mob[0]["mobile"] == MOB),
    ("search: a name spelt another way finds the patient first, marked as come that day", bool(f_name) and f_name[0]["id"] == "99906" and f_name[0]["came"]),
    ("search: a clinic ID finds the patient", bool(f_id) and f_id[0]["id"] == "99906"),
    ("search: a name nobody has finds nobody", f_none == []),
    ("review: SAVITA is never filed on SARITA", "WALKPARK000Q" not in out and row("WALKPARK000Q")["state"] == "check"),
    ("review: a one-digit-off ID that is a real patient keeps the picture off 99906", row("WALKPARK000R")["clinic_id"] != "99906" or row("WALKPARK000R")["state"] == "check"),
    ("review: VANITA is never filed on VINITA", "WALKPARK000S" not in out and row("WALKPARK000S")["state"] == "check"),
    ("review: a short ID that is the name's patient but for the spelling is kept -- not filed on the other patient", row("WALKPARK000T")["clinic_id"] != "99912"),
    ("screen: a long day folds all but the first three", len(pl) > 5 and not any(p["near"] for p in pl[:3]) and all(p["near"] for p in pl[3:])),
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
