#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s968.py -- kit S968_REGISTER_PUSH (the parent, S531, 27-Nov-2026; his "PROCEED" 10:40 IST).

Remakes the two changed files from their LIVE bytes by exact anchored replacements (each anchor must occur exactly the stated
number of times, or nothing is written):
    python3 make_s968.py <clinic_register.py> <day_check.py> <out_dir>
  clinic_register.py  (1) the three records' heading no longer says "all agree" when cash or card differ between the register
                          and Docterz (it read UPI alone); the waiting / bank-differs lines name a cash or card difference too
                      (2) a Save starts register_push.py for that day in its own process (never waited for; REGPUSH_SPAWN=0 off)
  day_check.py        (3) the "patient not found" card asks for the parchi as well, and offers Shavez / Bhati "Parchi banayein"
The third file, register_push.py, is NEW (the kit's to/ holds it whole).
"""
import hashlib
import os
import sys


def rep(src, old, new, n=1, what=""):
    k = src.count(old)
    if k != n:
        raise SystemExit("REFUSED: anchor %r found %d times, expected %d" % (what or old[:60], k, n))
    return src.replace(old, new)


SPAWN = '''

def _s968_spawn(con, d):
    """S968 (27-Nov-2026, the owner): start register_push.py for the day just saved, in its own fully detached process -- never
    waited for, never a reason for the Save to fail. REGPUSH_SPAWN=0 turns it off; REGPUSH_PY names the python."""
    import os as _os                             # noqa: PLC0415
    import subprocess as _sp                     # noqa: PLC0415
    import sys as _sys                           # noqa: PLC0415
    if _os.environ.get("REGPUSH_SPAWN", "1") == "0":
        return False
    try:
        here = _os.path.dirname(_os.path.abspath(__file__))
        script = _os.path.join(here, "register_push.py")
        path = con.execute("PRAGMA database_list").fetchone()[2]
        if not path or not _os.path.isfile(script):
            return False
        py = _os.environ.get("REGPUSH_PY", "/root/wa/venv/bin/python3")
        if not _os.path.isfile(py):
            py = _sys.executable
        logd = _os.path.join(here, "logs")
        _os.makedirs(logd, exist_ok=True)
        env = dict(_os.environ, REGPUSH_LOGF=_os.path.join(logd, "register_push.log"), TZ="Asia/Kolkata")
        p = _sp.Popen(["/bin/sh", "-c", '"$@" </dev/null >>"$REGPUSH_LOGF" 2>&1 &', "s968", py, "-B", script,
                       "--day", str(d), "--db", path], env=env, cwd=here, close_fds=True,
                      stdin=_sp.DEVNULL, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        p.wait(timeout=10)
        return True
    except Exception:                            # noqa: BLE001 -- the Save never fails for this
        return False
'''

VERDICT = '''    # S968 (27-Nov-2026, the owner): the heading was read off UPI alone, so a cash or card difference between the register
    # and Docterz sat under a green "all agree" (26-Nov: cash Rs 100 apart). Now the heading and its line say so.
    if reg is not None and doc["known"] and verdict in ("all agree", "waiting_bank", "bank differs"):
        _s968 = [(n, a, b) for n, a, b in (("cash", r_cash, doc["cash"]), ("card", r_card, doc["card"])) if a != b]
        if _s968:
            _s968w = "; ".join("%s: register Rs %s, Docterz Rs %s" % (n, _r(a), _r(b)) for n, a, b in _s968)
            if verdict == "all agree":
                verdict = ("%s differs" % _s968[0][0]) if len(_s968) == 1 else "cash and card differ"
                why = ("UPI agrees in all three, but the register and Docterz differ on %s — see the day's corrections below"
                       % _s968w)
            else:
                why = why + " The register and Docterz also differ on %s." % _s968w
'''


def register(s):
    s = rep(s, "\n\ndef _s636_check(con, d, u):\n", SPAWN + "\n\ndef _s636_check(con, d, u):\n", what="register spawn def")
    s = rep(s, '''    # THE DRAWER IS A FOURTH SIGNAL, and the fastest one.''',
            VERDICT + '''    # THE DRAWER IS A FOURTH SIGNAL, and the fastest one.''', what="register verdict")
    s = rep(s, '''                msg = "<div class='ok'><b>Saved.</b> %s</div>" % _esc(three_way(con, date)["why"])\n''',
            '''                msg = "<div class='ok'><b>Saved.</b> %s</div>" % _esc(three_way(con, date)["why"])\n'''
            '''                _s968_spawn(con, date)                                          # S968: Shavez and reception told by push\n''',
            what="register save")
    s = rep(s, ".pill.docterz_differs,.pill.register_differs,.pill.all_differ{background:#fadbd8}",
            ".pill.docterz_differs,.pill.register_differs,.pill.all_differ,.pill.cash_differs,.pill.card_differs,"
            ".pill.cash_and_card_differ{background:#fadbd8}", what="register css")
    return s


def daycheck(s):
    s = rep(s, '''                               en="%s — Docterz entry missing, patient not found · %s · %s" % (rs(delta[t]), SEC_EN[sec], T_EN[t]),
                               hi="%s — Docterz mein entry nahi, mareez nahi mila · %s · %s" % (rs(delta[t]), SEC_HI[sec], T_HI[t])))''',
            '''                               en="%s — Docterz entry missing, patient not found · %s · %s — find the patient: enter it in "
                                  "Docterz, and make the parchi if there is none" % (rs(delta[t]), SEC_EN[sec], T_EN[t]),   # S968
                               hi="%s — Docterz mein entry nahi, mareez nahi mila · %s · %s — mareez dhoondein: Docterz mein entry "
                                  "kijiye, parchi na ho to parchi bhi banaiye" % (rs(delta[t]), SEC_HI[sec], T_HI[t])))''',
            what="daycheck notfound words")
    s = rep(s, '''            btns.append("<a class='tb x' href='/finance/clinic/register/%s'>%s</a>" % (d, "Register mistake" if english else "Register ki galti"))\n''',
            '''            btns.append("<a class='tb x' href='/finance/clinic/register/%s'>%s</a>" % (d, "Register mistake" if english else "Register ki galti"))\n'''
            '''            if can_parchi(u) and _late_ok(d):                                # S968: money with no parchi -- the parchi too\n'''
            '''                btns.append("<a class='tb' href='/finance/slips?s=%s&day=%s'>%s</a>" % (\n'''
            '''                    "opd" if c.get("section") == "consult" else "xp", d, "Make the parchi" if english else "Parchi banayein"))\n''',
            what="daycheck notfound parchi button")
    return s


def main(a):
    if len(a) != 3:
        raise SystemExit(__doc__)
    cr, dc, out = a
    os.makedirs(out, exist_ok=True)
    made = []
    for name, src, fn in (("clinic_register.py", cr, register), ("day_check.py", dc, daycheck)):
        with open(src, "r", encoding="utf-8", newline="") as fh:
            made.append((name, fn(fh.read())))
    for name, text in made:
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("%s  %s" % (hashlib.md5(text.encode("utf-8")).hexdigest(), name))


if __name__ == "__main__":
    main(sys.argv[1:])
