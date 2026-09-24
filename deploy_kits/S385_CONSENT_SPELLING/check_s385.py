#!/usr/bin/env python3
"""check_s385.py -- kit S385_CONSENT_SPELLING, on the VPS (no browser there): the kit's casepack_portal.py routes on a
SCRATCH case folder, and the kit's page carries the spelling box; the live page is the negative control.
The browser walk (walk_s385.py, 10/10) was run offline in headless Chromium.
  python3 check_s385.py <kit dir> <live casepack_page.html>"""
import importlib.util, json, os, sys, tempfile
kit, live = sys.argv[1], sys.argv[2]
tmp = tempfile.mkdtemp(prefix="s385chk_")
os.environ["PORTAL_CASEPACK_DIR"] = tmp
os.environ["PORTAL_CONSOLE_DB"] = os.path.join(tmp, "x.db"); os.environ["PORTAL_FINANCE_DB"] = os.path.join(tmp, "y.db")
from flask import Flask
s = importlib.util.spec_from_file_location("cp385", os.path.join(kit, "casepack_portal.py")); cp = importlib.util.module_from_spec(s); s.loader.exec_module(cp)
app = Flask("c"); cp.register(app, lambda f: f, lambda: "manoj"); c = app.test_client()
bad = []
if c.get("/portal/casepack/trdict").get_json() != {"ok": True, "dict": {}}: bad.append("empty dictionary read")
j = c.post("/portal/casepack/trdict", json={"pairs": {"Walk Name": "वॉक नाम", "bad": "latin only", "": "क"}}).get_json()
if not (j and j.get("ok") and j.get("saved") == 1): bad.append("save: %s" % j)
if c.get("/portal/casepack/trdict").get_json().get("dict") != {"walk name": "वॉक नाम"}: bad.append("read back")
pg = open(os.path.join(kit, "casepack_page.html"), encoding="utf-8").read()
lv = open(live, encoding="utf-8").read()
for m in ('id="cs_fix"', "function csFixApply", "/portal/casepack/trdict", "csGenerate=async function"):
    if m not in pg: bad.append("page lacks " + m)
if 'id="cs_fix"' in lv: bad.append("negative control: the live page already has the box")
print("CHECK_S385 %s" % ("OK: the spelling routes save and read on a scratch folder; the page carries the box; the live page does not"
                         if not bad else "RED: " + "; ".join(bad)))
