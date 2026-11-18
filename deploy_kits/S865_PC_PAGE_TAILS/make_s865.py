#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s865.py -- kit S865_PC_PAGE_TAILS (the parent, S480, 18-Nov-2026). Builds pc_kits.py and setup_notes.py from the
18-Nov bundle's bytes (FROM checked by md5; every anchor exactly once).   python3 make_s865.py <from_dir> <to_dir>"""
import hashlib, os, sys
src, dst = sys.argv[1:3]
FROM = {"pc_kits.py": "45d6f15d", "setup_notes.py": "aa7ee189"}
os.makedirs(dst, exist_ok=True)


def rep(t, a, b, w):
    n = t.count(a)
    if n != 1:
        sys.exit("!! anchor %s found %d times" % (w, n))
    return t.replace(a, b)


for n, m in FROM.items():
    if hashlib.md5(open(os.path.join(src, n), "rb").read()).hexdigest()[:8] != m:
        sys.exit("!! %s is not its FROM pin" % n)

# ------------------------------------------------------------------ pc_kits.py
t = open(os.path.join(src, "pc_kits.py"), encoding="utf-8").read()
t = rep(t, '''    {"id": "lab", "label": "Pathology lab PC", "planned": True},
''', '''    # S865 (F-1386 tail a): the lab PC's agent (the NK Pathology chat's S655) runs since 25-Oct; its card reads that agent's
    # own heartbeat file and snapshot index (lab_door.py writes them; read only here). No one-button kit for it yet.
    {"id": "lab", "label": "Pathology lab PC", "what": "Labmate's data to the server every 3 hours · a heartbeat every 5 minutes",
     "health": "labpc",
     "kit_note": "Set up by the lab agent kit: INSTALL_LAB_AGENT.bat on the lab PC (S655). A one-button kit on this page "
                 "is not made yet."},
''', "pcs lab")
t = rep(t, '''def _ticks(pc_id):''', '''LAB_BEAT = os.environ.get("LAB_BEAT", "/root/labdata/lab_heartbeat.json")                     # S865: lab_door.py's own files
LAB_INDEX = os.environ.get("LAB_SNAP_INDEX", "/root/labdata/incoming/snapshots.json")        # read only here
LAB_HEARD_MIN = 20              # a heartbeat every 5 minutes: heard within 20 = working
LAB_SILENT_WARN_MIN = 60        # review 1: silent this long while the lab is open = a look
LAB_SILENT_BAD_H = 3            # ... and 3 hours = not working (lab_door.health_row's own rule)
LAB_OFF_HOURS = 26              # outside opening hours, up to 26 hours unheard is 'off', not a fault
LAB_SNAP_HOURS = 26             # lab_door.health_row's own rule: no snapshot for 26 hours = a look (no morning false alarm)


def _lab_open(now):
    """lab_door.health_row's opening hours: 08:00-21:00 Monday-Saturday, 08:00-14:00 Sunday (IST)."""
    return 8 <= now.hour < (14 if now.weekday() == 6 else 21)


def _lab_ts(s):
    try:
        return dt.datetime.fromisoformat(str(s or "")[:19])
    except ValueError:
        return None


def _lab_row(now=None):
    """S865: the lab PC's row, shaped as the health page's rows -- from the agent's heartbeat and the snapshot index, by
    lab_door.health_row's own hours and thresholds. Times, sizes and a count only (never text from the PC); never raises."""
    now = now or _ist_now()
    try:
        with open(LAB_BEAT, encoding="utf-8") as fh:
            rec = json.load(fh)
        heard = _lab_ts(rec.get("received_ist"))
        beat = rec.get("beat") if isinstance(rec.get("beat"), dict) else {}
        if heard is None:
            raise ValueError("no time")
    except Exception:                                          # noqa: BLE001
        return dict(key="labpc", state="info", detail="no heartbeat from the lab PC has reached the server yet")
    snap = None
    try:
        with open(LAB_INDEX, encoding="utf-8") as fh:
            idx = json.load(fh)
        for v in (idx.values() if isinstance(idx, dict) else []):        # review 5: each entry parsed, a bad one skipped
            if not isinstance(v, dict):
                continue
            ts = _lab_ts(v.get("received_ist"))
            try:
                size = int(v.get("bytes") or 0)
            except (TypeError, ValueError):
                size = 0
            if ts is not None and (snap is None or ts > snap[0]):
                snap = (ts, size)
    except Exception:                                          # noqa: BLE001
        snap = None
    att = beat.get("attention") if isinstance(beat.get("attention"), list) else []
    hs = heard.strftime("%Y-%m-%d %H:%M")
    if snap:
        mb = snap[1] / 1048576.0
        sn = "Labmate's data last reached the server %s (%s)" % (_when(snap[0].strftime("%Y-%m-%d %H:%M")),
                                                                 ("%.1f MB" % mb) if mb >= 0.1 else "under 0.1 MB")
    else:
        sn = "no Labmate data has reached the server yet"
    extra = ("; the PC reports %d thing%s to look at" % (len(att), "" if len(att) == 1 else "s")) if att else ""
    age = (now - heard).total_seconds()
    stale = snap is None or (now - snap[0]).total_seconds() > LAB_SNAP_HOURS * 3600
    if age <= LAB_HEARD_MIN * 60:
        state = "warn" if (stale or att) else "ok"
        return dict(key="labpc", state=state, detail="heard %s; %s%s" % (_when(hs), sn, extra))
    if _lab_open(now) and age > LAB_SILENT_WARN_MIN * 60:
        state = "bad" if age > LAB_SILENT_BAD_H * 3600 else "warn"
        return dict(key="labpc", state=state, detail="silent since %s while the lab is open; %s%s" % (_when(hs), sn, extra))
    if age <= LAB_OFF_HOURS * 3600:
        return dict(key="labpc", state="info", detail="switched off since %s (it is off out of hours); %s%s" % (_when(hs), sn, extra))
    return dict(key="labpc", state="warn", detail="not heard since %s; %s%s" % (_when(hs), sn, extra))


def _ticks(pc_id):''', "lab row")
t = rep(t, '''    try:
        rows = {c["key"]: c for c in _health(_db())["checks"]}
    except Exception:                                          # noqa: BLE001 -- the page never dies of a health check
        rows = {}
''', '''    try:
        rows = {c["key"]: c for c in _health(_db())["checks"]}
    except Exception:                                          # noqa: BLE001 -- the page never dies of a health check
        rows = {}
    rows.setdefault("labpc", _lab_row())                       # S865: lab_door's health row wins once it is wired
''', "rows lab")
t = rep(t, '''            card.append("<p class=kit>Its setup kit is not on the server yet — it is being packed and rehearsed. "
                        "Until then this card only shows whether the PC is working.</p>")''', '''            card.append("<p class=kit>%s</p>" % html.escape(pc["kit_note"]) if pc.get("kit_note") else   # S865
                        "<p class=kit>Its setup kit is not on the server yet — it is being packed and rehearsed. "
                        "Until then this card only shows whether the PC is working.</p>")''', "kit note")
