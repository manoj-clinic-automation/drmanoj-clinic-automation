#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
portal_wa.py — Shared WhatsApp sender for the clinic portal (S172, Phase A)
===========================================================================
ONE canonical sender that any portal page can call, backed by the MyOperator
WABA that is already live for the clinic (System B). Built from the
confirmed-200 contract in API_QUICK_REFERENCE_CARD (hash-pinned KB), NOT memory.

WABA hard rule (why this is template-driven):
  Outside a patient's 24-hour reply window, ONLY approved templates may be sent
  — free text is refused by WhatsApp. So Phase A sends approved templates only;
  free-text session replies (for agents in the GAS tracker) are Phase B.

SEND CONTRACT (System B, confirmed 200):
  POST https://publicapi.myoperator.co/chat/messages
  Headers: Authorization: Bearer <MYOP_AUTH_TOKEN>   (capital B required)
           X-MYOP-COMPANY-ID: 68384350414b9847
           Content-Type: application/json
  Body:  { "phone_number_id":"1090067637530949","customer_country_code":"91",
           "customer_number":"<10 digits>",
           "data":{"type":"template","context":{
               "template_name":..., "language":..., "body":{...}}},
           "reply_to":null,"myop_ref_id":null }
  Body-key format SPLITS BY FAMILY:
    drmanoj_*  -> NUMERIC keys "1","2","3", language "en"
    all others -> NAMED keys exactly as registered (var_1, var_2, ...)
  Success: 200 {status:success,...,data:{conversation_id, message_id}}

SAFETY RAILS
  * DRY-RUN default ON (PORTAL_WA_DRYRUN != "0"): the whole UI works but NOTHING
    real is sent — every call is logged as DRY and returns a simulated id. Flip
    to live only after testing to your own number.
  * Token read from portal config / env (MYOP_AUTH_TOKEN) — NEVER logged/printed.
  * Every attempt (dry or live) is appended to an outbound log (single writer).
  * Phones are stored full in the log (records) but callers should mask to last-4
    on screen.
