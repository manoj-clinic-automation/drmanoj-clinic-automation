#!/usr/bin/python3
"""
manojz_agent.py — the missing half of the pipeline's self-report.

WHY THIS EXISTS — the 27-Aug-2026 event, diagnosed
    The pull ran every ten minutes, then did not run between 11:40 and 14:51
    IST. Nothing was lost: the medical PC's watcher held every capture and the
    14:51 run swept all 95 of them in at once. But for three hours nobody knew,
    and the only reason it surfaced at all is that someone went looking for a
    file.

    MEASURED ACROSS THE WHOLE PULL LOG (107 runs):
        ok 107 · failed 0 · gaps over 15 min: 3 (17 min, 24 min, 191 min)
    **The pull has never once failed. It only sometimes does not run.**
    So the thing to watch is not "did it fail" — that check would be green
    forever, which is F-192's whole family. The thing to watch is SILENCE.

    Every gap-ending run also started off-cadence (second :02, :39, :42 against
    a normal :09-:12), which is what a missed scheduled task firing on wake
    looks like — consistent with the laptop sleeping, not with a broken link.

WHAT IT DOES
    Mirrors medical_agent's heartbeat on the manojz side, and adds the one
    thing neither side had: it notices its own silence and says so.

    Read-only. It writes exactly one file — its own heartbeat.
"""

import os
import re
import sys
import csv
import glob
import datetime as dt

BASE = os.environ.get("MARGSYNC", r"D:\Downloads\margsync")
STALE_WARN = int(os.environ.get("PULL_STALE_WARN", "20"))    # minutes
STALE_BAD = int(os.environ.get("PULL_STALE_BAD", "45"))
# ⚠ the log writes FRACTIONAL seconds: "27-08-2026 14:51:42.68  ok".
# A pattern that demands whitespace straight after the seconds matches NOTHING,
# and the agent then reports "NO LOG FOUND" — a false alarm about the very
# thing it exists to watch. Caught by the selftest on the real file.
LINE = re.compile(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})(?:\.\d+)?\s+(.*)$")


def _p(*a):
    return os.path.join(BASE, *a)


def pull_runs():
    """Every pull run in the log, oldest first: (when, verdict)."""
    out = []
    for f in sorted(glob.glob(_p("MargPull", "_logs", "pull_*.log"))):
        try:
            fh = open(f, errors="replace")
        except OSError:
            continue
        with fh:
            for ln in fh:
                m = LINE.match(ln.strip())
                if not m:
                    continue
                d, mo, y, h, mi, s, verdict = m.groups()
                out.append((dt.datetime(int(y), int(mo), int(d),
                                        int(h), int(mi), int(s)), verdict.strip()))
    out.sort()
    return out


def gaps(runs, threshold_min=15):
    g = []
    for i in range(1, len(runs)):
        mins = (runs[i][0] - runs[i - 1][0]).total_seconds() / 60.0
        if mins > threshold_min:
            g.append((runs[i - 1][0], runs[i][0], mins))
    return g


def last_ingest():
    """The newest row the router wrote, and how many it has ever written."""
    path = _p("MargArchive", "index.csv")
    newest, n, kinds = None, 0, {}
    try:
        fh = open(path, newline="", errors="replace")
    except OSError:
        return (None, 0, {})
    with fh:
        for row in csv.DictReader(fh):
            n += 1
            k = (row.get("type") or "").strip()
            kinds[k] = kinds.get(k, 0) + 1
            seen = (row.get("seen_at") or "").strip()
            if seen and (newest is None or seen > newest):
                newest = seen
    return (newest, n, kinds)


def report(now=None):
    # NOTE: the log is written in the machine's LOCAL time (IST on manojz).
    # Staleness is therefore only meaningful when this runs on manojz itself.
    now = now or dt.datetime.now()
    runs = pull_runs()
    lines = ["MANOJZ PIPELINE HEARTBEAT   %s" % now.strftime("%Y-%m-%dT%H:%M:%S"),
             "agent S206.1 on MANOJZ (python %s)" % sys.version.split()[0], ""]
    alarm = False

    if not runs:
        lines.append("PULL    : NO LOG FOUND at %s" % _p("MargPull", "_logs"))
        alarm = True
    else:
        last, verdict = runs[-1]
        quiet = (now - last).total_seconds() / 60.0
        if quiet >= STALE_BAD:
            state, alarm = "SILENT", True
        elif quiet >= STALE_WARN:
            state, alarm = "LATE", True
        else:
            state = "ALIVE"
        lines.append("PULL    : %s -- last run %s (%s), %.0f min ago"
                     % (state, last.strftime("%Y-%m-%dT%H:%M:%S"), verdict, quiet))
        bad = [r for r in runs if not r[1].endswith("ok")]
        lines.append("          %d runs logged, %d not-ok" % (len(runs), len(bad)))
        g = gaps(runs)
        lines.append("          %d gap(s) over 15 min in the log" % len(g))
        for a, b, mins in g[-3:]:
            lines.append("            %s -> %s   %.0f min"
                         % (a.strftime("%d-%b %H:%M"), b.strftime("%d-%b %H:%M"), mins))
        if len(runs) > 1:
            span = (runs[-1][0] - runs[0][0]).total_seconds() / 60.0
            lines.append("          log covers %.1f h -- %s"
                         % (span / 60.0,
                            "too short to call a gap normal or not"
                            if span < 60 * 72 else "enough history to judge"))

    newest, n, kinds = last_ingest()
    if newest:
        lines.append("ROUTER  : %d rows ever; newest %s" % (n, newest))
        top = sorted(kinds.items(), key=lambda kv: -kv[1])[:6]
        lines.append("          " + " · ".join("%s %d" % (k or "(blank)", v) for k, v in top))
    else:
        lines.append("ROUTER  : index.csv unreadable at %s" % _p("MargArchive"))
        alarm = True

    for label, rel in (("SPOOL", ("MargArchive", "_spool")),
                       ("REFUSED", ("MargArchive", "_REFUSED")),
                       ("UNKNOWN", ("MargArchive", "_UNKNOWN"))):
        d = _p(*rel)
        try:
            k = len([x for x in os.listdir(d) if x.lower().endswith((".xls", ".xlsx", ".pdf"))])
        except OSError:
            k = -1
        lines.append("%-8s: %s" % (label, "unreadable" if k < 0 else "%d file(s)" % k))

    lines.append("")
    lines.append("VERDICT : %s" % ("** NEEDS A LOOK **" if alarm else "healthy"))
    return "\n".join(lines), alarm


def main(argv=None):
    argv = argv or sys.argv[1:]
    text, alarm = report()
    print(text)
    out = _p("MargPull", "_manojz_heartbeat.txt")
    try:
        with open(out, "w") as fh:
            fh.write(text + "\n")
        print("\nwritten: %s" % out)
    except OSError as e:
        print("\ncould not write heartbeat: %s" % e)
    return 1 if alarm else 0


if __name__ == "__main__":
    sys.exit(main())
