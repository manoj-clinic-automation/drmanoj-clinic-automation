# -*- coding: utf-8 -*-
"""edits_s715.py -- S715_DESK_ITEM_LINES: the counted edits on /root/assetapp/sorting_desk.py (FROM 35fdd6c5, S674's TO).

Each edit is (name, old, new): `old` must occur EXACTLY ONCE in the file it is applied to, or make_s715.py refuses and writes
nothing. Two edits replace a whole JavaScript function between two markers (BETWEEN): the text from `start` up to (not including)
`end`, each marker once.

What the desk gains (the owner's mock-up https://claude.ai/artifact/XpbAyqQAyCimRnv3dz1ECm, his 'build' 10:09 IST 06-Nov-2026):
  * the supplier picked from a searchable list of the known suppliers (/desk/api/suppliers); a typed name that is not picked is not
    taken (Save says so); a new supplier whose first word matches a known one is warned;
  * the date from a calendar (type=date; Scan day and Today buttons); the Read line shows it dd-mm-yyyy;
  * the stationery lines: + Add a line, x to remove, a searchable item list with a tick, "+ Add <name> to the list" with unit and
    rate in place, the rate optional (the owner's alone, as S674 keeps rates off Shavez's screens), the lines total against the
    paper; a listed supplier's challan (Variety Stationers) sorted on the desk too, each line Clinic or NK Pathology (S674's sides);
    every line NK -> NK Pathology is chosen instead; both -> the paper is marked mixed;
  * the procedure room lines: the same searchable product list in place of the long drop-down;
  * "Read it again" on a paper nothing could be read from (the app's own /bills/<id>/reread); the empty boxes fill by themselves.
"""

KIT = "S715_DESK_ITEM_LINES"

# ------------------------------------------------------------------------------------------------ the server (Python) edits
PY_CONST = ('PROCROOM_S635 = "S635"',
            'ITEMS = "S715"                # S715_DESK_ITEM_LINES: the supplier list, the calendar, the stationery lines, Read it again\n'
            'PROCROOM_S635 = "S635"')

PY_CFG = ('    cfg["open"], cant = _s559_open(db, owner, request.args.get("open"))',
          '    cfg.update(_s715_cfg(owner))                                     # S715: the supplier list, Read it again, the units\n'
          '    cfg["open"], cant = _s559_open(db, owner, request.args.get("open"))')

PY_ROUTE = ('    app.add_url_rule("/desk/add", "s568_add"',
            '    app.add_url_rule("/desk/api/suppliers", "s715_suppliers", cr(_gate(api_suppliers)))                  # S715\n'
            '    app.add_url_rule("/desk/add", "s568_add"')

PY_PANEL = ('        out["stk"] = st.panel(db, b, rd)\n',
            '        out["stk"] = st.panel(db, b, rd)\n'
            '        _s715_stk(db, b, st, out["stk"], owner)                      # S715: a listed supplier; each saved line\'s side\n')

PY_SAVE = ('                msgs += st.save_lines(db, b, p.get("st_lines") or [], _who())\n',
           '                msgs += st.save_lines(db, b, _s715_lines(db, b, p.get("st_lines") or []), _who())      # S715: sides kept only on the listed flow\n'
           '                _s715_day(db, _row(db, bid))                                 # S715: a listed challan\'s lines carry its own date\n')

PY_LISTED = ('        if "st_lines" in p:\n'
             '            raise DeskError("%s is %s\'s — its lines are sorted on the Stationery page, not here. Nothing was saved." % (_stamp(b), b["vendor"]))\n',
             '        if "st_lines" in p:                                         # S715: sorted on the desk too -- each line Clinic or NK\n'
             '            _s715_sides(db, b, p.get("st_lines") or [])\n')

