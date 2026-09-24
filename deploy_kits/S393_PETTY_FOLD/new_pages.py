def _fold(title, summ, body, is_open=False):
    """S393: one section of the book as a fold -- the title and its one-line figure always visible,
    the detail on a tap. name='pb' makes the folds an accordion without JavaScript: opening one
    closes the other, so the whole book stays on one screen."""
    return ("<details class='card fold' name='pb'%s><summary><span class='ft'>%s</span><span class='fs'>%s</span></summary>"
            "<div class='fb'>%s</div></details>" % (" open" if is_open else "", title, summ, body))


def _keeper_html(con, u, msg):
    f = figures(con)
    today = _now().date()
    tom = today + dt.timedelta(days=1)
    out = []
    if msg:
        out.append("<div class='%s'>%s</div>" % ("ok" if msg in ("saved", "cancelled") else "bad", MSG_HI.get(msg, "")))
    st_today = availability(con, today.isoformat())
    word = {"yes": "✓ Available", "no": "✗ Nahi"}.get(st_today, "abhi nahi bataya")
    # the strip: always on screen
    out.append("<div class='strip'><span>Haath mein <b>₹ %s</b></span><span>Loan <b>₹ %s</b></span><span>Aaj: <b>%s</b></span></div>%s"
               % (_r(f["hand_p"]), _r(f["loan_p"]), word,
                  ("<div class='bad'>Aapko <b>₹ %s</b> chahiye — Dr Manoj / Dr Bhawna se lijiye.</div>" % _r(f["need_p"]))
                  if f["need_p"] else ""))

    def avail_row(d, label):
        st = availability(con, d.isoformat())
        cur = {"yes": "✓ Available", "no": "✗ Nahi"}.get(st, "abhi nahi bataya")
        return ("<div class='availrow'><b>%s</b> <span class='pill'>%s</span>"
                "<form method='post' action='/finance/petty/available' class='inline'>"
                "<input type='hidden' name='day' value='%s'><input type='hidden' name='status' value='yes'>"
                "<button class='big yes' type='submit'>Available</button></form>"
                "<form method='post' action='/finance/petty/available' class='inline'>"
                "<input type='hidden' name='day' value='%s'><input type='hidden' name='status' value='no'>"
                "<button class='big no' type='submit'>Nahi aaunga</button></form></div>"
                % (label, cur, d.isoformat(), d.isoformat()))
    out.append(_fold("Aaj aayenge?", {"yes": "✓ haan", "no": "✗ nahi"}.get(st_today, "batayein"),
                     avail_row(today, "Aaj %s" % today.strftime("%d-%b")) + avail_row(tom, "Kal %s" % tom.strftime("%d-%b"))))
    out.append(_fold("Paise mile", "doctor se", "<div class='btns'>%s</div>"
                     % "".join("<a class='tile' href='/finance/petty/new/receive/%s'>%s se mile</a>" % (c, n) for c, n in DOCTORS)))
    hol = [h for h in _holders(con) if not h["keeper"]]
    out.append(_fold("Diary kami poori", "%d diary" % len(hol), "<div class='btns'>%s</div>"
                     % "".join("<a class='tile' href='/finance/petty/new/topup/%s'>%s<br><span class='sm'>₹ %s rehna chahiye</span></a>"
                               % (h["code"], _esc(h["name"]), _r(h["hold_p"])) for h in hol)))
    pay = _payees(con)
    month = today.strftime("%Y-%m")

    def paid_this_month(code):
        return _sum(con, "kind='pay' AND party=? AND entry_date LIKE ?", (code, month + "%"))
    cons = [p for p in pay if p["head"] == "construction"]
    mon = [p for p in pay if p["head"] == "monthly"]
    out.append(_fold("Renovation", "%d + koi aur" % len(cons), "<div class='btns'>%s"
                     "<a class='tile other' href='/finance/petty/new/pay/other'>Koi aur<br><span class='sm'>naam likhna hoga</span></a></div>"
                     % "".join("<a class='tile' href='/finance/petty/new/pay/%s'>%s<br><span class='sm'>%s</span></a>"
                               % (p["code"], _esc(p["name"]), _esc(p["what_hi"])) for p in cons)))
    out.append(_fold("Har mahine", " · ".join("%s: %s" % (_esc(p["name"]), "de diya" if paid_this_month(p["code"]) else "baaki")
                                              for p in mon) or "—",
                     "<div class='btns'>%s</div>"
                     % "".join("<a class='tile' href='/finance/petty/new/pay/%s'>%s<br><span class='sm'>%s · ₹ %s · %s</span></a>"
                               % (p["code"], _esc(p["name"]), _esc(p["what_hi"]), _r(p["default_p"]),
                                  ("is mahine de diya" if paid_this_month(p["code"]) else "is mahine baaki"))
                               for p in mon)))
    out.append(_fold("Apna loan", "₹&nbsp;%s" % _r(f["loan_p"]),
                     "<p class='bignum'>Baaki ₹ %s</p>%s<div class='btns'>"
                     "<a class='tile' href='/finance/petty/new/loan_out/self'>Loan liya</a>"
                     "<a class='tile' href='/finance/petty/new/loan_back/self'>Loan wapas kiya</a></div>"
                     % (_r(f["loan_p"]),
                        ("<p class='mut'>Purana loan (opening): ₹ %s — isme jud gaya hai</p>" % _r(f["open_loan_p"]))
                        if f["open_loan_set"] else "<p class='mut'>Purana loan (opening) abhi doctor ne nahi likha</p>")))
    out.append(_fold("Haath mein — hisaab", "₹&nbsp;%s" % _r(f["hand_p"]),
                     "<p class='bignum'>₹ %s</p><p class='mut'>Rehna chahiye ₹ %s</p>%s"
                     "<p class='mut'>opening ₹ %s + mile ₹ %s − diary ₹ %s − diye ₹ %s − loan liya + loan wapas</p>%s"
                     % (_r(f["hand_p"]), _r(f["hold_p"]),
                        ("<p class='bad'>Aapko <b>₹ %s</b> chahiye — Dr Manoj / Dr Bhawna se lijiye.</p>" % _r(f["need_p"]))
                        if f["need_p"] else "<p class='ok'>Poora hai.</p>",
                        _r(f["open_cash_p"]), _r(f["received_p"]), _r(f["topup_p"]), _r(f["paid_p"]),
                        ("<p class='mut'>Shuru mein aapke paas the (opening): ₹ %s — isme jud gaya hai</p>" % _r(f["open_cash_p"]))
                        if f["open_cash_set"] else "<p class='mut'>Opening abhi doctor ne nahi likha</p>")))
    since = (today - dt.timedelta(days=14)).isoformat()
    rows = _physio_rows(con, since)
    if rows:
        body = []
        for r in rows:
            act = ("✓ theek" if r["ok_by"] else
                   "<form method='post' action='/finance/petty/physio/%s' class='inline'><button class='save' type='submit'>Theek hai</button></form>"
                   % r["business_date"])
            body.append("<tr><td>%s</td><td class='r'>%s</td><td class='r'>%s</td><td>%s</td></tr>"
                        % (_human(r["business_date"]), _r(r["cash_p"]), _r(r["upi_p"]), act))
        left = len([r for r in rows if not r["ok_by"]])
        out.append(_fold("Physio entry", ("%d dekhni" % left) if left else "theek ✓",
                         "<table class='grid'><thead><tr><th>Din</th><th class='r'>Cash</th><th class='r'>UPI</th><th></th></tr></thead>"
                         "<tbody>%s</tbody></table>" % "".join(body)))
    recent = list(con.execute("SELECT * FROM petty_entry WHERE entry_date>=? ORDER BY id DESC LIMIT 30",
                              ((today - dt.timedelta(days=7)).isoformat(),)))
    if recent:
        body = []
        for e in recent:
            can = (not e["void_at"]) and e["by_whom"] == _who(u) and e["entry_date"] == _today()
            state = ("<s>cancel</s>" if e["void_at"] else
                     ("<form method='post' action='/finance/petty/void/%d' class='inline'><button class='clear' type='submit'>Galti — cancel</button></form>" % e["id"]
                      if can else ""))
            body.append("<tr%s><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td></tr>"
                        % (" class='void'" if e["void_at"] else "", _human(e["entry_date"]),
                           _esc(_party_label(con, e, "hi")), _r(e["amount_p"]), state))
        out.append(_fold("Pichhle 7 din", "%d" % len([e for e in recent if not e["void_at"]]),
                         "<table class='grid'><tbody>%s</tbody></table>" % "".join(body)))
    return "".join(out)


