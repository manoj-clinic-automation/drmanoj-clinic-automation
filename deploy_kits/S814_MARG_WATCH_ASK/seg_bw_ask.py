# ====================================================================== S814 -- Ask (plan v4 section 8; the owner's OK of 13-Nov 09:24 IST on the mock)
#  From a row he asks Amir (onto the one-time jobs card Amir already taps: amir_job kind 'ask'), or takes the text to copy / WhatsApp
#  (Darpan, Shavez -- Darpan's own card line follows with the duty map). The message starts at the matter (D927). The answer comes back
#  to the same row; only he closes it. Two days without an answer: amber. The answer notice to his phone ships OFF (ask.notice).
ASK_KIT = "S814_MARG_WATCH_ASK"
ASK_DDL = (
    "CREATE TABLE IF NOT EXISTS marg_watch_ask (id INTEGER PRIMARY KEY AUTOINCREMENT, to_whom TEXT NOT NULL, text_hi TEXT NOT NULL, codes TEXT NOT NULL, "
    "asked_by TEXT, asked_at TEXT NOT NULL, staff_ref TEXT, answer_kind TEXT, answer_line TEXT, answered_by TEXT, answered_at TEXT, told_at TEXT)",
    "CREATE TABLE IF NOT EXISTS marg_watch_ask_row (ask_id INTEGER NOT NULL, row_key TEXT NOT NULL, PRIMARY KEY (ask_id, row_key))",
    "CREATE INDEX IF NOT EXISTS marg_watch_ask_row_key ON marg_watch_ask_row (row_key, ask_id)",
)
ASK_ANS = {"fixed": "Marg mein theek kar diya", "right": "Sahi hai, galti nahi", "supplier": "Supplier ne bill badla", "unknown": "Pata nahi",
           "returned": "Grahak ne maal wapas kiya", "mistake": "Bill galti se bana tha"}
ASK_WHO = {"amir": "Amir", "darpan": "Darpan", "shavez": "Shavez"}
ASK_ON_CARD = ("amir",)                     # whose own card takes the question in this kit
ASK_AMBER_DAYS = 2


def _ts19(t):
    return str(t or "").replace("T", " ")[:19]


def ask_ensure(con):
    for s in ASK_DDL:
        con.execute(s)


def _ask_tables(con):
    return _table(con, "marg_watch_ask") and _table(con, "marg_watch_ask_row")


def ask_sync(con, commit=True):
    """Amir's answer, from his one-time jobs card (amir_job, kind 'ask'), into the ask's own row. Returns the number brought in.
    commit=False: the caller holds the transaction (the notice switch, S446 review M1)."""
    if not (_ask_tables(con) and _table(con, "amir_job")):
        return 0
    n = 0
    for aid, ref in con.execute("SELECT id, staff_ref FROM marg_watch_ask WHERE answered_at IS NULL AND staff_ref LIKE 'amir_job:%'").fetchall():
        try:
            jid = int(str(ref).split(":", 1)[1])
        except (ValueError, IndexError):
            continue
        r = con.execute("SELECT said_at, said_by, said_what FROM amir_job WHERE id=? AND kind='ask'", (jid,)).fetchone()
        if not r or not r[0]:
            continue
        what = str(r[2] or "")
        code, _s, line = what.partition("|")
        n += con.execute("UPDATE marg_watch_ask SET answer_kind=?, answer_line=?, answered_by=?, answered_at=? WHERE id=? AND answered_at IS NULL",
                         (code if code in ASK_ANS else "unknown", line.strip()[:300] or None, r[1], r[0], aid)).rowcount
    if n and commit:
        con.commit()
    return n


def ask_withdraw(con, known, still_open):
    """S446 review S6: a question still on Amir's card whose rows are ALL known here and NONE still open (the owner closed or settled them,
    or the move came to be explained) leaves his card as withdrawn. A row this view does not know keeps its question. Returns the number."""
    if not (_ask_tables(con) and _table(con, "amir_job")):
        return 0
    n = 0
    for aid, ref in con.execute("SELECT id, staff_ref FROM marg_watch_ask WHERE answered_at IS NULL AND staff_ref LIKE 'amir_job:%'").fetchall():
        ks = [r[0] for r in con.execute("SELECT row_key FROM marg_watch_ask_row WHERE ask_id=?", (aid,))]
        if not ks or any(k not in known or k in still_open for k in ks):
            continue
        try:
            jid = int(str(ref).split(":", 1)[1])
        except (ValueError, IndexError):
            continue
        n += con.execute("UPDATE amir_job SET done_at=?, done_how='withdrawn' WHERE id=? AND kind='ask' AND done_at IS NULL AND said_at IS NULL",
                         (now_iso()[:19], jid)).rowcount
    if n:
        con.commit()
    return n


