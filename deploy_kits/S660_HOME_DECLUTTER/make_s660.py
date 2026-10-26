#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s660.py -- kit S660_HOME_DECLUTTER (the parent, S357, 26-Oct-2026). The owner's "build it" (07:19 IST) on the S357 analysis of
his PWA home, with his two changes: Call Tracker STAYS; the Sanjeevni chat's accordion (S657) is kept. Built ON S657's TO bytes.
  /root/portal/portal.py          5f4f3738 (S657 TO) -> TO   3 counted edits:
        P1 "WhatsApp Approvals" (the MyOperator vendor panel) moves from the Calls & WhatsApp group to System
        P2 a new tile "Attendance correction" (/register/attcorr, doctor) in the Staff group, after "Salary -- approve & lock"
        P3 WHO labels on a FOLDED group's staff screens for every folder, as S657 did for Sanjeevni's: Parchi desk . Shavez,
           Kal ke procedures . Shavez, Physiotherapy . Bhati, Petty book . Bhati, Check karein . staff, Report baaki . staff,
           Docterz daily collection . reception. Display only, folded view only (his login); a flat list (every staff login) is unchanged.
  /root/portal/tile_grants.json   171f94f8 (S657 TO) -> TO   v40 -> v41: manoj's mask gains "Clinic", "OPD & X-ray/Proc Slips",
        "Clinic Gist" -- his home only; the pages stay live; every other login byte-for-byte as v40.
Usage: python make_s660.py <root holding portal/portal.py + portal/tile_grants.json at S657's TO bytes> <out dir>"""
import hashlib, os, sys

FROM = {"portal/portal.py": "5f4f37381305883937b1382b17cdb8ca", "portal/tile_grants.json": "171f94f81f23a911fad3d36a9f191dfc"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "%s is not %s (S657 must be installed first)" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:90])
    T[r] = T[r].replace(old, new, 1)


P = "portal/portal.py"
# P1 -- WhatsApp Approvals -> System
rep(P, '''    "Follow-up WhatsApps": "Calls & WhatsApp", "WhatsApp Approvals": "Calls & WhatsApp",
''', '''    "Follow-up WhatsApps": "Calls & WhatsApp", "WhatsApp Approvals": "System",                 # S660: the vendor panel is a system thing
''')
# P2 -- the Attendance correction tile (D786) and its group
rep(P, '''    {"icon": "\\U0001F4B0", "name": "Salary \\u2014 approve & lock",
     "desc": "From Attendance + Ledger deductions", "live": True,
     "url": "/register/salary",
     "roles": ["doctor"]},

''', '''    {"icon": "\\U0001F4B0", "name": "Salary \\u2014 approve & lock",
     "desc": "From Attendance + Ledger deductions", "live": True,
     "url": "/register/salary",
     "roles": ["doctor"]},

    {"icon": "\\U0001F4DD", "name": "Attendance correction",                                       # S660 (D786)
     "desc": "Month-end: reception enters, Shavez checks, you approve & save", "live": True,
     "url": "/register/attcorr",
     "roles": ["doctor"]},

''')
rep(P, '''    "Salary \\u2014 approve & lock": "Staff", "Staff Ledger": "Staff",
''', '''    "Salary \\u2014 approve & lock": "Staff", "Staff Ledger": "Staff", "Attendance correction": "Staff",   # S660
''')
# P3 -- WHO labels for every folded group (display only)
rep(P, '''S657_STAFF_GROUP = ("Sanjeevni staff screens", "\\U0001F440", "What each person sees \\u2014 Darpan, Bhati, Amir, Shavez")
''', '''S657_STAFF_GROUP = ("Sanjeevni staff screens", "\\U0001F440", "What each person sees \\u2014 Darpan, Bhati, Amir, Shavez")
# S660 (the owner, 26-Oct-2026): the same label on the other folders' staff screens, when the folder is FOLDED (his login). Display only.
S660_WHO = {"Parchi desk": "Shavez", "Kal ke procedures": "Shavez", "Physiotherapy": "Bhati", "Petty book": "Bhati",
            "Check karein": "staff", "Report baaki": "staff", "Docterz daily collection": "reception"}
''')
rep(P, '''        out.append((label, items, folded, _group_slug(label), icon, desc))
    return out
''', '''        if folded:                                                                           # S660: whose screen, on a folded folder
            items = [dict(t, who=S660_WHO[t["name"]]) if t["name"] in S660_WHO and not t.get("who") else t for t in items]
        out.append((label, items, folded, _group_slug(label), icon, desc))
    return out
''')

G = "portal/tile_grants.json"
rep(G, ''' "version": 40,
''', ''' "version": 41,
''')
rep(G, '''   "mask": [
    "Daily Sale",
    "Order Medicines",
    "Marg Purchases",
    "Stock milaan"
   ],
   "groups": [
    "Patients",
    "Surgery",
    "Sanjeevni Medicos",
''', '''   "mask": [
    "Daily Sale",
    "Order Medicines",
    "Marg Purchases",
    "Stock milaan",
    "Clinic",
    "OPD & X-ray/Proc Slips",
    "Clinic Gist"
   ],
   "groups": [
    "Patients",
    "Surgery",
    "Sanjeevni Medicos",
''')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print(r, FROM[r][:8], "->", hashlib.md5(t.encode("utf-8")).hexdigest())
