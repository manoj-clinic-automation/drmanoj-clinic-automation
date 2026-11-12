#!/usr/bin/python3
# make_s805.py -- kit S805_WA_STOP_LIST_REMOVE (S439, 12-Nov-2026, the parent). Usage: make_s805.py <live wa_ladder.py> <out dir>
# D939, the WhatsApp items (c): on the owner's page /portal/messages a number on the stop list can be TAKEN OFF by the doctor, and
# a number he took off can be PUT BACK. A removal is recorded (table optout_removed in the kit's own store), never erased; the
# listener does not put the number back for a STOP it has already read (not on --rescan either); a NEW STOP reply puts it back.
# Still no send code. Every edit is an anchor that must occur exactly once in the live file (ca0334b4, S801).
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("ca0334b4"), "not the live wa_ladder.py (ca0334b4)"
t = b.decode("utf-8")
def rp(a, n):
    global t
    assert t.count(a) == 1, "anchor not once (%d): %s" % (t.count(a), a[:70])
    t = t.replace(a, n)

rp('VERSION = "S801 1.2"', 'VERSION = "S805 1.3"')
rp("  GET /portal/messages             the page (English; the doctor role only)\n",
   "  GET /portal/messages             the page (English; the doctor role only)\n"
   "  POST /portal/messages/api/unstop S805: the doctor takes ONE number off the stop list (recorded, never erased)\n"
   "  POST /portal/messages/api/restop S805: the doctor puts a number he took off back on the stop list\n")

# ---- the store: a record of every number taken off
rp('    con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")\n    return con\n',
   '    con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")\n'
   '    # S805: every number the doctor took off the stop list -- kept for ever; upto_rid = the last incoming message the\n'
   '    # listener had read at that moment (a STOP up to it is the old one and never puts the number back)\n'
   '    con.execute("CREATE TABLE IF NOT EXISTS optout_removed(id INTEGER PRIMARY KEY AUTOINCREMENT, mobile TEXT NOT NULL, "\n'
   '                "removed_at TEXT NOT NULL, removed_by TEXT NOT NULL DEFAULT \'\', was_at TEXT NOT NULL DEFAULT \'\', "\n'
   '                "was_source TEXT NOT NULL DEFAULT \'\', was_said TEXT NOT NULL DEFAULT \'\', upto_rid INTEGER NOT NULL DEFAULT 0)")\n'
   '    return con\n')

# ---- stops(): a number of the OLDER (hand-kept) file that the doctor took off is left out -- until that file is changed again
rp('    out, err = {}, ""\n    try:\n        con = store()\n        try:\n            for mob, at, src, said in con.execute("SELECT mobile, at, source, said FROM optout"):\n                out[mob] = {"at": at or "", "source": src or "", "said": said or ""}\n',
   '    out, err = {}, ""\n    taken = {}                                                         # S805: {mobile: when it was last taken off}\n    try:\n        con = store()\n        try:\n            for mob, at, src, said in con.execute("SELECT mobile, at, source, said FROM optout"):\n                out[mob] = {"at": at or "", "source": src or "", "said": said or ""}\n            taken = dict(con.execute("SELECT mobile, MAX(removed_at) FROM optout_removed GROUP BY mobile"))   # S805\n')
rp('    if os.path.exists(OLD_OPTOUT):\n        try:\n            with open(OLD_OPTOUT,',
   '    if os.path.exists(OLD_OPTOUT):\n        try:\n'
   '            # S805: a number of this hand-kept file that the doctor took off stays off -- until the file is changed again;\n'
   '            # then every number still in it is back on the list (the safe direction; he can take it off again)\n'
   '            fchg = dt.datetime.fromtimestamp(os.path.getmtime(OLD_OPTOUT), IST).strftime("%Y-%m-%d %H:%M:%S")\n'
   '            with open(OLD_OPTOUT,')
rp('                        if mob:\n                            out.setdefault(mob, {"at": "", "source": "older list", "said": ""})\n                            break\n',
   '                        if mob:\n                            if not (mob in taken and str(taken[mob] or "") >= fchg):   # S805\n                                out.setdefault(mob, {"at": "", "source": "older list", "said": ""})\n                            break\n')

# ---- the listener: a STOP it had already read when the number was taken off never puts it back
rp('        seen = new = 0\n        for rid, phone, ts, body in rows:\n',
   '        seen = new = 0\n        taken = dict(con.execute("SELECT mobile, MAX(upto_rid) FROM optout_removed GROUP BY mobile"))   # S805\n        for rid, phone, ts, body in rows:\n')
rp('            if mob and is_stop(body):\n',
   '            if mob and is_stop(body) and int(rid) > int(taken.get(mob, -1)):   # S805: only a STOP newer than the taking-off\n')

