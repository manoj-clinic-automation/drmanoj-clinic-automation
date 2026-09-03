#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_joiner_forms_s222.py -- S222: two read-only routes the forms need.

THE OWNER, on the joiner screen: "clicking on new joiner and exit buttons opens a small prompt.
It is not contextual. The new joiner should open a form... the exit lever should open the page
where we can select from the staff and then proceed."

He is right, and it is worse than a UI complaint. `/api/open` has ALWAYS accepted the
employment type, the list of authorities and a chosen username -- they are in its signature and
its validation, and `AUTHORITIES` is a documented eight-item list of what a person may be given.
**A prompt() can only ask one thing at a time, so the page never asked, and every join since
S208 has been recorded with employment defaulted to FULLTIME and no authorities at all.** The
register was built to capture the shape of a person's job at DECIDED; the screen in front of it
threw that away.

And on the exit side: the page asked the owner to TYPE a leaver's name. This register exists
because "one person, two rows" breaks attendance and salary -- and free-typing the name is the
straightest road to it.

TWO ROUTES, BOTH READ ONLY, so the form asks the register what is true instead of hard-coding it
(the rule the role picker already follows):

    GET /finance/staff/api/authorities   what a person may be given, and the employment kinds
    GET /finance/staff/api/logins        every portal login, so the exit picker offers real
                                         people and the page can show "all the users"

Target: /root/finance/joiner_app.py   (live pin 1ebab9190a33ee9e1691508e818a7c45)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_joiner_forms_s222.py
Offline:         JA_PATH=./joiner_app.py python3 -B patch_joiner_forms_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('JA_PATH', '/root/finance/joiner_app.py')
MARK = "S222 FORMS"
EXPECT_FROM = "1ebab9190a33ee9e1691508e818a7c45"


A_OLD = '''@bp.route("/api/open", methods=["POST"])
def api_open():
'''

A_NEW = '''@bp.route("/api/authorities")
def api_authorities():
    """S222 FORMS -- what a person may be given, and the kinds of employment.

    Read from the register itself so the joiner form never hard-codes either.
    A page that invents an authority gets it silently dropped by /api/open's own
    filter; a page that reads this list cannot."""
    u, err = _require("checker")
    if err:
        return err
    return jsonify(ok=True,
                   authorities=[{"key": k, "label": AUTHORITIES[k]}
                                for k in sorted(AUTHORITIES)],
                   employment=list(EMPLOYMENT),
                   default_employment=EMPLOYMENT[0])


@bp.route("/api/logins")
def api_logins():
    """S222 FORMS -- every portal login, so a leaver is CHOSEN, never typed.

    Free-typing a leaver's name is how one person becomes two records, which is
    the exact failure this register was built to stop. Never returns a salt or a
    hash -- clinic_users.list_users() does not expose them (D176)."""
    u, err = _require("checker")
    if err:
        return err
    CU, path, why = _portal_users()
    if not CU:
        return jsonify(ok=True, store_readable=False, why=why, logins=[])
    try:
        return jsonify(ok=True, store_readable=True, store=path,
                       logins=CU.list_users(path))
    except Exception as ex:
        return jsonify(ok=True, store_readable=False,
                       why="the user store could not be read (%s)" % ex, logins=[])


@bp.route("/api/open", methods=["POST"])
def api_open():
'''


PAIRS = [("A", A_OLD, A_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit("REFUSED: this file is %s, not the %s this kit was built against. "
                         "NOTHING was changed." % (before, EXPECT_FROM))
    if "_portal_users" not in src:
        raise SystemExit("REFUSED: S222_JOINER_LOGIN is not in this file. NOTHING was changed.")
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_forms_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s."
                         % (ex, bak))
    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
