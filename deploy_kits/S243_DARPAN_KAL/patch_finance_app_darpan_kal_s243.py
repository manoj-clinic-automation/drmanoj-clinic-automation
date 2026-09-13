#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_finance_app_darpan_kal_s243.py -- S243_DARPAN_KAL: mount the module, add the owner's card.

TWO files, patched ON THE BOX (neither live file is in the repository), each
anchor asserted to occur EXACTLY ONCE in the live bytes -- else REFUSED and
nothing is written.  Never writes the live file: writes <file>.new.

  finance_app.py   (live pin f002defb, the S243_AUTOAPPLY state)
     M  after the S241_AMIR_DAY mount block: import darpan_kal and init() it.
        GUARDED: a failure inside the module is printed and the console keeps
        serving (the S209 lesson -- one bad module killed the whole portal).

  finance_ui/finance_approvals.html   (live pin cc349dd0, the S243_AUTOAPPLY hub)
     N  the tab strip gains  <a href="#kalCard">Darpan</a>
     C  a card "Darpan -- needs you" before the Home-medicine card
     F  loadKal() defined before loadHomeMed()
     L  loadKal() called where loadHomeMed() is called

    FA_PATH=/root/finance/finance_app.py HUB_PATH=/root/finance/finance_ui/finance_approvals.html \
        /root/wa/venv/bin/python3 -B patch_finance_app_darpan_kal_s243.py [fa|hub|both]

