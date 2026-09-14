#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_months_s271.py -- S271 proved offline, including the patch itself."""
import io, os, re, sqlite3, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
def _find_s270():
    """The S270 block, wherever this kit is unpacked: beside it in the repo, or
    in the build tree it was written in. Named, never guessed silently."""
    for cand in (os.path.join(os.path.dirname(HERE), "S270_CHEQUE_REGISTER"),
                 os.path.join(os.path.dirname(HERE), "s270"),
                 os.path.join(HERE, "S270_CHEQUE_REGISTER")):
        if os.path.exists(os.path.join(cand, "block.py")):
            return cand
    return None

S270 = _find_s270()
OK = [0]; BAD = []

def ck(n, c, d=""):
    if c: OK[0] += 1; print("  ok   %s" % n)
    else: BAD.append(n); print("  FAIL %s   %s" % (n, d))

print("S271 selftest -- the register's months")

# ---- 1. the helper's own logic, run for real ----
NS = {}
helper = re.search(r"HELPER = '''(.*?)'''", io.open(
    os.path.join(HERE, "patch_cheque_months_s271.py"), encoding="utf-8").read(), re.S).group(1)
con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
con.execute("CREATE TABLE purchase_cheque (month TEXT, voided_at TEXT)")
con.execute("INSERT INTO purchase_cheque VALUES ('2026-07', NULL)")
con.commit()
NS["_months"] = lambda c: ["2026-09", "2026-08"]
exec(compile(helper, "helper", "exec"), NS)
f = NS["_cheque_months_s271"]
got = f(con)
ck("1 the book's months appear even with no cheque in them", "2026-09" in got and "2026-08" in got, got)
ck("2 a month that has a cheque but is not in the book still appears", "2026-07" in got, got)
ck("3 newest first", got == sorted(got, reverse=True), got)
ck("4 no duplicates", len(got) == len(set(got)))
NS["_months"] = lambda c: (_ for _ in ()).throw(RuntimeError("no book on this box"))
ck("5 a box without the purchase book still gets a working register",
   f(con) == ["2026-07"], "must fall back to the cheques alone, never raise")
NS["_months"] = lambda c: None
ck("6 _months returning nothing is survived", f(con) == ["2026-07"])
NS["_months"] = lambda c: ["2026-09", None, ""]
ck("7 empty month values are dropped", f(con) == ["2026-09", "2026-07"], f(con))

# ---- 2. the patch applied to the REAL S270 block, end to end ----
if S270 is None:
    print("  FAIL 8-15  the S270 kit's block.py is not beside this kit -- "
          "checks 8 to 15 COULD NOT RUN and are not passes (F-443).")
    BAD.append("8-15 the S270 block could not be found")
    print("\n%d checks passed, %d failed" % (OK[0], len(BAD)))
    sys.exit(1)
blk = io.open(os.path.join(S270, "block.py"), encoding="utf-8").read()
fake = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8")
fake.write(blk); fake.close()
r = subprocess.run([sys.executable, "-B",
                    os.path.join(HERE, "patch_cheque_months_s271.py"), "--file", fake.name],
                   capture_output=True, text=True)
out = io.open(fake.name, encoding="utf-8").read()
ck("8 the patch applies to the real S270 block", "patched" in r.stdout, r.stdout + r.stderr)
ck("9 the query now lives in the helper alone, not inline on the page",
   out.count("SELECT DISTINCT month FROM purchase_cheque") == 1,
   out.count("SELECT DISTINCT month FROM purchase_cheque"))
ck("10 the page now calls the helper", "months = _cheque_months_s271(con)" in out)
ck("11 the helper is defined in the file", "def _cheque_months_s271(con):" in out)
import ast
try:
    ast.parse(out); ok = True
except SyntaxError as e:
    ok = False; err = e
ck("12 the patched file parses clean", ok, "" if ok else err)
r2 = subprocess.run([sys.executable, "-B",
                     os.path.join(HERE, "patch_cheque_months_s271.py"), "--file", fake.name],
                    capture_output=True, text=True)
ck("13 running it twice does nothing the second time", "ALREADY PATCHED" in r2.stdout, r2.stdout)
fresh = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8")
fresh.write(blk); fresh.close()
r3 = subprocess.run([sys.executable, "-B",
                     os.path.join(HERE, "patch_cheque_months_s271.py"),
                     "--file", fresh.name, "--from", "0" * 32],
                    capture_output=True, text=True)
ck("14 a wrong --from is refused on an UNPATCHED file",
   r3.returncode != 0 and "REFUSING" in (r3.stdout + r3.stderr), r3.stdout + r3.stderr)
ck("14b and it wrote nothing", io.open(fresh.name, encoding="utf-8").read() == blk)
os.unlink(fresh.name); os.unlink(fake.name)

# ---- 3. it must not reintroduce the S270 drift ----
ck("15 the page-wide stylesheet is still untouched",
   not re.search(r"^CSS = CSS \+ CHEQUE_CSS", out, re.M))

print("\n%d checks passed, %d failed" % (OK[0], len(BAD)))
if BAD: print("FAILED: " + ", ".join(BAD))
sys.exit(1 if BAD else 0)
