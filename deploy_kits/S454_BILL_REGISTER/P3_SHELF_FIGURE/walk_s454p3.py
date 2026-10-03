#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p3.py -- kit S454_BILL_REGISTER, part 3 (S454 9: one shelf figure, D667; F-696): THE REAL finance app over SCRATCH COPIES of
finance.db, assets.db and the spine (backup API; the spine copy is the walk's own, written only by the walk), one process per side:

  NEW  the box after part 2 + part 3's built files        OLD  the box after part 2 -- the NEGATIVE CONTROL
  F  the figure: counted 100, 30 sold, 20 bought, 2 returned = 92 whatever Marg says; + 10 arrived by a bill's scan = 102; a later spot answer
     is the base; a part of the count family; no count = Marg's (named); below zero = 0 (named); two items on one spine key split, approximate
  P  the plan: on marg it is today's, line for line; on count its lines carry both figures (no staff screen prints them); F-696 gap (3) --
     an item longer than 20 characters gets its pace (red on the box as it is)
  W  a spot answer is compared with the shelf figure; a count recorded stores the shelf figure beside Marg's (the loss desk still by Marg)
  G  the gap at each closing: constant -- no flag; closed by a filed voucher -- no flag; moved a pack with no voucher -- flagged, the owner's
     line, the card, one more reason on the roster; an approximate item never flagged
  E  the staff-eye walk (DUTY_MAP v5) for reception, darpan, shavez, amir and the owner
Its rows are keyed W454P3; dates from today. No phone number or key in its output.

  --fin-new DIR --fin-old DIR --por DIR --db PATH --adb PATH --spine PATH --work DIR --duty-map FILE
"""
import argparse
import datetime as dt
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
TAG = "W454P3JSON "


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


def DMY(iso):
    return "%s-%s-%s" % (iso[8:10], iso[5:7], iso[:4])


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


def probe():
    SIDE = os.environ["SIDE"]
    NEW = SIDE == "new"
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import purchase_app as pa                                          # noqa: E402
    import order_rules as orr                                          # noqa: E402
    import order_sheet as OS                                           # noqa: E402
    import stock_watch as SW                                           # noqa: E402
    import stock_app                                                   # noqa: E402
    assert orr.__file__.startswith(FIN), orr.__file__
    pa._assets_db = os.environ["ASSETS_DB"]
    SF = None
    if NEW:
        import shelf_figure as SF                                      # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    spw = sqlite3.connect(os.environ["SPINE_DB"], timeout=60)            # the walk's OWN scratch spine
    out = {}

    def G(u, p):
        h = {"X-Clinic-User": u, "X-Clinic-Role": ""}
        if u == "reception":
            h["Cookie"] = "clinic_who=shivani"
        r = fc.get(p, base_url=BASE, headers=h)
        return r.status_code, r.get_data(as_text=True)

    def setv(k, v):
        db.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
        db.commit()

    def k20(n):
        return re.sub(r"\s+", " ", n.strip())[:20].strip()

    def sp_item(name, packing="1*10", kind="LOOSE"):
        spw.execute("INSERT OR REPLACE INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)", (k20(name), name, packing, kind, D(90), D(0)))
        spw.commit()

    def move(name, day, kind, units):
        spw.execute("INSERT INTO sp_move (k20, date, kind, units, ref) VALUES (?,?,?,?,?)", (k20(name), day, kind, float(units), "W454P3"))
        spw.commit()

    snap_as_on = db.execute("SELECT as_on FROM stock_snapshot ORDER BY substr(as_on,7,4) DESC, substr(as_on,4,2) DESC, substr(as_on,1,2) DESC LIMIT 1").fetchone()[0]

    def snap(name, qty, pack=10, as_on=None):
        db.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,?)",
                   (as_on or snap_as_on, name, qty, "1*%d" % pack, pack, NOW.isoformat(), "W454P3 walk"))
        db.commit()

    def count(items, day, part_of=None):
        cid = ins(db, "stock_count", dict(unit="medical", marg_as_on=DMY(day), bill_no="W454P3", bill_date=DMY(day), started_at=day + "T07:00:00",
                                          submitted_at=day + "T07:30:00", submitted_by="W454P3 walk", items_total=len(items), items_counted=len(items), status="submitted"))
        for name, q, marg in items:
            ins(db, "stock_count_item", dict(count_id=cid, item=name, packing="1*10", pack_size=10, marg_qty=marg, counted_qty=q, counted_by="W454P3",
                                             entered_by="W454P3", at=day + "T07:15:00"))
        if part_of:
            db.execute("INSERT INTO stock_count_part (count_id, part_of, recorded_at) VALUES (?,?,?)", (cid, part_of, NOW.isoformat()))
        db.commit()
        return cid

    TM, PM, NM, ZM, FA, FB = ("W454P3 TESTMED", "W454P3 PARTMED", "W454P3 NOCOUNT", "W454P3 NEGMED", "W454P3 FAMILYSHARED A", "W454P3 FAMILYSHARED B")
    BM, BF = "W454P3 BOUNDMED", "W454P3 BEFOREMED"
    for nm in (TM, PM, NM, ZM, FA, BM, BF):
        sp_item(nm)
    bday = D(6)
    c1 = count([(TM, 100, 300), (ZM, 10, 10), (FA, 60, 60), (FB, 40, 40), (BM, 0, 0), (BF, 50, 50)], bday)
    move(BM, bday, "PURCHASE", 100)                                     # a bill of the count day, entered after the count (Marg had 0 then)
    move(BM, D(3), "SALE", -30)
    move(BF, D(7), "PURCHASE", 40)                                      # a bill of the day before, already in Marg's 50 at the count
    move(BF, D(3), "SALE", -10)
    move(TM, D(4), "SALE", -30)
    move(TM, D(3), "SALE_RETURN", 2)
    move(TM, D(2), "PURCHASE", 20)
    move(ZM, D(3), "SALE", -50)
    move(FA, D(3), "SALE", -50)                                         # one spine key for A and B: their sales pooled
    for nm, q in ((TM, 555), (PM, 9), (NM, 77), (ZM, 10), (FA, 60), (FB, 40), (BM, 70), (BF, 40)):
        snap(nm, q)
    # ---------------------------------------------------------------- F  the figure
    if NEW:
        f = lambda n: SF.figures(db, items=[n]).get(n) or {}            # noqa: E731
        out["F_92"] = [f(TM).get("shelf"), f(TM).get("marg"), f(TM).get("named")]
        bm, bf = f(BM), f(BF)
        out["F_bound"] = dict(bm=[bm.get("shelf"), bm.get("boundary"), bm.get("base"), bm.get("sold"), bm.get("bought"), bm.get("named")],
                              bf=[bf.get("shelf"), bf.get("boundary"), bf.get("named")])
        oid = ins(db, "purchase_order", dict(created_at=D(3) + "T10:00:00", created_by="W454P3", vendor="W454P3 SUPPLIER", status="received",
                                              received_at=D(2) + "T11:00:00", total_p=0, section="Medicines"))
        ins(db, "purchase_order_line", dict(order_id=oid, item=TM, packs=1, pack_size=10, units=10, rate_p=100, value_p=100))
        db.execute("CREATE TABLE IF NOT EXISTS order_scan_tie (order_id INTEGER PRIMARY KEY, asset_bill_id INTEGER UNIQUE NOT NULL, stamp TEXT, scan_at TEXT, "
                   "tied_at TEXT NOT NULL, how TEXT NOT NULL, arrived INTEGER NOT NULL DEFAULT 0)")
        db.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,1)",
                   (oid, 99000001, "W454P3-1", D(2) + "T11:00:00", NOW.isoformat(), "scan"))
        db.commit()
        out["F_102"] = f(TM).get("shelf")
        # the spot comparison BEFORE a spot becomes the base (W): the point's expectation = the shelf figure
        P = SW.write_point(db, TM, 98, "spot", "W454P3 walk", silent=True)
        out["W_spot"] = dict(expected=P.get("expected"), gap=P.get("gap"))
        out["F_spot"] = f(TM).get("shelf")                              # the spot answer (98, today) is now the base
        c2 = count([(PM, 40, 9)], D(1), part_of=c1)
        out["F_part"] = f(PM).get("shelf")
        out["F_none"] = [f(NM).get("shelf"), f(NM).get("named")]
        out["F_neg"] = [f(ZM).get("shelf"), f(ZM).get("named")]
        fa_, fb_ = f(FA), SF.figures(db, items=[FA, FB])
        out["F_family"] = [fb_[FA]["shelf"], fb_[FB]["shelf"], fb_[FA]["approx"], fb_[FB]["approx"]]
        out["F_boundary"] = SF.boundary_report(db)[:3]
        _ = (c2, fa_)
    else:
        P = SW.write_point(db, TM, 98, "spot", "W454P3 walk", silent=True)
        out["W_spot"] = dict(expected=P.get("expected"), gap=P.get("gap"))
    # ---------------------------------------------------------------- P  the plan (Marg's basis: today's, line for line)
    LN = "W454P3 LONGNAMEMEDICINE TAB"
    md5 = "w454p3" + hashlib.md5(("i" + SIDE).encode()).hexdigest()[:26]
    ins(db, "purchase_export", dict(md5=md5, type="ITEMWISE", file="W454P3", period_from=D(60), period_to=D(0), export_stamp=NOW.strftime("%Y%m%d-%H%M%S"),
                                    received_at=NOW.isoformat(), n_rows=1, grand_amount_p=0), replace=True)
    ins(db, "purchase_line", dict(supplier_norm=pa.supplier_key("KEDAR PHARMACEUTICAL"), bill_no="W454P3", bill_date=D(20), month=D(20)[:7], item=LN, packing="1*10",
                                  qty=10, free=0, rate_p=1000, amount_p=10000, direction="PURCHASE", source_md5=md5, line_type="ITEMWISE"))
    for i in range(10):
        ins(db, "sale_line_item", dict(unit="medical", business_date=D(i + 1), bill_no="W454P3-%d" % i, item_name=LN[:20], item_key=LN[:20], qty_raw="2:0",
                                       pack="1*10", is_return=0))
    snap(LN, 0)
    db.commit()

    def plan_lines(basis):
        setv("order.stock_basis", basis)
        p = orr.plan(db, TODAY)
        return sorted((v.get("vendor_norm") or "", l["item"], l["qty"], l.get("marg_qty"), l.get("shelf_qty")) for v in (p.get("vendors") or {}).values() for l in v["lines"])
    lm = plan_lines("marg")
    out["P_marg"] = [(a, b, c) for a, b, c, _d, _e in lm]
    out["P_long_marg"] = any(x[1] == LN for x in lm)
    if NEW:
        lc = plan_lines("count")
        out["P_count_both"] = all(x[3] is not None for x in lc) and any(x[4] is not None for x in lc)
        out["P_long_count"] = any(x[1] == LN for x in lc)
        out["P_count_n"] = len(lc)
        # goods received and not yet in Marg: an item with no count keeps them; an item on the shelf figure has them in the figure already
        oid2 = ins(db, "purchase_order", dict(created_at=D(2) + "T10:00:00", created_by="W454P3", vendor="W454P3 SUPPLIER", status="received",
                                               received_at=D(1) + "T11:00:00", total_p=0, section="Medicines"))
        ins(db, "purchase_order_line", dict(order_id=oid2, item=NM, packs=2, pack_size=10, units=20, rate_p=100, value_p=200, supplied=2))
        db.commit()
        way = {}
        for basis in ("marg", "count"):
            setv("order.stock_basis", basis)
            tr = orr._snapshot_inputs(db, TODAY)[4]
            way[basis] = [(tr.get(pa.norm(NM)) or {}).get("units"), (tr.get(pa.norm(TM)) or {}).get("units")]
        out["P_way"] = way
    setv("order.stock_basis", "count")
    s, h = G("reception", "/finance/porders/s454/order")
    out["P_staff"] = dict(status=s, shelf=("shelf" in text_of(h).lower()), marg_word=("Marg " in text_of(h)))
    # ---------------------------------------------------------------- W  a count recorded
    if NEW:
        shelf_before = SF.figures(db, items=[TM])[TM]["shelf"]
        with fa.app.test_request_context():
            r = stock_app._record_count(dict(items=[dict(item=TM, counted_qty=95, marg_qty=555, pack_size=10, packing="1*10")], marg_as_on=DMY(D(0)),
                                             bill_no="W454P3C", bill_date=DMY(D(0))), dict(user="W454P3 walk"))
        cid = r.get("count_id")
        row = db.execute("SELECT marg_qty, counted_qty, shelf_qty FROM stock_count_item WHERE count_id=? AND item=?", (cid, TM)).fetchone()
        dif = db.execute("SELECT marg_qty, counted_qty, diff FROM stock_diff WHERE count_id=? AND item=?", (cid, TM)).fetchone()
        out["W_count"] = dict(ok=r.get("ok"), row=list(row) if row else None, diff=list(dif) if dif else None, shelf_before=shelf_before)
    # ---------------------------------------------------------------- G  the gap at each closing
    if NEW:
        GM = "W454P3 GAPMED"
        sp_item(GM)
        count([(GM, 100, 80)], D(0))
        days = [(TODAY + dt.timedelta(days=i)).isoformat() for i in range(1, 7)]
        res = []
        for i, (dday, marg) in enumerate(zip(days, (80, 80, 80, 100, 90, 90))):
            if i == 3:                                                  # Amir files the count's voucher (+20) -- Marg moves by it
                db.execute("CREATE TABLE IF NOT EXISTS stock_voucher_line (id INTEGER PRIMARY KEY, count_id INTEGER, round_no INTEGER, kind TEXT, batch_no INTEGER, item TEXT, change REAL)")
                ins(db, "stock_voucher_line", dict(count_id=0, round_no=9, kind="RECEIVE", batch_no=1, batches_n=1, line_no=1, section="", family="", item=GM,
                                                   packing="1*10", pack=10, marg_from=80, change=20, marg_to=100, counted=100, made_by="W454P3", made_at=NOW.isoformat()))
                ins(db, "stock_voucher_entered", dict(count_id=0, round_no=9, kind="RECEIVE", batch_no=1, marg_voucher_no="W454P3", entered_on=dday, by_user="W454P3",
                                                      at=NOW.isoformat()))
                db.commit()
            for nm, q in ((GM, marg), (FA, 60 - 10 * i), (FB, 40)):
                snap(nm, q, as_on=DMY(dday))
            n = SF.record_gaps(db)
            row = db.execute("SELECT gap, flagged, why FROM s454_shelf_gap WHERE as_on=? AND item=?", (dday, GM)).fetchone()
            fam = db.execute("SELECT flagged FROM s454_shelf_gap WHERE as_on=? AND item=?", (dday, FA)).fetchone()
            res.append(dict(day=dday, marg=marg, rows=n, gap=row[0] if row else None, flagged=row[1] if row else None, why=(row[2] or "") if row else "",
                            fam_flag=fam[0] if fam else None))
        out["G"] = res
        out["G_line"] = [l["text"] for l in OS.owner_lines(db) if "shelf figure" in l["text"]]
        s, h = G("manoj", "/finance/porders?old=1")
        m = re.search(r'<div [^>]*id="s454gap".*?</div>\s*(?:<details.*?</details>)?</div>', h, re.S)
        out["G_card"] = text_of(m.group(0)) if m else ""
        S = SW.settings(db)
        sp = SW.Spine(os.environ["SPINE_DB"])
        cands = SW._candidates(db, sp, S)
        c = cands.get(k20(GM)) or {}
        out["G_roster"] = dict(gap=c.get("gap"), reason=SW._reasons(c, S)[0] if c else "")
        RV = SW.build_roster(db, day=TODAY + dt.timedelta(days=7), S=S, sp=sp, who="W454P3 walk", force=True)
        out["G_roster_cap"] = [len([x for x in (RV.get("rows") or []) if not str(x.get("reason") or "").startswith("you asked")]), S["cap"]]
    out["E"] = staff_eye(fc, BASE)
    print(TAG + json.dumps(out, default=str))


def staff_eye(fc, BASE):
    import portal as po                                                # noqa: PLC0415
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W454J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True)
    eye = {}
    for who in ("reception", "darpan", "shavez", "amir", "manoj"):
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r.get_data(as_text=True))]
        rows = []
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
            if door and mark and isinstance(n, int) and n > 0 and str(door).startswith("/finance/"):
                path, body = str(door), ""
                ck = "clinic_sso=" + tok + ("; clinic_who=shivani" if who == "reception" else "")
                for _hop in range(4):
                    rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
                    if rr2.status_code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                        path = rr2.headers["Location"].replace(BASE, "")
                        continue
                    body = rr2.get_data(as_text=True)
                    break
                row["door_seen"] = mark in body
            rows.append(row)
        eye[who] = dict(status=r.status_code, duties=rows)
    ro.close()
    return eye


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
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W454P3 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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

    def run(side, fin):
        dbp, adbp, spp = (os.path.join(a.work, "w454p3_%s.db" % side), os.path.join(a.work, "w454p3_%s_assets.db" % side),
                          os.path.join(a.work, "w454p3_%s_spine.db" % side))
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por,
                   CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret,
                   ORDER_PUSH_STUB=os.path.join(a.work, "push_%s.jsonl" % side), DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, W454J=json.dumps(dict(pw=pw)),
                   PORDERS_SOURCE="tables")
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (side, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    N = run("new", a.fin_new)
    O = run("old", a.fin_old)
    check("both probes ran to the end (NEW = after part 3, OLD = the box after part 2)", N is not None and O is not None)
    if N is None or O is None:
        print("WALK_S454P3 RED -- a probe did not finish")
        return 1
    print("-- F  the shelf figure")
    check("counted 100, then 30 sold, 20 bought, 2 returned: %s whatever Marg says (%s)" % (N["F_92"][0], N["F_92"][1]), N["F_92"][0] == 92 and N["F_92"][1] == 555, N["F_92"])
    check("with 10 arrived by a bill's scan and not in Marg: %s" % N["F_102"], N["F_102"] == 102, N["F_102"])
    fb = N["F_bound"]
    check("the boundary (9.1): a bill dated the count day but entered after it (Marg had 0 at the count) is in: counted 0, sold 30, that bill 100 = %s "
          "(boundary %s); a bill of the day before that Marg already carried at the count is not added twice: %s" % (fb["bm"][0], fb["bm"][1], fb["bf"][0]),
          fb["bm"][:2] == [70, 100.0] and fb["bf"][:2] == [40, 0.0] and fb["bm"][5] is None, fb)
    check("NEGATIVE: without the boundary the same item reads below zero (counted %s, sold %s, bought after the count day %s)" % tuple(fb["bm"][2:5]),
          fb["bm"][2] - fb["bm"][3] + fb["bm"][4] < 0, fb["bm"])
    check("a later spot answer is the base: %s" % N["F_spot"], N["F_spot"] == 98, N["F_spot"])
    check("an item a part of the count family holds: that part's figure (%s)" % N["F_part"], N["F_part"] == 40, N["F_part"])
    check("no count: Marg's figure, named (%s)" % N["F_none"], N["F_none"] == [77, "no_count"], N["F_none"])
    check("below zero: zero, named (%s)" % N["F_neg"], N["F_neg"] == [0, "below_zero"], N["F_neg"])
    check("two items on one spine key share its sales by their counted share, marked approximate: %s" % N["F_family"],
          N["F_family"][:2] == [30, 20] and N["F_family"][2] and N["F_family"][3], N["F_family"])
    print("-- P  the plan")
    check("on order.stock_basis = marg the plan equals today's (the box after part 2), line for line (%d lines)" % len(N["P_marg"]),
          N["P_marg"] == O["P_marg"], [x for x in N["P_marg"] if x not in O["P_marg"]][:5] + ["/"] + [x for x in O["P_marg"] if x not in N["P_marg"]][:5])
    check("on count the plan's lines carry both figures (Marg's and the shelf's) for the owner", N["P_count_both"], N["P_count_n"])
    check("goods received and not yet in Marg, on count: an item with no count counts them once (W454P3 NOCOUNT 20); an order that arrived by "
          "its scan is in the shelf figure, not on the way (W454P3 TESTMED none): %s" % N["P_way"]["count"],
          N["P_way"]["count"] == [20, None], N["P_way"])
    check("NEGATIVE (part 1's way, kept on marg as the brief asks): the arrived-by-scan order of W454P3 TESTMED is counted twice -- in "
          "transit 10 and on the way 10: %s" % N["P_way"]["marg"], N["P_way"]["marg"] == [20, 20], N["P_way"])
    check("no staff screen prints them (the reception order list: no 'shelf', no 'Marg')", not N["P_staff"]["shelf"] and not N["P_staff"]["marg_word"], N["P_staff"])
    check("F-696 gap (3): an item whose name is longer than 20 characters gets its pace and its line on count", N["P_long_count"], N["P_long_count"])
    check("NEGATIVE: the box as it is never lists it (no pace for its name)", not O["P_long_marg"], O["P_long_marg"])
    print("-- W  the spot answer and the count")
    check("a spot answer is compared with the shelf figure: expected %s (the box as it is: %s)" % (N["W_spot"]["expected"], O["W_spot"]["expected"]),
          N["W_spot"]["expected"] == 102.0 and N["W_spot"]["gap"] == -4.0 and O["W_spot"]["expected"] != 102.0, [N["W_spot"], O["W_spot"]])
    wc = N["W_count"]
    check("a count recorded stores the shelf figure beside Marg's on its row (%s); the loss desk's difference stays by Marg (%s)" % (wc["row"], wc["diff"]),
          wc["ok"] and wc["row"] and wc["row"][2] == wc["shelf_before"] and wc["diff"] and wc["diff"][2] == 95 - 555, wc)
    print("-- G  the gap at each closing")
    G_ = N["G"]
    check("constant over three closings: no flag; closed by a filed voucher (+20): no flag, the gap 0", [g["flagged"] for g in G_[:4]] == [0, 0, 0, 0]
          and G_[3]["gap"] == 0, [(g["day"], g["gap"], g["flagged"], g["why"][:60]) for g in G_[:4]])
    check("moved a pack with no voucher: flagged, and it stays flagged at the next closing until the item is counted again ('%s')" % G_[4]["why"][:80], G_[4]["flagged"] == 1 and G_[5]["flagged"] == 1, [(g["gap"], g["flagged"]) for g in G_[4:]])
    check("an approximate item (two items on one key) is never flagged", all(not g["fam_flag"] for g in G_), [g["fam_flag"] for g in G_])
    check("the owner's line: '%s'" % ((N["G_line"] or [""])[0][:120]), bool(N["G_line"]) and "W454P3 GAPMED" in N["G_line"][0], N["G_line"])
    check("the owner's card: '%s'" % N["G_card"][:120], "moved apart on" in N["G_card"], N["G_card"][:300])
    check("the roster: one more reason ('%s'), never past its cap %s" % (N["G_roster"]["reason"][:60], N["G_roster_cap"]),
          N["G_roster"]["gap"] == 1 and "moved apart" in N["G_roster"]["reason"] and N["G_roster_cap"][0] <= N["G_roster_cap"][1], [N["G_roster"], N["G_roster_cap"]])
    print("-- E  the staff-eye walk (DUTY_MAP v5)")
    bad = []
    for who, v in N["E"].items():
        for d in v["duties"]:
            if d.get("tile") and d.get("tile_seen") is False:
                bad.append("%s tile %s" % (who, d["tile"]))
            if isinstance(d.get("due_n"), str):
                bad.append("%s %s: %s" % (who, d["id"], d["due_n"]))
            if d.get("door_seen") is False:
                bad.append("%s %s due but its marker is not on the door" % (who, d["id"]))
    check("every login's tiles on its home; every due duty's marker on its door", not bad, bad)
    print("-- the boundary: %s" % N.get("F_boundary"))
    print("WALK_S454P3 %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:900]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
