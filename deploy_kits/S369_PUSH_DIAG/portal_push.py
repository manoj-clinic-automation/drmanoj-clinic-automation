#!/usr/bin/env python3
# portal_push.py -- kit S366_RING_POPUP + S369_PUSH_DIAG (session 279, 22-Sep-2026)
# The portal's half of the ring-time pop-up: serves the service worker, hands out the public push key, stores
# each phone's push subscription under the signed-in login, and asks the ring-hook service (127.0.0.1) for a
# test pop-up. portal.py calls install(app, login_required, sso_user) once; nothing else in portal.py changes.
import json
import os
import urllib.request

from flask import request, jsonify, make_response, send_file

import ring_common as rc

SW_FILE = os.path.join(rc.PORTAL_DIR, "portal_sw.js")
DIAG_FILE = os.environ.get("PUSH_DIAG_FILE", os.path.join(rc.PORTAL_DIR, "push_diag.json"))


def _now_ist():
    from datetime import datetime, timezone, timedelta
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S")


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

    @app.route("/portal/push/diag", methods=["POST"])
    @login_required
    def push_diag_post():
        """S369: the card tells the portal what happened on the phone (permission, standalone, error, UA), so the
        assistant can read it from the doctor's browser instead of asking staff to describe their screen."""
        who = sso_user(request) or {}
        user = who.get("user", "")
        body = request.get_json(silent=True) or {}
        rec = {"when_ist": _now_ist(), "step": str(body.get("step") or "")[:40], "perm": str(body.get("perm") or "")[:20],
               "standalone": bool(body.get("standalone")), "error": str(body.get("error") or "")[:200],
               "sw": str(body.get("sw") or "")[:40], "ua": request.headers.get("User-Agent", "")[:160]}
        try:
            d = rc._read_json(DIAG_FILE, {"users": {}})
            lst = d.setdefault("users", {}).setdefault(user, [])
            lst.append(rec)
            d["users"][user] = lst[-12:]
            rc._atomic_write_json(DIAG_FILE, d)
        except Exception:
            pass
        return jsonify({"ok": True})

    @app.route("/portal/push/diag")
    @login_required
    def push_diag_get():
        who = sso_user(request) or {}
        if who.get("role") != "doctor":
            return jsonify({"ok": False}), 403
        d = rc._read_json(DIAG_FILE, {"users": {}})
        subs = rc.load_subs()["users"]
        return jsonify({"ok": True, "subscribed": {u: len(l) for u, l in subs.items() if l},
                        "attempts": d.get("users", {})})

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
      <div style="font-weight:600">\u0915\u0949\u0932 \u0906\u0928\u0947 \u092a\u0930 \u092e\u0930\u0940\u091c\u093c \u0915\u093e \u0928\u093e\u092e</div>
      <div id="pushMsg" style="color:var(--muted);font-size:13px">\u092b\u093c\u094b\u0928 \u092c\u091c\u0924\u0947 \u0939\u0940 \u0928\u093e\u092e \u0914\u0930 \u092a\u0941\u0930\u093e\u0928\u0940 visit \u092f\u0939\u093e\u0901 \u0926\u093f\u0916\u0947\u0917\u0940</div>
    </div>
    <button id="pushBtn" onclick="pushEnable()" style="background:var(--blue);color:#fff;border:0;border-radius:10px;padding:10px 16px;font-size:15px;font-weight:600">\u0938\u0942\u091a\u0928\u093e \u091a\u093e\u0932\u0942 \u0915\u0930\u0947\u0902</button>
    <button id="pushTestBtn" onclick="pushTest()" style="display:none;background:transparent;color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:9px 14px;font-size:14px">Test</button>
  </div>
  <div id="pushState" style="display:none;margin-top:10px;padding:10px 12px;border-radius:8px;background:#3b2a12;color:#ffd58a;font-size:14px;line-height:1.5"></div>
