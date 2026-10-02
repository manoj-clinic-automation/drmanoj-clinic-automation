# ==========================================================================================================================================
# S452_AMIR_PANEL_FIXES (02-Oct-2026, F-687 and the owner's rulings of 02-Oct evening) -- the reception phone's key; NEFT for Amir.
#   * The setup page is the owner's and a checker's: a maker or viewer gets the login gate's refusal. The key shows to them EVERY time,
#     each showing audited (purchase_audit 'phone_token_shown': who, when). "Shown once" is retired: it handed the key to whoever opened
#     the page FIRST, and the page admitted every staff login (on 02-Oct 19:46 IST the first opener was Amir's login).
#   * s452_new_token(con): a new key, made by the install; the old one answers 401 from that moment. The key is never printed or logged.
#   * The page's first line, in Hindi: when the phone last asked the queue door, with which answer (200 / 401), how many messages wait.
#   * NEFT for Amir. A month's NEFT is CONFIRMED when the bank's SMS for it has been read (purchase_neft_event source 'sms', S405) or a
#     Yes Bank statement line confirms it (bank_line_id, S407) -- "bank ka kaam ho gaya, <dd-mm>" -- or when the owner has entered it
#     himself (source 'owner'; provisional counts) -- "payment <dd-mm> ko ho gaya (Doctor sahab ne darj kiya)". Before that nothing of the
#     month reaches him: no line, no sheet. After: one line and the paid NEFT sheet as a PDF (NEFT_paid_<yyyy-mm>.pdf; the rows of
#     packs.build_neft_paid_sheet, S408, and their total). No supplier names, no "baaki". Shavez's and the owner's pages keep theirs.
# ==========================================================================================================================================
S452_PHONE_KEY = "supplier_msg.phone_last"
S452_ACCESS_LOG = os.environ.get("FINANCE_ACCESS_LOG", "/root/finance/access.log")


def s452_new_token(con):
    """A new reception-phone key (the install's data step). Returns the key's LENGTH only."""
    ensure(con)
    tok = secrets.token_hex(24)
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                ("supplier_msg.phone_token", tok, "S452 (F-687) -- the reception phone's key, renewed at S452 because the old one was readable by "
                 "a staff login; shown to the owner / a checker on the setup page, every showing audited"))
    con.execute("UPDATE setting SET note=? WHERE key='supplier_msg.token_shown'",
                ("S452 -- retired: the key is shown to the owner / a checker each time, audited (the once-rule gave it to the first opener)",))
    try:
        _pa()._audit(con, "S452 install", "phone_token_renewed", "phone-setup", dict(kit="S452_AMIR_PANEL_FIXES", length=len(tok)))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return len(tok)


def _s452_phone_seen(con, code):
    """The queue door was asked: when, and with which answer (one settings row; rewritten at most once a minute per answer)."""
    try:
        old = _setting(con, S452_PHONE_KEY, "")
        at, _sp, c = str(old).partition(" ")
        if at and c == str(code) and _age_min(at) < 1:
            return
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (S452_PHONE_KEY, "%s %d" % (_iso(), int(code)), "S452 -- when the reception phone last asked the queue door, and the answer"))
        con.commit()
    except Exception:                                          # noqa: BLE001 -- the phone's door never fails for its own record
        pass


def _s452_phone_from_log():
    """Before S452 nothing recorded the phone's asks: the newest queue-door line of the app's access log -> (iso, code) or ('', '')."""
    try:
        with open(S452_ACCESS_LOG, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 4 * 1024 * 1024))
            tail = fh.read().decode("utf-8", "replace")
    except (IOError, OSError):
        return "", ""
    for ln in reversed(tail.splitlines()):
        if "/finance/api/supplier-msg/next" not in ln:
            continue
        m = re.search(r"\[(\d{2})/(\w{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})[^\]]*\]\s+\"[^\"]*\"\s+(\d{3})", ln)
        if not m:
            continue
        try:
            t = dt.datetime.strptime("%s %s %s %s:%s:%s" % m.groups()[:6], "%d %b %Y %H:%M:%S")
        except ValueError:
            continue
        return t.isoformat(), m.group(7)
    return "", ""


