#!/usr/bin/env python3
"""
patch_darpan_returns.py -- S213: the returns card reads the SUMP, and stops
writing on a GET.

WHAT THIS CHANGES, and the ruling behind each change (SANJEEVNI_SALE_RETURNS_
FINALISED, S212; owner order ⭐1.2 at S213):

1. `/finance/darpan/api/cn-detail` is REBUILT on `finance_returns_audit`
   (the S212 sump). The old body read `sale_item WHERE service LIKE '%return%'`
   alone -- the bill spine, 63 of 179 returns. The sump takes the UNION of the
   item spine and the money spine, names the three populations (audited /
   orphan / no item detail), values every rupee through `finance_money`, and
   carries gross AND net so a discount on a refund is a verdict, not a
   rounding error.
2. THE GET NO LONGER WRITES. The old endpoint did `INSERT OR IGNORE ...
   commit()` inside the read -- loading the page created approval rows. Now
   `needs approval` is COMPUTED on read, and the row is created when the owner
   actually decides, inside the POST that was always the right place.
3. The back-audit matches on `item_key` (normalised), never raw `item_name` --
   the sump's audit_return does this natively; the old code's `sl.item_name=?`
   match is gone with the old body.
4. The owner's ruling survives verbatim: an untraceable return is not
   entertained without approval. It now also covers the orphans and the
   no-item-detail population, which the old card could not even see.

SAFETY: refuses unless the target is byte-identical to the S212-close live pin
(md5 b694bfddf7766965b6552abbe341698e) or already patched; exact-anchor
splice; timestamped backup; py_compile with automatic restore on failure.
READ-ONLY GUARANTEE: the new cn-detail contains no INSERT/UPDATE/DELETE/commit.
"""
import datetime
import hashlib
import os
import py_compile
import shutil
import sys

MARK = "S213 (returns sump r1)"
LIVE_PIN = "b694bfddf7766965b6552abbe341698e"   # /root/finance/darpan_app.py, S212 close

A_START = '@bp.route("/finance/darpan/api/cn-detail")'
A_END   = '@bp.route("/finance/darpan/api/cn-approve", methods=["POST"])'

NEW_CNDETAIL = '''@bp.route("/finance/darpan/api/cn-detail")
def api_cn_detail():
    """S213 (returns sump r1) -- every return of the month, from BOTH spines.

    The engine is finance_returns_audit (the S212 sump): the UNION of
    sale_line_item WHERE is_return=1 (the item spine -- sees the orphans) and
    sale_item WHERE service LIKE '%_return' (the money spine -- sees the bills
    with no lines). Three populations, named, never averaged. Every rupee
    through finance_money; gross and net both carried, so a discount on a
    refund is a verdict.

    READ-ONLY. The owner ruling of 30-Aug stands -- an untraceable return is
    not entertained without approval -- but the pending row is now COMPUTED
    here and CREATED only when the owner decides, in the POST below. A page
    load writes nothing (the S212 finding: the old card wrote on a GET).
    """
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    try:
        from finance_returns_audit import returns_for_day                  # noqa: PLC0415
    except ImportError:
        return jsonify(ok=False, error="module_absent",
                       message="finance_returns_audit.py is not in "
                               "/root/finance/ -- install S212_SUMP first"), 503
    month = str(request.args.get("month") or "").strip() or \\
        dt.date.today().isoformat()[:7]
    lo, hi = month + "-01", month + "-31"
    # day discovery: the same union returns_for_range uses, kept identical on
    # purpose -- run per-day here so every return can carry its date.
    days = [r[0] for r in con.execute(
        "SELECT DISTINCT business_date FROM sale_line_item "
        "WHERE unit=? AND is_return=1 AND business_date BETWEEN ? AND ? "
        "UNION "
        "SELECT DISTINCT e.business_date FROM sale_item s "
        "JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' "
        "AND e.business_date BETWEEN ? AND ? ORDER BY 1 DESC",
        (_unit, lo, hi, _unit, lo, hi))]
    out = []
    total_p = 0
    tally = {"audited": 0, "orphan": 0, "no item detail": 0}
    flagged = 0
    pending = 0
    for d in days:
        rows, _summary = returns_for_day(con, d, _unit)
        for r in rows:
            total_p += r["amount_p"]
            tally[r["population"]] = tally.get(r["population"], 0) + 1
            needs = (r["verdict"] != "ok")
            if r["verdict"] not in ("ok", "no patient attributed",
                                    "not examinable"):
                flagged += 1
            appr = con.execute(
                "SELECT status, decided_by, decided_at, note FROM "
                "darpan_return_approval WHERE unit=? AND cn_bill=?",
                (_unit, r["bill"])).fetchone()
            if needs and (appr is None or appr["status"] == "pending"):
                pending += 1
            # the bill as Marg exported it -- shown even when the audit could
            # not run (an orphan has lines but no patient; they are still real)
            marg = [dict(seq=m["seq"], item=m["item_name"], qty=m["qty_raw"],
                         pack=m["pack"], rate_p=m["amount_p"],
                         batch=m["batch"], expiry=m["expiry_ym"])
                    for m in con.execute(
                        "SELECT seq, item_name, qty_raw, pack, amount_p, "
                        "batch, expiry_ym FROM sale_line_item "
                        "WHERE unit=? AND bill_no=? AND is_return=1 "
                        "ORDER BY seq", (_unit, r["bill"]))]
            out.append(dict(
                date=d, bill=r["bill"], population=r["population"],
                amount_p=r["amount_p"], gross_p=r["gross_p"],
                net_p=r["net_p"], refund_shortfall_p=r["refund_shortfall_p"],
                money_from=r["money_from"], verdict=r["verdict"],
                note=r["note"], flags=r["flags"],
                name=r["name"], clinic_id=r["clinic_id"],
                mobile_last4=r["mobile_last4"],
                audit_lines=r["lines"], marg_lines=marg,
                needs_approval=needs,
                approval=(dict(appr) if appr else None)))
    return jsonify(ok=True, month=month, count=len(out), total_p=total_p,
                   audited=tally.get("audited", 0),
                   orphans=tally.get("orphan", 0),
                   no_item_detail=tally.get("no item detail", 0),
                   flagged=flagged, pending_approval=pending, notes=out)


'''

