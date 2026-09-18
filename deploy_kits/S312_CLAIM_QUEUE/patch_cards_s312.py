#!/usr/bin/env python
"""S312_CLAIM_QUEUE -- the two screens.  One patcher, two files, each anchored,
idempotent and refusing on drift:

  darpan_card.html  a new section "8 . Stock ke sawaal" -- what Darpan is being
                    asked, with the evidence, and his five taps.  It loads on
                    its own and hides itself when there is nothing to ask, so a
                    quiet day looks exactly as it did before S312.
  stock_hub.html    step 8 gains what it never had: the answers coming back, and
                    the owner's settle tap.  The step can now reach DONE.
"""
import argparse
import hashlib
import os
import shutil
import sys

MARK = "S312_CLAIM_QUEUE"

# ------------------------------------------------------------ Darpan's card
CARD_SEC_OLD = '''<div id="msg"></div>
<script>
'''
CARD_SEC_NEW = '''<!-- S312_CLAIM_QUEUE: stock ke sawaal, evidence ke saath -->
<div class="sec" id="claimSec" style="display:none">
 <div class="row"><span class="k">\u2753 8 \u00b7 Stock ke sawaal</span><span class="v" id="claimN">\u2014</span></div>
 <div class="muted">Stock check mein jo cheezein kam mili, doctor sahab ne unke
 baare mein poochha hai. Neeche har cheez ke saath wahi hai jo computer pehle se
 jaanta hai \u2014 kitna bika, kab bika. Jo aapko yaad ho wahi tap kijiye; yaad na
 ho to <b>Pata nahin</b> bilkul theek jawab hai.</div>
 <div id="claimList"></div>
</div>
<div id="msg"></div>
<script>
'''

CARD_JS_OLD = '''/* S210_HANDOVER -- the three routes out of the drawer and the RETURN leg,
   recorded where the cash actually moves: at the counter, by Darpan. */
'''
CARD_JS_NEW = '''/* S312_CLAIM_QUEUE (D471) -- the stock questions, asked with the evidence in
   hand.  A line arrives here only because the owner marked it "to pursue" on
   the hub; S308 put the thirty-day sale evidence on it.  Darpan taps one of
   five answers -- open becomes contacted -- and that is as far as he can go:
   the owner settles.  "Pata nahin" is offered first-class on purpose, because
   a guessed answer is worse than an honest blank in a record like this. */
const CLAIM_ANS=[["sold_no_bill","Bina bill ke gaya"],["returned_supplier","Supplier ko wapas gaya"],
                 ["found","Mil gaya"],["damaged","Toota / kharab"],["not_known","Pata nahin"]];
async function loadClaims(){
 try{
  const r=await fetch("/finance/darpan/api/claims?_="+Date.now(),{cache:"no-store"});
  const j=await r.json();
  if(!j.ok||!j.available||!j.claims.length){el("claimSec").style.display="none";return;}
  el("claimSec").style.display="";
  el("claimN").textContent=j.claims.length;
  let h="";
  for(const c of j.claims){
   const ev=(c.candidate?'<div class="muted">'+esc2(c.candidate)+'</div>':'');
   const said=c.answer?'<div class="ok">\u2713 '+esc2(c.answer_label)+'</div>':'';
   h+='<div class="sec" style="margin:8px 0;padding:10px 12px'+(c.aged?';border-left:4px solid #b3261e':'')+'">'
     +'<div class="row"><span class="k"><b>'+esc2(c.item)+'</b></span><span class="v">'
     +(c.short_qty!=null?('\u2212'+c.short_qty):'\u2014')+'</span></div>'
     +(c.aged?'<div class="bad">'+c.age_days+' din purana \u2014 pehle isi ka jawab dijiye</div>':'')
     +ev+said
     +'<div>'+CLAIM_ANS.map(a=>'<button class="btn'+(a[0]===c.answer?' primary':'')
        +'" onclick="answerClaim('+c.id+',\\''+a[0]+'\\')">'+a[1]+'</button>').join("")+'</div>'
     +'</div>';
  }
  el("claimList").innerHTML=h;
 }catch(e){el("claimSec").style.display="none";}
}
function esc2(s){return String(s==null?"":s).replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));}
async function answerClaim(id,ans){
 try{
  const j=await post("/finance/darpan/api/claim/"+id+"/answer",{answer:ans});
  toast("Likh liya \\u2713 \u2014 "+(j.label||""));loadClaims();
 }catch(e){toast(""+e);}
}
loadClaims();

/* S210_HANDOVER -- the three routes out of the drawer and the RETURN leg,
   recorded where the cash actually moves: at the counter, by Darpan. */
'''

