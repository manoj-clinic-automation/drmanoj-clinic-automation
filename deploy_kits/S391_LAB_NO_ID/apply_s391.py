#!/usr/bin/env python3
"""apply_s391.py -- kit S391_LAB_NO_ID. Makes the S391 slip_log.py from the live S384 bytes (30d799e1) by anchored
edits; every anchor must occur exactly once. Usage: python apply_s391.py <S384 slip_log.py> <out>"""
import hashlib, sys

src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest() == "30d799e1080db7c50aa95257a869998c", "the source is not S384 slip_log.py"
s = b.decode("utf-8")


def rep(old, new):
    global s
    n = s.count(old)
    assert n == 1, "anchor found %d times: %r" % (n, old[:80])
    s = s.replace(old, new)


# 1 -- the ID-less report: table, matching, sweep, list (inserted before pending_counts)
NOID = r'''# ---------------------------------------------------------------- S391: a lab report e-mailed with NO clinic ID
# The lab's subject is normally "Your Report  MRS. <name> ( 8118)". When the ID is left out, the mailbox runs could not
# tell whose report it was and skipped it -- the line stayed "mail bheja" for ever and the PDF was never filed.
# Now the mailbox asks here: the report is joined to the ONE open blood order with the same name (a mailed one wins a
# tie; a re-send follows the first), and anything still unsure is shown to reception to pick. Never guessed.
_noid_done = False


def noid_ensure(con):
    global _noid_done
    pend_ensure(con)
    if _noid_done:
        return
    con.executescript("""
CREATE TABLE IF NOT EXISTS lab_noid (
  msg_id      TEXT PRIMARY KEY,
  name        TEXT NOT NULL DEFAULT '',
  received_at TEXT NOT NULL,
  clinic_id   TEXT NOT NULL DEFAULT '',
  how         TEXT NOT NULL DEFAULT '',
  by_user     TEXT NOT NULL DEFAULT '',
  at          TEXT NOT NULL DEFAULT '',
  pushed_at   TEXT NOT NULL DEFAULT ''
);""")
    con.commit()
    _noid_done = True


def _norm_name(n):
    return " ".join(_name_tokens(n))


def _name_hit(a, b):
    """Stricter than same_name (which forgives a shared first four letters, so SUNITA ~ Sunil): here a word of one must
    equal a word of the other, or be spelt nearly the same (Kavita/Kavitha). A name with no usable word matches nobody."""
    import difflib
    for x in _name_tokens(a):
        for y in _name_tokens(b):
            if x == y or (min(len(x), len(y)) >= 4 and difflib.SequenceMatcher(None, x, y).ratio() >= 0.8):
                return True
    return False


def open_orders_for(con, received_at):
    """Blood orders still waiting that a report received then could close (on or before that day, within the lab
    window _report_for uses), not 'test nahi hua'."""
    d = (received_at or "")[:10]
    lo = (dt.date.fromisoformat(d) - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
    out = []
    for o in con.execute("SELECT * FROM blood_order WHERE state='ok' AND day BETWEEN ? AND ? ORDER BY day, id", (lo, d)):
        o = dict(o)
        if o["outcome"] == "not_tested" or _report_for(con, o["clinic_id"], o["day"]) is not None:
            continue
        o["name"] = _name_for(con, o["clinic_id"], o.get("name_seen") or "")
        out.append(o)
    return out


def noid_match(con, name, received_at):
    """The clinic ID this ID-less report belongs to, or '' when it is not certain."""
    cands = [o for o in open_orders_for(con, received_at) if _name_hit(name, o["name"])]
    if len(cands) > 1:
        m = [o for o in cands if o.get("mailed_at")]
        if m:
            cands = m
    if len(cands) > 1:
        e = [o for o in cands if _norm_name(o["name"]) == _norm_name(name)]
        if e:
            cands = e
    if len({o["clinic_id"] for o in cands}) == 1:
        return cands[0]["clinic_id"]
    if not cands and _norm_name(name):
        # the lab sent the same report again: follow the first one that found its patient
        lo = (dt.date.fromisoformat(received_at[:10]) - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
        prev = {r["clinic_id"] for r in con.execute(
            "SELECT name, clinic_id FROM lab_noid WHERE clinic_id<>'' AND received_at>=? AND received_at<=?", (lo, received_at))
            if _norm_name(r["name"]) == _norm_name(name)}
        if len(prev) == 1:
            return prev.pop()
    return ""


def noid_resolve(con, msg_id, cid, how, who=""):
    r = con.execute("SELECT received_at FROM lab_noid WHERE msg_id=?", (msg_id,)).fetchone()
    con.execute("UPDATE lab_noid SET clinic_id=?, how=?, by_user=?, at=? WHERE msg_id=?", (cid, how, who, _stamp(), msg_id))
    con.execute("INSERT OR IGNORE INTO lab_report(msg_id, clinic_id, received_at, pushed_at) VALUES (?,?,?,?)",
                (msg_id, cid, r["received_at"], _stamp()))


def noid_sweep(con):
    """Try again every ID-less report of the last week that is not placed yet (an order may have been written since)."""
    noid_ensure(con)
    since = (_now().date() - dt.timedelta(days=ORPHAN_DAYS)).isoformat()
    n = 0
    for r in con.execute("SELECT * FROM lab_noid WHERE clinic_id='' AND how='' AND received_at>=? ORDER BY received_at",
                         (since,)).fetchall():
        cid = noid_match(con, r["name"], r["received_at"])
        if cid:
            noid_resolve(con, r["msg_id"], cid, "auto")
            n += 1
    if n:
        con.commit()
    return n


def noid_pending(con):
    """ID-less reports of the last week that nobody could place yet -- reception picks."""
    noid_ensure(con)
    since = (_now().date() - dt.timedelta(days=ORPHAN_DAYS)).isoformat()
    return [dict(r) for r in con.execute("SELECT * FROM lab_noid WHERE clinic_id='' AND how='' AND received_at>=? "
                                          "ORDER BY received_at", (since,))]


'''
rep("def pending_counts(con):\n", NOID + "def pending_counts(con):\n")

