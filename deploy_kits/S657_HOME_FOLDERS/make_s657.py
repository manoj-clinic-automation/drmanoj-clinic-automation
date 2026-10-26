"""make_s657.py -- kit S657_HOME_FOLDERS (Sanjeevni session S353, 26-Oct-2026). The owner's "build" (06:04 IST) on the mock-up
https://claude.ai/artifact/7YXMpfkuiU4awTHHkNSNfu, after his "yes" (05:47) to the Expiry watch box and his ask (05:45) that the
expiry page stay exactly as designed and only become easy to reach.
  /root/portal/portal.py                          844166b1 -> TO   (THE PARENT'S FILE) 9 counted edits:
        P1 the strip takes a fourth box (and goes back to three when that box hides itself)  P2 a box with something due is amber
        P3 a folded group opens IN PLACE below its tile, not as a full-screen sheet  P4 the Expiry watch box  P5 a tile may name whose
        screen it is  P6 the group tiles are buttons with their panel beside them; the sheets go  P7 the accordion's script  P8 the box's
        number  P9 the split of the Sanjeevni group for a login that folds it (his) + the face of his Sanjeevni folder
  /root/portal/tile_grants.json                   025f8ab9 -> TO   (THE PARENT'S FILE) v39 -> v40: manoj's mask (Daily Sale, Order Medicines,
        Marg Purchases, Stock milaan leave HIS home only) and his folder order (the mock-up's)
  /root/finance/sanjeevni_approvals.py            bf86c8c8 -> TO   1 edit: GET /finance/sanjeevni/expiry/api/count (checker only, read only)
  /root/finance/finance_ui/finance_approvals.html 885f6f31 -> TO   (THE PARENT'S TEMPLATE, finance_app.py not touched) 1 edit: three links
        in "Other pages" for the pages whose tiles leave his home (Order medicines, the Marg purchases hub, Stock milaan)
Usage: python make_s657.py <live root, e.g. /root> <out dir>   (writes <out>/portal/..., <out>/finance/...)"""
import hashlib, json, os, sys

FROM = {
    "portal/portal.py": "844166b11f6d62ece43b42fde8e11094",
    "portal/tile_grants.json": "025f8ab9a2691023148ccc6deeac4f50",
    "finance/sanjeevni_approvals.py": "bf86c8c8f30a7b223326f6f1d68fbb28",
    "finance/finance_ui/finance_approvals.html": "885f6f31571ae19d20b8cb065080ad0b",
}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:80])
    T[r] = T[r].replace(old, new, 1)


