#!/usr/bin/env python3
"""walk_s298.py -- the exit page's words, driven through the real joiner_app over a COPY of finance.db.
Usage: walk_s298.py APP_DIR DB_COPY      (APP_DIR holds the joiner_app.py under test)"""
import importlib.util
import json
import sqlite3
import sys

app_dir, dbp = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("joiner_app_walk", app_dir + "/joiner_app.py")
ja = importlib.util.module_from_spec(spec)
sys.path.insert(0, app_dir)
spec.loader.exec_module(ja)
from flask import Flask  # noqa: E402

app = Flask("walk")


def db():
    c = sqlite3.connect(dbp)
    c.row_factory = sqlite3.Row
    return c


ja.init(app, db, lambda role: ("manoj", None), url_prefix="/finance/staff")
cl = app.test_client()
n = 0


def check(name, ok):
    global n
    n += 1
    if not ok:
        print("WALK FAIL %d %s" % (n, name))
        sys.exit(1)


r = cl.get("/finance/staff/api/record?ref=EXIT-2026-0001").get_json()
last = [s for s in r["steps"] if s["step"] == "STAFF_MASTER"][0]
check("exit record opens", r["ok"] and r["kind"] == "EXIT")
check("exit step 7 says the person no longer appears", "no longer appears" in last["label"])
check("exit step 7 says who does it", (last["why"] or "").startswith("Claude does this step"))
j = cl.get("/finance/staff/api/record?ref=JOIN-2026-0001").get_json()
jl = [s for s in j["steps"] if s["step"] == "STAFF_MASTER"][0]
check("join step 7 wording unchanged", jl["label"] == "staff master rebuilt and the person appears" and jl["why"] is None)
check("the other exit steps unchanged", [s["label"] for s in r["steps"]][:6] == [ja.STEP_LABEL[s] for s in ja.EXIT_STEPS[:6]])
p = cl.get("/finance/staff/api/pending").get_json()
print("  pending:", json.dumps([(x.get("ref"), x.get("waiting_label")) for x in (p.get("pending") or p.get("records") or [])]))
ok, why = ja.blocked_by("EXIT", {"DECIDED"}, "STAFF_MASTER")
check("refusal names exit wording", "no longer appears" not in why and "portal login disabled" in why)
print("WALK OK -- %d checks" % n)
