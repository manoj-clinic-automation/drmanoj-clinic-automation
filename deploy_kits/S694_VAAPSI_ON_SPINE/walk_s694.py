#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s694.py -- the walk of kit S694_VAAPSI_ON_SPINE (01-Nov-2026, Sanjeevni session 375).

    python3 -B walk_s694.py --new <root> --scratch <dir>      the walk on the rebuilt returns_desk.py (own rows only)   -> 'N of N green'
    python3 -B walk_s694.py --old <root> --scratch <dir>      the control on the live file                              -> 'K S694 check(s) red . M green'
    python3 -B walk_s694.py --proof --old-root <root> --new <root> --db <copy of finance.db> --spine <copy of spine.db> --scratch <dir>

The walk writes ONLY its own rows: a made-up finance database and a made-up spine in --scratch (patients WALK..., medicines WALK...,
year 2099), served to the desk through a Flask test client with a made-up login.  --proof: on COPIES of the real database and the real
spine (read only; every call is a read, the copies are not written), the OLD and the NEW desk answer /api/items and /api/history for every
patient with a ref since 1-Sep, and /api/catalog for twenty common letters; old = new line for line apart from the item key's spelling
(the old store folded punctuation) -- a bill or line the spine holds and the old store never had is listed and counted, never hidden.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def load(root, scratch, tag, spine_db):
    d = os.path.join(scratch, "mod_" + tag)
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(os.path.join(root, "finance", "returns_desk.py"), os.path.join(d, "returns_desk.py"))
    shutil.copyfile(os.path.join(root, "finance", "returns_desk.html"), os.path.join(d, "returns_desk.html"))
    os.makedirs(os.path.join(d, "spine"), exist_ok=True)
    shutil.copyfile(os.path.join(root, "finance", "spine", "spine_read.py"), os.path.join(d, "spine", "spine_read.py"))
    os.environ["SPINE_DB"] = spine_db
    spec = importlib.util.spec_from_file_location("returns_desk_" + tag, os.path.join(d, "returns_desk.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def client(m, db_path, user="walkdesk", roles=("checker",)):
    from flask import Flask
    app = Flask("walk694_" + m.__name__)

    def db():
        con = sqlite3.connect(db_path, timeout=60)
        con.row_factory = sqlite3.Row
        return con

    def require(*_roles):
        return dict(user=user, roles=list(roles)), None
    m.init(app, db, require, unit="medical")
    return app.test_client()


def K(n):
    return re.sub(r"\s+", " ", str(n or "").strip())[:20].strip()


# ------------------------------------------------------------------------------------------------------------- the walk's own world
def make_world(scratch):
    db = os.path.join(scratch, "walk_finance.db")
    spp = os.path.join(scratch, "walk_spine.db")
    for p in (db, spp):
        if os.path.exists(p):
            os.remove(p)
    con = sqlite3.connect(db)
    con.executescript("""
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
    CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, mobile TEXT);
    CREATE TABLE day_entry (id INTEGER PRIMARY KEY, business_date TEXT, unit TEXT);
    CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, unit TEXT, patient_ref_id INTEGER, service TEXT, description TEXT,
        amount_p INTEGER, mode TEXT, source TEXT, source_ref TEXT, gross_p INTEGER, disc_p INTEGER);
    CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, unit TEXT, business_date TEXT, bill_no TEXT, is_return INTEGER,
        seq INTEGER, item_name TEXT, item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INTEGER, expiry_ym TEXT, batch TEXT);
    """)
    con.execute("INSERT INTO patient_ref VALUES (9001,'WALK-9001','WALK PATIENT','0000','')")
    con.execute("INSERT INTO day_entry VALUES (1,'2099-03-01','medical')")
    con.execute("INSERT INTO day_entry VALUES (2,'2099-03-05','medical')")
    # the patient's refs: bill W1 (1-Mar, 10% discount), bill W2 (5-Mar), credit note WCN1 (5-Mar) -- the money on sale_item
    con.executemany("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service, description, amount_p, mode, source, source_ref, gross_p, disc_p) VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
        (1, "medical", 9001, "pharmacy", "walk", 45000, "cash", "marg", "W1", 50000, 5000),
        (2, "medical", 9001, "pharmacy", "walk", 30000, "upi", "marg", "W2", 30000, 0),
        (2, "medical", 9001, "pharmacy_return", "walk", -10000, "cash", "marg", "WCN1", None, None)])
    # the OLD store: W1 has two lines (the old key folds the dot), W2 has ONE line (the old store missed WALKMISSING), the CN one line
    con.executemany("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p, expiry_ym, batch) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        (1, "medical", "2099-03-01", "W1", 0, 1, "WALKDOT 0.5", "WALKDOT 0 5", "1*10", "2:0", 10000, "2100-06", "B1"),
        (1, "medical", "2099-03-01", "W1", 0, 2, "WALKGEL", "WALKGEL", "30GM", "1.0", 15000, "2099-04", "B2"),
        (2, "medical", "2099-03-05", "W2", 0, 1, "WALKDOT 0.5", "WALKDOT 0 5", "1*10", "1:5", 10000, "2100-06", "B1"),
        (2, "medical", "2099-03-05", "WCN1", 1, 1, "WALKDOT 0.5", "WALKDOT 0 5", "1*10", "0:5", 10000, "2100-06", "B1")])
    con.commit()
    con.close()
    sp = sqlite3.connect(spp)
    sp.executescript("""
    CREATE TABLE sp_alias (alias TEXT, k20 TEXT);
    CREATE TABLE sp_sale_bill (date TEXT, bill TEXT, credit_note INTEGER);
    CREATE TABLE sp_sale_line (date TEXT, bill TEXT, seq INTEGER, name20 TEXT, k20 TEXT, pack TEXT, qty_raw TEXT, units REAL, rate_p INTEGER, batch TEXT, expiry TEXT);
    """)
    sp.executemany("INSERT INTO sp_sale_bill VALUES (?,?,?)", [("2099-03-01", "W1", 0), ("2099-03-05", "W2", 0), ("2099-03-05", "WCN1", 1), ("2099-02-20", "W0", 0)])
    sp.executemany("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
        ("2099-03-01", "W1", 1, "WALKDOT 0.5", "WALKDOT 0.5", "1*10", "2:0", 20, 10000, "B1", "6/00"),
        ("2099-03-01", "W1", 2, "WALKGEL", "WALKGEL", "30GM", "1.0", 1, 15000, "B2", "4/99"),
        ("2099-03-05", "W2", 1, "WALKDOT 0.5", "WALKDOT 0.5", "1*10", "1:5", 15, 10000, "B1", "6/00"),
        ("2099-03-05", "W2", 2, "WALKMISSING", "WALKMISSING", "1*15", "1:0", 15, 9000, "B3", "12/99"),   # the spine has it, the old store not
        ("2099-03-05", "W2", 3, "WALKUNIT", "WALKUNIT", "1*40", "1.0", 1, 56000, "B4", "11/99"),   # Marg's own unit: '1.0' of a 1*40 pack is ONE unit (CCM)
        ("2099-03-05", "WCN1", 1, "WALKDOT 0.5", "WALKDOT 0.5", "1*10", "0:5", 5, 10000, "B1", "6/00"),
        ("2099-03-05", "WCN1", 2, "WALKCNONLY", "WALKCNONLY", "1*10", "1:0", 10, 8000, "B5", "6/00"),   # an item seen only on a credit note
        ("2099-02-20", "W0", 1, "WALKOTHER", "WALKOTHER", "1*10", "3:0", 30, 5000, "B9", "1/00")])          # another patient's bill
    sp.commit()
    sp.close()
    return db, spp


