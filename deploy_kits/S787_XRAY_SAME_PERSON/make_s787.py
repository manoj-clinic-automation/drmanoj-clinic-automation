#!/usr/bin/python3
# make_s787.py -- kit S787_XRAY_SAME_PERSON (S428, 11-Nov-2026, the parent; the owner 08:38 IST: "R. is entered multiple times ...
# S.A. ... not registered in Docterz, so there is no flow for him also. Do the needful.")
# Usage: make_s787.py <live check_screens.py> <live records.py> <live DUTY_MAP.json> <out dir>
# Exact replacements on the live bytes (check_screens.py c259e6a2 and records.py 794cb87f -- S782; DUTY_MAP.json v22 616e0839).
import hashlib, json, os, sys
cs_p, rec_p, dm_p, out = sys.argv[1:5]
def load(p, want):
    b = open(p, "rb").read()
    assert hashlib.md5(b).hexdigest().startswith(want), "not the live %s (%s)" % (os.path.basename(p), want)
    return b.decode("utf-8")
def rp(t, a, b):
    assert t.count(a) == 1, "anchor not once: " + a[:80]
    return t.replace(a, b)

C = load(cs_p, "c259e6a2")
C = rp(C, 'VERSION = "S782 1"', 'VERSION = "S787 1"')
# ---- _parked: the answers that close a picture, and the 'not in Docterz' ones kept for his page
C = rp(C, '''def _parked(con, recent=False):
    """The open parked pictures (xray_filing state 'check', nobody's answer yet), newest first. recent=True: only those first seen
    in the last STAFF_DAYS days (the reception's list -- S782)."""''', '''DONE_ANS = ("not_xray", "id_fixed", "no_docterz")      # S787: + 'no_docterz' -- the patient is not registered in Docterz


def _parked(con, recent=False, nodz=False):
    """The open parked pictures (xray_filing state 'check', nobody's answer yet), newest first. recent=True: only those first seen
    in the last STAFF_DAYS days (the reception's list -- S782). nodz=True (S787): ALSO those marked 'not in Docterz' -- they wait
    on his page until an ID exists, and can still be given one."""''')
C = rp(C, '''        if a and a["answer"] in ("not_xray", "id_fixed"):
            continue''', '''        if a and a["answer"] in DONE_ANS and not (nodz and a["answer"] == "no_docterz"):
            continue''')
