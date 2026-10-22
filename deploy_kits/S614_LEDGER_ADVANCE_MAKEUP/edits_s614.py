#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s614.py -- kit S614 (session S336, 22-Oct-2026): exact, counted edits turning the live /root/staff_ledger.py
(S612, 92885f3b) into the S614 file.     python3 edits_s614.py LIVE OUT [KIT]   (exit 0 only if all anchors occur once, = KIT)

THE OWNER, 22-Oct-2026 05:57 IST (D753): "I am not seeing the 3000 advance of 21st October from November 2026 salary
to be cut in November in the top section. Another thing is, while issuing a fresh advance, I should know what are
the pending advances. Of that staff."
  1. The statement's top section: under "Advance remaining after <month>", one line per advance that makes it up --
     what is left and when it is cut ("from November 2026 salary"; "from the monthly amount, oldest first"; the loan
     with its interest named apart).
  2. New entry: when a doctor picks a staff member, the blue box lists every open advance (date, amount, left, when
     cut), what the next close will cut, what is already booked against the chosen "Against which month" and the room
     under the ceiling.
  3. F-973: the New entry page's script died for a maker (Shavez): `var P = {{}};` is a JavaScript syntax error, so his
     form never showed or hid its fields and the ceiling line never appeared. Now `var P = {};`.
Screen review at 375px (sub-agent): five wording fixes taken in.
Display only: the figures are loans_view()'s, month_plan()'s, plan_for_staff()'s and advance_month_taken()'s own.
No ledger or salary figure changes.
"""
import hashlib
import sys

HELPERS = r'''# =============================================================================
#  S614 (D753): WHAT "ADVANCE REMAINING" IS MADE OF.
#  The owner, 22-Oct-2026: "I am not seeing the 3000 advance of 21st October from November 2026 salary to be cut
#  in November in the top section" -- and -- "while issuing a fresh advance, I should know what are the pending
#  advances. Of that staff."  ONE function names every open advance of a person: what is left now, what the close
#  of `plan` cuts from it, what is left after, and when the rest is cut. The figures are the Loans view's
#  (loans_view) and the close's own dry run (month_plan); nothing is worked out a second way (D349).
# =============================================================================
def _rsn(v):
    """Rs and its figure kept on one line (a phone wraps 'Rs' away from '5,000' otherwise)."""
    return _rs(v).replace("Rs ", "Rs&nbsp;")


def advance_makeup(staff, plan, rows=None, view=None):
    """[{id, date, amount, left_now, cut, interest, left, when, lane}] for staff's OPEN advances, oldest first."""
    rows = rows if rows is not None else load_ledger()
    if view is None:
        try:
            view = loans_view(rows, plan["month"], staff)
        except UnboundLocalError:                                 # F-974: loans_view() with nobody to list
            view = {"staff": []}
    d = next((x for x in (view.get("staff") or []) if x["staff"] == staff), None)
    trs = [t for t in (d["tranches"] if d else []) if t["open"]]
    by_id = {r["id"]: r for r in rows}
    pm = plan["month"]
    mine = [r for r in (plan.get("rows") or []) if r["staff"] == staff] if not plan.get("closed") else []
    cut, intr, held = {}, {}, set()
    for r in mine:
        if r["category"] == "ADVANCE_INSTALMENT":
            cut[r.get("contra_of")] = cut.get(r.get("contra_of"), 0) - int(r["amount"])
        elif r["category"] == "LOAN_INTEREST":
            intr[r.get("contra_of")] = intr.get(r.get("contra_of"), 0) - int(r["amount"])
        elif r["category"] == "CAPACITY_HOLD":
            held.add(r.get("contra_of"))
    left_of = {t["id"]: max(0, t["balance"] - cut.get(t["id"], 0)) for t in trs}
    loan_after = any(t["interest"] and left_of[t["id"]] > 0 for t in trs)
    _wf = sorted([t for t in trs if t["lane"] == "waterfall" and left_of[t["id"]] > 0],
                 key=lambda t: (t["date"], (by_id.get(t["id"]) or {}).get("ts_entry", "")))
    _head = _wf[0] if _wf else None                          # the close's own order: oldest first (D250)
    out = []
    for t in sorted(trs, key=lambda t: (t["date"], t["id"])):
        am = t.get("against_month") or ""
        left = left_of[t["id"]]
        if t["lane"] == "quota" and am > pm:
            when = "from %s salary" % _month_words(am)
        elif t["lane"] == "quota":
            when = "at the next close"
        elif t["lane"] == "loan":
            when = "a loan: %s a month, of which %s is interest" % (_rsn(t["instalment"]), _rsn(INTEREST_RS))
        elif t["lane"] == "schedule":
            _st = schedule_state(by_id.get(t["id"]) or {"id": t["id"], "amount": t["amount"]}, pm,
                                 rows + [r for r in mine if r.get("contra_of") == t["id"]
                                         and r["category"] == "ADVANCE_INSTALMENT"])
            when = (("by the agreed schedule &mdash; next %s in %s" % (_rs(_st["next_amount"]),
                                                                       _month_words(_st["next_month"])))
                    if _st.get("next_month") else "by the agreed schedule")
        elif loan_after:
            when = "after the loan is cleared, oldest first"
        elif _head is not None and t["id"] == _head["id"]:
            when = "from the monthly amount of %s, oldest first &mdash; next at the %s close" % (
                _rsn(_head["instalment"]), _month_words(_month_plus(pm, 1)))
        elif _head is not None:
            when = "after the older ones, from the monthly amount of %s" % _rsn(_head["instalment"])
        else:
            when = "from the monthly amount, oldest first"
        if left > 0 and t.get("deferred_now"):
            when += " (deferred at the %s close)" % _month_words(pm)
        elif left > 0 and t["id"] in held:
            when += " (part held at the %s close &mdash; the salary cannot bear it)" % _month_words(pm)
        out.append({"id": t["id"], "date": t["date"], "amount": t["amount"], "left_now": t["balance"],
                    "cut": cut.get(t["id"], 0), "interest": intr.get(t["id"], 0), "left": left,
                    "when": when, "lane": t["lane"], "instalment": t["instalment"]})
    return out


