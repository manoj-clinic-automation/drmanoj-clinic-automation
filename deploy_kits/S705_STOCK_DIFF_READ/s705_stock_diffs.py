#!/usr/bin/env python3
"""S705_STOCK_DIFF_READ -- READ-ONLY. Lists every OPEN stock difference the spine holds at its latest
checkable closing: when it began, Marg and the spine on both sides of that day, what moved in between,
and the item at each pending (newer) closing. Opens spine.db with mode=ro; writes nothing anywhere.
Usage: python3 -B s705_stock_diffs.py [/root/finance/spine/spine.db]"""
import collections
import sqlite3
import sys

DB = sys.argv[1] if len(sys.argv) > 1 else "/root/finance/spine/spine.db"


def f(x):
    return ("%+g" % x) if x else "0"


def g(x):
    return "%g" % x


def main():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    con.row_factory = sqlite3.Row
    meta = {r[0]: r[1] for r in con.execute("SELECT key, value FROM sp_meta")}
    chk_days = [x for x in (meta.get("checkable") or "").split(",") if x]
    pend = [x for x in (meta.get("pending") or "").split(",") if x]
    if not chk_days:
        print("S705: no checkable closing in this spine -- nothing to list")
        return 3
    last = chk_days[-1]
    print("S705 STOCK DIFFERENCES (read-only) -- spine built %s -- latest checkable closing %s -- pending %s"
          % ((meta.get("built") or "?")[:16], last, ",".join(pend) or "none"))
    per = collections.OrderedDict()
    for d in chk_days[-6:]:
        c = collections.Counter()
        for r in con.execute("SELECT note FROM sp_finding WHERE as_on = ?", (d,)):
            c[(r[0] or "").split(":")[0].split(" ")[0]] += 1
        per[d] = c
    print("findings per closing: " + " | ".join("%s %s" % (d, dict(c)) for d, c in per.items()))
    names = {}
    for r in con.execute("SELECT k20, name, packing FROM sp_item"):
        names.setdefault(r[0], (r[1] or r[0]) + ((" [" + r[2] + "]") if r[2] else ""))
    opens = [(r[0], r[1]) for r in con.execute(
        "SELECT k20, diff FROM sp_finding WHERE as_on = ? AND note LIKE 'OPEN%' ORDER BY k20", (last,))]
    print("OPEN at %s: %d item(s)   [diff = Marg minus spine; + Marg has more]" % (last, len(opens)))
    for n, (k, x) in enumerate(opens, 1):
        chk = {r[0]: (r[1], r[2], r[3]) for r in con.execute(
            "SELECT as_on, marg, spine, diff FROM sp_check WHERE k20 = ?", (k,))}
        row = lambda d: chk.get(d, (0.0, 0.0, 0.0))
        i = len(chk_days) - 1
        while i > 0 and abs(row(chk_days[i - 1])[2] - x) < 0.5:
            i -= 1
        since = chk_days[i]
        prev = chk_days[i - 1] if i > 0 else ""
        m1, s1, _ = row(since)
        head = "%2d. %s  diff %s  (Marg %s, spine %s at %s)" % (n, names.get(k, k), f(x), g(row(last)[0]), g(row(last)[1]), last)
        print(head)
        if prev:
            m0, s0, d0 = row(prev)
            mv = collections.OrderedDict()
            for r in con.execute("SELECT date, kind, units, ref FROM sp_move WHERE k20 = ? AND date > ? AND date <= ? ORDER BY date",
                                 (k, prev, since)):
                e = mv.setdefault(r[1], [0.0, 0, []])
                e[0] += r[2] or 0
                e[1] += 1
                if len(e[2]) < 3:
                    e[2].append("%s %s" % (r[0][5:], (r[3] or "")[:22]))
            moved = "; ".join("%s %s x%d (%s)" % (kd, f(round(v[0], 3)), v[1], ", ".join(v[2])) for kd, v in mv.items()) or "nothing"
            print("    began after %s (diff was %s): Marg %s->%s, spine %s->%s; moved in the spine: %s"
                  % (prev, f(d0), g(m0), g(m1), g(s0), g(s1), moved))
        else:
            print("    present since the first checkable closing %s (Marg %s, spine %s)" % (since, g(m1), g(s1)))
        tail = []
        for p in pend:
            cr = con.execute("SELECT units FROM sp_close WHERE as_on = ? AND k20 = ?", (p, k)).fetchone()
            sb = con.execute("SELECT COALESCE(SUM(units),0) FROM sp_move WHERE k20 = ? AND date <= ?", (k, p)).fetchone()[0]
            tail.append("at %s (pending) Marg %s, spine %s" % (p, g(cr[0]) if cr else "0 (not on it)", g(round(sb, 3))))
        later = ["%s %s %s" % (r[0][5:], f(r[1]), (r[2] or "")[:22]) for r in con.execute(
            "SELECT date, units, ref FROM sp_move WHERE k20 = ? AND date > ? AND kind LIKE 'PURCHASE%' ORDER BY date", (k, last))]
        if later:
            tail.append("purchases after %s: %s" % (last, "; ".join(later[:4])))
        if tail:
            print("    " + " . ".join(tail))
    print("S705 END -- %d item(s); nothing was written" % len(opens))
    return 0


if __name__ == "__main__":
    sys.exit(main())
