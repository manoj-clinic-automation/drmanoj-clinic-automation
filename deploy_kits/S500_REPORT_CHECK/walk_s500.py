#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s500.py -- kit S500_REPORT_CHECK: the walk (the brief's section 4), on the server, on scratch copies only.

    python3 -B walk_s500.py --kit DIR --work /tmp/... --fin-new DIR --fin-old DIR --por DIR --marg-ingest DIR
                            --db finance.db --adb assets.db --spine spine.db --duty-map DUTY_MAP.json(v9)

  fin-new / fin-old   scratch copies of /root/finance: NEW carries the seven files of the kit, OLD is the box as it is (the
                      three new files ABSENT from it).  Each side's spine/ sub-folder (spine/*.py, *.json) is that side's SPINE_DIR.
  por                 a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there.
  marg-ingest         a scratch copy of /root/marg_ingest/*.py (the page reads the bill chain through marg_take.chain_state).
  db / adb / spine    backup-API copies; every section works on its OWN further copy (rule 3); the walk's rows are keyed W500 and
                      found by key, never by counting.

THE WALK DAY is Wednesday 12-03-2031 (not the 1st-7th of its month, so the two month-report rows stay off the page); its due day is
Tuesday 11-03-2031.  The walk's mi_file rows carry md5 'W500...', received_at and stamp on the walk day, date_from = date_to = the due
day; its stock_snapshot reference rows carry item names 'W500 REF nnn' on the three days before the due day (as_on dd-mm-yyyy).  Nothing
of the walk can meet a real row.

Each side runs in its own process ("fn": sections 1-9 by function and by route with header auth; "eye": section 10, signed in through
the portal as each login), every one with ORDER_PUSH_STUB (a scratch file), a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB (a scratch
file): no walk can reach a real phone.  Each section's named control is the same probe on the OLD side and must go red there.
Nothing is imported from inside deploy_kits (rule 11).  No person, phone or account number is in this file.
"""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

TAG = "W500JSON "
MAP9_MD5 = "2016244829b4c70c00f1c59b0250ee35"
WALK_DAY = dt.date(2031, 3, 12)                 # a Wednesday
DUE_DAY = dt.date(2031, 3, 11)                  # the Tuesday before
REF_DAYS = (dt.date(2031, 3, 8), dt.date(2031, 3, 9), dt.date(2031, 3, 10))
SUNDAY = dt.date(2031, 3, 16)
PICS = ("menu_sales", "sale_dates", "sale_full", "sale_two", "sale_view", "store_ticks", "save_bar", "menu_stock", "store_whole",
        "report_menu", "only_total", "view_btn", "stock_view")
HROLE = {"shavez": "manager", "manoj": "doctor", "amir": "staff", "darpan": "staff", "w500none": "staff"}
USERS = {"shavez": "manager", "amir": "staff", "darpan": "staff", "shivani": "staff", "alisha": "staff", "reception": "staff",
         "bhawna": "doctor", "manoj": "doctor"}
# the salt card's words this kit changes in amir_day.py (OLD -> NEW), and the stage-A proof's rows (F-801: OLD judges Amir's vouchers on
# the FIRST closing after them, NEW on the NEWEST -- so the items it names differ); a page of Amir's that differs ONLY by these is explained
SALT_WORDS = (" &mdash; Excel mein (text nahi)", "<b>Excel</b> mein nikaaliye: text file server nahi padhta.", "Text ya Excel, dono chalte hain.", " (Excel)")
PROOF_RE = re.compile(r"<span class='big bad'>([^<]*)</span>(?:\s*<[^>]+>)*?\s*<span class=sub>(Marg mein [^<]*)</span>")
N, FAILS, NOTES = [0], [], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def steady(h):
    h = re.sub(r"\b\d{1,2}:\d\d(:\d\d)?\b", "HH:MM", h or "")
    return re.sub(r"\b[0-9a-f]{16,}\b", "HEX", h)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def ins(con, table, row):
    """INSERT the walk's own row; a NOT NULL column with no default that the row does not name gets '' (text) or 0."""
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(cols), ", ".join("?" * len(cols))), [row[c] for c in cols])
    return cur.lastrowid


def dmy(d):
    return d.strftime("%d-%m-%Y")


def has(h, *words):
    return {w: (w in (h or "")) for w in words}


# ============================================================================================================== the "fn" probe (1-9)
def probe_fn():
    FIN, WORK, SIDE, DB0 = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W500_DB0"))
    NEW = SIDE == "new"
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    out = dict(side=SIDE)
    READINGS = os.environ["SPINE_READINGS"]
    STUB = os.environ["REPORTS_NTFY_STUB"]
    TOKEN = os.environ["FINANCE_MARG_TOKEN"]
    OFFDIR = os.environ["REPORTS_WATCH_OFF_DIR"]

    def mk(name):
        p = os.path.join(WORK, "w500_%s.db" % name)
        copydb(DB0, p)
        c = sqlite3.connect(p, timeout=60)
        c.row_factory = sqlite3.Row
        return p, c

    def stub_lines():
        try:
            return [json.loads(l) for l in open(STUB, encoding="utf-8") if l.strip()]
        except FileNotFoundError:
            return []

    def stub_clear():
        open(STUB, "w").close()

    def reading(md5, family, ok, failed=(), **data):
        with open(os.path.join(READINGS, md5 + ".json"), "w") as fh:
            json.dump(dict(md5=md5, family=family, ok=ok, failed=list(failed), reader="S331.1", data=data), fh)
    import finance_app as fa                                            # noqa: E402
    import reports_tile as RT                                           # noqa: E402
    import stock_app as SA                                              # noqa: E402
    import order_rules as OR                                            # noqa: E402
    import amir_day as AD                                               # noqa: E402
    for m in (RT, SA, OR, AD):
        assert m.__file__.startswith(FIN), m.__file__
    W = None
    if NEW:
        import reports_watch as W                                       # noqa: E402
        import reports_guide as G                                       # noqa: E402
        assert W.__file__.startswith(FIN) and G.__file__.startswith(FIN)
    cl = fa.app.test_client()
    IST = RT.IST
    DAY, Y = WALK_DAY, DUE_DAY
    y_iso, day_iso = Y.isoformat(), DAY.isoformat()

    def at(h, m=0, d=DAY):
        return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=IST)

    def H(u):
        return {"X-Clinic-User": u, "X-Clinic-Role": HROLE[u]}

    def refs(c, days=REF_DAYS, n=379):
        for d in days:
            for i in range(n):
                ins(c, "stock_snapshot", dict(as_on=dmy(d), item="W500 REF %03d" % i, qty=(0 if i < 125 else 3), packing="1*10", pack_size=10,
                                              loaded_at="%sT06:11:00" % (d + dt.timedelta(days=1)).isoformat(), source="W500 walk"))
        c.commit()

    def mi(c, md5, typ, hm, verdict="VERIFIED", variant="", df=y_iso, dto=y_iso, reason="", pc="", stamp="", day=DAY):
        ins(c, "mi_file", dict(md5=md5, type=typ, variant=variant, date_from=df, date_to=dto, verdict=verdict, reason=reason, pc_verdict=pc,
                               server_name=md5 + ".xls", stamp=stamp, received_at="%sT%s+05:30" % (day.isoformat(), hm), source="W500"))
        c.commit()

    def pair(s):
        rows = {r["key"]: r for r in s["rows"] if r.get("pair")}
        return rows["SALE_BILLWISE"], rows["STOCK_CLOSING"]

    def row_view(r):
        return dict(state=r.get("state"), count=r.get("count"), zero=r.get("zero"), s500=r.get("s500"), loose=r.get("loose"), reason_hi=r.get("reason_hi"))
    FULL = [{"units": 0.0}] * 130 + [{"units": 4.0}] * 250
    SHORT = FULL[130:]

    # ---------------------------------------------------------------- 2  F-799 on the page
    s2 = {}
    _p, c = mk("f799")
    refs(c)
    mi(c, "W500k1", "STOCK_CLOSING", "09:39:05", variant="TOTALS", stamp="20310312-093902")
    reading("W500k1", "STOCK_CLOSING", True, items=SHORT)
    mi(c, "W500k2", "STOCK_CLOSING", "09:39:30", variant="TOTALS", stamp="20310312-093927")
    reading("W500k2", "STOCK_CLOSING", True, items=SHORT)
    s = RT.status(c, DAY, at(9, 45))
    h = RT.render(s)
    s2["one"] = row_view(pair(s)[1])
    s2["one_html"] = has(h, "Galat hai", "koshish 1 / 2", "Khali stock wale item nahi aaye", "Ek koshish aur hai", "/finance/reports/aaj/kaise/stock", "250 items")
    mi(c, "W500k3", "STOCK_CLOSING", "09:50:00", variant="TOTALS", stamp="20310312-095000")
    reading("W500k3", "STOCK_CLOSING", True, items=SHORT)
    s = RT.status(c, DAY, at(9, 55))
    h = RT.render(s)
    s2["two"] = row_view(pair(s)[1])
    s2["two_html"] = has(h, "Doosri baar bhi galat", "Doctor sahab", "Ek koshish aur hai")
    s2["two_line"] = s["line"]
    mi(c, "W500k4", "STOCK_CLOSING", "09:58:00", variant="TOTALS", stamp="20310312-095800")
    reading("W500k4", "STOCK_CLOSING", True, items=FULL)
    s = RT.status(c, DAY, at(10, 5))
    h = RT.render(s)
    s2["full"] = row_view(pair(s)[1])
    s2["full_html"] = has(h, "Sahi hai", "380 item, khali stock wale bhi")
    c.close()
    _p, c = mk("f799b")
    refs(c)
    mi(c, "W500e1", "STOCK_CLOSING", "15:02:00", variant="DEFAULT", day=Y)           # the afternoon before: not this morning's try
    s = RT.status(c, DAY, at(7, 0))
    s2["eve"] = row_view(pair(s)[1])
    c.close()
    out["s2"] = s2

    # ---------------------------------------------------------------- 3  not the totals list / not the whole store
    s3 = {}
    _p, c = mk("whole")
    refs(c)
    mi(c, "W500n1", "STOCK_CLOSING", "08:00:00", variant="DEFAULT", stamp="20310312-080000")
    s3["default"] = row_view(pair(RT.status(c, DAY, at(8, 5)))[1])
    mi(c, "W500n2", "STOCK_CLOSING", "08:10:00", variant="TOTALS", stamp="20310312-081000")
    reading("W500n2", None, None)
    s3["nofam"] = row_view(pair(RT.status(c, DAY, at(8, 15)))[1])
    c.close()
    out["s3"] = s3

    # ---------------------------------------------------------------- 4  the sale report
    s4 = {}
    _p, c = mk("sale")
    mi(c, "W500m1", "SALE_BILLWISE", "09:00:00", variant="SUMMARY1", stamp="20310312-090000")
    s = RT.status(c, DAY, at(9, 2))
    h = RT.render(s)
    s4["summary"] = row_view(pair(s)[0])
    s4["summary_html"] = has(h, "Step 3 dobara kijiye", "/finance/reports/aaj/pic/sale_two.jpg")
    mi(c, "W500m2", "SALE_BILLWISE", "09:05:00", variant="DETAIL", stamp="20310312-090500")
    reading("W500m2", "SALE_BILLWISE", True, bills=[{}] * 24)
    s = RT.status(c, DAY, at(9, 8))
    s4["detail"] = row_view(pair(s)[0])
    s4["detail_html"] = has(RT.render(s), "Sahi hai")
    c.close()
    out["s4"] = s4

    # ---------------------------------------------------------------- 5  F-788
    s5 = {}
    _p, c = mk("f788")
    s5["before"] = row_view(pair(RT.status(c, DAY, at(9, 0)))[0])
    mi(c, "W500r1", "SALE_BILLWISE", "09:05:00", verdict="REFUSED", df="", dto="", pc="REFUSED", reason="")
    mi(c, "W500r2", "SALE_BILLWISE", "09:06:00", verdict="REFUSED", df="2031-02-10", dto=y_iso, reason="deep parse failed: truncated")
    s = RT.status(c, DAY, at(9, 8))
    s5["after"] = row_view(pair(s)[0])
    s5["after_html"] = has(RT.render(s), "manzoor nahi hui")
    s5["after_line"] = s["line"]
    c.close()
    _p, c = mk("f788b")
    tab = c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='marg_push_staging'").fetchone() is not None
    s5["staging_table"] = tab
    if not tab:
        c.execute("CREATE TABLE marg_push_staging (id INTEGER PRIMARY KEY, received_at TEXT NOT NULL, status TEXT, survey_json TEXT, filename_hint TEXT)")
    ins(c, "marg_push_staging", dict(received_at="%sT09:20:00" % day_iso, status="rejected", survey_json=json.dumps({"error": "W500 refused: not a Marg export"}),
                                     filename_hint="W500.xls"))
    c.commit()
    s = RT.status(c, DAY, at(9, 30))
    s5["staging"] = row_view(pair(s)[0])
    s5["staging_html"] = has(RT.render(s), "manzoor nahi hui")
    s5["staging_line"] = s["line"]
    c.close()
    out["s5"] = s5

    # ---------------------------------------------------------------- 6  the floor (on the app's own copy)
    s6 = {}
    A = os.environ["FINANCE_DB"]
    ca = sqlite3.connect(A, timeout=60)
    ca.row_factory = sqlite3.Row
    r = ca.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
    s6["staff_on"] = bool(r and "|" in str(r[0] or ""))
    import aaj_floor                                                    # noqa: E402
    s6["floor_day"] = aaj_floor.day(ca)
    chain = RT._s482_chain(ca) or {}
    s6["chain_read"] = bool(chain)
    pre = [g for g in (chain.get("lines") or []) if str(g["between"][1]) < s6["floor_day"]]
    if not pre:
        if os.environ["MARG_INGEST_DIR"] not in sys.path:
            sys.path.append(os.environ["MARG_INGEST_DIR"])
        import marg_take                                                # noqa: E402 -- the scratch copy: its own CREATE TABLE IF NOT EXISTS
        ca.execute(marg_take.CHAIN_DDL)
        ins(ca, "mi_bill_chain", dict(series="W", day="2026-09-10", first_no=500002, last_no=500003, n_bills=2, gap_before="W500001", gap_inside="",
                                      empty=0, source_md5="W500", computed_at="2026-09-10T23:00:00"))
        ca.commit()
        chain = RT._s482_chain(ca) or {}
        pre = [g for g in (chain.get("lines") or []) if str(g["between"][1]) < s6["floor_day"]]
    post = [g for g in (chain.get("lines") or []) if str(g["between"][1]) >= s6["floor_day"]]
    s6["pre"], s6["post"] = [g["text_hi"] for g in pre], [g["text_hi"] for g in post]
    s6["floor_for"] = {}
    for who in ("shavez", "manoj"):
        with fa.app.test_request_context("/finance/reports/aaj", headers=H(who)):
            u, _err = fa.require("viewer", "maker", "checker")
            s6["floor_for"][who] = RT._s500_floor(ca, u) if NEW else "n/a"
        hp = cl.get("/finance/reports/aaj", headers=H(who)).get_data(as_text=True)
        s6["page_%s" % who] = dict(pre=[(_html.escape(t, quote=True) in hp) or (t in hp) for t in s6["pre"]],
                                   post=[(_html.escape(t, quote=True) in hp) or (t in hp) for t in s6["post"]])
        js = cl.get("/finance/reports/aaj/api/status", headers=H(who)).get_json(silent=True) or {}
        s6["line_%s" % who] = js.get("line")
    out["s6"] = s6

    # ---------------------------------------------------------------- 7  the guide (routes)
    s7 = {}
    for kind in ("sale", "stock"):
        r = cl.get("/finance/reports/aaj/kaise/%s" % kind, headers=H("shavez"))
        hh = r.get_data(as_text=True)
        m = re.search(r"<ol class=gs>(.*?)</ol>", hh, re.S)
        s7[kind] = dict(code=r.status_code, li=(m.group(1).count("<li>") if m else -1), refresh=("http-equiv=refresh" in hh),
                        due=(RT._ddmm(RT._due_day(RT._today())) in hh), signed=("Kaise banayein" in hh), words=has(hh, "REPORT", "Sahi report ki pehchaan"))
    pics = {}
    for n in PICS:
        r = cl.get("/finance/reports/aaj/pic/%s.jpg" % n, headers=H("shavez"))
        b = r.get_data()
        pics[n] = dict(code=r.status_code, mime=r.mimetype, head=b[:2].hex(), same=(NEW and b == (G.pic(n) or b"x")), cache=r.headers.get("Cache-Control", ""))
    s7["pics"] = pics
    s7["nope"] = cl.get("/finance/reports/aaj/pic/nope.jpg", headers=H("shavez")).status_code
    r = cl.get("/finance/reports/aaj/kaise/x", headers=H("shavez"))
    s7["kx"] = [r.status_code, (r.headers.get("Location") or "").replace("http://localhost", "")]
    s7["none"] = {}
    for p in ("/finance/reports/aaj", "/finance/reports/aaj/kaise/sale", "/finance/reports/aaj/pic/sale_two.jpg"):
        r = cl.get(p, headers=H("w500none"))
        s7["none"][p] = [r.status_code, (r.headers.get("Location") or "").replace("http://localhost", "")]
    out["s7"] = s7

    # ---------------------------------------------------------------- 8  the snapshot door (the app's own copy: FINANCE_DB)
    s8 = {}
    if NEW:
        W.ensure(ca)
    refs(ca, days=(dt.date(2031, 3, 8), dt.date(2031, 3, 9)))
    TH = {"X-Finance-Marg": TOKEN, "Content-Type": "application/json"}

    def push(as_on, n, source="push_snapshot W500 walk"):
        body = dict(as_on=as_on, source=source, items=[dict(item="W500 REF %03d" % i, qty=(0 if i < 125 else 3), packing="1*10", pack_size=10) for i in range(n)])
        r = cl.post("/finance/stock/api/snapshot", data=json.dumps(body), headers=TH)
        return [r.status_code, r.get_json(silent=True) or {}]

    def rows(as_on):
        return dict(snapshot=ca.execute("SELECT COUNT(*) FROM stock_snapshot WHERE as_on=?", (as_on,)).fetchone()[0],
                    feed=ca.execute("SELECT COUNT(*) FROM stock_feed WHERE as_on=?", (as_on,)).fetchone()[0],
                    expected=(ca.execute("SELECT COUNT(*) FROM stock_expected WHERE as_on=?", (as_on,)).fetchone()[0]
                              if ca.execute("SELECT 1 FROM sqlite_master WHERE name='stock_expected'").fetchone() else None))
    s8["eve"] = push("10-03-2031", 379)
    s8["short"] = push("11-03-2031", 250)
    s8["short_rows"] = rows("11-03-2031")
    s8["full"] = push("11-03-2031", 379)
    s8["full_rows"] = rows("11-03-2031")
    s8["expected"] = push("11-03-2031", 200, source="push_expected W500 walk pur_to=2031-03-11 base=W500")
    s8["expected_rows"] = rows("11-03-2031")
    if NEW:
        ca.execute("UPDATE setting SET value='0' WHERE key='reports.closing_min_share'")
        ca.commit()
    s8["off"] = push("12-03-2031", 250)
    s8["off_rows"] = rows("12-03-2031")
    if NEW:
        ca.execute("UPDATE setting SET value='90' WHERE key='reports.closing_min_share'")
        ca.commit()
    out["s8"] = s8

    # ---------------------------------------------------------------- 8b  F-801: the voucher proof
    s8b = {}
    _p, c = mk("proof")
    SA._voucher_ensure(c)
    SA._feed_ensure(c)
    ROOT = 9500001
    ITEM = "W500 PROOF ITEM"
    ins(c, "stock_voucher_line", dict(count_id=ROOT, round_no=1, kind="A", batch_no=1, section="Orthotics", item=ITEM, change=-10, marg_to=90, made_at="2031-03-08T12:00:00", line_no=1))
    ins(c, "stock_voucher_entered", dict(count_id=ROOT, round_no=1, kind="A", batch_no=1, marg_voucher_no="W500V1", at="2031-03-09T10:00:00", by_user="W500"))
    for as_on, marg, exp, rcv in (("07-03-2031", 100, 100, "2031-03-07T06:11:00"), ("10-03-2031", 100, 100, "2031-03-10T06:11:00"), ("11-03-2031", 90, 100, "2031-03-11T06:11:00")):
        ins(c, "stock_feed", dict(as_on=as_on, source="push_snapshot W500 proof", item=ITEM, qty=marg, received_at=rcv))
        ins(c, "stock_feed", dict(as_on=as_on, source="push_expected W500 proof pur_to=%s-%s-%s base=W500" % (as_on[6:10], as_on[3:5], as_on[0:2]),
                                  item=ITEM, qty=exp, received_at=rcv))
    c.commit()
    batches = SA._s446_batches(c, ROOT)
    ent = SA._s446_entered(c, ROOT)
    res = SA._s446_proof(c, ROOT, list(batches), ent, batches)
    s8b["proof"] = {k: res.get(k) for k in ("state", "as_before", "as_after", "items")}
    s8b["rows"] = [dict(item=r.get("item"), moved=r.get("moved"), need=r.get("need")) for r in (res.get("rows") or [])]
    c.close()
    out["s8b"] = s8b

    # ---------------------------------------------------------------- 8c  the salt card's words
    s8c = {}
    src = open(os.path.join(FIN, "amir_day.py"), encoding="utf-8").read()
    s8c["file"] = has(src, "Ek export aur: SALT WISE ITEM LIST", "Text ya Excel, dono chalte hain", "text nahi", "nahi padhta", '(Excel)")', "Excel mein (text nahi)")
    ins(ca, "purchase_salt_task", dict(section="rename", seq=950001, a="W500 WALK ITEM", b="W500 SALT", done=1, done_by="W500",
                                       done_at=dt.datetime.now().replace(microsecond=0).isoformat()))       # on the app's own copy: a tick newer than the last list
    ca.commit()
    hh = cl.get("/finance/amir/step/6", headers=H("amir")).get_data(as_text=True)
    s8c["page"] = has(hh, "Ek export aur: SALT WISE ITEM LIST", "Text ya Excel, dono chalte hain", "Excel mein (text nahi)", "text file server nahi padhta")
    s8c["page_code"] = 200 if "Ek export aur" in hh or "Amir" in hh else 0
    out["s8c"] = s8c

    # ---------------------------------------------------------------- 9  the watch (NEW only -- the module is not on OLD)
    s9 = {}
    if NEW:
        def two_wrong(c):
            refs(c)
            mi(c, "W500w1", "STOCK_CLOSING", "08:00:00", variant="TOTALS", stamp="20310312-080000")
            reading("W500w1", "STOCK_CLOSING", True, items=SHORT)
            mi(c, "W500w2", "STOCK_CLOSING", "08:10:00", variant="TOTALS", stamp="20310312-081000")
            reading("W500w2", "STOCK_CLOSING", True, items=SHORT)

        def alerts(c):
            return [dict(r) for r in c.execute("SELECT day, key, kind, sent_at FROM marg_report_alert ORDER BY key")]
        _p, c = mk("watch1")
        W.ensure(c)
        two_wrong(c)
        stub_clear()
        s9["t1"] = W.tick(c, now=at(8, 20))
        s9["t1_stub"] = stub_lines()
        s9["t1_rows"] = alerts(c)
        s9["t2"] = W.tick(c, now=at(8, 30))
        s9["t2_stub_n"] = len(stub_lines())
        s9["t2_html"] = has(RT.render(RT.status(c, DAY, at(8, 31))), "khabar chali gayi hai", "Doosri baar bhi galat")
        c.close()
        _p, c = mk("watch2")
        W.ensure(c)
        stub_clear()
        s9["late950"] = W.tick(c, now=at(9, 50))
        s9["late950_stub_n"] = len(stub_lines())
        s9["late1000"] = W.tick(c, now=at(10, 0))
        s9["late1000_stub"] = stub_lines()
        c.close()
        _p, c = mk("watch3")
        W.ensure(c)
        mi(c, "W500p1", "SALE_BILLWISE", "09:40:00", variant="DETAIL", stamp="20310312-094000")
        mi(c, "W500p2", "STOCK_CLOSING", "09:41:00", variant="TOTALS", stamp="20310312-094100")
        stub_clear()
        s9["pend_states"] = [r["state"] for r in pair(RT.status(c, DAY, at(10, 0)))]
        s9["pend1000"] = W.tick(c, now=at(10, 0))
        s9["pend1000_stub_n"] = len(stub_lines())
        s9["pend1020"] = W.tick(c, now=at(10, 20))
        s9["pend1020_stub_n"] = len(stub_lines())
        s9["pend1030"] = W.tick(c, now=at(10, 30))
        s9["pend1030_stub"] = stub_lines()
        c.close()
        _p, c = mk("watch4")
        W.ensure(c)
        two_wrong(c)
        saved = os.environ.pop("REPORTS_NTFY_STUB")
        try:
            s9["nostub"] = W.tick(c, now=at(8, 20))
            s9["nostub_rows"] = alerts(c)
            mi(c, "W500w4", "STOCK_CLOSING", "08:25:00", variant="TOTALS", stamp="20310312-082500")
            reading("W500w4", "STOCK_CLOSING", True, items=FULL)
            s9["withdrawn"] = W.tick(c, now=at(8, 30))
            s9["withdrawn_rows"] = alerts(c)
        finally:
            os.environ["REPORTS_NTFY_STUB"] = saved
        c.close()
        _p, c = mk("watch5")
        W.ensure(c)
        two_wrong(c)
        s9["sunday"] = W.tick(c, now=at(9, 0, d=SUNDAY))
        c.execute("UPDATE setting SET value='off' WHERE key='reports.alert'")
        c.commit()
        s9["alert_off"] = W.tick(c, now=at(8, 20))
        s9["alert_off_html"] = has(RT.render(RT.status(c, DAY, at(8, 21))), "Doctor sahab ko bataiye", "khabar ja rahi hai")
        c.execute("UPDATE setting SET value='on' WHERE key='reports.alert'")
        c.commit()
        offp = os.path.join(OFFDIR, "REPORTS_WATCH_OFF")
        open(offp, "w").close()
        try:
            s9["file_off"] = W.tick(c, now=at(8, 20))
            s9["file_off_html"] = has(RT.render(RT.status(c, DAY, at(8, 21))), "Doctor sahab ko bataiye", "khabar ja rahi hai")
        finally:
            os.remove(offp)
        s9["file_on_again_html"] = has(RT.render(RT.status(c, DAY, at(8, 22))), "Doctor sahab ko khabar ja rahi hai")
        c.close()
    _p, c = mk("tick")
    if hasattr(OR, "_s500_reports"):
        s9["or_tick"] = OR._s500_reports(c, {})
    else:
        s9["or_tick"] = "no _s500_reports"
    c.close()
    out["s9"] = s9

    # ---------------------------------------------------------------- 1  the selftests, both pythons (subprocesses, this side's folder)
    s1 = {}
    env = dict(os.environ)
    env.pop("REPORTS_NTFY_STUB", None)
    for py in ("/usr/bin/python3", "/root/wa/venv/bin/python3"):
        tag = "sys" if py.startswith("/usr") else "venv"
        p = subprocess.run([py, "-B", os.path.join(FIN, "reports_tile.py")], cwd=FIN, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=600)
        m = re.search(r"reports_tile selftest: (\d+) checks, (\d+) failures", p.stdout)
        s1["tile_" + tag] = [p.returncode, m.group(1) if m else None, m.group(2) if m else None, p.stdout.strip().splitlines()[-1][:200] if p.stdout.strip() else ""]
        if NEW:
            p = subprocess.run([py, "-B", os.path.join(FIN, "reports_watch.py"), "--selftest"], cwd=FIN, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, timeout=300)
            m = re.search(r"reports_watch selftest: (\d+) failure", p.stdout)
            s1["watch_" + tag] = [p.returncode, m.group(1) if m else None]
    out["s1"] = s1
    ca.close()
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "eye" probe (10)
def probe_eye():
    FIN, POR, DB, SIDE = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE"))
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import aaj_kaam as AK                                               # noqa: E402
    assert AK.__file__.startswith(FIN)
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W500J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    out = dict(side=SIDE)
    ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    sc, info = AK.connect(DB, mode="staff")
    out["floor"] = info.get("floor")
    out["floor_bad"] = info.get("bad")

    def page(path, ck):
        body, code, loc = "", 0, ""
        for _hop in range(4):
            rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
            code, loc = rr2.status_code, (rr2.headers.get("Location") or "").replace(BASE, "")
            if code in (301, 302, 303) and loc.startswith("/finance/"):
                path = loc
                continue
            body = rr2.get_data(as_text=True)
            break
        return code, body, loc
    DOORS = ("/finance/reports/aaj", "/finance/reports/aaj/api/status")
    eye = {}
    for who, prole in USERS.items():
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        ck = "clinic_sso=" + tok
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": ck})
        home = r.get_data(as_text=True)
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', home)]
        pages = {"home": md5b(steady(home.replace(tok, "TOKEN")).encode())}
        rows, doors = [], set(DOORS)
        mine = {who, (dm.get("shared") or {}).get(who)}
        con_due = ro if prole == "doctor" else sc
        for du in dm.get("duties") or []:
            if du.get("person") not in mine:
                continue
            row = {"id": du.get("id"), "tile": du.get("tile"), "tile_seen": (du.get("tile") in seen) if du.get("tile") else None, "door": du.get("door")}
            q = str(du.get("due_sql") or "").strip().rstrip(";")
            n = None
            if q:
                for tag, cx in (("due_n", con_due), ("plain_n", ro)):
                    try:
                        rr = cx.execute(q).fetchone()
                        row[tag] = int((rr[0] if rr else 0) or 0)
                        if tag == "due_n":
                            row["since"] = rr[1] if rr is not None and len(rr) > 1 else None
                    except Exception as e:                              # noqa: BLE001
                        row[tag] = "ERR " + str(e)[:80]
                n = row.get("due_n")
            door, mark = du.get("door"), du.get("door_marker")
            if door and str(door).startswith("/finance/"):
                doors.add(str(door))
                if mark and isinstance(n, int) and n > 0:
                    body = page(str(door), ck)[1]
                    row["door_seen"] = (mark in body) or (mark in _html.unescape(body))
            rows.append(row)
        texts, salted = {}, {}
        for d in sorted(doors):
            code, body, loc = page(d, ck)
            pages[d] = "%s %s" % (code, md5b(steady(body.replace(tok, "TOKEN")).encode()))
            b2 = steady(body.replace(tok, "TOKEN"))              # the same page with the salt card's words and the proof's rows taken out
            for w in SALT_WORDS:
                b2 = b2.replace(w, "")
            if d.startswith("/finance/amir"):
                texts[d + " proof"] = [list(x) for x in PROOF_RE.findall(body)]
                b2 = PROOF_RE.sub("", b2)
            salted[d] = "%s %s" % (code, md5b(b2.encode()))
            if d == "/finance/reports/aaj":
                texts[d] = dict(code=code, loc=loc, signed=("Signed in: %s" % who) in body, title=("Aaj ki reports" in body))
        eye[who] = dict(status=r.status_code, n_tiles=len(seen), tile_reports=("Aaj ki reports" in seen), duties=rows, pages=pages, salted=salted, texts=texts)
    ro.close()
    sc.close()
    out["eye"] = eye
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-eye"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_eye()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--fin-new", "--fin-old", "--por", "--marg-ingest", "--db", "--adb", "--spine", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    m9raw = open(a.duty_map, "rb").read()
    check("the duty map beside the kit is v9 (md5 %s); this kit changes no duty" % md5b(m9raw)[:8], md5b(m9raw) == MAP9_MD5 and json.loads(m9raw.decode("utf-8"))["version"] == 9)
    for f in ("reports_watch.py", "reports_guide.py", "reports_guide_pics.py"):
        check("OLD side has no %s; NEW side has it" % f, (not os.path.exists(os.path.join(a.fin_old, f))) and os.path.exists(os.path.join(a.fin_new, f)))
    # the walk's own sign-in: a random secret and its own user store, in the scratch portal folder
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W500 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for role in ("staff", "manager", "doctor"):
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])
    token = secrets.token_hex(24)

    def run(mode, side, fin):
        wd = os.path.join(Wd, "%s_%s" % (mode, side))
        for sub in ("nosso", "noring", "readings", "noarchive", "off"):
            os.makedirs(os.path.join(wd, sub))
        dbp, adbp, spp = [os.path.join(wd, "w500_%s.db" % x) for x in ("app", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W500_DB0=a.db,
                   SPINE_DIR=os.path.join(fin, "spine"), SPINE_READINGS=os.path.join(wd, "readings"), MI_ARCHIVE=os.path.join(wd, "noarchive"),
                   MARG_INGEST_DIR=a.marg_ingest, REPORTS_WATCH_OFF_DIR=os.path.join(wd, "off"),
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "eye" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
                   CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret,
                   DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, W500J=json.dumps(dict(pw=pw)), FINANCE_MARG_TOKEN=token,
                   RING_PORTAL_DIR=os.path.join(wd, "noring"), ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"), REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"),
                   ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
                   CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE", "FINANCE_CRON_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
            for l in p.stdout.splitlines()[-40:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    NW, OL = run("fn", "new", a.fin_new), run("fn", "old", a.fin_old)
    if not check("both function probes ran to the end (NEW = the box + S500, OLD = the box as it is), each on its own copies", NW is not None and OL is not None):
        return finish()

    # ------------------------------------------------------------------------------------------------------------------------------- 1
    print("-- 1  the selftests on both pythons")
    n1, o1 = NW["s1"], OL["s1"]
    check("reports_watch.py --selftest: 0 failure(s) on /usr/bin/python3 (%s) and the venv (%s)" % (n1.get("watch_sys"), n1.get("watch_venv")),
          n1.get("watch_sys", [1])[0] == 0 and n1.get("watch_sys", [1, ""])[1] == "0" and n1.get("watch_venv", [1])[0] == 0 and n1.get("watch_venv", [1, ""])[1] == "0")
    check("NEW reports_tile.py: 54 checks, 0 failures on both pythons (%s / %s)" % (n1["tile_sys"][:3], n1["tile_venv"][:3]),
          n1["tile_sys"][:3] == [0, "54", "0"] and n1["tile_venv"][:3] == [0, "54", "0"], (n1["tile_sys"][3], n1["tile_venv"][3]))
    check("control OLD reports_tile.py prints 40 checks (%s)" % (o1["tile_sys"][:3],), o1["tile_sys"][1] == "40" and o1["tile_sys"][2] == "0")

    # ------------------------------------------------------------------------------------------------------------------------------- 2
    print("-- 2  F-799 on the page: the short closing")
    n2, o2 = NW["s2"], OL["s2"]
    w = n2["one"]["s500"] or {}
    check("two closing files of 250 items (25 s apart) against three reference closings of 379: the row is bad, ONE try, wrong 1, fix stock25 (%s)"
          % {k: w.get(k) for k in ("tries", "wrong", "fix")}, n2["one"]["state"] == "bad" and w.get("tries") == 1 and w.get("wrong") == 1 and w.get("fix") == "stock25", n2["one"])
    check("the page says Galat hai · koshish 1 / 2 · Khali stock wale item nahi aaye · Ek koshish aur hai, with the link to /kaise/stock (%s)" % n2["one_html"],
          all(n2["one_html"][k] for k in ("Galat hai", "koshish 1 / 2", "Khali stock wale item nahi aaye", "Ek koshish aur hai", "/finance/reports/aaj/kaise/stock")))
    check("control OLD: the first scene is ok with count '250 items' (%s / %s)" % (o2["one"]["state"], o2["one"]["count"]),
          o2["one"]["state"] == "ok" and o2["one"]["count"] == "250 items" and o2["one"]["s500"] is None)
    w = n2["two"]["s500"] or {}
    check("a third short one ten minutes later: wrong 2 -- Doosri baar bhi galat, Doctor sahab, no 'Ek koshish aur hai'; the owner's line says 'closing stock wrong 2 times' (%s)"
          % n2["two_html"], w.get("wrong") == 2 and n2["two_html"]["Doosri baar bhi galat"] and n2["two_html"]["Doctor sahab"] and not n2["two_html"]["Ek koshish aur hai"]
          and "closing stock wrong 2 times" in (n2["two_line"] or ""), n2["two_line"])
    check("a fourth, full (380 items, 130 zero-stock): ok -- Sahi hai, '380 item, khali stock wale bhi' (%s / %s)" % (n2["full"]["state"], n2["full_html"]),
          n2["full"]["state"] == "ok" and n2["full"]["count"] == "380 items" and n2["full"]["zero"] == 130 and all(n2["full_html"].values()))
    w = n2["eve"]["s500"] or {}
    check("a wrong closing of the afternoon BEFORE the walk day is not a try (tries %s): the row is due and it is said under the row ('sahi nahi thi')" % w.get("tries"),
          n2["eve"]["state"] == "due" and w.get("tries") == 0 and any("sahi nahi thi" in (l.get("lead") or "") for l in (n2["eve"]["loose"] or [])), n2["eve"]["loose"])

    # ------------------------------------------------------------------------------------------------------------------------------- 3
    print("-- 3  not the totals list / not the whole store")
    n3, o3 = NW["s3"], OL["s3"]
    check("variant DEFAULT -> bad, fix stock4 (%s)" % ((n3["default"]["s500"] or {}).get("fix"),), n3["default"]["state"] == "bad" and (n3["default"]["s500"] or {}).get("fix") == "stock4")
    check("variant TOTALS with a reading whose family is null -> bad, 'WHOLE' in why_hi, the second try (%s)" % ((n3["nofam"]["s500"] or {}).get("why_hi"),),
          n3["nofam"]["state"] == "bad" and "WHOLE" in ((n3["nofam"]["s500"] or {}).get("why_hi") or "") and (n3["nofam"]["s500"] or {}).get("wrong") == 2)
    check("control OLD gives arrived for both (%s / %s)" % (o3["default"]["state"], o3["nofam"]["state"]), o3["default"]["state"] == "arrived" and o3["nofam"]["state"] == "arrived")

    # ------------------------------------------------------------------------------------------------------------------------------- 4
    print("-- 4  the sale report")
    n4, o4 = NW["s4"], OL["s4"]
    check("SUMMARY1 -> state refused (S480 stands), fix sale3; the page shows 'Step 3 dobara kijiye' and the picture sale_two (%s)" % n4["summary_html"],
          n4["summary"]["state"] == "refused" and (n4["summary"]["s500"] or {}).get("fix") == "sale3" and all(n4["summary_html"].values()))
    check("a DETAIL file with a passing reading 5 minutes later -> ok, Sahi hai", n4["detail"]["state"] == "ok" and n4["detail_html"]["Sahi hai"], n4["detail"])
    check("control OLD shows no 'Step 3 dobara' (%s)" % o4["summary_html"], not o4["summary_html"]["Step 3 dobara kijiye"])

    # ------------------------------------------------------------------------------------------------------------------------------- 5
    print("-- 5  F-788: a refused file that is not the day's report")
    n5, o5 = NW["s5"], OL["s5"]
    wa, wb = (n5["before"]["s500"] or {}), (n5["after"]["s500"] or {})
    check("a medical-PC refusal (empty dates) and a 30-day range refusal: neither is a try (tries %s -> %s), both in loose (%d), the page says 'manzoor nahi hui', "
          "the line says '2 refused (not the day's report)', the row is due" % (wa.get("tries"), wb.get("tries"), len(n5["after"]["loose"] or [])),
          wa.get("tries") == wb.get("tries") == 0 and len(n5["after"]["loose"] or []) == 2 and n5["after_html"]["manzoor nahi hui"]
          and "2 refused (not the day's report)" in (n5["after_line"] or "") and n5["after"]["state"] == "due", n5["after_line"])
    check("a rejected marg_push_staging row of today (table live: %s), nothing else: in loose, 'manzoor nahi hui', the line says '1 refused (not the day's report)'" % n5["staging_table"],
          len(n5["staging"]["loose"] or []) == 1 and n5["staging_html"]["manzoor nahi hui"] and "1 refused (not the day's report)" in (n5["staging_line"] or ""), n5["staging_line"])
    check("control OLD puts the refusal on the row itself (state %s)" % o5["after"]["state"], o5["after"]["state"] == "refused")

    # ------------------------------------------------------------------------------------------------------------------------------- 6
    print("-- 6  the floor on the bill-gap card")
    n6, o6 = NW["s6"], OL["s6"]
    check("aaj.staff_on is set on the copy (%s); the floor day is %s; gaps before the floor on the copy: %d, on or after: %d" % (n6["staff_on"], n6["floor_day"], len(n6["pre"]), len(n6["post"])),
          n6["staff_on"] and bool(n6["floor_day"]) and len(n6["pre"]) >= 1)
    check("_s500_floor gives the floor day for shavez and None for manoj (%s)" % n6["floor_for"], n6["floor_for"].get("shavez") == n6["floor_day"] and n6["floor_for"].get("manoj") is None)
    check("the bill-gap card for shavez holds no gap whose later day is before the floor (%s) and every later one (%s)" % (n6["page_shavez"]["pre"], n6["page_shavez"]["post"]),
          not any(n6["page_shavez"]["pre"]) and all(n6["page_shavez"]["post"]))
    check("for manoj the card holds every gap (%s / %s)" % (n6["page_manoj"]["pre"], n6["page_manoj"]["post"]), all(n6["page_manoj"]["pre"]) and all(n6["page_manoj"]["post"]))
    check("api/status's line is the same for both logins (the owner's line stays whole)", n6["line_shavez"] == n6["line_manoj"] and bool(n6["line_shavez"]), n6["line_shavez"])
    check("control OLD shows shavez the September gap (%s)" % o6["page_shavez"]["pre"], all(o6["page_shavez"]["pre"]) and len(o6["page_shavez"]["pre"]) >= 1)

    # ------------------------------------------------------------------------------------------------------------------------------- 7
    print("-- 7  the guide and its pictures")
    n7, o7 = NW["s7"], OL["s7"]
    for kind in ("sale", "stock"):
        g = n7[kind]
        check("/kaise/%s as shavez: 200, six steps in <ol class=gs>, no meta refresh%s (%s)" % (kind, ", the real clock's due day in the steps" if kind == "sale" else "", g),
              g["code"] == 200 and g["li"] == 6 and not g["refresh"] and (g["due"] if kind == "sale" else True) and g["words"]["Sahi report ki pehchaan"])
    pics = n7["pics"]
    check("each of the thirteen pictures: 200 image/jpeg, begins FF D8, equals reports_guide.pic(name), max-age=86400",
          all(p["code"] == 200 and p["mime"] == "image/jpeg" and p["head"] == "ffd8" and p["same"] and "max-age=86400" in p["cache"] for p in pics.values()) and len(pics) == 13,
          {k: (v["code"], v["mime"], v["head"], v["same"]) for k, v in pics.items() if not (v["code"] == 200 and v["same"])})
    check("/pic/nope.jpg -> 404 (%s); /kaise/x -> 302 to the page (%s)" % (n7["nope"], n7["kx"]), n7["nope"] == 404 and n7["kx"][0] == 302 and n7["kx"][1] == "/finance/reports/aaj")
    check("a login with no medical role (w500none) is turned away from the page, the guide and a picture -- 302 to the portal (%s)" % n7["none"],
          all(v[0] == 302 and v[1].startswith("/portal") for v in n7["none"].values()))
    check("control OLD answers 404 for /kaise/sale (%s)" % o7["sale"]["code"], o7["sale"]["code"] == 404)

    # ------------------------------------------------------------------------------------------------------------------------------- 8
    print("-- 8  the snapshot door (F-799): a short closing is refused and not loaded")
    n8, o8 = NW["s8"], OL["s8"]
    check("379 W500 items as on the due day's eve -> 200 (%s)" % n8["eve"][0], n8["eve"][0] == 200 and n8["eve"][1].get("ok") is True)
    check("250 as on the due day -> 409 short_closing (items %s, reference %s), and stock_snapshot / stock_feed hold no row for that as_on (%s)"
          % (n8["short"][1].get("items"), n8["short"][1].get("reference"), n8["short_rows"]),
          n8["short"][0] == 409 and n8["short"][1].get("error") == "short_closing" and n8["short"][1].get("items") == 250 and n8["short"][1].get("reference") == 379
          and n8["short_rows"]["snapshot"] == 0 and n8["short_rows"]["feed"] == 0, n8["short"][1])
    check("379 for the same as_on -> 200, 379 rows (%s)" % n8["full_rows"], n8["full"][0] == 200 and n8["full_rows"]["snapshot"] == 379)
    check("a push_expected body of 200 items -> 200 into stock_expected (%s)" % n8["expected_rows"],
          n8["expected"][0] == 200 and n8["expected"][1].get("stored_in") == "stock_expected" and n8["expected_rows"]["expected"] == 200 and n8["expected_rows"]["snapshot"] == 379)
    check("with reports.closing_min_share = 0 a 250 push -> 200 (%s, %s rows)" % (n8["off"][0], n8["off_rows"]["snapshot"]), n8["off"][0] == 200 and n8["off_rows"]["snapshot"] == 250)
    check("control OLD answers 200 to the first 250 push and stores 250 rows (%s, %s)" % (o8["short"][0], o8["short_rows"]), o8["short"][0] == 200 and o8["short_rows"]["snapshot"] == 250)

    # ------------------------------------------------------------------------------------------------------------------------------- 8b
    print("-- 8b F-801: the voucher proof reads the newest closing after the vouchers")
    nb, ob = NW["s8b"], OL["s8b"]
    check("NEW _s446_proof: done, as_after the newer day (%s)" % nb["proof"], nb["proof"]["state"] == "done" and nb["proof"]["as_after"] == "11-03-2031" and nb["proof"]["as_before"] == "07-03-2031")
    check("control OLD: wrong, as_after the first day after the vouchers (%s)" % ob["proof"], ob["proof"]["state"] == "wrong" and ob["proof"]["as_after"] == "10-03-2031", ob["rows"])

    # ------------------------------------------------------------------------------------------------------------------------------- 8c
    print("-- 8c the salt card's words")
    nc, oc = NW["s8c"], OL["s8c"]
    check("NEW amir_day.py holds 'Ek export aur: SALT WISE ITEM LIST' and 'Text ya Excel, dono chalte hain', and no 'text nahi' / 'nahi padhta' / '(Excel)\")' (%s)" % nc["file"],
          nc["file"]["Ek export aur: SALT WISE ITEM LIST"] and nc["file"]["Text ya Excel, dono chalte hain"] and not nc["file"]["text nahi"] and not nc["file"]["nahi padhta"]
          and not nc["file"]['(Excel)")'])
    check("Amir's step 6 with a salt tick newer than the last list shows the card (the duty's door_marker) with the new sentence (%s)" % nc["page"],
          nc["page"]["Ek export aur: SALT WISE ITEM LIST"] and nc["page"]["Text ya Excel, dono chalte hain"] and not nc["page"]["Excel mein (text nahi)"])
    check("control OLD holds 'Excel mein (text nahi)' (%s)" % oc["file"]["Excel mein (text nahi)"], oc["file"]["Excel mein (text nahi)"] and oc["page"]["Excel mein (text nahi)"])

    # ------------------------------------------------------------------------------------------------------------------------------- 9
    print("-- 9  the watch (reports_watch.tick, the stub for the phone)")
    n9, o9 = NW["s9"], OL["s9"]
    t1 = n9["t1_stub"]
    body = (t1[0].get("body") if t1 else "") or ""
    check("wrong twice at 08:20: ONE line in the stub, body 'Closing stock of 11-03 is wrong twice:' ... one sentence about the sale report (%s)" % n9["t1"],
          len(t1) == 1 and body.startswith("Closing stock of 11-03 is wrong twice:") and body.endswith("The sale report has not come yet.") and n9["t1"].get("sent") == 1
          and len(n9["t1_rows"]) == 1 and n9["t1_rows"][0]["key"] == "STOCK_CLOSING" and bool(n9["t1_rows"][0]["sent_at"]), body)
    check("the same tick again sends nothing more (%d lines, %s); the page now says 'khabar chali gayi hai' (%s)" % (n9["t2_stub_n"], n9["t2"], n9["t2_html"]),
          n9["t2_stub_n"] == 1 and n9["t2"].get("sent") == 0 and n9["t2"].get("made") == 0 and n9["t2_html"]["khabar chali gayi hai"])
    l10 = n9["late1000_stub"]
    b10 = (l10[0].get("body") if l10 else "") or ""
    check("nothing in at 09:50 -> nothing (%s); at 10:00 -> one message naming both (%s)" % (n9["late950"], b10[:120]),
          n9["late950_stub_n"] == 0 and n9["late950"].get("made") == 0 and len(l10) == 1 and "Sale report of 11-03 has not come by 10:00." in b10
          and "Closing stock of 11-03 has not come by 10:00." in b10 and n9["late1000"].get("sent") == 2)
    check("two files still being checked (%s) at 10:00 -> nothing, 10:20 -> nothing, 10:30 -> one message (%s)" % (n9["pend_states"], (n9["pend1030_stub"] or [{}])[0].get("body", "")[:140]),
          n9["pend_states"] == ["arrived", "arrived"] and n9["pend1000_stub_n"] == 0 and n9["pend1020_stub_n"] == 0 and len(n9["pend1030_stub"]) == 1
          and "had not finished by 10:30" in n9["pend1030_stub"][0].get("body", ""))
    nr = n9["nostub_rows"]
    check("with REPORTS_NTFY_STUB unset (ORDER_PUSH_STUB set): a row is made and not sent -- sent 0, how 'a walk's push stub is set -- nothing sent', sent_at NULL (%s / %s)" % (n9["nostub"], nr),
          n9["nostub"].get("sent") == 0 and n9["nostub"].get("how") == "a walk's push stub is set -- nothing sent" and len(nr) == 1 and nr[0]["sent_at"] in (None, ""))
    check("the report turns right before the next tick: the unsent row is withdrawn (%s -> rows %s)" % (n9["withdrawn"], n9["withdrawn_rows"]),
          n9["withdrawn"].get("withdrawn") == 1 and n9["withdrawn_rows"] == [])
    check("a Sunday -> quiet (%s)" % n9["sunday"], n9["sunday"].get("quiet") == "sunday")
    check("reports.alert = off -> off (%s), and the page says 'Doctor sahab ko bataiye' (%s)" % (n9["alert_off"], n9["alert_off_html"]),
          n9["alert_off"].get("off") == "reports.alert" and n9["alert_off_html"]["Doctor sahab ko bataiye"] and not n9["alert_off_html"]["khabar ja rahi hai"])
    check("a file REPORTS_WATCH_OFF in the scratch off-dir -> off (%s), the page says 'Doctor sahab ko bataiye' (%s); file gone -> 'khabar ja rahi hai' (%s)"
          % (n9["file_off"], n9["file_off_html"], n9["file_on_again_html"]),
          n9["file_off"].get("off") == "REPORTS_WATCH_OFF" and n9["file_off_html"]["Doctor sahab ko bataiye"] and not n9["file_off_html"]["khabar ja rahi hai"]
          and n9["file_on_again_html"]["Doctor sahab ko khabar ja rahi hai"])
    check("order_rules._s500_reports(con, {}) on its own copy (the real clock) returns a dict whose 'reports' is a dict with ok true (%s)" % mask(str(n9["or_tick"]))[:200],
          isinstance(n9["or_tick"], dict) and isinstance(n9["or_tick"].get("reports"), dict) and n9["or_tick"]["reports"].get("ok") is True)
    check("control OLD order_rules has no _s500_reports (%s)" % o9["or_tick"], o9["or_tick"] == "no _s500_reports")

    # ------------------------------------------------------------------------------------------------------------------------------- 10
    print("-- 10 the staff's eyes (D648): eight logins signed in on scratch copies (a walk-only store and secret)")
    EN, EO = run("eye", "new", a.fin_new), run("eye", "old", a.fin_old)
    if not check("both staff-eye probes ran to the end", EN is not None and EO is not None):
        return finish()
    check("aaj_kaam.connect(copy, mode='staff') is floored at a date (%s; views that could not be laid: %s)" % (EN["floor"], EN["floor_bad"]),
          bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(EN["floor"] or ""))))
    en, eo = EN["eye"], EO["eye"]
    ALLOW = {"/finance/reports/aaj", "/finance/reports/aaj/api/status"}
    for who in USERS:
        n, o = en[who], eo[who]
        diff = sorted(k for k in set(n["pages"]) | set(o["pages"]) if n["pages"].get(k) != o["pages"].get(k))
        salt_only = [d for d in diff if d not in ALLOW and d.startswith("/finance/amir") and n["salted"].get(d) == o["salted"].get(d)]
        unexplained = [d for d in diff if d not in ALLOW and d not in salt_only]
        t = n["texts"].get("/finance/reports/aaj") or {}
        check("%s: signs in (%s), %d tiles, 'Aaj ki reports' tile %s; the page answers %s%s; %d pages compared NEW vs OLD, differences: %s%s"
              % (who, n["status"], n["n_tiles"], n["tile_reports"], t.get("code"), (" (Signed in: %s)" % who) if t.get("signed") else (" -> %s" % t.get("loc")),
                 len(n["pages"]), diff or "none", (" -- Amir's card pages differ by the salt card's words and the stage-A proof rows (F-801) ALONE "
                                                   "(equal once those are taken out): %s" % salt_only) if salt_only else ""),
              n["status"] == 200 and n["n_tiles"] == o["n_tiles"] and not unexplained and n["pages"].get("home") == o["pages"].get("home"), unexplained)
        if who == "amir":
            for side, e in (("OLD (the first closing after the vouchers)", o), ("NEW (the newest closing)", e_n := n)):
                print("   Amir's stage-A proof rows on step 6, %s: %s" % (side, mask(str(e["texts"].get("/finance/amir/step/6 proof")))[:600]))

        def misses(side):
            due_ = [r for r in side["duties"] if isinstance(r.get("due_n"), int) and r["due_n"] > 0 and r.get("door")]
            return due_, sorted(r["id"] for r in due_ if (r.get("tile") and r.get("tile_seen") is False) or r.get("door_seen") is False)
        due, miss = misses(n)
        _d, miss_o = misses(o)
        errs = [r["id"] for r in n["duties"] if isinstance(r.get("due_n"), str)]
        before = [m for m in miss if m in miss_o]
        if before:
            NOTES.append("%s: due but not visible on either side (before this kit too): %s" % (who, before))
        check("   %s: %d duties in the map, %d due on the %s connection -- each due one visible (tile on the home, marker on its door) as on the OLD side%s"
              % (who, len(n["duties"]), len(due), "plain" if USERS[who] == "doctor" else "floored", ("; NOT visible on either side, before this kit too: %s (a finding)" % before) if before else ""),
              not [m for m in miss if m not in miss_o] and not errs, (miss, miss_o, errs))
        for r in n["duties"]:
            if r["id"] == "shavez.bill_chain_gap" and isinstance(r.get("plain_n"), int) and r["plain_n"] > 0 and r.get("due_n") == 0:
                NOTES.append("FINDING (parent): shavez.bill_chain_gap is due unfloored while the page now floors it")
    for who in ("shavez", "amir"):
        t = en[who]["texts"].get("/finance/reports/aaj") or {}
        check("%s holds the tile and opens the page (200, Signed in: %s)" % (who, who), en[who]["tile_reports"] and t.get("code") == 200 and t.get("signed"))
    for who in ("darpan", "shivani", "alisha", "bhawna", "manoj"):
        t = en[who]["texts"].get("/finance/reports/aaj") or {}
        check("%s opens the page by its address (200); tile on the home: %s%s" % (who, en[who]["tile_reports"], "" if en[who]["tile_reports"] else " (a finding for the parent's tile_grants.json)"),
              t.get("code") == 200 and t.get("title"))
        if not en[who]["tile_reports"]:
            NOTES.append("%s opens /finance/reports/aaj but holds no 'Aaj ki reports' tile (the parent's tile_grants.json)" % who)
    t = en["reception"]["texts"].get("/finance/reports/aaj") or {}
    to = eo["reception"]["texts"].get("/finance/reports/aaj") or {}
    check("reception (no medical role) -> 302 to the portal on both sides (%s / %s)" % (t.get("code"), to.get("code")),
          t.get("code") == 302 and str(t.get("loc")).startswith("/portal") and to.get("code") == 302)
    for x in sorted(set(NOTES)):
        print("   " + ("FINDING (parent): " if not x.startswith("FINDING") else "") + x)
    return finish()


def finish():
    if FAILS:
        print("WALK_S500 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:220])
        return 1
    print("WALK_S500 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
