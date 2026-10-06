#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rejudge_s488.py -- kit S488_DATES_AND_WAITS (A.10, F-754): the once-only re-judge of s454_shelf_gap, and the two measures the brief asks.

    python3 -B rejudge_s488.py rejudge --db DB --fin DIR [--dry]    the re-judge (writes s454_shelf_gap unless --dry); idempotent
    python3 -B rejudge_s488.py figures --db DB --fin DIR            shelf_figure.figures() of every item with a filed voucher (JSON)
    python3 -B rejudge_s488.py stay    --db DB --fin DIR            of the first-flagged rows that stay: how many the spine NOW explains

  --fin is a folder holding shelf_figure.py and stock_watch.py (the NEW ones for rejudge / stay; OLD or NEW for figures); SPINE_DB in the
  environment names the spine copy. The rows of each closing are read into memory WITH THEIR why AS IT STANDS BEFORE THE RUN:
    pass 1  a row first-flagged at its own closing (flagged = 1, why begins 'Marg moved' and names its own as_on): its voucher figure is
            worked out again with the new filed_vouchers over (previous closing, this closing]; when |marg_move - voucher| is under
            stock.gap_min_packs x (pack if pack > 1 else 1) it is cleared: flagged 0, voucher = the new figure,
            why = 'explained by the vouchers filed (re-judged S488)'.
    pass 2  in closing order: a flagged row whose ORIGINAL why equals the ORIGINAL why of the same item at the previous closing, where
            that row was cleared in this run, is cleared the same way (its own window's voucher figure).
  Nothing else in the table is written; a second run changes nothing. Item names (medicines) and figures only -- no person, no number.
"""
import argparse
import json
import os
import sqlite3
import sys

TAG = "S488JSON "
WHY = "explained by the vouchers filed (re-judged S488)"


def mods(fin):
    sys.path.insert(0, os.path.abspath(fin))
    import shelf_figure as SF                                           # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    assert SF.__file__.startswith(os.path.abspath(fin)) and SW.__file__.startswith(os.path.abspath(fin)), (SF.__file__, SW.__file__)
    return SF, SW


def first_day(SF, con):
    """The first filed voucher's day (ISO): the newest row of each batch, with a voucher number."""
    state = {}
    for cid, rno, kind, bno, vno, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                         "FROM stock_voucher_entered ORDER BY id"):
        state[(cid, rno, kind, bno)] = (vno, eon, at)
    days = [SF._s488_entry_day(eon, at) for (vno, eon, at) in state.values() if str(vno or "").strip()]
    days = [d for d in days if d]
    return min(days) if days else None


def filed_items(con):
    """Every item of a batch whose newest entry carries a voucher number."""
    state = {}
    for cid, rno, kind, bno, vno in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no FROM stock_voucher_entered ORDER BY id"):
        state[(cid, rno, kind, bno)] = vno
    keys = {k for k, v in state.items() if str(v or "").strip()}
    return sorted({r[4] for r in con.execute("SELECT count_id, round_no, kind, batch_no, item FROM stock_voucher_line") if tuple(r[:4]) in keys})


