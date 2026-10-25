"""make_s646.py -- kit S646_PROCROOM_TILES (session S349, the parent, 25-Oct-2026). The Scan App chat's ask of 25-Oct, relayed by the
owner at 07:40 IST: direct tiles to the procedure-room pages, which until now were reached only through Asset Register's menu.
  /root/portal/portal.py        6470f894 -> ?  3 counted edits: two tiles (after Parchi desk), their groups, the Assets & papers face
  /root/portal/tile_grants.json 11385907 -> ?  v38 -> v39: 'Kal ke procedures' granted to shavez by name; both new tiles masked for bhawna; the note says so
The procedure pages themselves (/root/assetapp/procroom.py) are the Scan App chat's and are not touched.
Usage: python make_s646.py <live portal dir> <out dir>"""
import hashlib, os, sys
PFROM, GFROM = "6470f8944f8ad3a313816139b9bc263b", "1138590794786d4b24ad90055f82bc06"
src, out = sys.argv[1], sys.argv[2]
p = open(os.path.join(src, "portal.py"), "rb").read(); g = open(os.path.join(src, "tile_grants.json"), "rb").read()
assert hashlib.md5(p).hexdigest() == PFROM, "the live portal.py is not 6470f894"
assert hashlib.md5(g).hexdigest() == GFROM, "the live tile_grants.json is not v38 11385907"
s, j = p.decode("utf-8"), g.decode("utf-8")

def rep(text, old, new):
    assert text.count(old) == 1, "anchor not found exactly once: " + old[:70]
    return text.replace(old, new, 1)

A = '''     "url": "/finance/slips/desk",\n     "roles": ["doctor"]},\n'''
s = rep(s, A, A + '''    {"icon": "\\U0001FA79", "name": "Kal ke procedures",
     # S646 NEW (the Scan App chat's ask, relayed by the owner 25-Oct-2026). Shavez's morning screen in the scan app: yesterday's
     # X-ray/Proc slips that Docterz confirms, each pre-filled with its procedure's items, one Save; Roman Hinglish, no rupees.
     # Granted by name to shavez in tile_grants.json v39; the doctor keeps it by role. The page is the Scan App chat's.
     "desc": "Kal ke X-ray/Proc parchi \\u2014 saamaan bharein",
     "live": True,
     "url": "/scanapp/procroom/morning",
     "roles": ["doctor"]},
    {"icon": "\\U0001F9F0", "name": "Procedure room",
     # S646 NEW. The owner's procedure-room page in the scan app: his rates by product and month, the month-end check inside it.
     "desc": "Rates \\u00b7 use by product \\u00b7 month end",
     "live": True,
     "url": "/scanapp/procroom",
     "roles": ["doctor"]},
''')
B = '''    "Asset Register": "Assets & papers", "Scan Purchase": "Assets & papers", "Forms & Downloads": "Assets & papers",\n'''
s = rep(s, B, B + '''    "Procedure room": "Assets & papers", "Kal ke procedures": "Patients",                  # S646\n''')
C = '''    "Assets & papers":      ("\\U0001F5C2\\uFE0F", "Asset register \\u00b7 scan a bill \\u00b7 forms"),\n'''
s = rep(s, C, '''    "Assets & papers":      ("\\U0001F5C2\\uFE0F", "Asset register \\u00b7 procedure room \\u00b7 scan a bill \\u00b7 forms"),\n''')
j = rep(j, '''    "Mahine ka kaam",\n    "Surgery cases"\n   ],''', '''    "Mahine ka kaam",\n    "Surgery cases",\n    "Kal ke procedures"\n   ],''')
j = rep(j, '''    "Check karein",\n    "WhatsApp Inbox"\n   ],\n   "extra": [\n    "Clinic",''', '''    "Check karein",\n    "WhatsApp Inbox",\n    "Kal ke procedures",\n    "Procedure room"\n   ],\n   "extra": [\n    "Clinic",''')
j = rep(j, '''",\n "version": 38,''', ''' S646 v39 (25-Oct-2026, the parent, the Scan App chat's ask relayed by the owner): 'Kal ke procedures' -- Shavez's morning screen for yesterday's procedure-room slips -- granted to shavez by name; 'Procedure room' is a doctor tile by role; both masked for bhawna -- only the two people the ask named get a new tile.",\n "version": 39,''')
os.makedirs(out, exist_ok=True)
for n, t in (("portal.py", s), ("tile_grants.json", j)):
    open(os.path.join(out, n), "wb").write(t.encode("utf-8"))
    print(n, "->", hashlib.md5(t.encode("utf-8")).hexdigest())
