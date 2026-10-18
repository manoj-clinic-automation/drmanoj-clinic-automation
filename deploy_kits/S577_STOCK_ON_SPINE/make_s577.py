#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s577.py -- kit S577_STOCK_ON_SPINE: the builder. Anchored edits on the LIVE bytes of five files, plus the new stock_figure.py copied
beside them.

    python3 -B make_s577.py --finance /root/finance --kit <this kit folder> --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes DIR/<file> for stock_app.py, shelf_figure.py, stock_watch.py, loss_piles.py, spine_build.py, selftest_spine.py and
DIR/stock_figure.py (the kit's copy, byte for byte); prints each md5 -- the installer compares them with PINS.sh.
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "050587dfb5951da65f95937615ddf144",
    "shelf_figure.py": "183c70fabb64ed1e5a43c645a225c560",
    "stock_watch.py": "0e6a42c4c7ae51eb8f8a0869fce2d101",
    "loss_piles.py": "81ae481e4480a12fead3016515037214",
    "spine/spine_build.py": "5d8b1f94d80189c16b2ee5b1e093429c",
    "spine/selftest_spine.py": "fc63d2c683a1970c58f60502302187a9",
}
NEW = "stock_figure.py"

# =============================================================================================================== spine_build.py
SB = []
SB.append(("B1 schema: sp_close_name", '''CREATE TABLE sp_close (as_on TEXT, k20 TEXT, units REAL, source_md5 TEXT, PRIMARY KEY (as_on, k20));
''', '''CREATE TABLE sp_close (as_on TEXT, k20 TEXT, units REAL, source_md5 TEXT, PRIMARY KEY (as_on, k20));
CREATE TABLE sp_close_name (md5 TEXT, name TEXT, packing TEXT, k20 TEXT, units REAL, PRIMARY KEY (md5, name, packing));
'''))
SB.append(("B2 build version", '''BUILD_VERSION = "S524.1"
''', '''BUILD_VERSION = "S577.1"
'''))
SB.append(("B3 build(): every accepted full capture", '''        if full:
            closings[r["data"]["as_on"]] = r                 # the latest capture of a date wins
    rej_c = ''', '''        if full:
            closings[r["data"]["as_on"]] = r                 # the latest capture of a date wins
    captures = [r for r in CL if r.get("_full")]             # S577: EVERY accepted full capture, kept by printed name (sp_close_name); the gate above is untouched
    rej_c = '''))
SB.append(("B4 build(): captures returned", '''                facts=facts, whole=whole, Z=Z, checkable=checkable, pending=pending, alias=alias, rename_alias=ren)
''', '''                facts=facts, whole=whole, Z=Z, checkable=checkable, pending=pending, alias=alias, rename_alias=ren, captures=captures)
'''))
SB.append(("B5 write(): sp_close_name", '''        con.executemany("INSERT INTO sp_close VALUES (?,?,?,?)", [(d, k, u, r["md5"]) for k, u in agg.items()])
    con.executemany("INSERT INTO sp_move VALUES (?,?,?,?,?)", B["moves"])
''', '''        con.executemany("INSERT INTO sp_close VALUES (?,?,?,?)", [(d, k, u, r["md5"]) for k, u in agg.items()])
    for r in B.get("captures") or []:                        # S577: every accepted full capture BY PRINTED NAME and packing, as Marg printed them;
        agn = collections.defaultdict(float)                 # a name printed twice with one packing inside one capture is summed; k20 = Z(name).
        for i in r["data"]["items"]:                         # The capture's printed day and stamp are sp_export.as_on / stamp (one copy, R2-C17).
            if i.get("name"):
                agn[(i["name"], i.get("packing") or "")] += i["units"]
        con.executemany("INSERT INTO sp_close_name VALUES (?,?,?,?,?)", [(r["md5"], n, p, B["Z"](n), u) for (n, p), u in agn.items()])
    con.executemany("INSERT INTO sp_move VALUES (?,?,?,?,?)", B["moves"])
'''))

# =============================================================================================================== selftest_spine.py
ST = []
ST.append(("T1 the S577 check", '''if __name__ == "__main__":
    test_readers()
    test_evidence()
    test_builder()
    test_s470()
    print("SELFTEST OK  %d checks" % N)
''', '''# ======================================================================= S577: every capture by name (sp_close_name)
def test_s577():
    tmp = tempfile.mkdtemp()
    try:
        d, rp = store(tmp, opening_units=36, recon=True)             # 36 + 10 - 25 - 1 = 20 = Marg (as test_builder)
        it = lambda q, name="ALPHA TAB": dict(serial=1, name=name, packing="1*10", qty_raw=q, units=M.qty_units(q, "1*10"), unit="STRI", plain=False)   # noqa: E731
        pad = [dict(serial=2, name="X%d" % i, packing="1*1", qty_raw="-", units=0.0, unit="ITEM", plain=False) for i in range(300)]
        r2 = rec("close2.XLS", "STOCK_CLOSING", dict(as_on="2026-04-05", items=[it("1:0"), it("1:0")] + pad, printed_total=20, lines_total=20), stamp="20260405-233000")
        json.dump(r2, open(os.path.join(d, r2["md5"] + ".json"), "w"))
        rules = json.load(open(rp))
        Bd = B.build(B.load_readings(d), rules, acceptance=True, finance_db=fake_finance(tmp))
        out = os.path.join(tmp, "s577.db")
        B.write(out, Bd, rules, d)
        c = sqlite3.connect(out)
        md5s = [r[0] for r in c.execute("SELECT DISTINCT n.md5 FROM sp_close_name n JOIN sp_export e ON e.md5=n.md5 WHERE e.as_on='2026-04-05'")]
        check("S577 sp_close_name: two captures of one printed day give two md5s", len(md5s) == 2)
        check("S577 sp_close keeps the later capture of the day (the gate's own rule, unchanged)",
              c.execute("SELECT source_md5 FROM sp_close WHERE as_on='2026-04-05' AND k20='ALPHA TAB'").fetchone()[0] == r2["md5"])
        check("S577 a name printed twice in one capture is summed into one row",
              c.execute("SELECT COUNT(*), SUM(units) FROM sp_close_name WHERE md5=? AND name='ALPHA TAB'", (r2["md5"],)).fetchone() == (1, 20.0))
        check("S577 the earlier capture of the day keeps its own figure by name",
              c.execute("SELECT units FROM sp_close_name WHERE md5<>? AND name='ALPHA TAB' AND md5 IN (%s)" % ",".join("?" * len(md5s)), [r2["md5"]] + md5s).fetchone()[0] == 20.0)
        check("S577 the gate is unchanged by the new table", Bd["G"].passed)
        c.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_readers()
    test_evidence()
    test_builder()
    test_s470()
    test_s577()
    print("SELFTEST OK  %d checks" % N)
'''))

