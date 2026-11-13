# ====================================================================== S815 -- Darpan's own Ask line; reports on need (the owner's 'looks right'
#  of 13-Nov 11:33 IST on the S815 mock-up). (a) A question to Darpan lands on his own page, Kal ka hisaab (marg_watch_ask.staff_ref 'darpan:card';
#  'darpan:withdrawn' when the row is no longer open); his one tap is written straight into marg_watch_ask. (b) A sale report asked for again:
#  by itself when several items rise on one closing with no record (D929; the figure is his, mwr.cluster, 3 to start; only moves found after the
#  install), or by him from a section A row. It shows on Shavez's Aaj ki reports and closes itself when VERIFIED sale (Detail) files received
#  after the ask cover every day of it that had a sale.
RPT_KIT = "S815_MARG_WATCH_DARPAN_REPORTS"
RPT_DDL = (
    "CREATE TABLE IF NOT EXISTS marg_watch_report (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, "
    "day_from TEXT NOT NULL, day_to TEXT NOT NULL, why TEXT, row_keys TEXT, asked_by TEXT, asked_at TEXT NOT NULL, closed_at TEXT, closed_how TEXT)",
)
RPT_CLUSTER_DEFAULT = 3
RPT_MAX_DAYS = 7
RPT_SHOW_CLOSED_DAYS = 7
DARPAN_CARD, DARPAN_GONE = "darpan:card", "darpan:withdrawn"


def rpt_ensure(con):
    for s in RPT_DDL:
        con.execute(s)
    if not setting(con, "mwr.since", ""):
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES ('mwr.since', ?, 'S815: moves found after this ask for the sale "
                    "report by themselves; earlier ones never do')", (_ts19(now_iso()),))
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES ('mwr.cluster', ?, 'S815 (D929): this many items or more rising on one "
                "closing with no record ask for those days sale report again -- his figure on the Marg watch')", (str(RPT_CLUSTER_DEFAULT),))


def _rpt_table(con):
    return _table(con, "marg_watch_report")


def rpt_cluster(con):
    try:
        n = int(setting(con, "mwr.cluster", str(RPT_CLUSTER_DEFAULT)))
    except ValueError:
        n = RPT_CLUSTER_DEFAULT
    return max(0, min(n, 99))


def _day(s, plus=0):
    return (dt.date.fromisoformat(str(s)[:10]) + dt.timedelta(days=plus)).isoformat()


def _rpt_span_for(rows):
    """The sale days to ask for: the three days before the later closing, widened to the first day between the closings, at most RPT_MAX_DAYS."""
    to = max(_day(r["day_to"], -1) for r in rows)
    fr = min(min(_day(r["day_to"], -3) for r in rows), min(str(r["day_from"])[:10] for r in rows))
    if (dt.date.fromisoformat(to) - dt.date.fromisoformat(fr)).days >= RPT_MAX_DAYS:
        fr = _day(to, -(RPT_MAX_DAYS - 1))
    return fr, to


def _rpt_days(fr, to):
    d, out = dt.date.fromisoformat(fr), []
    while d.isoformat() <= to:
        out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def _rpt_needed(con, fr, to):
    """The days of the span that had a sale in any report already in (a day with no sale needs no file)."""
    if not _table(con, "mi_sale_line"):
        return _rpt_days(fr, to)
    have = {r[0] for r in con.execute("SELECT DISTINCT substr(bill_date,1,10) FROM mi_sale_line WHERE substr(bill_date,1,10) BETWEEN ? AND ?",
                                      (fr, to))}
    return [d for d in _rpt_days(fr, to) if d in have]


def _rpt_covered(con, fr, to, asked_at):
    """(covered, missing days, newest file time): VERIFIED sale (Detail) files received after the ask, day by day."""
    need = _rpt_needed(con, fr, to)
    if not _table(con, "mi_file"):
        return False, need, None
    files = [(str(a)[:10], str(b)[:10], _ts19(c)) for a, b, c in con.execute(
        "SELECT date_from, date_to, received_at FROM mi_file WHERE type='SALE_BILLWISE' AND variant='DETAIL' AND verdict='VERIFIED' "
        "AND date_from <= ? AND date_to >= ?", (to, fr)) if _ts19(c) > _ts19(asked_at)]
    miss = [d for d in need if not any(a <= d <= b for a, b, _c in files)]
    return (not miss), miss, (max(c for _a, _b, c in files) if files else None)