# ------------------------------------------------------------ the owner's hub
HUB_OLD = '''  // 8 -- pursue, with the evidence already gathered (S308)
  const PC=d.pursue.cards||[];
  h+=step(8,d.pursue.state,"Darpan: sold without a bill?",
    d.pursue.lines?('<b>'+d.pursue.lines+'</b> line'+(d.pursue.lines===1?'':'s')+' you chose to pursue. What the server already knows about each is below, so he is asked with the evidence in hand. His answer is evidence; your tap decides.'):'Only the lines you mark to pursue come here.',
    (PC.length?'<div style="margin:4px 0 8px">'+PC.slice(0,10).map(c=>'<div class="pc"><b>'+esc(c.item)+'</b> <span class="sub">short '+esc(c.short_text)+'</span>'
      +(c.lines||[]).map(l=>'<div class="sub">'+esc(l)+'</div>').join("")+'</div>').join("")+(PC.length>10?'<div class="sub">and '+(PC.length-10)+' more</div>':'')+'</div>':'')
    +'<div class="links"><a class="b" href="'+esc(L.loss)+'">Loss desk</a></div>');
'''
HUB_NEW = '''  // 8 -- pursue, with the evidence already gathered (S308) and, since S312, the
  // claim queue: Darpan's answer comes back here and the owner settles it, which
  // is the first time this step has been able to finish at all (D471, D544).
  const PC=d.pursue.cards||[];
  const CL=(d.pursue.claims||[]), CS=d.pursue.summary, CBY={};
  for(const c of CL){ CBY[c.item]=c; }
  const OUT=[["sold_no_bill","sold without a bill"],["returned_supplier","went back to the supplier"],
             ["found","found -- not short"],["damaged","damaged"],["written_off","written off"],
             ["not_known","never established"]];
  function claimBits(item){
    const c=CBY[item]; if(!c) return "";
    if(c.state==="settled")
      return '<div class="sub">\\u2713 settled \\u2014 '+esc(c.outcome_label||c.outcome)
        +(c.closed_auto?' <i>(by itself: '+esc(c.auto_reason)+')</i>':'')+'</div>';
    const said=c.answer
      ? '<div class="sub"><b>Darpan says:</b> '+esc(c.answer_label)+(c.answer_note?' \\u2014 '+esc(c.answer_note):'')+'</div>'
      : '<div class="sub">not asked yet</div>';
    const cand=c.candidate?'<div class="sub">'+esc(c.candidate)+'</div>':'';
    const aged=c.aged?'<div class="sub"><b>'+c.age_days+' days old</b></div>':'';
    const btns='<div class="links">'+OUT.map(o=>'<button class="b" data-settle="'+c.id
      +'" data-outcome="'+o[0]+'">'+o[1]+'</button>').join("")+'</div>';
    return said+cand+aged+btns;
  }
  const sumLine=CS?('<div class="sub">Claims: <b>'+CS.open+'</b> not asked \\u00b7 <b>'+CS.contacted
      +'</b> answered, waiting for your word \\u00b7 <b>'+CS.settled+'</b> settled'
      +(CS.aged?' \\u00b7 <b>'+CS.aged+'</b> over 14 days':'')
      +(CS.auto?' \\u00b7 '+CS.auto+' closed by itself':'')+'</div>'
      +(d.pursue.returns_stored?'':'<div class="sub"><i>A purchase return would close a claim by itself \\u2014 but no purchase return is stored on this box yet, so that rule is written and asleep. A credit note is shown as a candidate only; it names no item and closes nothing.</i></div>')):"";
  h+=step(8,d.pursue.state,"Darpan: sold without a bill?",
    d.pursue.lines?('<b>'+d.pursue.lines+'</b> line'+(d.pursue.lines===1?'':'s')+' you chose to pursue. What the server already knows about each is below, so he is asked with the evidence in hand. His answer is evidence; your tap decides.'):'Only the lines you mark to pursue come here.',
    sumLine
    +(d.pursue.note?'<div class="sub">'+esc(d.pursue.note)+'</div>':'')
    +(PC.length?'<div style="margin:4px 0 8px">'+PC.slice(0,10).map(c=>'<div class="pc"><b>'+esc(c.item)+'</b> <span class="sub">short '+esc(c.short_text)+'</span>'
      +(c.lines||[]).map(l=>'<div class="sub">'+esc(l)+'</div>').join("")+claimBits(c.item)+'</div>').join("")+(PC.length>10?'<div class="sub">and '+(PC.length-10)+' more</div>':'')+'</div>':'')
    +'<div id="cmsg"></div>'
    +'<div class="links"><a class="b" href="'+esc(L.loss)+'">Loss desk</a></div>');
'''

