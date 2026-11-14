#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s837.py LIVE_ROOT OUT_ROOT KIT_DIR -- kit S837_STOCK_REGISTER_ONE_ITEM (14-Nov-2026, Sanjeevni session 463).
Rebuilds the six live files from their live bytes (each FROM pin checked first) and lays the new reader beside the door:
  finance/marg_billwatch.py      + seg_bw_s837.py, inserted before 'the command line'
  finance/reports_tile.py        + Shavez's Stock Register rows (only while his switch is ON)
  finance/sanjeevni_approvals.py + one Needs-you line (the Hub)
  finance/finance_ui/finance_approvals.html + the Hub's Go to line and its count
  marg_ingest/marg_take.py, marg_ingest/marg_ingest.py + the register read before the file is deleted
  marg_ingest/marg_register.py   NEW (copied from the kit)
Every patch is an exact anchor that occurs once; anything else stops the build."""
import hashlib, os, shutil, sys

FROM = {
    "finance/marg_billwatch.py": "960b5309e78570ef6fac605e34594f1f",
    "finance/reports_tile.py": "163a869aee0547f891d47023a45873c4",
    "finance/sanjeevni_approvals.py": "ae29e2bc5bf2da9819e1f095e8aee7a5",
    "finance/finance_ui/finance_approvals.html": "82f459efc902085a6b4f9285efe9c1ef",
    "marg_ingest/marg_take.py": "5cad2d24d63344146f562fd5d441dbdf",
    "marg_ingest/marg_ingest.py": "828c4dad6b159207b034d8129aed3ab7",
}


def one(s, a, b, what):
    if s.count(a) != 1:
        raise SystemExit("anchor not found once (%d) in %s: %r" % (s.count(a), what, a[:80]))
    return s.replace(a, b)


RT_BLOCK = '''

# ---- S837_STOCK_REGISTER_ONE_ITEM (14-Nov-2026, Sanjeevni session 463): Marg's Stock Register for one item, asked by the owner ----
#  Shown ONLY while the owner's switch for Shavez is ON (marg_billwatch.reg_for_shavez -> [] while OFF; OFF to start, his word of 20:28).
#  Read only; each row ticks itself when the register has come. Fail-soft: no module, no table, any fault -> no card, the page whole.
def _s837_asked(cx):
    try:
        import marg_billwatch as BW                            # noqa: PLC0415
        return BW.reg_for_shavez(cx)
    except Exception:                                          # noqa: BLE001
        return []


_status_before_s837 = status


def status(cx, today=None, now=None):                          # noqa: F811 -- S837
    s = _status_before_s837(cx, today, now)
    s["asked_reg"] = _s837_asked(cx)
    return s


def _s837_card(asked):
    if not asked:
        return ""
    lines = []
    for a in asked:
        state = ("<span class='state good'>&#10003; aa gayi, sahi hai</span>" if a.get("arrived")
                 else "<span class='state due'>&#9675; abhi baaki</span>")
        lines.append("<div class=line><span class=big>Doctor sahab ne ek item ka Stock Register maanga hai</span><br>"
                     "Item: <b>%s</b><br>From <b>%s</b> &middot; To <b>%s</b><br><span class=small>Marg ki REPORT wali ID se. Stock Register, "
                     "store WHOLE, item ka naam aur yeh do taareekh daaliye, phir Save (F3). File yahan khud aa jaati hai.</span>%s</div>"
                     % (_esc(a.get("item") or ""), _esc(_ddmm(a["day_from"])), _esc(_ddmm(a["day_to"])), state))
    return "<div class='card' id=s837reg style='border:2px solid #f0b400;background:#fffdf3'>%s</div>" % "".join(lines)


_render_before_s837 = render


def render(s, picked_date=False):                              # noqa: F811 -- S837: the card above the day's done / count line, as S815's
    page = _render_before_s837(s, picked_date)
    card = _s837_card(s.get("asked_reg") or [])
    if card:
        for mark in ("<div class='card' id=s815asked", "<div class='card done'>", "<div class='card'><p class='big wait'", "<p class=foot>",
                     "<div class=card id=s714flows>"):
            if page.count(mark) == 1:
                return page.replace(mark, card + mark)
    return page
# ---- S837 end ----------------------------------------------------------------------------------------------------------------------------
'''

SA_BLOCK = '''

# ---- S837_STOCK_REGISTER_ONE_ITEM (14-Nov-2026, Sanjeevni session 463): one Needs-you line while a Stock Register asked by the owner is not in --
#  its href opens his list (/finance/sanjeevni/marg-watch/take). Added to the lines BEFORE S761 groups them (group 'Marg & bank details').
#  NEEDS_YOU_WITHOUT_S837=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it. Fail-soft.
_needs_you_before_s837 = _needs_you_before_s761


def _needs_you_before_s761(con):                         # noqa: F811 -- S837: S761's grouping reads this name at call time
    r = _needs_you_before_s837(con)
    if os.environ.get("NEEDS_YOU_WITHOUT_S837") == "1":
        return r
    try:
        import marg_billwatch as _bw837                      # noqa: PLC0415
        add = _bw837.reg_needs_lines(con)
        if add:
            r["lines"] = list(r.get("lines") or []) + add
            r["count"] = int(r.get("count") or 0) + len(add)
    except Exception:                                    # noqa: BLE001
        pass
    return r
# ---- S837 end ---------------------------------------------------------------------------------------------------------------------------
'''

HTML_LINK_A = '        <a href="/finance/sanjeevni/marg-watch">Marg watch — bills changed after their day</a>\n'
HTML_LINK_B = HTML_LINK_A + '        <a href="/finance/sanjeevni/marg-watch/take">Marg reports for you to take — Stock Register <span id="gotoReg"></span></a>\n'
HTML_JS_A = "    var j=x.j||{}, e=$(\"gotoExp\"); if(e&&j.ok&&j.n) e.innerHTML='<span class=\"gb\" title=\"'+s761Esc(j.title||\"\")+'\">'+parseInt(j.n,10)+'</span>';\n  }).catch(function(){});\n"
HTML_JS_B = HTML_JS_A + ("  fetch(\"/finance/sanjeevni/marg-watch/api/register/count?_=\"+Date.now(),{cache:\"no-store\"}).then(srvJSON).then(function(x){   /* S837 */\n"
                         "    var j=x.j||{}, e=$(\"gotoReg\"); if(e&&j.ok&&j.n) e.innerHTML='<span class=\"gb\" title=\"'+s761Esc(j.title||\"\")+'\">'+parseInt(j.n,10)+'</span>';\n"
                         "  }).catch(function(){});\n")

TK_A = '            if typ == "ORDER_PENDING" and verdict == "VERIFIED":                    # S454 (D666): Darpan\'s order sheet, loaded at once\n'
TK_B = ('            if typ == "STOCK_ITEM_LEDGER" and verdict == "VERIFIED":                # S837: Marg\'s Stock Register for one item, read name-free\n'
        '                nlines = _s837_register(con, md5, local)                            #   before the file is deleted below (S186)\n') + TK_A
TK_FN_A = "def take(raw, name=\"\", source=\"manual\", db=None, archive=None):\n"
TK_FN_B = ('def _s837_register(con, md5, path):\n'
           '    """S837: Marg\'s Stock Register for one item -> mi_register / mi_register_line, name-free (marg_register.py). Never raises -> entries read."""\n'
           '    try:\n'
           '        import marg_register                                  # noqa: PLC0415\n'
           '        n, _note = marg_register.store_path(con, md5, path, MI.now_ist().isoformat(), MI._readers().open_sheet)\n'
           '        return n\n'
           '    except Exception:                                         # noqa: BLE001\n'
           '        return 0\n\n\n') + TK_FN_A
