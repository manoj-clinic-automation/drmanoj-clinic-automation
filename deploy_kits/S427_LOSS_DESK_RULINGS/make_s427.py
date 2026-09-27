#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s427.py -- builds the patched live files of kit S427_LOSS_DESK_RULINGS from the LIVE bytes by anchored edits.
Every anchor must occur exactly once (or exactly the declared count), and every source must be at its FROM pin, or
the build stops with nothing written. Nothing is re-typed. (loss_piles.py and stock_loss.html are whole-file
replacements shipped in the kit; qty_words.py is new.)

  stock_app.py      qty_words imported defensively; _qw() routes through it; the desk route runs the sales-after-count
                    test before it reads; /pile/recount answers 410; /pile/setting takes add/remove for the list;
                    NEW /pile/close (arm + confirm) and /items?q= (the owner's search box); five texts lose the word
                    'unit(s)' (the Marg cleanup Excel headers, the loose-column basis, the try-to-match Excel)
  stock_hub.html    the status card reads the four new piles; step 3's words; the swap texts lose 'unit(s)'
  stockmatch.py     the state carries the pinned staff block and Darpan's own recounts; /api/recount takes ANY item of
                    the round; NEW /api/items?q= (his search box) and /api/note ('Kuchh batana hai?')
  stockmatch.html   the staff block card (pinned, Hindi), 'Dobara ginna hai' (search + patte/goli), 'Aapne gina'
  stock_amir.html   the JS quantity helper renamed (words unchanged: strips / tabs / pcs) -- no 'units' identifier on the page

Usage: make_s427.py --finance /root/finance --out DIR      (writes the five files flat into DIR, prints each md5)
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "cf464882e49865f38153e1df6218301d",
    "stock_hub.html": "bb8741fa7671399f9c495c75946d7c11",
    "stockmatch.py": "d5f9392fea4247b37705e865e1c242cb",
    "stockmatch.html": "9a090e03c954bfda5a787e8d834f275c",
    "stock_amir.html": "c2ea41b2db7e2b337e0a97426aaed763",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what, count=1):
    n = s.count(old)
    if n != count:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly %d): %r" % (what, n, count, old[:90]))
    return s.replace(old, new)


# ---------------------------------------------------------------- stock_app.py
IMPORT_BLOCK = '''# --- S418_LOSS_DESK_PILES end ----------------------------------------------

# --- S427_LOSS_DESK_RULINGS begin (D632 / F-642) ---------------------------
# ONE nomenclature for every quantity a person reads: qty_words.py beside this file (strips + tabs, pcs / bottles /
# tubes / vials, Hindi patte / goli / nag). _qw() routes through it; without it the old words stand.
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import qty_words as _qty                               # noqa: PLC0415
    QTY_WORDS_OK = True
except Exception:                                          # pragma: no cover
    _qty = None
    QTY_WORDS_OK = False
# --- S427_LOSS_DESK_RULINGS end --------------------------------------------
'''

ROUTES = r'''
# ---- S427_LOSS_DESK_RULINGS begin (D632 / F-642) --------------------------------
# The owner's rulings of 27-Sep: piles by turnover, no recount pile, one tap closes the count and freezes the staff
# block (loss_piles v2.0). The S418 doors above stay; /pile/recount answers 410 (recount is Darpan's own option).
@bp.route("/api/loss/<int:cid>/pile/close", methods=["POST"])
def api_loss_pile_close(cid):
    """Close the count. First tap: {} -> arms for loss_piles.ARM_SECONDS and returns a token. Second tap: {token} ->
    every line in Write off, Big losses and Consumption is written off (closed), ONE frozen run with the four groups,
    Amir's voucher round for exactly those lines, and THE STAFF BLOCK frozen for Darpan's Stock milaan."""
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = _desk_root(con, cid)
    if root is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    who = (u or {}).get("user") or ""
    if not b.get("token"):
        ok, msg, code, armed = _lp.arm_close(con, root, who)
        return jsonify(ok=ok, message=msg, arm=armed), code
    ok, msg, code, done = _lp.close(con, root, b.get("token"), who)
    return jsonify(ok=ok, message=msg, done=done), code


@bp.route("/api/loss/<int:cid>/items")
def api_loss_items(cid):
    """The owner's search box on the consumption list: item names of the spine (and of this round) carrying the words typed."""
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    q = str(request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify(ok=True, items=[])
    root = _desk_root(con, cid) or cid
    names = []
    for it in _lp.items_search(con, root, q, 12):
        if it["item"] not in names:
            names.append(it["item"])
    for n_ in _lp.Spine().search(q, 12):
        if n_ not in names:
            names.append(n_)
    return jsonify(ok=True, items=names[:12])
# ---- S427_LOSS_DESK_RULINGS end ---------------------------------------------------
'''