# ---- the same person's photos as one card; the photo of a patient filed that day
C = rp(C, '''def _reason(con, row, people):''', '''def _alike_rows(a, b):
    """S787: two parked pictures of the same person -- the names alike but for the usual spelling (records._s782_alike, either
    way; a child's 'BABY OF ...' never) and their days at most a week apart."""
    sa, sb = R.xray_stem(a["orig_name"] or ""), R.xray_stem(b["orig_name"] or "")
    ta, tb = R._s752_tokens(sa), R._s752_tokens(sb)
    if not ta or not tb or R._s752_child(sa) or R._s752_child(sb) or not (_ok_day(a["day"]) and _ok_day(b["day"])):
        return False
    if abs((dt.date.fromisoformat(a["day"]) - dt.date.fromisoformat(b["day"])).days) > 7:
        return False
    return R._s782_alike(ta, tb) or R._s782_alike(tb, ta)


def _groups(rows):
    """S787 (the owner 08:38 IST 11-Nov: the same patient's photos entered several times): the parked pictures in groups of one
    person each, in the order given (newest first); the first of a group is the one shown, the answer goes to all of them."""
    out = []
    for r in rows:
        g = next((g for g in out if _alike_rows(g[0], r)), None)
        if g is None:
            out.append([r])
        else:
            g.append(r)
    return out


def group_of(con, sid, nodz=False):
    """The group (list of rows) the picture sid is in, or []."""
    for g in _groups(_parked(con, nodz=nodz)):
        if any(r["src_id"] == sid for r in g):
            return g
    return []


S787_BY = {"user": "system · S787: another photo of this patient was filed that day"}


def s787_auto(con):
    """S787 (the owner 08:38 IST 11-Nov): a parked picture whose name is -- but for the usual spelling -- the name of the patient
    whose X-ray photo was FILED on the picture's day (the film's printed date when it was read, else its own day; +-1 day) is that
    patient's other photo (a second view, or the same film added again): it is given his ID as a person's answer is, and the next
    filing run files it. Only when exactly ONE such patient, nobody else who came those days has a name like it, the name carries
    no second number, and the film or the name prints no ID of another real patient. Called by records' /api/xray-plan before
    each plan. Returns how many were given."""
    _rec()
    R.ensure(con)
    cache, n = {}, 0
    for r in _parked(con):
        stem = R.xray_stem(r["orig_name"] or "")
        toks = R._s752_tokens(stem)
        if not toks or R._s752_child(stem):
            continue
        own, how = R.xray_id(r["orig_name"] or "")
        if how == "many":
            continue
        fr = R._s772_film(con, r["src_id"])
        day = fr[0][0] if fr and fr[0] else r["day"]
        if not _ok_day(day):
            continue
        d0, d1 = _d(day, -1), _d(day, 1)

        def alike(names):
            return any(R._s782_alike(toks, R._s752_tokens(nm)) for nm in names or [])
        filed = [x["clinic_id"] for x in R._rows(con, "SELECT DISTINCT clinic_id FROM record_file WHERE kind='xray' AND state='ok' "
                                                     "AND clinic_id<>'' AND day>=? AND day<=? ORDER BY clinic_id", (d0, d1))]
        hits = [c for c in filed if alike(R._s782_names(con, c, cache))]
        if len(hits) != 1:
            continue
        cid = hits[0]
        if any(c != cid and alike(p["names"]) for c, p in _people(con, d0, d1, cache).items()):
            continue                                     # someone else who came those days could be the picture's: a person decides
        ids = set(fr[1]) if fr else set()
        if how == "one" and own:
            ids.add(own)
        if any(x != cid and R._known_id(con, x) for x in ids):
            continue
        _write(con, "xf:" + r["src_id"], "xray_file", r["clinic_id"] or "", "id_fixed", cid, S787_BY)
        n += 1
    if n:
        con.commit()
    return n


def _reason(con, row, people):''')
C = rp(C, '''def xray_queue(con, with_people=False, recent=False):
    cache = {}
    out = []
    for r in _parked(con, recent):
        people = _people(con, _d(r["day"], -1), _d(r["day"], 1), cache)
        hi, en = _reason(con, r, people)
        it = {"key": "xf:" + r["src_id"], "kind": "xray", "sid": r["src_id"], "day": r["day"], "dshort": _short(r["day"]),
              "month": _month(r["day"]), "time": str(r["file_time"] or "")[11:16], "title": r["orig_name"] or "(no name)",
              "reason": hi, "reason_en": en}''', '''def xray_queue(con, with_people=False, recent=False, nodz_only=False):
    """S787: one item per person (the same person's photos together, 'N photos' in the title); nodz_only=True -- the ones marked
    'not in Docterz' (his page's tile)."""
    cache = {}
    out = []
    answers = R._answers(con) if nodz_only else {}
    rows = _parked(con, recent, nodz=nodz_only)
    if nodz_only:
        rows = [r for r in rows if (answers.get("xf:" + r["src_id"]) or {}).get("answer") == "no_docterz"]
    for g in _groups(rows):
        r = g[0]
        people = _people(con, _d(r["day"], -1), _d(r["day"], 1), cache)
        hi, en = _reason(con, r, people)
        if nodz_only:
            a = answers.get("xf:" + r["src_id"]) or {}
            hi = en = "Not in Docterz \\u2014 marked by %s on %s" % (a.get("answered_by") or "?", _short(str(a.get("answered_at") or "")[:10]))
        it = {"key": "xf:" + r["src_id"], "kind": "xray", "sid": r["src_id"], "day": r["day"], "dshort": _short(r["day"]),
              "month": _month(r["day"]), "time": str(r["file_time"] or "")[11:16],
              "title": (r["orig_name"] or "(no name)") + (SEP + "%d photos" % len(g) if len(g) > 1 else ""),
              "n": len(g), "copies": [x["src_id"] for x in g[1:]], "reason": hi, "reason_en": en}''')