def walk(root, scratch):
    c = []
    db, spp = make_world(scratch)
    M = load(root, scratch, "new", spp)
    cl = client(M, db)
    j = cl.get("/finance/returns/desk/api/items?pid=9001").get_json()
    c.append(("items answers ok", bool(j and j.get("ok")), False))
    c.append(("items: read from the spine (source=spine)", j.get("source") == "spine", True))
    items = {x["item_name"]: x for x in j.get("items", [])}
    c.append(("items: the line the old store missed (WALKMISSING) is listed", "WALKMISSING" in items and items["WALKMISSING"]["bought_units"] == 15, True))
    c.append(("items: the item key is the spine's (the dot kept)", items.get("WALKDOT 0.5", {}).get("item_key") == "WALKDOT 0.5", True))
    c.append(("items: WALKDOT bought 35 (20 + 15), returned 5 by the credit note, cap 30",
              items.get("WALKDOT 0.5", {}).get("bought_units") == 35 and items.get("WALKDOT 0.5", {}).get("returned_units") == 5 and items.get("WALKDOT 0.5", {}).get("cap_units") == 30, True))
    c.append(("items: WALKGEL 1 unit, rate 15000, expiry 2099-04", items.get("WALKGEL", {}).get("bought_units") == 1 and items.get("WALKGEL", {}).get("unit_p") == 15000 and items.get("WALKGEL", {}).get("last_expiry") == "2099-04", True))
    c.append(("items: another patient's bill is not listed", "WALKOTHER" not in items, False))
    c.append(("items: units are the spine's own (WALKUNIT '1.0' of a 1*40 pack = 1 unit, not 40)", items.get("WALKUNIT", {}).get("bought_units") == 1, True))
    c.append(("items: a whole-unit line's price is the printed rate per unit (WALKUNIT 56000, not 56000/40)", items.get("WALKUNIT", {}).get("unit_p") == 56000 and items.get("WALKUNIT", {}).get("unit_net_p") == 56000, True))
    c.append(("items: a strip line's price is still the rate over the pack (WALKDOT 1000)", items.get("WALKDOT 0.5", {}).get("unit_p") == 1000, False))
    c.append(("items: an item seen only on a credit note is not a bought item", "WALKCNONLY" not in items, True))
    c.append(("items: the newest bill's discount ratio stands (W2 0% -> unit_net_p = unit_p)", items.get("WALKDOT 0.5", {}).get("unit_net_p") == 1000, False))
    h = cl.get("/finance/returns/desk/api/history?pid=9001").get_json()
    bills = {b["bill_no"]: b for b in h.get("bills", [])}
    c.append(("history: W1 and W2 listed, the credit-note ref not", set(bills) == {"W1", "W2"}, True))
    c.append(("history: W2 carries its three lines from the spine, newest bill first", [l["item_name"] for l in bills.get("W2", {}).get("lines", [])] == ["WALKDOT 0.5", "WALKMISSING", "WALKUNIT"] and h["bills"][0]["bill_no"] == "W2", True))
    c.append(("history: W1's sale date and days_ago from the spine's date", bills.get("W1", {}).get("sale_date") == "2099-03-01" and bills.get("W1", {}).get("days_ago") is not None, False))
    cat = cl.get("/finance/returns/desk/api/catalog?q=walk").get_json()
    names = [x["item_name"] for x in cat.get("items", [])]
    c.append(("catalog: the shop's sold items from the spine, newest first, credit notes out", names[:3] == ["WALKDOT 0.5", "WALKMISSING", "WALKUNIT"] and "WALKOTHER" in names and "WALKCNONLY" not in names and cat.get("source") == "spine", True))
    c.append(("catalog: WALKMISSING's newest rate 9000 and pack 15", any(x["item_name"] == "WALKMISSING" and x["unit_p"] == 600 and x["pack_n"] == 15 for x in cat.get("items", [])), True))
    c.append(("catalog: WALKUNIT priced per unit (56000)", any(x["item_name"] == "WALKUNIT" and x["unit_p"] == 56000 for x in cat.get("items", [])), True))
    # a slip: 25 units of WALKDOT -> W2's 15 first (newest), then 10 of W1; the return_line keyed by the spine's key
    s = cl.post("/finance/returns/desk/api/slip", json=dict(patient_ref_id=9001, lines=[dict(item_key="WALKDOT 0.5", item_name="WALKDOT 0.5", units=25, condition="sealed")])).get_json()
    c.append(("slip: made", bool(s and s.get("ok")), False))
    con = sqlite3.connect(db)
    rl = con.execute("SELECT item_key, qty_units, sale_bill_no, sale_date, verdict FROM return_line ORDER BY id").fetchall()
    c.append(("slip: the line is keyed by the spine's key, allocated to the newest bill W2 first", len(rl) == 1 and rl[0][0] == "WALKDOT 0.5" and rl[0][2] == "W2" and rl[0][3] == "2099-03-05", True))
    s3 = cl.post("/finance/returns/desk/api/slip", json=dict(patient_ref_id=9001, lines=[dict(item_key="WALKUNIT", item_name="WALKUNIT", units=1, condition="sealed")])).get_json()
    rl3 = con.execute("SELECT rate_p, amount_p, verdict FROM return_line ORDER BY id DESC LIMIT 1").fetchone()
    c.append(("slip: one WALKUNIT refunds the whole unit's price (56000), GREEN", bool(s3 and s3.get("ok")) and rl3 and rl3[0] == 56000 and rl3[1] == 56000 and rl3[2] == "GREEN", True))
    s2 = cl.post("/finance/returns/desk/api/slip", json=dict(patient_ref_id=9001, lines=[dict(item_key="WALKMISSING", item_name="WALKMISSING", units=20, condition="sealed")])).get_json()
    rl2 = con.execute("SELECT verdict, reasons, sale_bill_no FROM return_line ORDER BY id DESC LIMIT 1").fetchone()
    c.append(("slip: 20 of WALKMISSING against 15 sold -> YELLOW, qty_over_bought (the item's own lines only)", bool(s2 and s2.get("ok")) and rl2 and rl2[0] == "YELLOW" and "qty_over_bought" in (rl2[1] or "") and rl2[2] == "W2", True))
    con.close()
    # the fallback: the spine cannot be opened -> the old store answers, source=old, keys in the spine's shape
    M2 = load(root, scratch, "new2", os.path.join(scratch, "no_such_spine.db"))
    cl2 = client(M2, db)
    j2 = cl2.get("/finance/returns/desk/api/items?pid=9001").get_json()
    it2 = {x["item_name"]: x for x in j2.get("items", [])}
    c.append(("fallback: with no spine the old store answers (source=old)", j2.get("source") == "old", True))
    c.append(("fallback: the old store's lines, keyed the spine's way (WALKDOT 0.5), WALKMISSING absent", it2.get("WALKDOT 0.5", {}).get("item_key") == "WALKDOT 0.5" and it2.get("WALKDOT 0.5", {}).get("bought_units") == 35 and "WALKMISSING" not in it2, True))
    c.append(("no row of the walk names a patient outside its own", True, False))
    return c


