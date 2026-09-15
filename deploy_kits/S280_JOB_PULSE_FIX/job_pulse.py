#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
job_pulse.py -- S279. Can each of our scheduled jobs prove it ran?

THE FAULT THIS EXISTS FOR
    A job that is quiet looks exactly like a job that is passing. At S259 four of
    the six open faults were that one shape: a check built correctly, wired
    correctly, and then never switched on or never looked at. Of 38 clinic jobs
    only 8 leave a run record anyone can read back.

WHAT IT DOES
    Reads root's crontab and the clinic systemd timers, and for each job asks one
    question: WHEN WAS IT LAST ALIVE?

    * cron jobs   -- 45 of the 46 clinic cron lines already name their own log
                     file with `>> /path/to.log`. The log's modification time is
                     the trace. Nothing is inferred: the path is read out of the
                     crontab line itself.
    * timers      -- systemd knows its own last trigger; it is asked directly.

    Lines that write to the SAME log are one job: att_mailer morning and evening
    share a log and share a pulse.

WHAT IT IS HONEST ABOUT
    A log's timestamp proves the job WROTE SOMETHING. It does not prove the job
    succeeded, and a job that runs silently on a good day will look late. That
    limit is printed on the face of the report rather than left for someone to
    discover. This measures LIVENESS, which nothing measured before; it does not
    replace a job's own verdict.

WHAT IT TOUCHES
    Nothing. It reads the crontab, stats log files, and asks systemd. It writes
    only its own two outputs. No existing job is modified, no database is opened.

    python3 job_pulse.py                 write the report and the json
    python3 job_pulse.py --print         also print the table
    python3 job_pulse.py --selftest      no files, no crontab, no network
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

OUT_JSON = os.environ.get("JOB_PULSE_JSON", "/root/finance/job_pulse.json")
OUT_TXT = os.environ.get("JOB_PULSE_TXT", "/root/finance/JOB_PULSE_LATEST.txt")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

# The host's own housekeeping is not ours to watch.
NOT_OURS = ("CyberCP", "cleansessions", "acme.sh", "public_html")

TIMERS = ("clinic-certwatch", "clinic-watchdog",
          "clinic-health-report", "clinic-followup-push")

GRACE_MIN = 90          # allowed on top of twice the expected gap

# v1.1. Seven jobs keep a proper run record in the clinic database. Where one
# exists it BEATS the log file, because a log only moves when the job prints
# something: marg_ingest runs every 5 minutes and prints nothing on a quiet
# pass, so its log read 2.3 days old on the very first run while mi_run showed
# it had run at 01:00 that morning. The log is the fallback, not the authority.
FINANCE_DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
DB_TRACE = {
    "/root/marg_ingest/logs/ingest.log":   ("mi_run", "finished"),
    "/root/marg_ingest/logs/shadow.log":   ("sh_run", "finished"),
    "/root/finance/export_watch.log":      ("export_watch", "checked_at"),
    "/root/finance/spine_cadence.log":     ("marg_spine_run", "finished_at"),
    "/root/finance/sale_attribution.log":  ("sale_attrib_run", "finished_at"),
    "/root/finance/bank_match.log":        ("upi_match_day", "run_at"),
    "/root/finance/logs/docterz_ingest.log": ("clinic_day_revenue", "taken_at"),
}


def db_last(table, col, db=None):
    """The newest timestamp this job wrote, or None. Read-only, never raises."""
    import sqlite3
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (db or FINANCE_DB), uri=True, timeout=10)
        try:
            v = con.execute('SELECT MAX("%s") FROM "%s"' % (col, table)).fetchone()[0]
        finally:
            con.close()
    except Exception:
        return None
    if not v:
        return None
    txt = str(v).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            d = dt.datetime.strptime(txt[:26] if "+" in txt else txt[:19], fmt)
            return (d if d.tzinfo else d.replace(tzinfo=IST)).timestamp()
        except ValueError:
            continue
    return None
HORIZON_DAYS = 16       # window used to measure a schedule's widest gap.
                        # 8 was too short: a WEEKLY job showed one run in it
                        # and its gap read as unknown (selftest, S279).


