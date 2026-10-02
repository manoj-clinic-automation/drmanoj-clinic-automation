#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s446.py -- kit S446_AMIR_STAGES_BILLS: builds the six live files from the LIVE bytes (CLAUDE.md rule 2).

Each live file is checked against its FROM pin (S444's TO, read live) and every edit is anchored -- its anchor must occur EXACTLY once,
else the build stops and writes nothing. The blocks the kit appends live beside this file.

    make_s446.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {
    "amir_day.py": "2b497142efdb1a3d1b84e9f05cbf59ac",
    "stock_app.py": "c0120fb67c78105fe797982fcb6ab644",
    "sanjeevni_approvals.py": "d2c550401ebfb7716126d24a09fae78f",
    "purchase_app.py": "a51fe90eaa2922ba4e2b4db6388f797a",
    "darpan_kal.py": "803970bd04c7203632b98d9659923b3b",
    "darpan_kal.html": "a4eecb21a88f793ab5c81b75dab20a51",
}
E = {}


def edit(f, old, new):
    E.setdefault(f, []).append((old, new))


# ------------------------------------------------------------------ amir_day.py
edit("amir_day.py",
     '        "s444": _s444_state(cx, day),                     # S444: the vouchers, the renames, the salt list owed -- never a gate\n',
     '        "s444": _s444_state(cx, day),                     # S444: the vouchers, the renames, the salt list owed -- never a gate\n'
     '        "s446": _s446_state(cx, day),                     # S446: the count by stage, the packs by state, the bills for Marg, the doors\n')
edit("amir_day.py",
     "                  + _neft_card_s407() + _packs_card_s408() +\n",
     "                  + _neft_card_s407() +                         # S446 (F-673): the packs ride in the card above, chosen by state\n")
edit("amir_day.py",
     '            "<button class=btn name=go value=2>Sab bill daal diye</button></form></div>")\n'
     '    return _page(2, w, "Bill entry", body,\n',
     '            "<button class=btn name=go value=2>Sab bill daal diye</button></form></div>")\n'
     "    body = _s446_bills_list(w) + body                    # S446 (D650): the scanned bills to put into Marg, first\n"
     '    return _page(2, w, "Bill entry", body,\n')
edit("amir_day.py",
     "def _s444_card(w, top=False):\n"
     '    """(a) Stock voucher, (b) Naam badlo -- each line gone when its work is done; on step 6 the salt work follows as (c)."""\n',
     "def _s444_card(w, top=False):\n"
     '    """(a) Stock voucher, (b) Naam badlo -- each line gone when its work is done; on step 6 the salt work follows as (c)."""\n'
     '    if "s446" in w:\n'
     "        return _s446_card(w, top)                      # S446 (D649): the count by stage, the doors, the packs\n")
edit("amir_day.py", "def _s444_left(w):\n", "def _s444_left(w):\n    if \"s446\" in w:\n        return _s446_left(w)                           # S446\n")
edit("amir_day.py", "def _s444_summary_rows(w):\n", "def _s444_summary_rows(w):\n    if \"s446\" in w:\n        return _s446_summary_rows(w)                   # S446\n")
edit("amir_day.py",
     "        # (d) the count vouchers\n        out.extend(_s444_voucher_line(con))\n",
     "        # (d) the count vouchers -- S446: named by stage; where the count stands; the orthotics verified; the Sarvam trial\n"
     "        out.extend(_s446_owner_lines(con))\n")

# ------------------------------------------------------------------ stock_app.py
edit("stock_app.py",
     '    b["you"] = dict(user=(u or {}).get("user") or "")\n    return jsonify(ok=True, **b)\n',
     '    b["you"] = dict(user=(u or {}).get("user") or "")\n'
     "    b = _s446_board_filter(con, b, u)                     # S446 (D649): a login that is not the checker sees its stage only\n"
     "    return jsonify(ok=True, **b)\n")
edit("stock_app.py",
     '    html = _s444_board_html(html, (u or {}).get("user") or "")   # S444: BACK to "Amir ka kaam", and who is signed in\n',
     '    html = _s444_board_html(html, (u or {}).get("user") or "")   # S444: BACK to "Amir ka kaam", and who is signed in\n'
     '    html = html.replace(\'<div class="card"><h2><span class="n">4</span>\', \'<div class="card" id="rest"><h2><span class="n">4</span>\', 1)   # S446: the card\'s doors open here\n')

# ------------------------------------------------------------------ sanjeevni_approvals.py
edit("sanjeevni_approvals.py",
     "    # 3 · returns waiting for his OK, this month\n"
     "    rp = _returns_pending(con, today[:7])\n"
     "    if rp and rp[0]:\n",
     "    # 3 · returns waiting for his OK -- S446 (F-680): every open month, the oldest named (the old line, this month only, stays\n"
     "    #     exactly as it was only when NEEDS_YOU_WITHOUT_S406=1, an older kit's frozen walk)\n"
     "    rl = _s446_returns_line(con, today)\n"
     "    if rl:\n"
     "        lines.append(rl)\n"
     "    rp = _returns_pending(con, today[:7]) if rl is None else None\n"
     "    if rp and rp[0]:\n")

# ------------------------------------------------------------------ purchase_app.py (D650 · F-680)
edit("purchase_app.py",
     "               _pay_months_nav_s264(con, month, prefix),\n",
     "               _s446_earlier_card(con, month, prefix) + _pay_months_nav_s264(con, month, prefix),   # S446: an earlier month's baaki\n")
edit("purchase_app.py",
     "    return bar + body + up\n",
     "    return bar + _s446_sarvam_card(con) + body + up      # S446 (D650): Sarvam against Marg, one line\n")

# ------------------------------------------------------------------ darpan_kal.py + its page (D648)
edit("darpan_kal.py",
     "                orders_today=_orders_today_safe(con))          # S410 (D626)\n",
     "                orders_today=_orders_today_safe(con),          # S410 (D626)\n"
     "                amir_claims=_s446_claims(con))                 # S446 (D648): Amir's supplier claims -- Darpan's queue\n")
edit("darpan_kal.html",
     ' h+=ordersTodaySec(j.orders_today); /* S410 (D626): Aaj ke order -- N (M bheja) */\n',
     ' h+=ordersTodaySec(j.orders_today); /* S410 (D626): Aaj ke order -- N (M bheja) */\n'
     ' h+=amirClaimsSec(j.amir_claims);   /* S446 (D648): Amir ke claim -- two taps, nothing to type */\n')
edit("darpan_kal.html",
     "function pickParty(p){",
     "/* S446 (D648): Amir ke claim -- his supplier claims, Darpan's queue: supplier, bill, amount, raised when; two taps */\n"
     "function amirClaimsSec(c){\n"
     " if(!c||!c.length) return \"\";\n"
     " return sec('<div class=\"row\"><span class=\"k\">Amir ke claim — <b>'+c.length+'</b></span></div>'+c.map(x=>'<div class=\"flag\" data-claim=\"'+x.id+'\"><div><b>'+esc(x.supplier)+'</b> · bill '+esc(x.bill_no)+' · '+R(x.amount_p||0)+' <span class=\"badge amber\">'+esc(x.reason_hi)+'</span></div>'+\n"
     "  '<div class=\"muted\">'+esc(x.raised_at)+' · '+esc(x.raised_by)+(x.contacted?' · '+esc(x.contacted):'')+'</div><div>'+\n"
     "  (x.state!==\"contacted\"?'<span class=\"btn\" onclick=\"answerClaim('+x.id+',\\'baat_hui\\')\">Supplier se baat ho gayi</span>':'')+\n"
     "  '<span class=\"btn\" onclick=\"answerClaim('+x.id+',\\'mil_gaya\\')\">Credit / maal mil gaya</span></div></div>').join(\"\"));\n"
     "}\n"
     "async function answerClaim(id,ans){try{await post(\"/finance/darpan/kal/api/claim-answer\",{id:id,answer:ans});load();}catch(e){toast(\"\"+e);}}\n"
     "function pickParty(p){")

APPEND = {"amir_day.py": "amir_block_s446.py", "stock_app.py": "stock_block_s446.py", "darpan_kal.py": "darpan_block_s446.py",
          "sanjeevni_approvals.py": "approvals_block_s446.py"}
INSERT_BEFORE = {"purchase_app.py": ('\n\nif __name__ == "__main__":\n    import sys as _sys_s439\n', "purchase_block_s446.py")}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(finance, out, check_pins=True):
    os.makedirs(out, exist_ok=True)
    for f in FROM:
        raw = open(os.path.join(finance, f), "rb").read()
        if check_pins and md5b(raw) != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- someone changed it since the brief; nothing written" % (f, md5b(raw), FROM[f]))
        txt = raw.decode("utf-8")
        for old, new in E.get(f, []):
            n = txt.count(old)
            if n != 1:
                raise SystemExit("STOP: %s -- an anchor occurs %d times (must be exactly once): %r" % (f, n, old[:90]))
            txt = txt.replace(old, new, 1)
        if f in APPEND:
            txt = txt.rstrip("\n") + "\n\n\n" + open(os.path.join(HERE, APPEND[f]), "rb").read().decode("utf-8").strip("\n") + "\n"
        if f in INSERT_BEFORE:
            anchor, blk = INSERT_BEFORE[f]
            if txt.count(anchor) != 1:
                raise SystemExit("STOP: %s -- the insertion anchor occurs %d times" % (f, txt.count(anchor)))
            txt = txt.replace(anchor, "\n\n\n" + open(os.path.join(HERE, blk), "rb").read().decode("utf-8").strip("\n") + "\n" + anchor, 1)
        b = txt.encode("utf-8")
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        print("built %-24s %s -> %s  (%d edits%s)" % (f, FROM[f][:8], md5b(b), len(E.get(f, [])), ", block added" if (f in APPEND or f in INSERT_BEFORE) else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-pins", action="store_true")
    a = ap.parse_args()
    build(a.finance, a.out, check_pins=not a.no_pins)
