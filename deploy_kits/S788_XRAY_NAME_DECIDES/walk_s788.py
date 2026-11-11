#!/usr/bin/python3
# walk_s788.py -- kit S788_XRAY_NAME_DECIDES. Usage: walk_s788.py <dir holding check_screens.py (and records.py)> <a finance.db copy> [--control]
# A SCRATCH copy of the database; counts and ok/BAD only. Data-shaped checks (the 24-Oct SUNDARWATI case) run only when S788_SHAPE=1
# (the 11-Nov copy); everywhere else the rule is checked on whatever it gives. Last line "WALK OK n/n" | "WALK RED k of n" | "CONTROL: ...".
import importlib, os, re, shutil, sqlite3, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s788w."); DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB)
os.environ["FINANCE_DB"] = DB
for p in [x for x in os.environ.get("S788_LIBS", "").split(os.pathsep) if x] + [K]:
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why != "" and not ok) else ""))
try:
    R = importlib.import_module("records"); CS = importlib.import_module("check_screens")
    if CS.R is None:
        CS.attach(R)
    ck("A1 check_screens from the kit dir", os.path.dirname(os.path.abspath(CS.__file__)) == K)
    ck("A2 it has the S788 rule", hasattr(CS, "_s788_name_decides"))
except Exception as e:  # noqa: BLE001
    ck("A import", False, repr(e)[:150]); CS = None
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
if CS is not None and hasattr(CS, "_s788_name_decides"):
    P = CS._parked(con)
    reasons = {r["src_id"]: CS._reason(con, r, {})[1] for r in P}
    filmhas = [r for r in P if R.xray_id(r["orig_name"])[1] == "none" and (R._s772_film(con, r["src_id"]) or [[], []])[1]]
    ck("B1 a photo whose film shows an ID no longer says 'no clinic ID on the photo'", all("the film reads" in reasons[r["src_id"]] for r in filmhas)
       and not any(v == "No clinic ID on the photo" for v in reasons.values()), len(filmhas))
    n = CS.s787_auto(con)
    def ans(sid):
        x = con.execute("SELECT answer, note, answered_by FROM record_check WHERE key=?", ("xf:" + sid,)).fetchone()
        return dict(x) if x else {}
    g8 = [r for r in P if ans(r["src_id"]).get("answered_by", "").startswith("system · S788")]
    ck("C1 the rule gives (%d here)" % len(g8), len(g8) >= (1 if os.environ.get("S788_SHAPE") == "1" else 0))
    bad = []
    for r in g8:
        cid = ans(r["src_id"])["note"]
        fr = R._s772_film(con, r["src_id"]); own, how = R.xray_id(r["orig_name"])
        nums = set(fr[1] if fr else []) | ({own} if how == "one" and own else set())
        names = R._s782_names(con, cid, {})
        stem = R.xray_stem(r["orig_name"]); toks = R._s752_tokens(stem)
        if not nums or not all(x == cid or R._s752_one_off(x, cid) for x in nums) or not any(CS._s788_alike(toks, stem, nm) for nm in names):
            bad.append(1)
    ck("C2 each given: the name is that patient's and every number his ID or one digit off", not bad, len(bad))
    if os.environ.get("S788_SHAPE") == "1":
        sw = [r for r in P if re.sub(r"[^a-z]", "", (r["orig_name"] or "").lower()).startswith("sundarwati")]
        ck("C3 SUNDARWATI (24-Oct, the film read one digit off) goes to her own ID",
           len(sw) == 1 and ans(sw[0]["src_id"]).get("answer") == "id_fixed" and ans(sw[0]["src_id"]).get("note", "").endswith("43"))
    ck("C4 a second pass gives nothing more", CS.s787_auto(con) == 0)
    # the guard: a made-up second patient of the same name that day -> no S788 answer (on a fresh copy)
    con.close(); shutil.copyfile(SRC, DB); con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    if g8:
        r0 = next(r for r in P if r["src_id"] == g8[0]["src_id"])
        fr = R._s772_film(con, r0["src_id"]); day = fr[0][0] if fr and fr[0] else r0["day"]
        fake = "S788W1"
        assert not con.execute("SELECT 1 FROM patient_ref WHERE clinic_id=?", (fake,)).fetchone()
        sn = (con.execute("SELECT MAX(sn) FROM clinic_day_line").fetchone()[0] or 0) + 1000
        con.execute("INSERT INTO clinic_day_line (business_date, section, sn, clinic_id, patient) VALUES (?,?,?,?,?)",
                    (day, "consult", sn, fake, R.xray_stem(r0["orig_name"])))
        con.commit()
        CS.s787_auto(con)
        a0 = con.execute("SELECT answered_by FROM record_check WHERE key=?", ("xf:" + r0["src_id"],)).fetchone()
        ck("D1 when someone else who came has the same name, the name does not decide", not (a0 and str(a0[0]).startswith("system · S788")))
con.close(); shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
