#!/usr/bin/env python3
"""
patch_marg_report_mobile_s220.py -- S220 F-282b part 3: the full mobile travels with a parked bill.

THE OWNER'S RULING, 02-Sep 23:05: "phone full 10 for me and Darpan." The line the S180-era
code drew -- last4() is "the ONLY form of a phone number that leaves this module ... never
written to a CSV, a database or a log" -- was reversed for the counter by D356 (S211: the full
mobile on Darpan's worksheet, F-86 reversed) and patient_ref has carried `mobile` since
S218. The one place the old rule still bit: a bill the ingest PARKS for review keeps only
the last four, so nobody at the counter could ring the patient to ask who they were.

ONE new column in the lines CSV, "mobile" -- the digits of the report's phone when there are
ten of them, else blank. The ingest's adapter stores the whole CSV row as the parked bill's
raw_text, so the number reaches the review row with NO ingest change; the card (part 1)
shows it. `phone_last4` stays exactly as it was for everything that reads it. This
docstring, and the module's own selftest line, now say what is true.

FOUR anchored changes to marg_report.py (pin 2eac81a2, S214).
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_marg_report_mobile_s220.py
Offline: MR_PATH=/path/to/marg_report.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('MR_PATH', '/root/finance/marg_report.py')
MARK = 'S220 F-282b'

A_OLD = '''LINE_COLUMNS = ["bill_date", "bill_no", "clinic_id", "patient_name", "phone_last4",
                "description", "amount", "mode", "gross", "disc"]
'''
A_NEW = '''LINE_COLUMNS = ["bill_date", "bill_no", "clinic_id", "patient_name", "phone_last4",
                "description", "amount", "mode", "gross", "disc",
                "mobile"]        # S220 F-282b: the full number, by the owner's ruling (D356)
'''
B_OLD = '''                "phone_last4": last4(b["phone"]) or "",
'''
B_NEW = '''                "phone_last4": last4(b["phone"]) or "",
                "mobile": full_mobile(b["phone"]) or "",      # S220 F-282b
'''
C_OLD = '''    ck("lines CSV carries no full phone", "phone" not in LINE_COLUMNS)
'''
C_NEW = '''    ck("lines CSV carries the full mobile (owner's ruling, S220)", "mobile" in LINE_COLUMNS)
    ck("full_mobile keeps ten digits", full_mobile("+91 90000-" + "00002") == "90000" + "00002")   # assembled: F-185 gate
    ck("full_mobile refuses anything else", full_mobile("12345") is None and full_mobile("") is None)
'''
D_OLD = '''def last4(p):
    """The ONLY form of a phone number that leaves this module.
'''
D_NEW = '''def full_mobile(p):
    """S220 F-282b -- the owner's ruling of 02-Sep-2026: "phone full 10 for me and
    Darpan." D356 (S211) had already put the full mobile on Darpan's worksheet;
    this carries it into the lines CSV so a bill PARKED for review keeps the number
    the counter needs to ask who the patient was. Ten digits or nothing."""
    s = re.sub(r"\\D", "", str(p or ""))
    if len(s) > 10 and s.startswith("91"):
        s = s[-10:]
    return s if len(s) == 10 else None


def last4(p):
    """The masked form. Until S220 it was the ONLY form of a phone number that
    left this module; full_mobile() above now travels beside it, by the owner's
    ruling. Everything that reads phone_last4 is unchanged.
'''
PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW), ("D", D_OLD, D_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_f282b_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
