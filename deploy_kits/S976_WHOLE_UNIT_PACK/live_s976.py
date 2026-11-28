#!/usr/bin/env python3
"""live_s976.py -- S976_WHOLE_UNIT_PACK's live-shape proof and live read. Item names and figures only; no patient data.
Run with the finance folder as the working directory (its modules are imported from there):
    python3 live_s976.py dump DB OUT [--fix KITDIR]   (on a COPY) the record rebuilt by these modules -> OUT (json); --fix first puts the
                                                      stored counts right (fix_s976.py --write) and judges those counts again
    python3 live_s976.py compare A B                  every item but the whole-unit ones the same in both records; the whole-unit ones pack 1
    python3 live_s976.py apply DB KITDIR              (LIVE, after the files are placed) fix --write, the record rebuilt, the fixed counts judged again
    python3 live_s976.py read DB                      (LIVE, read only) the whole-unit items' record rows, today's list, the desk's band 2"""
import json, os, sqlite3, subprocess, sys

sys.path.insert(0, os.getcwd())
KEYS = ("pack", "marg_units", "shelf_units", "gap_units", "waiting_units", "state", "base_kind", "base_day")


def whole(con):
    import stock_figure as SF
    out = []
    for (item,) in con.execute("SELECT item FROM stock_of_record ORDER BY item").fetchall():
        if getattr(SF, "_s976_whole", None) and SF._s976_whole(con, item):
            out.append(item)
    return out


def fix_and_build(db, kit):
    r = subprocess.run([sys.executable, "-B", os.path.join(kit, "fix_s976.py"), db, "--write"], cwd=os.getcwd(), capture_output=True, text=True)
    fx = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
    con = sqlite3.connect(db, timeout=30)
    import stock_record as SR
    import stock_watch as SW
    sp = SW.Spine()
    B = SR.build(con, sp)
    ids = []
    if fx[0].startswith("FIXED n=") and "ids=" in fx[0]:
        rest = fx[0].split("ids=", 1)[1].split()             # 'FIXED n=0 ids=' has nothing after it (second look S1)
        ids = [int(x) for x in (rest[0].split(",") if rest else []) if x.strip().isdigit()]
    RJ = None
    if ids:
        import record_judges as RJM
        RJ = RJM.rejudge_all(con, sp, who="s976", write=True, since="2026-09-07", ids=set(ids))
        con.commit()
    return con, fx[0], B, ids, RJ


def dump(a):
    db, out = a[0], a[1]
    fx, ids, RJ = "", [], None
    if "--fix" in a:
        con, fx, B, ids, RJ = fix_and_build(db, a[a.index("--fix") + 1])
    else:
        con = sqlite3.connect(db, timeout=30)
        import stock_record as SR
        import stock_watch as SW
        B = SR.build(con, SW.Spine())
    con.row_factory = sqlite3.Row
    rows = {r["item"]: {k: r[k] for k in KEYS} for r in con.execute("SELECT * FROM stock_of_record")}
    con.row_factory = None
    W = whole(con)
    json.dump(dict(build=dict(ok=B.get("ok"), n=B.get("n"), reason=B.get("reason")), fix=fx, ids=ids, whole=W, rows=rows,
                   rejudge=(dict(n=RJ.get("n"), moved=RJ.get("moved"), withdrawn=RJ.get("withdrawn")) if RJ else None)), open(out, "w"), default=str)
    print("DUMP ok=%s n=%s fix=%s" % (B.get("ok"), B.get("n"), fx or "-"))


def f1(x):
    return "-" if x is None else ("%g" % float(x))


