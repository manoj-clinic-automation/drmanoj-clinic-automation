# walk_s717.py -- kit S717_GMB_WATCH (session 389, the parent, 06-Nov-2026)
# The readings and the listings on a MADE-UP store -- never the live one. Also re-proves S713's keeping on the new module.
#   python walk_s717.py <dir with portal_gmb.py> <the kit's seed_s717.txt>
#   last line: "N of N green"  (or "X S717 check(s) red . Y green")
import json, os, shutil, sqlite3, sys, tempfile

KDIR = os.path.abspath(sys.argv[1]); SEED = os.path.abspath(sys.argv[2])
T = tempfile.mkdtemp(prefix="s717walk_")
DB = os.path.join(T, "gmb_store.db")
OK, RED = [], []


def check(label, cond, why=""):
    (OK if cond else RED).append(label)
    print(("GREEN " if cond else "RED   ") + label + ("" if cond else "  -- " + str(why)[:220]))


STAGE = os.path.join(T, "code"); os.makedirs(STAGE); shutil.copy(os.path.join(KDIR, "portal_gmb.py"), STAGE)
sys.path.insert(0, STAGE); sys.dont_write_bytecode = True
from flask import Flask
import portal_gmb as G

N = 18
if not hasattr(G, "seed") or not hasattr(G, "check_reading"):
    for n in range(1, N + 1):
        check("%d (the module has no readings: not S717)" % n, False, "no seed / check_reading")
