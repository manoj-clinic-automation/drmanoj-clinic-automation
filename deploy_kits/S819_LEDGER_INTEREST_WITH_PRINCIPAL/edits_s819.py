#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s819.py -- kit S819 (session S453, 14-Nov-2026): exact, counted edits turning the live /root/staff_ledger.py
(S614, 85e2ab51) into the S819 file.     python3 edits_s819.py LIVE OUT [KIT]   (exit 0 only if all anchors occur once, = KIT)

THE OWNER'S RULING (F-1367): no interest is taken, charged or capitalised on a loan in a month unless principal
comes off the same loan that month.  ALL OR NOTHING: a month that cannot carry the whole instalment holds it
whole -- no interest, no penalty, the balance unchanged, the loan one month longer.  A month that can carry it
behaves exactly as before; the last month closes the loan as before.
  1. close_month(): when a person's waterfall carries a loan with interest and the salary cannot bear the WHOLE
     instalment, nothing is taken in the waterfall for that person that month -- no LOAN_INTEREST, no
     ADVANCE_INSTALMENT, no LOAN_CAPITALISE; what _take() spent is given back; ONE CAPACITY_HOLD row says so in
     plain words.  dry=True (S609) returns the same row.
  2. Every surface that shows the month reads that one row by ONE test (hold_whole): the statement's top box and
     month blocks, "what the remaining is made of", New entry's box, the Loans page, "Every advance", the close
     report -- the instalment held whole, no interest, the loan standing, one month longer.
