#!/usr/bin/env python3
"""build_page.py -- kit S368_APPROVALS_TREE. Builds finance_approvals.html (the tree) FROM the live
S365 bytes (6c668ccc): the head and stylesheet are kept, every old renderer is kept (they now live
under Checks), and the body is the owner's tree. Deterministic: same input bytes -> same output bytes.
  python3 build_page.py --src OLD.html --out NEW.html
"""
import argparse, hashlib, re, sys

ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
src = open(a.src, encoding="utf-8").read()
assert hashlib.md5(src.encode("utf-8")).hexdigest() == "6c668cccc9e80bec8c843599a274951d", "the source is not the S365 page"

head_end = src.index("</style></head><body>")
head = src[:head_end]
script = src[src.index("<script>\nfunction $(i)"):src.rindex("</script></body></html>")]

def rep(s, old, new, n=1):
    assert s.count(old) == n, (old[:60], s.count(old))
    return s.replace(old, new)

# ---- head: the header comment + the tree's own styles
head = rep(head, "<!doctype html>\n", """<!doctype html>
<!-- finance_approvals.html · kit S368_APPROVALS_TREE (Session 281, Sanjeevni, 22-Sep-2026) — the owner's
     ONE TREE (D591 finished, D603): Needs you in words · Days · Cash · Bank · Returns · Month · Checks
     (the audit material, collapsed, on this same page). Every rupee from sanjeevni_cash (D600); the
     sentences from sanjeevni_approvals.py (D349). Every renderer of the S365 page is kept below, under
     Checks; the S365 page itself is kept byte for byte at /finance/approvals/old. Base 6c668ccc.
  -- earlier headers kept below --
""")
head += """
/* ---- S368: the tree ---- */
.needs{list-style:none;margin:0;padding:0}.needs li{padding:5px 0;border-top:1px solid #eee;cursor:pointer;font-size:15px}
.needs li:first-child{border-top:0}.needs .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;vertical-align:middle}
.dot.bad{background:#c62828}.dot.warn{background:#ef8f00}.dot.info{background:#7a8a99}
.tree table{width:100%;border-collapse:collapse;font-size:13.5px}.tree th{font-weight:600;color:var(--text-3);text-align:left;padding:4px 6px;white-space:nowrap}
.tree td{padding:5px 6px;border-top:1px solid #eee;vertical-align:top}.tree td.num,.tree th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tree tr.dayrow{cursor:pointer}.tree tr.dayrow:hover td{background:#fafafa}.tree tr.open td{background:#f6f8fa}
.tree .sub{font-size:12px;color:var(--text-3)}.act{white-space:nowrap}.act button{margin-left:4px}
details.fold{border-top:1px solid #eee;padding:6px 0}details.fold>summary{cursor:pointer;font-weight:600;font-size:15px;list-style:none;display:flex;gap:8px;align-items:center}
details.fold>summary::-webkit-details-marker{display:none}details.fold>summary:before{content:"\\25B8";color:var(--text-3);font-weight:400}
details[open].fold>summary:before{content:"\\25BE"}details.fold>summary .sub{font-weight:400}details.fold>div{padding:6px 0 4px 18px}
details.mon{margin:4px 0}details.mon>summary{cursor:pointer;font-weight:600;padding:4px 0;list-style:none}details.mon>summary::-webkit-details-marker{display:none}
details.mon>summary:before{content:"\\25B8 ";color:var(--text-3);font-weight:400}details[open].mon>summary:before{content:"\\25BE "}
.logbox{background:#fff8e6;border:1px solid #f1d58a;border-radius:8px;padding:8px 10px;margin:6px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.logbox input{width:110px}.pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:12px;background:#eef1f4;color:#445}
.pill.ok{background:#e6f4ea;color:#1b5e20}.pill.warn{background:#fff3e0;color:#8a4b00}.pill.bad{background:#fdecea;color:#b71c1c}
@media (max-width:640px){.tree .hide-sm{display:none}.tree table{font-size:12.5px}.tree td,.tree th{padding:4px 3px}}
"""

