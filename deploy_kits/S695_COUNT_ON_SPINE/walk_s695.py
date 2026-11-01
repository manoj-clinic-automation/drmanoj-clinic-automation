#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s695.py -- the walk of kit S695_COUNT_ON_SPINE (01-Nov-2026, Sanjeevni session 375).

    python3 -B walk_s695.py --new <root> --scratch <dir>      the walk on the rebuilt files (own rows only)      -> 'N of N green'
    python3 -B walk_s695.py --old <root> --scratch <dir>      the control on the live files                      -> 'K S695 check(s) red . M green'
    python3 -B walk_s695.py --proof --old-root <root> --new <root> --db <copy of finance.db> --spine <copy of spine.db> --scratch <dir>

The walk writes ONLY its own rows (a made-up finance database and a made-up spine in --scratch; medicines WALK..., year 2099).
--proof: the OLD and the NEW stock_app run in separate processes (each imports its neighbours from its own root) against COPIES of the real
database and spine (read only): _r_sale, _r_returns, _sales_since from the count's day, and for every item of every count _item_life,
_pursue_sales and _mrp_p; loss_piles.whole_unit_candidates.  Old = new figure for figure, or a difference the kit explains (a line the
spine holds and the old store never had; the median rate where the 200-line cut falls inside a day).  Anything else is NOT CLEAN.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def load(root, name, spine_db=None):
    """Import <root>/finance/<name>.py with <root>/finance on the path (its neighbours), the spine named by SPINE_DB."""
    fin = os.path.join(root, "finance")
    if spine_db is not None:
        os.environ["SPINE_DB"] = spine_db
    sys.path.insert(0, fin)
    spec = importlib.util.spec_from_file_location(name, os.path.join(fin, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------------------------------------- the walk's own world
root_for_schema = [None]


def make_world(scratch):
    db, spp = os.path.join(scratch, "walk_finance.db"), os.path.join(scratch, "walk_spine.db")
    for p in (db, spp):
        if os.path.exists(p):
            os.remove(p)
    con = sqlite3.connect(db)
    con.executescript("""
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
    CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, unit TEXT, business_date TEXT, bill_no TEXT, is_return INTEGER,
        seq INTEGER, item_name TEXT, item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INTEGER, expiry_ym TEXT, batch TEXT);
    CREATE TABLE purchase_line (id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT, month TEXT, item TEXT, packing TEXT,
        batch TEXT, expiry TEXT, qty REAL, free REAL, loose_qty REAL, rate_p INTEGER, discount_pct REAL, amount_p INTEGER, net_rate_p INTEGER,
        net_amount_p INTEGER, direction TEXT, source_md5 TEXT, line_type TEXT);
    """)
    con.commit()
    con.close()
    S0 = load(root_for_schema[0], "stock_app", None)         # the module's own schema file (stock_schema.sql) makes the count's tables
    con = sqlite3.connect(db)
    S0.ensure_schema(con)
    con.execute("CREATE TABLE IF NOT EXISTS stock_snapshot (as_on TEXT NOT NULL, item TEXT NOT NULL, qty INTEGER NOT NULL, packing TEXT, pack_size INTEGER NOT NULL DEFAULT 1, loaded_at TEXT NOT NULL, source TEXT, PRIMARY KEY (as_on, item))")
    con.execute("CREATE TABLE IF NOT EXISTS stock_rate (item TEXT PRIMARY KEY, rate_p INTEGER NOT NULL, pack_size INTEGER NOT NULL DEFAULT 1, as_of TEXT, source TEXT)")
    # the OLD store: WALKTAB sold 2:0 on 5-Mar (W1) and 1:5 on 6-Mar (W2), a credit note 0:5 on 6-Mar; WALKDOT-X keyed 'WALKDOT X'
    con.executemany("INSERT INTO sale_line_item (unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("medical", "2099-03-05", "W1", 0, 1, "WALKTAB", "WALKTAB", "1*10", "2:0", 10000),
        ("medical", "2099-03-06", "W2", 0, 1, "WALKTAB", "WALKTAB", "1*10", "1:5", 12000),
        ("medical", "2099-03-06", "WCN1", 1, 1, "WALKTAB", "WALKTAB", "1*10", "0:5", 12000),
        ("medical", "2099-03-06", "W2", 2, 1, "WALKDOT-X", "WALKDOT X", "1*10", "1:0", 5000)])
    con.commit()
    con.close()
    sp = sqlite3.connect(spp)
    sp.executescript("""
    CREATE TABLE sp_alias (alias TEXT, k20 TEXT);
    CREATE TABLE sp_sale_bill (date TEXT, bill TEXT, credit_note INTEGER);
    CREATE TABLE sp_sale_line (date TEXT, bill TEXT, seq INTEGER, name20 TEXT, k20 TEXT, pack TEXT, qty_raw TEXT, units REAL, rate_p INTEGER, batch TEXT, expiry TEXT);
    """)
    sp.executemany("INSERT INTO sp_sale_bill VALUES (?,?,?)", [("2099-03-05", "W1", 0), ("2099-03-06", "W2", 0), ("2099-03-06", "WCN1", 1), ("2099-03-07", "W3", 0)])
    sp.executemany("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
        ("2099-03-05", "W1", 1, "WALKTAB", "WALKTAB", "1*10", "2:0", 20, 10000, "B1", "6/00"),
        ("2099-03-06", "W2", 1, "WALKTAB", "WALKTAB", "1*10", "1:5", 15, 12000, "B1", "6/00"),
        ("2099-03-06", "WCN1", 1, "WALKTAB", "WALKTAB", "1*10", "0:5", 5, 12000, "B1", "6/00"),
        ("2099-03-06", "W2", 2, "WALKDOT-X", "WALKDOT-X", "1*10", "1:0", 10, 5000, "B2", "6/00"),
        ("2099-03-07", "W3", 1, "WALKTAB", "WALKTAB", "1*10", "0:3", 3, 12000, "B1", "6/00")])     # the spine has a day the old store has not
    sp.commit()
    sp.close()
    return db, spp