UNTOUCHED: the owner's explicit skip / defer paths and their penalty (D250, D332), the order of advances before
the loan (schedule, quota, then the waterfall), interest-free advances (a part is still taken, the rest held),
every stored row.
"""
import hashlib
import sys

EDITS = [
    # 1 -- the one test every surface reads (D349: one definition, one place)
    ('_PLAN_CATS = ("ADVANCE_INSTALMENT", "LOAN_INTEREST", "LOAN_CAPITALISE", "CAPACITY_HOLD")\n',
     '_PLAN_CATS = ("ADVANCE_INSTALMENT", "LOAN_INTEREST", "LOAN_CAPITALISE", "CAPACITY_HOLD")\n'
     '# S819 (F-1367): the words that mark the hold row of a month in which a loan\'s WHOLE instalment was held --\n'
     '# written by close_month(), read by every surface that shows a month (D349: one test, one place).\n'
     'HOLD_WHOLE_MARK = "WHOLE instalment HELD"\n'
     '\n'
     '\n'
     'def hold_whole(r):\n'
     '    """True for the CAPACITY_HOLD row of a month whose whole loan instalment was held: no interest, nothing cut."""\n'
     '    return r.get("category") == "CAPACITY_HOLD" and HOLD_WHOLE_MARK in (r.get("narration") or "")\n'),
    # 2 -- plan_for_staff(): the statement's top box
    ('            held += amt\n'
     '            lines.append({"what": "held — the salary cannot bear it (advance of %s)" % when_s, "rs": amt, "held": True})\n',
     '            held += amt\n'
     '            if hold_whole(r):                                     # S819: the whole instalment, and no interest\n'
     '                _was = bool(plan.get("closed"))\n'
     '                lines.append({"what": "the whole loan instalment %s — the salary %s carry it (loan of %s): no interest, "\n'
     '                                      "nothing cut, the loan runs one month longer"\n'
     '                                      % ("was held" if _was else "is held this month", "could not" if _was else "cannot",\n'
     '                                         when_s), "rs": amt, "held": True, "whole": True})\n'
     '                continue\n'
     '            lines.append({"what": "held — the salary cannot bear it (advance of %s)" % when_s, "rs": amt, "held": True})\n'),
    # 3 -- loans_view(): each tranche knows whether its instalment is held whole this month
    ('             "app_owed": bool(r.get("special")) and not application_on_file(r["id"]),\n'
     '             "against_month": r.get("against_month") or ""}\n',
     '             "app_owed": bool(r.get("special")) and not application_on_file(r["id"]),\n'
     '             "against_month": r.get("against_month") or "", "held_now": False}\n'),
    # 4
    ('                _take[_r["contra_of"]] = _take.get(_r["contra_of"], 0) - int(_r["amount"])\n'
     '        for st, d in out.items():\n'
     '            for t in d["tranches"]:\n'
     '                if not t["open"] and not _pl.get("closed"):\n',
     '                _take[_r["contra_of"]] = _take.get(_r["contra_of"], 0) - int(_r["amount"])\n'
     '        _whole = {_r.get("contra_of") for _r in _pl["rows"] if hold_whole(_r)}          # S819\n'
     '        for st, d in out.items():\n'
     '            for t in d["tranches"]:\n'
     '                t["held_now"] = bool(t["open"] and t["id"] in _whole)\n'
     '                if not t["open"] and not _pl.get("closed"):\n'),
    # 5 -- loans_html(): the Loans page says so
    ('                    nxt = "<b style=\'color:#f87171\'>deferred this month</b>"\n'
     '                elif t["next_month"]:\n',
     '                    nxt = "<b style=\'color:#f87171\'>deferred this month</b>"\n'
     '                elif t.get("held_now"):                             # S819: all or nothing\n'
     '                    nxt = ("<b style=\'color:#f87171\'>held this month</b> <small>the salary cannot carry the whole "\n'
     '                           "instalment &mdash; nothing cut, no interest; the loan runs one month longer</small>")\n'
     '                elif t["next_month"]:\n'),
    # 6 -- close_month(): THE RULE
    ('        _wf_want = budget\n'
     '        budget = _take(staff, budget)\n'
     '        if budget < _wf_want:\n',
     '        _wf_want = budget\n'
     '        budget = _take(staff, budget)\n'
     '        # S819 (F-1367, the owner\'s ruling): NO INTEREST WITHOUT PRINCIPAL -- all or nothing. When this person\'s\n'
     '        # waterfall carries a loan with interest and the salary cannot bear the WHOLE instalment, the month holds\n'
     '        # it whole: no interest, no instalment, nothing added to the loan, the balance unchanged, the loan one\n'
     '        # month longer. What _take() spent is given back, so the capacity store reads as if nothing was asked.\n'
     '        # A waterfall of interest-free advances only is untouched (a part is still taken, the rest held).\n'
     '        if budget < _wf_want and interest_due > 0:\n'
     '            if _cap.get(staff) is not None:\n'
     '                _cap[staff] += budget\n'
     '            _sysrow(staff, "CAPACITY_HOLD", 0, advs[0]["issue"]["id"],\n'
     '                    f"Rs {_wf_want} — the {HOLD_WHOLE_MARK} for {month}: the salary cannot carry it (F-147). "\n'
     '                    f"No interest is taken and nothing is cut this month; the loan stands as it is and "\n'
     '                    f"runs one month longer (S819, F-1367)")\n'
     '            continue\n'
     '        if budget < _wf_want:\n'),
    # 7 -- close_report(): what the close did not collect
    ('            m = _re.search(r"Rs (\\d+)", r.get("narration", ""))\n'
     '            lines.append((r["staff"], f"Rs {m.group(1) if m else \'?\'} HELD — the salary could not bear it; it stays owed"))\n',
     '            m = _re.search(r"Rs (\\d+)", r.get("narration", ""))\n'
     '            if hold_whole(r):                                     # S819\n'
     '                lines.append((r["staff"], f"Rs {m.group(1) if m else \'?\'} — the WHOLE loan instalment HELD: the salary "\n'
     '                              f"could not carry it. No interest was taken; the loan runs one month longer"))\n'
     '                continue\n'
     '            lines.append((r["staff"], f"Rs {m.group(1) if m else \'?\'} HELD — the salary could not bear it; it stays owed"))\n'),
    # 8 -- month_book(): the statement's month blocks
    ('            m = _re.search(r"Rs (\\d+)", narr)\n'
     '            return {"rs": 0, "what": "held &mdash; the salary could not bear Rs %s of it (advance of %s); "\n',
     '            m = _re.search(r"Rs (\\d+)", narr)\n'
     '            if hold_whole(r):                                                # S819: the whole instalment, no interest\n'
     '                return {"rs": 0, "what": "the whole loan instalment of %s %s held (loan of %s) &mdash; the salary %s carry "\n'
     '                                         "it: no interest, nothing cut, the loan runs one month longer"\n'
     '                                         % (_rs(m.group(1)) if m else "?", "is" if run else "was", when,\n'
     '                                            "cannot" if run else "could not"), "kind": "hold"}\n'
     '            return {"rs": 0, "what": "held &mdash; the salary could not bear Rs %s of it (advance of %s); "\n'),
    # 9 -- advance_makeup(): what the remaining is made of (the statement's top section, New entry's box)
    ('        elif r["category"] == "CAPACITY_HOLD":\n'
     '            held.add(r.get("contra_of"))\n'
     '    left_of = ',
     '        elif r["category"] == "CAPACITY_HOLD":\n'
     '            held.add(r.get("contra_of"))\n'
     '    whole = {r.get("contra_of") for r in mine if hold_whole(r)}          # S819\n'
     '    left_of = '),
    # 10
    ('        elif left > 0 and t["id"] in held:\n',
     '        elif left > 0 and t["id"] in whole:                 # S819: all or nothing\n'
     '            when += (" (the whole instalment is held at the %s close &mdash; the salary cannot carry it; no interest "\n'
     '                     "this month, the loan runs one month longer)" % _month_words(pm))\n'
     '        elif left > 0 and t["id"] in held:\n'),
    # 11 -- statement_months_html(): "Every advance"
    ('                st = "to be cut in %s" % _sh(_am)\n',
     '                st = "to be cut in %s" % _sh(_am)\n'
     '            if x["open"] and x.get("held_now"):                        # S819: the whole instalment held\n'
     '                st = "held in %s &mdash; nothing cut, no interest" % _sh(v["month"])\n'),
    ('APP_VERSION = "4.2-S614-MAKEUP"', 'APP_VERSION = "4.3-S819-INTEREST"'),
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