# ---- the answers: the whole group; 'not in Docterz'
C = rp(C, '''        row = next((r for r in _parked(con) if r["src_id"] == sid), None)
        if not row:
            return 409, {"ok": False, "err": done}
        if a == "id_fixed":''', '''        g = group_of(con, sid, nodz=(a == "id_fixed"))    # S787: the same person's other photos go with it
        row = next((r for r in g if r["src_id"] == sid), None)
        if not row:
            return 409, {"ok": False, "err": done}
        many = W(" · %d photo" % len(g), " · %d photos" % len(g)) if len(g) > 1 else ""
        if a == "no_docterz":
            for x in g:
                _write(con, "xf:" + x["src_id"], "xray_file", x["clinic_id"] or "", "no_docterz", "", u)
            con.commit()
            return 200, {"ok": True, "msg": W("Theek hai: Docterz mein nahi \\u2014 Doctor sahab ki list mein gayi", "Moved to 'Not in Docterz'") + many}
        if a == "id_fixed":''')
C = rp(C, '''            _write(con, key, "xray_file", row["clinic_id"] or "", "id_fixed", nid, u)
            con.commit()''', '''            for x in g:                                  # S787: every photo of the group
                _write(con, "xf:" + x["src_id"], "xray_file", x["clinic_id"] or "", "id_fixed", nid, u)
            con.commit()''')
C = rp(C, '''            if nox:
                msg += W(" · Doctor sahab ko dikhega: X-ray hua, parchi nahi", " · it will show under 'X-ray taken, no X-ray slip'")
            return 200, {"ok": True, "msg": msg}''', '''            if nox:
                msg += W(" · Doctor sahab ko dikhega: X-ray hua, parchi nahi", " · it will show under 'X-ray taken, no X-ray slip'")
            return 200, {"ok": True, "msg": msg + many}''')
C = rp(C, '''    row = next((r for r in _parked(con) if r["src_id"] == sid), None)
    if not row:
        return jsonify(ok=False, err="gone"), 404''', '''    row = next((r for r in _parked(con, nodz=True) if r["src_id"] == sid), None)
    if not row:
        return jsonify(ok=False, err="gone"), 404''')
C = rp(C, '''    row = next((r for r in _parked(con) if r["src_id"] == sid), None)
    if not row:
        return Response("This picture is no longer waiting."''', '''    row = next((r for r in _parked(con, nodz=True) if r["src_id"] == sid), None)
    if not row:
        return Response("This picture is no longer waiting."''')
C = rp(C, '''    x = len(_parked(con, recent=not lab))''', '''    x = len(_groups(_parked(con, recent=not lab)))     # S787: one per person''')
C = rp(C, '''"wait": len(_parked(con)),''', '''"wait": len(_groups(_parked(con))),''')
C = rp(C, '''    data = {"filed": filed_items(con), "wait": xray_queue(con), "nox": nox_items(con), "lab": lab_items(con),''',
          '''    data = {"filed": filed_items(con), "wait": xray_queue(con), "nox": nox_items(con), "lab": lab_items(con),
            "nodz": xray_queue(con, nodz_only=True),                                     # S787''')
C = rp(C, '''tab if tab in ("filed", "wait", "nox", "lab") else "wait"''', '''tab if tab in ("filed", "wait", "nox", "lab", "nodz") else "wait"''')
# ---- the staff page: one more button
C = rp(C, '''<button class="b3" id="notx">Yeh X-ray nahi hai</button>''',
          '''<button class="b3" id="notx">Yeh X-ray nahi hai</button><button class="b3" id="nodz">Docterz mein nahi</button>''')
C = rp(C, '''var nx=$('notx');if(nx)nx.onclick=function(){post({key:it.key,a:'not_xray'}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;msgs();}});};''',
          '''var nx=$('notx');if(nx)nx.onclick=function(){post({key:it.key,a:'not_xray'}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;msgs();}});};
 var nd=$('nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:it.key,a:'no_docterz'}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;nd.disabled=false;msgs();}});};''')
# ---- his page: the fifth tile 'Not in Docterz'
C = rp(C, '''.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}''',
          '''.tiles{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px}''')
C = rp(C, '''['lab','Lab report came, no blood slip','also on Shavez’s list','#1D4ED8']];''',
          '''['lab','Lab report came, no blood slip','also on Shavez’s list','#1D4ED8'],['nodz','Not in Docterz','X-rayed, not registered · file once an ID exists','#7C3AED']];''')
C = rp(C, '''lab:['Lab report came, no blood slip','matched by the report’s clinic ID against the slips and Docterz · Shavez answers these too — whoever answers first closes it for both']};''',
          '''lab:['Lab report came, no blood slip','matched by the report’s clinic ID against the slips and Docterz · Shavez answers these too — whoever answers first closes it for both'],
 nodz:['Not in Docterz','patients X-rayed but not registered in Docterz · once they are, find them by name or mobile here and file the photo']};''')
