"""make_s668.py -- kit S668_EXPIRY_START_OF_DAY (Sanjeevni session S359, 27-Oct-2026). The owner, 11:58 IST: VOM L still on the expiry list
after its last strips were sold. S665 made the list catch up in the day; it still read VOM L 3:0 because the watch takes off only the sales
AFTER the Batch Stock's day, and the 26-Oct Batch Stock was taken at 05:38 on 26-Oct -- the START of that day (D740) -- so 26-Oct's own sales
were never taken off.
  /root/finance/expiry_watch.py  fed23760 -> TO  3 edits: _sales_after(R) -- the day whose END a Batch Stock stands for, by the estate's one
        capture-hour rule (stock_figure.end_day on the file's own stamp: a same-day print before 09:00 = the day before; after 22:00 or for an
        earlier day = its own day; in shop hours = its own day, as before); compute() takes the sales, the purchases since and the
        written-off check from that day instead of the printed day.
Usage: python make_s668.py <live root, e.g. /root> <out dir>   (writes <out>/finance/expiry_watch.py)"""
import hashlib, os, sys

FROM = {"finance/expiry_watch.py": "fed237603e3be0e5ca69cdd63ae43ff0"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:80])
    T[r] = T[r].replace(old, new, 1)


E = "finance/expiry_watch.py"
rep(E, '''    if chosen:
''', '''    if chosen:
        sales_after = _sales_after(chosen)                    # S668 (D740): the day whose END the Batch Stock stands for
''')
rep(E, '''WHERE l.date > ? ORDER BY l.date", (chosen["as_on"],)):''', '''WHERE l.date > ? ORDER BY l.date", (sales_after,)):''')
rep(E, '''        bought_since = {r[0] for r in sp.execute("SELECT DISTINCT k20 FROM sp_move WHERE kind='PURCHASE' AND date > ?", (chosen["as_on"],))}
        gone = written_off(sp, chosen["as_on"])
''', '''        bought_since = {r[0] for r in sp.execute("SELECT DISTINCT k20 FROM sp_move WHERE kind='PURCHASE' AND date > ?", (sales_after,))}
        gone = written_off(sp, sales_after)
''')
rep(E, '''def written_off(sp, as_on):''', '''def _sales_after(R):
    """S668 (D740, the owner 27-Oct-2026): the day whose END a Batch Stock stands for -- the estate's one capture-hour rule,
    stock_figure.end_day, on the file's own stamp (BATCH_STOCK_..__<as_on>__<YYYYMMDD-HHMMSS>__<md5>): a print taken before 09:00 on its own
    day is the START of that day, so that day's sales are taken off; after 22:00, or a print for an earlier day, stands for its own day; a
    same-day print in shop hours (the rule says None) keeps its own day, as before S668. Fail-soft: the printed day."""
    as_on = R.get("as_on")
    m = re.search(r"__(\\d{8}-\\d{6})__", str(R.get("name") or ""))
    try:
        import stock_figure                                   # noqa: PLC0415
        e = stock_figure.end_day(as_on, stock_figure.stamp_iso(m.group(1))) if m else None
    except Exception:                                         # noqa: BLE001
        e = None
    return e or as_on


def written_off(sp, as_on):''')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))
