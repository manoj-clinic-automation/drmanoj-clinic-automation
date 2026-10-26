"""walk_s660.py -- kit S660_HOME_DECLUTTER (the parent, S357, 26-Oct-2026). Writes nothing outside --scratch.
Loads the portal code under test (S660 TO) and the base (S657 TO), each with its own tile_grants.json, builds every login's home under
every role with the portal's own functions and renders the home page.
  python walk_s660.py --new <dir holding portal/ as built> --base <dir holding portal/ at S657's TO> --scratch <dir> [--old] [--lib <root of the unchanged modules>]
  --old: the control -- the base files as 'under test': every S660 check red, every older check green."""
import argparse, importlib.util, json, os, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--base"); ap.add_argument("--scratch"); ap.add_argument("--old", action="store_true"); ap.add_argument("--lib")
a = ap.parse_args()
NEW = os.path.abspath(a.base if a.old else a.new); BASE = os.path.abspath(a.base); LIB = os.path.abspath(a.lib or a.base)
os.makedirs(a.scratch, exist_ok=True)
res = []


def check(name, ok, s660=True, note=""):
    res.append((name, bool(ok), s660, str(note)[:400]))


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
GONE = {"Clinic", "OPD & X-ray/Proc Slips", "Clinic Gist"}
WHO = {"Parchi desk": "Shavez", "Kal ke procedures": "Shavez", "Physiotherapy": "Bhati", "Petty book": "Bhati",
       "Check karein": "staff", "Report baaki": "staff", "Docterz daily collection": "reception"}


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


# ---- the owner's home
nb, bb = bview(blocks(N, "manoj", "doctor")), bview(blocks(B, "manoj", "doctor"))
names_n = {n for _l, it, _f in nb for n, _w in it}; names_b = {n for _l, it, _f in bb for n, _w in it}
check("W1 his home: Clinic, OPD & X-ray/Proc Slips, Clinic Gist are gone", not (GONE & names_n), note=sorted(GONE & names_n))
check("W2 his home: Attendance correction is in the Staff folder, after Salary", any(l == "Staff" and [n for n, _ in it][-2:] == ["Salary — approve & lock", "Attendance correction"]
      or (l == "Staff" and "Attendance correction" in [n for n, _ in it]) for l, it, _f in nb), note=[(l, [n for n, _ in it]) for l, it, _f in nb if l == "Staff"])
check("W3 his home: WhatsApp Approvals sits in System, not in Calls & WhatsApp",
      any(l == "System" and "WhatsApp Approvals" in [n for n, _ in it] for l, it, _f in nb) and not any(l == "Calls & WhatsApp" and "WhatsApp Approvals" in [n for n, _ in it] for l, it, _f in nb))
who_n = {n: w for _l, it, _f in nb for n, w in it}
check("W4 his home: the seven staff screens carry whose they are", all(who_n.get(n) == w for n, w in WHO.items()), note={n: who_n.get(n) for n in WHO})
check("W5 his home: every other tile where it was (name, folder, order), Sanjeevni folders untouched",
      [(l, [n for n, _ in it if n not in GONE and n != "Attendance correction" and n != "WhatsApp Approvals"]) for l, it, _f in bb]
      == [(l, [n for n, _ in it if n != "Attendance correction" and n != "WhatsApp Approvals"]) for l, it, _f in nb])
check("W6 his home: the Sanjeevni folders and their who-labels are exactly S657's", [(l, it) for l, it, _f in nb if "Sanjeevni" in l] == [(l, it) for l, it, _f in bb if "Sanjeevni" in l], False)
# ---- everyone else: nothing changes
diff, seen_moved = [], []
for u in users:
    if u == "manoj":
        continue
    for r in ROLES:
        x, y = bview(blocks(N, u, r)), bview(blocks(B, u, r))
        xs = [(l, sorted(n for n, _ in it)) for l, it, _f in x]; ys = [(l, sorted(n for n, _ in it)) for l, it, _f in y]
        MOVED = {"Attendance correction", "WhatsApp Approvals"}                 # the two tiles this kit adds or moves: judged apart
        xs2 = [(l, [n for n in ns if n not in MOVED]) for l, ns in xs]; ys2 = [(l, [n for n in ns if n not in MOVED]) for l, ns in ys]
        if xs2 != ys2:
            diff.append((u, r, [p for p in xs2 if p not in ys2][:2]))
        if any("WhatsApp Approvals" in ns or "Attendance correction" in ns for _l, ns in xs) and u != "manoj":
            seen_moved.append((u, r))
check("W7 every other login under every role: the same tiles in the same folders (%d logins x 3 roles), the two added/moved tiles judged apart" % (len(users) - 1), not diff, False, note=diff[:3])
check("W7b the added/moved tiles reach no REAL login but his: only the doctor ROLE tried on other names sees them (Dr Bhawna's 'only' list hides them)",
      all(r == "doctor" for _u, r in seen_moved) and ("bhawna", "doctor") not in seen_moved, note=seen_moved[:6])
# ---- Dr Bhawna never sees the new tile (her 'only' list)
bh = {n for _l, it, _f in bview(blocks(N, "bhawna", "doctor")) for n, _w in it}
check("W8 Dr Bhawna's home: no Attendance correction, no WhatsApp Approvals", not ({"Attendance correction", "WhatsApp Approvals"} & bh), False, note=sorted(bh)[:8])
# ---- the rendered page
h = render(N, "manoj", "doctor")
check("W9 the rendered home: the Attendance correction tile with its door; the who labels in the panels; no sheet, no Back (S657 kept)",
      '/register/attcorr' in h and h.count('<div class="who">') >= 5 + 7 and 'class="gpanel"' in h and '>Back<' not in h, note="who=%d attcorr=%s" % (h.count('<div class="who">'), '/register/attcorr' in h))
check("W10 the rendered home: nothing named Clinic Gist / OPD & X-ray/Proc Slips remains, and the review page (Clinic) is not linked",
      '<div class="nm">Clinic Gist</div>' not in h and "OPD &amp; X-ray/Proc Slips" not in h and 'href="/finance/clinic/review"' not in h)
hs = render(N, "shavez", "manager")
check("W11 Shavez's rendered home: no who-labels (his list is flat), his tiles as before", '<div class="who">' not in hs and hs.count('class="tile') == render(B, "shavez", "manager").count('class="tile'), False)
open(os.path.join(a.scratch, "home_manoj_s660.html"), "w", encoding="utf-8").write(h)
for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if (note and not ok) else ""))
g = sum(1 for x in res if x[1])
if a.old:
    print("%d S660 check(s) red · %d older red · %d green" % (sum(1 for x in res if x[2] and not x[1]), sum(1 for x in res if not x[2] and not x[1]), g))
else:
    print("%d of %d green" % (g, len(res)))
