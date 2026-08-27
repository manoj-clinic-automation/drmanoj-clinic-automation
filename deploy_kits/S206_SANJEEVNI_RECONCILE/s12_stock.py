#!/usr/bin/python3
"""s12_stock.py -- current stock in the owner's taxonomy, and the consumption behind it."""
import json, collections, datetime, math
import ingest as I, packmap as PM, classify

rows=json.load(open("ledger_final.json"))
sale=json.load(open("sale.json"))
res=json.load(open("resolve.json"))
act=[r for r in rows if any(abs(r[t])>0 for t in ("opening","purchased","preturn","sold","sreturn","closing"))]
out,conf,cand=classify.classify(act)
cls={r["key"]:r["class"] for r in out}

# --- daily consumption per item, from the sale side only ---
D0=datetime.date(2026,4,1); D1=datetime.date(2026,8,26); DAYS=(D1-D0).days+1
mapping=res["mapping"]
per=collections.defaultdict(lambda: collections.defaultdict(float))
lastsale={}; firstsale={}
for l in sale:
    k=PM.norm(l.get("item")); k=mapping.get(k,k)
    sz=PM.pack_size(l.get("pack"))
    u,_=I.sale_units(l,sz)
    if u is None: continue
    if I.is_credit_note(l["bill"]): u=-u
    per[k][l["date"][:7]]+=u
    if not I.is_credit_note(l["bill"]) and u>0:
        lastsale[k]=max(lastsale.get(k,""),l["date"])
        firstsale[k]=min(firstsale.get(k,"9999"),l["date"])

cl_keys={PM.norm(r["item"]) for r in I.find_stock("26-08-2026","WHOLE STORES")[0]["rows"]}
stock=[]
for r in act:
    k=r["key"]; net=sum(per[k].values())
    # THE RATE RUNS FROM THE ITEM'S FIRST SALE, NOT FROM 1-APRIL.
    # An item first stocked in July has not been failing to sell since April;
    # it did not exist. Dividing by the whole 148-day window understates every
    # new item's rate and puts it in a reorder band it does not belong in.
    fs=firstsale.get(k)
    if fs:
        d0=datetime.date(*map(int,fs.split("-")))
        span=max((D1-d0).days+1,1)
    else:
        span=DAYS
    rate=net/span if span else 0
    cover=(r["closing"]/rate) if rate>0.0001 and r["closing"]>0 else (0 if r["closing"]<=0 else None)
    stock.append({**r,"class":cls.get(k,"BALANCED"),"per_month":dict(per[k]),
                  "on_list":k in cl_keys,
                  "net_sold":net,"per_day":rate,"cover_days":cover,
                  "first_sale":fs,"rate_span_days":span,
                  "last_sale":lastsale.get(k),
                  "shelf":PM.describe(r["closing"],r["size"]),
                  "months_active":len([m for m,v in per[k].items() if v>0])})
json.dump(stock,open("stock_final.json","w"))

onshelf=[s for s in stock if s["closing"]>0]
print("STOCK ON THE SHELF, 26-Aug-2026")
print("  lines with stock            : %d"%len(onshelf))
print("  lines at zero               : %d"%len([s for s in stock if s['closing']==0]))
print("  lines NEGATIVE              : %d"%len([s for s in stock if s['closing']<0]))
strip=[s for s in onshelf if s["size"]]; whole=[s for s in onshelf if not s["size"]]
print("  strip items %d  holding %d strips + loose"%(len(strip),sum(int(s['closing']//s['size']) for s in strip)))
print("  whole-unit items %d  holding %d units"%(len(whole),sum(int(s['closing']) for s in whole)))

def band(s):
    c=s["cover_days"]
    if s["closing"]<=0: return "NEGATIVE / NIL"
    if c is None: return "no sale since 1-Apr"
    if c<7: return "under 1 week"
    if c<14: return "1-2 weeks"
    if c<30: return "2-4 weeks"
    if c<90: return "1-3 months"
    return "over 3 months"
b=collections.Counter(band(s) for s in stock)
print("\nDAYS OF COVER AT THE MEASURED RATE")
for k in ("NEGATIVE / NIL","under 1 week","1-2 weeks","2-4 weeks","1-3 months","over 3 months","no sale since 1-Apr"):
    if b.get(k): print("   %-22s %3d items"%(k,b[k]))

print("\nRUNNING OUT INSIDE 14 DAYS  (%d)"%len([s for s in onshelf if s['cover_days'] is not None and s['cover_days']<14]))
print("  %-30s %-22s %10s %8s"%("item","on shelf","per day","days"))
for s in sorted([x for x in onshelf if x["cover_days"] is not None and x["cover_days"]<14],key=lambda s:s["cover_days"]):
    print("  %-30s %-22s %10.1f %8.1f"%(s["item"][:30],s["shelf"],s["per_day"],s["cover_days"]))

dead=[s for s in onshelf if not s["last_sale"] or s["last_sale"]<"2026-06-26"]
print("\nNO SALE IN THE LAST TWO MONTHS BUT STOCK ON THE SHELF : %d"%len(dead))
for s in sorted(dead,key=lambda s:-s["closing"])[:25]:
    print("  %-30s %-22s last sale %s"%(s["item"][:30],s["shelf"],s["last_sale"] or "never since 1-Apr"))
