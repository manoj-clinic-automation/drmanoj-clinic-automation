#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s403.py -- builds the eleven patched live files of kit S403_PURCHASE_ORDERS_LIVE from the LIVE bytes by
anchored edits. Every anchor must occur exactly once, and every source must be at its FROM pin, or the build
stops with nothing written. Nothing is re-typed.

  purchase_app.py          the month page and the scan-links page mark a bill unscanned 3 days after arrival red;
                           the staff page's 'Scan the bill' opens the intake pre-filled (S225 stays the one ordering system)
  darpan_kal.py / .html    Darpan's 'Kal ka hisaab' gains the card 'Orthotic kam hai -- N' (collapsed; the list; a button)
  sale_check.py / .html    Bhati's 'Medical sale check' gains the same card, view only
  sanjeevni_approvals.py   Needs you gains the three S403 lines (read from porders, fail-soft)
  finance_approvals.html   the owner's 'Purchase orders' section: Orthotic shortages -- N (keep +/- per item, the full 69),
                           the medicine buying rules as tap-to-approve
  asset_register.py        the reception intake accepts lane / vendor / bill no / date / amount in the link and files them
                           on the bill (smallest anchored change; the scanner widget is untouched)
  finance_app.py           the front gate learns the unit 'porders' (/finance/porders/...); the module is mounted
  portal.py                the tile 'Purchase orders' (roles ['doctor']; granted by name)
  tile_grants.json         v27 -> v28: the tile to darpan, shavez, shivani, alisha

Usage: make_s403.py --finance /root/finance --portal /root/portal --assets /root/assetapp --out DIR
"""
import hashlib
import json
import os
import sys

FROM = {
    "purchase_app.py": "9ad508789e2821c284b48ef6a4446cfa",
    "darpan_kal.py": "1958ee7c620d890f10a609473b2a8f1d",
    "darpan_kal.html": "4f115f44b9ed505f5838ef3ee0a4267a",
    "sale_check.py": "92ca5cb2d3a4388bbf6a29e35af2d492",
    "sale_check.html": "9c70af26456092285a9545083365bfff",
    "sanjeevni_approvals.py": "5fdfa364dee3dd9dcef9ad5fed3233d9",
    "finance_approvals.html": "6622587e47faff016bf280d380bd4564",
    "asset_register.py": "71bd32777b69e375e41576c7aeb7eb1d",
    "finance_app.py": "186a500a862a7f77da45e1e39b504f2e",
    "portal.py": "4a5b505e0274e37ab576fa0bc7852420",
    "tile_grants.json": "9e3124e02fd79d3e1ef01e52bdc5cc76",
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


# ---------------------------------------------------------------- purchase_app.py
def build_purchase(s):
    s = rep(s, '''def _rematch(con, who="system"):
''', '''def _scan_age(bill_date):
    """S403: days since the bill's date (its arrival, as Marg dates it); 0 when unreadable."""
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(bill_date or "")[:10])).days
    except ValueError:
        return 0


def _scan_overdue(bill_date, days=3):
    """S403 (D618): a bill unscanned three days after arrival turns red -- on the month page, on the scan-links page
    and on the Purchase orders screen (porders.py reads the same rule)."""
    return _scan_age(bill_date) > days


def _rematch(con, who="system"):
''', "scan helpers")
    s = rep(s, '''            lk = links.get(b["id"])
            scan = ('<a href="%s/bills/%d" target="_blank">scan %s</a>' % (_assets_url, lk[0], lk[1].lower())
                    if lk else '<span class="muted">no scan</span>')
''', '''            lk = links.get(b["id"])
            if lk:
                scan = '<a href="%s/bills/%d" target="_blank">scan %s</a>' % (_assets_url, lk[0], lk[1].lower())
            elif _scan_overdue(b["bill_date"]):                # S403 (D618): unscanned 3 days after arrival = red
                scan = '<span class="bad">no scan \\u2014 %d days</span>' % _scan_age(b["bill_date"])
            else:
                scan = '<span class="muted">no scan</span>'
''', "month page scan cell")
    s = rep(s, '''    return _page("Scan links", body)
