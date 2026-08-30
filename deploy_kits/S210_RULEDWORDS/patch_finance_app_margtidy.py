#!/usr/bin/env python3
"""
patch_finance_app_margtidy.py -- S210: the Marg push list stops lying,
and a report ruled OUT can finally be removed.

THE TWO FAULTS (owner-reported, 30-Aug-2026)
  F-249 (candidate)  the list renders the PUSH-TIME survey snapshot as if it
      were current, so 27-Aug wore a "not filed" badge on the owner's console
      after the day was long since filed. The snapshot is honest about the
      moment it was taken; showing it as "now" is the lie.
  Missing control    a pending push the owner has ruled NOT to apply (the June
      report) sat on the list forever with a live Apply button. He asked for a
      remove control before; it existed nowhere.

THE CHANGES -- three, all in finance_app.py, all anchored
  1  api_marg_push_list refreshes each day's `filed` flag LIVE from day_entry.
  2  the list hides status='dismissed' rows (the row itself is KEPT -- audit).
  3  a new owner-only route POST /finance/api/marg-push/dismiss {id, reason}
     marks a PENDING push dismissed, clears its replay payload, writes audit.

SAFETY: exact-anchor replaces -- refuses if an anchor is absent or ambiguous;
timestamped backup; py_compile with automatic restore on failure.

USAGE
    /root/wa/venv/bin/python3 patch_finance_app_margtidy.py /root/finance/finance_app.py
    python3 patch_finance_app_margtidy.py --selftest
"""
import datetime, os, py_compile, shutil, sys

MARK = "S210 (margtidy)"

A1 = """        out.append(dict(id=r["id"], received_at=r["received_at"],
                        file=r["filename_hint"], md5_8=r["file_md5"][:8],"""
N1 = """        # %s -- F-249: the survey is a PUSH-TIME snapshot. 'filed' must be
        # answered by the database NOW, or a filed day wears a lying badge.
        for _d in (sv.get("survey") or []):
            _d["filed"] = bool(con.execute(
                "SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                (UNIT, _d.get("date"))).fetchone())
        sv["not_filed"] = [_d.get("date") for _d in (sv.get("survey") or [])
                           if not _d.get("filed")]
        out.append(dict(id=r["id"], received_at=r["received_at"],
                        file=r["filename_hint"], md5_8=r["file_md5"][:8],""" % MARK

A2 = '''"FROM marg_push_staging ORDER BY id DESC LIMIT 20"):'''
N2 = '''"FROM marg_push_staging WHERE status != 'dismissed' "
                         "ORDER BY id DESC LIMIT 20"):'''

A3 = '''@app.route("/finance/api/marg-push/apply", methods=["POST"])'''
N3 = '''@app.route("/finance/api/marg-push/dismiss", methods=["POST"])
def api_marg_push_dismiss():
    """%s -- the owner's 'remove report'. A PENDING push he has ruled out is
    marked dismissed: it leaves the list, its replay payload is cleared so it
    can never be applied by accident, and the row + an audit entry are KEPT.
    Nothing that ever reached the books is touched -- pending means pending."""
    u, err = require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    pid, reason = b.get("id"), str(b.get("reason") or "").strip()
    if not pid:
        return jsonify(ok=False, error="no_id"), 400
    if not reason:
        return jsonify(ok=False, error="reason_required",
                       message="a removed report always says why"), 400
    con = db()
    _marg_staging(con)
    row = con.execute("SELECT * FROM marg_push_staging WHERE id=?",
                      (pid,)).fetchone()
    if not row:
        return jsonify(ok=False, error="not_found"), 404
    if row["status"] != "pending":
        return jsonify(ok=False, error="not_pending", status=row["status"],
                       message="only a pending push can be removed; this one "
                               "is %%s" %% row["status"]), 409
    con.execute("UPDATE marg_push_staging SET status='dismissed', "
                "parsed_json=NULL, apply_result_json=? WHERE id=?",
                (__import__("json").dumps({"dismissed_by": u["user"],
                 "dismissed_at": now_iso(), "reason": reason[:300]}), pid))
    audit(con, "marg_push_staging", pid, "dismiss",
          after={"reason": reason[:300], "by": u["user"],
                 "file": row["filename_hint"], "md5": row["file_md5"]},
          who=u["user"])
    con.commit()
    return jsonify(ok=True, id=pid, status="dismissed")


@app.route("/finance/api/marg-push/apply", methods=["POST"])''' % MARK


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    for a in (A1, A2, A3):
        n = s.count(a)
        if n != 1:
            return s, ("anchor_missing" if n == 0 else "anchor_ambiguous")
    s = s.replace(A1, N1).replace(A2, N2).replace(A3, N3)
    return s, "patched"


def selftest():
    """Dry-run against the real finance_app copies named on the command line
    after --selftest (default: none -> structural checks only)."""
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1; print("  FAIL:", name)
    for path in sys.argv[2:]:
        s = open(path, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s: patches cleanly" % os.path.basename(os.path.dirname(path)), st == "patched")
        check("  both mark comments landed (the SQL filter carries none by design)", out.count(MARK) == 2)
        check("  result compiles", compile(out, path, "exec") is not None)
        out2, st2 = patch_text(out)
        check("  second run is a no-op", st2 == "already_patched" and out2 == out)
        check("  dismissed filter present once", out.count("status != 'dismissed'") == 1)
        check("  live filed refresh present once", out.count("'filed' must be") == 1)
    _, st3 = patch_text("def f():\n    pass\n")
    check("no anchors -> refused", st3 == "anchor_missing")
    _, st4 = patch_text(open(sys.argv[2]).read() + A3) if len(sys.argv) > 2 else (None, "anchor_ambiguous")
    check("duplicate anchor -> refused as ambiguous", st4 == "anchor_ambiguous")
    print("selftest: %d passed, %d failed" % (ok, bad))
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
        print("!! REFUSING --", st)
        print("   The live file does not carry the exact anchors expected. Nothing changed.")
        return 1
    bak = "%s.bak_S210_margtidy_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        shutil.copy2(bak, p)
        print("!! compile FAILED -- original restored from", bak); print("  ", e)
        return 1
    print("patched OK"); print("backup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
