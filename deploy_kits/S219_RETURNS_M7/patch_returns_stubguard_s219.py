#!/usr/bin/env python3
"""
patch_returns_stubguard_s219.py -- S219 M7, part 1 of 4.

THE FINDING, AND WHOSE IT IS: the owner's. CN00184, a sale return sitting on
the reserved WALK-IN identity, was rendered on Darpan's worksheet as
"NEVER BOUGHT" -- an accusation about a patient, drawn from a pool of 2,116
bills belonging to nobody in particular.

FIVE anchored changes to finance_returns_audit.py, every OLD block sliced
verbatim from the live bytes:

  A  a return on a shared placeholder gets "identity needed", not a money
     verdict -- and its note says why, in words the owner can hand to Darpan
  B  _stub_identity(), a lookup on the schema's OWN reserved value
  C  DISCOUNTED RETURN still fires on such a row: it is gross against net on
     one bill and needs no patient to be true
  D  the full mobile when the column exists, phone_last4 when it does not
     (D356, asked rather than assumed -- S217 repaired a 500 caused by the
     opposite assumption)
  E  the row carries `mobile` alongside `mobile_last4`

WHAT DOES NOT CHANGE: every return on a real patient is audited exactly as
before, every rupee is counted exactly as before, and no row is hidden from
any screen. This file remains READ-ONLY.

SAFETY: exact-once assert on every anchor, timestamped backup, compile-check
with automatic restore, idempotent (re-running says so and stops).

USAGE (one line):
  /root/wa/venv/bin/python3 -B /root/finance/patch_returns_stubguard_s219.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('FRA_PATH', '/root/finance/finance_returns_audit.py')
MARK = 'A STUB POOL CANNOT CORROBORATE'

A_OLD = '        patient_ref_id = b["patient_ref_id"] if b is not None else None\n        if patient_ref_id:\n            rows, flags, note = audit_return(con, bill, patient_ref_id,\n                                             business_date,\n                                             b["amount_p"] if b else None)\n            worst = ("NEVER BOUGHT" if flags.get("never_bought") else\n                     "REFUNDED MORE THAN PAID" if flags.get("refund_exceeds") else\n                     "RETURNED MORE THAN SOLD" if flags.get("qty_exceeds") else\n                     "not examinable" if flags.get("no_item_detail") else "ok")\n        else:\n'

A_NEW = '        patient_ref_id = b["patient_ref_id"] if b is not None else None\n        # S219 M7 (owner-caught, CN00184) -- A STUB POOL CANNOT CORROBORATE.\n        #\n        # The branch below already refuses to audit a return with NO patient:\n        # "never bought" would be a statement about nobody. But a return\n        # attributed to the reserved WALK-IN identity passes that test while\n        # being the very same mistake wearing a name. WALK-IN is ONE row\n        # carrying 2,116 sale rows and 121 return rows -- a pool that would\n        # corroborate almost anything put beside it, and equally, one whose\n        # silence proves nothing. A NEVER BOUGHT verdict against it is not a\n        # finding about a patient; it is an artefact of pooling.\n        #\n        # The owner found it in the wild: CN00184 reached Darpan\'s worksheet\n        # as NEVER BOUGHT -- a real accusation drawn from nothing. These rows\n        # now say the thing that is actually true, that the identity is\n        # missing, and they go to the sheet that collects exactly that.\n        #\n        # THE MONEY IS UNAFFECTED. Only the verdict changes, from an\n        # accusation into a question.\n        stub = _stub_identity(con, patient_ref_id)\n        if patient_ref_id and not stub:\n            rows, flags, note = audit_return(con, bill, patient_ref_id,\n                                             business_date,\n                                             b["amount_p"] if b else None)\n            worst = ("NEVER BOUGHT" if flags.get("never_bought") else\n                     "REFUNDED MORE THAN PAID" if flags.get("refund_exceeds") else\n                     "RETURNED MORE THAN SOLD" if flags.get("qty_exceeds") else\n                     "not examinable" if flags.get("no_item_detail") else "ok")\n        elif stub:\n            rows, flags = [], {}\n            worst = "identity needed"\n            note = ("this return is attributed to %s -- a shared placeholder, "\n                    "not a person. Checking it against that identity\'s own "\n                    "purchases would be checking it against everybody\'s, so no "\n                    "verdict is given and none should be read into its absence. "\n                    "The money is real and is counted. Name the patient and it "\n                    "becomes auditable." % stub)\n        else:\n'

B_OLD = 'def returns_for_range(con, date_from, date_to, unit="medical"):'

B_NEW = 'def _stub_identity(con, pid):\n    """The name of the shared placeholder this return sits on, or None.\n\n    \'WALK-IN\' is reserved by the schema itself -- patient_ref.clinic_id is\n    documented as "the clinic\'s own patient ID; \'WALK-IN\' is reserved" -- and\n    it is the only such identity among 7,838 rows, the other 7,837 carrying an\n    all-digit clinic ID. So this is a LOOKUP, not a heuristic: there is no\n    threshold to tune and no name-shape to guess wrong.\n\n    Fail-soft by design. This file is READ-ONLY and never raises on data; a\n    database that cannot answer this question returns None, which restores the\n    exact behaviour that shipped before S219.\n    """\n    if not pid:\n        return None\n    try:\n        r = con.execute("SELECT clinic_id, name FROM patient_ref WHERE id=?",\n                        (pid,)).fetchone()\n    except Exception:                                        # noqa: BLE001\n        return None\n    if not r:\n        return None\n    if (r["clinic_id"] or "").strip().upper() == "WALK-IN":\n        return (r["name"] or "").strip() or "WALK-IN"\n    return None\n\n\ndef returns_for_range(con, date_from, date_to, unit="medical"):'

