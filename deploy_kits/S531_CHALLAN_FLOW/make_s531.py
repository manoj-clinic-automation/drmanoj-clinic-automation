#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s531.py -- S531_CHALLAN_FLOW (D689 item 2): exact, counted edits on md5-pinned live bytes.

    python3 make_s531.py <live_dir> <out_dir>

Reads  <live_dir>/asset_register.py   (must be d3f1b64ee103efe22266426af9280fbe, after S523)
       <live_dir>/clinic_papers.py    (must be c60e043ce62cb2e8843d5963e9db0256, S530.1)
       <live_dir>/scanner_widget.js   (must be cd9c6e6053d85895e8132eb021b63b6b, after S523)
Writes the three files to <out_dir> and prints each md5. Every anchor must occur EXACTLY once or the build refuses."""
import hashlib, os, sys

FROM = {"asset_register.py": "d3f1b64ee103efe22266426af9280fbe",
        "clinic_papers.py": "c60e043ce62cb2e8843d5963e9db0256",
        "scanner_widget.js": "cd9c6e6053d85895e8132eb021b63b6b"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(t, anchor, new, name, where="replace"):
    n = t.count(anchor)
    if n != 1:
        raise SystemExit("REFUSED: anchor for %s found %d times (need 1)" % (name, n))
    return t.replace(anchor, (anchor + new) if where == "after" else (new + anchor) if where == "before" else new)


# ====================================================================================== the widget: a snapshot of the fields at Save
def build_widget(t):
    t = edit(t, '''    var it = {n: ++upSeq, thumb: list[0], pages: list.length, tok: token(), status: "wait", tries: 0, at: hhmm()};''',
             '''    var it = {n: ++upSeq, thumb: list[0], pages: list.length, tok: token(), status: "wait", tries: 0, at: hhmm(),
              fields: Object.assign({}, CFG.uploadFields)};                                   // S531: the fields as they stood at Save''',
             "W1 enqueue snapshot")
    t = edit(t, '''              blob: f, fname: f.name || ("bill_" + today() + ".pdf")};''',
             '''              blob: f, fname: f.name || ("bill_" + today() + ".pdf"), fields: Object.assign({}, CFG.uploadFields)};   // S531''',
             "W2 enqueueFile snapshot")
    t = edit(t, '''    var fd = new FormData();
    Object.keys(CFG.uploadFields).forEach(function(k){ fd.append(k, CFG.uploadFields[k]); });
    fd.append("client_token", it.tok);''',
             '''    var fd = new FormData(), uf = it.fields || CFG.uploadFields;                            // S531: a retry sends what Save saw
    Object.keys(uf).forEach(function(k){ fd.append(k, uf[k]); });
    fd.append("client_token", it.tok);''',
             "W3 sendOnce uses the snapshot")
    assert t.count("S531") == 3
    return t


# ====================================================================================== the app: the column, the field, the button, the slip
def build_app(t):
    t = edit(t, '''        ("bill_month", "ALTER TABLE bills ADD COLUMN bill_month TEXT"),     # S435 (F-658): the month the scanning person confirmed
    ]:''', '''        ("bill_month", "ALTER TABLE bills ADD COLUMN bill_month TEXT"),     # S435 (F-658): the month the scanning person confirmed
        ("doc_kind",      "ALTER TABLE bills ADD COLUMN doc_kind TEXT"),           # S531: 'challan' -- goods received, bill awaited
        ("challan_state", "ALTER TABLE bills ADD COLUMN challan_state TEXT"),      # S531: awaiting / joined / closed / deleted
        ("challan_of",    "ALTER TABLE bills ADD COLUMN challan_of INTEGER"),      # S531: the bill it was joined to
    ]:''', "A1 columns")
    t = edit(t, '''def _create_intake_bill(fobj, note, lane=None, prefill=None):''',
             '''def _create_intake_bill(fobj, note, lane=None, prefill=None, challan=False):''', "A2 signature")
    t = edit(t, '''    bid = cur.lastrowid
    try:                                                     # S441: who is scanning (the shared login's chosen name)''',
             '''    bid = cur.lastrowid
    if challan:                                              # S531 (D689 item 2): a challan -- goods received, bill awaited.
        # On the pharmacy lane it is handed over as kind 'Challan' (not 'Pharmacy'), so the Sanjeevni side's register does
        # not take it for a scan to pair until that side chooses to read challans.
        db.execute("UPDATE bills SET doc_kind='challan', challan_state='awaiting'" + (", kind='Challan'" if _lane == "pharmacy" else "") + " WHERE id=?", (bid,))
        _audit_bill(db, bid, "challan", {"lane": _lane})
    try:                                                     # S441: who is scanning (the shared login's chosen name)''',
             "A3 mark the challan")
    t = edit(t, '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"), _form_prefill())     # S403
    if not bid:
        flash("No usable file received''',
             '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"), _form_prefill(), challan=(request.form.get("challan") == "1"))     # S403; S531
    if not bid:
        flash("No usable file received''', "A4 basic form passes the field")
    t = edit(t, '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"), _form_prefill())     # S403
    if not bid:
        return ("no usable file", 400)''',
             '''    bid = _create_intake_bill(fobj, request.form.get("note"),
                              request.form.get("lane"), _form_prefill(), challan=(request.form.get("challan") == "1"))     # S403; S531
    if not bid:
        return ("no usable file", 400)''', "A5 scanner door passes the field")
    # the intake page: the one big button in the top card, the lane line, the basic form's field, the reset after Save
    t = edit(t, '''<p class=muted id=pf_note style="margin:4px 0 0"></p></div>
<script>function _laneLine(){var s=document.getElementById('intake_lane'),m=document.getElementById('intake_month'),l=document.getElementById('lane_line');if(!s||!m||!l){return;}
l.textContent=s.options[s.selectedIndex].text.split(' — ')[0]+' · '+m.options[m.selectedIndex].text.replace(' (this month)','');}</script>''',
             '''<p class=muted id=pf_note style="margin:4px 0 0"></p>
<button type=button id=challan_btn style="display:block;width:100%;margin-top:10px;min-height:52px;font-size:17px;font-weight:700;border-radius:10px;border:2px solid #b7c2d4;background:#fff;color:#2d3742">\U0001F4C4 CHALLAN HAI?</button>
<p class=muted id=challan_hint style="margin:6px 0 0;font-size:13px">Sirf tab dabao jab kaagaz challan ho (maal aaya, bill baad mein). Bill ho to kuch mat dabao.</p></div>
<script>function _laneLine(){var s=document.getElementById('intake_lane'),m=document.getElementById('intake_month'),l=document.getElementById('lane_line');if(!s||!m||!l){return;}
var ch=(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields&&window.SCANNER_CONFIG.uploadFields.challan==='1');
l.textContent=s.options[s.selectedIndex].text.split(' — ')[0]+' · '+m.options[m.selectedIndex].text.replace(' (this month)','')+(ch?' · CHALLAN':'');}
function _challanSet(on){var b=document.getElementById('challan_btn'),h=document.getElementById('challan_basic');if(window.SCANNER_CONFIG){if(on){window.SCANNER_CONFIG.uploadFields.challan='1';}else{delete window.SCANNER_CONFIG.uploadFields.challan;}}
if(h){h.value=on?'1':'';}if(b){b.textContent=on?'✔ CHALLAN — bill baad mein':'\U0001F4C4 CHALLAN HAI?';b.style.background=on?'#fde7b0':'#fff';b.style.borderColor=on?'#c9972b':'#b7c2d4';}
var hh=document.getElementById('challan_hint');if(hh){hh.textContent=on?'Yeh scan challan ban kar jaayega. Galti se dabaya? Dobara dabao. Save ke baad button apne aap normal ho jaata hai.':'Sirf tab dabao jab kaagaz challan ho (maal aaya, bill baad mein). Bill ho to kuch mat dabao.';}_laneLine();}</script>''',
             "A6 the button and the lane line")
    t = edit(t, '''<input type=hidden name=lane id=lane_basic value="{{lane_default}}"><input type=hidden name=bill_month id=month_basic value="{{months[0]}}"><input type=hidden name=from value="{{frm or ''}}">''',
             '''<input type=hidden name=lane id=lane_basic value="{{lane_default}}"><input type=hidden name=bill_month id=month_basic value="{{months[0]}}"><input type=hidden name=from value="{{frm or ''}}"><input type=hidden name=challan id=challan_basic value="">''',
             "A7 basic form field")
    t = edit(t, '''if(f.vendor){var p=document.getElementById('pf_note');if(p){p.textContent='Bill: '+f.vendor+(f.bill_no?' · no. '+f.bill_no:'')+(f.amount?' · ₹'+f.amount:'')+' — filled in from Purchase orders';}}
_laneLine();})();</script>''',
             '''if(f.vendor){var p=document.getElementById('pf_note');if(p){p.textContent='Bill: '+f.vendor+(f.bill_no?' · no. '+f.bill_no:'')+(f.amount?' · ₹'+f.amount:'')+' — filled in from Purchase orders';}}
var cb=document.getElementById('challan_btn');if(cb){cb.addEventListener('click',function(){_challanSet(!(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields&&window.SCANNER_CONFIG.uploadFields.challan==='1'));});}
['camsave','savebtn'].forEach(function(id){var e=document.getElementById(id);if(e){e.addEventListener('click',function(){setTimeout(function(){_challanSet(false);},0);});}});   /* S531: after the widget has queued the upload (it keeps its own copy of the fields), the button goes back to normal */
_laneLine();})();</script>''',
             "A8 the toggle and the reset after Save")
    # the slip says CHALLAN
    t = edit(t, '''<p class=muted id=slipnote><b>{{b['scanned_by'] or b['submitted_by']}}</b> · {{b['submitted_at']}} · {{lanes[b['lane'] or 'clinic'][0].split(' — ')[0]}}</p>''',
             '''<p class=muted id=slipnote><b>{{b['scanned_by'] or b['submitted_by']}}</b> · {{b['submitted_at']}} · {{lanes[b['lane'] or 'clinic'][0].split(' — ')[0]}}</p>
{% if b['doc_kind']=='challan' %}<p style="font-size:18px;font-weight:700;color:#5b3a06;background:#fff4e0;border-radius:8px;padding:8px 10px;margin:6px 0">CHALLAN — bill baad mein aayega. Kaagaz par yeh number likho; bill aaye to yahi number batao.</p>{% endif %}''',
             "A9 the slip")
    t = edit(t, '''    return jsonify(ok=True, id=b["id"], stamp=b["stamp_no"], lane=b["lane"], status=b["status"], already=already, dup_of=b["dup_of"],''',
             '''    return jsonify(ok=True, id=b["id"], stamp=b["stamp_no"], lane=b["lane"], status=b["status"], already=already, dup_of=b["dup_of"],
                   challan=(b["doc_kind"] == "challan"),                                                  # S531''',
             "A10 the scan reply")
    t = edit(t, ">\u2014 badlo</a>", ">\u2014&nbsp;badlo</a>", "A11 badlo never splits")
    assert t.count("S531") >= 8, t.count("S531")
    return t


# ====================================================================================== the papers page: bills awaited, the join, the delete
PAPERS_BLOCK = '''

# ---------------------------------------------------------------------------------------------- S531: the challan flow (D689 item 2)
CHALLAN_AMBER_DEFAULT = 15          # days before an awaiting challan turns amber (the owner's edit on the mock-up); setting d710.challan_amber_days
CHALLAN_MATCH_DAYS = 60             # a bill is offered a challan of the same supplier within this many days
DELETED_DIR = "_deleted_challans"   # a deleted challan's own file is MOVED here, never removed (BUILD_NORM s1: mark, never delete)


def _has_challans(db):
    return "doc_kind" in _cols(db)


def _amber_days(db):
    try:
        r = db.execute("SELECT value FROM settings WHERE key='d710.challan_amber_days'").fetchone()
        return max(1, int(r[0])) if r and str(r[0]).strip().isdigit() else CHALLAN_AMBER_DEFAULT
    except sqlite3.Error:
        return CHALLAN_AMBER_DEFAULT


def _supplier_key(v):
    """A supplier's name reduced to its first two real words, lower-case, hyphens and dots joined, the rest of the
    punctuation dropped -- 'YUVIKA SURGICALS', 'Yuvika Surgicals Bareilly' and 'yuvika surgical' meet; 'M/S' and 'Pvt Ltd'
    never count as words."""
    w = [x for x in re.sub(r"[^a-z0-9 ]", " ", (v or "").lower().replace("-", "").replace(".", "")).split()
         if x not in ("the", "ms", "m", "s", "pvt", "ltd", "p", "co", "and", "&")]
    return " ".join(w[:2])


def _age_days(b, today):
    for k in ("bill_date", "created_at"):
        try:
            return (today - datetime.date.fromisoformat(str(b[k])[:10])).days
        except Exception:                                            # noqa: BLE001
            continue
    return 0


def challans_awaiting(db):
    if not _has_challans(db):
        return []
    return db.execute("SELECT b.* FROM bills b WHERE b.doc_kind='challan' AND COALESCE(b.challan_state,'awaiting')='awaiting' "
                      "AND b.status<>'rejected' AND b.dup_of IS NULL ORDER BY b.id DESC").fetchall()


def challan_for_bill(db, b, today=None):
    """The awaiting challans this bill may be the bill for: the same supplier, within CHALLAN_MATCH_DAYS, never the pharmacy
    lane (that side keeps its own), the amount within a tenth when both are read. A list, newest first; the person decides."""
    if not _has_challans(db) or (b["lane"] or "clinic") == "pharmacy" or (b["doc_kind"] or "") == "challan":
        return []
    key = _supplier_key(b["vendor"])
    if not key:
        return []
    today = today or datetime.date.today()
    out = []
    for c in challans_awaiting(db):
        if (c["lane"] or "clinic") == "pharmacy" or _supplier_key(c["vendor"]) != key:
            continue
        if abs(_age_days(c, today) - _age_days(b, today)) > CHALLAN_MATCH_DAYS:
            continue
        if b["total_amount"] is not None and c["total_amount"] is not None and c["total_amount"] and \\
                abs(float(b["total_amount"]) - float(c["total_amount"])) > 0.10 * float(c["total_amount"]):
            continue
        out.append(dict(c=c, stamp=_stamp(c), age=_age_days(c, today), amount=c["total_amount"]))
    return out


CHALLANS_TPL = CSS + """<div class=d6><h2>Bills awaited <span class=muted>({{rows|length}})</span></h2>
<p class=lead>Every challan whose bill has not come. After {{amber}} days a line turns amber: ask the supplier for the bill.
 When the bill is scanned, its own page offers the join; a challan of the same supplier shows up there by itself.</p>
{% for r in rows %}<div class=d6card {% if r.amber %}style="background:#fff4e0"{% endif %}>
<div class=d6row><a href="{{url_for('bill_view',bid=r.b['id'])}}">{% if r.b['source_stored'] %}<img loading=lazy alt="the challan" src="{{url_for('bill_thumb',bid=r.b['id'])}}">{% endif %}</a>
<div style="flex:1;min-width:0"><div class=d6top><b><a href="{{url_for('bill_view',bid=r.b['id'])}}" style="text-decoration:none">{{r.stamp}}</a> · {{r.b['vendor'] or 'supplier not read'}}</b>
<span>{% if r.b['total_amount'] is not none %}<b>{{inr(r.b['total_amount'])}}</b>{% else %}<span class=muted>amount not read</span>{% endif %}</span></div>
<div class=muted style="font-size:13px">challan {{r.b['bill_date'] or r.b['created_at'][:10]}} · <b class=nw>{{r.age}} day{{'' if r.age==1 else 's'}}</b> · {{lanes[r.b['lane'] or 'clinic'][0].split(' — ')[0]}}{% if r.b['scanned_by'] %} · {{r.b['scanned_by']}}{% endif %}</div></div></div>
{% if (r.b['lane'] or 'clinic')=='pharmacy' %}<div class="d6say other">A pharmacy challan: handed to the Sanjeevni side; its bill is paired there.</div>
{% elif r.cands %}<div class=d6say>Scanned since, same supplier: {% for c in r.cands %}<a href="{{url_for('d664_paper',bid=c['id'],back=url_for('d664_challans'))}}"><b>{{c['stamp_no'] or ('#'~c['id'])}}</b></a>{% if c['total_amount'] is not none %} ({{inr(c['total_amount'])}}){% endif %}{{', ' if not loop.last}}{% endfor %} — open one and press Join there.</div>
{% else %}<div class="d6say none">No bill of this supplier scanned since. When it comes, scan it as a bill; its page will offer this challan.</div>{% endif %}
<div class=d6btns>
<form method=post action="{{url_for('d664_challan_close',bid=r.b['id'])}}" onsubmit="return confirm('Close {{r.stamp}} as a challan that will never get a bill?')"><input type=hidden name=back value="{{url_for('d664_challans')}}"><button class="d6b skip">Bill nahi aayega — close it</button></form>
</div></div>{% endfor %}
{% if not rows %}<div class=d6card><b>No challan is waiting for its bill.</b></div>{% endif %}
{% if closed %}<details class=d6x style="margin-top:14px"><summary class=d6opt>Closed and deleted challans ({{closed|length}})<small>kept as a record; their numbers stay</small></summary>
<div class=in style="display:block">{% for c in closed %}<div class=d6line><div style="flex:1"><a href="{{url_for('bill_view',bid=c['id'])}}"><b>{{c['stamp_no'] or ('#'~c['id'])}}</b></a> · {{c['vendor'] or 'supplier not read'}}<br><span class=muted style="font-size:13px">{{c['challan_state']}}{% if c['challan_of'] %} · joined into <a href="{{url_for('d664_paper',bid=c['challan_of'])}}">the bill</a>{% endif %}</span></div></div>{% endfor %}</div></details>{% endif %}
<p class=muted>A challan is scanned by reception with one tap, CHALLAN HAI?, before Save. It is never counted as a purchase: the bill is.</p></div>"""


def challans_page():
    db = AR.get_db()
    today = datetime.date.today()
    amber = _amber_days(db)
    rows = []
    for c in challans_awaiting(db):
        cands = []
        key = _supplier_key(c["vendor"])
        if key and (c["lane"] or "clinic") != "pharmacy":
            for b in db.execute("SELECT b.* FROM bills b WHERE b.id>? AND b.status<>'rejected' AND b.dup_of IS NULL AND COALESCE(b.doc_kind,'bill')<>'challan' "
                                "AND COALESCE(b.lane,'clinic')<>'pharmacy' ORDER BY b.id DESC LIMIT 400", (c["id"],)):
                if _supplier_key(b["vendor"]) == key:
                    cands.append(b)
        age = _age_days(c, today)
        rows.append(dict(b=c, stamp=_stamp(c), age=age, amber=(age >= amber), cands=cands[:4]))
    closed = db.execute("SELECT b.* FROM bills b WHERE b.doc_kind='challan' AND b.challan_state IN ('closed','deleted','joined') ORDER BY b.id DESC LIMIT 40").fetchall() if _has_challans(db) else []
    return AR.page(CHALLANS_TPL, rows=rows, closed=closed, amber=amber, inr=_inr, lanes=AR.LANES,
                   flow=AR._flow("Bills awaited", url_for("d664_papers")))


def challan_close(bid):
    db = AR.get_db()
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    back = _back("d664_challans")
    if not _has_challans(db) or (b["doc_kind"] or "") != "challan" or (b["challan_state"] or "awaiting") != "awaiting":
        flash("%s is not a challan waiting for its bill." % _stamp(b))
        return redirect(back)
    db.execute("UPDATE bills SET challan_state='closed' WHERE id=?", (bid,))
    AR._audit_bill(db, bid, "challan_closed", {"by": _who()})
    db.commit()
    flash("%s is closed: no bill will come for it. It stays as a record under Bills awaited." % _stamp(b))
    return redirect(back)


def challan_delete(bid):
    """After the join only: the challan row is marked deleted and its own file is MOVED to uploads/%s (its picture is
    inside the bill's PDF when the join merged it). The stamp number stays reserved; nothing is removed.""" % DELETED_DIR
    db = AR.get_db()
    c = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not c:
        abort(404)
    back = _back("d664_challans")
    if not _has_challans(db) or (c["doc_kind"] or "") != "challan" or (c["challan_state"] or "") != "joined" or not c["challan_of"]:
        flash("%s can be deleted only after it is joined to its bill." % _stamp(c))
        return redirect(back)
    head = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (c["challan_of"],)).fetchone()
    moved = ""
    if c["source_stored"]:
        try:
            src = os.path.join(AR.UPLOAD_DIR, c["source_stored"])
            dst_dir = os.path.join(AR.UPLOAD_DIR, DELETED_DIR)
            os.makedirs(dst_dir, exist_ok=True)
            if os.path.exists(src):
                os.replace(src, os.path.join(dst_dir, c["source_stored"]))
                moved = c["source_stored"]
        except OSError:
            moved = ""
    db.execute("UPDATE bills SET challan_state='deleted', reject_reason=? WHERE id=?",
               ("challan — bill came: %s (deleted)" % (_stamp(head) if head else "the bill"), bid))
    AR._audit_bill(db, bid, "challan_deleted", {"bill": (head["stamp_no"] if head else None), "file_moved": moved, "by": _who()})
    db.commit()
    flash("Challan %s is deleted. Its number stays reserved and its picture is inside %s." % (_stamp(c), _stamp(head) if head else "the bill"))
    return redirect(back)