# =============================================================================================================== shelf_figure.py
SH = []
SH.append(("H1 header", '''#    * an item with no count keeps Marg's figure (named 'no_count'); a result below zero is taken as zero (named 'below_zero').
#  Base units (tabs / pieces), the pack size beside. One function, in one place: figures(). Read only.
# =============================================================================
import datetime as dt''', '''#    * an item with no count has NO shelf figure (shelf=None, named 'no_count'; S577, charter 3 -- never Marg's); below zero is zero ('below_zero').
#  Base units (tabs / pieces), the pack size beside. Read only.
#  S577_STOCK_ON_SPINE (18-Oct-2026, rung 4b): the figures come from stock_figure.py -- THE one stock function (Marg's figure and the shelf
#  figure, each on the closing it stands on, by printed name over the spine's own closing captures: sp_close_name). latest_snapshot and the
#  stock_feed capture lookups of S524 are retired; the shelf-gap sets are judged on usable captures only and written to
#  s577_shelf_gap (one set per end_day, with the capture's md5); the S454 gap table stays as a record, read by nothing.
# =============================================================================
import datetime as dt'''))
SH.append(("H2 version", '''VERSION = "1.0"
KIT = "S454_BILL_REGISTER"
''', '''VERSION = "2.0"
KIT = "S577_STOCK_ON_SPINE"                                    # v1.0 was S454_BILL_REGISTER (part 3)
'''))
SH.append(("H3 latest_snapshot -> the stock_figure door", '''def latest_snapshot(con):
    """(as_on iso, {item: dict(qty, packing, pack_size)}) -- Marg's newest closing stock."""
    if not _has(con, "stock_snapshot"):
        return None, {}
    ds = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    if not ds:
        return None, {}
    as_on = max(ds, key=lambda d: dmy_iso(d))
    return dmy_iso(as_on), {r[0]: dict(qty=int(r[1] or 0), packing=r[2] or "", pack_size=max(1, int(r[3] or 1)))
                            for r in con.execute("SELECT item, qty, packing, pack_size FROM stock_snapshot WHERE as_on=?", (as_on,))}


def count_family(con):
    """{item: dict(qty, day iso, at, count_id, fixed)} -- the newest full count's row of every item: the count's own figure, its parts',
    and the desk's corrections (stock_shelf_fix), the latest winning."""
    out = {}
    if not _has(con, "stock_count_item"):
        return out
    try:
        parts = {}
        if _has(con, "stock_count_part"):
            parts = {int(r[0]): int(r[1]) for r in con.execute("SELECT count_id, part_of FROM stock_count_part")}
        counts = [dict(id=int(r[0]), day=dmy_iso(r[1]), at=str(r[2] or "")) for r in
                  con.execute("SELECT id, marg_as_on, COALESCE(submitted_at, started_at) FROM stock_count WHERE status='submitted' ORDER BY id")]
    except sqlite3.Error:
        return out
    for c in counts:
        for item, qty, at, mq in con.execute("SELECT item, counted_qty, at, marg_qty FROM stock_count_item WHERE count_id=? AND counted_qty IS NOT NULL", (c["id"],)):
            prev = out.get(item)
            stamp = (c["day"], str(at or c["at"]))
            if prev is None or stamp >= (prev["day"], prev["at"]):
                out[item] = dict(qty=float(qty), day=c["day"], at=str(at or c["at"]), count_id=parts.get(c["id"], c["id"]), fixed=False,
                                 marg0=(float(mq) if mq is not None else None))
    if _has(con, "stock_shelf_fix"):
        for item, qty, at, cid in con.execute("SELECT item, qty, at, count_id FROM stock_shelf_fix ORDER BY at, id"):
            e = out.get(item)
            if e is not None and qty is not None and int(cid or 0) in (e["count_id"], 0):
                e.update(qty=float(qty), fixed=True, fixed_at=str(at))
    return out


def points(con):
    """{item_norm: dict(qty, at, source, item)} -- the newest stock point that is not the full count's own copy (spot, darpan, sales_test,
    receipt), settled or provisional."""
    out = {}
    if not _has(con, "stock_point"):
        return out
    for nm, item, at, qty, src in con.execute("SELECT item_norm, item, at, qty_units, source FROM stock_point WHERE source<>? ORDER BY at, id", (FULL,)):
        out[nm] = dict(qty=float(qty or 0), at=str(at), source=src, item=item)
    return out


def movements(sp, item, d_from, d_to, incl_from=True):
    """(sold, returned, bought) units of the item's spine key between two days. A credit note (bill CN...) is a return: the spine keeps its
    units positive, so it is told apart by its bill, as the orthotic shelf does. Purchases net of purchase returns; the count day's sales
    in (incl_from), its purchases out."""
    op = ">=" if incl_from else ">"
    k = sp.key(item)
''', '''def _sf():
    import stock_figure                                       # noqa: PLC0415 -- beside this file: THE one stock function (S577); it imports this file lazily
    return stock_figure


def count_family(con, ctx=None):
    """{item: dict(qty, day iso, at, count_id, fixed, marg0)} -- the newest full count's row of every item with the desk's corrections laid
    over (S577: stock_figure.count_family -- the one read of the count tables; a retired fix, count_id < 0, is never read)."""
    return _sf().count_family(con, ctx)


def points(con, ctx=None):
    """{item_norm: dict(qty, at, source, item)} -- the newest stock point that is not the full count's own copy and not superseded
    (S577: stock_figure.points -- the one change: a superseded point is excluded)."""
    return _sf().points(con, ctx)


def movements(sp, item, d_from, d_to, incl_from=True, ctx=None):
    """(sold, returned, bought) units of the item's spine key between two days. A credit note (bill CN...) is a return: the spine keeps its
    units positive, so it is told apart by its bill, as the orthotic shelf does. Purchases net of purchase returns; the count day's sales
    in (incl_from), its purchases out. S577: the key is stock_figure.key_of (charter 12), never a bare clip."""
    op = ">=" if incl_from else ">"
    k = _sf().key_of(sp, item, ctx)
'''))
SH.append(("H4 boundary_purchases keys and vouchers through the one rule", '''def boundary_purchases(con, sp, item, base_day, marg0, marg_now, marg_as_on, pack):
    """S454 9.1, the boundary: a purchase dated on (or up to BOUND_DAYS before) the count day that Marg did not carry yet at the count -- the bill
    entered after the count with an earlier date (PANSPED L: counted 0 at 14:41 on 06-09, its bill of 06-09 entered later; SHELCAL XT: a bill
    of 05-09). Marg's own figure at the count (marg0) tells: what Marg gained since the count beyond its sales, returns, later purchases and
    the count's vouchers filed. Such purchases are taken newest first while they fit that gain (one pack's tolerance). Units."""
    if marg0 is None or marg_now is None or not marg_as_on or not sp.ok or marg_as_on < base_day:
        return 0.0
    sold, ret, bought = movements(sp, item, base_day, marg_as_on)
    gain = float(marg_now) - (float(marg0) - sold + ret + bought) - filed_vouchers(con, item, base_day, marg_as_on)
    tol = float(max(1, pack))
    if gain < tol:
        return 0.0
    d0 = (dt.date.fromisoformat(base_day) - dt.timedelta(days=BOUND_DAYS)).isoformat()
    took = 0.0
    for r in sp.q("SELECT date, units FROM sp_move WHERE k20=? AND kind='PURCHASE' AND units>0 AND date>=? AND date<=? ORDER BY date DESC", sp.key(item), d0, base_day):
''', '''def boundary_purchases(con, sp, item, base_day, marg0, marg_now, marg_as_on, pack, ctx=None):
    """S454 9.1, the boundary: a purchase dated on (or up to BOUND_DAYS before) the count day that Marg did not carry yet at the count -- the bill
    entered after the count with an earlier date (PANSPED L: counted 0 at 14:41 on 06-09, its bill of 06-09 entered later; SHELCAL XT: a bill
    of 05-09). Marg's own figure at the count (marg0) tells: what Marg gained since the count beyond its sales, returns, later purchases and
    the count's vouchers filed. Such purchases are taken newest first while they fit that gain (one pack's tolerance). Units.
    S577: marg_now / marg_as_on come from stock_figure.closing (the newest usable capture); the key is key_of."""
    if marg0 is None or marg_now is None or not marg_as_on or not sp.ok or marg_as_on < base_day:
        return 0.0
    sold, ret, bought = movements(sp, item, base_day, marg_as_on, ctx=ctx)
    gain = float(marg_now) - (float(marg0) - sold + ret + bought) - filed_vouchers(con, item, base_day, marg_as_on, sp=sp, ctx=ctx)
    tol = float(max(1, pack))
    if gain < tol:
        return 0.0
    d0 = (dt.date.fromisoformat(base_day) - dt.timedelta(days=BOUND_DAYS)).isoformat()
    took = 0.0
    for r in sp.q("SELECT date, units FROM sp_move WHERE k20=? AND kind='PURCHASE' AND units>0 AND date>=? AND date<=? ORDER BY date DESC",
                  _sf().key_of(sp, item, ctx), d0, base_day):
'''))
SH.append(("H5 scan_arrivals keys by key_of", '''def scan_arrivals(con, sp, item, since_iso):
    """Units of orders that arrived by a bill's scan (S454 4.4) whose lines Marg has not answered and the spine does not carry."""
    if not _has(con, "order_scan_tie"):
        return 0.0
    sw = _sw()
    out = 0.0
    keys = {sw.pad_norm(item[:27]), sw.pad_norm(item)}
''', '''def scan_arrivals(con, sp, item, since_iso, ctx=None):
    """Units of orders that arrived by a bill's scan (S454 4.4) whose lines Marg has not answered and the spine does not carry (S577: the
    spine keyed by stock_figure.key_of). Seen, not touched (charter 12): the order lines are still matched by pad_norm(name[:27])."""
    if not _has(con, "order_scan_tie"):
        return 0.0
    sw = _sw()
    out = 0.0
    keys = {sw.pad_norm(item[:27]), sw.pad_norm(item)}
'''))
SH.append(("H6 scan_arrivals the spine look", '''        if sp.ok:
            n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", sp.key(item), sw.supkey(vendor), str(created)[:10])
            if n and n[0]["n"]:
                continue
        out += float(packs or 0) * float(size or 1)
    return out
''', '''        if sp.ok:
            n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", _sf().key_of(sp, item, ctx), sw.supkey(vendor), str(created)[:10])
            if n and n[0]["n"]:
                continue
        out += float(packs or 0) * float(size or 1)
    return out
'''))
SH.append(("H7 figures from stock_figure", '''def figures(con, sp=None, items=None, upto=None):
    """{item: dict(item, shelf, marg, pack_size, packing, base, base_kind, base_day, base_at, sold, bought, arrived, approx, named, key)}.
    items: the names to figure (default: Marg's newest closing plus the count's items). upto: the last day of movements (default today)."""
    sw = _sw()
    sp = sp or sw.Spine()
    t = (upto or today()).isoformat() if not isinstance(upto, str) else upto
    as_on, snap = latest_snapshot(con)
    fam = count_family(con)
    pts = points(con)
    names = list(items) if items is not None else sorted(set(snap) | set(fam))
    rows = {}
    for nm in names:
        s = snap.get(nm) or {}
        info = sw.item_info(con, sp, nm) if not s else dict(pack=s["pack_size"], packing=s["packing"])
        base, kind, day, at, marg0 = None, None, None, None, None
        f = fam.get(nm)
        if f:
            base, kind, day, at, marg0 = f["qty"], "count", f["day"], f["at"], f.get("marg0")
        p = pts.get(sw.norm_name(nm))
        if p and (day is None or p["at"][:10] > day or (p["at"][:10] == day and p["at"] > (at or ""))):
            base, kind, day, at, marg0 = p["qty"], p["source"], p["at"][:10], p["at"], None
        rows[nm] = dict(item=nm, key=(sp.key(nm) if sp.ok else nm[:20]), marg=(s.get("qty") if s else None), marg_as_on=as_on,
                        pack_size=int(s.get("pack_size") or info.get("pack") or 1), packing=s.get("packing") or info.get("packing") or "",
                        base=base, base_kind=kind, base_day=day, base_at=at, sold=0.0, returned=0.0, bought=0.0, arrived=0.0, approx=False, named=None, shelf=None,
                        marg0=marg0, boundary=0.0)
    # the families: items that share one spine key share its movements, split by their counted share
    by_key = {}
    for r in rows.values():
        by_key.setdefault(r["key"], []).append(r)
    for key, members in by_key.items():
        counted = [m for m in members if m["base"] is not None]
        if not counted or not sp.ok:
            for m in members:
                m["shelf"] = m["marg"]
                m["named"] = "no_count" if m["base"] is None else "no_spine"
            continue
        day = min(m["base_day"] for m in counted)
        sold, ret, bought = movements(sp, members[0]["item"], day, t)
        tot = sum(max(0.0, m["base"]) for m in counted)
        n = len(counted)
        for m in counted:
            share = (max(0.0, m["base"]) / tot) if tot > 0 else 1.0 / n
            arr = sum(a["units"] for a in sw._arrivals(con, m["item"], m["base_day"], sp) if not a["in_spine"]) + scan_arrivals(con, sp, m["item"], m["base_day"])
            if n > 1 and len({x["base_day"] for x in counted}) > 1:
                # different base days inside one key: each member's own window, pooled sales split by share
                s2, r2, b2 = movements(sp, m["item"], m["base_day"], t)
                m["sold"], m["returned"], m["bought"] = round(share * s2, 2), round(share * r2, 2), round(share * b2, 2)
            else:
                m["sold"], m["returned"], m["bought"] = round(share * sold, 2), round(share * ret, 2), round(share * bought, 2)
            m["arrived"] = arr
            if n == 1 and m["base_kind"] == "count":                # S454 9.1: a bill dated before the count, entered after it
                m["boundary"] = boundary_purchases(con, sp, m["item"], m["base_day"], m["marg0"], m["marg"], as_on, m["pack_size"])
            v = m["base"] - m["sold"] + m["returned"] + m["bought"] + m["boundary"] + arr
            m["approx"] = n > 1
            if v < 0:
                m["named"], v = "below_zero", 0.0
            m["shelf"] = int(round(v))
        for m in members:
            if m["base"] is None:
                m["shelf"], m["named"] = m["marg"], "no_count"
    return rows
''', '''def figures(con, sp=None, items=None, upto=None, ctx=None):
    """{item: dict(item, key, shelf, marg, marg_as_on, pack_size, packing, pack_src, base, base_kind, base_day, base_at, sold, returned,
    bought, boundary, arrived, approx, named, marg0, capture)} -- S577: both figures from stock_figure.figures, kept apart. marg =
    stock_figure.marg().figure (Marg's newest usable closing carried by the spine); marg_as_on = that capture's printed as_on; shelf =
    stock_figure.shelf() -- None with named='no_count' for an item no count has reached (never Marg's figure: charter 3). pack_size /
    packing from sp_close_name through qty_words.pack_of, else sp_item (pack_src names the one used).
    items: the names to figure (default: the newest usable capture's printed names plus the count's items). upto: the last day of
    movements (default today)."""
    sw = _sw()
    sp = sp or sw.Spine()
    SF = _sf()
    ctx = ctx or SF.Ctx(con, sp)
    t = (upto or today()).isoformat() if not isinstance(upto, str) else upto
    if items is None:
        cap = SF.capture_at(sp, t, ctx)
        printed = sorted({r["name"] for r in sp.q("SELECT DISTINCT name FROM sp_close_name WHERE md5=?", cap["md5"])}) if cap else []
        names = sorted(set(printed) | set(count_family(con, ctx)))
    else:
        names = list(items)
    rows = {}
    for nm in names:
        F = SF.figures(con, sp, [nm], t, ctx)[nm]
        M, S = F["marg"], F["shelf"]
        c = (M or {}).get("closing") or {}
        pk, packing, src = SF.pack_of(con, sp, nm, ctx)
        rows[nm] = dict(item=nm, key=S.get("key"), marg=(M["figure"] if M else None), marg_as_on=(c.get("as_on") or None),
                        capture=dict(md5=c.get("md5"), stamp_iso=c.get("stamp_iso"), end_day=c.get("end_day"), by=c.get("by")) if c else None,
                        pack_size=int(pk or 1), packing=packing or "", pack_src=src,
                        base=S.get("base"), base_kind=S.get("base_kind"), base_day=S.get("base_day"), base_at=S.get("base_at"),
                        sold=S.get("sold") or 0.0, returned=S.get("returned") or 0.0, bought=S.get("bought") or 0.0, arrived=S.get("arrived") or 0.0,
                        approx=bool(S.get("approx") or (M or {}).get("approx")), named=S.get("named"), shelf=S.get("shelf"),
                        marg0=S.get("marg0"), boundary=S.get("boundary") or 0.0)
    return rows
'''))
SH.append(("H8 the gap table and the captures", '''# ------------------------------------------------------------------ S454 9.3: Marg's daily stock beside the shelf figure
GAP_DDL = ("CREATE TABLE IF NOT EXISTS s454_shelf_gap (as_on TEXT NOT NULL, item TEXT NOT NULL, shelf REAL, marg REAL, gap REAL, marg_move REAL, "
           "voucher REAL, base_day TEXT, pack INTEGER, approx INTEGER NOT NULL DEFAULT 0, flagged INTEGER NOT NULL DEFAULT 0, why TEXT, at TEXT NOT NULL, "
           "PRIMARY KEY (as_on, item))")
''', '''# ------------------------------------------------------------------ S454 9.3 / S577: Marg's closing beside the shelf figure, per usable capture
GAP_DDL = ("CREATE TABLE IF NOT EXISTS s577_shelf_gap (end_day TEXT NOT NULL, item TEXT NOT NULL, capture_md5 TEXT, shelf REAL, marg REAL, gap REAL, "
           "marg_move REAL, voucher REAL, base_day TEXT, pack INTEGER, approx INTEGER NOT NULL DEFAULT 0, flagged INTEGER NOT NULL DEFAULT 0, why TEXT, "
           "at TEXT NOT NULL, PRIMARY KEY (end_day, item))")                 # S577 (R2-B6): one set per END DAY, from the newest usable capture (charter 4)
'''))
SH.append(("H9 the captures' moments and filed_vouchers", '''_S524_CAPTURES = {}                                           # (d_from, d_to) -> (time, capture(d_from), capture(d_to)) -- one pass


def _s524_capture(con, day_iso):
    """S524 (F-848): the moment Marg's closing of a day was taken -- MAX(received_at) of that day's closing-stock pushes (stock_feed keeps
    as_on as dd-mm-yyyy; received_at and stock_voucher_entered.at are both now_iso(), string-comparable). None when the day has none."""
    day = str(day_iso or "")[:10]
    if len(day) != 10:
        return None
    try:
        r = con.execute("SELECT MAX(received_at) FROM stock_feed WHERE as_on=? AND LOWER(source) LIKE 'push_snapshot%'",
                        (day[8:10] + "-" + day[5:7] + "-" + day[0:4],)).fetchone()
        return str(r[0]) if r and r[0] else None
    except sqlite3.Error:
        return None


def _s524_captures(con, lo, hi):
    """The two captures of a window, kept for the life of one pass (filed_vouchers is called once per item); 600 s at most."""
    now = dt.datetime.now().timestamp()
    hit = _S524_CAPTURES.get((lo, hi))
    if hit and now - hit[0] < 600:
        return hit[1], hit[2]
    if len(_S524_CAPTURES) > 64:
        _S524_CAPTURES.clear()
    c_from, c_to = (_s524_capture(con, lo) if lo else None), _s524_capture(con, hi)
    _S524_CAPTURES[(lo, hi)] = (now, c_from, c_to)
    return c_from, c_to


def filed_vouchers(con, item, d_from, d_to):
    """Units of the count's vouchers for this item that Amir filed in Marg between two closings (stock_voucher_line by round and batch,
    stock_voucher_entered) -- the change Marg is EXPECTED to show without a sale or a purchase.
    S488 (F-754): stock_voucher_entered is an append-only log -- the newest row (highest id) of each (count, round, kind, batch) is the
    batch's state, and a batch counts only while that row carries a voucher number (the rule the stage proof keeps).
    S524 (F-848): a batch is judged by its MOMENT -- it counts in (d_from, d_to] when capture(d_from) < at <= capture(d_to), the captures
    being the moments Marg's closings of those days were taken (stock_feed). When EITHER capture is unknown, S488's day rule decides for
    that batch: its day is entered_on read as a date (dd-mm-yyyy, dd/mm/yyyy or ISO), else the day of `at`; it counts when
    d_from < day <= d_to (ISO days)."""
    if not (_has(con, "stock_voucher_line") and _has(con, "stock_voucher_entered")):
        return 0.0
    lo, hi = str(d_from or "")[:10], str(d_to or "")[:10]
    if not hi:
        return 0.0
    try:
        state = {}
        for cid, rno, kind, bno, vno, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                             "FROM stock_voucher_entered ORDER BY id"):
            state[(cid, rno, kind, bno)] = (vno, eon, at)
        c_from, c_to = _s524_captures(con, lo, hi)
''', '''def _capture_moments(con, sp, lo, hi, ctx):
    """(stamp_iso of the capture standing for the end of lo, the same for hi) -- stock_figure.capture_for: the newest usable capture by stamp
    for each end_day (the one choice rule); None where none stands for that day. S577: the closing's own capture, never a stock_feed push
    (the 22:30 re-send moved the old S524 lookup)."""
    SF = _sf()
    cf = SF.capture_for(sp, lo, ctx) if lo else None
    ct = SF.capture_for(sp, hi, ctx)
    return (cf["stamp_iso"] if cf else None), (ct["stamp_iso"] if ct else None)


def filed_vouchers(con, item, d_from, d_to, sp=None, ctx=None):
    """Units of the count's vouchers for this item that Amir filed in Marg between two closings (stock_voucher_line by round and batch,
    stock_voucher_entered) -- the change Marg is EXPECTED to show without a sale or a purchase.
    S488 (F-754): stock_voucher_entered is an append-only log -- the newest row (highest id) of each (count, round, kind, batch) is the
    batch's state, and a batch counts only while that row carries a voucher number (the rule the stage proof keeps).
    S524 (F-848) / S577: a batch is judged by its MOMENT -- it counts in (d_from, d_to] when capture(d_from) < at <= capture(d_to), the
    captures being the spine's own usable closing captures standing for those end days (stock_figure.capture_for, the newest by stamp).
    When EITHER capture is unknown, S488's day rule decides for that batch: its day is entered_on read as a date (dd-mm-yyyy, dd/mm/yyyy or
    ISO), else the day of `at`; it counts when d_from < day <= d_to (ISO days)."""
    if not (_has(con, "stock_voucher_line") and _has(con, "stock_voucher_entered")):
        return 0.0
    lo, hi = str(d_from or "")[:10], str(d_to or "")[:10]
    if not hi:
        return 0.0
    try:
        state = {}
        for cid, rno, kind, bno, vno, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                             "FROM stock_voucher_entered ORDER BY id"):
            state[(cid, rno, kind, bno)] = (vno, eon, at)
        sp = sp or _sw().Spine()
        ctx = ctx or _sf().Ctx(con, sp)
        c_from, c_to = _capture_moments(con, sp, lo, hi, ctx)
'''))
SH.append(("H10 rejudge, record_gaps, gap_flags, gap_flag, gap_line", '''def rejudge(con, sp=None):
    """S494 (F-765): A FLAG IS JUDGED AGAIN WHEN LATER EVIDENCE ARRIVES. record_gaps judges a closing once, when Marg's closing-stock report
    lands -- often before that day's sale or purchase report has reached the spine. Every first flag (an ORIGIN: flagged, its why written by
    record_gaps for its own closing -- 'Marg moved ... on <its own as_on>') of a closing within stock.gap_rejudge_days days of the newest is
    worked out again exactly as record_gaps works it, from the stored rows and the spine as it is now; when its move is now explained
    (|move - vouchers| < stock.gap_min_packs packs) it is cleared, and every later copy of it (the same item, flagged, the same why) with it.
    ONE DIRECTION ONLY: it never raises a flag and never touches an unflagged row, an approximate row or a flag whose origin lies before the
    window (the spine's evidence can shrink for a while -- F-737). Nothing is written when nothing clears. Returns the rows cleared."""
    if not _has(con, "s454_shelf_gap"):
        return 0
    newest = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap").fetchone()[0]
    if not newest:
        return 0
    try:
        days = int(float(_setting(con, "stock.gap_rejudge_days", "7")))
    except ValueError:
        days = 7
    try:
        lo = (dt.date.fromisoformat(str(newest)[:10]) - dt.timedelta(days=days)).isoformat()
    except ValueError:
        return 0
    origins = [r for r in con.execute("SELECT as_on, item, marg, pack, why, at FROM s454_shelf_gap WHERE flagged=1 AND approx=0 AND as_on>=? "
                                      "AND why LIKE 'Marg moved %' ORDER BY as_on, item", (lo,)).fetchall()
               if (" on %s" % r[0]) in str(r[4] or "")]
    if not origins:
        return 0
    sp = sp or _sw().Spine()
    if not sp.ok:
        return 0
    try:
        mins = float(_setting(con, "stock.gap_min_packs", "1"))
    except ValueError:
        mins = 1.0
    stamp = dt.datetime.now().replace(microsecond=0).strftime("%d-%m %H:%M")
    clear = []
    for d, item, marg, pack, why, at in origins:                   # pass 1: each origin, oldest closing first
        prev = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap WHERE as_on<?", (d,)).fetchone()[0]
        if not prev or marg is None:
            continue
        p = con.execute("SELECT marg FROM s454_shelf_gap WHERE as_on=? AND item=?", (prev, item)).fetchone()
        if not p or p[0] is None:
            continue
        sold, ret, bought = movements(sp, item, prev, d, incl_from=False)
        move = float(marg) - float(p[0]) - (bought - sold + ret)
        vch = filed_vouchers(con, item, prev, d)
        pk = int(pack or 1)
        thr = mins * (pk if pk > 1 else 1)
        if thr > 0 and abs(move - vch) < thr:
            clear.append((d, item, why, move, vch, "explained by a report that arrived later (first flagged %s; judged again %s)" % (_s494_ddmm_hm(at), stamp)))
    if not clear:
        return 0
    n = 0
    try:
        for d, item, why, move, vch, new_why in clear:
            n += con.execute("UPDATE s454_shelf_gap SET flagged=0, marg_move=?, voucher=?, why=? WHERE as_on=? AND item=? AND flagged=1 AND approx=0",
                             (move, vch, new_why, d, item)).rowcount or 0
        for d, item, why, move, vch, new_why in clear:                # pass 2: its copies, matched on the origin's why as it stood
            n += con.execute("UPDATE s454_shelf_gap SET flagged=0, why=? WHERE item=? AND as_on>? AND flagged=1 AND approx=0 AND why=?",
                             (new_why, item, d, why)).rowcount or 0
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    return n


def record_gaps(con, sp=None):
    """At each new closing-stock report: for each item the gap between the shelf figure (movements up to that closing day) and Marg's.
    A gap that changes with no voucher -- Marg moved by more (or less) than its own sales, purchases and the vouchers Amir filed -- is a
    movement one side has and the other has not: flagged (never an approximate item; never a change under stock.gap_min_packs packs).
    On the count day the gap is the count's own correction; it stays until Amir files that item's voucher, and then closes by it.
    Idempotent: one set of rows per closing. Returns the rows written (0 when this closing is recorded already)."""
    con.execute(GAP_DDL)
    try:                                                      # S494 (F-765): first judge again what later reports explain
        rejudge(con, sp)
    except Exception:                                         # noqa: BLE001 -- never stops the closing's own rows
        pass
    as_on, snap = latest_snapshot(con)
    if not as_on or con.execute("SELECT 1 FROM s454_shelf_gap WHERE as_on=? LIMIT 1", (as_on,)).fetchone():
        return 0
    sw = _sw()
    sp = sp or sw.Spine()
    prev = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap WHERE as_on<?", (as_on,)).fetchone()[0]
    prow = {r[0]: dict(marg=r[1], gap=r[2], base_day=r[3], flagged=r[4], why=r[5]) for r in
            con.execute("SELECT item, marg, gap, base_day, flagged, why FROM s454_shelf_gap WHERE as_on=?", (prev,))} if prev else {}
    try:
        mins = float(_setting(con, "stock.gap_min_packs", "1"))
    except ValueError:
        mins = 1.0
    F = figures(con, sp=sp, items=list(snap), upto=as_on)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    n = 0
    for item, s in snap.items():
        f = F.get(item) or {}
        if f.get("shelf") is None or f.get("named") in ("no_count", "no_spine"):
            continue
        gap = float(f["shelf"]) - float(s["qty"])
        p = prow.get(item)
        flagged, why, move, vch = 0, None, None, None
        if p and p.get("marg") is not None and sp.ok:
            sold, ret, bought = movements(sp, item, prev, as_on, incl_from=False)
            move = float(s["qty"]) - float(p["marg"]) - (bought - sold + ret)    # Marg's change its own sales, returns and purchases do not explain
            vch = filed_vouchers(con, item, prev, as_on)
            thr = mins * (s["pack_size"] if s["pack_size"] > 1 else 1)
            if f.get("approx"):
                why = "approximate (one spine key, several items) -- never flagged"
            elif p.get("base_day") != f.get("base_day"):
                why = "a new count since the last closing (rebased)"
            elif abs(move - vch) >= thr and thr > 0:
                flagged = 1
                why = "Marg moved %+g beyond its own sales and purchases on %s%s" % (round(move, 1), as_on, (" (vouchers filed: %+g)" % vch) if vch else " with no voucher filed")
            elif p.get("flagged"):                            # it stays flagged until the item is counted again (a new base)
                flagged, why = 1, p.get("why")
        con.execute("INSERT OR REPLACE INTO s454_shelf_gap (as_on, item, shelf, marg, gap, marg_move, voucher, base_day, pack, approx, flagged, why, at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (as_on, item, f["shelf"], s["qty"], gap, move, vch, f.get("base_day"), s["pack_size"],
                                                            int(bool(f.get("approx"))), flagged, why, now))
        n += 1
    con.commit()
    return n


def gap_flags(con):
    """(as_on, [dict(item, gap, marg_move, why)]) -- the items flagged at the newest recorded closing."""
    try:
        con.execute(GAP_DDL)
        as_on = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap").fetchone()[0]
        if not as_on:
            return None, []
        return as_on, [dict(item=r[0], gap=r[1], marg_move=r[2], why=r[3]) for r in
                       con.execute("SELECT item, gap, marg_move, why FROM s454_shelf_gap WHERE as_on=? AND flagged=1 ORDER BY item", (as_on,))]
    except sqlite3.Error:
        return None, []


def gap_flag(con, item_norm):
    """1 when the item (stock_watch.norm_name) is flagged at the newest recorded closing -- one more reason on the spot-count roster."""
    _as_on, fl = gap_flags(con)
    sw = _sw()
    return 1 if any(sw.norm_name(x["item"]) == item_norm for x in fl) else 0


def gap_line(con):
    """The owner's one line: the count of such items and their names."""
    as_on, fl = gap_flags(con)
    if not fl:
        return None
    return dict(cls="info", target="porders", text="Marg and the shelf figure moved apart on %d item%s (closing of %s): %s -- they go up Darpan's spot-count list"
                % (len(fl), "" if len(fl) == 1 else "s", "%s-%s" % (as_on[8:10], as_on[5:7]), ", ".join(x["item"] for x in fl[:8])))
''', '''def rejudge(con, sp=None, ctx=None):
    """S494 (F-765): A FLAG IS JUDGED AGAIN WHEN LATER EVIDENCE ARRIVES. record_gaps judges a closing once -- often before that day's sale or
    purchase report has reached the spine. Every first flag (an ORIGIN: flagged, its why written by record_gaps for its own end day --
    'Marg moved ... on <its own end_day>') of a set within stock.gap_rejudge_days days of the newest is worked out again exactly as
    record_gaps works it, from the stored s577_shelf_gap rows and the spine as it is now; when its move is now explained
    (|move - vouchers| < stock.gap_min_packs packs) it is cleared, and every later copy of it (the same item, flagged, the same why) with it.
    ONE DIRECTION ONLY: it never raises a flag and never touches an unflagged row, an approximate row or a flag whose origin lies before the
    window (the spine's evidence can shrink for a while -- F-737). Nothing is written when nothing clears. Returns the rows cleared.
    S577: s577_shelf_gap alone (its window fills from the second pass); prev = the newest earlier set."""
    if not _has(con, "s577_shelf_gap"):
        return 0
    newest = con.execute("SELECT MAX(end_day) FROM s577_shelf_gap").fetchone()[0]
    if not newest:
        return 0
    try:
        days = int(float(_setting(con, "stock.gap_rejudge_days", "7")))
    except ValueError:
        days = 7
    try:
        lo = (dt.date.fromisoformat(str(newest)[:10]) - dt.timedelta(days=days)).isoformat()
    except ValueError:
        return 0
    origins = [r for r in con.execute("SELECT end_day, item, marg, pack, why, at FROM s577_shelf_gap WHERE flagged=1 AND approx=0 AND end_day>=? "
                                      "AND why LIKE 'Marg moved %' ORDER BY end_day, item", (lo,)).fetchall()
               if (" on %s" % r[0]) in str(r[4] or "")]
    if not origins:
        return 0
    sp = sp or _sw().Spine()
    if not sp.ok:
        return 0
    ctx = ctx or _sf().Ctx(con, sp)
    try:
        mins = float(_setting(con, "stock.gap_min_packs", "1"))
    except ValueError:
        mins = 1.0
    stamp = dt.datetime.now().replace(microsecond=0).strftime("%d-%m %H:%M")
    clear = []
    for d, item, marg, pack, why, at in origins:                   # pass 1: each origin, oldest end day first
        prev = con.execute("SELECT MAX(end_day) FROM s577_shelf_gap WHERE end_day<?", (d,)).fetchone()[0]
        if not prev or marg is None:
            continue
        p = con.execute("SELECT marg FROM s577_shelf_gap WHERE end_day=? AND item=?", (prev, item)).fetchone()
        if not p or p[0] is None:
            continue
        sold, ret, bought = movements(sp, item, prev, d, incl_from=False, ctx=ctx)
        move = float(marg) - float(p[0]) - (bought - sold + ret)
        vch = filed_vouchers(con, item, prev, d, sp=sp, ctx=ctx)
        pk = int(pack or 1)
        thr = mins * (pk if pk > 1 else 1)
        if thr > 0 and abs(move - vch) < thr:
            clear.append((d, item, why, move, vch, "explained by a report that arrived later (first flagged %s; judged again %s)" % (_s494_ddmm_hm(at), stamp)))
    if not clear:
        return 0
    n = 0
    try:
        for d, item, why, move, vch, new_why in clear:
            n += con.execute("UPDATE s577_shelf_gap SET flagged=0, marg_move=?, voucher=?, why=? WHERE end_day=? AND item=? AND flagged=1 AND approx=0",
                             (move, vch, new_why, d, item)).rowcount or 0
        for d, item, why, move, vch, new_why in clear:                # pass 2: its copies, matched on the origin's why as it stood
            n += con.execute("UPDATE s577_shelf_gap SET flagged=0, why=? WHERE item=? AND end_day>? AND flagged=1 AND approx=0 AND why=?",
                             (new_why, item, d, why)).rowcount or 0
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    return n


def record_gaps(con, sp=None, ctx=None):
    """S577 (charter 1b, 4): ONE set of rows per END DAY, from the NEWEST usable closing capture (stock_figure: the one choice rule) that the
    spine's sale and purchase reach covers (stock_figure.tryable). For each item the capture prints: the shelf figure (movements up to that
    end day) against Marg's figure at the capture, and Marg's move since the PREVIOUS usable capture (its figure from stock_figure.closing,
    never a stored row) beyond its own sales, returns, purchases and the vouchers Amir filed between the two captures' moments. A move a
    pack or more (stock.gap_min_packs) unexplained is flagged -- never an approximate item (a family figure), never an item with no count.
    A flag carries forward only from an earlier s577_shelf_gap set. Writes nothing while stock_figure.ready() is False ('not yet'), nothing
    when the newest covered end day is recorded already. Only the newest covered end day is written by a pass. Returns the rows written."""
    con.execute(GAP_DDL)
    sw = _sw()
    sp = sp or sw.Spine()
    SF = _sf()
    ctx = ctx or SF.Ctx(con, sp)
    try:                                                      # S494 (F-765): first judge again what later reports explain
        rejudge(con, sp, ctx)
    except Exception:                                         # noqa: BLE001 -- never stops the set's own rows
        pass
    if not SF.ready(sp):
        return 0
    R = SF.reach(sp)
    covered = sorted({c["end_day"] for c in SF.usable_captures(sp, ctx) if SF.tryable(c, R)[0]})
    if not covered:
        return 0
    E = covered[-1]
    C = SF.capture_for(sp, E, ctx)
    if C is None or con.execute("SELECT 1 FROM s577_shelf_gap WHERE end_day=? LIMIT 1", (E,)).fetchone():
        return 0
    earlier = [c["end_day"] for c in SF.usable_captures(sp, ctx) if c["end_day"] < E]
    P = SF.capture_for(sp, max(earlier), ctx) if earlier else None
    prev_set = con.execute("SELECT MAX(end_day) FROM s577_shelf_gap WHERE end_day<?", (E,)).fetchone()[0]
    prow = {r[0]: dict(base_day=r[1], flagged=r[2], why=r[3]) for r in
            con.execute("SELECT item, base_day, flagged, why FROM s577_shelf_gap WHERE end_day=?", (prev_set,))} if prev_set else {}
    try:
        mins = float(_setting(con, "stock.gap_min_packs", "1"))
    except ValueError:
        mins = 1.0
    names = sorted({r["name"] for r in sp.q("SELECT DISTINCT name FROM sp_close_name WHERE md5=?", C["md5"]) if r["name"]})
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    n = 0
    for item in names:
        f = figures(con, sp=sp, items=[item], upto=E, ctx=ctx).get(item) or {}
        if f.get("shelf") is None or f.get("named") in ("no_count", "no_spine") or f.get("marg") is None:
            continue
        m_now = float(f["marg"])
        gap = float(f["shelf"]) - m_now
        flagged, why, move, vch = 0, None, None, None
        pack = int(f.get("pack_size") or 1)
        p0 = SF.closing(con, sp, item, P["end_day"], ctx) if P else None
        if p0 is not None and sp.ok:
            sold, ret, bought = movements(sp, item, P["end_day"], E, incl_from=False, ctx=ctx)
            move = m_now - float(p0["units"]) - (bought - sold + ret)    # Marg's change its own sales, returns and purchases do not explain
            vch = filed_vouchers(con, item, P["end_day"], E, sp=sp, ctx=ctx)
            thr = mins * (pack if pack > 1 else 1)
            p = prow.get(item)
            if f.get("approx"):
                why = "approximate (one spine key, several items) -- never flagged"
            elif p and p.get("base_day") != f.get("base_day"):
                why = "a new count since the last closing (rebased)"
            elif abs(move - vch) >= thr and thr > 0:
                flagged = 1
                why = "Marg moved %+g beyond its own sales and purchases on %s%s" % (round(move, 1), E, (" (vouchers filed: %+g)" % vch) if vch else " with no voucher filed")
            elif p and p.get("flagged"):                      # it stays flagged until the item is counted again (a new base)
                flagged, why = 1, p.get("why")
        con.execute("INSERT OR REPLACE INTO s577_shelf_gap (end_day, item, capture_md5, shelf, marg, gap, marg_move, voucher, base_day, pack, approx, flagged, why, at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (E, item, C["md5"], f["shelf"], m_now, gap, move, vch, f.get("base_day"), pack,
                                                              int(bool(f.get("approx"))), flagged, why, now))
        n += 1
    con.commit()
    return n


def gap_flags(con):
    """(end_day, [dict(item, gap, marg_move, why)]) -- the items flagged in the newest recorded set (s577_shelf_gap)."""
    try:
        con.execute(GAP_DDL)
        end_day = con.execute("SELECT MAX(end_day) FROM s577_shelf_gap").fetchone()[0]
        if not end_day:
            return None, []
        return end_day, [dict(item=r[0], gap=r[1], marg_move=r[2], why=r[3]) for r in
                         con.execute("SELECT item, gap, marg_move, why FROM s577_shelf_gap WHERE end_day=? AND flagged=1 ORDER BY item", (end_day,))]
    except sqlite3.Error:
        return None, []


def gap_flag(con, item_norm, ctx=None):
    """1 when the item (stock_watch.norm_name) is flagged in the newest recorded set -- one more reason on the spot-count roster. S577: a
    flagged item is matched under every printed form of it (a renamed item's old and new names: stock_figure.printed_forms)."""
    _d, fl = gap_flags(con)
    if not fl:
        return 0
    sw, SF = _sw(), _sf()
    ctx = ctx or SF.Ctx(con, None)
    for x in fl:
        if any(sw.norm_name(f) == item_norm for f in SF.printed_forms(con, x["item"], ctx)):
            return 1
    return 0


def gap_line(con):
    """The owner's one line: the count of such items and their names."""
    end_day, fl = gap_flags(con)
    if not fl:
        return None
    return dict(cls="info", target="porders", text="Marg and the shelf figure moved apart on %d item%s (closing of %s): %s -- they go up Darpan's spot-count list"
                % (len(fl), "" if len(fl) == 1 else "s", "%s-%s" % (end_day[8:10], end_day[5:7]), ", ".join(x["item"] for x in fl[:8])))
'''))