# 2 -- blood_pending tries the ID-less reports first, so a line clears the moment its report is placeable
rep('''    """(pending, arrived_recently, orphans). Each pending row: the three fields and its state in words."""
    pend_ensure(con)
''', '''    """(pending, arrived_recently, orphans). Each pending row: the three fields and its state in words."""
    pend_ensure(con)
    try:
        noid_sweep(con)                                  # S391
    except Exception:                                    # noqa: BLE001 -- never blocks the list
        pass
''')

# 3 -- the doctors' counts carry the ID-less reports
rep('''    try:
        nm = len(name_mismatches(con))
    except Exception:                                    # noqa: BLE001
        nm = 0
''', '''    try:
        nm = len(name_mismatches(con))
    except Exception:                                    # noqa: BLE001
        nm = 0
    try:
        nx = len(noid_pending(con))                      # S391
    except Exception:                                    # noqa: BLE001
        nx = 0
''')
rep('''"orphans": len(orph), "name_mismatch": nm}''', '''"orphans": len(orph), "name_mismatch": nm, "no_id": nx}''')

# 4 -- the page: a hint for the desk, the ID-less section, and "naam se" on what arrived that way
rep('''    red = len([o for o in pend if o["st"] in ("late", "nomail")])
    sec = _sec("bp", "Blood report baaki", "%d%s" % (len(pend), (" · %d der" % red) if red else ""),
               "".join(rows) or '<p class="sm">Koi report baaki nahi. ✔</p>')''',
    '''    red = len([o for o in pend if o["st"] in ("late", "nomail")])
    hint = ('<p class="sm">Lab ko mail karte waqt naam ke baad clinic ID zaroor likhein, jaise <b>SITA ( 1234 )</b> — '
            'ID ho to report aate hi line yahan se apne aap hat jaati hai.</p>') if can_tap else ""
    sec = _sec("bp", "Blood report baaki", "%d%s" % (len(pend), (" · %d der" % red) if red else ""),
               hint + ("".join(rows) or '<p class="sm">Koi report baaki nahi. ✔</p>'))''')
