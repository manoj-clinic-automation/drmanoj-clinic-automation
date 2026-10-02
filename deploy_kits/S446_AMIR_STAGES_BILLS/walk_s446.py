#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s446.py -- kit S446_AMIR_STAGES_BILLS. THE REAL finance app (and the real portal, for the staff-eye walk) in one process per
side, over SCRATCH COPIES of finance.db and assets.db (backup API), through Flask's test clients. NEW = the box + the kit's six files;
OLD = the box as it is (the negative control). Sign-in for the staff-eye walk: the walk's own random secret and own user store in
scratch portal folders (never the live ones). Its own rows are keyed W446 (bills 'W446A/B' of 'KEDWALK446 PHARMA', scans stamped
'W446-nn', a claim 'W446C', crafted stock feeds 'push_snapshot W446' / 'push_expected base=W446 ...'); the live count's 37 vouchers are
read by key; every date is computed from today. Walk-only patches, each named where used: stock_watch.amir_view (the three doors'
due states) and packs.amir_pack for September (a crafted ready pack).

  --fin-new DIR --fin-old DIR --por DIR --ast DIR --shared DIR --db PATH --adb PATH --kit DIR --duty-map PATH
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

TODAY = dt.date.today()
SUP = "KEDWALK446 PHARMA"
USERS = {"amir": "staff", "darpan": "staff", "shavez": "manager", "manoj": "doctor"}


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


def DMY(d):
    return d.strftime("%d-%m-%Y")


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def ins(con, table, row, replace=False):
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    return con.execute("INSERT %sINTO %s (%s) VALUES (%s)" % ("OR REPLACE " if replace else "", table, ", ".join(cols), ", ".join("?" * len(cols))),
                       [row[c] for c in cols]).lastrowid