"""

import os, csv, json, re, ssl, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

BASE            = "https://publicapi.myoperator.co"
SEND_PATH       = "/chat/messages"
COMPANY_ID      = "68384350414b9847"
PHONE_NUMBER_ID = "1090067637530949"
IST             = timezone(timedelta(hours=5, minutes=30))

WA_DIR = os.environ.get("PORTAL_WA_DIR", "/root/wa/wa_portal")
LOG    = os.path.join(WA_DIR, "wa_portal_sends.csv")
LOG_COLS = ["ts_ist", "sent_by", "phone", "template", "values_json",
            "mode", "ok", "message_id", "conversation_id", "error"]

# --- template registry: the 10 manually-sendable approved templates (S137) ---
# Panel-automation templates (new_post_call_message, *missedaftercall) and the
# stray daily_account_summary are intentionally EXCLUDED — they fire by panel,
# not by hand. field = (key, human label, prefill_from_name)
TEMPLATES = {
    "drmanoj_post_visit": {
        "family": "numeric", "lang": "en", "group": "Follow-up",
        "title": "Post-visit (same day)",
        "fields": [{"key":"1","label":"Patient name","prefill":True,"type":"text"}],
        "preview": "Namaskar {1} ji, Dr. Manoj Agarwal Clinic mein aaj aapki visit "
                   "complete hui. \u0936\u0940\u0918\u094d\u0930 \u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f \u0932\u093e\u092d "
                   "ki shubhkaamnaayein. (Docterz app / follow-up date on prescription)"},
    "drmanoj_followup_tomorrow": {
        "family": "numeric", "lang": "en", "group": "Follow-up",
        "title": "Follow-up due tomorrow",
        "fields": [{"key":"1","label":"Patient name","prefill":True,"type":"text"}, {"key":"2","label":"Follow-up date","prefill":False,"type":"date"}],
        "preview": "Namaskar {1} ji, aapka follow-up kal scheduled hai. "
                   "Follow-up Date: {2}. Aane se pehle call karke time confirm karein."},
    "drmanoj_followup_due": {
        "family": "numeric", "lang": "en", "group": "Follow-up",
        "title": "Follow-up due today (0\u20133 days)",
        "fields": [{"key":"1","label":"Patient name","prefill":True,"type":"text"}, {"key":"2","label":"Follow-up date","prefill":False,"type":"date"}],
        "preview": "Namaskar {1} ji, aapka follow-up {2} ko tha jo abhi tak nahi "
                   "hua. Kripya jald clinic aayen ya appointment book karein."},
    "drmanoj_followup_missed": {
        "family": "numeric", "lang": "en", "group": "Follow-up",
        "title": "Follow-up missed (4\u201310 days)",
        "fields": [{"key":"1","label":"Patient name","prefill":True,"type":"text"}, {"key":"2","label":"Follow-up date","prefill":False,"type":"date"}],
        "preview": "Namaskar {1} ji, aapke treatment plan mein {2} ko ek follow-up "
                   "scheduled tha. Bina follow-up ke poora faida nahi milta."},
    "drmanoj_followup_dropout": {
        "family": "numeric", "lang": "en", "group": "Follow-up",
        "title": "Dropout (10+ days)",
        "fields": [{"key":"1","label":"Patient name","prefill":True,"type":"text"}, {"key":"2","label":"Follow-up date","prefill":False,"type":"date"},
                   {"key":"3","label":"Days overdue","prefill":False,"type":"number","auto_from":"2"}],
        "preview": "Namaskar {1} ji, {2} ko follow-up tha \u2014 ab {3} din ho chuke "
                   "hain. Regular follow-up zaroori hai. Ek baar zaroor batayein."},
    "appointment_confirmation_ortho": {
        "family": "named", "lang": "en", "group": "Appointment",
        "title": "Appointment confirmed",
        "fields": [{"key":"var_1","label":"Patient name","prefill":True,"type":"text"}, {"key":"var_2","label":"Date & time","prefill":False,"type":"datetime"}],
        "preview": "Hi {var_1}, your appointment with Dr. Manoj Agarwal is booked. "
                   "Date & Time: {var_2}. Kindly arrive 15 minutes early."},
    "appointment_reminder_1day_ortho": {
        "family": "named", "lang": "en", "group": "Appointment",
        "title": "Appointment reminder (tomorrow)",
        "fields": [{"key":"var_1","label":"Patient name","prefill":True,"type":"text"}, {"key":"var_2","label":"Date & time","prefill":False,"type":"datetime"}],
        "preview": "Hi {var_1}, gentle reminder \u2014 your appointment is tomorrow. "
                   "Date & Time: {var_2}. Please arrive 15 minutes early."},
    "reschedule_confirmation": {
        "family": "named", "lang": "hi", "group": "Appointment",
        "title": "Appointment rescheduled",
        "fields": [{"key":"var_1","label":"Patient name","prefill":True,"type":"text"}, {"key":"var_2","label":"New date/time","prefill":False,"type":"datetime"}],
        "preview": "\u0928\u092e\u0938\u094d\u0924\u0947 {var_1}, \u0906\u092a\u0915\u093e "
                   "\u0905\u092a\u0949\u0907\u0902\u091f\u092e\u0947\u0902\u091f reschedule \u0915\u0930 "
                   "\u0926\u093f\u092f\u093e \u0917\u092f\u093e \u0939\u0948\u0964 \u0928\u092f\u093e "
                   "\u0938\u092e\u092f: {var_2}"},
    "welcome_template": {
        "family": "named", "lang": "hi", "group": "Enquiry",
        "title": "Enquiry acknowledgement",
        "fields": [{"key":"var_1","label":"Patient name","prefill":True,"type":"text"}],
        "preview": "\u0928\u092e\u0938\u094d\u0915\u093e\u0930 {var_1}, \u0921\u0949. \u092e\u0928\u094b\u091c "
                   "\u0905\u0917\u094d\u0930\u0935\u093e\u0932 \u0938\u0947 \u0938\u0902\u092a\u0930\u094d\u0915 "
                   "\u0915\u0947 \u0932\u093f\u090f \u0927\u0928\u094d\u092f\u0935\u093e\u0926\u0964 "
                   "\u091f\u0940\u092e \u091c\u0932\u094d\u0926 \u0938\u0902\u092a\u0930\u094d\u0915 \u0915\u0930\u0947\u0917\u0940\u0964"},
    "decline_acknowledgement_manoj": {
        "family": "named", "lang": "en", "group": "Enquiry",
        "title": "Opt-out acknowledgement",
        "fields": [{"key":"var_1","label":"Patient name","prefill":True,"type":"text"}],
        "preview": "Hi {var_1}, thank you for informing us. We will not send further "
                   "messages regarding this inquiry."},
}


# --------------------------- helpers ---------------------------------------- #
def normalize_phone(raw):
    """Return a 10-digit Indian mobile, or None. Accepts +91.., 0.., 91.., spaces."""
    d = re.sub(r"\D", "", str(raw or ""))
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    if len(d) == 10 and d[0] in "6789":
        return d
    return None


def mask_phone(raw):
    d = re.sub(r"\D", "", str(raw or ""))
    return ("\u2022\u2022\u2022\u2022" + d[-4:]) if len(d) >= 4 else "\u2022\u2022\u2022\u2022"


def build_body(template_name, values):
    """Build the WABA body dict with family-correct keys. Raises ValueError with
    a plain-language message if the template is unknown or a field is missing."""
    t = TEMPLATES.get(template_name)
    if not t:
        raise ValueError("unknown template: %s" % template_name)
    body = {}
    for f in t["fields"]:
        key = f["key"]; label = f["label"]
        v = (values or {}).get(key, "")
        if isinstance(v, str):
            v = v.strip()
        if v in (None, ""):
            raise ValueError("missing value for '%s' (%s)" % (label, key))
        body[key] = str(v)
    return t, body


def _log(row):
    os.makedirs(WA_DIR, exist_ok=True)
    new = not os.path.exists(LOG)
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in LOG_COLS})


# --------------------------- the sender ------------------------------------- #
def send(phone, template_name, values, sent_by, token, dry_run=True, timeout=20):
    """Send one approved-template WhatsApp. Returns a dict:
       {ok, message_id, conversation_id, error, mode}. Never raises to the caller
       for send/HTTP failures — they come back as ok:False + a plain error."""
    now = datetime.now(IST).isoformat(timespec="seconds")
    ph = normalize_phone(phone)
    if not ph:
        r = {"ok": False, "error": "not a valid 10-digit mobile: %s" % mask_phone(phone),
             "mode": "reject"}
        _log({"ts_ist": now, "sent_by": sent_by, "phone": str(phone),
              "template": template_name, "values_json": json.dumps(values or {}),
              "mode": "reject", "ok": "0", "error": r["error"]})
        return r
    try:
        t, body = build_body(template_name, values)
    except ValueError as e:
        r = {"ok": False, "error": str(e), "mode": "reject"}
        _log({"ts_ist": now, "sent_by": sent_by, "phone": ph,
              "template": template_name, "values_json": json.dumps(values or {}),
              "mode": "reject", "ok": "0", "error": str(e)})
        return r

    payload = {
        "phone_number_id": PHONE_NUMBER_ID,
        "customer_country_code": "91",
        "customer_number": ph,
        "data": {"type": "template", "context": {
            "template_name": template_name, "language": t["lang"], "body": body}},
        "reply_to": None, "myop_ref_id": None,
    }

    # ---- DRY-RUN: log + simulate, never touch the API ----
    if dry_run:
        mid = "DRYRUN-" + datetime.now(IST).strftime("%Y%m%d%H%M%S")
        _log({"ts_ist": now, "sent_by": sent_by, "phone": ph, "template": template_name,
              "values_json": json.dumps(values or {}), "mode": "DRY", "ok": "1",
              "message_id": mid, "conversation_id": "", "error": ""})
        return {"ok": True, "message_id": mid, "conversation_id": "",
                "mode": "DRY", "error": ""}

    # ---- LIVE send ----
    if not token:
        r = {"ok": False, "error": "MYOP_AUTH_TOKEN not configured in the portal env",
             "mode": "LIVE"}
        _log({"ts_ist": now, "sent_by": sent_by, "phone": ph, "template": template_name,
              "values_json": json.dumps(values or {}), "mode": "LIVE", "ok": "0",
              "error": r["error"]})
        return r

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + SEND_PATH, data=data, method="POST")
    req.add_header("Authorization", "Bearer " + token)   # capital B required
    req.add_header("X-MYOP-COMPANY-ID", COMPANY_ID)
    req.add_header("Content-Type", "application/json")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8", "replace")
        j = json.loads(raw) if raw else {}
        d = j.get("data") or {}
        mid = d.get("message_id", "")
        cid = d.get("conversation_id") or d.get("conversaton_id") or ""  # misspelling seen in webhooks
        ok = (j.get("status") == "success") or bool(mid)
        r = {"ok": ok, "message_id": mid, "conversation_id": cid, "mode": "LIVE",
             "error": "" if ok else ("unexpected response: " + raw[:200])}
    except urllib.error.HTTPError as e:
        body_err = ""
        try:
            body_err = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        r = {"ok": False, "message_id": "", "conversation_id": "", "mode": "LIVE",
             "error": "HTTP %s: %s" % (e.code, body_err or e.reason)}
    except Exception as e:
        r = {"ok": False, "message_id": "", "conversation_id": "", "mode": "LIVE",
             "error": "send failed: %s" % e}

    _log({"ts_ist": now, "sent_by": sent_by, "phone": ph, "template": template_name,
          "values_json": json.dumps(values or {}), "mode": "LIVE",
          "ok": "1" if r["ok"] else "0", "message_id": r.get("message_id", ""),
          "conversation_id": r.get("conversation_id", ""), "error": r.get("error", "")})
    return r


def registry_public():
    """The template list for the front-end (no secrets)."""
    out = []
    for name, t in TEMPLATES.items():
        out.append({"name": name, "title": t["title"], "group": t["group"],
                    "lang": t["lang"], "preview": t["preview"],
                    "fields": [{"key": f["key"], "label": f["label"],
                                "prefill_name": f["prefill"],
                                "type": f.get("type","text"),
                                "auto_from": f.get("auto_from","")}
                               for f in t["fields"]]})
    out.sort(key=lambda x: (x["group"], x["title"]))
    return out


# ===========================================================================
# PORTAL WIRING (Phase A) — routes, standalone page, drop-in widget
# ===========================================================================
import sqlite3
CONSOLE_DB = os.environ.get("PORTAL_CONSOLE_DB", "/root/wa/console.db")


def _wa_search(q):
    """Read-only patient lookup from console.db (same mirror casepack uses)."""
    q = (q or "").strip()
    if len(q) < 2 or not os.path.exists(CONSOLE_DB):
        return []
    ql = q.lower(); qd = re.sub(r"\D", "", q)
    conn = sqlite3.connect("file:%s?mode=ro" % CONSOLE_DB, uri=True)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT phone10,name,age,gender,clinic_id FROM patients").fetchall()
    finally:
        conn.close()
    out = []
    for m in rows:
        nm = (m["name"] or "").strip(); mob = (m["phone10"] or "").strip()
        cid = (m["clinic_id"] or "").strip()
        if (ql in nm.lower()) or (q == cid) or (len(qd) >= 4 and qd in re.sub(r"\D", "", mob)):
            out.append({"name": nm, "phone": mob, "age": (m["age"] or "").strip(),
                        "sex": (m["gender"] or "").strip(), "clinic_id": cid})
        if len(out) >= 20:
            break
    return out


WIDGET_JS = r"""
(function(){
  var TPL=null, DRY=true, loaded=false;
  function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function mask(p){var d=(''+p).replace(/\D/g,'');
    return d.length>=4?'\u2022\u2022\u2022\u2022'+d.slice(-4):'\u2022\u2022\u2022\u2022';}
  function styleOnce(){
    if(document.getElementById('wawidget-css'))return;
    var s=document.createElement('style');s.id='wawidget-css';
    s.textContent=".waw-ov{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;"
    +"align-items:flex-start;justify-content:center;padding:18px 10px;overflow:auto;z-index:9999}"
    +".waw-box{background:#2F3E3D;color:#E7EEEC;border:1px solid #3D4F4D;border-radius:14px;"
    +"max-width:520px;width:100%;padding:16px;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif}"
    +".waw-box h3{margin:0 0 4px;font-size:17px}.waw-sub{color:#9DB0AC;font-size:12.5px;margin-bottom:10px}"
    +".waw-dry{background:rgba(224,179,106,.14);color:#E0B36A;border-radius:8px;padding:7px 10px;font-size:12.5px;margin-bottom:10px}"
    +".waw-l{display:block;font-size:12px;color:#9DB0AC;margin:9px 0 3px}"
    +".waw-in,.waw-sel{width:100%;box-sizing:border-box;padding:9px 10px;border:1px solid #3D4F4D;"
    +"border-radius:9px;background:#26332F;color:#E7EEEC;font-size:14px}"
    +".waw-prev{background:#26332F;border:1px solid #3D4F4D;border-radius:10px;padding:10px;"
    +"font-size:13px;line-height:1.5;margin-top:8px;white-space:pre-wrap;color:#CDE0DA}"
    +".waw-row{display:flex;gap:8px;margin-top:14px}"
    +".waw-btn{flex:1;padding:11px;border-radius:10px;border:none;font-size:14px;font-weight:700;cursor:pointer}"
    +".waw-send{background:#25D366;color:#053}.waw-send:disabled{opacity:.5;cursor:default}"
    +".waw-cancel{background:transparent;color:#9DB0AC;border:1px solid #3D4F4D}"
    +".waw-toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#12201F;"
    +"color:#fff;padding:10px 16px;border-radius:20px;font-size:13px;z-index:10000;max-width:88%;text-align:center}";
    document.head.appendChild(s);
  }
  function toast(msg){var t=document.createElement('div');t.className='waw-toast';t.textContent=msg;
    document.body.appendChild(t);setTimeout(function(){t.remove();},4200);}
  function load(cb){
    if(loaded){cb();return;}
    fetch('/portal/wa/templates').then(function(r){return r.json();}).then(function(j){
      TPL=j.templates||[];DRY=!!j.dry;loaded=true;cb();
    }).catch(function(){alert('Could not load WhatsApp templates.');});
  }
  function renderPreview(t,vals){
    var p=t.preview||'';
    t.fields.forEach(function(f){
      var v=vals[f.key]; p=p.split('{'+f.key+'}').join(v?v:('['+f.label+']'));
    });
    return p;
  }
  function open(opts){
    opts=opts||{};styleOnce();
    load(function(){
      var ov=document.createElement('div');ov.className='waw-ov';
      var box=document.createElement('div');box.className='waw-box';ov.appendChild(box);
      var groups={};TPL.forEach(function(t){(groups[t.group]=groups[t.group]||[]).push(t);});
      var optHTML='';Object.keys(groups).forEach(function(g){
        optHTML+='<optgroup label="'+esc(g)+'">';
        groups[g].forEach(function(t){optHTML+='<option value="'+esc(t.name)+'">'+esc(t.title)+'</option>';});
        optHTML+='</optgroup>';});
      box.innerHTML=
        '<h3>Send WhatsApp</h3>'
        +'<div class="waw-sub">from the clinic business number \u00b7 9358008080</div>'
        +(DRY?'<div class="waw-dry">\u26a0 TEST MODE — nothing is actually sent. Sends are logged only.</div>':'')
        +'<label class="waw-l">Patient mobile</label>'
        +'<input class="waw-in" id="waw-phone" placeholder="10-digit mobile" value="'+esc(opts.phone||'')+'">'
        +'<label class="waw-l">Message template</label>'
        +'<select class="waw-sel" id="waw-tpl">'+optHTML+'</select>'
        +'<div id="waw-fields"></div>'
        +'<div class="waw-l">Preview</div><div class="waw-prev" id="waw-prev"></div>'
        +'<div class="waw-row"><button class="waw-btn waw-cancel" id="waw-cancel">Cancel</button>'
        +'<button class="waw-btn waw-send" id="waw-send">Send</button></div>';
      document.body.appendChild(ov);
      var sel=box.querySelector('#waw-tpl'), fld=box.querySelector('#waw-fields'),
          prev=box.querySelector('#waw-prev'), phone=box.querySelector('#waw-phone');
      function cur(){return TPL.filter(function(t){return t.name===sel.value;})[0];}
      function vals(){var t=cur(),o={};t.fields.forEach(function(f){
        var el=box.querySelector('#waw-f-'+f.key);o[f.key]=el?el.value.trim():'';});return o;}
      function drawFields(){
        var t=cur(),h='';t.fields.forEach(function(f){
          var pre=(f.prefill_name&&opts.name)?esc(opts.name):'';
          h+='<label class="waw-l">'+esc(f.label)+'</label>'
            +'<input class="waw-in" id="waw-f-'+f.key+'" value="'+pre+'">';});
        fld.innerHTML=h;
        t.fields.forEach(function(f){box.querySelector('#waw-f-'+f.key).addEventListener('input',upd);});
        upd();
      }
      function upd(){prev.textContent=renderPreview(cur(),vals());}
      sel.addEventListener('change',drawFields);
      box.querySelector('#waw-cancel').onclick=function(){ov.remove();};
      ov.addEventListener('click',function(e){if(e.target===ov)ov.remove();});
      box.querySelector('#waw-send').onclick=function(){
        var ph=phone.value.trim(),t=cur(),v=vals();
        for(var i=0;i<t.fields.length;i++){if(!v[t.fields[i].key]){toast('Fill in: '+t.fields[i].label);return;}}
        if(!/^[6-9]\d{9}$/.test(ph.replace(/\D/g,'').replace(/^0/,'').replace(/^91(?=\d{10}$)/,''))){}
        if(!confirm((DRY?'[TEST] ':'')+'Send "'+t.title+'" to '+mask(ph)+' from the clinic WhatsApp?'))return;
        var b=box.querySelector('#waw-send');b.disabled=true;b.textContent='Sending…';
        fetch('/portal/wa/send',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({phone:ph,template:t.name,values:v})})
          .then(function(r){return r.json();}).then(function(j){
            if(j.ok){toast((j.mode==='DRY'?'\u2705 TEST logged (not sent): ':'\u2705 Sent: ')+t.title);ov.remove();
              if(opts.onsent)opts.onsent(j);}
            else{toast('\u274c '+(j.error||'send failed'));b.disabled=false;b.textContent='Send';}
          }).catch(function(){toast('\u274c network error');b.disabled=false;b.textContent='Send';});
      };
      drawFields();
    });
  }
  window.WAWidget={open:open};
})();
"""

WA_PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Send WhatsApp — Dr. Manoj Agarwal Clinic</title>
<style>
:root{--bg:#263433;--card:#2F3E3D;--ink:#E7EEEC;--muted:#9DB0AC;--line:#3D4F4D;--wa:#25D366;--warn:#E0B36A}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;font-size:16px}
.wrap{max-width:640px;margin:0 auto;padding:16px 12px 60px}
h1{font-size:20px;margin:0 0 2px}.sub{color:var(--muted);font-size:13px;margin-bottom:12px}
.dry{background:rgba(224,179,106,.14);color:var(--warn);border-radius:10px;padding:9px 12px;font-size:13px;margin:8px 0}
.search{width:100%;padding:13px;border:1px solid var(--line);border-radius:12px;background:var(--card);color:var(--ink);font-size:16px}
.row{display:flex;justify-content:space-between;align-items:center;gap:10px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin:8px 0;cursor:pointer}
.row .nm{font-weight:700}.row .mu{color:var(--muted);font-size:12.5px;margin-top:2px}
.row .go{color:var(--wa);font-weight:700;font-size:13px;white-space:nowrap}
.blank{background:transparent;color:var(--wa);border:1px solid var(--wa);border-radius:10px;padding:10px 14px;font-size:14px;font-weight:600;cursor:pointer;margin:10px 0}
.empty{color:var(--muted);text-align:center;padding:24px 10px}
</style></head><body>
<div class="wrap">
  <h1>Send WhatsApp</h1>
  <div class="sub">Approved templates \u00b7 from clinic number 9358008080</div>
  <div id="dry"></div>
  <input class="search" id="q" placeholder="Search patient by name / mobile / clinic ID" autocomplete="off">
  <button class="blank" id="blank">Compose without a patient</button>
  <div id="res"><div class="empty">Type at least 2 letters to find a patient.</div></div>
</div>
<script src="/portal/wa/widget.js"></script>
<script>
fetch('/portal/wa/templates').then(function(r){return r.json();}).then(function(j){
  if(j.dry)document.getElementById('dry').innerHTML='<div class="dry">\u26a0 TEST MODE is ON — messages are logged but not actually sent.</div>';
});
var q=document.getElementById('q'),res=document.getElementById('res'),tmr=null;
function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function mask(p){var d=(''+p).replace(/\D/g,'');return d.length>=4?'\u2022\u2022\u2022\u2022'+d.slice(-4):'';}
q.addEventListener('input',function(){clearTimeout(tmr);tmr=setTimeout(run,220);});
function run(){
  var v=q.value.trim();if(v.length<2){res.innerHTML='<div class="empty">Type at least 2 letters.</div>';return;}
  fetch('/portal/wa/search?q='+encodeURIComponent(v)).then(function(r){return r.json();}).then(function(j){
    if(!j.ok){res.innerHTML='<div class="empty">'+esc(j.error||'search error')+'</div>';return;}
    if(!j.matches.length){res.innerHTML='<div class="empty">No match.</div>';return;}
    res.innerHTML=j.matches.map(function(m){
      return '<div class="row" data-p="'+esc(m.phone)+'" data-n="'+esc(m.name)+'">'
        +'<div><div class="nm">'+esc(m.name||'—')+'</div>'
        +'<div class="mu">'+esc([m.age,m.sex].filter(Boolean).join('/'))
        +(m.clinic_id?' \u00b7 ID '+esc(m.clinic_id):'')+' \u00b7 '+mask(m.phone)+'</div></div>'
        +'<div class="go">WhatsApp \u2192</div></div>';
    }).join('');
    Array.prototype.forEach.call(res.querySelectorAll('.row'),function(el){
      el.onclick=function(){WAWidget.open({phone:el.getAttribute('data-p'),name:el.getAttribute('data-n')});};
    });
  });
}
document.getElementById('blank').onclick=function(){WAWidget.open({});};
</script></body></html>"""