def _challan_mark_joined(db, page, head):
    """Called by the join for every page it takes: a challan becomes 'joined' and remembers its bill."""
    try:
        if _has_challans(db) and (page["doc_kind"] or "") == "challan":
            db.execute("UPDATE bills SET challan_state='joined', challan_of=? WHERE id=?", (head["id"], page["id"]))
    except sqlite3.Error:
        pass


def _challan_mark_unjoined(db, page_id):
    try:
        if _has_challans(db):
            db.execute("UPDATE bills SET challan_state='awaiting', challan_of=NULL WHERE id=? AND doc_kind='challan' AND challan_state='joined'", (page_id,))
    except sqlite3.Error:
        pass


def challan_card(db, b, back):
    """For the paper page and the to-sort card: the challans this bill may close, with one Join button each; and, on a
    challan that is joined, the Delete button. '' when nothing applies."""
    try:
        if not _has_challans(db):
            return ""
        if (b["doc_kind"] or "") == "challan":
            st = b["challan_state"] or "awaiting"
            head = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["challan_of"],)).fetchone() if b["challan_of"] else None
            return Markup(render_template_string(CHALLAN_SELF_TPL, b=b, stamp=_stamp(b), st=st, head=head, hstamp=(_stamp(head) if head else ""), back=back))
        cands = challan_for_bill(db, b)
        if not cands:
            return ""
        return Markup(render_template_string(CHALLAN_JOIN_TPL, b=b, stamp=_stamp(b), cands=cands, inr=_inr, back=back))
    except Exception:                                                # noqa: BLE001
        return ""


