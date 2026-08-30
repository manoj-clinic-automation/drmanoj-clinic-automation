#!/usr/bin/env python3
"""
patch_darpan_msg.py -- F-246: stop telling the owner to do what he has done.

THE FAULT
    api_ledger_check told the owner: "the transfer-out was never saved into the
    day. Record it as an owner transfer below." api_transfer writes to
    cash_custody_event, so doing exactly that could never clear the message --
    and it went on accusing him afterwards.

WHAT IS AND IS NOT CLAIMED (the owner's own correction, S209)
    It IS a cash movement in real life: drawer -> Dr Bhawna. Calling it "not a
    cash movement" was wrong. What is true is narrower: no row was written into
    that day's ledger, so the DAY still counts the cash in the drawer, and the
    custody record is where the override lives. The new sentence says exactly
    that and nothing more.

THE CHANGE
    One insertion, in the READ-ONLY reporting function only. No write path, no
    schema, no query, no other message.

SAFETY
    anchored on one exact string · refuses if absent or ambiguous · a previous
    S209 block is REPLACED, so wording can be updated rather than stuck at v1 ·
    timestamped backup · py_compile, with the original restored on failure.

USAGE
    python3 patch_darpan_msg.py /root/finance/darpan_app.py
    python3 patch_darpan_msg.py --selftest
"""
import datetime, os, py_compile, shutil, sys

MARK = "S209 (F-246)"

ANCHOR = ('    if not out["problems"]:\n'
          '        out["problems"].append(\n'
          '            "nothing structurally wrong found%s -- compare the rows above "')

INSERT = '''    # ''' + MARK + ''' -- the day ledger and the custody record answer
    # different questions. This sentence used to prescribe a remedy that could
    # not satisfy it, and then kept accusing the owner after he had done it.
    if out.get("custody_events"):
        _fixed = []
        for _p in out["problems"]:
            if "the transfer-out was never saved" in _p:
                _p = ("No cash_movement row for %s, so the day ledger still "
                      "counts this cash in the drawer. Your override below "
                      "records where it actually went -- dated, signed, in the "
                      "custody record." % (iso or "this date"))
            _fixed.append(_p)
        out["problems"] = _fixed

'''


def _strip_old(s):
    """Remove a previously inserted S209 block so wording can be UPDATED.
    Idempotence must not mean 'stuck on version one'."""
    if MARK not in s or ANCHOR not in s:
        return s
    a = s.index(ANCHOR)
    m = s.rfind("    # " + MARK, 0, a)
    return s if m == -1 else s[:m] + s[a:]


def patch_text(s):
    """-> (new_text, status): patched | updated | anchor_missing | anchor_ambiguous"""
    was = MARK in s
    s = _strip_old(s)
    n = s.count(ANCHOR)
    if n == 0:
        return s, "anchor_missing"
    if n > 1:
        return s, "anchor_ambiguous"
    return s.replace(ANCHOR, INSERT + ANCHOR), ("updated" if was else "patched")


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
    check("the block lands BEFORE the anchor",
          out.index(MARK) < out.index('if not out["problems"]'))
    check("the patched file compiles", compile(out, "<t>", "exec") is not None)

    out2, st2 = patch_text(out)
    check("running again UPDATES rather than skipping", st2 == "updated")
    check("running again does not duplicate the block",
          out2.count("# " + MARK) == 1)
    check("the updated file still compiles",
          compile(out2, "<t>", "exec") is not None)
    check("an update is byte-identical to a fresh patch", out2 == out)

    _, st3 = patch_text("def f():\n    pass\n")
    check("no anchor -> REFUSED, not guessed at", st3 == "anchor_missing")
    _, st4 = patch_text(body + body)
    check("two anchors -> REFUSED as ambiguous", st4 == "anchor_ambiguous")

    ns = {}
    exec("def chk(out, iso):\n" + INSERT + "    return out\n", ns)
    P = "NO cash_movement row for X -- the transfer-out was never saved into the day."
    a = ns["chk"]({"problems": [P], "custody_events": [{"a": 1}]}, "2026-08-27")
    check("with a transfer, the sentence is rewritten",
          "still counts this cash in the drawer" in a["problems"][0])
    check("the rewrite names the date", "2026-08-27" in a["problems"][0])
    check("the rewrite does NOT claim it is not a cash movement",
          "not a day-ledger movement" not in a["problems"][0])
    check("the rewrite is short (under 220 chars)", len(a["problems"][0]) < 220)
    b = ns["chk"]({"problems": [P], "custody_events": []}, "2026-08-27")
    check("with no transfer, the original instruction survives",
          "never saved" in b["problems"][0])
    c = ns["chk"]({"problems": ["some other problem"],
                   "custody_events": [{"a": 1}]}, "2026-08-27")
    check("no other message is touched", c["problems"] == ["some other problem"])

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
    if st not in ("patched", "updated"):
        print("!! REFUSING --", st)
        print("   The live file does not carry the exact anchor expected.")
        print("   Nothing was changed.")
        return 1
    if new == s:
        print("already at this wording -- nothing to do.")
        return 0
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
    print("%s OK" % st)
    print("backup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
