#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""make_s854.py -- kit S854_LAB_NO_ID (the parent, S477, 17-Nov-2026; D979/D980, S450 study item 10): anchored patches on the
LIVE bytes of slip_log.py (231aebde) and check_screens.py (ac0e890a). Usage: python3 make_s854.py <from dir> <out dir>.
Every anchor must be found exactly once, else nothing is written."""
import hashlib
import os
import sys

FROM = {"slip_log.py": "231aebde", "check_screens.py": "ac0e890a"}

CANDS = '''

# ---------------------------------------------------------------- S854 (D979/D980; S450 item 10): suggested patients for a lab report
# with no clinic ID, best first, one tap each. Never automatic -- the automatic filing stays noid_match's (S391, proven: it agrees
# with this ranking on 23 of 25 past reports, the other two among its candidates). Where they come from: (1) a blood slip -- OPEN
# ones in S391's own window (LAB_WINDOW_DAYS), closed ones (report already in, or "test nahi hua") only 0-3 days before; (2) a
# clinic visit in the 7 days before; (3) the patient list, exactly the same name. Order: an open slip, then more words of the name
# shared, then the source, then the closer spelling, then the nearer day. "Sabse pakka" only for the ONLY open slip with the name.
# With a two-word name and any two-word hit, one-word hits are left out. Only numeric clinic IDs, never a merged one.
NOID_SLIP_DAYS = 3
NOID_VISIT_DAYS = 7
NOID_CAP = 6


def noid_name_index(con):
    \"\"\"{normalised name: [clinic IDs]} of the patient list (numeric IDs, not merged) -- built ONCE per page, not per report.\"\"\"
    idx = {}
    try:
        for cid, nm in con.execute("SELECT clinic_id, name FROM patient_ref WHERE COALESCE(clinic_id,'')<>'' "
                                   "AND (merged_into IS NULL OR merged_into='')").fetchall():
            k = _norm_name(nm)
            if k and re.fullmatch(r"\\d{1,8}", str(cid)):
                idx.setdefault(k, []).append(str(cid))
    except Exception:                                    # noqa: BLE001
        pass
    return idx


def _noid_shared(a, b):
    \"\"\"How many words of report name a are in name b (the same, or spelt nearly the same -- _name_hit's own test).\"\"\"
    import difflib
    tb = _name_tokens(b)
    return sum(1 for x in _name_tokens(a) if any(x == y or (min(len(x), len(y)) >= 4 and
                                                           difflib.SequenceMatcher(None, x, y).ratio() >= 0.8) for y in tb))


def noid_candidates(con, name, received_at, idx=None):
    \"\"\"[{cid, name, why, tier, open, shared, strong}] best first, at most NOID_CAP. Each row is read on its own: one bad date
    costs that row only. Never raises (the card then shows the ID box alone).\"\"\"
    import difflib
    try:
        d = (received_at or "")[:10]
        D0 = dt.date.fromisoformat(d)
    except ValueError:
        return []
    exact = _norm_name(name)
    words = _name_tokens(name)
    if not words:
        return []
    merged = set()
    try:
        merged = {str(r[0]) for r in con.execute("SELECT clinic_id FROM patient_ref WHERE merged_into IS NOT NULL AND merged_into<>''")}
    except Exception:                                    # noqa: BLE001
        pass
    best = {}
    tier_rank = {1: 0, 2: 1, 3: 1}                       # an exact whole-name match in the list ranks with the visitors

    def put(cid, nm, why, tier, open_slip, dist):
        cid = str(cid or "")
        if not re.fullmatch(r"\\d{1,8}", cid) or cid in merged:
            return
        sh = _noid_shared(name, nm)
        ratio = difflib.SequenceMatcher(None, _norm_name(nm), exact).ratio()
        key = (0 if open_slip else 1, -sh, tier_rank[tier], -ratio, dist)
        if cid not in best or key < best[cid][0]:
            best[cid] = (key, {"cid": cid, "name": nm or "", "why": why, "tier": tier, "open": open_slip, "shared": sh, "strong": False})
    lo = (D0 - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
    try:
        orders = con.execute("SELECT * FROM blood_order WHERE state='ok' AND day BETWEEN ? AND ? ORDER BY day, id", (lo, d)).fetchall()
    except Exception:                                    # noqa: BLE001
        orders = []
    n_open = set()
    for o in orders:
        try:
            o = dict(o)
            nm = _name_for(con, o["clinic_id"], o.get("name_seen") or "")
            if not _name_hit(name, nm):
                continue
            od = dt.date.fromisoformat(o["day"])
            rep = _report_for(con, o["clinic_id"], o["day"])
            is_open = rep is None and o.get("outcome") != "not_tested"
            if not is_open and (D0 - od).days > NOID_SLIP_DAYS:
                continue
            why = "blood parchi %s" % _dmy(o["day"])[:6]
            if o.get("outcome") == "not_tested":
                why += " · test nahi hua likha tha"
            elif rep is not None:
                why += " · iski report %s ko aa chuki" % _dmy((rep["received_at"] or "")[:10])[:6]
            if is_open:
                n_open.add(str(o["clinic_id"]))
            put(o["clinic_id"], nm, why, 1, is_open, (D0 - od).days)
        except Exception:                                # noqa: BLE001 -- this row only
            continue
    try:
        vrows = con.execute("SELECT clinic_id, MAX(visit_date) FROM patient_visit WHERE visit_date BETWEEN ? AND ? "
                            "AND COALESCE(clinic_id,'')<>'' GROUP BY clinic_id",
                            ((D0 - dt.timedelta(days=NOID_VISIT_DAYS)).isoformat(), d)).fetchall()
    except Exception:                                    # noqa: BLE001
        vrows = []
    for cid, vd in vrows:
        try:
            nm = _name_for(con, str(cid), "")
            if nm and _name_hit(name, nm):
                put(str(cid), nm, "clinic aaye %s" % _dmy(vd)[:6], 2, False, (D0 - dt.date.fromisoformat(str(vd)[:10])).days)
        except Exception:                                # noqa: BLE001
            continue
    if exact:
        for cid in (idx if idx is not None else noid_name_index(con)).get(exact, ()):
            try:
                put(cid, _name_for(con, cid, ""), "patient list mein isi naam se", 3, False, 0)
            except Exception:                            # noqa: BLE001
                continue
    out = [v for _k, v in sorted(best.values(), key=lambda kv: (kv[0], kv[1]["cid"]))]
    if len(words) >= 2 and any(x["shared"] >= 2 for x in out):
        out = [x for x in out if x["shared"] >= 2 or x["open"]]   # a two-word name: one-word hits only when nothing shares two --
        #                                                   never an OPEN slip (reception often writes the first name only)
    opens = [x for x in out if x["open"]]
    if len(opens) == 1 and len(n_open) == 1:
        opens[0]["strong"] = True                       # the ONLY open slip with the name -- "sabse pakka"
    elif len(n_open) > 1:
        for x in opens:
            x["why"] += " · isi naam ki %d parchi khuli — ID dekh kar chunein" % len(n_open)
    return out[:NOID_CAP]
'''

SL = [
    # 1 -- the ranked candidates, after noid_match
    ('''    return ""


def noid_resolve(con, msg_id, cid, how, who=""):''',
     '''    return ""
''' + CANDS + '''

def noid_resolve(con, msg_id, cid, how, who=""):'''),
    # 2 -- every unplaced report since the record began (not only the last 7 days: 4 older ones had dropped off every screen)
    ('''    """ID-less reports of the last week that nobody could place yet -- reception picks."""
    noid_ensure(con)
    since = (_now().date() - dt.timedelta(days=ORPHAN_DAYS)).isoformat()''',
     '''    """ID-less reports that nobody could place yet -- reception picks. S854: every one since the record began (EMR_FROM), not
    only the last week -- an older one had dropped off every screen and stayed unfiled."""
    noid_ensure(con)
    since = EMR_FROM'''),
    # 3 -- the card: the suggested patients, best first, one tap each
    ('''                oo = open_orders_for(con, r["received_at"])
                oo.sort(key=lambda o: (not same_name(r["name"], o["name"]) or not _name_tokens(o["name"]), o["day"], o["id"]))
                opts = "".join('<option value="%s">%s · %s · %s</option>' % (_esc(o["clinic_id"]), _esc(o["clinic_id"]),
                               _esc(o["name"] or "—"), _dmy(o["day"])[:6]) for o in oo)
                act = ('<form method="post" action="/finance/slips/pending/act" class="rb"><input type="hidden" name="key" value="nx:%s">'
                       '<select name="cid"><option value="">— kaun hai? —</option>%s</select>'
                       '<input name="cid2" inputmode="numeric" maxlength="12" placeholder="ya ID likhein">'
                       '<button name="act" value="noid_pick">Yahi hai</button>'
                       '<button name="act" value="noid_gone">Hamara nahi</button></form>' % (_esc(r["msg_id"]), opts))''',
     '''                cands = noid_candidates(con, r["name"], r["received_at"], idx)     # S854: best first, each with its reason
                opts = "".join('<button name="act" value="noid_pick:%s" class="cand"><b>%s</b> · %s<br><span class="sm">%s%s</span></button>' % (
                               _esc(c["cid"]), _esc(c["name"] or "—"), _esc(c["cid"]), _esc(c["why"]), " · sabse pakka" if (k == 0 and c["strong"]) else "")
                               for k, c in enumerate(cands))
                act = ('<form method="post" action="/finance/slips/pending/act" class="rb nxf"><input type="hidden" name="key" value="nx:%s">'
                       '<button name="act" value="noid_pick" hidden tabindex="-1" aria-hidden="true"></button>'   # Enter = the typed ID, never a suggestion
                       '%s%s'
                       '<input name="cid2" inputmode="numeric" maxlength="12" placeholder="ya ID likhein">'
                       '<button name="act" value="noid_pick">Yahi hai</button>'
                       '<button name="act" value="noid_gone">Hamara nahi</button></form>' % (
                           _esc(r["msg_id"]), ('<span class="sm">Shayad inmein se — sahi naam dabaiye:</span><br>' if cands else
                                               '<span class="sm">Naam se koi mareez nahi mila — ID likhein, ya "Hamara nahi".</span><br>'), opts))'''),
    # 4 -- a tap on a suggested patient
    ('''        if act == "noid_pick":
            cid = _clean_id(request.form.get("cid2")) or _clean_id(request.form.get("cid"))''',
     '''        if act.startswith("noid_pick:"):                # S854: one tap on a suggested patient
            request_cid = act.split(":", 1)[1]
            act = "noid_pick"
        else:
            request_cid = ""
        if act == "noid_pick":
            typed = _clean_id(request.form.get("cid2"))
            if request_cid:
                if not re.fullmatch(r"\\d{1,8}", request_cid) or not patient(con, request_cid):
                    return _pend_back("blood", err="Yeh mareez nahi mila — ID likhein.")
                if typed and typed != request_cid:
                    return _pend_back("blood", err="Do alag ID — ek hi chunein: naam dabaiye, ya ID likhkar 'Yahi hai'.")
            cid = _clean_id(request_cid) or typed or _clean_id(request.form.get("cid"))'''),
    ("""    if nxs:
        li = []
        for r in nxs:""", """    if nxs:
        li = []
        idx = noid_name_index(con) if can_tap else {}     # S854: the patient list read once for the whole card
        for r in nxs:"""),
    # 5 -- the card's own row wraps; a suggestion is a full-width button
    (""".rb{display:flex;gap:4px;flex:0 0 auto}""", """.rb{display:flex;gap:4px;flex:0 0 auto}.rb.nxf{flex-wrap:wrap;flex:1 1 100%%}.rb.nxf .cand{flex:1 1 100%%;text-align:left;min-height:44px}"""),
]

FILED_LAB = '''

def lab_filed_items(con):
    """S854: lab reports the lab mailed with no clinic ID that were filed by themselves (lab_noid 'auto', S391) -- or moved by a
    doctor here -- since FILED_SINCE, each with its filed report (record_file, source_ref = the mail's id + '#...')."""
    out = []
    try:
        rows = R._rows(con, "SELECT msg_id, name, received_at, clinic_id, how, at, by_user FROM lab_noid WHERE how IN ('auto','move','pick') "
                            "AND clinic_id<>'' AND received_at>=? ORDER BY received_at DESC", (FILED_SINCE,))
    except Exception:                                    # noqa: BLE001 -- no lab_noid table yet: nothing to show
        return out
    for r in rows:
        f = R._rows(con, "SELECT MIN(id) fid FROM record_file WHERE kind='blood' AND state='ok' AND drive_id<>'' AND clinic_id=? "
                         "AND substr(source_ref,1,length(?)+1)=? || '#'", (r["clinic_id"], r["msg_id"], r["msg_id"]))
        fid = f[0]["fid"] if f else None
        if not fid:
            continue                                     # not filed yet (the mailbox files it on its next run)
        day = str(r["received_at"])[:10]
        how = ("moved here by a doctor" if r["how"] == "move" else
               ("picked at reception by %s" % (r["by_user"] or "staff")) if r["how"] == "pick" else
               "filed by itself — the name on the lab's mail matched one open blood slip")
        out.append({"key": "lm:%s" % r["msg_id"], "kind": "filed", "lab": True, "cid": r["clinic_id"], "day": day, "dshort": _short(day),
                    "month": _month(day), "fid": fid, "name": _name_of(con, r["clinic_id"]) or "—", "orig": r["name"] or "",
                    "detail": "Lab report (no ID on the lab's mail) · " + how})
    return out
'''

CS = [
    ('''        out.append({"key": "mv:%d" % r["fid"], "kind": "filed", "cid": r["cid"], "day": day, "dshort": _short(day), "month": _month(day),
                    "fid": r["fid"], "name": _name_of(con, r["cid"]) or "—", "orig": r["orig_name"] or "", "detail": detail})
    return out
''',
     '''        out.append({"key": "mv:%d" % r["fid"], "kind": "filed", "cid": r["cid"], "day": day, "dshort": _short(day), "month": _month(day),
                    "fid": r["fid"], "name": _name_of(con, r["cid"]) or "—", "orig": r["orig_name"] or "", "detail": detail})
    out += lab_filed_items(con)                          # S854: the lab reports that filed themselves, with Move
    out.sort(key=lambda i: i["day"], reverse=True)
    return out
''' + FILED_LAB),
    ('''    if key.startswith(("nx:", "mv:")) and not _doctor(u):''',
     '''    if key.startswith("lm:"):                            # S854: a lab report (no ID on the lab's mail) filed by itself -- Move
        if not _doctor(u):
            return 403, {"ok": False, "err": W("Yeh Doctor sahab ka hai.", "For the doctors only.")}
        it = next((i for i in lab_filed_items(con) if i["key"] == key), None)
        if not it:
            return 409, {"ok": False, "err": "That report is no longer listed."}
        if not _id_ok(con, nid) or nid == it["cid"]:
            return 400, {"ok": False, "err": "Type the right clinic ID (a known ID, not the same one)."}
        name = _name_of(con, nid)
        if body.get("check"):
            return 200, {"ok": True, "check": True, "id": nid, "name": name or "—"}
        msg = key[3:]
        note = "moved from %s to %s by %s at %s (lab report, no ID on the lab's mail)" % (it["cid"], nid, R._who(u), R._stamp())
        n = con.execute("UPDATE record_file SET clinic_id=?, note=CASE WHEN note='' THEN ? ELSE note || ' | ' || ? END "
                        "WHERE kind='blood' AND state='ok' AND clinic_id=? AND substr(source_ref,1,length(?)+1)=? || '#'",
                        (nid, note, note, it["cid"], msg, msg)).rowcount
        con.execute("UPDATE lab_report SET clinic_id=? WHERE msg_id=?", (nid, msg))
        con.execute("UPDATE lab_noid SET clinic_id=?, how='move', by_user=?, at=? WHERE msg_id=?", (nid, R._who(u), R._stamp(), msg))
        _write(con, key, "lab_move", nid, "moved", "%s -> %s (%d file%s)" % (it["cid"], nid, n, "" if n == 1 else "s"), u)
        con.commit()
        return 200, {"ok": True, "msg": "Moved to %s (%s). The record moves; the Drive copy keeps its first name." % (name or "—", nid)}
    if key.startswith(("nx:", "mv:")) and not _doctor(u):'''),
    # the owner's filed tab: a lab report shows in a frame, and the words say report
    ('''if(TAB==='filed')acts='<button class="b2" data-o="1">'+(on?'Close':'See photo')+'</button><button class="b2" data-o="1">Wrong patient? Move</button>';''',
     '''if(TAB==='filed')acts='<button class="b2" data-o="1">'+(on?'Close':(i.lab?'See report':'See photo'))+'</button><button class="b2" data-o="1">Wrong patient? Move</button>';'''),
    (''' else{h+='<div class="pv"><a href="'+photo(i)+'" target="_blank" rel="noopener"><img src="'+photo(i)+'" alt="X-ray photo"></a></div>';''',
     ''' else{h+=(i.lab?'<iframe class="rp" src="/finance/records/file/'+i.fid+'" title="Lab report"></iframe>':'<div class="pv"><a href="'+photo(i)+'" target="_blank" rel="noopener"><img src="'+photo(i)+'" alt="X-ray photo"></a></div>');'''),
    ('''(CF?'<div class="cf"><b>Move this photo to '+esc(CF.name)''', '''(CF?'<div class="cf"><b>Move this '+(i.lab?'report':'photo')+' to '+esc(CF.name)'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch(src, pairs, name):
    for old, new in pairs:
        n = src.count(old)
        if n != 1:
            raise SystemExit("ANCHOR %s found %d times in %s: %r" % ("NOT" if n == 0 else "MANY", n, name, old[:90]))
        src = src.replace(old, new)
    return src


def main():
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    out = {}
    for name, pairs in (("slip_log.py", SL), ("check_screens.py", CS)):
        b = open(os.path.join(src_dir, name), "rb").read()
        if md5(b)[:8] != FROM[name]:
            raise SystemExit("FROM %s is %s, not %s -- the live file moved; nothing written" % (name, md5(b)[:8], FROM[name]))
        out[name] = patch(b.decode("utf-8"), pairs, name).encode("utf-8")
    os.makedirs(out_dir, exist_ok=True)
    for name, b in out.items():
        with open(os.path.join(out_dir, name), "wb") as fh:
            fh.write(b)
        print("%s %s -> %s" % (name, FROM[name], md5(b)[:8]))


if __name__ == "__main__":
    main()
