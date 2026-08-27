#!/usr/bin/python3
"""s22_rename.py -- the rename list: family-consistent, collision-checked."""
import json, collections
import rename16 as R, packmap as PM

N=json.load(open("names.json"))
names=N["names"]; close=N["close"]; open_=N["open"]; bought=N["bought"]; sold=N["sold"]; size=N["size"]
def live(k): return abs(close.get(k,0))+abs(open_.get(k,0))+bought.get(k,0)+abs(sold.get(k,0))

# A name that appears ONLY in the sale file is not a code in Marg -- it is what
# the sale report PRINTED after truncating. Renaming one would rename a shadow.
real={k for k in names if close.get(k) or open_.get(k) or bought.get(k)}
need=sorted(k for k in real if len(k)>R.LIMIT)
print("real item codes in Marg : %d      over %d characters : %d"%(len(real),R.LIMIT,len(need)))
print("sale-report shadows     : %d      (not codes -- nothing to rename)"%(len(names)-len(real)))

# group by family so every size in a family gets the same core
fam=collections.defaultdict(list)
for k in need: fam[R.family_key(names[k])].append(k)
print("families to rename      : %d"%len(fam))

def run(keepset):
    prop, why = {}, {}
    for f, ks in fam.items():
        members=[names[k] for k in ks]
        out,note=R.propose_family(members, keep_vendor=(f in keepset))
        for k in ks:
            prop[k]=out[names[k]]; why[k]=note+(" (brand kept: a sibling family needed it)" if f in keepset else "")
    return prop, why

fixed={k:names[k] for k in real if k not in need}
keep=set()
for _ in range(4):
    prop,why=run(keep)
    allmap={**fixed,**prop}
    g=collections.defaultdict(list)
    for k,v in allmap.items(): g[v.upper()[:R.LIMIT].strip()].append(k)
    coll={c:v for c,v in g.items() if len(v)>1}
    if not coll: break
    grew=False
    for v in coll.values():
        for k in v:
            if k in prop and R.family_key(names[k]) not in keep:
                keep.add(R.family_key(names[k])); grew=True
    if not grew: break

pairs=[(names[k],prop[k],why[k]) for k in need]
ok,problems=R.verify(pairs,{names[k].upper() for k in real})
print("\nAFTER RENAMING")
print("  still over %d chars      : %d"%(R.LIMIT,sum(1 for v in prop.values() if len(v)>R.LIMIT)))
print("  16-char collisions      : %d"%len(coll))
print("  verification problems   : %d"%len(problems))
for o,n,p in problems[:10]: print("     %-30s -> %-17s %s"%(o[:30],n,p))
if coll:
    print("  UNRESOLVED — owner must choose:")
    for c,v in coll.items():
        print("    '%s' : %s"%(c,", ".join(names[k] for k in v)))
json.dump({"rename":{names[k]:prop[k] for k in need},"why":{names[k]:why[k] for k in need},
           "live":{names[k]:round(live(k)) for k in need}},open("rename16.json","w"))

print("\nFAMILIES, IN FULL")
for f,ks in sorted(fam.items(), key=lambda kv:-sum(live(k) for k in kv[1])):
    if len(ks)<2: continue
    print("  %s"%f)
    for k in sorted(ks,key=lambda k:names[k]):
        print("      %-32s -> %-17s"%(names[k][:32],prop[k]))
