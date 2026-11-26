#!/usr/bin/env python3
"""S961 (S528, 26-Nov-2026, D1080, F-1687): reception agent S456.1 -> S961.1.
A report saved into the export folders is posted within about half a minute,
not after the next 5-minute heartbeat. Anchored edits on the FROM bytes; every
anchor must occur exactly once."""
import hashlib, sys
FROM_MD5 = "d3d4b67bdb1c3a356037b9cce9a30a0d"
src, dst = sys.argv[1], sys.argv[2]
raw = open(src, "rb").read()
assert hashlib.md5(raw).hexdigest() == FROM_MD5, "FROM is not S456.1"
t = raw.decode("utf-8")

def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, "anchor found %d times: %r" % (n, old[:70])
    t = t.replace(old, new)

rep('AGENT_VERSION = "S456.1"', 'AGENT_VERSION = "S961.1"')

rep('''     three registry keys and one file's date, read at most every six hours.
''',
'''     three registry keys and one file's date, read at most every six hours.

  8. A REPORT GOES UP AS SOON AS IT IS SAVED (S961, D1080, F-1687). Until
     S961 a report waited for the 5-minute heartbeat (16-25 Nov: none of the
     five evening exports came by this road). Now every tick (5 s) the agent
     LOOKS at the two export folders -- names, sizes and times only, nothing
     opened -- and when a Docterz report has changed and has stood still for
     20 seconds it is posted at once through job 5's own signed road, with
     job 5's own checks. Only after the server has answered a heartbeat since
     the agent started; a refusal or no answer waits a minute before the next
     try, and the heartbeat's pass stays the fallback. Repeated refusals wait longer
     each time (1, 2, 4 ... up to 30 minutes).
''')

rep('''    "server_jobs_seconds": 60,
}''', '''    "server_jobs_seconds": 60,
    "fast_upload": True,          # S961: post a new report within ~half a minute
    "fast_hold_seconds": 60,      # S961: after a failed fast post, wait this long (doubling, min 30 s, max 30 min)
}''')

# the report half of direct_pass becomes its own function, shared by both passes
rep('''    if beat.get("switched_off"):
        return
    downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    folders = [drive_sub(beat.get("my_drive"), cfg["docterz_rel"]), downloads]
    sent = _sent_read()
    done = 0
''', '''    if beat.get("switched_off"):
        return
    _done, failed = report_pass(st, cfg, beat.get("my_drive"), "heartbeat")
    if failed:
        st["fast"]["again"] = True   # S961: the fast lane tries again after its hold


def report_folders(cfg, my_drive):
    downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    return [drive_sub(my_drive, cfg["docterz_rel"]), downloads]


def report_pass(st, cfg, my_drive, road):
    """Post every report the server has not had (at most upload_max_files).
    Returns (posted, failed): failed is True when the server did not answer
    or refused for a reason other than the file itself."""
    up = st["upload"]
    folders = report_folders(cfg, my_drive)
    sent = _sent_read()
    done = 0
    failed = False
''')

rep('''        if err and code != 400:
            up["last_error"] = err
            log("direct upload: a %s report was not accepted -- %s" % (kind, err))
            break''', '''        if err and code != 400:
            up["last_error"] = err
            failed = True
            log("direct upload: a %s report was not accepted -- %s" % (kind, err))
            break''')
rep('''        if not _sent_write(sent):
            break''', '''        if not _sent_write(sent):
            failed = True            # S961: never post the same bytes again and again
            break''')

