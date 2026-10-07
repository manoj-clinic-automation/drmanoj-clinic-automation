#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s495.py -- S495_LIST_PAGE_FLOORS: the walk. WRITES NOTHING LIVE.

It works in a private scratch folder. The box's own finance code is COPIED there (never imported from /root/finance, never
written); the four files are edited on the copies by apply_s495.py; aaj_floor.py is put beside them. Every page is then
asked TWICE through Flask's own test client -- once of the file as it is live (loaded under another name, on an app of
its own) and once of the edited file -- on the same database, as the same login, and the two answers are compared.

  THE MADE-UP CLINIC (always): an empty database with the real tables, cut from the code's own CREATE TABLE statements
  (made whole on the live shape when --db is given: names and types only, no row read), with the walk's own made-up rows --
  for each page one dated before the floor and one after.
    A  the edits: each file at its pin, each anchor found, each result the kit's own bytes; everything compiles
    B  aaj_floor.py by itself: None for the owner, None for any doctor, None while the lists are not started, None when it
       cannot be told; the day by the setting aaj.from, else 01-Oct-2026
    C  LISTS NOT STARTED: every page, for staff and for the owner, is byte for byte what the live file gives
    D  LISTS STARTED, a staff login: the row before the floor is gone from each page, the row after is there
       (and the live file still shows both -- the negative control)
    E  LISTS STARTED, the owner -- and a doctor who is not the owner: every page is byte for byte what the live file gives
    F  what must NOT move: the doctors' line and counts, an answer and an action on an old item by its key
    G  the guards: no aaj_floor.py, or one that raises -- every page is byte for byte what the live file gives
    H  the floor follows the setting

  THE LIVE SHAPE (only with --db): a COPY of finance.db (SQLite's backup through a read-only door) in the scratch folder,
  with the lists marked started ON THE COPY. The four pages are asked as a staff login and as the owner: the staff's pages
  name no day before the floor that the live file does not also... (see S1-S4); the owner's are byte for byte the live
  file's. No name and no figure is printed -- counts only.

Last line: WALK_S495 GREEN|RED <n> checks, <f> fail
   usage: walk_s495.py --kit <dir> --finance <dir> [--code <dir>]... [--db <finance.db>] [--keep]
"""
import ast
import datetime as dt
import hashlib
import importlib
import importlib.util
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
CHECKS, FAILS, NOTES = [], [], []
FILES = ("clinic_register.py", "records.py", "slip_log.py", "petty_book.py")
PAGES = ("/finance/clinic/register/list", "/finance/checks", "/finance/slips/pending", "/finance/slips/pending?t=xray", "/finance/petty")


def check(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  ok   %s" % name)
    else:
        FAILS.append(name)
        print("  FAIL %s%s" % (name, ("  -- " + str(detail)[:400]) if detail != "" else ""))
    return bool(cond)


def note(text):
    NOTES.append(text)
    print("  note %s" % text)


def args(name):
    a, out = sys.argv, []
    for i, v in enumerate(a):
        if v == name and i + 1 < len(a):
            out.append(a[i + 1])
    return out


def arg(name, default=None):
    v = args(name)
    return v[0] if v else default


def md5f(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def backup(src, dst):
    a = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    try:
        b = sqlite3.connect(dst)
        try:
            a.backup(b)
        finally:
            b.close()
    finally:
        a.close()


def copy_code(src, dst):
    """The finance app's code and small data files -- no database, no backup, no upload."""
    keep = (".py", ".html", ".json", ".sql", ".js", ".css", ".txt")
    os.makedirs(dst, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if os.path.isfile(p) and name.endswith(keep) and ".bak" not in name and not name.startswith(".") and not name.startswith("console_") \
                and os.path.getsize(p) < 6_000_000:
            shutil.copy2(p, os.path.join(dst, name))
            n += 1
    return n


# ------------------------------------------------------------------------------------------ the made-up clinic's tables
CT = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.I)
AL = re.compile(r"ALTER\s+TABLE\s+([A-Za-z_][A-Za-z0-9_]*)\s+ADD\s+COLUMN\s+([^;\"']+)", re.I)
PATCH = (("blood_order", "later_until TEXT"), ("clinic_physio_day", "received_at TEXT"))


def _stmt(text, start):
    i, depth = text.index("(", start), 0
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[start:j + 1]
    return None


def schema_from_code(dirs):
    import warnings
    creates, alters = {}, []
    for d in dirs:
        for root, sub, files in os.walk(d):
            sub[:] = [x for x in sub if not x.startswith((".", "__"))]
            for f in sorted(files):
                if not f.endswith((".py", ".sql")) or ".bak" in f:
                    continue
                try:
                    src = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                texts = [src]
                if f.endswith(".py"):
                    texts = []
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            tree = ast.parse(src)
                    except SyntaxError:
                        continue
                    for n in ast.walk(tree):
                        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "TABLE" in n.value.upper():
                            texts.append(n.value)
                for s in texts:
                    for m in CT.finditer(s):
                        st = _stmt(s, m.start())
                        if st and m.group(1) not in creates:
                            creates[m.group(1)] = st
                    for m in AL.finditer(s):
                        alters.append("ALTER TABLE %s ADD COLUMN %s" % (m.group(1), m.group(2).strip()))
    return creates, alters


def make_clinic(path, code_dirs, real_db=None):
    con = sqlite3.connect(path)
    creates, alters = schema_from_code(code_dirs)
    n = 0
    for _t, st in creates.items():
        try:
            con.execute(st)
            n += 1
        except sqlite3.Error:
            pass
    for st in alters + ["ALTER TABLE %s ADD COLUMN %s" % p for p in PATCH]:
        try:
            con.execute(st)
        except sqlite3.Error:
            pass
    how = "%d tables cut from the code's own CREATE TABLE statements" % n
    if real_db:
        src = sqlite3.connect("file:%s?mode=ro" % real_db, uri=True, timeout=60)
        mine = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        added = made = 0
        for name, sql in src.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL").fetchall():
            if name not in mine:
                try:
                    con.execute(sql)
                    made += 1
                except sqlite3.Error:
                    pass
                continue
            have = {r[1] for r in con.execute("PRAGMA table_info(%s)" % name)}
            for r in src.execute("PRAGMA table_info(%s)" % name).fetchall():
                if r[1] not in have:
                    try:
                        con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (name, r[1], r[2] or "TEXT"))
                        added += 1
                    except sqlite3.Error:
                        pass
        src.close()
        how += "; made whole on the live shape (%d columns, %d tables added, no row read)" % (added, made)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.commit()
    con.close()
    return how