def compare(a):
    A, B = json.load(open(a[0])), json.load(open(a[1]))
    W = set(B["whole"])
    diff = [k for k in set(A["rows"]) | set(B["rows"]) if k not in W and A["rows"].get(k) != B["rows"].get(k)]
    wok = all(B["rows"].get(k, {}).get("pack") == 1 for k in W)
    c = B["rows"].get("CCM") or {}
    c0 = A["rows"].get("CCM") or {}
    print("LIVE-SHAPE built=%s/%s same_others=%s differ=%d whole=%s whole_pack1=%s | CCM pack %s->%s marg %s shelf %s gap %s state %s | %s" % (
        A["build"]["ok"], B["build"]["ok"], not diff, len(diff), ",".join(sorted(W)) or "-", wok, c0.get("pack"), c.get("pack"), f1(c.get("marg_units")),
        f1(c.get("shelf_units")), f1(c.get("gap_units")), c.get("state"), B.get("fix") or "-"))
    if diff:
        print("  differ: %s" % ", ".join(sorted(diff)[:8]))


def fix_day(con, SW):
    """Today's unanswered morning-list rows of a whole-unit item to pack 1 -- each row's before-image in s976_fix, so the undo puts it back."""
    import datetime as dt
    import stock_figure as SF
    day = SW.today().isoformat()
    con.execute("CREATE TABLE IF NOT EXISTS s976_fix (id INTEGER PRIMARY KEY, at TEXT NOT NULL, tbl TEXT NOT NULL, row_id INTEGER NOT NULL, "
                "before_json TEXT NOT NULL, after_json TEXT NOT NULL, undone_at TEXT)")
    cur = con.execute("SELECT * FROM stock_spot_roster WHERE day=? AND answered_at IS NULL AND COALESCE(pack,1)>1", (day,))
    cols = [d[0] for d in cur.description]
    n = 0
    ts = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).replace(tzinfo=None, microsecond=0).isoformat()
    for r in cur.fetchall():
        R = dict(zip(cols, r))
        if SF._s976_whole(con, R["item"]):
            con.execute("UPDATE stock_spot_roster SET pack=1 WHERE id=? AND answered_at IS NULL", (R["id"],))
            con.execute("INSERT INTO s976_fix (at, tbl, row_id, before_json, after_json) VALUES (?,?,?,?,?)",
                        (ts, "stock_spot_roster", R["id"], json.dumps(R, default=str), json.dumps(dict(pack=1))))
            n += 1
    con.commit()
    return n


def apply(a):
    con, fx, B, ids, RJ = fix_and_build(a[0], a[1])
    import stock_watch as SW
    if not str(fx).startswith("FIXED n="):
        print("APPLY-FAILED the count fix said: %s" % (fx or "nothing"))
        return
    nday = fix_day(con, SW)                                    # today's unanswered list rows of such an item: pack 1 now (cold review S3)
    print("APPLY build=%s n=%s | %s | rejudged %s | list rows put right %d" % (B.get("ok"), B.get("n"), fx, (RJ or {}).get("n", 0), nday))


def read(a):
    con = sqlite3.connect("file:%s?mode=ro" % a[0], uri=True, timeout=30)
    import stock_figure as SF
    import stock_check as SC
    out = []
    for item in whole(con):
        r = con.execute("SELECT pack, marg_units, shelf_units, gap_units, state FROM stock_of_record WHERE item=?", (item,)).fetchone()
        out.append("%s record pack %s marg %s shelf %s gap %s %s" % (item, r[0], f1(r[1]), f1(r[2]), f1(r[3]), r[4]))
        for q, p in con.execute("SELECT qty_units, pack FROM stock_spot_roster WHERE item=? AND day=date('now','+330 minutes')", (item,)).fetchall():
            out.append("%s today's list pack %s count %s" % (item, p, f1(q)))
    K = SC.desk(con)
    b2 = [r for r in (K.get("band2") or []) if SF._s976_whole(con, r.get("item"))]
    for r in b2:
        out.append("%s band2 '%s' %s" % (r.get("item"), r.get("fig"), r.get("verdict")))
    print("READ ok=%s | %s" % (K.get("ok"), " | ".join(out) or "no whole-unit item in the record"))


if __name__ == "__main__":
    m = sys.argv[1]
    {"dump": dump, "compare": compare, "apply": apply, "read": read}[m](sys.argv[2:])
