#!/usr/bin/env python3
"""walk_s896.py -- kit S896 (PC spare mode) on a MADE-UP root. python3 walk_s896.py <kit_dir>"""
import importlib.util, os, sys, tempfile, shutil
KIT = os.path.abspath(sys.argv[1]); fails = []
def check(n, c):
    print("  %s %s" % ("ok  " if c else "FAIL", n))
    if not c: fails.append(n)
spec = importlib.util.spec_from_file_location("dp896", os.path.join(KIT, "docterz_pickup.py")); DP = importlib.util.module_from_spec(spec); spec.loader.exec_module(DP)
root = tempfile.mkdtemp(prefix="walk896_")
trk = os.path.join(root, "trk"); dl = os.path.join(root, "dl"); ar = os.path.join(root, "ar")
for d in (trk, dl, ar, os.path.join(trk, "uploads"), os.path.join(trk, "outputs")): os.makedirs(d)
open(os.path.join(trk, "processor.py"), "w").write("def run_daily(*a, **k):\n    raise RuntimeError('never here')\n")
seen = {}
class Spy(DP.Pass):
    def run(self):
        seen["vps"] = self.vps_upload; seen["pj"] = self.patient_push; seen["lines"] = list(self.lines); return 0
    def refresh_latest(self, sheet_push=None):
        seen["sheet"] = sheet_push; return 0
DP.Pass = Spy
base = ["--tracker", trk, "--downloads", dl, "--archive", ar, "--dry-run"]
print("== without the flag: the sends are the defaults")
seen.clear(); DP.main(base)
check("vps_upload default (None -> push_to_vps)", seen.get("vps") is None)
check("patient_push default (None -> push_patient_join.py)", seen.get("pj") is None)
seen.clear(); DP.main(base + ["--refresh-latest"])
check("refresh: sheet_push default (None -> push_followups_today.py)", seen.get("sheet") is None)
print("== with the flag: nothing is sent, everything else runs")
open(os.path.join(ar, DP.SPARE_FLAG), "w").close()
seen.clear(); DP.main(base)
check("vps_upload replaced; says SPARE MODE, ok=True", callable(seen.get("vps")) and seen["vps"]("x/Staff_Action_Today_2026-11-21.xlsx") == (True, "SPARE MODE: Staff_Action_Today_2026-11-21.xlsx not sent (the server makes the list)"))
check("patient_push replaced; ok=True with a tail line", callable(seen.get("pj")) and seen["pj"][0] if False else callable(seen.get("pj")) and seen["pj"]()[0] is True)
check("the pass says SPARE MODE once", any("SPARE MODE" in l for l in seen.get("lines", [])))
seen.clear(); DP.main(base + ["--refresh-latest"])
check("refresh: the Sheet write replaced; ok=True", callable(seen.get("sheet")) and seen["sheet"]("x")[0] is True)
print("== CONTROL: the live docterz_pickup.py (ddbed001) ignores the flag")
LIVE = os.path.expanduser("~/mnt/followup_tracker_local_test_kit/local_test_kit/followup_tracker/docterz_pickup.py")
spec2 = importlib.util.spec_from_file_location("dplive", LIVE); DL = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(DL)
class Spy2(DL.Pass):
    def run(self):
        seen["vps"] = self.vps_upload; return 0
DL.Pass = Spy2; seen.clear(); DL.main(base)
check("CONTROL red: live code keeps the default send with the flag present", seen.get("vps") is None and not hasattr(DL, "SPARE_FLAG"))
print("== the watcher")
s = open(os.path.join(KIT, "watch_and_push_followups.py"), encoding="utf-8").read()
check("watcher: flag checked first in run_push, returns True (marked seen, never pushed)", "if os.path.exists(SPARE_FLAG):" in s and s.index("if os.path.exists(SPARE_FLAG):") < s.index("if not os.path.exists(PUSH_SCRIPT):"))
check("watcher flag path is the archive's _SPARE_MODE.txt", 'SPARE_FLAG = r"D:\\Downloads\\DocterzArchive\\_SPARE_MODE.txt"' in s)
shutil.rmtree(root, ignore_errors=True)
print("WALK: %d failure(s) of 10" % len(fails)); sys.exit(1 if fails else 0)