rep('''        if verdict in ("TAKEN", "ALREADY"):
            up["reports_sent"] += 1
            up["last_report_at"] = iso()
        log("direct upload: %s report for %s -> %s" % (
            kind, (ans or {}).get("day") or "?", verdict))
''', '''        if verdict in ("TAKEN", "ALREADY"):
            up["reports_sent"] += 1
            up["last_report_at"] = iso()
            if road == "fast":
                up["fast_sent"] += 1
                up["fast_last_at"] = iso()
                up["fast_last_after_save_s"] = int(time.time() - m)
        log("direct upload%s: %s report for %s -> %s" % (
            " (at once)" if road == "fast" else "", kind,
            (ans or {}).get("day") or "?", verdict))
    return done, failed


def fast_look(cfg, my_drive):
    """(signature, settling): the Docterz reports by NAME in the two folders,
    as (path, size, mtime) -- listings and stat only, no file is opened.
    settling is True while a report changed less than 20 s ago."""
    sig, settling, t = [], False, time.time()
    for folder in report_folders(cfg, my_drive):
        try:
            names = os.listdir(folder) if folder else []
        except OSError:
            continue
        for n in names:
            if not _report_kind(n.lower()):
                continue
            p = os.path.join(folder, n)
            try:
                size, m = os.path.getsize(p), os.path.getmtime(p)
            except OSError:
                continue
            if t - m > cfg["upload_days"] * 86400:
                continue
            sig.append((p, size, m))
            if 0 <= t - m < 25 or -2 < t - m < 0:
                settling = True          # a time far in the future (a clock change) is not waited on
    sig.sort()
    return tuple(sig), settling


def _unread_recent(sig, cache):
    """A report that has stood still but could not be read yet (Drive or the
    antivirus holding it): looked at again for two minutes after it was saved."""
    t = time.time()
    return any(20 <= t - m <= 120 and (p, size, m) not in cache for p, size, m in sig)


def fast_pass(st, cfg):
    """S961: every tick. Posts a changed report at once; quiet otherwise.
    Never raises out (the caller logs)."""
    fu = st["fast"]
    if not (cfg.get("direct_upload") and cfg.get("fast_upload")):
        return
    up = st["upload"]
    if up["ok_at"] is None or up["fail_streak"]:
        return                       # the server has not answered a heartbeat: the 5-minute pass decides
    if time.time() < fu["hold_until"]:
        return
    my_drive = st.get("my_drive")
    sig, settling = fast_look(cfg, my_drive)
    if sig == fu["sig"] and not fu["again"]:
        return
    first = fu["sig"] is None
    fu["sig"] = sig
    fu["again"] = settling
    if first:
        return                       # the first look after a start only learns the folders
    done, failed = report_pass(st, cfg, my_drive, "fast")
    if failed:
        try:
            base = max(30.0, float(cfg.get("fast_hold_seconds", 60) or 60))
        except (TypeError, ValueError):
            base = 60.0
        fu["hold_until"] = time.time() + min(1800.0, base * 2 ** min(fu["fails"], 5))
        fu["fails"] += 1
        fu["again"] = True
        return
    fu["fails"] = 0
    if done >= cfg["upload_max_files"]:
        fu["again"] = True           # more may be waiting: look again next tick
    elif _unread_recent(sig, st["upload_cache"]):
        fu["again"] = True
''')

# a clock set back must not leave the fast lane on hold for hours (second look, S528)
rep('''            if st.get("job") and gap > 0:
                st["job"]["started"] += gap''', '''            if st.get("job") and gap > 0:
                st["job"]["started"] += gap
            if gap < 0:
                st["fast"]["hold_until"] = 0.0''')

# remember where My Drive is, for the tick's look (searched fresh at each heartbeat)
rep('''            try:
                beat, procs = build_beat(st, cfg)
                write_beat(beat, cfg)''', '''            try:
                beat, procs = build_beat(st, cfg)
                st["my_drive"] = beat.get("my_drive")
                write_beat(beat, cfg)''')

rep('''        if not st.get("job") and not off:
            if os.path.exists(RESTART_FLAG):''', '''        if not off:
            try:
                fast_pass(st, cfg)
            except Exception as ex:                            # noqa: BLE001
                st["fast"]["hold_until"] = time.time() + 60
                log("fast upload FAILED: %s: %s" % (ex.__class__.__name__, ex))
            # time spent talking to the server is not a clock jump
            last_tick = time.time()

        if not st.get("job") and not off:
            if os.path.exists(RESTART_FLAG):''')

rep('''            "upload": {"ok_at": None, "fail_streak": 0, "last_error": None,
                       "reports_sent": 0, "last_report_at": None},''',
'''            "upload": {"ok_at": None, "fail_streak": 0, "last_error": None,
                       "reports_sent": 0, "last_report_at": None,
                       "fast_sent": 0, "fast_last_at": None,
                       "fast_last_after_save_s": None},
            "fast": {"sig": None, "again": False, "hold_until": 0.0, "fails": 0},
            "my_drive": None,''')

rep('''            "last_report_sent": st["upload"]["last_report_at"],
        },''', '''            "last_report_sent": st["upload"]["last_report_at"],
            "at_once": bool(cfg.get("fast_upload")),
            "sent_at_once_since_start": st["upload"]["fast_sent"],
            "last_sent_at_once": st["upload"]["fast_last_at"],
            "last_seconds_after_save": st["upload"]["fast_last_after_save_s"],
        },''')

open(dst, "wb").write(t.encode("utf-8"))
print("TO", hashlib.md5(t.encode("utf-8")).hexdigest(), len(t.encode("utf-8")))