def rpt_open(con):
    """READ ONLY (Shavez's page): the open asks, each with its days and whether the files have already come. [dict]."""
    if not _rpt_table(con):
        return []
    out = []
    for rid, kind, fr, to, why, by, at in con.execute("SELECT id, kind, day_from, day_to, why, asked_by, asked_at FROM marg_watch_report "
                                                      "WHERE closed_at IS NULL ORDER BY id").fetchall():
        ok, miss, last = _rpt_covered(con, fr, to, at)
        out.append(dict(id=rid, kind=kind, day_from=fr, day_to=to, why=why or "", by=by or "", at=at, arrived=ok, missing=miss, last=last))
    return out


def rpt_sync(con, commit=True):
    """Close every ask whose files have come. Returns the number closed."""
    if not _rpt_table(con):
        return 0
    n = 0
    for r in rpt_open(con):
        if r["arrived"]:
            n += con.execute("UPDATE marg_watch_report SET closed_at=?, closed_how=? WHERE id=? AND closed_at IS NULL",
                             (_ts19(now_iso()), "arrived %s" % (r["last"] or ""), r["id"])).rowcount
    if n and commit:
        con.commit()
    return n


def _rpt_add(con, ref, fr, to, why, keys, who):
    """One ask; the same ref never twice; an open ask that already covers the days is enough. Returns the new id or None."""
    if con.execute("SELECT 1 FROM marg_watch_report WHERE ref=?", (ref,)).fetchone():
        return None
    if con.execute("SELECT 1 FROM marg_watch_report WHERE closed_at IS NULL AND kind='SALE' AND day_from<=? AND day_to>=?", (fr, to)).fetchone():
        return None
    cur = con.execute("INSERT INTO marg_watch_report (ref, kind, day_from, day_to, why, row_keys, asked_by, asked_at) VALUES (?,?,?,?,?,?,?,?)",
                      (ref, "SALE", fr, to, why, ",".join(keys), who, _ts19(now_iso())))
    _audit(con, who, "marg_watch_report", ref, dict(day_from=fr, day_to=to, rows=keys))
    return cur.lastrowid


def rpt_auto(con, V=None, commit=True):
    """D929: several items rising on ONE closing with no record, found after the install -> that closing's sale days asked for again, once."""
    if not _rpt_table(con):
        return 0
    n_min = rpt_cluster(con)
    if n_min < 2:
        return 0
    since = setting(con, "mwr.since", "")
    if not since:
        return 0
    V = V or hand_view(con)
    per = collections.OrderedDict()
    for r in V["counted"]:
        if float(r.get("shift") or 0) > 0 and _ts19(r.get("found_at")) >= _ts19(since):
            per.setdefault(str(r["day_to"])[:10], []).append(r)
    made = 0
    for day_to, rs_ in per.items():
        if len(rs_) < n_min:
            continue
        fr, to = _rpt_span_for(rs_)
        if con.execute("SELECT 1 FROM marg_watch_report WHERE kind='SALE' AND day_from<=? AND day_to>=?", (fr, to)).fetchone():
            continue                                          # S448 review S1: those days were already asked (open or closed) -- never twice
        why = "%d items rose with no record on the %s closing: %s" % (len(rs_), dmon(day_to), ", ".join(
            "%s %s" % (r["item"], _H().snum(r["shift"])) for r in rs_[:6]) + (" …" if len(rs_) > 6 else ""))
        if _rpt_add(con, "cluster:%s" % day_to, fr, to, why, ["hand:%d" % int(r["id"]) for r in rs_], "auto"):
            made += 1
    if made and commit:
        con.commit()
    return made


def rpt_tick(con, V=None):
    """The five-minute pass (owner_notice's tick) and every page view: close what has come, then ask what the cluster rule asks. Never raises."""
    try:
        rpt_ensure(con)
        con.commit()
        rpt_sync(con)
        rpt_auto(con, V)
    except Exception:                                         # noqa: BLE001
        try:
            con.rollback()
        except sqlite3.Error:
            pass


def rpt_row_map(con):
    """{row key: the newest OPEN ask that names it}."""
    out = {}
    if not _rpt_table(con):
        return out
    for rid, keys, fr, to in con.execute("SELECT id, row_keys, day_from, day_to FROM marg_watch_report WHERE closed_at IS NULL ORDER BY id"):
        for k in str(keys or "").split(","):
            if k:
                out[k] = dict(id=rid, day_from=fr, day_to=to)
    return out


