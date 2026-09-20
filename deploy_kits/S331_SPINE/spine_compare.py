"""spine_compare.py -- S272 / kit S331 (Sanjeevni). Rung 3's witness: where do today's tables differ from the spine?

    /root/wa/venv/bin/python3 -B /root/finance/spine/spine_compare.py [--finance-db /root/finance/finance.db] [--spine spine.db]

READ-ONLY on both databases (finance.db is opened with mode=ro). Prints, per lane, what the live tables say
against what the spine says, so the day a lane is moved onto the spine (rung 4) the difference is known in
advance and not discovered on a screen. It writes one file, spine_compare_latest.txt, beside the spine.
It never writes finance.db, never reads a stock-count table for anything but a count of rows.
"""
import argparse
import collections
import datetime as dt
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spine_read import Spine, K  # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def compare(fin, sp, out=print):
    q = lambda s, *a: fin.execute(s, a).fetchall()
    lines = []
    L = lines.append
    L("spine_compare %s" % dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"))
    # 1. sale bills
    live = {(r[0], r[1]): r[2] for r in q("SELECT business_date, bill_no, gross_p FROM sale_bill")}
    spb = {(r["date"], r["bill"]): r["gross_p"] for r in sp.q("SELECT date, bill, gross_p FROM sp_sale_bill")}
    only_sp = [k for k in spb if k not in live]
    diff = [k for k in live if k in spb and live[k] != spb[k]]
    L("SALE BILLS  live sale_bill %d · spine %d · in spine only %d (from %s) · gross differs %d" % (
        len(live), len(spb), len(only_sp), min(k[0] for k in only_sp) if only_sp else "-", len(diff)))
    # 2. sale lines by day
    ld = collections.Counter(r[0] for r in q("SELECT business_date FROM sale_line_item"))
    sd = collections.Counter(r["date"] for r in sp.q("SELECT date FROM sp_sale_line"))
    days_missing = sorted(d for d in sd if ld.get(d, 0) == 0)
    days_off = sorted(d for d in sd if ld.get(d, 0) not in (0, sd[d]))
    L("SALE LINES  live sale_line_item %d · spine %d · days live has none of: %s · days line counts differ: %s" % (
        sum(ld.values()), sum(sd.values()), days_missing, days_off[:10]))
    # 3. purchases
    lp = {(r[0], r[1]): r[2] for r in q("SELECT supplier_norm, bill_no, amount_p FROM purchase_bill")}
    ret = sp.q("SELECT supplier, bill, date, amount_p FROM sp_purchase_bill WHERE direction='RETURN'")
    live_ret = q("SELECT COUNT(*) FROM purchase_line WHERE direction<>'PURCHASE'")[0][0]
    L("PURCHASES   live purchase_bill %d · spine %d · spine returns %d (%s) · live lines marked RETURN %d" % (
        len(lp), len(sp.q("SELECT 1 FROM sp_purchase_bill")), len(ret), ", ".join("%s/%s" % (r["supplier"][:10], r["bill"]) for r in ret), live_ret))
    # 4. salts
    ls = {r[0]: r[1] for r in q("SELECT item, salt FROM purchase_salt_marg")}
    ss = {}
    for r in sp.q("SELECT name, value FROM sp_item_fact WHERE fact='salt' AND as_on=(SELECT MAX(as_on) FROM sp_item_fact WHERE fact='salt')"):
        ss.setdefault(r["name"], r["value"])
    wrong = [(n, ls[n], ss[n]) for n in ls if n in ss and (ls[n] or "").upper() != (ss[n] or "").upper()]
    L("SALTS       live purchase_salt_marg %d · spine %d · differ %d%s" % (len(ls), len(ss), len(wrong),
      (": " + "; ".join("%s live=%s spine=%s" % w for w in wrong[:6])) if wrong else ""))
    # 5. MRP: the live median-price rule vs Marg's own MRP
    mrp = {}
    for r in sp.q("SELECT name, value FROM sp_item_fact WHERE fact='mrp' AND as_on=(SELECT MAX(as_on) FROM sp_item_fact WHERE fact='mrp')"):
        mrp.setdefault(K(r["name"]), r["value"])
    live_mrp = {}
    try:
        for r in q("SELECT i.canonical_raw, f.value FROM marg_item i JOIN marg_item_fact f ON f.item_id=i.item_id "
                   "WHERE f.fact='mrp_p' AND f.value IS NOT NULL AND f.value<>''"):
            live_mrp[K(r[0])] = float(r[1])
    except sqlite3.Error:
        pass
    import re as _re
    pk = {}
    for r in sp.q("SELECT k20, packing FROM sp_item"):
        m = _re.match(r'^(\d+)\*(\d+)$', (r["packing"] or "").rstrip("."))
        pk.setdefault(r["k20"], int(m.group(1)) * int(m.group(2)) if m else 1)
    # the live fact is a per-UNIT median sale price; Marg's MRP is per PACK
    off = [(k, live_mrp[k] / 100.0 * pk.get(k, 1), mrp[k]) for k in live_mrp
           if k in mrp and mrp[k] not in (None, "None") and abs(live_mrp[k] / 100.0 * pk.get(k, 1) - float(mrp[k])) > 0.5]
    L("MRP         live median-price facts (x pack) %d · Marg MRP in spine %d · differ by more than Rs 0.50: %d%s" % (
      len(live_mrp), len(mrp), len(off), (": " + "; ".join("%s live=%.2f Marg=%s" % o for o in sorted(off, key=lambda o: -abs(o[1] - float(o[2])))[:5])) if off else ""))
    # 6. stock now
    latest = sp.q("SELECT MAX(as_on) AS d FROM sp_close")[0]["d"]
    fl = q("SELECT as_on, COUNT(*) FROM stock_snapshot GROUP BY as_on ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC LIMIT 1")
    L("STOCK       spine latest Marg closing %s · live stock_snapshot latest %s" % (latest, fl[0] if fl else "-"))
    L("COUNT #1    stock_count_item rows %d (read-only look; the spine writes nothing here)" % q("SELECT COUNT(*) FROM stock_count_item")[0][0])
    L("SPINE       " + sp.status())
    for x in lines:
        out(x)
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance-db", default="/root/finance/finance.db")
    ap.add_argument("--spine", default=os.path.join(HERE, "spine.db"))
    a = ap.parse_args(argv)
    fin = sqlite3.connect("file:%s?mode=ro" % a.finance_db, uri=True)
    sp = Spine(a.spine)
    lines = compare(fin, sp)
    with open(os.path.join(os.path.dirname(a.spine), "spine_compare_latest.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
