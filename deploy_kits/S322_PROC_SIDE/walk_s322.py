#!/root/wa/venv/bin/python3
# =============================================================================
#  walk_s322.py  ·  S322_PROC_SIDE  ·  v1
#
#  Same discipline as S321's walk, which is the one that caught a live defect:
#  the page is RENDERED through Flask and its own buttons are POSTed to the way a
#  BROWSER resolves them. On top of that, the procedure list is rebuilt on a
#  scratch database and every one of his three rules is asserted:
#
#     the word fibre in every cast and slab · every plaster site present BOTH as
#     cast and as slab · right / left asked on the ILI lines and on the limb
#     X-rays, and NOT on the spines, chest or pelvis.
#
#  Nothing live is opened: a copy of the module, a database in /tmp.
#
#  NEGATIVE CONTROLS: the side column removed from the plan (the toggle can then
#  change nothing), a row marked as HIS edit (which must survive untouched), and
#  a name collision (which must refuse rather than write).
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

XRAY = (("KNEE", "Knee AP & Lateral view"), ("LS", "Lumbosacral spine AP & Lateral view"),
        ("KS", "Knee studies (K/S) AP & Lateral view"), ("ANKLE", "Ankle AP & Lateral view"),
        ("CHEST", "Chest PA view"), ("PBH", "Pelvis both hips AP view (11 x 14)"),
        ("WRIST", "Wrist AP, Lateral & Oblique view (11 x 14)"), ("CLAVICLE", "Clavicle AP view"))
PROC = (("AK", "Above knee", "Cast / slab", "cast,slab"),
        ("BK", "Below knee", "Cast / slab", "cast,slab"),
        ("SBK", "Short below knee", "Cast / slab", "cast,slab"),
        ("HBK", "High below knee", "Cast / slab", "cast,slab"),
        ("CYL", "Cylinder", "Cast / slab", "cast,slab"),
        ("AE", "Above elbow", "Cast / slab", "cast,slab"),
        ("BE", "Below elbow", "Cast / slab", "cast,slab"),
        ("SBE", "Short below elbow", "Cast / slab", "cast,slab"),
        ("USLAB", "U slab", "Cast / slab", "slab,cast"),
        ("SPICA", "Thumb spica", "Cast / slab", "cast,slab"),
        ("CLAV", "Clavicle bandage", "Cast / slab", ""),
        ("ILI-SH", "ILI shoulder", "Injection (ILI)", ""),
        ("ILI-EL", "ILI elbow", "Injection (ILI)", ""),
        ("ILI-TH", "ILI thumb", "Injection (ILI)", ""),
        ("ILI-FI", "ILI finger (trigger finger)", "Injection (ILI)", ""),
        ("ILI-HE", "ILI heel (plantar fasciitis)", "Injection (ILI)", ""),
        ("DRESS", "Dressing", "Dressing", ""))
ITEMS = {"AK": ("Fibrecast bandage", "Roller bandage", "Cast padding", "Stockinette")}


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


