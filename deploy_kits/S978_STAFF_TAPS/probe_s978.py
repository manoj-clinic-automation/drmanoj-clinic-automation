#!/usr/bin/env python3
"""probe_s978.py -- the live shape of kit S978 on a COPY of finance.db (counts and sums only; nothing written that is kept, no push).
Usage: probe_s978.py OLD_FINANCE_DIR NEW_FINANCE_DIR DB_COPY [DAYS]. Prints 'ALL PASS' last when every check holds."""
import sys, os, sqlite3, importlib, datetime as dt
OLD, NEW, DB = sys.argv[1], sys.argv[2], sys.argv[3]
DAYS = int(sys.argv[4]) if len(sys.argv) > 4 else 60
os.environ.update({"EVCHK_LIVE_DB": "/nonexistent/live.db", "REGPUSH_SPAWN": "0"})


def load(path):
    for m in ("day_check", "register_push", "clinic_register", "slip_log", "slip_adjust", "not_in_docterz", "evening_check"):
        sys.modules.pop(m, None)
    sys.path.insert(0, path)
    try:
        return importlib.import_module("day_check"), importlib.import_module("register_push")
    finally:
        sys.path.pop(0)


def run(path, html):
    dc, rp = load(path)
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    con.row_factory = sqlite3.Row
    dc.ensure = lambda c: None                            # a read-only copy: the tick table is already there
    out, errs, offers = {}, 0, {"lateslip": 0, "regfix": 0, "dunno": 0, "lessref": 0}
    t = dt.date.today()
    for i in range(1, DAYS + 1):
        d = (t - dt.timedelta(days=i)).isoformat()
        try:
            ch = dc.check_day(con, d)
            out[d] = (ch.get("state"), sorted((c["kind"], c["key"], int(c["amount"] or 0)) for c in ch["cards"]),
                      tuple(sorted((ch.get("top") or {}).items())), tuple(sorted(rp.owner_lines(ch).items())))
            if html and ch.get("state") == "checked":
                h = dc.cards_html(con, ch, {"user": "shavez", "roles": ["maker"]}, False)
                for k in offers:
                    offers[k] += h.count("value='%s'" % k)
        except Exception as ex:                           # noqa: BLE001
            errs += 1
            out[d] = ("ERR", type(ex).__name__, str(ex)[:80])
    return out, errs, offers


a, ea, _ = run(OLD, False)
b, eb, offers = run(NEW, True)
same = sum(1 for d in a if a[d] == b.get(d))
cards = sum(len(v[1]) for v in b.values() if v[0] == "checked")
print("LIVE %d days: same cards, totals and his lines on %d of %d; errors old %d new %d; cards %d; offered: late parchi %d, register fix %d, "
      "refund %d, don't know %d" % (DAYS, same, len(a), ea, eb, cards, offers["lateslip"], offers["regfix"], offers["lessref"], offers["dunno"]))


def trial(kind):
    """On a scratch copy of the copy: every offered tap of this kind done, the day read again -- does it match by itself?"""
    import shutil, tempfile
    tmp = tempfile.mkdtemp(prefix="p978_")
    cp = os.path.join(tmp, "t.db")
    s = sqlite3.connect(DB); dst = sqlite3.connect(cp); s.backup(dst); dst.close(); s.close()
    dc, rp = load(NEW)
    con = sqlite3.connect(cp); con.row_factory = sqlite3.Row
    done = matched = 0
    t = dt.date.today()
    try:
        for i in range(1, DAYS + 1):
            d = (t - dt.timedelta(days=i)).isoformat()
            ch = dc.check_day(con, d)
            for c in ch["cards"]:
                if kind == "regfix" and c["kind"] in ("notfound", "less"):
                    x = dc._s978_cell(con, c, d)
                    if x is None:
                        continue
                    ok_, er = dc._s978_regfix(con, d, c, {"field": x[0], "was": str(x[1]), "now": str(x[2])}, "probe", True)
                elif kind == "late" and c["kind"] == "notfound" and dc._late_ok(d) and c.get("cands"):
                    sv = dc._s978_services(con, d, c.get("section") or "consult", int(c["amount"]))
                    if not sv:
                        continue
                    no = dc._s978_next_no(con, dc.SEC_SERIES.get(c.get("section"), "xp"))
                    ok_, er = dc._s978_late(con, d, c, {"pick": c["cands"][0][0], "svc": sv[0][0], "no": str(no)}, "probe", True)
                else:
                    continue
                done += 1
                after = dc.check_day(con, d)
                if ok_ and not any(x["key"] == c["key"] for x in after["cards"]) and (after.get("top") or {}).get("left") == 0:
                    matched += 1
                else:
                    print("TRIAL %s %s: %s" % (kind, d, (er or "the day still differs")[:90]))
                break
    finally:
        con.close()
        shutil.rmtree(tmp, ignore_errors=True)
    return done, matched


ld, lm = trial("late")
rd, rm = trial("regfix")
print("TRIAL (a scratch copy): late parchis %d made, %d days matched by themselves; register fixes %d, %d days matched" % (ld, lm, rd, rm))
bad = [d for d in a if a[d] != b.get(d)]
for d in bad[:3]:
    print("DIFF", d)
ok = same == len(a) and eb == 0 and ea == 0 and lm == ld and rm == rd
print("ALL PASS" if ok else "NOT GREEN")
sys.exit(0 if ok else 1)
