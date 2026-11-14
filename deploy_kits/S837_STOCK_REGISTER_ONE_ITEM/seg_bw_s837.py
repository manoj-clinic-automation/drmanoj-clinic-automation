# ====================================================================== S837_STOCK_REGISTER_ONE_ITEM (14-Nov-2026, Sanjeevni session 463)
#  The owner's "Mockup is good" of 20:28 IST on s463_stock_register_mock_v1, with his word: "keep it with myself, with a switch for Shavez to
#  turn it off or on for him. Start Shavez off, on for me, and I should have a flow from the portal in multiple ways."
#  (a) From a section A row, or from his own list page (PAGE/take), he asks for Marg's Stock Register for ONE item and its days.
#      The ask is HIS: on his list page, on the Sanjeevni Hub's Needs-you and its Go to (with a count). Shavez sees it on Aaj ki reports
#      only when his switch is ON (setting mwr.reg_shavez, OFF to start; a figure he changes on the list page and on the Marg watch).
#  (b) The register arrives through the door, read name-free (marg_ingest/marg_register.py: mi_register, mi_register_line); an open ask
#      whose item and days it covers closes itself.
#  (c) On the row the register is shown as a table; a voucher-type entry only Marg holds that equals the move takes the row out of the count
#      (Explained after all > 'An entry only in Marg's Stock Register'); a balance that moved with no entry stays counted, with Marg's proof.
#  Reads mi_register / mi_register_line; writes only marg_watch_report (one added column, item) and its one setting. Fail-soft everywhere.
REG_KIT = "S837_STOCK_REGISTER_ONE_ITEM"
REG_TAKE = PAGE + "/take"
REG_SHOW_DAYS = 14
REG_MAX_DAYS = 92
REG_TRADE = ("SALE", "SALE RETURN", "PURCHASE", "PURCHASE RETURN")      # the system holds these through its own reports
REG_WORDS = "An entry only in Marg's Stock Register"


def _reg_norm(s):
    return re.sub(r"\s+", " ", str(s or "").upper()).strip()


REG_CUT = 20                                                  # Marg's sale export cuts an item's name at 20 letters (seen in mi_sale_line)
_REG_KNOWN = []                                               # every item name the stock record knows, refreshed by _reg_all (F-1423 M3)


def _reg_same(a, b, known=None):
    """The same item: the exact name. A prefix only where one side is exactly Marg's 20-letter cut of the other AND no other item the stock
    record knows shares that cut (F-1423 M3: the first build matched any two names agreeing in their first 20 letters)."""
    a, b = _reg_norm(a), _reg_norm(b)
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = (a, b) if len(a) < len(b) else (b, a)
    if len(short) != REG_CUT or not long_.startswith(short):
        return False
    names = {_reg_norm(n) for n in (known if known is not None else _REG_KNOWN)}
    return short not in names and len([n for n in names if n.startswith(short) and len(n) > REG_CUT]) == 1 and long_ in names


def reg_ensure(con):
    rpt_ensure(con)
    have = {r[1] for r in con.execute("PRAGMA table_info(marg_watch_report)")}
    if "item" not in have:
        con.execute("ALTER TABLE marg_watch_report ADD COLUMN item TEXT")
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES ('mwr.reg_shavez', 'off', 'S837: Marg''s Stock Register asks also "
                "shown on Shavez''s Aaj ki reports (on / off) -- OFF to start, the owner''s word of 14-Nov 20:28')")


_ensure_before_s837 = ensure


def ensure(con):                                              # noqa: F811 -- S837: + the item column and the switch
    _ensure_before_s837(con)
    reg_ensure(con)


def reg_shavez(con):
    return setting(con, "mwr.reg_shavez", "off").strip().lower() == "on"


def _reg_all(con):
    """Every register read at the door: [dict(md5, seq, item, per, date_from, date_to, ok, note, stored_at)], newest first. Read only."""
    global _REG_KNOWN
    if not _table(con, "mi_register"):
        return []
    _REG_KNOWN = _reg_names(con)
    cols = ("md5", "seq", "item", "per", "date_from", "date_to", "opening_u", "closing_u", "ok", "note", "stored_at", "n_jumps")
    return [dict(zip(cols, r)) for r in con.execute("SELECT %s FROM mi_register WHERE seq > 0 ORDER BY stored_at DESC, md5, seq" % ", ".join(cols))]


