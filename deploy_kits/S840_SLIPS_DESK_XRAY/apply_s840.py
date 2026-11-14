#!/usr/bin/python3
"""apply_s840.py -- kit S840_SLIPS_DESK_XRAY (the parent, built S465, rebuilt S467, 14-Nov-2026). Usage: apply_s840.py <in> <out>
Patches /root/finance/parchi_desk.py 5ec8aebc (read whole from the 14-Nov bundle) on exact anchors; every anchor must occur once."""
import hashlib, sys
FROM = "5ec8aebce77f6b631884956b51e36066"
src = open(sys.argv[1], "rb").read()
assert hashlib.md5(src).hexdigest() == FROM, "not the 5ec8aebc parchi_desk.py"
s = src.decode("utf-8")
def r(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)

r('No patient name, no number, no secret in this file (F-185).\n"""',
  'S840 (S465/S467, 14-Nov-2026, D979 item 4, A-D55): the green strip also says "X-ray upload baaki N" (Check karein\'s own 7-day\n'
  'strip, check_screens.day_strip); a box "X-ray, pichhle 7 din" under the day\'s skipped numbers; the three clinic-ID boxes take a\n'
  'NAME too -- a list under the box (GET /finance/slips/desk/api/find, check_screens.find_people: id, name, the mobile\'s last four,\n'
  'came that day) -- and a name is never saved as a clinic ID (the page refuses it; the save and blood doors refuse a clinic ID with a\n'
  'letter that the master does not know).\n'
  'No patient name, no number, no secret in this file (F-185).\n"""')
