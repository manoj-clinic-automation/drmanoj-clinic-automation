#!/usr/bin/python3
"""s14_monthly.py -- the item-wise sale/purchase ledger, month by month."""
import json, collections
import ingest as I, packmap as PM
res=json.load(open("resolve.json")); mapping=res["mapping"]
sale=json.load(open("sale.json")); pur,_,_=I.read_purchase()
stock=json.load(open("stock_final.json"))
MO=["2026-04","2026-05","2026-06","2026-07","2026-08"]
led=collections.defaultdict(lambda: {m:{"sold":0.0,"cn":0.0,"pur":0.0,"pret":0.0,"bills":set(),"vend":set()} for m in MO})
for l in sale:
    k=PM.norm(l.get("item")); k=mapping.get(k,k); m=l["date"][:7]
    if m not in led[k]: continue
    u,_=I.sale_units(l,PM.pack_size(l.get("pack")))
    if u is None: continue
    led[k][m]["cn" if I.is_credit_note(l["bill"]) else "sold"]+=u
    led[k][m]["bills"].add(l["bill"])
for r in pur:
    k=PM.norm(r.get("item")); k=mapping.get(k,k); m=r["_period"][0][:7]
    if m not in led[k]: continue
    led[k][m]["pret" if r.get("is_return") else "pur"]+=(r.get("loose_qty") or 0)
    if r.get("supplier"): led[k][m]["vend"].add(r["supplier"][:26])
for s in stock:
    d=led.get(s["key"])
    s["months"]={m:{"sold":round(v["sold"]),"cn":round(v["cn"]),"pur":round(v["pur"]),
                    "pret":round(v["pret"]),"bills":len(v["bills"]),
                    "vend":sorted(v["vend"])} for m,v in (d or {}).items()} if d else {}
json.dump(stock,open("stock_final.json","w"))

print("ITEM-WISE MONTHLY LEDGER  (top 12 movers)")
top=sorted([s for s in stock if s["net_sold"]>0],key=lambda s:-s["net_sold"])[:12]
hdr="  %-24s %-8s"%("item","")+"".join("%13s"%m[5:] for m in MO)+"%12s"%"on shelf"
print(hdr)
for s in top:
    for lab,key in (("sold","sold"),("bought","pur")):
        print("  %-24s %-8s"%(s["item"][:24] if lab=="sold" else "",lab)+
              "".join("%13s"%PM.describe(s["months"][m][key],s["size"],short=True) for m in MO)+
              ("%12s"%s["shelf"] if lab=="sold" else ""))
print("\nVENDOR PER ITEM (who supplies what) -- top movers")
for s in top:
    vs=sorted({v for m in MO for v in s["months"][m]["vend"]})
    print("  %-28s %s"%(s["item"][:28],", ".join(vs) or "no purchase this year"))
