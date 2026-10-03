#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p1.py -- kit S454_BILL_REGISTER, part 1. THE REAL finance app (and the real portal and asset app, for the staff-eye walk and the
re-lane) over SCRATCH COPIES of finance.db, assets.db and the spine (backup API), through Flask's test clients, one process per run:

  A  (new)  the order sheet's road and the reception screen: the converted sample through the scratch door, its load, a refused sheet, a
            second sheet, the comparison, Order karna hai (Order ho gaya, Kholiye / Call, WhatsApp through the phone's queue, its
            withdrawal, a quantity, an old line ordered again), the reminder, the freeze, order.source = system, the orthotic card, the
            printed sheet, Darpan's card, the owner's cards and settings, the staff-eye walk, the pictures of the screens the mock lacks.
  C  (new)  the first load "as already ordered", Marg's clearing, a lapse, the old lines' visibility, the bill-scan tie, the arrival
            screen, Bill scan karna hai, the questions (Photo dekh kar bataiye), the unread paper (S454 4.7), September parked.
  O  (old)  the NEGATIVE CONTROL: the same inputs on the box as it is.
Its own rows are keyed W454 (crafted suppliers 'W454 ... PHARMA', scans stamped 'W454-..', a Marg export 'W454...'); the sample sheet of
02-Oct (the repository's, phone numbers blanked) is moved so that its newest date is yesterday; every date is computed from today. No phone
number reaches the walk's output (a run of ten digits is masked by the installer too; the walk stops red if a key string reaches it).

  --fin-new DIR --fin-old DIR --marg-new DIR --marg-old DIR --por DIR --ast DIR --shared DIR --db PATH --adb PATH --spine PATH --kit DIR
  --duty-map PATH --uploads DIR --reader-new FILE --reader-old FILE [--pictures DIR]
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import time

TODAY = dt.date.today()
NOW = dt.datetime.now().replace(microsecond=0)
USERS = {"reception": "staff", "darpan": "staff", "shavez": "manager", "amir": "staff", "manoj": "doctor", "shivani": "staff"}
WHO = {"Cookie": "clinic_who=shivani"}
W454 = "W454"


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


def ddmm(iso):
    return "%s-%s" % (iso[8:10], iso[5:7])


def mask(s):
    s = re.sub(r"\+?\d[\d\s-]{8,}\d", lambda m: "#" * 10 if len(re.sub(r"\D", "", m.group(0))) >= 10 else m.group(0), str(s))
    return s


def ins(con, table, row, replace=False):
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    return con.execute("INSERT %sINTO %s (%s) VALUES (%s)" % ("OR REPLACE " if replace else "", table, ", ".join(cols), ", ".join("?" * len(cols))),
                       [row[c] for c in cols]).lastrowid


def load_reader(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ the sheets the walk feeds the door
def shifted(raw_text, newest_to):
    """The sample with every dd-mm-2026 moved by one delta so that its newest date (02-10-2026) becomes newest_to."""
    delta = newest_to - dt.date(2026, 10, 2)
    return re.sub(r"(\d\d)-(\d\d)-(2026)", lambda m: (dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) + delta).strftime("%d-%m-%Y"), raw_text)


def sample2(t1, newest):
    """The first sheet reprinted, with ONE new entry under KEDAR (an item no stock list carries): the subtotal and the TOTAL follow."""
    d = newest.strftime("%d-%m-%Y")
    line = "  W454 ZZTEST TAB       1*10     OP-0332   %s      10:0         -      10:0    10.00     100\n" % d
    a = "  RANIMIG 150           1*30     OP-0326   %s      10:0         -      10:0    33.60     336\n" % d
    assert t1.count(a) == 1
    t = t1.replace(a, a + line)
    t = t.replace("                                                           1020      1020             3996\n",
                  "                                                           1120      1120             4096\n")
    t = t.replace("TOTAL                                                      4046      4046            41226\n",
                  "TOTAL                                                      4146      4146            41326\n")
    return t


def tiny_sheet(supplier, items, sheet_date):
    """A one-supplier sheet in Marg's own layout: items = [(name, packing, entry, date_iso, qty_raw)] with plain whole quantities."""
    out = ["", "                               SANJEEVNI MEDICOS", "", "                            PENDING ORDERS (PURCHASE)", "-" * 132,
           "  ITEM NAME                      ENTRY NO.    DATED   ORDER QTY   RECEIVE   PENDING     RATE   VALUE  DUEDT  PARTY ORDER NO.", "-" * 132, "",
           "%s Ph." % supplier]
    tu = tv = 0
    for name, pack, entry, diso, q in items:
        dd = "%s-%s-%s" % (diso[8:10], diso[5:7], diso[:4])
        out.append("  %-21s %-8s %-9s %s %9s %9s %9s %8s %7s" % (name, pack, entry, dd, q, "-", q, "10.00", "%d" % (int(q) * 10)))
        tu += int(q)
        tv += int(q) * 10
    if len(items) > 1:
        out += [" " * 51 + "-" * 66, " " * 51 + "%13d %9d %16d" % (tu, tu, tv), " " * 51 + "-" * 66]
    out += ["-" * 132, "TOTAL" + " " * 54 + "%d %9d %16d" % (tu, tu, tv), "-" * 132, "*** End of Report ***", "", ""]
    _ = sheet_date
    return "\n".join(out)


# ======================================================================= the PROBE (one process per run)
def probe():
    MODE = os.environ["MODE"]
    NEW = MODE in ("A", "C")
    FIN, POR, MRG = os.environ["FINDIR"], os.environ["PORDIR"], os.environ["MARGDIR"]
    W = json.loads(os.environ["W454J"])
    for p in (POR, FIN, MRG):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import marg_ingest                                                 # noqa: E402,F401 -- the scratch copies first
    import marg_router                                                 # noqa: E402,F401
    import marg_take as MT                                             # noqa: E402
    assert MT.__file__.startswith(MRG), MT.__file__
    MT._Lock.__init__.__defaults__ = (os.path.join(os.environ["WALKDIR"], "marg.lock"), None)   # walk-only: never the live collector's lock
    import finance_app as fa                                           # noqa: E402
    import purchase_app as pa                                          # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    adb = sqlite3.connect(os.environ["ASSETS_DB"], timeout=60)
    adb.row_factory = sqlite3.Row
    q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]   # noqa: E731
    out = {}
    keys_seen = []

    def H(u, extra=None):
        h = {"X-Clinic-User": u, "X-Clinic-Role": ""}
        if u == "reception":
            h.update(WHO)
        if extra:
            h.update(extra)
        return h

    def G(u, p):
        r = fc.get(p, base_url=BASE, headers=H(u))
        return r.status_code, r.get_data(as_text=True), r

    def J(u, p, body=None):
        r = fc.post(p, base_url=BASE, headers=H(u), json=body if body is not None else {})
        return r.status_code, (r.get_json(silent=True) or {})

    def text(h):
        h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h or "", flags=re.S)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'").strip()

    def needs():
        return [l.get("text", "") for l in J("manoj", "/finance/sanjeevni/api/needs-you")[1].get("lines") or []] if False else \
            [l.get("text", "") for l in (fc.get("/finance/sanjeevni/api/needs-you", base_url=BASE, headers=H("manoj")).get_json(silent=True) or {}).get("lines") or []]

    def take(raw, name, src="push"):
        r = MT.take(raw, name=name, source=src, db=os.environ["FINANCE_DB"], archive=os.path.join(MRG, "archive"))
        return dict(status=r["status"], type=r["type"], verdict=r["verdict"], reason=(r["reason"] or "")[:160], md5=r["md5"])

    def stamp_name(md5):
        return "MEDICAL__%s__report_TXT__%s.XLS" % (dt.datetime.now().strftime("%Y%m%d-%H%M%S"), md5[:8])

    def export_md5():
        md5 = "w454" + hashlib.md5(("bw454" + MODE).encode()).hexdigest()[:28]
        if not db.execute("SELECT 1 FROM purchase_export WHERE md5=?", (md5,)).fetchone():
            ins(db, "purchase_export", dict(md5=md5, type="ITEMWISE", file="W454 walk", period_from=D(60), period_to=TODAY.isoformat(),
                                            export_stamp=NOW.strftime("%Y%m%d-%H%M%S"), received_at=NOW.isoformat(), n_rows=1, grand_amount_p=0), replace=True)
            db.commit()
        return md5

    def marg_line(supplier, item, date_iso, qty=10, bill_no=None):
        md5 = export_md5()
        sn = pa.supplier_key(supplier)
        ins(db, "purchase_line", dict(supplier_norm=sn, bill_no=bill_no or ("W454-%s" % secrets.token_hex(3)), bill_date=date_iso, month=date_iso[:7],
                                      item=item, packing="1*10", qty=qty, free=0, rate_p=1000, amount_p=qty * 1000, direction="PURCHASE", source_md5=md5,
                                      line_type="ITEMWISE"))
        db.commit()

    def marg_bill(supplier, bill_no, date_iso, amount_p):
        md5 = export_md5()
        bid = ins(db, "purchase_bill", dict(supplier_norm=pa.supplier_key(supplier), supplier=supplier, bill_no=bill_no, bill_date=date_iso, month=date_iso[:7],
                                            cash_p=0, credit_p=amount_p, amount_p=amount_p, source_md5=md5, bw_md5=md5, bw_amount_p=amount_p, date_src="BILLWISE"))
        db.commit()
        return bid

    def scan(stamp, vendor, bill_no, bill_date, amount, at, ocr="read", month=None, lane="pharmacy"):
        """A crafted pharmacy scan in the scratch asset store: submitted_at in IST, created_at in UTC (the asset app's own conventions)."""
        sid = ins(adb, "bills", dict(kind="Pharmacy" if lane == "pharmacy" else "Consumable", vendor=vendor, bill_no=bill_no, bill_date=bill_date,
                                     total_amount=amount, notes="W454 walk", created_at=(at - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                                     submitted_at=at.strftime("%Y-%m-%d %H:%M"), stamp_no=stamp, status="captured" if lane == "pharmacy" else "draft",
                                     ocr_status=ocr, lane=lane, source_stored="w454_%s.pdf" % stamp, source_orig="w454", submitted_by="W454 walk",
                                     bill_month=month or at.strftime("%Y-%m")))
        adb.commit()
        return sid

    def tok():
        r = db.execute("SELECT value FROM setting WHERE key='supplier_msg.phone_token'").fetchone()
        v = r[0] if r else ""
        if v and v not in keys_seen:
            keys_seen.append(v)
        return v

    def phone(path, body=None):
        h = {"X-Phone-Token": tok()}
        r = fc.post(path, base_url=BASE, headers=h, json=body) if body is not None else fc.get(path, base_url=BASE, headers=h)
        return r.status_code, (r.get_json(silent=True) or {})

    def setv(key, value):
        db.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        db.commit()

    reader = load_reader(os.environ["READER_NEW"], "mt_new")
    base_text = reader.ORDER_SAMPLE.decode("latin-1")
    S1 = shifted(base_text, TODAY - dt.timedelta(days=1)).encode("latin-1")
    x1 = reader.convert(S1)[0]
    if MODE == "O":
        out.update(o_probe(G, J, take, x1, stamp_name, q, db, adb, scan, phone, tok, needs, text, fa, pa, W))
    elif MODE == "A":
        out.update(a_probe(G, J, take, x1, S1, reader, stamp_name, q, db, adb, scan, phone, tok, needs, text, marg_line, marg_bill, setv, W, fc, BASE, H))
    else:
        out.update(c_probe(G, J, take, S1, reader, stamp_name, q, db, adb, scan, needs, text, marg_line, marg_bill, setv, W, fc, BASE, H, pa))
    blob = json.dumps(out, ensure_ascii=False, default=str)
    if any(k and k in blob for k in keys_seen):
        print("W454JSON " + json.dumps({"LEAK": True}))
        return
    print("W454JSON " + blob)


# ----------------------------------------------------------------------- the negative control: the box as it is
def o_probe(G, J, take, x1, stamp_name, q, db, adb, scan, phone, tok, needs, text, fa, pa, W):
    out = {"amir0": _amir_rows(G, pa, db)}
    s, h, _r = G("reception", "/finance/porders")
    out["home_is_old"] = [s, 'id="sub"' in h, "Aaj ka kaam" in h]
    out["take"] = take(x1, stamp_name(hashlib.md5(x1).hexdigest()))
    out["has_table"] = bool(db.execute("SELECT 1 FROM sqlite_master WHERE name='order_sheet'").fetchone())
    out["scan_needs"] = [t for t in needs() if t.startswith("Bill scan pending on")]
    t1 = phone("/finance/api/supplier-msg/next")
    t2 = phone("/finance/api/supplier-msg/next")
    out["next_twice"] = [t1[0], t2[0], bool(t1[1].get("id")) and t1[1].get("id") == t2[1].get("id")]
    sid = scan("W454-O1", "W454 OLD PHARMA", None, None, None, dt.datetime.now() - dt.timedelta(minutes=30), ocr="empty", month=TODAY.strftime("%Y-%m"))
    pa._rematch(db, "W454 walk")
    import porders                                                     # noqa: PLC0415
    k = porders.scan_work(db)
    out["old_wait_note"] = any("manager isse theek karega" in (x.get("note") or "") for x in k["wait"] if x["scan"] == sid)
    out["old_amir_has_unread"] = sid in [x["id"] for x in pa.scans_for_amir(db)["list"]] or sid in [x["id"] for x in pa.scans_for_amir(db)["held"]]
    out["old_amir_list_unread"] = sid in [x["id"] for x in pa.scans_for_amir(db)["list"]]
    import order_rules                                                 # noqa: PLC0415
    n0 = _stub_lines()
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(12, 0)))
    out["old_noon_push"] = _stub_lines() - n0
    s, j, _r = G("darpan", "/finance/darpan/kal/api/day")
    out["old_darpan_has_sheet"] = "order_sheet" in (json.loads(j) if isinstance(j, str) and j.startswith("{") else {})
    return out


def _stub_lines():
    p = os.environ.get("ORDER_PUSH_STUB", "")
    try:
        return sum(1 for _ in open(p, encoding="utf-8"))
    except OSError:
        return 0


def _stub_texts():
    p = os.environ.get("ORDER_PUSH_STUB", "")
    try:
        return [json.loads(l)["payload"]["body"] for l in open(p, encoding="utf-8")]
    except OSError:
        return []


def _save(name, html):
    d = os.environ.get("PICTURES", "")
    if not d:
        return
    os.makedirs(d, exist_ok=True)
    h = re.sub(r"(tel:)[+\d]+", r"\1##########", html)
    h = re.sub(r"\d{5} ?\d{5}", "#####-#####", h)
    h = re.sub(r"<script>window.WHO_SHARED.*?</script><script>/\* S441.*?</script>", "", h, flags=re.S)
    with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
        fh.write("<!-- S454 part 1 walk picture (scratch data, phone numbers masked): %s -->\n" % name + h)


