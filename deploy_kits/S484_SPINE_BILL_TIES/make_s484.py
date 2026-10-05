#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s484.py -- kit S484_SPINE_BILL_TIES (F-736; with F-734 / F-735 through make_s484_reader.py).

/root/finance/spine/spine_build.py is BUILT FROM THE LIVE BYTES (ce99bedf) by anchored edits at five sites: each anchor must occur
exactly once, else the build stops and nothing is written. Nothing here opens a database or the network.

    python3 -B make_s484.py --spine /root/finance/spine --out DIR        -> DIR/spine_build.py

  BUILD_VERSION   "S331.1" -> "S484.1" (sp_meta records the build)
  1.1  the order of bill-wise exports:      (stamp, number of bills, md5)
  1.2  the order of purchase-lines exports: (stamp, grouping == SUPPLIER, number of lines, md5)
  1.3  a bill number two suppliers share on one day, in a BILL-grouped sheet: when the whole sum settles on no single bill, the
       number's lines are cut, in sheet order, into runs whose money matches each bill -- tied only when exactly one cutting fits
  1.4  cut_shared_bill(lines, bills, tol), the helper 1.3 calls, above def build

The reader (marg_read.py) is built by make_s484_reader.py -- S483's make_s483.py, the same bytes under this kit's name.
"""
import argparse
import hashlib
import io
import os
import sys

KIT = "S484_SPINE_BILL_TIES"
FROM = "ce99bedf60194a84fe93455927a336e2"

HELPER = '''def cut_shared_bill(lines, bills, tol):
    """S484 (F-736). A BILL/ITEM WISE sheet prints the lines of every bill of one number on one day under that number, with no
    supplier. `lines` are that group's lines IN SHEET ORDER, `bills` the candidate bills of that number and day (two or more),
    `tol(bill)` the money tolerance in paise. The lines are cut into as many contiguous, non-empty runs as there are bills; a FIT
    is a cutting and an assignment of the bills to the runs in which every run's summed net_amount_p is within tol of its bill.
    Returns {index into lines: bill} when EXACTLY ONE fit exists (two fits that give every line the same bill are one fit);
    None when none fits, when more than one fits, or when the group is too large to enumerate honestly (more than 24 lines or
    more than 4 bills) -- the lines then stay tied to no bill and show in the gate's own line."""
    import itertools                                         # noqa: PLC0415 -- used here only
    n, k = len(lines), len(bills)
    if k < 2 or n < k or n > 24 or k > 4:
        return None
    pre = [0]
    for ln in lines:
        pre.append(pre[-1] + ln["net_amount_p"])
    fits = set()
    for cuts in itertools.combinations(range(1, n), k - 1):
        edge = (0,) + cuts + (n,)
        sums = [pre[edge[j + 1]] - pre[edge[j]] for j in range(k)]
        for order in itertools.permutations(range(k)):
            if all(abs(abs(bills[order[j]]["amount_p"]) - sums[j]) <= tol(bills[order[j]]) for j in range(k)):
                fits.add(tuple(order[j] for j in range(k) for _ in range(edge[j + 1] - edge[j])))
                if len(fits) > 1:
                    return None
    if len(fits) != 1:
        return None
    return {i: bills[b] for i, b in enumerate(next(iter(fits)))}


'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(name, src, pairs):
    """Anchored edits: every OLD must occur exactly once in what the edits before it left."""
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        if n != 1:
            raise SystemExit("!! %s: anchor %d occurs %d times, not once -- nothing built (%r)" % (name, i, n, old[:70]))
        src = src.replace(old, new)
    return src


