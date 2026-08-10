#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""portal_gist.py  --  builds portal_gist.json  (the D223 doctor-portal gist contract).

Unit 1 of 2 (the other is the portal tile in portal.py, which only READS this file).

WHAT IT DOES
  Reads, strictly READ-ONLY, from:
    * the Clinic Callback Tracker Google Sheet  (tabs: Call_Feed, Callbacks_Today, K_Strikes)
    * /root/wa/flag_investigator_results.json   (pipeline health, written by the Flag Investigator)
  Computes the operational gist (metrics 1-4) and writes ONE file: portal_gist.json.

ONE-WRITER (D235):  it writes only portal_gist.json.  It never writes any Sheet tab.
FAIL-LOUD (D236):   a source it cannot read/parse -> that block's numbers become null,
                    a note is added, and sources_ok is set false.  NEVER a silent zero.

METRICS v1 (this build):
  1 pipeline health   <- flag_investigator_results.json  (never_recorded / missed / escalate_lokesh)
  2 call volume       <- Call_Feed        (Direction + Start_Unix)
  3 unfiled outcomes  <- Callbacks_Today  (rows with a blank "Staff Status")
  4 third-strikes     <- K_Strikes        (distinct Mobile with Tries >= 3 in the last 7 days)
  5 verdict-awaiting-referee  -- DEFERRED  (verdict store is not on this Sheet; bound later)

RUN MODES
  --selftest   run the pure compute functions on fixtures; no Sheet, no creds, no network.
  --dry-run    read live sources, compute, PRINT the json to stdout; write nothing.
  (default)    read live sources, compute, ATOMICALLY write portal_gist.json.

VPS python:  /root/wa/venv/bin/python3 portal_gist.py --selftest
"""

import argparse
import datetime
import json
import os
import sys
import tempfile

# ----------------------------------------------------------------------------- config
IST         = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
SHEET_ID    = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"
CREDS_PATH  = "/root/wa/patient-mirror-key.json"
INV_JSON    = "/root/wa/recordings-archive/flag_investigator_results.json"
OUT_PATH    = "/root/wa/portal_gist.json"
STALE_AFTER_MIN = 45

# Investigator layout confirmed live (S165): never_recorded_7d + escalate_lokesh are
# TOP-LEVEL; the recording-gap categories live in a SPARSE `counts` dict (a category
# absent == a genuine 0, by the investigator's own design).  never_recorded_7d is the
# core field and FAIL-LOUDs if absent; `missed` reads counts and defaults to 0 (legit).
INV_NEVER_RECORDED_KEYS = ["never_recorded_7d", "never_recorded", "never_recorded_count"]
INV_ESCALATE_KEYS       = ["escalate_lokesh", "escalate"]
INV_MISSED_COUNT_KEY    = "missed_no_conversation"   # inside the sparse `counts` dict

TAB_CALL_DURATIONS  = "Call_Durations"   # live capture (Call_Feed is dead since Apr 2026)
TAB_CALLBACKS_TODAY = "Callbacks_Today"
TAB_KSTRIKES        = "K_Strikes"

# Call_Durations.category -> direction  (confirmed: incoming=1146, obd=502)
DIR_BY_CATEGORY = {"incoming": "in", "obd": "out"}


# ----------------------------------------------------------------------------- helpers
def now_ist():
    return datetime.datetime.now(IST)


def ist_date_of_unix(unix):
    return datetime.datetime.fromtimestamp(int(unix), IST).date()


def to_int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def parse_date_loose(s):
    """Best-effort date parse for text date columns; returns a date or None (never raises)."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    # take the date part if a datetime string
    head = s.replace("T", " ").split(" ")[0]
    fmts = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
            "%d-%b-%Y", "%d %b %Y", "%Y/%m/%d", "%d-%b-%y")
    for f in fmts:
        try:
            return datetime.datetime.strptime(head, f).date()
        except ValueError:
            continue
    return None


def norm_direction(v):
    """incoming/outgoing/other from many spellings; case-insensitive."""
    t = (str(v) if v is not None else "").strip().lower()
    if t.startswith("in") or t in ("i", "inbound", "incoming"):
        return "in"
    if t.startswith("out") or t in ("o", "outbound", "outgoing"):
        return "out"
    return "other"


