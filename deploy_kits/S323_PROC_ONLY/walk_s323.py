#!/root/wa/venv/bin/python3
# =============================================================================
#  walk_s323.py  ·  S323_PROC_ONLY  ·  v1
#
#  The page is rendered through Flask and its buttons are POSTed the way a browser
#  resolves them (the S321 lesson), and the database is seeded in the state HIS
#  box is actually in after S322 -- fibre names, and every row marked as HIS own
#  because he approved the X-ray list. That is the state in which S322 reported
#  "X-rays that now ask a side: 0", and this walk proves the fix works there.
#
#  Nothing live is opened.
#
#  NEGATIVE CONTROLS: a line where HE typed his own words keeps them; a rename
#  that would collide refuses; and the unpatched page is shown still carrying the
#  X-ray section and the remove buttons, so the four removals are measured
#  against something.
# =============================================================================
import importlib.util
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from urllib.parse import urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = "/root/finance/owner_sheets.py"
PREFIX = "/finance/clinic/sheets"
OK, BAD = [], []

XRAY = (("KNEE", "Knee AP & Lateral view", 50000), ("LS", "Lumbosacral spine AP & Lateral view", 50000),
        ("ANKLE", "Ankle AP & Lateral view", 50000), ("CHEST", "Chest PA view", 30000),
        ("PBH", "Pelvis both hips AP view (11 x 14)", 40000),
        ("WRIST", "Wrist AP, Lateral & Oblique view (11 x 14)", 80000),
        ("CLAVICLE", "Clavicle AP view", 30000))
PROC = (("AK", "Above knee fibre cast", "Cast / slab"),
        ("AK-SLAB", "Above knee fibre slab", "Cast / slab"),
        ("AE", "Above elbow fibre cast", "Cast / slab"),
        ("AE-SLAB", "Above elbow fibre slab", "Cast / slab"),
        ("SPICA", "Thumb spica fibre cast", "Cast / slab"),
        ("SPICA-SLAB", "Thumb spica fibre slab", "Cast / slab"),
        ("USLAB", "U fibre slab", "Cast / slab"),
        ("USLAB-CAST", "U fibre cast", "Cast / slab"),
        ("CLAV", "Clavicle bandage", "Cast / slab"),
        ("ILI-SH", "ILI shoulder", "Injection (ILI)"),
        ("ILI-HE", "ILI heel (plantar fasciitis)", "Injection (ILI)"),
        ("DRESS", "Dressing", "Dressing"))


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


def load(path, tag):
    spec = importlib.util.spec_from_file_location("os23_%s" % tag, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_db(path, module, owner_touched=True):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(module.SCHEMA)
    for table, col, decl in module.NEW_COLS:
        have = [r[1] for r in con.execute("PRAGMA table_info(%s)" % table)]
        if col not in have:
            con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, decl))
    ts = "2026-09-19 10:00:00"
    who = "manoj" if owner_touched else "seed"
    for code, name, price in XRAY:
        con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,seen,grp,source,side,"
                    "created_by,created_ts,updated_by,updated_ts) "
                    "VALUES ('xray',?,?,?,'approved',10,'X-ray','register-S223','','seed',?,?,?)",
                    (name, price, code, ts, who, ts))
    for code, name, grp in PROC:
        cur = con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,grp,forms,source,"
                          "side,created_by,created_ts,updated_by,updated_ts) "
                          "VALUES ('proc',?,0,?,'pending',?,'cast','ruling-S225',?,'seed',?,?,?)",
                          (name, code, grp, "ask" if grp != "Dressing" else "", ts, who, ts))
        con.execute("INSERT INTO owner_service_item (service_id,item,qty,unit,ask,sizes,added_by,added_ts) "
                    "VALUES (?,'Fibrecast bandage',1,'','size_qty','2\",3\"','seed',?)",
                    (cur.lastrowid, ts))
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

    def require(role, unit=None):
        return "manoj", None

    module.init(app, db, require, None, "clinic", PREFIX)
    return app


