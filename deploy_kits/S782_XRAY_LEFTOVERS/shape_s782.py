# S782 proof: on a COPY of the live database, what the next filing run would do with the parked pictures -- counts only, no name,
# no number. argv: <dir with records.py> <db copy> <now, IST iso>
import sys, types, sqlite3, os, collections, re
fl = types.ModuleType("flask")
class BP:
    def __init__(s, *a, **k): pass
    def route(s, *a, **k): return lambda f: f
    def __getattr__(s, n): return lambda *a, **k: (lambda f: f)
fl.Blueprint = BP
for n in ("Response", "jsonify", "redirect", "request"): setattr(fl, n, None)
sys.modules.setdefault("flask", fl)
os.environ["RECORDS_NOW"] = sys.argv[3]
sys.path.insert(0, sys.argv[1])
import records as R
con = sqlite3.connect(sys.argv[2]); con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("SELECT * FROM xray_filing WHERE state='check'")]
files = [{"id": r["src_id"], "name": r["orig_name"], "mimeType": "image/jpeg",
          "modifiedTime": R._s752_utc(r["file_time"] or ((r["day"] or "") + " 12:00:00"))} for r in rows]
out = R._s752_retry(con, files, sys.argv[3].replace("T", " ")[:19], True) if files else []
C = collections.Counter()
for o in out:
    v = (con.execute("SELECT verdict FROM xray_filing WHERE src_id=?", (o["id"],)).fetchone() or [""])[0] or ""
    C[(o["action"], "S782" if "S782" in v else "earlier rules")] += 1
print("parked before: %d" % len(rows))
for (a, w), n in sorted(C.items()):
    print("  %-4s %3d  (%s)" % (a, n, w))
print("parked after: %d" % con.execute("SELECT COUNT(*) FROM xray_filing WHERE state='check'").fetchone()[0])
print("SHAPE DONE")
