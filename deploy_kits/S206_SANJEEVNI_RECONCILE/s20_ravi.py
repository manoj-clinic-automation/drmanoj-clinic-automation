"""Which of the unexplained surpluses are Ravi Medical items?"""
import json, collections, classify
import ingest as I, packmap as PM
stock=json.load(open("stock_final.json")); pur,_,_=I.read_purchase()
out,_,_=classify.classify(stock)
sup=collections.defaultdict(collections.Counter)
for r in pur:
    if r.get("item") and r.get("supplier"): sup[PM.norm(r["item"])][r["supplier"][:26]]+=1
byk={s["key"]:s for s in stock}
print("EVERY UNEXPLAINED SURPLUS, AND WHO EVER SUPPLIED THAT ITEM")
print("  %-28s %8s  %-16s %s"%("item","surplus","value at cost","supplier on record"))
tot=0
for r in sorted([x for x in out if x["class"]=="GOODS_IN"],key=lambda r:-r["var"]):
    s=byk[r["key"]]; cpu=s.get("cost_per_unit")
    v=round((cpu or 0)*r["var"]); tot+=v
    who=", ".join(k for k,_ in sup.get(r["key"],collections.Counter()).most_common(2)) or "NEVER PURCHASED IN THE WINDOW"
    print("  %-28s %8s  %-16s %s"%(r["item"][:28],PM.describe(r["var"],r["size"]),
        ("Rs %s"%format(v,",")) if v else "not priced", who))
print("\n  total surplus at cost, where a cost exists : Rs %s"%format(tot,","))
print("\nRAVI MEDICAL -- what IS on record, by month")
rv=collections.defaultdict(lambda: collections.defaultdict(float))
bills=collections.defaultdict(set)
for r in pur:
    if "RAVI" in (r.get("supplier") or "").upper():
        rv[r["_period"][0][:7]][PM.norm(r["item"])]+=(r.get("loose_qty") or 0)
        if r.get("bill"): bills[r["_period"][0][:7]].add(r["bill"])
for m in sorted(rv):
    print("   %s : %2d items, %d bill(s) %s"%(m,len(rv[m]),len(bills[m]),sorted(bills[m])))
print("\n   MONTHS WITH NO RAVI BILL AT ALL:", [m for m in ("2026-04","2026-05","2026-06","2026-07","2026-08") if m not in rv])
