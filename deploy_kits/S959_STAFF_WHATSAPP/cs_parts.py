# the pieces make_s959.py puts into calls_staff.py (S955's a93cdc86 -> S959's). Each OLD must appear exactly once.
DOC_OLD = 'The tile "My Call Console" is added to the portal\'s tile list at register time'
DOC_NEW = '''S959_STAFF_WHATSAPP (the parent, S524, 26-Nov-2026; roadmap B2): the WhatsApp tab's Reply opens the chat on this page --
the newest 30 messages, read only -- and, for a staff login, a text reply inside WhatsApp's 24-hour window (his saved
replies one tap away) or, after it, the approved templates named in PORTAL_STAFF_WA_TEMPLATES (default
"welcome_template", the Enquiry acknowledgement; only templates whose one field is the patient's name). Every send goes
through portal_inbox's own sender (staff_send_text / staff_send_template: the same key, log, 24-hour rule and retry as his
Inbox), signed with her login, so his Inbox shows who answered and the chat leaves the awaiting list by itself. The
reception mobile may reply too (it handles the front desk's chats; signed "reception"). The doctor's ?as= view and a
WhatsApp-Inbox login keep the Inbox link as before. Only a chat this page listed in the last hour can be read or answered.
PORTAL_STAFF_WA_SEND = "0" (or "off" / "no" / "false", written as a STRING -- the portal's reader treats an int 0 as unset)
takes the reply away and refuses the routes -- the page is then as S955's. Two phones cannot both answer one chat: the
guards (the same text twice; another person's answer in the last 2 minutes or since this chat was opened; a second approved
message after the patient's last) are read under one write lock with a 'sending' row put in the chat before the send.
  GET  /portal/console/staff/api/wa/chat?phone=  the chat (header X-Staff-Console: 1)
  POST /portal/console/staff/api/wa/send         {"phone10", "text"} (header X-Staff-Console: 1)
  POST /portal/console/staff/api/wa/template     {"phone10", "template", "name"} (header X-Staff-Console: 1)
The tile "My Call Console" is added to the portal's tile list at register time'''

K_OLD = 'KIT_S955 = "S955_RECEPTION_CONSOLE"\n'
K_NEW = '''KIT_S955 = "S955_RECEPTION_CONSOLE"
KIT_S959 = "S959_STAFF_WHATSAPP"   # B2: the WhatsApp tab's reply (VERSION stays "S951 1.1": S951's walk pins it)
WA_SEND_DEFAULT = "1"
WA_TEMPLATES_DEFAULT = "welcome_template"
WA_CHAT_ROWS = 30
'''

G_OLD = 'REBUILD_GAP_S = 60\n'
G_NEW = '''REBUILD_GAP_S = 60
_WA_OFFERED = {}               # S959: chat key -> when the WhatsApp tab last showed it (the reply routes serve only these)
_WA_REBUILT = [0.0]            # S959: its own once-a-minute re-read (not the call route's)
'''

P_OLD = "        _OFFERED.pop(k_, None)                           # the call route's memory holds the last hour only\n"
P_NEW = P_OLD + "    for k_ in [k_ for k_, v_ in _WA_OFFERED.items() if v_ < cut]:\n        _WA_OFFERED.pop(k_, None)                        # S959: the same hour for the reply routes\n"

W_OLD = '        rr["n"] = c.get("n", 1)\n        wa_rows.append(rr)\n'
W_NEW = '        rr["n"] = c.get("n", 1)\n        if c.get("phone"):\n            _WA_OFFERED[str(c["phone"])] = time.time()   # S959\n        wa_rows.append(rr)\n'

F_OLD = 'def section_rank(section, sent_back=False):\n'
F_NEW = '''def wa_send_on():
    """S959: PORTAL_STAFF_WA_SEND (default 1); "0" / "false" / "no" / "off" takes the WhatsApp reply off this page."""
    try:
        v = CC._CFG("PORTAL_STAFF_WA_SEND", None) if CC._CFG else None
    except Exception:
        v = None
    if v is None or str(v).strip() == "":
        v = _cfg("PORTAL_STAFF_WA_SEND", WA_SEND_DEFAULT)
    return str(v if v is not None else WA_SEND_DEFAULT).strip().lower() not in ("0", "false", "no", "off")


def _pi():
    """S959: portal_inbox -- the owner's Inbox module, whose sender the reply uses. None when it cannot be imported."""
    try:
        import portal_inbox
        return portal_inbox
    except Exception:
        return None


def wa_templates(name=""):
    """S959: the approved templates this page offers after the 24-hour window -- PORTAL_STAFF_WA_TEMPLATES (comma list,
    default welcome_template), only those in portal_wa's registry whose fields are the patient's name alone."""
    try:
        import portal_wa
        reg = portal_wa.TEMPLATES
    except Exception:
        return []
    out = []
    for k in str(_cfg("PORTAL_STAFF_WA_TEMPLATES", WA_TEMPLATES_DEFAULT) or "").split(","):
        k = k.strip()
        t = reg.get(k) if k else None
        if not t or k in [x["key"] for x in out]:
            continue
        fs = t.get("fields") or []
        if len(fs) != 1 or not fs[0].get("prefill"):
            continue
        prev = str(t.get("preview") or "").replace("{" + str(fs[0]["key"]) + "}", "[name]")
        out.append({"key": k, "title": t.get("title") or k, "preview": prev, "field": fs[0]["key"], "name": name})
    return out


def section_rank(section, sent_back=False):
'''

