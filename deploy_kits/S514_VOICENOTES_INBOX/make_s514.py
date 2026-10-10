#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s514.py -- S514_VOICENOTES_INBOX (session 304, 10-Oct-2026): exact anchored edits, each anchor found exactly once.

  usage: make_s514.py <finance folder>   edits finance_app.py and aaj_panel.html IN THAT FOLDER (a scratch copy);
         voicenotes_inbox.py is a new file placed beside them by the installer.
  finance_app.py  ec5b3ab1 (as S513 leaves it) -> TO: the door in PUBLIC_PATHS (the key is checked in the module); the
                  owner's inbox path among the identity-only paths (the module checks the owner); the module mounted,
                  guarded (S209); and counted among the parts that must load (30).
  aaj_panel.html  898c42e1 (S493) -> TO: the Voicenotes lines above the task box, and the one-time set-up below it.
"""
import hashlib
import os
import sys

PINS = {"finance_app.py": ("ec5b3ab170ff37c63ac98f6f1f11ad09", "0d713b14570384e0de07ac93a3b113db"),
        "aaj_panel.html": ("898c42e14b142e06f2800d83aaaf01ca", "36bd57bcda586f18183aec54c537e2e6")}

APP = [
    ('''                "/finance/api/bank-sms",                   # S290: the phone's door; bank_sms.py checks its key
''',
     '''                "/finance/api/bank-sms",                   # S290: the phone's door; bank_sms.py checks its key
                "/finance/api/voicenotes-push",            # S514: Voicenotes' door; voicenotes_inbox.py checks its key
'''),
    ('''                       "/finance/aaj/api/switch")
''',
     '''                       "/finance/aaj/api/switch",
                       "/finance/aaj/api/vn")                  # S514: the owner's Voicenotes lines; the module checks the owner
'''),
    ("""'pc_kits', 'owner_console', 'aaj_kaam') if m not in sys.modules and m not in _mf]
        _all = 29                                             # S481: + owner_console · S487: + aaj_kaam
""",
     """'pc_kits', 'owner_console', 'aaj_kaam', 'voicenotes_inbox') if m not in sys.modules and m not in _mf]
        _all = 30                                             # S481: + owner_console · S487: + aaj_kaam · S514: + voicenotes_inbox