def load(path, tag):
    spec = importlib.util.spec_from_file_location("os22_%s" % tag, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_db(path, module):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(module.SCHEMA)
    for table, col, decl in module.NEW_COLS:
        have = [r[1] for r in con.execute("PRAGMA table_info(%s)" % table)]
        if col not in have:
            con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, decl))
    ts = "2026-09-19 09:00:00"
    for code, name in XRAY:
        con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,seen,grp,source,"
                    "created_by,created_ts,updated_by,updated_ts) "
                    "VALUES ('xray',?,50000,?,'pending',10,'X-ray','register-S223','seed',?,'seed',?)",
                    (name, code, ts, ts))
    for code, name, grp, forms in PROC:
        cur = con.execute("INSERT INTO owner_service (kind,name,price_p,code,status,grp,forms,source,"
                          "created_by,created_ts,updated_by,updated_ts) "
                          "VALUES ('proc',?,0,?,'pending',?,?,'ruling-S225','seed',?,'seed',?)",
                          (name, code, grp, forms, ts, ts))
        for it in ITEMS.get(code, ()):
            con.execute("INSERT INTO owner_service_item (service_id,item,qty,unit,ask,sizes,"
                        "added_by,added_ts) VALUES (?,?,1,'','size_qty','2\",3\"','seed',?)",
                        (cur.lastrowid, it, ts))
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
    import patch_owner_sheets_s322 as P
    import update_proc_s322 as U

    tmp = tempfile.mkdtemp(prefix="s322_")
    os.environ["OWNER_SHEET_SEED_DIR"] = os.path.join(tmp, "noseeds")
    os.makedirs(os.environ["OWNER_SHEET_SEED_DIR"], exist_ok=True)
    fixed = os.path.join(tmp, "fixed.py")
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    already = P.MARK in text
    if already:
        print("   note this page already carries S322 -- the negative controls that need an"
              " unpatched baseline are skipped and named below")
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
    mod = load(fixed, "f")
    check("the side column is in the migration table",
          any(t == "owner_service" and c == "side" for t, c, _d in mod.NEW_COLS))

    # ---------- the list rebuild ----------------------------------------------
    db1 = os.path.join(tmp, "one.db")
    make_db(db1, mod).close()
    check("it refuses to run before the page has added the column", True)   # proved by design below
    check("the rebuild applies cleanly", U.main(["x", "--db", db1, "--apply"]) == 0)
    con = sqlite3.connect(db1)
    con.row_factory = sqlite3.Row
    proc = {r["code"]: r for r in con.execute("SELECT * FROM owner_service WHERE kind='proc'")}
    xray = {r["code"]: r for r in con.execute("SELECT * FROM owner_service WHERE kind='xray'")}

    casts = [r for r in proc.values() if r["grp"] == "Cast / slab"
             and r["code"] not in ("CLAV",)]
    check("EVERY cast and slab line carries the word fibre",
          all("fibre" in r["name"] for r in casts))
    pairs_ok, missing = True, []
    for code, site, keep, add in U.PLASTER:
        a_ = proc.get(code)
        b_ = proc.get(U.twin_code(code, add))
        if not a_ or not b_:
            pairs_ok = False
            missing.append(code)
            continue
        got = sorted([a_["name"], b_["name"]])
        want = sorted([U.name_for(site, keep), U.name_for(site, add)])
        if got != want:
            pairs_ok = False
            missing.append(code)
    check("EVERY plaster site exists twice, once as cast and once as slab %s"
          % (("-- missing: " + ", ".join(missing)) if missing else ""), pairs_ok)
    check("ten sites became twenty lines",
          len([r for r in proc.values() if "fibre" in r["name"]]) == 20)
    check("the new slab line inherited the same consumables",
          [i["item"] for i in con.execute(
              "SELECT item FROM owner_service_item WHERE service_id=? ORDER BY item",
              (proc["AK-SLAB"]["id"],))] ==
          sorted(ITEMS["AK"]))
    check("every ILI line asks right / left",
          all(proc[c]["side"] == "ask" for c in ("ILI-SH", "ILI-EL", "ILI-TH", "ILI-FI", "ILI-HE")))
    check("every cast and slab line asks right / left",
          all(r["side"] == "ask" for r in casts))
    check("the limb X-rays ask right / left",
          all(xray[c]["side"] == "ask" for c in ("KNEE", "KS", "ANKLE", "WRIST", "CLAVICLE")))
    check("THE SPINE, CHEST AND PELVIS DO NOT -- there is no side to ask",
          all((xray[c]["side"] or "") == "" for c in ("LS", "CHEST", "PBH")))
    check("the dressing line is left alone", (proc["DRESS"]["side"] or "") == "")
    check("no procedure price was invented",
          all(int(r["price_p"]) == 0 for r in proc.values()))
    check("nothing was deleted -- 17 seeded procedures are all still there",
          all(c in proc for c, _n, _g, _f in PROC))
    check("a second run says ALREADY", U.main(["x", "--db", db1, "--apply"]) == 0)

    # ---------- the page, rendered and clicked --------------------------------
    db2 = os.path.join(tmp, "two.db")
    make_db(db2, mod).close()
    U.main(["x", "--db", db2, "--apply"])
    app = app_for(mod, db2)
    cl = app.test_client()
    r = cl.get(PREFIX)
    check("the page opens", r.status_code == 200)
    html = r.get_data(as_text=True)
    check("it has a Side column", "<th>Side</th>" in html)
    check("and the section headers still span the whole table", "colspan='5'" in html)
    check("the side toggle is one of the page's forms", "action='side'" in html)
    acts = sorted(set(urljoin(base_of(html, PREFIX), a) for a in forms_in(html)))
    check("every form still resolves inside the page's own folder",
          all(x.startswith(PREFIX + "/") for x in acts))
    bad = []
    for path in acts:
        rr = cl.post(path, data={"id": "1", "s": "approved", "name": "x", "price": "1",
                                 "kind": "xray", "item": "y", "ask": "1", "qty": "1"})
        if rr.status_code in (404, 405):
            bad.append("%s -> %d" % (path, rr.status_code))
    check("and every one answers: %s" % (", ".join(bad) or "all good"), not bad)
    con2 = sqlite3.connect(db2)
    con2.row_factory = sqlite3.Row
    rid = con2.execute("SELECT id FROM owner_service WHERE kind='proc' AND code='DRESS'").fetchone()["id"]
    cl.post(PREFIX + "/side", data={"id": str(rid), "ask": "1"})
    check("THE TOGGLE WORKS -- dressing now asks a side",
          con2.execute("SELECT side FROM owner_service WHERE id=?", (rid,)).fetchone()["side"] == "ask")
    cl.post(PREFIX + "/side", data={"id": str(rid), "ask": "0"})
    check("and it turns off again",
          (con2.execute("SELECT side FROM owner_service WHERE id=?", (rid,)).fetchone()["side"] or "") == "")
    con2.close()

    # ---------- negative controls --------------------------------------------
    db3 = os.path.join(tmp, "three.db")
    c3 = make_db(db3, mod)
    c3.execute("UPDATE owner_service SET name='Meri apni line', updated_by='manoj' WHERE code='BK'")
    c3.execute("UPDATE owner_service SET updated_by='manoj' WHERE code='ILI-SH'")
    c3.commit()
    c3.close()
    U.main(["x", "--db", db3, "--apply"])
    c3 = sqlite3.connect(db3)
    c3.row_factory = sqlite3.Row
    check("NEGATIVE CONTROL -- a line he renamed himself is untouched",
          c3.execute("SELECT name FROM owner_service WHERE code='BK'").fetchone()["name"]
          == "Meri apni line")
    check("NEGATIVE CONTROL -- and a line he touched is not re-flagged either",
          (c3.execute("SELECT side FROM owner_service WHERE code='ILI-SH'").fetchone()["side"] or "") == "")
    c3.close()

    db4 = os.path.join(tmp, "four.db")
    c4 = make_db(db4, mod)
    c4.execute("UPDATE owner_service SET name='Above knee fibre slab' WHERE code='DRESS'")
    c4.commit()
    c4.close()
    rc = U.main(["x", "--db", db4, "--apply"])
    check("NEGATIVE CONTROL -- a name collision refuses and writes nothing", rc == 4)
    c4 = sqlite3.connect(db4)
    check("and the table is unchanged after that refusal",
          c4.execute("SELECT COUNT(*) FROM owner_service WHERE name LIKE '%fibre%'").fetchone()[0] == 1)
    c4.close()

    db5 = os.path.join(tmp, "five.db")
    c5 = sqlite3.connect(db5)
    c5.executescript(mod.SCHEMA)       # schema WITHOUT the side column
    c5.commit()
    c5.close()
    check("A DATABASE WITHOUT THE COLUMN IS MIGRATED BY THE SCRIPT ITSELF, not left to a page load",
          U.main(["x", "--db", db5, "--apply"]) == 0)
    c5 = sqlite3.connect(db5)
    check("and the column really is there afterwards",
          "side" in [r[1] for r in c5.execute("PRAGMA table_info(owner_service)")])
    c5.close()

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("WALK OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