P = "portal/portal.py"
# ---- P1 the strip: four boxes; three again when the Expiry watch box hides itself (a login the expiry page refuses) -------------------
rep(P, r'''.strip{display:grid;grid-template-columns:minmax(320px,1.4fr) repeat(3,minmax(140px,1fr));gap:10px;margin:12px 0 4px}
''', r'''.strip{display:grid;grid-template-columns:minmax(320px,1.4fr) repeat(4,minmax(120px,1fr));gap:10px;margin:12px 0 4px}
@media(min-width:901px){.strip.c3{grid-template-columns:minmax(320px,1.4fr) repeat(3,minmax(140px,1fr))}}   /* S657 */
''')
# ---- P2 a box with something due is amber ------------------------------------------------------------------------------------------
rep(P, r'''.chipbox .cl{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
''', r'''.chipbox .cl{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.chipbox.due{border-color:var(--warn-ink);background:var(--warn-bg)}                       /* S657: something to move out */
.chipbox.due .cv{color:var(--warn-ink)}
''')
# ---- P3 a folded group opens in place (the owner's flow of 26-Oct): the sheet styles give way to the panel's ------------------------
rep(P, r'''.sheet{display:none;position:fixed;inset:0;z-index:20;background:var(--bg);overflow:auto;-webkit-overflow-scrolling:touch}
.sheet:target,.sheet.open{display:block}
body.sheet-open{overflow:hidden}
.sheetin{max-width:920px;margin:0 auto;padding:14px 16px 40px}
.sheet .back{display:inline-block;font-size:13px;color:var(--muted);text-decoration:none;border:1px solid var(--line);
 border-radius:10px;padding:7px 12px;margin:0 0 12px;background:var(--card)}
.sheet .back:hover{border-color:var(--blue);color:var(--ink)}
.sheeth{display:flex;align-items:center;gap:12px;margin:0 0 14px}
.sheeth .ic{font-size:30px;line-height:1}
.sheeth .nm{font-size:18px;font-weight:700;color:#fff}
.sheeth .ds{font-size:12px;color:var(--muted)}
@media(max-width:480px){.tile.grp .gn{margin-left:0}.sheetin{padding:10px 12px 36px}}
''', r'''/* S657 (the owner, 26-Oct-2026): a folded group opens IN PLACE, in a panel right below its row -- one open at a time; the tile
   again, or Close, shuts it. No page of its own and no Back. The next tiles close up the row (dense). */
.grid-groups{grid-auto-flow:row dense}
button.tile{font:inherit;color:inherit;text-align:left;cursor:pointer;width:100%}
.tile.grp .gv{display:inline-block;margin-left:3px;transition:transform .15s}
.tile.grp[aria-expanded="true"]{background:var(--card2);box-shadow:inset 0 0 0 2px var(--blue)}
.tile.grp[aria-expanded="true"] .gv{transform:rotate(90deg)}
.tile.grp:focus-visible,.gpanel .gclose:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
.gpanel{grid-column:1/-1;background:var(--card2);border:1px solid var(--blue);border-radius:12px;padding:10px 10px 12px}
.gpanel .gph{display:flex;align-items:center;gap:10px;margin:0 0 10px}
.gpanel .gph .ic{font-size:22px;line-height:1}
.gpanel .gph .nm{font-size:15px;font-weight:700;color:#fff}
.gpanel .gph .ds{font-size:11.5px;color:var(--muted)}
.gpanel .gclose{margin-left:auto;font:inherit;font-size:12.5px;color:var(--ink);background:var(--card);border:1px solid var(--line);
 border-radius:10px;padding:7px 14px;cursor:pointer;white-space:nowrap}
.gpanel .gclose:hover{border-color:var(--blue)}
.tile .who{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#93c5fd;margin-top:1px}
@media(max-width:480px){.tile.grp .gn{margin-left:0}.gpanel{padding:8px 8px 10px}}
@media(prefers-reduced-motion:reduce){.tile.grp .gv{transition:none}}
''')
# ---- P4 the Expiry watch box, beside 'Sanjeevni to approve' -----------------------------------------------------------------------
rep(P, r'''      <div class="cv" id="chipSanj">\u2013</div><div class="cl">Sanjeevni to approve</div></a>
''', r'''      <div class="cv" id="chipSanj">\u2013</div><div class="cl">Sanjeevni to approve</div></a>
    <a class="chipbox" id="chipExpBox" href="/finance/sanjeevni/expiry" target="_blank" rel="noopener" title="Expired, and what Marg stops selling on the 1st">
      <div class="cv" id="chipExp">\u2013</div><div class="cl">Expiry watch</div></a>
''')
# ---- P5 a tile may name whose screen it is (his Sanjeevni staff screens folder) --------------------------------------------------
rep(P, r'''        <div class="tx"><div class="nm">{{ t.name }}</div>
        <div class="ds"{% if t.review_counts %}''', r'''        <div class="tx"><div class="nm">{{ t.name }}</div>{% if t.who %}<div class="who">{{ t.who }}</div>{% endif %}
        <div class="ds"{% if t.review_counts %}''')
