#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s406.py -- builds the three patched live files of kit S406_RETURNS_TWO_KINDS from the LIVE bytes by anchored
edits. Every anchor must occur exactly once, and every source must be at its FROM pin, or the build stops with nothing
written. Nothing is re-typed.

  darpan_app.py            cn-detail's notes gain kind / status / noise / needs_ok / patient_text through returns_kinds
                           (fail-soft); pending_approval becomes the real count (pending_old kept); POST /api/cn-kind
                           (the owner's flip, audited)
  sanjeevni_approvals.py   the Needs-you returns line uses the new count (NEEDS_YOU_WITHOUT_S406=1 keeps the old rule,
                           for S400's frozen walk only); the months API gains counter_returns / counter_returns_pct
  finance_approvals.html   the Returns card re-rendered (two kinds, one status word, the audit text inside the tap-open
                           detail, the old renderer one link away as loadCNOld); the Month table gains the returns % column

Usage: make_s406.py --finance /root/finance --out DIR
"""
import hashlib
import os
import sys

FROM = {
    "darpan_app.py": "2c22822d49a20143058b5d781eb3c06e",
    "sanjeevni_approvals.py": "126f90fc9912092378e817f101a8f74e",
    "finance_approvals.html": "928a25ef503267ce8e518f126306c236",
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


# ---------------------------------------------------------------- darpan_app.py
def build_darpan(s):
    s = rep(s, '''INSTALL: two lines in finance_app.py, by patch_finance_app_darpan.py.
Flask and the standard library only, to match the app it joins.
"""
''', '''INSTALL: two lines in finance_app.py, by patch_finance_app_darpan.py.
Flask and the standard library only, to match the app it joins.

S406 (26-Sep-2026, D622): cn-detail's notes carry kind (counter | noncash), one status word, the rounding rule and
the real Need-your-OK count through returns_kinds.py (read layer; fail-soft -- the old fields stay as they were);
POST /finance/darpan/api/cn-kind is the owner's flip (audited). cn-approve is untouched.
"""
''', "header")
    s = rep(s, '''    return jsonify(ok=True, month=month, count=len(out), total_p=total_p,
                   audited=tally.get("audited", 0),
                   orphans=tally.get("orphan", 0),
                   no_item_detail=tally.get("no item detail", 0),
                   flagged=flagged, pending_approval=pending, notes=out,
                   large_p=_large_p, spot_checks=_spot_checks(con, _unit, month),
                   metrics=_month_metrics(con, _unit, month, total_p, _examinable_p, _flagged_p))
''', '''    # S406 (D622): two kinds, one status word, rounding is not a finding, Need-your-OK counts only real items.
    # returns_kinds is a read layer over these very notes; if it cannot answer, the old fields stand and it says so.
    pending_old = pending
    try:
        import returns_kinds                                        # noqa: PLC0415
        kinds = returns_kinds.enrich(con, _unit, month, out)
        pending = kinds["pending_ok"]
    except Exception as ex:                                         # noqa: BLE001
        kinds = dict(error=str(ex)[:200])
    return jsonify(ok=True, month=month, count=len(out), total_p=total_p,
                   audited=tally.get("audited", 0),
                   orphans=tally.get("orphan", 0),
                   no_item_detail=tally.get("no item detail", 0),
                   flagged=flagged, pending_approval=pending, pending_old=pending_old, kinds=kinds, notes=out,
                   large_p=_large_p, spot_checks=_spot_checks(con, _unit, month),
                   metrics=_month_metrics(con, _unit, month, total_p, _examinable_p, _flagged_p))
''', "cn-detail kinds")
    s = rep(s, '''@bp.route("/finance/darpan/api/idlookup")
''', '''@bp.route("/finance/darpan/api/cn-kind", methods=["POST"])
def api_cn_kind():
    """S406 (D622): the owner flips a credit note between 'counter' and 'noncash' (his own non-cash return). Owner
    only; recorded with who and when in cn_kind and in the audit; kept over every recompute."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    if not _is_owner(con, u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    bill = str(b.get("bill") or "").strip().upper()
    kind = str(b.get("kind") or "").strip()
    if not bill or kind not in ("counter", "noncash"):
        return jsonify(ok=False, error="bad_request", message="bill, and kind counter or noncash"), 400
    try:
        import returns_kinds                                        # noqa: PLC0415
        r = returns_kinds.flip(con, _unit, bill, kind, u["user"])
    except Exception as ex:                                         # noqa: BLE001
        return jsonify(ok=False, error="kinds_unavailable", message=str(ex)[:200]), 503
    _audit(con, u["user"], "cn_kind", {"bill": bill, "kind": kind})
    con.commit()
    return jsonify(ok=True, **r)


@bp.route("/finance/darpan/api/idlookup")
''', "cn-kind route")
    return s


# ---------------------------------------------------------------- sanjeevni_approvals.py
def build_approvals(s):
    s = rep(s, '''#  sanjeevni_approvals.py  ·  v1.6  ·  kit S405_BANK_SMS_DOOR  ·  Session 283 (Sanjeevni)
#
''', '''#  sanjeevni_approvals.py  ·  v1.7  ·  kit S406_RETURNS_TWO_KINDS  ·  Session 283 (Sanjeevni)
#
#  v1.7 (S406, D622, 26-Sep-2026): the Needs-you returns line counts only real items (returns_kinds.pending_count:
#  counter returns >= returns.big_p, never bought, returned more than sold); the months API gains counter_returns and
#  counter_returns_pct. NEEDS_YOU_WITHOUT_S406=1 keeps the old rule -- set only by S400's frozen walk re-run.
#
''', "header")
    s = rep(s, '''VERSION = "1.6"
''', '''VERSION = "1.7"
''', "version")
    s = rep(s, '''def _returns_pending(con, ym):
    """The returns of the month that wait for the owner's OK -- the same rule as cn-detail (S220)."""
    try:
        from finance_returns_audit import returns_for_day  # noqa: PLC0415
''', '''def _returns_pending(con, ym):
    """The returns of the month that wait for the owner's OK -- the same rule as cn-detail (S220).
    S406 (D622): the rule is returns_kinds' -- counter returns only, real items only. NEEDS_YOU_WITHOUT_S406=1 is set
    ONLY by S400's frozen walk re-run (it asserts Needs you unchanged); the service never sets it."""
    if os.environ.get("NEEDS_YOU_WITHOUT_S406") != "1":
        try:
            import returns_kinds  # noqa: PLC0415
            return returns_kinds.pending_count(con, _unit, ym)
        except Exception:  # noqa: BLE001
            pass
    try:
        from finance_returns_audit import returns_for_day  # noqa: PLC0415
''', "returns pending")
    s = rep(s, '''                        else ("Marg's own bills, %d of %d days" % (m["marg_days"], m["days"]) if m["marg_days"] else "no Marg bills on record")))
    return dict(ok=True, months=out)
