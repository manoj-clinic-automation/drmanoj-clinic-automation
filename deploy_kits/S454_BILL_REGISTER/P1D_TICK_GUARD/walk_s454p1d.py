#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s454p1d.py -- kit S454_BILL_REGISTER, part 1D: the cron's own command, `order_rules.py tick`, run AS A SCRIPT on a scratch copy of
finance.db (backup API), with the push stubbed (no push leaves the walk):

  NEW  a scratch copy of the finance folder with the built order_rules.py: exit 0, one line of JSON with the S454 pass in it
  OLD  the same with the live order_rules.py: NameError '_s454_pass' -- the negative control (the fault order_rules.log shows)
  Both pythons compile the built file; the module imported in-process exposes the same names as before (nothing else changed).

    walk_s454p1d.py --fin-new DIR --fin-old DIR --db FINANCE_DB --work DIR
"""
import argparse
import os
import sqlite3
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    for k in ("--fin-new", "--fin-old", "--db", "--work"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    assert a.work.startswith("/tmp/"), "refusing a non-scratch path"
    os.makedirs(a.work, exist_ok=True)
    ok = [0, 0]

    def check(label, cond, got=None):
        ok[0] += 1
        ok[1] += 1 if cond else 0
        print(("  ok   " if cond else "  FAIL ") + label + ("" if got is None else "   [%s]" % (str(got)[:500],)))
    res = {}
    for name, fin in (("new", a.fin_new), ("old", a.fin_old)):
        db = os.path.join(a.work, "p1d_%s.db" % name)
        s = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
        d = sqlite3.connect(db)
        s.backup(d)
        d.close()
        s.close()
        env = dict(os.environ, FINANCE_DB=db, ORDER_PUSH_STUB=os.path.join(a.work, "push_%s.jsonl" % name), PORDERS_SOURCE="tables")
        for k in ("ORDER_TICK", "ORDER_TODAY"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.join(fin, "order_rules.py"), "tick"], cwd=fin, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, timeout=600)
        res[name] = dict(code=p.returncode, out=p.stdout.strip()[-400:], err=p.stderr.strip()[-300:])
        names = subprocess.run([sys.executable, "-B", "-c", "import sys; sys.path.insert(0, %r); import order_rules as o; print(sorted(n for n in dir(o) if not n.startswith('__')))" % fin],
                               cwd=fin, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
        res[name]["names"] = names.stdout.strip()
    N, O = res["new"], res["old"]
    print("-- the cron's command, order_rules.py tick, run as a script on scratch copies")
    check("NEW: exit 0, one line of JSON with the order sheet's pass ('s454') in it", N["code"] == 0 and '"s454"' in N["out"], N)
    check("NEGATIVE: the live file fails exactly as order_rules.log shows (NameError: _s454_pass)", O["code"] != 0 and "_s454_pass" in O["err"] and "NameError" in O["err"], O["err"])
    check("imported in-process, the module exposes exactly the same names as the live one", N["names"] == O["names"] and len(N["names"]) > 20)
    print("WALK_S454P1D %s -- %d of %d passed" % ("GREEN" if ok[0] == ok[1] else "RED", ok[1], ok[0]))
    return 0 if ok[0] == ok[1] else 1


if __name__ == "__main__":
    sys.exit(main())
