#!/usr/bin/env python3
"""S256_GATEWAY_REF -- docterz_day.py. Keep the Razorpay reference instead of deleting it.

Docterz appends the gateway reference to the Mode cell, e.g. "Online Payment pay_TVSzKeESCXc04L".
Verified 13-Sep-2026 against two independent sources for the same payment: the 29-Aug Day Revenue
sheet (Bindu Malhotra, ID 7961, the Rs 600 consultation and the Rs 800 procedure) and the Docterz
payment-completed email for that visit -- the same id, character for character.

Until now the parser stripped the reference and mentioned it only in a note, so the one piece of
evidence that identifies a portal payment was discarded daily. This patch keeps it on the line.
The mode is still normalised exactly as before: no bucket, total or tender moves by a rupee.
"""
import io, sys
SRC, DST = sys.argv[1], sys.argv[2]
s = io.open(SRC, encoding="utf-8").read(); n = 0
def sub(old, new):
    global s, n
    c = s.count(old)
    if c != 1: raise SystemExit("ANCHOR COUNT %d (expected 1):\n%s" % (c, old[:140]))
    s = s.replace(old, new); n += 1

sub('''                "mode": "",          # filled just below, once normalised
''',
    '''                "mode": "",          # filled just below, once normalised
                "gateway_ref": "",   # S256: the Razorpay id, when Docterz appends one
''')

sub('''            tender[m] = tender.get(m, 0) + p
            lines[-1]["mode"] = m
''',
    '''            tender[m] = tender.get(m, 0) + p
            lines[-1]["mode"] = m
            gw = _GATEWAY.search(raw_mode)                 # S256: keep it, do not discard it
            lines[-1]["gateway_ref"] = gw.group(0).strip() if gw else ""
''')

sub('''                          "patient": _s(r[1]), "clinic_id": _s(r[2]), "amount_p": 0,
                          "mode": "", "shift": _s(r[3])})
''',
    '''                          "patient": _s(r[1]), "clinic_id": _s(r[2]), "amount_p": 0,
                          "mode": "", "gateway_ref": "", "shift": _s(r[3])})
''')
io.open(DST, "w", encoding="utf-8", newline="").write(s)
print("anchors applied:", n)