def ask_state(con):
    """{row key: the newest ask covering it} -- dict(id, to, at, answered, kind, line, by, amber, card)."""
    out = {}
    if not _ask_tables(con):
        return out
    try:
        ask_sync(con)
    except sqlite3.Error:
        try:
            con.rollback()
        except sqlite3.Error:
            pass
    now = now_ist().replace(tzinfo=None)
    for key, aid, to, at, kind, line, by, ans_at, ref in con.execute(
            "SELECT r.row_key, a.id, a.to_whom, a.asked_at, a.answer_kind, a.answer_line, a.answered_by, a.answered_at, a.staff_ref "
            "FROM marg_watch_ask_row r JOIN marg_watch_ask a ON a.id = r.ask_id ORDER BY a.id"):
        prev = out.get(key)
        if prev and prev["answered"] and not ans_at:           # S446 review: an answer stays on the row; a later 'text taken' does not hide it
            continue
        try:
            age = (now - dt.datetime.fromisoformat(_ts19(at))).total_seconds() / 86400.0
        except ValueError:
            age = 0
        out[key] = dict(id=aid, to=to, at=at, answered=bool(ans_at), kind=kind, line=line, by=by, ans_at=ans_at, card=bool(ref),
                        amber=(not ans_at) and bool(ref) and age >= ASK_AMBER_DAYS)
    return out


def ask_chip(a):
    who = ASK_WHO.get(a["to"], a["to"])
    if a["answered"]:
        return '<span class="st ans">Answered · %s</span>' % esc(who)
    if not a["card"]:
        return '<span class="st">Text taken for %s · %s</span>' % (esc(who), esc(dmon(str(a["at"])[:10])))
    if a["amber"]:
        return '<span class="st late" style="color:#b54708;border-color:#fec84b;background:#fffaeb">Asked %s — no answer yet</span>' % esc(dmon(str(a["at"])[:10]))
    return '<span class="st" style="color:#1f5fbf;border-color:#b2ccff;background:#eef4ff">Asked · %s · %s</span>' % (esc(who), esc(dmon(str(a["at"])[:10])))


def ask_answer_html(a, put_right=None):
    if not a:
        return ""
    who = ASK_WHO.get(a["to"], a["to"])
    if not a["answered"]:
        if not a["card"]:
            return '<p class="note" style="margin:8px 0 0">The text was taken for %s on %s (copy or WhatsApp) — the answer does not come back here by itself.</p>' % (
                esc(who), esc(dmon(str(a["at"])[:10])))
        return '<p class="note" style="margin:8px 0 0">Asked %s on %s — on his card, no answer yet.%s</p>' % (
            esc(who), esc(dmon(str(a["at"])[:10])), " Two days or more without an answer." if a["amber"] else "")
    h = ['<div class="closep" style="margin-top:8px"><b>%s answered</b> <span class="note">%s</span> — “%s”%s' % (
        esc(who), esc(_ts19(a["ans_at"])[:16]), esc(ASK_ANS.get(a["kind"], a["kind"] or "")), (": <i>%s</i>" % esc(a["line"])) if a.get("line") else "")]
    if a["kind"] == "fixed" and put_right is not None:
        h.append('<p class="note" style="margin:6px 0 0">%s</p>' % ("Put right — a later closing shows Marg back where it was." if put_right
                                                                   else "Checked against the next closing: not seen yet. It shows here when Marg is back."))
    h.append("</div>")
    return "".join(h)


def _ask_lines_a(rows):
    H = _H()
    return ["%s — %s-%s: %s se %s (%s)" % (r["item"], dmon(r["day_from"]), dmon(r["day_to"]), H.num(r["marg_from"]), H.num(r["marg_to"]), H.snum(r["shift"]))
            for r in rows]


