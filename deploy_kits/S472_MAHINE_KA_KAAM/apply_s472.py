#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s472.py -- S472_MAHINE_KA_KAAM (session 293, 04-Oct-2026). Exact-anchor edits on three files, CHAINED ON S471:
packs.py 6738d65d (S471's result) · packs_checklist.html 12ac3f27 (the 04-Oct bundle) · /root/portal/portal.py 1a9fb99d (S450).

The owner's words (04-Oct): "the Shavez Mahine ka kaam etc also needs a better flow". Built as planned and agreed:
  (a) a DATED RHYTHM: every item carries a due day of the following month (data, not code: a column packs_item.due_day, seeded
      from the item's kind -- Docterz days the 1st, the statements and scans the 5th, the NEFT the 7th, the hand-overs and the
      accountant's things the 10th -- and editable on the owner's page); the staff page opens with 'Aaj ka kaam' (what is due
      today or late), each row says 'N tak', a late one says so in red.
  (b) a NUDGE where Shavez already looks: the 'Mahine ka kaam' tile on his portal carries a live line -- 'N kaam baaki · M late ·
      aaj: <item>' -- from a new read-only door /finance/packs/api/checklist/line (staff-gated, fail-soft; the static text stands
      when it does not answer). No WhatsApp: a staff message outside a patient's window needs an approved template, and there is
      none for this; the tile is the one place he opens every day.
  (c) a HAND-OVER is ticked WITH A PHOTO of what was handed over (the register, the receipt book, the cheque register, the petty
      book): the tick door takes an optional photo (multipart; jpeg/png, 8 MB), kept under the packs folder; the row shows
      'photo ✓' with a link; a tick without a photo still works (the fallback stays) after a one-tap confirmation.
  (d) the button reads 'Ho gaya — tick karein'; a done row shows who and when.
  (e) the owner's section on /finance/packs shows what is LATE first (red), then open-with-due, the done ones folded away.
Every anchor must be found exactly once; all three files are verified before any is written.
   usage: apply_s472.py <packs.py> <packs_checklist.html> <portal.py>
"""
import hashlib
import sys

FROM = {"packs.py": "6738d65dacd26b3f308fe8fd688b806a", "packs_checklist.html": "12ac3f27f532e9604b77f8affd47c742",
        "portal.py": "1a9fb99dfab46621a91c3fa041e37b50"}

PY_EDITS = [
    ('''STMT_FILE_COLS = (("locked", "INTEGER NOT NULL DEFAULT 0"), ("unlocked_path", "TEXT"), ("unlocked_at", "TEXT"))
''',
     '''STMT_FILE_COLS = (("locked", "INTEGER NOT NULL DEFAULT 0"), ("unlocked_path", "TEXT"), ("unlocked_at", "TEXT"))
PACKS_ITEM_COLS = (("due_day", "INTEGER"),)                       # S472: the day of the FOLLOWING month an item is due by
# S472: the default due day by the item's kind (the owner edits any item's day on his page; a NULL keeps this rule)
DUE_BY_KEY = {"clinic_days": 1, "sanj_stmts": 5, "clinic_stmts": 5, "scans_clear": 5, "pm_final": 5, "neft_done": 7, "sent": 10}
DUE_BY_GROUP = {"Clinic": 3, "Lab": 10, "Sanjeevni": 10, "Accountant ka samaan": 10}
HANDOVER_WORDS = ("register", "receipt book", "cheque register", "petty book", "kaagaz")   # a manual item that hands a thing over: photo
HANDOVER_DIR = os.environ.get("PACKS_HANDOVER_DIR", os.path.join(PACK_DIR, "handover"))
'''),
    ('''    for c, d in STMT_FILE_COLS:
        if c not in have:
            con.execute("ALTER TABLE stmt_file ADD COLUMN %s %s" % (c, d))
''',
     '''    for c, d in STMT_FILE_COLS:
        if c not in have:
            con.execute("ALTER TABLE stmt_file ADD COLUMN %s %s" % (c, d))
    have_i = {r[1] for r in con.execute("PRAGMA table_info(packs_item)")}          # S472
    for c, d in PACKS_ITEM_COLS:
        if c not in have_i:
            con.execute("ALTER TABLE packs_item ADD COLUMN %s %s" % (c, d))
'''),
    ('''def checklist(con, month):
    ensure(con)
    rows, _att = pack_rows(con, month, light=True)
    by = {r["key"]: r for r in rows}
    done = {r[0]: (r[1], r[2]) for r in con.execute("SELECT item_id, done_by, done_at FROM packs_done WHERE month=?", (month,))}
    out = []
    for it in [dict(r) for r in con.execute("SELECT * FROM packs_item WHERE active=1 ORDER BY sort, id")]:
        auto, words = _auto_state(con, month, it["auto_key"], by)
        d = done.get(it["id"])
        out.append(dict(id=it["id"], grp=it["grp"], item=it["item"], auto=(it["auto_key"] is not None), auto_done=auto, words=words,
                        done=bool(d) or bool(auto), done_by=(d[0] if d else ("system" if auto else None)), done_at=(d[1] if d else None)))
    return out
''',
     '''def _due_day(it):
    """S472: the day of the following month this item is due by -- the owner's own value, else the rule by kind."""
    try:
        if it.get("due_day"):
            return max(1, min(28, int(it["due_day"])))
    except (TypeError, ValueError):
        pass
    k = it.get("auto_key") or ""
    if k in DUE_BY_KEY:
        return DUE_BY_KEY[k]
    if k.startswith("row:") or k.startswith("slot:"):
        return 10 if k.startswith("row:") else 5
    return DUE_BY_GROUP.get(it.get("grp") or "", 10)


