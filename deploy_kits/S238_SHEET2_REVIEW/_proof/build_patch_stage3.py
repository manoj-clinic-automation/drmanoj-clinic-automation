#!/usr/bin/env python3
"""build_patch_stage3.py -- salary_policy.py v1.8 (4136e7ae..., LIVE since 10-Sep 20:55)
-> v1.9 (S238, the owner's second review of Sheet 2, 10-Sep-2026 night).
Anchored, exactly-once edits; anything else aborts."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
PIN = "4136e7ae857d8dcbb8f7f987df5faa59"
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != PIN:
    sys.exit("source is not the live v1.8")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

rep('''salary_policy.py — v1.8 (S238) — THE ADVANCE LINE''', '''salary_policy.py — v1.9 (S238, the owner's second Sheet-2 review) — the advances
table flags any advance booked against a LATER month than it was given (most are
against the running month, so a later month is usually a keying slip); the second
table says, per advance, whether it is recovered IN ONE GO (how much, from which
salary) or ON INSTALMENTS (how much a month, and till which month); the fines table
spells out the days (not punched = sanctioned leave + outstation + absent without
leave) instead of an ambiguous "Leaves / Absent" pair; Sheet 2 prints on A4
LANDSCAPE; the ENFORCED/PREVIEW line is for the owner's screen only, never printed.
v1.8 (S238) — THE ADVANCE LINE''', "doc")

# ---- 1. recovery terms per advance ------------------------------------------------
rep('''def recovery_plan(r):''', '''def _ym_add(ym, n):
    y, m = int(ym[:4]), int(ym[5:7])
    t = y * 12 + (m - 1) + int(n)
    return "%04d-%02d" % (t // 12, t % 12 + 1)


def _adv_lane(r):
    """The same four lanes as staff_ledger.advance_lane (D349), read from the row."""
    amt = float(r.get("amount") or 0)
    inst = float(r.get("instalment") or amt)
    if [e for e in (r.get("schedule") or []) if float(e.get("amount") or 0) > 0]:
        return "schedule"
    if r.get("against_month") and not r.get("interest") and inst == amt:
        return "quota"
    return "loan" if r.get("interest") else "waterfall"


def project_recovery(rows, lines, start):
    """S238 v1.9: month by month, how the ledger's close will recover what is still
    open -- the SAME lanes and order as staff_ledger.close_month(): schedule steps,
    quota advances in full at their month, and ONE waterfall budget (the head
    tranche's instalment; Rs 1,000 interest out of it while a loan is open; the rest
    tranche to tranche, loans first, then oldest). Nothing waits before its
    against-month. Salary-capacity holds, skips and defers are NOT foreseen.
    Returns {advance id: [(month, principal, interest), ...]}."""
    by_id = {r.get("id"): r for r in rows}
    items = []
    for t in lines:
        r = by_id.get(t["id"])
        if not r or t["end"] <= 0:
            continue
        amt = float(r.get("amount") or 0)
        items.append({"id": t["id"], "r": r, "bal": float(t["end"]), "lane": _adv_lane(r),
                      "inst": float(r.get("instalment") or amt), "interest": bool(r.get("interest")),
                      "am": r.get("against_month") or str(r.get("date_from", ""))[:7],
                      "done": max(0.0, amt - float(t["end"]))})
    out = {i["id"]: [] for i in items}
    m = start
    for _ in range(480):
        live = [i for i in items if i["bal"] > 0.005]
        if not live:
            break
        elig = [i for i in live if i["am"] <= m]
        for i in [x for x in elig if x["lane"] == "schedule"]:
            sch = sorted(((str(e["month"]), float(e["amount"])) for e in i["r"]["schedule"]
                          if float(e.get("amount") or 0) > 0))
            k = max(0, min(len(sch), (int(m[:4]) * 12 + int(m[5:7])) -
                           (int(sch[0][0][:4]) * 12 + int(sch[0][0][5:7])) + 1))
            want = min(i["bal"], max(0.0, sum(a for _, a in sch[:k]) - i["done"]))
            if want > 0:
                i["bal"] -= want; i["done"] += want; out[i["id"]].append((m, want, 0.0))
        for i in [x for x in elig if x["lane"] == "quota"]:
            out[i["id"]].append((m, i["bal"], 0.0)); i["done"] += i["bal"]; i["bal"] = 0.0
        wf = sorted([x for x in elig if x["lane"] in ("loan", "waterfall") and x["bal"] > 0.005],
                    key=lambda x: (not x["interest"], str(x["r"].get("date_from", "")),
                                   str(x["r"].get("ts_entry", ""))))
        if wf:
            intr_due = 1000.0 * sum(1 for x in wf if x["interest"])
            budget = min(wf[0]["inst"], intr_due + sum(x["bal"] for x in wf))
            paid_i = {}
            for x in wf:
                if x["interest"] and budget > 0:
                    pi = min(1000.0, budget); budget -= pi; paid_i[x["id"]] = pi
            for x in wf:
                p = min(budget, x["bal"]) if budget > 0 else 0.0
                budget -= p
                if p > 0 or paid_i.get(x["id"]):
                    x["bal"] -= p; x["done"] += p
                    out[x["id"]].append((m, p, paid_i.get(x["id"], 0.0)))
        m = _ym_add(m, 1)
    return out


def recovery_terms(pays, end):
    """The owner's two columns for ONE advance, from its projected recoveries."""
    t = {"kind": "", "one_go_amt": 0.0, "one_go_month": "", "per": 0.0,
         "per_note": "", "from": "", "until": "", "open_after": False}
    pays = [(m, p + i, i) for m, p, i in pays if p + i > 0.005]
    if end <= 0:
        t["kind"] = "cleared"
        return t
    if not pays:
        t["kind"] = "unplanned"
        return t
    if len(pays) == 1:
        t.update(kind="one_go", one_go_amt=round(pays[0][1], 2), one_go_month=pays[0][0])
        return t
    amts = [round(a, 2) for _, a, _ in pays]
    per = max(set(amts), key=lambda v: (amts.count(v), v))
    notes = []
    if any(i for _, _, i in pays):
        notes.append("Rs 1,000 of it interest")
    if len(pays) <= 4 and len(set(amts)) > 1:
        per = 0.0
        notes = [" · ".join("%s %s" % (month_words(m)[:3], money(a)) for m, a, _ in pays)] + notes
    else:
        if amts[0] != per:
            notes.append("first month Rs %s" % money(amts[0]))
        if amts[-1] != per:
            notes.append("last month Rs %s" % money(amts[-1]))
    t.update(kind="instalments", per=per, per_note="; ".join(notes),
             **{"from": pays[0][0], "until": pays[-1][0]})
    return t