# ---- unstop(), restop() and taken_off()
rp('\n\ndef stop_status():\n', '''

def unstop(mobile, by):
    """S805 -- the doctor takes ONE number off the stop list. Returns (ok, text). The removal is RECORDED in optout_removed
    (the number, what it had said, when, who) and never erased; the listener does not put the number back for a STOP it had
    already read (not on --rescan either), but a NEW STOP reply -- also one that had arrived and was not read yet -- puts it back."""
    mob = m10(mobile)
    if not mob:
        return False, "that is not a mobile number"
    st, err = stops()
    if err:
        return False, err
    if mob not in st:
        return False, "that number is not on the stop list"
    was = st[mob]
    try:
        con = store()
        try:
            con.execute("BEGIN IMMEDIATE")        # the listener cannot write between the read of its place and this change
            row = con.execute("SELECT rid FROM optout WHERE mobile=?", (mob,)).fetchone()
            upto = max(int(_meta(con, "last_rid", "0") or 0), int((row[0] if row else 0) or 0))
            con.execute("INSERT INTO optout_removed(mobile, removed_at, removed_by, was_at, was_source, was_said, upto_rid) VALUES (?,?,?,?,?,?,?)",
                        (mob, now_ist().strftime("%Y-%m-%d %H:%M:%S"), str(by or "")[:40], was["at"], was["source"], was["said"], upto))
            con.execute("DELETE FROM optout WHERE mobile=?", (mob,))      # the row lives on, whole, in optout_removed
            con.commit()
        finally:
            con.close()
    except (sqlite3.Error, ValueError) as e:
        return False, "the stop list could not be changed (%s)" % type(e).__name__
    return True, "taken off the stop list"


def restop(mobile, by):
    """S805 -- the doctor puts a number he took off BACK on the stop list (a slip corrected). Only a number that was taken off
    here can be put back this way. Returns (ok, text)."""
    mob = m10(mobile)
    if not mob:
        return False, "that is not a mobile number"
    try:
        con = store()
        try:
            con.execute("BEGIN IMMEDIATE")
            r = con.execute("SELECT was_said FROM optout_removed WHERE mobile=? ORDER BY id DESC LIMIT 1", (mob,)).fetchone()
            if not r:
                con.rollback()
                return False, "that number was not taken off the stop list here"
            con.execute("INSERT OR IGNORE INTO optout(mobile, at, source, said, rid) VALUES (?,?,?,?,NULL)",
                        (mob, now_ist().strftime("%Y-%m-%d %H:%M:%S"), ("put back by " + str(by or "the doctor"))[:60], r[0] or ""))
            con.commit()
        finally:
            con.close()
    except sqlite3.Error as e:
        return False, "the stop list could not be changed (%s)" % type(e).__name__
    return True, "back on the stop list"


def taken_off(on_list=None, limit=50):
    """S805 -- the numbers the doctor took off the stop list and that are OFF it now, newest first, one line a number."""
    on = on_list if on_list is not None else stops()[0]
    rows, seen = [], set()
    try:
        con = store()
        try:
            for m, a, b_, s, sc in con.execute("SELECT mobile, removed_at, removed_by, was_said, was_source FROM optout_removed ORDER BY id DESC"):
                if m in seen:
                    continue
                seen.add(m)
                if m in on:                                              # it said STOP again, or was put back
                    continue
                rows.append({"mobile": m, "at": a, "by": b_, "said": s, "source": sc})
                if len(rows) >= int(limit):
                    break
        finally:
            con.close()
    except sqlite3.Error:
        return []
    return rows


def stop_status():
''')

# ---- the page's data and the two new doors
rp('"lists": lists, "stops": stop_rows, "fresh": fresh, "sends": False, "version": VERSION}',
   '"lists": lists, "stops": stop_rows, "taken_off": ([] if st_err else taken_off(st)), "fresh": fresh, "sends": False, "version": VERSION}')
rp('        resp = jsonify(p)\n        resp.headers["Cache-Control"] = "no-store"\n        return resp\n',
   '''        resp = jsonify(p)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    def _stop_door(change):                                            # S805
        if not _doctor():
            return jsonify({"ok": False, "msg": "Not for this login."}), 403
        if request.headers.get("X-Messages") != "1":                   # only this page's own script sends it
            return jsonify({"ok": False, "msg": "bad request"}), 400
        d = request.get_json(silent=True) or {}
        ok, text = change(d.get("mobile", "") if isinstance(d, dict) else "", (sso_user(request) or {}).get("user") or "doctor")
        resp = jsonify({"ok": ok, "msg": text})
        resp.headers["Cache-Control"] = "no-store"
        return resp, (200 if ok else 409)

    @app.route("/portal/messages/api/unstop", methods=["POST"])       # S805
    @login_required
    def wl_unstop():
        return _stop_door(unstop)

    @app.route("/portal/messages/api/restop", methods=["POST"])       # S805
    @login_required
    def wl_restop():
        return _stop_door(restop)
''')

