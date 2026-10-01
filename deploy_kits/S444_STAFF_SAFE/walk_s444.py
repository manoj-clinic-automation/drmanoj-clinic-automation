#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s444.py -- kit S444_STAFF_SAFE. THE REAL portal, THE REAL finance app and THE REAL asset app in ONE process per side, over
SCRATCH COPIES of finance.db and assets.db (backup API), driven through Flask's test clients. The NEW side carries the kit's nine
files; the OLD side is the box as it is (the negative control). Sign-in runs on the walk's OWN user store and the walk's OWN random
signing secret, written into each side's scratch portal folder (the live secret and the live password store are never copied).
Its own rows are keyed W444 (bills 'W444A..E' of 'KEDWALK444 PHARMA', exports 'w444...', scans stamped 'W444-nn', claims 'W444F/G',
a salt task 'W444 WALK ITEM', a refused file 'w444refused'), found by key, never by counting; every date is computed from today.
Real rows are read by key only: KEDAR 195 (27-Sep) and the count's vouchers.

  --fin-new DIR --fin-old DIR --por-new DIR --por-old DIR --ast DIR --shared DIR --db PATH --adb PATH --kit DIR --duty-map PATH
"""
import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys

TODAY = dt.date.today()
NOW = dt.datetime.now().replace(microsecond=0)


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


def T(minutes):
    return (NOW + dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%S")


SUP = "KEDWALK444 PHARMA"
KEDAR = ("KEDAR PHARMACEUTICAL", "195", "2026-09-27")
# name -> (bill no, rupees in Marg, scan total (None = no scan), paper amount S440 keeps (None = none))
BILLS = {"A": ("W444A", 1000.00, 1000.00, None),      # Marg = scan: mil gaya
         "B": ("W444B", 2000.00, 2100.00, None),      # the scan reads Rs 100 more: farq
         "C": ("W444C", 3000.00, None, None),         # no scan: scan nahi hua
         "D": ("W444D", 4000.00, 3900.00, 4100.00),   # the paper (S440) reads 4100: farq by the paper; his own slip -> clears at 4100
         "E": ("W444E", 5000.00, None, None)}         # no scan; his own slip -> clears when Marg's amount changes
USERS = {"amir": "staff", "shavez": "manager", "alisha": "staff", "shivani": "staff", "reception": "staff", "manoj": "doctor", "w444none": "staff"}


def md5id(s):
    return "w444" + hashlib.md5(s.encode()).hexdigest()[:28]


def ins(con, table, row, replace=False):
    """INSERT the walk's own row; a NOT NULL column with no default that the row does not name gets '' (text) or 0."""
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    cur = con.execute("INSERT %sINTO %s (%s) VALUES (%s)" % ("OR REPLACE " if replace else "", table, ", ".join(cols), ", ".join("?" * len(cols))),
                      [row[c] for c in cols])
    return cur.lastrowid