CSS_OLD = '</style></head><body><div class="wrap">'
CSS_NEW = ('.wap{margin-top:8px;border-top:1px dashed #c9d0d9;padding-top:8px}\n'
           '.wl{max-height:260px;overflow-y:auto;background:#f2f4f7;border-radius:10px;padding:6px;display:flex;flex-direction:column;gap:6px}\n'
           '.wm{max-width:88%;border-radius:10px;padding:6px 9px;font-size:14px;background:#fff;border:1px solid #d9dee5;white-space:pre-wrap;word-break:break-word}\n'
           '.wo{align-self:flex-end;background:#e3f4e6;border-color:#b9dcc0}\n'
           '.wt{display:block;font-size:11px;color:#4f5967;margin-bottom:2px}\n'
           '.wch{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}\n'
           '.wta{width:100%;box-sizing:border-box;font-size:15px;padding:8px;border:1px solid #c9d0d9;border-radius:8px;font-family:inherit;margin:6px 0}\n'
           '.wtp{background:#fff;border:1px solid #d9dee5;border-radius:10px;padding:8px;margin-top:6px;display:flex;flex-direction:column;gap:6px}\n'
           '.wtp input{font-size:14px;padding:8px;border:1px solid #c9d0d9;border-radius:8px;font-family:inherit}\n'
           + CSS_OLD)

MSG_OLD = '{% if r.msg %}<div class="msg">{{ r.msg }}</div>{% endif %}\n'
MSG_NEW = MSG_OLD + '{% if t.k == \'wa\' and wa_reply and not wa_ok_user and r.phone %}<div class="wap" hidden></div>{% endif %}\n'

B_OLD = '''{% if wa_ok_user and r.mid %}<a class="bwa" href="/portal/inbox?m={{ r.mid|urlencode }}">{{ 'Reply' if t.k == 'wa' else 'Chat' }}</a>{% endif %}'''
B_NEW = '''{% if wa_ok_user and r.mid %}<a class="bwa" href="/portal/inbox?m={{ r.mid|urlencode }}">{{ 'Reply' if t.k == 'wa' else 'Chat' }}</a>{% elif t.k == 'wa' and wa_reply and not wa_ok_user and r.phone %}<button type="button" class="bwa" data-ph="{{ r.phone }}" onclick="waOpen(this)">Reply</button>{% endif %}'''

RL_OLD = 'if(document.activeElement&&document.activeElement.tagName==="INPUT")return;location.reload();'
RL_NEW = 'if(document.activeElement&&(document.activeElement.tagName==="INPUT"||document.activeElement.tagName==="TEXTAREA"))return;if(document.querySelector(".wap:not([hidden])"))return;location.reload();'

