#!/usr/bin/env python3
"""walk_s892.py -- kit S892 (the parent, S489). READ-ONLY on the real machine: everything happens in a temporary folder with
made-up files (no person, no number).    python3 -B walk_s892.py <folder holding docterz_pickup.py> [--expect-red]
              [--processor <the tracker's processor.py, read only: its two parsers are run on the made-up files>]
Replays 19-Nov-2026: the last consultation day the pickup holds is Sat 14-Nov (he was away 16-18 Nov); a follow-up log due
19-Nov onwards was filed at 09:10. The new pass must make 19-Nov's call list ONCE from that log with a header-only consultation
file named for 18-Nov, send it to the VPS, and a second pass must do nothing."""
import datetime as dt
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time

FAILS, RUN = [], [0]


def ok(c, what):
    RUN[0] += 1
    if not c:
        FAILS.append(what)


def load(folder, name="dp_walk"):
    spec = importlib.util.spec_from_file_location(name, os.path.join(folder, "docterz_pickup.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def log_file(path, dues, mtime):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("Appointment ID,Mobile No,Patient Name,Followup Text,Followup Date,Doctor Name,Comments\n")
        for i, d in enumerate(dues):
            fh.write("A%05d,X,Patient %d,Dr,%s,Dr,\n" % (i, i, dt.date.fromisoformat(d).strftime("%d-%m-%Y")))
    os.utime(path, (mtime, mtime))


def setup(root, last_day="2026-11-14", dues=None, name="log19.csv"):
    tr, dl = os.path.join(root, "tracker"), os.path.join(root, "Downloads")
    ar = os.path.join(dl, "DocterzArchive")
    for d in (tr, dl, ar, os.path.join(tr, "uploads"), os.path.join(tr, "outputs"), os.path.join(ar, "FOLLOWUP_LOG")):
        os.makedirs(d, exist_ok=True)
    open(os.path.join(tr, "processor.py"), "w").write("# stand-in\n")
    base = dt.datetime(2026, 11, 19, 9, 2).timestamp()
    lg = os.path.join(ar, "FOLLOWUP_LOG", name)
    log_file(lg, dues or (["2026-11-19"] * 18 + ["2026-11-20"] * 9 + ["2026-11-21"] * 15 + ["2026-12-14"] * 2), base)
    cons = os.path.join(tr, "uploads", "consultation_report_%s.csv" % last_day)
    open(cons, "w").write("Consultation Date,Patient UID\n")
    st = {"seen": {"m19": {"type": "FOLLOWUP_LOG", "archived": lg, "mtime": base, "seen_at": "2026-11-19 09:10:02"}},
          "days": {last_day: {"digest": "x", "input": cons, "processed_at": "2026-11-14 21:05:06", "how": "auto"}},
          "last_followup": None}
    json.dump(st, open(os.path.join(ar, "_pickup_state.json"), "w"))
    return tr, dl, ar, lg


def one_pass(M, tr, dl, ar, today, calls, ups):
    def runner(c, f):
        calls.append((os.path.basename(c), open(c, encoding="utf-8-sig").read(), open(f).read().count("\n") - 1,
                      os.path.basename(f)))
        out = os.path.join(tr, "outputs", "Staff_Action_Today_x.xlsx")
        open(out, "w").write("x")
        return None, out, []
    p = M.Pass(tr, dl, ar, today=today, runner=runner, vps_upload=lambda s: (ups.append(s) or (True, "stub")),
               patient_push=lambda: (True, ["stub"]))
    p.write_tenders = lambda st: "skipped in the walk"
    p.run()
    return p, json.load(open(os.path.join(ar, "_pickup_state.json")))


def main(argv):
    folder = argv[1]
    M = load(folder)
    proc = argv[argv.index("--processor") + 1] if "--processor" in argv else None
    root = tempfile.mkdtemp(prefix="walk892_")
    try:
        # A: 19-Nov, last consultation day 14-Nov, a log due 19-Nov onwards
        tr, dl, ar, lg = setup(os.path.join(root, "a"))
        calls, ups = [], []
        p, st = one_pass(M, tr, dl, ar, dt.date(2026, 11, 19), calls, ups)
        ok(len(calls) == 1, "A1 the 19-Nov call list is made once from the follow-up log alone (runs: %d)" % len(calls))
        ok(calls and calls[0][0].startswith("consultation_report_2026-11-18__fu_alone_"),
           "A2 ...with a consultation file named for 18-Nov, the day before the call day (got %s)" % (calls[0][0] if calls else None))
        ok(calls and calls[0][1].strip().count("\n") == 0 and "Patient UID" in calls[0][1],
           "A3 ...that file is a header line only: no visit invented")
        ok(calls and calls[0][2] == 44, "A4 ...with the whole log (44 rows) handed to the tracker")
        ok(len(ups) == 1, "A5 ...and the workbook goes to the VPS (latest=True)")
        ok(st.get("fu_alone", {}).get("2026-11-19"), "A6 the state remembers the call day and the log it was made from")
        ok("2026-11-18" not in st["days"], "A7 no consultation day is recorded for 18-Nov (only the call list was made)")
        logtxt = open(os.path.join(ar, "_pickup_log.txt"), encoding="utf-8").read()
        ok("S892: no consultation report made the call list for 2026-11-19" in logtxt, "A8 the pickup log says what it did")
        p2, st2 = one_pass(M, tr, dl, ar, dt.date(2026, 11, 19), calls, ups)
        ok(len(calls) == 1, "A9 a second pass does nothing (runs: %d)" % len(calls))
        # a newer log for the same call day (reception re-exports) re-makes it once
        lg2 = os.path.join(ar, "FOLLOWUP_LOG", "log19b.csv")
        log_file(lg2, ["2026-11-19"] * 20 + ["2026-11-20"] * 9, dt.datetime(2026, 11, 19, 11, 0).timestamp())
        st2["seen"]["m19b"] = {"type": "FOLLOWUP_LOG", "archived": lg2, "mtime": os.path.getmtime(lg2), "seen_at": "x"}
        json.dump(st2, open(os.path.join(ar, "_pickup_state.json"), "w"))
        one_pass(M, tr, dl, ar, dt.date(2026, 11, 19), calls, ups)
        ok(len(calls) == 2 and calls[-1][2] == 29, "A10 a newer log for the same day re-makes the list once, from the newer log")
        one_pass(M, tr, dl, ar, dt.date(2026, 11, 19), calls, ups)
        ok(len(calls) == 2, "A11 ...and then rests")
        # B: a consultation day already owns the call day (last day 18-Nov -> call day 19-Nov): nothing
        trb, dlb, arb, lgb = setup(os.path.join(root, "b"), last_day="2026-11-18")
        stb = json.load(open(os.path.join(arb, "_pickup_state.json")))       # that day was run with this very log (S540's record)
        stb["days"]["2026-11-18"].update(fu_md5=M.md5_of(lgb), fu_reach="2026-12-14")
        json.dump(stb, open(os.path.join(arb, "_pickup_state.json"), "w"))
        cb, ub = [], []
        one_pass(M, trb, dlb, arb, dt.date(2026, 11, 19), cb, ub)
        ok(not cb, "B1 when a consultation day already made 19-Nov's list, the log alone does nothing (runs: %d)" % len(cb))
        # C: Sunday skipped -- a Saturday-evening log whose first due day from Sunday on is Monday
        trc, dlc, arc, _ = setup(os.path.join(root, "c"), dues=["2026-11-22"] * 2 + ["2026-11-23"] * 7)
        cc, uc = [], []
        one_pass(M, trc, dlc, arc, dt.date(2026, 11, 22), cc, uc)
        ok(len(cc) == 1 and cc[0][0].startswith("consultation_report_2026-11-21__fu_alone_"),
           "C1 Sunday is skipped: the list is for Monday 23-Nov, the file named for Saturday 21-Nov so Sunday's dues load (got %s)"
           % (cc[0][0] if cc else None))
        # D: an evening export on a day he was away -- due from tomorrow
        trd, dld, ard, _ = setup(os.path.join(root, "d"), dues=["2026-11-20"] * 9 + ["2026-11-21"] * 3)
        cd, ud = [], []
        one_pass(M, trd, dld, ard, dt.date(2026, 11, 19), cd, ud)
        ok(len(cd) == 1 and cd[0][0].startswith("consultation_report_2026-11-19__fu_alone_"),
           "D1 an evening log (due from tomorrow) makes tomorrow's list, file named for today")
        # E: a stale log whose dues are all in the past: nothing
        tre, dle, are, _ = setup(os.path.join(root, "e"), dues=["2026-11-10"] * 4)
        ce, ue = [], []
        one_pass(M, tre, dle, are, dt.date(2026, 11, 19), ce, ue)
        ok(not ce, "E1 a log with nothing due from today on makes nothing")
        # F: no follow-up log at all: nothing
        trf, dlf, arf, lgf = setup(os.path.join(root, "f"))
        stf = json.load(open(os.path.join(arf, "_pickup_state.json")))
        stf["seen"] = {}
        json.dump(stf, open(os.path.join(arf, "_pickup_state.json"), "w"))
        cf, uf = [], []
        one_pass(M, trf, dlf, arf, dt.date(2026, 11, 19), cf, uf)
        ok(not cf, "F1 with no follow-up log the pass makes nothing")
        # G: a consultation report arriving in the same pass runs as before and the log-alone path stands aside
        trg, dlg, arg, _ = setup(os.path.join(root, "g"))
        rep = os.path.join(dlg, "consultation_report_2026-11-19.csv")
        with open(rep, "w", encoding="utf-8", newline="") as fh:
            fh.write("Sr No,Consultation Date,Patient UID,Patient Name,Mobile,Bill Amount,Amount collected\n")
            fh.write("1,19-11-2026 10:05 AM,ABCDEFGH1,Patient A,X,600,600\n")
        old = time.time() - 900
        os.utime(rep, (old, old))
        cg, ug = [], []
        one_pass(M, trg, dlg, arg, dt.date(2026, 11, 19), cg, ug)
        ok(len(cg) == 1 and "fu_alone" not in cg[0][0], "G1 a consultation report runs as before; the log-alone path stands aside (runs: %s)"
           % [c[0] for c in cg])
        # I: a consultation day's list stands until its day -- a later-day list never replaces it early (cold review MUST)
        tri, dli, ari, lgi = setup(os.path.join(root, "i"), last_day="2026-11-19", dues=["2026-11-21"] * 6 + ["2026-11-23"] * 2)
        sti = json.load(open(os.path.join(ari, "_pickup_state.json")))
        sti["days"]["2026-11-19"].update(fu_md5=M.md5_of(lgi), fu_reach="2026-11-23")
        json.dump(sti, open(os.path.join(ari, "_pickup_state.json"), "w"))
        ci, ui = [], []
        one_pass(M, tri, dli, ari, dt.date(2026, 11, 19), ci, ui)
        one_pass(M, tri, dli, ari, dt.date(2026, 11, 20), ci, ui)
        ok(not ci, "I1 the 20-Nov list made from 19-Nov's report is not replaced on the 19th or the 20th (runs: %d)" % len(ci))
        one_pass(M, tri, dli, ari, dt.date(2026, 11, 21), ci, ui)
        ok(len(ci) == 1 and ci[0][0].startswith("consultation_report_2026-11-20__fu_alone_"),
           "I2 on the 21st, with no newer report, the log makes the 21-Nov list (got %s)" % [c[0] for c in ci])
        # R: the emergency refresh re-makes the log-alone list, not the older consultation day's
        trr, dlr, arr, _ = setup(os.path.join(root, "r"))
        cr, ur = [], []
        one_pass(M, trr, dlr, arr, dt.date(2026, 11, 19), cr, ur)

        def rrun(c, f):
            cr.append((os.path.basename(c), "", 0, ""))
            out = os.path.join(trr, "outputs", "Staff_Action_Today_y.xlsx")
            open(out, "w").write("y")
            return None, out, []
        pr = M.Pass(trr, dlr, arr, today=dt.date(2026, 11, 19), runner=rrun,
                    vps_upload=lambda s_: (True, "stub"), patient_push=lambda: (True, ["stub"]))
        pushed = []
        rc = pr.refresh_latest(sheet_push=lambda f: (pushed.append(f) or (True, ["DONE stub"])))
        ok(rc == 0 and len(cr) == 2 and cr[-1][0].startswith("consultation_report_2026-11-18__fu_alone_") and pushed,
           "R1 the refresh re-makes 19-Nov's list from the log alone and pushes it (rc %s, runs %s)" % (rc, [c[0] for c in cr]))
        # H: the processor's own parsers on the made-up files (read only)
        if proc:
            import pandas  # noqa: F401
            sys.path.insert(0, os.path.dirname(proc))
            spec = importlib.util.spec_from_file_location("proc_walk", proc)
            P = importlib.util.module_from_spec(spec)
            cwd = os.getcwd()
            os.chdir(os.path.join(root, "a", "tracker"))
            try:
                spec.loader.exec_module(P)
            finally:
                os.chdir(cwd)
            hf = os.path.join(root, "consultation_report_2026-11-18__fu_alone_20261119-095500.csv")
            open(hf, "w", encoding="utf-8-sig").write("Sr No,Consultation Date,Patient UID,Patient Name,Mobile\n")
            df, d = P.parse_consultation_report(hf)
            ok(len(df) == 0 and d == "2026-11-18", "H1 processor reads the header-only file as no visits on 18-Nov (got %d, %s)" % (len(df), d))
            fu, _ = P.parse_followup_log(lg, anchor_date=P.parse_date(d))
            ok(len(fu) == 18, "H2 processor loads the 18 due on the call day 19-Nov from the log (got %d)" % len(fu))
            lgs = os.path.join(root, "sun.csv")
            log_file(lgs, ["2026-11-22"] * 2 + ["2026-11-23"] * 7, time.time())
            fus, _ = P.parse_followup_log(lgs, anchor_date=P.parse_date("2026-11-21"))
            ok(len(fus) == 9, "H3 a Monday list read from Saturday keeps Sunday's 2 dues: 9 of 9 (got %d)" % len(fus))
        if hasattr(M, "next_call_day"):
            ok(M.next_call_day("2026-11-14") == "2026-11-16", "Z1 the S540 call-day rule is unchanged")
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
