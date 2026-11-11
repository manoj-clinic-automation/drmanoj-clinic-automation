#!/usr/bin/python3
# walk_s787.py -- kit S787_XRAY_SAME_PERSON. Usage: walk_s787.py <dir holding check_screens.py, records.py, DUTY_MAP.json(.s787)>
#                 <a finance.db copy> [--control]
# Runs on a SCRATCH copy of the database (made here, removed at the end); prints counts and ok/BAD only -- never a name or a number
# from the copy. Needs the copy to hold the 11-Nov shape (parked pictures with a same-name filed photo, a group of 3+). Last line:
# "WALK OK n/n" | "WALK RED k of n"; with --control "CONTROL: red ..." when red as it must be.
import importlib, json, os, re, shutil, sqlite3, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s787w.")
DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB)
os.environ["FINANCE_DB"] = DB
for p in [x for x in os.environ.get("S787_LIBS", "").split(os.pathsep) if x] + [K]:
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)                                              # the kit's dir ends up first, whatever the script's own dir
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why != "" and not ok) else ""))
U = {"user": "walk"}
try:
    R = importlib.import_module("records")
    CS = importlib.import_module("check_screens")
    if CS.R is None:
        CS.attach(R)
    ck("A1 both modules from the kit dir", os.path.dirname(os.path.abspath(CS.__file__)) == K and os.path.dirname(os.path.abspath(R.__file__)) == K)
except Exception as e:  # noqa: BLE001
    ck("A modules import", False, repr(e)[:150]); R = CS = None
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
def ans(sid):
    r = con.execute("SELECT answer, note, answered_by FROM record_check WHERE key=?", ("xf:" + sid,)).fetchone()
    return dict(r) if r else {}
if CS is not None and hasattr(CS, "s787_auto"):
    P0 = CS._parked(con)
    q0 = CS.xray_queue(con)
    ck("B1 the copy has parked pictures", len(P0) >= 10, len(P0))
    ck("B2 the same person's photos are one card", len(q0) < len(P0) and any(i.get("n", 1) >= 2 for i in q0), "%d cards / %d" % (len(q0), len(P0)))
    big = max(q0, key=lambda i: i.get("n", 1))
    ck("B3 the card says how many photos", big["title"].endswith("%d photos" % big["n"]) and len(big["copies"]) == big["n"] - 1)
    n = CS.s787_auto(con)
    given = [r for r in P0 if ans(r["src_id"]).get("answered_by", "").startswith(("system · S787", "system · S788"))]
    ck("C1 another photo of a patient filed that day gets his ID (%d here)" % n, len(given) == n and (n >= 1 or os.environ.get("S787_ANY") == "1"), "%d given" % n)
    okid = all(re.fullmatch(r"\d{1,8}", ans(r["src_id"]).get("note", "")) and R._known_id(con, ans(r["src_id"])["note"]) for r in given)
    ck("C2 each to a known ID that has a filed X-ray photo within a day", okid and all(con.execute(
        "SELECT 1 FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? LIMIT 1", (ans(r["src_id"])["note"],)).fetchone() for r in given))
    ck("C3 a second pass gives nothing more", CS.s787_auto(con) == 0)
    ck("C4 those leave the queue", len(CS._parked(con)) == len(P0) - n)
    # D: 'not in Docterz' on the biggest remaining group
    q1 = CS.xray_queue(con)
    g = max(q1, key=lambda i: i.get("n", 1))
    sids = [g["sid"]] + g["copies"]
    code, d = CS.answer(con, U, {"key": g["key"], "a": "no_docterz"}, en=True)
    ck("D1 'Not in Docterz' answers the whole card", code == 200 and all(ans(s).get("answer") == "no_docterz" for s in sids), (code, d))
    ck("D2 it leaves the waiting list", not any(i["sid"] in sids for i in CS.xray_queue(con)) and not any(r["src_id"] in sids for r in CS._parked(con)))
    nz = CS.xray_queue(con, nodz_only=True)
    mine = [x for x in nz if x["sid"] in sids or set(x["copies"]) & set(sids)]
    ck("D3 it is ONE item on his 'Not in Docterz' tile", len(mine) == 1 and mine[0]["n"] >= len(sids) and mine[0]["reason_en"].startswith("Not in Docterz"))
    ck("D4 the old list (records.xray_items) leaves it out too", not any(i.get("key") in ["xf:" + s for s in sids] for i in R.xray_items(con)))
    ck("D5 its photo and patients can still be opened", any(r["src_id"] == g["sid"] for r in CS._parked(con, nodz=True)))
    known = con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id GLOB '[0-9]*' AND (merged_into IS NULL OR merged_into='') LIMIT 1").fetchone()[0]
    code, d = CS.answer(con, U, {"key": g["key"], "a": "id_fixed", "new_id": known, "check": 1}, en=True)
    ck("D6 an ID can be checked for it later", code == 200 and d.get("check"))
    code, d = CS.answer(con, U, {"key": g["key"], "a": "id_fixed", "new_id": known}, en=True)
    ck("D7 and given: every photo of it filed to that ID", code == 200 and all(ans(s).get("answer") == "id_fixed" and ans(s).get("note") == known for s in sids)
       and "photos" in d.get("msg", ""), (code, d))
    ck("D8 gone from his tile", not any(x["sid"] in sids or set(x["copies"]) & set(sids) for x in CS.xray_queue(con, nodz_only=True)))
    # E: a card of one, 'not an X-ray' stays per picture
    q2 = CS.xray_queue(con)
    one = next((i for i in q2 if i["n"] == 1), None)
    if one:
        code, d = CS.answer(con, U, {"key": one["key"], "a": "not_xray"}, en=True)
        ck("E1 'Not an X-ray' still works", code == 200 and ans(one["sid"]).get("answer") == "not_xray")
    code, d = CS.answer(con, U, {"key": "xf:nosuchpicture0000", "a": "no_docterz"}, en=True)
    ck("E2 an unknown picture is refused", code == 409)
    ck("E3 the counts count people, not photos", CS.counts(con)["wait"] == len(CS.xray_queue(con)))
else:
    ck("B check_screens has s787_auto", False)
# F: the duty map and records' hook
dm = os.path.join(K, "DUTY_MAP.json.s787") if os.path.exists(os.path.join(K, "DUTY_MAP.json.s787")) else os.path.join(K, "DUTY_MAP.json")
try:
    D = json.load(open(dm, encoding="utf-8"))
    sqls = [x.get("due_sql", "") for x in D.get("duties", []) if "xray_filing" in x.get("due_sql", "")]
    ck("F1 the duty map v23: reception's X-ray line leaves 'not in Docterz' out", D.get("version") == 23 and len(sqls) == 1 and "'no_docterz'" in sqls[0])
    if sqls:
        con.execute("SELECT 1")
        r = con.execute(sqls[0]).fetchone()
        ck("F2 the line's SQL runs on the copy", r is not None)
except Exception as e:  # noqa: BLE001
    ck("F duty map", False, repr(e)[:120])
src = open(os.path.join(K, "records.py"), encoding="utf-8").read()
ck("F3 records: the plan asks s787_auto first", src.count("_s757.s787_auto(con)") == 1)
con.close()
shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
