#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s911.py -- kit S911: builds owner_console.py (TO) from the live bytes (FROM 500534f7, S897's) by two exact anchors.
    python3 make_s911.py <owner_console.py FROM> <owner_console.py TO>
"""
import ast
import hashlib
import sys

FROM_MD5 = "500534f7"

A1 = "def sec_work(con, cx):\n"
NEW1 = '''FUT_DIR = os.path.join(os.path.dirname(FIN), "followup_tracker")                       # S911: the server's tracker folder
FUT_RUNNER_LOG = os.path.join(FUT_DIR, "logs", "runner.log")
FUT_OFF = os.path.join(FUT_DIR, "OFF")                                                  # present = the PC makes the list


def _s911_call_cap_lines():
    """S911 (D1027): the newest 'CALL CAP' line of the server runner's log -- how many of the day's due calls fitted under the
    120-call cap, and how many wait for the next run. Read only; the cap itself stays. While the OFF file is present the PC
    makes the list, and the log is not read at all -- the line says so."""
    if not os.path.isdir(FUT_DIR):
        return []
    if os.path.exists(FUT_OFF):
        return [L("n", "Call list: the clinic PC makes it until the switch; how many fit under the 120-call cap shows here from the "
                  "server's first run")]
    found, stamp, last_stamp = None, "", ""
    try:
        with open(FUT_RUNNER_LOG, "rb") as fh:
            fh.seek(0, 2)
            n = fh.tell()
            fh.seek(max(0, n - 65536))
            tail = fh.read().decode("utf-8", "replace")
        for ln in tail.splitlines():
            m = re.match(r"\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2})", ln)
            if m:
                last_stamp = m.group(1)
            m = re.search(r"CALL CAP: kept (\\d+) of (\\d+) due for a call -- (\\d+) wait", ln)
            if m:
                found, stamp = (int(m.group(1)), int(m.group(2)), int(m.group(3))), last_stamp
    except OSError:
        pass
    if not found:
        return [L("n", "Call list: the server has not yet reported its 120-call cap count -- it shows here after its first evening run")]
    kept, due, wait = found
    at = ""
    if stamp:
        try:
            d = dt.datetime.strptime(stamp, "%Y-%m-%d %H:%M")
            at = " (the server's run of %s %s)" % (d.strftime("%d-%b"), d.strftime("%H:%M"))
        except ValueError:
            at = ""
    if wait <= 0:
        return [L("g", "Call list: all %d due calls are on the sheet%s" % (due, at))]
    return [L("n", "Call list: %d of %d due calls on the sheet -- %d wait for tomorrow (the 120-call cap)%s" % (kept, due, wait, at),
              href="/finance/console/patients", link="Patients", fig="%d of %d" % (kept, due))]


'''
A2 = '''        if os.path.exists(os.path.join(FIN, "docterz_door.py")):     # S897: one line that opens the Docterz reports door
            out.append(L("n", "Any Docterz CSV -- a long-period report, a clinical data report, a patient list -- goes in at one door",
                         href="/finance/console/docterz-reports", link="Docterz reports"))
        return out
'''
NEW2 = '''        if os.path.exists(os.path.join(FIN, "docterz_door.py")):     # S897: one line that opens the Docterz reports door
            out.append(L("n", "Any Docterz CSV -- a long-period report, a clinical data report, a patient list -- goes in at one door",
                         href="/finance/console/docterz-reports", link="Docterz reports"))
        try:                                                          # S911: the 120-call cap's count (D1027), read only
            out.extend(_s911_call_cap_lines())
        except Exception:
            pass
        return out
'''


def main(src, dst):
    raw = open(src, "rb").read()
    h = hashlib.md5(raw).hexdigest()[:8]
    if h != FROM_MD5:
        raise SystemExit("FROM is %s, not %s -- not the file this kit was built on" % (h, FROM_MD5))
    s = raw.decode("utf-8")
    for a in (A1, A2):
        if s.count(a) != 1:
            raise SystemExit("anchor not exactly once: %r" % a[:60])
    s = s.replace(A1, NEW1 + A1).replace(A2, NEW2)
    ast.parse(s)
    open(dst, "wb").write(s.encode("utf-8"))
    print("%s -> %s (%s)" % (src, dst, hashlib.md5(s.encode("utf-8")).hexdigest()[:8]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