def build_stock_app(s):
    s = rep(s, "# --- S418_LOSS_DESK_PILES end ----------------------------------------------\n", IMPORT_BLOCK, "import qty_words")
    s = rep(s, '''    n = abs(int(round(units or 0))); ps = max(1, int(ps or 1))
    if ps <= 1:
        return "%d pc%s" % (n, "" if n == 1 else "s")
''', '''    n = abs(int(round(units or 0))); ps = max(1, int(ps or 1))
    if QTY_WORDS_OK:
        return _qty.words(n, pack=ps)                          # S427: the one nomenclature -- '3 strips + 4 tabs', '12 pcs'
    if ps <= 1:
        return "%d pc%s" % (n, "" if n == 1 else "s")
''', "_qw routes through qty_words")
    s = rep(s, '''def api_loss_piles(cid):
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    d = _pad_report_data(con, cid)
''', '''def api_loss_piles(cid):
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    _lp.sales_test(con, _desk_root(con, cid) or cid)           # S427 (3.4): sold after the count -> the stock existed; closed by the system before piling
    d = _pad_report_data(con, cid)
''', "the sales-after-count test before the desk reads")
    s = rep(s, '''    ok, msg, code, n = _lp.recount_ask(con, root, (u or {}).get("user") or "")
    return jsonify(ok=ok, message=msg, asked=n), code
''', '''    return jsonify(ok=False, error="gone",                      # S427: there is no Recount pile; recount is Darpan's own option
                   message="Recount is Darpan's own option now -- 'Dobara ginna hai' on his Stock milaan."), 410
''', "/pile/recount answers 410")
    s = rep(s, '''    ok, msg = _lp.set_setting(con, str(b.get("key") or "").strip(), b.get("value"), (u or {}).get("user") or "", root)
''', '''    ok, msg = _lp.set_setting_req(con, str(b.get("key") or "").strip(), b, (u or {}).get("user") or "", root)   # S427: {value} or {add} / {remove} for the list
''', "/pile/setting takes add / remove")
    s = rep(s, '''# ---- S418_LOSS_DESK_PILES end ---------------------------------------------------
''', '''# ---- S418_LOSS_DESK_PILES end ---------------------------------------------------
''' + ROUTES.lstrip("\n"), "the S427 routes")
    # five texts a person reads lose the word 'unit(s)' (F-642)
    s = rep(s, '''            return int(round(loose + free * ps)), "loose column = the units; free strips added"
        return int(round(loose)), "loose column = the units"
''', '''            return int(round(loose + free * ps)), "loose column = the whole quantity; free strips added"
        return int(round(loose)), "loose column = the whole quantity"
''', "the loose-column basis")
    s = rep(s, '''["ITEM", "PACKING", "VOUCHER", "MARG FIGURE (units)", "NEW FIGURE (units)", "CHANGE",''',
            '''["ITEM", "PACKING", "VOUCHER", "MARG FIGURE (tabs or pcs)", "NEW FIGURE (tabs or pcs)", "CHANGE",''', "the Marg cleanup Excel headers")
    s = rep(s, '''why="the loose column (%d) is the whole quantity in units (%d strips x %d); read as %d units, not %d"''',
            '''why="the loose column (%d) is the whole quantity in tabs (%d strips x %d); read as %d tabs, not %d"''', "the loose-column why")
    s = rep(s, '''         "Difference per unit", "How close", "Confirmed? (yes / no)"],
''', '''         "Difference per piece", "How close", "Confirmed? (yes / no)"],
''', "the try-to-match Excel header")
    return s


