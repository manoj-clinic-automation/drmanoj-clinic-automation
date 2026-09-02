#!/usr/bin/env python3
"""
patch_audit_disputed_s220.py -- S220 F-277, part 2 of 4: the verdict.

finance_returns_audit.py (pin 200e4d1c) learns ONE new verdict:

    "identity disputed"

given when the bill that this return sits on carries an OPEN row in
identity_dispute -- the ingest found that the name on the bill and the name in
the master for that clinic ID are two different people. On the same principle
as S219's stub-guard: checking such a return against "that patient's" earlier
purchases would be checking it against a STRANGER'S, so no purchase-matching
verdict is given and none should be read into its absence. THE MONEY IS
UNAFFECTED: only the verdict changes, from a confident wrong answer into a
question.

THREE anchored changes, every OLD block sliced verbatim from the live bytes:
  A  `_identity_dispute()` -- a LOOKUP, fail-soft: a database without the
     table (the ingest patch not yet run) answers None, which restores the
     exact S219 behaviour.
  B  the roll-up: the dispute is tested BEFORE the stub, because a disputed
     row sits on a real patient_ref and would otherwise be audited against
     the wrong person.
  C  the DISCOUNTED RETURN override keeps working on a disputed row, for the
     reason S219 gave for "identity needed": gross-against-net on ONE bill
     needs no patient to be true.

Downstream, "identity disputed" is a QUESTION, not a finding:
  * finance_returns_escalate.py escalates MONEY_FLAGS only -- an allow-list --
    so it is never escalated to the owner. No change needed there.
  * darpan_app.py and the hub each carry a small list of "the audit could not
    run" verdicts; parts 3 and 4 add this one to each, so it counts as a
    question for Darpan and reads AMBER, never red.

Run on the box:
  /root/wa/venv/bin/python3 -B /root/finance/patch_audit_disputed_s220.py
Offline: FRA_PATH=/path/to/finance_returns_audit.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('FRA_PATH', '/root/finance/finance_returns_audit.py')
MARK = 'S220 F-277'

A_OLD = 'def _stub_identity(con, pid):\n'

A_NEW = '''def _identity_dispute(con, unit, bill):
    """S220 F-277: the open identity dispute on this bill, or None.

    A LOOKUP in identity_dispute, written by the ingest when the name on the
    bill and the master's name for the typed clinic ID disagree. Fail-soft
    like _stub_identity(): a database without the table answers None, which
    restores the exact behaviour that shipped at S219.
    """
    if not bill:
        return None
    try:
        r = con.execute(
            "SELECT clinic_id, bill_name, master_name FROM identity_dispute "
            "WHERE unit=? AND bill_no=? AND status='open' "
            "ORDER BY noted_at DESC LIMIT 1", (unit, bill)).fetchone()
    except Exception:
        return None
    if not r:
        return None
    return dict(clinic_id=r[0], bill_name=r[1] or "", master_name=r[2] or "")


def _stub_identity(con, pid):
'''

B_OLD = '        stub = _stub_identity(con, patient_ref_id)\n        if patient_ref_id and not stub:\n'

B_NEW = '''        stub = _stub_identity(con, patient_ref_id)
        # S220 F-277: a disputed identity is tested FIRST. The row sits on a
        # real patient_ref -- the one the typed ID points at -- but the bill
        # says it belongs to somebody else. Auditing it against that
        # patient's purchases would be judging her return by his buying, with
        # complete confidence. So, like the stub, it gets a question instead
        # of a verdict, and the money is counted exactly as before.
        disputed = _identity_dispute(con, unit, bill)
        if disputed:
            rows, flags = [], {}
            worst = "identity disputed"
            note = ("the bill names %s but clinic ID %s belongs to %s in the "
                    "master -- two different people on one ID. Until a person "
                    "says which is right, this return is not checked against "
                    "anyone's purchases, and nothing should be read into that. "
                    "The money is real and is counted."
                    % (disputed["bill_name"] or "(no name)", disputed["clinic_id"],
                       disputed["master_name"] or "(no name)"))
        elif patient_ref_id and not stub:
'''

C_OLD = '        if shortfall_material and worst in ("ok", "identity needed"):\n'

C_NEW = ('        # S220 F-277: "identity disputed" joins "identity needed" here, for\n'
         '        # the same reason -- the shortfall is one bill\'s own arithmetic.\n'
         '        if shortfall_material and worst in ("ok", "identity needed",\n'
         '                                            "identity disputed"):\n')

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
    bak = TARGET + ".bak_S220_f277_" + stamp
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
