#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s487.py -- S487_AAJ_KA_KAAM (parent; session 294, 05-Oct-2026; D679). Exact-anchor edits on TWO files, built from
their real bytes as S481 left them on the server at 18:22 IST on 05-Oct: /root/finance/finance_app.py ef1382d2 and
/root/portal/portal.py 10a675e7. Every anchor must be found exactly once; both files are verified before either is written.

WHAT. The staff's own daily list, 'Aaj ka kaam' (aaj_kaam.py, its page and aaj_duties.json are NEW files the installer
places; owner_console.py and owner_console.html are replaced whole by their 1.1).
 finance_app.py (4 edits)
   1. IDENTITY_ONLY_PATHS gains the list's five doors: a signed-in clinic login reaches ITS OWN list without holding a row in
      any unit (Bhati holds none in 'medical'); what a login may see is decided inside aaj_kaam.py, by its name.
   2. one guarded mount block after S481's: aaj_kaam.init(app, db, require, current_user).
   3. the health row "Parts of the finance app that did not load" learns the new part's name ...
   4. ... and counts 29 parts, not 28.
 portal.py (2 edits)
   5. the staff's tile 'Aaj ka kaam' at the top of the home page for every role but the doctor's, hidden until the list's own
      line door says show -- which it does only once the owner has turned the lists on.
   6. its script: one fetch of /finance/aaj/api/line.
NOT TOUCHED: every other route and page, TILES, tile_grants.json, the duty map, any table.
   usage: apply_s487.py <finance_app.py> <portal.py>
