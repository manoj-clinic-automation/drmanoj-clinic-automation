#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s757.py -- builds kit S757_XRAY_LAB_CHECK's files from the LIVE bytes (the 09-Nov bundle; every base pinned by md5).

  python3 make_s757.py <dir holding the live records.py, parchi_desk.py, owner_console.py, aaj_seed.py, aaj_duties.json,
                        tile_grants.json> <out dir>

  records.py        4 edits: the module's note; the home page's way in to his X-ray page; Check karein drawn by check_screens
                             (the old list stays as the fallback and at ?list=1, its item forms one function); check_screens'
                             doors attached to the blueprint at import
  parchi_desk.py    3 edits: the note; the page carries the Check karein strip and, from a lab item, the blood slip filled in;
                             the blood door takes a lab item's key and writes the slip on that item's visit day
  owner_console.py  2 edits: his 'Scans & papers' section gains one line -- the four tiles' counts, opening his X-ray page
  aaj_seed.py       1 edit : Shavez's morning line 'Check karein: X-ray photo aur lab report dekhiye'
  aaj_duties.json   1 edit : its fetch duty (asks GET /finance/checks/api/mine) -- shipped as aaj_duties.json.kit
  tile_grants.json  2 edits: F-1185 -- 'Marg Purchases' leaves the owner's mask (the tile shows on his home); version 44
                             -- shipped as tile_grants.json.kit
  check_screens.py  NEW, copied from beside this script.
