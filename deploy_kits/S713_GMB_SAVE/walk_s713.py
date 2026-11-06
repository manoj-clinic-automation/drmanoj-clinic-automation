# walk_s713.py -- kit S713_GMB_SAVE (session 389, the parent, 06-Nov-2026)
# The GMB keeping on a MADE-UP root: portal_gmb.py mounted on a bare Flask app with a temp store -- never the live one.
# It also proves the kit's portal.py is the live portal.py plus the one mount block, byte for byte.
#   python walk_s713.py <dir with portal_gmb.py + portal.py (new or live)> <the live portal.py>
#   last line: "N of N green"  (or "X S713 check(s) red . Y green")
import io, json, os, re, shutil, sqlite3, sys, tempfile

# made-up phone numbers are built at run time: the publish gate (NO_PHONE_NUMBERS) refuses any number in the files
A5, B5 = "9876" + "5", "4321" + "0"
PH = A5 + B5
KDIR = os.path.abspath(sys.argv[1]); LIVE_PORTAL = os.path.abspath(sys.argv[2])
T = tempfile.mkdtemp(prefix="s713walk_")
DB = os.path.join(T, "gmb_store.db")
OK, RED = [], []


def check(label, cond, why=""):
    (OK if cond else RED).append(label)
    print(("GREEN " if cond else "RED   ") + label + ("" if cond else "  -- " + str(why)[:200]))


BLOCK_START = "\n\n# S713 (the parent, S389, 06-Nov-2026; D832 Part B)"
BLOCK_END = '    GMB_SAVE_IMPORT_ERR = str(_gs_e)\n'
# 1 portal.py = the live file + the one block
new_p = io.open(os.path.join(KDIR, "portal.py"), encoding="utf-8", newline="").read()
live_p = io.open(LIVE_PORTAL, encoding="utf-8", newline="").read()
i = new_p.find(BLOCK_START); j = new_p.find(BLOCK_END, i if i >= 0 else 0)
check("1 portal.py is the live file plus the one mount block, nothing else",
      i >= 0 and j > i and new_p.count(BLOCK_START) == 1 and new_p[:i] + new_p[j + len(BLOCK_END):] == live_p,
      "block %s / rest differs" % ("found" if i >= 0 else "not found"))
check("2 the block mounts portal_gmb behind doctor_required, inside a try",
      i >= 0 and "import portal_gmb" in new_p[i:j] and "app, doctor_required," in new_p[i:j] and "\ntry:\n" in new_p[i:j])

mod = os.path.join(KDIR, "portal_gmb.py")
if not os.path.exists(mod):
    for n in range(3, 15):
        check("%d (portal_gmb.py is not there)" % n, False, "no module")
