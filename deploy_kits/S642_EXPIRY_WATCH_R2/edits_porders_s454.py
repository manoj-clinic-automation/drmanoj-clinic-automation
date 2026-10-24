# S638 anchored edits for /root/finance/porders_s454.py (FROM 647f2925)
# F-1015: reception's "Order ka maal nahi aaya" names every awaited medicine, with its quantity, for an order where nothing came too.
EDITS = []
EDITS.append(('''#  page (?old=1), for the owner only. No phone number is written anywhere but on a sender's own call screen and the reception phone's message.
# =============================================================================''', '''#  page (?old=1), for the owner only. No phone number is written anywhere but on a sender's own call screen and the reception phone's message.
#  S638_EXPIRY_WATCH (24-Oct-2026, F-1015): a late card of an order where NOTHING came names every awaited medicine with its quantity
#    (Shivani, 23-Oct: "SHIVAAZ 12-10 1 medicine" told her nothing); a part order's card is as it was. Nothing else on the page moves.
# ============================================================================='''))
EDITS.append(('''    else:
        sub = L(en, "late_sub", OS.ddmm(s["created_at"]), _s619_via(en, s["via"]), s["n"])
    callb =''', '''    else:
        sub = L(en, "late_sub", OS.ddmm(s["created_at"]), _s619_via(en, s["via"]), s["n"])
    names = "" if s["part"] else _s638_awaited(con, en, s)             # S638 (F-1015): what is awaited, by name and quantity
    callb ='''))
EDITS.append(('''    return ('<div class="card" data-order="%d" data-late="1"><div><div class="nm">%s</div><div class="sb am">%s</div></div>'
            '<div class="two">%s<a class="g" href="%s/s454/maal/%d">%s</a></div></div>'
            % (s["id"], esc(s["vendor"]), esc(sub), callb, P, s["id"], L(en, "baaki_aaya" if s["part"] else "maal_aaya")))''',
              '''    return ('<div class="card" data-order="%d" data-late="1"><div><div class="nm">%s</div><div class="sb am">%s</div>%s</div>'
            '<div class="two">%s<a class="g" href="%s/s454/maal/%d">%s</a></div></div>'
            % (s["id"], esc(s["vendor"]), esc(sub), names, callb, P, s["id"], L(en, "baaki_aaya" if s["part"] else "maal_aaya")))


def _s638_awaited(con, en, s):
    """S638 (F-1015): every line of the order still awaited (open / part), each with what is awaited -- the strips, pieces or bottles
    ordered less what came, in the shop's own words (qty_words with the whole-unit list loaded, OS.whole_units; fail-soft to the bare
    figure)."""
    out = []
    for x in s.get("lines") or []:
        if x.get("state") not in ("open", "part"):
            continue
        n = max(int(x.get("packs") or 0) - int(x.get("came") or 0), 0)
        ps = int(x.get("pack_size") or 1)
        try:
            qw = OS.whole_units(con)
            q = qw.words(n * ps, pack=ps, name=x.get("item"), lang="en" if en else "hi") if qw is not None else str(n)
        except Exception:                                              # noqa: BLE001
            q = str(n)
        out.append("%s · %s" % (x.get("item") or "", q))
    return ('<div class="sb s638aw">%s</div>' % "<br>".join(esc(o) for o in out)) if out else ""'''))