def _s452_phone_state_line(con):
    """The setup page's first line (Hindi): the phone's last ask, its answer, the messages waiting."""
    at, _sp, code = str(_setting(con, S452_PHONE_KEY, "")).partition(" ")
    if not at:
        at, code = _s452_phone_from_log()
    try:
        wait = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE status IN ('queued','failed') AND to_number IS NOT NULL").fetchone()[0])
    except Exception:                                          # noqa: BLE001
        wait = 0
    if at:
        try:
            when = dt.datetime.fromisoformat(at).strftime("%d-%m-%Y %H:%M")
        except ValueError:
            when = at
        ans = {"200": "200 (theek)", "401": "401 (galat key)"}.get(code, code or "?")
        txt = "Phone ne aakhri baar %s ko poocha — jawab %s · %d message intezaar mein" % (when, ans, wait)
    else:
        txt = "Phone ne abhi tak nahi poocha · %d message intezaar mein" % wait
    return '<div class="warn" id="s452phone" style="margin:0 0 12px"><b>%s</b></div>' % _esc(txt)


def _s452_token_shown(con, u):
    try:
        _pa()._audit(con, _who(u), "phone_token_shown", "phone-setup", dict(kit="S452"))
        con.commit()
    except Exception:                                          # noqa: BLE001
        pass


# ---------------------------------------------------------------- NEFT for Amir
def _s452_ddmm(iso):
    s = str(iso or "")[:10]
    return ("%s-%s" % (s[8:10], s[5:7])) if len(s) == 10 else s


def s452_neft_confirmed(con, month):
    """None until the month's NEFT is confirmed; then {month, kind 'bank' | 'owner', date}. Reads S405's / S407's rows only."""
    if not _good_month(month):
        return None
    ensure(con)
    ev = live_event(con, month)
    if not ev:
        return None
    if ev.get("source") == "sms":                              # S405: the bank's SMS, read by the system
        return dict(month=month, kind="bank", date=str(ev.get("sms_date") or ev.get("created_at") or "")[:10], event=ev["id"])
    try:
        bank, line, _d = bank_check(con, ev)                   # S407: a Yes Bank statement line confirms it
    except Exception:                                          # noqa: BLE001
        bank, line = None, None
    if bank == "confirmed" and line:
        return dict(month=month, kind="bank", date=str(line.get("txn_date") or "")[:10], event=ev["id"])
    if ev.get("source") == "owner":                            # S407: the owner's own "NEFT done" (provisional counts)
        return dict(month=month, kind="owner", date=str(ev.get("sms_date") or ev.get("created_at") or "")[:10], event=ev["id"])
    return None


def s452_amir_line(conf):
    m = _month_name(conf["month"])
    if conf["kind"] == "bank":
        return "NEFT %s — bank ka kaam ho gaya, %s" % (m, _s452_ddmm(conf["date"]))
    return "NEFT %s — payment %s ko ho gaya (Doctor sahab ne darj kiya)" % (m, _s452_ddmm(conf["date"]))


def s452_amir_card(con):
    """Amir's NEFT block, every step: per month with a live NEFT event of the last 45 days, one line and the PDF -- once confirmed."""
    ensure(con)
    since = (_now() - dt.timedelta(days=45)).isoformat()
    months = [r[0] for r in con.execute("SELECT month FROM purchase_neft_event WHERE kind<>'rejected' AND created_at>=? GROUP BY month "
                                        "ORDER BY month DESC LIMIT 3", (since,))]
    out = []
    for m in months:
        c = s452_neft_confirmed(con, m)
        if not c:
            continue
        out.append("<div class=line><span class=big>%s</span><p><a class='btn plain' href='/finance/amir/pack/%s/neft'>Paid NEFT sheet (PDF)</a></p></div>"
                   % (_esc(s452_amir_line(c)), _esc(m)))
    if not out:
        return ""
    return "<div class=card id=s452neft><h2>NEFT</h2>%s</div>" % "".join(out)


