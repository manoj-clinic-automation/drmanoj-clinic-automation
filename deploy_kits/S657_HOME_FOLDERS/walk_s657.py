"""walk_s657.py -- kit S657_HOME_FOLDERS (Sanjeevni session S353, 26-Oct-2026). Writes nothing outside --scratch.
Loads the portal code under test and the live one (each with its own tile_grants.json), builds every login's home under every role
with the portal's own functions, renders the home page, and calls the new count door on a copy of finance.db.
  python walk_s657.py --new <dir holding portal/ and finance/ as built> --live <the live root, e.g. /root> --db <a COPY of finance.db>
                      --scratch <dir> [--old] [--lib <root of the unchanged modules>]
  --old: the control -- the live files as 'under test': every S657 check red, every older check green."""
import argparse, importlib.util, json, os, re, shutil, sqlite3, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--live"); ap.add_argument("--db"); ap.add_argument("--scratch"); ap.add_argument("--old", action="store_true")
ap.add_argument("--lib", help="where the unchanged modules the code imports live (default: --live; after placing: /root)")
a = ap.parse_args()
NEW = os.path.abspath(a.live if a.old else a.new)
LIVE = os.path.abspath(a.live)
LIB = os.path.abspath(a.lib or a.live)
os.makedirs(a.scratch, exist_ok=True)
res = []


def check(name, ok, s657=True, note=""):
    res.append((name, bool(ok), s657, str(note)[:400]))