def build_spine_build(src):
    return edit("spine_build.py", src, [
        # ---- the build's own version, so sp_meta records which rules made a spine
        ('BUILD_VERSION = "S331.1"\n',
         'BUILD_VERSION = "S484.1"\n'),
        # ---- 1.4 the helper, above def build
        ('def build(readings, rules, acceptance=False, finance_db=None, log=print):\n',
         HELPER + 'def build(readings, rules, acceptance=False, finance_db=None, log=print):\n'),
        # ---- 1.1 bill-wise exports: at an equal second the fuller print is the later; the order is stated and total, never md5 alone
        ('    BW = sorted([r for r in fam_of("PURCHASE_BILLWISE") if r["_accepted"]], key=lambda r: r["stamp"])\n',
         '    BW = sorted([r for r in fam_of("PURCHASE_BILLWISE") if r["_accepted"]],\n'
         '                key=lambda r: (r["stamp"], len(r["data"]["bills"]), r["md5"]))   # S484 (F-736): equal stamps get a stated order\n'),
        # ---- 1.2 purchase-lines exports: at an equal second a SUPPLIER-grouped sheet is the later (it names the supplier), then the fuller
        ('    PL = sorted([r for r in ev if r.get("family") in ("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE")], key=lambda r: r["stamp"])\n',
         '    PL = sorted([r for r in ev if r.get("family") in ("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE")],\n'
         '                key=lambda r: (r["stamp"], r["data"].get("grouping") == "SUPPLIER", len(r["data"]["lines"]), r["md5"]))   # S484 (F-736)\n'),
        # ---- 1.3 the shared bill number in a BILL-grouped sheet
        ('        # BILL grouping: a bill number two suppliers share on one day is settled by the money of its own lines\n'
         '        grp_net = collections.defaultdict(int)\n'
         '        for ln in r["data"]["lines"]:\n'
         '            if r["data"]["grouping"] == "BILL":\n'
         '                grp_net[(ubill(ln["bill"]), ln["date"])] += ln["net_amount_p"]\n'
         '        for ln in r["data"]["lines"]:\n'
         '            if r["data"]["grouping"] == "SUPPLIER":\n'
         '                cands = [b for b in by_supbill_u.get((supnorm(ln["supplier"]), ubill(ln["bill"])), [])\n'
         '                         if r["data"]["date_from"] <= b["date"] <= r["data"]["date_to"]]\n'
         '            else:\n'
         '                cands = by_billdate_u.get((ubill(ln["bill"]), ln["date"]), [])\n'
         '                if len(cands) > 1:\n'
         '                    net = grp_net[(ubill(ln["bill"]), ln["date"])]\n'
         '                    cands = [b for b in cands if abs(abs(b["amount_p"]) - net) <= 100 + 0.002 * abs(b["amount_p"])]\n'
         '            if len(cands) != 1:\n'
         '                undated.append((r["name"], ln["bill"], ln["name"], len(cands), whole_auth))\n'
         '                continue\n',
         '        # BILL grouping: a bill number two suppliers share on one day is settled by the money of its own lines\n'
         '        grp_net = collections.defaultdict(int)\n'
         '        grp_ix = collections.defaultdict(list)\n'
         '        for li, ln in enumerate(r["data"]["lines"]):\n'
         '            if r["data"]["grouping"] == "BILL":\n'
         '                grp_net[(ubill(ln["bill"]), ln["date"])] += ln["net_amount_p"]\n'
         '                grp_ix[(ubill(ln["bill"]), ln["date"])].append(li)\n'
         '        # S484 (F-736): when the whole sum of a shared number settles on no single bill (both bills\' lines are printed under it),\n'
         '        # its lines are cut, in sheet order, into runs whose money matches each bill -- once per group, before the loop. The cutting\n'
         '        # starts from EVERY bill of that number and day, and ties a line only when exactly one cutting fits (cut_shared_bill).\n'
         '        cut = {}\n'
         '        for gk, ix in grp_ix.items():\n'
         '            pre = by_billdate_u.get(gk, [])\n'
         '            if len(pre) > 1 and len([b for b in pre if abs(abs(b["amount_p"]) - grp_net[gk]) <= 100 + 0.002 * abs(b["amount_p"])]) != 1:\n'
         '                fit = cut_shared_bill([r["data"]["lines"][i] for i in ix], pre, lambda b: 100 + 0.002 * abs(b["amount_p"]))\n'
         '                for j, b in (fit or {}).items():\n'
         '                    cut[ix[j]] = b\n'
         '        for li, ln in enumerate(r["data"]["lines"]):\n'
         '            if r["data"]["grouping"] == "SUPPLIER":\n'
         '                cands = [b for b in by_supbill_u.get((supnorm(ln["supplier"]), ubill(ln["bill"])), [])\n'
         '                         if r["data"]["date_from"] <= b["date"] <= r["data"]["date_to"]]\n'
         '            else:\n'
         '                cands = by_billdate_u.get((ubill(ln["bill"]), ln["date"]), [])\n'
         '                if len(cands) > 1:\n'
         '                    pre_n = len(cands)\n'
         '                    net = grp_net[(ubill(ln["bill"]), ln["date"])]\n'
         '                    cands = [b for b in cands if abs(abs(b["amount_p"]) - net) <= 100 + 0.002 * abs(b["amount_p"])]\n'
         '                    if len(cands) != 1:\n'
         '                        if li in cut:\n'
         '                            cands = [cut[li]]                # S484: its run\'s bill\n'
         '                        else:                                # no cutting fits, or more than one: untied, with the count of its bills\n'
         '                            undated.append((r["name"], ln["bill"], ln["name"], pre_n, whole_auth))\n'
         '                            continue\n'
         '            if len(cands) != 1:\n'
         '                undated.append((r["name"], ln["bill"], ln["name"], len(cands), whole_auth))\n'
         '                continue\n'),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", default="/root/finance/spine")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with io.open(os.path.join(a.spine, "spine_build.py"), "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM:
        raise SystemExit("!! spine_build.py is %s, not its FROM pin %s -- someone changed it since the brief; nothing built" % (md5(raw), FROM))
    out = build_spine_build(raw.decode("utf-8")).encode("utf-8")
    os.makedirs(a.out, exist_ok=True)
    with io.open(os.path.join(a.out, "spine_build.py"), "wb") as fh:
        fh.write(out)
    print("built spine_build.py  %s -> %s  (%d bytes)" % (FROM[:8], md5(out)[:8], len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
