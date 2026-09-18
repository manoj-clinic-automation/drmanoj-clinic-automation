#!/root/wa/venv/bin/python3
# =============================================================================
#  walk_s321.py  ·  S321_XRAY_VIEWS  ·  v1
#
#  THE WALK THAT WOULD HAVE CAUGHT IT. S316's walk posted to the routes by their
#  full URLs, so it never exercised what a BROWSER does with a relative action.
#  This one renders the real page through Flask's test client, reads every <form
#  action> out of the HTML, resolves each one the way a browser resolves it --
#  against the page's own URL and its <base> tag -- and then POSTS to the address
#  that comes out. A 404 there is the owner's "page not accessible".
#
#  Everything happens on a scratch database in /tmp and a COPY of the live module.
#  Nothing live is opened.
#
#  NEGATIVE CONTROL: the same render is done with the UNPATCHED module, where
#  Approve must resolve to /finance/clinic/status and 404 -- if it does not, this
#  walk is not testing what it claims to test.
# =============================================================================
import importlib.util
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
try:
    from urllib.parse import urljoin
except ImportError:                                   # py2, never here
    from urlparse import urljoin                      # noqa

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = "/root/finance/owner_sheets.py"
PREFIX = "/finance/clinic/sheets"
OK, BAD = [], []

SEED = (("KNEE", "Knee", 684), ("LS", "Lumbosacral spine", 600), ("KS", "Knee studies", 423),
        ("ANKLE", "Ankle", 325), ("FOOT", "Foot", 272), ("CS", "Cervical spine", 363),
        ("SHOULDER", "Shoulder", 217), ("WRIST", "Wrist", 190), ("ELBOW", "Elbow", 158),
        ("LEG", "Leg  (tibia-fibula)", 107), ("HAND", "Hand", 128), ("CHEST", "Chest", 125),
        ("PBH", "Pelvis both hips", 251), ("TOES", "Toes", 55), ("DS", "Dorsal spine", 54),
        ("THUMB", "Thumb", 45), ("FOREARM", "Forearm", 60), ("CLAVICLE", "Clavicle", 83),
        ("DL", "Dorsolumbar", 32))


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


def load(path, tag):
    spec = importlib.util.spec_from_file_location("os_%s" % tag, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_db(path, module):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(module.SCHEMA)
    ts = "2026-09-18 15:00:00"
    for code, label, seen in SEED:
        con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,seen,grp,source,"
                    "created_by,created_ts,updated_by,updated_ts) "
                    "VALUES ('xray',?,0,?,'pending',?,'X-ray','register-S223','seed',?,'seed',?)",
                    (label, code, seen, ts, ts))
    # one procedure row, so the walk proves procedures are untouched
    con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,grp,source,"
                "created_by,created_ts,updated_by,updated_ts) "
                "VALUES ('proc','Below-knee cast',0,'CAST-BK','pending','Cast / slab',"
                "'ruling-S225','seed',?,'seed',?)", (ts, ts))
    con.commit()
    return con


def app_for(module, db_path):
    from flask import Flask
    app = Flask(__name__)
    holder = {}

    def db():
        if "c" not in holder:
            c = sqlite3.connect(db_path)
            c.row_factory = sqlite3.Row
            holder["c"] = c
        return holder["c"]

    def require(role, unit=None):               # the doctor, always
        return "manoj", None

    module.init(app, db, require, None, "clinic", PREFIX)
    return app


def forms_in(html):
    """[(action, [hidden field names])] in source order."""
    out = []
    for m in re.finditer(r"<form[^>]*action=['\"]([^'\"]+)['\"][^>]*>(.*?)</form>", html, re.S):
        out.append((m.group(1), m.group(2)))
    return out


def base_of(html, url):
    m = re.search(r"<base[^>]*href=['\"]([^'\"]+)['\"]", html)
    return urljoin(url, m.group(1)) if m else url