@_hand_write
def rpt_ask_row(con, who, rid):
    """He asks from a section A row: the sale days around that move, for Shavez."""
    rpt_ensure(con)
    V = hand_view(con)
    r = next((x for x in V["counted"] if int(x["id"]) == int(rid)), None)
    if r is None:
        return False, "This move is no longer open — the page was out of date. Reload it.", 409
    fr, to = _rpt_span_for([r])
    if con.execute("SELECT 1 FROM marg_watch_report WHERE closed_at IS NULL AND kind='SALE' AND day_from<=? AND day_to>=?", (fr, to)).fetchone():
        return False, "Already asked — the sale report %s to %s is on Shavez's page." % (dmon(fr), dmon(to)), 409
    new = _rpt_add(con, "row:hand:%d:%s" % (int(rid), _ts19(now_iso())), fr, to, "you, from the row %s %s" % (r["item"], _H().snum(r["shift"])),
                   ["hand:%d" % int(rid)], who)
    con.commit()
    if not new:
        return False, "Already asked.", 409
    return True, "Asked — on Shavez's page: the sale report %s to %s." % (dmon(fr), dmon(to)), 200


@_hand_write
def rpt_set_cluster(con, who, n):
    s = str(n if n is not None else "").strip()
    if not re.match(r"^\d{1,2}$", s) or not (0 <= int(s) <= 99):
        return False, "A whole number, 0 to 99 (0 or 1 = never by itself).", 400
    rpt_ensure(con)
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('mwr.cluster', ?, 'S815 (D929): this many items or more rising on one "
                "closing with no record ask for those days sale report again -- his figure on the Marg watch')", (str(int(s)),))
    _audit(con, who, "marg_watch_report_cluster", "", dict(n=int(s)))
    con.commit()
    return True, "Saved: %s." % (("%d or more items" % int(s)) if int(s) >= 2 else "never by itself"), 200


def rpt_html(con):
    """The 'Reports asked for' strip on section A. Never raises."""
    try:
        rpt_ensure(con)
        rows = []
        if _rpt_table(con):
            cut = _ts19((now_ist() - dt.timedelta(days=RPT_SHOW_CLOSED_DAYS)).isoformat(sep=" "))
            rows = con.execute("SELECT id, day_from, day_to, why, asked_by, asked_at, closed_at, closed_how FROM marg_watch_report "
                               "WHERE closed_at IS NULL OR closed_at >= ? ORDER BY (closed_at IS NULL) DESC, id DESC", (cut,)).fetchall()
        n = rpt_cluster(con)
        h = ['<div class="closep" style="margin:0 0 12px;border-color:#b2ccff;background:#f8faff"><b>Reports asked for</b> '
             '<span class="note">— each closes itself when the file arrives; the rows are judged again</span>']
        if rows:
            h.append('<table class="btab" style="margin-top:8px"><tbody><tr class="hd"><th>Report</th><th>Dates</th><th>Why</th><th>Asked</th><th>State</th></tr>')
            for rid, fr, to, why, by, at, cl, how in rows:
                when = dmon(str(at)[:10]) + " " + str(at)[11:16]
                st = ('<span class="st ans">Arrived %s ✓</span>' % esc(dmon(str(cl)[:10]) + " " + str(cl)[11:16])) if cl else \
                     '<span class="st late">On Shavez\'s page</span>'
                h.append('<tr><td>Sale (Detail)</td><td>%s</td><td>%s</td><td>%s<br><span class="note">%s</span></td><td>%s</td></tr>'
                         % (esc(dmon(fr) if fr == to else "%s – %s" % (dmon(fr), dmon(to))), esc(why or ""),
                            "by itself" if by == "auto" else "you", esc(when), st))
            h.append("</tbody></table>")
        else:
            h.append('<p class="note" style="margin:6px 0 0">None asked yet.</p>')
        h.append('<div class="askrow" style="margin:8px 0 0"><label for="rcluster">Ask by itself when</label><input id="rcluster" type="text" '
                 'inputmode="numeric" maxlength="2" value="%d" style="width:50px" aria-label="Items rising together"><span>or more items rise on one '
                 'closing with no record.</span><button type="button" onclick="mwRCluster(this)">Save</button><span class="msg"></span></div></div>' % n)
        return "".join(h)
    except Exception as e:                                    # noqa: BLE001
        return '<p class="note">Reports asked for: not readable just now (%s).</p>' % esc(e.__class__.__name__)


def rpt_row_button(r):
    """One more button on an open section A row."""
    if (r.get("act") or {}).get("action") == "close":
        return ""
    if r.get("rpt"):
        return ('<p class="note" style="margin:8px 0 0">The sale report %s to %s is asked for — on Shavez\'s page until it arrives.</p>'
                % (esc(dmon(r["rpt"]["day_from"])), esc(dmon(r["rpt"]["day_to"]))))
    fr, to = _rpt_span_for([r])
    return ('<div class="askrow" style="margin:8px 0 0"><button type="button" data-h="%d" onclick="mwRAsk(this)">Ask for the sale report again — '
            '%s to %s</button><span class="note">goes to Shavez\'s page</span><span class="msg"></span></div>' % (int(r["id"]), esc(dmon(fr)), esc(dmon(to))))