def gap_min(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='stock.gap_min_packs'").fetchone()
        return float(str(r[0]).strip()) if r and str(r[0] or "").strip() else 1.0
    except (sqlite3.Error, ValueError):
        return 1.0


def rejudge(a):
    SF, _SW = mods(a.fin)
    con = sqlite3.connect(a.db, timeout=60)
    con.execute(SF.GAP_DDL)
    fd = first_day(SF, con)
    closings = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM s454_shelf_gap ORDER BY as_on")]
    prev = {c: (closings[i - 1] if i else None) for i, c in enumerate(closings)}
    target = [c for c in closings if fd and c >= fd]
    rows = {}
    for c in target:
        rows[c] = {r[0]: dict(item=r[0], flagged=int(r[1] or 0), why=r[2] or "", marg_move=r[3], pack=int(r[4] or 1)) for r in
                   con.execute("SELECT item, flagged, why, marg_move, pack FROM s454_shelf_gap WHERE as_on=?", (c,))}
    mins = gap_min(con)
    before = {c: sum(1 for r in rows[c].values() if r["flagged"]) for c in target}
    cleared, writes = {}, []
    vitems = {}
    for c in target:                                                    # pass 1
        p = prev[c]
        if not p:
            continue
        vitems[c] = sum(1 for it in rows[c] if SF.filed_vouchers(con, it, p, c))
        for it, r in rows[c].items():
            if not (r["flagged"] == 1 and r["why"].startswith("Marg moved") and (" on %s" % c) in r["why"]) or r["marg_move"] is None:
                continue
            v = SF.filed_vouchers(con, it, p, c)
            thr = mins * (r["pack"] if r["pack"] > 1 else 1)
            if abs(float(r["marg_move"]) - v) < thr:
                cleared[(c, it)] = v
                writes.append((c, it, v, 1))
    for c in target:                                                    # pass 2, in closing order
        p = prev[c]
        if not p or p not in rows:
            continue
        for it, r in rows[c].items():
            if r["flagged"] != 1 or (c, it) in cleared or (p, it) not in cleared:
                continue
            if r["why"] == (rows[p].get(it) or {}).get("why"):
                v = SF.filed_vouchers(con, it, p, c)
                cleared[(c, it)] = v
                writes.append((c, it, v, 2))
    n = 0
    if not a.dry:
        for c, it, v, _ps in writes:
            n += con.execute("UPDATE s454_shelf_gap SET flagged=0, voucher=?, why=? WHERE as_on=? AND item=? AND flagged=1", (v, WHY, c, it)).rowcount
        con.commit()
    after = {c: con.execute("SELECT COUNT(*) FROM s454_shelf_gap WHERE as_on=? AND flagged=1", (c,)).fetchone()[0] for c in target}
    out = dict(first_day=fd, closings=target, flagged_before=before, flagged_after=after, items_with_voucher=vitems,
               cleared={c: sorted(it for (cc, it) in cleared if cc == c) for c in target},
               by_pass={c: [sum(1 for w in writes if w[0] == c and w[3] == 1), sum(1 for w in writes if w[0] == c and w[3] == 2)] for c in target},
               written=n, dry=bool(a.dry), gap_min_packs=mins)
    con.close()
    print(TAG + json.dumps(out, sort_keys=True))
    for c in target:
        print("closing %s: %d items carry a filed voucher in (%s, %s]; flagged %d -> %s (pass 1 cleared %d, pass 2 %d)%s"
              % (c, vitems.get(c, 0), prev[c], c, before[c], after[c] if not a.dry else before[c] - len(out["cleared"][c]),
                 out["by_pass"][c][0], out["by_pass"][c][1], " [dry]" if a.dry else ""))
    return 0


def figures(a):
    SF, SW = mods(a.fin)
    con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
    items = filed_items(con)
    F = SF.figures(con, items=items)
    out = {k: dict(shelf=v.get("shelf"), boundary=v.get("boundary"), named=v.get("named"), base_day=v.get("base_day")) for k, v in F.items()}
    con.close()
    print(TAG + json.dumps(out, sort_keys=True, default=str))
    return 0


def stay(a):
    """Of the rows first-flagged at their own closing that are still flagged: how many the spine explains NOW (sales / purchases that
    reached it after the closing was recorded). Read only; nothing is changed."""
    SF, SW = mods(a.fin)
    con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
    sp = SW.Spine()
    mins = gap_min(con)
    closings = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM s454_shelf_gap ORDER BY as_on")]
    out = {}
    for i, c in enumerate(closings):
        p = closings[i - 1] if i else None
        if not p or not sp.ok:
            continue
        pm = {r[0]: r[1] for r in con.execute("SELECT item, marg FROM s454_shelf_gap WHERE as_on=?", (p,))}
        st = dict(stay=0, explained_now=0, moves=[], explained=[], stored=[])
        for it, marg, why, pack, mm in con.execute("SELECT item, marg, why, pack, marg_move FROM s454_shelf_gap WHERE as_on=? AND flagged=1", (c,)):
            if not (str(why or "").startswith("Marg moved") and (" on %s" % c) in str(why)) or pm.get(it) is None:
                continue
            st["stay"] += 1
            if mm is not None:
                st["stored"].append(float(mm))
            sold, ret, bought = SF.movements(sp, it, p, c, incl_from=False)
            move = float(marg) - float(pm[it]) - (bought - sold + ret)
            v = SF.filed_vouchers(con, it, p, c)
            st["moves"].append(round(move - v, 1))
            if abs(move - v) < mins * (int(pack or 1) if int(pack or 1) > 1 else 1):
                st["explained_now"] += 1
                st["explained"].append(it)
        st["neg"] = sum(1 for m in st["moves"] if m < 0)
        st["range_now"] = [min(st["moves"]), max(st["moves"])] if st["moves"] else None
        st["stored_range"] = [min(st["stored"]), max(st["stored"])] if st["stored"] else None
        st["stored_neg"] = sum(1 for m in st["stored"] if m < 0)
        st.pop("moves")
        st.pop("stored")
        out[c] = st
    con.close()
    print(TAG + json.dumps(out, sort_keys=True))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("rejudge", "figures", "stay"))
    ap.add_argument("--db", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    return {"rejudge": rejudge, "figures": figures, "stay": stay}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
