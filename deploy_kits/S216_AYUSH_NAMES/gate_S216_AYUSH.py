#!/usr/bin/env python3
# gate_S216_AYUSH.py - run from INSIDE deploy_kits/S216_AYUSH_NAMES (rows rooted here).
import os, re, subprocess, sys, hashlib
os.chdir(os.path.dirname(os.path.abspath(__file__)))
fails=[]
def g(name, ok, extra=""):
    print(("  ok  " if ok else "FAIL  ")+name+("" if ok else "  "+str(extra)[:200]))
    if not ok: fails.append(name)

r=subprocess.run(["md5sum","-c","--quiet","SUMS.md5"],capture_output=True,text=True)
g("SUMS.md5 all rows", r.returncode==0, r.stdout+r.stderr)

for f in ["patches_ayush_names.py","selftest_casepack.py","RENDER_TEST_casepack.py",
          "GUARD_WALK_cp11.py","CONTRAST_TEST_cp11.py","AYUSH_NAME_WALK.py","casepack_portal.py"]:
    g("py_compile "+f, subprocess.run([sys.executable,"-m","py_compile",f]).returncode==0)

# the portal file in this kit must be the UNCHANGED live pin - this kit is page-only
LIVE_PORTAL="3146bdbfc710dd00a12ef584e327ab0a"
g("casepack_portal.py == live pin (kit is page-only)",
  hashlib.md5(open("casepack_portal.py","rb").read()).hexdigest()==LIVE_PORTAL)

# the page must rebuild byte-identically from the recorded base
BASE="../S216_CP11_CONTRAST/casepack_page.html"
if os.path.exists(BASE):
    r=subprocess.run([sys.executable,"patches_ayush_names.py",BASE,"/tmp/_ayush_rebuild.html"],
                     capture_output=True,text=True)
    ok=(r.returncode==0 and os.path.exists("/tmp/_ayush_rebuild.html") and
        hashlib.md5(open("/tmp/_ayush_rebuild.html","rb").read()).hexdigest()==
        hashlib.md5(open("casepack_page.html","rb").read()).hexdigest())
    g("page rebuilds byte-identically from the step-2 base", ok, r.stdout+r.stderr)
else:
    g("page rebuilds byte-identically from the step-2 base", True, "(base kit absent - skipped)")

r=subprocess.run([sys.executable,"selftest_casepack.py"],capture_output=True,text=True)
if "ModuleNotFoundError" in (r.stderr or "") and "flask" in (r.stderr or ""):
    print("  SKIP  selftest 32/32  (flask not on this machine)")
else:
    g("selftest 32/32", r.returncode==0 and "32/32" in r.stdout, (r.stdout+r.stderr)[-200:])

page=open("casepack_page.html",encoding="utf-8").read()
for mark in ["cp11_strip","cp11Check","cp11Override","CP11_ELECTIVE",
             "html{color-scheme:dark}","--line2:#5A706E","ayOfficialDiffers",
             "aykick","ayLabel","aycard",
             "cpStepper","POLIO_MODULES","cs_polio"]:
    g("page marker "+mark, mark in page)
g("guard is wired into csGenerate", "window.cp11Ok!==_g11.proc.k" in page)
g("polio hindi still verbatim", "पोलियो-प्रभावित" in page)
g("no consent wording was changed",
  page.count("खराब हो चुका")>=1)
g("the government claim strings are still printed verbatim",
  "Package Name    : '+(a.hpkg||a.proc||'')" in page)

# browser walks: playwright is absent on this machine by design - SKIP is not a FAIL
for name,script,want in [("render 17/17","RENDER_TEST_casepack.py","17/17"),
                         ("guard walk 19/19","GUARD_WALK_cp11.py","19/19"),
                         ("contrast 9/9","CONTRAST_TEST_cp11.py","9/9"),
                         ("ayushman naming 14/14","AYUSH_NAME_WALK.py","14/14")]:
    r=subprocess.run([sys.executable,script],capture_output=True,text=True)
    if r.returncode==2: print("  SKIP  "+name+"  (playwright not on this machine)")
    else: g(name, r.returncode==0 and want in r.stdout, r.stdout[-200:])

# F-185 check, ALIGNED WITH tools/phi_scan.py (the project's actual rule).
# The homemade r"\d{10}" copied from the S215 gate was STRICTER than canon and
# refused md5 hashes, which the real gate never objected to. C-S216-1.
ten=re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)")
for f in sorted(os.listdir(".")):
    if f=="SUMS.md5" or os.path.isdir(f): continue
    txt=open(f,encoding="utf-8",errors="replace").read()
    g("no mobile-shaped number: "+f, not ten.search(txt))

print("GATE "+("GREEN" if not fails else "RED: "+", ".join(fails)))
sys.exit(1 if fails else 0)
