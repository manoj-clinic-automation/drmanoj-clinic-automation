"""walk_s663.py -- kit S663_PORTAL_CONSOLIDATE (the parent, S358, 26-Oct-2026). Writes nothing outside --scratch.
Loads the portal code under test and the base (S660's TO, fe9cc368), each with the same tile_grants.json, builds every login's home
under every role with the portal's own functions, and renders the home page.
  python walk_s663.py --new <dir holding portal/ as built> --base <dir holding portal/ at fe9cc368> --scratch <dir> [--old] [--lib <root>]
  --old: the control -- the base file as 'under test': every S663 check red, every older check green."""
import argparse, importlib.util, json, os, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--base"); ap.add_argument("--scratch"); ap.add_argument("--old", action="store_true"); ap.add_argument("--lib")
a = ap.parse_args()
NEW = os.path.abspath(a.base if a.old else a.new); BASE = os.path.abspath(a.base); LIB = os.path.abspath(a.lib or a.base)
os.makedirs(a.scratch, exist_ok=True)
res = []


def check(name, ok, s663=True, note=""):
    res.append((name, bool(ok), s663, str(note)[:400]))


def load_portal(root, tag):
    d = os.path.join(root, "portal")
    os.environ["TILE_GRANTS_FILE"] = os.path.join(d, "tile_grants.json")
    sys.path.insert(0, os.path.join(LIB, "portal"))
    spec = importlib.util.spec_from_file_location("portal_" + tag, os.path.join(d, "portal.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.TILE_GRANTS_FILE = os.path.join(d, "tile_grants.json"); m._GRANTS_CACHE.update(mtime=None, data=None)
    return m


N, B = load_portal(NEW, "new"), load_portal(BASE, "base")
users = sorted(json.load(open(os.path.join(BASE, "portal", "tile_grants.json")))["users"]) + ["someone_else"]
ROLES = ("doctor", "manager", "staff")


def secs(m, u, r, pc=True):
    m._GRANTS_CACHE.update(mtime=None, data=None)
    return m._visible_sections(r, pc, u)


def bview(m, u, r, pc=True):
    bl = m._home_blocks(secs(m, u, r, pc), m._folders_for(u))
    return [(lab, [(t["name"], t.get("who"), t.get("url")) for t in it], f) for lab, it, f, _s, _i, _d in bl]


def render(m, u, r):
    with m.app.test_request_context("/portal"):
        s = secs(m, u, r)
        return m.render_template_string(m.PORTAL_HTML, sections=s, blocks=m._home_blocks(s, m._folders_for(u)), sso=False,
                                        who={"user": u, "role": r}, role=r, pc=True, s444_nowork=False)


# ---- W1/W2: nobody's tiles move -- every login (and a stranger) under every role, on the clinic PC and off it
diff, n = [], 0
for u in users:
    for r in ROLES:
        for pc in (True, False):
            n += 1
            x, y = bview(N, u, r, pc), bview(B, u, r, pc)
            if x != y:
                diff.append((u, r, pc))
check("W1 every login x every role x PC/not: the same tiles, folders, order, who-labels and doors as before (%d homes)" % n, not diff, False, note=diff[:4])
errs = []
for u in users:
    for r in ROLES:
        try:
            render(N, u, r)
        except Exception as e:
            errs.append((u, r, repr(e)[:120]))
check("W2 every login's home renders under every role", not errs, False, note=errs[:3])
# ---- W3: the Expiry watch box hides when told to (Dr Bhawna)
hb = render(N, "bhawna", "doctor")
check("W3 Dr Bhawna's home: the Expiry watch box is there and a rule makes 'hidden' hide it", 'id="chipExpBox"' in hb and ".chipbox[hidden]{display:none}" in hb)
check("W3b the rule comes after .chipbox's display:block (so it decides)",
      hb.find(".chipbox[hidden]{display:none}") > hb.find("display:block;transition:border-color .1s}") > 0)
# ---- W4: the two faces on his folded home
hm = render(N, "manoj", "doctor")
check("W4 his home: the Patients folder face reads 'Records · parchi desk · procedures · reports'", "Records · parchi desk · procedures · reports" in hm)
check("W5 his home: the System folder face names WhatsApp approvals", "Board · users · clinic PCs · WhatsApp approvals" in hm)
check("W5b his home: no old face words left", "checks · slips · pending reports" not in hm)
# ---- W6: the Clinic Gist page's card
gist = [v for k, v in vars(N).items() if isinstance(v, str) and 'id="gReports"' in v]
check("W6 the Clinic Gist page: the Reports pending card hides when told to", len(gist) == 1 and "#gReports[hidden]{display:none!important}" in gist[0], note=len(gist))
# ---- W7: the Call Console's Staff tab -- the unused queries gone, and the page never read them
import jinja2, jinja2.meta
env = jinja2.Environment()
cons = getattr(N, "CONSOLE_HTML", "")
undecl = jinja2.meta.find_undeclared_variables(env.parse(cons)) if cons else {"<no CONSOLE_HTML>"}
check("W7 the Call Console template never reads 'staff' (so the queries fed nothing)", cons and "staff" not in undecl, False, note=sorted(undecl)[:10])
check("W7b _query_staff is gone from the portal", not hasattr(N, "_query_staff"))
src = open(os.path.join(NEW, "portal", "portal.py"), encoding="utf-8").read()
check("W7c the Staff tab still builds its week (wk_days, wk_matrix, wk_sd)", 'ctx["wk_days"], ctx["wk_matrix"], ctx["wk_sd"] = wk_days, wk_matrix, sd' in src, False)
open(os.path.join(a.scratch, "home_bhawna_s663.html"), "w", encoding="utf-8").write(hb)
open(os.path.join(a.scratch, "home_manoj_s663.html"), "w", encoding="utf-8").write(hm)
for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if (note and not ok) else ""))
g = sum(1 for x in res if x[1])
if a.old:
    print("%d S663 check(s) red · %d older red · %d green" % (sum(1 for x in res if x[2] and not x[1]), sum(1 for x in res if not x[2] and not x[1]), g))
else:
    print("%d of %d green" % (g, len(res)))
