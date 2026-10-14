#!/usr/bin/env python3
"""make_s552.py -- kit S552_PHYSIO_REGISTER (session 313, 14-Oct-2026, D646).
Builds the new /root/finance/finance_app.py and clinic_money.py from their LIVE bytes (FROM pins below) by exact, counted,
anchored edits -- ONE each. Every new text is built in memory first; nothing is written unless both FROM pins are exact and
every anchor occurs exactly once.
    python3 -B make_s552.py <finance_app FROM> <finance_app out> <clinic_money FROM> <clinic_money out>
  finance_app.py : one guarded mount block for physio_book, placed right after the S408 packs block.
  clinic_money.py: one link at the top of the Physiotherapy page for a login with any role in unit 'physiobook'."""
import hashlib
import sys

FROM = {"app": "0d713b14570384e0de07ac93a3b113db", "money": "b0408f82ec104e2170ccc069d0ec6450"}
EDITS = {"app": 0, "money": 0}
WANT = {"app": 1, "money": 1}


class Refuse(Exception):
    pass


def once(src, old, new, f):
    n = src.count(old)
    if n != 1:
        raise Refuse("%s: anchor found %d times: %r" % (f, n, old[:90]))
    EDITS[f] += 1
    return src.replace(old, new, 1)


# ===================================================================== finance_app.py
A_ANCHOR = "# --- S408_MONTH_END_PACKS end ---\n"
A_NEW = A_ANCHOR + """
# --- S552_PHYSIO_REGISTER begin -- Bhati's physio register: clinic slips matched to reception, home visits (owner, 13/14-Oct-2026, D646) ---
# PARENT (clinic). Its own unit 'physiobook' (bhati maker; the doctors checker) inside the /finance/physio namespace, so the front
# gate still asks for a 'physio' row first. Its own physio_* tables, created on first request (F-303). Reads clinic_physio_day
# (reception's daily figures), clinic_day_line and the setting table; writes only its own tables and the setting physio_book.on.
# Home-visit money never reaches packs, the day revenue or the morning match. GUARDED (S209): a fault inside the module is
# printed and every other page keeps serving.
try:
    import physio_book                                         # noqa: E402
    physio_book.init(app, db, require, audit, unit="physiobook")
except Exception as _ex_pbk:                                   # noqa: BLE001
    _MOUNT_FAILED.append(('physio_book', repr(_ex_pbk)[:200]))
    print("physio_book NOT mounted: %s" % _ex_pbk, file=sys.stderr)
# --- S552_PHYSIO_REGISTER end ---
"""

# ===================================================================== clinic_money.py
M_ANCHOR = """    out = ["<div class='card'><h2>%s</h2><p class='mut'>%s</p>%s</div>" % (
        L["title"], L["note"], "<div class='ok'>✓</div>" if msg else "")]
"""
M_NEW = """    out = []
    try:                                         # S552 (D646): the physio register's door, for a login with any role in unit 'physiobook'
        _pb = set(r[0] for r in con.execute("SELECT role FROM unit_role WHERE unit='physiobook' AND lower(username)=lower(?) AND active=1",
                                             ((u or {}).get("user") or "",)))
    except Exception:                            # noqa: BLE001 -- no unit_role here: no link, the page as before
        _pb = set()
    if _pb:
        out.append("<div class='card'><a class='btn' href='/finance/physio/book'>%s</a>%s</div>" % (
            "Patient-wise register ›" if hindi else "Physio register ›",
            "<a class='btn' href='/finance/physio/book/report'>Report ›</a>" if "checker" in _pb else ""))
    out.append("<div class='card'><h2>%s</h2><p class='mut'>%s</p>%s</div>" % (
        L["title"], L["note"], "<div class='ok'>✓</div>" if msg else ""))
"""


def build(app_src, money_src):
    app = once(app_src, A_ANCHOR, A_NEW, "app")
    money = once(money_src, M_ANCHOR, M_NEW, "money")
    if EDITS != WANT:
        raise Refuse("edit counts %s, expected %s" % (EDITS, WANT))
    return app, money


def main(a):
    if len(a) != 4:
        print(__doc__)
        return 2
    raw = {}
    for key, path in (("app", a[0]), ("money", a[2])):
        b = open(path, "rb").read()
        h = hashlib.md5(b).hexdigest()
        if h != FROM[key]:
            print("REFUSED: %s is %s, the FROM pin is %s" % (path, h, FROM[key]))
            return 1
        raw[key] = b.decode("utf-8")
    try:
        app, money = build(raw["app"], raw["money"])
    except Refuse as ex:
        print("REFUSED: %s" % ex)
        return 1
    for text, path in ((app, a[1]), (money, a[3])):
        with open(path, "wb") as fh:
            fh.write(text.encode("utf-8"))
    print("built: finance_app.py %s (%d edit) · clinic_money.py %s (%d edit)" % (
        hashlib.md5(app.encode("utf-8")).hexdigest(), EDITS["app"], hashlib.md5(money.encode("utf-8")).hexdigest(), EDITS["money"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
