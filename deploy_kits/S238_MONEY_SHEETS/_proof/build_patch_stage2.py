#!/usr/bin/env python3
"""build_patch_stage2.py -- salary_policy.py v1.8a (a5cf7afc..., the Sheet-1 print
stage) -> v1.8 (S238): Sheet 2 as the owner asked on 10-Sep-2026, and THE ADVANCE
LINE TAKEN FROM THE LEDGER (D349/D442). Anchored, exactly-once edits."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
PIN = "a5cf7afc457fa21275ac7eea40e784c0"
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != PIN:
    sys.exit("source is not stage-1 v1.8a")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

# ---- 0. the file's own history ------------------------------------------------
rep('''salary_policy.py — v1.8 (S238) — Sheet 1 PRINTS AS TWO A4 PAGES''', '''salary_policy.py — v1.8 (S238) — THE ADVANCE LINE IS THE LEDGER'S OWN (D349/D442):
the Advance column deducts exactly the recoveries the staff ledger recorded for the
month (instalment + interest rows stamped to it), never a second calculation from
today's open balances (which for August 2026 would have taken Darpan Rs 29,000
against the owner's Rs 20,000, and Surendra 0 against Rs 7,000). compute() reports
ledger_closed; the Lock refuses until the ledger month is closed.
Sheet 2 (the owner, 10-Sep-2026): advances taken this month exclude reversed
entries and say HOW each recovers; the open position is AS AT THE MONTH'S END (so it
reads the same on lock day as on any later day) -- open at start, taken, recovered,
interest, open at end; the improvement holds say what happened to last month's hold
in words; every section prints on one A4 sheet, never split, several to a sheet.
Sheet 1 PRINTS AS TWO A4 PAGES''', "doc")

# ---- 1. the one rule: what the ledger says for this person and month ---------
rep('''def _register(ym):''', '''def _reversed_ids(rows):
    """Advances genuinely reversed -- the same test staff_ledger.open_advances() uses."""
    by = {r.get("id"): r for r in rows}
    out = set()
    for r in rows:
        if (r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "APPROVED"
                and r.get("contra_of")):
            o = by.get(r["contra_of"])
            if o and float(r.get("amount") or 0) == -float(o.get("amount") or 0):
                out.add(o["id"])
    return out


def _brought_forward(r):
    """D258 migration rows: opening balances brought from the workbook."""
    return str(r.get("narration", "")).startswith("opening balance migrated")


def _rmonth(x):
    return (x.get("closed_month") or str(x.get("date_from", ""))[:7])


def ledger_money(rows, name, ym, rev=None):
    """S238 (D349): the staff ledger's OWN figures for one person and one month,
    AS AT THE MONTH'S END -- open at the start, taken in the month, recovered and
    interest charged at the month's close, open at the end. Later months' rows are
    ignored, so a locked month reads the same on any later day. deducted = what
    the ledger took from this month's salary (principal + interest)."""
    rev = _reversed_ids(rows) if rev is None else rev
    lines = []
    for r in rows:
        if (r.get("category") != "ADVANCE_ISSUE" or r.get("status") != "APPROVED"
                or r.get("staff") != name or float(r.get("amount") or 0) <= 0
                or r.get("id") in rev):
            continue
        d = str(r.get("date_from", ""))[:7]
        bf = _brought_forward(r)
        if bf:      # a migrated opening balance exists from its first recovery month
            d = min([d] + [_rmonth(x) for x in rows if x.get("contra_of") == r["id"]
                           and x.get("status") == "APPROVED" and _rmonth(x)])
        if d > ym:
            continue
        amt = float(r["amount"])
        rec = intr = cap_before = cap_now = rec_before = 0.0
        for x in rows:
            if x.get("contra_of") != r["id"] or x.get("status") != "APPROVED":
                continue
            m = _rmonth(x)
            a = float(x.get("amount") or 0)
            c = x.get("category")
            if c == "ADVANCE_INSTALMENT":
                if m < ym: rec_before += -a
                elif m == ym: rec += -a
            elif c == "LOAN_INTEREST" and m == ym:
                intr += -a
            elif c == "LOAN_CAPITALISE":
                if m < ym: cap_before += a
                elif m == ym: cap_now += a
        # brought forward = taken before this month, OR an opening balance migrated
        # from the workbook (D258: DATED on its entry day, but years of history)
        if d < ym or bf or rec_before or cap_before:
            start, taken = round(amt - rec_before + cap_before, 2), 0.0
        else:
            start, taken = 0.0, amt
        end = round(start + taken - rec + cap_now, 2)
        if start > 0 or taken > 0 or rec > 0 or intr > 0 or end > 0:
            lines.append({"id": r["id"], "date": str(r.get("date_from", "")),
                          "amount": amt, "interest_loan": bool(r.get("interest")),
                          "start": start, "taken": taken, "recovered": round(rec, 2),
                          "interest": round(intr, 2), "end": end, "bf": bf,
                          "plan": recovery_plan(r)})
    lines.sort(key=lambda t: (not t["interest_loan"], t["date"]))
    tot = lambda k: round(sum(t[k] for t in lines), 2)
    return {"lines": lines, "start": tot("start"), "taken": tot("taken"),
            "recovered": tot("recovered"), "interest": tot("interest"), "end": tot("end"),
            "deducted": round(tot("recovered") + tot("interest"), 2)}