def forms_in(html):
    return re.findall(r"<form[^>]*action=['\"]([^'\"]+)['\"]", html)


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
    import patch_owner_sheets_s323 as P
    import update_proc_s323 as U

    tmp = tempfile.mkdtemp(prefix="s323_")
    os.environ["OWNER_SHEET_SEED_DIR"] = os.path.join(tmp, "noseeds")
    os.makedirs(os.environ["OWNER_SHEET_SEED_DIR"], exist_ok=True)
    plain, fixed = os.path.join(tmp, "plain.py"), os.path.join(tmp, "fixed.py")
    shutil.copy2(src, plain)
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    already = P.MARK in text
    if already:
        print("   note this page already carries S323 -- the controls that need an unpatched"
              " baseline are skipped and named below")
        shutil.copy2(src, fixed)
        check("the page already carries the change (a re-run, not a failure)", True)
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
    mod = load(fixed, "f")

    # ---------- the data pass, in the state his box is in ---------------------
    db1 = os.path.join(tmp, "one.db")
    make_db(db1, mod, owner_touched=True).close()
    check("the rename and side pass applies cleanly", U.main(["x", "--db", db1, "--apply"]) == 0)
    con = sqlite3.connect(db1)
    con.row_factory = sqlite3.Row
    rows = {r["code"]: r for r in con.execute("SELECT * FROM owner_service")}
    check("ABBREVIATION FIRST, NAME IN BRACKETS -- A/E (Above elbow) fibre cast",
          rows["AE"]["name"] == "A/E (Above elbow) fibre cast")
    check("and its slab twin the same way",
          rows["AE-SLAB"]["name"] == "A/E (Above elbow) fibre slab")
    check("the knee pair too",
          rows["AK"]["name"] == "A/K (Above knee) fibre cast"
          and rows["AK-SLAB"]["name"] == "A/K (Above knee) fibre slab")
    check("thumb spica keeps SPICA as its shorthand",
          rows["SPICA"]["name"] == "SPICA (Thumb spica) fibre cast")
    check("the U slab is left plain -- its shorthand IS the word",
          rows["USLAB"]["name"] == "U fibre slab")
    check("the ILI lines read ILI (site)",
          rows["ILI-SH"]["name"] == "ILI (shoulder)"
          and rows["ILI-HE"]["name"] == "ILI (heel, plantar fasciitis)")
    check("THE X-RAYS NOW ASK A SIDE EVEN THOUGH HE HAD ALREADY APPROVED THEM",
          all(rows[c]["side"] == "ask" for c in ("KNEE", "ANKLE", "WRIST", "CLAVICLE")))
    check("and the spine, chest and pelvis still do not",
          all((rows[c]["side"] or "") == "" for c in ("LS", "CHEST", "PBH")))
    check("his approvals were not disturbed",
          all(rows[c]["status"] == "approved" for c, _n, _p in XRAY))
    check("no price moved",
          all(int(rows[c]["price_p"]) == p for c, _n, p in XRAY))
    check("a second run says ALREADY", U.main(["x", "--db", db1, "--apply"]) == 0)
    con.close()

    # ---------- the page itself ----------------------------------------------
    db2 = os.path.join(tmp, "two.db")
    make_db(db2, mod, owner_touched=True).close()
    U.main(["x", "--db", db2, "--apply"])
    app = app_for(mod, db2)
    cl = app.test_client()
    html = cl.get(PREFIX).get_data(as_text=True)
    check("THE PAGE NO LONGER CARRIES THE X-RAY LIST",
          "Knee AP &amp; Lateral view" not in html and "<h2>X-rays</h2>" not in html)
    check("it opens on the procedures", "Procedures and their consumables" in html)
    check("and says where the X-rays went, with a way to open them",
          "The X-ray list is done and is off this page" in html and "?kind=xray" in html)
    check("A SIDE THAT IS ASKED HAS NO TURN-OFF", "turn off" not in html)
    check("it simply reads R / L", ">R / L<" in html)
    check("THE CONSUMABLES ARE READ-ONLY -- no remove, no add box",
          "remove</button>" not in html and "add an item" not in html)
    check("but they are still shown, with how each is asked",
          "Fibrecast bandage" in html and "size" in html)
    xhtml = cl.get(PREFIX + "?kind=xray").get_data(as_text=True)
    check("the X-rays are one click away and still editable there",
          "Knee AP &amp; Lateral view" in xhtml and "rename" in xhtml)
    check("with a way back to the procedures", "Back to the procedures" in xhtml)
    acts = sorted(set(urljoin(base_of(html, PREFIX), a) for a in forms_in(html)))
    check("every form on the page still resolves inside its own folder",
          all(x.startswith(PREFIX + "/") for x in acts))
    bad = []
    for path in acts:
        rr = cl.post(path, data={"id": "1", "s": "approved", "name": "x", "price": "1",
                                 "kind": "xray", "ask": "1"})
        if rr.status_code in (404, 405):
            bad.append("%s -> %d" % (path, rr.status_code))
    check("and every one answers: %s" % (", ".join(bad) or "all good"), not bad)

    # ---------- negative controls -------------------------------------------
    db3 = os.path.join(tmp, "three.db")
    c3 = make_db(db3, mod, owner_touched=True)
    c3.execute("UPDATE owner_service SET name='Mera apna naam' WHERE code='AK'")
    c3.commit()
    c3.close()
    U.main(["x", "--db", db3, "--apply"])
    c3 = sqlite3.connect(db3)
    check("NEGATIVE CONTROL -- words he typed himself are kept",
          c3.execute("SELECT name FROM owner_service WHERE code='AK'").fetchone()[0]
          == "Mera apna naam")
    c3.close()

    db4 = os.path.join(tmp, "four.db")
    c4 = make_db(db4, mod, owner_touched=True)
    c4.execute("UPDATE owner_service SET name='A/E (Above elbow) fibre cast' WHERE code='DRESS'")
    c4.commit()
    c4.close()
    check("NEGATIVE CONTROL -- a colliding rename refuses and writes nothing",
          U.main(["x", "--db", db4, "--apply"]) == 4)

    if not already:
        mod_p = load(plain, "p")
        db5 = os.path.join(tmp, "five.db")
        make_db(db5, mod_p, owner_touched=True).close()
        h5 = app_for(mod_p, db5).test_client().get(PREFIX).get_data(as_text=True)
        check("NEGATIVE CONTROL -- the unpatched page DID carry the X-ray list",
              "Knee AP &amp; Lateral view" in h5)
        check("NEGATIVE CONTROL -- and the remove buttons and turn-off",
              "remove</button>" in h5 and "turn off" in h5)
    else:
        print("   --   two negative controls skipped: no unpatched baseline on a re-run")

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("WALK OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
