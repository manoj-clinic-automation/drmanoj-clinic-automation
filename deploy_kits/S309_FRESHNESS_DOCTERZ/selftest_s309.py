#!/usr/bin/env python3
"""selftest_s309.py -- S309 (F-517) offline proof of update_legs_s309.py, on a COPY of the live legs file.
Usage: python3 selftest_s309.py <dir holding update_legs_s309.py> <a copy of freshness_legs.json>"""
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import datetime

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def run(kit, *args):
    p = subprocess.run([sys.executable, "-B", os.path.join(kit, "update_legs_s309.py")] + list(args),
                       capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout + p.stderr


def main():
    kit, src = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    spec = importlib.util.spec_from_file_location("ul", os.path.join(kit, "update_legs_s309.py"))
    ul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ul)
    tmp = tempfile.mkdtemp(prefix="s309_")

    def point_at(text, database):
        """Point THIS leg's target at a test database, whatever it names today, so that no check here
        depends on the live data behind the live file."""
        a, b = ul.leg_span(text)
        return text[:a] + re.sub(r'("target"\s*:\s*)"[^"]*"', lambda m: m.group(1) + json.dumps(database), text[a:b]) + text[b:]

    fresh_db = os.path.join(tmp, "fresh.db")
    con = sqlite3.connect(fresh_db)
    con.execute("CREATE TABLE clinic_day_revenue (taken_at TEXT)")
    con.execute("INSERT INTO clinic_day_revenue VALUES (?)", (datetime.datetime.now().isoformat(" ")[:19],))
    con.commit(); con.close()
    f = os.path.join(tmp, "freshness_legs.json")
    shutil.copy(src, f)
    with open(f, encoding="utf-8") as fh:
        live_text = fh.read()
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(point_at(live_text, fresh_db))
    orig = open(f, encoding="utf-8").read()
    win, note = ul.current(orig)
    check("the copy still carries the 200 h window", win == 200)
    check("and the hand-run note", "run by hand" in (note or ""))
    rc, out = run(kit, "--check", "--file", f)
    check("--check is read-only and says PENDING", rc == 0 and "RESULT PENDING" in out
          and open(f, encoding="utf-8").read() == orig)
    rc, out = run(kit, "--apply", "--file", f)
    check("--apply says APPLIED", rc == 0 and "RESULT APPLIED" in out)
    new = open(f, encoding="utf-8").read()
    a, b = json.loads(orig), json.loads(new)
    check("the window is 50 h", ul.current(new)[0] == 50)
    check("the note names the timer and the measured quiet spells",
          "S291" in ul.current(new)[1] and "28.7" in ul.current(new)[1] and "run by hand" not in ul.current(new)[1])
    check("every other leg is untouched", len(a["legs"]) == len(b["legs"]) and all(
        x == y for x, y in zip(a["legs"], b["legs"]) if x["name"] != ul.LEG_NAME))
    check("the leg's other fields are untouched", all(
        y.get(k) == x.get(k) for x, y in zip(a["legs"], b["legs"]) if x["name"] == ul.LEG_NAME
        for k in ("name", "group", "kind", "target", "table", "column")))
    check("the file's own text changed on 4 lines only",
          sum(1 for x, y in zip(orig.split("\n"), new.split("\n")) if x != y) == 2
          and len(orig.split("\n")) == len(new.split("\n")))
    bak = f + ".bak_S309_" + ul.md5_text(orig)[:8]
    check("a backup holds the original bytes", os.path.isfile(bak) and open(bak, encoding="utf-8").read() == orig)
    rc, out = run(kit, "--apply", "--file", f)
    check("a second run changes nothing", rc == 0 and "RESULT ALREADY" in out
          and open(f, encoding="utf-8").read() == new)
    # refusals
    g = os.path.join(tmp, "no_leg.json")
    d = json.loads(orig)
    d["legs"] = [l for l in d["legs"] if l["name"] != ul.LEG_NAME]
    open(g, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
    rc, out = run(kit, "--apply", "--file", g)
    check("a file without the leg is refused", rc == 1 and "FAIL" in out)
    h = os.path.join(tmp, "odd.json")
    s_, e_ = ul.leg_span(orig)                       # only THIS leg's window, not another leg's
    open(h, "w", encoding="utf-8").write(
        orig[:s_] + orig[s_:e_].replace('"max_age_h": 200', '"max_age_h": 26') + orig[e_:])
    rc, out = run(kit, "--apply", "--file", h)
    check("a window that is not 200 h is refused", rc == 1 and "not in the leg exactly once" in out)
    two = orig[:s_] + orig[s_:e_].replace('"note": "watches', '"note": "second", "note": "watches') + orig[e_:]
    check("a leg with two notes is refused", ul.rewrite(two)[0] is None and "note is not in the leg exactly once" in ul.rewrite(two)[1])
    check("the defensive compare is in place",
          "another leg changed" in open(os.path.join(kit, "update_legs_s309.py"), encoding="utf-8").read())
    i = os.path.join(tmp, "broken.json")
    open(i, "w", encoding="utf-8").write(orig[:-3])
    rc, out = run(kit, "--apply", "--file", i)
    check("a file that is not JSON is refused", rc == 1)
    rc, out = run(kit, "--apply", "--file", os.path.join(tmp, "absent.json"))
    check("a missing file is refused", rc == 1 and "no legs file" in out)
    # the conf is what names the live file
    conf = os.path.join(tmp, "freshness.conf")
    open(conf, "w", encoding="utf-8").write("SOME_SECRET=notprinted\nLEGS_FILE=%s\n" % f)
    old_conf = ul.CONF
    ul.CONF = conf
    check("the path comes from freshness.conf when no --file is given", ul.resolve_file(None) == f)
    ul.CONF = old_conf
    # the data-age guard
    db = os.path.join(tmp, "f.db")
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE clinic_day_revenue (taken_at TEXT)")
    old_ts = (datetime.datetime.now() - datetime.timedelta(hours=120)).isoformat(" ")[:19]
    con.execute("INSERT INTO clinic_day_revenue VALUES (?)", (old_ts,))
    con.commit(); con.close()
    j = os.path.join(tmp, "red.json")
    open(j, "w", encoding="utf-8").write(point_at(orig, db))
    rc, out = run(kit, "--apply", "--file", j)
    check("stale data stops the change and says why", rc == 1 and "already" in out and "older than the 50 h window" in out
          and ul.current(open(j, encoding="utf-8").read())[0] == 200)
    rc, out = run(kit, "--apply", "--file", j, "--even-if-red")
    check("--even-if-red still allows it", rc == 0 and "RESULT APPLIED" in out)
    con = sqlite3.connect(db)
    con.execute("UPDATE clinic_day_revenue SET taken_at=?", (datetime.datetime.now().isoformat(" ")[:19],))
    con.commit(); con.close()
    k = os.path.join(tmp, "fresh.json")
    open(k, "w", encoding="utf-8").write(point_at(orig, db))
    rc, out = run(kit, "--check", "--file", k)
    check("fresh data reads its age", rc == 0 and "data age  : 0.0 h" in out)
    print("SELFTEST OK — %d checks (S309 Docterz freshness leg)" % N[0])


if __name__ == "__main__":
    main()
