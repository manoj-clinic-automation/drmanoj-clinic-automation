#!/usr/bin/env python3
"""S257_PORTAL_EVIDENCE -- clinic_money.py.
D510: portal money is recognised by the Razorpay id on the line (clinic_day_line.gateway_ref, kept
since S256), never by the mode word. The reconciler subtracts it from what it expects of the ICICI
bank, keeps it out of the pairing, and explains each one by its id -- the same shape as channel 5
(other UPI). The month card gains the channel as a row. Revenue, the counter-vs-Docterz comparison
and every tender figure are untouched. S255 did this on the label and was rolled back (F-467/F-468).
"""
import io, sys
SRC, DST = sys.argv[1], sys.argv[2]
s = io.open(SRC, encoding="utf-8").read(); n = 0
def sub(old, new):
    global s, n
    c = s.count(old)
    if c != 1: raise SystemExit("ANCHOR COUNT %d (expected 1):\n%s" % (c, old[:140]))
    s = s.replace(old, new); n += 1

sub('ONLINE_MODES = ("Online Payment", "Net Banking", "Patient APP", "Wallet")\n',
    'ONLINE_MODES = ("Online Payment", "Net Banking", "Patient APP", "Wallet")\n'
    '\n\n'
    'def _gateway_col(con):\n'
    '    """S257: \'gateway_ref\' when clinic_day_line carries the S256 column, else a blank literal."""\n'
    '    try:\n'
    '        cols = [r[1] for r in con.execute("PRAGMA table_info(clinic_day_line)")]\n'
    '        return "gateway_ref" if "gateway_ref" in cols else "\'\' AS gateway_ref"\n'
    '    except Exception:                                  # noqa: BLE001\n'
    '        return "\'\' AS gateway_ref"\n'
    '\n\n'
    'def _channel_of(ref):\n'
    '    """S257 D510: "portal" when a Razorpay id was on the line, else "icici". Never the mode word."""\n'
    '    return "portal" if (ref or "").strip() else "icici"\n')

sub('''    rows = list(con.execute("SELECT section, sn, patient, clinic_id, amount_p, mode, shift FROM clinic_day_line "
                            "WHERE business_date=? AND section IN ('consult','xray','proc') ORDER BY section, sn", (d,)))
''',
    '''    rows = list(con.execute("SELECT section, sn, patient, clinic_id, amount_p, mode, shift, %s FROM clinic_day_line "
                            "WHERE business_date=? AND section IN ('consult','xray','proc') ORDER BY section, sn"
                            % _gateway_col(con), (d,)))
''')

sub('''            out["online"].append(dict(patient="", clinic_id=l["clinic_id"], amount_p=l["amount_p"],
                                      how="%s (part of split bill %s)" % (t, l["invoice_no"] or "")))
''',
    '''            out["online"].append(dict(patient="", clinic_id=l["clinic_id"], amount_p=l["amount_p"],
                                      channel="icici", gateway_ref="",
                                      how="%s (part of split bill %s)" % (t, l["invoice_no"] or "")))
''')

sub('            out["online"].append(dict(patient=r["patient"], clinic_id=r["clinic_id"], amount_p=p, how=m))\n',
    '            out["online"].append(dict(patient=r["patient"], clinic_id=r["clinic_id"], amount_p=p, how=m,\n'
    '                                      gateway_ref=r["gateway_ref"] or "", channel=_channel_of(r["gateway_ref"])))\n')

sub('''    expected_bank = d_t["upi"] - other
    res["expected_bank_p"] = expected_bank
    ours = list(doc["online"])
''',
    '''    portal_rows = [o for o in doc["online"] if o.get("channel") == "portal"]
    portal_p = sum(o["amount_p"] for o in portal_rows)
    res["portal_p"] = portal_p
    expected_bank = d_t["upi"] - other - portal_p          # S257 D510: Razorpay settles to Yes Bank
    res["expected_bank_p"] = expected_bank
    ours = [o for o in doc["online"] if o.get("channel") != "portal"]
    for o in portal_rows:                                  # channel 4, explained by its own id
        who = "%s%s" % (o.get("patient") or "entry", (" · ID " + o["clinic_id"]) if o.get("clinic_id") else "")
        expl("portal", o["amount_p"], "₹%s (%s) is a portal payment — Razorpay id …%s — settled to the Yes Bank "
             "account, so it is never in the ICICI file." % (_r(o["amount_p"]), who, (o.get("gateway_ref") or "")[-4:]))
''')

sub('<p class="mut">Bank expects = Docterz online − other UPI (₹%s). Bank: %s%s.</p>',
    '<p class="mut">Bank expects = Docterz online − other UPI (₹%s) − portal (Razorpay, by id). Bank: %s%s.</p>')

sub('''      <table class="grid"><tbody>
      <tr><th class="sec">Other UPI (personal phones)</th><td class="r">₹ %s</td><td>%d payment%s · %s</td></tr>
''',
    '''      <table class="grid"><tbody>
      %s
      <tr><th class="sec">Other UPI (personal phones)</th><td class="r">₹ %s</td><td>%d payment%s · %s</td></tr>
''')
sub('''        dt.date(y, mth, 1).strftime("%B"), y, prev, prev, nxt, nxt, ym,
        _r(oth_total), len(oth), "s" if len(oth) != 1 else "",
''',
    '''        dt.date(y, mth, 1).strftime("%B"), y, prev, prev, nxt, nxt, ym, _portal_month_row(con, first, last),
        _r(oth_total), len(oth), "s" if len(oth) != 1 else "",
''')

sub('''# ---------------------------------------------------------------- channel 5: other UPI
''',
    '''# ------------------------------------------------------------ channel 4: portal (Razorpay)
def _portal_month_row(con, first, last):
    """One table row for the month's portal money: every line that carries a Razorpay id.
    Returns "" when there is none, so a month without a portal payment shows no row."""
    if _gateway_col(con) != "gateway_ref":
        return ""
    try:
        r = con.execute("SELECT COALESCE(SUM(amount_p),0) AS s, COUNT(*) AS c FROM clinic_day_line "
                        "WHERE business_date BETWEEN ? AND ? AND gateway_ref != ''", (first, last)).fetchone()
    except Exception:                                  # noqa: BLE001
        return ""
    total, count = r["s"] or 0, r["c"] or 0
    if not count:
        return ""
    return ('<tr><th class="sec">Portal (Razorpay → Yes Bank)</th><td class="r">₹ %s</td>'
            '<td>%d payment%s, each with its Razorpay id · settles to Yes Bank, never in the ICICI file</td></tr>'
            % (_r(total), count, "s" if count != 1 else ""))


# ---------------------------------------------------------------- channel 5: other UPI
''')
io.open(DST, "w", encoding="utf-8", newline="").write(s)
print("anchors applied:", n)
