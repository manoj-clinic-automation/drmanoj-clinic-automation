#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s611.py -- kit S611 (session S331, 21-Oct-2026): exact, counted edits turning the live /root/staff_ledger.py
(S609, 2fc0542f) into the S611 file.      python3 edits_s611.py LIVE OUT [KIT]   (exit 0 only if all anchors once, = KIT)

THE OWNER, 21-Oct-2026 19:57 IST: "when all months is selected ... it should properly display all the months which are
there in the system so that I can view and show a non-confusing statement: when the advances were taken, what amount
were taken, what were the settled advances, what was the salary cleared, what are the current advances."
20:14 IST: the word is "advance remaining".  20:16 IST: "proceed with the build."  For every staff member.

THE STATEMENT, NOW (one page, every person, every month the system holds):
  1. the top box (S609): Advance remaining now · To be cut from <month> salary, line by line · Advance remaining after;
  2. ONE BLOCK PER MONTH, oldest first: advances taken (date, amount, how it is recovered) · cut from that month's
     salary, line by line (which advance; cleared or what is left) · other ledger items of the month · salary: base ->
     paid, from that month's LOCKED salary sheet · advance remaining at the month's end. The running month shows what
     the close WILL cut (S609's dry run);
  3. every advance, one line each (taken, amount, how, recovered, balance, settled when) -- loans_view(), the Loans
     page's own figures;
  4. the old ledger lines, account summary and per-advance cards, kept, inside a closed "Technical entries" section.
Read-only: nothing in the ledger or the salary register changes.
"""
import hashlib
import sys

FUNCS = r'''
# =============================================================================
#  S611: THE STATEMENT, MONTH BY MONTH -- the owner, 21-Oct-2026: "a non-confusing statement: when the advances
#  were taken, what amount were taken, what were the settled advances, what was the salary cleared, what are the
#  current advances."  Read-only views over the ledger and the staff register's LOCKED salary runs.
# =============================================================================
SR_DB_PATH = os.environ.get("STAFF_REGISTER_DB", "/root/staff_register/staff_register.db")


def locked_salaries(db_path=None):
    """{ym: {name_lower: {"base": float|None, "net": float}}} from the staff register's LOCKED salary runs, read-only.
    The same reading as staff_register.locked_snapshot(): Sheet 3's frozen table (Salary = first figure, NET PAYABLE =
    last), plus any own-sheet NET; a month is used only when its NETs add up to the locked total payout."""
    import sqlite3 as _sq
    import re as _re
    import html as _h
    out = {}
    p = db_path or SR_DB_PATH
    if not os.path.exists(p):
        return out
    try:
        con = _sq.connect("file:%s?mode=ro" % p, uri=True, timeout=5)
        try:
            got_rows = con.execute("SELECT ym, total_payout, report_html FROM locked_run "
                                   "WHERE status='locked'").fetchall()
        finally:
            con.close()
    except Exception:                                             # noqa: BLE001
        return out

    def _f(t):
        try:
            return float(_h.unescape(str(t)).replace(",", "").strip())
        except (TypeError, ValueError):
            return None

    for ym, tot, doc in got_rows:
        doc = doc or ""
        m = _re.search(r"<table class='s3t'>(.*?)</table>", doc, _re.S)
        if not m:
            continue
        got, ok = {}, True
        for tr in _re.findall(r"<tr>(.*?)</tr>", m.group(1), _re.S):
            nm = _re.match(r"<td><b>(.*?)</b></td>", tr)
            if not nm:
                continue
            cells = _re.findall(r"<td class='n'>(.*?)</td>", tr)
            if len(cells) != 19:
                ok = False
                break
            base, adv, net = _f(cells[0]), _f(cells[1]), _f(cells[-1])
            if net is None:
                ok = False
                break
            got[_h.unescape(nm.group(1)).strip().lower()] = {"base": base, "adv": adv, "net": net}
        for nm, net in _re.findall(r"SHEET 5 · (.*?) — FULL WORKING — .*?<tr class='net'><td><b>NET PAYABLE</b></td>"
                                   r"<td class='n'><b>(.*?)</b></td></tr>", doc, _re.S):
            v = _f(net)
            if v is None:
                ok = False
                break
            got[_h.unescape(nm).strip().lower()] = {"base": None, "adv": None, "net": v}
        if not ok or not got:
            continue
        if tot is not None and int(round(sum(x["net"] for x in got.values()))) != int(tot):
            continue
        out[ym] = got
    return out


def _dmy(d):
    try:
        return datetime.date.fromisoformat(d[:10]).strftime("%d %b %Y")
    except Exception:                                             # noqa: BLE001
        return d or ""


def _rs(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    return ("Rs {:,.0f}".format(v)) if abs(v - round(v)) < 0.005 else "Rs {:,.2f}".format(v)


def _how(r):
    inst = r.get("instalment") or r["amount"]
    if r.get("interest"):
        return "loan, Rs %s a month (Rs %d of it interest)" % ("{:,}".format(int(inst)), INTEREST_RS)
    if advance_schedule(r):
        return "agreed schedule"
    if int(inst) >= int(r["amount"]):
        return "in full"
    return "Rs %s a month" % "{:,}".format(int(inst))


def month_book(staff, rows=None, salaries=None):
    """One person's months, oldest first: [{ym, words, state, taken, cuts, cut_total, others, salary, remaining}]."""
    import re as _re
    rows = rows if rows is not None else load_ledger()
    salaries = salaries if salaries is not None else locked_salaries()
    mine = [r for r in rows if r["staff"] == staff]
    by_id = {r["id"]: r for r in rows}
    issues = []
    for r in mine:
        if r["category"] != "ADVANCE_ISSUE" or r["status"] != "APPROVED" or r["amount"] <= 0:
            continue
        if any(x.get("contra_of") == r["id"] and x["category"] == "ADVANCE_ISSUE" and x["status"] == "APPROVED"
               and x["amount"] == -r["amount"] for x in rows):
            continue                                              # a reversed duplicate: not an advance
        issues.append(r)
    sysm = [r for r in mine if r["status"] == "APPROVED" and r["category"] in
            ("ADVANCE_INSTALMENT", "LOAN_INTEREST", "LOAN_CAPITALISE", "CAPACITY_HOLD")]
    others = [r for r in mine if r["status"] == "APPROVED" and r["category"] not in SALARY_EXCLUDED
              and r["category"] not in ("ADVANCE_INSTALMENT", "LOAN_INTEREST")
              and not r.get("contra_of")]
    plan = month_plan()
    nxt = plan["month"]
    planned = [r for r in (plan.get("rows") or []) if r["staff"] == staff] if not plan.get("closed") else []
    closed = {r.get("closed_month") for r in rows if r.get("closed_month")}

    def _mon(r):
        return (r.get("closed_month") or (r.get("date_from") or "")[:7])

    months = set(r["date_from"][:7] for r in issues)
    months |= set(_mon(r) for r in sysm if _mon(r))
    months |= set(_mon(r) for r in others if _mon(r))
    key = staff.strip().lower()
    months |= set(ym for ym, d in salaries.items() if key in d)
    if planned or any(r["date_from"][:7] == nxt for r in issues):
        months.add(nxt)
    months = sorted(m for m in months if m and len(m) == 7)

    def _rec_upto(iid, ym, extra=0):
        return sum(-r["amount"] for r in sysm if r["category"] == "ADVANCE_INSTALMENT" and r.get("contra_of") == iid
                   and _mon(r) <= ym) + extra

    def _cap_upto(iid, ym):
        return sum(r["amount"] for r in sysm if r["category"] == "LOAN_CAPITALISE" and r.get("contra_of") == iid
                   and _mon(r) <= ym)

    def _line(r, run=False):
        iss = by_id.get(r.get("contra_of") or "", {})
        when = _dmy(iss.get("date_from", ""))
        narr = r.get("narration") or ""
        if r["category"] == "CAPACITY_HOLD":
            m = _re.search(r"Rs (\d+)", narr)
            return {"rs": 0, "what": "held &mdash; the salary could not bear Rs %s of it (advance of %s); "
                                     "collected later" % (m.group(1) if m else "?", when), "kind": "hold"}
        if r["category"] == "LOAN_CAPITALISE":
            return {"rs": 0, "what": "Rs %d added to the loan of %s (month skipped)" % (r["amount"], when),
                    "kind": "hold"}
        amt = -int(r["amount"])
        if r["category"] == "LOAN_INTEREST":
            return {"rs": amt, "what": "interest on the loan of %s" % when, "kind": "cut"}
        m = _re.search(r"balance after:?\s*(-?\d+)", narr, _re.I)
        left = int(m.group(1)) if m else None
        if left is None:
            tail = ""
        elif left <= 0:
            tail = " &mdash; <b>%s</b>" % ("will clear it" if run else "cleared")
        else:
            tail = " &mdash; Rs {:,} %s on it".format(left) % ("will be left" if run else "left")
        return {"rs": amt, "what": "advance of %s%s" % (when, tail), "kind": "cut"}

    out = []
    for ym in months:
        running = (ym == nxt and ym not in closed)
        taken = [{"date": _dmy(r["date_from"]), "rs": r["amount"], "how": _how(r),
                  "note": (r.get("narration") or "")[:80]} for r in sorted(issues, key=lambda r: r["date_from"])
                 if r["date_from"][:7] == ym]
        src = planned if running else [r for r in sysm if _mon(r) == ym]
        cuts = [_line(r, running) for r in sorted(src, key=lambda r: (by_id.get(r.get("contra_of") or "", {}).get("date_from", ""),
                                                             r.get("category")))]
        cut_total = sum(c["rs"] for c in cuts if c["kind"] == "cut")
        rec_total = sum(-int(r["amount"]) for r in src if r["category"] == "ADVANCE_INSTALMENT")
        cap_total = sum(int(r["amount"]) for r in src if r["category"] == "LOAN_CAPITALISE")
        oth = [{"what": CATEGORIES.get(r["category"], [r["category"]])[0]
                + ((" &mdash; " + (r.get("narration") or "")[:60]) if r.get("narration") else ""),
                "rs": r["amount"]} for r in others if _mon(r) == ym]
        sal = salaries.get(ym, {}).get(key)
        extra = {}
        if running:
            for r in planned:
                if r["category"] == "ADVANCE_INSTALMENT":
                    extra[r.get("contra_of")] = extra.get(r.get("contra_of"), 0) - int(r["amount"])
        rem = 0
        for r in issues:
            if r["date_from"][:7] <= ym:
                rem += max(0, r["amount"] + _cap_upto(r["id"], ym) - _rec_upto(r["id"], ym, extra.get(r["id"], 0)))
        out.append({"ym": ym, "words": _month_words(ym),
                    "state": "running" if running else ("closed" if ym in closed else "open"),
                    "taken": taken, "cuts": cuts, "cut_total": cut_total, "rec_total": rec_total,
                    "cap_total": cap_total, "others": oth,
                    "salary": sal, "remaining": rem})
    return out


