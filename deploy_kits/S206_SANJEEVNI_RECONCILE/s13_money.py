import json, collections
import ingest as I, packmap as PM
pur,_,_=I.read_purchase()
res=json.load(open("resolve.json")); mapping=res["mapping"]
stock=json.load(open("stock_final.json"))
# cost per BASE UNIT, from the latest purchase of each item
cost={}
for r in pur:
    if r.get("is_return"): continue
    k=PM.norm(r.get("item")); k=mapping.get(k,k)
    lq=r.get("loose_qty") or 0; net=r.get("net_amount")
    if lq>0 and net: cost[k]=(net/lq, r.get("_period")[0][:7], r.get("supplier"))
tot=0; nocost=[]
for s in stock:
    c=cost.get(s["key"])
    s["cost_per_unit"]=round(c[0],4) if c else None
    s["cost_src"]=c[1] if c else None
    s["vendor"]=(c[2] or "")[:28] if c else None
    s["value"]=round((c[0]*s["closing"]),2) if c and s["closing"]>0 else 0
    tot+=s["value"]
    if s["closing"]>0 and not c: nocost.append(s)
json.dump(stock,open("stock_final.json","w"))
print("STOCK VALUE AT LAST PURCHASE COST : Rs %s"%format(round(tot),","))
print("  lines priced           : %d"%len([s for s in stock if s["value"]>0]))
print("  lines with stock but NO purchase this year (unpriced) : %d"%len(nocost))
print("     these are last year's stock; their cost is not in the window")
for s in sorted(nocost,key=lambda s:-s["closing"])[:12]:
    print("     %-30s %s"%(s["item"][:30],s["shelf"]))
print("\nBIGGEST MONEY STANDING STILL (stock with no sale in 2 months)")
dead=[s for s in stock if s["value"]>0 and (not s["last_sale"] or s["last_sale"]<"2026-06-26")]
print("  %d items, Rs %s"%(len(dead),format(round(sum(s['value'] for s in dead)),",")))
for s in sorted(dead,key=lambda s:-s["value"])[:18]:
    print("   %-30s %-20s Rs %9s  last sale %s"%(s["item"][:30],s["shelf"],
        format(round(s["value"]),","),s["last_sale"] or "never"))
