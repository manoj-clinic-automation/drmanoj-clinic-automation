#!/usr/bin/env python3
"""
patch_darpan_msg.py -- F-246: stop telling the owner to do what he has done.

THE FAULT
    api_ledger_check reports, for a date with no cash_movement row:

        "NO cash_movement row for 2026-08-27 -- the transfer-out was never
         saved into the day. Record it as an owner transfer below, with the
         date, so the record exists with an audit trail."

    api_transfer writes to cash_custody_event -- deliberately: an owner
    transfer records CUSTODY, not a day-ledger movement. Its own docstring
    says so. So recording the transfer can NEVER create a cash_movement row,
    and the message stands there afterwards accusing the owner of not having
    done it. He did it, correctly, and was told he had not.

THE CHANGE
    One insertion, in the READ-ONLY reporting function only. When custody
    events exist for the date, that one sentence is rewritten to say what is
    actually true. No write path, no schema, no other message touched.

SAFETY
    anchored on an exact unique string · refuses if the anchor is missing or
    appears more than once · already-patched is detected and skipped ·
    timestamped backup · py_compile before it is left in place, and the
    ORIGINAL is restored if compilation fails.

USAGE
    python3 patch_darpan_msg.py /root/finance/darpan_app.py
    python3 patch_darpan_msg.py --selftest
"""
import datetime, os, py_compile, shutil, sys

MARK = "S209 (F-246)"

ANCHOR = ('    if not out["problems"]:\n'
          '        out["problems"].append(\n'
          '            "nothing structurally wrong found%s -- compare the rows above "')

INSERT = '''    # ''' + MARK + ''' -- an owner transfer is a CUSTODY record, not a day-ledger
    # movement, so recording one can never create a cash_movement row. The
    # original sentence told the owner to do something that could not clear it,
    # and then went on accusing him after he had done it correctly.
    if out.get("custody_events"):
        _fixed = []
        for _p in out["problems"]:
            if "the transfer-out was never saved" in _p:
                _p = ("No cash_movement row for %s in the day ledger -- and that "
                      "is expected here: an owner transfer IS recorded for this "
                      "date, shown below. An owner transfer is a custody record, "
                      "not a day-ledger movement, so it never creates a "
                      "cash_movement row. Nothing further is needed."
                      % (iso or "this date"))
            _fixed.append(_p)
        out["problems"] = _fixed

'''


def patch_text(s):
    """Return (new_text, status). status: patched | already | anchor_missing |
    anchor_ambiguous"""
    if MARK in s:
        return s, "already"
    n = s.count(ANCHOR)
    if n == 0:
        return s, "anchor_missing"
    if n > 1:
        return s, "anchor_ambiguous"
    return s.replace(ANCHOR, INSERT + ANCHOR), "patched"


def selftest():
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
        else:
            bad += 1
            print("  FAIL:", name)

    body = "def f():\n" + ANCHOR + '\n            "x")\n'
    out, st = patch_text(body)
    check("a clean file is patched", st == "patched")
    check("the insertion goes BEFORE the anchor, not after",
          out.index(MARK) < out.index('if not out["problems"]'))
    check("the patched file still compiles as Python",
          compile(out, "<t>", "exec") is not None)

    out2, st2 = patch_text(out)
    check("running it twice is a no-op", st2 == "already" and out2 == out)

    _, st3 = patch_text("def f():\n    pass\n")
    check("a file without the anchor is REFUSED, not guessed at",
          st3 == "anchor_missing")

    _, st4 = patch_text(body + body)
    check("two anchors are REFUSED as ambiguous", st4 == "anchor_ambiguous")

    # the behaviour itself, run for real
    ns = {}
    exec("def check(out, iso):\n" + INSERT + "    return out\n", ns)
    with_ev = ns["check"]({"problems": ["NO cash_movement row for X -- the "
                                        "transfer-out was never saved into the day."],
                           "custody_events": [{"a": 1}]}, "2026-08-27")
    check("with a custody event, the sentence is rewritten",
          "expected here" in with_ev["problems"][0])
    check("the rewritten sentence names the date",
          "2026-08-27" in with_ev["problems"][0])
    no_ev = ns["check"]({"problems": ["NO cash_movement row for X -- the "
                                      "transfer-out was never saved into the day."],
                         "custody_events": []}, "2026-08-27")
    check("with NO custody event, the original instruction is left alone",
          "never saved" in no_ev["problems"][0])
    other = ns["check"]({"problems": ["some other problem"],
                         "custody_events": [{"a": 1}]}, "2026-08-27")
    check("no other message is touched", other["problems"] == ["some other problem"])

    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print(__doc__)
        return 2
    p = argv[1]
    if not os.path.isfile(p):
        print("!! not found:", p)
        return 2
    s = open(p, encoding="utf-8").read()
    new, st = patch_text(s)
    if st == "already":
        print("already patched -- nothing to do.")
        return 0
    if st != "patched":
        print("!! REFUSING --", st)
        print("   The live file does not carry the exact anchor this patch expects.")
        print("   Nothing was changed. Send me the file rather than forcing it.")
        return 1
    bak = "%s.bak_S209_F246_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        shutil.copy2(bak, p)
        print("!! compile FAILED -- original restored from", bak)
        print("  ", e)
        return 1
    print("patched OK")
    print("backup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