Each base must be the pinned live file and each piece must occur exactly once, or nothing is written."""
import hashlib
import os
import shutil
import sys

BASE = {"records.py": "a6ec1052937e1aee99b515e07e13a853", "parchi_desk.py": "fb405c1233c7f5c808aefb7e67c57a2f",
        "owner_console.py": "f2ab5deb9c5f284b5257a10d4735fce8", "aaj_seed.py": "dc7050d5de882cb65af843beb8110b07",
        "aaj_duties.json": "c5c80c37e5868864a5e6f58ea7c75112", "tile_grants.json": "f2dad1579505c672de4270ed7fecb224"}
OUTNAME = {"aaj_duties.json": "aaj_duties.json.kit", "tile_grants.json": "tile_grants.json.kit"}

# ------------------------------------------------------------------------------------------------ records.py
R1_OLD = '''suggestion on Check karein, never filed by itself.
Flask, requests and the standard library.'''
R1_NEW = '''suggestion on Check karein, never filed by itself.

S757 (S413, 09-Nov-2026, D875 -- the owner's FINAL on mock-up YBLGcgEAGi18QB9PL1bRL4 v9): Check karein is drawn by check_screens.py
beside this file -- each parked X-ray picture with its photo and that day's patients (tap + 'Haan' answers it the S373 way),
Shavez's one queue of X-ray photos and lab reports with no blood slip, and the owner's page /finance/records/xray-check (four
tiles). Without check_screens (or on any fault in it) the page is the list it was; ?list=1 always shows that list.
Flask, requests and the standard library.'''

R2_OLD = '''    body = [_check_line_html(con), '<form class="find" method="get" action="%s"><input name="q" value="%s" placeholder="Clinic ID or name" '
            'autofocus inputmode="search"><button class="go">Open</button></form>' % (P, _esc(q))]'''
R2_NEW = '''    body = [_check_line_html(con), '<p style="margin:0 0 10px"><a class="view" href="%s/xray-check">X-ray photos &amp; lab reports '
            '\\u2192</a></p>' % P,                         # S757 (D875): his four tiles
            '<form class="find" method="get" action="%s"><input name="q" value="%s" placeholder="Clinic ID or name" '
            'autofocus inputmode="search"><button class="go">Open</button></form>' % (P, _esc(q))]'''

R3_OLD = '''    items = _floor_items(con, u, check_items(con))
    ok = request.args.get("ok", "")
    body = ['<div class="ckb"><a class="view" href="%s/add">+ Kagaz jodein (MRI / CT / discharge)</a></div>' % CP]
    if ok:
        body.append('<div class="okb">%s</div>' % _esc(ok))
    if not items:
        body.append('<div class="okb">Sab theek hai — kuch dekhna baaki nahi.</div>')
    for i in items:
        btn = "".join('<button name="a" value="%s">%s</button>' % (c, _esc(l)) for c, l in ANS[i["kind"]])
        extra = ""
        if i["kind"] in ("lab_id", "xray_file"):
            extra = ('<input name="new_id" inputmode="numeric" placeholder="Sahi clinic ID" maxlength="8" value="%s">'
                     '<button name="a" value="id_fixed">Sahi ID lagayein</button>') % _esc(i.get("suggest") or "")   # S752
        if i["kind"] == "wa":
            body.append('<form class="ck" method="post" action="%s/answer"><input type="hidden" name="key" value="%s">'
                        '<div class="ckh"><span class="age">%d din</span></div><div>%s (%s)</div>%s</form>' % (
                            CP, _esc(i["key"]), _age(i["day"]), _esc(i["hi"]), _dmy(i["day"])[:6], _wa_form(i)))
            continue
        body.append('<form class="ck" method="post" action="%s/answer"><input type="hidden" name="key" value="%s">'
                    '<div class="ckh"><b>%s</b> · %s · <span class="age">%d din</span></div>'
                    '<div>%s (%s)</div>%s<div class="ckb">%s%s</div></form>' % (
                        CP, _esc(i["key"]), _esc(i["clinic_id"]), _esc(i["name"] or "—"), _age(i["day"]),
                        _esc(i["hi"]), _dmy(i["day"])[:6], ('<div class="sm">%s</div>' % _esc(i["why"])) if i["why"] else "",
                        extra, btn))   # S752: the ID box first -- Enter in it is 'Sahi ID lagayein', never 'Yeh X-ray nahi'
    return _shell("Check karein", "".join(body), lang="hi")'''
R3_NEW = '''    items = _floor_items(con, u, check_items(con))
    ok = request.args.get("ok", "")
    if not request.args.get("list"):                     # S757 (D875): the photo and lab-report screens; ?list=1 is the old list
        try:
            import check_screens                         # noqa: PLC0415
            return check_screens.staff_page(con, u, [i for i in items if i["kind"] != "xray_file"], ok)
        except Exception:                                # noqa: BLE001 -- the old list stands in
            pass
    body = ['<div class="ckb"><a class="view" href="%s/add">+ Kagaz jodein (MRI / CT / discharge)</a></div>' % CP]
    if ok:
        body.append('<div class="okb">%s</div>' % _esc(ok))
    if not items:
        body.append('<div class="okb">Sab theek hai — kuch dekhna baaki nahi.</div>')
    for i in items:
        body.append(_old_item_html(i))
    return _shell("Check karein", "".join(body), lang="hi")


def _old_item_html(i):
    """One open item as the S340 list draws it (a form posting to /finance/checks/answer). S757: one function, so that
    check_screens draws the items it does not own exactly as before."""
    btn = "".join('<button name="a" value="%s">%s</button>' % (c, _esc(l)) for c, l in ANS[i["kind"]])
    extra = ""
    if i["kind"] in ("lab_id", "xray_file"):
        extra = ('<input name="new_id" inputmode="numeric" placeholder="Sahi clinic ID" maxlength="8" value="%s">'
                 '<button name="a" value="id_fixed">Sahi ID lagayein</button>') % _esc(i.get("suggest") or "")   # S752
    if i["kind"] == "wa":
        return ('<form class="ck" method="post" action="%s/answer"><input type="hidden" name="key" value="%s">'
                '<div class="ckh"><span class="age">%d din</span></div><div>%s (%s)</div>%s</form>' % (
                    CP, _esc(i["key"]), _age(i["day"]), _esc(i["hi"]), _dmy(i["day"])[:6], _wa_form(i)))
    return ('<form class="ck" method="post" action="%s/answer"><input type="hidden" name="key" value="%s">'
            '<div class="ckh"><b>%s</b> · %s · <span class="age">%d din</span></div>'
            '<div>%s (%s)</div>%s<div class="ckb">%s%s</div></form>' % (
                CP, _esc(i["key"]), _esc(i["clinic_id"]), _esc(i["name"] or "—"), _age(i["day"]),
                _esc(i["hi"]), _dmy(i["day"])[:6], ('<div class="sm">%s</div>' % _esc(i["why"])) if i["why"] else "",
                extra, btn))   # S752: the ID box first -- Enter in it is 'Sahi ID lagayein', never 'Yeh X-ray nahi\''''

R4_OLD = '''    except Exception:                                    # noqa: BLE001 -- a suggestion never breaks the page
        pass
    return out
'''
R4_NEW = '''    except Exception:                                    # noqa: BLE001 -- a suggestion never breaks the page
        pass
    return out


# ---------------------------------------------------------------- S757 (S413, 09-Nov-2026, D875): check_screens' doors
# The photo and lab-report screens live in check_screens.py beside this file; their doors go on THIS blueprint here, at import,
# before finance_app registers it. Without that file (or on any fault in it) nothing is added and Check karein is the old list.
try:
    import sys as _s757_sys
    import check_screens as _s757                         # noqa: E402
    _s757.attach(_s757_sys.modules[__name__])
except Exception:                                        # noqa: BLE001
    _s757 = None
'''

# ------------------------------------------------------------------------------------------------ parchi_desk.py
D1_OLD = '''No patient name, no number, no secret in this file (F-185).
"""'''
D1_NEW = '''S757 (S413, 09-Nov-2026, D875): the page carries a strip to Check karein when X-ray photos or lab reports wait for this login
(it asks GET /finance/checks/api/mine), and ?lab=<key> -- from a lab report that came with no blood slip -- shows that patient
with one button that writes the blood slip on the visit day (check_screens.lab_slip_day decides; nothing else may) and goes back.
No patient name, no number, no secret in this file (F-185).
"""'''

D2_OLD = '''    return PAGE.replace("__BOOT__", boot).replace("__LANG__", "en" if eng else "hi").replace(
        "__TITLE__", "Parchi desk" if eng else "Parchi desk")'''
D2_NEW = '''    html = PAGE.replace("__BOOT__", boot).replace("__LANG__", "en" if eng else "hi").replace(
        "__TITLE__", "Parchi desk" if eng else "Parchi desk")
    try:                                                 # S757 (D875): the Check karein strip; a lab report's blood slip
        html = html.replace("</body>", _s757_extra(con, eng, u) + "</body>", 1)
    except Exception:                                    # noqa: BLE001 -- the desk as it was
        pass
    return html


def _s757_extra(con, eng, u):
    import html as _h                                    # noqa: PLC0415
    out = ['<div id="s757s" hidden style="position:sticky;top:0;z-index:20;background:#0F5E57;color:#fff;padding:8px 14px;'
           'font:600 15px/1.3 system-ui,sans-serif"><a href="/finance/checks" style="color:#fff;text-decoration:none">'
           '<span id="s757t"></span> &rarr;</a></div>'
           '<script>(function(){var s=document.getElementById("s757s");document.body.insertBefore(s,document.body.firstChild);'
           'fetch("/finance/checks/api/mine",{credentials:"same-origin",cache:"no-store"}).then(function(r){return r.ok?r.json():null;})'
           '.then(function(d){if(d&&d.open>0){document.getElementById("s757t").textContent=d.text;s.hidden=false;}}).catch(function(){});})();</script>']
    key = (request.args.get("lab") or "")[:80]
    if key:
        import check_screens                             # noqa: PLC0415
        it = check_screens.lab_item(con, key) if check_screens._lab_ok(con, u) else None   # the lab logins only
        if it and not it["wrong"]:
            day = check_screens._short(it["slip_day"])
            out.append(
                '<div id="s757l" style="margin:12px;border:2px solid #1D4ED8;border-radius:12px;background:#EEF2FF;padding:12px 14px;'
                'font:16px/1.4 system-ui,sans-serif;display:flex;flex-wrap:wrap;gap:10px;align-items:center">'
                '<span style="flex:1;min-width:240px"><b>%s</b> &middot; ID %s<br><span style="font-size:14px;color:#1E3A8A">%s</span></span>'
                '<button id="s757go" style="min-height:48px;padding:0 18px;border:0;border-radius:10px;background:#1D4ED8;color:#fff;'
                'font-weight:700;font-size:16px">%s</button><a href="/finance/checks" style="font-size:15px">%s</a>'
                '<span id="s757m" style="width:100%%;color:#9c2a20;font-weight:600"></span></div>'
                '<script>(function(){var b=document.getElementById("s757l");document.body.insertBefore(b,document.body.firstChild.nextSibling);'
                'document.getElementById("s757go").onclick=function(){var g=this;g.disabled=true;fetch("/finance/slips/desk/api/blood",'
                '{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({clinic_id:%s,lab_key:%s})})'
                '.then(function(r){return r.json();}).then(function(r){if(r.ok){location.href="/finance/checks?ok="+encodeURIComponent(r.msg);}'
                'else{g.disabled=false;document.getElementById("s757m").textContent=r.err||"";}}).catch(function(){g.disabled=false;});};})();</script>'
                % (_h.escape(it["name"]), _h.escape(it["cid"]),
                   _h.escape(("Lab report of %s came with no blood slip. Use this button \u2014 the slip is written on %s by itself." if eng else
                              "%s ki lab report aayi, blood parchi nahi bani. Yahi button dabaiye \u2014 parchi apne aap %s ki banegi.") % (it["dshort"], day)),
                   "Save the blood slip" if eng else "Blood parchi save karein", "Back" if eng else "Wapas",
                   json.dumps(it["cid"]), json.dumps(key)))
    return "".join(out)'''

D3_OLD = '''    day = SL._today()
    if con.execute("SELECT 1 FROM blood_order WHERE day=? AND clinic_id=? AND state='ok'", (day, cid)).fetchone():
        return _j(ok=False, err="ID %s ka blood test aaj pehle se likha hai." % cid)
    p = SL.patient(con, cid)
    c = con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                    (day, cid, p[0] if p else "", SL._who(u), SL._stamp()))
    SL._audit_safe(con, c.lastrowid, "blood_order", None, json.dumps({"cid": cid, "via": "desk"}), SL._who(u))'''
D3_NEW = '''    day = SL._today()
    lab_key = str(f.get("lab_key") or "")[:80]           # S757 (D875): the slip for a lab report that came with none
    if lab_key:
        try:
            import check_screens                         # noqa: PLC0415
            lab_day = check_screens.lab_slip_day(con, lab_key, cid) if check_screens._lab_ok(con, u) else None
        except Exception:                                # noqa: BLE001
            lab_day = None
        if not lab_day:
            return _j(ok=False, err="Yeh lab report ab list mein nahi hai (shayad ho chuki hai).")
        day = lab_day
    if con.execute("SELECT 1 FROM blood_order WHERE day=? AND clinic_id=? AND state='ok'", (day, cid)).fetchone():
        return _j(ok=False, err="ID %s ka blood test %s pehle se likha hai." % (cid, "us din" if lab_key else "aaj"))
    p = SL.patient(con, cid)
    c = con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                    (day, cid, p[0] if p else "", SL._who(u), SL._stamp()))
    SL._audit_safe(con, c.lastrowid, "blood_order", None, json.dumps({"cid": cid, "via": "desk", "lab": lab_key} if lab_key
                                                                     else {"cid": cid, "via": "desk"}), SL._who(u))'''

# ------------------------------------------------------------------------------------------------ owner_console.py
O1_OLD = '''    def baaki():
        import slip_log                                                # noqa: PLC0415
        c = slip_log.pending_counts(con)'''
O1_NEW = '''    def s757():                                                        # S757 (D875): the four tiles of his X-ray page
        import check_screens                                           # noqa: PLC0415
        c = check_screens.counts(con)
        tot["n"] += int(c["nox"]) + int(c["lab"])                      # the waiting photos are in the records line already
        t = ("X-ray photos & lab reports: %d photo%s waiting for staff · %d X-ray%s with no X-ray slip · %d lab report%s with no "
             "blood slip · %d filed by themselves since 8-Nov" % (c["wait"], "" if c["wait"] == 1 else "s", c["nox"],
                                                                  "" if c["nox"] == 1 else "s", c["lab"], "" if c["lab"] == 1 else "s",
                                                                  c["filed"]))
        return L("w" if (c["wait"] or c["nox"] or c["lab"]) else "g", t, href="/finance/records/xray-check", link="X-ray photos")

    def baaki():
        import slip_log                                                # noqa: PLC0415
        c = slip_log.pending_counts(con)'''
O2_OLD = '''    piece(lines, "The patient-record checks", recs)
'''
O2_NEW = '''    piece(lines, "The patient-record checks", recs)
    piece(lines, "The X-ray photo and lab-report checks", s757)
'''

# ------------------------------------------------------------------------------------------------ aaj_seed.py / aaj_duties.json
S_OLD = """             'opens': 'Kal ke procedures'},
            {'id': 'shavez.xray_film_count',"""
S_NEW = """             'opens': 'Kal ke procedures'},
            {'id': 'shavez.check_karein',                      # S757 (D875, 09-Nov-2026): photos and lab reports waiting
             'hi': 'Check karein: X-ray photo aur lab report dekhiye',
             'en': "X-ray photos with no patient yet, and lab reports that came with no blood slip -- one queue on his PC.",
             'when': 'first',
             'on': True,
             'opens': 'Check karein'},
            {'id': 'shavez.xray_film_count',"""

J_OLD = '''   "ok_hi": "11×14 film: box mein kaafi film hai"
  }
 ]
}
'''
J_NEW = '''   "ok_hi": "11×14 film: box mein kaafi film hai"
  },
  {
   "id": "shavez.check_karein",
   "person": "shavez",
   "kind": "fetch",
   "group": "open",
   "hi": "Check karein: X-ray photo aur lab report dekhiye",
   "en": "Shavez: X-ray photos with no patient yet and lab reports with no blood slip (S757, D875; read on the page from Check karein's own door)",
   "tile": "Check karein",
   "door": "/finance/checks",
   "fetch": {"url": "/finance/checks/api/mine", "field": "open", "text_field": "text"}
  }
 ]
}
'''

# ------------------------------------------------------------------------------------------------ tile_grants.json
T1_OLD = ''' "version": 43,'''
T1_NEW = ''' "version": 44,'''
T2_OLD = '''    "Order Medicines",
    "Marg Purchases",
    "Stock milaan",'''
T2_NEW = '''    "Order Medicines",
    "Stock milaan",'''

EDITS = {"records.py": [(R1_OLD, R1_NEW), (R2_OLD, R2_NEW), (R3_OLD, R3_NEW), (R4_OLD, R4_NEW)],
         "parchi_desk.py": [(D1_OLD, D1_NEW), (D2_OLD, D2_NEW), (D3_OLD, D3_NEW)],
         "owner_console.py": [(O1_OLD, O1_NEW), (O2_OLD, O2_NEW)],
         "aaj_seed.py": [(S_OLD, S_NEW)],
         "aaj_duties.json": [(J_OLD, J_NEW)],
         "tile_grants.json": [(T1_OLD, T1_NEW), (T2_OLD, T2_NEW)]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(src, out):
    built = {}
    for name, edits in EDITS.items():
        raw = open(os.path.join(src, name), "rb").read()
        if md5(raw) != BASE[name]:
            sys.exit("STOP: %s is %s, not the pinned live %s -- nothing written" % (name, md5(raw)[:8], BASE[name][:8]))
        txt = raw.decode("utf-8")
        for i, (old, new) in enumerate(edits, 1):
            n = txt.count(old)
            if n != 1:
                sys.exit("STOP: %s edit %d: the piece occurs %d times, not once -- nothing written" % (name, i, n))
            txt = txt.replace(old, new, 1)
        built[name] = txt.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    for name, b in built.items():
        open(os.path.join(out, OUTNAME.get(name, name)), "wb").write(b)
        print("%-17s %s -> %s  %d counted edit(s)" % (name, BASE[name][:8], md5(b), len(EDITS[name])))
    here = os.path.dirname(os.path.abspath(__file__))
    cs = os.path.join(here, "check_screens.py")
    if os.path.abspath(os.path.join(out, "check_screens.py")) != os.path.abspath(cs):
        shutil.copyfile(cs, os.path.join(out, "check_screens.py"))
    print("%-17s NEW      -> %s" % ("check_screens.py", md5(open(cs, "rb").read())))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
