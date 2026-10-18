#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s585.py -- S585_STATIONERY_ISSUE_MANY (D738): stationery.py rebuilt from the pinned live bytes (S568's TO, d11d7183) with
counted edits, each anchor found exactly once. stationery.py is the ONLY file changed. asset_register.py, sorting_desk.py (both at
drift 8, F-836), batteries.py and xray_costs.py (S582's TO), clinic_papers.py, asset_machine.py, scanner_widget.js and the parent's
packs.py are never touched.

    python3 make_s585.py <dir with the live stationery.py> <out dir>

What the edits do (the brief claude_code_briefs/S585_STATIONERY_ISSUE_MANY.md v2 with its review S585_BRIEF_R1.md, md5 706779ce...):
  E1  the docstring: what S585 adds
  E2  the marks: MANY = "S585", the switch stationery.many (absent = OFF), the history key and its by_whom
  E3  PLACES gains ("xray", "X-ray"); ONE_PLACES = PLACES[:4] -- the frozen list of the one-item screen (R1 B1)
  E4  HISTORY -- the seven lines of Shavez's sheet, by the owner's mapping (15:10 IST 18-Oct-2026), items by their EXACT names
  E5  many_on(db)
  E6  issue()'s refusal names X-ray (R1 C2)
  E7  _issue_view() -- one issue line for the owner's page (voided, before the latest count, from Shavez's sheet)
  E8  inventory(): the sheet's lines are never "this month" (C3); every line read for display (voided included), the earlier
      months, the sheet's lines (C5)
  E9  inventory(): the except branch
  E10 inventory(): the display lists
  E11 inventory(): the return
  E12 STOCK_TPL: the switch card at the top of the owner's Stationery page (R1 C1)
  E13 STOCK_TPL: the stock table's header made from the places (R1 C2)
  E14 STOCK_TPL: This month's issues with Void, the 'Show all issues' fold, the fold 'Earlier issues -- from Shavez's sheet (no date)'
  E15 DIYA_TPL: a hidden one=1 inside the form, rendered ONLY while the switch is ON and ?one=1 (so OFF renders S568's bytes)
  E16 MANY_TPL -- the many-items screen, built to the owner's mock-up (claude_code_briefs/S585_MOCKUP_Main.dc.html); its Ginti card is
      cut from DIYA_TPL itself, so it stays exactly as it is
  E17 stock_page(): the switch's state
  E18 issue_page(): ON -> the many-items screen; ?one=1 -> the one-item screen; OFF -> exactly S568's
  E19 many_post / many_switch / void_post / history_step / history_void
  E20 init(): three routes
  E21 the command line: --history <db> (the installer's data step) and --history-void <db> (its undo: marks, never deletes)
Every byte of the built stationery.py comes from the live file plus these edits (BUILD_NORM_v1)."""
import hashlib, os, sys

FROM = {"stationery.py": "d11d718392782d4a7a8b9c233363a526"}

E = []

# E1 -- the docstring
E.append(('''    Who: the owner always. A manager only while the switch stationery.issue_on is ON (absent = OFF; a row on the owner's
    Switches card). The reception login never (the app's checker gate refuses it).
"""''', '''    Who: the owner always. A manager only while the switch stationery.issue_on is ON (absent = OFF; a row on the owner's
    Switches card). The reception login never (the app's checker gate refuses it).

S585_STATIONERY_ISSUE_MANY (D738; the owner, 14:41-15:10 IST 18-Oct-2026: "develop a system where multiple items can be issued on one
screen"; Shavez's sheet STATIONARY.xlsx "so you can populate that also, and we can edit it later on if needed")
    Stationery diya with the switch stationery.many ON: one screen -- "1 · Kisko diya?" (Lab · Reception · Sanjeevni · Clinic · X-ray),
    "2 · Kya aur kitna diya?" (every active item: shelf stock, -, the number, +) and ONE "Save karo (N)": one issue per item with a
    number, through issue(), in ONE transaction (all or none) -- POST /stationery/diya/many, refused while the switch is OFF.
    The switch OFF (absent = OFF): exactly S568's one-item screen, byte for byte; ON, that screen stays at /stationery/diya?one=1.
    The switch is a card at the top of the owner's Stationery page (POST /stationery/many) -- not on the Switches card, which lives
    in sorting_desk.py and is not touched (R1 C1).
    X-ray is a place (issue(), the many-items screen, the owner's tables); the one-item screen keeps its four (ONE_PLACES, R1 B1).
    Void (the owner only, POST /stationery/void): a line is kept, struck through, and leaves the stock (stock_book ignores voided
    moves); voiding a line made before the latest count changes nothing -- the count stands. Audited in desk_audit.
    Shavez's sheet: seven lines written once by the installer (python3 stationery.py --history <db>; the key stationery.history_s585),
    each 1 s before its item's opening count, so the opening stock stands exactly; never in "this month"; listed in their own fold.
"""''', 1))

# E2 -- the marks
E.append(('''FIX = "S568_FIX1"             # K1 CORRECTIONS 1-2: the stock follows where the paper is now; the staff screen as the owner's mock-up
''', '''FIX = "S568_FIX1"             # K1 CORRECTIONS 1-2: the stock follows where the paper is now; the staff screen as the owner's mock-up
MANY = "S585"                 # S585_STATIONERY_ISSUE_MANY (D738): many items on one screen, X-ray as a place, Void, Shavez's sheet
MANY_SWITCH = "stationery.many"                  # absent = OFF: the staff page is exactly S568's one-item screen
HISTORY_KEY = "stationery.history_s585"          # set by the installer's data step when the sheet's lines are written
HISTORY_BY = "history (Shavez sheet)"            # the sheet's lines are known by this by_whom
''', 1))

# E3 -- PLACES gains X-ray; the one-item screen keeps its frozen four
E.append(('''PLACES = (("lab", "Lab"), ("reception", "Reception"), ("sanjeevni", "Sanjeevni"), ("clinic", "Clinic"))
''', '''PLACES = (("lab", "Lab"), ("reception", "Reception"), ("sanjeevni", "Sanjeevni"), ("clinic", "Clinic"), ("xray", "X-ray"))   # S585: X-ray
ONE_PLACES = PLACES[:4]       # S585 (R1 B1): the one-item screen's own frozen four -- its bytes stay S568's
''', 1))

# E4 -- the sheet's seven lines
E.append(('''UNITS = ("piece", "pack", "ream", "box", "packet", "register", "book", "file", "roll", "bundle", "set", "dozen")
''', '''UNITS = ("piece", "pack", "ream", "box", "packet", "register", "book", "file", "roll", "bundle", "set", "dozen")
# S585 s3.4: Shavez's sheet STATIONARY.xlsx by the owner's mapping (15:10 IST 18-Oct-2026) -- (the item's EXACT name, quantity, place, what)
HISTORY = (("Register 72 pages", 6, "reception", "the OPD register"),
           ("Register 104 pages", 6, "reception", "the lab register kept at reception"),
           ("Register 192 pages", 3, "lab", "the lab register"),
           ("Register 104 pages", 6, "lab", "the A/C register"),
           ("Small notebook (copy)", 2, "lab", "the expense copy"),
           ("Notebook (copy) 72 pages", 6, "sanjeevni", "Medical's daily detail"),
           ("Small notebook (copy)", 2, "xray", "X-ray"))
''', 1))

# E5 -- many_on
E.append(('''def issue_on(db):
    return (_setting(db, SWITCH, "off") or "").strip().lower() == "on"
''', '''def issue_on(db):
    return (_setting(db, SWITCH, "off") or "").strip().lower() == "on"


def many_on(db):
    """S585: the many-items screen -- absent = OFF."""
    return (_setting(db, MANY_SWITCH, "off") or "").strip().lower() == "on"
''', 1))

# E6 -- issue()'s refusal names X-ray
E.append(('''        raise ValueError("Kisko diya — Lab, Reception, Sanjeevni ya Clinic chuno.")
''', '''        raise ValueError("Kisko diya — Lab, Reception, Sanjeevni, Clinic ya X-ray chuno.")
''', 1))

# E7 -- one issue line for the owner's page
E.append(('''def inventory(db, ym):
''', '''def _issue_view(x, byid, lastc):
    """S585: one issue line for the owner's page -- voided (kept, struck through), made before the item's latest count (voiding it
    changes nothing), or one of Shavez's sheet."""
    it = byid.get(x["item_id"]) or {}
    lc = lastc.get(x["item_id"])
    voided = bool(x["voided_at"])
    return {"id": x["id"], "day": x["day"], "item": it.get("name", "?"), "unit": it.get("unit", ""), "qty": x["qty"],
            "place": PLACE_WORD.get(x["place"], x["place"]), "who": x["by_whom"] or "",
            "over": (not voided and x["stock_before"] is not None and x["qty"] > x["stock_before"] + 1e-9), "before": x["stock_before"],
            "voided": voided, "vby": x["voided_by"] or "", "vat": (x["voided_at"] or "")[:16],
            "pre": (lc is not None and x["ts"] <= lc), "hist": (x["by_whom"] or "") == HISTORY_BY}


def inventory(db, ym):
''', 1))

# E8 -- inventory(): the reads
E.append(('''        issues = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE voided_at='' AND substr(day,1,7)=? ORDER BY ts, id", (ym,))]
''', '''        issues = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE voided_at='' AND substr(day,1,7)=? AND COALESCE(by_whom,'')<>? "
                                              "ORDER BY ts, id", (ym, HISTORY_BY))]                  # S585 C3: the sheet is never "this month"
        shown = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE COALESCE(by_whom,'')<>? ORDER BY ts, id", (HISTORY_BY,))]
        hist = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE COALESCE(by_whom,'')=? ORDER BY ts, id", (HISTORY_BY,))]
        lastc = {r[0]: r[1] for r in db.execute("SELECT item_id, MAX(ts) FROM stationery_count GROUP BY item_id")}
''', 1))

# E9 -- inventory(): the except branch
E.append(('''        allines, issues, counts = [], [], []
''', '''        allines, issues, counts = [], [], []
        shown, hist, lastc = [], [], {}
''', 1))

# E10 -- inventory(): the display lists (voided lines included, struck through on the page)
E.append(('''    iss = [{"day": x["day"], "item": (byid.get(x["item_id"]) or {}).get("name", "?"), "unit": (byid.get(x["item_id"]) or {}).get("unit", ""),
            "qty": x["qty"], "place": PLACE_WORD.get(x["place"], x["place"]), "who": x["by_whom"] or "",
            "over": (x["stock_before"] is not None and x["qty"] > x["stock_before"] + 1e-9), "before": x["stock_before"]} for x in issues]
''', '''    iss = [_issue_view(x, byid, lastc) for x in shown if (x["day"] or "")[:7] == ym]                     # S585: voided lines shown, struck
    older = [_issue_view(x, byid, lastc) for x in reversed(shown) if (x["day"] or "")[:7] != ym]         # S585: the "Show all issues" fold
    hst = [_issue_view(x, byid, lastc) for x in hist]                                                     # S585: Shavez's sheet
''', 1))

# E11 -- inventory(): the return
E.append(('''    return {"rows": rows, "issues": iss, "counts": cts, "fed": sorted(fed.values(), key=lambda f: f["bid"]), "mixed": mixed_n(db, ym)}
''', '''    return {"rows": rows, "issues": iss, "counts": cts, "fed": sorted(fed.values(), key=lambda f: f["bid"]), "mixed": mixed_n(db, ym),
            "older": older, "history": hst}
''', 1))

# E12 -- STOCK_TPL: the switch card at the top
E.append(('''<div class=card id=s568mixed>''', '''<div class=card id=s585switch><form method=post action="{{url_for('s585_many')}}" style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0"><input type=hidden name=on value="{{'0' if many else '1'}}">
<b style="font-size:14px">Many items on one screen</b> <span class=muted>— Stationery diya for the staff: every item on one screen, one Save. OFF = the one-item screen.</span>
<button style="padding:4px 10px;border-radius:12px;font-size:12px;background:{{'#2b6e4f' if many else '#8a97a5'}}" title="tap to switch {{'off' if many else 'on'}}">{{'ON' if many else 'OFF'}}</button></form></div>
<div class=card id=s568mixed>''', 1))

# E13 -- STOCK_TPL: the header from the places
E.append(('''<th>Issued this month (Lab · Reception · Sanjeevni · Clinic)</th>''',
          '''<th>Issued this month ({% for k, w in places %}{{w}}{{' · ' if not loop.last}}{% endfor %})</th>''', 1))

# E14 -- STOCK_TPL: This month's issues with Void; the two folds
E.append(('''<div class=card><b>This month's issues</b>{% if inv.issues %}<table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th></tr>
{% for x in inv.issues %}<tr><td>{{dmy(x.day)}}</td><td>{{x.item}}</td><td>{{q(x.qty)}} {{x.unit}}</td><td>{{x.place}}</td><td class=muted>{{x.who}}</td><td>{% if x.over %}<span class="badge amber">above stock ({{q(x.before)}} then)</span>{% endif %}</td></tr>{% endfor %}</table>{% else %}<p class=muted>None yet.</p>{% endif %}</div>
''', '''{% macro s585row(x) %}<tr data-move="{{x.id}}"{% if x.voided %} class=s585v{% endif %}><td class=s>{{'no date' if x.hist else dmy(x.day)}}</td><td class=s>{{x.item}}</td><td class=s>{{q(x.qty)}} {{x.unit}}</td><td class=s>{{x.place}}</td><td class="s muted">{{x.who}}</td>
<td>{% if x.over %}<span class="badge amber">above stock ({{q(x.before)}} then)</span> {% endif %}{% if x.hist %}<span class=muted>from Shavez's sheet</span> {% endif %}{% if x.pre and not x.voided and not x.hist %}<span class=muted>before the latest count</span>{% endif %}</td>
<td>{% if x.voided %}<span class=muted>voided{{' by ' ~ x.vby if x.vby}} {{x.vat}}</span>{% else %}<form method=post action="{{url_for('s585_void')}}" style="margin:0" onsubmit="return confirm('Void this issue? It stays on the page, struck through.')"><input type=hidden name=id value="{{x.id}}"><button class="btn small danger">Void</button></form>{% endif %}</td></tr>{% endmacro %}
<style>.s585v td.s{text-decoration:line-through;color:#8a97a5}</style>
<div class=card id=s585issues><b>This month's issues</b> <span class=muted>— Void corrects a wrong line: it stays here, struck through, and leaves the stock. Voiding an issue made before the latest count does not change the stock — the count stands.</span>
{% if inv.issues %}<div style="overflow:auto"><table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th><th></th></tr>
{% for x in inv.issues %}{{s585row(x)}}{% endfor %}</table></div>{% else %}<p class=muted>None yet.</p>{% endif %}</div>
<details class=card id=s585older><summary><b>Show all issues</b> <span class=muted>— the earlier months ({{inv.older|length}})</span></summary>
{% if inv.older %}<div style="overflow:auto"><table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th><th></th></tr>
{% for x in inv.older %}{{s585row(x)}}{% endfor %}</table></div>{% else %}<p class=muted>None.</p>{% endif %}</details>
{% if inv.history %}<details class=card id=s585hist><summary><b>Earlier issues — from Shavez's sheet (no date)</b> <span class=muted>({{inv.history|length}}) — issued before the opening count: not in this month's figures, and they do not change the stock</span></summary>
<div style="overflow:auto"><table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th><th></th></tr>
{% for x in inv.history %}{{s585row(x)}}{% endfor %}</table></div></details>{% endif %}
''', 1))

# E15 -- DIYA_TPL: the hidden one=1 (rendered only while the switch is ON and ?one=1)
E.append(('''<button class="btn s568save">Save</button></form></div>''',
          '''{% if one %}<input type=hidden name=one value=1>{% endif %}<button class="btn s568save">Save</button></form></div>''', 1))

# E16 -- MANY_TPL, after DIYA_TPL
E.append(('''

def _href(bid):
''', '''

# S585: the many-items screen, built to the owner's mock-up (claude_code_briefs/S585_MOCKUP_Main.dc.html, 390 px wide): the title, the
# line "Ek baar mein kai cheezein — sirf jo diya, uska number likho"; "1 · Kisko diya?" -- five buttons in a three-column grid, at least
# 48 px tall; "2 · Kya aur kitna diya?" -- one row per active item: its name, "shelf pe <stock> <unit>", a 44 px "−", the number (a box
# that can be typed in), a 44 px "+"; a row with a number is green; the line of what will be saved; ONE "Save karo (N)" -- grey until a
# place and a number are chosen, and disabled on the first tap (R1 C7). The Ginti card below is DIYA_TPL's own, cut from it.
GINTI_TPL = DIYA_TPL[DIYA_TPL.index("<div class=card><b>Ginti</b>"):DIYA_TPL.rindex("{% endif %}")]
MANY_JS = r"""<script>(function(){var f=document.getElementById('s585form');if(!f)return;
var sv=document.getElementById('s585save'),sm=document.getElementById('s585sum');
function val(i){var s=String(i.value||'').replace(/,/g,'').trim();if(!s)return 0;var v=Number(s);return (isFinite(v)&&v>=0)?v:NaN;}
function upd(){var pl=f.querySelector('input[name=place]:checked'),ch=[],bad=[];
Array.prototype.forEach.call(f.querySelectorAll('.s585row'),function(r){var i=r.querySelector('input'),v=val(i);
if(isNaN(v)){bad.push(i.value);r.classList.remove('on');return;}r.classList.toggle('on',v>0);if(v>0)ch.push(r.getAttribute('data-name')+' '+v);});
var pw=pl?pl.nextElementSibling.textContent:'';
if(bad.length){sm.textContent='“'+bad[0]+'” number nahi hai — theek karo.';}
else if(!ch.length){sm.textContent=pw?('Abhi kuch nahi chuna → '+pw):'Abhi kuch nahi chuna.';}
else{sm.textContent=ch.length+(ch.length==1?' cheez':' cheezein')+' · '+ch.join(', ')+(pw?' → '+pw:' — Kisko diya chuno');}
var ready=!!pl&&ch.length>0&&!bad.length;sv.disabled=!ready;sv.textContent=ready?('Save karo ('+ch.length+')'):'Save karo';}
f.addEventListener('click',function(e){var b=e.target.closest?e.target.closest('button'):null;if(!b||b.type!=='button')return;
var i=b.parentNode.querySelector('input'),v=val(i);if(isNaN(v))v=0;v=v+(b.classList.contains('s585plus')?1:-1);i.value=v>0?String(v):'';upd();});
f.addEventListener('input',upd);f.addEventListener('change',upd);
f.addEventListener('submit',function(e){if(sv.disabled||f.getAttribute('data-sent')){e.preventDefault();return;}
f.setAttribute('data-sent','1');sv.disabled=true;sv.textContent='Save ho raha hai…';});
window.addEventListener('pageshow',function(){f.removeAttribute('data-sent');upd();});upd();})();</script>"""
MANY_TPL = """<style>
#s585many{max-width:560px;box-sizing:border-box}
#s585many .s585h{font-size:16px;font-weight:700;color:#2c4258;margin:14px 0 8px}
#s585many .s585grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
#s585many .s585place{position:relative;display:block;margin:0}
#s585many .s585place input{position:absolute;opacity:0;width:1px;height:1px;margin:0;padding:0}
#s585many .s585place span{display:flex;align-items:center;justify-content:center;min-height:48px;box-sizing:border-box;padding:0 4px;border:2px solid #c3ced9;border-radius:12px;background:#fff;font-size:16px;font-weight:600;color:#1d2733;text-align:center;cursor:pointer;user-select:none}
#s585many .s585place input:checked+span{border-color:#1f4e79;background:#1f4e79;color:#fff}
#s585many .s585place input:focus-visible+span{outline:2px solid #9db8d4;outline-offset:2px}
#s585many .s585row{display:flex;align-items:center;gap:10px;padding:10px 12px;margin:0 0 8px;border-radius:12px;background:#fff;border:1px solid #d5dde5}
#s585many .s585row.on{background:#eaf4ec;border-color:#7fb38e}
#s585many .s585nm{flex:1 1 auto;min-width:0}
#s585many .s585nm b{display:block;font-size:15px;font-weight:600;color:#1d2733;overflow-wrap:anywhere}
#s585many .s585nm span{display:block;font-size:13px;color:#4a5866}
#s585many .s585ctl{display:flex;align-items:center;gap:6px;flex:0 0 auto}
#s585many .s585ctl button{width:44px;height:44px;min-height:44px;padding:0;border-radius:10px;font-size:22px;line-height:1}
#s585many .s585minus{background:#fff;color:#1d2733;border:1px solid #b7c3cf}
#s585many .s585plus{background:#e8f0f8;color:#1f4e79;border:1px solid #1f4e79}
#s585many .s585ctl input{width:52px;max-width:52px;min-height:44px;margin:0;padding:4px;text-align:center;font-size:18px;font-weight:700}
#s585many .s585foot{position:sticky;bottom:0;background:#fff;border-top:1px solid #d5dde5;padding:12px 0 4px;margin-top:6px}
#s585many .s585sum{font-size:14px;color:#33414f;margin:0 0 8px}
#s585many .s585save{display:block;width:100%;min-height:52px;font-size:17px;font-weight:700;border-radius:12px;background:#1e6b35}
#s585many .s585save:disabled{background:#9aa6b2;cursor:default}
</style>
<h2 style="margin-bottom:4px">Stationery diya</h2>
{% if not ok %}<div class=card><p style="font-size:17px">{{off}}</p></div>{% else %}
<p class=muted style="margin-top:0;font-size:14px">Ek baar mein kai cheezein — sirf jo diya, uska number likho.</p>
<div class=card id=s585many><form method=post action="{{url_for('s585_issue_many')}}" id=s585form>
<div class=s585h style="margin-top:0">1 · Kisko diya?</div>
<div class=s585grid role=radiogroup aria-label="Kisko diya">{% for k, w in places %}<label class=s585place><input type=radio name=place value="{{k}}"><span>{{w}}</span></label>{% endfor %}</div>
<div class=s585h>2 · Kya aur kitna diya?</div>
{% for i in rows %}<div class=s585row data-item="{{i.id}}" data-name="{{i.name}}"><div class=s585nm><b>{{i.name}}</b><span>shelf pe {{q(i.stock)}} {{i.unit}}</span></div><div class=s585ctl><button type=button class=s585minus aria-label="Ek kam">−</button><input name="q{{i.id}}" inputmode=decimal autocomplete=off placeholder=0 aria-label="{{i.name}}: kitna"><button type=button class=s585plus aria-label="Ek zyada">+</button></div></div>
{% endfor %}{% if not rows %}<p class=muted>List mein abhi koi cheez nahi hai.</p>{% endif %}
<div class=s585foot><p class=s585sum id=s585sum>Abhi kuch nahi chuna.</p><button class="btn s585save" id=s585save disabled>Save karo</button></div></form>
<p class=muted style="margin:10px 0 0">Ek-ek cheez dena ho to: <a href="{{url_for('s568_issue', one=1)}}">purana screen</a></p></div>
""" + MANY_JS + "\\n" + GINTI_TPL + "{% endif %}"


def _href(bid):
''', 1))

# E17 -- stock_page(): the switch's state
E.append(('''                   rs=rs, plain=_plain, href=_href, dmy=_dmy, active_n=len([r for r in inv["rows"] if r["active"]]),
''', '''                   rs=rs, plain=_plain, href=_href, dmy=_dmy, active_n=len([r for r in inv["rows"] if r["active"]]), many=many_on(db),
''', 1))

# E18 -- issue_page(): ON -> the many-items screen; ?one=1 -> the one-item screen; OFF -> exactly S568's
E.append(('''        return redirect(url_for("s568_issue"))
    return AR.page(DIYA_TPL, ok=ok, off=OFF_LINE, items=item_rows(db, active_only=True), places=PLACES,
                   flow=AR._flow("Stationery diya", url_for("s568_stock") if _role() == "owner" else url_for("dashboard")))
''', '''        return redirect(url_for("s568_issue", one=1) if (request.form.get("one") == "1" and many_on(db)) else url_for("s568_issue"))
    many = many_on(db)                                               # S585: absent = OFF
    one = many and request.args.get("one") == "1"
    flow = AR._flow("Stationery diya", url_for("s568_stock") if _role() == "owner" else url_for("dashboard"))
    if many and not one:
        return many_page(db, ok, flow)
    return AR.page(DIYA_TPL, ok=ok, off=OFF_LINE, items=item_rows(db, active_only=True), places=ONE_PLACES, one=one, flow=flow)


def many_page(db, ok, flow):
    """S585: the many-items screen -- every active item with its shelf stock (one stock_book read)."""
    items = item_rows(db, active_only=True)
    book = stock_book(db) if ok else {}
    rows = [{"id": i["id"], "name": i["name"], "unit": i["unit"], "stock": book.get(i["id"], {"stock": 0.0})["stock"]} for i in items]
    return AR.page(MANY_TPL, ok=ok, off=OFF_LINE, rows=rows, items=items, places=PLACES, q=lambda x: _plain(x) if x is not None else "—",
                   flow=flow)
''', 1))

# E19 -- the many-items save, the switch, Void, the sheet's data step and its undo
E.append(('''def menu_items(role):
''', '''def done_many(done, place):
    """S585: 'Save ho gaya ✓ — Register 192 pages 2 piece, Small notebook (copy) 1 piece → Lab'."""
    return "Save ho gaya ✓ — %s → %s" % (", ".join("%s %s %s" % (it["name"], _plain(q), it["unit"] or "") for it, q in done).replace("  ", " "),
                                        PLACE_WORD.get(place, place))


def many_post():
    """S585 (R1 C7): the many-items screen's ONE Save -- one issue per item with a number, through issue(), then ONE commit (all or
    none). Refused while stationery.many is OFF; a place and at least one number are needed (the server checks, not the grey button)."""
    db = AR.get_db()
    if not may_issue(db):
        return OFF_LINE, 403
    back = url_for("s568_issue")
    if not many_on(db):
        flash("Yeh screen abhi band hai. Kuch save nahi hua.")
        return redirect(back)
    place = (request.form.get("place") or "").strip()
    act = item_rows(db, active_only=True)
    got, bad = {}, []
    for k, v in request.form.items():
        if k.startswith("q") and k[1:].isdigit() and str(v).strip():
            n = _num(v)
            if n is None or n < 0:
                bad.append(v)
            elif n > 0:
                got[int(k[1:])] = n
    if bad:
        flash("“%s” number nahi hai. Kuch save nahi hua." % str(bad[0])[:20])
        return redirect(back)
    if place not in PLACE_WORD:
        flash("Kisko diya — chuno. Kuch save nahi hua.")
        return redirect(back)
    if not got:
        flash("Kuch nahi chuna — kuch save nahi hua.")
        return redirect(back)
    order = [i["id"] for i in act] + sorted(k for k in got if k not in {i["id"] for i in act})
    done = []
    try:
        for iid in order:
            if iid in got:
                it, q, _before = issue(db, iid, got[iid], place)
                done.append((it, q))
        db.commit()
    except (ValueError, sqlite3.Error) as e:
        db.rollback()
        flash("%s Kuch save nahi hua." % (str(e) if isinstance(e, ValueError) else "Database ne mana kiya."))
        return redirect(back)
    flash(done_many(done, place))
    return redirect(back)


def many_switch():
    """S585 (R1 C1): the owner's ON / OFF for the many-items screen -- the shape of sorting_desk.switch()."""
    on = request.form.get("on") or ""
    if on not in ("0", "1"):
        abort(400)
    db = AR.get_db()
    old = _setting(db, MANY_SWITCH, "off")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (MANY_SWITCH, "on" if on == "1" else "off"))
    _audit(db, "stationery_many_switch", {"from": old, "to": "on" if on == "1" else "off"})
    db.commit()
    flash("Many items on one screen: %s. Stationery diya now shows %s." % (("ON", "every item on one screen") if on == "1" else ("OFF", "the one-item screen")))
    return redirect(url_for("s568_stock"))


def void_post():
    """S585 s3.3: the owner voids one issue line -- kept (voided_at / voided_by), struck through, out of the stock. A line made before
    the item's latest count changes nothing: the count stands."""
    db = AR.get_db()
    back = url_for("s568_stock") + "#s585issues"
    try:
        mid = int(request.form.get("id") or 0)
    except ValueError:
        mid = 0
    r = db.execute("SELECT * FROM stationery_move WHERE id=?", (mid,)).fetchone()
    if r is None:
        flash("That issue is not on the list — nothing changed.")
        return redirect(back)
    if r["voided_at"]:
        flash("That issue was already voided — nothing changed.")
        return redirect(back)
    it = next((i for i in item_rows(db) if i["id"] == r["item_id"]), None) or {"name": "?", "unit": ""}
    lc = db.execute("SELECT MAX(ts) FROM stationery_count WHERE item_id=?", (r["item_id"],)).fetchone()[0]
    pre = lc is not None and r["ts"] <= lc
    db.execute("UPDATE stationery_move SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (_now(), _who(), mid))
    _audit(db, "stationery_issue_voided", {"id": mid, "item": r["item_id"], "qty": r["qty"], "place": r["place"], "day": r["day"],
                                           "before_count": pre, "sheet": (r["by_whom"] or "") == HISTORY_BY})
    db.commit()
    msg = "Voided: %s %s %s to %s." % (it["name"], _plain(r["qty"]), it["unit"] or "", PLACE_WORD.get(r["place"], r["place"]))
    if pre:
        msg += " It was made before the latest count, so the stock does not change — the count stands."
    else:
        msg += " In stock now: %s %s." % (_plain(stock_of(db, r["item_id"])), it["unit"] or "")
    flash(msg.replace("  ", " "))
    return redirect(back)


def history_step(db_path, plan=None, who=HISTORY_BY, key=HISTORY_KEY, shift=-1.0, out=print):
    """S585 s3.4 (R1 C4): the installer's data step -- Shavez's sheet, once. ONE transaction (BEGIN IMMEDIATE) with its done-key,
    checked first; items by their EXACT names among the ACTIVE items; each line 1 s before its item's OPENING count (day = that count's
    day), stock_before NULL, by_whom 'history (Shavez sheet)'; an absent item, or one with no opening count, is skipped with one line;
    the stock figures are read before and after inside the transaction -- any difference rolls everything back. Returns 0 / 1."""
    plan = HISTORY if plan is None else plan
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.isolation_level = None
    try:
        con.execute("BEGIN IMMEDIATE")
        if _setting(con, key, None) is not None:
            out("history: already done (%s is set) -- nothing written" % key)
            con.execute("ROLLBACK")
            return 0
        items = item_rows(con, active_only=True)
        allit = {i["id"]: i for i in item_rows(con)}
        before = stock_book(con)
        at = _now()
        wrote = 0
        for name, qty, place, what in plan:
            it = next((i for i in items if i["name"] == name), None)
            if it is None:
                out("history: skipped -- no active item named '%s' (%s to %s, %s)" % (name, _plain(qty), PLACE_WORD.get(place, place), what))
                continue
            oc = con.execute("SELECT * FROM stationery_count WHERE item_id=? AND opening=1 ORDER BY ts, id LIMIT 1", (it["id"],)).fetchone()
            if oc is None:
                out("history: skipped -- '%s' has no opening count yet (%s to %s, %s)" % (name, _plain(qty), PLACE_WORD.get(place, place), what))
                continue
            if con.execute("SELECT 1 FROM stationery_move WHERE item_id=? AND place=? AND qty=? AND by_whom=? LIMIT 1",
                           (it["id"], place, float(qty), who)).fetchone():
                out("history: already there -- %s %s to %s" % (name, _plain(qty), PLACE_WORD.get(place, place)))
                continue
            con.execute("INSERT INTO stationery_move(item_id, qty, place, day, ts, stock_before, by_whom, at) VALUES(?,?,?,?,?,NULL,?,?)",
                        (it["id"], float(qty), place, oc["day"], float(oc["ts"]) + shift, who, at))
            wrote += 1
            out("history: wrote %s %s %s -> %s (%s); day %s, 1 s before its opening count" % (name, _plain(qty), it["unit"] or "",
                                                                                         PLACE_WORD.get(place, place), what, oc["day"]))
        after = stock_book(con)
        moved = sorted(i for i in set(before) | set(after)
                       if abs(before.get(i, {"stock": 0.0})["stock"] - after.get(i, {"stock": 0.0})["stock"]) > 1e-9)
        for i in sorted(before, key=lambda k: (allit.get(k) or {}).get("name", "").lower()):
            if before[i].get("counted"):
                out("stock: %s -- before %s, after %s" % ((allit.get(i) or {}).get("name", "?"), _plain(before[i]["stock"]),
                                                          _plain(after.get(i, {"stock": 0.0})["stock"])))
        if moved:
            con.execute("ROLLBACK")
            out("history: REFUSED -- a stock figure changed (%s); rolled back, nothing written" % ", ".join((allit.get(i) or {}).get("name", "?") for i in moved))
            return 1
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, "%d rows %s" % (wrote, at)))
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                        (at, who, "stationery_history_s585", json.dumps({"rows": wrote}, ensure_ascii=False)))
        except sqlite3.Error:
            pass
        con.execute("COMMIT")
        out("history: %d row(s) written; %s set; the stock figures before = after (%d counted items)" % (wrote, key, len([i for i in before if before[i].get("counted")])))
        return 0
    except Exception:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def history_void(db_path, who="undo S585", out=print):
    """S585: the data step's undo -- Shavez's lines VOIDED (marked, never deleted); the key stays, so a re-install writes nothing."""
    con = sqlite3.connect(db_path, timeout=30)
    try:
        n = con.execute("UPDATE stationery_move SET voided_at=?, voided_by=? WHERE by_whom=? AND voided_at=''", (_now(), who, HISTORY_BY)).rowcount
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)", (_now(), who, "stationery_history_voided", json.dumps({"rows": n})))
        except sqlite3.Error:
            pass
        con.commit()
    finally:
        con.close()
    out("history: %d line(s) of Shavez's sheet voided (kept, struck through)" % n)
    return 0


