# -*- coding: utf-8 -*-
"""edits_s741.py -- S741_STATIONERY_PRODUCT_PICK (F-1160): the counted edits on /root/assetapp/stationery.py (S735's TO, 2abbc10a).

The Stationery page's product box was a browser datalist that does not open on the owner's device (typing worked). Every product box
and unit box of the sorting form (his Stationery page: To sort and Change; the staff Stationery sort page) becomes a searchable list,
as on the sorting desk (S715): tap or type, the matching products drop down, one tap picks. The box stays a plain text box with the
same name, so a name not on the list is still added on Save exactly as today. No server rule changes; no data step.
Each anchor must occur exactly once in the FROM file (make_s741.py refuses otherwise).
"""

EDITS = []


def E(name, old, new):
    EDITS.append((name, (old, new)))


E("1 the kit marker",
  'STMT_LAST = "S735"                     # S735_STMT_LAST_MONTH: the page offers the month just ended first\n',
  'STMT_LAST = "S735"                     # S735_STMT_LAST_MONTH: the page offers the month just ended first\n'
  'PICK_S741 = "S741"                     # S741_STATIONERY_PRODUCT_PICK (F-1160): the product and unit boxes a searchable list\n')

E("2 the searchable list on the sorting form",
  '@media(max-width:600px){.s674 .ln{grid-template-columns:1fr 1fr}.s674 .ln.h{display:none}}\n</style>"""',
  '@media(max-width:600px){.s674 .ln{grid-template-columns:1fr 1fr}.s674 .ln.h{display:none}}\n'
  '.pk741{position:relative;display:block;max-width:300px}.pk741.u{max-width:100px}.pk741 input{width:100%;box-sizing:border-box}\n'
  '.dd741{position:absolute;left:0;right:0;top:100%;z-index:30;background:#fff;border:1px solid #b9c3cd;border-radius:6px;'
  'box-shadow:0 6px 18px rgba(20,30,40,.15);max-height:260px;overflow-y:auto;min-width:180px}\n'
  '.o741{display:block;width:100%;text-align:left;font:inherit;font-size:14px;padding:9px 10px;border:0;border-bottom:1px solid #edf0f3;'
  'background:#fff;color:#1f2a36;cursor:pointer;min-height:40px}.o741:hover{background:#eaf2fa}.o741.nw{color:#5e6a63;cursor:default;font-size:13px}\n'
  '</style>\n'
  '<script>/* S741 (F-1160): the product and unit boxes -- a searchable list in place of the datalist */\n'
  '(function(){var STAFF=location.pathname.indexOf("/stationery/sort")>=0;\n'
  'function esc(s){return String(s==null?"":s).replace(/[&<>"\']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c];});}\n'
  'function go(){var L={};Array.prototype.forEach.call(document.querySelectorAll("datalist#s674items,datalist#s568units"),function(d){\n'
  '  L[d.id]=Array.prototype.map.call(d.options,function(o){return o.value;}).filter(function(v){return v;});});\n'
  ' Array.prototype.forEach.call(document.querySelectorAll("form.s674 input[list=s674items],form.s674 input[list=s568units]"),function(inp){\n'
  '  var id=inp.getAttribute("list"),opts=L[id]||[],prod=(id=="s674items");inp.removeAttribute("list");inp.setAttribute("autocomplete","off");inp.setAttribute("data-s741",id);\n'
  '  var w=document.createElement("span");w.className="pk741"+(prod?"":" u");inp.parentNode.insertBefore(w,inp);w.appendChild(inp);\n'
  '  var dd=document.createElement("div");dd.className="dd741";dd.style.display="none";w.appendChild(dd);\n'
  '  function draw(){var v=inp.value.trim(),q=v.toLowerCase(),h="",n=0,exact=false;\n'
  '   var M=opts.filter(function(o){var l=o.toLowerCase();if(l==q){exact=true;}return !q||l.indexOf(q)>=0;});\n'
  '   M.sort(function(a,b){return (a.toLowerCase().indexOf(q)==0?0:1)-(b.toLowerCase().indexOf(q)==0?0:1)||a.localeCompare(b);});\n'
  '   M.slice(0,15).forEach(function(o){h+="<button type=button class=o741 data-v=\'"+esc(o)+"\'>"+esc(o)+"</button>";n++;});\n'
  '   if(prod&&q&&!exact){h+="<div class=\'o741 nw\'>"+(STAFF?"Naya saamaan \\u201c"+esc(v)+"\\u201d \\u2014 Save par list mein judega":"\\u201c"+esc(v)+"\\u201d is not on the list \\u2014 it is added on Save")+"</div>";n++;}\n'
  '   dd.innerHTML=h;dd.style.display=n?"block":"none";}\n'
  '  inp.addEventListener("focus",draw);inp.addEventListener("input",draw);\n'
  '  inp.addEventListener("blur",function(){setTimeout(function(){dd.style.display="none";},200);});\n'
  '  dd.addEventListener("mousedown",function(e){var t=e.target.closest?e.target.closest("[data-v]"):null;e.preventDefault();if(!t){return;}\n'
  '   inp.value=t.getAttribute("data-v");dd.style.display="none";inp.dispatchEvent(new Event("change",{bubbles:true}));});});}\n'
  'if(document.readyState=="loading"){document.addEventListener("DOMContentLoaded",go);}else{go();}})();</script>"""')
