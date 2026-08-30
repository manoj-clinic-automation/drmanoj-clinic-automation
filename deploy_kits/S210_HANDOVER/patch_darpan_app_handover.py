#!/usr/bin/env python3
"""
patch_darpan_app_handover.py -- S210: Darpan can finally RECORD a transfer.

THE GAP (owner, 30-Aug): "i dont see a money transfer section in his page."
The money model has three routes out of the drawer -- bank deposit, Dr
Bhawna, Dr Manoj -- and a RETURN leg (the doctors mostly hand it back for
banking later). Darpan's page could record NONE of them. Every transfer so
far was either typed on the old entry form or entered by the owner.

THE ROUTE -- POST /finance/darpan/api/handover  (maker or checker)
    body: {kind, amount, note?}  kind in:
        bank        drawer -> bank deposit        (reduces unbanked)
        to_bhawna   drawer -> Dr Bhawna           (location move)
        to_manoj    drawer -> Dr Manoj            (location move)
        back_bhawna Dr Bhawna -> drawer (return)  (location move)
        back_manoj  Dr Manoj  -> drawer (return)  (location move)
    Writes ONE cash_movement row (the S194 convention for day-form
    hand-overs), anchored to the latest filed day. THE ONE-RECORD RULE IS
    ENFORCED: if a custody event with the same date+party+amount already
    exists, the write is REFUSED -- recording the same handover in both
    tables double-counts (the S210 boundary finding, measured).

SAFETY: exact anchor (inserted before api_submit); refuse if absent or
ambiguous; backup; py_compile with auto-restore.

USAGE
    /root/wa/venv/bin/python3 patch_darpan_app_handover.py /root/finance/darpan_app.py
    python3 patch_darpan_app_handover.py --selftest <darpan_app copies...>
"""
import datetime, os, py_compile, shutil, sys

MARK = "S210 (handover)"

A1 = '''@bp.route("/finance/darpan/api/submit", methods=["POST"])'''

N1 = '''@bp.route("/finance/darpan/api/handover", methods=["POST"])
def api_handover():
    """%s -- Darpan records a drawer transfer: bank deposit, to a doctor, or
    a doctor's RETURN to the drawer. One cash_movement row (S194 convention),
    anchored to the latest filed day. Refuses a handover already recorded as
    a custody event for the same date+party+amount -- one handover, ONE
    record (S210 boundary finding: the app SUMS the two tables)."""
    u, err = _require("maker", "checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    KINDS = {"bank":        ("out", "bank"),
             "to_bhawna":   ("out", "dr_bhawna"),
             "to_manoj":    ("out", "dr_manoj"),
             "back_bhawna": ("in",  "dr_bhawna"),
             "back_manoj":  ("in",  "dr_manoj")}
    kind = str(b.get("kind") or "").strip()
    if kind not in KINDS:
        return jsonify(ok=False, error="bad_kind", kinds=sorted(KINDS)), 400
    try:
        amt_p = int(round(float(b.get("amount") or 0) * 100))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount"), 400
    if amt_p <= 0:
        return jsonify(ok=False, error="amount_must_be_positive"), 400
    note = str(b.get("note") or "").strip()[:120]
    direction, party = KINDS[kind]
    con = _db()
    ensure_schema(con)
    today = dt.date.today().isoformat()
    anchor = con.execute(
        "SELECT id, business_date FROM day_entry WHERE unit=? AND "
        "business_date<=? ORDER BY business_date DESC LIMIT 1",
        (_unit, today)).fetchone()
    if not anchor:
        return jsonify(ok=False, error="no_filed_day",
                       message="koi din file nahin hua -- pehle din ki "
                               "report load honi chahiye"), 409
    dup = con.execute(
        "SELECT id FROM cash_custody_event WHERE unit=? AND amount_p=? "
        "AND (from_party=? OR to_party=?) AND event_date>=?",
        (_unit, amt_p, party, party, anchor["business_date"])).fetchone()
    if dup:
        return jsonify(ok=False, error="already_recorded",
                       message="yeh handover pehle se owner transfer mein "
                               "likha hai -- dubara likhne se hisaab double "
                               "ho jayega"), 409
    ref = ("[darpan handover] %%s%%s" %% (kind, (" -- " + note) if note else ""))[:120]
    con.execute("INSERT INTO cash_movement (day_entry_id, direction, party, "
                "amount_p, reference) VALUES (?,?,?,?,?)",
                (anchor["id"], direction, party, amt_p, ref))
    _audit(con, u["user"], "darpan_handover",
           {"kind": kind, "amount_p": amt_p, "party": party,
            "direction": direction, "anchor_date": anchor["business_date"],
            "note": note})
    con.commit()
    return jsonify(ok=True, kind=kind, amount_p=amt_p,
                   anchor_date=anchor["business_date"])


@bp.route("/finance/darpan/api/submit", methods=["POST"])''' % MARK


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    n = s.count(A1)
    if n != 1:
        return s, ("anchor_missing" if n == 0 else "anchor_ambiguous")
    return s.replace(A1, N1), "patched"


def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1; print("  FAIL:", name)
    for path in sys.argv[2:]:
        s = open(path, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s: patches" % path.split("/")[-2], st == "patched")
        check("  compiles", compile(out, path, "exec") is not None)
        check("  five kinds incl. both return legs",
              all(k in out for k in ("back_bhawna", "back_manoj", "to_bhawna", "to_manoj", '"bank"')))
        check("  one-record refusal present", "already_recorded" in out)
        check("  audit row written", "darpan_handover" in out)
        _, st2 = patch_text(out)
        check("  second run no-op", st2 == "already_patched")
    _, st3 = patch_text("x=1\n")
    check("no anchor -> refused", st3 == "anchor_missing")
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print(__doc__); return 2
    p = argv[1]
    s = open(p, encoding="utf-8").read()
    new, st = patch_text(s)
    if st == "already_patched":
        print("already patched -- nothing to do."); return 0
    if st != "patched":
        print("!! REFUSING --", st, "\n   Nothing changed."); return 1
    bak = "%s.bak_S210_ho_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        shutil.copy2(bak, p)
        print("!! compile FAILED -- restored from", bak); print("  ", e); return 1
    print("patched OK"); print("backup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
