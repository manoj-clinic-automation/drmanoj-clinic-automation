# S295 replay -- the result table. FIXED = the engine as it stands (S410/S470 rules, re-implemented here); REFINED = the model S486 Part B builds.
import sim, datetime as dt
R = dict(sim.BASE, lag=1, instock=False, interim_safety=False, interim_margin=1, bigday=28, name="REFINED")
F = dict(model="fixed", lag=2, safety=3, interim=True, name="FIXED")
def line(tag, r): print("  %-40s lost sale %5.2f%% (Rs %6.0f) | empty-shelf item-days %4d | avg stock Rs %7.0f | supplier orders/wk %5.1f (of them between reviews %4.1f) | lines/wk %5.1f" % (tag, r["lost_pct"], r["lost_rs"], r["zero_c"], r["stock_c"], r["orders_wk"], r["interim"], r["lines_wk"]))
print("universe: %d medicines sold in the period; %d have a supplier on record; %d of those have books that add up (the like-for-like set)" % (len(sim.ACTIVE), len(sim.ORDERABLE), len(sim.CLEAN)))
for nm, w0, w1 in (("WHOLE 04-May .. 03-Oct (153 days)", None, None), ("FIRST HALF 04-May .. 19-Jul", "2026-05-04", "2026-07-19"), ("SECOND HALF 20-Jul .. 03-Oct", "2026-07-20", "2026-10-03")):
    a = sim.actual(dt.date.fromisoformat(w0) if w0 else None, dt.date.fromisoformat(w1) if w1 else None)
    print(nm); print("  %-40s (sales as they happened)      | empty-shelf item-days %4d | avg stock Rs %7.0f | supplier orders/wk %5.1f                                | lines/wk %5.1f" % ("THE SHOP AS IT WAS (Darpan's sheets)", a["zero_clean"], a["stock_c"], a["orders_wk"], a["lines_wk"]))
    ex = {"from": w0, "to": w1} if w0 else {}
    line("FIXED  (the engine as it stands)", sim.run(dict(F, **ex))); line("REFINED (S486 Part B)", sim.run(dict(R, **ex)))
print("WHAT EACH PART IS WORTH (whole period; REFINED with one part taken out)")
for tag, ch in (("without the shop's own lots (tens)", dict(use_lot=False)), ("list made before the sale report lands", dict(lag=2)), ("without the short (7-day) rate", dict(use_short=False)),
                ("without orders between reviews", dict(interim=False)), ("between-review orders with full safety", dict(interim_safety=True)), ("without the largest-day floor", dict(bigday=0)),
                ("with in-stock-day correction", dict(instock=True)), ("Kedar on a learnt rhythm too", dict(kedar_fixed=False)), ("minimum order Rs 2,000", dict(min_order_p=200000)), ("safety 2 days", dict(safety=2)), ("safety 4 days", dict(safety=4))):
    line(tag, sim.run(dict(R, **ch)))
print("IF GOODS TAKE TWO DAYS TO ARRIVE, NOT ONE (whole period)")
line("FIXED", sim.run(dict(F, lead_real=2))); line("REFINED", sim.run(dict(R, lead_real=2))); line("REFINED, safety 4", sim.run(dict(R, lead_real=2, safety=4)))
