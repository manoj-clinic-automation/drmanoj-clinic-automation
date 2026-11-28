#!/usr/bin/env python3
"""fix_s976.py -- S976_WHOLE_UNIT_PACK (F-1742): the counts Darpan's screen stored with a pack per piece for a whole-unit item
(CCM, 28-11: one bottle stored as 40) put right -- the count divided by the pack it was stored with, its gap with it; the morning-list row
and any open loss line beside it. Every row's before-image is kept in s976_fix; --undo puts each back exactly.
Run from the finance folder (it reads stock_figure / stock_watch / qty_words beside it):
    python3 fix_s976.py DB --dry      lists what would change, writes nothing
    python3 fix_s976.py DB --write    makes the change (refuses more than MAX points); prints FIXED ids=...
    python3 fix_s976.py DB --undo     puts every S976 change back
Item names only; no patient data is read."""
import datetime as dt, json, os, sqlite3, sys

sys.path.insert(0, os.getcwd())
MAX = int(os.environ.get("S976_MAX", "3"))
FROM_DAY = "2026-09-07"                                  # after the 06-Sep full count (stored in whole pieces); the count screens only


def now():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).replace(tzinfo=None, microsecond=0).isoformat()


def ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS s976_fix (id INTEGER PRIMARY KEY, at TEXT NOT NULL, tbl TEXT NOT NULL, row_id INTEGER NOT NULL, "
                "before_json TEXT NOT NULL, after_json TEXT NOT NULL, undone_at TEXT)")


def row(con, t, i):
    c = con.execute("SELECT * FROM %s WHERE id=?" % t, (i,))
    r = c.fetchone()
    return dict(zip([d[0] for d in c.description], r)) if r else None


def has(con, t):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone())


def candidates(con):
    import stock_figure as SF
    import stock_watch as SW
    sp = SW.Spine()
    done = {r[0] for r in con.execute("SELECT row_id FROM s976_fix WHERE tbl='stock_point' AND undone_at IS NULL")}
    out = []
    for pid, item, at, q, rid in con.execute("SELECT id, item, at, qty_units, roster_id FROM stock_point WHERE source IN ('spot','darpan') AND at>=? "
                                             "AND COALESCE(status,'')<>'superseded' AND qty_units>0 ORDER BY at, id", (FROM_DAY,)).fetchall():
        if pid in done or not SF._s976_whole(con, item):
            continue
        pack = 0
        if rid:
            r = con.execute("SELECT pack FROM stock_spot_roster WHERE id=?", (rid,)).fetchone()
            pack = int((r[0] if r else 0) or 0)
            if r and pack == 1:
                continue                                 # its list row already asked in whole pieces: a true count (cold review note)
        if pack <= 1:
            try:
                pack = int(SF._pack_of_before_s976(con, sp, item)[0] or 1)
            except Exception:                            # noqa: BLE001
                pack = 1
        if pack > 1 and abs(float(q) / pack - round(float(q) / pack)) < 1e-9:
            out.append(dict(id=pid, item=item, at=at, qty=float(q), pack=pack, roster_id=rid))
    return out