def _ask_text(kind, lines, to_whom, detail=""):
    """The Hindi (Roman letters) text -- it starts at the matter: no name, no 'ji' (D927)."""
    tail = "Apne card par jawab chuniye." if to_whom in ASK_ON_CARD else "Bataiye."
    if kind == "A":
        head = "Marg mein stock badla, par system mein iska koi bill, sale ya voucher nahi hai:"
        return "%s\n%s\nYeh kisne aur kyon badla? %s" % (head, "\n".join("%d. %s" % (i + 1, l) for i, l in enumerate(lines)), tail)
    return "%s\nYeh kisne aur kyon kiya? %s" % (detail, tail)


def _b_detail(f):
    who = " ".join(str(f["sup"]).split()).title()
    if f["side"] == "sale":
        if f["kind"] == "gone":
            return "Sale bill %s (%s) Marg se hata diya gaya — din ki report ke baad." % (f["no"], dmon(f["date"]))
        if f["kind"] == "late":
            return "Sale bill %s (%s) din ki report ke baad Marg mein chadhaya gaya." % (f["no"], dmon(f["date"]))
        return "Sale bill %s (%s) din ki report ke baad Marg mein badla gaya." % (f["no"], dmon(f["date"]))
    if f["kind"] == "gone":
        return "%s ka bill %s (%s) Marg se hata diya gaya — din ki report ke baad." % (who, f["no"], dmon(f["date"]))
    if f["kind"] == "late":
        return "%s ka bill %s (%s) bahut der se Marg mein chadhaya gaya." % (who, f["no"], dmon(f["date"]))
    return "%s ka bill %s (%s) din ki report ke baad Marg mein badla gaya." % (who, f["no"], dmon(f["date"]))


def _b_codes(f):
    if f["side"] == "sale" and f["kind"] == "gone":
        return ("returned", "mistake", "unknown")
    if f["side"] == "purchase":
        return ("fixed", "right", "supplier", "unknown")
    return ("fixed", "right", "unknown")


def _ask_box(keys_lines, kind, suggest, codes, detail=""):
    """The Ask box on a row: whom, the rows asked together (A), the message as it will go, and the three roads."""
    first = keys_lines[0][0]
    h = ['<div class="closep mwask" data-kind="%s" data-detail="%s" data-codes="%s" style="border-color:#b2ccff;background:#f8faff"><b>Ask</b>'
         % (kind, esc(detail), ",".join(codes))]
    h.append('<p class="note" style="margin:4px 0 2px">Whom</p>')
    for w, words in (("amir", "<b>Amir</b> — on his card (he keys purchases and vouchers in Marg)"),
                     ("darpan", "<b>Darpan</b> — the counter and the shelf · text to copy or WhatsApp"),
                     ("shavez", "<b>Shavez</b> — text to copy or WhatsApp")):
        h.append('<label><input type="radio" name="w%s" value="%s"%s onchange="mwAskText(this)"> %s%s</label>'
                 % (esc(first), w, " checked" if w == suggest else "", words, ' <span class="note">(suggested)</span>' if w == suggest else ""))
    if kind == "A" and len(keys_lines) > 1:
        h.append('<p class="note" style="margin:8px 0 2px">Ask about these together (other open moves of the same days)</p>')
    for x, (k, line) in enumerate(keys_lines):
        hide = "" if (kind == "A" and len(keys_lines) > 1) else ' style="display:none"'
        h.append('<label%s><input type="checkbox" class="mwk" value="%s" data-line="%s"%s onchange="mwAskText(this)"> %s</label>'
                 % (hide, esc(k), esc(line), " checked" if x == 0 else "", esc(line)))
    h.append('<p class="note" style="margin:8px 0 0">The message (it starts at the matter — no name, no "ji"):</p><pre class="mwtext" '
             'style="white-space:pre-wrap;background:#fff;border:1px dashed #b2ccff;border-radius:8px;padding:8px 10px;margin:6px 0"></pre>')
    h.append('<div class="askrow"><button type="button" class="pri mwcard" onclick="mwAskSend(this)">Put on Amir\'s card</button>'
             '<button type="button" onclick="mwAskCopy(this)">Copy the text</button><a class="mwwa" target="_blank" rel="noopener" href="#" '
             'onclick="return mwAskTaken(this)" style="padding:6px 10px;border:1px solid #d0d5dd;border-radius:8px;text-decoration:none">Open WhatsApp</a>'
             '<span class="msg"></span></div><p class="note" style="margin:4px 0 0">WhatsApp opens with the text and no number — you pick the chat.</p></div>')
    return "".join(h)


