#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline proof for expected_on_capture.py (rev 2): a synthetic index.csv; stubs in place of PUSH_STOCK_DAILY.bat and
push_purchases.py that exit with the code the test asks for and record the ORDER they were called in. No real data."""
import io, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "expected_on_capture.py")
HDR = "seen_at,type,variant,date_from,date_to,data_from,data_to,export_stamp,md5,verdict,reason,rows,archived_path,source_path,uploaded,notes\n"
ok = True


def ck(label, cond):
    global ok
    print(("PASS  " if cond else "FAIL  ") + label)
    ok = ok and bool(cond)


tmp = tempfile.mkdtemp(prefix="eoc_")
arch, out = os.path.join(tmp, "MargArchive"), os.path.join(tmp, "_analysis")
os.makedirs(arch); os.makedirs(out)
calls = os.path.join(tmp, "calls.txt")
stub = os.path.join(tmp, "stub.py")
io.open(stub, "w").write("import sys, io\nio.open(%r, 'a').write(sys.argv[1] + '\\n')\nprint(sys.argv[1], 'says: exit', sys.argv[2])\nsys.exit(int(sys.argv[2]))\n" % calls)


def env(daily_code, purch_code=0):
    return dict(os.environ, MARG_ARCHIVE=arch, MARG_ANALYSIS=out,
                STOCK_DAILY_CMD="|".join([sys.executable, stub, "DAILY", str(daily_code)]),
                PURCHASE_CMD="|".join([sys.executable, stub, "PURCH", str(purch_code)]))


def run(daily_code, *args, purch_code=0):
    p = subprocess.run([sys.executable, "-B", SCRIPT] + list(args), capture_output=True, text=True, env=env(daily_code, purch_code))
    return p.returncode, p.stdout


def calls_list():
    return io.open(calls).read().split() if os.path.exists(calls) else []


def reset_calls():
    if os.path.exists(calls):
        os.remove(calls)


def write_idx(rows):
    io.open(os.path.join(arch, "index.csv"), "w", newline="").write(HDR + "".join(rows))


mark = os.path.join(out, "expected_on_capture_last.txt")
SALE = "2026-09-06 01:20:34,SALE_BILLWISE,DETAIL,2026-09-05,2026-09-05,2026-09-05,2026-09-05,20260906-011252,f5e12d78aaaaaaaaaaaaaaaaaaaaaaaa,VERIFIED,,225,x,y,,\n"
STOCK = "2026-09-06 01:20:34,STOCK_CLOSING,TOTALS,2026-09-05,2026-09-05,,,20260906-011454,d7d28657bbbbbbbbbbbbbbbbbbbbbbbb,VERIFIED,structural,439,x,y,,\n"
REFUSED_SALE = "2026-09-05 19:31:39,_UNKNOWN,,2026-09-05,2026-09-05,,,20260905-190248,98f6be70cccccccccccccccccccccccc,REFUSED,no signature,239,x,y,,\n"
OLDER = "2026-09-05 09:00:25,SALE_BILLWISE,DETAIL,2026-09-04,2026-09-04,2026-09-04,2026-09-04,20260905-085353,0be4e3cbdddddddddddddddddddddddd,VERIFIED,,140,x,y,,\n"
PURCH_OLD = "2026-09-03 11:30:00,PURCHASE_BILLWISE,DEFAULT,2026-09-01,2026-09-03,,,20260903-105720,aaaa0001eeeeeeeeeeeeeeeeeeeeeeee,VERIFIED,,11,x,y,,\n"
PURCH_NEW = "2026-09-06 10:40:00,PURCHASE_ITEMWISE,DEFAULT,2026-09-04,2026-09-06,,,20260906-103500,bbbb0002ffffffffffffffffffffffff,VERIFIED,,9,x,y,,\n"
PURCH_REF = "2026-09-06 10:41:00,PURCHASE_ITEMWISE,DEFAULT,2026-09-04,2026-09-06,,,20260906-103600,cccc0003ffffffffffffffffffffffff,REFUSED,unreadable,0,x,y,,\n"

# 1 no sale rows -> nothing to do
write_idx([STOCK, REFUSED_SALE, PURCH_OLD])
rc, o = run(0)
ck("no VERIFIED sale export -> exit 0, 'nothing to do', nothing run", rc == 0 and "nothing to do" in o and calls_list() == [])

# 2 dry run
write_idx([OLDER, STOCK, REFUSED_SALE, SALE, PURCH_OLD])
rc, o = run(0, "--dry-run")
ck("dry run names the newest sale (05-Sep) and the purchase export, runs nothing, writes no marker",
   rc == 0 and "for 2026-09-05" in o and "NEW purchase export" in o and "dry run" in o and calls_list() == [] and not os.path.exists(mark))

# 3 first real run: both are new -> purchases FIRST, then the daily; marked with both md5s
rc, o = run(0)
ck("first run: push_purchases then PUSH_STOCK_DAILY, in that order; exit 0; marker SENT <sale> <purchase>",
   rc == 0 and calls_list() == ["PURCH", "DAILY"] and "purchase books current" in o and "sent and marked" in o
   and io.open(mark).read().split() == ["SENT", "f5e12d78aaaaaaaaaaaaaaaaaaaaaaaa", "aaaa0001eeeeeeeeeeeeeeeeeeeeeeee"])
reset_calls()

# 4 nothing new -> quiet
rc, o = run(0)
ck("nothing new -> quiet, nothing run", rc == 0 and o.strip() == "" and calls_list() == [])

# 5 a NEW purchase export only (Sunday morning, Amir's exports; no new sale) -> purchases first, then recompute
write_idx([OLDER, STOCK, SALE, PURCH_OLD, PURCH_NEW, PURCH_REF])
rc, o = run(0)
ck("new purchase export, same sale -> push_purchases then PUSH_STOCK_DAILY; the REFUSED purchase row is ignored; marker carries the new purchase md5",
   rc == 0 and calls_list() == ["PURCH", "DAILY"] and "NEW purchase export: PURCHASE_ITEMWISE" in o and "NEW sale export" not in o
   and io.open(mark).read().split()[2] == "bbbb0002ffffffffffffffffffffffff")
reset_calls()

# 6 a new purchase export but push_purchases FAILS -> the daily is NOT run, nothing marked, retried next time
PURCH_3 = PURCH_NEW.replace("bbbb0002", "dddd0004").replace("2026-09-06 10:40:00", "2026-09-06 11:00:00")
write_idx([OLDER, STOCK, SALE, PURCH_OLD, PURCH_NEW, PURCH_3])
rc, o = run(0, purch_code=1)
ck("push_purchases fails (exit 1) -> PUSH_STOCK_DAILY NOT run, marker unchanged, exit 1",
   rc == 1 and calls_list() == ["PURCH"] and "NOT current" in o and io.open(mark).read().split()[2] == "bbbb0002ffffffffffffffffffffffff")
reset_calls()
rc, o = run(0, purch_code=2)
ck("push_purchases exit 2 without REFUSING (nothing left to send: the nightly got there first) counts as current -> daily runs, marked",
   rc == 0 and calls_list() == ["PURCH", "DAILY"] and io.open(mark).read().split()[2] == "dddd0004ffffffffffffffffffffffff")
reset_calls()

# 7 a newer sale, the daily REFUSES (exit 3) -> said once, marked REFUSED, not retried for the same pair
SALE2 = SALE.replace("f5e12d78aaaaaaaaaaaaaaaaaaaaaaaa", "11111111eeeeeeeeeeeeeeeeeeeeeeee").replace("20260906-011252", "20260906-020000").replace("2026-09-06 01:20:34", "2026-09-06 02:00:00")
write_idx([OLDER, STOCK, SALE, SALE2, PURCH_OLD, PURCH_NEW, PURCH_3])
rc, o = run(3)
ck("newer sale, daily refuses (exit 3) -> only the daily ran (purchases unchanged), exit 3, marker REFUSED",
   rc == 3 and calls_list() == ["DAILY"] and "REFUSED" in o and io.open(mark).read().split()[0:2] == ["REFUSED", "11111111eeeeeeeeeeeeeeeeeeeeeeee"])
reset_calls()
rc, o = run(3)
ck("the refusal is said once: same pair -> quiet", rc == 0 and o.strip() == "" and calls_list() == [])

# 8 daily fails (exit 1) -> not marked, retried
SALE3 = SALE.replace("f5e12d78aaaaaaaaaaaaaaaaaaaaaaaa", "22222222ffffffffffffffffffffffff").replace("20260906-011252", "20260906-030000").replace("2026-09-06 01:20:34", "2026-09-06 03:00:00")
write_idx([OLDER, STOCK, SALE, SALE2, SALE3, PURCH_OLD, PURCH_NEW, PURCH_3])
rc, o = run(1)
ck("daily fails (exit 1) -> exit 1, 'NOT marked', marker unchanged", rc == 1 and "NOT marked" in o and io.open(mark).read().split()[1] == "11111111eeeeeeeeeeeeeeeeeeeeeeee")
reset_calls()
rc, o = run(0)
ck("...next cycle retries; success -> SENT with the new sale", rc == 0 and calls_list() == ["DAILY"] and io.open(mark).read().split()[0:2] == ["SENT", "22222222ffffffffffffffffffffffff"])
reset_calls()

# 9 the .bat missing (no stub) -> REFUSING, exit 2
e = dict(os.environ, MARG_ARCHIVE=arch, MARG_ANALYSIS=out, STOCK_DAILY_BAT=os.path.join(tmp, "absent.bat"))
e.pop("STOCK_DAILY_CMD", None); e.pop("PURCHASE_CMD", None)
write_idx([OLDER, STOCK, SALE, SALE2, SALE3, SALE3.replace("22222222", "33333333"), PURCH_OLD, PURCH_NEW, PURCH_3])
p = subprocess.run([sys.executable, "-B", SCRIPT], capture_output=True, text=True, env=e)
ck("PUSH_STOCK_DAILY.bat missing -> REFUSING, exit 2, nothing marked", p.returncode == 2 and "REFUSING" in p.stdout and io.open(mark).read().split()[1] == "22222222ffffffffffffffffffffffff")

print("\n%s" % ("ALL PASS" if ok else "SELFTEST FAILED"))
sys.exit(0 if ok else 1)