"""
import hashlib
import sys

FROM = {"finance_app.py": "ef1382d2ce26d13d3c8388fdeb85e867", "portal.py": "10a675e750086b4bffc6b1b1e41ea8de"}
ORDER = ("finance_app.py", "portal.py")

# ---------------------------------------------------------------- finance_app.py
A_IDENT = 'IDENTITY_ONLY_PATHS = ("/finance/api/whoami", "/finance/clinic/api/whoami")\n'
B_IDENT = ('IDENTITY_ONLY_PATHS = ("/finance/api/whoami", "/finance/clinic/api/whoami",\n'
           '                       # S487: the staff\'s own list. A signed-in login reaches ITS OWN list; aaj_kaam.py decides by name.\n'
           '                       "/finance/aaj", "/finance/aaj/api/list", "/finance/aaj/api/line", "/finance/aaj/api/tick",\n'
           '                       "/finance/aaj/api/switch")\n')

A_MOUNT = '''    print("owner_console NOT mounted: %s" % _ex_oc, file=sys.stderr)
# --- S481_COMMAND_CONSOLE end ---
'''
B_MOUNT = A_MOUNT + '''
# --- S487_AAJ_KA_KAAM begin -- the staff's own daily list, 'Aaj ka kaam' (owner, 05-Oct-2026, D679) ---
# PARENT. One list per login: the duty map by its own due_sql with nothing before the floor (01-Sep-2026) counted, the parent's
# extra lines (aaj_duties.json), and the taps. Reading is plain SELECTs through a read-only connection of the module's own;
# its two writes are a tap (duty_tick, made on the first tap) and the owner's switch (setting aaj.staff_on). OFF for staff
# until the owner turns it on. GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import aaj_kaam                                            # noqa: E402
    aaj_kaam.init(app, db, require, current_user)
except Exception as _ex_ak:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('aaj_kaam', repr(_ex_ak)[:200]))
    print("aaj_kaam NOT mounted: %s" % _ex_ak, file=sys.stderr)
# --- S487_AAJ_KA_KAAM end ---
'''

A_NAMES = "'packs', 'reception_door', 'pc_kits', 'owner_console') if m not in sys.modules and m not in _mf]"
B_NAMES = "'packs', 'reception_door', 'pc_kits', 'owner_console', 'aaj_kaam') if m not in sys.modules and m not in _mf]"

A_COUNT = "        _all = 28                                             # S481: + owner_console\n"
B_COUNT = "        _all = 29                                             # S481: + owner_console · S487: + aaj_kaam\n"

# ---------------------------------------------------------------- portal.py (inside PORTAL_HTML: plain ASCII, no doubled brace,
# no backslash -- the page is a Jinja template inside a Python string)
A_TILE = '''  {% if role == 'doctor' %}
  <style>
  .todaytile{display:block;'''
B_TILE = '''  {% if role != 'doctor' %}
  <style>
  .kaamtile{display:block;text-decoration:none;background:#14456e;color:#fff;border-radius:14px;padding:16px 16px 14px;margin:0 0 12px}
  .kaamtile[hidden]{display:none}
  .kaamtile .kt-h{font-size:20px;font-weight:700;margin:0 0 4px}
  .kaamtile .kt-l{font-size:17px}
  .kaamtile .kt-l.late{color:#ffd0c9;font-weight:700}
  .kaamtile .kt-f{margin-top:8px;font-size:14px;color:#c9dcea}
  </style>
  <a class="kaamtile" id="kaamTile" href="/finance/aaj" target="_blank" rel="noopener" hidden>
    <div class="kt-h">Aaj ka kaam</div>
    <div class="kt-l" id="kaamLine"></div>
    <div class="kt-f">List kholiye &rarr;</div>
  </a>
  {% endif %}
''' + A_TILE

A_JS = "/* S481: the owner's Today tile. ONE fetch of the console's own tile door (the owner only). The tile is hidden until that\n"
B_JS = '''/* S487: the staff's 'Aaj ka kaam' tile. ONE fetch of the list's own line door. Hidden until that door says show -- which it
   does only for a login that has a list, and only once the owner has turned the lists on. Finance down: the home is as before.
   A line whose count lives behind another app's door (the staff register, Mahine ka kaam) is counted here exactly as the list's
   own page counts it: that door is asked with this login, and one is added when it has something waiting. */
(function(){
  var t=document.getElementById('kaamTile');
  if(!t)return;
  fetch('/finance/aaj/api/line',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok||!d.show)return;
     var l=document.getElementById('kaamLine'), n=Number(d.open||0), late=Number(d.late||0);
     function draw(){
       if(!l)return;
       l.textContent=n?(n+' kaam baaki'+(late?(' '+String.fromCharCode(183)+' '+late+' late'):'')):(d.text_hi||'');
       l.className=late?'kt-l late':'kt-l';
     }
     draw();
     t.hidden=false;
     (d.fetch||[]).forEach(function(f){
       fetch(f.url,{credentials:'same-origin'})
        .then(function(r){return r.ok?r.json():null;})
        .then(function(j){
          if(!j)return;
          if(f.only_if&&!j[f.only_if])return;
          if(Number(j[f.field]||0)>0){n+=1;draw();}
        })
        .catch(function(){});
     });
   })
   .catch(function(){});
})();
''' + A_JS

EDITS = {"finance_app.py": [(A_IDENT, B_IDENT), (A_MOUNT, B_MOUNT), (A_NAMES, B_NAMES), (A_COUNT, B_COUNT)],
         "portal.py": [(A_TILE, B_TILE), (A_JS, B_JS)]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: apply_s487.py <finance_app.py> <portal.py>")
    for a, b in ((A_TILE, B_TILE), (A_JS, B_JS)):         # the template's own hazards, refused before anything is read
        new = b.replace(a, "")
        if "\\\\" in new or "\\" in new or "{{" in new or "}}" in new or "{#" in new or '"""' in new or any(ord(c) > 126 for c in new):
            raise SystemExit("a portal block carries a backslash, a doubled brace or a non-ASCII letter -- nothing written")
    out = {}
    for name, path in zip(ORDER, argv[1:]):
        with open(path, encoding="utf-8", newline="") as fh:
            src = fh.read()
        if md5(src.encode("utf-8")) != FROM[name]:
            raise SystemExit("%s is %s, not the %s this kit was built on -- nothing written" % (name, md5(src.encode("utf-8")), FROM[name]))
        for i, (a, b) in enumerate(EDITS[name], 1):
            n = src.count(a)
            if n != 1:
                raise SystemExit("%s: anchor %d found %d times (must be exactly once) -- nothing written" % (name, i, n))
            src = src.replace(a, b)
        compile(src, name, "exec")
        out[name] = (path, src)
    for name in ORDER:                                    # both verified; only now is either written
        path, src = out[name]
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(src)
        print("%s  %s  (%d edits)" % (md5(src.encode("utf-8")), name, len(EDITS[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