def _reg_lines(con, md5, seq):
    cols = ("n", "day", "bill_no", "kind", "batch", "qty_u", "value_p", "bal_u", "jump_u")
    return [dict(zip(cols, r)) for r in con.execute("SELECT %s FROM mi_register_line WHERE md5=? AND seq=? ORDER BY n" % ", ".join(cols),
                                                    (md5, seq))]


def reg_find(con, item, fr, to, regs=None, need_ok=False):
    """The newest register of this item whose days cover fr..to, with its lines; else None. need_ok: only one whose own Received / Issued
    footers agree with its rows (F-1423 M2) -- the only kind that may close an ask or settle a row."""
    for g in (regs if regs is not None else _reg_all(con)):
        if need_ok and int(g.get("ok") or 0) != 1:
            continue
        if _reg_same(g["item"], item) and str(g["date_from"]) <= fr and str(g["date_to"]) >= to:
            g = dict(g)
            g["lines"] = _reg_lines(con, g["md5"], g["seq"])
            return g
    return None


def _reg_rows(con, where="", args=()):
    if not _rpt_table(con):
        return []
    have = {r[1] for r in con.execute("PRAGMA table_info(marg_watch_report)")}
    if "item" not in have:
        return []
    cols = ("id", "item", "day_from", "day_to", "why", "row_keys", "asked_by", "asked_at", "closed_at", "closed_how")
    return [dict(zip(cols, r)) for r in con.execute("SELECT %s FROM marg_watch_report WHERE kind='REGISTER' %s ORDER BY id" % (", ".join(cols), where), args)]


def reg_open(con):
    """The open asks for a Stock Register, each with whether a register covering it is already in. [dict]."""
    regs = _reg_all(con)
    out = []
    for a in _reg_rows(con, "AND closed_at IS NULL"):
        g = reg_find(con, a["item"], a["day_from"], a["day_to"], regs, need_ok=True)
        a.update(arrived=bool(g), reg=g)
        out.append(a)
    return out


def reg_sync(con, commit=True):
    """Close every open ask a register now covers. -> the number closed."""
    n = 0
    for a in reg_open(con):
        if a["arrived"]:
            n += con.execute("UPDATE marg_watch_report SET closed_at=?, closed_how=? WHERE id=? AND closed_at IS NULL",
                             (_ts19(now_iso()), "arrived %s" % _ts19(a["reg"]["stored_at"]), a["id"])).rowcount
    if n and commit:
        con.commit()
    return n


def reg_for_shavez(con):
    """READ ONLY (Shavez's page): the open asks -- none at all while his switch is OFF."""
    try:
        if not reg_shavez(con):
            return []
        return [dict(id=a["id"], item=a["item"], day_from=a["day_from"], day_to=a["day_to"], arrived=a["arrived"]) for a in reg_open(con)]
    except Exception:                                         # noqa: BLE001
        return []


def _reg_span(r):
    return _day(r["day_from"], -1), str(r["day_to"])[:10]


def _reg_add(con, who, item, fr, to, why, keys):
    item = _reg_norm(item)
    for a in _reg_rows(con, "AND closed_at IS NULL"):
        if _reg_same(a["item"], item) and a["day_from"] <= fr and a["day_to"] >= to:
            return None, "Already asked — %s, %s to %s, is on your list." % (a["item"], dmon(a["day_from"]), dmon(a["day_to"]))
    ref = "reg:%s:%s:%s:%s" % (item[:40], fr, to, _ts19(now_iso()))
    cur = con.execute("INSERT INTO marg_watch_report (ref, kind, day_from, day_to, why, row_keys, asked_by, asked_at, item) VALUES (?,?,?,?,?,?,?,?,?)",
                      (ref, "REGISTER", fr, to, why, ",".join(keys), who, _ts19(now_iso()), item))
    _audit(con, who, "marg_watch_register", ref, dict(item=item, day_from=fr, day_to=to, rows=keys))
    return cur.lastrowid, ""


def _reg_where(con):
    return "on your list and on Shavez's page" if reg_shavez(con) else "on your list"