rep('''    if orphans and (roles & {"maker", "checker"}):
        li = "".join(''', '''    try:
        nxs = noid_pending(con)                          # S391
    except Exception:                                    # noqa: BLE001
        nxs = []
    if nxs:
        li = []
        for r in nxs:
            act = ""
            if can_tap:
                oo = open_orders_for(con, r["received_at"])
                oo.sort(key=lambda o: (not same_name(r["name"], o["name"]) or not _name_tokens(o["name"]), o["day"], o["id"]))
                opts = "".join('<option value="%s">%s · %s · %s</option>' % (_esc(o["clinic_id"]), _esc(o["clinic_id"]),
                               _esc(o["name"] or "—"), _dmy(o["day"])[:6]) for o in oo)
                act = ('<form method="post" action="/finance/slips/pending/act" class="rb"><input type="hidden" name="key" value="nx:%s">'
                       '<select name="cid"><option value="">— kaun hai? —</option>%s</select>'
                       '<input name="cid2" inputmode="numeric" maxlength="12" placeholder="ya ID likhein">'
                       '<button name="act" value="noid_pick">Yahi hai</button>'
                       '<button name="act" value="noid_gone">Hamara nahi</button></form>' % (_esc(r["msg_id"]), opts))
            li.append('<div class="lrow miss"><div class="rl"><b>%s</b> <span class="sm">report %s</span>'
                      '<br><span class="chip ck">ID nahi likha</span></div>%s</div>'
                      % (_esc(r["name"] or "—"), _esc(_dmy(r["received_at"][:10])[:6] + " " + _hm(r["received_at"])), act))
        out.append(_sec("bx", "Report aayi, ID nahi likha", "%d" % len(nxs),
                        '<p class="sm">Lab ne mail mein clinic ID nahi likha, aur naam se pakka nahi hua. Mareez chunein — '
                        'report us line par jud jayegi.</p>' + "".join(li)).replace('class="badge"', 'class="badge red"', 1))
    if orphans and (roles & {"maker", "checker"}):
        li = "".join(''')
rep('''    if gt:
        out.append(_sec("bg", "Aa gayi (kal aur aaj)", "%d" % len(gt), "".join(
            '<div class="lrow"><span class="no">%s</span> %s <span class="sm">✔ %s</span></div>'
            % (_esc(o["clinic_id"]), _esc(o["name"]), _esc((o.get("received_at") or "")[5:16])) for o in gt)))''',
    '''    if gt:
        try:
            byname = {r[0] for r in con.execute("SELECT msg_id FROM lab_noid WHERE clinic_id<>''")}    # S391
        except Exception:                                # noqa: BLE001
            byname = set()
        out.append(_sec("bg", "Aa gayi (kal aur aaj)", "%d" % len(gt), "".join(
            '<div class="lrow"><span class="no">%s</span> %s <span class="sm">✔ %s%s</span></div>'
            % (_esc(o["clinic_id"]), _esc(o["name"]), _esc((o.get("received_at") or "")[5:16]),
               " · naam se juda" if o.get("msg_id") in byname else "") for o in gt)))''')

# 5 -- blood_pending keeps which report closed each line (for "naam se juda")
rep('''        if rep is not None:
            o["received_at"] = rep["received_at"]
            got.append(o)''', '''        if rep is not None:
            o["received_at"] = rep["received_at"]
            o["msg_id"] = rep["msg_id"]
            got.append(o)''')