def recovery_plan(r):''', "terms")

rep('''    lines.sort(key=lambda t: (not t["interest_loan"], t["date"]))
    tot = lambda k: round(sum(t[k] for t in lines), 2)''', '''    lines.sort(key=lambda t: (not t["interest_loan"], t["date"]))
    # S238 v1.9: how each advance is recovered from here on (the close's own lanes)
    closed = any(x.get("closed_month") == ym for x in rows)
    proj = project_recovery(rows, lines, _ym_add(ym, 1) if closed else ym)
    for t in lines:
        t["terms"] = recovery_terms(proj.get(t["id"], []), t["end"])
    tot = lambda k: round(sum(t[k] for t in lines), 2)''', "terms_fill")

# ---- 2. the advances table: flag a later against-month ------------------------------
rep('''               "<th>How it is recovered</th><th class='noprint'></th></tr>")''',
    '''               "<th>How it is recovered</th><th>Check</th><th class='noprint'></th></tr>")''', "adv_head")
rep('''            out.append("<tr><td><b>%s</b></td><td>%s</td><td class='n'>%s</td>"
                       "<td>%s</td><td>%s</td><td class='noprint'>%s</td></tr>"
                       % (e(st["name"]), e(str(r.get("date_from", ""))),
                          money(r.get("amount") or 0),
                          e(str(r.get("against_month") or "-")),
                          e(recovery_plan(r)), door))
    if not any_a:
        out.append("<tr><td colspan='6'>none recorded</td></tr>")''', '''            _am = str(r.get("against_month") or "")
            _late = bool(_am) and _am > str(r.get("date_from", ""))[:7]
            if _late:
                n_late += 1
            out.append("<tr%s><td><b>%s</b></td><td>%s</td><td class='n'>%s</td>"
                       "<td>%s</td><td>%s</td><td>%s</td><td class='noprint'>%s</td></tr>"
                       % (" class='flag'" if _late else "", e(st["name"]), e(str(r.get("date_from", ""))),
                          money(r.get("amount") or 0),
                          e(month_words(_am) if _am else "-"),
                          e(recovery_plan(r)),
                          ("&#9888; later month — check" if _late else "ok"), door))
    if not any_a:
        out.append("<tr><td colspan='7'>none recorded</td></tr>")''', "adv_rows")
rep('''    any_a = False
    for st in pick:
        for r in st["advances_month"]:''', '''    any_a = False
    n_late = 0
    for st in pick:
        for r in st["advances_month"]:''', "adv_counter")
rep('''    out.append("</table></div></section>")

    # S200/R7: the owner's own advance record''', '''    out.append("</table></div>")
    if n_late:
        out.append("<div class='note'>%d advance%s above %s booked against a LATER month than "
                   "the month it was given. Advances are normally against the running month — "
                   "if one is a slip, correct it in the ledger (reverse it and enter it again), "
                   "then reload this sheet.</div>" % (n_late, "" if n_late == 1 else "s",
                                                      "is" if n_late == 1 else "are"))
    out.append("</section>")

    # S200/R7: the owner's own advance record''', "adv_note")