@_hand_write
def reg_ask_row(con, who, rid):
    """He asks from a section A row: that item, from the day before the move to its closing."""
    reg_ensure(con)
    V = hand_view(con)
    r = next((x for x in V["counted"] + V["closed"] + V["explained"] if int(x["id"]) == int(rid)), None)
    if r is None:
        return False, "This move is no longer on the page — reload it.", 409
    try:
        fr, to = _reg_span(r)
        dt.date.fromisoformat(fr), dt.date.fromisoformat(to)
    except (TypeError, ValueError, KeyError):
        return False, "This row's days cannot be read — reload the page.", 400
    if reg_find(con, r["item"], fr, to, need_ok=True):
        return False, "Marg's Stock Register for %s, %s to %s, is already in — it is shown in the row." % (r["item"], dmon(fr), dmon(to)), 409
    new, why = _reg_add(con, who, r["item"], fr, to, "you, from the row %s %s" % (r["item"], _H().snum(r["shift"])), ["hand:%d" % int(rid)])
    if not new:
        return False, why, 409
    con.commit()
    return True, "Asked — %s: Stock Register for %s, %s to %s." % (_reg_where(con), r["item"], dmon(fr), dmon(to)), 200


@_hand_write
def reg_ask_item(con, who, item, fr, to):
    """He asks from his list page, for any item and days."""
    reg_ensure(con)
    item = _reg_norm(item)
    if not item or len(item) > 60:
        return False, "The item's name, as Marg has it.", 400
    try:
        a, b = dt.date.fromisoformat(str(fr)[:10]), dt.date.fromisoformat(str(to)[:10])
    except ValueError:
        return False, "Both days, please (From and To).", 400
    if a > b:
        return False, "From must not be after To.", 400
    if b > now_ist().date():
        return False, "To cannot be a day still to come.", 400
    if (b - a).days >= REG_MAX_DAYS:
        return False, "At most %d days in one ask." % REG_MAX_DAYS, 400
    if reg_find(con, item, a.isoformat(), b.isoformat(), need_ok=True):
        return False, "Already in — %s, %s to %s, is below under Arrived." % (item, dmon(a.isoformat()), dmon(b.isoformat())), 409
    new, why = _reg_add(con, who, item, a.isoformat(), b.isoformat(), "you, from your list", [])
    if not new:
        return False, why, 409
    con.commit()
    return True, "Asked — %s." % _reg_where(con), 200


@_hand_write
def reg_set_shavez(con, who, on):
    reg_ensure(con)
    con.execute("UPDATE setting SET value=? WHERE key='mwr.reg_shavez'", ("on" if on else "off",))
    _audit(con, who, "marg_watch_register_shavez", "", dict(on=bool(on)))
    con.commit()
    return True, ("Shavez: ON — your asks also show on his Aaj ki reports." if on else "Shavez: OFF — the asks stay with you only."), 200


def reg_count(con):
    """The Hub's Go to badge: the open asks. -> (n, title)."""
    try:                                                      # READ ONLY (F-1423 S5): no DDL, no sync, no rollback here -- the tick closes them
        op = [a for a in reg_open(con) if not a["arrived"]]
        return len(op), "; ".join("%s %s–%s" % (a["item"], dmon(a["day_from"]), dmon(a["day_to"])) for a in op[:6])
    except Exception:                                         # noqa: BLE001
        return 0, ""


def reg_needs_lines(con):
    """The Sanjeevni Hub's Needs-you: one line while any ask is open -- his own while Shavez is OFF; with Shavez ON, only asks over a day old."""
    try:
        n_all, _t = reg_count(con)
        if not n_all:
            return []
        on = reg_shavez(con)
        cut = _ts19((now_ist() - dt.timedelta(days=1)).isoformat(sep=" "))
        op = [a for a in reg_open(con) if not a["arrived"] and (not on or _ts19(a["asked_at"]) <= cut)]
        if not op:
            return []
        names = ", ".join("%s (%s–%s)" % (a["item"], dmon(a["day_from"]), dmon(a["day_to"])) for a in op[:3]) + (" and %d more" % (len(op) - 3) if len(op) > 3 else "")
        who = "for you to take" if not on else "asked over a day ago, not in yet"
        return [dict(cls="warn", target="checks-marg", href=REG_TAKE,
                     text="Marg's Stock Register %s — %d item%s: %s" % (who, len(op), "" if len(op) == 1 else "s", names))]
    except Exception:                                         # noqa: BLE001
        return []


def _reg_q(u, per):
    """Units shown as Marg prints them: strips:loose when the pack has more than one, else a plain number."""
    if u is None:
        return ""
    u = int(u)
    if per and int(per) > 1:
        a, b = divmod(abs(u), int(per))
        return "%s%d:%d" % ("-" if u < 0 else "", a, b)
    return "%d" % u


