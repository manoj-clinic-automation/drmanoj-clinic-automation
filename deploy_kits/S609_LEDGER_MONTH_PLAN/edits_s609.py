#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s609.py -- kit S609 (session S331, 21-Oct-2026): the exact, counted edits that turn the live
/root/staff_ledger.py (32dfcfb9) into the S609 file.
    python3 edits_s609.py LIVE_FILE OUT_FILE [KIT_FILE]     (exit 0 only if every anchor occurs once, and = KIT_FILE)
READ ONLY on the live file.

THE OWNER, 21-Oct-2026 18:45 IST: "Surendra has taken 5k advance this month; looking at his statement, it's not
visible what instalment amount is due for deduction this month, and what total advance he has."

WHAT WAS WRONG (read from the live page and code, S331):
  * the statement listed each open advance with its own "monthly deduction Rs 2000" -- for Surendra two old
    advances each said Rs 2000, and the new one Rs 5000; nothing said the month's total or what is left after it;
  * the close does not take Rs 2000 per old advance: the waterfall takes ONE instalment (the head advance's
    Rs 2000) across them -- so the October close will take Rs 7000, not Rs 9000;
  * the Loans page's "falling due in 2026-10: Rs 8000" added each tranche's own instalment -- also not what the
    close takes.
THE FIX: the close itself gains a dry run (close_month(..., dry=True) returns the rows it WOULD write and writes
nothing -- the one rule, never a copy), and the statement and the Loans page show what that dry run says.
"""
import hashlib
import sys

EDITS = []

# 1. close_month: a dry run, the same code path ------------------------------------------------------------
EDITS.append(('''def close_month(users, checker, month):
    """month = 'YYYY-MM'. Generates ADVANCE_INSTALMENT rows, marks rows closed,
    writes approved_adjustments_<month>.csv. Idempotent: refuses a re-close."""
    if users[checker]["role"] != "checker":
        raise PermissionError("only a checker closes the month")''',
'''def close_month(users, checker, month, dry=False):
    """month = 'YYYY-MM'. Generates ADVANCE_INSTALMENT rows, marks rows closed,
    writes approved_adjustments_<month>.csv. Idempotent: refuses a re-close.

    S609: dry=True runs every lane exactly as the close does and RETURNS the system rows it would append,
    writing nothing (no row, no stamp, no CSV). The statement and the Loans page show this -- the close's own
    arithmetic, never a second copy of it."""
    if not dry and users[checker]["role"] != "checker":
        raise PermissionError("only a checker closes the month")'''))

EDITS.append(('''    def _sysrow(staff, cat, amount, ref, narr):
        append_ledger({''', '''    planned = []                                            # S609: the dry run's rows
    def _sysrow(staff, cat, amount, ref, narr):
        (planned.append if dry else append_ledger)({'''))

EDITS.append(('''    # 2. collect + stamp every approved, un-closed row
    rows = load_ledger()''', '''    if dry:                                                 # S609: nothing written
        return planned
    # 2. collect + stamp every approved, un-closed row
    rows = load_ledger()'''))

# 2. month_plan(): the next close, or a closed month's actual rows ------------------------------------------
EDITS.append(('''def perk_records(staff=None, year=None, rows=None):''', '''_PLAN_CATS = ("ADVANCE_INSTALMENT", "LOAN_INTEREST", "LOAN_CAPITALISE", "CAPACITY_HOLD")


def next_close_month(rows=None):
    """The month the next close will be: the month after the newest closed one (this month if none is closed)."""
    rows = rows if rows is not None else load_ledger()
    closed = sorted({r.get("closed_month") for r in rows if r.get("closed_month")})
    cur = datetime.date.today().strftime("%Y-%m")
    if not closed:
        return cur
    y, m = int(closed[-1][:4]), int(closed[-1][5:7])
    return "%04d-%02d" % (y + (m == 12), (m % 12) + 1)


def month_plan(month=None):
    """S609. What the close of `month` takes (or took): {"month", "closed", "rows", "error"}.
    A closed month: the system rows it actually wrote. The next open month: close_month(dry=True)."""
    rows = load_ledger()
    month = month or next_close_month(rows)
    if any(r.get("closed_month") == month for r in rows):
        got = [r for r in rows if r.get("closed_month") == month and r.get("maker") == "SYSTEM"
               and r["category"] in _PLAN_CATS and r["status"] == "APPROVED"]
        return {"month": month, "closed": True, "rows": got, "error": ""}
    if month != next_close_month(rows):
        return {"month": month, "closed": False, "rows": [], "error": "not the next month to close"}
    try:
        got = close_month({}, "preview", month, dry=True) or []
    except Exception as ex:                                       # noqa: BLE001
        return {"month": month, "closed": False, "rows": [], "error": str(ex)}
    return {"month": month, "closed": False, "rows": got, "error": ""}


def plan_for_staff(staff, plan, rows=None):
    """One person's lines of a month_plan: [{what, rs, held, issue_date, left_after}], with totals."""
    rows = rows if rows is not None else load_ledger()
    by_id = {r["id"]: r for r in rows}
    lines, take, held = [], 0, 0
    for r in plan.get("rows") or []:
        if r["staff"] != staff:
            continue
        iss = by_id.get(r.get("contra_of") or "", {})
        when = iss.get("date_from", "")
        when_s = "-".join(reversed(when.split("-"))) if when else ""
        if r["category"] == "CAPACITY_HOLD":
            import re as _re9
            m = _re9.search(r"Rs (\\d+)", r.get("narration") or "")
            amt = int(m.group(1)) if m else 0
            held += amt
            lines.append({"what": "held — the salary cannot bear it (advance of %s)" % when_s, "rs": amt, "held": True})
            continue
        if r["category"] == "LOAN_CAPITALISE":
            lines.append({"what": "added to the loan of %s (skipped / deferred month)" % when_s,
                          "rs": r["amount"], "held": True})
            continue
        amt = -int(r["amount"])
        take += amt
        if r["category"] == "LOAN_INTEREST":
            what = "interest on the loan of %s" % when_s
        else:
            import re as _re9
            m = _re9.search(r"balance after: (-?\\d+)", r.get("narration") or "")
            left = int(m.group(1)) if m else None
            what = ("advance of %s" % when_s) + ("" if left is None else
                                                 (" — clears it" if left <= 0 else " — Rs %d left on it" % left))
        lines.append({"what": what, "rs": amt, "held": False})
    return {"lines": lines, "take": take, "held": held}


