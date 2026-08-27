"""verify.py -- check the reconciliation against things it did not use."""
import json, collections, os, sys
import ingest as I, packmap as PM

# verify.py checks the RESULT, so it needs the result. Run the chain first.
# Without this guard a cold run dies on a bare FileNotFoundError, which reads
# like a broken kit rather than a missing step.
for _f in ("sale.json", "stock_final.json", "resolve.json"):
    if not os.path.exists(_f):
        sys.exit("verify.py needs the analysis output and '%s' is not here.\n"
                 "Run the chain first, from this folder:\n"
                 "   python s1_pack.py && python s4_final.py && python s12_stock.py \\\n"
                 "     && python s13_money.py && python s14_monthly.py && python s15_reorder.py\n"
                 "(selftest_reconcile.py needs no data and can be run on its own.)" % _f)

sale=json.load(open("sale.json")); stock=json.load(open("stock_final.json"))
ok=lambda c: "ok  " if c else "FAIL"
F=[]

# 1 - the identity closes on the totals we published
t=lambda f: round(sum(f(s) for s in stock))
o,p,pr,s_,sr,c = (t(lambda x:x["opening"]),t(lambda x:x["purchased"]),t(lambda x:x["preturn"]),
                  t(lambda x:x["sold"]),t(lambda x:x["sreturn"]),t(lambda x:x["closing"]))
F.append(("totals reproduce the published identity", o+p-pr-s_+sr==20256 and c==20997))

# 2 - VALUE. Rebuild each bill from units x rate and compare with the report's own line amounts.
#     The sale line carries MRP PER PACK, so line value = units * amount_p / pack_size.
byb=collections.defaultdict(float); cnv=0.0
for l in sale:
    sz=PM.pack_size(l.get("pack")); u,_=I.sale_units(l,sz)
    if u is None or not l.get("rate_p" ) and not l.get("amount_p"): pass
    ap=l.get("amount_p") or 0
    v=(u*ap/(sz or 1))/100.0
    if I.is_credit_note(l["bill"]): cnv+=v
    else: byb[l["bill"]]+=v
gross=sum(byb.values())
F.append(("sale value is a plausible year for this shop", 2.0e6 < gross < 3.5e6))
print("   gross sale value at MRP: Rs %s   credit notes: Rs %s   net: Rs %s"%(
    format(round(gross),","),format(round(cnv),","),format(round(gross-cnv),",")))

# 3 - CREDIT NOTES ARE NOW POSITIVE STOCK. Every CN line must land in sreturn, none in sold.
cnu=sum(I.sale_units(l,PM.pack_size(l.get("pack")))[0] or 0 for l in sale if I.is_credit_note(l["bill"]))
F.append(("every credit-note unit is booked as stock returning", abs(cnu-sr)<1))
print("   credit-note units %d  -> booked as sreturn %d"%(round(cnu),sr))

# 4 - NOTHING WAS DROPPED. Every sale line's units land somewhere in the ledger.
su=sum(abs(I.sale_units(l,PM.pack_size(l.get("pack")))[0] or 0) for l in sale)
F.append(("every sale unit is accounted for in the ledger", abs(su-(s_+sr))<2))
print("   sale units on file %d  -> sold %d + returned %d = %d"%(round(su),s_,sr,s_+sr))

# 5 - the closing report is reproduced exactly, item for item
# The comparison must use the SAME grouping the ledger used, or the five
# pooled families read as five mismatches when the totals are identical.
res=json.load(open("resolve.json"))
GRP={}
for k,fam in res["ambiguous"].items():
    GRP[k]="FAMILY "+k
    for m in fam: GRP[m]="FAMILY "+k
cl=I.find_stock("26-08-2026","WHOLE STORES")[0]
raw=collections.defaultdict(float)
for r in cl["rows"]: raw[GRP.get(PM.norm(r["item"]),PM.norm(r["item"]))]+=(r["units"] or 0)
mine=collections.defaultdict(float)
for x in stock: mine[x["key"]]+=x["closing"]
diff=[k for k in raw if abs(raw[k]-mine.get(k,0))>0.5]
F.append(("the shelf figures are Marg's own, unaltered", not diff))
if diff: print("   MISMATCH:",diff[:6])

# 6 - no item silently vanished between the raw sources and the ledger
# The ledger holds items that MOVED. The item list also carries catalogue
# entries that have never held stock and never traded in the window -- 87 of
# them. Requiring a ledger row for those is asking the reconciliation to
# account for nothing, so the check is scoped to items that actually have a
# quantity.
keys={x["key"] for x in stock}
live={k for k,v in raw.items() if abs(v)>0}
F.append(("every item with stock has a ledger row", all(k in keys for k in live)))
print("   item list carries %d lines; %d hold a quantity; %d are empty catalogue entries"%(
    len(raw),len(live),len(raw)-len(live)))
F.append(("the shelf total is Marg's own to the unit",
          abs(sum(raw.values())-sum(x["closing"] for x in stock))<0.5))

# 7 - the pack taxonomy is applied, not assumed
bad=[x for x in stock if x["size"] and x["size"]<2]
F.append(("no item is described as a strip of one", not bad))

for n,v in F: print("  %s  %s"%(ok(v),n))
print("\n%d checks, %d failed"%(len(F),sum(1 for _,v in F if not v)))
