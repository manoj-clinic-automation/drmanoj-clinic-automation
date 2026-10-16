#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s568.py -- S568_STATIONERY_STOCK: the three edited scan-app files and the parent's packs.py, rebuilt from the pinned live
bytes; the new stationery.py is the kit's own file (copied beside them).

    python3 make_s568.py <dir with the live sorting_desk.py, clinic_papers.py, asset_register.py [, packs.py]> <out dir>
    python3 make_s568.py --cp-on <S566's tidy clinic_papers.py (c6f126aa)> <out file>      (S563's tidy fetch, re-run)

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the
counted number of times. Every byte of each built file comes from the live file plus these edits. packs.py: build_bundle's
kind filter only (S568_BRIEF_R1 C3); when packs.py is absent from the input folder, or not at its pin, it is left out and
said (the brief: "STOP that file, build the rest and say so").

S568 FIX1 (16-Oct-2026, the kit review K1's CORRECTIONS 1-3; same kit, revised in place): the FROM pins and every anchor are
unchanged; only SD1's mark (STOCK_FIX) and SD22's block (add_page refuses any file but a PDF or a photo, before the intake is
called) differ in sorting_desk.py; stationery.py carries CORRECTIONS 1 and 2."""
import hashlib, os, shutil, sys

FROM = {"sorting_desk.py": "a053a222ee0fa8b0026aa4fc2511e8a9",
        "clinic_papers.py": "024464cc3d3ab5e1ead1526540904d61",
        "asset_register.py": "8b3c455128663db69c48232bf26c0083",
        "packs.py": "048d2ad81abb0271a1cddd31134544bb"}
CP_TIDY_S566 = "c6f126aa"                                            # S566's tidy comparison pin (first 8): the --cp-on input
HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================================================ sorting_desk.py
SD_EDITS = [
    # SD1 -- the mark
    (r'''LAST = "S566"                 # S566_SCANAPP_LAST_FIXES: a restore checks for a double first; every waiting paper reachable; one count
''',
     r'''LAST = "S566"                 # S566_SCANAPP_LAST_FIXES: a restore checks for a double first; every waiting paper reachable; one count
STOCK = "S568"                # S568_STATIONERY_STOCK: Stationery & packaging, its lines to the stock, the mixed tick, Add from a file
PEXP = "Pharmacy expense"     # S568 item 7: the Aumni preset's kind (never 'Pharmacy': Sanjeevni's registers never pair it)
STOCK_FIX = "S568_FIX1"       # S568 FIX1 (K1 CORRECTION 3): "Add a paper from a file" takes a PDF or a photo only
''', 1),
    # SD2 (item 1, R1 C8) -- CONS (and so CLINIC_DEST)
    (r'''CONS = ("procedure", "xray_small", "xray_11x14", "others")
''',
     r'''CONS = ("procedure", "xray_small", "xray_11x14", "others", "stationery")          # S568 item 1
''', 1),
    # SD3 (item 1) -- the desk's destination list
    (r'''                            ("xray_11x14", "X-ray 11 × 14"), ("others", "Others"))),
''',
     r'''                            ("xray_11x14", "X-ray 11 × 14"), ("others", "Others"), ("stationery", "Stationery & packaging"))),      # S568
''', 1),
    # SD3b (item 1) -- the fifth consumables button on a narrow screen: two short lines, so the six groups keep their rows (the
    # S560 desk-layout browser walk's 1280 x 720 case); from 1301 px wide nothing changes
    (r'''.d.on{border:2px solid #2b5d8a;background:#e3edf7;font-weight:700}.d.pe.on{border-color:#6b4a8a;background:#efe7f6}
''',
     r'''.d.on{border:2px solid #2b5d8a;background:#e3edf7;font-weight:700}.d.pe.on{border-color:#6b4a8a;background:#efe7f6}
@media (max-width:1300px){.d[data-d=stationery]{max-width:86px;line-height:1.1;padding:2px 8px}}
''', 1),
    # SD4 (item 3) -- its grey note
    (r'''    "implant_stock": "Goes to the implant stock ledger of this supplier (owed until paid).",
''',
     r'''    "implant_stock": "Goes to the implant stock ledger of this supplier (owed until paid).",
    "stationery": "Clinic stationery and packaging. Match its lines to the stationery list below — the stock goes up once.",      # S568
''', 1),
    # SD5 (item 4, R1 C9) -- the switch, one tuple
    (r'''            ("machine.on", "Machine pages for Shavez"))                                  # S557 A7
''',
     r'''            ("machine.on", "Machine pages for Shavez"),                                  # S557 A7
            ("stationery.issue_on", "Stationery diya for managers"))                    # S568 item 4 (absent = OFF)
''', 1),
    # SD6 (item 1) -- The month's sections: after Others (month_total follows it)
    (r'''                  ("others", "Others", ("others",)),
''',
     r'''                  ("others", "Others", ("others",)),
                  ("stationery", "Stationery & packaging", ("stationery",)),                  # S568 item 1
''', 1),
    # SD7 (item 6, R1 C12) -- the mixed mark: one new column on bills, by the desk's own ensure
    (r'''BILL_COLS = (("paid_on", "TEXT"), ("paid_amount", "REAL"), ("to_accountant", "INTEGER NOT NULL DEFAULT 0"))      # S560 item 6
''',
     r'''BILL_COLS = (("paid_on", "TEXT"), ("paid_amount", "REAL"), ("to_accountant", "INTEGER NOT NULL DEFAULT 0"),      # S560 item 6
             ("mixed", "INTEGER NOT NULL DEFAULT 0"))                                                     # S568 item 6
''', 1),
    # SD8 (item 1, R1 C8) -- the rate-before branch
    (r'''        if key in ("procedure", "xray", "others"):
''',
     r'''        if key in ("procedure", "xray", "others", "stationery"):          # S568
''', 1),
    # SD9 (item 7, R1 C6) -- The month's pharmacy count leaves the pharmacy expense out; its own line, never in a total
    (r'''    apart = {"pharmacy": one(" AND b.lane='pharmacy'"), "lab": one(" AND b.lane='lab_purchase'"),
             "mk": pe_all - pe_bh, "bh": pe_bh, "patient": one(" AND b.subgroup=?", PATIENT)}
''',
     r'''    apart = {"pharmacy": one(" AND b.lane='pharmacy' AND COALESCE(b.kind,'')<>'" + PEXP + "'"), "lab": one(" AND b.lane='lab_purchase'"),   # S568
             "mk": pe_all - pe_bh, "bh": pe_bh, "patient": one(" AND b.subgroup=?", PATIENT)}
    apart.update(_s568_apart(db, ym))                                 # S568 item 7: Sanjeevni -- pharmacy expenses (never a section)
''', 1),
    # SD10 (item 4) -- the switch's state
    (r'''            "machine.on": (_setting(db, "machine.on", "off") or "").strip().lower() == "on"}      # S557 A7
''',
     r'''            "machine.on": (_setting(db, "machine.on", "off") or "").strip().lower() == "on",      # S557 A7
            "stationery.issue_on": (_setting(db, "stationery.issue_on", "off") or "").strip().lower() == "on"}      # S568
''', 1),
    # SD11 (item 7) -- The month's Kept apart: the pharmacy expenses line
    (r'''<div style="display:flex;justify-content:space-between;font-size:14px"><span>Pharmacy — Sanjeevni</span><b>{{apart.pharmacy}} scan{{'' if apart.pharmacy==1 else 's'}}</b></div>
''',
     r'''<div style="display:flex;justify-content:space-between;font-size:14px"><span>Pharmacy — Sanjeevni</span><b>{{apart.pharmacy}} scan{{'' if apart.pharmacy==1 else 's'}}</b></div>
{% if apart.pexp %}<div id=s568pexp style="display:flex;justify-content:space-between;gap:8px;font-size:14px"><span>Sanjeevni — pharmacy expenses</span><b>{{apart.pexp}} · {{inr(apart.pexp_total)}} · paid by Dr MK's card</b></div>{% endif %}
''', 1),
    # SD12 (item 7) -- the desk: "Add a paper from a file" under Open B-____ (the left column; the right panel's height unchanged)
    (r'''<div id=openerr class=err style="padding:0 12px"></div>
''',
     r'''<div id=openerr class=err style="padding:0 12px"></div>
{% if add_href %}<a id=s568addlink href="{{add_href}}" style="display:block;padding:4px 12px 6px;font-size:13px;border-bottom:1px solid #e6ebf0">+ Add a paper from a file</a>{% endif %}
''', 1),
    # SD13 (items 3, 6) -- the desk: the mixed tick and the stationery panel, under the destination's note
    (r'''<div class=muted style="font-size:12px" id=destnote></div><div id=hints class=muted style="font-size:12px"></div></div>
''',
     r'''<div class=muted style="font-size:12px" id=destnote></div><div id=hints class=muted style="font-size:12px"></div>
<label id=mixbox style="display:none;gap:6px;align-items:center;font-size:13px;color:#1f2a36"><input type=checkbox id=mixed style="width:auto;display:inline"> mixed: clinic + lab items</label>
<div class=box id=st568 style="display:none"></div></div>
''', 1),
    # SD14 -- the desk's script: the paper opened
    (r'''s560init(j);draw();drawList();});}
''',
     r'''s560init(j);s568init(j);draw();drawList();});}
''', 1),
    # SD15 -- the desk's script: painted
    (r''' s560paint(j);paint2();}
''',
     r''' s560paint(j);s568paint(j);paint2();}
''', 1),
    # SD16 -- the desk's script: the Save's body
    (r''' s560body(b,j);if($('pg_on').checked&&$('pg_no').value.trim()){b.page_of=$('pg_no').value.trim();b.dest='';}post(b);});
''',
     r''' s560body(b,j);s568body(b,j);if($('pg_on').checked&&$('pg_no').value.trim()){b.page_of=$('pg_no').value.trim();b.dest='';}post(b);});
''', 1),
    # SD17 -- the desk's script: S568's functions
    (r'''$('readbox').addEventListener('toggle',function(){S.readopen=$('readbox').open;cue();});
''',
     r'''// S568_STATIONERY_STOCK: the Stationery & packaging panel (match / Add to the list / not a stock item) and the mixed tick
function inr2(x){var n=parseFloat(x);if(!isFinite(n)){return '';}return (Math.round(n*100)%100)?('₹'+n.toFixed(2)):inr(n);}
function s568init(j){S.stk=null;var bx=$('st568');if(bx){bx.innerHTML='';bx.removeAttribute('data-for');}
 if(j.stk){S.stk={lines:(j.stk.lines||[]).map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,rate:l.rate,item:String(l.item==null?'':l.item),hand:l.hand,sug:l.sug,saved:l.saved};})};}S.mixed=!!j.mixed;}
function s568uk(u){u=String(u||'').toLowerCase().replace(/[^a-z]/g,'');var m={pcs:'piece',pc:'piece',pieces:'piece',nos:'piece',no:'piece',nag:'piece',pkt:'packet',pkts:'packet',packets:'packet',packs:'pack',pk:'pack',reams:'ream',boxes:'box',rolls:'roll',sets:'set',books:'book',registers:'register',files:'file',dozens:'dozen',doz:'dozen',bundles:'bundle'};return m[u]||u;}
function s568flag(l){var it=null;((S.cur.stk||{}).items||[]).forEach(function(x){if(String(x.id)==l.item){it=x;}});if(!it){return '';}
 var lu=s568uk(l.unit),iu=s568uk(it.unit);if(lu&&iu&&lu!=iu){return 'unit differs — on the paper: '+l.unit+', on the list: '+it.unit;}
 if(l.rate==null||l.rate===''||it.rate==null){return '';}return Math.round(parseFloat(l.rate)*100)!=Math.round(parseFloat(it.rate)*100)?'rate '+inr2(l.rate)+' — list '+inr2(it.rate):'';}
function s568flags(){((S.stk||{}).lines||[]).forEach(function(l,i){var e=document.querySelector('[data-stf="'+i+'"]');if(e){e.textContent=s568flag(l);}});}
function s568paint(j){var box=$('st568'),mb=$('mixbox');if(!box||!mb){return;}
 mb.style.display=((S.kind=='bill'||S.kind=='challan')&&(S.dest=='stationery'||S.dest=='lab'))?'flex':'none';$('mixed').checked=!!S.mixed;
 if(S.dest!='stationery'||!j.stk||!S.stk){box.style.display='none';return;}
 if(box.getAttribute('data-for')==String(j.id)&&box.innerHTML){box.style.display='flex';s568flags();return;}
 var h='<b>Stationery lines</b><span class=muted>Match each line to the list, “+ Add to the list”, or “not a stock item”. A line left alone counts nothing.</span>';
 if(!j.stk.counts){h+='<div class=muted>'+esc(j.stk.why)+'.</div>';}if(j.stk.noread){h+='<div class=muted>No items read — fill the line by hand.</div>';}
 S.stk.lines.forEach(function(l,i){var o='<option value="">— choose —</option>';(j.stk.items||[]).forEach(function(x){o+='<option value="'+x.id+'"'+(String(x.id)==l.item?' selected':'')+'>'+esc(x.name)+' ('+esc(x.unit)+')</option>';});
  o+='<option value=new'+(l.item=='new'?' selected':'')+'>+ Add to the list</option><option value=ns'+(l.item=='ns'?' selected':'')+'>not a stock item</option>';
  h+='<div class=stl style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">'+(l.hand?'<input data-stn="'+i+'" value="'+esc(l.name)+'" placeholder="item" style="width:150px;font-size:13px;padding:4px">':'<span style="min-width:120px">'+esc(l.name)+'</span>')
   +'<input data-stq="'+i+'" value="'+esc(l.qty)+'" inputmode=decimal style="width:60px;font-size:13px;padding:4px"><span class=muted>'+esc(l.unit||'')+'</span>'
   +'<select data-sti="'+i+'" style="font-size:13px;padding:3px">'+o+'</select>'+((l.sug&&!l.saved)?'<span class=muted>suggested</span>':'')+'<span class=err data-stf="'+i+'"></span></div>';});
 box.innerHTML=h;box.setAttribute('data-for',String(j.id));box.style.display='flex';s568flags();cue();}
function s568body(b,j){if(S.dest=='stationery'&&j.stk&&S.stk){b.st_lines=S.stk.lines.map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,rate:l.rate,item:l.item};});}
 if($('mixbox')&&$('mixbox').style.display!='none'){b.mixed=!!$('mixed').checked;}}
document.addEventListener('input',function(e){var t=e.target;if(!S.stk||!t.hasAttribute){return;}
 if(t.hasAttribute('data-stq')){S.stk.lines[+t.getAttribute('data-stq')].qty=t.value;}else if(t.hasAttribute('data-stn')){S.stk.lines[+t.getAttribute('data-stn')].name=t.value;}});
document.addEventListener('change',function(e){var t=e.target;if(t.id=='mixed'){S.mixed=t.checked;return;}if(!S.stk||!t.hasAttribute||!t.hasAttribute('data-sti')){return;}var l=S.stk.lines[+t.getAttribute('data-sti')];l.item=t.value;l.sug=false;s568flags();});
$('readbox').addEventListener('toggle',function(){S.readopen=$('readbox').open;cue();});
''', 1),
    # SD18 (item 7) -- the desk page hands the template its "Add a paper from a file" address
    (r'''    return render_template_string(DESK_TPL, bg=_bg(), cfg=cfg, n=n, owner=owner, chip=_chip(db), title="Sorting desk", cant=cant)
''',
     r'''    return render_template_string(DESK_TPL, bg=_bg(), cfg=cfg, n=n, owner=owner, chip=_chip(db), title="Sorting desk", cant=cant,
                                  add_href=(url_for("s568_add") if "s568_add" in AR.app.view_functions else ""))      # S568 item 7
''', 1),
    # SD19 (items 3, 6) -- one paper: its stationery panel, its mixed mark; the supplier note's mixed count
    (r'''            "supplier_note": supplier_note(db, key, name, mode, today, owner), "mode": mode,
''',
     r'''            "supplier_note": _s568_note(db, key, supplier_note(db, key, name, mode, today, owner), today), "mode": mode,      # S568 item 6
''', 1),
    (r'''            **_s560_paper(db, b, owner, rd, today)}                    # S560: paid state, receipt / statement lists, the fix
''',
     r'''            **_s560_paper(db, b, owner, rd, today), **_s568_paper(db, b, owner, rd)}      # S560: paid state ...; S568: the stationery panel
''', 1),
    # SD20 (items 3, 6) -- the Save: the stationery lines and the mixed mark, in the same transaction
    (r'''    msgs += _s560_post(db, bid, p, s560, status0)                   # S560: filed, the payment, the construction tick
''',
     r'''    msgs += _s560_post(db, bid, p, s560, status0)                   # S560: filed, the payment, the construction tick
    msgs += _s568_post(db, bid, p, dest)                            # S568 items 3, 6: the stationery lines; the mixed mark
''', 1),
    # SD21 (item 7) -- the route
    (r'''    app.add_url_rule("/desk/api/restore", "s563_restore", cr(_gate(restore_answer)), methods=["POST"])     # S563 F-902
''',
     r'''    app.add_url_rule("/desk/api/restore", "s563_restore", cr(_gate(restore_answer)), methods=["POST"])     # S563 F-902
    app.add_url_rule("/desk/add", "s568_add", cr(_gate(add_page)), methods=["GET", "POST"])                 # S568 item 7
''', 1),
    # SD22 -- the S568 block
    (r'''# --- S566_SCANAPP_LAST_FIXES end ---


# ---------------------------------------------------------------------------------------------- the mount
''',
     r'''# --- S566_SCANAPP_LAST_FIXES end ---


# ---------------------------------------------------------------------------------------------- S568_STATIONERY_STOCK (D730)
# The owner's rulings, 16-Oct-2026: a clinic stationery / packaging paper goes to the new clinic consumables group "Stationery &
# packaging"; its lines are matched on the desk to the stationery list (stationery.py), the stock going up once (counted when
# read, R1 B2); a challan or bill can be ticked "mixed: clinic + lab items"; "Add a paper from a file" goes through the intake's
# own code path, with ONE preset -- the Aumni envelopes, a Sanjeevni pharmacy expense paid by Dr MK's card (kind 'Pharmacy
# expense', written before the intake's first commit; paid on the paper itself, audited as card -- no paper_payment row).
def _s568_st():
    """stationery.py, when it is mounted; else None (the panel and its lines then give nothing)."""
    m = sys.modules.get("stationery")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _s568_paper(db, b, owner, rd):
    """paper_json's S568 part: the mixed mark; the stationery panel (its lines, the active items, whether they count)."""
    out = {"mixed": bool(_col(b, "mixed")), "stk": None}
    st = _s568_st()
    if st is None or _lane(b) == "pharmacy":
        return out
    try:
        out["stk"] = st.panel(db, b, rd)
    except Exception as ex:                                          # noqa: BLE001
        print("S568 panel: %s" % ex, file=sys.stderr)
    return out


def _s568_note(db, key, note, today=None):
    """The desk's supplier note (R1 note 18) + 'Mixed challans this month: N' when this supplier has any."""
    st = _s568_st()
    if st is None or not key:
        return note
    try:
        n = st.mixed_n(db, (today or _today()).strftime("%Y-%m"), key)
    except Exception:                                                # noqa: BLE001
        n = 0
    if not n:
        return note
    add = "Mixed challans this month: %d (clinic + lab items on one paper — raise it with the supplier)." % n
    return (note + " " + add) if note else add


def _s568_post(db, bid, p, dest):
    """In the Save's transaction: the mixed tick (a challan or a bill; audited); the stationery lines when the paper is in
    Stationery & packaging (a re-save replaces them, never adds); a paper moved out of it has its lines voided (kept)."""
    msgs = []
    b = _row(db, bid)
    if "mixed" in p and "mixed" in b.keys() and (b["doc_kind"] or "bill") in ("bill", "challan"):
        want, cur = (1 if p.get("mixed") else 0), int(b["mixed"] or 0)
        if want != cur:
            db.execute("UPDATE bills SET mixed=? WHERE id=?", (want, bid))
            AR._audit_bill(db, bid, "mixed", {"from": cur, "to": want, "via": "desk"})
            msgs.append("Marked: mixed clinic + lab items." if want else "The mixed mark is taken off.")
    st = _s568_st()
    if st is None:
        return msgs
    b = _row(db, bid)
    if dest == "stationery" and (b["subgroup"] or "") == "stationery":
        if "st_lines" in p:
            try:
                msgs += st.save_lines(db, b, p.get("st_lines") or [], _who())
            except ValueError as e:
                raise DeskError(str(e) + " Nothing was saved.")
    elif st.has_lines(db, b):
        st.void_lines(db, b, _who(), "saved on the desk to %s" % DEST_NAME.get(dest, dest))
        msgs.append("Its stationery lines are taken off the stock (it is no longer in Stationery & packaging).")
    return msgs


def _s568_apart(db, ym):
    """The month's 'Sanjeevni — pharmacy expenses': count and total (the amount read, else the amount paid) -- never a section,
    never in month_total."""
    try:
        r = db.execute("SELECT COUNT(*), SUM(COALESCE(b.total_amount, b.paid_amount)) FROM bills b WHERE b.kind=? AND b.status<>'rejected' "
                       "AND b.dup_of IS NULL AND b.page_of IS NULL AND " + CP.MONTH_OF + "=?", (PEXP, ym)).fetchone()
        return {"pexp": r[0] or 0, "pexp_total": r[1] or 0}
    except sqlite3.Error:
        return {"pexp": 0, "pexp_total": 0}


S568_FILE_EXT = ("pdf", "jpg", "jpeg", "png", "webp", "heic")       # S568 FIX1: the intake's PDF and photo types -- never doc / docx
S568_FILE_REFUSED = "That file cannot be taken — only a PDF or a photo (pdf, jpg, jpeg, png, webp, heic). Nothing was saved."

ADD_TPL = PAGE_HEAD +"""<div class=top><a href="{{url_for('s551_desk')}}" style="font-size:14px">‹ Sorting desk</a><span class=t>Add a paper from a file</span><span class=muted style="font-size:14px">A PDF or a photo — it goes in as a scan does: the stamp, the double-scan check, the reading.</span></div>
{% if msg %}<div class="msg{{' bad' if bad else ''}}" id=s568msg>{{msg}}</div>{% endif %}
<form method=post enctype=multipart/form-data class=card id=s568add style="margin:14px 18px;display:flex;flex-direction:column;gap:10px;max-width:660px">
<label style="font-size:14px">The file<input type=file name=paper_file accept=".pdf,.jpg,.jpeg,.png,.webp,.heic,application/pdf,image/jpeg,image/png,image/webp,image/heic" style="display:block;margin-top:4px"></label>
<b style="font-size:14px">What is it?</b>
<label style="font-size:14px;display:flex;gap:6px;align-items:center"><input type=radio name=what value=paper checked style="width:auto"> A paper for the scan app, on the lane</label>
<div style="margin-left:24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap"><select name=lane>{% for k, w in lanes %}<option value="{{k}}">{{w}}</option>{% endfor %}</select>
<label style="font-size:14px;display:flex;gap:6px;align-items:center"><input type=checkbox name=challan value=1 style="width:auto"> It is a challan (goods came; the bill comes later)</label></div>
<label style="font-size:14px;display:flex;gap:6px;align-items:center"><input type=radio name=what value=pexp style="width:auto"> Sanjeevni pharmacy expense — paid by Dr MK's card</label>
<div style="margin-left:24px;display:flex;gap:12px;flex-wrap:wrap"><label style="font-size:13px">Paid on<input name=paid_on placeholder="dd-mm-yyyy" style="display:block;width:130px"></label><label style="font-size:13px">Amount<input name=amount placeholder="₹" inputmode=decimal style="display:block;width:120px"></label></div>
<div class=muted style="margin-left:24px;font-size:12px">Filed on the pharmacy lane as a pharmacy expense — never a medicine bill, so Sanjeevni's register never pairs it with a Marg bill — and marked paid by your card. It shows on The month as “Sanjeevni — pharmacy expenses”, never in the clinic's totals. No card number is asked for or kept.</div>
<label style="font-size:14px">Note <span class=muted>(optional)</span><input name=note maxlength=120 style="display:block;width:100%"></label>
<button class=go style="min-height:40px;font-size:15px">Save</button></form></body></html>"""


def _s568_lanes():
    """The intake's own lane choices for this user (asset_register._intake_lanes_s544), in the app's words."""
    role = ""
    try:
        role = g.user["role"] or ""
    except Exception:                                                # noqa: BLE001
        pass
    out = []
    for k in AR._intake_lanes_s544(role):
        w = (getattr(AR, "LANE_WORD", {}) or {}).get(k) or AR.LANES[k][0]
        out.append((k, w))
    return out


def add_page():
    """GET / POST /desk/add -- S568 item 7: a PDF or an image through the intake's own code path (_create_intake_bill: the
    same storage, stamp, fingerprint double check and reading). The plain form offers the intake's choices only (the lanes
    this user has, the challan tick). The preset: the pharmacy lane, kind 'Pharmacy expense' written before the intake's
    first commit (kind_over), status captured; paid on the paper itself (bills.paid_on / paid_amount, the day and amount
    typed) with one bill_audit 'paid' {how: card}. Owner and managers; managers only while the desk is on (the _gate)."""
    lanes = _s568_lanes()
    if request.method == "GET":
        m, bad = _msg_args()
        return render_template_string(ADD_TPL, bg=_bg(), title="Add a paper from a file", lanes=lanes, msg=m, bad=bad)
    f = request.form
    fobj = request.files.get("paper_file")
    note = (f.get("note") or "").strip()[:120]
    if not (fobj and fobj.filename):
        return _back_to("s568_add", "Choose the file (a PDF or a photo). Nothing was saved.", True)
    ext = fobj.filename.rsplit(".", 1)[1].lower() if "." in fobj.filename else ""      # the intake's own reading of it
    if ext not in S568_FILE_EXT:                                    # S568 FIX1 (K1 CORRECTION 3): a PDF or a photo only
        return _back_to("s568_add", S568_FILE_REFUSED, True)
    pexp =(f.get("what") or "") == "pexp"
    if pexp:
        try:
            if not str(f.get("paid_on") or "").strip():
                raise DeskError("Type the day it was paid (dd-mm-yyyy). Nothing was saved.")
            d = typed_date(f.get("paid_on"))
            amt = _amount(f.get("amount"))
            if amt is None or amt <= 0:
                raise DeskError("Type the amount paid. Nothing was saved.")
        except DeskError as e:
            return _back_to("s568_add", str(e), True)
        bid = AR._create_intake_bill(fobj, note, "pharmacy", {}, challan=False, kind_over=PEXP)
    else:
        lane = (f.get("lane") or "").strip()
        if lane not in dict(lanes):
            return _back_to("s568_add", "Choose the lane. Nothing was saved.", True)
        bid = AR._create_intake_bill(fobj, note, lane, {}, challan=(f.get("challan") == "1"))
    if not bid:
        return _back_to("s568_add", S568_FILE_REFUSED, True)
    db = AR.get_db()
    b = _row(db, bid)
    if b["dup_of"]:
        first = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone()
        return _back_to("s568_add", "%s is the same file as %s — it is set aside as a second copy%s." % (
            _stamp(b), _stamp(first) if first else "an earlier paper", " (not marked paid)" if pexp else ""), True)
    if pexp:
        db.execute("UPDATE bills SET paid_on=?, paid_amount=? WHERE id=?", (d, amt, bid))
        AR._audit_bill(db, bid, "paid", {"how": "card", "note": "Dr MK's card", "via": "add_from_file", "on": d, "amount": amt})
        _audit_desk(db, "add_from_file", {"id": bid, "preset": "pharmacy_expense"})
        db.commit()
        return _back_to("s568_add", "Saved as %s — Sanjeevni pharmacy expense, paid by Dr MK's card (%s on %s)." % (_stamp(b), _inr(amt), _dmy(d)))
    _audit_desk(db, "add_from_file", {"id": bid, "lane": b["lane"]})
    db.commit()
    if _lane(b) == "pharmacy":
        return _back_to("s568_add", "Saved as %s on the pharmacy lane (the Sanjeevni side keeps it)." % _stamp(b))
    return redirect(url_for("s551_desk", open=bid))


# --- S568_STATIONERY_STOCK end ---


# ---------------------------------------------------------------------------------------------- the mount
''', 1),
]

# ============================================================================================ clinic_papers.py
CP_EDITS = [
    # CP1 -- the mark
    (r'''LAST = "S566"                # S566: the old challan doors check on the server; a half-read bill date takes no month
''',
     r'''LAST = "S566"                # S566: the old challan doors check on the server; a half-read bill date takes no month
STOCK = "S568"               # S568: the group Stationery & packaging; a Sanjeevni pharmacy expense is never moved by the system
''', 1),
    # CP2 (item 1, R1 C8) -- SUB
    (r'''    "others":     "Others",
''',
     r'''    "others":     "Others",
    "stationery": "Stationery & packaging",                         # S568 item 1 (D730)
''', 1),
    # CP3 -- GROUP_OF
    (r'''GROUP_OF = {"procedure": "procedure", "xray": "xray", "xray_small": "xray", "xray_11x14": "xray", "others": "others"}
''',
     r'''GROUP_OF = {"procedure": "procedure", "xray": "xray", "xray_small": "xray", "xray_11x14": "xray", "others": "others",
            "stationery": "stationery"}                                                                  # S568
''', 1),
    # CP4 -- CONSUMABLE
    (r'''CONSUMABLE = ("procedure", "xray", "xray_small", "xray_11x14", "others")
''',
     r'''CONSUMABLE = ("procedure", "xray", "xray_small", "xray_11x14", "others", "stationery")               # S568
''', 1),
    # CP5 -- GROUPS (Others' hint becomes "the rest")
    (r'''          ("others", "Others", "stationery and the rest"))