open(os.path.join(dst, "pc_kits.py"), "w", encoding="utf-8").write(t)

# ------------------------------------------------------------------ setup_notes.py
t = open(os.path.join(src, "setup_notes.py"), encoding="utf-8").read()
t = rep(t, '''            "Two mails a day from the server, at 11:30 and at 21:00 (the day summary), and a self-check at 14:00.",
        ]),''', '''            "Two mails a day from the server, at 11:30 and at 21:00 (the day summary), and a self-check at 14:00.",
            "<b>A watch on the machine itself</b> (since 14-Nov-2026): every 5 minutes the server checks when the machine last "
            "called it. In clinic hours on a working day, 30 minutes without a call, no punch by 10:00, or a clock that has "
            "gone wrong each send you one message (a silence, one more when the machine is back). The Attendance group on the "
            "<a href='/finance/freshness'>freshness page</a> shows it as \\u201cattendance machine contact\\u201d.",
        ]),''', "notes watch")
t = rep(t, '''        ("If something goes wrong", [
            "<b>No punches are showing.</b>''', '''        ("If something goes wrong", [
            "<b>13/14-Nov-2026, for the record:</b> the machine's clock stopped at 13-Nov 10:38 and the machine then shut "
            "itself down; switched on again on 14-Nov it showed the right time, and it was to go to BL Computers for a check. "
            "That day's attendance was entered by hand in the staff register. The watch above was built that day so that a "
            "silence like it is told within half an hour.",
            "<b>No punches are showing.</b>''', "notes nov")
t = rep(t, '''NOTES_CHECKED = "22-Oct-2026"''', '''NOTES_CHECKED = "18-Nov-2026"''', "notes checked")
open(os.path.join(dst, "setup_notes.py"), "w", encoding="utf-8").write(t)
for n in FROM:
    print("%s %s" % (hashlib.md5(open(os.path.join(dst, n), "rb").read()).hexdigest(), n))