''', '''    red = [b for b in un_b if _scan_overdue(b["bill_date"])]          # S403 (D618): the same red list as the Purchase orders screen
    if red:
        body = body.replace('<div class="card"><h2>Scans with no Marg bill',
                            '<div class="card"><h2 class="bad">Unscanned 3 days after arrival (%d)</h2><div class="muted">Reception scans these from the '
                            'Purchase orders screen (Bill scan karo); the intake opens with the vendor, bill number and amount filled in.</div>'
                            '<div class="scroll"><table><tr><th>Date</th><th>Supplier</th><th>Bill no</th><th class="n">Amount</th><th class="n">Days</th></tr>%s</table></div></div>'
                            '<div class="card"><h2>Scans with no Marg bill' % (len(red), "".join(
                                '<tr><td>%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n bad">%d</td></tr>'
                                % (_human(b["bill_date"]), _esc(b["supplier"]), _esc(b["bill_no"]), _r(b["amount_p"]), _scan_age(b["bill_date"])) for b in red)), 1)
    return _page("Scan links", body)
''', "scan-links red list")
    s = rep(s, '''        return ('<a href="/scanapp/intake" target="_blank"><button class="sm">Scan the bill</button></a>'
                '<br><small class="muted">note on the scan: %s · ₹%s</small>%s'
                % (_esc(o["vendor"]), _esc(_r(o["total_p"])[1:]), note))
''', '''        from urllib.parse import quote                         # noqa: PLC0415
        return ('<a href="/scanapp/intake?lane=pharmacy&vendor=%s" target="_blank"><button class="sm">Scan the bill</button></a>'   # S403: the intake opens pre-filled
                '<br><small class="muted">note on the scan: %s · ₹%s</small>%s'
                % (quote(str(o["vendor"] or ""), safe=""), _esc(o["vendor"]), _esc(_r(o["total_p"])[1:]), note))
''', "staff page scan link")
    return s


# ---------------------------------------------------------------- darpan_kal.py / .html
def build_kal(s):
    s = rep(s, '''INSTALL: two lines in finance_app.py after the S241_AMIR_DAY mount, by
patch_finance_app_darpan_kal_s243.py.  Flask and the standard library only.
"""
''', '''INSTALL: two lines in finance_app.py after the S241_AMIR_DAY mount, by
patch_finance_app_darpan_kal_s243.py.  Flask and the standard library only.

S403 (D618, 26-Sep-2026): the day payload carries 'ortho_short' -- the orthotic shortages of the Purchase orders
screen (porders.shortage_summary, read in-process, fail-soft) -- for the card 'Orthotic kam hai -- N' on the page.
"""
''', "kal docstring")
    s = rep(s, '''# ------------------------------------------------------------------ api: the day
def _day_payload(con, iso, who):
''', '''def _ortho_short_safe(con):
    """S403 (D618): 'Orthotic kam hai -- N' for Darpan's card, read from porders in-process; never breaks the page."""
    try:
        import porders                                       # noqa: PLC0415
        return porders.shortage_summary(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, n=0, items=[], error=str(e)[:80])


# ------------------------------------------------------------------ api: the day
def _day_payload(con, iso, who):
''', "kal helper")
    s = rep(s, '''                returns=_returns_for(con, iso), owed=_owed(con), reasons=list(REASONS),
                return_answers=list(RETURN_ANSWERS), parties=list(PARTIES))
''', '''                returns=_returns_for(con, iso), owed=_owed(con), reasons=list(REASONS),
                return_answers=list(RETURN_ANSWERS), parties=list(PARTIES),
                ortho_short=_ortho_short_safe(con))            # S403 (D618)
