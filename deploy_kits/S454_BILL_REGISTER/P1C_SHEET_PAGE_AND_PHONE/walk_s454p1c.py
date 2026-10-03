#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p1c.py -- kit S454_BILL_REGISTER, part 1C (S454 17): THE REAL finance app over SCRATCH COPIES of finance.db and assets.db (backup
API), through Flask's test client, one process per side:

  NEW  the finance files with the built supplier_msg.py, porders_s454.py, order_sheet.py, order_sheet_pdf.py (v1.1)
  OLD  the box as it is -- the NEGATIVE CONTROL

  1  the printed sheet: every piece of text inside its own cell and inside the page's margins, MEASURED from the PDF's own text positions and
     the font's widths (clinic_day_pdf's AFM tables) -- on the order as it stands live (a copy), and with crafted rows: a medicine name of 30
     characters with an old-pending tag, a supplier with two phone numbers and a long name, a supplier with none, an order long enough for a
     second page; the head line's counts against the rows drawn; every line under "Maal aaya?" on the page with its Order box ticked; after a
     crafted scan of one awaited supplier's bill (the tie), that supplier gone from the page; order.sheet_print_old = 0.
  2  "1 medicine" (the owner's English), "1 dawa".
  3  the "Reception phone" card (the owner only), the test number (masked), the test message (handed once, sent, failed with the reason, never
     retried), counted nowhere else; payment and order messages handed out exactly as before (the same rows in the same order, NEW = OLD).
  4  the data steps of 17.9 (message 1 put back, only if it still reads sent at 15:00:27 by reception-phone) and 17.10 (alive 720 minutes);
     the owner's and the staff's lines when the phone has been dark an hour (and twelve); the setup page's steps.
Its own rows are keyed W454C (suppliers 'W454C ... PHARMA'); every date is computed from today; no phone number and no key reaches its output
(a run of ten digits is masked; the walk stops red if the key string reaches it). The walk's test number is made at run time.

  --fin-new DIR --fin-old DIR --por DIR --db PATH --adb PATH --work DIR [--pictures DIR]
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

TODAY = dt.date.today()
NOW = dt.datetime.now().replace(microsecond=0)
USERS = {"reception": "staff", "darpan": "staff", "shavez": "manager", "amir": "staff", "manoj": "doctor", "shivani": "staff"}
TAG = "W454CJSON "
MM = 72.0 / 25.4
LM, RM, TOP, BOT = 12 * MM, 595.28 - 12 * MM, 841.89 - 11 * MM, 11 * MM


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


# ======================================================================= the PDF, measured
def pdf_pages(pdf):
    """[[op line]] per page content stream (the hand-written PDF: one op per line)."""
    out = []
    for m in re.finditer(rb"stream\n(.*?)\nendstream", pdf, re.S):
        body = m.group(1)
        if b" Tj ET" in body or b" re S" in body:
            out.append(body.split(b"\n"))
    return out


RX_T = re.compile(rb"^BT /F(\d) ([\d.]+) Tf 0 g ([-\d.]+) ([-\d.]+) Td \((.*)\) Tj ET$")
RX_R = re.compile(rb"^([\d.]+) w ([\d.]+) G ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) re S(?: % (\S+))?$")
RX_L = re.compile(rb"^([\d.]+) w ([\d.]+) G ([-\d.]+) ([-\d.]+) m ([-\d.]+) ([-\d.]+) l S$")
RX_K = re.compile(rb"^[\d.]+ w [\d.]+ G ([-\d.]+) ([-\d.]+) m .* l S % tick-(\S+)$")


def sp(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def unesc(b):
    return b.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\").decode("cp1252")


def measure(pdf, cdp):
    """{pages:[{texts, rects, rows, bands, ticks}], bad:[(page, text, why)]} -- every text against its cell and the page's margins."""
    res = dict(pages=[], bad=[])
    for pi, ops in enumerate(pdf_pages(pdf), 1):
        texts, rects, vlines, ticks = [], [], [], []
        for op in ops:
            op = op.strip()
            m = RX_T.match(op)
            if m:
                s = unesc(m.group(5))
                size = float(m.group(2))
                texts.append(dict(s=s, font=int(m.group(1)), size=size, x=float(m.group(3)), y=float(m.group(4)),
                                  w=cdp._width(s, size, m.group(1) == b"2")))
                continue
            m = RX_R.match(op)
            if m:
                rects.append(dict(lw=float(m.group(1)), gray=float(m.group(2)), x=float(m.group(3)), y=float(m.group(4)), w=float(m.group(5)),
                                  h=float(m.group(6)), tag=(m.group(7) or b"").decode()))
                continue
            m = RX_L.match(op)
            if m and abs(float(m.group(3)) - float(m.group(5))) < 0.01:
                vlines.append(dict(x=float(m.group(3)), y1=min(float(m.group(4)), float(m.group(6))), y2=max(float(m.group(4)), float(m.group(6)))))
                continue
            m = RX_K.match(op)
            if m:
                ticks.append(dict(x=float(m.group(1)), y=float(m.group(2)), tag=m.group(3).decode()))
        big = [r for r in rects if r["w"] > 30 and r["h"] > 8]
        small = [r for r in rects if r["w"] < 15]
        for t in texts:
            x0, x1, y0, y1 = t["x"], t["x"] + t["w"], t["y"] - 0.21 * t["size"], t["y"] + 0.70 * t["size"]
            if x0 < LM - 0.5 or x1 > RM + 0.5 or y0 < BOT - 0.5 or y1 > TOP + 0.5:
                res["bad"].append((pi, t["s"], "outside the page's margins (x %.1f..%.1f of %.1f..%.1f)" % (x0, x1, LM, RM)))
                continue
            cands = [r for r in big if r["x"] - 0.01 <= x0 <= r["x"] + r["w"] and r["y"] - 0.01 <= t["y"] <= r["y"] + r["h"]]
            if not cands:
                continue
            r = min(cands, key=lambda r: r["w"] * r["h"])
            ls = [v["x"] for v in vlines if r["x"] + 0.01 < v["x"] < r["x"] + r["w"] - 0.01 and v["y1"] - 0.01 <= t["y"] <= v["y2"] + 0.01]
            left = max([v for v in ls if v <= x0 + 0.01] or [r["x"]])
            right = min([v for v in ls if v > x0 + 0.01] or [r["x"] + r["w"]])
            if x1 > right - 0.2:
                res["bad"].append((pi, t["s"], "runs past its cell's right edge by %.1f pt" % (x1 - right)))
            elif y0 < r["y"] - 0.2 or y1 > r["y"] + r["h"] + 0.2:
                res["bad"].append((pi, t["s"], "runs out of its row"))
            else:
                for b in small:
                    if r["x"] <= b["x"] <= r["x"] + r["w"] and r["y"] <= b["y"] <= r["y"] + r["h"]:
                        if x0 < b["x"] + b["w"] and x1 > b["x"] and y0 < b["y"] + b["h"] and y1 > b["y"]:
                            res["bad"].append((pi, t["s"], "runs into a box"))
                            break
        rows = [r for r in big if abs(r["gray"] - 0.25) < 0.01]
        bands = [r for r in big if abs(r["lw"] - 0.9) < 0.01 and r["gray"] == 0.0]
        prow = []
        for r in rows:
            inside = [t for t in texts if r["x"] <= t["x"] <= r["x"] + r["w"] and r["y"] <= t["y"] <= r["y"] + r["h"]]
            prow.append(dict(text=" ".join(t["s"] for t in sorted(inside, key=lambda t: (-t["y"], t["x"]))),
                             item=" ".join(t["s"] for t in sorted(inside, key=lambda t: (-t["y"], t["x"])) if t["x"] < LM + 66 * MM and t["font"] != 3),
                             old=any(t["font"] == 3 and t["s"].startswith("purana") for t in inside),
                             ticked=any(k["tag"] == "col-order" and r["y"] <= k["y"] <= r["y"] + r["h"] for k in ticks)))
        pband = []
        for r in bands:
            inside = [t for t in texts if r["x"] <= t["x"] <= r["x"] + r["w"] and r["y"] <= t["y"] <= r["y"] + r["h"] and t["font"] == 2]
            first = sorted(inside, key=lambda t: (-t["y"], t["x"]))[:1]
            pband.append(dict(name=first[0]["s"] if first else "", ticks=sorted(k["tag"] for k in ticks if k["tag"].startswith("band-")
                                                                                   and r["y"] <= k["y"] <= r["y"] + r["h"])))
        res["pages"].append(dict(rows=prow, bands=pband, head=[t["s"] for t in texts if t["s"].startswith("Order: ")][:1]))
    return res


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
    import order_sheet as OS                                           # noqa: E402
    import order_sheet_pdf as OP                                       # noqa: E402
    import supplier_msg as SM                                          # noqa: E402
    import porders_s454 as PS                                          # noqa: E402
    import clinic_day_pdf as cdp                                       # noqa: E402
    assert OS.__file__.startswith(FIN) and SM.__file__.startswith(FIN), (OS.__file__, SM.__file__)
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    db.row_factory = sqlite3.Row
    adb = sqlite3.connect(os.environ["ASSETS_DB"], timeout=60)
    adb.row_factory = sqlite3.Row
    out = {}
    walk_tok = secrets.token_hex(24)
    test_num = "9" + "0" * 5 + "4321"                                  # the walk's own test number, made here (never a real one)

    def H(u):
        h = {"X-Clinic-User": u, "X-Clinic-Role": ""}
        if u == "reception":
            h["Cookie"] = "clinic_who=shivani"
        return h

    def G(u, p):
        r = fc.get(p, base_url=BASE, headers=H(u))
        return r.status_code, r.get_data(as_text=True)

    def J(u, p, body=None):
        r = fc.post(p, base_url=BASE, headers=H(u), json=body if body is not None else {})
        return r.status_code, (r.get_json(silent=True) or {})

    def phone(path, body=None):
        h = {"X-Phone-Token": walk_tok}
        r = fc.post(path, base_url=BASE, headers=h, json=body) if body is not None else fc.get(path, base_url=BASE, headers=h)
        return r.status_code, (r.get_json(silent=True) or {}), r.get_data()

    def setv(k, v):
        db.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
        db.commit()

    def text(h):
        h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h or "", flags=re.S)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'").strip()

    setv("supplier_msg.phone_token", walk_tok)
    setv("supplier_msg.phone_last", "%s 200" % NOW.isoformat())
    OS.ensure(db)
    SM.ensure(db)

    # ---- 1  the printed sheet on the live order (a copy)
    import porders_s454 as PS2                                         # noqa: E402
    maal = PS2.maal_orders(db)
    awaited_items = []
    for o in maal:
        for l in db.execute("SELECT item FROM purchase_order_line WHERE order_id=? AND supplied IS NULL", (o["id"],)):
            awaited_items.append((o["vendor"], l[0]))
    pdf0 = OP.build(db)
    m0 = measure(pdf0, cdp)
    rows0 = [r for p in m0["pages"] for r in p["rows"]]
    out["live"] = dict(pages=len(m0["pages"]), bad=[(p, mask(s), w) for p, s, w in m0["bad"]], rows=len(rows0),
                       old=sum(1 for r in rows0 if r["old"]), ticked=sum(1 for r in rows0 if r["ticked"]),
                       bands=[b["name"] for p in m0["pages"] for b in p["bands"]], head=[mask(h) for p in m0["pages"] for h in p["head"]],
                       awaited=len(awaited_items),
                       awaited_on_page=sum(1 for v, it in awaited_items if any(sp(it) in sp(r["text"]) and r["ticked"] for r in rows0)),
                       awaited_missing=[it for v, it in awaited_items if not any(sp(it) in sp(r["text"]) and r["ticked"] for r in rows0)][:8])
    if NEW:
        lay = OP.layout(db)
        out["live"]["counts"] = lay["counts"]
        out["rows_per_page"] = OP.rows_per_page()
        out["live"]["band_ticks"] = [(b["name"], b["ticks"]) for p in m0["pages"] for b in p["bands"]]

    # ---- crafted rows: a 30-character name with an old tag, two phone numbers and a long name, no number, a long order
    p1 = "9" + "1" * 9
    p2 = "8" + "2" * 9
    sid = ins(db, "order_sheet", dict(md5="w454c-%s" % secrets.token_hex(6), name="W454C walk", source="walk", stamp="", taken_at=NOW.isoformat(),
                                      newest_date=TODAY.isoformat(), n_lines=0, n_new=0, n_old=0, n_known=0, n_suppliers=0, as_ordered=0))
    two = "W454C TWO PHONE PHARMACEUTICALS PRIVATE LIMITED"
    nophone = "W454C NO PHONE PHARMA"
    ins(db, "purchase_vendor_contact", dict(vendor_norm=pa.supplier_key(two), phone=p1, phone2=p2), replace=True)
    k = [0]

    def line(sup, item, state, kind, days_ago=0, qty=10):
        k[0] += 1
        d = (TODAY - dt.timedelta(days=days_ago)).isoformat()
        return ins(db, "order_sheet_line", dict(entry_no="W454C-%03d" % k[0], item_printed=item[:21], item=item, resolved=0, supplier=sup,
                                                supplier_norm=pa.supplier_key(sup), packing="1*10", pack_size=10, line_date=d, qty_raw="%d:0" % qty, qty=qty,
                                                loose=0, strip=1, units=qty * 10, rate_p=1000, value_p=qty * 1000, kind=kind, state=state, first_sheet=sid,
                                                last_sheet=sid, created_at=NOW.isoformat()))
    name30 = "W454C THIRTY CHARACTER NAME XY"
    assert len(name30) == 30
    line(two, "W454C TWO TAB", "to_order", "new")
    line(two, name30, "old", "old", days_ago=12)
    line(nophone, "W454C ALONE CAP", "to_order", "new")
    db.commit()
    pdf1 = OP.build(db)
    m1 = measure(pdf1, cdp)
    rows1 = [r for p in m1["pages"] for r in p["rows"]]
    out["crafted"] = dict(bad=[(p, mask(s), w) for p, s, w in m1["bad"]], pages=len(m1["pages"]),
                          name30_whole=any(r["item"] == name30 for r in rows1),
                          two_band=[b["name"] for p in m1["pages"] for b in p["bands"] if b["name"].startswith("W454C TWO")],
                          nophone_text=("(number nahi hai)" in " ".join(OP.text_of(pdf1))))
    for s_ in ("A", "B", "C"):
        for i in range(16):
            line("W454C LONG %s PHARMA" % s_, "W454C LONG %s ITEM %02d" % (s_, i), "to_order", "new")
    db.commit()
    pdf2 = OP.build(db)
    m2 = measure(pdf2, cdp)
    names2 = [(pi, b["name"]) for pi, p in enumerate(m2["pages"], 1) for b in p["bands"]]
    split = sorted({n for _pi, n in names2 if sum(1 for _q, x in names2 if x == n) > 1})
    rows2 = [r for p in m2["pages"] for r in p["rows"]]
    out["long"] = dict(bad=[(p, mask(s), w) for p, s, w in m2["bad"]], pages=len(m2["pages"]), split=split, rows=len(rows2),
                       head=[mask(h) for p in m2["pages"] for h in p["head"]][:1], ticked=sum(1 for r in rows2 if r["ticked"]),
                       old=sum(1 for r in rows2 if r["old"]), bands=len([n for n in names2 if not n[1].endswith("(aage)")]))
    if NEW:
        out["long"]["counts"] = OP.layout(db)["counts"]
    # print_old = 0
    setv("order.sheet_print_old", "0")
    m3 = measure(OP.build(db), cdp)
    out["print_old0"] = sum(1 for p in m3["pages"] for r in p["rows"] if r["old"])
    setv("order.sheet_print_old", "1")

    # ---- the tie: a crafted scan of one awaited supplier's bill; that supplier leaves the page
    if maal:
        o = [x for x in maal if x.get("order_src") == "s454"][:1] or maal[:1]
        o = o[0]
        at = NOW - dt.timedelta(minutes=5)
        ins(adb, "bills", dict(kind="Pharmacy", vendor=o["vendor"], bill_no="W454C1", bill_date=TODAY.isoformat(), total_amount=1234.0, notes="W454C walk",
                               created_at=(at - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"), submitted_at=at.strftime("%Y-%m-%d %H:%M"),
                               stamp_no="W454C-1", status="captured", ocr_status="read", lane="pharmacy", source_stored="w454c.pdf", source_orig="w454c",
                               submitted_by="W454C walk", bill_month=TODAY.strftime("%Y-%m")))
        adb.commit()
        before = [b["name"] for p in measure(OP.build(db), cdp)["pages"] for b in p["bands"]]
        try:
            ties = OS.tie_pass(db, "W454C walk")
        except Exception as e:                                         # noqa: BLE001
            ties = "error %s" % e
        after = [b["name"] for p in measure(OP.build(db), cdp)["pages"] for b in p["bands"]]
        out["tie"] = dict(vendor=o["vendor"], ties=str(ties)[:120], before=o["vendor"] in before, after=o["vendor"] in after,
                          tied=bool(db.execute("SELECT 1 FROM order_scan_tie WHERE order_id=?", (o["id"],)).fetchone()))

    # ---- 2  the words
    out["words"] = dict(en1=PS.L(True, "dawa", 1), en11=PS.L(True, "dawa", 11), hi1=PS.L(False, "dawa", 1),
                        whose=PS.L(True, "whose", "Darpan's", "02-10", 1, 1), order1=PS.L(True, "orderN", "02-10", 1))
    s_, h_ = G("manoj", "/finance/porders/s454/order?all=1")
    t_ = text(h_)
    out["owner_list"] = dict(status=s_, has_1_medicine=bool(re.search(r"(?<![\d,])1 medicine\b(?!s)", t_)), has_1_medicines=bool(re.search(r"(?<![\d,])1 medicines", t_)))

    # ---- 3  the Reception phone card and the test message
    def card(u):
        s, h = G(u, "/finance/porders?old=1")
        m = re.search(r'<div [^>]*id="s454phone".*?</script></div>', h, re.S)
        return s, (m.group(0) if m else ""), h

    s, c0, full0 = card("manoj")
    out["card0"] = dict(status=s, present=bool(c0), text=mask(text(c0))[:600], key_in_page=(walk_tok in full0),
                        disabled=('id="s454testsend" style="min-height:40px" disabled' in c0), reason=("Save a test number first." in c0))
    out["card_others"] = {u: bool(card(u)[1]) for u in ("shavez", "reception", "darpan")}
    out["routes_others"] = {u: [J(u, "/finance/porders/api/s454/test_number", {"number": test_num})[0], J(u, "/finance/porders/api/s454/test_send")[0]]
                            for u in ("shavez", "reception")}
    out["save_bad"] = J("manoj", "/finance/porders/api/s454/test_number", {"number": "12345"})[0]
    sv = J("manoj", "/finance/porders/api/s454/test_number", {"number": test_num})
    out["save"] = [sv[0], bool((sv[1] or {}).get("ok"))]
    s, c1, full1 = card("manoj")
    digits = "91" + test_num
    out["card1"] = dict(masked=("4321" in c1 and "•" in c1), full_in_page=(test_num in full1 or digits in full1), enabled=not re.search(r'id="s454testsend"[^>]*disabled', c1))
    aud = [dict(r) for r in db.execute("SELECT action, detail FROM purchase_audit WHERE action LIKE 's454_test%' ORDER BY id")]
    out["audit_has_number"] = any(test_num in (a["detail"] or "") or "4321" in (a["detail"] or "") for a in aud)
    out["audit_actions"] = [a["action"] for a in aud]

    def counts():
        return dict(pay=len(SM.messages(db)), pend=len(SM.pending(db)), state=SM._s452_phone_state_line(db),
                    s454=PS.counts(db), orders=db.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND status IN ('queued','failed')").fetchone()[0],
                    owner=[l["text"] for l in OS.owner_lines(db)])
    c_before = counts()
    st = J("manoj", "/finance/porders/api/s454/test_send")
    tid = (st[1] or {}).get("message_id")
    row = dict(db.execute("SELECT kind, month, status, body FROM supplier_msg WHERE id=?", (tid,)).fetchone()) if tid else {}
    out["test_queued"] = dict(code=st[0], kind=row.get("kind"), month=row.get("month"), two_lines=(row.get("body") or "").count("\n") == 1,
                              rupee=("₹ 1,234.50" in (row.get("body") or "")), head=(row.get("body") or "").startswith("Sanjeevni test · "))
    c_after = counts()
    out["counts_unchanged"] = (c_before == c_after, [k for k in c_before if c_before[k] != c_after[k]])
    n1 = phone("/finance/api/supplier-msg/next")
    n2 = phone("/finance/api/supplier-msg/next")
    js_ok = False
    try:
        jj = json.loads(n1[2].decode("utf-8"))
        js_ok = jj.get("text", "").count("\n") == 1 and "₹" in jj.get("text", "") and jj.get("to") == digits
    except ValueError:
        pass
    out["test_next"] = dict(first_is_test=(n1[1].get("id") == tid), second_not_test=(n2[1].get("id") != tid), json_ok=js_ok, raw_has_escaped_newline=(b"\\n" in n1[2]))
    d1 = phone("/finance/api/supplier-msg/done", {"id": tid, "ok": True})
    s, c2, _f = card("manoj")
    out["test_sent"] = dict(code=d1[0], status=(db.execute("SELECT status FROM supplier_msg WHERE id=?", (tid,)).fetchone() or [None])[0], card=mask(text(c2))[:400],
                            three=all(w in text(c2) for w in ("queued", "handed to the phone", "sent")))
    pic_card = c2                                                      # the picture: the card as it reads right after a test went
    for u in ("reception", "shavez", "darpan"):
        for p in ("/finance/porders", "/finance/porders/s454/order", "/finance/porders/s454/maal", "/finance/purchase/page/pay"):
            s, h = G(u, p)
            if "Sanjeevni test" in h or "Test message" in h:
                out.setdefault("test_on_staff", []).append([u, p])
    out.setdefault("test_on_staff", [])
    st2 = J("manoj", "/finance/porders/api/s454/test_send")
    tid2 = (st2[1] or {}).get("message_id")
    db.execute("UPDATE supplier_msg SET handed_at=NULL WHERE id=?", (tid2,))
    db.commit()
    n3 = phone("/finance/api/supplier-msg/next")
    d2 = phone("/finance/api/supplier-msg/done", {"id": tid2, "ok": False, "error": "send not clicked"})
    s, c3, _f = card("manoj")
    old = (NOW - dt.timedelta(minutes=45)).isoformat()
    db.execute("UPDATE supplier_msg SET last_try_at=?, handed_at=? WHERE id=?", (old, old, tid2))
    db.commit()
    seen = []
    for _i in range(3):
        n = phone("/finance/api/supplier-msg/next")
        seen.append(n[1].get("id"))
    out["test_failed"] = dict(handed=(n3[1].get("id") == tid2), code=d2[0], card_reason=("failed" in text(c3) and "send not clicked" in text(c3)),
                              retried=(tid2 in seen))

    # ---- 4  17.9 / 17.10 data steps (the kit's own data module, on this copy)
    if NEW:
        spec = importlib.util.spec_from_file_location("data_s454p1c", os.environ["DATA_MOD"])
        DM = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(DM)
        r1 = dict(db.execute("SELECT status, sent_by, sent_at FROM supplier_msg WHERE id=1").fetchone() or {})
        a1 = DM.reset_msg1(db, "W454C walk")
        r2 = dict(db.execute("SELECT status, attempts, sent_at, sent_by, last_try_at FROM supplier_msg WHERE id=1").fetchone() or {})
        a2 = DM.reset_msg1(db, "W454C walk")
        out["msg1"] = dict(before=r1, first=a1, after=r2, again=a2)
        db.execute("UPDATE supplier_msg SET status='sent', sent_by='manoj', sent_at='2026-10-03T15:00:27' WHERE id=1")
        db.commit()
        out["msg1_other"] = dict(result=DM.reset_msg1(db, "W454C walk"), status=db.execute("SELECT status FROM supplier_msg WHERE id=1").fetchone()[0])
        out["alive"] = DM.set_alive(db, "W454C walk")
        out["alive_again"] = DM.set_alive(db, "W454C walk")
        # dark for an hour: the staff's button, the owner's line; an order message waiting past the hour goes back to "call kijiye"
        setv("supplier_msg.phone_last", "%s 200" % (NOW - dt.timedelta(minutes=61)).isoformat())
        db.execute("DELETE FROM setting WHERE key='s454.phone_off_met'")
        db.commit()
        alive1 = OS.phone_state(db)
        s, h = G("reception", "/finance/porders/s454/order?all=1")
        btn_off = bool(re.search(r'id="waall"\s+disabled', h))
        owner1 = [l["text"] for l in OS.owner_lines(db) if "reception phone" in l["text"].lower()]
        b, code = OS.order_supplier(db, "Shivani (Reception)", pa.supplier_key(two), "whatsapp")
        db.execute("UPDATE supplier_msg SET queued_at=? WHERE kind='order' AND ref=?", ((NOW - dt.timedelta(minutes=61)).isoformat(), b.get("order_id")))
        db.commit()
        wd = OS.withdraw_late(db)
        s, h2 = G("reception", "/finance/porders/s454/order?all=1")
        card_two = re.search(r'<div class="card" data-sn="%s">.*?</div></div>' % re.escape(pa.supplier_key(two)), h2, re.S)
        out["dark_hour"] = dict(alive=list(alive1), button_disabled=btn_off, owner_line=owner1, queued=[code, bool(b.get("queued"))], withdrawn=wd,
                                staff_card=text(card_two.group(0)) if card_two else "")
        setv("supplier_msg.phone_last", "%s 200" % (NOW - dt.timedelta(hours=13)).isoformat())
        OS.order_supplier(db, "Shivani (Reception)", pa.supplier_key(two), "whatsapp")
        out["dark_13h"] = dict(alive=list(OS.phone_state(db)), owner_line=[l["text"] for l in OS.owner_lines(db) if "reception phone" in l["text"].lower()])
    # ---- the setup page (the walk's own key on this copy; the page is never printed)
    s, h = G("manoj", "/finance/purchase/page/phone-setup")
    t = text(h)
    out["setup"] = dict(status=s, key_there=(walk_tok in h),
                        new=all(w in t for w in ("har 1 minute", "X-Phone-Token", "{lv=msg[to]}", "URL encode parameters", "Device Unlocked", "Screen On",
                                                 "Test actions", "WhatsApp Business", "pehli request ko copy karke", "application/json")),
                        old_sentence=("turant dobara poochhe" in t or "turant step 1 se phir chalaiye" in t), five_min=("har 5 minute" in t))
    if os.environ.get("PICTURES") and NEW:
        c4 = pic_card
        with open(os.path.join(os.environ["PICTURES"], "17_reception_phone_card.html"), "w", encoding="utf-8") as fh:
            fh.write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                     '<title>Reception phone card (walk)</title></head><body style="font:16px system-ui;max-width:480px;margin:12px auto">%s</body></html>'
                     % re.sub(r"<script.*?</script>", "", c4, flags=re.S))
    # ---- queue parity: payment and order messages handed out exactly as before (the same rows, in the same order) on a fresh copy
    pdb = sqlite3.connect(os.environ["PARITY_DB"], timeout=60)
    pdb.execute("INSERT INTO setting (key, value) VALUES ('supplier_msg.phone_token', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (walk_tok,))
    pdb.commit()
    pdb.close()
    out["parity"] = None
    try:
        par = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--parity"],
                             env=dict(os.environ, WALK_TOK=walk_tok, FINANCE_DB=os.environ["PARITY_DB"]), cwd=FIN,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
        js = [l for l in par.stdout.splitlines() if l.startswith("PARITY ")]
        out["parity"] = json.loads(js[-1][7:]) if js else dict(error=mask(par.stdout[-400:]))
    except Exception as e:                                                 # noqa: BLE001
        out["parity"] = dict(error=str(e)[:200])
    blob = json.dumps(out, ensure_ascii=False, default=str)
    if walk_tok in blob or test_num in blob or p1 in blob or p2 in blob:
        print(TAG + json.dumps({"LEAK": True}))
        return
    print(TAG + blob)


def parity():
    """On its own fresh copy: drain the reception phone's queue through the real door; one failure, retried after its 30 minutes."""
    FIN, POR = os.environ["FINDIR"], os.environ["PORDIR"]
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                               # noqa: E402
    fc = fa.app.test_client(use_cookies=False)
    tok = os.environ["WALK_TOK"]
    db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)

    def ph(path, body=None):
        h = {"X-Phone-Token": tok}
        r = fc.post(path, base_url="https://followup.dr-manoj.in", headers=h, json=body) if body is not None else fc.get(path, base_url="https://followup.dr-manoj.in", headers=h)
        return r.get_json(silent=True) or {}
    # the walk's own rows, the same on both sides: four payment messages and two order messages, queued long ago (so they come first in
    # the queue's order) to numbers made here; every queued row's handout cleared, so the live phone's own handouts do not decide the run
    num = "9" + "3" * 9
    for i in range(6):
        kind = "neft" if i < 4 else "order"
        db.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, to_number, body, status, queued_at) VALUES (?,?,?,?,?,?,?,?,?)",
                   ("W454C", "W454C P%d" % i, "W454C P%d" % i, kind, 990000 + i, "91" + num, "W454C parity %d" % i, "queued", "2000-01-01T00:00:%02d" % i))
    try:
        db.execute("UPDATE supplier_msg SET handed_at=NULL WHERE status IN ('queued','failed')")
    except sqlite3.Error:
        pass
    db.commit()
    seq, failed = [], None
    for i in range(80):
        n = ph("/finance/api/supplier-msg/next")
        if not n.get("id"):
            break
        seq.append(n["id"])
        if i == 2:
            failed = n["id"]
            ph("/finance/api/supplier-msg/done", {"id": n["id"], "ok": False, "error": "W454C parity"})
        else:
            ph("/finance/api/supplier-msg/done", {"id": n["id"], "ok": True})
    if failed:
        old = (dt.datetime.now() - dt.timedelta(minutes=45)).replace(microsecond=0).isoformat()
        db.execute("UPDATE supplier_msg SET last_try_at=?, handed_at=? WHERE id=?", (old, old, failed))
        db.commit()
        n = ph("/finance/api/supplier-msg/next")
        seq.append(("retry", n.get("id")))
    print("PARITY " + json.dumps(dict(seq=seq, n=len(seq))))


