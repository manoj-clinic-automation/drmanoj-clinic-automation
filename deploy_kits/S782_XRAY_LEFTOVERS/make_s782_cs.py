#!/usr/bin/python3
# make_s782_cs.py -- kit S782_XRAY_LEFTOVERS (S427, 11-Nov-2026, the parent). Usage: make_s782_cs.py <live check_screens.py> <output>
# Builds the new check_screens.py from the live ce7d248d bytes by exact replacement (every anchor must occur once).
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("ce7d248d"), "not the live check_screens.py (ce7d248d)"
t = b.decode("utf-8")
R = [
('''VERSION = "S757 1"
''', '''VERSION = "S782 1"
STAFF_DAYS = 7                              # S782 (the owner 05:15 IST 11-Nov): a parked picture older than this leaves the other
                                            # staff's Check karein; the owner and the lab logins (Shavez) keep every one
'''),
('''def _parked(con):
    """The open parked pictures (xray_filing state 'check', nobody's answer yet), newest first."""''',
'''def _parked(con, recent=False):
    """The open parked pictures (xray_filing state 'check', nobody's answer yet), newest first. recent=True: only those first seen
    in the last STAFF_DAYS days (the reception's list -- S782)."""'''),
('''        r["day"] = r["day"] if _ok_day(r["day"]) else str(r["planned_at"] or "")[:10]
        out.append(r)''',
'''        r["day"] = r["day"] if _ok_day(r["day"]) else str(r["planned_at"] or "")[:10]
        if recent and r["day"] < _d(R._today(), -STAFF_DAYS):
            continue                                     # S782: older -- the owner's and Shavez's only
        out.append(r)'''),
('''    out.sort(key=lambda x: (x["rank"], x["name"].lower(), x["id"]))
    return out
''', '''    # S782 (the owner 05:18 IST 11-Nov): the closest names first -- X-rayed and only seen together: a name that is the picture's
    # but for the spelling (records._s782_alike) is tagged and listed with the matches; the rest by letter likeness
    # (records._s782_sp); the three best on top, everyone else folded under one button when the day is long.
    for x in out:
        x["sp"] = R._s782_sp(ft, people[x["id"]]["names"]) if ft and not child else 0.0
        if x["rank"] > 2 and ft and not child and any(R._s782_alike(ft, R._s752_tokens(n)) for n in people[x["id"]]["names"]):
            x["tag"], x["tag_en"], x["rank"] = "Naam milta-julta", "Similar name", 2
    out.sort(key=lambda x: (min(x["rank"], 3), -round(x["sp"], 2), x["rank"], x["name"].lower(), x["id"]))
    for i, x in enumerate(out):
        x["top"] = x["rank"] <= 2
        x["near"] = len(out) > 5 and i >= 3
    return out
'''),
('''def xray_queue(con, with_people=False):
    cache = {}
    out = []
    for r in _parked(con):''', '''def xray_queue(con, with_people=False, recent=False):
    cache = {}
    out = []
    for r in _parked(con, recent):'''),
('''    x = len(_parked(con))
    lab = _lab_ok(con, u)''', '''    lab = _lab_ok(con, u)
    x = len(_parked(con, recent=not lab))               # S782: reception -- the last STAFF_DAYS days; Shavez and doctors -- all'''),
('''    lab = _lab_ok(con, u)
    items = xray_queue(con)''', '''    lab = _lab_ok(con, u)
    items = xray_queue(con, recent=not lab)             # S782: older pictures -- the owner's and Shavez's only'''),
("""'<button class="more" data-more="1">Ek din pehle / baad ke marij ('+near.length+')</button>'""",
 """'<button class="more" data-more="1">Baaki marij ('+near.length+')</button>'"""),
("""wait:['Waiting for staff','tap a photo to see it and pick the patient']""",
 """wait:['Waiting to be filed','tap a photo to see it and pick the patient \u00b7 older than 7 days: only you and Shavez see it']"""),
("""['wait','Waiting for staff (Check karein)','you can file them too','#17202A']""",
 """['wait','Waiting to be filed','staff see the last 7 days · older ones: you and Shavez','#17202A']"""),
("""'<button class="more" data-more="1">Patients of the day before / after ('+near.length+')</button>'""",
 """'<button class="more" data-more="1">All other patients ('+near.length+')</button>'"""),
]
# ---- S782 (the owner 05:42 / 05:43 IST 11-Nov): the box under the list finds a patient by clinic ID, NAME or MOBILE, and shows the
# ---- full mobile number on each match
R.append(("""def api_pats_staff():""", """def _mobile(con, cid):
    \"\"\"The patient's mobile number as the clinic holds it (the owner: full numbers); the last four when only those are kept.\"\"\"
    r = R._rows(con, "SELECT mobile, phone_last4 FROM patient_ref WHERE clinic_id=? ORDER BY (merged_into IS NULL OR merged_into='') DESC, "
                     "id LIMIT 1", (cid,))
    if not r:
        return ""
    m = re.sub(r"\\D", "", str(r[0].get("mobile") or ""))
    return m[-10:] if len(m) >= 10 else ("\\u2026" + r[0]["phone_last4"] if r[0].get("phone_last4") else "")


def find_people(con, q, day=""):
    \"\"\"Up to 8 patients for what was typed: a clinic ID; a mobile number (10 digits); or a name -- the name's spelling variants first
    (records._s782_alike), then by likeness; those who came that day (or a day either side) ahead. Each: id, name, mobile, came.\"\"\"
    q = str(q or "").strip()[:60]
    digits = re.sub(r"\\D", "", q)
    found = []
    if re.fullmatch(r"\\d{1,8}", q):
        found = [q] if R._known_id(con, q) else []
    elif len(digits) >= 10 and not re.search(r"[A-Za-z]", q):
        m10 = digits[-10:]
        found = [r["clinic_id"] for r in R._rows(con, "SELECT DISTINCT clinic_id, mobile FROM patient_ref WHERE phone_last4=? AND clinic_id<>''",
                                                  (m10[-4:],)) if re.sub(r"\\D", "", str(r["mobile"] or ""))[-10:] == m10]
        if not found:                                    # a number the clinic keeps only as its fingerprint
            fp = R._fp_of(m10)[0]
            if fp:
                found = [r["clinic_id"] for r in R._rows(con, "SELECT DISTINCT clinic_id FROM patient_ref WHERE mobile_fp=? AND clinic_id<>''", (fp,))]
    else:
        toks = R._s752_tokens(q)
        if toks:
            near = set(_people(con, _d(day, -1), _d(day, 1), {}).keys()) if _ok_day(day) else set()
            cands = set(near)                            # everyone who came that day, whatever the spelling
            for w in toks[:3]:                           # and anyone whose name shares a word's first four letters
                like = "%" + w[:4] + "%"
                cands |= {r["c"] for r in R._rows(con, "SELECT DISTINCT clinic_id c FROM patient_ref WHERE name LIKE ? AND clinic_id<>'' LIMIT 600", (like,))}
                cands |= {r["c"] for r in R._rows(con, "SELECT DISTINCT clinic_id c FROM slip WHERE name_seen LIKE ? AND clinic_id<>'' LIMIT 300", (like,))}
                cands |= {r["c"] for r in R._rows(con, "SELECT DISTINCT clinic_id c FROM clinic_day_line WHERE patient LIKE ? AND clinic_id<>'' LIMIT 300", (like,))}
            sc = []
            for c in cands:
                names = R._s772_names(con, c)
                s = 1.0 if any(R._s782_alike(toks, R._s752_tokens(n)) for n in names) else R._s782_sp(toks, names)
                if s >= 0.5:
                    sc.append((-(s + (0.2 if c in near else 0)), c))
            found = [c for _, c in sorted(sc)]
    near = set(_people(con, _d(day, -1), _d(day, 1), {}).keys()) if _ok_day(day) else set()
    out, seen = [], set()
    for c in found:
        p = R.person(con, c) or {}
        if c in seen or p.get("merged"):
            continue
        seen.add(c)
        out.append({"id": c, "name": p.get("name") or "\\u2014", "mobile": _mobile(con, c), "came": c in near})
        if len(out) >= 8:
            break
    return out


def _find_for(sid, q):
    con = R._db()
    row = next((r for r in _parked(con) if r["src_id"] == sid), None)
    if not row:                                          # only for a picture that is waiting -- never a patient directory
        return jsonify(ok=False, err="gone"), 404
    return jsonify(ok=True, pats=find_people(con, q, row.get("day") or ""))


def api_find_staff():
    u, err = _json_gate()
    if err:
        return err
    return _find_for(str(request.args.get("sid") or "")[:200], request.args.get("q") or "")


def api_find_owner():
    u, err = _doc_gate()
    if err:
        return err
    return _find_for(str(request.args.get("sid") or "")[:200], request.args.get("q") or "")


def api_pats_staff():"""))
R.append(("""    bp.add_url_rule(CP + "/api/pats", "s757_pats", api_pats_staff)
""", """    bp.add_url_rule(CP + "/api/pats", "s757_pats", api_pats_staff)
    bp.add_url_rule(CP + "/api/find", "s782_find", api_find_staff)              # S782: ID / name / mobile
    bp.add_url_rule(P + "/xray-check/api/find", "s782_owner_find", api_find_owner)
"""))
# staff page: the box, its results, its wiring
R.append(("""var B=__BOOT__, IT=B.items, F='all', CUR=null, PICK=-1, BIG=false, MSG=B.ok||'', ERR='', PATS={}, LATER=[], CF=null, OPEN={};""",
          """var B=__BOOT__, IT=B.items, F='all', CUR=null, PICK=-1, BIG=false, MSG=B.ok||'', ERR='', PATS={}, LATER=[], CF=null, OPEN={}, FOUND={}, FQ={};"""))