def _reg_factor(g, r):
    """Units of the register per unit of the stock record: 1 or the pack, PROVEN from Marg's own balance at the move's later closing.
    None when the pack is more than one and the balance does not prove which (F-1423 M1: the first build guessed 1) -- then nothing settles."""
    per = int(g.get("per") or 1)
    if per <= 1:
        return 1
    bal = g.get("opening_u")
    for ln in g["lines"]:
        if str(ln["day"]) <= str(r["day_to"]):
            bal = ln["bal_u"]
    mt = r.get("marg_to")
    if bal is None or mt in (None, 0):
        return None
    hits = [f for f in (1, per) if abs(float(mt) * f - float(bal)) < 0.5]
    return hits[0] if len(hits) == 1 else None


def reg_verdict(con, r, regs=None):
    """What Marg's own register says about a section A move. None while no register covers it."""
    fr_, to_ = _day(r["day_from"], 1), str(r["day_to"])[:10]
    g = reg_find(con, r["item"], fr_, to_, regs, need_ok=True) or reg_find(con, r["item"], fr_, to_, regs)   # a sound one first (M2)
    if not g:
        return None
    lo, hi = str(r["day_from"])[:10], str(r["day_to"])[:10]
    win = [ln for ln in g["lines"] if lo < str(ln["day"]) <= hi]
    f = _reg_factor(g, r)
    if int(g.get("ok") or 0) != 1:                            # F-1423 M2: Marg's own totals disagree -- shown, settles nothing
        return dict(kind="unsure", note="Marg's own totals in this file do not add up (%s), so it settles nothing — ask for it again." % (g.get("note") or "footers"),
                    reg=g, lo=lo, hi=hi, factor=f)
    if f is None:                                             # F-1423 M1: the units cannot be matched -- shown, settles nothing
        return dict(kind="unsure", note="Marg's own Stock Register is below, but its units could not be matched to the stock record's "
                    "(pack %s), so it settles nothing." % (g.get("pack") or g.get("per")), reg=g, lo=lo, hi=hi, factor=None)
    want = float(r.get("shift") or 0) * f
    other = [ln for ln in win if _reg_norm(ln["kind"]) not in REG_TRADE]
    ov = sum(int(ln["qty_u"]) for ln in other)
    jv = sum(int(ln["jump_u"]) for ln in win)
    per = g.get("per") or 1
    if other and abs(ov - want) < 0.5:
        kind = "marg_only"
        note = "Marg's own Stock Register holds %s — an entry our system never received." % "; ".join(
            "%s %s (%s, %s)" % (ln["kind"], ln["bill_no"] or "with no number", dmon(ln["day"]), ("+" if int(ln["qty_u"]) > 0 else "") + _reg_q(ln["qty_u"], per))
            for ln in other)
    elif jv and abs(jv - want) < 0.5:
        kind = "jump"
        note = "Marg's own Stock Register has no entry for this: its balance moved by %s between %s and %s with nothing behind it." % (
            ("+" if jv > 0 else "") + _reg_q(jv, per), dmon(lo), dmon(hi))
    elif not win and not jv:
        kind = "quiet"
        note = "Marg's own Stock Register shows no movement between %s and %s." % (dmon(lo), dmon(hi))
    else:
        kind = "mixed"
        note = "Marg's own Stock Register for these days is below; no one entry in it accounts for the move."
    return dict(kind=kind, note=note, reg=g, lo=lo, hi=hi, factor=f)


