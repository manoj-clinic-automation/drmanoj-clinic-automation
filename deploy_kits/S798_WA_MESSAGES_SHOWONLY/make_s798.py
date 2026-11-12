#!/usr/bin/python3
# make_s798.py -- kit S798_WA_MESSAGES_SHOWONLY (S437, 12-Nov-2026, the parent; the owner's "ok" 10:12 IST on the show-only page of
# the approved WhatsApp messages, D934). Usage: make_s798.py <live portal.py> <out dir>
# Exact replacements on the live bytes (portal.py 8b723919 -- S786); every anchor must occur once.
import hashlib, os, sys
pp, out = sys.argv[1], sys.argv[2]
b = open(pp, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("8b723919"), "not the live portal.py (8b723919)"
P = b.decode("utf-8")
def rp(t, a, n):
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    return t.replace(a, n)
P = rp(P, '''     "url": "/portal/booking",
     "roles": ["doctor"]},
''', '''     "url": "/portal/booking",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4E8", "name": "WhatsApp messages",
     # S798 NEW (the owner, 12-Nov-2026: D934 and his "ok" of 10:12 IST). SHOW ONLY -- which approved WhatsApp message would go to
     # whom today (follow-up tomorrow, after the visit, appointment reminder, date passed, long overdue), with the rules applied and
     # the STOP list. Served by wa_ladder.py (/portal/messages), which holds no send code. The doctors hold it by role.
     "desc": "Show only \\u00b7 who would get which message",
     "live": True,
     "url": "/portal/messages",
     "roles": ["doctor"]},
''')
P = rp(P, '''    "Online booking": "Patients",                                                            # S786
''', '''    "Online booking": "Patients",                                                            # S786
    "WhatsApp messages": "Patients",                                                         # S798
''')
P = rp(P, '''    print("online_booking_portal NOT mounted: %r" % (_e_s786,), file=_sys_s786.stderr)
''', '''    print("online_booking_portal NOT mounted: %r" % (_e_s786,), file=_sys_s786.stderr)

# S798_WA_MESSAGES_SHOWONLY: /portal/messages -- who would get which approved WhatsApp message today, SHOW ONLY (wa_ladder.py holds
# no send code; optional: absent = no page)
try:
    import wa_ladder
    wa_ladder.install(app, login_required, _sso_user)
except Exception as _e_s798:                                          # noqa: BLE001 -- the portal stands without it
    import sys as _sys_s798
    print("wa_ladder NOT mounted: %r" % (_e_s798,), file=_sys_s798.stderr)
''')
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
with open(os.path.join(out, "portal", "portal.py"), "wb") as fh:
    fh.write(P.encode("utf-8"))
print("portal.py", hashlib.md5(P.encode("utf-8")).hexdigest())
