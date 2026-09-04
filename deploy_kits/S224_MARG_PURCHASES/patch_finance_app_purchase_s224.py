#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_finance_app_purchase_s224.py -- S224: mount Marg Purchases inside the finance app.

THREE EDITS, each anchored on an exact line, each refused if the anchor is not found
EXACTLY ONCE. It changes nothing unless every anchor matches and the file's md5 is the
one you hand it.

  1. the MOUNT     two lines after the S223 `clinic_register.init(` block, in the same
                   shape as the six modules already mounted there.
  2. the GATE      the pharmacy sender's token (X-Finance-Marg) may open THREE more
                   paths -- push, vendors, feed -- exactly as it already opens
                   /finance/stock/api/snapshot. Without this the nightly push is 302'd to
                   the login page before the route ever runs (the S207 fault, again).
  3. healthz       /finance/purchase/api/healthz joins PUBLIC_PATHS: no auth, per contract.

THE PIN. The repo's finance_app.py is BEHIND the box, so the expected md5 is NOT
hard-coded here: you pass the one you read on the box.

Run on the box:
    md5sum /root/finance/finance_app.py
    /root/wa/venv/bin/python3 -B /root/finance/patch_finance_app_purchase_s224.py <that md5>
Offline:
    FA_PATH=./finance_app.py python3 -B patch_finance_app_purchase_s224.py <md5 of that copy>
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S224_MARG_PURCHASES begin"

A_OLD = '''import clinic_register                                        # noqa: E402
clinic_register.init(app, db, require, audit, unit=CLINIC_UNIT)
# --- S223_CLINIC_REGISTER end ---'''

A_NEW = '''import clinic_register                                        # noqa: E402
clinic_register.init(app, db, require, audit, unit=CLINIC_UNIT)
# --- S223_CLINIC_REGISTER end ---

# --- S224_MARG_PURCHASES begin -- Marg's purchase exports, pushed from manojz ---
# Bills, item lines, the month's verdicts and FINALISE, scan links to the asset
# app, and the order book. Its tables are created on first request, never here.
# The token is the same sender's token stock_app already takes; the gate above
# lets it open the three machine paths and nothing else.
import purchase_app                                           # noqa: E402
purchase_app.init(app, db, require, unit=UNIT, marg_token=MARG_TOKEN,
                  assets_db=os.environ.get("ASSETS_DB", "/root/assetapp/assets.db"))
# --- S224_MARG_PURCHASES end ---'''

# The gate, as S208 left it. Tier 1 is the whole block; if it is not there verbatim,
# tier 2 extends the tuple alone (same effect on the three paths).
B1_OLD = '''    if MARG_TOKEN and p in ("/finance/api/marg-push",
                            "/finance/api/pipeline-status",
                            "/finance/stock/api/snapshot") \\
            and request.headers.get("X-Finance-Marg") == MARG_TOKEN:
        return None
'''
B1_NEW = '''    if MARG_TOKEN and p in ("/finance/api/marg-push",
                            "/finance/api/pipeline-status",
                            "/finance/stock/api/snapshot",
                            "/finance/purchase/api/push",        # S224
                            "/finance/purchase/api/vendors",     # S224
                            "/finance/purchase/api/feed") \\
            and request.headers.get("X-Finance-Marg") == MARG_TOKEN:
        return None
    # S224: on the purchase machine door a WRONG token answers 401, never a login
    # redirect -- the sender must see the refusal, not a 302 it cannot follow.
    if p.startswith("/finance/purchase/api/") and "X-Finance-Marg" in request.headers:
        return jsonify(ok=False, error="bad_token"), 401
'''
B2_OLD = '''"/finance/stock/api/snapshot")'''
B2_NEW = '''"/finance/stock/api/snapshot",
                            "/finance/purchase/api/push",        # S224
                            "/finance/purchase/api/vendors",     # S224
                            "/finance/purchase/api/feed")'''

C_OLD = '''PUBLIC_PATHS = ("/finance/healthz",'''
C_NEW = '''PUBLIC_PATHS = ("/finance/healthz",
                "/finance/purchase/api/healthz",           # S224: no auth, per contract'''

REQUIRED = ("\ndef require(", "\ndef db(", "\nMARG_TOKEN = ", "\nUNIT = ", "\nimport os")


def main():
    if len(sys.argv) < 2 or len(sys.argv[1]) != 32:
        sys.exit("USAGE: patch_finance_app_purchase_s224.py <md5 of the finance_app.py you are patching>\n"
                 "       read it with:  md5sum /root/finance/finance_app.py")
    from_md5 = sys.argv[1].lower()
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    src = io.open(TARGET, encoding="utf-8").read()
    cur = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != from_md5:
        sys.exit("REFUSING: %s is %s, you said %s (D172/D188). Read the box's pin again."
                 % (TARGET, cur, from_md5))
    for name in REQUIRED:
        if src.count(name) != 1:
            sys.exit("REFUSING: %r occurs %d times, expected exactly 1" % (name.strip(), src.count(name)))
    if src.count(A_OLD) != 1:
        sys.exit("REFUSING: the S223 clinic_register mount anchor did not match exactly once. "
                 "Install S223_REGISTER_CARD first.")
    if src.count(C_OLD) != 1:
        sys.exit("REFUSING: the PUBLIC_PATHS anchor did not match exactly once")
    if src.count(B1_OLD) == 1:
        gate_old, gate_new, tier = B1_OLD, B1_NEW, "full block"
    elif src.count(B2_OLD) == 1:
        gate_old, gate_new, tier = B2_OLD, B2_NEW, "tuple only (401 nicety skipped)"
    else:
        sys.exit("REFUSING: the S208 gate anchor (\"/finance/stock/api/snapshot\") did not match exactly once")
    new = src.replace(A_OLD, A_NEW, 1).replace(gate_old, gate_new, 1).replace(C_OLD, C_NEW, 1)
    bak = TARGET + ".bak_S224_purchase_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after patch (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % from_md5)
    print("gate edit    %s" % tier)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     purchase_app.py, purchase_schema.sql beside it, then restart clinic-finance.service")


if __name__ == "__main__":
    main()
