#!/usr/bin/env python3
"""walk_s424.py -- walk for S424. usage: walk_s424.py <patched clinic_state_backup.py copy> <kit dir>
Runs gather() on scratch trees only (every real source list re-pointed at scratch). Prints WALK OK n/n."""
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

PATCHED, KIT = sys.argv[1], sys.argv[2]
sys.path.insert(0, KIT)
import apply_s424 as ap   # noqa: E402
N = [0, 0]
def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1; print("  ok  " + name)
    else:
        print("  RED %s %s" % (name, extra))

check("second apply changes nothing", ap.apply(PATCHED) == "already")
spec = importlib.util.spec_from_file_location("csb", PATCHED)
csb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csb)
T = tempfile.mkdtemp(prefix="s424_")
cp, vt = os.path.join(T, "casepack"), os.path.join(T, "vitals")
for p, body in ((cp + "/case_ledger.csv", "Case_ID\nC-1\n"), (cp + "/consent_ledger.csv", "x\n"),
                (cp + "/casepack_page.html", "<html>"), (cp + "/casepack_portal.py", "code"),
                (cp + "/tr_dict.json", "{}"), (cp + "/med_list.csv.tmp", "half"),
                (cp + "/case_archive/2026/RAM_4321/C-2026-000001_RAM_bundle_v1_2026-09-01.json", "{}"),
                (cp + "/case_archive/2026/RAM_4321/C-2026-000001_consent_1.html", "<p>"),
                (cp + "/case_archive/2026/RAM_4321/service_account.json", "{secret}"),
                (vt + "/vitals_ledger.csv", "Vitals_ID\n"), (vt + "/plan_ledger.csv", "Plan_ID\n"),
                (vt + "/vitals_page.html", "<html>"),
                (vt + "/plan_archive/2026/PU-0001/2026-09-27_P-2026-000015_patient.pdf", "%PDF-1.4"),
                (vt + "/plan_archive/pending/7777_x/2026-09-27_P-2026-000016_physio.pdf", "%PDF-1.4"),
                (vt + "/__pycache__/x.pyc", "c")):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(body)
db = os.path.join(cp, "cases.db"); c = sqlite3.connect(db); c.execute("CREATE TABLE t(a)"); c.commit(); c.close()
csb.SRC_FILES, csb.SRC_DIRS, csb.SRC_TREES = [], [], [cp, vt, os.path.join(T, "absent")]
dest = os.path.join(T, "stage"); os.makedirs(dest)
g = csb.gather({}, dest, integrity_fatal=True)
got = sorted(e[0] for e in g.entries if e[0].startswith("data/"))
want = ["data/casepack/case_archive/2026/RAM_4321/C-2026-000001_RAM_bundle_v1_2026-09-01.json",
        "data/casepack/case_archive/2026/RAM_4321/C-2026-000001_consent_1.html",
        "data/casepack/case_ledger.csv", "data/casepack/casepack_page.html", "data/casepack/cases.db",
        "data/casepack/consent_ledger.csv", "data/casepack/tr_dict.json",
        "data/vitals/plan_archive/2026/PU-0001/2026-09-27_P-2026-000015_patient.pdf",
        "data/vitals/plan_archive/pending/7777_x/2026-09-27_P-2026-000016_physio.pdf",
        "data/vitals/plan_ledger.csv", "data/vitals/vitals_ledger.csv", "data/vitals/vitals_page.html"]
check("every data file at every depth, PDFs included, paths preserved", got == want, got)
check("code, __pycache__ and a temp file are NOT taken", not any(x.endswith((".py", ".pyc", ".tmp")) for x in got))
check("the secret-named file is skipped and counted", g.secrets_skipped == 1 and not any("service_account" in x for x in got))
check("the sqlite file went through the integrity check", any(os.path.basename(s) == "cases.db" for s, _ in g.databases), g.databases)
check("for FATAL 41 each tree is ONE source; its files are not", g.sources_present == [cp, vt], g.sources_present)
check("an absent tree is 'missing', not fatal", os.path.join(T, "absent") in g.sources_missing)
check("the files really are in the stage", os.path.isfile(os.path.join(dest, got[-5])))
shutil.rmtree(T, ignore_errors=True)
print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