# ---- 3. the second table: one go / instalments -----------------------------------------
a = s.index("    # S238: the open position AS AT THE MONTH'S END")
b = s.index("    if staff:\n        st = pick[0] if pick else None")
s = s[:a] + '''    # S238 v1.9 (the owner): per advance, is it recovered IN ONE GO or ON INSTALMENTS
    # -- and for instalments, how much a month and till when. As at the month's end.
    out.append("<section class='s2sec'><h2>Advances &amp; loans still being recovered — "
               "as at the end of %s</h2><div class='tw'><table>"
               "<tr><th>Staff</th><th>Advance (date · amount)</th>"
               "<th>Recovered in one go</th><th>On instalments</th>"
               "<th>Recovered this month</th><th>Balance at month end</th>"
               "<th class='noprint'></th></tr>" % month_words(ym))
    any_l = False
    for st in pick:
        lm = st.get("ledger_money") or {}
        lines = [t for t in lm.get("lines", []) if t["end"] > 0 or t["recovered"] > 0]
        if not lines:
            continue
        any_l = True
        door = ('<a class="door" href="%s/statement?staff=%s">ledger</a>'
                % (ledger_prefix, e(st["name"]))) if doors else ""
        for i, t in enumerate(lines):
            tt = t.get("terms") or {}
            if tt.get("kind") == "one_go":
                one = "Rs %s from the <b>%s</b> salary" % (money(tt["one_go_amt"]), month_words(tt["one_go_month"]))
                inst = "—"
            elif tt.get("kind") == "instalments":
                one = "—"
                span = "%s → <b>%s</b>" % (month_words(tt["from"]), month_words(tt["until"]))
                if tt.get("per"):
                    inst = "<b>Rs %s a month</b> · %s%s" % (
                        money(tt["per"]), span,
                        ("<br><small>%s</small>" % e(tt["per_note"])) if tt.get("per_note") else "")
                else:
                    inst = "%s<br><small>%s</small>" % (span, e(tt.get("per_note", "")))
            elif tt.get("kind") == "unplanned":
                one, inst = "—", "no recovery terms on the ledger"
            else:
                one, inst = "cleared", "—"
            label = ("brought forward · " if t.get("bf") else e(t["date"]) + " · ") + money(t["amount"])
            if t["interest_loan"]:
                label += " <small>(interest loan)</small>"
            out.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='n'>%s</td>"
                       "<td class='n'><b>%s</b></td><td class='noprint'>%s</td></tr>"
                       % (("<b>%s</b>" % e(st["name"])) if i == 0 else "", label, one, inst,
                          money(t["recovered"] + t["interest"]), money(t["end"]),
                          door if i == 0 else ""))
        if len(lines) > 1:
            out.append("<tr class='tot'><td></td><td>total</td><td></td><td></td>"
                       "<td class='n'>%s</td><td class='n'><b>%s</b></td><td class='noprint'></td></tr>"
                       % (money(lm["recovered"] + lm["interest"]), money(lm["end"])))
    if not any_l:
        out.append("<tr><td colspan='7'>nothing being recovered</td></tr>")
    out.append("</table></div>")
    out.append("<div class='sub'>'Recovered this month' is what the ledger took from this "
               "month's salary (interest included). The months ahead follow the ledger's own "
               "recovery rules and current terms; a month skipped, deferred or held because the "
               "salary could not bear it moves them later.</div>")
    if not res.get("ledger_closed", True):
        out.append("<div class='note'>The staff ledger is not closed for %s yet — "
                   "'Recovered this month' fills in at the ledger close.</div>" % month_words(ym))
    out.append("</section>")

''' + s[b:]

