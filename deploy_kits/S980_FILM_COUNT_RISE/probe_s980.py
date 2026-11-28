#!/usr/bin/env python3
"""probe_s980.py -- the live shape of kit S980 on a COPY of finance.db: the film pages drawn by the old and the new code, compared by
hash and status only (no page text is printed). Usage: probe_s980.py OLD_DIR NEW_DIR DB_COPY. Last line 'ALL PASS' when green."""
import sys, os, sqlite3, shutil, tempfile, hashlib, importlib
OLD, NEW, DB = sys.argv[1:4]
os.environ.update({"EVCHK_LIVE_DB": "/nonexistent/live.db", "RING_PORTAL_DIR": "/nonexistent/portal"})
from flask import Flask
res = {}
for side, path in (("old", OLD), ("new", NEW)):
    for m in ("xray_film", "day_check"):
        sys.modules.pop(m, None)
    sys.path.insert(0, path)
    xf = importlib.import_module("xray_film")
    sys.path.pop(0)
    tmp = tempfile.mkdtemp(prefix="p980_")
    cp = os.path.join(tmp, "c.db")
    s = sqlite3.connect(DB); d = sqlite3.connect(cp); s.backup(d); d.close(); s.close()
    con = sqlite3.connect(cp); con.row_factory = sqlite3.Row
    U = [{"user": "manoj", "roles": ["checker"]}]
    app = Flask("p980" + side); app.config["TESTING"] = True
    xf.init(app, lambda: con, lambda *r, **k: (U[0], None), None)
    c = app.test_client()
    out = {}
    for who, roles in (("manoj", ["checker"]), ("alisha", ["maker"])):
        U[0] = {"user": who, "roles": roles}
        for url in ("/finance/slips/film/log", "/finance/slips/film/subah", "/finance/slips/film/list"):
            r = c.get(url)
            body = r.get_data()
            out[(who, url)] = (r.status_code, hashlib.md5(body).hexdigest(), b"newbox_8x10" in body)
    res[side] = out
    con.close(); shutil.rmtree(tmp, ignore_errors=True)
same = sum(1 for k in res["old"] if res["old"][k][:2] == res["new"][k][:2])
codes = sorted(set(v[0] for v in res["new"].values()))
tick_old = res["old"][("alisha", "/finance/slips/film/subah")][2]
tick_new = res["new"][("alisha", "/finance/slips/film/subah")][2]
print("LIVE film pages: status %s; the same bytes on %d of %d (only the staff morning page may differ); the staff new-box tick old %s -> new %s"
      % (codes, same, len(res["old"]), tick_old, tick_new))
diff = [k for k in res["old"] if res["old"][k][:2] != res["new"][k][:2]]
ok = codes == [200] and all(k == ("alisha", "/finance/slips/film/subah") for k in diff) and tick_new
print("ALL PASS" if ok else "NOT GREEN %s" % diff)
sys.exit(0 if ok else 1)
