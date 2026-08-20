#!/usr/bin/env python3
"""S193_UX — in-place, fail-loud patches to the two live served pages.
Each patch asserts its anchor occurs exactly once, or the whole run refuses
(nothing written). Usage: patch_pages.py <finance_entry.html> <finance_approvals.html>"""
import sys

ENTRY_PATCHES = [
    # E1 — a fresh/empty day must NOT pre-fill the money boxes with 0
    ('$("total").value = (j.day.total_p / 100).toFixed(2).replace(/\\.00$/, "");\n      $("upi").value = (j.day.upi_p / 100).toFixed(2).replace(/\\.00$/, "");',
     '$("total").value = j.day.total_p ? (j.day.total_p / 100).toFixed(2).replace(/\\.00$/, "") : "";\n      $("upi").value = j.day.upi_p ? (j.day.upi_p / 100).toFixed(2).replace(/\\.00$/, "") : "";',
     'E1 blank-0 on load'),
    # E2 — remember scroll before handing off to the scanner, restore on return
    ('function saveThenScan(doc){\n  var date = $("bdate").value;',
     'function saveThenScan(doc){\n  try{ sessionStorage.setItem("sanjScroll", String(window.scrollY)); }catch(e){}\n  var date = $("bdate").value;',
     'E2a store scroll (doc scan)'),
    ('function saveThenScanExpense(uid){',
     'function saveThenScanExpense(uid){\n  try{ sessionStorage.setItem("sanjScroll", String(window.scrollY)); }catch(e){}',
     'E2b store scroll (bill scan)'),
    # E3 — restore scroll after a scan return + select numeric boxes on focus
    ('  loadDay($("bdate").value);\n  loadShouts();\n  loadWhere();\n});',
     '  loadDay($("bdate").value);\n  loadShouts();\n  loadWhere();\n  /* S193_UX: after returning from a scan, go back to where you were */\n  try{ var _sy=sessionStorage.getItem("sanjScroll"); if(_sy!==null){ sessionStorage.removeItem("sanjScroll"); setTimeout(function(){ window.scrollTo(0, parseInt(_sy,10)||0); }, 60); } }catch(e){}\n  /* S193_UX: tapping a number box selects it, so typing replaces the value */\n  document.addEventListener("focusin", function(e){ if(e.target && e.target.matches && e.target.matches(\'input[inputmode="numeric"]\')) e.target.select(); });\n});',
     'E3 restore scroll + select-on-focus'),
]

HUB_PATCHES = [
    # H1 — the review/month-close link, named so it is findable
    ('>Month close ↗</a>', '>Review &amp; month close ↗</a>', 'H1 rename review tab'),
    # H2 — custody reads "held now" vs "passed on", with a total
    ('''$("custHeld").innerHTML=held.length?held.map(function(x){
      return '<span class="stat"><span class="lbl">'+esc(NAMES[x.party]||x.party)+'</span><span class="val">'+fmt(x.held)+'</span></span>'}).join("")
      :'<span class="mut">no custody balances recorded yet</span>';''',
     '''var _hold=held.filter(function(x){return x.held>0}),_cond=held.filter(function(x){return x.held<=0});
    var _tot=_hold.reduce(function(a,x){return a+(x.held||0)},0);
    $("custHeld").innerHTML=held.length?(
      '<span class="stat"><span class="lbl">Held now · total</span><span class="val">'+fmt(_tot)+'</span></span>'+
      _hold.map(function(x){return '<span class="stat"><span class="lbl">'+esc(NAMES[x.party]||x.party)+'</span><span class="val">'+fmt(x.held)+'</span></span>'}).join("")+
      _cond.map(function(x){return '<span class="stat"><span class="lbl">'+esc(NAMES[x.party]||x.party)+'</span><span class="val mut" style="font-size:15px">passed on</span></span>'}).join("")
    ):'<span class="mut">no custody balances recorded yet</span>';''',
     'H2 custody held/passed-on'),
    # H3 — collapsible cards for readability (append to the init script)
    ('}\nload();\n</script>',
     '''}
load();
/* S193_UX: make every card collapsible; noisy ones start collapsed. */
(function(){
  var st=document.createElement("style");
  st.textContent=".card.collapsed > *:not(:first-child){display:none}.cabToggle{color:var(--text-3);font-weight:400;font-size:13px;margin-right:4px}";
  document.head.appendChild(st);
  document.querySelectorAll(".card").forEach(function(card){
    var head=card.querySelector(".h2row")||card.querySelector("h2"); if(!head) return;
    head.style.cursor="pointer";
    var h=card.querySelector("h2")||head; var tag=document.createElement("span"); tag.className="cabToggle"; tag.textContent="\\u25be "; h.insertBefore(tag,h.firstChild);
    head.addEventListener("click",function(e){ var t=e.target.tagName; if(t==="A"||t==="BUTTON"||t==="INPUT"||t==="SELECT") return; var c=card.classList.toggle("collapsed"); tag.textContent=c?"\\u25b8 ":"\\u25be "; });
  });
  ["margCard","cashCard","custCard","monthCard","orthoCard","exCard"].forEach(function(id){ var c=document.getElementById(id); if(c){ c.classList.add("collapsed"); var t=c.querySelector(".cabToggle"); if(t)t.textContent="\\u25b8 "; } });
})();
</script>''',
     'H3 collapsible cards'),
]

def apply(path, patches):
    s=open(path,encoding="utf-8").read(); n=0
    for old,new,label in patches:
        c=s.count(old)
        if c!=1:
            sys.stderr.write("REFUSED [%s]: anchor found %d times (need 1) in %s\n"%(label,c,path)); sys.exit(3)
        s=s.replace(old,new); n+=1
    open(path,"w",encoding="utf-8").write(s)
    print("  patched %s (%d edits)"%(path,n))

if __name__=="__main__":
    apply(sys.argv[1], ENTRY_PATCHES)
    apply(sys.argv[2], HUB_PATCHES)
    print("ALL PATCHES APPLIED")
