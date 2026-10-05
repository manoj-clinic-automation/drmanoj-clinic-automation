
/* ---- S485 (D677): आज का ऑर्डर -- Darpan reviews the system's list: hold, add, − / +, पक्का. The tab fetches its own API; a failure
   here never touches कल का हिसाब. No reload on a tap: every answer is the day's list again, and the open blocks stay open. ---- */
const OU="/finance/darpan/kal/api/order";
const OWD=["रवि","सोम","मंगल","बुध","गुरु","शुक्र","शनि"];
let OTAB=false, OJ=null, OOPEN={}, OWNER_RO=false, OADD=null;
function showTab(order){
 OTAB=order; el("tabKal").classList.toggle("on",!order); el("tabOrder").classList.toggle("on",order); document.body.classList.toggle("otab",order);
 el("body").style.display=order?"none":""; el("order").style.display=order?"":"none"; el("pick").style.visibility=order?"hidden":"";
 if(order) loadOrder(); else el("obar").style.display="none";
}
el("tabKal").onclick=()=>showTab(false); el("tabOrder").onclick=()=>showTab(true);
const oesc=s=>esc(s).replace(/'/g,"&#39;");
function oqty(q,unit){return q+" "+(unit==="strip"?"पत्ता":"नग");}
function odate(iso){const d=new Date(iso+"T00:00:00");return OWD[d.getDay()]+" "+iso.slice(8,10)+"-"+iso.slice(5,7)+"-"+iso.slice(0,4);}
function otime(t){return (t||"").replace(/^0/,"");}
async function loadOrder(){
 if(!OJ) el("order").innerHTML=sec('<span class="muted">सूची खुल रही है…</span>');
 try{const r=await fetch(OU+"?_="+Date.now(),{cache:"no-store"}); const j=await r.json(); if(!r.ok||!j.ok) throw 0; OJ=j; renderOrder();}
 catch(e){OJ=null; el("order").innerHTML=sec('<span class="amber">सूची अभी नहीं खुली — थोड़ी देर में फिर देखिए</span>'); el("obar").style.display="none";}
}
async function otap(path,body){
 try{const j=await post(OU+path,body); OJ=j; renderOrder(); return j;}catch(e){toast(""+e); loadOrder(); return null;}
}
function oline(l,can){
 const shelf=l.on_hand_text===""?"":(l.days_left===0?'शेल्फ '+esc(l.on_hand_text)+' · <span class="bad">खत्म</span>':'शेल्फ '+esc(l.on_hand_text)+(l.days_left!=null?' · ~'+l.days_left+' दिन':''));
 const key=oesc(JSON.stringify({pid:l.pid,item:l.item}));
 let h='<div class="oln'+(l.held?' held':'')+'"><div class="oit"><b>'+esc(l.item)+'</b> <span class="muted">'+esc(l.packing)+'</span>'+(l.added?' <span class="badge ok">जोड़ी</span>':'')+
  '<div class="muted">'+(l.held?'इस बार नहीं':shelf)+'</div></div><div class="oqt">';
 if(l.held) h+=(can?'<span class="btn sm" onclick=\'otap("/hold",Object.assign('+key+',{hold:false}))\'>वापस लो</span>':'');
 else{
  h+=(can?'<span class="btn pm" onclick=\'otap("/qty",Object.assign('+key+',{dir:-1}))\'>−</span>':'')+'<b class="oq">'+oqty(l.qty,l.unit)+'</b>'+
   (can?'<span class="btn pm" onclick=\'otap("/qty",Object.assign('+key+',{dir:1}))\'>+</span>':'');
  if(can) h+='<div><span class="btn sm" onclick=\'otap("/hold",Object.assign('+key+',{hold:true}))\'>नहीं चाहिए</span></div>';
 }
 return h+'</div></div>';
}
function renderOrder(){
 const j=OJ, ro=OWNER_RO||j.me==="owner", can=j.editable&&!ro;   /* the owner reads: the answer says who asked (never the other fetch's timing) */
 let h="";
 if(j.source!=="darpan") h+=sec('<span class="amber">'+(j.source==="marg_sheet"?'अभी मार्ग की शीट से ऑर्डर हो रहा है':'अभी ऑर्डर इस पेज से नहीं हो रहा है')+'</span>');
 if(j.frozen) h+=sec('<span class="bad">दवा का ऑर्डर अभी बंद है</span>');
 else if(!j.opened) h+=sec('<div class="row"><span class="k">आज की सूची '+esc(otime(j.list_time))+' बजे आएगी।</span></div>');
 else if(!j.suppliers.length) h+=sec('<div class="row"><span class="k">आज कोई ऑर्डर नहीं बनता।</span></div>');
 else{
  const od=j.order_day_names||[];
  h+='<div class="ohead"><b>'+esc(odate(j.date))+'</b> · '+j.n_suppliers+' सप्लायर · '+j.n_lines+' दवा'+
   (od.length?'<div class="muted">'+(od.length<=3?'आज '+esc(od.join(", "))+' का दिन':'आज '+od.length+' सप्लायर का दिन')+'</div>':'')+'</div>';
  if(j.all_pakka) h+=sec('<span class="ok">सब पक्का — रिसेप्शन ऑर्डर करेगी।</span>');
  j.suppliers.forEach(b=>{
   const open=b.status==="open", sn=b.supplier_norm;
   if(!(sn in OOPEN)) OOPEN[sn]=open||ro;   /* a reader sees every block open; Darpan's fold once they are पक्का */
   h+='<details class="osup" data-sn="'+esc(sn)+'"'+(OOPEN[sn]?' open':'')+' ontoggle="if(this.isConnected)OOPEN[this.dataset.sn]=this.open"><summary><b>'+esc(b.display)+'</b> · '+b.n+' दवा'+
    (b.order_day?' <span class="badge amber">आज का दिन</span>':'')+
    (b.status==="darpan_ok"?' <span class="ok ost">✓ पक्का — रिसेप्शन को गया '+esc(b.pakka_at)+'</span>':'')+
    (b.status==="sent"?' <span class="ok ost">✓ ऑर्डर हो गया '+esc(b.sent_at)+'</span>':'')+
    (ro&&b.pakka_at?'<div class="muted">Darpan ने पक्का किया '+esc(b.pakka_at)+'</div>':'')+'</summary>'+
    b.lines.map(l=>oline(l,can&&open)).join("")+
    (can&&open?'<button class="btn primary opk" onclick=\'opakka('+oesc(JSON.stringify(sn))+')\'>पक्का</button>':'')+'</details>';
  });
 }
 const y=j.yesterday||[];
 if(y.length){
  const W={arrived:s=>'ऑर्डर हो गया '+esc(s.at)+' · <span class="ok">माल आया ✓</span>',ordered:s=>'ऑर्डर हो गया '+esc(s.at)+' · <span class="amber">अभी नहीं आया</span>',
   no_answer:s=>'<span class="amber">फ़ोन नहीं उठा — रिसेप्शन फिर करेगी</span>',not_ordered:s=>'<span class="amber">ऑर्डर बाकी</span>'};
  h+='<details class="oyest"><summary>कल के ऑर्डर — क्या हुआ ('+y.length+')</summary><table>'+y.map(s=>'<tr><td>'+esc(s.display)+'</td><td>'+(W[s.state]||W.ordered)(s)+'</td></tr>').join("")+'</table></details>';
 }
 el("order").innerHTML=h;
 const anyOpen=j.suppliers.some(b=>b.status==="open");
 el("obar").style.display=(OTAB&&can)?"flex":"none";
 el("oall").style.display=anyOpen?"":"none";
}
/* the fold is set AFTER the answer: a toggle event of the blocks drawn before the tap can land while the tap is in flight */
async function opakka(sn){const j=await otap("/pakka",{supplier_norm:sn}); if(j){OOPEN[sn]=false; renderOrder(); toast("✓ पक्का — रिसेप्शन को गया");}}
async function opakkaAll(){if(!OJ) return; const j=await otap("/pakka",{all:true}); if(j){OJ.suppliers.forEach(b=>{OOPEN[b.supplier_norm]=false;}); renderOrder(); toast("सब पक्का — रिसेप्शन ऑर्डर करेगी।");}}
/* the add sheet: three letters of a name, then a tap; a medicine never bought asks for its supplier */
function oaddOpen(){OADD=null; el("osheet").style.display="block"; el("oq").value=""; el("ohits").innerHTML=""; el("oq").focus();}
function oaddClose(){el("osheet").style.display="none";}
let OQT=null;
function oaddType(){clearTimeout(OQT); OQT=setTimeout(oaddFind,250);}
async function oaddFind(){
 const q=el("oq").value.trim(); OADD=null;
 if(q.length<3){el("ohits").innerHTML=""; return;}
 try{const r=await fetch(OU+"/items?q="+encodeURIComponent(q)+"&_="+Date.now(),{cache:"no-store"}); const j=await r.json(); if(!j.ok) throw 0;
  window.OCHIPS=j.chips||[];
  el("ohits").innerHTML=j.hits.length?j.hits.map((x,i)=>'<div class="ohit" id="ohit'+i+'" onclick=\'oaddPick('+i+','+oesc(JSON.stringify(x))+')\'><b>'+esc(x.item)+'</b> <span class="muted">'+esc(x.packing)+'</span>'+
   '<div class="muted">'+(x.supplier?esc(x.supplier)+' · '+oqty(x.qty,x.unit):'<span class="amber">सप्लायर चुनिए</span>')+'</div><div class="ochips" id="ochips'+i+'"></div></div>').join(""):'<div class="muted">इस नाम की दवा नहीं मिली</div>';
 }catch(e){el("ohits").innerHTML='<div class="amber">सूची अभी नहीं खुली — थोड़ी देर में फिर देखिए</div>';}
}
async function oaddPick(i,x){
 if(x.supplier_norm){const j=await otap("/add",{item:x.item}); if(j){oaddClose(); OOPEN[j.added.supplier_norm]=true; renderOrder(); toast("जोड़ी — "+x.item);} return;}
 el("ochips"+i).innerHTML=(window.OCHIPS||[]).map(c=>'<span class="btn sm" onclick=\'event.stopPropagation();oaddWith('+oesc(JSON.stringify(x.item))+','+oesc(JSON.stringify(c.supplier_norm))+')\'>'+esc(c.display)+'</span>').join("");
}
async function oaddWith(item,sn){const j=await otap("/add",{item:item,supplier_norm:sn}); if(j){oaddClose(); OOPEN[sn]=true; renderOrder(); toast("जोड़ी — "+item);}}
