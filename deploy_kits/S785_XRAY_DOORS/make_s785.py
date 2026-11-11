#!/usr/bin/python3
# make_s785.py -- kit S785_XRAY_DOORS (S427, 11-Nov-2026, the parent; the owner 06:34-06:38 IST: "cannot find the flow from my portal
# page or through my command console" -> "go"). Usage: make_s785.py <live portal.py> <live owner_console.py> <out dir>
# Exact replacements on the live bytes (portal.py 59b5c252, owner_console.py 27d31775); every anchor must occur once.
import hashlib, os, sys
pp, oc, out = sys.argv[1], sys.argv[2], sys.argv[3]
def load(p, want):
    b = open(p, "rb").read()
    assert hashlib.md5(b).hexdigest().startswith(want), "not the live %s (%s)" % (os.path.basename(p), want)
    return b.decode("utf-8")
def rp(t, a, b):
    assert t.count(a) == 1, "anchor not once: " + a[:70]
    return t.replace(a, b)
P = load(pp, "59b5c252")
P = rp(P, '''     "url": "/finance/records",
     "roles": ["doctor"]},
''', '''     "url": "/finance/records",
     "roles": ["doctor"]},
    {"icon": "\\U0001FA7B", "name": "X-ray photos",
     # S785 NEW (the owner, 11-Nov-2026 06:38 IST). His X-ray page: the photos waiting to be filed (older than 7 days his and
     # Shavez's), the ones filed by themselves, the X-rays with no X-ray slip, the lab reports with no blood slip. The doctors only
     # (Dr Bhawna's 'only' list keeps it off her home); the page's own gate is unit 'records', unchanged.
     "desc": "Photos waiting \\u00b7 filed \\u00b7 no X-ray slip",
     "live": True,
     "url": "/finance/records/xray-check",
     "roles": ["doctor"]},
''')
P = rp(P, '''    "Patient records": "Patients", "Check karein": "Patients", "Report baaki": "Patients",
''', '''    "Patient records": "Patients", "Check karein": "Patients", "Report baaki": "Patients",
    "X-ray photos": "Patients",                                                              # S785
''')
O = load(oc, "27d31775")
O = rp(O, '''    n, late = len(mine), sum(1 for i in mine if i["late"])
    if not lines:
        lines.append(L("g", "Nothing is waiting for you."))''', '''    xl = _s785_xray_line(con)                                          # S785: X-ray photos that are now his and Shavez's
    if xl:
        lines.append(xl)
    n, late = len(mine) + (1 if xl else 0), sum(1 for i in mine if i["late"])
    if not lines:
        lines.append(L("g", "Nothing is waiting for you."))''')
O = rp(O, '''def _sec_needs_map(con, cx):
''', '''def _s785_xray_line(con):
    """S785 (the owner, 11-Nov-2026 06:38 IST): a Needs-you line while X-ray photos older than check_screens.STAFF_DAYS wait --
    since S782 they are off reception's list and his and Shavez's to file. None when there are none, or anything fails."""
    try:
        import check_screens as CS                                     # noqa: PLC0415
        old = len(CS._parked(con)) - len(CS._parked(con, recent=True))
        days = int(CS.STAFF_DAYS)
    except Exception:                                                  # noqa: BLE001 -- the section stands without it
        return None
    if old <= 0:
        return None
    return L("w", "%d X-ray photo%s waiting more than %d days -- yours and Shavez's to file" % (old, "" if old == 1 else "s", days),
             href="/finance/records/xray-check", link="X-ray photos")


def _sec_needs_map(con, cx):
''')
O = rp(O, '''        t = ("X-ray photos & lab reports: %d photo%s waiting for staff · %d X-ray%s''', '''        t = ("X-ray photos & lab reports: %d photo%s waiting to be filed · %d X-ray%s''')
os.makedirs(os.path.join(out, "portal"), exist_ok=True); os.makedirs(os.path.join(out, "finance"), exist_ok=True)
for rel, t in (("portal/portal.py", P), ("finance/owner_console.py", O)):
    open(os.path.join(out, rel), "wb").write(t.encode("utf-8"))
    print("written", rel, hashlib.md5(t.encode("utf-8")).hexdigest()[:8])
