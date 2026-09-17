#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_s283.py -- job_pulse.py v1.1 -> v1.2 (F-498, second half).
Exact anchors, each must occur exactly once; refuses on any other starting md5."""
import hashlib, sys

FROM = "917713f5269bb6af46ea355fc212ad2c"

EDITS = [
# 1 -- the docstring says what v1.2 is
('''WHAT IT TOUCHES
    Nothing.''',
'''THREE DIFFERENT FACTS ABOUT A LOG (v1.2, F-498 second half)
    A log that is OLD, a log that is EMPTY and a log that is NOT THERE are three
    different facts, and v1.1 read the first two alike. An old log means the job
    spoke once and has since gone quiet. An empty log means the shell opened it
    -- so cron did fire the line -- but the job has never printed one word, and
    its timestamp is only when the file was made. A missing log means the line
    has never fired at all, since `>>` creates the file on the first run. Each
    now has its own verdict: SILENT / LATE, EMPTY, NEVER RAN. A run table, where
    a job keeps one, still beats all three.

WHAT IT TOUCHES
    Nothing.'''),

# 2 -- one list of problem verdicts, used everywhere
('''GRACE_MIN = 90          # allowed on top of twice the expected gap
''',
'''GRACE_MIN = 90          # allowed on top of twice the expected gap

# v1.2 -- one list, read by the report, the summary line and the selftest, so a
# new verdict can never be counted in one place and forgotten in another.
PROBLEM = ("SILENT", "NEVER RAN", "EMPTY", "OFF", "AHEAD?", "NO TRACE")
'''),

# 3 -- collect() learns a file's size
('''def collect(now=None, crontab_text=None, stat=os.path.getmtime, ask_systemd=None,
            db_lookup=db_last):''',
'''def collect(now=None, crontab_text=None, stat=os.path.getmtime, ask_systemd=None,
            db_lookup=db_last, size=os.path.getsize):'''),

# 4 -- the three facts
('''        try:
            mt = stat(log)
        except Exception:
            mt = None
        e["via"] = "log"
        if log in DB_TRACE and db_lookup is not None:
            dmt = db_lookup(*DB_TRACE[log])
            if dmt is not None and (mt is None or dmt > mt):
                mt, e["via"] = dmt, "%s table" % DB_TRACE[log][0]
        age = None if mt is None else int((now.timestamp() - mt) // 60)
        allowed = None if e["allowed_min"] is None else e["allowed_min"] * 2 + GRACE_MIN
        e["age_min"] = age
        e["last_seen"] = ("-" if age is None else
                          dt.datetime.fromtimestamp(now.timestamp() - age * 60, IST)
                          .strftime("%d-%m-%Y %H:%M"))
        e["allowed_min"] = allowed
        e["verdict"] = "NO TRACE" if age is None else verdict(age, allowed)
        rows.append(e)''',
'''        # v1.2 -- which of three facts is this log? written / empty / absent.
        # "unknown" (a stat that failed for any other reason) keeps v1.1's reading.
        state = "written"
        try:
            mt = stat(log)
        except FileNotFoundError:
            mt, state = None, "absent"
        except Exception:
            mt, state = None, "unknown"
        if state == "written":
            try:
                if size(log) == 0:
                    state = "empty"
            except Exception:
                pass
        e["via"] = "log"
        e["log_state"] = state
        from_table = False
        if log in DB_TRACE and db_lookup is not None:
            dmt = db_lookup(*DB_TRACE[log])
            # a run table beats a quiet log, and ALWAYS beats an empty or absent
            # one: an empty file's time is only when it was made.
            if dmt is not None and (mt is None or state != "written" or dmt > mt):
                mt, e["via"], from_table = dmt, "%s table" % DB_TRACE[log][0], True
        age = None if mt is None else int((now.timestamp() - mt) // 60)
        allowed = None if e["allowed_min"] is None else e["allowed_min"] * 2 + GRACE_MIN
        e["age_min"] = age
        e["last_seen"] = ("-" if age is None else
                          dt.datetime.fromtimestamp(now.timestamp() - age * 60, IST)
                          .strftime("%d-%m-%Y %H:%M"))
        e["allowed_min"] = allowed
        if from_table:
            e["verdict"] = verdict(age, allowed)
        elif state == "absent":
            e["verdict"], e["via"] = "NEVER RAN", "log is not there"
        elif state == "empty":
            e["verdict"], e["via"] = "EMPTY", "log empty since made"
        else:
            e["verdict"] = "NO TRACE" if age is None else verdict(age, allowed)
        rows.append(e)'''),

# 5 -- the header says what the three words mean
('''  LATE without being broken. This measures LIVENESS -- which nothing measured
  before -- and it never replaces a job's own verdict.
"""''',
'''  LATE without being broken. This measures LIVENESS -- which nothing measured
  before -- and it never replaces a job's own verdict.

THREE WORDS FOR A LOG THAT DOES NOT MOVE -- they are different facts
  SILENT / LATE  the job printed before and has since stopped.
  EMPTY          cron opened the log, so the line fired, but the job has never
                 printed a word. "last seen" is only when the file was made.
                 A job that prints only when it has work reads this way too.
  NEVER RAN      the log the line names does not exist: the line has not fired.
