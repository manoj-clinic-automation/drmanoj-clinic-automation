#!/usr/bin/python3
# make_s786.py -- kit S786_ONLINE_BOOKING (S428, 11-Nov-2026, the parent; the owner 07:15 / 07:59 IST: online bookings paid on
# Docterz shown to staff). Usage: make_s786.py <live portal.py> <live owner_console.py> <live tile_grants.json> <out dir>
# Exact replacements on the live bytes (portal.py 34750b24 and owner_console.py 1a3d4fd4 -- S785; tile_grants.json 66de5e20 -- v45,
# S769); every anchor must occur once. tile_grants.json is rewritten in its own format (indent 1, UTF-8, newline at the end).
import hashlib, json, os, sys
pp, oc, tg, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
def load(p, want):
    b = open(p, "rb").read()
    assert hashlib.md5(b).hexdigest().startswith(want), "not the live %s (%s)" % (os.path.basename(p), want)
    return b.decode("utf-8")
def rp(t, a, b):
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    return t.replace(a, b)

P = load(pp, "34750b24")
P = rp(P, '''     "url": "/finance/checks",
     "roles": ["doctor"]},
''', '''     "url": "/finance/checks",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4B3", "name": "Online booking",
     # S786 NEW (the owner, 11-Nov-2026 07:15 / 07:59 IST). Consultations booked and paid online through Docterz (Razorpay): name,
     # clinic ID, the FULL mobile, Rs 600 paid, the booked time; outside Mon-Sat 11:00-13:30 / 19:00-20:30 staff call the patient.
     # Served by online_booking_portal.py (/portal/booking). Granted by name in tile_grants.json v46 to reception, shivani,
     # alisha, shavez; the doctors hold it by role (Dr Bhawna's 'only' list keeps it off her home).
     "desc": "Online paid \\u00b7 samay \\u00b7 phone",
     "live": True,
     "url": "/portal/booking",
     "roles": ["doctor"]},
''')
P = rp(P, '''    "Patient records": "Patients", "Check karein": "Patients", "Report baaki": "Patients",
''', '''    "Patient records": "Patients", "Check karein": "Patients", "Report baaki": "Patients",
    "Online booking": "Patients",                                                            # S786
''')
P = rp(P, '''if _PORTAL_PUSH:
    try:
        portal_push.install(app, login_required, _sso_user)
    except Exception:
        _PORTAL_PUSH = False
''', '''if _PORTAL_PUSH:
    try:
        portal_push.install(app, login_required, _sso_user)
    except Exception:
        _PORTAL_PUSH = False

# S786_ONLINE_BOOKING: /portal/booking -- the online bookings paid on Docterz (online_booking_portal.py; optional: absent = no page)
try:
    import online_booking_portal
    online_booking_portal.install(app, login_required, _sso_user)
except Exception as _e_s786:                                          # noqa: BLE001 -- the portal stands without it
    import sys as _sys_s786
    print("online_booking_portal NOT mounted: %r" % (_e_s786,), file=_sys_s786.stderr)
''')

O = load(oc, "1a3d4fd4")
O = rp(O, '''    xl = _s785_xray_line(con)                                          # S785: X-ray photos that are now his and Shavez's
    if xl:
        lines.append(xl)
    n, late = len(mine) + (1 if xl else 0), sum(1 for i in mine if i["late"])
''', '''    xl = _s785_xray_line(con)                                          # S785: X-ray photos that are now his and Shavez's
    if xl:
        lines.append(xl)
    bl = _s786_booking_line(con)                                       # S786: online bookings paid on Docterz
    if bl:
        lines.append(bl)
    n, late = len(mine) + (1 if xl else 0) + (1 if bl else 0), sum(1 for i in mine if i["late"])
''')
O = rp(O, '''def _s785_xray_line(con):
''', '''def _s786_when(a):
    try:
        t = dt.datetime.strptime(a or "", "%Y-%m-%d %H:%M")
    except ValueError:
        return "time not read"
    return "%s %d %s, %d:%02d %s" % (t.strftime("%a"), t.day, t.strftime("%b"), (t.hour % 12) or 12, t.minute, "PM" if t.hour >= 12 else "AM")


def _s786_booking_line(con):
    """S786 (the owner, 11-Nov-2026 07:15 / 07:59 IST): a Needs-you line while an online booking paid on Docterz is booked for
    today or later -- red while one booked outside his timings has not been called by staff. None when there are none, or
    anything fails (no table yet: nothing has come)."""
    try:
        today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
        rs = con.execute("SELECT name, appt_at, out_of_hours, COALESCE(called_at,'') FROM online_booking "
                         "WHERE substr(COALESCE(appt_at,''),1,10) >= ? ORDER BY appt_at LIMIT 20", (today,)).fetchall()
    except Exception:                                                  # noqa: BLE001 -- the section stands without it
        return None
    if not rs:
        return None
    need = sum(1 for r in rs if r[2] and not r[3])
    if len(rs) == 1:
        t = "Online booking paid on Docterz: %s, %s" % (rs[0][0] or "?", _s786_when(rs[0][1]))
    else:
        t = "%d online bookings paid on Docterz, the next %s" % (len(rs), _s786_when(rs[0][1]))
    if need:
        t += " -- %d outside your timings, staff have not called yet" % need
    return L("b" if need else "w", t, href="/portal/booking", link="Online booking")


def _s785_xray_line(con):
''')

G = json.loads(load(tg, "66de5e20"))
assert G.get("version") == 45, "tile_grants.json is not v45"
for u in ("reception", "shivani", "alisha", "shavez"):
    ex = G["users"][u].setdefault("extra", [])
    assert "Online booking" not in ex
    ex.append("Online booking")
G["version"] = 46
G["_note"] += (" v46 (S786, the parent, 11-Nov-2026; the owner 07:15 / 07:59 IST): the NEW tile 'Online booking' (/portal/booking -- "
               "consultations booked and paid online on Docterz: name, clinic ID, full mobile, the booked time, the call when it is "
               "outside the timings) granted by name to reception, shivani, alisha and shavez; the doctors hold it by role. The page's "
               "own gate reads THIS file: who is shown the tile may open the page. Nothing else in this file moves.")
GT = json.dumps(G, indent=1, ensure_ascii=False) + "\n"

os.makedirs(os.path.join(out, "portal"), exist_ok=True); os.makedirs(os.path.join(out, "finance"), exist_ok=True)
for rel, t in (("portal/portal.py", P), ("finance/owner_console.py", O), ("portal/tile_grants.json.s786", GT)):
    open(os.path.join(out, rel), "wb").write(t.encode("utf-8"))
    print("written", rel, hashlib.md5(t.encode("utf-8")).hexdigest()[:8])
