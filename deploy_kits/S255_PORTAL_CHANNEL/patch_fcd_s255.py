#!/usr/bin/env python3
"""S255_PORTAL_CHANNEL -- finance_clinic_day.py.
D510: Docterz's Wallet / Patient APP / Net Banking rows are Razorpay payments. They settle to the
Yes Bank current account, never to the ICICI account whose MPR this app reads. Until today all four
online modes were one bucket, so every portal rupee was expected in the ICICI file and eventually
flagged 'never reached the ICICI account'.

This patch splits the bucket at its single source (_our_online_entries, the F-459 one place), and
gives the MPR card the ICICI-only figure. our_online_p keeps its meaning -- the day's whole online
revenue -- so nothing that reports revenue moves by a rupee.
"""
import io, sys

SRC = sys.argv[1]; DST = sys.argv[2]
s = io.open(SRC, encoding="utf-8").read()
n = 0

def sub(old, new):
    global s, n
    c = s.count(old)
    if c != 1:
        raise SystemExit("ANCHOR COUNT %d (expected 1):\n%s" % (c, old[:120]))
    s = s.replace(old, new); n += 1

# 1 -- the two channels, beside the existing constant
sub('_ONLINE_MODES = ("Online Payment", "Net Banking", "Patient APP", "Wallet")\n',
    '_ONLINE_MODES = ("Online Payment", "Net Banking", "Patient APP", "Wallet")\n'
    '# S255 D510: of those four, three are Razorpay -- they settle to Yes Bank and are never in the\n'
    '# ICICI MPR. "Online Payment" is the counter\'s own ICICI UPI and is.\n'
    '_PORTAL_MODES = ("Net Banking", "Patient APP", "Wallet")\n'
    '\n\n'
    'def _channel_of(mode):\n'
    '    """"portal" (Razorpay -> Yes Bank) or "icici" (the counter\'s UPI, in the MPR)."""\n'
    '    return "portal" if (mode or "").strip() in _PORTAL_MODES else "icici"\n')

# 2 -- tag the plain online bills
sub('            ours.append(dict(r, how=r["mode"]))\n',
    '            ours.append(dict(r, how=r["mode"], channel=_channel_of(r["mode"])))\n')

# 3 -- tag the online legs of split bills
sub('''            ours.append(dict(patient="", clinic_id=r["clinic_id"], amount_p=r["amount_p"],
                             mode=r["tender"], shift="", how="%s (part of a split bill %s)"
                             % (r["tender"], r["invoice_no"] or "")))
''',
    '''            ours.append(dict(patient="", clinic_id=r["clinic_id"], amount_p=r["amount_p"],
                             mode=r["tender"], shift="", channel=_channel_of(r["tender"]),
                             how="%s (part of a split bill %s)"
                             % (r["tender"], r["invoice_no"] or "")))
''')

# 4 -- the two derived figures, from the same one list
sub('''def our_online_p(con, date):
    """THE day's online figure (F-459).  clinic_money.py reads this too."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date))
''',
    '''def our_online_p(con, date):
    """THE day's online figure (F-459).  clinic_money.py reads this too.  Unchanged meaning: all
    online revenue, both channels.  Use our_icici_online_p when comparing against the ICICI MPR."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date))


def our_icici_online_p(con, date):
    """S255 D510: the part of the day's online money the ICICI MPR can be expected to show."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date) if o.get("channel") != "portal")


def our_portal_p(con, date):
    """S255 D510: the Razorpay part -- Wallet, Patient APP, Net Banking.  Settles to Yes Bank;
    no independent record exists for it yet (the payment-email relay is step 2 of D507)."""
    return sum(o["amount_p"] for o in _our_online_entries(con, date) if o.get("channel") == "portal")
''')

# 5 -- the MPR card compares like with like
sub('    out.append(_mpr_card(con, date, our_online_p(con, date)))          # S249 F-459: the ONE online figure\n',
    '    out.append(_mpr_card(con, date, our_icici_online_p(con, date)))    # S249 F-459 + S255 D510: ICICI-only\n')

io.open(DST, "w", encoding="utf-8", newline="").write(s)
print("anchors applied:", n)
