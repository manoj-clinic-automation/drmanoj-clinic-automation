#!/usr/bin/env python3
"""apply_s413.py -- kit S413_SLIP_PICKER. Makes the S413 slip_log.py from the live S401 bytes (36405348).
The owner, 26-Sep-2026: the X-ray/Proc form's drop-downs cut long names and show no price; the search must be
intuitive ("SBK" or "BK" bring the right lines) and one box must serve X-rays and procedures alike.
  1. the two drop-down columns are replaced by ONE picker: a search box over X-rays and procedures together,
     the most-used lines (last 90 days) as tappable buttons with their price, a result list while typing, and
     every chosen line shown in full with its price, side (when the rate page asks), chhoot (procedures) and a
     remove cross; a running total at the bottom. The form still posts the same fields (xray0.., proc0.., _side,
     _other, _disc), so the server side of saving is untouched.
  2. the X-ray room rows list each line on its own with its price, instead of one comma-run string.
Usage: python apply_s413.py <S401 slip_log.py> <out>"""
import hashlib, sys
b = open(sys.argv[1], "rb").read()
assert hashlib.md5(b).hexdigest() == "364053483a5a4c4161663e77775f1a01", "the source is not S401 slip_log.py"
s = b.decode("utf-8")


def rep(old, new, n=1):
    global s
    assert s.count(old) == n, ("anchor", old[:70], s.count(old))
    s = s.replace(old, new)


# 1 -- the picker's data: aliases and usage, beside services()
rep('''# ---------------------------------------------------------------- the books and the next number
def book(con, series):''', '''def _aliases(kind, name):
    """S413: the words a line can be found by -- its name, the short form and the long form inside brackets
    (B/K, Below knee), its group word (X-ray / cast / slab / plaster / injection / ILI / dressing)."""
    words = [name]
    for m in re.finditer(r"\\(([^)]*)\\)", name):
        words.append(m.group(1))
    words.append(re.sub(r"\\([^)]*\\)", " ", name))
    low = name.lower()
    if kind == "xray":
        words += ["x-ray", "xray", "x ray"]
    if "cast" in low:
        words += ["plaster", "cast", "fibre", "pop"]
    if "slab" in low:
        words += ["plaster", "slab", "fibre", "pop"]
    if "ili" in low or "injection" in low:
        words += ["injection", "ili", "inj"]
    if "dress" in low:
        words += ["dressing", "patti"]
    if "bandage" in low or "clavicle" in low:
        words += ["bandage", "collar"]
    return " ".join(words)


def usage_counts(con, days=90):
    """S413: how often each rate line was chosen in the last `days` days -- the most-used ones sit on top."""
    since = (_now().date() - dt.timedelta(days=days)).isoformat()
    try:
        return {r["service_id"]: r["n"] for r in con.execute(
            "SELECT i.service_id, COUNT(*) n FROM slip_item i JOIN slip s ON s.id=i.slip_id "
            "WHERE s.state='ok' AND s.day>=? AND i.service_id IS NOT NULL GROUP BY i.service_id", (since,))}
    except Exception:                                    # noqa: BLE001
        return {}


def picker_json(con, xr, pr):
    use = usage_counts(con)
    out = []
    for kind, rows in (("xray", xr), ("proc", pr)):
        for r in rows:
            out.append({"id": r["id"], "k": kind, "n": r["name"], "p": int(r["price_p"] or 0), "s": 1 if r["side"] else 0,
                        "a": _aliases(kind, r["name"]).lower(), "u": int(use.get(r["id"], 0))})
    return json.dumps(out, ensure_ascii=False).replace("</", "<\\\\/")


# ---------------------------------------------------------------- the books and the next number
def book(con, series):''')

