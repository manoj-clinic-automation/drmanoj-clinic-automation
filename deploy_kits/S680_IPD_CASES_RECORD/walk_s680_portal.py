"""walk_s680_portal.py -- kit S680_IPD_CASES_RECORD (the parent, S368, 29-Oct-2026, D801; final S370, 30-Oct-2026, D804). Writes nothing outside --scratch.
The tile 'Surgery cases' is renamed 'IPD cases' in portal.py, and tile_grants.json follows the name (shavez's grant, bhawna's
mask). Loads the portal under test and the base (portal.py 1e0c6548 with grants v41 83828b81), each with ITS OWN tile_grants.json,
builds every login's home under every role, on the clinic PC and off it, with the portal's own functions, and renders the homes.
Also checks the Case Pack page: the one link's words changed, nothing else.
  python walk_s680_portal.py --new <dir holding portal/ and casepack_page.html as built> --base <dir holding the same, live>
                             --lib <root holding portal/ (the live portal's other modules)> --scratch <dir> [--old]
  --old: the control -- the base files as 'under test': every S680 check red, every older check green."""
import argparse, importlib.util, json, os, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--base"); ap.add_argument("--scratch"); ap.add_argument("--old", action="store_true"); ap.add_argument("--lib")
a = ap.parse_args()
NEW = os.path.abspath(a.base if a.old else a.new); BASE = os.path.abspath(a.base); LIB = os.path.abspath(a.lib or a.base)
os.makedirs(a.scratch, exist_ok=True)
res = []
OLDN, NEWN = "Surgery cases", "IPD cases"


def check(name, ok, s680=True, note=""):
    res.append((name, bool(ok), s680, str(note)[:400]))


def load_portal(root, tag):
    d = os.path.join(root, "portal")
    os.environ["TILE_GRANTS_FILE"] = os.path.join(d, "tile_grants.json")
    if os.path.join(LIB, "portal") not in sys.path:
        sys.path.insert(0, os.path.join(LIB, "portal"))
    spec = importlib.util.spec_from_file_location("portal_" + tag, os.path.join(d, "portal.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.TILE_GRANTS_FILE = os.path.join(d, "tile_grants.json"); m._GRANTS_CACHE.update(mtime=None, data=None)
    return m


N, B = load_portal(NEW, "new"), load_portal(BASE, "base")
users = sorted(set(json.load(open(os.path.join(BASE, "portal", "tile_grants.json")))["users"]) | {"manoj", "shavez"}) + ["someone_else"]
ROLES = ("doctor", "manager", "staff")


def secs(m, u, r, pc=True):
    m._GRANTS_CACHE.update(mtime=None, data=None)
    return m._visible_sections(r, pc, u)


def bview(m, u, r, pc=True, rename=False):
    bl = m._home_blocks(secs(m, u, r, pc), m._folders_for(u))
    nm = (lambda x: NEWN if (rename and x == OLDN) else x)
    return [(lab, [(nm(t["name"]), t.get("who"), t.get("url")) for t in it], f) for lab, it, f, _s, _i, _d in bl]


def names(m, u, r, pc=True):
    return {t["name"] for _lab, it, _f, _s, _i, _d in m._home_blocks(secs(m, u, r, pc), m._folders_for(u)) for t in it}


def render(m, u, r):
    with m.app.test_request_context("/portal"):
        s = secs(m, u, r)
        return m.render_template_string(m.PORTAL_HTML, sections=s, blocks=m._home_blocks(s, m._folders_for(u)), sso=False,
                                        who={"user": u, "role": r}, role=r, pc=True, s444_nowork=False)


# ---- P1: nobody's home changes except the one tile's name
diff, n, had, has = [], 0, 0, 0
for u in users:
    for r in ROLES:
        for pc in (True, False):
            n += 1
            x, y = bview(N, u, r, pc, rename=True), bview(B, u, r, pc, rename=True)     # the name aside, nothing moves
            if x != y:
                diff.append((u, r, pc))
            had += OLDN in names(B, u, r, pc)
            has += NEWN in names(N, u, r, pc)
check("P1 every login x every role x PC/not: the same tiles, folders, order, who-labels and doors, the one tile renamed (%d homes)" % n,
      not diff, False, note=diff[:4])
check("P2 'IPD cases' is on exactly the homes that had 'Surgery cases' (%d of %d), and 'Surgery cases' on none" % (had, n),
      had > 0 and has == had and not any(OLDN in names(N, u, r, pc) for u in users for r in ROLES for pc in (True, False)), note=(had, has))
check("P3 Shavez (by his grant, any role) and the doctor see IPD cases; Dr Bhawna (masked) does not",
      NEWN in names(N, "shavez", "staff") and NEWN in names(N, "manoj", "doctor") and NEWN not in names(N, "bhawna", "doctor"))
errs = []
for u in users:
    for r in ROLES:
        try:
            render(N, u, r)
        except Exception as e:                   # noqa: BLE001
            errs.append((u, r, repr(e)[:120]))
check("P4 every login's home renders under every role", not errs, False, note=errs[:3])
hm, hs = render(N, "manoj", "doctor"), render(N, "shavez", "staff")
check("P5 his home and Shavez's say IPD cases, never Surgery cases", NEWN in hm and NEWN in hs and OLDN not in hm and OLDN not in hs)
check("P5b the Surgery folder's face reads 'Case pack · IPD cases'", "Case pack · IPD cases" in getattr(N, "GROUP_META", {}).get("Surgery", ("", ""))[1])
g = json.load(open(os.path.join(NEW, "portal", "tile_grants.json"), encoding="utf-8"))
g0 = json.load(open(os.path.join(BASE, "portal", "tile_grants.json"), encoding="utf-8"))
ren = lambda o: json.loads(json.dumps(o, ensure_ascii=False).replace('"%s"' % OLDN, '"%s"' % NEWN))
check("P6 tile_grants.json: version 42, the name followed in shavez's grant and bhawna's mask, every other grant, mask and default as before",
      g.get("version") == 42 and {k: g[k] for k in g if k not in ("_note", "version")} == ren({k: g0[k] for k in g0 if k not in ("_note", "version")})
      and OLDN not in json.dumps({k: g[k] for k in g if k != "_note"}) and NEWN in g["users"]["shavez"].get("extra", [])
      and NEWN in g["users"]["bhawna"].get("mask", []) and g["_note"].startswith(g0["_note"]))
cp_new = open(os.path.join(NEW, "casepack_page.html"), encoding="utf-8").read()
cp_old = open(os.path.join(BASE, "casepack_page.html"), encoding="utf-8").read()
MOBUID = "+'&uid='+encodeURIComponent(pbSel.Patient_UID||'')"     # the UID only: the number is looked up on the server, never in an address
check("P7 [S370 D804] the Case Pack's link reads 'Continue to IPD case' and also carries the patient's UID (the IPD form looks up the full mobile from it); "
      "nothing else on that page changed",
      "Continue to IPD case (papers" in cp_new and "Continue to surgery case" not in cp_new and cp_new.count(MOBUID) == 1
      and cp_new.replace("Continue to IPD case (papers", "Continue to surgery case (papers").replace(MOBUID, "") == cp_old)
open(os.path.join(a.scratch, "home_manoj_s680.html"), "w", encoding="utf-8").write(hm)
for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if (note and not ok) else ""))
gr = sum(1 for x in res if x[1])
if a.old:
    print("%d S680 check(s) red · %d older red · %d green" % (sum(1 for x in res if x[2] and not x[1]), sum(1 for x in res if not x[2] and not x[1]), gr))
else:
    print("%d of %d green" % (gr, len(res)))