def statement_months_html(staff, month=None):
    """The month blocks and the every-advance table, as HTML for the statement page."""
    from html import escape as _e
    full = month_book(staff)
    _after = {full[i]["ym"]: full[i + 1] for i in range(len(full) - 1)}
    book = [b for b in full if b["ym"] == month] if month else full
    h = ""
    for b in book:
        run = b["state"] == "running"
        title = "%s%s" % (b["words"], " (running)" if run else ("" if b["state"] == "closed" else " (not yet closed)"))
        rows_ = ""
        if b["taken"]:
            rows_ += "<tr><td>Advances taken</td><td>%s</td></tr>" % "<br>".join(
                "%s &middot; <b>%s</b> &middot; %s%s" % (t["date"], _rs(t["rs"]), t["how"],
                                                       (" &middot; <small>%s</small>" % _e(t["note"])) if t["note"] else "")
                for t in b["taken"])
        else:
            rows_ += "<tr><td>Advances taken</td><td><small>none</small></td></tr>"
        lbl = "To be cut at month end" if run else "Cut from salary"
        if b["cuts"]:
            rows_ += "<tr><td>%s</td><td><b>%s</b><br>%s</td></tr>" % (lbl, _rs(b["cut_total"]), "<br>".join(
                ("%s &mdash; %s" % (_rs(c["rs"]), c["what"])) if c["kind"] == "cut" else c["what"] for c in b["cuts"]))
        else:
            rows_ += "<tr><td>%s</td><td><small>nothing</small></td></tr>" % lbl
        if b["others"]:
            rows_ += "<tr><td>Other items</td><td>%s</td></tr>" % "<br>".join(
                "%s%s &mdash; %s" % ("+" if o["rs"] > 0 else "", _rs(o["rs"]), o["what"]) for o in b["others"])
        s = b["salary"]
        if s:
            net = s["net"]
            paid = ("paid <b>%s</b>" % _rs(net)) if net >= 0 else (
                "paid <b>Rs 0</b> &mdash; short by %s" % _rs(-net))
            if net < 0:                                   # the same amount taken early next month: say so
                for t_ in _after.get(b["ym"], {}).get("taken", []):
                    if t_["rs"] == -net:
                        paid += "<br><small>see the advance of %s &mdash; the same amount</small>" % t_["date"]
                        break
            parts = ""
            if s.get("base") is not None and s.get("adv") is not None:
                other = round(s["base"] - s["adv"] - net, 2)
                parts = "Base %s<br>&minus; advances %s<br>" % (_rs(s["base"]), _rs(s["adv"]))
                if abs(other) >= 0.5:
                    parts += ("&minus; leave, late &amp; fines %s<br>" % _rs(other)) if other > 0 else (
                        "+ credits %s<br>" % _rs(-other))
                parts += "= "
            elif s.get("base"):
                parts = "Base %s &rarr; " % _rs(s["base"])
            rows_ += "<tr><td>Salary</td><td>%s%s</td></tr>" % (parts, paid)
        else:
            rows_ += "<tr><td>Salary</td><td><small>%s</small></td></tr>" % (
                "worked out at the month's close" if run else "no locked salary sheet for this month")
        rows_ += "<tr><td>Advance remaining %s</td><td><b>%s</b></td></tr>" % (
            "after the close" if run else "at month end", _rs(b["remaining"]))
        rows_ = rows_.replace("<tr><td>", "<tr><td style='width:30%;color:var(--muted);font-size:12.5px'>")
        h += ("<div class='card'><b style='font-size:16px'>%s</b><div style='margin-top:6px'>"
              "<table style='table-layout:fixed'>%s</table></div></div>" % (title, rows_))
    if not book:
        h += "<div class='card'><small>Nothing in this month.</small></div>"
    # every advance, one line each -- the Loans page's own figures
    try:
        v = loans_view(load_ledger(), month_plan()["month"], staff)
        trs = (v["staff"][0]["tranches"] if v["staff"] else [])
    except Exception:                                             # noqa: BLE001
        trs = []
    if trs:
        _iss = {r["id"]: r for r in load_ledger()}
        t = ("<tr><th>taken</th><th>amount</th><th>recovered</th><th>remaining</th></tr>")
        for x in sorted(trs, key=lambda x: x["date"]):
            _sh = lambda ym: _month_words(ym)[:3] + " " + str(ym)[:4] if ym else ""
            if x["open"]:
                st = ("to be cut in %s" % _sh(x["next_month"])) if x.get("next_month") and x.get("next_amount") else "open"
                if x["balance"] and x.get("next_amount") and x["next_amount"] < x["balance"]:
                    st = "Rs %s to be cut in %s" % ("{:,}".format(x["next_amount"]), _sh(x["next_month"]))
            else:
                st = "settled%s" % ((" " + _sh(x["last_paid"])) if x.get("last_paid") else "")
            _hw = _how(_iss[x["id"]]) if x["id"] in _iss else _e(x["how"])
            t += ("<tr><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td><td><b>%s</b><br><small>%s</small></td></tr>"
                  % (_dmy(x["date"]), _hw, _rs(x["amount"]), _rs(x["recovered"]), _rs(x["balance"]), st))
        _wf = sum(1 for x in trs if x.get("lane") == "waterfall") > 1
        h += ("<div class='card'><b style='font-size:16px'>Every advance</b>"
              + ("<br><small>Advances not taken against one month's salary are cut from ONE monthly amount &mdash; "
                 "the oldest one's &mdash; oldest first. A later advance waits until the older ones are cleared; "
                 "if the salary is too small, the rest is held and cut later.</small>" if _wf else "")
              + "<div class='tw' style='margin-top:6px'><table style='font-size:12.5px;width:100%%'>%s</table></div></div>" % t)
    return "<style>.stm small{color:#e1eaf3;font-size:12.5px}</style><div class='stm'>" + h + "</div>"