CHALLAN_JOIN_TPL = """<div class=d6card style="background:#fff4e0"><b style="font-size:16px">The bill for a challan?</b>
{% for r in cands %}<p style="margin:6px 0">This may be the bill for challan <b>{{r.stamp}}</b> — {{r.c['vendor']}}, {{r.age}} day{{'' if r.age==1 else 's'}} ago{% if r.amount is not none %}, {{inr(r.amount)}} on the challan{% endif %}.</p>
<form method=post action="{{url_for('d664_join',bid=b['id'])}}" class=d6btns style="display:flex;margin:0 0 8px"><input type=hidden name=back value="{{back}}"><input type=hidden name=page value="{{r.c['id']}}"><button class="d6b yes">Yes — join {{r.stamp}} into this bill</button></form>{% endfor %}
<p class=muted style="font-size:13px;margin:4px 0 0">The join makes one PDF: the bill first, the challan after. The challan then leaves Bills awaited and can be deleted from this page.</p></div>"""

CHALLAN_SELF_TPL = """<div class=d6card style="background:#fff4e0"><b style="font-size:16px">This paper is a challan</b>
{% if st=='awaiting' %}<p style="margin:6px 0">Goods received, bill awaited. It is on <a href="{{url_for('d664_challans')}}">Bills awaited</a>; when the bill is scanned, the bill's page offers the join.</p>
{% elif st=='joined' %}<p style="margin:6px 0">Joined into <a href="{{url_for('d664_paper',bid=head['id'])}}"><b>{{hstamp}}</b></a> — one PDF now. It can be deleted: its number stays reserved and its picture is inside {{hstamp}}.</p>
<form method=post action="{{url_for('d664_challan_delete',bid=b['id'])}}" class=d6btns style="display:flex" onsubmit="return confirm('Delete challan {{stamp}}? Its picture stays inside {{hstamp}}.')"><input type=hidden name=back value="{{url_for('d664_paper',bid=head['id'],back=back)}}"><button class="d6b alt">Delete the challan {{stamp}}</button></form>
{% elif st=='closed' %}<p style="margin:6px 0">Closed: no bill will come for it.</p>
{% else %}<p style="margin:6px 0">Deleted after its bill came{% if head %} ({{hstamp}}){% endif %}; the number stays as a record.</p>{% endif %}</div>"""


