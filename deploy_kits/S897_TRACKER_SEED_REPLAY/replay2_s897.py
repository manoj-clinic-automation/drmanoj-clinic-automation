#!/usr/bin/env python3
"""replay2_s897.py -- kit S897 (the parent, S493, 20-Nov-2026): REPLAY 2 -- the past month again, ON THE BOX (plan s4).

replay_s895.py (S492) proved the code on the PC: 30 of 30 runs identical. This is the same harness pointed at the SEEDED
/root/followup_tracker/ -- the server's Python, libraries, clock and line endings -- so the environment is proved too.
For every 'tracker run for <day>' the PC's console log (seeded, archive/_console.log) records since 19-Oct-2026, re-run
processor.run_daily() with the SAME inputs (uploads/, seeded), from the data snapshot taken just before that run
(data/backups/, seeded), the clock pinned to that run, the Call_Feed fetch OFF and outbound_log.csv from the NEXT snapshot.
THE REFERENCE on the box is the workbook the PC UPLOADED that evening, which the receiver's inbox holds under the day's
name -- the LAST upload of a day wins there, so only the LAST run of each day is compared; an earlier run of the same day is
SKIPPED and said. Pass = the workbook identical cell for cell (the Generated: stamp aside) and every data CSV identical to
the next snapshot (the input file's name and Revenue_ID aside, as Replay 1). Counts, dates and file names only.

    /root/wa/venv/bin/python3 -B replay2_s897.py --list            the pairing table only, nothing run
    /root/wa/venv/bin/python3 -B replay2_s897.py --run [--only N]  replay (all runs, or the N-th), report to --report
"""
import os
os.environ["TZ"] = "Asia/Kolkata"
import time
time.tzset()
import argparse, csv, datetime as dt, glob, importlib, io, re, shutil, sys, tempfile  # noqa: E402

VERSION = "S897.1"
LIVE = os.environ.get("FUT_ROOT", "/root/followup_tracker")
ARCHIVE = os.environ.get("FUT_ARCHIVE", os.path.join(LIVE, "archive"))
INBOX = os.environ.get("FU_INBOX_DIR", "/root/wa/followup-inbox")
SCRATCH = os.environ.get("REPLAY2_SCRATCH", "/tmp/s897replay")
SINCE = "2026-10-19"
RUN_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] tracker run for (\d{4}-\d{2}-\d{2})\s+\(inputs: (\S+) \+ (\S+);")
WROTE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] tracker wrote (\S+)")
SNAP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{6})_daily$")
CODE_FILES = ["processor.py", "revenue.py", "revenue_ingest.py", "concessions.py", "diagnosis_normalizer.py"]
CODE_CHANGE = dt.datetime(2026, 11, 10, 19, 13)
OLD_PROCESSOR = os.path.join("replay", "processor.py.bak_S777_0e7c129f")
CLOCK_MODULES = ["processor", "revenue", "revenue_ingest", "concessions", "diagnosis_normalizer"]


