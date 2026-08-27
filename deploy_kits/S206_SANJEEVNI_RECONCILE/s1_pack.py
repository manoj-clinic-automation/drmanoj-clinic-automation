import json, collections, sys
import ingest as I, packmap as PM

sale, sfiles, sobs = I.read_sale()
pur,  pfiles, pobs = I.read_purchase()
op = I.find_stock("31-03-2026", "WHOLE STORES") or I.find_stock("31-03-2026", "MAIN STORE")
cl = I.find_stock("26-08-2026", "WHOLE STORES")
print("opening exports:", [(r["store"], r["source"], len(r["rows"])) for r in op])
print("closing exports:", [(r["store"], r["source"], len(r["rows"])) for r in cl])

obs = list(sobs) + list(pobs)
for rep, tag in ((op[0] if op else None, "open"), (cl[0] if cl else None, "close")):
    if rep:
        for r in rep["rows"]:
            obs.append((r["item"], r.get("packing"), tag))

pm, conf = PM.build(obs)
json.dump({k: v for k, v in pm.items()}, open("packmap.json", "w"))
json.dump(conf, open("packconf.json", "w"))
json.dump(sale, open("sale.json", "w"))

print("\nsale lines %d   purchase rows %d   items with a packing %d" % (len(sale), len(pur), len(pm)))
whole = sum(1 for v in pm.values() if v["whole"])
print("  strip items %d   whole-unit items %d" % (len(pm)-whole, whole))
sz = collections.Counter(v["size"] for v in pm.values() if v["size"])
print("  strip sizes:", ", ".join("1*%d:%d" % (k, n) for k, n in sz.most_common()))
print("\nPACK-SIZE CONFLICTS: %d" % len(conf))
for c in conf:
    print("  %-32s %s" % (c["item"][:32],
        " vs ".join("%s(=%s, %d lines %s)" % (v["packing"], v["size"], v["lines"],
                    "/".join(sorted(v["sources"]))) for v in c["variants"])))