# =============================================================================================================== stock_watch.py
SW = []
SW.append(("W1 version", '''VERSION = "1.4"
KIT = "S502_STOCK_MILAAN_TODAY"                               # v1.3 was S436_STAFF_PAGES_CLEAN
''', '''VERSION = "1.5"
KIT = "S577_STOCK_ON_SPINE"                                   # v1.4 was S502_STOCK_MILAAN_TODAY, v1.3 S436_STAFF_PAGES_CLEAN
# v1.5 (S577, rung 4b, 18-Oct-2026): a spot count is judged by stock_figure.expect_for_point -- the shelf figure (counted), Marg's figure
# (uncounted), or NO figure for a size that shares a family figure (basis 'approx': the plain receipt only, no verdict, no loss line, no
# trace, out of the month's leakage). stock_point.basis (additive) carries it; settle_provisional re-judges a provisional point on its stored
# basis; a correction keeps the old point's basis; open_trace judges its window on the same base. _arrivals and bill_pending_lines key the
# spine by stock_figure.key_of (charter 12). expected_units stays for the witness week only; the unread close-day method of Spine is gone.
'''))
SW.append(("W2 the stock_figure door", '''def _sa():
    import stock_app                                          # noqa: PLC0415 -- beside this file, loaded first by finance_app
    return stock_app
''', '''def _sa():
    import stock_app                                          # noqa: PLC0415 -- beside this file, loaded first by finance_app
    return stock_app


def _sf():
    import stock_figure                                       # noqa: PLC0415 -- beside this file: THE one stock function (S577); it imports this file lazily
    return stock_figure
'''))
SW.append(("W3 ensure: stock_point.basis", '''def ensure(con):
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)" % ",".join("?" * len(_TABLES)), _TABLES)}
    if len(have) < len(_TABLES):
        con.executescript(SCHEMA)
    _s502_columns(con)
''', '''def _s577_columns(con):
    """S577: stock_point.basis -- 'shelf' | 'marg' | 'approx' (what the point was judged against; NULL on older rows = 'marg'). Additive."""
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_point)").fetchall()}
        if cols and "basis" not in cols:
            con.execute("ALTER TABLE stock_point ADD COLUMN basis TEXT")
    except sqlite3.Error:
        pass


def ensure(con):
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)" % ",".join("?" * len(_TABLES)), _TABLES)}
    if len(have) < len(_TABLES):
        con.executescript(SCHEMA)
    _s502_columns(con)
    _s577_columns(con)
'''))
SW.append(("W4 latest_close_day removed", '''    def latest_close_day(self):
        r = self.q("SELECT MAX(as_on) AS d FROM sp_close")
        return r[0]["d"] if r and r[0]["d"] else None

    def sales(self, name, d_from, d_to, incl_from=False):''', '''    def sales(self, name, d_from, d_to, incl_from=False):'''))
