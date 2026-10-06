def has_slip(st, res):
    """D681: a salary slip is printed only for a person with a running instalment loan on the
    common sheet (a loan line that was cut this month, or still has a balance). Money that comes
    back in ONE salary -- an advance booked against next month -- is not an instalment loan."""
    v = _views_of(st, res)
    return any((L["cut"] > 0.005 or L["balance_after"] > 0.005) and L["n_all"] != 1 for L in v["loans"])


def slip_html(st, res, cap):
    """One printed page for one person: the salary slip, in the wording staff read (Roman Hindi),
    with the advance shown as it is made up -- this month's advances, each loan's instalment and
    what is still owed. Reads only what the month already computed; decides nothing.
    For a private-loan person these are the COMMON-sheet figures (D682): the long-term loan is
    not on this page."""
    e = html.escape
    ym = res["ym"]
    closed = bool(res.get("ledger_closed", False))
    nm = str(st["name"])
    v = _views_of(st, res)
    di = round(float(st.get("dress_rs", 0)) + float(st.get("icard_rs", 0)), 2)
    fines = round(float(st.get("fine_uninf", 0)) + float(st.get("fine_exc", 0)), 2)
    leaves = st.get("leaves_total", 0)
    wtd = st.get("leaves_weighted", leaves)
    offs = st.get("offs", 0)
    charged = round(float(wtd) - float(offs), 2)

    def row(label, work, amount, cls=""):
        return ("<tr%s><td>%s%s</td><td class='n'>%s</td></tr>"
                % ((" class='%s'" % cls) if cls else "", e(label),
                   ("<br><span class='wk'>%s</span>" % e(work)) if work else "",
                   inr(amount)))

    o = ['<div class="s4pg slip" style="page-break-before:always">',
         _clinic_hdr("SALARY SLIP — %s — %s" % (nm.upper(), month_words(ym)), cap),
         "<div class='tw'><table class='ownt'>",
         "<tr><th>Vivran</th><th>Rs.</th></tr>",
         row("Salary", "", st["base"]),
         "<tr class='sec'><td colspan='2'>Kaate gaye</td></tr>"]
    if leaves or st.get("leave_amt"):
        # a short-shift day (a Sunday) counts as less than a full day: say what the days were counted as
        gine = ("%s din gine gaye · " % money(wtd)) if abs(float(wtd) - float(leaves)) > 0.005 else ""
        if charged >= 0:
            o.append(row("Chhutti — %s din" % money(leaves),
                         "%s%s din free · %s din ka paisa kata" % (gine, money(offs), money(charged)),
                         st["leave_amt"]))
        else:
            o.append(row("Chhutti — %s din" % money(leaves),
                         "%s%s din free · %s din bache, paisa joda" % (gine, money(offs), money(-charged)),
                         st["leave_amt"]))
    if st.get("late_min") or st.get("collect"):
        o.append(row("Late — %s minute, %s mark" % (money(st["late_min"]), money(st["marks"])),
                     "is mahine ka", st["collect"]))
    if st.get("prior_collect"):
        o.append(row("Pichhle mahine ka late", "jo roka gaya tha", st["prior_collect"]))
    if di:
        o.append(row("Dress aur I-card — %s + %s din"
                     % (money(st.get("dress_days", 0)), money(st.get("icard_days", 0))), "", di))
    if fines:
        o.append(row("Anya jurmana", "", fines))
    adv = round(sum(a["cut"] for a in v["month_adv"]), 2)
    if v["month_adv"]:
        o.append(row("Is mahine ka advance",
                     " + ".join("%s %s" % (_d_short(a["date"]), inr(a["cut"])) for a in v["month_adv"]),
                     adv, "new"))
    for L in v["loans"]:
        if L["cut"] <= 0.005:
            continue
        o.append(row("Loan ki kist",
                     "kist %d / %d · loan Rs %s (%s)" % (L["n_paid"] + (0 if closed else 1), L["n_all"],
                                                         inr(L["amount"]), L["given"]),
                     L["cut"], "new"))
    priv = st.get("priv") or {}
    if priv.get("extra"):
        o.append(row("Purana loan — ek aur kist", "", priv["extra"], "new"))
    if st.get("manual_adv"):
        o.append(row("Pehle diya advance", "", st["manual_adv"], "new"))
    o.append(row("Advance kata — kul", "upar ki advance wali lines ka jod · " + ("is mahine" if closed else "ledger band hone par katega"),
                 st.get("adv_ded", 0) if closed else adv + sum(L["cut"] for L in v["loans"]), "newtot"))
    if st.get("net_round_off"):                         # with the cuts, in every case: what is not paid in notes
        o.append(row("Round off — poore 10 rupaye", "", st["net_round_off"]))
    if st.get("duty_credits") or st.get("ot_paid"):
        o.append("<tr class='sec'><td colspan='2'>Joda gaya</td></tr>")
        if st.get("duty_credits"):
            o.append(row("Duty credit", "", st["duty_credits"]))
        if st.get("ot_paid"):
            o.append(row("Overtime", "", st["ot_paid"]))
    o.append("<tr class='net'><td><b>%s</b></td><td class='n'><b>%s</b></td></tr>"
             % ("Is mahine mila" if closed else "Is mahine mila — advance katne se PEHLE", inr(st["net"])))
    o.append("</table></div>")
    if not closed:
        o.append('<div class="ownwarn">Yeh slip abhi FINAL NAHI hai: is mahine ka ledger band nahi hua, '
                 'isliye advance aur kist abhi salary se nahi kate. Ledger band hone ke baad dobara nikalein.</div>')
    for L in v["loans"]:
        ahead = [(m, a) for m, a, k in L["strip"] if k == "due"]
        if L["balance_after"] <= 0.005 and not ahead:
            o.append('<div class="loanfoot"><b>Loan Rs %s (%s): poora ho gaya.</b></div>'
                     % (inr(L["amount"]), e(L["given"])))
        elif ahead:
            o.append('<div class="loanfoot"><b>Loan baaki: Rs %s</b> <span class="wk">(loan Rs %s, %s)</span><br>%s · %s mein khatam</div>'
                     % (inr(L["balance_after"]), inr(L["amount"]), e(L["given"]),
                        " · ".join("%s %s" % (MONTHS[int(m[5:7])], inr(a)) for m, a in ahead[:6])
                        + (" …" if len(ahead) > 6 else ""),
                        MONTHS[int(ahead[-1][0][5:7])] + (" " + ahead[-1][0][:4] if ahead[-1][0][:4] != ym[:4] else "")))
        else:
            o.append('<div class="loanfoot"><b>Loan baaki: Rs %s</b> <span class="wk">(loan Rs %s, %s)</span></div>'
                     % (inr(L["balance_after"]), inr(L["amount"]), e(L["given"])))
    if float(st["net"]) < 0:
        o.append('<div class="ownwarn">Is mahine advance, salary se Rs. %s zyada kata hai. '
                 'Matlab is mahine kuch nahi milega, aur Rs. %s agle mahine se adjust hoga.</div>'
                 % (inr(abs(float(st["net"]))), inr(abs(float(st["net"])))))
    o.append('<div class="sub">Mila / Received — hastakshar</div>'
             '<div style="height:44px;border-bottom:1px solid #444;max-width:320px"></div>')
    o.append("</div>")
    return "".join(o)


