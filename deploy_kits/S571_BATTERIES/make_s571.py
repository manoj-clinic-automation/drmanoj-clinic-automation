#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s571.py -- S571_BATTERIES: the two edited scan-app files rebuilt from the pinned live bytes (S568's TO pins); the new
batteries.py is the kit's own file (copied beside them). clinic_papers.py is read, never edited (no Renewals or month wiring
needed it); packs.py, stationery.py, asset_machine.py and scanner_widget.js are never touched.

    python3 make_s571.py <dir with the live sorting_desk.py, asset_register.py> <out dir>

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the counted
number of times. Every byte of each built file comes from the live file plus these edits."""
import hashlib, os, shutil, sys

FROM = {"sorting_desk.py": "695ba90b4b3652f0e087f29b7c25d706",
        "asset_register.py": "e5356e0c75f564085b20a059f76a4b48"}
HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================================================ sorting_desk.py
SD_EDITS = [
    # SD1 -- the mark
    ('''STOCK_FIX = "S568_FIX1"       # S568 FIX1 (K1 CORRECTION 3): "Add a paper from a file" takes a PDF or a photo only
''',
     '''STOCK_FIX = "S568_FIX1"       # S568 FIX1 (K1 CORRECTION 3): "Add a paper from a file" takes a PDF or a photo only
BATTERY = "S571"              # S571_BATTERIES: the switch batteries.on; a battery's bill offered on the desk; the payer pre-selects
''', 1),
    # SD2 (item 6, R1 C2) -- the switch, one entry appended to SWITCHES
    ('''            ("stationery.issue_on", "Stationery diya for managers"))                    # S568 item 4 (absent = OFF)
''',
     '''            ("stationery.issue_on", "Stationery diya for managers"),                    # S568 item 4 (absent = OFF)
            ("batteries.on", "Batteries for Shavez"))                                   # S571 item 6 (absent = OFF)
''', 1),
    # SD3 (item 6, R1 C2) -- its state, one key in switch_states()
    ('''            "stationery.issue_on": (_setting(db, "stationery.issue_on", "off") or "").strip().lower() == "on"}      # S568
''',
     '''            "stationery.issue_on": (_setting(db, "stationery.issue_on", "off") or "").strip().lower() == "on",      # S568
            "batteries.on": (_setting(db, "batteries.on", "off") or "").strip().lower() == "on"}      # S571
''', 1),
    # SD4 (item 3, R1 note 12) -- paper_json's tail: the battery offer / link / pre-select
    ('''            **_s560_paper(db, b, owner, rd, today), **_s568_paper(db, b, owner, rd)}      # S560: paid state ...; S568: the stationery panel
''',
     '''            **_s560_paper(db, b, owner, rd, today), **_s568_paper(db, b, owner, rd),      # S560: paid state ...; S568: the stationery panel
            **_s571_paper(db, b, owner)}                                                     # S571: the battery offer (nothing without batteries.py)
''', 1),
    # SD5 (item 3) -- the offer's box on the desk, under the stationery panel
    ('''<div class=box id=st568 style="display:none"></div></div>
''',
     '''<div class=box id=st568 style="display:none"></div><div class=box id=bt571 style="display:none"></div></div>
''', 1),
    # SD6 (item 3) -- a paper opened: the payer's pre-select (browser only)
    ('''s560init(j);s568init(j);draw();drawList();});}
''',
     '''s560init(j);s568init(j);s571init(j);draw();drawList();});}
''', 1),
    # SD7 (item 3) -- painted
    (''' s560paint(j);s568paint(j);paint2();}
''',
     ''' s560paint(j);s568paint(j);s571paint(j);paint2();}
''', 1),
    # SD8 (item 3) -- the desk script's S571 part: one tap links (its own POST, never the desk's Save)
    ('''$('readbox').addEventListener('toggle',function(){S.readopen=$('readbox').open;cue();});
''',
     '''// S571_BATTERIES: "Battery fitted at <place> on <date> — this bill?" -- one tap links it (its own POST; the paper is never changed);
// a linked paper still waiting: "Where does it go?" pre-selected from the place's payer, in the browser only -- nothing is saved until Save
function s571init(j){var b=j.bat||null;S.pre571='';if(b&&b.pre&&!S.dest){S.dest=b.pre;S.pre571=b.pre;}}
function s571paint(j){var x=$('bt571');if(!x){return;}var b=j.bat||null,h='';
 if(b&&b.linked){h+='<div class=paidline id=bt571linked>'+esc(b.linked)+((S.pre571&&S.dest==S.pre571)?' “'+esc(C.names[S.pre571]||S.pre571)+'” is pre-chosen from the place’s payer ('+esc(b.payer||'')+') — nothing is saved until Save.':'')+'</div>';}
 ((b&&b.offers)||[]).forEach(function(o){h+='<div class=bt571o>'+esc(o.text)+' <button type=button class=b data-bt571="'+o.fit+'">Yes — link it</button></div>';});
 x.innerHTML=h;x.style.display=h?'flex':'none';}
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-bt571]'):null;if(!t||!S.cur||!S.cur.bat){return;}var j=S.cur;
 jpost(j.bat.link,{fit:parseInt(t.getAttribute('data-bt571'),10),paper:j.id,as:'bill'}).then(function(r){if(!r.ok){$('err').textContent=r.error||'Not linked.';return;}$('savednote').textContent=r.message;openPaper(j.id);});});
$('readbox').addEventListener('toggle',function(){S.readopen=$('readbox').open;cue();});
''', 1),
    # SD9 (item 3) -- paper_json's S571 part
    ('''# --- S568_STATIONERY_STOCK end ---
''',
     '''# --- S568_STATIONERY_STOCK end ---


# ---------------------------------------------------------------------------------------------- S571_BATTERIES (D730 (1))
# A B.L. Computers / Jasoria paper on the desk: "Battery fitted at <place> on <date> — this bill?" when that place's battery has its
# bill awaited (batteries.desk_offer: the desk's visibility rules; an owner-only place to the owner only). Linking is its own POST
# (/batteries/link) and never writes the paper (D664). A linked paper not sorted yet: the place's payer pre-selects "Where does it
# go?" in the browser only (clinic -> Clinic equipment, NK Pathology -> NK Pathology, owner -> Personal; 'to confirm' -> nothing).
def _s571_bt():
    """batteries.py, when it is mounted; else None (the offer then gives nothing)."""
    m = sys.modules.get("batteries")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _s571_paper(db, b, owner):
    bt = _s571_bt()
    if bt is None or _lane(b) == "pharmacy":
        return {}
    try:
        return bt.desk_offer(db, b, owner, current_dest(b))
    except Exception as ex:                                          # noqa: BLE001
        print("S571 offer: %s" % ex, file=sys.stderr)
        return {}
''', 1),
]

# ============================================================================================ asset_register.py
AR_EDITS = [
    # AR1 (item 4, R1 B1) -- the Renewals page: the Batteries card counts toward 'Nothing due'
    ('''{% set d664w = d664_warranty_card() if d664_warranty_card is defined else '' %}{% if not ordered and not consum and not d664w %}''',
     '''{% set d664w = d664_warranty_card() if d664_warranty_card is defined else '' %}{% set s571b = s571_battery_card(show_all) if s571_battery_card is defined else '' %}{% if not ordered and not consum and not d664w and not s571b %}''', 1),
    # AR2 (item 4, R1 B1) -- ONE hook: the card, next to d664's warranty card
    ('''{{ d664w }}
''',
     '''{{ d664w }}
{{ s571b }}
''', 1),
    # AR3 (item 1, R1 note 11) -- the one menu: Batteries after Machines
    ('''    out += [("assets_list", "Machines", url_for("assets_list")), ("renewals", "Renewals", url_for("renewals")),
''',
     '''    out += [("assets_list", "Machines", url_for("assets_list"))] + _s571_menu(r) + [("renewals", "Renewals", url_for("renewals")),      # S571
''', 1),
    # AR4 (R1 note 11) -- the mark and the guarded mount, after the S568 block
    ('''# --- S568_STATIONERY_STOCK end ---
''',
     '''# --- S568_STATIONERY_STOCK end ---


# --- S571_BATTERIES begin -- D730 (1): battery places, their history, reminders on Renewals (batteries.py) (16-Oct-2026) ---
# Guarded: if batteries.py is absent or cannot load, this app runs exactly as before -- the menu item, the Renewals card and the desk's
# offer give nothing.
BATTERY_S571 = "S571"


def _s571_menu(role):
    """The one menu's Batteries item (batteries.menu_items): the owner; a manager while batteries.on is ON."""
    try:
        _m = _sys.modules.get("batteries")
        if _m is not None and getattr(_m, "MOUNTED", False):
            return list(_m.menu_items(role))
    except Exception as _ex:                                      # noqa: BLE001
        print("S571 menu: %s" % _ex, file=_sys.stderr)
    return []


