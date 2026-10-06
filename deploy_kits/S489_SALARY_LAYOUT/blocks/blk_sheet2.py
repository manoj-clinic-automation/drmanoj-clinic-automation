_S489_CSS = ("<style>"
             ".chip{display:inline-block;border:1px solid #9aa5b4;border-radius:4px;padding:1px 8px;"
             "font-size:13.5px;margin:2px 5px 2px 0;white-space:nowrap;font-weight:600;background:#fff}"
             ".chip.paid{background:#dcf0dc;border-color:#3d8b3d;color:#14532d}"
             ".chip.now{background:#fff3d6;border-color:#c79a2a;color:#6b4a00}"
             ".chip.due{border-style:dashed;color:#333}"
             ".chip.skip,.chip.defer,.chip.hold{background:#fde8e8;border-color:#b55;color:#7a1f1f}"
             "tr.strip td{background:#fbfaf6;white-space:normal}"
             "th.n{text-align:right}"
             "tr.pfirst td{border-top:2px solid #6b6252}"
             "@media print{.s2sec table,table.lled{width:calc(100% - 2px) !important} .lfacts{padding-right:2px}"
             " .chip{font-size:10.5px;padding:0 5px}}"
             "tr.bear td{background:#13233b;color:#fff;border-color:#13233b}"
             ".lfacts{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0}"
             ".lfacts div.f{flex:1;min-width:150px;border:1px solid #b9b0a0;border-radius:8px;padding:8px 12px;background:#fff}"
             ".lfacts .l{font-size:12px;color:#555;text-transform:uppercase;letter-spacing:.05em}"
             ".lfacts .v{font-size:21px;font-weight:700}"
             ".lfacts .s{font-size:13px;color:#555}"
             "table.lled td,table.lled th{padding:8px 12px}"
             "table.lled tr.open td{background:#f0ede6;font-weight:700}"
             "table.lled tr.skip td{background:#fff8e1}"
             "table.lled tr.next td{color:#777;font-style:italic;font-weight:400}"
             "table.lled tr.tot td{background:#13233b;color:#fff;border-color:#13233b}"
             ".tag{display:inline-block;border:1px solid;border-radius:4px;padding:0 8px;font-size:13px;font-weight:700}"
             ".tag.pd{background:#dcf0dc;border-color:#3d8b3d;color:#14532d}"
             ".tag.sk{background:#fff3d6;border-color:#c79a2a;color:#6b4a00}"
             ".tag.du{background:#fff;border-color:#9aa5b4;border-style:dashed;color:#555;font-style:normal}"
             ".tag.no{background:#fde8e8;border-color:#b55;color:#7a1f1f}"
             ".signline{margin-top:26px;font-size:13px;color:#444}"
             ".signline span{display:inline-block;min-width:260px;border-bottom:1px solid #444;height:34px}"
             "</style>")

_STRIP_WORD = {"skip": "skipped", "defer": "deferred", "hold": "held"}


def _strip_html(loan):
    """The month strip of one loan: a chip per month, paid months ticked."""
    bits = []
    due = [m for m, _a, k in loan["strip"] if k == "due"]
    for m, a, k in loan["strip"]:
        if k == "paid":
            bits.append("<span class='chip paid'>%s %s &#10004;</span>" % (_m_short(m), inr(a)))
        elif k == "now":
            bits.append("<span class='chip now'>%s %s · this salary</span>" % (_m_short(m), inr(a)))
        elif k == "due":
            last = " · last" if (due and m == due[-1] and len(due) > 1) else ""
            bits.append("<span class='chip due'>%s %s%s</span>" % (_m_short(m), inr(a), last))
        else:
            bits.append("<span class='chip %s'>%s · %s</span>" % (k, _m_short(m), _STRIP_WORD.get(k, k)))
    return " ".join(bits)


def _views_of(st, res):
    v = st.get("views")
    if v is None:                                   # a result made by an older compute (never on the box)
        v = advance_views(st.get("ledger_money"), st["name"], res["ym"], bool(res.get("ledger_closed")),
                          loan_pages()["groups"],
                          private=str(st["name"]).strip().lower() in private_loan_names(res.get("settings")))
    return v


