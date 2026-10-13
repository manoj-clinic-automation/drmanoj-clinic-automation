#!/usr/bin/env python3
"""Renders the intake page (switch ON) for reception and for the owner from the built app on a fresh made-up database,
into <out dir>/intake_<role>.html, with the widget pointed at the local file. For browser_s544.js."""
import importlib.util, os, sqlite3, sys, tempfile
D, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
wd = tempfile.mkdtemp(prefix="s544_pages_", dir=os.path.expanduser("~"))
os.environ["ASSETS_DB"] = os.path.join(wd, "assets.db"); os.environ["ASSETS_UPLOADS"] = os.path.join(wd, "up"); os.makedirs(os.environ["ASSETS_UPLOADS"])
sys.path.insert(0, D)
spec = importlib.util.spec_from_file_location("asset_register", os.path.join(D, "asset_register.py"))
m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_owner_2031','Walk Owner','owner','x',1)")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('scan.lanes5','on')"); db.commit()
ep = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [None])[0]
uid = db.execute("SELECT id FROM users WHERE role='owner'").fetchone()[0]
os.makedirs(OUT, exist_ok=True)
own = m.app.test_client()
with own.session_transaction() as s:
    s["uid"] = uid; s["epoch"] = ep
real = m._sso_user
pages = {"owner": own.get("/intake").get_data(as_text=True)}
m._sso_user = lambda: {"id": None, "username": "walkrecep2031", "display_name": "Walkrecep2031", "role": "reception", "active": 1}
pages["reception"] = m.app.test_client().get("/intake").get_data(as_text=True)
m._sso_user = real
import re
for k, t in pages.items():
    t = re.sub(r'<script src="[^"]*scan/widget\.js[^"]*"></script>', '<script src="file://%s"></script>' % os.path.join(D, "scanner_widget.js"), t)
    t = re.sub(r'<script src="https://cdnjs[^"]*"></script>', '', t)
    open(os.path.join(OUT, "intake_%s.html" % k), "w", encoding="utf-8").write(t)
print("written", sorted(pages))
