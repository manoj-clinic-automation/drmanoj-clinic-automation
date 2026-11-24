#!/usr/bin/env python3
"""
call_log_compare.py -- S949 (the parent, S516, 24-Nov-2026): roadmap S510 F1a's proof -- the call log table = the Sheet.

Nightly 23:40 IST (cron # S949_CALL_LOG_COMPARE, its own flock, the ALL_OFF gate). Reads the server table call_log_raw
(/root/wa/calls.db, read-only) and the Call_Durations tab of the Clinic Callback Tracker (read-only, the hook's own
service-account key) and compares them row by row on the 14 fields:

  the window   = Sheet rows captured at or after the table's started_at (the hook's first write to the table)
  only sheet   = a window key the table lacks             (the table missed a call)
  only table   = a table key no Sheet row carries          (the Sheet missed a call)
  differ       = a key in both whose fields are not equal  (by field name, counted per field)
  duplicates   = a key twice in the window of the Sheet    (the Sheet doubled a row)
  in flight    = a key the table wrote in the last 10 minutes -- not judged tonight

EQUAL when only-sheet, only-table, differ and duplicates are all 0. The state file call_log_compare.state.json (0600)
carries last_run_iso, last_success_iso (EQUAL runs only), last_fail_iso (DIFFER or ERROR), the counts and
equal_runs_in_a_row (EQUAL runs that had at least one row). The health leg 'call log table = sheet' reads it: green after an
EQUAL night, red at once after a DIFFER or ERROR night. One retry after 60 s when the Sheet or the table cannot be read.

Counts only, everywhere: no key, no number, no name is ever printed or written (the keys carry patient numbers).
  --check     the state in one line           --selftest  offline, made-up rows
"""
import os
import sys
import json
import glob
import time
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _load_env():
    for path in ("/root/wa/.env", os.path.join(HERE, ".env")):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except OSError:
            pass


_load_env()                          # before the module reads CALLHOOK_DB, exactly as the hook does
import call_log_db as cldb          # noqa: E402

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
STATE = os.environ.get("CALL_LOG_COMPARE_STATE", "").strip() or os.path.join(HERE, "call_log_compare.state.json")
IN_FLIGHT_S = 600


def now_iso():
    return datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"


