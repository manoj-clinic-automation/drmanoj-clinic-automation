#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p2.py -- kit S454_BILL_REGISTER, part 2 (S454 5, 6, 7, 8, 12): THE REAL finance app and portal over SCRATCH COPIES of finance.db and
assets.db (backup API), through Flask's test clients, one process per side:

  NEW  the finance files with part 2's built files       OLD  the box as it is -- the NEGATIVE CONTROL
  R  the rules (scan_register): supplier, bill number, date, total; the three states; the noise
  L  the matcher on September's real data: every link kept; the auto-link (and two candidates ask); a wrong paper from a line settles nothing
  Q  the questions: "the amount differs" beyond the noise; a paired scan whose date or number differs makes no card
  A  Amir: purchase.entry_mode paper / both; digital refused; his paid NEFT sheet holds no account number
  G  the month's register: the head adds up, every bill in one state and the same on every page, a double entry one row, parked / counted,
     the owner's accept and undo; no Roman Hindi on it
  N  what reaches a person: Shavez's line and the owner's Needs-you on a counted line older than purchase.scan_wait_days, gone on its scan;
     none for a parked month; a read scan not in Marg after purchase.entry_wait_days (the owner only); "Last 7 days"
  S  the Sarvam counter; a parked month's amount answer on the register
  V  Vendor payments for the owner and Shavez only (and the phone book's accounts); the phone's keyed queue as before
  D  manoj.returns_ok equals the owner's returns line
  E  the staff-eye walk (DUTY_MAP v5) for reception, darpan, shavez, amir and the owner
Its own rows are keyed W454P2 (suppliers 'W454P2 ... PHARMA', scans stamped 'W454P2-..'); dates computed from today (ORDER_TODAY only inside N);
no phone number, account number or key reaches its output (the walk stops red if a seeded string does).

  --fin-new DIR --fin-old DIR --por DIR --db PATH --adb PATH --work DIR --duty-map-new FILE --duty-map-old FILE [--pictures DIR]
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
USERS = {"reception": "staff", "darpan": "staff", "shavez": "manager", "amir": "staff", "manoj": "doctor", "shivani": "staff", "bhati": "staff"}
TAG = "W454P2JSON "
HINDI = ("karo", "kijiye", " hai ", "baaki", "nahi ", "dawa", "kaam")


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


# ======================================================================= the PROBE (one process per side)
def probe():
    SIDE = os.environ["SIDE"]
    NEW = SIDE == "new"
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                           # noqa: E402
    import purchase_app as pa                                          # noqa: E402
    import porders                                                     # noqa: E402
    import porders_s454 as PS                                          # noqa: E402
    import order_sheet as OS                                           # noqa: E402
    assert pa.__file__.startswith(FIN), pa.__file__
    pa._assets_db = os.environ["ASSETS_DB"]
    SR = None
    if NEW:
        import scan_register as SR                                     # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    adb = sqlite3.connect(os.environ["ASSETS_DB"], timeout=60)
    adb.row_factory = sqlite3.Row
    out = {}
    secrets_seen = []

    def H(u):
        h = {"X-Clinic-User": u, "X-Clinic-Role": ""}
        if u == "reception":
            h["Cookie"] = "clinic_who=shivani"
        return h

    def G(u, p):
        r = fc.get(p, base_url=BASE, headers=H(u))
        return r.status_code, r.get_data(as_text=True)

    def GB(u, p):
        r = fc.get(p, base_url=BASE, headers=H(u))
        return r.status_code, r.get_data()

    def J(u, p, body=None):
        r = fc.post(p, base_url=BASE, headers=H(u), json=body if body is not None else {})
        return r.status_code, (r.get_json(silent=True) or {})

    def setv(k, v):
        db.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
        db.commit()

    def needs():
        r = fc.get("/finance/sanjeevni/api/needs-you", base_url=BASE, headers=H("manoj"))
        return [l.get("text", "") for l in (r.get_json(silent=True) or {}).get("lines") or []]

    def export_md5(tag="a"):
        md5 = "w454p2" + hashlib.md5(("bw454p2" + SIDE + tag).encode()).hexdigest()[:26]
        if not db.execute("SELECT 1 FROM purchase_export WHERE md5=?", (md5,)).fetchone():
            ins(db, "purchase_export", dict(md5=md5, type="BILLWISE", file="W454P2 walk", period_from=D(60), period_to=TODAY.isoformat(),
                                            export_stamp=NOW.strftime("%Y%m%d-%H%M%S"), received_at=NOW.isoformat(), n_rows=1, grand_amount_p=0), replace=True)
            db.commit()
        return md5

    def marg_bill(supplier, bill_no, date_iso, amount_p, tag="a"):
        md5 = export_md5(tag)
        bid = ins(db, "purchase_bill", dict(supplier_norm=pa.supplier_key(supplier), supplier=supplier, bill_no=bill_no, bill_date=date_iso, month=date_iso[:7],
                                            cash_p=0, credit_p=amount_p, amount_p=amount_p, source_md5=md5, bw_md5=md5, bw_amount_p=amount_p, date_src="BILLWISE"))
        db.commit()
        return bid

    def scan(stamp, vendor, bill_no, bill_date, amount, at, ocr="read"):
        sid = ins(adb, "bills", dict(kind="Pharmacy", vendor=vendor, bill_no=bill_no, bill_date=bill_date, total_amount=amount, notes="W454P2 walk",
                                     created_at=(at - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"), submitted_at=at.strftime("%Y-%m-%d %H:%M"),
                                     stamp_no=stamp, status="captured", ocr_status=ocr, lane="pharmacy", source_stored="w454p2_%s.pdf" % stamp,
                                     source_orig="w454p2", submitted_by="W454P2 walk", bill_month=(bill_date or at.strftime("%Y-%m-%d"))[:7]))
        adb.commit()
        return sid

    def links():
        return {r[0]: (r[1], r[2]) for r in db.execute("SELECT bill_id, asset_bill_id, grade FROM purchase_scan_link")}

    def bill_of(sup, no):
        r = db.execute("SELECT id FROM purchase_bill WHERE bill_no=? AND supplier_norm LIKE ? ORDER BY id DESC LIMIT 1", (no, sup.split()[0] + "%")).fetchone()
        return r[0] if r else None

    pa._ensure(db)
    OS.ensure(db)
    # ---------------------------------------------------------------- R  the rules
    if NEW:
        cx = SR.Ctx(db)
        sv = lambda a, b: SR.supplier(cx, a, b)                         # noqa: E731
        out["R_supplier"] = dict(
            pvt=sv("GUNINA PHARMACEUTICALS PVT. LTD.", "GUNINA PHARMACEUTICALS PVT LTD"), extn=sv("ESS KAY AGENCIES (EXTN)", "ESS KAY AGENCIES EXTN"),
            amp=sv("W454P2 SURGICAL & MEDICALS", "W454P2 SURGICAL AND MEDICALS"), bly=sv("W454P2 RAMA PHARMA BAREILLY", "W454P2 RAMA PHARMA"),
            p_inside=[SR.sup_norm("JP PHARMA"), SR.sup_norm("A P PHARMA PVT. LTD."), SR.sup_norm("M/S W454P2 PHARMA CO.")],
            shop=sv("M/S SANJEEVNI MEDICOS", "DEEPAM PHARMA"), heading=sv("WHOLE SALE CHEMIST & DRUGGIST", "DRUG DEAL"),
            other=sv("W454P2 RAMA PHARMA", "W454P2 SHYAM PHARMA"))
        out["R_billno"] = dict(series=SR.billno("YS/0585/2026-27", "585"), prefix=SR.billno("GPPL-26-64906", "64906"), tail=SR.billno("18112 (NOT015878)", "15878"),
                               licence=SR.billno("21/2014/BLY", "21"), dl=SR.billno("DL NO 20B 4521", "4521"), wrong=SR.billno("KT-475964", "75904"),
                               marg_zeros=SR.billno("A000363", "A000363"), empty=SR.billno("", "5"), fy_only=SR.billno("2026-27", "2026"))
        out["R_date"] = dict(year=SR.date_md("2024-09-18", "2026-09-18"), month=SR.date_md("2026-03-12", "2026-09-12"), none=SR.date_md("", "2026-09-12"))
        b0 = dict(supplier="W454P2 RAMA PHARMA", bill_no="A000777", bill_date="2026-09-12", amount_p=352800)

        def st(**kw):
            s = dict(id=None, vendor="W454P2 RAMA PHARMA", bill_no="A000777", bill_date="2026-09-12", amount_p=352800)
            s.update(kw)
            a = SR.agree(cx, s, b0)
            return [SR.pair_state(a), a["supplier"], a["billno"], a["date"], a["total"]]
        out["R_states"] = dict(month_wrong=st(bill_date="2026-03-12"), number_misread=st(bill_no="A000771"), rs6=st(amount_p=352800 + 600),
                               rs243=st(amount_p=352800 + 24300), no_total=st(amount_p=None), shop_and_date=st(vendor="SANJEEVNI MEDICOS", bill_date="2026-03-12"))
    # ---------------------------------------------------------------- L  the matcher on September's real data
    links0 = links()
    r0 = pa._rematch(db, "W454P2 walk")
    links1 = links()
    out["L_kept"] = sorted(b for b in links0 if b not in links1)
    out["L_new"] = sorted((b, links1[b][0], links1[b][1]) for b in links1 if b not in links0)
    out["L_auto_audit"] = db.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='auto_link'").fetchone()[0]
    # two candidates ask; one wrong paper from a line settles nothing
    t1 = marg_bill("W454P2 TWIN PHARMA", "9001", D(3), 123400)
    t2 = marg_bill("W454P2 TWIN PHARMA", "9002", D(2), 123400)
    s_twin = scan("W454P2-T1", "W454P2 TWIN PHARMA", "X1", D(2), 1234.0, NOW - dt.timedelta(hours=3))
    one = marg_bill("W454P2 SOLO PHARMA", "8001", D(3), 567800)
    s_one = scan("W454P2-S1", "W454P2 SOLO PHARMA", "ZZ9", D(1), 5678.0, NOW - dt.timedelta(hours=3))
    line = marg_bill("W454P2 LINE PHARMA", "7001", TODAY.replace(day=1).isoformat(), 500000)   # a counted month: on reception's list
    s_wrong = scan("W454P2-W1", "W454P2 LINE PHARMA", "8888", D(1), 3210.0, NOW - dt.timedelta(hours=2))
    ver = marg_bill("W454P2 RAMA PHARMA", "A000777", D(5), 352800)
    s_ver = scan("W454P2-V1", "W454P2 RAMA PHARMA BAREILLY", "A000777", (TODAY.replace(year=TODAY.year - 1) - dt.timedelta(days=5)).isoformat(), 3534.0,
                 NOW - dt.timedelta(hours=1))
    pa._rematch(db, "W454P2 walk 2")
    lk = links()
    out["L_twin"] = [lk.get(t1), lk.get(t2)]
    out["L_one"] = lk.get(one)
    out["L_wrong"] = lk.get(line)
    out["L_ver"] = lk.get(ver)
    out["L_ids"] = dict(s_twin=s_twin, s_one=s_one, s_wrong=s_wrong, s_ver=s_ver)
    k = porders.scan_work(db)
    out["L_twin_asked"] = any(x["scan"] == s_twin for x in k["confirm"])
    # the line's intake link carries the supplier only
    setv("purchase.register_from", "2026-10-01")
    sl = [x for x in PS.scan_lines(db) if x.get("kind") == "marg"]
    out["Q_intake"] = [x["intake"] for x in sl if x.get("bill_id") == line][:1]
    # ---------------------------------------------------------------- Q  the questions (September is parked: read straight from scan_work)
    sept = {r[0] for r in db.execute("SELECT id FROM purchase_bill WHERE COALESCE(month, substr(bill_date,1,7))='2026-09'")}
    out["Q_amount"] = sorted(x["bill_id"] for x in k["amount"] if x["bill_id"] in sept)
    allq = {x.get("bill_id") for g in ("confirm", "amount") for x in k[g]}
    out["Q_date_misread_asked"] = [b for b in (bill_of("JANTA PHARMACEUTICALS", "19460"), bill_of("GUNINA PHARMACEUTICALS PVT LTD", "64906")) if b in allq]
    # ---------------------------------------------------------------- G  the register
    if NEW:
        R9 = SR.register(db, "2026-09")
        out["G_counts"] = dict(counts=R9["counts"], total=R9["total"], settled=R9["settled"], rows=len(R9["rows"]), states=sorted({r["state"] for r in R9["rows"]}),
                               ids=len({r["id"] for r in R9["rows"]}), n_bills=R9["n_bills"], scans=R9["scan_counts"])
        out["G_double"] = [r["bill_no"] for r in R9["rows"] if r["state"] == "double"]
        waiting = sorted(r["id"] for r in R9["rows"] if r["state"] == "amount_differs" and "waiting for reception" in r["note"])
        out["G_same"] = dict(register=waiting, questions=out["Q_amount"])
        s9 = SR.sarvam(db, "2026-09")
        out["G_sarvam"] = s9
    s, h = G("manoj", "/finance/purchase/page/scans?month=2026-09")
    t = text_of(h)
    out["G_page9"] = dict(status=s, verified=("Verified" in t), has_scan=("Has its scan" in t), parked=("is parked" in t), accept=("Accept without paper" in h),
                          hindi=[w for w in HINDI if w in (" " + t.lower() + " ")], settled=bool(re.search(r"\d+ of \d+ settled", t)),
                          ready=("Last 7 days:" in t), legacy=("old Scan links tables" in t))
    s, h = G("manoj", "/finance/purchase/page/scans?legacy=1")
    out["G_legacy"] = [s, "Scans with no Marg bill" in h]
    # accept / undo on a counted month
    oct_bill = marg_bill("W454P2 PAPER PHARMA", "6001", TODAY.replace(day=1).isoformat() if TODAY.day > 1 else TODAY.isoformat(), 111100)
    db.execute("INSERT OR IGNORE INTO s454_paper_missing (bill_id, by, at) VALUES (?,?,?)", (oct_bill, "shivani", NOW.isoformat()))
    db.commit()
    out["G_accept"] = dict(other=J("shavez", "/finance/purchase/api/s454/nopaper", {"bill": oct_bill, "accept": 1})[0])
    if NEW:
        out["G_accept"]["owner"] = J("manoj", "/finance/purchase/api/s454/nopaper", {"bill": oct_bill, "accept": 1})
        Rm = SR.register(db, TODAY.strftime("%Y-%m"))
        out["G_accept"]["state"] = next((r["state"] for r in Rm["rows"] if r["id"] == oct_bill), None)
        out["G_accept"]["undo"] = J("manoj", "/finance/purchase/api/s454/nopaper", {"bill": oct_bill, "accept": 0})[0]
        Rm = SR.register(db, TODAY.strftime("%Y-%m"))
        out["G_accept"]["state_after_undo"] = next((r["state"] for r in Rm["rows"] if r["id"] == oct_bill), None)
        b194 = bill_of("L.K. DRUG HOUSE", "75707")
        db.execute("INSERT OR IGNORE INTO s454_paper_missing (bill_id, by, at) VALUES (?,?,?)", (b194, "shivani", NOW.isoformat()))
        db.commit()
        out["G_accept"]["parked"] = J("manoj", "/finance/purchase/api/s454/nopaper", {"bill": b194, "accept": 1})[0]
        out["G_accept"]["audit"] = [r[0] for r in db.execute("SELECT action FROM purchase_audit WHERE action LIKE 's454_paper_accept%' ORDER BY id")]
    # ---------------------------------------------------------------- S  the Sarvam page; a parked month's amount answer on the register
    s, h = G("manoj", "/finance/purchase/page/sarvam?month=2026-09")
    out["S_page"] = dict(status=s, head=text_of(re.search(r'<div class="muted">(.*?)</div>', h, re.S).group(1)) if re.search(r'<div class="muted">(.*?)</div>', h, re.S) else "")
    b513 = bill_of("MANNAT PHARMA", "A000371")
    s513 = (links().get(b513) or (None,))[0]
    out["S_answer"] = dict(code=J("reception", "/finance/porders/api/s454/amount", {"scan": s513, "paper": "3528"})[0] if s513 else None)
    if NEW:
        R9b = SR.register(db, "2026-09")
        out["S_answer"]["state"] = next((r["state"] for r in R9b["rows"] if r["id"] == b513), None)
        out["S_answer"]["amir_fix"] = db.execute("SELECT COUNT(*) FROM purchase_bill WHERE id=? AND verdict='WRONG'", (b513,)).fetchone()[0]
    # ---------------------------------------------------------------- A  Amir
    s, h = G("amir", "/finance/amir/step/2")
    t = text_of(h)
    out["A_paper"] = dict(status=s, head=bool(re.search(r"Scan ho chuke bill \(\d+\)", t)), words=("Aap apne register se jaise daalte hain" in t),
                          grey=("reception ki jaanch mein" in t), old_head=("Marg mein daalne ke bill" in t), dl=("/finance/purchase/api/scan-file/" in h))
    s, h7 = G("amir", "/finance/amir/step/7")
    out["A_step7"] = dict(status=s, scan=("Scan ho chuke" in h7 or "scan-file" in h7))
    setv("purchase.entry_mode", "both")
    s, h = G("amir", "/finance/amir/step/2")
    t = text_of(h)
    out["A_both"] = dict(status=s, old_head=("Marg mein daalne ke bill" in t), new_head=("Scan ho chuke bill" in t))
    setv("purchase.entry_mode", "paper")
    out["A_digital"] = J("manoj", "/finance/porders/api/s454/setting", {"key": "purchase.entry_mode", "value": "digital"})
    out["A_setting_both"] = J("manoj", "/finance/porders/api/s454/setting", {"key": "purchase.entry_mode", "value": "both"})[0]
    J("manoj", "/finance/porders/api/s454/setting", {"key": "purchase.entry_mode", "value": "paper"})
    accts = [re.sub(r"\D", "", r[0] or "") for r in db.execute("SELECT acct_no FROM purchase_vendor_contact WHERE COALESCE(acct_no,'')<>''")]
    accts = [a for a in accts if len(a) >= 8]
    secrets_seen.extend(accts)
    ms = [r[0] for r in db.execute("SELECT DISTINCT month FROM purchase_neft_event ORDER BY month DESC LIMIT 2")]
    neft = {}
    for m in ms:
        s, b = GB("amir", "/finance/amir/pack/%s/neft" % m)
        neft[m] = dict(status=s, pdf=b[:5] == b"%PDF-", acct=any(a.encode() in b for a in accts))
    out["A_neft"] = neft
    # ---------------------------------------------------------------- V  Vendor payments
    seeded = "7" + "3" * 11
    secrets_seen.append(seeded)
    ins(db, "purchase_vendor_contact", dict(vendor_norm=pa.supplier_key("W454P2 BANK PHARMA"), vendor="W454P2 BANK PHARMA", phone="9" + "4" * 9,
                                            acct_no=seeded, ifsc="YESB0000001", acct_name="W454P2 BANK PHARMA", bank_status="VERIFIED"), replace=True)
    db.commit()
    month_pay = (ms[0] if ms else TODAY.strftime("%Y-%m"))
    pay_paths = ["/finance/purchase/page/pay", "/finance/purchase/page/pay/%s" % month_pay, "/finance/purchase/page/pay/%s/letter" % month_pay,
                 "/finance/purchase/page/pay/%s/advice.xlsx" % month_pay, "/finance/purchase/page/pay/%s/pack" % month_pay]
    open_paths = ["/finance/purchase/page/hub", "/finance/purchase/page/scans", "/finance/purchase/page/staff", "/finance/purchase/page/book",
                  "/finance/purchase/page/month/%s" % month_pay, "/finance/amir/step/2", "/finance/porders?old=1", "/finance/porders"]
    V = {}
    for u in ("amir", "darpan", "bhati", "reception", "shavez", "manoj"):
        codes = {}
        for p in pay_paths:
            s, b = GB(u, p)
            codes[p.rsplit("/", 1)[-1] if p.count("/") > 4 else "pay"] = s
        link, leak = False, []
        for p in open_paths:
            s, b = GB(u, p)
            if s == 200:
                if b'>Vendor payments</a>' in b:
                    link = True
                if seeded.encode() in b or b"YESB0000001" in b:
                    leak.append(p)
        V[u] = dict(codes=codes, link=link, leak=leak)
    out["V"] = V
    s, b = GB("darpan", "/finance/purchase/page/book")
    out["V_book_darpan"] = dict(status=s, last4=(("…" + seeded[-4:]).encode("utf-8") in b), full=(seeded.encode() in b))
    out["V_book_bank_edit"] = J("darpan", "/finance/purchase/api/book", {"action": "bank", "vendor": "W454P2 BANK PHARMA", "acct_no": "1", "ifsc": "X"})[0]
    tok = secrets.token_hex(24)
    secrets_seen.append(tok)
    setv("supplier_msg.phone_token", tok)
    r = fc.get("/finance/api/supplier-msg/next", base_url=BASE, headers={"X-Phone-Token": tok})
    out["V_phone"] = r.status_code
    # ---------------------------------------------------------------- D  manoj.returns_ok equals the owner's returns line
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    rq = next((x for x in dm["duties"] if x["id"] == "manoj.returns_ok"), {})
    if NEW:
        import amir_day                                                # noqa: E402
        amir_day._s454_returns_cache(db)
    nline = None
    for l in needs():
        m = re.match(r"^Counter returns waiting for your OK: (\d+)", l)
        if m:
            nline = int(m.group(1))
    try:
        rr = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True).execute(rq.get("due_sql") or "SELECT NULL").fetchone()
        nduty = int(rr[0] or 0) if rr else None
    except sqlite3.Error as e:
        nduty = "ERR %s" % e
    out["D_returns"] = dict(duty=nduty, owner_line=(nline or 0))
    # ---------------------------------------------------------------- N  what reaches a person (counted months only)
    os.environ["ORDER_TODAY"] = (TODAY.replace(day=1) + dt.timedelta(days=40)).replace(day=12).isoformat()   # the 12th of next month: a counted month
    T2 = dt.date.fromisoformat(os.environ["ORDER_TODAY"])
    for b_ in (line,):                                                 # the walk's own earlier rows leave reception's list (paper not found)
        db.execute("INSERT OR IGNORE INTO s454_paper_missing (bill_id, by, at) VALUES (?,?,?)", (b_, "shivani", NOW.isoformat()))
    db.commit()
    nb = marg_bill("W454P2 WAIT PHARMA", "5001", (T2 - dt.timedelta(days=5)).isoformat(), 222200, tag="n")
    ln = needs()
    s, h = G("shavez", "/finance/reports/aaj")
    out["N_line"] = dict(owner=[l for l in ln if l.startswith("Bill scan waiting")], shavez=("Bill scan baaki:" in text_of(h)), shavez_status=s)
    sc_n = scan("W454P2-N1", "W454P2 WAIT PHARMA", "5001", (T2 - dt.timedelta(days=5)).isoformat(), 2222.0, dt.datetime.combine(T2, dt.time(9, 0)))
    pa._rematch(db, "W454P2 walk N")
    ln = needs()
    s, h = G("shavez", "/finance/reports/aaj")
    out["N_after"] = dict(linked=bool(links().get(nb)), owner=[l for l in ln if l.startswith("Bill scan waiting")], shavez=("Bill scan baaki:" in text_of(h)))
    rs_ = scan("W454P2-R1", "KEDAR PHARMACEUTICAL", "W454P2-99", (T2 - dt.timedelta(days=9)).isoformat(), 77.0, dt.datetime.combine(T2 - dt.timedelta(days=9), dt.time(10, 0)))
    pa._rematch(db, "W454P2 walk R")
    ln = needs()
    s, h = G("amir", "/finance/amir/step/2")
    out["N_entry"] = dict(owner=[l for l in ln if l.startswith("Scanned and not yet in Marg")], amir_has_line=("for your eyes only" in h or "Scanned and not yet" in h),
                          amir_lists=("W454P2-R1" in h))
    if NEW:
        out["N_ready"] = list(SR.readiness(db))
    os.environ.pop("ORDER_TODAY", None)
    # ---------------------------------------------------------------- E  the staff-eye walk (DUTY_MAP v5 / v4)
    out["E"] = staff_eye(fc, BASE)
    blob = json.dumps(out, ensure_ascii=False, default=str)
    if any(x and x in blob for x in secrets_seen):
        print(TAG + json.dumps({"LEAK": True}))
        return
    print(TAG + blob)


def staff_eye(fc, BASE):
    """Sign in through the walk's own portal (its own secret and user store) as each login; render its home; for each of its duties whose due_sql
    says it is due, fetch the door and look for its marker (S444's model)."""
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


# ======================================================================= main
def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--por", "--db", "--adb", "--work", "--duty-map-new", "--duty-map-old"):
        ap.add_argument(k, required=True)
    ap.add_argument("--pictures", default="")
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
        fh.write("# W454P2 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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

    def run(side, fin, dmap):
        dbp, adbp = os.path.join(a.work, "w454p2_%s.db" % side), os.path.join(a.work, "w454p2_%s_assets.db" % side)
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, FINANCE_DB=dbp, ASSETS_DB=adbp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por,
                   CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret,
                   ORDER_PUSH_STUB=os.path.join(a.work, "push_%s.jsonl" % side), DUTY_MAP=dmap, REAL_DUTY_MAP=dmap, DUTY_MAP_JSON=dmap,
                   W454J=json.dumps(dict(pw=pw)), PORDERS_SOURCE="tables", PICTURES=a.pictures)
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
    N = run("new", a.fin_new, a.duty_map_new)
    O = run("old", a.fin_old, a.duty_map_old)
    check("both probes ran to the end (NEW the built files, OLD the box as it is); no key, phone or account number reached any output",
          N is not None and O is not None and not N.get("LEAK") and not O.get("LEAK"))
    if N is None or O is None or N.get("LEAK") or O.get("LEAK"):
        print("WALK_S454P2 RED -- a probe did not finish, or a seeded string reached its output")
        return 1
    print("-- R  the rules (scan_register)")
    rs = N["R_supplier"]
    check("supplier: 'PVT. LTD.', '(EXTN)', '&' against 'AND' and a trailing BAREILLY agree; another name differs",
          [rs["pvt"], rs["extn"], rs["amp"], rs["bly"], rs["other"]] == ["agree", "agree", "agree", "agree", "differ"], rs)
    check("a 'P' inside a name is kept, a standalone P / PVT / LTD / CO / M/S dropped: %s" % rs["p_inside"],
          rs["p_inside"] == ["JP PHARMA", "A PHARMA", "W454P2 PHARMA"], rs["p_inside"])
    check("the shop's own name and a heading ('WHOLE SALE CHEMIST & DRUGGIST') are never a supplier: not read", rs["shop"] == "not_read" and rs["heading"] == "not_read", rs)
    rb = N["R_billno"]
    check("bill number: a printed number with its series and year, a prefix, a run inside brackets agree with Marg's short number; Marg's own zeros dropped",
          [rb["series"], rb["prefix"], rb["tail"], rb["marg_zeros"]] == ["agree"] * 4, rb)
    check("bill number: a licence-shaped reading agrees with nothing; a misread number differs; the financial year is never the number; empty = not read",
          [rb["licence"], rb["dl"], rb["wrong"], rb["fy_only"], rb["empty"]] == ["differ", "differ", "differ", "differ", "not_read"], rb)
    check("date: a wrong year agrees (day and month), a wrong month differs", N["R_date"] == dict(year="agree", month="differ", none="not_read"), N["R_date"])
    st = N["R_states"]
    check("states: a wrong month with supplier, number and total agreeing is Verified; a misread number with the rest agreeing Has its scan; Rs 6 off agrees "
          "(noise); Rs 243 off is Amount differs; no total read Has its scan",
          st["month_wrong"][0] == "verified" and st["number_misread"][0] == "has_scan" and st["rs6"][0] == "verified" and st["rs6"][4] == "noise"
          and st["rs243"][0] == "amount_differs" and st["no_total"][0] == "has_scan" and st["shop_and_date"][0] == "has_scan", st)
    print("-- L  the matcher on September's real data (scratch copy)")
    check("every link that existed before the pass exists after it", N["L_kept"] == [] and O["L_kept"] == [], [N["L_kept"], O["L_kept"]])
    auto = [x for x in N["L_new"] if x[2] == "AUTO"]
    check("the auto-link pairs September's four papers with the ONE unscanned bill of their supplier and amount (audited auto_link): %s" % auto,
          len(auto) == 4 and N["L_auto_audit"] >= 4, N["L_new"])
    check("NEGATIVE: the box as it is pairs none of them", not [x for x in O["L_new"] if x[0] in {y[0] for y in auto}], O["L_new"])
    check("one candidate pairs by itself (W454P2 SOLO); two candidates of the same amount (W454P2 TWIN) pair with neither and ask 'is this the bill?'",
          N["L_one"] and N["L_one"][1] == "AUTO" and N["L_twin"] == [None, None] and N["L_twin_asked"], [N["L_one"], N["L_twin"], N["L_twin_asked"]])
    check("a wrong paper scanned from a line (the line's supplier carried, its own number and amount read) does not settle that line's bill",
          N["L_wrong"] is None, N["L_wrong"])
    check("a scan reading the supplier with BAREILLY, Marg's number, the date a year off and the total Rs 6 off is paired as Verified by the matcher",
          N["L_ver"] and N["L_ver"][1] == "EXACT", N["L_ver"])
    check("the intake link of a Marg bill's line carries that line's supplier only (no bill number, no amount)",
          N["Q_intake"] and "vendor=" in N["Q_intake"][0] and "bill_no=" not in N["Q_intake"][0] and "amount=" not in N["Q_intake"][0], N["Q_intake"])
    check("NEGATIVE: the box as it is carries the bill number and the amount in it", O["Q_intake"] and "bill_no=" in O["Q_intake"][0], O["Q_intake"])
    print("-- Q  the questions")
    check("September's 'the amount differs' questions, beyond the noise: %s" % N["Q_amount"], set(O["Q_amount"]) < set(N["Q_amount"]) and len(N["Q_amount"]) == 6,
          dict(new=N["Q_amount"], old=O["Q_amount"]))
    check("a paired scan whose date (JANTA 19460, GUNINA 64906) was read differently makes no card", N["Q_date_misread_asked"] == [], N["Q_date_misread_asked"])
    print("-- G  the month's register (September, parked)")
    g = N["G_counts"]
    check("the head's figures add up to the month's rows (%d bills in Marg, the double entry one row); every bill in exactly one state: %s"
          % (g["n_bills"], json.dumps(g["counts"])), sum(g["counts"].values()) == g["total"] == g["rows"] == g["ids"] and g["n_bills"] == g["total"] + 1, g)
    check("Verified and Has its scan counted apart; '%d of %d settled'" % (g["settled"], g["total"]),
          g["counts"]["verified"] > 0 and g["counts"]["has_scan"] > 0 and g["settled"] == g["counts"]["verified"] + g["counts"]["has_scan"] + g["counts"]["accepted"], g)
    check("a bill entered twice in Marg is one row: %s" % N["G_double"], len(N["G_double"]) == 1 and " and " in N["G_double"][0], N["G_double"])
    check("the same bill reads the same on every page: the register's 'Amount differs, waiting for reception' = the questions' 'the amount differs'",
          N["G_same"]["register"] == N["G_same"]["questions"], N["G_same"])
    pg = N["G_page9"]
    check("the page: Verified and Has its scan, '... settled', 'Last 7 days', headed as parked, no accept tap, no Roman Hindi; the old tables one link away",
          pg["status"] == 200 and pg["verified"] and pg["has_scan"] and pg["settled"] and pg["ready"] and pg["parked"] and not pg["accept"] and not pg["hindi"]
          and pg["legacy"] and N["G_legacy"] == [200, True], [pg, N["G_legacy"]])
    check("NEGATIVE: the box as it is has no register (no Verified / Has its scan, no settled line)", not O["G_page9"]["settled"] and not O["G_page9"]["has_scan"], O["G_page9"])
    ga = N["G_accept"]
    check("a counted month's 'paper not found': another login is refused; the owner's tap settles the row (Accepted without paper), Undo brings it back "
          "(both audited); a parked month has no accept",
          ga["other"] == 403 and ga["owner"][0] == 200 and ga["state"] == "accepted" and ga["undo"] == 200 and ga["state_after_undo"] == "no_scan"
          and ga["parked"] == 409 and ga["audit"] == ["s454_paper_accepted", "s454_paper_accept_undone"], ga)
    print("-- S  the Sarvam counter")
    s9 = N["G_sarvam"]
    check("the Sarvam page's head counts by the rules (supplier misread %d · bill no. %d · date %d · total %d on %d linked bills) -- the register's foot gives "
          "the same" % (s9["misses"]["supplier"], s9["misses"]["billno"], s9["misses"]["date"], s9["misses"]["total"], s9["n"]),
          N["S_page"]["status"] == 200 and ("supplier misread %d" % s9["misses"]["supplier"]) in N["S_page"]["head"]
          and ("total misread %d" % s9["misses"]["total"]) in N["S_page"]["head"], N["S_page"])
    check("a parked month's amount answer (MANNAT A000371: the paper reads Rs 3,528) is recorded on the register only: the row turns Verified, nothing for Amir",
          N["S_answer"]["code"] == 200 and N["S_answer"]["state"] == "verified" and N["S_answer"]["amir_fix"] == 0, N["S_answer"])
    print("-- A  Amir")
    ap_ = N["A_paper"]
    check("purchase.entry_mode = paper: step 2 reads 'Scan ho chuke bill (N)' with its words, the downloads, no grey line; step 7 lists no scan",
          ap_["status"] == 200 and ap_["head"] and ap_["words"] and not ap_["grey"] and not ap_["old_head"] and not N["A_step7"]["scan"], [ap_, N["A_step7"]])
    check("NEGATIVE: the box as it is reads 'Marg mein daalne ke bill'", O["A_paper"]["old_head"] and not O["A_paper"]["head"], O["A_paper"])
    check("on both: S452's words return", N["A_both"]["old_head"] and not N["A_both"]["new_head"], N["A_both"])
    check("'digital' is refused with its line; 'both' is accepted", N["A_digital"][0] == 400 and "not built" in (N["A_digital"][1].get("message") or "")
          and N["A_setting_both"] == 200, N["A_digital"])
    check("his paid NEFT sheet holds no account number (%s)" % ", ".join("%s: %s" % (k, v["status"]) for k, v in N["A_neft"].items()),
          all(not v["acct"] for v in N["A_neft"].values()) and N["A_neft"] == O["A_neft"], N["A_neft"])
    print("-- V  Vendor payments: the owner and Shavez only")
    V = N["V"]
    staff = ("amir", "darpan", "bhati", "reception")
    check("as amir, darpan, bhati and the reception login: the page, the month, the letter, the advice and the pack refuse (403 -- or 302, the login "
          "gate's own answer to a login with no purchase access at all)", all(set(V[u]["codes"].values()) <= {302, 401, 403} for u in staff), {u: V[u]["codes"] for u in staff})
    check("no link to Vendor payments on any page they open; no page they can open holds the seeded account number or IFSC",
          not any(V[u]["link"] for u in staff) and not any(V[u]["leak"] for u in staff), {u: (V[u]["link"], V[u]["leak"]) for u in staff})
    check("as shavez and the owner: the pages open as before (the link is there)", all(V[u]["link"] and V[u]["codes"]["pay"] in (200, 302) for u in ("shavez", "manoj"))
          and V["manoj"]["codes"] == O["V"]["manoj"]["codes"], {u: V[u] for u in ("shavez", "manoj")})
    check("NEGATIVE: the box as it is opens them to the staff", any(set(O["V"][u]["codes"].values()) - {403} for u in staff), {u: O["V"][u]["codes"] for u in staff})
    check("the phone book shows Darpan the account's last four digits and no IFSC, and refuses him a bank edit", N["V_book_darpan"]["status"] == 200
          and N["V_book_darpan"]["last4"] and not N["V_book_darpan"]["full"] and N["V_book_bank_edit"] == 403, [N["V_book_darpan"], N["V_book_bank_edit"]])
    check("the reception phone's keyed queue answers as before", N["V_phone"] == O["V_phone"] == 200, [N["V_phone"], O["V_phone"]])
    print("-- D  the duty")
    check("manoj.returns_ok reads the owner's own returns line: %s" % N["D_returns"], N["D_returns"]["duty"] == N["D_returns"]["owner_line"], N["D_returns"])
    check("NEGATIVE: on the box as it is the duty and the owner's line differ", O["D_returns"]["duty"] != O["D_returns"]["owner_line"], O["D_returns"])
    print("-- N  what reaches a person")
    check("a counted bill 5 days unscanned: the owner reads 'Bill scan waiting', Shavez's page 'Bill scan baaki'; both gone once its scan pairs",
          N["N_line"]["owner"] and N["N_line"]["shavez"] and N["N_after"]["linked"] and not N["N_after"]["owner"] and not N["N_after"]["shavez"], [N["N_line"], N["N_after"]])
    check("a read scan not in Marg after 9 days: the owner's line (for his eyes only); Amir's pages carry no new line",
          N["N_entry"]["owner"] and not N["N_entry"]["amir_has_line"], N["N_entry"])
    check("'Last 7 days' counts: %s (bills entered · scan before the entry · paired with no tap)" % N.get("N_ready"), isinstance(N.get("N_ready"), list)
          and N["N_ready"][0] >= N["N_ready"][1] >= 0 and N["N_ready"][0] >= N["N_ready"][2] >= 0, N.get("N_ready"))
    print("-- E  the staff-eye walk (DUTY_MAP v5)")
    E = N["E"]
    bad = []
    for who, v in E.items():
        for d in v["duties"]:
            if d.get("tile") and d.get("tile_seen") is False:
                bad.append("%s tile %s not on the home" % (who, d["tile"]))
            if isinstance(d.get("due_n"), str):
                bad.append("%s %s: %s" % (who, d["id"], d["due_n"]))
            if d.get("door_seen") is False:
                bad.append("%s %s due (%s) but its door marker is not on the door" % (who, d["id"], d["due_n"]))
    check("every login's tiles are on its home, every due duty's marker on its door (reception, darpan, shavez, amir, the owner)", not bad,
          bad or {w: [(d["id"], d["due_n"], d.get("door_seen")) for d in v["duties"] if d.get("due_n")] for w, v in E.items()})
    print("WALK_S454P2 %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:900]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
