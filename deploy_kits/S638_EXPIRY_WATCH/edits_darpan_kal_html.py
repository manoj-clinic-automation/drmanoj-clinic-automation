# S638 anchored edits for /root/finance/darpan_kal.html (FROM 81dbb26a)
# D780: the order tab opens with the batches to sell first (Roman Hindi, as the owner approved it): batch and stock, nothing to tap.
EDITS = []
EDITS.append(('''function renderOrder(){
 const j=OJ, ro=OWNER_RO||j.me==="owner", can=j.editable&&!ro;   /* the owner reads: the answer says who asked (never the other fetch's timing) */
 let h="";''', '''function sellFirst(j){   /* S638 (D780): the batches Marg stops selling soon -- batch and stock, a do-this line, nothing to tap */
 const g=j.sell_first||[]; if(!g.length) return "";
 let s='<div class="ohead s638sf"><b>In batches ko pehle bechein</b>';
 g.forEach(x=>{s+='<div class="muted" style="margin-top:6px"><b>'+esc(x.label)+'</b></div>';
  (x.rows||[]).forEach(r=>{s+='<div class="row"><span class="k">'+esc(r.item)+'</span> <span style="font-family:monospace">'+esc(r.batch)+'</span> &middot; <b>'+esc(r.stock)+'</b></div>'})});
 return s+'</div>';
}
function renderOrder(){
 const j=OJ, ro=OWNER_RO||j.me==="owner", can=j.editable&&!ro;   /* the owner reads: the answer says who asked (never the other fetch's timing) */
 let h=sellFirst(j);'''))
