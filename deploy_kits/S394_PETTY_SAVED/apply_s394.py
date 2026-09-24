#!/usr/bin/env python3
"""apply_s394.py -- kit S394_PETTY_SAVED. Makes the S394 petty_book.py from the S393 bytes (3bf8d230) by anchored
edits. The owner 24-Sep: "a 'saved' message on the screen should be useful for him ... include the entry amount,
name and transfer type, in a language he understands best". Bhati reads Hindi best: the card is in Devanagari, the
names as they were entered. Usage: python apply_s394.py <S393 petty_book.py> <out>"""
import hashlib, sys
b = open(sys.argv[1], "rb").read()
assert hashlib.md5(b).hexdigest() == "3bf8d2304c5ee8108875a606e6db03f1", "the source is not S393 petty_book.py"
s = b.decode("utf-8")


def rep(old, new):
    global s
    n = s.count(old)
    assert n == 1, "anchor found %d times: %r" % (n, old[:80])
    s = s.replace(old, new)


# 1 -- the save and the refusal say WHICH entry (its id), so the page can show it
rep('''    if con.execute("SELECT 1 FROM petty_entry WHERE void_at='' AND kind=? AND party=? AND other_name=? AND amount_p=? "
                   "AND by_whom=? AND at BETWEEN ? AND ? LIMIT 1", (kind, party, other, amt, _who(u), cut, _stamp())).fetchone():
        return redirect("/finance/petty?msg=dup")''', '''    first = con.execute("SELECT id FROM petty_entry WHERE void_at='' AND kind=? AND party=? AND other_name=? AND amount_p=? "
                        "AND by_whom=? AND at BETWEEN ? AND ? ORDER BY id LIMIT 1",
                        (kind, party, other, amt, _who(u), cut, _stamp())).fetchone()
    if first:
        return redirect("/finance/petty?msg=dup&e=%d" % first["id"])''')
rep('''                dict(kind=kind, party=party, other=other, amount_p=amt, photo=bool(photo)), _who(u))
    return redirect("/finance/petty?msg=saved")''', '''                dict(kind=kind, party=party, other=other, amount_p=amt, photo=bool(photo)), _who(u))
    return redirect("/finance/petty?msg=saved&e=%d" % cur.lastrowid)''')

# 2 -- the card
rep('''def _keeper_html(con, u, msg):''', '''KIND_HI = {"receive": ("पैसे मिले", "किससे"), "topup": ("डायरी भरी", "किसकी"), "pay": ("भुगतान किया", "किसको"),
           "loan_out": ("अपना लोन लिया", ""), "loan_back": ("अपना लोन वापस किया", "")}


def _saved_card(con, u, msg):
    """S394: after a save, a big card saying WHAT was saved -- type, name, amount, time -- in Hindi (Devanagari),
    the names as they were entered; after a refused repeat, the same card for the entry that already stands."""
    if msg not in ("saved", "dup"):
        return ""
    try:
        eid = int(request.args.get("e") or 0)
    except ValueError:
        return ""
    e = con.execute("SELECT * FROM petty_entry WHERE id=?", (eid,)).fetchone() if eid else None
    if e is None or e["by_whom"] != _who(u) or e["void_at"]:
        return ""
    what, wholabel = KIND_HI.get(e["kind"], (e["kind"], ""))
    name = _party_label(con, e, "en")
    for tail in (" gave", " diary topped up"):
        if name.endswith(tail):
            name = name[: -len(tail)]
    rows = [("क्या", "<b>%s</b>" % what)]
    if wholabel:
        rows.append((wholabel, "<b>%s</b>" % _esc(name)))
    rows.append(("रकम", "<b class='svamt'>₹ %s</b>" % _r(e["amount_p"])))
    rows.append(("कब", "%s, %s" % (_human(e["entry_date"]), (e["at"] or "")[11:16])))
    table = "<table class='svt'><tbody>%s</tbody></table>" % "".join("<tr><td>%s</td><td>%s</td></tr>" % r for r in rows)
    if msg == "saved":
        cancel = ("<form method='post' action='/finance/petty/void/%d' class='inline'><button class='clear' type='submit'>"
                  "गलती हुई — कैंसल करें</button></form>" % e["id"]) if e["entry_date"] == _today() else ""
        return "<div class='saved'><div class='sv1'>✓ सेव हो गया</div>%s%s</div>" % (table, cancel)
    return ("<div class='saved dup'><div class='sv1'>⚠ यह एंट्री पहले ही सेव है</div>%s"
            "<p>दोबारा नहीं लिखी। सच में दूसरी बार दिया हो तो 10 मिनट बाद लिखिए।</p></div>" % table)


def _keeper_html(con, u, msg):''')
rep('''    out = []
    if msg:
        out.append("<div class='%s'>%s</div>" % ("ok" if msg in ("saved", "cancelled") else "bad", MSG_HI.get(msg, "")))
    st_today = availability(con, today.isoformat())''', '''    out = []
    card = _saved_card(con, u, msg)                      # S394
    if card:
        out.append(card)
    elif msg:
        out.append("<div class='%s'>%s</div>" % ("ok" if msg in ("saved", "cancelled") else "bad", MSG_HI.get(msg, "")))
    st_today = availability(con, today.isoformat())''')

# 3 -- its look
rep('''.three td:first-child{width:40%%}''', '''.three td:first-child{width:40%%}
.saved{background:#dff0d8;border:3px solid #2c6e2f;border-radius:12px;padding:12px 14px;margin:0 0 10px;font-size:20px}
.saved.dup{background:#fff3cd;border-color:#9a6b00}
.saved .sv1{font-size:26px;font-weight:800;color:#1e5a22;margin:0 0 6px}.saved.dup .sv1{color:#7a4f00}
.svt{border-collapse:collapse}.svt td{padding:3px 14px 3px 0;vertical-align:top}.svt td:first-child{color:var(--mut)}
.svamt{font-size:26px}
.saved button.clear{font-size:18px;padding:11px 16px;margin-top:8px}''')
rep('''APP_VERSION = "S393-PETTY-BOOK-1.2"''', '''APP_VERSION = "S394-PETTY-BOOK-1.3"''')
rep('''NO JAVASCRIPT. Tables on first request''', '''S394 (24-Sep-2026) -- the owner: a 'saved' message useful to Bhati, with the amount, the name and the kind of entry,
in the language he understands best. After a save his page opens on a big green card in Hindi (Devanagari): kya /
kisko-kisse-kiski / rakam / kab, with its own cancel; a refused repeat shows the entry that already stands.

NO JAVASCRIPT. Tables on first request''')

open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("S394 petty_book.py md5", hashlib.md5(s.encode("utf-8")).hexdigest())
