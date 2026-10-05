# S295 replay -- the simulator. Each policy is run day by day over the same real demand (the shop's own sales), starting from the
# same real stock, ordering from each item's real last supplier, goods arriving the next morning. Nothing is fitted to the future:
# every rate, lot and rhythm is computed from the days before the day it is used.
import pickle, os, math, datetime as dt, statistics, collections, sys, json
X = pickle.load(open(os.path.expanduser("~/replay/data.pkl"), "rb"))
ITEMS, SALES, PUR, RULES, IRULES, STOCK, DAYS, A = X["items"], X["sales"], X["pur"], X["rules"], X["irules"], X["stock"], X["days"], X["A"]
E0 = dt.date(2026, 5, 4)
EVAL = [d for d in DAYS if d >= E0]
ONE = dt.timedelta(1)
DOW = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
BADK = {k for k, _ in X["bad"]}
ACTIVE = [k for k in ITEMS if SALES.get(k) and IRULES.get(k) not in ("never", "on_demand", "internal")]
ORDERABLE = {k for k in ACTIVE if any(p["bought"] > 0 for p in PUR.get(k, []))}
CLEAN = {k for k in ORDERABLE if k not in BADK}
def cost(k, d):                                               # paise per unit, the last purchase before d (else the first ever)
    ps = [p for p in PUR.get(k, []) if p["bought"] > 0 and p["net_p"] > 0]
    if not ps: return 0.0
    b = [p for p in ps if p["date"] < d] or ps[:1]
    return b[-1]["net_p"] / b[-1]["bought"]
COST = {k: cost(k, A) for k in ITEMS}
def supplier(k, d):
    b = [p for p in PUR.get(k, []) if p["date"] < d and p["bought"] > 0]
    return b[-1]["sup"] if b else None
SUPDATES = collections.defaultdict(set)
for k, ps in PUR.items():
    for p in ps:
        if p["bought"] > 0: SUPDATES[p["sup"]].add(p["date"])
def rule(s): return RULES.get(s) or dict(cadence="weekly", days="MON", blocked="SUN,THU", single=1, min_order_p=50000)
def blocked(s, d): return DOW[d.weekday()] == "SUN" or DOW[d.weekday()] in (rule(s)["blocked"] or "").split(",")
def learnt_interval(s, d, P):
    ds = sorted(x for x in SUPDATES.get(s, ()) if d - dt.timedelta(90) <= x < d)
    if len(ds) < 3: return P["review_default"]
    gaps = [(b - a).days for a, b in zip(ds, ds[1:])]
    v = int(math.floor(statistics.median(gaps) + 0.5))
    return max(P["review_min"], min(P["review_max"], v))
