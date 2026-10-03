#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p3b.py -- kit S454_BILL_REGISTER, P3B_FIRST_DAY (S454 18: what the first afternoon of use showed): THE REAL finance app over
SCRATCH COPIES of finance.db, assets.db and the spine (backup API), one process per side:

  NEW  the box after part 3 + P3B's built files        OLD  the box as it is (after part 3) -- the NEGATIVE CONTROL
  A  18.1  F-712: what the asset app stores for a scan (one reading, no page of its own) -- so no guess is built; the line "Ek scan mein ek
           hi bill." under the scan button on the home and under every "Bill scan karo" on "Maal aaya?"; no question of a new kind
  B  18.2  the arrival screen's button: "Maal aa gaya" with every line Aa gaya, "Save kijiye" while a line is Kam aaya / Nahi mila (the
           page's own rule); the rows written are the same as the box writes
  C  18.3  "P.L." dropped like PVT / LTD; a "P" or "A.P.L." inside a name kept; September's Sarvam counter: supplier misreads fall by one
  D  18.4  on marg an order that arrived by its scan is on the way once (in transit), not twice
  E  18.5  F-713: a credit note is a return in the spine's sales reading: the sale, the return, the expected stock
  F  18.6  the owner's agreement card says on what stock: the stored sheet "on Marg's stock"; a comparison taken on count / marg says so
  S  the staff-eye walk (DUTY_MAP v5) for reception, darpan, shavez, amir and the owner
Its rows are keyed W454P3B; dates from today. No phone number or key in its output.

  --fin-new DIR --fin-old DIR --por DIR --db PATH --adb PATH --spine PATH --work DIR --duty-map FILE