def _due_iso(month, day):
    """The due date of month's checklist: <day> of the FOLLOWING month."""
    y, m = int(month[:4]), int(month[5:7])
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return "%04d-%02d-%02d" % (y, m, day)


def _is_handover(it):
    s = (it.get("item") or "").lower()
    return not it.get("auto_key") and any(w in s for w in HANDOVER_WORDS)


def checklist(con, month, today=None):
    ensure(con)
    today = today or _today()
    rows, _att = pack_rows(con, month, light=True)
    by = {r["key"]: r for r in rows}
    done = {r[0]: (r[1], r[2], r[3]) for r in con.execute("SELECT item_id, done_by, done_at, note FROM packs_done WHERE month=?", (month,))}
    out = []
    for it in [dict(r) for r in con.execute("SELECT * FROM packs_item WHERE active=1 ORDER BY sort, id")]:
        auto, words = _auto_state(con, month, it["auto_key"], by)
        d = done.get(it["id"])
        dd = _due_day(it)
        due = _due_iso(month, dd)
        is_done = bool(d) or bool(auto)
        photo = (d[2] if (d and d[2] and str(d[2]).startswith("handover/")) else None)
        out.append(dict(id=it["id"], grp=it["grp"], item=it["item"], auto=(it["auto_key"] is not None), auto_done=auto, words=words,
                        done=is_done, done_by=(d[0] if d else ("system" if auto else None)), done_at=(d[1] if d else None),
                        due_day=dd, due=due, late=(not is_done and today.isoformat() > due), due_today=(not is_done and today.isoformat() == due),   # S472
                        handover=_is_handover(it), photo=photo))
    return out


def checklist_line(con, month=None, today=None):
    """S472: the one line for Shavez's tile: 'N kaam baaki · M late · aaj: <item>'. Hindi, counts only."""
    today = today or _today()
    month = month or _prev_month(today.strftime("%Y-%m"))
    items = checklist(con, month, today)
    open_ = [x for x in items if not x["done"]]
    late = [x for x in open_ if x["late"]]
    due_today = [x for x in open_ if x["due_today"]]
    if not open_:
        text = "%s: sab ho gaya ✓" % _month_name(month)
    else:
        text = "%d kaam baaki" % len(open_)
        if late:
            text += " · %d late" % len(late)
        if due_today:
            text += " · aaj: " + due_today[0]["item"][:40]
        elif late:
            text += " · pehle: " + late[0]["item"][:40]
    return dict(ok=True, month=month, open=len(open_), late=len(late), due_today=len(due_today), text_hi=text)