def main(argv):
    src = LIVE
    for a in argv[1:]:
        if a.startswith("--file="):
            src = a.split("=", 1)[1]
    if not os.path.isfile(src):
        print("RED -- %s is not there" % src)
        return 3
    sys.path.insert(0, HERE)
    import patch_owner_sheets_s321 as P
    import update_xray_s321 as U

    tmp = tempfile.mkdtemp(prefix="s321_")
    os.environ["OWNER_SHEET_SEED_DIR"] = os.path.join(tmp, "noseeds")
    os.makedirs(os.environ["OWNER_SHEET_SEED_DIR"], exist_ok=True)
    plain = os.path.join(tmp, "plain.py")
    fixed = os.path.join(tmp, "fixed.py")
    shutil.copy2(src, plain)
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    already = P.MARK in text
    if already:
        # A RE-RUN. The live page already carries the fix, so there is nothing to
        # apply and no unpatched baseline to compare against: the three negative
        # controls below are NOT APPLICABLE and say so rather than going red.
        print("   note this page already carries the S321 fix -- the negative controls"
              " need an unpatched baseline and are skipped, named, below")
        shutil.copy2(src, fixed)
        check("the page already carries the fix (a re-run, not a failure)", True)
    else:
        new, msgs = P.apply_to_text(text)
        check("the patch applies to this owner_sheets.py", new is not None and new != text)
        if new is None:
            print("   " + "; ".join(msgs))
            return 4
        with open(fixed, "w", encoding="utf-8") as fh:
            fh.write(new)
    check("the file the page will run compiles",
          subprocess.run([sys.executable, "-m", "py_compile", fixed]).returncode == 0)

    # ---------- the rename / price pass, on a scratch database -----------------
    mod_f = load(fixed, "f")
    db1 = os.path.join(tmp, "one.db")
    con = make_db(db1, mod_f)
    con.close()
    rc = U.main(["x", "--db", db1, "--apply"])
    check("the update pass applies cleanly", rc == 0)
    con = sqlite3.connect(db1)
    con.row_factory = sqlite3.Row
    rows = {r["code"]: r for r in con.execute("SELECT code,name,price_p,kind FROM owner_service")}
    check("every X-ray now carries its views (knee)",
          rows["KNEE"]["name"] == "Knee AP & Lateral view")
    check("the default price is 500 where he said 500", rows["KNEE"]["price_p"] == 50000)
    check("a single view is 300 (clavicle)",
          rows["CLAVICLE"]["name"] == "Clavicle AP view" and rows["CLAVICLE"]["price_p"] == 30000)
    check("the wrist is three views on 11 x 14 at 800",
          rows["WRIST"]["name"] == "Wrist AP, Lateral & Oblique view (11 x 14)"
          and rows["WRIST"]["price_p"] == 80000)
    check("PBH is a single view on 11 x 14 at 400",
          rows["PBH"]["name"] == "Pelvis both hips AP view (11 x 14)"
          and rows["PBH"]["price_p"] == 40000)
    check("CHEST BECAME TWO STUDIES, AP and PA, 300 each",
          rows["CHEST"]["name"] == "Chest PA view" and rows["CHEST"]["price_p"] == 30000
          and rows["CHEST_AP"]["name"] == "Chest AP view" and rows["CHEST_AP"]["price_p"] == 30000)
    check("all 19 seeded studies plus the new one are present", len(
        [r for r in rows.values() if r["kind"] == "xray"]) == 20)
    check("the procedure row was not touched", rows["CAST-BK"]["name"] == "Below-knee cast")
    check("a second run says ALREADY and writes nothing",
          U.main(["x", "--db", db1, "--apply"]) == 0
          and con.execute("SELECT COUNT(*) c FROM owner_service").fetchone()["c"] == 21)

    # his own edit must survive
    con.execute("UPDATE owner_service SET name='Knee mera naam', price_p=77700, "
                "updated_by='manoj' WHERE code='KNEE'")
    con.commit()
    U.main(["x", "--db", db1, "--apply"])
    r = con.execute("SELECT name, price_p FROM owner_service WHERE code='KNEE'").fetchone()
    check("A ROW HE HAS EDITED HIMSELF IS NEVER OVERWRITTEN",
          r["name"] == "Knee mera naam" and r["price_p"] == 77700)
    con.close()

    # ---------- the browser-shape test: do the buttons post anywhere real? ----
    db2 = os.path.join(tmp, "two.db")
    make_db(db2, mod_f).close()
    app = app_for(mod_f, db2)
    cl = app.test_client()
    url = PREFIX                                     # exactly what the tile links to
    r = cl.get(url)
    check("the page opens at the URL the tile uses", r.status_code == 200)
    html = r.get_data(as_text=True)
    check("the page carries a <base> tag pointing at its own folder",
          base_of(html, url).endswith("/finance/clinic/sheets/"))
    acts = forms_in(html)
    check("the page has the forms it should (rename, price, status, add)", len(acts) >= 8)
    resolved = sorted(set(urljoin(base_of(html, url), a) for a, _b in acts))
    check("EVERY form action now resolves inside this page's own folder",
          all(x.startswith(PREFIX + "/") for x in resolved))
    bad = []
    for path in resolved:
        rr = cl.post(path, data={"id": "1", "s": "approved", "name": "x", "price": "1",
                                 "kind": "xray", "item": "y", "iid": "1", "qty": "1"})
        if rr.status_code in (404, 405):
            bad.append("%s -> %d" % (path, rr.status_code))
    check("and every one of them answers (no 404, no 405): %s" % (", ".join(bad) or "all good"),
          not bad)
    rr = cl.post(PREFIX + "/status", data={"id": "1", "s": "approved"})
    check("APPROVE ITSELF WORKS -- it redirects back to the page",
          rr.status_code in (302, 303) and "/finance/clinic/sheets" in (rr.headers.get("Location") or ""))
    con = sqlite3.connect(db2)
    con.row_factory = sqlite3.Row
    st = con.execute("SELECT status FROM owner_service WHERE id=1").fetchone()["status"]
    check("and the row really is approved afterwards", st == "approved")
    con.close()

    # ---------- negative control: the unpatched module -------------------------
    if already:
        print("   --   NEGATIVE CONTROLS SKIPPED: no unpatched baseline on a re-run"
              " (the fix is already in the live file)")
        shutil.rmtree(tmp, ignore_errors=True)
        print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
        if BAD:
            print("RED: " + "; ".join(BAD))
            return 1
        print("WALK OK -- %d checks (re-run: 3 negative controls not applicable)" % len(OK))
        return 0
    mod_p = load(plain, "p")
    db3 = os.path.join(tmp, "three.db")
    make_db(db3, mod_p).close()
    app2 = app_for(mod_p, db3)
    cl2 = app2.test_client()
    h2 = cl2.get(url).get_data(as_text=True)
    check("NEGATIVE CONTROL -- the unpatched page has no base tag",
          "<base" not in h2)
    a2 = sorted(set(urljoin(base_of(h2, url), a) for a, _b in forms_in(h2)))
    check("NEGATIVE CONTROL -- unpatched, Approve resolves OUTSIDE the page's folder",
          any(x == "/finance/clinic/status" for x in a2))
    check("NEGATIVE CONTROL -- and that address 404s, which is what he saw",
          cl2.post("/finance/clinic/status", data={"id": "1", "s": "approved"}).status_code == 404)

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("WALK OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