r("import datetime as dt\nimport json\n", "import datetime as dt\nimport json\nimport re\n")
r('''    try:                                                 # S757 (D875): the Check karein strip; a lab report's blood slip
        html = html.replace("</body>", _s757_extra(con, eng, u) + "</body>", 1)
    except Exception:                                    # noqa: BLE001 -- the desk as it was
        pass
    return html
''', '''    strip = _s840_strip(con)                             # S840 (D979 item 4): Check karein's 7-day X-ray strip; None if unread
    up = sum(int(s_["x"]["pending"]) for s_ in strip) if strip else 0
    try:
        html = html.replace('<div id="missing"></div>', '<div id="missing"></div>' + _s840_box(strip, eng, up), 1)
    except Exception:                                    # noqa: BLE001 -- the desk as it was
        pass
    try:                                                 # S757 (D875): the Check karein strip; a lab report's blood slip
        html = html.replace("</body>", _s757_extra(con, eng, u, up) + "</body>", 1)
    except Exception:                                    # noqa: BLE001 -- the desk as it was
        pass
    return html


def _s840_strip(con):
    """S840: check_screens.day_strip (S836) -- the last 7 days' X-rays and their states, the same lists Check karein shows."""
    try:
        import check_screens                             # noqa: PLC0415
        check_screens._rec()
        return check_screens.day_strip(con)
    except Exception:                                    # noqa: BLE001 -- the desk without the box
        return None


_S840_ST = {"pending": ("photo baaki", "photo pending"), "notdue": ("abhi samay hai", "not due yet"),
            "issue": ("photo atki — Check karein", "picture stuck — Check karein"), "filing": ("file ho rahi", "being filed"),
            "notdone": ("X-ray nahi hua", "X-ray not done"), "answered": ("jawab diya", "answered")}


def _s840_box(strip, eng, up):
    """S840: "X-ray, pichhle 7 din" -- per day with an X-ray: how many, how many filed, and every one not yet filed by name."""
    import html as _h                                    # noqa: PLC0415
    if not strip:
        return ""
    k = 1 if eng else 0
    days = []
    for d in strip:
        x = d["x"]
        if not x["n"] and not x["unplaced"]:
            continue
        head = "%s%s &middot; %d X-ray &middot; %d %s" % (_h.escape(d["dshort"]), (" (Today)" if eng else " (Aaj)") if d["today"] else "",
                                                          x["n"], x["filed"], "filed" if eng else "file")
        if x["unplaced"]:
            head += " &middot; %d %s" % (x["unplaced"], "pictures without a name" if eng else "photo bina naam")
        rows = []
        for r_ in x["rows"]:
            if r_["st"] in ("filed", "in"):
                continue
            sh = r_.get("sh_en" if eng else "sh") or ""
            rows.append('<div style="padding:2px 0 2px 10px"><b>%s</b> %s%s &middot; <span style="color:%s">%s</span></div>'
                        % (_h.escape(r_["cid"]), _h.escape(r_["name"]), (" &middot; " + _h.escape(sh)) if sh else "",
                           "#9c2a20" if r_["st"] in ("pending", "issue") else "#3c464e", _S840_ST.get(r_["st"], (r_["st"], r_["st"]))[k]))
        days.append('<div style="padding:6px 0;border-bottom:1px solid #e1e7eb"><div style="font-weight:600">%s</div>%s</div>' % (head, "".join(rows)))
    if not days:
        return ""
    title = ("X-rays, the last 7 days" if eng else "X-ray, pichhle 7 din") + (
        (" &mdash; %d photos to upload" if eng else " &mdash; upload baaki %d") % up if up else "")
    return ('<details id="s840x" class="box" style="margin:0 0 10px"%s><summary style="font-size:18px;font-weight:700;color:#14456e;'
            'cursor:pointer;min-height:40px">%s</summary><div style="font-size:15px">%s</div><p class="sm"><a href="/finance/checks">%s</a></p>'
            '</details>' % (" open" if up else "", title, "".join(days), "Check karein &rarr;"))
''')
r('''def _s757_extra(con, eng, u):
    import html as _h                                    # noqa: PLC0415
    out = ['<div id="s757s" hidden style="position:sticky;top:0;z-index:20;background:#0F5E57;color:#fff;padding:8px 14px;'
           'font:600 15px/1.3 system-ui,sans-serif"><a href="/finance/checks" style="color:#fff;text-decoration:none">'
           '<span id="s757t"></span> &rarr;</a></div>'
           '<script>(function(){var s=document.getElementById("s757s");document.body.insertBefore(s,document.body.firstChild);'
           'fetch("/finance/checks/api/mine",{credentials:"same-origin",cache:"no-store"}).then(function(r){return r.ok?r.json():null;})'
           '.then(function(d){if(d&&d.open>0){document.getElementById("s757t").textContent=d.text;s.hidden=false;}}).catch(function(){});})();</script>']
''', '''def _s757_extra(con, eng, u, up=0):
    import html as _h                                    # noqa: PLC0415
    upw = json.dumps((("X-ray photos to upload: %d" if eng else "X-ray upload baaki %d") % up) if up else "")
    out = ['<div id="s757s" hidden style="position:sticky;top:0;z-index:20;background:#0F5E57;color:#fff;padding:8px 14px;'
           'font:600 15px/1.3 system-ui,sans-serif"><a href="/finance/checks" style="color:#fff;text-decoration:none">'
           '<span id="s757t"></span><span id="s840u"></span> &rarr;</a></div>'
           '<script>(function(){var s=document.getElementById("s757s");document.body.insertBefore(s,document.body.firstChild);'
           'var U=' + upw.replace("</", "<\\\\/") + ',ut=document.getElementById("s840u"),tt=document.getElementById("s757t");'
           'if(U){ut.textContent=U;s.hidden=false;}'
           'fetch("/finance/checks/api/mine",{credentials:"same-origin",cache:"no-store"}).then(function(r){return r.ok?r.json():null;})'
           '.then(function(d){if(d&&d.open>0){tt.textContent=d.text;if(U)ut.textContent=" \\u00b7 "+U;s.hidden=false;}}).catch(function(){});})();</script>']
''')
r('''    if not noid and str(f.get("clinic_id") or "").strip() and not cid:
        return _j(ok=False, err="Clinic ID mein sirf number likhein.")
''', '''    if not noid and str(f.get("clinic_id") or "").strip() and not cid:
        return _j(ok=False, err="Clinic ID mein sirf number likhein.")
    if cid and re.search(r"[A-Za-z]", cid) and not SL.patient(con, cid):   # S840 (A-D55): a typed name never becomes a clinic ID
        return _j(ok=False, err=("A name is not a clinic ID -- pick the patient from the list under the box." if eng else
                                 "Naam clinic ID nahi hai -- box ke neeche list mein se mareez chunein."))
''')
r('''    cid = SL._clean_id(f.get("clinic_id"))
    if not cid:
        return _j(ok=False, err="Mareez chunein ya clinic ID likhein.")
''', '''    cid = SL._clean_id(f.get("clinic_id"))
    if not cid:
        return _j(ok=False, err="Mareez chunein ya clinic ID likhein.")
    if re.search(r"[A-Za-z]", cid) and not SL.patient(con, cid):        # S840 (A-D55): a typed name never becomes a clinic ID
        return _j(ok=False, err=("A name is not a clinic ID -- pick the patient from the list under the box." if _eng(u) else
                                 "Naam clinic ID nahi hai -- box ke neeche list mein se mareez chunein."))
''')
r('''def _body():
    try:''', '''@bp.route("/finance/slips/desk/api/find")
def api_find():
    """S840 (A-D55): patients by NAME for the desk's three clinic-ID boxes -- up to 8: id, name, the mobile's last four, came that
    day (check_screens.find_people, which never returns a merged patient). A name only (3+ characters with a letter); an ID is
    looked up by /api/patient as before. Never a full mobile number."""
    u, err = _gate()
    if err:
        return err
    q = str(request.args.get("q") or "").strip()[:60]
    if len(q) < 3 or not re.search(r"[A-Za-z]", q):
        return _j(ok=True, pats=[])
    day = _day_arg(request.args.get("day")) or _SL()._today()
    try:
        import check_screens                             # noqa: PLC0415
        check_screens._rec()
        rows = check_screens.find_people(_db(), q, day)
    except Exception:                                    # noqa: BLE001
        return _j(ok=False, pats=[])
    out = []
    for p in rows[:8]:
        m = re.sub(r"\\D", "", str(p.get("mobile") or ""))
        out.append(dict(id=str(p.get("id") or ""), name=str(p.get("name") or ""), m4=m[-4:] if len(m) >= 4 else "", came=bool(p.get("came"))))
    return _j(ok=True, pats=out)


def _body():
    try:''')