JS_OLD = 'setInterval(function(){if(document.hidden)return;'
JS_NEW = r'''/* S959: the WhatsApp reply -- every message is put on the page with textContent, never as markup */
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
function waLine(box,m){var d=el("div","wm "+(m.dir==="out"?"wo":"wi"));d.appendChild(el("span","wt",(m.dir==="out"?("Clinic"+(m.by?" · "+m.by:"")):"Patient")+(m.when?" · "+m.when:"")+(m.st?" · "+m.st:"")));d.appendChild(document.createTextNode(m.text||""));box.appendChild(d);}
function waPost(u,o,b,done){b.disabled=true;fetch(u,{method:"POST",headers:H,body:JSON.stringify(o),credentials:"same-origin"}).then(function(r){return r.json();}).then(function(k){toast(k.msg||"");done(k);}).catch(function(){toast("No answer came back - the message may have gone. Close and open Reply to read the chat before sending again.");done({ok:false});}).then(function(){setTimeout(function(){b.disabled=false;},3000);});}
function waDraw(p,ph,j){p.textContent="";if(!j||!j.ok){p.appendChild(el("p","ps",(j&&j.msg)||"The chat could not be read just now."));return;}
var box=el("div","wl");(j.msgs||[]).forEach(function(m){waLine(box,m);});if(!(j.msgs||[]).length)box.appendChild(el("span","wt","No messages kept for this chat."));p.appendChild(box);box.scrollTop=box.scrollHeight;
if(!j.can_send){p.appendChild(el("p","ps",j.note||"Replies are sent from the WhatsApp Inbox."));return;}
if(j.window&&j.window.open){p.appendChild(el("p","ps","Reply window open · "+j.window.hours_left+" h left"));
var ta=el("textarea","wta");ta.rows=3;ta.maxLength=4000;ta.placeholder="Type your reply";ta.setAttribute("aria-label","Your reply");
if((j.replies||[]).length){var ch=el("div","wch");j.replies.forEach(function(r){var c=el("button","bsm",r.title);c.type="button";c.onclick=function(){ta.value=r.body;ta.focus();};ch.appendChild(c);});p.appendChild(ch);}
p.appendChild(ta);var s=el("button","bcall","Send");s.type="button";s.onclick=function(){var x=ta.value.trim();if(!x){toast("Type a message first.");return;}
waPost("/portal/console/staff/api/wa/send",{phone10:ph,text:x,upto:j.upto||""},s,function(k){if(k.ok){waLine(box,{dir:"out",by:j.me||"",when:"now",st:k.queued?"retrying":"sent",text:x});box.scrollTop=box.scrollHeight;ta.value="";}});};
var bt=el("div","btns");bt.appendChild(s);p.appendChild(bt);}
else{p.appendChild(el("p","ps","More than 24 hours since they last wrote. WhatsApp allows only an approved message now - or call them."));
(j.templates||[]).forEach(function(t){var w=el("div","wtp");w.appendChild(el("p","pn",t.title));w.appendChild(el("p","ps",t.preview));var nm=el("input");nm.type="text";nm.maxLength=60;nm.value=t.name||"";nm.placeholder="Patient's name";nm.setAttribute("aria-label","Patient's name");w.appendChild(nm);
var s2=el("button","bwa","Send this message");s2.type="button";s2.onclick=function(){var v=nm.value.trim();if(!v){toast("Write the patient's name first.");return;}
waPost("/portal/console/staff/api/wa/template",{phone10:ph,template:t.key,name:v},s2,function(k){if(k.ok){waLine(box,{dir:"out",by:j.me||"",when:"now",st:"",text:"Template: "+t.title});box.scrollTop=box.scrollHeight;}});};w.appendChild(s2);p.appendChild(w);});}}
window.waOpen=function(b){var p=b.closest(".pt").querySelector(".wap");if(!p)return;if(!p.hidden){p.hidden=true;b.textContent="Reply";return;}p.hidden=false;b.textContent="Close";p.textContent="Reading the chat…";
fetch("/portal/console/staff/api/wa/chat?phone="+encodeURIComponent(b.dataset.ph),{headers:{"X-Staff-Console":"1"},credentials:"same-origin"}).then(function(r){return r.json();}).then(function(j){waDraw(p,b.dataset.ph,j);}).catch(function(){p.textContent="The chat could not be read - check the connection and try again.";});};
setInterval(function(){if(document.hidden)return;'''

R_OLD = 'as_view=as_view, can_dispute=not doc, can_rec=not doc, wa_ok_user=wa_user)'
R_NEW = 'as_view=as_view, can_dispute=not doc, can_rec=not doc, wa_ok_user=wa_user,\n                                      wa_reply=wa_send_on() and not doc)'

