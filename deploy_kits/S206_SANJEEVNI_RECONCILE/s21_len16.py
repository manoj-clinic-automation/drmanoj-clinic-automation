"""
s21_len16.py -- what actually breaks at the 16-character bill print.

Read RAW, not through the ledger: the ledger pools some of these names into
size-families, so asking it for a per-size figure returns zero and every one of
them looks dead. They are not.
"""
import json, collections
import ingest as I, packmap as PM
op=I.find_stock("31-03-2026","WHOLE STORES")[0]; cl=I.find_stock("26-08-2026","WHOLE STORES")[0]
pur,_,_=I.read_purchase(); sale=json.load(open("sale.json"))

names, close, open_, bought, sold, size = {}, collections.Counter(), collections.Counter(), \
    collections.Counter(), collections.Counter(), {}
def reg(nm, pk=None):
    k=PM.norm(nm)
    if k: names.setdefault(k, " ".join(str(nm).split())); size.setdefault(k, PM.pack_size(pk))
    return k
for r in cl["rows"]:
    k=reg(r["item"], r.get("packing")); close[k]+=(r["units"] or 0)
for r in op["rows"]:
    k=reg(r["item"], r.get("packing")); open_[k]+=(r["units"] or 0)
for r in pur:
    if r.get("item"):
        k=reg(r["item"], r.get("packing")); bought[k]+=(r.get("loose_qty") or 0)
for l in sale:
    if not l.get("item"): continue
    k=reg(l["item"], l.get("pack"))
    u,_=I.sale_units(l, PM.pack_size(l.get("pack")))
    if u: sold[k]+= (-u if I.is_credit_note(l["bill"]) else u)

CUT=16
def live(k): return abs(close[k])+abs(open_[k])+bought[k]+abs(sold[k])
print("distinct item names across all sources : %d"%len(names))
for L in (16,20):
    over=[k for k in names if len(k)>L]
    g=collections.defaultdict(list)
    for k in names: g[k[:L].strip()].append(k)
    coll={c:v for c,v in g.items() if len(v)>1}
    hot={c:v for c,v in coll.items() if sum(1 for k in v if live(k))>1}
    print("  at %2d chars : %3d names too long · %2d collision groups (%d names) · "
          "%d groups where MORE THAN ONE side is actually in use"%(
          L,len(over),len(coll),sum(len(v) for v in coll.values()),len(hot)))

g=collections.defaultdict(list)
for k in names: g[k[:CUT].strip()].append(k)
hot=[(c,v) for c,v in g.items() if sum(1 for k in v if live(k))>1]
hot.sort(key=lambda cv:-sum(live(k) for k in cv[1]))
print("\nGROUPS WHERE TWO OR MORE LIVE ITEMS PRINT THE SAME 16 CHARACTERS")
print("(the only ones a bill or a report cannot tell apart in practice)\n")
for c,v in hot:
    print("  '%s'"%c)
    for k in sorted(v, key=lambda k:-live(k)):
        if not live(k): continue
        print("      %-32s shelf %-7s 31-Mar %-7s bought %-7s sold %s"%(
            names[k][:32], PM.describe(close[k],size.get(k)) if close[k] else "-",
            PM.describe(open_[k],size.get(k)) if open_[k] else "-",
            PM.describe(bought[k],size.get(k)) if bought[k] else "-",
            PM.describe(sold[k],size.get(k)) if sold[k] else "-"))
    dead=[k for k in v if not live(k)]
    if dead: print("      (+%d empty codes in the same group)"%len(dead))
    print()
json.dump({"names":names,"close":dict(close),"open":dict(open_),"bought":dict(bought),
           "sold":dict(sold),"size":size}, open("names.json","w"))
