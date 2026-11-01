#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s691.py -- kit S691_LISTS_FILM_STUDY (01-Nov-2026, the parent, session 374). Runs the REAL finance app on COPIES only.

    --new <fin> --db <copy> --scratch <dir> --kit <kitdir> [--root <root>] [--only inner|builder|mutants]
          every S691 check on the code folder <fin> (the inner walk in its own process), the builder checks (when --root is
          given: make_s691.py re-run on <root> gives the three TO files byte for byte and refuses a changed FROM), the mutants.
          Last line: "N of N green".
    --control <fin> --db <copy> --scratch <dir> --kit <kitdir>
          the CONTROL: the S691 checks on the LIVE code. Last line: "X S691 check(s) red . Y green".
    --inner <fin> --db <copy> --scratch <dir>       (one process: the app is loaded once)

<fin> is a folder holding a whole copy of /root/finance's code (never the database). --db is a COPY of finance.db; the walk copies
it again into --scratch and writes made-up rows to that copy only (clinic IDs W691-nn, names W691 ..., slip numbers from 910001,
the days 10-12 Nov 2027, film bills w691:*). Every check reads made-up rows only (F-1067). Header sign-in is switched on for this
process only. No patient name, no ten-digit number in this file.
"""
import argparse
import hashlib
import io
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile

res = []
D1, D2, D3 = "2027-11-10", "2027-11-11", "2027-11-12"   # far ahead: never a real clinic day when this runs
NOW = "2027-11-20T10:00:00"


def check(name, ok, note=""):
    res.append((name, bool(ok), str(note)[:240]))


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


def seed(con, xs):
    cur = con.cursor()
    sid = {}

    def slip(no, day, cid, name, paid=""):
        cur.execute("INSERT INTO slip (series, slip_no, day, clinic_id, name_seen, state, paid_mode, logged_by, logged_at) "
                    "VALUES ('xp',?,?,?,?,'ok',?,'w691',?)", (no, day, cid, name, paid, day + " 10:00:00"))
        sid[no] = cur.lastrowid

    def item(no, kind, svc, name, side="", price=0, disc=0, sort=1):
        cur.execute("INSERT INTO slip_item (slip_id, kind, service_id, name, side, price_p, sort, discount_p) VALUES (?,?,?,?,?,?,?,?)",
                    (sid[no], kind, svc, name, side, price, sort, disc))

    slip(910001, D1, "W691-01", "W691 One")
    item(910001, "xray", xs, "W691 study", "R", 50000)
    slip(910002, D1, "W691-02", "W691 Two")
    item(910002, "xray", xs, "W691 study", "R", 50000)
    slip(910003, D1, "W691-03", "W691 Three", paid="cash")             # the old room tick: ignored now
    item(910003, "xray", xs, "W691 study", "L", 50000)
    slip(910004, D3, "W691-04", "W691 Four")                           # D3 has no Docterz report
    item(910004, "xray", xs, "W691 study", "R", 50000)
    slip(910005, D2, "W691-05", "W691 Five")                           # full discount: Free
    item(910005, "xray", xs, "W691 study", "R", 50000, 50000)
    slip(910006, D2, "W691-06", "W691 Six")                            # the glucometer: Rs 50 procedure
    item(910006, "proc", None, "RBS Glucometer", "", 5000)
    slip(910007, D2, "W691-07", "W691 Seven")                          # both sides: twice the films
    item(910007, "xray", xs, "W691 study", "B", 50000)
    slip(910010, D1, "W691-10", "W691 Ten")                            # one patient, two slips, one Docterz charge
    item(910010, "xray", xs, "W691 study", "R", 30000)
    slip(910011, D1, "W691-10", "W691 Ten")
    item(910011, "xray", xs, "W691 study", "L", 20000)
    slip(910012, D1, "", "W691 Noid")                                  # no clinic ID
    item(910012, "xray", xs, "W691 study", "", 50000)
    for r in [(D1, "xray", 9101, "W691 One", "W691-01", 50000, "Cash"),
              (D1, "xray", 9102, "W691 Two", "W691-02", 80000, "Cash"),
              (D1, "consult", 9103, "W691 Three", "W691-03", 30000, "Cash"),   # the day's report is in; no X-ray charge for her
              (D2, "xray", 9104, "W691 Six", "W691-06", 5000, "Online Payment"),
              (D2, "xray", 9105, "W691 Seven", "W691-07", 50000, "Split Payment"),
              (D2, "xray", 9106, "W691 Eight", "W691-08", 30000, "Cash"),       # no slip: Docterz only
              (D1, "xray", 9107, "W691 Ten", "W691-10", 50000, "Cash"),
              (D2, "xray", 9108, "W691 Twelve", "W691-12", 40000, "Split Payment")]:   # no slip, paid two ways
        cur.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)", r)
    for src, day, size in (("w691:a", "2027-03-20", "8x10"), ("w691:b", "2027-04-02", "8x10"), ("w691:c", "2027-10-01", "11x14")):
        cur.execute("INSERT INTO xf_purchase (src, size, bill_day, boxes, vendor, seen_at) VALUES (?,?,?,1,'W691 Films',?)",
                    (src, size, day, NOW.replace("T", " ")))
    con.commit()


def row_of(html, cid):
    """The <tr> of a made-up clinic ID (the first one)."""
    for m in re.finditer(r"<tr>(.*?)</tr>", html, re.S):
        if cid in m.group(1):
            return m.group(1)
    return ""


def inner(a):
    fin, scr = os.path.abspath(a.inner), os.path.abspath(a.scratch)
    os.makedirs(scr, exist_ok=True)
    dbp = os.path.join(scr, "w691.db")
    copydb(a.db, dbp)
    raw = sqlite3.connect(dbp)
    raw.row_factory = sqlite3.Row
    used = raw.execute("SELECT COUNT(*) FROM slip WHERE clinic_id LIKE 'W691%' OR slip_no >= 910001 OR name_seen LIKE 'W691%'").fetchone()[0]
    used += raw.execute("SELECT COUNT(*) FROM clinic_day_line WHERE clinic_id LIKE 'W691%' OR business_date >= '2027-01-01'").fetchone()[0]
    used += raw.execute("SELECT COUNT(*) FROM owner_service WHERE name LIKE '%W691%'").fetchone()[0]
    check("S691 W0 the made-up IDs, names, slip numbers and days are unused in the database copy (F-1059)", used == 0, used)
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", CLINICLISTS_NOW=NOW,
                      XRAYFILM_NOW=NOW, ASSETS_DB=os.path.join(scr, "no_such_assets.db"))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                           # noqa: E402
    mf = [n for n, _w in getattr(fa, "_MOUNT_FAILED", [])]
    check("S691 A1 the real finance app mounts with _MOUNT_FAILED empty", mf == [], mf)
    XF = sys.modules.get("xray_film")
    XF.ensure(raw)
    raw.commit()
    xr = raw.execute("SELECT s.service_id, s.films, s.size FROM xf_study s JOIN owner_service o ON o.id = s.service_id "
                     "WHERE s.size='8x10' AND s.both_one=0 AND lower(o.name) NOT LIKE 'both%' AND s.id = "
                     "(SELECT MAX(q.id) FROM xf_study q WHERE q.service_id=s.service_id) ORDER BY s.service_id LIMIT 1").fetchone()
    xs, xf = xr[0], int(xr[1])
    seed(raw, xs)
    c = fa.app.test_client(use_cookies=False)

    def G(path, user="manoj"):
        r = c.get(path, headers={"X-Clinic-User": user} if user else {})
        return r.status_code, (r.get_data(as_text=True) if ".xlsx" not in path else r.get_data())

    def P(path, data, user="manoj", live=True):
        h = {"X-Clinic-User": user}
        if live:
            h["X-Requested-With"] = "fetch"
        r = c.post(path, data=data, headers=h)
        return r.status_code, r.get_data(as_text=True), (r.headers.get("Location") or "")

    tables = [r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]

    def counts():
        return {t: raw.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in tables}

    # ------------------------------------------------------------------ his lists page: Paid from Docterz
    before = counts()
    rng = "?f=%s&t=%s" % (D1, D3)
    s1, hx = G("/finance/slips/lists/xray" + rng)
    s2, hp = G("/finance/slips/lists/proc" + rng)
    s3, bx = G("/finance/slips/lists/xray.xlsx" + rng)
    check("S691 L0 his lists page answers him (both tabs, the Excel)", (s1, s2, s3) == (200, 200, 200), (s1, s2, s3))
    r1, r2, r3, r4, r5, r7 = (row_of(hx, "W691-0%d" % n) for n in (1, 2, 3, 4, 5, 7))
    check("S691 L1 slip = Docterz: Paid shows Docterz's mode (Cash)", ">Cash<" in r1 and "amb" not in r1, r1[-160:])
    check("S691 L2 Docterz charged another amount: amber 'Docterz Rs 800 for the day'", "Docterz ₹800 for the day" in r2 and "amb" in r2, r2[-160:])
    check("S691 L3 the day's report is in, no charge: amber 'Not in Docterz'", "Not in Docterz" in r3 and "amb" in r3, r3[-160:])
    check("S691 L4 no Docterz report for that day yet: 'Docterz not in yet', not amber", "Docterz not in yet" in r4 and "amb" not in r4, r4[-160:])
    check("S691 L5 a full discount: the Paid cell says Free", "<td>Free</td>" in r5, r5[-160:])
    check("S691 L6 a bill paid two ways reads 'Paid (two ways)' -- never 'split' (his ruling of 13-Oct)", "Paid (two ways)" in r7
          and "split" not in hx.lower(), r7[-160:])
    check("S691 L7 the room's old tick is not Paid any more (a ticked slip with no Docterz charge is 'Not in Docterz')",
          "Not in Docterz" in r3 and ">Cash<" not in r3)
    r6p = row_of(hp, "W691-06")
    check("S691 L8 the glucometer: Docterz's Rs 50 X-ray charge pays the Rs 50 procedure line, 'Online Payment' reads UPI",
          ">UPI<" in r6p, r6p[-160:])
    dz6 = row_of(hx, "W691-06")
    check("S691 L9 ... and it is not listed as a Docterz-only X-ray", dz6 == "", dz6[-120:])
    r8 = row_of(hx, "W691-08")
    check("S691 L10 a Docterz charge with no slip is still 'In Docterz only'", "In Docterz only" in r8, r8[-160:])
    m = re.search(r"(\d+) lines? not matching Docterz", hx)
    check("S691 L11 the summary counts the lines not matching Docterz (3 on the X-ray tab: Rs 800, not in Docterz, no clinic ID)",
          bool(m) and m.group(1) == "3" and "not marked paid" not in hx.lower(), m.group(0) if m else "none")
    chips = re.findall(r"<span class='chip'>(?:8×10|11×14): (\d+) (films?)</span>", hx)
    check("S691 L12 the day chips say '1 film' and 'N films' -- never '14 film' (a day with the both-sides line has %d)" % (3 * xf),
          bool(chips) and all((n == "1") == (w == "film") for n, w in chips) and ("%d" % (3 * xf), "films") in chips, chips[:6])
    check("S691 L13 one film is '1 film', none is '0 films'", ("8×10: %s<" % ("1 film" if xf == 1 else "%d films" % xf)) in hx
          and "11×14: 0 films<" in hx)
    rows = []
    try:
        with zipfile.ZipFile(io.BytesIO(bx)) as z:
            rows = z.read("xl/sharedStrings.xml").decode("utf-8") if "xl/sharedStrings.xml" in z.namelist() else \
                "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("xl/worksheets/"))
    except Exception as e:                                             # noqa: BLE001
        rows = str(e)
    check("S691 L14 the Excel's Paid column carries Docterz's words", "Not in Docterz" in rows and "Docterz not in yet" in rows
          and "Not marked paid" not in rows and "split payment" not in rows.lower())   # (the sheet's own ySplit pane attribute is not a word)
    r12 = row_of(hx, "W691-12")
    check("S691 L18 a Docterz-only charge paid two ways reads 'Docterz: Paid (two ways)'", "Docterz: Paid (two ways)" in r12, r12[-160:])
    r10 = [m_.group(1) for m_ in re.finditer(r"<tr>(.*?)</tr>", hx, re.S) if "W691-10" in m_.group(1)]
    check("S691 L16 one patient, two slips on one day (300 + 200), Docterz 500 once: both lines Cash", len(r10) == 2
          and all(">Cash<" in x for x in r10), len(r10))
    r11 = [m_.group(1) for m_ in re.finditer(r"<tr>(.*?)</tr>", hx, re.S) if "W691 Noid" in m_.group(1)]
    check("S691 L17 a slip with no clinic ID matches nothing: 'Not in Docterz' (the day's report is in)", len(r11) == 1
          and "Not in Docterz" in r11[0], len(r11))
    raw.execute("INSERT INTO owner_service (kind, name, status, source, created_by, created_ts, updated_by, updated_ts) "
                "VALUES ('xray','W691 Unsized view','approved','owner','w691','','w691','')")
    nosz = raw.execute("SELECT id FROM owner_service WHERE name='W691 Unsized view'").fetchone()[0]
    raw.execute("INSERT INTO slip (series, slip_no, day, clinic_id, name_seen, state, paid_mode, logged_by, logged_at) "
                "VALUES ('xp', 910008, ?, 'W691-09', 'W691 Nine', 'ok', '', 'w691', ?)", (D2, D2 + " 11:00:00"))
    raw.execute("INSERT INTO slip_item (slip_id, kind, service_id, name, side, price_p, sort, discount_p) VALUES (?, 'xray', ?, "
                "'W691 Unsized view', '', 30000, 1, 0)", (raw.execute("SELECT id FROM slip WHERE slip_no=910008").fetchone()[0], nosz))
    raw.commit()
    before = counts()
    _s, hx2 = G("/finance/slips/lists/xray" + rng)
    r9 = row_of(hx2, "W691-09")
    check("S691 L15 'size not set' links to his rate page's X-rays", "/finance/clinic/sheets?kind=xray" in r9 and "size not set" in r9, r9[-200:])
    after = counts()
    check("S691 N1 the lists page writes nothing", before == after, [t for t in tables if before.get(t) != after.get(t)][:4])

    # ------------------------------------------------------------------ the film log: every billed slip, the bills card
    sl = [e for e in XF.slip_lines(raw, D1, D3) if str(e.get("cid", "")).startswith("W691")]
    check("S691 F1 the film log counts every 'ok' X-ray slip, ticked or not (D775: billed is done)", len(sl) == 9, len(sl))
    sf = XF.slip_films(raw, D1, D3)
    want = 9 * xf                                                      # 910001-005, 010, 011 one study each; the both-sides line twice
    real = sum(e["films"] for e in XF.slip_lines(raw, D1, D3) if e["size"] == "8x10")
    check("S691 F2 the day's slip films are counted from those slips", sf.get("8x10") == real and
          sum(e["films"] for e in sl if e["size"] == "8x10") == want, (sf.get("8x10"), real, want))
    s_, hl = G("/finance/slips/film/list?m=2027-11")
    l3 = row_of(hl, "W691-03")
    l2 = row_of(hl, "W691-02")
    check("S691 F3 the staff X-ray list shows the slips and Docterz's Paid (English for him)", s_ == 200 and "Not in Docterz" in l3
          and "Docterz Rs 800 for the day" in l2, (s_, l3[-80:]))
    s_, hs = G("/finance/slips/film/list?m=2027-11", "shavez")
    check("S691 F4 ... in Hinglish for Shavez, with no rupee figure", s_ == 200 and "Docterz mein nahi" in row_of(hs, "W691-03")
          and "Docterz abhi nahi aaya" in row_of(hs, "W691-04") and "Docterz mein alag raqam" in row_of(hs, "W691-02")
          and "Rs 800" not in hs, s_)
    s_, xs_ = G("/finance/slips/film/list.xlsx?m=2027-11", "shavez")
    try:
        with zipfile.ZipFile(io.BytesIO(xs_)) as z:
            xt = "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("xl/"))
    except Exception as e:                                             # noqa: BLE001
        xt = str(e)
    check("S691 F12 ... and in Shavez's Excel too (no rupee figure)", s_ == 200 and "Docterz mein alag raqam" in xt and "Rs 800" not in xt, s_)
    s_, hg = G("/finance/slips/film/log")
    i = hg.find("FILM BILLS IN THE SCAN APP")
    card = hg[i:i + 3000] if i >= 0 else ""
    card = card[:card.find("</div>") + 200]
    check("S691 F5 the bills card: this financial year only, the count with its date", "2 film bills since 1 Apr 2027" in card
          and "02-Apr" in card and "01-Oct" in card and "20-Mar" not in card, re.sub("<[^>]+>", " ", card)[:200])
    check("S691 F6 ... a link to the Scan App's film bills, for him", "href='/scanapp/xray'" in card)
    s_, hb = G("/finance/slips/film/log", "bhawna")
    check("S691 F7 ... and not for the other checker (the Scan App page is his alone)", s_ == 200 and "/scanapp/xray" not in hb, s_)
    check("S691 F8 the film log's per-study form is retired to a link to his rate page",
          "owner/study" not in hg and "/finance/clinic/sheets?kind=xray" in hg)
    n0 = raw.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0]
    P("/finance/slips/film/owner/study", {"service_id": str(xs), "size": "8x10", "films": "5", "both_one": "0"}, live=False)
    n1 = raw.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0]
    P("/finance/slips/film/owner/study", {"service_id": str(xs), "size": "8x10", "films": "7", "both_one": "0"}, live=False)
    n2 = raw.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0]
    newest = raw.execute("SELECT films FROM xf_study WHERE service_id=? ORDER BY id DESC LIMIT 1", (xs,)).fetchone()[0]
    check("S691 F9 the film log's own study route still saves (5 films now allowed) and refuses 7", (n1 - n0, n2 - n1, newest) == (1, 0, 5),
          (n1 - n0, n2 - n1, newest))
    P("/finance/slips/film/owner/study", {"service_id": str(xs), "size": "8x10", "films": str(xf), "both_one": "0"}, live=False)
    pid0 = raw.execute("SELECT id FROM owner_service WHERE kind='proc' ORDER BY id LIMIT 1").fetchone()[0]
    q0 = raw.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0]
    P("/finance/slips/film/owner/study", {"service_id": str(pid0), "size": "8x10", "films": "1", "both_one": "0"}, live=False)
    q1 = raw.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0]
    check("S691 F10 a film size is never saved on a procedure (the film log's own route)", q1 == q0, q1 - q0)
    import datetime as _dt
    fy = [XF.fy_start(_dt.date(*d)).isoformat() for d in ((2028, 2, 10), (2027, 4, 1), (2027, 3, 31), (2027, 12, 31))]
    check("S691 F11 the financial year starts 1 April (Feb-2028 -> 1-Apr-2027; 31-Mar-2027 -> 1-Apr-2026)",
          fy == ["2027-04-01", "2027-04-01", "2026-04-01", "2027-04-01"], fy)

    # ------------------------------------------------------------------ his rate page: the film on every X-ray
    s_, hr = G("/finance/clinic/sheets?kind=xray")
    i = hr.find("id='it-%d'" % xs)
    li = hr[i:hr.find("</summary>", i)] if i >= 0 else ""
    check("S691 O1 an X-ray line shows its film (8×10 × n)", s_ == 200 and ("8×10 &times; %d" % xf) in li, li[-120:])
    i = hr.find("id='it-%d'" % nosz)
    lu = hr[i:hr.find("</details>", i)] if i >= 0 else ""
    check("S691 O2 a study with no film yet says 'film?' and offers the size inside", "film?" in lu and "action='film'" in lu, lu[:120])
    st, body, _l = P("/finance/clinic/sheets/film", {"id": str(nosz), "kind": "xray", "size": "11x14", "films": "2", "both_one": "1"})
    try:
        import json as _json
        body = _json.loads(body).get("html") or ""
    except ValueError:
        body = ""
    nr = raw.execute("SELECT size, films, both_one FROM xf_study WHERE service_id=? ORDER BY id DESC LIMIT 1", (nosz,)).fetchone()
    check("S691 O3 saving a film writes the film log's study row and redraws the line", st == 200 and "11×14 &times; 2" in body
          and nr is not None and tuple(nr) == ("11x14", 2, 1), (st, tuple(nr) if nr else None))
    pid = raw.execute("SELECT id FROM owner_service WHERE kind='proc' ORDER BY id LIMIT 1").fetchone()[0]
    k0 = raw.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0]
    a1 = P("/finance/clinic/sheets/film", {"id": str(pid), "kind": "proc", "size": "8x10", "films": "1"})[0]
    a2 = P("/finance/clinic/sheets/film", {"id": str(nosz), "kind": "xray", "size": "8x10", "films": "7"})[0]
    a3 = P("/finance/clinic/sheets/film", {"id": str(nosz), "kind": "xray", "size": "9x9", "films": "1"})[0]
    a4 = P("/finance/clinic/sheets/film", {"id": str(nosz), "kind": "xray", "size": "8x10", "films": "1"}, user="bhawna")[0]
    k1 = raw.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0]
    check("S691 O4 refused, nothing written: a procedure, 7 films, a size that is not a film, another login", (a1, a2, a3) == (400, 400, 400)
          and a4 in (302, 401, 403) and k1 == k0, (a1, a2, a3, a4, k1 - k0))
    o0 = raw.execute("SELECT COUNT(*) FROM owner_service").fetchone()[0]
    st, _b, loc = P("/finance/clinic/sheets/add", {"kind": "xray", "name": "W691 New view", "price": "400"}, live=False)
    o1 = raw.execute("SELECT COUNT(*) FROM owner_service").fetchone()[0]
    check("S691 O5 a new X-ray without a film size is refused, nothing added", o1 == o0 and "c=bad" in loc, (o1 - o0, loc[-60:]))
    P("/finance/clinic/sheets/add", {"kind": "xray", "name": "W691 New view", "price": "400", "size": "8x10", "films": "2"}, live=False)
    nv = raw.execute("SELECT id FROM owner_service WHERE name='W691 New view'").fetchone()
    nvs = raw.execute("SELECT size, films, both_one FROM xf_study WHERE service_id=? ORDER BY id DESC LIMIT 1", (nv[0],)).fetchone() if nv else None
    check("S691 O6 ... with 8×10 and 2 films it is added, its film saved", nvs is not None and tuple(nvs) == ("8x10", 2, 0),
          tuple(nvs) if nvs else None)
    P("/finance/clinic/sheets/add", {"kind": "proc", "name": "W691 New proc", "price": "100"}, live=False)
    npr = raw.execute("SELECT id FROM owner_service WHERE name='W691 New proc'").fetchone()
    check("S691 O7 a procedure needs no film (added, no film row)", npr is not None and
          raw.execute("SELECT COUNT(*) FROM xf_study WHERE service_id=?", (npr[0],)).fetchone()[0] == 0)
    P("/finance/clinic/sheets/add", {"kind": "xray", "name": "Both W691 views", "size": "8x10", "films": "1"}, live=False)
    bv = raw.execute("SELECT id FROM owner_service WHERE name='Both W691 views'").fetchone()
    if bv:
        P("/finance/clinic/sheets/film", {"id": str(bv[0]), "kind": "xray", "size": "8x10", "films": "1", "both_one": "1"})
    bb = raw.execute("SELECT both_one FROM xf_study WHERE service_id=? ORDER BY id DESC LIMIT 1", (bv[0],)).fetchone() if bv else None
    check("S691 O8 a 'Both ...' study never takes 'both sides on one film' (it never doubles anyway)", bb is not None and bb[0] == 0, bb)
    _s, hpv = G("/finance/clinic/sheets")
    _s, hxv = G("/finance/clinic/sheets?kind=xray")
    check("S691 O9 the Add row carries film size and films, hidden on the procedures view", "<span id='addfilm' style='display:none'>" in hpv
          and "<span id='addfilm'>" in hxv and "name='size'" in hxv)
    s_, _b = G("/finance/clinic/sheets/api/services")
    check("S691 O10 the chamber screen's read-back door still answers", s_ == 200, s_)


def builder_checks(a, fin, scr):
    kit, root = os.path.abspath(a.kit), os.path.abspath(a.root)
    b1 = os.path.join(scr, "b1")
    shutil.rmtree(b1, ignore_errors=True)
    p = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s691.py"), root, b1], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=120)
    o = p.stdout.decode("utf-8", "replace")
    same = p.returncode == 0 and all(md5f(os.path.join(b1, f)) == md5f(os.path.join(fin, f))
                                     for f in ("owner_sheets.py", "xray_film.py", "clinic_lists.py"))
    check("M1 make_s691.py re-run on the FROM files gives the three TO files byte for byte", same, o[-200:])
    r2 = os.path.join(scr, "r2")
    shutil.rmtree(r2, ignore_errors=True)
    shutil.copytree(root, r2)
    with open(os.path.join(r2, "xray_film.py"), "ab") as fh:
        fh.write(b"\n")
    p2 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s691.py"), r2, os.path.join(scr, "b2")], stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, timeout=120)
    check("M2 a FROM file changed by one byte: the builder stops and writes nothing", p2.returncode != 0
          and not os.path.exists(os.path.join(scr, "b2")))
    p3 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s691.py"), b1, os.path.join(scr, "b3")], stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, timeout=120)
    check("M3 the builder run on its own output stops", p3.returncode != 0 and not os.path.exists(os.path.join(scr, "b3")))


MUTANTS = [
    ("X1", "xray_film.py", "a different Docterz amount taken as paid", "        elif k[1] and k in dz and dz[k][0] == tot:\n",
     "        elif k[1] and k in dz:\n"),
    ("X2", "xray_film.py", "the glucometer rule gone", 'sec = "proc" if (r[2] == "xray" and a == GLUCO_P and (r[0], cid) in gl) else r[2]',
     "sec = r[2]"),
    ("X3", "xray_film.py", "'Online Payment' not read as UPI", '"online payment": "UPI"', '"online payment": "Online"'),
    ("X4", "xray_film.py", "the financial year from 1 January", "day.year if day.month >= 4 else", "day.year if day.month >= 1 else"),
    ("X5", "xray_film.py", "the room's tick gating the film count again",
     "\"WHERE s.series='xp' AND s.state='ok' AND s.day>=? AND s.day<=? ORDER BY s.day, s.slip_no, i.sort, i.id\")\n    marks",
     "\"WHERE s.series='xp' AND s.state='ok' AND s.paid_mode IN ('cash','upi') AND s.day>=? AND s.day<=? ORDER BY s.day, s.slip_no, i.sort, i.id\")\n    marks"),
    ("X6", "xray_film.py", "films per study capped at 4", "FILMS_MAX = 6 ", "FILMS_MAX = 4 "),
    ("X7", "xray_film.py", "'not in yet' said for a day whose report is in", "        elif k[0] in days:\n", "        elif False:\n"),
    ("X8", "xray_film.py", "the Scan App link shown to the other checker", 'SCANAPP_XRAY) if own else ""))', 'SCANAPP_XRAY) if True else ""))'),
    ("X9", "xray_film.py", "last year's bills listed", "WHERE gone_at='' AND bill_day >= ? ORDER BY", "WHERE gone_at='' AND bill_day >= ? OR 1 ORDER BY"),
    ("O1", "owner_sheets.py", "a new X-ray added without its film size", '        if size not in FILM_LABEL:\n            raise ValueError("pick the film size',
     '        if False:\n            raise ValueError("pick the film size'),
    ("O2", "owner_sheets.py", "a 'Both' study allowed one film for both sides", "        both_one = 0                                                   # a",
     "        pass                                                           # a"),
    ("X10", "xray_film.py", "a film saved on a procedure", "SELECT 1 FROM owner_service WHERE id=? AND kind='xray'\", (sid,)).fetchone()\n    if not ok:\n        raise ValueError(\"no such X-ray",
     "SELECT 1 FROM owner_service WHERE id=?\", (sid,)).fetchone()\n    if not ok:\n        raise ValueError(\"no such X-ray"),
    ("C1", "clinic_lists.py", "'not in Docterz' left out of the summary count", 'if e["paid"] in ("differ", "none")', 'if e["paid"] in ("differ",)'),
    ("C2", "clinic_lists.py", "'14 film' again", '    return "%d film" % n if n == 1 else "%d films" % n\n', '    return "%d film" % n\n'),
    ("C3", "clinic_lists.py", "a different Docterz amount not amber", '        return "Docterz %s for the day" % rs(p), True', '        return "Docterz %s for the day" % rs(p), False'),
    ("X11", "xray_film.py", "'split payment' named on the page", '"split payment": "Paid (two ways)"', '"split payment": "Split Payment"'),
    ("X12", "xray_film.py", "staff shown the rupee figure", '"Docterz mein alag raqam" if hi else', '"Docterz Rs 800" if hi else'),
    ("X13", "xray_film.py", "the staff Excel in English", "names=True, lang=lang)   # S691 review 2", "names=True)   # S691 review 2"),
    ("C4", "clinic_lists.py", "a Docterz-only row's mode shown raw", 'dmode=_dzmode(r["mode"]),', 'dmode=(r["mode"] or "").strip(),'),
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
        p = os.path.join(dst, mutate[0])
        s = open(p, encoding="utf-8").read()
        if s.count(mutate[1]) != 1:
            return False
        open(p, "w", encoding="utf-8").write(s.replace(mutate[1], mutate[2]))
    return True


def report():
    for n, ok, note in res:
        print("  %s %s%s" % ("GREEN" if ok else "RED  ", n, ("" if ok else "  -- " + note)))


def main():
    ap = argparse.ArgumentParser()
    for k in ("new", "control", "inner", "db", "scratch", "kit", "root"):
        ap.add_argument("--" + k)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.inner:
        try:
            inner(a)
        except Exception:                                              # noqa: BLE001
            import traceback
            check("S691 Z the inner walk ran to its end", False, traceback.format_exc()[-230:])
        report()
        print("%d of %d green" % (sum(1 for r in res if r[1]), len(res)))
        return
    fin = os.path.abspath(a.new or a.control)
    scr = os.path.abspath(a.scratch)
    os.makedirs(scr, exist_ok=True)
    only = set(x for x in a.only.split(",") if x)
    out, lines = run_inner(fin, a.db, os.path.join(scr, "i0"))
    if not lines:
        print(out[-1500:])
    for ln in lines:
        res.append((ln[8:].split("  -- ")[0], ln.startswith("  GREEN "), (ln.split("  -- ", 1) + [""])[1]))
    if a.control:
        report()
        red = sum(1 for r in res if not r[1])
        print("%d S691 check(s) red . %d green" % (red, len(res) - red))
        return
    if a.root and (not only or "builder" in only):
        builder_checks(a, fin, scr)
    if not only or "mutants" in only:
        print("THE MUTANTS -- each must turn at least one S691 check red")
        for mid, f, what, old, new in MUTANTS:
            d = os.path.join(scr, "m_" + mid)
            if not mkfin(fin, d, (f, old, new)):
                check("%s mutant '%s' applies (its text found once)" % (mid, what), False)
                continue
            _o, ls = run_inner(d, a.db, os.path.join(scr, "mi_" + mid))
            reds = [ln[8:56] for ln in ls if ln.startswith("  RED ")]
            check("%s mutant caught: %s" % (mid, what), bool(reds), "no check went red" if not reds else "")
            print("   %s %s -> %s" % (mid, what, reds[:2]))
            shutil.rmtree(d, ignore_errors=True)
            shutil.rmtree(os.path.join(scr, "mi_" + mid), ignore_errors=True)
    report()
    print("%d of %d green" % (sum(1 for r in res if r[1]), len(res)))


if __name__ == "__main__":
    main()