PY_BLOCK = ('# ---------------------------------------------------------------------------------------------- the mount\n',
            r'''# ---------------------------------------------------------------------------------------------- S715_DESK_ITEM_LINES
_S715_HIDE = ("personal", "resume", "patient_paper")      # a person's papers: their names are never offered as suppliers
_S715_UNITS = ("piece", "pack", "packet", "ream", "box", "roll", "register", "book", "file", "bundle", "set", "dozen")


def _s715_cfg(owner):
    """S715: the page's new addresses -- the supplier list, Read it again (the app's own re-read door) -- and the stationery units."""
    st = _s568_st()
    rr = ""
    try:
        if "bill_reread" in AR.app.view_functions:
            rr = url_for("bill_reread", bid=0)
    except Exception:                                                # noqa: BLE001
        rr = ""
    return {"sup715": url_for("s715_suppliers"), "reread": rr, "units": list(getattr(st, "UNITS", None) or _S715_UNITS)}


def supplier_list(db, owner=True):
    """S715: the known suppliers -- one per supplier key (clinic_papers' first-two-words rule, the desk's _key), named as most often
    written, most used first, from SORTED papers only (accepted, filed, or a draft a person has put in a section -- a challan waiting
    for its bill); a listed stationery supplier always. Never the pharmacy lane or Other documents, a second scan or
    a set-aside paper, a person's papers (Personal, Resumes, a patient's), the owner's expense lane for anyone but the owner, the
    owner's own name. The suppliers set how they bill (challan_supplier) join with no paper.
    A listed stationery supplier (S674) is marked: its lines carry Clinic or NK."""
    lanes = ("pharmacy", "other_doc") if owner else ("pharmacy", "other_doc", "owner_expense")
    try:                                                             # a SORTED paper only (accepted / filed): a paper still waiting may carry a
        rows = db.execute("SELECT vendor, COUNT(*) FROM bills WHERE vendor IS NOT NULL AND TRIM(vendor)<>'' AND dup_of IS NULL "      # patient's name read as the vendor
                          "AND (status IN ('approved','captured') OR (status='draft' AND COALESCE(subgroup,'')<>'')) AND COALESCE(kind,'')<>'Pharmacy' "
                          "AND COALESCE(lane,'clinic') NOT IN (%s) AND COALESCE(subgroup,'') NOT IN (?,?,?) GROUP BY vendor"
                          % ",".join("?" * len(lanes)), lanes + _S715_HIDE).fetchall()
    except sqlite3.Error:
        rows = []
    by = {}
    for v, n in rows:
        v = re.sub(r"\s+", " ", str(v or "")).strip()
        k = _key(v)
        if not k:
            continue
        try:
            if own_name(db, v):
                continue
        except Exception:                                            # noqa: BLE001
            pass
        e = by.setdefault(k, {"n": 0, "names": {}})
        e["n"] += int(n or 0)
        e["names"][v] = e["names"].get(v, 0) + int(n or 0)
    md = {}
    try:
        for k, nm, mode in db.execute("SELECT supplier_key, name, mode FROM challan_supplier"):
            md[k] = mode or ""
            if k and k not in by and (nm or "").strip():
                by[k] = {"n": 0, "names": {nm.strip(): 0}}
    except sqlite3.Error:
        pass
    st = _s568_st()
    listed = set()
    try:
        if st is not None and hasattr(st, "suppliers"):
            listed = set(st.suppliers(db))
    except Exception:                                                # noqa: BLE001
        listed = set()
    for k in listed:                                                 # a listed supplier is always offered, named from its papers
        if k and k not in by:
            nm = ""
            try:
                for (v,) in db.execute("SELECT vendor FROM bills WHERE vendor IS NOT NULL AND TRIM(vendor)<>'' AND dup_of IS NULL "
                                       "AND COALESCE(lane,'clinic')<>'pharmacy' ORDER BY id DESC LIMIT 5000"):
                    if _key(v) == k:
                        nm = re.sub(r"\s+", " ", v).strip()
                        break
            except sqlite3.Error:
                nm = ""
            by[k] = {"n": 0, "names": {nm or k.title(): 0}}
    words = dict(MODES)
    out = []
    for k, e in by.items():
        low = {}                                                     # one spelling whatever its capitals; the commonest, then the shortest
        for v, n in e["names"].items():
            g = low.setdefault(v.lower(), {"n": 0, "forms": {}})
            g["n"] += n
            g["forms"][v] = g["forms"].get(v, 0) + n
        best = sorted(low.values(), key=lambda g: (-g["n"], len(next(iter(g["forms"])))))[0]["forms"]
        name = sorted(best.items(), key=lambda kv: (-kv[1], kv[0].isupper(), kv[0]))[0][0]
        note = ["%d paper%s" % (e["n"], "" if e["n"] == 1 else "s")] if e["n"] else ["no paper yet"]
        if md.get(k):
            note.append(words.get(md[k], md[k]))
        if k in listed:
            note.append("stationery list — Clinic or NK on each line")
        out.append({"name": name, "key": k, "n": e["n"], "listed": k in listed, "note": " · ".join(note)})
    out.sort(key=lambda x: (-x["n"], x["name"].lower()))
    return out[:3000]


def api_suppliers():
    db = AR.get_db()
    return jsonify(ok=True, suppliers=supplier_list(db, _owner()))


def _s715_stk(db, b, st, stk, owner=True):
    """S715: the stationery panel learns whether the paper's supplier is listed (S674) and each saved line's side, so a re-save from the
    desk never turns an NK line into a clinic one. Never raises."""
    if not isinstance(stk, dict):
        return
    try:
        stk["listed"] = bool(_s674_listed(db, b))
        sides = {}
        for s in st.saved_lines(db, b):
            sides.setdefault(s.get("line_no"), s.get("side") or "clinic")
        for l in stk.get("lines") or []:
            l["side"] = sides.get(l.get("no"), "") if l.get("saved") else ""
        if not owner:                                                # S674: no rate on a manager's screen (the item list's rates)
            for it in stk.get("items") or []:
                it["rate"] = None
    except Exception as ex:                                          # noqa: BLE001
        stk.setdefault("listed", False)
        print("S715 panel: %s" % ex, file=sys.stderr)


def _s715_sides(db, b, lines):
    """S715 (in the Save's transaction, before any line is written): a listed supplier's challan sorted on the desk -- every chosen line
    Clinic or NK (S674: a line with no side waits); every line NK -> refused: the Stationery page places such a paper on the NK lane
    with its lines, the desk does not; both sides -> the paper is marked mixed (audited), as the Stationery page marks it."""
    chosen = [x for x in lines if isinstance(x, dict) and str(x.get("item") if x.get("item") is not None else "").strip() not in ("", "ns")]
    if not chosen:
        return
    sides = [str(x.get("side") or "").strip() for x in chosen]
    if any(s not in ("clinic", "nk") for s in sides):
        raise DeskError("%s is %s's: choose Clinic or NK Pathology on each line. Nothing was saved." % (_stamp(b), b["vendor"]))
    if all(s == "nk" for s in sides):
        raise DeskError("Every line of %s is NK Pathology's — sort it on the Stationery page, where it waits. Nothing was saved." % _stamp(b))
    if "clinic" in sides and "nk" in sides and "mixed" in b.keys() and not int(b["mixed"] or 0):
        db.execute("UPDATE bills SET mixed=1 WHERE id=?", (b["id"],))
        AR._audit_bill(db, b["id"], "mixed", {"from": 0, "to": 1, "via": "desk S715 (Clinic and NK lines)"})


def _s715_goods_listed(db, b):
    st = _s568_st()
    try:
        return bool(st is not None and hasattr(st, "is_goods") and st.is_goods(b) and _s674_listed(db, b))
    except Exception:                                                # noqa: BLE001
        return False


def _s715_lines(db, b, lines):
    """S715: the lines as save_lines takes them -- a listed supplier's challan keeps each line's side (checked by _s715_sides); any
    other paper's lines are the clinic's, whatever the page sent (an NK side is never stored off the listed flow)."""
    if _s715_goods_listed(db, b):
        return lines
    st = _s568_st()
    try:
        nk = any((s.get("side") or "") == "nk" for s in st.saved_lines(db, b)) if st is not None else False
    except Exception:                                                # noqa: BLE001
        nk = False
    if nk:
        raise DeskError("%s holds NK Pathology lines -- it stays a challan of a listed supplier; change it on the Stationery page. "
                        "Nothing was saved." % _stamp(b))
    out = []
    for x in lines:
        if isinstance(x, dict):
            x = dict(x)
            x["side"] = "clinic"
        out.append(x)
    return out


def _s715_day(db, b):
    """S715: a listed supplier's challan sorted on the desk -- its lines carry the paper's own date, as the Stationery page's sort does
    (the account's and the statement's month), not the day it was sorted."""
    if not _s715_goods_listed(db, b):
        return
    pd = (b["bill_date"] or "").strip()[:10]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", pd):
        db.execute("UPDATE stationery_line SET day=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''", (pd, b["id"], b["created_at"] or ""))


# ---------------------------------------------------------------------------------------------- the mount
''')

