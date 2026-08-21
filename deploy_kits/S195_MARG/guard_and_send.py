#!/usr/bin/env python3
"""guard_and_send.py — validate a Marg REPORT_1.XLS BEFORE it is sent (S195).

The quick-win guard for the Marg daily-sale automation. It runs the SAME
read_report() the clinic server uses (marg_report.py, sitting next to this
file), so its judgment is identical to the server's. It exits 0 ONLY when the
file is a single-day "Detail" Bill-Wise Sales export that:

  * has the expected 9-column layout (not the CASH-less Summary-1),
  * ENDS WITH "GRAND TOTAL :" — i.e. is not a silent truncated partial,
  * passes its own per-day and grand-total arithmetic, and
  * carries the business date we expected (default: today).

Anything else exits non-zero and writes a plain-text alert. A truncated or
stale REPORT_1.XLS is therefore NEVER sent silently — the exact failure this
project keeps paying for.

It does NOT send anything itself. GUARD_AND_SEND.bat calls SEND_TO_CLINIC.bat
only when this exits 0. The maker/checker split (D325) is untouched: the sender
still only STAGES the report for review; Dr Manoj alone applies it.

On GREEN it can also drop a copy into an archive folder NAMED BY THE BUSINESS
DATE the report is for (REPORT_2026-08-19.XLS), so the Sent folder is filed by
the day it covers, not the moment it was saved. Incomplete/refused files are
never archived.

Usage:
  guard_and_send.py <REPORT_1.XLS> [--expect today|yesterday|YYYY-MM-DD|any]
                                   [--alert <file>] [--allow-range]
                                   [--archive-dir <dir>] [--max-age-days N] [--json]

Exit codes:
  0  GREEN   — validated, safe to send
  2  REFUSED — failed a check (reason printed + appended to the alert file)
  3  ERROR   — could not read the file at all (missing xlrd, not an .xls, …)
"""
import argparse
import datetime
import json
import os
import shutil
import sys

# read_report lives in marg_report.py, shipped alongside this file (the exact
# same parser the server ingests with). Import it from this script's folder.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from marg_report import read_report, MargReportError
except Exception as ex:                                            # noqa: BLE001
    sys.stderr.write("ERROR: cannot import marg_report.py next to this script: %s\n" % ex)
    sys.exit(3)

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))   # Asia/Kolkata


def _today_ist():
    return datetime.datetime.now(IST).date()


def resolve_expected(expect):
    """'today' | 'yesterday' | 'YYYY-MM-DD' | 'any' -> an ISO date or None."""
    if not expect or expect.lower() == "any":
        return None
    e = expect.strip().lower()
    if e == "today":
        return _today_ist().isoformat()
    if e == "yesterday":
        return (_today_ist() - datetime.timedelta(days=1)).isoformat()
    try:
        return datetime.date.fromisoformat(expect.strip()).isoformat()
    except ValueError:
        raise SystemExit("bad --expect value %r (use today|yesterday|YYYY-MM-DD|any)" % expect)


def write_alert(alert_path, reason, path):
    stamp = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    block = (
        "%s  REFUSED to send: %s\n"
        "   file: %s\n"
        "   Report NAHI bheji gayi — file poori/ theek nahi hai. Marg mein\n"
        "   BILL WISE SALES report (With Item Deta. = Yes) dobara chalayen,\n"
        "   sahi date chunein, phir dobara bhejein. (Dr. Manoj ko batayen.)\n"
        "   ------------------------------------------------------------\n"
        % (stamp, reason, path)
    )
    try:
        with open(alert_path, "a", encoding="utf-8") as fh:
            fh.write(block)
    except Exception as ex:                                        # noqa: BLE001
        sys.stderr.write("(could not write alert file %s: %s)\n" % (alert_path, ex))


