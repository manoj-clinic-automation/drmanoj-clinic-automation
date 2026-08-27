#!/usr/bin/python3
"""
s19_dupes.py -- every pair of item codes that may be one product.

Scope is the WHOLE vocabulary, not only the codes carrying a variance. A
duplicate that happens to balance is still a duplicate: it splits the sale
history, splits the reorder maths, and will strand stock the next time one
side is used and the other is not.

Evidence recorded per pair, so the owner rules rather than the machine:
  SPLIT     one side carries the purchases, the other the sales -- the
            signature of a code opened to replace another
  BOTH      both sides trade -- almost certainly two real products
  DORMANT   one side has no activity at all -- a stub
"""
import json, re, collections, itertools
import ingest as I, packmap as PM

stock={s["key"]:s for s in json.load(open("stock_final.json"))}
op=I.find_stock("31-03-2026","WHOLE STORES")[0]; cl=I.find_stock("26-08-2026","WHOLE STORES")[0]
pur,_,_=I.read_purchase(); sale=json.load(open("sale.json"))
res=json.load(open("resolve.json")); mp=res["mapping"]

seen={}
def note(name, where):
    k=PM.norm(name)
    if not k: return
    seen.setdefault(k, {"item":re.sub(r"\s+"," ",name.strip()), "where":set()})["where"].add(where)
for r in op["rows"]: note(r["item"],"31-Mar list")
for r in cl["rows"]: note(r["item"],"today's list")
for r in pur: note(r.get("item"),"purchase")
for l in sale:
    k=PM.norm(l.get("item"))
    note(mp.get(k,l.get("item")) if k in mp else l.get("item"),"sale")

def squash(s): return re.sub(r"[^A-Z0-9]","",s.upper())
def toks(s):   return re.findall(r"[A-Z0-9.]+",s.upper())
def subseq(a,b):
    it=iter(b); return all(any(w==x for x in it) for w in a)

pairs=[]
keys=sorted(seen)
bysq=collections.defaultdict(list)
for k in keys: bysq[squash(k)].append(k)
# 1 - identical once punctuation and spacing are removed
for sq,ks in bysq.items():
    for a,b in itertools.combinations(sorted(ks),2):
        pairs.append((a,b,"identical once spaces and punctuation are removed"))
# 2 - one contains the other, or one token inserted
for a,b in itertools.combinations(keys,2):
    if squash(a)==squash(b): continue
    sa,sb=squash(a),squash(b)
    if len(sa)<4 or len(sb)<4: continue
    why=None
    if sa in sb or sb in sa: why="one name contains the other"
    else:
        ta,tb=toks(a),toks(b)
        sh,lo=(ta,tb) if len(ta)<=len(tb) else (tb,ta)
        if len(sh)>=2 and 0<len(lo)-len(sh)<=1 and subseq(sh,lo):
            why="same name with '%s' added"%" ".join(w for w in lo if w not in sh)
        elif len(sa)==len(sb) and sum(x!=y for x,y in zip(sa,sb))==1:
            why="one character apart"
        elif len(sa)>=10 and sorted(sa)==sorted(sb):
            # THE SAME WORDS IN A DIFFERENT ORDER.
            # 'DISPO SYRINGE NIPRO 3ML' and 'NIPRO 3 ML DISPO SYRINGE' are one
            # product typed twice. A token test misses it because '3ML' and
            # '3 ML' tokenise differently; comparing the letters of the squashed
            # name catches it exactly. Ten characters minimum, so short codes
            # cannot pair up by coincidence.
            why="the same words in a different order"
    if why: pairs.append((a,b,why))

def act(k):
    s=stock.get(k)
    if not s: return (0,0,0,0)
    return (round(s["opening"]),round(s["purchased"]),round(s["sold"]-s["sreturn"]),round(s["closing"]))
rows=[]
for a,b,why in pairs:
    oa,pa,sa_,ca=act(a); ob,pb,sb_,cb=act(b)
    if pa+sa_+pb+sb_==0 and oa+ob+ca+cb==0: continue          # two empty stubs, nothing to rule on
    if (pa>0 and sa_==0 and sb_>0 and pb==0) or (pb>0 and sb_==0 and sa_>0 and pa==0):
        ev="SPLIT — purchases on one code, sales on the other"
    elif pa>0 and sa_>0 and pb>0 and sb_>0: ev="BOTH TRADE — probably two real products"
    elif (pa+sa_==0) or (pb+sb_==0):        ev="DORMANT — one side has no activity"
    else:                                    ev="PARTIAL — check"
    rows.append({"a":seen[a]["item"],"b":seen[b]["item"],"why":why,"evidence":ev,
                 "a_open":oa,"a_pur":pa,"a_sold":sa_,"a_close":ca,
                 "b_open":ob,"b_pur":pb,"b_sold":sb_,"b_close":cb,
                 "a_where":sorted(seen[a]["where"]),"b_where":sorted(seen[b]["where"])})
order={"SPLIT":0,"PARTIAL":1,"DORMANT":2,"BOTH TRADE":3}
rows.sort(key=lambda r:(order[r["evidence"].split(" —")[0]], -(r["a_close"]+r["b_close"]+r["a_open"]+r["b_open"])))
json.dump(rows,open("dupes.json","w"))
print("CANDIDATE DUPLICATE CODES: %d\n"%len(rows))
cur=None
for r in rows:
    tag=r["evidence"].split(" —")[0]
    if tag!=cur: cur=tag; print("\n### %s\n"%r["evidence"])
    print("  %-30s open %-5d pur %-5d sold %-5d now %-5d"%(r["a"][:30],r["a_open"],r["a_pur"],r["a_sold"],r["a_close"]))
    print("  %-30s open %-5d pur %-5d sold %-5d now %-5d   [%s]"%(r["b"][:30],r["b_open"],r["b_pur"],r["b_sold"],r["b_close"],r["why"]))
    print()