def makeup_html(staff, plan, rows=None, view=None):
    """The top section's list under "Advance remaining after <month>": one <li> per advance still open after it."""
    if plan.get("closed"):
        return ""
    li, mk = "", advance_makeup(staff, plan, rows, view)
    for x in mk:
        if x["left"] <= 0:
            continue
        kind = "loan" if x["lane"] == "loan" else "advance"
        what = (("%s of %s" % (kind, _dmy(x["date"]))) if x["left"] == x["amount"] else
                ("left on the %s of %s (%s)" % (kind, _dmy(x["date"]), _rsn(x["amount"]))))
        li += "<li>%s &mdash; %s &mdash; %s</li>" % (_rsn(x["left"]), what, x["when"])
    _int = sum(x["interest"] for x in mk)
    note = ("<small>%s of the cut is interest, so what is owed falls by %s.</small><br>" % (
        _rsn(_int), _rsn(sum(x["cut"] for x in mk)))) if _int else ""
    return note + (("<ul style='margin:2px 0 4px 18px;padding:0'>%s</ul>" % li) if li else "")


def entry_position(staff, plan, rows=None, view=None):
    """S614: the New entry page's box for one person -- every open advance (date, amount, left, when cut), what the
    next close cuts, and the advances still waiting for approval. Display only."""
    rows = rows if rows is not None else load_ledger()
    mw = _month_words(plan["month"])
    lines = []
    for x in advance_makeup(staff, plan, rows, view):
        if x["lane"] == "loan" and (x["cut"] or x["interest"]):
            w = "%s off the loan at the %s close (+ %s interest), then %s left &mdash; %s a month" % (
                _rsn(x["cut"]), mw, _rsn(x["interest"]), _rsn(x["left"]), _rsn(x["instalment"]))
        elif x["cut"] and x["left"] <= 0:
            w = (("cut in full at the %s close" % mw) if x["left_now"] >= x["amount"] else
                 ("the last %s cut at the %s close" % (_rsn(x["cut"]), mw)))
        elif x["cut"]:
            w = "%s at the %s close, then %s left &mdash; %s" % (_rsn(x["cut"]), mw, _rsn(x["left"]), x["when"])
        else:
            w = x["when"]
        lines.append("%s &middot; %s &middot; <b>%s left</b> &middot; %s" % (
            _dmy(x["date"]), _rsn(x["amount"]), _rsn(x["left_now"]), w))
    if plan.get("error") and not plan.get("closed"):
        cut = "<i>could not be worked out (%s)</i>" % _hesc(str(plan["error"])[:120])
    else:
        pm_ = plan_for_staff(staff, plan, rows)
        cut = "<b>%s</b>" % _rsn(pm_["take"]) + ((" (of it %s interest)" % _rsn(pm_["interest"]))
                                               if pm_.get("interest") else "")
    _pr = [r for r in rows if r["category"] == "ADVANCE_ISSUE" and r["status"] == "PENDING" and r["staff"] == staff
           and int(r["amount"]) > 0]
    pend = ["%s &middot; %s" % (_dmy(r.get("date_from") or ""), _rsn(r["amount"])) for r in _pr]
    pendm = {}                                              # what of a month's booking is still waiting (quota rule)
    for r in _pr:
        if not r.get("interest") and r.get("against_month"):
            pendm[r["against_month"]] = pendm.get(r["against_month"], 0) + int(r["amount"])
    return {"open": lines, "cut": cut, "cut_month": mw, "pend": pend, "pendm": pendm}