# ---- the page
r('.sm{font-size:15px;color:#3c464e}\n', '.sm{font-size:15px;color:#3c464e}\n'
  '.fd{display:flex;flex-direction:column;gap:4px;margin:-4px 0 8px}.fd:empty{display:none}.fd button{text-align:left;min-height:44px;border:2px solid var(--accent);'
  'background:#fff;color:var(--ink);border-radius:8px;padding:6px 10px;font-size:16px}.fd .fdn{font-size:15px;color:var(--warn);font-weight:600}\n')
r('<label class="f"><span data-t="cid">Clinic ID</span><input id="opd_id" inputmode="numeric" autocomplete="off"></label>',
  '<label class="f"><span data-t="cid">Clinic ID</span><input id="opd_id" inputmode="text" autocomplete="off"></label><div class="fd" id="opd_fd"></div>')
r('<label class="f"><span data-t="or_id">ya clinic ID</span><input id="xp_id" inputmode="numeric" autocomplete="off"></label>',
  '<label class="f"><span data-t="or_id">ya clinic ID</span><input id="xp_id" inputmode="text" autocomplete="off"></label><div class="fd" id="xp_fd"></div>')
r('<label class="f"><span data-t="or_id">ya clinic ID</span><input id="bl_id" inputmode="numeric" autocomplete="off"></label>',
  '<label class="f"><span data-t="or_id">ya clinic ID</span><input id="bl_id" inputmode="text" autocomplete="off"></label><div class="fd" id="bl_fd"></div>')
r('cid:["Clinic ID","Clinic ID"]', 'cid:["Clinic ID ya naam","Clinic ID or name"]')
r('or_id:["ya clinic ID","or the clinic ID"]', 'or_id:["ya clinic ID / naam","or the clinic ID / name"]')
r('saving:["Save ho raha hai…","Saving…"],',
  'byname:["naam se — neeche list mein se mareez chunein","by name — pick the patient from the list below"],'
  'pickl:["Naam clinic ID nahi hai — box ke neeche list mein se mareez chunein","A name is not a clinic ID — pick the patient from the list under the box"],'
  'nof:["is naam se koi nahi mila — poora naam ya clinic ID likhein","no match — type the full name or the clinic ID"],came:["aaj/kal aaya","came that day"],'
  'saving:["Save ho raha hai…","Saving…"],')
r("function look(inp,out,cb){var v=inp.value.trim();if(!v){out.textContent='';out.className='name';cb&&cb(null);return;}",
  "function look(inp,out,cb){var v=inp.value.trim();if(!v){out.textContent='';out.className='name';cb&&cb(null);return;}\n"
  " if(/[A-Za-z]/.test(v)&&!SELV[v]){out.textContent=w('byname');out.className='name new';cb&&cb(null);return;}   /* S840: a name -- the list below, never /api/patient */")