"""),
    ('''    print("aaj_kaam NOT mounted: %s" % _ex_ak, file=sys.stderr)
# --- S487_AAJ_KA_KAAM end ---
''',
     '''    print("aaj_kaam NOT mounted: %s" % _ex_ak, file=sys.stderr)
# --- S487_AAJ_KA_KAAM end ---

# --- S514_VOICENOTES_INBOX begin -- a to-do list made in Voicenotes reaches the owner's task box (owner, D689) ---
# PARENT. One public door, POST /finance/api/voicenotes-push?key=..., opened only by /root/finance/voicenotes.key (checked
# in the module); the lines wait in vn_inbox until the owner puts them into "Give a task" on his panel. Nothing here makes
# a task. GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import voicenotes_inbox                                    # noqa: E402
    voicenotes_inbox.init(app, db, require, current_user)
except Exception as _ex_vn:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('voicenotes_inbox', repr(_ex_vn)[:200]))
    print("voicenotes_inbox NOT mounted: %s" % _ex_vn, file=sys.stderr)
# --- S514_VOICENOTES_INBOX end ---
'''),
]

PANEL = [
    ('''.say{display:grid;gap:8px;margin-top:8px}
''',
     '''.say{display:grid;gap:8px;margin-top:8px}
/* S514: the lines Voicenotes sent, waiting above the task box */
.vn{border:1px solid var(--navy);background:var(--navy-soft);border-radius:10px;padding:4px 12px 10px;margin:10px 0}
.vn h3{margin-top:10px}
.vnl{display:flex;gap:10px;align-items:flex-start;padding:6px 0;border-top:1px solid var(--line);cursor:pointer;overflow-wrap:anywhere}
.vnl:first-of-type{border-top:0}
.vnl input{width:18px;height:18px;margin-top:4px;flex:none}
.vnl span{flex:1}
.vnl .vnw{flex:none;font-size:12.5px;color:var(--muted);max-width:40%}
.vnset{margin-top:14px;font-size:15px}
.vnset summary{cursor:pointer;font-weight:700;color:var(--navy);min-height:32px}
.vnset ol{padding-left:22px;margin:8px 0}
.vnset input{width:100%;font:13px monospace;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
'''),
    ('''        <p class="hint">Type it, speak it with the microphone on your keyboard, or paste a to-do list from Voicenotes. <b>One line is one task.</b></p>
        <textarea id="ttext"''',
     '''        <p class="hint">Type it, speak it with the microphone on your keyboard, or paste it. A to-do list you make in Voicenotes arrives here by itself. <b>One line is one task.</b></p>
        <div id="vnbox" class="vn" role="group" aria-label="From Voicenotes" hidden></div>
        <textarea id="ttext"'''),
    ('''        <div class="foot"><button class="btn" id="tasssave" type="button">Save these names</button></div>
      </section>
''',
     '''        <div class="foot"><button class="btn" id="tasssave" type="button">Save these names</button></div>
        <details class="vnset" id="vnset"><summary>Voicenotes sending here by itself — set up once</summary>
          <ol>
            <li>In Voicenotes, click your picture (top right) → <b>Integrations</b> → <b>Webhooks</b> → <b>Add Webhook</b>.</li>
            <li>Paste the address below (the Copy button copies it).</li>
            <li>Tick <b>To-Do List Creation</b> only, then <b>Create</b>.</li>
          </ol>
          <input type="text" id="vnurl" readonly aria-label="The address for Voicenotes">
          <div class="foot"><button class="btn" id="vncopy" type="button">Copy the address</button></div>
          <p class="hint" id="vnseen"></p>
          <p class="hint">The address carries its own key: keep it to Voicenotes. A list then waits above the task box until you put it in and press Give.</p>
        </details>
      </section>
'''),
    ('''  /* ---------- September ---------- */
''',
     '''  /* ---------- S514: the to-do lists Voicenotes sends (they wait here; nothing is given until he presses Give) ---------- */
  var VN={items:[],seen:[],url:""}, vnPick={};
  function vnCall(body){ var o={method:body?"POST":"GET",credentials:"same-origin",cache:"no-store",headers:{}};
    if(body){ o.headers["Content-Type"]="application/json"; o.body=JSON.stringify(body) }
    return fetch("/finance/aaj/api/vn",o).then(function(x){
      if((x.headers.get("Content-Type")||"").indexOf("json")<0) throw new Error("server");
      return x.json().then(function(j){ if(!j.ok) throw new Error(j.error||"refused"); return j }) }) }
  function vnLoad(){ vnCall(null).then(function(j){ VN=j; drawVn() }, function(){ /* the panel works without it */ }) }
  function drawVn(){
    var box=$("vnbox"), its=VN.items||[]; box.textContent=""; box.hidden=!its.length;
    if(its.length){
      box.appendChild(el("h3",null,"From Voicenotes · "+its.length+(its.length===1?" line":" lines")));
      its.forEach(function(it){ if(vnPick[it.id]===undefined) vnPick[it.id]=true;
        var l=el("label","vnl"), i=el("input"); i.type="checkbox"; i.checked=!!vnPick[it.id]; i.onchange=function(){ vnPick[it.id]=i.checked };
        l.appendChild(i); l.appendChild(el("span",null,it.text)); l.appendChild(el("span","vnw",(it.title?(it.title+" · "):"")+stamp(it.at))); box.appendChild(l) });
      var f=el("div","foot"), b1=el("button","btn pri","Put the ticked ones in the box below"), b2=el("button","btn","Remove the ticked ones");
      b1.type="button"; b2.type="button";
      var ticked=function(){ return its.filter(function(it){return vnPick[it.id]}) };
      b1.onclick=function(){ var tk=ticked(); if(!tk.length)return; var t=$("ttext");
        t.value=(t.value.trim()?(t.value.replace(/\\s+$/,"")+"\\n"):"")+tk.map(function(it){return it.text}).join("\\n"); countTasks();
        vnCall({op:"used",ids:tk.map(function(it){return it.id})}).then(function(j){ VN=j; drawVn(); t.focus() },
          function(){ $("tmsg").textContent="Put in the box. The Voicenotes list could not be updated, so it may show them again." }) };
      b2.onclick=function(){ var tk=ticked(); if(!tk.length)return; b2.disabled=true;
        vnCall({op:"drop",ids:tk.map(function(it){return it.id})}).then(function(j){ VN=j; drawVn(); status("Removed "+hhmm()) }, function(e){ b2.disabled=false; sayErr(e) }) };
      f.appendChild(b1); f.appendChild(b2); box.appendChild(f);
    }
    $("vnurl").value=VN.url||""; $("vncopy").disabled=!VN.url;
    var s=(VN.seen||[])[0];
    $("vnseen").textContent=s?("Last received "+stamp(s.at)+": "+(s.event||"(no name)")+" — "+(s.why?s.why:(s.kept+" new line"+(s.kept===1?"":"s")))):"Nothing received from Voicenotes yet.";
  }
  $("vncopy").onclick=function(){ var u=$("vnurl"); if(!u.value)return; u.select();
    var done=function(){ status("Address copied "+hhmm()) }, old=function(){ try{ document.execCommand("copy"); done() }catch(e){} };
    try{ navigator.clipboard.writeText(u.value).then(done,old) }catch(e){ old() } };

  /* ---------- September ---------- */
'''),
    ('''      $("grid").hidden=false; status("All changes are saved by themselves."); drawAll(); drawTasks(); drawSept();
''',
     '''      $("grid").hidden=false; status("All changes are saved by themselves."); drawAll(); drawTasks(); drawSept(); vnLoad();
'''),
]


def md5b(b):
    return hashlib.md5(b).hexdigest()


def edit(path, edits, frm):
    raw = open(path, "rb").read()
    if md5b(raw) != frm:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, md5b(raw), frm))
    s = raw.decode("utf-8")
    for n, (a, b) in enumerate(edits, 1):
        got = s.count(a)
        if got != 1:
            raise SystemExit("!! %s anchor %d found %d time(s), expected 1 - nothing written" % (os.path.basename(path), n, got))
        s = s.replace(a, b)
    return s.encode("utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_s514.py <finance folder>")
    d = sys.argv[1]
    outs = {}
    for name, edits in (("finance_app.py", APP), ("aaj_panel.html", PANEL)):
        outs[name] = edit(os.path.join(d, name), edits, PINS[name][0])
    compile(outs["finance_app.py"], "finance_app.py", "exec")
    for name, b in outs.items():
        to = PINS[name][1]
        if not to.startswith("@@") and md5b(b) != to:
            raise SystemExit("!! %s would be %s, not the kit's %s - nothing written" % (name, md5b(b), to))
    for name, b in outs.items():
        with open(os.path.join(d, name), "wb") as fh:
            fh.write(b)
        print("%s -> %s" % (name, md5b(b)))


if __name__ == "__main__":
    main()
