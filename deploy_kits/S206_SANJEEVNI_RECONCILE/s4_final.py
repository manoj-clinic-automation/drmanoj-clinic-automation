#!/usr/bin/python3
"""s4_final.py -- the reconciliation of record. Nothing stranded, nothing guessed."""
import json, collections
import ingest as I, packmap as PM, resolve as R

sale = json.load(open("sale.json"))
pur, preps, _ = I.read_purchase()
op = I.find_stock("31-03-2026", "WHOLE STORES")[0]
cl = I.find_stock("26-08-2026", "WHOLE STORES")[0]
K = PM.norm

# ---------- 1 · master vocabulary: every name Marg itself holds ----------
master, packrow = set(), {}
for rep in (op, cl):
    for r in rep["rows"]:
        k = K(r["item"])
        if k: master.add(k); packrow.setdefault(k, r.get("packing"))
for r in pur:
    k = K(r.get("item"))
    if k: master.add(k); packrow.setdefault(k, r.get("packing"))

# ---------- 2 · unglue, then map truncated sale names onto the master ----------
glued = 0
for ln in sale:
    n, pk = R.unglue(ln.get("item") or "")
    if pk:
        glued += 1; ln["item"] = n; ln["pack"] = ln.get("pack") or pk
salekeys = {K(l["item"]) for l in sale if l.get("item")}
mapping, ambiguous, unresolved = R.build_map(salekeys, master)

# ---------- 3 · post every movement ----------
# ---------- 2b - FAMILY POOLING WHERE THE SIZE WAS NEVER RECORDED ----------
# Six sizes of 'L S BELT CONT GRAY UNISON _' cut to the same 20 characters.
# The sale report did not record which size left the shelf, so no per-size
# ledger can be right. The honest unit of reconciliation for such a family is
# THE FAMILY. Both the truncated sale code and every size in it post to one
# group, and the group is labelled so the limitation is visible on the page
# rather than buried. Inventing a size to make a line balance would be the
# worst outcome available here.
GRP, GRPNAME = {}, {}
for k, fam in ambiguous.items():
    g = "FAMILY " + k
    GRP[k] = g
    for m in fam:
        GRP[m] = g
    GRPNAME[g] = "%s (%s) - size not recorded on sale" % (
        k, "/".join((f[len(k):].strip() or "-") for f in fam))
def G(k):
    return GRP.get(k, k)

M = collections.defaultdict(lambda: collections.defaultdict(float))
disp, branch = {}, collections.Counter()

for tag, rep in (("opening", op), ("closing", cl)):
    for r in rep["rows"]:
        k = G(K(r["item"]))
        if k: disp.setdefault(k, GRPNAME.get(k, r["item"])); M[k][tag] += (r["units"] or 0)
for r in pur:
    k = G(K(r.get("item")))
    if not k: continue
    disp.setdefault(k, GRPNAME.get(k, r["item"]))
    M[k]["preturn" if r.get("is_return") else "purchased"] += (r.get("loose_qty") or 0)
for ln in sale:
    k = K(ln.get("item"))
    if not k: continue
    k = G(mapping.get(k, k))
    disp.setdefault(k, GRPNAME.get(k, ln["item"]))
    u, how = I.sale_units(ln, PM.pack_size(ln.get("pack")) or PM.pack_size(packrow.get(k)))
    branch[how] += 1
    if u is None: continue
    M[k]["sreturn" if I.is_credit_note(ln["bill"]) else "sold"] += u

rows = []
for k in sorted(M):
    d = M[k]
    o,p,pr,s,sr,c = d["opening"],d["purchased"],d["preturn"],d["sold"],d["sreturn"],d["closing"]
    exp = o + p - pr - s + sr
    rows.append({"key":k,"item":disp[k],"opening":o,"purchased":p,"preturn":pr,"sold":s,
                 "sreturn":sr,"expected":exp,"closing":c,"var":round(c-exp,3),
                 "size":PM.pack_size(packrow.get(k)),"in_master":k in master,
                 "family":k.startswith("FAMILY "),
                 "in":[t for t in ("opening","purchased","preturn","sold","sreturn","closing") if d[t]]})
json.dump(rows, open("ledger_final.json","w"))
json.dump({"mapping":mapping,"ambiguous":ambiguous,"unresolved":unresolved},open("resolve.json","w"))

active=[r for r in rows if any(abs(r[t])>0 for t in ("opening","purchased","preturn","sold","sreturn","closing"))]
tol=0.5
bal=[r for r in active if abs(r["var"])<=tol]; off=[r for r in active if abs(r["var"])>tol]
print("unglued sale lines            : %d"%glued)
print("truncated names mapped        : %d"%len(mapping))
print("truncated but AMBIGUOUS       : %d  %s"%(len(ambiguous), list(ambiguous)))
print("sale names in no master       : %d"%len(unresolved))
print("sale qty branches             : %s"%dict(branch))
print("\nITEMS THAT MOVED %d    BALANCED %d (%.1f%%)    OFF %d"%(
    len(active),len(bal),100.0*len(bal)/len(active),len(off)))
print("  surplus %+.0f   shortfall %+.0f   net %+.0f"%(
    sum(r["var"] for r in off if r["var"]>0),sum(r["var"] for r in off if r["var"]<0),
    sum(r["var"] for r in active)))
print("\nEVERY REMAINING VARIANCE")
print("  %-30s %7s %7s %6s %7s %5s %7s %8s"%("item","open","purch","-pret","-sold","+cn","close","VAR"))
for r in sorted(off,key=lambda r:-abs(r["var"])):
    print("  %-30s %7.0f %7.0f %6.0f %7.0f %5.0f %7.0f %+8.0f"%(
        r["item"][:30],r["opening"],r["purchased"],r["preturn"],r["sold"],r["sreturn"],r["closing"],r["var"]))