def _month_words(ym):
    try:
        return datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except Exception:                                             # noqa: BLE001
        return ym


def perk_records(staff=None, year=None, rows=None):'''))

# 3. the statement: the month's deduction, the total, what is left ----------------------------------------
EDITS.append(('''        for a in st["advances"]:
            # SL4: a quota advance (explicit against_month, not a loan, default''', '''        # S609: what the month's close takes, and what is left -- by the close's own dry run
        _plan = month_plan(month if month and month <= next_close_month() else None)
        _mine = plan_for_staff(staff, _plan)
        _outst = sum(a["balance"] for a in st["advances"])
        _mw = _month_words(_plan["month"])
        _li = "".join("<li>Rs %d &mdash; %s</li>" % (l["rs"], l["what"]) for l in _mine["lines"])
        if _plan.get("error") and not _plan["closed"]:
            _cut = "<i>could not be worked out (%s)</i>" % _plan["error"][:120]
        else:
            _cut = "<b>Rs %d</b>" % _mine["take"]
        _left = max(0, _outst - (_mine["take"] if not _plan["closed"] else 0))
        advbox = (f"<div class='card' style='border:2px solid #2e6b34'><b>Advances &mdash; {staff}</b><br>"
                  f"Total advance outstanding now: <b>Rs {_outst}</b><br>"
                  f"{'Cut' if _plan['closed'] else 'To be cut'} from {_mw} salary: {_cut}"
                  + (f"<ul style='margin:4px 0 4px 18px;padding:0'>{_li}</ul>" if _li else "<br>")
                  + ("" if _plan["closed"] else f"Left after {_mw}: <b>Rs {_left}</b><br>")
                  + ("<small>Worked out by the month-close's own rules. If the salary cannot bear it all, the rest is "
                     "held and collected later, not lost.</small>" if not _plan["closed"] else
                     "<small>As taken at the close.</small>")
                  + "</div>") + advbox
        _per_adv = {}
        for _r in _plan.get("rows") or []:
            if _r["staff"] == staff and _r["category"] == "ADVANCE_INSTALMENT":
                _per_adv[_r.get("contra_of")] = _per_adv.get(_r.get("contra_of"), 0) - int(_r["amount"])
        for a in st["advances"]:
            # SL4: a quota advance (explicit against_month, not a loan, default'''))

