#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_forms_s222.py -- S222: the joiner form and the exit picker.

THE OWNER, twice, plainly: "remove words jodna, vidaai, with proper english ones" and then
"make it all englsh flow".

WHY A WHOLE-FILE SWAP AND NOT A PATCHER. Forty-seven strings change. An anchor patcher with
forty-seven anchors is forty-seven ways to refuse on a live file for no benefit; the page is
7 KB and the repository holds the exact bytes that are live. So: verify the pin, copy the old
one aside, write the new one.

NOTHING BUT WORDS CHANGES. No id, no class, no API path, no function, no logic. The English
file was produced by replacing whole quoted strings in the live file and nothing else -- and
the browser gate re-runs every flow on the result: the record list, opening a finished record,
the tested password line in all three of its states, the missing-login warning, and the search.

D366 IS OBEYED, NOT BROKEN. /finance/staff is the OWNER'S console -- it is checker-only -- so
it goes English with the rest of his screens. The WhatsApp message that reaches a new joiner is
composed by the SERVER (api_message) and stays HINDI, because a staff member reads that one.
This kit does not touch it.

    /root/wa/venv/bin/python3 -B /root/finance/install_english_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.environ.get('SM_PATH', '/root/finance/staff_manage.html')
SOURCE = os.environ.get('SM_SRC', os.path.join(HERE, 'staff_manage.html'))
EXPECT_FROM = "eb4e415de611f027c05929338f256a59"
EXPECT_TO = "8300adab775d7e7918c7ed9d07344901"


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    if not os.path.exists(SOURCE):
        raise SystemExit("REFUSED: the English page is not beside this script (%s)." % SOURCE)
    new = md5(SOURCE)
    if new != EXPECT_TO:
        raise SystemExit("REFUSED: the English page beside this script is %s, not the %s "
                         "this kit shipped. NOTHING was changed." % (new, EXPECT_TO))
    if not os.path.exists(TARGET):
        raise SystemExit("REFUSED: no page at %s." % TARGET)
    cur = md5(TARGET)
    print("current pin  %s" % cur)
    if cur == EXPECT_TO:
        print("already installed -- nothing to do")
        return 0
    if cur != EXPECT_FROM:
        raise SystemExit("REFUSED: the live page is %s, not the %s this kit was built against "
                         "(S222_STAFF_ENGLISH must be in first). NOTHING was changed." % (cur, EXPECT_FROM))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_forms_" + stamp
    shutil.copyfile(TARGET, bak)
    shutil.copyfile(SOURCE, TARGET)
    pin = md5(TARGET)
    if pin != EXPECT_TO:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the written file is %s, not %s. RESTORED from %s."
                         % (pin, EXPECT_TO, bak))
    print("installed %s" % TARGET)
    print("backup    %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    print("no restart -- this page is read from disk on every request; hard-reload it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
