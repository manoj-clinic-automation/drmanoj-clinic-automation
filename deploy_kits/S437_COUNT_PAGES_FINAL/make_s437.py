#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s437.py -- builds the patched live files of kit S437_COUNT_PAGES_FINAL from the LIVE bytes by anchored edits. Every anchor must
occur exactly once and every source must be at its FROM pin, or the build stops with nothing written. (stock_amir.html, stockmatch.html,
loss_piles.py v2.4 and qty_words.py v1.2 are whole files shipped in the kit.)

  stock_app.py           the voucher state carries the vouchers as Amir keys them (vouchers_flat: STOCK ISSUE 1..N, then STOCK RECEIVE
                         1..M, continuous across the count) and every line's quantity words (from / to / change, Hindi and English,
                         through qty_words with the item's name); _voucher_numbers() for the statement; Naam badlo gated on the proof
                         (state 'done'); the whole-unit list loaded into qty_words at the top of the S227 report composer; _qw() names
                         the item of the lane it is wording (the CCM bug).
  stock_statement.py     v1.3: a line's voucher reads "Marg corrected -- on STOCK RECEIVE voucher N" / "on STOCK ISSUE voucher N".
  stock_hub.html         "Not yet on a voucher 0" reads "Every line is on a voucher".
  stock_loss.html        "The staff block -- frozen" as tables (Big losses open, Small losses collapsed, Orthotics apart, total rows);
                         "As Darpan sees it" -> one link; the whole-unit list on the settings card (the candidates, one tap each).