def refuse(reason, path, alert_path, as_json):
    write_alert(alert_path, reason, path)
    if as_json:
        print(json.dumps({"ok": False, "verdict": "REFUSED",
                          "reason": reason, "path": os.path.basename(path)}))
    else:
        sys.stderr.write("REFUSED: %s\n" % reason)
        sys.stderr.write("  -> NOT sending. Alert written to %s\n" % alert_path)
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description="Guard a Marg REPORT_1.XLS before sending.")
    ap.add_argument("xls", help="path to the REPORT_1.XLS to validate")
    ap.add_argument("--expect", default="today",
                    help="business date the file must carry: today | yesterday | "
                         "YYYY-MM-DD | any  (default: today)")
    ap.add_argument("--alert", default=None,
                    help="alert log file to append refusals to "
                         "(default: guard_alerts.txt next to the report)")
    ap.add_argument("--allow-range", action="store_true",
                    help="permit a multi-day range export (default: single-day only)")
    ap.add_argument("--max-age-days", type=int, default=3,
                    help="in --expect any mode, refuse a single-day file whose business "
                         "date is older than this many days (0 = no freshness check; "
                         "ignored when --expect pins an exact date). Default: 3")
    ap.add_argument("--archive-dir", default=None,
                    help="on GREEN only, save a copy here named by the report's own "
                         "business date/period, e.g. REPORT_2026-08-19.XLS "
                         "(single-day) or REPORT_2026-08-01_to_2026-08-15.XLS (range). "
                         "Incomplete/refused files are never archived.")
    ap.add_argument("--json", action="store_true", help="emit a one-line JSON verdict")
    a = ap.parse_args(argv)

    path = a.xls
    alert_path = a.alert or os.path.join(os.path.dirname(os.path.abspath(path)) or ".",
                                         "guard_alerts.txt")

    if not os.path.exists(path):
        sys.stderr.write("ERROR: file not found: %s\n" % path)
        return 3

    try:
        expected = resolve_expected(a.expect)
    except SystemExit as ex:
        sys.stderr.write(str(ex) + "\n")
        return 3

    # --- parse with the server's own reader ---------------------------------
    try:
        rep = read_report(path)
    except MargReportError as ex:
        # wrong layout, Summary-1 (no CASH), unreadable .xls structure, etc.
        return refuse(str(ex), path, alert_path, a.json)
    except Exception as ex:                                        # noqa: BLE001
        sys.stderr.write("ERROR: could not read %s: %s\n" % (path, ex))
        return 3

    # --- truncation / arithmetic (read_report already computed these) -------
    if not rep["ok"]:
        return refuse("file failed its own checks — " + " | ".join(rep["errors"]),
                      path, alert_path, a.json)

    # --- variant --------------------------------------------------------------
    if rep["variant"] != "single-day" and not a.allow_range:
        return refuse("expected a single-day Detail export but this is a %s "
                      "(%s). Use --allow-range only for a deliberate catch-up."
                      % (rep["variant"], rep["period"]), path, alert_path, a.json)

    # --- business date --------------------------------------------------------
    dates = [d["date"] for d in rep["days"]]
    file_date = dates[0] if dates else None
    if expected is not None:
        if rep["variant"] == "single-day":
            if file_date != expected:
                return refuse("business date is %s but we expected %s — this looks "
                              "like a stale or wrong-day REPORT_1.XLS."
                              % (file_date, expected), path, alert_path, a.json)
        else:  # range with --allow-range: expected date must be inside the span
            if expected not in dates:
                return refuse("expected date %s is not among the days in this range "
                              "export (%s)" % (expected, rep["period"]),
                              path, alert_path, a.json)
    elif rep["variant"] == "single-day" and a.max_age_days > 0 and file_date:
        # --expect any: no exact-date pin, so guard against a stale leftover file.
        age = (_today_ist() - datetime.date.fromisoformat(file_date)).days
        if age > a.max_age_days:
            return refuse("business date %s is %d day(s) old (limit %d) — this looks "
                          "like a stale leftover REPORT_1.XLS. Pin the date with "
                          "--expect YYYY-MM-DD for a deliberate catch-up."
                          % (file_date, age, a.max_age_days), path, alert_path, a.json)

    # --- GREEN ---------------------------------------------------------------
    tot = {"bills": 0, "net": 0, "cash": 0}
    for d in rep["days"]:
        c = d["computed"]
        tot["bills"] += len(d["bills"])
        tot["net"] += c["net"]
        tot["cash"] += c["cash"]
    noncash = tot["net"] - tot["cash"]

    # --- archive a copy named by the business date / period it is FOR --------
    archived = None
    if a.archive_dir:
        p0, p1 = rep["period"]
        if rep["variant"] == "single-day" or (p1 in (None, p0)):
            arch_name = "REPORT_%s.XLS" % (file_date or p0)
        else:
            arch_name = "REPORT_%s_to_%s.XLS" % (p0, p1)
        try:
            os.makedirs(a.archive_dir, exist_ok=True)
            archived = os.path.join(a.archive_dir, arch_name)
            shutil.copy2(path, archived)           # latest export for a date wins
        except Exception as ex:                                    # noqa: BLE001
            # archiving is a convenience, never a reason to block a good file
            sys.stderr.write("(warning: could not archive to %s: %s)\n"
                             % (a.archive_dir, ex))
            archived = None

    summary = {
        "ok": True, "verdict": "GREEN", "path": os.path.basename(path),
        "date": file_date, "variant": rep["variant"], "bills": tot["bills"],
        "net": round(tot["net"] / 100.0, 2), "cash": round(tot["cash"] / 100.0, 2),
        "noncash": round(noncash / 100.0, 2),
        "archived_as": (os.path.basename(archived) if archived else None),
        "warnings": rep["warnings"],
    }
    if a.json:
        print(json.dumps(summary))
    else:
        print("GREEN — safe to send.")
        print("  %s  |  %d bill(s)  |  NET %.2f  CASH %.2f  NON-CASH %.2f"
              % (file_date, tot["bills"], tot["net"] / 100.0,
                 tot["cash"] / 100.0, noncash / 100.0))
        if archived:
            print("  archived as: %s" % os.path.basename(archived))
        for w in rep["warnings"]:
            print("  note: %s" % w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