# --------------------------------------------------------------- cron parsing
def _field(spec, lo, hi):
    """The set of values a single cron field matches. Returns None if unreadable."""
    out = set()
    for part in str(spec).split(","):
        step = 1
        if "/" in part:
            part, _, s = part.partition("/")
            if not s.isdigit() or int(s) == 0:
                return None
            step = int(s)
        if part in ("*", ""):
            a, b = lo, hi
        elif "-" in part:
            a, _, b = part.partition("-")
            if not (a.isdigit() and b.isdigit()):
                return None
            a, b = int(a), int(b)
        elif part.isdigit():
            a = b = int(part)
        else:
            return None
        if a > b or a < lo or b > hi:
            return None
        out.update(range(a, b + 1, step))
    return out or None


def widest_gap_minutes(fields, now=None):
    """The longest stretch, in minutes, that this schedule may legitimately stay
    silent -- measured by walking a real week, not guessed from the shape."""
    mi, ho, dom, mon, dow = fields
    S = [_field(mi, 0, 59), _field(ho, 0, 23), _field(dom, 1, 31),
         _field(mon, 1, 12), _field(dow, 0, 7)]
    if any(s is None for s in S):
        return None
    mset, hset, domset, monset, dowset = S
    dowset = {0 if d == 7 else d for d in dowset}
    now = now or dt.datetime.now(IST)
    start = (now - dt.timedelta(days=HORIZON_DAYS)).replace(second=0, microsecond=0)
    hits, t = [], start
    end = now
    dom_star = str(dom).strip() == "*"
    dow_star = str(dow).strip() == "*"
    while t <= end:
        if t.month in monset and t.hour in hset and t.minute in mset:
            d_ok = t.day in domset
            w_ok = ((t.weekday() + 1) % 7) in dowset
            # cron's rule: when both day fields are restricted, EITHER matches
            if dom_star and dow_star:
                ok = True
            elif dom_star:
                ok = w_ok
            elif dow_star:
                ok = d_ok
            else:
                ok = d_ok or w_ok
            if ok:
                hits.append(t)
        t += dt.timedelta(minutes=1)
    if len(hits) < 2:
        return None
    return max(int((b - a).total_seconds() // 60) for a, b in zip(hits, hits[1:]))


LOG_RE = re.compile(r'>>?\s*(/\S+\.log)')
SCRIPT_RE = re.compile(r'([A-Za-z0-9_\-]+\.(?:py|sh))')


def read_crontab(text=None):
    """[(schedule_fields, command, logpath|None, label)] for the clinic's own lines."""
    if text is None:
        try:
            text = subprocess.check_output(["crontab", "-l"], text=True, timeout=30)
        except Exception as e:
            return [], "crontab could not be read: %s" % e
    jobs = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not re.match(r'^[0-9*]', line):
            continue
        if any(k in line for k in NOT_OURS):
            continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        fields, cmd = parts[:5], parts[5]
        m = LOG_RE.search(cmd)
        log = m.group(1) if m else None
        s = SCRIPT_RE.search(re.sub(r'>>?.*$', '', cmd))
        label = s.group(1) if s else cmd.split()[0].split("/")[-1]
        jobs.append((fields, cmd, log, label))
    return jobs, None


# ------------------------------------------------------------------- verdicts
def verdict(age_min, allowed_min):
    if age_min is None:
        return "NO TRACE"
    if age_min < 0:
        # v1.1: the first run printed "-329 min" for two timers. An age can
        # never be negative; a future timestamp means the clock or the zone was
        # misread, and saying so is better than printing a number that cannot
        # be true.
        return "AHEAD?"
    if allowed_min is None:
        return "SEEN"
    if age_min <= allowed_min:
        return "ALIVE"
    if age_min <= allowed_min * 3:
        return "LATE"
    return "SILENT"


def human_age(mins):
    if mins is None:
        return "-"
    if mins < 90:
        return "%d min" % mins
    if mins < 60 * 48:
        return "%.1f h" % (mins / 60.0)
    return "%.1f days" % (mins / 1440.0)


def collect(now=None, crontab_text=None, stat=os.path.getmtime, ask_systemd=None,
            db_lookup=db_last):
    now = now or dt.datetime.now(IST)
    jobs, err = read_crontab(crontab_text)
    by_log = {}
    no_log = []
    for fields, cmd, log, label in jobs:
        gap = widest_gap_minutes(fields, now)
        if log is None:
            no_log.append({"kind": "cron", "job": label, "command": cmd[:160],
                           "trace": None, "age_min": None, "allowed_min": gap,
                           "last_seen": "-", "lines": 1, "verdict": "NO TRACE"})
            continue
        e = by_log.setdefault(log, {"kind": "cron", "job": label, "trace": log,
                                    "lines": 0, "allowed_min": gap})
        e["lines"] += 1
        if label not in e["job"]:
            e["job"] = e["job"] + " + " + label
        if gap is not None and (e["allowed_min"] is None or gap < e["allowed_min"]):
            e["allowed_min"] = gap

    rows = []
    for log, e in sorted(by_log.items()):
        try:
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
        rows.append(e)
    rows.extend(no_log)

    # Two different files can share a name -- rxguard/backup.sh and
    # gutlog/backup.sh are separate jobs with one label between them. Grouping
    # is by log path so they are already separate; only the NAME would confuse
    # a reader, so an ambiguous one is qualified by the folder its log sits in.
    seen = {}
    for r in rows:
        seen[r["job"]] = seen.get(r["job"], 0) + 1
    for r in rows:
        if seen.get(r["job"], 0) > 1 and r.get("trace"):
            folder = os.path.basename(os.path.dirname(r["trace"].rstrip("/")))
            if folder:
                r["job"] = "%s/%s" % (folder, r["job"])

    ask = ask_systemd or _systemd
    for unit in TIMERS:
        rows.append(ask(unit, now))
    return rows, err


def _systemd(unit, now):
    out = {"kind": "timer", "job": unit, "trace": "systemd", "lines": 1,
           "age_min": None, "allowed_min": None, "last_seen": "-",
           "verdict": "NO TRACE", "enabled": "?"}
    try:
        out["enabled"] = subprocess.run(
            ["systemctl", "is-enabled", unit + ".timer"],
            capture_output=True, text=True, timeout=20).stdout.strip() or "?"
    except Exception:
        pass
    # v1.1 -- THE FAULT THE FIRST RUN FOUND. v1.0 parsed systemd's timestamp and
    # forced UTC on it, then converted to IST, so two timers reported a run in
    # the future and an age of -329 minutes. systemd prints in the BOX's zone.
    # Ask for a unix epoch, which carries no zone to get wrong; only if that is
    # not supported fall back to a naive parse read as LOCAL time, never UTC.
    when = None
    try:
        r = subprocess.run(["systemctl", "show", unit + ".service", "--value",
                            "--timestamp=unix", "-p", "ExecMainStartTimestamp"],
                           capture_output=True, text=True, timeout=20)
        v = (r.stdout or "").strip()
        if v.startswith("@") and v[1:].isdigit():
            when = dt.datetime.fromtimestamp(int(v[1:]), IST)
    except Exception:
        pass
    try:
        if when is None:
            r = subprocess.run(["systemctl", "show", unit + ".service", "--value",
                                "-p", "ExecMainStartTimestamp"],
                               capture_output=True, text=True, timeout=20)
            val = (r.stdout or "").strip()
            # drop the weekday and any trailing zone abbreviation
            m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", val)
            if m:
                naive = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                when = naive.astimezone() if naive.tzinfo else \
                    naive.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
                when = when.astimezone(IST)
        if when is not None:
            out["age_min"] = int((now - when).total_seconds() // 60)
            out["last_seen"] = when.strftime("%d-%m-%Y %H:%M")
            out["allowed_min"] = 60 * 26 * 2 + GRACE_MIN
            out["verdict"] = verdict(out["age_min"], out["allowed_min"])
            out["via"] = "systemd"
    except Exception:
        pass
    if out["enabled"] == "disabled":
        out["verdict"] = "OFF"
    return out


# --------------------------------------------------------------------- output
HEADER = """JOB PULSE -- can each of our scheduled jobs prove it ran?
when   : %s IST
reads  : root's crontab, the log each line names, and systemd for the timers.
writes : only this file and job_pulse.json. No job is touched, no database opened.

WHAT A GREEN LINE MEANS, EXACTLY
  A log's timestamp proves the job WROTE SOMETHING at that moment. It does not
  prove the job succeeded, and a job that runs silently on a quiet day will read
  LATE without being broken. This measures LIVENESS -- which nothing measured
  before -- and it never replaces a job's own verdict.
"""


def render(rows, err, now):
    order = {"SILENT": 0, "OFF": 1, "AHEAD?": 2, "NO TRACE": 3, "LATE": 4,
             "SEEN": 5, "ALIVE": 6}
    rows = sorted(rows, key=lambda r: (order.get(r["verdict"], 9), r["job"]))
    L = [HEADER % now.strftime("%d-%m-%Y %H:%M")]
    if err:
        L.append("!! %s" % err)
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    L.append("  " + " | ".join("%s %d" % (k, counts[k]) for k in
                               sorted(counts, key=lambda k: order.get(k, 9))))
    L.append("")
    L.append("%-9s %-32s %-17s %-10s %s" % ("verdict", "job", "last seen",
                                            "age", "read from"))
    L.append("-" * 96)
    for r in rows:
        L.append("%-9s %-32s %-17s %-10s %s" % (
            r["verdict"], r["job"][:32], r["last_seen"],
            human_age(r["age_min"]), r.get("via") or
            ("(names no log)" if not r.get("trace") else "log")))
    L.append("")
    bad = [r for r in rows if r["verdict"] in ("SILENT", "OFF", "NO TRACE", "AHEAD?")]
    L.append("VERDICT : %s" % ("OK -- every job has written something within its "
                               "own schedule" if not bad else
                               "%d job(s) cannot show they are alive" % len(bad)))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", action="store_true")
    ap.add_argument("--json", default=OUT_JSON)
    ap.add_argument("--txt", default=OUT_TXT)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    now = dt.datetime.now(IST)
    rows, err = collect(now)
    report = render(rows, err, now)
    for path, blob in ((a.txt, report),
                       (a.json, json.dumps({"when": now.isoformat(),
                                            "jobs": rows, "error": err},
                                           indent=1) + "\n")):
        try:
            tmp = path + ".new"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(blob)
            os.replace(tmp, path)
        except Exception as e:
            print("could not write %s: %s" % (path, e))
            return 2
    if a.show:
        print(report)
    else:
        bad = [r for r in rows if r["verdict"] in ("SILENT", "OFF", "NO TRACE", "AHEAD?")]
        print("job_pulse: %d jobs, %d cannot show they are alive -> %s"
              % (len(rows), len(bad), a.txt))
    return 0


# ----------------------------------------------------------------- self test
def selftest():
    ok = True

    def check(name, got, want):
        nonlocal ok
        if got != want:
            ok = False
            print("FAIL %-44s got %r want %r" % (name, got, want))
        else:
            print("ok   %s" % name)

    check("every minute", _field("*", 0, 59) == set(range(60)), True)
    check("*/30 minutes", sorted(_field("*/30", 0, 59)), [0, 30])
    check("hour range 9-19", sorted(_field("9-19", 0, 23)), list(range(9, 20)))
    check("bad field refused", _field("banana", 0, 59), None)

    now = dt.datetime(2026, 9, 15, 12, 0, tzinfo=IST)
    check("every 5 min -> 5", widest_gap_minutes(["*/5", "*", "*", "*", "*"], now), 5)
    check("daily 01:05 -> 1440", widest_gap_minutes(["5", "1", "*", "*", "*"], now), 1440)
    # 09:00-19:00 every 30 min: the last fire is 19:30 and the next is 09:00,
    # so the overnight silence is 13.5 h, not 14 h. The first version of this
    # test asserted 840 and the code was right.
    check("daytime only -> overnight gap",
          widest_gap_minutes(["*/30", "9-19", "*", "*", "*"], now), 810)
    check("weekly -> 10080", widest_gap_minutes(["20", "2", "*", "*", "0"], now), 10080)

    cron = "\n".join([
        "5 1 * * * /root/finance/finance_backup.sh >> /root/finance/backup.log 2>&1",
        "0 * * * * /usr/local/CyberCP/bin/python /usr/local/CyberCP/x.py",
        "30 11 * * * cd /root && /root/att_mailer.py morning >> /root/att_mailer.log 2>&1",
        "0 21 * * * cd /root && /root/att_mailer.py evening >> /root/att_mailer.log 2>&1",
        "30 2 * * * tar -czf /root/backups/a.tgz -C /root assetapp 2>/dev/null",
    ])
    jobs, err = read_crontab(cron)
    check("host lines dropped", len(jobs), 4)
    check("no crontab error", err, None)

    ages = {"/root/finance/backup.log": now.timestamp() - 3 * 3600,
            "/root/att_mailer.log": now.timestamp() - 40 * 86400}
    rows, _ = collect(now, cron, lambda p: ages[p], lambda u, n: {
        "kind": "timer", "job": u, "trace": "systemd", "lines": 1, "age_min": 10,
        "allowed_min": 3210, "last_seen": "-", "verdict": "ALIVE", "enabled": "enabled"})
    by = {r["job"]: r for r in rows}
    check("two lines, one log, one job", by.get("att_mailer.py") is not None, True)
    check("fresh backup log is ALIVE", by["finance_backup.sh"]["verdict"], "ALIVE")
    check("40-day-old log is SILENT", by["att_mailer.py"]["verdict"], "SILENT")
    check("job naming no log has NO TRACE",
          [r["verdict"] for r in rows if r["trace"] is None], ["NO TRACE"])
    check("timers included", sum(1 for r in rows if r["kind"] == "timer"), 4)

    # v1.1 -- the two faults the first live run exposed
    check("a negative age is never reported as fine", verdict(-329, 3210), "AHEAD?")
    check("a negative age is counted as a problem",
          "AHEAD?" in ("SILENT", "OFF", "NO TRACE", "AHEAD?"), True)

    cron2 = ("*/5 * * * * /root/marg_ingest/marg_ingest.py "
             ">> /root/marg_ingest/logs/ingest.log 2>&1")
    quiet_log = now.timestamp() - 2.3 * 86400      # what the log said on day one
    real_run = now.timestamp() - 40 * 60           # what mi_run said
    rows2, _ = collect(now, cron2, lambda p: quiet_log,
                       lambda u, n2: {"kind": "timer", "job": u, "trace": "systemd",
                                      "lines": 1, "age_min": 1, "allowed_min": 99,
                                      "last_seen": "-", "verdict": "ALIVE"},
                       lambda t, c: real_run)
    mi = [r for r in rows2 if r.get("trace", "").endswith("ingest.log")][0]
    check("the run table beats a quiet log", mi["verdict"], "ALIVE")
    check("and the report says which was read", mi["via"], "mi_run table")
    rows3, _ = collect(now, cron2, lambda p: quiet_log,
                       lambda u, n2: {"kind": "timer", "job": u, "trace": "systemd",
                                      "lines": 1, "age_min": 1, "allowed_min": 99,
                                      "last_seen": "-", "verdict": "ALIVE"},
                       lambda t, c: None)
    mi3 = [r for r in rows3 if r.get("trace", "").endswith("ingest.log")][0]
    check("with no run record it falls back to the log", mi3["via"], "log")

    txt = render(rows, None, now)
    check("report names its own limit on its face",
          "does not" in txt and "succeeded" in txt, True)
    check("worst first", txt.index("SILENT") < txt.index("ALIVE"), True)

    print("\nSELFTEST %s" % ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
