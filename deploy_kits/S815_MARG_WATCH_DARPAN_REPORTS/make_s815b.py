#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s815b.py LIVE_BW SEG OUT -- kit S815 (13-Nov-2026, Sanjeevni session 446): marg_billwatch.py a36d8265 (S814) -> Darpan's own Ask line
and the 'Reports asked for' strip with the cluster rule (D929) and the row button. Every patch is an exact anchor that occurs once; anything else
stops the build. The page's script is a plain Python string formatted with %: no '%' and no backslash-n inside the added JS."""
import hashlib, sys

FROM = "a36d82651b09996c4bc85139af2690e3"


def one(s, a, b):
    if s.count(a) != 1:
        raise SystemExit("anchor not found once (%d): %r" % (s.count(a), a[:80]))
    return s.replace(a, b)


WRAPS = '''
# ---- S815 wraps of three S814 functions (later definitions win at every call site) ----
_ask_withdraw_s814 = ask_withdraw


def ask_withdraw(con, known, still_open):                     # noqa: F811 -- S815: Darpan's question leaves his page the same way
    n = _ask_withdraw_s814(con, known, still_open)
    if not _ask_tables(con):
        return n
    m = 0
    for (aid,) in con.execute("SELECT id FROM marg_watch_ask WHERE answered_at IS NULL AND staff_ref=?", (DARPAN_CARD,)).fetchall():
        ks = [r[0] for r in con.execute("SELECT row_key FROM marg_watch_ask_row WHERE ask_id=?", (aid,))]
        if not ks or any(k not in known or k in still_open for k in ks):
            continue
        m += con.execute("UPDATE marg_watch_ask SET staff_ref=? WHERE id=? AND staff_ref=? AND answered_at IS NULL", (DARPAN_GONE, aid, DARPAN_CARD)).rowcount
    if m:
        con.commit()
    return n + m


_ask_state_s814 = ask_state


def ask_state(con):                                            # noqa: F811 -- S815: a withdrawn question is not shown as still asked
    S = _ask_state_s814(con)
    if not S or not _ask_tables(con):
        return S
    gone = {r[0] for r in con.execute("SELECT id FROM marg_watch_ask WHERE answered_at IS NULL AND staff_ref=?", (DARPAN_GONE,))}
    if _table(con, "amir_job"):
        for aid, ref in con.execute("SELECT id, staff_ref FROM marg_watch_ask WHERE answered_at IS NULL AND staff_ref LIKE 'amir_job:%'").fetchall():
            try:
                jid = int(str(ref).split(":", 1)[1])
            except (ValueError, IndexError):
                continue
            if con.execute("SELECT 1 FROM amir_job WHERE id=? AND done_how='withdrawn'", (jid,)).fetchone():
                gone.add(aid)
    return {k: v for k, v in S.items() if v["id"] not in gone}


'''

JS_ADD = (" var c=box.querySelector('.mwcard');c.style.display=(who==='amir'||who==='darpan')?'':'none';"
          "c.textContent=(who==='darpan')?'Put on Darpan’s page':'Put on Amir’s card';")

JS_FUNCS = ("function mwRAsk(b){mwPost('/api/report/ask',{row:parseInt(b.getAttribute('data-h'),10)},b.parentNode.querySelector('.msg'));}\n"
            "function mwRCluster(b){var row=b.parentNode;mwPost('/api/report/cluster',{n:row.querySelector('input').value},row.querySelector('.msg'));}\n")

ROUTES = '''
    @bp.route(PAGE + "/api/report/ask", methods=["POST"])          # S815: a sale report asked for again, from a section A row
    def api_report_ask():
        u, con, b, err = _post()
        if err:
            return err
        try:
            rid = int(b.get("row"))
        except (TypeError, ValueError):
            return jsonify(ok=False, message="Which row?"), 400
        ok, msg, code = rpt_ask_row(con, str(u.get("user") or "owner"), rid)
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/report/cluster", methods=["POST"])      # S815 (D929): his figure
    def api_report_cluster():
        u, con, b, err = _post()
        if err:
            return err
        ok, msg, code = rpt_set_cluster(con, str(u.get("user") or "owner"), b.get("n"))
        return jsonify(ok=ok, message=msg), code

    return bp


def init(app, db_getter, require_fn):'''