def fixed_is_day(s, d):
    r = rule(s); w = DOW[d.weekday()]
    if w not in (r["days"] or "MON").split(","): return False
    if r["cadence"] == "fortnightly": return ((d - dt.date(2026, 9, 28)).days // 7) % 2 == 0
    if r["cadence"] == "monthly": return d.day <= 7
    return True
GAP = dict(weekly=7, fortnightly=14, monthly=30, custom=4)
CAP = dict(weekly=14, fortnightly=21, monthly=45, custom=14)
def run(P):
    name = P["name"]
    stock = {k: max(0.0, STOCK[k][E0 - ONE]) for k in ACTIVE}
    pipe = collections.defaultdict(list)                       # k -> [(arrival_day, units)]
    hist = {k: {} for k in ACTIVE}                             # day-end sim stock
    last_rev = {}
    for s, ds in SUPDATES.items():
        b = [x for x in ds if x < E0]
        if b: last_rev[s] = max(b)
    first_seen = {k: min(list(SALES[k]) + [p["date"] for p in PUR.get(k, [])]) for k in ACTIVE}
    M = collections.Counter(); inv_c = 0.0; zero_c = 0; unmet_item = collections.Counter(); inv_p = 0.0; orders = set(); lines = 0; bought_p = 0.0; zero_days = 0; unmet_days = 0; cover_num = 0.0
    lag = P["lag"]
    def rate_of(k, d):
        end = d - dt.timedelta(lag)
        sd = SALES[k]
        if P["model"] == "fixed":
            tot = sum(sd.get(end - dt.timedelta(n), 0.0) for n in range(0, 28 - lag + 1) if end - dt.timedelta(n) >= d - dt.timedelta(28))
            return max(0.0, tot) / 28.0, None
        def win(w):
            lo = max(end - dt.timedelta(w - 1), first_seen[k])
            n = (end - lo).days + 1
            if n <= 0: return 0.0, 0, 0
            u = 0.0; instock = 0; sell = 0
            for i in range(n):
                x = lo + dt.timedelta(i); q = sd.get(x, 0.0); u += q
                st = hist[k].get(x, STOCK[k].get(x, 1.0))
                if st > 0 or q > 0: instock += 1
                if q > 0: sell += 1
            den = max(instock, math.ceil(w * P["min_instock"])) if P["instock"] else w
            return max(0.0, u) / den, sell, instock
        rl, _, _ = win(28); rs, sells, _ = win(P["short"])
        r = rl
        if P["use_short"] and sells >= P["short_min_sell"] and rs > rl:
            r = min(rs, rl * P["short_cap"]) if rl > 0 else rs
        return r, (rl, rs)
    def lot_of(k, d):
        b = [p["bought"] for p in PUR.get(k, []) if d - dt.timedelta(180) <= p["date"] < d and p["bought"] > 0]
        if not b: return None
        q = P.get("lot_q", 0.5)
        if q == 0.5: return statistics.median(b)
        b = sorted(b); return b[min(len(b) - 1, int(q * len(b)))]
    def box_round(k, need_units, d):                           # today's rails: strips to tens (min 10); units as they are
        ps = ITEMS[k]["ps"]; strips = math.ceil(need_units / ps)
        if ps > 1: strips = max(10, int(math.ceil(strips / 10.0) * 10))
        return strips * ps
    def qty_for(k, d, cover, cap, r, on_hand, interim=False):
        level = r * min(cover, 45)
        fp = P.get("floor_packs", 0)
        if fp and r > 0: level = max(level, fp * ITEMS[k]["ps"] + 1e-9)
        bd = P.get("bigday", 0)
        if bd and r > 0:
            end = d - dt.timedelta(P["lag"]); v = sorted(SALES[k].get(end - dt.timedelta(n), 0.0) for n in range(bd))
            v = [x for x in v if x > 0]
            if v: level = max(level, v[-1] if P.get("bigday_q", 1.0) >= 1.0 else v[min(len(v) - 1, int(P["bigday_q"] * len(v)))])
        need = level - on_hand
        if need <= 0: return 0
        lot = lot_of(k, d) if P["model"] == "levels" and P["use_lot"] else None
        if not lot: return box_round(k, need, d)
        if (d - first_seen[k]).days <= P["new_days"] and not interim: return lot
        q = math.ceil(need / lot) * lot
        while q > lot and r > 0 and (on_hand + q) / r > cap: q -= lot
        return q
    W0 = dt.date.fromisoformat(P['from']) if P.get('from') else E0; W1 = dt.date.fromisoformat(P['to']) if P.get('to') else A; nwin = 0
    for d in EVAL:
        inwin = W0 <= d <= W1; nwin += inwin
        for k in ACTIVE:                                       # arrivals of the morning
            if pipe[k]:
                arr = sum(u for a, u in pipe[k] if a <= d); pipe[k] = [(a, u) for a, u in pipe[k] if a > d]; stock[k] += arr
        # ---- ordering (afternoon; what it knows: sales through d-lag, stock now)
        bysup = collections.defaultdict(list)
        for k in ACTIVE:
            s = supplier(k, d)
            if s: bysup[s].append(k)
        for s, ks in bysup.items():
            if blocked(s, d): continue
            r_ = rule(s)
            if P["model"] == "fixed" or (P.get("kedar_fixed") and r_["cadence"] == "custom"):
                review = fixed_is_day(s, d); gap = GAP[r_["cadence"]]; cap = CAP[r_["cadence"]]
                nxt = next(x for x in (d + dt.timedelta(n) for n in range(1, 62)) if fixed_is_day(s, x))
            else:
                iv = learnt_interval(s, d, P)
                review = (d - last_rev.get(s, d - dt.timedelta(999))).days >= iv
                g = d + dt.timedelta(iv)
                while blocked(s, g): g += ONE
                gap = (g - d).days; cap = 14 if iv <= 7 else (21 if iv <= 14 else 45)
                nd = max(d + ONE, last_rev.get(s, d - dt.timedelta(999)) + dt.timedelta(iv))
                while blocked(s, nd): nd += ONE
                nxt = nd
            cover = min(gap + 1 + P["safety"] + (P.get("single_extra", 3) if r_["single"] else 0), cap)
            todo = []; out_of = False
            for k in ks:
                on_order = sum(u for a, u in pipe[k])
                on_hand = stock[k] + on_order
                r, _x = rate_of(k, d)
                ls = max([x for x in SALES[k] if x < d and SALES[k][x] > 0] or [dt.date(2000, 1, 1)])
                if (d - ls).days > 60: continue                # dead item
                if review:
                    q = qty_for(k, d, cover, cap, r, on_hand)
                else:
                    if not P["interim"]: continue
                    horizon = (nxt - d).days + 1 + P["safety"]
                    trig = horizon if P.get("interim_safety", True) else (nxt - d).days + 1 + P.get("interim_margin", 0)
                    fp = P.get("floor_packs", 0)
                    if r <= 0: continue
                    bdl = 0.0
                    if P.get("bigday") and P.get("bigday_interim"):
                        end = d - dt.timedelta(P["lag"]); bdl = max([SALES[k].get(end - dt.timedelta(n), 0.0) for n in range(P["bigday"])] + [0.0])
                    if on_hand / r >= trig and not (fp and on_hand < fp * ITEMS[k]["ps"]) and not (bdl and on_hand < bdl): continue
                    q = qty_for(k, d, horizon, cap, r, on_hand, interim=True)
                if q <= 0: continue
                val = q * COST[k]
                if val < 5000 and on_hand > 0: continue        # the minimum line
                if stock[k] + on_order <= 0: out_of = True
                todo.append((k, q, val))
            if not todo: continue
            if sum(v for _, _, v in todo) < P.get("min_order_p", r_["min_order_p"]) and not out_of: continue
            for k, q, val in todo:
                arr = d + dt.timedelta(P.get('lead_real', 1))
                pipe[k].append((arr, q)); lines += inwin; bought_p += val * inwin
            if inwin: orders.add((s, d))
            if not review and inwin: M["interim_orders"] += 1
            if review: last_rev[s] = d
        # ---- the day's sales
        for k in ACTIVE:
            q = SALES[k].get(d, 0.0)
            if q <= 0: stock[k] -= q
            else:
                sold = min(q, stock[k]); stock[k] -= sold
                if not inwin: hist[k][d] = stock[k]; continue
                M["demand"] += q; M["unmet"] += q - sold
                if k in ORDERABLE:
                    M["demand_o"] += q * COST[k]; M["unmet_o"] += (q - sold) * COST[k]
                    if q - sold > 1e-9: M["unmet_days_o"] += 1; unmet_item[k] += (q - sold) * COST[k]
                if q - sold > 1e-9: unmet_days += 1
            hist[k][d] = stock[k]
            if not inwin: continue
            inv_p += stock[k] * COST[k]
            z = stock[k] <= 0 and any(SALES[k].get(d - dt.timedelta(n), 0) > 0 for n in range(1, 29))
            if z: zero_days += 1
            if k in CLEAN:
                inv_c += stock[k] * COST[k]
                if z: zero_c += 1
    n = nwin; weeks = n / 7.0
    return dict(name=name, fill=100.0 * (1 - M["unmet"] / M["demand"]), unmet_item_days=unmet_days, zero_item_days=zero_days,
                avg_stock_rs=inv_p / n / 100.0, orders_wk=len(orders) / weeks, lines_wk=lines / weeks, bought_rs=bought_p / 100.0, hist=hist,
                interim=M["interim_orders"] / weeks, zero_c=zero_c, stock_c=inv_c / n / 100.0, lost_rs=M["unmet_o"] / 100.0, lost_pct=100.0 * M["unmet_o"] / M["demand_o"], unmet_days_o=M["unmet_days_o"], top=unmet_item.most_common(12), end_stock=sum(stock[k] * COST[k] for k in ACTIVE) / 100.0)
def actual(w0=None, w1=None):
    w0 = w0 or E0; w1 = w1 or A; EV = [d for d in EVAL if w0 <= d <= w1]
    n = len(EV); inv = 0.0; zero = 0; zero_clean = 0; inv_c = 0.0
    for k in ACTIVE:
        for d in EV:
            st = max(0.0, STOCK[k][d]); inv += st * COST[k]
            if k in CLEAN: inv_c += st * COST[k]
            if STOCK[k][d] <= 0 and any(SALES[k].get(d - dt.timedelta(x), 0) > 0 for x in range(1, 29)):
                zero += 1
                if k in CLEAN: zero_clean += 1
    od = {(p["sup"], p["date"]) for k in ACTIVE for p in PUR.get(k, []) if w0 <= p["date"] <= w1 and p["bought"] > 0}
    ln = sum(1 for k in ACTIVE for p in PUR.get(k, []) if w0 <= p["date"] <= w1 and p["bought"] > 0)
    val = sum(p["net_p"] for k in ACTIVE for p in PUR.get(k, []) if w0 <= p["date"] <= w1 and p["bought"] > 0)
    return dict(name="ACTUAL (the shop, Darpan's sheets)", zero_item_days=zero, zero_clean=zero_clean, avg_stock_rs=inv / n / 100.0, orders_wk=len(od) / (n / 7.0), lines_wk=ln / (n / 7.0), bought_rs=val / 100.0, stock_c=inv_c / n / 100.0)
BASE = dict(model="levels", lag=2, safety=3, short=7, short_cap=2.0, short_min_sell=3, use_short=True, instock=True, min_instock=0.25, use_lot=True, new_days=28,
            review_min=2, review_max=30, review_default=7, interim=True, kedar_fixed=True)
def show(r):
    print("%-46s lost sale %5.2f%% Rs %7.0f on %3d item-days | CLEAN: zero-days %4d stock Rs %7.0f | ALL: stock Rs %7.0f end Rs %7.0f | orders/wk %5.1f (interim %4.1f) lines/wk %5.1f | bought Rs %8.0f" % (
        r["name"], r["lost_pct"], r["lost_rs"], r["unmet_days_o"], r["zero_c"], r["stock_c"], r["avg_stock_rs"], r["end_stock"], r["orders_wk"], r["interim"], r["lines_wk"], r["bought_rs"]))
if __name__ == "__main__":
    print("active %d | orderable (a supplier on record) %d | clean history and orderable %d | days %d %s .. %s" % (len(ACTIVE), len(ORDERABLE), len(CLEAN), len(EVAL), EVAL[0], EVAL[-1]))
    a = actual()
    print("%-46s (sales as they happened)                    | CLEAN: zero-days %4d stock Rs %7.0f | ALL: stock Rs %7.0f              | orders/wk %5.1f lines/wk %5.1f | bought Rs %8.0f" % (a["name"], a["zero_clean"], a["stock_c"], a["avg_stock_rs"], a["orders_wk"], a["lines_wk"], a["bought_rs"]))
    runs = [dict(name="FIXED (the engine as it is today)", model="fixed", lag=2, safety=3, interim=True), dict(BASE, name="LEVELS (the brief as written)")]
    for extra in sys.argv[1:]:
        e = json.loads(extra); runs.append(dict(BASE, **e) if e.get("model", "levels") == "levels" else e)
    for P in runs:
        r = run(P); show(r)
        if P.get("top"): print("      top lost:", [(k, round(v / 100)) for k, v in r["top"]])
