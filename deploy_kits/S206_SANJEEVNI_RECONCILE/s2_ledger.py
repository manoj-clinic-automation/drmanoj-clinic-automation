#!/usr/bin/python3
"""
s2_ledger.py -- one ledger per item, and nothing stranded.

    opening(31-Mar-2026) + purchased - vendor returns - sold + credit notes
        = closing(26-Aug-2026)

CONVERSION RULE (decided by measurement, not preference)
    Each `packs:loose` pair is converted with THE PACKING PRINTED ON ITS OWN
    ROW, never with a map-wide pack size. Marg printed that pair against that
    packing; using a different one changes the answer by a multiple. The
    pack map is used only to CLASSIFY (strip vs whole) and to DISPLAY.
"""
import json, collections, sys
import ingest as I, packmap as PM

sale = json.load(open("sale.json"))
pm   = json.load(open("packmap.json"))
pur, preps, _ = I.read_purchase()
op = I.find_stock("31-03-2026", "WHOLE STORES")[0]
cl = I.find_stock("26-08-2026", "WHOLE STORES")[0]

def K(n): return PM.norm(n)
M = collections.defaultdict(lambda: collections.defaultdict(float))
disp, branch = {}, collections.Counter()

# ---- opening / closing : row's own packing ----
for tag, rep in (("opening", op), ("closing", cl)):
    for r in rep["rows"]:
        k = K(r["item"])
        if not k: continue
        disp.setdefault(k, r["item"])
        M[k][tag] += (r["units"] or 0)

# ---- purchase : loose_qty is already base units; returns flagged ----
noqty = 0
for r in pur:
    k = K(r.get("item"))
    if not k: continue
    disp.setdefault(k, r["item"])
    q = r.get("loose_qty")
    if q is None:
        noqty += 1; continue
    M[k]["preturn" if r.get("is_return") else "purchased"] += q

# ---- sale : credit notes are goods coming BACK ----
unread = []
for ln in sale:
    k = K(ln.get("item"))
    if not k: continue
    disp.setdefault(k, ln["item"])
    size = PM.pack_size(ln.get("pack"))
    u, how = I.sale_units(ln, size)
    branch[how] += 1
    if u is None:
        unread.append(ln); continue
    M[k]["sreturn" if I.is_credit_note(ln["bill"]) else "sold"] += u

rows = []
for k in sorted(M):
    d = M[k]
    o,p,pr,s,sr,c = (d["opening"],d["purchased"],d["preturn"],d["sold"],d["sreturn"],d["closing"])
    exp = o + p - pr - s + sr
    rows.append({"key":k,"item":disp[k],"opening":o,"purchased":p,"preturn":pr,
                 "sold":s,"sreturn":sr,"expected":exp,"closing":c,
                 "var":round(c-exp,3),
                 "size":(pm.get(k) or {}).get("size"),
                 "in":[t for t in ("opening","purchased","preturn","sold","sreturn","closing") if d[t]]})
json.dump(rows, open("ledger2.json","w"))

tol=0.5
bal=[r for r in rows if abs(r["var"])<=tol]; off=[r for r in rows if abs(r["var"])>tol]
print("sale qty branches:", dict(branch), " unreadable:", len(unread), " purchase rows w/o qty:", noqty)
print("purchase reports:"); [print("   %-58s %5d rows  %s"%f) for f in preps]
print("\nITEMS %d    BALANCED %d (%.1f%%)    OFF %d"%(len(rows),len(bal),100.0*len(bal)/len(rows),len(off)))
print("  surplus on shelf %+.0f    shortfall %+.0f    net %+.0f"%(
    sum(r["var"] for r in off if r["var"]>0), sum(r["var"] for r in off if r["var"]<0),
    sum(r["var"] for r in rows)))
print("\nWORST 30 BY ABSOLUTE VARIANCE")
print("  %-30s %8s %8s %8s %8s %8s %8s %9s"%("item","open","purch","-pret","-sold","+cn","close","VAR"))
for r in sorted(off,key=lambda r:-abs(r["var"]))[:30]:
    print("  %-30s %8.0f %8.0f %8.0f %8.0f %8.0f %8.0f %+9.0f"%(
        r["item"][:30],r["opening"],r["purchased"],r["preturn"],r["sold"],r["sreturn"],r["closing"],r["var"]))
