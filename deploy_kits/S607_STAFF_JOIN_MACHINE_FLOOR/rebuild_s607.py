#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""rebuild_s607.py -- kit S607: rebuild staff_easy.py / staff_easy.html from the LIVE (S606) bytes by exact
counted edits and compare with the kit's copies. READ ONLY on the live files.
    python3 rebuild_s607.py LIVE_DIR KIT_DIR OUT_DIR      exit 0 = identical"""
import hashlib, os, sys
live, kit, out = sys.argv[1:4]
EDITS = {'staff_easy.py': [('def _machine_view(con):\n    """What the machine has sent that nobody owns yet, newest first."""\n    seen = _punches()\n    master = _master_codes()\n    reg = {}\n    for r in con.execute("SELECT code,person,retired_on FROM emp_code"):\n        reg[int(J._v(r, "code", 0))] = (J._v(r, "person", 1), J._v(r, "retired_on", 2))\n    floor = (dt.date.today() - dt.timedelta(days=60)).isoformat()', 'def _machine_view(con, since=None):\n    """What the machine has sent that nobody owns yet, newest first.\n\n    S607: only fingers pressed from the day before the joining was opened. The\n    clinic\'s machine already carried test presses from its set-up day (07-Oct:\n    number 2, and the retired 100) -- offered on a new joiner\'s page they invite\n    a wrong "Yes"; number 2 is likely the owner\'s own administrator finger."""\n    seen = _punches()\n    master = _master_codes()\n    reg = {}\n    for r in con.execute("SELECT code,person,retired_on FROM emp_code"):\n        reg[int(J._v(r, "code", 0))] = (J._v(r, "person", 1), J._v(r, "retired_on", 2))\n    floor = (dt.date.today() - dt.timedelta(days=60)).isoformat()\n    if since:\n        try:\n            floor = max(floor, (dt.date.fromisoformat(str(since)[:10]) - dt.timedelta(days=1)).isoformat())\n        except ValueError:\n            pass'), ('        if code not in reg and code not in master:\n            new.append', "        if code not in reg and code not in master:\n            if first[:10] < floor:\n                continue                      # an old unknown finger, not this joining's\n            new.append"), ('    _u, err = _owner()\n    if err:\n        return err\n    fin = _fin()\n    new, reused, nxt = _machine_view(fin)\n    return jsonify(ok=True, new=new, reused=reused, next_code=nxt, now=_now())', '    _u, err = _owner()\n    if err:\n        return err\n    fin = _fin()\n    since = None\n    r = _jrow(fin, (request.args.get("ref") or "").strip())\n    if r:\n        since = J._v(r, "opened_on", 10)\n    new, reused, nxt = _machine_view(fin, since)\n    return jsonify(ok=True, new=new, reused=reused, next_code=nxt, now=_now())'), ('        new, _reused, _n = _machine_view(fin)', '        new, _reused, _n = _machine_view(fin, J._v(r, "opened_on", 10))'), ('KIT = "S606"', 'KIT = "S607"')], 'staff_easy.html': [('try{ j=await get(API+"/machine"); }', 'try{ j=await get(API+"/machine?ref="+encodeURIComponent(CUR.ref)); }')]}
bad = 0
os.makedirs(out, exist_ok=True)
for name, edits in EDITS.items():
    s = open(os.path.join(live, name), encoding="utf-8").read()
    for old, new in edits:
        n = s.count(old)
        if n != 1:
            print("  REFUSED %s: an anchor occurs %d times (expected 1)" % (name, n)); bad += 1; break
        s = s.replace(old, new)
    with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(os.path.join(out, name), "rb").read()).hexdigest()
    b = hashlib.md5(open(os.path.join(kit, name), "rb").read()).hexdigest()
    print("  %-16s rebuilt %s  kit %s  %s" % (name, a[:8], b[:8], "same" if a == b else "DIFFERENT"))
    bad += (a != b)
sys.exit(1 if bad else 0)
