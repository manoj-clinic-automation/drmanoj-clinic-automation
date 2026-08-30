#!/usr/bin/env python3
"""
patch_marg_report_words.py -- S210: three parser sentences brought in line
with D348 and with what the system actually does.

C3 of S203_PENDENCY_RECONCILIATION proved the WALK-IN sentence wrong twice
(names a destination D348 retired; counts from the wrong authority). The CN
sentence carries developer-speak ("needs finance_ingest at S180 U1 or later")
on a box whose ingest has been S180 U1+ for months. The odd-ID sentence says
"scored low", vocabulary D348 retired. Wording only -- no parsing, no
routing, no number changes.

USAGE
    /root/wa/venv/bin/python3 patch_marg_report_words.py /root/finance/marg_report.py
    python3 patch_marg_report_words.py --selftest <copies...>
"""
import datetime, os, py_compile, shutil, sys

MARK = "S210 words"

A1 = '''        warnings.append("%d credit note(s) totalling %.2f — kept, and carried through "
                        "signed (needs finance_ingest at S180 U1 or later)"
                        % (len(cn), sum(b["net_p"] for b in cn) / 100.0))'''
N1 = '''        warnings.append("%d credit note(s) totalling %.2f — returns, kept and "
                        "carried through signed"  # ''' + MARK + '''
                        % (len(cn), sum(b["net_p"] for b in cn) / 100.0))'''

A2 = '''        warnings.append("%d of %d bills carry no clinic ID and will attribute to WALK-IN"
                        % (len(no_id), nbills))'''
N2 = '''        warnings.append("%d of %d bills carry no clinic ID — they count in sales in "
                        "full; at load, named ones park for the cross-match and "
                        "nameless ones book as WALK-IN (D348)"  # ''' + MARK + '''
                        % (len(no_id), nbills))'''


A3 = '        warnings.append("%d bill(s) carry a clinic ID that is not %d digits (%s) — scored "\n                        "low so they go to review rather than to a possibly wrong patient"\n                        % (len(odd), CLINIC_ID_DIGITS,'
N3 = '        warnings.append("%d bill(s) carry a clinic ID that is not %d digits (%s) — "\n                        "these park for review, never attached to a guessed patient"  # S210 words\n                        % (len(odd), CLINIC_ID_DIGITS,'


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    for a in (A1, A2, A3):
        if s.count(a) != 1:
            return s, "anchor_missing"
    return s.replace(A1, N1).replace(A2, N2).replace(A3, N3), "patched"


def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1; print("  FAIL:", name)
    for path in sys.argv[2:]:
        s = open(path, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s patches" % os.path.basename(path), st == "patched")
        check("  compiles", compile(out, path, "exec") is not None)
        check("  WALK-IN destination claim gone", "will attribute to WALK-IN" not in out)
        check("  S180 developer-speak gone", "S180 U1 or later" not in out)
        check("  'scored low' gone", "scored low" not in out)
        check("  D348 cited", "D348" in out)
        _, st2 = patch_text(out)
        check("  second run no-op", st2 == "already_patched")
    _, st3 = patch_text("x=1\n")
    check("no anchors -> refused", st3 == "anchor_missing")
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
    bak = "%s.bak_S210_words_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
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