R.append(("""function footHtml(it){return '<div class="ft"><label for="cid">Inmein nahi hai? Clinic ID likhiye</label><div class="row2" style="gap:8px"><input id="cid" inputmode="numeric" placeholder="Clinic ID" autocomplete="off"><button class="go" id="cidgo">Daalein</button></div>'+""",
          """function foundHtml(it){var fs=FOUND[it.key];if(!fs)return '';if(!fs.length)return '<span class="sm">Is naam / number ka koi marij nahi mila.</span>';
 return fs.map(function(p,k){return '<button class="pr" data-f="'+k+'"><span><span class="nm">'+esc(p.name)+'</span><span class="sr">ID '+esc(p.id)+(p.mobile?' · '+esc(p.mobile):'')+'</span></span>'+(p.came?'<span class="tag">Us din aaye the</span>':'')+'</button>';}).join('');}
function footHtml(it){return '<div class="ft"><label for="cid">Inmein nahi hai? Clinic ID, naam ya mobile likhiye</label><div class="row2" style="gap:8px"><input id="cid" placeholder="Clinic ID / naam / mobile" autocomplete="off" value="'+esc(FQ[it.key]||'')+'"><button class="go" id="cidgo">Dhoondhein</button></div>'+foundHtml(it)+"""))
R.append(("""  post({key:it.key,a:'id_fixed',new_id:v,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};MSG='';ERR='';draw();}else{ERR=r.err;msgs();}});};""",
          """  FQ[it.key]=v;if(!/^\\d{1,8}$/.test(v)){fetch('/finance/checks/api/find?sid='+encodeURIComponent(it.sid)+'&q='+encodeURIComponent(v),{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.ok?r.json():{ok:false};}).then(function(d){if(d.ok){FOUND[it.key]=d.pats;ERR='';draw();}else{ERR='Dhoondh nahi paaye — page dobara kholiye';msgs();}}).catch(function(){ERR='Internet / server nahi mila — dobara dabaiye';msgs();});return;}
  post({key:it.key,a:'id_fixed',new_id:v,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};MSG='';ERR='';draw();}else{ERR=r.err;msgs();}});};
 [].forEach.call(root.querySelectorAll('[data-f]'),function(b){b.onclick=function(){var p=FOUND[it.key][+b.getAttribute('data-f')];post({key:it.key,a:'id_fixed',new_id:p.id,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};MSG='';ERR='';draw();var y=$('yes');if(y)y.scrollIntoView({block:'nearest'});}else{ERR=r.err;msgs();}});};});"""))
