#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""online_booking_portal.py -- kit S786_ONLINE_BOOKING (session S428, 11-Nov-2026, the parent). NEW.

The page staff open for the online bookings paid through Docterz (online_booking.py reads them from the clinic Gmail every 3
minutes into finance.db table online_booking). The owner, 11-Nov-2026 07:59 IST: patient name, clinic ID (existing patients),
FULL mobile, "paid 600/- online", the booked time; when the time is outside Mon-Sat 11:00-13:30 / 19:00-20:30 staff call the
patient and tell them to come in those timings.

  GET  /portal/booking             the page (Hindi for staff, English for the doctors)
  GET  /portal/booking/api/list    the bookings: arrived in the last 3 days, or booked for today or later
  POST /portal/booking/api/called  {id} -- 'Phone kar diya': who and when, once (the first tap stands)

WHO: a doctor-role login, and the logins the 'Online booking' tile is granted to by name in tile_grants.json (the same rule as
'Call ke baad': who is shown the tile may open the page). Anyone else: 403. portal.py calls install(app, login_required, sso_user)
once. Reads finance.db read-only; its one write is the tap (called_by / called_at on a row still without one).
"""
import datetime as dt
import json
import os
import sqlite3

from flask import jsonify, make_response, request

VERSION = "S786 1.0"
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
STATE = os.environ.get("OB_STATE", "/root/finance/online_booking_state.json")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", os.path.dirname(os.path.abspath(__file__)))
GRANTS = os.environ.get("TILE_GRANTS_FILE", os.path.join(PORTAL_DIR, "tile_grants.json"))
TILE = "Online booking"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
STALE_MIN = 30


def now_ist():
    return dt.datetime.now(IST)


def access(who):
    """'doctor' | 'staff' | '' -- from the login's role and the tile's grants."""
    who = who or {}
    if who.get("role") == "doctor":
        return "doctor"
    user = who.get("user") or ""
    if not user:
        return ""
    try:
        with open(GRANTS, encoding="utf-8") as fh:
            g = json.load(fh)
        u = (g.get("users") or {}).get(user) or {}
        if TILE in (u.get("extra") or []) and TILE not in (u.get("mask") or []):
            return "staff"
    except Exception:                                                  # noqa: BLE001 -- no grants file: staff see nothing
        pass
    return ""


def _ro():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _state():
    try:
        with open(STATE, encoding="utf-8") as fh:
            st = json.load(fh)
    except Exception:                                                  # noqa: BLE001
        st = {}
    last = st.get("last_ok") or ""
    try:
        age = (now_ist().replace(tzinfo=None) - dt.datetime.strptime(last, "%Y-%m-%d %H:%M:%S")).total_seconds() / 60.0
    except Exception:                                                  # noqa: BLE001
        age = None
    return {"last_ok": last[11:16] if last else "", "last_ok_day": last[:10], "stale": age is None or age > STALE_MIN,
            "error": bool(st.get("error"))}


def rows(today=None):
    today = today or now_ist().strftime("%Y-%m-%d")
    since = (dt.datetime.strptime(today, "%Y-%m-%d") - dt.timedelta(days=3)).strftime("%Y-%m-%d")
    try:
        con = _ro()
    except Exception:                                                  # noqa: BLE001
        return None
    try:
        rs = con.execute("SELECT id, name, mobile, amount_p, appt_at, appt_raw, out_of_hours, clinic_ids, mail_at, called_by, called_at "
                         "FROM online_booking WHERE substr(COALESCE(appt_at,''),1,10) >= ? OR COALESCE(mail_at,'') >= ? "
                         "ORDER BY CASE WHEN substr(COALESCE(appt_at,''),1,10) >= ? THEN 0 ELSE 1 END, "
                         "COALESCE(appt_at,'') ASC, id DESC LIMIT 60", (today, since, today)).fetchall()
    except sqlite3.OperationalError:                                   # no table yet: nothing has come
        return []
    finally:
        con.close()
    out = []
    for r in rs:
        try:
            ids = json.loads(r["clinic_ids"] or "[]")
        except ValueError:
            ids = []
        a = r["appt_at"] or ""
        out.append({"id": r["id"], "name": r["name"] or "", "mobile": r["mobile"] or "", "rupees": (r["amount_p"] or 0) // 100,
                    "appt_at": a, "appt_raw": r["appt_raw"] or "", "out": bool(r["out_of_hours"]), "ids": ids,
                    "mail_at": r["mail_at"] or "", "called_by": r["called_by"] or "", "called_at": (r["called_at"] or "")[11:16],
                    "past": bool(a) and a[:10] < today, "today": a[:10] == today})
    return out


def mark_called(rid, login):
    con = sqlite3.connect(DB, timeout=10)
    try:
        cur = con.execute("UPDATE online_booking SET called_by=?, called_at=? WHERE id=? AND COALESCE(called_at,'')=''",
                          (login, now_ist().strftime("%Y-%m-%d %H:%M"), rid))
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def install(app, login_required, sso_user):
    @app.route("/portal/booking")
    @login_required
    def ob_page():
        kind = access(sso_user(request))
        if not kind:
            return make_response("Not for this login.", 403)
        resp = make_response(PAGE.replace("__LANG__", "en" if kind == "doctor" else "hi"))
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/booking/api/list")
    @login_required
    def ob_list():
        if not access(sso_user(request)):
            return jsonify({"ok": False}), 403
        rs = rows()
        if rs is None:
            return jsonify({"ok": False, "msg": "database not readable"}), 503
        resp = jsonify({"ok": True, "rows": rs, "state": _state(), "now": now_ist().strftime("%H:%M")})
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/booking/api/called", methods=["POST"])
    @login_required
    def ob_called():
        who = sso_user(request) or {}
        if not access(who):
            return jsonify({"ok": False}), 403
        body = request.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        try:
            rid = int(body.get("id"))
            assert 0 < rid < 2 ** 62
        except Exception:                                              # noqa: BLE001
            return jsonify({"ok": False, "msg": "bad id"}), 400
        try:
            ok = mark_called(rid, who.get("user") or "?")
        except Exception:                                              # noqa: BLE001
            return jsonify({"ok": False, "msg": "not saved"}), 503
        return jsonify({"ok": True, "saved": ok})


PAGE = r"""<!doctype html><html lang="__LANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Online booking</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--tx:#e2e8f0;--mu:#94a3b8;--ok:#22c55e;--warn:#f59e0b;--bad:#ef4444;--ln:#334155}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:16px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--ln)}
header a{color:var(--mu);text-decoration:none;font-size:22px}h1{font-size:19px;margin:0;flex:1}
#st{font-size:12px;color:var(--mu)}#st.bad{color:var(--bad);font-weight:700}
main{padding:12px 16px 40px;max-width:760px;margin:0 auto}
.card{background:var(--card);border:1px solid var(--ln);border-radius:14px;padding:14px;margin:0 0 12px}
.card.today{border-color:#3b82f6}.card.past{opacity:.55}
.nm{font-size:19px;font-weight:700}.id{font-size:14px;color:var(--mu);margin-top:2px}
.row{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:10px;align-items:center}
.mob{font-size:20px;font-weight:700;color:#93c5fd;text-decoration:none;letter-spacing:.5px}
.paid{background:rgba(34,197,94,.15);color:#86efac;font-weight:700;border-radius:999px;padding:3px 12px}
.tm{font-weight:700}
.warn{margin-top:12px;background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.5);border-radius:10px;padding:10px 12px}
.warn b{color:#fca5a5}.done{margin-top:12px;color:#86efac;font-weight:600}
.note{margin-top:10px;font-size:14px;color:var(--mu)}
button{font:inherit;font-weight:700;border:0;border-radius:10px;padding:10px 16px;background:var(--bad);color:#fff;margin-top:10px;cursor:pointer}
.empty{color:var(--mu);text-align:center;padding:40px 10px}
</style></head><body>
<header><a href="/portal" aria-label="back">&#8592;</a><h1 id="h"></h1><span id="st"></span></header>
<main id="m"></main>
<script>
var EN=document.documentElement.lang==='en';
var T=EN?{h:'Online bookings (paid on Docterz)',paid:'paid online',newp:'New patient (no clinic ID on this number)',
 out:'<b>Outside clinic timings.</b> Call the patient: come Mon–Sat 11:00–1:30 or 7:00–8:30 pm.',
 btn:'Called the patient',called:'Called by ',at:' at ',noamt:'Do not collect the fee again — in Docterz enter it as Wallet.',
 none:'No online booking in the last 3 days.',chk:'Last checked ',stale:'NOT CHECKED SINCE ',never:'Not checked yet',
 timeq:'time not read',same:'also on this number: ',err:'Could not load — pull down to retry.'}
:{h:'Online booking (Docterz par paid)',paid:'online paid',newp:'नया मरीज़ (इस नंबर पर कोई ID नहीं)',
 out:'<b>यह समय clinic का नहीं है।</b> Patient को phone करके बताएं: सोम–शनि 11:00–1:30 या शाम 7:00–8:30 के बीच आएं।',
 btn:'Phone kar diya',called:'Phone kiya: ',at:' · ',noamt:'फीस दोबारा न लें — Docterz में Wallet चुनें।',
 none:'पिछले 3 दिन में कोई online booking नहीं।',chk:'Check: ',stale:'CHECK नहीं हुआ — ',never:'अभी check नहीं हुआ',
 timeq:'समय नहीं पढ़ा',same:'इस नंबर पर और: ',err:'Load नहीं हुआ — दोबारा खोलें।'};
document.getElementById('h').textContent=T.h;
var MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
var DAY=EN?['Sun','Mon','Tue','Wed','Thu','Fri','Sat']:['रवि','सोम','मंगल','बुध','गुरु','शुक्र','शनि'];
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function when(a,raw){if(!a)return raw||T.timeq;var p=a.split(/[- :]/),d=new Date(+p[0],+p[1]-1,+p[2]),h=+p[3],m=p[4],ap=h>=12?'PM':'AM',h12=h%12||12;
 return DAY[d.getDay()]+', '+(+p[2])+' '+MON[+p[1]-1]+' · '+h12+':'+m+' '+ap;}
function card(r){var c='card'+(r.today?' today':'')+(r.past?' past':'');
 var id=r.ids&&r.ids.length?('Clinic ID '+esc(r.ids[0].id)+(r.ids.length>1?' · '+T.same+r.ids.slice(1).map(function(x){return esc(x.id)+(x.name?' ('+esc(x.name)+')':'');}).join(', '):'')):T.newp;
 var h='<div class="'+c+'"><div class="nm">'+esc(r.name||'?')+'</div><div class="id">'+id+'</div>'+
 '<div class="row"><a class="mob" href="tel:'+esc(r.mobile)+'">'+esc(r.mobile||'?')+'</a><span class="paid">₹'+esc(r.rupees)+' '+T.paid+'</span></div>'+
 '<div class="row"><span class="tm">'+esc(when(r.appt_at,r.appt_raw))+'</span></div>'+
 '<div class="note">'+T.noamt+'</div>';
 if(r.out){ if(r.called_by){h+='<div class="done">✔ '+T.called+esc(r.called_by)+T.at+esc(r.called_at)+'</div>';}
  else{h+='<div class="warn">'+T.out+'</div>'+(r.past?'':'<button data-id="'+r.id+'">'+T.btn+'</button>');} }
 return h+'</div>';}
function load(){fetch('/portal/booking/api/list',{credentials:'same-origin',cache:'no-store'}).then(function(x){return x.json();}).then(function(d){
 var s=document.getElementById('st'),st=d.state||{};
 if(!st.last_ok){s.textContent=T.never;s.className='bad';}else if(st.stale||st.error){s.textContent=T.stale+st.last_ok;s.className='bad';}else{s.textContent=T.chk+st.last_ok;s.className='';}
 var m=document.getElementById('m');m.innerHTML=(d.rows&&d.rows.length)?d.rows.map(card).join(''):'<div class="empty">'+T.none+'</div>';
 }).catch(function(){document.getElementById('m').innerHTML='<div class="empty">'+T.err+'</div>';});}
document.addEventListener('click',function(e){var b=e.target.closest('button[data-id]');if(!b)return;b.disabled=true;
 fetch('/portal/booking/api/called',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:+b.dataset.id})})
 .then(function(){load();}).catch(function(){b.disabled=false;});});
load();setInterval(load,60000);
</script></body></html>"""
