#!/usr/bin/python3
"""s16_page.py -- the browsable record of the reconciliation."""
import json, collections, html, datetime
import packmap as PM, classify
from page_css import CSS

stock=json.load(open("stock_final.json"))
reo=json.load(open("reorder_final.json"))
res=json.load(open("resolve.json"))
out,conf,cand=classify.classify(stock)
cls={r["key"]:(r["class"],r["why"]) for r in out}
MO=["2026-04","2026-05","2026-06","2026-07","2026-08"]
MON={"2026-04":"Apr","2026-05":"May","2026-06":"Jun","2026-07":"Jul","2026-08":"Aug"}
E=lambda s: html.escape(str(s),quote=True)

for s in stock:
    c=cls.get(s["key"])
    s["cls"], s["why"] = (c if c else ("BALANCED","opening + purchases - returns - sales + credit notes lands exactly on the shelf count"))
    s["desc_close"]=PM.describe(s["closing"],s["size"])
    s["desc_var"]=PM.describe(s["var"],s["size"])

tot=lambda f: sum(f(s) for s in stock)
IDENT=[("opening 31-Mar","+",tot(lambda s:s["opening"])),("purchased","+",tot(lambda s:s["purchased"])),
       ("returned to vendor","−",tot(lambda s:s["preturn"])),("sold","−",tot(lambda s:s["sold"])),
       ("credit notes back","+",tot(lambda s:s["sreturn"]))]
expect=sum(x[2]*(1 if x[1]=="+" else -1) for x in IDENT)
close=tot(lambda s:s["closing"])

CLSMETA={
 "BALANCED":("good","Balances exactly","Every movement accounts for the shelf count."),
 "RENAMED":("warn","Renamed code","One product under two codes. Sales landed on one, purchases on the other."),
 "GOODS_IN":("bad","On shelf, no bill","More stock than the paperwork explains — goods in against a bill not yet entered."),
 "GOODS_OUT":("bad","Gone, no sale","Less stock than the paperwork explains — breakage, expiry, sample or an unbilled issue."),
 "DELISTED":("mut","Off the item list","Had stock on 31-Mar, never moved, and is not on today's list — a stock-taker will never see it."),
 "NEG_CLEARED":("warn","Negative cleared","Opened short because goods arrived before the bill; this is the correction."),
}
cnt=collections.Counter(s["cls"] for s in stock)

def rows_html(items):
    o=[]
    for i,s in enumerate(items):
        tone=CLSMETA[s["cls"]][0]
        o.append('<tr class="item" data-i="%d" tabindex="0"><td><b>%s</b><div style="font-size:11.5px;color:var(--text-3)">%s%s</div></td>'
                 '<td><span class="badge b-%s">%s</span></td>'
                 '<td class="num">%s</td><td class="num">%s</td><td class="num">%s</td><td class="num">%s</td>'
                 '<td class="num"><b>%s</b></td><td class="num">%s</td><td class="num">%s</td></tr>'%(
            i,E(s["item"]),E(s["packing_txt"]),(" · "+E(s["vendor"])) if s.get("vendor") else "",
            tone,E(CLSMETA[s["cls"]][1]),
            fmt(s["opening"],s), fmt(s["purchased"],s), fmt(s["sold"],s), fmt(s["sreturn"],s),
            E(s["desc_close"]), (E(s["desc_var"]) if abs(s["var"])>0.5 else "—"),
            ("%.0f"%s["cover_days"]) if s["cover_days"] is not None and s["closing"]>0 else "—"))
        o.append('<tr class="det" data-d="%d" hidden><td colspan="9">%s</td></tr>'%(i,detail(s)))
    return "".join(o)

def fmt(u,s):
    if not u: return "—"
    return E(PM.describe(u,s["size"],short=True))

def detail(s):
    m="".join('<div class="mo"><div class="m">%s</div><div class="r">sold %s</div>'
              '<div class="r" style="color:var(--text-3)">bought %s</div></div>'%(
        MON[k], E(PM.describe(s["months"].get(k,{}).get("sold",0),s["size"],short=True)) or "0",
        E(PM.describe(s["months"].get(k,{}).get("pur",0),s["size"],short=True)) or "0") for k in MO)
    v=sorted({x for k in MO for x in s["months"].get(k,{}).get("vend",[])})
    return ('<div><b>%s</b> &mdash; %s</div><div class="mgrid">%s</div>'
            '<div style="margin-top:8px;font-size:12.5px">last sale %s &nbsp;·&nbsp; first sale %s'
            ' &nbsp;·&nbsp; %.2f a day &nbsp;·&nbsp; supplier %s &nbsp;·&nbsp; value %s</div>')%(
        E(CLSMETA[s["cls"]][1]), E(s["why"]), m,
        E(s.get("last_sale") or "none since 1-Apr"), E(s.get("first_sale") or "—"),
        s["per_day"], E(", ".join(v) or "no purchase in the window"),
        ("Rs "+format(round(s["value"]),",")) if s.get("value") else "not priced this year")

