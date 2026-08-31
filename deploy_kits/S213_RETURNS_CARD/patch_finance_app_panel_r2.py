#!/usr/bin/env python3
"""
patch_finance_app_panel_r2.py -- S211 endpoint, r2 at S213: the returns and
payment keys are no longer dropped at the jsonify (the S212/S213 finding --
day_report() already computed both; the route threw them away).

    GET /finance/api/day-gaps?d=YYYY-MM-DD

NO NEW PAGE. The owner's standing rule, recorded at S210 and repeated at S211:
one page, no jumping, no duplication, all data on the page, collapsed and
expandable. A separate panel page would have been a second place to look.

NO DUPLICATION. The console already shows `Declared (Darpan)`, `Bank - ICICI
UPI settled` and the Marg day totals, so this endpoint deliberately returns
NONE of them. It returns only the two things the console has never had:

  * IDENTITY GAPS -- bills that did not resolve to a patient, each with the
    chain of steps that produced the verdict
  * SANCTIONED PHARMACY DISCOUNTS -- sanctioned percent, amount given, whether
    it matched; rounding exempt but recorded; over-discount in its own bucket

plus one contextual line: who was at the counter that day, and how that was
decided -- because a gap belongs to whoever was standing there.

READ-ONLY: it opens the database, reads, and returns. No INSERT, UPDATE, DELETE
or commit anywhere in the route.

SAFETY: exact-anchor insert, refuses on a missing or ambiguous anchor,
timestamped backup, py_compile with automatic restore on failure.
"""
import datetime, os, py_compile, shutil, sys

MARK = "S211 (day gaps api r2)"

ANCHOR = '''@app.route("/finance/api/marg-push/apply", methods=["POST"])'''

NEW = '''@app.route("/finance/api/day-gaps", methods=["GET"])
def api_day_gaps():
    """S211 (day gaps api r2) -- the things the console has never had.

    Deliberately does NOT return the declared figure, the bank settlement or the
    Marg totals: the console already shows all three, and a second copy of a
    number is a second thing to reconcile."""
    u, err = require("checker")
    if err:
        return err
    try:
        import finance_daily_gaps as _g                        # noqa: PLC0415
    except ImportError:
        return jsonify(ok=False, error="module_absent",
                       message="finance_daily_gaps.py is not in /root/finance/"), 503
    d = (request.args.get("d") or "").strip()
    if not d:
        row = db().execute("SELECT MAX(business_date) m FROM day_entry "
                           "WHERE unit=?", (UNIT,)).fetchone()
        d = row["m"] if row and row["m"] else None
    if not d:
        return jsonify(ok=True, date=None, gaps=[], discounts=[], dtally={},
                       counter={}, note="no day has been filed yet")
    con = db()
    rep = _g.day_report(con, d, UNIT)
    drows, dtal = rep.get("discounts", ([], {}))
    rrows, rsum = rep.get("returns", ([], {}))
    return jsonify(ok=True, date=d, counter=rep["counter"],
                   totals=rep["totals"], gaps=rep["identity_gaps"],
                   discounts=drows, dtally=dtal,
                   returns=rrows, returns_summary=rsum,
                   payment=rep.get("payment"),
                   era=rep.get("before_identity_era"))


@app.route("/finance/api/marg-push/apply", methods=["POST"])'''


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    if '"/finance/api/day-gaps"' in s:
        # the r1 endpoint (which drops returns/payment) is already installed --
        # patching again would add a second route. r1 was never installed on
        # the live box; if this fires, restore from the r1 backup first.
        return s, "r1_already_installed_restore_first"
    n = s.count(ANCHOR)
    if n != 1:
        return s, ("anchor_missing" if n == 0 else "anchor_ambiguous")
    return s.replace(ANCHOR, NEW), "patched"


def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1
        print(("  ok   " if cond else "  FAIL ") + name)
    for path in sys.argv[2:]:
        s = open(path, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s: patches cleanly (%s)" % (os.path.basename(path), st), st == "patched")
        if st != "patched":
            continue
        check("  the result compiles", compile(out, path, "exec") is not None)
        out2, st2 = patch_text(out)
        check("  a second run is a no-op", st2 == "already_patched" and out2 == out)
        check("  the original apply route SURVIVES", out.count(ANCHOR) == 1)
        check("  the endpoint is added once",
              out.count('@app.route("/finance/api/day-gaps"') == 1)
        check("  returns and payment are NOT dropped at the jsonify",
              "returns=rrows" in out and "payment=rep.get" in out)
    check("NO new HTML page is created", "PANEL_HTML" not in NEW and "<html" not in NEW)
    check("NO duplication: it returns no declared / bank / marg total",
          all(k not in NEW for k in ("declared_digital", "bank_settled", "marg_total")))
    check("READ-ONLY: no write statement in the route",
          all(w not in NEW.upper() for w in ("INSERT INTO", "UPDATE ", "DELETE FROM",
                                             ".COMMIT()")))
    _, st3 = patch_text("def f():\\n    pass\\n")
    check("no anchor -> refused", st3 == "anchor_missing")
    print("\\nselftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print(__doc__); return 2
    p = argv[1]
    if not os.path.isfile(p):
        print("!! not found:", p); return 2
    s = open(p, encoding="utf-8").read()
    new, st = patch_text(s)
    if st == "already_patched":
        print("already patched -- nothing to do."); return 0
    if st != "patched":
        print("!! REFUSED:", st, "-- nothing was written."); return 1
    bak = "%s.bak_S211_daygaps_r2_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8", newline="").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except py_compile.PyCompileError as ex:
        shutil.copy2(bak, p)
        print("!! compile failed -- RESTORED from", bak, "\\n", ex); return 1
    print("patched OK\\nbackup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
