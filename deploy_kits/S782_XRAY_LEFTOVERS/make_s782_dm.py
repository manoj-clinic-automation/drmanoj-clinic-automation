#!/usr/bin/python3
# make_s782_dm.py -- kit S782: DUTY_MAP.json v21 (fdec576c) -> v22. Reception's X-ray line counts only pictures first seen in the
# last 7 days (the owner 05:15 IST 11-Nov: older ones go to him and Shavez). Usage: make_s782_dm.py <live DUTY_MAP.json> <output>
import hashlib, json, sys
raw = open(sys.argv[1], "rb").read()
assert hashlib.md5(raw).hexdigest().startswith("fdec576c"), "not DUTY_MAP v21 (fdec576c)"
t = raw.decode("utf-8")
for a, b in (("WHERE x.state = 'check' AND NOT EXISTS",
              "WHERE x.state = 'check' AND COALESCE(NULLIF(x.day, ''), substr(x.planned_at, 1, 10)) >= date('now','localtime','-7 days') AND NOT EXISTS"),
             ('"version": 21,', '"version": 22,'), ('"kit": "S763_F802_AGAIN",', '"kit": "S782_XRAY_LEFTOVERS",')):
    assert t.count(a) == 1, a
    t = t.replace(a, b)
json.loads(t)
open(sys.argv[2], "wb").write(t.encode("utf-8"))
print("written", sys.argv[2], hashlib.md5(t.encode("utf-8")).hexdigest()[:8])
