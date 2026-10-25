#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replay_s644.py -- walk B.9.7a: the S295 replay (claude_code_briefs/S486_replay: load.py + sim.py, the reference) and the SAME replay with
the KIT'S OWN pure functions (order_rules.model_rate / model_big_day / model_lot / model_interval / model_cap_days / model_level / model_qty /
model_interim_due) in place of the script's inline arithmetic, day by day over the shop's real sales from the real stock, on one nightly copy
of finance.db opened READ-ONLY. The five figures of the kit's run must land within 10 % of the reference's. No person's data is read.

    python -B replay_s644.py --db <finance_nightly.db copy> --app <folder holding order_rules.py> [--as-on dd-mm-yyyy] [--from ISO --to ISO]

--as-on: the Marg closing the stock is rolled back from (default: the newest in stock_snapshot; the anchor day is the day before it)."""
import argparse
import collections
import datetime as dt
import math
import os
import re
import sqlite3
import statistics
import sys


def norm(s):
    s = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", s)


def K(s):
    return norm(str(s or "")[:20])


def units(q, size):
    s = str(q or "").strip()
    if not s or s == "-":
        return 0.0
    if ":" in s:
        a, b = (s.split(":", 1) + ["0"])[:2]
        try:
            return float(a or 0) * size + float(b or 0)
        except ValueError:
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def supkey(s):
    s = norm(s)
    return re.sub(r"\s+BAREIL\w*$", "", s)


D = lambda s: dt.date.fromisoformat(s)   # noqa: E731
DOW = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
ONE = dt.timedelta(1)


def load(db, as_on=None):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    if not as_on:
        ds = [r[0] for r in c.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
        as_on = max(ds, key=lambda x: (x[6:10], x[3:5], x[0:2]))
    A = dt.date(int(as_on[6:10]), int(as_on[3:5]), int(as_on[0:2])) - ONE          # day-end stock of A = Marg's closing as on as_on
    snap = {}
    for item, qty, packing, ps in c.execute("SELECT item, qty, packing, pack_size FROM stock_snapshot WHERE as_on=?", (as_on,)):
        snap.setdefault(K(item), []).append(dict(item=item, qty=float(qty or 0), packing=packing, ps=int(ps or 1) or 1))
    sect = {K(i): s for i, s in c.execute("SELECT item, section FROM stock_item_section")}
    items = {}
    for k, v in snap.items():
        if len(v) > 1 or sect.get(k) == "Orthotics":
            continue
        items[k] = dict(v[0], section=sect.get(k, "?"))
    sales = collections.defaultdict(lambda: collections.defaultdict(float))
    for name, d, q, ret in c.execute("SELECT item_name, business_date, qty_raw, is_return FROM sale_line_item WHERE unit='medical'"):
        k = K(name)
        if k in items:
            sales[k][D(d)] += units(q, items[k]["ps"]) * (-1 if ret else 1)
    sets = {}
    for sn, bn, md5, stamp in c.execute("SELECT l.supplier_norm, l.bill_no, l.source_md5, e.export_stamp FROM purchase_line l JOIN purchase_export e ON e.md5=l.source_md5 "
                                        "WHERE e.superseded_by IS NULL GROUP BY 1,2,3,4"):
        k = (sn, bn)
        if k not in sets or (stamp, md5) > sets[k]:
            sets[k] = (stamp, md5)
    pur = collections.defaultdict(list)
    for sn, bn, bd, item, qty, free, net, amt, direction, md5 in c.execute(
            "SELECT supplier_norm, bill_no, bill_date, item, qty, free, net_amount_p, amount_p, direction, source_md5 FROM purchase_line"):
        if sets.get((sn, bn), (None, None))[1] != md5:
            continue
        k = K(item)
        if k not in items or not bd:
            continue
        ps = items[k]["ps"]
        sign = -1 if (direction or "").upper().startswith("RET") else 1
        q = float(qty or 0)
        f = float(free or 0)
        pur[k].append(dict(date=D(bd), sup=supkey(sn), qty=q, units=sign * (q + f) * ps, bought=sign * q * ps, free=f, net_p=float(net or amt or 0)))
    for k in pur:
        pur[k].sort(key=lambda r: r["date"])
    rules = {supkey(r[0]): dict(cadence=r[1], days=r[2], blocked=r[3] or "", single=int(r[4] or 0), min_order_p=int(r[5] or 50000))
             for r in c.execute("SELECT supplier_norm, cadence, order_days, blocked_days, single_source_extra, min_order_p FROM order_supplier_rule")}
    irules = {K(r[0]): r[1] for r in c.execute("SELECT item, rule FROM order_item_rule")}
    S0 = dt.date(2026, 4, 1)
    days = [S0 + dt.timedelta(n) for n in range((A - S0).days + 1)]
    stock, bad = {}, []
    for k, it in items.items():
        s = it["qty"]
        ser = {A: s}
        pbd = collections.defaultdict(float)
        for p in pur.get(k, []):
            pbd[p["date"]] += p["units"]
        for d in reversed(days[1:]):
            s = s - pbd.get(d, 0.0) + sales[k].get(d, 0.0)
            ser[d - ONE] = s
        stock[k] = ser
        if min(ser.values()) < -0.5 * it["ps"]:
            bad.append(k)
    c.close()
    return dict(items=items, sales={k: dict(v) for k, v in sales.items()}, pur=dict(pur), rules=rules, irules=irules, stock=stock, days=days, bad=set(bad), A=A, as_on=as_on)


def simulate(X, P, OR=None):
    """The reference arithmetic (OR is None) or the kit's (OR = order_rules). Everything else -- the calendar, the dead item, the minimum line
    and order, box rounding, the shop's real sales and stock -- is the same code in both."""
    ITEMS, SALES, PUR, RULES, IRULES, STOCK, DAYS, A = X["items"], X["sales"], X["pur"], X["rules"], X["irules"], X["stock"], X["days"], X["A"]
    E0 = dt.date(2026, 5, 4)
    EVAL = [d for d in DAYS if d >= E0]
    ACTIVE = [k for k in ITEMS if SALES.get(k) and IRULES.get(k) not in ("never", "on_demand", "internal")]
    ORDERABLE = {k for k in ACTIVE if any(p["bought"] > 0 for p in PUR.get(k, []))}
    CLEAN = {k for k in ORDERABLE if k not in X["bad"]}

    def cost(k, d):
        ps = [p for p in PUR.get(k, []) if p["bought"] > 0 and p["net_p"] > 0]
        if not ps:
            return 0.0
        b = [p for p in ps if p["date"] < d] or ps[:1]
        return b[-1]["net_p"] / b[-1]["bought"]
    COST = {k: cost(k, A) for k in ITEMS}

    def supplier(k, d):
        b = [p for p in PUR.get(k, []) if p["date"] < d and p["bought"] > 0]
        return b[-1]["sup"] if b else None
    SUPDATES = collections.defaultdict(set)
    for k, ps in PUR.items():
        for p in ps:
            if p["bought"] > 0:
                SUPDATES[p["sup"]].add(p["date"])

    def rule(s):
        return RULES.get(s) or dict(cadence="weekly", days="MON", blocked="SUN,THU", single=1, min_order_p=50000)

    def blocked(s, d):
        return DOW[d.weekday()] == "SUN" or DOW[d.weekday()] in (rule(s)["blocked"] or "").split(",")

    def learnt_interval(s, d):
        ds = sorted(x for x in SUPDATES.get(s, ()) if d - dt.timedelta(90) <= x < d)
        if OR:
            return OR.model_interval(ds, d - ONE, 3, P["review_default"], P["review_min"], P["review_max"])[0]
        if len(ds) < 3:
            return P["review_default"]
        gaps = [(b - a).days for a, b in zip(ds, ds[1:])]
        v = int(math.floor(statistics.median(gaps) + 0.5))
        return max(P["review_min"], min(P["review_max"], v))

    def fixed_is_day(s, d):
        r = rule(s)
        w = DOW[d.weekday()]
        if w not in (r["days"] or "MON").split(","):
            return False
        if r["cadence"] == "fortnightly":
            return ((d - dt.date(2026, 9, 28)).days // 7) % 2 == 0
        if r["cadence"] == "monthly":
            return d.day <= 7
        return True
    GAP = dict(weekly=7, fortnightly=14, monthly=30, custom=4)
    CAP = dict(weekly=14, fortnightly=21, monthly=45, custom=14)
    stock = {k: max(0.0, STOCK[k][E0 - ONE]) for k in ACTIVE}
    pipe = collections.defaultdict(list)
    last_rev = {}
    for s, ds in SUPDATES.items():
        b = [x for x in ds if x < E0]
        if b:
            last_rev[s] = max(b)
    first_seen = {k: min(list(SALES[k]) + [p["date"] for p in PUR.get(k, [])]) for k in ACTIVE}
    M = collections.Counter()
    inv_c = 0.0
    zero_c = 0
    orders = set()
    lines = 0
    lag = P["lag"]

    def rate_of(k, d):
        end = d - dt.timedelta(lag)
        sd = SALES[k]
        if P["model"] == "fixed":
            tot = sum(sd.get(end - dt.timedelta(n), 0.0) for n in range(0, 28 - lag + 1) if end - dt.timedelta(n) >= d - dt.timedelta(28))
            return max(0.0, tot) / 28.0
        if OR:
            return OR.model_rate(sd, end, 28, P["short"], P["short_min_sell"], P["short_cap"] * 100)[0]

        def win(w):
            u = 0.0
            sell = 0
            for i in range(w):
                q = sd.get(end - dt.timedelta(i), 0.0)
                u += q
                if q > 0:
                    sell += 1
            return max(0.0, u) / w, sell
        rl, _ = win(28)
        rs, sells = win(P["short"])
        r = rl
        if sells >= P["short_min_sell"] and rs > rl:
            r = min(rs, rl * P["short_cap"]) if rl > 0 else rs
        return r

    def lot_of(k, d):
        if OR:
            return OR.model_lot([(p["date"], p["bought"]) for p in PUR.get(k, []) if p["bought"] > 0], d - ONE, 180)
        b = [p["bought"] for p in PUR.get(k, []) if d - dt.timedelta(180) <= p["date"] < d and p["bought"] > 0]
        return statistics.median(b) if b else None

    def box_round(k, need_units):
        ps = ITEMS[k]["ps"]
        strips = math.ceil(need_units / ps)
        if ps > 1:
            strips = max(10, int(math.ceil(strips / 10.0) * 10))
        return strips * ps

    def big_day(k, d):
        end = d - dt.timedelta(lag)
        if OR:
            return OR.model_big_day(SALES[k], end, P["bigday"])[0]
        v = [SALES[k].get(end - dt.timedelta(n), 0.0) for n in range(P["bigday"])]
        v = [x for x in v if x > 0]
        return max(v) if v else 0.0

    def qty_for(k, d, cover, cap, r, on_hand, interim=False):
        bd = big_day(k, d) if (P["bigday"] and r > 0) else 0.0
        level = OR.model_level(r, min(cover, 45), bd) if OR else max(r * min(cover, 45), bd)
        need = level - on_hand
        if need <= 0:
            return 0
        lot = lot_of(k, d) if P["model"] == "levels" else None
        if not lot:
            return box_round(k, need)
        is_new = (d - first_seen[k]).days <= P["new_days"] and not interim
        if OR:
            return OR.model_qty(need, lot, on_hand, r, cap, is_new)[0]
        if is_new:
            return lot
        q = math.ceil(need / lot) * lot
        while q > lot and r > 0 and (on_hand + q) / r > cap:
            q -= lot
        return q
    W0 = D(P["from"]) if P.get("from") else E0
    W1 = D(P["to"]) if P.get("to") else A
    nwin = 0
    for d in EVAL:
        inwin = W0 <= d <= W1
        nwin += inwin
        for k in ACTIVE:
            if pipe[k]:
                arr = sum(u for a, u in pipe[k] if a <= d)
                pipe[k] = [(a, u) for a, u in pipe[k] if a > d]
                stock[k] += arr
        bysup = collections.defaultdict(list)
        for k in ACTIVE:
            s = supplier(k, d)
            if s:
                bysup[s].append(k)
        for s, ks in bysup.items():
            if blocked(s, d):
                continue
            r_ = rule(s)
            if P["model"] == "fixed" or (P.get("kedar_fixed") and r_["cadence"] == "custom"):
                review = fixed_is_day(s, d)
                gap = GAP[r_["cadence"]]
                cap = CAP[r_["cadence"]]
                nxt = next(x for x in (d + dt.timedelta(n) for n in range(1, 62)) if fixed_is_day(s, x))
            else:
                iv = learnt_interval(s, d)
                review = (d - last_rev.get(s, d - dt.timedelta(999))).days >= iv
                g = d + dt.timedelta(iv)
                while blocked(s, g):
                    g += ONE
                gap = (g - d).days
                cap = OR.model_cap_days(iv, 14, 21, 45) if OR else (14 if iv <= 7 else (21 if iv <= 14 else 45))
                nd = max(d + ONE, last_rev.get(s, d - dt.timedelta(999)) + dt.timedelta(iv))
                while blocked(s, nd):
                    nd += ONE
                nxt = nd
            cover = min(gap + 1 + P["safety"] + (3 if r_["single"] else 0), cap)
            todo = []
            out_of = False
            for k in ks:
                on_order = sum(u for a, u in pipe[k])
                on_hand = stock[k] + on_order
                r = rate_of(k, d)
                ls = max([x for x in SALES[k] if x < d and SALES[k][x] > 0] or [dt.date(2000, 1, 1)])
                if (d - ls).days > 60:
                    continue
                if review:
                    q = qty_for(k, d, cover, cap, r, on_hand)
                else:
                    if not P["interim"] or r <= 0:
                        continue
                    horizon = (nxt - d).days + 1 + P["safety"]
                    if P["model"] == "levels":
                        due = OR.model_interim_due(on_hand, r, (nxt - d).days, 1, P["interim_margin"]) if OR else (on_hand / r < (nxt - d).days + 1 + P["interim_margin"])
                    else:
                        due = on_hand / r < horizon
                    if not due:
                        continue
                    q = qty_for(k, d, horizon, cap, r, on_hand, interim=True)
                if q <= 0:
                    continue
                val = q * COST[k]
                if val < 5000 and on_hand > 0:
                    continue
                if stock[k] + on_order <= 0:
                    out_of = True
                todo.append((k, q, val))
            if not todo:
                continue
            if sum(v for _, _, v in todo) < r_["min_order_p"] and not out_of:
                continue
            for k, q, val in todo:
                pipe[k].append((d + ONE, q))
                lines += inwin
            if inwin:
                orders.add((s, d))
            if not review and inwin:
                M["interim_orders"] += 1
            if review:
                last_rev[s] = d
        for k in ACTIVE:
            q = SALES[k].get(d, 0.0)
            if q <= 0:
                stock[k] -= q
            else:
                sold = min(q, stock[k])
                stock[k] -= sold
                if inwin and k in ORDERABLE:
                    M["demand_o"] += q * COST[k]
                    M["unmet_o"] += (q - sold) * COST[k]
            if not inwin:
                continue
            z = stock[k] <= 0 and any(SALES[k].get(d - dt.timedelta(n), 0) > 0 for n in range(1, 29))
            if k in CLEAN:
                inv_c += stock[k] * COST[k]
                if z:
                    zero_c += 1
    n = nwin
    weeks = n / 7.0
    return dict(lost_pct=100.0 * M["unmet_o"] / M["demand_o"] if M["demand_o"] else 0.0, zero_c=zero_c, stock_c=inv_c / n / 100.0,
                orders_wk=len(orders) / weeks, interim=M["interim_orders"] / weeks, lines_wk=lines / weeks, n_clean=len(CLEAN), n_active=len(ACTIVE))


REFINED = dict(model="levels", lag=1, safety=3, short=7, short_cap=2.0, short_min_sell=3, new_days=28, review_min=2, review_max=30, review_default=7,
               interim=True, kedar_fixed=True, interim_margin=1, bigday=28)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--app", required=True)
    ap.add_argument("--as-on", default="")
    ap.add_argument("--from", dest="frm", default="")
    ap.add_argument("--to", default="")
    a = ap.parse_args()
    sys.path.insert(0, os.path.abspath(a.app))
    import order_rules as OR                                   # noqa: E402
    X = load(a.db, a.as_on or None)
    P = dict(REFINED)
    if a.frm:
        P["from"], P["to"] = a.frm, a.to
    ref = simulate(X, P, None)
    kit = simulate(X, P, OR)
    print("replay on %s: closing as on %s, anchor %s, %d medicines sold, %d like-for-like" % (os.path.basename(a.db), X["as_on"], X["A"], ref["n_active"], ref["n_clean"]))
    worst = 0.0
    for name, key in (("lost sale %", "lost_pct"), ("empty-shelf item-days", "zero_c"), ("average stock Rs", "stock_c"), ("supplier orders / week", "orders_wk"), ("lines / week", "lines_wk")):
        r, k = ref[key], kit[key]
        dev = abs(k - r) / r * 100.0 if r else (0.0 if not k else 100.0)
        worst = max(worst, dev)
        print("  %-24s reference %10.2f   kit %10.2f   %5.1f %%" % (name, r, k, dev))
    print("  (between-review orders / week: reference %.1f, kit %.1f)" % (ref["interim"], kit["interim"]))
    print("REPLAY %s -- the kit's arithmetic is within %.1f %% of the reference (10 %% allowed)" % ("OK" if worst <= 10.0 else "RED", worst))
    return 0 if worst <= 10.0 else 1


if __name__ == "__main__":
    sys.exit(main())