# ------------------------------------------------------------------------------------------------ the page (HTML / CSS / JS)
CSS = ('#app>.top{padding:5px 18px}\n</style></head>',
       '#app>.top{padding:5px 18px}\n'
       '.pk715{position:relative;display:inline-block;flex:1 1 200px;min-width:170px}#right .pk715 input{display:block;width:100%;font-size:13px;padding:5px 6px}\n'
       '.dd715{position:absolute;left:0;right:0;top:100%;z-index:30;background:#fff;border:1px solid #b9c3cd;border-radius:6px;box-shadow:0 6px 18px rgba(20,30,40,.15);max-height:260px;overflow-y:auto}\n'
       '.o715{display:block;width:100%;text-align:left;font-size:13px;padding:8px 10px;border:0;border-bottom:1px solid #edf0f3;background:#fff;color:#1f2a36;cursor:pointer;min-height:36px}.o715:hover{background:#eaf2fa}.o715 small{display:block;color:#5b6875;font-size:11px}.o715.add{color:#2b5d8a;font-weight:600}\n'
       '.l715{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:flex-end;border-top:1px solid #e6ebf0;padding:6px 0 4px}\n'
       '#right .n715{display:flex;flex-direction:column;font-size:11px;color:#5b6875;margin:0}#right .n715 input,#right .n715 select{width:84px;font-size:13px;padding:4px}#right .n715 select{width:auto}\n'
       '.g715{color:#2b6e4f}.w715{font-size:12px;color:#8a3b12;margin-top:2px}.a715{flex-basis:100%;display:flex;flex-wrap:wrap;gap:6px 8px;align-items:flex-end;border:1px dashed #b9c3cd;border-radius:6px;padding:6px 8px}#right .a715 input{font-size:13px;padding:4px}#right .a715 select{font-size:13px;padding:3px}\n'
       '.dt715{display:flex;gap:6px;flex-wrap:wrap;margin-top:3px}.dt715 .b{font-size:12px;min-height:26px;padding:2px 8px}\n'
       '</style></head>')

SUPPLIER_BOX = ('<div class=grid2><div><label>Supplier<input id=f_vendor></label>',
                '<div class=grid2><div><div class=pk715 style="display:block"><label>Supplier<input id=f_vendor autocomplete=off placeholder="type 2 letters, pick from the list"></label>'
                '<div id=sup715 class=dd715 style="display:none"></div></div><div id=supw715 class=w715 style="display:none"></div>')

SAVE_DATE = ("bill_date:$('f_date').value", "bill_date:s715date()")
FLAG_RATE = ("if(l.rate==null||l.rate===''||it.rate==null){return '';}", "if(!C.owner||l.rate==null||l.rate===''||it.rate==null){return '';}")
DATE_BOX = ('<label>Date<input id=f_date placeholder="dd-mm-yyyy"></label>',
            '<label>Date<input id=f_date type=date></label><div id=dt715 class=dt715></div>')

