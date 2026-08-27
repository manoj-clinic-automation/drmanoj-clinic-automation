#!/usr/bin/python3
"""s23_renamelist.py -- the rename list as a worksheet, with merges called out first."""
import json, collections, csv
import rename16 as R, packmap as PM
N=json.load(open("names.json")); RN=json.load(open("rename16.json"))
names=N["names"]; close=N["close"]; open_=N["open"]; bought=N["bought"]; sold=N["sold"]; size=N["size"]
dup=json.load(open("dupes.json"))
def live(k): return abs(close.get(k,0))+abs(open_.get(k,0))+bought.get(k,0)+abs(sold.get(k,0))

# Items that should be MERGED before they are renamed -- renaming half of a
# split pair just makes a tidier split.
merge_into={}
for r in dup:
    if not r["evidence"].startswith(("SPLIT","PARTIAL")): continue
    a,b=r["a"],r["b"]
    # TWO SIZES ARE NOT A DUPLICATE. 'ANKLE BINDER BAMBOO L' and '... M' differ
    # by one character and both trade, so the name test pairs them -- but their
    # identifiers differ, and that settles it. Merging them would destroy a real
    # size distinction to fix a problem that does not exist.
    ia=R.split_name(R.toks(a))[1]; ib=R.split_name(R.toks(b))[1]
    sz=lambda i: bool(i) and all(R.SIZE.match(t) for t in i)
    if sz(ia) and sz(ib) and ia != ib: continue      # two SIZES, not a duplicate
    if ia and ib and ia != ib: continue              # two strengths, likewise
    if r["a_pur"]>r["b_pur"]: merge_into[PM.norm(b)]=a
    elif r["b_pur"]>r["a_pur"]: merge_into[PM.norm(a)]=b

rows=[]
for old,new in RN["rename"].items():
    k=PM.norm(old); L=live(k)
    grp="IN USE" if L else "DORMANT"
    if k in merge_into: grp="MERGE FIRST"
    rows.append({"group":grp,"old":old,"new":new,"len":len(new),"why":RN["why"][old],
        "merge_into":merge_into.get(k,""),
        "shelf":PM.describe(close.get(k,0),size.get(k)) if close.get(k) else "",
        "sold":PM.describe(sold.get(k,0),size.get(k)) if sold.get(k) else "",
        "bought":PM.describe(bought.get(k,0),size.get(k)) if bought.get(k) else "",
        "live":round(L)})
order={"MERGE FIRST":0,"IN USE":1,"DORMANT":2}
rows.sort(key=lambda r:(order[r["group"]],-r["live"],r["old"]))
D="/sessions/rcw-01y9d9zd4e5vdfg7p1wmkijm/mnt/Downloads/margsync/_analysis/"
with open(D+"_rename.csv","w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["Do this","Current name in Marg","Chars","New name","Chars","On shelf","Bought Apr-Aug",
                "Sold Apr-Aug","Merge into","How it was shortened"])
    for r in rows:
        w.writerow([r["group"],r["old"],len(r["old"]),r["new"],r["len"],r["shelf"],r["bought"],
                    r["sold"],r["merge_into"],r["why"]])
c=collections.Counter(r["group"] for r in rows)
print("RENAME LIST : %d real item codes over 16 characters"%len(rows))
for k in ("MERGE FIRST","IN USE","DORMANT"): print("   %-12s %d"%(k,c.get(k,0)))
flagged=[r for r in rows if "DROPPED" in r["why"]]
print("\n   %d proposals gave up a whole word and are flagged for your eye:"%len(flagged))
for r in flagged: print("      %-30s -> %-17s %s"%(r["old"][:30],r["new"],r["why"][:46]))
print("\n\nMERGE FIRST — renaming half a split pair only makes a tidier split")
for r in [x for x in rows if x["group"]=="MERGE FIRST"]:
    print("   %-30s  merge into '%s'"%(r["old"][:30],r["merge_into"]))