</div>
"""

CARD_JS = r"""
/* S366 + S369: ring-time pop-up -- enable, keep fresh, test, and REPORT what happened */
function _pushSay(t){ var m=document.getElementById('pushMsg'); if(m) m.textContent=t; }
function _pushState(t, warn){ var s=document.getElementById('pushState'); if(!s) return; if(!t){ s.style.display='none'; return; } s.style.display=''; s.textContent=t; s.style.background=warn?'#4a1d1d':'#1d3b2a'; s.style.color=warn?'#ffb4b4':'#a7f3c4'; }
function _pushDiag(step, extra){ try{ var d={step:step, perm:(window.Notification?Notification.permission:'none'), standalone:!!(window.matchMedia&&window.matchMedia('(display-mode: standalone)').matches)}; if(extra) for(var k in extra) d[k]=extra[k]; fetch('/portal/push/diag',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).catch(function(){}); }catch(e){} }
function _b64u(s){ var p='='.repeat((4-s.length%4)%4); var b=atob((s+p).replace(/-/g,'+').replace(/_/g,'/')); var a=new Uint8Array(b.length); for(var i=0;i<b.length;i++)a[i]=b.charCodeAt(i); return a; }
function _withTimeout(p, ms, label){ return Promise.race([p, new Promise(function(_,rej){ setTimeout(function(){ rej(new Error(label||'timeout')); }, ms); })]); }
async function _pushSubscribe(){
  var k=await (await fetch('/portal/push/key',{cache:'no-store'})).json(); if(!k.ok) throw new Error('nokey');
  var reg=await _withTimeout(navigator.serviceWorker.register('/portal/sw.js',{scope:'/portal/'}), 15000, 'sw-register-timeout');
  await _withTimeout(navigator.serviceWorker.ready, 15000, 'sw-ready-timeout');
  var sub=await reg.pushManager.getSubscription();
  if(!sub) sub=await _withTimeout(reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:_b64u(k.key)}), 20000, 'subscribe-timeout');
  var r=await fetch('/portal/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub.toJSON()})});
  if(!r.ok) throw new Error('save-'+r.status);
  return sub;
}
var DENIED_TXT='सूचना बंद है (blocked) — फ़ोन की Settings → Apps → Chrome → Notifications चालू करें; फिर Chrome → Settings → Site settings → Notifications में followup.dr-manoj.in को Allow करें; फिर यहाँ दोबारा दबाएँ';
async function pushEnable(){
  var b=document.getElementById('pushBtn'); if(b) b.disabled=true;
  _pushState('रुकें… Chrome से अनुमति माँग रहे हैं (ऊपर पूछे तो Allow दबाएँ)', false);
  _pushDiag('tap');
  try{
    var perm;
    try{ perm=await _withTimeout(Notification.requestPermission(), 25000, 'permission-timeout'); }
    catch(e){ if(String(e&&e.message).indexOf('permission-timeout')>=0){ _pushDiag('permission-timeout'); _pushState('Chrome ने पूछा ही नहीं — address bar में घंटी (bell) का निशान दबाएँ और Allow चुनें, या Chrome → Site settings → Notifications में followup.dr-manoj.in को Allow करें', true); if(b) b.disabled=false; return; } throw e; }
    if(perm!=='granted'){ _pushDiag('perm-'+perm); _pushState(DENIED_TXT, true); if(b) b.disabled=false; return; }
    _pushState('अनुमति मिली — फ़ोन को जोड़ रहे हैं…', false);
    await _pushSubscribe();
    _pushDiag('subscribed');
    _pushSay('✅ चालू — test सूचना भेजी गई');
    _pushState('✅ चालू — अब test सूचना आनी चाहिए', false);
    if(b) b.style.display='none'; var t=document.getElementById('pushTestBtn'); if(t) t.style.display='';
    pushTest();
  }catch(e){ var msg=(e&&(e.name+': '+e.message))||String(e); _pushDiag('error', {error: msg}); _pushState('नहीं हो पाया — ' + msg + ' — दोबारा दबाएँ', true); if(b) b.disabled=false; }
}
async function pushTest(){
  try{ var r=await (await fetch('/portal/push/test',{method:'POST'})).json(); _pushDiag('test', {error: r.ok?'':('sent='+r.sent+' failed='+r.failed)});
       _pushSay(r.ok?'✅ test सूचना भेजी गई — ऊपर देखें':'test नहीं पहुँची — सूचना दोबारा चालू करें'); }
  catch(e){ _pushSay('server से जवाब नहीं'); }
}
(async function(){
  try{
    if(!('serviceWorker' in navigator)||!('PushManager' in window)||!('Notification' in window)){ _pushDiag('unsupported', {error: navigator.userAgent.slice(0,80)}); return; }
    var st=await (await fetch('/portal/push/status',{cache:'no-store'})).json();
    if(!st||!st.ok||!st.agent||!st.ready) return;
    var card=document.getElementById('pushCard'); if(card) card.style.display='';
    _pushDiag('load', {sw: (await navigator.serviceWorker.getRegistrations()).length + ' reg'});
    if(Notification.permission==='granted'){
      try{ await _pushSubscribe(); _pushDiag('refreshed'); }catch(e){ _pushDiag('refresh-error', {error: String(e&&e.message||e)}); }
      _pushSay('✅ कॉल सूचना चालू है');
      var b=document.getElementById('pushBtn'); if(b) b.style.display='none'; var t=document.getElementById('pushTestBtn'); if(t) t.style.display='';
    } else if(Notification.permission==='denied'){
      _pushState(DENIED_TXT, true);
    }
  }catch(e){ _pushDiag('load-error', {error: String(e&&e.message||e)}); }
})();
"""