# 2 -- the form: the picker replaces the two select columns
rep('''                   '<div class="lists"><div class="lst"><b>X-ray</b>' + _item_rows("xray", xr, MAX_XRAY, "X-ray chunein") +
                   '<button type="button" class="more" data-kind="xray">+ aur X-ray</button></div>'
                   '<div class="lst"><b>Procedure</b>' + _item_rows("proc", pr, MAX_PROC, "Procedure chunein") +
                   '<button type="button" class="more" data-kind="proc">+ aur procedure</button></div></div>'
                   + _gap_ok() + '<button class="go">Save</button></form>')''',
    '''                   _picker_html(con, xr, pr)                          # S413
                   + _gap_ok() + '<button class="go">Save</button></form>')''')
rep('''def _book_line(con, series):''', '''def _picker_html(con, xr, pr):
    """S413: one search box over X-rays and procedures, the most-used lines as buttons, the chosen lines in full."""
    return ('<div class="pk" data-maxx="%d" data-maxp="%d"><script type="application/json" class="pkdata">%s</script>'
            '<div class="row"><label class="pkq">X-ray / procedure dhundhein<input type="search" class="pks" '
            'placeholder="likhein: knee, SBK, BK slab, ILI, dressing \\u2026" autocomplete="off" autocorrect="off" '
            'autocapitalize="off"></label></div>'
            '<div class="pkr" hidden></div>'
            '<div class="pksel"><b>Chuni hui</b><div class="pkl"></div><div class="pktot" hidden></div></div>'
            '<div class="pkt"><b>Aksar (tap karein)</b><div class="pkc"></div></div>'
            '<div class="pkh"></div></div>' % (MAX_XRAY, MAX_PROC, picker_json(con, xr, pr)))


def _book_line(con, series):''')

# 3 -- the room rows: each line with its price
rep('''            '<div class="rrow%s"><div class="rl"><span class="no">%d</span> %s<br><span class="sm">%s%s</span></div>'
            '<span class="amt">%s</span>\'''', '''            '<div class="rrow%s"><div class="rl"><span class="no">%d</span> %s<br><span class="sm">%s%s</span></div>'
            '<span class="amt">%s</span>\'''')
rep('''                _esc(_items_label(s.get("items") or _items_of(con, s["id"]))),
                (" · %s" % _dmy(s["day"])[:6]) if s["day"] != today else "",''',
    '''                _items_lines(s.get("items") or _items_of(con, s["id"])),                    # S413
                (" · %s" % _dmy(s["day"])[:6]) if s["day"] != today else "",''')
rep('''# ================================================================ the Docterz cross-match (report)''',
    '''def _items_lines(items):
    """S413: the room reads each line whole -- name, side, price after chhoot -- one per line."""
    out = []
    for it in items:
        p = int(it.get("price_p") or 0) - int(it.get("discount_p") or 0)
        tag = ""
        if len(items) > 1 or int(it.get("discount_p") or 0) or not it.get("price_p"):
            tag = " <em>%s</em>" % ((_rs(p) + ((" (chhoot %s)" % _rs(it["discount_p"])) if int(it.get("discount_p") or 0) else ""))
                                   if it.get("price_p") else "rate nahi")
        out.append('<span class="il">%s%s%s</span>' % (_esc(it["name"]), (" " + _esc(it["side"])) if it.get("side") else "", tag))
    return "".join(out)


# ================================================================ the Docterz cross-match (report)''')