# ----------------------------------------------------------------------- A: the sheet and the order screen
def a_probe(G, J, take, x1, S1, reader, stamp_name, q, db, adb, scan, phone, tok, needs, text, marg_line, marg_bill, setv, W, fc, BASE, H):
    import order_sheet as OS                                           # noqa: PLC0415
    import order_sheet_pdf as OP                                       # noqa: PLC0415
    import porders                                                     # noqa: PLC0415
    import order_rules                                                 # noqa: PLC0415
    import supplier_msg                                                # noqa: PLC0415
    import purchase_app as pa                                          # noqa: PLC0415
    out = {"amir0": _amir_rows(G, pa, db)}
    # ---- the road: the door takes the converted sheet; the loader runs at once
    m1 = hashlib.md5(x1).hexdigest()
    out["take1"] = take(x1, stamp_name(m1))
    out["sheet1"] = q("SELECT n_lines, n_new, n_old, n_known, n_suppliers, units_total, newest_date FROM order_sheet WHERE md5=?", m1)
    out["lines1"] = q("SELECT kind, state, COUNT(*) n, COUNT(DISTINCT supplier_norm) s FROM order_sheet_line GROUP BY kind, state")
    out["ravi"] = [r["item_printed"] for r in q("SELECT item_printed FROM order_sheet_line WHERE supplier_norm='RAVI MEDICAL AGENCY' ORDER BY id")]
    out["knee"] = q("SELECT item_printed, packing, entry_no, kind FROM order_sheet_line WHERE item_printed LIKE 'KNEE IMMOB%'")
    out["krishna"] = q("SELECT item_printed FROM order_sheet_line WHERE supplier_norm='KRISHNA MEDICOS'")
    n_before = q("SELECT COUNT(*) n FROM order_sheet_line")[0]["n"]
    time.sleep(1.1)
    out["take1_again"] = take(x1, stamp_name(m1))
    out["load_twice_adds"] = q("SELECT COUNT(*) n FROM order_sheet_line")[0]["n"] - n_before
    out["notice1"] = [t for t in _stub_texts() if t.startswith("Darpan ki order sheet aa gayi")]
    # a sheet whose heads were altered: the router refuses it; Darpan's card says "adhoori"
    rows = reader.order_rows(S1)
    rows[1][3] = "PACK"
    bad = reader.ole2(reader.workbook_stream(rows))
    time.sleep(1.1)
    out["take_bad"] = take(bad, stamp_name(hashlib.md5(bad).hexdigest()))
    s, b, _r = G("darpan", "/finance/darpan/kal/api/day")
    out["darpan_bad"] = (json.loads(b) if s == 200 else {}).get("order_sheet")
    out["owner_refused_line"] = [t for t in needs() if t.startswith("Darpan's order sheet refused today")]
    # an old line Marg has since supplied: "aa chuka dd-mm"; the others "nahi aaya"
    xg = q("SELECT * FROM order_sheet_line WHERE item_printed='XGESIC LA'")[0]
    supplied = (dt.date.fromisoformat(xg["line_date"]) + dt.timedelta(days=2)).isoformat()
    marg_line("DRUG DEAL BAREILLY", "XGESIC LA", supplied, 20)
    OS.refresh(db)
    olds = OS.old_lines(db)
    out["old_words"] = {l["item_printed"]: OS.old_word(l) for l in olds}
    out["xg_supplied"] = ddmm(supplied)
    # the second sheet: the first reprinted plus one new entry -- only that line is new; its name resolves to nothing
    t2 = sample2(S1.decode("latin-1"), TODAY - dt.timedelta(days=1)).encode("latin-1")
    x2 = reader.convert(t2)[0]
    time.sleep(1.1)
    out["take2"] = take(x2, stamp_name(hashlib.md5(x2).hexdigest()))
    out["sheet2"] = q("SELECT n_lines, n_new, n_old, n_known, unresolved FROM order_sheet WHERE md5=?", hashlib.md5(x2).hexdigest())
    out["notice2"] = [t for t in _stub_texts() if t.startswith("Darpan ki order sheet aa gayi")]
    s, b, _r = G("darpan", "/finance/darpan/kal/api/day")
    jd = json.loads(b) if s == 200 else {}
    out["darpan_ok"] = jd.get("order_sheet")
    out["darpan_line"] = jd.get("orders_today")
    out["unresolved_line"] = [t for t in needs() if "not found in Marg's stock list" in t]
    out["cmp1"] = json.loads(q("SELECT cmp FROM order_sheet WHERE md5=?", m1)[0]["cmp"] or "{}")
    # ---- the home
    s, h, _r = G("reception", "/finance/porders")
    out["home"] = dict(status=s, rows=re.findall(r'<a class="row" id="row_(\w+)"[^>]*><span class="n">(\d+)</span><span class="l">([^<]+)</span>', h),
                       scan_btn='id="scannew"' in h and "/scanapp/intake?lane=pharmacy" in h, purana=re.findall(r'id="park_([\d-]+)"', h),
                       oldpage='id="oldpage"' in h, alldone='id="alldone"' in h)
    _save("01_home_reception.html", h)
    out["home_shavez_oldlink"] = 'id="oldpage"' in G("shavez", "/finance/porders")[1]
    out["home_darpan_oldlink"] = 'id="oldpage"' in G("darpan", "/finance/porders")[1]
    s, h, _r = G("manoj", "/finance/porders")
    out["home_owner_en"] = ["Today's work" in h, "Aaj ka kaam" not in h, 'id="oldpage"' in h]
    _save("10_home_owner_english.html", h)
    st = J("reception", "/finance/porders/api/s454/state")[1] if False else json.loads(G("reception", "/finance/porders/api/s454/state")[1])
    out["state0"] = st
    # ---- the printed sheet, before anything is ordered (the orthotic keeps set to 0 on this copy for one page: walk-only data)
    keep0 = q("SELECT item, keep, source FROM porder_keep")
    db.execute("UPDATE porder_keep SET keep=0, source='owner'")
    db.commit()
    setv("order.sheet_print_old", "0")
    r = fc.get("/finance/porders/s454/sheet.pdf", base_url=BASE, headers=H("reception"))
    pdf0 = r.data
    lay0 = OP.layout(db)
    txt0 = OP.text_of(pdf0)
    sheet_new = q("SELECT item, qty_raw FROM order_sheet_line WHERE kind='new' AND state='to_order'")
    out["pdf0"] = dict(status=r.status_code, ctype=r.headers.get("Content-Type"), pages=pdf0.count(b"/Type /Page "), lay_pages=len(lay0["pages"]),
                       old_rows=sum(1 for b in lay0["blocks"] for x in b["rows"] if x["old"]),
                       all_items=all(any(x["item"] == t for t in txt0) for x in sheet_new),
                       all_qty=all(any(OS.qty_text(x["qty_raw"]) == t for t in txt0) for x in sheet_new),
                       ravi_nonum=any(t == "Ph. (number nahi hai)" for t in txt0), heads=sum(1 for t in txt0 if t == "Kam aaya / nahi aaya"),
                       foot=any(t.startswith("Order kisne kiya:") for t in txt0))
    setv("order.sheet_print_old", "1")
    r = fc.get("/finance/porders/s454/sheet.pdf", base_url=BASE, headers=H("reception"))
    pdf1 = r.data
    lay1 = OP.layout(db)
    txt1 = OP.text_of(pdf1)
    old_rows = [x for b in lay1["blocks"] for x in b["rows"] if x["old"]]
    new_rows = [x for b in lay1["blocks"] for x in b["rows"] if not x["old"]]
    blocks_per_page = [i for p in lay1["pages"] for i in p]
    out["pdf1"] = dict(pages=pdf1.count(b"/Type /Page "), old_rows=len(old_rows), old_tags=sum(1 for x in old_rows if x["tag"].startswith("purana, ")
                                                                                                and ("aa chuka" in x["tag"] or "nahi aaya" in x["tag"])),
                       order_boxes=pdf1.count(b"% col-order"), aaya_boxes=pdf1.count(b"% col-aaya"), new_rows=len(new_rows),
                       split=(sorted(blocks_per_page) != list(range(len(lay1["blocks"])))), only_old=lay1["first_only"] is not None,
                       sirf=any(t == "Sirf purane pending" for t in txt1), tag_in_text=any(t.startswith("purana, ") for t in txt1))
    with open(os.path.join(os.environ["WALKDIR"], "order_sheet_walk.pdf"), "wb") as fh:
        fh.write(pdf1)
    for k in keep0:
        db.execute("UPDATE porder_keep SET keep=?, source=? WHERE item=?", (k["keep"], k["source"], k["item"]))
    db.commit()
    # ---- Order karna hai: the list, a card, Order ho gaya (twice)
    out["phone_line_before"] = [t for t in needs() if t.startswith("The reception phone")]
    s, h, _r = G("reception", "/finance/porders/s454/order")
    out["phone_line_met"] = [t for t in needs() if t.startswith("The reception phone")]
    _save("02_order_list.html", h)
    out["list"] = dict(status=s, whose=re.findall(r'id="whose">([^<]+)<', h), cards=len(re.findall(r'<div class="card" data-sn=', h)),
                       two=len(re.findall(r'>Kholiye</a><button class="g"', h)), wa='id="waall"' in h, wa_disabled='id="waall" disabled' in h,
                       waoff="Reception phone set nahi hai — call se order kijiye" in h, printb='id="print"' in h, oldlink=re.findall(r'id="oldlink"[^>]*>([^<]+)<', h),
                       more=re.findall(r'class="more"[^>]*>([^<]+)<', h), callnote="Call se order kiya? Us supplier par" in h)
    _save("03_whatsapp_disabled.html", h)
    s, j = J("reception", "/finance/porders/api/s454/ordered", dict(sn="KEDAR PHARMACEUTICAL"))
    out["kedar1"] = [s, j.get("ok"), j.get("already")]
    o = q("SELECT * FROM purchase_order WHERE supplier_norm='KEDAR PHARMACEUTICAL' AND order_src='s454'")
    out["kedar_order"] = [dict(status=x["status"], by=x["created_by"], via=x["order_via"], ext=x["ext_ref"], n=q("SELECT COUNT(*) n FROM purchase_order_line WHERE order_id=?", x["id"])[0]["n"],
                               section=x["section"]) for x in o]
    s, j = J("reception", "/finance/porders/api/s454/ordered", dict(sn="KEDAR PHARMACEUTICAL"))
    out["kedar2"] = [s, j.get("ok"), j.get("already"), len(q("SELECT 1 FROM purchase_order WHERE supplier_norm='KEDAR PHARMACEUTICAL' AND order_src='s454'"))]
    out["kedar_card_gone"] = "KEDAR PHARMACEUTICAL" not in [e["sn"] for e in OS.entries(db)]
    # ---- Kholiye: one supplier, the Call, the number under it; the call's tap; the card then reads "call kiya tha"
    s, h, _r = G("reception", "/finance/porders/s454/order/DEEPAM%20PHARMA")
    tel = re.findall(r'href="tel:([+\d]*)"', h)
    nums = re.findall(r'<div class="num">([^<]+)</div>', h)
    out["deepam"] = dict(status=s, lines=re.findall(r'<span class="i">([^<]+)</span><span class="q">([^<]+)</span>', h), tel=bool(tel and len(re.sub(r"\D", "", tel[0])) >= 10),
                         num_shown=bool(nums and len(re.sub(r"\D", "", nums[0])) >= 10), baat="Baat ho gayi? Tab yeh dabaiye." in h, ordered='id="ordered"' in h,
                         qty='id="qtylink"' in h)
    a0 = q("SELECT COUNT(*) n FROM purchase_audit WHERE action='s454_call'")[0]["n"]
    out["call"] = J("reception", "/finance/porders/api/s454/call", dict(sn="DEEPAM PHARMA"))[0]
    out["call_audit"] = q("SELECT COUNT(*) n FROM purchase_audit WHERE action='s454_call'")[0]["n"] - a0
    out["called_card"] = "2 dawa · call kiya tha, order baaki" in text(G("reception", "/finance/porders/s454/order")[1])
    s, h, _r = G("reception", "/finance/porders/s454/order/RAVI%20MEDICAL%20AGENCY")
    out["ravi_page"] = ["Is supplier ka phone number yahan nahi hai" in h, "tel:" not in h, 'id="ordered"' in h]
    _save("04_supplier_no_phone.html", h)
    out["ravi_owner_line"] = [t for t in needs() if t == "To order: RAVI MEDICAL AGENCY has no phone number in the phone book"]
    out["scan_needs"] = [t for t in needs() if t.startswith("Bill scan pending on")]
    # ---- a quantity changed goes into the order and the message; an old line ordered again, and removed again
    s, j = J("reception", "/finance/porders/api/s454/qty", dict(src="sheet", ref=str(q("SELECT id FROM order_sheet_line WHERE item_printed='AURAB L CAP'")[0]["id"]),
                                                                item=q("SELECT item FROM order_sheet_line WHERE item_printed='AURAB L CAP'")[0]["item"], delta=1))
    out["qty_plus"] = s
    up = q("SELECT id, state FROM order_sheet_line WHERE item_printed='UPRISE 6L INJ'")[0]
    out["reorder"] = J("reception", "/finance/porders/api/s454/reorder", dict(line=up["id"]))[0]
    e = next((x for x in OS.entries(db) if x["sn"] == "RADHA MEDICAL & SCIENTIFIC"), None)
    out["reorder_in_card"] = bool(e and any(l["item"] == "UPRISE 6L INJ" for l in e["lines"])) and q("SELECT state, reorder_day FROM order_sheet_line WHERE id=?", up["id"])[0]["reorder_day"] == TODAY.isoformat()
    s, j = J("reception", "/finance/porders/api/s454/qty", dict(src="sheet", ref=str(up["id"]), item="UPRISE 6L INJ", remove=1))
    out["reorder_removed"] = [s, j.get("back_to_old"), q("SELECT state FROM order_sheet_line WHERE id=?", up["id"])[0]["state"]]
    s, h, _r = G("reception", "/finance/porders/s454/old")
    out["oldpage"] = dict(status=s, n=len(re.findall(r'class="ol" data-line=', h)), btn=h.count(">Dobara order karo<"))
    _save("05_purane_pending_all.html", h)
    s, h, _r = G("reception", "/finance/porders/s454/order/JANTA%20PHARMACEUTICALS")
    out["janta_old_block"] = ["Purane pending — dobara order tabhi, jab zaroorat ho" in h, h.count(">Dobara order karo<")]
    # ---- order.source = system: the day's proposals are the lines to order; the orthotic card on both settings, one card with the sheet's line
    vendor, short = OS._ortho_short(db)
    out["ortho_short_n"] = len(short)
    if short:
        it = short[0]
        ins(db, "order_sheet_line", dict(entry_no="OP-W454", item_printed=it["item"][:21], item=it["item"], resolved=1, supplier=vendor, supplier_norm=pa.supplier_key(vendor),
                                         packing="1*1", pack_size=1, line_date=TODAY.isoformat(), qty_raw="3", qty=3, units=3, rate_p=0, value_p=0, kind="new",
                                         state="to_order", first_sheet=1, last_sheet=1, created_at=dt.datetime.now().isoformat()))
        db.commit()
        e = next((x for x in OS.entries(db) if x["sn"] == pa.supplier_key(vendor)), None)
        out["ortho_card"] = dict(one=sum(1 for x in OS.entries(db) if x["sn"] == pa.supplier_key(vendor)) == 1,
                                 item_once=sum(1 for l in (e or {}).get("lines", []) if l["item"] == it["item"]) == 1,
                                 sheet_qty=next((l["qty"] for l in (e or {}).get("lines", []) if l["item"] == it["item"]), None) == 3,
                                 sources=(e or {}).get("sources"))
    pid = ins(db, "order_proposal", dict(day=TODAY.isoformat(), supplier_norm="W454 SYSTEM PHARMA", vendor="W454 SYSTEM PHARMA", kind="fixed", status="open",
                                         lines=json.dumps([dict(item="W454 SYS TAB", qty=20, unit="strip", pack_size=10, packing="1*10", rate_p=500, on_hand=4)]),
                                         total_p=10000, prepared_at=dt.datetime.now().isoformat()))
    db.commit()
    setv("order.source", "system")
    es = OS.entries(db)
    out["system"] = dict(sys_card=any(e["sn"] == "W454 SYSTEM PHARMA" and e["lines"][0]["item"] == "W454 SYS TAB" for e in es),
                         no_sheet=not any("sheet" in e["sources"] for e in es), ortho=any("ortho" in e["sources"] for e in es) if short else None,
                         whose=re.findall(r'id="whose">([^<]+)<', G("reception", "/finance/porders/s454/order")[1]))
    s, j = J("reception", "/finance/porders/api/s454/ordered", dict(sn="W454 SYSTEM PHARMA"))
    out["system_ordered"] = [s, q("SELECT status, sent_order_id IS NOT NULL AS linked FROM order_proposal WHERE id=?", pid)]
    setv("order.source", "marg_sheet")
    out["sheet_ortho"] = any("ortho" in e["sources"] for e in OS.entries(db)) if short else None
    # ---- WhatsApp: the phone silent -> refused, the owner hears of it once met; no key -> the same
    nl0 = [t for t in needs() if t.startswith("The reception phone")]
    s, j = J("reception", "/finance/porders/api/s454/whatsapp")
    out["wa_silent"] = [s, j.get("error"), j.get("why")]
    out["owner_phone_line"] = [nl0, [t for t in needs() if t.startswith("The reception phone")]]
    k = tok()
    setv("supplier_msg.phone_token", "")
    s, j = J("reception", "/finance/porders/api/s454/whatsapp")
    out["wa_nokey"] = [s, j.get("why")]
    setv("supplier_msg.phone_token", k)
    # the phone alive (walk-only: its last ask written as now): every pending supplier with a number gets one order and one message
    setv("supplier_msg.phone_last", "%s 200" % dt.datetime.now().replace(microsecond=0).isoformat())
    month = "2026-08"
    pay0 = dict(state=supplier_msg.state(db, month)["counts"], pending=len(supplier_msg.pending(db)), bank=[l["text"] for l in supplier_msg.needs_you_lines(db)])
    before = {e["sn"]: e["state"] for e in OS.entries(db)}
    s, h, _r = G("reception", "/finance/porders/s454/order")
    out["wa_enabled"] = 'id="waall" disabled' not in h and 'id="waall"' in h
    s, j = J("reception", "/finance/porders/api/s454/whatsapp")
    out["wa_all"] = [s, j.get("queued"), j.get("skipped")]
    msgs = q("SELECT id, vendor_norm, ref, status, body, to_number IS NOT NULL AS has_to FROM supplier_msg WHERE kind='order'")
    drafts = q("SELECT id, supplier_norm, status FROM purchase_order WHERE order_src='s454' AND status='draft'")
    out["wa_msgs"] = dict(n=len(msgs), suppliers=sorted(m["vendor_norm"] for m in msgs), drafts=len(drafts), ravi=any(m["vendor_norm"] == "RAVI MEDICAL AGENCY" for m in msgs),
                          one_each=len({m["vendor_norm"] for m in msgs}) == len(msgs), pending_before=sorted(sn for sn, st in before.items() if st != "in_line"))
    pay1 = dict(state=supplier_msg.state(db, month)["counts"], pending=len(supplier_msg.pending(db)), bank=[l["text"] for l in supplier_msg.needs_you_lines(db)])
    out["pay_unchanged"] = [pay0 == pay1, pay0, pay1]
    body_sh = next((m["body"] for m in msgs if m["vendor_norm"] == "SHRADDHA MEDICOSE"), "")
    body_ja = next((m["body"] for m in msgs if m["vendor_norm"] == "JANTA PHARMACEUTICALS"), "")
    body_ra = next((m["body"] for m in msgs if m["vendor_norm"] == "RADHA MEDICAL & SCIENTIFIC"), "")
    out["body"] = dict(aurab="AURAB L CAP — 11 strips" in body_sh, head=body_sh.startswith(pa.WA_HEADER + "\n\n"), lines=body_sh.count("\n") - 1,
                       units=" units" in "".join(m["body"] for m in msgs), old_in_msg=any(x in body_ja for x in ("NUPTACH", "POWERGESIC")) or "UPRISE" in body_ra,
                       json_ok=_json_roundtrip(body_sh))
    out["aurab_line"] = q("SELECT l.packs FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.supplier_norm='SHRADDHA MEDICOSE' AND l.item LIKE 'AURAB L CAP%'")
    st1 = json.loads(G("reception", "/finance/porders/api/s454/state")[1])
    out["state_inline"] = dict(order=st1["counts"]["order"], maal=st1["counts"]["maal"], inline=sorted(x["sn"] for x in st1["suppliers"] if x["state"] == "in_line"))
    s, h, _r = G("reception", "/finance/porders/s454/order")
    _save("06_whatsapp_line_mein_hai.html", h)
    out["inline_word"] = "WhatsApp line mein hai" in h
    # the phone's queue: next hands a message once, not again within the gap
    n1 = phone("/finance/api/supplier-msg/next")
    n2 = phone("/finance/api/supplier-msg/next")
    out["next"] = [n1[0], n2[0], bool(n1[1].get("id")), n1[1].get("id") != n2[1].get("id")]
    # the phone says sent (DEEPAM) / failed (DRUG DEAL); GUNINA's waits past the hour
    mid = {m["vendor_norm"]: m["id"] for m in msgs}
    out["done_ok"] = phone("/finance/api/supplier-msg/done", dict(id=mid.get("DEEPAM PHARMA"), ok=True))[0]
    out["done_fail"] = phone("/finance/api/supplier-msg/done", dict(id=mid.get("DRUG DEAL"), ok=False, error="send not clicked"))[0]
    db.execute("UPDATE supplier_msg SET queued_at=? WHERE id=?", ((dt.datetime.now() - dt.timedelta(minutes=61)).replace(microsecond=0).isoformat(), mid.get("GUNINA PHARMACEUTICALS PVT LTD")))
    db.commit()
    es = {e["sn"]: e for e in OS.entries(db)}                         # a page read runs the withdrawal pass first
    G("reception", "/finance/porders/s454/order")
    es = {e["sn"]: e for e in OS.entries(db)}
    out["after_phone"] = dict(deepam=q("SELECT status, order_via FROM purchase_order WHERE supplier_norm='DEEPAM PHARMA' AND order_src='s454'"),
                              drug_state=(es.get("DRUG DEAL") or {}).get("state"), gunina_state=(es.get("GUNINA PHARMACEUTICALS PVT LTD") or {}).get("state"),
                              deepam_gone="DEEPAM PHARMA" not in es)
    s, h, _r = G("reception", "/finance/porders/s454/order")
    out["wa_no_word"] = "WhatsApp nahi gaya — call kijiye" in h
    out["green_line"] = re.findall(r'id="wagone"><div class="t">([^<]+)</div><div>([^<]+)</div>', h)
    _save("07_whatsapp_nahi_gaya.html", h)
    s, j = J("reception", "/finance/porders/api/s454/ordered", dict(sn="DRUG DEAL"))
    out["drug_confirm"] = [s, j.get("confirmed"), q("SELECT COUNT(*) n FROM purchase_order WHERE supplier_norm='DRUG DEAL' AND order_src='s454'")[0]["n"],
                           q("SELECT status FROM purchase_order WHERE supplier_norm='DRUG DEAL' AND order_src='s454'")[0]["status"]]
    # never in two places: pending / in the line / ordered
    es = {e["sn"]: e["state"] for e in OS.entries(db)}
    ordered = {r["supplier_norm"] for r in q("SELECT supplier_norm FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received')")}
    out["exclusive"] = [sn for sn in set(es) | ordered if (sn in ordered) and (es.get(sn) in ("pending", "in_line"))]
    # ---- the reminder: one push at 17:00 naming those still to order; nothing at 12:00 or 15:00; on marg_sheet nothing at 09:00
    n0 = _stub_lines()
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(12, 0)))
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(15, 0)))
    out["remind_noon"] = _stub_lines() - n0
    os.environ["ORDER_TICK"] = "prepare"
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(9, 0)))
    os.environ.pop("ORDER_TICK", None)
    out["remind_0900"] = _stub_lines() - n0
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(17, 0)))
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(17, 10)))
    texts = _stub_texts()[n0:]
    out["remind_rows"] = q("SELECT slot, text FROM order_notice WHERE day=? AND slot LIKE 'R%'", TODAY.isoformat())
    out["notice_to"] = [x.strip() for x in order_rules._setting(db, "order.notice_to").split(",") if x.strip()]
    pend_names = [e["vendor"] for e in OS.entries(db) if e["state"] != "in_line"]
    out["remind_1700"] = dict(n=len(texts), text=texts[-1] if texts else "", names_ok=bool(texts) and all(nm in texts[-1] for nm in pend_names))
    # ---- frozen: the row is not shown and the routes refuse
    setv("order.freeze", json.dumps(dict(by="W454 walk", at=dt.datetime.now().replace(microsecond=0).isoformat(), reason="W454 walk freeze")))
    s, h, _r = G("reception", "/finance/porders")
    s2, j2 = J("reception", "/finance/porders/api/s454/ordered", dict(sn="SHRADDHA MEDICOSE"))
    out["frozen"] = ['id="row_order"' not in h, s2, j2.get("error")]
    setv("order.freeze", "")
    # ---- the owner's cards on the old page; the settings card: each key of part 1, changed, taking effect, audited; nobody else
    s, h, _r = G("manoj", "/finance/porders?old=1")
    out["owner_cards"] = dict(status=s, src='id="s454src"' in h, cmp=re.findall(r"Orders of [\d-]+: the system agreed on \d+ of \d+ items with Darpan's sheet", h),
                              old=re.findall(r"Marg shows \d+ old pending orders: \d+ already supplied since, \d+ never came", h),
                              sheet=re.findall(r"Order sheet of [\d-]+: taken [^<]+", h), settings='id="s454settings"' in h, oldpage='id="sub"' in h)
    _save("11_owner_cards_and_settings.html", h)
    s, h, _r = G("reception", "/finance/porders?old=1")
    out["reception_old"] = [s, 'id="sub"' in h, 'id="s454settings"' in h]
    keys = list(OS.SETTINGS)
    vals = {"porders.simple": "0", "order.source": "system", "order.sheet_max_age_days": "8", "order.sheet_print_old": "0", "order.old_done_days": "5",
            "order.old_show_days": "45", "order.remind_times": "18:30", "order.whatsapp_wait_min": "45", "order.phone_alive_min": "20",
            "supplier_msg.handout_gap_min": "12", "purchase.register_from": "2026-11-01", "purchase.parked_months": "2026-09,2026-10",
            "purchase.arrival_scan_days": "6", "purchase.unread_pair_days": "5"}
    eff = {}
    a0 = q("SELECT COUNT(*) n FROM purchase_audit WHERE action='s454_setting'")[0]["n"]
    for kk in keys:
        old = OS.setting(db, kk)
        s, j = J("manoj", "/finance/porders/api/s454/setting", dict(key=kk, value=vals[kk]))
        now_v = OS.setting(db, kk)
        if kk == "porders.simple":
            eff[kk] = 'id="sub"' in G("reception", "/finance/porders")[1]
        elif kk == "order.source":
            eff[kk] = OS.source(db) == "system"
        elif kk == "order.sheet_print_old":
            eff[kk] = not any(x["old"] for b in OP.layout(db)["blocks"] for x in b["rows"])
        elif kk == "order.remind_times":
            eff[kk] = OS.reminder_due(db, dt.datetime.combine(TODAY, dt.time(18, 30)))[0] == "R1830"
        elif kk == "order.phone_alive_min":
            setv("supplier_msg.phone_last", "%s 200" % (dt.datetime.now() - dt.timedelta(minutes=25)).replace(microsecond=0).isoformat())
            eff[kk] = OS.phone_state(db)[0] is False
        elif kk == "purchase.register_from":
            import porders_s454                                        # noqa: PLC0415
            eff[kk] = porders_s454.month_class(db, "2026-10") == "parked" or porders_s454.month_class(db, "2026-10") == "hidden"
        elif kk == "purchase.parked_months":
            import porders_s454                                        # noqa: PLC0415
            eff[kk] = porders_s454.parked(db) == ["2026-09", "2026-10"]
        else:
            eff[kk] = now_v == vals[kk]
        s2, j2 = J("manoj", "/finance/porders/api/s454/setting", dict(key=kk, value=old))
        eff[kk] = [s, now_v == vals[kk], eff[kk], s2, OS.setting(db, kk) == old]
    out["settings"] = eff
    out["settings_audit"] = q("SELECT COUNT(*) n FROM purchase_audit WHERE action='s454_setting'")[0]["n"] - a0
    out["settings_bad"] = [J("manoj", "/finance/porders/api/s454/setting", dict(key="order.remind_times", value="25:00"))[0],
                           J("manoj", "/finance/porders/api/s454/setting", dict(key="no.such", value="1"))[0],
                           J("reception", "/finance/porders/api/s454/setting", dict(key="order.source", value="system"))[0],
                           J("darpan", "/finance/porders/api/s454/setting", dict(key="order.source", value="system"))[0]]
    out["n_settings"] = len(keys)
    # ---- the staff-eye walk (DUTY_MAP v4): every login the kit affects, at the end of the run
    out["eye"] = staff_eye(db, fc, BASE)
    return out


