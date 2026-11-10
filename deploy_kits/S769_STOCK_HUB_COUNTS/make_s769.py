#!/usr/bin/env python3
"""make_s769.py LIVE_FINANCE_DIR LIVE_PORTAL_DIR OUT_DIR -- builds the kit's files from THIS box's live bytes (F-472).
Every live file must be at its FROM pin; each anchored edit must match exactly once. section_count.py / .html are whole-file
replacements of S768's (their FROM pins are checked too); tile_grants.json is edited as JSON and written in its own format."""
import hashlib
import json
import os
import shutil
import sys

KDIR = os.path.dirname(os.path.abspath(__file__))
FROM = {"stockmatch.py": "d80523b696c1d0771ba1bf583df85092", "stock_hub.html": "a710a98a568227d4b2ba220d792e6a2c",
        "section_count.py": "305dd037e9cce75a0443a58cbbac09c2", "section_count.html": "c51a328e9bb3836f402e6836a6dd107b",
        "tile_grants.json": "e486f3de51dfc8e0c330e5e874a35bf2"}
GRANT = ("alisha", "amir", "shavez", "shivani")
TILE = "Stock milaan"

HUB_CSS = """.s769h{font-size:17px;margin:18px 0 4px}
.s769g{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:8px}
.s769c{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--surface)}
.s769c.on{border-color:var(--accent)} .s769c.amber{border-color:var(--warn);background:var(--warn-soft)}
.s769row{display:flex;flex-wrap:wrap;align-items:center;gap:10px;border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:8px 0;background:var(--surface)}
.s769row .t{flex:1 1 320px}
.s769st{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:8px}
.s769sw{border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--surface);text-align:left;font:inherit;cursor:pointer;color:var(--ink);min-height:44px}
.s769sw.on{border-color:var(--accent);background:var(--accent-soft)}
.s769sw .p{display:inline-block;margin-top:6px;font-size:13px;font-weight:700;padding:3px 9px;border-radius:999px;border:1px solid var(--line)}
.s769sw.on .p{background:var(--accent);color:var(--on-accent);border-color:var(--accent)}
.s769bad{color:var(--diff)}
.s769row .b,.s769c .b,#s769sum .b{min-height:44px} #s769msg:empty{display:none} .b.sure{color:var(--diff);border-color:var(--diff)}
@media (max-width:700px){.s769g{grid-template-columns:1fr}.s769st{grid-template-columns:1fr 1fr}}
"""