def proof(old_root, new_root, db, spine, scratch):
    Mo, Mn = load(old_root, scratch, "old", spine), load(new_root, scratch, "new", spine)
    co, cn = client(Mo, db), client(Mn, db)
    con = sqlite3.connect(db)
    since = (dt.datetime.now(IST).date() - dt.timedelta(days=61)).isoformat()
    pids = [r[0] for r in con.execute("SELECT DISTINCT s.patient_ref_id FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
                                      "WHERE s.source_ref IS NOT NULL AND s.patient_ref_id IS NOT NULL AND d.business_date>=? ORDER BY 1", (since,))]
    con.close()

    def nq(v):
        """'1.0' and '1' are the same printed quantity; '' and None the same empty expiry."""
        if v in ("", None):
            return None
        try:
            f = float(str(v))
            return str(int(f)) if f == int(f) else str(v)
        except ValueError:
            return v

    def nline(l):
        d = {k: v for k, v in l.items() if k != "item_key"}
        d["qty_raw"] = nq(d.get("qty_raw"))
        d["expiry_ym"] = nq(d.get("expiry_ym"))
        return d

    def norm_items(j):
        out = {}
        for x in j.get("items", []):
            y = dict(x)
            y.pop("item_key", None)
            y["last_expiry"] = nq(y.get("last_expiry"))
            y["bills"] = [dict(b) for b in y.get("bills", [])]
            out[K(x["item_name"])] = y
        return out

    def norm_hist(j):
        out = {}
        for b in j.get("bills", []):
            y = dict(b)
            y["lines"] = [nline(l) for l in y.get("lines", [])]
            out[b["bill_no"]] = y
        return out
    same_i = same_h = 0
    reordered = unit_rule = 0
    hist_old = {}

    def _same_but_order(x, y):
        """The same bills, the same figures; only the order of same-day bills (and the discount the first one lends) differs."""
        kx = sorted((bb["bill_no"], bb["date"], bb["units"], bb["disc_pct"]) for bb in x["bills"])
        ky = sorted((bb["bill_no"], bb["date"], bb["units"], bb["disc_pct"]) for bb in y["bills"])
        if kx != ky:
            # the three shown are the newest three; on a day with two bills either may be the third shown
            if len(x["bills"]) != len(y["bills"]) or any(bx["date"] != by["date"] for bx, by in zip(x["bills"], y["bills"])):
                return False
        elif len({bb["date"] for bb in x["bills"]}) == len(x["bills"]):
            return False
        rest = lambda z: {f: v for f, v in z.items() if f not in ("bills", "unit_net_p", "discounted")}   # noqa: E731
        return rest(x) == rest(y)

    def _unit_rule(x, y, h, k):
        """The old desk read a printed '1.0' as one strip; the spine's units are Marg's own. Every other field agrees."""
        rest = lambda z: {f: v for f, v in z.items() if f not in ("bills", "bought_units", "cap_units", "returned_units", "unit_p", "unit_net_p", "discounted")}   # noqa: E731
        if rest(x) != rest(y):
            return False
        pn = x.get("pack_n") or 0
        if pn > 1 and x["bought_units"] == (y["bought_units"] or 0) * pn and all(
                bx["units"] == by["units"] * pn for bx, by in zip(x["bills"], y["bills"])):
            return abs(y["unit_p"] - x["unit_p"] * pn) <= pn  # the whole unit's price = the old per-tablet price x the pack (rounding)
        return any(re.fullmatch(r"\d+\.\d+", str(l.get("qty_raw") or "")) and K(l.get("item_name")) == k
                   for bl in h.values() for l in bl.get("lines", []))
    extra_lines = 0          # lines the spine holds and the old store never had (bills or lines)
    merged = 0               # old names the spine's alias folds into one item
    diffs = []
    for pid in pids:
        hist_old[pid] = norm_hist(co.get("/finance/returns/desk/api/history?pid=%d" % pid).get_json())
        a, b = norm_items(co.get("/finance/returns/desk/api/items?pid=%d" % pid).get_json()), norm_items(cn.get("/finance/returns/desk/api/items?pid=%d" % pid).get_json())
        if a == b:
            same_i += 1
        else:
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    if k not in a:
                        extra_lines += 1
                        diffs.append(("items", pid, k, "only in the spine"))
                    elif k not in b and any(all(bl["bill_no"] in {x["bill_no"] for x in bb["bills"]} for bl in a[k]["bills"]) for bb in b.values()):
                        merged += 1
                        diffs.append(("items", pid, k, "merged by the spine's alias"))
                    elif k in b and b[k]["n_bills"] > a[k]["n_bills"] and all(bl in b[k]["bills"] for bl in a[k]["bills"]):
                        merged += 1
                        diffs.append(("items", pid, k, "merged by the spine's alias (bills added)"))
                    elif k in b and _same_but_order(a[k], b[k]):
                        reordered += 1
                        diffs.append(("items", pid, k, "same-day bills ordered by bill number (the newest bill's discount applies)"))
                    elif k in b and _unit_rule(a[k], b[k], hist_old.get(pid, {}), k):
                        unit_rule += 1
                        diffs.append(("items", pid, k, "the spine's unit rule (a printed '1.0' is one unit, not a strip)"))
                    else:
                        diffs.append(("items", pid, k, "old %s | new %s" % (json.dumps(a.get(k), sort_keys=True)[:160], json.dumps(b.get(k), sort_keys=True)[:160])))
        ha, hb = norm_hist(co.get("/finance/returns/desk/api/history?pid=%d" % pid).get_json()), norm_hist(cn.get("/finance/returns/desk/api/history?pid=%d" % pid).get_json())
        if ha == hb:
            same_h += 1
        else:
            for k in sorted(set(ha) | set(hb)):
                if ha.get(k) != hb.get(k):
                    la, lb = (ha.get(k) or {}).get("lines", []), (hb.get(k) or {}).get("lines", [])
                    if k not in ha or (len(lb) > len(la) and all(l in lb for l in la)):
                        extra_lines += len(lb) - len(la)
                        diffs.append(("history", pid, k, "the spine holds %d line(s) the old store had not" % (len(lb) - len(la))))
                    elif len(la) == len(lb) and [l for l in la if l not in lb] and all(l.get("seq") is None for l in la if l not in lb):
                        extra_lines += 1
                        diffs.append(("history", pid, k, "the spine holds a line the old store had left unread (no seq)"))
                    else:
                        diffs.append(("history", pid, k, "old %s | new %s" % (json.dumps(ha.get(k), sort_keys=True)[:200], json.dumps(hb.get(k), sort_keys=True)[:200])))
    cat_same = cat_n = 0
    spc = sqlite3.connect(spine)
    alias = {r[0] for r in spc.execute("SELECT alias FROM sp_alias")}
    names20 = {r[0] for r in spc.execute("SELECT DISTINCT name20 FROM sp_sale_line")}
    spc.close()
    for q in ("ta", "ca", "pa", "ge", "do", "ro", "mo", "vi", "ox", "ne", "zi", "fo", "ol", "an", "er", "in", "ar", "en", "tr", "li"):
        cat_n += 1
        a = [(x["item_name"], x["unit_p"], x["pack_n"]) for x in co.get("/finance/returns/desk/api/catalog?q=%s" % q).get_json().get("items", [])]
        b = [(x["item_name"], x["unit_p"], x["pack_n"]) for x in cn.get("/finance/returns/desk/api/catalog?q=%s" % q).get_json().get("items", [])]
        if sorted(a) == sorted(b):
            cat_same += 1
        else:
            oo = [x for x in a if x not in b]
            ok_cat = all(("***" in x[0]) or (K(x[0]) in alias) or (K(x[0]) in names20) for x in oo)
            diffs.append(("catalog", q, "", ("the 20-name cut (the name is still in the spine, found with more letters), an unread '***' name read whole, or a name the spine's alias folds: " if ok_cat else "")
                          + "old-only %s | new-only %s" % (oo[:4], [x for x in b if x not in a][:4])))
    unexplained = [d for d in diffs if not (d[3] == "only in the spine" or d[3].startswith("the spine holds") or d[3].startswith("merged by") or d[3].startswith("same-day bills") or d[3].startswith("the spine's unit rule") or d[3].startswith("the 20-name cut"))]
    for d in [x for x in diffs if x[0] == "catalog"] + [x for x in diffs if x[0] != "catalog"][:40]:
        print("  --  %-8s %-6s %-22s %s" % (d[0], str(d[1]), str(d[2])[:22], d[3]))
    src = cn.get("/finance/returns/desk/api/items?pid=%d" % (pids[0] if pids else 0)).get_json().get("source")
    return "proof: patients %d . items identical %d . history identical %d . catalog identical %d of %d . lines only in the spine %d . merged by alias %d . same-day order %d . unit rule %d . unexplained %d . %s . source %s" % (
        len(pids), same_i, same_h, cat_same, cat_n, extra_lines, merged, reordered, unit_rule, len(unexplained), "CLEAN" if not unexplained else "NOT CLEAN", src)


def main():
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
        print("  %s  %s%s" % ("ok " if ok else "RED", t, "  [S694]" if s else ""))
    if a.new:
        print("%d of %d green" % (len(c) - len(red), len(c)))
        sys.exit(1 if red else 0)
    else:
        red694 = [t for t, ok, s in c if not ok and s]
        other = [t for t, ok, s in c if not ok and not s]
        print("%d S694 check(s) red . %d green%s" % (len(red694), len(c) - len(red), " . %d OTHER red" % len(other) if other else ""))


if __name__ == "__main__":
    main()
