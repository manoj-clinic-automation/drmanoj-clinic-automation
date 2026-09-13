#!/usr/bin/env python3
"""S258_CONSTANT_TIME -- every machine-door token check becomes a constant-time compare.
Usage: patch_compare_s258.py <which: fa|st|pu> <src> <dst>
  fa = finance_app.py (7 sites)  st = stock_app.py (1 site)  pu = purchase_app.py (1 site)
Behaviour is identical for every real request. The one difference is deliberate: an EMPTY expected
token never matches anything (before, a missing token and a missing header could compare equal on
the two `!=` sites). Nothing else -- no route, no role, no table -- is touched.
"""
import io, sys
WHICH, SRC, DST = sys.argv[1], sys.argv[2], sys.argv[3]
s = io.open(SRC, encoding="utf-8").read(); n = 0
def sub(old, new, count=1):
    global s, n
    c = s.count(old)
    if c != count: raise SystemExit("ANCHOR COUNT %d (expected %d):\n%s" % (c, count, old[:120]))
    s = s.replace(old, new); n += 1

HELPER = ('import hmac                                            # S258\n'
          '\n\n'
          'def _tok_ok(given, expected):\n'
          '    """S258: constant-time token compare (F-470). False when either side is empty."""\n'
          '    try:\n'
          '        return bool(expected) and bool(given) and hmac.compare_digest(str(given), str(expected))\n'
          '    except Exception:                                  # noqa: BLE001\n'
          '        return False\n')

if WHICH == "fa":
    sub("import os\nimport re\nimport sqlite3\nimport urllib.parse\n",
        "import os\nimport re\nimport sqlite3\nimport urllib.parse\n" + HELPER)
    sub('    if CRON_TOKEN and request.headers.get("X-Finance-Cron") == CRON_TOKEN:\n',
        '    if _tok_ok(request.headers.get("X-Finance-Cron"), CRON_TOKEN):              # S258\n')
    sub('            and request.headers.get("X-Finance-Marg") == MARG_TOKEN:\n',
        '            and _tok_ok(request.headers.get("X-Finance-Marg"), MARG_TOKEN):      # S258\n')
    sub('            and request.headers.get("X-Finance-Renewals") == RENEWALS_TOKEN:\n',
        '            and _tok_ok(request.headers.get("X-Finance-Renewals"), RENEWALS_TOKEN):  # S258\n')
    sub('    is_cron = bool(CRON_TOKEN and request.headers.get("X-Finance-Cron") == CRON_TOKEN)\n',
        '    is_cron = _tok_ok(request.headers.get("X-Finance-Cron"), CRON_TOKEN)         # S258\n', count=2)
    sub('    if request.headers.get("X-Finance-Marg") != MARG_TOKEN:\n',
        '    if not _tok_ok(request.headers.get("X-Finance-Marg"), MARG_TOKEN):          # S258\n')
    sub('    if request.headers.get("X-Finance-Marg", "") != tok:\n',
        '    if not _tok_ok(request.headers.get("X-Finance-Marg", ""), tok):             # S258\n')
    sub('    if request.headers.get("X-Finance-Renewals") != RENEWALS_TOKEN:\n',
        '    if not _tok_ok(request.headers.get("X-Finance-Renewals"), RENEWALS_TOKEN):  # S258\n')
elif WHICH in ("st", "pu"):
    sub("import os\n", "import os\n" + HELPER)
    sub('    if _marg_token and request.headers.get("X-Finance-Marg") == _marg_token:\n',
        '    if _tok_ok(request.headers.get("X-Finance-Marg"), _marg_token):             # S258\n')
else:
    raise SystemExit("which?")
io.open(DST, "w", encoding="utf-8", newline="").write(s)
print("%s: anchors applied: %d" % (WHICH, n))
