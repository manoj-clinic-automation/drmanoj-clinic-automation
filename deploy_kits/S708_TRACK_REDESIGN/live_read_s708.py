#!/usr/bin/env python3
"""live_read_s708.py -- S708, READ-ONLY on a COPY of a real finance.db: draws the old order list (?old=1) and the new one, and reception's
list, for the owner (English) and Shavez (Roman Hindi), and prints only their SHAPE -- section counts, the viewer queue, sizes, the words'
language -- never a name, a number or a phone. It writes nothing to the database it is given (it works on a temporary copy).
    python3 -B live_read_s708.py <finance code dir> <finance.db>     (assets.db: whatever order_sheet._assets() reaches, else none)"""
import os
import re
import shutil
import sqlite3
import sys
import tempfile

CODE, DB = sys.argv[1], sys.argv[2]
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(CODE)), "shared"))
from flask import Flask                                       # noqa: E402

import porders_s454 as P4                                     # noqa: E402

tmp = tempfile.mkdtemp(prefix="s708live_")
cp = os.path.join(tmp, "f.db")
shutil.copyfile(DB, cp)
before = os.path.getsize(cp)
con = sqlite3.connect(cp, timeout=30)
con.row_factory = sqlite3.Row
app = Flask("s708live")


def draw(path, u, kind, login, fn):
    P4._auth_page = lambda: (u, con, kind, login, None)
    with app.test_request_context(path):
        r = fn()
    return r[0] if isinstance(r, tuple) else r


def shape(name, html):
    secs = re.findall(r'<details class="s7sec[^"]*" id="(\w+)"( open)?><summary>.*?<span class="t">([^<]*)</span><span class="c"[^>]*>(\d+)</span>', html)
    print("%-22s %6d B  sections: %s" % (name, len(html.encode()), " | ".join("%s=%s%s" % (i, n, " OPEN" if o else "") for i, o, t, n in secs)))
    print("%-22s viewer queue %d · View large %d · cards %d · todo lines %d · old-grp %d" % (
        "", html.count('data-vq="1"'), html.count("s7open(this)"), html.count('class="s7c"'), len(re.findall(r'<a href="#sec_\w+" onclick="return s7go', html)),
        len(re.findall(r'class="grp" id="sec_(\w+)">[^<]*· (\d+)', html))))
    grp = re.findall(r'<div class="s7g" id="(g_\w+)">[^<]*· (\d+)', html)
    if grp:
        print("%-22s scan groups: %s" % ("", " ".join("%s=%s" % x for x in grp)))
    old = re.findall(r'class="grp" id="(sec_\w+)">[^<]*· (\d+)', html)
    if old:
        print("%-22s old sections: %s; done %s" % ("", " ".join("%s=%s" % x for x in old), (re.findall(r'id="sec_done"><summary[^>]*>[^<]*· (\d+)', html) or ["-"])[0]))
    for k in ("Traceback", "S708 track page failed", "Error"):
        if k in html:
            print("%-22s !! contains %r" % ("", k))


own = dict(user="manoj", login="manoj", roles=["checker"], _en=True)
shv = dict(user="shavez", login="shavez", roles=["maker"], _en=False)
try:
    ho = draw("/finance/porders/s454/track?old=1", own, "owner", "manoj", P4.track_page)
    shape("owner old", ho)
except Exception as ex:                                       # noqa: BLE001 -- the old page's own fault is not this kit's gate
    ho = ""
    print("owner old              could not be drawn here: %s" % type(ex).__name__)
h = draw("/finance/porders/s454/track", own, "owner", "manoj", P4.track_page)
shape("owner new", h)
if ho:
    old = dict(re.findall(r'class="grp" id="(sec_\w+)">[^<]*· (\d+)', ho))
    new = dict((i, n) for i, o, t, n in re.findall(r'<details class="s7sec[^"]*" id="(\w+)"( open)?><summary>.*?<span class="t">([^<]*)</span><span class="c"[^>]*>(\d+)</span>', h))
    same = all(old.get(k) == new.get(k) for k in ("sec_na", "sec_short", "sec_marg"))
    print("%-22s not arrived / came short / not in Marg: old %s, new %s -- %s" % ("", [old.get(k) for k in ("sec_na", "sec_short", "sec_marg")],
                                                                         [new.get(k) for k in ("sec_na", "sec_short", "sec_marg")], "COUNTS AGREE" if same else "COUNTS DIFFER"))
hi_in_owner = [w for w in ("kijiye", "dabaiye", "nahi aaye", "Kam aaye") if w in h]
print("%-22s Roman Hindi words on the owner's page: %s" % ("", hi_in_owner or "none"))
hs = draw("/finance/porders/s454/track", shv, "sender", "shavez", P4.track_page)
shape("shavez new", hs)
print("%-22s STAFF SIZE %s (%d B; the charter's line is 100 KB)" % ("", "OK" if len(hs.encode()) < 100000 else "OVER", len(hs.encode())))
rec = draw("/finance/porders/s454/rescan", dict(user="reception", login="reception", roles=["maker"], _en=False), "sender", "reception", P4.rescan_page)
print("%-22s %6d B  cards %d · Scan karo %d · lost buttons %d" % ("reception new", len(rec.encode()), rec.count('class="s7c"'), rec.count(">Scan karo<"),
                                                                rec.count("/api/s454/s708/lost'")))
con.close()
print("database copy unchanged in size: %s" % (os.path.getsize(cp) == before))
shutil.rmtree(tmp)
