#!/usr/bin/env python3
"""walk_s447.py -- walk for S447_RATE_GROUPS.
usage: walk_s447.py <original (S441)> <patched copy> [<finance.db>]
Proves on the LIVE SHAPE -- the 28 procedure lines exactly as the rate page had them on 02-Oct, in the order
services() hands them over -- that the original page shows 'Cast / slab' three times (the negative control: the
walk must be able to see the fault) and the patched page shows every group once, in the owner's order, every line
once, each site's cast directly above its slab; that a line waiting for his call opens its group and comes first;
that the X-ray section is rendered byte for byte as before; and that the file is unchanged outside the one edit.
With a third argument (on the box: the live finance.db, opened READ-ONLY) the same group checks run on the real
rows, read with services()'s own ORDER BY. No network, nothing written. Prints WALK OK n/n."""
import importlib.util
import re
import sqlite3
import sys
import types

ORIG, NEW = sys.argv[1], sys.argv[2]
DB = sys.argv[3] if len(sys.argv) > 3 else None
N = [0, 0]


def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1
        print("  ok  %s" % name)
    else:
        print("  RED %s %s" % (name, extra))


try:
    import flask  # noqa: F401
except ImportError:                      # the PC's shell has no flask; the page builder never calls it
    f = types.ModuleType("flask")
    f.Blueprint = lambda *a, **k: types.SimpleNamespace(route=lambda *a, **k: (lambda fn: fn))
    f.jsonify = f.redirect = lambda *a, **k: None
    f.request = types.SimpleNamespace(values={}, form={}, headers={})
    sys.modules["flask"] = f


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


o_src = open(ORIG, encoding="utf-8").read()
n_src = open(NEW, encoding="utf-8").read()
A = "    else:\n        groups = []\n"
B = "        for g, items in groups:\n"
A2 = "    else:\n        by = {}"
check("outside the one edit the file is the original byte for byte",
      A in o_src and A2 in n_src and o_src[:o_src.index(A)] == n_src[:n_src.index(A2)]
      and o_src[o_src.index(B):] == n_src[n_src.index(B):])
compile(n_src, NEW, "exec")
check("compiles", True)
O, P = load(ORIG, "os_orig_s447"), load(NEW, "os_new_s447")
check("loads", hasattr(P, "_section_html") and hasattr(P, "services"))
ORDER_BY = "seen DESC, name"
check("services() still hands rows over by status, seen, name (the order this walk replays)", ORDER_BY in n_src)

CS, ILI = "Cast / slab", "Injection (ILI)"
LIVE = [("stitch removal", ""), ("A/E (Above elbow) fibre cast", CS), ("A/E (Above elbow) fibre slab", CS),
        ("A/K (Above knee) fibre cast", CS), ("A/K (Above knee) fibre slab", CS), ("B/E (Below elbow) fibre cast", CS),
        ("B/E (Below elbow) fibre slab", CS), ("B/K (Below knee) fibre cast", CS), ("B/K (Below knee) fibre slab", CS),
        ("CYL (Cylinder) fibre cast", CS), ("CYL (Cylinder) fibre slab", CS), ("Clavicle bandage", CS),
        ("HBK (High below knee) fibre cast", CS), ("HBK (High below knee) fibre slab", CS),
        ("SBE (Short below elbow) fibre cast", CS), ("SBE (Short below elbow) fibre slab", CS),
        ("SBK (Short below knee) fibre cast", CS), ("SBK (Short below knee) fibre slab", CS),
        ("SPICA (Thumb spica) fibre cast", CS), ("SPICA (Thumb spica) fibre slab", CS), ("U fibre cast", CS),
        ("U fibre slab", CS), ("Dressing", "Dressing"), ("ILI (elbow)", ILI), ("ILI (heel)", ILI),
        ("ILI (shoulder)", ILI), ("ILI (thumb)", ILI), ("ILI (trigger finger)", ILI)]


def row(i, name, grp, status="approved", kind="proc", seen=0):
    return {"id": i, "kind": kind, "name": name, "price_p": 100000, "price": "1,000", "active": True, "note": "",
            "code": "", "status": status, "seen": seen, "grp": grp, "forms": "", "source": "walk", "side": "",
            "updated_by": "", "updated_ts": "", "items": []}


def as_services(rows):
    """The order services() returns: pending, approved, then the rest; seen DESC; name (sqlite BINARY)."""
    rank = {"pending": 0, "approved": 1}
    return sorted(rows, key=lambda r: (rank.get(r["status"], 2), -r["seen"], r["name"].encode("utf-8")))


