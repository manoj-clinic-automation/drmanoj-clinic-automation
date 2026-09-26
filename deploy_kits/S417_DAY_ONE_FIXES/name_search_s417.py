#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""name_search_s417.py -- kit S417_DAY_ONE_FIXES (F-636), brief section 4. FACTS ONLY: it changes nothing, it opens the database
read-only. The owner saw an item printed as "GRDIANS 25 MG" (his reading) and says the product is JIARDIANCE 10 mg. This lists every
stock / sale / purchase name that matches JARDIAN / JIARDIAN / GRDIAN, spelling-tolerant (the name's letters only, upper-case, against
(J|G)I?A?RDIAN -- JARDIANCE, JIARDIANCE, GRDIANS and GARDIAN match; GUARDIAN does not), with the strength the name prints, the packing,
the stock now, the supplier(s), the last purchase and the last sale. A rename, if the owner wants one, goes the D620 way (Amir in Marg,
the rename memory follows) -- never from here.

  name_search_s417.py --db PATH [--json]
"""
import argparse
import datetime as dt
import json
import re
import sqlite3
import sys

PATTERN = r"(J|G)I?A?RDIAN"


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone() is not None


def _letters(s):
    return re.sub(r"[^A-Z]", "", str(s or "").upper())


def _strength(name):
    m = re.search(r"(?<![A-Z0-9.])(\d+(?:\.\d+)?)\s*(MG|MCG|GM|G|ML)?\b", str(name or "").upper())
    if not m:
        return "not printed"
    return m.group(1) + ((" " + m.group(2).lower()) if m.group(2) else " (the name prints no unit)")


def _newest_as_on(con):
    rows = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")] if _has(con, "stock_snapshot") else []
    return max(rows, key=lambda d: (str(d)[6:], str(d)[3:5], str(d)[:2])) if rows else None


def _stock_words(qty, pack, packing):
    try:
        n = int(qty or 0)
        size = int(pack or 0)
    except (TypeError, ValueError):
        return str(qty)
    if size > 1:
        s, loose = divmod(abs(n), size)
        return ("-" if n < 0 else "") + "%d strip%s" % (s, "" if s == 1 else "s") + ((" + %d" % loose) if loose else "")
    return "%d" % n


def search(con, pattern=PATTERN):
    rx = re.compile(pattern)
    names = {}
    sources = (("stock_snapshot", "item"), ("purchase_line", "item"), ("sale_line_item", "item_name"), ("marg_item_name", "name"),
               ("stock_item_section", "item"), ("purchase_salt_marg", "item"), ("stock_count_item", "item"))
    for t, col in sources:
        if not _has(con, t):
            continue
        for (v,) in con.execute("SELECT DISTINCT %s FROM %s" % (col, t)):
            if v and rx.search(_letters(v)):
                names.setdefault(str(v).strip(), set()).add(t)
    as_on = _newest_as_on(con)
    since90 = (dt.date.today() - dt.timedelta(days=90)).isoformat()
    sup_name = {}
    if _has(con, "purchase_bill"):
        sup_name = {r[0]: " ".join(str(r[1] or "").split()) for r in con.execute("SELECT supplier_norm, MAX(supplier) FROM purchase_bill GROUP BY supplier_norm")}
    out = []
    for name in sorted(names):
        row = dict(item=name, strength=_strength(name), found_in=sorted(names[name]))
        st = con.execute("SELECT qty, packing, pack_size FROM stock_snapshot WHERE as_on=? AND item=?", (as_on, name)).fetchone() if as_on else None
        row["stock"] = (dict(as_on=as_on, qty=st[0], packing=st[1], pack_size=st[2], words=_stock_words(st[0], st[2], st[1])) if st else None)
        pl = []
        if _has(con, "purchase_line"):
            pl = con.execute("SELECT supplier_norm, bill_no, bill_date, qty, free, packing, purchase_rate_p, rate_p, direction FROM purchase_line "
                             "WHERE item=? ORDER BY bill_date DESC, id DESC", (name,)).fetchall()
        row["suppliers"] = sorted({sup_name.get(r[0]) or r[0] for r in pl if r[0]})
        row["packing"] = (st[1] if st else None) or (pl[0][5] if pl else None)
        row["purchases_n"] = len(pl)
        row["last_purchase"] = (dict(date=pl[0][2], supplier=sup_name.get(pl[0][0]) or pl[0][0], bill_no=pl[0][1], qty=pl[0][3], free=pl[0][4],
                                     rate_rs=round(((pl[0][6] or pl[0][7] or 0) / 100.0), 2), direction=pl[0][8]) if pl else None)
        sl = []
        if _has(con, "sale_line_item"):
            sl = con.execute("SELECT business_date, qty_raw, is_return FROM sale_line_item WHERE item_name=? ORDER BY business_date DESC, id DESC", (name,)).fetchall()
        row["sale_lines_n"] = len(sl)
        row["sale_lines_90d"] = sum(1 for r in sl if str(r[0]) >= since90 and not r[2])
        row["last_sale"] = (dict(date=sl[0][0], qty=sl[0][1], is_return=bool(sl[0][2])) if sl else None)
        row["salt"] = None
        if _has(con, "purchase_salt_marg"):
            r = con.execute("SELECT salt FROM purchase_salt_marg WHERE item=? ORDER BY as_on DESC LIMIT 1", (name,)).fetchone()
            row["salt"] = r[0] if r else None
        row["order_rule"] = None
        if _has(con, "order_item_rule"):
            r = con.execute("SELECT rule, value, set_by, set_at FROM order_item_rule WHERE item=?", (name,)).fetchone()
            row["order_rule"] = (dict(rule=r[0], value=r[1], set_by=r[2], set_at=r[3]) if r else None)
        row["section"] = None
        if _has(con, "stock_item_section"):
            r = con.execute("SELECT section FROM stock_item_section WHERE item=?", (name,)).fetchone()
            row["section"] = r[0] if r else None
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pattern", default=PATTERN)
    a = ap.parse_args()
    con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)          # read-only: this script changes nothing
    rows = search(con, a.pattern)
    if a.json:
        print("JSON:" + json.dumps(rows, default=str))
        return 0
    print("name search (%s) -- %d name(s)" % (a.pattern, len(rows)))
    for r in rows:
        st, lp, ls = r["stock"] or {}, r["last_purchase"] or {}, r["last_sale"] or {}
        print("  %-26s strength %-28s packing %-8s stock %s (%s) · suppliers %s · last purchase %s %s qty %s · last sale %s (%d sale lines, %d in 90 days) · salt %s · rule %s · section %s"
              % (r["item"], r["strength"], r["packing"] or "-", st.get("qty", "-"), st.get("words", "-"), ", ".join(r["suppliers"]) or "-",
                 lp.get("date", "-"), lp.get("supplier", ""), lp.get("qty", "-"), ls.get("date", "never"), r["sale_lines_n"], r["sale_lines_90d"],
                 r["salt"] or "-", (r["order_rule"] or {}).get("rule", "-"), r["section"] or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
