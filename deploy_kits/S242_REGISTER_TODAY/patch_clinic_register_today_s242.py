#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_clinic_register_today_s242.py -- S242: the register opens on TODAY.

THE OWNER, 12-Sep-2026: "its showing of 11 sept, shd be of today, to be used at end of day."

WHAT WAS WRONG, read from the screen's own code and not guessed. `register_index` builds its list
of candidate days from ONE table:

    SELECT business_date FROM clinic_day_revenue ORDER BY business_date DESC LIMIT 45

That table is Docterz's. Today is not in it until Docterz has sent the day, and Docterz sends after
the day -- so at the hour this screen is actually used, the newest day the code can see is
YESTERDAY, and that is the day it redirected to. Nothing was broken; the screen was reading a
record that does not know about today yet.

THE FIX. One helper, used in two places: today is put at the head of the candidate days whether or
not Docterz has heard of it. Nothing else changes -- not the gate, not the tables, not what a day
page shows, not the to-do behaviour. Once today is filled, "next unfilled day" walks back through
the older unfilled days exactly as before.

    /finance/clinic/register        opens TODAY when today is not yet filled
    /finance/clinic/register/list   lists today too, so a filled today is visible

The day page itself needed no change: it already accepts any valid ISO date (`_iso_ok`), and a day
Docterz has not sent reads as "not known" rather than as zero (`docterz_day` -> known=False,
`bank_upi` -> (None, False)). That is the existing design and it is why today renders correctly.

Three anchors, each must match EXACTLY ONCE, or nothing is changed. Idempotent by the MARK.
Timestamped backup, compile-with-restore.

Run on the box:
    /root/wa/venv/bin/python3 -B /root/finance/patch_clinic_register_today_s242.py
Offline:
    REG_PATH=./clinic_register.py python3 -B patch_clinic_register_today_s242.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

REG = os.environ.get("REG_PATH", "/root/finance/clinic_register.py")
FROM_MD5 = "93a31e68234df066776b7b80ef65ffbd"
MARK = "def _with_today("

# A -- the helper, inserted immediately above the pages section
A_OLD = '''# ---------------------------------------------------------------- pages
@bp.route("/finance/clinic/register")'''
A_NEW = '''def _with_today(days):
    """S242 (D482): TODAY LEADS.

    The candidate days come from `clinic_day_revenue`, which is Docterz's record of a day. Docterz
    sends AFTER the day, so at the end of today that table's newest row is yesterday -- and the
    screen opened on yesterday, which is not the day the person came to fill.

    The register is the counter's own record and it does not wait for anybody. Today belongs at the
    head of the list whether Docterz has heard of it or not. A day with no Docterz row still renders
    correctly: `docterz_day` returns known=False and `bank_upi` returns (None, False), so the other
    two records read "not known" rather than a zero that would invent a difference.
    """
    t = dt.date.today().isoformat()
    return days if t in days else [t] + list(days)


# ---------------------------------------------------------------- pages
@bp.route("/finance/clinic/register")'''

# B -- register_index: today joins the candidates before the to-do is worked out
B_OLD = '''    if not days:
        today = dt.date.today()
        days = [(today - dt.timedelta(days=i)).isoformat() for i in range(21)]
    done = {r[0] for r in con.execute("SELECT business_date FROM clinic_register_day")}
    todo = [d for d in days if d not in done]'''
B_NEW = '''    if not days:
        today = dt.date.today()
        days = [(today - dt.timedelta(days=i)).isoformat() for i in range(21)]
    days = _with_today(days)
    done = {r[0] for r in con.execute("SELECT business_date FROM clinic_register_day")}
    todo = [d for d in days if d not in done]'''

# C -- register_list: "all days" shows today as well, so a filled today is visible there
C_OLD = '''    return _shell("Daily register", _list_html(con, days, only_todo=False))'''
C_NEW = '''    days = _with_today(days)
    return _shell("Daily register", _list_html(con, days, only_todo=False))'''

PAIRS = (("the _with_today helper", A_OLD, A_NEW),
         ("register_index candidates", B_OLD, B_NEW),
         ("register_list candidates", C_OLD, C_NEW))


def main():
    if not os.path.exists(REG):
        sys.exit("REFUSING: %s not found" % REG)
    src = io.open(REG, encoding="utf-8").read()
    cur = hashlib.md5(io.open(REG, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s. Read the box's pin again before anything else."
                 % (REG, cur, FROM_MD5))
    for label, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, n))
    new = src
    for _label, old, rep in PAIRS:
        new = new.replace(old, rep, 1)
    bak = REG + ".bak_S242_today_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(REG, bak)
    io.open(REG, "w", encoding="utf-8", newline="\n").write(new)
    try:
        import py_compile
        import tempfile
        _fd, _cf = tempfile.mkstemp(suffix=".pyc")
        os.close(_fd)
        try:
            py_compile.compile(REG, cfile=_cf, doraise=True)
        finally:
            try:
                os.remove(_cf)
            except OSError:
                pass
    except Exception as e:                       # noqa: BLE001
        shutil.copy2(bak, REG)
        sys.exit("REFUSING: compile failed (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(REG, "rb").read()).hexdigest()
    print("current pin  %s" % FROM_MD5)
    print("patched  %s" % REG)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- the line the close records (A0: never from memory)" % got)
    print("next     systemctl restart clinic-finance")


if __name__ == "__main__":
    main()