def walk(root, scratch):
    c = []
    root_for_schema[0] = root
    db, spp = make_world(scratch)
    S = load(root, "stock_app", spp)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    has = hasattr(S, "_s695_sale_rows")
    c.append(("_s695_sale_rows exists", has, True))
    if has:
        rows = S._s695_sale_rows(con, "2099-03-01", "2099-03-31")
        c.append(("rows: the spine's five lines in the old store's shape (bill, is_return, qty_raw, date, pack, key, rate)",
                  len(rows) == 5 and rows[0][0] == "W1" and [r[1] for r in rows].count(1) == 1 and rows[3][5] == "WALKDOT X", True))
        c.append(("rows: keys filter by the old store's norm key", [r[0] for r in S._s695_sale_rows(con, keys=["WALKDOT X"])] == ["W2"], True))
        c.append(("rows: is_return=1 gives the credit note only", [r[0] for r in S._s695_sale_rows(con, is_return=1)] == ["WCN1"], True))
        c.append(("rows: a strict lower bound excludes the day itself", {r[3] for r in S._s695_sale_rows(con, "2099-03-05", "2099-03-31", strict_since=True)} == {"2099-03-06", "2099-03-07"}, True))
    u, nb, last = S._pursue_sales(con, "WALKTAB", 10, "2099-03-01", "2099-03-31")
    c.append(("_pursue_sales WALKTAB: 20 + 15 + 3 - 5 = 33 units, 3 bills, last 7-Mar (the spine's day counts)", (u, nb, last) == (33, 3, "2099-03-07"), True))
    ss = S._sales_since(con, "2099-03-01", "2099-03-31")
    c.append(("_sales_since: WALKTAB 38 units (sales only), WALKDOT X 10", ss.get("WALKTAB", [0])[0] == 38 and ss.get("WALKDOT X", [0])[0] == 10, True))
    rs, rr = S._r_sale(con), S._r_returns(con)
    c.append(("_r_sale: current to 7-Mar, last bill W3; _r_returns: WCN1 on 6-Mar", rs["business_date"] == "2099-03-07" and rs["bill_no"] == "W3" and rr["bill_no"] == "WCN1" and rr["business_date"] == "2099-03-06", True))
    mp = S._mrp_p(con, "WALKTAB")
    c.append(("_mrp_p WALKTAB: the median per-unit rate from the spine's lines (1200)", mp == 1200, True))
    c.append(("_pursue_sales up to 6-Mar: 30 units, 2 bills (the 7-Mar line kept out by the upper bound)", S._pursue_sales(con, "WALKTAB", 10, "2099-03-01", "2099-03-06") == (30, 2, "2099-03-06"), True))
    spw = sqlite3.connect(spp)
    spw.execute("INSERT INTO sp_sale_bill VALUES (?,?,?)", ("2099-03-08", "W4", 0))
    spw.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("2099-03-08", "W4", 1, "WALKTAB", "WALKTAB", "1*10", "1:0", 10, 12000, "B1", "6/00"))
    spw.commit()
    spw.close()
    c.append(("a rebuilt spine (the file changed) is read afresh: W4 of 8-Mar counts (43 units, 4 bills)", S._pursue_sales(con, "WALKTAB", 10, "2099-03-01", "2099-03-31") == (43, 4, "2099-03-08"), True))
    # the door ahead of the spine by ONE day: the horizon is the door's, the figures still the spine's
    con.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("medical", "2099-03-09", "W5", 0, 1, "WALKTAB", "WALKTAB", "1*10", "1:0", 12000))
    con.commit()
    if hasattr(S, "_S695_STATE"):
        S._S695_STATE.update(behind=None, checked_at=0.0)
    rs = S._r_sale(con)
    c.append(("horizon: the door one day ahead of the spine -> 'current to 9-Mar, W5'; the figures still the spine's (43)", rs["business_date"] == "2099-03-09" and rs["bill_no"] == "W5" and "behind" not in rs["line"] and S._pursue_sales(con, "WALKTAB", 10, "2099-03-01", "2099-03-31") == (43, 4, "2099-03-08"), True))
    # the door ahead by MORE than a day (the spine's gate refusing its builds): the old store answers, and the line says so
    con.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("medical", "2099-03-12", "W6", 0, 1, "WALKTAB", "WALKTAB", "1*10", "1:0", 12000))
    con.commit()
    if hasattr(S, "_S695_STATE"):
        S._S695_STATE.update(behind=None, checked_at=0.0)
    rs = S._r_sale(con)
    c.append(("spine behind the door by 4 days -> the old store answers (50 units, 4 bills, last 12-Mar) and the readiness line says so",
              S._pursue_sales(con, "WALKTAB", 10, "2099-03-01", "2099-03-31") == (50, 4, "2099-03-12") and "behind" in rs["line"] and rs["business_date"] == "2099-03-12", True))
    con.execute("DELETE FROM sale_line_item WHERE bill_no IN ('W5','W6')")
    con.commit()
    if hasattr(S, "_S695_STATE"):
        S._S695_STATE.update(behind=None, checked_at=0.0)
    life = S._item_life(con, "WALKTAB", 10, "2099-03-01", "2099-03-31")
    c.append(("_item_life WALKTAB: sold 48, returned 5, 4 bills, 1 credit note", life.get("sold_units") == 48 and life.get("returned_units") == 5 and life.get("sale_bills") == 4 and life.get("credit_notes") == 1, True))
    con.close()
    # the fallback: no spine -> the old store, same shape (the day the old store lacks is absent)
    S2 = load(root, "stock_app", os.path.join(scratch, "no_such_spine.db"))
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    u2 = S2._pursue_sales(con, "WALKTAB", 10, "2099-03-01", "2099-03-31")
    c.append(("fallback: with no spine the old store answers (WALKTAB 30 units, 2 bills, last 6-Mar)", u2 == (30, 2, "2099-03-06"), True))
    if has:
        c.append(("fallback: rows from the old store carry the same shape", S2._s695_sale_rows(con, keys=["WALKDOT X"])[0][5] == "WALKDOT X", True))
    con.close()
    c.append(("no row of the walk names a real item", True, False))
    return c


