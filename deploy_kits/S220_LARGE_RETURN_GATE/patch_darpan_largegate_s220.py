#!/usr/bin/env python3
"""
patch_darpan_largegate_s220.py -- S220 item 1, part 1 of 3: THE LARGE-RETURN GATE.

THE FINDING (S220, on the live db copy): the near-doubling of returns May->Aug is
not MORE returns (counts flat: 43 / 31 / 39 / 43) but BIGGER ones -- the average
rose Rs 232 -> Rs 433, and returns of Rs 1,000 or more went from ZERO in May to
SIX in August: Rs 8,330, 45% of the month. The setting `returns.large_p`
(100000 paise = Rs 1,000) has existed since S208 and NOTHING enforces it.

THE OWNER'S RULING (02-Sep): a return of Rs 1,000 or more is not settled until
he taps OK on the returns card the same day; and its items go on the
SPOT-COUNT list -- "random stock checks of the items which we flag could be a
deterrent" (stock checking is otherwise suspended).

FOUR anchored changes to darpan_app.py (pin f2ac3b17, the S220 F-277 bytes):
  A  two helpers before the cn-detail route: `_spot_checks()` (the month's
     spot-count list, creating its table on first use) and the POST endpoint
     `/finance/darpan/api/spot-check` (mark one item counted -- owner only,
     the counted quantity and a note recorded, dated, named).
  B  read `returns.large_p` once per request, beside `returns.act_from`.
  C  a large return NEEDS the owner's decision even when its verdict is "ok"
     -- it joins `needs`, so it counts as PENDING (the NEED YOU badge) until
     approved or rejected through the existing cn-approve flow. It is NOT
     added to `flagged` -- size is not a money finding.
  D  the row carries `large`; the response carries `large_p` and the month's
     `spot_checks`, so the card can show both without a second request.
The spot-count rows themselves are WRITTEN by finance_returns_escalate.py
(part 2), which runs after every Apply and hourly -- never on a GET (S212).

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_largegate_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 LARGE-RETURN GATE'

A_OLD = '@bp.route("/finance/darpan/api/cn-detail")\ndef api_cn_detail():\n'

A_NEW = '''# ---- S220 LARGE-RETURN GATE: the spot-count list ------------------------------
SPOT_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS stock_spot_check ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " bill_no TEXT NOT NULL, item_key TEXT NOT NULL, item_name TEXT, batch TEXT,"
    " reason TEXT NOT NULL, requested_at TEXT NOT NULL,"
    " status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','done','skipped')),"
    " counted_qty TEXT, counted_by TEXT, counted_at TEXT, note TEXT,"
    " UNIQUE(unit, bill_no, item_key))")


def _spot_checks(con, unit, month):
    """The spot-count list: items the system flagged (a large return, or a money
    verdict) that a person should physically count. Rows are written by
    finance_returns_escalate (after Apply, and hourly) -- never here."""
    try:
        con.execute(SPOT_SCHEMA)
        rows = con.execute(
            "SELECT id, business_date, bill_no, item_key, item_name, batch, reason, "
            "status, counted_qty, counted_by, counted_at, note FROM stock_spot_check "
            "WHERE unit=? AND business_date LIKE ? ORDER BY status='due' DESC, "
            "business_date DESC, id", (unit, month + "%")).fetchall()
        return [dict(r) for r in rows]
    except Exception:                                        # noqa: BLE001
        return []


@bp.route("/finance/darpan/api/spot-check", methods=["POST"])
def api_spot_check():
    """Mark one spot-count item counted (or skipped). Owner only. What was
    counted is recorded as typed, with the name and the time; the tool never
    judges the count -- the difference against Marg's stock is a later read."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    try:
        sid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        sid = 0
    status = str(b.get("status") or "done").strip()
    if status not in ("done", "skipped"):
        return jsonify(ok=False, error="bad_status"), 400
    qty = str(b.get("counted_qty") or "").strip()
    note = str(b.get("note") or "").strip()
    if status == "done" and not qty:
        return jsonify(ok=False, error="qty_required",
                       message="a count records the quantity counted"), 400
    con.execute(SPOT_SCHEMA)
    r = con.execute("SELECT id, status FROM stock_spot_check WHERE id=? AND unit=?",
                    (sid, _unit)).fetchone()
    if r is None:
        return jsonify(ok=False, error="not_found"), 404
    con.execute("UPDATE stock_spot_check SET status=?, counted_qty=?, counted_by=?, "
                "counted_at=?, note=? WHERE id=?",
                (status, qty or None, u["user"], now_iso(), note or None, sid))
    _audit(con, u["user"], "spot_check_" + status, {"id": sid, "counted_qty": qty, "note": note})
    con.commit()
    return jsonify(ok=True, id=sid, status=status)
# ---- end S220 LARGE-RETURN GATE ---------------------------------------------------


@bp.route("/finance/darpan/api/cn-detail")
def api_cn_detail():
'''

B_OLD = '    _act_from = _setting(con, "returns.act_from", "") or "2026-09-02"\n    for d in days:\n'

B_NEW = ('    _act_from = _setting(con, "returns.act_from", "") or "2026-09-02"\n'
         '    # S220 LARGE-RETURN GATE: the line above which a return needs the owner\'s\n'
         '    # OK regardless of verdict. A setting since S208; enforced from here.\n'
         '    try:\n'
         '        _large_p = int(_setting(con, "returns.large_p", "100000") or 100000)\n'
         '    except (TypeError, ValueError):\n'
         '        _large_p = 100000\n'
         '    for d in days:\n')

C_OLD = '            _hist = (d < _act_from)\n            needs = (r["verdict"] != "ok") and not _hist\n'

C_NEW = ('            _hist = (d < _act_from)\n'
         '            # S220 LARGE-RETURN GATE: Rs 1,000+ (returns.large_p) needs the\n'
         '            # owner\'s decision even when the audit says ok -- size is where\n'
         '            # the money moved (0 -> 6 such returns, May -> Aug). It joins\n'
         '            # `needs` (PENDING until decided), never `flagged`.\n'
         '            _large = (int(r["amount_p"] or 0) >= _large_p) and not _hist\n'
         '            needs = ((r["verdict"] != "ok") or _large) and not _hist\n')

D1_OLD = '                historical=_hist,                    # S219 M7 (the cutover)\n'
D1_NEW = ('                historical=_hist,                    # S219 M7 (the cutover)\n'
          '                large=_large,                        # S220 LARGE-RETURN GATE\n')

D2_OLD = '                   flagged=flagged, pending_approval=pending, notes=out)\n'
D2_NEW = ('                   flagged=flagged, pending_approval=pending, notes=out,\n'
          '                   large_p=_large_p, spot_checks=_spot_checks(con, _unit, month))\n')

PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW),
         ("D1", D1_OLD, D1_NEW), ("D2", D2_OLD, D2_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_large_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s -- the live file is unchanged." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
