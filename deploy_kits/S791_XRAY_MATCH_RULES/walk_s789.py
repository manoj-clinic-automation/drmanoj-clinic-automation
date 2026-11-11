#!/usr/bin/python3
# walk_s789.py -- kit S789_LAB_TILE_COUNT. Usage: walk_s789.py <dir holding check_screens.py> <a finance.db copy> [--control]
# Read-only on a scratch copy; counts and ok/BAD only. Last line "WALK OK n/n" | "WALK RED k of n" | "CONTROL: ...".
import importlib, os, re, shutil, sqlite3, sys, tempfile
K, SRC = os.path.abspath(sys.argv[1]), sys.argv[2]
CONTROL = "--control" in sys.argv
T = tempfile.mkdtemp(prefix="s789w."); DB = os.path.join(T, "f.db"); shutil.copyfile(SRC, DB); os.environ["FINANCE_DB"] = DB
for p in [x for x in os.environ.get("S789_LIBS", "").split(os.pathsep) if x] + [K]:
    while p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
RES = []
def ck(name, ok, why=""):
    RES.append(bool(ok)); print("%s %s%s" % ("ok " if ok else "BAD", name, ("  -- " + str(why)) if (why != "" and not ok) else ""))
R = importlib.import_module("records"); CS = importlib.import_module("check_screens")
if CS.R is None:
    CS.attach(R)
ck("A1 check_screens from the kit dir", os.path.dirname(os.path.abspath(CS.__file__)) == K)
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
L = CS.lab_items(con); w = [i for i in L if i["wrong"]]
ck("B1 the count (his tile, his console line) is the reports that need an answer (%d of %d)" % (len(w), len(L)), CS.counts(con)["lab"] == len(w))
src = open(os.path.join(K, "check_screens.py"), encoding="utf-8").read()
ck("B2 his page: the tile counts the asking ones and names the rest 'for information'",
   "B.lab.filter(function(i){return i.wrong;}).length" in src and "for information only" in src and 'sorted(lab_items(con), key=lambda i: not i["wrong"])' in src)
con.close(); shutil.rmtree(T, ignore_errors=True)
bad = RES.count(False)
if CONTROL:
    print("CONTROL: red (%d of %d)" % (bad, len(RES)) if bad else "CONTROL: GREEN -- the control did not go red")
else:
    print("WALK OK %d/%d" % (len(RES), len(RES)) if not bad else "WALK RED %d of %d" % (bad, len(RES)))