''', "kal payload")
    return s


def build_kal_html(s):
    s = rep(s, ''' h+=sec(vh);
 el("body").innerHTML=h;
}
''', ''' h+=sec(vh);
 h+=orthoShortSec(j.ortho_short);   /* S403 (D618): Orthotic kam hai -- N */
 el("body").innerHTML=h;
}
/* S403 (D618): 'Orthotic kam hai -- N' -- collapsed; the list; a button that opens the Purchase orders screen */
function orthoShortSec(o){
 if(!o||!o.ok) return "";
 const n=o.n||0;
 return sec('<details><summary><span class="k">Orthotic kam hai — <b>'+n+'</b></span>'+(n?'':' <span class="ok">सब ठीक</span>')+'</summary>'+
  (n?'<table>'+o.items.map(x=>'<tr><td>'+esc(x.item)+'</td><td class="n">'+x.short+' kam'+(x.approx?' <span class="badge amber">approx</span>':'')+'</td></tr>').join("")+'</table>':'')+
  (o.sent?'<div class="muted">order bheja: '+esc(o.sent.sent_text)+' · '+esc(o.sent.by)+'</div>':'')+
  '<a class="btn primary" href="'+esc(o.url||"/finance/porders")+'">Purchase orders खोलें ↗</a></details>');
}
''', "kal html card")
    return s


# ---------------------------------------------------------------- sale_check.py / .html
def build_salecheck(s):
    s = rep(s, '''#  sale_check.py  ·  v1.1  ·  kit S402_SALECHECK_RETURNS  ·  Session 283 (Sanjeevni)  ·  D616
''', '''#  sale_check.py  ·  v1.1  ·  kit S402_SALECHECK_RETURNS  ·  Session 283 (Sanjeevni)  ·  D616
#  + S403 (26-Sep-2026, D618): the days list carries 'ortho_short' (porders.shortage_summary, in-process, fail-soft) for the
#  view-only card 'Orthotic kam hai -- N' on Bhati's list. He holds no porders row: nothing here sends or receives.
#  VERSION stays 1.1: S402's own walk (frozen) reads it back.
''', "salecheck header")
    s = rep(s, '''# ------------------------------------------------------------------ auth
def _auth():
    u, err = _require("maker", "checker", unit=ACCESS_UNIT)
''', '''def _ortho_short_safe(con):
    """S403 (D618): the orthotic shortages for Bhati's view-only card; never breaks the list."""
    try:
        import porders                                       # noqa: PLC0415
        return porders.shortage_summary(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, n=0, items=[], error=str(e)[:80])


# ------------------------------------------------------------------ auth
def _auth():
    u, err = _require("maker", "checker", unit=ACCESS_UNIT)
''', "salecheck helper")
    s = rep(s, '''    return jsonify(ok=True, me=kind, days=day_lines(con), log_from=_log_from(con))
''', '''    return jsonify(ok=True, me=kind, days=day_lines(con), log_from=_log_from(con),
                   ortho_short=_ortho_short_safe(con))         # S403 (D618): view only
''', "salecheck days payload")
    return s


def build_salecheck_html(s):
    s = rep(s, '''let DAYS=[], D=null, VIEW="list", GALTI=null, MSG=null;
''', '''let DAYS=[], D=null, VIEW="list", GALTI=null, MSG=null, J_ORTHO=null;   /* S403: the view-only orthotic card */
''', "salecheck html vars")
    s = rep(s, ''' try{const j=await get("/finance/salecheck/api/days");DAYS=j.days||[];}''',
            ''' try{const j=await get("/finance/salecheck/api/days");DAYS=j.days||[];J_ORTHO=j.ortho_short||null;}''', "salecheck html load")
    s = rep(s, '''  el("body").innerHTML=h;return;
 }
 const d=D;
''', '''  h+=orthoShortCard(J_ORTHO);   /* S403 (D618): Orthotic kam hai -- N, view only */
  el("body").innerHTML=h;return;
 }
 const d=D;
