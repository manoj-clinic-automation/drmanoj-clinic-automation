#!/usr/bin/python3
# walk_s858.py -- kit S858_PATIENTS_TILE (the parent, S478, 17-Nov-2026), D997 item 3.
# Usage: walk_s858.py <portal.py BEFORE> <portal.py AFTER> <tile_grants.json BEFORE> <tile_grants.json AFTER>
# Writes nothing but a temp folder of its own (removed at the end). Stdlib only; no Flask, no network, no store.
# S816's method: it runs the portal's OWN tile code -- portal.py from "TILES = [" to the end of the S586 block (the tile list,
# the groups, _grants_for, _visible_sections, _home_blocks) -- once from each file, with each grants file, and compares what
# every role and every login in the grants file is drawn. The control (BEFORE given as AFTER) must go RED.
# Last line: "WALK OK n/n" or "WALK RED k of n".
import json, os, re, shutil, sys, tempfile, types
B_P, A_P, B_G, A_G = [os.path.abspath(a) for a in sys.argv[1:5]]
T = tempfile.mkdtemp(prefix="s858w.")
START, END = "\nTILES = [\n", "# ---- S586 end"
NEW_T, NEW_G = "Patients — month by month", "Patients by month"
RES = []


def ck(name, ok, why=""):
    RES.append(bool(ok))
    print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)[:300]) if (why and not ok) else ""))


RING = types.ModuleType("ring_outcome"); RING.list_on = lambda: True
sys.modules["ring_outcome"] = RING


def load(path, tag):
    src = open(path, encoding="utf-8").read()
    i, j = src.index(START), src.index(END)
    os.environ["TILE_GRANTS_FILE"] = os.path.join(T, "none.json")
    ns = {"os": os, "re": re, "json": json, "__file__": os.path.join(T, tag + "_portal.py"), "__name__": "s858_" + tag}
    exec(compile(src[i:j], tag, "exec"), ns)
    return ns


def use_grants(ns, path):
    ns["TILE_GRANTS_FILE"] = path
    ns["_GRANTS_CACHE"].update(mtime=None, data=None)


def secs(ns, role, pc, user):
    return [(g, [t["name"] for t in items]) for g, items in ns["_visible_sections"](role, pc, user)]


def blocks(ns, role, pc, user):
    return [(l, [t["name"] for t in it], f) for l, it, f, _s, _i, _d in ns["_home_blocks"](ns["_visible_sections"](role, pc, user), ns["_folders_for"](user))]


try:
    B = load(B_P, "before")
    A = load(A_P, "after")
    gb = os.path.join(T, "gb.json"); shutil.copy(B_G, gb)
    ga = os.path.join(T, "ga.json"); shutil.copy(A_G, ga)
    use_grants(B, gb); use_grants(A, ga)
    tile = [t for t in A["TILES"] if t["name"] == NEW_T]
    ck("1 the new tile exists once, a doctor tile by role, opening the Patients page",
       len(tile) == 1 and tile[0]["roles"] == ["doctor"] and tile[0]["url"] == "/finance/console/patients" and tile[0].get("live"), tile)
    ck("2 its group is 'Patients by month', placed right after Patients, and has a face",
       tile and tile[0].get("group") == NEW_G and A["GROUP_ORDER"][:2] == ["Patients", NEW_G] and NEW_G in A["GROUP_META"])
    ck("3 the tile list is the old one plus this tile, nothing else changed",
       [t for t in A["TILES"] if t["name"] != NEW_T] == B["TILES"])
    users = sorted(json.load(open(A_G, encoding="utf-8")).get("users", {}))
    diffs, saw_new = [], []
    for role in ("doctor", "manager", "staff"):
        for u in [""] + users:
            for pc in (False, True):
                b, a = secs(B, role, pc, u), secs(A, role, pc, u)
                a_wo = [(g, [n for n in names if n != NEW_T]) for g, names in a]
                a_wo = [(g, names) for g, names in a_wo if names]
                if a_wo != b:
                    diffs.append((role, u, pc))
                if any(NEW_T in names for _g, names in a):
                    saw_new.append((role, u))
    ck("4 for every role x every login x PC/phone, everything else is drawn exactly as before", not diffs, diffs[:3])
    ck("5 the new tile is drawn only for the doctor role", saw_new and all(r == "doctor" for r, _u in saw_new), saw_new[:5])
    m = blocks(A, "doctor", False, "manoj")
    names = [l for l, _n, _f in m]
    blk = [x for x in m if x[0] == NEW_G]
    ck("6 his folded home: the tile sits right after the Patients folder", names[:2] == ["Patients", NEW_G], names[:4])
    ck("7 ... drawn flat (a group of one is a plain tile, not a folder)", blk and blk[0][1] == [NEW_T] and blk[0][2] is False, blk)
    mb = blocks(B, "doctor", False, "manoj")
    ck("8 ... and every other block of his home is as before", [x for x in m if x[0] != NEW_G] == mb, "")
    only = json.load(open(A_G, encoding="utf-8"))["users"].get("bhawna", {}).get("only")
    ck("9 Dr Bhawna's 'only' list keeps her home as it was (no new tile)", only is None or not any(NEW_T in n for _g, n in secs(A, "doctor", False, "bhawna")))
    use_grants(A, os.path.join(T, "missing.json")); use_grants(B, os.path.join(T, "missing.json"))
    fa, fb = secs(A, "doctor", False, "walk_x"), secs(B, "doctor", False, "walk_x")
    ck("10 with no grants file at all (the fallback), the doctor still gets the tile after Patients, staff do not",
       [g for g, _n in fa][:2] == ["Patients", NEW_G] and not any(NEW_T in n for _g, n in secs(A, "staff", False, "walk_x"))
       and [(g, [x for x in n if x != NEW_T]) for g, n in fa if [x for x in n if x != NEW_T]] == fb)
    gb_j, ga_j = json.load(open(B_G, encoding="utf-8")), json.load(open(A_G, encoding="utf-8"))
    ga_cmp = json.loads(json.dumps(ga_j)); gb_cmp = json.loads(json.dumps(gb_j))
    ga_cmp["users"]["manoj"]["groups"] = [x for x in ga_cmp["users"]["manoj"]["groups"] if x != NEW_G]
    for d in (ga_cmp, gb_cmp):
        d.pop("_note", None); d.pop("version", None)
    ck("11 tile_grants.json: only manoj's order gains the group (after Patients), the version moves by one, the note grows",
       ga_cmp == gb_cmp and ga_j["users"]["manoj"]["groups"][:2] == ["Patients", NEW_G] and ga_j["version"] == gb_j["version"] + 1
       and ga_j["_note"].startswith(gb_j["_note"]))
    raw = open(A_G, encoding="utf-8").read()
    ck("12 tile_grants.json is written in its own format (indent 1, UTF-8, newline at the end)",
       raw == json.dumps(ga_j, indent=1, ensure_ascii=False) + "\n")
except Exception as e:
    ck("CRASH in the walk", False, "%s: %s" % (e.__class__.__name__, e))
finally:
    shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
sys.exit(1 if bad else 0)
