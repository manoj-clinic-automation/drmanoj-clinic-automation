"""proof_s761.py -- kit S761_HUB_NEEDS_GOTO: the owner's Needs you read on THIS box's real data, grouped. Read only: it reads a COPY of
finance.db (the sources' own reads run on the copy) and the LIVE spine through SPINE_DB (spine_read opens it mode=ro) when given.
Prints COUNTS only -- per group its key and how many lines -- never a line's words, a name or a number.
  python3 proof_s761.py <finance dir under test> <shared dir> <finance.db> <scratch dir> [<spine.db, read only>]
Last line: 'PROOF S761: lines N · groups G (key n, ...) · every line once · the old lines unchanged · shelf line ok|none · N.NN s'
or 'PROOF S761: STOP -- <why>' (a line lost or doubled; the old lines differ; the read failed; over 8 s),
or, on the live files (no groups yet): 'PROOF S761 (the live files): no groups -- lines N'."""
import os, re, sqlite3, sys, time, warnings
warnings.filterwarnings("ignore")
fin, shared, db, scr = (os.path.abspath(x) for x in sys.argv[1:5])
spine = os.path.abspath(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] else ""
os.makedirs(scr, exist_ok=True)
cp = os.path.join(scr, "proof761.db")
src = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
dst = sqlite3.connect(cp)
src.backup(dst)
src.close(); dst.close()
os.environ["SPINE_DB"] = spine if (spine and os.path.isfile(spine)) else os.path.join(scr, "no_spine_here.db")
sys.path[:0] = [fin, os.path.join(fin, "spine"), shared]
os.chdir(scr)
import sanjeevni_approvals as sa                                       # noqa: E402
assert os.path.dirname(os.path.abspath(sa.__file__)) == fin
sa._unit = "medical"
c = sqlite3.connect(cp, timeout=30)
c.row_factory = sqlite3.Row
try:
    t0 = time.time()
    J = sa.needs_you(c)
    t = time.time() - t0
except Exception as e:                                                # noqa: BLE001
    print("PROOF S761: STOP -- the Needs-you read failed: %r" % (e,))
    sys.exit(0)
L = J.get("lines") or []
if not hasattr(sa, "s761_groups"):
    print("PROOF S761 (the live files): no groups -- lines %d" % len(L))
    sys.exit(0)
G = J.get("groups") or []
if not G and L:
    print("PROOF S761: STOP -- no groups (%s)" % J.get("groups_error"))
    sys.exit(0)
idx = sorted(i for g in G for i in g["idx"])
if idx != list(range(len(L))) or sum(g["n"] for g in G) != len(L):
    print("PROOF S761: STOP -- a line was lost or doubled (%d in groups, %d lines)" % (sum(g["n"] for g in G), len(L)))
    sys.exit(0)
OLD = sa._needs_you_before_s761(c)
same = [(l.get("cls"), l.get("target"), l.get("text")) for l in (OLD.get("lines") or [])] == [(l.get("cls"), l.get("target"), l.get("text")) for l in L]
print("groups (red first, counts only): " + " · ".join("%s %d%s" % (g["key"], g["n"], " (red)" if g["cls"] == "bad" else "") for g in G))
ag = [g for g in G if g["key"] == "arrived"]
if ag:
    print("arrived but not in Marg: %d lines from %d dealer(s)" % (ag[0]["n"], len(ag[0].get("vendors") or [])))
sh = [l["text"] for l in L if "moved apart on" in str(l.get("text"))]
shelf = "none"
if sh:
    m = re.search(r"moved apart on (\d+) item", sh[0])
    n = int(m.group(1)) if m else 0
    named = sh[0].split("): ", 1)[-1].split(" -- ")[0]
    k = len([x for x in named.split(" and ")[0].split(", ") if x])
    more = re.search(r" and (\d+) more$", named)
    shelf = "ok" if (n <= 8 and not more) or (n > 8 and more and k + int(more.group(1)) == n) else "WRONG"
    print("the shelf line: %d items, %d named%s" % (n, k, (", and %s more" % more.group(1)) if more else ""))
con_n = None
try:                                                                   # S761 (F-1199): the owner console's Sanjeevni count is the header's N
    import owner_console as oc                                         # noqa: E402
    oc._sanj_pages = lambda con, cx: ([], 0)
    cx = dict(needs_you=J, tile={})
    oc.sec_sanj(c, cx)
    con_n = cx["tile"].get("sanj_open")
except Exception as e:                                                # noqa: BLE001
    print("PROOF S761: STOP -- the console's Sanjeevni section could not be read: %r" % (e,))
    sys.exit(0)
print("the header counts %s (what needs him; %s grey lines that ask nothing in the fold); the console's Sanjeevni count %s" % (J.get("n_items"), J.get("n_info"), con_n))
if con_n != J.get("n_items"):
    print("PROOF S761: STOP -- the console counts %s, the hub's header %s" % (con_n, J.get("n_items")))
    sys.exit(0)
if t > 8.0:
    print("PROOF S761: STOP -- the Needs-you read took %.2f s (over 8 s)" % t)
    sys.exit(0)
if not same:
    print("PROOF S761: STOP -- the old lines differ under the kit's files")
    sys.exit(0)
if shelf == "WRONG":
    print("PROOF S761: STOP -- the shelf line's count and its names disagree")
    sys.exit(0)
print("PROOF S761: lines %d · groups %d (%s) · every line once · the old lines unchanged · header %s = console %s · shelf line %s · %.2f s"
      % (len(L), len(G), ", ".join("%s %d" % (g["key"], g["n"]) for g in G), J.get("n_items"), con_n, shelf, t))