HUB_JS = r"""
/* ---- S769_STOCK_HUB_COUNTS (10-Nov-2026, the owner 07:26 IST): the hub lists every count. The top: start a count from a
   template, the counts in progress (Open / Cancel / the correction -> Send to Amir), "Who may count" (the doctor's switch, the
   counting page only). A closed count (06-Sep) folds to one line; "Show the full flow" opens the page above unchanged. ---- */
const SCP="/finance/stockmatch/count";
let S769=null, S769OPEN=null;
function s769dd(s){ if(!s) return ""; const d=new Date(String(s).slice(0,10)+"T00:00:00"); return isNaN(d)?esc(String(s)):d.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"}).replace(/ /g,"-"); }
function s769dmy(s){ const m=/^(\d\d)-(\d\d)-(\d{4})$/.exec(String(s||"")); return m?s769dd(m[3]+"-"+m[2]+"-"+m[1]):String(s||""); }
function s769cap(s){ s=String(s||""); return s?s.charAt(0).toUpperCase()+s.slice(1):s; }
function s769sum(){
  const d=D; if(!d) return;
  const K=d.desk||{}, V=d.vouchers||{}, W=d.words||{}, O=d.ortho||{};
  const closed=!!d.closed;
  if(S769OPEN===null) S769OPEN=!closed;
  const fig=(t,lab)=>t&&t.n?(lab+' '+rsx(t.mrp_p)+' ('+t.n+' line'+(t.n===1?'':'s')+')'):'';
  const bits=[d.differed+' differed', fig(K.written_off,'written off'), fig(K.back,'back in store'),
    (V.batches_total?(V.batches_entered||0)+' of '+V.batches_total+' Marg vouchers entered':''),
    (O&&O.verdict_en?O.verdict_en:'')].filter(Boolean);
  document.getElementById("s769sum").innerHTML='<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center"><div style="flex:1 1 420px">'
    +(closed?'✓ ':'')+'<b>'+esc(s769dmy(d.day)||"")+'</b> · whole shop · '+d.counted+' items · counted by '+esc(d.counted_by||"-")+', entered by '+esc(d.entered_by||"-")
    +(closed?' — closed':' — in progress')+'<div class="sub">'+bits.map(esc).join(' · ')+'</div></div>'
    +'<button class="b" id="s769tog">'+(S769OPEN?'Hide the full flow ▴':'Show the full flow ▸')+'</button></div>';
  document.getElementById("s769fold").style.display=S769OPEN?"":"none";
}
function s769top(){
  fetch(SCP+"/api/hub?_="+Date.now(),{cache:"no-store"}).then(r=>r.json()).then(j=>{ if(!j.ok) throw new Error(j.message||j.error); S769=j; s769render(); })
    .catch(e=>{ document.getElementById("s769top").innerHTML='<div class="facts err">The counts could not be read ('+esc(e.message||"no answer")+'). The 06-Sep count below is unaffected.</div>'; });
}
function s769render(){
  const J=S769; let h='<h2 class="s769h">Start a new count</h2><div class="s769g">';
  J.templates.forEach(t=>{ const g=t.guard||{};
    const gl=t.open?'<div class="sub">A count is open \u2014 it is under Counts in progress.</div>':g.blocked?(g.checked===false?'<div class="sub s769bad">'+esc(g.why)+'</div>':'<div class="sub s769bad">'+(g.lines||[]).map(l=>esc(l.text)).join('<br>')+'</div>')
      :'<div class="sub">No '+esc(t.section.toLowerCase())+' bill is waiting for Marg — ready to start.</div>';
    h+='<div class="s769c on"><b>'+esc(t.section)+' shelf</b><div class="sub">'+t.items+' items in Marg\'s closing of '+esc(s769dmy(t.snap_as_on)||"-")+' · new products join by themselves · count-twice marks</div>'+gl
      +'<div class="links"><a class="b main" href="'+esc(t.url)+'">'+(t.open?'Continue the open count':'Start the '+esc(t.section.toLowerCase())+' count')+'</a></div></div>'; });
  const W=J.whole||{};
  h+='<div class="s769c"><b>Whole shop</b><div class="sub">All '+(W.items||'')+' items · the flow of 06-Sep (match, loss desk, vouchers, proof)'
    +(W.plan&&W.plan.length?' · the Sunday plan is open: '+W.plan.map(s769dd).join(', '):'')+'</div><div class="links"><a class="b" href="'+esc(W.url)+'">Whole-shop counting screen</a></div></div></div>';
  const act=J.counts.filter(c=>c.status==="draft"||c.status==="sent"), past=J.counts.filter(c=>!(c.status==="draft"||c.status==="sent"));
  h+='<h2 class="s769h">Counts in progress</h2>';
  if(!act.length) h+='<div class="facts">None open.</div>';
  act.forEach(c=>{ const K=c.correction;
    let t, btn='<a class="b main" href="'+esc(c.url)+'">Open</a>';
    if(c.status==="draft"){ t='<b>'+esc(c.section)+'</b> · started '+s769dd(c.started_at)+' '+esc(String(c.started_at||"").slice(11,16))+' by '+esc(s769cap(c.started_by))
        +'<div class="sub">Counting — '+c.done+' of '+c.total+' entered'+(c.saved_at?' · last saved '+esc(String(c.saved_at).slice(11,16)):'')+'</div>';
      btn+='<button class="b" data-s769cancel="'+c.id+'">Cancel this count</button>'; }
    else { t='<b>'+esc(c.section)+'</b> · counted '+s769dd(c.day)+' · sent by '+esc(s769cap(c.sent_by))
        +'<div class="sub">'+(!K||K.state!=="ready"?esc((K&&K.why)||'The correction comes after that day\'s Marg closing.')
          :('Correction ready: '+K.changes+' line'+(K.changes===1?'':'s')+' to change in Marg'+(K.hand?' · <span class="s769bad">'+K.hand+' need your figure</span>':'')
            +(K.open_aside?' · <span class="s769bad">'+K.open_aside+' kept-aside to settle</span>':'')+(K.renames?' · '+K.renames+' renames':'')))+'</div>';
      btn='<a class="b main" href="'+esc(c.url)+'">'+(K&&K.state==="ready"?'See the correction → Send to Amir':'Open')+'</a><button class="b" data-s769cancel="'+c.id+'">Cancel this count</button>'; }
    h+='<div class="s769row'+(c.status==="draft"?' ':'')+'"><div class="t">'+t+'</div>'+btn+'</div>'; });
  h+='<span class="msg" id="s769msg"></span>';
  h+='<h2 class="s769h">Who may count</h2><div class="facts" style="margin-top:4px">Switch a person on when they help with a count. They see only the counting page, none of Darpan\'s other Stock milaan work. Switch them off when the count is done. Darpan can always count.'
    +'<div class="s769st">'+J.staff.map(s=>'<button class="s769sw'+(s.on?' on':'')+'" data-s769who="'+esc(s.user)+'" data-on="'+(s.on?1:0)+'"><b>'+esc(s769cap(s.user))+'</b><br><span class="p">'+(s.on?'Can count':'Off')+'</span></button>').join('')+'</div></div>';
  if(past.length){ h+='<h2 class="s769h">Earlier section counts</h2>'+past.map(c=>'<div class="s769row"><div class="t">'+(c.status==="to_amir"?'✓ ':'')+'<b>'+esc(c.section)+'</b> · '
      +s769dd(c.day||c.started_at)+' · '+(c.status==="to_amir"?'sent to Amir '+s769dd(c.to_amir_at):(c.status==="cancelled"?'cancelled':esc(c.status)))+'</div><a class="b" href="'+esc(c.url)+'">Open</a></div>').join(''); }
  document.getElementById("s769top").innerHTML=h;
}
document.addEventListener("click", async e=>{
  const t=e.target;
  if(t.id==="s769tog"){ S769OPEN=!S769OPEN; s769sum(); return; }
  const cx=t.closest("[data-s769cancel]");
  if(cx){ if(cx.dataset.sure!=="1"){ cx.dataset.sure="1"; cx.classList.add("sure"); cx.textContent="Tap again to cancel this count"; return; }
    const j=await post(SCP+"/api/cancel",{count:+cx.getAttribute("data-s769cancel")}); say("s769msg", j&&j.ok?{ok:true,message:"Cancelled. Nothing was changed anywhere."}:j); s769top(); return; }
  const sw=t.closest("[data-s769who]");
  if(sw){ sw.disabled=true; const j=await post(SCP+"/api/access",{user:sw.getAttribute("data-s769who"),on:sw.getAttribute("data-on")!=="1"});
    if(!(j&&j.ok)){ say("s769msg", j); } s769top(); return; }
});
s769top();
"""

