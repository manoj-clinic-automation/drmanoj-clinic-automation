#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s456.py -- kit S456_WINDOWS_CURRENCY. Walks the Reception PC row of the health page on the kit's
reception_door.py (--new) beside the one being replaced (--old), with made-up heartbeats in a scratch folder:
the trouble rows must read as before, BOTH Docterz reports must be named, the Windows words must be the PC's own.
Nothing live is read or written. The last line is  WALK_S456 GREEN <n> checks  or  WALK_S456 RED.

    python3 -B walk_s456.py --new built/reception_door.py --old /root/finance/reception_door.py
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import sys
import tempfile
import time

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("%s  %s%s" % ("  ok  " if cond else "  FAIL", name, ("  -- " + str(detail)[:300]) if (detail and not cond) else ""))


def load(path, tag, beat_file):
    os.environ["RECEPTION_BEAT"] = beat_file
    spec = importlib.util.spec_from_file_location("reception_door_" + tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def row(m, beat_file, beat, age_min=2, now_ist=None, settings=None, raw=None):
    """One call of health_row: (state, words, hint)."""
    if beat is None and raw is None:
        if os.path.exists(beat_file):
            os.remove(beat_file)
    else:
        with open(beat_file, "w", encoding="utf-8") as fh:
            fh.write(raw if raw is not None else json.dumps(
                {"received_ts": int(time.time() - age_min * 60), "received_ist": "x", "from": "walk", "beat": beat}))
    got = []
    st = settings or {}
    m.health_row(lambda k, l, s, d, h="": got.append((k, l, s, d, h)), lambda con, k, d=None: st.get(k, d), None,
                 now_ist=now_ist or dt.datetime(2026, 10, 5, 11, 0))
    assert len(got) == 1, got
    assert got[0][0] == "reception" and got[0][1] == "Reception PC", got
    return got[0][2:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True)
    ap.add_argument("--old", required=True)
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="s456_walk_")
    bf = os.path.join(tmp, "reception_heartbeat.json")
    new, old = load(a.new, "new", bf), load(a.old, "old", bf)
    def reps(cons="2026-10-03T21:02:57", foll="2026-10-03T21:03:15", dl_foll="2026-07-07T08:39:18"):
        return {"docterz_exports": {"consultation_newest": cons, "followup_newest": foll, "consultation_today": 0},
                "downloads_folder": {"consultation_newest": "2026-10-01T20:13:37", "followup_newest": dl_foll}}

    base = dict({"agent_version": "S453.1", "google_drive_running": True, "attention": []}, **reps())
    win_old = {"product": "Windows 10 Home Single Language", "release": "22H2", "build": "19045.6466",
               "system_files_dated": "2025-10-15", "update_installed": "2025-11-12", "update_is_this_build": True}
    stale = dict(base, agent_version="S456.1", windows=win_old)
    fresh = dict(stale, windows=dict(win_old, product="Windows 11 Pro", release="24H2", build="26100.6584",
                                     system_files_dated="2026-08-28", update_installed="2026-09-12"))
    GOOD = "heard 2 minute(s) ago \u00b7 Google Drive running \u00b7 Docterz reports \u2014 consultation report: 03-Oct 21:02 \u00b7 follow-up log: 03-Oct 21:03"
    # the walk's "now" is Monday 05-Oct-2026 11:00: Saturday evening's downloads are the newest there can be

    # 1. the trouble rows read exactly as before
    for name, kw in (("no heartbeat yet", dict(beat=None)),
                     ("a heartbeat 30 minutes old in clinic hours", dict(beat=base, age_min=30)),
                     ("a heartbeat 60 minutes old in clinic hours", dict(beat=base, age_min=60)),
                     ("a heartbeat 5 hours old at night", dict(beat=base, age_min=300, now_ist=dt.datetime(2026, 10, 5, 23, 0))),
                     ("the PC's own attention line", dict(beat=dict(base, attention=["Google Drive is NOT running"]))),
                     ("a heartbeat file that is not JSON", dict(beat=None, raw="{not json")),
                     ("attention + old Windows + a missed report", dict(beat=dict(stale, attention=["disk space is low: 1.0 GB free"], **reps(foll="2026-07-07T08:39:18")))),
                     ("silent PC + old Windows", dict(beat=stale, age_min=60))):
        o, n = row(old, bf, **kw), row(new, bf, **kw)
        check("unchanged: %s" % name, o == n, (o, n))

    # 2. BOTH Docterz reports are named (the owner, 03-Oct)
    s, words, hint = row(new, bf, base)
    check("both reports named, each with the time it was last downloaded; 'ok'", s == "ok" and words == GOOD and hint == "", (s, words))
    s, words, hint = row(new, bf, dict(base, google_drive_running=False))
    check("Google Drive not running is still said in the row", "Google Drive NOT running" in words, words)
    s, words, hint = row(new, bf, dict(base, **reps(foll="2026-07-07T08:39:18")))
    check("the follow-up log not downloaded since July -> amber, and the row says which and since when",
          s == "warn" and "consultation report: 03-Oct 21:02" in words and "follow-up log: NOT downloaded since 07-Jul 08:39" in words, (s, words))
    check("...the hint names the follow-up log only, and what is built from it",
          "evening: the follow-up log. " in hint and "Callback Tracker" in hint and "BOTH" in hint, hint)
    s, words, hint = row(new, bf, dict(base, **reps(cons="2026-10-01T20:13:37", foll="2026-10-01T20:14:00")))
    check("both missed -> both named", s == "warn" and "the consultation report and the follow-up log" in hint, (s, hint))
    s, words, hint = row(new, bf, dict(base, **reps(foll="2026-07-07T08:39:18", dl_foll="2026-10-03T21:10:00")))
    check("the newest of the PC's two folders counts (saved into Downloads by mistake is still downloaded)",
          s == "ok" and "follow-up log: 03-Oct 21:10" in words, (s, words))
    s, words, hint = row(new, bf, dict(base, **reps(cons="2026-10-02T21:02:57", foll="2026-10-02T21:03:15")))
    check("Friday's files on a Monday morning: Saturday evening was missed -> amber", s == "warn", (s, words))
    s, words, hint = row(new, bf, base, settings={"pipeline.clinic_sunday": "1"})
    check("a clinic that opens on Sunday: Saturday's files on Monday -> Sunday evening was missed", s == "warn", (s, words))
    s, words, hint = row(new, bf, dict(base, **reps(cons="2026-10-02T21:02:57", foll="2026-10-02T21:03:15")), settings={"reception.report_missed_evenings": "2"})
    check("the line is a setting (reception.report_missed_evenings)", s == "ok", (s, words))
    s, words, hint = row(new, bf, dict(base, **reps(cons="2026-10-04T21:00:00", foll="2026-10-04T21:01:00")))
    check("yesterday evening's files -> 'ok'", s == "ok" and "04-Oct 21:00" in words, (s, words))
    s, words, hint = row(new, bf, dict(base, **reps()), now_ist=dt.datetime(2026, 10, 3, 22, 0))
    check("the evening itself, files just downloaded -> 'ok'", s == "ok", (s, words))
    nb = dict(base); nb["docterz_exports"] = {"present": True}; nb["downloads_folder"] = {"present": False}
    s, words, hint = row(new, bf, nb)
    check("a PC that has never had either report -> amber, 'NOT SEEN on this PC' twice", s == "warn" and words.count("NOT SEEN on this PC") == 2, (s, words))
    for junk in ("x", [1], None, {"followup_newest": 5, "consultation_newest": "yesterday"}):
        jb = dict(base); jb["docterz_exports"] = junk; jb["downloads_folder"] = junk
        s, words, hint = row(new, bf, jb)
        check("junk where a folder's counts should be (%s) -> a row, not an error" % type(junk).__name__, s == "warn" and words.startswith("heard 2 minute(s) ago"), (s, words))

    # 3. Windows, in the PC's own words (F-700)
    s, words, hint = row(new, bf, stale)
    check("old Windows -> 'info' (worth knowing, never a problem), the usual words first", s == "info" and words.startswith(GOOD + " \u00b7 "), (s, words))
    check("...and it says since when, in plain words",
          words.endswith("Windows 10 Home Single Language 22H2: no Windows update since Nov 2025"), words)
    check("...the hint carries the day, the build and that it is his decision",
          "12-Nov-2025" in hint and "build 19045.6466" in hint and "decision for you" in hint and "Clinic PCs tile" in hint, hint)
    s, words, hint = row(new, bf, dict(stale, **reps(foll="2026-07-07T08:39:18")))
    check("a missed report wins over old Windows: amber, and the Windows words wait", s == "warn" and "Windows" not in words, (s, words))
    s, words, hint = row(new, bf, fresh)
    check("a PC updated last month -> 'ok', and says when", s == "ok" and words.endswith("Windows 11 Pro 24H2, last updated Sep 2026") and hint == "", (s, words, hint))
    s, words, hint = row(new, bf, stale, settings={"reception.windows_stale_days": "400"})
    check("the line is a setting (reception.windows_stale_days)", s == "ok" and words.endswith("last updated Nov 2025"), (s, words))
    s, words, hint = row(new, bf, dict(stale, windows=dict(win_old, update_installed=None)))
    check("only the system files' date readable -> judged by it", s == "info" and "since Oct 2025" in words and "15-Oct-2025" in hint, (s, words, hint))
    s, words, hint = row(new, bf, dict(stale, windows=dict(win_old, system_files_dated="2026-09-20")))
    check("the NEWER of the two dates decides", s == "ok" and words.endswith("last updated Sep 2026"), (s, words))
    s, words, hint = row(new, bf, dict(stale, windows=dict(win_old, update_installed="12/11/2025", system_files_dated=None)))
    check("no readable date -> 'ok', and says the date could not be read", s == "ok" and "could not be read" in words, (s, words))
    for junk in ([1, 2], "x", 7, {"product": None}, {"product": {"a": 1}, "update_installed": 5, "system_files_dated": "2025-13-45"}):
        s, words, hint = row(new, bf, dict(base, windows=junk))
        check("junk for a Windows reading (%s) -> a row, not an error" % type(junk).__name__, s == "ok" and words.startswith(GOOD), (s, words))
    s, words, hint = row(new, bf, dict(stale, windows=dict(win_old, product="<script>alert('x')</script>", release="<b>", build="<i>1</i>")))
    check("only plain characters reach the page", not any(c in words + hint for c in "<>'\"&") and s == "info", (words, hint))
    s, words, hint = row(new, bf, dict(stale, windows=dict(win_old, product="W" * 500)))
    check("a long name is cut", len(words) < 260, len(words))
    s, words, hint = row(new, bf, base, age_min=2, now_ist=dt.datetime(2026, 10, 4, 12, 0))
    check("a Sunday morning reads Saturday evening's files as on time", s == "ok", (s, words))
    try:
        os.remove(bf)
        os.rmdir(tmp)
    except OSError:
        pass
    print("%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("   FAILED: " + f)
    print("WALK_S456 GREEN %d checks" % len(PASS) if not FAIL else "WALK_S456 RED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
