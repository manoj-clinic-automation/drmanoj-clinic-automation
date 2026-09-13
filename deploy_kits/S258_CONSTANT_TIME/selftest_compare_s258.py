#!/usr/bin/env python3
"""S258 selftest: the helper's truth table equals the old expressions on every real input, and is
stricter only when the expected token is empty. Plus: no plain compare survives in any patched file."""
import io, os, re, sys, hmac
HERE = os.path.dirname(os.path.abspath(__file__)); ok = fail = 0
def chk(c, l):
    global ok, fail
    if c: ok += 1;  print("PASS ", l)
    else: fail += 1; print("FAIL ", l)
src = io.open(os.path.join(HERE, "stock_app.py"), encoding="utf-8").read()
m = re.search(r"def _tok_ok\(given, expected\):.*?return False\n", src, re.S); ns = {"hmac": hmac}
exec(m.group(0), ns); tok_ok = ns["_tok_ok"]
T = "x" * 32
cases = [(T, T, True), ("wrong", T, False), (None, T, False), ("", T, False), (T + "y", T, False), (T[:-1], T, False)]
for given, exp, want in cases:
    old_eq = bool(exp and given == exp)                      # the `if TOKEN and hdr == TOKEN` shape
    old_ne = not (given != exp)                              # the `if hdr != TOKEN: refuse` shape
    chk(tok_ok(given, exp) == want == old_eq == old_ne, "given=%r -> %s (old shapes agree)" % ((given or "")[:6], want))
chk(tok_ok("", "") is False and tok_ok(None, "") is False, "empty expected token never matches (stricter than the old `!=` shape)")
chk(tok_ok(123, "123") is False or tok_ok("123", "123") is True, "non-string given handled without raising")
for f, uses in (("_pred_finance_app.py", 8), ("stock_app.py", 1), ("purchase_app.py", 1)):
    p = os.path.join(HERE, f)
    if not os.path.exists(p): continue
    s = io.open(p, encoding="utf-8").read()
    chk(len(re.findall(r'(==|!=) *(CRON_TOKEN|MARG_TOKEN|RENEWALS_TOKEN|_marg_token|tok)\b', s)) == 0, "%s: no plain token compare left" % f)
    chk(s.count("_tok_ok(") == uses + 1, "%s: %d call site(s) + 1 definition" % (f, uses))
    chk(s.count("import hmac") == 1, "%s: hmac imported once" % f)
print("\n%d passed, %d failed" % (ok, fail)); sys.exit(1 if fail else 0)
