#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s761.py -- S761_HUB_NEEDS_GOTO: the anchored changes of four live files (three this project's; owner_console.py the parent's, one
expression, PLANNED on the board v1129) and the appended section of one.
    python3 -B make_s761.py <finance dir> <out dir> [<dir holding the sec_*761.txt files>]
Each FROM file must carry its pinned md5 (S760's TO for the two it shares with S760; the 09-Nov bundle for shelf_figure.py; S757's TO for owner_console.py); every anchor
must stand EXACTLY the number of times named; the TO md5s are printed. finance_app.py is not touched."""
import hashlib
import os
import sys

FROM = {"finance/finance_ui/finance_approvals.html": "11eab919f4111f0a72b973475b7ef43a",   # S760's TO (installed 09-Nov 09:14 IST)
        "finance/sanjeevni_approvals.py": "1408fb421a0d4b9cccfb92a15820dce9",             # S760's TO (installed 09-Nov 09:14 IST)
        "finance/shelf_figure.py": "23b2394a7a10a99ff0c30121087813f1",                   # the 09-Nov bundle
        "finance/owner_console.py": "7dd1a85872c31d90e9fe65a8bdf70f92"}                  # S757's TO (installed 09-Nov 07:46 IST; the parent's file, PLANNED v1129)
APPEND = {"finance/sanjeevni_approvals.py": "sec_sa761.txt"}

CASH_OLD = '    $("cashPos").innerHTML=\n      \'<div id="cashPosNote" style="width:100%">\'+\n      (window.HEALTH&&window.HEALTH.drawer_inflated?\'<div class="alert warn">⚠ Today\\\'s bank UPI statement has not arrived — the drawer figure may read inflated.</div>\':\'\')+\n      \'</div>\'+\n      \'<div class="stat" style="margin-bottom:2px"><span class="lbl">Cash in the unit\'+(j.as_of?\' · as of \'+esc(j.as_of):\'\')+\'</span><span class="val">\'+fmt(j.unbanked)+\'</span></div>\'+\n      \'<div class="stat" style="margin-bottom:4px"><span class="lbl">Last bank deposit</span><span><span class="badge \'+gapCls+\'">\'+gapTxt+\'</span></span></div>\'+\n      row("In Darpan’s drawer"+((j.waiting_days&&j.waiting_days.length)?\' <span class="mut" style="font-weight:400">· \'+j.waiting_days.length+\' day(s) awaiting your approval</span>\':\'\'), j.drawer, drawerDetail)+\n      (j.basis==="sanjeevni_cash"\n        ? row("With you & Dr Bhawna (pool)", j.reserve, trailTable(j.reserve_detail))\n        : row("Parked · Dr Bhawna", j.reserve, trailTable(j.reserve_detail))+\n          row("Parked · Dr Manoj", j.with_manoj, trailTable(j.manoj_detail)))+\n      row("Banked to date ("+esc(j.bank_count)+")", j.bank_deposited, depDetail)+\n      \'<div class="mut" style="font-size:12px;margin-top:6px">Tap any line to expand · one arithmetic for the whole page (S210).</div>\';'
CASH_NEW = '    var BX=[["Cash in the unit", j.unbanked, ""], ["In Darpan’s drawer", j.drawer, drawerDetail]];\n    if(j.basis==="sanjeevni_cash") BX.push(["With you &amp; Dr Bhawna (pool)", j.reserve, trailTable(j.reserve_detail)]);\n    else { BX.push(["Parked · Dr Bhawna", j.reserve, trailTable(j.reserve_detail)]); BX.push(["Parked · Dr Manoj", j.with_manoj, trailTable(j.manoj_detail)]); }\n    BX.push(["Banked to date ("+esc(j.bank_count)+")", j.bank_deposited, depDetail]);\n    try{ $("cashPos").innerHTML=s761CashHTML(j,BX,gapTxt,gapCls); return; }catch(e761){ /* S761: the S210 drawing below stands */ }\n    $("cashPos").innerHTML=\n      \'<div id="cashPosNote" style="width:100%">\'+\n      (window.HEALTH&&window.HEALTH.drawer_inflated?\'<div class="alert warn">⚠ Today\\\'s bank UPI statement has not arrived — the drawer figure may read inflated.</div>\':\'\')+\n      \'</div>\'+\n      \'<div class="stat" style="margin-bottom:2px"><span class="lbl">Cash in the unit\'+(j.as_of?\' · as of \'+esc(j.as_of):\'\')+\'</span><span class="val">\'+fmt(j.unbanked)+\'</span></div>\'+\n      \'<div class="stat" style="margin-bottom:4px"><span class="lbl">Last bank deposit</span><span><span class="badge \'+gapCls+\'">\'+gapTxt+\'</span></span></div>\'+\n      row("In Darpan’s drawer", j.drawer, drawerDetail)+\n      (j.basis==="sanjeevni_cash"\n        ? row("With you & Dr Bhawna (pool)", j.reserve, trailTable(j.reserve_detail))\n        : row("Parked · Dr Bhawna", j.reserve, trailTable(j.reserve_detail))+\n          row("Parked · Dr Manoj", j.with_manoj, trailTable(j.manoj_detail)))+\n      row("Banked to date ("+esc(j.bank_count)+")", j.bank_deposited, depDetail)+\n      \'<div class="mut" style="font-size:12px;margin-top:6px">Tap any line to expand · one arithmetic for the whole page (S210).</div>\';'
NEEDS_OLD = '    el.innerHTML=L.map(function(l){\n      var act=l.neft_event?\' <button onclick="event.stopPropagation();neftEvent(\'+parseInt(l.neft_event,10)+\',\\\'ok\\\')">OK</button> <button class="ghost" onclick="event.stopPropagation();neftEvent(\'+parseInt(l.neft_event,10)+\',\\\'reject\\\')">Not this</button>\':\'\';   /* S405 */\n      if(l.review_supplier) act+=\' <button onclick="event.stopPropagation();poSet(\\\'\'+esc(l.review_supplier).replace(/\'/g,"\\\\\'")+\'\\\',\\\'move_to\\\',\\\'\'+esc(l.review_target||"weekly")+\'\\\')">Move Kedar to \'+esc(l.review_target||"weekly")+\'</button>\';   /* S410 */\n      var go=l.href?\'location.href=\\\'\'+esc(l.href)+\'\\\'\':\'goSec(\\\'\'+esc(l.target)+\'\\\')\';   /* S638 (D780): a line with href opens its own page */\n      return \'<li onclick="\'+go+\'"><span class="dot \'+esc(l.cls||"warn")+\'"></span>\'+esc(l.text)+act+\' <span class="mut">▸</span></li>\'}).join("");'
NEEDS_NEW = '    if(j.groups&&j.groups.length){ try{ s761Needs(j); $("needsNote").textContent=(j.n_items?"":"Nothing needs a decision; the blue fold is for your information."); return; }catch(e761){ var nh0=$("needsHead"); if(nh0) nh0.textContent=""; } }   /* S761: grouped; the flat list below if the drawing fails */\n    el.innerHTML=L.map(function(l){\n      var act=l.neft_event?\' <button onclick="event.stopPropagation();neftEvent(\'+parseInt(l.neft_event,10)+\',\\\'ok\\\')">OK</button> <button class="ghost" onclick="event.stopPropagation();neftEvent(\'+parseInt(l.neft_event,10)+\',\\\'reject\\\')">Not this</button>\':\'\';   /* S405 */\n      if(l.review_supplier) act+=\' <button onclick="event.stopPropagation();poSet(\\\'\'+esc(l.review_supplier).replace(/\'/g,"\\\\\'")+\'\\\',\\\'move_to\\\',\\\'\'+esc(l.review_target||"weekly")+\'\\\')">Move Kedar to \'+esc(l.review_target||"weekly")+\'</button>\';   /* S410 */\n      var go=l.href?\'location.href=\\\'\'+esc(l.href)+\'\\\'\':\'goSec(\\\'\'+esc(l.target)+\'\\\')\';   /* S638 (D780): a line with href opens its own page */\n      return \'<li onclick="\'+go+\'"><span class="dot \'+esc(l.cls||"warn")+\'"></span>\'+esc(l.text)+act+\' <span class="mut">▸</span></li>\'}).join("");'
LINKS_OLD = '<details class="fold" id="linksCard"><summary>Other pages</summary><div>\n  <a class="ext" href="/finance/sanjeevni/expiry">Expiry watch ↗</a> ·\n  <a class="ext" href="/finance/purchase/page/staff">Order medicines (the old page) ↗</a> ·\n  <a class="ext" href="/finance/purchase/page/hub">Marg purchases hub ↗</a> ·\n  <a class="ext" href="/finance/stockmatch">Stock milaan ↗</a> ·\n  <a class="ext" href="/finance/workbench">Yes Bank statement · load and reconcile ↗</a> ·\n  <a class="ext" href="/finance/darpan/kal/month">The cash month table ↗</a> ·\n  <a class="ext" href="/finance/review">Review &amp; month close ↗</a> ·\n  <a class="ext" href="/finance/darpan/corrections">Corrections ↗</a> ·\n  <a class="ext" href="/finance/accountant/upi-cash">Accountant ↗</a> ·\n  <a class="ext" href="/finance/pipeline">Pipeline ↗</a> ·\n  <a class="ext" href="/finance/staff">Staff ↗</a> ·\n  <a class="ext" href="/finance/approvals/old">The approvals page as it was ↗</a>\n</div></details>'

OC_EDITS = [
    # F-1199 (one count): the console's Sanjeevni chip and tile count what the hub's header counts (sanjeevni_approvals' n_items -- the lines
    # that need him); an answer without it (an older sanjeevni_approvals, a grouping that failed) keeps the red + amber count as before
    ('    n = sum(1 for x in rows if x.get("cls") in ("bad", "warn"))\n',
     '    n = ny["n_items"] if isinstance(ny.get("n_items"), int) else sum(1 for x in rows if x.get("cls") in ("bad", "warn"))   # S761 (F-1199)\n', 1)]

SF_EDITS = [
    # F-1199 (one figure, one name, one count): 'moved apart on 13 items' named only 8 -- the line now says how many more
    ('", ".join(x["item"] for x in fl[:8])))',
     '", ".join(x["item"] for x in fl[:8]) + ((" and %d more" % (len(fl) - 8)) if len(fl) > 8 else "")))       # S761 (F-1199)', 1)]

HTML_HEADER = ('<!doctype html>\n<!-- KIT_S760',
               '<!doctype html>\n<!-- KIT_S761 S761_HUB_NEEDS_GOTO (Sanjeevni session 414, 09-Nov-2026, D873 / F-1199): the rest of the approved hub --\n'
               '     Needs you grouped (one line per kind of work, red first, the information folded; the groups made by sanjeevni_approvals so\n'
               '     the count is one source), the "Go to" panel on the top bar (every pharmacy page; the old "Other pages" strip folded into it),\n'
               '     Cash and Bank side by side as figures (the confirmed folded away), Days with only the open month open, an Orders tab,\n'
               '     F-1199: the Cash card names no day count of its own, "banked" names one figure only.\n'
               '  -- kit S760 header below -->\n<!-- KIT_S760', 1)

HTML_EDITS = [
    HTML_HEADER,
    ('    <a href="#returnsCard">Returns</a><a href="#monthsCard">Month</a><a href="#checksCard" onclick="openChecks();return true">Checks</a>\n'
     '    <a class="ext" href="/finance/approvals/old">The old page ↗</a>\n  </nav>',
     '    <a href="#returnsCard">Returns</a><a href="#porders">Orders</a><a href="#monthsCard">Month</a><a href="#checksCard" onclick="openChecks();return true">Checks</a>\n'
     '    <a class="ext" href="/finance/approvals/old">The old page ↗</a>\n  </nav>\n@@GOTO@@', 1),
    ('<div class="card" id="needsCard"><h2><span class="kick">In words</span>Needs you</h2>',
     '<div class="card" id="needsCard"><h2><span class="kick">In words · grouped · one line per kind of work</span>Needs you<span class="nh" id="needsHead"></span></h2>', 1),
    ('<div class="card" id="cashPosCard">', '<div class="cb-row">\n<div class="card" id="cashPosCard">', 1),
    ('leaves this picture altogether.</div></div>', 'leaves this picture altogether.</div></div>\n</div>', 1),
    (LINKS_OLD, '', 1),
    (NEEDS_OLD, NEEDS_NEW, 1),
    # S761 (review 3): the header is reset on EVERY path of loadNeeds -- a read error, nothing to show, the flat list -- and set only by the groups
    ('    var j=x.j||{}; var el=$("needs"); if(!el)return;\n',
     '    var j=x.j||{}; var el=$("needs"); if(!el)return;\n    var nh761=$("needsHead"); if(nh761) nh761.textContent="";   /* S761 */\n', 1),
    ('  }).catch(function(){var el=$("needs");if(el)el.innerHTML=\'<li class="mut">could not reach the server</li>\'});\n',
     '  }).catch(function(){var el=$("needs");if(el)el.innerHTML=\'<li class="mut">could not reach the server</li>\'; var nh761=$("needsHead"); if(nh761) nh761.textContent="";});   /* S761 */\n', 1),
    (CASH_OLD, CASH_NEW, 1),
    ("' · banked ₹'+esc(DAYS.position.bank)+'", "'", 1),        # F-1199: 'banked' names one figure (the Cash card's); Bank says 'pool deposits'
    ("(ix===0||pend?' open':'')", "(pend||(ix===0&&ym===s761Ym())?' open':'')", 1),
    ("' · <span class=\"ok\">all approved</span>'", "' · <span class=\"ok\">all approved ✓</span>'", 1),
    ("h+='<details class=\"mon\" open><summary>Yes Bank <span", "h+='<details class=\"mon\"'+(s761Bad(j.deposits)?' open':'')+'><summary>Yes Bank <span", 1),
    (" · banked from the pool ₹'+esc(j.banked_total)", " · pool deposits recorded here ₹'+esc(j.banked_total)", 1),
    ("h+='<details class=\"mon\"'+(mv.length?' open':'')+'><summary>Transfers", "h+='<details class=\"mon\"'+(s761Bad(mv)?' open':'')+'><summary>Transfers", 1),
    ("The next statement settles them.</div>';", "The next statement settles them.</div>';\n    try{ h+=s761BankLine(j); }catch(e761){}   /* S761 */", 1),
]
JS_AT = "/* ---- Needs you: the server's sentences (sanjeevni_approvals, D349) ---- */"
CSS_AT = ".rh-btn{min-height:44px}"


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(text, edits, name):
    for old, new, n in edits:
        c = text.count(old)
        if c != n:
            sys.exit("!! %s: anchor stands %d time(s), expected %d:\n%s" % (name, c, n, old[:200]))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fin, out = sys.argv[1], sys.argv[2]
    here = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    sec = lambda f: open(os.path.join(here, f), "rb").read().decode("utf-8")   # noqa: E731
    for rel, want in FROM.items():
        src = os.path.join(fin, rel[len("finance/"):])
        b = open(src, "rb").read()
        if md5(b) != want:
            sys.exit("!! %s is %s, expected %s -- not the live bytes this kit was built on; STOP" % (src, md5(b)[:8], want[:8]))
        if b"\r\n" in b:
            sys.exit("!! %s carries CRLF; STOP" % src)
        t = b.decode("utf-8")
        if "KIT_S761" in t or "S761 (F-1199)" in t:
            sys.exit("!! %s already carries S761; STOP" % src)
        if rel.endswith("shelf_figure.py"):
            t = apply(t, SF_EDITS, rel)
        elif rel.endswith("owner_console.py"):
            t = apply(t, OC_EDITS, rel)
        elif rel.endswith(".html"):
            t = apply(t, HTML_EDITS, rel)
            t = apply(t, [("@@GOTO@@", sec("sec_goto761.txt").rstrip("\n"), 1),
                          (JS_AT, sec("sec_js761.txt").rstrip("\n") + "\n" + JS_AT, 1),
                          (CSS_AT, CSS_AT + "\n" + sec("sec_css761.txt").rstrip("\n"), 1)], rel)
            if 'id="linksCard"' in t:
                sys.exit("!! the old strip is still there; STOP")
        if rel in APPEND:
            t = t.rstrip("\n") + "\n" + sec(APPEND[rel])
        nb = t.encode("utf-8")
        os.makedirs(os.path.join(out, os.path.dirname(rel)), exist_ok=True)
        open(os.path.join(out, rel), "wb").write(nb)
        print("%s  %s -> %s" % (rel, want[:8], md5(nb)))


if __name__ == "__main__":
    main()