def register(app, guard, get_user, cfg_get):
    """Attach the shared WhatsApp routes. guard = the WA send-permission decorator
    (portal-owned). get_user = ()->username. cfg_get = portal's config reader."""
    from flask import request, jsonify, Response

    def _token():   return cfg_get("MYOP_AUTH_TOKEN", "") or os.environ.get("MYOP_AUTH_TOKEN", "")
    def _dry():     return (cfg_get("PORTAL_WA_DRYRUN", "1") or "1") != "0"

    @app.route("/portal/wa")
    @guard
    def wa_page():
        fp = os.path.join(WA_DIR, "wa_page.html")
        html = open(fp, encoding="utf-8").read() if os.path.exists(fp) else WA_PAGE
        return Response(html, mimetype="text/html; charset=utf-8")

    @app.route("/portal/wa/widget.js")
    @guard
    def wa_widget_js():
        fp = os.path.join(WA_DIR, "wa_widget.js")
        js = open(fp, encoding="utf-8").read() if os.path.exists(fp) else WIDGET_JS
        return Response(js, mimetype="application/javascript; charset=utf-8")

    @app.route("/portal/wa/templates")
    @guard
    def wa_templates():
        return jsonify({"ok": True, "dry": _dry(), "templates": registry_public()})

    @app.route("/portal/wa/search")
    @guard
    def wa_search():
        try:
            return jsonify({"ok": True, "matches": _wa_search(request.args.get("q", ""))})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/portal/wa/send", methods=["POST"])
    @guard
    def wa_send_route():
        b = request.get_json(force=True, silent=True) or {}
        r = send(b.get("phone", ""), b.get("template", ""), b.get("values") or {},
                 (get_user() or "portal"), _token(), dry_run=_dry())
        return jsonify(r), (200 if r.get("ok") else 400)

    return True