SW.append(("W5 _arrivals keys by key_of", '''def _arrivals(con, item, since_iso, sp):
    """Tapped arrivals of the item after since_iso (purchase_order_line, supplied packs x pack_size) with the supplier,
    each marked whether the spine already carries a purchase of the item from that supplier after the tap's order day."""
    out = []
    try:
        keys = {pad_norm(item[:27]), pad_norm(item)}
''', '''def _arrivals(con, item, since_iso, sp, ctx=None):
    """Tapped arrivals of the item after since_iso (purchase_order_line, supplied packs x pack_size) with the supplier,
    each marked whether the spine already carries a purchase of the item from that supplier after the tap's order day.
    S577: the spine is keyed by stock_figure.key_of (a renamed item reaches its family's purchases); the order line is still matched by
    pad_norm(name[:27]) -- seen, not touched (charter 12)."""
    out = []
    k20 = None
    try:
        keys = {pad_norm(item[:27]), pad_norm(item)}
'''))
SW.append(("W6 _arrivals the spine look", '''            if sp.ok:
                rows = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", sp.key(item), sk, str(r[10])[:10])
                in_spine = bool(rows and rows[0]["n"])
''', '''            if sp.ok:
                if k20 is None:
                    k20 = _sf().key_of(sp, item, ctx)
                rows = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", k20, sk, str(r[10])[:10])
                in_spine = bool(rows and rows[0]["n"])
'''))
SW.append(("W7 expected_units: witness only", '''def expected_units(con, sp, item):
    """The stock the records say should be on the shelf now: the latest Marg closing (spine) - sales since + purchases
    since (net of returns) + PROVISIONAL tapped arrivals the spine does not yet carry. Returns dict."""
''', '''def expected_units(con, sp, item):
    """WITNESS ONLY (S577, rung 4b-2 retires it): the old expectation -- the latest sp_close (printed day = day end, no capture rule) -
    sales since + purchases since (net of returns) + PROVISIONAL tapped arrivals. Read by stock_figure.witness beside stock_figure.marg for
    one week; no judgment reads it any more (expect_for_point is the one)."""
'''))
SW.append(("W8 write_point", '''def write_point(con, item, qty_units, source, who, roster_id=None, note=None, sp=None, count_id=None, silent=False,
                expected=_UNSET, expected_as_on=None, commit=True):
    """ONE stock point: expected from the records (provisional if an arrival term is provisional), the gap, and what
    follows -- a short within the item's allowance is a quiet loss point; a larger one is a dated loss line under the
    staff block and on the owner's watch card; a surplus is noted. Returns the point row."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    item = info["item"]
    if expected is _UNSET:
        E = _s454_expected(con, sp, item)                      # S454 P3 (9.2, D667): the shelf figure, else the records' expectation
    else:                                                      # S502 (F-812): a correction is judged against the figure the old point was judged on
        E = dict(expected=(None if expected is None else float(expected)), provisional=0.0,
                 as_on=(str(expected_as_on)[:10] if expected_as_on else None))
    ts = now_iso()
    gap = None if E["expected"] is None else round(float(qty_units) - E["expected"], 3)
    status = "provisional" if E["provisional"] else "settled"
    cur = con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, note, count_id, roster_id, provisional_units) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (norm_name(item), item, ts, float(qty_units), source, who or "", E["expected"], gap, status, (ts if status == "settled" else None), note, count_id, roster_id, E["provisional"]))
    pid = int(cur.lastrowid)
    P = dict(id=pid, item=item, pack=info["pack"], packing=info["packing"], qty=float(qty_units), expected=E["expected"], gap=gap, status=status, provisional=E["provisional"],
             qty_text=qw(qty_units, info["pack"], info["packing"], item), qty_hi=qw(qty_units, info["pack"], info["packing"], item, "hi"),
             gap_text=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item)), gap_hi=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item, "hi")),
             verdict="", verdict_hi="", loss_line=None, trace=None)
    if gap is None:
        P["verdict"], P["verdict_hi"] = "no Marg figure for this item yet -- counted and kept", "Marg mein yeh item nahi mila -- ginti likh li"
''', '''def write_point(con, item, qty_units, source, who, roster_id=None, note=None, sp=None, count_id=None, silent=False,
                expected=_UNSET, expected_as_on=None, commit=True, basis=None):
    """ONE stock point: expected from stock_figure.expect_for_point (the shelf figure for a counted item, Marg's figure for an uncounted
    one; provisional if an arrival is provisional), the gap, and what follows -- a short within the item's allowance is a quiet loss point;
    a larger one is a dated loss line under the staff block and on the owner's watch card; a surplus is noted. Returns the point row.
    S577 (R2-B8): a size that shares a FAMILY figure (basis 'approx') stores NULL expected and NULL gap -- no verdict, no loss line, no trace;
    the staff receipt alone. A correction (expected given) carries the OLD point's basis."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    item = info["item"]
    if expected is _UNSET:
        E = _s454_expected(con, sp, item)                      # S577: stock_figure.expect_for_point -- basis shelf | marg | approx
    else:                                                      # S502 (F-812): a correction is judged against the figure the old point was judged on
        E = dict(expected=(None if (expected is None or basis == "approx") else float(expected)), provisional=0.0,
                 as_on=(str(expected_as_on)[:10] if expected_as_on else None), basis=(basis or ("marg" if expected is not None else None)))
    basis = E.get("basis")
    ts = now_iso()
    gap = None if E["expected"] is None else round(float(qty_units) - E["expected"], 3)
    status = "provisional" if E["provisional"] else "settled"
    cur = con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, note, count_id, roster_id, provisional_units, basis) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (norm_name(item), item, ts, float(qty_units), source, who or "", E["expected"], gap, status, (ts if status == "settled" else None), note, count_id, roster_id, E["provisional"], basis))
    pid = int(cur.lastrowid)
    P = dict(id=pid, item=item, pack=info["pack"], packing=info["packing"], qty=float(qty_units), expected=E["expected"], gap=gap, status=status, provisional=E["provisional"],
             qty_text=qw(qty_units, info["pack"], info["packing"], item), qty_hi=qw(qty_units, info["pack"], info["packing"], item, "hi"),
             gap_text=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item)), gap_hi=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item, "hi")),
             verdict="", verdict_hi="", loss_line=None, trace=None, basis=basis, expected_as_on=E.get("as_on"))
    if basis == "approx":
        P["verdict"], P["verdict_hi"] = "", ""                 # S577: counted against a family figure -- not judged; the receipt alone (R3 blocker 2)
    elif gap is None:
        P["verdict"], P["verdict_hi"] = "no Marg figure for this item yet -- counted and kept", "Marg mein yeh item nahi mila -- ginti likh li"
'''))
SW.append(("W9 write_point: the trace on the same base", '''            if not silent:
                try:
                    P["trace"] = open_trace(con, item, "point", gap, who, sp=sp, point_id=pid)["id"]
                except Exception:                             # noqa: BLE001
                    P["trace"] = None
    _audit(con, "point", dict(item=item, qty=float(qty_units), source=source, expected=E["expected"], gap=gap, status=status, text="%s: %s counted (%s), %s" % (item, P["qty_text"], source, P["verdict"])), who, pid)
''', '''            if not silent:
                try:
                    P["trace"] = open_trace(con, item, "point", gap, who, sp=sp, point_id=pid, E=E)["id"]   # S577: the trace on the point's own base
                except Exception:                             # noqa: BLE001
                    P["trace"] = None
    _audit(con, "point", dict(item=item, qty=float(qty_units), source=source, expected=E["expected"], gap=gap, status=status, basis=basis, text="%s: %s counted (%s), %s" % (item, P["qty_text"], source, P["verdict"] or "counted against a family figure -- not judged")), who, pid)
'''))
SW.append(("W10 settle_provisional on the stored basis", '''def settle_provisional(con, sp=None):
    """A provisional point whose arrival the spine now carries is re-evaluated and settled. Idempotent."""
    ensure(con)
    sp = sp or Spine()
    n = 0
    for r in con.execute("SELECT id, item, qty_units FROM stock_point WHERE status='provisional'").fetchall():
        E = expected_units(con, sp, r[1])
        if E["provisional"]:
            continue
        gap = None if E["expected"] is None else round(float(r[2]) - E["expected"], 3)
        con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, status='settled', settled_at=?, provisional_units=0 WHERE id=?", (E["expected"], gap, now_iso(), r[0]))
        n += 1
    if n:
        con.commit()
    return n
''', '''def settle_provisional(con, sp=None):
    """A provisional point whose arrival the spine now carries is re-judged ON ITS STORED BASIS (S577: stock_figure.expect_for_point with
    basis='shelf' | 'marg'; NULL = 'marg', the old meaning read through the one capture rule) and settled. An approx point is never
    re-judged. Idempotent."""
    ensure(con)
    sp = sp or Spine()
    ctx = _sf().Ctx(con, sp)
    n = 0
    for r in con.execute("SELECT id, item, qty_units, basis FROM stock_point WHERE status='provisional'").fetchall():
        b = str(r[3] or "marg")
        if b == "approx":
            continue
        E = _sf().expect_for_point(con, sp, r[1], ctx=ctx, basis=b, exclude_id=r[0])   # judged against the base BEFORE the point itself
        if E["provisional"]:
            continue
        gap = None if E["expected"] is None else round(float(r[2]) - E["expected"], 3)
        con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, status='settled', settled_at=?, provisional_units=0, basis=? WHERE id=?",
                    (E["expected"], gap, now_iso(), b, r[0]))
        n += 1
    if n:
        con.commit()
    return n
'''))
SW.append(("W11 bill_pending_lines keys by key_of", '''    seen = set()
    for item, supplied, ps, arrived, vendor, created, lid in rows:
        if not sp.ok:
            break
        sk = supkey(vendor)
        n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", sp.key(item), sk, str(created)[:10])
''', '''    seen = set()
    ctx = _sf().Ctx(con, sp)                                   # S577 (F-873): the spine keyed by the one identity -- a renamed item reaches its purchases
    for item, supplied, ps, arrived, vendor, created, lid in rows:
        if not sp.ok:
            break
        sk = supkey(vendor)
        n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", _sf().key_of(sp, item, ctx), sk, str(created)[:10])
'''))
SW.append(("W12 answer_roster: the receipt alone for an approx point", '''    con.commit()
    return True, "Likh liya: %s — %s. %s" % (r[1], P["qty_hi"], P["verdict_hi"]), 200, P
''', '''    con.commit()
    return True, ("Likh liya: %s — %s. %s" % (r[1], P["qty_hi"], P["verdict_hi"])).rstrip(), 200, P     # S577: an approx point has no verdict -- the receipt alone
'''))
SW.append(("W13 correct_roster carries the old basis", '''    old = con.execute("SELECT id, item, qty_units, expected_units, at, by, note FROM stock_point WHERE id=?", (int(r[5]),)).fetchone()
''', '''    old = con.execute("SELECT id, item, qty_units, expected_units, at, by, note, basis FROM stock_point WHERE id=?", (int(r[5]),)).fetchone()
'''))
SW.append(("W14 correct_roster: write_point with the basis", '''        P = write_point(con, old[1], q, "spot", who, roster_id=r[0], note="badla: pehle %s likha tha (point %d)" % (old_words, old[0]), sp=sp,
                        expected=old[3], expected_as_on=str(old[4] or "")[:10], commit=False, silent=True)
''', '''        P = write_point(con, old[1], q, "spot", who, roster_id=r[0], note="badla: pehle %s likha tha (point %d)" % (old_words, old[0]), sp=sp,
                        expected=old[3], expected_as_on=str(old[4] or "")[:10], commit=False, silent=True, basis=(old[7] or ("marg" if old[3] is not None else None)))   # S577: the old point's basis, approx included
'''))
SW.append(("W15 correct_roster: the words", '''    if P.get("loss_line"):                                    # still short beyond the allowance against the old expected figure: its trace, as write_point would have
        try:
            P["trace"] = open_trace(con, old[1], "point", P["gap"], who, sp=sp, point_id=P["id"])["id"]
        except Exception:                                     # noqa: BLE001 -- the correction stands; the trace is a courtesy
            P["trace"] = None
    return True, "Badal diya: %s — %s. %s" % (old[1], P["qty_hi"], P["verdict_hi"]), 200, P
''', '''    if P.get("loss_line"):                                    # still short beyond the allowance against the old expected figure: its trace, as write_point would have
        try:
            P["trace"] = open_trace(con, old[1], "point", P["gap"], who, sp=sp, point_id=P["id"], E=dict(basis=P.get("basis"), as_on=P.get("expected_as_on"), expected=P.get("expected")))["id"]
        except Exception:                                     # noqa: BLE001 -- the correction stands; the trace is a courtesy
            P["trace"] = None
    return True, ("Badal diya: %s — %s. %s" % (old[1], P["qty_hi"], P["verdict_hi"])).rstrip(), 200, P
'''))
SW.append(("W16 darpan_point: the words", '''    P = write_point(con, info["item"], qty_units, "darpan", who, sp=sp)
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), norm_name(info["item"])))
    con.commit()
    return True, "Likh liya: %s — %s. %s" % (info["item"], P["qty_hi"], P["verdict_hi"]), 200, P
''', '''    P = write_point(con, info["item"], qty_units, "darpan", who, sp=sp)
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), norm_name(info["item"])))
    con.commit()
    return True, ("Likh liya: %s — %s. %s" % (info["item"], P["qty_hi"], P["verdict_hi"])).rstrip(), 200, P
'''))
SW.append(("W17 gadbad: no trace for an approx point", '''    t = re.sub(r"\\s+", " ", str(text or "")).strip()[:500]
    P = None
    if qty_units is not None:
        P = write_point(con, info["item"], qty_units, "darpan", who, note="gadbad: " + t, sp=sp, silent=True)
        gap = P["gap"]
    else:
        gap = None
    T = open_trace(con, info["item"], "darpan", gap, who, sp=sp, note=t, point_id=(P["id"] if P else None))
    return True, "Likh liya -- system dekh raha hai (%s)." % T["verdict_hi"], 200, dict(point=P, trace=T)
''', '''    t = re.sub(r"\\s+", " ", str(text or "")).strip()[:500]
    P = None
    if qty_units is not None:
        P = write_point(con, info["item"], qty_units, "darpan", who, note="gadbad: " + t, sp=sp, silent=True)
        gap = P["gap"]
        if P.get("basis") == "approx":                        # S577: a family figure -- the text is kept on the point; no trace, no "wajah mil gayi"
            return True, "Likh liya: %s — %s." % (info["item"], P["qty_hi"]), 200, dict(point=P, trace=None)
    else:
        gap = None
    T = open_trace(con, info["item"], "darpan", gap, who, sp=sp, note=t, point_id=(P["id"] if P else None),
                   E=(dict(basis=P.get("basis"), as_on=P.get("expected_as_on"), expected=P.get("expected")) if P else None))
    return True, "Likh liya -- system dekh raha hai (%s)." % T["verdict_hi"], 200, dict(point=P, trace=T)
'''))
SW.append(("W18 open_trace on the point's base", '''def open_trace(con, item, trigger, gap_units, who, sp=None, note=None, point_id=None, count_id=None, quiet=False):
    """Rebuild from the anchor (the last settled point with gap 0, else the last closed full count) to now and run the
    seven checks in order; each explains the gap exactly, in part, or is ruled out. Verdict explained / partly /
    unexplained. The fix is one line for Amir. Unexplained -> Needs you the same day."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    item = info["item"]; pack, packing = info["pack"], info["packing"]
    nm = norm_name(item)
    t = today().isoformat()
    anchor = last_point(con, nm, settled_only=True, gap_zero=True)
    fc = last_full_count(con)
    if anchor:
        anchor_at, anchor_text = anchor["at"], "the point of %s (%s, matched the records)" % (stamp(anchor["at"]), POINT_SOURCE_HI.get(anchor["source"], anchor["source"]))
    elif fc:
        anchor_at, anchor_text = fc["as_on"] + "T00:00:00", "the full count of %s" % dmy(fc["as_on"])
    else:
        anchor_at, anchor_text = (today() - dt.timedelta(days=90)).isoformat() + "T00:00:00", "90 days back (no count on record)"
    w_from = anchor_at[:10]
    gap = None if gap_units is None else float(gap_units)
    if gap is None:
        E = expected_units(con, sp, item)
        lp = last_point(con, nm)
''', '''def open_trace(con, item, trigger, gap_units, who, sp=None, note=None, point_id=None, count_id=None, quiet=False, E=None):
    """Rebuild from the anchor (the last settled point with gap 0, else the last closed full count) to now and run the
    seven checks in order; each explains the gap exactly, in part, or is ruled out. Verdict explained / partly /
    unexplained. The fix is one line for Amir. Unexplained -> Needs you the same day.
    S577: E is the point's own judgment (basis, as_on, expected -- from write_point); the window starts no earlier than that base, so the
    gap is traced on the figure it was measured against. Without E the point's basis is read from stock_figure.expect_for_point."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    item = info["item"]; pack, packing = info["pack"], info["packing"]
    nm = norm_name(item)
    t = today().isoformat()
    anchor = last_point(con, nm, settled_only=True, gap_zero=True)
    fc = last_full_count(con)
    if anchor:
        anchor_at, anchor_text = anchor["at"], "the point of %s (%s, matched the records)" % (stamp(anchor["at"]), POINT_SOURCE_HI.get(anchor["source"], anchor["source"]))
    elif fc:
        anchor_at, anchor_text = fc["as_on"] + "T00:00:00", "the full count of %s" % dmy(fc["as_on"])
    else:
        anchor_at, anchor_text = (today() - dt.timedelta(days=90)).isoformat() + "T00:00:00", "90 days back (no count on record)"
    w_from = anchor_at[:10]
    if E is None:
        try:
            E = _sf().expect_for_point(con, sp, item)
        except Exception:                                     # noqa: BLE001
            E = {}
    basis, basis_day = (E or {}).get("basis"), str((E or {}).get("as_on") or "")[:10]
    if basis in ("shelf", "marg") and basis_day and basis_day > w_from:
        w_from = basis_day                                    # S577: the window starts at the base the point was judged on
        anchor_text += "; judged on the %s of %s" % ("shelf figure" if basis == "shelf" else "Marg figure", dmy(basis_day))
    gap = None if gap_units is None else float(gap_units)
    if gap is None:
        lp = last_point(con, nm)
'''))
SW.append(("W19 open_trace: the basis in the findings", '''                      (nm, item, ts, trigger, anchor_at, w_from, window_to, gap, verdict, json.dumps(dict(anchor=anchor_text, findings=findings, sales=float(sales["u"] or 0), returns=float(sales.get("ret") or 0),
                                                                                                        purchases=sum(float(p["units"] or 0) for p in purch if p["direction"] != "RETURN"), note=note or "", point_id=point_id)),
''', '''                      (nm, item, ts, trigger, anchor_at, w_from, window_to, gap, verdict, json.dumps(dict(anchor=anchor_text, findings=findings, sales=float(sales["u"] or 0), returns=float(sales.get("ret") or 0),
                                                                                                        purchases=sum(float(p["units"] or 0) for p in purch if p["direction"] != "RETURN"), note=note or "", point_id=point_id,
                                                                                                        basis=basis, basis_day=basis_day or None)),
'''))
SW.append(("W20 owner_view: the approx lines", '''        return dict(ok=True, plan=P, roster_today=R, next_day=(nxt.isoformat() if nxt else None), next_day_text=(dmy(nxt.isoformat()) if nxt else ""),
                    roster_next=(preview_roster(con, nxt, S, sp) if nxt else []), watch=watch_list(con, S, sp, root), watch_left_out=list(LAST_LEFT_OUT),
''', '''        approx_lines = ["%s: counted %s against a family figure (approximate) \\u2014 not judged" % (r[0], qw(r[1], int(r[2] or 1), r[3] or "", r[0]))
                        for r in con.execute("SELECT p.item, p.qty_units, COALESCE(s.pack,1), COALESCE(s.packing,'') FROM stock_point p LEFT JOIN stock_spot_roster s ON s.point_id=p.id "
                                             "WHERE p.basis='approx' AND p.status<>'superseded' AND p.at>=? ORDER BY p.id DESC LIMIT 12", ((t - dt.timedelta(days=30)).isoformat(),))]   # S577
        return dict(ok=True, plan=P, roster_today=R, next_day=(nxt.isoformat() if nxt else None), next_day_text=(dmy(nxt.isoformat()) if nxt else ""),
                    roster_next=(preview_roster(con, nxt, S, sp) if nxt else []), watch=watch_list(con, S, sp, root), watch_left_out=list(LAST_LEFT_OUT), approx_lines=approx_lines,
'''))
SW.append(("W21 _s454_expected -> expect_for_point", '''def _s454_expected(con, sp, item):
    E = expected_units(con, sp, item)
    try:
        import shelf_figure                                   # noqa: PLC0415
        f = (shelf_figure.figures(con, sp=sp, items=[item]) or {}).get(item) or {}
        if f.get("shelf") is not None and f.get("named") not in ("no_count", "no_spine"):
            E = dict(E, expected=float(f["shelf"]), provisional=float(f.get("arrived") or 0), as_on=f.get("base_day"), close=f.get("base"),
                     sold=float(f.get("sold") or 0), bought=float(f.get("bought") or 0), basis="shelf", records=E.get("expected"))
    except Exception:                                         # noqa: BLE001 -- the count is never refused for it
        pass
    return E
''', '''def _s454_expected(con, sp, item):
    """S577: stock_figure.expect_for_point -- basis 'shelf' (a counted item: the shelf figure), 'marg' (uncounted: Marg's figure by the
    one capture rule, plus taps) or 'approx' (a size that shares a family figure: no figure, no verdict). Fail-soft: no figure at all."""
    try:
        return _sf().expect_for_point(con, sp, item)
    except Exception:                                         # noqa: BLE001 -- the count is never refused for it
        return dict(expected=None, provisional=0.0, as_on=None, close=None, sold=0.0, bought=0.0, basis=None, records=None, terms=[])
'''))
SW.append(("W22 _s454_gap_flag", '''def _s454_gap_flag(con, nm):
    try:
        import shelf_figure                                   # noqa: PLC0415
        return shelf_figure.gap_flag(con, nm)
    except Exception:                                         # noqa: BLE001
        return 0
''', '''def _s454_gap_flag(con, nm, ctx=None):
    try:
        import shelf_figure                                   # noqa: PLC0415
        return shelf_figure.gap_flag(con, nm, ctx)
    except Exception:                                         # noqa: BLE001
        return 0
'''))
SW.append(("W23 _candidates: one ctx for the flags", '''    out = {}
    for it in sp.items():
        k = it["k20"]
        if k in out:
            continue
        pack = pack_of(it["packing"])
''', '''    out = {}
    gctx = _sf().Ctx(con, sp)                                  # S577: one context for the roster's gap-flag reads
    for it in sp.items():
        k = it["k20"]
        if k in out:
            continue
        pack = pack_of(it["packing"])
'''))
SW.append(("W24 _candidates: the flag read", '''                      loss=short_last.get(nm, 0), value=1 if (mrp and mrp >= S["high_value_p"]) else 0, mrp_p=mrp, stale=since_days, last_point=lp, gap=_s454_gap_flag(con, nm))
''', '''                      loss=short_last.get(nm, 0), value=1 if (mrp and mrp >= S["high_value_p"]) else 0, mrp_p=mrp, stale=since_days, last_point=lp, gap=_s454_gap_flag(con, nm, gctx))
'''))