''', '''                        else ("Marg's own bills, %d of %d days" % (m["marg_days"], m["days"]) if m["marg_days"] else "no Marg bills on record")))
    # S406 (D622): counter returns per month -- count, rupees, % of counter sales (fail-soft: None when the engine cannot answer)
    for row in out:
        try:
            import returns_kinds  # noqa: PLC0415
            f = returns_kinds.month_fields(con, _unit, row["ym"])
        except Exception:  # noqa: BLE001
            f = {}
        row["counter_returns_n"] = f.get("counter_returns_n")
        row["counter_returns_p"] = f.get("counter_returns_p")
        row["counter_returns"] = rs(f["counter_returns_p"]) if f.get("counter_returns_p") is not None else None
        row["counter_returns_pct"] = f.get("counter_returns_pct")
    return dict(ok=True, months=out)
''', "months fields")
    return s


# ---------------------------------------------------------------- finance_approvals.html
NEW_CN_JS = r'''/* ---- S406 (D622): the Returns card, two kinds -- counter returns (the %) and the owner's own non-cash returns; one
   status word per line; the audit text inside the tap-open detail (unchanged words); the old renderer one link away. ---- */
function cnKind(bill,kind){
  fetch("/finance/darpan/api/cn-kind",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({bill:bill,kind:kind})})
   .then(function(r){return r.json()}).then(function(j){ if(!j.ok){alert(j.message||j.error);return} loadCN(); loadMonths(); loadNeeds(); })
   .catch(function(){alert("nothing was saved — the server could not be reached")});
}
function cnStatusHtml(n){
  var w=n.status||"ok";
  if(w==="ok") return '<span class="ok">ok</span>'+(n.approval&&n.approval.status==="approved"?' <span class="mut">✓ approved</span>':'')+(n.noise?' <span class="mut">(rounding)</span>':'');
  if(w==="your OK") return '<span class="badge b-warn">your OK</span>';
  if(w==="rejected") return '<span class="badge b-bad">rejected</span>';
  if(w==="never bought"||w==="over-refund") return '<span class="badge b-bad">'+esc(w)+'</span>';
  return '<span class="badge b-warn">'+esc(w)+'</span>';
}
function cnDetailHtml(n,j){
  var h='';
  var vb = n.verdict==="ok" ? '<span class="ok">ok</span>'
         : (n.verdict==="no patient attributed"||n.verdict==="not examinable"||n.verdict==="identity needed"||n.verdict==="identity disputed")
           ? '<span class="badge b-warn">'+esc(n.verdict)+'</span>' : '<span class="badge b-bad">'+esc(n.verdict)+'</span>';
  var money=' · ₹'+(n.amount_p/100).toFixed(2);
  if(n.gross_p!=null && n.net_p!=null && n.gross_p!==n.net_p) money=' · goods worth ₹'+(n.gross_p/100).toFixed(2)+' → refunded ₹'+(n.net_p/100).toFixed(2);
  h+='<div style="margin:2px 0"><b>'+esc(n.bill||"?")+'</b> · '+esc(n.date)+money+' · audit verdict '+vb+
     (n.refund_shortfall_p?' · <span class="badge b-warn">₹'+(n.refund_shortfall_p/100).toFixed(2)+' withheld on the refund</span>':'')+
     (n.diff_p!=null?' · difference ₹'+(n.diff_p/100).toFixed(2)+(n.noise?' <span class="mut">(below the rounding line — not a finding)</span>':''):'')+
     (n.large?' · <span class="badge b-warn">₹'+((j.large_p||100000)/100).toFixed(0)+'+</span>':'')+'</div>';
  h+='<div class="mut" style="margin:4px 0">population: <b>'+esc(n.population)+'</b> · money from '+esc(n.money_from)+'</div>';
  h+= n.name
    ? '<div style="margin:2px 0">patient: <b>'+esc(n.name)+'</b>'+(n.clinic_id?' · ID '+esc(n.clinic_id):'')+(n.mobile?' · '+esc(n.mobile):(n.mobile_last4?' · …'+esc(n.mobile_last4):''))+'</div>'
    : (n.patient_text?'<div style="margin:2px 0">patient (from the bill text): <b>'+esc(n.patient_text)+'</b></div>':'<div class="mut" style="margin:2px 0">no patient attributed to this return</div>');
  h+='<div class="mut" style="margin:2px 0">kind: <b>'+esc(n.kind==="noncash"?"your non-cash return":"counter return")+'</b> — '+esc(n.kind_why||"")+(n.kind_source==="owner"?' (your word'+(n.kind_by?', '+esc(n.kind_by):'')+')':'')+
     ' <button class="ghost" onclick="event.stopPropagation();cnKind(\''+esc(n.bill)+'\',\''+(n.kind==="noncash"?"counter":"noncash")+'\')">'+(n.kind==="noncash"?"mark as counter return":"mark as my non-cash return")+'</button></div>';
  if(n.note) h+='<div class="mut" style="margin:2px 0">'+esc(n.note)+'</div>';
  if((n.audit_lines||[]).length){
    h+='<div style="margin-top:4px"><b>against their own earlier purchases</b></div>'+
       '<div class="tblwrap"><table><thead><tr><th>item</th><th>qty</th><th class="num">rate</th><th class="num">line ₹</th><th>batch</th><th>exp</th><th>verdict</th></tr></thead><tbody>';
    n.audit_lines.forEach(function(l){
      var lc=l.verdict==="ok"?'<span class="ok">✓ '+esc(l.detail||"ok")+'</span>'
           :(l.verdict==="bought, quantity differs"?'<span class="mut">'+esc(l.detail||l.verdict)+'</span>'
           :'<span class="badge b-bad">'+esc(l.verdict)+'</span> <span class="mut">'+esc(l.detail||"")+'</span>');
      h+='<tr><td>'+esc(l.item)+'</td><td>'+esc(l.qty_raw||"")+'</td><td class="num">'+(l.rate_p!=null?(l.rate_p/100).toFixed(2):"—")+'</td>'+
         '<td class="num">'+(l.amount_line_p!=null?(l.amount_line_p/100).toFixed(2):"—")+'</td><td>'+esc(l.batch||"")+'</td><td>'+esc(l.expiry_ym||"")+'</td><td>'+lc+'</td></tr>';
    });
    h+='</tbody></table></div>';
  }else if((n.marg_lines||[]).length){
    h+='<div style="margin-top:4px"><b>the bill, as Marg exported it</b> <span class="mut">(the audit could not run — shown so nothing is hidden)</span></div>'+
       '<div class="tblwrap"><table><thead><tr><th>item</th><th>qty</th><th>pack</th><th class="num">rate</th><th>batch</th><th>exp</th></tr></thead><tbody>';
    n.marg_lines.forEach(function(m){
      h+='<tr><td>'+esc(m.item)+'</td><td>'+esc(m.qty||"")+'</td><td>'+esc(m.pack||"")+'</td><td class="num">'+(m.rate_p!=null?(m.rate_p/100).toFixed(2):"—")+'</td><td>'+esc(m.batch||"")+'</td><td>'+esc(m.expiry||"")+'</td></tr>';
    });
    h+='</tbody></table></div>';
  }else{
    h+='<div class="mut">item lines are not on this server for this bill</div>';
  }
  var a=n.approval||{};
  if(n.pending_ok)
    h+='<div class="note" style="margin:6px 0"><span class="badge b-warn">⚠ NOT entertained without your approval — owner ruling, 30-Aug</span> '+
       '<button onclick="event.stopPropagation();cnDecide(\''+esc(n.bill)+'\',\'approved\')">I know this case — approve</button> '+
       '<button class="ghost" onclick="event.stopPropagation();cnDecide(\''+esc(n.bill)+'\',\'rejected\')">Reject — recover</button></div>';
  else if(n.approval && a.status && a.status!=="pending")
    h+='<div class="mut" style="margin:6px 0">'+(a.status==="approved"?"✓ approved":"✕ REJECTED")+' by '+esc(a.decided_by||"")+' · '+esc((a.decided_at||"").slice(0,16))+(a.note?' · '+esc(a.note):'')+'</div>';
  else if(n.needs_approval && !n.needs_ok)
    h+='<div class="mut" style="margin:6px 0">the old rule asked for your OK here; the S406 rule does not (rounding, or not a counter return) — '+
       '<button class="ghost" onclick="event.stopPropagation();cnDecide(\''+esc(n.bill)+'\',\'approved\')">approve anyway</button></div>';
  return h;
}
function cnLineHtml(n,j,ix){
  var who = n.name ? esc(n.name) : (n.patient_text ? '<span class="mut">'+esc(n.patient_text)+'</span>' : '<span class="mut">—</span>');
  return '<tr class="dayrow" onclick="var d=$(\'cnd'+ix+'\');d.style.display=d.style.display===\'none\'?\'\':\'none\'"><td><b>'+esc(n.bill||"?")+'</b></td><td>'+esc(n.date)+'</td><td>'+who+'</td>'+
         '<td class="num">'+gapRs(n.amount_p)+'</td><td>'+cnStatusHtml(n)+' <span class="mut">▸</span></td></tr>'+
         '<tr id="cnd'+ix+'" style="display:none"><td colspan="5"><div class="day-detail">'+cnDetailHtml(n,j)+'</div></td></tr>';
}
function loadCN(){
  if(window.CN_OLD){loadCNOld();return}
  var box=$("cnBox"); if(!box) return;
  var mEl=$("cnMonth"); var m=(mEl&&mEl.value)||"";
  fetch("/finance/darpan/api/cn-detail"+(m?("?month="+encodeURIComponent(m)):"")).then(function(r){return r.json()})
   .then(function(j){
    if(!j.ok){box.innerHTML='<span class="bad">'+esc(j.message||j.error||"returns unavailable")+'</span>';return}
    if(mEl && !mEl.value && j.month) mEl.value=j.month;
    window.CN_PENDING=j.pending_approval||0; updateNeeds();
    var K=j.kinds||{};
    if(K.error||!K.counter){box.innerHTML='<span class="mut">the two-kinds view is unavailable ('+esc(K.error||"no data")+') — </span><a href="#" onclick="window.CN_OLD=1;loadCN();return false">old view</a>';return}
    var MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    var lab=function(m){return m?(MON[parseInt(m.slice(5,7),10)-1]+" "+m.slice(0,4)):""};
    var pc=function(v){return v==null?"—":(Number(v).toFixed(1)+"%")};
    var C=K.counter||{}, NC=K.noncash||{}, P=K.prev||{};
    var h='<div style="font-size:15px"><b>Counter returns — '+(C.n||0)+' · '+gapRs(C.p||0)+' · '+pc(C.pct)+' of counter sales</b>'+
      (P.ym?' <span class="mut">('+esc(lab(P.ym))+': '+(P.counter_returns_n==null?"—":P.counter_returns_n)+' · '+gapRs(P.counter_returns_p||0)+' · '+pc(P.counter_returns_pct)+')</span>':'')+
      ' · '+(j.pending_approval?'<span class="badge b-warn">'+j.pending_approval+' NEED YOUR OK</span>':'<span class="ok">nothing needs your OK ✓</span>')+
      ' <span class="mut" style="font-size:12px">· <a href="#" onclick="window.CN_OLD=1;loadCN();return false">old view</a></span></div>';
    var notes=j.notes||[];
    var head='<thead><tr><th>bill</th><th>date</th><th>patient</th><th class="num">amount</th><th>status</th></tr></thead>';
    var cn=notes.filter(function(n){return n.kind!=="noncash"});
    h+=cn.length?'<div class="tblwrap"><table>'+head+'<tbody>'+cn.map(function(n){return cnLineHtml(n,j,notes.indexOf(n))}).join("")+'</tbody></table></div>':'<div class="mut">no counter returns this month</div>';
    var nc=notes.filter(function(n){return n.kind==="noncash"});
    h+='<details style="margin:8px 0"><summary><b>Your non-cash returns — '+(NC.n||0)+' · '+gapRs(NC.p||0)+'</b> <span class="mut">goods back against a home / procedure bill, no cash; never in the counter %</span></summary>'+
       (nc.length?'<div class="tblwrap"><table>'+head+'<tbody>'+nc.map(function(n){return cnLineHtml(n,j,notes.indexOf(n))}).join("")+'</tbody></table></div>':'<div class="mut">none this month</div>')+'</details>';
    var S=K.settings||{};
    h+='<div class="mut" style="font-size:12px">Rounding is not a finding: a difference under ₹'+((S.noise_p||2000)/100)+' or '+(S.noise_pct||2)+'% reads ok. Need your OK = ₹'+((S.big_p||100000)/100)+'+, never bought, or returned more than sold — counter returns only. Tap a line for the audit detail; the flip is one tap inside it. (S406, D622)</div>';
    box.innerHTML=h;
    loadCNSpot(j);
  }).catch(function(e){box.innerHTML='<span class="bad">could not load returns ('+e+')</span>'});
}
function loadCNSpot(j){
  /* the S220 spot-count list, exactly as the old renderer draws it (into spotBox) */
  var h="", sc=j.spot_checks||[];
  if(sc.length){
    var due=sc.filter(function(s){return s.status==="due"}).length;
    h+='<details style="margin:10px 0 4px 0"'+(due?' open':'')+'><summary><b>Spot-count list</b> · '+sc.length+' item(s)'+
       (due?' · <span class="badge b-warn">'+due+' to count</span>':' · <span class="ok">all counted ✓</span>')+'</summary>';
    h+='<div class="tblwrap"><table><thead><tr><th>item</th><th>batch</th><th>why</th><th>credit note</th><th>date</th><th>count</th></tr></thead><tbody>';
    sc.forEach(function(s){
      var act= s.status==="due"
        ? '<button class="ghost" onclick="spotCount('+s.id+',\'done\')">counted</button> <button class="ghost" onclick="spotCount('+s.id+',\'skipped\')">skip</button>'
        : (s.status==="done"?'<span class="ok">✓ '+esc(s.counted_qty||"")+'</span>':'<span class="mut">skipped</span>')+
          '<span class="mut"> · '+esc(s.counted_by||"")+' '+esc((s.counted_at||"").slice(0,16))+(s.note?' · '+esc(s.note):'')+'</span>';
      h+='<tr><td>'+esc(s.item_name||s.item_key)+'</td><td>'+esc(s.batch||"")+'</td><td>'+esc(s.reason)+'</td><td>'+esc(s.bill_no)+'</td><td>'+esc(s.business_date)+'</td><td>'+act+'</td></tr>';
    });
    h+='</tbody></table></div><div class="mut">Count the shelf, type what is there. The difference against Marg is read later; this only records the count, by name and time.</div></details>';
  }
  var spot=$("spotBox"); if(spot)spot.innerHTML=h||'<span class="mut">nothing on the spot-count list</span>';
}
function loadCNOld(){
'''


def build_html(s):
    s = rep(s, '''<!doctype html>
<!-- S405_BANK_SMS_DOOR''', '''<!doctype html>
<!-- S406_RETURNS_TWO_KINDS (Session 283, 26-Sep-2026, D622): the Returns card re-rendered -- Counter returns (N · ₹ · %
     of counter sales, last month beside it) and the owner's own non-cash returns as a collapsed block; one clean line per
     return with ONE status word; the audit text inside the tap-open detail; the old renderer one link away (loadCNOld).
     The Month table gains the returns % column. Nothing else on the page moves.
  -- kit S405 header below --
<!-- S405_BANK_SMS_DOOR''', "header")
    s = rep(s, '''function loadCN(){
  /* S213 (returns sump r1) + S217: own card, month picker (cn-detail has
''', NEW_CN_JS + '''  /* S213 (returns sump r1) + S217: own card, month picker (cn-detail has
''', "the renderer")
    s = rep(s, '''    var h='<div class="tblwrap"><table><thead><tr><th>month</th><th class="num">sale</th><th class="num hide-sm">online</th><th class="num hide-sm">cash</th><th class="num hide-sm">without cash</th><th class="num">banked</th><th></th></tr></thead><tbody>';
''', '''    var h='<div class="tblwrap"><table><thead><tr><th>month</th><th class="num">sale</th><th class="num hide-sm">online</th><th class="num hide-sm">cash</th><th class="num hide-sm">without cash</th><th class="num">banked</th><th class="num">returns</th><th></th></tr></thead><tbody>';
''', "months head")
    s = rep(s, '''         '<td class="num">₹'+esc(m.sale)+'</td><td class="num hide-sm">₹'+esc(m.upi)+'</td><td class="num hide-sm">₹'+esc(m.cash)+'</td><td class="num hide-sm">₹'+esc(m.without_cash)+'</td><td class="num">₹'+esc(m.banked)+'</td><td class="mut">▸</td></tr>';
      h+='<tr style="display:none"><td colspan="7"><div class="sub" style="padding:4px 0 6px 12px;font-size:13px">'+
''', '''         '<td class="num">₹'+esc(m.sale)+'</td><td class="num hide-sm">₹'+esc(m.upi)+'</td><td class="num hide-sm">₹'+esc(m.cash)+'</td><td class="num hide-sm">₹'+esc(m.without_cash)+'</td><td class="num">₹'+esc(m.banked)+'</td>'+
         '<td class="num">'+(m.counter_returns_pct==null?'<span class="mut">—</span>':esc(Number(m.counter_returns_pct).toFixed(1))+'%')+(m.counter_returns!=null?' <span class="sub">₹'+esc(m.counter_returns)+'</span>':'')+'</td><td class="mut">▸</td></tr>';   /* S406: counter returns % */
      h+='<tr style="display:none"><td colspan="8"><div class="sub" style="padding:4px 0 6px 12px;font-size:13px">'+
''', "months row")
    return s


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance"), args.get("--out")
    if not (fin and out):
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    built = {
        "darpan_app.py": build_darpan(load(os.path.join(fin, "darpan_app.py"), "darpan_app.py")),
        "sanjeevni_approvals.py": build_approvals(load(os.path.join(fin, "sanjeevni_approvals.py"), "sanjeevni_approvals.py")),
        "finance_approvals.html": build_html(load(os.path.join(fin, "finance_ui", "finance_approvals.html"), "finance_approvals.html")),
    }
    for name, text in built.items():
        raw = text.encode("utf-8")
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(raw)
        print("built %s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
