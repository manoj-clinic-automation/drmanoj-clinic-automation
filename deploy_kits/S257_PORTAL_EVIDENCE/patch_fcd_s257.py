#!/usr/bin/env python3
"""S257_PORTAL_EVIDENCE -- finance_clinic_day.py.
D510: an online payment is portal (Razorpay -> Yes Bank) because it CARRIES A RAZORPAY ID, read from
clinic_day_line.gateway_ref (kept since S256) -- never because of the mode word. S255 split on the
label and was rolled back (F-467, F-468). This patch splits on the evidence, at the one F-459 source,
and keeps the MPR page's pairing list in step with the reconciler (the F-468 contradiction).
our_online_p keeps its meaning: all online revenue. Nothing that reports revenue moves.
"""
import io, sys
SRC, DST = sys.argv[1], sys.argv[2]
s = io.open(SRC, encoding="utf-8").read(); n = 0
def sub(old, new):
    global s, n
    c = s.count(old)
    if c != 1: raise SystemExit("ANCHOR COUNT %d (expected 1):\n%s" % (c, old[:140]))
    s = s.replace(old, new); n += 1

# 1 -- read the reference when the column exists; a database from before S256 reads ''
sub('''def _our_online_entries(con, date):
    """Every online entry of the day: plain online bills from clinic_day_line, plus the online legs
    of split bills from clinic_day_tender.  The MPR page pairs these; the card sums them."""
    ours = []
    try:
        for r in con.execute(
                "SELECT section, sn, patient, clinic_id, amount_p, mode, shift FROM clinic_day_line "
                "WHERE business_date=? AND mode IN (%s) ORDER BY section, sn"
                % ",".join("?" * len(_ONLINE_MODES)), (date,) + _ONLINE_MODES):
            ours.append(dict(r, how=r["mode"]))
''',
    '''def _gateway_col(con):
    """S257: 'gateway_ref' when clinic_day_line carries the S256 column, else a blank literal, so
    the query never fails on a database that has not been written to since S256."""
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(clinic_day_line)")]
        return "gateway_ref" if "gateway_ref" in cols else "'' AS gateway_ref"
    except Exception:                                             # noqa: BLE001
        return "'' AS gateway_ref"


def _channel_of(ref):
    """S257 D510: "portal" when a Razorpay id was on the line, else "icici". The mode word is never consulted."""
    return "portal" if (ref or "").strip() else "icici"


def _our_online_entries(con, date):
    """Every online entry of the day: plain online bills from clinic_day_line, plus the online legs
    of split bills from clinic_day_tender.  The MPR page pairs these; the card sums them.
    S257: each entry carries channel = portal | icici, decided by its Razorpay id (D510)."""
    ours = []
    try:
        for r in con.execute(
                "SELECT section, sn, patient, clinic_id, amount_p, mode, shift, %s FROM clinic_day_line "
                "WHERE business_date=? AND mode IN (%s) ORDER BY section, sn"
                % (_gateway_col(con), ",".join("?" * len(_ONLINE_MODES))), (date,) + _ONLINE_MODES):
            ours.append(dict(r, how=r["mode"], channel=_channel_of(r["gateway_ref"])))
''')

# 2 -- split-bill legs carry no id today: ICICI until evidence says otherwise
sub('''            ours.append(dict(patient="", clinic_id=r["clinic_id"], amount_p=r["amount_p"],
                             mode=r["tender"], shift="", how="%s (part of a split bill %s)"
                             % (r["tender"], r["invoice_no"] or "")))
''',
    '''            ours.append(dict(patient="", clinic_id=r["clinic_id"], amount_p=r["amount_p"],
                             mode=r["tender"], shift="", gateway_ref="", channel="icici",
                             how="%s (part of a split bill %s)"
                             % (r["tender"], r["invoice_no"] or "")))
''')

# 3 -- the two derived figures off the one list
sub('''def our_online_p(con, date):
    """THE day's online figure (F-459).  clinic_money.py reads this too."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date))
''',
    '''def our_online_p(con, date):
    """THE day's online figure (F-459).  clinic_money.py reads this too.  Unchanged meaning: all
    online revenue, both channels.  Use our_icici_online_p against the ICICI MPR."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date))


def our_icici_online_p(con, date):
    """S257 D510: the part of the day's online money the ICICI MPR can be expected to show."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date) if o.get("channel") != "portal")


def our_portal_p(con, date):
    """S257 D510: the Razorpay part, proven by an id on the line. Settles to Yes Bank."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date) if o.get("channel") == "portal")
''')

# 4 -- the day card compares like with like
sub('    out.append(_mpr_card(con, date, our_online_p(con, date)))          # S249 F-459: the ONE online figure\n',
    '    out.append(_mpr_card(con, date, our_icici_online_p(con, date)))    # S249 F-459 + S257 D510: ICICI-only\n')

# 5 -- the MPR page pairs the same ICICI-only list (the F-468 fix) and says what it kept out
sub('''    ours = _our_online_entries(con, date)                         # S249 F-459: the same entries as the card
''',
    '''    _all = _our_online_entries(con, date)                         # S249 F-459: the same entries as the card
    ours = [o for o in _all if o.get("channel") != "portal"]      # S257 D510 / F-468: portal never pairs here
    portal_kept_out = [o for o in _all if o.get("channel") == "portal"]
''')
sub('''    pairs, bank_only, ours_only = _mpr_pairs(bank, ours)
    bank_p = sum(b["amount_p"] for b in bank)
    ours_p = sum(o["amount_p"] for o in ours)
    diff = bank_p - ours_p
''',
    '''    pairs, bank_only, ours_only = _mpr_pairs(bank, ours)
    bank_p = sum(b["amount_p"] for b in bank)
    ours_p = sum(o["amount_p"] for o in ours)
    diff = bank_p - ours_p
    portal_note = ""
    if portal_kept_out:
        portal_note = ('<p class="mut">Kept out of this pairing: %s — portal (Razorpay) payments, settled to '
                       'Yes Bank, never in the ICICI file.</p>'
                       % " · ".join("₹ %s (%s, id …%s)" % (_rupees(o["amount_p"]), _esc(o.get("patient") or "entry"),
                                                            _esc((o.get("gateway_ref") or "")[-4:]))
                                    for o in portal_kept_out))
''')
# 7 -- render the note under the summary card
sub('''    if not day_read:
        out.append('<div class="card"><p>The clinic\\'s Docterz sheet for this day has not been read yet, '
''',
    '''    if portal_note:
        out.append(portal_note)                                   # S257: what the pairing deliberately left out
    if not day_read:
        out.append('<div class="card"><p>The clinic\\'s Docterz sheet for this day has not been read yet, '
''')
io.open(DST, "w", encoding="utf-8", newline="").write(s)
print("anchors applied:", n)
