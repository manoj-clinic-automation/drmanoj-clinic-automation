#!/usr/bin/python3
# walk_s790.py -- kit S790_XRAY_PHOTO_NUDGE. Usage: walk_s790.py <kit dir> <a finance.db copy> [--control]
# Read-only against a scratch copy; counts and ok/BAD only. Last line "WALK OK n/n" | "WALK RED k of n" | "CONTROL: ...".
import hashlib, importlib, json, os, shutil, sqlite3, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s790w."); DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB)
os.environ.update({"FINANCE_DB": DB, "XN_STATE": os.path.join(T, "st.json")})
sys.path.insert(0, os.path.join(K, "finance"))
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why != "" and not ok) else ""))
try:
    X = importlib.import_module("xray_photo_nudge")
    ck("A1 the module is the kit's", os.path.dirname(os.path.abspath(X.__file__)) == os.path.join(K, "finance"))
except Exception as e:  # noqa: BLE001
    X = None; ck("A1 the module is there", False, repr(e)[:100])
if X:
    md5 = hashlib.md5(open(DB, "rb").read()).hexdigest()
    con = sqlite3.connect(DB)
    last = con.execute("SELECT MAX(day) FROM slip WHERE series='xp' AND state='ok'").fetchone()[0]
    duty = con.execute(X.SQL.replace("s.day <= ?", "s.day < ?"), (X.FROM_DAY, last)).fetchall()
    con.close()
    t, old, total = X.counts(sqlite3.connect("file:%s?mode=ro" % DB, uri=True), last)
    ck("B1 the count runs on the copy (today %d of %d, older %d)" % (t, total, old), total >= t >= 0 and old >= 0)
    ck("B2 older ones = the same rule as reception's Aaj ka kaam line (minus photos already on their way)", old == len(duty))
    sent = []
    st = X.run(pusher=lambda who, p: (sent.append((who, p)) or (1, 0)), today=last)
    ck("C1 one notification to each of the six logins", sorted(w for w, _ in sent) == sorted(X.STAFF + X.OWNER))
    en = [p for w, p in sent if w == "manoj"]; hi = [p for w, p in sent if w == "alisha"]
    ck("C2 English for the owner, Hindi words for staff, the tap opens Report baaki's X-ray list",
       en and hi and en[0]["url"] == hi[0]["url"] == "/finance/slips/pending?t=xray" and en[0]["title"] != hi[0]["title"])
    n = t + old
    ck("C3 the title says the work: pending -> the count; none -> done", (str(n) in hi[0]["title"]) if n else hi[0]["title"].startswith("✅"))
    c0 = X.cards(0, 0, 5)
    ck("C4 when everything is in, it says so (done shown as done)", c0["en"][0].startswith("✅") and "5 of 5" in c0["en"][1])
    ck("D1 the database is never written", hashlib.md5(open(DB, "rb").read()).hexdigest() == md5)
    ck("D2 its state is kept", json.load(open(os.environ["XN_STATE"]))["pending_today"] == t)
shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
