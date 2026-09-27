#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s418.py -- builds the patched live files of kit S418_LOSS_DESK_PILES from the LIVE bytes by anchored edits.
Every anchor must occur exactly once, and every source must be at its FROM pin, or the build stops with nothing
written. Nothing is re-typed. (stock_loss.html is a whole-page replacement shipped in the kit; loss_piles.py is new.)

  stock_app.py     loss_piles imported defensively; the shelf layer laid over the report (apply_fixes); the voucher
                   round takes an item filter (the write-off pile's lines only); the batch size reads the desk's
                   'stock.voucher_batch' first; the hub and the report carry THE five totals (loss_piles.totals);
                   the desk's routes: /api/loss/<cid>/piles, /pile/move, /pile/accept, /pile/writeoff (arm + confirm),
                   /pile/pursue (then the existing S228 sheet, unchanged), /pile/recount, /pile/setting, /record.pdf
  stock_hub.html   a status card with the five totals and the links; steps 3-5 (cut the list, type the answers, the
                   decision desk) leave the owner's path -- one step 'The Loss desk' in their place; the rest renumbered
  stockmatch.py    Darpan's Stock milaan also carries 'Phir se gino' (the recount box) and 'Bina bill?' (the pursue
                   answers, the claim queue's own door); two routes
  stockmatch.html  the two cards

Usage: make_s418.py --finance /root/finance --out DIR      (writes the four files flat into DIR, prints each md5)
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_app.py": "586ae78ae6437f806692c2a1e4eeeb37",
    "stock_hub.html": "68d11419e7fb9a8e5fec74095b60b255",
    "stockmatch.py": "d37c674b6b7435966f048503c40622df",
    "stockmatch.html": "c5db7067fc18cf9a6bd29c48f4c1540d",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


# ---------------------------------------------------------------- stock_app.py
ROUTES = r'''

# ---- S418_LOSS_DESK_PILES begin (D631 / F-641) ----------------------------------
# The Loss desk as FOUR PILES (loss_piles.py). The page stays /page/loss (page_loss, above, unchanged); these are
# its doors. The owner's only -- the checker -- except Accept back, which the setting 'stock.accept_back_by' may
# widen to Darpan. Every tap writes the same rows the older doors write (the lane word + the S221 decision), and
# the sheet for Darpan IS the S228 sheet (api_loss_share, unchanged).
def _desk_totals_safe(con, d):
    """THE five totals, for the hub and the report -- loss_piles.totals, the function the desk itself prints."""
    if not LOSS_PILES_OK:
        return dict(ok=False, note="loss_piles.py is not beside stock_app.py")
    try:
        return dict(ok=True, **_lp.totals(con, d))
    except Exception as e:                                     # noqa: BLE001 -- a total is never worth a broken hub
        return dict(ok=False, note="The desk's totals could not be read: %s" % str(e)[:160])


def _desk_gate(roles=("checker",)):
    u, err = _require(*roles)
    if err:
        return None, None, err
    if not LOSS_PILES_OK:
        return None, None, (jsonify(ok=False, error="unavailable", message="loss_piles.py is not beside stock_app.py"), 503)
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    _loss_ensure(con)
    _voucher_ensure(con)
    _lp.ensure(con)
    return u, con, None


def _desk_owner_only(u):
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    return None


@bp.route("/api/loss/<int:cid>/piles")
def api_loss_piles(cid):
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    out = _lp.desk(con, d, (u or {}).get("user") or "")
    return jsonify(ok=True, you=dict(user=(u or {}).get("user") or ""), **out)


def _desk_root(con, cid):
    root, _fam, R = _pad_family(con, cid)
    return (root if R is not None else None)


@bp.route("/api/loss/<int:cid>/pile/move", methods=["POST"])
def api_loss_pile_move(cid):
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
    ok, msg, code = _lp.move(con, root, str(b.get("item") or "").strip(), str(b.get("pile") or "").strip(), (u or {}).get("user") or "")
    return jsonify(ok=ok, message=msg), code


@bp.route("/api/loss/<int:cid>/pile/accept", methods=["POST"])
def api_loss_pile_accept(cid):
    u, con, err = _desk_gate(("checker", "maker", "viewer"))
    if err:
        return err
    who = (u or {}).get("user") or ""
    if not (_may_decide(u) or (who and who in _lp.settings(con)["accept_back_by"])):
        return jsonify(ok=False, error="forbidden", message="Only the owner accepts a line back (setting: who may tap Accept back)."), 403
    b = request.get_json(silent=True) or {}
    items = [str(i).strip() for i in (b.get("items") or ([b.get("item")] if b.get("item") else [])) if str(i or "").strip()]
    if not items:
        return jsonify(ok=False, error="empty", message="No item named."), 400
    root = _desk_root(con, cid)
    if root is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    ok, msg, code, n = _lp.accept(con, root, items[:200], who)
    return jsonify(ok=ok, message=msg, accepted=n), code


@bp.route("/api/loss/<int:cid>/pile/writeoff", methods=["POST"])
def api_loss_pile_writeoff(cid):
    """First tap: {} -> arms for loss_piles.ARM_SECONDS and returns a token. Second tap: {token} -> writes the pile off."""
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
        ok, msg, code, armed = _lp.arm(con, root, who)
        return jsonify(ok=ok, message=msg, arm=armed), code
    ok, msg, code, done = _lp.writeoff(con, root, b.get("token"), who)
    return jsonify(ok=ok, message=msg, done=done), code


@bp.route("/api/loss/<int:cid>/pile/pursue", methods=["POST"])
def api_loss_pile_pursue(cid):
    """Every Pursue line not yet on a sheet: RECOVER (open) + the tick; then the S228 sheet itself (api_loss_share)."""
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    root = _desk_root(con, cid)
    if root is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    n = _lp.pursue_prepare(con, root, (u or {}).get("user") or "")
    if not n:
        return jsonify(ok=False, error="empty", message="Every Pursue line is already on a sheet with Darpan."), 400
    resp = api_loss_share(root)
    try:                                                       # the claim queue follows the words at once (the hub does the same on read)
        d2 = _pad_report_data(con, root)
        if d2 is not None:
            _pursue_block(con, d2, d2["totals"])
    except Exception:                                          # noqa: BLE001 -- the sheet is made; the hub syncs on its next read
        pass
    return resp


@bp.route("/api/loss/<int:cid>/pile/recount", methods=["POST"])
def api_loss_pile_recount(cid):
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    root = _desk_root(con, cid)
    if root is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    ok, msg, code, n = _lp.recount_ask(con, root, (u or {}).get("user") or "")
    return jsonify(ok=ok, message=msg, asked=n), code


@bp.route("/api/loss/<int:cid>/pile/setting", methods=["POST"])
def api_loss_pile_setting(cid):
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = _desk_root(con, cid) or 0
    ok, msg = _lp.set_setting(con, str(b.get("key") or "").strip(), b.get("value"), (u or {}).get("user") or "", root)
    return jsonify(ok=ok, message=msg), (200 if ok else 400)


@bp.route("/api/loss/<int:cid>/record.pdf")
def api_loss_record_pdf(cid):
    """The count's record: the five totals, the rules in force, every written-off group item by item, back in store,
    to pursue, to recount, and every change of a rule."""
    u, con, err = _desk_gate()
    if err:
        return err
    err = _desk_owner_only(u)
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    pdf = _lp.record_pdf(con, d)
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="LOSS_DESK_RECORD_count%d.pdf"' % d["count_id"],
                             "Cache-Control": "no-store"})
# ---- S418_LOSS_DESK_PILES end ---------------------------------------------------
'''


def build_stock_app(s):
    s = rep(s, '''# --- S313_SECTION_MAP end ------------------------------------------------
''', '''# --- S313_SECTION_MAP end ------------------------------------------------

# --- S418_LOSS_DESK_PILES begin (D631) -------------------------------------
# The owner's Loss desk as four piles, the shelf layer and THE five totals live beside this file. Defensive, like
# the two above: without it the report, the hub and every older page behave exactly as before S418.
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import loss_piles as _lp                               # noqa: PLC0415
    LOSS_PILES_OK = True
except Exception:                                          # pragma: no cover
    _lp = None
    LOSS_PILES_OK = False
# --- S418_LOSS_DESK_PILES end ----------------------------------------------
''', "import loss_piles")
    s = rep(s, '''    matches = _match_apply(con, _root, diffs, pairs, words)   # S299 TRY TO MATCH: his Yes takes the units off both lines
''', '''    matches = _match_apply(con, _root, diffs, pairs, words)   # S299 TRY TO MATCH: his Yes takes the units off both lines
    if LOSS_PILES_OK:
        _lp.apply_fixes(con, _root, diffs)                    # S418: the shelf layer -- Accept back (= Marg's figure) and Darpan's recount, at read time
''', "the shelf layer")
    s = rep(s, "def _voucher_pending(con, d, section=None):\n",
            "def _voucher_pending(con, d, section=None, items=None):\n", "_voucher_pending signature")
    s = rep(s, '''        if section and _item_section(con, x) != section:      # S404: a section round carries that section's lines only
            continue
''', '''        if section and _item_section(con, x) != section:      # S404: a section round carries that section's lines only
            continue
        if items is not None and item not in items:            # S418: the write-off pile's round carries those lines only
            continue
''', "_voucher_pending items filter")
    s = rep(s, "def _voucher_make(con, d, user, section=None):\n",
            "def _voucher_make(con, d, user, section=None, items=None):\n", "_voucher_make signature")
    s = rep(s, "        pend = _voucher_pending(con, d, section)\n",
            "        pend = _voucher_pending(con, d, section, items)\n", "_voucher_make passes items")
    s = rep(s, '''        return max(1, min(8, int(_stock_setting(con, "stock.voucher_lines", 6))))
''', '''        return max(1, min(8, int(_stock_setting(con, "stock.voucher_batch", _stock_setting(con, "stock.voucher_lines", 6)))))   # S418: the desk's setting first
''', "_voucher_batch_size")
    s = rep(s, '''                ortho=_ortho_section_safe(con, d),   # S404: the orthotic section -- Darpan's answers, the orthotic round, the verdict
''', '''                ortho=_ortho_section_safe(con, d),   # S404: the orthotic section -- Darpan's answers, the orthotic round, the verdict
                desk=_desk_totals_safe(con, d),      # S418 (F-641): THE five totals -- the same function the desk and the record print
''', "hub desk totals")
    s = rep(s, '''    d["you"] = dict(user=(u or {}).get("user") or "", checker=_has_role(u, "checker"))
''', '''    d["you"] = dict(user=(u or {}).get("user") or "", checker=_has_role(u, "checker"))
    d["desk"] = _desk_totals_safe(con, d)                      # S418 (F-641): the report reads the same five totals
''', "report desk totals")
    s = rep(s, '''# ---- end S228 LOSS DESK -------------------------------------------------------
''', ROUTES.lstrip("\n") + '''# ---- end S228 LOSS DESK -------------------------------------------------------
''', "the desk's routes")
    return s


# ---------------------------------------------------------------- stock_hub.html
HUB_CARD = r'''
/* ---- S418_LOSS_DESK_PILES (D631, F-641): the hub is a status card with links. The five totals are the server's
   (loss_piles.totals) -- the very figures the Loss desk and its record print. ---- */
function rsx(p){ if(p==null) return "-"; const neg=p<0; let n=Math.abs(Math.round(p)); const paise=n%100; n=Math.floor(n/100);
  let s=String(n); if(s.length>3){ let head=s.slice(0,-3), tail=s.slice(-3), parts=[]; while(head.length>2){parts.unshift(head.slice(-2));head=head.slice(0,-2);} if(head)parts.unshift(head); s=parts.join(",")+","+tail; }
  return (neg?"-":"")+"Rs "+s+(paise?"."+String(paise).padStart(2,"0"):""); }
function deskFigs(T){
  const c=(k,t)=>'<div><div class="k">'+k+'</div><div class="v">'+rsx(t.mrp_p)+'</div><div class="sub">'+t.n+' line'+(t.n===1?'':'s')+' · cost '+rsx(t.cost_p)+'</div></div>';
  const G=T.written_off.groups||{}, g=[["allowance","within the allowance"],["small","small real gap"],["consume","clinic consumption"],["owner","your choice"],["earlier","before the piles"]]
    .filter(x=>G[x[0]]&&G[x[0]].n).map(x=>x[1]+' '+G[x[0]].n+' · '+rsx(G[x[0]].mrp_p));
  return '<div class="bridge">'+c("Still open",T.open)+c("Back in store",T.back)+c("Written off",T.written_off)+'</div>'
    +'<div class="bridge">'+c("To pursue",T.pursue)+c("Recount",T.recount)+c("With you + write-off pile",{n:T.with_me.n+T.writeoff.n,mrp_p:T.with_me.mrp_p+T.writeoff.mrp_p,cost_p:T.with_me.cost_p+T.writeoff.cost_p})+'</div>'
    +(g.length?'<div class="sub">Written off, by group: '+g.map(esc).join(' · ')+'</div>':'')
    +'<div class="sub">Short at the count: <b>'+rsx(T.short.mrp_p)+'</b> · '+T.short.n+' lines (medicines and consumables; the orthotics are closed on their own section below).</div>';
}
function deskCard(K, L){
  if(!K||K.ok===false) return '<div class="facts"><b>The Loss desk</b> — <span class="err">'+esc((K&&K.note)||'its totals could not be read')+'</span><div class="links"><a class="b main" href="'+esc(L.loss)+'">Open the Loss desk</a></div></div>';
  return '<div class="facts"><b>Where the count stands</b> — the same five figures as your Loss desk.'+deskFigs(K)
    +'<div class="links"><a class="b main" href="'+esc(L.loss)+'">Open the Loss desk — four piles</a><a class="b" href="'+esc(L.loss_record)+'" target="_blank" rel="noopener">The record (PDF)</a><a class="b" href="'+esc(L.amir)+'">Amir\'s board</a><a class="b" href="/finance/stockmatch">Darpan\'s Stock milaan</a></div></div>';
}
'''


def build_hub(s):
    s = rep(s, '''  // 1 -- the count
  h+=step(1,"done",''', '''  L.loss_record=L.loss.replace("/page/loss?count=","/api/loss/").replace(/$/,"/record.pdf");   // S418
  h+=deskCard(d.desk, L);                                                                            // S418: the status card
  // 1 -- the count
  h+=step(1,"done",''', "status card")
    a = s.index("  // 3 -- Darpan's list\n")
    b_anchor = '''    +'<div class="links"><a class="b main" href="'+esc(L.desk)+'">Decision desk</a><a class="b" href="'+esc(L.loss)+'">Loss desk</a></div>');
'''
    if s.count("  // 3 -- Darpan's list\n") != 1 or s.count(b_anchor) != 1:
        sys.exit("REFUSED: the hub's steps 3-5 block is not where it was")
    b = s.index(b_anchor) + len(b_anchor)
    new_mid = '''  // 3 -- S418: the Loss desk (steps 3-5 -- cut the list, type the answers, the decision desk -- left the owner's path; their routes stay)
  const K=d.desk||{};
  h+=step(3,(K.ok===false?"wait":((K.open&&K.open.n)?"now":"done")),"The Loss desk — four piles",
    (K.ok===false?esc(K.note||""):('<b>'+((K.open&&K.open.n)||0)+'</b> line'+(((K.open&&K.open.n)===1)?'':'s')+' still open: with you '+K.with_me.n+' · write-off pile '+K.writeoff.n+' · to pursue '+K.pursue.n+' · recount '+K.recount.n+'. ')
      +'Accept back what you have, write off the normal loss as a group, pursue the real gaps, recount what cannot be right.'),
    '<div class="links"><a class="b main" href="'+esc(L.loss)+'">Open the Loss desk</a></div>');
'''
    s = s[:a] + new_mid + s[b:]
    s = rep(s, "puts both on the Marg vouchers at once — step 6.", "puts both on the Marg vouchers at once — step 4.", "step 2's pointer to the vouchers")
    s = rep(s, "  h+=step(6,V.state,", "  h+=step(4,V.state,", "step 6 -> 4")
    s = rep(s, '  h+=step(7,P.state||"wait",', '  h+=step(5,P.state||"wait",', "step 7 -> 5")
    s = rep(s, "  h+=step(8,d.pursue.state,", "  h+=step(6,d.pursue.state,", "step 8 -> 6")
    s = rep(s, '''async function post(url, body){
''', HUB_CARD.lstrip("\n") + '''
async function post(url, body){
''', "hub helpers")
    return s


# ---------------------------------------------------------------- stockmatch.py
SM_ROUTES = r'''


# ------------------------------------------------------------------ S418 (D631): the recount box and the pursue answers
def _lp():
    import loss_piles                                         # noqa: PLC0415 -- beside this file
    return loss_piles


def _s418_extra(con, root):
    """'Phir se gino' (the items the owner asked to be counted again -- blind: no Marg figure, no first count) and
    'Bina bill?' (the live claims of the round, the claim queue's own answers). Never raises."""
    out = dict(recounts=[], claims=[], claim_answers=[])
    try:
        out["recounts"] = _lp().recount_list(con, root)
    except Exception:                                          # noqa: BLE001
        pass
    try:
        sa = _sa()
        if getattr(sa, "CLAIM_QUEUE_OK", False):
            cq = sa._cq
            out["claims"] = [dict(id=c["id"], item=c["item"], state=c["state"], answer=c["answer"], answer_hi=c["answer_label"],
                                  short_qty=c["short_qty"], value_p=c["value_p"])
                             for c in cq.lines(con, root, limit=200) if c["state"] != "settled"]
            out["claim_answers"] = [dict(key=k, hi=v) for k, v in cq.ANSWERS.items()]
    except Exception:                                          # noqa: BLE001
        pass
    return out


@bp.route("/finance/stockmatch/api/recount", methods=["POST"])
def api_recount():
    """Phir se gino: {item, strips, loose} or {item, units}. His figure replaces the shelf; the owner's desk re-piles."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = root_of(con, _cid())
    item = str(b.get("item") or "").strip()
    rl = {r["item"]: r for r in _lp().recount_list(con, root)}
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
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    d = report(con, root)
    st = _state_for(con, d, u, kind)
    st.update(saved=dict(kind="recount", item=item, qty=q, message=msg), round_made=None)
    return jsonify(**st)


@bp.route("/finance/stockmatch/api/claim", methods=["POST"])
def api_claim():
    """Bina bill?: {id, answer} -- the claim queue's own answer door (open -> contacted), audited. The owner settles."""
    u, con, kind, err = _auth()
    if err:
        return err
    sa = _sa()
    if not getattr(sa, "CLAIM_QUEUE_OK", False):
        return jsonify(ok=False, error="unavailable", message="Claim queue nahi mili."), 503
    b = request.get_json(silent=True) or {}
    try:
        cid_ = int(b.get("id") or 0)
    except (TypeError, ValueError):
        cid_ = 0
    ans = str(b.get("answer") or "").strip()
    root = root_of(con, _cid())
    mine = {c["id"]: c for c in _s418_extra(con, root)["claims"]}
    if cid_ not in mine:
        return jsonify(ok=False, error="not_found", message="Yeh line ab poochne ki list mein nahi hai."), 404
    ok, msg = sa._cq.answer(con, cid_, ans, "", (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="bad_request", message=msg), 400
    at = now_iso()
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("claim_line", cid_, "claim_answered", json.dumps(dict(answer=mine[cid_]["answer"])),
                     json.dumps(dict(answer=ans, item=mine[cid_]["item"], via="stockmatch")), (u or {}).get("user") or "", at))
    except sqlite3.Error:
        pass
    con.commit()
    d = report(con, root)
    st = _state_for(con, d, u, kind)
    st.update(saved=dict(kind="claim", item=mine[cid_]["item"], answer=ans, hi=sa._cq.ANSWERS.get(ans, ans)), round_made=None)
    return jsonify(**st)
'''


def build_stockmatch_py(s):
    s = rep(s, '''    st.update(me=kind, user=me)
    return st
''', '''    st.update(me=kind, user=me)
    st.update(_s418_extra(con, d["count_id"]))                # S418: Phir se gino + Bina bill? (medicines too)
    return st
''', "_state_for extra")
    s = s.rstrip("\n") + "\n" + SM_ROUTES
    return s


SM_JS = r'''
/* ---- S418 (D631): Phir se gino (count the item again -- no Marg figure is shown, count what is on the shelf) and
   Bina bill? (the lines the doctor is pursuing -- one answer each). ---- */
function s418Cards(s){
 let h='';
 const R=s.recounts||[], open=R.filter(r=>!r.done);
 h+='<div class="card"><h2>Phir se gino <span class="tag">'+open.length+'</span></h2><div class="muted">Doctor sahab ne yeh item dobara ginne ko kaha hai. Shelf par jitna hai utna likhiye.</div>';
 if(!R.length) h+='<div class="empty">Abhi kuch ginna nahi hai.</div>';
 R.forEach((r,i)=>{
  h+='<div class="line'+(r.done?' done':'')+'"><div class="nm">'+esc(r.item)+'</div><div class="muted">'+esc(r.packing||'')+(r.pack>1?' &middot; ek patte mein '+r.pack:'')+'</div>';
  if(r.done) h+='<div class="ans">Aapne gina: '+esc(r.qty_text)+' <span class="muted">('+esc(r.at_text)+')</span></div>';
  if(!r.done||r.fix){
   h+='<div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+(r.pack>1?'<label>Patte <input id="rs'+i+'" inputmode="numeric" style="width:5em;font-size:17px;padding:8px"></label> <label>Goli <input id="rl'+i+'" inputmode="numeric" style="width:5em;font-size:17px;padding:8px"></label>'
     :'<label>Pieces <input id="rl'+i+'" inputmode="numeric" style="width:6em;font-size:17px;padding:8px"></label>')+'<span class="btn ok" onclick="recount('+i+')">Likh do</span></div>';
  } else h+='<div><span class="muted" style="cursor:pointer;text-decoration:underline" onclick="S.recounts['+i+'].fix=1;render()">badalna hai?</span></div>';
  h+='</div>';
 });
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
async function recount(i){
 if(BUSY)return; const r=S.recounts[i]; const a=el("rs"+i), b=el("rl"+i);
 const body={item:r.item}; if(r.pack>1){body.strips=(a&&a.value)||0;body.loose=(b&&b.value)||0;} else {body.units=(b&&b.value)||"";}
 if(r.pack<=1&&String(body.units).trim()===""){MSG={kind:"err",title:"Ginti likhiye",lines:[esc(r.item)]};render();return;}
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/recount"+Q,body); after(j,"✓ Save ho gaya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function claim(id,key){
 if(BUSY)return; BUSY=true;
 try{const j=await post("/finance/stockmatch/api/claim"+Q,{id:id,answer:key}); after(j,"✓ Save ho gaya",["<b>"+esc(j.saved.item)+"</b>","Jawab: <b>"+esc(j.saved.hi)+"</b>"]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
'''


def build_stockmatch_html(s):
    s = rep(s, "<h1>Stock milaan &mdash; Orthotics</h1>\n", "<h1>Stock milaan</h1>\n", "h1")
    s = rep(s, '''" · sirf orthotics · round "''', '''" · phir se gino · bina bill · orthotics · round "''', "subtitle")
    s = rep(s, ''' const s=S; let h=msgHtml();
''', ''' const s=S; let h=msgHtml();
 h+=s418Cards(s);                                            // S418: Phir se gino + Bina bill?
''', "render hook")
    s = rep(s, '''function after(j,title,lines){
''', SM_JS.lstrip("\n") + '''function after(j,title,lines){
''', "s418 js")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = {
        "stock_app.py": load(os.path.join(a.finance, "stock_app.py"), "stock_app.py"),
        "stock_hub.html": load(os.path.join(a.finance, "stock_hub.html"), "stock_hub.html"),
        "stockmatch.py": load(os.path.join(a.finance, "stockmatch.py"), "stockmatch.py"),
        "stockmatch.html": load(os.path.join(a.finance, "stockmatch.html"), "stockmatch.html"),
    }
    out = {
        "stock_app.py": build_stock_app(src["stock_app.py"]),
        "stock_hub.html": build_hub(src["stock_hub.html"]),
        "stockmatch.py": build_stockmatch_py(src["stockmatch.py"]),
        "stockmatch.html": build_stockmatch_html(src["stockmatch.html"]),
    }
    os.makedirs(a.out, exist_ok=True)
    for name, text in out.items():
        b = text.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("%s  %s" % (md5(b), name))


if __name__ == "__main__":
    main()
