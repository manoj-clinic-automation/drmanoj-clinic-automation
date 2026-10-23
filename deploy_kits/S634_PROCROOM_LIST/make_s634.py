#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s634.py -- S634_PROCROOM_LIST (D773 Kit 1): rebuilds sorting_desk.py's and asset_register.py's TO bytes from the pinned FROM
bytes by exact, counted edits, and places the kit's NEW procroom.py beside them.

    python3 -B make_s634.py <FROM folder> <TO folder>

Each edit's anchor must occur exactly ONCE in the FROM file; the FROM md5 must equal the pin; the TO md5 is printed.

The owner, S342 (04:39-06:32 IST 23-Oct-2026), D773: one product list, his; every slip line in its own place; rates his only. His
"okay to start" on the S345 mock-ups, 08:31 IST 23-Oct-2026.
"""
import hashlib
import os
import shutil
import sys

FROM_PIN = {"sorting_desk.py": "377adbcabf50186f67220d5a29e500dc", "asset_register.py": "2bb2860073201090a1ca345e701a9e58"}
FROM_PIN_FULL = {}
HERE = os.path.dirname(os.path.abspath(__file__))

DESK_PY = r'''# ---------------------------------------------------------------------------------------------- S634_PROCROOM_LIST (D773 Kit 1)
# The owner's rulings, 23-Oct-2026 (S342, D773): a Procedure room paper's lines each get a product from his list (procroom.py) and a
# place -- Procedure room, Home use (Dr MK), Clinic equipment, OT, Sanjeevni (orthotics, flagged for him). The desk's panel carries
# NO rate: the rates are his alone, on his Procedure room page. Without procroom.py the desk runs exactly as before.
def _s634_pr():
    """procroom.py, when it is mounted; else None (the panel and its lines then give nothing)."""
    m = sys.modules.get("procroom")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _s634_paper(db, b, owner, rd, dest=""):
    """paper_json's S634 part: the Procedure room panel (its lines, the products, the places, whether they count) -- no rate."""
    out = {"pr": None}
    pr = _s634_pr()
    if pr is None or _lane(b) == "pharmacy":
        return out
    if not owner and ((b["subgroup"] or "") == "procedure" or dest == "procedure" or _yuvika(b["vendor"])):
        out["stk"] = None                                            # D773: a Procedure room paper -- in it, suggested to it, or Yuvika's --
        #                                                              sends no stationery panel (it carries the paper's rates) to a non-owner
    try:
        out["pr"] = pr.panel(db, b, rd, owner)
    except Exception as ex:                                          # noqa: BLE001
        print("S634 panel: %s" % ex, file=sys.stderr)
    return out


def _s634_post(db, bid, p, dest):
    """In the Save's transaction: the Procedure room lines when the paper is in Procedure room (a re-save replaces them, never
    adds); a paper moved out of it has its lines voided (kept)."""
    pr = _s634_pr()
    if pr is None:
        return []
    b = _row(db, bid)
    if dest == "procedure" and (b["subgroup"] or "") == "procedure":
        if "pr_lines" in p:
            try:
                return pr.save_lines(db, b, p.get("pr_lines") or [], _who(), _owner())
            except ValueError as e:
                raise DeskError(str(e) + " Nothing was saved.")
        return []
    if pr.has_lines(db, b):
        pr.void_lines(db, b, _who(), "saved on the desk to %s" % DEST_NAME.get(dest, dest))
        return ["Its Procedure room lines are taken off (it is no longer in Procedure room)."]
    return []


'''

DESK_JS = r'''// S634_PROCROOM_LIST: the Procedure room panel -- each line's product (or "not on the list"), quantity, brand and place; no rate
function s634init(j){S.pr=null;var bx=$('pr634');if(bx){bx.innerHTML='';bx.removeAttribute('data-for');}
 if(j.pr){S.pr={lines:(j.pr.lines||[]).map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,brand:l.brand||'',place:l.place||'proc',item:String(l.item==null?'':l.item),hand:l.hand,sug:l.sug,saved:l.saved,orth:l.orth};})};}}
function s634flag(l){if(l.item=='free'&&l.place=='proc'){return 'a Procedure room line needs a product from the list — or “Not on the list”';}
 if(l.place=='sanj'){return 'orthotics — goes to Sanjeevni, flagged for Dr Manoj';}if(l.item=='ask'){return 'waits for Dr Manoj to add it to his list';}return '';}
