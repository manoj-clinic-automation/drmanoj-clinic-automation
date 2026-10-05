# S295 replay -- loader. Reads the nightly finance.db copy READ-ONLY; builds per-item daily sales, effective purchase lines,
# the reconstructed day-end stock series (Marg closing of 04-10 rolled back by purchases and sales). No person's data is read.
import sqlite3, os, re, math, datetime as dt, collections, pickle, statistics
DB = os.path.expanduser("~/fn.db")
def norm(s):
    s = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", s)
def K(s): return norm(str(s or "")[:20])
def units(q, size):
    s = str(q or "").strip()
    if not s or s == "-": return 0.0
    if ":" in s:
        a, b = (s.split(":", 1) + ["0"])[:2]
        try: return float(a or 0) * size + float(b or 0)
        except ValueError: return 0.0
    try: return float(s)
    except ValueError: return 0.0
def supkey(s):
    s = norm(s)
    return re.sub(r"\s+BAREIL\w*$", "", s)
D = lambda s: dt.date.fromisoformat(s)
def load():
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    # item master: the newest Marg closing (as_on 04-10-2026 = after the sales of 03-10)
    snap = {}
    for item, qty, packing, ps in c.execute("SELECT item, qty, packing, pack_size FROM stock_snapshot WHERE as_on='04-10-2026'"):
        snap.setdefault(K(item), []).append(dict(item=item, qty=float(qty or 0), packing=packing, ps=int(ps or 1) or 1))
    sect = {K(i): s for i, s in c.execute("SELECT item, section FROM stock_item_section")}
    items = {}
    fam = 0
    for k, v in snap.items():
        if len(v) > 1: fam += 1; continue                      # a family (two Marg items under one 20-letter key) is left out
        if sect.get(k) == "Orthotics": continue
        items[k] = dict(v[0], section=sect.get(k, "?"))
    # sales
    sales = collections.defaultdict(lambda: collections.defaultdict(float))
    for name, d, q, ret in c.execute("SELECT item_name, business_date, qty_raw, is_return FROM sale_line_item WHERE unit='medical'"):
        k = K(name)
        if k in items:
            sales[k][D(d)] += units(q, items[k]["ps"]) * (-1 if ret else 1)
    # effective purchase lines: one set per (supplier, bill): the live export with the latest stamp
    sets = {}
    for sn, bn, md5, stamp in c.execute("SELECT l.supplier_norm, l.bill_no, l.source_md5, e.export_stamp FROM purchase_line l JOIN purchase_export e ON e.md5=l.source_md5 "
                                        "WHERE e.superseded_by IS NULL GROUP BY 1,2,3,4"):
        k = (sn, bn)
        if k not in sets or (stamp, md5) > sets[k]: sets[k] = (stamp, md5)
    pur = collections.defaultdict(list)
    for sn, bn, bd, item, qty, free, net, amt, direction, md5 in c.execute(
            "SELECT supplier_norm, bill_no, bill_date, item, qty, free, net_amount_p, amount_p, direction, source_md5 FROM purchase_line"):
        if sets.get((sn, bn), (None, None))[1] != md5: continue
        k = K(item)
        if k not in items or not bd: continue
        ps = items[k]["ps"]
        sign = -1 if (direction or "").upper().startswith("RET") else 1
        q = float(qty or 0); f = float(free or 0)
        pur[k].append(dict(date=D(bd), sup=supkey(sn), qty=q, units=sign * (q + f) * ps, bought=sign * q * ps, free=f, net_p=float(net or amt or 0)))
    for k in pur: pur[k].sort(key=lambda r: r["date"])
    # the supplier rule rows (blocked days, single-source extra, Kedar)
    rules = {supkey(r[0]): dict(cadence=r[1], days=r[2], blocked=r[3] or "", single=int(r[4] or 0), min_order_p=int(r[5] or 50000))
             for r in c.execute("SELECT supplier_norm, cadence, order_days, blocked_days, single_source_extra, min_order_p FROM order_supplier_rule")}
    irules = {K(r[0]): r[1] for r in c.execute("SELECT item, rule FROM order_item_rule")}
    A = dt.date(2026, 10, 3)                                    # the anchor: day-end stock of 03-10 = Marg's closing as on 04-10
    S0 = dt.date(2026, 4, 1)
    days = [S0 + dt.timedelta(n) for n in range((A - S0).days + 1)]
    stock = {}
    bad = []
    for k, it in items.items():
        s = it["qty"]; ser = {A: s}
        pbd = collections.defaultdict(float)
        for p in pur.get(k, []): pbd[p["date"]] += p["units"]
        for d in reversed(days[1:]):                            # day-end of d-1 = day-end of d - purchases(d) + sales(d)
            s = s - pbd.get(d, 0.0) + sales[k].get(d, 0.0)
            ser[d - dt.timedelta(1)] = s
        stock[k] = ser
        mn = min(ser.values())
        if mn < -0.5 * it["ps"]: bad.append((k, mn / it["ps"]))
    return dict(items=items, sales={k: dict(v) for k, v in sales.items()}, pur=dict(pur), rules=rules, irules=irules, stock=stock, days=days, bad=bad, fam=fam, A=A)
if __name__ == "__main__":
    X = load()
    pickle.dump(X, open(os.path.expanduser("~/replay/data.pkl"), "wb"))
    it = X["items"]
    print("items in the replay universe:", len(it), "| families left out:", X["fam"], "| by section:", collections.Counter(v["section"] for v in it.values()))
    print("items with any sale:", sum(1 for k in it if X["sales"].get(k)), "| with any purchase:", sum(1 for k in it if X["pur"].get(k)))
    print("sale days:", len({d for v in X["sales"].values() for d in v}), "| purchase lines (effective, in universe):", sum(len(v) for v in X["pur"].values()))
    print("reconstructed stock below zero by more than half a pack at some day:", len(X["bad"]))
    for k, m in sorted(X["bad"], key=lambda x: x[1])[:25]: print("   %-22s min %8.1f packs" % (k, m))
