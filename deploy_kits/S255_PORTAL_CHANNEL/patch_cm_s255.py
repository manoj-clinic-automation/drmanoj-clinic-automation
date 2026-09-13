#!/usr/bin/env python3
"""S255_PORTAL_CHANNEL -- clinic_money.py.
D510: portal money (Docterz Wallet / Patient APP / Net Banking = Razorpay) settles to Yes Bank and
is never in the ICICI MPR. The reconciler used to expect it there, hold it as "not in the bank yet"
for two banking days and then flag it to the owner as money that "never reached the ICICI account".

After this patch the reconciler subtracts portal money from what it expects of the bank, keeps it
out of the pairing, and says what it actually is -- one explained line per payment, exactly as
channel 5 (other UPI) is handled. The month card gains the channel as its own row.
Nothing changes for revenue: the day's total, the counter-vs-Docterz comparison and every tender
figure are untouched.
"""
import io, sys

SRC = sys.argv[1]; DST = sys.argv[2]
s = io.open(SRC, encoding="utf-8").read()
n = 0

def sub(old, new):
    global s, n
    c = s.count(old)
    if c != 1:
        raise SystemExit("ANCHOR COUNT %d (expected 1):\n%s" % (c, old[:140]))
    s = s.replace(old, new); n += 1

# 1 -- the channel split, beside the existing constant
sub('ONLINE_MODES = ("Online Payment", "Net Banking", "Patient APP", "Wallet")\n',
    'ONLINE_MODES = ("Online Payment", "Net Banking", "Patient APP", "Wallet")\n'
    '# S255 D510: three of those four are Razorpay. The receipt goes to the owner\'s personal Gmail\n'
    '# and the money settles to the Yes Bank current account -- so it is NEVER in the ICICI MPR this\n'
    '# page reads. "Online Payment" is the counter\'s own ICICI UPI and is.\n'
    'PORTAL_MODES = ("Net Banking", "Patient APP", "Wallet")\n'
    '\n\n'
    'def _channel_of(mode):\n'
    '    """"portal" (Razorpay -> Yes Bank) or "icici" (the counter\'s UPI, in the MPR)."""\n'
    '    return "portal" if (mode or "").strip() in PORTAL_MODES else "icici"\n')

# 2 -- tag the online legs of split bills
sub('''            out["online"].append(dict(patient="", clinic_id=l["clinic_id"], amount_p=l["amount_p"],
                                      how="%s (part of split bill %s)" % (t, l["invoice_no"] or "")))
''',
    '''            out["online"].append(dict(patient="", clinic_id=l["clinic_id"], amount_p=l["amount_p"],
                                      channel=_channel_of(t),
                                      how="%s (part of split bill %s)" % (t, l["invoice_no"] or "")))
''')

# 3 -- tag the plain online bills
sub('            out["online"].append(dict(patient=r["patient"], clinic_id=r["clinic_id"], amount_p=p, how=m))\n',
    '            out["online"].append(dict(patient=r["patient"], clinic_id=r["clinic_id"], amount_p=p,\n'
    '                                      how=m, channel=_channel_of(m)))\n')

# 4 -- pass 4: portal money leaves the bank expectation and explains itself
sub('''    expected_bank = d_t["upi"] - other
    res["expected_bank_p"] = expected_bank
    ours = list(doc["online"])
''',
    '''    portal_rows = [o for o in doc["online"] if o.get("channel") == "portal"]
    portal_p = sum(o["amount_p"] for o in portal_rows)
    res["portal_p"] = portal_p
    expected_bank = d_t["upi"] - other - portal_p          # S255 D510: Razorpay settles to Yes Bank
    res["expected_bank_p"] = expected_bank
    ours = [o for o in doc["online"] if o.get("channel") != "portal"]
    for o in portal_rows:                                  # channel 4, explained before the bank is read
        who = "%s%s" % (o.get("patient") or "entry", (" · ID " + o["clinic_id"]) if o.get("clinic_id") else "")
        expl("portal", o["amount_p"], "₹%s (%s, %s) is a portal payment — Razorpay settles it to the Yes Bank "
             "account, so it is never in the ICICI file. Awaiting the Razorpay record."
             % (_r(o["amount_p"]), who, o["how"]))
''')

# 5 -- the numbers table says what it now subtracts
sub('<p class="mut">Bank expects = Docterz online − other UPI (₹%s). Bank: %s%s.</p>',
    '<p class="mut">Bank expects = Docterz online − other UPI (₹%s) − portal money (Razorpay → Yes Bank). Bank: %s%s.</p>')

# 6 -- the month card gains the channel as its own row (one placeholder, one argument)
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

# 7 -- the month figure itself, from the same two tables the day reads
sub('''# ---------------------------------------------------------------- channel 5: other UPI
''',
    '''# ------------------------------------------------------------ channel 4: portal (Razorpay)
def _portal_month_row(con, first, last):
    """One table row for the month's portal money. Same two sources as the day: plain bills in
    clinic_day_line and the legs of split bills in clinic_day_tender. Returns "" if there is none,
    so a clinic that never takes a portal payment never sees the row."""
    q = ",".join("?" * len(PORTAL_MODES))
    total, count = 0, 0
    for table, col in (("clinic_day_line", "mode"), ("clinic_day_tender", "tender")):
        if not _table(con, table):
            continue
        try:
            r = con.execute("SELECT COALESCE(SUM(amount_p),0) AS s, COUNT(*) AS c FROM %s "
                            "WHERE business_date BETWEEN ? AND ? AND %s IN (%s)" % (table, col, q),
                            (first, last) + PORTAL_MODES).fetchone()
            total += r["s"] or 0
            count += r["c"] or 0
        except Exception:                                  # noqa: BLE001
            pass
    if not total and not count:
        return ""
    return ('<tr><th class="sec">Portal (Razorpay → Yes Bank)</th><td class="r">₹ %s</td>'
            '<td>%d payment%s · no independent record yet — the receipt is in the owner\\'s personal '
            'Gmail and the money settles to Yes Bank</td></tr>'
            % (_r(total), count, "s" if count != 1 else ""))


# ---------------------------------------------------------------- channel 5: other UPI
''')

io.open(DST, "w", encoding="utf-8", newline="").write(s)
print("anchors applied:", n)