body = r"""</style></head><body>

<div class="hdr"><div class="hdr-in">
  <div class="brand">
    <img class="mark" alt="clinic logo" src="__LOGO__">
    <div>
      <div class="nm">Dr. Manoj Agarwal Clinic</div>
      <div class="sub">Advanced Orthopaedic Surgery Centre · Sanjeevni Hub</div>
    </div>
  </div>
  <nav class="tabs">
    <a href="#needsCard">Needs you</a><a href="#daysCard">Days</a><a href="#cashPosCard">Cash</a><a href="#bankCard">Bank</a>
    <a href="#returnsCard">Returns</a><a href="#monthsCard">Month</a><a href="#checksCard" onclick="openChecks();return true">Checks</a>
    <a class="ext" href="/finance/approvals/old">The old page ↗</a>
  </nav>
</div></div>

<div class="wrap">

<div id="alertBar"></div>
<div id="walkOverlay" onclick="if(event.target===this)walkClose()"><div id="walkBox" class="walkCard">loading…</div></div>

<div class="card" id="needsCard"><h2><span class="kick">In words</span>Needs you</h2>
<ul class="needs" id="needs"><li class="mut">loading&hellip;</li></ul>
<div class="note" id="needsNote"></div></div>

<div class="card tree" id="daysCard"><h2><span class="kick">One line per day · tap a day to open it</span>Days</h2>
<div id="days">loading&hellip;</div>
<div class="note">Sale, online and without-cash are Marg's and the bank's own figures; <b>cash</b> is the day's cash for the drawer from the one calculation. Approve first, then log the cash out if you want it on record (D592) — August and September need no logging (D598).</div></div>

<div class="card" id="cashPosCard"><h2><span class="kick">One figure, split</span>Cash — where it is</h2>
  <div id="cashPos" class="held"><span class="mut">loading…</span></div>
</div>

<div class="card tree" id="bankCard"><h2><span class="kick">The bank's own record, pharmacy only</span>Bank</h2>
<div id="bank">loading&hellip;</div></div>

<div class="card" id="returnsCard"><h2><span class="kick">Credit notes, each to its medicines</span>Returns</h2>
  <div class="row"><span class="mut">month</span><input type="month" id="cnMonth" onchange="loadCN()">
  <button class="ghost" onclick="loadCN()">show</button></div>
  <div id="cnBox" class="note" style="margin-top:8px">loading&hellip;</div>
</div>

<div class="card tree" id="monthsCard"><h2><span class="kick">One Marg figure, named for its days</span>Month</h2>
<div id="months">loading&hellip;</div></div>

<div class="card" id="checksCard"><h2><span class="kick">The audit material · everything kept, nothing on the tree</span>Checks</h2>
<div class="note">Each line opens on its own. Nothing here is needed to approve a day; it is here so nothing is hidden.</div>
<div id="checksAlerts"></div>

<details class="fold" id="kalCard" data-load="loadKal"><summary>Darpan's word vs the data <span class="sub">· his handovers, his reasons, what the data says</span></summary><div>
  <div id="kal">loading&hellip;</div>
  <div class="note">Every morning Darpan's page shows yesterday's expected cash; he types what he handed and to whom. Only a contradiction, a repeat pattern, a flagged return he could not explain, cash owed back to him, or a handover not yet marked received reaches here. Amber = waiting, not wrong.</div>
</div></details>

<details class="fold" id="gapCard" data-load="loadDayGaps"><summary>Gaps &amp; sanctioned discounts <span class="sub">· one day, bill by bill</span></summary><div>
  <div class="row"><label class="mut" for="gapDate">day</label><input type="date" id="gapDate" onchange="loadDayGaps(this.value)"><span id="gapWho" class="mut"></span></div>
  <div id="gapOut" class="mut" style="margin-top:8px">loading&hellip;</div>
  <div class="day-detail" id="gapDrill" style="display:none"></div>
</div></details>

<details class="fold" id="margCard" data-load="loadMargFold"><summary>Marg reports <span class="sub">· pushed from the counter, or loaded by hand</span></summary><div>
  <div class="row">
    <input type="file" id="mgFile" accept=".xls,.xlsx">
    <button class="ghost" id="mgCheck" onclick="mgSend(false)">Check first</button>
    <button id="mgApply" onclick="mgSend(true)">Load into the books</button>
    <span id="mgMsg" class="mut"></span>
  </div>
  <div id="mgOut" class="note"></div>
  <div style="margin-top:8px"><b>Pushed reports</b> <span class="mut">— from the medical PC</span>
  <div id="mpList" class="mut" style="margin-top:6px">loading&hellip;</div></div>
  <div id="rptToday" class="mut" style="margin-top:8px">Today's reports: loading&hellip;</div>
  <div id="mm" class="note">loading&hellip;</div>
  <div id="idBox" class="note"></div>
  <details class="help" id="amirVisitBox"><summary id="amirVisitSum">Amir's visit — what was done</summary>
  <div id="amirVisit">loading&hellip;</div></details>
  <details class="help"><summary>How this works</summary><div>
  Export from Marg as <b>Bill wise sales statement</b> with <b>With Item Deta. = Yes</b>.
  <b>Check first</b> writes nothing. The file is parsed and deleted on the server; a day not yet
  filed is skipped and <b>flagged</b>; re-loading a day supersedes it cleanly.</div></details>
</div></details>

<details class="fold" id="mprCard" data-load="loadMPR"><summary>Bank MPR — all three units <span class="sub">· the bank's day file, CSV for Darpan</span></summary><div>
  <div class="row"><span class="mut">day</span><input type="date" id="mprDate" onchange="loadMPR()">
  <button class="ghost" onclick="loadMPR()">show</button>
  <button class="ghost" onclick="mprCSV()">Download CSV for Darpan</button></div>
  <div id="mprOut" class="note" style="margin-top:8px">loading&hellip;</div>
</div></details>

<details class="fold" id="signalsCard" data-load="loadIntent"><summary>Return signals &amp; the spot-count list <span class="sub">· patterns against their own baselines; shelves to count</span></summary><div>
  <div id="intentBox" style="margin-top:4px"></div>
  <div id="spotBox" style="margin-top:8px" class="note"><span class="mut">open Returns above once; the list fills from the same read</span></div>
</div></details>

<details class="fold" id="reviewCard" data-load="loadReview"><summary>Parked rows <span class="sub">· bills with no patient name; the money is counted in full</span></summary><div>
  <div id="reviewOut" class="note">loading&hellip;</div>
</div></details>

<details class="fold" id="exCard" data-load="loadExFold"><summary>Open differences &amp; the walk <span class="sub">· the reconciler's own rows</span></summary><div>
  <div class="row"><button class="ghost" onclick="walkStart()">▶ Walk the day</button></div>
  <div id="ex">loading&hellip;</div>
</div></details>

<details class="fold" id="pendCard" data-load="loadQueueFold"><summary>The old queue <span class="sub">· the S217 table, as it was</span></summary><div>
  <div id="pend">loading&hellip;</div>
</div></details>

<details class="fold" id="homeMedCard" data-load="loadHomeMed"><summary>Billed without cash — the old card <span class="sub">· home &amp; procedure medicine</span></summary><div>
  <div id="homeMed">loading&hellip;</div>
</div></details>

<details class="fold" id="reclassCard" data-load="loadReclass"><summary>Cash ⇄ UPI reclassified <span class="sub">· dormant since the CA's ruling of 13-Sep</span></summary><div>
  <div class="note">Since the CA's ruling of 13-Sep-2026 nothing is corrected in Marg: the month's record goes to the <a href="/finance/accountant/upi-cash">accountant report — UPI booked as cash ↗</a>.</div>
  <div id="reclass">loading&hellip;</div>
</div></details>

<details class="fold" id="cashCard" data-load="loadCashFold"><summary>The drawer ledger — the old running total <span class="sub">· opening → collected → expenses → closing, never minus the handovers</span></summary><div>
  <div class="row"><div class="stat"><span class="lbl">Cash in hand (ledger)</span><span class="val" id="cashNow">—</span></div></div>
  <div class="row"><span class="mut">show</span>
    <button class="ghost" onclick="loadCash(30)">30 days</button>
    <button class="ghost" onclick="loadCash(60)">60</button>
    <button class="ghost" onclick="loadCash(90)">90</button></div>
  <div id="cashTbl" style="margin-top:10px">loading&hellip;</div>
</div></details>

<details class="fold" id="monthCard" data-load="loadMonthFold"><summary>Month — Entered · Marg · Bank, the old table <span class="sub">· its "Marg" is only the lines matched to a patient</span></summary><div>
  <div class="row"><input type="month" id="ymPick"><button class="ghost" onclick="loadMonth()">show</button>
  <span id="monthTot" class="mut"></span></div>
  <div id="monthTbl" style="margin-top:10px">loading&hellip;</div>
</div></details>

<details class="fold" id="orthoCard" data-load="loadOrtho"><summary>Orthotics <span class="sub">· last sold and pace; true stock lives on the Stock page</span></summary><div>
  <div class="row"><span class="mut">item keywords:</span>
    <input type="text" id="orthoVocab" size="42" placeholder="e.g. belt, brace, knee cap, collar, splint">
    <button class="ghost" onclick="saveVocab()">save</button><span id="orthoMsg" class="mut"></span></div>
  <div id="orthoOut" style="margin-top:10px">loading&hellip;</div>
</div></details>

<details class="fold" id="staffCardsCard" data-load="loadStaffCards"><summary>Staff cards <span class="sub">· who works where</span></summary><div>
  <div id="staffCards" class="note">loading&hellip;</div>
</div></details>

<details class="fold" id="stripCard"><summary>The old counters <span class="sub">· the S217 strip, as it was</span></summary><div>
  <div class="strip" id="strip">loading&hellip;</div>
  <div id="needsList"></div>
</div></details>

<details class="fold" id="linksCard"><summary>Other pages</summary><div>
  <a class="ext" href="/finance/workbench">Yes Bank statement · load and reconcile ↗</a> ·
  <a class="ext" href="/finance/darpan/kal/month">The cash month table ↗</a> ·
  <a class="ext" href="/finance/review">Review &amp; month close ↗</a> ·
  <a class="ext" href="/finance/darpan/corrections">Corrections ↗</a> ·
  <a class="ext" href="/finance/accountant/upi-cash">Accountant ↗</a> ·
  <a class="ext" href="/finance/pipeline">Pipeline ↗</a> ·
  <a class="ext" href="/finance/staff">Staff ↗</a> ·
  <a class="ext" href="/finance/approvals/old">The approvals page as it was ↗</a>
</div></details>
</div>

</div>
<button id="toTop" title="back to top" onclick="window.scrollTo({top:0,behavior:'smooth'})">▲</button>

"""
logo = re.search(r'src="(data:image/png;base64,[^"]+)"', src).group(1)
body = body.replace("__LOGO__", logo)