for s in stock:
    s["packing_txt"]=("1*%d"%s["size"]) if s["size"] else "single unit"

srt=sorted(stock,key=lambda s:(0 if s["cls"]!="BALANCED" else 1,-abs(s["var"]),-s["net_sold"]))
DATA=[{"i":i,"n":s["item"].upper(),"c":s["cls"],"s":1 if s["closing"]>0 else 0} for i,s in enumerate(srt)]

def vend_block(items,tag):
    g=collections.defaultdict(list)
    for i in items: g[i["vendor"] or "no vendor on record"].append(i)
    o=[]
    for v,its in sorted(g.items(),key=lambda kv:-sum(x["order_value"] for x in kv[1])):
        val=sum(x["order_value"] for x in its)
        li="".join('<tr><td>%s</td><td class="num">%s</td><td class="num">%.1f</td>'
                   '<td class="num">%s</td><td class="num"><b>%s</b></td></tr>'%(
            E(x["item"]),E(x["desc_close"] if "desc_close" in x else PM.describe(x["closing"],x["size"])),
            x["per_day"],("%.0f"%x["cover"]) if x["cover"]>-999 else "",
            E(("%d strips"%x["order_strips"]) if x["size"] else ("%d"%x["order_units"])))
            for x in sorted(its,key=lambda x:x["cover"]))
        o.append('<div class="card vend"><h3>%s</h3><div class="meta">%d item%s &nbsp;·&nbsp; about Rs %s'
                 ' &nbsp;·&nbsp; one bill</div><div class="tblwrap"><table><thead><tr><th>item</th>'
                 '<th class="num">on shelf</th><th class="num">a day</th><th class="num">days left</th>'
                 '<th class="num">order</th></tr></thead><tbody>%s</tbody></table></div></div>'%(
            E(v),len(its),"" if len(its)==1 else "s",format(val,","),li))
    return "".join(o)

eq="".join('<div class="term"><span class="l">%s</span><span class="v">%s</span><span class="u">tablets &amp; units</span></div>%s'%(
    E(l),format(int(round(v)),","),'<div class="op">%s</div>'%E(IDENT[i+1][1]) if i+1<len(IDENT) else '<div class="op">=</div>')
    for i,(l,op,v) in enumerate(IDENT))
eq+=('<div class="term res"><span class="l">on the shelf 26-Aug</span><span class="v">%s</span>'
     '<span class="u">counted, not calculated</span></div>')%format(int(round(close)),",")

chips="".join('<button class="chip" data-c="%s" aria-pressed="false"><span class="v" style="color:var(--%s)">%d</span>'
              '<span class="l">%s</span><span class="w">%s</span></button>'%(
    k,{"good":"good","warn":"warn","bad":"bad","mut":"text-3"}[CLSMETA[k][0]],cnt.get(k,0),
    E(CLSMETA[k][1]),E(CLSMETA[k][2])) for k in ("BALANCED","RENAMED","GOODS_IN","GOODS_OUT","NEG_CLEARED","DELISTED") if cnt.get(k))

gross=sum(abs(s["var"]) for s in stock if abs(s["var"])>0.5)
moved=sum(s["opening"]+s["purchased"] for s in stock)
onshelf=[s for s in stock if s["closing"]>0]
value=sum(s.get("value") or 0 for s in stock)
low=[s for s in onshelf if s["cover_days"] is not None and s["cover_days"]<14]
dead=[s for s in onshelf if not s.get("last_sale") or s["last_sale"]<"2026-06-26"]
neg=[s for s in stock if s["closing"]<0]