# ---------------------------------------------------------------- stock_hub.html
def build_hub(s):
    s = rep(s, "  const units=rs.reduce((a,r)=>a+(r.qty||0),0);\n", "  const pieces=rs.reduce((a,r)=>a+(r.qty||0),0);\n", "matchTable total")
    s = rep(s, '''(kind==="med"?"pack":"unit")''', '''(kind==="med"?"pack":"piece")''', "difference per piece", count=2)
    s = rep(s, '''<td colspan="3">Units a swap would explain</td><td class="num">'+units+'</td>''',
            '''<td colspan="3">Pieces a swap would explain</td><td class="num">'+pieces+'</td>''', "pieces a swap would explain")
    s = rep(s, "A Yes takes the units off both lines (the rest stays short)", "A Yes takes the quantity off both lines (the rest stays short)", "step 2 text")
    s = rep(s, """+' ('+V.swap_units+' unit'+(V.swap_units===1?'':'s')+'). A swap takes the loss off""",
            """+' ('+V.swap_units+' tabs or pcs in all). A swap takes the loss off""", "step 4 swap count")
    s = rep(s, """' still open: with you '+K.with_me.n+' · write-off pile '+K.writeoff.n+' · to pursue '+K.pursue.n+' · recount '+K.recount.n+'. ')
      +'Accept back what you have, write off the normal loss as a group, pursue the real gaps, recount what cannot be right.'),""",
            """' still open: with you '+K.with_me.n+' · write off '+K.writeoff.n+' · big losses '+K.bigloss.n+' · consumption '+K.consume.n+'. ')
      +'Accept back what you have; one tap closes the count -- the rest is written off by name, and Darpan sees the staff block on his Stock milaan.'),""", "step 3 text")
    s = rep(s, """["consume","clinic consumption"],["owner","your choice"],["earlier","before the piles"]]""",
            """["consume","clinic consumption"],["big","big loss"],["owner","your choice"],["earlier","before the piles"]]""", "written-off groups on the card")
    s = rep(s, """+c("To pursue",T.pursue)+c("Recount",T.recount)+c("With you + write-off pile",""",
            """+c("Big losses",T.bigloss)+c("Consumption",T.consume)+c("With you + write off",""", "the card's second row")
    return s


# ---------------------------------------------------------------- stockmatch.py
SM_ROUTES = r'''


# ------------------------------------------------------------------ S427 (D632): Dobara ginna hai, the staff block's note
@bp.route("/finance/stockmatch/api/items")
def api_items():
    """Darpan's search box: the items of this round whose name carries every word typed (12 at most)."""
    u, con, kind, err = _auth()
    if err:
        return err
    root = root_of(con, _cid())
    q = str(request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify(ok=True, items=[])
    return jsonify(ok=True, items=_lp().items_search(con, root, q, 12))


@bp.route("/finance/stockmatch/api/note", methods=["POST"])
def api_note():
    """'Kuchh batana hai?' -- one free line under the pinned staff block, stored, shown on the owner's record card."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = root_of(con, _cid())
    ok, msg, code = _lp().add_note(con, root, b.get("text"), (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    d = report(con, root)
    st = _state_for(con, d, u, kind)
    st.update(saved=dict(kind="note", message=msg), round_made=None)
    return jsonify(**st)
'''


def build_stockmatch_py(s):
    s = rep(s, '''    out = dict(recounts=[], claims=[], claim_answers=[])
    try:
        out["recounts"] = _lp().recount_list(con, root)
''', '''    out = dict(recounts=[], claims=[], claim_answers=[], block=None)
    try:
        out["recounts"] = _lp().recounts_by(con, root)        # S427: his own recounts (Dobara ginna hai), newest first
        out["block"] = _lp().block_view(con, root)            # S427: THE STAFF BLOCK, pinned until the next count closes
''', "_s418_extra carries the block")
    s = rep(s, '''    rl = {r["item"]: r for r in _lp().recount_list(con, root)}
    if item not in rl:
        return jsonify(ok=False, error="not_found", message="Yeh item phir se ginne ki list mein nahi hai."), 404
    try:
        if b.get("units") not in (None, ""):
            q = int(float(b.get("units")))
        else:
            q = int(float(b.get("strips") or 0)) * int(rl[item]["pack"] or 1) + int(float(b.get("loose") or 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request", message="Ginti likhiye."), 400
    ok, msg, code = _lp().recount_answer(con, root, item, q, (u or {}).get("user") or "")
''', '''    info = _lp().round_item(con, root, item)                   # S427: ANY item of the round -- Dobara ginna hai
    if not info:
        return jsonify(ok=False, error="not_found", message="Yeh item is ginti mein nahi hai."), 404
    try:
        whole = b.get("pcs") if b.get("pcs") not in (None, "") else b.get("units")
        if whole not in (None, ""):
            q = int(float(whole))
        else:
            q = int(float(b.get("strips") or 0)) * int(info["pack"] or 1) + int(float(b.get("loose") or 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request", message="Ginti likhiye."), 400
    ok, msg, code = _lp().recount_any(con, root, item, q, (u or {}).get("user") or "")
''', "api_recount takes any item of the round")
    s = s.rstrip("\n") + "\n" + SM_ROUTES
    return s


