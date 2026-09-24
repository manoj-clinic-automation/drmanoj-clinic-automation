#!/usr/bin/env python3
"""check_portal_s383.py -- kit S383_REPORT_NAMES. Loads a SCRATCH copy of the portal (the kit's portal.py beside the live
modules), renders the Clinic Gist page's template and reads the Gist tile's script. Changes nothing.
  python3 check_portal_s383.py <scratch portal dir>"""
import importlib.util, os, sys
d = os.path.abspath(sys.argv[1]); sys.path.insert(0, d); os.chdir(d)
s = importlib.util.spec_from_file_location("portal_s383", os.path.join(d, "portal.py"))
P = importlib.util.module_from_spec(s); s.loader.exec_module(P)
from flask import render_template_string
bad = []
with P.app.test_request_context("/portal/gist"):
    for v in ({"ok": False}, {"ok": True, "stale": False, "age_min": 3}):
        try:
            h = render_template_string(P.GIST_HTML, v=v, g={"sources_ok": True, "notes": [], "stale_after_min": 60}, who={"user": "manoj"})
        except Exception as e:                           # noqa: BLE001
            bad.append("gist page did not render: %s" % str(e)[:120]); continue
        if 'id="gReports"' not in h or "/finance/slips/api/pending-counts" not in h:
            bad.append("gist page has no reports card")
src = open(os.path.join(d, "portal.py"), encoding="utf-8").read()
if src.count("/finance/slips/api/pending-counts") < 2 or "Promise.all([calls,reps])" not in src:
    bad.append("the Gist tile line does not read the counts")
print("PORTAL_S383 %s%s" % ("OK: the Gist page carries the Reports card; the tile line reads the counts" if not bad else "RED: ",
                            "; ".join(bad)))