"""'''),

# 6 -- report order and the problem count use the one list
('''    order = {"SILENT": 0, "OFF": 1, "AHEAD?": 2, "NO TRACE": 3, "LATE": 4,
             "SEEN": 5, "ALIVE": 6}''',
'''    order = {"SILENT": 0, "NEVER RAN": 1, "EMPTY": 2, "OFF": 3, "AHEAD?": 4,
             "NO TRACE": 5, "LATE": 6, "SEEN": 7, "ALIVE": 8}'''),
('''    bad = [r for r in rows if r["verdict"] in ("SILENT", "OFF", "NO TRACE", "AHEAD?")]
    L.append("VERDICT''',
'''    bad = [r for r in rows if r["verdict"] in PROBLEM]
    L.append("VERDICT'''),
('''        bad = [r for r in rows if r["verdict"] in ("SILENT", "OFF", "NO TRACE", "AHEAD?")]
        print("job_pulse''',
'''        bad = [r for r in rows if r["verdict"] in PROBLEM]
        print("job_pulse'''),
('''    check("a negative age is counted as a problem",
          "AHEAD?" in ("SILENT", "OFF", "NO TRACE", "AHEAD?"), True)''',
'''    check("a negative age is counted as a problem", "AHEAD?" in PROBLEM, True)'''),

# 7 -- selftests for the second half
('''    txt = render(rows, None, now)
    check("report names its own limit on its face",''',
'''    # v1.2 -- F-498 second half: old, empty and absent are three facts
    timer = lambda u, n2: {"kind": "timer", "job": u, "trace": "systemd",
                           "lines": 1, "age_min": 1, "allowed_min": 99,
                           "last_seen": "-", "verdict": "ALIVE"}
    cron4 = "\\n".join([
        "5 1 * * * /root/a/old.py >> /root/a/old.log 2>&1",
        "5 1 * * * /root/a/quiet.py >> /root/a/quiet.log 2>&1",
        "5 1 * * * /root/a/gone.py >> /root/a/gone.log 2>&1",
        "*/5 * * * * /root/marg_ingest/marg_ingest.py >> /root/marg_ingest/logs/ingest.log 2>&1",
    ])
    made = now.timestamp() - 9 * 86400

    def st4(p):
        if p.endswith("gone.log"):
            raise FileNotFoundError(p)
        return made

    sz4 = lambda p: 0 if (p.endswith("quiet.log") or p.endswith("ingest.log")) else 812
    rows4, _ = collect(now, cron4, st4, timer, lambda t, c: real_run, sz4)
    b4 = {r["job"]: r for r in rows4}
    check("an old log that has words is still SILENT", b4["old.py"]["verdict"], "SILENT")
    check("an EMPTY log is its own fact", b4["quiet.py"]["verdict"], "EMPTY")
    check("and says so where it was read", b4["quiet.py"]["via"], "log empty since made")
    check("a log that is not there reads NEVER RAN", b4["gone.py"]["verdict"], "NEVER RAN")
    check("an absent log is not confused with naming none",
          b4["gone.py"]["trace"], "/root/a/gone.log")
    check("a run table beats an empty log", b4["marg_ingest.py"]["verdict"], "ALIVE")
    check("EMPTY and NEVER RAN are counted as problems",
          "EMPTY" in PROBLEM and "NEVER RAN" in PROBLEM, True)
    check("a stat that fails oddly keeps the v1.1 reading",
          collect(now, cron4.splitlines()[0], lambda p: (_ for _ in ()).throw(
              PermissionError(p)), timer, None, sz4)[0][0]["verdict"], "NO TRACE")
    txt4 = render(rows4, None, now)
    check("the report explains the three words",
          "THREE WORDS FOR A LOG" in txt4 and "the line has not fired" in txt4, True)
    table4 = txt4[txt4.index("-" * 96):]
    check("worst first: silent, never ran, empty, then alive",
          table4.index("\\nSILENT ") < table4.index("\\nNEVER RAN ")
          < table4.index("\\nEMPTY ") < table4.index("\\nALIVE "), True)
    check("the summary counts the empty and the absent",
          "3 job(s) cannot show they are alive" in txt4, True)

    txt = render(rows, None, now)
    check("report names its own limit on its face",'''),
# 8 -- v1.1's own ordering test read the explanation box once the box named SILENT
('    check("worst first", txt.index("SILENT") < txt.index("ALIVE"), True)',
 '    table = txt[txt.index("-" * 96):]\n    check("worst first", table.index("\\nSILENT ") < table.index("\\nALIVE "), True)'),
]


def main():
    if len(sys.argv) != 3:
        print("usage: patch_s283.py IN OUT"); return 2
    src = open(sys.argv[1], "rb").read()
    got = hashlib.md5(src).hexdigest()
    if got != FROM:
        print("REFUSED: input is %s, expected %s" % (got, FROM)); return 1
    t = src.decode("utf-8")
    for i, (a, b) in enumerate(EDITS, 1):
        n = t.count(a)
        if n != 1:
            print("REFUSED: anchor %d found %d times" % (i, n)); return 1
        t = t.replace(a, b)
    open(sys.argv[2], "wb").write(t.encode("utf-8"))
    print("patched: %d anchors, %s -> %s" % (len(EDITS), FROM,
          hashlib.md5(t.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
