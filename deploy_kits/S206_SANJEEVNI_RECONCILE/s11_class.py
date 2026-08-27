import json, collections, classify, packmap as PM
rows=json.load(open("stock_final.json"))
act=[r for r in rows if any(abs(r[t])>0 for t in ("opening","purchased","preturn","sold","sreturn","closing"))]
out,conf,cand=classify.classify(act)
json.dump({"classified":out,"confirmed_pairs":conf,"candidates":cand},open("classified.json","w"))
c=collections.Counter(r["class"] for r in out)
print("ITEMS THAT MOVED %d   BALANCED %d   OFF %d\n"%(len(act),len(act)-len(out),len(out)))
for k,n in c.most_common():
    tot=sum(abs(r["var"]) for r in out if r["class"]==k)
    print("  %-12s %3d items   %6.0f units"%(k,n,tot))
for k,_ in c.most_common():
    print("\n===== %s ====="%k)
    for r in sorted([x for x in out if x["class"]==k],key=lambda r:-abs(r["var"])):
        print("  %-30s %+7.0f  (%s)   %s"%(r["item"][:30],r["var"],PM.describe(r["var"],r["size"]),r["why"][:64]))