def ts(s):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def read_runs():
    runs, pending = [], None
    with open(os.path.join(ARCHIVE, "_console.log"), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = RUN_RE.match(line)
            if m:
                pending = {"t": ts(m.group(1)), "day": m.group(2), "cons": m.group(3), "fu": m.group(4), "wrote": None}
                continue
            m = WROTE_RE.match(line)
            if m and pending is not None:
                pending["wrote"] = m.group(2)
                if pending["t"].strftime("%Y-%m-%d") >= SINCE:
                    runs.append(pending)
                pending = None
    return runs


def snapshots():
    out = []
    for n in sorted(os.listdir(os.path.join(LIVE, "data", "backups"))):
        m = SNAP_RE.match(n)
        if m and os.path.exists(os.path.join(LIVE, "data", "backups", n, "followup_ledger.csv")):   # an emptied (pruned) folder is no snapshot
            out.append((dt.datetime.strptime(m.group(1) + m.group(2), "%Y-%m-%d%H%M%S"), os.path.join(LIVE, "data", "backups", n)))
    return out


def pair(runs, snaps):
    """snapshot for a run = the one stamped within -5 s .. +90 s of the log line; next = the first later snapshot."""
    for i, r in enumerate(runs):
        r["snap"] = r["next"] = r["ref_xlsx"] = None
        for t, p in snaps:
            if -5 <= (t - r["t"]).total_seconds() <= 90:
                r["snap"] = p
                break
        later = [p for t, p in snaps if r["snap"] and t > ts_of(r["snap"])]
        r["next"] = later[0] if later else None
        # the reference = the workbook the PC uploaded, in the receiver's inbox under the day's name: the LAST run of the
        # day owns it; an earlier run of the same day has no reference on the box (its workbook was overwritten).
        r["last_of_day"] = bool(r["wrote"]) and all(o["t"] <= r["t"] for o in runs if o["wrote"] == r["wrote"])
        if r["last_of_day"]:
            p = os.path.join(INBOX, r["wrote"])
            r["ref_xlsx"] = p if os.path.exists(p) else None
    return runs


def ts_of(snapdir):
    m = SNAP_RE.match(os.path.basename(snapdir))
    return dt.datetime.strptime(m.group(1) + m.group(2), "%Y-%m-%d%H%M%S")


def short(name):
    return name[:38] + ("..." if len(name) > 38 else "")


def print_table(runs):
    print("%-3s %-19s %-10s %-41s %-41s %-6s %-6s %-6s" % ("#", "run at (IST)", "day", "consultation input", "follow-up log", "snap", "next", "inbox"))
    for i, r in enumerate(runs, 1):
        print("%-3d %-19s %-10s %-41s %-41s %-6s %-6s %-6s" % (
            i, r["t"], r["day"], short(r["cons"]), short(r["fu"]),
            "yes" if r["snap"] else "NONE", "yes" if r["next"] else "live", ("yes" if r["ref_xlsx"] else "NONE") if r.get("last_of_day") else "-"))


class Clock:
    """Pin date.today() / datetime.now() in the tracker's modules to one instant."""
    def __init__(self, when):
        self.when = when

    def install(self, modules):
        when = self.when
        class _D(dt.date):
            @classmethod
            def today(cls):
                return dt.date(when.year, when.month, when.day)
        class _DT(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return dt.datetime(when.year, when.month, when.day, when.hour, when.minute, when.second)
            @classmethod
            def today(cls):
                return cls.now()
        for m in modules:
            if hasattr(m, "date"):
                m.date = _D
            if hasattr(m, "datetime"):
                m.datetime = _DT


def pin_instant(r):
    """the minute the PC's own run stamped its ledgers (Processed_On in the next snapshot's revenue ledger), else the log time."""
    best = None
    if r["next"]:
        p = os.path.join(r["next"], "revenue_ledger.csv")
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace", newline="") as fh:
                rd = csv.DictReader(fh)
                col = next((c for c in (rd.fieldnames or []) if c.strip().lower() == "processed_on"), None)
                if col:
                    for row in rd:
                        v = (row.get(col) or "").strip()
                        try:
                            tv = dt.datetime.strptime(v[:16], "%Y-%m-%d %H:%M")
                        except ValueError:
                            continue
                        if abs((tv - r["t"]).total_seconds()) <= 600 and (best is None or tv > best):
                            best = tv
    return (best + dt.timedelta(seconds=30)) if best else r["t"]


def build_scratch(r, root):
    trk = os.path.join(root, "tracker")
    os.makedirs(os.path.join(trk, "data"), exist_ok=True)
    os.makedirs(os.path.join(trk, "outputs"), exist_ok=True)
    os.makedirs(os.path.join(trk, "uploads"), exist_ok=True)
    for f in os.listdir(LIVE):
        if f.endswith(".py") and f != "server_runner.py":
            shutil.copy2(os.path.join(LIVE, f), os.path.join(trk, f))
    # the engine as it was on that evening: processor.py changed once in the window (S777 / D893, 10-Nov-2026 19:13 IST)
    r["code"] = "current"
    if r["t"] < CODE_CHANGE:
        shutil.copy2(os.path.join(LIVE, OLD_PROCESSOR), os.path.join(trk, "processor.py"))
        r["code"] = "pre-S777"
    for f in os.listdir(r["snap"]):
        shutil.copy2(os.path.join(r["snap"], f), os.path.join(trk, "data", f))
    for f in ("diagnosis_source_meta.json", "revenue_source_meta.json", ".secret_key", "New"):
        p = os.path.join(LIVE, "data", f)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(trk, "data", f))
    # the Call_Feed as the PC saw it after that run; the fetch itself OFF (no feed_url.txt)
    if r["next"] and os.path.exists(os.path.join(r["next"], "outbound_log.csv")):
        shutil.copy2(os.path.join(r["next"], "outbound_log.csv"), os.path.join(trk, "data", "outbound_log.csv"))
    for name in (r["cons"], r["fu"]):
        src = os.path.join(LIVE, "uploads", name)
        if not os.path.exists(src):
            return trk, "input missing: %s" % name
        shutil.copy2(src, os.path.join(trk, "uploads", name))
    return trk, None


def run_one(r, trk):
    cwd = os.getcwd()
    saved_path = list(sys.path)
    for m in list(sys.modules):
        if m in CLOCK_MODULES or m.startswith(tuple(x + "." for x in CLOCK_MODULES)):
            del sys.modules[m]
    sys.path.insert(0, trk)
    os.chdir(trk)
    buf = io.StringIO()
    try:
        old_out = sys.stdout
        sys.stdout = buf
        try:
            mods = []
            for name in CLOCK_MODULES:
                try:
                    mods.append(importlib.import_module(name))
                except Exception:
                    pass
            Clock(pin_instant(r)).install(mods)
            processor = sys.modules["processor"]
            audit, staff = processor.run_daily(os.path.join(trk, "uploads", r["cons"]), os.path.join(trk, "uploads", r["fu"]), today=None)
        finally:
            sys.stdout = old_out
    finally:
        os.chdir(cwd)
        sys.path[:] = saved_path
    return staff, buf.getvalue()


def compare_xlsx(a, b):
    import openpyxl
    wa = openpyxl.load_workbook(a, data_only=False)
    wb = openpyxl.load_workbook(b, data_only=False)
    notes = []
    if wa.sheetnames != wb.sheetnames:
        notes.append("sheets differ: %s vs %s" % (wa.sheetnames, wb.sheetnames))
    for s in wa.sheetnames:
        if s not in wb.sheetnames:
            continue
        xa, xb = wa[s], wb[s]
        if (xa.max_row, xa.max_column) != (xb.max_row, xb.max_column):
            notes.append("%s: size %dx%d vs %dx%d" % (s, xa.max_row, xa.max_column, xb.max_row, xb.max_column))
        diff = gen = 0
        rows = max(xa.max_row, xb.max_row); cols = max(xa.max_column, xb.max_column)
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                va, vb = xa.cell(i, j).value, xb.cell(i, j).value
                if va != vb:
                    if isinstance(va, str) and isinstance(vb, str) and "Generated:" in va and "Generated:" in vb \
                            and va.split("Generated:")[0] == vb.split("Generated:")[0]:
                        gen += 1
                    else:
                        diff += 1
        if diff:
            notes.append("%s: %d cell(s) differ" % (s, diff))
        if gen:
            notes.append("%s: Generated stamp only (%d)" % (s, gen))
    return notes


def compare_csv(a, b):
    """columns whose values differ, with the row count; the input-file-name column is expected (and named)."""
    def load(p):
        with open(p, encoding="utf-8", errors="replace", newline="") as fh:
            rd = csv.reader(fh)
            rows = list(rd)
        return rows
    ra, rb = load(a), load(b)
    if not ra or not rb:
        return ["empty file"] if (ra or rb) else []
    if ra[0] != rb[0]:
        return ["header differs"]
    if len(ra) != len(rb):
        return ["rows %d vs %d" % (len(ra) - 1, len(rb) - 1)]
    bad = {}
    for x, y in zip(ra[1:], rb[1:]):
        for k, (u, v) in enumerate(zip(x, y)):
            if u != v:
                bad[ra[0][k]] = bad.get(ra[0][k], 0) + 1
    return ["%s (%d)" % (k, v) for k, v in sorted(bad.items())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--report", default=os.path.join(LIVE, "logs", "REPLAY2_REPORT.txt"))
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    runs = pair(read_runs(), snapshots())
    print_table(runs)
    if not a.run:
        return 0
    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    rep = open(a.report, "a", encoding="utf-8")
    def say(s):
        print(s); rep.write(s + "\n"); rep.flush()
    say("REPLAY 2 (%s, on the box) -- %s IST -- %d run(s) logged since %s" % (VERSION, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(runs), SINCE))
    passed = failed = skipped = 0
    for i, r in enumerate(runs, 1):
        if a.only:
            lo, _, hi = a.only.partition("-")
            if not (int(lo) <= i <= int(hi or lo)):
                continue
        tag = "#%d %s day %s" % (i, r["t"], r["day"])
        if not r.get("last_of_day"):
            say("%s SKIP (an earlier run of the day; the inbox holds the day's last workbook)" % tag); skipped += 1; continue
        if not r["snap"] or not r["ref_xlsx"]:
            say("%s SKIP (snapshot %s, inbox workbook %s)" % (tag, "yes" if r["snap"] else "none", "yes" if r["ref_xlsx"] else "none")); skipped += 1; continue
        os.makedirs(SCRATCH, mode=0o700, exist_ok=True)
        root = tempfile.mkdtemp(prefix="s897_", dir=SCRATCH)
        try:
            trk, err = build_scratch(r, root)
            if err:
                say("%s SKIP (%s)" % (tag, err)); skipped += 1; continue
            try:
                staff, log = run_one(r, trk)
                notes = []
                if not staff or os.path.basename(staff) != r["wrote"]:
                    notes.append("workbook name %s vs %s" % (os.path.basename(staff or "") or "(none)", r["wrote"]))
                notes += ["xlsx " + n for n in compare_xlsx(staff, r["ref_xlsx"])]
            except Exception as e:
                say("%s FAIL run or compare raised: %s: %s" % (tag, type(e).__name__, str(e)[:160])); failed += 1; continue
            if r["next"]:
                for f in sorted(os.listdir(r["next"])):
                    if not f.endswith(".csv"):
                        continue
                    mine = os.path.join(trk, "data", f)
                    if not os.path.exists(mine):
                        notes.append("%s: not written" % f); continue
                    d = compare_csv(mine, os.path.join(r["next"], f))
                    if d:
                        notes.append("%s: %s" % (f, "; ".join(d)))
            else:
                notes.append("data: no later snapshot -- data files not compared")
            ok = not any(("differ" in n or "FAIL" in n or "rows " in n or "not written" in n or "header" in n) for n in notes)
            say("%s %s (code %s)%s" % (tag, "PASS" if ok else "FAIL", r.get("code"), ("  [" + " | ".join(notes) + "]") if notes else ""))
            passed += ok; failed += (not ok)
        finally:
            if not a.keep:
                shutil.rmtree(root, ignore_errors=True)
    say("RESULT: %d pass, %d fail, %d skipped of %d" % (passed, failed, skipped, len(runs)))
    if runs and not passed and not failed:
        say("NOTHING COMPARED: every run was skipped -- the inbox holds no workbook under the names the console log wrote, or no snapshot paired; not a proof")
    rep.close()
    if not a.keep:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