def s452_neft_rows(con, month):
    """The paid NEFT sheet's rows, exactly as packs.build_neft_paid_sheet (S408) writes them, with the payable in paise."""
    pa = _pa()
    _s, groups = pa._pay_rows(con, month)
    st = state(con, month)
    ev = st.get("event") or {}
    bank = st.get("bank_line") or {}
    rows = []
    for g in groups:
        paid = "paid" if (g["route"] == "NEFT" and ev) else ("cheque" if g["route"] != "NEFT" else "not yet")
        rows.append((g["name"], int(g["payable_p"]), g["route"], paid, _dmy(ev.get("date")) if (g["route"] == "NEFT" and ev) else "",
                     _dmy(bank.get("date")) if (g["route"] == "NEFT" and bank) else ""))
    return rows


def _s452_rs(p):
    """Paise -> '1,23,456.00' (Indian grouping)."""
    p = int(p or 0)
    neg, p = p < 0, abs(p)
    whole, paise = divmod(p, 100)
    v = str(whole)
    if len(v) > 3:
        head, tail = v[:-3], v[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        v = ",".join(parts) + "," + tail
    return ("-" if neg else "") + v + ".%02d" % paise


def s452_neft_pdf(con, month):
    """The paid NEFT sheet as an A4 PDF -- the same rows as the S408 sheet, then the total; Amir cannot change a PDF."""
    import clinic_day_pdf as cdp                               # noqa: PLC0415 -- the estate's dependency-free PDF writer
    rows = s452_neft_rows(con, month)
    p = cdp._PDF("NEFT paid %s" % month)
    xs = (40, 330, 345, 395, 445, 510)
    head = ("Vendor", "Payable Rs", "Route", "Paid", "NEFT date", "Bank date")

    def page(first):
        p.new_page()
        y = 800
        if first:
            p.text(40, y, "Sanjeevni Medicos -- paid NEFT sheet -- %s" % _month_name(month), 13, bold=True)
            y -= 16
            p.text(40, y, "Printed %s. The same rows as the paid NEFT sheet of the vendor payments." % _now().strftime("%d-%m-%Y %H:%M"), 8.5, gray=0.35)
            y -= 20
        for i, h in enumerate(head):
            p.text(xs[i], y, h, 9, bold=True, align=("r" if i == 1 else "l"))
        p.line(40, y - 4, 555, y - 4, 0.6)
        return y - 17

    y = page(True)
    tot = neft = 0
    for r in rows:
        if y < 70:
            y = page(False)
        p.text(xs[0], y, cdp._fit(str(r[0]), 9, 280), 9)
        p.text(xs[1], y, _s452_rs(r[1]), 9, align="r")
        for i in (2, 3, 4, 5):
            p.text(xs[i], y, str(r[i] or ""), 9)
        tot += r[1]
        neft += r[1] if r[2] == "NEFT" else 0
        y -= 14
    if y < 90:
        y = page(False)
    p.line(40, y + 8, 555, y + 8, 0.6)
    p.text(xs[0], y - 4, "Total (%d vendors)" % len(rows), 9.5, bold=True)
    p.text(xs[1], y - 4, _s452_rs(tot), 9.5, bold=True, align="r")
    p.text(xs[0], y - 20, "of which by NEFT", 9)
    p.text(xs[1], y - 20, _s452_rs(neft), 9, align="r")
    return p.build()


def s452_amir_neft_pdf(con, month):
    """Amir's NEFT route (/finance/amir/pack/<month>/neft, packs.py): the PDF once the month's NEFT is confirmed, else the login gate's
    refusal. He gets no .xlsx by this address."""
    from flask import Response                                 # noqa: PLC0415
    if not _good_month(month):
        return "bad month", 400
    if not s452_neft_confirmed(con, month):
        return jsonify(ok=False, error="not_permitted", message="Your login is not permitted to do this."), 403
    return Response(s452_neft_pdf(con, month), mimetype="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="NEFT_paid_%s.pdf"' % month, "Cache-Control": "no-store"})
# ---- S452_AMIR_PANEL_FIXES end ----------------------------------------------------------------------------------------------------------