function s634flags(){((S.pr||{}).lines||[]).forEach(function(l,i){var e=document.querySelector('[data-prf="'+i+'"]');if(e){e.textContent=s634flag(l);}});}
function s634paint(j){var box=$('pr634');if(!box){return;}
 if(S.dest!='procedure'||!j.pr||!S.pr){box.style.display='none';return;}
 if(box.getAttribute('data-for')==String(j.id)&&box.innerHTML){box.style.display='flex';s634flags();return;}
 var h='<b>Procedure room lines</b><span class=muted>Give each line its product, quantity and place. A line left without a product counts nothing. No rates here — Dr Manoj adds them.</span>';
 if(!j.pr.counts){h+='<div class=muted>'+esc(j.pr.why)+'.</div>';}if(j.pr.noread){h+='<div class=muted>No items read — fill the line by hand.</div>';}
 S.pr.lines.forEach(function(l,i){var o='<option value="">— product —</option>',bl='';(j.pr.items||[]).forEach(function(x){o+='<option value="'+x.id+'"'+(String(x.id)==l.item?' selected':'')+'>'+esc(x.name)+(x.rare?' (rarely used)':'')+'</option>';if(String(x.id)==l.item){bl=(x.brands||[]).join(', ');}});
  if(j.pr.owner){o+='<option value=new'+(l.item=='new'?' selected':'')+'>+ Add to the list</option>';}
  o+='<option value=ask'+(l.item=='ask'?' selected':'')+'>Not on the list — for Dr Manoj</option><option value=free'+(l.item=='free'?' selected':'')+'>Not a list item (by its name)</option>';
  var p='';(j.pr.places||[]).forEach(function(x){p+='<option value="'+x[0]+'"'+(x[0]==l.place?' selected':'')+'>'+esc(x[1])+'</option>';});
  h+='<div class=prl style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;border-top:1px solid #e6ebf0;padding:6px 0 2px">'+(l.hand?'<input data-prn="'+i+'" value="'+esc(l.name)+'" placeholder="what it is" style="width:150px;font-size:13px;padding:4px">':'<span style="min-width:120px">'+esc(l.name)+'</span>')
   +'<input data-prq="'+i+'" value="'+esc(l.qty)+'" inputmode=decimal placeholder="qty" style="width:56px;font-size:13px;padding:4px"><span class=muted>'+esc(l.unit||'')+'</span>'
   +'<select data-pri="'+i+'" style="font-size:13px;padding:3px;max-width:230px">'+o+'</select>'
   +'<input data-prb="'+i+'" value="'+esc(l.brand)+'" placeholder="brand" title="'+esc(bl?('Brands: '+bl):'Brand, if written')+'" style="width:90px;font-size:13px;padding:4px">'
   +'<select data-prp="'+i+'" style="font-size:13px;padding:3px">'+p+'</select>'+((l.sug&&!l.saved)?'<span class=muted>suggested</span>':'')+'<span class=err data-prf="'+i+'"></span></div>';});
 h+='<a href="#" data-pradd=1 style="font-size:13px">+ Another line</a>';
 box.innerHTML=h;box.setAttribute('data-for',String(j.id));box.style.display='flex';s634flags();cue();}
function s634body(b,j){if(S.dest=='procedure'&&j.pr&&S.pr){b.pr_lines=S.pr.lines.map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,brand:l.brand,place:l.place,item:l.item,sug:!!(l.sug&&!l.saved)};});}}
document.addEventListener('input',function(e){var t=e.target;if(!S.pr||!t.hasAttribute){return;}
 if(t.hasAttribute('data-prq')){var lq=S.pr.lines[+t.getAttribute('data-prq')];lq.qty=t.value;lq.sug=false;}else if(t.hasAttribute('data-prn')){S.pr.lines[+t.getAttribute('data-prn')].name=t.value;}
 else if(t.hasAttribute('data-prb')){S.pr.lines[+t.getAttribute('data-prb')].brand=t.value;}});
document.addEventListener('change',function(e){var t=e.target;if(!S.pr||!t.hasAttribute){return;}
 if(t.hasAttribute('data-pri')){var l=S.pr.lines[+t.getAttribute('data-pri')];l.item=t.value;l.sug=false;s634flags();}
 else if(t.hasAttribute('data-prp')){var lp=S.pr.lines[+t.getAttribute('data-prp')];lp.place=t.value;lp.sug=false;s634flags();}});
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-pradd]'):null;if(!t||!S.pr||!S.cur){return;}e.preventDefault();
 var n=0;S.pr.lines.forEach(function(l){if(l.no>n){n=l.no;}});S.pr.lines.push({no:n+1,name:'',qty:'',unit:'',brand:'',place:'proc',item:'',hand:true,sug:false,saved:false,orth:false});
 var bx=$('pr634');if(bx){bx.removeAttribute('data-for');}s634paint(S.cur);});
'''

AR_PY = r'''# --- S634_PROCROOM_LIST begin -- D773 Kit 1: the procedure-room product list, each slip line's place, his rates (procroom.py) (23-Oct-2026) ---
# Guarded: if procroom.py is absent or cannot load, this app runs exactly as before -- the menu item and the desk's panel give nothing.
PROCROOM_S634 = "S634"