def groups_of(html):
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", g)).strip()
            for g in re.findall(r"<details class='grp'[^>]*><summary>(.*?)</summary>", html)]


def names_in(html):
    return re.findall(r"<span class='nm'>(.*?)</span>", html)


def judge(label, rows, expect_first=True):
    c = {"approved": sum(1 for r in rows if r["status"] == "approved"),
         "pending": sum(1 for r in rows if r["status"] == "pending")}
    h = P._section_html("proc", rows, c, True)
    g = [re.sub(r" \d+ · \d+ waiting$| \d+$", "", x) for x in groups_of(h)]
    check("%s: every group is one block (%d groups)" % (label, len(g)), len(g) == len(set(g)), repr(g))
    check("%s: every line is on the page exactly once (%d)" % (label, len(rows)),
          sorted(names_in(h)) == sorted(P._esc(r["name"]) for r in rows) and h.count("id='it-") == len(rows))
    if expect_first:
        known = [x for x in g if x in (CS, ILI, "Dressing")]
        check("%s: Cast / slab, then Injection (ILI), then Dressing; 'Other' last" % label,
              known == [x for x in (CS, ILI, "Dressing") if x in g] and g[:len(known)] == known
              and ("Other" not in g or g[-1] == "Other"), repr(g))
    return h, g


rows = as_services([row(100 + i, n, gp) for i, (n, gp) in enumerate(LIVE)])
c28 = {"approved": 28, "pending": 0}
before = [re.sub(r" \d+$", "", x) for x in groups_of(O._section_html("proc", rows, c28, True))]
check("NEGATIVE CONTROL -- the original page shows Cast / slab three times on these rows",
      before.count(CS) == 3 and len(before) == 6, repr(before))
h, g = judge("the 28 live lines", rows)
check("the groups read: Cast / slab . Injection (ILI) . Dressing . Other", g == [CS, ILI, "Dressing", "Other"], repr(g))
check("Cast / slab holds its 21 lines, ILI 5, Dressing 1, Other 1",
      [x.rsplit(" ", 1)[-1] for x in groups_of(h)] == ["21", "5", "1", "1"], repr(groups_of(h)))
nm = names_in(h)
pairs = [(a, b) for a, b in zip(nm, nm[1:]) if a.endswith(" fibre cast")]
check("each site's cast sits directly above its slab (10 pairs)",
      len(pairs) == 10 and all(b == a[:-4] + "slab" for a, b in pairs), repr(pairs[:3]))

rows2 = as_services([row(100 + i, n, gp) for i, (n, gp) in enumerate(LIVE)] + [row(900, "Zz new slab", CS, "pending")])
h2 = P._section_html("proc", rows2, {"approved": 28, "pending": 1}, True)
m = re.search(r"<details class='grp'( open)?><summary>Cast / slab <span class='tag'>22 &middot; 1 waiting</span>", h2)
check("a line waiting for his call opens its group and is counted", bool(m and m.group(1)))
check("...and comes first inside it", names_in(h2)[0] == "Zz new slab")
check("...and the group is still one block", [re.sub(r" \d+.*$", "", x) for x in groups_of(h2)].count(CS) == 1)

xr = as_services([row(i, "X-ray %d" % i, "X-ray", kind="xray", seen=50 - i) for i in range(1, 9)])
cx = {"approved": 8, "pending": 0}
check("the X-ray section is rendered byte for byte as before",
      O._section_html("xray", xr, cx, True) == P._section_html("xray", xr, cx, True))
check("an empty list still reads 'Nothing on this list yet'", "Nothing on this list yet" in P._section_html("proc", [], {"approved": 0, "pending": 0}, False))
odd = as_services([row(1, "Alpha", "Zebra group"), row(2, "Beta", ""), row(3, "Gamma", "apple group"), row(4, "Delta", CS)])
_, g3 = judge("unknown groups", odd, expect_first=False)
check("unknown groups follow by name, 'Other' last", g3 == [CS, "apple group", "Zebra group", "Other"], repr(g3))

if DB:
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    con.row_factory = sqlite3.Row
    real = []
    for r in con.execute("SELECT * FROM owner_service WHERE kind='proc' ORDER BY kind, "
                         "CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END, seen DESC, name"):
        d = row(r["id"], r["name"], r["grp"], r["status"], seen=r["seen"])
        d["price_p"] = r["price_p"]
        real.append(d)
    con.close()
    check("the REAL database gave its procedure lines (%d), read-only" % len(real), len(real) > 0)
    judge("the REAL lines", real)

print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