EDITS = {
    "stockmatch.py": [(
        '@bp.route("/finance/stockmatch")\ndef page():\n    u, con, kind, err = _auth()\n    if err:\n        return err\n    return send_file(PAGE)\n',
        '@bp.route("/finance/stockmatch")\ndef page():\n    u, con, kind, err = _auth()\n    if err:                                                   '
        '# S769: a login the doctor switches on for counting holds the Stock milaan tile;\n'
        '        from flask import redirect                            # noqa: PLC0415 -- the count page serves it, or says it is not switched on\n'
        '        return redirect("/finance/stockmatch/count", code=302)\n    return send_file(PAGE)\n'),
    ],
    "stock_hub.html": [
        ("<title>Stock check</title>", "<title>Stock checks</title>"),
        ("</style></head>", HUB_CSS + "</style></head>"),
        ('<div><h1>Stock check</h1><div class="sub" id="who"></div></div>\n<div id="body"><div class="facts">Loading…</div></div>\n'
         '<div class="foot" id="foot"></div>\n</div>',
         '<div><h1>Stock checks</h1><div class="sub">Every count, its flow and its result in one place</div></div>\n'
         '<div id="s769top"><div class="facts">Loading the counts…</div></div>\n'
         '<h2 class="s769h">Earlier whole-shop counts</h2>\n<div class="facts" id="s769sum">Loading…</div>\n'
         '<div id="s769fold">\n<div class="sub" id="who"></div>\n<div id="body"><div class="facts">Loading…</div></div>\n'
         '<div class="foot" id="foot"></div>\n</div>\n</div>'),
        ("document.getElementById(\"foot\").innerHTML='<a class=\"b\" href=\"'+esc(L.count)+'\">Start a new count</a>';",
         "document.getElementById(\"foot\").innerHTML='';   s769sum();   // S769: 'Start a new count' moved to the top, with the templates"),
        ("h+=step(4,V.state,", "h+=step(4,((V.pending===0&&V.batches_total&&V.batches_entered>=V.batches_total)?\"done\":V.state),   /* S769: 37 of 37 entered is done */ "),
        ("h+=step(6,d.pursue.state,", "h+=step(6,((!d.pursue.lines&&CS&&!CS.open&&!CS.contacted)?\"done\":d.pursue.state),   /* S769: nothing waiting is done */ "),
        ("\nload();\n</script></body></html>", "\nload();\n" + HUB_JS + "</script></body></html>"),
    ],
}
NEW = ("section_count.py", "section_count.html")


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(fin, portal, out):
    os.makedirs(out, exist_ok=True)
    src = {n: os.path.join(fin, n) for n in ("stockmatch.py", "stock_hub.html", "section_count.py", "section_count.html")}
    src["tile_grants.json"] = os.path.join(portal, "tile_grants.json")
    for n, p in src.items():
        if md5(open(p, "rb").read()) != FROM[n]:
            print("REFUSED: %s is %s, not its FROM pin %s" % (n, md5(open(p, "rb").read())[:8], FROM[n][:8]))
            return 2
    for name, edits in EDITS.items():
        t = open(src[name], "rb").read().decode("utf-8")
        for old, new in edits:
            if t.count(old) != 1:
                print("REFUSED: %s: an anchor matches %d times: %r" % (name, t.count(old), old[:60]))
                return 2
            t = t.replace(old, new)
        open(os.path.join(out, name), "wb").write(t.encode("utf-8"))
        print("built %s %s -> %s" % (name, FROM[name][:8], md5(t.encode("utf-8"))[:8]))
    t = open(src["tile_grants.json"], "rb").read().decode("utf-8")
    d = json.loads(t)
    if json.dumps(d, ensure_ascii=False, indent=1) + "\n" != t:
        print("REFUSED: tile_grants.json is not in the format this kit writes back")
        return 2
    if d.get("version") != 44:
        print("REFUSED: tile_grants.json is v%s, not v44" % d.get("version"))
        return 2
    for u in GRANT:
        ex = d["users"][u].setdefault("extra", [])
        if TILE not in ex:
            ex.append(TILE)
    d["version"] = 45
    d["_note"] = d["_note"] + (" v45 (S769, the Sanjeevni chat, 10-Nov-2026; the owner 07:26 IST): 'Stock milaan' granted by name to alisha, amir,"
                               " shavez, shivani -- for them it opens the stock COUNT page, which serves them only while the doctor's 'Who may"
                               " count' switch is on (unit stockcount); otherwise it says they are not switched on.")
    b = (json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    open(os.path.join(out, "tile_grants.json"), "wb").write(b)
    print("built tile_grants.json e486f3de -> %s" % md5(b)[:8])
    shutil.copy2(os.path.join(fin, "stockmatch.html"), os.path.join(out, "stockmatch.html"))      # unchanged; the walk serves Stock milaan from it
    shutil.copy2(os.path.join(KDIR, "section_count_seed_S768.txt"), os.path.join(out, "section_count_seed_S768.txt"))   # the walk's seed
    for name in NEW:
        shutil.copy2(os.path.join(KDIR, name + ".kit"), os.path.join(out, name))
        print("copied %s %s -> %s" % (name, FROM[name][:8], md5(open(os.path.join(out, name), "rb").read())[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