# 4 -- the styles
rep('''.irow{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px}''',
    '''.pk{margin:4px 0 8px}.pkq{flex:1 1 100%%}.pks{width:100%%}
.pkr{background:#fff;border:2px solid var(--accent);border-radius:10px;margin:-4px 0 8px;max-height:46vh;overflow:auto}
.pkr button,.pkc button{display:flex;justify-content:space-between;align-items:center;gap:8px;width:100%%;text-align:left;font:inherit;font-size:16px;min-height:46px;padding:8px 10px;border:0;border-bottom:1px solid #e1e7eb;background:#fff;color:var(--ink)}
.pkr button:last-child{border-bottom:0}.pkr button em,.pkc button em,.pkl em{font-style:normal;font-weight:700;white-space:nowrap;color:var(--accent)}
.pkr button .k,.pkc button .k{font-size:12px;color:var(--mut);background:#eef2f4;border-radius:8px;padding:1px 6px;margin-left:6px;white-space:nowrap}
.pkr .none{padding:10px;color:var(--mut);font-size:15px}
.pkt b,.pksel b{display:block;font-size:14px;color:var(--mut);margin:6px 0 3px}
.pkc{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.pkc button{border:2px solid var(--line);border-radius:9px;min-height:48px;font-size:14px;padding:6px 8px;flex-direction:column;align-items:flex-start;gap:2px}.pkc button:active{background:var(--entry)}.pkc button .k{display:none}.pkc button em{font-size:15px}
.pkl:empty::after{content:"abhi kuch nahi chuna";font-size:14px;color:var(--mut)}
.pkl .it{display:flex;flex-wrap:wrap;align-items:center;gap:6px;background:var(--okbg);border:2px solid var(--ok);border-radius:9px;padding:6px 8px;margin-bottom:6px;font-size:16px}
.pkl .it .nm{flex:1 1 60%%;min-width:0;font-weight:600}.pkl .it .x{min-width:44px;min-height:40px;border:2px solid var(--bad);color:var(--bad);background:#fff;border-radius:8px;font-size:18px;font-weight:700}
.pkl .it .dl{display:flex;align-items:center;gap:6px;font-size:14px;color:var(--mut)}.pkl .it select,.pkl .it input{min-height:40px;font-size:15px}.pkl .it select.side{width:84px}.pkl .it input.disc{width:120px}.pkl .it input.oth{flex:1 1 100%%}
.pktot{font-size:18px;font-weight:700;color:#fff;background:var(--accent);border-radius:8px;text-align:right;padding:6px 10px;margin:2px 0 6px}
.irow{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px}''')
rep('''.rrow{display:flex;gap:8px;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid #e1e7eb}''',
    '''.rrow{display:flex;flex-wrap:wrap;gap:6px 8px;align-items:center;padding:8px 0;border-bottom:1px solid #e1e7eb}.rrow .rl{flex:1 1 100%%}.rrow .rb{margin-left:auto}''')
rep('''.rrow.old .rl{color:var(--warn)}''', '''.rrow.old .rl{color:var(--warn)}.il{display:block;font-size:15px;color:var(--ink)}.il em{font-style:normal;font-weight:700;color:var(--accent)}''')