# ---- the script: keep every renderer; swap the orchestration; add the tree
s = script
s = rep(s, '''function load(){
  fetch("/finance/api/approvals").then(function(r){return r.json()}).then(function(j){''',
'''/* S368: the old orchestration is now loadOld() -- the S217 strip, queue, month grid and exceptions
   live under Checks and load when a fold that needs them is opened. The tree loads in load(). */
function loadOld(){
  if(window._oldLoading)return; window._oldLoading=true;
  fetch("/finance/api/approvals").then(function(r){return r.json()}).then(function(j){
    window._oldLoading=false;''')
s = rep(s, '''    renderPending(); renderMM(); renderEx(); updateNeeds();
  }).catch(function(){$("strip").textContent="could not load"});
  loadHealth(); loadPushes(); loadReports(); loadCash(30); loadCashPos(); initMonth(); loadOrtho();
  loadDayGaps();
}''',
'''    renderPending(); renderMM(); renderEx(); updateNeeds();
  }).catch(function(){window._oldLoading=false;$("strip").textContent="could not load"});
}
function load(){
  loadHealth(); loadNeeds(); loadDays(); loadCashPos(); loadBank(); loadCN(); loadMonths();
  document.querySelectorAll("details.fold[open][data-load]").forEach(function(f){var fn=window[f.getAttribute("data-load")];if(fn)fn()});
}''')
# the reconciler's and the review queue's counters are audit material: they go to Checks, not the top (D591)
s = rep(s, '''      var h="";
      (j.attention||[]).forEach(function(a){
        h+='<div class="alert '+(a.cls||'warn')+'">'+esc(a.text)+
           (a.sub?'<span class="sub">'+esc(a.sub)+'</span>':'')+'</div>';
      });''', '''      var h="", hc="";
      (j.attention||[]).forEach(function(a){
        var line='<div class="alert '+(a.cls||'warn')+'">'+esc(a.text)+
           (a.sub?'<span class="sub">'+esc(a.sub)+'</span>':'')+'</div>';
        if(/open exception|review queue|flag\\(s\\)/i.test(a.text||"")) hc+=line; else h+=line;
      });
      var ca=$("checksAlerts"); if(ca) ca.innerHTML=hc;''')
