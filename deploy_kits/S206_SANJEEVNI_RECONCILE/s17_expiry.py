"""Does the manual expiry-removal explain GOODS_OUT? Test it, don't assume it."""
import json, collections, datetime
import ingest as I, packmap as PM, classify
stock=json.load(open("stock_final.json")); sale=json.load(open("sale.json"))
pur,_,_=I.read_purchase()
out,_,_=classify.classify(stock)
cls={r["key"]:r["class"] for r in out}
res=json.load(open("resolve.json")); mp=res["mapping"]

# every batch expiry we can see, per item, from BOTH sides
exp=collections.defaultdict(set)
for l in sale:
    k=PM.norm(l.get("item")); k=mp.get(k,k)
    if l.get("expiry"): exp[k].add(l["expiry"])
for r in pur:
    k=PM.norm(r.get("item")); k=mp.get(k,k)
    e=r.get("expiry")
    if e:
        e=str(e).strip()
        if "/" in e:
            mm,yy=e.split("/")[0],e.split("/")[-1]
            try: exp[k].add("20%s-%02d"%(yy[-2:],int(mm)))
            except ValueError: pass

WIN0,WIN1="2026-04","2026-08"
def expiring(k):
    return sorted(e for e in exp.get(k,()) if e<=WIN1)

print("DID A BATCH EXPIRE INSIDE THE WINDOW?  (a batch dated <= 2026-08 was unsellable)")
print("  %-28s %8s  %s"%("item","gap","batches at or before Aug-2026"))
hit=miss=0
for r in sorted([x for x in out if x["class"]=="GOODS_OUT"],key=lambda r:r["var"]):
    e=expiring(r["key"]); 
    if e: hit+=1
    else: miss+=1
    print("  %-28s %+8.0f  %s"%(r["item"][:28],r["var"], ", ".join(e) if e else "none visible"))
print("\n  %d of %d GOODS_OUT items held a batch that expired in or before the window"%(hit,hit+miss))

print("\nAND THE CONTROL -- do BALANCED items hold expiring batches just as often?")
bal=[s for s in stock if cls.get(s["key"]) is None and s["sold"]>0]
b=sum(1 for s in bal if expiring(s["key"]))
print("  %d of %d balanced trading items also held one (%.0f%%)  vs GOODS_OUT %.0f%%"%(
    b,len(bal),100.0*b/max(len(bal),1),100.0*hit/max(hit+miss,1)))