else:
    STAGE = os.path.join(T, "code"); os.makedirs(STAGE); shutil.copy(mod, STAGE)
    sys.path.insert(0, STAGE); sys.dont_write_bytecode = True
    from flask import Flask
    import portal_gmb as G

    def allow(f):
        return f

    def make(guard):
        app = Flask("s713walk_%s" % id(guard))
        G.register(app, guard, lambda: "manoj", lambda k, d="": DB if k == "GMB_STORE_DB" else d)
        return app.test_client()

    cl = make(allow)
    H = {"X-Gmb": "1"}
    st = {"relation": "mother", "language": "Hindi", "problems": ["knee"], "good": ["pain"], "qualities": [],
          "ayushman": False, "bone": None, "side": None, "surgery": {}, "knee": [], "other": "call %s %s" % (A5, B5),
          "extra": ["(%s) %s" % (A5, B5), "+91 %s.%s" % (A5, B5), A5 + "\u2013" + B5], "n": int(PH)}
    D = ["छोटा draft", "Medium draft, phone %s inside" % PH, "Long draft text here"]

    def post(path, b, h=H):
        r = cl.post("/portal/gmb/api/" + path, data=json.dumps(b), content_type="application/json", headers=h)
        return r.status_code, (r.get_json(silent=True) or {})

    s, j1 = post("press", {"state": st, "drafts": D}, h={})
    check("3 a save without the page's own header is refused (403)", s == 403, (s, j1))
    s, j1 = post("press", {"state": st, "drafts": D[:2]})
    check("4 a press with two drafts is refused (400)", s == 400, (s, j1))
    s, j1 = post("press", {"state": st, "drafts": D})
    pid = j1.get("id")
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    row = c.execute("SELECT * FROM press WHERE id=?", (pid,)).fetchone() if pid else None
    check("5 a press is kept: the drafts as generated, the ticks, language, relation, IST time, kit S713",
          s == 200 and row is not None and row["d0"] == D[0] and row["d2"] == D[2] and row["lang"] == "Hindi"
          and row["relation"] == "mother" and json.loads(row["state"])["problems"] == ["knee"]
          and row["at"].endswith("+05:30") and row["kit"] == "S713" and row["who"] == "manoj",
          (s, j1, dict(row) if row else None))
    sj = json.loads(row["state"]) if row is not None else {}
    check("6 no phone number is kept (a draft; the ticks in 5 typed forms and as a bare number), and the ticks stay valid JSON",
          row is not None and PH not in row["d1"] and "[number]" in row["d1"]
          and sj.get("other") == "call [number]" and sj.get("extra") == ["[number]"] * 3 and sj.get("n") is None
          and not any(ch.isdigit() for ch in "".join(sj.get("extra", []))),
          (row["d1"], row["state"]) if row else None)
    s, j2 = post("share", {"id": pid, "which": 0, "how": "copied", "text": D[0]})
    check("7 a copy of the draft as it was is kept as not edited", s == 200 and j2.get("edited") is False, (s, j2))
    s, j3 = post("share", {"id": pid, "which": 2, "how": "shared", "text": "Long draft text here, edited by sir"})
    sh = c.execute("SELECT * FROM share WHERE press_id=? AND how='shared'", (pid,)).fetchone()
    check("8 Shared after an edit keeps the text as shared, marked edited",
          s == 200 and j3.get("edited") is True and sh is not None and sh["text"].endswith("edited by sir")
          and sh["which"] == 2 and sh["at"].endswith("+05:30"), (s, j3))
    s, j4 = post("share", {"id": pid, "which": 1, "how": "whatsapp", "text": "ring %s please" % PH})
    w = c.execute("SELECT text FROM share WHERE how='whatsapp'").fetchone()
    check("9 WhatsApp is kept, without a phone number", s == 200 and w is not None and PH not in w["text"], (s, j4))
    bad = [post("share", {"id": pid, "which": 3, "how": "shared", "text": "x"})[0],
           post("share", {"id": pid, "which": 0, "how": "posted", "text": "x"})[0],
           post("share", {"id": 99999, "which": 0, "how": "shared", "text": "x"})[0],
           post("share", {"id": pid, "which": 0, "how": "shared", "text": "x" * 5000})[0]]
    check("10 a wrong draft number, a wrong kind, an unknown press and an over-long text are refused",
          bad == [400, 400, 404, 400], bad)
    r = cl.get("/portal/gmb/api/health"); h = r.get_json(silent=True) or {}
    check("11 health counts 1 press, 3 shares, 2 edited (the Shared one and the WhatsApp one)",
          h.get("kit") == "S713" and h.get("presses") == 1 and h.get("shares") == 3 and h.get("edited") == 2, h)
    c.close()

    def refuse(f):
        def w(*a, **k):
            return ("refused", 403)
        w.__name__ = f.__name__
        return w
    cr = make(refuse)
    codes = [cr.post("/portal/gmb/api/press", data="{}", content_type="application/json", headers=H).status_code,
             cr.post("/portal/gmb/api/share", data="{}", content_type="application/json", headers=H).status_code,
             cr.get("/portal/gmb/api/health").status_code]
    check("12 every door sits behind the gate it is given (a refusing gate refuses all three)", codes == [403, 403, 403], codes)
    src = io.open(mod, encoding="utf-8").read()
    check("13 the store is a .db file (the nightly code bundle carries no .db)",
          '"/root/portal/gmb_store.db"' in src and DB.endswith(".db"))
    check("14 the module writes nowhere but its store (no open() for writing, no os.remove)",
          not re.search(r"open\([^)]*['\"][wa]", src) and "os.remove" not in src and "shutil" not in src)

shutil.rmtree(T, ignore_errors=True)
n = len(OK) + len(RED)
print("%d of %d green" % (n, n) if not RED else "%d S713 check(s) red . %d green" % (len(RED), len(OK)))