def _s634_menu(role):
    """The one menu's Procedure room item (procroom.menu_items): the owner only."""
    try:
        _m = _sys.modules.get("procroom")
        if _m is not None and getattr(_m, "MOUNTED", False):
            return list(_m.menu_items(role))
    except Exception as _ex:                                      # noqa: BLE001
        print("S634 menu: %s" % _ex, file=_sys.stderr)
    return []


try:
    import procroom as _procroom
    _procroom.init(_sys.modules[__name__])
except Exception as _ex_s634:                                  # noqa: BLE001
    print("procroom NOT mounted: %s" % _ex_s634, file=_sys.stderr)
# --- S634_PROCROOM_LIST end ---


'''

EDITS = {"sorting_desk.py": [
    ('''BATTERY = "S571"              # S571_BATTERIES: the switch batteries.on; a battery's bill offered on the desk; the payer pre-selects
''',
     '''BATTERY = "S571"              # S571_BATTERIES: the switch batteries.on; a battery's bill offered on the desk; the payer pre-selects
PROCROOM = "S634"             # S634_PROCROOM_LIST: a Procedure room paper's lines -- product, quantity, brand, place; no rate (procroom.py)
'''),
    ('''    "stationery": "Clinic stationery and packaging. Match its lines to the stationery list below — the stock goes up once.",      # S568
''',
     '''    "stationery": "Clinic stationery and packaging. Match its lines to the stationery list below — the stock goes up once.",      # S568
    "procedure": "Procedure-room goods. Give each line its product and its place below — the rates are Dr Manoj's alone.",      # S634
'''),
    ('''            **_s571_paper(db, b, owner)}                                                     # S571: the battery offer (nothing without batteries.py)''',
     '''            **_s571_paper(db, b, owner),                                                     # S571: the battery offer (nothing without batteries.py)
            **_s634_paper(db, b, owner, rd, dest)}                                           # S634: the Procedure room panel (nothing without procroom.py)'''),
    ('''    msgs += _s568_post(db, bid, p, dest)                            # S568 items 3, 6: the stationery lines; the mixed mark
''',
     '''    msgs += _s568_post(db, bid, p, dest)                            # S568 items 3, 6: the stationery lines; the mixed mark
    msgs += _s634_post(db, bid, p, dest)                            # S634: the Procedure room lines (procroom.py)
'''),
    ('''<div class=box id=st568 style="display:none"></div>''',
     '''<div class=box id=st568 style="display:none"></div><div class=box id=pr634 style="display:none"></div>'''),
    ('''s568init(j);s571init(j);''', '''s568init(j);s634init(j);s571init(j);'''),
    ('''s568paint(j);s571paint(j);''', '''s568paint(j);s634paint(j);s571paint(j);'''),
    ('''s560body(b,j);s568body(b,j);''', '''s560body(b,j);s568body(b,j);s634body(b,j);'''),
    ('''// S571_BATTERIES: "Battery fitted at''', DESK_JS + '''// S571_BATTERIES: "Battery fitted at'''),
    ('''# ---------------------------------------------------------------------------------------------- the mount
def init(ar):''', DESK_PY + '''# ---------------------------------------------------------------------------------------------- the mount
def init(ar):'''),
], "asset_register.py": [
    ('''        out += _s568_menu(r)                                           # S568: nothing when stationery.py is not mounted
''',
     '''        out += _s568_menu(r)                                           # S568: nothing when stationery.py is not mounted
        out += _s634_menu(r)                                           # S634: nothing when procroom.py is not mounted
'''),
    ('''# ---------------------------------------------------------------- main
if __name__ == "__main__":''', AR_PY + '''# ---------------------------------------------------------------- main
if __name__ == "__main__":'''),
]}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    total = 0
    for f, edits in EDITS.items():
        with open(os.path.join(src, f), "rb") as h:
            raw = h.read()
        pin = FROM_PIN_FULL.get(f) or FROM_PIN[f]
        if not md5b(raw).startswith(pin):
            out("%s: FROM is %s, not the pin %s -- STOP" % (f, md5b(raw)[:8], pin[:8]))
            return 1
        t = raw.decode("utf-8")
        for i, (a, b) in enumerate(edits, 1):
            n = t.count(a)
            if n != 1:
                out("%s: edit %d anchor found %d times (must be 1) -- STOP" % (f, i, n))
                return 1
            t = t.replace(a, b)
        data = t.encode("utf-8")
        with open(os.path.join(dst, f), "wb") as h:
            h.write(data)
        total += len(edits)
        out("%s: %d counted edit(s), %s -> %s" % (f, len(edits), md5b(raw)[:8], md5b(data)))
    shutil.copyfile(os.path.join(HERE, "procroom.py"), os.path.join(dst, "procroom.py"))
    with open(os.path.join(dst, "procroom.py"), "rb") as h:
        out("procroom.py: NEW, %s" % md5b(h.read()))
    out("make_s634: %d counted edits in all, and one new file" % total)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