def advances_sections_html(res, pick, doors=False, ledger_prefix="/ledger"):
    """D681: the three advance tables of Sheet 2, for the staff in `pick`."""
    e = html.escape
    ym = res["ym"]
    closed = bool(res.get("ledger_closed", False))
    mw = month_words(ym)
    msal = MONTHS[int(ym[5:7])]
    out = []

    def door(st):
        return ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                % (ledger_prefix, e(st["name"]))) if doors else ""

    # ---- 1 · this month's advances -------------------------------------------------
    out.append("<section class='s2sec'><h2>1 · This month's advances — cut in full from this salary</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th>Date given</th><th class='n'>Amount</th>"
               "<th>Cut from</th><th class='noprint'></th></tr>")
    any_a = False
    for st in pick:
        v = _views_of(st, res)
        for i, a in enumerate(v["month_adv"]):
            any_a = True
            out.append("<tr%s><td>%s</td><td>%s</td><td class='n'>%s</td><td>%s</td><td class='noprint'>%s</td></tr>"
                       % (" class='pfirst'" if i == 0 else "", ("<b>%s</b>" % e(st["name"])) if i == 0 else "",
                          "brought forward" if a.get("bf") else e("%s %s" % (_d_short(a["date"]), str(a["date"])[:4])),
                          inr(a["amount"]),
                          ("%s salary" % msal) if closed else ("%s salary — at the ledger close" % msal),
                          door(st) if i == 0 else ""))
    if not any_a:
        out.append("<tr><td colspan='5'>none this month</td></tr>")
    out.append("</table></div><div class='sub'>Each of these is cut in full from this one salary."
               "</div></section>")

    # ---- 2 · instalment loans -------------------------------------------------------
    out.append("<section class='s2sec'><h2>2 · Instalment loans — one line per person, per loan</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th>Loan</th><th>Instalment</th>"
               "<th class='n'>Paid so far</th><th class='n'>Cut this month</th><th class='n'>Balance</th><th>Ends</th>"
               "<th class='noprint'></th></tr>")
    any_l = False
    n_late = 0
    for st in pick:
        v = _views_of(st, res)
        for i, L in enumerate(v["loans"]):
            any_l = True
            if L["balance_after"] <= 0.005 and not [1 for _m, _a, k in L["strip"] if k == "due"]:
                ends = "finished this month" if L["cut"] > 0.005 else "finished"
            elif L["ends"]:
                ends = e(month_words(L["ends"]))
            else:
                ends = "no recovery set — see the ledger"
            if L.get("late_month"):
                n_late += 1
                ends += " <small>· booked against a later month — check</small>"
            paid = ("%s<br><small>%d of %d</small>" % (inr(L["paid"]), L["n_paid"], L["n_all"])
                    if L["n_all"] else inr(L["paid"]))
            out.append("<tr%s><td>%s</td><td>Rs %s<br><small>given %s</small></td><td>%s</td>"
                       "<td class='n'>%s</td><td class='n'><b>%s</b></td><td class='n'><b>%s</b></td>"
                       "<td>%s</td><td class='noprint'>%s</td></tr>"
                       % (" class='pfirst'" if i == 0 else "", "<b>%s</b>" % e(st["name"]), inr(L["amount"]),
                          e(L["given"]), e(L["inst"]), paid,
                          inr(L["cut"]) if L["cut"] > 0.005 else "—",
                          inr(L["balance_after"] if not closed else L["balance"]), ends,
                          door(st) if i == 0 else ""))
            parts = ""
            if len(L["parts"]) > 1:
                parts = ("<div class='sub' style='margin:3px 0 0'>Handed over in %d parts: %s.</div>"
                         % (len(L["parts"]),
                            " · ".join("%s %s" % (_d_short(t["date"]), inr(t["amount"])) for t in L["parts"])))
            out.append("<tr class='strip'><td></td><td colspan='7'>%s%s</td></tr>" % (_strip_html(L), parts))
    if not any_l:
        out.append("<tr><td colspan='8'>no instalment loan is running</td></tr>")
    out.append("</table></div><div class='sub'>Money paid back over more than one salary. One line for the "
               "whole loan, however many parts it was handed over in. A ticked month is what the ledger took; "
               "the months ahead follow the ledger's own recovery rules, and a month skipped, deferred or held "
               "moves them later.</div></section>")

    # ---- 3 · what each salary bears -------------------------------------------------
    out.append("<section class='s2sec'><h2>3 · What each salary bears this month</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th class='n'>This month's advances</th><th class='n'>Loan instalment</th>"
               "<th class='n'>Cut from %s salary</th><th class='n'>Loan balance after</th><th class='n'>Next month's instalment</th></tr>" % e(msal))
    any_b = False
    odd = []
    for st in pick:
        v = _views_of(st, res)
        adv = round(sum(a["cut"] for a in v["month_adv"]), 2)
        loan = round(sum(L["cut"] for L in v["loans"]), 2)
        priv = st.get("priv") or {}
        extra = float(priv.get("extra") or 0.0)             # a second long-term instalment in one month
        man = float(st.get("manual_adv") or 0.0)
        total = round(adv + loan + extra + man, 2)
        bal = round(sum(L["balance_after"] for L in v["loans"]), 2)
        nxt = round(sum(L["next"] for L in v["loans"]), 2)
        if not (adv or loan or extra or man or bal):
            continue
        any_b = True
        if closed and abs(total - float(st.get("adv_ded") or 0.0)) > 0.5:
            odd.append(st["name"])
        dash = "—"
        out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td class='n'>%s</td>"
                   "<td class='n'><b>%s</b></td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                   % (e(st["name"]), inr(adv + man) if (adv or man) else dash,
                      inr(loan + extra) if (loan or extra) else dash, inr(total),
                      inr(bal) if bal > 0.005 else dash, inr(nxt) if nxt > 0.005 else dash))
    if not any_b:
        out.append("<tr><td colspan='6'>nothing is cut for advances this month</td></tr>")
    out.append("</table></div>")
    if odd:
        out.append("<div class='note'><b>Does not add up for %s:</b> the two columns do not make the Advance "
                   "figure on the salary sheet. Do not approve this sheet — read the ledger statement first.</div>"
                   % e(", ".join(odd)))
    if not closed:
        out.append("<div class='note'>The staff ledger is not closed for %s yet. The 'cut' figures above are what "
                   "the ledger close WILL take; they enter the salary only when it has run.</div>" % mw)
    if n_late:
        out.append("<div class='note'>%d advance%s above %s booked against a LATER month than the month it was "
                   "given and set to come back in one go. If that is a slip, correct it in the ledger (reverse it "
                   "and enter it again), then reload this sheet.</div>"
                   % (n_late, "" if n_late == 1 else "s", "is" if n_late == 1 else "are"))
    out.append("<div class='sub'>The first money column is table 1, the second is table 2; together they are "
               "the Advance figure on the salary sheet.</div></section>")
    return "".join(out)