# owner page: the box, its results, its wiring
R.append(("""var B=__BOOT__, TAB=B.tab, OPEN=null, PICK=-1, CF=null, MSG='', ERR='', PATS={}, MORE={};""",
          """var B=__BOOT__, TAB=B.tab, OPEN=null, PICK=-1, CF=null, MSG='', ERR='', PATS={}, MORE={}, FOUND={}, FQ={};"""))
R.append(("""<input id="nid" inputmode="numeric" placeholder="Not here? Type the clinic ID"><button class="b2" id="nidgo">Use this ID</button></div>""",
          """<input id="nid" placeholder="Not here? Clinic ID, name or mobile" value="'+esc(FQ[i.key]||'')+'"><button class="b2" id="nidgo">Find</button></div>'+(FOUND[i.key]?(FOUND[i.key].length?FOUND[i.key].map(function(p,k){return '<button class="pr" data-f="'+k+'"><span><b>'+esc(p.name)+'</b><span class="s">ID '+esc(p.id)+(p.mobile?' · '+esc(p.mobile):'')+'</span></span>'+(p.came?'<span class="tag">came that day</span>':'')+'</button>';}).join(''):'<span class="f">No patient found for that name or number.</span>'):'')+'"""))
R.append(("""  var ng=el.querySelector('#nidgo');if(ng)ng.onclick=function(){var v=(el.querySelector('#nid').value||'').trim();if(!v)return;post({key:key,a:'id_fixed',new_id:v,check:1})""",
          """  [].forEach.call(el.querySelectorAll('[data-f]'),function(b){b.onclick=function(){var p=FOUND[key][+b.getAttribute('data-f')];post({key:key,a:'id_fixed',new_id:p.id,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};ERR='';}else ERR=r.err;draw();});};});
  var ni=el.querySelector('#nid');if(ni)ni.onkeydown=function(e){if(e.key==='Enter'){e.preventDefault();el.querySelector('#nidgo').click();}};
  var ng=el.querySelector('#nidgo');if(ng)ng.onclick=function(){var v=(el.querySelector('#nid').value||'').trim();if(!v)return;FQ[key]=v;if(!/^\\d{1,8}$/.test(v)){fetch('/finance/records/xray-check/api/find?sid='+encodeURIComponent(i.sid)+'&q='+encodeURIComponent(v),{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.ok?r.json():{ok:false};}).then(function(d){if(d.ok){FOUND[key]=d.pats;ERR='';}else ERR='The search did not answer — reload the page and try again.';draw();}).catch(function(){ERR='The server did not answer — try again.';draw();});return;}post({key:key,a:'id_fixed',new_id:v,check:1})"""))

assert t.count("footHtml()") == 3, "footHtml() not three times"
t = t.replace("footHtml()", "footHtml(it)")
for old, new in R:
    assert t.count(old) == 1, "anchor not once: " + old[:70]
    t = t.replace(old, new)
open(dst, "wb").write(t.encode("utf-8"))
print("written", dst, hashlib.md5(t.encode("utf-8")).hexdigest()[:8])
