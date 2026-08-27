#!/usr/bin/python3
"""
s15_reorder.py -- what to order, from whom, in strips.

COVER TARGET
    Order up to 30 days of cover, in whole strips, for anything with less
    than 14 days left. 30/14 are the owner's practical rhythm: he orders from
    Ravi and Agarwal on the 1st, and the fast movers arrive weekly.

WHY IT IS BUNDLED BY STOCKIST
    The owner's constraint is not money, it is BILLS: every bill is an entry
    Amir has to make. One order to Kedar covering nine items is one bill.
    Nine separate orders are nine.
"""
import json, collections, math
import packmap as PM
stock=json.load(open("stock_final.json"))
MO=["2026-04","2026-05","2026-06","2026-07","2026-08"]
TARGET, TRIGGER = 30, 14

def vendor(s):
    v=collections.Counter()
    for m in MO:
        for x in (s.get("months",{}).get(m,{}) or {}).get("vend",[]): v[x]+=1
    return v.most_common(1)[0][0] if v else None

# A TOP-UP RULE IS ONLY SAFE ON A REGULAR MOVER.
# 'HYLASTO S4 PFS' sells 0.2 a day and costs thousands a unit. Thirty days of
# cover on it is a five-figure order for an item that moves a few times a
# quarter -- the arithmetic is right and the instruction is wrong. So an item
# qualifies for AUTOMATIC top-up only if it sold in at least two of the last
# three months. Everything else that is running low is still surfaced, under
# CONFIRM FIRST, with its numbers -- never dropped, never auto-ordered.
RECENT = ["2026-06", "2026-07", "2026-08"]

def regular(s):
    return sum(1 for m in RECENT if (s.get("months", {}).get(m, {}) or {}).get("sold", 0) > 0) >= 2

need, confirm = [], []
for s in stock:
    if s["per_day"] <= 0.02: continue
    cov = s["closing"] / s["per_day"] if s["per_day"] > 0 else 9e9
    if cov >= TRIGGER: continue
    want = s["per_day"] * TARGET - s["closing"]
    if want <= 0: continue
    sz = s["size"] or 1
    strips = max(1, int(math.ceil(want / sz)))
    rec = {**s, "cover": cov, "order_units": strips * sz, "order_strips": strips,
           "vendor": vendor(s), "order_value": round(strips * sz * (s.get("cost_per_unit") or 0)),
           "regular": regular(s)}
    (need if rec["regular"] else confirm).append(rec)
byv=collections.defaultdict(list)
for n in need: byv[n["vendor"] or "NO VENDOR ON RECORD"].append(n)
json.dump({"auto":need,"confirm":confirm},open("reorder_final.json","w"))
print("REORDER: %d items below %d days cover, topped to %d days"%(len(need),TRIGGER,TARGET))
print("bundled into %d orders instead of %d separate ones\n"%(len(byv),len(need)))
for v,items in sorted(byv.items(),key=lambda kv:-sum(i["order_value"] for i in kv[1])):
    val=sum(i["order_value"] for i in items)
    print("%s   %d items   about Rs %s"%(v,len(items),format(val,",")))
    for i in sorted(items,key=lambda i:i["cover"]):
        print("    %-28s have %-18s %5.1f/day  %4.1f d   ORDER %s"%(
            i["item"][:28],i["shelf"],i["per_day"],i["cover"],
            ("%d strips"%i["order_strips"]) if i["size"] else ("%d"%i["order_units"])))
    print()
print("CONFIRM FIRST -- low on stock but not a regular mover (%d items, about Rs %s)"%(
    len(confirm),format(sum(i["order_value"] for i in confirm),",")))
for i in sorted(confirm,key=lambda i:-i["order_value"])[:14]:
    print("    %-28s have %-16s %4.2f/day  sold in %d of last 3 months  would be Rs %s"%(
        i["item"][:28],i["shelf"],i["per_day"],
        sum(1 for m in RECENT if (i.get("months",{}).get(m,{}) or {}).get("sold",0)>0),
        format(i["order_value"],",")))