# =============================================================================================================== loss_piles.py
LP = []
LP.append(("L1 version", '''VERSION = "2.4"
KIT = "S437_COUNT_PAGES_FINAL"                                 # v2.3 was S436_STAFF_PAGES_CLEAN, v2.2 S432_DESK_GROUP_FLOW
''', '''VERSION = "2.5"
KIT = "S577_STOCK_ON_SPINE"                                    # v2.4 was S437_COUNT_PAGES_FINAL, v2.3 S436_STAFF_PAGES_CLEAN
# v2.5 (S577, 18-Oct-2026, F-841): THE DESK ONLY READS. The full build writes stock_pile_cache and _meta and nothing else: sales_test is
# gone (it wrote stock_shelf_fix / stock_sales_test / stock_diff words into count #1 on nearly every read, because the stamp's spine part was
# spine.db's mtime -- moved by every passing build). A line that sold more than was counted stays open in its pile and says so in its why
# ("sold after count: ...") for the owner's decision. The stamp's spine part is now the md5 of the spine's INPUTS (its ok exports, its rules
# version, its aliases). One new setting: stock.voucher_shelf_tol_packs (the voucher guard's shelf tolerance; the default is read, no row).
'''))
LP.append(("L2 the tolerance setting", '''    dict(key="stock.voucher_batch", label="Lines per Marg voucher", kind="int", default="6", seed="6", lo=1, hi=8,
         hint="How many lines Amir enters on one Marg voucher (Marg prints six to eight)."),
''', '''    dict(key="stock.voucher_batch", label="Lines per Marg voucher", kind="int", default="6", seed="6", lo=1, hi=8,
         hint="How many lines Amir enters on one Marg voucher (Marg prints six to eight)."),
    dict(key="stock.voucher_shelf_tol_packs", label="Voucher guard: shelf tolerance (packs)", kind="int", default="1", seed=None, lo=0, hi=5,
         hint="S577: a voucher line is held for you, never given to Amir, when it would take Marg past the shelf figure by more than this many "
              "packs (strips, or pcs). 0 = exact. The default is read until you set it (no row is written for it)."),
'''))
LP.append(("L3 settings(): the tolerance", '''                voucher_batch=max(1, min(8, num("stock.voucher_batch", 6))), accept_back_by=who,
                staff_block_items=max(1, num("stock.staff_block_items", 20)))
''', '''                voucher_batch=max(1, min(8, num("stock.voucher_batch", 6))), accept_back_by=who,
                staff_block_items=max(1, num("stock.staff_block_items", 20)),
                voucher_shelf_tol_packs=max(0.0, min(5.0, num("stock.voucher_shelf_tol_packs", 1.0, float))))    # S577
'''))
LP.append(("L4 _classify_one: sold after count, the owner's line", '''    if f and f["source"] == "recount":
        why = "recounted by %s: %s on the shelf -- %s" % (f["by"] or "Darpan", qw(f["qty"], pack, packing, item), why)
    base.update(bucket=pile, pile=pile, group=group, why=why, sent=C["shares"].get(item))
    return "line", base
''', '''    if f and f["source"] == "recount":
        why = "recounted by %s: %s on the shelf -- %s" % (f["by"] or "Darpan", qw(f["qty"], pack, packing, item), why)
    sa_ = _sold_after(con, x, C)                                # S577 (F-841): what sales_test used to CLOSE by itself is now said, and left to the owner
    if sa_:
        base["sold_after"] = sa_
        why = "sold after count: %s sold since %s against %s counted + %s bought -- %s" % (
            qw(sa_["sold"], pack, packing, item), sa._r_dmy(sa_["as_on"]), qw(sa_["counted"], pack, packing, item), qw(sa_["bought"], pack, packing, item), why)
    base.update(bucket=pile, pile=pile, group=group, why=why, sent=C["shares"].get(item))
    return "line", base


def _sold_after(con, x, C):
    """S577 (F-841): dict(sold, bought, counted, as_on) when the item's sales since the count day exceed counted + bought since -- the stock
    existed, the count was short. sales_test closed such a line by itself (and corrected the shelf to Marg's figure); now the line stays open
    in its pile and its why says so, for the owner's existing doors. None otherwise, and never for an orthotic line or a line with a word."""
    try:
        sp = C["sp"]
        as_on = C.get("as_on")
        upto = dt.date.today().isoformat()
        if not sp.ok or not as_on or as_on >= upto or int(x.get("diff") or 0) >= 0:
            return None
        sold = sp.sales(x["item"], as_on, upto, incl_from=False)
        if sold is None:
            return None
        bought = max(0.0, float(sp.purchases(x["item"], as_on, upto) or 0.0))
        counted = int(x["counted"])
        if sold[0] <= counted + bought:
            return None
        return dict(sold=sold[0], bought=bought, counted=counted, as_on=as_on)
    except Exception:                                         # noqa: BLE001 -- a line is never lost for it
        return None
'''))
LP.append(("L5 the stamp's spine part", '''def _spine_stamp():
    p = SPINE_DB
    try:
        st = os.stat(p)
        return "%d:%d" % (int(st.st_mtime * 1000), st.st_size)
    except OSError:
        return "none"
''', '''def _spine_stamp():
    """S577 (R2 on R1-C1): the md5 of the spine's INPUTS -- the sorted md5 list of its ok=1 exports, its rules version (sp_meta) and its
    sorted aliases -- read from spine.db. A rebuild of the same inputs no longer rebuilds the desk; a new export, a rules change or a rename
    tick does. 'none' when the spine cannot be read."""
    p = SPINE_DB
    try:
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
        try:
            ex = [str(r[0]) for r in c.execute("SELECT md5 FROM sp_export WHERE ok=1 ORDER BY md5")]
            rv = c.execute("SELECT value FROM sp_meta WHERE key='rules_version'").fetchone()
            al = ["%s=%s" % (r[0], r[1]) for r in c.execute("SELECT alias, k20 FROM sp_alias ORDER BY alias, k20")]
        finally:
            c.close()
        return hashlib.md5(("|".join(ex) + "#" + str(rv[0] if rv else "") + "#" + "|".join(al)).encode("utf-8")).hexdigest()
    except sqlite3.Error:
        return "none"
'''))
LP.append(("L6 rebuild(): the desk only reads", '''def rebuild(con, root, who="system", d=None, sp=None):
    """THE FULL BUILD: the report once, the sales-after-count test on it (a hit -> the report once more), classify with the
    spine prefetched, every row written in ONE transaction with the stamp. Returns (lines, over, skipped, info)."""
    sa = _sa()
    t0 = dt.datetime.now()
    sp = sp or Spine()
    d = d or sa._pad_report_data(con, root)
    if d is None:
        return None
    hits = sales_test(con, root, d=d, sp=sp, who="system")
    if hits:
        d = sa._pad_report_data(con, root)
    S = settings(con)
''', '''def rebuild(con, root, who="system", d=None, sp=None):
    """THE FULL BUILD: the report once, classify with the spine prefetched, every row written in ONE transaction with the stamp. Writes
    stock_pile_cache and stock_pile_cache_meta and NOTHING ELSE (S577, F-841: the desk only reads; sales_test is gone). Returns
    (lines, over, skipped, info)."""
    sa = _sa()
    t0 = dt.datetime.now()
    sp = sp or Spine()
    d = d or sa._pad_report_data(con, root)
    if d is None:
        return None
    S = settings(con)
'''))
LP.append(("L7 rebuild(): info", '''    con.commit()
    return lines, over, skipped, dict(built="full", ms=ms, built_at=ts, sales_hits=hits, lines_n=len(lines))
''', '''    con.commit()
    return lines, over, skipped, dict(built="full", ms=ms, built_at=ts, lines_n=len(lines))
'''))
LP.append(("L8 sales_test removed", '''def sales_test(con, root, d=None, sp=None, who="system"):
    """A line whose sales since the count day exceed counted + bought since: the stock existed, the count was short.
    Closed by the system -- EXPLAINED, cause FOUND, shelf = Marg, audited 'system: sold after count' -- before piling.
    Idempotent: a closed line has a word and is skipped. Returns the items closed on this call; never raises.
    S432: runs inside the cache's full build (a spine rebuild changes the stamp), not on every read."""
    try:
        sa = _sa()
        ensure(con)
        d = d or sa._pad_report_data(con, root)
        if d is None:
            return []
        sp = sp or Spine()
        if not sp.ok:
            return []
        as_on = _as_on_iso(con, root, d)
        upto = dt.date.today().isoformat()
        if not as_on or as_on >= upto:
            return []
        ts, done = now_iso(), []
        for x in d["differences"]:
            rem = int(x["diff"] or 0)
            if rem >= 0 or is_ortho(con, x):
                continue
            act = (x.get("word") or {}).get("action")
            if act in ("WRITE_OFF", "EXPLAINED", "MARG_FIX"):
                continue
            sold = sp.sales(x["item"], as_on, upto, incl_from=False)
            bought = sp.purchases(x["item"], as_on, upto)
            if sold is None:
                continue
            sold_n = sold[0]
            bought_n = max(0.0, bought or 0.0)
            counted = int(x["counted"])
            if sold_n <= counted + bought_n:
                continue
            item, pack, packing = x["item"], int(x.get("pack") or 1), x.get("packing") or ""
            note = "system: sold after count -- %s sold since %s against %s counted + %s bought (S427)" % (
                qw(sold_n, pack, packing, item), sa._r_dmy(as_on), qw(counted, pack, packing, item), qw(bought_n, pack, packing, item))
            did = _word(con, root, item, "EXPLAINED", note, who, ts, close=True)
            if did:
                con.execute("UPDATE stock_diff SET cause='FOUND', cause_note=?, cause_by=?, cause_at=? WHERE id=?", (note, who, ts, did))
            con.execute("INSERT INTO stock_shelf_fix (count_id, item, qty, source, note, by_user, at) VALUES (?,?,?,?,?,?,?)",
                        (root, item, int(x["marg"]), "sales_test", note, who, ts))
            con.execute("INSERT INTO stock_sales_test (count_id, item, at, counted, marg, sold_after, bought_after, as_on, upto, diff_id) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)", (root, item, ts, counted, int(x["marg"]), sold_n, bought_n, as_on, upto, did))
            _audit(con, root, "sales_test", dict(item=item, diff_id=did, counted=counted, sold_after=sold_n, bought_after=bought_n, marg=x["marg"],
                                                 text="%s closed by the system: %s" % (item, note[8:])), who)
            done.append(item)
        con.commit()
        return done
    except Exception:                                         # noqa: BLE001 -- the test is never worth a broken desk
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        return []


''', ''''''))
LP.append(("L9 _desk_from: the owner's line about the system's two closings", '''    out.update(done=dict(back=sorted([l for l in lines if l["bucket"] == "back"], key=_sortkey),
                         written_off=sorted([l for l in lines if l["bucket"] == "written_off"], key=lambda l: (l["group"], -(l["mrp_p"] or 0), l["item"]))),
               over=over, sold_after=sorted([l for l in lines if l.get("test")], key=_sortkey),
               settings=settings_view(con), record=record(con, d, lines=lines))
    return out
''', '''    out.update(done=dict(back=sorted([l for l in lines if l["bucket"] == "back"], key=_sortkey),
                         written_off=sorted([l for l in lines if l["bucket"] == "written_off"], key=lambda l: (l["group"], -(l["mrp_p"] or 0), l["item"]))),
               over=over, sold_after=sorted([l for l in lines if l.get("test")], key=_sortkey),
               settings=settings_view(con), record=record(con, d, lines=lines), system_closed=_system_closed(con, d["count_id"]))
    return out


def _system_closed(con, root):
    """S577 (F-841): the owner's one English line about the lines the system closed as 'sold after count' (stock_sales_test, a record):
    dict(n, items, day, text) or None. From now on such lines are his to decide (the why of an open line says 'sold after count: ...')."""
    try:
        rows = con.execute("SELECT item, at FROM stock_sales_test WHERE count_id=? ORDER BY id", (int(root),)).fetchall()
    except sqlite3.Error:
        return None
    if not rows:
        return None
    days = sorted({str(r[1] or "")[:10] for r in rows})
    day = ", ".join("%s-%s" % (d[8:10], d[5:7]) for d in days if len(d) == 10) or "?"
    items = [str(r[0]) for r in rows]
    return dict(n=len(rows), items=items, day=day,
                text="%d line%s %s closed by the system on %s as 'sold after count' (%s); from now on such lines are yours to decide."
                % (len(rows), "" if len(rows) == 1 else "s", "was" if len(rows) == 1 else "were", day, ", ".join(items)))
'''))