HUB_CLICK_OLD = '''  const rt=t.closest("button[data-ret]");
'''
HUB_CLICK_NEW = '''  const st=t.closest("button[data-settle]");
  if(st && !BUSY){ BUSY=true;
    const j=await post(BASE+"/api/claim/"+st.getAttribute("data-settle")+"/settle",
                       {outcome:st.getAttribute("data-outcome")}); BUSY=false;
    say("cmsg", j); if(j&&j.ok){ setTimeout(load, 500); } return; }
  const rt=t.closest("button[data-ret]");
'''

FILES = {
    "darpan_card.html": [("Darpan's claim section", CARD_SEC_OLD, CARD_SEC_NEW),
                         ("Darpan's claim script", CARD_JS_OLD, CARD_JS_NEW)],
    "stock_hub.html":   [("hub step 8", HUB_OLD, HUB_NEW),
                         ("hub settle click", HUB_CLICK_OLD, HUB_CLICK_NEW)],
}


def do(path, edits, frm, expect):
    if not os.path.exists(path):
        print("MISSING %s" % path); return 2
    src = open(path, encoding="utf-8").read()
    cur = hashlib.md5(src.encode("utf-8")).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED %s -- %s" % (os.path.basename(path), cur)); return 0
    if frm and cur != frm:
        print("REFUSED %s -- live md5 %s, expected %s" % (os.path.basename(path), cur, frm)); return 3
    for name, old, new in edits:
        n = src.count(old)
        if n != 1:
            print("REFUSED -- anchor '%s' occurs %d times, expected 1" % (name, n)); return 4
        src = src.replace(old, new)
    shutil.copyfile(path, path + ".bak_S312_" + cur[:8])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    got = hashlib.md5(src.encode("utf-8")).hexdigest()
    if expect and got != expect:
        print("REFUSED AFTER WRITE %s -- got %s, expected %s" % (os.path.basename(path), got, expect)); return 5
    print("PATCHED %s %s -> %s" % (os.path.basename(path), cur, got))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--card-from", default=""); ap.add_argument("--card-expect", default="")
    ap.add_argument("--hub-from", default=""); ap.add_argument("--hub-expect", default="")
    a = ap.parse_args()
    rc = do(os.path.join(a.dir, "darpan_card.html"), FILES["darpan_card.html"], a.card_from, a.card_expect)
    if rc:
        return rc
    return do(os.path.join(a.dir, "stock_hub.html"), FILES["stock_hub.html"], a.hub_from, a.hub_expect)


if __name__ == "__main__":
    sys.exit(main())
