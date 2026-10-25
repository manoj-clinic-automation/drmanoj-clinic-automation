"""walk_s646.py -- kit S646_PROCROOM_TILES (S349, the parent, 25-Oct-2026). Loads the portal code under test and the live one, each with
its own tile_grants.json, and draws every login's home sections (_visible_sections, the function the home page uses) under every
role. Writes nothing.
  python walk_s646.py <dir with portal.py + tile_grants.json under test> <dir with the LIVE portal.py + tile_grants.json> [--old]
  --old: the control -- run with the live files as 'under test': every S646 check red, every older check green."""
import importlib.util, json, os, sys, warnings
warnings.filterwarnings("ignore")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
NEW, LIVE = os.path.abspath(args[0]), os.path.abspath(args[1])
OLD = "--old" in sys.argv

def load(d, tag):
    os.environ["TILE_GRANTS_FILE"] = os.path.join(d, "tile_grants.json")
    sys.path.insert(0, LIVE)
    spec = importlib.util.spec_from_file_location("portal_" + tag, os.path.join(d, "portal.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.TILE_GRANTS_FILE = os.path.join(d, "tile_grants.json"); m._GRANTS_CACHE.update(mtime=None, data=None)
    return m

N, L = load(NEW, "new"), load(LIVE, "live")
users = sorted(json.load(open(os.path.join(LIVE, "tile_grants.json")))["users"]) + ["someone_else"]
ROLES = ("doctor", "manager", "staff")

def home(m, u, r):
    m._GRANTS_CACHE.update(mtime=None, data=None)
    return {g: [t["name"] for t in ts] for g, ts in m._visible_sections(r, True, u)}

res = []
def check(name, ok, s646=True, note=""):
    res.append((name, bool(ok), s646, note))

tn = {t["name"]: t for t in N.TILES}
k = tn.get("Kal ke procedures"); p = tn.get("Procedure room")
check("A1 'Kal ke procedures' opens /scanapp/procroom/morning, in Patients", bool(k) and k["url"] == "/scanapp/procroom/morning" and k.get("group") == "Patients")
check("A2 'Procedure room' opens /scanapp/procroom, in Assets & papers", bool(p) and p["url"] == "/scanapp/procroom" and p.get("group") == "Assets & papers")
sh = {r: home(N, "shavez", r) for r in ROLES}
check("A3 Shavez's home shows 'Kal ke procedures' under every role he could hold", all("Kal ke procedures" in sh[r].get("Patients", []) for r in ("manager", "staff")))
check("A4 ... and never 'Procedure room' (the owner's rates page)", all("Procedure room" not in sum(sh[r].values(), []) for r in ("manager", "staff")))
mj = home(N, "manoj", "doctor")
check("A5 the owner's home: 'Procedure room' in Assets & papers, 'Kal ke procedures' in Patients",
      "Procedure room" in mj.get("Assets & papers", []) and "Kal ke procedures" in mj.get("Patients", []))
bw = home(N, "bhawna", "doctor")
check("A6 Dr Bhawna's home shows neither new tile", "Procedure room" not in sum(bw.values(), []) and "Kal ke procedures" not in sum(bw.values(), []))
gf = json.load(open(os.path.join(NEW, "tile_grants.json")))
check("A7 tile_grants.json is v39", gf.get("version") == 39)
# every other login, every role: the same home as the live code
diff = []
for u in users:
    for r in ROLES:
        a, b = home(N, u, r), home(L, u, r)
        for t in ("Kal ke procedures", "Procedure room"):
            for d in (a,):
                for g in list(d):
                    d[g] = [x for x in d[g] if not (x == t and ((u == "shavez" and t == "Kal ke procedures" and r != "doctor") or r == "doctor"))]
        a = {g: v for g, v in a.items() if v}; b = {g: v for g, v in b.items() if v}
        if a != b:
            diff.append("%s/%s" % (u, r))
check("A8 every other tile of every login under every role is as before (%d logins x 3 roles)" % len(users), not diff, False, ", ".join(diff)[:300])
check("A9 every tile still maps to a group with a face (the portal's own import asserts held)", set(N._TILE_GROUP.values()) <= set(N.GROUP_ORDER), False)
check("A10 the Assets & papers face names the procedure room", "procedure room" in N.GROUP_META["Assets & papers"][1])

for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if note else ""))
g = sum(1 for r in res if r[1])
if OLD:
    print("%d S646 check(s) red · %d older red · %d green" % (sum(1 for r in res if r[2] and not r[1]), sum(1 for r in res if not r[2] and not r[1]), g))
else:
    print("%d of %d green" % (g, len(res)))