# 5 -- the script
rep('''  [].forEach.call(document.querySelectorAll('form.vf'),function(f){f.addEventListener('submit',function(e){''',
    '''  [].forEach.call(document.querySelectorAll('.pk'),function(pk){        /* S413: the picker */
    var f=pk.closest('form'),data=[];try{data=JSON.parse(pk.querySelector('.pkdata').textContent);}catch(e){}
    var q=pk.querySelector('.pks'),res=pk.querySelector('.pkr'),chips=pk.querySelector('.pkc'),list=pk.querySelector('.pkl'),
        tot=pk.querySelector('.pktot'),hid=pk.querySelector('.pkh'),maxx=+pk.getAttribute('data-maxx'),maxp=+pk.getAttribute('data-maxp'),
        sel=[],KIND={xray:'X-ray',proc:'Procedure'};
    data.push({id:'other',k:'xray',n:'Other X-ray (naam likhein)',p:0,s:1,a:'other x-ray xray aur koi',u:-1});
    data.push({id:'other',k:'proc',n:'Other procedure (naam likhein)',p:0,s:1,a:'other procedure aur koi',u:-1});
    function norm(t){return (t||'').toLowerCase().replace(/[^a-z0-9\\u0900-\\u097f]+/g,'');}
    function rs(p){return p?'\\u20b9'+(p/100).toLocaleString('en-IN'):'rate nahi';}
    function score(it,words){var full=norm(it.n+' '+it.a),name=norm(it.n),sc=0;
      for(var i=0;i<words.length;i++){var w=words[i];if(!w)continue;
        if(name.indexOf(w)===0)sc+=30;else if(full.indexOf(w)<0)return -1;
        else{var toks=(it.n+' '+it.a).toLowerCase().split(/[^a-z0-9]+/),ws=false;
          for(var j=0;j<toks.length;j++){if(toks[j].indexOf(w)===0){ws=true;break;}}sc+=ws?20:10;}}
      return sc+Math.min(it.u,9);}
    function btn(it,cls){var b=document.createElement('button');b.type='button';b.className=cls||'';
      b.innerHTML='<span>'+esc(it.n)+'<span class="k">'+KIND[it.k]+'</span></span><em>'+rs(it.p)+'</em>';
      b.addEventListener('click',function(){add(it);q.value='';res.hidden=true;q.blur();});return b;}
    function esc(t){return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
    function search(){var words=q.value.trim().toLowerCase().split(/\\s+/).map(norm).filter(Boolean);
      res.innerHTML='';if(!words.length){res.hidden=true;return;}
      var hits=data.map(function(it){return {it:it,sc:score(it,words)};}).filter(function(x){return x.sc>=0;})
        .sort(function(a,b){return b.sc-a.sc||a.it.n.localeCompare(b.it.n);}).slice(0,12);
      if(!hits.length){res.innerHTML='<div class="none">Kuch nahi mila \\u2014 doosra shabd likhein, ya "other".</div>';}
      hits.forEach(function(h){res.appendChild(btn(h.it));});res.hidden=false;}
    function top(){chips.innerHTML='';data.filter(function(it){return it.u>0;}).sort(function(a,b){return b.u-a.u;}).slice(0,8)
      .concat(data.filter(function(it){return it.u<=0&&it.id!=='other';}).slice(0,6)).slice(0,6).forEach(function(it){chips.appendChild(btn(it));});}
    function add(it){var nx=sel.filter(function(x){return x.it.k==='xray';}).length,np=sel.filter(function(x){return x.it.k==='proc';}).length;
      if(it.k==='xray'&&nx>=maxx){alert('Ek parchi par '+maxx+' X-ray tak.');return;}
      if(it.k==='proc'&&np>=maxp){alert('Ek parchi par '+maxp+' procedure tak.');return;}
      sel.push({it:it,side:'',disc:'',oth:''});draw();}
    function draw(){list.innerHTML='';var t=0,pr=0;
      sel.forEach(function(x,i){var it=x.it,d=document.createElement('div');d.className='it';
        var h='<span class="nm">'+esc(it.n)+' <em>'+rs(it.p)+'</em></span>';
        if(it.s)h+='<select class="side"><option value="">side</option><option value="R"'+(x.side==='R'?' selected':'')+'>R</option><option value="L"'+(x.side==='L'?' selected':'')+'>L</option><option value="B"'+(x.side==='B'?' selected':'')+'>Both</option></select>';
        if(it.k==='proc'&&it.id!=='other')h+='<label class="dl">chhoot \\u20b9<input class="disc" inputmode="numeric" maxlength="6" placeholder="0" value="'+esc(x.disc)+'"></label>';
        if(it.id==='other')h+='<input class="oth" maxlength="60" placeholder="naam likhein" value="'+esc(x.oth)+'">';
        h+='<button type="button" class="x" aria-label="hatao">\\u00d7</button>';d.innerHTML=h;
        var sd=d.querySelector('.side'),ds=d.querySelector('.disc'),o=d.querySelector('.oth');
        if(sd)sd.addEventListener('change',function(){x.side=sd.value;hidden();});
        if(ds)ds.addEventListener('input',function(){x.disc=ds.value.replace(/[^0-9]/g,'');total();hidden();});
        if(o)o.addEventListener('input',function(){x.oth=o.value;hidden();});
        d.querySelector('.x').addEventListener('click',function(){sel.splice(i,1);draw();});
        list.appendChild(d);});
      total();hidden();}
    function total(){var t=0,ask=0;sel.forEach(function(x){var p=x.it.p-(+x.disc||0)*100;if(x.it.p)t+=Math.max(p,0);else ask++;});
      tot.hidden=!sel.length;tot.textContent='Kul: '+(t?'\\u20b9'+(t/100).toLocaleString('en-IN'):'\\u2014')+(ask?' + '+ask+' rate nahi':'');}
    function hidden(){hid.innerHTML='';var ix=0,ip=0;
      sel.forEach(function(x){var it=x.it,i=it.k==='xray'?ix++:ip++,p=it.k+i,h='';
        h+='<input type="hidden" name="'+p+'" value="'+esc(it.id)+'">';
        h+='<input type="hidden" name="'+p+'_side" value="'+esc(x.side)+'">';
        if(it.id==='other')h+='<input type="hidden" name="'+p+'_other" value="'+esc(x.oth)+'">';
        if(it.k==='proc'&&x.disc)h+='<input type="hidden" name="'+p+'_disc" value="'+esc(x.disc)+'">';
        hid.insertAdjacentHTML('beforeend',h);});}
    var tm;q.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(search,120);});
    q.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();var b=res.querySelector('button');if(b&&!res.hidden)b.click();}});
    q.addEventListener('focus',function(){if(q.value)search();});
    document.addEventListener('click',function(e){if(!pk.contains(e.target))res.hidden=true;});
    if(f)f.addEventListener('submit',function(e){if(!sel.length){e.preventDefault();alert('Kam se kam ek X-ray ya procedure chunein.');q.focus();}});
    top();draw();
  });
  [].forEach.call(document.querySelectorAll('form.vf'),function(f){f.addEventListener('submit',function(e){''')

