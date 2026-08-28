#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_manojz.py -- rehearse REINSTALL_MANOJZ.md section 7, READ-ONLY.

S207 / Q2 of the UNATTENDED_QUEUE.  Turns the six proof checks in
`deploy_kits/S205_LIVE_TOOLS/REINSTALL_MANOJZ.md` section 7 into one command
that prints a pass/fail table and exits 0 (all clear) or 1 (something failed).

WHY THIS EXISTS
    The reinstall kit has NEVER BEEN REHEARSED.  A recovery document nobody has
    followed is a guess.  The only way it ever gets rehearsed without risk is if
    running it changes nothing -- so this file changes nothing, on purpose, and
    can therefore be run on the LIVE machine on any ordinary day.

WHAT "READ-ONLY" MEANS HERE, EXACTLY
    This script opens files for reading, lists directories, and runs
    `pipeline_status.py` in its two harmless modes (--selftest, which works in a
    temp folder, and --dry-run, which gathers and PRINTS and posts nothing).
    It never writes to D:\\Downloads\\margsync\\, never posts, never sends,
    never touches the medical PC's disk, and never reads a token.

    ONE CHECK IS DELIBERATELY NOT THE DOCUMENT'S CHECK.  Section 7 check 5 says
    to RUN PULL_FROM_MEDICAL.bat.  That is not read-only -- it copies, files,
    sends to the clinic server and mirrors to Drive.  So check 5 here READS THE
    EVIDENCE the last scheduled run left in `_last_pull.txt` instead.  That is a
    weaker check and it is labelled as such in the output.  It is not a
    substitute on a REBUILT machine, where the pull has never run: there, run
    the batch by hand, once, as the document says.

USAGE
      VERIFY_MANOJZ.bat                 (the wrapper -- finds python for you)
      python verify_manojz.py
      python verify_manojz.py --selftest    prove the parsers offline
      python verify_manojz.py --show-host   print the medical address unmasked

