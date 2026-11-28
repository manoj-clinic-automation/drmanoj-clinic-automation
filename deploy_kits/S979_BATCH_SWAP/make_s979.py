#!/usr/bin/env python3
"""make_s979.py -- S979_BATCH_SWAP: builds the three TO files from the live FROM bytes (each FROM pinned by md5; every anchor exactly once).
    python3 make_s979.py FROM_DIR TO_DIR"""
import hashlib, os, sys

FROM = {"expiry_watch.py": "5db83cbcd25b57fdbd52ab3077623f21",
        "stockmatch.py": "91b5193ff21848274da94ef8dcebf82c",
        "stockmatch.html": "bc67e10238047204e90df933773d3e08"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def rep(s, a, b, name):
    n = s.count(a)
    if n != 1:
        raise SystemExit("ANCHOR %s: found %d times: %r" % (name, n, a[:80]))
    return s.replace(a, b)


EW = [
("ew-kit", '''KIT_S883 = "S883_LEDGER_BATCHES"''', '''KIT_S979 = "S979_BATCH_SWAP"       # 28-Nov-2026 (D1113): the batch swap -- batch_swap.py, its cases on every run, the owner's section
KIT_S883 = "S883_LEDGER_BATCHES"'''),
("ew-run", '''            log("expiry_watch %s: the batch rows failed and were rolled back (%s: %s); the lists stand" % (KIT_S883, type(ex).__name__, str(ex)[:120]))
        judged, made = [], []''', '''            log("expiry_watch %s: the batch rows failed and were rolled back (%s: %s); the lists stand" % (KIT_S883, type(ex).__name__, str(ex)[:120]))
        try:                                                  # S979 (D1113): the batch swap's cases on this run's batches -- never a push
            import batch_swap as _BS                          # noqa: PLC0415 -- beside this file
            with con:
                _BS.after_run(con, rid, today, sp, alias, log)
        except Exception as ex:                               # noqa: BLE001 -- the lists stand; the swap waits for the next run
            try:
                con.rollback()
            except sqlite3.Error:
                pass
            log("expiry_watch %s: the batch swap failed and was rolled back (%s: %s); the lists stand" % (KIT_S979, type(ex).__name__, str(ex)[:120]))
        judged, made = [], []'''),
("ew-page", '''    out = [head, sub, '<div class="screen">']''', '''    out = [head, sub, '<div class="screen">', _s979_section(con, today)]   # S979 (D1113): Batch swaps, collapsed, above Near expiry'''),
("ew-marks", '''    nr = sorted(sec.get("near", []), key=lambda x: (x["expiry"], -x["units"]))''', '''    nr = sorted(sec.get("near", []), key=lambda x: (x["expiry"], -x["units"]))
    s979_marks = _s979_marks(con)                             # S979: Darpan's 'Hai, N' -- the batch stays here as listed, marked'''),
("ew-nearrow", '''        body.append('<tr><td>%s</td><td class="m">%s</td><td class="m">%s</td><td class="m n">%s</td></tr>'
                    % (esc(x["item"]), esc(x["batch"]), esc(mon_year(x["expiry"])), esc(qty_txt(x["units"], x["pack"]))))''',
 '''        body.append('<tr><td>%s%s</td><td class="m">%s</td><td class="m">%s</td><td class="m n">%s</td></tr>'
                    % (esc(x["item"]), _s979_mark(s979_marks, x), esc(x["batch"]), esc(mon_year(x["expiry"])), esc(qty_txt(x["units"], x["pack"]))))'''),
("ew-needs", '''                            text="%s's Batch Stock came as a filtered list, not the whole store -- it is not used" % MON[today.month]))
    return out''', '''                            text="%s's Batch Stock came as a filtered list, not the whole store -- it is not used" % MON[today.month]))
    out.extend(_s979_needs(con, today))                       # S979: one line when a batch swap is red
    return out'''),
("ew-helpers", '''def _hand_section(con, today):''', '''def _s979_section(con, today):
    """S979 (D1113): the collapsed 'Batch swaps' section (batch_swap.owner_section). Fail-soft ''."""
    try:
        import batch_swap as _BS                              # noqa: PLC0415 -- beside this file
        return _BS.owner_section(con, today)
    except Exception:                                         # noqa: BLE001 -- the page stands without it
        return ""


def _s979_marks(con):
    try:
        import batch_swap as _BS                              # noqa: PLC0415
        return _BS.near_marks(con)
    except Exception:                                         # noqa: BLE001
        return {}


def _s979_mark(marks, x):
    """' <tag>Darpan found it -- on the shelf . N</tag>' for a near batch he answered 'Hai, N'; '' otherwise."""
    if not marks:
        return ""
    n = marks.get((x.get("k20"), re.sub(r'[^A-Z0-9]', '', nbatch(x.get("batch")))))
    if not n:
        return ""
    return (' <span style="display:inline-block;font-size:.72rem;padding:0 6px;border-radius:999px;background:var(--amber-soft);'
            'color:var(--amber)">Darpan found it &mdash; on the shelf &middot; %s</span>' % esc(qty_txt(n, x.get("pack") or 1)))


def _s979_needs(con, today):
    try:
        import batch_swap as _BS                              # noqa: PLC0415
        return _BS.needs_you(con, today)
    except Exception:                                         # noqa: BLE001
        return []


def _hand_section(con, today):'''),
]

SM = [
("sm-ver", '''VERSION = "1.4"
KIT = "S936_RECOUNT_SITTING"''', '''VERSION = "1.5"
KIT = "S979_BATCH_SWAP"                                             # v1.5 S979 (the batch swap's card)
KIT_S936 = "S936_RECOUNT_SITTING"'''),
("sm-state", '''    st["watch"] = _sw_view(con, me)                                # S428: Aaj ki ginti, the plan question, the loss lines, the traces
    return st''', '''    st["watch"] = _sw_view(con, me)                                # S428: Aaj ki ginti, the plan question, the loss lines, the traces
    st["swap"] = _bs_view(con)                                     # S979 (D1113): Expiry batch -- shelf par dekhiye; Batch badlo
    return st'''),
]

SM_TAIL = '''

# ------------------------------------------------------------------ S979 (D1113, 28-Nov-2026): the batch swap's card
#  'Expiry batch -- shelf par dekhiye' (Nahi hai / Hai, N) and 'Batch badlo -- Marg mein sirf 2 bill' (Dono bill bana diye).
#  The rules are batch_swap.py's; this file only carries his taps through the same door as every Stock milaan tap (_auth).
def _bs():
    import batch_swap                                         # noqa: PLC0415 -- beside this file
    return batch_swap


def _bs_view(con):
    try:
        return _bs().darpan_view(con)
    except Exception:                                         # noqa: BLE001 -- the page stands without the card
        return None


@bp.route("/finance/stockmatch/api/swap", methods=["POST"])
def api_swap():
    """{case, answer: nahi | hai, strips/loose or pcs} -- his shelf answer."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        cid = int(b.get("case"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request", message="Item chuniye."), 400
    q = {k: b.get(k) for k in ("strips", "loose", "pcs")}
    ok, msg, code = _bs().answer(con, cid, str(b.get("answer") or "").strip().lower(), q, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="swap", message=msg))


@bp.route("/finance/stockmatch/api/swap/bills", methods=["POST"])
def api_swap_bills():
    """{ids: [...]} -- 'Dono bill bana diye': his tap is recorded; the next sale report closes the cases."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg, code = _bs().bills_made(con, b.get("ids") or [], (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="swap_bills", message=msg))
'''

HT = [
("ht-render", ''' h+=s428Top(s);                                              // S428 / S502''', ''' h+=swapCards(s);                                            // S979 (D1113): Expiry batch -- shelf par dekhiye; Batch badlo (above Aaj ki ginti)
 h+=s428Top(s);                                              // S428 / S502'''),
("ht-fns", '''function todayText(){''', '''/* ---- S979 (D1113): the batch swap. An expiring batch Marg still holds beside a newer one: he checks the shelf (Nahi hai / Hai),
   then makes two Marg bills named STOCK (a sale of the old batch, a sale return on the newer batch, same rate). ---- */
function swapLine(x,b){return '<div class="muted" style="color:#1c1c1c;font-size:15px;margin:4px 0;padding-left:10px;border-left:3px solid #2e6b34">'+esc(x.item)+' &middot; '+esc(x.swap_hi)+' &middot; batch <b>'+esc(b?x.new_batch:x.old_batch)+'</b> ('+esc(b?x.new_exp:x.old_exp)+')</div>';}
function swapCards(s){
 const W=s&&s.swap; if(!W||!W.ok) return '';
 let h='';
 if(W.half&&W.half.length){
  h+='<div class="card" style="border:2px solid #b3261e"><h2>STOCK bill adhoora <span class="tag">'+W.half.length+'</span></h2><div class="muted">Sale report mein ek hi bill aaya. Yeh bill bhi Marg mein banaiye (naam STOCK, wahi rate):</div>';
  W.half.forEach(x=>{h+='<div class="line"><div class="nm">'+(x.missing==="ret"?'Bill 2 &middot; SALE RETURN':'Bill 1 &middot; SALE')+'</div>'+swapLine(x,x.missing==="ret")+'</div>';});
  h+='</div>';
 }
 if(W.ask&&W.ask.length){
  h+='<div class="card" style="border:2px solid #b4541a"><h2>Expiry batch &mdash; shelf par dekhiye <span class="tag">'+W.ask.length+'</span></h2><div class="muted">Marg mein yeh purana batch abhi bhi likha hai. Shelf par dekh kar bataiye.</div>';
  W.ask.forEach(x=>{
   h+='<div class="line"><div class="nm">'+esc(x.item)+'</div><div class="muted">batch '+esc(x.old_batch)+' &middot; exp '+esc(x.old_exp)+' &middot; Marg mein '+esc(x.paper_hi)+' &middot; aakhri bikri '+esc(x.last_sell)+'</div>'
    +'<div><span class="btn" onclick="swapAns('+x.id+',\\'nahi\\','+x.pack+')">Nahi hai</span></div>'
    +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap;align-items:center"><b style="margin-right:6px">Hai &mdash;</b>'+boxes(x.pack,'Nag','x'+x.id)+' <span class="btn ok" onclick="swapAns('+x.id+',\\'hai\\','+x.pack+')">Bhej do</span></div></div>';
  });
  h+='</div>';
 }
 if(W.bills){
  const B=W.bills;
  h+='<div class="card" style="border:2px solid #2e6b34"><h2>Batch badlo &mdash; Marg mein sirf 2 bill</h2><div class="muted">Customer ka naam: <b>STOCK</b> &middot; cash nahi &middot; item ka total nahi badlega.</div>'
   +'<div class="line"><div class="nm">Bill 1 &middot; SALE &middot; naam STOCK</div>'+B.sale.map(x=>swapLine(x,false)).join('')+'</div>'
   +'<div class="line"><div class="nm">Bill 2 &middot; SALE RETURN &middot; naam STOCK &middot; wahi rate</div>'+B.ret.map(x=>swapLine(x,true)).join('')+'</div>'
   +'<div><span class="btn ok" onclick="swapBills()">Dono bill bana diye</span></div></div>';
 }
 if(W.made&&W.made.length){
  h+='<div class="card"><div class="muted">STOCK bill bana diye: '+W.made.map(x=>esc(x.item)).join(', ')+' &mdash; kal subah ki sale report se band hoga.</div></div>';
 }
 return h;
}
async function swapAns(id,ans,pack){
 if(BUSY)return;
 const body={case:id,answer:ans};
 if(ans==="hai"&&!readBoxes(pack,"x"+id,body)){MSG={kind:"err",title:"Shelf par kitna hai, likhiye",lines:[]};render();window.scrollTo(0,0);return;}
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/swap"+Q,body);after(j,"\\u2713 Save ho gaya",[esc((j.saved||{}).message||"")]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function swapBills(){
 const B=(S&&S.swap&&S.swap.bills)||null;
 if(BUSY||!B)return;
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/swap/bills"+Q,{ids:B.ids});after(j,"\\u2713 Likh liya",[esc((j.saved||{}).message||"")]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
function todayText(){'''),
]


def build(src, dst):
    os.makedirs(dst, exist_ok=True)
    for name, want in FROM.items():
        b = open(os.path.join(src, name), "rb").read()
        if md5(b) != want:
            raise SystemExit("FROM %s is %s, not %s -- refused" % (name, md5(b), want))
    s = open(os.path.join(src, "expiry_watch.py"), encoding="utf-8").read()
    for n, a, b in EW:
        s = rep(s, a, b, n)
    open(os.path.join(dst, "expiry_watch.py"), "w", encoding="utf-8").write(s)
    s = open(os.path.join(src, "stockmatch.py"), encoding="utf-8").read()
    for n, a, b in SM:
        s = rep(s, a, b, n)
    s = s.rstrip("\n") + "\n" + SM_TAIL
    open(os.path.join(dst, "stockmatch.py"), "w", encoding="utf-8").write(s)
    s = open(os.path.join(src, "stockmatch.html"), encoding="utf-8").read()
    for n, a, b in HT:
        s = rep(s, a, b, n)
    open(os.path.join(dst, "stockmatch.html"), "w", encoding="utf-8").write(s)
    for name in FROM:
        print("%-16s %s -> %s" % (name, FROM[name][:8], md5(open(os.path.join(dst, name), "rb").read())[:8]))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
