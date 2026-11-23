#!/usr/bin/env python3
"""make_s937b.py -- kit S937 half 2: order_flow.py 6b3165d2 -> TO (the owner 17:10/17:30: his Purchase orders page carries a clear
'Today's order sheet -- Print · WhatsApp' button, there all day, also when everything is ordered and reception's To-order row is gone)."""
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
if hashlib.md5(b).hexdigest() != "6b3165d21235735b80dc913a36ba40da":
    sys.exit("not at FROM")
s = b.decode("utf-8")
OLD = '''                '<a href="/finance/porders?home=1" style="float:right;font-size:14px;text-decoration:none">Reception\\'s screen →</a>'   # S925
                '</div>%s</body></html>') % body'''
NEW = '''                '<a href="/finance/porders?home=1" style="float:right;font-size:14px;text-decoration:none">Reception\\'s screen →</a>'   # S925
                '<a id="s937sheet" href="/finance/porders/s454/order" style="display:block;margin:10px 0 2px;padding:12px 14px;border-radius:10px;'
                'background:#1f5f99;color:#fff;font-size:17px;font-weight:700;text-decoration:none">Today\\'s order sheet — Print · WhatsApp →</a>'   # S937
                '</div>%s</body></html>') % body'''
assert s.count(OLD) == 1, "anchor 1"
s = s.replace(OLD, NEW)
OLD2 = 'VERSION = "2.0"   # S926'
assert s.count(OLD2) == 1, "anchor 2"
s = s.replace(OLD2, 'VERSION = "2.1"   # S937: the order-sheet button on his page. S926')
open(dst, "w", encoding="utf-8").write(s)
print(hashlib.md5(s.encode("utf-8")).hexdigest())