def loan_page_html(res, staff, doors=False, ledger_prefix="/ledger", back=None, prefix="/register"):
    """D682: the PRIVATE page of a person with a long-term loan -- one loan-ledger table."""
    e = html.escape
    ym = res["ym"]
    closed = bool(res.get("ledger_closed", False))
    st = next((x for x in res["staff"] if str(x["name"]).strip().lower() == staff.strip().lower()), None)
    out = [_head("Loan %s" % ym), _nav(prefix, ym, "darpan"), _S489_CSS]
    nm = (st["name"] if st else staff)
    out.append(_clinic_hdr("%s — LOAN LEDGER — %s" % (nm.upper(), month_words(ym)), "PRIVATE"))
    if back:
        out.append('<div class="noprint"><a class="doorbtn back" href="%s">&larr; Back to the flow</a></div>' % e(back))
    out.append('<div class="noprint"><a class="doorbtn" href="javascript:window.print()">&#128424; Print / save as PDF</a></div>')
    v = _views_of(st, res) if st else {"priv_lines": []}
    priv = (st or {}).get("priv")
    lines = [t for t in v.get("priv_lines", [])
             if t["start"] > 0 or t["taken"] > 0 or t["end"] > 0 or t["recovered"] > 0 or t["interest"] > 0]
    if not st or not lines:
        if st and st.get("ledger_money") is None:
            out.append("<div class='note'>The staff ledger could not be read just now, so this page cannot be shown. "
                       "Reload it in a minute.</div>")
        else:
            out.append("<div class='note'>%s has no long-term loan open in %s.</div>" % (e(nm), month_words(ym)))
        out.append(_LOAN_PRINT_CSS + "</body></html>")
        return "".join(out)
    hist_all = loan_history(st["name"])
    main = next((t for t in lines if t["id"] == hist_all.get("loan_id")), lines[0])
    hist = hist_all if main["id"] == hist_all.get("loan_id") else {}
    rows, opening, note = loan_ledger(main, hist, ym, closed)
    done_ids = {t["id"] for t in ((st.get("ledger_money") or {}).get("cleared") or [])}
    if not note and not hist.get("pre") and main.get("bf") and hist_all.get("loan_id") not in done_ids:
        # (a record that belongs to a loan since paid off is not missing -- this is simply his next loan)
        note = ("The record of this loan's months before the ledger began (loan_pages.json) was not found, "
                "so this table starts where the ledger starts.")
    others = [t for t in lines if t["id"] != main["id"]]
    sib = {}                                        # what the ledger took, month by month, for his OTHER long-term lines
    for t in others:
        for m_, p_, i_ in t.get("hist", []):
            if p_ + i_ > 0.005:
                sib[m_] = round(sib.get(m_, 0.0) + p_ + i_, 2)
    # before the close, where this month's instalment WILL go is the ledger's own plan
    sib_plan = 0.0 if closed else round(sum(p_ + i_ for t in others for m_, p_, i_ in t.get("proj", []) if m_ == ym), 2)
    side = "interest-free part" if main.get("interest_loan") else "other loan"
    kind = "loan with interest" if main.get("interest_loan") else "interest-free loan"
    inst = float(main.get("inst") or 0.0)
    int_part = INTEREST_FLAT if main.get("interest_loan") else 0.0
    past_rows = [r for r in rows if r["status"] != "next"]
    first_ym = past_rows[0]["ym"] if past_rows else ym
    out.append("<div class='lfacts'>"
               "<div class='f'><div class='l'>Opening balance</div><div class='v'>%s</div><div class='s'>%s</div></div>"
               "<div class='f'><div class='l'>Instalment</div><div class='v'>%s a month</div><div class='s'>%s</div></div>"
               "<div class='f'><div class='l'>Balance now · this loan</div><div class='v'>%s</div><div class='s'>after the %s salary</div></div>"
               "</div>"
               % (inr(opening if opening is not None else main["amount"]),
                  e("as at %s" % _date_words(hist.get("opening_date")) if (hist.get("pre") and hist.get("opening_date"))
                    else "when it entered the ledger"),
                  inr(inst),
                  ("%s off the loan + %s interest" % (inr(inst - int_part), inr(int_part))) if int_part else "no interest",
                  inr(main["end"]), month_words(ym)))
    if note:
        out.append("<div class='note'><b>Check:</b> %s</div>" % e(note))
    out.append("<div class='tw'><table class='lled'><tr><th>Salary month</th><th class='n'>Balance at start</th>"
               "<th class='n'>Instalment cut</th><th class='n'>Interest</th><th class='n'>Off the loan</th>"
               "<th class='n'>Balance at end</th><th>Status</th></tr>")
    out.append("<tr class='open'><td colspan='5'>Opening balance — %s (%s)</td><td class='n'>%s</td><td></td></tr>"
               % (e(_date_words(hist.get("opening_date")) if (hist.get("pre") and hist.get("opening_date"))
                    else "the ledger's first entry"),
                  e(kind), inr(opening if opening is not None else main["amount"])))
    t_inst = t_int = t_pr = t_add = 0.0
    n_skip = 0
    # a month counts as skipped only when NOTHING was taken for his long-term loan in it: an instalment
    # the ledger moved onto his other long-term line (a defer on this loan alone) was still taken.
    fy_sk = [m_ for m_ in skips_in_fy(past_rows, ym)
             if sib.get(m_, 0.0) <= 0.005 and not (m_ == ym and sib_plan > 0.005)]
    next_html = ""
    for r in rows:
        dash = "—"
        if r["status"] == "next":
            next_html = ("<tr class='next'><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                         "<td class='n'>%s</td><td class='n'>%s</td><td><span class='tag du'>Next</span></td></tr>"
                         % (e("%s %s" % (_m_short(r["ym"]), r["ym"][:4])), inr(r["start"]), inr(r["inst"]),
                            inr(r["interest"]) if r["interest"] else dash, inr(r["principal"]), inr(r["end"])))
            continue
        t_inst += r["inst"]; t_int += r["interest"]; t_pr += r["principal"]; t_add += r["added"]
        if r["status"] in ("paid", "part"):
            tag = "<span class='tag pd'>%s</span>" % ("Paid" if r["status"] == "paid" else "Part paid")
            cls = ""
        elif r["status"] in ("skip", "defer", "hold", "none") and sib.get(r["ym"], 0.0) > 0.005:
            tag = ("<span class='tag du'>Not on this loan</span> <small>· Rs %s taken for the %s</small>"
                   % (inr(sib[r["ym"]]), side))
            cls = ""
        elif r["status"] in ("skip", "defer", "hold") and r["ym"] == ym and sib_plan > 0.005:
            tag = ("<span class='tag du'>Not on this loan</span> <small>· Rs %s will be taken for the %s "
                   "at the ledger close</small>" % (inr(sib_plan), side))
            cls = ""
        elif r["status"] in ("skip", "defer", "hold"):
            n_skip += 1
            word = {"skip": "Skipped", "defer": "Skipped", "hold": "Held"}[r["status"]]
            k = (fy_sk.index(r["ym"]) + 1) if r["ym"] in fy_sk else 0
            tag = "<span class='tag sk'>%s</span>%s" % (word, (" <small>%s</small>" % _nth_of_two(k)) if k else "")
            if r["ym"] == ym and priv and priv.get("paid"):
                tag += " <small>· Rs %s paid to him</small>" % inr(priv["paid"])
            cls = " class='skip'"
        elif r["status"] == "pending":
            tag = "<span class='tag du'>Waits for the ledger close</span>"
            cls = ""
        else:
            tag = "<span class='tag no'>Nothing collected</span>"
            if r["ym"] == ym and priv and priv.get("paid"):
                tag += " <small>· Rs %s paid to him</small>" % inr(priv["paid"])
            cls = " class='skip'"
        intr = inr(r["interest"]) if r["interest"] else dash
        if r["added"] > 0.005:
            intr = "%s <small>added to loan</small>" % inr(r["added"])
        elif r["added"] < -0.005:
            intr = "%s <small>taken off the loan</small>" % inr(-r["added"])
        out.append("<tr%s><td>%s</td><td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                   "<td class='n'>%s</td><td class='n'><b>%s</b></td><td style='white-space:nowrap'>%s</td></tr>"
                   % (cls, e("%s %s" % (_m_short(r["ym"]), r["ym"][:4])), inr(r["start"]),
                      inr(r["inst"]) if r["inst"] else dash, intr,
                      inr(r["principal"]) if r["principal"] else dash, inr(r["end"]), tag))
    out.append("<tr class='tot'><td>%s to %s</td><td></td><td class='n'>%s</td><td class='n'>%s</td>"
               "<td class='n'>%s</td><td class='n'>%s</td><td></td></tr>"
               % (e(_m_short(first_ym)), e(_m_short(ym)), inr(t_inst),
                  inr(t_int) + ((" <small>+ %s added</small>" % inr(t_add)) if t_add > 0.005 else ""),
                  inr(t_pr), inr(past_rows[-1]["end"] if past_rows else main["end"])))
    out.append(next_html)
    out.append("</table></div>")
    foot = []
    if priv:
        if priv.get("paid") is None:
            foot.append("%s: Rs %s is kept aside from the salary for this instalment; the ledger close has not run yet."
                        % (month_words(ym), inr(priv["kept"])))
        else:
            foot.append("%s: Rs %s kept aside from salary · Rs %s instalment taken · %s."
                        % (month_words(ym), inr(priv["kept"]), inr(priv["cut_shown"]),
                           ("Rs %s paid to him" % inr(priv["paid"])) if priv["paid"] > 0.005 else "nothing left to pay him"))
            if priv.get("extra"):
                foot.append("A further Rs %s was collected for this loan through the salary sheet this month."
                            % inr(priv["extra"]))
    for t in others:
        foot.append("%s of Rs %s: balance Rs %s — %s."
                    % ("Interest-free part" if not t.get("interest_loan") else "Second loan", inr(t["amount"]), inr(t["end"]),
                       "starts when this loan is finished" if (t["end"] >= t["amount"] - 0.005 and main["end"] > 0.005)
                       else "being paid back"))
    foot.append("Skipped this year (April to March): %s." % _nth_of_two(len(fy_sk)))
    out.append("<div class='sub' style='margin-top:8px'>%s</div>" % "<br>".join(e(x) for x in foot))
    if doors:
        out.append('<div class="note noprint"><b>Full picture doors:</b> '
                   '<a class="doorbtn" href="%s/statement?staff=%s">&#128220; Complete ledger statement</a> '
                   '<a class="doorbtn" href="%s/advances">&#128181; Advances page</a> '
                   '<a class="doorbtn" href="%s/perks">&#127873; Perks</a></div>'
                   % (e(ledger_prefix), e(st["name"]), e(ledger_prefix), e(ledger_prefix)))
    out.append("<div class='signline'>Dekha / Seen — hastakshar &nbsp; <span></span> &nbsp;&nbsp; Date &nbsp; "
               "<span style='min-width:120px'></span></div>")
    out.append(_LOAN_PRINT_CSS)
    out.append("</body></html>")
    return "".join(out)


