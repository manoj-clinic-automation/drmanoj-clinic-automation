#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s428.py -- builds the patched live files of kit S428_STOCK_WATCH from the LIVE bytes by anchored edits. Every anchor
must occur exactly once, and every source must be at its FROM pin, or the build stops with nothing written. Nothing is
re-typed. (stock_watch.py is new.)

  stock_app.py               stock_watch imported defensively; the desk read runs a trace on every Big-loss line and carries the
                             watch card; /pile/setting routes count./spot./arrival./leak. keys to the watch; a close writes the full
                             count's points; Amir's board carries the watch; NEW /api/watch, /api/watch/ask, /api/watch/plan/pick,
                             /api/watch/plan/line, /api/watch/trace/<id>/seen, /api/watch/roster, /api/watch/roster/build
  stockmatch.py              the state carries Darpan's watch view; NEW /api/spot, /api/stock, /api/gadbad, /api/plan, /api/trace/<id>/seen,
                             /api/watch-items
  stockmatch.html            'Aaj ki ginti' on top, the plan question, the dated loss lines, 'Stock batao', 'Kuchh gadbad hai', 'Dekh liya'
  stock_amir.html            'Ginti ka Sunday chunein', 'bill entry baaki', the traces' fix lines
  stock_loss.html            'Count this' on every line, the watch card (plan, rosters, the watch list, traces, tap vs bill, leakage),
                             the second settings heading 'Counts & watch'
  sanjeevni_approvals.py     v1.11: the Month section's leakage line; Needs you block 14 (fail-soft)
  finance_ui/finance_approvals.html  ONE anchored line: the leakage line under a month (PARENT'S file, declared)
  packs_checklist.html       ONE anchored line: the confirmed count Sunday on Shavez's checklist

Usage: make_s428.py --finance /root/finance --out DIR      (writes the eight files flat into DIR, prints each md5;
       finance_approvals.html is written flat as finance_approvals.html)
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "24c2b5fe7cacfe238751e487e52eb6d0",
    "stockmatch.py": "e85807dab1f8672d482272e0d355fe28",
    "stockmatch.html": "ecd039f4f64d5be6a15d7ffbbcdf3950",
    "stock_amir.html": "244ac6eeb0117b14f2c3c7fa1576f728",
    "stock_loss.html": "fdd913e75677580a7897fe2631196c4c",
    "sanjeevni_approvals.py": "64548b9b36770992dd3da2081e52ffe1",
    "finance_ui/finance_approvals.html": "588975fcff2644db115b63058c4d62dc",
    "packs_checklist.html": "6f027a7e74314584bfb5ae88607e6275",
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
IMPORT_BLOCK = '''# --- S427_LOSS_DESK_RULINGS end --------------------------------------------

# --- S428_STOCK_WATCH begin (D633) -----------------------------------------
# Sunday full counts, spot counts three mornings a week, arrivals as provisional stock, the trace, the leakage budget,
# the watch list -- stock_watch.py beside this file. Defensive: without it every page behaves exactly as before S428.
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import stock_watch as _sw                              # noqa: PLC0415
    STOCK_WATCH_OK = True
except Exception:                                          # pragma: no cover
    _sw = None
    STOCK_WATCH_OK = False
# --- S428_STOCK_WATCH end --------------------------------------------------
'''

ROUTES = r'''
# ---- S428_STOCK_WATCH begin (D633) ----------------------------------------------
def _watch_gate(roles=("checker",)):
    u, err = _require(*roles)
    if err:
        return None, None, err
    if not STOCK_WATCH_OK:
        return None, None, (jsonify(ok=False, error="unavailable", message="stock_watch.py is not beside stock_app.py"), 503)
    con = _db()
    ensure_schema(con)
    _sw.ensure(con)
    return u, con, None


@bp.route("/api/watch")
def api_watch():
    """The owner's watch card: the plan, today's and the next roster, the watch list, the traces, tap vs bill, leakage, settings."""
    u, con, err = _watch_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    return jsonify(**_sw.owner_view(con, _newest_root(con) or 0))


@bp.route("/api/watch/ask", methods=["POST"])
def api_watch_ask():
    """The owner's 'Count this' -> the head of Darpan's next morning list."""
    u, con, err = _watch_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg, code = _sw.ask(con, str(b.get("item") or "").strip(), (u or {}).get("user") or "")
    return jsonify(ok=ok, message=msg), code


@bp.route("/api/watch/plan/pick", methods=["POST"])
def api_watch_plan_pick():
    """Amir picks the count's Sunday ('Ginti ka Sunday chunein'); the owner may too."""
    u, con, err = _watch_gate(("checker", "maker", "viewer"))
    if err:
        return err
    who = (u or {}).get("user") or ""
    if not (_may_decide(u) or who == "amir"):
        return jsonify(ok=False, error="forbidden", message="Amir picks the Sunday."), 403
    b = request.get_json(silent=True) or {}
    ok, msg, code = _sw.plan_pick(con, str(b.get("sunday") or "").strip(), who)
    return jsonify(ok=ok, message=msg, plan=_sw.plan_state(con).get("plan")), code


@bp.route("/api/watch/plan/line")
def api_watch_plan_line():
    """One line for Shavez's checklist (and any staff page): the confirmed count Sunday, in Hindi."""
    u, con, err = _watch_gate(("checker", "maker", "viewer"))
    if err:
        return err
    return jsonify(**_sw.plan_line(con))


@bp.route("/api/watch/trace/<int:tid>/seen", methods=["POST"])
def api_watch_trace_seen(tid):
    u, con, err = _watch_gate(("checker", "maker"))
    if err:
        return err
    ok, msg, code = _sw.trace_seen(con, tid, (u or {}).get("user") or "")
    return jsonify(ok=ok, message=msg), code


@bp.route("/api/watch/roster")
def api_watch_roster():
    """The roster of a day (default today), the owner's read."""
    u, con, err = _watch_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    day = str(request.args.get("day") or "").strip()
    try:
        d = dt.date.fromisoformat(day) if day else dt.date.today()
    except ValueError:
        return jsonify(ok=False, error="bad_request", message="day as YYYY-MM-DD"), 400
    return jsonify(ok=True, **_sw.roster_view(con, d))


@bp.route("/api/watch/roster/build", methods=["POST"])
def api_watch_roster_build():
    """The owner asks for today's list now (the 06:30 job does this by itself; a forced build ignores the spot days)."""
    u, con, err = _watch_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    b = request.get_json(silent=True) or {}
    R = _sw.build_roster(con, dt.date.today(), who=(u or {}).get("user") or "", force=bool(b.get("force")))
    return jsonify(ok=True, **R)
# ---- S428_STOCK_WATCH end -----------------------------------------------------------
'''


def build_stock_app(s):
    s = rep(s, "# --- S427_LOSS_DESK_RULINGS end --------------------------------------------\n", IMPORT_BLOCK, "import stock_watch")
    s = rep(s, '''    out = _lp.desk(con, d, (u or {}).get("user") or "")
''', '''    out = _lp.desk(con, d, (u or {}).get("user") or "")
    if STOCK_WATCH_OK:                                          # S428 (D633): a trace on every Big-loss line; the owner's watch card
        _sw.trace_big_losses(con, d["count_id"], [l for p in out["piles"] for l in p["lines"]], (u or {}).get("user") or "")
        out["watch"] = _sw.owner_view(con, d["count_id"])
''', "the desk read: traces + the watch card")
    s = rep(s, '''    ok, msg = _lp.set_setting_req(con, str(b.get("key") or "").strip(), b, (u or {}).get("user") or "", root)   # S427: {value} or {add} / {remove} for the list
''', '''    key_ = str(b.get("key") or "").strip()
    if STOCK_WATCH_OK and key_.startswith(_sw.PREFIXES):       # S428: the 'Counts & watch' heading's keys
        ok, msg = _sw.set_setting(con, key_, b.get("value"), (u or {}).get("user") or "")
    else:
        ok, msg = _lp.set_setting_req(con, key_, b, (u or {}).get("user") or "", root)   # S427: {value} or {add} / {remove} for the list
''', "/pile/setting routes the watch keys")
    s = rep(s, '''    ok, msg, code, done = _lp.close(con, root, b.get("token"), who)
''', '''    ok, msg, code, done = _lp.close(con, root, b.get("token"), who)
    if ok and STOCK_WATCH_OK and (done or {}).get("run"):     # S428 (3.1): a closed full count writes one point per counted item
        _sw.full_count_points(con, root, None, who)
''', "the close writes the full count's points")
    s = rep(s, '''    return dict(count_id=d["count_id"], day=d["day"], lookups=look, vouchers=vouchers, made=_voucher_state(con, d), tranches=tr,   # S301
''', '''    return dict(watch=(_sw.amir_view(con) if STOCK_WATCH_OK else None),   # S428: the Sunday buttons, bill entry baaki, the traces' fix lines
                count_id=d["count_id"], day=d["day"], lookups=look, vouchers=vouchers, made=_voucher_state(con, d), tranches=tr,   # S301
''', "Amir's board carries the watch")
    s = rep(s, '''# ---- S427_LOSS_DESK_RULINGS end ---------------------------------------------------
''', '''# ---- S427_LOSS_DESK_RULINGS end ---------------------------------------------------
''' + ROUTES.lstrip("\n"), "the S428 routes")
    return s


# ---------------------------------------------------------------- stockmatch.py
SM_ROUTES = r'''


# ------------------------------------------------------------------ S428 (D633): Aaj ki ginti, Stock batao, Kuchh gadbad hai, the plan
def _sw():
    import stock_watch                                        # noqa: PLC0415 -- beside this file
    return stock_watch


def _sw_view(con):
    try:
        return _sw().darpan_view(con)
    except Exception:                                          # noqa: BLE001
        return None


def _qty_from(b, pack):
    """{strips, loose} or {pcs} -> tablets / pieces; None when nothing was typed."""
    whole = b.get("pcs") if b.get("pcs") not in (None, "") else b.get("units")
    if whole not in (None, ""):
        return int(float(whole))
    if b.get("strips") in (None, "") and b.get("loose") in (None, ""):
        return None
    return int(float(b.get("strips") or 0)) * int(pack or 1) + int(float(b.get("loose") or 0))


def _sw_state(con, u, kind, saved):
    root = root_of(con, _cid())
    d = report(con, root)
    st = _state_for(con, d, u, kind) if d else dict(ok=True)
    st.update(saved=saved, round_made=None)
    return jsonify(**st)


@bp.route("/finance/stockmatch/api/spot", methods=["POST"])
def api_spot():
    """Aaj ki ginti -- one item of the day's roster: {roster_id, strips, loose} or {roster_id, pcs}."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        rid = int(b.get("roster_id") or 0)
    except (TypeError, ValueError):
        rid = 0
    r = con.execute("SELECT pack FROM stock_spot_roster WHERE id=?", (rid,)).fetchone() if rid else None
    if not r:
        return jsonify(ok=False, error="not_found", message="Yeh item aaj ki list mein nahi hai."), 404
    try:
        q = _qty_from(b, r[0])
    except (TypeError, ValueError):
        q = None
    if q is None or q < 0 or q > 100000:
        return jsonify(ok=False, error="bad_request", message="Ginti likhiye."), 400
    ok, msg, code, P = _sw().answer_roster(con, rid, q, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="spot", message=msg, point=P))


@bp.route("/finance/stockmatch/api/watch-items")
def api_watch_items():
    """Stock batao / Kuchh gadbad hai: any item of the shop (the spine's names) carrying the words typed."""
    u, con, kind, err = _auth()
    if err:
        return err
    q = str(request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify(ok=True, items=[])
    sw = _sw()
    sp = sw.Spine()
    out = []
    for it in sp.search(q, 12):
        pack = sw.pack_of(it["packing"])
        out.append(dict(item=it["name"], pack=pack, packing=it["packing"] or "", whole=sw._qwm().whole_word(it["packing"] or "", None, it["name"], pack, "hi")))
    return jsonify(ok=True, items=out)


@bp.route("/finance/stockmatch/api/stock", methods=["POST"])
def api_stock_batao():
    """Stock batao -- any item, any day: {item, strips, loose} or {item, pcs} -> a darpan point."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    item = str(b.get("item") or "").strip()
    sw = _sw()
    info = sw.item_info(con, sw.Spine(), item)
    try:
        q = _qty_from(b, info["pack"])
    except (TypeError, ValueError):
        q = None
    if not item or q is None or q < 0 or q > 100000:
        return jsonify(ok=False, error="bad_request", message="Item aur ginti likhiye."), 400
    ok, msg, code, P = sw.darpan_point(con, item, q, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="stock", message=msg, point=P))


@bp.route("/finance/stockmatch/api/gadbad", methods=["POST"])
def api_gadbad():
    """Kuchh gadbad hai -- {item, text, strips?, loose? | pcs?} -> a loss point when counted, and THE TRACE."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    item = str(b.get("item") or "").strip()
    text = str(b.get("text") or "").strip()
    if not item or not text:
        return jsonify(ok=False, error="bad_request", message="Item aur kya gadbad hai, dono likhiye."), 400
    sw = _sw()
    info = sw.item_info(con, sw.Spine(), item)
    try:
        q = _qty_from(b, info["pack"])
    except (TypeError, ValueError):
        q = None
    ok, msg, code, R = sw.gadbad(con, item, text, (u or {}).get("user") or "", qty_units=q)
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="gadbad", message=msg, trace=(R or {}).get("trace"), point=(R or {}).get("point")))


@bp.route("/finance/stockmatch/api/plan", methods=["POST"])
def api_plan():
    """The count's Sunday: {answer: ok | no} -- 'Theek hai' confirms, 'Nahi ho payega' sends it back to Amir."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg, code = _sw().plan_answer(con, str(b.get("answer") or "").strip().lower(), (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="plan", message=msg))


@bp.route("/finance/stockmatch/api/trace/<int:tid>/seen", methods=["POST"])
def api_trace_seen(tid):
    """'Dekh liya' on a trace."""
    u, con, kind, err = _auth()
    if err:
        return err
    ok, msg, code = _sw().trace_seen(con, tid, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="trace_seen", message=msg))
'''


def build_stockmatch_py(s):
    s = rep(s, '''    st.update(_s418_extra(con, d["count_id"]))                # S418: Phir se gino + Bina bill? (medicines too)
''', '''    st.update(_s418_extra(con, d["count_id"]))                # S418: Phir se gino + Bina bill? (medicines too)
    st["watch"] = _sw_view(con)                                # S428: Aaj ki ginti, the plan question, the loss lines, the traces
''', "_state_for carries the watch")
    s = s.rstrip("\n") + "\n" + SM_ROUTES
    return s


# ---------------------------------------------------------------- stockmatch.html
SM_JS = r'''/* ---- S428 (D633): Darpan's side of the watch. Aaj ki ginti (the morning's items, on top), the count's Sunday
   (Theek hai / Nahi ho payega), the dated loss lines under the block, Stock batao (any item, any day), Kuchh gadbad
   hai (what he sees -> the trace), Dekh liya on a trace. ---- */
function boxes(pack, whole, id){
 return pack>1?'<label>Patte <input id="ws'+id+'" inputmode="numeric" style="width:5em;font-size:17px;padding:8px"></label> <label>Goli <input id="wl'+id+'" inputmode="numeric" style="width:5em;font-size:17px;padding:8px"></label>'
  :'<label>'+esc(whole||'Nag')+' <input id="wl'+id+'" inputmode="numeric" style="width:6em;font-size:17px;padding:8px"></label>';
}
function readBoxes(pack, id, body){
 const a=el("ws"+id), b=el("wl"+id);
 if(pack>1){ body.strips=(a&&a.value)||0; body.loose=(b&&b.value)||0; return String((a&&a.value)||"").trim()!==""||String((b&&b.value)||"").trim()!==""; }
 body.pcs=(b&&b.value)||""; return String(body.pcs).trim()!=="";
}
function s428Top(s){
 const W=s.watch; if(!W||!W.ok) return '';
 let h='';
 const R=W.roster||{items:[]};
 if(R.items.length){
  h+='<div class="card"><h2>Aaj ki ginti <span class="tag">'+R.open+'</span></h2><div class="muted">'+esc(R.day_text)+' &middot; yeh '+R.items.length+' item aaj subah gin kar likhiye. Shelf par jitna hai utna.</div>';
  R.items.forEach(r=>{
   h+='<div class="line'+(r.answered_at?' done':'')+'"><div class="nm">'+esc(r.item)+'</div><div class="muted">'+esc(r.packing||'')+(r.pack>1?' &middot; ek patte mein '+r.pack:'')+(r.reason_hi?' &middot; '+esc(r.reason_hi):'')+'</div>';
   if(r.answered_at) h+='<div class="ans">Aapne gina: '+esc(r.qty_hi)+'</div>';
   else h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(r.pack,r.whole_hi,"r"+r.id)+'<span class="btn ok" onclick="spot('+r.id+','+r.pack+')">Bhej do</span></div>';
   h+='</div>';
  });
  h+='</div>';
 }
 if(W.plan){
  h+='<div class="card"><h2>Poori ginti ka Sunday</h2><div class="muted">'+esc(W.plan.text_hi)+'</div>';
  if(!W.plan.confirmed) h+='<div><span class="btn ok" onclick="plan(\'ok\')">Theek hai</span><span class="btn bad" onclick="plan(\'no\')">Nahi ho payega</span></div>';
  h+='</div>';
 }
 return h;
}
function s428Cards(s){
 const W=s.watch; if(!W||!W.ok) return '';
 let h='';
 if((W.losses||[]).length){
  h+='<div class="card"><h2>Ginti mein kam nikla</h2>'+W.losses.map(l=>'<div class="line"><div class="nm">'+esc(l.text_hi)+'</div></div>').join("")+'</div>';
 }
 h+='<div class="card"><h2>Stock batao</h2><div class="muted">Kisi bhi din, koi bhi item: naam likhiye, phir shelf par jitna hai utna likhiye.</div>';
 h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap"><input id="sq" placeholder="Item ka naam" oninput="wsearch(\'sq\',\'ssugg\',\'spick\')" autocomplete="off" style="flex:1;min-width:12em;font-size:17px;padding:8px"></div><div id="ssugg" class="sugg"></div>';
 if(SSEL){ h+='<div class="line"><div class="nm">'+esc(SSEL.item)+'</div><div class="muted">'+esc(SSEL.packing||'')+(SSEL.pack>1?' &middot; ek patte mein '+SSEL.pack:'')+'</div><div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(SSEL.pack,SSEL.whole,"s")+'<span class="btn ok" onclick="stockBatao()">Likh do</span></div></div>'; }
 h+='</div>';
 h+='<div class="card"><h2>Kuchh gadbad hai?</h2><div class="muted">Koi item kam lag raha hai, ek-do dabbe nahi mil rahe? Item chuniye, kya dikh raha hai likhiye. System bikri aur kharid dekh kar batayega.</div>';
 h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap"><input id="gq" placeholder="Item ka naam" oninput="wsearch(\'gq\',\'gsugg\',\'gpick\')" autocomplete="off" style="flex:1;min-width:12em;font-size:17px;padding:8px"></div><div id="gsugg" class="sugg"></div>';
 if(GSEL){ h+='<div class="line"><div class="nm">'+esc(GSEL.item)+'</div><div class="muted">'+esc(GSEL.packing||'')+(GSEL.pack>1?' &middot; ek patte mein '+GSEL.pack:'')+'</div>'
   +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap"><input id="gt" placeholder="Kya gadbad hai?" maxlength="500" style="flex:1;min-width:12em;font-size:16px;padding:8px"></div>'
   +'<div class="muted">Abhi shelf par kitna hai (likh sakein to):</div><div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(GSEL.pack,GSEL.whole,"g")+'<span class="btn ok" onclick="gadbad()">Bhej do</span></div></div>'; }
 h+='</div>';
 if((W.traces||[]).length){
  h+='<div class="card"><h2>System ne dekha</h2>'+W.traces.map(t=>'<div class="line"><div class="nm">'+esc(t.text_hi)+'</div><div><span class="btn chip" onclick="seen('+t.id+')">Dekh liya</span></div></div>').join("")+'</div>';
 }
 return h;
}
let SSEL=null, GSEL=null, WSUGG={}, WT=null;
function wsearch(inp, box, pick){
 const q=(el(inp)?el(inp).value:"").trim(); clearTimeout(WT);
 if(q.length<2){ if(el(box)) el(box).innerHTML=""; return; }
 WT=setTimeout(async()=>{ try{ const j=await get("/finance/stockmatch/api/watch-items"+(Q?Q+"&":"?")+"q="+encodeURIComponent(q)); WSUGG[box]=j.items||[];
   if(el(box)) el(box).innerHTML=WSUGG[box].length?WSUGG[box].map((it,i)=>'<span class="btn chip" onclick="'+pick+'('+i+')">'+esc(it.item)+'</span>').join(""):'<div class="empty">Koi item nahi mila.</div>';
  }catch(e){ if(el(box)) el(box).innerHTML='<div class="empty">'+esc(e.message)+'</div>'; } },250);
}
function spick(i){ SSEL=WSUGG["ssugg"][i]; const q=el("sq")?el("sq").value:""; render(); if(el("sq")) el("sq").value=q; }
function gpick(i){ GSEL=WSUGG["gsugg"][i]; const q=el("gq")?el("gq").value:""; render(); if(el("gq")) el("gq").value=q; const t=el("gt"); if(t) t.focus(); }
async function spot(rid, pack){
 if(BUSY)return; const body={roster_id:rid};
 if(!readBoxes(pack,"r"+rid,body)){MSG={kind:"err",title:"Ginti likhiye",lines:[]};render();return;}
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/spot"+Q,body); after(j,"✓ Save ho gaya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function stockBatao(){
 if(BUSY||!SSEL)return; const body={item:SSEL.item};
 if(!readBoxes(SSEL.pack,"s",body)){MSG={kind:"err",title:"Ginti likhiye",lines:[esc(SSEL.item)]};render();return;}
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/stock"+Q,body); SSEL=null; after(j,"✓ Save ho gaya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function gadbad(){
 if(BUSY||!GSEL)return; const body={item:GSEL.item, text:((el("gt")||{}).value||"").trim()};
 if(!body.text){MSG={kind:"err",title:"Kya gadbad hai, likhiye",lines:[esc(GSEL.item)]};render();return;}
 readBoxes(GSEL.pack,"g",body);
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/gadbad"+Q,body); GSEL=null; after(j,"✓ Likh liya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function plan(ans){
 if(BUSY)return; BUSY=true;
 try{const j=await post("/finance/stockmatch/api/plan"+Q,{answer:ans}); after(j,"✓ Likh liya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function seen(id){
 if(BUSY)return; BUSY=true;
 try{const j=await post("/finance/stockmatch/api/trace/"+id+"/seen"+Q,{}); after(j,"✓",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
'''


def build_stockmatch_html(s):
    s = rep(s, " h+=s418Cards(s);                                            // S427 over S418: the staff block, Dobara ginna hai, Bina bill?\n",
            " h+=s428Top(s);                                              // S428: Aaj ki ginti on top, the count's Sunday\n"
            " h+=s418Cards(s);                                            // S427 over S418: the staff block, Dobara ginna hai, Bina bill?\n"
            " h+=s428Cards(s);                                            // S428: the loss lines, Stock batao, Kuchh gadbad hai, Dekh liya\n", "render hooks")
    s = rep(s, "async function claim(id,key){\n", SM_JS + "async function claim(id,key){\n", "the S428 JS")
    s = rep(s, '''" · dobara ginna hai · bina bill · orthotics · round "''', '''" · aaj ki ginti · dobara ginna hai · bina bill · round "''', "subtitle")
    return s


# ---------------------------------------------------------------- stock_amir.html
AMIR_JS = r'''/* ---- S428 (D633): the watch on Amir's board -- Ginti ka Sunday chunein (when a full count falls due), bill entry
   baaki (an arrival tapped, no purchase in Marg after the grace days), the traces' fix lines. ---- */
function watchCard(W){
  if(!W||W.ok===false) return '';
  let h='<div class="card" id="watch"><h2><span class="n">7</span>Stock ginti — Sunday, bill entry, sudhaar</h2><div class="hi">स्टॉक गिनती का Sunday, बिल एंट्री बाकी, Marg में सुधार</div>';
  const P=W.plan;
  if(P){
    h+='<div class="lead"><b>Poori ginti due hai</b> ('+esc(P.due_from?("from "+P.due_from.split("-").reverse().join("-")):"")+'). '+(P.status==="confirmed"?'Sunday <b>'+esc(P.sunday_text)+'</b> — Darpan ne haan kaha ✓':(P.status==="picked"?'Aapne <b>'+esc(P.sunday_text)+'</b> chuna — Darpan ki haan baaki':'Ginti ka Sunday chunein:'))+'</div>';
    if(P.status!=="confirmed") h+='<div style="margin:6px 0">'+(P.window_text||[]).map((t,i)=>'<button class="b'+(P.window[i]===P.sunday?' main':'')+'" data-sunday="'+esc(P.window[i])+'">'+esc(t)+'</button>').join(" ")+'</div><div class="msg" id="wmsg"></div>';
  } else h+='<div class="lead">Agli poori ginti '+esc((W.due_from||"").split("-").reverse().join("-"))+' ke baad ke kisi Sunday ko — tab yahan Sunday chunne ka button aayega.</div>';
  const B=W.bill_pending||[];
  h+='<h3 style="font-size:15px;margin:10px 0 2px">Bill entry baaki ('+B.length+')</h3>'+(B.length?B.map(x=>'<div class="row"><div><div class="it">'+esc(x.text_hi)+'</div><div class="q">'+esc(x.item)+' — maal aa gaya, Marg mein bill abhi nahi</div></div></div>').join(""):'<div class="empty">koi nahi — har tapped arrival ka bill Marg mein hai</div>');
  const F=W.fixes||[];
  h+='<h3 style="font-size:15px;margin:10px 0 2px">Marg mein sudhaar ('+F.length+')</h3>'+(F.length?F.map(x=>'<div class="row"><div><div class="it">'+esc(x.item)+'</div><div class="q">'+esc(x.fix)+' · '+esc(x.at_text)+'</div></div></div>').join(""):'<div class="empty">koi nahi</div>');
  return h+'</div>';
}
'''


def build_amir(s):
    s = rep(s, '''  document.getElementById("body").innerHTML=h;
''', '''  h+=watchCard(d.watch);                                                                             // S428: the stock watch
  document.getElementById("body").innerHTML=h;
''', "the watch card on the board")
    s = rep(s, '''document.addEventListener("click", async e=>{
''', AMIR_JS + '''document.addEventListener("click", async e=>{
  const sd=e.target.closest("button[data-sunday]"); if(sd){ const m=document.getElementById("wmsg"); if(m) m.textContent="…";   // S428
    const r=await fetch(BASE+"/api/watch/plan/pick",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sunday:sd.dataset.sunday})}).catch(()=>null);
    const j=r?await r.json().catch(()=>null):null; if(m) m.textContent=(j&&j.message)||"the server did not answer"; if(j&&j.ok) setTimeout(load, 700); return; }
''', "the Sunday buttons' handler")
    return s


# ---------------------------------------------------------------- stock_loss.html
LOSS_JS = r'''/* ---- S428 (D633): the watch card -- the full count's Sunday, the mornings' rosters, 'Count this', the close-watch list,
   the traces, tap vs bill, this month's leakage -- and the second settings heading 'Counts & watch'. ---- */
let WSUGG=[];
function pointsHtml(pts){ return pts.length?pts.map(p=>esc(p.at_text)+' '+esc(p.qty_text)+(p.gap_text?' ('+esc(p.gap_text)+')':'')).join(' · '):'no count yet'; }
function watchCard(){
  const W=D.watch; if(!W) return '';
  if(W.ok===false) return '<section class="card"><h2>Counts &amp; watch</h2><div class="err">'+esc(W.note||'could not be read')+'</div></section>';
  const P=W.plan||{}, pl=P.plan, m=MSG.watch?'<span class="msg'+(MSG.watch.ok?'':' bad')+'">'+MSG.watch.html+'</span>':'<span class="msg"></span>';
  let h='<section class="card" id="watch"><h2>Counts &amp; watch</h2>';
  h+='<div class="grp"><span>Full count</span><span>every '+esc(P.cadence_months)+' month'+(String(P.cadence_months)==="1"?'':'s')+'</span></div>';
  h+='<div class="lead">'+(P.last?'Last closed full count: '+esc(dash(P.last.as_on.split("-").reverse().join("-")))+'. ':'No closed full count yet. ')
    +(pl?('<b>Due</b> (from '+esc(pl.due_from.split("-").reverse().join("-"))+'): '+(pl.status==="confirmed"?'Sunday <b>'+esc(pl.sunday_text)+'</b> — Amir picked, Darpan said yes.':(pl.status==="picked"?'Amir picked '+esc(pl.sunday_text)+' — Darpan\'s yes pending.':'Amir picks a Sunday on his board ('+pl.window_text.join(', ')+').')))
      :('Next due from <b>'+esc(P.due_from.split("-").reverse().join("-"))+'</b>. Sundays only; Amir picks, Darpan confirms.'))+'</div>';
  h+='<div class="grp"><span>Spot counts</span><span>'+esc((W.spot_days||[]).map(d=>d[0]+d.slice(1).toLowerCase()).join(", "))+' · up to '+W.cap+' items</span></div>';
  const R=W.roster_today||{items:[]};
  if(R.items.length) h+='<div class="lead"><b>Today ('+esc(R.day_text)+'):</b> '+R.items.map(r=>esc(r.item)+(r.answered_at?' — Darpan: '+esc(rs(0)).slice(0,0)+esc(r.qty_hi)+(r.gap!=null?(r.gap<0?' (short)':(r.gap>0?' (over)':' (= records)')):''):' — not yet')).join(' · ')+'</div>';
  else h+='<div class="lead"><b>Today:</b> '+(R.is_spot_day?'no list yet':'not a spot morning')+'.</div>';
  if(W.next_day) h+='<div class="lead"><b>Next morning ('+esc(W.next_day_text)+'):</b> '+((W.roster_next||[]).length?W.roster_next.map(r=>esc(r.item)+' <span class="sub">('+esc(dash(r.reason))+')</span>').join(' · '):'nothing yet')+'</div>';
  h+='<div class="lead">Count this — any item, at the head of Darpan\'s next list:</div><div class="row" style="display:flex;gap:8px;flex-wrap:wrap"><input id="watch_q" placeholder="Search an item" autocomplete="off" style="font:inherit;font-size:15px;padding:7px 9px;border-radius:9px;border:1.5px solid var(--line);background:var(--surface);color:var(--ink);min-height:40px;width:16em;max-width:100%"></div>'
    +'<div class="chips" id="watch_sugg">'+WSUGG.map(n=>'<button class="chip add" data-ask="'+esc(n)+'">+ '+esc(n)+'</button>').join("")+'</div>'
    +((W.asks||[]).length?'<div class="sub">Asked: '+W.asks.map(a=>esc(a.item)).join(', ')+'</div>':'')+m;
  const L=W.leak, LP=W.leak_prev;
  h+='<div class="grp"><span>Leakage</span><span>budget '+esc(L?L.budget_pct:'')+'%</span></div>';
  h+='<div class="lead">'+(L?'<b style="color:'+(L.red?'var(--diff)':'var(--ok)')+'">'+esc(L.text)+'</b>':'—')+(LP&&LP.pct!=null?' · previous month: '+esc(LP.text):'')+'</div>';
  const T=W.traces||[];
  h+='<div class="grp"><span>Traces</span><span>'+T.length+'</span></div>';
  if(!T.length) h+='<div class="none">No trace yet — one opens on every Big-loss line and on every flag.</div>';
  T.slice(0,12).forEach(t=>{ h+='<div class="li"><div><div class="n">'+esc(t.item)+' <span class="tag'+(t.verdict==="explained"?' ok':'')+'">'+esc(t.verdict_text)+'</span></div><div class="q">'+esc(t.gap_text)+' · '+esc(t.window_text)+' · from '+esc(dash(t.anchor_text))+'</div></div><div class="v" style="color:var(--muted);font-weight:400;font-size:12.5px">'+esc(t.opened_text)+'</div>'
    +'<div class="w">'+t.findings.filter(f=>!f.ok||f.explains).map(f=>esc(dash(f.text))).join(' · ')+(t.fix?' — <b>Amir: '+esc(t.fix)+'</b>':'')+'</div></div>'; });
  const V=W.tap_vs_bill||[];
  if(V.length) h+='<div class="grp"><span>Tap vs bill</span><span>'+V.length+'</span></div>'+V.map(x=>'<div class="rl">'+esc(x.text)+' · '+esc(x.vendor)+' · '+esc(x.at_text)+'</div>').join("");
  const WL=W.watch||[];
  h+='<div class="grp"><span>Close-watch list</span><span>'+WL.length+'</span></div>';
  WL.slice(0,W.cap>0?60:60).forEach(x=>{ h+='<div class="li"><div><div class="n">'+esc(x.item)+'</div><div class="q">'+esc(x.why)+' · '+x.trend.map(tr=>esc(tr.label)+' sold '+esc(tr.sold)+(tr.lost?', lost '+esc(tr.lost):'')).join(' · ')+'</div></div><div class="v" style="color:var(--muted);font-weight:400;font-size:12.5px">'+esc(pointsHtml(x.points))+'</div><div class="act"><button class="s" data-count="'+esc(x.item)+'">Count this</button></div></div>'; });
  const N=W.notices||[];
  if(N.length) h+='<div class="grp"><span>Lines</span><span></span></div>'+N.slice(0,8).map(n=>'<div class="rl">'+esc(n.at_text)+' · '+esc(n.text)+'</div>').join("");
  return h+'</section>';
}
function watchSettings(){
  const W=D.watch; if(!W||!W.settings) return '';
  let h='<div class="grp" style="margin-top:18px"><span>Counts &amp; watch</span><span>S428</span></div><p class="lead">Sunday full counts, the mornings\' spot counts, arrivals, the trace and the leakage budget. In strips words; every change recorded.</p>';
  W.settings.forEach(s=>{
    let c;
    if(s.kind==="choice") c='<select id="set_'+esc(s.key)+'">'+s.choices.map(o=>'<option value="'+esc(o.v)+'"'+(String(s.value)===o.v?' selected':'')+'>'+esc(o.t)+'</option>').join("")+'</select>';
    else if(s.kind==="rupees") c='<input id="set_'+esc(s.key)+'" inputmode="numeric" placeholder="rupees" value="'+(s.rupees==null?'':s.rupees)+'" aria-label="'+esc(s.label)+' in rupees">';
    else c='<input id="set_'+esc(s.key)+'" value="'+esc(s.value)+'" aria-label="'+esc(s.label)+'">';
    h+='<div class="set"><div><b>'+esc(s.label)+'</b> — <span class="sub">now: '+esc(s.shown)+'</span></div><div class="h">'+esc(dash(s.hint))+'</div><div class="row">'+c+'<button class="s" data-save="'+esc(s.key)+'">Save</button></div></div>';
  });
  return h;
}
let WQT=null;
document.addEventListener("input", e=>{
  if(e.target.id!=="watch_q") return;
  const q=e.target.value.trim(); clearTimeout(WQT);
  if(q.length<2){ WSUGG=[]; const s=document.getElementById("watch_sugg"); if(s) s.innerHTML=""; return; }
  WQT=setTimeout(async()=>{ const r=await fetch(BASE+"/api/loss/"+D.count_id+"/items?q="+encodeURIComponent(q),{cache:"no-store"}).catch(()=>null); const j=r?await r.json().catch(()=>null):null;
    WSUGG=(j&&j.ok)?j.items:[]; const s=document.getElementById("watch_sugg"); if(s) s.innerHTML=WSUGG.map(n=>'<button class="chip add" data-ask="'+esc(n)+'">+ '+esc(n)+'</button>').join(""); },250);
});
'''


def build_loss(s):
    s = rep(s, "  act+=moveMenu(l);\n", '''  act+='<button class="s" data-count="'+esc(l.item)+'">Count this</button>';   // S428
  act+=moveMenu(l);
''', "Count this on every line")
    s = rep(s, "  h+=closeCard();\n", "  h+=closeCard()+watchCard();                                  // S428: the watch card\n", "the watch card")
    s = rep(s, "  return h+(MSG.settings?'<span class=\"msg'+(MSG.settings.ok?'':' bad')+'\">'+MSG.settings.html+'</span>':'')+'</details>';\n",
            "  h+=watchSettings();                                          // S428: the second heading\n  return h+(MSG.settings?'<span class=\"msg'+(MSG.settings.ok?'':' bad')+'\">'+MSG.settings.html+'</span>':'')+'</details>';\n", "the second settings heading")
    s = rep(s, "function render(){\n", LOSS_JS + "function render(){\n", "the watch JS")
    s = rep(s, '''  const sv=t.closest("[data-save]");
''', '''  const ct=t.closest("[data-count],[data-ask]");                // S428: Count this
  if(ct){ BUSY=true; const j=await post(BASE+"/api/watch/ask",{item:ct.getAttribute("data-count")||ct.getAttribute("data-ask")}); BUSY=false; WSUGG=[]; const qi=document.getElementById("watch_q"); if(qi) qi.value="";
    MSG={watch:{ok:!!(j&&j.ok),html:esc((j&&j.message)||"The server did not answer.")}}; load(true); return; }
  const sv=t.closest("[data-save]");
''', "the Count this handler")
    s = rep(s, '''  const qv=(document.getElementById("consume_q")||{}).value||"";
''', '''  const qv=(document.getElementById("consume_q")||{}).value||"";
  const wv=(document.getElementById("watch_q")||{}).value||"";   // S428
''', "keep the watch query (1)")
    s = rep(s, '''  const qi=document.getElementById("consume_q"); if(qi&&qv){ qi.value=qv; }
''', '''  const qi=document.getElementById("consume_q"); if(qi&&qv){ qi.value=qv; }
  const wi=document.getElementById("watch_q"); if(wi&&wv){ wi.value=wv; }   // S428
''', "keep the watch query (2)")
    return s


# ---------------------------------------------------------------- sanjeevni_approvals.py
def build_approvals(s):
    s = rep(s, 'VERSION = "1.10"\n', 'VERSION = "1.11"\n', "VERSION")
    s = rep(s, "#  v1.10 (S410, D626, 26-Sep-2026): Needs you gains order_rules' lines",
            "#  v1.11 (S428, D633, 27-Sep-2026): the Month section gains the leakage line (stock_watch.month_leak, fail-soft); Needs you gains\n"
            "#  the stock watch's lines -- the confirmed count Sunday, a cadence move, an unexplained trace, missed mornings, red leakage months.\n"
            "#  v1.10 (S410, D626, 26-Sep-2026): Needs you gains order_rules' lines", "the header")
    s = rep(s, '''    return dict(ok=True, months=out)
''', '''    # S428 (D633): the month's leakage line -- loss points + count write-offs at cost against the month's sales (fail-soft)
    try:
        import stock_watch  # noqa: PLC0415
        for row in out:
            row["leak"] = stock_watch.month_leak(con, row["ym"])
    except Exception:  # noqa: BLE001
        for row in out:
            row["leak"] = None
    return dict(ok=True, months=out)
''', "the Month section's leakage line")
    s = rep(s, '''    # 7 · the statement's age (a word, not a fault)
''', '''    # 14 · S428 (D633): the stock watch -- the confirmed count Sunday, a cadence move, an unexplained trace, missed mornings,
    #      red leakage months running (fail-soft). NEEDS_YOU_WITHOUT_S428=1 is set ONLY by an older kit's frozen walk re-run.
    if os.environ.get("NEEDS_YOU_WITHOUT_S428") != "1":
        try:
            import stock_watch  # noqa: PLC0415
            lines.extend(stock_watch.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 7 · the statement's age (a word, not a fault)
''', "Needs you block 14")
    return s


# ---------------------------------------------------------------- finance_ui/finance_approvals.html (PARENT'S -- one anchored line)
def build_approvals_html(s):
    s = rep(s, '''         '<br>'+esc(m.marg_note)+(m.marg!=null?' — ₹'+esc(m.marg):'')+'</div></td></tr>';
''', '''         '<br>'+esc(m.marg_note)+(m.marg!=null?' — ₹'+esc(m.marg):'')+(m.leak&&m.leak.text?'<br><b style="color:'+(m.leak.red?'#8C3A2B':'#0E5C58')+'">'+esc(m.leak.text)+'</b>':'')+'</div></td></tr>';   /* S428: leakage vs budget */
''', "the leakage line under a month")
    return s


# ---------------------------------------------------------------- packs_checklist.html (one anchored line)
def build_checklist(s):
    s = rep(s, '''    var h='<div class="mut">'+(open?('<span class="open">'+open+' kaam baaki</span>'):'<span class="ok">sab ho gaya ✓</span>')+'</div>';
''', '''    var h='<div class="mut">'+(open?('<span class="open">'+open+' kaam baaki</span>'):'<span class="ok">sab ho gaya ✓</span>')+'</div><div id="plan428"></div>';
    fetch("/finance/stock/api/watch/plan/line?_="+Date.now(),{cache:"no-store"}).then(function(r){return r.json()}).then(function(p){if(p&&p.ok&&p.text_hi){var e=document.getElementById("plan428");if(e)e.innerHTML='<div class="row"><div>'+esc(p.text_hi)+'</div><div class="ok">system</div></div>'}}).catch(function(){});   /* S428: the full count's Sunday */
''', "the count Sunday on Shavez's checklist")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = {name: load(os.path.join(a.finance, name), name) for name in FROM}
    out = {
        "stock_app.py": build_stock_app(src["stock_app.py"]),
        "stockmatch.py": build_stockmatch_py(src["stockmatch.py"]),
        "stockmatch.html": build_stockmatch_html(src["stockmatch.html"]),
        "stock_amir.html": build_amir(src["stock_amir.html"]),
        "stock_loss.html": build_loss(src["stock_loss.html"]),
        "sanjeevni_approvals.py": build_approvals(src["sanjeevni_approvals.py"]),
        "finance_approvals.html": build_approvals_html(src["finance_ui/finance_approvals.html"]),
        "packs_checklist.html": build_checklist(src["packs_checklist.html"]),
    }
    os.makedirs(a.out, exist_ok=True)
    for name, text in out.items():
        b = text.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s" % (md5(b), name))


if __name__ == "__main__":
    main()
