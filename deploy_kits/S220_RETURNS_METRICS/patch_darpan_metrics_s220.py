#!/usr/bin/env python3
"""
patch_darpan_metrics_s220.py -- S220 item 2, part 1 of 2: THE TWO LINES.

THE OWNER'S QUESTION (02-Sep): "total returns -- out of it what amount surfaces
in analytics with intent flags, so we have a metric to track?"  And: "I get a
gist, expandable down to the last detail, in the same place."

MEASURED on the live db (the S220 design brief SS9): July 71% examinable / 50%
flagged; August 75% / 29%. Two lines from here, on the card that exists:
  EXAMINABLE %  -- of the month's return rupees, the share the audit could
                   actually judge (target >= 98; the identity work closes it)
  FLAGGED %     -- of the month's return rupees, the share carrying a MONEY
                   verdict (watched, not targeted -- the first F-277 morning
                   should make it FALL, and that fall is the measurement)
plus the gist line: the month's returns as a share of the month's SALES, with
the previous month beside it, and the count that needs the owner.

THREE anchored changes to darpan_app.py (pin b24ecef3, the large-gate bytes):
  A  two tallies beside `flagged`/`pending`
  B  every row adds its rupees to one of them
  C  `metrics` in the response: examinable_p, flagged_p, sales_p, rate_pct,
     prev_month, prev_rate_pct -- the rate from the bill spine on BOTH months
     (one source, one rule; D349), the shares from the audit's own verdicts.
No new table, no write. English only (owner's console).

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_metrics_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 METRICS'

A_OLD = '    flagged = 0\n    pending = 0\n'
A_NEW = ('    flagged = 0\n    pending = 0\n'
         '    # S220 METRICS: rupees the audit could judge, and rupees it flagged.\n'
         '    _examinable_p = 0\n'
         '    _flagged_p = 0\n'
         '    _CANT = ("not examinable", "identity needed", "identity disputed",\n'
         '             "no patient attributed")\n'
         '    try:\n'
         '        from finance_returns_escalate import MONEY_FLAGS as _MONEY   # noqa: PLC0415\n'
         '    except Exception:                                                # noqa: BLE001\n'
         '        _MONEY = ("NEVER BOUGHT", "REFUNDED MORE THAN PAID",\n'
         '                  "RETURNED MORE THAN SOLD", "DISCOUNTED RETURN")\n')

B_OLD = '            total_p += r["amount_p"]\n'
B_NEW = ('            total_p += r["amount_p"]\n'
         '            if r["verdict"] not in _CANT:                 # S220 METRICS\n'
         '                _examinable_p += r["amount_p"]\n'
         '            if r["verdict"] in _MONEY:\n'
         '                _flagged_p += r["amount_p"]\n')

C_OLD = '                   large_p=_large_p, spot_checks=_spot_checks(con, _unit, month))\n'
C_NEW = ('                   large_p=_large_p, spot_checks=_spot_checks(con, _unit, month),\n'
         '                   metrics=_month_metrics(con, _unit, month, total_p, _examinable_p, _flagged_p))\n'
         '\n'
         '\n'
         'def _month_metrics(con, unit, month, total_p, examinable_p, flagged_p):\n'
         '    """S220 METRICS: the gist line\'s numbers. The return RATE is returns / sales\n'
         '    on the bill spine for this month and the previous one -- the same source and\n'
         '    the same rule for both, so the arrow never compares two definitions (D349).\n'
         '    The examinable and flagged shares come from the audit\'s verdicts above.\n'
         '    Fail-soft: anything it cannot compute is None, and the card says so."""\n'
         '    def _spine(m):\n'
         '        try:\n'
         '            r = con.execute(\n'
         '                "SELECT COALESCE(SUM(CASE WHEN s.service LIKE \'%!_return\' ESCAPE \'!\' THEN s.amount_p END),0),"\n'
         '                " COALESCE(SUM(CASE WHEN s.service NOT LIKE \'%!_return\' ESCAPE \'!\' THEN s.amount_p END),0)"\n'
         '                " FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id"\n'
         '                " WHERE e.unit=? AND substr(e.business_date,1,7)=?", (unit, m)).fetchone()\n'
         '            return int(r[0] or 0), int(r[1] or 0)\n'
         '        except Exception:                                            # noqa: BLE001\n'
         '            return 0, 0\n'
         '    try:\n'
         '        y, mo = int(month[:4]), int(month[5:7])\n'
         '        prev = "%04d-%02d" % ((y - 1, 12) if mo == 1 else (y, mo - 1))\n'
         '    except Exception:                                                # noqa: BLE001\n'
         '        prev = None\n'
         '    ret_p, sales_p = _spine(month)\n'
         '    pret_p, psales_p = _spine(prev) if prev else (0, 0)\n'
         '    pct = lambda a, b: (round(100.0 * a / b, 1) if b else None)\n'
         '    return dict(examinable_p=examinable_p, flagged_p=flagged_p,\n'
         '                examinable_pct=pct(examinable_p, total_p), flagged_pct=pct(flagged_p, total_p),\n'
         '                sales_p=sales_p, rate_pct=pct(ret_p, sales_p),\n'
         '                prev_month=prev, prev_rate_pct=pct(pret_p, psales_p))\n')

PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW)]


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
    bak = TARGET + ".bak_S220_metrics_" + stamp
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