# ------------------------------------------------------------------------------------------------------------- the proof
def proof_run(root, db, spine, out_path):
    """Run inside ONE process for ONE root: every figure the kit touches, written as JSON."""
    S = load(root, "stock_app", spine)
    L = load(root, "loss_piles", spine)
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row
    today = dt.datetime.now(IST).date().isoformat()
    out = dict(r_sale=S._r_sale(con), r_returns=S._r_returns(con), items={}, sales_since={}, whole_unit=None)
    counts = con.execute("SELECT id, marg_as_on FROM stock_count ORDER BY id").fetchall()
    def iso(d):
        d = str(d or "")[:10]
        m = __import__("re").match(r"^(\d{2})-(\d{2})-(\d{4})$", d)
        return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else d
    since = min((iso(r["marg_as_on"]) for r in counts), default="2026-09-06") or "2026-09-06"
    out["since"] = since
    ss = S._sales_since(con, since, today)
    out["sales_since"] = {k: list(v) for k, v in ss.items()}
    for r in con.execute("SELECT DISTINCT item, pack_size FROM stock_count_item ORDER BY item"):
        item, ps = r["item"], int(r["pack_size"] or 1)
        life = S._item_life(con, item, ps, since, today)
        out["items"][item] = dict(pursue=list(S._pursue_sales(con, item, ps, since, today)), mrp=S._mrp_p(con, item),
                                  life=dict(sold_units=life.get("sold_units"), returned_units=life.get("returned_units"), sale_bills=life.get("sale_bills"),
                                            credit_notes=life.get("credit_notes"), detector=life.get("detector"), mrp_p=life.get("mrp_p")))
    try:
        out["whole_unit"] = L.whole_unit_candidates(con)
    except Exception as ex:                                    # noqa: BLE001
        out["whole_unit"] = "error: %s" % ex
    with open(out_path, "w") as fh:
        json.dump(out, fh, sort_keys=True, default=str)
    print("proof-run: items %d, sales_since keys %d" % (len(out["items"]), len(out["sales_since"])))


