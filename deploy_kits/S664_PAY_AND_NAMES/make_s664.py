"""make_s664.py -- kit S664_PAY_AND_NAMES (Sanjeevni session S359, 26-Oct-2026). The owner's "Do all 5" (18:04 IST): the S335 list, its code part.
  /root/finance/supplier_msg.py  f208d2b5 -> TO  3 edits  F-702's residue: the backup Bhejo on the Vendor payments page asks first when the
        message was already handed to the reception phone (handed_at) -- it may still go from there; Cancel sends nothing
  /root/finance/bank_sms.py      4ddbdd16 -> TO  1 edit   the NEFT portion of a month counts only the lines with something to pay, as the bank
        advice does (_advice_rows_s265 skips payable <= 0); a negative payable no longer lowers the figure the bank SMS is matched against
  /root/finance/purchase_app.py  82654e0c -> TO  4 edits  (on S662's bytes) the S446 page and the owner's Needs-you line say "Scan reading", not
        "Sarvam": Claude reads the pharmacy bills and Sarvam is off by his setting (D747); nothing it counts changes
Usage: python make_s664.py <live root, e.g. /root> <out dir>   (writes <out>/finance/...)"""
import hashlib, os, sys

FROM = {
    "finance/supplier_msg.py": "f208d2b52abf866eda6a138c266ec1f8",
    "finance/bank_sms.py": "4ddbdd16acb4d8198a2f7111b960c43c",
    "finance/purchase_app.py": "82654e0c6e8f18225067bd04fc4329ea",
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


M = "finance/supplier_msg.py"
# ---- E1 the message list carries handed_at (ensure() adds the column; never to_number, never body) ------------------------------------
rep(M, "last_error, last_try_at FROM supplier_msg\"\n", "last_error, last_try_at, handed_at FROM supplier_msg\"   # S664: + handed_at\n")
# ---- E1a the Bhejo button carries, when the message was handed to the phone, the question to ask first ------------------------------
rep(M, """'<button class="sm" onclick="msgSend407(%d)">Bhejo</button>' % m["id"] if sender else""",
    """'<button class="sm" onclick="msgSend407(%d,this)"%s>Bhejo</button>' % (m["id"], _s664_handed(m, owner)) if sender else""")
rep(M, """function msgSend407(id){fetch(P+'/api/supplier-msg/send'""",
    """function msgSend407(id,b){var t=b&&b.getAttribute('data-handed');if(t&&!confirm(t))return;fetch(P+'/api/supplier-msg/send'""")
T[M] = T[M].rstrip("\n") + '''


# ---- S664 (F-702's residue, 26-Oct-2026): the backup Bhejo asks first when the message was already handed to the reception phone ----
def _s664_handed(m, owner):
    """' data-handed="..."' -- the question the Bhejo button asks before sending -- when the reception phone was handed this message; else ''."""
    h = m.get("handed_at") if hasattr(m, "get") else None
    if not h:
        return ""
    when = "%s %s" % (_dmy(h), str(h)[11:16])
    q = ("This message was handed to the reception phone on %s and may still go from there. Send it from here as well?" % when if owner
         else "Yeh message %s ko reception phone ko diya gaya tha — wahan se bhi ja sakta hai. Phir bhi yahan se bhejein?" % when)
    return ' data-handed="%s"' % _esc(q)
'''

B = "finance/bank_sms.py"
# ---- E2 the NEFT portion = the advice's lines (payable > 0) ------------------------------------------------------------------------------
rep(B, """        return int(sum(g["payable_p"] for g in groups if g["route"] == "NEFT"))""",
    """        return int(sum(g["payable_p"] for g in groups if g["route"] == "NEFT" and g["payable_p"] > 0))   # S664: as the advice (payable > 0)""")

A = "finance/purchase_app.py"
# ---- E3 Scan reading, not Sarvam (D747) ------------------------------------------------------------------------------------------------
rep(A, 'text="Sarvam trial (Marg overrules until %s) -- %s"', 'text="Scan reading trial (Marg overrules until %s) -- %s"')
rep(A, '<h2>Sarvam against Marg (trial until %s: Marg overrules)</h2>', '<h2>Scan reading against Marg (trial until %s: Marg overrules)</h2>')
rep(A, "body = ('<h1>Sarvam against Marg — %s</h1><div class=\"muted\">%s. Each cell: what Sarvam read / what Marg holds. ",
    "body = ('<h1>Scan reading against Marg — %s</h1><div class=\"muted\">%s. Each cell: what the scan reader read / what Marg holds. ")
rep(A, 'return _page("Sarvam against Marg — %s" % _month_name(month), body)', 'return _page("Scan reading against Marg — %s" % _month_name(month), body)')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))