try:
    import batteries as _batteries
    _batteries.init(_sys.modules[__name__])
except Exception as _ex_s571:                                  # noqa: BLE001
    print("batteries NOT mounted: %s" % _ex_s571, file=_sys.stderr)
# --- S571_BATTERIES end ---
''', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(name, text, edits):
    n = 0
    for i, (old, new, cnt) in enumerate(edits, 1):
        got = text.count(old)
        if got != cnt:
            raise SystemExit("REFUSED: %s edit %d: the anchor is found %d times, not %d:\n  %s" % (name, i, got, cnt, old[:160]))
        text = text.replace(old, new)
        n += 1
    return text, n


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    os.makedirs(out, exist_ok=True)
    plan = {"sorting_desk.py": SD_EDITS, "asset_register.py": AR_EDITS}
    built = {}
    for f, edits in plan.items():
        raw = open(os.path.join(src, f), "rb").read()
        if md5(raw) != FROM[f]:
            raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
        text, n = apply(f, raw.decode("utf-8"), edits)
        built[f] = (text.encode("utf-8"), n)
    for f, (b, n) in built.items():
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        print("%-18s %s -> %s  (%d counted edit%s, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n, "" if n == 1 else "s"))
    shutil.copyfile(os.path.join(HERE, "batteries.py"), os.path.join(out, "batteries.py"))
    print("%-18s (new)     -> %s  (the kit's own file)" % ("batteries.py", md5(open(os.path.join(out, "batteries.py"), "rb").read())[:8]))


if __name__ == "__main__":
    main()
