#!/usr/bin/env python3
"""walk_box_s523.py -- the app's part of the S523 walk, on the box: the built app on a COPY of the live database
(the copy lives under the session's own home and is removed by the installer, F-752); every door the kit adds.

    python3 walk_box_s523.py <dir with asset_register.py + scanner_widget.js> <opencv.js> <live assets.db> [--expect-red]

Prints GREEN/RED per check; exit 1 on any RED (with --expect-red: exit 0 only if at least one RED -- the control)."""
import importlib.util, os, shutil, sqlite3, subprocess, sys, tempfile

D, CVJS, LIVEDB = [os.path.abspath(a) for a in sys.argv[1:4]]
EXPECT_RED = "--expect-red" in sys.argv
R = []


def check(name, ok, detail=""):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)) if detail else ""))


def main():
    wd = tempfile.mkdtemp(prefix="s523_walk_", dir=os.path.expanduser("~"))
    try:
        static = os.path.join(wd, "static"); os.makedirs(static)
        shutil.copy(CVJS, os.path.join(static, "opencv.js"))
        subprocess.run(["gzip", "-k", "-9", os.path.join(static, "opencv.js")], check=True)
        shutil.copy(os.path.join(D, "asset_register.py"), wd); shutil.copy(os.path.join(D, "scanner_widget.js"), wd)
        for extra in ("clinic_papers.py",):
            p = os.path.join(D, extra)
            if os.path.exists(p): shutil.copy(p, wd)
        dbc = os.path.join(wd, "assets.db")
        src = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True); dst = sqlite3.connect(dbc); src.backup(dst); src.close(); dst.close()
        os.environ["ASSETS_DB"] = dbc; os.environ["ASSETS_UPLOADS"] = os.path.join(wd, "uploads"); os.makedirs(os.environ["ASSETS_UPLOADS"])
        os.environ["SCANNER_OPENCV_JS"] = os.path.join(static, "opencv.js")
        sys.path.insert(0, wd)
        spec = importlib.util.spec_from_file_location("asset_register", os.path.join(wd, "asset_register.py"))
        try:
            m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
        except Exception as e:                                                    # noqa: BLE001
            check("P0 the app imports on a copy of the live database", False, repr(e)[:200]); return
        check("P0 the app imports on a copy of the live database", True)
        c = m.app.test_client()
        r = c.get("/scan/opencv.js", headers={"Accept-Encoding": "gzip"})
        check("P1 /scan/opencv.js: the gzip copy, cached a year", r.status_code == 200 and r.headers.get("Content-Encoding") == "gzip" and "immutable" in r.headers.get("Cache-Control", ""),
              "%s %s" % (r.status_code, r.headers.get("Content-Encoding")))
        r2 = c.get("/scan/opencv.js")
        check("P2 /scan/opencv.js: the plain copy", r2.status_code == 200 and r2.headers.get("Content-Encoding") is None and len(r2.data) > 9000000, "%s %d" % (r2.status_code, len(r2.data)))
        # an owner session without a password: the test client's session cookie is signed by the app's own secret
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        u = db.execute("SELECT id, username FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone(); db.close()
        check("P3 an active owner login exists in the database", bool(u), u["username"] if u else "none")
        if not u: return
        with c.session_transaction() as s:
            s["uid"] = u["id"]
            try: s["epoch"] = m._sso_epoch()
            except Exception: pass                                                # noqa: BLE001
        r4 = c.get("/intake"); t4 = r4.get_data(as_text=True)
        if r4.status_code != 200:
            # the app's own session shape may differ; the fallback is the seeded password of a throw-away owner
            db = sqlite3.connect(dbc); from werkzeug.security import generate_password_hash
            db.execute("INSERT OR IGNORE INTO users(username,display_name,role,password_hash,active) VALUES('s523walk','S523 walk','owner',?,1)", (generate_password_hash("s523-walk-only"),)); db.commit(); db.close()
            c = m.app.test_client(); c.post("/login", data={"username": "s523walk", "password": "s523-walk-only"})
            r4 = c.get("/intake"); t4 = r4.get_data(as_text=True)
        check("P4 /intake answers for the owner", r4.status_code == 200, r4.status_code)
        db = sqlite3.connect(dbc); on_now = db.execute("SELECT value FROM settings WHERE key='scan.cv'").fetchone(); db.close()
        was_on = bool(on_now and (on_now[0] or "").strip().lower() == "on")
        check("P5 the intake's config carries cvScan only when the switch is on (now: %s)" % ("on" if was_on else "off"), ('"cvScan": true' in t4) == was_on)
        r5 = c.get("/admin"); t5 = r5.get_data(as_text=True)
        check("P6 /admin shows the switch card", r5.status_code == 200 and "smart outline" in t5 and "set_scan_cv" in t5, r5.status_code)
        r6 = c.post("/admin", data={"action": "set_scan_cv", "on": "1"}, follow_redirects=True)
        r7 = c.get("/intake"); t7 = r7.get_data(as_text=True)
        check("P7 switched ON (on the copy): cvScan true and the library's versioned URL", '"cvScan": true' in t7 and "/scan/opencv.js?v=" in t7)
        c.post("/admin", data={"action": "set_scan_cv", "on": "0"}, follow_redirects=True)
        r8 = c.get("/intake")
        check("P8 switched OFF (on the copy): the intake as today", '"cvScan"' not in r8.get_data(as_text=True))
        r9 = c.get("/healthz"); check("P9 /healthz answers", r9.status_code == 200, r9.status_code)
        r10 = c.get("/scan/widget.js"); check("P10 the widget served carries S523", r10.status_code == 200 and b"S523" in r10.data)
        r11 = c.get("/papers"); check("P11 the papers page still answers (clinic_papers mounted)", r11.status_code == 200, r11.status_code)
        r12 = c.get("/bills"); check("P12 the bills page still answers", r12.status_code == 200, r12.status_code)
        db = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True); live_on = db.execute("SELECT value FROM settings WHERE key='scan.cv'").fetchone(); db.close()
        check("P13 the LIVE database was not written by this walk (scan.cv unchanged)", (bool(live_on and live_on[0] == "on")) == was_on)
    finally:
        shutil.rmtree(wd, ignore_errors=True)


main()
red = R.count(False)
print("%d checks: %d green, %d red" % (len(R), len(R) - red, red))
if EXPECT_RED:
    sys.exit(0 if red else 1)
sys.exit(1 if red else 0)
