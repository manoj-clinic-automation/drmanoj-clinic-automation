#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s489.py -- builds the kit's salary_policy.py (v1.17) from the LIVE file's bytes
(/root/staff_register/salary_policy.py 92aecbe3, the 06-Oct-2026 01:35 bundle) by exact anchors,
each found exactly once. Re-running it on the same FROM bytes reproduces the TO md5.
usage: python3 make_s489.py <from salary_policy.py> <to salary_policy.py>"""
import sys, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
FROM_MD5 = "92aecbe37d4272523c1cf6a4d8c8aced"


def blk(name):
    with open(os.path.join(HERE, "blocks", name), encoding="utf-8") as f:
        return f.read()


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        raise SystemExit("!! anchor '%s' found %d times, expected exactly 1" % (what, n))
    return s.replace(old, new)


def cut(s, start, end, new, what):
    """replace from the line starting with `start` up to (not including) `end`."""
    if s.count(start) != 1 or s.count(end) != 1:
        raise SystemExit("!! block '%s': start x%d, end x%d" % (what, s.count(start), s.count(end)))
    a, b = s.index(start), s.index(end)
    if not a < b:
        raise SystemExit("!! block '%s': end before start" % what)
    return s[:a] + new + s[b:]


def main(src, dst):
    raw = open(src, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM_MD5:
        raise SystemExit("!! FROM is %s, expected %s" % (got, FROM_MD5))
    s = raw.decode("utf-8")

    # A1 -- header
    s = rep(s, '"""\nsalary_policy.py — v1.16 (S239, the owner, 11-Sep-2026) — PART-TIME staff pay NO leave charge:',
            '"""\nsalary_policy.py — v1.17 (S489, the owner, 06-Oct-2026; D681, D682) — ADVANCES AND LOANS, RE-LAID.\n'
            'Sheet 2 shows advances in two tables that never mix: this month\'s advances (cut in full from\n'
            'this salary) and instalment loans, ONE LINE PER PERSON PER LOAN however many parts it was handed\n'
            'over in, with a month strip, and one closing line per person. A salary slip is printed only for\n'
            'a person with a running instalment loan. A person with a PRIVATE long-term loan (Darpan) is back\n'
            'on the common sheets at base LESS the loan\'s standing instalment;\n'
            'late, absence, overtime and incentive are still worked on the full base. The long-term loan and\n'
            'its instalment live only on his own page -- one loan-ledger table from April 2026 -- and a month\n'
            'the instalment is not taken shows only there: the amount kept aside is paid to him on that page.\n'
            'NO RUPEE MOVES: every figure is still the staff ledger\'s own. full net = common net + paid to him.\n'
            'Nobody is paid on a sheet of their own any more (S240\'s SHEET 5 is retired).\n'
            'v1.16 (S239, the owner, 11-Sep-2026) — PART-TIME staff pay NO leave charge:', "A1 header")

    # A2 / A3 -- nobody off the common pages
    s = rep(s, 'SEPARATE_PAGES = ["Darpan"]     # staff with their OWN money page on Sheet 2 (owner)',
            'SEPARATE_PAGES = []             # S489 (D682): nobody is kept off the main money page; the private LOAN page is private_loan_names()\n'
            'VERSION = "1.17-S489"', "A2 SEPARATE_PAGES")
    s = rep(s, 'OWN_SHEET_DEFAULT = "darpan"',
            'OWN_SHEET_DEFAULT = ""          # S489 (D682): nobody is paid on a sheet of their own any more', "A3 OWN_SHEET_DEFAULT")

    # A4 -- ledger_money: every line also says how it has been and will be recovered
    s = rep(s, '''        if start > 0 or taken > 0 or rec > 0 or intr > 0 or end > 0:
            lines.append({"id": r["id"], "date": str(r.get("date_from", "")),
                          "amount": amt, "interest_loan": bool(r.get("interest")),
                          "start": start, "taken": taken, "recovered": round(rec, 2),
                          "interest": round(intr, 2), "end": end, "bf": bf,
                          "plan": recovery_plan(r)})
    lines.sort(key=lambda t: (not t["interest_loan"], t["date"]))
    # S238 v1.9: how each advance is recovered from here on (the close's own lanes)
    closed = any(x.get("closed_month") == ym for x in rows)
    proj = project_recovery(rows, lines, _ym_add(ym, 1) if closed else ym)
    for t in lines:
        t["terms"] = recovery_terms(proj.get(t["id"], []), t["end"])
    tot = lambda k: round(sum(t[k] for t in lines), 2)
    return {"lines": lines, "start": tot("start"), "taken": tot("taken"),
            "recovered": tot("recovered"), "interest": tot("interest"), "end": tot("end"),
            "deducted": round(tot("recovered") + tot("interest"), 2)}
''', '''        # S489 (D681): what the ledger has taken month by month, what it added, and the months
        # an instalment was skipped, deferred or held -- for the one-line-per-loan view.
        _hist, _caps, _marks = {}, [], {}
        for x in rows:
            if x.get("contra_of") != r["id"] or x.get("status") != "APPROVED":
                continue
            c = x.get("category")
            a = float(x.get("amount") or 0)
            if c in ("ADVANCE_INSTALMENT", "LOAN_INTEREST"):
                m = _rmonth(x)
                if m and m <= ym:
                    _h = _hist.setdefault(m, [0.0, 0.0])
                    _h[0 if c == "ADVANCE_INSTALMENT" else 1] += -a
            elif c == "LOAN_CAPITALISE":
                m = str(x.get("date_from", ""))[:7] or _rmonth(x)   # the month it BELONGS to (a close stamps both alike)
                if m and m <= ym:
                    _caps.append((m, a))
            elif c in ("LOAN_SKIP", "ADVANCE_DEFER", "CAPACITY_HOLD"):
                m = str(x.get("date_from", ""))[:7]
                if m and m <= ym:
                    _marks[m] = {"LOAN_SKIP": "skip", "ADVANCE_DEFER": "defer", "CAPACITY_HOLD": "hold"}[c]
        _line = {"id": r["id"], "date": str(r.get("date_from", "")),
                 "amount": amt, "interest_loan": bool(r.get("interest")),
                 "start": start, "taken": taken, "recovered": round(rec, 2),
                 "interest": round(intr, 2), "end": end, "bf": bf,
                 "plan": recovery_plan(r),
                 "inst": float(r.get("instalment") or amt), "lane": _adv_lane(r),
                 "against": str(r.get("against_month") or ""),
                 "private": bool(r.get("interest")) or bool(bf),
                 "hist": sorted((m, round(v[0], 2), round(v[1], 2)) for m, v in _hist.items()),
                 "caps": sorted(_caps), "marks": _marks, "proj": []}
        if start > 0 or taken > 0 or rec > 0 or intr > 0 or end > 0:
            lines.append(_line)
        else:
            cleared.append(_line)         # finished in an earlier month: kept for a loan's own history
    lines.sort(key=lambda t: (not t["interest_loan"], t["date"]))
    # S238 v1.9: how each advance is recovered from here on (the close's own lanes)
    closed = any(x.get("closed_month") == ym for x in rows)
    proj = project_recovery(rows, lines, _ym_add(ym, 1) if closed else ym)
    for t in lines:
        t["terms"] = recovery_terms(proj.get(t["id"], []), t["end"])
        t["proj"] = list(proj.get(t["id"], []))
    tot = lambda k: round(sum(t[k] for t in lines), 2)
    return {"lines": lines, "cleared": cleared, "start": tot("start"), "taken": tot("taken"),
            "recovered": tot("recovered"), "interest": tot("interest"), "end": tot("end"),
            "deducted": round(tot("recovered") + tot("interest"), 2)}
''', "A4 ledger_money tail")
    s = rep(s, '''    rev = _reversed_ids(rows) if rev is None else rev
    lines = []
    for r in rows:
        if (r.get("category") != "ADVANCE_ISSUE" or r.get("status") != "APPROVED"
                or r.get("staff") != name or float(r.get("amount") or 0) <= 0''',
            '''    rev = _reversed_ids(rows) if rev is None else rev
    lines = []
    cleared = []
    for r in rows:
        if (r.get("category") != "ADVANCE_ISSUE" or r.get("status") != "APPROVED"
                or r.get("staff") != name or float(r.get("amount") or 0) <= 0''', "A4b ledger_money head")

    # A4c -- project_recovery: a defer or a skip ALREADY RECORDED moves the plan as the close will
    s = rep(s, '''    against-month. Salary-capacity holds, skips and defers are NOT foreseen.
    Returns {advance id: [(month, principal, interest), ...]}."""''',
            '''    against-month. S489: a DEFER or a SKIP already recorded in the ledger moves the plan
    exactly as close_month() will -- a deferred month collects nothing for that advance and
    its schedule runs one month longer; a skipped month pauses the person's whole waterfall
    and adds the flat interest to the skipped loan. Salary-capacity holds, and defers or
    skips not yet recorded, are still NOT foreseen.
    Returns {advance id: [(month, principal, interest), ...]}."""
    _def, _skp, _pen = {}, {}, set()
    for x in rows:
        if x.get("status") != "APPROVED" or not x.get("contra_of"):
            continue
        _m = str(x.get("date_from", ""))[:7]
        if x.get("category") == "ADVANCE_DEFER":
            _def.setdefault(x["contra_of"], set()).add(_m)
            if x.get("defer_penalty") and not x.get("penalty_waived"):
                _pen.add((x["contra_of"], _m))
        elif x.get("category") == "LOAN_SKIP":
            _skp.setdefault(x["contra_of"], set()).add(_m)''', "A4c project_recovery head")
    s = rep(s, '''        elig = [i for i in live if i["am"] <= m]
        for i in [x for x in elig if x["lane"] == "schedule"]:
            sch = sorted(((str(e["month"]), float(e["amount"])) for e in i["r"]["schedule"]
                          if float(e.get("amount") or 0) > 0))
            k = max(0, min(len(sch), (int(m[:4]) * 12 + int(m[5:7])) -
                           (int(sch[0][0][:4]) * 12 + int(sch[0][0][5:7])) + 1))
''', '''        elig = [i for i in live if i["am"] <= m]
        for i in elig:                                  # S489: deferred this month -- nothing is collected for it
            if m in _def.get(i["id"], ()) and (i["id"], m) in _pen:
                i["bal"] += 1000.0                      # the 3rd+ defer of the year adds the flat interest
        elig = [i for i in elig if m not in _def.get(i["id"], ())]
        for i in [x for x in elig if x["lane"] == "schedule"]:
            sch = sorted(((str(e["month"]), float(e["amount"])) for e in i["r"]["schedule"]
                          if float(e.get("amount") or 0) > 0))
            k = max(0, min(len(sch), (int(m[:4]) * 12 + int(m[5:7])) -
                           (int(sch[0][0][:4]) * 12 + int(sch[0][0][5:7])) + 1
                           - len([_d for _d in _def.get(i["id"], ()) if _d <= m])))
''', "A4d project_recovery schedule lane")
    s = rep(s, '''        if wf:
            intr_due = 1000.0 * sum(1 for x in wf if x["interest"])
''', '''        if wf and any(x["interest"] and m in _skp.get(x["id"], ()) for x in wf):
            for x in wf:                                # S489: a skipped month -- the whole waterfall waits
                if x["interest"] and m in _skp.get(x["id"], ()):
                    x["bal"] += 1000.0
            wf = []
        if wf:
            intr_due = 1000.0 * sum(1 for x in wf if x["interest"])
''', "A4e project_recovery waterfall")

    # A5 -- the new pure functions, before the data plumbing that follows recovery_plan
    s = rep(s, "\ndef _register(ym):\n", "\n" + blk("blk_funcs.py") + "def _register(ym):\n", "A5 new functions")

    # A6 -- compute: the views, and the private split
    s = rep(s, "    man_adv = manual_advances(ym)\n    L, led_err = _ledger()\n",
            "    man_adv = manual_advances(ym)\n"
            "    _lp = loan_pages()                 # S489: loan groups + a private loan's pre-ledger months\n"
            "    _privn = private_loan_names(s)\n"
            "    _view_err = []\n"
            "    L, led_err = _ledger()\n", "A6a compute head")
    s = rep(s, '''        net = float(int(abs(net_exact) / 10) * 10) * (-1.0 if net_exact < 0 else 1.0)
        net_round_off = round(net_exact - net, 2)

        staff_out.append({
            "uid": uid, "name": name, "base": base, "exempt": exempt,''',
            '''        net = float(int(abs(net_exact) / 10) * 10) * (-1.0 if net_exact < 0 else 1.0)
        net_round_off = round(net_exact - net, 2)

        # S489 (D681): the ledger's lines sorted into what Sheet 2 shows.
        # S489 (D682): a person with a PRIVATE long-term loan sits on the common sheets at base
        # LESS the loan's standing instalment. Everything above -- day rate, minute rate, leave,
        # late, overtime, incentive -- was worked on the FULL base and is not touched. Only three
        # shown figures change: the salary, the advance column (the long-term instalment leaves
        # it) and the net (it loses what the private page pays him: nothing in an ordinary month,
        # the whole instalment in a month it was not taken).  full net == net + priv["reserve"].
        _is_priv = name.strip().lower() in _privn
        try:
            views = (advance_views(lm, name, ym, ledger_closed, _lp["groups"], private=_is_priv)
                     if lm else {"month_adv": [], "loans": [], "priv_lines": []})
            priv = private_split(views["priv_lines"], ym, ledger_closed) if _is_priv else None
        except Exception as _e:        # sorting the lines for display must never take the salary sheet down
            views, priv = {"month_adv": [], "loans": [], "priv_lines": []}, None
            _view_err.append("%s (%s)" % (name, type(_e).__name__))
        base_shown, adv_shown, adv_full, net_full = base, adv_ded, adv_ded, net
        if priv and base:
            base_shown = round(base - priv["kept"], 2)
            adv_shown = round(adv_ded - priv["cut_shown"], 2)
            net = round(net - priv["reserve"], 2)
            net_exact = round(net_exact - priv["reserve"], 2)

        staff_out.append({
            "uid": uid, "name": name, "base": base_shown, "base_full": base, "exempt": exempt,''', "A6b compute split")
    s = rep(s, '''            "open_bal": open_bal, "adv_ded": adv_ded, "manual_adv": m_adv,''',
            '''            "open_bal": open_bal, "adv_ded": adv_shown, "adv_ded_full": adv_full, "manual_adv": m_adv,
            "views": views, "priv": priv, "net_full": net_full,''', "A6c compute dict")

    s = rep(s, '''    notes = []
    if reg_err:
        notes.append("register: %s (grid items zero)" % reg_err)
''', '''    notes = []
    if _view_err:
        notes.append("The advance tables could not be laid out for %s — the salary figures are still the "
                     "ledger's own, but read the ledger statement and do NOT approve or print these sheets."
                     % ", ".join(_view_err))
    if reg_err:
        notes.append("register: %s (grid items zero)" % reg_err)
''', "A6d compute note")

    # A7 -- Sheet 2's advance tables and the private loan page
    s = cut(s, 'def sheet2_html(res, doors=False, ledger_prefix="/ledger", back=None,',
            "    # S238: say, in words, what happened to LAST month's hold (the owner, 10-Sep-2026).",
            blk("blk_sheet2.py"), "A7 sheet2")

    # A8 -- the slip replaces the own sheet
    s = cut(s, "def own_sheet_html(st, res, cap):", "def sheets34_html(", blk("blk_slip.py"), "A8 slip")
    s = rep(s, '''    for _s in _own_staff:                               # S240: his own two pages
        out.append(own_sheet_html(_s, res, cap))
''', '''    for _s in res["staff"]:                             # S489 (D681): a slip only where an instalment loan runs
        if has_slip(_s, res):
            out.append(slip_html(_s, res, cap))
    out.append(_SLIP_CSS)
''', "A9 slips in sheets34")
    s = rep(s, '''_OWN_SHEET_CSS = ("<style>.ownt td,.ownt th{padding:6px 9px}"''',
            '''_SLIP_CSS = ("<style>.ownt tr.new td{background:#f3faf3}"
             ".ownt tr.newtot td{background:#dcf0dc;font-weight:700}"
             ".ownt tr.new td:first-child{padding-left:22px}"
             ".ownt tr.new td.n{font-weight:400;color:#444}"
             ".slip table.ownt{min-width:440px}"
             "@media print{.slip table.ownt{width:calc(100% - 2px)}}"
             ".loanfoot{border:1px solid #c79a2a;background:#fffbeb;padding:8px 12px;margin:8px 0;"
             "font-size:14px;max-width:520px;line-height:1.45}"
             ".loanfoot .wk{color:#666;font-size:12px}</style>")

_OWN_SHEET_CSS = ("<style>.ownt td,.ownt th{padding:6px 9px}"''', "A9b slip css")

    # A10 -- the nav names the private page for what it is
    s = rep(s, '''             ("darpan", "Darpan", "%s/salary/flow/sheet2?ym=%s&staff=Darpan" % (prefix, ym)),''',
            '''             ("darpan", "Darpan · loan (private)", "%s/salary/flow/sheet2?ym=%s&staff=Darpan" % (prefix, ym)),''',
            "A10 nav")

    # A11 -- selftest
    s = rep(s, '''    print("salary_policy math selftest PASS")\n''', blk("blk_selftest.py") +
            '''    print("salary_policy math selftest PASS")\n''', "A11 selftest")

    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("TO %s  %s  (%d lines)" % (hashlib.md5(s.encode("utf-8")).hexdigest(), dst, s.count("\n")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