# 6 -- the old select rows and their script are gone (nothing else called them)
import ast as _ast
tree = _ast.parse(s)
L = s.split("\n")
drop = set()
for n in tree.body:
    if isinstance(n, _ast.FunctionDef) and n.name in ("_opts", "_item_rows"):
        drop.update(range(n.lineno, n.end_lineno + 1))
        k = n.end_lineno + 1
        while k <= len(L) and L[k - 1].strip() == "" and k <= n.end_lineno + 2:
            drop.add(k); k += 1
s = "\n".join(x for i, x in enumerate(L) if i + 1 not in drop)
assert "_opts(" not in s and "_item_rows(" not in s
rep("""    [].forEach.call(f.querySelectorAll('.irow'),function(r){
      var s=r.querySelector('.svc'),sd=r.querySelector('.side'),o=r.querySelector('.oth'),ds=r.querySelector('.disc');
      s.addEventListener('change',function(){var op=s.options[s.selectedIndex];
        if(ds){ds.hidden=(!s.value||s.value==='other');if(ds.hidden)ds.value='';}
        sd.hidden=!(op&&(op.getAttribute('data-side')==='1'||s.value==='other'));
        o.hidden=(s.value!=='other');if(sd.hidden)sd.value='';});});
    [].forEach.call(f.querySelectorAll('.more'),function(b){b.addEventListener('click',function(){
      var nxt=f.querySelector('.irow[data-kind="'+b.getAttribute('data-kind')+'"][hidden]');
      if(nxt){nxt.hidden=false;}if(!f.querySelector('.irow[data-kind="'+b.getAttribute('data-kind')+'"][hidden]'))b.hidden=true;});});
""", "")
rep(""".irow{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px}.irow .svc{flex:1;min-width:0}.irow .side{width:78px}.irow .oth{flex:1 1 100%%}
""", "")

open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("S413 slip_log.py md5", hashlib.md5(s.encode("utf-8")).hexdigest())
