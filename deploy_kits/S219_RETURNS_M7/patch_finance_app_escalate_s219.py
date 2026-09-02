#!/usr/bin/env python3
"""
patch_finance_app_escalate_s219.py -- S219 M7, part 4 of 4.

THE HALF THAT WAS MISSING. A flagged return already reached DARPAN -- his page
computes `needs` from the verdict and shows it pending. It never reached THE
OWNER. An alarm only the person being asked about it can see is not an alarm.

TWO small anchored changes to finance_app.py, both sliced verbatim from the
LIVE bytes (b42b1f08..., the M1 build installed 02-Sep 13:42):

  J  _marg_after_apply() -- escalate at the moment a day's returns become
     knowable. It already exists to run things that must never damage a
     committed apply, and the call is wrapped again inside it.
  K  api_shout() -- the safety net, over a bounded recent window, for days
     filed by any other path or before this existed.

Neither call can raise into a money path: both are inside try/except that
swallow, and the escalator itself opens nothing it cannot also explain.
Requires finance_returns_escalate.py beside finance_app.py; if that file is
absent BOTH calls are no-ops and the app behaves exactly as it does today.

SAFETY: exact-once assert, timestamped backup, compile-check with restore,
idempotent.

USAGE (one line):
  /root/wa/venv/bin/python3 -B /root/finance/patch_finance_app_escalate_s219.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('FA_PATH', '/root/finance/finance_app.py')
MARK = 'S219 M7 escalation'

J_OLD = '    try:\n        _s = _marg_apply_summary(con, iso)\n        _g = _marg_continuity_check(con, iso)\n        con.commit()\n        return _s, _g'

J_NEW = '    try:\n        _s = _marg_apply_summary(con, iso)\n        _g = _marg_continuity_check(con, iso)\n        # S219 M7 escalation: the owner\'s rule is "the moment the system flags\n        # them", and THIS is that moment -- the one place a day\'s returns\n        # become knowable. Darpan already receives them (a flagged return is\n        # `needs` on his desk by construction); the owner did not, and an alarm\n        # only Darpan can see is not an alarm to the owner. Wrapped in its own\n        # try so that an escalation can never cost a day its books.\n        try:\n            import finance_returns_escalate as _fre\n            _fre.escalate_day(con, iso, UNIT)\n        except Exception:                                    # noqa: BLE001\n            pass\n        con.commit()\n        return _s, _g'

K_OLD = '    con = db()\n    refresh_missing_days(con)\n    con.execute("UPDATE recon_exception SET shout_count = shout_count + 1, last_shout_at=? "\n                "WHERE unit=? AND status=\'open\'", (now_iso(), UNIT))'

K_NEW = '    con = db()\n    refresh_missing_days(con)\n    # S219 M7: the safety net under the apply-time escalation. A return flagged\n    # before that hook existed, or on a day filed by any other path, would\n    # otherwise never reach the owner at all. Bounded to the recent window so\n    # the watchdog stays cheap, and it re-opens a resolved day ONLY when the\n    # set of flagged bills has actually changed -- a decision the owner already\n    # made must not be undone by a cron.\n    try:\n        import finance_returns_escalate as _fre\n        _fre.escalate_recent(con, UNIT)\n    except Exception:                                        # noqa: BLE001\n        pass\n    con.execute("UPDATE recon_exception SET shout_count = shout_count + 1, last_shout_at=? "\n                "WHERE unit=? AND status=\'open\'", (now_iso(), UNIT))'

PAIRS = [("J", J_OLD, J_NEW), ("K", K_OLD, K_NEW)]


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
    bak = TARGET + ".bak_S219_m7_" + stamp
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
    print("restart  systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