C_OLD = '        # A clean return that was refunded short is not "ok".\n        if shortfall_material and worst == "ok":\n            worst = "DISCOUNTED RETURN"\n'

C_NEW = '        # A clean return that was refunded short is not "ok".\n        # S219 M7: "identity needed" is included deliberately. A discount\n        # withheld on a refund is gross against net on ONE bill -- it needs no\n        # patient at all to be true, so suppressing it on a stub row would hide\n        # a real money finding behind a data-quality one.\n        if shortfall_material and worst in ("ok", "identity needed"):\n            worst = "DISCOUNTED RETURN"\n'

D_OLD = 'def _return_bills(con, unit, business_date):\n    """Every return BILL of the day. Source B -- the money spine."""\n    rows = con.execute(\n        # phone_last4, NOT mobile. `mobile` exists only on the VPS (added for\n        # D356) and is absent from finance_schema.sql, so selecting it makes\n        # this file unrunnable anywhere else -- including a rehearsal box.\n        # phone_last4 exists in BOTH, and is already masked at rest, which is\n        # the owner\'s rule anyway.\n        # gross_p and disc_p are NOT selected. They exist on the live box only\n        # (S193 discount ingest) and are absent from finance_schema.sql, and\n        # the inherited query read neither of them -- it merely carried them,\n        # which made the whole function unrunnable anywhere but the VPS. Found\n        # by the S212 walk, not by a gate.\n        "SELECT s.id, s.source_ref bill, s.amount_p, "\n        "       s.patient_ref_id, p.name, p.phone_last4, p.clinic_id "\n        "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "\n        "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "\n        "WHERE e.unit=? AND e.business_date=? "\n        "AND s.service LIKE \'%!_return\' ESCAPE \'!\' "\n        "ORDER BY s.source_ref", (unit, business_date)).fetchall()\n    return collections.OrderedDict((r["bill"], r) for r in rows)'

D_NEW = 'def _has_col(con, table, col):\n    """Does this database have that column? Asked, never assumed.\n\n    S217 had to repair a live 500 -- "no such column: mobile" -- caused by code\n    written for a schema the box did not have. The opposite mistake is just as\n    real: finance_patient_sync DOES add `mobile`, so a file hard-wired to\n    phone_last4 keeps masking a number the owner ruled should be shown (D356)\n    long after the column arrives. Asking costs one pragma per day rendered.\n    """\n    try:\n        return any(r[1] == col for r in con.execute(\n            "PRAGMA table_info(%s)" % table).fetchall())\n    except Exception:                                        # noqa: BLE001\n        return False\n\n\ndef _return_bills(con, unit, business_date):\n    """Every return BILL of the day. Source B -- the money spine."""\n    # S219 M7 (D356): the full mobile is selected WHEN THE COLUMN EXISTS, and\n    # phone_last4 when it does not, so this file runs unchanged on the VPS and\n    # on a rehearsal box built from finance_schema.sql. D356 reversed F-86\'s\n    # masking for the owner\'s own console -- "it\'s for clinic internal use" --\n    # and F-185 is untouched: no number reaches the repository, only the box.\n    #\n    # gross_p and disc_p are still NOT selected. They exist on the live box\n    # only (S193 discount ingest) and are absent from finance_schema.sql, and\n    # the inherited query read neither of them -- it merely carried them, which\n    # made the whole function unrunnable anywhere but the VPS. Found by the\n    # S212 walk, not by a gate.\n    _mob = "p.mobile" if _has_col(con, "patient_ref", "mobile") else "NULL"\n    rows = con.execute(\n        "SELECT s.id, s.source_ref bill, s.amount_p, "\n        "       s.patient_ref_id, p.name, p.phone_last4, p.clinic_id, "\n        "       %s mobile "\n        "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "\n        "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "\n        "WHERE e.unit=? AND e.business_date=? "\n        "AND s.service LIKE \'%%!_return\' ESCAPE \'!\' "\n        "ORDER BY s.source_ref" % _mob, (unit, business_date)).fetchall()\n    return collections.OrderedDict((r["bill"], r) for r in rows)'

E_OLD = '            mobile_last4=(_last4(b["phone_last4"]) if b is not None else ""),'

E_NEW = '            mobile_last4=(_last4(b["phone_last4"]) if b is not None else ""),\n            # S219 M7 (D356): the full number when the box has it, "" when it\n            # does not -- never a half-number dressed as a whole one.\n            mobile=((b["mobile"] or "") if b is not None else ""),'

PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW), ("D", D_OLD, D_NEW), ("E", E_OLD, E_NEW)]


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
