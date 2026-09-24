#!/usr/bin/env python3
"""apply_s392.py -- kit S392_LAB_NO_ID_2. Makes the S392 slip_log.py from the live S391 bytes (00038e76) by one anchored
edit: the re-send rule of noid_match looks both ways in time. Usage: python apply_s392.py <S391 slip_log.py> <out>"""
import hashlib, sys
b = open(sys.argv[1], "rb").read()
assert hashlib.md5(b).hexdigest() == "00038e76db04dd7edf62127f16e18de9", "the source is not S391 slip_log.py"
s = b.decode("utf-8")
old = '''        # the lab sent the same report again: follow the first one that found its patient
        lo = (dt.date.fromisoformat(received_at[:10]) - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
        prev = {r["clinic_id"] for r in con.execute(
            "SELECT name, clinic_id FROM lab_noid WHERE clinic_id<>'' AND received_at>=? AND received_at<=?", (lo, received_at))
            if _norm_name(r["name"]) == _norm_name(name)}'''
new = '''        # the same report sent more than once: follow the copy that found its patient -- EARLIER OR LATER (S392: the
        # mailbox reads newest first, so a resend can take the order before the original is looked at)
        d0 = dt.date.fromisoformat(received_at[:10])
        lo = (d0 - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
        hi = (d0 + dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat() + " 23:59:59"
        prev = {r["clinic_id"] for r in con.execute(
            "SELECT name, clinic_id FROM lab_noid WHERE clinic_id<>'' AND received_at>=? AND received_at<=?", (lo, hi))
            if _norm_name(r["name"]) == _norm_name(name)}'''
assert s.count(old) == 1, "anchor"
s = s.replace(old, new)
open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("S392 slip_log.py md5", hashlib.md5(s.encode("utf-8")).hexdigest())
