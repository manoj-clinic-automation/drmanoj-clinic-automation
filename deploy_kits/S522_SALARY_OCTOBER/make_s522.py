#!/usr/bin/env python3
"""make_s522.py -- builds the two S522 files from their pinned FROM bytes by exact, counted edits.

    python3 -B make_s522.py <dir with staff_ledger.py + salary_policy.py at their FROM pins> <out dir>

Every anchor must occur exactly once; the new text is built in memory and written only when every
edit has applied (F-792). FROM pins: staff_ledger.py eacd7154..., salary_policy.py ac603874...
"""
import hashlib
import os
import sys

FROM = {"staff_ledger.py": "eacd71544715ff597712aee5e6233135",
        "salary_policy.py": "ac603874431a43bed278f7db45d2c0f9"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, old, new, name, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit("REFUSED: %s anchor '%s' found %d times (want 1)" % (name, label, n))
    return text.replace(old, new)


# =====================================================================================
#  staff_ledger.py
# =====================================================================================
L_EDITS = []

# L1 -- the free defers are counted in MONTHS, and a defer can say it is part of a skipped month
L_EDITS.append(("L1 record_defer signature",
"""def record_defer(users, checker, issue_id, month, reason, waive_penalty=False):
    \"\"\"DEFER one advance's collection for `month` (D332 §2.1). The instalment""",
"""def record_defer(users, checker, issue_id, month, reason, waive_penalty=False, skip_month=False):
    \"\"\"DEFER one advance's collection for `month` (D332 §2.1). The instalment"""))

L_EDITS.append(("L2 months not rows",
"""    used = fy_defers(issue["staff"], month, rows)
    penalty = bool(issue.get("interest")) and len(used) >= DEFERS_FREE_FY
    waived = bool(waive_penalty) and penalty""",
"""    used = fy_defers(issue["staff"], month, rows)
    # S522 (the owner, 06/11-Oct-2026): the free defers of a financial year are counted in
    # MONTHS, not rows -- a month skipped on two long-term lines at once is ONE of the two.
    used_m = sorted({r["date_from"] for r in used if r["date_from"] != month})
    penalty = bool(issue.get("interest")) and len(used_m) >= DEFERS_FREE_FY
    waived = bool(waive_penalty) and penalty"""))

L_EDITS.append(("L3 narration and the skip mark",
"""           "narration": (f"collection deferred for {month} ({fy_of(month)} "
                         f"{len(used)+1}) — {reason.strip()}"
""",
"""           "narration": ((f"MONTH SKIPPED — every long-term loan — {month} ({fy_of(month)} "
                          if skip_month else f"collection deferred for {month} ({fy_of(month)} ")
                         + f"{len(used_m)+1}) — {reason.strip()}"
"""))

L_EDITS.append(("L4 the row carries skip_month",
"""           "defer_penalty": penalty, "penalty_waived": waived}
    append_ledger(row)
    return row
""",
"""           "defer_penalty": penalty, "penalty_waived": waived,
           "skip_month": bool(skip_month)}
    append_ledger(row)
    return row


def fy_defer_months(staff, month, rows=None):
    \"\"\"S522: the MONTHS of the financial year of `month` in which this staff had any defer.\"\"\"
    return sorted({r["date_from"] for r in fy_defers(staff, month, rows)})


def skip_month_lines(staff, month, rows=None):
    \"\"\"S522: the long-term lines one 'skip a month' tap would stop for `month` -- every open
    advance of this staff that the close would otherwise collect from in that month, EXCEPT an
    advance that comes back in full from its own month's salary (the quota lane -- that is the
    month's own salary money, D331/SL4) and one that counts against a later month. A line already
    deferred for the month, or already collected at that month's close, is not offered again.\"\"\"
    rows = rows if rows is not None else load_ledger()
    mine = [a for a in open_advances() if a["issue"]["staff"] == staff]
    # a month already skipped the OLD way (LOAN_SKIP, D250) is left exactly as it was recorded: its
    # Rs 1000 is charged by the close only while the loan is in the waterfall (review of S522, item 2)
    if any(is_skipped(a["issue"]["id"], month, rows) for a in mine):
        return []
    out = []
    for a in mine:
        iid = a["issue"]["id"]
        if advance_lane(a) == "quota":
            continue
        if advance_against_month(a["issue"]) > month:
            continue
        if is_deferred(iid, month, rows):
            continue
        if any(r.get("closed_month") == month and r["category"] == "ADVANCE_INSTALMENT"
               and r["contra_of"] == iid for r in rows):
            continue
        # a scheduled advance is offered only when a step is actually due this month: a defer moves its
        # whole schedule, so deferring a month that owes nothing would push every later step for nothing
        if advance_lane(a) == "schedule":
            due = schedule_due_cum(a["issue"], month, rows)
            if not due or due - advance_recovered(iid, rows) <= 0:
                continue
        out.append(a)
    return out


def record_skip_month(users, checker, staff, month, reason, waive_penalty=False):
    \"\"\"S522 (the owner, 06-Oct-2026 -- a skipped loan month as ONE button that "should show in
    his related ledger everywhere"): stop collection for `month` on EVERY long-term line of one
    person at once, through the ledger's own DEFER (D332 §2.1 -- DEFER replaces SKIP as the
    owner's verb). Each line's schedule moves one month later; nothing is collected on any of them
    that month. It counts as ONE month of the year's two free defers; from the third month an
    interest-bearing loan carries the flat Rs 1000 penalty unless the owner waives it at the tap.
    The month and the person are checked before the first row is written; should a later line
    still refuse, the message says how many were skipped and the statement shows which.\"\"\"
    if users[checker]["role"] != "checker":
        raise PermissionError("only checkers skip a month")
    datetime.date.fromisoformat(month + "-01")
    if not (reason or "").strip():
        raise ValueError("a skipped month needs a written reason")
    import fcntl
    with open(_p("skip_month.lock"), "a") as _lk:     # one tap at a time: a second tap waits, then finds the lines done
        fcntl.flock(_lk, fcntl.LOCK_EX)
        rows = load_ledger()
        if any(r.get("closed_month") == month for r in rows):
            raise ValueError(f"{month} is already closed — a closed month cannot be skipped now")
        if any(is_skipped(a["issue"]["id"], month, rows) for a in open_advances() if a["issue"]["staff"] == staff):
            raise ValueError(f"{month} is already skipped for {staff} the old way (Rs {INTEREST_RS} added) — "
                             f"it is left as it was recorded")
        lines = skip_month_lines(staff, month, rows)
        if not lines:
            if any(r.get("category") == "ADVANCE_DEFER" and r.get("skip_month") and r.get("staff") == staff
                   and r.get("date_from") == month for r in rows):
                raise ValueError(f"{month} is already skipped for {staff}")
            raise ValueError(f"{staff} has no long-term loan to skip in {month}")
        out = []
        for a in lines:
            try:
                out.append(record_defer(users, checker, a["issue"]["id"], month, reason,
                                        waive_penalty=waive_penalty, skip_month=True))
            except (PermissionError, ValueError, OSError) as e:
                if out:
                    raise ValueError(f"only {len(out)} of {len(lines)} loans were skipped for {month} "
                                     f"before this stopped: {e} — read the statement") from e
                raise
        return out
"""))

# L5 -- the Advances page: the defer counter in months; the old Rs 1000 SKIP button is not offered
L_EDITS.append(("L5 defer counter in months",
"""            _usedd = fy_defers(a["issue"]["staff"], nxt)
            _pen = a["interest"] and len(_usedd) >= DEFERS_FREE_FY""",
"""            _usedd = [m_ for m_ in fy_defer_months(a["issue"]["staff"], nxt) if m_ != nxt]   # S522: months
            _pen = a["interest"] and len(_usedd) >= DEFERS_FREE_FY"""))

L_EDITS.append(("L6 the old skip button retired from the page",
"""            skiprow = ""
            if a["interest"]:
                used = fy_skips(a["issue"]["staff"], nxt)
                skiprow = (f"<br><small>skips used {fy_of(nxt)}: {len(used)}/{SKIPS_PER_FY}"
                           + (" (" + ", ".join(x["date_from"] for x in used) + ")" if used else "")
                           + "</small>"
                           f\"\"\"<form method="post" action="{URL_PREFIX}/skip" style="margin-top:4px">
                           <input type="hidden" name="id" value="{iid}">
                           <input type="month" name="month" value="{nxt}"
                                  style="width:auto"> <button class="no"
                           onclick="return confirm('Skip a loan month for {a['issue']['staff']}? '
                             + 'Nothing recovers and Rs {INTEREST_RS} capitalises onto the loan. '
                             + 'This cannot be undone by hand.')">Skip this month
                           (Rs {INTEREST_RS} capitalises)</button></form>\"\"\")
""",
"""            skiprow = ""      # S522: the old per-loan SKIP (Rs 1000 capitalised, D250) is no longer offered --
                              # the one button at the top of the person's block skips a month through DEFER
                              # (D332). The /skip route stays for the record and as a fallback.
"""))

L_EDITS.append(("L7 the one button, per person",
"""            inner = "".join(groups.get(_st, []))
            if pend.get(_st):""",
"""            inner = _skip_card(_st, nxt, _rows_all) + "".join(groups.get(_st, []))
            if pend.get(_st):"""))

L_EDITS.append(("L8 the card's builder, inside advances()",
"""        # pending advances (awaiting approval) + lifetime perks, per staff
        pend = {}""",
"""        _closed_all = closed_months(_rows_all)
        _skip_m = _month_plus(_closed_all[0], 1) if _closed_all else nxt   # the first month the ledger has not closed

        def _skip_card(staff_name, month, rows_):
            \"\"\"S522: ONE button that skips a month on every long-term loan of this person.\"\"\"
            month = _skip_m
            try:
                lines_ = skip_month_lines(staff_name, month, rows_)
            except Exception:                         # the page must never fall over for this card
                return ""
            if not lines_:
                return ""
            done_m = [m_ for m_ in fy_defer_months(staff_name, month, rows_) if m_ != month]
            has_int = any(x["interest"] for x in lines_)
            pen_ = has_int and len(done_m) >= DEFERS_FREE_FY
            names_ = " · ".join("Rs %s (%s)" % (x["issue"]["amount"], x["issue"]["date_from"]) for x in lines_)
            sname = html_esc(staff_name)
            return (f"<div class='card' style='margin:8px 0;border:2px solid #e0a93e'>"
                    f"<b>Skip a month — every long-term loan of {sname} at once</b><br>"
                    f"<small>Nothing is collected that month on: {names_}. Each one moves one month later. "
                    f"It shows as a skipped month on his loan page, Sheet 2, his slip and his statement.<br>"
                    f"Skipped this year ({fy_of(month)}): {len(done_m)} of {DEFERS_FREE_FY} free"
                    + (f" (" + ", ".join(done_m) + ")" if done_m else "")
                    + (f" — skipping {month} adds Rs {INTEREST_RS} to each loan with interest unless you waive it"
                       if pen_ else
                       (f"; from the third month each loan with interest carries Rs {INTEREST_RS} unless waived"
                        if has_int else ""))
                    + "</small>"
                    f"<form method='post' action='{URL_PREFIX}/skip-month' style='margin-top:6px'>"
                    f"<input type='hidden' name='staff' value='{sname}'>"
                    f"<input type='month' name='month' value='{month}' style='width:auto'> "
                    f"<input name='reason' placeholder='reason (required)' required> "
                    + (f"<label style='font-weight:normal'><input type='checkbox' name='waive' style='width:auto'> "
                       f"waive the Rs {INTEREST_RS} if this is the third skipped month of the year</label> " if has_int else "")
                    + "<button class='no' onclick=\\"return confirm('Skip this month on every long-term loan of this person? Nothing is collected on any of them and each moves one month later."
                    + (f" Rs {INTEREST_RS} is added to each loan with interest unless waive is ticked." if pen_ else "")
                    + "')\\">Skip this month — all his loans</button>"
                    f"</form></div>")
        # pending advances (awaiting approval) + lifetime perks, per staff
        pend = {}"""))

L_EDITS.append(("L9 the route",
"""    @app.route(URL_PREFIX + "/late-collect", methods=["POST"])""",
"""    @app.route(URL_PREFIX + "/skip-month", methods=["POST"])
    def skip_month_route():
        u, users = user()
        if not u: return redirect(URL_PREFIX + "/login")
        if users[u]["role"] != "checker": abort(403)
        try:
            record_skip_month(users, u, request.form["staff"].strip(), request.form["month"].strip(),
                              request.form.get("reason", ""), waive_penalty=("waive" in request.form))
        except (PermissionError, ValueError, KeyError) as e:
            return page("Advances", f"<p style='color:red'>NOT recorded: {html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/advances'>back to Advances</a></p>", u)
        return redirect(URL_PREFIX + "/advances")

    @app.route(URL_PREFIX + "/late-collect", methods=["POST"])"""))

# L10 -- the ledger's own selftest proves the skipped month
L_EDITS.append(("L10 selftest: one skipped month over two lines",
"""    # --- capacity (F-147): nothing recovers that the salary cannot bear -----""",
"""    # --- S522: ONE skipped month over every long-term line ------------------
    K1 = make_entry(users, "doc", "Kesh", "ADVANCE_ISSUE", "2029-04-03", "2029-04-03", 0,
                    "60000", "loan", instalment="6000", interest=True)
    K2 = make_entry(users, "doc", "Kesh", "ADVANCE_ISSUE", "2029-04-03", "2029-04-03", 0,
                    "30000", "interest-free part", instalment="6000")
    K3 = make_entry(users, "doc", "Kesh", "ADVANCE_ISSUE", "2029-05-02", "2029-05-02", 0,
                    "2000", "this month's advance", against_month="2029-05")
    ck(K3["status"] == "APPROVED" and len(skip_month_lines("Kesh", "2029-05")) == 2
       and K3["id"] not in [x["issue"]["id"] for x in skip_month_lines("Kesh", "2029-05")],
       "S522: both long-term lines are offered, the month's own advance is not")
    try:
        record_skip_month(users, "mfull", "Kesh", "2029-05", "x"); ck(False, "maker skip-month must fail")
    except PermissionError: ck(True, "S522: only a checker skips a month")
    try:
        record_skip_month(users, "doc", "Kesh", "2029-05", ""); ck(False, "no reason must fail")
    except ValueError: ck(True, "S522: a skipped month needs a reason")
    sk1 = record_skip_month(users, "doc", "Kesh", "2029-05", "family wedding")
    ck(len(sk1) == 2 and all(r["skip_month"] and r["category"] == "ADVANCE_DEFER" for r in sk1),
       "S522: one tap writes a skip-marked defer on each line")
    ck(not any(r["defer_penalty"] for r in sk1), "S522: the first skipped month is free")
    ck(fy_defer_months("Kesh", "2029-05") == ["2029-05"], "S522: two rows are ONE month of the year")
    try:
        record_skip_month(users, "doc", "Kesh", "2029-05", "again"); ck(False, "double skip-month must fail")
    except ValueError as _e2: ck("already skipped for Kesh" in str(_e2), "S522: a second tap says the month is already skipped")
    sk2 = record_skip_month(users, "doc", "Kesh", "2029-06", "second")
    ck(not any(r["defer_penalty"] for r in sk2), "S522: the second skipped month is free too")
    sk3 = record_skip_month(users, "doc", "Kesh", "2029-07", "third")
    ck([r["defer_penalty"] for r in sk3 if r["contra_of"] == K1["id"]] == [True]
       and [r["defer_penalty"] for r in sk3 if r["contra_of"] == K2["id"]] == [False],
       "S522: the third month carries the penalty on the loan with interest only")
    try:
        record_skip_month(users, "doc", "Nobody", "2029-05", "x"); ck(False, "no loan must fail")
    except ValueError: ck(True, "S522: a person with no long-term loan is refused")
    # review of S522, item 1: a scheduled advance with no step due in the month is not offered
    S1 = make_entry(users, "doc", "Sched", "ADVANCE_ISSUE", "2029-05-02", "", 0, "9000", "sched",
                    schedule="2029-07:3000, 2029-08:3000, 2029-09:3000")
    ck(S1["status"] == "APPROVED", "S522: the scheduled advance is approved")
    ck(not skip_month_lines("Sched", "2029-05") and [x["issue"]["id"] for x in skip_month_lines("Sched", "2029-07")] == [S1["id"]],
       "S522: a scheduled advance is offered only in a month a step is due")
    # review of S522, item 2: a month already skipped the old way is left as it was recorded
    O1 = make_entry(users, "doc", "Olds", "ADVANCE_ISSUE", "2029-04-03", "2029-04-03", 0,
                    "40000", "loan", instalment="5000", interest=True)
    record_skip(users, "doc", O1["id"], "2029-05")
    ck(skip_month_lines("Olds", "2029-05") == [], "S522: an old-style skip leaves nothing to offer for its month")
    try:
        record_skip_month(users, "doc", "Olds", "2029-05", "x"); ck(False, "old skip month must refuse")
    except ValueError: ck(True, "S522: a month already skipped the old way is refused")
    # --- capacity (F-147): nothing recovers that the salary cannot bear -----"""))


L_EDITS.append(("L11 selftest: the card and the route",
"""    ck(_rd.status_code in (301, 302, 303) and is_deferred(C["id"], "2028-03"),
       "SL6: the /defer route records the deferral")
""",
"""    ck(_rd.status_code in (301, 302, 303) and is_deferred(C["id"], "2028-03"),
       "SL6: the /defer route records the deferral")
    ck("Skip a month — every long-term loan of" in _pg6 and "Skip this month — all his loans" in _pg6
       and "capitalises)</button>" not in _pg6,
       "S522: the Advances page offers the one-button skip and no longer the old Rs 1000 skip")
    RQ = make_entry(users, "doc", "D'Souza", "ADVANCE_ISSUE", "2030-04-02", "2030-04-02", 0,
                    "12000", "loan", instalment="3000", interest=True)
    _pgq = _cl6.get(URL_PREFIX + "/advances").data.decode()
    ck("D&#x27;Souza" in _pgq and "confirm('Skip this month on every long-term loan of this person?" in _pgq,
       "S522: a name with an apostrophe never enters the confirm() script")
    ck(_pgq.count("unless waive is ticked.") == _pgq.count("to each loan with interest unless you waive it"),
       "S522: the confirm box names the Rs 1000 exactly where the card does")
    _rq = _cl6.post(URL_PREFIX + "/skip-month", data={"staff": "D'Souza", "month": "2030-05", "reason": "route skip"})
    ck(_rq.status_code in (301, 302, 303) and is_deferred(RQ["id"], "2030-05")
       and [r for r in load_ledger() if r["contra_of"] == RQ["id"] and r.get("skip_month")
            and r["narration"].startswith("MONTH SKIPPED")],
       "S522: the /skip-month route records the skipped month, with its statement words")
    _rq2 = _cl6.post(URL_PREFIX + "/skip-month", data={"staff": "D'Souza", "month": "2030-06", "reason": ""})
    ck(b"NOT recorded" in _rq2.data and not is_deferred(RQ["id"], "2030-06"),
       "S522: the route refuses a skip without a reason and says so")
"""))


# =====================================================================================
#  salary_policy.py
# =====================================================================================
P_EDITS = []

P_EDITS.append(("P1 version",
"""VERSION = "1.17-S489\"""",
"""VERSION = "1.18-S522\""""))

P_EDITS.append(("P2 docstring head",
'''"""
salary_policy.py — v1.17 (S489, the owner, 06-Oct-2026; D681, D682) — ADVANCES AND LOANS, RE-LAID.''',
'''"""
salary_policy.py — v1.18 (S522, the owner, 11-Oct-2026) — a month skipped on every long-term loan at once
(the ledger's skip-marked DEFER) reads "skipped" on Sheet 2's strip, the loan page and the slip; Sheets 3
and 4 print with thousands separators, Sheet 4 carries a total row and its right border; Sheet 3's dress /
I-card footnote is the settings' own; the slip's negative-net line says what is true (nothing carries it).
v1.17 (S489, the owner, 06-Oct-2026; D681, D682) — ADVANCES AND LOANS, RE-LAID.'''))

P_EDITS.append(("P3 a skip-marked defer is a skipped month",
"""                if m and m <= ym:
                    _marks[m] = {"LOAN_SKIP": "skip", "ADVANCE_DEFER": "defer", "CAPACITY_HOLD": "hold"}[c]""",
"""                if m and m <= ym:
                    _marks[m] = {"LOAN_SKIP": "skip", "ADVANCE_DEFER": "defer", "CAPACITY_HOLD": "hold"}[c]
                    if c == "ADVANCE_DEFER" and x.get("skip_month"):
                        _marks[m] = "skip"                # S522: the one-button skipped month"""))

P_EDITS.append(("P4 the slip names a skipped kist",
"""    priv = st.get("priv") or {}
    if priv.get("extra"):
        o.append(row("Purana loan — ek aur kist", "", priv["extra"], "new"))""",
"""    for L in v["loans"]:                                # S522: a month the kist was not taken says so
        if L["cut"] > 0.005:
            continue
        _mk = [k for m, _a, k in L["strip"] if m == ym and k in ("skip", "defer", "hold")]
        if _mk:
            o.append(row("Loan ki kist — is mahine %s" % ("roki gayi" if _mk[0] == "hold" else "skip"),
                         "loan Rs %s (%s) · is mahine kuch nahi kata" % (inr(L["amount"]), L["given"]), 0, "new"))
    priv = st.get("priv") or {}
    if priv.get("extra"):
        o.append(row("Purana loan — ek aur kist", "", priv["extra"], "new"))"""))

P_EDITS.append(("P5 the slip's negative-net line made true (F-760)",
"""        o.append('<div class="ownwarn">Is mahine advance, salary se Rs. %s zyada kata hai. '
                 'Matlab is mahine kuch nahi milega, aur Rs. %s agle mahine se adjust hoga.</div>'
                 % (inr(abs(float(st["net"]))), inr(abs(float(st["net"])))))""",
"""        o.append('<div class="ownwarn">Is mahine advance, salary se Rs. %s zyada kata hai. '
                 'Matlab is mahine kuch nahi milega. Yeh Rs. %s aapke naam baaki hai — agle mahine ki '
                 'salary se yeh apne-aap nahi katega; iska hisaab alag se hoga.</div>'
                 % (inr(abs(float(st["net"]))), inr(abs(float(st["net"])))))"""))

P_EDITS.append(("P6 Sheet 3 rows with separators",
"""        out.append("<tr>" + "".join(
            ("<td><b>%s</b></td>" % e(str(v))) if i == 0 else
            ("<td class='n'>%s</td>" % money(v)) for i, v in enumerate(vals))
            + "</tr>")""",
"""        out.append("<tr>" + "".join(
            ("<td><b>%s</b></td>" % e(str(v))) if i == 0 else
            ("<td class='n'>%s</td>" % _s3n(v, i)) for i, v in enumerate(vals))
            + "</tr>")"""))

P_EDITS.append(("P7 Sheet 3 total with separators",
"""    out.append('<tr class="tot"><td>TOTAL</td>' + "".join(
        "<td class='n'>%s</td>" % money(tot[i]) for i in range(1, len(cols)))
        + "</tr></table></div>")""",
"""    out.append('<tr class="tot"><td>TOTAL</td>' + "".join(
        "<td class='n'>%s</td>" % _s3n(tot[i], i) for i in range(1, len(cols)))
        + "</tr></table></div>")"""))

P_EDITS.append(("P8 Sheet 3 footnote from the settings",
"""               'the annual pot (paid at Diwali) — not in this month&#39;s net. D+I fine: Rs.%s/day '
               'each without. NET PAYABLE is cut to the last Rs.10 — the paise and the last digit are not paid out.</div>'
               % ("%g" % s["day_divisor"], s["free_late_min"], money(s.get("min_charge_rs", 0)),
                  100 - s["collect_now_pct"], s["improve_pct"], money(s["dress_rs"])))""",
"""               'the annual pot (paid at Diwali) — not in this month&#39;s net. D+I fine: %s. '
               'NET PAYABLE is cut to the last Rs.10 — the paise and the last digit are not paid out.</div>'
               % ("%g" % s["day_divisor"], s["free_late_min"], money(s.get("min_charge_rs", 0)),
                  100 - s["collect_now_pct"], s["improve_pct"], _di_words(s)))"""))

P_EDITS.append(("P9 Sheet 4 amounts, total row",
"""    for i, st in enumerate(res["staff"], 1):
        out.append("<tr style='height:40px'><td>%d</td><td><b>%s</b></td>"
                   "<td class='n'>%s</td><td></td><td></td></tr>"
                   % (i, e(st["name"]), money(st["net"])))
    out.append("</table></div>")""",
"""    _s4tot = 0.0
    for i, st in enumerate(res["staff"], 1):
        _s4tot += float(st["net"])
        out.append("<tr style='height:40px'><td>%d</td><td><b>%s</b></td>"
                   "<td class='n'>%s</td><td></td><td></td></tr>"
                   % (i, e(st["name"]), inr(st["net"])))
    out.append("<tr class='tot'><td></td><td>TOTAL</td><td class='n'>%s</td><td></td><td></td></tr>"
               % inr(_s4tot))                       # S522: the owner -- Sheet 4 prints its total
    out.append("</table></div>")"""))

P_EDITS.append(("P10 the right border inside the page",
"""  table.s3t{width:100%;table-layout:auto}""",
"""  table.s3t{width:calc(100% - 2px);table-layout:auto}"""))

P_EDITS.append(("P11 Sheet 4 table inside the page",
"""  .s4pg table{width:100%}""",
"""  .s4pg table{width:calc(100% - 2px)}"""))

P_EDITS.append(("P12 the two helpers",
"""def sheets34_html(res, back=None, approved=None, prefix="/register", status_html=""):""",
"""_S3_COUNT_COLS = {3, 5, 6, 12, 13}      # Leaves, Late min, Marks, Dress days, I-card days -- counts, not rupees


def _s3n(v, i):
    \"\"\"S522: a Sheet 3 figure -- rupees with Indian thousands separators, counts as they were.
    (The lock's reader, staff_register.locked_snapshot, strips commas before it reads a figure.)\"\"\"
    return money(v) if i in _S3_COUNT_COLS else inr(v)


def _di_words(s):
    \"\"\"S522: Sheet 3's dress / I-card footnote, from the settings the month was worked on.\"\"\"
    d, c = float(s.get("dress_rs") or 0), float(s.get("icard_rs") or 0)
    if d and c and d == c:
        return "Rs.%s/day each without the dress or the I-card" % money(d)
    bits = [("dress Rs.%s/day without" % money(d)) if d else "dress not charged",
            ("I-card Rs.%s/day without" % money(c)) if c else "I-card not charged"]
    return " · ".join(bits)


def sheets34_html(res, back=None, approved=None, prefix="/register", status_html=""):"""))

P_EDITS.append(("P13 selftest: the skipped month and the two helpers",
"""    # money that comes back in ONE salary is not an instalment loan: no slip for it""",
"""    # S522: a skip-marked DEFER (the one-button skipped month) reads 'skip' on the private page and the strip
    _R7 = _R + [dict(_sys("d1q", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d1"), skip_month=True),
                dict(_sys("d2q", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d2"), skip_month=True),
                dict(_sys("d4q", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d4"), skip_month=True)]
    _v7 = advance_views(ledger_money(_R7, "Dev", "2031-10"), "Dev", "2031-10", True, [], private=True)
    _p7 = private_split(_v7["priv_lines"], "2031-10", True)
    assert (_p7["kept"], _p7["cut"], _p7["paid"], _p7["status"]) == (6000, 0, 6000, "skip"), _p7
    assert ("2031-10", 0.0, "skip") in _v7["loans"][0]["strip"], _v7["loans"][0]["strip"]
    assert "skipped" in _strip_html(_v7["loans"][0])
    _sl7 = slip_html({"name": "Dev", "views": _v7, "base": 14000, "net": -500, "adv_ded": 0}, {"ym": "2031-10", "ledger_closed": True}, "")
    assert "is mahine skip" in _sl7 and "apne-aap nahi katega" in _sl7 and "agle mahine se adjust" not in _sl7
    _r7 = loan_ledger(_v7["priv_lines"][0], _H, "2031-10", True)[0]
    assert _r7[-2]["status"] == "skip" and _r7[-2]["end"] == 86000
    _R8 = _R + [_sys("d1z", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d1")]       # an ordinary defer stays a defer
    assert ledger_money(_R8, "Dev", "2031-10")["lines"][0]["marks"].get("2031-10") == "defer"
    assert _s3n(123456.5, 1) == "1,23,456.50" and _s3n(7.5, 3) == "7.5" and _s3n(1234, 5) == "1234"
    assert _di_words({"dress_rs": 15, "icard_rs": 15}).startswith("Rs.15/day each")
    assert _di_words({"dress_rs": 15, "icard_rs": 0}) == "dress Rs.15/day without · I-card not charged"
    # money that comes back in ONE salary is not an instalment loan: no slip for it"""))


def build(src_dir, out_dir):
    out = {}
    for name, edits in (("staff_ledger.py", L_EDITS), ("salary_policy.py", P_EDITS)):
        b = open(os.path.join(src_dir, name), "rb").read()
        if md5(b) != FROM[name]:
            raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (name, md5(b), FROM[name]))
        t = b.decode("utf-8")
        for label, old, new in edits:
            t = edit(t, old, new, name, label)
        out[name] = t.encode("utf-8")
        print("%-18s %d edits  %s -> %s" % (name, len(edits), FROM[name][:8], md5(out[name])[:8]))
    os.makedirs(out_dir, exist_ok=True)
    for name, b in out.items():
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(b)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2])