def write(con):
    ts = now()
    con.execute("BEGIN IMMEDIATE")                       # the rows are chosen inside the write lock (cold review S2)
    C = candidates(con)
    if len(C) > MAX:
        con.rollback()
        print("REFUSED %d points (more than %d): %s" % (len(C), MAX, "; ".join("%s %s %g/%d" % (c["item"], c["at"][:16], c["qty"], c["pack"]) for c in C)))
        return 2
    try:
        for c in C:
            P = row(con, "stock_point", c["id"])
            nq = round(c["qty"] / c["pack"])
            ng = None if P.get("expected_units") is None else round(nq - float(P["expected_units"]), 3)
            note = ((P.get("note") or "") + " · S976 (F-1742): stored %g = %d %s read with a pack of %d; corrected to %d" % (
                c["qty"], nq, "piece" if nq == 1 else "pieces", c["pack"], nq)).strip(" ·")
            con.execute("UPDATE stock_point SET qty_units=?, gap_units=?, note=? WHERE id=?", (float(nq), ng, note[:600], c["id"]))
            con.execute("INSERT INTO s976_fix (at, tbl, row_id, before_json, after_json) VALUES (?,?,?,?,?)",
                        (ts, "stock_point", c["id"], json.dumps(P, default=str), json.dumps(dict(qty_units=nq, gap_units=ng), default=str)))
            if c["roster_id"]:
                R = row(con, "stock_spot_roster", c["roster_id"])
                if R:
                    con.execute("UPDATE stock_spot_roster SET qty_units=?, pack=1 WHERE id=?", (float(nq), R["id"]))
                    con.execute("INSERT INTO s976_fix (at, tbl, row_id, before_json, after_json) VALUES (?,?,?,?,?)",
                                (ts, "stock_spot_roster", R["id"], json.dumps(R, default=str), json.dumps(dict(qty_units=nq, pack=1))))
            if has(con, "stock_watch_loss_line"):
                for (lid,) in con.execute("SELECT id FROM stock_watch_loss_line WHERE point_id=?", (c["id"],)).fetchall():
                    L = row(con, "stock_watch_loss_line", lid)
                    g = float(L.get("gap_units") or 0) / c["pack"]
                    con.execute("UPDATE stock_watch_loss_line SET gap_units=?, pack=1 WHERE id=?", (g, lid))
                    con.execute("INSERT INTO s976_fix (at, tbl, row_id, before_json, after_json) VALUES (?,?,?,?,?)",
                                (ts, "stock_watch_loss_line", lid, json.dumps(L, default=str), json.dumps(dict(gap_units=g, pack=1))))
        con.commit()
    except Exception:
        con.rollback()
        raise
    print("FIXED n=%d ids=%s %s" % (len(C), ",".join(str(c["id"]) for c in C), "; ".join("%s %s %g -> %d" % (c["item"], c["at"][:10], c["qty"], round(c["qty"] / c["pack"])) for c in C)))
    return 0


def undo(con):
    ts = now()
    n = 0
    con.execute("BEGIN IMMEDIATE")
    try:
        left = []
        # the fix's own mark (CHECK) must still stand; then the columns the fix and its re-judging set are put back (RESTORE) -- nothing else
        CHECK = dict(stock_point=("qty_units",), stock_spot_roster=("pack",), stock_watch_loss_line=("pack",))
        RESTORE = dict(stock_point=("qty_units", "gap_units", "expected_units", "basis", "judge_words", "note"),
                       stock_spot_roster=("qty_units", "pack"), stock_watch_loss_line=("gap_units", "pack", "mrp_p", "void_at", "void_why"))   # mrp_p: a re-judged resize sets it (re-look M1)
        for i, t, rid, b, a in con.execute("SELECT id, tbl, row_id, before_json, after_json FROM s976_fix WHERE undone_at IS NULL ORDER BY id DESC").fetchall():
            B, A = json.loads(b), json.loads(a)
            now_ = row(con, t, rid) or {}
            same = bool(now_) and all(k in A and now_.get(k) is not None and abs(float(now_[k]) - float(A[k])) < 1e-9 for k in CHECK[t])
            if same and t == "stock_spot_roster" and "qty_units" not in A and now_.get("answered_at"):
                same = False                                 # a list row re-packed at install and answered since, in pieces: left (re-look S1)
            if not same:                                     # changed since the fix: left as it now stands (second look S3)
                left.append("%s %d" % (t, rid))
                continue
            cols = [k for k in RESTORE[t] if k in B and (k in now_)]
            if t == "stock_spot_roster" and "qty_units" not in A:
                cols = ["pack"]                              # a list row the install only re-packed
            con.execute("UPDATE %s SET %s WHERE id=?" % (t, ", ".join("%s=?" % k for k in cols)), [B.get(k) for k in cols] + [rid])
            con.execute("UPDATE s976_fix SET undone_at=? WHERE id=?", (ts, i))
            n += 1
        con.commit()
    except Exception:
        con.rollback()
        raise
    print("UNDONE rows=%d%s" % (n, (" left (changed since the fix): " + ", ".join(left)) if left else ""))
    return 0


def main(a):
    con = sqlite3.connect(a[0], timeout=30, isolation_level=None)
    ensure(con)
    if "--undo" in a:
        return undo(con)
    if "--write" in a:
        return write(con)
    C = candidates(con)
    print("WOULD n=%d %s" % (len(C), "; ".join("%s %s %g/%d" % (c["item"], c["at"][:16], c["qty"], c["pack"]) for c in C)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