MI_A = "            kept = 0\n            if dest and os.path.exists(dest):\n                if phi:\n"
MI_B = ('            if typ == "STOCK_ITEM_LEDGER" and verdict == "VERIFIED" and not dry:   # S837: Marg\'s Stock Register, read name-free before\n'
        '                try:                                                           #   the file is deleted below (as marg_take.take does)\n'
        '                    import marg_register                                       # noqa: PLC0415\n'
        '                    nlines, _n837 = marg_register.store_path(con, f["md5"], local, now_ist().isoformat(), R.open_sheet)\n'
        '                except Exception:                                              # noqa: BLE001\n'
        '                    nlines = 0\n') + MI_A


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main(live, out, kit):
    for rel, want in FROM.items():
        got = md5(os.path.join(live, rel))
        if got != want:
            raise SystemExit("FROM pin: %s is %s, expected %s -- it changed after this kit was built" % (rel, got[:8], want[:8]))
    rd = lambda rel: open(os.path.join(live, rel), encoding="utf-8").read()
    res = {}
    s = rd("finance/marg_billwatch.py")
    seg = open(os.path.join(kit, "seg_bw_s837.py"), encoding="utf-8").read()
    res["finance/marg_billwatch.py"] = one(s, "# ====================================================================== the command line\n",
                                           seg + "# ====================================================================== the command line\n", "marg_billwatch")
    s = rd("finance/reports_tile.py")
    res["finance/reports_tile.py"] = one(s, '\nif __name__ == "__main__":\n    sys.exit(selftest())', RT_BLOCK + '\nif __name__ == "__main__":\n    sys.exit(selftest())', "reports_tile")
    s = rd("finance/sanjeevni_approvals.py")
    end = "# ---- KIT_S761 end ---------------------------------------------------------------------------------------------------------------------\n"
    if not s.endswith(end):
        raise SystemExit("sanjeevni_approvals.py does not end with S761's end line")
    res["finance/sanjeevni_approvals.py"] = s + SA_BLOCK
    s = rd("finance/finance_ui/finance_approvals.html")
    s = one(s, HTML_LINK_A, HTML_LINK_B, "approvals link")
    res["finance/finance_ui/finance_approvals.html"] = one(s, HTML_JS_A, HTML_JS_B, "approvals js")
    s = rd("marg_ingest/marg_take.py")
    s = one(s, TK_A, TK_B, "marg_take hook")
    res["marg_ingest/marg_take.py"] = one(s, TK_FN_A, TK_FN_B, "marg_take fn")
    s = rd("marg_ingest/marg_ingest.py")
    res["marg_ingest/marg_ingest.py"] = one(s, MI_A, MI_B, "marg_ingest hook")
    for rel, txt in res.items():
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(txt)
    p = os.path.join(out, "marg_ingest/marg_register.py")
    shutil.copyfile(os.path.join(kit, "marg_register.py"), p)
    for rel in list(res) + ["marg_ingest/marg_register.py"]:
        print("%s  %s" % (md5(os.path.join(out, rel)), rel))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