def ask_box_a(r, peers):
    """Section A: suggested Amir; the other open moves of the same closing can ride along."""
    if (r.get("act") or {}).get("action") == "close":         # S446 review S7: a row he closed is not asked about
        return ""
    rows = [r] + [p for p in peers if p["id"] != r["id"]]
    kl = [("hand:%d" % int(x["id"]), l) for x, l in zip(rows, _ask_lines_a(rows))]
    return _ask_box(kl, "A", "amir", ("fixed", "right", "unknown"))


def ask_box_b(f):
    """Section B: one bill. A removed sale bill is his own (D928): no one is suggested."""
    if f.get("status") in ("closed", "settled"):
        return ""
    suggest = "" if (f["side"] == "sale" and f["kind"] == "gone") else ("amir" if f["side"] == "purchase" else "darpan")
    return _ask_box([(f["fkey"], "%s %s" % (f["no"], dmon(f["date"])))], "B", suggest, _b_codes(f), _b_detail(f))


def _ask_attach(con, fs):
    try:
        S = ask_state(con)
    except Exception:                                         # noqa: BLE001 -- the page never waits for Ask
        S = {}
    for f in fs:
        f["ask"] = S.get(f["fkey"])
    try:                                                      # S446 review S6: a closed or settled bill's question leaves Amir's card
        ask_withdraw(con, {f["fkey"] for f in fs}, {f["fkey"] for f in fs if f["status"] not in ("closed", "settled")})
    except Exception:                                         # noqa: BLE001
        try:
            con.rollback()
        except sqlite3.Error:
            pass


@_hand_write
def ask_send(con, who, keys, to_whom, card=True):
    """(ok, message, http). He asks: the text is made HERE from the rows (never taken from the page); on Amir's card when card and to Amir;
    otherwise only recorded as 'text taken' (copy / WhatsApp), so the row says so."""
    ask_ensure(con)
    if to_whom not in ASK_WHO:
        return False, "Whom?", 400
    keys = list(dict.fromkeys(str(k) for k in (keys or []) if str(k)))
    if not keys:
        return False, "Which rows?", 400
    if len(keys) > 12:                                         # S446 review S4: never cut silently
        return False, "At most 12 rows in one question — untick some.", 400
    if card and to_whom in ASK_ON_CARD:                        # S446 review S3: one open question per row on his card
        q = ",".join("?" * len(keys))
        if con.execute("SELECT 1 FROM marg_watch_ask a JOIN marg_watch_ask_row r ON r.ask_id = a.id WHERE a.staff_ref IS NOT NULL "
                       "AND a.answered_at IS NULL AND r.row_key IN (%s) LIMIT 1" % q, keys).fetchone():
            return False, "Already on Amir's card — no answer yet.", 409
    if all(k.startswith("hand:") for k in keys):
        V = hand_view(con)
        live = {"hand:%d" % int(r["id"]): r for r in V["counted"]}
        if any(k not in live for k in keys):
            return False, "A row is no longer open — the page was out of date. Reload it.", 409
        rows = [live[k] for k in keys]
        text, codes = _ask_text("A", _ask_lines_a(rows), to_whom), ("fixed", "right", "unknown")
        subject = "Marg watch question: " + ", ".join(sorted({r["item"] for r in rows}))[:120]
    elif len(keys) == 1 and re.match(r"^[0-9a-f]{16}$", keys[0]):
        f = _find(con, keys[0])
        if f is None or f["status"] in ("closed", "settled"):
            return False, "This row is no longer open — the page was out of date. Reload it.", 409
        text, codes = _ask_text("B", [], to_whom, _b_detail(f)), _b_codes(f)
        subject = "Marg watch question: bill %s" % f["no"]
    else:
        return False, "Which rows?", 400
    ts = now_iso()
    cur = con.execute("INSERT INTO marg_watch_ask (to_whom, text_hi, codes, asked_by, asked_at) VALUES (?,?,?,?,?)",
                      (to_whom, text, ",".join(codes), who, ts))
    aid = cur.lastrowid
    for k in keys:
        con.execute("INSERT OR IGNORE INTO marg_watch_ask_row (ask_id, row_key) VALUES (?,?)", (aid, k))
    if card and to_whom in ASK_ON_CARD:
        if not _table(con, "amir_job"):
            con.rollback()
            return False, "Amir's card could not be reached just now — use Copy or WhatsApp.", 503
        j = con.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                        ("mwask:%d" % aid, "ask", subject, text, ",".join(codes), ts, who, ts))
        con.execute("UPDATE marg_watch_ask SET staff_ref=? WHERE id=?", ("amir_job:%d" % j.lastrowid, aid))
    _audit(con, who, "marg_watch_ask", "ask:%d" % aid, dict(to=to_whom, rows=keys, card=bool(card and to_whom in ASK_ON_CARD)))
    con.commit()
    return True, ("On %s's card." % ASK_WHO[to_whom]) if (card and to_whom in ASK_ON_CARD) else "Noted on the row.", 200