# ---- 4. the fines table: days spelled out -----------------------------------------------
rep('''                   "<div class='tw'><table class='wide'><tr><th>Staff</th><th>Leaves</th>"
                   "<th>Absent</th><th>Late charge</th><th>Collect now</th><th>Hold</th>"
                   "<th>Leave amt (+ded/-cr)</th><th>Uninformed</th><th>Excess-absent</th>"
                   "<th>Dress</th><th>I-card</th><th>Night duty (+)</th>"
                   "<th>Incentive (+)</th></tr>")
        for st in res["staff"]:
            out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>%d</td>"
                       % (e(st["name"]), st["leaves_total"], st["absent_excl"])
                       + "".join("<td class='n'>%s</td>" % money(v) for v in (''', '''                   "<div class='tw'><table class='wide'><tr><th rowspan='2'>Staff</th>"
                   "<th colspan='4'>DAYS NOT PUNCHED on the machine</th>"
                   "<th rowspan='2'>Leave days counted<br><small>(leave used + absent without leave)</small></th>"
                   "<th rowspan='2'>Days off allowed</th>"
                   "<th rowspan='2'>Late charge</th><th rowspan='2'>Collect now</th><th rowspan='2'>Hold</th>"
                   "<th rowspan='2'>Leave amt<br><small>(+ded / −credit)</small></th>"
                   "<th rowspan='2'>Uninformed</th><th rowspan='2'>Excess-absent</th>"
                   "<th rowspan='2'>Dress</th><th rowspan='2'>I-card</th><th rowspan='2'>Night duty (+)</th>"
                   "<th rowspan='2'>Incentive (+)</th></tr>"
                   "<tr><th>total</th><th>sanctioned leave</th><th>outstation</th>"
                   "<th>absent, no leave</th></tr>")
        for st in res["staff"]:
            out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>%d</td>"
                       "<td class='n'>%d</td><td class='n'>%d</td><td class='n'>%s</td><td class='n'>%s</td>"
                       % (e(st["name"]), st.get("absent", 0), st.get("leave_in_absent", 0),
                          min(st.get("outst_days", 0), max(0, st.get("absent", 0) - st.get("leave_in_absent", 0))),
                          st.get("genuine", 0), money(st["leaves_total"]), money(st.get("offs", 0)))
                       + "".join("<td class='n'>%s</td>" % money(v) for v in (''', "fines")
rep('''        out.append("</table></div></section>")

    out.append('<div class="sub">Advance/loan figures are the ledger\\'s own, for the month ''', '''        out.append("</table></div>"
                   "<div class='sub'>Days not punched = sanctioned leave + outstation + absent "
                   "without leave — one set of days, not two to be added. 'Leave days counted' = "
                   "leave used (discretionary + festival) + absent without leave; the leave amount "
                   "is worked on it, less the days off allowed (a Sunday counts at its lower weight). "
                   "Outstation days are duty, not leave.</div></section>")

    out.append('<div class="sub">Advance/loan figures are the ledger\\'s own, for the month ''', "fines_note")

# ---- 5. Sheet 2 prints landscape; the enforcement line never prints ------------------
rep(''' @page{size:A4 portrait;margin:8mm}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:12px;margin:0 0 4px}
  .banner,.note{font-size:10.5px;padding:4px 8px;margin:6px 0}
  .s2sec{''', ''' @page{size:A4 landscape;margin:8mm}
 @media print{
  body{margin:0;font-size:11px;line-height:1.3}
  .tw{overflow:visible}
  .hdr h1{font-size:17px} .hdr .sub{font-size:12px;margin:0 0 4px}
  .banner,.note{font-size:10.5px;padding:4px 8px;margin:6px 0}
  tr.flag td{background:#fff3d6}
  .s2sec{''', "s2_landscape")
rep('''        return '<div class="banner enf">ENFORCED — this month is covered by the served notice.</div>'
    return ('<div class="banner prev">PREVIEW — nothing on this page is applied \'''', '''        return '<div class="banner enf noprint">ENFORCED — this month is covered by the served notice.</div>'
    return ('<div class="banner prev noprint">PREVIEW — nothing on this page is applied \'''', "banner")
rep(''' .hdr{text-align:center;margin-bottom:4px}''', ''' .hdr{text-align:center;margin-bottom:4px}
 tr.flag td{background:#fff3d6}''', "flag_css")
