#!/usr/bin/env python3
"""
patch_finance_app_ruledwords.py -- S210: STORED warnings brought under the
rulings, on read.

WHY THE OLD SENTENCES SURVIVED THE PARSER FIX
    Each push's warnings are written into marg_push_staging.survey_json AT
    PUSH TIME. The list replays the stored text. patch_marg_report_words
    fixed the parser -- future pushes only. The 28/29-Aug rows (and every
    older row) still carry the retired sentences. This patch rewrites them
    AS THE LIST IS SERVED, numbers preserved, so one rule covers every row
    ever stored and every row to come.

THE RULINGS APPLIED (each has a record)
    S208 (owner): a credit note IS a SALES RETURN, verified against the same
        patient's earlier bill, approved by the owner.
    D348 (S201, signed): a no-ID bill counts in sales IN FULL; named ones
        park for the cross-match, nameless book as WALK-IN. "variance",
        "low confidence", "scored low" retired.

SAFETY: exact anchor (the S210 margtidy block -- run that patch first);
refuse if absent/ambiguous; backup; py_compile with auto-restore.

USAGE
    /root/wa/venv/bin/python3 patch_finance_app_ruledwords.py /root/finance/finance_app.py
    python3 patch_finance_app_ruledwords.py --selftest <margtidy-patched copies...>
"""
import datetime, os, py_compile, shutil, sys

MARK = "S210 (ruled words on read)"

A1 = """        sv["not_filed"] = [_d.get("date") for _d in (sv.get("survey") or [])
                           if not _d.get("filed")]"""

N1 = A1 + """
        # %s -- stored survey warnings predate the rulings; rewrite them as
        # served, numbers preserved (S208: CN = SALES RETURN; D348: no-ID
        # routing; 'scored low' retired). The parser writes the ruled words
        # for new pushes; this line covers every row already stored.
        _W = []
        for _w in (sv.get("warnings") or []):
            _m = re.match(r"(\\d+) credit note\\(s\\) totalling (-?[0-9.,]+) \\u2014 kept.*", _w)
            if _m:
                _w = ("%%s SALES RETURN(s) \\u2014 credit notes totalling %%s \\u2014 kept and "
                      "carried through signed; each is approved by you against the "
                      "same patient (S208)" %% (_m.group(1), _m.group(2)))
            _m = re.match(r"(\\d+) of (\\d+) bills carry no clinic ID and will attribute to WALK-IN", _w)
            if _m:
                _w = ("%%s of %%s bills carry no clinic ID \\u2014 they count in sales in full; "
                      "named ones park for the cross-match, nameless book as WALK-IN "
                      "(D348)" %% (_m.group(1), _m.group(2)))
            _w = _w.replace("\\u2014 scored low so they go to review rather than to a "
                            "possibly wrong patient",
                            "\\u2014 these park for review, never attached to a guessed patient")
            _W.append(_w)
        sv["warnings"] = _W""" % MARK


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    n = s.count(A1)
    if n != 1:
        return s, ("anchor_missing (run patch_finance_app_margtidy first)" if n == 0
                   else "anchor_ambiguous")
    return s.replace(A1, N1), "patched"


def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1; print("  FAIL:", name)
    import re as _re
    # the rewrite logic itself, against the owner's EXACT pasted sentences
    ns = {"re": _re}
    # exec the block exactly as it will run: dedent N1's rewrite lines by 8
    _lines = [l[8:] for l in N1.split("\n")
              if l.startswith("        ") and not l.lstrip().startswith("#")]
    _lines = _lines[_lines.index('_W = []'):]
    try:
        _sv = {"warnings": [
            "4 credit note(s) totalling -1442.00 \u2014 kept, and carried through signed (needs finance_ingest at S180 U1 or later)",
            "10 of 27 bills carry no clinic ID and will attribute to WALK-IN",
            "3 bill(s) carry a clinic ID that is not 4 digits (75, 842) \u2014 scored low so they go to review rather than to a possibly wrong patient",
            "some other warning left alone"]}
        ns["sv"] = _sv
        exec(compile("\n".join(_lines), "<rw>", "exec"), ns)
        out = ns["sv"]["warnings"]
        check("CN sentence -> SALES RETURN, numbers kept",
              out[0].startswith("4 SALES RETURN(s)") and "-1442.00" in out[0] and "S208" in out[0])
        check("developer-speak gone", "S180 U1" not in out[0])
        check("WALK-IN -> D348 routing, numbers kept",
              out[1].startswith("10 of 27") and "D348" in out[1] and "will attribute" not in out[1])
        check("'scored low' -> parked-for-review", "scored low" not in out[2] and "guessed patient" in out[2])
        check("unknown warnings untouched", out[3] == "some other warning left alone")
    except Exception as e:
        check("rewrite logic executes (%s)" % e, False)
    for path in sys.argv[2:]:
        s0 = open(path, encoding="utf-8").read()
        # dry-run on a margtidy-patched copy
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import patch_finance_app_margtidy as mt
        s1, st0 = mt.patch_text(s0)
        check("%s: margtidy precursor applies" % path.split("/")[-2], st0 == "patched")
        out2, st = patch_text(s1)
        check("  ruledwords patches on top", st == "patched")
        check("  compiles", compile(out2, path, "exec") is not None)
        _, st2 = patch_text(out2)
        check("  second run no-op", st2 == "already_patched")
        _, st3 = patch_text(s0)
        check("  UNpatched copy refused (margtidy first)", st3.startswith("anchor_missing"))
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
    bak = "%s.bak_S210_rw_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
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