DRAW_DATE = ("$('f_date').value=j.date;", "$('f_date').value=d2i(j.date);")
OPEN_INIT = ("s571init(j);draw();", "s571init(j);s715init(j);draw();")
DRAW_END = ("$('supnote').textContent=j.supplier_note||'';paint();}", "$('supnote').textContent=j.supplier_note||'';s715draw(j);paint();}")
USE_IT = ("$(F[t.getAttribute('data-f')]).value=t.getAttribute('data-v');}});", "s715use(F,t.getAttribute('data-f'),t.getAttribute('data-v'));}});")
NOTHING = ("if(j.flags.nothing){f+='<div class=flag>Nothing could be read — type what you see.</div>';}",
           "if(j.flags.nothing){f+='<div class=flag>Nothing could be read — type what you see.'+s715rr(j)+'</div>';}")
GATE = ("'Choose where it goes'));}", "'Choose where it goes'));s715gate(ok);}")
SUMLINE = ("(d?' · '+esc(d):'')", "(d?' · '+esc(s715dmy(d)):'')")
STK_INIT = ("hand:l.hand,sug:l.sug,saved:l.saved};})};}S.mixed=!!j.mixed;}",
            "hand:l.hand,sug:l.sug,saved:l.saved,side:l.side||'',gone:false};})};}S.mixed=!!j.mixed;}")
PR_PICK = ("+'<select data-pri=\"'+i+'\" style=\"font-size:13px;padding:3px;max-width:230px\">'+o+'</select>'", "+pk715('pr',i,l)")

STK_PAINT = ("function s568paint(j){", "\nfunction s568body(b,j){",
             "function s568paint(j){s715stk(j);}")
STK_BODY = ("function s568body(b,j){", "\ndocument.addEventListener('input',function(e){var t=e.target;if(!S.stk",
            "function s568body(b,j){if(S.dest=='stationery'&&j.stk&&S.stk){var lis=s715listed(),both={};"
            "b.st_lines=S.stk.lines.filter(function(l){return !(l.gone&&l.hand);}).map(function(l){var it=l.gone?'ns':l.item;if(it&&it!='ns'&&l.side){both[l.side]=1;}"
            "return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,rate:l.rate,item:it,side:l.side||(lis?'':'clinic')};});"
            "if(lis&&both.clinic&&both.nk&&$('mixed')){$('mixed').checked=true;S.mixed=true;}}\n"
            " if($('mixbox')&&$('mixbox').style.display!='none'){b.mixed=!!$('mixed').checked;}}")