def recovery_plan(r):
    """How an advance recovers, in words (the owner: the old 'Instalment' header
    was wrong -- it printed the whole amount for a recover-in-full advance)."""
    amt = float(r.get("amount") or 0)
    sched = r.get("schedule") or []
    if sched:
        return " · ".join("%s %s" % (month_words(str(e.get("month", "")))[:3] + " "
                                     + str(e.get("month", ""))[2:4],
                                     money(e.get("amount") or 0)) for e in sched)
    inst = float(r.get("instalment") or amt)
    if r.get("interest"):
        return "loan · %s a month (Rs 1,000 of it interest)" % money(inst)
    if inst >= amt:
        am = r.get("against_month") or str(r.get("date_from", ""))[:7]
        return "in full from the %s salary" % month_words(am)
    return "%s a month, in line behind any open interest loan" % money(inst)


def _register(ym):''', "ledger_money")

# ---- 2. compute(): the advance line from the ledger ----------------------------
rep('''        # ledger side (advances/loans) — descriptive + a preview deduction
        advances_month, loans, adv_ded = [], [], 0.0
        open_bal = 0.0''', '''        # ledger side (advances/loans) — S238: the ledger's OWN figures (D349)
        advances_month, loans, adv_ded = [], [], 0.0
        open_bal = 0.0
        lm = None''', "adv_init")
rep('''        if L:
            for r in led_rows:
                if (r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "APPROVED"
                        and r.get("staff") == name
                        and str(r.get("date_from", ""))[:7] == ym
                        and float(r.get("amount") or 0) > 0):
                    advances_month.append(r)
            for o in opens:
                if o["issue"].get("staff") != name:
                    continue
                open_bal += o["balance"]
                inst = min(o["balance"], o["instalment"] or o["balance"])
                due_now = True
                am = o["issue"].get("against_month")
                if am and am > ym:
                    due_now = False           # future-attributed quota advance
                # S200/R7: EVERY open advance is listed on Sheet 2 — the
                # interest-only filter hid Darpan's non-interest tranches.
                loans.append({"o": o, "due": inst if due_now else 0,
                              "interest": o["interest"]})
                if due_now:
                    adv_ded += inst
            adv_ded = round(adv_ded, 2)''', '''        if L:
            for r in led_rows:
                if (r.get("category") == "ADVANCE_ISSUE" and r.get("status") == "APPROVED"
                        and r.get("staff") == name
                        and str(r.get("date_from", ""))[:7] == ym
                        and float(r.get("amount") or 0) > 0
                        and r.get("id") not in led_rev
                        and not _brought_forward(r)):
                    advances_month.append(r)
            lm = ledger_money(led_rows, name, ym, led_rev)
            loans = lm["lines"]
            open_bal = lm["end"]
            # S238 (D349/D442): deduct EXACTLY what the ledger recovered for this
            # month — its instalment and interest rows stamped to the month. Before
            # the ledger close runs there are none, so the Lock refuses (below).
            adv_ded = lm["deducted"]''', "adv_block")
rep('''    L, led_err = _ledger()
    led_rows = []
    opens = []
    if L:
        try:
            led_rows = L.load_ledger()
            opens = L.open_advances()
        except Exception as e:
            led_err = "%s: %s" % (type(e).__name__, e)
            L = None''', '''    L, led_err = _ledger()
    led_rows = []
    opens = []
    led_rev = set()
    if L:
        try:
            led_rows = L.load_ledger()
            opens = L.open_advances()
            led_rev = _reversed_ids(led_rows)
        except Exception as e:
            led_err = "%s: %s" % (type(e).__name__, e)
            L = None
    ledger_closed = bool(L) and any(r.get("closed_month") == ym for r in led_rows)''', "led_load")
rep('''            "open_bal": open_bal, "adv_ded": adv_ded, "manual_adv": m_adv,''', '''            "open_bal": open_bal, "adv_ded": adv_ded, "manual_adv": m_adv,
            "ledger_money": lm,''', "staff_out")
rep('''    if led_err:
        notes.append("ledger: %s (advance/loan columns empty)" % led_err)''', '''    if led_err:
        notes.append("ledger: %s (advance/loan columns empty)" % led_err)
    elif not ledger_closed:
        notes.append("The staff ledger has NOT been closed for %s yet, so the Advance column "
                     "is 0 — recoveries enter only at the ledger close (it opens on the 1st of "
                     "the next month). The Lock refuses until it has run." % month_words(ym))''', "note")
rep('''    return {"ym": ym, "settings": s, "covered": covered, "staff": staff_out,''',
    '''    return {"ym": ym, "settings": s, "covered": covered, "staff": staff_out,
            "ledger_closed": ledger_closed,''', "ret")

# ---- 3. Sheet 2 -------------------------------------------------------------------
rep("             if staff else \"SHEET 2 \u00b7 ADVANCES, LOANS &amp; HOLDS \u2014 %s\" % month_words(ym))",
    "             if staff else \"SHEET 2 \u00b7 ADVANCES, LOANS & HOLDS \u2014 %s\" % month_words(ym))", "s2_title_amp")
rep('''    out.append("<h2>Advances taken this month</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Date</th><th>Amount</th><th>Against month</th>"
               "<th>Instalment</th><th></th></tr>")''', '''    out.append("<section class='s2sec'><h2>Advances taken this month</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Date</th><th>Amount</th><th>Against month</th>"
               "<th>How it is recovered</th><th class='noprint'></th></tr>")''', "s2_adv_head")
rep('''            out.append("<tr><td><b>%s</b></td><td>%s</td><td class='n'>%s</td>"
                       "<td>%s</td><td class='n'>%s</td><td>%s</td></tr>"
                       % (e(st["name"]), e(str(r.get("date_from", ""))),
                          money(r.get("amount") or 0),
                          e(str(r.get("against_month") or "-")),
                          money(r.get("instalment") or r.get("amount") or 0), door))
    if not any_a:
        out.append("<tr><td colspan='6'>none recorded</td></tr>")
    out.append("</table></div>")''', '''            out.append("<tr><td><b>%s</b></td><td>%s</td><td class='n'>%s</td>"
                       "<td>%s</td><td>%s</td><td class='noprint'>%s</td></tr>"
                       % (e(st["name"]), e(str(r.get("date_from", ""))),
                          money(r.get("amount") or 0),
                          e(str(r.get("against_month") or "-")),
                          e(recovery_plan(r)), door))
    if not any_a:
        out.append("<tr><td colspan='6'>none recorded</td></tr>")
    out.append("</table></div></section>")''', "s2_adv_body")
rep('''    out.append("<h2>Current open loans &amp; advances (as of today)</h2>"
               "<div class='tw'><table><tr><th>Staff</th><th>Taken</th>"
               "<th>Instalment</th>%s<th>Balance</th><th></th></tr>"
               % ("<th>Due this month</th>" if cur_month else ""))
    any_l = False
    for st in pick:
        for lo in st["loans"]:
            any_l = True
            o = lo["o"]
            door = ('<a class="door" href="%s/advances">ledger</a>' % ledger_prefix) if doors else ""
            out.append("<tr><td><b>%s</b>%s</td><td>%s</td><td class='n'>%s</td>%s"
                       "<td class='n'>%s</td><td>%s</td></tr>"
                       % (e(st["name"]),
                          " <small>(interest loan)</small>" if lo.get("interest") else "",
                          e(str(o["issue"].get("date_from", ""))),
                          money(o["instalment"]),
                          ("<td class='n'>%s</td>" % money(lo["due"])) if cur_month else "",
                          money(o["balance"]), door))
    if not any_l:
        out.append("<tr><td colspan='6'>none open</td></tr>")
    out.append("</table></div>")''', '''    # S238: the open position AS AT THE MONTH'S END, from the ledger's own rows —
    # it reads the same on lock day as on any later day (the owner, 10-Sep-2026).
    out.append("<section class='s2sec'><h2>Open advances &amp; loans — position at the end of %s</h2>"
               "<div class='tw'><table><tr><th>%s</th><th>Open at start</th>"
               "<th>Taken this month</th><th>Recovered this month</th><th>Interest (from salary)</th>"
               "<th>Open at month end</th><th class='noprint'></th></tr>"
               % (month_words(ym), "Advance / loan" if staff else "Staff"))
    any_l = False
    for st in pick:
        lm = st.get("ledger_money") or {}
        if not lm.get("lines"):
            continue
        any_l = True
        door = ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                % (ledger_prefix, e(st["name"]))) if doors else ""
        if staff:          # the person's own page: every advance, one line each
            for t in lm["lines"]:
                out.append("<tr><td>%s · %s%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                           "<td class='n'>%s</td><td class='n'>%s</td><td class='n'><b>%s</b></td>"
                           "<td class='noprint'>%s</td></tr>"
                           % ("brought forward" if t.get("bf") else e(t["date"]), money(t["amount"]),
                              " <small>(interest loan)</small>" if t["interest_loan"] else "",
                              money(t["start"]), money(t["taken"]), money(t["recovered"]),
                              money(t["interest"]), money(t["end"]), door))
        out.append("<tr%s><td><b>%s</b></td><td class='n'>%s</td><td class='n'>%s</td>"
                   "<td class='n'>%s</td><td class='n'>%s</td><td class='n'><b>%s</b></td>"
                   "<td class='noprint'>%s</td></tr>"
                   % (" class='tot'" if staff else "", e(st["name"] if not staff else "Total"),
                      money(lm["start"]), money(lm["taken"]), money(lm["recovered"]),
                      money(lm["interest"]), money(lm["end"]), "" if staff else door))
    if not any_l:
        out.append("<tr><td colspan='7'>none open</td></tr>")
    out.append("</table></div>")
    if not res.get("ledger_closed", True):
        out.append("<div class='note'>The staff ledger is not closed for %s yet — the "
                   "'Recovered' and 'Interest' columns fill in at the ledger close.</div>"
                   % month_words(ym))
    out.append("</section>")''', "s2_open")
rep('''            out.append("<h2>Duty credits this month</h2><div class='tw'><table>"''',
    '''            out.append("<section class='s2sec'><h2>Duty credits this month</h2><div class='tw'><table>"''', "s2_duty_open")
rep('''                          money(st["outst_rs"]), money(st["extra_rs"]), money(st["night_rs"])))''',
    '''                          money(st["outst_rs"]), money(st["extra_rs"]), money(st["night_rs"])))
            out.append("</section>")''', "s2_duty_close")
rep('''    out.append("<h2>Improvement holds</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Last month held</th><th>This month</th>"
               "<th>New charge</th><th>Collect now</th><th>New hold</th></tr>")
    for st in pick if staff else [x for x in res["staff"] if x["name"] not in sep]:
        if not (st["held"] or st["release"] or st.get("prior_collect")
                or st["release_note"] or st["late_charge"]):
            continue
        out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td>%s</td>"
                   "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                   % (e(st["name"]),
                      (money(st["release"]) if st["release"] else
                       ("COLLECT " + money(st.get("prior_collect", 0))
                        if st.get("prior_collect") else "-")),
                      e(st["release_note"] or "-"),
                      money(st["late_charge"]), money(st["collect"]),
                      money(st["held"])))
    out.append("</table></div>")''', '''    # S238: say, in words, what happened to LAST month's hold (the owner, 10-Sep-2026).
    pm = prev_ym(ym)
    _hs = hold_state()
    _pm_recorded = any(k[1] == pm for k in _hs)
    out.append("<section class='s2sec'><h2>Improvement holds</h2>")
    if not _pm_recorded:
        out.append("<div class='note'>No hold was carried from %s: holds are written only "
                   "when a month is LOCKED, and %s has no locked hold on record.</div>"
                   % (month_words(pm), month_words(pm)))
    out.append("<div class='tw'><table>"
               "<tr><th>Staff</th><th>%s hold</th><th>What happened to it</th>"
               "<th>Late charge this month</th><th>Collected now</th>"
               "<th>Held till next month</th></tr>" % month_words(pm))
    _any_h = False
    for st in pick if staff else [x for x in res["staff"] if x["name"] not in sep]:
        ph = _hs.get((st["name"], pm))
        if not (st["held"] or st["release"] or st.get("prior_collect")
                or st["release_note"] or st["late_charge"] or ph):
            continue
        _any_h = True
        if ph and ph.get("status") == "HELD":
            if st["release"]:
                what = "CANCELLED — %s" % (st["release_note"] or "improved")
            elif st.get("prior_collect"):
                what = "COLLECTED in this month — %s" % (st["release_note"] or "no improvement")
            else:
                what = "still held"
            last = money(ph["held"])
        elif ph:
            what = "already closed (%s)" % ph.get("status", "").lower()
            last = money(ph.get("held", 0))
        else:
            what, last = "no hold", "-"
        out.append("<tr><td><b>%s</b></td><td class='n'>%s</td><td>%s</td>"
                   "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td></tr>"
                   % (e(st["name"]), last, e(what), money(st["late_charge"]),
                      money(st["collect"]), money(st["held"])))
    if not _any_h:
        out.append("<tr><td colspan='6'>no late charge and no hold this month</td></tr>")
    out.append("</table></div></section>")''', "s2_holds")
rep('''        out.append("<h2>All fines, leaves &amp; credits (every staff — for review)</h2>"
                   "<div class='tw'><table><tr><th>Staff</th><th>Leaves</th>"''', '''        out.append("<section class='s2sec'><h2>All fines, leaves &amp; credits (every staff — for review)</h2>"
                   "<div class='tw'><table class='wide'><tr><th>Staff</th><th>Leaves</th>"''', "s2_fines_open")
rep('''                       + "</tr>")
        out.append("</table></div>")

    out.append('<div class="sub">Advance/loan figures are the ledger\\'s own; '
               'corrections happen in the ledger (defer / waive there), then '
               'reload this sheet.</div>')
    out.append("</body></html>")''', '''                       + "</tr>")
        out.append("</table></div></section>")

    out.append('<div class="sub">Advance/loan figures are the ledger\\'s own, for the month '
               'shown; corrections happen in the ledger, then reload this sheet.</div>')
    out.append(_S2_PRINT_CSS)
    out.append("</body></html>")''', "s2_tail")
rep('''# S238: A4, two pages. Page 1 = the grid''', '''# S238: Sheet 2 on A4 — every section whole on one sheet, never split; several
# sections share a sheet when they fit. Screen view unchanged.
_S2_PRINT_CSS = """<style>
 @page{size:A4 portrait;margin:8mm}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:12px;margin:0 0 4px}
  .banner,.note{font-size:10.5px;padding:4px 8px;margin:6px 0}
  .s2sec{break-inside:avoid;page-break-inside:avoid;margin:0 0 10px}
  .s2sec h2{font-size:13px;margin:8px 0 4px;break-after:avoid;page-break-after:avoid}
  .s2sec table{width:100%;margin:2px 0}
  .s2sec th,.s2sec td{font-size:11px;padding:4px 5px;white-space:normal}
  .s2sec table.wide th,.s2sec table.wide td{font-size:9.5px;padding:3px 2px}
  .sub{font-size:10px}
  tr{break-inside:avoid;page-break-inside:avoid}
 }
</style>"""


# S238: A4, two pages. Page 1 = the grid''', "s2_css")

open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