# ---- P6 the group tiles are buttons, each with its panel right after it; the full-screen sheets go -------------------------------
rep(P, r'''  {# S586 (D739): a folded group is ONE tile on the home grid; its tiles open as a submenu (a sheet, closed by Back).
     All groups folded (the owner): the group grid IS the home. Some folded (Dr Bhawna's Staff): the flat tiles come
     first and the folders after them -- the work someone does most sits highest (his ruling of 03-Sep). #}
  {%- macro groups(folded) -%}
  <div class="grid grid-groups">
  {% for label, items, is_folded, slug, gicon, gdesc in folded %}
      <a class="tile grp" href="#g-{{ slug }}" data-group="{{ slug }}">
        <div class="ic">{{ gicon }}</div>
        <div class="tx"><div class="nm">{{ label }}</div>
        <div class="ds">{{ gdesc }}</div></div>
        <span class="gn">{{ items|length }}</span>
      </a>
  {% endfor %}
  </div>
  {%- endmacro -%}''', r'''  {# S586 (D739): a folded group is ONE tile on the home grid. All groups folded (the owner): the group grid IS the home. Some folded
     (Dr Bhawna's Staff): the flat tiles come first and the folders after them -- the work someone does most sits highest (03-Sep).
     S657 (the owner, 26-Oct-2026): a group tile OPENS IN PLACE -- its panel sits right after it in the same grid, spans the row,
     and shuts again from the tile or its Close. No sheet, no Back. #}
  {%- macro groups(folded) -%}
  <div class="grid grid-groups" id="groupGrid">
  {% for label, items, is_folded, slug, gicon, gdesc in folded %}
      <button class="tile grp" type="button" id="gt-{{ slug }}" data-group="{{ slug }}" aria-expanded="false" aria-controls="g-{{ slug }}">
        <div class="ic">{{ gicon }}</div>
        <div class="tx"><div class="nm">{{ label }}</div>
        <div class="ds">{{ gdesc }}</div></div>
        <span class="gn">{{ items|length }}<span class="gv" aria-hidden="true">\u203a</span></span>
      </button>
      <div class="gpanel" id="g-{{ slug }}" role="region" aria-label="{{ label }}" hidden>
        <div class="gph"><span class="ic">{{ gicon }}</span><div><div class="nm">{{ label }}</div><div class="ds">{{ gdesc }}</div></div>
          <button class="gclose" type="button" data-close="{{ slug }}">Close</button></div>
        <div class="grid">
        {% for t in items %}{{ tile(t) }}{% endfor %}
        </div>
      </div>
  {% endfor %}
  </div>
  {%- endmacro -%}''')
