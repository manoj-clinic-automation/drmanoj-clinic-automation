#!/usr/bin/env python3
"""check_portal_s382.py -- kit S382_REPORT_BAAKI. Loads a SCRATCH copy of the portal (the kit's portal.py beside the live
modules) with the edited grants file and says which of the tiles each person would see. Changes nothing.
  TILE_GRANTS_FILE=<edited copy> python3 check_portal_s382.py <scratch portal dir>"""
import importlib.util, os, sys
d = os.path.abspath(sys.argv[1]); sys.path.insert(0, d); os.chdir(d)
s = importlib.util.spec_from_file_location("portal_s382", os.path.join(d, "portal.py"))
P = importlib.util.module_from_spec(s); s.loader.exec_module(P)
def sees(u, role):
    return {t["name"] for _, ts in P._visible_sections(role, False, u) for t in ts}
want = {"sukhveer": True, "alisha": True, "shivani": True, "shavez": True, "bhati": False, "darpan": False}
bad = [u for u, w in want.items() if ("Report baaki" in sees(u, "staff")) != w]
doc = "Report baaki" in sees("manoj", "doctor")
att = "Meri attendance" in sees("sukhveer", "staff") or "Attendance" in sees("sukhveer", "staff")
print("PORTAL_S382 %s: Report baaki for sukhveer/alisha/shivani/shavez and the doctor%s; sukhveer's attendance tile %s"
      % ("OK" if not bad and doc else "RED", "" if not bad else (" -- WRONG for " + ", ".join(bad)), "present" if att else "NOT SEEN"))