Usage: make_s437.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "ec9abc4801599d9acd1ab34f66a21a83",
    "stock_statement.py": "24a040b1b58a21f043ff92ffce1e2860",
    "stock_hub.html": "7b2ea5065c1b1bf110a4301ccd0384a1",
    "stock_loss.html": "5ead2a32949ec6e77e95b8645db350e2",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def sub(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for '%s' occurs %d times, not once" % (what, n))
    return text.replace(old, new)


# ----------------------------------------------------------------------------- stock_app.py
def patch_stock_app(s):
    s = sub(s, 'def _qw(units, ps):\n    """QUANTITY IN THE SHOP\'S OWN WORDS -- the owner, 06-Sep-2026: \'400 units is a',
            '_QW_ITEM = None                                            # S437: the item _lane_of is wording (a whole-unit item reads in its own word)\n\n\n'
            'def _qw(units, ps, name=None):\n    """QUANTITY IN THE SHOP\'S OWN WORDS -- the owner, 06-Sep-2026: \'400 units is a', "_qw def")
    s = sub(s, "        return _qty.words(n, pack=ps)                          # S427: the one nomenclature -- '3 strips + 4 tabs', '12 pcs'",
            "        return _qty.words(n, pack=ps, name=(name or _QW_ITEM))   # S427: the one nomenclature -- '3 strips + 4 tabs', '12 pcs'; S437: a whole-unit item in its word", "_qw body")
    s = sub(s, '    marg, counted, diff, mrp_p, cost_p; ctx carries the item\'s context."""\n'
               '    pack = max(1, int(d["pack"] or 1)); diff = int(d["diff"]); marg = int(d["marg"]); cnt = int(d["counted"])',
            '    marg, counted, diff, mrp_p, cost_p; ctx carries the item\'s context."""\n'
            '    global _QW_ITEM\n'
            '    _QW_ITEM = d.get("item")                                  # S437: every quantity word of this lane names its item (the whole-unit list)\n'
            '    pack = max(1, int(d["pack"] or 1)); diff = int(d["diff"]); marg = int(d["marg"]); cnt = int(d["counted"])', "_lane_of item")
    s = sub(s, "    salts = _salts_less_fixes(con)                            # S436 (3.3): an item whose salt is on the open salt-fix list pairs with nothing",
            "    _whole_units_load(con)                                    # S437: the whole-unit items into qty_words before any quantity is worded\n"
            "    salts = _salts_less_fixes(con)                            # S436 (3.3): an item whose salt is on the open salt-fix list pairs with nothing", "report composer load")
    s = sub(s, '        b["lines"].append(dict(line_no=r[4], section=r[5] or "", family=r[6] or "", item=r[7], packing=r[8] or "", pack=r[9] or 1,\n'
               '                               marg_from=r[10], change=r[11], marg_to=r[12], counted=r[13], rate_p=r[14], value_p=r[15], reason=r[16]))',
            '        b["lines"].append(dict(line_no=r[4], section=r[5] or "", family=r[6] or "", item=r[7], packing=r[8] or "", pack=r[9] or 1,\n'
            '                               marg_from=r[10], change=r[11], marg_to=r[12], counted=r[13], rate_p=r[14], value_p=r[15], reason=r[16],\n'
            '                               **_s437_line_words(r[7], r[8] or "", r[9] or 1, r[10], r[11], r[12])))   # S437: the words of the line', "voucher line words")
    s = sub(s, '    n_issue = sum(1 for p in pend if p["kind"] == "ISSUE")\n    n_recv = len(pend) - n_issue\n    return dict(pending=pend, pending_issue=n_issue, pending_receive=n_recv,',
            '    n_issue = sum(1 for p in pend if p["kind"] == "ISSUE")\n    n_recv = len(pend) - n_issue\n'
            '    flat = _s437_flat(out)                                    # S437: the vouchers as Amir keys them -- STOCK ISSUE 1..N, then STOCK RECEIVE 1..M\n'
            '    return dict(vouchers_flat=flat, pending=pend, pending_issue=n_issue, pending_receive=n_recv,', "voucher state flat")
    s = sub(s, '    # (c) Naam badlo -- only when the orthotic round exists and every earlier round is entered\n'
               '    try:\n'
               '        vm = _voucher_state(con, d)\n'
               '        ortho_rounds = [r for r in vm["rounds"] if r["batches"] and all((b.get("sections") or []) == ["Orthotics"] for b in r["batches"])]\n'
               '        earlier = [r for r in vm["rounds"] if r not in ortho_rounds]\n'
               '        out["renames_ready"] = bool(ortho_rounds) and all(r["closed"] for r in earlier)\n'
               '        out["renames_wait_hi"] = "" if out["renames_ready"] else ("नाम बदलना — बाद में, जब वाउचर हो जाएँ" + ("" if ortho_rounds else " (orthotic round अभी बना नहीं)"))\n',
            '    # (c) Naam badlo -- S437: ONLY after the proof is green (Marg = shelf reached for this count, hub step 5 DONE); the owner: "if he sees\n'
            '    #     them before, he might do the corrections earlier and spoil our flow". The rounds\' order stays for the record.\n'
            '    try:\n'
            '        vm = _voucher_state(con, d)\n'
            '        ortho_rounds = [r for r in vm["rounds"] if r["batches"] and all((b.get("sections") or []) == ["Orthotics"] for b in r["batches"])]\n'
            '        earlier = [r for r in vm["rounds"] if r not in ortho_rounds]\n'
            '        out["renames_ready"] = (_proof_state(con, d).get("state") == "done")\n'
            '        out["renames_wait_hi"] = "" if out["renames_ready"] else "नाम बदलना — बाद में, जब Marg और shelf मिल जाएँ"\n', "renames gate")
    s = sub(s, "# ---- S436_STAFF_PAGES_CLEAN end -------------------------------------------------\n",
            "# ---- S436_STAFF_PAGES_CLEAN end -------------------------------------------------\n"
            "# ---- S437_COUNT_PAGES_FINAL begin (F-659, 28-Sep-2026): the vouchers as Amir keys them, the words of a line, the whole-unit items ----\n"
            "VOUCHER_HI = {\"ISSUE\": \"STOCK ISSUE\", \"RECEIVE\": \"STOCK RECEIVE\"}\n"
            "\n"
            "\n"
            "def _whole_units_load(con):\n"
            "    \"\"\"S437: the desk's whole-unit list (stock.whole_unit_items, 'ITEM = word') into qty_words -- every quantity word after this names\n"
            "    the item, and a whole-unit item (CCM) reads in its word, never strips / tabs. Fail-soft: no list, no older qty_words -> as before.\"\"\"\n"
            "    if not QTY_WORDS_OK or not hasattr(_qty, \"set_whole_units\"):\n"
            "        return {}\n"
            "    try:\n"
            "        r = con.execute(\"SELECT value FROM setting WHERE key='stock.whole_unit_items'\").fetchone()\n"
            "        raw = json.loads(r[0]) if r and str(r[0] or \"\").strip() else []\n"
            "        return _qty.set_whole_units(raw if isinstance(raw, list) else [])\n"
            "    except Exception:                                          # noqa: BLE001\n"
            "        return {}\n"
            "\n"
            "\n"
            "def _s437_line_words(item, packing, pack, m_from, change, m_to):\n"
            "    \"\"\"The words of one voucher line, Hindi and English, through qty_words with the item's name (the whole-unit list applies).\"\"\"\n"
            "    def w(v, lang):\n"
            "        if QTY_WORDS_OK:\n"
            "            return _qty.words(v, packing=packing, pack=pack, name=item, lang=lang)\n"
            "        return _qw(v, pack)\n"
            "    return dict(from_hi=w(m_from, \"hi\"), to_hi=w(m_to, \"hi\"), qty_hi=w(abs(int(change or 0)), \"hi\"),\n"
            "                from_text=w(m_from, \"en\"), to_text=w(m_to, \"en\"), qty_text=w(abs(int(change or 0)), \"en\"))\n"
            "\n"
            "\n"
            "def _s437_flat(rounds):\n"
            "    \"\"\"The vouchers of the count in the order Amir keys them: every STOCK ISSUE voucher (round by round, batch by batch) numbered 1..N,\n"
            "    then every STOCK RECEIVE voucher 1..M. The internal round numbers ride along for the entered door, never for his eyes.\"\"\"\n"
            "    out = []\n"
            "    for kind in (\"ISSUE\", \"RECEIVE\"):\n"
            "        seq = 0\n"
            "        for rd in sorted(rounds, key=lambda r: r[\"round_no\"]):\n"
            "            for b in sorted([b for b in rd[\"batches\"] if b[\"kind\"] == kind], key=lambda b: b[\"batch_no\"]):\n"
            "                seq += 1\n"
            "                out.append(dict(kind=kind, seq=seq, title=\"%s voucher %d\" % (VOUCHER_HI[kind], seq), title_hi=\"%s — वाउचर %d\" % (VOUCHER_HI[kind], seq),\n"
            "                                round_no=rd[\"round_no\"], batch_no=b[\"batch_no\"], n=b[\"n\"], value_p=b.get(\"value_p\"), sections=b.get(\"sections\") or [],\n"
            "                                entered=b.get(\"entered\"), lines=b[\"lines\"]))\n"
            "    return out\n"
            "\n"
            "\n"
            "def _voucher_numbers(con, root):\n"
            "    \"\"\"item -> ['STOCK ISSUE voucher 3', 'STOCK RECEIVE voucher 1', ...] -- the same numbering as Amir's board (the statement reads it).\"\"\"\n"
            "    _voucher_ensure(con)\n"
            "    seq, out, nxt = {}, {}, {\"ISSUE\": 0, \"RECEIVE\": 0}\n"
            "    rows = con.execute(\"SELECT round_no, kind, batch_no, item FROM stock_voucher_line WHERE count_id=? ORDER BY kind='RECEIVE', round_no, batch_no, line_no\", (int(root),)).fetchall()\n"
            "    for rno, kind, bno, item in rows:\n"
            "        k = (rno, kind, bno)\n"
            "        if k not in seq:\n"
            "            nxt[kind] = nxt.get(kind, 0) + 1\n"
            "            seq[k] = nxt[kind]\n"
            "        lab = \"%s voucher %d\" % (VOUCHER_HI.get(kind, kind), seq[k])\n"
            "        if lab not in out.setdefault(item, []):\n"
            "            out[item].append(lab)\n"
            "    return out\n"
            "# ---- S437_COUNT_PAGES_FINAL end -------------------------------------------------\n", "S437 block")
    return s


# ----------------------------------------------------------------------------- stock_statement.py
def patch_statement(s):
    s = sub(s, 'VERSION = "1.2"\nKIT = "S436_STAFF_PAGES_CLEAN"                                 # v1.0 was S431_COUNT_STATEMENT, v1.1 S432_DESK_GROUP_FLOW\n',
            'VERSION = "1.3"\nKIT = "S437_COUNT_PAGES_FINAL"                                  # v1.0 was S431_COUNT_STATEMENT, v1.1 S432_DESK_GROUP_FLOW, v1.2 S436_STAFF_PAGES_CLEAN\n'
            '# v1.3 (S437, F-659, 28-Sep-2026): a line\'s voucher reads as Amir keys it -- "Marg corrected -- on STOCK RECEIVE voucher N" (the shelf held\n'
            '# more than Marg; Marg brought up to the shelf, never a loss) / "on STOCK ISSUE voucher N" -- from the count\'s continuous voucher numbers\n'
            '# (stock_app._voucher_numbers), no internal round number.\n', "statement header")
    s = sub(s, '    for r in con.execute("SELECT item, round_no FROM stock_voucher_line WHERE count_id=? ORDER BY round_no", (root,)):\n'
               '        rounds_by_item.setdefault(r[0], []).append(int(r[1]))\n',
            '    for r in con.execute("SELECT item, round_no FROM stock_voucher_line WHERE count_id=? ORDER BY round_no", (root,)):\n'
            '        rounds_by_item.setdefault(r[0], []).append(int(r[1]))\n'
            '    vno_by_item = {}                                          # S437: the vouchers as Amir keys them (STOCK ISSUE 1..N, STOCK RECEIVE 1..M)\n'
            '    try:\n'
            '        vno_by_item = _sa()._voucher_numbers(con, root)\n'
            '    except Exception:                                         # noqa: BLE001\n'
            '        vno_by_item = {}\n'
            '\n'
            '    def _voucher_words(item):\n'
            '        labels = vno_by_item.get(item) or []\n'
            '        if labels:\n'
            '            recv_only = all(l.startswith("STOCK RECEIVE") for l in labels)\n'
            '            return ("Marg corrected -- on " if recv_only else "on ") + ", ".join(labels)\n'
            '        return "on voucher round %s" % ", ".join(str(r) for r in sorted(set(rounds_by_item.get(item) or [])))\n', "statement numbers")
    s = sub(s, '            if item in rounds_by_item:\n'
               '                L["voucher"] = "on voucher round %s" % ", ".join(str(r) for r in sorted(set(rounds_by_item[item])))\n'
               '            elif item in pending:\n',
            '            if item in rounds_by_item:\n'
            '                L["voucher"] = _voucher_words(item)           # S437\n'
            '            elif item in pending:\n', "ortho voucher words")
    s = sub(s, '            if item in rounds_by_item:\n'
               '                L["voucher"] = "on voucher round %s" % ", ".join(str(r) for r in sorted(set(rounds_by_item[item])))\n'
               '        if marg < 0:',
            '            if item in rounds_by_item:\n'
            '                L["voucher"] = _voucher_words(item)           # S437\n'
            '        if marg < 0:', "medicine voucher words")
    return s


# ----------------------------------------------------------------------------- stock_hub.html
def patch_hub(s):
    s = sub(s, "    +'<div class=\"figs\"><span>Not yet on a voucher <b>'+(V.pending||0)+'</b></span><span>Marg vouchers entered <b>'+(V.batches_entered||0)+' of '+(V.batches_total||0)+'</b></span></div>',   // S301",
            "    +'<div class=\"figs\"><span>'+(V.pending?'Not yet on a voucher <b>'+V.pending+'</b>':'Every line is on a voucher <b>\\u2713</b>')+'</span><span>Marg vouchers entered <b>'+(V.batches_entered||0)+' of '+(V.batches_total||0)+'</b></span></div>',   // S301; S437: 0 says so",
            "hub pending")
    s = sub(s, "    +'<span>Not yet on a voucher <b>'+V.pending+'</b></span><span>Orthotic vouchers entered <b>'+(V.batches.length-V.not_entered)+' of '+V.batches.length+'</b></span>'",
            "    +'<span>'+(V.pending?'Not yet on a voucher <b>'+V.pending+'</b>':'Every orthotic line is on a voucher <b>\\u2713</b>')+'</span><span>Orthotic vouchers entered <b>'+(V.batches.length-V.not_entered)+' of '+V.batches.length+'</b></span>'",
            "hub ortho pending")
    return s


# ----------------------------------------------------------------------------- stock_loss.html
def patch_loss(s):
    s = sub(s, ".block .note{font-size:13.5px;margin-top:6px;padding-top:6px;border-top:1px dashed var(--line)}\n",
            ".block .note{font-size:13.5px;margin-top:6px;padding-top:6px;border-top:1px dashed var(--line)}\n"
            "/* S437: the block as tables */\n"
            ".block details.bt{margin-top:6px}.block details.bt>summary{cursor:pointer;font-weight:700;list-style:none}.block details.bt>summary::-webkit-details-marker{display:none}.block details.bt>summary small{font-weight:400;color:var(--muted)}\n"
            ".block table.bt{width:100%;border-collapse:collapse;font-size:13px;margin:4px 0;font-variant-numeric:tabular-nums}.block table.bt th,.block table.bt td{padding:4px 5px;text-align:right;border-bottom:1px solid var(--line);vertical-align:top}.block table.bt th{font-weight:600;color:var(--muted);font-size:12px}.block table.bt th:first-child,.block table.bt td:first-child{text-align:left}.block table.bt td:first-child{font-weight:600;overflow-wrap:anywhere}.block table.bt tfoot td{font-weight:700;border-top:2px solid var(--ink-2);border-bottom:0}\n"
            ".chips .wu{display:inline-flex;gap:6px;align-items:center;margin:2px 4px 2px 0}.chips .wu select{font:inherit;font-size:13px;padding:3px 6px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)}\n",
            "loss css")
    s = sub(s, "function blockHtml(Bk, title, frozen){\n"
               "  if(!Bk) return '';\n"
               "  let h='<div class=\"block\"><div class=\"sub\">'+esc(title)+'</div><div class=\"b1\">'+esc(Bk.lines_en[0])+'</div><div class=\"b2\">'+esc(Bk.lines_en[1])+'</div><div class=\"b3\">'+esc(Bk.lines_en[2])+'</div>'\n"
               "    +'<div class=\"hi\">As Darpan sees it: '+Bk.lines_hi.map(esc).join(' · ')+'</div>';\n",
            "function blockHtml(Bk, title, frozen){\n"
            "  if(!Bk) return '';\n"
            "  const T=Bk.tables;\n"
            "  let h='<div class=\"block\"><div class=\"sub\">'+esc(title)+'</div>';\n"
            "  if(T){                                                       // S437: the block as tables -- kul, Big losses open, Small losses collapsed, Orthotics apart, total rows\n"
            "    const tb=(X,open,cls)=>{ const H=(T.headers||{}).en||[\"Item\",\"Marg\",\"Counted\",\"Short\",\"Rs\"];\n"
            "      return '<details class=\"bt\"'+(open?' open':'')+'><summary class=\"'+cls+'\">'+esc(X.en)+(open?'':' <small>(show)</small>')+'</summary><table class=\"bt\"><thead><tr>'+H.map(x=>'<th>'+esc(x)+'</th>').join(\"\")+'</tr></thead><tbody>'\n"
            "        +(X.rows||[]).map(r=>'<tr><td>'+esc(r.item)+'</td><td>'+esc(r.marg_text)+'</td><td>'+esc(r.counted_text)+'</td><td>'+esc(r.short_text)+'</td><td>'+esc(r.rs)+'</td></tr>').join(\"\")\n"
            "        +'</tbody><tfoot><tr><td>Total</td><td></td><td></td><td>'+lines((X.rows||[]).length)+'</td><td>'+esc(X.rs)+'</td></tr></tfoot></table></details>'; };\n"
            "    h+='<div class=\"b1\">'+esc(T.kul.en)+'</div>'+tb(T.badi,true,\"b3\")+tb(T.chhoti,false,\"b2\")+((T.ortho&&T.ortho.n)?tb(T.ortho,false,\"b2\"):'');\n"
            "    h+='<div class=\"hi\"><a href=\"/finance/stockmatch\">Darpan\\'s page shows this in Hindi</a></div>';\n"
            "  } else {\n"
            "    h+='<div class=\"b1\">'+esc(Bk.lines_en[0])+'</div><div class=\"b2\">'+esc(Bk.lines_en[1])+'</div><div class=\"b3\">'+esc(Bk.lines_en[2])+'</div>'\n"
            "      +'<div class=\"hi\">As Darpan sees it: '+Bk.lines_hi.map(esc).join(' · ')+'</div>';\n"
            "  }\n", "loss block tables")
    s = sub(s, "    if(s.kind===\"list\"){\n"
               "      c='<div class=\"chips\">'+(s.items.length?s.items.map(it=>'<button class=\"chip\" data-consume-remove=\"'+esc(it)+'\" title=\"Take off the list\">'+esc(it)+' ×</button>').join(\"\"):'<span class=\"none\">Nothing on the list.</span>')+'</div>'\n",
            "    if(s.kind===\"list\"&&s.key===\"stock.whole_unit_items\"){   // S437: the whole-piece items -- ITEM = word; the candidates with one tap each\n"
            "      const words=s.words||[\"bottle\",\"jar\",\"pc\",\"tube\",\"vial\",\"sachet\"];\n"
            "      const sel=(id,dflt)=>'<select id=\"'+id+'\" aria-label=\"the word\">'+words.map(w=>'<option value=\"'+w+'\"'+(w===dflt?' selected':'')+'>'+w+'</option>').join(\"\")+'</select>';\n"
            "      c='<div class=\"chips\">'+(s.items.length?s.items.map(it=>'<button class=\"chip\" data-whole-remove=\"'+esc(it)+'\" title=\"Take off the list\">'+esc(it)+' ×</button>').join(\"\"):'<span class=\"none\">Nothing on the list.</span>')+'</div>';\n"
            "      const CD=s.candidates||[];\n"
            "      if(CD.length) c+='<div class=\"h\">Looks like a whole-piece item ('+CD.length+') — one tap adds it with the word beside it:</div><div class=\"chips\">'+CD.map((x,i)=>'<span class=\"wu\"><button class=\"chip add\" data-whole-add=\"'+esc(x.item)+'\" data-whole-sel=\"whole_w'+i+'\" title=\"'+esc(x.why)+'\">+ '+esc(x.item)+' <small>'+esc(x.packing)+'</small></button>'+sel(\"whole_w\"+i,x.word)+'</span>').join(\"\")+'</div>';\n"
            "      c+='<div class=\"row\"><input id=\"whole_q\" placeholder=\"Or type an item name\" aria-label=\"Type an item to add to the whole-piece list\" autocomplete=\"off\">'+sel(\"whole_w\",\"bottle\")+'<button class=\"s\" data-whole-add-typed=\"1\">Add</button></div>';\n"
            "      h+='<div class=\"set\"><div><b>'+esc(s.label)+'</b> — <span class=\"sub\">now: '+esc(s.shown)+'</span></div><div class=\"h\">'+esc(s.hint)+'</div>'+c+'</div>';\n"
            "      return;\n"
            "    }\n"
            "    if(s.kind===\"list\"){\n"
            "      c='<div class=\"chips\">'+(s.items.length?s.items.map(it=>'<button class=\"chip\" data-consume-remove=\"'+esc(it)+'\" title=\"Take off the list\">'+esc(it)+' ×</button>').join(\"\"):'<span class=\"none\">Nothing on the list.</span>')+'</div>'\n",
            "loss settings whole list")
    s = sub(s, "  const ca=t.closest(\"[data-consume-add]\");\n",
            "  const wa=t.closest(\"[data-whole-add]\");                   // S437: the whole-piece list\n"
            "  if(wa){ const se=document.getElementById(wa.getAttribute(\"data-whole-sel\")); BUSY=true; const j=await post(BASE+\"/api/loss/\"+D.count_id+\"/pile/setting\",{key:\"stock.whole_unit_items\",add:wa.getAttribute(\"data-whole-add\"),word:(se&&se.value)||\"bottle\"}); BUSY=false;\n"
            "    MSG={settings:{ok:!!(j&&j.ok),html:esc((j&&j.message)||\"The server did not answer.\")}}; load(true); return; }\n"
            "  if(t.closest(\"[data-whole-add-typed]\")){ const qi=document.getElementById(\"whole_q\"), se=document.getElementById(\"whole_w\"); const nm=((qi&&qi.value)||\"\").trim();\n"
            "    if(!nm){ MSG={settings:{ok:false,html:\"Type the item's name.\"}}; load(true); return; }\n"
            "    BUSY=true; const j=await post(BASE+\"/api/loss/\"+D.count_id+\"/pile/setting\",{key:\"stock.whole_unit_items\",add:nm,word:(se&&se.value)||\"bottle\"}); BUSY=false;\n"
            "    MSG={settings:{ok:!!(j&&j.ok),html:esc((j&&j.message)||\"The server did not answer.\")}}; load(true); return; }\n"
            "  const wr=t.closest(\"[data-whole-remove]\");\n"
            "  if(wr){ BUSY=true; const j=await post(BASE+\"/api/loss/\"+D.count_id+\"/pile/setting\",{key:\"stock.whole_unit_items\",remove:wr.getAttribute(\"data-whole-remove\")}); BUSY=false;\n"
            "    MSG={settings:{ok:!!(j&&j.ok),html:esc((j&&j.message)||\"The server did not answer.\")}}; load(true); return; }\n"
            "  const ca=t.closest(\"[data-consume-add]\");\n", "loss whole handlers")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, fn in (("stock_app.py", patch_stock_app), ("stock_statement.py", patch_statement), ("stock_hub.html", patch_hub), ("stock_loss.html", patch_loss)):
        src = load(os.path.join(a.finance, name), name)
        out = fn(src)
        raw = out.encode("utf-8")
        open(os.path.join(a.out, name), "wb").write(raw)
        print("%s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