_LOAN_PRINT_CSS = """<style>
 @page{size:A4 portrait;margin:12mm}
 @media print{
  body{margin:0;font-size:12px;line-height:1.35;background:#fff}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:13px;margin:0 0 4px}
  table.lled{width:100%} table.lled th,table.lled td{font-size:12px;padding:6px 8px}
  .lfacts .v{font-size:17px} .lfacts .s,.lfacts .l{font-size:10.5px}
  .sub{font-size:10.5px} .note{font-size:11px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>"""


def _nth_of_two(k):
    """'1 of 2', '2 of 2' -- and past two, just the count (the page does not pretend a third is 'of 2')."""
    return ("%d of 2" % k) if k <= 2 else ("%d this year" % k)


def _date_words(iso):
    """'2026-03-31' -> '31 March 2026'."""
    try:
        return "%d %s %s" % (int(iso[8:10]), MONTHS[int(iso[5:7])], iso[:4])
    except (ValueError, TypeError, IndexError):
        return str(iso or "")


def sheet2_html(res, doors=False, ledger_prefix="/ledger", back=None,
                staff=None, prefix="/register", approve_html=""):
    """Sheet 2 — money review. S489 (D681/D682): the main page carries EVERYONE's advances in two
    tables that never mix (this month's advances; instalment loans, one line per loan) and one closing
    line per person. staff=<a private-loan name> renders that person's private LOAN LEDGER page;
    staff=<anyone else> the same tables for that one person. No bottom totals (owner ruling)."""
    e = html.escape
    ym = res["ym"]
    if staff is not None and staff.strip().lower() in private_loan_names(res.get("settings")):
        return loan_page_html(res, staff, doors=doors, ledger_prefix=ledger_prefix, back=back, prefix=prefix)
    sep = set()                                     # S489: nobody is kept off the main money page any more

    def _has(st):
        v = _views_of(st, res)
        return bool(v["month_adv"] or v["loans"] or st.get("manual_adv") or (st.get("priv") or {}).get("extra"))
    pick = [st for st in res["staff"]
            if (staff is None and _has(st))
            or (staff is not None and st["name"].lower() == staff.lower())]
    title = ("SHEET 2 · %s — MONEY PAGE — %s" % (staff.upper(), month_words(ym))
             if staff else "SHEET 2 · ADVANCES, LOANS & HOLDS — %s" % month_words(ym))

    out = [_head("Money %s" % ym), _nav(prefix, ym, "s2"), _S489_CSS,
           _clinic_hdr(title)]
    if back:
        out.append('<div class="noprint"><a class="doorbtn back" href="%s">&larr; Back to the flow</a></div>' % e(back))
    if approve_html and staff is None:
        out.append('<div class="noprint">%s</div>' % approve_html)
    out.append(_banner(res))
    for n in res["notes"]:
        out.append('<div class="note">%s</div>' % e(n))

    out.append(advances_sections_html(res, pick, doors=doors, ledger_prefix=ledger_prefix))

    # S200/R7: the owner's own advance record for months settled OUTSIDE the
    # ledger (July 2026 and earlier). Display-only — already deducted when paid;
    # never touches NET. File: manual_advances_<ym>.json beside this engine.
    _madv = os.path.join(BASE, "manual_advances_%s.json" % ym)
    if staff is None and os.path.exists(_madv):
        try:
            with open(_madv, encoding="utf-8") as _f:
                _rows = json.load(_f)
        except Exception:
            _rows = []
        if _rows:
            out.append("<h2>Advances settled OUTSIDE the ledger (owner's record)</h2>"
                       "<div class='note'>These DEDUCT in this month's Advance column "
                       "(already handed over when the month was paid) — so the NET on "
                       "Sheets 3/4 is what remains to hand over.</div>"
                       "<div class='tw'><table><tr><th>Staff</th><th>Amount</th>"
                       "<th>Note</th></tr>")
            for _r in _rows:
                out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td>%s</td></tr>"
                           % (e(str(_r.get("staff", ""))), money(_r.get("amount") or 0),
                              e(str(_r.get("note", "")))))
            out.append("</table></div>")

    if staff:
        st = pick[0] if pick else None
        if st:
            out.append('<div class="note noprint"><b>Full picture doors:</b> '
                       '<a class="doorbtn" href="%s/statement?staff=%s">&#128220; Complete ledger statement</a> '
                       '<a class="doorbtn" href="%s/advances">&#128181; Advances page</a> '
                       '<a class="doorbtn" href="%s/perks">&#127873; Perks</a>'
                       '<br><small>The tables above show OPEN money only. PENDING advances '
                       '(e.g. one awaiting a signed application) appear on the Advances page, '
                       'and every perk/benefit ever paid is on the Perks page.</small></div>'
                       % (e(ledger_prefix), e(st["name"]), e(ledger_prefix), e(ledger_prefix)))
            out.append("<section class='s2sec'><h2>Duty credits this month</h2><div class='tw'><table>"
                       "<tr><th>Outstation nights</th><th>Outstation Rs</th>"
                       "<th>Extra duty Rs</th><th>Night duty Rs (ledger)</th></tr>"
                       "<tr><td class='n'>%d</td><td class='n'>%s</td>"
                       "<td class='n'>%s</td><td class='n'>%s</td></tr></table></div>"
                       % (int(st.get("outst_days", 0)),
                          money(st["outst_rs"]), money(st["extra_rs"]), money(st["night_rs"])))
            out.append("</section>")

