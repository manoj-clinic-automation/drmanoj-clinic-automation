# -*- coding: utf-8 -*-
"""edits_s732.py -- S732_DESK_OTHER_LINES: the counted edits on /root/assetapp/sorting_desk.py (FROM d2742ded, S731's TO).

D838's second kit, at the owner's word "X-ray film and Others lines on the desk" (17:19 IST 06-Nov-2026), narrowed by his word at
17:25 IST ("the X-ray part is pretty well sorted ... check whether anything is really required"): checked live -- all 11 film bills
since April read with their size and boxes (the film log: none 'size unknown', none held; the X-ray costs page: none 'size not
read') -- so NO film lines. What is built, on his approved mock-up https://claude.ai/artifact/XpbAyqQAyCimRnv3dz1ECm (its Other lines
panel):
  * a paper in "Others": Other lines -- what it is, the quantity, the unit, the rate; + Add a line, x to remove, each line's
    amount and the lines' total against the paper; the note "Kept as a clinic consumable bill.";
  * the lines start from what was read and ARE the paper's own item lines (bill_items) -- no table is added. The Save writes them
    ONLY when the person changed the panel; the first reading stays in claude_reading. Audited 'desk_lines'.

Each edit is (name, old, new): `old` must occur EXACTLY ONCE in the FROM bytes, or make_s732.py refuses and writes nothing.
"""

KIT = "S732_DESK_OTHER_LINES"

E_MARK = ('CHALLAN_READ = "S731"         # S731_CHALLAN_READ (F-1136): a paper never put to Claude is read after its Save\n',
          'CHALLAN_READ = "S731"         # S731_CHALLAN_READ (F-1136): a paper never put to Claude is read after its Save\n'
          'OTHERLINES = "S732"           # S732_DESK_OTHER_LINES (D838): Other lines on the desk\n')

E_PAPER = ('            **_s634_paper(db, b, owner, rd, dest)}                                           # S634: the Procedure room panel (nothing without procroom.py)\n',
           '            **_s634_paper(db, b, owner, rd, dest),                                           # S634: the Procedure room panel (nothing without procroom.py)\n'
           '            **_s732_paper(db, b)}                                                            # S732: the Other lines panel\n')

E_POST = ('    msgs += _s634_post(db, bid, p, dest)                            # S634: the Procedure room lines (procroom.py)\n',
          '    msgs += _s634_post(db, bid, p, dest)                            # S634: the Procedure room lines (procroom.py)\n'
          '    msgs += _s732_post(db, bid, p, dest)                            # S732: the Other lines (the paper\'s item lines)\n')