def norm(v):
    """One spelling for a value from either side: None -> '', 12.0 -> '12', whitespace trimmed."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    if s.endswith(".0") and s[:-2].lstrip("-").isdigit():
        s = s[:-2]
    return s


def compare(sheet_values, table_rows, started_at, now_ts=None):
    """Pure. sheet_values = the tab as a list of lists (row 1 the header); table_rows = dicts with the 14 fields and
    'written_at'. Returns the counts dict (no keys in it)."""
    now_ts = time.time() if now_ts is None else now_ts
    if not sheet_values:
        raise ValueError("the tab is empty")
    head = [str(h).strip().lower() for h in sheet_values[0]]
    missing = [h for h in cldb.HEADER if h not in head]
    if missing:
        raise ValueError("the tab lacks %d of the 14 columns" % len(missing))
    pos = {h: head.index(h) for h in cldb.HEADER}

    def cell(r, h):
        i = pos[h]
        return r[i] if i < len(r) else ""

    sheet_all, window, dup = {}, {}, 0
    for r in sheet_values[1:]:
        k = norm(cell(r, "client_ref_id"))
        if not k:
            continue
        rec = {h: norm(cell(r, h)) for h in cldb.HEADER}
        sheet_all[k] = rec                       # the LAST row of a key, as the hook's index keeps it
        cap = rec["captured_at_ist"]
        if cap and started_at and cap >= started_at:
            if k in window:
                dup += 1
            window[k] = rec
    table = {}
    in_flight = set()
    for t in table_rows:
        k = norm(t.get("client_ref_id"))
        table[k] = {h: norm(t.get(h)) for h in cldb.HEADER}
        w = t.get("written_at") or ""
        try:
            wt = datetime.datetime.fromisoformat(w).timestamp() if w else 0
        except ValueError:
            wt = 0
        if wt and now_ts - wt < IN_FLIGHT_S:
            in_flight.add(k)
    only_sheet = sum(1 for k in window if k not in table and k not in in_flight)
    only_table = sum(1 for k in table if k not in sheet_all and k not in in_flight)
    differ, fields = 0, {}
    for k, trow in table.items():
        if k in in_flight or k not in sheet_all:
            continue
        srow = sheet_all[k]
        bad = [h for h in cldb.HEADER if trow[h] != srow[h]]
        if bad:
            differ += 1
            for h in bad:
                fields[h] = fields.get(h, 0) + 1
    return {"sheet_window": len(window), "table_rows": len(table), "both": sum(1 for k in table if k in sheet_all),
            "only_sheet": only_sheet, "only_table": only_table, "differ": differ, "differ_fields": fields,
            "sheet_duplicates": dup, "in_flight": len(in_flight)}


def verdict_of(c):
    return "EQUAL" if (c["only_sheet"] == 0 and c["only_table"] == 0 and c["differ"] == 0
                       and c["sheet_duplicates"] == 0) else "DIFFER"


def read_state(path=STATE):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(d, path=STATE):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def record(verdict, counts, started, err="", path=STATE):
    prev = read_state(path)
    t = now_iso()
    st = {"last_run_iso": t, "last_success_iso": prev.get("last_success_iso", ""),
          "last_fail_iso": prev.get("last_fail_iso", ""), "verdict": verdict, "counts": counts or {},
          "started_at": started or prev.get("started_at", ""), "error": err,
          "equal_runs_in_a_row": int(prev.get("equal_runs_in_a_row", 0) or 0), "writer": "call_log_compare.py (S949)"}
    if started and prev.get("started_at") and started != prev.get("started_at"):
        st["equal_runs_in_a_row"] = 0               # a new table (a re-install): its nights count from zero
    if verdict == "EQUAL":
        st["last_success_iso"] = t
        if (counts or {}).get("sheet_window", 0) > 0:
            st["equal_runs_in_a_row"] += 1
    else:
        st["last_fail_iso"] = t
        st["equal_runs_in_a_row"] = 0
    write_state(st, path)
    return st


def line_of(st):
    c = st.get("counts") or {}
    if st.get("verdict") == "ERROR":
        return "COMPARE ERROR at %s: %s" % (st.get("last_run_iso", ""), st.get("error", ""))
    df = c.get("differ_fields") or {}
    return ("COMPARE %s at %s: sheet %d in window . table %d . both %d . only sheet %d . only table %d . differ %d%s"
            " . sheet duplicates %d . in flight %d . equal runs in a row %d (table since %s)"
            % (st.get("verdict", "?"), st.get("last_run_iso", ""), c.get("sheet_window", 0), c.get("table_rows", 0),
               c.get("both", 0), c.get("only_sheet", 0), c.get("only_table", 0), c.get("differ", 0),
               (" (" + ", ".join("%s %d" % kv for kv in sorted(df.items())) + ")") if df else "",
               c.get("sheet_duplicates", 0), c.get("in_flight", 0), st.get("equal_runs_in_a_row", 0),
               st.get("started_at", "")))


def _find_sa_key():
    k = os.environ.get("CALLHOOK_SA_KEY", "").strip() or os.environ.get("WA_SA_KEY", "").strip()
    if k and os.path.exists(k):
        return k
    for d in ("/root/wa", "/root/wa/keys", HERE, "/root"):
        for p in glob.glob(os.path.join(d, "*.json")):
            try:
                with open(p, encoding="utf-8") as f:
                    o = json.load(f)
                if o.get("type") == "service_account" and o.get("client_email"):
                    return p
            except Exception:           # noqa: BLE001
                continue
    return ""


def read_sheet():
    import gspread
    sid = (os.environ.get("CALLHOOK_SHEET_ID", "").strip() or os.environ.get("WA_SHEET_ID", "").strip()
           or "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0")
    tab = os.environ.get("CALLHOOK_TAB", "Call_Durations").strip() or "Call_Durations"
    key = _find_sa_key()
    if not key:
        raise RuntimeError("no service-account key")
    return gspread.service_account(filename=key).open_by_key(sid).worksheet(tab).get_all_values()


def read_table():
    if os.environ.get("CALLHOOK_DB", "").strip().lower() in ("off", "0", "no", "false", "none", "disabled"):
        raise RuntimeError("the table is off (CALLHOOK_DB=off)")
    con = cldb.connect(readonly=True)
    try:
        cols = ", ".join(cldb.HEADER)
        rows = [dict(r) for r in con.execute("SELECT %s, written_at FROM call_log_raw" % cols)]
        r = con.execute("SELECT v FROM meta WHERE k='started_at'").fetchone()
        return rows, (r[0] if r else "")
    finally:
        con.close()


def run():
    err = ""
    for attempt in (1, 2):
        try:
            sv = read_sheet()               # the Sheet FIRST: a call landing between the reads is then in flight
            rows, started = read_table()
            c = compare(sv, rows, started)
            st = record(verdict_of(c), c, started)
            print(line_of(st))
            return 0 if st["verdict"] == "EQUAL" else 1
        except Exception as e:          # noqa: BLE001
            err = "%s (%s)" % (type(e).__name__, str(e)[:60].replace("\n", " "))
            if attempt == 1:
                time.sleep(int(os.environ.get("CALL_LOG_COMPARE_RETRY_S", "60")))
    st = record("ERROR", {}, "", err)
    print(line_of(st))
    return 2


def _selftest():
    import tempfile
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL: %s" % name)

    num = "5" + "0" * 8 + "3"
    H = list(cldb.HEADER)
    start = "2026-11-24T21:00:00+05:30"

    def srow(key, cap, **kw):
        d = {h: "" for h in H}
        d.update({"client_ref_id": key, "captured_at_ist": cap, "category": "incoming", "total_duration": "12",
                  "phone10": num})
        d.update(kw)
        return [d[h] for h in H]

    def trow(key, cap, **kw):
        d = {h: "" for h in H}
        d.update({"client_ref_id": key, "captured_at_ist": cap, "category": "incoming", "total_duration": 12,
                  "phone10": num, "written_at": "2026-11-24T21:20:00+05:30"})
        d.update(kw)
        return d

    late = datetime.datetime(2026, 11, 25, 0, 0, tzinfo=IST).timestamp()
    sv = [H, srow("IN-old", "2026-11-23T10:00:00+05:30"), srow("IN-a", "2026-11-24T21:05:00+05:30"),
          srow("IN-b", "2026-11-24T21:10:00+05:30")]
    tr = [trow("IN-a", "2026-11-24T21:05:00+05:30"), trow("IN-b", "2026-11-24T21:10:00+05:30")]
    c = compare(sv, tr, start, late)
    check("equal: the window excludes the old row", c["sheet_window"] == 2 and verdict_of(c) == "EQUAL")
    check("a number 12 equals the Sheet's '12'", c["differ"] == 0)
    c = compare(sv, tr[:1], start, late)
    check("only sheet counted", c["only_sheet"] == 1 and verdict_of(c) == "DIFFER")
    c = compare(sv, tr + [trow("IN-c", "2026-11-24T22:00:00+05:30")], start, late)
    check("only table counted", c["only_table"] == 1 and verdict_of(c) == "DIFFER")
    c = compare(sv, [tr[0], trow("IN-b", "2026-11-24T21:10:00+05:30", status="missed")], start, late)
    check("a differing field counted by name", c["differ"] == 1 and c["differ_fields"] == {"status": 1})
    c = compare(sv + [srow("IN-b", "2026-11-24T21:11:00+05:30")], tr, start, late)
    check("a doubled Sheet row is a duplicate", c["sheet_duplicates"] == 1 and verdict_of(c) == "DIFFER")
    nowish = datetime.datetime(2026, 11, 24, 21, 35, tzinfo=IST).timestamp()
    c = compare(sv, tr + [trow("IN-d", "2026-11-24T21:31:00+05:30", written_at="2026-11-24T21:31:00+05:30")], start, nowish)
    check("a row written 4 minutes ago is in flight, not judged", c["in_flight"] == 1 and c["only_table"] == 0)
    try:
        compare([H[:5]], tr, start, late)
        check("a tab without the columns refused", False)
    except ValueError:
        check("a tab without the columns refused", True)
    c = compare([H], [], start, late)
    check("nothing yet: equal with 0 rows", verdict_of(c) == "EQUAL" and c["sheet_window"] == 0)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "s.json")
        st = record("EQUAL", {"sheet_window": 0}, start, path=p)
        check("an empty EQUAL is a success but not a counted run", st["last_success_iso"] and st["equal_runs_in_a_row"] == 0)
        st = record("EQUAL", {"sheet_window": 3}, start, path=p)
        st = record("EQUAL", {"sheet_window": 4}, start, path=p)
        check("equal runs counted", st["equal_runs_in_a_row"] == 2)
        good = st["last_success_iso"]
        st = record("DIFFER", {"sheet_window": 4, "only_sheet": 1}, start, path=p)
        check("a DIFFER keeps the last success, sets the fail, resets the run",
              st["last_success_iso"] == good and st["last_fail_iso"] and st["equal_runs_in_a_row"] == 0)
        check("the state file is 0600", (os.stat(p).st_mode & 0o777) == 0o600)
        ln = line_of(st)
        check("the line carries no key and no number", "IN-" not in ln and num not in ln)
        st = record("EQUAL", {"sheet_window": 2}, "2026-12-01T21:00:00+05:30", path=p)
        check("a new started_at (a re-install) restarts the count at 1", st["equal_runs_in_a_row"] == 1)
        st = record("ERROR", {}, "", "OperationalError (x)", path=p)
        check("an ERROR is a fail", st["verdict"] == "ERROR" and line_of(st).startswith("COMPARE ERROR"))
        # end to end against a real table file (the reader's SQL)
        cldb.DB_PATH = os.path.join(td, "calls.db")
        cldb.init()
        rec = {h: "" for h in H}
        rec.update({"client_ref_id": "IN-z", "captured_at_ist": "2099-01-01T00:00:00+05:30", "phone10": num})
        cldb.upsert(rec)
        rows, started = read_table()
        check("read_table: the row and started_at", len(rows) == 1 and "written_at" in rows[0] and started)
    check("norm", norm(12.0) == "12" and norm(None) == "" and norm(" a ") == "a" and norm("30.0") == "30")
    print("selftest: %d/%d passed" % (passed, passed + failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if "--check" in sys.argv:
        s = read_state()
        print(line_of(s) if s else "COMPARE: no run recorded yet")
        sys.exit(0)
    sys.exit(run())