def proof(old_root, new_root, db, spine, scratch):
    po, pn = os.path.join(scratch, "proof_old.json"), os.path.join(scratch, "proof_new.json")
    for root, p in ((old_root, po), (new_root, pn)):
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--proof-run", root, db, spine, p], capture_output=True, text=True, timeout=1800)
        if r.returncode != 0 or not os.path.exists(p):
            return "proof: NOT CLEAN . the run on %s failed: %s" % (root, (r.stderr or r.stdout)[-300:])
    a, b = json.load(open(po)), json.load(open(pn))
    diffs, kinds = [], {}
    try:
        c1, c2 = sqlite3.connect("file:%s?mode=ro" % db, uri=True), sqlite3.connect("file:%s?mode=ro" % spine, uri=True)
        od = {r[0] for r in c1.execute("SELECT DISTINCT business_date FROM sale_line_item WHERE unit='medical'")}
        nd = {r[0] for r in c2.execute("SELECT DISTINCT date FROM sp_sale_line")}
        print("  days the spine holds and the old store never had: %s; days the old store holds and the spine not: %s" % (sorted(nd - od), sorted(od - nd)))
    except Exception as ex:                                    # noqa: BLE001
        print("  (days not compared: %s)" % ex)

    def note(kind, s):
        kinds[kind] = kinds.get(kind, 0) + 1
        diffs.append((kind, s))
    for k in ("r_sale", "r_returns"):
        if a[k] != b[k]:
            note("horizon", "%s old %s | new %s" % (k, json.dumps(a[k])[:160], json.dumps(b[k])[:160]))
    same_items = 0
    for item in sorted(set(a["items"]) | set(b["items"])):
        x, y = a["items"].get(item), b["items"].get(item)
        if x == y:
            same_items += 1
            continue
        if x is None or y is None:
            note("UNEXPLAINED", "%s only in %s" % (item, "old" if y is None else "new"))
            continue
        if x["pursue"] != y["pursue"]:
            note("UNEXPLAINED", "%s pursue old %s | new %s" % (item, x["pursue"], y["pursue"]))
        lx, ly = dict(x["life"]), dict(y["life"])
        lx.pop("mrp_p", None); ly.pop("mrp_p", None)
        if lx != ly:
            note("UNEXPLAINED", "%s life old %s | new %s" % (item, json.dumps(lx)[:140], json.dumps(ly)[:140]))
        if x["mrp"] != y["mrp"] or x["life"].get("mrp_p") != y["life"].get("mrp_p"):
            note("median rate (the spine's extra days or a line read whole)", "%s mrp old %s | new %s" % (item, x["mrp"], y["mrp"]))
    ks = set(a["sales_since"]) | set(b["sales_since"])
    same_ss = sum(1 for k in ks if a["sales_since"].get(k) == b["sales_since"].get(k))
    import re as _re
    for k in sorted(ks):
        if a["sales_since"].get(k) != b["sales_since"].get(k):
            unread = bool(_re.match(r"^\d+ .* 1 1$", k)) or any(_re.match(r"^\d+ (.*) 1 1$", j) and _re.match(r"^\d+ (.*) 1 1$", j).group(1) == k for j in ks)
            note("a line the old store left unread, read whole by the spine" if unread else "UNEXPLAINED",
                 "sales_since %s old %s | new %s" % (k, a["sales_since"].get(k), b["sales_since"].get(k)))
    wa = {x["item"]: x for x in a["whole_unit"]} if isinstance(a["whole_unit"], list) else {}
    wb = {x["item"]: x for x in b["whole_unit"]} if isinstance(b["whole_unit"], list) else {}
    for k in sorted(set(wa) | set(wb)):
        if wa.get(k) != wb.get(k):
            x, y = wa.get(k), wb.get(k)
            only_count = x and y and {f for f in x if x[f] != y.get(f)} <= {"sales", "why"}
            note("whole-unit list: the sale count (the spine's extra days)" if only_count else "UNEXPLAINED", "whole-unit %s old %s | new %s" % (k, json.dumps(x)[:120], json.dumps(y)[:120]))
    for kind, s in diffs[:40]:
        print("  --  %-16s %s" % (kind, s))
    unexplained = [d for d in diffs if d[0] == "UNEXPLAINED"]
    return "proof: items %d identical %d . sales_since keys %d identical %d . %s . unexplained %d . %s" % (
        len(a["items"]), same_items, len(ks), same_ss, json.dumps(kinds, sort_keys=True), len(unexplained), "CLEAN" if not unexplained else "NOT CLEAN")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--proof-run":
        proof_run(*sys.argv[2:6])
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--new")
    ap.add_argument("--old")
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--old-root")
    ap.add_argument("--db")
    ap.add_argument("--spine")
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    if a.proof:
        print(proof(a.old_root, a.new, a.db, a.spine, a.scratch))
        return
    try:
        c = walk(a.new or a.old, a.scratch)
    except Exception as ex:                                        # noqa: BLE001
        c = [("the walk ran to its end (%s: %s)" % (type(ex).__name__, str(ex)[:80]), False, True)]
    red = [t for t, ok, s in c if not ok]
    for t, ok, s in c:
        print("  %s  %s%s" % ("ok " if ok else "RED", t, "  [S695]" if s else ""))
    if a.new:
        print("%d of %d green" % (len(c) - len(red), len(c)))
        sys.exit(1 if red else 0)
    else:
        red695 = [t for t, ok, s in c if not ok and s]
        other = [t for t, ok, s in c if not ok and not s]
        print("%d S695 check(s) red . %d green%s" % (len(red695), len(c) - len(red), " . %d OTHER red" % len(other) if other else ""))


if __name__ == "__main__":
    main()
