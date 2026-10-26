"""make_s662.py -- kit S662_SMALL_LIST (Sanjeevni session S359, 26-Oct-2026). The owner's "Do all 5" (18:04 IST) on the small list:
  /root/finance/porders.py       3209d0a2 -> TO  2 edits  F-987's residual: a rescan whose paper amount equals the amount the bill is ALREADY
        marked WRONG at stands with that verdict (amount_state marg_wrong, nothing written to the bill) instead of going to the owner's list
  /root/finance/purchase_app.py  447b745f -> TO  3 edits  the purchase page's staff_send (the third door to any dealer, F-959's note) closed:
        the HTTP action answers 409 send_via_order_list; the page's Send on WhatsApp button and its sentence go. The internal _staff_send
        (order_rules.send_proposal, porders.api_send_med) is NOT touched.
  /root/finance/order_rules.py   8a116cbd -> TO  1 edit   a learnt lead needs 3 orders (LEAD_MIN_N); below that the default stands and no
        "learned from" is printed. Read only by reseed() -- the 1st of the month (next: 1-Nov 05:30). Nothing else reads it.
  /root/finance/section_map.py   9bf9b98f -> TO  2 edits  F-1023: DYNA (the orthotic brand) matched as a whole word, so DYNAPAR QPS PLUS
        (a medicine) is no longer an orthotic; LIST_VERSION says so
  /root/finance/stock_app.py     40f2c922 -> TO  1 edit   the same word in stock_app's own copy of the list (the S268 lists stay twins)
Usage: python make_s662.py <live root, e.g. /root> <out dir>   (writes <out>/finance/...)"""
import hashlib, os, sys

FROM = {
    "finance/porders.py": "3209d0a25839e41b9a78fee143208926",
    "finance/purchase_app.py": "447b745f16c81ef62d389900d1d8ae13",
    "finance/order_rules.py": "8a116cbda12e0e2173925c1ae73ed3f8",
    "finance/section_map.py": "9bf9b98fbfe64276b46c0a56ee9719e0",
    "finance/stock_app.py": "40f2c92260ae6b6715d49729fef464ff",
}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:80])
    T[r] = T[r].replace(old, new, 1)


P = "finance/porders.py"
# ---- E1a the bill's recorded WRONG amount is read with it ---------------------------------------------------------------------------
rep(P, 'bill = con.execute("SELECT id, supplier, bill_no, amount_p, month, verdict FROM purchase_bill WHERE id=?", (lk[0],)).fetchone()',
    'bill = con.execute("SELECT id, supplier, bill_no, amount_p, month, verdict, wrong_amount_p FROM purchase_bill WHERE id=?", (lk[0],)).fetchone()   # S662: + wrong_amount_p')
# ---- E1b F-987's residual: the same paper amount as the WRONG already on the bill stands with that verdict ---------------------------
rep(P, "    else:                                                         # neither (or the bill already carries a person's verdict / a final month): the owner\n",
    "    elif bill[5] == \"WRONG\" and bill[6] is not None and abs(paper - int(bill[6])) <= S440_TOL_P:   # S662 (F-987's residual): a rescan of a\n"
    "        # bill already marked WRONG at this very paper amount stands with that verdict -- nothing written to the bill, not the owner's line\n"
    "        _s440_put(con, sid, who, paper_amount=paper, amount_state=\"marg_wrong\")\n"
    "        _audit(con, who, \"scan_amount\", bill[0], dict(scan=sid, outcome=\"marg_wrong\", stands=True, paper_p=paper, scan_p=scan_p, marg_p=marg_p, kit=\"S662\"))\n"
    "        con.commit()\n"
    "        out = dict(outcome=\"marg_wrong\", message=\"Marg galat hai — yeh bill pehle se Amir ki list par hai.\")\n"
    "    else:                                                         # neither (or the bill already carries a person's verdict / a final month): the owner\n")

A = "finance/purchase_app.py"
# ---- E2a the HTTP door refuses; the function stays for the order list's own sends -------------------------------------------------
rep(A, '    if action == "staff_send":                       # S225: any person of the unit may send\n        return _staff_send(con, u, b)\n',
    '    if action == "staff_send":                       # S662: the third door CLOSED -- an order goes only from the one order list\n'
    '        msg = ("Orders now go from the one order list (Order karna hai), one WhatsApp per order." if _is_doctor(u)\n'
    '               else "Order ab \'Order karna hai\' list se hi jaata hai.")\n'
    '        return jsonify(ok=False, error="send_via_order_list", message=msg), 409\n')
# ---- E2b the page: no Send on WhatsApp button; Call stays --------------------------------------------------------------------------
rep(A, """            btns = ('<button class="p" onclick="sendWA(%d)">Send on WhatsApp</button> ' % i\n                    + " ".join(""",
    """            btns = (" ".join(                                            # S662: no Send button -- the order list sends\n""")
# ---- E2c the page's sentence ------------------------------------------------------------------------------------------------------
rep(A, """'<h1>Order medicines</h1><div class="muted">Stock as on %s. Tap <b>Send on WhatsApp</b> '\n            'and the order goes to the stockist as a message; it is recorded here as sent, by you, at that '\n            'minute. <b>Call</b>""",
    """'<h1>Order medicines</h1><div class="muted">Stock as on %s. Orders are not sent from this page: they go from the '\n            'one order list (<b>Order karna hai</b>), one WhatsApp per order. '\n            '<b>Call</b>""")

R = "finance/order_rules.py"
# ---- E3 a learnt lead needs three orders --------------------------------------------------------------------------------------------
rep(R, '    if not vals:\n        return None, 0\n    return int(round(statistics.median(vals))), len(vals)\n',
    '    if len(vals) < LEAD_MIN_N:                                # S662: one or two orders do not make a lead -- the default stands\n'
    '        return None, 0\n'
    '    return int(round(statistics.median(vals))), len(vals)\n\n\n'
    'LEAD_MIN_N = 3                                                # S662: orders needed before a supplier\'s own lead replaces order.lead_days\n')

S = "finance/section_map.py"
# ---- E5 F-1023: DYNA as a whole word -----------------------------------------------------------------------------------------------
rep(S, '"VISSCO", "DYNA", "BAMBOO")', '"VISSCO", " DYNA ", "BAMBOO")')   # S662 (F-1023): not inside DYNAPAR
rep(S, 'LIST_VERSION = "S268 (copied from stock_app.py of the 18-Sep-2026 bundle)"',
    'LIST_VERSION = "S268 (copied from stock_app.py of the 18-Sep-2026 bundle); S662: DYNA a whole word in both"')
K = "finance/stock_app.py"
rep(K, '"VISSCO", "DYNA", "BAMBOO")', '"VISSCO", " DYNA ", "BAMBOO")')   # S662 (F-1023): the twin list

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))