def put(con, table, **cols):
    info = con.execute("PRAGMA table_info(%s)" % table).fetchall()
    if not info:
        raise RuntimeError("no such table in the made-up clinic: %s" % table)
    names = [x[1] for x in info]
    for k in cols:
        if k not in names:
            raise RuntimeError("%s has no column %s" % (table, k))
    row = dict(cols)
    for _cid, name, typ, notnull, dflt, pk in info:
        if name in row or not notnull or dflt is not None or (pk and "INT" in str(typ).upper()):
            continue
        row[name] = 0 if any(w in str(typ).upper() for w in ("INT", "REAL", "NUM")) else ""
    ks = list(row)
    con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(ks), ",".join("?" * len(ks))), [row[k] for k in ks])


# ------------------------------------------------------------------------------------------ two services on one database
class Who:
    """Who is signed in, for both apps at once. owner: checker everywhere, the month's packs too. doctor (not the owner):
    checker of the clinic's pages, nothing on the packs. Anyone else: a maker on the clinic's pages."""
    user, owner, doctor = "alisha", False, False

    @classmethod
    def require(cls, *roles, unit=None):
        if cls.owner:
            have = {"checker"}
        elif cls.doctor:
            have = {"checker"} if unit != "packs" else set()
        else:
            have = {"maker"} if unit != "packs" else set()
        if not have & set(roles):
            return None, ("not_permitted", 403)
        return {"user": cls.user, "role": ("doctor" if (cls.owner or cls.doctor) else "staff"), "roles": sorted(have)}, None


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def mount(mods, con):
    from flask import Flask
    app = Flask("walk_s495_%d" % id(mods))
    mods["clinic_register"].init(app, lambda: con, Who.require, None, unit="clinic")
    mods["records"].init(app, lambda: con, Who.require, None)
    mods["slip_log"].init(app, lambda: con, Who.require, None)
    mods["petty_book"].init(app, lambda: con, Who.require, None)
    return app.test_client()