'''),
    ('''    con.execute("INSERT INTO packs_done (month, item_id, done_by, done_at, note) VALUES (?,?,?,?,?)", (m, iid, _who(u), _now(), str(b.get("note") or "")[:120]))
    con.commit()
    return jsonify(ok=True, done_by=_who(u), done_at=_now()), 200
''',
     '''    note = str(b.get("note") or "")[:120]
    photo_rel = _save_handover_photo(m, iid)                      # S472: the photo of what was handed over, when one came
    if photo_rel:
        note = photo_rel
    con.execute("INSERT INTO packs_done (month, item_id, done_by, done_at, note) VALUES (?,?,?,?,?)", (m, iid, _who(u), _now(), note))
    con.commit()
    return jsonify(ok=True, done_by=_who(u), done_at=_now(), photo=bool(photo_rel)), 200


def _save_handover_photo(month, iid):
    """S472: the optional photo on a tick (multipart field 'photo'; jpeg/png; 8 MB) -> handover/<month>/<item>_<stamp>.<ext>
    under the packs folder; returns the relative path or None. A bad file is refused silently (the tick still stands)."""
    f = request.files.get("photo") if request.files else None
    if not f or not f.filename:
        return None
    blob = f.read(8 * 1024 * 1024 + 1)
    if not blob or len(blob) > 8 * 1024 * 1024:
        return None
    ext = "jpg" if blob[:3] == b"\\xff\\xd8\\xff" else ("png" if blob[:8] == b"\\x89PNG\\r\\n\\x1a\\n" else None)
    if not ext:
        return None
    rel = "handover/%s/%d_%s.%s" % (month, iid, _now().replace(":", "").replace("-", "")[:15], ext)
    path = os.path.join(PACK_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(blob)
    return rel


@bp.route("/finance/packs/api/checklist/line")
def api_checklist_line():
    """S472: the tile's line (staff and the owner). Counts and one item name; nothing else."""
    u, err = _staff()
    if err:
        return err
    try:
        return jsonify(**checklist_line(_db()))
    except Exception:                                          # noqa: BLE001 -- the tile never waits on this
        return jsonify(ok=False), 200


@bp.route("/finance/packs/handover/<month>/<name>")
def page_handover(month, name):
    """S472: a hand-over photo, to staff and the owner."""
    u, err = _staff()
    if err:
        return err
    if not _good_month(month) or not re.fullmatch(r"[0-9]+_[0-9T]+\\.(jpg|png)", name or ""):
        return "no such photo", 404
    p = os.path.join(PACK_DIR, "handover", month, name)
    if not os.path.exists(p):
        return "no such photo", 404
    return send_file(p, as_attachment=False)
'''),
    # the tick door must read a multipart body too (the photo); JSON stays the first choice
    ('''def api_checklist_tick():
    u, err = _staff()
    if err:
        return err
    b = request.get_json(silent=True) or {}
''',
     '''def api_checklist_tick():
    u, err = _staff()
    if err:
        return err
    b = request.get_json(silent=True) or (dict(request.form) if request.form else {})      # S472: multipart when a photo comes
'''),
    # the owner edits an item's due day
    ('''        if act == "rename":
            con.execute("UPDATE packs_item SET item=?, edited_by=?, edited_at=? WHERE id=?", (str(b.get("item") or "").strip()[:160], _who(u), _now(), iid))
''',
     '''        if act == "rename":
            con.execute("UPDATE packs_item SET item=?, edited_by=?, edited_at=? WHERE id=?", (str(b.get("item") or "").strip()[:160], _who(u), _now(), iid))
            try:                                                                              # S472: the due day rides the same tap
                dd = int(b.get("due_day")) if b.get("due_day") not in (None, "") else None
                con.execute("UPDATE packs_item SET due_day=? WHERE id=?", ((max(1, min(28, dd)) if dd else None), iid))
            except (TypeError, ValueError):
                pass
'''),
]

CHK_EDITS = [
    ('''    var open=j.items.filter(function(c){return !c.done}).length;
    var h='<div class="mut">'+(open?('<span class="open">'+open+' kaam baaki</span>'):'<span class="ok">sab ho gaya ✓</span>')+'</div><div id="plan428"></div>';''',
     '''    var open=j.items.filter(function(c){return !c.done}).length, late=j.items.filter(function(c){return !c.done&&c.late}), today=j.items.filter(function(c){return !c.done&&c.due_today});
    var h='<div class="mut">'+(open?('<span class="open">'+open+' kaam baaki</span>'+(late.length?' · <span class="late">'+late.length+' late</span>':'')):'<span class="ok">sab ho gaya ✓</span>')+'</div><div id="plan428"></div>';
    /* S472: aaj ka kaam -- what is due today or already late, first */
    if(late.length||today.length){h+='<h2>Aaj ka kaam</h2>'+late.concat(today).map(function(c){return '<div class="row"><div>'+esc(c.item)+' <span class="mut">('+esc(c.grp)+')</span></div><div style="text-align:right">'+(c.late?'<span class="late">late — '+c.due_day+' tak tha</span>':'<span class="open">aaj tak</span>')+'</div></div>'}).join("")}'''),
    ('''      var right=c.done?('<span class="ok">'+(c.auto?'system se ho gaya ✓':'ho gaya ✓')+'</span><br><span class="mut">'+esc(c.done_by||"")+' '+esc((c.done_at||"").slice(0,16))+' '+esc(c.words||"")+'</span>')
                      :(c.auto?('<span class="open">baaki</span><br><span class="mut">system dekhega · '+esc(c.words||"")+'</span>'):('<button onclick="tick('+c.id+')">Ho gaya</button>'));
      return '<div class="row"><div>'+esc(c.item)+'</div><div style="text-align:right">'+right+'</div></div>'}).join("")});''',
     '''      var due='<span class="mut">'+c.due_day+' tak</span>';
      var right=c.done?('<span class="ok">'+(c.auto?'system se ho gaya ✓':'ho gaya ✓')+'</span>'+(c.photo?' <a href="/finance/packs/'+esc(c.photo)+'" target="_blank">photo ✓</a>':'')+'<br><span class="mut">'+esc(c.done_by||"")+' '+esc((c.done_at||"").slice(0,16))+' '+esc(c.words||"")+'</span>')
                      :(c.auto?('<span class="open">baaki</span><br><span class="mut">system dekhega · '+esc(c.words||"")+' · '+c.due_day+' tak</span>')
                      :(c.handover?('<label class="pbtn">📷 Photo ke saath ho gaya<input type="file" accept="image/*" capture="environment" onchange="tickPhoto('+c.id+',this)"></label> <button class="ghost" onclick="tick('+c.id+',true)">bina photo</button><br>'+(c.late?'<span class="late">late — '+c.due_day+' tak tha</span>':due))
                      :('<button onclick="tick('+c.id+')">Ho gaya — tick karein</button><br>'+(c.late?'<span class="late">late — '+c.due_day+' tak tha</span>':due))));
      return '<div class="row"><div>'+esc(c.item)+'</div><div style="text-align:right">'+right+'</div></div>'}).join("")});'''),
    ('''function tick(id){fetch("/finance/packs/api/checklist/tick",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({month:$("m").value,id:id})}).then(function(r){return r.json()}).then(function(j){
  if(!j.ok){alert(j.message||j.error);return} $("flash").innerHTML='<div class="green">'+(j.already?'Pehle se likha hai.':'Ho gaya — aapke naam se likh liya.')+'</div>'; load()}).catch(function(){alert("save nahi hua — server nahi mila")})}''',
     '''function after(j){if(!j.ok){alert(j.message||j.error);return} $("flash").innerHTML='<div class="green">'+(j.already?'Pehle se likha hai.':('Ho gaya — aapke naam se likh liya'+(j.photo?', photo ke saath':'')+'.'))+'</div>'; load()}