"""
import argparse
import datetime as dt
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
TAG = "W454P3BJSON "
ONE_HI, ONE_EN = "Ek scan mein ek hi bill.", "One bill per scan."


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


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
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import purchase_app as pa                                          # noqa: E402
    import order_rules as orr                                          # noqa: E402
    import order_sheet as OS                                           # noqa: E402
    import stock_watch as SW                                           # noqa: E402
    import scan_register as SR                                         # noqa: E402
    assert orr.__file__.startswith(FIN) and SR.__file__.startswith(FIN), (orr.__file__, SR.__file__)
    pa._assets_db = os.environ["ASSETS_DB"]
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    spw = sqlite3.connect(os.environ["SPINE_DB"], timeout=60)            # the walk's OWN scratch spine
    adb = sqlite3.connect("file:%s?mode=ro" % os.environ["ASSETS_DB"], uri=True)
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

    def order(vendor, items, status="sent", created=None, received=None):
        oid = ins(db, "purchase_order", dict(created_at=created or (NOW - dt.timedelta(hours=1)).isoformat(), created_by="W454P3B walk", vendor=vendor,
                                              status=status, received_at=received, total_p=0, section="Medicines"))
        lids = [ins(db, "purchase_order_line", dict(order_id=oid, item=it, packs=5, pack_size=10, units=50, rate_p=100, value_p=500)) for it in items]
        db.commit()
        return oid, lids
    # ---------------------------------------------------------------- A  18.1
    cols = [r[1] for r in adb.execute("PRAGMA table_info(bills)")]
    icols = [r[1] for r in adb.execute("PRAGMA table_info(bill_items)")]
    b121 = adb.execute("SELECT id, total_amount, bill_no FROM bills WHERE stamp_no='B-0121'").fetchone()
    isum = adb.execute("SELECT COALESCE(SUM(amount),0), COUNT(*) FROM bill_items WHERE bill_id=?", (b121[0],)).fetchone() if b121 else None
    out["A_store"] = dict(page_cols=[c for c in cols + icols if "page" in c.lower()], b121=([b121[1], round(isum[0], 2), isum[1]] if b121 else None))
    o1, l1 = order("W454P3B SUPPLIER ONE", ["W454P3B MED A", "W454P3B MED B", "W454P3B MED C"])
    o2, l2 = order("W454P3B SUPPLIER TWO", ["W454P3B MED D", "W454P3B MED E"])
    s, h = G("reception", "/finance/porders")
    t = text_of(h)
    out["A_home"] = dict(status=s, line=(ONE_HI in t), after=(t.find(ONE_HI) > t.find("Naya bill scan karo") >= 0) if ONE_HI in t else False,
                         once=t.count(ONE_HI))
    s, h = G("reception", "/finance/porders/s454/maal")
    cards = len(re.findall(r'data-order="\d+"', h))
    blocks = re.findall(r'<div class="card" data-order="\d+">.*?</div></div>(?=<div class="card"|$|<)', h, re.S)
    under = sum(1 for b in re.split(r'(?=<div class="card" data-order=)', h) if "data-order=" in b and re.search(r"📷[^<]*</a>\s*<div[^>]*>%s</div>" % re.escape(ONE_HI), b))
    out["A_maal"] = dict(status=s, cards=cards, lines=text_of(h).count(ONE_HI), under=under, _b=len(blocks))
    s, h = G("manoj", "/finance/porders")
    out["A_owner"] = dict(status=s, en=(ONE_EN in text_of(h)), hi=(ONE_HI in text_of(h)))
    s, js = G("reception", "/finance/porders/api/s454/state")
    try:
        out["A_q"] = json.loads(js).get("counts")
    except ValueError:
        out["A_q"] = js[:200]
    # ---------------------------------------------------------------- B  18.2
    s, h = G("reception", "/finance/porders/s454/maal/%d" % o1)
    m = re.search(r'<button class="big" id="maalok"([^>]*)>([^<]*)</button>', h)
    out["B_btn"] = dict(status=s, attrs=(m.group(1) if m else ""), text=(m.group(2) if m else None))
    fn = re.search(r"function arLabel\(\)\{(.*?)\}\n", h, re.S)
    out["B_js"] = dict(label_fn=(fn.group(1) if fn else ""), called=bool(re.search(r"function arHow\(id,how\)\{.*?arLabel\(\);\}", h, re.S)))
    s1, j1 = POST("reception", "/finance/porders/api/s454/arrive", dict(order_id=o1, lines=[dict(id=l1[0], how="short", supplied=2), dict(id=l1[1], how="missing")]))
    s2, j2 = POST("reception", "/finance/porders/api/s454/arrive", dict(order_id=o2, lines=[]))
    rows = [list(r) for r in db.execute("SELECT o.vendor, l.item, l.packs, l.supplied, l.short, l.missing, l.arrived_by, o.status FROM purchase_order_line l "
                                        "JOIN purchase_order o ON o.id=l.order_id WHERE o.id IN (?,?) ORDER BY l.id", (o1, o2))]
    out["B_rows"] = dict(codes=[s1, s2], j=[j1.get("ok"), j2.get("ok")], rows=rows)
    # ---------------------------------------------------------------- C  18.3
    cx = SR.Ctx(db)
    out["C_norm"] = {x: SR.sup_norm(x) for x in ("GUNINA PHARMACEUTICALS P.L. LTD.", "GUNINA PHARMACEUTICALS PVT. LTD.", "A.P.L. TRADERS", "P L PHARMA",
                                                  "PEE ELL PHARMA", "S P DISTRIBUTORS", "AMRIT PHARMA P. LTD")}
    out["C_agree"] = SR.supplier(cx, "GUNINA PHARMACEUTICALS P.L. LTD.", "GUNINA PHARMACEUTICALS")
    out["C_keep"] = SR.supplier(cx, "SAI P.L. AGENCIES", "SAI AGENCIES")
    sv = SR.sarvam(db, "2026-09")
    out["C_sarvam"] = dict(n=sv["n"], misses=sv["misses"])
    scans = SR.asset_scans(db) or {}
    rows_ = {}
    for bid, l in SR.links(db).items():                            # every linked bill: the supplier as the counter reads it
        b_ = db.execute("SELECT supplier, bill_no, bill_date FROM purchase_bill WHERE id=?", (bid,)).fetchone()
        s_ = scans.get(l["scan"])
        if b_ and s_ and str(b_[2])[:7] == "2026-09":
            rows_[str(bid)] = [s_.get("vendor"), b_[0], b_[1], SR.supplier(cx, s_.get("vendor"), b_[0])]
    out["C_rows"] = rows_
    # ---------------------------------------------------------------- D  18.4
    WM = "W454P3B WAYMED"
    oid3, _l3 = order("W454P3B SUPPLIER THREE", [WM], status="received", created=D(3) + "T10:00:00", received=D(2) + "T11:00:00")
    db.execute("UPDATE purchase_order_line SET packs=1, units=10 WHERE order_id=?", (oid3,))
    db.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,1)",
               (oid3, 99054301, "W454P3B-1", D(2) + "T11:00:00", NOW.isoformat(), "scan"))
    db.commit()
    way = {}
    for basis in ("marg", "count"):
        setv("order.stock_basis", basis)
        tr = orr._snapshot_inputs(db, TODAY)[4]
        way[basis] = (tr.get(pa.norm(WM)) or {}).get("units")
    out["D_way"] = way
    setv("order.stock_basis", "count")
    # ---------------------------------------------------------------- E  18.5
    CNM = "W454P3B CNMED"
    k = SW._k20(CNM)
    ins(spw, "sp_item", dict(k20=k, name=CNM, packing="1*10", unit_kind="LOOSE", first_seen=D(30), last_seen=D(0)), replace=True)
    ins(spw, "sp_close", dict(k20=k, as_on=D(5), units=100.0))
    ins(spw, "sp_sale_line", dict(date=D(2), bill="A0W54301", seq=1, name20=k, k20=k, pack="1*10", qty_raw="0:10", units=10.0, rate_p=1000))
    ins(spw, "sp_sale_line", dict(date=D(1), bill="CN0W5431", seq=1, name20=k, k20=k, pack="1*10", qty_raw="0:3", units=3.0, rate_p=1000))
    spw.commit()
    sp = SW.Spine(os.environ["SPINE_DB"])
    s_ = sp.sales(CNM, D(5), D(0))
    e_ = SW.expected_units(db, sp, CNM)
    out["E"] = dict(u=s_["u"], ret=s_["ret"], n=s_["n"], expected=e_.get("expected"), sold=e_.get("sold"))
    # ---------------------------------------------------------------- F  18.6
    def card():
        s, h = G("manoj", "/finance/porders?old=1")
        m = re.search(r'<div [^>]*id="s454cmp"><b>([^<]*)</b>(?:\s*<span id="s454basis">([^<]*)</span>)?', h)
        return [s, _html.unescape(m.group(1)) if m else None, _html.unescape(m.group(2)) if m and m.group(2) else None]
    out["F_stored"] = card()
    ns = OS.newest_sheet(db)
    out["F_cmp_before"] = (json.loads(ns["cmp"]) or {}).get("x") if ns and ns.get("cmp") else None
    res = {}
    if ns:
        for basis in ("count", "marg"):
            setv("order.stock_basis", basis)
            c = OS.compare(db, ns["id"])
            res[basis] = dict(stored=c.get("basis"), card=card())
    out["F_taken"] = res
    setv("order.stock_basis", "count")
    out["S"] = staff_eye(fc, BASE)
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
        fh.write("# W454P3B walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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
        dbp, adbp, spp = [os.path.join(a.work, "w454p3b_%s_%s.db" % (side, x)) for x in ("fin", "assets", "spine")]
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
    check("both probes ran to the end (NEW = after P3B, OLD = the box as it is)", N is not None and O is not None)
    if N is None or O is None:
        print("WALK_S454P3B RED -- a probe did not finish")
        return 1
    print("-- A  18.1 two bills in one scan (F-712)")
    st = N["A_store"]
    print("   what the asset app stores: one reading per scan (bills: vendor, bill_no, bill_date, total_amount; bill_items: the lines); columns "
          "holding a page: %s (page_of is S441's join of a forgotten page, not a page's own reading). B-0121: total %s, its %s item lines add to %s "
          "-- the first bill only; nothing of the second bill is stored." % (st["page_cols"], (st["b121"] or [None])[0], (st["b121"] or [0, 0, 0])[2],
                                                                            (st["b121"] or [0, 0])[1]))
    check("so no two-bill question is built: the stored reading has no page of its own (only S441's page_of join) and B-0121's lines add to its "
          "first bill (within Rs 2)", st["page_cols"] == ["page_of"] and st["b121"] and abs(st["b121"][0] - st["b121"][1]) <= 2, st)
    check("no question of a new kind: the reception counts are the same on both sides (a two-page bill asks nothing new)", N["A_q"] == O["A_q"], [N["A_q"], O["A_q"]])
    check("the home: 'Ek scan mein ek hi bill.' once, right under 'Naya bill scan karo'", N["A_home"]["status"] == 200 and N["A_home"]["after"] and N["A_home"]["once"] == 1, N["A_home"])
    check("NEGATIVE: the box as it is has no such line on the home", not O["A_home"]["line"], O["A_home"])
    check("Maal aaya?: the line under every 'Bill scan karo' (%d cards)" % N["A_maal"]["cards"],
          N["A_maal"]["cards"] >= 2 and N["A_maal"]["under"] == N["A_maal"]["cards"] == N["A_maal"]["lines"], N["A_maal"])
    check("NEGATIVE: the box as it is has none on Maal aaya?", O["A_maal"]["lines"] == 0 and O["A_maal"]["cards"] == N["A_maal"]["cards"], O["A_maal"])
    check("the owner's English: 'One bill per scan.'", N["A_owner"]["en"] and not N["A_owner"]["hi"], N["A_owner"])
    print("-- B  18.2 the arrival screen's button")
    b, j = N["B_btn"], N["B_js"]
    rule = "var b=document.getElementById('maalok'),s=false;for(var k in HOW){if(HOW[k]==='short'||HOW[k]==='missing'){s=true;}}b.textContent=b.getAttribute(s?'data-save':'data-ok');"
    check("it opens reading 'Maal aa gaya' (every line Aa gaya), with 'Save kijiye' as its other word", b["status"] == 200 and b["text"] == "Maal aa gaya"
          and 'data-ok="Maal aa gaya"' in b["attrs"] and 'data-save="Save kijiye"' in b["attrs"], b)
    check("the page's rule: any line tapped Kam aaya or Nahi mila -> 'Save kijiye'; every tap undone to Aa gaya -> 'Maal aa gaya'; it runs on every tap",
          j["label_fn"] == rule and j["called"], j)
    check("NEGATIVE: the box as it is keeps 'Maal aa gaya' whatever is tapped (no second word, no rule)", 'data-save' not in O["B_btn"]["attrs"] and not O["B_js"]["label_fn"], [O["B_btn"], O["B_js"]])
    check("the rows written are the same as the box writes (one short, one missing, one received; an order with nothing tapped)",
          N["B_rows"] == O["B_rows"] and N["B_rows"]["codes"] == [200, 200], [N["B_rows"], O["B_rows"]])
    print("-- C  18.3 'P.L.'")
    cn, co = N["C_norm"], O["C_norm"]
    check("'GUNINA PHARMACEUTICALS P.L. LTD.' reads 'GUNINA PHARMACEUTICALS' and agrees with Marg's supplier", cn["GUNINA PHARMACEUTICALS P.L. LTD."] == "GUNINA PHARMACEUTICALS"
          and N["C_agree"] == "agree", [cn["GUNINA PHARMACEUTICALS P.L. LTD."], N["C_agree"]])
    moved = {k: (O["C_rows"].get(k), v) for k, v in N["C_rows"].items() if O["C_rows"].get(k) != v}
    check("on September's real linked bills exactly one supplier reading moves, and it is the 'P.L.' scan: %s" % [(v[1][0], v[1][1], v[1][2]) for v in moved.values()],
          len(moved) == 1 and all("P.L." in str(v[1][0]).upper() and v[1][3] == "agree" for v in moved.values()), moved)
    check("NEGATIVE: the box as it is leaves an 'L' in the name and reads that scan's supplier as differing",
          co["GUNINA PHARMACEUTICALS P.L. LTD."] != "GUNINA PHARMACEUTICALS" and len(moved) == 1 and all(v[0] and v[0][3] == "differ" for v in moved.values()),
          [co["GUNINA PHARMACEUTICALS P.L. LTD."], moved])
    check("nothing else moves: 'A.P.L. TRADERS', 'P L PHARMA', 'S P DISTRIBUTORS', PVT. LTD., 'P. LTD' read as before",
          all(cn[x] == co[x] for x in cn if x != "GUNINA PHARMACEUTICALS P.L. LTD."), {x: (cn[x], co[x]) for x in cn})
    ms, mo = N["C_sarvam"]["misses"], O["C_sarvam"]["misses"]
    check("September's Sarvam counter: supplier misreads %d -> %d; bill no., date and total unchanged" % (mo["supplier"], ms["supplier"]),
          ms["supplier"] == mo["supplier"] - 1 and all(ms[k] == mo[k] for k in ("billno", "date", "total")), [N["C_sarvam"], O["C_sarvam"]])
    print("-- D  18.4 on marg, an order that arrived by its scan")
    check("on marg it is on the way ONCE (in transit 10): %s" % N["D_way"]["marg"], N["D_way"]["marg"] == 10, N["D_way"])
    check("on count as part 3 made it (10): %s" % N["D_way"]["count"], N["D_way"]["count"] == 10 == O["D_way"]["count"], [N["D_way"], O["D_way"]])
    check("NEGATIVE: the box as it is counts it twice on marg (in transit 10 + on order 10): %s" % O["D_way"]["marg"], O["D_way"]["marg"] == 20, O["D_way"])
    print("-- E  18.5 a credit note is a return (F-713)")
    check("10 sold and a credit note of 3: sales %s, returns %s, sale lines %s; expected stock 100 - 10 + 3 = %s" % (N["E"]["u"], N["E"]["ret"], N["E"]["n"], N["E"]["expected"]),
          N["E"]["u"] == 7 and N["E"]["ret"] == 3 and N["E"]["n"] == 1 and N["E"]["expected"] == 93, N["E"])
    check("NEGATIVE: the box as it is reads the credit note as a sale: sales %s, expected %s" % (O["E"]["u"], O["E"]["expected"]),
          O["E"]["u"] == 13 and O["E"]["expected"] == 87, O["E"])
    print("-- F  18.6 the owner's agreement card")
    fs, ft = N["F_stored"], N["F_taken"]
    check("the stored sheet keeps its figure and says 'on Marg's stock': '%s %s'" % (fs[1], fs[2]), fs[0] == 200 and fs[2] == "on Marg's stock"
          and fs[1] == O["F_stored"][1], [fs, O["F_stored"]])
    check("a comparison taken on count is stored with its basis and reads 'on the shelf figure'; on marg 'on Marg's stock'",
          ft.get("count", {}).get("stored") == "count" and ft["count"]["card"][2] == "on the shelf figure" and ft.get("marg", {}).get("stored") == "marg"
          and ft["marg"]["card"][2] == "on Marg's stock", ft)
    check("NEGATIVE: the box as it is says nothing of the basis", O["F_stored"][2] is None and all(v["card"][2] is None and v["stored"] is None for v in O["F_taken"].values()),
          [O["F_stored"], O["F_taken"]])
    print("-- S  the staff-eye walk (DUTY_MAP v5)")
    bad = []
    for who, v in N["S"].items():
        for d in v["duties"]:
            if d.get("tile") and d.get("tile_seen") is False:
                bad.append("%s tile %s" % (who, d["tile"]))
            if isinstance(d.get("due_n"), str):
                bad.append("%s %s: %s" % (who, d["id"], d["due_n"]))
            if d.get("door_seen") is False:
                bad.append("%s %s due but its marker is not on the door" % (who, d["id"]))
    check("every login's tiles on its home; every due duty's marker on its door", not bad, bad)
    print("WALK_S454P3B %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:900]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
