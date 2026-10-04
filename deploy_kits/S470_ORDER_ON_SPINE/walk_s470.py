#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s470.py -- kit S470_ORDER_ON_SPINE (the brief's section 5): THE REAL finance app over SCRATCH COPIES of finance.db, assets.db and
the spine (backup API), one process per side:

  NEW  the box + S470's built files            OLD  the box as it is -- the NEGATIVE CONTROL of every section

   1  A    the read door's new methods (the spine's own selftest, and on the scratch spine); OLD has none and its sales() counts a credit
           note as a sale
   2  B    equality on tables: with order.engine_source = tables, NEW's plan and interim plan equal OLD's, line for line, on both bases
   3  B    the spine source: every rate equals one worked out in this walk from sp_sale_line / sp_sale_bill; Marg's stock equals
           stock_snapshot's item by item (those that differ printed); the count-basis figures identical on both sides (a guard);
           NEGATIVE: a sale bill only the spine holds -- OLD's rate is lower by exactly its units / 28
   4  B.4  arrivals: received on D, the bill dated D-1 -- OLD counts the goods twice, NEW drops them; with no bill they leave on day 15
   5  B.7  sold, never bought: OLD's plan drops it silently, NEW names it under no_supplier and the owner's card counts it
   6  B.8  the six settings: in the setting table, read (pace_days 14 moves the rate; dead_after_days 1 zeroes a line), set from the
           owner's card by the owner only; purchase_app.py differs from the box's by the one edit
   7  C    the trial: the kept file, the three old scores and the two new ones by hand, the blocked day in no denominator, finance.db
           untouched; NEGATIVE: OLD's trial writes lines that are in no proposal
   8  D    the owner's card: the weekly line; "not ready yet" with no file and with an old one; no such card for reception
   9  E    the staff-eye walk: every home and every door of reception, darpan, shavez, amir and the owner the same on both sides (the
           owner's old page alone gains its card), every tile on its home, every due duty's marker on its door
  10       the crons' own commands as scripts on the built files; every added block above its file's __main__ guard
Its rows are keyed W470; dates from today. No phone number or key in its output.

  --fin-new DIR --fin-old DIR --por DIR --db PATH --adb PATH --spine PATH --work DIR --duty-map FILE
"""
import argparse
import datetime as dt
import difflib
import hashlib
import html as _html
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys

TODAY = dt.date.today()
NOW = dt.datetime.now().replace(microsecond=0)
USERS = {"reception": "staff", "darpan": "staff", "shavez": "manager", "amir": "staff", "manoj": "doctor", "shivani": "staff"}
TAG = "W470JSON "
S1, S2 = "W470 SUPPLIER ONE", "W470 SUPPLIER TWO"
MA, MB, MC, MD_, MN, CN = "W470 MED A", "W470 MED B", "W470 MED C", "W470 MED D", "W470 MED N", "W470 CN MED"
SCORE_LINE = ("Last week: of what was bought, 62% was on the list beforehand · of what was listed, 40% was bought within 14 days · "
              "3 medicines ran out, 1 of them listed in time.")
NOT_READY = "The weekly score is not ready yet."


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


def K(n):
    return re.sub(r"\s+", " ", (n or "").strip())[:20].strip()


def mask(s):
    return re.sub(r"\+?\d[\d\s-]{8,}\d", lambda m: "#" * 10 if len(re.sub(r"\D", "", m.group(0))) >= 10 else m.group(0), str(s))


def ins(con, table, row, replace=False):
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    return con.execute("INSERT %sINTO %s (%s) VALUES (%s)" % ("OR REPLACE " if replace else "", table, ", ".join(cols), ", ".join("?" * len(cols))),
                       [row[c] for c in cols]).lastrowid


def text_of(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h or "", flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def steady(h):
    """A page with what changes from one minute to the next taken out: clock times, long hex strings (a token, a cache key)."""
    h = re.sub(r"\b\d{1,2}:\d\d(:\d\d)?\b", "HH:MM", h or "")
    return re.sub(r"\b[0-9a-f]{16,}\b", "HEX", h)


def plan_shape(p):
    """A plan as it is compared: every supplier, every line, every field -- less the three S470 adds on a line, and the two new top keys."""
    out = {}
    for vn, v in sorted((p.get("vendors") or {}).items()):
        d = {k: x for k, x in v.items() if k != "lines"}
        d["lines"] = [{k: x for k, x in l.items() if k not in ("lot", "free", "family")} for l in v["lines"]]
        out[vn] = d
    return dict(as_on=p.get("as_on"), today=p.get("today"), off=p.get("off"), vendors=out, held_items=p.get("held_items"))


def probe():
    SIDE = os.environ["SIDE"]
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import purchase_app as pa                                          # noqa: E402
    import order_rules as orr                                          # noqa: E402
    import shelf_figure as SF                                          # noqa: E402
    assert orr.__file__.startswith(FIN) and pa.__file__.startswith(FIN), (orr.__file__, pa.__file__)
    pa._assets_db = os.environ["ASSETS_DB"]
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    spw = sqlite3.connect(os.environ["SPINE_DB"], timeout=60)            # the walk's OWN scratch spine
    spw.row_factory = sqlite3.Row
    NEW = SIDE == "new"
    out = {}

    def H(u):
        h = {"X-Clinic-User": u, "X-Clinic-Role": ""}
        if u == "reception":
            h["Cookie"] = "clinic_who=shivani"
        return h

    def G(u, p):
        r = fc.get(p, base_url=BASE, headers=H(u))
        return r.status_code, r.get_data(as_text=True)

    def POST(u, p, body):
        r = fc.post(p, base_url=BASE, headers=H(u), json=body)
        return r.status_code, r.get_json(silent=True) or {}

    def setv(k, v):
        db.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
        db.commit()

    def inputs(today=TODAY):
        return orr._snapshot_inputs(db, today)
    orr.ensure(db)
    basis0 = orr._s454_basis(db)
    # ================================================================ 9  the staff-eye walk, on the copies as they are (before any made-up row)
    out["E"] = staff_eye(fc, BASE)
    # ================================================================ 2  equality on tables (NEW on tables; OLD has only the tables)
    eq = {}
    for basis in ("count", "marg"):
        setv("order.stock_basis", basis)
        if NEW:
            setv("order.engine_source", "tables")
        p, ip = orr.plan(db, TODAY), orr.interim_plan(db, TODAY)
        eq[basis] = dict(plan=plan_shape(p), interim=plan_shape(ip), lines=sum(len(v["lines"]) for v in p["vendors"].values()), engine=p.get("engine"),
                         new_keys=sorted(k for k in p if k in ("no_supplier", "engine")))
    out["B_tables"] = eq
    # ================================================================ 3  the spine source, on today's real data
    setv("order.stock_basis", basis0)
    out["B_shelf"] = hashlib.md5(json.dumps(sorted((k, v.get("shelf"), v.get("marg"), v.get("named"), v.get("base"), v.get("sold"), v.get("bought"), v.get("arrived"))
                                                   for k, v in SF.figures(db).items()), default=str).encode()).hexdigest()
    if NEW:
        setv("order.engine_source", "spine")
        as_on, snap, pace, purch, _tr, _or = inputs()
        out["B_engine"] = orr._s470_engine()
        alias = {r["alias"]: r["k20"] for r in spw.execute("SELECT alias, k20 FROM sp_alias")}
        key = lambda n: alias.get(K(n), K(n))                           # noqa: E731
        ds0 = [r[0] for r in db.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
        nkey = {}                                                       # the items of Marg's stock list under each key
        for r in db.execute("SELECT item FROM stock_snapshot WHERE as_on=?", (max(ds0, key=pa._as_on_key),)):
            nkey[key(r[0])] = nkey.get(key(r[0]), 0) + 1
        tot = {}
        for r in spw.execute("SELECT l.k20, l.units, COALESCE(b.credit_note,0) AS cn FROM sp_sale_line l LEFT JOIN sp_sale_bill b ON b.date=l.date AND b.bill=l.bill "
                             "WHERE l.date>=? AND l.date<=?", (D(28), D(0))):
            tot[r["k20"]] = tot.get(r["k20"], 0.0) + (-r["units"] if r["cn"] else r["units"])
        bad, n_rate = [], 0
        for k, e in pace.items():
            s = snap[k]
            kk = key(s["item"])
            want = max(0.0, tot.get(kk, 0.0)) / max(1, nkey.get(kk, 1)) / 28.0
            n_rate += 1
            if abs(want - e["rate_per_day"]) > 1e-9:
                bad.append((s["item"], round(want, 4), round(e["rate_per_day"], 4)))
        p = orr.plan(db, TODAY)
        lines = [(vn, l["item"], l["per_day"]) for vn, v in p["vendors"].items() for l in v["lines"]]
        bad_l = [(i, pd) for _vn, i, pd in lines if pd is not None and abs(pd - round(pace[pa.norm(i)]["rate_per_day"], 2)) > 1e-9]
        out["B_rate"] = dict(items=n_rate, bad=bad[:10], plan_lines=len(lines), bad_lines=bad_l[:10], with_sales=sum(1 for e in pace.values() if e["rate_per_day"] > 0))
        setv("order.stock_basis", "marg")
        as_m, snap_m = inputs()[:2]
        ds = [r[0] for r in db.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
        ss_on = max(ds, key=pa._as_on_key)
        ss = {pa.norm(r[0]): int(r[1] or 0) for r in db.execute("SELECT item, qty FROM stock_snapshot WHERE as_on=?", (ss_on,))}
        both = sorted(set(ss) & set(snap_m))
        differ = [(snap_m[k]["item"], ss[k], snap_m[k]["qty"], snap_m[k]["_s470"]["family"]) for k in both if ss[k] != snap_m[k]["qty"]]
        ortho = {pa.norm(r[0]) for r in db.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")}
        absent = sorted(set(ss) - set(snap_m))
        out["B_stock"] = dict(spine_on=as_m, snapshot_on=ss_on, same_day=(pa._as_on_key(as_m) == pa._as_on_key(ss_on)), both=len(both), spine=len(snap_m), snapshot=len(ss),
                              differ=differ, alone_differ=[d for d in differ if d[3] == 1], absent=absent, absent_med=[k for k in absent if k not in ortho],
                              extra=sorted(set(snap_m) - set(ss)), no_closing=orr.plan(db, TODAY).get("no_closing"))
        setv("order.stock_basis", basis0)
    # ================================================================ the made-up rows, the same on both sides, in both stores
    ss_on = max([r[0] for r in db.execute("SELECT DISTINCT as_on FROM stock_snapshot")], key=pa._as_on_key)
    last = spw.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    ins(db, "purchase_export", dict(md5="w470" + "0" * 28, superseded_by=None), replace=True)

    def item(name, qty, spine_qty=None):
        ins(db, "stock_snapshot", dict(as_on=ss_on, item=name, qty=qty, packing="1*10", pack_size=10))
        ins(spw, "sp_item", dict(k20=K(name), name=name, packing="1*10", unit_kind="LOOSE", first_seen=D(60), last_seen=last), replace=True)
        ins(spw, "sp_close", dict(as_on=last, k20=K(name), units=float(qty if spine_qty is None else spine_qty), source_md5="w470"), replace=True)

    seq = [0]

    def sale(name, day, units, tables=True, spine=True, cn=False):
        seq[0] += 1
        bill = ("CN0W%04d" if cn else "A0W%05d") % (4700 + seq[0])
        if tables:
            ins(db, "sale_line_item", dict(unit="medical", business_date=day, bill_no=bill, is_return=1 if cn else 0, seq=1, item_name=name, item_key=name,
                                           pack="1*10", qty_raw="%d:%d" % (units // 10, units % 10), amount_p=0))
        if spine:
            ins(spw, "sp_sale_bill", dict(date=day, bill=bill, gross_p=0, disc_p=0, tax_p=0, drcr_p=0, net_p=0, cash_p=0, credit_note=1 if cn else 0, source_md5="w470"))
            ins(spw, "sp_sale_line", dict(date=day, bill=bill, seq=1, name20=K(name), k20=K(name), pack="1*10", qty_raw="%d:%d" % (units // 10, units % 10),
                                          units=float(units), rate_p=1000, batch="", expiry=""))

    def bought(name, vendor, bill, day, qty, free=0, rate_p=5000):
        ins(db, "purchase_line", dict(supplier_norm=vendor, bill_no=bill, bill_date=day, month=day[:7], item=name, packing="1*10", qty=qty, free=free, rate_p=rate_p,
                                      amount_p=qty * rate_p, net_amount_p=qty * rate_p, purchase_rate_p=rate_p, direction="PURCHASE", source_md5="w470" + "0" * 28,
                                      line_type="ITEMWISE"))
        ins(spw, "sp_purchase_bill", dict(supplier=vendor + " BAREILLY", supkey=re.sub(r"[^A-Z]", "", vendor.upper())[:8], bill=bill, date=day, amount_p=qty * rate_p,
                                          direction="PURCHASE", source_md5="w470"), replace=True)
        ins(spw, "sp_purchase_line", dict(supkey=re.sub(r"[^A-Z]", "", vendor.upper())[:8], bill=bill, date=day, seq=1, name27=name, k20=K(name), packing="1*10", qty=float(qty),
                                          free=float(free), units=float((qty + free) * 10), amount_p=qty * rate_p, net_amount_p=qty * rate_p, direction="PURCHASE",
                                          source_md5="w470"))

    def order(vendor, name, packs, created, received):
        oid = ins(db, "purchase_order", dict(created_at=created, created_by="W470 walk", vendor=vendor, status="received", received_at=received, total_p=0, section="Medicines"))
        ins(db, "purchase_order_line", dict(order_id=oid, item=name, packs=packs, pack_size=10, units=packs * 10, rate_p=100, value_p=packs * 100, supplied=packs))
        return oid
    item(MA, 480, spine_qty=500)                                     # the two stores disagree on purpose: who is read?
    sale(MA, D(20), 28)
    sale(MA, D(5), 14)
    sale(MA, D(3), 28, tables=False)                                 # a bill only the spine holds (the shape of the missing bills)
    item(MB, 100)
    item(MC, 100)
    item(MD_, 0)
    sale(MD_, D(9), 20)
    sale(MD_, D(2), 20)
    bought(MD_, S2, "W47D1", D(30), 10, free=2)
    item(MN, 40)
    sale(MN, D(4), 10)
    sale(CN, D(2), 10, tables=False)
    sale(CN, D(1), 3, tables=False, cn=True)
    ins(spw, "sp_item", dict(k20=K(CN), name=CN, packing="1*10", unit_kind="LOOSE", first_seen=D(60), last_seen=D(30)), replace=True)
    order(S1, MB, 3, D(7) + "T10:00:00", D(5) + "T11:00:00")
    order(S1, MC, 2, D(7) + "T10:00:00", D(5) + "T11:00:00")
    db.commit()
    spw.commit()
    # ================================================================ 1  A: the read door on the scratch spine
    import importlib.util                                               # noqa: PLC0415
    spec = importlib.util.spec_from_file_location("w470_spine_read", os.path.join(FIN, "spine", "spine_read.py"))
    SR = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(SR)
    sp = SR.Spine(os.environ["SPINE_DB"])
    a = dict(has={m: hasattr(sp, m) for m in ("sales_daily", "stock_series", "purchase_lines", "family", "last_sale", "closing")},
             old_sales_units=sp.sales(CN, D(5), D(0))["units"])
    if NEW:
        a["daily"] = [(r["date"], r["units"], r["bills"]) for r in sp.sales_daily(CN, D(5), D(0))]
        a["last_sale"] = sp.last_sale(CN)
        a["purchase"] = [(l["supplier"], l["direction"], l["qty"], l["free"]) for l in sp.purchase_lines(MD_)]
        a["closing"] = [sp.closing(MA), sp.stock(MA)["marg_units"]]
        a["series"] = [x["units"] for x in sp.stock_series(MA, D(2), D(0))]
        a["family"] = sp.family(MA)["n"]
    sp.con.close()
    out["A"] = a
    # ================================================================ 3  the bill only the spine holds; Marg's stock: who is read
    setv("order.stock_basis", "marg")
    x = inputs()
    out["B_neg"] = dict(rate=x[2].get(pa.norm(MA), {}).get("rate_per_day"), stock=x[1].get(pa.norm(MA), {}).get("qty"))
    setv("order.stock_basis", basis0)
    # ================================================================ 4  B.4 arrivals
    way = {}
    for basis in ("count", "marg"):
        setv("order.stock_basis", basis)
        tr = inputs()[4]
        way[basis] = dict(b=(tr.get(pa.norm(MB)) or {}).get("units"), c=(tr.get(pa.norm(MC)) or {}).get("units"))
    bought(MB, S1, "W47B1", D(6), 3)                                 # Marg's bill: dated the day BEFORE the receipt (D-1), entered now
    db.commit()
    spw.commit()
    for basis in ("count", "marg"):
        setv("order.stock_basis", basis)
        tr = inputs()[4]
        way[basis + "_billed"] = dict(b=(tr.get(pa.norm(MB)) or {}).get("units"), c=(tr.get(pa.norm(MC)) or {}).get("units"))
        d14, d15 = dt.date.fromisoformat(D(5)) + dt.timedelta(days=14), dt.date.fromisoformat(D(5)) + dt.timedelta(days=15)
        way[basis + "_days"] = [(inputs(d14)[4].get(pa.norm(MC)) or {}).get("units"), (inputs(d15)[4].get(pa.norm(MC)) or {}).get("units")]
    setv("order.stock_basis", basis0)
    out["B4"] = way
    # ================================================================ 5 / 6  no supplier; the settings
    def line_of(p, name):
        return next((l for v in p["vendors"].values() for l in v["lines"] if l["item"] == name), None)
    p = orr.plan(db, TODAY)
    ns = p.get("no_supplier")
    ld = line_of(p, MD_)
    out["B7"] = dict(has_key="no_supplier" in p, named=bool(ns) and any(x["item"] == MN for x in ns), n=len(ns or []), row=next((x for x in (ns or []) if x["item"] == MN), None),
                     on_a_line=line_of(p, MN) is not None)
    out["B5"] = dict(line=bool(ld), lot=(ld or {}).get("lot"), free=(ld or {}).get("free"), vendor=(ld or {}).get("vendor_norm"), qty=(ld or {}).get("qty"),
                     rate_p=(ld or {}).get("rate_p"))
    s6 = dict(rows={r[0]: r[1] for r in db.execute("SELECT key, value FROM setting WHERE key IN ('order.engine_source','order.pace_days','order.dead_after_days',"
                                                    "'order.on_order_days','order.in_transit_days','order.lot_history_days')")})
    r28 = inputs()[2].get(pa.norm(MA), {}).get("rate_per_day")
    setv("order.pace_days", "14")
    s6["pace"] = [r28, inputs()[2].get(pa.norm(MA), {}).get("rate_per_day")]
    setv("order.pace_days", "28")
    setv("order.dead_after_days", "1")
    s6["dead"] = [bool(ld), line_of(orr.plan(db, TODAY), MD_) is not None]
    setv("order.dead_after_days", "60")
    setv("order.on_order_days", "4")
    c1, j1 = POST("manoj", "/finance/porders/api/s454/setting", dict(key="order.pace_days", value="21"))
    c2, j2 = POST("manoj", "/finance/porders/api/s454/setting", dict(key="order.pace_days", value="3"))
    c3, j3 = POST("manoj", "/finance/porders/api/s454/setting", dict(key="order.engine_source", value="maybe"))
    c4, j4 = POST("reception", "/finance/porders/api/s454/setting", dict(key="order.pace_days", value="14"))
    s6["api"] = dict(ok=[c1, j1.get("ok"), j1.get("before"), j1.get("value")], low=[c2, j2.get("error")], word=[c3, j3.get("error")], staff=[c4, j4.get("error")],
                     row=(db.execute("SELECT value FROM setting WHERE key='order.pace_days'").fetchone() or [None])[0],
                     audit=db.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s454_setting' AND ref='order.pace_days'").fetchone()[0])
    setv("order.pace_days", "28")
    out["B8"] = s6
    # ================================================================ 8  D: the owner's card
    sf = os.environ["ORDER_SCORE_FILE"]

    def card(u="manoj"):
        s, h = G(u, "/finance/porders?old=1")
        m = re.search(r'<div [^>]*id="s470">(.*?)</div></div>', h, re.S) or re.search(r'<div [^>]*id="s470">(.*?)</div>', h, re.S)
        sc = re.search(r'<div id="s470score">(.*?)</div>', h, re.S)
        nsup = re.search(r'<div id="s470nosup">(.*?)<details>', h, re.S)
        return dict(status=s, card=bool(m), score=_html.unescape(sc.group(1)) if sc else None, nosup=text_of(nsup.group(1)) if nsup else None,
                    names=(MN in h), keys=sum(1 for k in ("order.engine_source", "order.pace_days", "order.dead_after_days", "order.on_order_days", "order.in_transit_days",
                                                         "order.lot_history_days") if ("<code>%s</code>" % k) in h),
                    after_src=(h.find('id="s470"') > h.find('id="s454src"') >= 0), s470=("s470" in h))
    if os.path.exists(sf):
        os.remove(sf)
    d8 = dict(none=card())
    with open(sf, "w", encoding="utf-8") as fh:
        json.dump(dict(date=TODAY.isoformat(), bought_on_list_pct=61.9, listed_bought_pct=40.0, stockouts=3, stockouts_listed_in_time=1, value_not_bought_p=123400,
                       days_scored_7=4, days_scored_14=2), fh)
    d8["made"] = card()
    with open(sf, "w", encoding="utf-8") as fh:
        json.dump(dict(date=D(3), bought_on_list_pct=61.9, listed_bought_pct=40.0, stockouts=3, stockouts_listed_in_time=1, days_scored_7=4, days_scored_14=2), fh)
    d8["stale"] = card()
    with open(sf, "w", encoding="utf-8") as fh:
        json.dump(dict(date=TODAY.isoformat(), bought_on_list_pct=None, listed_bought_pct=None, stockouts=0, stockouts_listed_in_time=0, days_scored_7=0, days_scored_14=0,
                       first_score_on=D(-1)), fh)
    d8["first_week"] = card()
    d8["reception"] = card("reception")
    out["D"] = d8
    print(TAG + json.dumps(out, default=str))


def staff_eye(fc, BASE):
    import portal as po                                                # noqa: PLC0415
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W470J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True)
    eye = {}
    for who in ("reception", "darpan", "shavez", "amir", "manoj"):
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
        home = r.get_data(as_text=True)
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', home)]
        ck = "clinic_sso=" + tok + ("; clinic_who=shivani" if who == "reception" else "")

        def page(path):
            body, code = "", 0
            for _hop in range(4):
                rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
                code = rr2.status_code
                if code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                    path = rr2.headers["Location"].replace(BASE, "")
                    continue
                body = rr2.get_data(as_text=True)
                break
            return code, body
        pages = {"home": hashlib.md5(steady(home.replace(tok, "TOKEN")).encode()).hexdigest()}
        rows, doors = [], set()
        mine = {who, (dm.get("shared") or {}).get(who)}
        for du in dm.get("duties") or []:
            if du.get("person") not in mine:
                continue
            row = {"id": du.get("id"), "tile": du.get("tile"), "tile_seen": (du.get("tile") in seen) if du.get("tile") else None}
            sql = str(du.get("due_sql") or "").strip().rstrip(";")
            n = None
            if sql:
                try:
                    rr = ro.execute(sql).fetchone()
                    n = int((rr[0] if rr else 0) or 0)
                except Exception as e:                             # noqa: BLE001
                    n = "ERR " + str(e)[:80]
            row["due_n"] = n
            door, mark = du.get("door"), du.get("door_marker")
            if door and str(door).startswith("/finance/"):
                doors.add(str(door))
                if mark and isinstance(n, int) and n > 0:
                    row["door_seen"] = mark in page(str(door))[1]
            rows.append(row)
        for extra in ("/finance/porders", "/finance/porders?old=1"):
            doors.add(extra)
        for d in sorted(doors):
            code, body = page(d)
            pages[d] = "%s %s" % (code, hashlib.md5(steady(body.replace(tok, "TOKEN")).encode()).hexdigest())
        eye[who] = dict(status=r.status_code, duties=rows, pages=pages)
    ro.close()
    return eye


# ============================================================================================================================ the trial (7)
def trial_fixture(db_path, spine_path, T):
    """Made-up proposals and purchases around a far-off 'today' T, where the copies hold nothing of their own: every score is by hand."""
    def d(n):
        return (T - dt.timedelta(days=n)).isoformat()
    db = sqlite3.connect(db_path)
    sp = sqlite3.connect(spine_path)
    A, B, C, Dd, E, F, OX = ["W470 ITEM %s" % x for x in "ABCDEF"] + ["W470 ORTHO X"]

    def prop(day, sup, kind, lines):
        ins(db, "order_proposal", dict(day=day, supplier_norm=sup, vendor=sup, kind=kind, status="open", prepared_at=day + "T09:00:00",
                                       total_p=sum(v for _i, _q, v in lines),
                                       lines=json.dumps([dict(item=i, qty=q, unit="strip", pack_size=10, value_p=v) for i, q, v in lines])))
    prop(d(14), S1, "fixed", [(A, 10, 100000), (B, 5, 50000)])
    prop(d(14), S1, "interim", [(A, 2, 20000)])                        # the same key twice on one day: ONE proposed key, 120 units
    prop(d(7), S2, "fixed", [(C, 3, 30000), (Dd, 2, 40000)])
    ins(db, "stock_item_section", dict(item=OX, section="Orthotics"), replace=True)
    db.commit()
    db.close()
    for nm in (A, B, C, Dd, E, F, OX):
        ins(sp, "sp_item", dict(k20=K(nm), name=nm, packing="1*10", unit_kind="LOOSE", first_seen=d(40), last_seen=d(40)), replace=True)

    def buy(nm, day, units, bill):
        ins(sp, "sp_purchase_line", dict(supkey="WSUPPLIE", bill=bill, date=day, seq=1, name27=nm, k20=K(nm), packing="1*10", qty=units / 10.0, free=0.0, units=float(units),
                                         amount_p=1000, net_amount_p=1000, direction="PURCHASE", source_md5="w470"))
        ins(sp, "sp_move", dict(k20=K(nm), date=day, kind="PURCHASE", units=float(units), ref="w470"))

    def sell(nm, day, units, bill):
        ins(sp, "sp_sale_bill", dict(date=day, bill=bill, gross_p=0, disc_p=0, tax_p=0, drcr_p=0, net_p=0, cash_p=0, credit_note=0, source_md5="w470"))
        ins(sp, "sp_sale_line", dict(date=day, bill=bill, seq=1, name20=K(nm), k20=K(nm), pack="1*10", qty_raw="0:%d" % units, units=float(units), rate_p=1000, batch="", expiry=""))
        ins(sp, "sp_move", dict(k20=K(nm), date=day, kind="SALE", units=-float(units), ref=bill))
    for nm, op in ((B, 5), (F, 2), (C, 50), (OX, 1)):
        ins(sp, "sp_move", dict(k20=K(nm), date=d(30), kind="OPENING", units=float(op), ref="w470"))
    buy(A, d(12), 100, "W47P1")                                        # listed on T-14, bought two days later
    buy(C, d(5), 30, "W47P2")                                          # listed on T-7, bought
    buy(E, d(4), 10, "W47P3")                                          # never listed, bought
    buy(OX, d(3), 5, "W47P4")                                          # an orthotic: the engine never lists one
    sell(B, d(9), 5, "A0W47B")                                         # B runs out on T-9; it was on the list of T-14 (in time)
    sell(F, d(11), 3, "A0W47F")                                        # F runs out on T-11; never on a list
    sell(C, d(8), 4, "A0W47C")                                         # C sold, never out
    sell(OX, d(10), 1, "A0W47X")                                       # the orthotic runs out: not a medicine
    sp.commit()
    sp.close()


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine", "--work", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    for p in (a.work, a.por):
        assert p.startswith("/tmp/"), "refusing a non-scratch path: " + p
    os.makedirs(a.work, exist_ok=True)
    n, fails = [0], []

    def check(label, cond, got=None):
        n[0] += 1
        print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(str(got))[:700] + "]") if got is not None else ""))
        if not cond:
            fails.append(label)

    def copydb(src, dst):
        s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
        d = sqlite3.connect(dst)
        s.backup(d)
        d.close()
        s.close()

    def md5f(p):
        return hashlib.md5(open(p, "rb").read()).hexdigest()
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W470 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                    # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    try:
        clinic_users.add_role(store, "staff")
    except ValueError:
        pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    def base_env(side, dbp, adbp, spp):
        env = dict(os.environ, SIDE=side, PORDIR=a.por, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por,
                   CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret,
                   ORDER_PUSH_STUB=os.path.join(a.work, "push_%s.jsonl" % side), DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, W470J=json.dumps(dict(pw=pw)),
                   PORDERS_SOURCE="tables", ORDER_SCORE_FILE=os.path.join(a.work, "score_%s.json" % side))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY"):
            env.pop(k, None)
        return env

    def run(side, fin):
        dbp, adbp, spp = [os.path.join(a.work, "w470_%s_%s.db" % (side, x)) for x in ("fin", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=dict(base_env(side, dbp, adbp, spp), FINDIR=fin), cwd=fin,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (side, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    N = run("new", a.fin_new)
    O = run("old", a.fin_old)
    check("both probes ran to the end (NEW = the box + S470, OLD = the box as it is)", N is not None and O is not None)
    if N is None or O is None:
        print("WALK_S470 RED -- a probe did not finish")
        return 1
    # ------------------------------------------------------------------------------------------------------------------ 1
    print("-- 1  A: the read door's new methods")
    st = {}
    for side, fin in (("new", a.fin_new), ("old", a.fin_old)):
        p = subprocess.run([sys.executable, "-B", "selftest_spine.py"], cwd=os.path.join(fin, "spine"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=900)
        m = re.search(r"SELFTEST OK\s+(\d+) checks", p.stdout)
        st[side] = dict(rc=p.returncode, n=int(m.group(1)) if m else None, last=p.stdout.strip().splitlines()[-1:])
    check("the spine's selftest passes with one check per new method (%s checks; the box as it is: %s)" % (st["new"]["n"], st["old"]["n"]),
          st["new"]["rc"] == 0 and st["old"]["rc"] == 0 and st["new"]["n"] == st["old"]["n"] + 6, st)
    A_ = N["A"]
    check("on the scratch spine: 10 sold and a credit note of 3 read 10 and -3 by the day (returns deducted); the last sale is the credit note's day",
          all(A_["has"].values()) and [x[1] for x in A_["daily"]] == [10.0, -3.0] and A_["last_sale"] == {"date": D(1)}, [A_["daily"], A_["last_sale"]])
    check("a purchase line carries the supplier's printed name, its direction, quantity and free; closing() equals stock().marg_units; a day with no movement "
          "repeats the day before; one row under a key is a family of one",
          A_["purchase"] == [[S2 + " BAREILLY", "PURCHASE", 10.0, 2.0]] and A_["closing"][0]["units"] == A_["closing"][1] == 500.0 and len(set(A_["series"])) == 1
          and len(A_["series"]) == 3 and A_["family"] == 1, [A_["purchase"], A_["closing"], A_["series"], A_["family"]])
    check("NEGATIVE: the box's read door has none of the six, and its sales() counts the credit note as a sale (13 units, not 7)",
          not any(O["A"]["has"].values()) and O["A"]["old_sales_units"] == 13.0, O["A"])
    # ------------------------------------------------------------------------------------------------------------------ 2
    print("-- 2  B: equality on tables (order.engine_source = tables)")
    for basis in ("count", "marg"):
        tn, to = N["B_tables"][basis], O["B_tables"][basis]
        check("on %s: NEW's plan on tables equals the box's, line for line (%d lines) -- and the interim plan" % (basis, to["lines"]),
              tn["plan"] == to["plan"] and tn["interim"] == to["interim"] and tn["lines"] == to["lines"] and to["lines"] > 0 and tn["engine"] == "tables",
              None if tn["plan"] == to["plan"] else [k for k in set(tn["plan"]["vendors"]) | set(to["plan"]["vendors"]) if tn["plan"]["vendors"].get(k) != to["plan"]["vendors"].get(k)][:6])
    check("NEGATIVE: the box's plan has no 'engine' and no 'no_supplier' (the comparison leaves those, and a line's lot / free / family, out)",
          O["B_tables"]["count"]["new_keys"] == [] and N["B_tables"]["count"]["new_keys"] == ["engine", "no_supplier"], [O["B_tables"]["count"]["new_keys"], N["B_tables"]["count"]["new_keys"]])
    # ------------------------------------------------------------------------------------------------------------------ 3
    print("-- 3  B: the spine source")
    r = N["B_rate"]
    check("on spine (the plan says '%s') every item's rate equals the one worked out here from sp_sale_line / sp_sale_bill: %d items (%d with a sale in the window), 0 off; "
          "every line of the plan (%d) prints that rate" % (N["B_engine"], r["items"], r["with_sales"], r["plan_lines"]),
          N["B_engine"] == "spine" and r["items"] > 100 and not r["bad"] and r["plan_lines"] > 0 and not r["bad_lines"], [r["bad"], r["bad_lines"]])
    s = N["B_stock"]
    print("   Marg's stock: the spine's closing of %s against stock_snapshot of %s -- %d items in both; they differ on %d:" % (s["spine_on"], s["snapshot_on"], s["both"], len(s["differ"])))
    for item, q_ss, q_sp, fam in s["differ"]:
        print("      %-30s stock_snapshot %5s · the spine %5s%s" % (item, q_ss, q_sp, ("   (1 of %d under one key: the key's figure shared equally)" % fam) if fam > 1 else "   <-- alone under its key"))
    print("   items of the stock list the spine's closing does not hold under their 20-letter key: %d %s -- every one an orthotic of a family declared in "
          "the spine's rules (F-719; orthotics are S403's, never this engine's); medicines among them: %d" % (len(s["absent"]), s["absent"], len(s["absent_med"])))
    check("Marg's stock from the spine: every medicine of the stock list is read (%d of %d items; none of the rest is a medicine; nothing the list does not hold), "
          "the same day, and the same figure on every item alone under its key (a family's members differ by the equal share -- printed above, a finding)"
          % (s["both"], s["snapshot"]),
          s["both"] == s["spine"] and not s["extra"] and not s["absent_med"] and s["no_closing"] == [] and (not s["same_day"] or not s["alone_differ"]),
          [s["same_day"], s["alone_differ"][:8], s["absent_med"], s["extra"], s["no_closing"]])
    check("the count-basis figures (shelf_figure.figures, every item) are identical on both sides", N["B_shelf"] == O["B_shelf"], [N["B_shelf"], O["B_shelf"]])
    check("a sale bill only the spine holds (28 units): NEW's rate is %s a day, and Marg's stock is the spine's 500" % N["B_neg"]["rate"],
          abs(N["B_neg"]["rate"] - 70 / 28.0) < 1e-9 and N["B_neg"]["stock"] == 500, N["B_neg"])
    check("NEGATIVE: the box's rate is lower by exactly 28 / 28 = 1 a day (%s), and its stock is stock_snapshot's 480" % O["B_neg"]["rate"],
          abs((N["B_neg"]["rate"] - O["B_neg"]["rate"]) - 1.0) < 1e-9 and O["B_neg"]["stock"] == 480, O["B_neg"])
    # ------------------------------------------------------------------------------------------------------------------ 4
    print("-- 4  B.4: arrivals not yet in Marg")
    wn, wo = N["B4"], O["B4"]
    check("received and no bill in Marg yet: 30 and 20 units count as stock, on both bases, on both sides",
          all(w[b] == dict(b=30, c=20) for w in (wn, wo) for b in ("count", "marg")), [wn["count"], wn["marg"], wo["count"], wo["marg"]])
    check("the bill is entered, dated the day BEFORE the receipt (and after the order's own day): NEW drops the 30 units, on both bases; the unbilled 20 stay",
          all(wn[b + "_billed"] == dict(b=None, c=20) for b in ("count", "marg")), [wn["count_billed"], wn["marg_billed"]])
    check("NEGATIVE: the box still counts the 30 units (the bill is dated before the tap, so it never sees it) -- twice, once Marg's stock has them",
          all(wo[b + "_billed"] == dict(b=30, c=20) for b in ("count", "marg")), [wo["count_billed"], wo["marg_billed"]])
    check("with no bill the goods leave the stock on day 15 after the receipt, on both sides (day 14: 20 units, day 15: none)",
          all(w[b + "_days"] == [20, None] for w in (wn, wo) for b in ("count", "marg")), [wn["count_days"], wo["count_days"]])
    # ------------------------------------------------------------------------------------------------------------------ 5
    print("-- 5  B.7 / B.5: a sold item never bought; the lot")
    b7 = N["B7"]
    check("NEW names the never-bought item under no_supplier (%d in all), with its stock and rate, and orders it from nobody" % b7["n"],
          b7["has_key"] and b7["named"] and b7["row"] == dict(item=MN, on_hand=40, rate_per_day=0.36) and not b7["on_a_line"], b7)
    check("the owner's card counts them: '%s', the item in its list" % N["D"]["made"]["nosup"],
          N["D"]["made"]["nosup"] == "%d medicines have no supplier on record" % b7["n"] and N["D"]["made"]["names"], N["D"]["made"])
    check("NEGATIVE: the box's plan drops it silently (no such key, on no line)", not O["B7"]["has_key"] and not O["B7"]["on_a_line"], O["B7"])
    b5 = N["B5"]
    check("a line carries its lot and free from the spine (bought 10 + 2 free: lot 100 units, free 0.2), its supplier the normalised key, its cost per pack",
          b5["line"] and b5["lot"] == 100.0 and b5["free"] == 0.2 and b5["vendor"] == S2 and b5["rate_p"] == 5000 and O["B5"]["line"] and O["B5"]["lot"] is None
          and O["B5"]["qty"] == b5["qty"], [b5, O["B5"]])
    # ------------------------------------------------------------------------------------------------------------------ 6
    print("-- 6  B.8: constants become settings")
    b8 = N["B8"]
    check("the six settings are rows of the setting table at their present values", b8["rows"] == {"order.engine_source": "spine", "order.pace_days": "28",
          "order.dead_after_days": "60", "order.on_order_days": "4", "order.in_transit_days": "14", "order.lot_history_days": "180"}, b8["rows"])
    check("order.pace_days 28 -> 14 moves the rate (%s -> %s a day: 70 units / 28 days, 42 units / 14 days)" % tuple(b8["pace"]),
          abs(b8["pace"][0] - 2.5) < 1e-9 and abs(b8["pace"][1] - 3.0) < 1e-9, b8["pace"])
    check("order.dead_after_days = 1 zeroes the line whose last sale is 2 days old (through purchase_app's one edit)", b8["dead"] == [True, False], b8["dead"])
    check("NEGATIVE: the box, with the same setting rows, reads neither: the rate stays, the line stays", O["B8"]["dead"] == [True, True]
          and O["B8"]["pace"][0] == O["B8"]["pace"][1], [O["B8"]["dead"], O["B8"]["pace"]])
    api = b8["api"]
    check("the owner sets one from the settings card (200, audited, before 28 -> 21); a value out of range and a wrong word are refused (400); a staff login is refused (403)",
          api["ok"] == [200, True, "28", "21"] and api["row"] == "21" and api["audit"] >= 1 and api["low"] == [400, "bad_value"] and api["word"] == [400, "bad_value"]
          and api["staff"][0] == 403, api)
    check("the settings card shows the six keys", N["D"]["made"]["keys"] == 6 and O["D"]["made"]["keys"] == 0, [N["D"]["made"]["keys"], O["D"]["made"]["keys"]])
    check("NEGATIVE: the box's settings route does not know the key (400 bad_key)", O["B8"]["api"]["ok"][0] == 400, O["B8"]["api"])
    dl = [l for l in difflib.unified_diff(open(os.path.join(a.fin_old, "purchase_app.py"), encoding="utf-8").read().splitlines(),
                                          open(os.path.join(a.fin_new, "purchase_app.py"), encoding="utf-8").read().splitlines(), lineterm="", n=0)]
    for l in dl:
        print("      " + l[:170])
    ch = [l for l in dl if (l.startswith("+") or l.startswith("-")) and not l.startswith(("+++", "---"))]
    check("purchase_app.py differs from the box's by the one edit only (the diff above: %d lines, under 12; 2 lines out, 2 in)" % len(dl),
          len(dl) < 12 and len(ch) == 4 and all("plan_line" in l or "DEAD_AFTER_DAYS" in l for l in ch), len(dl))
    # ------------------------------------------------------------------------------------------------------------------ 7
    print("-- 7  C: the trial keeps and scores the real list")
    T = dt.date(TODAY.year + 1, 3, 20)                                   # a far-off 'today': the copies hold no sale or purchase of their own there
    tdb, tsp = os.path.join(a.work, "w470_trial_fin.db"), os.path.join(a.work, "w470_trial_spine.db")
    copydb(a.db, tdb)
    copydb(a.spine, tsp)
    trial_fixture(tdb, tsp, T)
    m0 = md5f(tdb)
    outs = {}
    for side, fin in (("new", a.fin_new), ("old", a.fin_old)):
        od = os.path.join(a.work, "orders_%s" % side)
        os.makedirs(od, exist_ok=True)
        cmd = [sys.executable, "-B", os.path.join(fin, "spine", "order_rehearsal.py"), "--spine", tsp, "--out", od, "--date", T.isoformat()]
        if side == "new":
            cmd += ["--finance-db", tdb, "--from", (T - dt.timedelta(days=14)).isoformat()]
            p = subprocess.run(cmd, cwd=os.path.join(fin, "spine"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=900)
            cmd = [c for c in cmd if c not in ("--from", (T - dt.timedelta(days=14)).isoformat())]
        p = subprocess.run(cmd, cwd=os.path.join(fin, "spine"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=900)
        outs[side] = dict(rc=p.returncode, dir=od, tail=p.stdout.strip().splitlines()[-3:])

    def kept(side, n_):
        try:
            return json.load(open(os.path.join(outs[side]["dir"], "order_rehearsal_%s.json" % (T - dt.timedelta(days=n_)).isoformat()), encoding="utf-8"))
        except (OSError, ValueError):
            return None
    k14, k7, k10, k0 = kept("new", 14), kept("new", 7), kept("new", 10), kept("new", 0)
    check("the trial exits 0 and finance.db is untouched (its md5 before and after: %s)" % m0[:8], outs["new"]["rc"] == 0 and md5f(tdb) == m0, outs["new"])
    check("the kept file of T-14 holds every line as the engine wrote it (3 lines, the same key twice), each with its kind and source 'order_proposal', "
          "key = the spine's key, order_units = qty x pack_size",
          k14 is not None and k14["source"] == "order_proposal" and [(l["key"], l["kind"], l["source"], l["order_units"], l["value_p"]) for l in k14["lines"]]
          == [("W470 ITEM A", "fixed", "order_proposal", 100, 100000), ("W470 ITEM B", "fixed", "order_proposal", 50, 50000), ("W470 ITEM A", "interim", "order_proposal", 20, 20000)],
          k14 and k14["lines"])
    check("the blocked day in between is kept with no proposal (0 lines)", k10 is not None and k10["lines"] == [] and k10["totals"]["proposals"] == 0, k10 and k10["totals"])
    sc7, sc0 = (k7 or {}).get("score") or {}, (k0 or {}).get("score") or {}
    check("the three old scores, by hand. Seven nights after T-14: proposed 2 keys (A merged: 120 units), bought as proposed 1 (A), not bought 1 (B), bought not proposed 0. "
          "Seven nights after T-7: proposed 2, bought 1 (C), not bought 1 (D), bought not proposed 2 (E and the orthotic)",
          [sc7.get(x) for x in ("proposed", "bought_as_proposed", "proposed_not_bought", "bought_not_proposed")] == [2, 1, 1, 0] and sc7.get("hits") == [["W470 ITEM A", 120, 100.0]]
          and [sc0.get(x) for x in ("proposed", "bought_as_proposed", "proposed_not_bought", "bought_not_proposed")] == [2, 1, 1, 2], [sc7, sc0])
    try:
        w = json.load(open(os.path.join(outs["new"]["dir"], "order_score_latest.json"), encoding="utf-8"))
    except (OSError, ValueError):
        w = {}
    check("the owner's week, by hand: bought on list 50% (C on the list, E not; the orthotic left out) · listed and bought within 14 days 50% (A yes, B no) · "
          "2 medicines ran out (B, F), 1 listed in time (B) · Rs 500 listed and not bought · 1 day scored at 7, 1 at 14 (the blocked days in no denominator)",
          [w.get(x) for x in ("bought_on_list_pct", "listed_bought_pct", "stockouts", "stockouts_listed_in_time", "value_not_bought_p", "days_scored_7", "days_scored_14")]
          == [50.0, 50.0, 2, 1, 50000, 1, 1] and sorted((o["key"], o["listed_in_time"]) for o in w.get("stockout_items", [])) == [("W470 ITEM B", True), ("W470 ITEM F", False)], w)
    ko = None
    try:
        ko = json.load(open(os.path.join(outs["old"]["dir"], "order_rehearsal_%s.json" % T.isoformat()), encoding="utf-8"))
    except (OSError, ValueError):
        pass
    props = {"W470 ITEM A", "W470 ITEM B", "W470 ITEM C", "W470 ITEM D"}
    okeys = sorted({l.get("key") for l in (ko or {}).get("lines", [])})
    check("NEGATIVE: the box's trial, on the same copies and the same night, does not keep the proposals: its file has no source and no kind, its lines are what its "
          "own copy of the rules makes (%s), not the four proposed keys, and it scores nothing of them" % okeys,
          ko is not None and "source" not in ko and set(okeys) != props and not props <= set(okeys) and not any("kind" in l for l in ko.get("lines", []))
          and ko.get("score") is None, ko and [ko.get("totals"), ko.get("score")])
    # the same night for real: today, on the copies as they are -- what each trial writes against what the engine proposed today
    con_t = sqlite3.connect("file:%s?mode=ro" % tdb, uri=True)
    real = [json.loads(r[0] or "[]") for r in con_t.execute("SELECT lines FROM order_proposal WHERE day=?", (TODAY.isoformat(),))]
    con_t.close()
    real_items = {K(l["item"]) for ls in real for l in ls}
    today_out = {}
    for side, fin in (("new", a.fin_new), ("old", a.fin_old)):
        od = os.path.join(a.work, "orders_today_%s" % side)
        os.makedirs(od, exist_ok=True)
        cmd = [sys.executable, "-B", os.path.join(fin, "spine", "order_rehearsal.py"), "--spine", tsp, "--out", od] + (["--finance-db", tdb] if side == "new" else [])
        p = subprocess.run(cmd, cwd=os.path.join(fin, "spine"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=900)
        try:
            j = json.load(open(os.path.join(od, "order_rehearsal_%s.json" % TODAY.isoformat()), encoding="utf-8"))
        except (OSError, ValueError):
            j = {}
        today_out[side] = dict(rc=p.returncode, lines=len(j.get("lines") or []), not_proposed=sum(1 for l in (j.get("lines") or []) if l.get("key") not in real_items),
                               source=j.get("source"))
    check("tonight for real, on the copies as they are: the engine proposed %d line(s) today; NEW's file keeps exactly those (%d); "
          "NEGATIVE: the box's trial writes %d lines, %d of them in no proposal of today" % (sum(len(x) for x in real), today_out["new"]["lines"],
                                                                                           today_out["old"]["lines"], today_out["old"]["not_proposed"]),
          today_out["new"]["rc"] == 0 and today_out["new"]["lines"] == sum(len(x) for x in real) and today_out["new"]["not_proposed"] == 0
          and today_out["new"]["source"] == "order_proposal" and today_out["old"]["lines"] > 0 and today_out["old"]["not_proposed"] > 0 and md5f(tdb) == m0, today_out)
    # ------------------------------------------------------------------------------------------------------------------ 8
    print("-- 8  D: the owner's card")
    d8 = N["D"]
    check("with a score file of today the card shows the one line, after 'Who decides the order': '%s'" % d8["made"]["score"],
          d8["made"]["status"] == 200 and d8["made"]["score"] == SCORE_LINE and d8["made"]["after_src"], d8["made"])
    check("with no file: '%s'; with a file three days old: the same" % d8["none"]["score"], d8["none"]["score"] == NOT_READY and d8["stale"]["score"] == NOT_READY,
          [d8["none"]["score"], d8["stale"]["score"]])
    check("in the first week (nothing 7 days old yet) it says when the first score comes: '%s'" % d8["first_week"]["score"],
          (d8["first_week"]["score"] or "").startswith(NOT_READY + " The first week is scored on the night of "), d8["first_week"]["score"])
    check("reception's old page has no such card and no such line", d8["reception"]["card"] is False and not d8["reception"]["s470"] and d8["reception"]["score"] is None, d8["reception"])
    check("NEGATIVE: the box's owner page has no such card", O["D"]["made"]["card"] is False and O["D"]["made"]["score"] is None and O["D"]["made"]["status"] == 200, O["D"]["made"])
    # ------------------------------------------------------------------------------------------------------------------ 9
    print("-- 9  E: the staff-eye walk (DUTY_MAP as it is; no duty moves, no staff screen changes)")
    bad, moved, npages = [], [], 0
    for who, v in N["E"].items():
        for d in v["duties"]:
            if d.get("tile") and d.get("tile_seen") is False:
                bad.append("%s tile %s" % (who, d["tile"]))
            if isinstance(d.get("due_n"), str):
                bad.append("%s %s: %s" % (who, d["id"], d["due_n"]))
            if d.get("door_seen") is False:
                bad.append("%s %s due but its marker is not on the door" % (who, d["id"]))
        for path, h in v["pages"].items():
            npages += 1
            if O["E"][who]["pages"].get(path) != h:
                moved.append("%s %s" % (who, path))
    check("every login's tiles on its home; every due duty's marker on its door", not bad, bad)
    check("every home and every door of reception, darpan, shavez, amir and the owner is the same on both sides (%d pages; clock times and tokens apart) -- "
          "but the owner's old Purchase-orders page, which gains the card" % npages, moved == ["manoj /finance/porders?old=1"], moved)
    # ------------------------------------------------------------------------------------------------------------------ 10
    print("-- 10  the crons' own commands as scripts")
    cr = {}
    newsrc = open(os.path.join(a.fin_new, "order_rules.py"), encoding="utf-8").read()
    i0, i1, ig = newsrc.index("# S470_ORDER_ON_SPINE (04-Oct-2026"), newsrc.index("# ---- S470 end"), newsrc.index('if __name__ == "__main__":')
    mut_dir = os.path.join(a.work, "fin_mut")
    if not os.path.isdir(mut_dir):
        import shutil                                                  # noqa: PLC0415
        shutil.copytree(a.fin_new, mut_dir, ignore=shutil.ignore_patterns("__pycache__"))
    b0 = newsrc.rfind("\n# ====", 0, i0) + 1
    b1 = newsrc.index("\n", i1) + 1
    with open(os.path.join(mut_dir, "order_rules.py"), "w", encoding="utf-8") as fh:        # the block moved BELOW the guard: part 1's fault, on purpose
        fh.write(newsrc[:b0] + newsrc[b1:] + "\n" + newsrc[b0:b1])
    for side, fin in (("new", a.fin_new), ("mut", mut_dir)):
        for slot in ("prepare", "remind17"):
            dbp, adbp, spp = [os.path.join(a.work, "w470_cron_%s_%s_%s.db" % (side, slot, x)) for x in ("fin", "assets", "spine")]
            copydb(a.db, dbp)
            copydb(a.adb, adbp)
            copydb(a.spine, spp)
            env = dict(base_env("cron_" + side, dbp, adbp, spp), ORDER_TICK=slot)
            p = subprocess.run([sys.executable, "-B", "order_rules.py", "tick"], cwd=fin, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=900)
            cr["%s %s" % (side, slot)] = dict(rc=p.returncode, last=mask((p.stdout.strip().splitlines() or [""])[-1])[:200])
    check("order_rules.py tick, as the cron spells it, exits 0 on the built file with ORDER_TICK=prepare and =remind17 (scratch copies)",
          cr["new prepare"]["rc"] == 0 and cr["new remind17"]["rc"] == 0 and '"slot": "prepare"' in cr["new prepare"]["last"], [cr["new prepare"], cr["new remind17"]])
    check("NEGATIVE: the same file with the S470 block moved below its __main__ guard fails as a script (%s)" % cr["mut prepare"]["last"][-60:],
          cr["mut prepare"]["rc"] != 0 and "NameError" in cr["mut prepare"]["last"], cr["mut prepare"])
    check("order_rehearsal.py exited 0 on the scratch copies (section 7); the block of order_rules.py sits above its __main__ guard, as do purchase_app's edit, the read "
          "door's methods and the selftest's function above theirs",
          outs["new"]["rc"] == 0 and i0 < i1 < ig and all(src.index(mark) < src.rindex('if __name__ == "__main__":') for src, mark in (
              (open(os.path.join(a.fin_new, "purchase_app.py"), encoding="utf-8").read(), "dead_after=None"),
              (open(os.path.join(a.fin_new, "spine", "spine_read.py"), encoding="utf-8").read(), "def sales_daily"),
              (open(os.path.join(a.fin_new, "spine", "selftest_spine.py"), encoding="utf-8").read(), "def test_s470"))), [i0, i1, ig])
    print("WALK_S470 %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:900]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
