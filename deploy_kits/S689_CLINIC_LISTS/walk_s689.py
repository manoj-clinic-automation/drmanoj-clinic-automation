#!/usr/bin/env python3
"""walk_s689.py -- kit S689_CLINIC_LISTS (01-Nov-2026, the parent, S373). Runs the REAL finance app and the REAL portal on COPIES only.

    --new <fin> --portal <pdir> --base <bdir> --db <copy> --scratch <dir> --kit <kitdir> [--root <root>] [--only a,b]
          every check on the files to test: the S689 checks through the real finance app (inner, its own process), the portal
          checks (pdir/portal/portal.py under test against bdir/portal/portal.py, both with bdir's tile_grants.json), the
          builder checks (when --root is given: make_s689.py re-run on <root> gives the three TO files byte for byte; it refuses
          a changed FROM and its own output) and the mutants. Last line: "N of N green".
    --control <fin> --portal <bdir> --base <bdir> --db <copy> --scratch <dir> --kit <kitdir>
          the CONTROL: the S689 checks on the LIVE files. Last line: "X S689 check(s) red . Y green".
    --inner <fin> --db <copy> --scratch <dir>       (one process: the app is loaded once)

<fin> is a folder holding a whole copy of /root/finance's code (never the database). --db is a COPY of finance.db; the walk copies it
again into --scratch and writes made-up rows to that copy only (W689 names, clinic IDs W689-nn, slip numbers from 900001, the days
10-12 Nov 2027, Docterz sn from 9001). Header sign-in is switched on for this process only. No ten-digit number in this file.
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

res = []


def check(name, ok, note=""):
    res.append((name, bool(ok), str(note)[:300]))


def md5f(p):
    try:
        return hashlib.md5(open(p, "rb").read()).hexdigest()
    except OSError:
        return ""


def copydb(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


D1, D2, D3 = "2027-11-10", "2027-11-11", "2027-11-12"   # far ahead: never a real clinic day when this runs
NOW = "2027-11-20T10:00:00"


def seed(con, xs):
    """The made-up rows. xs = (service_id, films, size) of an X-ray study with a size and both_one 0."""
    cur = con.cursor()
    sid = {}

    def slip(no, day, cid, name, state="ok", paid="", series="xp"):
        cur.execute("INSERT INTO slip (series, slip_no, day, clinic_id, name_seen, state, paid_mode, logged_by, logged_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)", (series, no, day, cid, name, state, paid, "w689", day + " 10:00:00"))
        sid[no] = cur.lastrowid
        return cur.lastrowid

    def item(no, kind, svc, name, side="", price=0, disc=0, sort=0):
        cur.execute("INSERT INTO slip_item (slip_id, kind, service_id, name, side, price_p, sort, discount_p) VALUES (?,?,?,?,?,?,?,?)",
                    (sid[no], kind, svc, name, side, price, sort, disc))

    slip(900001, D1, "W689-01", "W689 Asha Rani", paid="cash")
    item(900001, "proc", 21, "B/K (Below knee) fibre cast", "R", 300000, 0, 1)
    item(900001, "proc", 61, "ILI KNEE", "", 50000, 0, 2)
    slip(900002, D1, "W689-02", "W689 Bholu Ram", paid="upi")
    item(900002, "proc", 36, "Dressing", "", 10000, 0, 1)
    item(900002, "xray", xs[0], "W689 study", "B", 50000, 0, 2)
    slip(900003, D1, "W689-03", "W689 Chanda Devi")                            # not marked paid
    item(900003, "proc", 30, "Clavicle bandage", "", 80000, 0, 1)
    slip(900004, D2, "W689-10", "W689 Dinesh Kumar")                           # free (full discount), paid_mode ''
    item(900004, "proc", 35, "ILI (heel)", "L", 50000, 50000, 1)
    slip(900005, D2, "W689-04", "W689 Ekta Void", state="void", paid="cash")
    item(900005, "proc", 20, "A/K (Above knee) fibre cast", "R", 700000, 0, 1)
    slip(900006, D2, "W689-11", "W689 Farid Cancelled", state="cancelled")
    item(900006, "proc", 20, "A/K (Above knee) fibre cast", "L", 700000, 0, 1)
    slip(900008, D2, "W689-05", "W689 Gopal Sugar", paid="cash")
    item(900008, "proc", 62, "RBS Glucometer", "", 5000, 0, 1)
    slip(900009, D3, "W689-12", "W689 Hari Free Typed", paid="cash")
    item(900009, "proc", None, "Other: W689 splint", "", 20000, 0, 1)
    item(900009, "proc", None, "ILI W689 wrist", "R", 30000, 0, 2)
    slip(900010, D3, "W689-08", "W689 Indu Disc", paid="cash")
    item(900010, "proc", 41, "HBK (High below knee) fibre slab", "L", 300000, 30000, 1)
    slip(900011, D1, "W689-08", "W689 Indu Disc", paid="cash")
    item(900011, "proc", 36, "Dressing", "", 10000, 0, 1)
    slip(900012, D3, "W689-13", "", paid="upi")                               # no name typed: the name comes from the patient master
    item(900012, "proc", 36, "Dressing", "", 10000, 0, 1)
    cur.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4) VALUES (?,?,?)", ("W689-13", "W689 Lata Ref", "0000"))
    dz = [(D1, "proc", 9001, "W689 Bholu Ram", "W689-02", 10000, "Cash"),      # has a proc line that day: not listed
          (D1, "proc", 9002, "W689 Jaya Only", "W689-06", 15000, "UPI"),       # no slip: listed
          (D2, "xray", 9003, "W689 Gopal Sugar", "W689-05", 5000, "Cash"),     # the glucometer under X-ray: matched
          (D1, "xray", 9004, "W689 Kamal Xonly", "W689-07", 50000, "Cash"),    # no slip: listed (X-rays)
          (D1, "proc", 9005, "W689 Chanda Devi", "W689-03", 80000, "Cash"),    # her unpaid slip has the line: not listed
          (D2, "proc", 9006, "W689 Indu Disc", "W689-08", 12000, "Cash"),      # her slip is on D1 and D3, not D2: listed
          (D2, "proc", 9007, "W689 Zero Amt", "W689-09", 0, "Cash"),           # amount 0: not listed
          (D2, "proc", 9008, "W689 Ekta Void", "W689-04", 30000, "Cash"),      # only a void slip: listed
          (D3, "xray", 9009, "W689 Hari Free Typed", "W689-12", 5000, "Cash")]  # Rs 50 X-ray, no Rs 50 proc line: listed
    for r in dz:
        cur.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)", r)
    con.commit()


def inner(a):
    fin, scr = os.path.abspath(a.inner), os.path.abspath(a.scratch)
    os.makedirs(scr, exist_ok=True)
    dbp = os.path.join(scr, "w689.db")
    copydb(a.db, dbp)
    raw = sqlite3.connect(dbp)
    raw.row_factory = sqlite3.Row
    used = raw.execute("SELECT COUNT(*) FROM slip WHERE clinic_id LIKE 'W689%' OR slip_no >= 900001 OR name_seen LIKE 'W689%'").fetchone()[0]
    used += raw.execute("SELECT COUNT(*) FROM clinic_day_line WHERE clinic_id LIKE 'W689%' OR business_date IN (?,?,?)", (D1, D2, D3)).fetchone()[0]
    used += raw.execute("SELECT COUNT(*) FROM patient_ref WHERE clinic_id LIKE 'W689%'").fetchone()[0]
    check("S689 W0 the made-up IDs, slip numbers and days are unused in the database copy (F-1059)", used == 0, used)
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", CLINICLISTS_NOW=NOW,
                      XRAYFILM_NOW=NOW)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                           # noqa: E402
    mf = [n for n, _w in getattr(fa, "_MOUNT_FAILED", [])]
    check("S689 A1 the real finance app mounts with _MOUNT_FAILED empty and clinic_lists loaded", mf == [] and "clinic_lists" in sys.modules, mf)
    CL = sys.modules.get("clinic_lists")
    XF = sys.modules.get("xray_film")
    if XF is not None:
        XF.ensure(raw)                                                 # the film log's own tables and its seeded study sizes
        raw.commit()
    xs = raw.execute("SELECT s.service_id, s.films, s.size FROM xf_study s JOIN owner_service o ON o.id = s.service_id "
                     "WHERE s.size<>'' AND s.both_one=0 AND lower(o.name) NOT LIKE 'both%' AND s.id = "
                     "(SELECT MAX(q.id) FROM xf_study q WHERE q.service_id=s.service_id) ORDER BY s.service_id LIMIT 1").fetchone() \
        if XF is not None else None
    xs = (xs[0], int(xs[1]), xs[2]) if xs else (None, 1, "")
    seed(raw, xs)
    tables = [r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]

    def counts():
        return {t: raw.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in tables}
    before = counts()
    c = fa.app.test_client(use_cookies=False)

    def G(path, user):
        h = {"X-Clinic-User": user} if user else {}
        r = c.get(path, headers=h)
        loc = (r.headers.get("Location") or "").replace("http://localhost", "")
        return r.status_code, (r.get_data(as_text=True) if ".xlsx" not in path else r.get_data()), loc, r

    B = "/finance/slips/lists"
    rng = "?f=%s&t=%s" % (D1, D3)
    # ---- who reaches what
    s1 = [G(B + p, "manoj")[0] for p in ("/proc", "/xray", "/proc.xlsx", "/xray.xlsx", "/proc" + rng)]
    check("S689 A2 manoj: both lists and both Excel files answer 200", s1 == [200] * 5, s1)
    st, _b, loc, _r = G(B, "manoj")
    check("S689 A3 manoj: the hub redirects to the procedures list", st in (301, 302) and loc.endswith(B + "/proc"), (st, loc))
    others = {}
    for u in ("bhawna", "shavez", "alisha", "shivani", "awdhesh", "bhati", "sukhveer", "reception", "darpan"):
        others[u] = [G(B + p, u)[0] for p in ("", "/proc", "/xray", "/proc.xlsx", "/xray.xlsx", "/foo")]
    bad = {u: v for u, v in others.items() if any(x == 200 for x in v)}
    check("S689 A4 no other login reaches any of these paths (403 inside, or the front gate)", not bad, bad)
    check("S689 A5 the other doctor (bhawna, a slips checker) gets 403 on every path", others["bhawna"] == [403] * 6, others["bhawna"])
    nl = [G(B + p, "")[0] for p in ("", "/proc", "/xray.xlsx")]
    check("S689 A6 no login: the front gate (302) on every path", nl == [302] * 3, nl)
    st, _b, loc, _r = G(B + "/foo", "manoj")
    check("S689 A7 an unknown tab sends manoj back to the procedures list", st in (301, 302) and loc.endswith(B + "/proc"), (st, loc))
    # ---- the rows (the module's own functions on the copy)
    rp = CL.rows_for(raw, "proc", D1, D3) if CL else []
    got = sorted((str(e["no"]), e["cid"], e["kind"], e["paid"], e["amount_p"]) for e in rp)
    want = sorted([("900001", "W689-01", "cast", "cash", 300000), ("900001", "W689-01", "ili", "cash", 50000),
                   ("900002", "W689-02", "dress", "upi", 10000), ("900003", "W689-03", "other", "unpaid", 80000),
                   ("900004", "W689-10", "ili", "free", 0), ("900008", "W689-05", "other", "cash", 5000),
                   ("900009", "W689-12", "other", "cash", 20000), ("900009", "W689-12", "ili", "cash", 30000),
                   ("900010", "W689-08", "cast", "cash", 270000), ("900011", "W689-08", "dress", "cash", 10000),
                   ("900012", "W689-13", "dress", "upi", 10000),
                   ("", "W689-06", "dz", "dz", 15000), ("", "W689-08", "dz", "dz", 12000), ("", "W689-04", "dz", "dz", 30000)])
    check("S689 B1 the procedure rows of 10-12 Nov are exactly the expected 14 (kinds, paid, amounts, Docterz only)", got == want,
          [x for x in got if x not in want] + ["missing:"] + [x for x in want if x not in got])
    check("S689 B2 void and cancelled slips never show", not [e for e in rp if str(e["no"]) in ("900005", "900006")])
    check("S689 B3 the clavicle bandage is Other, not a cast; ILI KNEE and a typed 'ILI ...' are ILI; 'Other: ...' typed is Other",
          [e["kind"] for e in rp if e["item"] == "Clavicle bandage"] == ["other"]
          and [e["kind"] for e in rp if e["item"] in ("ILI KNEE", "ILI W689 wrist")] == ["ili", "ili"]
          and [e["kind"] for e in rp if e["item"] == "Other: W689 splint"] == ["other"])
    check("S689 B9 a slip with no name typed shows the patient master's name (slip_log's own rule)",
          [e["name"] for e in rp if str(e["no"]) == "900012"] == ["W689 Lata Ref"], [e["name"] for e in rp if str(e["no"]) == "900012"])
    check("S689 B8 a name that only begins with the letters ili ('Ilizarov ...', 'iliac ...') is not ILI; 'ILI (heel)', 'ILI KNEE' are",
          CL is not None and CL.kind_of("Ilizarov pin site dressing", "") == "other" and CL.kind_of("Iliac crest graft", "Cast / slab") == "other"
          and CL.kind_of("ILI (heel)", "Injection (ILI)") == "ili" and CL.kind_of("ILI KNEE", "") == "ili" and CL.kind_of("ili", "") == "ili")
    check("S689 B4 a partial discount: the amount is rate minus discount and the discount is kept for the row",
          [(e["amount_p"], e["disc_p"]) for e in rp if str(e["no"]) == "900010"] == [(270000, 30000)])
    rx = CL.rows_for(raw, "xray", D1, D3) if CL else []
    gx = sorted((str(e["no"]), e["cid"], e["paid"], e["amount_p"], e.get("size"), e.get("films")) for e in rx)
    wx = sorted([("900002", "W689-02", "upi", 50000, xs[2], 2 * xs[1]), ("", "W689-07", "dz", 50000, "", 0),
                 ("", "W689-12", "dz", 5000, "", 0)])
    check("S689 B5 the X-ray rows: side B doubles the study's films (the film log's rule); the Rs 50 Docterz X-ray of a patient with "
          "a Rs 50 procedure line is matched, one without it is listed; the no-slip X-ray is listed", gx == wx, (gx, wx))
    if XF is not None and CL is not None:
        a1 = sorted((e["no"], e["size"], e["films"]) for e in XF.slip_lines(raw, "2026-10-01", D3))
        a2 = sorted((e["no"], e["size"], e["films"]) for e in CL.rows_for(raw, "xray", "2026-10-01", D3) if e["mode"] in ("cash", "upi"))
        check("S689 B6 for every paid X-ray line since 1-Oct the film size and films equal the film log's own (xray_film.slip_lines)",
              a1 == a2 and len(a1) > 0, (len(a1), len(a2)))
    else:
        check("S689 B6 for every paid X-ray line since 1-Oct the film size and films equal the film log's own (xray_film.slip_lines)", False, "no module")
    sm = CL.summary(rp, "proc") if CL else {}
    check("S689 B7 the month counts by kind and their amounts add up (cast 2 = Rs 5,700; ILI 3; dressing 3; other 3; Docterz only 3)",
          sm.get("kinds", {}).get("cast") == (2, 570000) and sm["kinds"]["ili"][0] == 3 and sm["kinds"]["dress"] == (3, 30000)
          and sm["kinds"]["other"][0] == 3 and sm["kinds"]["dz"] == (3, 57000) and sm["n"] == 14 and sm["free"] == 1 and sm["unpaid"] == 1,
          sm)
    # ---- the page
    st, body, _l, _r = G(B + "/proc" + rng, "manoj")
    names = ["W689 Asha Rani", "W689 Bholu Ram", "W689 Chanda Devi", "W689 Dinesh Kumar", "W689 Jaya Only", "W689 Indu Disc", "W689 Ekta Void"]
    check("S689 C1 the procedures page for 10-12 Nov shows every made-up patient, Free, Not marked paid, the discount and Docterz only",
          st == 200 and all(n in body for n in names) and ">Free<" in body and "Not marked paid" in body and "(disc. ₹300)" in body
          and "In Docterz only" in body and "W689 Farid" not in body, [n for n in names if n not in body])
    check("S689 C2 the page shows the amounts (the day's total Rs 4,650 on 10 Nov) and the month tiles", "₹4,650" in body and "Casts &amp; slabs" in body)
    tb = body[body.find("<table"):] if "<table" in body else ""
    check("S689 C3 the days come newest first", 0 <= tb.find("Fri 12 Nov") < tb.find("Thu 11 Nov") < tb.find("Wed 10 Nov"),
          (tb.find("Fri 12 Nov"), tb.find("Thu 11 Nov"), tb.find("Wed 10 Nov")))
    st, bx, _l, _r = G(B + "/xray" + rng, "manoj")
    check("S689 C4 the X-ray page shows the films column, the doubled films and the Docterz-only X-ray", st == 200 and "Films" in bx
          and "W689 Kamal Xonly" in bx and ("<td class='r'>%d</td>" % (2 * xs[1])) in bx)
    # ---- the search
    st, bs, _l, _r = G(B + "/proc?q=asha", "manoj")
    check("S689 D1 a search is case-blind and spans 1-Oct to today whatever the month: 'asha' finds W689 Asha Rani's two lines",
          st == 200 and "W689 <mark>Asha</mark> Rani" in bs and "W689 Bholu" not in bs and "Search “asha” across 1 Oct 2026" in bs)
    st, bs, _l, _r = G(B + "/proc" + rng + "&q=W689-08", "manoj")
    check("S689 D2 a search by clinic ID finds that patient's slip lines AND the Docterz-only line", st == 200 and bs.count("<mark>W689-08</mark>") == 3, bs.count("<mark>W689-08</mark>"))
    st, bs, _l, _r = G(B + "/proc" + rng + "&q=900009", "manoj")
    check("S689 D3 a search by slip number finds that slip's lines", st == 200 and bs.count("<mark>900009</mark>") == 2)
    rq = CL.rows_for(raw, "proc", D1, D3, "ili") if CL else []      # the made-up days only: a real "Dilip" must not matter (review 3)
    check("S689 D4 a search by procedure name: 'ili' finds every ILI line and nothing that is not", rq and all("ili" in e["item"].lower() for e in rq)
          and {"900001", "900004", "900009"} <= {str(e["no"]) for e in rq})
    st, bs, _l, _r = G(B + "/proc?q=%3Cscript%3Ex", "manoj")
    check("S689 D5 a search with markup in it is shown escaped, never as markup", st == 200 and "<script>x" not in bs and "&lt;script&gt;x" in bs)
    rn = CL.rows_for(raw, "proc", D1, D3, "no") if CL else [None]
    check("S689 D7 a short search ('no') does not list the Docterz-only rows by their placeholder words", CL is not None
          and not [e for e in rn if e["dz"]], [e["cid"] for e in rn if e and e["dz"]])
    st, bs, _l, _r = G(B + "/proc?q=zzW689nothing", "manoj")
    check("S689 D6 a search with no match says so", st == 200 and "Nothing matches" in bs)
    # ---- the dates
    st, bm, _l, _r = G(B + "/proc?m=2027-11", "manoj")
    check("S689 E1 the month November 2027 (to 20 Nov) holds the made-up days", st == 200 and "W689 Asha Rani" in bm and "(to 20-Nov)" in bm)
    st, bm, _l, _r = G(B + "/proc?m=2026-09", "manoj")
    check("S689 E2 a month before October is refused with a word, and this month shown", st == 200 and "outside 1 October" in bm)
    st, bm, _l, _r = G(B + "/proc?f=2026-13-45", "manoj")
    check("S689 E3 a date that is not a date is refused with a word", st == 200 and "not a date" in bm)
    r_sep = CL.rows_for(raw, "proc", "2026-09-01", "2026-09-30") if CL else []
    st, bm, _l, _r = G(B + "/proc?f=2026-09-01&t=2026-09-30", "manoj")
    check("S689 E4 a range before 1 October is clamped to 1 October (no September slip shown)", st == 200 and " Sep 2026</b>" not in bm
          and (len(r_sep) > 0), len(r_sep))
    st, bm, _l, _r = G(B + "/proc?f=%s&t=%s" % (D3, D1), "manoj")
    check("S689 E5 a From after the To is swapped, not refused", st == 200 and "W689 Asha Rani" in bm and "W689 Hari" in bm)
    # ---- the Excel
    st, xb, _l, rr = G(B + "/proc.xlsx" + rng + "&q=W689", "manoj")
    ok_x, nrows, txt = False, 0, ""
    try:
        z = zipfile.ZipFile(io.BytesIO(xb))
        txt = "".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.startswith("xl/"))
        ok_x = "W689 Asha Rani" in txt and "Not marked paid" in txt and "Docterz only" in txt
        nrows = len(re.findall(r"<row ", txt))
    except Exception as e:                                             # noqa: BLE001
        txt = repr(e)
    check("S689 F1 the Excel of a range + search is a workbook with the made-up rows, Not marked paid and Docterz only", st == 200 and ok_x
          and "spreadsheetml" in (rr.headers.get("Content-Type") or ""), (st, txt[:120]))
    check("S689 F2 the Excel has one row per line on the screen (14) plus its title and header rows", nrows >= 16, nrows)
    st, xb2, _l, _r = G(B + "/xray.xlsx" + rng, "manoj")
    check("S689 F3 the X-ray Excel answers and names the film size", st == 200 and xb2[:2] == b"PK")
    # ---- nothing written
    after = counts()
    check("S689 G1 nothing is written: every table's row count is the same after every page and Excel above",
          before == after, {t: (before[t], after[t]) for t in tables if before.get(t) != after.get(t)})
    src = open(os.path.join(fin, "clinic_lists.py"), encoding="utf-8").read() if os.path.exists(os.path.join(fin, "clinic_lists.py")) else ""
    check("S689 G2 the module has no INSERT, UPDATE, DELETE, CREATE or DROP, and no ten-digit number",
          src != "" and not re.search(r"\b(INSERT|UPDATE|DELETE|CREATE|DROP)\b", src) and not re.search(r"\d{10}", src))
    # ---- the live data's own control (October on the real rows, independent SQL)
    n_sql = raw.execute("SELECT COUNT(*), COALESCE(SUM(i.price_p - i.discount_p), 0) FROM slip s JOIN slip_item i ON i.slip_id=s.id "
                        "AND i.kind='proc' WHERE s.series='xp' AND s.state='ok' AND s.day BETWEEN '2026-10-01' AND '2026-10-31'").fetchone()
    ro = [e for e in (CL.rows_for(raw, "proc", "2026-10-01", "2026-10-31") if CL else []) if not e["dz"]]
    check("S689 L1 October on the real rows: the list's procedure lines and their total equal an independent count of the slips",
          CL is not None and (len(ro), sum(e["amount_p"] for e in ro)) == (n_sql[0], n_sql[1]) and n_sql[0] > 0, ((len(ro), sum(e["amount_p"] for e in ro)), tuple(n_sql)))
    x_sql = raw.execute("SELECT COUNT(*) FROM slip s JOIN slip_item i ON i.slip_id=s.id AND i.kind='xray' WHERE s.series='xp' AND "
                        "s.state='ok' AND s.day BETWEEN '2026-10-01' AND '2026-10-31'").fetchone()[0]
    xo = [e for e in (CL.rows_for(raw, "xray", "2026-10-01", "2026-10-31") if CL else []) if not e["dz"]]
    check("S689 L2 October on the real rows: the list's X-ray lines equal an independent count", CL is not None and len(xo) == x_sql and x_sql > 0, (len(xo), x_sql))
    raw.close()
    for f in (dbp, dbp + "-wal", dbp + "-shm"):
        try:
            os.remove(f)
        except OSError:
            pass


def portal_checks(a):
    import importlib.util
    import warnings
    warnings.filterwarnings("ignore")
    base = os.path.abspath(a.base)
    gfile = os.path.join(base, "portal", "tile_grants.json")

    def load(d, tag):
        os.environ["TILE_GRANTS_FILE"] = gfile
        sys.path.insert(0, os.path.join(base, "portal"))
        spec = importlib.util.spec_from_file_location("portal_" + tag, os.path.join(d, "portal", "portal.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.TILE_GRANTS_FILE = gfile
        m._GRANTS_CACHE.update(mtime=None, data=None)
        return m
    try:
        N, Bm = load(os.path.abspath(a.portal), "new"), load(base, "base")
    except Exception as e:                                             # noqa: BLE001
        check("S689 P0 both portals load", False, repr(e))
        return
    users = sorted(json.load(open(gfile))["users"]) + ["someone_else"]

    def names(m, u, r):
        m._GRANTS_CACHE.update(mtime=None, data=None)
        return {t["name"]: (g, t.get("url")) for g, it in m._visible_sections(r, True, u) for t in it}
    diffs = {}
    for u in users:
        for r in ("doctor", "manager", "staff"):
            nn, bb = names(N, u, r), names(Bm, u, r)
            add = set(nn) - set(bb)
            gone = set(bb) - set(nn)
            if add or gone or any(nn[k] != bb[k] for k in set(nn) & set(bb)):
                diffs[(u, r)] = (sorted(add), sorted(gone))
    mn = names(N, "manoj", "doctor")
    check("S689 P1 manoj's home has the tile 'X-ray & procedures' in Patients, opening /finance/slips/lists",
          mn.get("X-ray & procedures") == ("Patients", "/finance/slips/lists"), mn.get("X-ray & procedures"))
    check("S689 P2 Dr Bhawna's home does not have it", "X-ray & procedures" not in names(N, "bhawna", "doctor"))
    staffish = [k for k, v in diffs.items() if k[1] != "doctor"]
    check("S689 P3 no manager or staff login sees any change on its home", not staffish, staffish)
    other = {k: v for k, v in diffs.items() if v != (["X-ray & procedures"], [])}
    check("S689 P4 the only change on any home is the one new tile (every login, every role)", not other, other)
    try:
        with N.app.test_request_context("/portal"):
            s = N._visible_sections("doctor", True, "manoj")
            html = N.render_template_string(N.PORTAL_HTML, sections=s, blocks=N._home_blocks(s, N._folders_for("manoj")), sso=False,
                                            who={"user": "manoj", "role": "doctor"}, role="doctor", pc=True, s444_nowork=False)
        check("S689 P5 manoj's home page renders with the tile and its link", "X-ray &amp; procedures" in html and "/finance/slips/lists" in html)
    except Exception as e:                                             # noqa: BLE001
        check("S689 P5 manoj's home page renders with the tile and its link", False, repr(e))


def builder_checks(a, fin, scr):
    kit, root = os.path.abspath(a.kit), os.path.abspath(a.root)
    b1 = os.path.join(scr, "b1")
    shutil.rmtree(b1, ignore_errors=True)
    p = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s689.py"), root, b1], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    o = p.stdout.decode("utf-8", "replace")
    same = p.returncode == 0 and md5f(os.path.join(b1, "finance/finance_app.py")) == md5f(os.path.join(fin, "finance_app.py")) \
        and md5f(os.path.join(b1, "finance/clinic_lists.py")) == md5f(os.path.join(fin, "clinic_lists.py")) \
        and md5f(os.path.join(b1, "portal/portal.py")) == md5f(os.path.join(os.path.abspath(a.portal), "portal/portal.py"))
    check("M1 make_s689.py re-run on the FROM files gives the three TO files byte for byte", same, o[-300:])
    check("M2 its edits are counted: 3, each anchor found exactly once", "3 counted edits, each anchor found exactly once" in o and o.count("edit ok:") == 3)
    r2 = os.path.join(scr, "r2")
    shutil.rmtree(r2, ignore_errors=True)
    for f in ("finance/finance_app.py", "portal/portal.py"):
        os.makedirs(os.path.dirname(os.path.join(r2, f)), exist_ok=True)
        shutil.copyfile(os.path.join(root, f), os.path.join(r2, f))
    with open(os.path.join(r2, "portal/portal.py"), "ab") as fh:
        fh.write(b"\n")
    p2 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s689.py"), r2, os.path.join(scr, "b2")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    check("M3 a FROM file changed by one byte: the builder STOPs and writes nothing", p2.returncode != 0 and "STOP" in p2.stdout.decode()
          and not os.path.exists(os.path.join(scr, "b2")))
    r3 = os.path.join(scr, "r3")
    shutil.rmtree(r3, ignore_errors=True)
    shutil.copytree(b1, r3)
    p3 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s689.py"), r3, os.path.join(scr, "b3")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    check("M4 the builder run on its own output STOPs (no second mount, no second tile)", p3.returncode != 0 and "STOP" in p3.stdout.decode())


MUTANTS = [
    ("X1", "ILI KNEE not counted as ILI", 'if re.match(r"ili\\b", n):', 'if re.match(r"ili \\(", n):'),
    ("X17", "any name beginning ili counted as ILI", 'if re.match(r"ili\\b", n):', 'if n.startswith("ili"):'),
    ("X18", "the search reading a Docterz-only row's placeholder words", '(not e["dz"] and ql in e["item"].lower())', '(ql in e["item"].lower())'),
    ("X19", "the patient master's name not used", "        if seen:\n            return seen\n        if not cid or SL is None:", "        if True:\n            return seen\n        if not cid or SL is None:"),
    ("X2", "the clavicle bandage counted as a cast", 'if g.startswith("cast") and ("cast" in n or "slab" in n):', 'if g.startswith("cast"):'),
    ("X3", "void slips listed", "WHERE s.series = 'xp' AND s.state = 'ok' AND s.day >= ? AND s.day <= ? ORDER BY",
     "WHERE s.series = 'xp' AND s.state IN ('ok','void') AND s.day >= ? AND s.day <= ? ORDER BY"),
    ("X4", "the other doctor let in", 'if err or str((u or {}).get("user") or "") != OWNER:', 'if err:'),
    ("X5", "Docterz matched on the patient whatever the day", "        if cid and key in have:\n",
     "        if cid and any(k[1] == cid for k in have):\n"),
    ("X6", "the Rs 50 glucometer rule gone", "GLUCO_P = 5000 ", "GLUCO_P = 4999 "),
    ("X7", "side B not doubled", '        films *= 2\n', '        films *= 1\n'),
    ("X8", "the search word shown unescaped in the heading", 'head = "Search “%s” across 1 Oct 2026 – %s" % (_esc(q)', 'head = "Search “%s” across 1 Oct 2026 – %s" % ((q)'),
    ("X9", "a full discount not shown Free", "    if net_p <= 0:\n        return \"free\"", "    if net_p < 0:\n        return \"free\""),
    ("X10", "the search blind to the clinic ID", ' or ql in e["cid"].lower()', ''),
    ("X11", "a range before 1-Oct not clamped", "            d0, d1 = max(d0, lo), min(d1, hi)\n", "            pass\n"),
    ("X12", "a Docterz line of 0 listed", "WHERE section = ? AND amount_p > 0 AND", "WHERE section = ? AND amount_p >= 0 AND"),
    ("X13", "unpaid slips hidden", "WHERE s.series = 'xp' AND s.state = 'ok' AND s.day >= ? AND s.day <= ? ORDER BY",
     "WHERE s.series = 'xp' AND s.state = 'ok' AND s.paid_mode <> '' AND s.day >= ? AND s.day <= ? ORDER BY"),
    ("X14", "the days oldest first on the page", "    for day in sorted(byday, reverse=True):", "    for day in sorted(byday):"),
    ("X15", "the discount amount ignored", "        net = price - disc\n", "        net = price\n"),
    ("X16", "an unpaid slip's line not matching Docterz", "    for r in con.execute(\"SELECT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id = s.id AND i.kind = ? \"\n                         \"WHERE s.series = 'xp' AND s.state = 'ok' AND",
     "    for r in con.execute(\"SELECT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id = s.id AND i.kind = ? \"\n                         \"WHERE s.series = 'xp' AND s.state = 'ok' AND s.paid_mode <> '' AND"),
]


def run_inner(fin, db, scr):
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", fin, "--db", db, "--scratch", scr],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    out = p.stdout.decode("utf-8", "replace")
    lines = [ln for ln in out.splitlines() if ln.startswith("  GREEN ") or ln.startswith("  RED ")]
    return out, lines


def mkfin(src, dst, mutate=None):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.db", "*.db-*"))
    if mutate:
        p = os.path.join(dst, "clinic_lists.py")
        s = open(p, encoding="utf-8").read()
        if s.count(mutate[0]) != 1:
            return False
        open(p, "w", encoding="utf-8").write(s.replace(mutate[0], mutate[1]))
    return True


def report(lines_from_inner=()):
    for n, ok, note in res:
        print("  %s %s%s" % ("GREEN" if ok else "RED  ", n, ("" if ok else "  -- " + note)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new")
    ap.add_argument("--control")
    ap.add_argument("--inner")
    ap.add_argument("--portal")
    ap.add_argument("--base")
    ap.add_argument("--db")
    ap.add_argument("--scratch")
    ap.add_argument("--kit")
    ap.add_argument("--root")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.inner:
        try:
            inner(a)
        except Exception as e:                                         # noqa: BLE001
            import traceback
            check("S689 Z the inner walk ran to its end", False, traceback.format_exc()[-280:])
        report()
        print("%d of %d green" % (sum(1 for r in res if r[1]), len(res)))
        return
    fin = os.path.abspath(a.new or a.control)
    scr = os.path.abspath(a.scratch)
    os.makedirs(scr, exist_ok=True)
    only = set(x for x in a.only.split(",") if x)
    out, lines = run_inner(fin, a.db, os.path.join(scr, "i0"))
    if not lines:
        print(out[-2000:])
    for ln in lines:
        res.append((ln[8:].split("  -- ")[0], ln.startswith("  GREEN "), (ln.split("  -- ", 1) + [""])[1]))
    portal_checks(a)
    if a.control:
        report()
        red = sum(1 for r in res if not r[1])
        print("%d S689 check(s) red . %d green" % (red, len(res) - red))
        return
    if a.root and (not only or "builder" in only):
        builder_checks(a, fin, scr)
    if not only or "mutants" in only:
        print("THE MUTANTS -- each must turn at least one S689 check red")
        for mid, what, old, new in MUTANTS:
            d = os.path.join(scr, "m_" + mid)
            if not mkfin(fin, d, (old, new)):
                check("%s mutant '%s' applies (its text found once)" % (mid, what), False)
                continue
            _o, ls = run_inner(d, a.db, os.path.join(scr, "mi_" + mid))
            reds = [ln[8:60] for ln in ls if ln.startswith("  RED ")]
            check("%s mutant caught: %s" % (mid, what), bool(reds), "no check went red" if not reds else "")
            print("   %s %s -> %s" % (mid, what, reds[:2]))
            shutil.rmtree(d, ignore_errors=True)
    report()
    print("%d of %d green" % (sum(1 for r in res if r[1]), len(res)))


if __name__ == "__main__":
    main()