# ---------------------------------------------------------------- stockmatch.html
SM_CSS = ''' .blk{background:#2b1d1d;color:#fff;border-color:#2b1d1d}
 .blk .bl1{font-size:18px;font-weight:700}.blk .bl2{font-size:15px;opacity:.9;margin-top:2px}.blk .bl3{font-size:16px;font-weight:700;margin-top:6px;color:#ffd9d2;overflow-wrap:anywhere}
 .blk .muted{color:#d8cfcf}.blk input{border:1px solid #777;border-radius:8px;background:#fff;color:#1c1c1c}
 .sugg .btn{margin:4px 6px 0 0}
</style>
</head>'''

SM_JS = r'''function s418Cards(s){
 let h='';
 /* ---- S427 (D632): THE STAFF BLOCK -- pinned until the next count closes. Total loss; the small part written off; the big
    part BY NAME. No reasons, no percentages, no questions; one line 'Kuchh batana hai?' under it. ---- */
 const K=s.block;
 if(K){
  h+='<div class="card blk"><div class="bl1">'+esc(K.lines_hi[0])+'</div><div class="bl2">'+esc(K.lines_hi[1])+'</div><div class="bl3">'+esc(K.lines_hi[2])+'</div>';
  (K.notes||[]).forEach(n=>{ h+='<div class="muted" style="margin-top:4px">'+esc(n.by)+' ('+esc(n.at_text)+'): '+esc(n.text)+'</div>'; });
  h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap;margin-top:8px"><input id="note_t" placeholder="Kuchh batana hai?" maxlength="500" style="flex:1;min-width:12em;font-size:16px;padding:8px"><span class="btn ok" onclick="note()">Bhej do</span></div></div>';
 }
 /* ---- S427: Dobara ginna hai -- Darpan's OWN option, any item of the round; no Marg figure is shown. ---- */
 h+='<div class="card"><h2>Dobara ginna hai</h2><div class="muted">Koi item dobara ginna ho to naam likhiye, phir shelf par jitna hai utna likhiye. Aapki ginti darj ho jaati hai.</div>';
 h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap"><input id="rq" placeholder="Item ka naam" oninput="rsearch()" autocomplete="off" style="flex:1;min-width:12em;font-size:17px;padding:8px"></div><div id="rsugg" class="sugg"></div>';
 if(RSEL){
  h+='<div class="line"><div class="nm">'+esc(RSEL.item)+'</div><div class="muted">'+esc(RSEL.packing||'')+(RSEL.pack>1?' &middot; ek patte mein '+RSEL.pack:'')+'</div>'
   +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+(RSEL.pack>1?'<label>Patte <input id="rs0" inputmode="numeric" style="width:5em;font-size:17px;padding:8px"></label> <label>Goli <input id="rl0" inputmode="numeric" style="width:5em;font-size:17px;padding:8px"></label>'
   :'<label>'+esc(RSEL.whole||'Nag')+' <input id="rl0" inputmode="numeric" style="width:6em;font-size:17px;padding:8px"></label>')+'<span class="btn ok" onclick="recount()">Likh do</span></div></div>';
 }
 const R=s.recounts||[];
 if(R.length){ h+='<div class="muted" style="margin-top:8px">Aapne gina:</div>'; R.forEach(r=>{ h+='<div class="line done"><div class="nm">'+esc(r.item)+'</div><div class="ans">'+esc(r.qty_text)+' <span class="muted">('+esc(r.at_text)+')</span></div></div>'; }); }
 h+='</div>';
 const C=s.claims||[], A=s.claim_answers||[];
 if(C.length){
  h+='<div class="card"><h2>Bina bill? <span class="tag">'+C.filter(c=>!c.answer).length+'</span></h2><div class="muted">Doctor sahab in lines ka pata kar rahe hain &mdash; ek jawab chuniye.</div>';
  C.forEach(c=>{
   h+='<div class="line'+(c.answer?' done':'')+'"><div class="nm">'+esc(c.item)+'</div>'+(c.short_qty?'<div class="muted">'+c.short_qty+' kam</div>':'');
   if(c.answer) h+='<div class="ans">Aapne: '+esc(c.answer_hi)+'</div>';
   h+='<div>'+A.map(a=>'<span class="btn chip'+(c.answer===a.key?' on':'')+'" onclick="claim('+c.id+',\''+a.key+'\')">'+esc(a.hi)+'</span>').join("")+'</div></div>';
  });
  h+='</div>';
 }
 return h;
}
let RSEL=null, RSUGG=[], RT=null;
function rsearch(){
 const q=(el("rq")?el("rq").value:"").trim(); clearTimeout(RT);
 if(q.length<2){ if(el("rsugg")) el("rsugg").innerHTML=""; return; }
 RT=setTimeout(async()=>{ try{ const j=await get("/finance/stockmatch/api/items"+(Q?Q+"&":"?")+"q="+encodeURIComponent(q)); RSUGG=j.items||[];
   if(el("rsugg")) el("rsugg").innerHTML=RSUGG.length?RSUGG.map((it,i)=>'<span class="btn chip" onclick="rpick('+i+')">'+esc(it.item)+'</span>').join(""):'<div class="empty">Koi item nahi mila.</div>';
  }catch(e){ if(el("rsugg")) el("rsugg").innerHTML='<div class="empty">'+esc(e.message)+'</div>'; } },250);
}
function rpick(i){ RSEL=RSUGG[i]; const q=el("rq")?el("rq").value:""; render(); if(el("rq")) el("rq").value=q; const a=el("rs0")||el("rl0"); if(a) a.focus(); }
async function recount(){
 if(BUSY||!RSEL)return; const r=RSEL; const a=el("rs0"), b=el("rl0");
 const body={item:r.item};
 if(r.pack>1){ body.strips=(a&&a.value)||0; body.loose=(b&&b.value)||0; if(String((a&&a.value)||"").trim()===""&&String((b&&b.value)||"").trim()===""){MSG={kind:"err",title:"Ginti likhiye",lines:[esc(r.item)]};render();return;} }
 else { body.pcs=(b&&b.value)||""; if(String(body.pcs).trim()===""){MSG={kind:"err",title:"Ginti likhiye",lines:[esc(r.item)]};render();return;} }
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/recount"+Q,body); RSEL=null; after(j,"✓ Save ho gaya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function note(){
 if(BUSY)return; const t=((el("note_t")||{}).value||"").trim();
 if(!t){MSG={kind:"err",title:"Kuchh likhiye",lines:[]};render();return;}
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/note"+Q,{text:t}); after(j,"✓ Likh liya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
'''