PY_BLOCK = r'''# ---------------------------------------------------------------------------------------------- S732_DESK_OTHER_LINES
# D838's second kit (the owner's word 17:19 IST 06-Nov-2026; X-ray film lines dropped at his word 17:25 -- every film bill since April
# was read with its size and boxes): a paper in Others gets Other lines on the desk (what it is, quantity, unit, rate), on his mock-up
# https://claude.ai/artifact/XpbAyqQAyCimRnv3dz1ECm. The lines ARE the paper's item lines (bill_items), written only when the person
# changed the panel (fo_lines sent); the first reading stays in claude_reading. No table is added.
S732_DESTS = ("others",)
S732_MAX = 40
NOTES.setdefault("others", "Kept as a clinic consumable bill. One line per thing on the paper: what it is, quantity and rate.")


def _s732_paper(db, b):
    """paper_json's S732 part: the paper's item lines for the Other lines panel (the page shows it only in Others)."""
    if _lane(b) == "pharmacy" or (b["subgroup"] or "") in ("personal", "resume", "patient_paper"):
        return {"fo": None}
    try:
        rows = db.execute("SELECT item_name, pack_size, quantity, rate FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)).fetchall()
    except sqlite3.Error:
        rows = []
    lines = [{"name": (r["item_name"] or "")[:120], "qty": r["quantity"], "unit": (r["pack_size"] or "")[:20], "rate": r["rate"]}
             for r in rows[:S732_MAX]]
    return {"fo": {"lines": lines, "noread": not lines}}


def _s732_num(v, what, n):
    s = str(v if v is not None else "").strip().replace(",", "")
    if s == "":
        return None
    try:
        x = float(s)
    except ValueError:
        raise DeskError("Line %d: the %s is not a number. Nothing was saved." % (n, what))
    if not (0 <= x <= 10000000):
        raise DeskError("Line %d: the %s is out of range. Nothing was saved." % (n, what))
    return x


def _s732_post(db, bid, p, dest):
    """In the Save's transaction: the Other lines become the paper's item lines -- only when the panel was changed (fo_lines sent)
    and the paper goes to Others. A line with nothing typed is dropped; when none is left the item lines stay as they are. Each line
    needs what it is and the quantity; the rate is optional; the amount = quantity x rate."""
    if "fo_lines" not in p or dest not in S732_DESTS:
        return []
    raw = p.get("fo_lines")
    if not isinstance(raw, list):
        return []
    out = []
    for i, l in enumerate(raw[:S732_MAX], 1):
        if not isinstance(l, dict):
            continue
        name = " ".join(str(l.get("name") or "").split())[:120]
        unit = " ".join(str(l.get("unit") or "").split())[:20]
        qty = _s732_num(l.get("qty"), "quantity", i)
        rate = _s732_num(l.get("rate"), "rate", i)
        if not (name or qty or rate):
            continue
        if not name:
            raise DeskError("Line %d: what is it? Nothing was saved." % i)
        if not qty:
            raise DeskError("Line %d: the quantity? Nothing was saved." % i)
        out.append((name, unit or None, qty, rate, round(qty * rate, 2) if rate is not None else None))
    if not out:
        return []
    was = db.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (bid,)).fetchone()[0]
    db.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,))
    for name, unit, qty, rate, amt in out:
        db.execute("INSERT INTO bill_items(bill_id, item_name, pack_size, quantity, rate, amount) VALUES(?,?,?,?,?,?)",
                   (bid, name, unit, qty, rate, amt))
    AR._audit_bill(db, bid, "desk_lines", {"kind": "others", "lines": len(out), "was": was, "via": "desk"})
    return ["%d item line%s saved." % (len(out), "" if len(out) == 1 else "s")]


'''

E_PYBLOCK = ('# ---------------------------------------------------------------------------------------------- S715_DESK_ITEM_LINES\n',
             PY_BLOCK + '# ---------------------------------------------------------------------------------------------- S715_DESK_ITEM_LINES\n')

E_BOX = ('<div class=box id=pr634 style="display:none"></div>',
         '<div class=box id=pr634 style="display:none"></div><div class=box id=fo732 style="display:none"></div>')

E_INIT = ('s634init(j);s571init(j)', 's634init(j);s732init(j);s571init(j)')

E_PAINT = ('s634paint(j);s571paint(j);paint2();}', 's634paint(j);s732paint(j);s571paint(j);paint2();}')

E_BODY = ("s634body(b,j);if($('pg_on')", "s634body(b,j);s732body(b,j);if($('pg_on')")