rep(P, r'''  {% for label, items, is_folded, slug, gicon, gdesc in folded %}
  <section class="sheet" id="g-{{ slug }}" aria-label="{{ label }}">
    <div class="sheetin">
      <a class="back" href="#">\u2039 Home</a>
      <div class="sheeth"><span class="ic">{{ gicon }}</span><div><div class="nm">{{ label }}</div><div class="ds">{{ gdesc }}</div></div></div>
      <div class="grid">
      {% for t in items %}{{ tile(t) }}{% endfor %}
      </div>
    </div>
  </section>
  {% endfor %}
''', r'''  {# S657: the S586 sheets are gone -- each folder's panel is drawn beside its tile inside groups() #}
''')
# ---- P7 the accordion's script (replaces the sheet's hash script) -----------------------------------------------------------------
rep(P, r'''/* S586 (D739): a group tile opens its sheet by the address hash; Back (the browser's or the sheet's) closes it. */
(function(){
  function sync(){
    var h=(location.hash||'').replace(/^#/,''), open=null;
    document.querySelectorAll('.sheet').forEach(function(s){
      var on=(s.id===h); s.classList.toggle('open',on); if(on)open=s;
    });
    document.body.classList.toggle('sheet-open',!!open);
    if(open){open.scrollTop=0;}
  }
  window.addEventListener('hashchange',sync);
  sync();
})();
''', r'''/* S657 (the owner, 26-Oct-2026): a group tile opens its panel IN PLACE; one open at a time; the tile again, Close or Esc shuts it.
   The open folder is remembered for this tab only, so the home comes back as it was left. An old #g-<group> link still opens it. */
(function(){
  var KEY='s657_open';
  function tiles(){return Array.prototype.slice.call(document.querySelectorAll('.tile.grp[aria-controls]'));}
  function set(t,on){
    var p=document.getElementById(t.getAttribute('aria-controls'));
    t.setAttribute('aria-expanded',on?'true':'false'); if(p)p.hidden=!on;
    return p;
  }
  function keep(slug){try{if(slug)sessionStorage.setItem(KEY,slug);else sessionStorage.removeItem(KEY);}catch(e){}}
  function open(t,scroll){
    tiles().forEach(function(o){if(o!==t)set(o,false);});
    var p=set(t,true); keep(t.getAttribute('data-group'));
    if(scroll&&p&&p.scrollIntoView){setTimeout(function(){try{p.scrollIntoView({block:'nearest',behavior:'smooth'});}catch(e){p.scrollIntoView(false);}},30);}
  }
  function shut(t){set(t,false); keep(''); }
  tiles().forEach(function(t){
    t.addEventListener('click',function(){ if(t.getAttribute('aria-expanded')==='true')shut(t); else open(t,true); });
  });
  document.querySelectorAll('.gclose[data-close]').forEach(function(c){
    c.addEventListener('click',function(){var t=document.getElementById('gt-'+c.getAttribute('data-close')); if(t){shut(t); t.focus();}});
  });
  document.addEventListener('keydown',function(e){
    if(e.key!=='Escape')return;
    tiles().forEach(function(t){if(t.getAttribute('aria-expanded')==='true'){shut(t); t.focus();}});
  });
  var want=(location.hash||'').replace(/^#g-/,''), s=null;
  if(!want){try{want=sessionStorage.getItem(KEY)||'';}catch(e){want='';}}
  if(want){s=document.getElementById('gt-'+want); if(s)open(s,!!location.hash);}
})();
''')
# ---- P8 the Expiry watch box's number: one read of the expiry page's own count door; a refusal hides the box -------------------
rep(P, r'''     c=document.getElementById('chipRev');
     if(c&&typeof d.review!=='undefined')c.textContent=d.review;
   })
   .catch(function(){});
})();
''', r'''     c=document.getElementById('chipRev');
     if(c&&typeof d.review!=='undefined')c.textContent=d.review;
   })
   .catch(function(){});
})();
/* S657: the Expiry watch box (the owner, 26-Oct-2026) -- expired batches still in stock plus what Marg stops selling on the next 1st,
   the same two counts as his Needs-you line. A login the expiry page refuses (Dr Bhawna), or finance down: the box hides itself. */
(function(){
  var box=document.getElementById('chipExpBox'), c=document.getElementById('chipExp');
  if(!box||!c)return;
  function off(){box.hidden=true; if(box.parentNode&&box.parentNode.classList)box.parentNode.classList.add('c3');}
  fetch('/finance/sanjeevni/expiry/api/count',{credentials:'same-origin',cache:'no-store'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok){off();return;}
     var n=Number(d.n||0); c.textContent=n; box.classList.toggle('due',n>0);
     if(d.title)box.title=d.title;
   })
   .catch(off);
})();
''')
# ---- P9 the Sanjeevni group, folded (his login): his own work, and the staff's screens as a second folder -----------------------
rep(P, r'''    "Sanjeevni Medicos":    ("\U0001F48A", "Pharmacy \u2014 sale, stock, purchases, Marg"),
''', r'''    "Sanjeevni Medicos":    ("\U0001F48A", "Approve \u00b7 purchase orders \u00b7 pay \u00b7 stock"),   # S657: the folded face (his login)
''')
rep(P, r'''def _home_blocks(sections, folders):
    """[(label, items, folded, slug, icon, desc)] -- a folded group with ONE tile is drawn flat (no sheet for one)."""
    out = []
    for label, items in sections:
        folded = label in folders and len(items) > 1
        icon, desc = GROUP_META.get(label, ("\U0001F4C1", ""))
        out.append((label, items, folded, _group_slug(label), icon, desc))
    return out
''', r'''# S657 (the owner, 26-Oct-2026, mock-up 7YXMpfkuiU4awTHHkNSNfu): when the Sanjeevni group is FOLDED (his login), the staff's own screens --
# the ones he opens to see what they see -- become a second folder, each tile naming whose screen it is. Display only: a login that
# sees the group flat (every staff login) is drawn exactly as before; nothing is granted or hidden here.
S657_STAFF_SCREENS = {"Kal ka hisaab": "Darpan", "Medical sale check": "Bhati", "Amir ka kaam": "Amir",
                      "Aaj ki reports": "Shavez \u00b7 Shivani", "Vaapsi Desk": "Counter"}
S657_STAFF_GROUP = ("Sanjeevni staff screens", "\U0001F440", "What each person sees \u2014 Darpan, Bhati, Amir, Shavez")


def _home_blocks(sections, folders):
    """[(label, items, folded, slug, icon, desc)] -- a folded group with ONE tile is drawn flat (no panel for one)."""
    out = []
    for label, items in sections:
        folded = label in folders and len(items) > 1
        icon, desc = GROUP_META.get(label, ("\U0001F4C1", ""))
        if label == "Sanjeevni Medicos" and folded:                                         # S657
            mine = sorted([t for t in items if t["name"] not in S657_STAFF_SCREENS],
                          key=lambda t: t["name"] != "Sanjeevni Medicos")                    # his approvals page first
            staff = [dict(t, who=S657_STAFF_SCREENS[t["name"]]) for t in items if t["name"] in S657_STAFF_SCREENS]
            if mine and staff:
                out.append((label, mine, len(mine) > 1, _group_slug(label), icon, desc))
                sl, si, sd = S657_STAFF_GROUP
                out.append((sl, staff, len(staff) > 1, _group_slug(sl), si, sd))
                continue
        out.append((label, items, folded, _group_slug(label), icon, desc))
    return out
''')

