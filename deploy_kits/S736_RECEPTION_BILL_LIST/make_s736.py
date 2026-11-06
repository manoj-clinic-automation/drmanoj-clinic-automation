#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s736.py -- S736_RECEPTION_BILL_LIST: the counted edits and the appended sections of the three live files of this project.
    python3 -B make_s736.py <dir holding porders_s454.py, scan_register.py, purchase_app.py> <out dir> [<dir holding the S736 sections>]
Each FROM file must carry its pinned md5; every anchor must stand EXACTLY ONCE; the TO md5s are printed. The sections are read from
sec_p4.txt, sec_sr.txt beside this script (or the third argument)."""
import hashlib
import os
import sys

FROM = {"porders_s454.py": "8fd445b3b9abb24deaf2590c32bf3ea1",      # S711's TO (live 06-Nov 08:42)
        "scan_register.py": "57ca3088c53c117543ea886869eb3b61",     # S726's TO (live 06-Nov 17:59)
        "purchase_app.py": "4b6ea0832a5d484426f8f4669efbd3df"}      # S726's TO

E_P4 = [
# 1 -- the home: the server's asking runs before the counts; reception's logins see ONE row, Aaj ka bill kaam
('''    _every_read(con)
    c = counts(con)
    nm = ""
''',
'''    _every_read(con)
    if _s618_doer(con, str(login).lower()):                   # S736 (D847): the server asks reception for a rescan by itself -- on reception's home
        _s736_raise_soft(con)
    c = counts(con)
    nm = ""
'''),
('''    if c.get("rescan") and _s618_doer(con, str(login).lower()):   # S618: Phir se scan karo, directly above Bill scan karna hai -- the reception logins only
        rows = rows[:3] + (("rescan", P + "/s454/rescan", "r_rescan"),) + rows[3:]
''',
'''    s736_ok = False
    if _s618_doer(con, str(login).lower()):                   # S736 (D847): the reception logins -- ONE row, Aaj ka bill kaam (rescans, papers,
        c, s736_ok = _s736_home(con, c)                       # bills to scan, bill questions); Photo dekh kar bataiye keeps the other questions
        if s736_ok:
            rows = rows[:3] + (("billkaam", P + "/s454/billkaam", "r_billkaam"), ("q", P + "/s454/q?nobill=1", "r_q"))
    if not s736_ok and c.get("rescan") and _s618_doer(con, str(login).lower()):   # S618: Phir se scan karo, directly above Bill scan karna hai -- the reception logins only
        rows = rows[:3] + (("rescan", P + "/s454/rescan", "r_rescan"),) + rows[3:]
'''),
# 2 -- Photo dekh kar bataiye opened from reception's home: the bill questions are on Aaj ka bill kaam
('''    qs = questions(con, "parked" if month else "counted", month)
    back = (P + "/s454/purana/" + month) if month else P
    if not qs:
''',
'''    qs = questions(con, "parked" if month else "counted", month)
    if request.args.get("nobill") == "1" and not month:      # S736: reception's home row -- the bill questions are on Aaj ka bill kaam
        qs = [q for q in qs if q["kind"] != "bill"]
    back = (P + "/s454/purana/" + month) if month else P
    if not qs:
'''),
# 3 -- Shavez's Scans to redo: the server asks first; the scans after two tries are his and the owner's
('''    """Scans to redo (the owner, English; the askers, Roman Hindi). Writes nothing."""
''',
'''    """Scans to redo (the owner, English; the askers, Roman Hindi). S736: the server's asking runs first (scan_rescan_ask rows, audited)."""
'''),
('''    who = "owner" if en else "shavez"
    x = rescan_list(con)
    h = ['<div class="mut">%s</div>' % L(en, "redo_top")]
''',
'''    who = "owner" if en else "shavez"
    _s736_raise_soft(con)                                      # S736 (D847): the bad scans of a counted month are already with reception
    x = rescan_list(con)
    h = ['<div class="mut">%s</div>' % L(en, "redo_top")]
    h.append(_s736_escalated_html(con, en))                    # S736: rescanned twice and still in trouble -- his and the owner's
'''),
]

E_PA = [
# 1 -- the owner's taps on the step view (owner-only, as the page itself)
('''    return _s726_check_page(_db(), u)
# ---- S726 end -----------------------------------------------------------------------------------------------------------------------------
''',
'''    return _s726_check_page(_db(), u)
# ---- S726 end -----------------------------------------------------------------------------------------------------------------------------


# ---- S736 (06-Nov-2026, Sanjeevni session 396, kit S736_RECEPTION_BILL_LIST; D840, D847): the owner's taps on the step view --------------
@bp.route("/api/s736/decide", methods=["POST"])
def api_s736_decide():
    """Second look (the paper's figure stands / the scan misread), Accept (a scan after two tries), Undo -- scan_register.s736_decide.
    The checker who is the doctor only, as /page/check."""
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):
        return _refuse("This is for the doctor only.")
    con = _db()
    b = request.get_json(silent=True) or {}
    try:
        ok, msg = _s454_sr().s736_decide(con, _who(u), b)
    except Exception as e:                                     # noqa: BLE001
        return jsonify(ok=False, error="failed", message=str(e)[:160]), 500
    return jsonify(ok=ok, message=msg), (200 if ok else 409)
# ---- S736 end -----------------------------------------------------------------------------------------------------------------------------
'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(name, text, edits):
    for i, (old, new) in enumerate(edits, 1):
        n = text.count(old)
        if n != 1:
            sys.exit("REFUSED: %s edit %d anchor found %d times (must be once)" % (name, i, n))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sd, od = sys.argv[1], sys.argv[2]
    secd = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    src = {}
    for n, pin in FROM.items():
        b = open(os.path.join(sd, n), "rb").read()
        if md5(b) != pin:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (n, md5(b)[:8], pin[:8]))
        src[n] = b.decode("utf-8")
    sec_p4 = open(os.path.join(secd, "sec_p4.txt"), encoding="utf-8").read()
    sec_sr = open(os.path.join(secd, "sec_sr.txt"), encoding="utf-8").read()
    out = {}
    p4 = edit("porders_s454.py", src["porders_s454.py"], E_P4)
    if not p4.endswith("\n"):
        sys.exit("REFUSED: porders_s454.py does not end in a newline")
    out["porders_s454.py"] = p4 + sec_p4
    sr = src["scan_register.py"]
    if not sr.endswith("\n"):
        sys.exit("REFUSED: scan_register.py does not end in a newline")
    out["scan_register.py"] = sr + sec_sr
    out["purchase_app.py"] = edit("purchase_app.py", src["purchase_app.py"], E_PA)
    os.makedirs(od, exist_ok=True)
    for n in ("porders_s454.py", "scan_register.py", "purchase_app.py"):
        b = out[n].encode("utf-8")
        open(os.path.join(od, n), "wb").write(b)
        print("%s  %s -> %s" % (n, FROM[n][:8], md5(b)))


if __name__ == "__main__":
    main()