Prints md5 before and after.  ALREADY PATCHED -> exit 0 for that file.
--selftest <finance_app.py> <finance_approvals.html>
"""
import hashlib
import io
import os
import sys

FA_TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
HUB_TARGET = os.environ.get("HUB_PATH", "/root/finance/finance_ui/finance_approvals.html")
FA_MARK = "S243_DARPAN_KAL begin"
HUB_MARK = "S243 darpan kal"

# ---------------------------------------------------------------- finance_app.py
M_OLD = "# --- S241_AMIR_DAY end ---\n"
M_NEW = M_OLD + (
    "\n"
    "# --- S243_DARPAN_KAL begin -- Darpan's morning page: yesterday's cash, two inputs (13-Sep ruling) ---\n"
    "# Rides on the D354 auto-applied day; creates no day_entry; lands the handover as ONE cash_movement\n"
    "# (the api_handover record). GUARDED: a fault inside the module must never take the console down\n"
    "# (S209) -- it is printed to the journal and every other page keeps serving.\n"
    "try:\n"
    "    import darpan_kal                                          # noqa: E402\n"
    "    darpan_kal.init(app, db, require, unit=UNIT)\n"
    "except Exception as _ex_kal:                                   # noqa: BLE001\n"
    "    print(\"darpan_kal NOT mounted: %s\" % _ex_kal, file=sys.stderr)\n"
    "# --- S243_DARPAN_KAL end ---\n")

# ---------------------------------------------------------------- the hub
N_OLD = '    <a href="#homeMedCard">Home med</a><a href="#reclassCard">Reclassified</a>\n'
N_NEW = '    <a href="#homeMedCard">Home med</a><a href="#reclassCard">Reclassified</a><a href="#kalCard">Darpan</a>\n'

C_OLD = '<!-- S194 ⭐2 -->\n<div class="card" id="homeMedCard">'
C_NEW = ('<!-- ' + HUB_MARK + ' -->\n'
         '<div class="card" id="kalCard"><h2><span class="kick">Darpan — needs you</span>Yesterday\'s cash, his word, the data</h2>\n'
         '  <div id="kal">loading&hellip;</div>\n'
         '  <details class="help"><summary>How this works</summary><div>\n'
         '  Every morning Darpan\'s page (<a href="/finance/darpan/kal">/finance/darpan/kal</a>) shows yesterday\'s sale from Marg,\n'
         '  minus home/procedure medicine, minus online, = expected cash. He types the cash handed over and to whom. A match closes\n'
         '  the day silently. A shortfall takes a reason, which the server checks against the data. Only a contradiction, a repeat\n'
         '  pattern, a flagged return he could not explain, cash owed back to him, or a handover not yet marked received reaches here.\n'
         '  Amber = waiting, not wrong.</div></details></div>\n\n'
         + C_OLD)

F_OLD = '/* S194 ⭐2 home-medicine sales, ⭐3 cash/UPI reclassifications */\nfunction loadHomeMed(){\n'
F_NEW = ('/* ' + HUB_MARK + ' -- the owner\'s queue from darpan_kal.py; one line per item */\n'
         'function loadKal(){\n'
         '  fetch("/finance/darpan/kal/api/owner?_="+Date.now(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){\n'
         '    if(!j||!j.ok){$("kal").innerHTML=\'<span class="mut">\'+esc((j&&(j.message||j.error))||"—")+\'</span>\';return}\n'
         '    var d=j.days||{};\n'
         '    var h=\'<div class="held"><div class="stat"><span class="lbl">Needs you</span><span class="val">\'+j.count+\'</span></div>\'+\n'
         '          \'<div class="stat"><span class="lbl">Waiting “received”</span><span class="val">\'+j.amber+\'</span></div>\'+\n'
         '          \'<div class="stat"><span class="lbl">Owed to Darpan</span><span class="val">\'+fmt("₹"+(j.owed_p/100))+\'</span></div>\'+\n'
         '          \'<div class="stat"><span class="lbl">Days · 30d</span><span class="val">\'+(d.n||0)+\' <span class="mut">(\'+(d.complete||0)+\' clean, \'+(d.explained||0)+\' explained)</span></span></div></div>\';\n'
         '    if(!(j.items||[]).length){h+=\'<div class="ok">✓ Nothing needs you. Every handover matched or was explained by the data.</div>\';}\n'
         '    else{h+=\'<div class="tblwrap" style="margin-top:8px"><table><tbody>\';\n'
         '      j.items.forEach(function(it){h+=\'<tr><td>\'+(it.amber?\'<span class="mut">\':\'\')+esc(it.line)+(it.amber?\'</span>\':\'\')+\'</td><td>\'+\n'
         '        (it.link?\'<a href="\'+esc(it.link)+\'">open</a>\':(it.kind==="owed"?\'<button class="ghost" onclick="kalOwed(\'+it.id+\')">returned</button>\':""))+\'</td></tr>\'});\n'
         '      h+=\'</tbody></table></div>\';}\n'
         '    $("kal").innerHTML=h;\n'
         '  }).catch(function(){$("kal").innerHTML=\'<span class="mut">could not load</span>\'});\n'
         '}\n'
         'function kalOwed(id){fetch("/finance/darpan/kal/api/owed/returned",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:id})}).then(function(){loadKal()})}\n'
         + F_OLD)

L_OLD = 'loadHomeMed(); loadReclass(); loadMPR(); loadReview(); loadStaffCards();\n'
L_NEW = 'loadHomeMed(); loadReclass(); loadMPR(); loadReview(); loadStaffCards(); loadKal();\n'


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_fa(src):
    if FA_MARK in src:
        return src, "already"
    n = src.count(M_OLD)
    if n != 1:
        return src, "refused: anchor M occurs %d times (need exactly 1)" % n
    if src.count("import darpan_kal") != 0:
        return src, "refused: darpan_kal is already imported without the mark"
    return src.replace(M_OLD, M_NEW, 1), "patched"


def patch_hub(src):
    if HUB_MARK in src:
        return src, "already"
    for nm, old in (("N", N_OLD), ("C", C_OLD), ("F", F_OLD), ("L", L_OLD)):
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %s occurs %d times (need exactly 1)" % (nm, n)
    out = (src.replace(N_OLD, N_NEW, 1).replace(C_OLD, C_NEW, 1)
           .replace(F_OLD, F_NEW, 1).replace(L_OLD, L_NEW, 1))
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
        check("  mount lands after the S241 block, once",
              out.count("darpan_kal.init(app, db, require, unit=UNIT)") == 1
              and out.find("S241_AMIR_DAY end") < out.find("S243_DARPAN_KAL begin"))
        check("  only additions: every original line still present",
              all(ln in out for ln in s.splitlines() if ln.strip()))
        check("  second run is a no-op", patch_fa(out)[1] == "already")
    for p in hubs:
        s = io.open(p, encoding="utf-8").read()
        out, st = patch_hub(s)
        check("%s: patches (%s)" % (os.path.basename(p), st), st == "patched")
        if st != "patched":
            continue
        check("  card, tab, loader and call each once",
              out.count('id="kalCard"') == 1 and out.count('href="#kalCard"') == 1
              and out.count("function loadKal()") == 1 and out.count("loadStaffCards(); loadKal();") == 1)
        check("  the home-medicine card and loader survive",
              out.count('id="homeMedCard"') == 1 and out.count("function loadHomeMed()") == 1)
        check("  only additions: every original line still present",
              all(ln in out for ln in s.splitlines() if ln.strip()))
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
