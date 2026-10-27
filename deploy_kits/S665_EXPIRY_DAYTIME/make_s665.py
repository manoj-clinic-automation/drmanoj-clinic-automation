"""make_s665.py -- kit S665_EXPIRY_DAYTIME (Sanjeevni session S359, 27-Oct-2026). The owner, 11:58 IST: "The expiry watch is showing stale
stock of VOM L ... despite Shavez exported his reports successfully in morning." Read: VOM L's last 3 strips (batch C1235) were sold on 26-Oct;
those sales came in Shavez's 09:35 IST export and the spine had them by the next ten-minute build, but the watch is made only at 23:57.
  /root/finance/spine/near_expiry.py  c12284f3 -> TO  1 edit: --if-newer -- make the watch only when the spine holds a sale day newer than
        the newest run's sales_to (or there is no run yet); otherwise exit silently. The 23:57 line (no flag) is unchanged.
The installer adds ONE crontab line (S665_EXPIRY_DAYTIME): every ten minutes 09:05-23:55 IST, under the spine's own lock.
Usage: python make_s665.py <live root, e.g. /root> <out dir>   (writes <out>/finance/spine/near_expiry.py)"""
import hashlib, os, sys

FROM = {"finance/spine/near_expiry.py": "c12284f33770318088c7584b4de9ca0c"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:80])
    T[r] = T[r].replace(old, new, 1)


N = "finance/spine/near_expiry.py"
rep(N, '''def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    return expiry_watch.main(["run"] + argv)
''', '''def _opt(argv, name, default):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def newer(db=None, spine=None):
    """S665 (27-Oct-2026): (make it now?, why). Yes when the spine holds a sale day newer than the newest run's sales_to, or no run exists
    yet -- the morning's sales reach the spine within ten minutes of Shavez's export, and the list should not wait for 23:57. Read only."""
    import sqlite3                                            # noqa: PLC0415
    db = db or expiry_watch.DB_DEFAULT
    spine = spine or expiry_watch.SPINE_DEFAULT
    try:
        sp = sqlite3.connect("file:%s?mode=ro" % spine, uri=True)
        try:
            s = sp.execute("SELECT MAX(date) FROM sp_sale_line").fetchone()[0] or ""
        finally:
            sp.close()
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        try:
            r = (con.execute("SELECT sales_to FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
                 if expiry_watch._has(con, "stock_expiry_run") else None)
        finally:
            con.close()
    except sqlite3.Error as ex:
        return False, "not read (%s)" % ex
    if r is None:
        return True, "no run yet"
    last = r[0] or ""
    if s > last:
        return True, "the spine's sales reach %s; the newest run's reached %s" % (s, last or "-")
    return False, "up to date (sales to %s)" % (last or "-")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--if-newer" in argv:                                  # S665: the daytime line -- silent unless the morning's sales are newer
        argv = [x for x in argv if x != "--if-newer"]
        go, why = newer(_opt(argv, "--db", None), _opt(argv, "--spine", None))
        if not go:
            return 0
        print("near_expiry --if-newer (S665): %s" % why)
    return expiry_watch.main(["run"] + argv)
''')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))