# the login name is not the source (F-613)
s = rep(s, '''h+='<div class="alert info">Latest filed day: <b>'+esc(f.date)+'</b> — filed by <b>'+esc(f.entered_by||"?")+
           '</b> at '+esc((f.entered_at||"").replace("T"," ").slice(0,16))+''',
'''h+='<div class="alert info">Latest filed day: <b>'+esc(f.date)+'</b> — filed '+
           esc((f.entered_at||"").replace("T"," ").slice(0,16))+' (from Marg and the bank; open the day for how)'+''')
# the spot-count list moves to Checks
s = rep(s, '''    var sc=j.spot_checks||[];
    if(sc.length){''', '''    var hMain=h; h="";
    var sc=j.spot_checks||[];
    if(sc.length){''')
s = rep(s, '''    box.innerHTML=h;
  }).catch(function(e){box.innerHTML='<span class="bad">could not load returns (\'+e+\')</span>'});''',
'''    var spot=$("spotBox"); if(spot)spot.innerHTML=h||'<span class="mut">nothing on the spot-count list</span>';
    box.innerHTML=hMain;
  }).catch(function(e){box.innerHTML='<span class="bad">could not load returns ('+e+')</span>'});''')
# boot + the S193 collapsible: every .card collapsible on its heading; Checks starts collapsed
s = rep(s, '''loadAmirVisit(); loadHomeMed(); loadReclass(); loadMPR(); loadReview(); loadStaffCards(); loadKal();
load();''', '''load();''')
s = rep(s, '''  ["margCard","cashCard","monthCard","orthoCard","exCard","homeMedCard","reclassCard"].forEach(function(id){''',
'''  ["checksCard"].forEach(function(id){''')
# the heading is the card's OWN heading, never one inside a fold (Checks holds the old drawer card's .h2row)
s = rep(s, '''    var head=card.querySelector(".h2row")||card.querySelector("h2"); if(!head) return;''',
'''    var head=card.querySelector(":scope > .h2row")||card.querySelector(":scope > h2"); if(!head) return;''')
s = rep(s, '''    var h=card.querySelector("h2")||head;''', '''    var h=card.querySelector(":scope > h2")||head;''')