''',
     r'''          ("others", "Others", "the rest"),                                                          # S568
          ("stationery", "Stationery & packaging", "printed stationery, A4, registers, carry bags"))
''', 1),
    # CP6 (item 1) -- the papers page's chooser: its summary line
    (r'''<small>then one tap: Procedure room · X-ray films · Others</small></summary>
''',
     r'''<small>then one tap: Procedure room · X-ray films · Others · Stationery &amp; packaging</small></summary>
''', 1),
    # CP7 (item 1) -- the papers page's chooser: Others' hint, and the new button
    (r'''<button class="d6opt {{'on' if cur=='others'}}" name=subgroup value=others>Others{% if sug=='others' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>stationery and the rest</small></button>
''',
     r'''<button class="d6opt {{'on' if cur=='others'}}" name=subgroup value=others>Others{% if sug=='others' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>the rest</small></button>
<button class="d6opt {{'on' if cur=='stationery'}}" name=subgroup value=stationery>Stationery &amp; packaging{% if sug=='stationery' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>printed stationery, A4, registers, carry bags</small></button>
''', 1),
    # CP8 (R1 note 16, a call: a suggestion only, never saved without a person) -- the stationery words suggest the new group
    (r'''        return dict(kind="sub", value="others", label=SUB["others"], why="the words read on it: " + ", ".join(st[:3]))
''',
     r'''        return dict(kind="sub", value="stationery", label=SUB["stationery"], why="the words read on it: " + ", ".join(st[:3]))   # S568
''', 1),
    # CP9 (item 7, R1 C6) -- the papers page's pharmacy count leaves the pharmacy expense out
    (r'''        ph = n("SELECT COUNT(*) " + base + " AND b.lane='pharmacy'")
''',
     r'''        ph = n("SELECT COUNT(*) " + base + " AND b.lane='pharmacy' AND COALESCE(b.kind,'')<>'Pharmacy expense'")      # S568
''', 1),
    # CP10 (item 1, R1 C8) -- the papers page's consumables count
    (r'''        cs = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic' AND b.subgroup IN ('procedure','xray','xray_small','xray_11x14','others')")
''',
     r'''        cs = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic' AND b.subgroup IN ('procedure','xray','xray_small','xray_11x14','others','stationery')")   # S568
''', 1),
    # CP11 (item 1, R1 C8) -- the old month page's group list
    (r'''    if g_ in ("procedure", "xray", "others", "unsorted"):
''',
     r'''    if g_ in ("procedure", "xray", "others", "stationery", "unsorted"):          # S568
''', 1),
    # CP12 (item 7, R1 C5) -- supplier_history never learns from a pharmacy expense
    (r'''    for r in db.execute("SELECT b.id, b.vendor, b.lane, b.status, b.subgroup, b.doc_kind FROM bills b WHERE b.id<>? AND b.status<>'rejected' "
''',
     r'''    for r in db.execute("SELECT b.id, b.vendor, b.lane, b.status, b.subgroup, b.doc_kind FROM bills b WHERE b.id<>? AND b.status<>'rejected' "
                        "AND COALESCE(b.kind,'')<>'Pharmacy expense' "                                  # S568 (R1 C5)
''', 1),
    # CP13 (item 7, R1 C5) -- auto_home never moves a pharmacy expense
    (r'''    if "page_of" in b.keys() and b["page_of"]:
        return did
    key = _supplier_key(b["vendor"])
''',
     r'''    if "page_of" in b.keys() and b["page_of"]:
        return did
    if (b["kind"] or "") == "Pharmacy expense":                      # S568 (R1 C5): a Sanjeevni pharmacy expense stays put
        return did
    key = _supplier_key(b["vendor"])
''', 1),
]

# ============================================================================================ asset_register.py
AR_EDITS = [
    # AR1 (item 7, R1 C4) -- the intake's one new optional keyword (default: today's behaviour, byte for byte)
    (r'''def _create_intake_bill(fobj, note, lane=None, prefill=None, challan=False):
''',
     r'''def _create_intake_bill(fobj, note, lane=None, prefill=None, challan=False, kind_over=None):      # S568: kind_over
''', 1),
    # AR2 (item 7, R1 C4) -- the kind written in the same statement block as S531's challan line, before the first commit
    (r'''        _audit_bill(db, bid, "challan", {"lane": _lane})
    try:                                                     # S441: who is scanning (the shared login's chosen name)
''',
     r'''        _audit_bill(db, bid, "challan", {"lane": _lane})
    if kind_over:                                            # S568 item 7: the desk's "Add a paper from a file" preset only --
        # written before this function's first commit, so no reader ever sees the paper as kind 'Pharmacy' (R1 C4)
        db.execute("UPDATE bills SET kind=?, doc_kind='bill' WHERE id=?", (kind_over, bid))
        _audit_bill(db, bid, "kind", {"from": _kind, "to": kind_over, "via": "add_from_file"})
    try:                                                     # S441: who is scanning (the shared login's chosen name)
''', 1),
    # AR3 (R1 C5) -- the old edit page keeps the kind
    (r'''        kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan") else''',
     r'''        kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan", "Pharmacy expense") else''', 1),
    # AR4 (R1 C5) -- and its form says so
    (r'''{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan') %}''',
     r'''{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan','Pharmacy expense') %}''', 1),
    # AR5 (R1 C5) -- the re-lane door refuses a pharmacy expense for anyone but the owner (reception's "Galat lane" too)
    (r'''    frm = b["lane"] or KIND_LANE.get(b["kind"], "clinic")
    if g.user["role"] == "reception":''',
     r'''    frm = b["lane"] or KIND_LANE.get(b["kind"], "clinic")
    if (b["kind"] or "") == "Pharmacy expense" and g.user["role"] != "owner":      # S568 (R1 C5)
        abort(403)
    if g.user["role"] == "reception":''', 1),
    # AR6 (R1 C5) -- an owner's move of it says so in its audit
    (r'''    _audit_bill(db, bid, "relane", {"from": frm, "to": to, "status": status})
''',
     r'''    _audit_bill(db, bid, "relane", dict({"from": frm, "to": to, "status": status},
                                        **({"kind_from": "Pharmacy expense"} if (b["kind"] or "") == "Pharmacy expense" else {})))      # S568
''', 1),
    # AR6b (item 7, R1 B1) -- the old bill page: "paid by Dr MK's card" on every pharmacy-expense paper (the preset defines it)
    (r'''        sd = _s560_sd()
        if sd is None or (b["lane"] or "") == "pharmacy":
            return Markup("")
''',
     r'''        if (b["kind"] or "") == "Pharmacy expense":                  # S568 (R1 B1): the preset's words, on its own page
            return _s568_paid_line(b)
        sd = _s560_sd()
        if sd is None or (b["lane"] or "") == "pharmacy":
            return Markup("")
''', 1),
    # AR7 (item 2) -- the one menu: the owner's Stationery; a manager's Stationery diya with the switch ON
    (r'''        out.append(("s551_implants", "Implant ledger", url_for("s551_implants")))
''',
     r'''        out.append(("s551_implants", "Implant ledger", url_for("s551_implants")))
        out += _s568_menu(r)                                           # S568: nothing when stationery.py is not mounted
''', 1),
    # AR8 (R1 C12) -- the mark and the guarded mount of stationery.py, after sorting_desk's
    (r'''# --- S566_SCANAPP_LAST_FIXES end ---


# ---------------------------------------------------------------- main
''',
     r'''# --- S566_SCANAPP_LAST_FIXES end ---


# --- S568_STATIONERY_STOCK begin -- D730: the stationery list and its stock (stationery.py); Add a paper from a file (16-Oct-2026) ---
# Guarded: if stationery.py is absent or cannot load, this app runs exactly as before -- the menu item and the desk's panel give nothing.
STOCK_S568 = "S568"


def _s568_menu(role):
    """The one menu's stationery item (stationery.menu_items): the owner's Stationery; a manager's Stationery diya, switch ON."""
    try:
        _m = _sys.modules.get("stationery")
        if _m is not None and getattr(_m, "MOUNTED", False):
            return list(_m.menu_items(role))
    except Exception as _ex:                                      # noqa: BLE001
        print("S568 menu: %s" % _ex, file=_sys.stderr)
    return []


def _s568_paid_line(b):
    """R1 B1: a Sanjeevni pharmacy expense (the Aumni preset) is paid by Dr MK's card -- said on its own bill page, with the day
    and amount kept on the paper (bills.paid_on / paid_amount). No card number is ever kept."""
    try:
        bits = "paid by Dr MK's card"
        if b["paid_on"]:
            bits = "Paid %s · ₹%s · %s" % (_s559_dmy(b["paid_on"]), _inr(b["paid_amount"]) if b["paid_amount"] is not None else "—", bits)
        return Markup('<br><span id=s568card style="color:#2b6e4f">') + _s560_esc("Sanjeevni pharmacy expense — " + bits) + Markup("</span>")
    except Exception as _ex:                                      # noqa: BLE001
        print("S568 paid line: %s" % _ex, file=_sys.stderr)
        return Markup("")


try:
    import stationery as _stationery
    _stationery.init(_sys.modules[__name__])
except Exception as _ex_s568:                                  # noqa: BLE001
    print("stationery NOT mounted: %s" % _ex_s568, file=_sys.stderr)
# --- S568_STATIONERY_STOCK end ---


# ---------------------------------------------------------------- main
''', 1),
]

# ============================================================================================ packs.py (THE PARENT'S) -- build_bundle only
PK_EDITS = [
    # PK1 (item 8, R1 C3) -- every bundle takes only bills and invoices; a paper with no kind set stays in
    (r'''            xk_sql = " AND COALESCE(doc_kind,'bill') NOT IN ('receipt','statement')"
            if "challan_state" in cols:
                xk_sql += " AND NOT (COALESCE(doc_kind,'')='challan' AND COALESCE(challan_state,'awaiting')<>'final')"
''',
     r'''            xk_sql = " AND COALESCE(doc_kind,'bill')='bill'"            # S568 (D730 item 5): only bills and invoices go to the accountants
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


def cp_on_tidy(src, out):
    """--cp-on: S568's clinic_papers edits on S566's tidy comparison file (S563's item-3-only clinic_papers.py with S566's edits,
    pin c6f126aa..), for S563's tidy fetch re-run on the S568 files."""
    raw = open(src, "rb").read()
    if md5(raw)[:8] != CP_TIDY_S566:
        raise SystemExit("REFUSED: %s is %s, not S566's tidy clinic_papers.py %s" % (src, md5(raw)[:8], CP_TIDY_S566))
    text, n = apply("clinic_papers.py (the tidy comparison)", raw.decode("utf-8"), CP_EDITS)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("clinic_papers.py (tidy comparison) %s -> %s  (%d counted edits, each anchor exactly once)" % (CP_TIDY_S566, md5(text.encode("utf-8"))[:8], n))


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if "--cp-on" in sys.argv and len(a) == 2:
        return cp_on_tidy(a[0], a[1])
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    os.makedirs(out, exist_ok=True)
    plan = {"sorting_desk.py": SD_EDITS, "clinic_papers.py": CP_EDITS, "asset_register.py": AR_EDITS, "packs.py": PK_EDITS}
    built = {}
    for f, edits in plan.items():
        p = os.path.join(src, f)
        if f == "packs.py" and not os.path.exists(p):
            print("packs.py           not in the input folder -- not built (the brief: build the rest and say so)")
            continue
        raw = open(p, "rb").read()
        if md5(raw) != FROM[f]:
            if f == "packs.py":
                print("packs.py           is %s, not the pinned FROM %s -- STOPPED for that file; the rest is built" % (md5(raw)[:8], FROM[f][:8]))
                continue
            raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
        text, n = apply(f, raw.decode("utf-8"), edits)
        built[f] = (text.encode("utf-8"), n)
    for f, (b, n) in built.items():
        with open(os.path.join(out, f), "wb") as fh:
            fh.write(b)
        print("%-18s %s -> %s  (%d counted edit%s, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n, "" if n == 1 else "s"))
    shutil.copyfile(os.path.join(HERE, "stationery.py"), os.path.join(out, "stationery.py"))
    print("%-18s (new)     -> %s  (the kit's own file)" % ("stationery.py", md5(open(os.path.join(out, "stationery.py"), "rb").read())[:8]))


if __name__ == "__main__":
    main()