# ---- Darpan's own page (Kal ka hisaab) -- read and answered there through these two
def ask_for_darpan(con):
    """The questions on Darpan's page: open, on his page, not answered. [dict(id, text, codes, answers, at)]."""
    if not _ask_tables(con):
        return []
    out = []
    for aid, text, codes, at in con.execute("SELECT id, text_hi, codes, asked_at FROM marg_watch_ask WHERE to_whom='darpan' AND staff_ref=? "
                                            "AND answered_at IS NULL ORDER BY id", (DARPAN_CARD,)).fetchall():
        cs = [c for c in str(codes or "").split(",") if c in ASK_ANS]
        out.append(dict(id=aid, text=text or "", codes=cs, answers=[dict(code=c, label=ASK_ANS[c]) for c in cs], at=str(at or "")[:16]))
    return out


def ask_answer_darpan(con, who, aid, code, line=""):
    """His one tap: (ok, message, http). Once only; only an answer offered on that question; no take-back. The caller's connection commits here.
    S448 (review S3): a busy database answers 503 with a Hindi line (rolled back), never a 500; every message is plain Hindi."""
    try:
        return _ask_answer_darpan(con, who, aid, code, line)
    except sqlite3.Error:
        try:
            con.rollback()
        except sqlite3.Error:
            pass
        return False, "Abhi system vyast hai -- ek minute baad phir dabaiye.", 503


def _ask_answer_darpan(con, who, aid, code, line=""):
    try:
        aid = int(aid)
    except (TypeError, ValueError):
        return False, "Yeh sawaal nahin mila -- page dobara kholiye.", 400
    if not _ask_tables(con):
        return False, "Yeh sawaal nahin mila -- page dobara kholiye.", 404
    r = con.execute("SELECT codes FROM marg_watch_ask WHERE id=? AND to_whom='darpan' AND staff_ref=? AND answered_at IS NULL", (aid, DARPAN_CARD)).fetchone()
    if r is None:
        gone = con.execute("SELECT 1 FROM marg_watch_ask WHERE id=? AND to_whom='darpan' AND staff_ref=? AND answered_at IS NULL", (aid, DARPAN_GONE)).fetchone()
        return False, ("Yeh sawaal Doctor sahab ne hata diya hai -- kuch karna nahin." if gone else "Is sawaal ka jawab pehle hi ho chuka hai."), 409
    if code not in ASK_ANS or code not in str(r[0] or "").split(","):
        return False, "Yeh jawab is sawaal mein nahin hai -- page dobara kholiye.", 400
    line = re.sub(r"[\s|]+", " ", str(line or "")).strip()[:300] or None
    n = con.execute("UPDATE marg_watch_ask SET answer_kind=?, answer_line=?, answered_by=?, answered_at=? WHERE id=? AND staff_ref=? AND answered_at IS NULL",
                    (code, line, who, _ts19(now_iso()), aid, DARPAN_CARD)).rowcount
    if n != 1:
        con.rollback()
        return False, "Is sawaal ka jawab pehle hi ho chuka hai.", 409
    _audit(con, who, "marg_watch_ask_answer", "ask:%d" % aid, dict(answer=code, line=line))
    con.commit()
    return True, "Jawab chala gaya.", 200


def _ask_open_on_card(con, keys):
    """S815 (and the S814 review's S3, made exact): a row is 'already asked' only while its question still stands on a staff page --
    Darpan's 'darpan:card', or Amir's job still open. A withdrawn question does not block a new one after a reopen."""
    if not keys or not _ask_tables(con):
        return False
    q = ",".join("?" * len(keys))
    for ref in [r[0] for r in con.execute("SELECT DISTINCT a.staff_ref FROM marg_watch_ask a JOIN marg_watch_ask_row r ON r.ask_id = a.id "
                                          "WHERE a.staff_ref IS NOT NULL AND a.answered_at IS NULL AND r.row_key IN (%s)" % q, keys)]:
        if ref == DARPAN_CARD:
            return True
        if str(ref).startswith("amir_job:"):
            try:
                jid = int(str(ref).split(":", 1)[1])
            except (ValueError, IndexError):
                continue
            if not _table(con, "amir_job") or con.execute("SELECT 1 FROM amir_job WHERE id=? AND done_at IS NULL", (jid,)).fetchone():
                return True
    return False