def norm(b):
    """A page's bytes with the clock taken out (a minute can turn between two askings)."""
    return re.sub(rb"\b\d\d:\d\d(?::\d\d)?\b", b"HH:MM", b)


def get(c, url, user="alisha", owner=False, doctor=False):
    Who.user, Who.owner, Who.doctor = user, owner, doctor
    r = c.get(url)
    return r.status_code, r.get_data()


def main():
    kit, fin = arg("--kit"), arg("--finance")
    if not (kit and fin):
        print(__doc__)
        print("WALK_S495 RED 0 checks, 1 fail")
        return 2
    # the folder this script runs from holds aaj_floor.py: it never stays on the path, or 'no aaj_floor.py' could not be walked
    # (compared by their REAL paths: Python puts the script's folder on the path with every link in it resolved)
    here = {os.path.realpath(os.path.dirname(os.path.abspath(__file__))), os.path.realpath(kit)}
    sys.path[:] = [p for p in sys.path if os.path.realpath(p or ".") not in here]
    scratch = tempfile.mkdtemp(prefix="walk_s495_")
    try:
        os.chmod(scratch, 0o700)
        return walk(kit, fin, arg("--db"), args("--code") or [fin], scratch)
    finally:
        if "--keep" in sys.argv:
            print("  kept %s" % scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)


