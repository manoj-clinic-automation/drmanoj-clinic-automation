#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s594.py -- the walk of kit S594_WITNESS_CRON (brief v2, section 3).

Works on the crontab TEXT only -- a copy of `crontab -l` given with --crontab -- never the live crontab:
  * the add is idempotent (applied twice to the copy -> one line, the rest of the text byte for byte as it was),
  * the line parses as five fields + command (58 23 * * *; cd .. && <python> -B stock_figure.py witness >> <log> 2>&1 # S577_WITNESS),
  * the command's program exists and is executable, its script exists and is readable, its working folder and log folder exist,
  * the line's tag is unique in the file after the add, and no other line at the same minute writes to the same log,
  * --run-witness (on the box, read only): `stock_figure.py witness` run once as the line will run it -- exit 0, its last line names
    the file, the file is there and not empty; "switched off" is a FAIL, "not ready" is a NOTE (the exit is 0 and the file is written).
  * --expect-red: the negative control -- a copy that ALREADY holds the tag must make the walk refuse to add (exit 0 then; a copy
    without the tag makes the control itself red: "NOT RED").
Exit 0 green, 1 red, 2 refused (the copy already holds the tag and --expect-red was not given).
No number of ten digits or more is printed (mask)."""
import argparse
import os
import re
import subprocess
import sys

KIT = "S594_WITNESS_CRON"
TAG = "# S577_WITNESS"
CRON_LINE = "58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS"

RE_FIELDS = re.compile(r"^(\S+) (\S+) (\S+) (\S+) (\S+) (.+)$")
RE_CMD = re.compile(r"^cd (\S+) && (\S+) -B (\S+) witness >> (\S+) 2>&1 " + re.escape(TAG) + "$")
RE_WRITTEN = re.compile(r"^stock_figure witness written: (\S+)$")


def mask(s):
    return re.sub(r"\d{10,}", "##########", s)


class Refused(Exception):
    pass


def tag_count(text):
    return sum(1 for ln in text.split("\n") if TAG in ln)


def apply_add(text):
    """The add exactly as the installer does it: `( crontab -l; echo "$CRON_LINE" ) | crontab -`, behind the gate
    `grep -c '# S577_WITNESS'` == 0. A text that already holds the tag is refused (nothing added)."""
    if tag_count(text):
        raise Refused("the text already holds %r (%d line(s))" % (TAG, tag_count(text)))
    if not text.endswith("\n"):
        raise Refused("the text does not end in a newline -- an echo after it would glue onto the last line")
    return text + CRON_LINE + "\n"


class Walk(object):
    def __init__(self):
        self.n = 0
        self.fails = []
        self.notes = []

    def c(self, name, ok, detail=""):
        self.n += 1
        detail = mask(str(detail))
        if ok:
            print("  ok   %s%s" % (name, (": " + detail) if detail else ""))
        else:
            print("  FAIL %s%s" % (name, (": " + detail) if detail else ""))
            self.fails.append(name)
        return ok

    def note(self, text):
        text = mask(text)
        print("  NOTE %s" % text)
        self.notes.append(text)


def schedule_of(line):
    m = RE_FIELDS.match(line.strip())
    return m.groups() if m else None


def main():
    ap = argparse.ArgumentParser(description="the walk of kit %s" % KIT)
    ap.add_argument("--crontab", required=True, help="a text copy of `crontab -l` (never the live crontab)")
    ap.add_argument("--workdir", default=None, help="the folder the line cd's into (default: the line's own)")
    ap.add_argument("--program", default=None, help="the python the line runs (default: the line's own)")
    ap.add_argument("--script", default=None, help="the script the line runs (default: the line's own, inside --workdir)")
    ap.add_argument("--log", default=None, help="the log file the line appends to (default: the line's own)")
    ap.add_argument("--run-witness", action="store_true", help="on the box: run the command once as the line will run it (read only)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--expect-red", action="store_true", help="the negative control: the copy already holds the tag -> the walk must refuse")
    ap.add_argument("--print-line", action="store_true", help="print the line and exit")
    a = ap.parse_args()
    if a.print_line:
        print(CRON_LINE)
        return 0

    with open(a.crontab, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8", "replace")
    lines0 = text.count("\n")
    n_tag0 = tag_count(text)

    if a.expect_red:
        if n_tag0:
            print("WALK OK negative control %s: the walk refuses to add -- the copy already holds '%s' (%d line(s), %d lines in all)" % (KIT, TAG, n_tag0, lines0))
            return 0
        print("  NOT RED: the copy has no '%s' line (%d lines) -- the walk would add it; the negative control proves nothing" % (TAG, lines0))
        print("WALK RED negative control %s" % KIT)
        return 1

    W = Walk()
    print("walk %s on the crontab text %s (%d lines, %d entries)" % (KIT, os.path.basename(a.crontab), lines0,
          sum(1 for ln in text.split("\n") if ln.strip() and not ln.lstrip().startswith("#"))))

    # ---- 1 the text as it is --------------------------------------------------------------------------------------------------------
    W.c("1.1 the copy is not empty", len(raw) > 0, "%d bytes" % len(raw))
    W.c("1.2 the copy ends in a newline", raw.endswith(b"\n"))
    if not W.c("1.3 no witness line yet", n_tag0 == 0, "%d line(s) carry %s" % (n_tag0, TAG)):
        print("WALK RED %s (refused: the copy already holds the tag; nothing to add)" % KIT)
        return 2

    # ---- 2 the add, once and twice --------------------------------------------------------------------------------------------------
    try:
        once = apply_add(text)
    except Refused as e:
        W.c("2.1 the add applies once", False, str(e))
        print("WALK RED %s" % KIT)
        return 1
    W.c("2.1 the add applies once", tag_count(once) == 1 and once.count("\n") == lines0 + 1, "%d -> %d lines, %d tagged line" % (lines0, once.count("\n"), tag_count(once)))
    W.c("2.2 the rest of the text is byte for byte as it was", once.startswith(text) and once[len(text):] == CRON_LINE + "\n")
    W.c("2.3 the last line is the brief's line", once.split("\n")[-2] == CRON_LINE)
    try:
        apply_add(once)
        twice = None
    except Refused as e:
        twice = str(e)
    W.c("2.4 a second add refuses (idempotent: applied twice -> one line)", twice is not None and tag_count(once) == 1, twice or "a second line was added")

    # ---- 3 the line parses ----------------------------------------------------------------------------------------------------------
    f = schedule_of(CRON_LINE)
    W.c("3.1 five fields + command", f is not None and len(f) == 6)
    if f:
        mi, hh, dom, mon, dow, cmd = f
        W.c("3.2 minute 58, hour 23, every day", (mi, hh, dom, mon, dow) == ("58", "23", "*", "*", "*"), "%s %s %s %s %s" % (mi, hh, dom, mon, dow))
        W.c("3.3 the command ends in the tag", cmd.endswith(" " + TAG))
        m = RE_CMD.match(cmd)
        W.c("3.4 the command parses: cd <dir> && <python> -B <script> witness >> <log> 2>&1 # tag", m is not None, cmd)
    else:
        m = None
    if not m:
        print("WALK RED %s" % KIT)
        return 1
    workdir, program, script, log = m.groups()
    W.c("3.5 the script is stock_figure.py, the program the jobs' venv python", script == "stock_figure.py" and program == "/root/wa/venv/bin/python3", "%s %s" % (program, script))
    W.c("3.6 the log is the witness log in the spine folder", log == "/root/finance/spine/stock_figure_witness.log", log)

    # ---- 4 the tag unique, no clash at the same minute ----------------------------------------------------------------------------
    W.c("4.1 the tag is unique after the add", tag_count(once) == 1)
    same_min = []
    same_log = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        g = schedule_of(s)
        if g and g[0] == "58" and g[1] == "23":
            same_min.append(s)
        if (">> " + log + " ") in (s + " ") or ("> " + log + " ") in (s + " "):
            same_log.append(s)
    W.c("4.2 no other line writes to the witness log", not same_log, "%d line(s)" % len(same_log))
    W.c("4.3 the lines already at 58 23 write elsewhere", all(log not in s for s in same_min), "%d other line(s) at 58 23: %s" % (len(same_min), "; ".join(s.split("#")[-1].strip() for s in same_min) or "none"))

    # ---- 5 the program, the script, the folders -----------------------------------------------------------------------------------
    wd = a.workdir or workdir
    prog = a.program or program
    scr = a.script or os.path.join(wd, script)
    lg = a.log or log
    W.c("5.1 the working folder exists", os.path.isdir(wd), wd)
    W.c("5.2 the program exists and is executable", os.path.isfile(prog) and os.access(prog, os.X_OK), prog)
    W.c("5.3 the script exists and is readable", os.path.isfile(scr) and os.access(scr, os.R_OK), scr)
    W.c("5.4 the log folder exists and is writable", os.path.isdir(os.path.dirname(lg)) and os.access(os.path.dirname(lg), os.W_OK), os.path.dirname(lg))

    # ---- 6 the rehearsal (the box only) --------------------------------------------------------------------------------------------
    reh = ""
    if a.run_witness:
        try:
            p = subprocess.run([prog, "-B", scr, "witness"], cwd=wd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=a.timeout)
            out = p.stdout.decode("utf-8", "replace")
            rc = p.returncode
        except subprocess.TimeoutExpired:
            out, rc = "(timed out after %d s)" % a.timeout, 124
        except OSError as e:
            out, rc = str(e), 127
        outl = [x for x in out.rstrip("\n").split("\n") if x != ""]
        last = outl[-1] if outl else ""
        for x in outl[:-1]:
            W.note("rehearsal stderr/stdout: %s" % x[:300])
        W.c("6.1 the rehearsal exits 0", rc == 0, "exit %d" % rc)
        W.c("6.2 not switched off", "switched off" not in out, last[:200])
        mw = RE_WRITTEN.match(last)
        W.c("6.3 the last line names the file", mw is not None, last[:200])
        wf = mw.group(1) if mw else ""
        size = os.path.getsize(wf) if wf and os.path.isfile(wf) else -1
        W.c("6.4 the file is there and not empty", size > 0, "%s, %d bytes" % (wf, size))
        if size > 0:
            with open(wf, "r", encoding="utf-8", errors="replace") as fh:
                wl = fh.read().split("\n")
            if any("not ready" in x for x in wl[:3]):
                W.note("the file says the spine is not ready (reported, not a stop): %s" % wl[1][:200])
            items = 0
            seen_head = False
            for x in wl:
                if x.startswith("item ") and "marg()" in x:
                    seen_head = True
                    continue
                if seen_head:
                    if not x.strip():
                        break
                    items += 1
            apart = [x for x in wl if x.startswith("marg() vs") or x.startswith("marg_shadow lines")]
            reh = "%s (%d bytes): %d items compared; %s" % (os.path.basename(wf), size, items, " · ".join(apart))
            print("  the first ten lines of the file:")
            for x in wl[:10]:
                print("     " + mask(x)[:200])
            W.c("6.5 the file compares items (or says why not)", items > 0 or any("not ready" in x for x in wl[:3]), "%d items" % items)
            print("  REHEARSAL %s" % mask(reh))

    if W.fails:
        print("WALK RED %s: %d check(s) red of %d: %s" % (KIT, len(W.fails), W.n, "; ".join(W.fails)))
        return 1
    print("WALK OK %s: %d checks green (the crontab text %d -> %d lines, the add idempotent, the line parses, program/script/folders present%s)%s" % (
        KIT, W.n, lines0, lines0 + 1, ", the rehearsal wrote its file" if a.run_witness else "", ("; %d note(s)" % len(W.notes)) if W.notes else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
