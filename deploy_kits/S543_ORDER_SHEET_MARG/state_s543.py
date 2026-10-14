#!/usr/bin/env python3
"""state_s543.py -- kit S543_ORDER_SHEET_MARG (14-Oct-2026). READ ONLY.
  python3 -B state_s543.py --db <finance.db> --map12 <v12> --map13 <v13> [--marg /root/marg_ingest]
      the install-day state of the brief's §0, by key, from the database alone (mode=ro): Marg's newest export, its four groups,
      Purane pending, Maal aaya?, both map counts under v12 and v13; and the collector (the newest ORDER_PENDING file VERIFIED, on disk,
      taken). Exit 1 when the collector is red (charter 1b).
  python3 -B state_s543.py --page --fin <scratch copy of /root/finance> --db <a COPY of finance.db> --map13 <v13>
      the ordering page as shavez on that copy (the real app, header sign-in for this process only): 200, the heading, both buttons.
No phone number, no export cell is printed."""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys

NEWEST = "SELECT id FROM order_sheet ORDER BY COALESCE(NULLIF(stamp,''),'0') DESC, taken_at DESC, id DESC LIMIT 1"


def state(a):
    c = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    sid = c.execute(NEWEST).fetchone()[0]
    sh = dict(c.execute("SELECT id, stamp, taken_at, md5 FROM order_sheet WHERE id=?", (sid,)).fetchone())
    M = [dict(r) for r in c.execute("SELECT * FROM order_sheet_line WHERE last_sheet=? ORDER BY supplier_norm, line_date, id", (sid,))]
    tied = {r[0] for r in c.execute("SELECT order_id FROM order_scan_tie")}
    removed = {(r[0], r[1]) for r in c.execute("SELECT ref, item FROM s454_line_edit WHERE src='sheet' AND removed=1")}
    mx = int(c.execute("SELECT value FROM setting WHERE key='order.sheet_max_age_days'").fetchone()[0])
    today = dt.date.today()
    g = dict(to_order=[], in_line=[], ordered=[], old=[])
    for l in M:
        o = c.execute("SELECT status, created_at FROM purchase_order WHERE id=?", (l["order_id"],)).fetchone() if l["order_id"] else None
        if l["state"] == "to_order" and (str(l["id"]), l["item"]) not in removed:
            g["to_order"].append(l)
        elif l["state"] == "in_line":
            g["in_line"].append(l)
        elif l["state"] == "ordered" and o and ((o[0] == "sent" and l["order_id"] not in tied) or (today - dt.date.fromisoformat(o[1][:10])).days < mx):
            g["ordered"].append(l)
        else:
            g["old"].append(l)
    maal = []
    for o in c.execute("SELECT * FROM purchase_order WHERE status='sent' ORDER BY created_at, id").fetchall():
        if o["id"] in tied:
            continue
        ents = {x.strip() for x in str(o["ext_ref"] or "").split(",") if x.strip()}
        if ents:
            items = {r[0] for r in c.execute("SELECT item FROM purchase_order_line WHERE order_id=?", (o["id"],))}
            if not any(x["supplier_norm"] == o["supplier_norm"] and x["entry_no"] in ents and x["item"] in items for x in M):
                continue
        maal.append("%d %s" % (o["id"], o["vendor"]))
    m = re.match(r"^(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)", str(sh["stamp"] or ""))
    st = ("%s-%s %s:%s" % (m.group(3), m.group(2), m.group(4), m.group(5))) if m else "-"
    print("   Marg's newest export: sheet %d, stamp %s -- 'Marg mein khula order (%s) · %d supplier, %d dawa'"
          % (sid, sh["stamp"] or "-", st, len({l["supplier_norm"] for l in M}), len(M)))
    print("   groups: to_order %d · in_line %d · ordered %d · old %d" % tuple(len(g[k]) for k in ("to_order", "in_line", "ordered", "old")))
    print("   Purane pending (%d): %s" % (len(g["old"]), ", ".join(l["item"] for l in g["old"]) or "-"))
    print("   Maal aaya? (%d): %s" % (len(maal), ", ".join(maal) or "-"))
    cols = {r[1] for r in c.execute("PRAGMA table_info(order_sheet_line)")}
    if "marg_pend_raw" in cols:
        print("   Marg's RECEIVE / PENDING kept on %d of the %d lines" % (sum(1 for l in M if l.get("marg_pend_raw") is not None), len(M)))
    for p, nm in ((a.map12, "v12"), (a.map13, "v13")):
        if not p:
            continue
        d = json.load(open(p, encoding="utf-8"))
        r = {x["id"]: tuple(c.execute(x["due_sql"]).fetchone()) for x in d["duties"] if x["id"] in ("reception.medicine_orders", "reception.order_arrival")}
        print("   the map %s (version %s): reception.medicine_orders %s · reception.order_arrival %s" % (nm, d.get("version"), r.get("reception.medicine_orders"),
                                                                                                         r.get("reception.order_arrival")))
    ok = True
    if a.marg:
        f = c.execute("SELECT md5, server_name, date_from, verdict, received_at FROM mi_file WHERE type='ORDER_PENDING' ORDER BY received_at DESC LIMIT 1").fetchone()
        if f:
            p = os.path.join(a.marg, "archive", "ORDER_PENDING", str(f["date_from"] or "")[:7], f["server_name"] or "")
            taken = c.execute("SELECT 1 FROM order_sheet WHERE md5=?", (f["md5"],)).fetchone() is not None
            ok = f["verdict"] == "VERIFIED" and os.path.isfile(p) and taken
            print("   the collector: the newest ORDER_PENDING file (%s) %s, %s, %s" % (str(f["received_at"])[:16], f["verdict"],
                                                                                   "on disk" if os.path.isfile(p) else "NOT on disk", "taken" if taken else "NOT taken"))
        else:
            ok = False
            print("   the collector: no ORDER_PENDING file at all")
    c.close()
    return 0 if ok else 1


def page(a):
    os.environ.update(FINANCE_DB=os.path.abspath(a.db), FINANCE_ALLOW_HEADER_AUTH="1", ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map13),
                      FINANCE_SSO_DIR=os.path.join(os.path.dirname(os.path.abspath(a.db)), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="")
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    sys.path.insert(0, os.path.abspath(a.fin))
    os.chdir(a.fin)
    import finance_app as fa                                  # noqa: E402
    cl = fa.app.test_client(use_cookies=False)
    r = cl.get("/finance/porders/s454/order", base_url="https://followup.dr-manoj.in", headers={"X-Clinic-User": "shavez", "X-Clinic-Role": "manager"})
    h = r.get_data(as_text=True)
    m = re.search(r'id="margopen">([^<]*)<', h)
    import html                                               # noqa: PLC0415
    ok = r.status_code == 200 and m is not None and 'id="print"' in h and 'id="margpdf"' in h
    print("   /finance/porders/s454/order as shavez on a copy with the placed files: %d · '%s' · print button %s · Marg PDF button %s"
          % (r.status_code, html.unescape(m.group(1)) if m else "-", 'id="print"' in h, 'id="margpdf"' in h))
    print("PAGE OK" if ok else "PAGE RED")
    return 0 if ok else 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--map12")
    ap.add_argument("--map13")
    ap.add_argument("--marg")
    ap.add_argument("--fin")
    ap.add_argument("--page", action="store_true")
    a = ap.parse_args()
    return page(a) if a.page else state(a)


if __name__ == "__main__":
    sys.exit(main())
