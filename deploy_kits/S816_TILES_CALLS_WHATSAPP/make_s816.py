#!/usr/bin/python3
# make_s816.py -- kit S816_TILES_CALLS_WHATSAPP (S447, 13-Nov-2026, the parent; F-1324, the owner's approved mock-up "the tiles",
# artifact 8J3R3QtW9awbajmLN4rmic). Usage: make_s816.py <live portal.py> <out dir>   -> <out dir>/portal/portal.py
# Exact replacements on the live bytes (portal.py 3a0f7cd1 -- S798's); every anchor must occur exactly once; the result must be
# the pinned TO. The kit carries NO copy of portal.py: it is remade on the box from the file that is live there.
#   1. the tile "WhatsApp messages" moves from Patients to Calls & WhatsApp (between WhatsApp Inbox and Send WhatsApp) with a new
#      small line; its name, icon, address and roles are unchanged
#   2. the tile "Follow-up WhatsApps" is removed from TILES          3. the tile "WhatsApp Approvals" is removed from TILES
#   4. the folded System group's face no longer names the retired tile: its small line drops " (dot) WhatsApp approvals" and
#      nothing else (decided in S447 after the first build: a face must not name a tile that is gone)
# Nothing else: no route, no page code, no other tile, no other group face, no grant.
import hashlib, os, sys
FROM = "3a0f7cd17803d8b74af7b67eb4d68964"
TO = "8f60b3106e6b2b9687495b01a74b90c5"
pp, out = sys.argv[1], sys.argv[2]
b = open(pp, "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "not the live portal.py this kit was built on (3a0f7cd1)"
P = b.decode("utf-8")


def rp(t, a, n):
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    return t.replace(a, n)


# 1a. the tile's dict leaves its place after "Online booking" (the Patients run of TILES)
P = rp(P, r'''    {"icon": "\U0001F4E8", "name": "WhatsApp messages",
     # S798 NEW (the owner, 12-Nov-2026: D934 and his "ok" of 10:12 IST). SHOW ONLY -- which approved WhatsApp message would go to
     # whom today (follow-up tomorrow, after the visit, appointment reminder, date passed, long overdue), with the rules applied and
     # the STOP list. Served by wa_ladder.py (/portal/messages), which holds no send code. The doctors hold it by role.
     "desc": "Show only \u00b7 who would get which message",
     "live": True,
     "url": "/portal/messages",
     "roles": ["doctor"]},
''', r'''    # S816 (F-1324): the "WhatsApp messages" tile (S798) MOVED from here to Calls & WhatsApp -- its dict now stands between
    # "WhatsApp Inbox" and "Send WhatsApp", above.
''')

# 1b. ... and stands between "WhatsApp Inbox" and "Send WhatsApp" (the order inside a group is the order in TILES)
P = rp(P, r'''    {"icon": "\U0001F4AC", "name": "Send WhatsApp",
''', r'''    {"icon": "\U0001F4E8", "name": "WhatsApp messages",
     # S798 NEW (the owner, 12-Nov-2026: D934). The approved WhatsApp messages to patients, day by day. Served by wa_ladder.py
     # (/portal/messages). The doctors hold it by role.
     # S816 (F-1324; the owner's approved mock-up of 13-Nov-2026, "the tiles"): MOVED here from Patients, between WhatsApp Inbox
     # and Send WhatsApp, and its small line as on the mock-up. Name, icon, address and roles unchanged.
     "desc": "Daily patient messages \u00b7 switches \u00b7 what went",
     "live": True,
     "url": "/portal/messages",
     "roles": ["doctor"]},

    {"icon": "\U0001F4AC", "name": "Send WhatsApp",
''')

# 2 + 3. the two retired tiles leave TILES (the way S586 retired its eight); a note stands where they were
P = rp(P, r'''    {"icon": "\U0001F4E3", "name": "Follow-up WhatsApps",
     "desc": "The follow-up list, cleaned \u00b7 on the Call Console", "live": True,
     "url": "/portal/console#followups",
     "roles": ["doctor"]},

    {"icon": "\U0001F4F1", "name": "WhatsApp Approvals",
     "desc": "Vendor panel \u2014 active again", "live": True,
     "url": "https://followup.dr-manoj.in/wa-approve",
     "roles": ["doctor"]},
''', r'''    # S816 (F-1324; the owner's approved mock-up of 13-Nov-2026): TWO TILES RETIRED from the home screen -- removed from TILES,
    # as S586 retired its eight. Both were the doctors' by role only; no staff login was drawn either.
    #   "Follow-up WhatsApps" -- was /portal/console#followups, in Calls & WhatsApp: only a link into the Call Console.
    #   "WhatsApp Approvals"  -- was https://followup.dr-manoj.in/wa-approve, in System: the oldest tick-and-send page.
    # Nothing behind them is touched: both addresses still answer and the wa-approve service still runs (clinic-doctor watches
    # it). Putting a tile back = its dict from kit S816's README back into this list + its line in _TILE_GROUP.
''')

# the groups: "WhatsApp messages" leaves Patients ...
P = rp(P, r'''    "WhatsApp messages": "Patients",                                                         # S798
''', '')
# ... and is listed under Calls & WhatsApp; the two retired names leave the table
P = rp(P, r'''    "Follow-up WhatsApps": "Calls & WhatsApp", "WhatsApp Approvals": "System",                 # S660: the vendor panel is a system thing
''', r'''    "WhatsApp messages": "Calls & WhatsApp",                                                 # S816 (F-1324): from Patients; two retired
''')

# 4. the folded System group's face: only " \u00b7 WhatsApp approvals" leaves its small line (the tile it named is retired)
P = rp(P, r'''    "System":               ("\u2699\uFE0F", "Board \u00b7 users \u00b7 clinic PCs \u00b7 WhatsApp approvals"),   # S663
''', r'''    "System":               ("\u2699\uFE0F", "Board \u00b7 users \u00b7 clinic PCs"),   # S663
''')

nb = P.encode("utf-8")
got = hashlib.md5(nb).hexdigest()
assert got == TO, "the remade portal.py is not the pinned one (got %s)" % got[:8]
os.makedirs(os.path.join(out, "portal"), exist_ok=True)
with open(os.path.join(out, "portal", "portal.py"), "wb") as fh:
    fh.write(nb)
print("portal.py", got)