def walk(kit, fin, real_db, code_dirs, scratch):
    today = dt.date.today()
    D = lambda n: (today - dt.timedelta(days=n)).isoformat()             # noqa: E731
    floor, OLD, NEW = D(5), D(8), D(3)

    # ---------------------------------------------------------------------------------------- A  the edits
    print("A  the edits")
    code = os.path.join(scratch, "code")
    n = copy_code(fin, code)
    live = os.path.join(scratch, "live_files")
    os.makedirs(live)
    for f in FILES:
        shutil.copy2(os.path.join(fin, f), os.path.join(live, f))
    ap = load(os.path.join(kit, "apply_s495.py"), "apply_s495")           # by its file: the kit's folder never goes on the path (it holds aaj_floor.py)
    frm = {f: md5f(os.path.join(code, f)) for f in FILES}
    check("A1 the four live files are at the pins this kit was built on", all(frm[f] == ap.PINS[f][0] for f in FILES), frm)
    r = subprocess.run([sys.executable, "-B", os.path.join(kit, "apply_s495.py"), code], capture_output=True, text=True, timeout=120)
    to = {f: md5f(os.path.join(code, f)) for f in FILES}
    check("A2 the edits apply, each anchor found exactly as written, and give the kit's own bytes", r.returncode == 0 and all(to[f] == ap.PINS[f][1] for f in FILES),
          (r.returncode, (r.stdout + r.stderr)[-300:]))
    r2 = subprocess.run([sys.executable, "-B", os.path.join(kit, "apply_s495.py"), code], capture_output=True, text=True, timeout=120)
    check("A3 applied twice, the second time is refused and nothing moves", r2.returncode != 0 and all(md5f(os.path.join(code, f)) == to[f] for f in FILES), r2.returncode)
    for f in FILES:
        a, b = open(os.path.join(live, f), encoding="utf-8").read().splitlines(), open(os.path.join(code, f), encoding="utf-8").read().splitlines()
        gone = [x for x in a if x not in b]
        check("A4 %s: nothing of the live file is lost but the line(s) the edit rewrites" % f, len(gone) <= 2 and len(b) > len(a), (len(gone), gone[:3]))
    shutil.copy2(os.path.join(kit, "aaj_floor.py"), os.path.join(code, "aaj_floor.py"))
    note("%d code files copied to the scratch folder; aaj_seed.py %s" % (n, "is there (S493 installed)" if os.path.exists(os.path.join(code, "aaj_seed.py")) else "is not there"))

    # ---------------------------------------------------------------------------------------- the made-up clinic
    db = os.path.join(scratch, "clinic.db")
    note("the made-up clinic: %s" % make_clinic(db, code_dirs, real_db))
    con = sqlite3.connect(db, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('aaj.from', ?, 'walk')", (floor,))
    put(con, "clinic_register_day", business_date=D(30))
    for d, tag in ((OLD, "ZOLD"), (NEW, "ZNEW")):
        put(con, "clinic_day_revenue", business_date=d)
        put(con, "clinic_physio_day", business_date=d, cash_p=12300)
        put(con, "blood_order", day=d, clinic_id=tag, name_seen="Walk " + tag, state="ok")
        put(con, "xray_filing", src_id="walk-" + tag, orig_name=tag + ".jpg", state="check", day=d, planned_at=d + " 10:00:00")
        put(con, "xray_filing", src_id="walk-noday-" + tag, orig_name="noday-" + tag + ".jpg", state="check", day="", planned_at=d + " 10:00:00")
        sid = con.execute("SELECT COALESCE(MAX(id),0)+1 FROM slip").fetchone()[0]
        put(con, "slip", id=sid, series="xp", slip_no=sid, state="ok", clinic_id="X" + tag, name_seen="Walk X" + tag, day=d)
        put(con, "slip_item", slip_id=sid, kind="xray", name="Knee AP")
    con.commit()

    sys.path.insert(0, code)
    for m in ("clinic_register", "records", "slip_log", "petty_book", "aaj_floor", "aaj_seed"):
        sys.modules.pop(m, None)
    new = {m[:-3]: importlib.import_module(m[:-3]) for m in FILES}
    old = {m[:-3]: load(os.path.join(live, m), "live_" + m[:-3]) for m in FILES}
    cn, co = mount(new, con), mount(old, con)
    for u in PAGES:                                                       # a first asking makes each page's own tables
        get(co, u), get(cn, u)
    con.commit()
    fl = importlib.import_module("aaj_floor")

    def start(on):
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('aaj.staff_on', ?, 'walk')", ((D(1) + "T09:00:00|manoj") if on else "",))
        con.commit()

    # ---------------------------------------------------------------------------------------- B  the helper by itself
    print("B  aaj_floor.py by itself")
    start(False)
    Who.user, Who.owner = "alisha", False
    check("B1 lists not started: no floor for anyone", fl.floor_for(con, Who.require) is None and fl.started(con) is False)
    start(True)
    check("B2 started, a staff login: the floor is the setting's day", fl.floor_for(con, Who.require) == floor, fl.floor_for(con, Who.require))
    Who.owner = True
    check("B3 started, the owner: no floor", fl.floor_for(con, Who.require, {"user": "manoj", "role": "doctor"}) is None and fl.floor_for(con, Who.require) is None)
    Who.owner = False
    check("B3b started, a doctor who holds nothing on the packs: no floor either", fl.floor_for(con, Who.require, {"user": "bhawna", "role": "Doctor"}) is None
          and fl.floor_for(con, Who.require, {"user": "shavez", "role": "manager"}) == floor)
    con.execute("UPDATE setting SET value='not a day' WHERE key='aaj.from'")
    dflt = fl.floor_for(con, Who.require)
    con.execute("DELETE FROM setting WHERE key='aaj.from'")
    dflt2 = fl.floor_for(con, Who.require)
    check("B4 a setting that is not a day, or no setting: 01-Oct-2026", dflt == "2026-10-01" == dflt2, (dflt, dflt2))
    con.execute("INSERT INTO setting (key, value, note) VALUES ('aaj.from', ?, 'walk')", (floor,))
    con.execute("UPDATE setting SET value='yes' WHERE key='aaj.staff_on'")
    check("B5 a switch that does not read as started is not started", fl.floor_for(con, Who.require) is None)
    con.commit()
    empty = sqlite3.connect(":memory:")
    check("B6 no setting table at all: no floor, and no error", fl.floor_for(empty, Who.require) is None)
    check("B7 a login check that raises: no floor, and no error", fl.floor_for(con, lambda *a, **k: 1 / 0) is None)
    check("B8 keep(): rows on or after the floor; all of them with no floor; a row with no day goes",
          fl.keep([{"day": OLD}, {"day": NEW}, {"day": ""}, {}], floor) == [{"day": NEW}] and len(fl.keep([{"day": OLD}, {}], None)) == 2)

    # ---------------------------------------------------------------------------------------- C  not started
    print("C  lists not started: every page is the live file's page")
    start(False)
    for u in PAGES:
        for user, owner in (("alisha", False), ("manoj", True)):
            a, b = get(co, u, user, owner), get(cn, u, user, owner)
            check("C1 %s as %s" % (u, "the owner" if owner else "staff"), a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]) and len(b[1]) > 500, (a[0], b[0], len(a[1]), len(b[1])))

    # ---------------------------------------------------------------------------------------- D  started, staff
    print("D  lists started, a staff login")
    start(True)
    marks = {
        "/finance/clinic/register/list": ("/finance/clinic/register/%s'" % OLD, "/finance/clinic/register/%s'" % NEW),
        "/finance/checks": ('value="bo:%s:ZOLD"' % OLD, 'value="bo:%s:ZNEW"' % NEW),
        "/finance/slips/pending": ("Walk ZOLD", "Walk ZNEW"),
        "/finance/slips/pending?t=xray": ("Walk XZOLD", "Walk XZNEW"),
        "/finance/petty": ("/finance/petty/physio/%s'" % OLD, "/finance/petty/physio/%s'" % NEW),
    }
    for u, (mo, mn) in marks.items():
        a, b = get(co, u)[1].decode("utf-8"), get(cn, u)[1].decode("utf-8")
        check("D1 %s: the live file shows the row before the floor and the row after (the negative control)" % u, mo in a and mn in a, (mo in a, mn in a))
        check("D2 %s: the edited file shows the row after, and NOT the one before" % u, mo not in b and mn in b, (mo in b, mn in b))
    b = get(cn, "/finance/checks")[1].decode("utf-8")
    check("D3 Check karein: an X-ray file with a day by its day; one with no day by the day it was first seen",
          'value="xf:walk-ZNEW"' in b and 'value="xf:walk-noday-ZNEW"' in b and 'value="xf:walk-ZOLD"' not in b and 'value="xf:walk-noday-ZOLD"' not in b)
    st, body = get(cn, "/finance/clinic/register")
    Who.user, Who.owner = "alisha", False
    loc = cn.get("/finance/clinic/register").headers.get("Location", "")
    check("D4 the counter sheet still opens on today (the newest day not filled)", st == 302 and loc.endswith("/finance/clinic/register/" + today.isoformat()), (st, loc))
    for d in (today.isoformat(), NEW):
        put(con, "clinic_register_day", business_date=d)
    con.commit()
    lo = co.get("/finance/clinic/register").headers.get("Location", "")
    r = cn.get("/finance/clinic/register")
    check("D5 with only a day before the floor left unfilled: the live file sends staff to it, the edited file says nothing is left",
          lo.endswith("/finance/clinic/register/" + OLD) and r.status_code == 200 and b"Nothing left to fill" in r.get_data(), (lo, r.status_code))
    con.execute("DELETE FROM clinic_register_day WHERE business_date IN (?,?)", (today.isoformat(), NEW))
    con.commit()
    for u in ("/finance/clinic/register/%s" % OLD,):
        a, b = get(co, u), get(cn, u)
        check("D6 a day before the floor opened by its own address is as before (the floor is on the LIST)", a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]), (a[0], b[0]))

    # ---------------------------------------------------------------------------------------- E  started, the owner
    print("E  lists started, the owner and a doctor: every page is the live file's page")
    for u in PAGES:
        a, b = get(co, u, "manoj", True), get(cn, u, "manoj", True)
        check("E1 %s as the owner" % u, a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]), (a[0], b[0], len(a[1]), len(b[1])))
        a, b = get(co, u, "bhawna", False, True), get(cn, u, "bhawna", False, True)
        check("E2 %s as a doctor who is not the owner" % u, a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]), (a[0], b[0], len(a[1]), len(b[1])))
    Who.doctor = False

    # ---------------------------------------------------------------------------------------- F  what must not move
    print("F  what must not move")
    cl_o, cl_n = old["records"].check_line(con), new["records"].check_line(con)
    check("F1 the doctors' line of Check karein counts every item, old and new", cl_o == cl_n and cl_n[1] >= 6, (cl_o, cl_n))
    pc_o, pc_n = old["slip_log"].pending_counts(con), new["slip_log"].pending_counts(con)
    check("F2 the doctors' counts of Report baaki are whole", pc_o == pc_n and pc_n and pc_n["blood"] >= 2 and pc_n["xray"] >= 2, (pc_o, pc_n))
    Who.user, Who.owner = "alisha", False
    r = cn.post("/finance/checks/answer", data={"key": "bo:%s:ZOLD" % OLD, "a": "asked"})
    row = con.execute("SELECT answer FROM record_check WHERE key=?", ("bo:%s:ZOLD" % OLD,)).fetchone()
    check("F3 an answer on an item from before the floor, sent by its key, is still taken", r.status_code in (302, 303) and row is not None, (r.status_code, row))
    bid = con.execute("SELECT id FROM blood_order WHERE clinic_id='ZOLD'").fetchone()[0]
    r = cn.post("/finance/slips/pending/act", data={"key": "b:%d" % bid, "act": "not_tested"})
    oc = con.execute("SELECT outcome FROM blood_order WHERE id=?", (bid,)).fetchone()[0]
    check("F4 an action on a blood test from before the floor, sent by its key, is still taken", r.status_code in (302, 303) and oc == "not_tested", (r.status_code, oc))
    con.execute("UPDATE blood_order SET outcome='' WHERE id=?", (bid,))
    con.execute("DELETE FROM record_check WHERE key=?", ("bo:%s:ZOLD" % OLD,))
    con.commit()

    # ---------------------------------------------------------------------------------------- G  the guards
    print("G  the guards")
    real = fl.floor_for
    fl.floor_for = lambda *a, **k: 1 / 0
    for u in PAGES:
        a, b = get(co, u), get(cn, u)
        check("G1 the helper raises: %s is the live file's page" % u, a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]), (a[0], b[0]))
    fl.floor_for = real
    os.rename(os.path.join(code, "aaj_floor.py"), os.path.join(code, "aaj_floor.away"))
    saved = sys.modules.pop("aaj_floor")
    importlib.invalidate_caches()
    for u in PAGES:
        a, b = get(co, u), get(cn, u)
        check("G2 no aaj_floor.py: %s is the live file's page" % u, a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]), (a[0], b[0]))
    os.rename(os.path.join(code, "aaj_floor.away"), os.path.join(code, "aaj_floor.py"))
    sys.modules["aaj_floor"] = saved
    importlib.invalidate_caches()
    b = get(cn, "/finance/checks")[1].decode("utf-8")
    check("G3 the helper back: the floor is back", 'value="bo:%s:ZOLD"' % OLD not in b and 'value="bo:%s:ZNEW"' % NEW in b)

    # ---------------------------------------------------------------------------------------- H  the setting
    print("H  the floor follows the setting")
    con.execute("UPDATE setting SET value=? WHERE key='aaj.from'", (D(20),))
    con.commit()
    b = get(cn, "/finance/checks")[1].decode("utf-8")
    check("H1 the floor moved back before both rows: both are shown", 'value="bo:%s:ZOLD"' % OLD in b and 'value="bo:%s:ZNEW"' % NEW in b)
    con.execute("UPDATE setting SET value=? WHERE key='aaj.from'", (D(1),))
    con.commit()
    st, raw = get(cn, "/finance/slips/pending?t=xray")
    b = raw.decode("utf-8")
    check("H2 the floor moved after both rows: neither is shown, on a page that is whole", st == 200 and "X-ray photo baaki" in b and "Walk XZOLD" not in b and "Walk XZNEW" not in b, st)
    con.execute("UPDATE setting SET value=? WHERE key='aaj.from'", (floor,))
    con.commit()
    con.execute("ALTER TABLE xray_filing RENAME TO xray_filing_away")
    a, b = get(co, "/finance/checks"), get(cn, "/finance/checks")
    con.execute("ALTER TABLE xray_filing_away RENAME TO xray_filing")
    con.commit()
    check("H3 the page's own read for the floor fails: the page is the live file's page (a failed read is never an empty answer)",
          a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]) and ('value="bo:%s:ZOLD"' % OLD).encode() in b[1], (a[0], b[0], len(a[1]), len(b[1])))
    con.close()

    # ---------------------------------------------------------------------------------------- the live shape
    if real_db:
        print("LIVE SHAPE  a copy of finance.db, the lists marked started on the copy")
        lv = os.path.join(scratch, "live.db")
        backup(real_db, lv)
        lc = sqlite3.connect(lv, check_same_thread=False)
        lc.row_factory = sqlite3.Row
        lc.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('aaj.staff_on', ?, 'walk')", (D(0) + "T00:00:01|walk",))
        lc.commit()
        Who.user, Who.owner = "alisha", False
        f = importlib.import_module("aaj_floor").floor_for(lc, Who.require)
        check("S1 the floor on the live shape is 01-Oct-2026 (or the owner's own aaj.from)", bool(f) and f >= "2026-10-01", f)
        ln, lo = mount(new, lc), mount(old, lc)
        for u in PAGES:
            get(lo, u), get(ln, u)
        lc.commit()
        day_re = re.compile(r"(?:register/|physio/|bo:|xm:|orph:)(20\d\d-\d\d-\d\d)")
        for u in PAGES:
            a, b = get(lo, u), get(ln, u)
            da, dbb = day_re.findall(a[1].decode("utf-8", "replace")), day_re.findall(b[1].decode("utf-8", "replace"))
            before = [d for d in dbb if d < f]
            check("S2 %s as staff: it answers, and names no day before the floor" % u, b[0] == 200 and not before, (b[0], len(before)))
            note("%s as staff: the live file names %d day(s), %d of them before the floor; the edited file names %d" % (u, len(da), len([d for d in da if d < f]), len(dbb)))
            note("%s as staff: the page is %d bytes live, %d bytes edited" % (u, len(a[1]), len(b[1])))
        for u in PAGES:
            a, b = get(lo, u, "manoj", True), get(ln, u, "manoj", True)
            check("S3 %s as the owner: byte for byte the live file's page" % u, a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]), (a[0], b[0], len(a[1]), len(b[1])))
        lc.execute("UPDATE setting SET value='' WHERE key='aaj.staff_on'")
        lc.commit()
        for u in PAGES:
            a, b = get(lo, u), get(ln, u)
            check("S4 %s as staff with the lists NOT started: byte for byte the live file's page" % u, a[0] == b[0] == 200 and norm(a[1]) == norm(b[1]), (a[0], b[0], len(a[1]), len(b[1])))
        lc.close()

    f = len(FAILS)
    print("WALK_S495 %s %d checks, %d fail" % ("GREEN" if not f else "RED", len(CHECKS), f))
    return 0 if not f else 1


if __name__ == "__main__":
    sys.exit(main())
