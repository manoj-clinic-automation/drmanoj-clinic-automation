#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""make_s853.py -- kit S853_PATIENTS_PART2: anchored patches on the LIVE bytes of patients_page.py (595ce680) and
patients_page.html (a2a8a17c). Usage: python3 make_s853.py <dir holding the two FROM files> <out dir>. Every anchor must be
found exactly once, else nothing is written."""
import hashlib
import os
import sys

FROM = {"patients_page.py": "595ce680946c9222995888945f2feb6a", "patients_page.html": "a2a8a17cafde7a80bfa3c2403d4958f9"}

PY = [
    ('VERSION = "S851 1.0"', 'VERSION = "S853 1.0"'),
    ('PART 2 (a later kit, shown on the page as "comes next"): the calls and WhatsApp at the front desk, Google, the reviews, last\n'
     '  year\'s history from his two Docterz exports, the one-tap placing of diagnosis words, the "Called" columns.',
     'PART 2 (kit S853, S477): patients_part2.read2() is called at the end of read(), inside a try -- the front desk (calls and\n'
     '  WhatsApp), Google, the reviews, last year from his two Docterz exports, the "Called" columns. A fault there leaves Part 1 whole.'),
    ('    reading["glance"] = {m: glance_for(reading, m) for m in months}\n    return reading, lists\n',
     '    reading["glance"] = {m: glance_for(reading, m) for m in months}\n'
     '    try:                                                               # S853: Part 2 -- never at Part 1\'s cost\n'
     '        import patients_part2                                          # noqa: PLC0415\n'
     '        reading["p2"] = patients_part2.read2(reading, lists, today)\n'
     '    except Exception as e:                                             # noqa: BLE001 -- the page says Part 2 could not be read\n'
     '        reading["p2"] = dict(ok=False, why="%s: %s" % (type(e).__name__, str(e)[:160]))\n'
     '    return reading, lists\n'),
    ('sug=("Visits per open day fell by %d%%. Read it with the season first (the same weeks last year come with Part 2); "\n'
     '                             "the missed calls of the slow days come on this page with Part 2." % round(-ch)) if ch <= -10 else',
     'sug=("Visits per open day fell by %d%%. Read it with the season first, then the missed calls at the "\n'
     '                             "front desk." % round(-ch)) if ch <= -10 else'),
]

P2JS = r'''
// ---------------------------------------------------------------- S853: Part 2
function p2(){return (R&&R.p2)||{};}
function p2bad(b,what){return '<div class="card"><h2>'+esc(what)+'</h2><p class="sub">could not be read just now'+(b&&b.why?' ('+esc(b.why)+')':'')+'. The rest of the page is whole.</p></div>';}
function sgn(v){if(v==null||v==="")return "–";v=Math.round(v);return (v>0?"+":v<0?"−":"")+Math.abs(v)+"%";}
function n0(v){return v==null?"–":String(v);}
function lyCard(){
  var H=p2().history;if(!H||!H.ok)return p2bad(H,"The same months a year before");
  var rows=R.months.map(function(m){var x=H.ly[m.ym];if(!x)return '';var me=mrow(m.ym);
    return '<tr class="'+(m.ym===M?'shade':'')+'"><td>'+esc(m.short)+' 2025</td><td>'+x.patients+(me?' <span class="grey">('+me.patients+')</span>':'')+'</td><td>'+x.new+(me?' <span class="grey">('+me.new+')</span>':'')+'</td><td>'+x.visits+'</td><td>'+x.vpd+(me?' <span class="grey">('+me.vpd+')</span>':'')+'</td><td>'+(x.consult==null?'<span class="grey">not held</span>':inr(x.consult))+'</td><td>'+(x.xray==null?'<span class="grey">not held</span>':inr(x.xray))+'</td><td>'+(x.proc==null?'<span class="grey">not held</span>':inr(x.proc))+'</td><td>'+(x.review_kept_num==null?'–':x.review_kept_num+'%')+'</td></tr>';}).join("");
  var rg=(H.range||{}).review_kept, ro=(H.range||{}).o30;
  return '<div class="card"><h2>The same months a year before</h2><p class="sub">from your two Docterz exports (January 2025 – June 2026) · this year\'s figure in grey beside it</p><div class="tw"><table><thead><tr><th>Month</th><th>Patients</th><th>New</th><th>Visits</th><th>Visits a day</th><th>Consultations ₹</th><th>X-rays ₹</th><th>Procedures ₹</th><th>Planned reviews kept</th></tr></thead><tbody>'+rows+'</tbody></table></div>'+
    '<p class="note">Docterz holds consultation fees from April 2025 and X-ray and procedure charges from October 2025, so rupees compare year on year only from those months.'+(rg?' Over the 18 months, planned reviews kept moved between '+rg.lo+'% and '+rg.hi+'%, usually '+rg.p25+'–'+rg.p75+'%.':'')+(ro?' Seen-before patients back in 8–30 days: usually '+ro.p25+'–'+ro.p75+'% (range '+ro.lo+'–'+ro.hi+'%).':'')+'</p></div>';
}
function googleCard(){
  var G=p2().google;if(!G||!G.ok)return p2bad(G,"Before they reach you — Google");
  var t1=G.rows.map(function(r){return '<tr class="'+(r.ym===M?'shade':'')+'"><td>'+esc(mlab(r.ym))+'</td><td>'+r.searches.toLocaleString("en-IN")+'</td><td>'+r.views.toLocaleString("en-IN")+'</td><td>'+r.calls+'</td><td><b>'+r.directions+'</b></td><td>'+r.chats+'</td><td>'+r.website+'</td><td>'+r.actions+'</td><td class="hl"><b>'+n0(r.new)+'</b></td><td>'+n0(r.per10)+'</td></tr>';}).join("");
  var t2=G.rows.map(function(r){var y=r.yoy||{};return '<tr class="'+(r.ym===M?'shade':'')+'"><td>'+esc(mlab(r.ym))+'</td><td>'+r.calls+'</td><td class="yy">'+sgn(y.calls)+'</td><td>'+r.directions+'</td><td class="yy"><b>'+sgn(y.directions)+'</b></td><td>'+r.acts3+'</td><td class="yy">'+sgn(y.actions)+'</td><td class="yy">'+sgn(y.views)+'</td><td class="yy">'+sgn(y.searches)+'</td><td class="hl"><b>'+n0(r.new)+'</b>'+(r.new_ly!=null?' <span class="grey">('+r.new_ly+')</span>':'')+'</td><td class="hl yy"><b>'+sgn(r.new_yoy)+'</b></td></tr>';}).join("");
  var last=G.last?mlab(G.last):"–";
  return '<div class="card"><h2>Before they reach you — Google</h2><p class="sub">from Google\'s own monthly mail of your Business Profile, and each month against the same month last year (Google\'s comparison) — beside the clinic\'s own new patients · latest: '+esc(last)+'</p>'+
    '<div class="tw"><table><thead><tr><th>Month</th><th>Searches that showed you</th><th>Profile views</th><th>Calls</th><th>Asked directions</th><th>Chats</th><th>Website visits</th><th>All actions</th><th>New patients at the clinic</th><th>New patients per 10 direction requests</th></tr></thead><tbody>'+t1+'</tbody></table></div>'+
    '<p class="sub" style="margin-top:12px"><b>Each month against the same month a year before</b></p><div class="tw"><table><thead><tr><th>Month</th><th>Calls</th><th>vs a year before</th><th>Asked directions</th><th>vs a year before</th><th>Calls + directions + website</th><th>vs a year before</th><th>Profile views vs a year before</th><th>Searches vs a year before</th><th>New patients at the clinic (last year)</th><th>vs a year before</th></tr></thead><tbody>'+t2+'</tbody></table></div>'+
    '<p class="note">Top searches: '+esc(G.top_terms)+' — people looking for an orthopaedic doctor, not yet for you by name. '+esc(G.closed_days)+' The link between Google and new patients is moderate, not exact: month by month they rise and fall together, week by week Google does not predict the clinic.</p></div>';
}
function deskCard(){
  var Dk=p2().desk;if(!Dk||!Dk.ok)return p2bad(Dk,"At the front desk — calls and WhatsApp");
  var d=Dk.months[M];if(!d)return '';
  var h=['<div class="card"><h2>At the front desk — calls and WhatsApp</h2><p class="sub">'+esc(d.span)+' ('+d.days+' days) · from the Call Console\'s own record and the WhatsApp inbox, read by the Call Console\'s own rules · calls and WhatsApp of one person read together · <a href="/portal/console">open the Call Console</a></p><div class="tiles">'+
    d.tiles.map(function(g){return '<div class="tile'+(g.warn?' warn':'')+'"><div class="l">'+esc(g.label)+'</div><div class="v">'+esc(g.value)+'</div><div class="s">'+esc(g.sub)+'</div></div>';}).join("")+'</div>'];
  h.push('<p class="sub" style="margin-top:12px"><b>Calls — each caller counted once a day, however many times he rang</b></p><div class="tw"><table><thead><tr><th></th><th>Callers (per day)</th><th>Answered at the first ring</th><th>Rang again and got through</th><th>We called back and spoke</th><th>Reached on a later day</th><th>Not reached yet (last 7 days)</th><th class="hl">Never reached</th><th class="hl">… with no call-back on record</th></tr></thead><tbody>'+
    d.calls.map(function(r){return '<tr><td>'+esc(r.label)+'</td><td>'+r.n+'</td><td>'+r.first+' ('+esc(r.first_p)+')</td><td>'+r.again+' ('+esc(r.again_p)+')</td><td>'+r.back+' ('+esc(r.back_p)+')</td><td>'+r.later+' ('+esc(r.later_p)+')</td><td>'+(r.open||0)+'</td><td class="hl"><b>'+r.never+' ('+esc(r.never_p)+')</b></td><td class="hl">'+r.nocb+'</td></tr>';}).join("")+'</tbody></table></div><p class="note">'+esc(d.note)+'</p>');
  if(Dk.wa_ok){h.push('<p class="sub" style="margin-top:12px"><b>WhatsApp — each sender counted once</b></p><div class="tw"><table><thead><tr><th></th><th>People</th><th>Answered</th><th>Reply or call tried</th><th class="hl">Nothing on record</th><th class="hl">Lost</th></tr></thead><tbody>'+
    d.wa.map(function(r){return '<tr><td>'+esc(r.label)+'</td><td>'+r.n+'</td><td>'+r.ans+'</td><td>'+r.tried+'</td><td class="hl">'+r.nothing+'</td><td class="hl"><b>'+esc(r.lost)+'</b></td></tr>';}).join("")+'</tbody></table></div>');}
  else h.push('<p class="note">The WhatsApp inbox could not be read just now; the calls above stand.</p>');
  h.push('<div class="cols" style="margin-top:12px"><div><p class="sub"><b>When the phone rings (incoming calls)</b></p><div class="tw"><table><thead><tr><th>Hour</th><th>Answered</th><th>Missed</th><th>Missed share</th></tr></thead><tbody>'+
    d.hours.map(function(r){return '<tr><td>'+esc(r.label)+'</td><td>'+r.ans+'</td><td>'+r.miss+'</td><td><b>'+esc(r.share)+'</b></td></tr>';}).join("")+'</tbody></table></div></div>'+
    '<div><p class="sub"><b>What the answered calls were about (the AI\'s verdict on each recording)</b></p><div class="tw"><table><thead><tr><th></th><th>Calls with a verdict</th><th>Booked or coming</th><th>Enquiry only</th><th>Call again</th><th>Other answers</th></tr></thead><tbody>'+
    d.about.map(function(r){return '<tr><td class="l">'+esc(r.label)+'</td><td>'+r.n+'</td><td>'+r.booked+' ('+esc(r.booked_p)+')</td><td>'+r.enq+' ('+esc(r.enq_p)+')</td><td>'+r.again+'</td><td class="l">'+esc(r.other||"–")+'</td></tr>';}).join("")+'</tbody></table></div></div></div>');
  if(Dk.wa_ok&&Dk.wa_months&&Dk.wa_months.length){h.push('<p class="sub" style="margin-top:12px"><b>WhatsApp to the clinic number, month by month</b></p><div class="tw"><table><thead><tr><th>Month</th><th>People who wrote</th><th class="hl">Not in your patient list</th><th>New conversations</th><th>… only “hi” or “hello”</th><th>… a photo or report first</th><th>Asked for time or appointment</th><th>Replied from the clinic WhatsApp</th><th>Replies that failed</th><th>Google chat clicks</th></tr></thead><tbody>'+
    Dk.wa_months.map(function(r){return '<tr class="'+(r.partial?'part':'')+'"><td>'+esc(mlab(r.ym))+(r.partial?' (so far)':'')+'</td><td>'+r.people+'</td><td class="hl">'+r.unk+'</td><td>'+r.convs+'</td><td>'+r.greet+'</td><td>'+r.media+'</td><td>'+r.askt+'</td><td>'+r.replies+'</td><td>'+r.failed+'</td><td>'+(r.chats==null?'<span class="grey">··</span>':r.chats)+'</td></tr>';}).join("")+'</tbody></table></div>');}
  h.push('<p class="note">“Unknown” = the number is not in your patient list today, so a caller since registered under that number counts as your patient. A caller is “answered at the first ring” when his first call of the day was picked up; “reached on a later day” = an answered call within 7 days. WhatsApp “answered” follows your rule of 2-Nov — a reply that went, or a call of 30 seconds or more within two clinic hours, or your Done. A WhatsApp is judged by its chat as it stands today, so a message answered later counts as answered. A missed caller of the last 7 days is “not reached yet”, never “never”. A call-back from a personal mobile is not on record. The call record begins '+esc(dmy(Dk.calls_from))+'; WhatsApp is complete from September.</p></div>');
  return h.join("");
}
function reviewsCard(){
  var V=p2().reviews;if(!V||!V.ok)return p2bad(V,"Google reviews — the good ones are asked for");
  var L=V.last||{}, mo=V.months[M]||{};
  var tiles=[['Reviewers on your listing',n0(L.ours_n),L.taken_on?'counted on '+dmy(L.taken_on):'no reading yet'],
    ['Gave 1 or 2 stars',L.low==null?'–':L.low+'%',L.ours_n&&L.low!=null?'about '+Math.round(L.ours_n*L.low/100)+' reviewers':''],
    ['Drafts made with Review Assist',String(mo.drafts||0),(mo.shared||0)+' shared · '+mlab(M)+(V.since?' · kept since '+dmy(V.since):''),!(mo.drafts)],
    ['New reviewers since the last reading',V.new_since==null?'··':(V.new_since>=0?'+':'')+V.new_since,V.prev_on?'since '+dmy(V.prev_on):'the first figure comes with the next fortnightly reading'],
    ['Asks per 100 patients seen',mo.per100==null?'–':String(mo.per100),'drafts made against '+mlab(M)+'\'s patients — the figure you control']];
  return '<div class="card"><h2>Google reviews — the good ones are asked for</h2><p class="sub">from the fortnightly reading of your listing and the Review Assist page\'s own record · <a href="/portal/gmb">open Review Assist</a></p><div class="tiles">'+
    tiles.map(function(t){return '<div class="tile'+(t[3]?' warn':'')+'"><div class="l">'+esc(t[0])+'</div><div class="v">'+esc(t[1])+'</div><div class="s">'+esc(t[2])+'</div></div>';}).join("")+'</div>'+
    (V.themes&&V.themes.length?'<p class="sub" style="margin-top:12px"><b>What the unhappy reviewers wrote about — and where this page can see the same thing</b></p><div class="tw"><table><thead><tr><th>Complaint</th><th>Of your reviewers</th><th>Of other local listings\' reviewers</th><th style="text-align:left">Where this page can look</th></tr></thead><tbody>'+
    V.themes.map(function(t){return '<tr><td>'+esc(t.name)+'</td><td><b>'+esc(t.ours)+'%</b></td><td>'+esc(t.other)+'%</td><td class="l grey">'+esc(t.look||"–")+'</td></tr>';}).join("")+'</tbody></table></div>':'')+
    '<p class="note">An unhappy patient writes by himself; a satisfied one writes when you ask him in the clinic and help him with the words — so the good reviews follow the asks.</p></div>';
}
function mlab(ym){var m=["January","February","March","April","May","June","July","August","September","October","November","December"];return m[+ym.slice(5,7)-1]+" "+ym.slice(0,4);}
function calledCell(f){
  var C=p2().called;if(!C||!C.ok)return '<td class="grey">··</td>';
  var x=C.rows[f.ym+":"+f.kind];if(!x||!x.n)return '<td class="grey">'+(x&&x.unknown?'before the call record':x&&x.notyet?'not yet':x&&x.nophone?'no number on record':'–')+'</td>';
  return '<td class="tap" data-k="'+esc("fuc:"+f.ym+":"+f.kind+":called")+'" title="kept: called '+esc(x.kept_called)+' · not called '+esc(x.kept_not)+'">'+x.called+' of '+x.n+'</td>';
}
function missedCalled(name){
  var C=p2().called;if(!C||!C.ok)return '<td class="grey">··</td>';
  var x=C.groups[M+":"+name];if(!x||!x.missed)return '<td>–</td>';return '<td>'+x.called+' of '+x.missed+'</td>';
}
function lateHist(){
  var H=p2().history;if(!H||!H.ok)return '';
  var F=H.final||{}, out=[], L=(H.late_full||{})[M];
  var order=["Rheumatology","Degenerative Joint Disease","Radicular Spine Disease","Trauma","Other groups"];
  var parts=order.filter(function(g){return F[g]&&F[g].n>=MIN_BASE;}).map(function(g){var f=F[g];var p=function(v){return Math.round(100*v/f.n)+'%';};return g+' ('+f.n+') — '+p(f.kept)+' by the date, '+p(f.within)+' within a month after, '+p(f.later)+' later, '+p(f.never)+' never';});
  if(L&&L.total)out.push('Measured on the full record from January 2025, the same '+L.trio[0]+'–'+L.trio[L.trio.length-1]+' late returns: '+(L.total.a||0)+' after 1–2 months, '+(L.total.b||0)+' after 2–3, '+(L.total.c||0)+' after 3–6, '+(L.total.d||0)+' after more than six months, and '+(L.total.e||0)+' by patients not seen at all since before January 2025.');
  if(parts.length)out.push('How a review date (8 days or more) was finally kept, January 2025 – May 2026: '+parts.join('; ')+'.');
  return out.length?'<p class="note">'+esc(out.join(' '))+'</p>':'';
}
var MIN_BASE=20;
'''

HT = [
    ('td.w{color:var(--warn);font-weight:600}',
     'td.w{color:var(--warn);font-weight:600}\ntd.hl,th.hl{background:var(--warn-soft)} td.yy{color:var(--accent)}\n.tile.warn{border-color:var(--warn);background:var(--warn-soft)} .tile.warn .v{color:var(--warn)}'),
    (" June is left out, as you ruled.</p></div>');",
     " June is left out, as you ruled.</p></div>');\n  // S853: Part 2 -- last year, Google, the front desk, the reviews; a fault in one card costs that card only\n  [[lyCard,'The same months a year before'],[googleCard,'Before they reach you — Google'],[deskCard,'At the front desk — calls and WhatsApp'],[reviewsCard,'Google reviews']].forEach(function(c){try{h.push(c[0]());}catch(e){h.push(p2bad({why:String(e)},c[1]));}});"),
    ("'<td>'+esc(f.kept_pct)+'</td><td class=\"grey\">··</td></tr>';", "'<td>'+esc(f.kept_pct)+'</td>'+calledCell(f)+'</tr>';"),
    ('"Called" (grey) splits each row into called by staff and not called — it comes with Part 2, from the call log.',
     '"Called" = the clinic rang a number of that clinic ID (any outgoing call, answered or not) from 3 days before the date to 30 days after it (a follow-up still open, or an ID with no number on record, is left out); the tap opens the called ones, and the figure\\\'s hover shows how often the called and the not-called kept the date.'),
    ("+esc(x.md)+'</td><td class=\"grey\">··</td></tr>';", "+esc(x.md)+'</td>'+missedCalled(x.name)+'</tr>';"),
    (" Last year\\'s history (the gaps of a year and more, and how each review date was finally kept) comes with Part 2, from your two Docterz exports.</p></div>');}",
     "</p>'+lateHist()+'</div>');}"),
    ("The one-tap placing (the page suggests a group; one tap places the word, its spelling slips and its other sides) comes with Part 2.",
     "The one-tap placing (the page suggests a group; one tap places the word, its spelling slips and its other sides) comes next."),
    ("<div class=\"card next\"><h2>Comes next — part 2</h2><ul><li>At the front desk — calls and WhatsApp, each caller counted once a day; the \"Called\" columns above.</li><li>Before they reach you — Google (the monthly Performance figures, year on year).</li><li>Google reviews — the good ones are asked for.</li><li>Last year from your two Docterz exports — the same months a year before; how each review date was finally kept.</li><li>The one-tap placing of diagnosis words.</li></ul></div>",
     "<div class=\"card next\"><h2>Still to come</h2><ul><li>The one-tap placing of diagnosis words.</li><li>Google\\'s monthly figures read by the server by itself each month (today they are read from Google\\'s mail at each session).</li><li>Which enquiry callers became patients.</li></ul></div>"),
    ("function openList(key,what){", P2JS.strip("\n") + "\nfunction openList(key,what){"),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch(src, pairs, name):
    for old, new in pairs:
        n = src.count(old)
        if n != 1:
            raise SystemExit("ANCHOR %s found %d times in %s: %r" % ("NOT" if n == 0 else "MANY", n, name, old[:80]))
        src = src.replace(old, new)
    return src


def main():
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    out = {}
    for name, pairs in (("patients_page.py", PY), ("patients_page.html", HT)):
        b = open(os.path.join(src_dir, name), "rb").read()
        if md5(b) != FROM[name]:
            raise SystemExit("FROM %s is %s, not %s -- the live file moved; nothing written" % (name, md5(b), FROM[name]))
        out[name] = patch(b.decode("utf-8"), pairs, name).encode("utf-8")
    os.makedirs(out_dir, exist_ok=True)
    for name, b in out.items():
        with open(os.path.join(out_dir, name), "wb") as fh:
            fh.write(b)
        print("%s %s -> %s" % (name, FROM[name][:8], md5(b)[:8]))


if __name__ == "__main__":
    main()