tree_js = r'''
/* =========================== S368: THE TREE =========================== */
function goSec(target){
  var map={days:"daysCard",bank:"bankCard",returns:"returnsCard",cash:"cashPosCard",months:"monthsCard"};
  if(target&&target.indexOf("checks-")===0){openChecks(); var fid={"checks-marg":"margCard","checks-kal":"kalCard","checks-ex":"exCard"}[target];
    if(fid){var f=$(fid); if(f){f.open=true; foldLoad(f); f.scrollIntoView({behavior:"smooth"})}} return;}
  goCard(map[target]||target);
}
function openChecks(){var c=$("checksCard"); if(!c)return; c.classList.remove("collapsed"); var t=c.querySelector(".cabToggle"); if(t)t.textContent="▾ ";}
var foldDone={};
function foldLoad(f){ var fn=f.getAttribute("data-load"); if(!fn||foldDone[f.id])return; foldDone[f.id]=true; var g=window[fn]; if(g)g(); }
document.querySelectorAll("details.fold[data-load]").forEach(function(f){ f.addEventListener("toggle",function(){ if(f.open)foldLoad(f) }) });
function loadMargFold(){ loadPushes(); loadReports(); loadAmirVisit(); loadIDs(); loadOld(); }
function loadExFold(){ loadOld(); }
function loadQueueFold(){ loadOld(); }
function loadCashFold(){ loadCash(30); }
function loadMonthFold(){ initMonth(); }

/* ---- Needs you: the server's sentences (sanjeevni_approvals, D349) ---- */
function loadNeeds(){
  fetch("/finance/sanjeevni/api/needs-you?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var el=$("needs"); if(!el)return;
    if(!j.ok){el.innerHTML='<li class="mut">could not read what needs you — '+esc(j.message||j.error||("HTTP "+x.s))+'</li>';return}
    var L=j.lines||[];
    if(!L.length){el.innerHTML='<li><span class="ok">✓ Nothing needs you.</span></li>'; $("needsNote").textContent=""; return}
    el.innerHTML=L.map(function(l){return '<li onclick="goSec(\''+esc(l.target)+'\')"><span class="dot '+esc(l.cls||"warn")+'"></span>'+esc(l.text)+' <span class="mut">▸</span></li>'}).join("");
    $("needsNote").textContent=(j.count?"":"Nothing needs a decision; the grey line is for your information.");
  }).catch(function(){var el=$("needs");if(el)el.innerHTML='<li class="mut">could not reach the server</li>'});
}

/* ---- Days: one line per day, grouped by month; tap = the day panel (S365/S367) ---- */
var DAYS=null, dayOpen={};
function loadDays(){
  fetch("/finance/sanjeevni/api/days?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; if(!j.ok){$("days").innerHTML='<span class="mut">'+esc(j.message||j.error||"could not load")+'</span>';return}
    DAYS=j; renderDays();
  }).catch(function(){$("days").innerHTML='<span class="mut">could not reach the server</span>'});
}
function R(x){return (x==null||x==="")?"—":"₹"+x}
function renderDays(){
  if(!DAYS)return;
  var months={}, order=[];
  DAYS.days.forEach(function(d){var ym=d.date.slice(0,7); if(!months[ym]){months[ym]=[];order.push(ym)} months[ym].push(d)});
  order.reverse();
  var MON=["January","February","March","April","May","June","July","August","September","October","November","December"];
  var h="";
  order.forEach(function(ym,ix){
    var rows=months[ym]; var pend=rows.filter(function(d){return !d.approved}).length;
    var sale=0; rows.forEach(function(d){sale+=parseInt(String(d.sale||"0").replace(/,/g,""),10)||0});
    h+='<details class="mon"'+(ix===0||pend?' open':'')+'><summary>'+MON[parseInt(ym.slice(5,7),10)-1]+' '+ym.slice(0,4)+
       ' <span class="mut" style="font-weight:400">· '+rows.length+' day(s)'+(pend?' · <span class="badge b-warn">'+pend+' to approve</span>':' · <span class="ok">all approved</span>')+'</span></summary>';
    h+='<div class="tblwrap"><table><thead><tr><th>day</th><th class="num">sale</th><th class="num hide-sm">online</th><th class="num hide-sm">without cash</th><th class="num">cash</th><th>status</th><th class="act"></th></tr></thead><tbody>';
    rows.slice().reverse().forEach(function(d){
      var st;
      if(!d.approved) st='<span class="pill warn">to approve</span>';
      else if(d.log) st='<span class="pill ok">'+esc(d.log.amount)+' to '+esc(d.log.to)+(d.log.received?'':' · not yet received')+'</span>';
      else if(d.went) st='<span class="pill ok">'+esc(d.went)+'</span>';
      else st='<span class="pill">approved</span>';
      if(d.marg_ok===false) st+=' <span class="pill bad">Marg says '+esc(d.marg)+'</span>';
      if(d.elsewhere) st+=' <span class="pill">'+esc(d.elsewhere)+' paid at the clinic</span>';
      (d.banked||[]).forEach(function(b){st+=' <span class="pill ok">'+esc(b.amount)+' banked'+(b.place?' · '+esc(b.place):'')+'</span>'});
      var acts='';
      if(!d.approved) acts+='<button onclick="event.stopPropagation();approve(\''+d.date+'\')">Approve</button>';
      if(d.approved&&!d.log&&!d.went.match(/to Dr|to you|to the bank/)) acts+='<button class="ghost" onclick="event.stopPropagation();logCash(\''+d.date+'\','+(d.cash_p||0)+')">Log cash</button>';
      var op=!!dayOpen[d.date];
      h+='<tr class="dayrow'+(op?' open':'')+'" onclick="dayToggle(\''+d.date+'\')"><td><b>'+esc(d.day)+'</b> <span class="sub">'+esc(d.weekday)+'</span></td>'+
         '<td class="num">'+R(d.sale)+'</td><td class="num hide-sm">'+R(d.upi)+'</td><td class="num hide-sm">'+R(d.without_cash)+'</td>'+
         '<td class="num"><b>'+R(d.cash)+'</b></td><td>'+st+'</td><td class="act">'+acts+'</td></tr>';
      if(op) h+='<tr><td colspan="7"><div id="logbox-'+d.date+'"></div><div class="day-detail" id="dd-'+d.date+'">loading&hellip;</div></td></tr>';
    });
    h+='</tbody></table></div></details>';
  });
  if(DAYS.position) h+='<div class="mut" style="font-size:12px;margin-top:6px">Position after the last day: drawer ₹'+esc(DAYS.position.drawer)+' · with you &amp; Dr Bhawna ₹'+esc(DAYS.position.with_doctors)+' · banked ₹'+esc(DAYS.position.bank)+' — the one calculation (D600).</div>';
  $("days").innerHTML=h;
  Object.keys(dayOpen).forEach(function(d){ if(dayOpen[d]&&$("dd-"+d)) dayDetail(d,"dd-"+d) });
}
function dayToggle(d){ dayOpen[d]=!dayOpen[d]; renderDays(); }
function logCash(d,cash_p){
  dayOpen[d]=true; renderDays();
  var box=$("logbox-"+d); if(!box)return;
  box.innerHTML='<div class="logbox"><b>Log the cash of '+esc(d)+'</b> ₹<input type="number" id="logamt-'+d+'" value="'+((cash_p||0)/100)+'"> to '+
    '<button onclick="logSend(\''+d+'\',\'dr_manoj\')">me</button><button onclick="logSend(\''+d+'\',\'dr_bhawna\')">Dr Bhawna</button>'+
    '<button class="ghost" onclick="$(\'logbox-'+d+'\').innerHTML=\'\'">cancel</button><span class="mut">Prefilled with the day\'s expected cash; change it if Darpan handed a different amount.</span></div>';
}
function logSend(d,party){
  var v=parseFloat($("logamt-"+d).value); if(isNaN(v)||v<0){alert("type the amount");return}
  fetch("/finance/darpan/kal/api/log",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({date:d,amount_p:Math.round(v*100),party:party})})
    .then(srvJSON).then(function(x){var j=x.j||{}; var r=(j.results||[])[0]||{};
      if(!j.ok){alert(r.message||r.error||j.error||"could not log");return}
      loadDays(); loadCashPos(); loadNeeds();
    }).catch(function(e){alert("nothing was logged — the server could not be reached ("+e+")")});
}

/* ---- Bank: pharmacy UPI by day; the Yes Bank statement and its cash deposits ---- */
var BANK_YM=null;
function loadBank(ym){
  BANK_YM=ym||BANK_YM||(new Date()).toISOString().slice(0,7);
  fetch("/finance/sanjeevni/api/bank?month="+BANK_YM+"&_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var el=$("bank"); if(!j.ok){el.innerHTML='<span class="mut">'+esc(j.message||j.error||"could not load")+'</span>';return}
    var h='';
    var st=j.statement;
    h+='<details class="mon" open><summary>Yes Bank <span class="mut" style="font-weight:400">· '+
       (st?('statement loaded to <b>'+esc(st.to_day)+'</b> ('+st.days_since+' day'+(st.days_since===1?'':'s')+' ago) · banked from the pool ₹'+esc(j.banked_total)):'no statement loaded yet')+
       '</span></summary><div class="tblwrap"><table><thead><tr><th>date</th><th class="num">amount</th><th class="hide-sm">where</th><th>the statement says</th></tr></thead><tbody>';
    if(!(j.deposits||[]).length) h+='<tr><td colspan="4" class="mut">no cash deposits on record</td></tr>';
    (j.deposits||[]).forEach(function(d){
      var ic=d.status==="ok"?'<span class="ok">✓</span>':(d.status==="bad"?'<span class="bad">✗</span>':'<span class="mut">⏳</span>');
      h+='<tr><td>'+esc(d.day)+'</td><td class="num">₹'+esc(d.amount)+'</td><td class="hide-sm">'+esc(d.place)+'</td><td>'+ic+' '+esc(d.text)+'</td></tr>';
    });
    h+='</tbody></table></div>'+(st?'<div class="mut" style="font-size:12px">Statement '+esc(st.from_day)+' → '+esc(st.to_day)+' · opening ₹'+esc(st.opening)+' · closing ₹'+esc(st.closing)+' · loaded '+esc(st.loaded_at)+'. ':'')+
       '<a href="/finance/workbench">Load a newer statement (PDF) ↗</a></div></details>';
    var MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    var lab=MON[parseInt(BANK_YM.slice(5,7),10)-1]+" "+BANK_YM.slice(0,4);
    h+='<details class="mon"><summary>Pharmacy UPI (ICICI) <span class="mut" style="font-weight:400">· '+esc(lab)+': ₹'+esc(j.upi_total)+' over '+j.upi_days+' day(s)</span></summary>'+
       '<div class="row"><button class="ghost" onclick="bankShift(-1)">‹ earlier</button><b>'+esc(lab)+'</b><button class="ghost" onclick="bankShift(1)">later ›</button></div>'+
       '<div class="tblwrap"><table><thead><tr><th>day</th><th class="num">settled</th><th class="num">payments</th></tr></thead><tbody>';
    if(!(j.upi||[]).length) h+='<tr><td colspan="3" class="mut">no bank statement for this month</td></tr>';
    (j.upi||[]).forEach(function(u){h+='<tr class="dayrow" onclick="dayOpen[\''+u.date+'\']=true;renderDays();goCard(\'daysCard\')"><td>'+esc(u.day)+'</td><td class="num">₹'+esc(u.amount)+'</td><td class="num">'+u.payments+'</td></tr>'});
    h+='</tbody></table></div><div class="mut" style="font-size:12px">The bank\'s own settlement file, pharmacy account only. Tap a day to open it above.</div></details>';
    el.innerHTML=h;
  }).catch(function(){$("bank").innerHTML='<span class="mut">could not reach the server</span>'});
}
function bankShift(n){ var y=parseInt(BANK_YM.slice(0,4),10), m=parseInt(BANK_YM.slice(5,7),10)+n; if(m<1){m=12;y--} if(m>12){m=1;y++} loadBank(y+"-"+(m<10?"0":"")+m); }

/* ---- Month: sanjeevni_cash.month_rows, one Marg figure named for its days ---- */
function loadMonths(){
  fetch("/finance/sanjeevni/api/months?_="+Date.now(),{cache:"no-store"}).then(srvJSON).then(function(x){
    var j=x.j||{}; var el=$("months"); if(!j.ok){el.innerHTML='<span class="mut">'+esc(j.message||j.error||"could not load")+'</span>';return}
    var h='<div class="tblwrap"><table><thead><tr><th>month</th><th class="num">sale</th><th class="num hide-sm">online</th><th class="num hide-sm">cash</th><th class="num hide-sm">without cash</th><th class="num">banked</th><th></th></tr></thead><tbody>';
    (j.months||[]).slice().reverse().forEach(function(m){
      h+='<tr class="dayrow" onclick="var n=this.nextElementSibling;n.style.display=n.style.display===\'none\'?\'\':\'none\'"><td><b>'+esc(m.label)+'</b> <span class="sub">'+m.days+' days</span></td>'+
         '<td class="num">₹'+esc(m.sale)+'</td><td class="num hide-sm">₹'+esc(m.upi)+'</td><td class="num hide-sm">₹'+esc(m.cash)+'</td><td class="num hide-sm">₹'+esc(m.without_cash)+'</td><td class="num">₹'+esc(m.banked)+'</td><td class="mut">▸</td></tr>';
      h+='<tr style="display:none"><td colspan="7"><div class="sub" style="padding:4px 0 6px 12px;font-size:13px">'+
         'Home medicine ₹'+esc(m.home)+' · procedure medicine ₹'+esc(m.procedure)+' · other without cash ₹'+esc(m.other)+' · paid at the clinic counter ₹'+esc(m.elsewhere)+
         '<br>Cash income ₹'+esc(m.cash_income)+' · income with online ₹'+esc(m.income)+
         '<br>'+esc(m.marg_note)+(m.marg!=null?' — ₹'+esc(m.marg):'')+'</div></td></tr>';
    });
    h+='</tbody></table></div><div class="mut" style="font-size:12px">Sale, online and cash are the filed days (Marg and the bank since D354); banked is the pool\'s deposits to Yes Bank.</div>';
    el.innerHTML=h;
  }).catch(function(){$("months").innerHTML='<span class="mut">could not reach the server</span>'});
}
'''
s = rep(s, "\nload();\n/* S193_UX", tree_js + "\nload();\n/* S193_UX")

out = head + body + s + "</script></body></html>\n"
open(a.out, "w", encoding="utf-8").write(out)
print("built", len(out), hashlib.md5(out.encode("utf-8")).hexdigest())
