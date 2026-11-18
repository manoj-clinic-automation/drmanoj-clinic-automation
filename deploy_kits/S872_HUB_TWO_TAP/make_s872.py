"""make_s872.py <finance dir holding the FROM file> <out dir> -- kit S872_HUB_TWO_TAP: finance_ui/finance_approvals.html, three anchored
patches. The three S869 buttons that asked with window.confirm() -- Mark all N received, Accept (write off), remove an entry -- fire the
Hub's own two-tap way instead (tap once: the button says 'Tap again to ...'; tap again within 5 s: it sends), because the Claude app's
built-in browser answers every confirm() with No by itself (the owner, 18-Nov 13:26). Nothing else on the page changes."""
import hashlib, os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
FROM = "7253dc9f9a8ec0cfd576808af4c9b6a7"
P1_OLD = '''function s869ReceivedAll(n){
  if(!window.confirm("Mark all "+n+" handover(s) to Dr Bhawna as received?")) return;
  s869Post("/finance/sanjeevni/api/received-all",{party:"dr_bhawna"}).then(function(j){ s869Refresh(); alert((j.n||0)+" handover(s) marked received for Dr Bhawna"); }).catch(function(e){ alert("not marked — "+e.message); });
}'''
P1_NEW = '''/* S872 (18-Nov-2026): no confirm dialog on this page -- the Claude app's built-in browser answers it No by itself. Two taps instead:
   the first turns the button into 'Tap again to ...' for 5 seconds, the second sends. One pattern for Mark all / Accept / remove. */
var S872_ARM={};
function s872TwoTap(key,btn,armText,go){
  if(S872_ARM[key]){ clearTimeout(S872_ARM[key].t); S872_ARM[key]=null; btn.disabled=true; go(); return; }
  var was=btn.textContent; btn.textContent=armText;
  S872_ARM[key]={t:setTimeout(function(){ S872_ARM[key]=null; btn.textContent=was; },5000)};
}
function s869ReceivedAll(n,btn){
  var go=function(){ s869Post("/finance/sanjeevni/api/received-all",{party:"dr_bhawna"}).then(function(j){ s869Refresh(); }).catch(function(e){ if(btn) btn.disabled=false; alert("not marked — "+e.message); }); };
  if(!btn){ go(); return; }
  s872TwoTap("all",btn,"Tap again to mark all "+n+" received",go);
}'''
P2_OLD = '''    ' <button onclick="s869ReceivedAll('+U.length+')">Mark all '+U.length+' received</button> <span class="mut">· she does not use the app; your tap stands for her</span></div>';'''
P2_NEW = '''    ' <button onclick="s869ReceivedAll('+U.length+',this)">Mark all '+U.length+' received</button> <span class="mut">· she does not use the app; your tap stands for her (tap twice)</span></div>';'''
P3_OLD = '''function s869Remove(id,d,elId){
  if(!window.confirm("Remove this entry?")) return;
  s869Post("/finance/sanjeevni/api/day-entry/remove",{id:id}).then(function(){ s869Refresh(); if($(elId)) dayDetail(d,elId); }).catch(function(e){ alert("not removed — "+e.message); });
}
function s869Accept(d){
  if(!window.confirm("Accept the short of "+d+" -- written off, out of the drawer?")) return;
  s869Post("/finance/darpan/kal/api/owner/decide",{date:d,decision:"accept",note:"accepted on the Hub's Cash card"}).then(function(){ s869Refresh(); }).catch(function(e){ alert("not accepted — "+e.message); });
}'''
P3_NEW = '''function s869Remove(id,d,elId,el){
  var go=function(){ s869Post("/finance/sanjeevni/api/day-entry/remove",{id:id}).then(function(){ s869Refresh(); if($(elId)) dayDetail(d,elId); }).catch(function(e){ alert("not removed — "+e.message); }); };
  if(!el){ go(); return; }
  s872TwoTap("rm"+id,el,"tap again to remove",go);
}
function s869Accept(d,btn){
  var go=function(){ s869Post("/finance/darpan/kal/api/owner/decide",{date:d,decision:"accept",note:"accepted on the Hub's Cash card"}).then(function(){ s869Refresh(); }).catch(function(e){ if(btn) btn.disabled=false; alert("not accepted — "+e.message); }); };
  if(!btn){ go(); return; }
  s872TwoTap("acc"+d,btn,"Tap again to write off "+d,go);
}'''
P4_OLD = '''  if(E.length) h+='<b>Your entries:</b> '+E.map(function(e){ return esc(e.words)+' <a href="#" onclick="s869Remove('+e.id+',\\''+d+'\\',\\''+elId+'\\');return false" class="mut">remove</a>'; }).join(' · ');'''
P4_NEW = '''  if(E.length) h+='<b>Your entries:</b> '+E.map(function(e){ return esc(e.words)+' <a href="#" onclick="s869Remove('+e.id+',\\''+d+'\\',\\''+elId+'\\',this);return false" class="mut">remove</a>'; }).join(' · ');'''
P5_OLD = '''+(r.actions.indexOf("accept")>=0?' <button class="ghost" onclick="s869Accept(\\''+r.date+'\\')">Accept (write off)</button>':'')+'</td></tr>';'''
P5_NEW = '''+(r.actions.indexOf("accept")>=0?' <button class="ghost" onclick="s869Accept(\\''+r.date+'\\',this)">Accept (write off)</button>':'')+'</td></tr>';'''
b = open(os.path.join(SRC, "finance_ui", "finance_approvals.html"), "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "finance_approvals.html is not at its FROM pin (%s)" % hashlib.md5(b).hexdigest()
t = b.decode("utf-8")
for old, new in ((P1_OLD, P1_NEW), (P2_OLD, P2_NEW), (P3_OLD, P3_NEW), (P4_OLD, P4_NEW), (P5_OLD, P5_NEW)):
    assert t.count(old) == 1, "anchor not found once: %r" % old[:70]
    t = t.replace(old, new)
assert "window.confirm" not in t[t.find("KIT_S869_HUB_DAYS_CASH"):t.find("end KIT_S869")], "a confirm() is left in the S869 block"
os.makedirs(os.path.join(OUT, "finance_ui"), exist_ok=True)
open(os.path.join(OUT, "finance_ui", "finance_approvals.html"), "wb").write(t.encode("utf-8"))
print("finance_ui/finance_approvals.html", hashlib.md5(t.encode("utf-8")).hexdigest())
