# ====================================================================== S812 -- section A: stock moved in Marg with no record (D914, D923, D943)
HAND_KIT = "S812_MARG_WATCH_STOCK"
HAND_DECISIONS = {"ok": "OK — Marg is right as it is", "notok": "Not OK", "lot": "OK — with the lot"}
SPINE_STATE = os.path.join(HERE, "spine", "spine_state.json")
SPINE_LATE_H = 26        # F-1329's owed part: the stock record not rebuilt for longer than a working day is said at the top of section A


def _H():
    import marg_hand_change                                   # noqa: PLC0415 -- the engine; this page only reads its table
    return marg_hand_change


def hand_acts(con):
    """{row id: his newest act} from billwatch_act (fkey 'hand:<id>')."""
    out = {}
    if not _table(con, "billwatch_act"):
        return out
    for fk, action, decision, reason, by, at in con.execute("SELECT fkey, action, decision, reason, by_user, at FROM billwatch_act "
                                                            "WHERE fkey LIKE 'hand:%' ORDER BY id"):
        try:
            out[int(fk[5:])] = dict(action=action, decision=decision, reason=reason, by=by, at=at)
        except ValueError:
            continue
    return out


def hand_view(con):
    """Section A's rows, sorted into what the page shows. Reads only."""
    H = _H()
    rows = H.rows_for_page(con, all_rows=True)
    A = hand_acts(con)
    since = setting(con, "hand.s812_since", "")
    floor_p = H.floor_p(con)
    out = dict(counted=[], closed=[], explained=[], renamed=[], cleared=[], since=since, floor_p=floor_p)
    cut = (now_ist().date() - dt.timedelta(days=30)).isoformat()
    for r in rows:
        r["act"] = A.get(r["id"])
        r["before"] = (not since) or bool(r.get("hist")) or str(r.get("found_at") or "") < since
        r["below"] = bool(floor_p) and r.get("value_p") is not None and abs(int(r["value_p"])) < floor_p
        if r.get("rec_kind"):
            out["explained"].append(r)
        elif r["kind"] == "rename":
            if r["status"] == "open":
                out["renamed"].append(r)
        elif r["status"] != "open":
            if str(r.get("status_at") or "")[:10] >= cut:
                out["cleared"].append(r)
        elif (r["act"] or {}).get("action") == "close":
            out["closed"].append(r)
        else:
            out["counted"].append(r)
    return out


def _spine_line(con):
    """The stock record's own health, at the top of section A -- red when it has not been rebuilt for over a working day (F-1329)."""
    try:
        with open(SPINE_STATE, encoding="utf-8") as fh:
            st = json.load(fh)
    except (OSError, ValueError):
        return '<p class="note">The stock record\'s health file could not be read just now.</p>'
    ok_at = str(st.get("last_success_iso") or "")
    try:
        age = (dt.datetime.now(IST) - dt.datetime.fromisoformat(ok_at)).total_seconds() / 3600.0
    except ValueError:
        age = None
    when = "%s %s" % (dmon(ok_at[:10]), ok_at[11:16]) if ok_at else "never"
    if st.get("passed") is False and (age is None or age > SPINE_LATE_H):
        why = "; ".join(str(x) for x in (st.get("failed") or []))[:200]
        return ('<p class="bad" style="margin:0 0 10px"><b>The stock record has not been rebuilt since %s</b> — its own check fails%s. '
                'The moves below stop at that day; nothing newer is judged until it builds again.</p>' % (esc(when), (": " + esc(why)) if why else ""))
    return '<p class="note" style="margin:0 0 10px">Read from the stock record built %s.</p>' % esc(when)


def _rr(p):
    """Paise -> whole rupees (a stock move's value is an estimate; its paise are noise)."""
    return int(round(int(p) / 100.0)) * 100


def _hand_money(rows):
    up = _rr(sum(int(r["value_p"]) for r in rows if r.get("value_p") and int(r["value_p"]) > 0))
    dn = _rr(sum(int(r["value_p"]) for r in rows if r.get("value_p") and int(r["value_p"]) < 0))
    norate = sum(1 for r in rows if r.get("value_p") is None)
    return up, dn, norate


def _hand_status(r):
    act = r.get("act") or {}
    if act.get("action") == "close":
        return '<span class="st ans">Closed by you — %s</span>' % esc(HAND_DECISIONS.get(act.get("decision"), "OK"))
    if act.get("action") == "notok":
        return '<span class="st late">Marked Not OK by you</span>'
    if act.get("action") == "reopen":
        return '<span class="st">Open — reopened by you</span>'
    if r.get("below"):
        return '<span class="st">Open · below your floor (not told)</span>'
    return '<span class="st late">No record behind it</span>'