# =============================================================================================================== stock_app.py
SA = []
SA.append(("A1 the stock_figure import", '''# --- S428_STOCK_WATCH end --------------------------------------------------
''', '''# --- S428_STOCK_WATCH end --------------------------------------------------

# --- S577_STOCK_ON_SPINE begin (rung 4b) -----------------------------------
# THE one stock function (stock_figure.py beside this file): Marg's figure and the shelf figure, each on the closing it stands on, by printed
# name over the spine's own captures; the one capture rule and the one identity live there. A hard dependency: the voucher guard, the stage
# proof's helpers and the stock-now / drift pages read it, and the kit places it in the same move as this file.
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import stock_figure as _sf                                 # noqa: E402
# --- S577_STOCK_ON_SPINE end -----------------------------------------------
'''))
SA.append(("A2 _voucher_lines", '''def _voucher_lines(con, d, section=None, items=None):
    """(offered, held, unread) -- the count-day sum judged ONCE per item. offered = the lines the next round would carry: per item, what
    the Marg cleanup list now needs minus what earlier rounds already moved. Ordered section, family, item.
    S404: with `section` ('Orthotics'), that section's lines only -- the rest stay for their own round.
    S537 (charter 1b, 5, 12): an item the owner settled for this count is skipped (stock_voucher_settle). A line that LOWERS Marg is HELD
    -- never offered, never frozen, never Amir's -- when Marg's newest closing of the item BY ITS FULL PRINTED NAME, plus the units of the
    count's vouchers already made but not yet in that closing, plus the line itself, would go below zero (_voucher_guard). A name absent
    from that closing is offered and listed in `unread` (the guard not applied; the owner's summary line). Writes nothing."""
''', '''def _voucher_lines(con, d, section=None, items=None, ctx=None):
    """(offered, held, unread) -- the count-day sum judged ONCE per item. offered = the lines the next round would carry: per item, what
    the Marg cleanup list now needs minus what earlier rounds already moved. Ordered section, family, item.
    S404: with `section` ('Orthotics'), that section's lines only -- the rest stay for their own round.
    S537 (charter 1b, 5, 12): an item the owner settled for this count is skipped (stock_voucher_settle). A line that LOWERS Marg is HELD
    -- never offered, never frozen, never Amir's -- when Marg's newest USABLE closing of the item by its printed name (stock_figure.closing,
    S577: a renamed item is judged under every form of its name), plus the units of the count's vouchers already made but not yet in that
    closing, plus the line itself, would go below zero (_voucher_guard, why='below_zero').
    S577 (D715 a, the second half): ANY line is held (why='past_shelf') when it would take Marg past the SHELF figure beyond the tolerance
    stock.voucher_shelf_tol_packs x pack -- judged only when the shelf figure is known, neither figure is approximate, no arrival is open and
    no late-keyed bill explains the residual; the rest are counted in `unread` with why='not_shelf' ("not judged against the shelf").
    While stock_figure.ready() is False every lowering line is held (why='not_ready'), never offered (R2-B7). A name the closing does not
    print is offered and listed in `unread` (why='unread'; the guard not applied; the owner's summary line). Writes nothing."""
'''))
SA.append(("A3 _voucher_lines: every line judged", '''        if ch < 0:                                             # S537 (R2-3): only a line that lowers Marg is tested
            if G is None:
                G = _voucher_guard_base(con, d["count_id"])
            g = _voucher_guard(G, item, ch)
            if g["held"]:
                held.append(dict(row, marg_now=g["marg_now"], as_on=g["as_on"], unkeyed=g["unkeyed"]))
                continue
            if g["unread"]:
                unread.append(dict(row, as_on=g["as_on"]))
        out.append(row)
''', '''        if G is None:                                          # S577: every line is tested -- below zero (ch < 0) and past the shelf (any ch)
            G = _voucher_guard_base(con, d["count_id"], ctx)
        g = _voucher_guard(G, item, ch, pack=row["pack"])
        if g["held"]:
            held.append(dict(row, why=g["why"], marg_now=g["marg_now"], as_on=g["as_on"], unkeyed=g["unkeyed"], shelf=g["shelf"], after=g["after"], taken=g["taken"]))
            continue
        if g["unread"]:
            unread.append(dict(row, as_on=g["as_on"], why="unread"))
        elif not g["judged_shelf"]:
            unread.append(dict(row, as_on=g["as_on"], why="not_shelf"))
        out.append(row)
'''))
SA.append(("A4 _voucher_pending; _voucher_held removed; the guard", '''def _voucher_pending(con, d, section=None, items=None):
    """The lines the next round would carry (S537: settled items skipped, held lines never here) -- _voucher_lines' offered."""
    return _voucher_lines(con, d, section, items)[0]


def _voucher_held(con, d, section=None):
    """S537: the lines the guard holds back from Amir (each named on the owner's Needs-you) -- _voucher_lines' held, the same loop."""
    return _voucher_lines(con, d, section)[1]


def _voucher_guard_base(con, root):
    """S537 (2.3): what the guard reads, once per judgment -- Marg's newest closing BY THE FULL PRINTED NAME (shelf_figure.latest_snapshot:
    the newest closing by its real date; a name it does not print is 'not readable', never an older figure; sizes stay apart -- the spine's
    20-letter key would fold them) and, per item, `unkeyed`: the units of the count's frozen lines (not voided) whose batch is not in that
    closing -- not entered, or first entered after the closing's day (they will move Marg too). Read only."""
    try:
        import shelf_figure                                    # noqa: PLC0415
        as_on, snap = shelf_figure.latest_snapshot(con)
    except Exception:                                          # noqa: BLE001 -- no closing readable: every line offered, the owner told
        as_on, snap = None, {}
    ent, win, unk = _s446_entered(con, int(root)), _s446_window(con, int(root)), {}
    for rno, kind, bno, item, ch in con.execute("SELECT l.round_no, l.kind, l.batch_no, l.item, l.change FROM stock_voucher_line l "
                                                "WHERE l.count_id=? AND " + _void_sql("l"), (int(root),)):
        k = (int(rno), str(kind), int(bno))
        if k in ent and as_on and str(win.get(k) or ent[k][1] or "")[:10] <= as_on:
            continue                                           # entered on or before the closing's day: already in it
        unk[item] = unk.get(item, 0) + int(ch or 0)
    return dict(as_on=as_on, snap=snap or {}, unkeyed=unk)


def _voucher_guard(G, item, ch, frozen=False):
    """S537: one line's test against _voucher_guard_base -> dict(held, unread, marg_now, as_on, unkeyed). Held when the line lowers Marg
    and marg_now + unkeyed (+ the line, unless it is a frozen line already inside unkeyed -- counted once) is below zero."""
    s = (G.get("snap") or {}).get(item)
    unk = int((G.get("unkeyed") or {}).get(item, 0))
    if s is None:
        return dict(held=False, unread=True, marg_now=None, as_on=G.get("as_on"), unkeyed=unk)
    m = int(s.get("qty") or 0)
    return dict(held=bool(ch < 0 and m + unk + (0 if frozen else ch) < 0), unread=False, marg_now=m, as_on=G.get("as_on"), unkeyed=unk)


def _voucher_held_batches(con, root, keys, batches, G=None):
    """S537 (R2-2): ({key: [held line]}, {unreadable item}) -- the frozen batches among `keys` with ANY line that fails _voucher_guard (the
    line's own change counted once inside unkeyed). Such a batch is never released to Amir: amir_stage's stage-C release and "Aur voucher
    kholiye" (_s452_release) skip it; the owner's line names it with its voucher number. Read only."""
    G = G or _voucher_guard_base(con, root)
    out, unread = {}, set()
    for k in keys:
        b = batches.get(k) or {}
        bad = []
        for item, ch, _mto in b.get("lines") or []:
            if int(ch) >= 0:
                continue
            g = _voucher_guard(G, item, int(ch), frozen=True)
            if g["unread"]:
                unread.add(item)
            if g["held"]:
                pk = (b.get("pk") or {}).get(item, ("", None))
                bad.append(dict(item=item, change=int(ch), packing=pk[0] or "", pack=pk[1] or 1, marg_now=g["marg_now"], as_on=g["as_on"],
                                unkeyed=g["unkeyed"], key=k))
        if bad:
            out[k] = bad
    return out, unread
''', '''def _voucher_pending(con, d, section=None, items=None, ctx=None):
    """The lines the next round would carry (S537: settled items skipped, held lines never here) -- _voucher_lines' offered."""
    return _voucher_lines(con, d, section, items, ctx)[0]


def _voucher_guard_base(con, root, ctx=None):
    """S577 (D715 a; F-874): what the guard reads, once per judgment. ready = stock_figure.ready (the spine's closing table); cap = the newest
    USABLE capture (the one capture rule); per item (lazily, through _voucher_guard) stock_figure.closing / marg / shelf by every printed form
    of the name (a renamed item is judged; the day shown is the capture's printed as_on, as the S524 header says); `unkeyed`: the units of the
    count's frozen lines (not voided) whose batch is not in that capture -- not entered, or first entered (_s446_window) after the capture's
    MOMENT (known limit, R2-C18: a voucher typed in Marg before the capture but recorded here after it is counted twice; no grace); tol_packs
    = stock.voucher_shelf_tol_packs (the default is read: no row written). Read only."""
    sp = ctx.sp if (ctx is not None and ctx.sp is not None) else _s524_spine()
    ctx = ctx if ctx is not None else _sf.Ctx(con, sp)
    if ctx.con is None:
        ctx.con = con
    if ctx.sp is None:
        ctx.sp = sp
    ready = _sf.ready(sp)
    cap = _sf.capture_at(sp, None, ctx) if ready else None
    ent, win, unk = _s446_entered(con, int(root)), _s446_window(con, int(root)), {}
    for rno, kind, bno, item, ch in con.execute("SELECT l.round_no, l.kind, l.batch_no, l.item, l.change FROM stock_voucher_line l "
                                                "WHERE l.count_id=? AND " + _void_sql("l"), (int(root),)):
        k = (int(rno), str(kind), int(bno))
        if k in ent and cap and str(win.get(k) or ent[k][1] or "")[:19] <= cap["stamp_iso"]:
            continue                                           # entered at or before the capture's moment: already in it
        unk[item] = unk.get(item, 0) + int(ch or 0)
    try:
        tol = float(_lp.settings(con)["voucher_shelf_tol_packs"]) if LOSS_PILES_OK else 1.0
    except Exception:                                          # noqa: BLE001
        tol = 1.0
    return dict(ready=ready, ctx=ctx, cap=cap, as_on=(cap["as_on"] if cap else None), unkeyed=unk, tol_packs=tol, not_judged=set())


def _voucher_guard(G, item, ch, frozen=False, pack=1):
    """One line's test against _voucher_guard_base -> dict(held, why, unread, marg_now, as_on, taken, unkeyed, shelf, after, judged_shelf).
    not ready -> a lowering line is held (why='not_ready'). Below zero (ch < 0; S537's meaning): m + unk + (0 if frozen else ch) < 0 with
    m = closing().units (why='below_zero'); a closing read by key (a family sum hides one size) counts as unread for it, as does a name the
    capture does not print. Past the shelf (S577, any ch): after = marg.figure + unk + (0 if frozen else ch); held when ch < 0 and
    after < shelf - tol, or ch > 0 and after > shelf + tol (why='past_shelf'); applied only when the shelf is known, neither figure is
    approximate, no arrival is open, no late-keyed bill explains the residual and the capture is not an early-morning one holding a bill
    of its own day -- else the item is 'not judged against the shelf' (judged_shelf False, G['not_judged'])."""
    unk = int((G.get("unkeyed") or {}).get(item, 0))
    out = dict(held=False, why=None, unread=False, marg_now=None, as_on=G.get("as_on"), taken=None, unkeyed=unk, shelf=None, after=None, judged_shelf=False)
    if not G.get("ready"):
        if ch < 0:
            out.update(held=True, why="not_ready")
        return out
    ctx = G["ctx"]
    con, sp = ctx.con, ctx.sp
    e = ctx.c.get(("guard", item))
    if e is None:
        c = _sf.closing(con, sp, item, None, ctx)
        e = dict(closing=c, marg=(_sf.marg(con, sp, item, None, ctx) if c else None), shelf=(_sf.shelf(con, sp, item, None, ctx) if c else None))
        ctx.c[("guard", item)] = e
    c = e["closing"]
    if c is None:
        out["unread"] = ch < 0
        G["not_judged"].add(item)
        return out
    out.update(marg_now=c["units"], as_on=c["as_on"], taken=c["stamp_iso"])
    if ch < 0:
        if c["by"] == "key":
            out["unread"] = True                               # R2-C5: a family sum hides one size -- the below-zero test is not applied
        elif float(c["units"]) + unk + (0 if frozen else ch) < 0:
            out.update(held=True, why="below_zero")
            return out
    M, S = e["marg"], e["shelf"]
    sh = (S or {}).get("shelf")
    if M is None or S is None or sh is None or M.get("approx") or S.get("approx") or float(S.get("arrived") or 0) != 0:
        G["not_judged"].add(item)
        return out
    after = float(M["figure"]) + unk + (0 if frozen else ch)
    tol = float(G.get("tol_packs") or 0) * max(1, int(pack or 1))
    if _sf.early_bill(sp, M["key"], c) or _sf.late_purchase(con, sp, item, c, after, sh, tol, ctx):
        G["not_judged"].add(item)
        return out
    out.update(shelf=float(sh), after=after, judged_shelf=True)
    if (ch < 0 and after < float(sh) - tol) or (ch > 0 and after > float(sh) + tol):
        out.update(held=True, why="past_shelf")
    return out


def _voucher_held_batches(con, root, keys, batches, G=None, ctx=None):
    """S537 (R2-2) / S577: ({key: [held line]}, {unreadable item}) -- the frozen batches among `keys` with ANY line that fails _voucher_guard
    (frozen=True: the line's own change counted once inside unkeyed; below zero for ISSUE lines, past the shelf for any line). Such a batch is
    never released to Amir: amir_stage's stage-C release and "Aur voucher kholiye" (_s452_release) skip it; the owner's line names it with its
    voucher number. Read only."""
    G = G or _voucher_guard_base(con, root, ctx)
    out, unread = {}, set()
    for k in keys:
        b = batches.get(k) or {}
        bad = []
        for item, ch, _mto in b.get("lines") or []:
            pk = (b.get("pk") or {}).get(item, ("", None))
            g = _voucher_guard(G, item, int(ch), frozen=True, pack=pk[1] or 1)
            if g["unread"] and int(ch) < 0:
                unread.add(item)
            if g["held"]:
                bad.append(dict(item=item, change=int(ch), packing=pk[0] or "", pack=pk[1] or 1, marg_now=g["marg_now"], as_on=g["as_on"],
                                unkeyed=g["unkeyed"], key=k, why=g["why"], shelf=g["shelf"], after=g["after"], taken=g["taken"]))
        if bad:
            out[k] = bad
    return out, unread
'''))
SA.append(("A5 amir_stage: ctx", '''def amir_stage(con, cid=None, d=None):
    """Where the count stands for Amir: {count_id, stage A|B|C|done, A, B, C, visible (keys his board lists), renames_visible,
    numbers {key: n}}. Writes only stock_stage_event (a verification seen, a recheck, a lot released) -- once each.
''', '''def amir_stage(con, cid=None, d=None, ctx=None):
    """Where the count stands for Amir: {count_id, stage A|B|C|done, A, B, C, visible (keys his board lists), renames_visible,
    numbers {key: n}}. Writes only stock_stage_event (a verification seen, a recheck, a lot released) -- once each.
    S577: one stock_figure context (ctx) for every guard read of this call -- built here when the caller passes none.
'''))
SA.append(("A6 amir_stage: A's guard reads", '''    _sq = _voucher_seq(con, root)                              # S528 (3.6): ONE numbering -- the stage decides what is shown, never how it is numbered
    # ---- A
    a_open = [k for k in ortho if k not in ent]
    A = dict(total=len(ortho), entered=len(ortho) - len(a_open), open=len(a_open), pending=0, proof=None,
             verified_at=_s446_event(con, root, "A", "verified"))
    rep = d if d is not None else _report_cached(con, root)
    A["held"], A["unread"] = [], 0                             # S537 (2.3): the lines the guard holds back -- the owner's, never pending
    if rep is not None:
        try:
            _o, _h, _u = _voucher_lines(con, rep, section="Orthotics")
            A["pending"], A["held"], A["unread"] = len(_o), _h, len(_u)
        except Exception:                                      # noqa: BLE001
            A["pending"] = 0
''', '''    _sq = _voucher_seq(con, root)                              # S528 (3.6): ONE numbering -- the stage decides what is shown, never how it is numbered
    ctx = ctx if ctx is not None else _sf.Ctx(con, _s524_spine())   # S577: one context for every guard read below
    # ---- A
    a_open = [k for k in ortho if k not in ent]
    A = dict(total=len(ortho), entered=len(ortho) - len(a_open), open=len(a_open), pending=0, proof=None,
             verified_at=_s446_event(con, root, "A", "verified"))
    rep = d if d is not None else _report_cached(con, root)
    A["held"], A["unread"], A["not_shelf"] = [], 0, 0           # S537 (2.3) / S577: the lines the guard holds back -- the owner's, never pending
    if rep is not None:
        try:
            _o, _h, _u = _voucher_lines(con, rep, section="Orthotics", ctx=ctx)
            A["pending"], A["held"] = len(_o), _h
            A["unread"], A["not_shelf"] = len([u for u in _u if u.get("why") != "not_shelf"]), len([u for u in _u if u.get("why") == "not_shelf"])
        except Exception:                                      # noqa: BLE001
            A["pending"] = 0
'''))
SA.append(("A7 amir_stage: C's guard reads", '''    held_c, unread_c = _voucher_held_batches(con, root, [k for k in med if k not in released and k not in ent], batches)
''', '''    G_c = _voucher_guard_base(con, root, ctx)                  # S577: the one guard reading of this call
    held_c, unread_c = _voucher_held_batches(con, root, [k for k in med if k not in released and k not in ent], batches, G=G_c)
'''))
SA.append(("A8 amir_stage: C's counts", '''    C["held"] = [dict(l, seq=(_sq.get(k) or (0,))[0]) for k in _s446_order(held_c) for l in held_c[k]]
    C["unread"] = len(unread_c)
    if rep is not None:
        try:
            _o, _h, _u = _voucher_lines(con, rep)
            _a = {h["item"] for h in A.get("held") or []}
            C["held"] += [h for h in _h if h["item"] not in _a]
            C["unread"] = len(unread_c | {u["item"] for u in _u})
        except Exception:                                      # noqa: BLE001
            pass
''', '''    C["held"] = [dict(l, seq=(_sq.get(k) or (0,))[0]) for k in _s446_order(held_c) for l in held_c[k]]
    C["unread"], C["not_shelf"] = len(unread_c), len(G_c["not_judged"])
    if rep is not None:
        try:
            _o, _h, _u = _voucher_lines(con, rep, ctx=ctx)
            _a = {h["item"] for h in A.get("held") or []}
            C["held"] += [h for h in _h if h["item"] not in _a]
            C["unread"] = len(unread_c | {u["item"] for u in _u if u.get("why") != "not_shelf"})
            C["not_shelf"] = len(G_c["not_judged"] | {u["item"] for u in _u if u.get("why") == "not_shelf"})
        except Exception:                                      # noqa: BLE001
            pass
'''))
SA.append(("A9 stage words: the held lines by their why", '''        G_ = (A if stage == "A" else C if stage == "C" else {})
        for h in G_.get("held") or []:
            vn = (" (%s voucher %d)" % (VOUCHER_HI.get(h["key"][1], h["key"][1]), int(h["seq"]))) if h.get("key") and h.get("seq") else ""
            owner_lines.append(dict(cls="warn", target="stock", text="Count #%d: %s%s \\u2014 the count-day sum asks %s; Marg's closing of %s holds %s: not given to Amir"
                                    % (root, h.get("item"), vn, _s528_qty_en(h.get("change"), h.get("item"), h.get("packing"), h.get("pack")),
                                       _s524_dmy(h.get("as_on"))[:5], _s537_qty_en(h.get("marg_now"), h.get("item"), h.get("packing"), h.get("pack")))))
        if int(G_.get("unread") or 0):
            owner_lines.append(dict(cls="info", target="stock", text="Count #%d: closing not readable for %d item(s) \\u2014 guard not applied"
                                    % (root, int(G_["unread"]))))
''', '''        G_ = (A if stage == "A" else C if stage == "C" else {})
        for h in G_.get("held") or []:
            vn = (" (%s voucher %d)" % (VOUCHER_HI.get(h["key"][1], h["key"][1]), int(h["seq"]))) if h.get("key") and h.get("seq") else ""
            why = h.get("why") or "below_zero"
            if why == "not_ready":                             # S577 (R3-C8): the spine's closing table is not ready -- held, never offered
                owner_lines.append(dict(cls="warn", target="stock", text="Count #%d: %s%s \\u2014 held: the spine's closing table is not ready yet" % (root, h.get("item"), vn)))
            elif why == "past_shelf":                          # S577 (D715 a): it would take Marg past the shelf figure
                tk = str(h.get("taken") or "")
                owner_lines.append(dict(cls="warn", target="stock", text="Count #%d: %s%s \\u2014 the count-day sum asks %s; it would take Marg to %s against the shelf figure %s (closing of %s, taken %s): not given to Amir"
                                        % (root, h.get("item"), vn, _s528_qty_en(h.get("change"), h.get("item"), h.get("packing"), h.get("pack")),
                                           _s537_qty_en(h.get("after"), h.get("item"), h.get("packing"), h.get("pack")), _s537_qty_en(h.get("shelf"), h.get("item"), h.get("packing"), h.get("pack")),
                                           _s524_dmy(h.get("as_on"))[:5], (tk[11:16] if len(tk) >= 16 else "?"))))
            else:
                owner_lines.append(dict(cls="warn", target="stock", text="Count #%d: %s%s \\u2014 the count-day sum asks %s; Marg's closing of %s holds %s: not given to Amir"
                                        % (root, h.get("item"), vn, _s528_qty_en(h.get("change"), h.get("item"), h.get("packing"), h.get("pack")),
                                           _s524_dmy(h.get("as_on"))[:5], _s537_qty_en(h.get("marg_now"), h.get("item"), h.get("packing"), h.get("pack")))))
        if int(G_.get("unread") or 0):
            owner_lines.append(dict(cls="info", target="stock", text="Count #%d: closing not readable for %d item(s) \\u2014 guard not applied"
                                    % (root, int(G_["unread"]))))
        if int(G_.get("not_shelf") or 0):                      # S577: the items the past-the-shelf test could not judge
            owner_lines.append(dict(cls="info", target="stock", text="Count #%d: not judged against the shelf for %d item(s) (a family figure, no count, goods not yet billed, or a bill keyed after the closing)"
                                    % (root, int(G_["not_shelf"]))))
'''))
SA.append(("A10 the capture rule and the reach: one-line wrappers", '''def _s524_stamp_iso(stamp):
    """'YYYYMMDD-HHMMSS' -> 'YYYY-MM-DDTHH:MM:SS' (exactly as marg_take.py reads a capture); '' when it is not a stamp."""
    s = str(stamp or "")
    if not _re221.match(r"^\\d{8}-\\d{6}$", s):
        return ""
    return "%s-%s-%sT%s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])


def _s524_end_day(as_on, stamp_iso):
    """push_expected._gap_side as the one capture-hour rule: the day whose END the closing's figure stands for, or None when the capture
    fell inside that day's shop hours (a same-day print between 09:00 and 22:00; a print dated after its capture) -- then it is skipped."""
    sd, hm = str(stamp_iso)[:10], str(stamp_iso)[11:16]
    if len(sd) != 10 or len(str(as_on)) != 10:
        return None
    if as_on < sd:                                             # printed for an earlier day: the whole day was before the capture
        return as_on
    if as_on > sd:
        return None
    if hm >= "22:00":
        return as_on
    if hm < "09:00":
        try:
            return (dt.date.fromisoformat(as_on) - dt.timedelta(days=1)).isoformat()
        except ValueError:
            return None
    return None
''', '''def _s524_stamp_iso(stamp):
    """S577: stock_figure.stamp_iso -- the one stamp parser ('YYYYMMDD-HHMMSS' -> ISO; '' when it is not a stamp)."""
    return _sf.stamp_iso(stamp)


def _s524_end_day(as_on, stamp_iso):
    """S577: stock_figure.end_day -- the one capture rule (charter 11), moved verbatim; None for a mid-day capture."""
    return _sf.end_day(as_on, stamp_iso)
'''))
SA.append(("A11 the reach wrappers", '''def _s524_reach(sp):
    """{last_sale, sale_stamp, last_pur, pur_stamp}: last_sale = MAX(date_to) over ok=1 SALE_BILLWISE; last_pur = MIN of MAX(date_to) over ok=1
    PURCHASE_BILLWISE and over ok=1 PURCHASE_ITEMWISE|PURCHASE_BILLITEMWISE (spine_build.py 377-378); the stamps are those newest exports'."""
    def last(fam_sql):
        return str(sp.q("SELECT MAX(date_to) AS d FROM sp_export WHERE ok=1 AND " + fam_sql)[0]["d"] or "")

    def stamp_of(fam_sql, d):
        return str(sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND date_to=? AND " + fam_sql, d)[0]["s"] or "") if d else ""
    S, B, I = "family='SALE_BILLWISE'", "family='PURCHASE_BILLWISE'", "family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')"
    ls, lb, li = last(S), last(B), last(I)
    lp = min(lb, li) if (lb and li) else ""
    return dict(last_sale=ls, sale_stamp=stamp_of(S, ls), last_pur=lp, pur_stamp=(min(stamp_of(B, lb), stamp_of(I, li)) if lp else ""))


def _s570_covers(day, stamp, c, d):
    """S570 (F-905): the newest export of a family (reaching `day`, captured at `stamp`) covers the closing `c` (end_day `d`) when it was
    captured after the closing, OR when its own capture, read by the estate's one capture rule (_s524_end_day, charter 11), stands for the
    end of a day at or after d. The morning order -- the sale report ~05:10, the closing ~05:17, both the end of yesterday -- is covered;
    a same-day capture inside shop hours gives None, and None never covers."""
    if stamp > c["stamp"]:
        return True
    e = _s524_end_day(str(day or ""), _s524_stamp_iso(stamp))
    return e is not None and e >= d


def _s524_tryable(c, reach):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): last_sale and last_pur at or past its end_day, and
    both newest exports cover it (_s570_covers: captured after it, or standing by their own capture for the end of a day at or after its
    end_day -- S570, F-905). short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach:
        return False, "sale"
    if reach["last_sale"] < d or not _s570_covers(reach["last_sale"], reach["sale_stamp"], c, d):
        return False, "sale"
    if not reach["last_pur"] or reach["last_pur"] < d or not _s570_covers(reach["last_pur"], reach["pur_stamp"], c, d):
        return False, "pur"
    return True, ""
''', '''def _s524_reach(sp):
    """S577: stock_figure.reach -- the spine's sale and purchase reach, moved verbatim."""
    return _sf.reach(sp)


def _s570_covers(day, stamp, c, d):
    """S577: stock_figure.covers (S570, F-905), moved verbatim."""
    return _sf.covers(day, stamp, c, d)


def _s524_tryable(c, reach):
    """S577: stock_figure.tryable -- (ok, short), moved verbatim; record_gaps reads the same rule (charter 1b)."""
    return _sf.tryable(c, reach)
'''))
SA.append(("A12 _s524_key_of -> key_of", '''def _s524_key_of(sp, item, cache):
    """The spine's own key of an item: sp_item's k20 for the name (one row expected), else sp.key(name) -- never bare K() (R1-B1)."""
    if item in cache:
        return cache[item]
    try:
        r = sp.q("SELECT DISTINCT k20 FROM sp_item WHERE name=?", item)
        k = str(r[0]["k20"]) if r else sp.key(item)
    except Exception:                                          # noqa: BLE001
        k = sp.key(item)
    cache[item] = k
    return k
''', '''def _s524_key_of(sp, item, cache, ctx=None):
    """S577: stock_figure.key_of -- the one identity (sp_item's k20 for the printed name, spacing and case ignored; the ticked renames;
    else the spine's alias key), never bare K() (R1-B1). `cache` is the table's own dict, as before."""
    if item in cache:
        return cache[item]
    k = _sf.key_of(sp, item, ctx)
    cache[item] = k
    return k
'''))
SA.append(("A13 _s524_table: the identity and the residual match", '''    mixed = _s524_mixed(sp)
    T["mixed"] = mixed
    kof = {}
    for b in batches.values():
        for item, _ch, _m in b["lines"]:
            _s524_key_of(sp, item, kof)
    T["kof"] = kof
''', '''    mixed = _s524_mixed(sp)
    T["mixed"] = mixed
    kof = {}
    kctx = _sf.Ctx(con, sp)                                    # S577: one identity context for the table
    for b in batches.values():
        for item, _ch, _m in b["lines"]:
            _s524_key_of(sp, item, kof, kctx)
    T["kof"] = kof
'''))
SA.append(("A14 _s524_table: late_match", '''                    ok, lp = abs(res) < 0.5, None
                    if not ok:
                        pl = late.get(k, [])
                        for u in pl:
                            if abs(res - u) < 0.5:
                                ok, lp = True, u
                                break
                        if not ok:
                            for i in range(len(pl)):
                                for j in range(i + 1, len(pl)):
                                    if abs(res - pl[i] - pl[j]) < 0.5:
                                        ok, lp = True, pl[i] + pl[j]
                                        break
                                if ok:
                                    break
''', '''                    ok, lp = abs(res) < 0.5, None
                    if not ok:
                        lp = _sf.late_match(res, late.get(k, []))     # S577: the one residual match (stock_figure; the voucher guard reads it too)
                        ok = lp is not None
'''))
SA.append(("A15 api_drift", '''    u, err = _require("checker", "maker")
    if err:
        return err
    con = _db()
    _feed_ensure(con)
    latest = _feed_latest(con)
    byday = {}
    for (as_on, kind), v in latest.items():
        for item, qty in v["items"].items():
            byday.setdefault((as_on, item), {})[kind] = qty
    per = {}
    for (as_on, item) in sorted(byday, key=lambda k: (_proof_day_key(k[0]), k[1])):   # S488 (F-753): a day sorts as a date
        v = byday[(as_on, item)]
        if "expected" not in v or "marg" not in v:
            continue
        d = int(v["expected"]) - int(v["marg"])
        e = per.setdefault(item, dict(item=item, runs=0, deltas=[], days=[]))
        e["runs"] += 1
        e["deltas"].append(d)
        e["days"].append(as_on)
    out = []
    for item, e in per.items():
        ds = e["deltas"]
        nz = [x for x in ds if x != 0]
        same = len(set(nz)) == 1 and len(nz) == len(ds) and len(ds) > 1
        if not nz:
            verdict = "agrees every day"
        elif len(ds) == 1:
            # ONE day is not a series. Calling it the shelf on day one is
            # the overclaim the whole page exists to avoid.
            verdict = "first day compared -- too early to say which"
        elif same:
            verdict = "SAME gap every day -- look at the arithmetic"
        else:
            verdict = "gap on some days -- look at the shelf"
        out.append(dict(item=item, runs=e["runs"], last=ds[-1],
                        agreed=len(ds) - len(nz), disagreed=len(nz),
                        verdict=verdict,
                        cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item),
                        days=e["days"][-8:], deltas=ds[-8:]))
    out.sort(key=lambda x: (-x["disagreed"], -abs(x["last"] or 0)))
    feeds = [dict(as_on=r[0], source=r[1], items=r[2], first=r[3], last=r[4])
             for r in con.execute(
                 "SELECT as_on, source, COUNT(*), MIN(received_at), MAX(received_at) "
                 "FROM stock_feed GROUP BY as_on, source ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC, source"
                 " LIMIT 40")]
    rdy = _readiness_safe(con)
    return jsonify(ok=True, items=out, feeds=feeds, readiness=rdy,
                   purchase=purchase_due(con),
                   comparable=len(out),
                   note=("A day is comparable only when BOTH feeds arrived for it. "
                         "push_expected.py has to be running for this page to fill."))
''', '''    u, err = _require("checker", "maker")
    if err:
        return err
    con = _db()
    _feed_ensure(con)
    # S577 (3.3 F): the figures of record are stock_figure's -- Marg's figure and the shelf figure, each on the capture it stands on. The PC's
    # push_expected series (the old drift) is shown beside them to the DOCTOR role only, headed "PC's old estimate (retiring)".
    doctor = _has_role(u, "doctor")
    rec, cap = _s577_record(con)
    out = []
    pc = {}
    if doctor:
        latest = _feed_latest(con)
        byday = {}
        for (as_on, kind), v in latest.items():
            for item, qty in v["items"].items():
                byday.setdefault((as_on, item), {})[kind] = qty
        for (as_on, item) in sorted(byday, key=lambda k: (_proof_day_key(k[0]), k[1])):   # S488 (F-753): a day sorts as a date
            v = byday[(as_on, item)]
            if "expected" not in v or "marg" not in v:
                continue
            d = int(v["expected"]) - int(v["marg"])
            e = pc.setdefault(item, dict(runs=0, deltas=[], days=[]))
            e["runs"] += 1
            e["deltas"].append(d)
            e["days"].append(as_on)
    for item in sorted(set(rec) | set(pc)):
        r = rec.get(item) or {}
        e = pc.get(item) or dict(runs=0, deltas=[], days=[])
        ds = e["deltas"]
        nz = [x for x in ds if x != 0]
        same = len(set(nz)) == 1 and len(nz) == len(ds) and len(ds) > 1
        if not doctor:
            verdict = "PC's old estimate (retiring) -- shown to the doctor only"
        elif not ds:
            verdict = "no PC estimate for this item"
        elif not nz:
            verdict = "agrees every day"
        elif len(ds) == 1:
            verdict = "first day compared -- too early to say which"   # ONE day is not a series
        elif same:
            verdict = "SAME gap every day -- look at the arithmetic"
        else:
            verdict = "gap on some days -- look at the shelf"
        out.append(dict(item=item, marg=r.get("marg"), shelf=r.get("shelf"), gap_now=r.get("gap"), approx=r.get("approx"), named=r.get("named"),
                        marg_as_on=r.get("marg_as_on"), capture_at=r.get("capture_at"),
                        runs=e["runs"], last=(ds[-1] if ds else None), agreed=len(ds) - len(nz), disagreed=len(nz), verdict=verdict,
                        pc_old_head="PC's old estimate (retiring)",
                        cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item), days=e["days"][-8:], deltas=ds[-8:]))
    out.sort(key=lambda x: (-x["disagreed"], -abs(x["last"] or 0), -abs(x["gap_now"] or 0), x["item"]))
    feeds = [dict(as_on=r[0], source=r[1], items=r[2], first=r[3], last=r[4])
             for r in con.execute(
                 "SELECT as_on, source, COUNT(*), MIN(received_at), MAX(received_at) "
                 "FROM stock_feed GROUP BY as_on, source ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC, source"
                 " LIMIT 40")] if doctor else []
    rdy = _readiness_safe(con)
    return jsonify(ok=True, items=out, feeds=feeds, readiness=rdy,
                   purchase=purchase_due(con),
                   comparable=len([x for x in out if x["runs"]]),
                   record=dict(as_on=(cap or {}).get("as_on"), capture_at=(cap or {}).get("stamp_iso"), end_day=(cap or {}).get("end_day"),
                               ready=bool(cap), source="stock_figure (Marg's figure and the shelf figure, by printed name on the newest usable closing)"),
                   note=("The figures of record are Marg's figure and the shelf figure (stock_figure). The PC's old estimate (retiring) is "
                         "shown beside them to the doctor only; a day of it is comparable only when both feeds arrived."))
'''))
SA.append(("A16 api_now", '''    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    latest = _feed_latest(con)
    days = sorted({d for (d, k) in latest}, key=_proof_day_key)          # S488 (F-753): the newest day by date, not by text
    if not days:
        return jsonify(ok=True, as_on=None, rows=[], totals={},
                       readiness=_readiness_safe(con),
                       note="No stock figure has reached this server yet.")
    as_on = days[-1]
    ours = (latest.get((as_on, "expected")) or {}).get("items", {})
    marg = (latest.get((as_on, "marg")) or {}).get("items", {})
    rows = []
    for item in sorted(set(ours) | set(marg)):
        o = ours.get(item)
        m = marg.get(item)
        gap = (o - m) if (o is not None and m is not None) else None
        rows.append(dict(item=item, ours=o, marg=m, gap=gap,
                         cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item)))
    both = [r for r in rows if r["gap"] is not None]
    totals = dict(
        items=len(rows), compared=len(both),
        agree=sum(1 for r in both if r["gap"] == 0),
        differ=sum(1 for r in both if r["gap"] != 0),
        below_zero=sum(1 for r in rows
                       if (r["ours"] is not None and r["ours"] < 0)
                       or (r["marg"] is not None and r["marg"] < 0)),
        ours_only=sum(1 for r in rows if r["marg"] is None),
        marg_only=sum(1 for r in rows if r["ours"] is None))
    rows.sort(key=lambda r: (r["gap"] is None, -abs(r["gap"] or 0), r["item"]))
    return jsonify(ok=True, as_on=as_on, rows=rows, totals=totals,
                   ours_at=(latest.get((as_on, "expected")) or {}).get("received_at"),
                   marg_at=(latest.get((as_on, "marg")) or {}).get("received_at"),
                   readiness=_readiness_safe(con))
''', '''    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    # S577 (3.3 F): the figures of record are stock_figure's. ours = the SHELF figure (None for an item no count has reached), marg = Marg's
    # figure on the newest usable closing capture, gap = ours - marg. The PC's push_expected figure is shown beside them to the DOCTOR role
    # only (pc_old, headed "PC's old estimate (retiring)").
    doctor = _has_role(u, "doctor")
    rec, cap = _s577_record(con)
    if not cap:
        return jsonify(ok=True, as_on=None, rows=[], totals={},
                       readiness=_readiness_safe(con),
                       note="The spine's closing table is not ready yet: no stock figure of record.")
    pc, pc_at = {}, None
    if doctor:
        latest = _feed_latest(con)
        ds = sorted({d for (d, k) in latest if k == "expected"}, key=_proof_day_key)
        if ds:
            pc = (latest.get((ds[-1], "expected")) or {}).get("items", {})
            pc_at = (latest.get((ds[-1], "expected")) or {}).get("received_at")
    rows = []
    for item, r in sorted(rec.items()):
        row = dict(item=item, ours=r["shelf"], marg=r["marg"], gap=r["gap"], named=r["named"], approx=r["approx"],
                   marg_as_on=r["marg_as_on"], capture_at=r["capture_at"], cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item))
        if doctor:
            row["pc_old"], row["pc_old_head"] = pc.get(item), "PC's old estimate (retiring)"
        rows.append(row)
    both = [r for r in rows if r["gap"] is not None]
    totals = dict(
        items=len(rows), compared=len(both),
        agree=sum(1 for r in both if r["gap"] == 0),
        differ=sum(1 for r in both if r["gap"] != 0),
        below_zero=sum(1 for r in rows
                       if (r["ours"] is not None and r["ours"] < 0)
                       or (r["marg"] is not None and r["marg"] < 0)),
        ours_only=sum(1 for r in rows if r["marg"] is None),
        marg_only=sum(1 for r in rows if r["ours"] is None),
        no_count=sum(1 for r in rows if r["named"] == "no_count"))
    rows.sort(key=lambda r: (r["gap"] is None, -abs(r["gap"] or 0), r["item"]))
    return jsonify(ok=True, as_on=_s524_dmy(cap["as_on"]), rows=rows, totals=totals,
                   ours_at=now_iso(), marg_at=cap["stamp_iso"], capture=dict(as_on=cap["as_on"], end_day=cap["end_day"], stamp_iso=cap["stamp_iso"], md5=cap["md5"][:8]),
                   pc_old_at=pc_at, pc_old_head=("PC's old estimate (retiring)" if doctor else None),
                   columns=["Item", "Ours (the shelf figure)", "Marg (the newest usable closing, carried forward)", "Gap"] + (["PC's old estimate (retiring)"] if doctor else []),
                   readiness=_readiness_safe(con))


def _s577_record(con):
    """({item: dict(marg, shelf, gap, named, approx, marg_as_on, capture_at)}, the capture) -- the figures of record for the stock-now and
    drift pages (stock_figure.figures over the newest usable capture's printed names plus the count's), one context. ({}, None) while the
    spine's closing table is not ready."""
    sp = _s524_spine()
    if not _sf.ready(sp):
        return {}, None
    ctx = _sf.Ctx(con, sp)
    cap = _sf.capture_at(sp, None, ctx)
    if cap is None:
        return {}, None
    names = sorted({str(r["name"]) for r in sp.q("SELECT DISTINCT name FROM sp_close_name WHERE md5=?", cap["md5"]) if r["name"]} | set(_sf.count_family(con, ctx)))
    out = {}
    for n in names:
        F = _sf.figures(con, sp, [n], None, ctx)[n]
        M, S = F["marg"], F["shelf"]
        m = (int(round(M["figure"])) if M else None)
        s = (int(S["shelf"]) if (S and S.get("shelf") is not None) else None)
        out[n] = dict(marg=m, shelf=s, gap=((s - m) if (s is not None and m is not None) else None), named=S.get("named") if S else None,
                      approx=bool((S or {}).get("approx") or (M or {}).get("approx")), marg_as_on=(M["closing"]["as_on"] if M else None),
                      capture_at=(M["closing"]["stamp_iso"] if M else None))
    return out, cap
'''))

EDITS = {"spine/spine_build.py": SB, "spine/selftest_spine.py": ST, "shelf_figure.py": SH, "stock_watch.py": SW, "loss_piles.py": LP, "stock_app.py": SA}


def apply(src, edits, label):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM[label]:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, FROM[label]))
        return None
    t = raw.decode("utf-8")
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(os.path.join(a.finance, label), edits, label)
        if out is None:
            return 2
        built[label] = out
    new_src = os.path.join(a.kit, NEW)
    if not os.path.exists(new_src):
        print("STOP: %s is not in the kit folder -- nothing built" % new_src)
        return 2
    built[NEW] = open(new_src, "rb").read()
    os.makedirs(os.path.join(a.out, "spine"), exist_ok=True)
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s%s" % (dst, hashlib.md5(out).hexdigest(), ("  (FROM %s)" % FROM[label]) if label in FROM else "  (NEW)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
