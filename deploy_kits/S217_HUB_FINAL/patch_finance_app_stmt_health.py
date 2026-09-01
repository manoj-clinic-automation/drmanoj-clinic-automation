#!/usr/bin/env python3
"""
patch_finance_app_stmt_health.py -- S217: /finance/api/statement-health.

ONE endpoint that says, in composed sentences, what must not be missed:
  * a weekday with no day_entry            -> "not filed yet" (bad)
  * a FILED day whose ICICI statement has
    not arrived                            -> "drawer reads inflated" (warn)
  * filed days newer than the tracker's
    last visit date                        -> "Docterz report upload pending"
Serves BOTH pages: the hub's alert bar and Darpan's Hindi notice
(require maker+checker, same as cash-position). READ-ONLY.

SAFETY: exact-anchor insert above the marg-push/apply route (the S213
mechanism), refuses on drift, timestamped backup, in-process compile with
automatic restore. Idempotent by MARK.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S217 (statement health)"
ANCHOR = '@app.route("/finance/api/marg-push/apply", methods=["POST"])'

NEW = '''@app.route("/finance/api/statement-health", methods=["GET"])
def api_statement_health():
    """S217 (statement health) -- the owner's words: "make it impossible for
    me to miss it on my page." The server composes the sentences; the pages
    only display them (D349: one copy of every rule). READ-ONLY."""
    u, err = require("maker", "checker")
    if err:
        return err
    import datetime as _dt                                   # noqa: PLC0415
    con = db()
    today = _dt.date.today()
    cutoff = (today - _dt.timedelta(days=9)).isoformat()
    days = {}
    for r in con.execute(
            "SELECT business_date, status, entered_by, entered_at, "
            " approved_by, approved_at FROM day_entry "
            "WHERE unit=? AND business_date>=?", (UNIT, cutoff)):
        days[r["business_date"]] = dict(r)
    stmts = {}
    for r in con.execute(
            "SELECT statement_date, parsed_total_p FROM upi_statement "
            "WHERE unit=? AND statement_date>=?", (UNIT, cutoff)):
        stmts[r["statement_date"]] = r["parsed_total_p"]
    dz = con.execute("SELECT MAX(visit_date) m FROM patient_visit").fetchone()
    docterz_last = dz["m"] if dz and dz["m"] else None
    att, dpend, out_days = [], [], []
    latest = None
    drawer_inflated = False
    for i in range(9, -1, -1):
        d = today - _dt.timedelta(days=i)
        iso = d.isoformat()
        sunday = d.weekday() == 6
        e = days.get(iso)
        st_present = iso in stmts
        row = dict(date=iso, sunday=sunday,
                   status=(e["status"] if e else None),
                   entered_by=(e["entered_by"] if e else None),
                   entered_at=(e["entered_at"] if e else None),
                   approved_by=(e["approved_by"] if e else None),
                   approved_at=(e["approved_at"] if e else None),
                   statement=("present" if st_present
                              else ("not_expected" if sunday else "missing")),
                   bank_p=stmts.get(iso))
        out_days.append(row)
        if e:
            latest = row
        if iso == today.isoformat():
            continue        # today is not yet due -- neither filing nor bank
        if not e and not sunday:
            att.append(dict(cls="bad",
                text=u"\\u26a0 %s abhi FILE nahin hua \\u2014 din ka form pending hai." % iso,
                sub="No day entry exists for this date. Nothing reconciles "
                    "until it is filed."))
        if e and not st_present and not sunday:
            att.append(dict(cls="warn",
                text=u"\\u26a0 Bank UPI statement for %s has NOT arrived \\u2014 "
                     u"drawer will read INFLATED until it lands." % iso,
                sub="ICICI's mail lands ~11am and is pushed hourly; when it "
                    "arrives, any UPI typed as cash flags on its own."))
            drawer_inflated = True
        if e and docterz_last and iso > docterz_last:
            dpend.append(iso)
    if dpend:
        att.append(dict(cls="info",
            text=u"\\u24d8 Docterz report upload pending for: %s" % ", ".join(dpend),
            sub="Export the day report from Docterz on the clinic PC; the "
                "tracker push re-matches the waiting bills automatically."))
    return jsonify(ok=True, unit=UNIT, today=today.isoformat(),
                   days=out_days, latest_filed=latest, attention=att,
                   docterz_last=docterz_last, docterz_pending=dpend,
                   drawer_inflated=drawer_inflated)


'''


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched (%s) -- nothing to do" % MARK)
        return 0
    n = src.count(ANCHOR)
    if n != 1:
        raise SystemExit("REFUSED: anchor matches %d times (need exactly 1)." % n)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S217_health_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src.replace(ANCHOR, NEW + ANCHOR, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); original restored from %s" % (ex, bak))
    print("patched %s (%s); backup %s" % (TARGET, MARK, bak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