def reg_table(V):
    """The register in the row: date, entry, in, out, balance -- the move's days marked."""
    g, lo, hi = V["reg"], V["lo"], V["hi"]
    per = g.get("per") or 1
    fr = _day(lo, -1)
    lines = [ln for ln in g["lines"] if fr <= str(ln["day"]) <= hi]
    h = ['<div class="closep" style="border:2px solid #f0b400;background:#fffdf3"><b>Marg\'s Stock Register — %s — %s to %s</b> '
         '<span class="note">(read %s; no patient name is kept)</span>' % (esc(g["item"]), esc(dmon(g["date_from"])), esc(dmon(g["date_to"])),
                                                                         esc(dmon(str(g["stored_at"])[:10]) + " " + _ts19(g["stored_at"])[11:16]))]
    h.append('<table class="btab" style="margin-top:6px;min-width:0"><tbody><tr class="hd"><th>Date</th><th>Entry</th><th class="n">In</th>'
             '<th class="n">Out</th><th class="n">Balance</th></tr>')
    shown = lines[-60:]
    if len(lines) > len(shown):
        h.append('<tr><td colspan="5" class="note">… %d earlier entries of these days not shown</td></tr>' % (len(lines) - len(shown)))
    if not shown:
        h.append('<tr><td colspan="5" class="note">No entry in these days.</td></tr>')
    for ln in shown:
        q = int(ln["qty_u"])
        hit = (lo < str(ln["day"]) <= hi) and (int(ln["jump_u"]) or _reg_norm(ln["kind"]) not in REG_TRADE)
        jump = ('<br><span class="note" style="color:#a3231b">the balance moved %s more than this entry</span>'
                % esc(("+" if int(ln["jump_u"]) > 0 else "") + _reg_q(ln["jump_u"], per))) if int(ln["jump_u"]) else ""
        h.append('<tr%s><td>%s</td><td>%s %s%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td></tr>'
                 % (' style="background:#fff4d6;font-weight:600"' if hit else "", esc(dmon(ln["day"])), esc(ln["kind"]), esc(ln["bill_no"]), jump,
                    esc(_reg_q(q, per)) if q > 0 else "", esc(_reg_q(-q, per)) if q < 0 else "", esc(_reg_q(ln["bal_u"], per))))
    h.append("</tbody></table>")
    good = V["kind"] in ("marg_only",)
    h.append('<p style="margin:8px 0 0;padding:8px 10px;border-left:4px solid %s;background:%s">%s</p></div>'
             % ("#0b6b3a" if good else "#a3231b", "#f3fbf5" if good else "#fef6f5", esc(V["note"])))
    return "".join(h)


_hand_view_before_s837 = hand_view


def hand_view(con):                                           # noqa: F811 -- S837: the register's word on each row; an entry only Marg holds explains it
    V = _hand_view_before_s837(con)
    try:
        regs = _reg_all(con)
        asks = {}
        for a in _reg_rows(con, "AND closed_at IS NULL"):
            for k in str(a.get("row_keys") or "").split(","):
                if k:
                    asks[k] = a
        keep = []
        for r in V["counted"]:
            r["reg_ask"] = asks.get("hand:%d" % int(r["id"]))
            r["reg"] = reg_verdict(con, r, regs) if regs else None
            if r["reg"] and r["reg"]["kind"] == "marg_only":
                r["rec_kind"], r["rec_ref"], r["rec_note"] = "marg_only", "", r["reg"]["note"]
                V["explained"].append(r)
            else:
                keep.append(r)
        if len(keep) != len(V["counted"]):                    # a question on a row the register explained leaves the staff card (S446 review S6)
            try:
                ask_withdraw(con, {"hand:%d" % int(r["id"]) for r in V["counted"]}, {"hand:%d" % int(r["id"]) for r in keep})
            except Exception:                                 # noqa: BLE001
                try:
                    con.rollback()
                except sqlite3.Error:
                    pass
        V["counted"] = keep
        for r in V["closed"]:
            r["reg_ask"] = asks.get("hand:%d" % int(r["id"]))
            r["reg"] = reg_verdict(con, r, regs) if regs else None
        for r in V["counted"]:
            r["peers"] = [p for p in V["counted"] if p["day_to"] == r["day_to"] and p["id"] != r["id"]]
        H = _H()
        if "marg_only" not in H.REC_WORDS:
            H.REC_WORDS["marg_only"] = REG_WORDS
    except Exception:                                         # noqa: BLE001 -- the page as it was
        pass
    return V


_hand_status_before_s837 = _hand_status


def _hand_status(r):                                          # noqa: F811 -- S837
    act = r.get("act") or {}
    if not r.get("ask") and not r.get("rpt") and act.get("action") not in ("close", "notok"):
        if r.get("reg") and r["reg"]["kind"] == "jump":
            return '<span class="st late">No entry in Marg either</span>'
        if r.get("reg_ask"):
            return '<span class="st late">Register asked</span>'
    return _hand_status_before_s837(r)


_rpt_row_button_before_s837 = rpt_row_button


def rpt_row_button(r):                                        # noqa: F811 -- S837: + Marg's Stock Register, asked or shown
    h = _rpt_row_button_before_s837(r)
    try:
        if r.get("reg"):
            return h + reg_table(r["reg"])
        if (r.get("act") or {}).get("action") == "close":
            return h
        fr, to = _reg_span(r)
        if r.get("reg_ask"):
            a = r["reg_ask"]
            return h + ('<p class="note" style="margin:8px 0 0">Marg\'s Stock Register for this item, %s to %s, is asked for — '
                        '<a href="%s">on your list</a> until it arrives.</p>' % (esc(dmon(a["day_from"])), esc(dmon(a["day_to"])), REG_TAKE))
        return h + ('<div class="askrow" style="margin:8px 0 0"><button type="button" data-h="%d" onclick="mwRegAsk(this)">Ask Marg\'s Stock Register — '
                    '%s, %s to %s</button><span class="note">%s</span><span class="msg"></span></div>'
                    % (int(r["id"]), esc(r["item"]), esc(dmon(fr)), esc(dmon(to)), "comes to your list" if not _REG_SH else
                       "comes to your list and Shavez's page"))
    except Exception:                                         # noqa: BLE001
        return h