# ======================================================================= the PROBE (one process per side)
def probe():
    NEW = os.environ["MODE"] == "new"
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    W = json.loads(os.environ["W446"])
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import portal as po                                                # noqa: E402
    import amir_day                                                    # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}             # noqa: E731
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    db.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]   # noqa: E731
    out = {}

    def FG(u, p):
        r = fc.get(p, base_url=BASE, headers=H(u))
        return r.status_code, r.get_data(as_text=True), r.headers.get("Location", "")

    def FJ(u, p, body=None):
        r = fc.post(p, base_url=BASE, headers=H(u), json=body or {}) if body is not None else fc.get(p, base_url=BASE, headers=H(u))
        return r.status_code, (r.get_json(silent=True) or {})

    def text(h):
        return (re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).replace("&mdash;", "--").replace("&#10003;", "✓")
                .replace("&#8377;", "Rs ").replace("&middot;", "·").strip())

    def card(n=1):
        h = FG("amir", "/finance/amir/step/%d" % n)[1]
        m = re.search(r"id=s444duty.*?</div></div>", h, re.S)
        return text(m.group(0)) if m else ""

    def needs():
        return [l.get("text", "") for l in FJ("manoj", "/finance/sanjeevni/api/needs-you")[1].get("lines") or []]

    def board(u):
        s, j = FJ(u, "/finance/stock/api/pad/amir/1")
        vf = (j.get("made") or {}).get("vouchers_flat") or []
        return dict(status=s, n=len(vf), seq=[v["seq"] for v in vf], keys=["%d|%s|%d" % (v["round_no"], v["kind"], v["batch_no"]) for v in vf],
                    renames=bool(j.get("renames_ready")), stage=(j.get("stage") or {}).get("stage"))

    def enter(keys, no):
        res = []
        for k in keys:
            r, kind, b = k.split("|")
            res.append(FJ("amir", "/finance/stock/api/pad/vouchers/1/entered", dict(round=int(r), kind=kind, batch=int(b), marg_voucher_no=no))[0])
        return res

    def din_band():
        with fa.app.test_request_context("/finance/amir/step/7", base_url=BASE, headers=H("amir")):
            w = amir_day._work(db, amir_day._today())
            w["done"].update({2: True, 4: True, 5: True, 6: True, 7: False})
            return amir_day._ready_to_close(w) and ("Din band kijiye" in amir_day._step7(w))

    # ------------------------------------------------------------------ 0. the staff-eye walk (first, on the untouched scratch copy)
    pw = W["pw"]

    def login(user):
        r = pc.post("/portal/login", base_url=BASE, data={"user": user, "password": pw[user]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        return m.group(1) if m else ""

    def tiles(h):
        import html as _h                                              # noqa: PLC0415
        return [_h.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', h or "")]

    dm = json.load(open(os.environ["REAL_DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True)
    eye = {}
    for who in ("amir", "darpan", "shavez", "manoj"):
        tok = login(who)
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
        seen = tiles(r.get_data(as_text=True))
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
                for _hop in range(4):
                    rr2 = fc.get(path, base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
                    if rr2.status_code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                        path = rr2.headers["Location"].replace(BASE, "")
                        continue
                    body = rr2.get_data(as_text=True)
                    break
                row["door_seen"] = mark in body
            rows.append(row)
        eye[who] = dict(status=r.status_code, duties=rows)
    ro.close()
    out["eye"] = eye
    # ------------------------------------------------------------------ 1. Stage A: the orthotic vouchers only
    out["a_cards"] = {n: card(n) for n in range(1, 8)}
    out["a_board_amir"], out["a_board_manoj"] = board("amir"), board("manoj")
    out["a_din_band"] = din_band() if NEW else None
    ortho = W["ortho"]
    out["a_enter"] = enter(ortho, "W446-A")
    time.sleep(1.2)
    out["a_after_enter"] = card(1)
    # the crafted closing-stock exports: R (yesterday, before the first entry) carries every vouchered item at 100 on both feeds;
    # L (today, after the last entry) carries Marg moved by exactly its vouchers -- but for one orthotic item, one unit more
    need = W["need"]
    yday, tday = DMY(TODAY - dt.timedelta(days=1)), DMY(TODAY)
    exp_src = "push_expected base=W446 pur_to=%s" % TODAY.isoformat()

    def feed(as_on, marg, rec):
        for item, qty in marg.items():
            ins(db, "stock_feed", dict(as_on=as_on, source="push_snapshot W446", item=item, qty=qty, received_at=rec))
            ins(db, "stock_feed", dict(as_on=as_on, source=exp_src, item=item, qty=100, received_at=rec))
        db.commit()

    feed(yday, {i: 100 for i in need}, now_iso())
    wrong = sorted(W["ortho_items"])[0]
    m1 = {i: 100 + (need[i] if i in W["ortho_items"] else 0) for i in need}
    m1[wrong] += 1
    time.sleep(1.2)
    feed(tday, m1, now_iso())
    out["a_wrong"] = dict(card=card(1), item=wrong, marg=m1[wrong], should=m1[wrong] - 1)
    # Amir corrects that voucher in Marg and marks it again; the next export is right
    wk = [k for k in ortho if wrong in W["key_items"][k]]
    time.sleep(1.2)
    out["a_reenter"] = enter(wk, "W446-A2")
    time.sleep(1.2)
    m2 = dict(m1)
    m2[wrong] -= 1
    feed(tday, m2, now_iso())
    out["b_cards"] = {n: card(n) for n in (1, 6)}
    out["b_board_amir"] = board("amir")
    # ------------------------------------------------------------------ 2. Stage B: the renames, then a crafted export with the new names
    import item_alias                                                  # noqa: E402
    planned = [r["old_name"] for r in item_alias.rows(db) if r["state"] == "planned"]
    out["b_planned"] = len(planned)
    out["b_tick"] = [FJ("amir", "/finance/stock/api/pad/rename/tick", dict(old=o))[0] for o in planned]
    names = [r["new_name"] for r in item_alias.rows(db)]
    v = item_alias.verify_closing(db, names, TODAY.isoformat(), source="W446 crafted export", captured=dt.datetime.now().replace(microsecond=0).isoformat())
    db.commit()
    out["b_verified"] = len(v["verified"])
    out["c_cards"] = {n: card(n) for n in (1, 6)}
    out["c_board_amir"] = board("amir")
    n1 = needs()
    out["c_needs_once"] = sum(1 for t in n1 if t.startswith("Orthotics verified and renamed"))
    out["c_needs_stage"] = [t for t in n1 if t.startswith("Count #1:")]
    out["c_needs_again"] = sum(1 for t in needs() if t.startswith("Orthotics verified and renamed"))
    # ------------------------------------------------------------------ 3. Stage C: a verified lot releases the next 5; an unverified one after 2 visits
    lot1 = out["c_board_amir"]["keys"]
    time.sleep(1.2)
    out["c_enter1"] = enter(lot1, "W446-C1")
    time.sleep(1.2)
    lot_items = {}
    for k in lot1:
        for item, ch in W["key_lines"].get(k, []):
            lot_items[item] = lot_items.get(item, 0) + ch
    m3 = dict(m2)
    for i, ch in lot_items.items():
        m3[i] = 100 + ch
    feed(tday, m3, now_iso())
    out["c_after_verified"] = card(1)
    out["c_board2"] = board("amir")
    rel = q("SELECT id FROM stock_stage_event WHERE count_id=1 AND stage='C' AND event='release' ORDER BY id DESC LIMIT 1") if NEW else []
    if rel:
        # two of his visits AFTER that lot was released: the release is set 4 days back, and his visit days 3 and 2 days back exist
        db.execute("UPDATE stock_stage_event SET at=? WHERE id=?", (D(4) + "T00:00:00", rel[0]["id"]))
        for k in (3, 2):
            if not q("SELECT 1 FROM amir_day WHERE day=?", D(k)):
                ins(db, "amir_day", dict(day=D(k), opened_at=D(k) + " 08:00:00", closed_by="W446 walk"))
        db.commit()
    out["c_after_visits"] = card(1)
    out["c_board3"] = board("amir")
    out["c_din_band"] = din_band() if NEW else None
    # ------------------------------------------------------------------ 4. packs chosen by state
    out["p_before"] = card(1)
    out["p_seen"] = fc.post("/finance/amir/pack/2026-08/seen", base_url=BASE, headers=H("amir"), data={"go": "1"}).status_code
    out["p_after"] = card(1)
    try:
        import packs                                                   # noqa: E402
        real = packs.amir_pack
        packs.amir_pack = lambda con, m: dict(real(con, m), ready=True, seen=None) if m == W["prev"] else real(con, m)   # walk-only: a crafted ready pack
        out["p_crafted"] = card(1)
        packs.amir_pack = real
    except Exception as e:                                             # noqa: BLE001
        out["p_crafted"] = "ERR %s" % e
    out["p_foot_old_text"] = "Pichle mahine ka pack" in FG("amir", "/finance/amir/step/1")[1]
    # ------------------------------------------------------------------ 5. the bills as files; the Sarvam comparison
    s2 = FG("amir", "/finance/amir/step/2")[1]
    out["f_list_ids"] = sorted(int(x) for x in set(re.findall(r"/finance/purchase/api/scan-file/(\d+)", s2)))
    out["f_heading"] = bool(re.search(r"Marg mein daalne ke bill \(\d+\)", s2))
    sid = W["scan_today"]
    r = fc.get("/finance/purchase/api/scan-file/%d" % sid, base_url=BASE, headers=H("amir"))
    out["f_amir"] = [r.status_code, r.headers.get("Content-Disposition", ""), hashlib.md5(r.data).hexdigest()]
    out["f_alisha"] = fc.get("/finance/purchase/api/scan-file/%d" % sid, base_url=BASE, headers=H("alisha")).status_code
    out["f_manoj"] = fc.get("/finance/purchase/api/scan-file/%d" % sid, base_url=BASE, headers=H("manoj")).status_code
    r = fc.get("/finance/purchase/api/scan-files/today.zip", base_url=BASE, headers=H("amir"))
    try:
        import io, zipfile                                             # noqa: E401
        z = zipfile.ZipFile(io.BytesIO(r.data))
        out["f_zip"] = [r.status_code, sorted(z.namelist())]
    except Exception:                                                  # noqa: BLE001
        out["f_zip"] = [r.status_code, None]
    out["f_zip_alisha"] = fc.get("/finance/purchase/api/scan-files/today.zip", base_url=BASE, headers=H("alisha")).status_code
    try:
        import purchase_app                                            # noqa: E402
        purchase_app.sarvam_compare(db)
        out["s_row"] = (q("SELECT supplier_ok, billno_ok, date_ok, total_ok, items_read, items_wrong, all_ok, month FROM purchase_sarvam_check WHERE asset_bill_id=?",
                          W["scan_linked"]) or [None])[0]
        mth = TODAY.strftime("%Y-%m")
        out["s_summary"] = purchase_app.sarvam_summary(db, mth)
        out["s_rows_month"] = db.execute("SELECT COUNT(*), SUM(all_ok) FROM purchase_sarvam_check WHERE month=?", (mth,)).fetchone()[:]
    except Exception as e:                                             # noqa: BLE001
        out["s_row"] = "ERR %s" % e
    out["s_scans_page"] = "id=\"s446sarvam\"" in FG("manoj", "/finance/purchase/page/scans")[1]
    out["s_needs"] = [t for t in needs() if t.startswith("Sarvam trial")]
    h5 = FG("amir", "/finance/amir/step/5")[1]
    out["s_bill_line"] = text((re.search(r"W446B.*?id='s444amt'>(.*?)</div>", h5, re.S) or [None, ""])[1]) if "W446B" in h5 else None
    hp = FG("manoj", "/finance/purchase/page/pay/%s" % TODAY.strftime("%Y-%m"))[1]
    out["s_pay"] = dict(marg=("1,23,456" in hp or "123,456" in hp or "1,23,456" in text(hp)), scan=("1,23,506" in text(hp)))
    # ------------------------------------------------------------------ 6. the doors
    try:
        import stock_watch                                             # noqa: E402
        real_v = stock_watch.amir_view
        stock_watch.amir_view = lambda con: dict(ok=True, plan=dict(status="open"), bill_pending=[1, 2], fixes=[1, 2, 3])   # walk-only: the due states
        out["d_due"] = card(1)
        stock_watch.amir_view = real_v
        out["d_not_due"] = card(1)
    except Exception as e:                                             # noqa: BLE001
        out["d_due"] = out["d_not_due"] = "ERR %s" % e
    s, j = FJ("darpan", "/finance/darpan/kal/api/day")
    out["k_claims"] = [c.get("bill_no") for c in (j.get("amir_claims") or [])] if "amir_claims" in j else None
    out["k_page"] = "Amir ke claim" in FG("darpan", "/finance/darpan/kal")[1]
    cid = W["claim"]
    out["k_ans1"] = FJ("darpan", "/finance/darpan/kal/api/claim-answer", dict(id=cid, answer="baat_hui"))[0]
    out["k_state1"] = (q("SELECT state FROM amir_claim WHERE id=?", cid) or [{}])[0].get("state")
    out["k_ans2"] = FJ("darpan", "/finance/darpan/kal/api/claim-answer", dict(id=cid, answer="mil_gaya"))[0]
    out["k_state2"] = (q("SELECT state, settled_outcome FROM amir_claim WHERE id=?", cid) or [{}])[0]
    out["k_after"] = [c.get("bill_no") for c in (FJ("darpan", "/finance/darpan/kal/api/day")[1].get("amir_claims") or [])]
    s, hp, loc = FG("shavez", "/finance/purchase/page/pay")
    hp2 = FG("shavez", loc.replace(BASE, "").replace("http://localhost", ""))[1] if loc else hp
    out["v_earlier"] = text((re.search(r'id="s446earlier".*?</div></div>', hp2, re.S) or [""])[0])
    nn = needs()
    out["r_line"] = [t for t in nn if "return" in t.lower() and "OK" in t]
    try:
        import returns_kinds                                           # noqa: E402
        tot, dates = 0, []
        for k in range(6):
            mm = (TODAY.replace(day=1) - dt.timedelta(days=1) * 0)
            y, m_ = TODAY.year, TODAY.month - k
            while m_ <= 0:
                y, m_ = y - 1, m_ + 12
            ym = "%04d-%02d" % (y, m_)
            tot += returns_kinds.pending_count(db, "medical", ym)[0]
        out["r_expected"] = tot
    except Exception as e:                                             # noqa: BLE001
        out["r_expected"] = "ERR %s" % e
    print("W446JSON " + json.dumps(out, default=str))


# ======================================================================= the WALK
def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--por", "--ast", "--shared", "--db", "--adb", "--kit", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    for p in (a.db, a.adb):
        assert p.startswith("/tmp/"), "refusing a non-scratch database: " + p
    n, fails = [0], []

    def check(label, cond, got=None):
        n[0] += 1
        print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:420] + "]") if got is not None else ""))
        if not cond:
            fails.append(label)

    def copydb(src, dst):
        s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
        d = sqlite3.connect(dst)
        s.backup(d)
        d.close()
        s.close()

    # ---- the walk's own sign-in (staff-eye): a random secret and its own user store in the scratch portal folder
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    assert a.por.startswith("/tmp/")
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W446 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w446-walk-seed'\n" % secret)
    sys.path.insert(0, a.por)
    import clinic_users                                                # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    try:
        clinic_users.add_role(store, "staff")
    except ValueError:
        pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])
    # ---- the live count's vouchers, read by key on the scratch copy
    F = sqlite3.connect(a.db)
    bat = {}
    for rno, kind, bno, sec, item, ch in F.execute("SELECT round_no, kind, batch_no, section, item, change FROM stock_voucher_line WHERE count_id=1"):
        b = bat.setdefault("%d|%s|%d" % (rno, kind, bno), dict(secs=set(), lines=[]))
        b["secs"].add(sec or "")
        b["lines"].append((item, int(ch or 0)))
    ortho = sorted([k for k, b in bat.items() if "Orthotics" in b["secs"]], key=lambda k: (k.split("|")[1] != "ISSUE", int(k.split("|")[0]), int(k.split("|")[2])))
    need = {}
    for b in bat.values():
        for item, ch in b["lines"]:
            need[item] = need.get(item, 0) + ch
    ortho_items = sorted({i for k in ortho for i, _c in bat[k]["lines"]})
    F.close()
    # ---- the crafted rows, the same ids on both sides
    copydb(a.db, a.db + ".old")
    copydb(a.adb, a.adb + ".old")
    up = os.path.join(os.path.dirname(a.adb), "w446_uploads")
    os.makedirs(up, exist_ok=True)
    pdf = b"%PDF-1.4\n% W446 walk paper\n" + secrets.token_bytes(64) + b"\n%%EOF\n"
    with open(os.path.join(up, "w446_today.pdf"), "wb") as fh:
        fh.write(pdf)
    with open(os.path.join(up, "w446_linked.pdf"), "wb") as fh:
        fh.write(pdf + b"x")

    def craft(fin, ast):
        Fc = sqlite3.connect(fin, timeout=30)
        Ac = sqlite3.connect(ast, timeout=30)
        md5 = "w446" + hashlib.md5(b"bw").hexdigest()[:28]
        ins(Fc, "purchase_export", dict(md5=md5, type="BILLWISE", file="W446", period_from=TODAY.replace(day=1).isoformat(), period_to=TODAY.isoformat(),
                                        export_stamp=dt.datetime.now().strftime("%Y%m%d-%H%M%S"), received_at=now_iso(), n_rows=1, grand_amount_p=0), replace=True)
        s1 = ins(Ac, "bills", dict(kind="Pharmacy", vendor=SUP, bill_no="W446A", bill_date=TODAY.isoformat(), total_amount=500.0, notes="W446 walk",
                                   created_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), stamp_no="W446-01", status="captured", ocr_status="read",
                                   lane="pharmacy", source_stored="w446_today.pdf", source_orig="w446"))
        s2 = ins(Ac, "bills", dict(kind="Pharmacy", vendor=SUP, bill_no="W446B", bill_date=D(1), total_amount=1240.56, notes="W446 walk",
                                   created_at=(dt.datetime.now() - dt.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), stamp_no="W446-02", status="captured",
                                   ocr_status="read", lane="pharmacy", source_stored="w446_linked.pdf", source_orig="w446"))
        ins(Ac, "bill_items", dict(bill_id=s2, item_name="W446 TAB ALPHA 10", quantity=10, rate=50.0, batch="B1", expiry="01/28"))
        ins(Ac, "bill_items", dict(bill_id=s2, item_name="W446 TAB BETA 10", quantity=7, rate=20.0, batch="B2", expiry="02/28"))
        bid = ins(Fc, "purchase_bill", dict(supplier_norm=SUP, supplier=SUP, bill_no="W446B", bill_date=D(1), month=D(1)[:7], cash_p=0, credit_p=123456,
                                             amount_p=123456, source_md5=md5, bw_md5=md5, bw_amount_p=123456, date_src="BILLWISE", scan_bill_id=s2))
        ins(Fc, "purchase_scan_link", dict(bill_id=bid, asset_bill_id=s2, grade="EXACT", matched_on="W446 walk", linked_at=now_iso()))
        for item, qty, rate in (("W446 TAB ALPHA 10", 10, 5000), ("W446 TAB BETA 10", 5, 2000)):
            ins(Fc, "purchase_line", dict(supplier_norm=SUP, bill_no="W446B", bill_date=D(1), month=D(1)[:7], item=item, qty=qty, free=0, rate_p=rate,
                                          batch=("B1" if "ALPHA" in item else "B2"), expiry=("01/28" if "ALPHA" in item else "02/28"), amount_p=qty * rate, source_md5=md5))
        cid = ins(Fc, "amir_claim", dict(supplier=SUP, supplier_norm=SUP, bill_no="W446C", bill_date=D(3), amount_p=55500, reason="short", raised_by="amir",
                                         raised_at=D(2) + " 10:00:00", state="open"))
        ins(Fc, "setting", dict(key="purchase.sarvam_trial_until", value=(TODAY + dt.timedelta(days=60)).isoformat(), note="W446 walk"), replace=True)
        Fc.commit(); Ac.commit(); Fc.close(); Ac.close()
        return dict(scan_today=s1, scan_linked=s2, claim=cid, bill=bid)

    ids = craft(a.db, a.adb)
    assert ids == craft(a.db + ".old", a.adb + ".old"), "the crafted rows must carry the same ids on both sides"
    print("-- crafted on both sides: scans W446-01 (today, unlinked) / W446-02 (linked to Marg bill W446B, Sarvam read Rs 1,240.56 against Marg Rs 1,234.56, "
          "BETA qty 7 against 5), claim W446C (raised %s), the Sarvam trial setting; the live count #1: %d vouchers, %d orthotic" % (D(2), len(bat), len(ortho)))
    t = TODAY.replace(day=1) - dt.timedelta(days=1)
    W = dict(pw=pw, ortho=ortho, need=need, ortho_items=ortho_items, key_items={k: sorted({i for i, _c in b["lines"]}) for k, b in bat.items()},
             key_lines={k: b["lines"] for k, b in bat.items()}, prev=t.strftime("%Y-%m"), **ids)

    def run(side):
        fin = a.fin_new if side == "new" else a.fin_old
        dbp, adbp = (a.db, a.adb) if side == "new" else (a.db + ".old", a.adb + ".old")
        env = dict(os.environ, MODE=side, FINDIR=fin, PORDIR=a.por, FINANCE_DB=dbp, ASSETS_DB=adbp, ASSETS_UPLOADS=up, FINANCE_ALLOW_HEADER_AUTH="1",
                   FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"),
                   CLINIC_SSO_SECRET=secret, REAL_DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, SHARED_LIB_DIR=a.shared, W446=json.dumps(W))
        env.pop("SARVAM_API_KEY", None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=1800)
        js = [l for l in p.stdout.splitlines() if l.startswith("W446JSON ")]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (side, p.returncode))
            for l in p.stdout.splitlines()[-25:]:
                print("   " + l[:300])
            return None
        return json.loads(js[-1][9:])

    N = run("new")
    O = run("old")
    check("both probes ran to the end (new / old)", N is not None and O is not None)
    if N is None or O is None:
        print("WALK_S446 RED -- a probe did not finish")
        return 1
    print("-- 0  the staff-eye walk (DUTY_MAP.json): amir, darpan, shavez and the owner")
    for who in ("amir", "darpan", "shavez", "manoj"):
        e = N["eye"][who]
        missing = [d["id"] for d in e["duties"] if d["tile"] and not d["tile_seen"]]
        unseen = [d["id"] for d in e["duties"] if d.get("door_seen") is False]
        errs = [d["id"] for d in e["duties"] if isinstance(d.get("due_n"), str)]
        due = [(d["id"], d["due_n"]) for d in e["duties"] if isinstance(d.get("due_n"), int) and d["due_n"] > 0]
        check("%s: %d duties; every tile on the home; every due duty's door shows it (%s)" % (who, len(e["duties"]), ", ".join("%s %s" % x for x in due) or "none due"),
              e["status"] == 200 and e["duties"] and not missing and not unseen and not errs, dict(missing=missing, unseen=unseen, errors=errs))
    print("-- 1  Stage A: the orthotic vouchers only")
    no = len(W["ortho"])
    check("every step 1-7 shows 'Orthotic voucher baaki: %d' and nothing of medicine or renames" % no,
          all(("Orthotic voucher baaki: %d" % no) in N["a_cards"][str(k)] and "Dawa" not in N["a_cards"][str(k)] and "Naam badlo" not in N["a_cards"][str(k)]
              and "Stock voucher baaki" not in N["a_cards"][str(k)] for k in range(1, 8)), N["a_cards"]["1"][:200])
    ba, bm = N["a_board_amir"], N["a_board_manoj"]
    check("Amir's board lists the %d orthotic vouchers only, numbered 1..%d, ISSUE first; no renames" % (no, no),
          ba["status"] == 200 and ba["n"] == no and ba["seq"] == list(range(1, no + 1)) and ba["keys"] == W["ortho"] and not ba["renames"] and ba["stage"] == "A", ba)
    check("the owner's board still lists all %d" % len(W["key_items"]), bm["n"] == len(W["key_items"]), bm["n"])
    check("Din band offered in Stage A (the gate steps unchanged)", N["a_din_band"] is True)
    check("all %d marked entered -> 'Ab closing stock export kijiye'" % no, all(s == 200 for s in N["a_enter"]) and "Ab closing stock export kijiye" in N["a_after_enter"], N["a_after_enter"][:200])
    aw = N["a_wrong"]
    check("a crafted export with ONE orthotic item wrong: that item named with Marg's figure and the one it should be, and its voucher; no rename shown",
          aw["item"] in aw["card"] and ("Marg mein %d, hona chahiye %d" % (aw["marg"], aw["should"])) in aw["card"] and "voucher" in aw["card"] and "Naam badlo" not in aw["card"], aw)
    check("corrected and marked again, a clean export: 'Orthotic: sab sahi ✓' and 'Naam badlo: %d naam'; still no medicine voucher" % N["b_planned"],
          "Orthotic: sab sahi ✓" in N["b_cards"]["1"] and ("Naam badlo: %d naam" % N["b_planned"]) in N["b_cards"]["1"] and "Dawa" not in N["b_cards"]["1"]
          and N["b_board_amir"]["renames"] and N["b_board_amir"]["n"] == 0, [N["b_cards"]["1"][:200], N["b_board_amir"]])
    print("-- 2  Stage B -> C: a crafted export with the new names")
    check("every rename ticked and the export with the new names verifies them (%d)" % N["b_verified"],
          all(s == 200 for s in N["b_tick"]) and N["b_verified"] == N["b_planned"], [N["b_tick"][:3], N["b_verified"]])
    cc = N["c_cards"]["1"]
    check("'Orthotic poora ✓' and Stage C's first 5: 'Dawa voucher: aaj ke 5 (baaki %d)'" % (len(W["key_items"]) - no - 5),
          "Orthotic poora ✓" in cc and ("Dawa voucher: aaj ke 5 (baaki %d)" % (len(W["key_items"]) - no - 5)) in cc, cc[:200])
    cb = N["c_board_amir"]
    check("his board lists those 5, numbered 1..5, oldest round first", cb["n"] == 5 and cb["seq"] == [1, 2, 3, 4, 5] and cb["keys"][0].startswith("1|"), cb)
    check("the owner's line 'Orthotics verified and renamed -- live orthotic ordering can start' -- once", N["c_needs_once"] == 1 and N["c_needs_again"] == 1,
          [N["c_needs_once"], N["c_needs_again"]])
    check("the owner's one small line of where the count stands", any("Stage C" in t for t in N["c_needs_stage"]), N["c_needs_stage"])
    check("a lot entered and verified on the next export releases the next 5: 'aaj ke 5 (baaki %d)'" % (len(W["key_items"]) - no - 10),
          ("aaj ke 5 (baaki %d)" % (len(W["key_items"]) - no - 10)) in N["c_after_verified"] and N["c_board2"]["n"] == 5 and N["c_board2"]["keys"] != cb["keys"],
          [N["c_after_verified"][:160], N["c_board2"]])
    check("a lot left unverified: the next 5 after 2 of his visits; the unverified lot stays listed (10 on his board)",
          ("aaj ke 5 (baaki %d)" % (len(W["key_items"]) - no - 15)) in N["c_after_visits"] and N["c_board3"]["n"] == 10, [N["c_after_visits"][:160], N["c_board3"]["n"]])
    check("Din band offered in Stage C", N["c_din_band"] is True)
    print("-- 3  the monthly packs, chosen by state")
    check("August's pack in the card until 'dekh liya'", "Mahine ka pack -- August 2026" in N["p_before"] and N["p_seen"] in (200, 302, 303)
          and "August 2026" not in N["p_after"], [N["p_before"][-200:], N["p_seen"], N["p_after"][-120:]])
    pm = "%s %s" % (("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")[int(W["prev"][5:7]) - 1], W["prev"][:4])
    check("a crafted ready pack for %s appears (walk-only patch of packs.amir_pack)" % pm, ("Mahine ka pack -- %s" % pm) in N["p_crafted"], N["p_crafted"][-200:])
    check("the old foot card is gone", N["p_foot_old_text"] is False)
    print("-- 4  the scanned bills as files; Marg overrules Sarvam")
    check("step 2: 'Marg mein daalne ke bill (N)' lists exactly the captured pharmacy scans with no Marg bill (the crafted today's among them, the linked one not)",
          N["f_heading"] and ids["scan_today"] in N["f_list_ids"] and ids["scan_linked"] not in N["f_list_ids"], N["f_list_ids"][-5:])
    want_name = "%s_W446A_%s.pdf" % (SUP.replace(" ", "_"), DMY(TODAY))
    check("a download carries the new name and the stored bytes (md5 equal)", N["f_amir"][0] == 200 and want_name in N["f_amir"][1] and N["f_amir"][2] == hashlib.md5(pdf).hexdigest(), N["f_amir"])
    check("the zip holds today's", N["f_zip"][0] == 200 and want_name in (N["f_zip"][1] or []), N["f_zip"])
    check("another staff login gets 403 (file and zip); the owner 200", N["f_alisha"] == 403 and N["f_zip_alisha"] == 403 and N["f_manoj"] == 200, [N["f_alisha"], N["f_zip_alisha"], N["f_manoj"]])
    sr = N["s_row"]
    check("a crafted linked scan writes its comparison row: supplier, bill no., date agree; total wrong (Sarvam Rs 1,240.56, Marg Rs 1,234.56); 1 item of 2 wrong",
          isinstance(sr, dict) and sr["supplier_ok"] == 1 and sr["billno_ok"] == 1 and sr["date_ok"] == 1 and sr["total_ok"] == 0 and sr["items_read"] == 2
          and sr["items_wrong"] == 1 and sr["all_ok"] == 0, sr)
    ss, rm = N.get("s_summary") or {}, N.get("s_rows_month") or [0, 0]
    check("the owner's summary adds up: bills = rows of the month; agreed = rows all right", ss.get("n") == rm[0] and ss.get("agreed") == (rm[1] or 0) and ss.get("total_wrong", 0) >= 1, [ss, rm])
    check("the Scan links page carries the Sarvam line; the monthly Needs-you summary is there", N["s_scans_page"] and N["s_needs"], N["s_needs"][:1])
    check("Marg's total is the bill's: Amir's line reads 'Marg: Rs 1,235' (Marg's Rs 1,234.56), Sarvam's Rs 1,241 only as the paper prompt",
          bool(N["s_bill_line"]) and "Marg: Rs 1,235" in N["s_bill_line"] and "Kaagaz (scan): Rs 1,241" in N["s_bill_line"], N["s_bill_line"])
    print("-- 5  the doors")
    check("the card's three door lines show while due (walk-only patch of stock_watch.amir_view) and only then",
          all(x in N["d_due"] for x in ("Poori ginti ka Sunday", "Marg mein bill baaki: 2", "Stock trace ke sudhar: 3"))
          and not any(x in N["d_not_due"] for x in ("Poori ginti ka Sunday", "Marg mein bill baaki", "Stock trace ke sudhar")), [N["d_due"][-200:], N["d_not_due"][-80:]])
    check("Darpan's Kal ka hisaab lists the crafted claim W446C and carries 'Amir ke claim'", N["k_claims"] is not None and "W446C" in N["k_claims"] and N["k_page"], N["k_claims"])
    check("his taps: 'Supplier se baat ho gayi' -> contacted; 'Credit / maal mil gaya' -> settled, and it leaves the list",
          N["k_ans1"] == 200 and N["k_state1"] == "contacted" and N["k_ans2"] == 200 and N["k_state2"].get("state") == "settled" and "W446C" not in N["k_after"],
          [N["k_ans1"], N["k_state1"], N["k_ans2"], N["k_state2"], N["k_after"]])
    check("Shavez's Vendor payments shows 'Pichhle mahine ka baaki' with the earlier month", "Pichhle mahine ka baaki" in N["v_earlier"], N["v_earlier"][:200])
    rl = N["r_line"]
    check("the returns line counts every open month by the S406 rule: %s" % N["r_expected"],
          (N["r_expected"] == 0 and not rl) or (rl and rl[0].startswith("Counter returns waiting for your OK: %s," % N["r_expected"]) and "oldest" in rl[0]), rl)
    print("-- 6  NEGATIVE CONTROL: the same walk on the box as it is")
    check("NEGATIVE: the old card -- 'Stock voucher baaki: N orthotic, M dawa' -- shows medicine with orthotic; no stage", "Stock voucher baaki:" in O["a_cards"]["1"] and "Orthotic voucher baaki" not in O["a_cards"]["1"], O["a_cards"]["1"][:160])
    check("NEGATIVE: the old board lists all %d to Amir" % len(W["key_items"]), O["a_board_amir"]["n"] == len(W["key_items"]), O["a_board_amir"]["n"])
    check("NEGATIVE: no August pack, no bills list, no file door (404)", "Mahine ka pack" not in O["p_before"] and not O["f_heading"] and O["f_amir"][0] == 404, [O["f_heading"], O["f_amir"][0]])
    check("NEGATIVE: no claims on Darpan's page, no earlier-month card, no Sarvam row", O["k_claims"] is None and not O["v_earlier"] and not isinstance(O["s_row"], dict),
          [O["k_claims"], O["v_earlier"][:40], str(O["s_row"])[:60]])
    check("NEGATIVE: the old returns line is this month only", not any("Counter returns waiting" in t for t in O["r_line"]), O["r_line"])
    print("WALK_S446 %s -- %d of %d passed" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0]))
    for f in fails:
        print("   FAILED: " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