# --------------------------------------------------------------------- pure compute (1-4)
def compute_pipeline(inv):
    """inv = parsed flag_investigator_results.json dict.
    never_recorded_7d is REQUIRED (raises if absent -> fail-loud). escalate defaults False.
    missed is read from the sparse `counts` dict and defaults to 0 (a legit design-zero)."""
    nr = None
    for k in INV_NEVER_RECORDED_KEYS:
        if k in inv:
            nr = to_int(inv[k])
            break
    if nr is None:
        raise KeyError("flag_investigator_results.json: none of %r present/int" % (INV_NEVER_RECORDED_KEYS,))
    esc = False
    for k in INV_ESCALATE_KEYS:
        if k in inv:
            esc = inv[k]
            break
    counts = inv.get("counts") or {}
    ms = to_int(counts.get(INV_MISSED_COUNT_KEY, 0)) or 0
    return {"never_recorded_7d": nr, "missed_7d": ms, "escalate_lokesh": bool(esc)}


def compute_calls(rows, today):
    """rows: list of dicts from Call_Durations. Windows on ended_at_ist (already IST ISO,
    first 10 chars = the date); direction from category (incoming->in, obd->out).
    Excludes synthetic health probes (status == 'probe')."""
    out = {"in_today": 0, "out_today": 0, "in_7d": 0, "out_7d": 0}
    today_iso = today.isoformat()
    week = {(today - datetime.timedelta(days=i)).isoformat() for i in range(7)}  # 7 days incl. today
    skipped = 0
    unknown_dir = 0
    for r in rows:
        if str(r.get("status", "")).strip().lower() == "probe":
            continue
        day = str(r.get("ended_at_ist", ""))[:10]
        if len(day) != 10 or day[4] != "-":
            skipped += 1
            continue
        direc = DIR_BY_CATEGORY.get(str(r.get("category", "")).strip().lower())
        if direc is None:
            unknown_dir += 1
            continue
        if day == today_iso:
            out["in_today" if direc == "in" else "out_today"] += 1
        if day in week:
            out["in_7d" if direc == "in" else "out_7d"] += 1
    return out, skipped, unknown_dir


def compute_unfiled(cbt_rows):
    """Callbacks_Today rows with a blank 'Staff Status' == awaiting a filed outcome."""
    n = 0
    for r in cbt_rows:
        if str(r.get("Staff Status", "")).strip() == "":
            n += 1
    return n, len(cbt_rows)


def compute_strikes(kstrike_rows, today):
    """Distinct Mobile with Tries >= 3 in the last 7 days (uses the 'When' column)."""
    week_lo = today - datetime.timedelta(days=6)
    hit = set()
    skipped = 0
    for r in kstrike_rows:
        tries = to_int(r.get("Tries"))
        when = parse_date_loose(r.get("When"))
        if tries is None or when is None:
            skipped += 1
            continue
        if tries >= 3 and week_lo <= when <= today:
            mob = str(r.get("Mobile", "")).strip()
            hit.add(mob if mob else "row#%d" % id(r))
    return len(hit), skipped


