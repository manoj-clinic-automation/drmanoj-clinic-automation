#!/usr/bin/env python3
"""
repair_call_durations_s698.py -- S698 (F-1083): the one-off repair of the Call_Durations tab from the raw log.

WHY. Since 29-Oct midday the receiver's row arithmetic drifted (a gap in the tab), so every call.summary was written
on the PREVIOUS call's row: the new call stood twice (its call.end row and the overwritten row) and the older call
was gone from the tab. The raw log (call_hook_logs/YYYY-MM-DD.jsonl, written BEFORE any sheet write) holds every
event, so it is the truth. This script rebuilds the affected region of the tab from it, once.

WHAT IT DOES
  1. Reads the tab (all rows). The REGION = from the first row that is either of a day >= --since or carries a key
     seen twice, down to the last row. Rows above the region are never touched.
  2. Loads the truth: every raw-log event of the region's days through the receiver's own extract_record()
     (call.summary wins over call.end for one key), with the original capture time.
  3. --dry-run: prints the plan, counts only (no number, no name). Nothing written.
     --apply:   backs the WHOLE tab up to a CSV (owner-only), deletes the region's rows, appends the truth's records
                in capture order (plus any region row whose key the raw log does not hold, as it was), re-reads the
                tab and verifies: no key twice, every truth key present. A failed verify puts the backed-up region
                rows back (RESTORED: the duplicates return, nothing is lost) and exits 1.
  The receiver (call-hook) must be RESTARTED after an apply so its row index is rebuilt (the S698 installer does).

RUN (on the VPS)
  /root/wa/venv/bin/python3 /root/wa/call-hook/repair_call_durations_s698.py --dry-run
  /root/wa/venv/bin/python3 /root/wa/call-hook/repair_call_durations_s698.py --apply
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DEFAULT_SINCE = "2026-10-27"      # two days before the first doubled call seen (29-Oct midday)
GUARD_DAYS = 21                   # a region reaching further back than this is not repaired without --force


# ------------------------------------------------------------------------------------ pure parts (selftested)
def day_of(ts):
    return (str(ts or "")[:10]) if re.match(r"^\d{4}-\d{2}-\d{2}", str(ts or "")) else ""


def norm_captured(at):
    """The raw log's 'at' (an ISO stamp, microseconds possible) -> the receiver's captured_at_ist shape."""
    s = str(at or "").strip()
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", s)
    return (m.group(1) + "+05:30") if m else s


def load_truth(raw_dir, from_day, extract):
    """key -> record from the raw logs of days >= from_day. call.summary beats call.end; otherwise the later line.
    The record's captured_at_ist is the ORIGINAL capture time (the wrapper's 'at')."""
    records, lines, bad = {}, 0, 0
    for fp in sorted(glob.glob(os.path.join(raw_dir, "*.jsonl"))):
        if day_of(os.path.basename(fp)) < from_day:
            continue
        try:
            fh = open(fp, "r", encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                lines += 1
                try:
                    w = json.loads(line)
                except ValueError:
                    bad += 1
                    continue
                rec = extract(w.get("body"), str(w.get("event_type") or ""))
                if not rec:
                    continue
                rec["captured_at_ist"] = norm_captured(w.get("at")) or rec.get("captured_at_ist", "")
                key = rec["client_ref_id"]
                prev = records.get(key)
                if prev and prev.get("source_event") == "call.summary" and rec.get("source_event") != "call.summary":
                    continue
                records[key] = rec
    return records, lines, bad


def region_of(rows, since_day, key_col=0, cap_col=11, scan_days=14):
    """rows = the tab's data rows (row 2 onward). Returns (start_index0, start_sheet_row, why) or (None, None, why).
    A key seen twice is looked for only among rows dated within scan_days before the since-day: an old doubled
    probe row of July must not pull the region back to July."""
    try:
        scan_from = (datetime.date.fromisoformat(since_day) - datetime.timedelta(days=scan_days)).isoformat()
    except Exception:
        scan_from = since_day
    seen, dup_first = {}, None
    for i, r in enumerate(rows):
        k = (r[key_col] if len(r) > key_col else "").strip()
        if not k:
            continue
        d = day_of(r[cap_col] if len(r) > cap_col else "")
        if d and d < scan_from:
            continue
        if k in seen:
            dup_first = seen[k] if dup_first is None else min(dup_first, seen[k])
        else:
            seen[k] = i
    day_first = None
    for i, r in enumerate(rows):
        d = day_of(r[cap_col] if len(r) > cap_col else "")
        if d and d >= since_day:
            day_first = i
            break
    cands = [x for x in (dup_first, day_first) if x is not None]
    if not cands:
        return None, None, "no row of a day >= %s and no key seen twice" % since_day
    s = min(cands)
    why = "the first key seen twice" if (dup_first is not None and s == dup_first) else ("the first row of %s" % since_day)
    return s, s + 2, why


def plan_repair(rows, truth, start0, header, key_col=0, cap_col=11):
    """What --apply does. Pure. Returns a dict with the region rows, the rows to append (in capture order), counts."""
    region = rows[start0:]
    keys_in_region = [(r[key_col] if len(r) > key_col else "").strip() for r in region]
    keys_in_region = [k for k in keys_in_region if k]
    distinct = set(keys_in_region)
    dups = {k for k in distinct if keys_in_region.count(k) > 1}
    truth_keys = set(truth)
    tab_only = []          # region rows the raw log does not hold: kept as they were (never dropped)
    seen_tab_only = set()
    for r in region:
        k = (r[key_col] if len(r) > key_col else "").strip()
        if k and k not in truth_keys and k not in seen_tab_only:
            tab_only.append(list(r) + [""] * (len(header) - len(r)))
            seen_tab_only.add(k)
    restored = sorted(truth_keys - distinct)          # calls the drift destroyed
    out = []
    for k, rec in truth.items():
        out.append((rec.get("captured_at_ist") or "", [rec.get(h, "") for h in header]))
    for r in tab_only:
        out.append((r[cap_col] if len(r) > cap_col else "", r))
    out.sort(key=lambda t: t[0])
    append_rows = [r for _, r in out]
    by_day = {}
    for r in region:
        d = day_of(r[cap_col] if len(r) > cap_col else "")
        by_day.setdefault(d, [0, set(), 0])
        by_day[d][0] += 1
        k = (r[key_col] if len(r) > key_col else "").strip()
        if k:
            by_day[d][1].add(k)
    for k, rec in truth.items():
        d = day_of(rec.get("captured_at_ist"))
        by_day.setdefault(d, [0, set(), 0])
        by_day[d][2] += 1
    return {"region_rows": len(region), "distinct": len(distinct), "dups": len(dups), "truth": len(truth),
            "tab_only": len(tab_only), "restored": len(restored), "append": append_rows,
            "by_day": {d: (v[0], len(v[1]), v[2]) for d, v in by_day.items()}}


def verify(rows_after, truth_keys, key_col=0, cap_col=11, fresh_from=""):
    """ok, the keys seen twice (fresh events that arrived while the repair ran excepted), the truth keys missing,
    the fresh keys. A fresh event is a row whose captured_at is at or after fresh_from: the live receiver wrote it
    while this ran; the receiver's restart re-indexes it and the builder folds it -- never a reason to undo."""
    keys, fresh = [], set()
    for r in rows_after:
        k = (r[key_col] if len(r) > key_col else "").strip()
        if not k:
            continue
        keys.append(k)
        if fresh_from and str(r[cap_col] if len(r) > cap_col else "") >= fresh_from:
            fresh.add(k)
    dups = sorted({k for k in keys if keys.count(k) > 1 and k not in fresh})
    missing = sorted(set(truth_keys) - set(keys))
    return (not dups and not missing), dups, missing, sorted(fresh)


