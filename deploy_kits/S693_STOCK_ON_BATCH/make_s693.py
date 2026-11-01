#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s693.py -- kit S693_STOCK_ON_BATCH (01-Nov-2026, Sanjeevni session 375).

    python3 -B make_s693.py <root> <outdir>     reads <root>/finance/expiry_watch.py, writes <outdir>/finance/expiry_watch.py

WHY (the plan's section 9, step 0 -- the S690 plan's step 3; the owner's word 1-Nov 09:28 'club these and build now').  The expiry watch
lowers every batch of the newest whole-shop Batch Stock by the spine's sale lines after the report's day -- but a purchase after that day
reaches no batch (the spine's purchase lines carry no batch), so a medicine bought again since the report (93 of 159 sold in October) is
judged only by Marg's own printed minus; a counter sale into a minus batch on such a medicine waits for the next monthly report.

WHAT.  One file, expiry_watch.py, six anchored edits (each anchor must occur exactly once, else the builder refuses):
  1. _s693_place(...) and _s693_sale_tie(...) above _sales_after: the purchase item report's lines after the report's day (finance.db
     purchase_line, the effective exports only -- the purchase page's own rule; direction PURCHASE; medicines) are placed on their batch:
     the report prints the LAST 8 characters of a batch, so a line ties to the ONE Batch Stock batch of the same medicine whose letters
     and digits are equal to, or end with, the printed batch (4+ characters); a batch the report has and the Batch Stock does not is a
     NEW batch (its expiry from the line); a line with no batch, or one that fits two batches, leaves its medicine UNTIED (judged as
     before).  Units are the report's loose figure (Marg's own unit, the Batch Stock's), else (qty + free) x pack.
  2. compute(): the placement runs after the Batch Stock is read and before the sales are taken off.
  3. a sale line whose batch is not on the Batch Stock as printed is tied by the same letters-and-digits rule (one batch only).
  4. the wrong-batch rule: a re-bought medicine whose every purchase since the report was placed is judged like any other (a batch below
     zero beside one with stock); an untied one still by Marg's printed minus alone.  The run's note records what was placed.
Nothing else changes: the voucher pair (S690), the owner's page, the readers, the fixes' judging (printed figures), every other section.
"""
import hashlib
import os
import sys

REL = "finance/expiry_watch.py"
FROM = "b68cda86162768661226065192286336"

EDITS = [
    # 0 -- the kit's name on every run it writes
    ('KIT = "S690_AMIR_BATCH_FIX"          # S638 built the watch; S690: the voucher pair, the Batch Stock every ',
     'KIT = "S693_STOCK_ON_BATCH"          # S638 built the watch; S693 new stock on its batch; S690: the voucher pair, the Batch Stock every '),
    # 1 -- the placement, above _sales_after
    ('\ndef _sales_after(R):\n',
     '\n'
     'EFF_LINE_S693 = ("EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND e.md5=l.source_md5)")   # purchase_app.EFF_LINE\n'
     '\n\n'
     'def _s693_alnum(b):\n'
     '    return re.sub(r\'[^A-Z0-9]\', \'\', nbatch(b))\n'
     '\n\n'
     'def _s693_fits(x, a):\n'
     '    return bool(x) and len(a) >= 4 and len(x) >= 4 and (x == a or x.endswith(a) or a.endswith(x))\n'
     '\n\n'
     'def _s693_tie(cands, pb):\n'
     '    """The ONE batch among cands (bt keys of one medicine) whose letters-and-digits equal, or end with, the printed batch pb\n'
     '    (the purchase item report prints the last 8 characters of a batch; 4+ characters; either may be the clip of the other, so a sale\n'
     '    printing a batch in full ties to a new batch made from the report\'s clip).  -> the key, or None (none, or more than one)."""\n'
     '    a = _s693_alnum(pb)\n'
     '    if len(a) < 4:\n'
     '        return None\n'
     '    hit = [kk for kk in cands if kk[1] and _s693_fits(_s693_alnum(kk[1]), a)]\n'
     '    return hit[0] if len(hit) == 1 else None\n'
     '\n\n'
     'def _s693_expiry(v):\n'
     '    """The purchase line\'s expiry (\'5/28\', \'12/2027\', \'2027-05\') as the watch\'s YYYY-MM, else \'\'."""\n'
     '    s = str(v or "").strip()\n'
     '    m = re.match(r\'^(\\d{1,2})/(\\d{2}|\\d{4})$\', s)\n'
     '    if m:\n'
     '        y = int(m.group(2))\n'
     '        return "%04d-%02d" % (y + 2000 if y < 100 else y, int(m.group(1)))\n'
     '    return s if re.match(r\'^\\d{4}-\\d{2}$\', s) else ""\n'
     '\n\n'
     'def _s693_place(con, bt, order, key, is_o, sales_after):\n'
     '    """S693 (plan step 3): new stock placed on its batch from the purchase item report (purchase_line, effective exports, PURCHASE,\n'
     '    bill date after the report\'s day, medicines).  Writes into bt: units (+ the purchase), bought (+), and a NEW batch for one the\n'
     '    Batch Stock does not print (printed 0, new 1).  -> (by_k: medicine -> its bt keys; tied: medicines whose every such line was placed;\n'
     '    untied: medicines with a line that could not be placed; placed: the count of lines placed; placed_units: units placed per medicine).\n'
     '    Reads only; fail-soft: nothing placed."""\n'
     '    by_k = {}\n'
     '    for kk in order:\n'
     '        by_k.setdefault(kk[0], []).append(kk)\n'
     '    tied, untied, placed = set(), set(), 0\n'
     '    placed_units = {}\n'
     '    if not _has(con, "purchase_line") or not _has(con, "purchase_export"):\n'
     '        return by_k, tied, untied, placed, placed_units\n'
     '    try:\n'
     '        rows = con.execute("SELECT l.item, l.packing, l.batch, l.expiry, l.qty, l.free, l.loose_qty, l.supplier_norm, l.bill_no, l.bill_date "\n'
     '                           "FROM purchase_line l WHERE l.bill_date > ? AND l.direction=\'PURCHASE\' AND COALESCE(l.line_type,\'ITEMWISE\')=\'ITEMWISE\' AND "\n'
     '                           + EFF_LINE_S693 + " ORDER BY l.bill_date, l.id", (sales_after,)).fetchall()\n'
     '    except sqlite3.Error:\n'
     '        return by_k, tied, untied, placed, placed_units\n'
     '    seen = set()\n'
     '    for item, packing, batch, expiry, qty, free, loose, sup, bill, bdate in rows:\n'
     '        if is_o(item, packing or ""):\n'
     '            continue\n'
     '        line_key = (sup, bill, bdate, item, nbatch(batch or ""), qty, free, loose)    # S227: the same bill line in two overlapping exports counts once\n'
     '        if line_key in seen:\n'
     '            continue\n'
     '        seen.add(line_key)\n'
     '        k = key(item)\n'
     '        pb = nbatch(batch or "")\n'
     '        pack = pack_of(packing or "")\n'
     '        # units = Marg\'s own LOOS figure: the Batch Stock\'s unit (THIO Q AP 1*10: bought 10 + 2 free, loose 12, printed 12; CCM 1*40: loose 5,\n'
     '        # printed 5) -- NOT the count\'s tablet rule (stock_app._purchase_units), which would place 132 and 205 against a print of 12 and 5\n'
     '        units = int(round(loose)) if loose is not None else int(round(((qty or 0) + (free or 0)) * pack))\n'
     '        if not pb or units <= 0:\n'
     '            untied.add(k)\n'
     '            continue\n'
     '        cands = by_k.get(k, [])\n'
     '        kk = (k, pb) if (k, pb) in bt else _s693_tie(cands, pb)\n'
     '        if kk is None:\n'
     '            a = _s693_alnum(pb)\n'
     '            if any(kk2[1] and _s693_fits(_s693_alnum(kk2[1]), a) for kk2 in cands):\n'
     '                untied.add(k)                             # two batches fit the printed piece\n'
     '                continue\n'
     '            kk = (k, pb)                                  # a batch the Batch Stock does not print: new\n'
     '            base = bt[cands[0]] if cands else {}\n'
     '            bt[kk] = dict(item=base.get("item", item), k20=k, packing=base.get("packing", packing or ""), pack=base.get("pack", pack),\n'
     '                          batch=pb, expiry=_s693_expiry(expiry), units=0, printed=0, sold=0, bought=0, new=1)\n'
     '            order.append(kk)\n'
     '            by_k.setdefault(k, []).append(kk)\n'
     '        x = bt[kk]\n'
     '        x["units"] += units\n'
     '        x["bought"] = x.get("bought", 0) + units\n'
     '        if not x.get("expiry") and expiry:\n'
     '            x["expiry"] = _s693_expiry(expiry)\n'
     '        tied.add(k)\n'
     '        placed += 1\n'
     '        placed_units[k] = placed_units.get(k, 0) + units\n'
     '    tied -= untied\n'
     '    return by_k, tied, untied, placed, placed_units\n'
     '\n\n'
     'def _s693_sale_tie(bt, by_k, k, nb):\n'
     '    """A sale line\'s batch not printed as such on the Batch Stock: the one batch of the medicine it fits (letters and digits), else None."""\n'
     '    return _s693_tie(by_k.get(k, []), nb)\n'
     '\n\n'
     'def _sales_after(R):\n'),
    # 2 -- the placement in compute(), before the sales are taken off
    ('        new_wrong = []\n',
     '        by_k, s693_tied, s693_untied, s693_placed, s693_units = _s693_place(con, bt, order, key, is_o, sales_after)   # S693: new stock on its batch\n'
     '        sp_bought = {}                                        # the spine\'s own purchase units since the day: a report that lags the spine is not whole\n'
     '        for r in sp.execute("SELECT k20, COALESCE(SUM(units),0) FROM sp_move WHERE kind=\'PURCHASE\' AND date > ? GROUP BY k20", (sales_after,)):\n'
     '            kk0 = alias.get(r[0], r[0])\n'
     '            sp_bought[kk0] = sp_bought.get(kk0, 0) + (r[1] or 0)\n'
     '        s693_tied = {k for k in s693_tied if s693_units.get(k, 0) + 0.5 >= sp_bought.get(k, 0)}\n'
     '        s693_untied = set(s693_untied) | {k for k in s693_units if k not in s693_tied}\n'
     '        new_wrong = []\n'),
    # 3 -- a sale whose batch is printed differently
    ('            if (k, nb) in bt:\n'
     '                x = bt[(k, nb)]\n',
     '            if (k, nb) not in bt and nb:\n'
     '                kk3 = _s693_sale_tie(bt, by_k, k, nb)     # S693: the batch as the sale text prints it vs the Batch Stock\'s\n'
     '                if kk3 is not None:\n'
     '                    nb = kk3[1]\n'
     '            if (k, nb) in bt:\n'
     '                x = bt[(k, nb)]\n'),
    # 4 -- the wrong-batch rule and the run\'s note
    ('            if k in bought_since:                             # a re-supply carries no batch on the spine: only Marg\'s own printed minus counts\n',
     '            if k in bought_since and k not in s693_tied:      # S693: a re-supply placed on its batch is judged like any other; untied: Marg\'s printed minus only\n'),
    ('        run["_bt"], run["_sales_after"], run["_bought"] = bt, sales_after, bought_since    # S690: for the fixes (never persisted)\n',
     '        run["_bt"], run["_sales_after"], run["_bought"] = bt, sales_after, bought_since    # S690: for the fixes (never persisted)\n'
     '        run["note"] = (run["note"] + (" | " if run["note"] else "") + "S693: %d purchase line(s) since %s placed on %d batch(es), %d new; untied %s"\n'
     '                       % (s693_placed, sales_after, len({kk for kk in bt if bt[kk].get("bought")}), len([kk for kk in bt if bt[kk].get("new")]),\n'
     '                          ",".join(sorted(s693_untied))[:200] or "none"))[:900]\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src_bytes, want_from):
    if md5(src_bytes) != want_from:
        raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (REL, md5(src_bytes)[:8], want_from[:8]))
    s = src_bytes.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %d occurs %d times (must be exactly once)" % (i, n))
        s = s.replace(old, new, 1)
    return s.encode("utf-8")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, outdir = sys.argv[1], sys.argv[2]
    with open(os.path.join(root, REL), "rb") as fh:
        out = build(fh.read(), FROM)
    dst = os.path.join(outdir, REL)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(out)
    print("built %s %s -> %s (%d edits)" % (REL, FROM[:8], md5(out)[:8], len(EDITS)))


if __name__ == "__main__":
    main()