def load_portal(root, tag):
    d = os.path.join(root, "portal")
    os.environ["TILE_GRANTS_FILE"] = os.path.join(d, "tile_grants.json")
    sys.path.insert(0, os.path.join(LIB, "portal"))
    spec = importlib.util.spec_from_file_location("portal_" + tag, os.path.join(d, "portal.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.TILE_GRANTS_FILE = os.path.join(d, "tile_grants.json"); m._GRANTS_CACHE.update(mtime=None, data=None)
    return m


N, L = load_portal(NEW, "new"), load_portal(LIVE, "live")
users = sorted(json.load(open(os.path.join(LIVE, "portal", "tile_grants.json")))["users"]) + ["someone_else"]
ROLES = ("doctor", "manager", "staff")
GONE = {"Daily Sale", "Order Medicines", "Marg Purchases", "Stock milaan"}
STAFF = {"Kal ka hisaab": "Darpan", "Medical sale check": "Bhati", "Amir ka kaam": "Amir", "Aaj ki reports": "Shavez · Shivani",
         "Vaapsi Desk": "Counter"}


def secs(m, u, r):
    m._GRANTS_CACHE.update(mtime=None, data=None)
    return m._visible_sections(r, True, u)


def blocks(m, u, r):
    return m._home_blocks(secs(m, u, r), m._folders_for(u))


def bview(bl):
    return [(lab, [(t["name"], t.get("who")) for t in it], f) for lab, it, f, _s, _i, _d in bl]


def render(m, u, r):
    with m.app.test_request_context("/portal"):
        s = secs(m, u, r)
        return m.render_template_string(m.PORTAL_HTML, sections=s, blocks=m._home_blocks(s, m._folders_for(u)), sso=False,
                                        who={"user": u, "role": r}, role=r, pc=True, s444_nowork=False)


def links(html):
    """(href, name) of every page tile; a folder's own tile (S586's '#g-' link, S657's button) is a folder, not a page."""
    return [x for x in re.findall(r'<a class="tile[^"]*" href="([^"]+)"[^>]*>.*?<div class="nm">([^<]+)</div>', html, re.S)
            if not x[0].startswith("#g-")]


# ---- A: the owner -------------------------------------------------------------------------------------------------------------
mn = {g: [t["name"] for t in ts] for g, ts in secs(N, "manoj", "doctor")}
ml = {g: [t["name"] for t in ts] for g, ts in secs(L, "manoj", "doctor")}
shown = set(sum(mn.values(), []))
check("A1 the owner's home: Daily Sale, Order Medicines, Marg Purchases, Stock milaan are gone", not (GONE & shown), note=sorted(GONE & shown))
want = {g: [x for x in v if x not in GONE] for g, v in ml.items()}
want = {g: v for g, v in want.items() if v}
check("A2 ... and every other tile of his is where it was", {g: sorted(v) for g, v in mn.items()} == {g: sorted(v) for g, v in want.items()})
bv = bview(blocks(N, "manoj", "doctor"))
labs = [b[0] for b in bv]
check("A3 his folders in the mock-up's order (Patients, Surgery, Sanjeevni Medicos, Sanjeevni staff screens, Docterz ...)",
      labs[:5] == ["Patients", "Surgery", "Sanjeevni Medicos", "Sanjeevni staff screens", "Docterz & clinic day"], note=labs)
san = dict((b[0], b) for b in bv).get("Sanjeevni Medicos")
sst = dict((b[0], b) for b in bv).get("Sanjeevni staff screens")
check("A4 his Sanjeevni Medicos folder: approvals (first), purchase orders, vendor payments, stock check, corrections -- folded",
      bool(san) and san[2] and san[1][0][0] == "Sanjeevni Medicos" and sorted(n for n, _w in san[1]) == sorted(["Sanjeevni Medicos", "Purchase orders", "Vendor payments",
                                                                         "Stock Check", "Corrections"]), note=san)
check("A5 his Sanjeevni staff screens folder: the five staff screens, each naming whose screen it is -- folded",
      bool(sst) and sst[2] and dict(sst[1]) == STAFF, note=sst)
# ---- B: everyone else: the same home as today ---------------------------------------------------------------------------------
diff = []
for u in users:
    for r in ROLES:
        if u == "manoj":
            continue
        if bview(blocks(N, u, r)) != bview(blocks(L, u, r)):
            diff.append("%s/%s" % (u, r))
check("B1 every other login under every role: the same folders and tiles, in the same order (%d logins x 3 roles)" % (len(users) - 1),
      not diff, False, ", ".join(diff))
lt = []
for u, r in (("darpan", "staff"), ("shavez", "manager"), ("amir", "staff"), ("bhati", "staff"), ("reception", "staff"), ("bhawna", "doctor")):
    if sorted(links(render(N, u, r))) != sorted(links(render(L, u, r))):
        lt.append("%s/%s" % (u, r))
check("B2 the rendered home of darpan, shavez, amir, bhati, reception and Dr Bhawna holds the same tiles and links", not lt, False, lt)
# ---- C: the rendered page -------------------------------------------------------------------------------------------------------
hm = render(N, "manoj", "doctor")
open(os.path.join(a.scratch, "home_manoj.html"), "w", encoding="utf-8").write(hm)
check("C1 his home has the Expiry watch box, opening /finance/sanjeevni/expiry, next to 'Sanjeevni to approve'",
      re.search(r'chipSanj.*?</a>\s*<a class="chipbox" id="chipExpBox" href="/finance/sanjeevni/expiry"', hm, re.S) is not None)
check("C2 the box reads its number from /finance/sanjeevni/expiry/api/count", "/finance/sanjeevni/expiry/api/count" in hm)
gts = re.findall(r'id="gt-([a-z0-9-]+)"[^>]*aria-controls="g-([a-z0-9-]+)"', hm)
pans = set(re.findall(r'<div class="gpanel" id="g-([a-z0-9-]+)"', hm))
check("C3 every folder is a button with its own panel right after it, closed at rest (%d folders)" % len(gts),
      gts and all(x == y and x in pans for x, y in gts) and len(pans) == len(gts)
      and all(re.search(r'id="g-%s"[^>]*hidden>' % re.escape(x), hm) for x, _y in gts))
check("C4 no full-screen sheet and no Back link is left", 'class="sheet"' not in hm and "Home</a>" not in hm)
check("C5 each panel has a Close button", len(re.findall(r'class="gclose" type="button" data-close=', hm)) == len(gts) and bool(gts))
check("C6 the staff screens panel names whose screen each is", all(('<div class="who">%s</div>' % w) in hm for w in STAFF.values()))
check("C7 the accordion script is in the page and the sheet's hash script is not", "s657_open" in hm and "sheet-open" not in hm)
hd = render(N, "darpan", "staff")
check("C8 a staff login's page carries no Expiry watch box (the strip is the doctor's)", 'id="chipExpBox"' not in hd, False)
hb = render(N, "bhawna", "doctor")
check("C9 Dr Bhawna's folded Staff group opens in place too (her flat tiles first, as before)",
      'id="gt-staff"' in hb and 'id="g-staff"' in hb and 'class="sheet"' not in hb)
# ---- D: the count door, on a copy of finance.db -------------------------------------------------------------------------------
db = os.path.join(a.scratch, "walk.db")
shutil.copyfile(a.db, db)
fin = os.path.join(NEW, "finance")
sys.path[:0] = [fin, os.path.join(LIB, "finance")]
spec = importlib.util.spec_from_file_location("sa_new", os.path.join(fin, "sanjeevni_approvals.py"))
SA = importlib.util.module_from_spec(spec); spec.loader.exec_module(SA)
import flask  # noqa: E402
app = flask.Flask("walk")
who = {"role": "checker"}


def req(*roles):
    if who["role"] in roles:
        return {"user": "manoj", "role": "doctor"}, None
    return None, (flask.jsonify(ok=False, error="not_permitted"), 403)


def getdb():
    c = sqlite3.connect(db); c.row_factory = sqlite3.Row
    return c


SA.init(app, getdb, req)
cl = app.test_client()
r1 = cl.get("/finance/sanjeevni/expiry/api/count")
j = r1.get_json(silent=True) or {}
check("D1 the count door answers the owner (200, ok)", r1.status_code == 200 and j.get("ok") is True, note="%s %s" % (r1.status_code, j))
import expiry_watch as EW  # noqa: E402
c = getdb()
line = " ".join(x["text"] for x in EW.needs_you_lines(c) if x.get("text", "").startswith("Expiry watch"))
nums = [int(x) for x in re.findall(r"(\d+) (?:expired|stop)", line)]
check("D2 its number is his Needs-you line's own two counts added (%s = %s)" % (j.get("n"), line or "no line"),
      j.get("n") == sum(nums) and (j.get("expired", 0) + j.get("stops", 0)) == j.get("n"))
check("D3 it says not to be cached", r1.headers.get("Cache-Control") == "no-store")
who["role"] = "viewer"
r2 = cl.get("/finance/sanjeevni/expiry/api/count")
check("D4 a login the expiry page refuses is refused here too (403)", r2.status_code == 403)
who["role"] = "checker"
r3 = cl.get("/finance/sanjeevni/expiry")
check("D5 the expiry page itself still opens, unchanged", r3.status_code == 200 and b"Expired medicines" in r3.data, False)
n_after = sqlite3.connect(db).execute("SELECT COUNT(*) FROM stock_expiry_run").fetchone()[0]
n_before = sqlite3.connect(a.db).execute("SELECT COUNT(*) FROM stock_expiry_run").fetchone()[0]
check("D6 the door writes nothing (the runs table is as it was)", n_after == n_before, False)
# ---- E: the approvals page links and the grants --------------------------------------------------------------------------------
h_new = open(os.path.join(NEW, "finance", "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
h_old = open(os.path.join(LIVE, "finance", "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
addl = ['href="/finance/purchase/page/staff"', 'href="/finance/purchase/page/hub"', 'href="/finance/stockmatch"']
check("E1 his approvals page, Other pages, links the three pages whose tiles left his home", all(x in h_new for x in addl))
strip = h_new
for x in ('  <a class="ext" href="/finance/purchase/page/staff">Order medicines (the old page) ↗</a> ·\n',
          '  <a class="ext" href="/finance/purchase/page/hub">Marg purchases hub ↗</a> ·\n',
          '  <a class="ext" href="/finance/stockmatch">Stock milaan ↗</a> ·\n'):
    strip = strip.replace(x, "")
check("E2 ... and nothing else on that page changed", strip == h_old, False)
g = json.load(open(os.path.join(NEW, "portal", "tile_grants.json")))
names = {t["name"] for t in N.TILES}
check("E3 tile_grants.json is v40; every masked name is a real tile", g.get("version") == 40 and set(g["users"]["manoj"].get("mask", [])) <= names
      and set(g["users"]["manoj"].get("mask", [])) == GONE)
check("E4 every tile still maps to a group with a face (the portal's own import asserts held)", set(N._TILE_GROUP.values()) <= set(N.GROUP_ORDER), False)

for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if (note and not ok) else ""))
gr = sum(1 for r in res if r[1])
if a.old:
    print("%d S657 check(s) red · %d older red · %d green" % (sum(1 for r in res if r[2] and not r[1]), sum(1 for r in res if not r[2] and not r[1]), gr))
else:
    print("%d of %d green" % (gr, len(res)))
