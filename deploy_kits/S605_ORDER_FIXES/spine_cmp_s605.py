#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spine_cmp_s605.py -- kit S605_ORDER_FIXES, F-951: the stop conditions of the brief's section 3.6, on two SCRATCH spines.

    python3 -B spine_cmp_s605.py --old <spine.db built by the OLD spine_build> --new <spine.db built by the NEW one> --finance-db <a COPY> --rules <spine_rules.json>

Read only (every database opened mode=ro). The eight families are the ticked renames whose old 20-character key more than one ticked rename
shares (marg_item_rename, as spine_build reads it); their keys = every old key and every new key. Prints, per table, the rows OLD vs NEW;
STOP (exit 3) when a row differs under ANY other key, when a table without a key differs, when the NEW gate does not pass, or when check 5
(the 06-Sep count baseline) is not green. Then, per family: the split day, each key's Marg closing and the spine's figure at the latest
closing (OLD: one family figure; NEW: each size its own), and the moves the spine keys to the old key now. Prints 'SPINE CMP OK S605'."""
import argparse
import collections
import json
import re
import sqlite3
import sys

KEYED = {"sp_item": "k20", "sp_alias": "k20", "sp_sale_line": "k20", "sp_purchase_line": "k20", "sp_close": "k20", "sp_close_name": "k20",
         "sp_move": "k20", "sp_recon": "k20", "sp_check": "k20", "sp_finding": "k20"}
WHOLE = ("sp_export", "sp_item_fact", "sp_sale_bill", "sp_purchase_bill")


def K(n):
    return re.sub(r"\s+", " ", (n or "").strip())[:20].strip()


def ro(p):
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
    c.row_factory = sqlite3.Row
    return c


def rows(c, t):
    return collections.Counter(tuple(r) for r in c.execute("SELECT * FROM %s" % t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--finance-db", required=True)
    ap.add_argument("--rules", required=True, help="spine_rules.json (read only)")
    a = ap.parse_args()
    O, N, F = ro(a.old), ro(a.new), ro(a.finance_db)
    ren = {}
    for old, new in F.execute("SELECT old_name, new_name FROM marg_item_rename WHERE done_at IS NOT NULL"):
        if K(new) != K(old):
            ren[K(new)] = K(old)
    n = collections.Counter(ren.values())
    fam = collections.defaultdict(list)
    for nk, ok in sorted(ren.items()):
        if n[ok] > 1:
            fam[ok].append(nk)
    keys = set(fam) | {k for v in fam.values() for k in v}
    R = json.load(open(a.rules, encoding="utf-8"))
    ral = {x: v["to"] for x, v in (R.get("aliases") or {}).items()}
    rfam = R.get("families") or {}
    for k in list(keys):                                              # the key spine_build's Z reaches: the rules' alias, then the rules' family
        k2 = ral.get(k, k)
        keys |= {k2, rfam.get(k2, k2)}
    print("the families' keys (old, new, and the rules' family names they reach): %d" % len(keys))
    print("the families: %d (%d renames) -- %s" % (len(fam), sum(len(v) for v in fam.values()), "; ".join("%s: %d" % (k, len(v)) for k, v in sorted(fam.items()))))
    stop = []
    for t, kc in sorted(KEYED.items()):
        ro_, rn = rows(O, t), rows(N, t)
        ix = [d[1] for d in O.execute("PRAGMA table_info(%s)" % t)].index(kc)
        gone, added = ro_ - rn, rn - ro_
        outside = [r for r in list(gone) + list(added) if r[ix] not in keys]
        fam_d = sum(gone.values()) + sum(added.values()) - len(outside)
        print("  %-16s OLD %7d rows, NEW %7d rows; differing rows: %d under the families' keys, %d under any other key%s"
              % (t, sum(ro_.values()), sum(rn.values()), fam_d, len(outside), (" -- e.g. %s" % [tuple(x)[:6] for x in outside[:3]]) if outside else ""))
        if outside:
            stop.append("%s: %d row(s) moved under another key" % (t, len(outside)))
    for t in WHOLE:
        same = rows(O, t) == rows(N, t)
        print("  %-16s %s" % (t, "byte-equal OLD vs NEW" if same else "DIFFERS"))
        if not same:
            stop.append("%s differs" % t)
    mo = dict(O.execute("SELECT key, value FROM sp_meta").fetchall())
    mn = dict(N.execute("SELECT key, value FROM sp_meta").fetchall())
    md = sorted(k for k in set(mo) | set(mn) if mo.get(k) != mn.get(k))
    print("  sp_meta          differs only in %s (the build's moment and version)" % md)
    if set(md) - {"built", "build_version"}:
        stop.append("sp_meta differs in %s" % md)
    go = [(r["name"], r["blocking"], r["ok"]) for r in O.execute("SELECT name, blocking, ok FROM sp_gate ORDER BY n")]
    gn = [(r["name"], r["blocking"], r["ok"]) for r in N.execute("SELECT name, blocking, ok FROM sp_gate ORDER BY n")]
    nb = sum(1 for _n, b, _o in gn if b)
    nok = sum(1 for _n, b, o in gn if b and o)
    print("  sp_gate          OLD %d/%d, NEW %d/%d blocking checks green; the same checks: %s" % (
        sum(1 for _n, b, o in go if b and o), sum(1 for _n, b, _o in go if b), nok, nb, [x[0] for x in go] == [x[0] for x in gn]))
    if nok != nb:
        stop.append("the NEW gate is red: %s" % [x[0] for x in gn if x[1] and not x[2]])
    c5 = [x for x in gn if x[0].startswith("the 06-Sep count baseline")]
    c5o = [x for x in go if x[0].startswith("the 06-Sep count baseline")]
    print("  check 5          %s (OLD %s)" % (c5, c5o))
    if not c5 or not c5[0][2] or c5 != c5o:
        stop.append("check 5 (the 06-Sep baseline) is not green and equal")
    last = (N.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0] or "")
    print("\n  per family (the latest full closing %s): key -- Marg's closing / the spine's figure, OLD -> NEW" % last)
    for ok_, news in sorted(fam.items()):
        sp = N.execute("SELECT source FROM sp_alias WHERE kind='rename_family' AND alias=?", (news[0],)).fetchone()
        print("   %s  (%s)" % (ok_, sp[0] if sp else "no rename_family row"))
        for k in [ok_] + news:
            def fig(c):
                m = c.execute("SELECT as_on, units FROM sp_close WHERE k20=? AND as_on<=? ORDER BY as_on DESC LIMIT 1", (k, last)).fetchone()
                s = c.execute("SELECT ROUND(COALESCE(SUM(units),0),2) FROM sp_move WHERE k20=? AND date<=?", (k, last)).fetchone()[0]
                return "%s@%s / %s" % (m[1] if m else "-", m[0][5:] if m else "", s)
            mv = N.execute("SELECT kind, COUNT(*), ROUND(SUM(units),2) FROM sp_move WHERE k20=? GROUP BY kind ORDER BY kind", (k,)).fetchall()
            print("      %-22s %-22s -> %-22s NEW moves %s" % (k, fig(O), fig(N), [tuple(x) for x in mv]))
    if stop:
        print("SPINE CMP STOP S605: %s" % "; ".join(stop))
        return 3
    print("SPINE CMP OK S605: every row outside the %d families byte-equal; the NEW gate %d/%d; check 5 green and untouched" % (len(fam), nok, nb))
    return 0


if __name__ == "__main__":
    sys.exit(main())
