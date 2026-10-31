#!/usr/bin/env python3
"""walk_s688.py -- kit S688_XRAY_FILM_LOG (31-Oct-2026, the parent, S372). Runs the REAL finance app on COPIES only.

    --new  <fin> --db <copy> --scratch <dir> --kit <kitdir> [--root <root>] [--old <fin>] [--kit687 <dir>] [--only M1,M2]
          every check on the files to test: the S688 checks through the real app (inner), the builder checks (when --root
          is given: make_s688.py re-run on <root> must give <fin>'s four files byte for byte), every other person's Aaj list
          unchanged against --old, S687's own inner walk on these files (--kit687), and the mutants. Last line: "N of N green".
    --control <fin> --db <copy> --scratch <dir> --kit <kitdir>
          the CONTROL: the S688 checks only, on the LIVE files. Last line: "X S688 check(s) red . Y green".
    --inner <fin> --db <copy> --scratch <dir> --kit <kitdir>       (one process: the app is loaded once)
    --dump  <fin> --db <copy> --scratch <dir> --out <json> [--kit <kitdir>]   every person's list, as the owner sees it

<fin> is a folder holding a whole copy of /root/finance's code (never the database). --db is a COPY of finance.db; the walk
writes to it (made-up rows only: W688 names, slip numbers from 900001) and to nothing else but --scratch, where it also makes a
MADE-UP assets.db with the Scan App's real schema (no copy of the real assets.db is used). DUTY_MAP_JSON (env) names the duty
map when it is not at /root/deploy/repo/claude_code_briefs/DUTY_MAP.json. Header sign-in is switched on for this process only.
No ten-digit number is written in this file: the test phone number is put together at run time.
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile

NOW = "datetime('now','localtime')"
IDS = ("reception.xray_film_count", "shavez.xray_film_count", "shavez.xray_film_order_8x10", "shavez.xray_film_order_11x14")
PERSON = {"reception.xray_film_count": "reception", "shavez.xray_film_count": "shavez", "shavez.xray_film_order_8x10": "shavez",
          "shavez.xray_film_order_11x14": "shavez"}
WHENS = {"reception.xray_film_count": "first", "shavez.xray_film_count": "day", "shavez.xray_film_order_8x10": "comeup",
         "shavez.xray_film_order_11x14": "comeup"}
DOORS = {"reception.xray_film_count": "/finance/slips/film/subah", "shavez.xray_film_count": "/finance/slips/film/subah",
         "shavez.xray_film_order_8x10": "/finance/slips/film/log", "shavez.xray_film_order_11x14": "/finance/slips/film/log"}
B = "/finance/slips/film"
PAGES = (B, B + "/subah", B + "/log", B + "/list", B + "/log.xlsx", B + "/list.xlsx")
TEN = re.compile(r"(?<!\d)\d{10,}(?!\d)")
SAVED_HI = "सेव हो गया"
CHECK_RE = re.compile(r"^  (ok |RED)  ")
RETIRED = "reception.week_film_stock"        # the owner's ruling, 20:20 IST 31-Oct-2026: the machine shows the films loaded
TABLES = ("xf_setting", "xf_save", "xf_count", "xf_purchase", "xf_bill_size", "xf_bill_qty", "xf_study", "xf_contact")
results = []

ASSETS_DDL = """
CREATE TABLE IF NOT EXISTS assets(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL,
  location_id INTEGER NOT NULL,
  category TEXT NOT NULL DEFAULT 'Other',
  purchase_date TEXT, price REAL, vendor TEXT, vendor_phone TEXT,
  serial_no TEXT, status TEXT NOT NULL DEFAULT 'Active',
  contract_type TEXT NOT NULL DEFAULT 'None', provider TEXT, contract_cost REAL,
  notes TEXT, hidden INTEGER NOT NULL DEFAULT 0, hide_price INTEGER NOT NULL DEFAULT 0,
  created_by INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')), bill_id INTEGER);
CREATE TABLE IF NOT EXISTS bills(
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'Consumable',
  vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL,
  notes TEXT, source_stored TEXT, source_orig TEXT,
  created_by INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  stamp_no TEXT, status TEXT NOT NULL DEFAULT 'approved', lane TEXT, dup_of INTEGER, rescan_of INTEGER, subgroup TEXT);
CREATE TABLE IF NOT EXISTS bill_items(
  id INTEGER PRIMARY KEY,
  bill_id INTEGER NOT NULL,
  item_name TEXT NOT NULL, pack_size TEXT, quantity REAL, rate REAL, amount REAL,
  make TEXT, model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT, asset_id INTEGER);
CREATE TABLE IF NOT EXISTS xray_film_line(id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL, asset_created_at TEXT NOT NULL DEFAULT '',
  size TEXT NOT NULL, boxes REAL, amount REAL NOT NULL, by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '',
  voided_by TEXT NOT NULL DEFAULT '');
"""


def check(name, cond, note=""):
    results.append((name, bool(cond), note))
    print("  %s  %s%s" % ("ok " if cond else "RED", name, ("  -- " + str(note)[:220]) if note and not cond else ""))
    sys.stdout.flush()


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def copydb(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:                                             # noqa: BLE001
        return default if default is not None else ("ERR", "%s: %s" % (type(e).__name__, str(e)[:160]))


# ================================================================================================ the inner walk
def inner(a):
    fin, dbp, scr, kit = os.path.abspath(a.inner), os.path.abspath(a.db), os.path.abspath(a.scratch), os.path.abspath(a.kit)
    os.makedirs(scr, exist_ok=True)
    print("-- S688 inner walk: %s . db %s" % (fin, os.path.basename(dbp)))
    raw = sqlite3.connect(dbp, timeout=30, isolation_level=None)
    raw.row_factory = sqlite3.Row
    # ---- 0 the copy prepared: xf_* gone (first-request state), the lists on, no saved Shavez / Reception panel
    for (t,) in list(raw.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'xf\\_%' ESCAPE '\\'")):
        raw.execute("DROP TABLE %s" % t)
    have = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    on = raw.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
    if not (on and "|" in str(on[0] or "")):
        raw.execute("DELETE FROM setting WHERE key='aaj.staff_on'")
        raw.execute("INSERT INTO setting (key, value, note) VALUES ('aaj.staff_on','2026-10-07T11:27:09|manoj','S688 walk')")
    if "aaj_cfg" in have:
        raw.execute("DELETE FROM aaj_cfg WHERE person IN ('shavez','reception')")
    mj_tables(dbp, fin)
    schema0 = {r[0]: r[1] for r in raw.execute("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'xf\\_%' ESCAPE '\\' AND sql IS NOT NULL")}
    svc = {r["code"] or ("#%d" % r["id"]): r["id"] for r in raw.execute("SELECT id, code FROM owner_service WHERE kind='xray'")}
    svn = {r["name"]: r["id"] for r in raw.execute("SELECT id, name FROM owner_service WHERE kind='xray'")}
    # the made-up slips: March 2027 (no copy holds any: a live copy's own November never mixes in) -- paid, unpaid and void
    oct_lines = raw.execute("SELECT COUNT(*) FROM slip s JOIN slip_item i ON i.slip_id=s.id AND i.kind='xray' WHERE s.series='xp' AND s.state='ok' "
                            "AND s.paid_mode IN ('cash','upi') AND s.day BETWEEN '2026-10-01' AND '2026-10-31'").fetchone()[0]
    sums0 = raw.execute("SELECT COUNT(*), COALESCE(SUM(id*3+slip_no),0) FROM slip").fetchone()[:]
    made = []

    def mkslip(no, day, items, paid="cash", state="ok", name="W688 PATIENT"):
        sid = raw.execute("INSERT INTO slip (series, slip_no, day, clinic_id, no_id_name, name_seen, state, paid_mode, logged_by, logged_at) "
                          "VALUES ('xp',?,?,'',?,'',?,?,'w688',?)", (no, day, "%s %d" % (name, no), state, paid, day + " 10:00:00")).lastrowid
        for k, it in enumerate(items):
            raw.execute("INSERT INTO slip_item (slip_id, kind, service_id, name, side, price_p, sort) VALUES (?,?,?,?,?,0,?)",
                        (sid, "xray", it[0], it[1], it[2] if len(it) > 2 else "", k))
        made.append(sid)
    s_ks, s_knee, s_pbh, s_wrist, s_femur = svc.get("KS"), svc.get("KNEE"), svc.get("PBH"), svc.get("WRIST"), svc.get("FEMUR")
    s_frog = svn.get("Pelvis both hips frog-leg view (11 x 14)")
    s_ls, s_ankle = svc.get("LS"), svc.get("ANKLE")
    mkslip(900001, "2027-03-01", [(s_ks, "")])                       # K/S: two 8x10 films
    mkslip(900002, "2027-03-01", [(s_knee, ""), (s_pbh, "")])         # 1 x 8x10, 1 x 11x14
    mkslip(900003, "2027-03-01", [(s_wrist, ""), (s_femur, ""), (s_frog, "")], paid="upi")   # 3 x 11x14
    mkslip(900004, "2027-03-01", [(None, "Other: W688 typed study")])  # size not set
    mkslip(900005, "2027-03-01", [(s_ls, "")], paid="")               # NOT paid: not counted
    mkslip(900006, "2027-03-01", [(s_ks, "")], state="void")          # void: not counted
    mkslip(900007, "2027-03-02", [(s_ls, "")])
    mkslip(900008, "2027-03-02", [(s_ls, "")], paid="upi")
    mkslip(900009, "2027-03-03", [(s_ankle, "")])
    s_bknees = svn.get("Both knees AP standing view")
    # side B (both sides): a day after the last count (no span reads it)
    mkslip(900010, "2027-03-12", [(s_knee, "", "B"), (s_bknees, "", "B"), (s_ls, "", "L"), (s_ks, "", "B")])
    # the made-up Scan App database (the real schema from the asset app's code; no copy of the real one)
    adb = os.path.join(scr, "assets_w688.db")
    if os.path.exists(adb):
        os.remove(adb)
    ac = sqlite3.connect(adb, isolation_level=None)
    ac.executescript(ASSETS_DDL)

    # ---- the files under test
    duties_path = os.path.join(fin, "aaj_duties.json")
    duties = safe(lambda: json.load(open(duties_path, encoding="utf-8")), {})
    extra = {x.get("id"): x for x in (duties.get("extra") or [])} if isinstance(duties, dict) else {}
    mine = [extra.get(i) for i in IDS]
    check("S688 F1 the duties file holds the four duties (kind sql, each door its own page)",
          all(d and d.get("kind") == "sql" and d.get("door") == DOORS[d["id"]] for d in mine), [d and d.get("door") for d in mine])
    check("S688 F2 each duty SQL is one read-only SELECT (WITH), no ';', its clock written exactly once, reads only xf_* tables",
          all(d and re.match(r"(?is)^(select|with)\b", d.get("sql") or "") and ";" not in d["sql"] and d["sql"].count(NOW) == 1
              and set(re.findall(r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)", d["sql"])) <= set(TABLES) | {"cur", "u", "lt", "w", "cfg", "t", "d", "av", "st0", "sp"}
              for d in mine))
    wpath = os.path.join(scr, "w688_duties.json")

    def write_duties(ts=None):
        w = json.loads(json.dumps(duties)) if isinstance(duties, dict) else {}
        for x in w.get("extra") or []:
            if ts and x.get("id") in IDS and isinstance(x.get("sql"), str):
                x["sql"] = x["sql"].replace(NOW, "'%s'" % ts)
        with open(wpath, "w", encoding="utf-8") as fh:
            json.dump(w, fh, ensure_ascii=False)
    write_duties()
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", AAJ_DUTIES_JSON=wpath,
                      XRAYFILM_NOW="2026-10-31T10:00:00", ASSETS_DB=adb)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                           # noqa: E402
    import aaj_kaam                                                    # noqa: E402
    import aaj_seed                                                    # noqa: E402
    sys.path.insert(1, kit)
    import cfg_s688                                                    # noqa: E402
    mf = [n for n, _w in getattr(fa, "_MOUNT_FAILED", [])]
    check("S688 A1 the real finance app mounts with _MOUNT_FAILED empty, xray_film AND month_jobs loaded",
          mf == [] and "xray_film" in sys.modules and "month_jobs" in sys.modules, mf)
    xf = sys.modules.get("xray_film")
    seed = {p["key"]: {ln["id"]: ln for ln in p["lines"]} for p in aaj_seed.PEOPLE}
    check("S688 F3 the panels: Reception's count line under 'Sabse pehle', Shavez's stand-in under 'Aaj', his two order lines under "
          "'Jab aaye', all on, the order lines worded '<size> film mangwaiye — 1 box'",
          all(i in seed.get(PERSON[i], {}) and seed[PERSON[i]][i]["on"] and seed[PERSON[i]][i]["when"] == WHENS[i] for i in IDS)
          and seed["shavez"].get("shavez.xray_film_order_8x10", {}).get("hi") == "8×10 film mangwaiye — 1 box"
          and seed["shavez"].get("shavez.xray_film_order_11x14", {}).get("hi") == "11×14 film mangwaiye — 1 box",
          [seed.get(PERSON[i], {}).get(i, {}).get("when") for i in IDS])
    check("S688 F5 the retired weekly tick 'X-ray film ka stock giniye' is on no panel of the seed and not in the duties file",
          not [x for p in aaj_seed.PEOPLE for x in p["lines"] if x["id"] == RETIRED] and RETIRED not in extra
          and RETIRED not in open(duties_path, encoding="utf-8").read())
    check("S688 F4 the data step's lines are the seed's (id, words, group, on)",
          all(any(x["id"] == i and x["hi"] == seed[PERSON[i]][i]["hi"] and x["en"] == seed[PERSON[i]][i]["en"]
                  and x["when"] == seed[PERSON[i]][i]["when"] and x["on"] for x in cfg_s688.LINES[PERSON[i]]) for i in IDS if i in seed.get(PERSON[i], {}))
          and all(i in seed.get(PERSON[i], {}) for i in IDS))

    c = fa.app.test_client(use_cookies=False)
    urls, pages, staff_pages = [], [], []

    def req(method, path, user, data=None, now=None):
        if now:
            os.environ["XRAYFILM_NOW"] = now
        h = {"X-Clinic-User": user} if user else {}
        r = c.get(path, headers=h) if method == "GET" else c.post(path, data=data or {}, headers=h)
        loc = (r.headers.get("Location") or "").replace("http://localhost", "")
        urls.append(path)
        if loc:
            urls.append(loc)
        return r.status_code, r.get_data(as_text=(".xlsx" not in path)), loc, r

    def G(path, user, now=None):
        s_, b_, l_, _r = req("GET", path, user, now=now)
        if isinstance(b_, str) and s_ == 200:
            pages.append(b_)
            if user in ("shavez", "alisha", "shivani"):
                staff_pages.append(b_)
        return s_, b_, l_

    def P(path, user, data, now=None):
        s_, b_, l_, _r = req("POST", path, user, data, now)
        return s_, b_, l_

    def sq(sql, args=()):
        try:
            return raw.execute(sql, args).fetchall()
        except sqlite3.Error as e:
            return [("ERR", str(e))]

    def n_of(t):
        r = sq("SELECT COUNT(*) FROM %s" % t)
        return r[0][0] if r and r[0][0] != "ERR" else -1

    def due(did, ts):
        d = extra.get(did)
        if not d:
            return ("no duty",)
        try:
            r = raw.execute(d["sql"].replace(NOW, "'%s'" % ts)).fetchone()
            return (r[0], r[1]) if r[0] else (0,)
        except sqlite3.Error as e:
            return ("ERR", str(e)[:80])

    def py_due(size, day):
        import datetime as _dt
        con_ = sqlite3.connect(dbp)
        con_.row_factory = sqlite3.Row
        try:
            return bool(xf.size_state(con_, size, _dt.date.fromisoformat(day))["due"])
        finally:
            con_.close()

    def st_of(size, day):
        import datetime as _dt
        con_ = sqlite3.connect(dbp)
        con_.row_factory = sqlite3.Row
        try:
            s_ = xf.size_state(con_, size, _dt.date.fromisoformat(day))
            return dict(left=s_["left"], avg=s_["avg"], days=s_["days"], due=s_["due"], why=s_["why"], spare=s_["spare"], loads=s_["loads"])
        except Exception as e:                                         # noqa: BLE001 -- the control: no module, no state
            return dict(left=None, avg=None, days=None, due=None, why="ERR %s" % type(e).__name__, spare=None, loads=None)
        finally:
            con_.close()

    agree = []

    def both(day, ts=None):
        """The order duty's SQL and the module's own rule agree, for both sizes."""
        ts = ts or (day + " 09:30:00")
        for size in ("8x10", "11x14"):
            sqln = due("shavez.xray_film_order_%s" % size, ts)[0]
            pyd = safe(lambda: py_due(size, day), "ERR")
            agree.append((day, size, sqln, pyd))
        return {s: due("shavez.xray_film_order_%s" % s, ts)[0] for s in ("8x10", "11x14")}

    # ---- 1 the first request makes the tables, the study seed and the one supplier row
    s, body, _l = G(B + "/subah", "alisha")
    tabs = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'xf\\_%' ESCAPE '\\'")}
    check("S688 T1 reception's first request: 200 and the eight xf_* tables made", s == 200 and tabs == set(TABLES), (s, sorted(tabs)))
    stud = {r[0]: (r[1], r[2]) for r in sq("SELECT service_id, size, films FROM xf_study") if len(r) == 3}
    want = {s_ks: ("8x10", 2), s_knee: ("8x10", 1), s_pbh: ("11x14", 1), s_wrist: ("11x14", 1), s_femur: ("11x14", 1), s_frog: ("11x14", 1),
            svn.get("wrist ap & lateral views"): ("11x14", 1), svn.get("Both knees AP standing view"): ("", 1), svn.get("Chest PA view"): ("", 1),
            svn.get("X RAY BOTH LOWER LIMBS"): ("", 1), s_ls: ("8x10", 1)}
    check("S688 T2 the studies seeded from his words: K/S two 8x10, Knee AP & Lateral one 8x10, wrist / pelvis both hips / femur / frog-leg "
          "11x14, both-knees, chest PA and both lower limbs 'size not set' (never guessed)",
          all(k is not None and stud.get(k) == v for k, v in want.items()) and len(stud) == len(svn), {k: stud.get(k) for k in want})
    ct = sq("SELECT name, firm, role, phone FROM xf_contact")
    check("S688 T3 one contact seeded: Nigam, Jugnu Medicos (Fuji), films supplier, NO number",
          [tuple(r) for r in ct] == [("Nigam", "Jugnu Medicos (Fuji)", "films_supplier", "")], [tuple(r) for r in ct])
    out1 = safe(lambda: cfg_s688.tables(dbp, fin), "ERR")
    out2 = safe(lambda: cfg_s688.panel(dbp), "ERR")
    check("S688 T4 the data step after it: 0 tables made, no saved panel, 0 changed (idempotent)",
          str(out1).startswith("tables: 0 made") and str(out2).endswith("0 changed"), (out1, out2))

    # ---- 2 who reaches what
    want_st = {}
    for u in ("manoj", "bhawna"):
        want_st[u] = {p: 200 for p in PAGES}
        want_st[u][B] = 302
    for u in ("shavez", "alisha", "shivani"):
        want_st[u] = {p: 200 for p in PAGES}
        want_st[u][B] = 302
    bad = []
    for u in ("manoj", "bhawna", "shavez", "alisha", "shivani", "darpan", "awdhesh", "bhati", "sukhveer", "w688nobody", ""):
        for p in PAGES:
            st, b_, loc, _r = req("GET", p, u)
            w = want_st.get(u, {}).get(p)
            if u in ("awdhesh", "bhati", "sukhveer"):
                w = 403
            elif u in ("darpan", "w688nobody", ""):
                w = 302
            if st != w:
                bad.append((u or "anon", p, st, w))
    st1, _b, l1 = G(B, "manoj")
    st2, _b, l2 = G(B, "alisha")
    check("S688 R1 every page: manoj, bhawna, shavez, alisha, shivani 200; awdhesh, bhati, sukhveer (slips logins with no job) 403; "
          "darpan, no slips row or no login 302; the hub sends the doctors to the English log and the staff to the morning count",
          not bad and l1.endswith(B + "/log") and l2.endswith(B + "/subah"), bad[:6])
    n0 = (n_of("xf_contact"), n_of("xf_setting"), n_of("xf_study"), n_of("xf_save"))
    rr = [P(B + "/owner/contact", u, {"op": "add", "name": "W688 X", "role": "other"})[0] for u in ("bhawna", "shavez", "alisha")]
    rr += [P(B + "/owner/settings", "shavez", {"order_days": "5", "standin_after": "11:00", "count_from": "2026-11-01"})[0],
           P(B + "/owner/study", "bhawna", {"service_id": str(s_ls), "size": "11x14", "films": "1"})[0],
           P(B + "/subah", "awdhesh", {"c_8x10": "1", "c_11x14": "1"})[0],
           P(B + "/owner/count", "shavez", {"day": "2026-10-31", "op": "void"})[0]]
    check("S688 R2 only the owner changes contacts, settings, film sizes and past counts (bhawna, shavez, alisha 403); a slips login with "
          "no job cannot save a count (403); nothing written",
          rr == [403] * 7 and (n_of("xf_contact"), n_of("xf_setting"), n_of("xf_study"), n_of("xf_save")) == n0, rr)

    # ---- 3 the Aaj lines before any count: not before count.from, never on a Sunday, the stand-in only from 11:00
    d31 = due("reception.xray_film_count", "2026-10-31 09:00:00")
    d01 = due("reception.xray_film_count", "2026-11-01 09:00:00")
    d02 = due("reception.xray_film_count", "2027-03-01 08:00:00")
    s1059 = due("shavez.xray_film_count", "2027-03-01 10:59:00")
    s1100 = due("shavez.xray_film_count", "2027-03-01 11:00:00")
    check("S688 L1 reception's count line: not on 31-Oct (before 1-Nov), not on Sunday 1-Nov, due Monday 1-Mar-2027 from the morning; "
          "Shavez's stand-in not at 10:59, due at 11:00",
          d31 == (0,) and d01 == (0,) and d02 == (1, "2027-03-01") and s1059 == (0,) and s1100 == (1, "2027-03-01"), (d31, d01, d02, s1059, s1100))

    def rows_of(user, as_=None):
        st_, b_, _l_, _r = req("GET", "/finance/aaj/api/list" + ("?as=%s" % as_ if as_ else ""), user)
        try:
            j = json.loads(b_)
        except ValueError:
            return st_, {}, []
        return st_, j, [dict(r, section=s_["key"]) for s_ in (j.get("sections") or []) for r in s_["rows"]]

    def unread(key):
        rd = aaj_kaam.Reader(dbp)
        try:
            return aaj_kaam.person_list(rd, rd.people[key])["unread"]
        finally:
            rd.close()
    write_duties("2027-03-01 11:30:00")
    _s, ja, ra = rows_of("alisha")
    _s, js, rs = rows_of("shavez")
    _s, jv, rv = rows_of("shivani")
    na = {r["id"]: r for r in ra if r["id"] in IDS}
    ns = {r["id"]: r for r in rs if r["id"] in IDS}
    check("S688 L2 1-Mar 11:30, nothing counted: alisha's and shivani's list (Reception's) shows the count line under 'Sabse pehle' opening "
          "the morning page; Shavez's shows his stand-in; no order line (no box yet); every list whole (unread 0)",
          set(na) == {"reception.xray_film_count"} and na["reception.xray_film_count"]["door"] == DOORS["reception.xray_film_count"]
          and na["reception.xray_film_count"]["section"] == "first" and set(ns) == {"shavez.xray_film_count"}
          and {r["id"] for r in rv if r["id"] in IDS} == {"reception.xray_film_count"}
          and ja.get("partial") is False and js.get("partial") is False
          and safe(lambda: unread("reception"), -1) == 0 and safe(lambda: unread("shavez"), -1) == 0, (sorted(na), sorted(ns), ja.get("partial")))
    items = safe(lambda: aaj_kaam.build_all(dbp)["items"], [])
    bi = {i.get("id"): i for i in items if isinstance(i, dict) and i.get("id") in IDS}
    check("S688 L3 the owner's console reading (build_all): the four duties read, none in error; the count lines n = 1 on 1-Mar 11:30",
          set(bi) == set(IDS) and all(bi[i]["err"] is None for i in IDS) and bi["reception.xray_film_count"]["n"] == 1
          and bi["shavez.xray_film_count"]["n"] == 1, {k: (v["n"], v["err"]) for k, v in bi.items()})

    # ---- 4 the morning figures -- FILMS LEFT on the machine's screen: 1-Mar, 2-Mar, (3-Mar missed), 4-Mar; refusals; the Saved card
    sb = P(B + "/subah", "alisha", {"c_8x10": "120"}, now="2027-03-01T09:10:00")[2]
    sb2 = P(B + "/subah", "alisha", {"c_8x10": "120", "c_11x14": "1x0"}, now="2027-03-01T09:10:00")[2]
    sb3 = P(B + "/subah", "alisha", {"c_8x10": "160", "c_11x14": "100"}, now="2027-03-01T09:11:00")[2]
    _s, so3, _l = G(sb3, "alisha") if sb3 else (0, "", "")
    nb = n_of("xf_count")
    st, _b, loc = P(B + "/subah", "alisha", {"c_8x10": "120", "c_11x14": "100"}, now="2027-03-01T09:12:00")
    g = G(loc, "alisha") if loc else (0, "", "")
    check("S688 S1 alisha saves 1-Mar's films left (one Save, both sizes): the Saved card 'सेव हो गया' with both figures and who; a half-filled "
          "or a wrong figure refused, and a figure above a box's 150 refused for staff ('Dr Manoj se confirm karaiye'); nothing written",
          "msg=blank" in sb and "msg=bad" in sb2 and "msg=over" in sb3 and "Dr Manoj se confirm karaiye" in so3 and nb == 0 and st == 302
          and "msg=saved" in loc and SAVED_HI in g[1] and "bachi 120" in g[1] and "bachi 100" in g[1] and "Alisha" in g[1] and n_of("xf_count") == 2,
          (sb, sb2, sb3, nb, loc))
    write_duties("2027-03-01 11:30:00")
    _s, _j, ra2 = rows_of("alisha")
    _s, _j, rs2 = rows_of("shavez")
    check("S688 L4 after the save the count lines are gone from Reception's and Shavez's lists (unread 0)",
          not [r for r in ra2 + rs2 if r["id"] in IDS] and safe(lambda: unread("reception"), -1) == 0, [r["id"] for r in ra2 + rs2 if r["id"] in IDS])
    P(B + "/subah", "shivani", {"c_8x10": "116", "c_11x14": "96"}, now="2027-03-02T09:05:00")
    st, _b, loc = P(B + "/subah", "shavez", {"c_8x10": "113", "c_11x14": "94"}, now="2027-03-04T09:02:00")
    g = G(loc, "shavez", now="2027-03-04T09:03:00") if loc else (0, "", "")
    check("S688 S3 a normal decline: Shavez saves 4-Mar (3-Mar missed): the Saved card shows the joined span -- 8x10 116 -> 113 used 3, on "
          "slips 3; 11x14 96 -> 94 used 2, on slips 0",
          "msg=saved" in loc and SAVED_HI in g[1] and "kal lagi 3 · parchi par 3" in g[1] and "kal lagi 2 · parchi par 0" in g[1], loc)
    sp = safe(lambda: xf.spans(_con(dbp), __import__("datetime").date(2027, 3, 4))[0], [])
    spw = [(x["p"], x["end"], x["machine"]["8x10"], x["slips"]["8x10"], x["machine"]["11x14"], x["slips"]["11x14"], x["slips"][""]) for x in sp] if isinstance(sp, list) else sp
    check("S688 S4 the arithmetic: 1-Mar used 120-116 = 4 / 100-96 = 4 against slips 3 (K/S = 2, knee 1) / 4 (pelvis, wrist, femur, frog-leg) "
          "and 1 'size not set'; the missed 3-Mar joins 2-Mar: 3 / 2 against 3 / 0 (the unpaid and the void slip never count)",
          spw == [("2027-03-01", "2027-03-01", 4, 3, 4, 4, 1), ("2027-03-02", "2027-03-03", 3, 3, 2, 0, 0)], spw)

    # BLOCKER (review 4): the owner re-saves 2-Mar (same figures) at 16:30 -- his correction's time never makes 2-Mar a late count
    lt0 = P(B + "/owner/count", "manoj", {"day": "2027-03-02", "op": "edit", "c_8x10": "116", "c_11x14": "96"}, now="2027-03-04T16:30:00")[2]
    lsp = safe(lambda: [(x["p"], x["q"], x.get("late"), x.get("pending")) for x in xf.log_spans(_con(dbp), __import__("datetime").date(2027, 3, 4))[0]], "ERR")
    # ---- 5 the film log: staff see the gap, no reason asked; the owner's English page; the month's summary
    s_a, la, _l = G(B + "/log?m=2027-03", "alisha", now="2027-03-04T16:40:00")
    s_o, lo, _l = G(B + "/log?m=2027-03", "manoj", now="2027-03-04T16:40:00")
    check("S688 LT1 the owner corrects 2-Mar at 16:30 on 4-Mar: the late rule reads the day's FIRST staff count (Shivani, 09:05), not his "
          "correction -- 1-Mar, 2-Mar and 4-Mar stay separate spans, none late, and neither page says 'der se ginti' / 'late count'",
          "msg=saved" in lt0 and lsp == [("2027-03-01", "2027-03-02", False, False), ("2027-03-02", "2027-03-04", False, False)]
          and "der se ginti" not in la and "late count" not in lo, (lt0, lsp))
    check("S688 G1 the gap is on the staff page (Hinglish) -- '8×10 +1' on 1-Mar, '11×14 +2' on 2–3 Mar, the missed morning 'joined' -- "
          "with no reason field anywhere (no text box, no 'kaaran' asked)",
          s_a == 200 and "8×10 +1" in la and "11×14 +2" in la and "agli ginti mein joda gaya" in la and "<textarea" not in la
          and not re.search(r"name='(?:reason|kaaran|why|wajah)", la) and "Farq wale din: <b>2</b>" in la and "Subah ginti nahi hui: <b>1</b>" in la,
          (s_a,))
    check("S688 G2 the owner's log is English (no Devanagari) with the boxes, the month (days with a gap 2, mornings not counted 1), the "
          "contacts, the film bills, the box loads, the settings and the film sizes",
          s_o == 200 and not re.search(r"[ऀ-ॿ]", lo) and "Days with a gap: <b>2</b>" in lo and "Mornings not counted: <b>1</b>" in lo
          and all(x in lo for x in ("Contacts — films, Fuji service and support", "FILM BILLS IN THE SCAN APP", "NEW BOXES LOADED", "SETTINGS",
                                    "FILM SIZE AND FILMS PER STUDY", "Not counted next morning — joined to the next count")), s_o)

    # ---- 6 films left, days left, box loads, the order line -- the duty's SQL and the module's rule agree at every step
    st5 = st_of("8x10", "2027-03-04")
    check("S688 B1 4-Mar: 8x10 films left = the newest figure 113, average 7 films / 3 days; days left 48 (no order line); too little data "
          "before 3 days of counts (2-Mar: no days-left, no line)",
          st5["left"] == 113 and abs(st5["avg"] - 7 / 3.0) < 1e-9 and int(st5["days"]) == 48 and not st5["due"]
          and st_of("8x10", "2027-03-02")["days"] is None and st_of("8x10", "2027-03-02")["why"] == "little" and both("2027-03-02") == {"8x10": 0, "11x14": 0},
          (st5, st_of("8x10", "2027-03-02")))
    ns0 = n_of("xf_count")
    su1 = P(B + "/subah", "alisha", {"c_8x10": "90", "c_11x14": "15"}, now="2027-03-05T09:00:00")[2]
    _s, psu, _l = G(su1, "alisha", now="2027-03-05T09:00:20") if su1 else (0, "", "")
    ns1 = n_of("xf_count")
    su2 = P(B + "/subah", "alisha", {"c_8x10": "90", "c_11x14": "15", "sure_11x14": "1"}, now="2027-03-05T09:00:40")[2]
    def _ns():
        import datetime as _dt
        m_ = sqlite3.connect(":memory:")
        m_.row_factory = sqlite3.Row
        m_.executescript(xf.SCHEMA)
        for dd, v in (("2027-05-01", 120), ("2027-05-02", 116)):
            m_.execute("INSERT INTO xf_count (save_id, day, size, remaining, saved_at, saved_by) VALUES (0,?,'8x10',?,?,'w')", (dd, v, dd + " 09:00:00"))
        return (xf.needs_sure(m_, "8x10", "2027-05-03", 10), xf.needs_sure(m_, "8x10", "2027-05-03", 80))
    nsr = safe(_ns, "ERR")
    check("S688 SU1 a fall far above the average (11x14 94 -> 15 = 79 used, the average 2 a day, over 30): staff are not refused but asked -- "
          "nothing written, the figures kept in the fields, 'Haan, machine par yahi dikh raha hai' for 11x14 only; ticked, saved. With no "
          "average yet (two counts) no question is asked",
          "msg=sure" in su1 and "what=11x14" in su1 and ns1 == ns0 and "name='sure_11x14'" in psu and "name='sure_8x10'" not in psu
          and "Haan, machine par yahi dikh raha hai" in psu and "itni film ek saath aam taur par nahi lagti" in psu and "value='15'" in psu
          and "msg=saved" in su2 and nsr == (False, False), (su1, su2, nsr))
    d6 = both("2027-03-05")
    # BLOCKER (review 3): a typo one film UP must never become a box load
    nk0 = n_of("xf_count")
    k1 = P(B + "/subah", "shivani", {"c_8x10": "91", "c_11x14": "14"}, now="2027-03-06T08:50:00")[2]
    _s, pk1, _l = G(k1, "shivani", now="2027-03-06T08:50:30") if k1 else (0, "", "")
    k2 = P(B + "/subah", "shivani", {"c_8x10": "70", "c_11x14": "140"}, now="2027-03-06T08:55:00")[2]
    _s, pk2, _l = G(k2, "shivani", now="2027-03-06T08:55:30") if k2 else (0, "", "")
    nk1 = n_of("xf_count")
    k3 = P(B + "/subah", "alisha", {"c_8x10": "70", "c_11x14": "140", "newbox_11x14": "1"}, now="2027-03-06T09:00:00")[2]
    check("S688 BK1 a figure UP is a new box only from 20 or less, ticked: 8x10 90 -> 91 refused for staff ('Pichhli ginti mein 90 film "
          "bachi thi — badhi kaise? Dr Manoj se confirm karaiye'); 11x14 15 -> 140 without the tick refused (the tick shown); with "
          "'Haan, naya box lagaya gaya' ticked -- saved, a box load",
          "msg=risen" in k1 and "what=8x10" in k1 and "Pichhli ginti mein 90 film bachi thi — badhi kaise? Dr Manoj se confirm karaiye" in pk1
          and "msg=tick" in k2 and "Haan, naya box lagaya gaya" in pk2 and nk1 == nk0 and "msg=saved" in k3, (k1, k2, k3))
    d7 = both("2027-03-06")
    st7 = st_of("8x10", "2027-03-06")
    check("S688 B2 5-Mar: 8x10 90 left at 7.5 a day = 12 days -- no line; 6-Mar: 70 left at 10 a day = 7 days, under 10 -- the 8x10 order "
          "line; 11x14 heavy use (15 left on 5-Mar) -- its line too",
          d6 == {"8x10": 0, "11x14": 1} and d7 == {"8x10": 1, "11x14": 1} and st7["left"] == 70 and st7["days"] == 7.0, (d6, d7, st7))
    r11 = safe(lambda: xf.readings(_con(dbp), "11x14", "2027-03-06")[-1], {})
    s_o, lo6, _l = G(B + "/log", "manoj", now="2027-03-06T09:20:00")
    s_s, ls6, _l = G(B + "/log", "shavez", now="2027-03-06T09:21:00")
    check("S688 LD1 a rise is a box load: 11x14 15 -> 140 on 6-Mar = ONE automatic box load that day, used 15 + (150 - 140) = 25; the log says "
          "'naya box (machine se pata chala)' (staff and owner) and the owner's NEW BOXES LOADED lists it; the spare stock goes to -1: "
          "'1 box ka bill abhi nahi aaya — pehle bill scan karaiye, phir order dekhiye' (owner: '1 box(es) loaded with no bill yet — scan "
          "the bill first, then see about the order')",
          r11.get("load") is True and r11.get("used") == 25 and r11.get("left") == 140 and "11×14: naya box (machine se pata chala)" in ls6
          and "06-Mar — 11×14 · naya box (machine se pata chala)" in lo6 and st_of("11x14", "2027-03-06")["loads"] == ["2027-03-06"]
          and st_of("11x14", "2027-03-06")["spare"] == -1 and "1 box ka bill abhi nahi aaya — pehle bill scan karaiye, phir order dekhiye" in ls6
          and "1 box(es) loaded with no bill yet — scan the bill first, then see about the order" in lo6, r11)
    check("S688 OP1 the opening boxes not set: the owner's page says 'Opening boxes not set — set them so ordering is right' (both sizes); "
          "the order card on the page the line opens says '(Dr Manoj ne shuru ka stock abhi nahi bhara)'; the line's own help no longer "
          "promises it clears when a bill is scanned",
          "Opening boxes not set — set them so ordering is right" in lo6 and "8×10 and 11×14" in lo6
          and ls6.count("(Dr Manoj ne shuru ka stock abhi nahi bhara)") == 2
          and all("scan ho." not in extra[i]["how_hi"] and "wahin likha hai" in extra[i]["how_hi"]
                  for i in ("shavez.xray_film_order_8x10", "shavez.xray_film_order_11x14")), lo6.count("Opening boxes not set"))
    write_duties("2027-03-06 09:30:00")
    _s, js7, rs7 = rows_of("shavez")
    o7 = {r["id"]: r for r in rs7 if r["id"] in IDS}
    items = safe(lambda: aaj_kaam.build_all(dbp)["items"], [])
    bi = {i.get("id"): i for i in items if isinstance(i, dict) and i.get("id") in IDS}
    check("S688 B3 Shavez's list on 6-Mar: '8×10 film mangwaiye — 1 box' and '11×14 ...' under 'Jab aaye', opening the film log; the owner's "
          "console has both lines (n 1, no error); the list whole",
          set(o7) == {"shavez.xray_film_order_8x10", "shavez.xray_film_order_11x14"} and o7["shavez.xray_film_order_8x10"]["text"] == "8×10 film mangwaiye — 1 box"
          and all(o7[i]["section"] == "comeup" and o7[i]["door"] == DOORS[i] for i in o7) and js7.get("partial") is False
          and bi.get("shavez.xray_film_order_8x10", {}).get("n") == 1 and bi.get("shavez.xray_film_order_11x14", {}).get("n") == 1
          and all(bi[i]["err"] is None for i in bi) and safe(lambda: unread("shavez"), -1) == 0, (sorted(o7), {k: (v["n"], v["err"]) for k, v in bi.items()}))
    # the setting is the line's edge: exactly 7.0 days left -> no line under 7, a line under 8
    sa = P(B + "/owner/settings", "manoj", {"order_days": "7"}, now="2027-03-06T09:40:00")[2]
    e7 = both("2027-03-06")["8x10"]
    P(B + "/owner/settings", "manoj", {"order_days": "8"}, now="2027-03-06T09:41:00")
    e8 = both("2027-03-06")["8x10"]
    gs = G(sa, "manoj") if sa else (0, "", "")
    P(B + "/owner/settings", "manoj", {"order_days": "10"}, now="2027-03-06T09:42:00")
    check("S688 B4 the owner's setting is the edge: 7.0 days left -- no line under 7 days, a line under 8; his save opens on the Saved card",
          e7 == 0 and e8 == 1 and "msg=saved" in sa and "✓ Saved" in gs[1], (e7, e8, sa))
    # the order page: no supplier number yet, then the owner types it; the WhatsApp link carries clinic, size, 1 box
    s_o, lo, _l = G(B + "/log", "manoj", now="2027-03-06T09:45:00")
    no_num = "Type the films supplier's number" in lo and "wa.me" not in lo
    ph = "98" + "7" * 8
    sc_, _b, lc = P(B + "/owner/contact", "manoj", {"op": "edit", "id": "1", "name": "Nigam", "firm": "Jugnu Medicos (Fuji)", "role": "films_supplier",
                                                     "phone": ph[:5] + " " + ph[5:], "email": ""}, now="2027-03-06T09:46:00")
    gc = G(lc, "manoj") if lc else (0, "", "")
    s_s, ls_, _l = G(B + "/log", "shavez", now="2027-03-06T09:47:00")
    m = re.search(r"href='(https://wa\.me/[^']+)'", ls_)
    wl = m.group(1).replace("&amp;", "&") if m else ""
    check("S688 C1 the order card: before a number 'type the supplier's number'; the owner types it (spaces taken out, Saved card); Shavez's "
          "page then has the WhatsApp button to wa.me/91<number> with the message: the clinic, '8×10', '1 box'; Call and WhatsApp on the contact",
          no_num and "msg=saved" in lc and "✓ Saved" in gc[1] and (sq("SELECT phone FROM xf_contact WHERE id=1") or [("",)])[0][0] == ph
          and wl.startswith("https://wa.me/91" + ph + "?text=") and "8%C3%9710" in wl and "1%20box" in wl and "Dr%20Manoj%20Agarwal%20Clinic" in wl
          and ("tel:+91" + ph) in ls_ and "WhatsApp par order bhejiye" in ls_, (no_num, lc, wl[:40]))
    # +91 only for a ten-digit mobile; a landline (leading 0) and a toll-free (1800) number dialled as typed, no WhatsApp
    land, free = "0581" + "2345678", "1800" + "1234567"
    P(B + "/owner/contact", "manoj", {"op": "add", "name": "W688 Service", "firm": "Fuji", "role": "fuji_service", "phone": land[:4] + "-" + land[4:]},
      now="2027-03-06T09:48:00")
    P(B + "/owner/contact", "manoj", {"op": "add", "name": "W688 Support", "firm": "Fuji", "role": "fuji_support", "phone": free[:4] + " " + free[4:7] + " " + free[7:]},
      now="2027-03-06T09:48:30")
    P(B + "/owner/contact", "manoj", {"op": "add", "name": "W688 Mobile", "firm": "Fuji", "role": "other", "phone": "+91 " + ph},
      now="2027-03-06T09:48:40")
    _s, lt_, _l = G(B + "/log", "shivani", now="2027-03-06T09:49:00")
    P(B + "/owner/contact", "manoj", {"op": "edit", "id": "1", "name": "Nigam", "firm": "Jugnu Medicos (Fuji)", "role": "films_supplier",
                                      "phone": land, "email": ""}, now="2027-03-06T09:49:30")
    _s, ll_, _l = G(B + "/log", "manoj", now="2027-03-06T09:49:40")
    P(B + "/owner/contact", "manoj", {"op": "edit", "id": "1", "name": "Nigam", "firm": "Jugnu Medicos (Fuji)", "role": "films_supplier",
                                      "phone": ph, "email": ""}, now="2027-03-06T09:49:50")
    check("S688 C3 phone links: +91 only before a ten-digit mobile (a mobile typed '+91 ...' kept as its ten digits); a landline with its 0 and "
          "a 1800 number dialled as typed, digits only, with no WhatsApp button; a supplier on a landline: no WhatsApp order, 'call'",
          ("href='tel:%s'" % land) in lt_ and ("href='tel:%s'" % free) in lt_ and ("wa.me/91" + land) not in lt_ and ("wa.me/" + land) not in lt_
          and ("wa.me/91" + free) not in lt_ and ("wa.me/" + free) not in lt_ and lt_.count("href='tel:+91%s'" % ph) == 2
          and (sq("SELECT phone FROM xf_contact WHERE name='W688 Mobile'") or [("",)])[0][0] == ph
          and "not a mobile: no WhatsApp" in ll_ and "?text=" not in ll_, (land in lt_, free in lt_))

    # the spare stock: bills add their boxes, box loads take one off, never below 0; a bill with no size on its lines counts nothing
    def bill(day, sub, item=None, qty=None, made=None):
        bid_ = ac.execute("INSERT INTO bills (vendor, bill_date, created_at, status, subgroup) VALUES ('W688 JUGNU',?,?,'approved',?)",
                          (day, made or (day + " 18:00:00"), sub)).lastrowid
        if item:
            ac.execute("INSERT INTO bill_items (bill_id, item_name, quantity) VALUES (?,?,?)", (bid_, item, qty))
        return bid_
    p0 = both("2027-03-06")["8x10"]
    bill("2027-03-05", "xray_small")
    _s, lo1, _l = G(B + "/log", "manoj", now="2027-03-06T10:00:00")
    pa = both("2027-03-06")["8x10"]
    check("S688 O1 a film bill whose lines name no size (the 'small film' group: 8x10 or 10x12) is 'size unknown': listed beside the order "
          "cards on the owner's page with one-tap 8×10 / 11×14 / not film, counts nothing",
          p0 == 1 and pa == 1 and "FILM BILLS WITH NO SIZE" in lo1 and "size not read" in lo1 and "/owner/billsize" in lo1, (p0, pa))
    bc = bill("2027-03-05", "xray", "FUJI DRY FILM 8X10 150 SHEETS", 1)
    G(B + "/subah", "alisha", now="2027-03-06T10:05:00")
    pc = both("2027-03-06")["8x10"]
    s_s, ls2, _l = G(B + "/log", "shavez", now="2027-03-06T10:06:00")
    ac.execute("UPDATE bills SET status='rejected' WHERE id=?", (bc,))
    G(B + "/log", "manoj", now="2027-03-06T10:07:00")
    pr = both("2027-03-06")["8x10"]
    bill("2027-03-06", "xray", "FUJI DRY FILM 8X10 150 SHEETS", 2)
    G(B + "/log", "manoj", now="2027-03-06T10:08:00")
    p2b = both("2027-03-06")["8x10"]
    check("S688 O2 a 1-box 8x10 bill -> spare 1, the line clears ('1 box rakha hai', 'spare: 1 box'); rejected on the desk, the line is back; "
          "a 2-box bill -> spare 2, clears",
          pc == 0 and "1 box rakha hai" in ls2 and "spare: 1 box" in ls2 and pr == 1 and p2b == 0 and st_of("8x10", "2027-03-06")["spare"] == 2,
          (pc, pr, p2b))
    aid = ac.execute("INSERT INTO assets (name, location_id, purchase_date, vendor, created_at) VALUES ('W688 film', 1, '2027-03-07', 'W688 JUGNU', '2027-03-07 10:00:00')").lastrowid
    ac.execute("INSERT INTO xray_film_line (asset_id, asset_created_at, size, boxes, amount) VALUES (?, '2027-03-07 10:00:00', '11 x 14', 1, 1)", (aid,))
    G(B + "/log", "manoj", now="2027-03-07T10:00:00")
    p4 = both("2027-03-07", "2027-03-07 10:30:00")
    sp4 = st_of("11x14", "2027-03-07")["spare"]
    bill("2027-03-08", "xray", "FUJI DRY FILM 11X14 150 SHEETS", 1)
    G(B + "/log", "manoj", now="2027-03-07T23:00:00")
    p4b = both("2027-03-08", "2027-03-08 08:00:00")["11x14"]
    sp4b = st_of("11x14", "2027-03-08")["spare"]
    check("S688 O3 the spare stock is not floored: the 6-Mar box load leaves 11x14 at -1; a film line dated 7-Mar pays for that box (spare "
          "0) -- the line STAYS; a later 11x14 bill (8-Mar) -> spare 1 -> the line clears",
          p4 == {"8x10": 0, "11x14": 1} and sp4 == 0 and p4b == 0 and sp4b == 1, (p4, sp4, p4b, sp4b))
    rn = P(B + "/subah", "manoj", {"c_8x10": "140", "c_11x14": "130"}, now="2027-03-08T08:58:00")[2]
    P(B + "/subah", "manoj", {"c_8x10": "140", "c_11x14": "130", "note": "W688 box changed"}, now="2027-03-08T09:00:00")
    p8 = both("2027-03-08", "2027-03-08 09:10:00")
    s8, s11 = st_of("8x10", "2027-03-08"), st_of("11x14", "2027-03-08")
    ss = P(B + "/owner/settings", "manoj", {"spare_from": "2027-03-09", "open_11x14": "0"}, now="2027-03-08T09:20:00")[2]
    p8z = both("2027-03-08", "2027-03-08 09:22:00")["11x14"]
    P(B + "/owner/settings", "manoj", {"open_11x14": "1"}, now="2027-03-08T09:24:00")
    p8o, s11o = both("2027-03-08", "2027-03-08 09:25:00")["11x14"], st_of("11x14", "2027-03-08")["spare"]
    P(B + "/owner/settings", "manoj", {"spare_from": "2026-10-31", "open_11x14": "0"}, now="2027-03-08T09:30:00")
    _s, lop1, _l = G(B + "/log", "manoj", now="2027-03-08T09:31:00")
    P(B + "/owner/settings", "manoj", {"open_8x10": "0"}, now="2027-03-08T09:32:00")
    _s, lop2, _l = G(B + "/log", "manoj", now="2027-03-08T09:33:00")
    opn = [tuple(r) for r in sq("SELECT key, value FROM xf_setting WHERE key LIKE 'spare.open.%' ORDER BY id")]
    check("S688 OP2 his first save of an opening figure sets it even when it is 0 (a row of its own); with 11×14 set the warning names 8×10 "
          "only; once he types 8×10's 0 the warning is gone (a save of other settings never sets them)",
          "Opening boxes not set" in lop1 and "8×10: the spare" in lop1 and "Opening boxes not set" not in lop2
          and opn[-1] == ("spare.open.8x10", "0") and ("spare.open.11x14", "0") in opn, (opn,))
    check("S688 SP1 the owner's rise 70 -> 140 without a note refused ('tick it or type a note'), with a note saved (a box load); the 2-box "
          "8x10 bill (6-Mar) less that load -> 1 spare, no line; 11x14 130 (a decline) keeps its 1 spare; from a start day 9-Mar with no "
          "opening stock 11x14 has 0 -> its line (130 left at 17.1 a day); opening stock 1 -> no line",
          "msg=risenote" in rn and s8["spare"] == 1 and s8["loads"] == ["2027-03-08"] and s11["spare"] == 1 and p8 == {"8x10": 0, "11x14": 0}
          and "msg=saved" in ss and p8z == 1 and s11o == 1 and p8o == 0, (rn, s8, s11, p8, p8z, s11o, p8o))
    # above 150 and the 200 sanity: refused for staff, the owner saves (above 150 with a note); his correction makes every figure move
    o1 = P(B + "/subah", "shivani", {"c_8x10": "160", "c_11x14": "128"}, now="2027-03-09T09:00:00")[2]
    o2 = P(B + "/subah", "manoj", {"c_8x10": "300", "c_11x14": "128"}, now="2027-03-09T09:01:00")[2]
    o3 = P(B + "/subah", "manoj", {"c_8x10": "300", "c_11x14": "128", "note": "W688 a trial box"}, now="2027-03-09T09:02:00")[2]
    jq = P(B + "/subah", "shavez", {"c_8x10": "60", "c_11x14": "120", "newbox_11x14": "1"}, now="2027-03-10T09:00:30")[2]
    jo = P(B + "/subah", "shavez", {"c_8x10": "60", "c_11x14": "120", "sure_8x10": "1"}, now="2027-03-10T09:01:00")[2]
    check("S688 J1 above a box's 150: refused for Shivani; the owner without a note refused, with a note saved (300); then 300 -> 60 (a "
          "decline of 240, far above the average) is asked once ('sure', the typed figures and the tick kept in the address) and saved by "
          "Shavez when confirmed (the old 200 rule is gone)",
          "msg=over" in o1 and "msg=note" in o2 and "msg=saved" in o3 and "msg=sure" in jq and "what=8x10" in jq and "v_8x10=60" in jq
          and "nb_11x14=1" in jq and "msg=saved" in jo, (o1, o2, o3, jq, jo))
    a0 = st_of("8x10", "2027-03-10")
    sp0 = safe(lambda: [x["machine"]["8x10"] for x in xf.spans(_con(dbp), __import__("datetime").date(2027, 3, 10))[0][-2:]], [])
    q0 = both("2027-03-10", "2027-03-10 09:30:00")["8x10"]
    eo = P(B + "/owner/count", "manoj", {"day": "2027-03-09", "op": "edit", "c_8x10": "135", "c_11x14": "128"}, now="2027-03-10T09:40:00")[2]
    go = G(eo, "manoj") if eo else (0, "", "")
    a1 = st_of("8x10", "2027-03-10")
    sp1 = safe(lambda: [x["machine"]["8x10"] for x in xf.spans(_con(dbp), __import__("datetime").date(2027, 3, 10))[0][-2:]], [])
    q1 = both("2027-03-10", "2027-03-10 09:45:00")["8x10"]
    rows9 = [r[0] for r in sq("SELECT remaining FROM xf_count WHERE day='2027-03-09' AND size='8x10' ORDER BY id")]
    au = sq("SELECT before_json, after_json FROM audit_log WHERE table_name='xf_save' AND action='count_edit' ORDER BY id DESC LIMIT 1")
    _s, lgap, _l = G(B + "/log", "alisha", now="2027-03-10T09:50:00")
    check("S688 RC1 the owner corrects 9-Mar from 300 to 135: append-only (both rows kept), audited old and new; everything moves -- 8-Mar->9-Mar "
          "used 0 (a 'box load') becomes 5, 9-Mar->10-Mar 240 becomes 75 (the gap with it), the 30-day average 370/9 becomes 210/9, the box "
          "load of 9-Mar goes so the spare goes 0 -> 1, and the 8x10 line clears",
          "msg=saved" in eo and "Morning count correction" in go[1] and rows9 == [300, 135] and au and '"8x10": 300' in str(au[0][0])
          and '"8x10": 135' in str(au[0][1]) and sp0 == [0, 240] and sp1 == [5, 75] and abs((a0["avg"] or 0) - 370 / 9.0) < 1e-9
          and abs((a1["avg"] or 0) - 210 / 9.0) < 1e-9 and a0["spare"] == 0 and a1["spare"] == 1 and a0["loads"] == ["2027-03-08", "2027-03-09"]
          and a1["loads"] == ["2027-03-08"] and q0 == 1 and q1 == 0 and "8×10 +75" in lgap, (sp0, sp1, a0, a1, q0, q1, rows9))
    ag = [x for x in agree if x[2] != (1 if x[3] is True else 0 if x[3] is False else "x")]
    check("S688 O6 at every step the order duty's SQL and the module's own rule agree (%d readings)" % len(agree), agree and not ag, ag[:4])
    # the owner's film-size change moves the slips' films
    P(B + "/owner/study", "manoj", {"service_id": str(s_ls), "size": "11x14", "films": "2", "both_one": "0"}, now="2027-03-10T09:50:00")
    sp2 = safe(lambda: xf.slip_films(_con(dbp), "2027-03-02", "2027-03-02"), {})
    P(B + "/owner/study", "manoj", {"service_id": str(s_ls), "size": "8x10", "films": "1", "both_one": "0"}, now="2027-03-10T09:51:00")
    check("S688 O7 the owner's change of a study's film size moves that day's slip films (2-Mar: two LS slips -> 11x14 x 2 each = 4)",
          sp2.get("11x14") == 4 and sp2.get("8x10") == 0, sp2)

    def films10():
        return {(e["study"], e["side"]): e["films"] for e in xf.slip_lines(_con(dbp), "2027-03-12", "2027-03-12")}
    f0 = safe(films10, {})
    P(B + "/owner/study", "manoj", {"service_id": str(s_knee), "size": "8x10", "films": "1", "both_one": "1"}, now="2027-03-10T09:52:00")
    f1 = safe(films10, {})
    P(B + "/owner/study", "manoj", {"service_id": str(s_knee), "size": "8x10", "films": "1", "both_one": "0"}, now="2027-03-10T09:53:00")
    kn, bk, ls_n, ks = "Knee AP & Lateral view", "Both knees AP standing view", "Lumbosacral spine AP & Lateral view", "Knee studies (K/S) AP & Lateral view"
    check("S688 SD1 side B (both sides): knee AP & lateral B = 2 films, K/S B = 4; 'Both knees AP standing' B stays 1 (a 'Both' study never "
          "doubles); LS side L = 1; the owner marks knee 'both sides on one film' -> knee B = 1",
          f0 == {(kn, "B"): 2, (bk, "B"): 1, (ls_n, "L"): 1, (ks, "B"): 4} and f1.get((kn, "B")) == 1 and f1.get((ks, "B")) == 4, (f0, f1))

    # ---- 7 the X-ray list from 1-Oct, the Excel files
    s_l, ll, _l = G(B + "/list?m=2026-10", "shavez", now="2027-03-10T10:00:00")
    s_n, ln_, _l = G(B + "/list?m=2027-03", "manoj", now="2027-03-10T10:00:00")
    s9, _b, l9 = G(B + "/list?m=2026-09", "shavez", now="2027-03-10T10:00:00")
    rows_oct = len(re.findall(r"<tr><td>\d\d-Oct</td>", ll))
    check("S688 X1 the X-ray list: October's page has one row per paid X-ray line of the slip book (%d), each with date, slip no., clinic ID, "
          "patient, study, film, films, paid; March 2027's has the made-up slips with K/S 2 films and 'size not set'; September (before 1-Oct) is "
          "refused" % oct_lines,
          s_l == 200 and rows_oct == oct_lines and s_n == 200 and "W688 PATIENT 900001" in ln_ and "Knee studies (K/S) AP &amp; Lateral view</td><td>8×10</td><td class='r'>2</td>" in ln_
          and "size not set" in ln_ and "W688 PATIENT 900005" not in ln_ and "W688 PATIENT 900006" not in ln_ and s9 == 302 and "msg=bad" in l9,
          (rows_oct, oct_lines, s9))
    xl = {}
    for path, u in ((B + "/log.xlsx?m=2027-03", "alisha"), (B + "/list.xlsx?m=2027-03", "manoj"), (B + "/list.xlsx?m=2026-10", "shivani")):
        st_, data, _l, r = req("GET", path, u, now="2027-03-10T10:05:00")
        try:
            z = zipfile.ZipFile(io.BytesIO(data))
            s1 = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
            ok = (st_ == 200 and z.testzip() is None and "xl/workbook.xml" in z.namelist() and "[Content_Types].xml" in z.namelist()
                  and r.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            xl[path] = (ok, s1)
        except Exception as e:                                         # noqa: BLE001
            xl[path] = (False, str(e)[:80])
    lx, li, lo_ = xl[B + "/log.xlsx?m=2027-03"], xl[B + "/list.xlsx?m=2027-03"], xl[B + "/list.xlsx?m=2026-10"]
    check("S688 X2 the Excel downloads are real .xlsx (a zip with the workbook and the sheet XML): the month's log (the joined day, the box "
          "loads) and the X-ray list (March's made-up slips; October's %d lines)" % oct_lines,
          lx[0] and li[0] and lo_[0] and "joined to the next count" in lx[1] and "naya box (machine se pata chala)" in lx[1] and "W688 PATIENT 900003" in li[1]
          and lo_[1].count("<row ") == oct_lines + 2, (lx[0], li[0], lo_[0], lo_[1].count("<row ") if lo_[0] else lo_[1]))

    # the owner voids a morning: the old rows stay, the day reads as not counted, its count line is due again; then he un-voids it
    nv = n_of("xf_count")
    vo = P(B + "/owner/count", "manoj", {"day": "2027-03-10", "op": "void"}, now="2027-03-10T10:10:00")[2]
    rd10 = [r["day"] for r in safe(lambda: xf.readings(_con(dbp), "8x10", "2027-03-10"), [])]
    dv = due("reception.xray_film_count", "2027-03-10 10:15:00")
    _s, sv10, _l = G(B + "/subah", "alisha", now="2027-03-10T10:16:00")
    check("S688 V1 the owner voids 10-Mar's count: two rows added (nothing deleted), 10-Mar no longer a reading, the field empty again and "
          "Reception's count line due again",
          "msg=saved" in vo and n_of("xf_count") == nv + 2 and "2027-03-10" not in rd10 and "2027-03-09" in rd10 and dv == (1, "2027-03-10")
          and "Aaj ki ginti ho gayi" not in sv10, (vo, rd10[-2:], dv))
    nu = n_of("xf_count")
    uo = P(B + "/owner/count", "manoj", {"day": "2027-03-10", "op": "unvoid"}, now="2027-03-10T10:20:00")[2]
    ux = P(B + "/owner/count", "manoj", {"day": "2027-03-06", "op": "unvoid"}, now="2027-03-10T10:21:00")[2]
    rd10b = [(r["day"], r["left"]) for r in safe(lambda: xf.readings(_con(dbp), "8x10", "2027-03-10"), [])]
    au2 = sq("SELECT 1 FROM audit_log WHERE table_name='xf_save' AND action='count_unvoid'")
    check("S688 V2 the owner un-voids 10-Mar: two rows added, 10-Mar reads 60 again, the count line not due, audited; un-voiding a day "
          "that is not voided is refused",
          "msg=saved" in uo and "msg=notvoid" in ux and n_of("xf_count") == nu + 2 and rd10b[-1:] == [("2027-03-10", 60)]
          and due("reception.xray_film_count", "2027-03-10 10:25:00") == (0,) and len(au2) == 1, (uo, ux, rd10b[-1:]))
    # the owner says what a size-unknown film bill is: one tap, audited; it then counts (or, 'not film', never)
    src_a = (sq("SELECT src FROM xf_purchase WHERE gone_at='' AND size=''") or [("",)])[0][0]
    spa0 = st_of("8x10", "2027-03-10")["spare"]
    bs0 = P(B + "/owner/billsize", "shavez", {"src": src_a, "size": "8x10"}, now="2027-03-10T10:30:00")[0]
    bs1 = P(B + "/owner/billsize", "manoj", {"src": src_a, "size": "8x10"}, now="2027-03-10T10:31:00")[2]
    spa1 = st_of("8x10", "2027-03-10")["spare"]
    bill("2027-03-10", "xray")
    G(B + "/log", "manoj", now="2027-03-10T10:32:00")
    src_b = (sq("SELECT src FROM xf_purchase WHERE gone_at='' AND size=''") or [("",)])[0][0]
    P(B + "/owner/billsize", "manoj", {"src": src_b, "size": "none"}, now="2027-03-10T10:33:00")
    _s, lbs, _l = G(B + "/log", "manoj", now="2027-03-10T10:34:00")
    check("S688 BS1 the owner taps '8×10' on the size-unknown bill (staff 403): kept, audited, the 8x10 spare goes up by its box (1 -> 2); a "
          "second one tapped 'not film' counts nowhere; the list of bills with no size is then empty",
          bs0 == 403 and "msg=saved" in bs1 and spa0 == 1 and spa1 == 2 and src_a and src_b and src_a != src_b
          and [tuple(r) for r in sq("SELECT size FROM xf_purchase WHERE src IN (?, ?) ORDER BY src = ?", (src_a, src_b, src_b))] == [("8x10",), ("none",)]
          and len(sq("SELECT 1 FROM audit_log WHERE table_name='xf_bill_size'")) == 2 and "FILM BILLS WITH NO SIZE" not in lbs, (bs0, bs1, spa0, spa1))
    # a film bill read as more than 10 boxes (a sheet count?) is HELD -- not counted -- until the owner confirms or corrects it
    spq0, spr0 = st_of("8x10", "2027-03-10")["spare"], st_of("11x14", "2027-03-10")["spare"]
    bq8 = bill("2027-03-10", "xray", "FUJI DRY FILM 8X10 150 SHEETS", 12)
    bq11 = bill("2027-03-10", "xray", "FUJI DRY FILM 11X14 150 SHEETS", 20)
    _s, lq, _l = G(B + "/log", "manoj", now="2027-03-10T10:35:00")
    hq = lambda b_: [tuple(r) for r in sq("SELECT held, boxes FROM xf_purchase WHERE src LIKE ?", ("bill:%d:%%" % b_,))]    # noqa: E731
    h0 = (hq(bq8), hq(bq11))
    spq1, spr1 = st_of("8x10", "2027-03-10")["spare"], st_of("11x14", "2027-03-10")["spare"]
    src8 = (sq("SELECT src FROM xf_purchase WHERE src LIKE ?", ("bill:%d:%%" % bq8,)) or [("",)])[0][0]
    src11 = (sq("SELECT src FROM xf_purchase WHERE src LIKE ?", ("bill:%d:%%" % bq11,)) or [("",)])[0][0]
    qs = P(B + "/owner/billqty", "shavez", {"src": src8, "op": "fix", "boxes": "1"}, now="2027-03-10T10:36:00")[0]
    qf = P(B + "/owner/billqty", "manoj", {"src": src8, "op": "fix", "boxes": "1"}, now="2027-03-10T10:37:00")[2]
    qc = P(B + "/owner/billqty", "manoj", {"src": src11, "op": "confirm"}, now="2027-03-10T10:38:00")[2]
    _s, lq2, _l = G(B + "/log", "manoj", now="2027-03-10T10:39:00")
    spq2, spr2 = st_of("8x10", "2027-03-10")["spare"], st_of("11x14", "2027-03-10")["spare"]
    check("S688 QT1 film bills read as 12 and 20 boxes (over 10) are held: listed under 'FILM BILLS: CHECK QUANTITY' with confirm / correct, "
          "the spare stock unchanged; staff 403; the owner corrects the 8x10 to 1 (spare +1) and confirms the 11x14's 20 (spare +20), both "
          "audited; the list then empty",
          h0 == ([(1, 12.0)], [(1, 20.0)]) and spq1 == spq0 and spr1 == spr0 and "FILM BILLS: CHECK QUANTITY" in lq and "/owner/billqty" in lq
          and qs == 403 and "msg=saved" in qf and "msg=saved" in qc and hq(bq8) == [(0, 1.0)] and hq(bq11) == [(0, 20.0)]
          and spq2 == spq0 + 1 and spr2 == spr0 + 20 and len(sq("SELECT 1 FROM audit_log WHERE table_name='xf_bill_qty'")) == 2
          and "FILM BILLS: CHECK QUANTITY" not in lq2, (h0, spq0, spq1, spq2, spr0, spr1, spr2, qs, qf, qc))
    # a late count (a stand-in after 11:00): the span ending at it and the next span shown as ONE, never two misleading gaps
    lc0 = P(B + "/subah", "shavez", {"c_8x10": "55", "c_11x14": "118"}, now="2027-03-11T11:30:00")[2]
    _s, pc0, _l = G(lc0, "shavez", now="2027-03-11T11:30:30") if lc0 else (0, "", "")
    _s, sc0, _l = G(B + "/subah", "alisha", now="2027-03-11T11:40:00")
    _s, lgc0, _l = G(B + "/log?m=2027-03", "alisha", now="2027-03-11T11:41:00")
    _s, ogc0, _l = G(B + "/log?m=2027-03", "manoj", now="2027-03-11T11:42:00")
    r10 = [r_ for r_ in re.findall(r"<tr[^>]*>.*?</tr>", lgc0) if re.match(r"<tr[^>]*><td>[^<]*10-Mar", r_)]
    pend = "der se ginti — kal ki ginti ke saath judegi"
    check("S688 LC0 the newest late count (11-Mar 11:30) before the next count: staff see '%s' on the Saved card, the morning page and the "
          "10-Mar row -- no gap, no 'kal lagi', not in the gap days; the owner sees the figures with 'late count — joins the next count'" % pend,
          pend in pc0 and "kal lagi" not in pc0 and pend in sc0 and "film ka farq" not in sc0 and "koi farq nahi" not in sc0
          and len(r10) == 1 and pend in r10[0] and "gapc" not in r10[0] and "late count — joins the next count" in ogc0, (len(r10), r10[:1]))
    P(B + "/subah", "alisha", {"c_8x10": "18", "c_11x14": "115"}, now="2027-03-12T09:00:00")
    _s, llc, _l = G(B + "/log?m=2027-03", "alisha", now="2027-03-12T09:10:00")
    _s, olc, _l = G(B + "/log?m=2027-03", "manoj", now="2027-03-12T09:11:00")
    ml_ = safe(lambda: xf.month_log(_con(dbp), "2027-03", __import__("datetime").date(2027, 3, 12)), {})
    rws = [(r["day"], r["kind"], r["s"]["p"] if r.get("s") else None, r["s"].get("late") if r.get("s") else None,
            r["s"]["machine"]["8x10"] if r.get("s") else None) for r in (ml_.get("rows") or []) if r["day"] in ("2027-03-10", "2027-03-11")]
    check("S688 LC1 a late count (11-Mar at 11:30, Shavez standing in): 10-Mar and 11-Mar shown as ONE span -- 8x10 60 -> 18 = 42 used, 11x14 "
          "5 -- labelled 'der se ginti — do din milake' (owner: 'late count — two days combined'); 10-Mar reads 'joined', no second gap",
          rws == [("2027-03-11", "span", "2027-03-10", True, 42), ("2027-03-10", "joined", "2027-03-10", True, 42)]
          and "der se ginti — do din milake" in llc and "late count — two days combined" in olc, rws)

    # a film bill kept on a machine record that is also on the desk counts once (xray_costs' match: the record's bill link, or
    # the same supplier, date and amount)
    P(B + "/owner/settings", "manoj", {"spare_from": "2027-03-11"}, now="2027-03-12T09:00:00")
    d1 = ac.execute("INSERT INTO bills (vendor, bill_date, created_at, status, subgroup, total_amount) VALUES "
                    "('W688 JUGNU MEDICOS','2027-03-12','2027-03-12 18:00:00','approved','xray_11x14',5000)").lastrowid
    a1_ = ac.execute("INSERT INTO assets (name, location_id, purchase_date, vendor, created_at) VALUES ('W688 film A', 1, '2027-03-12', 'W688 Jugnu', '2027-03-12 19:00:00')").lastrowid
    ac.execute("INSERT INTO xray_film_line (asset_id, asset_created_at, size, boxes, amount) VALUES (?, '2027-03-12 19:00:00', '11x14', 1, 5000)", (a1_,))
    d2 = ac.execute("INSERT INTO bills (vendor, bill_date, created_at, status, subgroup, total_amount) VALUES "
                    "('W688 OTHER','2027-03-12','2027-03-12 18:30:00','approved','xray_11x14',7000)").lastrowid
    a2_ = ac.execute("INSERT INTO assets (name, location_id, purchase_date, vendor, created_at, bill_id) VALUES ('W688 film B', 1, '2027-03-13', 'W688 Elsewhere', '2027-03-13 10:00:00', ?)", (d2,)).lastrowid
    ac.execute("INSERT INTO xray_film_line (asset_id, asset_created_at, size, boxes, amount) VALUES (?, '2027-03-13 10:00:00', '11 x 14', 1, 6500)", (a2_,))
    a3_ = ac.execute("INSERT INTO assets (name, location_id, purchase_date, vendor, created_at) VALUES ('W688 film C', 1, '2027-03-13', 'W688 Elsewhere', '2027-03-13 11:00:00')").lastrowid
    ac.execute("INSERT INTO xray_film_line (asset_id, asset_created_at, size, boxes, amount) VALUES (?, '2027-03-13 11:00:00', '11 x 14', 1, 4000)", (a3_,))
    G(B + "/log", "manoj", now="2027-03-13T12:00:00")
    sp11d = st_of("11x14", "2027-03-13")["spare"]
    srcs = sorted(r[0].split(":")[0] for r in sq("SELECT src FROM xf_purchase WHERE gone_at='' AND size='11x14' AND bill_day >= '2027-03-12'"))
    check("S688 DD1 a film bill on a machine record that is also on the desk counts once: same supplier, date and amount -> the desk's "
          "only; the record's own bill link -> the desk's only; a record with no twin counts: 11x14 spare 3 (two desk bills + one record), not 5",
          sp11d == 3 and srcs == ["bill", "bill", "line"] and d1 and a3_, (sp11d, srcs))
    # a box load across more than 3 uncounted days (12-Mar -> 17-Mar): 'check' on the owner's page -- two boxes could have gone in
    ck = P(B + "/subah", "alisha", {"c_8x10": "145", "c_11x14": "110", "newbox_8x10": "1"}, now="2027-03-17T09:00:00")[2]
    _s, ock, _l = G(B + "/log?m=2027-03", "manoj", now="2027-03-17T09:10:00")
    _s, sck, _l = G(B + "/log?m=2027-03", "alisha", now="2027-03-17T09:11:00")
    check("S688 CK1 18 -> 145 ticked after 5 uncounted days: a box load, and the owner's page says 'check: several days uncounted — the films "
          "used may be off by a box' (on the row and in NEW BOXES LOADED); the staff page does not",
          "msg=saved" in ck and ock.count("check: several days uncounted — the films used may be off by a box") >= 2
          and "check: several days uncounted" not in sck, ck)

    # random states (as the reviewer sampled them): the order duty's own SQL against the module's rule, on a scratch database --
    # films left, the 30-day average, the spare stock and the line itself, for 300 made-up histories of figures, voids and bills
    import datetime as _dt
    import random
    rng = random.Random(688)
    mem = sqlite3.connect(":memory:")
    mem.row_factory = sqlite3.Row
    bad_rs = []
    try:
        mem.executescript(xf.SCHEMA)
        for it in range(300):
            for tb in ("xf_count", "xf_save", "xf_purchase", "xf_setting"):
                mem.execute("DELETE FROM %s" % tb)
            base = _dt.date(2027, 4, 1)
            mem.execute("INSERT INTO xf_setting (key, value, set_at, set_by) VALUES ('order.days', ?, 'x', 'w')", (str(rng.randint(3, 15)),))
            mem.execute("INSERT INTO xf_setting (key, value, set_at, set_by) VALUES ('spare.from', ?, 'x', 'w')",
                        ((base + _dt.timedelta(days=rng.randint(-3, 12))).isoformat(),))
            for sz in ("8x10", "11x14"):
                if rng.random() < 0.6:
                    mem.execute("INSERT INTO xf_setting (key, value, set_at, set_by) VALUES (?, ?, 'x', 'w')", ("spare.open." + sz, str(rng.randint(0, 2))))
                v = rng.randint(0, 150)
                for dd in range(26):
                    if rng.random() < 0.7:
                        v = rng.randint(v, 150) if rng.random() < 0.15 else max(0, v - rng.randint(0, 25))
                        day = (base + _dt.timedelta(days=dd)).isoformat()
                        mem.execute("INSERT INTO xf_count (save_id, day, size, remaining, saved_at, saved_by, void) VALUES (0,?,?,?,?, 'w', ?)",
                                    (day, sz, v, day + " 09:00:00", 1 if rng.random() < 0.06 else 0))
                        if rng.random() < 0.08:
                            mem.execute("INSERT INTO xf_count (save_id, day, size, remaining, saved_at, saved_by, void) VALUES (0,?,?,?,?, 'w', 0)",
                                        (day, sz, rng.randint(0, 150), day + " 15:00:00"))
            for bn in range(rng.randint(0, 4)):
                bd_ = (base + _dt.timedelta(days=rng.randint(-2, 26))).isoformat()
                mem.execute("INSERT INTO xf_purchase (src, size, bill_day, boxes, vendor, seen_at, gone_at, held) VALUES (?,?,?,?, '', 'x', ?, ?)",
                            ("w%d:%d" % (it, bn), rng.choice(("8x10", "11x14", "")), bd_, rng.choice((None, 1, 2, 3, 12)), "" if rng.random() < 0.85 else "g",
                             1 if rng.random() < 0.2 else 0))
            today_ = base + _dt.timedelta(days=rng.randint(2, 30))
            for sz in ("8x10", "11x14"):
                q_ = extra["shavez.xray_film_order_" + sz]["sql"].replace(NOW, "'%s 10:00:00'" % today_)
                n_ = mem.execute(q_).fetchone()[0]
                probe = q_.rsplit("SELECT CASE WHEN EXISTS (SELECT 1 FROM lt)", 1)[0] + "SELECT (SELECT r FROM lt), (SELECT a FROM av), (SELECT n FROM sp)"
                r_, a_, s_ = mem.execute(probe).fetchone()
                stt = xf.size_state(mem, sz, today_)
                same = (n_ == (1 if stt["due"] else 0) and (r_ is None) == (stt["left"] is None) and (r_ is None or float(r_) == stt["left"])
                        and (a_ is None) == (stt["avg"] is None) and (a_ is None or abs(a_ - stt["avg"]) < 1e-9) and float(s_) == stt["spare"])
                if not same:
                    bad_rs.append((it, sz, n_, stt["due"], r_, stt["left"], a_, stt["avg"], s_, stt["spare"]))
    except Exception as e:                                             # noqa: BLE001
        bad_rs.append(("ERR", type(e).__name__, str(e)[:120]))
    finally:
        mem.close()
    check("S688 RS1 300 random histories (rises, declines, voids, same-day re-saves, bills of 0-3 boxes, gone bills, opening stock, start "
          "days, bills held for their quantity): the order duty's SQL and the module agree on films left, the average, the spare stock and the line, every one",
          not bad_rs, bad_rs[:3])

    # ---- 8 the words, the URLs, the tables
    jp = "".join(p for p in pages if isinstance(p, str))
    jst = "".join(staff_pages)
    check("S688 W1 the staff pages are Roman Hinglish ('Machine ki screen par jitni film bachi dikh rahi hain, wahi likhiye'; the count before "
          "the first X-ray); the owner's pages English; no counter and no box tap anywhere", "Subah ki ginti" in jst
          and "Machine mein kitni film bachi hain" in jst and "Morning count" in jp
          and "Ginti subah pehla X-ray hone se pehle kijiye" in jst and "Machine ki screen par jitni film bachi dikh rahi hain, wahi likhiye." in jst
          and "counter" not in jp.lower() and "Naya box lagaya" not in jp and "/film/box" not in jp)
    bad_urls = [u for u in urls if TEN.search(u) or not re.match(r"^/portal$|^/finance/(slips/film|aaj)[A-Za-z0-9/_.\-]*(\?((m|msg|id|what|as|v_8x10|v_11x14|nb_8x10|nb_11x14)=[A-Za-z0-9_.\-]*&?)*)?$", u)]
    hrefs = re.findall(r"(?:href|action)='([^']*)'", jp)
    bad_h = [h for h in hrefs if TEN.search(h) and not re.match(r"^(tel:|https://wa\.me/)", h)]
    check("S688 W2 no ten-digit number in any URL, redirect or form action (only m, msg, id, what -- and the confirm's typed films-left figures -- in a query); the phone number only in the "
          "tel: and wa.me links", not bad_urls and not bad_h and any(h.startswith("tel:+") for h in hrefs), (bad_urls[:4], bad_h[:4]))
    schema1 = {r[0]: r[1] for r in raw.execute("SELECT name, sql FROM sqlite_master WHERE name NOT LIKE 'xf\\_%' ESCAPE '\\' AND sql IS NOT NULL")}
    newt = sorted(r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'") if r[0] not in schema0 and not r[0].startswith("xf_"))
    for sid in made:
        raw.execute("DELETE FROM slip_item WHERE slip_id=?", (sid,))
        raw.execute("DELETE FROM slip WHERE id=?", (sid,))
    sums1 = raw.execute("SELECT COUNT(*), COALESCE(SUM(id*3+slip_no),0) FROM slip").fetchone()[:]
    check("S688 W3 additive only: no existing table changed, every new table xf_*; the slip book unchanged by the pages (the walk's own "
          "made-up slips taken out, the rest as it was)", schema1 == schema0 and not newt and tuple(sums1) == tuple(sums0), (newt, sums0, sums1))
    big = re.findall(r"min-height:(\d+)px", jp)
    check("S688 W4 touch targets: every button, field and link of the pages at least 44 px", big and min(int(x) for x in big) >= 44, sorted(set(big)))
    write_duties()
    check("S688 W5 on today's real clock every list reads whole (unread 0: reception, shavez, darpan, everyone)",
          all(safe(lambda k=k: unread(k), -1) == 0 for k in ("reception", "shavez", "darpan", "amir", "bhati", "sukhveer")))

    # ---- 9 the data step on saved panels (its own copy)
    cdb = os.path.join(scr, "cfg.db")
    copydb(dbp, cdb)
    cc = sqlite3.connect(cdb)
    cc.execute("CREATE TABLE IF NOT EXISTS aaj_cfg (person TEXT PRIMARY KEY, doc TEXT NOT NULL, edited_at TEXT NOT NULL, edited_by TEXT NOT NULL)")
    for person in ("shavez", "reception"):
        sd = next(p for p in aaj_seed.PEOPLE if p["key"] == person)
        old_lines = [dict(id=x["id"], hi=x["hi"], en=x.get("en", ""), when=x["when"], on=x["on"]) for x in sd["lines"] if x["id"] not in IDS]
        removed = [dict(id="shavez.xray_film_count", hi="x", en="", when="day", on=False)] if person == "shavez" else []
        if person == "reception":
            old_lines.insert(3, dict(id=RETIRED, hi="X-ray film ka stock giniye (dono size)", en="X-ray film stock counted, both sizes.",
                                     when="week", on=True))
        doc = dict(on=True, note="", first_on=None, lines=old_lines, removed=removed)
        cc.execute("INSERT OR REPLACE INTO aaj_cfg VALUES (?, ?, '2026-10-30T10:00:00', 'manoj')", (person, json.dumps(doc)))
    cc.commit()
    cc.close()

    def merged():
        con_ = sqlite3.connect("file:%s?mode=ro" % cdb, uri=True)
        try:
            ps = aaj_kaam.cfg_load(con_)[0]
            return {ln["id"]: bool(ln["on"]) for k in ("shavez", "reception") for ln in ps[k]["lines"] if ln["id"] in IDS}
        finally:
            con_.close()
    def docs():
        con_ = sqlite3.connect(cdb)
        try:
            return {k: json.loads(d) for k, d in con_.execute("SELECT person, doc FROM aaj_cfg WHERE person IN ('shavez','reception')")}
        finally:
            con_.close()
    rec = os.path.join(scr, "cfg_rec.json")
    d0 = safe(docs, {})
    m0 = safe(merged, {})
    r1 = safe(lambda: cfg_s688.panel(cdb, rec), "ERR")
    m1 = safe(merged, {})
    d1 = safe(docs, {})
    rj = safe(lambda: json.load(open(rec)), {})
    u1 = safe(lambda: cfg_s688.undo(cdb, rec), "ERR")
    d2 = safe(docs, {})
    safe(lambda: cfg_s688.panel(cdb), "ERR")
    r2 = safe(lambda: cfg_s688.panel(cdb), "ERR")
    on3 = {"reception.xray_film_count", "shavez.xray_film_order_8x10", "shavez.xray_film_order_11x14"}
    check("S688 C2 saved panels: before the data step the new lines would show OFF (new); the step puts them ON (3 changed), the line the "
          "owner took off (Shavez's stand-in) stays off; a second run changes nothing",
          m0 == {i: False for i in on3} and str(r1).endswith("3 changed") and m1 == {i: True for i in on3} and str(r2).endswith("0 changed"),
          (m0, r1, m1, r2))
    keep_ = lambda d, k: [x for x in d.get(k, {}).get("lines", []) if x["id"] not in IDS and x["id"] != RETIRED]    # noqa: E731
    check("S688 C3 the retired line on a saved panel: the data step takes it off (every other line as it was, in order) and records it; "
          "the red install's undo takes the added lines off and puts it back exactly where it was",
          isinstance(d1, dict) and d1 and not [x for x in d1["reception"]["lines"] if x["id"] == RETIRED]
          and keep_(d1, "reception") == keep_(d0, "reception") and keep_(d1, "shavez") == keep_(d0, "shavez")
          and rj.get("retired", {}).get("reception", [[None]])[0][:2] == ["lines", 3] and sorted(rj.get("added", {})) == ["reception", "shavez"]
          and "1 put back" in str(u1) and d2 and d2["reception"]["lines"] == d0["reception"]["lines"] and d2["shavez"]["lines"] == d0["shavez"]["lines"]
          and d2["shavez"]["removed"] == d0["shavez"]["removed"], (u1, rj.get("retired")))
    os.remove(cdb)
    ac.close()
    red = sum(1 for r in results if not r[1])
    print("INNER %d red . %d green" % (red, len(results) - red))
    return 0


def mj_tables(dbp, fin):
    """S687's mj_* tables, as its installer's data step made them on the box (the 31-Oct copy predates S687's install)."""
    p = os.path.join(fin, "month_jobs.py")
    if not os.path.isfile(p):
        return
    import importlib.util                                              # noqa: PLC0415
    spec = importlib.util.spec_from_file_location("month_jobs_s688_walk", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    con = sqlite3.connect(dbp, timeout=60)
    try:
        m.ensure(con)
    finally:
        con.close()


def _con(p):
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    return con


# ================================================================================================ every person's list (for old = new)
def dump(a):
    fin, dbp = os.path.abspath(a.dump), os.path.abspath(a.db)
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="")
    os.environ.pop("AAJ_DUTIES_JSON", None)
    mj_tables(dbp, fin)
    if a.kit and os.path.isfile(os.path.join(fin, "xray_film.py")):
        sys.path.insert(0, fin)
        sys.path.insert(1, os.path.abspath(a.kit))
        import cfg_s688                                                # noqa: E402
        cfg_s688.tables(dbp, fin)                                      # as the installer's data step does before the restart
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                           # noqa: E402
    import aaj_kaam                                                    # noqa: E402
    import aaj_seed                                                    # noqa: E402
    c = fa.app.test_client(use_cookies=False)
    out = {"mount_failed": [n for n, _w in fa._MOUNT_FAILED], "lists": {}, "unread": {}, "own": {}}
    for p in aaj_seed.PEOPLE:
        r = c.get("/finance/aaj/api/list?as=%s" % p["key"], headers={"X-Clinic-User": "manoj"})
        j = r.get_json(silent=True) or {}
        out["lists"][p["key"]] = [(s["key"], x["id"], x["kind"], x["text"], x.get("door")) for s in (j.get("sections") or []) for x in s["rows"]]
    for login in ("alisha", "shivani", "shavez", "bhati", "darpan", "amir", "sukhveer"):
        r = c.get("/finance/aaj/api/list", headers={"X-Clinic-User": login})
        j = r.get_json(silent=True) or {}
        out["own"][login] = (r.status_code, j.get("partial"), [(s["key"], x["id"]) for s in (j.get("sections") or []) for x in s["rows"]])
    rd = aaj_kaam.Reader(dbp)
    try:
        for k, doc in rd.people.items():
            out["unread"][k] = aaj_kaam.person_list(rd, doc)["unread"]
    finally:
        rd.close()
    out["console"] = sorted(str(i.get("id")) for i in aaj_kaam.build_all(dbp)["items"] if isinstance(i, dict))
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return 0


# ================================================================================================ the outer walk
def run_inner(fin, db, scr, kit, tag, script=None, ok_re=r"^INNER (\d+) red \. (\d+) green$"):
    shutil.rmtree(scr, ignore_errors=True)
    os.makedirs(scr)
    wdb = os.path.join(scr, "inner.db")
    copydb(db, wdb)
    p = subprocess.run([sys.executable, "-B", script or os.path.abspath(__file__), "--inner", fin, "--db", wdb, "--scratch", scr, "--kit", kit],
                       cwd="/tmp", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    outp = p.stdout.decode("utf-8", "replace")
    for f in (wdb, wdb + "-journal", wdb + "-wal", wdb + "-shm"):
        if os.path.exists(f):
            os.remove(f)
    shutil.rmtree(scr, ignore_errors=True)
    m = re.search(ok_re, outp, re.M)
    return (int(m.group(1)), int(m.group(2))) if m else None, outp


def mkfin(src, dst, over=None):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.db", "*.db-*", "*.bak*", "__pycache__", "*uploads*", "*.gz", "*.tar"))
    for f, b in (over or {}).items():
        with open(os.path.join(dst, f), "wb") as fh:
            fh.write(b)


MUTANTS = [
    ("X1", "the count line due on a Sunday", "aaj_duties.json", "reception.xray_film_count", "AND strftime('%w', (SELECT day FROM d)) <> '0' ", ""),
    ("X2", "Shavez's stand-in without its 11:00", "aaj_duties.json", "shavez.xray_film_count",
     "AND time((SELECT ts FROM t)) >= COALESCE((SELECT s.value FROM xf_setting s WHERE s.key = 'standin.after' AND s.value <> '' ORDER BY s.id DESC LIMIT 1), '11:00') ", ""),
    ("X3", "the 8x10 order line blind to the spare stock", "aaj_duties.json", "shavez.xray_film_order_8x10", "AND (SELECT n FROM sp) <= 0 ", ""),
    ("X4", "the duty: a box load not taken off the spare stock", "aaj_duties.json", "shavez.xray_film_order_8x10",
     "- (SELECT COUNT(*) FROM u WHERE u.ld = 1", "- 0 * (SELECT COUNT(*) FROM u WHERE u.ld = 1"),
    ("X5", "the module: the films used on a box load taken as 0", "xray_film.py", None, "            used = max(0, prev + pb - v)", "            used = 0"),
    ("X6", "Knee studies (K/S) one film", "xray_film.py", None, '        return "8x10", 2\n', '        return "8x10", 1\n'),
    ("X7", "a study with no size guessed as 8x10", "xray_film.py", None, '    return "", 1\n\n\ndef ensure', '    return "8x10", 1\n\n\ndef ensure'),
    ("X8", "the gap hidden from staff", "xray_film.py", None, '    if not parts:\n        return "<span', '    if not parts or lang == "hi":\n        return "<span'),
    ("X9", "staff allowed to change contacts", "xray_film.py", None, "    return u if own else None\n", "    return u\n"),
    ("X10", "no Saved card after a save", "xray_film.py", None, 'head = "✓ Saved — सेव हो गया" if lang == "hi" else "✓ Saved"', 'head = "OK"'),
    ("X11", "staff allowed a figure above a box's 150", "xray_film.py", None, '            if not own:\n                return None, "over"',
     '            if False:\n                return None, "over"'),
    ("X12", "the average over the last 3 days, not 30", "aaj_duties.json", "shavez.xray_film_order_8x10", "'-30 days'", "'-3 days'"),
    ("X13", "the duty: the films used on a box load taken as 0", "aaj_duties.json", "shavez.xray_film_order_8x10",
     "ELSE MAX(0, LAG(r) OVER (ORDER BY day) + (SELECT pb FROM cfg) - r) END", "ELSE 0 END"),
    ("X14", "a phone number put in the page's URL", "xray_film.py", None,
     '    _audit_safe(con, "xf_contact", cid, op,', '    return redirect(BASE + "/log?msg=saved&what=contact&ph=" + phone)\n    _audit_safe(con, "xf_contact", cid, op,'),
    ("X15", "film bills read by their group only (the item's size ignored)", "xray_film.py", None,
     "                sz = size_of(it[\"item_name\"])\n", "                sz = \"\"\n"),
    ("X16", "the unpaid slips counted", "xray_film.py", None, "s.paid_mode IN ('cash','upi') AND s.day>=?", "s.day>=?"),
    ("X17", "a bill's boxes ignored (every bill one box)", "aaj_duties.json", "shavez.xray_film_order_8x10", "COALESCE(p.boxes, 1)", "1"),
    ("X18", "side B (both sides) not doubled", "xray_film.py", None, 'if side in ("B", "BOTH") and', 'if side in ("NONE",) and'),
    ("X19", "a rise from more than 20 left taken from staff (a typo one film up becomes a box load)", "xray_film.py", None,
     '                if prev > lm:', '                if False:'),
    ("X20", "a 'Both ...' study doubled on side B", "xray_film.py", None, ' and not sname.strip().lower().startswith("both"):', ':'),
    ("X21", "a 'small film' bill with no size counted as 8x10", "xray_film.py", None,
     'sz = {"xray_11x14": "11x14"}.get(b["subgroup"] or "", "")', 'sz = {"xray_11x14": "11x14", "xray_small": "8x10"}.get(b["subgroup"] or "", "")'),
    ("X22", "a voided count still read", "xray_film.py", None, "WHERE c.size=? AND c.day<=? AND c.void=0 AND c.id = ", "WHERE c.size=? AND c.day<=? AND c.id = "),
    ("X23", "+91 put before a landline", "xray_film.py", None, '    return ("tel:+91" + d) if is_mobile(d) else ("tel:" + str(d or ""))',
     '    return "tel:+91" + str(d or "")'),
    ("X24", "the spare stock floored at 0 again (a bill after a load would clear the line)", "xray_film.py", None,
     '    return s + billed - loads', '    return max(0.0, s + billed - loads)'),
    ("X25", "the owner's opening spare boxes ignored", "xray_film.py", None, '        s = float(setting(con, "spare.open." + size))', '        s = 0.0'),
    ("X26", "a rise not taken as a box load", "xray_film.py", None, "        load = prev is not None and v > prev", "        load = False"),
    ("X27", "the owner's figure above 150 saved without a note", "xray_film.py", None, '            if not note:\n                return None, "note"',
     '            if False:\n                return None, "note"'),
    ("X28", "a machine record's film bill counted again beside its desk twin", "xray_film.py", None,
     '                if desk_twin(desk, l, amt[l["asset_id"]]):', '                if False:'),
    ("X29", "a voided count cannot be un-voided", "xray_film.py", None, 'op not in ("edit", "void", "unvoid")', 'op not in ("edit", "void")'),
    ("X30", "films left taken from the first figure, not the newest", "xray_film.py", None,
     '        st["left"] = float(rs[-1]["left"])', '        st["left"] = float(rs[0]["left"])'),
    ("X31", "the log's used on a box load: the plain difference", "xray_film.py", None,
     '            mach[k] = (a - b) if b <= a else max(0, a + int(_num_setting(con, "box.films")) - b)', '            mach[k] = a - b'),
    ("X32", "the new-box tick not asked of staff", "xray_film.py", None, '                if not tick:', '                if False:'),
    ("X33", "a late count not joined to the next span", "xray_film.py", None,
     '        while lt[cur["q"]] and i + 1 < len(sp):', '        while False:'),
    ("X34", "no 'check' on a box load across several uncounted days", "xray_film.py", None, "CHECK_GAP_DAYS = 3 ", "CHECK_GAP_DAYS = 300 "),
    ("X35", "the owner's word on a size-unknown bill ignored", "xray_film.py", None, "(ov.get(src, sz) if not sz else sz, bd", "(sz, bd"),
    ("X36", "the duty: spare 0 taken as a spare (due only below 0)", "aaj_duties.json", "shavez.xray_film_order_8x10",
     "AND (SELECT n FROM sp) <= 0 ", "AND (SELECT n FROM sp) < 0 "),
    ("X37", "the late time read from the day's newest row (an owner's evening correction makes a morning 'late')", "xray_film.py", None,
     "\"SELECT saved_at FROM xf_save WHERE day=? AND kind='count' ORDER BY id LIMIT 1\"", "\"SELECT saved_at FROM xf_save WHERE day=? ORDER BY id DESC LIMIT 1\""),
    ("X38", "no confirm asked of staff on a fall far above the average", "xray_film.py", None,
     '        if not own and (form.get("sure_%s" % k) or "") != "1" and needs_sure(con, k, day, vals[k]):', '        if False:'),
    ("X39", "a film bill held for its quantity counted in the spare stock", "xray_film.py", None,
     "AND gone_at='' AND held=0 AND bill_day>=?", "AND gone_at='' AND bill_day>=?"),
]


def mutate(fin, mid):
    for x in MUTANTS:
        if x[0] != mid:
            continue
        _i, _w, f, did, old, new = x
        p = os.path.join(fin, f)
        s = open(p, encoding="utf-8").read()
        if did is None:
            if s.count(old) != 1:
                return None
            s = s.replace(old, new)
        else:
            j = json.loads(s)
            hit = [d for d in j["extra"] if d.get("id") == did]
            if len(hit) != 1 or hit[0]["sql"].count(old) != 1:
                return None
            hit[0]["sql"] = hit[0]["sql"].replace(old, new)
            s = json.dumps(j, ensure_ascii=False, indent=1)
        return {f: s.encode("utf-8")}
    return None


def builder_checks(a, fin, scr):
    kit, root = os.path.abspath(a.kit), os.path.abspath(a.root)
    files = ("finance/finance_app.py", "finance/aaj_duties.json", "finance/aaj_seed.py", "finance/xray_film.py")
    b1 = os.path.join(scr, "b1")
    shutil.rmtree(b1, ignore_errors=True)
    p = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s688.py"), root, b1], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    o = p.stdout.decode("utf-8", "replace")
    same = p.returncode == 0 and all(md5f(os.path.join(b1, f)) == md5f(os.path.join(fin, f[len("finance/"):])) for f in files)
    check("M1 make_s688.py re-run on the FROM files gives the four TO files byte for byte", same, o[-300:])
    check("M2 its edits are counted: 6, each anchor found exactly once", "6 counted edits, each anchor found exactly once" in o and o.count("edit ok:") == 6)
    r2 = os.path.join(scr, "r2")
    shutil.rmtree(r2, ignore_errors=True)
    os.makedirs(os.path.join(r2, "finance"))
    for f in files[:3] + ("finance/month_jobs.py",):
        shutil.copyfile(os.path.join(root, f), os.path.join(r2, f))
    with open(os.path.join(r2, "finance/aaj_seed.py"), "ab") as fh:
        fh.write(b"\n")
    b2 = os.path.join(scr, "b2")
    p2 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s688.py"), r2, b2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    check("M3 a changed FROM file is refused, nothing written", p2.returncode != 0 and not os.path.exists(b2), p2.stdout[-160:])
    shutil.copyfile(os.path.join(root, "finance/aaj_seed.py"), os.path.join(r2, "finance/aaj_seed.py"))
    with open(os.path.join(r2, "finance/month_jobs.py"), "ab") as fh:
        fh.write(b"\n")
    p4 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s688.py"), r2, b2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    shutil.copyfile(os.path.join(root, "finance/month_jobs.py"), os.path.join(r2, "finance/month_jobs.py"))
    with open(os.path.join(r2, "finance/xray_film.py"), "w") as fh:
        fh.write("# someone else's\n")
    p3 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s688.py"), r2, b2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    check("M4 S687's month_jobs.py changed, or an xray_film.py already on the box: refused, nothing written",
          p4.returncode != 0 and p3.returncode != 0 and not os.path.exists(b2), (p4.stdout[-120:], p3.stdout[-120:]))
    sys.path.insert(0, kit)
    import make_s688 as mk                                             # noqa: E402
    olda = open(os.path.join(root, files[0]), encoding="utf-8").read()
    newa = open(os.path.join(fin, "finance_app.py"), encoding="utf-8").read()
    check("M5 finance_app.py: exactly ONE inserted mount block, nothing else changed", newa.replace(mk.MOUNT, mk.MOUNT_ANCHOR, 1) == olda
          and newa.count("import xray_film") == 1 and len(newa.splitlines()) - len(olda.splitlines()) == mk.MOUNT.count("\n") - 1)
    olds = open(os.path.join(root, files[2]), encoding="utf-8").read()
    news = open(os.path.join(fin, "aaj_seed.py"), encoding="utf-8").read()
    back = news
    for anchor, person in ((mk.SHAVEZ_ANCHOR, "shavez"), (mk.RECEPTION_ANCHOR, "reception")):
        _a, nw = mk.seed_edit(anchor, person)
        back = back.replace(nw, anchor)
    back = back.replace("            {'id': 'reception.week_pathology_register',", mk.RETIRE_LINE + "            {'id': 'reception.week_pathology_register',", 1)
    check("M6 aaj_seed.py: Shavez's three lines and Reception's one added, the retired weekly line taken off, nothing else", back == olds)
    oj = json.load(open(os.path.join(root, files[1]), encoding="utf-8"))
    nj = json.load(open(os.path.join(fin, "aaj_duties.json"), encoding="utf-8"))
    keep = [d for d in oj["extra"] if d.get("id") != RETIRED]
    check("M7 aaj_duties.json: the four duties added at the end, the retired tick taken out, every other key and duty as it was",
          {k: v for k, v in nj.items() if k != "extra"} == {k: v for k, v in oj.items() if k != "extra"} and len(keep) == len(oj["extra"]) - 1
          and nj["extra"][:len(keep)] == keep and [d["id"] for d in nj["extra"][len(keep):]] == list(IDS))
    kf = [os.path.join(kit, f) for f in sorted(os.listdir(kit)) if os.path.isfile(os.path.join(kit, f))]
    ten = [os.path.basename(f) for f in kf if TEN.search(open(f, "rb").read().decode("utf-8", "replace"))]
    crlf = [os.path.basename(f) for f in kf if b"\r" in open(f, "rb").read()]
    check("M8 no ten-digit number in any kit file; every kit file LF only", not ten and not crlf, (ten, crlf))
    bad = []
    for f in [x for x in kf if x.endswith(".py")] + [os.path.join(fin, n) for n in ("xray_film.py", "finance_app.py", "aaj_seed.py")]:
        q = subprocess.run([sys.executable, "-c", "import sys,py_compile; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)", f,
                            os.path.join(scr, "pc.pyc")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if q.returncode:
            bad.append(os.path.basename(f))
    check("M9 every kit and built python file compiles", not bad, bad)
    for d in (b1, r2):
        shutil.rmtree(d, ignore_errors=True)


def outer(a):
    scr = os.path.abspath(a.scratch)
    os.makedirs(scr, exist_ok=True)
    kit = os.path.abspath(a.kit)
    if a.control:
        fin = os.path.abspath(a.control)
        print("CONTROL -- the S688 checks on the LIVE files")
        sc, outp = run_inner(fin, a.db, os.path.join(scr, "c0"), kit, "live")
        print("\n".join(l for l in outp.splitlines() if CHECK_RE.match(l)))
        if sc is None:
            print(outp[-600:])
            print("CONTROL did not finish")
            return 1
        print("%d S688 check(s) red . %d green" % sc)
        return 0
    fin = os.path.abspath(a.new)
    only = set((a.only or "").split(",")) - {""}
    if not only or "inner" in only:
        print("THE FILES -- the S688 checks through the real app")
        sc, outp = run_inner(fin, a.db, os.path.join(scr, "n0"), kit, "new")
        for l in outp.splitlines():
            if CHECK_RE.match(l):
                print(l)
                results.append((l[7:], l.startswith("  ok "), ""))
        if sc is None:
            print(outp[-1500:])
            check("the inner walk finished", False)
    if a.kit687 and (not only or "s687" in only):
        print("S687 -- its own inner walk on these files (the month jobs still mount and walk)")
        k7 = os.path.abspath(a.kit687)
        sc, outp = run_inner(fin, a.db, os.path.join(scr, "k7"), k7, "s687", script=os.path.join(k7, "walk_s687.py"))
        check("K1 S687's inner walk on the S688 files: every check green (%s)" % (("%d red . %d green" % sc) if sc else "did not finish"),
              sc is not None and sc[0] == 0 and sc[1] >= 40, outp[-400:] if sc is None or sc[0] else "")
    if a.root and (not only or "builder" in only):
        print("THE BUILDER")
        builder_checks(a, fin, scr)
    if a.old and (not only or "lists" in only):
        print("EVERY PERSON'S AAJ LIST -- the live files against these, on two identical copies, today's clock")
        outs = {}
        for tag, f in (("old", os.path.abspath(a.old)), ("new", fin)):
            d = os.path.join(scr, "d_%s.db" % tag)
            copydb(a.db, d)
            o = os.path.join(scr, "d_%s.json" % tag)
            p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--dump", f, "--db", d, "--scratch", scr, "--out", o, "--kit", kit],
                               cwd="/tmp", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            outs[tag] = json.load(open(o)) if p.returncode == 0 and os.path.exists(o) else None
            for x in (d, o):
                if os.path.exists(x):
                    os.remove(x)
            if outs[tag] is None:
                print(p.stdout.decode("utf-8", "replace")[-600:])
        o_, n_ = outs.get("old"), outs.get("new")
        ok = o_ is not None and n_ is not None
        diff = []
        if ok:
            for k in sorted(set(o_["lists"]) | set(n_["lists"])):
                a1 = [x for x in (o_["lists"].get(k) or []) if x[1] != RETIRED]
                b1 = [x for x in (n_["lists"].get(k) or []) if x[1] not in IDS]
                if a1 != b1:
                    diff.append(k)
        check("B1 every person's list as the owner sees it (?as=) is unchanged apart from the new film lines and the retired one", ok and not diff, diff)
        allnew = ok and [x for k in n_["lists"] for x in n_["lists"][k] if x[1] == RETIRED] + [x for k in n_["own"] for x in n_["own"][k][2] if x[1] == RETIRED]
        check("RT1 the retired weekly tick: on Reception's list and the owner's console before, gone from every list and the console after; "
              "every other console line unchanged",
              ok and any(x[1] == RETIRED for x in o_["lists"].get("reception", [])) and RETIRED in o_["console"] and not allnew
              and RETIRED not in n_["console"] and [i for i in o_["console"] if i != RETIRED] == [i for i in n_["console"] if i not in IDS],
              ok and (RETIRED in o_["console"], RETIRED in n_["console"]))
        check("B2 every login's own list unchanged apart from the new film lines and the retired one (status, partial, lines)",
              ok and all((o_["own"][k][0], o_["own"][k][1], [x for x in o_["own"][k][2] if x[1] != RETIRED]) ==
                         (n_["own"][k][0], n_["own"][k][1], [x for x in n_["own"][k][2] if x[1] not in IDS]) for k in o_["own"]),
              ok and {k: (o_["own"][k][:2], n_["own"][k][:2]) for k in o_["own"]})
        check("B3 unread per person unchanged; Reception's and Shavez's 0 (the new lines all read: F-1024)",
              ok and o_["unread"] == n_["unread"] and n_["unread"].get("reception") == 0 and n_["unread"].get("shavez") == 0,
              ok and (o_["unread"], n_["unread"]))
        check("B4 the app mounts on both, _MOUNT_FAILED empty", ok and o_["mount_failed"] == [] and n_["mount_failed"] == [])
    if not only or [x for x in only if x.startswith("X")] or "mutants" in only:
        print("THE MUTANTS -- each must turn at least one S688 check red")
        todo = [x for x in MUTANTS if not (only and "mutants" not in only and x[0] not in only)]

        def one(x):
            over = mutate(fin, x[0])
            if over is None:
                return x, None, None
            mf = os.path.join(scr, "mut_fin_" + x[0])
            mkfin(fin, mf, over)
            try:
                sc_, outp_ = run_inner(mf, a.db, os.path.join(scr, "m_" + x[0]), kit, x[0])
            finally:
                shutil.rmtree(mf, ignore_errors=True)
            return x, sc_, outp_
        # WALK_JOBS (default 2) mutants at a time: each in its own folder and its own copy of the database
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max(1, int(os.environ.get("WALK_JOBS") or 2))) as ex:
            done = list(ex.map(one, todo))
        for x, sc, outp in done:
            if outp is None:
                check("%s %s: the mutation applies" % (x[0], x[1]), False)
                continue
            reds = [l[7:60] for l in outp.splitlines() if l.startswith("  RED  ")]
            check("%s caught: %s (%s)" % (x[0], x[1], (reds[0].strip() if reds else "no red")), sc is not None and sc[0] >= 1, outp[-300:] if sc is None else "")
    green = sum(1 for r in results if r[1])
    print("%d of %d green" % (green, len(results)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new")
    g.add_argument("--control")
    g.add_argument("--inner")
    g.add_argument("--dump")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--kit")
    ap.add_argument("--kit687")
    ap.add_argument("--root")
    ap.add_argument("--old")
    ap.add_argument("--out")
    ap.add_argument("--only")
    a = ap.parse_args()
    if a.inner:
        return inner(a)
    if a.dump:
        return dump(a)
    return outer(a)


if __name__ == "__main__":
    sys.exit(main())
