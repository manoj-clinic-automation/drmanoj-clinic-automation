#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s481.py -- S481_COMMAND_CONSOLE (parent; session 294, 05-Oct-2026). Exact-anchor edits on TWO files, built from
their real bytes at the 05-Oct 01:35 bundle (both unchanged since, the board's v281): /root/finance/finance_app.py 47a83382
and /root/portal/portal.py d9b7685f. Every anchor must be found exactly once; both files are verified before either is written.

WHAT. The owner asked (05-Oct-2026) for one big tile at the top of his Clinic app that shows the day at a glance and opens a
command console: the day's revenues, what waits for him, who did which export and entry and when, attendance, Sanjeevni,
scans and papers, the system -- every section collapsed to a count, expandable, each line a link to the page that owns it.
The reader and its page are NEW files the installer places beside finance_app.py (owner_console.py, owner_console.html).
 finance_app.py (3 edits)
   1. one guarded mount block after the packs block: owner_console.init(app, db, require, unit="packs").
   2. the health row "Parts of the finance app that did not load" learns the new part's name ...
   3. ... and counts 28 parts, not 27.
 portal.py (2 edits)
   4. the Today tile, above the doctor-only strip: hidden until the console's own tile door answers, so for anyone the door
      refuses (every login but the owner's), or with clinic-finance down, the home page is exactly as it was.
   5. its script: one fetch of /finance/console/api/tile, a second look three seconds later while a new reading is made.
NOT TOUCHED: every other route and page, TILES, tile_grants.json, the tile-summary door, the strip's own chips, any table.
   usage: apply_s481.py <finance_app.py> <portal.py>
"""
import hashlib
import sys

FROM = {"finance_app.py": "47a83382595c59f42b80d2f72831837d", "portal.py": "d9b7685f75926164df34a10eca5dcb77"}
ORDER = ("finance_app.py", "portal.py")

# ---------------------------------------------------------------- finance_app.py
A_MOUNT = '''    print("packs NOT mounted: %s" % _ex_pk, file=sys.stderr)
# --- S408_MONTH_END_PACKS end ---
'''
B_MOUNT = A_MOUNT + '''
# --- S481_COMMAND_CONSOLE begin -- the owner's Today tile and command console (owner, 05-Oct-2026) ---
# PARENT. ONE READING LAYER: owner_console.py serves a json file that a SEPARATE SHORT PROCESS makes on a COPY of finance.db
# (the owning modules' own functions, the duty map's own due_sql). Through the live connection it asks one thing only --
# PRAGMA database_list, the file to copy -- and it writes nothing. The owner only (checker of unit 'packs'). GUARDED (S209):
# a fault inside the module is printed and every other page keeps serving.
try:
    import owner_console                                       # noqa: E402
    owner_console.init(app, db, require, unit="packs")
except Exception as _ex_oc:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('owner_console', repr(_ex_oc)[:200]))
    print("owner_console NOT mounted: %s" % _ex_oc, file=sys.stderr)
# --- S481_COMMAND_CONSOLE end ---
'''

A_NAMES = "'packs', 'reception_door', 'pc_kits') if m not in sys.modules and m not in _mf]"
B_NAMES = "'packs', 'reception_door', 'pc_kits', 'owner_console') if m not in sys.modules and m not in _mf]"

A_COUNT = "        _all = 27\n"
B_COUNT = "        _all = 28                                             # S481: + owner_console\n"

# ---------------------------------------------------------------- portal.py (inside PORTAL_HTML: plain ASCII, no doubled brace,
# and no backslash but the page's own \\u00b7 middle dot -- the page is a Jinja template inside a Python string)
A_TILE = '''  {% if role == 'doctor' %}
  <div class="strip">
'''
B_TILE = '''  {% if role == 'doctor' %}
  <style>
  .todaytile{display:block;text-decoration:none;background:#1f5f4a;color:#f2f7f4;border-radius:14px;padding:16px 16px 12px;margin:0 0 12px}
  .todaytile[hidden]{display:none}
  .todaytile .tt-h{display:flex;justify-content:space-between;align-items:baseline;font-size:17px;font-weight:700;margin:0 0 10px}
  .todaytile .tt-h small{font-size:12px;font-weight:400;color:#b9d4c8}
  .todaytile .tt-k{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}
  .todaytile .tt-k b{display:block;font-size:22px;font-weight:600;line-height:1.15;font-variant-numeric:tabular-nums}
  .todaytile .tt-k b.w{color:#f0c56a}
  .todaytile .tt-k b.b{color:#ffb3a3}
  .todaytile .tt-k b.g{color:#9fe0c0}
  .todaytile .tt-k span{display:block;font-size:12px;color:#b9d4c8}
  .todaytile .tt-f{display:flex;justify-content:space-between;gap:10px;margin-top:12px;font-size:13px;color:#b9d4c8}
  </style>
  <a class="todaytile" id="todayTile" href="/finance/console" target="_blank" rel="noopener" hidden>
    <div class="tt-h"><span id="ttDay">Today</span><small id="ttAsOf"></small></div>
    <div class="tt-k">
      <div><b id="ttClinic">&ndash;</b><span id="ttClinicW">Clinic</span></div>
      <div><b id="ttSanj">&ndash;</b><span id="ttSanjW">Sanjeevni</span></div>
      <div><b id="ttNeeds">&ndash;</b><span id="ttNeedsW">waiting for you</span></div>
      <div><b id="ttWork">&ndash;</b><span id="ttWorkW">staff duties late</span></div>
    </div>
    <div class="tt-f"><span id="ttSys"></span><span>Open the console &rarr;</span></div>
  </a>
  <div class="strip">
'''

A_JS = "/* S472: Shavez's 'Mahine ka kaam' tile -- "
B_JS = '''/* S481: the owner's Today tile. ONE fetch of the console's own tile door (the owner only). The tile is hidden until that
   door answers: for any other login, or with finance down, the home page is exactly as before. While a new reading is being
   made the door says so and the tile looks again three seconds later (eight looks at most). */
(function(){
  var t=document.getElementById('todayTile');
  if(!t)return;
  var tries=0;
  function put(id,v,c){
    var e=document.getElementById(id);
    if(!e)return;
    if(v!==undefined&&v!==null)e.textContent=v;
    if(c!==undefined)e.className=c;
  }
  function load(){
    fetch('/finance/console/api/tile',{credentials:'same-origin'})
     .then(function(r){return r.ok?r.json():null;})
     .then(function(d){
       if(!d||!d.ok)return;
       t.hidden=false;
       var x=d.tile;
       if(x){
         put('ttDay','Today'+(d.day_words?(' \\u00b7 '+d.day_words):''));
         put('ttAsOf',(d.as_of_label||'')+(d.building?' \\u00b7 reading again':''));
         put('ttClinic',x.clinic,x.clinic_cls==='g'?'':(x.clinic_cls||''));
         put('ttClinicW',x.clinic_word);
         put('ttSanj',x.sanj,x.sanj_cls==='g'?'':(x.sanj_cls||''));
         put('ttSanjW',x.sanj_word);
         var n=x.needs_n||0;
         put('ttNeeds',String(n),n?(x.needs_late?'b':'w'):'g');
         put('ttNeedsW','waiting for you'+(x.needs_late?(' \\u00b7 '+x.needs_late+' late'):''));
         var late=(x.work_late||0)+(x.work_not_done||0);
         put('ttWork',String(late),late?(x.work_not_done?'b':'w'):'g');
         put('ttWorkW','staff duties late'+(x.att_total?(' \\u00b7 '+x.att_in+' of '+x.att_total+' in'):''));
         put('ttSys','System: '+(x.sys_word||'not read'));
       }else{
         put('ttAsOf','reading the clinic, a few seconds');
       }
       if(d.building&&tries<8){tries++;setTimeout(load,3000);}
     })
     .catch(function(){});
  }
  load();
})();
''' + A_JS

EDITS = {"finance_app.py": [(A_MOUNT, B_MOUNT), (A_NAMES, B_NAMES), (A_COUNT, B_COUNT)],
         "portal.py": [(A_TILE, B_TILE), (A_JS, B_JS)]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: apply_s481.py <finance_app.py> <portal.py>")
    for b in (B_TILE, B_JS):                              # the template's own hazards, refused before anything is read
        if "\\" in b.replace("\\u00b7", "") or "{{" in b or "}}" in b or "{#" in b or '"""' in b or any(ord(c) > 126 for c in b):
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
