#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s890.py -- S890_RENEWALS_ONE_LIST: the anchored patches to asset_register.py (the Scan App's) and portal.py (the parent's).

    python3 make_s890.py <asset_register.py FROM> <portal.py FROM> <out folder>

Every anchor must occur EXACTLY once in the file it is applied to, or nothing is written (F-472: patches from the real bytes).
Prints the md5 (8) of each FROM and TO. The installer runs the same script on the live files after checking their pins.
"""
import hashlib
import os
import sys

MOUNT = '''

# --- S890_RENEWALS_ONE_LIST begin -- D1017 (18-Nov-2026): every renewal on ONE list on the server (renewals_one.py) ---
# Guarded: if renewals_one.py is absent or cannot load, this app runs exactly as before -- the /renewals page draws its old
# sections only (the two s890_* globals stay undefined and the template skips them). Built by the parent chat on a PLANNED line;
# the file and its tables are this project's (the Scan App's). The staff-document rows of `expiries` reach the page through it
# (F-1493); the default lead time above is 45 (his ruling), an asset row with its own threshold keeps it.
try:
    import renewals_one as _renewals_one
    _renewals_one.init(_sys.modules[__name__])
except Exception as _ex_s890:                                        # noqa: BLE001
    print("renewals_one NOT mounted: %s" % _ex_s890, file=_sys.stderr)
# --- S890_RENEWALS_ONE_LIST end ---
'''

AR_EDITS = (
    ("THRESHOLD_DEFAULT = 60  # days; per-expiry override supported",
     "THRESHOLD_DEFAULT = 45  # days; per-expiry override supported -- S890 (D1017): 45 for every renewal but a passport (was 60)"),
    ("{% set d664w = d664_warranty_card() if d664_warranty_card is defined else '' %}{% set s571b = s571_battery_card(show_all) if s571_battery_card is defined else '' %}{% if not ordered and not consum and not d664w and not s571b %}",
     "{% set d664w = d664_warranty_card() if d664_warranty_card is defined else '' %}{% set s571b = s571_battery_card(show_all) if s571_battery_card is defined else '' %}"
     "{% set s890t = s890_top(show_all) if s890_top is defined else '' %}{% set s890s = s890_staff(show_all) if s890_staff is defined else '' %}"
     "{% if not ordered and not consum and not d664w and not s571b and not s890t and not s890s %}"),
    ("{% endif %}\n{% for ent_name, g in ordered %}",
     "{% endif %}\n{{ s890t }}\n{% for ent_name, g in ordered %}"),
    ("{{ d664w }}\n{{ s571b }}",
     "{{ d664w }}\n{{ s890s }}\n{{ s571b }}"),
)

PORTAL_EDITS = (
    # the folder tile: one bold line per inside tile (his word 21:56 18-Nov), the Renewals line carries the red count
    ('        <div class="ds">{{ gdesc }}</div></div>\n        <span class="gn">',
     '        <div class="gl">{% for t in items %}<div class="gll"{% if t.name == \'Renewals\' %} data-s890-renewals{% endif %}>{{ t.name }}</div>{% endfor %}</div></div>\n'
     '        <span class="gn">'),
    (".tile.grp{border-color:var(--blue);position:relative}",
     ".tile.grp{border-color:var(--blue);position:relative}\n"
     ".tile.grp .gl{margin-top:5px;display:flex;flex-direction:column;gap:3px}\n"
     ".tile.grp .gll{font-size:13px;font-weight:700;color:var(--ink);line-height:1.35;text-align:left}\n"
     ".tile.grp .gll .s890n{display:inline-block;margin-left:6px;min-width:18px;padding:0 6px;border-radius:999px;background:#b23b3b;color:#fff;font-size:11px;line-height:18px;text-align:center}"),
    ("/* S657: the Expiry watch box",
     "/* S890 (D1017): the red count on the Renewals line of the folder tile -- due within its lead time or overdue, read from the one list\n"
     "   on the server. Not signed in to the scan app, or the scan app down: no count, the tile is as before. */\n"
     "(function(){\n"
     "  var ls=document.querySelectorAll('[data-s890-renewals]');\n"
     "  if(!ls.length)return;\n"
     "  fetch('/scanapp/renewals/one/api/count',{credentials:'same-origin',cache:'no-store'})\n"
     "   .then(function(r){return r.ok?r.json():null;})\n"
     "   .then(function(d){\n"
     "     if(!d||!d.ok||d.n===null||d.n===undefined)return;\n"
     "     var n=Number(d.n||0)+Number(d.mails||0);\n"
     "     if(!n)return;\n"
     "     for(var i=0;i<ls.length;i++){var s=document.createElement('span');s.className='s890n';s.textContent=n;ls[i].appendChild(s);}\n"
     "   })\n"
     "   .catch(function(){});\n"
     "})();\n"
     "/* S657: the Expiry watch box"),
)


def md5(b):
    return hashlib.md5(b).hexdigest()[:8]


def patch(path, edits, name):
    src = open(path, encoding="utf-8", newline="").read()
    out = src
    for i, (old, new) in enumerate(edits, 1):
        n = out.count(old)
        if n != 1:
            raise SystemExit("make_s890: %s anchor %d occurs %d times (must be 1) -- nothing written" % (name, i, n))
        out = out.replace(old, new, 1)
    return src, out


def main(ar_from, portal_from, outdir):
    os.makedirs(outdir, exist_ok=True)
    src, out = patch(ar_from, AR_EDITS, "asset_register.py")
    out = out.rstrip("\n") + "\n" + MOUNT
    p = os.path.join(outdir, "asset_register.py")
    open(p, "w", encoding="utf-8", newline="").write(out)
    print("asset_register.py  %s -> %s  (%d anchors + mount block)" % (md5(src.encode()), md5(out.encode()), len(AR_EDITS)))
    src, out = patch(portal_from, PORTAL_EDITS, "portal.py")
    p = os.path.join(outdir, "portal.py")
    open(p, "w", encoding="utf-8", newline="").write(out)
    print("portal.py          %s -> %s  (%d anchors)" % (md5(src.encode()), md5(out.encode()), len(PORTAL_EDITS)))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