def challans_count(db):
    try:
        return len(challans_awaiting(db))
    except Exception:                                                # noqa: BLE001
        return 0
'''


def build_papers(t):
    # C1 the block, before the mount (after warranty_card and friends; before 'def init(ar):')
    t = edit(t, '\n\ndef init(ar):', PAPERS_BLOCK + '\n\ndef init(ar):', "C1 block")
    # C2 challans never count as papers to sort, consumables or sections
    for name, anchor in (("C2a _live", '''    w = ("COALESCE(%s.lane,'clinic')='clinic' AND %s.status IN ('draft','approved') AND %s.dup_of IS NULL"
         % (alias, alias, alias))'''),
                         ("C2b _live_sort", '''    w = ("((COALESCE(%s.lane,'clinic')='clinic' AND %s.status IN ('draft','approved')) OR (%s.lane='other_doc' AND %s.status='captured'))"
         " AND %s.dup_of IS NULL" % (alias, alias, alias, alias, alias))'''),
                         ("C2c _live_sections", '''    w = ("COALESCE(%s.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND %s.status IN ('draft','approved','captured')"
         " AND %s.dup_of IS NULL" % (alias, alias, alias))''')):
        t = edit(t, anchor, anchor + '''
    if "doc_kind" in _cols(db):
        w += " AND COALESCE(%s.doc_kind,'bill')<>'challan'" % alias                     # S531: a challan is not a purchase''', name, "replace")
    # C3 the join marks a challan; the unjoin unmarks it
    t = edit(t, '''            AR._audit_bill(db, pg["id"], "d664_joined_into", {"to": bid, "to_stamp": head["stamp_no"], "merged": bool(merged)})''',
             '''            AR._audit_bill(db, pg["id"], "d664_joined_into", {"to": bid, "to_stamp": head["stamp_no"], "merged": bool(merged)})
            _challan_mark_joined(db, pg, head)                                                          # S531''', "C3a join marks")
    t = edit(t, '''            AR._audit_bill(db, pg["id"], "d664_unjoined", {"from": bid, "from_stamp": head["stamp_no"]})''',
             '''            AR._audit_bill(db, pg["id"], "d664_unjoined", {"from": bid, "from_stamp": head["stamp_no"]})
            _challan_mark_unjoined(db, pg["id"])                                                        # S531''', "C3b unjoin unmarks")
    # C4 the paper page carries the challan card; the to-sort card too
    t = edit(t, '''{% if can_join and (joined or not p.head) %}<div class=d6card><b style="font-size:16px">One purchase, one PDF</b>''',
             '''{{challan_html}}
{% if can_join and (joined or not p.head) %}<div class=d6card><b style="font-size:16px">One purchase, one PDF</b>''', "C4a paper tpl")
    t = edit(t, '''                   accepts=((b["lane"] or "clinic") == "clinic" and b["status"] == "draft"),''',
             '''                   accepts=((b["lane"] or "clinic") == "clinic" and b["status"] == "draft"),
                   challan_html=challan_card(db, b, _back()),                                           # S531''', "C4b paper ctx")
    t = edit(t, '''{% if p.after %}<div class="d6say other">The next {{'scan' if p.after|length==1 else (p.after|length)|string ~ ' scans'}}''',
             '''{% if p.challans %}<div class="d6say other">This may be the bill for challan <b>{{p.challans[0].stamp}}</b> — {{p.challans[0].age}} day{{'' if p.challans[0].age==1 else 's'}} ago{% if p.challans|length>1 %} (and {{p.challans|length-1}} more){% endif %}. <a href="{{url_for('d664_paper',bid=p.b['id'],back=url_for('d664_papers'))}}">Open it to join.</a></div>{% endif %}
{% if p.after %}<div class="d6say other">The next {{'scan' if p.after|length==1 else (p.after|length)|string ~ ' scans'}}''', "C4c to-sort card")
    t = edit(t, '''                njoined=(len(_joined(db, b["id"])) if _can_join(db) else 0),
                head_stamp=(_stamp(head) if head else ""))''',
             '''                njoined=(len(_joined(db, b["id"])) if _can_join(db) else 0),
                head_stamp=(_stamp(head) if head else ""), challans=challan_for_bill(db, b))             # S531''', "C4d _paper")
    # C5 the stand fold and the month page carry the challans
    t = edit(t, '''        total = n("SELECT COUNT(*) " + base)
        waiting = db.execute("SELECT COUNT(*) FROM bills b WHERE " + _live_sort(db) + " AND COALESCE(b.subgroup,'')=''").fetchone()[0]''',
             '''        ch = challans_count(db)
        if ch or _has_challans(db):
            rows.append(dict(name="Challans \\u2014 bills awaited", n=ch, text="goods received, bill not yet scanned" if ch else "none waiting", href=url_for("d664_challans")))
        total = n("SELECT COUNT(*) " + base)
        waiting = db.execute("SELECT COUNT(*) FROM bills b WHERE " + _live_sort(db) + " AND COALESCE(b.subgroup,'')=''").fetchone()[0]''', "C5a stand")
    t = edit(t, '''<p class=lead>For you or Shavez. Staff are asked nothing new when they scan. One tap sorts a paper and accepts it.
 &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a></p>''',
             '''<p class=lead>For you or Shavez. Staff are asked nothing new when they scan. One tap sorts a paper and accepts it.
 &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a> &nbsp;<a href="{{url_for('d664_challans')}}">Bills awaited{% if nch %} ({{nch}}){% endif %} →</a></p>''', "C5b papers head link")
    t = edit(t, '''                   inr=_inr, cons=CONSUMABLE, stand=(stand(db) if AR.is_owner() else None),''',
             '''                   inr=_inr, cons=CONSUMABLE, stand=(stand(db) if AR.is_owner() else None), nch=challans_count(db),''', "C5c papers ctx")
    # C6 the routes
    t = edit(t, '''    app.add_url_rule("/papers/<int:bid>/warranty", "d664_warranty", ar.checker_required(set_warranty), methods=["POST"])''',
             '''    app.add_url_rule("/papers/<int:bid>/warranty", "d664_warranty", ar.checker_required(set_warranty), methods=["POST"])
    app.add_url_rule("/papers/challans", "d664_challans", ar.checker_required(challans_page))                              # S531
    app.add_url_rule("/papers/challans/<int:bid>/close", "d664_challan_close", ar.checker_required(challan_close), methods=["POST"])
    app.add_url_rule("/papers/challans/<int:bid>/delete", "d664_challan_delete", ar.checker_required(challan_delete), methods=["POST"])''', "C6 routes")
    t = edit(t, 'VERSION = "S530.1"', 'VERSION = "S531.1"', "C7 version")
    t = edit(t, 'import datetime\nimport re\nimport secrets\nimport sqlite3\nimport sys\n', 'import datetime\nimport os\nimport re\nimport secrets\nimport sqlite3\nimport sys\n', "C8 import os")
    assert t.count("S531") >= 10, t.count("S531")
    return t


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    live, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    srcs = {}
    for name, want in FROM.items():
        b = open(os.path.join(live, name), "rb").read()
        if md5(b) != want:
            raise SystemExit("REFUSED: %s is %s, not the pinned %s" % (name, md5(b)[:8], want[:8]))
        srcs[name] = b.decode("utf-8")
    outs = {"scanner_widget.js": build_widget(srcs["scanner_widget.js"]), "asset_register.py": build_app(srcs["asset_register.py"]),
            "clinic_papers.py": build_papers(srcs["clinic_papers.py"])}
    for name, text in outs.items():
        nb = text.encode("utf-8")
        open(os.path.join(out, name), "wb").write(nb)
        print("%s  %s  %d bytes" % (md5(nb), name, len(nb)))
    print("BUILT")


if __name__ == "__main__":
    main()
