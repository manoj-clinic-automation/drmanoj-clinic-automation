#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s654.py -- builds kit S654_SLIP_TOOLS's two files from the LIVE bytes (D789; session 354, 25-Oct-2026).

  python3 make_s654.py <dir holding the live slip_log.py and parchi_desk.py> <out dir>

slip_log.py  (93103944), 5 counted edits:
  1 ensure(): slip_book gains prev_first_no / prev_last_no (the book before this one), filled once from the book size
  2 log_slip(): a number of the PREVIOUS book is accepted (a late entry, or a leftover slip) -- the message names both ranges
  3 set_book(): the old range is kept as the previous book
  4 renumber_slip(): a saved slip of the last LATE_DAYS days gets a new number (a 'missing' row at that number is taken over)
    void_past_slip(): a saved slip of the last LATE_DAYS days is removed, with a reason -- the desk's two new doors
  5 the version line
parchi_desk.py (99b7e43b), 4 counted edits:
  1 two JSON doors: /finance/slips/desk/api/renumber and /finance/slips/desk/api/void
  2 words for the two buttons (Hindi / English)
  3 the day's OPD and X-ray rows carry 'No.' and 'Hatao'; a tap opens a small inline form (new number / reason) with Theek
  4 the version line
Each base must be the pinned live file and each piece must occur exactly once, or nothing is written."""
import hashlib
import os
import sys

BASE = {"slip_log.py": "93103944a60cbce13ec4dde462626bf6", "parchi_desk.py": "99b7e43b95a034398962269dc6ce84fa"}

SL_EDITS = [
    # 1 -- ensure(): the previous book's range, migrated in place
    ('''    for s, (a, b) in BOOKS.items():
        con.execute("INSERT OR IGNORE INTO slip_book(series, first_no, last_no, start_no, set_by, set_at) "
                    "VALUES (?,?,?,NULL,'seed',?)", (s, a, b, _stamp()))
    con.commit()
    _schema_done = True
''',
     '''    for s, (a, b) in BOOKS.items():
        con.execute("INSERT OR IGNORE INTO slip_book(series, first_no, last_no, start_no, set_by, set_at) "
                    "VALUES (?,?,?,NULL,'seed',?)", (s, a, b, _stamp()))
    try:                                                  # S654 (D789): the book BEFORE this one -- its numbers stay valid
        cols = {r[1] for r in con.execute("PRAGMA table_info(slip_book)")}
        if "prev_first_no" not in cols:
            con.execute("ALTER TABLE slip_book ADD COLUMN prev_first_no INTEGER")
            con.execute("ALTER TABLE slip_book ADD COLUMN prev_last_no INTEGER")
        for r in con.execute("SELECT series, first_no, last_no FROM slip_book WHERE prev_first_no IS NULL").fetchall():
            size = int(r[2]) - int(r[1]) + 1                 # the first time: the same size, just before this book
            if size > 0 and int(r[1]) - size >= 1:
                con.execute("UPDATE slip_book SET prev_first_no=?, prev_last_no=? WHERE series=?",
                            (int(r[1]) - size, int(r[1]) - 1, r[0]))
    except Exception:                                    # noqa: BLE001 -- the slips still save without it
        pass
    con.commit()
    _schema_done = True
'''),
    # 2 -- log_slip(): the previous book's number is accepted
    ('''    if not (b["first_no"] <= slip_no <= b["last_no"]):
        raise SlipError("%d is book (%d–%d) ka number nahi hai. Book badli ho to neeche "
                        "'Book' mein naya range likhein." % (slip_no, b["first_no"], b["last_no"]))
''',
     '''    if not (b["first_no"] <= slip_no <= b["last_no"]) and not _in_prev_book(b, slip_no):   # S654: the old book's number is fine
        pa, pb = _prev_range(b)
        raise SlipError("%d is book (%d–%d%s) ka number nahi hai. Book badli ho to neeche "
                        "'Book' mein naya range likhein." % (slip_no, b["first_no"], b["last_no"],
                                                              (", pichhli %d–%d" % (pa, pb)) if pa else ""))
'''),
    # 3 -- set_book(): the old range becomes the previous book
    ('''    old = book(con, series)
    con.execute("UPDATE slip_book SET first_no=?, last_no=?, start_no=?, set_by=?, set_at=? WHERE series=?",
                (a, b, st, _who(u), _stamp(), series))
''',
     '''    old = book(con, series)
    con.execute("UPDATE slip_book SET first_no=?, last_no=?, start_no=?, set_by=?, set_at=? WHERE series=?",
                (a, b, st, _who(u), _stamp(), series))
    if old is not None and (old["first_no"], old["last_no"]) != (a, b):      # S654 (D789): the old book's numbers stay valid
        con.execute("UPDATE slip_book SET prev_first_no=?, prev_last_no=? WHERE series=?",
                    (old["first_no"], old["last_no"], series))
'''),
    # 4 -- the two desk doors, beside log_slip's helpers
    ('''# ---------------------------------------------------------------- writing a slip
class SlipError(Exception):
    pass
''',
     '''# ---------------------------------------------------------------- writing a slip
class SlipError(Exception):
    pass


def _prev_range(b):
    """(first, last) of the book before this one, or (None, None)."""
    try:
        pa, pb = b["prev_first_no"], b["prev_last_no"]
    except (IndexError, KeyError):
        return None, None
    return (int(pa), int(pb)) if (pa is not None and pb is not None) else (None, None)


def _in_prev_book(b, no):
    pa, pb = _prev_range(b)
    return pa is not None and pa <= int(no) <= pb


def _fixable(con, who, sid):
    """S654 (D789): a SAVED slip of the last LATE_DAYS days, as the desk may change it. Raises SlipError."""
    s = con.execute("SELECT * FROM slip WHERE id=?", (sid,)).fetchone()
    if s is None or s["state"] == "void":
        raise SlipError("Parchi nahi mili.")
    if s["state"] != "ok":
        raise SlipError("Parchi %d likhi hui nahi hai (%s) -- 'Aaj ki list' mein batayein." % (s["slip_no"], s["state"]))
    if _late_day(s["day"]) is None:
        raise SlipError("Parchi %d %d din se purani hai -- ab nahi badal sakti." % (s["slip_no"], LATE_DAYS))
    return s


def renumber_slip(con, who, sid, new_no, why):
    """S654 (D789, the owner 25-Oct-2026: a slip saved under the wrong number). The number of a saved slip of the last
    LATE_DAYS days changes to new_no -- a number of this book or the previous one, not used by another saved slip. A
    'missing' row at new_no is taken over (it was this very slip). Everything the slip carries (items, chhoot, paid ticks)
    stays. Returns (old_no, new_no). Audited."""
    s = _fixable(con, who, sid)
    new_no = _int(new_no)
    why = (why or "").strip()[:120]
    if new_no is None or new_no <= 0:
        raise SlipError("Naya number likhein.")
    if new_no == s["slip_no"]:
        raise SlipError("Yahi number pehle se hai.")
    if not why:
        raise SlipError("Number badalne ki wajah likhein.")
    b = book(con, s["series"])
    if not b or not ((b["first_no"] <= new_no <= b["last_no"]) or _in_prev_book(b, new_no)):
        pa, pb = _prev_range(b) if b else (None, None)
        raise SlipError("%d is book (%d–%d%s) ka number nahi hai." % (new_no, b["first_no"] if b else 0, b["last_no"] if b else 0,
                                                                   (", pichhli %d–%d" % (pa, pb)) if pa else ""))
    cur = _live(con, s["series"], new_no)
    now = _stamp()
    if cur is not None and cur["state"] != "missing":
        raise SlipError("Parchi %d pehle se likhi hai (%s, %s)." % (new_no, cur["logged_by"] or "?", (cur["logged_at"] or "")[11:16]))
    if cur is not None:                                   # the skipped number was this slip all along
        con.execute("UPDATE slip SET state='void', note=?, updated_by=?, updated_at=? WHERE id=?",
                    ("number %d given to slip %d (S654)" % (new_no, s["id"]), who, now, cur["id"]))
    con.execute("UPDATE slip SET slip_no=?, note=?, updated_by=?, updated_at=? WHERE id=?",
                (new_no, ("tha %d: %s" % (s["slip_no"], why))[:200], who, now, s["id"]))
    _audit_safe(con, s["id"], "slip_renumber", json.dumps({"slip_no": s["slip_no"]}),
                json.dumps({"slip_no": new_no, "why": why, "took_missing": bool(cur is not None)}), who)
    con.commit()
    return s["slip_no"], new_no


def void_past_slip(con, who, sid, why):
    """S654 (D789): a saved slip of the last LATE_DAYS days is taken off, with a reason (one's own same-day entry needs
    none -- as the list's Hatao). Its chhoot waiting for approval is withdrawn. Returns the slip's number. Audited."""
    s = _fixable(con, who, sid)
    why = (why or "").strip()[:120]
    same = s["logged_by"] == who and (s["logged_at"] or "")[:10] == _today()
    if not same and not why:
        raise SlipError("Parchi %d hatane ki wajah likhein." % s["slip_no"])
    now = _stamp()
    con.execute("UPDATE slip SET state='void', note=?, updated_by=?, updated_at=? WHERE id=?",
                (why or "same-day correction", who, now, s["id"]))
    try:
        con.execute("UPDATE slip_adjust SET state='replaced' WHERE slip_id=? AND state='pending'", (s["id"],))
    except Exception:                                    # noqa: BLE001 -- no slip_adjust table: nothing to take back
        pass
    _audit_safe(con, s["id"], "slip_void", json.dumps({"state": "ok"}), json.dumps({"state": "void", "why": why or "same-day",
                                                                                   "via": "desk"}), who)
    con.commit()
    return s["slip_no"]
'''),
]

PD_EDITS = [
    # 1 -- the two doors, before the page
    ('''# ---------------------------------------------------------------- the page
PAGE = r"""''',
     '''@bp.route("/finance/slips/desk/api/renumber", methods=["POST"])
def api_renumber():
    """S654 (D789): a saved parchi of the day shown gets a new number. JSON {id, no, why} in; the day's state out."""
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    f = _body()
    who = SL._who(u)
    day = _day_arg(f.get("day"))
    if day is None:
        return _j(ok=False, err="Din sahi chunein.")
    try:
        old, new = SL.renumber_slip(con, who, int(f.get("id") or 0), f.get("no"), f.get("why"))
    except SL.SlipError as ex:
        return _j(ok=False, err=str(ex), state=state(con, day, who))
    except (TypeError, ValueError):
        return _j(ok=False, err="Galat form.")
    return _j(ok=True, msg="Parchi %d ab %d hai." % (old, new), state=state(con, day, who))


@bp.route("/finance/slips/desk/api/void", methods=["POST"])
def api_void():
    """S654 (D789): a saved parchi of the day shown is taken off, with a reason. JSON {id, why} in; the day's state out."""
    u, err = _gate()
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    f = _body()
    who = SL._who(u)
    day = _day_arg(f.get("day"))
    if day is None:
        return _j(ok=False, err="Din sahi chunein.")
    try:
        no = SL.void_past_slip(con, who, int(f.get("id") or 0), f.get("why"))
    except SL.SlipError as ex:
        return _j(ok=False, err=str(ex), state=state(con, day, who))
    except (TypeError, ValueError):
        return _j(ok=False, err="Galat form.")
    return _j(ok=True, msg="Parchi %d hata di." % no, state=state(con, day, who))


# ---------------------------------------------------------------- the page
PAGE = r"""'''),
    # 2 -- the words
    ('''gapok:["Haan, yahi number","Yes, this number"],''',
     '''gapok:["Haan, yahi number","Yes, this number"],renum:["No.","No."],hatao:["Hatao","Remove"],newno:["Naya number","New number"],fixwhy:["wajah (zaroori)","reason (required)"],theek:["Theek","OK"],rehne:["Rehne do","Cancel"],'''),
    # 3 -- the rows carry the two buttons; the inline form
    (''' rows($('lo'),st.opd,function(o){return '<div class="lr"><span class="n">'+o.no+'</span><span class="t">'+esc(o.cid||'')+' '+esc(o.name||'')+(o.new?' <b>'+(EN?'new':'naya')+'</b>':'')+'</span><span class="m">'+esc(o.by)+' '+esc(o.at)+'</span></div>';},'lo_n');
 rows($('lx'),st.xp,function(o){return '<div class="lr"><span class="n">'+o.no+'</span><span class="t">'+esc(o.cid||'')+' '+esc(o.name||'')+'<br><span class="sm">'+o.items.map(function(i){return esc(i.n+(i.side?' '+i.side:''))+(i.d?' (chhoot '+rs(i.d)+')':'');}).join(' · ')+'</span></span><span class="m">'+rs(o.total)+'<br>'+esc(o.by)+' '+esc(o.at)+'</span></div>';},'lx_n');
''',
     ''' function fx(o){return '<span class="fx"><button type="button" class="fxb" data-fx="renum" data-id="'+o.id+'" data-no="'+o.no+'">'+w('renum')+'</button><button type="button" class="fxb" data-fx="hatao" data-id="'+o.id+'" data-no="'+o.no+'">'+w('hatao')+'</button></span>';}
 rows($('lo'),st.opd,function(o){return '<div class="lr" data-sid="'+o.id+'"><span class="n">'+o.no+'</span><span class="t">'+esc(o.cid||'')+' '+esc(o.name||'')+(o.new?' <b>'+(EN?'new':'naya')+'</b>':'')+'</span><span class="m">'+esc(o.by)+' '+esc(o.at)+fx(o)+'</span></div>';},'lo_n');
 rows($('lx'),st.xp,function(o){return '<div class="lr" data-sid="'+o.id+'"><span class="n">'+o.no+'</span><span class="t">'+esc(o.cid||'')+' '+esc(o.name||'')+'<br><span class="sm">'+o.items.map(function(i){return esc(i.n+(i.side?' '+i.side:''))+(i.d?' (chhoot '+rs(i.d)+')':'');}).join(' · ')+'</span></span><span class="m">'+rs(o.total)+'<br>'+esc(o.by)+' '+esc(o.at)+fx(o)+'</span></div>';},'lx_n');
 /* S654 (D789): No. / Hatao on a saved parchi of the day shown -- a small form in the row, Theek sends it */
 document.querySelectorAll('.fxb').forEach(function(b){b.addEventListener('click',function(){var row=b.closest('.lr');if(!row||row.querySelector('.fxf'))return;
  var kind=b.getAttribute('data-fx'),id=b.getAttribute('data-id'),no=b.getAttribute('data-no');var f=document.createElement('div');f.className='fxf';
  f.innerHTML=(kind==='renum'?'<label>'+w('newno')+' <input class="fxno" inputmode="numeric" value="'+esc(no)+'" style="width:6em"></label> ':'')+'<label>'+w('fixwhy')+' <input class="fxwhy" maxlength="120" style="width:12em"></label> <button type="button" class="fxok">'+w('theek')+'</button> <button type="button" class="fxno2">'+w('rehne')+'</button>';
  row.appendChild(f);(f.querySelector('.fxno')||f.querySelector('.fxwhy')).focus();
  f.querySelector('.fxno2').addEventListener('click',function(){f.remove();});
  f.querySelector('.fxok').addEventListener('click',function(){var body={id:Number(id),day:day,why:f.querySelector('.fxwhy').value.trim()};if(kind==='renum')body.no=f.querySelector('.fxno').value.trim();
   f.querySelector('.fxok').disabled=true;api(kind==='renum'?'/finance/slips/desk/api/renumber':'/finance/slips/desk/api/void',body).then(function(r){msg(!!r.ok,r.ok?r.msg:r.err);if(r.state)draw(r.state);else f.querySelector('.fxok').disabled=false;});});
 });});
'''),
]

OTHER = {
    "parchi_desk.py": [('''.sm{font-size:15px;color:#3c464e}
</style></head><body>''',
                        '''.sm{font-size:15px;color:#3c464e}
.fx{display:block;margin-top:3px}.fxb{min-height:30px;border-radius:7px;border:1px solid var(--line);background:#fff;padding:2px 8px;font-size:13px;margin-left:4px;cursor:pointer}
.fxf{flex-basis:100%;background:var(--warnbg);border-radius:8px;padding:6px 8px;margin-top:6px;font-size:14px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.fxf input{min-height:36px;font-size:15px;padding:2px 6px;border:1px solid var(--line);border-radius:6px}.fxf button{min-height:36px;border-radius:7px;border:2px solid var(--warn);background:#fff;padding:2px 12px;font-weight:700}.lr{flex-wrap:wrap}
</style></head><body>''')],
}
VERSION_EDITS = {
    "slip_log.py": ("# -*- coding: utf-8 -*-\n", "# -*- coding: utf-8 -*-\n# S654_SLIP_TOOLS (session 354, 25-Oct-2026; D789): a saved parchi of the last 7 days can be renumbered or removed on the\n# desk; the previous book's numbers stay valid; a new book keeps the old range. renumber_slip / void_past_slip below.\n"),
    "parchi_desk.py": ("# -*- coding: utf-8 -*-\n", "# -*- coding: utf-8 -*-\n# S654_SLIP_TOOLS (session 354, 25-Oct-2026; D789): No. / Hatao on the day's rows -- api_renumber / api_void below.\n"),
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(txt, edits, name):
    for i, (old, new) in enumerate(edits, 1):
        n = txt.count(old)
        if n != 1:
            sys.exit("STOP: %s edit %d: the piece occurs %d times, not once -- nothing written" % (name, i, n))
        txt = txt.replace(old, new, 1)
    return txt


def main(src, out):
    os.makedirs(out, exist_ok=True)
    plan = {"slip_log.py": SL_EDITS, "parchi_desk.py": PD_EDITS}
    for name, edits in plan.items():
        raw = open(os.path.join(src, name), "rb").read()
        if md5(raw) != BASE[name]:
            sys.exit("STOP: %s is %s, not the pinned live %s -- nothing written" % (name, md5(raw)[:8], BASE[name][:8]))
        txt = raw.decode("utf-8")
        all_edits = edits + OTHER.get(name, []) + [VERSION_EDITS[name]]
        txt = apply(txt, all_edits, name)
        b = txt.encode("utf-8")
        open(os.path.join(out, name), "wb").write(b)
        print("%-15s %s -> %s  %d counted edit(s)" % (name, BASE[name][:8], md5(b), len(all_edits)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