STANDARD LIBRARY ONLY.  Python 3.8+.  A verifier that needs pip is a verifier
that cannot run on the machine it was written to rebuild.
"""

import argparse
import datetime
import io
import json
import os
import re
import subprocess
import sys
import time

VERSION = "S207.2"          # S207.1 -> .2 after the first live run:
                            # the zone label, the future-dated heartbeat,
                            # and IGNORED. Bump this WITH KIT_ID.txt.

MARGPULL   = r"D:\Downloads\margsync\MargPull"
LAST_PULL  = os.path.join(MARGPULL, "_last_pull.txt")
PICTURE    = r"D:\Downloads\margsync\MARG_PICTURE.txt"
STATUS_PY  = os.path.join(MARGPULL, "pipeline_status.py")

# How stale _last_pull.txt may be before check 5 is a WARN. The scheduled task
# runs every 10 minutes; 30 gives it two misses before anyone is told off.
PULL_STALE_MINUTES = 30

PASS, FAIL, WARN, MANUAL, INFO = "PASS", "FAIL", "WARN", "MANUAL", "INFO"


# ---------------------------------------------------------------- parsers
# Every one of these is a pure function of text so the selftest can prove it
# without the live machine. That is the whole reason they are separate.

def parse_last_pull(text):
    """Read _last_pull.txt. Returns the LAST END line's verdict.

    The file is appended to, so the last END line is the live one. An earlier
    PROBLEM followed by a later ok means the pull recovered -- reading the
    first match instead of the last would report a fault that is over.
    """
    out = {"end_line": None, "ended_ok": None, "problem": "", "starts": 0}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if line.startswith("START"):
            out["starts"] += 1
        if not line.startswith("END"):
            continue
        out["end_line"] = line
        if "-- ok" in line:
            out["ended_ok"] = True
            out["problem"] = ""
        elif "PROBLEM" in line:
            out["ended_ok"] = False
            m = re.search(r"PROBLEM:\s*(.*)$", line)
            out["problem"] = (m.group(1).strip() if m else "unnamed")
    return out


def parse_picture(text):
    """Read MARG_PICTURE.txt's two headline numbers.

    Written by marg_gate.py as
        days with NO export   : 0
        exports NOT on server : 0
    The spacing is cosmetic and has changed before, so match on the words.
    """
    out = {"no_export_days": None, "not_on_server": None}
    m = re.search(r"days\s+with\s+NO\s+export\s*:\s*(\d+)", text or "", re.I)
    if m:
        out["no_export_days"] = int(m.group(1))
    m = re.search(r"exports\s+NOT\s+on\s+server\s*:\s*(\d+)", text or "", re.I)
    if m:
        out["not_on_server"] = int(m.group(1))
    return out


def parse_share_probe(source):
    """Pull DEF_MEDICAL_HOST out of pipeline_status.py's own source.

    NOT hard-coded here, deliberately. Two files carrying the same address is
    two files to change on the day it moves, and the one nobody changes is the
    one that fails silently. pipeline_status.py is the source of truth; this
    reads it. Returns None if it cannot be found -- and the check then says so
    rather than guessing.
    """
    m = re.search(r'^DEF_MEDICAL_HOST\s*=\s*["\']([^"\']+)["\']',
                  source or "", re.M)
    if not m:
        return None
    return m.group(1)


def mask_host(host):
    """100.119.151.40 -> 100.119.151.xx . A tailnet address is not a secret,
    but printing one costs nothing to avoid (--show-host prints it whole)."""
    if not host:
        return "?"
    parts = host.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return ".".join(parts[:3] + ["xx"])
    return host[:3] + "..." if len(host) > 6 else host


def redact(text, host, show=False):
    """Take the medical address back out of anything we are about to print.

    Masking the path we BUILT is not enough: an OSError carries the full path
    in its own message, and that message goes straight to the screen. The
    first version of this file masked the header and then printed
    "No such file or directory: '\\\\100.119.151.40\\DDrive...'" one line
    below it -- caught by running it, which is the only way that is ever found.
    """
    if show or not host or not text:
        return text
    return text.replace(host, mask_host(host))


def parse_selftest_line(text):
    """'PIPELINE_STATUS SELFTEST PASSED - 42 checks OK' -> (True, 42)."""
    t = text or ""
    n = None
    m = re.search(r"(\d+)\s+checks?\s+OK", t, re.I)
    if m:
        n = int(m.group(1))
    ok = bool(re.search(r"SELFTEST\s+PASSED", t, re.I))
    return ok, n


def age_minutes(path, now=None):
    """Minutes since a file was last written, or None if it is not there.

    Uses mtime, NOT the timestamp inside the file. %DATE% in a .bat is
    locale-dependent -- it has been dd-mm-yyyy on this machine, but a rebuilt
    Windows with a different regional setting writes something else, and a
    verifier that misreads a date is worse than one that does not read it.
    """
    try:
        st = os.stat(path)
    except OSError:
        return None
    now = now or datetime.datetime.now()
    return (now - datetime.datetime.fromtimestamp(st.st_mtime)).total_seconds() / 60.0


def stamp(now=None):
    """The local time, labelled with the machine's ACTUAL zone.

    It used to hard-code "IST". That is right on manojz and on the medical PC,
    and WRONG anywhere else -- the first live run of this file printed
    "27-Aug 23:59 IST" on a box running UTC, which is exactly the mistake the
    working protocol exists to prevent. If the label is not IST, the machine is
    not the one this was written for, and that is worth seeing.
    """
    now = now or datetime.datetime.now()
    try:
        zone = time.strftime("%Z") or "local"
    except Exception:                                          # noqa: BLE001
        zone = "local"
    return "%s %s" % (now.strftime("%d-%b-%Y %H:%M:%S"), zone)


def read_text(path, limit=400000):
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return None


# ---------------------------------------------------------------- the run
def run(py, args, timeout=180):
    """Run a child and return (rc, combined output). Never raises."""
    try:
        p = subprocess.run([py] + args, capture_output=True, timeout=timeout)
        out = (p.stdout or b"").decode("utf-8", "replace")
        err = (p.stderr or b"").decode("utf-8", "replace")
        return p.returncode, (out + err)
    except subprocess.TimeoutExpired:
        return 99, "TIMED OUT after %ds" % timeout
    except OSError as ex:
        return 98, "could not run: %s" % ex


class Table(object):
    def __init__(self):
        self.rows = []

    def add(self, num, name, verdict, detail):
        self.rows.append((num, name, verdict, detail))

    def render(self):
        L = []
        L.append("")
        L.append("  #  CHECK                          RESULT   DETAIL")
        L.append("  -- ------------------------------ -------- " + "-" * 44)
        for num, name, verdict, detail in self.rows:
            first = True
            for chunk in (detail or "").split("\n"):
                if first:
                    L.append("  %-2s %-30s %-8s %s" % (num, name[:30], verdict, chunk))
                    first = False
                else:
                    L.append("  %-2s %-30s %-8s %s" % ("", "", "", chunk))
        return "\n".join(L)

    def counts(self):
        c = {}
        for _n, _k, v, _d in self.rows:
            c[v] = c.get(v, 0) + 1
        return c


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Read-only rehearsal of REINSTALL_MANOJZ.md section 7")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the parsers offline; touches nothing")
    ap.add_argument("--show-host", action="store_true",
                    help="print the medical address unmasked")
    ap.add_argument("--margpull", default=MARGPULL)
    ap.add_argument("--picture", default=PICTURE,
                    help="override MARG_PICTURE.txt (used by the offline tests)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    margpull  = a.margpull
    status_py = os.path.join(margpull, "pipeline_status.py")
    last_pull = os.path.join(margpull, "_last_pull.txt")
    py        = sys.executable or "python"

    t = Table()
    print("=" * 78)
    print("  VERIFY_MANOJZ  %s   read-only rehearsal of REINSTALL_MANOJZ.md 7" % VERSION)
    print("  %s" % stamp())
    print("  It changes NOTHING. Safe on the live machine, any day.")
    print("=" * 78)

    # ---- 1 -- python
    t.add("1", "Python 3 present", PASS,
          "%s\n%s" % (sys.version.split()[0], py))

    # ---- 2 -- the medical share
    src = read_text(status_py)
    if src is None:
        t.add("2", "Medical share readable", FAIL,
              "cannot read %s\nso the medical address is unknown" % status_py)
        host = None
    else:
        host = parse_share_probe(src)
        if not host:
            t.add("2", "Medical share readable", FAIL,
                  "DEF_MEDICAL_HOST not found in pipeline_status.py")
        else:
            shown = host if a.show_host else mask_host(host)
            probe = r"\\%s\DDrive\MARGERP\users" % host
            try:
                names = os.listdir(probe)
                t.add("2", "Medical share readable", PASS,
                      r"\\%s\DDrive\MARGERP\users" % shown +
                      "\n%d entr%s listed" % (len(names),
                                              "y" if len(names) == 1 else "ies"))
            except OSError as ex:
                t.add("2", "Medical share readable", FAIL,
                      r"\\%s\DDrive\MARGERP\users" % shown +
                      "\n%s: %s" % (ex.__class__.__name__,
                                    redact(str(ex), host, a.show_host)) +
                      "\nif this says guest access is blocked, the stored" +
                      "\ncredential of REINSTALL_MANOJZ.md section 4 is missing")

    # ---- 3 -- pipeline_status selftest
    if not os.path.isfile(status_py):
        t.add("3", "pipeline_status --selftest", FAIL,
              "not found: %s" % status_py)
    else:
        rc, out = run(py, [status_py, "--selftest"])
        ok, n = parse_selftest_line(out)
        if rc == 0 and ok:
            t.add("3", "pipeline_status --selftest", PASS,
                  "SELFTEST PASSED, %s checks OK" % (n if n is not None else "?"))
        else:
            t.add("3", "pipeline_status --selftest", FAIL,
                  "exit %s\n%s" % (rc, (out or "").strip().splitlines()[-1][:60]
                                   if (out or "").strip() else "no output"))

    # ---- 4 -- pipeline_status dry-run
    payload = None
    if not os.path.isfile(status_py):
        t.add("4", "pipeline_status --dry-run", FAIL, "not found")
    else:
        rc, out = run(py, [status_py, "--dry-run"])
        try:
            start = out.index("{")
            payload = json.loads(out[start:])
        except (ValueError, IndexError):
            payload = None
        if payload is None:
            t.add("4", "pipeline_status --dry-run", FAIL,
                  "exit %s, and no JSON came back" % rc)
        else:
            verdict = (payload.get("link") or {}).get("verdict")
            cred = (payload.get("credential") or {}).get("exists")
            bits = ["link.verdict = %s" % verdict,
                    "credential.exists = %s" % cred]
            if verdict == "ok" and cred is True:
                t.add("4", "pipeline_status --dry-run", PASS, "\n".join(bits))
            else:
                bits.append("wanted verdict ok and credential true")
                t.add("4", "pipeline_status --dry-run", FAIL, "\n".join(bits))
            # the JSON is NEVER printed whole: it carries paths and counts that
            # do not belong in a log somebody pastes into a chat.

    # ---- 5 -- last pull (SUBSTITUTE: the document says RUN the batch)
    txt = read_text(last_pull)
    if txt is None:
        t.add("5", "Last pull ended ok  (read)", FAIL,
              "no %s\nOn a REBUILT machine this is expected: run" % last_pull +
              "\nPULL_FROM_MEDICAL.bat once by hand, as section 7 says.")
    else:
        lp = parse_last_pull(txt)
        mins = age_minutes(last_pull)
        agestr = "written %s min ago" % (int(mins) if mins is not None else "?")
        if lp["ended_ok"] is True and mins is not None and mins <= PULL_STALE_MINUTES:
            t.add("5", "Last pull ended ok  (read)", PASS,
                  "END ... -- ok\n%s" % agestr)
        elif lp["ended_ok"] is True:
            t.add("5", "Last pull ended ok  (read)", WARN,
                  "END ... -- ok, but %s\nthe 10-minute task may not be running" % agestr)
        elif lp["ended_ok"] is False:
            t.add("5", "Last pull ended ok  (read)", FAIL,
                  "END ... -- PROBLEM: %s\n%s" % (lp["problem"], agestr))
        else:
            t.add("5", "Last pull ended ok  (read)", FAIL,
                  "no END line in the file\n%s" % agestr)

    # ---- 6 -- the picture
    txt = read_text(a.picture)
    if txt is None:
        t.add("6", "MARG_PICTURE both zero", FAIL, "no %s" % a.picture)
    else:
        pic = parse_picture(txt)
        d, s = pic["no_export_days"], pic["not_on_server"]
        detail = "days with NO export   : %s\nexports NOT on server : %s" % (
            "?" if d is None else d, "?" if s is None else s)
        if d == 0 and s == 0:
            t.add("6", "MARG_PICTURE both zero", PASS, detail)
        elif d is None or s is None:
            t.add("6", "MARG_PICTURE both zero", FAIL,
                  detail + "\ncould not read one of the two numbers")
        else:
            t.add("6", "MARG_PICTURE both zero", FAIL, detail)

    # ---- 7 -- the one that is not a command
    t.add("7", "Heartbeat on the health page", MANUAL,
          "open the clinic health page and confirm" +
          "\n'Pipeline heartbeat - manojz reported N minutes ago'." +
          "\nSection 7: until that is true the rebuild is NOT finished," +
          "\nhowever green everything above is.")

    print(t.render())
    c = t.counts()
    print("")
    print("  PASS %d   FAIL %d   WARN %d   MANUAL %d"
          % (c.get(PASS, 0), c.get(FAIL, 0), c.get(WARN, 0), c.get(MANUAL, 0)))
    print("")
    if c.get(FAIL):
        print("  RESULT: FAIL -- %d check(s) did not pass. The rebuild is not proven."
              % c[FAIL])
        return 1
    if c.get(WARN):
        print("  RESULT: PASS WITH WARNINGS -- read the WARN row(s) above.")
    else:
        print("  RESULT: PASS -- every automatable check in section 7 is green.")
    print("  Check 7 is a human step and is NOT counted. Check 5 READ the last")
    print("  pull rather than running one; on a rebuilt machine run the batch once.")
    return 0


# ---------------------------------------------------------------- selftest
def selftest():
    """Prove every parser offline, against strings taken from the real files.

    Run this before trusting a run on a live machine. It touches no path on
    either PC and needs neither.
    """
    n = [0]

    def ck(cond, msg):
        n[0] += 1
        if not cond:
            print("check %d FAILED: %s" % (n[0], msg))
            raise AssertionError(msg)

    # -- parse_last_pull
    lp = parse_last_pull("START 26-08-2026 01:00:00\nEND 26-08-2026 01:00:11 -- ok\n")
    ck(lp["ended_ok"] is True, "a clean pull reads as ok")
    ck(lp["starts"] == 1, "one START is counted")
    lp = parse_last_pull("START 26-08-2026 01:10:00\n"
                         "END 26-08-2026 01:10:09 -- PROBLEM: send=1 picture=2\n")
    ck(lp["ended_ok"] is False, "a PROBLEM pull reads as not ok")
    ck("send=1" in lp["problem"], "the failing steps are named: %r" % lp["problem"])
    lp = parse_last_pull("END 26-08 01:00:11 -- PROBLEM: send=1\n"
                         "END 26-08 01:10:11 -- ok\n")
    ck(lp["ended_ok"] is True,
       "the LAST END wins -- a recovered pull is not reported as broken")
    lp = parse_last_pull("END 26-08 01:10:11 -- ok\n"
                         "END 26-08 01:20:11 -- PROBLEM: capture=3\n")
    ck(lp["ended_ok"] is False and "capture=3" in lp["problem"],
       "and equally, an ok followed by a PROBLEM is a PROBLEM")
    ck(parse_last_pull("")["ended_ok"] is None, "an empty file is unknown, not ok")
    ck(parse_last_pull("START 1\n")["ended_ok"] is None,
       "a pull that started and never ended is unknown, not ok")

    # -- parse_picture
    p = parse_picture("days with NO export   : 0\nexports NOT on server : 0\n")
    ck(p["no_export_days"] == 0 and p["not_on_server"] == 0, "both zeroes read")
    p = parse_picture("days with NO export   : 3\nexports NOT on server : 12\n")
    ck(p["no_export_days"] == 3 and p["not_on_server"] == 12, "non-zeroes read")
    p = parse_picture("days with NO export: 0\nexports NOT on server: 0\n")
    ck(p["no_export_days"] == 0, "spacing is cosmetic -- matched on the words")
    p = parse_picture("days with NO export   : 2  (28-07, 29-07)\n")
    ck(p["no_export_days"] == 2,
       "a trailing annotation does not break the number (marg_gate appends one)")
    ck(parse_picture("")["no_export_days"] is None, "an empty picture is unknown")
    ck(parse_picture("nothing here")["not_on_server"] is None,
       "a picture missing the line is unknown, NOT zero -- silence is not green")

    # -- parse_share_probe
    ck(parse_share_probe('DEF_MEDICAL_HOST = "100.119.151.40"\n') == "100.119.151.40",
       "the host is read out of pipeline_status.py's own source")
    ck(parse_share_probe("DEF_MEDICAL_HOST = 'medical'\n") == "medical",
       "single quotes too")
    ck(parse_share_probe("# DEF_MEDICAL_HOST = \"1.2.3.4\"\n") is None,
       "a COMMENTED line is not the definition")
    ck(parse_share_probe("") is None, "no source, no guess")

    # -- mask_host
    ck(mask_host("100.119.151.40") == "100.119.151.xx", "the last octet is masked")
    ck(mask_host("medical") == "med...", "a name is truncated")
    ck(mask_host(None) == "?", "no host masks to ?")

    # -- redact. This block exists because the leak it guards was REAL: the
    #    first run of this file masked the header and then printed the whole
    #    address one line below it, inside an OSError message.
    leak = ("[Errno 2] No such file or directory: "
            "'\\\\100.119.151.40\\DDrive\\MARGERP\\users'")
    out = redact(leak, "100.119.151.40")
    ck("100.119.151.40" not in out,
       "the address does NOT survive inside an exception message")
    ck("100.119.151.xx" in out, "and it is replaced by the masked form")
    ck(redact(leak, "100.119.151.40", show=True) == leak,
       "--show-host prints it whole, deliberately")
    ck(redact("nothing to hide", None) == "nothing to hide",
       "no host, nothing to redact")
    ck(redact(None, "1.2.3.4") is None, "no text, no crash")

    # -- parse_selftest_line
    ok, cnt = parse_selftest_line("PIPELINE_STATUS SELFTEST PASSED - 42 checks OK")
    ck(ok is True and cnt == 42, "the selftest banner is read")
    ok, cnt = parse_selftest_line("PIPELINE_STATUS SELFTEST PASSED - 47 checks OK")
    ck(ok is True and cnt == 47,
       "the COUNT is not hard-coded -- 42 today, more tomorrow, still a pass")
    ok, cnt = parse_selftest_line("check 12 FAILED: something")
    ck(ok is False, "a failure is not read as a pass")
    ck(parse_selftest_line("")[0] is False, "no output is not a pass")

    # -- age_minutes
    ck(age_minutes(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "_no_such_file_")) is None,
       "a missing file has no age, and does not crash")

    # -- the table
    tb = Table()
    tb.add("1", "x", PASS, "a")
    tb.add("2", "y", FAIL, "b\nc")
    ck(tb.counts()[FAIL] == 1, "the table counts a FAIL")
    ck("c" in tb.render(), "a multi-line detail is rendered on its own row")

    print("VERIFY_MANOJZ SELFTEST PASSED - %d checks OK" % n[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
