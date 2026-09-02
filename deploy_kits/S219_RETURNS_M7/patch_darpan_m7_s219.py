#!/usr/bin/env python3
"""
patch_darpan_m7_s219.py -- S219 M7, part 2 of 4.

TWO rulings land here, both the owner's.

1. THE PAST IS ACCEPTED (02-Sep-2026). "Bury the historical data and take it
   as accepted." Returns before the cutover keep their verdict, their money and
   their place in the list -- nothing is deleted, because that history IS the
   baseline the detector is calibrated on -- but they raise no task and inflate
   no counter. The date is a SETTING (`returns.act_from`), not a constant, so
   he can move it without touching code.

2. "identity needed" is not an accusation. darpan_app.py keeps its OWN list of
   verdicts that do not count as flagged -- a second copy of a rule, which is
   how two copies drift apart. It already excluded "no patient attributed" and
   "not examinable". The new verdict belongs with them.

THREE anchored changes, every OLD block sliced verbatim from the live bytes:
  E1 read the cutover once, before the loop
  F  history generates no work; "identity needed" is not counted as a finding
  G  the full mobile (D356) and the `historical` flag reach the page

SAFETY: exact-once assert, timestamped backup, compile-check with restore,
idempotent.

USAGE (one line):
  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_m7_s219.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'THE PAST IS ACCEPTED'

E1_OLD = '    out = []\n    total_p = 0\n    tally = {"audited": 0, "orphan": 0, "no item detail": 0}\n    flagged = 0\n    pending = 0\n    for d in days:'

E1_NEW = '    out = []\n    total_p = 0\n    tally = {"audited": 0, "orphan": 0, "no item detail": 0}\n    flagged = 0\n    pending = 0\n    # S219 M7 -- THE OWNER\'S RULING OF 02-Sep-2026: THE PAST IS ACCEPTED.\n    # A date, in one setting, because a cutover written into code is one that\n    # cannot be moved when he decides to move it.\n    _act_from = _setting(con, "returns.act_from", "") or "2026-09-02"\n    for d in days:'

F_OLD = '            needs = (r["verdict"] != "ok")\n            if r["verdict"] not in ("ok", "no patient attributed",\n                                    "not examinable"):\n                flagged += 1'

F_NEW = '            # THE PAST IS ACCEPTED (02-Sep-2026). A return from before the\n            # cutover keeps its verdict, its money and its place in the list --\n            # the data stays whole, and it is the baseline the detector is\n            # calibrated against -- but IT GENERATES NO WORK. Nobody is asked to\n            # reconstruct an identity from April: before July the counter\n            # captured no clinic ID at all (43 of 43 in April, 36 of 36 in May),\n            # so 109 of those rows are a missing system, not a missing answer.\n            _hist = (d < _act_from)\n            needs = (r["verdict"] != "ok") and not _hist\n            # "identity needed" joins the two verdicts already excluded here,\n            # for the same reason: all three say the audit COULD NOT RUN, which\n            # is not a finding. Counting them inflates the number the owner is\n            # meant to act on, and a count that cries wolf is one he stops\n            # reading. It stays in `needs`, so the row still reaches Darpan\'s\n            # desk -- as a question, not as a charge.\n            if not _hist and r["verdict"] not in (\n                    "ok", "no patient attributed", "not examinable",\n                    "identity needed"):\n                flagged += 1'

G_OLD = '                mobile_last4=r["mobile_last4"],'

G_NEW = '                mobile_last4=r["mobile_last4"],\n                mobile=r.get("mobile", ""),          # S219 M7 (D356)\n                historical=_hist,                    # S219 M7 (the cutover)'

PAIRS = [("E1", E1_OLD, E1_NEW), ("F", F_OLD, F_NEW), ("G", G_OLD, G_NEW)]


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
