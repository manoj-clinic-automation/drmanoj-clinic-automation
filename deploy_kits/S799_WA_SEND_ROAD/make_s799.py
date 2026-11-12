#!/usr/bin/python3
# make_s799.py -- kit S799_WA_SEND_ROAD (S437, 12-Nov-2026, the parent; the owner 11:25 IST: the tracker's WhatsApp sends go while
# the Inbox's fail -- F-1031). Usage: make_s799.py <live portal_inbox.py> <live portal_wa.py> <out dir>
# ONE added line in each file: the two urllib senders name a plain User-Agent, as the relay's working sends carry none of
# urllib's own. Exact replacements on the live bytes (portal_inbox.py 06e2c28e -- S793; portal_wa.py 34994b23); each anchor once.
import hashlib, os, sys
pi, pw, out = sys.argv[1], sys.argv[2], sys.argv[3]
def load(p, want):
    b = open(p, "rb").read()
    assert hashlib.md5(b).hexdigest().startswith(want), "not the live %s (%s)" % (os.path.basename(p), want)
    return b.decode("utf-8")
def rp(t, a, n):
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    return t.replace(a, n)
I = load(pi, "06e2c28e")
I = rp(I, '''    req.add_header("Accept", "application/json")
    t0 = time.time()
''', '''    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "clinic-portal/1.0")                  # S799: urllib's own User-Agent is refused at MyOperator's gateway (F-1031)
    t0 = time.time()
''')
Wt = load(pw, "34994b23")
Wt = rp(Wt, '''    req.add_header("Content-Type", "application/json")
    ctx = ssl.create_default_context()
''', '''    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "clinic-portal/1.0")    # S799: urllib's own User-Agent is refused at MyOperator's gateway (F-1031)
    ctx = ssl.create_default_context()
''')
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
for name, t in (("portal_inbox.py", I), ("portal_wa.py", Wt)):
    with open(os.path.join(out, "portal", name), "wb") as fh:
        fh.write(t.encode("utf-8"))
    print(name, hashlib.md5(t.encode("utf-8")).hexdigest())