function tick(id,noPhoto){if(noPhoto&&!confirm("Bina photo ke tick karein?"))return;
  fetch("/finance/packs/api/checklist/tick",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({month:$("m").value,id:id})}).then(function(r){return r.json()}).then(after).catch(function(){alert("save nahi hua — server nahi mila")})}
/* S472: the hand-over's photo rides the same tick, as a form */
function tickPhoto(id,inp){if(!inp.files||!inp.files[0])return; var fd=new FormData(); fd.append("month",$("m").value); fd.append("id",id); fd.append("photo",inp.files[0]);
  fetch("/finance/packs/api/checklist/tick",{method:"POST",body:fd}).then(function(r){return r.json()}).then(after).catch(function(){alert("save nahi hua — server nahi mila")})}'''),
    ('''.row:first-child{border-top:0}.ok{color:#2f6b45;font-weight:700}.open{color:#8a6100;font-weight:700}''',
     '''.row:first-child{border-top:0}.ok{color:#2f6b45;font-weight:700}.open{color:#8a6100;font-weight:700}.late{color:#9c2a20;font-weight:700}
.pbtn{display:inline-block;background:#14456e;color:#fff;border-radius:10px;padding:10px 14px;font-size:16px;cursor:pointer}.pbtn input{display:none}button.ghost{background:#fff;color:#14456e;border:1px solid #8a9aa6;font-size:15px;padding:8px 10px}'''),
]