''', "salecheck html list")
    s = rep(s, '''function retBlock(r){''', '''function orthoShortCard(o){
 /* S403 (D618): the same card as Darpan's -- the list only; Bhati sends and receives nothing. */
 if(!o||!o.ok) return "";
 const n=o.n||0;
 return '<div class="card"><details'+(n?'':' ')+'><summary>Orthotic kam hai — <b>'+n+'</b>'+(n?'':' <span class="muted">sab theek</span>')+'</summary>'+
   (n?'<table>'+o.items.map(x=>'<tr><td>'+esc(x.item)+'</td><td class="n">'+x.short+' kam'+(x.approx?' <span class="chip pending">approx</span>':'')+'</td></tr>').join("")+'</table>':'')+
   (o.sent?'<div class="muted">order bheja: '+esc(o.sent.sent_text)+' · '+esc(o.sent.by)+'</div>':'')+'</details></div>';
}
function retBlock(r){''', "salecheck html card")
    return s


# ---------------------------------------------------------------- sanjeevni_approvals.py
def build_approvals(s):
    s = rep(s, '''#  sanjeevni_approvals.py  ·  v1.4  ·  kit S400_MEDICAL_SALE_CHECK  ·  Session 283 (Sanjeevni)
''', '''#  sanjeevni_approvals.py  ·  v1.5  ·  kit S403_PURCHASE_ORDERS_LIVE  ·  Session 283 (Sanjeevni)
#
#  v1.5 (S403, D618, 26-Sep-2026): Needs you gains three lines read from porders (fail-soft): 'Orthotic shortages: N items --
#  order not sent' · 'Bill scan pending on N purchase bills' · 'Buying rules for medicines await your approval'.
''', "approvals header")
    s = rep(s, '''VERSION = "1.4"
''', '''VERSION = "1.5"
''', "approvals version")
    s = rep(s, '''    # 7 · the statement's age (a word, not a fault)
''', '''    # 9 · S403 (D618): orthotic shortages with no order sent, bills awaiting a scan, the medicine buying rules.
    #     NEEDS_YOU_WITHOUT_S403=1 is set ONLY by an older kit's walk (S400's asserts 'unchanged except its own line');
    #     the service never sets it.
    if os.environ.get("NEEDS_YOU_WITHOUT_S403") != "1":
        try:
            import porders  # noqa: PLC0415
            lines.extend(porders.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 7 · the statement's age (a word, not a fault)
''', "approvals needs-you")
    return s


# ---------------------------------------------------------------- finance_approvals.html
def build_approvals_html(s):
    s = rep(s, '''  <div id="cnBox" class="note" style="margin-top:8px">loading&hellip;</div>
</div>

<div class="card tree" id="monthsCard">''', '''  <div id="cnBox" class="note" style="margin-top:8px">loading&hellip;</div>
</div>

<div class="card" id="porders"><h2><span class="kick">Orthotics first · the S225 engine for medicines</span>Purchase orders</h2>
<details class="fold" id="pordersShortCard" data-load="loadPOrders"><summary>Orthotic shortages — <span id="poN">…</span> <span class="sub">· keep-in-stock ± per item · the full 69 with keep numbers</span></summary><div>
  <div id="poOut">loading&hellip;</div>
</div></details>
<details class="fold" id="pordersRulesCard" data-load="loadPORules"><summary>Buying rules for medicines <span class="sub">· the S225 settings and the do-not-order list, one sitting</span></summary><div>
  <div id="poRules">loading&hellip;</div>
</div></details>
<div class="note">The staff screen is <a href="/finance/porders">Purchase orders</a> — Darpan, Shavez, Shivani and Alisha send; Bhati sees the shortages inside Medical sale check. Nothing here sends anything. (S403, D618)</div>
</div>

<div class="card tree" id="monthsCard">''', "approvals html card")
    s = rep(s, '''function loadNeeds(){
  fetch("/finance/sanjeevni/api/needs-you?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
''', '''function loadNeeds(){
  loadPOSummary();   /* S403: the count on the Purchase orders fold */
  fetch("/finance/sanjeevni/api/needs-you?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
''', "approvals html needs hook")
    s = rep(s, '''/* -------------------------------- orthotics ------------------------------ */
function loadOrtho(){
''', '''/* ---- S403 (D618): the owner's Purchase orders section -- orthotic shortages, keep ±, the rules sitting ---- */
function loadPOSummary(){
  fetch("/finance/porders/api/summary?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){var j=x.j||{}; var e=$("poN"); if(e) e.textContent=j.ok?j.n:"?";}).catch(function(){});
}
function loadPOrders(){
  fetch("/finance/porders/api/state?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var o=$("poOut"); if(!o)return; if(!j.ok){o.textContent=j.message||j.error||"could not load";return}
    var e=$("poN"); if(e) e.textContent=j.ortho.n;
    var h='<div class="mut">Shelf = the 06-Sep count + purchases − sales + returns since ('+esc(j.source)+'); Marg\\'s closing beside it as a cross-check. Keep 0 never shows a shortage. '+(j.ortho.recent?'Order sent '+esc(j.ortho.recent.sent_text)+' by '+esc(j.ortho.recent.by)+'.':'')+'</div>';
    h+='<div class="tblwrap"><table><thead><tr><th>Item</th><th class="num">Shelf</th><th class="num">Marg</th><th class="num">Keep</th><th class="num">On order</th><th class="num">Short</th></tr></thead><tbody>';
    (j.ortho.lines||[]).forEach(function(l){h+=poRow(l)});
    if(!(j.ortho.lines||[]).length) h+='<tr><td colspan="6" class="mut">nothing short</td></tr>';
    h+='</tbody></table></div>';
    h+='<details style="margin-top:8px"><summary class="mut">The full '+(j.all||[]).length+' orthotics with keep numbers</summary><div class="tblwrap"><table><thead><tr><th>Item</th><th class="num">Shelf</th><th class="num">Marg</th><th class="num">Keep</th><th class="num">On order</th><th class="num">Short</th></tr></thead><tbody>';
    (j.all||[]).forEach(function(l){h+=poRow(l)});
    h+='</tbody></table></div></details>';
    o.innerHTML=h;
  }).catch(function(){var o=$("poOut"); if(o) o.textContent="could not reach the server"});
}
function poRow(l){
  var it=esc(l.item).replace(/'/g,"\\\\'");
  var k='<span class="mut">'+(l.keep_source==="owner"?"you":"seed")+'</span> <button class="ghost" onclick="poKeep(\\''+it+'\\',-1)">−</button> <b>'+l.keep+'</b> <button class="ghost" onclick="poKeep(\\''+it+'\\',1)">+</button>';
  return '<tr><td>'+esc(l.item)+(l.approx?' <span class="pill warn">approx</span>':'')+(l.rename?' <span class="mut">→ '+esc(l.rename.new)+' ('+esc(l.rename.state)+')</span>':'')+'</td><td class="num">'+l.shelf+'</td><td class="num">'+(l.marg==null?"—":l.marg)+'</td><td class="num">'+k+'</td><td class="num">'+l.on_order+'</td><td class="num">'+(l.short?'<b class="bad">'+l.short+'</b>':'—')+'</td></tr>';
}
function poKeep(item,delta){
  fetch("/finance/porders/api/keep",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({item:item,delta:delta})})
    .then(srvJSON).then(function(x){var j=x.j||{}; if(!j.ok){alert(j.message||j.error||"not changed");return} loadPOrders(); loadNeeds();})
    .catch(function(){alert("the server could not be reached")});
}
function loadPORules(){
  fetch("/finance/porders/api/rules?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var o=$("poRules"); if(!o)return; if(!j.ok){o.textContent="could not load";return}
    var s=j.s225||{}, L=j.lists||{};
    var h='<div class="mut">S225 engine: pace over '+s.pace_days+' days · lead '+s.lead_days+' + safety '+s.safety_days+' days · cover at most '+s.max_cover_days+' days · cadence weekly above ₹'+s.tier_weekly_rs+'/month, fortnightly above ₹'+s.tier_fortnight_rs+', else monthly · a line below ₹'+s.min_line_rs+' is dropped · '+esc(s.rounding)+'.</div>';
    ["never_reorder","on_demand","internal_use","orthotics_cycle"].forEach(function(k){h+='<div><b>'+k.replace(/_/g," ")+'</b>: '+((L[k]||[]).length?(L[k]||[]).map(esc).join(", "):'<span class="mut">empty</span>')+'</div>'});
    h+=j.approved?'<div class="ok" style="margin-top:8px">✓ approved by '+esc(j.approved.by)+' at '+esc(j.approved.at)+' — the staff screen may send medicine orders.</div>'
                 :'<div style="margin-top:8px"><button onclick="poApprove()">I approve these buying rules and the do-not-order list</button> <span class="mut">Until then the staff screen says "Doctor sahab ke rules ka intezaar".</span></div>';
    o.innerHTML=h;
  }).catch(function(){var o=$("poRules"); if(o) o.textContent="could not reach the server"});
}
function poApprove(){
  if(!confirm("Approve the medicine buying rules as they stand? The staff screen will then send medicine orders on WhatsApp.")) return;
  fetch("/finance/porders/api/rules/approve",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(srvJSON).then(function(x){var j=x.j||{}; if(!j.ok){alert(j.message||j.error||"not recorded");return} loadPORules(); loadNeeds();}).catch(function(){alert("the server could not be reached")});
}

/* -------------------------------- orthotics ------------------------------ */
function loadOrtho(){
''', "approvals html functions")
    return s


# ---------------------------------------------------------------- asset_register.py
def build_assets(s):
    s = rep(s, '''@app.route("/intake")
@login_required
def intake():
''', '''INTAKE_PREFILL = ("lane", "vendor", "bill_no", "bill_date", "amount")


def _intake_prefill():
    """S403 (D618): the Purchase orders screen opens the intake with the vendor (and the bill number, date and
    amount when Marg already has the bill) in the link; they ride the scanner's uploadFields and the basic form
    into the bill row, so the Marg match is EXACT the moment the scan lands. Absent = exactly as before."""
    out = {}
    for k in INTAKE_PREFILL:
        v = (request.args.get(k) or "").strip()[:120]
        if v:
            out[k] = v
    if out.get("lane") not in ("pharmacy", "clinic"):
        out.pop("lane", None)
    return out


def _form_prefill():
    return {k: (request.form.get(k) or "").strip()[:120] for k in INTAKE_PREFILL if (request.form.get(k) or "").strip()}


@app.route("/intake")
@login_required
def intake():
''', "assets prefill helpers")
    s = rep(s, '''        "uploadFields": {},          # the Note is injected live by the page below
''', '''        "uploadFields": _intake_prefill(),   # S403: the link's lane / vendor / bill no / date / amount; the Note is injected live below
''', "assets scan_cfg")
    s = rep(s, '''<p class=muted style="margin:4px 0 0">A pharmacy bill is filed as a scan and a stamp only.
It does not go into the clinic approval list.</p>
''', '''<p class=muted style="margin:4px 0 0">A pharmacy bill is filed as a scan and a stamp only.
It does not go into the clinic approval list.</p>
<p class=muted id=pf_note style="margin:4px 0 0"></p>
''', "assets note line")
    s = rep(s, '''<input type=hidden name=lane id=lane_basic value="clinic">
''', '''<input type=hidden name=lane id=lane_basic value="clinic">
<input type=hidden name=vendor id=pf_vendor><input type=hidden name=bill_no id=pf_bill_no><input type=hidden name=bill_date id=pf_bill_date><input type=hidden name=amount id=pf_amount>
''', "assets hidden inputs")
    s = rep(s, '''<script>function _pick(i,s){var e=document.getElementById(s);e.textContent=i.files&&i.files.length?('\\u2713 '+i.files[0].name):'';}</script></details>
''', '''<script>function _pick(i,s){var e=document.getElementById(s);e.textContent=i.files&&i.files.length?('\\u2713 '+i.files[0].name):'';}</script></details>
<script>(function(){var f=(window.SCANNER_CONFIG||{}).uploadFields||{};var s=document.getElementById('intake_lane');if(f.lane&&s){s.value=f.lane;if(s.onchange)s.onchange();}
['vendor','bill_no','bill_date','amount'].forEach(function(k){var e=document.getElementById('pf_'+k);if(e&&f[k]){e.value=f[k];}});
if(f.vendor){var p=document.getElementById('pf_note');if(p){p.textContent='Bill: '+f.vendor+(f.bill_no?' \\u00b7 no. '+f.bill_no:'')+(f.amount?' \\u00b7 \\u20b9'+f.amount:'')+' \\u2014 filled in from Purchase orders';}}})();</script>
''', "assets prefill script")
    s = rep(s, '''def _create_intake_bill(fobj, note, lane=None):
''', '''def _create_intake_bill(fobj, note, lane=None, prefill=None):
''', "assets create signature")
    s = rep(s, '''    _pharma = (lane or "").strip().lower() == "pharmacy"
    cur = db.execute(
        "INSERT INTO bills(kind,notes,source_stored,source_orig,stamp_no,status,"
        "submitted_by,submitted_at) VALUES(?,?,?,?,?,?,?,?)",
        ("Pharmacy" if _pharma else "Consumable", note, stored,
         secure_filename(fobj.filename), stamp,
         "captured" if _pharma else "draft",
         g.user["display_name"], _now_ist()))
''', '''    _pharma = (lane or "").strip().lower() == "pharmacy"
    pf = prefill or {}                                       # S403: the Purchase orders link's vendor / bill no / date / amount
    cur = db.execute(
        "INSERT INTO bills(kind,notes,source_stored,source_orig,stamp_no,status,"
        "submitted_by,submitted_at,vendor,bill_no,bill_date,total_amount) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        ("Pharmacy" if _pharma else "Consumable", note, stored,
         secure_filename(fobj.filename), stamp,
         "captured" if _pharma else "draft",
         g.user["display_name"], _now_ist(),
         (pf.get("vendor") or None), (pf.get("bill_no") or None),
         (_norm_date(pf.get("bill_date")) if pf.get("bill_date") else None),
         (_num(pf.get("amount")) if pf.get("amount") else None)))
''', "assets create insert")
    s = rep(s, '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"))
    if not bid:
        flash("No usable file received — send a photo or a PDF and try again.")
''', '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"), _form_prefill())     # S403
    if not bid:
        flash("No usable file received — send a photo or a PDF and try again.")
''', "assets submit")
    s = rep(s, '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"))
    if not bid:
        return ("no usable file", 400)
''', '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"), _form_prefill())     # S403
    if not bid:
        return ("no usable file", 400)
''', "assets scan submit")
    return s


# ---------------------------------------------------------------- finance_app.py
def build_finance_app(s):
    s = rep(s, '''    if path == "/finance/stockmatch" or path.startswith("/finance/stockmatch/"):
        return "stockmatch"  # S404: Darpan's 'Stock milaan' -- the orthotic matches of the count (owner, 26-Sep-2026, D619).
''', '''    if path == "/finance/stockmatch" or path.startswith("/finance/stockmatch/"):
        return "stockmatch"  # S404: Darpan's 'Stock milaan' -- the orthotic matches of the count (owner, 26-Sep-2026, D619).
    if path == "/finance/porders" or path.startswith("/finance/porders/"):
        return "porders"     # S403: the Purchase orders screen (owner, 26-Sep-2026, D618). bhati holds no row here.
''', "finance_app _unit_for_path")
    s = rep(s, '''# --- S404_ORTHO_STOCK_CLOSE end ---


if __name__ == "__main__":
''', '''# --- S404_ORTHO_STOCK_CLOSE end ---


# --- S403_PURCHASE_ORDERS_LIVE begin -- ONE screen: shortages -> WhatsApp order -> arrival -> bill scan (owner, 26-Sep-2026, D618) ---
# Its own unit 'porders' (makers darpan, shavez, shivani, alisha; checker = the owner). Reuses purchase_app (S225): the
# order book, _staff_send, _arrive, the scan match. GUARDED (S209): a fault inside the module is printed and every
# other page keeps serving.
try:
    import porders                                             # noqa: E402
    porders.init(app, db, require, unit=UNIT)
except Exception as _ex_po:                                    # noqa: BLE001
    print("porders NOT mounted: %s" % _ex_po, file=sys.stderr)
# --- S403_PURCHASE_ORDERS_LIVE end ---


if __name__ == "__main__":
''', "finance_app mount")
    return s


# ---------------------------------------------------------------- portal.py
def build_portal(s):
    s = rep(s, '''     "url": "/finance/stockmatch",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', '''     "url": "/finance/stockmatch",
     "roles": ["doctor"]},
    {"icon": "\\U0001F6D2", "name": "Purchase orders",
     # S403 NEW (owner, 26-Sep-2026, D618). ONE screen on the phone: the orthotic shortages (from the 06-Sep count) ->
     # the WhatsApp order to Yuvika -> Order aaya? -> Bill scan karo; medicines wait for the owner's buying rules.
     # Its own server unit ('porders': darpan, shavez, shivani, alisha makers; the doctor checker; bhati no row --
     # his view is inside Medical sale check). Granted by name in tile_grants.json v28; the doctor holds it by role.
     "desc": "Kam saaman \\u2192 order \\u2192 aaya? \\u2192 bill scan",
     "live": True,
     "url": "/finance/porders",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', "portal tile")
    s = rep(s, '''    "Stock milaan": "Money & Accounts",
''', '''    "Stock milaan": "Money & Accounts",
    "Purchase orders": "Money & Accounts",
''', "portal section")
    return s


# ---------------------------------------------------------------- tile_grants.json
def build_grants(raw):
    d = json.loads(raw)
    if json.dumps(d, indent=2, ensure_ascii=False) != raw:
        sys.exit("REFUSED: tile_grants.json does not round-trip through json.dumps(indent=2) -- build by hand")
    if d.get("version") != 27:
        sys.exit("REFUSED: tile_grants.json is v%r, expected v27" % d.get("version"))
    for who in ("darpan", "shavez", "shivani", "alisha"):
        ex = d["users"].setdefault(who, {}).setdefault("extra", [])
        if "Purchase orders" not in ex:
            ex.append("Purchase orders")
    d["version"] = 28
    d["_note"] += (" | v28 (S403, 26-Sep-2026): the NEW tile 'Purchase orders' (/finance/porders) to darpan, shavez, shivani and alisha -- "
                   "ONE screen: the orthotic shortages -> the WhatsApp order to Yuvika -> Order aaya? -> Bill scan karo; medicines wait for the "
                   "owner's buying rules; the doctor holds it by role. Its gate is a NEW server unit 'porders' (bhati holds NO row: his view is "
                   "inside Medical sale check); nothing else in this file moves.")
    return json.dumps(d, indent=2, ensure_ascii=False)


def main(argv):
    a = dict(zip(argv[1::2], argv[2::2]))
    fin, por, ast, out = a.get("--finance"), a.get("--portal"), a.get("--assets"), a.get("--out")
    if not (fin and por and ast and out):
        print(__doc__)
        return 2
    os.makedirs(out, exist_ok=True)
    built = {
        "purchase_app.py": build_purchase(load(os.path.join(fin, "purchase_app.py"), "purchase_app.py")),
        "darpan_kal.py": build_kal(load(os.path.join(fin, "darpan_kal.py"), "darpan_kal.py")),
        "darpan_kal.html": build_kal_html(load(os.path.join(fin, "darpan_kal.html"), "darpan_kal.html")),
        "sale_check.py": build_salecheck(load(os.path.join(fin, "sale_check.py"), "sale_check.py")),
        "sale_check.html": build_salecheck_html(load(os.path.join(fin, "sale_check.html"), "sale_check.html")),
        "sanjeevni_approvals.py": build_approvals(load(os.path.join(fin, "sanjeevni_approvals.py"), "sanjeevni_approvals.py")),
        "finance_approvals.html": build_approvals_html(load(os.path.join(fin, "finance_ui", "finance_approvals.html"), "finance_approvals.html")),
        "asset_register.py": build_assets(load(os.path.join(ast, "asset_register.py"), "asset_register.py")),
        "finance_app.py": build_finance_app(load(os.path.join(fin, "finance_app.py"), "finance_app.py")),
        "portal.py": build_portal(load(os.path.join(por, "portal.py"), "portal.py")),
        "tile_grants.json": build_grants(load(os.path.join(por, "tile_grants.json"), "tile_grants.json")),
    }
    for name, text in built.items():
        data = text.encode("utf-8")
        open(os.path.join(out, name), "wb").write(data)
        print("%s  %s" % (md5(data), name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
