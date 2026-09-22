#!/usr/bin/env python3
# portal_push.py -- kit S366_RING_POPUP (session 279, 22-Sep-2026)
# The portal's half of the ring-time pop-up: serves the service worker, hands out the public push key, stores
# each phone's push subscription under the signed-in login, and asks the ring-hook service (127.0.0.1) for a
# test pop-up. portal.py calls install(app, login_required, sso_user) once; nothing else in portal.py changes.
import json
import os
import urllib.request

from flask import request, jsonify, make_response, send_file

import ring_common as rc

SW_FILE = os.path.join(rc.PORTAL_DIR, "portal_sw.js")


def _env():
    return rc.load_env()


def _ring_port(env):
    try:
        return int(env.get("RING_HOOK_PORT") or "8110")
    except ValueError:
        return 8110


def install(app, login_required, sso_user):
    @app.route("/portal/sw.js")
    def portal_sw():
        resp = make_response(send_file(SW_FILE, mimetype="application/javascript"))
        resp.headers["Cache-Control"] = "no-cache"
        resp.headers["Service-Worker-Allowed"] = "/portal/"
        return resp

    @app.route("/portal/push/key")
    def push_key():
        env = _env()
        key = env.get("VAPID_PUBLIC", "")
        return jsonify({"ok": bool(key), "key": key})

    @app.route("/portal/push/status")
    @login_required
    def push_status():
        who = sso_user(request) or {}
        user = who.get("user", "")
        agents = rc.load_agents()
        is_agent = any((a or {}).get("user") == user for a in agents.values())
        return jsonify({"ok": True, "user": user, "agent": is_agent, "subs": len(rc.subs_for(user)),
                        "ready": bool(_env().get("VAPID_PUBLIC"))})

    @app.route("/portal/push/subscribe", methods=["POST"])
    @login_required
    def push_subscribe():
        who = sso_user(request) or {}
        user = who.get("user", "")
        if not user:
            return jsonify({"ok": False, "error": "no login"}), 401
        body = request.get_json(silent=True) or {}
        sub = body.get("subscription") if isinstance(body.get("subscription"), dict) else body
        ok = rc.add_sub(user, sub, ua=request.headers.get("User-Agent", ""))
        return jsonify({"ok": ok, "subs": len(rc.subs_for(user))}), (200 if ok else 400)

    @app.route("/portal/push/unsubscribe", methods=["POST"])
    @login_required
    def push_unsubscribe():
        who = sso_user(request) or {}
        user = who.get("user", "")
        body = request.get_json(silent=True) or {}
        ok = rc.remove_sub(user, str(body.get("endpoint") or ""))
        return jsonify({"ok": ok, "subs": len(rc.subs_for(user))})

    @app.route("/portal/push/test", methods=["POST"])
    @login_required
    def push_test():
        who = sso_user(request) or {}
        user = who.get("user", "")
        env = _env()
        key = env.get("RING_INTERNAL_KEY", "")
        if not (user and key):
            return jsonify({"ok": False, "error": "not configured"}), 503
        try:
            req = urllib.request.Request("http://127.0.0.1:%d/ring-hook/test" % _ring_port(env),
                                         data=json.dumps({"user": user}).encode("utf-8"),
                                         headers={"Content-Type": "application/json", "X-Internal-Key": key}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                return jsonify(json.loads(r.read().decode("utf-8") or "{}"))
        except Exception as e:  # noqa: BLE001
            return jsonify({"ok": False, "error": type(e).__name__}), 502


# The card on the portal home. Shown only to a login that owns a ringing phone (ring_agents.json); the doctor's
# phone is not in the MyOperator call flow (owner, 21-Sep-2026) so he never sees it. Staff-facing -> Hindi.
CARD_HTML = """
<div id="pushCard" class="card" style="display:none;margin:0 0 12px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--card)">
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <div style="font-size:26px">\U0001F4F3</div>
    <div style="flex:1;min-width:180px">
      <div style="font-weight:600">कॉल आने पर मरीज़ का नाम</div>
      <div id="pushMsg" style="color:var(--muted);font-size:13px">फ़ोन बजते ही नाम और पुरानी visit यहाँ दिखेगी</div>
    </div>
    <button id="pushBtn" onclick="pushEnable()" style="background:var(--blue);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-size:15px;font-weight:600">सूचना चालू करें</button>
    <button id="pushTestBtn" onclick="pushTest()" style="display:none;background:transparent;color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:9px 14px;font-size:14px">Test</button>
  </div>
</div>
"""

CARD_JS = r"""
/* S366: ring-time pop-up -- enable, keep fresh, test */
function _pushSay(t){ var m=document.getElementById('pushMsg'); if(m) m.textContent=t; }
function _b64u(s){ var p='='.repeat((4-s.length%4)%4); var b=atob((s+p).replace(/-/g,'+').replace(/_/g,'/')); var a=new Uint8Array(b.length); for(var i=0;i<b.length;i++)a[i]=b.charCodeAt(i); return a; }
async function _pushSubscribe(){
  var k=await (await fetch('/portal/push/key',{cache:'no-store'})).json(); if(!k.ok) throw new Error('nokey');
  var reg=await navigator.serviceWorker.register('/portal/sw.js',{scope:'/portal/'});
  await navigator.serviceWorker.ready;
  var sub=await reg.pushManager.getSubscription();
  if(!sub) sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:_b64u(k.key)});
  var r=await fetch('/portal/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub.toJSON()})});
  if(!r.ok) throw new Error('save');
  return sub;
}
async function pushEnable(){
  var b=document.getElementById('pushBtn'); if(b) b.disabled=true;
  try{
    var perm=await Notification.requestPermission();
    if(perm!=='granted'){ _pushSay('सूचना बंद है — फ़ोन की Settings → Apps → Chrome → Notifications चालू करें'); if(b) b.disabled=false; return; }
    await _pushSubscribe();
    _pushSay('✅ चालू — test सूचना भेजी गई');
    if(b) b.style.display='none'; var t=document.getElementById('pushTestBtn'); if(t) t.style.display='';
    pushTest();
  }catch(e){ _pushSay('नहीं हो पाया (' + (e&&e.message||e) + ') — दोबारा दबाएँ'); if(b) b.disabled=false; }
}
async function pushTest(){
  try{ var r=await (await fetch('/portal/push/test',{method:'POST'})).json();
       _pushSay(r.ok?'✅ test सूचना भेजी गई — ऊपर देखें':'test नहीं पहुँची — सूचना दोबारा चालू करें'); }
  catch(e){ _pushSay('server से जवाब नहीं'); }
}
(async function(){
  try{
    if(!('serviceWorker' in navigator)||!('PushManager' in window)||!('Notification' in window)) return;
    var st=await (await fetch('/portal/push/status',{cache:'no-store'})).json();
    if(!st||!st.ok||!st.agent||!st.ready) return;
    var card=document.getElementById('pushCard'); if(card) card.style.display='';
    if(Notification.permission==='granted'){
      try{ await _pushSubscribe(); }catch(e){}
      _pushSay('✅ कॉल सूचना चालू है');
      var b=document.getElementById('pushBtn'); if(b) b.style.display='none'; var t=document.getElementById('pushTestBtn'); if(t) t.style.display='';
    } else if(Notification.permission==='denied'){
      _pushSay('सूचना बंद है — फ़ोन की Settings → Apps → Chrome → Notifications चालू करें');
    }
  }catch(e){}
})();
"""