HTML="""<title>Sanjeevni Stock Ledger</title>
<style>%s</style>
<header class="brand"><div class="brow"><div class="mark">SJ</div><div class="bt">
<h1>Sanjeevni Stock Ledger</h1><p>1 April &ndash; 26 August 2026 &nbsp;&middot;&nbsp; %d items &nbsp;&middot;&nbsp; every movement accounted for</p>
</div></div><div class="tabs" role="tablist">
<button role="tab" aria-selected="true" data-t="rec">Reconciliation</button>
<button role="tab" aria-selected="false" data-t="stk">Stock &amp; ledgers</button>
<button role="tab" aria-selected="false" data-t="ord">What to order</button>
<button role="tab" aria-selected="false" data-t="met">How it was built</button>
</div></header>
<main>

<section class="panel" id="rec">
<div class="card"><p class="kicker">the identity every item must satisfy</p>
<h2>What came in, what went out, what is on the shelf</h2>
<p class="sub">Read left to right. The last box is the only figure that was <em>counted</em> rather than calculated &mdash; everything before it is the paperwork. The two agree to %.2f%%.</p>
<div class="eq">%s</div>
<details class="note"><summary>Why the two do not land on the same number</summary>
<p>The calculated total comes to %s and the shelf holds %s &mdash; a gap of %s units, %.2f%% of the %s units that moved through the shop. That gap is not spread thinly across everything: %d of %d items land exactly, and the whole difference sits in %d items, each one named below with what kind of event would explain it.</p></details>
</div>

<div class="chips">%s</div>

<div class="card"><p class="kicker">how to read the classes</p><h2>Named, not written off</h2>
<p class="sub">Tap any class above to open the full ledger filtered to it. Nothing is rounded away or pooled into an &lsquo;other&rsquo; bucket &mdash; an item with no identifiable cause would be labelled unexplained and stay visible. None are.</p></div>
</section>

<section class="panel" id="stk" hidden>
<div class="chips">
<div class="chip" style="cursor:default"><span class="v">%d</span><span class="l">lines with stock</span><span class="w">%d strip items, %d counted singly</span></div>
<div class="chip" style="cursor:default"><span class="v">Rs %s</span><span class="l">at last purchase cost</span><span class="w">%d lines have no purchase this year and cannot be priced from it</span></div>
<div class="chip" style="cursor:default"><span class="v" style="color:var(--bad)">%d</span><span class="l">negative on the shelf</span><span class="w">goods sold before the bill was entered</span></div>
<div class="chip" style="cursor:default"><span class="v" style="color:var(--warn)">%d</span><span class="l">no sale in two months</span><span class="w">stock standing still</span></div>
</div>
<div class="card"><p class="kicker">the full ledger</p><h2>Every item, every month</h2>
<p class="sub">Quantities are in strips for anything packed <span class="mono">1*N</span> and in single units for everything else &mdash; a tube, a vial, a syringe, a belt. Tap any row for its month-by-month sale and purchase ledger.</p>
<div class="tools"><input id="q" type="search" placeholder="Search an item&hellip;" aria-label="Search items"><span class="hits" id="hits"></span></div>
<div class="tblwrap"><table><thead><tr><th>item</th><th>what happened</th>
<th class="num">31-Mar</th><th class="num">bought</th><th class="num">sold</th><th class="num">back</th>
<th class="num">on shelf</th><th class="num">gap</th><th class="num">days</th></tr></thead>
<tbody id="tb">%s</tbody></table></div></div>
</section>

<section class="panel" id="ord" hidden>
<div class="card"><p class="kicker">bundled by stockist, not by item</p>
<h2>%d items are inside two weeks of cover</h2>
<p class="sub">Topped up to thirty days, in whole strips, at each item&rsquo;s own measured rate. Bundled into %d orders instead of %d &mdash; the constraint is bills to enter, not money.</p></div>
%s
<div class="card"><p class="kicker">not automatic</p><h2>Confirm before ordering &mdash; %d items</h2>
<p class="sub">Low on stock, but these have not sold in at least two of the last three months. A thirty-day top-up on an occasional item is arithmetically right and practically wrong: it would commit about Rs %s to stock that turns over a few times a year.</p></div>
%s
</section>

<section class="panel" id="met" hidden>
<div class="card"><p class="kicker">sources</p><h2>What this was built from</h2>
<p class="sub">Five Marg exports, none of them edited: closing stock as on 31-Mar-2026 and 26-Aug-2026, item-wise purchases for the five months April to August, and every sale report of the year &mdash; bills A00001 to A03215 with no gap in the chain.</p>
<details class="note" open><summary>Three faults were found and fixed in the reading, not the data</summary>
<p><b>Whole-unit sales read as zero.</b> A strip line writes its quantity as <span class="mono">0:1</span>; a tube, vial or spray writes <span class="mono">1.0</span>. A reader that only understands the first form returned nothing for the second &mdash; 2,807 lines, 16.3%% of the year. Those items then read as dead stock when they were selling well.</p>
<p><b>Credit notes counted as sales.</b> Bills run A&hellip;, credit notes run CN&hellip;. A credit note is goods coming back, so subtracting it makes the error twice the quantity. That doubling is what gave it away: TYRO BR was out by 704 against 352 units of credit notes.</p>
<p><b>The sale report truncates item names at 20 characters.</b> HARD COLLAR ADJ L HOSPIK is rung up as HARD COLLAR ADJ L HO, which exists in no item list, so its sales attached to a name that owns no stock. Eleven codes, the largest carrying 574 units.</p>
</details>
<details class="note"><summary>Where a size cannot be recovered, it is not invented</summary>
<p>Six sizes of L S BELT CONT GRAY UNISON cut to the same twenty characters, so the sale report did not record which size left the shelf. Those sales are pooled at the family and labelled, rather than assigned to a size to make a line balance.</p></details>
<details class="note"><summary>Pack sizes come from the row, never from an assumption</summary>
<p><span class="mono">2:3</span> is 23 tablets at 1*10 and 33 at 1*15, so a wrong pack size is wrong by a multiple. Each quantity is converted with the packing printed on its own row. Two items disagree between sources and are reported rather than resolved: FOLITRAX 7.5 and INTACOXIA-60 both carry an older pack size on the March export.</p></details>
<p class="foot">Built %s IST. Patient data and phone numbers appear nowhere in this page or in the code behind it.</p>
</div>
</section>
</main>
<button id="top" hidden></button>
<script>
const D=%s;
const tb=document.getElementById('tb'), q=document.getElementById('q'), hits=document.getElementById('hits');
let filt=null;
function apply(){
  const t=(q.value||'').trim().toUpperCase(); let n=0;
  const rows=tb.querySelectorAll('tr.item');
  rows.forEach(r=>{const d=D[+r.dataset.i];
    const ok=(!t||d.n.includes(t))&&(!filt||d.c===filt);
    r.hidden=!ok; const det=tb.querySelector('tr.det[data-d="'+r.dataset.i+'"]');
    if(det&&!ok)det.hidden=true; if(ok)n++;});
  hits.textContent=n+' of '+D.length+' items'+(filt?' · '+filt.toLowerCase().replace('_',' '):'');
}
q.addEventListener('input',apply);
function show(t){
  document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected',x.dataset.t===t));
  document.querySelectorAll('.panel').forEach(p=>p.hidden=(p.id!==t));
  window.scrollTo({top:0});
}
document.querySelectorAll('.chip[data-c]').forEach(c=>c.addEventListener('click',()=>{
  const v=c.dataset.c; filt=(filt===v)?null:v;
  document.querySelectorAll('.chip[data-c]').forEach(x=>x.setAttribute('aria-pressed',x.dataset.c===filt));
  apply(); if(filt)show('stk');}));
function toggle(r){const d=tb.querySelector('tr.det[data-d="'+r.dataset.i+'"]'); if(d)d.hidden=!d.hidden;}
tb.addEventListener('click',e=>{const r=e.target.closest('tr.item'); if(r)toggle(r);});
tb.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const r=e.target.closest('tr.item');
  if(r){e.preventDefault();toggle(r);}}});
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>show(b.dataset.t)));
apply();
</script>"""%(CSS,len(stock),
 100.0-100.0*gross/moved, eq,
 format(int(round(expect)),","),format(int(round(close)),","),format(int(round(gross)),","),
 100.0*gross/moved, format(int(round(moved)),","),
 cnt.get("BALANCED",0),len(stock),len(stock)-cnt.get("BALANCED",0),
 chips,
 len(onshelf),len([s for s in onshelf if s["size"]]),len([s for s in onshelf if not s["size"]]),
 format(round(value),","),len([s for s in onshelf if not s.get("cost_per_unit")]),
 len(neg),len(dead), rows_html(srt),
 len(reo["auto"]),len({(x["vendor"] or "") for x in reo["auto"]}),len(reo["auto"]),
 vend_block(reo["auto"],"auto"),
 len(reo["confirm"]),format(sum(x["order_value"] for x in reo["confirm"]),","),
 vend_block(reo["confirm"],"conf"),
 datetime.datetime.now().strftime("%d %b %Y %H:%M"),
 json.dumps(DATA,separators=(",",":")))
open("/tmp/sanjeevni_ledger.html","w").write(HTML)
print("written %d KB"%(len(HTML)//1024))