# ------------------------------------------------------------------------ orchestration
def build_gist(get_inv, get_rows, today=None):
    """get_inv() -> dict ;  get_rows(tabname) -> list[dict].  Both may raise; we contain it."""
    if today is None:
        today = now_ist().date()
    gist = {
        "generated_ist": now_ist().replace(microsecond=0).isoformat(),
        "stale_after_min": STALE_AFTER_MIN,
        "pipeline": None,
        "calls": None,
        "unfiled_outcomes": None,
        "third_strikes_7d": None,
        "verdict_awaiting_referee": None,   # DEFERRED until the verdict store is bound
        "sources_ok": True,
        "notes": [],
    }

    def fail(field, msg):
        gist["sources_ok"] = False
        gist["notes"].append("%s: %s" % (field, msg))

    # 1 pipeline
    try:
        gist["pipeline"] = compute_pipeline(get_inv())
    except Exception as e:
        fail("pipeline", str(e))

    # 2 calls
    try:
        calls, skipped, unknown = compute_calls(get_rows(TAB_CALL_DURATIONS), today)
        gist["calls"] = calls
        if skipped:
            gist["notes"].append("calls: %d Call_Durations rows had no usable ended_at_ist (skipped)" % skipped)
        if unknown:
            gist["notes"].append("calls: %d Call_Durations rows had an unmapped category (skipped)" % unknown)
    except Exception as e:
        fail("calls", str(e))

    # 3 unfiled outcomes (Callbacks_Today rows not yet actioned by staff = blank Staff Status)
    try:
        n, total = compute_unfiled(get_rows(TAB_CALLBACKS_TODAY))
        gist["unfiled_outcomes"] = n
    except Exception as e:
        fail("unfiled_outcomes", str(e))

    # 4 third strikes
    try:
        n, skipped = compute_strikes(get_rows(TAB_KSTRIKES), today)
        gist["third_strikes_7d"] = n
        if skipped:
            gist["notes"].append("third_strikes_7d: %d K_Strikes rows unparseable (skipped)" % skipped)
    except Exception as e:
        fail("third_strikes_7d", str(e))

    # 5 verdict-awaiting-referee: deferred by design (not a failure)
    gist["notes"].append("verdict_awaiting_referee: deferred - verdict store not on this Sheet (bind later)")
    return gist