r("function deb(fn){var h;return function(){clearTimeout(h);h=setTimeout(fn,250);};}",
  "function deb(fn){var h;return function(){clearTimeout(h);h=setTimeout(fn,250);};}\n"
  "/* S840 (A-D55): a NAME typed in a clinic-ID box -- the list under it; a name is never saved as a clinic ID */\n"
  "function idOnly(v){return /[A-Za-z]/.test(v)&&!SELV[v]?'':v;}\n"
  "var FD={opd:[],xp:[],bl:[]},SELV={};   /* SELV: IDs picked from the server's own list (a master ID may hold a letter) */\n"
  "function fdHide(wh){var el=$(wh+'_fd');if(el)el.innerHTML='';}\n"
  "function fdClose(wh){fdHide(wh);FD[wh]=[];}\n"
  "function fdShow(wh){var el=$(wh+'_fd');el.innerHTML='';\n"
  " if(!FD[wh].length){el.innerHTML='<div class=\"fdn\">'+esc(w('nof'))+'</div>';return;}\n"
  " FD[wh].forEach(function(p){var b=document.createElement('button');b.type='button';\n"
  "  b.textContent=p.id+' · '+p.name+(p.m4?' · …'+p.m4:'')+(p.came?' · '+w('came'):'');\n"
  "  b.addEventListener('mousedown',function(e){e.preventDefault();});b.addEventListener('click',function(){fdPick(wh,p);});el.appendChild(b);});}\n"
  "function fdPick(wh,p){fdClose(wh);SELV[p.id]=1;var inp=$(wh+'_id');inp.value=p.id;if(wh==='opd'){look(inp,$('opd_name'));}else{setPick(wh,p.id,p.name);}inp.focus();}\n"
  "function finder(wh){var inp=$(wh+'_id');\n"
  " var go=deb(function(){var v=inp.value.trim();if(!/[A-Za-z]/.test(v)||v.length<3||SELV[v]){fdClose(wh);return;}\n"
  "  api('/finance/slips/desk/api/find?q='+encodeURIComponent(v)+'&day='+encodeURIComponent(day)).then(function(r){if(inp.value.trim()!==v)return;\n"
  "   FD[wh]=(r&&r.ok&&r.pats)||[];fdShow(wh);});});\n"
  " inp.addEventListener('input',function(){FD[wh]=[];go();});   /* a changed box never keeps the old list's answer */\n"
  " inp.addEventListener('keydown',function(e){if(e.key==='Escape')fdClose(wh);});\n"
  " inp.addEventListener('blur',function(){setTimeout(function(){fdHide(wh);},250);});}\n"
  "function idFor(wh){var v=$(wh+'_id').value.trim();if(!/[A-Za-z]/.test(v)||SELV[v])return v;\n"
  " var L=FD[wh]||[];if(L.length===1){fdPick(wh,L[0]);return null;}   /* the one match is picked; the next Save saves it */\n"
  " if(L.length)fdShow(wh);msg(false,w('pickl'));return null;}")
r("$('xp_id').addEventListener('input',deb(function(){pick.xp=$('xp_id').value.trim();draw(S);look($('xp_id'),$('xp_name'));}));",
  "$('xp_id').addEventListener('input',deb(function(){pick.xp=idOnly($('xp_id').value.trim());draw(S);look($('xp_id'),$('xp_name'));}));")
r("$('bl_id').addEventListener('input',deb(function(){pick.bl=$('bl_id').value.trim();draw(S);look($('bl_id'),$('bl_name'));}));",
  "$('bl_id').addEventListener('input',deb(function(){pick.bl=idOnly($('bl_id').value.trim());draw(S);look($('bl_id'),$('bl_name'));}));")
r("function saveOpd(extra){var b={series:'opd',slip_no:$('opd_no').value.trim(),clinic_id:$('opd_id').value.trim(),",
  "function saveOpd(extra){var cidv=$('opd_noid').checked?$('opd_id').value.trim():idFor('opd');if(cidv===null)return;\n"
  " var b={series:'opd',slip_no:$('opd_no').value.trim(),clinic_id:cidv,")
r("if(r.ok){msg(true,r.msg);$('opd_id').value='';", "if(r.ok){fdClose('opd');msg(true,r.msg);$('opd_id').value='';")
r(" var b={series:'xp',slip_no:$('xp_no').value.trim(),clinic_id:$('xp_id').value.trim(),",
  " var cidv=idFor('xp');if(cidv===null)return;\n var b={series:'xp',slip_no:$('xp_no').value.trim(),clinic_id:cidv,")
r("if(r.ok){msg(true,r.msg);sel=[];drawSel();", "if(r.ok){fdClose('xp');msg(true,r.msg);sel=[];drawSel();")
r("$('bl_go').addEventListener('click',function(){var cid=$('bl_id').value.trim();$('bl_go').disabled=true;",
  "$('bl_go').addEventListener('click',function(){var cid=idFor('bl');if(cid===null)return;$('bl_go').disabled=true;")
r("if(r.ok){msg(true,r.msg);$('bl_id').value='';", "if(r.ok){fdClose('bl');msg(true,r.msg);$('bl_id').value='';")
r("drawTiles();drawSel();draw(S);$('opd_id').focus();", "['opd','xp','bl'].forEach(finder);\ndrawTiles();drawSel();draw(S);$('opd_id').focus();")
open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("applied:", hashlib.md5(s.encode("utf-8")).hexdigest())