_rpt_open_before_s837 = rpt_open


def rpt_open(con):                                            # noqa: F811 -- S837: the sale asks only (Shavez's sale card, their closing)
    if not _rpt_table(con):
        return []
    return [r for r in _rpt_open_before_s837(con) if r.get("kind", "SALE") == "SALE"]


def rpt_row_map(con):                                         # noqa: F811 -- S837: the sale asks only (a register ask has its own map)
    out = {}
    if not _rpt_table(con):
        return out
    for rid, keys, fr, to in con.execute("SELECT id, row_keys, day_from, day_to FROM marg_watch_report WHERE closed_at IS NULL AND kind='SALE' ORDER BY id"):
        for k in str(keys or "").split(","):
            if k:
                out[k] = dict(id=rid, day_from=fr, day_to=to)
    return out


_rpt_tick_before_s837 = rpt_tick


def rpt_tick(con, V=None):                                    # noqa: F811 -- S837: + close the register asks a register now covers
    _rpt_tick_before_s837(con, V)
    try:
        reg_ensure(con)
        con.commit()
        reg_sync(con)
    except Exception:                                         # noqa: BLE001
        try:
            con.rollback()
        except sqlite3.Error:
            pass


_rpt_html_before_s837 = rpt_html


def rpt_html(con):                                            # noqa: F811 -- S837: the strip names each kind; the register asks; Shavez's switch
    try:
        reg_ensure(con)
        cut = _ts19((now_ist() - dt.timedelta(days=RPT_SHOW_CLOSED_DAYS)).isoformat(sep=" "))
        rows = con.execute("SELECT id, kind, item, day_from, day_to, why, asked_by, asked_at, closed_at FROM marg_watch_report "
                           "WHERE closed_at IS NULL OR closed_at >= ? ORDER BY (closed_at IS NULL) DESC, id DESC", (cut,)).fetchall()
        on = reg_shavez(con)
        n = rpt_cluster(con)
        h = ['<div class="closep" style="margin:0 0 12px;border-color:#b2ccff;background:#f8faff"><b>Reports asked for</b> '
             '<span class="note">— each closes itself when the file arrives; the rows are judged again · <a href="%s">Your list of reports to take ›</a></span>' % REG_TAKE]
        if rows:
            h.append('<table class="btab" style="margin-top:8px"><tbody><tr class="hd"><th>Report</th><th>Dates</th><th>Why</th><th>Asked</th><th>State</th></tr>')
            for rid, kind, item, fr, to, why, by, at, cl in rows:
                when = dmon(str(at)[:10]) + " " + str(at)[11:16]
                days = dmon(fr) if fr == to else "%s – %s" % (dmon(fr), dmon(to))
                if kind == "REGISTER":
                    rep, days = "Stock Register", "%s<br><span class=\"note\">%s</span>" % (esc(item or ""), esc(days))
                    st = ('<span class="st ans">Arrived %s ✓</span>' % esc(dmon(str(cl)[:10]) + " " + str(cl)[11:16])) if cl else \
                         ('<span class="st late">On your list%s</span>' % (" and Shavez's page" if on else ""))
                else:
                    rep, days = "Sale (Detail)", esc(days)
                    st = ('<span class="st ans">Arrived %s ✓</span>' % esc(dmon(str(cl)[:10]) + " " + str(cl)[11:16])) if cl else \
                         '<span class="st late">On Shavez\'s page</span>'
                h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s<br><span class="note">%s</span></td><td>%s</td></tr>'
                         % (rep, days, esc(why or ""), "by itself" if by == "auto" else "you", esc(when), st))
            h.append("</tbody></table>")
        else:
            h.append('<p class="note" style="margin:6px 0 0">None asked yet.</p>')
        h.append('<div class="askrow" style="margin:8px 0 0"><label for="rcluster">Ask by itself when</label><input id="rcluster" type="text" '
                 'inputmode="numeric" maxlength="2" value="%d" style="width:50px" aria-label="Items rising together"><span>or more items rise on one '
                 'closing with no record.</span><button type="button" onclick="mwRCluster(this)">Save</button><span class="msg"></span></div>' % n)
        h.append(reg_switch_html(con))
        h.append("</div>")
        return "".join(h)
    except Exception:                                         # noqa: BLE001
        return _rpt_html_before_s837(con)