JS = ("// S571_BATTERIES:", r"""// S715_DESK_ITEM_LINES: the supplier from a searchable list, the date from a calendar, the stationery lines (add a line, search the
// list, add to the list with unit and rate, Clinic or NK for a listed supplier), the procedure room product search, Read it again
var S715={sup:[],keys:{},state:'',touched:false,add:-1,addName:'',addUnit:'piece',addRate:'',rr:false,dt:false,lis:null};
function k715(v){return String(v||'').toLowerCase().replace(/[-.]/g,'').replace(/[^a-z0-9 ]/g,' ').split(/\s+/).filter(function(x){return x&&['the','ms','m','s','pvt','ltd','p','co','and'].indexOf(x)<0;}).slice(0,2).join(' ');}
function s715dmy(d){var m=String(d||'').match(/^(\d{4})-(\d{2})-(\d{2})$/);return m?m[3]+'-'+m[2]+'-'+m[1]:String(d||'');}
function s715today(){var d=new Date();return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2);}
function s715init(j){S715.state=j.supplier?'ok':'';S715.touched=false;S715.add=-1;S715.addName='';S715.rr=false;S715.dt=false;S715.lis=null;}
function s715date(){var v=$('f_date').value;if(!v&&!S715.dt&&S.cur&&S.cur.date){return S.cur.date;}return v;}
function s715draw(j){var sc=d2i(j.scanned);$('dt715').innerHTML=(sc?'<button type=button class=b data-dt715="'+sc+'">Scan day '+esc(j.scanned)+'</button>':'')+'<button type=button class=b data-dt715="'+s715today()+'">Today</button>';
 $('sup715').style.display='none';s715supw();}
function s715known(v){return S715.keys[k715(v)]||null;}
function s715supw(){var v=$('f_vendor').value.trim(),w='';
 if(v&&S715.state==''){w='Pick the supplier from the list, or “+ New supplier” — a typed name alone is not taken.';}
 else if(v&&S715.state=='new'){var f=k715(v).split(' ')[0],sim=null;S715.sup.forEach(function(x){if(!sim&&f&&x.key.split(' ')[0]==f&&x.key!=k715(v)){sim=x;}});
  w=sim?'This looks like '+sim.name+' — pick it from the list: two names for one supplier split its bills and statement.':'New supplier — check the full name as printed on the paper.';}
 $('supw715').textContent=w;$('supw715').style.display=w?'block':'none';}
function s715supdd(){var v=$('f_vendor').value.trim(),q=v.toLowerCase(),dd=$('sup715'),h='',n=0,exact=false;
 var L=S715.sup.filter(function(x){var nm=x.name.toLowerCase();if(k715(v)&&x.key==k715(v)){exact=true;}return !q||nm.indexOf(q)>=0||x.key.indexOf(k715(v)||'\u0000')==0;});
 L.sort(function(a,b){var sa=a.name.toLowerCase().indexOf(q)==0?0:1,sb=b.name.toLowerCase().indexOf(q)==0?0:1;return sa-sb||b.n-a.n;});
 L.slice(0,12).forEach(function(x){h+='<button type=button class=o715 data-sp715="'+esc(x.key)+'">'+esc(x.name)+'<small>'+esc(x.note)+'</small></button>';n++;});
 if(q&&!exact){h+='<button type=button class="o715 add" data-spnew715=1>+ New supplier “'+esc(v)+'” — check the full name as printed</button>';n++;}
 if(!n&&!S715.sup.length){h='<div class=o715 style="cursor:default">The supplier list is loading…</div>';n=1;}
 dd.innerHTML=h;dd.style.display=n?'block':'none';}
function s715use(F,k,v){if(k=='date'){$('f_date').value=d2i(v);S715.dt=true;}else{$(F[k]).value=v;}if(k=='vendor'){S715.state='ok';s715supw();s715restk();}sumline();paint2();}
function s715restk(){var bx=$('st568');if(bx){bx.removeAttribute('data-for');}if(S.cur){s568paint(S.cur);}}
function s715rr(j){if(!C.reread||!j.file){return '';}return S715.rr?'':' <button type=button class=b data-rr715="'+j.id+'">Read it again</button><span id=rr715msg class=muted style="display:block;font-size:12px"></span>';}
function s715poll(id,k){var W=[20000,40000,60000];if(k>=W.length){return;}setTimeout(function(){if(!S.cur||S.cur.id!=id){return;}getJ(pu(id)).then(function(j2){if(!S.cur||S.cur.id!=id||!j2||!j2.ok){return;}var got=[];
  if(!$('f_vendor').value.trim()&&j2.supplier){$('f_vendor').value=j2.supplier;S715.state='ok';got.push('supplier');}
  if(!$('f_no').value.trim()&&j2.bill_no){$('f_no').value=j2.bill_no;got.push('number');}
  if(!$('f_date').value&&j2.date){$('f_date').value=d2i(j2.date);got.push('date');}
  if(!$('f_amt').value.trim()&&j2.amount){$('f_amt').value=j2.amount;got.push('amount');}
  if(j2.items&&j2.items!='No items read.'){$('items').textContent=j2.items;}
  if(!S715.touched&&j2.stk&&j2.stk.lines&&!j2.stk.noread){S.cur.stk=j2.stk;var mx=S.mixed;s568init(j2);S.mixed=mx;s715restk();got.push('the lines');}
  var m=$('rr715msg');if(m){m.textContent=got.length?'Read again: filled '+got.join(', ')+' — check them.':(k==W.length-1?'Still not read — type what you see.':'Asked again — the empty boxes fill in by themselves if it reads. Carry on.');}
  s715supw();sumline();paint2();if(!got.length){s715poll(id,k+1);}});},W[k]);}
function s715gate(ok){if(!ok||!S.cur){return;}var pg=$('pg_on').checked&&$('pg_no').value.trim();if(pg||S.flag=='same'||S.flag=='restore'){return;}
 var v=$('f_vendor').value.trim(),why='';if(v&&S715.state==''){why='Pick the supplier from the list';}else{why=s715linewhy();}
 if(why){$('save').disabled=true;$('save').textContent=why;}}
function s715listed(){var j=S.cur;if(!j||!j.stk){return false;}if(S.kind&&S.kind!='challan'){return false;}var v=$('f_vendor').value.trim();
 if(v!=(j.supplier||'').trim()){var x=s715known(v);return !!(x&&x.listed);}return !!j.stk.listed;}
function s715it(l){var it=null;((S.cur&&S.cur.stk&&S.cur.stk.items)||[]).forEach(function(x){if(String(x.id)==String(l.item)){it=x;}});return it;}
function s715unit(l){var it=s715it(l);return it?it.unit:(l.unit||'');}
function s715linewhy(){if(S.dest!='stationery'||!S.stk||!S.cur||!S.cur.stk){return '';}var lis=s715listed(),why='',k=0,sides={},n=0;
 S.stk.lines.forEach(function(l){if(l.gone){return;}k++;if(why||!l.item||l.item=='ns'){return;}n++;
  if(!(num(l.qty)>0)){why='Type the quantity on line '+k;return;}if(lis){if(!l.side){why='Choose Clinic or NK on line '+k;return;}sides[l.side]=1;}});
 if(!why&&lis&&n&&sides.nk&&!sides.clinic){why='Every line is NK Pathology’s — sort it on the Stationery page';}return why;}
function s715tag(i){var l=S.stk.lines[i],it=s715it(l);if(l.item=='new'){return '<span class=g715>+ new on the list: '+esc(l.name)+' ('+esc(l.unit||'piece')+') — added when you Save</span>';}
 if(l.item=='ns'){return '<span class=muted>not a stock item — counts nothing</span>';}
 if(it){return '<span class=g715>✓ '+esc(it.name)+' — on the list'+((l.sug&&!l.saved)?' (suggested — check)':'')+'</span>';}
 if(l.item){return '<span class=err>the chosen item is no longer on the list — pick another</span>';}return '<span class=muted>no item chosen yet</span>';}
function pk715(kind,i,l){var v='';if(kind=='st'){var it=s715it(l);v=it?it.name:((l.item=='new'||l.hand)?l.name:'');}
 else{((S.cur&&S.cur.pr&&S.cur.pr.items)||[]).forEach(function(x){if(String(x.id)==String(l.item)){v=x.name;}});
  if(l.item=='new'){v='+ Add to the list';}else if(l.item=='ask'){v='Not on the list — for Dr Manoj';}else if(l.item=='free'){v='Not a list item (by its name)';}}
 return '<span class=pk715><input data-pk="'+kind+':'+i+'" value="'+esc(v)+'" placeholder="search the list" autocomplete=off aria-label="'+(kind=='st'?'Item':'Product')+' on line '+(i+1)+'"><span class=dd715 style="display:none"></span></span>';}
function pk715open(el){var p=el.getAttribute('data-pk').split(':'),kind=p[0],i=+p[1],q=el.value.trim().toLowerCase(),dd=el.nextSibling,h='',exact=false;if(!S.cur){return;}
 var L=kind=='st'?((S.cur.stk||{}).items||[]):((S.cur.pr||{}).items||[]);
 L.forEach(function(x){if(x.name.toLowerCase()==q){exact=true;}});
 var M=L.filter(function(x){return !q||x.name.toLowerCase().indexOf(q)>=0;});if(q&&!M.length){var w=q.split(/\s+/);M=L.filter(function(x){var nm=x.name.toLowerCase();return w.every(function(y){return nm.indexOf(y)>=0;});});}
 M.slice(0,15).forEach(function(x){h+='<button type=button class=o715 data-pkk="'+kind+':'+i+'" data-pko="'+esc(x.id)+'">'+esc(x.name)+' <span class=muted>('+esc(x.unit||'')+')</span>'+(x.rare?' <span class=muted>rarely used</span>':'')+'</button>';});
 if(kind=='st'){if(q&&!exact){h+='<button type=button class="o715 add" data-pkk="st:'+i+'" data-pko="__new">+ Add “'+esc(el.value.trim())+'” to the list</button>';}
  else if(!q){h+='<button type=button class="o715 add" data-pkk="st:'+i+'" data-pko="__new">+ Add a new item to the list</button>';}
  h+='<button type=button class=o715 data-pkk="st:'+i+'" data-pko="ns">not a stock item</button>';}
 else{h='<button type=button class=o715 data-pkk="pr:'+i+'" data-pko="">— no product —</button>'+h;if(S.cur.pr.owner){h+='<button type=button class="o715 add" data-pkk="pr:'+i+'" data-pko="new">+ Add to the list (the name in “what it is”)</button>';}
  h+='<button type=button class=o715 data-pkk="pr:'+i+'" data-pko="ask">Not on the list — for Dr Manoj</button><button type=button class=o715 data-pkk="pr:'+i+'" data-pko="free">Not a list item (by its name)</button>';}
 dd.innerHTML=h;dd.style.display=h?'block':'none';}
function s715addf(i,l){var u='';(C.units||['piece']).forEach(function(x){u+='<option'+(S715.addUnit==x?' selected':'')+'>'+esc(x)+'</option>';});
 return '<div class=a715><b style="flex-basis:100%;font-size:12px">Add a new item to the list</b><label class=n715>Name<input data-a7n=1 value="'+esc(S715.addName)+'" style="width:200px"></label><label class=n715>Unit<select data-a7u=1>'+u+'</select></label>'
  +(C.owner?'<label class=n715>Rate ₹<input data-a7r=1 inputmode=decimal value="'+esc(S715.addRate)+'" placeholder="if known"></label>':'')
  +'<button type=button class=b data-a7ok="'+i+'">Add to the list</button><button type=button class=b data-a7no=1>Cancel</button><span class=err id=a7err></span></div>';}
function s715stk(j){var box=$('st568'),mb=$('mixbox');if(!box||!mb){return;}
 mb.style.display=((S.kind=='bill'||S.kind=='challan')&&(S.dest=='stationery'||S.dest=='lab'))?'flex':'none';$('mixed').checked=!!S.mixed;
 if(S.dest!='stationery'||!j.stk||!S.stk){box.style.display='none';return;}
 if(box.getAttribute('data-for')==String(j.id)&&box.innerHTML&&s715listed()===S715.lis){box.style.display='flex';s568flags();s715tot();return;}
 var own=!!C.owner,lis=s715listed();S715.lis=lis;
 var h='<b>Stationery lines</b><span class=muted>One line per item on the paper: search the list and pick it, then the quantity'+(own?' and the rate (if known)':'')+'. Not on the list? “+ Add … to the list” on the line.'+(lis?' This supplier’s lines: Clinic or NK Pathology on each.':'')+' A line with no item counts nothing.</span>';
 if(!j.stk.counts){h+='<div class=muted>'+esc(j.stk.why)+'.</div>';}if(j.stk.noread){h+='<div class=muted>No items read — fill the lines by hand.</div>';}
 S.stk.lines.forEach(function(l,i){if(l.gone){return;}
  h+='<div class=l715 data-l715="'+i+'">'+(l.hand?'':'<div class=muted style="font-size:12px;flex-basis:100%">On the paper: '+esc(l.name)+'</div>')+pk715('st',i,l)
   +'<label class=n715>Qty<input data-s7q="'+i+'" value="'+esc(l.qty)+'" inputmode=decimal></label><span class=muted style="font-size:12px;padding-bottom:6px">'+esc(s715unit(l))+'</span>'
   +(own?'<label class=n715>Rate ₹<input data-s7r="'+i+'" value="'+esc(l.rate==null?'':l.rate)+'" inputmode=decimal placeholder="if known"></label>':'')
   +(lis?'<label class=n715>For<select data-s7s="'+i+'"><option value=""'+(l.side?'':' selected')+'>— choose —</option><option value=clinic'+(l.side=='clinic'?' selected':'')+'>Clinic</option><option value=nk'+(l.side=='nk'?' selected':'')+'>NK Pathology</option></select></label>':'')
   +'<button type=button class=b data-s7x="'+i+'" aria-label="Remove line '+(i+1)+'" title="'+(l.hand?'Remove this line':'Take this line off: kept as not a stock item')+'">×</button>'
   +'<div style="flex-basis:100%;font-size:12px"><span id=tag715_'+i+'>'+s715tag(i)+'</span> <span class=err data-stf="'+i+'"></span></div>'+(S715.add===i?s715addf(i,l):'')+'</div>';});
 h+='<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><button type=button class=b data-s7add=1>+ Add a line</button><span id=tot715 style="font-size:13px"></span></div>';
 box.innerHTML=h;box.setAttribute('data-for',String(j.id));box.style.display='flex';s568flags();s715tot();cue();}
function s715tot(){var e=$('tot715');if(!e||!S.stk){return;}if(!C.owner){e.textContent='';return;}var sum=0,nr=0,n=0;
 S.stk.lines.forEach(function(l){if(l.gone||!l.item||l.item=='ns'){return;}n++;var q=num(l.qty),r=parseFloat(String(l.rate==null?'':l.rate).replace(/[^0-9.]/g,''));if(isFinite(r)&&q>0){sum+=q*r;}else{nr++;}});
 if(!n){e.textContent='';return;}var pa=$('f_amt').value.trim(),p=num(pa),t='Lines total '+inr(sum)+(nr?' · '+nr+' line'+(nr==1?'':'s')+' without a rate':'');
 if(pa){t+=' · paper '+inr(p)+(nr?'':(Math.abs(p-sum)<1?' · matches':' · difference '+inr(p-sum)));}e.textContent=t;e.style.color=(pa&&!nr&&Math.abs(p-sum)<1)?'#2b6e4f':'#7a4b00';}
function s715pick(kind,i,val,el){if(!S.cur){return;}if(kind=='st'){var l=S.stk.lines[i];S715.touched=true;
  if(val=='__new'){S715.add=i;S715.addName=(el&&el.value.trim())||(l.hand?l.name:'')||'';S715.addUnit=l.unit||'piece';S715.addRate=(l.rate==null?'':String(l.rate));}
  else if(val=='ns'){l.item='ns';l.sug=false;S715.add=-1;}
  else{l.item=String(val);l.sug=false;S715.add=-1;var it=s715it(l);if(it&&l.hand){l.name=it.name;}}
  s715restk();if(S715.add===i){var a=document.querySelector('[data-a7n]');if(a){a.focus();}}}
 else{var p=S.pr.lines[i];p.item=String(val);p.sug=false;var bo=$('pr634');if(bo){bo.removeAttribute('data-for');}s634paint(S.cur);}
 paint2();}
document.addEventListener('focusin',function(e){var t=e.target;if(!t||!t.getAttribute){return;}if(t.id=='f_vendor'){s715supdd();}else if(t.hasAttribute('data-pk')){pk715open(t);}});
document.addEventListener('focusout',function(e){var t=e.target;if(!t||!t.getAttribute){return;}if(t.id=='f_vendor'){setTimeout(function(){$('sup715').style.display='none';},180);}
 else if(t.hasAttribute('data-pk')){var dd=t.nextSibling;setTimeout(function(){if(dd){dd.style.display='none';}},180);}});
document.addEventListener('input',function(e){var t=e.target;if(!t||!t.getAttribute){return;}
 if(t.id=='f_vendor'){S715.state='';s715supdd();s715supw();if(S715.lis!==null&&s715listed()!=S715.lis){s715restk();}paint2();return;}
 if(t.id=='f_date'){S715.dt=true;return;}
 if(t.id=='f_amt'){s715tot();return;}
 if(t.hasAttribute('data-pk')){var p=t.getAttribute('data-pk').split(':'),i=+p[1];if(p[0]=='st'&&S.stk){var l=S.stk.lines[i];S715.touched=true;if(l.item&&l.item!='ns'){l.item='';}if(l.hand){l.name=t.value;}var g=$('tag715_'+i);if(g){g.innerHTML=s715tag(i);}}else if(p[0]=='pr'&&S.pr&&S.pr.lines[i]){S.pr.lines[i].item='';s634flags();}pk715open(t);paint2();return;}
 if(!S.stk){return;}
 if(t.hasAttribute('data-s7q')){S.stk.lines[+t.getAttribute('data-s7q')].qty=t.value;S715.touched=true;s715tot();paint2();}
 else if(t.hasAttribute('data-s7r')){S.stk.lines[+t.getAttribute('data-s7r')].rate=t.value;S715.touched=true;s715tot();}
 else if(t.hasAttribute('data-a7n')){S715.addName=t.value;}else if(t.hasAttribute('data-a7r')){S715.addRate=t.value;}});
document.addEventListener('change',function(e){var t=e.target;if(!t||!t.getAttribute){return;}if(t.id=='f_date'){S715.dt=true;return;}if(!S.stk){return;}if(t.hasAttribute('data-a7u')){S715.addUnit=t.value;return;}if(t.hasAttribute('data-s7s')){S.stk.lines[+t.getAttribute('data-s7s')].side=t.value;S715.touched=true;paint2();}});
document.addEventListener('mousedown',function(e){var t=e.target.closest?e.target.closest('[data-pko],[data-sp715],[data-spnew715]'):null;if(!t){return;}e.preventDefault();
 if(t.hasAttribute('data-pko')){var p=t.getAttribute('data-pkk').split(':');var el=document.querySelector('[data-pk="'+p[0]+':'+p[1]+'"]');t.parentNode.style.display='none';s715pick(p[0],+p[1],t.getAttribute('data-pko'),el);return;}
 if(t.hasAttribute('data-sp715')){var x=S715.keys[t.getAttribute('data-sp715')];if(x){$('f_vendor').value=x.name;S715.state='ok';}}else{S715.state='new';}
 $('sup715').style.display='none';s715supw();s715restk();sumline();paint2();});
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-dt715],[data-s7x],[data-s7add],[data-a7ok],[data-a7no],[data-rr715]'):null;if(!t){return;}
 if(t.hasAttribute('data-dt715')){$('f_date').value=t.getAttribute('data-dt715');S715.dt=true;sumline();return;}
 if(t.hasAttribute('data-rr715')){var id=+t.getAttribute('data-rr715');t.disabled=true;
  fetch(C.reread.replace(/\/0\/reread$/,'/'+id+'/reread'),{method:'POST',credentials:'same-origin',redirect:'manual'}).then(function(r){var asked=r.type=='opaqueredirect'||r.ok;r={ok:asked,status:r.status};S715.rr=true;var m=$('rr715msg');if(m){m.textContent=r.ok?'Asked again — the empty boxes fill in by themselves if it reads. Carry on.':'Could not ask again ('+r.status+') — type what you see.';}t.style.display='none';if(r.ok){s715poll(id,0);}},function(){var m=$('rr715msg');if(m){m.textContent='Could not ask again — type what you see.';}t.disabled=false;});return;}
 if(!S.stk||!S.cur){return;}
 if(t.hasAttribute('data-s7x')){S.stk.lines[+t.getAttribute('data-s7x')].gone=true;S715.touched=true;if(S715.add===+t.getAttribute('data-s7x')){S715.add=-1;}s715restk();paint2();}
 else if(t.hasAttribute('data-s7add')){var n=0;S.stk.lines.forEach(function(l){if(l.no>n){n=l.no;}});S.stk.lines.push({no:n+1,name:'',qty:'',unit:'',rate:null,item:'',hand:true,sug:false,saved:false,side:'',gone:false});S715.touched=true;s715restk();
  var ins=document.querySelectorAll('#st568 [data-pk]');if(ins.length){ins[ins.length-1].focus();}paint2();}
 else if(t.hasAttribute('data-a7no')){S715.add=-1;s715restk();}
 else if(t.hasAttribute('data-a7ok')){var i=+t.getAttribute('data-a7ok'),l=S.stk.lines[i],nm=(document.querySelector('[data-a7n]').value||'').replace(/\s+/g,' ').trim();
  if(!nm){$('a7err').textContent='Type the item’s name.';return;}var same=null;((S.cur.stk||{}).items||[]).forEach(function(x){if(x.name.toLowerCase()==nm.toLowerCase()){same=x;}});
  if(same){l.item=String(same.id);}else{l.item='new';l.name=nm;l.unit=document.querySelector('[data-a7u]').value;}
  var r=document.querySelector('[data-a7r]');if(r&&r.value.trim()){l.rate=r.value.trim();}l.sug=false;S715.add=-1;S715.touched=true;s715restk();paint2();}});
if(C.sup715){getJ(C.sup715).then(function(j){S715.sup=(j&&j.suppliers)||[];S715.keys={};S715.sup.forEach(function(x){S715.keys[x.key]=x;});if(S.cur){s715supw();}});}
// S571_BATTERIES:""")

EDITS = [("const", PY_CONST), ("cfg", PY_CFG), ("route", PY_ROUTE), ("panel", PY_PANEL), ("listed", PY_LISTED), ("save", PY_SAVE), ("pyblock", PY_BLOCK),
         ("css", CSS), ("supplier", SUPPLIER_BOX), ("date", DATE_BOX), ("drawdate", DRAW_DATE), ("openinit", OPEN_INIT), ("drawend", DRAW_END),
         ("useit", USE_IT), ("savedate", SAVE_DATE), ("flagrate", FLAG_RATE), ("nothing", NOTHING), ("gate", GATE), ("sumline", SUMLINE), ("stkinit", STK_INIT), ("prpick", PR_PICK), ("js", JS)]
BETWEEN = [("stkpaint", STK_PAINT), ("stkbody", STK_BODY)]
