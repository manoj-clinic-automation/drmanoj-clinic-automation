#!/usr/bin/env python3
"""
finance_returns_escalate.py -- S219 M7: the owner hears about a flagged return.

THE HALF THAT WAS MISSING. When the sump flags a sale return, Darpan already
sees it: his page computes `needs` from the verdict and shows the row pending.
The OWNER never saw it unless he opened that page and looked. An alarm visible
only to the person being asked about it is not an alarm.

WHAT THIS DOES. For a day whose returns carry a REAL money flag, it opens one
`recon_exception` -- the same spine that already refuses to let a missing day
age out quietly, already carries a shout counter, and already demands a written
reason before anything closes. Nothing new to learn, nothing new to watch.

WHAT IT DELIBERATELY DOES NOT DO.

  * It never escalates "identity needed". A return attributed to a shared
    placeholder is a data-quality question for Darpan, not a money accusation
    for the owner. (S219: measured on the Marg register, 127 of 197 returns
    over five months carry no clinic ID -- escalating those would bury the
    handful that matter under a hundred that do not.)

  * It never escalates "not examinable" or "no patient attributed". Those say
    the audit COULD NOT RUN. A check must be asked what question it answers.

  * It never re-opens a day the owner has already decided on unless the SET OF
    FLAGGED BILLS HAS ACTUALLY CHANGED. A decision he made must not be undone
    by a cron; but a genuinely new flag on that day must not be swallowed by a
    resolution written before it existed. Both failures are real, and the
    stored fingerprint is what tells them apart.

  * It writes nothing but that one row. finance_returns_audit.py stays
    READ-ONLY, which is why this is a separate file at all.

ONE ROW PER DAY, by construction: recon_exception is UNIQUE on
(unit, business_date, kind), so this cannot spam however often it is called.
"""
import collections

from finance_returns_audit import returns_for_day

KIND = "return_flagged"

# The verdicts that are FINDINGS ABOUT MONEY. Every other verdict this module
# might meet -- "ok", "identity needed", "not examinable", "no patient
# attributed", "bought, quantity differs" -- is either clean or an admission
# that the audit could not run, and neither is an owner's alarm.
MONEY_FLAGS = ("NEVER BOUGHT", "REFUNDED MORE THAN PAID",
               "RETURNED MORE THAN SOLD", "DISCOUNTED RETURN")

# The three that mean somebody may be owed money back, or may owe it.
SEVERE = ("NEVER BOUGHT", "REFUNDED MORE THAN PAID", "RETURNED MORE THAN SOLD")

RECENT_DAYS = 21          # the watchdog's window; the apply hook covers the rest

# THE OWNER'S RULING OF 02-Sep-2026 -- THE PAST IS ACCEPTED. "Bury the
# historical data and take it as accepted." Nothing before this date raises an
# alarm: the rows keep their verdicts and their money, and they remain the
# baseline the detector is calibrated on, but they ask nobody for anything.
# Held in the `setting` table so he can move the line without a code change --
# a cutover written into code is one that cannot be moved when he moves it.
DEFAULT_ACT_FROM = "2026-09-02"


def act_from(con):
    """The date on and after which a flagged return is worth someone's day."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='returns.act_from'"
                        ).fetchone()
        v = (r[0] if r else "") or ""
    except Exception:                                        # noqa: BLE001
        v = ""
    return v.strip() or DEFAULT_ACT_FROM


def flagged_rows(rows):
    """The day's rows that are real money findings, in the order shown."""
    return [r for r in rows if r.get("verdict") in MONEY_FLAGS]


