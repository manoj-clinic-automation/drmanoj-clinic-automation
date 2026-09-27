#!/usr/bin/env python3
"""apply_s423_portal.py -- kit S423_VITALS_VPS -- three anchored edits to /root/portal/portal.py (read whole at
S284 from the 27-Sep bundle, 912a1d82; drift 0). Idempotent. usage: apply_s423_portal.py <portal.py>
  1. the Vitals & Plan tile: /portal/vitals, no longer PC-only (same name, so every grant and mask still applies)
  2. its section: Clinic (beside the Surgical Case Pack) instead of Clinic PC tools
  3. vitals_portal mounted right after the Case Pack, behind the Case Pack's own gate, failing loud on its page"""
import sys

TAG = "# S423 (F-598): VITALS & PLAN ON THE SERVER"
EDITS = [
    ('''    {"icon": "\\U0001FA7A", "name": "Vitals & Plan",
     "desc": "clinic_writer \\u2014 Vitals \\u00b7 Nutrition \\u00b7 Physio", "live": True,
     "url": "http://localhost:5057", "roles": ["doctor"], "pc_only": True},
''', '''    {"icon": "\\U0001FA7A", "name": "Vitals & Plan",
     "desc": "Vitals \\u00b7 Nutrition \\u00b7 Physio", "live": True,
     "url": "/portal/vitals", "roles": ["doctor"]},                  # S423 (F-598): on the server; PC copy = fallback
'''),
    ('"Vitals & Plan": "Clinic PC tools"', '"Vitals & Plan": "Clinic"'),
    ('''            "Surgical Case Pack failed to load: " + CASEPACK_IMPORT_ERR, 500)

''', '''            "Surgical Case Pack failed to load: " + CASEPACK_IMPORT_ERR, 500)


# ---------------------------------------------------------------------------
# S423 (F-598): VITALS & PLAN ON THE SERVER -- logic in vitals_portal.py beside this file,
# the page and every record under /root/wa/vitals/ (PHI store, never in the repository).
# Owner-only, behind the Case Pack's own gate. The clinic PC's copy stays as the fallback.
# ---------------------------------------------------------------------------
try:
    import vitals_portal
    vitals_portal.register(
        app, casepack_required,
        lambda: ((_sso_user(request) or {}).get("user") or "doctor"))
    VITALS_IMPORT_ERR = ""
except Exception as _vp_e:                      # fail loud on the page, never brick the portal
    VITALS_IMPORT_ERR = str(_vp_e)

    @app.route("/portal/vitals")
    @login_required
    def _vitals_broken():
        return make_response(
            "Vitals & Plan failed to load: " + VITALS_IMPORT_ERR, 500)

'''),
]


def apply(path):
    s = open(path, encoding="utf-8", newline="").read()
    if TAG in s:
        return "already"
    for old, new in EDITS:
        if s.count(old) != 1:
            raise SystemExit("REFUSED: an anchor is not in portal.py exactly once: %r" % old[:70])
    for old, new in EDITS:
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s)
    return "patched"


if __name__ == "__main__":
    print("portal.py :", apply(sys.argv[1]))