JS = r"""// S732_DESK_OTHER_LINES (D838, its second kit): Other lines -- the paper's own item lines
function s732blank(){return {name:'',qty:'',unit:'',rate:''};}
function s732init(j){S.fo=null;var bx=$('fo732');if(bx){bx.innerHTML='';bx.removeAttribute('data-for');}
 if(j.fo){S.fo={touched:false,lines:(j.fo.lines||[]).map(function(l){return {name:l.name||'',qty:(l.qty==null?'':String(l.qty)),unit:l.unit||'',rate:(l.rate==null?'':String(l.rate))};})};}}
function s732why(l){if(!l.name.trim()&&!l.qty&&!l.rate){return '';}if(!l.name.trim()){return 'what is it?';}if(!(num(l.qty)>0)){return 'the quantity?';}return '';}
function s732tot(){if(!S.fo){return;}var bx=$('fo732'),t=0,any=false;if(!bx){return;}
 S.fo.lines.forEach(function(l,i){var a=bx.querySelector('[data-foa="'+i+'"]'),e=bx.querySelector('[data-foe="'+i+'"]');var q=num(l.qty),r=num(l.rate),has=String(l.rate).trim()!=='';
  if(a){a.textContent=(has&&q>0)?inr2(q*r):'';}if(has&&q>0){t+=q*r;any=true;}if(e){e.textContent=S.fo.touched?s732why(l):'';}});
 var w=$('fotot732');if(w){var amt=String(($('f_amt')||{}).value||'').trim();w.textContent=any?('Lines total '+inr2(t)+(amt?(' · the paper '+inr2(num(amt))):'')):'';}}
function s732paint(j){var box=$('fo732');if(!box){return;}
 if(S.dest!='others'||!j.fo||!S.fo){box.style.display='none';return;}
 if(box.getAttribute('data-for')==String(j.id)&&box.innerHTML){box.style.display='flex';s732tot();return;}
 if(!S.fo.lines.length){S.fo.lines.push(s732blank());}var st='font-size:13px;padding:4px';
 var h='<b>Other lines</b><span class=muted>One line per thing on the paper: what it is, quantity and rate.</span>';
 if(j.fo.noread){h+='<div class=muted>No items read — fill the lines by hand.</div>';}
 S.fo.lines.forEach(function(l,i){h+='<div class=fol732 style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;border-top:1px solid #e6ebf0;padding:6px 0 2px">'
  +'<input data-fon="'+i+'" value="'+esc(l.name)+'" placeholder="what it is" aria-label="What it is" style="width:200px;'+st+'">'
  +'<input data-foq="'+i+'" value="'+esc(l.qty)+'" inputmode=decimal placeholder="qty" aria-label="Quantity" style="width:56px;'+st+'">'
  +'<input data-fou="'+i+'" value="'+esc(l.unit)+'" placeholder="unit" aria-label="Unit" style="width:70px;'+st+'">'
  +'<input data-fr="'+i+'" value="'+esc(l.rate)+'" inputmode=decimal placeholder="rate ₹" aria-label="Rate" style="width:80px;'+st+'">'
  +'<span data-foa="'+i+'" style="min-width:64px;text-align:right"></span><a href="#" data-fox="'+i+'" title="Remove this line" aria-label="Remove this line" style="font-size:16px;text-decoration:none;padding:0 4px">×</a><span class=err data-foe="'+i+'"></span></div>';});
 h+='<div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap"><a href="#" data-foadd=1 style="font-size:13px">+ Add a line</a><span id=fotot732 class=muted></span></div>';
 box.innerHTML=h;box.setAttribute('data-for',String(j.id));box.style.display='flex';s732tot();cue();}
function s732body(b,j){if(S.dest=='others'&&j.fo&&S.fo&&S.fo.touched){b.fo_lines=S.fo.lines.map(function(l){return {name:l.name,qty:l.qty,unit:l.unit,rate:l.rate};});}}
function s732redraw(){var bx=$('fo732');if(bx){bx.removeAttribute('data-for');}s732paint(S.cur);}
document.addEventListener('input',function(e){var t=e.target;if(!S.fo||!t||!t.hasAttribute){return;}var k=null,f='';
 if(t.hasAttribute('data-foq')){k=t.getAttribute('data-foq');f='qty';}else if(t.hasAttribute('data-fr')){k=t.getAttribute('data-fr');f='rate';}
 else if(t.hasAttribute('data-fon')){k=t.getAttribute('data-fon');f='name';}else if(t.hasAttribute('data-fou')){k=t.getAttribute('data-fou');f='unit';}
 if(k===null){if(t.id=='f_amt'){s732tot();}return;}var l=S.fo.lines[+k];if(!l){return;}l[f]=t.value;S.fo.touched=true;s732tot();});
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-foadd],[data-fox]'):null;if(!t||!S.fo||!S.cur){return;}e.preventDefault();
 if(t.hasAttribute('data-foadd')){S.fo.lines.push(s732blank());}else{S.fo.lines.splice(+t.getAttribute('data-fox'),1);}S.fo.touched=true;s732redraw();});
"""

E_JS = ("function s634init(j){S.pr=null;", JS + "function s634init(j){S.pr=null;")

EDITS = [("mark", E_MARK), ("paper", E_PAPER), ("post", E_POST), ("pyblock", E_PYBLOCK), ("box", E_BOX), ("init", E_INIT),
         ("paint", E_PAINT), ("body", E_BODY), ("js", E_JS)]