def reg_switch_html(con):
    on = reg_shavez(con)
    return ('<div class="askrow" style="margin:8px 0 0"><span><b>Stock Register asks — Shavez:</b> %s</span>'
            '<button type="button" data-on="%d" onclick="mwRegShavez(this)">%s</button><span class="msg"></span>'
            '<span class="note">%s</span></div>'
            % ("ON — they also show on his Aaj ki reports" if on else "OFF — they stay with you only",
               0 if on else 1, "Turn Shavez off" if on else "Turn Shavez on",
               "" if on else "Turn him on once Ram Singh has added Stock Register to his REPORT login in Marg."))


REG_JS = r"""
function mwRegAsk(b){mwPost('/api/register/ask',{row:parseInt(b.getAttribute('data-h'),10)},b.parentNode.querySelector('.msg'));}
function mwRegShavez(b){mwPost('/api/register/shavez',{on:b.getAttribute('data-on')==='1'},b.parentNode.querySelector('.msg'));}
"""

_page_html_before_s837 = page_html


def page_html(con):                                           # noqa: F811 -- S837: the two buttons' script
    p = _page_html_before_s837(con)
    if p.count("</body></html>") == 1:
        return p.replace("</body></html>", "<script>%s</script></body></html>" % REG_JS)
    return p


def reg_page_html(con):
    """His list: the Stock Registers to take, how, the switch for Shavez, ask for any item, and what has arrived."""
    reg_ensure(con)
    con.commit()
    reg_sync(con)
    op = [a for a in reg_open(con) if not a["arrived"]]
    cut = _ts19((now_ist() - dt.timedelta(days=REG_SHOW_DAYS)).isoformat(sep=" "))
    done = _reg_rows(con, "AND closed_at IS NOT NULL AND closed_at >= ?", (cut,))
    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>Marg reports to take</title><style>%s</style></head><body><div class="wrap">' % CSS]
    h.append('<a class="back" href="/finance/approvals">← Sanjeevni Hub</a> <a class="back" href="%s">Marg watch</a>' % PAGE)
    h.append('<h1>Marg reports for you to take</h1><p class="sub">Marg\'s <b>Stock Register</b> for one item lists every entry Marg holds for it — '
             'sale, purchase, issue, receive, return — with the running balance. Take it from your own Marg login; the file comes here by itself '
             'and the Marg watch reads it (no patient name is kept).</p>')
    h.append('<div class="card"><h2>To take <small>%d</small></h2>' % len(op))
    if op:
        h.append('<table class="btab" style="min-width:0"><tbody><tr class="hd"><th>Item</th><th>From</th><th>To</th><th>Why</th><th>Asked</th></tr>')
        for a in op:
            h.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                     % (esc(a["item"]), esc(dmon(a["day_from"], True)), esc(dmon(a["day_to"], True)), esc(a["why"] or ""),
                        esc(dmon(str(a["asked_at"])[:10]) + " " + str(a["asked_at"])[11:16])))
        h.append('</tbody></table><p class="note" style="margin:10px 0 0"><b>In Marg:</b> the Stock Register for the item · store <b>WHOLE</b> · '
                 'From and To as above · view it · <b>Save</b> (F3) as text, as you save the other reports. The line leaves this list by itself '
                 'when the file has been read.</p>')
    else:
        h.append('<p class="lead" style="margin:0">Nothing to take.</p>')
    h.append(reg_switch_html(con) + "</div>")
    h.append('<div class="card"><h2>Ask for an item</h2><div class="askrow"><input id="ritem" list="ritems" type="text" maxlength="60" '
             'placeholder="Item, as Marg names it" style="min-width:260px" aria-label="Item"><label>From <input id="rfr" type="date"></label>'
             '<label>To <input id="rto" type="date"></label><button type="button" class="pri" onclick="regAskItem(this)">Ask</button>'
             '<span class="msg"></span></div><datalist id="ritems">%s</datalist></div>' % "".join(
                 '<option value="%s">' % esc(n) for n in _reg_names(con)))
    h.append('<div class="card"><h2>Arrived <small>last %d days</small></h2>' % REG_SHOW_DAYS)
    shown = 0
    regs = _reg_all(con)
    for a in reversed(done):
        g = reg_find(con, a["item"], a["day_from"], a["day_to"], regs, need_ok=True)
        if not g:
            continue
        shown += 1
        V = dict(kind="shown", note="%d entr%s; %s" % (len(g["lines"]), "y" if len(g["lines"]) == 1 else "ies",
                                                       ("%d balance step%s with no entry behind it" % (g["n_jumps"], "" if g["n_jumps"] == 1 else "s"))
                                                       if g.get("n_jumps") else "every balance step has its entry"),
                 reg=g, lo=_day(a["day_from"], -1), hi=a["day_to"])
        h.append(reg_table(V))
    if not shown:
        h.append('<p class="lead" style="margin:0">None in the last %d days.</p>' % REG_SHOW_DAYS)
    h.append("</div>")
    h.append('<script>var MW=%s;function mwPost(path,data,m){if(m)m.textContent="Saving…";fetch(MW+path,{method:"POST",credentials:"same-origin",'
             'headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}).then(function(r){return r.json();}).then(function(j){'
             'if(!j.ok){if(m)m.textContent=j.message||"Not saved.";return;}location.reload();}).catch(function(){if(m)m.textContent='
             '"Not saved — the network did not answer. Try again.";});}%s'
             'function regAskItem(b){var r=b.parentNode;mwPost("/api/register/ask",{item:r.querySelector("#ritem").value,'
             'from:r.querySelector("#rfr").value,to:r.querySelector("#rto").value},r.querySelector(".msg"));}</script>' % (json.dumps(PAGE), REG_JS))
    h.append("</div></body></html>")
    return "".join(h)