# ======================================================================= the PROBE (one process per side)
def probe():
    MODE = os.environ["MODE"]
    NEW = MODE == "new"
    FIN, POR, AST = os.environ["FINDIR"], os.environ["PORDIR"], os.environ["ASTDIR"]
    W = json.loads(os.environ["W444"])
    for p in (AST, POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import portal as po                                                # noqa: E402
    import asset_register as ar                                        # noqa: E402
    import amir_day                                                    # noqa: E402
    import stock_app                                                   # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}             # noqa: E731
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    db.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]   # noqa: E731
    out = {}

    def FG(u, path, **kw):
        r = fc.get(path, base_url=BASE, headers=H(u), **kw)
        return r.status_code, r.get_data(as_text=True), r.headers.get("Location", "")

    def text(h):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).replace("&#8377;", "Rs ").replace("&middot;", "·").replace("&mdash;", "--").strip()

    def needs():
        r = fc.get("/finance/sanjeevni/api/needs-you", base_url=BASE, headers=H("manoj"))
        j = r.get_json(silent=True) or {}
        return [l.get("text", "") for l in j.get("lines") or []]

    # ------------------------------------------------------------------ 1. sign-in: one name, whatever is typed
    def login(typed, pw):
        r = pc.post("/portal/login", base_url=BASE, data={"user": typed, "password": pw})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        u = None
        if tok:
            b = tok.split(".")[0]
            u = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)).decode())["u"]
        return r.status_code, tok, u

    def portal_get(tok, path="/portal", home_cookie=None):
        ck = "clinic_sso=" + tok + (("; clinic_portal_home=" + home_cookie) if home_cookie else "")
        r = pc.get(path, base_url=BASE, headers={"Cookie": ck})
        sc = " ".join(r.headers.getlist("Set-Cookie"))
        m = re.search(r"clinic_portal_home=([^;]+)", sc)
        return r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True), (m.group(1) if m else None)

    def tiles(h):
        import html as _h                                              # noqa: PLC0415
        return [_h.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', h or "")]

    pw = W["pw"]
    sign = {}
    for typed in ("Amir", "AMIR", " amir ", "amir"):
        sc, tok, u = login(typed, pw["amir"])
        s1, loc1, h1, hc = portal_get(tok)
        s2, loc2, h2, _ = portal_get(tok, home_cookie=hc) if hc else (None, None, None, None)
        s3, _l3, h3, _ = portal_get(tok, "/portal?all=1")
        sign[typed] = dict(login=sc, u=u, first=[s1, loc1], again=[s2, loc2, "Amir ka kaam" in (h2 or "")],
                           all=[s3, "Amir ka kaam" in h3, ("amir (staff)" in h3), ("Amir (staff)" in h3)])
    out["sign"] = sign
    # an old token minted as "Amir" (before S444 the token kept the case as typed), signed with the walk's secret
    sec = os.environ["CLINIC_SSO_SECRET"]
    now = int(dt.datetime.now().timestamp())
    body = base64.urlsafe_b64encode(json.dumps({"u": "Amir", "r": "staff", "e": W["epoch"], "iat": now - 3600, "exp": now + 86400},
                                               separators=(",", ":"), sort_keys=True).encode()).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(hmac.new(sec.encode(), body.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    old = body + "." + sig
    s1, loc1, h1, _ = portal_get(old)
    s3, _l, h3, _ = portal_get(old, "/portal?all=1")
    r = fc.get("/finance/api/whoami", base_url=BASE, headers={"Cookie": "clinic_sso=" + old})
    who_fin = (r.get_json(silent=True) or {}).get("user")
    r = fc.get("/finance/amir", base_url=BASE, headers={"Cookie": "clinic_sso=" + old})
    fin_amir = [r.status_code, r.headers.get("Location", "")]
    with ar.app.test_request_context("/intake", base_url=BASE, headers={"Cookie": "clinic_sso=" + old}):
        au = ar._sso_user()
        who_ast = (au or {}).get("username") if au else None
    ra = ar.app.test_client(use_cookies=False).get("/intake", base_url=BASE, headers={"Cookie": "clinic_sso=" + old})
    out["oldtoken"] = dict(portal=[s1, loc1, "Amir ka kaam" in h1, "Amir (staff)" in h1, "amir (staff)" in h1],
                           portal_all=[s3, "Amir ka kaam" in h3], finance_who=who_fin, finance_amir=fin_amir,
                           asset_who=who_ast, asset_intake=ra.status_code)
    # a fresh sign-in as "Amir": the finance app and the asset app read the same name
    _sc, tok, _u = login("Amir", pw["amir"])
    r = fc.get("/finance/api/whoami", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
    out["fresh_finance_who"] = (r.get_json(silent=True) or {}).get("user")
    r = fc.get("/finance/amir", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
    out["fresh_finance_amir"] = [r.status_code, r.headers.get("Location", "")]
    ra = ar.app.test_client(use_cookies=False).get("/intake", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
    out["fresh_asset_intake"] = ra.status_code
    # a login with no work set
    _sc, tok, _u = login("w444none", pw["w444none"])
    s, loc, h, _ = portal_get(tok)
    out["nowork"] = dict(status=s, hindi=("Is naam par koi kaam set nahi hai" in h), signout=("/portal/logout" in h and "Sign out</a>" in h),
                         tiles=tiles(h))
    # ------------------------------------------------------------------ 2. the staff-eye walk: each login's home, as that login
    dm = json.load(open(os.environ["REAL_DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True)
    eye = {}
    for who in ("amir", "shavez", "alisha", "shivani", "reception"):
        _sc, tok, _u = login(who, pw[who])
        s1, loc1, h1, _ = portal_get(tok)
        s3, _l, h3, _ = portal_get(tok, "/portal?all=1")
        seen = tiles(h3)
        rows = []
        mine = {who, (dm.get("shared") or {}).get(who)}                 # a login that works another's queue (shivani -> alisha's)
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
                path = str(door)
                body = ""
                for _hop in range(4):
                    r = fc.get(path, base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
                    if r.status_code in (301, 302, 303) and r.headers.get("Location", "").startswith(("/finance/", BASE + "/finance/")):
                        path = r.headers["Location"].replace(BASE, "")
                        continue
                    body = r.get_data(as_text=True)
                    break
                row["door_seen"] = mark in body
            rows.append(row)
        eye[who] = dict(first=[s1, loc1], tiles=seen, duties=rows)
    ro.close()
    out["eye"] = eye
    # ------------------------------------------------------------------ 3. Amir's door: the vouchers, on every step
    steps = {}
    for n in range(1, 8):
        s, h, _l = FG("amir", "/finance/amir/step/%d" % n)
        m = re.search(r"Stock voucher baaki: (\d+) orthotic, (\d+) dawa", h)
        steps[n] = dict(status=s, card=[int(m.group(1)), int(m.group(2))] if m else None, signed=("Signed in: amir" in h),
                        sab=("/portal?all=1" in h), naam=("Naam badlo:" in h), salt=("Ek export aur: SALT WISE ITEM LIST" in h),
                        title6=("Marg sudhar" in h) if n == 6 else None)
    out["steps"] = steps
    # ------------------------------------------------------------------ 4. the bill line (step 5)
    s, h5, _l = FG("amir", "/finance/amir/step/5")
    blocks = {}
    for blk in h5.split("<div class=bill>")[1:]:
        m = re.search(r"name='k_(\d+)' value='([^']*)'", blk)
        if not m:
            continue
        key = m.group(2).replace("&amp;", "&")
        amt = re.search(r"id='s444amt'>(.*?)</div>", blk, re.S)
        blocks[key] = dict(i=int(m.group(1)), amt=text(amt.group(1)) if amt else None, waiting=("Marg ki agli export ka intezaar" in blk),
                           self_radio=("value='self'" in blk))
    keyof = lambda b: "%s|%s|%s" % (SUP, BILLS[b][0], W["bill_date"])  # noqa: E731
    out["bill"] = {b: blocks.get(keyof(b)) for b in BILLS}
    kk = "%s|%s|%s" % KEDAR
    out["kedar_block"] = blocks.get(kk)
    # ------------------------------------------------------------------ 5. "Meri entry galat thi": no claim, waits, clears itself
    form = {"n": str(max([v["i"] for v in blocks.values()] + [0]) + 1)}
    for b in ("D", "E"):
        v = blocks.get(keyof(b))
        if v:
            form["k_%d" % v["i"]] = keyof(b)
            form["r_%d" % v["i"]] = "self"
    r = fc.post("/finance/amir/step/5", base_url=BASE, headers=H("amir"), data=form)
    disp = lambda b: (q("SELECT reason, by_user FROM amir_bill_disposition WHERE supplier_norm=? AND bill_no=? AND bill_date=?", SUP, BILLS[b][0], W["bill_date"]) or [None])[0]  # noqa: E731
    claims = lambda b: q("SELECT id, state, settled_outcome FROM amir_claim WHERE supplier_norm=? AND bill_no=?", SUP, BILLS[b][0])  # noqa: E731
    audits = lambda b: [r["who"] for r in q("SELECT who FROM purchase_audit WHERE action='amir_self_cleared' AND ref=?", keyof(b))]  # noqa: E731
    out["self_post"] = r.status_code
    out["self_after"] = {b: dict(disp=disp(b), claims=claims(b)) for b in ("D", "E")}

    def add_export(tag, minutes, amounts):
        md5 = md5id(tag)
        ins(db, "purchase_export", dict(md5=md5, type="BILLWISE", file="W444_" + tag, period_from=D(20), period_to=TODAY.isoformat(),
                                        export_stamp=(NOW + dt.timedelta(minutes=minutes)).strftime("%Y%m%d-%H%M%S"), received_at=T(minutes),
                                        n_rows=len(amounts), grand_amount_p=0), replace=True)
        for (sup, bno, bdate), rs in amounts:
            # as the ingest does (purchase_app, one row per bill): a later export carrying the bill moves its amount and its bw_md5
            p = int(round(rs * 100))
            db.execute("UPDATE purchase_bill SET cash_p=0, credit_p=?, amount_p=?, source_md5=?, bw_md5=?, bw_amount_p=? "
                       "WHERE supplier_norm=? AND bill_no=? AND bill_date=?", (p, p, md5, md5, p, sup, bno, bdate))
        db.commit()

    dk = lambda b: (SUP, BILLS[b][0], W["bill_date"])                    # noqa: E731
    add_export("e1", 1, [(dk("D"), 4000.00), (dk("E"), 5000.00)])
    FG("amir", "/finance/amir/step/5")
    out["after_e1"] = {b: disp(b) for b in ("D", "E")}
    add_export("e2", 2, [(dk("D"), 4000.00), (dk("E"), 5000.00)])
    FG("amir", "/finance/amir/step/5")
    out["after_e2"] = {b: disp(b) for b in ("D", "E")}
    out["needs_after_e2"] = needs()
    add_export("e3", 3, [(dk("D"), 4100.00), (dk("E"), 5200.00)])
    FG("amir", "/finance/amir/step/5")
    FG("amir", "/finance/amir/step/5")
    out["after_e3"] = {b: dict(disp=disp(b), audits=audits(b)) for b in ("D", "E")}
    out["needs_after_e3"] = needs()
    # ------------------------------------------------------------------ 6. KEDAR 195: the owner's ruling (applied on the new side before this probe)
    out["kedar"] = dict(disp=(q("SELECT reason, by_user FROM amir_bill_disposition WHERE supplier_norm=? AND bill_no=? AND bill_date=?", *KEDAR) or [None])[0],
                        claims=q("SELECT id, state, settled_outcome, settled_by FROM amir_claim WHERE supplier_norm=? AND bill_no=? AND bill_date=?", *KEDAR))
    add_export("kedar", 4, [(KEDAR, 17959.00)])
    FG("amir", "/finance/amir/step/5")
    out["kedar_after"] = dict(disp=(q("SELECT reason, by_user FROM amir_bill_disposition WHERE supplier_norm=? AND bill_no=? AND bill_date=?", *KEDAR) or [None])[0],
                              audits=[r["who"] for r in q("SELECT who FROM purchase_audit WHERE action='amir_self_cleared' AND ref=?", "%s|%s|%s" % KEDAR)])
    # ------------------------------------------------------------------ 7. the salt list
    def reports():
        s, h, _l = FG("shavez", "/finance/reports/aaj")
        m = re.search(r"Salt-wise item list</span>.*?</div>", h, re.S)
        row = m.group(0) if m else ""
        dm_ = re.search(r"(\d+) din se baaki", row)
        return dict(status=s, row=bool(row), days=int(dm_.group(1)) if dm_ else None, red=("state bad" in row), signed=("Signed in: shavez" in h))
    out["salt0"] = dict(s6=("Ek export aur" in FG("amir", "/finance/amir/step/6")[1]), s7=("Ek export aur" in FG("amir", "/finance/amir/step/7")[1]),
                        rep=reports())
    ins(db, "purchase_salt_task", dict(section="rename", seq=944401, a="W444 WALK ITEM", done=1, done_by="amir", done_at=T(-1)), replace=True)
    db.commit()
    h6, h7 = FG("amir", "/finance/amir/step/6")[1], FG("amir", "/finance/amir/step/7")[1]
    hs = FG("amir", "/finance/amir/salts")[1]
    lastv = db.execute("SELECT MAX(received_at) FROM mi_file WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED'").fetchone()[0]
    out["salt1"] = dict(s6=("Ek export aur: SALT WISE ITEM LIST" in h6), s7=("Ek export aur: SALT WISE ITEM LIST" in h7),
                        s7_shavez=("Aaj nahi aayi to Shavez kal subah nikalega" in h7), salts_page=("Ek export aur" in hs),
                        salts_signed=("Signed in: amir" in hs), rep=reports(), needs=needs(), last_verified=lastv)
    # close still allowed while the card stands: the day's own gate, with every gate step done
    if NEW:
        with fa.app.test_request_context("/finance/amir/step/7", base_url=BASE, headers=H("amir")):
            w = amir_day._work(db, amir_day._today())
            w["done"].update({2: True, 4: True, 5: True, 6: True, 7: False})
            hh = amir_day._step7(w)
            out["close_ok"] = dict(ready=amir_day._ready_to_close(w), button=("Din band kijiye" in hh), card=("Ek export aur" in hh),
                                   gate=list(amir_day.GATE_STEPS))
    db.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('amir.salt_owed_days', '0', 'W444 walk')")
    db.commit()
    out["salt_needs_0"] = needs()
    ins(db, "mi_file", dict(md5=md5id("saltlist"), type="SALT_WISE_ITEM_LIST", verdict="VERIFIED", received_at=T(1) + "+05:30",
                            stamp=(NOW + dt.timedelta(minutes=1)).strftime("%Y%m%d-%H%M%S")), replace=True)
    db.commit()
    out["salt2"] = dict(s6=("Ek export aur" in FG("amir", "/finance/amir/step/6")[1]), needs=needs(), rep=reports())
    db.execute("DELETE FROM setting WHERE key='amir.salt_owed_days' AND note='W444 walk'")
    db.commit()
    # ------------------------------------------------------------------ 8. claims open too long; a report refused today; the duty map
    out["needs_claims"] = needs()
    db.execute("UPDATE amir_claim SET state='settled', settled_outcome='w444', settled_by='W444 walk' WHERE bill_no='W444F'")
    db.commit()
    out["needs_claims_after"] = needs()
    # ------------------------------------------------------------------ 9. the count vouchers: (d) after 2 of his visits; entering one lowers the card
    duties = stock_app.amir_duties(db) if hasattr(stock_app, "amir_duties") else None
    out["duties0"] = duties
    since = None
    if duties:
        c = [x for x in duties["counts"] if x["open"]]
        if c:
            since = max([x for x in (c[0].get("made_first"), c[0].get("last_touch")) if x]).replace("T", " ")
    vis = q("SELECT day FROM amir_day WHERE opened_at > ?", since or "9999")
    added = []
    d0 = dt.date.fromisoformat((since or TODAY.isoformat())[:10])
    k = 1
    while len(vis) + len(added) < 2 and k < 30:
        day = (d0 + dt.timedelta(days=k)).isoformat()
        if day < TODAY.isoformat() and not q("SELECT 1 FROM amir_day WHERE day=?", day):
            ins(db, "amir_day", dict(day=day, opened_at=day + " 08:00:00", closed_at=day + " 09:00:00", closed_by="W444 walk"))
            added.append(day)
        k += 1
    db.commit()
    out["visits"] = dict(real=len(vis), crafted=added)
    out["needs_visits"] = needs()
    out["card_before"] = steps[1]["card"]
    bat = q("SELECT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=1 AND section='Orthotics' ORDER BY kind, round_no, batch_no LIMIT 1")
    if bat:
        r = fc.post("/finance/stock/api/pad/vouchers/1/entered", base_url=BASE, headers=H("amir"),
                    json={"round": bat[0]["round_no"], "kind": bat[0]["kind"], "batch": bat[0]["batch_no"], "marg_voucher_no": "W444-1"})
        out["entered_post"] = r.status_code
    h1 = FG("amir", "/finance/amir/step/1")[1]
    m = re.search(r"Stock voucher baaki: (\d+) orthotic, (\d+) dawa", h1)
    out["card_after"] = [int(m.group(1)), int(m.group(2))] if m else None
    out["needs_after_enter"] = needs()
    # the board: BACK to his page, who is signed in, his visit remembered (the owner's own look marked as the checker's)
    s, hb, _l = FG("amir", "/finance/stock/page/amir?count=1")
    FG("manoj", "/finance/stock/page/amir?count=1")
    try:
        opens = q("SELECT by_user, checker FROM stock_board_open ORDER BY id")
    except Exception:                                                  # noqa: BLE001
        opens = None
    out["board"] = dict(status=s, back=('id="s444back" href="/finance/amir"' in hb), signed=("Signed in: amir" in hb), opens=opens)
    # renames: only on a green proof
    if NEW:
        for r_ in q("SELECT DISTINCT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=1"):
            db.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (1,?,?,?,?,?,?,?)",
                       (r_["round_no"], r_["kind"], r_["batch_no"], "W444-ALL", TODAY.strftime("%d-%m-%Y"), "W444 walk", T(5)))
        db.commit()
        stock_app._S444_RENAMES_CACHE.clear()
        h6 = FG("amir", "/finance/amir/step/6")[1]
        out["renames_real"] = dict(voucher=("Stock voucher baaki" in h6), naam=("Naam badlo:" in h6))
        real_ps = stock_app._proof_state
        stock_app._proof_state = lambda con, d: {"state": "done"}       # walk only: the crafted green proof
        stock_app._S444_RENAMES_CACHE.clear()
        h6 = FG("amir", "/finance/amir/step/6")[1]
        h2 = FG("amir", "/finance/amir/step/2")[1]
        m = re.search(r"Naam badlo: (\d+) naam", h6)
        import item_alias                                              # noqa: E402
        out["renames_green"] = dict(n=int(m.group(1)) if m else None, top2=("Naam badlo:" in h2),
                                    expect=sum(1 for r in item_alias.rows(db) if r.get("state") in ("planned", "amber")))
        stock_app._proof_state = real_ps
        stock_app._S444_RENAMES_CACHE.clear()
    # ------------------------------------------------------------------ 10. signed in: Purchase orders' BACK bar, Shavez's reports
    s, hp, _l = FG("alisha", "/finance/porders")
    bar = re.search(r'<div id="s440bar">.*?</div>', hp, re.S)
    out["porders"] = dict(status=s, signed_in_bar=bool(bar and "Signed in: alisha" in bar.group(0)), bars=hp.count('id="s440bar"'), backs=hp.count("← BACK"))
    out["needs_final"] = needs()
    print("W444JSON " + json.dumps(out, default=str))


# ======================================================================= the WALK
def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--por-new", "--por-old", "--ast", "--shared", "--db", "--adb", "--kit", "--duty-map"):
        ap.add_argument(k, required=True)
    for k in ("--live-portal", "--live-db", "--live-adb"):
        ap.add_argument(k, default="")
    a = ap.parse_args()
    for p in (a.db, a.adb):
        assert "walk" in p or "scratch" in p or p.startswith("/tmp"), "refusing a non-scratch database: " + p
    n, fails = [0], []

    def check(label, cond, got=None):
        n[0] += 1
        print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if got is not None else ""))
        if not cond:
            fails.append(label)

    def copydb(src, dst):
        s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
        d = sqlite3.connect(dst)
        s.backup(d)
        d.close()
        s.close()

    # ---- the walk's own sign-in: a random secret and its own user store, in each side's scratch portal folder
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    for por in (a.por_new, a.por_old):
        assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
        with open(os.path.join(por, "portal_config.py"), "w") as fh:
            fh.write("# W444 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w444-walk-seed'\n" % secret)
        sys.path.insert(0, por)
        import clinic_users                                            # noqa: E402
        store = os.path.join(por, "clinic_users.json")
        if os.path.exists(store):
            os.remove(store)
        for u, role in USERS.items():
            try:
                clinic_users.add_role(store, "staff")
            except ValueError:
                pass
            clinic_users.add_user(store, u, role, pw[u])
        epoch = clinic_users.get_epoch(store)
        sys.path.remove(por)
        sys.modules.pop("clinic_users", None)
    # ---- the crafted rows, the same ids on both sides
    copydb(a.db, a.db + ".old")
    copydb(a.adb, a.adb + ".old")
    bill_date = D(2)

    def craft(fin, ast):
        F = sqlite3.connect(fin, timeout=30)
        A = sqlite3.connect(ast, timeout=30)
        md5 = md5id("bw0")
        ins(F, "purchase_export", dict(md5=md5, type="BILLWISE", file="W444_BW0", period_from=D(20), period_to=TODAY.isoformat(),
                                       export_stamp=(NOW - dt.timedelta(hours=2)).strftime("%Y%m%d-%H%M%S"), received_at=T(-120), n_rows=len(BILLS),
                                       grand_amount_p=0), replace=True)
        ids = {}
        for k, (bno, rs, scan, paper) in sorted(BILLS.items()):
            sid = None
            if scan is not None:
                sid = ins(A, "bills", dict(kind="Pharmacy", vendor=SUP, bill_no=bno, bill_date=bill_date, total_amount=scan, notes="W444 walk",
                                           created_at=NOW.strftime("%Y-%m-%d %H:%M:%S"), stamp_no="W444-%02d" % (len(ids) + 1), status="captured",
                                           ocr_status="read", lane="pharmacy", source_stored="w444.pdf", source_orig="w444"))
            p = int(round(rs * 100))
            ins(F, "purchase_bill", dict(supplier_norm=SUP, supplier=SUP, bill_no=bno, bill_date=bill_date, month=bill_date[:7], cash_p=0, credit_p=p,
                                         amount_p=p, source_md5=md5, bw_md5=md5, bw_amount_p=p, date_src="BILLWISE", scan_bill_id=sid))
            if paper is not None:
                ins(F, "purchase_scan_state", dict(asset_bill_id=sid, why="linked", detail="W444 walk", checked_at=T(-60), paper_amount=int(round(paper * 100))),
                    replace=True)
            ids[k] = sid
        for bno, ago in (("W444F", 8), ("W444G", 3)):
            ins(F, "amir_claim", dict(supplier=SUP, supplier_norm=SUP, bill_no=bno, bill_date=D(ago + 2), amount_p=1234500, reason="short",
                                      raised_by="amir", raised_at=D(ago) + " 10:00:00", state="open"))
        ins(F, "mi_file", dict(md5=md5id("refused"), type="SALE_BILLWISE", verdict="REFUSED", reason="W444 walk: text export refused at line 52 (***)",
                               pc_verdict="", received_at=T(-5) + "+05:30"), replace=True)
        F.commit()
        A.commit()
        F.close()
        A.close()
        return ids

    ids = craft(a.db, a.adb)
    assert ids == craft(a.db + ".old", a.adb + ".old"), "the crafted rows must carry the same ids on both sides"
    print("-- crafted on both sides: 5 bills of %s dated %s (export %s), %d scans (W444-nn), claims W444F (8 days) / W444G (3 days), a refused file"
          % (SUP, bill_date, md5id("bw0")[:10], sum(1 for v in ids.values() if v)))
    # ---- the crafted duty map: one orphan duty (no code raises it), one already coded
    cmap = os.path.join(os.path.dirname(os.path.abspath(a.db)), "w444_duty_map.json")
    with open(cmap, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "people": {"darpan": "Darpan"}, "duties": [
            {"id": "w444.orphan", "person": "darpan", "duty": "W444 crafted orphan", "tile": None, "door": None,
             "due_sql": "SELECT COUNT(*) AS n, MIN(raised_at) AS since FROM amir_claim WHERE bill_no LIKE 'W444%' AND state <> 'settled'",
             "allowed_days": 1, "owner_line": "W444 orphan duty: {n} due since {since} ({person}, {days} days)", "coded": None},
            {"id": "w444.coded", "person": "darpan", "duty": "W444 coded", "tile": None, "door": None,
             "due_sql": "SELECT COUNT(*) AS n, NULL AS since FROM amir_claim", "allowed_days": 0, "owner_line": "W444 SHOULD NOT SHOW", "coded": "amir_day (c)"}]}, fh)
    # ---- the new side: the owner's ruling on KEDAR 195 and the settings, by the kit's own data step, on the scratch copy
    ap_out = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "apply_s444.py"), "--finance", a.fin_new, "--db", a.db],
                            env=dict(os.environ, FINANCE_DB=a.db, DUTY_MAP_JSON=cmap, ASSETS_DB=a.adb), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print("-- the data step on the scratch copy (new side):")
    for line in ap_out.stdout.splitlines()[-14:]:
        print("   " + line)
    check("the data step ran on the scratch copy (settings seeded, KEDAR 195 ruled)", ap_out.returncode == 0 and "S444 apply done" in ap_out.stdout, ap_out.returncode)

    def run(side):
        fin, por = (a.fin_new, a.por_new) if side == "new" else (a.fin_old, a.por_old)
        dbp, adbp = (a.db, a.adb) if side == "new" else (a.db + ".old", a.adb + ".old")
        env = dict(os.environ, MODE=side, FINDIR=fin, PORDIR=por, ASTDIR=a.ast, FINANCE_DB=dbp, ASSETS_DB=adbp, FINANCE_ALLOW_HEADER_AUTH="1",
                   FINANCE_SSO_DIR=por, CLINIC_PORTAL_DIR=por, CLINIC_USERS_FILE=os.path.join(por, "clinic_users.json"),
                   TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, DUTY_MAP_JSON=cmap, REAL_DUTY_MAP=a.duty_map,
                   SHARED_LIB_DIR=a.shared, ASSETS_UPLOADS=os.path.join(os.path.dirname(adbp), "w444_uploads"),
                   W444=json.dumps({"pw": pw, "epoch": epoch, "bill_date": bill_date, "ids": ids}))
        env.pop("SARVAM_API_KEY", None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1500)
        js = [l for l in p.stdout.splitlines() if l.startswith("W444JSON ")]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (side, p.returncode))
            for l in p.stdout.splitlines()[-25:]:
                print("   " + l[:300])
            return None
        return json.loads(js[-1][9:])

    # ---- the pre-install name check: green on the live stores, STOP on a crafted capital name (a third scratch copy)
    print("-- 0  the name check that runs before the switch")
    names = os.path.join(a.kit, "names_s444.py")
    if a.live_portal:
        p = subprocess.run([sys.executable, "-B", names, "--portal", a.live_portal, "--finance-db", a.live_db, "--assets-db", a.live_adb],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        check("on the LIVE stores (read-only): every name already small letters -> green", p.returncode == 0 and "GREEN" in p.stdout, p.stdout.strip().splitlines()[-2:])
    cap = a.db + ".caps"
    copydb(a.db, cap)
    c = sqlite3.connect(cap)
    ins(c, "unit_role", dict(unit="medical", username="W444Amir", role="viewer", active=1))
    c.commit()
    c.close()
    p = subprocess.run([sys.executable, "-B", names, "--portal", a.por_new, "--finance-db", cap, "--assets-db", a.adb],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    check("a crafted capital name (unit_role 'W444Amir') -> STOP, named, exit 3", p.returncode == 3 and "W444Amir" in p.stdout, p.stdout.strip().splitlines()[-1:])
    os.remove(cap)
    N = run("new")
    O = run("old")
    check("both probes ran to the end (new / old)", N is not None and O is not None)
    if N is None or O is None:
        print("WALK_S444 RED -- a probe did not finish")
        return 1
    # ================================================================= 1. sign-in
    print("-- 1  one sign-in name, whatever is typed (the portal, the finance app, the asset app)")
    for typed in ("Amir", "AMIR", " amir "):
        s = N["sign"][typed]
        check("typed %r: the session is named 'amir'; the first /portal goes to /finance/amir (302); the next shows his tiles; ?all=1 shows 'Amir ka kaam' and 'amir (staff)'" % typed,
              s["u"] == "amir" and s["first"][0] == 302 and s["first"][1].endswith("/finance/amir") and s["again"][0] == 200 and s["again"][2]
              and s["all"][0] == 200 and s["all"][1] and s["all"][2], s)
    s = N["sign"]["amir"]
    check("typed 'amir' (the phone): the same", s["u"] == "amir" and s["first"][0] == 302 and s["all"][1], s)
    o = N["oldtoken"]
    check("a token minted before S444 as 'Amir' now reads as amir in all three apps: the portal sends it to /finance/amir and shows 'amir (staff)', finance says 'amir', the asset app 'amir'",
          o["portal"][0] == 302 and o["portal"][1].endswith("/finance/amir") and o["portal_all"][1] and o["finance_who"] == "amir" and o["asset_who"] == "amir", o)
    check("/finance/amir and the asset intake admit him (303 into his day · 200)", o["finance_amir"][0] == 303 and "/finance/amir/step/" in o["finance_amir"][1] and o["asset_intake"] == 200
          and N["fresh_finance_amir"][0] == 303 and N["fresh_asset_intake"] == 200 and N["fresh_finance_who"] == "amir", [o["finance_amir"], o["asset_intake"], N["fresh_finance_amir"], N["fresh_finance_who"]])
    nw = N["nowork"]
    check("a login with no work set sees the Hindi line and a big Sign out; only its own 'Meri attendance' stays (no Scan Purchase, no Forms)",
          nw["status"] == 200 and nw["hindi"] and nw["signout"] and nw["tiles"] == ["Meri attendance"], nw)
    # ================================================================= 2. the staff-eye walk
    print("-- 2  the staff-eye walk: each login's home, as that login, carries each of its pending duties (DUTY_MAP.json)")
    for who in ("amir", "shavez", "alisha", "shivani", "reception"):
        e = N["eye"][who]
        missing = [d["id"] for d in e["duties"] if d["tile"] and not d["tile_seen"]]
        unseen = [d["id"] for d in e["duties"] if d.get("door_seen") is False]
        errs = [d["id"] for d in e["duties"] if isinstance(d.get("due_n"), str)]
        due = [(d["id"], d["due_n"]) for d in e["duties"] if isinstance(d.get("due_n"), int) and d["due_n"] > 0]
        extra = (e["first"][0] == 302 and e["first"][1].endswith("/finance/amir")) if who == "amir" else (e["first"][0] == 200)
        check("%s: %d duties on the map; every tile on the home; every due duty's door shows it (%s); first /portal %s"
              % (who, len(e["duties"]), ", ".join("%s %s" % x for x in due) or "none due now", "-> /finance/amir" if who == "amir" else "200"),
              e["duties"] and not missing and not unseen and not errs and extra, dict(missing=missing, unseen=unseen, errors=errs, first=e["first"]))
    # ================================================================= 3. Amir's door
    print("-- 3  Amir's one door: the count's vouchers on every step, orthotic first; renames only on a green proof; the board's BACK")
    exp = N["duties0"]["counts"][0] if N.get("duties0") and N["duties0"]["counts"] else None
    check("the vouchers read from the box: count #1, %s" % (("%d open (%d orthotic, %d dawa)" % (exp["open"], exp["ortho"], exp["dawa"])) if exp else "none"),
          bool(exp) and exp["count_id"] == 1 and exp["open"] == exp["ortho"] + exp["dawa"] and exp["ortho"] > 0, exp)
    card = [exp["ortho"], exp["dawa"]] if exp else None
    check("every step 1-7 of his day carries 'Stock voucher baaki: %s orthotic, %s dawa' and 'Signed in: amir' and the 'Sab tiles' link" % tuple(card or ["?", "?"]),
          all(N["steps"][str(k)]["card"] == card and N["steps"][str(k)]["signed"] and N["steps"][str(k)]["sab"] for k in range(1, 8)),
          {k: N["steps"][str(k)]["card"] for k in range(1, 8)})
    check("step 6 is 'Marg sudhar'; no rename shows while the vouchers are open (the proof is not green)",
          N["steps"]["6"]["title6"] and not any(N["steps"][str(k)]["naam"] for k in range(1, 8)), N["steps"]["6"])
    check("marking one voucher entered on his board lowers the card (orthotic %s -> %s)" % (card[0] if card else "?", card[0] - 1 if card else "?"),
          N.get("entered_post") == 200 and card and N["card_after"] == [card[0] - 1, card[1]], [N.get("entered_post"), N["card_after"]])
    check("his board: BACK goes to /finance/amir, 'Signed in: amir', and his visit is remembered (the owner's own look marked as the checker's)",
          N["board"]["status"] == 200 and N["board"]["back"] and N["board"]["signed"] and N["board"]["opens"] == [{"by_user": "amir", "checker": 0}, {"by_user": "manoj", "checker": 1}],
          N["board"])
    check("renames: with every voucher entered but the REAL proof (not green) -- no rename line and no voucher line",
          N["renames_real"] == {"voucher": False, "naam": False}, N["renames_real"])
    check("renames: on a crafted green proof (walk only) -- 'Naam badlo: %s naam' on step 6 and at the top of step 2" % N["renames_green"]["expect"],
          N["renames_green"]["n"] == N["renames_green"]["expect"] and N["renames_green"]["n"] > 0 and N["renames_green"]["top2"], N["renames_green"])
    nv = [t for t in N["needs_visits"] if t.startswith("Count vouchers waiting")]
    check("the owner's line (d) after 2 of his visits without the board: 'Count vouchers waiting: N (orthotic M) -- Amir has not opened them in 2 visits'",
          len(nv) == 1 and ("(orthotic %d)" % card[0]) in nv[0] and "in %d visits" % (N["visits"]["real"] + len(N["visits"]["crafted"])) in nv[0], [nv, N["visits"]])
    check("... and it is gone the moment one voucher is entered", not [t for t in N["needs_after_enter"] if t.startswith("Count vouchers waiting")], N["needs_after_enter"][:6])
    # ================================================================= 4. the bill line
    print("-- 4  the bill line: Marg's amount beside the paper's (S439/S440 link), three states")
    B = N["bill"]
    check("W444A: 'Marg: Rs 1,000 · Kaagaz (scan): Rs 1,000 · mil gaya'", B["A"] and "Marg: Rs 1,000 · Kaagaz (scan): Rs 1,000 · mil gaya" in (B["A"]["amt"] or ""), B["A"])
    check("W444B: 'Marg: Rs 2,000 · Kaagaz (scan): Rs 2,100 · farq Rs 100'", B["B"] and "Marg: Rs 2,000 · Kaagaz (scan): Rs 2,100 · farq Rs 100" in (B["B"]["amt"] or ""), B["B"])
    check("W444C: 'Marg: Rs 3,000 · Kaagaz (scan): -- · scan nahi hua'", B["C"] and "scan nahi hua" in (B["C"]["amt"] or "") and "Marg: Rs 3,000" in (B["C"]["amt"] or ""), B["C"])
    check("W444D: the paper amount S440 keeps wins over the scan's reading: 'Kaagaz (paper): Rs 4,100 · farq Rs 100'",
          B["D"] and "Marg: Rs 4,000 · Kaagaz (paper): Rs 4,100 · farq Rs 100" in (B["D"]["amt"] or ""), B["D"])
    check("the seventh answer 'Meri entry galat thi' is on every bill", all(B[k] and B[k]["self_radio"] for k in BILLS), {k: (B[k] or {}).get("self_radio") for k in BILLS})
    # ================================================================= 5. self
    print("-- 5  'Meri entry galat thi -- Marg mein theek kar di': no claim, waits, clears itself (audited once)")
    sa = N["self_after"]
    check("answered 'self' on W444D and W444E: the answer is kept, NO claim is raised", N["self_post"] == 303 and all(sa[b]["disp"] and sa[b]["disp"]["reason"] == "self" and not sa[b]["claims"] for b in "DE"), sa)
    check("a later export at the OLD amount: both still wait ('self')", all((N["after_e1"][b] or {}).get("reason") == "self" for b in "DE") and all((N["after_e2"][b] or {}).get("reason") == "self" for b in "DE"), [N["after_e1"], N["after_e2"]])
    nb = [t for t in N["needs_after_e2"] if t.startswith("Amir's own correction on %s" % SUP)]
    check("after 2 such exports the owner's line (b): 'Amir's own correction on <supplier> bill W444D/E not yet seen in Marg after 2 exports'", len(nb) == 2 and all("after 2 exports" in t for t in nb), nb)
    ae = N["after_e3"]
    check("an export at the paper's amount clears W444D by itself, audited ONCE as 'S444 auto: Marg = kaagaz'",
          ae["D"]["disp"]["reason"] == "ok" and ae["D"]["disp"]["by_user"] == "S444 auto: Marg = kaagaz" and ae["D"]["audits"] == ["S444 auto: Marg = kaagaz"], ae["D"])
    check("no scan: an export with a CHANGED amount clears W444E (audited once)", ae["E"]["disp"]["reason"] == "ok" and len(ae["E"]["audits"]) == 1, ae["E"])
    check("... and line (b) is gone", not [t for t in N["needs_after_e3"] if t.startswith("Amir's own correction on %s" % SUP)], N["needs_after_e3"][:6])
    print("-- 6  KEDAR 195 (27-Sep), the owner's ruling of 01-Oct")
    K = N["kedar"]
    check("claim #1 settled by the rule ('amir_own_entry', by 'S444 rule'); the answer is 'self'",
          K["disp"] and K["disp"]["reason"] == "self" and K["claims"] and all(c["state"] == "settled" and c["settled_outcome"] == "amir_own_entry" and c["settled_by"] == "S444 rule" for c in K["claims"]), K)
    kb = N["kedar_block"] or {}
    check("its bill waits on step 5: 'Marg: Rs 17,716 · Kaagaz (scan): Rs 17,959 · farq Rs 243' and 'Marg ki agli export ka intezaar'",
          "Marg: Rs 17,716 · Kaagaz (scan): Rs 17,959 · farq Rs 243" in (kb.get("amt") or "") and kb.get("waiting"), kb)
    KA = N["kedar_after"]
    check("an export showing Rs 17,959 clears it by itself, audited once", KA["disp"]["reason"] == "ok" and KA["audits"] == ["S444 auto: Marg = kaagaz"], KA)
    # ================================================================= 7. salt
    print("-- 7  the salt list cannot be silently forgotten")
    check("with the last verified list newer than every tick (the box today): no card on steps 6 and 7", not N["salt0"]["s6"] and not N["salt0"]["s7"], N["salt0"])
    s1 = N["salt1"]
    check("a salt tick newer than the last verified list: the red card on step 6, on step 7 (with 'Aaj nahi aayi to Shavez kal subah nikalega') and on the salts page",
          s1["s6"] and s1["s7"] and s1["s7_shavez"] and s1["salts_page"] and s1["salts_signed"], s1)
    exp_days = (TODAY - dt.date.fromisoformat(s1["last_verified"][:10])).days if s1.get("last_verified") else None
    check("Shavez's 'Aaj ki reports' row: '%s din se baaki', red, and 'Signed in: shavez'" % exp_days,
          s1["rep"]["row"] and s1["rep"]["days"] == exp_days and s1["rep"]["red"] and s1["rep"]["signed"], s1["rep"])
    co = N.get("close_ok") or {}
    check("Din band is still allowed with the card standing (GATE_STEPS 2,4,5,6 unchanged)", co.get("ready") and co.get("button") and co.get("card") and co.get("gate") == [2, 4, 5, 6], co)
    check("the owner's line (a) waits for its threshold (2 days): absent for a fresh tick", not [t for t in s1["needs"] if t.startswith("Salt list not received")], s1["needs"][:6])
    na = [t for t in N["salt_needs_0"] if t.startswith("Salt list not received")]
    check("at a threshold of 0 days: 'Salt list not received for N days -- M salt corrections unproven (Amir / Shavez ...'", len(na) == 1 and "(Amir / Shavez" in na[0], na)
    check("a verified list arriving after the tick: the card and the line are gone, the row is not owed", not N["salt2"]["s6"] and not [t for t in N["salt2"]["needs"] if t.startswith("Salt list")] and N["salt2"]["rep"]["days"] is None, N["salt2"])
    # ================================================================= 8. claims, refused, the duty map
    print("-- 8  Darpan's claims, a report refused today, the duty map's orphan duty")
    cl = [t for t in N["needs_claims"] if t.startswith("Claim for Darpan open")]
    check("a claim open 8 days: 'Claim for Darpan open 8 days: KEDWALK444 PHARMA bill W444F Rs 12,345'; the 3-day one is not raised",
          any("bill W444F Rs 12,345" in t and "open 8 days" in t for t in cl) and not any("W444G" in t for t in cl), cl)
    check("... settled -> gone", not [t for t in N["needs_claims_after"] if "W444F" in t], [t for t in N["needs_claims_after"] if "Claim" in t])
    check("a report refused today is named the same day", any(t.startswith("Report refused today: SALE_BILLWISE") and "line 52" in t for t in N["needs_final"]),
          [t for t in N["needs_final"] if "refused" in t])
    check("the duty map raises its orphan duty (no code raises it) and not the coded one",
          any(t.startswith("W444 orphan duty:") for t in N["needs_claims"]) and not any("SHOULD NOT SHOW" in t for t in N["needs_claims"]), [t for t in N["needs_claims"] if "W444" in t])
    print("-- 9  'Signed in' in the S440 BACK bar of Purchase orders (and only there)")
    P = N["porders"]
    check("Purchase orders: 'Signed in: alisha' inside the BACK bar; the bar once, '← BACK' once", P["status"] == 200 and P["signed_in_bar"] and P["bars"] == 1 and P["backs"] == 1, P)
    # ================================================================= NEGATIVE CONTROL: the box as it is
    print("-- 10 NEGATIVE CONTROL: the same walk on the box as it is")
    s = O["sign"]["Amir"]
    check("NEGATIVE: typed 'Amir' -> the old session is named 'Amir'; no redirect; no 'Amir ka kaam' tile (no grant)", s["u"] == "Amir" and s["first"][0] == 200 and not s["all"][1] and s["all"][3], s)
    check("NEGATIVE: the old token reads 'Amir' in the finance app and shows no grant on the portal", O["oldtoken"]["finance_who"] == "Amir" and not O["oldtoken"]["portal_all"][1], O["oldtoken"])
    check("NEGATIVE: no Hindi line for a login with no work (the unrelated tiles show)", not O["nowork"]["hindi"] and "Scan Purchase" in O["nowork"]["tiles"], O["nowork"])
    check("NEGATIVE: no paper amount on the bill line, no 'self' answer, no voucher card", not any((O["bill"][k] or {}).get("amt") for k in BILLS)
          and not any((O["bill"][k] or {}).get("self_radio") for k in BILLS) and not any(O["steps"][str(k)]["card"] for k in range(1, 8)), [O["bill"]["A"], O["steps"]["1"]])
    check("NEGATIVE: 'self' is not kept by the old page (the bill stays unanswered)", not any(O["self_after"][b]["disp"] for b in "DE"), O["self_after"])
    old_n = [t for t in O["needs_final"] + O["needs_claims"] + O["needs_visits"] if t.startswith(("Salt list", "Amir's own", "Claim for Darpan", "Count vouchers", "Report refused", "W444 orphan"))]
    check("NEGATIVE: no S444 Needs-you line", not old_n, old_n)
    check("NEGATIVE: KEDAR 195's claim stays open on the box as it is", O["kedar"]["claims"] and all(c["state"] == "open" for c in O["kedar"]["claims"]), O["kedar"])
    check("NEGATIVE: no red salt card, Shavez's row without its days", not O["salt1"]["s6"] and O["salt1"]["rep"]["days"] is None, [O["salt1"]["s6"], O["salt1"]["rep"]])
    check("NEGATIVE: the board has no BACK bar, Purchase orders no 'Signed in'", not O["board"]["back"] and not O["porders"]["signed_in_bar"], [O["board"], O["porders"]])
    print("WALK_S444 %s -- %d of %d passed" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0]))
    for f in fails:
        print("   FAILED: " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