else:
    def allow(f):
        return f

    def make(guard):
        app = Flask("s717walk_%s" % id(guard))
        G.register(app, guard, lambda: "manoj", lambda k, d="": DB if k == "GMB_STORE_DB" else d)
        return app.test_client()

    cl = make(allow); H = {"X-Gmb": "1"}

    def post(path, b, h=H):
        r = cl.post("/portal/gmb/api/" + path, data=json.dumps(b), content_type="application/json", headers=h)
        return r.status_code, (r.get_json(silent=True) or {})

    def get():
        r = cl.get("/portal/gmb/api/watch")
        return r.status_code, (r.get_json(silent=True) or {})

    s, j = get()
    check("1 before any reading the section has nothing to show (latest null)", s == 200 and j.get("latest") is None, (s, j))
    check("2 the seed puts the 5-Nov reading in once", G.seed(DB, SEED) == "seeded", "")
    check("3 the seed a second time writes nothing", G.seed(DB, SEED) == "already", "")
    s, j = get()
    L = (j.get("latest") or {}).get("data") or {}
    check("4 the reading reads back: 167 ours, 146 elsewhere, 9.0 percent, 6 complaints, 16 words",
          s == 200 and L.get("ours_n") == 167 and L.get("else_n") == 146 and L.get("ours_low_pct") == 9.0
          and len(L.get("themes", [])) == 6 and len(L.get("words", [])) == 16 and j.get("previous") is None, L)
    check("5 the five other listings are the listings to read", j.get("listings") == [
        "Dr Praveen Agarwal (Jaipur Ortho)", "Dr Abhishek Singh", "RG Hospital", "Shri Siddhi Vinayak Hospital", "Dr Mohit Gupta"],
        j.get("listings"))
    seed = json.load(open(SEED, encoding="utf-8"))
    nxt = json.loads(json.dumps(seed)); nxt["taken_on"] = "2026-11-06"; nxt["data"]["themes"][0]["ours"] = 5.1
    s, j = post("snapshot", nxt)
    s2, j2 = get()
    check("6 a new reading is kept; the page then gets it as latest and the 5-Nov one as previous",
          s == 200 and (j2.get("latest") or {}).get("taken_on") == "2026-11-06"
          and (j2.get("previous") or {}).get("taken_on") == "2026-11-05", (s, j, j2.get("latest", {}).get("taken_on")))
    bad = []
    for mut in (lambda d: d.update(taken_on="19-11-2026"),
                lambda d: d["data"]["themes"][0].update(ours=140),
                lambda d: d["data"].update(themes=[]),
                lambda d: d["data"]["words"].append("x" * 31),
                lambda d: d["data"].update(note="y" * 301),
                lambda d: d["data"].update(ours_n="167"),
                lambda d: d["data"].update(sources=[]),
                lambda d: d.update(taken_on="2026-19-39"),
                lambda d: d.update(taken_on="2062-11-19"),
                lambda d: d["data"]["themes"][0].update(ours=10 ** 400),
                lambda d: d["data"]["themes"].append(dict(d["data"]["themes"][0]))):
        x = json.loads(json.dumps(seed)); mut(x); bad.append(post("snapshot", x)[0])
    check("7 a wrong date, a percent over 100, no complaints, a long word, a long note, a text count, no sources, a day "
          "that does not exist, a future date, a huge number and a complaint twice are refused", bad == [400] * 11, bad)
    s, j = post("snapshot", seed, h={})
    check("8 a reading without the page's own header is refused (403)", s == 403, s)
    s, j = post("watch", {"name": "Dr New Listing"})
    check("9 the owner adds a listing; it is in the list at once", s == 200 and j.get("listings", [])[-1] == "Dr New Listing", j)
    s, j = post("watch", {"name": "Dr New Listing"})
    check("10 adding the same listing again does not make it twice", s == 200 and j.get("listings", []).count("Dr New Listing") == 1, j)
    s, j = post("watch", {"name": "call 98765" + "43210"})
    check("11 a phone number typed as a listing is kept as [number]", s == 200 and "[number]" in j.get("listings", [])[-1]
          and "43210" not in j.get("listings", [])[-1], j.get("listings"))
    for k in range(20):
        post("watch", {"name": "Listing %c%c" % (65 + k, 65 + k)})
    s, j = post("watch", {"name": "One too many"})
    check("12 twenty listings at most", s == 400, (s, j))
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    rows = [json.loads(r["data"]) for r in c.execute("SELECT data FROM snapshot")]
    keys = set(k for r in rows for k in r)
    check("13 a reading keeps only counts, percents, names and words (no review text, no reviewer, no star average)",
          keys == {"ours_n", "else_n", "ours_low_pct", "themes", "words", "sources", "note"}, keys)
    c.close()
    # S713's keeping still works on the new module
    s, j = post("press", {"state": {"language": "Hindi", "relation": "self"}, "drafts": ["a", "b", "c"]})
    s2, j2 = post("share", {"id": j.get("id"), "which": 1, "how": "shared", "text": "b, edited"})
    check("14 S713's keeping still works: a press and an edited share", s == 200 and s2 == 200 and j2.get("edited") is True, (s, j, s2, j2))
    r = cl.get("/portal/gmb/api/health"); h = r.get_json(silent=True) or {}
    check("15 health says S717", h.get("kit") == "S717" and h.get("presses") == 1, h)

    def refuse(f):
        def w(*a, **k):
            return ("refused", 403)
        w.__name__ = f.__name__
        return w
    cr = make(refuse)
    codes = [cr.get("/portal/gmb/api/watch").status_code,
             cr.post("/portal/gmb/api/watch", data="{}", content_type="application/json", headers=H).status_code,
             cr.post("/portal/gmb/api/snapshot", data="{}", content_type="application/json", headers=H).status_code,
             cr.post("/portal/gmb/api/press", data="{}", content_type="application/json", headers=H).status_code]
    check("16 every door sits behind the gate it is given", codes == [403] * 4, codes)
    src = open(os.path.join(KDIR, "portal_gmb.py"), encoding="utf-8").read()
    check("17 the module writes nowhere but its store", "os.remove" not in src and "shutil" not in src
          and "open(" not in src.replace("io.open(seed_file, encoding=\"utf-8\")", ""), "")
    check("18 the seed file itself is a valid reading with no review text", G.check_reading(seed["taken_on"], seed["data"])[1] is None
          and set(seed["data"]) == {"ours_n", "else_n", "ours_low_pct", "themes", "words", "sources", "note"}, "")

shutil.rmtree(T, ignore_errors=True)
n = len(OK) + len(RED)
print("%d of %d green" % (n, n) if not RED else "%d S717 check(s) red . %d green" % (len(RED), len(OK)))
