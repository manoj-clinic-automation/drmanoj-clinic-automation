#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s616.py -- kit S616 (S336, 22-Oct-2026): the owner's 'Tasks & messages' tile on the portal home.

    python3 walk_s616.py <from_portal.py> <to_portal.py> <grants.json> <from_panel.html> <to_panel.html>

The home page rendered from both files for every login that matters (no request, no SSO, no live file touched):
  - the doctor's home carries the tile, hidden, opening /finance/aaj?tab=tasks, and its script asks the Voicenotes door;
  - nobody else's home carries it; every login's tiles and groups are exactly as before;
  - the doctor's page is the FROM page plus the two inserted blocks, byte for byte;
  - every inline script parses (node --check), when node is on this machine;
  - the panel opens on Tasks for ?tab=tasks and is named 'Staff lists & tasks'.
Exit 0 = GREEN (last line 'WALK OK ...'); with the FROM files as TO it goes RED.
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

LOGINS = [("manoj", "doctor"), ("bhawna", "doctor"), ("shavez", "manager"), ("shivani", "staff"), ("alisha", "staff"),
          ("reception", "staff"), ("amir", "staff"), ("darpan", "staff"), ("bhati", "staff")]
passed, failed = [], []


def check(c, label):
    (passed if c else failed).append(label)
    print(("  ok   " if c else "  FAIL ") + label)
    return c


def load(path, grants, tag):
    os.environ["TILE_GRANTS_FILE"] = grants
    os.environ.setdefault("PORTAL_TOKEN_SEED", "walk-seed")
    for mod in ("clinic_sso", "clinic_users", "tracker_pass", "portal_push", "portal_config"):
        sys.modules.pop(mod, None)
    spec = importlib.util.spec_from_file_location("portal_" + tag, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["portal_" + tag] = m
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spec.loader.exec_module(m)
    return m


def render(m, user, role):
    sections = m._visible_sections(role, False, user)
    with m.app.test_request_context("/portal"):
        kw = dict(sections=sections, sso=False, who={"user": user, "role": role}, role=role, pc=False, s444_nowork=False)
        if hasattr(m, "_home_blocks"):
            kw["blocks"] = m._home_blocks(sections, m._folders_for(user))
        return sections, m.render_template_string(m.PORTAL_HTML, **kw)


def names(sections):
    return [t["name"] for _g, items in sections for t in items]


def js_ok(page):
    node = shutil.which("node")
    if not node:
        return None
    for sc in re.findall(r"<script>(.*?)</script>", page, re.S):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
            fh.write(sc)
        r = subprocess.run([node, "--check", fh.name], capture_output=True, text=True)
        os.remove(fh.name)
        if r.returncode != 0:
            return False
    return True


frm, to, grants, pfrom, pto = sys.argv[1:6]
A = load(frm, grants, "from")
B = load(to, grants, "to")
_s, pm = render(B, "manoj", "doctor")
if not check('id="taskTile"' in pm, "the doctor's home carries the Tasks & messages tile"):
    print("WALK RED S616: no tile (the S586 file)")
    sys.exit(1)
check('<a class="tasktile" id="taskTile" href="/finance/aaj?tab=tasks" target="_blank" rel="noopener" hidden>' in pm,
      "the tile opens /finance/aaj?tab=tasks and starts hidden")
check("Tasks &amp; messages" in pm and "fetch('/finance/aaj/api/vn'" in pm and "/finance/aaj/api/switch?panel=1" in pm,
      "its script asks the Voicenotes door first, then the panel's tasks")
check(pm.find('id="taskTile"') < pm.find('<div class="strip">') and pm.find('id="todayTile"') < pm.find('id="taskTile"'),
      "it sits below Today and above the strip")
for user, role in LOGINS:
    sa, pa = render(A, user, role)
    sb, pb = render(B, user, role)
    check(names(sa) == names(sb) and [g for g, _i in sa] == [g for g, _i in sb],
          "%s/%s: the same tiles and groups as before (%d)" % (user, role, len(names(sb))))
    if role != "doctor":
        pbs = re.sub(r"/\* S616: the owner's 'Tasks & messages' tile.*?\n\}\)\(\);\n", "", pb, count=1, flags=re.S)
        check('id="taskTile"' not in pb and pbs == pa,
              "%s: no tile; the page is the old page plus the script that finds no tile and stops" % user)
_s, pmA = render(A, "manoj", "doctor")
stripped = re.sub(r"  <style>\n  \.tasktile.*?</a>\n", "", pm, count=1, flags=re.S)
stripped = re.sub(r"/\* S616: the owner's 'Tasks & messages' tile.*?\n\}\)\(\);\n", "", stripped, count=1, flags=re.S)
check(stripped == pmA, "the doctor's page is the old page plus the two blocks, nothing else changed")
j = js_ok(pm)
if j is None:
    print("  --   the page scripts: no node on this machine (checked in the rehearsal)")
else:
    check(j and js_ok(render(B, "shavez", "manager")[1]), "every inline script parses (the doctor's and a staff home)")
P0, P1 = open(pfrom, encoding="utf-8").read(), open(pto, encoding="utf-8").read()
check("<title>Staff lists &amp; tasks</title>" in P1 and "<h1>Staff lists &amp; tasks</h1>" in P1, "the panel is named 'Staff lists & tasks'")
check('/[?&]tab=tasks(&|$)/.test(location.search)?"tasks":recall("aaj.tab")' in P1, "the panel opens on Tasks for ?tab=tasks")
check(P1.replace("<title>Staff lists &amp; tasks</title>", "<title>Staff daily lists</title>")
        .replace("<h1>Staff lists &amp; tasks</h1>", "<h1>Staff daily lists</h1>")
        .replace('(/[?&]tab=tasks(&|$)/.test(location.search)?"tasks":recall("aaj.tab"))', 'recall("aaj.tab")') == P0,
      "the panel is otherwise byte-identical")
jp = js_ok(P1)
if jp is not None:
    check(jp, "the panel's script parses")
print("")
print(("WALK OK" if not failed else "WALK RED") + " S616: %d passed, %d failed" % (len(passed), len(failed)))
sys.exit(0 if not failed else 1)
