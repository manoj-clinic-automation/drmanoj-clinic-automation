#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p5.py -- kit S454_BILL_REGISTER, part 5 (S454 11: the items): THE REAL finance app over SCRATCH COPIES of finance.db, assets.db and
the spine (backup API; the asset copy is the walk's own), one process per side:

  NEW  the box (after P3B) + part 5's built files        OLD  the box as it is -- the NEGATIVE CONTROL
  I  11.1  the items page lists a crafted bill whose lines do not add up and not one whose lines do; its head line; the owner only
  L  11.2  the learning pairs a crafted verified bill's lines on quantity and rate and learns each name once; it does not learn from a bill
           that is not verified, nor from one whose line counts differ; the Sarvam check then reads those lines right
  R  today's data: August's and September's items check; September's item figure before and after the learning
  S  the staff-eye walk (DUTY_MAP v5) for reception, darpan, shavez, amir and the owner
Its rows are keyed W454P5; dates from today. No phone number or key in its output.

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
TAG = "W454P5JSON "


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


def probe():
    SIDE = os.environ["SIDE"]
    NEW = SIDE == "new"
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import purchase_app as pa                                          # noqa: E402
    import scan_register as SR                                         # noqa: E402
    assert pa.__file__.startswith(FIN), pa.__file__
    pa._assets_db = os.environ["ASSETS_DB"]
    IC = None
    if NEW:
        import item_check as IC                                        # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    adb = sqlite3.connect(os.environ["ASSETS_DB"], timeout=60)          # the walk's OWN scratch copy
    out = {}

    def G(u, p):
        h = {"X-Clinic-User": u, "X-Clinic-Role": ""}
        if u == "reception":
            h["Cookie"] = "clinic_who=shivani"
        r = fc.get(p, base_url=BASE, headers=h)
        return r.status_code, r.get_data(as_text=True)
    # ---------------------------------------------------------------- R  today's data, before anything of the walk's own
    db.execute(pa.S446_SARVAM_DDL)
    out["R_before"] = SR.sarvam(db, "2026-09")
    pa.sarvam_compare(db)
    out["R_after"] = SR.sarvam(db, "2026-09")
    out["R_learnt"] = IC.learnt(db) if NEW else []
    if NEW:
        out["R_check"] = {m: {k: v for k, v in IC.items_check(db, m).items() if k in ("n", "adds", "differs", "nolines")} for m in ("2026-08", "2026-09", "2026-10")}
    # ---------------------------------------------------------------- the walk's own bills
    md5 = "w454p5" + hashlib.md5(("x" + SIDE).encode()).hexdigest()[:26]
    ins(db, "purchase_export", dict(md5=md5, type="BILLITEMWISE", file="W454P5", period_from=D(30), period_to=D(0), export_stamp=NOW.strftime("%Y%m%d-%H%M%S"),
                                    received_at=NOW.isoformat(), n_rows=1, grand_amount_p=0), replace=True)
    SUP = "W454P5 PHARMA"
    SK = pa.supplier_key(SUP)

    def bill(no, day, amount_p, lines):
        bid = ins(db, "purchase_bill", dict(supplier_norm=SK, supplier=SUP, bill_no=no, bill_date=day, month=day[:7], cash_p=0, credit_p=amount_p, amount_p=amount_p,
                                            source_md5=md5, bw_md5=md5, sw_md5=md5, date_src="BILLWISE", bw_amount_p=amount_p, sw_amount_p=amount_p))
        for item, qty, rate_p, disc, tax in lines:
            v = qty * rate_p * (1 - disc / 100.0) * (1 + tax / 100.0)
            ins(db, "purchase_line", dict(supplier_norm=SK, bill_no=no, bill_date=day, month=day[:7], item=item, packing="1*10", tax=tax, qty=qty, free=None,
                                          rate_p=rate_p, discount_pct=disc, amount_p=int(qty * rate_p), net_rate_p=0, net_amount_p=int(round(v)), loose_qty=0,
                                          purchase_rate_p=rate_p, direction="PURCHASE", source_md5=md5, line_type="BILLITEMWISE"))
        db.commit()
        return bid
    month = TODAY.strftime("%Y-%m")
    dA = TODAY.replace(day=1).isoformat()
    bA = bill("W5410", dA, 105000, [("W454P5 MED ADDS", 10, 10000, 0, 5)])               # 10 x 100 + 5% = Rs 1,050: adds up
    bB = bill("W5411", dA, 100000, [("W454P5 MED SHORT", 10, 10000, 0, 5)])              # its line comes to Rs 1,050 against Rs 1,000: does not
    # ---------------------------------------------------------------- I  11.1
    s, h = G("manoj", "/finance/purchase/page/items?month=%s" % month)
    head = re.search(r'id="s454itemshead"><b>([^<]*)</b>', h)
    out["I"] = dict(status=s, A=('data-bill="%d"' % bA) in h, B=('data-bill="%d"' % bB) in h, head=_html.unescape(head.group(1)) if head else None,
                    diff=bool(re.search(r'data-bill="%d".*?\+₹50' % bB, h, re.S)))
    out["I_staff"] = {u: G(u, "/finance/purchase/page/items?month=%s" % month)[0] for u in ("darpan", "amir", "reception", "shavez")}
    s, h = G("manoj", "/finance/purchase/page/sarvam?month=2026-09")
    out["I_link"] = 'id="s454items"' in h
    # ---------------------------------------------------------------- L  11.2
    def scan(no, day, total, items):
        sid = ins(adb, "bills", dict(kind="Pharmacy", vendor=SUP, bill_no=no, bill_date=day, total_amount=total, status="captured", lane="pharmacy",
                                     stamp_no="W454P5-%s" % no, submitted_by="W454P5", submitted_at=NOW.strftime("%Y-%m-%d %H:%M"), ocr_status="read",
                                     bill_month=day[:7], scanned_by="W454P5"))
        for nm, q, r in items:
            ins(adb, "bill_items", dict(bill_id=sid, item_name=nm, quantity=q, rate=r, amount=q * r))
        adb.commit()
        return sid

    def link(bid, sid):
        ins(db, "purchase_scan_link", dict(bill_id=bid, asset_bill_id=sid, grade="EXACT", matched_on="W454P5 walk", linked_at=NOW.isoformat()))
        db.commit()
    dL = D(3)
    bV = bill("W5401", dL, 210000, [("W454P5 KORAX 5", 10, 10000, 0, 5), ("W454P5 VELOZ 20", 5, 20000, 0, 5)])
    sV = scan("W5401", dL, 2100.0, [("KORAMIN XR CAPSULE 10S", 10, 100.0), ("VELTRIX DUO SACHET 3S", 5, 200.0)])
    link(bV, sV)
    bU = bill("W5404", dL, 105000, [("W454P5 MED SIX", 10, 10000, 0, 5)])                  # verified, but the names share nothing
    sU = scan("W5404", dL, 1050.0, [("BARBELLY JUNCTION", 10, 100.0)])
    link(bU, sU)
    bN = bill("W5402", dL, 105000, [("W454P5 MED THREE", 10, 10000, 0, 5)])               # the scan read another number: not verified
    sN = scan("W5888", dL, 1050.0, [("KP GAMMA", 10, 100.0)])
    link(bN, sN)
    bC = bill("W5403", dL, 210000, [("W454P5 MED FOUR", 10, 10000, 0, 5), ("W454P5 MED FIVE", 5, 20000, 0, 5)])
    sC = scan("W5403", dL, 2100.0, [("MN DELTA", 10, 100.0)])                               # one line read of two: the counts differ
    link(bC, sC)
    cx = SR.Ctx(db)
    sc = SR.asset_scans(db) or {}
    out["L_verified"] = [SR.verified(SR.agree(cx, dict(sc[s_]), dict(db.execute("SELECT * FROM purchase_bill WHERE id=?", (b_,)).fetchone())))
                         for b_, s_ in ((bV, sV), (bN, sN), (bC, sC), (bU, sU))]
    pa.sarvam_compare(db)
    n1 = len(IC.learnt(db)) if NEW else 0
    pa.sarvam_compare(db)
    n2 = len(IC.learnt(db)) if NEW else 0
    mine = [x for x in (IC.learnt(db) if NEW else []) if x["supplier_norm"] == SK]
    out["L_learnt"] = dict(mine=sorted((x["scan_name"], x["marg_item"]) for x in mine), again=[n1, n2])

    def row(sid):
        r = db.execute("SELECT items_read, items_wrong, detail FROM purchase_sarvam_check WHERE asset_bill_id=?", (sid,)).fetchone()
        if not r:
            return None
        d = json.loads(r[2] or "{}")
        return dict(read=r[0], wrong=r[1], items=[(x.get("scan_item"), x.get("marg_item"), x.get("bad")) for x in d.get("items") or []])
    out["L_rows"] = dict(V=row(sV), N=row(sN), C=row(sC))
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
        fh.write("# W454P5 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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
        dbp, adbp, spp = [os.path.join(a.work, "w454p5_%s_%s.db" % (side, x)) for x in ("fin", "assets", "spine")]
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
    check("both probes ran to the end (NEW = after part 5, OLD = the box as it is)", N is not None and O is not None)
    if N is None or O is None:
        print("WALK_S454P5 RED -- a probe did not finish")
        return 1
    print("-- R  today's data")
    for m, r in sorted(N["R_check"].items()):
        print("   items check %s: %d of %d bills with lines add up, %d do not, %d with no lines" % (m, r["adds"], r["n"] - r["nolines"], r["differs"], r["nolines"]))
    rb, ra, ro_ = N["R_before"], N["R_after"], O["R_after"]
    print("   September's item figure: %d of %d read right before the learning; %d of %d after (the box as it is: %d of %d); names learnt: %d"
          % (rb["items_right"], rb["items_read"], ra["items_right"], ra["items_read"], ro_["items_right"], ro_["items_read"], len(N["R_learnt"])))
    for x in N["R_learnt"][:30]:
        print("     %s: '%s' = %s" % (x["supplier_norm"], x["scan_name"], x["marg_item"]))
    check("the learning never lowers September's figure, and the box as it is does not move it (%d -> %d; the box %d -> %d)"
          % (rb["items_right"], ra["items_right"], O["R_before"]["items_right"], ro_["items_right"]),
          ra["items_right"] >= rb["items_right"] and ro_["items_right"] == O["R_before"]["items_right"] and ra["items_read"] == rb["items_read"], [rb, ra, ro_])
    print("-- I  11.1 the items check")
    I = N["I"]
    check("the page lists the bill whose lines do not add up (+Rs 50) and not the one whose lines do", I["status"] == 200 and I["B"] and not I["A"] and I["diff"], I)
    check("its head line: '%s'" % I["head"], bool(I["head"]) and " add up " in I["head"] and "not." in I["head"], I["head"])
    check("the owner only: darpan, amir, reception and shavez are refused (%s)" % N["I_staff"], all(v != 200 for v in N["I_staff"].values()), N["I_staff"])
    check("one link to it on the Sarvam page", N["I_link"], N["I_link"])
    check("NEGATIVE: the box as it is has no items page and no link", O["I"]["status"] == 404 and not O["I_link"], [O["I"]["status"], O["I_link"]])
    print("-- L  11.2 learning the suppliers' item names")
    check("the walk's four pairs: verified, not verified (another number read), verified with one line read of two, verified",
          N["L_verified"] == [True, False, True, True], N["L_verified"])
    L = N["L_learnt"]
    check("from the verified pair both lines are learnt on quantity and rate: %s" % L["mine"],
          L["mine"] == [["KORAMIN XR CAPSULE 10S", "W454P5 KORAX 5"], ["VELTRIX DUO SACHET 3S", "W454P5 VELOZ 20"]], L)
    check("learnt once: the next pass learns nothing (%s)" % L["again"], L["again"][0] == L["again"][1], L["again"])
    check("nothing learnt from the bill that is not verified (KP GAMMA) nor from the one whose line counts differ (MN DELTA)",
          not [x for x in L["mine"] if x[0] in ("KP GAMMA", "MN DELTA")], L["mine"])
    check("nothing learnt where quantity and rate agree but the names share nothing (BARBELLY JUNCTION against W454P5 MED SIX)",
          not [x for x in L["mine"] if x[0] == "BARBELLY JUNCTION"], L["mine"])
    rv = N["L_rows"]["V"]
    check("the Sarvam check now reads the verified bill's two lines right, by the learnt names: %s" % rv, rv and rv["wrong"] == 0 and
          sorted((x[0], x[1]) for x in rv["items"]) == [("KORAMIN XR CAPSULE 10S", "W454P5 KORAX 5"), ("VELTRIX DUO SACHET 3S", "W454P5 VELOZ 20")], rv)
    ov = O["L_rows"]["V"]
    check("NEGATIVE: the box as it is reads both names as wrong: %s" % ov, ov and ov["wrong"] == 2 and all("name" in (x[2] or []) for x in ov["items"]), ov)
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
    print("WALK_S454P5 %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:900]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