def statement_months_html(staff, month=None):
'''

EDITS = [
    # 1 -- the helpers, just above the statement's month blocks
    ('def statement_months_html(staff, month=None):\n', HELPERS),
    # 2 -- the statement's top box: the make-up of "Advance remaining after <month>"
    ('        _topbox = (f"<div class=\'card\' style=\'border:2px solid #2e6b34\'><b>Advances &mdash; {staff}</b><br>"',
     '        try:                                                      # S614 (D753): what the remaining is made of\n'
     '            _mk_html = makeup_html(staff, _plan)\n'
     '        except Exception:                                         # noqa: BLE001\n'
     '            _mk_html = ""\n'
     '        _topbox = (f"<div class=\'card\' style=\'border:2px solid #2e6b34\'><b>Advances &mdash; {staff}</b><br>"'),
    ('                  + ("" if _plan["closed"] else f"Advance remaining after {_mw}: <b>{_rs(_left)}</b><br>")\n',
     '                  + ("" if _plan["closed"] else f"Advance remaining after {_mw}: <b>{_rsn(_left)}</b><br>")\n'
     '                  + _mk_html\n'),
    ('            _cut = "<b>%s</b>" % _rs(_mine["take"])', '            _cut = "<b>%s</b>" % _rsn(_mine["take"])'),
    ('                  f"Advance remaining now: <b>{_rs(_outst)}</b><br>"', '                  f"Advance remaining now: <b>{_rsn(_outst)}</b><br>"'),
    ('                  + ("<small>This is what the month-end close will cut. If the salary cannot cover it all, the rest "',
     '                  + ("<small>The lines under \'To be cut\' are what the month-end close will take. If the salary cannot cover it all, the rest "'),
    # 4 -- New entry: the position box's data, for every staff member (a doctor's page only)
    ('        posmeta = {}\n'
     '        if is_checker:\n'
     '            advs_all = open_advances()\n'
     '            cur_m = datetime.date.today().strftime("%Y-%m")\n'
     '            for s in staff_names():\n'
     '                sa = [a for a in advs_all if a["issue"]["staff"] == s]\n'
     '                if not sa: continue\n'
     '                posmeta[s] = {\n'
     '                    "loan": sum(a["balance"] for a in sa if a["interest"]),\n'
     '                    "free": sum(a["balance"] for a in sa if not a["interest"]),\n'
     '                    "skips": [x["date_from"] for x in fy_skips(s, cur_m)],\n'
     '                }\n',
     '        posmeta = {}\n'
     '        if is_checker:\n'
     '            advs_all = open_advances()\n'
     '            cur_m = datetime.date.today().strftime("%Y-%m")\n'
     '            _rows_p = load_ledger()                                # S614 (D753): every open advance, one by one\n'
     '            try:\n'
     '                _pl_p = month_plan()\n'
     '                _vw_p = loans_view(_rows_p, _pl_p["month"])\n'
     '            except Exception as _ex:                                # noqa: BLE001\n'
     '                _pl_p = {"month": next_close_month(_rows_p), "closed": False, "rows": [], "error": str(_ex)}\n'
     '                _vw_p = None\n'
     '            for s in staff_names():\n'
     '                sa = [a for a in advs_all if a["issue"]["staff"] == s]\n'
     '                posmeta[s] = {\n'
     '                    "loan": sum(a["balance"] for a in sa if a["interest"]),\n'
     '                    "free": sum(a["balance"] for a in sa if not a["interest"]),\n'
     '                    "skips": [x["date_from"] for x in fy_skips(s, cur_m)],\n'
     '                }\n'
     '                try:\n'
     '                    posmeta[s].update(entry_position(s, _pl_p, _rows_p, _vw_p))\n'
     '                except Exception as _ex:                            # noqa: BLE001\n'
     '                    posmeta[s].update({"open": [], "pend": [], "pendm": {}, "cut_month": _month_words(_pl_p["month"]),\n'
     '                                       "cut": "<i>could not be worked out</i>"})\n'
     '        _pjs = json.dumps(posmeta if is_checker else {}).replace("</", "<" + chr(92) + "/")   # S614: F-973\n'),
    # 5 -- what is booked against a month: this month and the next three (the same advance_month_taken)
    ('                               "taken": {_m0: advance_month_taken(_s, _m0, _rows_now),\n'
     '                                         _m1: advance_month_taken(_s, _m1, _rows_now)}}\n',
     '                               "taken": {_mx: advance_month_taken(_s, _mx, _rows_now)   # S614: + two more\n'
     '                                         for _mx in sorted({_m0, _m1, _month_plus(_m0, 2), _month_plus(_m0, 3)})}}\n'),
    # 6 -- F-973: "{{}}" inside an f-string's expression is not doubled -- it reached the page as `{{}}`
    ('        var P = {json.dumps(posmeta) if is_checker else "{{}}"};\n',
     '        var P = {_pjs};\n'),
    # 7 -- the box: the open advances one by one, the close's cut, the month's booking and the room under the ceiling
    ('          el.innerHTML = "<b>" + stf.value + " — current position</b><br>"\n'
     '            + (p.loan ? "Interest-bearing loan outstanding: <b>Rs " + p.loan\n'
     '                        + "</b> · skips this FY: " + p.skips.length + "/{SKIPS_PER_FY}"\n'
     '                        + (p.skips.length ? " (" + p.skips.join(", ") + ")" : "") + "<br>" : "")\n'
     '            + (p.free ? "Interest-free outstanding: <b>Rs " + p.free + "</b><br>" : "")\n',
     '          var amv = document.getElementById("am");               // S614 (D753)\n'
     '          var mon = (amv && amv.value) || new Date().toISOString().slice(0, 7);\n'
     '          var mwd = new Date(+mon.slice(0, 4), +mon.slice(5, 7) - 1, 1)\n'
     '                      .toLocaleString("en-US", {{month: "long", year: "numeric"}});\n'
     '          var fm = function (n) {{ return Number(n).toLocaleString("en-US"); }};\n'
     '          var a = A[stf.value], bk = "";\n'
     '          if (a && !a.enforced) {{\n'
     '            bk = "No ceiling: no base salary on file for " + stf.value + ".";\n'
     '          }} else if (a) {{\n'
     '            var tk = a.taken[mon], wt = (p.pendm || {{}})[mon] || 0;\n'
     '            bk = (tk === undefined)\n'
     '              ? "Booked against " + mwd + ": worked out exactly at save · ceiling Rs " + fm(a.ceiling)\n'
     '              : "Already booked against " + mwd + ": <b>Rs " + fm(tk) + "</b>"\n'
     '                + (wt ? " (includes Rs " + fm(wt) + " waiting for approval)" : "")\n'
     '                + (tk > a.ceiling ? " · <b style=\'color:#f59e0b\'>over the ceiling by Rs " + fm(tk - a.ceiling) + "</b>"\n'
     '                                  : " · room under the ceiling: <b>Rs " + fm(a.ceiling - tk) + "</b>")\n'
     '                + " (ceiling Rs " + fm(a.ceiling) + ")";\n'
     '          }}\n'
     '          var op = p.open || [], pd = p.pend || [];\n'
     '          el.innerHTML = "<b>" + stf.value + " — current position</b><br>"\n'
     '            + (op.length ? "Open advances (" + op.length + "):<ul style=\'margin:2px 0 4px 18px;padding:0\'><li>"\n'
     '                           + op.join("</li><li>") + "</li></ul>" : "No open advance.<br>")\n'
     '            + (pd.length ? "Waiting for approval: " + pd.join(", ") + "<br>" : "")\n'
     '            + (p.cut_month ? "The " + p.cut_month + " close will cut: " + p.cut + "<br>" : "")\n'
     '            + (p.loan ? "Skips this FY: " + p.skips.length + "/{SKIPS_PER_FY}"\n'
     '                        + (p.skips.length ? " (" + p.skips.join(", ") + ")" : "") + "<br>" : "")\n'
     '            + (bk ? bk + "<br>" : "")\n'),
    # 8 -- the box follows the chosen month
    ('        if (amEl) amEl.addEventListener("change", advline);\n',
     '        if (amEl) amEl.addEventListener("change", advline);\n'
     '        if (amEl) amEl.addEventListener("change", staffpos);     // S614\n'
     '        staffpos();\n'),
    ('APP_VERSION = "4.1-S612-STATEMENT"', 'APP_VERSION = "4.2-S614-MAKEUP"'),
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
        s = s.replace(old, new)
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