PORTAL_EDITS = [
    ('''     "desc": "Mahine ke ant ka kaam \\u2014 tick karo",
     "live": True,
''',
     '''     "desc": "Mahine ke ant ka kaam \\u2014 tick karo",
     "packs_counts": True,     # S472: the live line 'N kaam baaki · M late · aaj: ...' (fail-soft, the text above stands)
     "live": True,
'''),
    ('''        <div class="ds"{% if t.review_counts %} data-review-counts{% endif %}{% if t.gist %} data-gist-summary{% endif %}{% if t.sanjeevni_counts %} data-sanjeevni-counts{% endif %}{% if t.daily_sale_counts %} data-daily-sale-counts{% endif %}>{{ t.desc }}</div></div>''',
     '''        <div class="ds"{% if t.review_counts %} data-review-counts{% endif %}{% if t.gist %} data-gist-summary{% endif %}{% if t.sanjeevni_counts %} data-sanjeevni-counts{% endif %}{% if t.daily_sale_counts %} data-daily-sale-counts{% endif %}{% if t.packs_counts %} data-packs-counts{% endif %}>{{ t.desc }}</div></div>'''),
    ('''/* Daily Sale tile: the maker's own to-do line (S187_P2a). Fail-soft: no
   medical seat or finance down -> the static text stands. */
(function(){
  var el=document.querySelector('[data-daily-sale-counts]');
  if(!el)return;''',
     '''/* S472: Shavez's 'Mahine ka kaam' tile -- 'N kaam baaki · M late · aaj: ...'. Fail-soft:
   no packs seat or finance down -> the static text stands. */
(function(){
  var el=document.querySelector('[data-packs-counts]');
  if(!el)return;
  fetch('/finance/packs/api/checklist/line',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){ if(d&&d.ok&&d.text_hi){ el.textContent=d.text_hi; if(d.late){el.style.color='#9c2a20';} } })
   .catch(function(){});
})();
/* Daily Sale tile: the maker's own to-do line (S187_P2a). Fail-soft: no
   medical seat or finance down -> the static text stands. */
(function(){
  var el=document.querySelector('[data-daily-sale-counts]');
  if(!el)return;'''),
]


def apply(src, edits, what):
    for n, (old, new) in enumerate(edits, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! %s anchor %d was found %d time(s), expected 1 - nothing written" % (what, n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: apply_s472.py <packs.py> <packs_checklist.html> <portal.py>")
    plan = [("packs.py", sys.argv[1], PY_EDITS), ("packs_checklist.html", sys.argv[2], CHK_EDITS), ("portal.py", sys.argv[3], PORTAL_EDITS)]
    outs = []
    for name, path, edits in plan:
        raw = open(path, "rb").read()
        have = hashlib.md5(raw).hexdigest()
        if have != FROM[name]:
            raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM[name]))
        out = apply(raw.decode("utf-8"), edits, name).encode("utf-8")
        if name.endswith(".py"):
            compile(out, path, "exec")
        outs.append((name, path, raw, out, len(edits)))
    for name, path, raw, out, n in outs:
        with open(path, "wb") as fh:
            fh.write(out)
        print("%s %s -> %s (%d edits; %+d bytes)" % (name, hashlib.md5(raw).hexdigest()[:8], hashlib.md5(out).hexdigest()[:8], n, len(out) - len(raw)))


if __name__ == "__main__":
    main()
