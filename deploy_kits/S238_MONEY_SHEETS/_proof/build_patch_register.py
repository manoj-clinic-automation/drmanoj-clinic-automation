#!/usr/bin/env python3
"""build_patch_register.py -- staff_register.py v0.12 (f85a4b06...) -> v0.13 (S238):
the Lock refuses until the staff ledger has closed the month, so the Advance column
can never be locked at 0 before the recoveries are in. One anchored insertion."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
PIN = "f85a4b0663ee0028c967cefec716bd12"
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != PIN:
    sys.exit("source is not the pinned v0.12")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)
rep('''v0.12(S200/R7) — approve WHERE YOU READ:''', '''v0.13(S238) — the Lock refuses until the STAFF LEDGER has closed the month: the
              Advance column is now the ledger's own recoveries (salary_policy v1.8,
              D349/D442), and before the ledger close there are none to lock.
v0.12(S200/R7) — approve WHERE YOU READ:''', "doc")
rep('''    if not res.get("enforced"):
        return _render_salary(ym, u,
            "This month is PREVIEW''', '''    if not res.get("ledger_closed", False):
        return _render_salary(ym, u,
            "The staff ledger has not been closed for this month \\u2014 the advance and "
            "loan recoveries are not in yet, so the Advance column would lock at 0. Run the "
            "ledger close first (Ledger \\u2192 Salary \\u2192 step 5, from the 1st of the next "
            "month), then lock.")
    if not res.get("enforced"):
        return _render_salary(ym, u,
            "This month is PREVIEW''', "lock_gate")
# F-185: the selftest's dummy emergency number is a ten-digit run, which the
# repository's phone gate refuses in a new file. It is a fixture, never validated
# as digits -- a plain placeholder does the same job.
import re as _re
s, _n = _re.subn(r'("Wife", ")\d{10}(")', r'\1EXAMPLE-0000\2', s)
if _n != 1:
    sys.exit("dummy-number anchor found %d times" % _n)
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
