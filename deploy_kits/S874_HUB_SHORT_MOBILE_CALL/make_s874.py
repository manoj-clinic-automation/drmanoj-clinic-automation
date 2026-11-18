"""make_s874.py <finance dir holding the FROM files> <out dir> -- kit S874_HUB_SHORT_MOBILE_CALL:
   sanjeevni_day.py            WHOLE file from the kit (v1.4; FROM = S869's 4359d048)
   finance_ui/finance_approvals.html  four anchored patches on S872's page (1f594b5f): the day's own short with Accept / Add an entry;
                               the full mobile with a Call button on every bill and return (the portal's click-to-call door)."""
import hashlib, os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
KD = os.path.dirname(os.path.abspath(__file__))
FROM = {"finance_ui/finance_approvals.html": "1f594b5f8a750b90f16c590abada0bdc", "sanjeevni_day.py": "4359d04826ad508867be3e9e880d9168"}
P1_OLD = '''        var who=b.typed?('<b>'+esc(b.typed)+'</b> <span class="mut">as typed in Marg</span>'+((b.name&&b.name!==b.typed)?' <span class="mut">· '+esc(b.name)+'</span>':'')):('<span class="mut">'+esc(b.name||"no patient name")+'</span>');
        return '<div style="border-bottom:1px dotted #eee;padding:2px 0">'+
          '<div onclick="var n=this.nextElementSibling;if(n)n.style.display=n.style.display===\\'none\\'?\\'\\':\\'none\\'" style="cursor:pointer;display:flex;gap:8px">'+
          '<span style="flex:1">'+esc(b.bill)+' '+who+(its?' <span class="tog">▸</span>':'')+'</span>'+'''
P1_NEW = '''        var who=b.typed?('<b>'+esc(b.typed)+'</b> <span class="mut">as typed in Marg</span>'+((b.name&&b.name!==b.typed)?' <span class="mut">· '+esc(b.name)+'</span>':'')):('<span class="mut">'+esc(b.name||"no patient name")+'</span>');
        who+=s874Mob(b);                                                                   /* S874: the full mobile + Call */
        return '<div style="border-bottom:1px dotted #eee;padding:2px 0">'+
          '<div onclick="var n=this.nextElementSibling;if(n)n.style.display=n.style.display===\\'none\\'?\\'\\':\\'none\\'" style="cursor:pointer;display:flex;gap:8px">'+
          '<span style="flex:1">'+esc(b.bill)+' '+who+(its?' <span class="tog">▸</span>':'')+'</span>'+'''
P2_OLD = '''        var who=[b.patient?('<b>'+esc(b.patient)+'</b>'):'<span class="mut">no patient name</span>', b.clinic_id?('#'+esc(b.clinic_id)):'', b.mobile?esc(b.mobile):''].filter(Boolean).join(' · ');'''
P2_NEW = '''        var who=[b.patient?('<b>'+esc(b.patient)+'</b>'):'<span class="mut">no patient name</span>', b.clinic_id?('#'+esc(b.clinic_id)):''].filter(Boolean).join(' · ')+s874Mob(b);   /* S874 */'''
P3_OLD = '''    if(v.went) h+='<div style="margin:6px 0"><b>Where the cash went:</b> '+esc(v.went)+'</div>';
    h+=s869Entries(v,d,elId);                                                      /* S869: your entries on this day, + Add an entry */'''
P3_NEW = '''    if(v.went) h+='<div style="margin:6px 0"><b>Where the cash went:</b> '+esc(v.went)+'</div>';
    if(v.short) h+='<div class="alert warn" style="margin:6px 0"><b>₹'+esc(v.short)+' short</b> — less left the drawer than came in. '+
      (v.can_accept?'<button onclick="event.stopPropagation();s869Accept(\\''+d+'\\',this)">Accept (write off)</button> ':'')+
      '<button class="ghost" onclick="event.stopPropagation();s869Toggle(\\''+d+'\\')">Add an entry</button>'+(v.can_accept?' <span class="mut">(tap twice to accept)</span>':'')+'</div>';   /* S874 */
    h+=s869Entries(v,d,elId);                                                      /* S869: your entries on this day, + Add an entry */'''
P4_OLD = '''/* ==== end KIT_S869 ==== */'''
P4_NEW = '''/* ==== KIT_S874_HUB_SHORT_MOBILE_CALL (18-Nov-2026, Sanjeevni session 482; his words 13:41) ==== the full mobile on every bill and
   return of HIS Hub, with a Call button through the portal's own click-to-call (your MyOperator agent rings, then the patient is joined;
   one call per number per minute, as on the Call Console). A tel: link beside it for the phone. */
function s874Mob(b){
  var L=(b.mobiles&&b.mobiles.length)?b.mobiles:(b.mobile?[b.mobile]:[]);
  if(!L.length) return '';
  return L.map(function(m){ var full=/^[6-9]\\d{9}$/.test(String(m));
    return ' <span class="mut" onclick="event.stopPropagation()">· <a href="tel:+91'+esc(m)+'" style="text-decoration:none">'+esc(m)+'</a>'+(full?' <button class="ghost" style="padding:0 6px" title="Call through MyOperator: your phone rings first" onclick="s874Call(\\''+esc(m)+'\\',this)">📞</button>':'')+'</span>'; }).join('');
}
function s874Call(ph,btn){
  if(btn){ btn.disabled=true; btn.textContent='…'; }
  fetch('/portal/console/api/call',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone10:ph})})
    .then(function(r){ return r.text().then(function(t){ var j={}; try{ j=JSON.parse(t) }catch(e){} return {s:r.status,j:j,redirected:r.redirected}; }); })
    .then(function(x){ if(btn){ btn.disabled=false; btn.textContent='📞'; }
      if(x.s===200&&x.j.ok){ alert(x.j.msg||'Your phone is ringing — pick up, and the patient is joined.'); return; }
      if(x.s===401||x.s===403||x.redirected||x.s===302){ alert('Sign in to the portal once in this browser, then tap again: https://followup.dr-manoj.in/portal/'); return; }
      alert(x.j.msg||('The call could not be placed (HTTP '+x.s+')')); })
    .catch(function(){ if(btn){ btn.disabled=false; btn.textContent='📞'; } alert('The call could not be placed — the server could not be reached'); });
}
/* ==== end KIT_S874 ==== */
/* ==== end KIT_S869 ==== */'''


def main():
    os.makedirs(os.path.join(OUT, "finance_ui"), exist_ok=True)
    for f in FROM:
        b = open(os.path.join(SRC, f), "rb").read()
        assert hashlib.md5(b).hexdigest() == FROM[f], "%s is not at its FROM pin (%s)" % (f, hashlib.md5(b).hexdigest())
        if f.endswith(".html"):
            t = b.decode("utf-8")
            for old, new in ((P1_OLD, P1_NEW), (P2_OLD, P2_NEW), (P3_OLD, P3_NEW), (P4_OLD, P4_NEW)):
                assert t.count(old) == 1, "anchor not found once: %r" % old[:70]
                t = t.replace(old, new)
            t = t.encode("utf-8")
        else:
            t = open(os.path.join(KD, f), "rb").read()
        open(os.path.join(OUT, f), "wb").write(t)
        print(f, hashlib.md5(t).hexdigest())


if __name__ == "__main__":
    main()