def _detail(rows):
    """The sentence the owner reads. BILL NUMBERS AND VERDICTS ONLY.

    No name, no clinic ID, no telephone number ever goes into recon_exception:
    the row is read on screens, logged, and copied into documents, and F-185's
    rule is 'no number at all'. The bill number is enough to find the case on
    the card, and the card is where the identity belongs.
    """
    n = len(rows)
    head = "%d sale return%s flagged on this day" % (n, "" if n == 1 else "s")
    body = "; ".join("%s %s" % (r.get("bill") or "?", r.get("verdict"))
                     for r in rows[:12])
    if n > 12:
        body += "; and %d more" % (n - 12)
    return head + " -- " + body + ". Open the SALE RETURNS card to decide each one."


def escalate_day(con, iso, unit="medical"):
    """Raise, refresh, or clear ONE exception for one day. Returns the action.

    One of: 'opened', 'updated', 're-opened', 'left-resolved', 'cleared',
    'historical', 'none'. Never raises on data -- a day that cannot be read escalates
    nothing, exactly as it did before this file existed.
    """
    if iso < act_from(con):
        return "historical"          # accepted; it asks nobody for anything
    try:
        rows, _summary = returns_for_day(con, iso, unit)
    except Exception:                                        # noqa: BLE001
        return "none"
    bad = flagged_rows(rows)
    cur = con.execute(
        "SELECT id, status, detail FROM recon_exception "
        "WHERE unit=? AND business_date=? AND kind=?", (unit, iso, KIND)).fetchone()

    if not bad:
        # Every flag on the day has gone -- corrected data, or a decision that
        # changed the verdict. An open alarm for a condition that no longer
        # holds is how people learn to ignore alarms.
        if cur is not None and cur["status"] == "open":
            con.execute("UPDATE recon_exception SET status='resolved', "
                        "resolution='no return on this day is flagged any more', "
                        "closed_by='S219_M7', closed_at=datetime('now') WHERE id=?",
                        (cur["id"],))
            return "cleared"
        return "none"

    detail = _detail(bad)
    severity = "high" if any(r["verdict"] in SEVERE for r in bad) else "medium"
    worth_p = sum(int(r.get("amount_p") or 0) for r in bad)

    if cur is None:
        con.execute(
            "INSERT OR IGNORE INTO recon_exception "
            "(unit, business_date, kind, severity, status, detail, diff_p, "
            " opened_at, shout_count) "
            "VALUES (?,?,?,?, 'open', ?, ?, datetime('now'), 0)",
            (unit, iso, KIND, severity, detail, worth_p))
        return "opened"

    if cur["status"] == "open":
        con.execute("UPDATE recon_exception SET detail=?, severity=?, diff_p=? "
                    "WHERE id=?", (detail, severity, worth_p, cur["id"]))
        return "updated"

    # Decided already. Re-open ONLY on a genuinely new set of flags.
    if (cur["detail"] or "") == detail:
        return "left-resolved"
    con.execute(
        "UPDATE recon_exception SET status='open', detail=?, severity=?, diff_p=?, "
        "resolution=NULL, closed_by=NULL, closed_at=NULL, opened_at=datetime('now') "
        "WHERE id=?", (detail, severity, worth_p, cur["id"]))
    return "re-opened"


def escalate_recent(con, unit="medical", days=RECENT_DAYS):
    """The watchdog's sweep. Bounded, and cheap: only days that HAVE returns."""
    out = collections.Counter()
    try:
        iso_days = [r[0] for r in con.execute(
            "SELECT DISTINCT business_date FROM sale_line_item "
            "WHERE unit=? AND is_return=1 AND business_date >= date('now', ?) "
            "UNION "
            "SELECT DISTINCT e.business_date FROM sale_item s "
            "JOIN day_entry e ON e.id=s.day_entry_id "
            "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' "
            "AND e.business_date >= date('now', ?) ORDER BY 1",
            (unit, "-%d days" % days, unit, "-%d days" % days)).fetchall()]
        _from = act_from(con)
        iso_days = [d for d in iso_days if d >= _from]
    except Exception:                                        # noqa: BLE001
        return dict(out)
    for iso in iso_days:
        out[escalate_day(con, iso, unit)] += 1
    return dict(out)