OLD_404 = '''    r = con.execute("SELECT id, status FROM darpan_return_approval "
                    "WHERE unit=? AND cn_bill=?", (_unit, bill)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found",
                       message="no pending approval for %s" % bill), 404'''

NEW_404 = '''    # S213 (returns sump r1): the GET no longer writes, so the row may not
    # exist yet -- the owner's decision is what creates it. business_date
    # comes from the return itself (either spine), refusing a bill this
    # server has never seen.
    r = con.execute("SELECT id, status FROM darpan_return_approval "
                    "WHERE unit=? AND cn_bill=?", (_unit, bill)).fetchone()
    if not r:
        d0 = con.execute(
            "SELECT business_date d FROM sale_line_item "
            "WHERE unit=? AND bill_no=? AND is_return=1 "
            "UNION "
            "SELECT e.business_date d FROM sale_item s "
            "JOIN day_entry e ON e.id=s.day_entry_id "
            "WHERE e.unit=? AND s.source_ref=? "
            "AND s.service LIKE '%!_return' ESCAPE '!' LIMIT 1",
            (_unit, bill, _unit, bill)).fetchone()
        if not d0:
            return jsonify(ok=False, error="not_found",
                           message="no return bill %s on this server" % bill), 404
        con.execute("INSERT OR IGNORE INTO darpan_return_approval "
                    "(unit, cn_bill, business_date) VALUES (?,?,?)",
                    (_unit, bill, d0["d"]))
        r = con.execute("SELECT id, status FROM darpan_return_approval "
                        "WHERE unit=? AND cn_bill=?", (_unit, bill)).fetchone()'''


def patch_text(s, skip_pin=False):
    if MARK in s:
        return s, "already_patched"
    if not skip_pin:
        h = hashlib.md5(s.encode("utf-8")).hexdigest()
        if h != LIVE_PIN:
            return s, "not_the_live_bytes (md5 %s; expected %s)" % (h, LIVE_PIN)
    i = s.find(A_START)
    j = s.find(A_END)
    if i < 0 or j < 0 or s.count(A_START) != 1 or s.count(A_END) != 1 or j <= i:
        return s, "anchor_missing_or_ambiguous"
    if OLD_404 not in s or s.count(OLD_404) != 1:
        return s, "approve_anchor_missing"
    s2 = s[:i] + NEW_CNDETAIL + s[j:]
    s2 = s2.replace(OLD_404, NEW_404)
    return s2, "patched"


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
        check("  cn-approve route SURVIVES", out.count(A_END) == 1)
        check("  the sump is the source",
              "from finance_returns_audit import returns_for_day" in out)
        body = out[out.find(A_START):out.find(A_END)]
        check("  READ-ONLY GET: no write statement in cn-detail",
              all(w not in body.upper() for w in
                  ("INSERT INTO", "INSERT OR IGNORE", "UPDATE ", "DELETE FROM",
                   ".COMMIT()")))
        check("  the three populations are named",
              all(k in body for k in ('"audited"', '"orphan"', '"no item detail"')))
        check("  gross and net both travel", "gross_p" in body and "net_p" in body)
        check("  the owner ruling survives in the POST",
              "INSERT OR IGNORE INTO darpan_return_approval" in out)
        check("  raw item_name matching is gone",
              "sl.item_name=?" not in out)
    _, st3 = patch_text("x=1\n")
    check("wrong bytes -> refused by pin", st3.startswith("not_the_live_bytes"))
    _, st4 = patch_text("x=1\n", skip_pin=True)
    check("no anchor -> refused", st4 == "anchor_missing_or_ambiguous")
    print("\nselftest: %d passed, %d failed" % (ok, bad))
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
    bak = "%s.bak_S213_returns_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8", newline="").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except py_compile.PyCompileError as ex:
        shutil.copy2(bak, p)
        print("!! compile failed -- RESTORED from", bak, "\n", ex); return 1
    print("patched OK\nbackup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