# ---- 6. holds: marked, not withheld; 20% improvement cancels (the owner, 10-Sep) ----
rep('''    "improve_pct": 30,          # % fewer chargeable minutes releases the hold''',
    '''    "improve_pct": 20,          # % fewer chargeable minutes CANCELS last month's hold (owner 10-Sep-2026: 30 was too high)''', "improve_default")
rep('''               "<tr><th>Staff</th><th>%s hold</th><th>What happened to it</th>"
               "<th>Late charge this month</th><th>Collected now</th>"
               "<th>Held till next month</th></tr>" % month_words(pm))''',
    '''               "<tr><th>Staff</th><th>%s hold</th><th>What happened to it</th>"
               "<th>Late charge this month</th><th>Deducted now</th>"
               "<th>Hold marked (paid now, not deducted)</th></tr>" % month_words(pm))''', "hold_head")
rep('''            elif st.get("prior_collect"):
                what = "COLLECTED in this month — %s" % (st["release_note"] or "no improvement")''',
    '''            elif st.get("prior_collect"):
                what = "DEDUCTED this month — %s" % (st["release_note"] or "no improvement")''', "hold_what")
rep('''        out.append("<tr><td colspan='6'>no late charge and no hold this month</td></tr>")
    out.append("</table></div></section>")''',
    '''        out.append("<tr><td colspan='6'>no late charge and no hold this month</td></tr>")
    out.append("</table></div><div class='sub'>A hold is only MARKED — it is paid with this "
               "month's salary, not withheld. If next month's chargeable late minutes fall by "
               "%d%% or more, it is cancelled; if not, it is deducted from next month's salary."
               "</div></section>" % s_now["improve_pct"])''', "hold_note")
rep('''    pm = prev_ym(ym)
    _hs = hold_state()''', '''    pm = prev_ym(ym)
    s_now = load_settings()
    _hs = hold_state()''', "hold_settings")
rep("""'at own salary minute-rate (charges under Rs.%s ignored). Hold: '
               '%d%% of the charge, returnable on %d%% improvement. Duty '""",
    """'at own salary minute-rate (charges under Rs.%s ignored). Hold: '
               '%d%% of the charge is marked, not deducted; cancelled on %d%% improvement next month, '
               'otherwise deducted next month. Duty '""", "sheet3_note")
# ---- 7. the advances table says the SAME thing as the recovery table ----------------
rep('''def recovery_plan(r):''', '''def terms_words(t, ym):
    """One advance's recovery in plain words -- what it gave this month, then what is
    ahead (from the close's own lanes, see project_recovery)."""
    tt = t.get("terms") or {}
    got = float(t.get("recovered") or 0) + float(t.get("interest") or 0)
    pre = ("Rs %s from the %s salary" % (money(got), month_words(ym))) if got > 0 else ""
    k = tt.get("kind")
    if k == "one_go":
        nxt = "Rs %s from the %s salary" % (money(tt["one_go_amt"]), month_words(tt["one_go_month"]))
    elif k == "instalments":
        nxt = (("Rs %s a month, " % money(tt["per"])) if tt.get("per") else "") + \\
            "%s to %s" % (month_words(tt["from"]), month_words(tt["until"]))
        if tt.get("per_note"):
            nxt += " (%s)" % tt["per_note"]
    elif k == "unplanned":
        nxt = "no recovery terms on the ledger"
    else:
        return (pre + " — cleared") if pre else "cleared"
    return (pre + "; then " + nxt) if pre else nxt


def recovery_plan(r):''', "terms_words")
rep('''                          e(month_words(_am) if _am else "-"),
                          e(recovery_plan(r)),''', '''                          e(month_words(_am) if _am else "-"),
                          e(terms_words(_ln[r.get("id")], ym) if r.get("id") in _ln else recovery_plan(r)),''', "adv_words")
rep('''            _am = str(r.get("against_month") or "")''', '''            _ln = {x["id"]: x for x in (st.get("ledger_money") or {}).get("lines", [])}
            _am = str(r.get("against_month") or "")''', "adv_ln")
# ---- 8. landscape gives the fines table room: bigger print (visual check) -----------
rep('''  .s2sec table.wide th,.s2sec table.wide td{font-size:9.5px;padding:3px 2px}''',
    '''  .s2sec table.wide th,.s2sec table.wide td{font-size:11.5px;padding:6px 3px}
  .s2sec table.wide small{font-size:10.5px}
  .s2sec td small{font-size:10px}''', "wide_print")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