def _hand_decide(r):
    rid = int(r["id"])
    act = r.get("act") or {}
    if act.get("action") == "close":
        line = "Closed by you — %s%s · %s." % (HAND_DECISIONS.get(act.get("decision"), "OK"), (": " + act["reason"]) if act.get("reason") else "",
                                              dmon(str(act.get("at"))[:10]))
        return ('<div class="closep"><div class="askrow"><span>%s</span><button type="button" data-h="%d" onclick="mwHReopen(this)">Reopen</button>'
                '<span class="msg"></span></div></div>' % (esc(line), rid))
    was = ""
    if act.get("action") == "notok":
        was = "<p class='note' style='margin:0 0 6px'>Marked Not OK by you on %s%s.</p>" % (esc(dmon(str(act.get("at"))[:10])),
                                                                                         esc((": " + act["reason"]) if act.get("reason") else ""))
    h = ['<div class="closep">%s<b>Your decision</b>' % was]
    for v, words in (("ok", "<b>OK</b> — Marg is right as it is (the shelf agrees, or I made this change)"),
                     ("notok", "<b>Not OK</b> — to be put right; the row stays open, marked")):
        h.append('<label><input type="radio" name="h%d" value="%s"> %s</label>' % (rid, v, words))
    h.append('<div class="askrow" style="margin:8px 0 0"><input type="text" maxlength="300" placeholder="Reason (optional)" aria-label="Reason (optional)">'
             '<button type="button" class="pri" data-h="%d" onclick="mwHClose(this)">Save my decision</button><span class="msg"></span></div></div>' % rid)
    return "".join(h)


def _hand_table(rows, H, decide=True):
    head = ('<table class="btab"><colgroup><col style="width:15%"><col style="width:27%"><col style="width:13%"><col style="width:9%">'
            '<col style="width:11%"><col style="width:16%"><col style="width:9%"></colgroup><tbody><tr class="hd"><th>Between</th><th>Item</th>'
            '<th>Marg</th><th class="n">Moved</th><th class="n">₹</th><th>Status</th><th></th></tr>')
    h = [head]
    per = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: (r["day_to"], r["day_from"], r["item"]), reverse=True):
        per.setdefault((r["day_from"], r["day_to"]), []).append(r)
    for (a, b), rs_ in per.items():
        up, dn, nr = _hand_money(rs_)
        tot = " · ".join(x for x in ((rs(up, sign=True) if up else ""), (rs(dn, sign=True) if dn else ""), ("%d with no rate" % nr) if nr else "") if x)
        h.append('<tr class="hd"><th colspan="7" style="text-align:left">%s – %s · %d move%s%s</th></tr>'
                 % (esc(dmon(a)), esc(dmon(b)), len(rs_), "" if len(rs_) == 1 else "s", (" · " + esc(tot)) if tot else ""))
        for r in rs_:
            rid = int(r["id"])
            v = r.get("value_p")
            money = "no rate" if v is None else ('<span class="%s">%s</span>' % ("dn" if int(v) < 0 else "up", esc(rs(_rr(v), sign=True))))
            new = "" if r["before"] else '<span class="badge">NEW</span>'
            h.append('<tr><td class="was" data-k="Between">%s – %s</td><td><b>%s</b>%s</td><td class="m">%s → %s</td><td class="n">%s</td>'
                     '<td class="n" data-k="₹">%s</td><td>%s</td><td><button type="button" class="pri" data-f="h%d" aria-expanded="false" '
                     'aria-controls="dh%d" onclick="mwView(this)">View</button></td></tr>'
                     % (esc(dmon(r["day_from"])), esc(dmon(r["day_to"])), esc(r["item"]), new, esc(H.num(r["marg_from"])), esc(H.num(r["marg_to"])),
                        esc(H.snum(r["shift"])), money, _hand_status(r) if decide else esc(H.REC_WORDS.get(r.get("rec_kind"), r.get("status") or "")),
                        rid, rid))
            body = '<p style="margin:0 0 6px">%s</p>' % esc(H.why_of(r))
            if decide:
                body += '<p class="note" style="margin:0 0 8px">%s</p>%s' % (esc(H.remedy_of(r)), _hand_decide(r))
            h.append('<tr class="dt" id="dh%d" hidden><td colspan="7">%s</td></tr>' % (rid, body))
    h.append("</tbody></table>")
    return "".join(h)