@_hand_write
def ask_set_notice(con, who, on):
    ts = now_iso()
    ask_ensure(con)
    if con.in_transaction:
        con.commit()
    con.execute("BEGIN IMMEDIATE")                             # S446 review M1: one transaction; the switch itself is written LAST
    if on:                                                     # every answer already back is marked as before the notice: never told
        ask_sync(con, commit=False)
        con.execute("UPDATE marg_watch_ask SET told_at='before the notice' WHERE answered_at IS NOT NULL AND told_at IS NULL")
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('ask.notice_from', ?, 'S814: the answer notice was turned on; earlier answers are not told')", (ts,))
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('ask.notice', ?, 'S814: a phone line when a staff answer comes back -- his switch on the Marg watch')",
                ("on" if on else "off",))
    _audit(con, who, "marg_watch_ask_notice", "", dict(on=bool(on)))
    con.commit()
    return True, "The answer notice is %s." % ("on" if on else "off"), 200


def ask_notice_html(con):
    on = setting(con, "ask.notice", "off").strip().lower() == "on"
    return ('<div class="askrow" style="margin:0 0 10px"><span>Phone line when a staff answer comes back: <b%s>%s</b></span>'
            '<button type="button" data-on="%s" onclick="mwAskNotice(this)">%s</button><span class="msg"></span></div>'
            % (' class="up"' if on else "", "On" if on else "Off", "0" if on else "1", "Turn off" if on else "Turn on"))


def ask_messages(con, now):
    """For owner_notice: answers that came back after he turned the notice on, not yet told. [dict(key, title, body)]."""
    if setting(con, "ask.notice", "off").strip().lower() != "on" or not _ask_tables(con):
        return []
    out = []                                                   # S446 review S8: READS ONLY -- an answer not yet synced is read from his card
    for aid, to, kind, line, at, ref in con.execute("SELECT id, to_whom, answer_kind, answer_line, answered_at, staff_ref FROM marg_watch_ask "
                                                     "WHERE told_at IS NULL AND (answered_at IS NOT NULL OR staff_ref LIKE 'amir_job:%') ORDER BY id").fetchall():
        if not at:                                             # no clock compared: two pages, two clocks
            try:
                j = con.execute("SELECT said_at, said_what FROM amir_job WHERE id=? AND kind='ask'", (int(str(ref).split(":", 1)[1]),)).fetchone()
            except (ValueError, IndexError):
                j = None
            if not j or not j[0]:
                continue
            code, _s, ln = str(j[1] or "").partition("|")
            kind, line = (code if code in ASK_ANS else "unknown"), (ln.strip()[:300] or None)
        n = con.execute("SELECT COUNT(*) FROM marg_watch_ask_row WHERE ask_id=?", (aid,)).fetchone()[0]
        out.append(dict(key="ask:%d" % aid, title="Marg watch: %s answered" % ASK_WHO.get(to, to),
                        body="“%s”%s — %d row%s. Marg watch." % (ASK_ANS.get(kind, kind or ""), (": " + line) if line else "", n, "" if n == 1 else "s")))
    return out


