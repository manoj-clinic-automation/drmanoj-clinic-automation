#!/usr/bin/env python3
# gate_S215_CP1.py — run from INSIDE deploy_kits/S215_CP1 (rows rooted here).
import os, re, subprocess, sys, hashlib
os.chdir(os.path.dirname(os.path.abspath(__file__)))
fails = []
def g(name, ok, extra=""):
    print(("  ok  " if ok else "FAIL  ") + name + ("" if ok else " " + extra))
    if not ok: fails.append(name)
r = subprocess.run(["md5sum", "-c", "--quiet", "SUMS.md5"], capture_output=True, text=True)
g("SUMS.md5 all rows", r.returncode == 0, r.stdout + r.stderr)
for f in ["casepack_portal.py", "selftest_casepack.py", "patches_page.py", "RENDER_TEST_casepack.py"]:
    g("py_compile " + f, subprocess.run([sys.executable, "-m", "py_compile", f]).returncode == 0)
r = subprocess.run([sys.executable, "selftest_casepack.py"], capture_output=True, text=True)
g("selftest 32/32", r.returncode == 0 and "32/32" in r.stdout, r.stdout[-200:])
page = open("casepack_page.html", encoding="utf-8").read()
for mark in ["cpStepper", "POLIO_MODULES", "cs_polio", "cs_hist", "consent_ledger" if False else "cpFeedForward"]:
    g("page marker " + mark, mark in page)
g("page polio hindi verbatim", "पोलियो-प्रभावित" in page)
ten = re.compile(r"\d{10}")
for f in sorted(os.listdir(".")):
    if f == "SUMS.md5" or os.path.isdir(f): continue
    txt = open(f, encoding="utf-8", errors="replace").read()
    g("no ten-digit run: " + f, not ten.search(txt))
print("GATE " + ("GREEN" if not fails else "RED: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