def hand_html(con):
    """Section A on the Marg watch page. Never raises: a fault here says so in one line and leaves section B whole."""
    try:
        return _hand_html(con)
    except Exception as e:                                    # noqa: BLE001
        return ('<div class="card" id="stock"><h2>Stock moved in Marg with no record</h2><p class="bad">Not readable just now (%s).</p></div>'
                % esc(e.__class__.__name__))


def _hand_html(con):
    H = _H()
    V = hand_view(con)
    cnt, old = V["counted"], [r for r in V["counted"] if r["before"]]
    new = [r for r in cnt if not r["before"]]
    up, dn, nr = _hand_money(cnt)
    try:
        lr = json.loads(setting(con, "hand.last_run", "") or "{}")
    except ValueError:
        lr = {}
    h = ['<div class="card" id="stock"><h2>Stock moved in Marg with no record <small>%d open · %s added · %s gone%s</small></h2>'
         % (len(cnt), esc(rs(up, sign=True) if up else "₹0"), esc(rs(dn, sign=True) if dn else "₹0"),
            (" · %d with no rate" % nr) if nr else "")]
    h.append(_spine_line(con))
    if not lr:
        h.append('<p class="note">Section A has not run yet — it fills at the next rebuild of the stock record (every few minutes).</p>')
    h.append('<p class="lead">Marg\'s stock moved and nothing in the system stands behind it — no sale, bill or voucher. A move with any record behind '
             'it, even a wrong one, is under <b>Explained after all</b> at the foot of this section and is never counted.</p>')
    fr = V["floor_p"] // 100
    h.append('<div class="askrow" style="margin:0 0 12px"><label for="hfloor">Tell me only of moves worth at least ₹</label>'
             '<input id="hfloor" type="text" inputmode="numeric" maxlength="7" value="%d" style="width:90px" aria-label="Floor in rupees">'
             '<button type="button" onclick="mwHFloor(this)">Save</button><span class="msg"></span><span class="note">%s</span></div>'
             % (fr, "0 — every move is told (your ruling of 12-Nov)." if not fr else "Smaller moves stay listed here; they are not told."))
    if new:
        h.append('<h3 style="margin:6px 0">New <small>%d</small></h3>%s' % (len(new), _hand_table(new, H)))
    if old:
        h.append('<details class="fold"%s><summary>Before this section began — %d move%s (never told as new)</summary>'
                 % (" open" if not new else "", len(old), "" if len(old) == 1 else "s"))
        h.append('<div class="askrow" style="margin:8px 0 12px"><button type="button" class="pri" data-n="%d" onclick="mwHLot(this)">OK all %d — close them together'
                 '</button><span class="msg"></span></div>%s</details>' % (len(old), len(old), _hand_table(old, H)))
    if not cnt:
        h.append('<p class="lead" style="margin:0">Nothing is open — every move has a record behind it.</p>')
    if V["closed"]:
        h.append('<details class="fold"><summary>Closed by you (%d)</summary>%s</details>' % (len(V["closed"]), _hand_table(V["closed"], H)))
    ex = V["explained"]
    if ex:
        grp = collections.OrderedDict()
        for k in H.REC_WORDS:
            grp[k] = [r for r in ex if r.get("rec_kind") == k]
        parts = "".join('<h3 style="margin:10px 0 4px">%s <small>%d</small></h3>%s' % (esc(H.REC_WORDS[k]), len(v), _hand_table(v, H, decide=False))
                        for k, v in grp.items() if v)
        h.append('<details class="fold"><summary>Explained after all — %d move%s with a record behind them (not counted)</summary>%s</details>'
                 % (len(ex), "" if len(ex) == 1 else "s", parts))
    if V["renamed"]:
        h.append('<details class="fold"><summary>Renamed in Marg — no stock moved (%d)</summary>%s</details>'
                 % (len(V["renamed"]), _hand_table(V["renamed"], H, decide=False)))
    if V["cleared"]:
        h.append('<details class="fold"><summary>Cleared by itself or put right in Marg — last 30 days (%d)</summary>%s</details>'
                 % (len(V["cleared"]), _hand_table(V["cleared"], H, decide=False)))
    if lr:
        h.append('<p class="note" style="margin:10px 0 0">Last read %s · judged to %s · purchase lists taken to %s · %s bill change%s read for the records%s.</p>'
                 % (esc(str(lr.get("at") or "")[:16]), esc(dmon(lr.get("judged_to") or "")), esc(str(lr.get("last_pur_taken") or "—")),
                    esc(str(lr.get("bills") if lr.get("bills") is not None else "—")), "" if lr.get("bills") == 1 else "s",
                    (" (" + esc(lr.get("bills_why")) + ")") if lr.get("bills_why") else ""))
    h.append("</div>")
    return "".join(h)