# ======================================================================= main
def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--por", "--db", "--adb", "--work", "--data-mod"):
        ap.add_argument(k, required=True)
    ap.add_argument("--pictures", default="")
    a = ap.parse_args()
    for p in (a.work, a.por):
        assert p.startswith("/tmp/"), "refusing a non-scratch path: " + p
    os.makedirs(a.work, exist_ok=True)
    n, fails = [0], []

    def check(label, cond, got=None):
        n[0] += 1
        print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(str(got))[:600] + "]") if got is not None else ""))
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
        fh.write("# W454C walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w454c-walk-seed'\n" % secret)
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

    pbase = os.path.join(a.work, "w454c_parity_base.db")
    copydb(a.db, pbase)                                                    # ONE copy for both sides: the live phone may be sending meanwhile

    def run(side, fin):
        dbp, adbp, pdbp = (os.path.join(a.work, "w454c_%s.db" % side), os.path.join(a.work, "w454c_%s_assets.db" % side),
                           os.path.join(a.work, "w454c_%s_parity.db" % side))
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(pbase, pdbp)
        stub = os.path.join(a.work, "w454c_push_%s.jsonl" % side)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, FINANCE_DB=dbp, ASSETS_DB=adbp, PARITY_DB=pdbp, FINANCE_ALLOW_HEADER_AUTH="1",
                   FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"),
                   CLINIC_SSO_SECRET=secret, ORDER_PUSH_STUB=stub, DATA_MOD=a.data_mod, PICTURES=a.pictures, PORDERS_SOURCE="tables")
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=1800)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (side, p.returncode))
            for l in p.stdout.splitlines()[-25:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    N = run("new", a.fin_new)
    O = run("old", a.fin_old)
    check("both probes ran to the end (NEW the built files, OLD the box as it is); no key and no phone number reached any output",
          N is not None and O is not None and not N.get("LEAK") and not O.get("LEAK"))
    if N is None or O is None or N.get("LEAK") or O.get("LEAK"):
        print("WALK_S454P1C RED -- a probe did not finish, or a key / number reached its output")
        return 1
    L_, LO = N["live"], O["live"]
    print("-- 1  the printed order sheet (measured from the PDF's own text positions and the font's widths)")
    check("the live order (a copy): every piece of text inside its own cell and the page's margins (%d page(s), %d rows)" % (L_["pages"], L_["rows"]),
          L_["bad"] == [] and L_["rows"] > 0, L_["bad"][:6])
    check("NEGATIVE: the page as installed fails it -- old-pending tags across Pack / Qty, the foot past the right edge",
          any(w.startswith("runs past") for _p, s, w in LO["bad"] if s.startswith("purana")) and any(s.startswith("Order ho gaya to") for _p, s, w in LO["bad"]),
          LO["bad"][:8])
    check("every line under 'Maal aaya?' is on the page with its Order box ticked (%d of %d)" % (L_["awaited_on_page"], L_["awaited"]),
          L_["awaited"] > 0 and L_["awaited_on_page"] == L_["awaited"], L_["awaited_missing"])
    check("NEGATIVE: the page as installed leaves them off (%d of %d)" % (LO["awaited_on_page"], LO["awaited"]), LO["awaited_on_page"] < LO["awaited"], LO["awaited_missing"])
    c = L_.get("counts") or {}
    hd = (L_["head"] or [""])[0]
    check("the head line counts what is on the page: %s" % hd,
          c.get("to_order", 0) + c.get("awaited", 0) + c.get("old", 0) == L_["rows"] and c.get("awaited") == L_["ticked"] and c.get("old") == L_["old"]
          and ("%d dawa" % L_["rows"]) in hd and ("%d supplier" % len(L_["bands"])) in hd and (("%d ka maal aana hai" % L_["ticked"]) in hd if L_["ticked"] else True)
          and (("%d purane pending" % L_["old"]) in hd if L_["old"] else "purane" not in hd), dict(counts=c, rows=L_["rows"], ticked=L_["ticked"], old=L_["old"]))
    check("a paper order (way not known) ticks only its lines: no band box ticked on the live page", all(not t for _n, t in L_.get("band_ticks") or []), L_.get("band_ticks"))
    cr = N["crafted"]
    check("crafted: a 30-character name with its old tag, a long supplier name with two numbers, a supplier with none -- every text inside its cell; the name whole",
          cr["bad"] == [] and cr["name30_whole"] and cr["two_band"] and cr["nophone_text"], cr)
    check("NEGATIVE: the page as installed runs the 30-character name's tag out of its cell", any("purana" in s for _p, s, _w in O["crafted"]["bad"]), O["crafted"]["bad"][:6])
    lg = N["long"]
    lc = lg.get("counts") or {}
    check("a long order: %d pages, no supplier's block split, every text inside its cell, the head line equal to the rows (%s)" % (lg["pages"], (lg["head"] or [""])[0]),
          lg["pages"] >= 2 and lg["split"] == [] and lg["bad"] == [] and sum(lc.values()) == lg["rows"] and ("%d dawa" % lg["rows"]) in (lg["head"] or [""])[0], lg)
    check("order.sheet_print_old = 0 leaves the old lines off", N["print_old0"] == 0, N["print_old0"])
    t = N.get("tie") or {}
    check("a crafted scan of %s's bill ties its order; the supplier is then gone from the page" % t.get("vendor"),
          t.get("before") is True and t.get("tied") is True and t.get("after") is False, t)
    print("-- 2  one word")
    w = N["words"]
    check("the owner's English: '%s', '%s', '%s', '%s'; staff Hindi '%s'" % (w["en1"], w["en11"], w["whose"], w["order1"], w["hi1"]),
          w["en1"] == "1 medicine" and w["en11"] == "11 medicines" and w["hi1"] == "1 dawa" and "1 supplier," in w["whose"] and w["whose"].endswith("1 medicine")
          and w["order1"].endswith("1 medicine"), w)
    check("the owner's list for a supplier of one medicine reads '1 medicine', never '1 medicines'", N["owner_list"]["has_1_medicine"] and not N["owner_list"]["has_1_medicines"], N["owner_list"])
    check("NEGATIVE: the box as it is says '1 medicines'", O["words"]["en1"] == "1 medicines", O["words"]["en1"])
    print("-- 3  the Reception phone card and its test message")
    c0 = N["card0"]
    check("the owner's card on ?old=1: last asked, the messages waiting (orders, payments), 'awake and unlocked', the send button disabled with its reason; the key is not on the page",
          c0["present"] and "Last asked the server:" in c0["text"] and "order message" in c0["text"] and "payment message" in c0["text"] and "awake and unlocked" in c0["text"]
          and c0["disabled"] and c0["reason"] and not c0["key_in_page"], c0["text"][:300])
    check("NEGATIVE: the box as it is has no such card", not O["card0"]["present"])
    check("no other login gets the card (shavez, reception, darpan) or its taps (403)", not any(N["card_others"].values())
          and all(v == [403, 403] for v in N["routes_others"].values()), [N["card_others"], N["routes_others"]])
    check("the test number: a bad one refused (400); saved (200); shown masked to its last four; never in full on the page; never in the audit",
          N["save_bad"] == 400 and N["save"] == [200, True] and N["card1"]["masked"] and not N["card1"]["full_in_page"] and N["card1"]["enabled"]
          and not N["audit_has_number"], [N["save_bad"], N["save"], N["card1"], N["audit_actions"]])
    tq = N["test_queued"]
    check("'Send a test message' queues one message of kind 'test' (month 'test'): two lines, 'Sanjeevni test · dd-mm hh:mm' and the rupee line",
          tq["code"] == 200 and tq["kind"] == "test" and tq["month"] == "test" and tq["two_lines"] and tq["rupee"] and tq["head"], tq)
    check("it is counted nowhere else: the payment list, its pending line, the setup page's count, the reception screen's counts, the order messages, the owner's lines -- all unchanged",
          N["counts_unchanged"][0], N["counts_unchanged"][1])
    tn = N["test_next"]
    check("the phone's next hands the test first, once (F-702); the JSON carries the line break and the rupee sign intact, to the saved number",
          tn["first_is_test"] and tn["second_not_test"] and tn["json_ok"] and tn["raw_has_escaped_newline"], tn)
    ts = N["test_sent"]
    check("the phone's 'sent' marks it sent; the card shows queued · handed to the phone · sent, with their times", ts["code"] == 200 and ts["status"] == "sent" and ts["three"], ts["card"])
    check("no staff screen shows the test (reception, shavez, darpan: home, order list, Maal aaya?, Vendor payments)", N["test_on_staff"] == [], N["test_on_staff"])
    tf = N["test_failed"]
    check("'could not send' shows on the card with the phone's reason; a failed test is never handed out again (not even after its 30 minutes)",
          tf["handed"] and tf["code"] == 200 and tf["card_reason"] and not tf["retried"], tf)
    pn, po = N.get("parity") or {}, O.get("parity") or {}
    check("payment and order messages handed out exactly as before: the same %d rows in the same order, one failure retried after 30 minutes -- NEW = the box as it is"
          % len(pn.get("seq") or []), len(pn.get("seq") or []) >= 7 and pn.get("seq") == po.get("seq") and (pn.get("seq") or [[None]])[-1][1] is not None,
          dict(new=pn.get("seq"), old=po.get("seq")))
    print("-- 4  the data steps, the dark phone, the setup page")
    m1 = N["msg1"]
    check("17.9: message 1 read sent by reception-phone at 15:00:27 -> put back to waiting (queued, attempts 0, sent_at / sent_by / last_try_at cleared), audited; again: nothing",
          (m1["first"] or {}).get("reset") is True and m1["after"].get("status") == "queued" and m1["after"].get("attempts") == 0
          and m1["after"].get("sent_at") is None and m1["after"].get("sent_by") is None and m1["after"].get("last_try_at") is None and (m1["again"] or {}).get("reset") is False
          if m1["before"].get("sent_by") == "reception-phone" and m1["before"].get("sent_at") == "2026-10-03T15:00:27" else (m1["first"] or {}).get("reset") is False, m1)
    check("17.9: a message 1 that reads otherwise (sent by someone else) is left as it is", (N["msg1_other"]["result"] or {}).get("reset") is False and N["msg1_other"]["status"] == "sent",
          N["msg1_other"])
    check("17.10: order.phone_alive_min set to 720 (audited); a second run changes nothing", (N["alive"] or {}).get("after") == "720" and (N["alive_again"] or {}).get("changed") is False,
          [N["alive"], N["alive_again"]])
    dh = N["dark_hour"]
    check("dark for an hour: the phone still counts as alive, the WhatsApp button is enabled, no owner line; an order message waiting past the hour goes back: '%s'" % dh["staff_card"],
          dh["alive"][0] is True and not dh["button_disabled"] and dh["owner_line"] == [] and dh["queued"] == [200, True] and dh["withdrawn"] >= 1
          and "WhatsApp nahi gaya" in dh["staff_card"], dh)
    d13 = N["dark_13h"]
    check("dark for 13 hours with an order message waiting: the owner reads '%s'" % ((d13["owner_line"] or [""])[0]),
          d13["alive"][0] is False and d13["owner_line"] and "12 hours" in d13["owner_line"][0], d13)
    su = N["setup"]
    check("the setup page's steps as the macro was built (1 minute, the exact header name, {lv=msg[...]}, URL encode, the two constraints, Test actions, one WhatsApp); "
          "Part 1's 'ask again at once' and '5 minute' gone", su["status"] == 200 and su["key_there"] and su["new"] and not su["old_sentence"] and not su["five_min"], su)
    check("NEGATIVE: the box as it is still prints 'ask again at once'", O["setup"]["old_sentence"] is True, O["setup"])
    print("-- the report's facts: one page holds %s one-line medicine rows under one supplier band" % N.get("rows_per_page"))
    print("WALK_S454P1C %s -- %d of %d passed%s" % ("GREEN" if not fails else "RED", n[0] - len(fails), n[0], "" if not fails else ": " + "; ".join(fails)[:600]))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    elif "--parity" in sys.argv:
        parity()
    else:
        sys.exit(main())