def build_statement(staff, month=None):'''

EDITS = [
    ('def build_statement(staff, month=None):', None),          # replaced by FUNCS (which ends with it)
    ('                  f"Total advance outstanding now: <b>Rs {_outst}</b><br>"',
     '                  f"Advance remaining now: <b>{_rs(_outst)}</b><br>"'),
    ('                  + ("" if _plan["closed"] else f"Left after {_mw}: <b>Rs {_left}</b><br>")',
     '                  + ("" if _plan["closed"] else f"Advance remaining after {_mw}: <b>{_rs(_left)}</b><br>")'),
    ('        advbox = (f"<div class=\'card\' style=\'border:2px solid #2e6b34\'><b>Advances &mdash; {staff}</b><br>"',
     '        _topbox = (f"<div class=\'card\' style=\'border:2px solid #2e6b34\'><b>Advances &mdash; {staff}</b><br>"'),
    ('                     "<small>As taken at the close.</small>")\n                  + "</div>") + advbox',
     '                     "<small>As taken at the close.</small>")\n                  + "</div>")              # S611: the top box'),
    ('''        body = (head + f"<h3>{staff}" + (f" · {month}" if month else " · all months")
                + f" · net Rs {st['net']}</h3>" + advbox
                + f"<table>{h}{b}</table>" + note)''',
     '''        # S611: the statement month by month; the old lines kept, closed, under "Technical entries"
        body = (head + f"<h3>{staff} &mdash; advances and salary"
                + (f" · {_month_words(month)}" if month else " · all months") + "</h3>"
                + _topbox + statement_months_html(staff, month)
                + "<details class='card'><summary style='cursor:pointer'><b>Technical entries</b> "
                  "<small>&mdash; every ledger line, the account summary and each advance's card</small></summary>"
                + f"<p><small>Ledger net ({month or 'all months'}): Rs {st['net']}</small></p>"
                + advbox + f"<div class='tw'><table>{h}{b}</table></div>" + note + "</details>")'''),
    ('APP_VERSION = "3.9-S609-MONTH-PLAN"', 'APP_VERSION = "4.0-S611-STATEMENT"'),
    ('        _li = "".join("<li>Rs %d &mdash; %s</li>" % (l["rs"], l["what"]) for l in _mine["lines"])',
     '        _li = "".join("<li>%s &mdash; %s</li>" % (_rs(l["rs"]), l["what"])\n'
     '                      for l in sorted(_mine["lines"], key=lambda l: l.get("d", "")))'),
    ('            _cut = "<b>Rs %d</b>" % _mine["take"]', '            _cut = "<b>%s</b>" % _rs(_mine["take"])'),
    ('                  + ("<small>Worked out by the month-close\'s own rules. If the salary cannot bear it all, the rest is "\n'
     '                     "held and collected later, not lost.</small>" if not _plan["closed"] else',
     '                  + ("<small>This is what the month-end close will cut. If the salary cannot cover it all, the rest "\n'
     '                     "is held and cut later, not lost.</small>" if not _plan["closed"] else'),
    ('        when_s = "-".join(reversed(when.split("-"))) if when else ""', '        when_s = _dmy(when) if when else ""'),
    ('        lines.append({"what": what, "rs": amt, "held": False})',
     '        lines.append({"what": what, "rs": amt, "held": False, "d": when})'),
    ('(" — clears it" if left <= 0 else " — Rs %d left on it" % left))',
     '(" — clears it" if left <= 0 else " — %s left on it" % _rs(left)))'),
    ('<p><small>v{APP_VERSION} · append-only · corrections by contra entry only</small></p>',
     '<p><small>v{APP_VERSION} · entries are never erased · a mistake is corrected by a reversing entry</small></p>'),
]


def main():
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1)" % (i, n))
            return 1
        s = s.replace(old, FUNCS.lstrip("\n") if new is None else new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %d edits applied · rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
