"""s18 -- exactly which products differ between the 31-Mar and 26-Aug lists."""
import json, collections
import ingest as I, packmap as PM
op=I.find_stock("31-03-2026","WHOLE STORES")[0]; cl=I.find_stock("26-08-2026","WHOLE STORES")[0]
stock=json.load(open("stock_final.json"))
moved={s["key"]:s for s in stock}
def rollup(rep):
    d=collections.defaultdict(float); nm={}; pk={}
    for r in rep["rows"]:
        k=PM.norm(r["item"])
        if not k: continue
        d[k]+=(r["units"] or 0); nm.setdefault(k,r["item"]); pk.setdefault(k,r.get("packing"))
    return d,nm,pk
O,ON,OP=rollup(op); C,CN,CP=rollup(cl)
allk=set(O)|set(C)
gone=[k for k in allk if k in O and k not in C]
new =[k for k in allk if k in C and k not in O]
both=[k for k in allk if k in O and k in C]
print("31-MAR LIST : %d lines, %d with a quantity"%(len(O),sum(1 for v in O.values() if v)))
print("26-AUG LIST : %d lines, %d with a quantity"%(len(C),sum(1 for v in C.values() if v)))
print("\nON THE MARCH LIST, NOT ON TODAY'S : %d"%len(gone))
gs=[k for k in gone if O[k]]
print("   of those, %d STILL HELD STOCK on 31-Mar  (%d units)"%(len(gs),round(sum(O[k] for k in gs))))
print("   the other %d were already at zero"%(len(gone)-len(gs)))
print("\n   held stock and vanished from the list -- did they sell?")
print("   %-32s %8s %8s  %s"%("item","31-Mar","sold","verdict"))
for k in sorted(gs,key=lambda k:-O[k]):
    m=moved.get(k); sold=round(m["sold"]-m["sreturn"]) if m else 0
    pk=PM.pack_size(OP.get(k))
    v = "sold out, list tidied" if sold>=O[k]-0.5 else ("part sold, %s unaccounted"%PM.describe(O[k]-sold,pk) if sold else "NEVER SOLD -- %s unaccounted"%PM.describe(O[k],pk))
    print("   %-32s %8s %8s  %s"%(ON[k][:32],PM.describe(O[k],pk),PM.describe(sold,pk) if sold else "-",v))
print("\nON TODAY'S LIST, NOT ON MARCH'S : %d   (%d hold stock now)"%(len(new),sum(1 for k in new if C[k])))
for k in sorted([k for k in new if C[k]],key=lambda k:-C[k])[:20]:
    m=moved.get(k); pk=PM.pack_size(CP.get(k))
    print("   %-32s now %-16s bought %s"%(CN[k][:32],PM.describe(C[k],pk),
        PM.describe(round(m["purchased"]),pk) if m else "nothing on record"))
json.dump({"gone":[[ON[k],O[k]] for k in gone],"new":[[CN[k],C[k]] for k in new]},open("twolists.json","w"))