# ---- the page
rp(".empty{padding:12px 14px;color:var(--t2);border-top:1px solid var(--ln)}\n",
   ".rw .off,.rw .on{font:inherit;font-size:13px;min-height:36px;padding:4px 10px;border:1px solid var(--ln);background:var(--cd);border-radius:10px;cursor:pointer;color:var(--ac);white-space:nowrap}\n"
   ".rw .off.sure{background:var(--warnbg);color:var(--warn);border-color:var(--warn);font-weight:700}\n"
   ".empty{padding:12px 14px;color:var(--t2);border-top:1px solid var(--ln)}\n")
rp("var DAY='';\n", "var DAY='',OPENSTOP=false;\n")
rp(''' var h='<details><summary><span class="tt"><b>Numbers that said STOP</b><span>never messaged again</span></span><span class="n"><b>'+s.length+'</b></span></summary>';''',
   ''' var h='<details'+(OPENSTOP?' open':'')+'><summary><span class="tt"><b>Numbers that said STOP</b><span>never messaged again, unless you take one off</span></span><span class="n"><b>'+s.length+'</b></span></summary>';''')
rp('''h+='<div class="rw"><span class="nm">'+esc(r.mobile)+'</span><span class="meta">'+esc(r.source)''',
   '''h+='<div class="rw"><span class="nm">'+esc(r.mobile)+'</span><button class="off" data-m="'+esc(r.mobile)+'">Take off the stop list</button><span class="meta">'+esc(r.source)''')
rp("function load(){\n",
   '''function taken(t){
 if(!t||!t.length)return '';
 var h='<details'+(OPENSTOP?' open':'')+'><summary><span class="tt"><b>Taken off the stop list by you</b><span>can be messaged again; a new STOP reply puts the number back</span></span><span class="n"><b>'+t.length+'</b></span></summary>';
 t.forEach(function(r){h+='<div class="rw"><span class="nm">'+esc(r.mobile)+'</span><button class="on" data-m="'+esc(r.mobile)+'">Put back on the stop list</button><span class="meta">taken off '+esc((r.at||'').slice(0,16))+(r.by?' by '+esc(r.by):'')+(r.said?' &middot; had said: '+esc(r.said):(r.source?' &middot; '+esc(r.source):''))+'</span></div>';});
 return h+'</details>';}
function load(){
''')
rp("document.getElementById('m').innerHTML=d.lists.map(sec).join('')+stops(d.stops);",
   "document.getElementById('m').innerHTML=d.lists.map(sec).join('')+stops(d.stops)+taken(d.taken_off);")
rp("document.getElementById('td').onclick=function(){DAY='';load();};\n",
   '''document.getElementById('td').onclick=function(){DAY='';load();};
document.getElementById('m').addEventListener('click',function(e){
 var b=e.target;if(!b||!b.classList)return;var off=b.classList.contains('off'),on=b.classList.contains('on');if(!off&&!on)return;
 var label=off?'Take off the stop list':'Put back on the stop list';
 function calm(){b.disabled=false;b.removeAttribute('data-sure');b.classList.remove('sure');}
 if(off){var now=Date.now();
  if(b.getAttribute('data-sure')!=='1'){b.setAttribute('data-sure','1');b.setAttribute('data-t',String(now));b.textContent='Tap again to take it off';b.classList.add('sure');
   setTimeout(function(){if(b.isConnected&&!b.disabled&&b.getAttribute('data-sure')==='1'){calm();b.textContent=label;}},6000);return;}
  if(now-(+b.getAttribute('data-t')||0)<700)return;}
 b.disabled=true;b.textContent=off?'Taking off...':'Putting back...';
 fetch('/portal/messages/api/'+(off?'unstop':'restop'),{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Messages':'1'},body:JSON.stringify({mobile:b.getAttribute('data-m')})})
  .then(function(x){return x.json();}).then(function(d){if(d&&d.ok){OPENSTOP=true;load();}else{calm();b.textContent='Could not: '+((d&&d.msg)||'try again');}})
  .catch(function(){calm();b.textContent='Could not - open the page again and retry';});
});
''')
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
with open(os.path.join(out, "portal", "wa_ladder.py"), "wb") as fh:
    fh.write(t.encode("utf-8"))
print("wa_ladder.py", hashlib.md5(t.encode("utf-8")).hexdigest())