def _json_roundtrip(body):
    try:
        return json.loads(json.dumps(dict(text=body), ensure_ascii=False))["text"] == body and "\n" in body
    except ValueError:
        return False


def staff_eye(db, fc, BASE):
    """Sign in through the walk's own portal (its own secret and user store) as each login; render its home; for each of its duties in
    DUTY_MAP.json whose due_sql says it is due, fetch the door and look for its marker."""
    import portal as po                                                # noqa: PLC0415
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W454J"])["pw"]
    dm = json.load(open(os.environ["REAL_DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % os.environ["FINANCE_DB"], uri=True)
    eye = {}
    for who in ("reception", "darpan", "shavez", "amir", "manoj"):
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + tok})
        import html as _h                                              # noqa: PLC0415
        seen = [_h.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r.get_data(as_text=True))]
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


# ----------------------------------------------------------------------- C: as already ordered; the tie; arrival; scans; questions; parked
def c_probe(G, J, take, S1, reader, stamp_name, q, db, adb, scan, needs, text, marg_line, marg_bill, setv, W, fc, BASE, H, pa):
    import order_sheet as OS                                           # noqa: PLC0415
    import order_rules                                                 # noqa: PLC0415
    import porders                                                     # noqa: PLC0415
    import porders_s454 as P4                                          # noqa: PLC0415
    out = {}
    # walk-only data (named): the box's own pharmacy scans of the last two days are set aside on this scratch copy, so that the crafted scans
    # alone decide the tie (live, today's real scans DO tie to the paper orders of 02-Oct -- the installer reports which)
    adb.execute("UPDATE bills SET status='rejected' WHERE kind='Pharmacy' AND COALESCE(stamp_no,'') NOT LIKE 'W454-%' AND created_at>=?",
                ((dt.datetime.utcnow() - dt.timedelta(days=2)).strftime("%Y-%m-%d"),))
    adb.commit()
    yday = TODAY - dt.timedelta(days=1)
    t_order = dt.datetime.combine(yday, dt.time(15, 0))
    # Amir's lists before (the box's own rows): nothing is added and nothing is removed by this kit
    amir0 = _amir_rows(G, pa, db)
    # ---- the first load, "as already ordered" (the installer's own function, first_load_s454.load)
    sys.path.insert(0, os.environ["KITDIR"])
    import first_load_s454 as FL                                       # noqa: PLC0415
    r = FL.load_text(db, S1, os.environ["READER_NEW"], name="W454 first load")
    out["first"] = dict(made=len(r.get("paper_orders") or []), new=r.get("new"), old=r.get("old"))
    po_ = q("SELECT id, supplier_norm, status, created_at, order_via FROM purchase_order WHERE order_via='paper'")
    out["paper"] = dict(n=len(po_), when=sorted({x["created_at"] for x in po_}), status=sorted({x["status"] for x in po_}))
    es = OS.entries(db, with_ortho=False)
    out["paper_no_card"] = not es
    s, h, _r = G("reception", "/finance/porders/s454/maal")
    out["maal"] = dict(status=s, cards=len(re.findall(r'class="card" data-order=', h)), dates=sorted(set(re.findall(r"Order (\d\d-\d\d) · \d+ dawa", h))),
                       billscan=h.count(">Bill scan karo</a>") if False else h.count("Bill scan karo"), nobill=h.count("Bill nahi hai, ya kam aaya?"))
    _save("08_maal_aaya.html", h)
    kedar = next(x for x in po_ if x["supplier_norm"] == "KEDAR PHARMACEUTICAL")
    marg_line("KEDAR PHARMACEUTICAL", "MEG QCS", TODAY.isoformat(), 20)
    porders.detect_supplies(db)
    out["paper_cleared"] = q("SELECT item, billed_qty, supplied FROM purchase_order_line WHERE order_id=? AND item='MEG QCS'", kedar["id"])
    # ---- a never-ticked line Marg has supplied closes; a new line eight days old lapses; old lines' visibility
    t2 = tiny_sheet("W454 TICK PHARMA", [("W454 NEVER TAB", "1*1", "OP-9101", yday.isoformat(), "5")], yday)
    x2 = reader.convert(t2.encode("latin-1"))[0]
    out["take_tiny"] = take(x2, stamp_name(hashlib.md5(x2).hexdigest()))
    out["tick_card0"] = any(e["sn"] == "W454 TICK PHARMA" for e in OS.entries(db, with_ortho=False))
    marg_line("W454 TICK PHARMA", "W454 NEVER TAB", TODAY.isoformat(), 5)
    OS.refresh(db)
    out["tick_closed"] = [q("SELECT state, marg_date FROM order_sheet_line WHERE item_printed='W454 NEVER TAB'"), not any(e["sn"] == "W454 TICK PHARMA" for e in OS.entries(db, with_ortho=False))]
    d8 = TODAY - dt.timedelta(days=8)
    t3 = tiny_sheet("W454 LAPSE PHARMA", [("W454 LAPSE TAB", "1*1", "OP-9201", d8.isoformat(), "4")], d8)
    x3 = reader.convert(t3.encode("latin-1"))[0]
    out["take_lapse"] = take(x3, stamp_name(hashlib.md5(x3).hexdigest()))
    OS.refresh(db)
    out["lapsed"] = [q("SELECT state FROM order_sheet_line WHERE item_printed='W454 LAPSE TAB'"), [t for t in needs() if "W454 LAPSE PHARMA was never placed" in t]]
    old = q("SELECT id, item_printed, line_date FROM order_sheet_line WHERE state='old' ORDER BY id")
    a_id, b_id = old[0]["id"], old[1]["id"]
    db.execute("UPDATE order_sheet_line SET marg_date=?, marg_bill='W454', marg_seen_at=? WHERE id=?", (D(7), D(7) + "T10:00:00", a_id))
    db.execute("UPDATE order_sheet_line SET line_date=? WHERE id=?", (D(61), b_id))
    db.commit()
    staff = {l["id"] for l in OS.old_lines(db)}
    owner = {l["id"] for l in OS.old_lines(db, staff=False)}
    out["visibility"] = [a_id not in staff, b_id not in staff, a_id in owner, b_id in owner]
    db.execute("UPDATE order_sheet_line SET marg_seen_at=? WHERE id=?", (D(6) + "T10:00:00", a_id))
    db.execute("UPDATE order_sheet_line SET line_date=? WHERE id=?", (D(60), b_id))
    db.commit()
    staff = {l["id"] for l in OS.old_lines(db)}
    out["visibility_day_before"] = [a_id in staff, b_id in staff]
    out["cmp"] = json.loads(q("SELECT cmp FROM order_sheet ORDER BY id LIMIT 1")[0]["cmp"] or "{}")
    # ---- the tie: a scan after the order arrives it; lines stay open; in transit; no "Scan karo"
    t_scan = dt.datetime.combine(TODAY, dt.time(0, 30))
    s1 = scan("W454-11", "KEDAR PHARMACEUTICAL", "71101", TODAY.isoformat(), 3996.0, t_scan)
    OS.tie_pass(db, "W454")
    ko = q("SELECT status, received_by FROM purchase_order WHERE id=?", kedar["id"])[0]
    transit = pa._in_transit(db)
    out["tie1"] = dict(status=ko["status"], by=ko["received_by"], open=q("SELECT COUNT(*) n FROM purchase_order_line WHERE order_id=? AND supplied IS NULL", kedar["id"])[0]["n"],
                       transit=pa.norm("KT ROS DT") in transit, scan_karo=any(x["order_id"] == kedar["id"] for x in porders.received_unbilled(db, porders.unscanned_bills(db))),
                       tie=q("SELECT asset_bill_id, how FROM order_scan_tie WHERE order_id=?", kedar["id"]),
                       # S403's shortage and S410's interim check keep its open lines counted until Marg answers them (4.4) -- and the
                       # control: the query as it was (status = 'sent' only) would drop them the moment the scan arrives it
                       onord403=any(k.upper().startswith("KT ROS") for k in porders._on_order(db, q("SELECT vendor FROM purchase_order WHERE id=?", kedar["id"])[0]["vendor"])),
                       onord410=pa.norm("KT ROS DT") in order_rules._on_order_units(db, TODAY),
                       control=q("SELECT COUNT(*) n FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.status='sent' AND o.id=? "
                                 "AND l.supplied IS NULL", kedar["id"])[0]["n"])
    # a second scan of that supplier goes to the next order
    k2 = OS.make_order(db, "W454 walk", "KEDAR PHARMACEUTICAL", [dict(item="MEG QCS", packs=10, pack_size=15, rate_p=8000)], "sent", "call",
                       created_at=dt.datetime.combine(TODAY, dt.time(1, 0)).isoformat())
    db.commit()
    s2 = scan("W454-12", "KEDAR PHARMACEUTICAL", "71102", TODAY.isoformat(), 1200.0, dt.datetime.combine(TODAY, dt.time(1, 30)))
    OS.tie_pass(db, "W454")
    out["tie2"] = q("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", s2)
    out["k2"] = k2
    # an older order received on the arrival screen and unscanned + a newer awaited: the scan goes to the older
    dp = next(x for x in po_ if x["supplier_norm"] == "DEEPAM PHARMA")
    J("reception", "/finance/porders/api/s454/arrive", dict(order_id=dp["id"], lines=[]))
    dpn = OS.make_order(db, "W454 walk", "DEEPAM PHARMA", [dict(item="TENDOZAC TAB", packs=10, pack_size=10, rate_p=19050)], "sent", "call",
                        created_at=dt.datetime.combine(TODAY, dt.time(1, 0)).isoformat())
    db.commit()
    s3 = scan("W454-13", "DEEPAM PHARMA", "71103", TODAY.isoformat(), 2000.0, dt.datetime.combine(TODAY, dt.time(2, 0)))
    OS.tie_pass(db, "W454")
    out["tie_older"] = [q("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", s3), dp["id"], dpn,
                        q("SELECT status FROM purchase_order WHERE id=?", dpn)[0]["status"]]
    # the older past its seven days (GUNINA) / replaced by its Marg bill's line (JANTA): the scan goes to the newer
    gu = next(x for x in po_ if x["supplier_norm"] == "GUNINA PHARMACEUTICALS PVT LTD")
    J("reception", "/finance/porders/api/s454/arrive", dict(order_id=gu["id"], lines=[]))
    db.execute("UPDATE purchase_order SET received_at=? WHERE id=?", ((TODAY - dt.timedelta(days=8)).isoformat() + "T10:00:00", gu["id"]))
    db.commit()
    gun = OS.make_order(db, "W454 walk", "GUNINA PHARMACEUTICALS PVT LTD", [dict(item="DFO MR", packs=10, pack_size=10, rate_p=10352)], "sent", "call",
                        created_at=dt.datetime.combine(TODAY, dt.time(1, 0)).isoformat())
    db.commit()
    ja = next(x for x in po_ if x["supplier_norm"] == "JANTA PHARMACEUTICALS")
    out["ja_arrive"] = J("reception", "/finance/porders/api/s454/arrive", dict(order_id=ja["id"], lines=[]))[0]
    marg_bill("JANTA PHARMACEUTICALS BAREILLY", "82201", TODAY.isoformat(), 500000)
    jan = OS.make_order(db, "W454 walk", "JANTA PHARMACEUTICALS", [dict(item="VOLITRA APS SPRAY", packs=10, pack_size=1, rate_p=26786)], "sent", "call",
                        created_at=dt.datetime.combine(TODAY, dt.time(1, 0)).isoformat())
    db.commit()
    s4 = scan("W454-14", "GUNINA PHARMACEUTICALS PVT LTD", "71104", TODAY.isoformat(), 1035.0, dt.datetime.combine(TODAY, dt.time(2, 0)))
    s5 = scan("W454-15", "JANTA PHARMACEUTICALS", "71105", TODAY.isoformat(), 2679.0, dt.datetime.combine(TODAY, dt.time(2, 0)))
    OS.tie_pass(db, "W454")
    out["tie_newer"] = [q("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", s4), gun, q("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", s5), jan]
    # a scan made before the order, a bill dated before the order's day, the same date in a wrong year, a merely similar spelling
    sz = next(x for x in po_ if x["supplier_norm"] == "SHIVAAZ FORMULATIONS")
    db.execute("UPDATE purchase_order SET created_at=? WHERE id=?", (dt.datetime.combine(TODAY, dt.time(3, 0)).isoformat(), sz["id"]))
    db.commit()
    s6 = scan("W454-16", "SHIVAAZ FORMULATIONS", "71106", TODAY.isoformat(), 670.0, dt.datetime.combine(TODAY, dt.time(2, 50)))
    ra = next(x for x in po_ if x["supplier_norm"] == "RADHA MEDICAL & SCIENTIFIC")
    s7 = scan("W454-17", "RADHA MEDICAL & SCIENTIFIC", "71107", (yday - dt.timedelta(days=2)).isoformat(), 1921.0, dt.datetime.combine(TODAY, dt.time(2, 0)))
    kr = next(x for x in po_ if x["supplier_norm"] == "KRISHNA MEDICOS")
    s8 = scan("W454-18", "KRISHNA MEDICOS", "71108", "2019-%s" % yday.isoformat()[5:], 1794.0, dt.datetime.combine(TODAY, dt.time(2, 0)))
    sh = next(x for x in po_ if x["supplier_norm"] == "SHRADDHA MEDICOSE")
    s9 = scan("W454-19", "SHRADHA MEDICOS", "71109", TODAY.isoformat(), 2460.0, dt.datetime.combine(TODAY, dt.time(2, 0)))
    OS.tie_pass(db, "W454")
    tied = {r["asset_bill_id"]: r["order_id"] for r in q("SELECT asset_bill_id, order_id FROM order_scan_tie")}
    out["no_tie"] = dict(before_order=s6 not in tied, bill_before=s7 not in tied, wrong_year=tied.get(s8) == kr["id"], similar=s9 not in tied)
    # a supplier filled in two minutes after the scan was made: tied at the next cron run, with no page opened
    dd = next(x for x in po_ if x["supplier_norm"] == "DRUG DEAL")
    s10 = scan("W454-20", None, "71110", TODAY.isoformat(), 3134.0, dt.datetime.combine(TODAY, dt.time(2, 0)), ocr="reading")
    OS.tie_pass(db, "W454")
    out["late0"] = s10 not in {r["asset_bill_id"] for r in q("SELECT asset_bill_id FROM order_scan_tie")}
    adb.execute("UPDATE bills SET vendor='DRUG DEAL', ocr_status='read' WHERE id=?", (s10,))
    adb.commit()
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(6, 10)))
    out["late1"] = q("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", s10) == [dict(order_id=dd["id"])]
    # Marg's bill then records ordered against supplied on the open lines
    marg_line("KEDAR PHARMACEUTICAL", "KT ROS DT", TODAY.isoformat(), 15)
    porders.detect_supplies(db)
    out["marg_records"] = q("SELECT packs, billed_qty, supplied, short FROM purchase_order_line WHERE order_id=? AND item='KT ROS DT'", kedar["id"])
    # an unticked supplier whose bill is scanned after the sheet's load: one order "by the bill's scan", arrived, its card gone
    t4 = tiny_sheet("W454 WALK PHARMA", [("W454 WALK TAB", "1*1", "OP-9301", TODAY.isoformat(), "6")], TODAY)
    x4 = reader.convert(t4.encode("latin-1"))[0]
    take(x4, stamp_name(hashlib.md5(x4).hexdigest()))
    t5 = tiny_sheet("W454 EARLY PHARMA", [("W454 EARLY TAB", "1*1", "OP-9302", TODAY.isoformat(), "6")], TODAY)
    x5 = reader.convert(t5.encode("latin-1"))[0]
    take(x5, stamp_name(hashlib.md5(x5).hexdigest()))
    t6 = tiny_sheet("W454 OLDBILL PHARMA", [("W454 OLDBILL TAB", "1*1", "OP-9303", TODAY.isoformat(), "6")], TODAY)
    x6 = reader.convert(t6.encode("latin-1"))[0]
    take(x6, stamp_name(hashlib.md5(x6).hexdigest()))
    nowm = dt.datetime.now().replace(second=0, microsecond=0)
    s11 = scan("W454-21", "W454 WALK PHARMA", "71111", TODAY.isoformat(), 60.0, nowm + dt.timedelta(minutes=2))
    s12 = scan("W454-22", "W454 EARLY PHARMA", "71112", TODAY.isoformat(), 60.0, nowm - dt.timedelta(minutes=90))
    s13 = scan("W454-23", "W454 OLDBILL PHARMA", "71113", (TODAY - dt.timedelta(days=3)).isoformat(), 60.0, nowm + dt.timedelta(minutes=2))
    OS.tie_pass(db, "W454")
    wo = q("SELECT o.status, o.order_via, o.created_by FROM purchase_order o JOIN order_scan_tie t ON t.order_id=o.id WHERE t.asset_bill_id=?", s11)
    tied = {r["asset_bill_id"] for r in q("SELECT asset_bill_id FROM order_scan_tie")}
    out["unticked"] = dict(order=wo, card_gone=not any(e["sn"] == "W454 WALK PHARMA" for e in OS.entries(db, with_ortho=False)),
                           early=s12 not in tied, oldbill=s13 not in tied)
    # an unread paper ties nothing before its "Haan", and ties after it
    t7 = tiny_sheet("W454 UNREAD PHARMA", [("W454 UNREAD TAB", "1*1", "OP-9304", TODAY.isoformat(), "6")], TODAY)
    x7 = reader.convert(t7.encode("latin-1"))[0]
    take(x7, stamp_name(hashlib.md5(x7).hexdigest()))
    s14 = scan("W454-24", "W454 UNREAD PHARMA", None, None, None, dt.datetime.now().replace(second=0, microsecond=0) + dt.timedelta(minutes=3), ocr="empty")
    OS.tie_pass(db, "W454")
    u0 = s14 in {r["asset_bill_id"] for r in q("SELECT asset_bill_id FROM order_scan_tie")}
    J("reception", "/finance/porders/api/s454/pharmacy", dict(scan=s14, yes=True))
    OS.tie_pass(db, "W454")
    out["unread_tie"] = [u0, s14 in {r["asset_bill_id"] for r in q("SELECT asset_bill_id FROM order_scan_tie")}]
    # a re-run of the matcher loses no tie
    n_t = q("SELECT COUNT(*) n FROM order_scan_tie")[0]["n"]
    pa._rematch(db, "W454 walk")
    out["rematch_keeps"] = [n_t, q("SELECT COUNT(*) n FROM order_scan_tie")[0]["n"]]
    # ---- the arrival screen: all received in one tap; one line short and one not come; 'Abhi nahi aaya' saves nothing; then Baad mein
    rv = next(x for x in po_ if x["supplier_norm"] == "RAVI MEDICAL AGENCY")
    s, h, _r = G("reception", "/finance/porders/s454/maal/%d" % sh["id"])
    _save("09_arrival_screen.html", h)
    out["arrival_page"] = dict(status=s, all_ticked=h.count("<span id=\"ic") == len(q("SELECT 1 FROM purchase_order_line WHERE order_id=?", sh["id"])),
                               tap="Jo kam aaya ya nahi mila, us par tap kijiye." in h, maalok='id="maalok"' in h, abhinahi='id="abhinahi"' in h)
    s, h0, _r = G("reception", "/finance/porders/s454/maal/%d" % rv["id"])
    out["abhi_nahi"] = q("SELECT status FROM purchase_order WHERE id=?", rv["id"])[0]["status"]
    s, j = J("reception", "/finance/porders/api/s454/arrive", dict(order_id=rv["id"], lines=[]))
    out["arrive_all"] = [s, q("SELECT status FROM purchase_order WHERE id=?", rv["id"])[0]["status"],
                         q("SELECT COUNT(*) n FROM purchase_order_line WHERE order_id=? AND supplied=packs", rv["id"])[0]["n"]]
    shl = q("SELECT id, packs FROM purchase_order_line WHERE order_id=? ORDER BY id", sh["id"])
    s, j = J("reception", "/finance/porders/api/s454/arrive", dict(order_id=sh["id"], lines=[dict(id=shl[0]["id"], how="short", supplied=4),
                                                                                         dict(id=shl[1]["id"], how="missing")]))
    out["arrive_diff"] = [s, q("SELECT supplied, short, missing FROM purchase_order_line WHERE order_id=? ORDER BY id", sh["id"]),
                          q("SELECT status FROM purchase_order WHERE id=?", sh["id"])[0]["status"]]
    s, h, _r = G("reception", "/finance/porders/s454/maal/%d?done=1" % rv["id"])
    out["after_screen"] = ["Maal darj ho gaya" in h, 'id="scannow"' in h, 'id="later"' in h, "Baad mein karenge to yeh" in h]
    lines = P4.scan_lines(db)
    out["baad_mein"] = dict(ravi=any(x["kind"] == "recv" and x["order_id"] == rv["id"] for x in lines), shr=any(x["kind"] == "recv" and x["order_id"] == sh["id"] for x in lines))
    s15 = scan("W454-25", "RAVI MEDICAL AGENCY", "71114", TODAY.isoformat(), 170.0, dt.datetime.now().replace(second=0, microsecond=0) + dt.timedelta(minutes=4))
    OS.tie_pass(db, "W454")
    n_before = len(P4.scan_lines(db))
    marg_bill("SHRADDHA MEDICOSE", "82202", TODAY.isoformat(), 246000)
    lines2 = P4.scan_lines(db)
    out["leaves"] = dict(on_scan=not any(x["kind"] == "recv" and x["order_id"] == rv["id"] for x in lines2),
                         on_bill=not any(x["kind"] == "recv" and x["order_id"] == sh["id"] for x in lines2) and any(x["kind"] == "marg" and x["bill_no"] == "82202" for x in lines2),
                         count_same=len(lines2) == n_before)
    wa = OS.make_order(db, "W454 walk", "W454 ARR PHARMA", [dict(item="W454 ARR TAB", packs=5, pack_size=1, rate_p=100)], "sent", "call")
    db.commit()
    J("reception", "/finance/porders/api/s454/arrive", dict(order_id=wa, lines=[]))
    in0 = any(x["kind"] == "recv" and x["order_id"] == wa for x in P4.scan_lines(db))
    os.environ["ORDER_TODAY"] = (TODAY + dt.timedelta(days=8)).isoformat()
    in8 = any(x["kind"] == "recv" and x["order_id"] == wa for x in P4.scan_lines(db))
    os.environ.pop("ORDER_TODAY", None)
    out["eighth_day"] = [in0, in8]
    # ---- Bill scan karna hai: by supplier, five at a time; Koi paper nahi mil raha? on Marg lines only
    for i in range(7):
        marg_bill("W454 SCAN PHARMA", "8230%d" % i, TODAY.isoformat(), 10000 + i)
    s, h, _r = G("reception", "/finance/porders/s454/scan")
    out["scan_page"] = dict(status=s, shown=len(re.findall(r'<div class="ln" data-kind=', h)), agle='id="agle"' in h, groups=re.findall(r'<div class="grp">([^<]+)</div>', h),
                            grey=sorted(set(re.findall(r"(Maal aa gaya, bill scan baaki|Marg mein hai, scan nahi)", h))), nopaper='id="nopaper"' in h)
    _save("12_bill_scan_karna_hai.html", h)
    s, h, _r = G("reception", "/finance/porders/s454/scan?n=2")
    out["scan_more"] = len(re.findall(r'<div class="ln" data-kind=', h))
    s, h, _r = G("reception", "/finance/porders/s454/scan?missing=1")
    ids = [int(x) for x in re.findall(r'class="pm_"[^>]*value="(\d+)"', h) or re.findall(r'value="(\d+)" class="pm_"', h)]
    out["tick_list"] = dict(n=len(ids), only_marg=all(q("SELECT 1 FROM purchase_bill WHERE id=?", i) for i in ids))
    _save("13_koi_paper_nahi_mil_raha.html", h)
    gone = q("SELECT id FROM purchase_bill WHERE bill_no='82300'")[0]["id"]
    s, j = J("reception", "/finance/porders/api/s454/paper_missing", dict(bills=[gone]))
    out["paper_missing"] = [s, not any(x.get("bill_id") == gone for x in P4.scan_lines(db)), bool(q("SELECT 1 FROM s454_paper_missing WHERE bill_id=?", gone))]
    # ---- the questions: kinds 1, 2, 3 and S441's; one at a time; amounts unlabelled; date / number differing makes no card; Baad mein
    mo = TODAY.strftime("%Y-%m")
    marg_bill("W454 QONE PHARMA", "5001", TODAY.isoformat(), 100000)
    q1 = scan("W454-31", "W454 QONE PHARMA", "9999", (TODAY - dt.timedelta(days=10)).isoformat(), 1000.0, dt.datetime.combine(TODAY, dt.time(3, 1)), month=mo)
    marg_bill("W454 QTWO PHARMA", "7002", TODAY.isoformat(), 500000)
    q2 = scan("W454-32", "W454 QTWO PHARMA", "7002", TODAY.isoformat(), 5600.0, dt.datetime.combine(TODAY, dt.time(3, 2)), month=mo)
    q3 = scan("W454-33", "ZQXW UNKNOWN TRADERS", "8003", TODAY.isoformat(), 777.0, dt.datetime.combine(TODAY, dt.time(3, 3)), month=mo)
    marg_bill("W454 QFOUR PHARMA", "4004", TODAY.isoformat(), 200000)
    q4 = scan("W454-34", "W454 QFOUR PHARMA", "4004", (TODAY - dt.timedelta(days=20)).isoformat(), 2000.0, dt.datetime.combine(TODAY, dt.time(3, 4)), month=mo)
    q5a = scan("W454-35", "W454 QFIVE PHARMA", "6006", TODAY.isoformat(), 300.0, dt.datetime.combine(TODAY, dt.time(3, 5)), month=mo)
    q5b = scan("W454-36", "W454 QFIVE PHARMA", "6006", TODAY.isoformat(), 300.0, dt.datetime.combine(TODAY, dt.time(3, 6)), month=mo)
    adb.execute("CREATE TABLE IF NOT EXISTS scan_question (id INTEGER PRIMARY KEY AUTOINCREMENT, bill_id INTEGER NOT NULL, kind TEXT NOT NULL, cand_id INTEGER, "
                "detail TEXT, asked_at TEXT NOT NULL, answer TEXT, answered_by TEXT, answered_at TEXT, UNIQUE(bill_id, kind))")
    adb.execute("INSERT INTO scan_question (bill_id, kind, cand_id, detail, asked_at) VALUES (?,?,?,?,?)", (q5b, "twin", q5a, "W454 walk", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    adb.commit()
    q6 = scan("W454-37", "W454 QFOUR PHARMA", "9898", (TODAY - dt.timedelta(days=10)).isoformat(), 2000.0, dt.datetime.combine(TODAY, dt.time(3, 7)), month=mo)
    pa._rematch(db, "W454 walk")
    qs = P4.questions(db)
    kinds = {x["scan"]: x["kind"] for x in qs}
    q6q = [x for x in qs if x["scan"] == q6]
    for x in qs:
        if x["scan"] != q6:
            db.execute("INSERT OR REPLACE INTO s454_later (asset_bill_id, kind, at) VALUES (?,?,?)", (x["scan"], x["kind"], dt.datetime.now().isoformat()))
    db.commit()
    s, h6, _r = G("reception", "/finance/porders/s454/q")
    out["doosra"] = dict(kind=[x["kind"] for x in q6q], taken=[x.get("taken") for x in q6q], wording="Kya yeh W454 QFOUR PHARMA ke bill 4004 ka doosra scan hai?" in h6)
    _save("14_question_bill_doosra_scan.html", h6)
    db.execute("DELETE FROM s454_later")
    db.commit()
    out["q_kinds"] = dict(q1=kinds.get(q1), q2=kinds.get(q2), q3=kinds.get(q3), q4=kinds.get(q4), q5=kinds.get(q5b), n=len(qs),
                          q4_linked=bool(q("SELECT 1 FROM purchase_scan_link WHERE asset_bill_id=?", q4)))
    s, h, _r = G("reception", "/finance/porders/s454/q")
    first = re.findall(r'href="/scanapp/bills/(\d+)/file"', h)[:1]
    out["q_page"] = dict(status=s, sawaal=re.findall(r'id="sawaal">([^<]+)<', h), one=h.count('data-q="'), later='id="later"' in h)
    kq0 = re.findall(r'data-q="(\w+)"', h)
    if first and kq0:
        J("reception", "/finance/porders/api/s454/later", dict(scan=int(first[0]), kind=kq0[0]))
        h2 = G("reception", "/finance/porders/s454/q")[1]
        out["later_moves"] = [first, re.findall(r'href="/scanapp/bills/(\d+)/file"', h2)[:1], int(first[0]) == P4.questions(db)[-1]["scan"]]
    db.execute("DELETE FROM s454_later")
    db.commit()
    # walk the cards: the amount card's two amounts are unlabelled; the vendor card offers likely suppliers; S441's card
    seen_kinds = {}
    for _i in range(len(qs)):
        s, h, _r = G("reception", "/finance/porders/s454/q")
        kq = re.findall(r'data-q="(\w+)"', h)
        sid = (re.findall(r'href="/scanapp/bills/(\d+)/file"', h) or ["0"])[0]
        if kq and kq[0] not in seen_kinds:
            seen_kinds[kq[0]] = int(sid)
            _save("14_question_%s.html" % kq[0], h)
            if kq[0] == "amount":
                blk = h[h.find('data-q="amount"'):]
                out["amount_card"] = dict(buttons=len(re.findall(r"s454/amount',\{scan:\d+,paper:'[\d.]+'\}\)\">", blk)), labelled=bool(re.search(r"(?i)\b(marg|scan)\b", text(blk.split('id="later"')[0]))),
                                          koiaur="Koi aur amount" in blk)
        if not kq:
            break
        J("reception", "/finance/porders/api/s454/later", dict(scan=int(sid), kind=kq[0]))
    out["seen_kinds"] = sorted(seen_kinds)
    db.execute("DELETE FROM s454_later")
    db.commit()
    s, h, _r = G("reception", "/finance/porders/s454/q")
    s2, j2 = J("reception", "/finance/porders/api/s454/confirm", dict(scan=q1, bill=q("SELECT id FROM purchase_bill WHERE bill_no='5001'")[0]["id"], yes=True))
    out["confirm_q1"] = [s2, bool(q("SELECT 1 FROM purchase_scan_link WHERE asset_bill_id=?", q1))]
    # ---- S454 4.7: a paper with nothing read
    u1 = scan("W454-41", None, None, None, None, dt.datetime.combine(TODAY, dt.time(4, 0)), ocr="empty", month=mo)
    pa._rematch(db, "W454 walk")
    qs = P4.questions(db)
    k4 = [x for x in qs if x["scan"] == u1]
    w = porders.scan_work(db)
    am = pa.scans_for_amir(db)
    out["unread"] = dict(card=[x["kind"] for x in k4], wait=any(x["scan"] == u1 for x in w["wait"]), amir_list=any(x["id"] == u1 for x in am["list"]),
                         held=[x.get("held") for x in am["held"] if x["id"] == u1])
    J("reception", "/finance/porders/api/s454/pharmacy", dict(scan=u1, yes=True))
    out["unread_next"] = [x["kind"] for x in P4.questions(db) if x["scan"] == u1]
    s, j = J("reception", "/finance/porders/api/s454/vendor", dict(scan=u1, vendor="W454 QTWO PHARMA"))
    out["unread_vendor"] = s
    out["unread_after_vendor"] = [x["kind"] for x in P4.questions(db) if x["scan"] == u1]
    out["unread_no_pair"] = not q("SELECT 1 FROM purchase_scan_link WHERE asset_bill_id=?", u1)
    u2 = scan("W454-42", None, None, None, None, dt.datetime.combine(TODAY, dt.time(4, 10)), ocr="empty", month=mo)
    J("reception", "/finance/porders/api/s454/pharmacy", dict(scan=u2, yes=True))
    J("reception", "/finance/porders/api/s454/vendor", dict(scan=u2, vendor="W454 UPAIR PHARMA")) if False else None
    marg_bill("W454 UPAIR PHARMA", "UP1", TODAY.isoformat(), 5000)
    J("reception", "/finance/porders/api/s454/vendor", dict(scan=u2, vendor="W454 UPAIR PHARMA"))
    qq = [x for x in P4.questions(db) if x["scan"] == u2]
    out["unread_one_bill"] = [x["kind"] for x in qq]
    if qq and qq[0]["kind"] == "bill":
        _save("15_question_unread_pair.html", G("reception", "/finance/porders/s454/q")[1])
        s, j = J("reception", "/finance/porders/api/s454/confirm", dict(scan=u2, bill=qq[0]["bill"], yes=True))
        out["unread_paired"] = [s, q("SELECT grade, matched_on FROM purchase_scan_link WHERE asset_bill_id=?", u2)]
    u3 = scan("W454-43", None, None, None, None, dt.datetime.combine(TODAY, dt.time(4, 20)), ocr="empty", month=mo)
    J("reception", "/finance/porders/api/s454/pharmacy", dict(scan=u3, yes=True))
    marg_bill("W454 UTWO PHARMA", "UT1", TODAY.isoformat(), 5000)
    marg_bill("W454 UTWO PHARMA", "UT2", TODAY.isoformat(), 6000)
    J("reception", "/finance/porders/api/s454/vendor", dict(scan=u3, vendor="W454 UTWO PHARMA"))
    out["unread_two_bills"] = [x["kind"] for x in P4.questions(db) if x["scan"] == u3]
    u4 = scan("W454-44", None, None, None, None, dt.datetime.combine(TODAY, dt.time(4, 30)), ocr="empty", month=mo)
    s, j = J("reception", "/finance/porders/api/s454/pharmacy", dict(scan=u4, yes=False))
    out["unread_nahi"] = [s, relane(u4)]
    served = "".join(G(u, p)[1] for u, p in (("reception", "/finance/porders"), ("reception", "/finance/porders?old=1"), ("reception", "/finance/porders/s454/q"),
                                              ("reception", "/finance/porders/api/state"), ("amir", "/finance/amir/step/2"), ("manoj", "/finance/purchase/page/scans")))
    out["manager_phrase"] = "manager isse theek karega" in served
    # ---- parked: September in no home row; the two rows behind the link open September only; an earlier month nowhere; a parked kind-2
    c = P4.counts(db)
    sep = P4.counts(db, "2026-09")
    out["parked"] = dict(home=c, sep=sep, aug=P4.counts(db, "2026-08"), aug_redirect=G("reception", "/finance/porders/s454/purana/2026-08")[0],
                         link='id="park_2026-09"' in G("reception", "/finance/porders")[1] if (sep["scan"] or sep["q"]) else None)
    s, h, _r = G("reception", "/finance/porders/s454/purana/2026-09")
    _save("16_purana_kaam_september.html", h)
    out["purana_page"] = [s, "Yeh zaroori nahi hai. Jab samay ho, tab kijiye." in h]
    marg_bill("W454 QSEP PHARMA", "7102", "2026-09-20", 500000)
    qs9 = scan("W454-51", "W454 QSEP PHARMA", "7102", "2026-09-20", 5600.0, dt.datetime.combine(TODAY, dt.time(5, 0)), month="2026-09")
    pa._rematch(db, "W454 walk")
    in_sep = any(x["scan"] == qs9 and x["kind"] == "amount" for x in P4.questions(db, "parked", "2026-09"))
    in_home = any(x["scan"] == qs9 for x in P4.questions(db))
    bid9 = q("SELECT id FROM purchase_bill WHERE bill_no='7102'")[0]["id"]
    s, j = J("reception", "/finance/porders/api/s454/amount", dict(scan=qs9, paper="5600"))
    out["parked_amount"] = dict(in_sep=in_sep, in_home=in_home, status=s, parked=j.get("parked"), verdict=q("SELECT verdict FROM purchase_bill WHERE id=?", bid9)[0]["verdict"],
                                state=q("SELECT amount_state FROM purchase_scan_state WHERE asset_bill_id=?", qs9), answer=q("SELECT value FROM s454_scan_answer WHERE asset_bill_id=? AND kind='amount'", qs9),
                                gone=not any(x["scan"] == qs9 for x in P4.questions(db, "parked", "2026-09")))
    # ---- the reminder: none when nothing is pending (every sheet line here was ordered on paper or closed; the orthotic keeps 0 here)
    db.execute("UPDATE porder_keep SET keep=0, source='owner'")
    db.execute("UPDATE order_sheet_line SET state='dropped' WHERE state='to_order'")
    db.commit()
    n0 = _stub_lines()
    order_rules.tick(db, now=dt.datetime.combine(TODAY, dt.time(17, 0)))
    out["remind_none"] = [_stub_lines() - n0, q("SELECT text FROM order_notice WHERE day=? AND slot='R1700'", TODAY.isoformat())]
    amir1 = _amir_rows(G, pa, db)
    out["amir_same"] = [amir0 == amir1, amir0, amir1]
    return out


def _amir_rows(G, pa, db):
    """Amir's lists, the box's own rows only (W454 scans excluded): step 2's list, his Marg sudhar card's lines, step 7's 'baaki' list."""
    s2 = G("amir", "/finance/amir/step/2")[1]
    s7 = G("amir", "/finance/amir/step/7")[1]
    acon = pa._assets_con()
    w = set()
    if acon is not None:
        w = {r[0] for r in acon.execute("SELECT id FROM bills WHERE stamp_no LIKE 'W454-%'")}
        acon.close()
    ids = sorted(int(x) for x in re.findall(r"/finance/purchase/api/scan-file/(\d+)", s2) if int(x) not in w)
    sudhar = re.findall(r"id=s444duty.*?</div></div>", s7, re.S)
    baaki = re.findall(r"<li>([^<]+)</li>", s7)
    return dict(step2=ids, sudhar=len(re.findall(r"<div class=line>", sudhar[0])) if sudhar else 0, step7=sorted(baaki))


def relane(sid):
    """'Nahi, pharmacy ka nahi': the page posts the asset app's own re-lane route -- run here on the scratch asset store, as the
    reception login (staff -> the asset app's 'reception' user), through the walk's own portal sign-in."""
    try:
        AST = os.environ["ASTDIR"]
        if AST not in sys.path:
            sys.path.insert(0, AST)
        import asset_register as ar                                    # noqa: PLC0415
        import portal as po                                            # noqa: PLC0415
        pw = json.loads(os.environ["W454J"])["pw"]
        pc = po.app.test_client(use_cookies=False)
        r = pc.post("/portal/login", base_url="https://followup.dr-manoj.in", data={"user": "reception", "password": pw["reception"]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ac = ar.app.test_client(use_cookies=False)
        r = ac.post("/bills/%d/lane" % sid, base_url="https://followup.dr-manoj.in", headers={"Cookie": "clinic_sso=" + (m.group(1) if m else "")},
                    data={"lane": "clinic", "back": "/finance/porders/s454/q"})
        a = sqlite3.connect("file:%s?mode=ro" % os.environ["ASSETS_DB"], uri=True)
        row = a.execute("SELECT lane, kind FROM bills WHERE id=?", (sid,)).fetchone()
        a.close()
        return [r.status_code, row[0] if row else None, row[1] if row else None]
    except Exception as e:                                              # noqa: BLE001
        return ["error", str(e)[:160]]


# ======================================================================= the WALK
def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--marg-new", "--marg-old", "--por", "--ast", "--shared", "--db", "--adb", "--spine", "--kit", "--duty-map",
              "--uploads", "--reader-new", "--reader-old"):
        ap.add_argument(k, required=True)
    ap.add_argument("--pictures", default="")
    a = ap.parse_args()
    for p in (a.db, a.adb, a.por):
        assert p.startswith("/tmp/"), "refusing a non-scratch path: " + p
    walk = os.path.dirname(a.db)
    n, fails = [0], []

    def check(label, cond, got=None):
        n[0] += 1
        print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(str(got))[:500] + "]") if got is not None else ""))
        if not cond:
            fails.append(label)

    def copydb(src, dst):
        s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
        d = sqlite3.connect(dst)
        s.backup(d)
        d.close()
        s.close()

    # ---- the walk's own sign-in: a random secret and its own user store in the scratch portal folder
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W454 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w454-walk-seed'\n" % secret)
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
    # ---- the readers: the medical PC's new one and its live one (the negative control)
    rn = load_reader(a.reader_new, "rn")
    ro_ = load_reader(a.reader_old, "ro")
    smp = rn.ORDER_SAMPLE
    sel = subprocess.run([sys.executable, "-B", a.reader_new, "--selftest"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    print("-- 1  the reader (marg_txt S454) on the sample of 02-Oct")
    check("its selftest passes (%d checks), the SALE and STOCK samples still themselves" % sel.stdout.count("  OK   "), "SELFTEST OK" in sel.stdout and "FAIL" not in sel.stdout,
          [l for l in sel.stdout.splitlines() if "FAIL" in l][:3])
    rows = rn.order_rows(smp)
    it = rows[2:-1]
    check("the sample is ORDER; 11 suppliers, 32 lines, 4,046 units; RAVI's four lines across the page break; the one-space name whole; KRISHNA's one line",
          rn.kind(smp) == "ORDER" and len({r[0] for r in it}) == 11 and len(it) == 32 and rows[-1][6] == 4046.0
          and [r[2] for r in it if r[0] == "RAVI MEDICAL AGENCY"] == ["DECA INSTABOLIN 50", "ETOBONE P", "MET4MIN GL 1", "OPTIFENAC TBR"]
          and any(r[2] == "KNEE IMMOBILISER UNIS" and r[3] == "1*1" for r in it) and [r[2] for r in it if r[0] == "KRISHNA MEDICOS"] == ["NARCOGEN FORTE"])
    bads = {"a line removed": smp.replace(b"  VERC 16               1*10     OP-0329   02-10-2026      10:0         -      10:0    95.25     953\n", b""),
            "the TOTAL altered": smp.replace(b"4046      4046", b"4047      4047"), "the last line cut off": smp[:smp.index(b"*** End of Report ***")],
            "a line of an unknown kind": smp.replace(b"KRISHNA MEDICOS", b"  ODD LINE\nKRISHNA MEDICOS")}
    res = {}
    for k, v in bads.items():
        try:
            rn.order_rows(v)
            res[k] = "NOT REFUSED"
        except rn.Refused as e:
            res[k] = str(e)[:80]
    check("refused, each with its reason: %s" % "; ".join("%s -> %s" % kv for kv in res.items()), all(v != "NOT REFUSED" for v in res.values()))
    check("the same sample twice gives the same bytes", rn.convert(smp)[0] == rn.convert(smp)[0], hashlib.md5(rn.convert(smp)[0]).hexdigest()[:8])
    check("NEGATIVE: the medical PC's reader as it is (S446) does not know the sheet", ro_.kind(smp) is None and rn.kind(rn.SELFTEST_SAMPLE) == ro_.kind(ro_.SELFTEST_SAMPLE) == "SALE")
    # ---- the scratch sides
    up = os.path.join(walk, "w454_uploads")
    os.makedirs(up, exist_ok=True)
    stub = os.path.join(walk, "w454_push.jsonl")

    def side_db(tag):
        d1, d2 = os.path.join(walk, "w454_%s.db" % tag), os.path.join(walk, "w454_%s_assets.db" % tag)
        copydb(a.db, d1)
        copydb(a.adb, d2)
        return d1, d2

    def run(mode, fin, mrg):
        dbp, adbp = side_db(mode)
        mdir = os.path.join(walk, "marg_%s" % mode)
        if os.path.isdir(mdir):
            shutil.rmtree(mdir)
        shutil.copytree(mrg, mdir)
        for sub in ("archive", "work"):
            if os.path.isdir(os.path.join(mdir, sub)):
                shutil.rmtree(os.path.join(mdir, sub))
        if os.path.exists(stub):
            os.remove(stub)
        env = dict(os.environ, MODE=mode, FINDIR=fin, PORDIR=a.por, MARGDIR=mdir, FINANCE_DB=dbp, ASSETS_DB=adbp, ASSETS_UPLOADS=up, FINANCE_ALLOW_HEADER_AUTH="1",
                   FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"),
                   CLINIC_SSO_SECRET=secret, REAL_DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, SHARED_LIB_DIR=a.shared, W454J=json.dumps(dict(pw=pw)),
                   KITDIR=a.kit, ORDER_PUSH_STUB=stub, READER_NEW=a.reader_new, MARG_INGEST_DIR=mdir, WALKDIR=walk, ASTDIR=a.ast, PORDERS_SOURCE="tables",
                   PICTURES=a.pictures, FINANCE_DB_FOR_SCANS=dbp)
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith("W454JSON ")]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (mode, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][9:])

    A = run("A", a.fin_new, a.marg_new)
    C = run("C", a.fin_new, a.marg_new)
    O = run("O", a.fin_old, a.marg_old)
    check("the three probes ran to the end (A, C new; O the box as it is); no phone key reached any output",
          A is not None and C is not None and O is not None and not any((x or {}).get("LEAK") for x in (A, C, O)))
    if A is None or C is None or O is None or any(x.get("LEAK") for x in (A, C, O)):
        print("WALK_S454P1 RED -- a probe did not finish, or a key reached its output")
        return 1
    print("-- 2  the road: the door, the signature, the loader")
    check("the converted sheet passes the scratch door as ORDER_PENDING VERIFIED and is loaded at once: 32 lines, 21 new under 10 suppliers, 11 old pending, 4,046 units",
          A["take1"]["type"] == "ORDER_PENDING" and A["take1"]["verdict"] == "VERIFIED" and A["sheet1"] and A["sheet1"][0]["n_lines"] == 32 and A["sheet1"][0]["n_new"] == 21
          and A["sheet1"][0]["n_old"] == 11 and A["sheet1"][0]["units_total"] == 4046 and A["sheet1"][0]["newest_date"] == D(1)
          and sorted((r["kind"], r["s"]) for r in A["lines1"] if r["kind"] == "new") == [("new", 10)], [A["take1"], A["sheet1"], A["lines1"]])
    check("RAVI's four lines across the page break, the one-space name whole, KRISHNA's single line -- as the loader holds them",
          A["ravi"] == ["DECA INSTABOLIN 50", "ETOBONE P", "MET4MIN GL 1", "OPTIFENAC TBR"] and A["knee"] and A["knee"][0]["packing"] == "1*1" and A["krishna"] == [dict(item_printed="NARCOGEN FORTE")])
    check("the same file again: ALREADY, nothing added", A["take1_again"]["status"] == "ALREADY" and A["load_twice_adds"] == 0, [A["take1_again"]["status"], A["load_twice_adds"]])
    check("NEGATIVE: the box as it is refuses the same file (no signature) and holds no order tables", O["take"]["verdict"] in ("REFUSED", "UNKNOWN") and not O["has_table"], O["take"])
    check("a sheet whose heads were altered is refused by the router; Darpan's card then reads 'adhoori'; the owner's line names it",
          A["take_bad"]["verdict"] == "REFUSED" and "ORDER_PENDING" in A["take_bad"]["reason"] and (A["darpan_bad"] or {}).get("refused") is True and A["owner_refused_line"],
          [A["take_bad"], A["darpan_bad"]])
    check("one push when a sheet arrives: 'Darpan ki order sheet aa gayi: 10 supplier, 21 dawa.' (then 10 supplier, 22 dawa for the second, which adds one)",
          A["notice1"][:1] == ["Darpan ki order sheet aa gayi: 10 supplier, 21 dawa."] and A["notice2"][-1:] == ["Darpan ki order sheet aa gayi: 10 supplier, 22 dawa."],
          [A["notice1"], A["notice2"]])
    words = A["old_words"]
    check("an old line Marg has since supplied reads 'aa chuka %s'; the others 'nahi aaya'" % A["xg_supplied"],
          words.get("XGESIC LA") == "aa chuka %s" % A["xg_supplied"] and all(v == "nahi aaya" for k, v in words.items() if k != "XGESIC LA") and len(words) >= 10, words)
    s2 = (A["sheet2"] or [{}])[0]
    check("a second sheet reprinting the first's lines with one new entry: only that line is new; its name resolves to nothing and the owner reads one line",
          s2.get("n_new") == 1 and s2.get("n_known") == 32 and "W454 ZZTEST TAB" in (s2.get("unresolved") or "") and A["unresolved_line"], [s2, A["unresolved_line"]])
    cm = A["cmp1"]
    check("the comparison is kept at the load: the system agreed on %s of %s items, with the three lists" % (cm.get("x"), cm.get("y")),
          cm.get("y") == 21 and isinstance(cm.get("x"), int) and len(cm.get("both") or []) == cm.get("x") and len(cm.get("only_sheet") or []) == 21 - cm.get("x")
          and isinstance(cm.get("only_system"), list), dict(x=cm.get("x"), y=cm.get("y"), only_system=len(cm.get("only_system") or [])))
    print("-- 3  Darpan")
    dk, dl = A["darpan_ok"] or {}, A["darpan_line"] or {}
    check("his card: '%s ki sheet mil gayi' -- 22 dawa · 10 supplier (the second sheet's order) -- and his old line counts the sheet's suppliers still to be ordered" % ddmm(D(1)),
          (dk.get("sheet") or {}).get("date") == ddmm(D(1)) and (dk.get("sheet") or {}).get("dawa") == 22 and (dk.get("sheet") or {}).get("suppliers") == 10 and dk.get("refused") is False and dl.get("unsent") == len([x for x in A["state0"]["suppliers"] if x["state"] != "in_line"
                                                                                                                     and x["sn"] != "YUVIKA SURGICALS"]),
          [dk, dl])
    print("-- 4  the home")
    hm = A["home"]
    rowk = [r[0] for r in hm["rows"]]
    check("the scan button first; a row per kind of work with its count and its name and nothing else; Purana page for the owner and Shavez only",
          hm["status"] == 200 and hm["scan_btn"] and "order" in rowk and all(r[2] in ("Order karna hai", "Maal aaya?", "Bill scan karna hai", "Photo dekh kar bataiye") for r in hm["rows"])
          and not hm["oldpage"] and A["home_shavez_oldlink"] and not A["home_darpan_oldlink"] and A["home_owner_en"] == [True, True, True], hm)
    check("the order row counts the suppliers still to be ordered (%s)" % A["state0"]["counts"]["order"],
          any(r[0] == "order" and int(r[1]) == A["state0"]["counts"]["order"] for r in hm["rows"]) and A["state0"]["counts"]["order"] >= 10, A["state0"]["counts"])
    print("-- 5  Order karna hai")
    li = A["list"]
    check("the list: whose order and its date, Sab ko WhatsApp bhejo, Order sheet print karo, the call line, cards with Kholiye + Order ho gaya, 'Baaki N supplier', 'Purane pending: N'",
          li["whose"] and li["whose"][0].startswith("Darpan ka order · %s · " % ddmm(D(1))) and li["wa"] and li["printb"] and li["callnote"] and li["cards"] == 4
          and li["two"] == 4 and li["more"] and li["oldlink"], li)
    check("the phone silent: the WhatsApp button drawn disabled with 'Reception phone set nahi hai — call se order kijiye'", li["wa_disabled"] and li["waoff"], li)
    ko = A["kedar_order"]
    check("'Order ho gaya' on KEDAR's card: one order, sent, by 'Shivani (Reception)', its six lines, Marg's entries OP-0326,OP-0332; the card gone",
          A["kedar1"][:2] == [200, True] and len(ko) == 1 and ko[0]["status"] == "sent" and ko[0]["by"] == "Shivani (Reception)" and ko[0]["n"] == 6 and ko[0]["via"] == "call"
          and ko[0]["ext"] == "OP-0326,OP-0332" and A["kedar_card_gone"], [A["kedar1"], ko])
    check("a second tap within ten minutes: no second order", A["kedar2"][0] == 200 and A["kedar2"][2] is True and A["kedar2"][3] == 1, A["kedar2"])
    dp = A["deepam"]
    check("Kholiye (DEEPAM): the medicines in the order's unit ('20 strip', '10 strip'); a tel: link and the number shown under it; the call line; Order ho gaya; Quantity badalni hai?",
          dp["status"] == 200 and dp["lines"] == [["TENDOZAC TAB", "20 strip"], ["VERC 16", "10 strip"]] and dp["tel"] and dp["num_shown"] and dp["baat"] and dp["ordered"] and dp["qty"],
          dp["lines"])
    check("the Call tap writes one audit row; the card then reads '2 dawa · call kiya tha, order baaki'", A["call"] == 200 and A["call_audit"] == 1 and A["called_card"])
    check("a supplier with no number (RAVI): no Call, 'Is supplier ka phone number yahan nahi hai', Order ho gaya still there; the owner's line",
          A["ravi_page"] == [True, True, True] and A["ravi_owner_line"], [A["ravi_page"], A["ravi_owner_line"]])
    check("the phone silent: 'Sab ko WhatsApp bhejo' refused (409); the owner's line appears once someone has met the disabled button, not before (never a standing line)",
          A["wa_silent"][0] == 409 and A["wa_silent"][1] == "phone_off" and not A["phone_line_before"] and A["phone_line_met"] and A["owner_phone_line"][1],
          [A["phone_line_before"], A["phone_line_met"], A["owner_phone_line"]])
    check("no key set: the same refusal", A["wa_nokey"] == [409, "no_key"], A["wa_nokey"])
    wm = A["wa_msgs"]
    check("the phone alive: one order (a draft) and one queued message of kind 'order' per supplier with a number; none for RAVI; no payment count moved",
          A["wa_enabled"] and A["wa_all"][0] == 200 and wm["n"] == A["wa_all"][1] and wm["n"] == wm["drafts"] and not wm["ravi"] and wm["one_each"] and wm["n"] >= 8
          and "RAVI MEDICAL AGENCY" in (A["wa_all"][2] or []) and A["pay_unchanged"][0], [A["wa_all"], wm, A["pay_unchanged"]])
    b = A["body"]
    check("the message: the shop's heading, then a line per medicine in qty_words (never 'units'); the changed quantity in it (AURAB L CAP — 11 strips, the order line 11); "
          "no old line in any message; JSON-safe across its lines", b["aurab"] and b["head"] and b["lines"] >= 2 and not b["units"] and not b["old_in_msg"] and b["json_ok"]
          and [x["packs"] for x in A["aurab_line"]] == [11], [b, A["aurab_line"]])
    si = A["state_inline"]
    check("while a message waits its supplier is in the line: not pending (the order row counts the rest), not under Maal aaya?; the page says 'WhatsApp line mein hai'",
          len(si["inline"]) == wm["n"] and si["order"] == len(wm["pending_before"]) - wm["n"] and A["inline_word"], si)
    check("the queue's next hands a message once and not again within the gap (F-702)", A["next"][0] == 200 and A["next"][2] and A["next"][3], A["next"])
    check("NEGATIVE: the box as it is hands the same message twice", O["next_twice"][2] is True, O["next_twice"])
    ap_ = A["after_phone"]
    check("the phone's 'sent' makes DEEPAM ordered (via whatsapp); 'failed' and silence past the hour withdraw DRUG DEAL's and GUNINA's: pending again",
          A["done_ok"] == 200 and A["done_fail"] == 200 and ap_["deepam"] == [dict(status="sent", order_via="whatsapp")] and ap_["deepam_gone"]
          and ap_["drug_state"] == "withdrawn" and ap_["gunina_state"] == "withdrawn", ap_)
    check("the list then says 'WhatsApp nahi gaya — call kijiye', and the green line how many went and who sent", A["wa_no_word"] and A["green_line"]
          and A["green_line"][0][0].startswith("WhatsApp chala gaya: 1 supplier") and A["green_line"][0][1].endswith("Shivani (Reception) ne bheja"), A["green_line"])
    check("'Order ho gaya' then confirms DRUG DEAL's same order: one order, sent", A["drug_confirm"][0] == 200 and A["drug_confirm"][2] == 1 and A["drug_confirm"][3] == "sent", A["drug_confirm"])
    check("no supplier is in two places (pending / in the line / ordered)", A["exclusive"] == [], A["exclusive"])
    check("Quantity +1 accepted; an old line ordered again joins its supplier's card as a line of today; Remove puts it back among the old pending",
          A["qty_plus"] == 200 and A["reorder"] == 200 and A["reorder_in_card"] and A["reorder_removed"][0] == 200 and A["reorder_removed"][1] is True and A["reorder_removed"][2] == "old",
          [A["reorder_in_card"], A["reorder_removed"]])
    check("the old pending: a block apart on the supplier's screen; the foot link lists all of them, each with 'Dobara order karo'",
          A["janta_old_block"][0] and A["janta_old_block"][1] == 2 and A["oldpage"]["n"] == A["oldpage"]["btn"] and A["oldpage"]["n"] >= 9, [A["janta_old_block"], A["oldpage"]])
    rm = A["remind_1700"]
    check("the reminder: none at 12:00 or 15:00; on marg_sheet none at 09:00; ONE notice at 17:00 (to each of order.notice_to) naming those still to order, not again at 17:10",
          A["remind_noon"] == 0 and A["remind_0900"] == 0 and len(A["remind_rows"]) == 1 and rm["n"] == len(A["notice_to"]) and rm["text"].startswith("Order baaki: ")
          and rm["names_ok"], [A["remind_noon"], A["remind_0900"], rm, A["remind_rows"], A["notice_to"]])
    check("frozen: the order row is not shown and the routes refuse (423)", A["frozen"][0] and A["frozen"][1] == 423 and A["frozen"][2] == "frozen", A["frozen"])
    sy = A["system"]
    check("order.source = system: the day's proposals are the lines to order ('System ka order'), the sheet's lines are not; ordering one sends its proposal",
          sy["sys_card"] and sy["no_sheet"] and sy["whose"] and sy["whose"][0].startswith("System ka order") and A["system_ordered"][0] == 200
          and A["system_ordered"][1] == [dict(status="sent", linked=1)], [sy, A["system_ordered"]])
    if A["ortho_short_n"]:
        oc = A["ortho_card"]
        check("the orthotic shortage card (S403) on both settings; with the sheet's own line for that supplier it is ONE card, the item once, at the sheet's quantity",
              sy["ortho"] and A["sheet_ortho"] and oc["one"] and oc["item_once"] and oc["sheet_qty"], [oc, sy["ortho"], A["sheet_ortho"]])
    print("-- 6  the printed order sheet")
    p0, p1 = A["pdf0"], A["pdf1"]
    check("an A4 PDF of ONE page for the sample's new lines (old lines off, order.sheet_print_old = 0): every medicine and its quantity in the text, one row of heads, "
          "RAVI '(number nahi hai)', the foot", p0["status"] == 200 and p0["ctype"] == "application/pdf" and p0["pages"] == 1 and p0["old_rows"] == 0 and p0["all_items"]
          and p0["all_qty"] and p0["ravi_nonum"] and p0["heads"] == 1 and p0["foot"], p0)
    check("with the old lines on: each tagged 'purana, dd-mm' with what the system knows, NO box under Order (Order boxes = new rows only), 'Sirf purane pending', no block split",
          p1["old_rows"] >= 9 and p1["old_tags"] == p1["old_rows"] and p1["order_boxes"] == p1["new_rows"] and p1["aaya_boxes"] == p1["new_rows"] + p1["old_rows"]
          and p1["sirf"] and p1["tag_in_text"] and not p1["split"], p1)
    print("-- 7  the owner's cards and the settings")
    oc = A["owner_cards"]
    check("on the old page, for the owner: who decides (with its switch), the agreement line, the old pending orders, the sheet's state, the settings card",
          oc["src"] and oc["cmp"] and oc["old"] and oc["sheet"] and oc["settings"] and oc["oldpage"], oc)
    check("reception's old page: today's page, no settings card", A["reception_old"] == [200, True, False], A["reception_old"])
    st = A["settings"]
    check("each of the %d keys of part 1 changed on the owner's card, taking effect, and put back" % A["n_settings"],
          all(v[0] == 200 and v[1] and v[2] and v[3] == 200 and v[4] for v in st.values()), {k: v for k, v in st.items() if not (v[0] == 200 and v[1] and v[2] and v[3] == 200 and v[4])})
    check("an audit row for every change (%d)" % A["settings_audit"], A["settings_audit"] == 2 * A["n_settings"])
    check("a bad value and an unknown key refused; reception and darpan cannot change a setting", A["settings_bad"] == [400, 400, 403, 403], A["settings_bad"])
    print("-- 8  as already ordered: the first load of 02-Oct")
    check("the first load 'as already ordered': one order per supplier (10), made on paper at 15:00 the sheet's day, awaiting arrival; no card under 'Order karna hai'",
          C["first"]["made"] == 10 and C["paper"]["n"] == 10 and C["paper"]["when"] == ["%sT15:00:00" % D(1)] and C["paper"]["status"] == ["sent"] and C["paper_no_card"], [C["first"], C["paper"]])
    check("Maal aaya?: a card per order with 'Order %s · N dawa', Bill scan karo, 'Bill nahi hai, ya kam aaya?'" % ddmm(D(1)),
          C["maal"]["cards"] >= 10 and ddmm(D(1)) in C["maal"]["dates"] and C["maal"]["nobill"] == C["maal"]["cards"], C["maal"])
    check("a crafted Marg purchase clears its line (billed, supplied)", C["paper_cleared"] and C["paper_cleared"][0]["billed_qty"] == 20 and C["paper_cleared"][0]["supplied"] == 20, C["paper_cleared"])
    check("a new line never ticked that Marg has supplied: closed 'aa chuka, bina order ke', no order; its supplier's card gone",
          C["take_tiny"]["verdict"] == "VERIFIED" and C["tick_card0"] and C["tick_closed"][0] and C["tick_closed"][0][0]["state"] == "closed_marg" and C["tick_closed"][1], C["tick_closed"])
    check("a new line eight days old and never ordered: old pending (lapsed), and the owner reads one line", C["lapsed"][0] == [dict(state="lapsed")] and C["lapsed"][1], C["lapsed"])
    check("an old 'aa chuka' line on its eighth day and a 'nahi aaya' line on its sixty-first: gone from the staff's block and sheet, still on the owner's list (the day before: shown)",
          C["visibility"] == [True, True, True, True] and C["visibility_day_before"] == [True, True], [C["visibility"], C["visibility_day_before"]])
    print("-- 9  arrival by the bill's scan")
    t1 = C["tie1"]
    check("a scan of an awaited supplier after the order: the order has arrived ('bill scan W454-11'), its lines still open, in transit, no 'Scan karo' for it",
          t1["status"] == "received" and t1["by"] == "bill scan W454-11" and t1["open"] >= 4 and t1["transit"] and not t1["scan_karo"] and t1["tie"], t1)
    check("... and its open lines still count (S403's shortage, S410's interim check) until Marg's bill answers them; the old query (status 'sent' only) "
          "would have dropped them", t1["onord403"] and t1["onord410"] and t1["control"] == 0, t1)
    check("a second scan of that supplier is tied to the next order", C["tie2"] == [dict(order_id=C["k2"])], C["tie2"])
    to = C["tie_older"]
    check("an older order received on the arrival screen and unscanned + a newer awaited: the scan goes to the older; the newer still awaited",
          to[0] == [dict(order_id=to[1])] and to[3] == "sent", to)
    tn = C["tie_newer"]
    check("the older past its seven days, or replaced by its Marg bill's line: the scan goes to the newer", tn[0] == [dict(order_id=tn[1])] and tn[2] == [dict(order_id=tn[3])], tn)
    check("a scan made before the order, a bill dated before the order's day, a merely similar spelling: no tie; the same date in another year: tied by day and month",
          C["no_tie"] == dict(before_order=True, bill_before=True, wrong_year=True, similar=True), C["no_tie"])
    check("a supplier filled in after the scan was made is tied at the next cron run, with no page opened", C["late0"] and C["late1"], [C["late0"], C["late1"]])
    mr = C["marg_records"]
    check("afterwards Marg's bill records ordered against supplied on the open lines", mr and mr[0]["billed_qty"] == 15 and mr[0]["supplied"] == 15 and mr[0]["short"] == 1, mr)
    un = C["unticked"]
    check("a supplier never ticked whose bill is scanned after the sheet's load: one order 'by the bill's scan', arrived, its card gone; scanned before the load, or a bill dated "
          "before the sheet: nothing", un["order"] and un["order"][0]["status"] == "received" and un["order"][0]["order_via"] == "scan" and un["card_gone"] and un["early"] and un["oldbill"], un)
    check("an unread paper ties nothing before its 'Haan', and ties after it", C["unread_tie"] == [False, True], C["unread_tie"])
    check("a re-run of the matcher loses no tie", C["rematch_keeps"][0] == C["rematch_keeps"][1] and C["rematch_keeps"][0] >= 8, C["rematch_keeps"])
    print("-- 10  the arrival screen")
    ar_ = C["arrival_page"]
    check("from the small link: every line shown received, 'Jo kam aaya ya nahi mila, us par tap kijiye.', Maal aa gaya, Abhi nahi aaya", ar_["status"] == 200 and ar_["all_ticked"]
          and ar_["tap"] and ar_["maalok"] and ar_["abhinahi"], ar_)
    check("all received in one tap; one line short (4) and one 'Nahi mila' saved by today's rules; 'Abhi nahi aaya' saves nothing",
          C["arrive_all"][0] == 200 and C["arrive_all"][1] == "received" and C["arrive_all"][2] >= 1 and C["arrive_diff"][0] == 200 and C["arrive_diff"][2] == "received"
          and C["arrive_diff"][1][0] == dict(supplied=4, short=1, missing=0) and C["arrive_diff"][1][1] == dict(supplied=0, short=1, missing=1) and C["abhi_nahi"] == "sent",
          [C["arrive_all"], C["arrive_diff"], C["abhi_nahi"]])
    check("then 'Maal darj ho gaya', 'Bill abhi scan karna hai?' with Bill scan karo and Baad mein; 'Baad mein' puts it under 'Bill scan karna hai'",
          C["after_screen"] == [True, True, True, True] and C["baad_mein"]["ravi"] and C["baad_mein"]["shr"], [C["after_screen"], C["baad_mein"]])
    lv = C["leaves"]
    check("it leaves on its scan; on a Marg bill of that supplier (whose own line takes its place, the count unchanged); on the eighth day",
          lv["on_scan"] and lv["on_bill"] and lv["count_same"] and C["eighth_day"] == [True, False], [lv, C["eighth_day"]])
    print("-- 11  Bill scan karna hai")
    sp = C["scan_page"]
    check("grouped by supplier ('W454 SCAN PHARMA · 7 bill'), five lines at a time and 'Agle 5 dikhaiye', the grey line saying which kind, 'Koi paper nahi mil raha?'",
          sp["shown"] == 5 and sp["agle"] and sp["nopaper"] and any(g.endswith(" bill") for g in sp["groups"]) and C["scan_more"] > 5, [sp, C["scan_more"]])
    check("the tick list holds Marg-bill lines only; 'Paper nahi mila' takes a line off and records it", C["tick_list"]["n"] >= 7 and C["tick_list"]["only_marg"]
          and C["paper_missing"] == [200, True, True], [C["tick_list"], C["paper_missing"]])
    print("-- 12  Photo dekh kar bataiye")
    qk = C["q_kinds"]
    check("kinds 1, 2, 3 and S441's in the queue; a paired scan whose date differs makes no card", qk["q1"] == "bill" and qk["q2"] == "amount" and qk["q3"] == "vendor"
          and qk["q5"] == "s441" and qk["q4"] is None and qk["q4_linked"], qk)
    check("a scan of a bill that already has its scan: 'Kya yeh W454 QFOUR PHARMA ke bill 4004 ka doosra scan hai?'", C["doosra"] == dict(kind=["bill"], taken=[True], wording=True), C["doosra"])
    check("one question on the screen, 'Sawaal 1 / N', 'Baad mein'; the kinds walked: %s" % ", ".join(C["seen_kinds"]),
          C["q_page"]["status"] == 200 and C["q_page"]["sawaal"] and C["q_page"]["sawaal"][0].startswith("Sawaal 1 / ") and C["q_page"]["one"] == 1 and C["q_page"]["later"]
          and {"bill", "amount", "vendor", "s441"} <= set(C["seen_kinds"]), C["q_page"])
    ac_ = C.get("amount_card") or {}
    check("the amount card: two amounts, not labelled as Marg's or the scan's, and 'Koi aur amount'", ac_.get("buttons") == 2 and not ac_.get("labelled") and ac_.get("koiaur"), ac_)
    lm = C.get("later_moves") or [None, None, False]
    check("'Baad mein' sends a card to the end of the queue", lm[0] != lm[1] and lm[2], lm)
    check("'Haan' on 'Kya yeh ... ka bill ... hai?' pairs it (S440's own meaning)", C["confirm_q1"] == [200, True], C["confirm_q1"])
    print("-- 13  a paper with no bill number and no amount (F-695)")
    u = C["unread"]
    check("it is a card 'Kya yeh dawa (pharmacy) ka bill hai?', not in Marg ka intezaar, not on Amir's list or in its count", u["card"] == ["pharmacy"] and not u["wait"]
          and not u["amir_list"] and u["held"] == ["unread paper"], u)
    check("NEGATIVE: the box as it is puts such a paper in 'Marg ka intezaar' with 'manager isse theek karega'", O["old_wait_note"] is True, O["old_wait_note"])
    check("'manager isse theek karega' is in no served page", not C["manager_phrase"])
    check("'Haan' with the supplier unknown: the supplier card next; chosen, it pairs with no Marg bill by itself", C["unread_next"] == ["vendor"] and C["unread_vendor"] == 200
          and C["unread_after_vendor"] == [] and C["unread_no_pair"], [C["unread_next"], C["unread_after_vendor"]])
    check("with one Marg bill of its supplier inside the window a kind-1 card, its 'Haan' pairs it 'paired by reception; nothing was read on the paper'; with two, none",
          C["unread_one_bill"] == ["bill"] and (C.get("unread_paired") or [0, []])[0] == 200
          and (C.get("unread_paired") or [0, [{}]])[1][0].get("matched_on") == "paired by reception; nothing was read on the paper" and C["unread_two_bills"] == [],
          [C["unread_one_bill"], C.get("unread_paired"), C["unread_two_bills"]])
    check("'Nahi': it is in the clinic lane on the scratch asset store (the asset app's own re-lane route)", C["unread_nahi"][0] == 200 and C["unread_nahi"][1][1:] == ["clinic", "Consumable"]
          if isinstance(C["unread_nahi"][1], list) else False, C["unread_nahi"])
    print("-- 14  September parked")
    pk = C["parked"]
    check("September's work is in no home row; behind 'Purana kaam: September' the two rows open September only; August (not named) shows nowhere",
          pk["sep"]["scan"] + pk["sep"]["q"] > 0 and pk["link"] and pk["aug"] == dict(scan=0, q=0) and pk["aug_redirect"] == 302 and C["purana_page"] == [200, True], pk)
    pa_ = C["parked_amount"]
    check("a kind-2 answer in September raises nothing for Amir (no WRONG on the bill, no S440 amount state); recorded for the register; the card gone",
          pa_["in_sep"] and not pa_["in_home"] and pa_["status"] == 200 and pa_["parked"] and pa_["verdict"] is None and pa_["state"] in ([], [dict(amount_state=None)])
          and pa_["answer"] == [dict(value="560000")] and pa_["gone"], pa_)
    check("the reminder: none when nothing is pending (decided once, silent)", C["remind_none"][0] == 0 and C["remind_none"][1] == [dict(text="(silent: nothing pending)")], C["remind_none"])
    a0, o0 = A["amir0"], O["amir0"]
    check("Amir's step 2 list, his Marg sudhar card and his step 7 on the box's own data: the same with the kit as without it (nothing added, nothing removed)",
          a0 == o0, [a0, o0])
    print("-- 15  the staff-eye walk (DUTY_MAP.json v4)")
    for who in ("reception", "darpan", "shavez", "amir", "manoj"):
        e = A["eye"][who]
        missing = [d["id"] for d in e["duties"] if d["tile"] and not d["tile_seen"]]
        unseen = [d["id"] for d in e["duties"] if d.get("door_seen") is False]
        errs = [d["id"] for d in e["duties"] if isinstance(d.get("due_n"), str)]
        due = [(d["id"], d["due_n"]) for d in e["duties"] if isinstance(d.get("due_n"), int) and d["due_n"] > 0]
        check("%s: %d duties; every tile on the home; every due duty's door shows it (%s)" % (who, len(e["duties"]), ", ".join("%s %s" % x for x in due) or "none due"),
              e["status"] == 200 and e["duties"] and not missing and not unseen and not errs, dict(missing=missing, unseen=unseen, errors=errs))
    rc = {d["id"]: d for d in A["eye"]["reception"]["duties"]}
    check("reception's order duty is due on the scratch copy and 'Order karna hai' shows on its home", isinstance(rc["reception.medicine_orders"]["due_n"], int)
          and rc["reception.medicine_orders"]["due_n"] > 0 and rc["reception.medicine_orders"].get("door_seen") is True, rc["reception.medicine_orders"])
    print("-- 16  NEGATIVE CONTROL: the box as it is")
    check("NEGATIVE: /finance/porders is today's page for reception", O["home_is_old"] == [200, True, False], O["home_is_old"])
    check("NEGATIVE: Amir's list as it is holds an unread paper (when its supplier is known) or the matcher's wait list does", O["old_wait_note"] or O["old_amir_has_unread"])
    check("a parked month raises no Needs-you: no 'Bill scan pending' line for September's bills (the box as it is raises one)", A["scan_needs"] == [] and bool(O["scan_needs"]),
          [A["scan_needs"], O["scan_needs"]])
    print("WALK_S454P1 %s -- %d of %d passed" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0]))
    for f in fails:
        print("   FAILED: " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        sys.exit(main())