# ------------------------------------------------------------------------------------ the sheet side
def open_tab(chc):
    ws = chc.store_handle()
    return ws


def read_all(ws):
    vals = ws.get_all_values()
    if not vals:
        return [], []
    return vals[0], vals[1:]


def backup_csv(header, rows, backup_dir, stamp):
    os.makedirs(backup_dir, exist_ok=True)
    try:
        os.chmod(backup_dir, 0o700)
    except OSError:
        pass
    fp = os.path.join(backup_dir, "Call_Durations_before_S698_%s.csv" % stamp)
    with open(fp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    try:
        os.chmod(fp, 0o600)
    except OSError:
        pass
    n = sum(1 for _ in open(fp, encoding="utf-8")) - 1
    return fp, n


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    ap.add_argument("--since", default=DEFAULT_SINCE)
    ap.add_argument("--raw-dir", default=None)
    ap.add_argument("--backup-dir", default=os.path.join(HERE, "backups"))
    ap.add_argument("--force", action="store_true", help="repair a region reaching further back than %d days" % GUARD_DAYS)
    ap.add_argument("--hook", default=os.path.join(HERE, "call_hook_capture.py"))
    a = ap.parse_args(argv)

    sys.path.insert(0, os.path.dirname(os.path.abspath(a.hook)))
    import call_hook_capture as chc          # the receiver's own extract_record, header, sheet handle
    header_want = list(chc.HEADER)
    raw_dir = a.raw_dir or chc.RAW_DIR
    try:
        ws = open_tab(chc)
    except Exception as e:
        print("REPAIR: the tab could not be opened (%s: %s) -- nothing done" % (type(e).__name__, e))
        return 1
    header, rows = read_all(ws)
    if [h.strip().lower() for h in header] != [h.lower() for h in header_want]:
        print("REPAIR: the tab's header is not the receiver's (%s) -- nothing done" % header)
        return 1
    kc, cc = 0, header_want.index("captured_at_ist")
    start0, start_row, why = region_of(rows, a.since, kc, cc)
    if start0 is None:
        print("REPAIR: nothing to repair -- %s" % why)
        return 0
    first_day = min((day_of(r[cc]) for r in rows[start0:] if len(r) > cc and day_of(r[cc])), default=a.since)
    from_day = min(first_day, a.since)
    guard = (datetime.datetime.now(IST).date() - datetime.date.fromisoformat(from_day)).days if re.match(r"^\d{4}-\d{2}-\d{2}$", from_day) else 0
    if guard > GUARD_DAYS and not a.force:
        print("REPAIR GUARD: the region starts at sheet row %d (%s), a day %d days back -- further than the %d-day guard; nothing done. Tell Claude." % (start_row, from_day, guard, GUARD_DAYS))
        return 1
    truth, lines, bad = load_truth(raw_dir, from_day, chc.extract_record)
    p = plan_repair(rows, truth, start0, header_want, kc, cc)
    print("REPAIR S698 (%s): the tab has %d data rows; the region starts at sheet row %d (%s), %d rows, %d distinct keys, %d keys seen twice"
          % ("DRY RUN" if a.dry_run else "APPLY", len(rows), start_row, why, p["region_rows"], p["distinct"], p["dups"]))
    print("  the raw log from %s: %d lines (%d unreadable) -> %d calls; %d of them are NOT in the tab (destroyed by the drift, restored by this); %d region keys the raw log lacks (kept as they are)"
          % (from_day, lines, bad, p["truth"], p["restored"], p["tab_only"]))
    print("  %-11s %9s %9s %9s" % ("day", "tab rows", "tab keys", "raw calls"))
    for d in sorted(p["by_day"]):
        t = p["by_day"][d]
        print("  %-11s %9d %9d %9d" % (d or "(no day)", t[0], t[1], t[2]))
    print("  after the repair the region holds %d rows (was %d)" % (len(p["append"]), p["region_rows"]))
    if a.dry_run:
        print("  DRY RUN: nothing written.")
        return 0
    t_start = datetime.datetime.now(IST)
    stamp = t_start.strftime("%Y%m%d_%H%M%S")
    fresh_from = t_start.strftime("%Y-%m-%dT%H:%M:%S")
    fp, n = backup_csv(header, rows, a.backup_dir, stamp)
    if n != len(rows):
        print("REPAIR: the backup holds %d rows, the tab %d -- nothing deleted. Tell Claude." % (n, len(rows)))
        return 1
    print("  backup: %s (%d rows, mode 600)" % (fp, n))
    end_row = len(rows) + 1
    ws.delete_rows(start_row, end_row)
    if p["append"]:
        for i in range(0, len(p["append"]), 200):
            ws.append_rows(p["append"][i:i + 200], value_input_option="RAW")
    header2, rows2 = read_all(ws)
    ok, dups, missing, fresh = verify(rows2, set(truth), kc, cc, fresh_from)
    if ok:
        print("  VERIFIED: %d data rows now; no key twice; every raw-log call of the region present%s. RESTART call-hook now (its row index)."
              % (len(rows2), ("; %d event(s) arrived while this ran (the receiver re-indexes them on its restart)" % len(fresh)) if fresh else ""))
        return 0
    print("  !! VERIFY FAILED: %d key(s) twice, %d raw-log call(s) missing -- putting the backed-up region rows back" % (len(dups), len(missing)))
    try:
        for i in range(0, len(rows[start0:]), 200):
            ws.append_rows([list(r) for r in rows[start0:][i:i + 200]], value_input_option="RAW")
        print("  RESTORED the region's %d original rows after the rebuilt ones (duplicates are back; nothing lost). Tell Claude." % len(rows[start0:]))
    except Exception as e:
        print("  !! the restore failed too (%s) -- the backup CSV is %s. Tell Claude." % (type(e).__name__, fp))
    return 1


# ------------------------------------------------------------------------------------ selftest (offline)
def _selftest():
    H = ["client_ref_id", "ref_id", "session_id", "category", "status", "total_duration", "customer_result",
         "customer_talk_duration", "customer_ring_duration", "recording_filename", "ended_at_ist", "captured_at_ist",
         "source_event", "phone10"]
    cc = H.index("captured_at_ist")
    def row(key, day, ref="", ev="call.summary"):
        r = [""] * len(H)
        r[0] = key; r[1] = ref; r[cc] = day + "T10:00:00+05:30"; r[12] = ev; r[13] = "5000000001"
        return r
    rows = [row("IN-a", "2026-10-20"), row("IN-b", "2026-10-25"), row("IN-c", "2026-10-29", ev="call.end"),
            row("IN-d", "2026-10-29"), row("IN-d", "2026-10-29", ev="call.end"), row("IN-e", "2026-10-30")]
    failed = 0
    def check(name, cond):
        nonlocal failed
        print("  [%s] %s" % ("PASS" if cond else "FAIL", name))
        if not cond:
            failed += 1
    s0, sr, why = region_of(rows, "2026-10-27", 0, cc)
    check("region: starts at the first row of the since-day (sheet row 4)", s0 == 2 and sr == 4)
    s1, sr1, why1 = region_of(rows, "2026-10-31", 0, cc)
    check("region: a key seen twice pulls the start up to its first row (sheet row 5)", s1 == 3 and sr1 == 5 and "twice" in why1)
    check("region: nothing when no duplicate and no row of the day", region_of(rows[:2], "2026-11-01", 0, cc)[0] is None)
    truth = {"IN-c": dict(zip(H, row("IN-c", "2026-10-29"))), "IN-d": dict(zip(H, row("IN-d", "2026-10-29"))),
             "IN-e": dict(zip(H, row("IN-e", "2026-10-30"))), "IN-lost": dict(zip(H, row("IN-lost", "2026-10-29")))}
    p = plan_repair(rows, truth, s0, H, 0, cc)
    check("plan: the region's 4 rows carry 3 keys, 1 seen twice", p["region_rows"] == 4 and p["distinct"] == 3 and p["dups"] == 1)
    check("plan: the destroyed call comes back; nothing tab-only", p["restored"] == 1 and p["tab_only"] == 0 and len(p["append"]) == 4)
    rows_x = rows + [row("IN-odd", "2026-10-30")]
    p2 = plan_repair(rows_x, truth, s0, H, 0, cc)
    check("plan: a region row the raw log lacks is kept, as it was", p2["tab_only"] == 1 and len(p2["append"]) == 5
          and any(r[0] == "IN-odd" for r in p2["append"]))
    check("plan: appended in capture order", [r[cc] for r in p["append"]] == sorted(r[cc] for r in p["append"]))
    ok, d, m, f = verify(rows[:2] + p["append"], set(truth), 0, cc)
    check("verify: the rebuilt tab passes", ok and not d and not m)
    ok2, d2, m2, f2 = verify(rows, set(truth), 0, cc)
    check("verify: the old tab fails (a key twice, a call missing)", not ok2 and d2 == ["IN-d"] and m2 == ["IN-lost"])
    ok3, d3, m3, f3 = verify(rows[:2] + p["append"] + [row("IN-e", "2026-10-30")], set(truth), 0, cc, fresh_from="2026-10-30T09:00:00")
    check("verify: a key doubled by an event that arrived while the repair ran is tolerated and named", ok3 and f3 == ["IN-e"] and not d3)
    old = [row("IN-old", "2026-07-01"), row("IN-old", "2026-07-01")] + rows
    s4, sr4, why4 = region_of(old, "2026-10-27", 0, cc)
    check("region: an old doubled row of July does not pull the region back (the scan is 14 days)", s4 == 4 and sr4 == 6)
    check("captured stamp normalised", norm_captured("2026-10-29T12:34:56.123456+05:30") == "2026-10-29T12:34:56+05:30")
    print("selftest: %s" % ("PASSED" if not failed else "FAILED (%d)" % failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
