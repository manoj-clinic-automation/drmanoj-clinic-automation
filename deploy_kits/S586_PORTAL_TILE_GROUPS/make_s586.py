#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s586.py -- S586_PORTAL_TILE_GROUPS (D739): the patcher for /root/portal/portal.py.

    python3 make_s586.py <portal.py at FROM> <out_dir>

FROM is the S579 TO, 963911cc41eac1ef98677b54e1a17291 (the live file at 18-Oct 13:xx IST; reproduced
byte-exact at the S326 open from the 18-Oct bundle's f8b059f6 + make_s579.py). Every edit is an anchor
found EXACTLY ONCE in those bytes; a miss or a double stops the run with nothing written (BUILD_NORM_v1).

WHAT CHANGES (display only -- no role, grant or gate changes in code; bhawna's are in tile_grants.json):
  1. Eight tiles retired (removed from TILES): UPI Sheet, Vehicle Tracking, Monthly Accounting,
     Revenue Reconciler, Case Pack - PC fallback, CC Statements -> Tally, CC Statement Saver, Inbox Janitor
     -- the owner's word, 15:38 IST 18-Oct. Their two config reads go with them (nothing else read them).
  2. Renewals opens the server's renewals page (/scanapp/renewals) instead of the Google sheet.
  3. GROUP_ORDER / _TILE_GROUP: ten groups -- Patients, Surgery, Calls & WhatsApp, Docterz & clinic day,
     Accounts & month-end, Staff, Assets & papers, Sanjeevni Medicos, Personal, System. The Sanjeevni tiles
     are not edited: they move together under one label. GROUP_META gives each group its tile face.
  4. Folders: tile_grants.json may carry per login "folders": ["*"] or a list of group labels, and
     "only": [tile names]. A folded group is drawn as ONE tile that opens its submenu (a sheet; the
     browser's back button closes it). "only" hides every other tile for that login (display only; a
     hidden tile is still gated by its own page). Absent -> the home is flat, exactly as today.
  5. The template's 'Clinic PC tools' chip row goes (the group no longer exists; Follow-up Tracker is a
     pc_only tile under Calls & WhatsApp).
"""
import sys, os, re, hashlib

FROM_MD5 = "963911cc41eac1ef98677b54e1a17291"
RETIRE = ["UPI Sheet", "Vehicle Tracking", "Monthly Accounting", "Revenue Reconciler",
          "Case Pack \\u00b7 PC fallback", "CC Statements \\u2192 Tally", "CC Statement Saver", "Inbox Janitor"]

NEW_GROUPS = '''GROUP_ORDER = ["Patients", "Surgery", "Calls & WhatsApp", "Docterz & clinic day",
               "Accounts & month-end", "Staff", "Assets & papers", "Sanjeevni Medicos",
               "Personal", "System"]

# S586 (D739, 18-Oct-2026): the face of each group when a login has it FOLDED -- one tile that opens
# the group's tiles as a submenu. Display only.
GROUP_META = {
    "Patients":             ("\\U0001FA7B", "Records \\u00b7 checks \\u00b7 slips \\u00b7 pending reports"),
    "Surgery":              ("\\U0001FA78", "Case pack \\u00b7 surgery cases"),
    "Calls & WhatsApp":     ("\\U0001F4DE", "Console \\u00b7 tracker \\u00b7 templates \\u00b7 reviews"),
    "Docterz & clinic day": ("\\U0001F3E6", "Collections \\u00b7 morning match \\u00b7 physio \\u00b7 petty"),
    "Accounts & month-end": ("\\U0001F4E6", "Packs \\u00b7 month checklist \\u00b7 renewals"),
    "Staff":                ("\\U0001F465", "Attendance \\u00b7 register \\u00b7 salary \\u00b7 ledger"),
    "Assets & papers":      ("\\U0001F5C2\\uFE0F", "Asset register \\u00b7 scan a bill \\u00b7 forms"),
    "Sanjeevni Medicos":    ("\\U0001F48A", "Pharmacy \\u2014 sale, stock, purchases, Marg"),
    "Personal":             ("\\U0001FAC0", "RxGuard \\u00b7 GutLog \\u00b7 FitLog"),
    "System":               ("\\u2699\\uFE0F", "Board \\u00b7 users \\u00b7 clinic PCs"),
}

_TILE_GROUP = {
    # Patients
    "Patient records": "Patients", "Check karein": "Patients", "Report baaki": "Patients",
    "OPD & X-ray/Proc Slips": "Patients", "Vitals & Plan": "Patients", "Procedures & prices": "Patients",
    # Surgery
    "Surgical Case Pack": "Surgery", "Surgery cases": "Surgery",
    # Calls & WhatsApp (Follow-up Tracker is pc_only: shown on the clinic PC alone, as before)
    "Clinic Gist": "Calls & WhatsApp", "Call Console": "Calls & WhatsApp", "Call Tracker": "Calls & WhatsApp",
    "Call ke baad": "Calls & WhatsApp", "Send WhatsApp": "Calls & WhatsApp",
    "Follow-up WhatsApps": "Calls & WhatsApp", "WhatsApp Approvals": "Calls & WhatsApp",
    "GMB Review Assist": "Calls & WhatsApp", "Follow-up Tracker": "Calls & WhatsApp",
    # Docterz & clinic day
    "Docterz Revenue": "Docterz & clinic day", "Docterz daily collection": "Docterz & clinic day",
    "Daily Collection": "Docterz & clinic day", "Clinic": "Docterz & clinic day",
    "Morning match": "Docterz & clinic day", "Physiotherapy": "Docterz & clinic day",
    "Petty book": "Docterz & clinic day", "Bhati aaj": "Docterz & clinic day",
    # Accounts & month-end
    "Month-end packs": "Accounts & month-end", "Mahine ka kaam": "Accounts & month-end",
    "Renewals": "Accounts & month-end",
    # Staff -- S198_P1: one connected family (attendance -> salary; ledger advances recovered at the close)
    "Attendance": "Staff", "Staff Register": "Staff", "Meri attendance": "Staff",
    "Salary \\u2014 approve & lock": "Staff", "Staff Ledger": "Staff",
    "Staff Ledger \\u2014 Entry": "Staff",
    # Assets & papers
    "Asset Register": "Assets & papers", "Scan Purchase": "Assets & papers", "Forms & Downloads": "Assets & papers",
    # Sanjeevni Medicos -- the pharmacy chat's tiles, unchanged, under one label (D739)
    "Sanjeevni Medicos": "Sanjeevni Medicos", "Daily Sale": "Sanjeevni Medicos", "Kal ka hisaab": "Sanjeevni Medicos",
    "Medical sale check": "Sanjeevni Medicos", "Stock milaan": "Sanjeevni Medicos", "Stock Check": "Sanjeevni Medicos",
    "Purchase orders": "Sanjeevni Medicos", "Vaapsi Desk": "Sanjeevni Medicos", "Corrections": "Sanjeevni Medicos",
    "Marg Purchases": "Sanjeevni Medicos", "Order Medicines": "Sanjeevni Medicos", "Vendor payments": "Sanjeevni Medicos",
    "Amir ka kaam": "Sanjeevni Medicos", "Aaj ki reports": "Sanjeevni Medicos",
    # Personal
    "RxGuard": "Personal", "GutLog": "Personal", "FitLog": "Personal",
    # System
    "System Board": "System", "Manage Users": "System", "Clinic PCs": "System",
}
# Every tile must map to a known group (fail loud at import, not silently mis-place).
for _t in TILES:
    assert _t["name"] in _TILE_GROUP, "ungrouped tile: " + _t["name"]
    _t["group"] = _TILE_GROUP[_t["name"]]
assert set(_TILE_GROUP.values()) <= set(GROUP_ORDER), "group not in GROUP_ORDER"
assert set(GROUP_META) == set(GROUP_ORDER), "a group without a face"
'''

NEW_VIS = '''    out = []
    only = _only_for(user)                                                  # S586: a login's "only" list (display only)
    for _g in group_order:
        _items = [t for t in TILES
                  if t.get("group") == _g
                  and (role in t["roles"] or t["name"] in extra)
                  and t["name"] not in mask
                  and (only is None or t["name"] in only)
                  and (not t.get("pc_only") or pc)
                  and (t["name"] != S497_TILE or _s497_tile_on(role))]      # S497: off for staff until he turns it on
        if _items:
            out.append((_g, _items))
    return out


# ---- S586_PORTAL_TILE_GROUPS (D739) -- folders and "only", read from tile_grants.json; display only ---------------
def _only_for(user):
    """The login's "only" list from tile_grants.json, or None (= no narrowing). Never raises."""
    try:
        g = _tile_grants() or {}
        lst = ((g.get("users") or {}).get(user) or {}).get("only")
        if isinstance(lst, list) and lst:
            return set(str(x) for x in lst)
    except Exception:
        pass
    return None


def _folders_for(user):
    """Which groups this login sees folded into one tile each: "*" = every group; a list = those; none = flat."""
    try:
        g = _tile_grants() or {}
        lst = ((g.get("users") or {}).get(user) or {}).get("folders")
        if lst == "*" or (isinstance(lst, list) and "*" in lst):
            return set(GROUP_ORDER)
        if isinstance(lst, list):
            return set(str(x) for x in lst) & set(GROUP_ORDER)
    except Exception:
        pass
    return set()


def _group_slug(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _home_blocks(sections, folders):
    """[(label, items, folded, slug, icon, desc)] -- a folded group with ONE tile is drawn flat (no sheet for one)."""
    out = []
    for label, items in sections:
        folded = label in folders and len(items) > 1
        icon, desc = GROUP_META.get(label, ("\\U0001F4C1", ""))
        out.append((label, items, folded, _group_slug(label), icon, desc))
    return out
# ---- S586 end -------------------------------------------------------------------------------------------------------
'''

NEW_RENDER = '''    blocks = _home_blocks(s444.get("sections", sections), _folders_for(who["user"] if who else ""))   # S586 (D739)
    return render_template_string(PORTAL_HTML,
                                  sections=s444.get("sections", sections), blocks=blocks,
                                  sso=_sso_ready(), who=who, role=role,
                                  pc=pc, s444_nowork=s444.get("nowork", False))
'''

TILE_MACRO = '''  {%- macro tile(t) -%}
    {% if t.live %}
      <a class="tile" href="{{ t.url }}" target="_blank" rel="noopener"{% if t.clinic_meta %} data-clinic-tile{% endif %}>
        <div class="ic">{{ t.icon }}</div>
        <div class="tx"><div class="nm">{{ t.name }}</div>
        <div class="ds"{% if t.review_counts %} data-review-counts{% endif %}{% if t.gist %} data-gist-summary{% endif %}{% if t.sanjeevni_counts %} data-sanjeevni-counts{% endif %}{% if t.daily_sale_counts %} data-daily-sale-counts{% endif %}{% if t.packs_counts %} data-packs-counts{% endif %}>{{ t.desc }}</div></div>
      </a>
    {% else %}
      <div class="tile held" title="Not yet hosted">
        <div class="ic">{{ t.icon }}</div>
        <div class="tx"><div class="nm">{{ t.name }}</div>
        <div class="ds">{{ t.desc }}</div></div>
        <span class="tag h">MANUAL</span>
      </div>
    {% endif %}
  {%- endmacro -%}
  {# S586 (D739): a folded group is ONE tile on the home grid; its tiles open as a submenu (a sheet, closed by Back).
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
  {%- endmacro -%}
  {% set folded = blocks|selectattr(2)|list %}
  {% set all_folded = folded and (folded|length == blocks|length) %}
  {% if all_folded %}{{ groups(folded) }}{% endif %}
  {% for label, items, is_folded, slug, gicon, gdesc in blocks %}
  {% if not is_folded %}
  <div class="kick">{{ label }}</div>
  <div class="grid">
  {% for t in items %}{{ tile(t) }}{% endfor %}
  </div>
  {% endif %}
  {% endfor %}
  {% if folded and not all_folded %}<div class="kick">More</div>{{ groups(folded) }}{% endif %}
  {% for label, items, is_folded, slug, gicon, gdesc in folded %}
  <section class="sheet" id="g-{{ slug }}" aria-label="{{ label }}">
    <div class="sheetin">
      <a class="back" href="#">\\u2039 Home</a>
      <div class="sheeth"><span class="ic">{{ gicon }}</span><div><div class="nm">{{ label }}</div><div class="ds">{{ gdesc }}</div></div></div>
      <div class="grid">
      {% for t in items %}{{ tile(t) }}{% endfor %}
      </div>
    </div>
  </section>
  {% endfor %}
  <div class="foot">
'''

NEW_CSS = '''@media(max-width:480px){.wrap{padding:10px 12px 36px}
 .grid{grid-template-columns:repeat(2,1fr)}
 .tile{flex-direction:column;align-items:flex-start;gap:6px;min-height:88px}
 .tag{margin-left:0}}
/* S586 (D739): group tiles and their submenu sheets */
.grid-groups{margin:4px 0 14px}
.tile.grp{border-color:var(--blue);position:relative}
.tile.grp .gn{margin-left:auto;font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px;
 background:rgba(59,130,246,.18);color:#93c5fd;white-space:nowrap;font-variant-numeric:tabular-nums}
.sheet{display:none;position:fixed;inset:0;z-index:20;background:var(--bg);overflow:auto;-webkit-overflow-scrolling:touch}
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
</style></head><body>
"""

PORTAL_HTML = HOME_HEAD + """
'''

NEW_JS = '''/* S586 (D739): a group tile opens its sheet by the address hash; Back (the browser's or the sheet's) closes it. */
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
/* S198_P1: the 46px floating back-to-top'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def once(s, needle, what):
    n = s.count(needle)
    if n != 1:
        sys.exit("ANCHOR %s: found %d times, need exactly 1 -- nothing written" % (what, n))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out_dir = sys.argv[1], sys.argv[2]
    raw = open(src, "rb").read()
    if md5(raw) != FROM_MD5:
        sys.exit("FROM is %s, expected %s -- not the file this patcher was built on" % (md5(raw)[:8], FROM_MD5[:8]))
    s = raw.decode("utf-8")
    edits = 0

    # 1. retire eight tiles (each block = from its "    {" line to its "}," line, inclusive)
    for nm in RETIRE:
        key = '"name": "%s"' % nm
        once(s, key, "tile " + nm)
        k = s.find(key)
        a = s.rfind("\n    {", 0, k) + 1
        b = s.find("},\n", k) + 3
        blk = s[a:b]
        once(s, blk, "block " + nm)
        s = s.replace(blk, "", 1); edits += 1
    cfg = 'CC_SAVER_URL      = _cfg_get("CC_SAVER_URL")\nINBOX_JANITOR_URL = _cfg_get("INBOX_JANITOR_URL")\n'
    once(s, cfg, "config reads"); s = s.replace(cfg, "", 1); edits += 1
    for name in ("CC_SAVER_URL", "INBOX_JANITOR_URL"):
        live = [l for l in s.split("\n") if name in l and not l.strip().startswith("#")]
        if live:
            sys.exit("%s still read somewhere: %r" % (name, live[:2]))

    # 2. Renewals -> the server
    old = ('    {"icon": "\\U0001F5D3\\uFE0F", "name": "Renewals",\n'
           '     "desc": "Master sheet \\u2014 every renewal & due date", "live": True,\n'
           '     "url": "https://docs.google.com/spreadsheets/d/1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E",\n'
           '     "roles": ["doctor"]},\n')
    new = ('    {"icon": "\\U0001F5D3\\uFE0F", "name": "Renewals",\n'
           '     "desc": "Every renewal & due date \\u2014 on the server", "live": True,   # S586 (D739): the sheet retired\n'
           '     "url": "/scanapp/renewals",\n'
           '     "roles": ["doctor"]},\n')
    once(s, old, "Renewals tile"); s = s.replace(old, new, 1); edits += 1

    # 3. the groups
    a = 'GROUP_ORDER = ["Clinic", "Staff", "Money & Accounts", "Personal & Health",\n               "Clinic PC tools", "Admin"]\n'
    b = 'assert set(_TILE_GROUP.values()) <= set(GROUP_ORDER), "group not in GROUP_ORDER"\n'
    once(s, a, "GROUP_ORDER"); once(s, b, "group assert")
    i = s.find(a); j = s.find(b, i) + len(b)
    s = s[:i] + NEW_GROUPS + s[j:]; edits += 1

    # 4. _visible_sections + the folder helpers
    old_vis = ('    out = []\n'
               '    for _g in group_order:\n'
               '        _items = [t for t in TILES\n'
               '                  if t.get("group") == _g\n'
               '                  and (role in t["roles"] or t["name"] in extra)\n'
               '                  and t["name"] not in mask\n'
               '                  and (not t.get("pc_only") or pc)\n'
               '                  and (t["name"] != S497_TILE or _s497_tile_on(role))]      # S497: off for staff until he turns it on\n'
               '        if _items:\n'
               '            out.append((_g, _items))\n'
               '    return out\n')
    once(s, old_vis, "_visible_sections loop"); s = s.replace(old_vis, NEW_VIS, 1); edits += 1

    # 5. home() passes blocks
    old_r = ('    return render_template_string(PORTAL_HTML,\n'
             '                                  sections=s444.get("sections", sections),\n'
             '                                  sso=_sso_ready(), who=who, role=role,\n'
             '                                  pc=pc, s444_nowork=s444.get("nowork", False))\n')
    once(s, old_r, "home render"); s = s.replace(old_r, NEW_RENDER, 1); edits += 1

    # 6. the template: sections loop -> group tiles + sheets
    ts = "  {% for label, items in sections %}\n  <div class=\"kick\">{{ label }}</div>\n  {% if label == 'Clinic PC tools' %}\n"
    te = "  {% endfor %}\n  </div>\n  {% endif %}\n  {% endfor %}\n  <div class=\"foot\">\n"
    once(s, ts, "template start"); once(s, te, "template end")
    i = s.find(ts); j = s.find(te, i) + len(te)
    s = s[:i] + TILE_MACRO + s[j:]; edits += 1

    # 7. CSS
    old_css = ('@media(max-width:480px){.wrap{padding:10px 12px 36px}\n'
               ' .grid{grid-template-columns:repeat(2,1fr)}\n'
               ' .tile{flex-direction:column;align-items:flex-start;gap:6px;min-height:88px}\n'
               ' .tag{margin-left:0}}\n'
               '</style></head><body>\n"""\n\nPORTAL_HTML = HOME_HEAD + """\n')
    once(s, old_css, "home css end"); s = s.replace(old_css, NEW_CSS, 1); edits += 1

    # 8. JS
    old_js = "/* S198_P1: the 46px floating back-to-top"
    once(s, old_js, "toTop js"); s = s.replace(old_js, NEW_JS, 1); edits += 1

    # 9. the mini chip row CSS is now unused -> leave in place? No: it is dead. Remove the four rules.
    mini = ('.mini{display:flex;flex-wrap:wrap;gap:8px}\n'
            '.mchip{font-size:12px;color:var(--muted);background:var(--card2);\n'
            ' border:1px solid var(--line);border-radius:16px;padding:6px 12px;text-decoration:none;display:inline-block}\n'
            'a.mchip:hover{border-color:var(--blue);color:var(--ink)}\n'
            '.mchip.held{opacity:.55}\n')
    once(s, mini, "mini css"); s = s.replace(mini, "", 1); edits += 1

    if "import re\n" not in s:
        once(s, "import os\nimport json\n", "imports"); s = s.replace("import os\nimport json\n", "import os\nimport re\nimport json\n", 1); edits += 1

    out = s.encode("utf-8")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "portal.py")
    open(p, "wb").write(out)
    print("portal.py  %s -> %s  (%d counted edits, %d -> %d bytes)" % (FROM_MD5[:8], md5(out)[:8], edits, len(raw), len(out)))
    print(md5(out))


if __name__ == "__main__":
    main()