# ---- tile_grants.json v40: his mask and his folder order ---------------------------------------------------------------------
G = "portal/tile_grants.json"
rep(G, '''    "Stock Check",
    "Vaapsi Desk"
   ],
   "folders": [
    "*"
   ]
  },''', '''    "Stock Check",
    "Vaapsi Desk"
   ],
   "mask": [
    "Daily Sale",
    "Order Medicines",
    "Marg Purchases",
    "Stock milaan"
   ],
   "groups": [
    "Patients",
    "Surgery",
    "Sanjeevni Medicos",
    "Docterz & clinic day",
    "Accounts & month-end",
    "Staff",
    "Calls & WhatsApp",
    "Assets & papers",
    "Personal",
    "System"
   ],
   "folders": [
    "*"
   ]
  },''')
rep(G, '''",\n "version": 39,''', ''' S657 v40 (26-Oct-2026, the Sanjeevni chat, the owner's mock-up 7YXMpfkuiU4awTHHkNSNfu): manoj's mask -- Daily Sale, Order Medicines, Marg Purchases and Stock milaan leave HIS home only (the pages stay live; the last three are linked from his approvals page, Other pages; Daily Sale sends him to his review console anyway) -- and his folder order as in the mock-up. Nobody else's tiles change.",\n "version": 40,''')

# ---- sanjeevni_approvals.py: the count door ---------------------------------------------------------------------------------
S = "finance/sanjeevni_approvals.py"
rep(S, '''    saved = expiry_watch.save_settings(con, request.form, u.get("user") or "owner")
    return expiry_watch.owner_page(con, saved=saved)
''', '''    saved = expiry_watch.save_settings(con, request.form, u.get("user") or "owner")
    return expiry_watch.owner_page(con, saved=saved)


@bp.route("/finance/sanjeevni/expiry/api/count", methods=["GET"])
def api_expiry_count():
    """S657 (the owner, 26-Oct-2026): the number on his home's Expiry watch box -- the two counts of his Needs-you line
    (expiry_watch.needs_you_lines, the same rule): expired batches still in stock, and batches Marg stops selling on the next 1st.
    Read only; the page itself is unchanged."""
    u, err = _require("checker")
    if err:
        return err
    import expiry_watch  # noqa: PLC0415
    today = expiry_watch.now_ist().date()
    run_, sec = expiry_watch.newest(_db())
    nxt = expiry_watch.ym_add(today.strftime("%Y-%m"), 1)
    on = "1-%s" % expiry_watch.MON[int(nxt[5:7])]
    if not run_:
        resp = jsonify(ok=True, n=0, expired=0, stops=0, stops_on=on, made="", title="No list yet")
    else:
        sec = expiry_watch.now_view(sec, today)
        ex = [x for x in sec.get("expired", []) if (x.get("units") or 0) > 0]
        soon = [x for x in sec.get("near", []) if x.get("expiry") and x["expiry"] <= nxt]
        resp = jsonify(ok=True, n=len(ex) + len(soon), expired=len(ex), stops=len(soon), stops_on=on,
                       made=str(run_.get("at") or "")[:16],
                       title="%d expired \\u00b7 %d stop%s selling on %s" % (len(ex), len(soon), "" if len(soon) == 1 else "", on))
    resp.headers["Cache-Control"] = "no-store"
    return resp
''')

# ---- finance_approvals.html: the three pages whose tiles leave his home, in Other pages -------------------------------------
H = "finance/finance_ui/finance_approvals.html"
rep(H, '''  <a class="ext" href="/finance/sanjeevni/expiry">Expiry watch ↗</a> ·
''', '''  <a class="ext" href="/finance/sanjeevni/expiry">Expiry watch ↗</a> ·
  <a class="ext" href="/finance/purchase/page/staff">Order medicines (the old page) ↗</a> ·
  <a class="ext" href="/finance/purchase/page/hub">Marg purchases hub ↗</a> ·
  <a class="ext" href="/finance/stockmatch">Stock milaan ↗</a> ·
''')

json.loads(T[G])
for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print(r, FROM[r][:8], "->", hashlib.md5(t.encode("utf-8")).hexdigest())