def main():
    src, seg, out = sys.argv[1:4]
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("the live file is not %s -- stopped" % FROM[:8])
    s = raw.decode("utf-8")
    s = one(s, "# ====================================================================== his acts",
            open(seg, encoding="utf-8").read() + WRAPS + "# ====================================================================== his acts")
    s = one(s, "    ask_ensure(con)                                           # S814\n",
            "    ask_ensure(con)                                           # S814\n    rpt_ensure(con)                                           # S815\n")
    s = one(s, 'ASK_ON_CARD = ("amir",)                     # whose own card takes the question in this kit',
            'ASK_ON_CARD = ("amir", "darpan")           # whose own page takes the question (S815: Darpan\'s Kal ka hisaab)')
    s = one(s, '    tail = "Apne card par jawab chuniye." if to_whom in ASK_ON_CARD else "Bataiye."',
            '    tail = {"amir": "Apne card par jawab chuniye.", "darpan": "Yahin jawab chuniye."}.get(to_whom, "Bataiye.")   # S815')
    s = one(s, ''' var tail=who==='amir'?'Apne card par jawab chuniye.':'Bataiye.';var t;''',
            ''' var tail=who==='amir'?'Apne card par jawab chuniye.':(who==='darpan'?'Yahin jawab chuniye.':'Bataiye.');var t;''')
    s = one(s, " var c=box.querySelector('.mwcard');c.style.display=who==='amir'?'':'none';", JS_ADD)
    s = one(s, "function mwAskNotice(b){", JS_FUNCS + "function mwAskNotice(b){")
    s = one(s, '("darpan", "<b>Darpan</b> — the counter and the shelf · text to copy or WhatsApp"),',
            '("darpan", "<b>Darpan</b> — on his own page, Kal ka hisaab (the counter and the shelf)"),')
    s = one(s, "— on his card, no answer yet.%s</p>", "— on his own page, no answer yet.%s</p>")
    s = one(s, '''        q = ",".join("?" * len(keys))
        if con.execute("SELECT 1 FROM marg_watch_ask a JOIN marg_watch_ask_row r ON r.ask_id = a.id WHERE a.staff_ref IS NOT NULL "
                       "AND a.answered_at IS NULL AND r.row_key IN (%s) LIMIT 1" % q, keys).fetchone():
            return False, "Already on Amir's card — no answer yet.", 409''',
            '''        if _ask_open_on_card(con, keys):                       # S815: only a question still standing on a staff page blocks
            return False, "Already asked on a staff page — no answer yet.", 409''')
    s = one(s, '''    if card and to_whom in ASK_ON_CARD:
        if not _table(con, "amir_job"):''', '''    if card and to_whom == "darpan":                           # S815: Darpan's own page reads the ask itself
        con.execute("UPDATE marg_watch_ask SET staff_ref=? WHERE id=?", (DARPAN_CARD, aid))
    elif card and to_whom in ASK_ON_CARD:
        if not _table(con, "amir_job"):''')
    s = one(s, '''    return True, ("On %s's card." % ASK_WHO[to_whom]) if (card and to_whom in ASK_ON_CARD) else "Noted on the row.", 200''',
            '''    return True, ("On %s." % {"amir": "Amir's card", "darpan": "Darpan's page"}[to_whom]) if (card and to_whom in ASK_ON_CARD) else "Noted on the row.", 200''')
    s = one(s, "    V = hand_view(con)\n    cnt, old = V[\"counted\"], [r for r in V[\"counted\"] if r[\"before\"]]\n",
            "    V = hand_view(con)\n    rpt_tick(con, V)                                          # S815: close what has come; the cluster rule (D929)\n"
            "    try:\n        RM = rpt_row_map(con)\n    except Exception:                                         # noqa: BLE001\n        RM = {}\n"
            "    for _k in (\"counted\", \"closed\"):\n        for _r in V[_k]:\n            _r[\"rpt\"] = RM.get(\"hand:%d\" % int(_r[\"id\"]))\n"
            "    cnt, old = V[\"counted\"], [r for r in V[\"counted\"] if r[\"before\"]]\n")
    s = one(s, "    h.append(ask_notice_html(con))                            # S814: the answer notice, OFF to begin with\n",
            "    h.append(ask_notice_html(con))                            # S814: the answer notice, OFF to begin with\n"
            "    h.append(rpt_html(con))                                   # S815: Reports asked for, and his cluster figure\n")
    s = one(s, '''ask_box_a(r, r.get("peers") or []))   # S814''',
            '''ask_box_a(r, r.get("peers") or []) + rpt_row_button(r))   # S814, S815''')
    s = one(s, '''        return ask_chip(r["ask"])                           # S814
    if act.get("action") == "close":
        return '<span class="st ans">Closed by you''', '''        return ask_chip(r["ask"])                           # S814
    if r.get("rpt") and act.get("action") not in ("close", "notok"):
        return '<span class="st late">Report asked</span>'   # S815
    if act.get("action") == "close":
        return '<span class="st ans">Closed by you''')
    s = one(s, "\n    return bp\n\n\ndef init(app, db_getter, require_fn):", ROUTES)
    b = s.encode("utf-8")
    open(out, "wb").write(b)
    print(hashlib.md5(b).hexdigest())


if __name__ == "__main__":
    main()