def menu_items(role):
''', 1))

# E20 -- init(): the three routes
E.append(('''    app.add_url_rule("/stationery/count", "s568_count", ar.checker_required(count_post), methods=["POST"])
''', '''    app.add_url_rule("/stationery/count", "s568_count", ar.checker_required(count_post), methods=["POST"])
    app.add_url_rule("/stationery/diya/many", "s585_issue_many", ar.checker_required(many_post), methods=["POST"])    # S585
    app.add_url_rule("/stationery/many", "s585_many", ar.owner_required(many_switch), methods=["POST"])              # S585
    app.add_url_rule("/stationery/void", "s585_void", ar.owner_required(void_post), methods=["POST"])                # S585
''', 1))

# E21 -- the command line
E.append(('''        print("stationery %s: tables ready (%s)" % (VERSION, ", ".join(ensure_path(sys.argv[2]))))
    else:
''', '''        print("stationery %s: tables ready (%s)" % (VERSION, ", ".join(ensure_path(sys.argv[2]))))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--history":          # S585: the installer's data step (Shavez's sheet, once)
        sys.exit(history_step(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--history-void":     # S585: its undo -- voids those lines, never deletes
        sys.exit(history_void(sys.argv[2]))
    else:
''', 1))


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(name, text, edits):
    n = 0
    for old, new, cnt in edits:
        k = text.count(old)
        if k != cnt:
            raise SystemExit("REFUSED: an anchor in %s was found %d times, not %d: %r" % (name, k, cnt, old[:70]))
        text = text.replace(old, new)
        n += 1
    return text, n


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    os.makedirs(out, exist_ok=True)
    f = "stationery.py"
    with open(os.path.join(src, f), "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM[f]:
        raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
    text, n = apply(f, raw.decode("utf-8"), E)
    b = text.encode("utf-8")
    with open(os.path.join(out, f), "wb") as fh:
        fh.write(b)
    print("%-15s %s -> %s  (%d counted edits, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n))


if __name__ == "__main__":
    main()