EDITS.append(('''            advbox += (f"<div class='card'><b>Open {'loan' if a['interest'] else 'advance'}"
                       f"</b> Rs {a['issue']['amount']} ({a['issue']['date_from']})"
                       f" — balance <b>Rs {a['balance']}</b> · monthly deduction "
                       + ded + "</div>")''', '''            advbox += (f"<div class='card'><b>Open {'loan' if a['interest'] else 'advance'}"
                       f"</b> Rs {a['issue']['amount']} ({a['issue']['date_from']})"
                       f" — balance <b>Rs {a['balance']}</b> · monthly deduction "
                       + ded + f" · <b>{_mw}: Rs {_per_adv.get(a['issue']['id'], 0)}</b></div>")'''))

# 4. the Loans page: "falling due" = what the close takes -------------------------------------------------
EDITS.append(('''        d["tranches"].sort(key=lambda t: (not t["open"], not t["interest"], t["date"]))
        d["outstanding"] = sum(t["balance"] for t in d["tranches"])
        d["due"] = sum(t["due_this_month"] for t in d["tranches"])''', '''        d["tranches"].sort(key=lambda t: (not t["open"], not t["interest"], t["date"]))
        d["outstanding"] = sum(t["balance"] for t in d["tranches"])
        d["due"] = sum(t["due_this_month"] for t in d["tranches"])
    # S609: for the next close (or a closed month) "falling due" is what the close takes -- its own dry run.
    # The per-tranche instalments above added each waterfall advance's own instalment; the close takes ONE.
    try:
        _pl = month_plan(month)
    except Exception:                                             # noqa: BLE001
        _pl = {"rows": [], "error": "plan failed", "closed": False}
    if not _pl.get("error"):
        _take = {}
        for _r in _pl["rows"]:
            if _r["category"] in ("ADVANCE_INSTALMENT", "LOAN_INTEREST") and _r.get("contra_of"):
                _take[_r["contra_of"]] = _take.get(_r["contra_of"], 0) - int(_r["amount"])
        for st, d in out.items():
            for t in d["tranches"]:
                if not t["open"] and not _pl.get("closed"):
                    continue
                if _pl.get("closed") and t["id"] not in _take:
                    continue
                t["due_this_month"] = _take.get(t["id"], 0)
                if t["lane"] != "schedule" and t["open"]:
                    t["next_amount"] = t["due_this_month"]
                    t["next_month"] = month if t["due_this_month"] else t["next_month"]
            d["due"] = sum(_take.get(t["id"], 0) for t in d["tranches"])'''))

EDITS.append(('''    body += ("<p><small>“Falling due” is each loan's own instalment for the month, by the lane that recovers it "
             "(schedule · against-salary · loan · waterfall — D349). The close then applies the salary "
             "capacity check (D333): what the salary cannot bear is held, not lost. Corrections in the ledger are never "
             "deleted — a reversed advance is counted out here, not shown as a loan.</small></p>")''',
'''    body += ("<p><small>“Falling due” is what the month's close takes, worked out by the close's own rules "
             "(S609) — the old advances share ONE instalment between them, and the salary capacity check (D333) "
             "applies: what the salary cannot bear is held, not lost. Corrections in the ledger are never "
             "deleted — a reversed advance is counted out here, not shown as a loan.</small></p>")'''))

EDITS.append(('''APP_VERSION = "3.8-S247-LATE-COLLECT"''', '''APP_VERSION = "3.9-S609-MONTH-PLAN"'''))


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