def _reg_names(con):
    """The item names for his ask box: the stock record's items, else the moves' items. Never raises."""
    try:
        sp = sqlite3.connect("file:%s?mode=ro" % _H().SPINE_DB, uri=True, timeout=10)
        try:
            return [str(r[0]) for r in sp.execute("SELECT DISTINCT name FROM sp_item WHERE COALESCE(name,'') <> '' ORDER BY name LIMIT 20000")]
        finally:
            sp.close()
    except Exception:                                         # noqa: BLE001
        try:
            return [str(r[0]) for r in con.execute("SELECT DISTINCT item FROM marg_hand_change ORDER BY item")]
        except sqlite3.Error:
            return []


_mount_before_s837 = _mount


def _mount():                                                 # noqa: F811 -- S837: his list page and its three doors
    from flask import jsonify, request                       # noqa: PLC0415
    bp = _mount_before_s837()

    def _doc():
        return _require("checker")

    @bp.route(REG_TAKE)
    def s837_take():
        u, err = _doc()
        if err:
            return err
        return reg_page_html(_db()), 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}

    @bp.route(PAGE + "/api/register/ask", methods=["POST"])
    def s837_ask():
        u, err = _doc()
        if err:
            return err
        con, b = _db(), (request.get_json(silent=True) or {})
        who = str(u.get("user") or "owner")
        if b.get("row") is not None:
            try:
                rid = int(b.get("row"))
            except (TypeError, ValueError):
                return jsonify(ok=False, message="Which row?"), 400
            ok, msg, code = reg_ask_row(con, who, rid)
        else:
            ok, msg, code = reg_ask_item(con, who, str(b.get("item") or ""), str(b.get("from") or ""), str(b.get("to") or ""))
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/register/shavez", methods=["POST"])
    def s837_shavez():
        u, err = _doc()
        if err:
            return err
        b = request.get_json(silent=True) or {}
        if not isinstance(b.get("on"), bool):
            return jsonify(ok=False, message="On or off?"), 400
        ok, msg, code = reg_set_shavez(_db(), str(u.get("user") or "owner"), b["on"])
        return jsonify(ok=ok, message=msg), code

    @bp.route(PAGE + "/api/register/count")
    def s837_count():
        u, err = _doc()
        if err:
            return err
        n, title = reg_count(_db())
        return jsonify(ok=True, n=n, title=title)

    return bp


_hand_html_before_s837 = _hand_html


def _hand_html(con):                                          # noqa: F811 -- S837: the row button knows where an ask goes
    global _REG_SH
    try:
        _REG_SH = reg_shavez(con)
    except Exception:                                         # noqa: BLE001
        _REG_SH = False
    return _hand_html_before_s837(con)


_REG_SH = False
# ---- S837 end ------------------------------------------------------------------------------------------------------------------------------

