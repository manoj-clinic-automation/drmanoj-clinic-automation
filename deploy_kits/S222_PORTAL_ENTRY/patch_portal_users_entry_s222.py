#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_users_entry_s222.py -- S222: the flow starts at Manage Users.

THE OWNER: "this should be a part of the manage users, not a separate system. We open... I go to
the portal. I click upon manage users. Then I see all the users. There, the option should be
there, add new joiner, exit leaver. And from there, it should flow."

WHY THIS FILE WAS NOT TOUCHED UNTIL ITS BYTES WERE PROVEN

/root/portal/portal.py gates every login in the clinic, and the repository's copy is STALE
(d74aa3f9... against a live 16bfd590...). Editing it from a stale copy is exactly the mistake
this session refused to make on darpan_corrections.html this morning -- and was right to, because
the Register's own pin table turned out to be wrong about that file.

So the bytes were reproduced first, and they reproduce EXACTLY:

    deploy_kits/S204_VPS_LIVE/root__portal__portal.py   24ea2c0b44bad08fbce71908a5019ecc
      + deploy_kits/S218_PORTAL_TILE/patch_portal_vaapsi_tile.py
      = 16bfd590e2e422bb81bb8b6ad6e84eae   <- the pin the box printed on 03-Sep-2026

That is the whole live file, offline, and this patch was written against it. The pin below is
therefore predicted, not hoped for.

WHAT IT ADDS: one card at the top of /portal/users, above "Add a login", carrying three links --
add a joiner, exit a leaver, all staff records. Nothing is removed; the user table, the add form
and every action on it are untouched. A login is one of the register's six steps, and the card
says so, because "add a login" on that page has always looked like the whole job and never was.

Target: /root/portal/portal.py   (live pin 16bfd590e2e422bb81bb8b6ad6e84eae)
Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/patch_portal_users_entry_s222.py
Offline:         PORTAL_PATH=./portal.py python3 -B patch_portal_users_entry_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('PORTAL_PATH', '/root/portal/portal.py')
MARK = "S222 JOINER ENTRY"
EXPECT_FROM = "16bfd590e2e422bb81bb8b6ad6e84eae"
STAFF = "https://followup.dr-manoj.in/finance/staff"


A_OLD = '''  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}

  <div class="ucard">
    <h2>Add a login</h2>
'''

A_NEW = '''  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}

  <!-- S222 JOINER ENTRY -- a login is one of six steps, and this page used to
       look like the whole job. The register walks the rest and refuses a step
       taken out of order. -->
  <div class="ucard">
    <h2>Joining and leaving</h2>
    <div style="color:var(--muted);font-size:12px;margin:-4px 0 10px">
      A login is only one of six steps. The register walks the whole thing &mdash; roster row,
      login, credentials, first sign-in, biometric and Emp&nbsp;Code, staff master &mdash; and
      refuses a step taken out of order.
    </div>
    <div class="acts">
      <a class="ibtn go" style="text-decoration:none;display:inline-block"
         href="__STAFF__?flow=join">&#10133; Add a new joiner</a>
      <a class="ibtn" style="text-decoration:none;display:inline-block"
         href="__STAFF__?flow=exit">&#128682; Exit a leaver</a>
      <a class="ibtn" style="text-decoration:none;display:inline-block"
         href="__STAFF__">&#128203; All staff records</a>
    </div>
  </div>

  <div class="ucard">
    <h2>Add a login</h2>
'''.replace("__STAFF__", STAFF)


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
                         "NOTHING was changed. This is the login system -- send me that hash "
                         "rather than forcing it." % (before, EXPECT_FROM))
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_entry_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s -- the "
                         "live file is unchanged." % (ex, bak))
    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    print("next     systemctl restart clinic-portal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