def build_stockmatch_html(s):
    s = rep(s, '''" · phir se gino · bina bill · orthotics · round "''', '''" · dobara ginna hai · bina bill · orthotics · round "''', "subtitle")
    s = rep(s, " h+=s418Cards(s);                                            // S418: Phir se gino + Bina bill?\n",
            " h+=s418Cards(s);                                            // S427 over S418: the staff block, Dobara ginna hai, Bina bill?\n", "the render hook's comment")
    s = rep(s, "</style>\n</head>", SM_CSS, "the block's style")
    s = rep(s, "/* ---- S418 (D631): Phir se gino (count the item again -- no Marg figure is shown, count what is on the shelf) and\n   Bina bill? (the lines the doctor is pursuing -- one answer each). ---- */\n",
            "/* ---- S427 (D632) over S418 (D631): the staff block, Dobara ginna hai (Darpan's own recount -- no Marg figure is shown, count\n   what is on the shelf) and Bina bill? (the lines the doctor is pursuing -- one answer each). ---- */\n", "the S418 comment")
    a_anchor, b_anchor = "function s418Cards(s){\n", "async function claim(id,key){\n"
    if s.count(a_anchor) != 1 or s.count(b_anchor) != 1:
        sys.exit("REFUSED: the S418 cards block is not where it was")
    a, b = s.index(a_anchor), s.index(b_anchor)
    if not (a < b):
        sys.exit("REFUSED: the S418 cards block is out of order")
    s = s[:a] + SM_JS + s[b:]
    return s


# ---------------------------------------------------------------- stock_amir.html
def build_amir(s):
    s = rep(s, "units(", "qw(", "the quantity helper's name", count=16)
    if "unit" in s.lower():
        sys.exit("REFUSED: stock_amir.html still carries the word 'unit'")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = {name: load(os.path.join(a.finance, name), name) for name in FROM}
    out = {
        "stock_app.py": build_stock_app(src["stock_app.py"]),
        "stock_hub.html": build_hub(src["stock_hub.html"]),
        "stockmatch.py": build_stockmatch_py(src["stockmatch.py"]),
        "stockmatch.html": build_stockmatch_html(src["stockmatch.html"]),
        "stock_amir.html": build_amir(src["stock_amir.html"]),
    }
    os.makedirs(a.out, exist_ok=True)
    for name, text in out.items():
        b = text.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s" % (md5(b), name))


if __name__ == "__main__":
    main()