def _hand_find(con, rid):
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return None
    return next((r for r in _H().rows_for_page(con, all_rows=True) if int(r["id"]) == rid), None)


def _hand_write(fn):
    def run(con, *a):
        try:
            ensure(con)
            return fn(con, *a)
        except sqlite3.Error as e:
            try:
                con.rollback()
            except sqlite3.Error:
                pass
            return False, "Not saved — the database was busy (%s). Try again." % str(e)[:60], 503
    return run


@_hand_write
def hand_close(con, who, rid, decision, reason):
    r = _hand_find(con, rid)
    if r is None or r.get("rec_kind") or r["kind"] != "hand":
        return False, "This move is no longer on the list — the page was out of date. Reload it.", 409
    if (hand_acts(con).get(int(r["id"])) or {}).get("action") == "close":
        return False, "This move is already closed. Reopen it first.", 409
    if decision not in ("ok", "notok"):
        return False, "Pick one of the choices.", 400
    reason = re.sub(r"\s+", " ", str(reason or "")).strip()[:300]
    action = "notok" if decision == "notok" else "close"
    con.execute("INSERT INTO billwatch_act (fkey, action, decision, reason, by_user, at) VALUES (?,?,?,?,?,?)",
                ("hand:%d" % int(r["id"]), action, decision, reason or None, who, now_iso()))
    _audit(con, who, "handwatch_" + action, "hand:%d" % int(r["id"]), dict(decision=decision, reason=reason or None, item=r["item"],
                                                                          day_from=r["day_from"], day_to=r["day_to"], shift=r["shift"]))
    con.commit()
    return True, "Saved.", 200


@_hand_write
def hand_reopen(con, who, rid):
    r = _hand_find(con, rid)
    if r is None:
        return False, "This move is no longer on the list — the page was out of date. Reload it.", 409
    a = hand_acts(con).get(int(r["id"])) or {}
    if a.get("action") not in ("close", "notok"):
        return False, "This move is open already.", 409
    con.execute("INSERT INTO billwatch_act (fkey, action, decision, reason, by_user, at) VALUES (?,?,?,?,?,?)",
                ("hand:%d" % int(r["id"]), "reopen", None, None, who, now_iso()))
    _audit(con, who, "handwatch_reopen", "hand:%d" % int(r["id"]), dict(item=r["item"], day_to=r["day_to"]))
    con.commit()
    return True, "Reopened.", 200


@_hand_write
def hand_ok_lot(con, who, n_shown):
    if not setting(con, "hand.s812_since", ""):
        return False, "Section A has not run yet — nothing to close together.", 409
    lot = [r for r in hand_view(con)["counted"] if r["before"]]
    try:
        n_shown = int(n_shown)
    except (TypeError, ValueError):
        n_shown = -1
    if not lot:
        return False, "Nothing is waiting from before this section began.", 409
    if n_shown != len(lot):
        return False, "The list changed while the page was open (%d now). Reload it and look again." % len(lot), 409
    ts = now_iso()
    for r in lot:
        con.execute("INSERT INTO billwatch_act (fkey, action, decision, reason, by_user, at) VALUES (?,?,?,?,?,?)",
                    ("hand:%d" % int(r["id"]), "close", "lot", None, who, ts))
    _audit(con, who, "handwatch_ok_lot", "", dict(n=len(lot), ids=[int(r["id"]) for r in lot]))
    con.commit()
    return True, "Closed %d." % len(lot), 200


@_hand_write
def hand_set_floor(con, who, rupees):
    """D943: his floor in rupees -- a whole number from 0 (none) to 1,00,000."""
    s = re.sub(r"[,\s₹]", "", str(rupees if rupees is not None else ""))
    if not re.match(r"^\d{1,6}$", s) or int(s) > 100000:
        return False, "A whole number of rupees, 0 to 100000.", 400
    _H().ensure(con)
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                ("hand.floor_rs", str(int(s)), next(n for k, _d, n in _H().SETTINGS if k == "hand.floor_rs")))
    _audit(con, who, "handwatch_floor", "", dict(rupees=int(s)))
    con.commit()
    return True, "Saved: ₹%d." % int(s), 200


