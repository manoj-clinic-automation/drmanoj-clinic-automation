#!/usr/bin/env python3
"""walk_s540.py -- kit S540 (session 311). READ-ONLY on the real machine: everything happens in a temporary folder with
made-up files (no person, no number).    python3 -B walk_s540.py <folder holding docterz_pickup.py> [--expect-red]
Replays 10 -> 12 Oct: a one-month follow-up log at 08:48 and a one-day log at 20:40 on Saturday; Saturday's list was made
with the one-day log; on Monday the pass must re-make Saturday's (Monday's) list ONCE with the one-month log, and a
second pass must do nothing. Also: a weekday run pairs with the reaching log; past the call day nothing is re-made."""
import datetime as dt
import importlib.util
import json
import os
import shutil
import sys
import tempfile

FAILS, RUN = [], [0]


def ok(c, what):
    RUN[0] += 1
    if not c:
        FAILS.append(what)


def load(folder):
    spec = importlib.util.spec_from_file_location("dp_walk", os.path.join(folder, "docterz_pickup.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def log_file(path, dues):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("Appointment ID,Mobile No,Patient Name,Followup Text,Followup Date,Doctor Name,Comments\n")
        for i, d in enumerate(dues):
            fh.write("A%05d,X,Patient %d,Dr,%s,Dr,\n" % (i, i, dt.date.fromisoformat(d).strftime("%d-%m-%Y")))


def setup(root):
    tr, dl = os.path.join(root, "tracker"), os.path.join(root, "Downloads")
    ar = os.path.join(dl, "DocterzArchive")
    for d in (tr, dl, ar, os.path.join(tr, "uploads"), os.path.join(tr, "outputs"), os.path.join(ar, "FOLLOWUP_LOG")):
        os.makedirs(d, exist_ok=True)
    open(os.path.join(tr, "processor.py"), "w").write("# stand-in\n")
    month = os.path.join(ar, "FOLLOWUP_LOG", "month.csv")
    oneday = os.path.join(ar, "FOLLOWUP_LOG", "oneday.csv")
    log_file(month, ["2026-10-10"] * 3 + ["2026-10-12"] * 11 + ["2026-10-20"] * 4 + ["2026-11-09"])
    log_file(oneday, ["2026-10-11"])
    base = dt.datetime(2026, 10, 10, 8, 48).timestamp()
    os.utime(month, (base, base))
    os.utime(oneday, (base + 12 * 3600, base + 12 * 3600))
    cons = os.path.join(tr, "uploads", "consultation_report_2026-10-10.csv")
    open(cons, "w").write("Consultation Date,Patient UID\n")
    st = {"seen": {"m1": {"type": "FOLLOWUP_LOG", "archived": month, "mtime": base, "seen_at": "2026-10-10 08:55:01"},
                   "m2": {"type": "FOLLOWUP_LOG", "archived": oneday, "mtime": base + 12 * 3600, "seen_at": "2026-10-10 21:00:05"}},
          "days": {"2026-10-10": {"digest": "x", "input": cons, "processed_at": "2026-10-10 21:00:42", "how": "auto"}},
          "last_followup": None}
    json.dump(st, open(os.path.join(ar, "_pickup_state.json"), "w"))
    return tr, dl, ar, month, oneday


def one_pass(M, tr, dl, ar, today, calls, ups):
    def runner(c, f):
        calls.append((os.path.basename(c), open(f).read().count("\n") - 1))
        out = os.path.join(tr, "outputs", "Staff_Action_Today_x.xlsx")
        open(out, "w").write("x")
        return None, out, []
    p = M.Pass(tr, dl, ar, today=today, runner=runner, vps_upload=lambda s: (ups.append(s) or (True, "stub")),
               patient_push=lambda: (True, ["stub"]))
    p.write_tenders = lambda st: "skipped in the walk"
    p.run()
    return p, json.load(open(os.path.join(ar, "_pickup_state.json")))


def main(argv):
    M = load(argv[1])
    root = tempfile.mkdtemp(prefix="walk540_")
    try:
        tr, dl, ar, month, oneday = setup(root)
        calls, ups = [], []
        p, st = one_pass(M, tr, dl, ar, dt.date(2026, 10, 12), calls, ups)
        ok(len(calls) == 1, "W1 Monday: Saturday's list is re-made once (runs: %d)" % len(calls))
        ok(calls and calls[0][1] == 19, "W2 ...with the one-month log (19 rows), not the one-day log (got %s)" % calls)
        ok(len(ups) == 1, "W3 ...and the workbook goes to the VPS")
        ok(st["days"]["2026-10-10"].get("fu_reach") == "2026-11-09", "W4 the day remembers the log's reach")
        p2, st2 = one_pass(M, tr, dl, ar, dt.date(2026, 10, 12), calls, ups)
        ok(len(calls) == 1, "W5 a second pass does nothing (runs: %d)" % len(calls))
        tr2, dl2, ar2, *_ = setup(os.path.join(root, "b"))
        c2, u2 = [], []
        one_pass(M, tr2, dl2, ar2, dt.date(2026, 10, 13), c2, u2)
        ok(not c2, "W6 past the call day (Tuesday) nothing is re-made")
        if hasattr(M, "next_call_day"):
            ok(M.next_call_day("2026-10-10") == "2026-10-12" and M.next_call_day("2026-10-09") == "2026-10-10",
               "W7 the call day skips Sunday only")
            pk = M.Pass(tr2, dl2, ar2, today=dt.date(2026, 10, 12))
            stx = json.load(open(os.path.join(ar2, "_pickup_state.json")))
            fu, reach, why = pk.pick_followup(stx, "2026-10-10")
            ok(os.path.basename(fu) == "month.csv" and reach == "2026-11-09", "W8 pick_followup chooses the reaching log")
            fu2, _r, _w = pk.pick_followup(stx, "2026-10-09")
            ok(os.path.basename(fu2) == "oneday.csv", "W9 when the newest log reaches the call day, the newest wins")
        else:
            ok(False, "W7 next_call_day exists")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if "--expect-red" in argv:
        print(("WALK OK -- the negative control is RED as it must be (%d fail, e.g. %s)" % (len(FAILS), FAILS[0])) if FAILS
              else "WALK RED -- the old file passed: the walk proves nothing")
        return 0 if FAILS else 1
    for f in FAILS:
        print("FAIL", f)
    if not FAILS:
        print("WALK OK -- %d checks green" % RUN[0])
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
