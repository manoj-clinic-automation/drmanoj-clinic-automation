#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s493.py -- S493_LISTS_2: the walk. WRITES NOTHING LIVE.

It works in a private scratch folder: the kit's four files, the duties file and the duty map are COPIED there and the module
is imported from the copies. Two databases are walked:

  THE MADE-UP CLINIC (always). An empty database with the real tables, cut from the CREATE TABLE statements in the code
  under --code -- the same way on the build machine and on the server, so the walk that ran green where the kit was made is
  the walk that runs on the box. The walk puts its own made-up rows in it. Here every rule is proven, through Flask's own
  test client:
    A  the files: they compile, say what the kit says, and hold the owner's mock-up as he left it
    B  every line's SQL runs on the floored connection; every floor view lays
    C  THE FLOOR: for each dated table a row before the floor and a row after -- the line counts only the one after;
       work no view catches is HELD BACK when it is dated before the floor; the owner's own lines keep 1.0's floor
       (asked of 1.0 itself when --old is given), except the two tables he ruled off
    D  who sees what: off until the owner's Start; a switch per person and per line; the desk's logins share one list
    E  one line = one job: his wording, his order, his groups; the job's own day in the door; two duties, one line
    F  what a save may hold: a page cannot send a line's working; a line he adds is a tap line
    G  taps: once, the first stands; weekly and monthly lines begin after the lists start
    H  a list that is not whole says so; a floor that cannot be laid holds its lines back; a saved panel that cannot be
       read switches every list OFF (what he switched off never comes back on by a fault)
    I  tasks: given, answered, sent back, closed; who may give; who may answer
    J  September, for him only
    K  the console's contract: build_all() has every key owner_console.py reads, and its own functions run on it
    L  the pages: no count, no 'late'; the scripts parse (when node is on the box)

  THE LIVE SHAPE (only with --db: a copy of finance.db made with SQLite's backup through a read-only door). Nothing is
  written to it. Every floor view lays, every line of every person is read, no floored view holds a row before the floor,
  the owner's own counts equal 1.0's, and the copy is byte-identical afterwards. What each person would see today is noted.

Last line: WALK_S493 GREEN|RED <n> checks, <f> fail
   usage: walk_s493.py --kit <dir> --finance <dir> --dutymap <DUTY_MAP.json> [--code <dir>]... [--db <finance.db>]
                       [--old <aaj_kaam.py of 1.0>] [--console <owner_console.py>] [--allow-unread N] [--keep]
"""
import ast
import datetime as dt
import hashlib
import importlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
CHECKS, FAILS, NOTES = [], [], []


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


# ------------------------------------------------------------------------------------------ the made-up clinic's tables
CT = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.I)
AL = re.compile(r"ALTER\s+TABLE\s+([A-Za-z_][A-Za-z0-9_]*)\s+ADD\s+COLUMN\s+([^;\"']+)", re.I)
# columns the code adds by a helper the cutter cannot follow -- wanted only when the shape is cut from code
PATCH = (("stock_writeoff_run", "kind TEXT"), ("purchase_order_line", "arrived_at TEXT"), ("mi_file", "reason TEXT"),
         ("purchase_order", "received_at TEXT"), ("purchase_order", "order_src TEXT"), ("purchase_scan_state", "likely_bill INTEGER"),
         ("purchase_scan_state", "confirmed_at TEXT"), ("blood_order", "later_until TEXT"), ("clinic_physio_day", "received_at TEXT"),
         ("purchase_order_line", "supplied REAL"), ("purchase_order_line", "billed_bill_no TEXT"), ("purchase_order", "supplier_norm TEXT"), ("purchase_scan_state", "amount_state TEXT"))


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
    creates, alters = {}, []
    for d in dirs:
        for root, sub, files in os.walk(d):
            sub[:] = [x for x in sub if not x.startswith((".", "__"))]
            for f in sorted(files):
                if not f.endswith((".py", ".sql")) or ".bak" in f:
                    continue
                p = os.path.join(root, f)
                try:
                    src = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                texts = [src]
                if f.endswith(".py"):
                    texts = []
                    try:
                        import warnings
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
    """An empty database with the real tables, cut from the code. Returns how it was shaped."""
    con = sqlite3.connect(path)
    creates, alters = schema_from_code(code_dirs)
    n = 0
    for _t, st in creates.items():
        try:
            con.execute(st)
            n += 1
        except sqlite3.Error:
            pass
    for st in alters:
        try:
            con.execute(st)
        except sqlite3.Error:
            pass
    for t, col in PATCH:
        try:
            con.execute("ALTER TABLE %s ADD COLUMN %s" % (t, col))
        except sqlite3.Error:
            pass
    how = "%d tables cut from the code's own CREATE TABLE statements" % n
    if real_db:
        # ON THE BOX: a column the live table has and the cut does not (added by a helper the cutter cannot follow, or by a
        # kit newer than the code this walk was built against) is added -- its name and type only. No row is read.
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
    """One made-up row: the named columns as given, every other NOT NULL column without a default filled by its type."""
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


# ------------------------------------------------------------------------------------------ the service, in miniature
class Svc:
    """aaj_kaam mounted on a bare Flask app with the two things finance_app gives it: who is signed in, and is he the owner."""

    def __init__(self, mod, db_path):
        from flask import Flask
        self.mod, self.db_path = mod, db_path
        self.app = Flask("walk_s493")
        self.con = sqlite3.connect(db_path, check_same_thread=False)
        self.user, self.owner = None, False
        self.fns = (lambda: self.con, lambda *roles, **kw: (({"user": self.user} if self.owner else None), None if self.owner else "no"),
                    lambda: ({"user": self.user} if self.user else None))
        mod.init(self.app, *self.fns)
        self.c = self.app.test_client()

    def me(self, user, owner=False):
        """Who is asking. The module keeps what init() gave it in three names of its own; a walk with two services at once
        hands them back to the one that is being asked."""
        self.user, self.owner = user, owner
        self.mod._db, self.mod._require, self.mod._user = self.fns
        return self

    def get(self, url):
        r = self.c.get(url)
        try:
            return r.status_code, json.loads(r.get_data(as_text=True))
        except ValueError:
            return r.status_code, r.get_data(as_text=True)

    def post(self, url, body, raw=False):
        r = self.c.post(url, data=body) if raw else self.c.post(url, json=body)
        try:
            return r.status_code, json.loads(r.get_data(as_text=True))
        except ValueError:
            return r.status_code, r.get_data(as_text=True)

    def lst(self, user, q=""):
        return self.me(user).get("/finance/aaj/api/list" + q)[1]

    def panel(self):
        return self.me("manoj", True).get("/finance/aaj/api/switch?panel=1")[1]

    def close(self):
        self.con.close()


def rows_of(d):
    return [r for s in (d.get("sections") or []) for r in s["rows"]]


def ids_of(d):
    return [r["id"] for r in rows_of(d)]


def row(d, rid):
    return next((r for r in rows_of(d) if r["id"] == rid), None)


def sec_of(d, rid):
    return next((s["key"] for s in (d.get("sections") or []) for r in s["rows"] if r["id"] == rid), None)


def doc_of(p):
    """The document the panel page sends for one person (aaj_panel.html docOf)."""
    def one(l):
        return {"id": l["id"], "hi": l["hi"], "en": l["en"], "when": l["when"], "on": bool(l["on"])}
    return {"on": bool(p["on"]), "note": p.get("note") or "", "lines": [one(l) for l in p["lines"]], "removed": [one(l) for l in p.get("removed") or []]}


def save(svc, key, change):
    """Read one person's panel, change it as the page would, save it. Returns the panel after."""
    p = next(x for x in svc.panel()["panel"]["people"] if x["key"] == key)
    d = doc_of(p)
    change(d)
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "person", "key": key, "base": p.get("edited_at"), "doc": d})
    assert st == 200 and j.get("ok") and j.get("edited_at"), (st, j)
    return next(x for x in svc.panel()["panel"]["people"] if x["key"] == key)


def main():
    kit, fin, dutymap = arg("--kit"), arg("--finance"), arg("--dutymap")
    if not (kit and fin and dutymap):
        print(__doc__)
        print("WALK_S493 RED 0 checks, 1 fail")
        return 2
    real_db, old_py, console_py = arg("--db"), arg("--old"), arg("--console")
    allow_unread = int(arg("--allow-unread", "0"))
    code_dirs = args("--code") or [fin]
    scratch = tempfile.mkdtemp(prefix="walk_s493_")
    try:
        return walk(kit, fin, dutymap, real_db, old_py, console_py, allow_unread, code_dirs, scratch)
    finally:
        if "--keep" in sys.argv:
            print("  kept %s" % scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)


