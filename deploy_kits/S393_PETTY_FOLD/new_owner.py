def _owner_html(con, u, msg):
    f = figures(con)
    today = _now().date()
    month = today.strftime("%Y-%m")
    out = []
    if msg:
        out.append("<div class='%s'>%s</div>" % ("bad" if msg in ("bad", "amount", "notyours", "openamount") else "ok", MSG_EN.get(msg, "")))
    st = availability(con, today.isoformat())
    pend = list(con.execute("SELECT * FROM petty_entry WHERE void_at='' AND confirm_at='' AND kind IN ('receive','loan_out') ORDER BY id"))
    # S393: the strip -- always on screen
    out.append("<div class='strip'><span>Bhati today: <b>%s</b></span><span>In hand <b>₹ %s</b></span>"
               "<span>Loan <b>₹ %s</b></span>%s</div>"
               % ({"yes": "Available", "no": "Not available"}.get(st, "Not marked yet"), _r(f["hand_p"]), _r(f["loan_p"]),
                  ("<span class='hot'>%d need your tap</span>" % len(pend)) if pend else ""))
    if pend:
        body = []
        for e in pend:
            mine = e["kind"] == "loan_out" or e["party"] == _who(u)
            act = ("<form method='post' action='/finance/petty/confirm/%d' class='inline'><button class='save' type='submit'>%s</button></form>"
                   % (e["id"], "OK" if e["kind"] == "loan_out" else "Yes, I gave it") if mine
                   else "<span class='mut'>for %s</span>" % dict(DOCTORS).get(e["party"], e["party"]))
            body.append("<tr><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td></tr>"
                        % (_human(e["entry_date"]), _esc(_party_label(con, e, "en")), _r(e["amount_p"]), act))
        out.append(_fold("Needs your tap", "%d · ₹&nbsp;%s" % (len(pend), _r(sum(int(e["amount_p"]) for e in pend))),
                         "<table class='grid'><tbody>%s</tbody></table>" % "".join(body)))
    # the three
    last_top = {}
    for h in _holders(con):
        if h["keeper"]:
            continue
        r = con.execute("SELECT * FROM petty_entry WHERE void_at='' AND kind='topup' AND party=? ORDER BY id DESC LIMIT 1",
                        (h["code"],)).fetchone()
        last_top[h["code"]] = r
    rows, summ = [], []
    for h in _holders(con):
        lc = con.execute("SELECT * FROM petty_count WHERE holder=? ORDER BY id DESC LIMIT 1", (h["code"],)).fetchone()
        counted = ("matched %s" % _human(lc["at"]) if lc and not lc["short_p"]
                   else ("short ₹ %s on %s" % (_r(lc["short_p"]), _human(lc["at"])) if lc else "never counted"))
        if h["keeper"]:
            state = "in hand ₹ %s%s" % (_r(f["hand_p"]), (" · needs ₹ %s" % _r(f["need_p"])) if f["need_p"] else "")
        else:
            t = last_top.get(h["code"])
            month_top = _sum(con, "kind='topup' AND party=? AND entry_date LIKE ?", (h["code"], month + "%"))
            state = ("last topped up %s (₹ %s) · this month ₹ %s" % (_human(t["entry_date"]), _r(t["amount_p"]), _r(month_top))
                     if t else "not topped up yet")
            summ.append("%s&nbsp;₹&nbsp;%s" % (_esc(h["name"]), _r(month_top)))
        form = ("<form method='post' action='/finance/petty/count' class='inline'><input type='hidden' name='holder' value='%s'>"
                "<input type='hidden' name='matches' value='1'><button class='save' type='submit'>Counted — matches</button></form>"
                "<form method='post' action='/finance/petty/count' class='inline'><input type='hidden' name='holder' value='%s'>"
                "<input class='amts' name='short' type='number' inputmode='decimal' min='1' step='any' placeholder='short ₹'>"
                "<button class='clear' type='submit'>Short</button></form>") % (h["code"], h["code"])
        rows.append("<tr><td><b>%s</b><br><span class='mut'>holds ₹ %s</span></td><td>%s<br><span class='mut'>%s</span></td></tr>"
                    "<tr><td colspan='2' class='acts'>%s</td></tr>"
                    % (_esc(h["name"]), _r(h["hold_p"]), state, counted, form))
    out.append(_fold("Diaries", " · ".join(summ),
                     "<table class='grid three'><tbody>%s</tbody></table>" % "".join(rows)))
    op = opening(con)

    def open_form(what, label, row):
        now = ("₹ %s <span class='mut'>· set by %s on %s</span>" % (_r(row["amount_p"]), _esc(row["by_whom"]), _human(row["at"]))
               if row else "<b>not set yet</b>")
        return ("<tr><td>%s</td><td>%s</td></tr><tr><td colspan='2' class='acts'><form method='post' action='/finance/petty/opening' class='inline'>"
                "<input type='hidden' name='what' value='%s'>"
                "<input class='amts' name='amount' type='number' inputmode='decimal' min='0' step='any' required placeholder='₹'>"
                "<button class='save' type='submit'>%s</button></form></td></tr>"
                % (label, now, what, "Correct" if row else "Save"))
    out.append(_fold("Bhati's cash", "₹&nbsp;%s" % _r(f["hand_p"]),
                     "<p class='bignum'>₹ %s in hand</p>"
                     "<p class='mut'>opening ₹ %s + received ₹ %s − diaries ₹ %s − payments ₹ %s − loans out + loans back</p>"
                     "<table class='grid'><tbody>%s</tbody></table>"
                     % (_r(f["hand_p"]), _r(f["open_cash_p"]), _r(f["received_p"]), _r(f["topup_p"]), _r(f["paid_p"]),
                        open_form("cash", "Opening cash<br><span class='mut'>held at the start</span>", op["cash"]))))
    out.append(_fold("Bhati's loan", "₹&nbsp;%s" % _r(f["loan_p"]),
                     "<p class='bignum'>₹ %s owed</p>"
                     "<p class='mut'>opening ₹ %s + loans taken − loans repaid</p>"
                     "<table class='grid'><tbody>%s</tbody></table>"
                     % (_r(f["loan_p"]), _r(f["open_loan_p"]),
                        open_form("loan", "Opening loan<br><span class='mut'>owed at the start</span>", op["loan"]))))
    body = []
    for p in _payees(con):
        tot = _sum(con, "kind='pay' AND party=?", (p["code"],))
        mt = _sum(con, "kind='pay' AND party=? AND entry_date LIKE ?", (p["code"], month + "%"))
        extra = (" · <b>%s</b>" % ("paid this month" if mt else "NOT paid this month")) if p["head"] == "monthly" else ""
        body.append("<tr><td>%s<br><span class='mut'>%s%s</span></td><td class='r'>%s</td><td class='r'><b>%s</b></td></tr>"
                    % (_esc(p["name"]), _esc(p["what_en"]), extra, _r(mt), _r(tot)))
    oth = _sum(con, "kind='pay' AND party='other'")
    body.append("<tr><td>Others (named on each entry)</td><td class='r'>%s</td><td class='r'><b>%s</b></td></tr>"
                % (_r(_sum(con, "kind='pay' AND party='other' AND entry_date LIKE ?", (month + "%",))), _r(oth)))
    out.append(_fold("Payments", "%s ₹&nbsp;%s" % (today.strftime("%b"), _r(_sum(con, "kind='pay' AND entry_date LIKE ?", (month + "%",)))),
                     "<table class='grid'><thead><tr><th>To</th><th class='r'>%s</th><th class='r'>All time</th></tr></thead>"
                     "<tbody>%s</tbody></table>" % (today.strftime("%b %Y"), "".join(body))))
    ents = list(con.execute("SELECT * FROM petty_entry WHERE entry_date LIKE ? ORDER BY id DESC", (month + "%",)))
    body = []
    for e in ents:
        ph = ("<a href='/finance/petty/photo/%d'>photo</a>" % e["id"]) if e["photo"] else ""
        state = ("cancelled by %s" % _esc(e["void_by"]) if e["void_at"] else
                 "<form method='post' action='/finance/petty/void/%d' class='inline'><button class='clear' type='submit'>Cancel</button></form>" % e["id"])
        conf = (" ✓ %s" % _esc(e["confirm_by"])) if e["confirm_at"] else ""
        body.append("<tr%s><td>%s</td><td>%s%s</td><td class='r'>%s</td><td>%s</td><td>%s</td></tr>"
                    % (" class='void'" if e["void_at"] else "", _human(e["entry_date"]), _esc(_party_label(con, e, "en")), conf,
                       _r(e["amount_p"]), ph, state))
    nv = len([e for e in ents if e["void_at"]])
    out.append(_fold("Entries — %s" % today.strftime("%b"),
                     "%d%s" % (len(ents) - nv, (" + %d cut" % nv) if nv else ""),
                     "<table class='grid'><tbody>%s</tbody></table>" % ("".join(body) or "<tr><td>None yet.</td></tr>")))
    out.append("<p class='mut'>Separate from Sanjeevni and clinic money: nothing here reaches either.</p>")
    return "".join(out)