C = rp(C, '''function title(i){if(TAB==='wait')return i.title;''', '''function title(i){if(TAB==='wait'||TAB==='nodz')return i.title;''')
C = rp(C, '''function detail(i){if(TAB==='wait')return i.reason_en;''', '''function detail(i){if(TAB==='wait'||TAB==='nodz')return i.reason_en;''')
C = rp(C, '''function photo(i){return TAB==='wait'?''', '''function photo(i){return (TAB==='wait'||TAB==='nodz')?''')
C = rp(C, '''<div class="acts"><button class="b2" id="notx">Not an X-ray</button></div>';''',
          '''<div class="acts"><button class="b2" id="notx">Not an X-ray</button>'+(TAB==='wait'?'<button class="b2" id="nodz">Not in Docterz (not registered)</button>':'')+'</div>';''')
C = rp(C, '''  if(TAB==='wait')h+=picker(i);''', '''  if(TAB==='wait'||TAB==='nodz')h+=picker(i);''')
C = rp(C, '''  if(TAB==='wait')acts='<button class="'+(on?'b2':'b1')+'" data-o="1">'+(on?'Close':'See &amp; file')+'</button>';''',
          '''  if(TAB==='wait'||TAB==='nodz')acts='<button class="'+(on?'b2':'b1')+'" data-o="1">'+(on?'Close':'See &amp; file')+'</button>';''')
C = rp(C, '''if(OPEN&&TAB==='wait'&&!PATS[i.sid])''', '''if(OPEN&&(TAB==='wait'||TAB==='nodz')&&!PATS[i.sid])''')
C = rp(C, '''  var nx=el.querySelector('#notx');if(nx)nx.onclick=function(){post({key:key,a:'not_xray'}).then(function(r){if(r.ok)drop(key,r.msg);else{ERR=r.err;draw();}});};''',
          '''  var nx=el.querySelector('#notx');if(nx)nx.onclick=function(){post({key:key,a:'not_xray'}).then(function(r){if(r.ok)drop(key,r.msg);else{ERR=r.err;draw();}});};
  var nd=el.querySelector('#nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:key,a:'no_docterz'}).then(function(r){if(r.ok){B.nodz.unshift(i);drop(key,r.msg);}else{ERR=r.err;nd.disabled=false;draw();}});};''')

Rr = load(rec_p, "794cb87f")
Rr = rp(Rr, '''    con = _db()
    items, notes = xray_actions(con)''', '''    con = _db()
    try:                                                 # S787: another photo of a patient filed that day gets his ID first
        if _s757 is not None:
            _s757.s787_auto(con)
    except Exception:                                    # noqa: BLE001 -- the plan stands without it
        pass
    items, notes = xray_actions(con)''')
Rr = rp(Rr, '''        if a and a["answer"] in ("not_xray", "id_fixed"):
            continue
        out.append({"key": key, "kind": "xray_file",''', '''        if a and a["answer"] in ("not_xray", "id_fixed", "no_docterz"):   # S787: + not in Docterz (his page)
            continue
        out.append({"key": key, "kind": "xray_file",''')
Rr = rp(Rr, '''"id_fixed": "ID corrected", "not_xray": "not an X-ray", "not_done": "X-ray not done"}''',
            '''"id_fixed": "ID corrected", "not_xray": "not an X-ray", "not_done": "X-ray not done",
          "no_docterz": "not in Docterz"}                                                        # S787''')

D = load(dm_p, "616e0839")
D = rp(D, "c.answer IN ('not_xray','id_fixed'))", "c.answer IN ('not_xray','id_fixed','no_docterz'))")
D = rp(D, '"version": 22,', '"version": 23,')
D = rp(D, '"kit": "S782_XRAY_LEFTOVERS",', '"kit": "S787_XRAY_SAME_PERSON",')
json.loads(D)

os.makedirs(out, exist_ok=True)
for rel, t in (("check_screens.py", C), ("records.py", Rr), ("DUTY_MAP.json.s787", D)):
    open(os.path.join(out, rel), "wb").write(t.encode("utf-8"))
    print("written", rel, hashlib.md5(t.encode("utf-8")).hexdigest()[:8])
