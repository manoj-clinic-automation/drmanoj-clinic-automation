/* ---- S939 (D1053): on Marg's sheet this tab is THE ONE LIST -- the old-line questions, reception's raises, सूची पक्की करो, what went.
   Every decision is two taps (no dialog); every answer is the tab again. ---- */
let D53ARM=null;
function d53btn(label,body,cls){return '<button class="btn sm d53 '+(cls||"")+'" onclick=\'d53two(this,'+oesc(JSON.stringify(body))+')\'>'+esc(label)+'</button>';}
function d53two(b,body){
 if(b.dataset.busy) return;
 if(D53ARM!==b){
  if(D53ARM&&D53ARM.isConnected){D53ARM.textContent=D53ARM.dataset.t;D53ARM.classList.remove("arm");}
  b.dataset.t=b.dataset.t||b.textContent; b.textContent=b.dataset.t+" — दोबारा दबाइए"; b.classList.add("arm"); D53ARM=b;
  setTimeout(()=>{if(D53ARM===b){b.textContent=b.dataset.t;b.classList.remove("arm");D53ARM=null;}},4000); return;
 }
 D53ARM=null; b.dataset.busy="1"; b.textContent="…"; d53post(body);
}
async function d53post(body){
 try{const j=await post(OU+"/d1053",body); OJ=j; renderOrder(); toast(body.do==="final"?"✓ सूची पक्की — रिसेप्शन WhatsApp भेज सकती है":"✓ हो गया");}
 catch(e){toast(""+e); loadOrder();}
}
function d1053Render(){
 const j=OJ, d=j.d1053;
 let h=sellFirst(j);
 if(j.frozen){el("order").innerHTML=h+sec('<span class="bad">दवा का ऑर्डर अभी बंद है</span>'); el("obar").style.display="none"; return;}
 if(!d.sheet.present) h+=sec('<span class="muted">आज की Marg सूची अभी नहीं आई।</span>');
 else h+='<div class="ohead" id="d53head"><b>Marg की सूची '+esc(d.sheet.at)+'</b> · '+d.sheet.suppliers+' सप्लायर · '+d.sheet.count+' दवाएँ</div>';
 const q=d.old.length+d.raised.length;
 if(q){
  let s='<div class="d53t">1 · पुरानी दवा — आपका फ़ैसला ('+q+')</div>';
  d.old.forEach(o=>{
   const b={do:"decide",kind:o.kind,ref:o.ref};
   s+='<div class="d53q" data-kind="'+esc(o.kind)+'" data-ref="'+esc(o.ref)+'"><div class="d53i">'+esc(o.item)+' · '+esc(o.qty)+'</div>'+
    '<div class="muted">'+esc(o.vendor)+' · ऑर्डर '+esc(o.day)+' · '+o.age+' दिन'+(o.note?' · '+esc(o.note):'')+'</div>'+
    (o.said?'<div class="d53said">रिसेप्शन ('+esc(o.said.by)+') ने भेजा '+esc(o.said.at)+' — "डीलर के पास नहीं"</div>':'')+
    '<div>'+d53btn("आज के ऑर्डर में जोड़ो",Object.assign({act:"add"},b),"primary")+d53btn("आउट ऑफ़ स्टॉक → डॉक्टर साहब",Object.assign({act:"na"},b),"d53w")+
    d53btn("अभी नहीं चाहिए",Object.assign({act:"later"},b),"")+'</div></div>';
  });
  d.raised.forEach(r=>{
   const b={do:"decide",qid:r.id};
   s+='<div class="d53q" data-qid="'+r.id+'"><div class="d53said">रिसेप्शन ('+esc(r.by)+') ने भेजा · '+esc(r.at)+'</div><div class="d53i">'+esc(r.item)+' · '+esc(r.qty)+'</div>'+
    '<div class="muted">'+esc(r.vendor)+' ने फ़ोन पर कहा: "अभी नहीं है"</div>'+
    '<div>'+d53btn("रहने दो, ऑर्डर में",Object.assign({act:"keep"},b),"primary")+d53btn("आउट ऑफ़ स्टॉक → डॉक्टर साहब",Object.assign({act:"na"},b),"d53w")+
    d53btn("इस बार हटाओ",Object.assign({act:"remove"},b),"")+'</div></div>';
  });
  h+='<div class="d53box" id="d53q">'+s+'</div>';
 }
 if(d.came_n||d.transit_n) h+=sec((d.came_n?'<div>✓ '+d.came_n+' पुरानी दवा आ चुकी थीं — बिल/Marg से अपने आप हटीं</div>':'')+
   (d.transit_n?'<div>✓ '+d.transit_n+' दवा रास्ते में — समय पर नहीं आईं तो यहाँ खुद दिखेंगी</div>':''));
 if(d.sheet.present){
  if(d.final) h+=sec('<span class="ok" id="d53final">✓ सूची पक्की '+esc(d.final.at)+' ('+esc(d.final.by)+') — रिसेप्शन WhatsApp भेज सकती है</span>');
  else h+=sec('<div class="d53t" style="color:#1c1c1c">2 · सूची पक्की करो</div><div class="muted">'+(q?'पहले ऊपर के '+q+' फ़ैसले। ':'')+'पक्की होते ही रिसेप्शन WhatsApp भेज सकेगी।</div>'+
   (q?'<button class="btn opk" id="d53fin" disabled>सूची पक्की करो ('+q+' फ़ैसले बाक़ी)</button>':d53btn("सूची पक्की करो",{do:"final"},"primary opk d53fin")));
 }
 if(d.cards.length){
  h+='<div class="ohead"><b>आज का ऑर्डर — '+d.cards.length+' सप्लायर</b> <span class="muted">(रिसेप्शन यही ऑर्डर करेगी)</span></div>';
  d.cards.forEach(c=>{
   h+='<details class="osup"><summary><b>'+esc(c.vendor)+'</b> · '+c.n+' दवा'+(c.state!=="pending"?' <span class="badge amber">WhatsApp लाइन में</span>':'')+'</summary>'+
    c.lines.map(l=>'<div class="oln"><div class="oit"><b>'+esc(l.item)+'</b>'+(l.raised?' <span class="badge amber">रिसेप्शन ने भेजा</span>':'')+'</div><div class="oqt"><b class="oq">'+esc(l.qty)+'</b></div></div>').join("")+'</details>';
  });
 }
 if(d.sent.length){
  h+='<details class="oflow" id="d53sent"><summary><b>भेजा गया — माल आने तक ('+d.sent.length+')</b></summary>'+
   d.sent.map(s=>'<div class="ofl"><b>'+esc(s.vendor)+'</b> · '+s.n+' दवा<div class="ok">'+esc(s.word)+'</div>'+(s.due?'<div class="'+(s.late?'amber':'muted')+'">'+(s.late?'लेट — '+esc(s.due)+' तक आना था':'माल '+esc(s.due)+' शाम तक')+'</div>':'')+'</div>').join("")+'</details>';
 }
 h+=oflowHtml();
 el("order").innerHTML=h; el("obar").style.display="none";
}
