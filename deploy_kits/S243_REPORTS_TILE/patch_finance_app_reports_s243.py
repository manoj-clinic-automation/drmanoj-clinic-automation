#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_finance_app_reports_s243.py -- S243_REPORTS_TILE: mount the module, add the owner's line.

TWO files, patched ON THE BOX (neither live file is in the repository), each anchor asserted to
occur EXACTLY ONCE in the live bytes -- else REFUSED and nothing is written.  Never writes the
live file: writes <file>.new.

  finance_app.py   (live pin f002defb, the S243_AUTOAPPLY state -- OR the same file after
                    S243_SCREEN_FIXES and/or S243_DARPAN_KAL: the anchor is the __main__ block
                    at the very end, which none of those kits touch; proven on all four states)
     M  immediately before `if __name__ == "__main__":` -- import reports_tile and init() it.
        GUARDED: a failure inside the module is printed and the console keeps serving (S209).

  finance_ui/finance_approvals.html   (live pin cc349dd0 -- OR after S243_DARPAN_KAL 7dbb5e56:
                    the three anchors sit inside the Marg card and load(), which that kit leaves
                    alone; proven on both states)
     N  one line under "Pushed reports" on the Marg card:  Today's reports: 2 of 3 arrived
     F  loadReports() defined before loadPushes()
     L  loadReports() called where loadPushes() is called (inside load())

    FA_PATH=/root/finance/finance_app.py HUB_PATH=/root/finance/finance_ui/finance_approvals.html \
        /root/wa/venv/bin/python3 -B patch_finance_app_reports_s243.py [fa|hub|both]