def walk(kit, fin, dutymap, real_db, old_py, console_py, allow_unread, code_dirs, scratch):
    today = dt.date.today()
    D = lambda n: (today - dt.timedelta(days=n)).isoformat()             # noqa: E731 -- n days ago
    floor = D(5)                                                          # the made-up clinic's floor: five days ago, by the setting
    OLD, NEW = D(8), D(3)                                                 # a day before that floor, a day after it

    # ---------------------------------------------------------------------------------------- A  the files
    print("A  the files")
    code = os.path.join(scratch, "code")
    os.makedirs(code)
    for f in ("aaj_kaam.py", "aaj_seed.py", "aaj_kaam.html", "aaj_panel.html"):
        shutil.copy2(os.path.join(kit, f), os.path.join(code, f))
    shutil.copy2(os.path.join(fin, "aaj_duties.json"), os.path.join(code, "aaj_duties.json"))
    shutil.copy2(dutymap, os.path.join(code, "DUTY_MAP.json"))
    os.environ["DUTY_MAP_JSON"] = os.path.join(code, "DUTY_MAP.json")
    os.environ["AAJ_DUTIES_JSON"] = os.path.join(code, "aaj_duties.json")
    for f in ("aaj_kaam.py", "aaj_seed.py"):
        try:
            compile(open(os.path.join(code, f), encoding="utf-8").read(), f, "exec")
            ok = True
        except SyntaxError as e:
            ok = str(e)
        check("A1 %s compiles" % f, ok is True, ok)
    sys.path.insert(0, code)
    for m in ("aaj_kaam", "aaj_seed"):
        sys.modules.pop(m, None)
    ak = importlib.import_module("aaj_kaam")
    seed = importlib.import_module("aaj_seed")
    check("A2 the module is 2.0 and found its seed", ak.VERSION == "S493 2.0" and ak.SEED is seed and ak.SEED_ERR is None, (ak.VERSION, ak.SEED_ERR))
    M = json.load(open(os.path.join(code, "DUTY_MAP.json"), encoding="utf-8"))
    X = json.load(open(os.path.join(code, "aaj_duties.json"), encoding="utf-8"))
    known = {d["id"] for d in M["duties"]} | {d["id"] for d in X["extra"]}
    people = {p["key"]: p for p in seed.PEOPLE}
    check("A3 six lists, in his turn-on order", [p["key"] for p in seed.PEOPLE] == ["bhati", "sukhveer", "shavez", "amir", "reception", "darpan"],
          [p["key"] for p in seed.PEOPLE])
    check("A4 on as he left them: five on, Amir off", [k for k, p in people.items() if p["on"]] == ["bhati", "sukhveer", "shavez", "reception", "darpan"])
    check("A5 the counts of lines are his", [len(p["lines"]) for p in seed.PEOPLE] == [5, 1, 13, 9, 17, 9], [len(p["lines"]) for p in seed.PEOPLE])
    hi = {l["id"]: l["hi"] for p in seed.PEOPLE for l in p["lines"]}
    check("A6 his own wording is in the seed, trimmed",
          hi["reception.medicine_orders"] == "Dawa ka order kijiye apne app se" and hi["shavez.sale_report"] == "Kal ki marg sale report nikaliye"
          and hi["shavez.match_check"] == "Reception ka kal ka hisaab check kijiye"
          and hi["shavez.bill_chain_gap"] == "Bill number ki series tooti hai: likhe hue dinon ki sale report dobara nikaliye", "")
    check("A7 Shavez's lines are in the order he put them",
          [l["id"] for l in people["shavez"]["lines"]][:5] == ["shavez.sale_report", "shavez.closing_stock", "shavez.match_check", "shavez.docterz_watch",
                                                              "shavez.staff_register_approve"], [l["id"] for l in people["shavez"]["lines"]][:5])
    wh = {l["id"]: l["when"] for p in seed.PEOPLE for l in p["lines"]}
    check("A8 the groups he moved: Bhati's two and Darpan's two to 'first', Shavez's check to 'first'",
          all(wh[i] == "first" for i in ("bhati.sale_check", "bhati.physio_tick", "darpan.spot_count", "darpan.order_review", "shavez.match_check")))
    held = [l for l in people["darpan"]["lines"] if l["id"] in ("darpan.desk_shelf_counts", "darpan.desk_identity")]
    check("A9 the two Vaapsi Desk lines are held off, with the reason said", len(held) == 2 and all((not l["on"]) and "September" in l.get("why", "") for l in held))
    miss = []
    for p in seed.PEOPLE:
        for l in p["lines"]:
            for s in (seed.ENGINE.get(l["id"]) or {}).get("src") or [l["id"]]:
                if s not in known:
                    miss.append("%s -> %s" % (l["id"], s))
    check("A10 every line stands on a duty the duty files hold", not miss, miss)
    check("A11 a line's working names only doors of this site", all(str(v["door"]).startswith("/finance/") for v in seed.ENGINE.values() if "door" in v))
    check("A12 the floor's default is 01-Oct-2026", seed.FLOOR_DEFAULT == "2026-10-01")
    sqls = {d["id"]: d["due_sql"] for d in M["duties"] if d.get("person") != "manoj"}
    sqls.update({d["id"]: d["sql"] for d in X["extra"] if d.get("kind") == "sql"})
    sqls.update(seed.DUE)
    check("A14 no duty reads a table by a name the floor cannot shadow (main.<table>)", not [i for i, q in sqls.items() if re.search(r"\bmain\.", q)])
    for f in ("aaj_kaam.html", "aaj_panel.html"):
        h = open(os.path.join(code, f), encoding="utf-8").read()
        check("A13 %s closes what it opens" % f, h.count("<script>") == h.count("</script>") == 1 and h.rstrip().endswith("</html>")
              and h.count("<div") == h.count("</div>"), (h.count("<div"), h.count("</div>")))

    # ---------------------------------------------------------------------------------------- the made-up clinic
    db = os.path.join(scratch, "clinic.db")
    how = make_clinic(db, code_dirs, real_db)
    note("the made-up clinic: %s" % how)
    con = sqlite3.connect(db)
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('aaj.from', ?, 'walk')", (floor,))
    con.commit()

    # ---------------------------------------------------------------------------------------- B  every SQL runs, every view lays
    print("B  every line's SQL on the floored connection")
    allp = ak.build_all(db, with_raw=True)
    check("B1 the staff's floor is the setting aaj.from", allp["floor"] == floor, allp["floor"])
    check("B2 the owner's floor is 1.0's (01-Sep-2026)", allp["owner_floor"] == "2026-09-01", allp["owner_floor"])
    check("B3 every floor view lays", not allp["floor_bad"] and sorted(allp["staff_views"]) == sorted(seed.FLOOR), allp["floor_bad"])
    stand = {s for p in seed.PEOPLE for l in p["lines"] for s in ((seed.ENGINE.get(l["id"]) or {}).get("src") or [l["id"]])}
    stand |= {d["id"] for d in M["duties"] if d.get("person") == "manoj"}
    errs = ["%s: %s" % (i["id"], i["err"]) for i in allp["items"] if i["err"] and i["id"] in stand]
    other = ["%s: %s" % (i["id"], i["err"]) for i in allp["items"] if i["err"] and i["id"] not in stand]
    check("B4 every duty a panel line or the owner's console stands on runs (%d duties)" % len(stand), not errs, errs)
    if other:
        note("duties of the map that no panel line stands on and that could not be read here (another kit's, not yet whole): %s" % "; ".join(other))
    check("B5 every duty of both files is there", {i["id"] for i in allp["items"]} == known, known ^ {i["id"] for i in allp["items"]})
    rd = ak.Reader(db)
    bad = []
    for p in rd.people.values():
        for l in p["lines"]:
            st = ak.line_state(rd, l)
            if st["kind"] is None or st["err"]:
                bad.append("%s: %s" % (l["id"], st["err"]))
    rd.close()
    check("B6 every line of every panel is read", not bad, bad)
    con2 = sqlite3.connect(db)
    con2.execute("DELETE FROM setting WHERE key='aaj.from'")
    con2.commit()
    c0, i0 = ak.connect(db, X, "staff")
    check("B7 with no setting the floor is 01-Oct-2026", i0["floor"] == "2026-10-01", i0["floor"])
    c0.close()
    con2.execute("INSERT INTO setting (key, value, note) VALUES ('aaj.from', 'not a day', 'walk')")
    con2.commit()
    c0, i0 = ak.connect(db, X, "staff")
    check("B8 a setting that is not a day is not a floor", i0["floor"] == "2026-10-01", i0["floor"])
    c0.close()
    con2.execute("UPDATE setting SET value=? WHERE key='aaj.from'", (floor,))
    con2.commit()
    con2.close()

    # ---------------------------------------------------------------------------------------- C  the floor, table by table
    print("C  the floor")
    put(con, "clinic_register_day", business_date=D(30))
    for d in (OLD, NEW):
        put(con, "clinic_day_revenue", business_date=d)
        put(con, "clinic_money_flag", business_date=d, key="w-desk", code="w", owner=0, status="open")
        put(con, "clinic_money_flag", business_date=d, key="w-owner", code="w", owner=1, status="to_owner")
        put(con, "clinic_money_day", business_date=d, status="maker_done")
        put(con, "clinic_physio_day", business_date=d, cash_p=100)
        put(con, "day_entry", unit="medical", business_date=d, status="submitted")
        put(con, "blood_order", day=d, clinic_id="W493", state="ok")
        put(con, "xray_filing", src_id="w493-" + d, state="check", day=d, planned_at=d + " 10:00:00")
        put(con, "stock_spot_check", unit="medical", business_date=d, bill_no="W" + d, item_key="w", reason="w", requested_at=d + "T10:00:00", status="due")
        put(con, "identity_dispute", unit="medical", business_date=d, clinic_id="W493", status="open", noted_at=d)
        put(con, "mi_bill_chain", series="A", day=d, gap_before="A1..A2", gap_inside="")
        put(con, "stock_voucher_line", count_id=1, round_no=1, kind="ISSUE", batch_no=(1 if d == OLD else 2), batches_n=2, made_at=d + " 10:00:00")
        put(con, "slip_adjust", slip_id=1, kind="discount", day=d, made_by="w", made_at=d + " 10:00:00", state="pending")
        put(con, "supplier_msg", month=d[:7], vendor_norm="w" + d, vendor="W", kind="neft", ref=1, body="w", status="queued", queued_at=d + "T10:00:00")
        put(con, "purchase_order", created_at=d + "T10:00:00", created_by="w", vendor="W" + d, status="sent")
        put(con, "purchase_export", md5="m" + d, type="BILLWISE", received_at=d + "T10:00:00")
        put(con, "purchase_bill", supplier_norm="w", supplier="W", bill_no="B" + d, bill_date=d, month=d[:7], bw_md5="m" + d)
        put(con, "order_sheet_line", entry_no="e" + d, item_printed="i", item="i", supplier="S", supplier_norm="s" + d, line_date=d, kind="order",
            state="to_order", first_sheet=1, last_sheet=1, created_at=d)
        put(con, "amir_claim", supplier="W", bill_no="B", raised_at=d + "T10:00:00", state="open")
        put(con, "claim_line", count_id=1, item="i", item_key="i" + d, raised_at=d + "T10:00:00", state="open")
        put(con, "export_watch", day=d, who="amir", punched=1, verdict="red", missing="", have="", note="", checked_at=d)
        put(con, "purchase_salt_task", section="s", seq=1, a="a" + d, done=1, done_at=d + "T10:00:00")
    for d in (OLD, D(4)):                                                # the bill-entry line waits three days after the goods: its 'after' row is four days old
        put(con, "purchase_order_line", order_id=1, item="i" + d, arrived_at=d + "T10:00:00", supplied=1, billed_bill_no="")
    put(con, "petty_available", day=D(9), status="yes", by_whom="bhati", at=D(9))      # Bhati last answered before the floor
    put(con, "stock_count_plan", due_from=OLD, status="open")
    put(con, "stock_count_plan", due_from=D(40), picked_at=OLD + "T10:00:00", status="picked")
    put(con, "mi_file", type="ORDER_PENDING", verdict="REFUSED", received_at=OLD + "T10:00:00")       # no view can date this one
    put(con, "day_entry", unit="medical", business_date="2026-08-20", status="submitted")
    put(con, "stock_count_plan", due_from=NEW, status="open")
    put(con, "stock_count_plan", due_from=D(40), picked_at=NEW + "T10:00:00", status="picked")
    put(con, "xray_filing", src_id="w493-noday-old", state="check", day="", planned_at=OLD + " 10:00:00")
    put(con, "xray_filing", src_id="w493-noday-new", state="check", day="", planned_at=NEW + " 10:00:00")
    sid = {}
    for d in (OLD, NEW):
        cur = con.execute("SELECT COALESCE(MAX(id),0)+1 FROM slip").fetchone()[0]
        put(con, "slip", id=cur, series="xp", state="ok", clinic_id="W493", day=d)
        put(con, "slip_item", slip_id=cur, kind="xray")
        sid[d] = cur
    put(con, "stock_spot_roster", day=D(1), item_norm="w", item="w", asked_at=D(1))
    con.commit()
    allp = ak.build_all(db, with_raw=True)
    it = {i["id"]: i for i in allp["items"]}
    one = ("alisha.counter_sheet", "alisha.match_flags", "shavez.match_check", "bhati.physio_tick", "bhati.sale_check",
           "alisha.xray_photo", "darpan.desk_shelf_counts", "darpan.desk_identity", "shavez.bill_chain_gap", "amir.count_vouchers",
           "shavez.slip_adjust_check", "shavez.supplier_messages", "reception.order_arrival", "amir.bills_answer", "reception.medicine_orders",
           "darpan.amir_claims", "darpan.count_claims", "amir.purchase_exports", "amir.salt_list", "amir.full_count_sunday", "darpan.count_sunday_yes")
    for i in one:
        check("C1 %s counts the row after the floor and not the one before" % i, it[i]["n"] == 1 and it[i]["since"] == NEW and it[i]["n_all"] >= 2 and not it[i]["err"],
              (it[i]["n"], it[i]["since"], it[i]["n_all"], it[i]["err"]))
    check("C2 alisha.check_xray_files: a file with a day by its day, a file with none by the day it was seen", it["alisha.check_xray_files"]["n"] == 2
          and it["alisha.check_xray_files"]["n_all"] == 4, (it["alisha.check_xray_files"]["n"], it["alisha.check_xray_files"]["n_all"]))
    check("C3 the two blood lines count only the test after the floor", it["alisha.check_blood"]["n"] == 1 and it["sukhveer.blood_mail"]["n"] == 1,
          (it["alisha.check_blood"]["n"], it["sukhveer.blood_mail"]["n"]))
    check("C1 amir.arrival_bill_entry counts the row after the floor and not the one before", it["amir.arrival_bill_entry"]["n"] == 1
          and it["amir.arrival_bill_entry"]["since"] == D(4) and it["amir.arrival_bill_entry"]["n_all"] == 2, (it["amir.arrival_bill_entry"]["n"], it["amir.arrival_bill_entry"]["since"]))
    old_staff = [(i["id"], i["since"]) for i in allp["items"] if i["person"] != "manoj" and i["kind"] == "sql" and i["n"] > 0 and i["since"]
                 and re.match(r"^\d{4}-\d\d-\d\d$", i["since"]) and i["since"] < floor]
    old_staff = [x for x in old_staff if x[0] in stand]
    exp_old = ["darpan.order_sheet", "bhati.availability"] + (["shavez.month_reports"] if today.replace(day=1).isoformat() < floor else [])
    check("C1b with a row before the floor in every dated table, the only staff work still dated before it is what no view can catch",
          sorted(i for i, _s in old_staff) == sorted(exp_old), old_staff)
    rd = ak.Reader(db)
    stm = ak.line_state(rd, next(l for l in rd.people["shavez"]["lines"] if l["id"] == "shavez.month_reports"))
    rd.close()
    check("C1b2 the month's two reports are this month's job wherever the floor lies: not held", stm["due"] is True and stm["held"] is None, stm)
    rd = ak.Reader(db)
    ln = lambda pk, lid: next(l for l in rd.people[pk]["lines"] if l["id"] == lid)      # noqa: E731
    st1, st2 = ak.line_state(rd, ln("darpan", "darpan.order_sheet")), ak.line_state(rd, ln("bhati", "bhati.availability"))
    rd.close()
    check("C1c THE SECOND GUARD: an order sheet refused before the floor is HELD BACK, and the panel can say since when", st1["due"] is False and st1["held"] == OLD and not st1["err"], st1)
    check("C1d ... but 'Aaj aayenge?' is today's job however long ago he last answered: not held", st2["due"] is True and st2["held"] is None, st2)
    con.execute("UPDATE mi_file SET received_at=? WHERE type='ORDER_PENDING'", (NEW + "T10:00:00",))
    con.commit()
    rd = ak.Reader(db)
    st1 = ak.line_state(rd, next(l for l in rd.people["darpan"]["lines"] if l["id"] == "darpan.order_sheet"))
    rd.close()
    check("C1e ... and the same sheet refused after the floor is a job", st1["due"] is True and st1["held"] is None, st1)
    con.execute("DELETE FROM mi_file WHERE type='ORDER_PENDING'")
    # THE FLOOR NEVER MAKES WORK: the medicine to order (listed after the floor) already has its order drafted -- before the floor.
    # purchase_order is NOT under a view for exactly this: the draft must still be seen.
    put(con, "purchase_order", created_at=OLD + "T11:00:00", created_by="w", vendor="S", status="draft", order_src="s454", supplier_norm="s" + NEW)
    con.commit()
    capd = {i["id"]: i for i in ak.build_all(db)["items"]}["reception.medicine_orders"]
    check("C1f an order drafted BEFORE the floor still answers a medicine listed after it: nothing is due", capd["n"] == 0 and not capd["err"], (capd["n"], capd.get("capped")))
    con.execute("DELETE FROM purchase_order WHERE status='draft'")
    con.commit()
    capd = {i["id"]: i for i in ak.build_all(db)["items"]}["reception.medicine_orders"]
    check("C1g ... and without that draft the same line is due", capd["n"] == 1 and capd["capped"] is False, (capd["n"], capd.get("capped")))
    check("C1h no table that another duty asks 'is it done?' of lies under a view", not {"purchase_order", "purchase_bill"} & set(seed.FLOOR)
          and set(seed.REWRITE) == {"reception.order_arrival", "amir.bills_answer"})
    keep_map = ak.DUTY_MAP
    moved = json.loads(open(keep_map, encoding="utf-8").read())
    for du in moved["duties"]:
        if du["id"] == "reception.order_arrival":
            du["due_sql"] = du["due_sql"].replace("WHERE o.status = 'sent' AND", "WHERE o.status = 'sent'  AND")
    ak.DUTY_MAP = os.path.join(code, "DUTY_MAP_moved.json")
    json.dump(moved, open(ak.DUTY_MAP, "w", encoding="utf-8"))
    mv = {i["id"]: i for i in ak.build_all(db)["items"]}["reception.order_arrival"]
    ak.DUTY_MAP = keep_map
    check("C1i the duty map moves under a duty that carries its own floor: the duty is UNREAD, never shown unfloored", mv["n"] == 0 and "no longer fits" in str(mv["err"]), (mv["n"], mv["err"]))
    # the cap itself, on a made-up duty: floored books say 1, whole books say 0
    cap = ak._item("extra", {"id": "walk.cap", "person": "shavez", "kind": "sql", "sql": "SELECT (SELECT COUNT(*) FROM temp.sqlite_master WHERE name='day_entry') AS n, NULL"},
                   ak.connect(db, X, "staff")[0], {}, sqlite3.connect(db), {}, today, floor, None)
    check("C1j THE CAP: where the floored books show work and the whole books show none, nothing is due", cap["n"] == 0 and cap["capped"] is True, (cap["n"], cap.get("capped")))
    check("C4 Darpan's spot count is TODAY's roster: yesterday's unanswered row is not a job", it["darpan.spot_count"]["n"] == 0, it["darpan.spot_count"]["n"])
    put(con, "stock_spot_roster", day=today.isoformat(), item_norm="w2", item="w2", asked_at=today.isoformat())
    con.commit()
    check("C5 ... and today's is", {i["id"]: i for i in ak.build_all(db, with_raw=False)["items"]}["darpan.spot_count"]["n"] == 1)
    # the owner's own lines
    check("C6 the owner's approve line keeps 1.0's floor: both days counted, August not", it["manoj.approve_days"]["n"] == 2 and it["manoj.approve_days"]["n_all"] == 3,
          (it["manoj.approve_days"]["n"], it["manoj.approve_days"]["n_all"]))
    check("C6b the owner's slip line is his 1.0 line too: both slips, though Shavez's line shows one", it["manoj.slip_adjust"]["n"] == 2 and it["shavez.slip_adjust_check"]["n"] == 1,
          (it["manoj.slip_adjust"]["n"], it["shavez.slip_adjust_check"]["n"]))
    check("C7 the owner's two ruled-off lines stand on the new floor", it["manoj.clinic_flags"]["n"] == 1 and it["manoj.physio_received"]["n"] == 1,
          (it["manoj.clinic_flags"]["n"], it["manoj.physio_received"]["n"]))
    check("C8 the views handed to the console are the owner's", allp["views"].get("day_entry") == "2026-09-01" and allp["views"].get("clinic_money_flag") == floor
          and allp["views"].get("clinic_physio_day") == floor, allp["views"])
    if old_py:
        o = os.path.join(scratch, "old")
        os.makedirs(o)
        shutil.copy2(old_py, os.path.join(o, "aaj_kaam_10.py"))
        sys.path.insert(0, o)
        ak10 = importlib.import_module("aaj_kaam_10")
        a10 = {i["id"]: i for i in ak10.build_all(db, with_raw=False)["items"]}
        it = {i["id"]: i for i in ak.build_all(db)["items"]}             # both asked now, of the same rows
        same = [i for i in it if i.startswith("manoj.") and i not in ("manoj.clinic_flags", "manoj.physio_received")]
        diff = [(i, a10[i]["n"], it[i]["n"]) for i in same if i in a10 and a10[i]["n"] != it[i]["n"]]
        check("C9 every other line of the owner counts exactly what 1.0 counts (%d lines)" % len(same), not diff and len(same) >= 9, diff)
        check("C10 NEGATIVE CONTROL: 1.0 counts the rows before the floor (so C1 can fail)", a10["alisha.check_xray_files"]["n"] == 4 and a10["shavez.match_check"]["n"] == 2
              and a10["alisha.xray_photo"]["n"] == 2, (a10["alisha.check_xray_files"]["n"], a10["shavez.match_check"]["n"], a10["alisha.xray_photo"]["n"]))
        more = [(i, a10[i]["n"], it[i]["n"]) for i in it if i in a10 and not i.startswith("manoj.") and i != "darpan.spot_count" and it[i]["n"] > a10[i]["n"]]
        check("C11 no staff line counts MORE than 1.0 did", not more, more)
    else:
        note("C9-C11 not run: no --old (1.0's aaj_kaam.py)")

    # ---------------------------------------------------------------------------------------- D  who sees what
    print("D  who sees what")
    svc = Svc(ak, db)
    st, j = svc.me(None).get("/finance/aaj/api/list")
    check("D1 not signed in: 401", st == 401 and j.get("error") == "not_signed_in", (st, j))
    for u in ("bhati", "alisha", "shavez", "amir"):
        j = svc.lst(u)
        check("D2 lists not started: %s sees nothing" % u, j == {"ok": False, "error": "off"}, j)
    st, j = svc.me("bhati").get("/finance/aaj/api/line")
    check("D3 lists not started: no tile", j.get("show") is False, j)
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", {"id": "bhati.petty_today"})
    check("D4 lists not started: no tap", st == 403, (st, j))
    st, j = svc.me("bhati").get("/finance/aaj/api/switch?panel=1")
    check("D5 the panel is the owner's: a staff login is refused", st == 403 and "panel" not in j, (st, j))
    st, j = svc.me("bhati").post("/finance/aaj/api/switch", {"on": True})
    check("D6 ... and cannot start the lists", st == 403 and not ak.staff_switch(sqlite3.connect(db))[0], (st, j))
    pn = svc.panel()
    check("D7 the owner's panel: six people, the floor, not started", pn.get("ok") and pn["on"] is False and len(pn["panel"]["people"]) == 6
          and pn["panel"]["floor"] == floor and not pn["panel"]["floor_bad"] and not pn["panel"]["defs_err"], (pn.get("on"), pn["panel"].get("floor_bad")))
    j = svc.me("manoj", True).get("/finance/aaj/api/list?as=bhati")[1]
    check("D8 before the start the owner sees a list as it will be, taps off", j.get("ok") and j["view_as"] and j["on"] is False and rows_of(j)
          and not any(r["can_tick"] for r in rows_of(j)), (j.get("ok"), len(rows_of(j))))
    st, j = svc.me("bhati").get("/finance/aaj/api/list?as=shavez")
    check("D9 a staff login cannot look at another's list", st == 403 and j.get("error") == "owner_only", (st, j))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {})
    check("D10 an empty post starts nothing", st == 400 and not ak.staff_switch(sqlite3.connect(db))[0], (st, j))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", "on=1", raw=True)
    check("D11 a form post starts nothing", st == 400 and not ak.staff_switch(sqlite3.connect(db))[0], (st, j))
    # a first_on ten days ago, so that this week's lines have begun (G proves the other side)
    svc.con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('aaj.staff_first_on', ?, 'walk')", (D(10) + "T09:00:00",))
    svc.con.commit()
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"on": True})
    check("D12 the owner starts the lists", st == 200 and j["on"] is True and j["by"] == "manoj", (st, j))
    b = svc.lst("bhati")
    check("D13 started: Bhati has his list", b.get("ok") and b["on"] and b["person_on"] and b["has"] and b["name"] == "Bhati", b)
    check("D14 Amir's switch is off: he still sees nothing", svc.lst("amir") == {"ok": False, "error": "off"}, svc.lst("amir"))
    check("D15 a login with no list sees nothing", svc.lst("awdhesh") == {"ok": False, "error": "off"}, svc.lst("awdhesh"))
    a, s, r = svc.lst("alisha"), svc.lst("shivani"), svc.lst("reception")
    check("D16 the desk's three logins work one list", a.get("ok") and a["name"] == "Reception" and ids_of(a) == ids_of(s) == ids_of(r) and ids_of(a), (ids_of(a), ids_of(s)))
    st, j = svc.me("manoj", True).get("/finance/aaj/api/list")
    check("D17 the owner's own address is his panel, not a list", j == {"ok": False, "error": "owner_panel"}, j)
    st, j = svc.me("manoj", True).post("/finance/aaj/api/tick", {"id": "bhati.petty_today"})
    check("D18 the owner cannot tap for anyone", st == 403, (st, j))
    pg = svc.me("manoj", True).c.get("/finance/aaj").get_data(as_text=True)
    ps = svc.me("bhati").c.get("/finance/aaj").get_data(as_text=True)
    po = svc.me("manoj", True).c.get("/finance/aaj?as=bhati").get_data(as_text=True)
    check("D19 /finance/aaj: the owner gets the panel, a staff login the list, the owner's ?as= the list", "Staff daily lists" in pg and "<title>Aaj ka kaam</title>" in ps
          and "<title>Aaj ka kaam</title>" in po)
    p = save(svc, "bhati", lambda d: d.update(on=False))
    check("D20 a person's own switch: off, and only that person is off", svc.lst("bhati") == {"ok": False, "error": "off"} and svc.lst("shavez").get("ok"))
    p = save(svc, "bhati", lambda d: d.update(on=True))
    check("D21 ... and on again", svc.lst("bhati").get("ok") and p["on"])
    save(svc, "amir", lambda d: d.update(on=True))
    am = svc.lst("amir")
    check("D22 Amir switched on by the owner: his list is there, and his two off lines are not on it", am.get("ok")
          and not {"amir.own_correction", "amir.scan_files"} & set(ids_of(am)), ids_of(am))
    save(svc, "amir", lambda d: d.update(on=False))

    # ---------------------------------------------------------------------------------------- E  one line, one job
    print("E  one line = one job")
    b = svc.lst("bhati")
    want = [l for l in people["bhati"]["lines"]]
    check("E1 Bhati: the due lines, in his order", ids_of(b) == ["bhati.availability", "bhati.sale_check", "bhati.physio_tick", "bhati.petty_today", "bhati.petty_cash_match"], ids_of(b))
    check("E2 each line reads exactly as he wrote it", all(row(b, l["id"])["text"] == l["hi"] for l in want), [(r["id"], r["text"]) for r in rows_of(b)])
    keys = set().union(*[set(r) for r in rows_of(b)])
    check("E3 a row carries no count, no day, no 'late'", not keys & {"n", "late", "days", "since", "n_all", "behind"}, sorted(keys))
    check("E4 his groups: three lines under 'Sabse pehle', two under 'Aaj'", [(s["title"], len(s["rows"])) for s in b["sections"]] == [("Sabse pehle", 3), ("Aaj", 2)],
          [(s["title"], len(s["rows"])) for s in b["sections"]])
    con.execute("DELETE FROM clinic_physio_day WHERE business_date=?", (NEW,))
    con.commit()
    check("E5 work done: the line is gone by itself", "bhati.physio_tick" not in ids_of(svc.lst("bhati")), ids_of(svc.lst("bhati")))
    sh = svc.lst("shavez")
    check("E6 Shavez's check opens the matched day itself", row(sh, "shavez.match_check") and row(sh, "shavez.match_check")["door"] == "/finance/clinic/match/" + NEW,
          row(sh, "shavez.match_check"))
    a = svc.lst("alisha")
    check("E7 the counter sheet opens the unfilled day itself", row(a, "alisha.counter_sheet") and row(a, "alisha.counter_sheet")["door"] == "/finance/clinic/register/" + NEW,
          row(a, "alisha.counter_sheet"))
    check("E8 Morning match: two duties, ONE line, opening the day", ids_of(a).count("rec.match") == 1 and row(a, "rec.match")["door"] == "/finance/clinic/match/" + NEW
          and "alisha.match_first_pass" not in ids_of(a) and "alisha.match_flags" not in ids_of(a), row(a, "rec.match"))
    put(con, "clinic_day_revenue", business_date=D(2))               # a later day whose first pass is not made
    con.execute("UPDATE clinic_money_flag SET status='explained' WHERE owner=0")
    con.commit()
    a = svc.lst("alisha")
    check("E9 ... the flags answered, the line stays for the first pass still to make, and opens THAT day", "rec.match" in ids_of(a)
          and row(a, "rec.match")["door"] == "/finance/clinic/match/" + D(2), row(a, "rec.match"))
    put(con, "clinic_money_day", business_date=D(2), status="closed")
    con.commit()
    check("E10 ... both done, the line goes", "rec.match" not in ids_of(svc.lst("alisha")), ids_of(svc.lst("alisha")))
    # the Docterz pair: yesterday (or Saturday, on a Monday)
    yd = con.execute("SELECT CASE strftime('%w', date('now','localtime','-1 day')) WHEN '0' THEN date('now','localtime','-2 day') "
                     "ELSE date('now','localtime','-1 day') END").fetchone()[0]
    put(con, "docterz_export", drive_id="w-old", kind="consultation", business_date=D(20), status="current")
    con.commit()
    a, sh = svc.lst("alisha"), svc.lst("shavez")
    check("E11 the two Docterz reports: ONE line for the desk, with what to do and nothing to open", ids_of(a).count("rec.docterz_morning") == 1
          and row(a, "rec.docterz_morning")["door"] is None and "Docterz" in row(a, "rec.docterz_morning")["how"], row(a, "rec.docterz_morning"))
    check("E12 ... and Shavez's reminder of it, as he switched it on", "shavez.docterz_watch" in ids_of(sh), ids_of(sh))
    put(con, "docterz_export", drive_id="w-c", kind="consultation", business_date=yd, status="current")
    con.commit()
    check("E13 one report in: the line stays for the other", "rec.docterz_morning" in ids_of(svc.lst("alisha")))
    put(con, "docterz_export", drive_id="w-f", kind="followup", business_date=yd, status="current")
    con.commit()
    check("E14 both in: the line goes, for the desk and for Shavez", "rec.docterz_morning" not in ids_of(svc.lst("alisha")) and "shavez.docterz_watch" not in ids_of(svc.lst("shavez")))
    a = svc.lst("alisha")
    f = row(a, "reception.staff_register")
    check("E15 the staff register line asks the register's own door and carries no count in its words", f and f["kind"] == "fetch" and f["fetch"]["url"] == "/portal/review-counts"
          and f["fetch"]["field"] == "to_enter" and "{n}" not in f["text"] and f["door"] == "/register/review", f)
    hour, wd = con.execute("SELECT CAST(strftime('%H','now','localtime') AS INTEGER), strftime('%w','now','localtime')").fetchone()
    night = (hour >= 19 and wd != "0")
    check("E16 the two 'before leaving' lines are there after 7 pm only (now: %02d h)" % hour,
          ("reception.night_exports" in ids_of(a)) == night and ("reception.night_counter_sheet" in ids_of(a)) == night, ids_of(a))
    p = save(svc, "bhati", lambda d: [l.update(on=False) for l in d["lines"] if l["id"] == "bhati.availability"])
    check("E17 a line's own switch: off, and only that line is off", "bhati.availability" not in ids_of(svc.lst("bhati")) and "bhati.sale_check" in ids_of(svc.lst("bhati")))
    save(svc, "bhati", lambda d: [l.update(on=True) for l in d["lines"] if l["id"] == "bhati.availability"])
    check("E18 ... and on again", "bhati.availability" in ids_of(svc.lst("bhati")))
    save(svc, "bhati", lambda d: [l.update(hi="  Aaj aa rahe hain?\x07  Haan / nahin \n bataiye ") for l in d["lines"] if l["id"] == "bhati.availability"])
    check("E19 he changes the wording: the staff read the new words, cleaned", row(svc.lst("bhati"), "bhati.availability")["text"] == "Aaj aa rahe hain? Haan / nahin bataiye",
          row(svc.lst("bhati"), "bhati.availability"))
    save(svc, "bhati", lambda d: d["lines"].insert(0, d["lines"].pop(1)))
    check("E20 he moves a line up: the list follows", ids_of(svc.lst("bhati"))[:2] == ["bhati.sale_check", "bhati.availability"], ids_of(svc.lst("bhati")))
    save(svc, "bhati", lambda d: [l.update(when="night") for l in d["lines"] if l["id"] == "bhati.sale_check"])
    check("E21 he changes a line's group: it moves there", sec_of(svc.lst("bhati"), "bhati.sale_check") == "night")
    save(svc, "bhati", lambda d: d["removed"].append(d["lines"].pop(next(i for i, l in enumerate(d["lines"]) if l["id"] == "bhati.sale_check"))))
    pb = next(x for x in svc.panel()["panel"]["people"] if x["key"] == "bhati")
    check("E22 he removes a line: off the list, kept under 'Removed'", "bhati.sale_check" not in ids_of(svc.lst("bhati")) and [l["id"] for l in pb["removed"]] == ["bhati.sale_check"]
          and len(pb["lines"]) == 4, [l["id"] for l in pb["removed"]])
    save(svc, "bhati", lambda d: d["lines"].append(d["removed"].pop()))
    check("E23 ... and puts it back", len(next(x for x in svc.panel()["panel"]["people"] if x["key"] == "bhati")["lines"]) == 5)

    # ---------------------------------------------------------------------------------------- F  what a save may hold
    print("F  what a save may hold")

    def evil(d):
        d["lines"][0].update(src=["manoj.approve_days"], door="https://example.org/x", sql="SELECT 1", kind="job")
        d["lines"].append({"id": "evil.line", "hi": "x", "en": "", "when": "day", "on": True})
        d["lines"].append({"id": "manoj.approve_days", "hi": "x", "en": "", "when": "day", "on": True})
        d["lines"].append({"id": "own.A B", "hi": "x", "en": "", "when": "day", "on": True})
        d["lines"].append({"id": "own.w1", "hi": "Dukaan ka shutter check kijiye", "en": "Shutter checked", "when": "whenever", "on": True})
        d["lines"].append({"id": "own.w1", "hi": "twice", "en": "", "when": "day", "on": True})
        d["key"] = "shavez"
    p = save(svc, "sukhveer", evil)
    stored = json.loads(svc.con.execute("SELECT doc FROM aaj_cfg WHERE person='sukhveer'").fetchone()[0])
    check("F1 what is stored holds a line's id, words, group and switch -- nothing else", all(set(l) == {"id", "hi", "en", "when", "on"} for l in stored["lines"])
          and set(stored) == {"on", "note", "first_on", "lines", "removed"}, stored)
    check("F2 a made-up line, another person's duty, a bad id, a second copy: all dropped", [l["id"] for l in p["lines"]] == ["sukhveer.blood_mail", "own.w1"], [l["id"] for l in p["lines"]])
    check("F3 the line he added is a tap line, in a real group", p["lines"][1]["kind"] == "tick" and p["lines"][1]["own"] and p["lines"][1]["when"] == "day", p["lines"][1])
    su = svc.lst("sukhveer")
    check("F4 Sukhveer's own line still opens its own page", row(su, "sukhveer.blood_mail") and row(su, "sukhveer.blood_mail")["door"] == "/finance/slips/pending", row(su, "sukhveer.blood_mail"))
    check("F5 the line he added shows to Sukhveer with a 'Ho gaya' tap", row(su, "own.w1") and row(su, "own.w1")["kind"] == "tick" and row(su, "own.w1")["can_tick"]
          and row(su, "own.w1")["text"] == "Dukaan ka shutter check kijiye", row(su, "own.w1"))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "person", "key": "nobody", "doc": {"on": True, "lines": []}})
    check("F6 a save for a person who is not on the panel is refused", st == 400, (st, j))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "format_disk"})
    check("F7 an unknown instruction is refused", st == 400, (st, j))
    long = "k" * 900
    p = save(svc, "sukhveer", lambda d: d["lines"][1].update(hi=long))
    check("F8 a very long line is cut to 300 letters", len(p["lines"][1]["hi"]) == 300)
    save(svc, "sukhveer", lambda d: d["lines"][1].update(hi="Dukaan ka shutter check kijiye"))
    n_cfg = svc.con.execute("SELECT COUNT(*) FROM aaj_cfg").fetchone()[0]
    check("F9 one stored document per person he has touched", n_cfg == 3, n_cfg)
    sv = save(svc, "shavez", lambda d: None)
    check("F10 a save with nothing changed changes nothing: Shavez's 13 lines, his order, his switches", [l["id"] for l in sv["lines"]] == [l["id"] for l in people["shavez"]["lines"]]
          and all(l["on"] for l in sv["lines"]) and sv["on"], [l["id"] for l in sv["lines"]])
    svc.con.execute("UPDATE aaj_cfg SET doc=? WHERE person='shavez'", (json.dumps({"on": True, "note": "", "lines": [{"id": "shavez.sale_report", "hi": "A", "en": "", "when": "first", "on": True}], "removed": []}),))
    svc.con.commit()
    sv = next(x for x in svc.panel()["panel"]["people"] if x["key"] == "shavez")
    check("F11 a line a later kit adds is shown to him switched OFF and marked new -- never put on a list unasked", len(sv["lines"]) == 13 and sv["lines"][0]["hi"] == "A"
          and all((not l["on"]) and l["new"] for l in sv["lines"][1:]), [(l["id"], l["on"], l["new"]) for l in sv["lines"][:3]])
    svc.con.execute("DELETE FROM aaj_cfg WHERE person='shavez'")
    svc.con.commit()

    # ---------------------------------------------------------------------------------------- G  taps
    print("G  taps")
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", {"id": "bhati.petty_today"})
    check("G1 Bhati taps his line", st == 200 and j["ok"] and j["by"] == "bhati" and j["yours"], (st, j))
    r = row(svc.lst("bhati"), "bhati.petty_today")
    check("G2 the line says who and when, and cannot be tapped again", r["done"] and r["done"]["by_name"] == "Bhati" and not r["can_tick"], r)
    at1 = r["done"]["at"]
    svc.con.execute("UPDATE duty_tick SET at='2000-01-01 00:00:00' WHERE duty_id='bhati.petty_today'")
    svc.con.commit()
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", {"id": "bhati.petty_today"})
    check("G3 a second tap changes nothing: the first stands", st == 200 and j["at"] == "2000-01-01 00:00:00" and at1 != j["at"], (st, j))
    st, j = svc.me("shavez").post("/finance/aaj/api/tick", {"id": "bhati.petty_cash_match"})
    check("G4 a line is tapped by its own person only", st == 404 and row(svc.lst("bhati"), "bhati.petty_cash_match")["done"] is None, (st, j))
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", {"id": "bhati.sale_check"})
    check("G5 a line the books decide cannot be tapped away", st == 404, (st, j))
    wk = "reception.week_float"
    ps_w, ps_m = today - dt.timedelta(days=today.weekday()), today.replace(day=1)
    save(svc, "reception", lambda d: d["lines"][0].update(en="Yesterday's Docterz reports are missing."))
    stored = json.loads(svc.con.execute("SELECT doc FROM aaj_cfg WHERE person='reception'").fetchone()[0])
    a = svc.lst("alisha")
    check("G6 the lists first started ten days ago: this week's lines have begun -- and an edit of the panel does not start them over",
          row(a, wk) and row(a, wk)["can_tick"] and stored["first_on"] is None, (row(a, wk), stored["first_on"]))
    exp_m = ps_m >= today - dt.timedelta(days=10)
    check("G7 ... and this month's only if the month began since (%s)" % ("it did" if exp_m else "it did not"), (row(a, "reception.month_new_register") is not None) == exp_m)
    st, j = svc.me("alisha").post("/finance/aaj/api/tick", {"id": wk})
    st2, j2 = svc.me("shivani").post("/finance/aaj/api/tick", {"id": wk})
    r = row(svc.lst("shivani"), wk)
    check("G8 the desk's shared line: Alisha tapped; Shivani's tap does not take it over, and she sees it done by Alisha", st == 200 and j2.get("by") == "alisha"
          and j2.get("yours") is False and r["done"]["by"] == "alisha" and not r["can_tick"], (st, j2, r))
    svc.con.execute("UPDATE setting SET value=? WHERE key='aaj.staff_first_on'", (today.isoformat() + "T09:00:00",))
    svc.con.commit()
    a = svc.lst("alisha")
    exp_w = ps_w >= today
    check("G9 lists first started TODAY: a weekly line begins only with a week that starts today or later (%s)" % ("today is Monday" if exp_w else "so not this week"),
          (row(a, "reception.week_film_stock") is not None) == exp_w, ids_of(a))
    v = svc.me("manoj", True).get("/finance/aaj/api/list?as=alisha")[1]
    check("G10 ... the owner's view shows it, marked as beginning later, with no tap", row(v, "reception.week_film_stock") is not None
          and (row(v, "reception.week_film_stock")["later"] == (not exp_w)) and not row(v, "reception.week_film_stock")["can_tick"], row(v, "reception.week_film_stock"))
    st, j = svc.me("alisha").post("/finance/aaj/api/tick", {"id": "reception.week_film_stock"})
    check("G11 ... and a line that has not begun cannot be tapped", (st == 200) == exp_w, (st, j))
    svc.con.execute("UPDATE setting SET value=? WHERE key='aaj.staff_first_on'", (D(10) + "T09:00:00",))
    svc.con.commit()
    save(svc, "sukhveer", lambda d: d.update(on=False))
    save(svc, "sukhveer", lambda d: d.update(on=True))
    stored = json.loads(svc.con.execute("SELECT doc FROM aaj_cfg WHERE person='sukhveer'").fetchone()[0])
    check("G12 a person on from the start, switched off and on: the lists' own first day stays theirs", stored["first_on"] == D(10), stored["first_on"])
    save(svc, "amir", lambda d: d.update(on=True))
    stored = json.loads(svc.con.execute("SELECT doc FROM aaj_cfg WHERE person='amir'").fetchone()[0])
    save(svc, "amir", lambda d: d.update(on=False))
    save(svc, "amir", lambda d: d.update(on=True))
    stored2 = json.loads(svc.con.execute("SELECT doc FROM aaj_cfg WHERE person='amir'").fetchone()[0])
    save(svc, "amir", lambda d: d.update(on=False))
    check("G12b a person he switches on later begins that day, and off-and-on again does not move it", stored["first_on"] == today.isoformat() == stored2["first_on"],
          (stored["first_on"], stored2["first_on"]))
    save(svc, "bhati", lambda d: [l.update(when="week") for l in d["lines"] if l["id"] == "bhati.petty_cash_match"])
    stb, jb = svc.me("bhati").post("/finance/aaj/api/tick", {"id": "bhati.petty_cash_match"})
    keyb = svc.con.execute("SELECT period_key FROM duty_tick WHERE duty_id='bhati.petty_cash_match'").fetchone()
    check("G12c he moves a tap line to 'once a week': its tap now stands for the week", stb == 200 and keyb and keyb[0].startswith("W"), (stb, jb, keyb))
    cit = {i["id"]: i for i in ak.build_all(db)["items"]}["bhati.petty_cash_match"]
    check("G12c2 ... and the console reads the same line by the same rhythm: tapped, for the week", cit["period"] == "week" and cit["done"] and cit["done"]["by"] == "bhati", (cit["period"], cit["done"]))
    svc.con.execute("DELETE FROM duty_tick WHERE duty_id='bhati.petty_cash_match'")
    svc.con.commit()
    save(svc, "bhati", lambda d: [l.update(when="day") for l in d["lines"] if l["id"] == "bhati.petty_cash_match"])
    pb = next(x for x in svc.panel()["panel"]["people"] if x["key"] == "bhati")
    st_a, j_a = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "person", "key": "bhati", "base": pb["edited_at"], "doc": dict(doc_of(pb), note="first screen")})
    st_b, j_b = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "person", "key": "bhati", "base": pb["edited_at"], "doc": dict(doc_of(pb), note="second screen", on=False)})
    pb2 = next(x for x in svc.panel()["panel"]["people"] if x["key"] == "bhati")
    check("G12d two screens: the second, saving over what it never saw, is refused -- nothing of it is kept", st_a == 200 and st_b == 409 and j_b["error"] == "stale"
          and pb2["note"] == "first screen" and pb2["on"] is True, (st_a, st_b, pb2["note"], pb2["on"]))
    st, j = svc.me("sukhveer").post("/finance/aaj/api/tick", {"id": "own.w1"})
    check("G13 the line the owner added is tapped by its person", st == 200 and row(svc.lst("sukhveer"), "own.w1")["done"]["by"] == "sukhveer", (st, j))
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", "id=bhati.petty_cash_match", raw=True)
    check("G14 a form post is not a tap", st == 400 and row(svc.lst("bhati"), "bhati.petty_cash_match")["done"] is None, (st, j))

    # ---------------------------------------------------------------------------------------- H  a list that is not whole
    print("H  a list that is not whole says so")
    j = svc.me("sukhveer").get("/finance/aaj/api/line")[1]
    check("H1 the tile: words only -- no number for the home page to draw", j["ok"] and j["show"] and j["open"] == 0 and j["late"] == 0 and j["fetch"] == []
          and j["text_hi"] in ("Kaam baaki hai — kholiye", "Sab ho gaya ✓", "Aaj ki list dekhiye"), j)
    con.execute("DELETE FROM blood_order")
    con.commit()
    j = svc.me("sukhveer").get("/finance/aaj/api/line")[1]
    su = svc.lst("sukhveer")
    check("H2 nothing left for Sukhveer: 'Sab ho gaya'", j["text_hi"] == "Sab ho gaya ✓" and su["open"] == 0 and not su["partial"], (j, su["open"]))
    broken = os.path.join(scratch, "broken.db")
    shutil.copy2(db, broken)
    bc = sqlite3.connect(broken)
    bc.execute("ALTER TABLE blood_order RENAME TO blood_order_gone")
    bc.commit()
    bc.close()
    s2 = Svc(ak, broken)
    su = s2.lst("sukhveer")
    j = s2.me("sukhveer").get("/finance/aaj/api/line")[1]
    check("H3 his line cannot be read: the list says it is not whole, and never 'Sab ho gaya'", su["partial"] and j["partial"] and j["text_hi"] == "List adhoori hai — kholiye", (su["partial"], j))
    pn = s2.panel()["panel"]
    bl = next(l for x in pn["people"] if x["key"] == "sukhveer" for l in x["lines"] if l["id"] == "sukhveer.blood_mail")
    check("H4 ... and his panel says which line and why", bl["err"] and "blood_order" in str(pn["floor_bad"]), (bl["err"], pn["floor_bad"]))
    s2.close()
    shutil.copy2(db, broken)
    bc = sqlite3.connect(broken)
    if sqlite3.sqlite_version_info >= (3, 25, 0):
        bc.execute("ALTER TABLE xray_filing RENAME COLUMN planned_at TO planned_when")
        bc.commit()
        bc.close()
        s2 = Svc(ak, broken)
        a = s2.lst("alisha")
        pn = s2.panel()["panel"]
        check("H5 a floor that cannot be laid: the line is HELD BACK, not shown unfloored", "xray_filing" in pn["floor_bad"] and "alisha.check_xray_files" not in ids_of(a) and a["partial"],
              (pn["floor_bad"], ids_of(a)))
        s2.close()
    else:
        bc.close()
        note("H5 not run: this SQLite (%s) cannot rename a column" % sqlite3.sqlite_version)
    shutil.copy2(db, broken)
    bc = sqlite3.connect(broken)
    bc.execute("UPDATE aaj_cfg SET doc='{not a document' WHERE person='bhati'")
    bc.commit()
    bc.close()
    s2 = Svc(ak, broken)
    pn = s2.panel()["panel"]
    check("H5b Bhati's saved panel is damaged: HIS list is off, said on the panel; the others stand", s2.lst("bhati") == {"ok": False, "error": "off"}
          and pn["cfg_bad"] == ["bhati"] and s2.lst("alisha").get("ok"), (pn["cfg_bad"], s2.lst("bhati")))
    fixed = save(s2, "bhati", lambda d: d.update(on=True))
    check("H5b2 ... and his next save of that panel repairs it", fixed["on"] and not s2.panel()["panel"]["cfg_bad"] and s2.lst("bhati").get("ok"), s2.panel()["panel"]["cfg_bad"])
    s2.close()
    shutil.copy2(db, broken)
    bc = sqlite3.connect(broken)
    bc.execute("ALTER TABLE aaj_cfg RENAME TO aaj_cfg_was")
    bc.execute("CREATE TABLE aaj_cfg (person TEXT)")                      # there, and unreadable
    bc.commit()
    bc.close()
    s2 = Svc(ak, broken)
    pn = s2.panel()["panel"]
    check("H5c the saved panels cannot be read at all: EVERY list is off (the seed is the start, never the fallback), and the panel says why",
          all(s2.lst(u) == {"ok": False, "error": "off"} for u in ("bhati", "alisha", "shavez", "sukhveer", "darpan")) and pn["cfg_err"]
          and not any(x["on"] for x in pn["people"]), (pn["cfg_err"], [x["on"] for x in pn["people"]]))
    s2.close()
    shutil.copy2(db, broken)
    bc = sqlite3.connect(broken)
    bc.execute("ALTER TABLE setting RENAME TO setting_was")
    bc.commit()
    bc.close()
    try:
        c0, i0 = ak.connect(broken, X, "staff")
        c0.close()
        ok = False
    except sqlite3.Error:
        ok = True
    check("H5d a floor that cannot be READ is not guessed: no list is cut", ok)
    ak.DUTY_MAP = os.path.join(code, "no_such_map.json")
    su, a = svc.lst("sukhveer"), svc.lst("alisha")
    check("H6 the duty map cannot be read: every list says it is not whole", su.get("partial") and a.get("partial"), (su, a.get("partial")))
    ak.DUTY_MAP = os.path.join(code, "DUTY_MAP.json")

    # ---------------------------------------------------------------------------------------- I  tasks
    print("I  tasks")
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch?panel=1", {"op": "task_add", "to": ["bhati", "reception"], "items": ["  Waiting room ka AC service karwaiye ", "", "Generator ka diesel check kijiye"], "due": D(-2)})
    check("I1 the owner gives two tasks to two lists: four tasks", st == 200 and j.get("made") == 4 and len(j["panel"]["tasks"]) == 4, (st, j.get("made")))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task_add", "to": ["amir"], "items": ["x"]})
    check("I2 a task to a person whose list is off is refused (nobody would see it)", st == 400 and j["error"] == "no_person", (st, j))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task_add", "to": ["bhati"], "items": ["   ", ""]})
    check("I3 an empty task is refused", st == 400 and j["error"] == "say_something", (st, j))
    b, sh, a = svc.lst("bhati"), svc.lst("shavez"), svc.lst("alisha")
    check("I4 Bhati sees his two, from Dr Manoj, with the day asked", len(b["tasks"]) == 2 and {t["text"] for t in b["tasks"]} == {"Waiting room ka AC service karwaiye", "Generator ka diesel check kijiye"}
          and all(t["by_name"] == "Dr Manoj" and t["due"] == D(-2) and t["can_answer"] and not t["can_close"] for t in b["tasks"]), b["tasks"])
    check("I5 Shavez sees none; the desk sees its two", sh["tasks"] == [] and len(a["tasks"]) == 2, (len(sh["tasks"]), len(a["tasks"])))
    check("I6 an open task counts as work: the tile does not say 'Sab ho gaya'", svc.me("bhati").get("/finance/aaj/api/line")[1]["text_hi"] == "Kaam baaki hai — kholiye")
    tb = b["tasks"][0]["id"]
    ta = a["tasks"][0]["id"]
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", {"task": tb, "act": "done"})
    t = next(t for t in svc.lst("bhati")["tasks"] if t["id"] == tb)
    check("I7 Bhati says done: it shows as done, waiting for the owner", st == 200 and t["state"] == "done" and t["notes"][-1]["kind"] == "done", (st, t))
    st, j = svc.me("alisha").post("/finance/aaj/api/tick", {"task": ta, "act": "cant"})
    check("I8 'could not' needs a reason", st == 400 and j["error"] == "say_something", (st, j))
    st, j = svc.me("alisha").post("/finance/aaj/api/tick", {"task": ta, "act": "cant", "note": "Mistri kal aayega"})
    t = next(t for t in svc.lst("shivani")["tasks"] if t["id"] == ta)
    check("I9 Alisha says why; Shivani, on the same list, sees Alisha's answer", st == 200 and t["state"] == "cant" and t["notes"][-1]["by_name"] == "Alisha" and t["notes"][-1]["note"] == "Mistri kal aayega", t)
    st, j = svc.me("shavez").post("/finance/aaj/api/tick", {"task": tb, "act": "done"})
    check("I10 a task is answered by its own person only", st == 404, (st, j))
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", {"task": tb, "act": "close"})
    check("I11 a person cannot close a task given to them", st == 404 and next(t for t in svc.lst("bhati")["tasks"] if t["id"] == tb)["state"] == "done", (st, j))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch?panel=1", {"op": "task", "id": ta, "act": "reopen", "note": "Aaj hi bulaiye"})
    t = next(t for t in svc.lst("alisha")["tasks"] if t["id"] == ta)
    check("I12 the owner sends it back with a word: open again, his word on it", st == 200 and t["state"] == "open" and t["notes"][-1]["note"] == "Aaj hi bulaiye" and t["notes"][-1]["by_name"] == "Dr Manoj", t)
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch?panel=1", {"op": "task", "id": tb, "act": "close"})
    check("I13 the owner closes Bhati's: it leaves Bhati's page and stays on the panel as closed", st == 200 and tb not in [t["id"] for t in svc.lst("bhati")["tasks"]]
          and next(t for t in j["panel"]["tasks"] if t["id"] == tb)["state"] == "closed")
    st, j = svc.me("bhati").post("/finance/aaj/api/tick", {"task": tb, "act": "note", "note": "x"})
    check("I14 a closed task takes no more answers", st == 400 and j["error"] == "closed", (st, j))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task", "id": 999999, "act": "close"})
    check("I15 a task that does not exist: said so", st == 404, (st, j))
    odd = [svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task", "id": v, "act": "close"})[0] for v in (True, 1.9, "1", 10 ** 30, -1, None, [1])]
    odd += [svc.me("bhati").post("/finance/aaj/api/tick", {"task": v, "act": "done"})[0] for v in (True, 1.9, "1", 10 ** 30, 1e400)]
    check("I15b a number that is not a task's number is refused, never an error and never task 1", odd == [404] * len(odd), odd)
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task", "id": tb, "act": "close"})
    st2, j2 = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task", "id": tb, "act": "reply", "note": "x"})
    st3, j3 = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task", "id": tb, "act": "reopen"})
    check("I15c a closed task takes one thing only -- being sent back, with a word", (st, st2, st3) == (400, 400, 400) and j["error"] == "closed" and j3["error"] == "say_something", (st, st2, st3))
    svc.con.execute("UPDATE aaj_task SET state='done', state_at=? WHERE id=?", (D(5) + " 10:00:00", ta + 0))
    svc.con.commit()
    gone = ta not in [t["id"] for t in svc.lst("alisha")["tasks"]]
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "task", "id": ta, "act": "reply", "note": "Shabash"})
    back = [t for t in svc.lst("alisha")["tasks"] if t["id"] == ta]
    check("I15d an answered task leaves the person's page after two days; his reply brings it back with his word", gone and st == 200 and back and back[0]["notes"][-1]["note"] == "Shabash", (gone, st))
    st, j = svc.me("shavez").post("/finance/aaj/api/tick", {"give": {"to": ["bhati"], "text": "Petty book lekar aaiye"}})
    check("I16 a login the owner has not named cannot give a task", st == 403, (st, j))
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch?panel=1", {"op": "assigners", "logins": ["Shavez", "bhawna", "drop table", "shavez"]})
    check("I17 the owner names who may give: two logins kept, the bad one dropped", st == 200 and j["panel"]["assigners"] == ["shavez", "bhawna"], j["panel"].get("assigners"))
    sh = svc.lst("shavez")
    check("I18 Shavez now has the giving box and the people to give to", sh["can_give"] and [p["key"] for p in sh["people"]] == ["bhati", "sukhveer", "shavez", "amir", "reception", "darpan"]
          and not svc.lst("bhati")["can_give"], sh.get("people"))
    st, j = svc.me("shavez").post("/finance/aaj/api/tick", {"give": {"to": ["bhati", "amir"], "text": "Petty book lekar aaiye"}})
    gv = svc.lst("shavez")["given"]
    check("I19 Shavez gives one to Bhati (Amir's list is off: skipped)", st == 200 and j["made"] == 1 and len(gv) == 1 and gv[0]["person"] == "bhati" and gv[0]["can_close"], (st, j, gv))
    bw = svc.lst("bhawna")
    check("I20 a giver with no list of her own gets the giving page, and no list", bw.get("ok") and bw["can_give"] and not bw["has"] and bw["sections"] == [] and bw["tasks"] == [], bw.get("ok"))
    st, j = svc.me("bhawna").post("/finance/aaj/api/tick", {"give": {"to": ["reception"], "text": "Dressing trolley bhariye"}})
    tg = svc.lst("bhawna")["given"][0]["id"]
    st2, j2 = svc.me("bhawna").post("/finance/aaj/api/tick", {"task": gv[0]["id"], "act": "close"})
    st3, j3 = svc.me("bhawna").post("/finance/aaj/api/tick", {"task": tg, "act": "close"})
    check("I21 a giver closes her own task, not another giver's", st == 200 and st2 == 404 and st3 == 200, (st, st2, st3))
    alltasks = svc.panel()["panel"]["tasks"]
    check("I22 the owner's panel holds every giver's tasks", len(alltasks) == 6 and {t["by_name"] for t in alltasks} == {"Dr Manoj", "Shavez", "Dr Bhawna"}, {t["by_name"] for t in alltasks})
    svc.me("manoj", True).post("/finance/aaj/api/switch", {"op": "assigners", "logins": []})
    check("I23 the owner takes the names away: no giving box, and Dr Bhawna has no page", not svc.lst("shavez")["can_give"] and svc.lst("bhawna") == {"ok": False, "error": "off"})
    st, j = svc.me("shavez").post("/finance/aaj/api/tick", {"task": gv[0]["id"], "act": "close"})
    check("I23b ... and Shavez can no longer close or send back the task he gave", st == 404, (st, j))
    v = svc.me("manoj", True).get("/finance/aaj/api/list?as=alisha")[1]
    check("I24 the owner's view of a list shows its tasks with no button", v["tasks"] and not any(t["can_answer"] or t["can_close"] for t in v["tasks"]))

    # ---------------------------------------------------------------------------------------- J  September, for him
    print("J  September, for him only")
    put(con, "darpan_kal_day", unit="medical", business_date=OLD, handed_p=5000)
    put(con, "darpan_kal_day", unit="medical", business_date=NEW, handed_p=5000)
    con.commit()
    sp = {s["id"]: s for s in svc.panel()["panel"]["sept"]}
    check("J1 five lines, each read", len(sp) == 5 and not any(s["err"] for s in sp.values()), [(k, s["err"]) for k, s in sp.items()])
    check("J2 the bill gap before the floor is his; Shavez's list does not carry it", sp["sept.bill_gap"]["n"] == 1 and sp["sept.bill_gap"]["since"]
          and row(svc.lst("shavez"), "shavez.bill_chain_gap") is not None and it["shavez.bill_chain_gap"]["since"] == NEW)
    check("J3 the count vouchers before the floor; Darpan's cash before the floor only", sp["sept.count_vouchers"]["n"] == 1 and sp["sept.cash_received"]["n"] == 1,
          (sp["sept.count_vouchers"]["n"], sp["sept.cash_received"]["n"]))
    check("J4 the month before the floor is not final yet", sp["sept.purchases_final"]["n"] == 1 and sp["sept.returns_ok"]["n"] == 0)
    for u in ("bhati", "alisha", "shavez", "sukhveer"):
        blob = json.dumps(svc.lst(u))
        check("J5 nothing of September's list reaches %s" % u, "sept." not in blob and "September" not in blob)

    # ---------------------------------------------------------------------------------------- K  the console's contract
    print("K  the console's contract")
    allp = ak.build_all(db, with_raw=True)
    need = {"now", "today", "floor", "views", "on", "on_since", "on_by", "names", "works", "items", "map_version", "extra_version", "map_err", "extra_err"}
    check("K1 build_all() has every key 1.0 had", need <= set(allp), need - set(allp))
    ik = {"id", "person", "also", "kind", "group", "n", "n_all", "since", "days", "late", "soft", "err", "hi", "en", "how_hi", "door", "tile", "from_map", "ok_hi", "fact", "behind"}
    lack = [(i["id"], sorted(ik - set(i))) for i in allp["items"] if ik - set(i)]
    check("K2 every item has every key 1.0's items had", not lack, lack[:3])
    check("K3 the lists read as started, by the owner", allp["on"] is True and allp["on_by"] == "manoj")
    if console_py:
        cdir = os.path.join(scratch, "console")
        os.makedirs(cdir)
        shutil.copy2(console_py, os.path.join(cdir, "owner_console.py"))
        sys.path.insert(0, cdir)
        oc = importlib.import_module("owner_console")
        try:
            blocks = oc.list_blocks(allp)
            lines = []
            late_n, open_n = oc._work_people_aaj(lines, {"punch": {}, "today": allp["today"]}, allp)
            heads = [l.get("b") for l in lines if l.get("href", "") and "/finance/aaj?as=" in str(l.get("href"))]
            ok = bool(blocks) and bool(heads) and isinstance(open_n, int)
            det = (len(blocks), heads)
        except Exception as e:                                         # noqa: BLE001
            ok, det = False, "%s: %s" % (type(e).__name__, e)
        check("K4 the console's own staff section runs on it (owner_console.list_blocks, _work_people_aaj)", ok, det)
        try:
            cx = {"aaj": allp, "tile": {}, "today": allp["today"]}
            ro = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
            ro.row_factory = sqlite3.Row
            sec = oc.sec_needs(ro, cx)
            ro.close()
            ok, det = bool(sec.get("ok")) and isinstance(cx["tile"].get("needs_n"), int), (sec.get("chip"), cx["tile"])
        except Exception as e:                                         # noqa: BLE001
            ok, det = False, "%s: %s" % (type(e).__name__, e)
        check("K5 the console's own 'Needs you' section runs on it (owner_console.sec_needs)", ok, det)
    else:
        note("K4-K5 not run: no --console (owner_console.py)")
    st, j = svc.me("manoj", True).get("/finance/aaj/api/switch")
    check("K6 the console's switch button still reads the switch as it did", st == 200 and set(j) == {"ok", "on", "since", "by"} and j["on"] is True, j)
    st, j = svc.me("manoj", True).post("/finance/aaj/api/switch", {"on": 0})
    check("K7 ... and stops every list with the same post", st == 200 and j["on"] is False and svc.lst("bhati") == {"ok": False, "error": "off"}, (st, j))
    first = svc.con.execute("SELECT value FROM setting WHERE key='aaj.staff_first_on'").fetchone()[0]
    svc.me("manoj", True).post("/finance/aaj/api/switch", {"on": 1})
    check("K8 off and on again does not move the first day", svc.con.execute("SELECT value FROM setting WHERE key='aaj.staff_first_on'").fetchone()[0] == first)

    # ---------------------------------------------------------------------------------------- L  the pages
    print("L  the pages")
    page = open(os.path.join(code, "aaj_kaam.html"), encoding="utf-8").read()
    panel = open(os.path.join(code, "aaj_panel.html"), encoding="utf-8").read()
    body = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    check("L1 the staff's page draws no count and no 'late'", "kaam baaki" not in body and "late" not in body.lower().replace("later", "").replace("template", ""),
          [m.group(0) for m in re.finditer(r".{20}late.{10}", body.lower().replace("later", ""))][:3])
    check("L2 both pages draw with textContent only", "innerHTML" not in page and "innerHTML" not in panel and "document.write" not in page + panel)
    check("L3 neither page asks anything of another site", not re.search(r"(?:src|href)\s*=\s*[\"']https?://", page + panel) and "@import" not in page + panel)
    check("L4 the panel sends a line's id, words, group and switch -- nothing else", "return {id:l.id,hi:l.hi,en:l.en,when:l.when,on:!!l.on}" in panel)
    check("L4b the staff's page says 'Sab ho gaya' only when every door it asked has answered", "!DOORFAIL" in page and "DOORFAIL+=1" in page)
    node = shutil.which("node")
    if node:
        for name, h in (("aaj_kaam.html", page), ("aaj_panel.html", panel)):
            js = os.path.join(scratch, name + ".js")
            open(js, "w", encoding="utf-8").write(h.split("<script>", 1)[1].split("</script>", 1)[0])
            r = subprocess.run([node, "--check", js], capture_output=True, text=True, timeout=60)
            check("L5 the script of %s parses" % name, r.returncode == 0, r.stderr[:300])
    else:
        note("L5 not run: node is not on this machine (the scripts were parsed where the kit was built)")
    svc.close()
    con.close()

    # ---------------------------------------------------------------------------------------- the live shape
    if real_db:
        print("LIVE SHAPE  a copy of finance.db, read only")
        live = os.path.join(scratch, "live.db")
        backup(real_db, live)
        before = md5f(live)
        allp = ak.build_all(live, with_raw=True)
        check("S1 the floor on the live shape is 01-Oct-2026 (or the owner's own aaj.from)", allp["floor"] >= "2026-10-01", allp["floor"])
        check("S2 every floor view lays on the live tables", not allp["floor_bad"] and sorted(allp["staff_views"]) == sorted(seed.FLOOR), allp["floor_bad"])
        errs = ["%s: %s" % (i["id"], i["err"]) for i in allp["items"] if i["err"] and i["id"] in stand]
        other = ["%s: %s" % (i["id"], i["err"]) for i in allp["items"] if i["err"] and i["id"] not in stand]
        check("S3 every duty a panel line or the owner's console stands on runs on the live tables (%d allowed unread)" % allow_unread, len(errs) <= allow_unread, errs)
        if other:
            note("duties no panel line stands on that could not be read on the live tables (another kit's, not yet whole): %s" % "; ".join(other))
        capped = [i["id"] for i in allp["items"] if i.get("capped")]
        note("lines where the floor hid the row that says the job is done, so nothing is due (capped): %s" % (", ".join(capped) or "none"))
        c, info = ak.connect(live, X, "staff")
        leak, cut, odds = [], [], []
        for t, expr in seed.FLOOR.items():
            if t in info["views"]:
                # counted here, row by row, from the table itself -- not asked of the view
                vals = [r[0] for r in c.execute("SELECT (%s) FROM main.%s" % (expr, t))]
                keep = sum(1 for v in vals if v is not None and str(v) >= info["views"][t])
                seen = c.execute("SELECT COUNT(*) FROM temp.%s" % t).fetchone()[0]
                odd = sum(1 for v in vals if v is not None and str(v) != "" and not re.match(r"^\d{4}-\d\d-\d\d", str(v)))
                if seen != keep:
                    leak.append((t, len(vals), keep, seen))
                if odd:
                    odds.append("%s %d of %d" % (t, odd, len(vals)))
                cut.append("%s %d of %d" % (t, seen, len(vals)))
        c.close()
        check("S4 each floored table shows exactly its rows dated on or after the floor (counted from the table, row by row)", not leak, leak)
        note("rows the staff's floor leaves in sight (table, shown of all): %s" % "; ".join(cut))
        note("rows whose date does not read as a date -- kept OFF the lists, tell the assistant: %s" % ("; ".join(odds) or "none"))
        rd = ak.Reader(live)
        bad, shown, heldl = [], {}, []
        for p in rd.people.values():
            lst = ak.person_list(rd, p, view_as=True)
            shown[p["key"]] = [r["id"] for k in ak.WHEN_KEYS for r in lst["sections"][k] if not r.get("later")]
            for l in p["lines"]:
                st = ak.line_state(rd, l)
                if st["kind"] is None or st["err"]:
                    bad.append("%s: %s" % (l["id"], st["err"]))
                if st.get("held"):
                    heldl.append("%s (from %s)" % (l["id"], st["held"]))
        rd.close()
        note("held back from staff because its oldest work is dated before the floor: %s" % (", ".join(heldl) or "nothing"))
        check("S5 every line of every panel is read on the live tables (%d allowed unread)" % allow_unread, len(bad) <= allow_unread, bad)
        for k, v in shown.items():
            note("today %s would see %d line%s: %s" % (k, len(v), "" if len(v) == 1 else "s", ", ".join(v) or "-"))
        it = {i["id"]: i for i in allp["items"]}
        hid = [(i["id"], i["n"], i["n_all"]) for i in allp["items"] if i["person"] != "manoj" and i["kind"] == "sql" and i["n_all"] > i["n"]]
        note("kept off the staff's lists by the floor (line, shown, in the books): %s" % (hid or "nothing"))
        if old_py:
            a10 = {i["id"]: i for i in sys.modules["aaj_kaam_10"].build_all(live, with_raw=False)["items"]}
            same = [i for i in it if i.startswith("manoj.") and i not in ("manoj.clinic_flags", "manoj.physio_received")]
            diff = [(i, a10[i]["n"], it[i]["n"]) for i in same if i in a10 and (a10[i]["n"] != it[i]["n"] or bool(a10[i]["err"]) != bool(it[i]["err"]))]
            check("S6 on the live shape the owner's own lines count exactly what 1.0 counts (%d lines)" % len(same), not diff, diff)
            note("the owner's two ruled-off lines, 1.0 -> now: clinic flags %s -> %s, physiotherapy %s -> %s"
                 % (a10.get("manoj.clinic_flags", {}).get("n"), it["manoj.clinic_flags"]["n"], a10.get("manoj.physio_received", {}).get("n"), it["manoj.physio_received"]["n"]))
        if console_py:
            oc = sys.modules["owner_console"]
            try:
                lines = []
                oc._work_people_aaj(lines, {"punch": {}, "today": allp["today"]}, allp)
                ro = sqlite3.connect("file:%s?mode=ro" % live, uri=True)
                ro.row_factory = sqlite3.Row
                cx = {"aaj": allp, "tile": {}, "today": allp["today"]}
                sec = oc.sec_needs(ro, cx)
                ro.close()
                ok, det = bool(lines) and bool(sec.get("ok")), (len(lines), sec.get("chip"))
            except Exception as e:                                     # noqa: BLE001
                ok, det = False, "%s: %s" % (type(e).__name__, e)
            check("S6b the console's own two sections run on the live shape", ok, det)
            note("the console's 'Needs you' would read: %s" % (sec.get("chip") if ok else "?"))
        sv2 = Svc(ak, live)
        on_live = ak.staff_switch(sv2.con)[0]
        pn = sv2.panel()
        check("S7 the panel reads on the live shape: six people, five September lines", pn.get("ok") and len(pn["panel"]["people"]) == 6 and len(pn["panel"]["sept"]) == 5
              and not [s for s in pn["panel"]["sept"] if s["err"]], [s for s in pn["panel"]["sept"] if s["err"]])
        note("September, for him, on the live shape: %s" % ", ".join("%s=%s" % (s["id"].split(".")[1], s["n"]) for s in pn["panel"]["sept"]))
        j = sv2.lst("bhati")
        check("S8 the lists are %s on the live shape, and a staff login %s" % ("ON" if on_live else "OFF", "has a list" if on_live else "sees nothing"),
              (j == {"ok": False, "error": "off"}) if not on_live else bool(j.get("ok")), j if not on_live else j.get("ok"))
        sv2.close()
        check("S9 the copy of the live database is byte-identical after all of it", md5f(live) == before)
        if console_py:
            # THE CONSOLE'S OWN BUILDER, as the service runs it, with the new engine beside it: the whole of the box's finance
            # code copied to the scratch folder, the kit's files laid over it, and owner_console.py --build run there.
            cb = os.path.join(scratch, "console_build")
            os.makedirs(cb)
            for name in sorted(os.listdir(fin)):
                p = os.path.join(fin, name)
                if os.path.isfile(p) and name.endswith((".py", ".html", ".json", ".sql", ".txt")) and ".bak" not in name and not name.startswith((".", "console_")) \
                        and os.path.getsize(p) < 6_000_000:
                    shutil.copy2(p, os.path.join(cb, name))
            for f in ("aaj_kaam.py", "aaj_seed.py", "aaj_kaam.html", "aaj_panel.html"):
                shutil.copy2(os.path.join(kit, f), os.path.join(cb, f))
            out = os.path.join(scratch, "reading.dat")
            env = dict(os.environ, FINANCE_DB=live, DUTY_MAP_JSON=os.path.join(code, "DUTY_MAP.json"), AAJ_DUTIES_JSON=os.path.join(cb, "aaj_duties.json"),
                       TMPDIR=scratch, CONSOLE_SNAPSHOT=out, CONSOLE_BUILD_LOG=os.path.join(scratch, "console_build.log"))
            r = subprocess.run([sys.executable, "-B", os.path.join(cb, "owner_console.py"), "--build", "--db", live, "--out", out], cwd=cb, env=env,
                               capture_output=True, text=True, timeout=200)
            try:
                snap = json.load(open(out, encoding="utf-8"))
                ls = snap.get("lists") or {}
                ok = r.returncode == 0 and ls.get("engine") is True and not ls.get("err") and ls.get("floor") == allp["floor"] and "work" not in (snap.get("failed") or []) \
                    and "needs" not in (snap.get("failed") or [])
                det = (r.returncode, ls, snap.get("failed"))
            except Exception as e:                                     # noqa: BLE001
                ok, det = False, "%s: %s | %s" % (type(e).__name__, e, (r.stdout + r.stderr)[-300:])
            check("S10 the console's own builder, run with the new engine on the copy, makes its reading: the lists read by the new engine, 'Needs you' and 'Today's work' whole", ok, det)
            if ok:
                note("the console's reading: sections not read: %s · took %s s" % (", ".join(snap.get("failed") or []) or "none", snap.get("took_s")))
            check("S11 ... and the copy is still byte-identical (the builder reads a copy of its own)", md5f(live) == before)

    f = len(FAILS)
    print("WALK_S493 %s %d checks, %d fail" % ("GREEN" if not f else "RED", len(CHECKS), f))
    return 0 if not f else 1


if __name__ == "__main__":
    sys.exit(main())