RT_OLD = '    # the tile, beside the owner\'s "Call Console" -- display only; granted by name in tile_grants.json\n'
RT_NEW = '''    # S959 (B2): the WhatsApp tab's reply -- through portal_inbox's own sender; only a chat the tab listed in the last hour
    def _wa_listed(ph):
        t = _WA_OFFERED.get(ph)
        if ph and (t is None or time.time() - t > OFFER_KEEP_S) and time.time() - _WA_REBUILT[0] >= REBUILD_GAP_S:
            _WA_REBUILT[0] = time.time()                 # another worker drew the page: read the lists here (once a minute)
            try:
                _data((allowed_keys() or [""])[0])
            except Exception:
                pass
            t = _WA_OFFERED.get(ph)
        return bool(ph) and t is not None and time.time() - t <= OFFER_KEEP_S

    def _wa_sender():
        """(login, None) for a staff login this page serves with the reply on, else (None, (json, code))."""
        if request.headers.get("X-Staff-Console") != "1":
            return None, (jsonify({"ok": False, "msg": "bad request"}), 400)
        if not wa_send_on():
            return None, (jsonify({"ok": False, "msg": "Replies from this page are switched off - use the Call button."}), 403)
        login = _login()
        key = CC.login_key(login)
        if _doc() or not login or not key or key in CC.OWNER_FIRST or key not in allowed_keys():
            return None, (jsonify({"ok": False, "msg": "Replies from this page are for the staff logins - the doctor replies from his WhatsApp Inbox."}), 403)
        return login, None

    def _wa_body():
        b = request.get_json(silent=True)
        b = b if isinstance(b, dict) else {}
        return b, re.sub(r"\\D", "", str(b.get("phone10") or ""))

    @app.route("/portal/console/staff/api/wa/chat", endpoint="s959_staff_wa_chat")
    @staff_gate
    def _staff_wa_chat():
        if request.headers.get("X-Staff-Console") != "1":
            return jsonify({"ok": False, "msg": "bad request"}), 400
        _key, _as_view, doc = _viewer()
        ph = re.sub(r"\\D", "", str(request.args.get("phone") or ""))
        if not _wa_listed(ph):
            return jsonify({"ok": False, "msg": "This chat is not on your WhatsApp list now - reload the page."}), 409
        pi = _pi()
        if pi is None or not hasattr(pi, "staff_chat"):
            return jsonify({"ok": False, "msg": "The chat could not be read just now - try again in a few minutes."}), 503
        r = pi.staff_chat(ph, WA_CHAT_ROWS)
        if not r.get("ok"):
            return jsonify({"ok": False, "msg": r.get("msg") or "The chat could not be read just now."}), int(r.get("code") or 500)
        pts = {}
        try:
            conn = CC._H["console_conn"]() if CC._H.get("console_conn") else None
            if conn is not None:
                try:
                    pts = _pats(conn)
                finally:
                    conn.close()
        except Exception:
            pts = {}
        nm = (pts.get(ph) or {}).get("name") or r.get("name") or ""
        can = wa_send_on() and not doc
        resp = jsonify({"ok": True, "me": _login(), "window": r.get("window") or {}, "msgs": r.get("msgs") or [], "upto": r.get("upto") or "",
                        "replies": r.get("replies") or [], "templates": wa_templates(nm) if can else [], "can_send": can,
                        "note": "" if can else ("Replies from this page are switched off - use the Call button." if not doc
                                               else "You are seeing her page - reply from your WhatsApp Inbox.")})
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/console/staff/api/wa/send", methods=["POST"], endpoint="s959_staff_wa_send")
    @staff_gate
    def _staff_wa_send():
        login, bad = _wa_sender()
        if bad:
            return bad
        b, ph = _wa_body()
        if not _wa_listed(ph):
            return jsonify({"ok": False, "msg": "This chat is not on your WhatsApp list now - reload the page."}), 409
        pi = _pi()
        if pi is None or not hasattr(pi, "staff_send_text"):
            return jsonify({"ok": False, "msg": "Not sent - the WhatsApp sender is not reachable. Try again in a few minutes."}), 503
        r = pi.staff_send_text(ph, str(b.get("text") or ""), login, _CFG, seen_upto=str(b.get("upto") or "")[:40] or None)
        return jsonify({"ok": bool(r.get("ok")), "msg": r.get("msg") or "", "queued": bool(r.get("queued"))}), int(r.get("code") or 200)

    @app.route("/portal/console/staff/api/wa/template", methods=["POST"], endpoint="s959_staff_wa_template")
    @staff_gate
    def _staff_wa_template():
        login, bad = _wa_sender()
        if bad:
            return bad
        b, ph = _wa_body()
        if not _wa_listed(ph):
            return jsonify({"ok": False, "msg": "This chat is not on your WhatsApp list now - reload the page."}), 409
        t = next((x for x in wa_templates() if x["key"] == str(b.get("template") or "")), None)
        if t is None:
            return jsonify({"ok": False, "msg": "This message is not offered on this page."}), 400
        name = " ".join(str(b.get("name") or "").split())[:60]
        if not name:
            return jsonify({"ok": False, "msg": "Write the patient's name first."}), 400
        pi = _pi()
        if pi is None or not hasattr(pi, "staff_send_template"):
            return jsonify({"ok": False, "msg": "Not sent - the WhatsApp sender is not reachable. Try again in a few minutes."}), 503
        r = pi.staff_send_template(ph, t["key"], {t["field"]: name}, login, _CFG)
        return jsonify({"ok": bool(r.get("ok")), "msg": r.get("msg") or "", "mode": r.get("mode") or ""}), int(r.get("code") or 200)

''' + RT_OLD

PARTS = [(DOC_OLD, DOC_NEW), (K_OLD, K_NEW), (G_OLD, G_NEW), (P_OLD, P_NEW), (W_OLD, W_NEW), (F_OLD, F_NEW),
         (CSS_OLD, CSS_NEW), (MSG_OLD, MSG_NEW), (B_OLD, B_NEW), (RL_OLD, RL_NEW), (JS_OLD, JS_NEW), (R_OLD, R_NEW),
         (RT_OLD, RT_NEW)]