Prints md5 before and after.  ALREADY PATCHED -> exit 0 for that file.
--selftest <finance_app.py> <finance_approvals.html>
"""
import hashlib
import io
import os
import sys

FA_TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
HUB_TARGET = os.environ.get("HUB_PATH", "/root/finance/finance_ui/finance_approvals.html")
FA_MARK = "S243_REPORTS_TILE begin"
HUB_MARK = "S243 reports tile"

# ---------------------------------------------------------------- finance_app.py
M_OLD = ('\n\nif __name__ == "__main__":\n'
         '    if "--selftest" in sys.argv:\n'
         '        sys.exit(selftest())\n')
M_NEW = (
    "\n\n"
    "# --- S243_REPORTS_TILE begin -- \"Aaj ki reports\": the Marg report generator's morning page (13-Sep ruling) ---\n"
    "# Reads mi_file / marg_push_staging / stock_feed / purchase_export / purchase_salt_task / amir_day and\n"
    "# the punch file; writes nothing, creates no table. GUARDED: a fault inside the module must never\n"
    "# take the console down (S209) -- it is printed to the journal and every other page keeps serving.\n"
    "try:\n"
    "    import reports_tile                                        # noqa: E402\n"
    "    reports_tile.init(app, db, require, unit=UNIT)\n"
    "except Exception as _ex_rpt:                                   # noqa: BLE001\n"
    "    print(\"reports_tile NOT mounted: %s\" % _ex_rpt, file=sys.stderr)\n"
    "# --- S243_REPORTS_TILE end ---\n"
    + M_OLD)

# ---------------------------------------------------------------- the hub
N_OLD = '  <div id="mpList" class="mut" style="margin-top:6px">loading&hellip;</div></div>\n'
N_NEW = (N_OLD +
         '  <!-- ' + HUB_MARK + ' -->\n'
         '  <div id="rptToday" class="mut" style="margin-top:8px">Today\'s reports: loading&hellip;</div>\n')

F_OLD = '/* ---------- Marg: pushed reports ---------- */\nfunction loadPushes(){\n'
F_NEW = ('/* ' + HUB_MARK + ' -- the report generator\'s morning list, as one line; reports_tile.py decides */\n'
         'function loadReports(){\n'
         '  fetch("/finance/reports/aaj/api/status?_="+Date.now(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){\n'
         '    if(!j||!j.ok){$("rptToday").innerHTML=\'<span class="mut">Today\\\'s reports: \'+esc((j&&(j.message||j.error))||"could not load")+\'</span>\';return}\n'
         '    var bad=(j.rows||[]).filter(function(r){return r.state==="refused"}).map(function(r){return r.label});\n'
         '    var due=(j.rows||[]).filter(function(r){return r.state==="due"}).map(function(r){return r.label});\n'
         '    $("rptToday").innerHTML=\'<b>\'+esc(j.line)+\'</b>\'+(j.amir_day?\' <span class="mut">(Amir day)</span>\':"")+\n'
         '      (bad.length?\' <span class="bad">refused: \'+esc(bad.join(", "))+\'</span>\':"")+\n'
         '      (due.length?\' <span class="mut">due: \'+esc(due.join(", "))+\'</span>\':"")+\n'
         '      \' <a href="/finance/reports/aaj" class="mut">open</a>\';\n'
         '  }).catch(function(){$("rptToday").innerHTML=\'<span class="mut">Today\\\'s reports: could not load</span>\'});\n'
         '}\n'
         + F_OLD)

L_OLD = '  loadHealth(); loadPushes(); loadCash(30); loadCashPos(); initMonth(); loadOrtho();\n'
L_NEW = '  loadHealth(); loadPushes(); loadReports(); loadCash(30); loadCashPos(); initMonth(); loadOrtho();\n'


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_fa(src):
    if FA_MARK in src:
        return src, "already"
    n = src.count(M_OLD)
    if n != 1:
        return src, "refused: anchor M occurs %d times (need exactly 1)" % n
    if src.count("import reports_tile") != 0:
        return src, "refused: reports_tile is already imported without the mark"
    return src.replace(M_OLD, M_NEW, 1), "patched"


def patch_hub(src):
    if HUB_MARK in src:
        return src, "already"
    for nm, old in (("N", N_OLD), ("F", F_OLD), ("L", L_OLD)):
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %s occurs %d times (need exactly 1)" % (nm, n)
    out = src.replace(N_OLD, N_NEW, 1).replace(F_OLD, F_NEW, 1).replace(L_OLD, L_NEW, 1)
    return out, "patched"


def selftest(paths):
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  PASS ", name)
        else:
            bad += 1
            print("  FAIL ", name)

    fa = [p for p in paths if p.endswith(".py")]
    hubs = [p for p in paths if p.endswith(".html")]
    for p in fa:
        s = io.open(p, encoding="utf-8").read()
        out, st = patch_fa(s)
        check("%s: patches (%s)" % (os.path.basename(p), st), st == "patched")
        if st != "patched":
            continue
        try:
            compile(out, p, "exec")
            check("  compiles", True)
        except SyntaxError as ex:
            check("  compiles (%s)" % ex, False)
        check("  mount lands after every other mount and before __main__, once",
              out.count("reports_tile.init(app, db, require, unit=UNIT)") == 1
              and out.find("S241_AMIR_DAY end") < out.find("S243_REPORTS_TILE begin") < out.find('if __name__ == "__main__":')
              and ("S243_DARPAN_KAL end" not in out or out.find("S243_DARPAN_KAL end") < out.find("S243_REPORTS_TILE begin")))
        check("  only additions: every original line still present",
              all(ln in out for ln in s.splitlines() if ln.strip()))
        check("  second run is a no-op", patch_fa(out)[1] == "already")
    for p in hubs:
        s = io.open(p, encoding="utf-8").read()
        out, st = patch_hub(s)
        check("%s: patches (%s)" % (os.path.basename(p), st), st == "patched")
        if st != "patched":
            continue
        check("  line, loader and call each once",
              out.count('id="rptToday"') == 1 and out.count("function loadReports()") == 1
              and out.count("loadPushes(); loadReports();") == 1)
        check("  the pushed-reports list and loader survive",
              out.count('id="mpList"') == 1 and out.count("function loadPushes()") == 1)
        check("  the S243_DARPAN_KAL anchors are untouched (either install order works)",
              out.count('    <a href="#homeMedCard">Home med</a><a href="#reclassCard">Reclassified</a>') == 1
              and out.count("loadHomeMed(); loadReclass(); loadMPR(); loadReview(); loadStaffCards();") == 1)
        check("  only additions, plus one call: every original line still present (the call line grew)",
              all(ln in out for ln in s.splitlines() if ln.strip() and ln + "\n" != L_OLD)
              and L_OLD.strip()[:-len(" loadCash(30); loadCashPos(); initMonth(); loadOrtho();")] in out)
        check("  second run is a no-op", patch_hub(out)[1] == "already")
    check("a stranger .py is refused", patch_fa("x = 1\n")[1].startswith("refused"))
    check("a stranger page is refused", patch_hub("<html></html>\n")[1].startswith("refused"))
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def run_one(target, fn, label):
    raw = io.open(target, "rb").read()
    src = raw.decode("utf-8")
    print("source %s md5 %s" % (target, md5(raw)))
    new, st = fn(src)
    if st == "already":
        print("ALREADY PATCHED (%s) -- nothing to do" % label)
        return 0
    if st != "patched":
        print("REFUSED (%s): %s -- nothing written" % (label, st[len("refused: "):]))
        return 2
    if label == "fa":
        compile(new, target, "exec")
    io.open(target + ".new", "w", encoding="utf-8", newline="\n").write(new)
    print("wrote %s.new md5 %s" % (target, md5(new.encode("utf-8"))))
    return 0


def main(argv):
    if argv and argv[0] == "--selftest":
        return selftest(argv[1:])
    which = (argv[0] if argv else "both")
    rc = 0
    if which in ("fa", "both"):
        rc = max(rc, run_one(FA_TARGET, patch_fa, "fa"))
    if which in ("hub", "both"):
        rc = max(rc, run_one(HUB_TARGET, patch_hub, "hub"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