# 6 -- the taps: pick the patient, or "not ours"
rep('''    m = re.fullmatch(r"xm:(\\d{4}-\\d{2}-\\d{2}):([0-9A-Za-z\\-/]{1,12})", key)
    if m:
        if "maker" not in roles:''', '''    m = re.fullmatch(r"nx:([0-9A-Za-z_\\-]{1,64})", key)
    if m:                                                # S391: the report the lab mailed with no ID
        noid_ensure(con)
        r = con.execute("SELECT * FROM lab_noid WHERE msg_id=?", (m.group(1),)).fetchone()
        if not r:
            return _pend_back("blood", err="Report nahi mili.")
        if r["clinic_id"] or r["how"]:
            return _pend_back("blood", ok="Yeh report pehle hi jud chuki hai.")
        if act == "noid_pick":
            cid = _clean_id(request.form.get("cid2")) or _clean_id(request.form.get("cid"))
            if not cid:
                return _pend_back("blood", err="Mareez chunein ya clinic ID likhein.")
            noid_resolve(con, r["msg_id"], cid, "pick", who)
            has = con.execute("SELECT 1 FROM blood_order WHERE clinic_id=? AND state='ok' LIMIT 1", (cid,)).fetchone()
            msg = ("%s: report jud gayi ✔" % cid) if has else ("%s: report jud gayi — is ID ka test likha nahi tha, "
                                                                "reception dekhe." % cid)
        elif act == "noid_gone":
            con.execute("UPDATE lab_noid SET how='gone', by_user=?, at=? WHERE msg_id=?", (who, now, r["msg_id"]))
            msg = "Theek — yeh report list se hata di."
        else:
            return _pend_back("blood", err="Galat button.")
        _audit_safe(con, 0, "pend_" + act, None, json.dumps({"msg": r["msg_id"]}), who)
        con.commit()
        return _pend_back("blood", ok=msg)
    m = re.fullmatch(r"xm:(\\d{4}-\\d{2}-\\d{2}):([0-9A-Za-z\\-/]{1,12})", key)
    if m:
        if "maker" not in roles:''')

# 7 -- the mailbox's door for an ID-less report (same token as lab-report)
rep('''@bp.route("/finance/slips/api/pending-counts")''', '''@bp.route("/finance/slips/api/lab-noid", methods=["POST"])
def api_lab_noid():
    """S391. The clinic mailbox's Apps Script found a lab report with no clinic ID in the subject: message id, the name
    in the subject, time received. Answers the clinic ID when it is certain (then the report is counted at once), ''
    while it is not -- the mailbox asks again next run and files the PDF when an ID comes back. Same token as lab-report."""
    tok = os.environ.get("FINANCE_CRON_TOKEN", "")
    given = request.headers.get("X-Finance-Cron", "")
    if not (tok and given and _hmac.compare_digest(str(given), str(tok))):
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    rows = j.get("reports") if isinstance(j.get("reports"), list) else [j]
    con = _db()
    ensure(con)
    blood_ensure(con)
    noid_ensure(con)
    good = []
    for x in rows[:200]:
        mid = str(x.get("msg_id") or "")[:64]
        at = str(x.get("received_at") or "")[:19].replace("T", " ")
        if re.fullmatch(r"[0-9A-Za-z_\\-]{1,64}", mid) and re.fullmatch(r"\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}(:\\d{2})?", at):
            good.append((at, mid, " ".join(str(x.get("name") or "").split())[:60]))
    out = []
    for at, mid, nm in sorted(good):
        con.execute("INSERT OR IGNORE INTO lab_noid(msg_id, name, received_at, pushed_at) VALUES (?,?,?,?)",
                    (mid, nm, at, _stamp()))
        r = con.execute("SELECT clinic_id, how FROM lab_noid WHERE msg_id=?", (mid,)).fetchone()
        cid = r["clinic_id"]
        if not cid and not r["how"]:
            cid = noid_match(con, nm, at)
            if cid:
                noid_resolve(con, mid, cid, "auto")
        out.append({"msg_id": mid, "clinic_id": cid, "gone": r["how"] == "gone"})
    con.commit()
    return jsonify(ok=True, reports=out)


@bp.route("/finance/slips/api/pending-counts")''')

open(dst, "wb").write(s.encode("utf-8"))
print("S391 slip_log.py md5", hashlib.md5(s.encode("utf-8")).hexdigest())