# ------------------------------------------------------------------------------ live I/O
def live_get_inv():
    with open(INV_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def make_live_get_rows():
    import gspread  # imported lazily so --selftest needs neither gspread nor creds
    gc = gspread.service_account(filename=CREDS_PATH)
    sh = gc.open_by_key(SHEET_ID)
    cache = {}

    def get_rows(tab):
        if tab not in cache:
            cache[tab] = sh.worksheet(tab).get_all_records()  # header row -> dict keys
        return cache[tab]

    return get_rows


def atomic_write(path, text):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".portal_gist.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
        os.chmod(path, 0o644)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


# --------------------------------------------------------------------------------- tests
def selftest():
    fails = []
    nchecks = [0]

    def check(name, cond):
        nchecks[0] += 1
        print(("  ok   " if cond else "  FAIL ") + name)
        if not cond:
            fails.append(name)

    T = datetime.date(2026, 8, 10)                 # a fixed "today" for determinism
    def unix_on(date, h=12):
        return int(datetime.datetime(date.year, date.month, date.day, h, 0, tzinfo=IST).timestamp())

    # --- pipeline: live layout (top-level never_recorded_7d + sparse counts) ---
    p = compute_pipeline({"never_recorded_7d": 2, "escalate_lokesh": False,
                          "counts": {"missed_no_conversation": 5}})
    check("pipeline top-level + counts.missed", p == {"never_recorded_7d": 2, "missed_7d": 5, "escalate_lokesh": False})
    p2 = compute_pipeline({"never_recorded_7d": 0, "escalate_lokesh": True, "counts": {"recoverable_pastdate": 1}})
    check("pipeline sparse counts -> missed 0, escalate true",
          p2 == {"never_recorded_7d": 0, "missed_7d": 0, "escalate_lokesh": True})
    p3 = compute_pipeline({"never_recorded": 4})     # alt alias, no counts, no escalate
    check("pipeline alt-alias, missed/escalate default",
          p3 == {"never_recorded_7d": 4, "missed_7d": 0, "escalate_lokesh": False})
    raised = False
    try:
        compute_pipeline({"counts": {"missed_no_conversation": 3}})   # no never_recorded -> must raise
    except KeyError:
        raised = True
    check("pipeline raises when never_recorded absent (fail-loud)", raised)

    # --- calls: Call_Durations, category direction, ended_at_ist window, probe + bad-date skip ---
    def cd_row(cat, day, status="bridged"):
        return {"category": cat, "status": status, "ended_at_ist": day + "T12:00:00+05:30"}
    T_iso = T.isoformat()
    d3 = (T - datetime.timedelta(days=3)).isoformat()
    d8 = (T - datetime.timedelta(days=8)).isoformat()
    cdur = [
        cd_row("incoming", T_iso),                    # in today & 7d
        cd_row("obd", T_iso),                         # out today & 7d
        cd_row("incoming", d3),                       # in 7d only
        cd_row("obd", d8),                            # outside 7d
        cd_row("incoming", T_iso, status="probe"),    # probe -> excluded
        cd_row("weird", T_iso),                       # unmapped category -> counted unknown
        {"category": "incoming", "status": "bridged", "ended_at_ist": ""},   # bad date -> skipped
    ]
    calls, skipped, unknown = compute_calls(cdur, T)
    check("calls in_today",  calls["in_today"] == 1)
    check("calls out_today", calls["out_today"] == 1)
    check("calls in_7d",     calls["in_7d"] == 2)
    check("calls out_7d",    calls["out_7d"] == 1)
    check("calls skipped bad-date", skipped == 1)
    check("calls unknown category", unknown == 1)

    # --- unfiled outcomes: blank Staff Status ---
    cbt = [
        {"Staff Status": ""}, {"Staff Status": "   "}, {"Staff Status": "Called"}, {"Staff Status": "Done"},
    ]
    n, total = compute_unfiled(cbt)
    check("unfiled counts blanks only", n == 2 and total == 4)

    # --- third strikes: distinct mobiles, Tries>=3, within 7d ---
    ks = [
        {"When": "2026-08-10", "Tries": "3", "Mobile": "9990001111"},   # hit
        {"When": "2026-08-09", "Tries": "5", "Mobile": "9990001111"},   # same mobile -> still 1 distinct
        {"When": "2026-08-08", "Tries": "4", "Mobile": "8880002222"},   # hit (distinct)
        {"When": "2026-08-10", "Tries": "2", "Mobile": "7770003333"},   # below 3
        {"When": "2026-07-01", "Tries": "9", "Mobile": "6660004444"},   # outside 7d
        {"When": "bad-date",   "Tries": "9", "Mobile": "5550005555"},   # unparseable -> skipped
    ]
    n, skipped = compute_strikes(ks, T)
    check("third strikes distinct in-window", n == 2)
    check("third strikes skipped bad rows",   skipped == 1)

    # --- orchestration fail-loud aggregation ---
    def bad_inv():
        raise IOError("no such file")
    def rows_for(tab):
        if tab == TAB_CALL_DURATIONS:  return cdur
        if tab == TAB_CALLBACKS_TODAY: return cbt
        if tab == TAB_KSTRIKES:        return ks
        return []
    g = build_gist(bad_inv, rows_for, today=T)
    check("build: bad pipeline -> null + sources_ok false", g["pipeline"] is None and g["sources_ok"] is False)
    check("build: good calls still present", g["calls"]["in_7d"] == 2)
    check("build: unfiled present", g["unfiled_outcomes"] == 2)
    check("build: strikes present", g["third_strikes_7d"] == 2)
    check("build: verdict deferred (null)", g["verdict_awaiting_referee"] is None)
    check("build: has a pipeline note", any(x.startswith("pipeline:") for x in g["notes"]))
    json.dumps(g)  # must be serialisable
    check("build: json-serialisable", True)

    # all-good build has sources_ok true
    g2 = build_gist(lambda: {"never_recorded_7d": 0, "escalate_lokesh": False, "counts": {}},
                    rows_for, today=T)
    check("build: all sources ok -> sources_ok true", g2["sources_ok"] is True)

    print("\nSELFTEST: %d checks, %d failed" % (nchecks[0], len(fails)))
    return fails


# ---------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Build portal_gist.json (D223 gist).")
    ap.add_argument("--selftest", action="store_true", help="run fixtures; no Sheet/creds/network")
    ap.add_argument("--dry-run", action="store_true", help="read live, print json, write nothing")
    args = ap.parse_args()

    if args.selftest:
        fails = selftest()
        sys.exit(1 if fails else 0)

    get_rows = make_live_get_rows()
    gist = build_gist(live_get_inv, get_rows)
    text = json.dumps(gist, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(text)
        return
    atomic_write(OUT_PATH, text)
    print("wrote %s (sources_ok=%s, notes=%d)" % (OUT_PATH, gist["sources_ok"], len(gist["notes"])))


if __name__ == "__main__":
    main()
