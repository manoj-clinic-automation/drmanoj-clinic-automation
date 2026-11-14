#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""att_silence_watch.py -- kit S830_ATT_SILENCE_ALERT (session S460, 14-Nov-2026, the parent). NEW. Answers F-1402.

WHY. From 13-Nov 11:17 to 14-Nov 11:44 IST no punch reached the server and nothing told anyone: the machine's clock had frozen
and it then shut itself down. The console's freshness page watches the punch FILE with a 74-hour window, and att_doctor.py's
rule fires only at 14:00 on a day with ZERO punches -- nothing looks at the gap since the machine last called.

WHAT IT DOES. Run by cron every 5 minutes. It changes nothing the machine sees: /root/attlistener_v2.py is NOT touched (D247).
  * THE MACHINE'S CONTACT. The machine calls the listener about every 12 seconds, each call a short connection on port
    8041. Its last contact is the newest of:
      - a connection on port 8041 FROM THE MACHINE'S OWN ADDRESS, seen now in the kernel's tables: /proc/net/nf_conntrack
        (a closed connection stays there about two minutes) and /proc/net/tcp, tcp6. The machine's address is learnt from
        /root/attlistener_sources.jsonl -- the address its punches and its own calls (they carry a 'request_code') came
        from -- and kept in the state; a stray caller from any other address is never the machine;
      - the newest line of /root/attlistener_sources.jsonl from the machine (S535: every punch, and the first 30 other calls
        of each day);
      - the newest 'received_at' in /root/punches.csv.
    SILENCE IS JUDGED ONLY ONCE THIS BOX HAS SHOWN IT CAN SEE THE MACHINE'S CONNECTIONS (the first time one is seen, kept in
    the state as conn_seen_iso): a box whose tables never show them could not tell silence from blindness. Until then the
    10:00 rule and the clock rule work, and the line says so.
  * SILENCE: on a working day (Monday-Saturday), inside clinic hours (the earliest start to the latest end of the active
    staff's weekday shifts in staff_master.csv, through att_core.load_staff; 10:00-20:00 when that cannot be read), at
    least 30 minutes after the start, no contact for 30 minutes -> ONE message to the owner for that silence. When contact
    comes back after a told silence -> ONE message saying so.
  * NO PUNCH BY 10:00 on a working day (nothing received today) -> ONE message that day. When the machine is also silent,
    that message stands for the silence too (no second message until the machine is back).
  * THE MACHINE'S CLOCK (S792 records it): a punch today whose machine time differs from the time stored for it by more than
    5 minutes (the listener kept the server's time), or two punches of today that reached the server 2 minutes or more apart
    yet carry the same machine time -> ONE message that day.
  * THE CONSOLE LINE: every run writes last_ok_iso (nothing wrong now) or last_failure_iso (silent / no punch now) into its
    state file; the freshness page's leg "attendance machine contact" reads them (the installer adds the leg), so the
    console's "N of M feeds fresh" counts it and names it when it is red -- and goes red if this watcher stops.

HOW IT REACHES THE OWNER. The portal's own Web Push (ring_common.push_user, as docterz_missing_alert.py and callback_clock.py),
to the owner's login; when no device takes it, the private ntfy topic in /root/finance/freshness.conf (never printed). A
message neither took is tried again on the next runs, three tries a day at most. Each try is counted BEFORE it is made, so a
run stopped mid-way never sends twice.

It only READS the punch file, the source log, the staff master and /proc. It writes its state file (and .lock) and, only when
something changes, one line on stdout (cron appends it to /root/att_silence_watch.log, cut back past 200 KB). No staff name,
no number, no address is in a message or a line. Any error = one line, exit 0.
Off switch: /root/finance/_off/ALL_OFF or /root/finance/_off/ATT_SILENCE_OFF (nothing judged, nothing written; the
freshness leg turns red within the hour, which is honest).

CLI:  att_silence_watch.py               the run (what cron calls)
      att_silence_watch.py --dry [--now 'YYYY-MM-DD HH:MM']   what it WOULD send; sends nothing, writes nothing
      att_silence_watch.py --probe        one line: what this box lets it read (the installer's gate)
      att_silence_watch.py --seed         the installer's first run: records the listener's count and the newest contact,
                                          writes last_ok_iso, judges nothing and sends nothing (the next cron run judges)
Stdlib only (+ ring_common from /root/portal for the push, att_core from /root for the hours: either absent = said, and
the fallback used).
"""
import argparse
import datetime as dt
import json
import os
import sys

VERSION = "S830 1"
ROOT = os.environ.get("ASW_ROOT", "/root")
PUNCH_CSV = os.environ.get("ATT_PUNCH_CSV", os.path.join(ROOT, "punches.csv"))
SOURCE_LOG = os.environ.get("ATT_SOURCE_LOG", os.path.join(ROOT, "attlistener_sources.jsonl"))
PROC = os.environ.get("ASW_PROC", "/proc")
STATE = os.environ.get("ASW_STATE", os.path.join(ROOT, "att_silence_watch.state.json"))
LOG = os.environ.get("ASW_LOG", os.path.join(ROOT, "att_silence_watch.log"))
OFF_DIR = os.environ.get("FINANCE_OFF_DIR", os.path.join(ROOT, "finance", "_off"))
OFF_NAMES = ("ALL_OFF", "ATT_SILENCE_OFF")
NTFY_CONF = os.environ.get("ASW_NTFY_CONF", os.path.join(ROOT, "finance", "freshness.conf"))
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", os.path.join(ROOT, "portal"))
PORT = int(os.environ.get("ATT_LISTENER_PORT", "8041"))
LISTENER_MARK = b"attlistener_v2.py"
SILENT_MIN = 30                  # minutes without contact, inside clinic hours
PUNCH_BY = dt.time(10, 0)        # a working day with no punch received by this time
KEEP_IPS = 4                     # the machine's addresses remembered (its broadband address can change)
CLOCK_OFF_MIN = 5                # S792's own threshold
STUCK_GAP_MIN = 2
HOURS_FALLBACK = (dt.time(10, 0), dt.time(20, 0))
START_CLAMP = (dt.time(8, 0), dt.time(11, 0))
END_CLAMP = (dt.time(17, 0), dt.time(22, 0))
MAX_TRIES = 3
MAX_SILENCES = 3                 # silences told in one day; after that the day's silences are only on the console
KEEP_DAYS = 30
TAIL_BYTES = 1 << 20
LOG_CUT = 200 * 1024
OWNER = ("manoj",)               # the owner's portal login (callback_clock.OWNER)
OWNER_URL = "/finance/console"
TITLE = "Attendance machine"
LOOP4 = ("127.", "0.0.0.0")


# ------------------------------------------------------------------ small helpers
def fmt_day(d):
    return d.strftime("%a %d-%b")


def fmt_t(t, today):
    if t is None:
        return "(nothing on record)"
    return t.strftime("%H:%M") if t.date() == today else t.strftime("%a %d-%b %H:%M")


def heard(t, today):
    return "was last heard from at %s" % fmt_t(t, today) if t else "has not been heard from at all"


def dur(mins):
    mins = int(mins)
    if mins < 60:
        return "%d min" % mins
    h, m = divmod(mins, 60)
    return "%d h %02d min" % (h, m) if h < 48 else "%d days" % (mins // 1440)


def parse_dt(s):
    try:
        return dt.datetime.strptime(str(s).strip()[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:                                    # noqa: BLE001
        return None


def iso(t):
    return t.strftime("%Y-%m-%d %H:%M:%S") if t else ""


def tail_lines(path, nbytes=TAIL_BYTES):
    """The last nbytes of a text file as whole lines (the first, partial, line dropped when the file is longer)."""
    with open(path, "rb") as fh:
        fh.seek(0, 2)
        size = fh.tell()
        start = max(0, size - nbytes)
        fh.seek(start)
        data = fh.read()
    lines = data.decode("utf-8", "replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]
    return lines


def off_switch(off_dir=None):
    d = off_dir or OFF_DIR
    for n in OFF_NAMES:
        if os.path.exists(os.path.join(d, n)):
            return n
    return ""


# ------------------------------------------------------------------ the reads (each returns its value and never raises)
def read_punches(path, today):
    """-> (rows_today, newest_received, ok). rows_today: [(stored, received, machine)] for punches RECEIVED today."""
    rows, newest = [], None
    try:
        for line in tail_lines(path):
            p = line.strip().split(",")
            if len(p) < 5 or p[0] == "user_id":
                continue
            stored, rec = parse_dt(p[1]), parse_dt(p[4])
            mach = parse_dt(p[5]) if len(p) >= 6 and p[5].strip() else stored
            if rec is None:
                continue
            if newest is None or rec > newest:
                newest = rec
            if rec.date() == today:
                rows.append((stored, rec, mach))
        return rows, newest, True
    except FileNotFoundError:
        return rows, newest, True                        # no punch file yet = no punch
    except Exception:                                    # noqa: BLE001
        return rows, newest, False


def is_loop(ip):
    ip = str(ip or "")
    return (not ip) or ip.startswith(LOOP4) or ip in ("::1", "::") or ip.startswith("::ffff:127.")


def read_sources(path):
    """-> (newest time of a line from the machine, {address: newest time} of the machine's lines, ok). A line is the
    machine's when it is a punch or carries a request_code (the machine's own calls do; a stray caller's do not)."""
    newest, ips = None, {}
    try:
        for line in tail_lines(path, TAIL_BYTES // 2):
            try:
                o = json.loads(line)
            except Exception:                            # noqa: BLE001
                continue
            if not isinstance(o, dict) or is_loop(o.get("ip")) or not (o.get("punch") or o.get("request_code")):
                continue
            t = parse_dt(o.get("t"))
            if t is None:
                continue
            if newest is None or t > newest:
                newest = t
            ip = str(o.get("ip"))
            if ip.startswith("::ffff:"):
                ip = ip[7:]
            if ip not in ips or t > ips[ip]:
                ips[ip] = t
        return newest, ips, True
    except FileNotFoundError:
        return None, ips, True
    except Exception:                                    # noqa: BLE001
        return None, ips, False


def listener_proc(proc=None):
    """-> (pid, start_ticks, syscr) of the listener, or (None, None, None). Only its presence is used (the probe, the line):
    a socket's reads are not counted in /proc/<pid>/io, so its count says nothing about the machine's calls."""
    proc = proc or PROC
    me = str(os.getpid())
    try:
        names = os.listdir(proc)
    except OSError:
        return None, None, None
    for n in sorted(names):
        if not n.isdigit() or n == me:
            continue
        try:
            with open(os.path.join(proc, n, "cmdline"), "rb") as fh:
                cmd = fh.read()
        except OSError:
            continue
        if LISTENER_MARK not in cmd or b"att_silence_watch" in cmd:
            continue
        start = syscr = None
        try:
            with open(os.path.join(proc, n, "stat"), "r") as fh:
                st = fh.read()
            start = st[st.rfind(")") + 2:].split()[19]
        except Exception:                                # noqa: BLE001
            start = None
        try:
            with open(os.path.join(proc, n, "io"), "r") as fh:
                for line in fh:
                    if line.startswith("syscr:"):
                        syscr = int(line.split()[1])
        except Exception:                                # noqa: BLE001
            syscr = None
        return int(n), start, syscr
    return None, None, None


def _hex_ip(h):
    """The address part of a /proc/net/tcp{,6} field -> dotted IPv4, or the hex for IPv6 ('' when unreadable)."""
    a = h.split(":")[0].upper()
    try:
        if len(a) == 8:
            return ".".join(str(int(a[i:i + 2], 16)) for i in (6, 4, 2, 0))
        if len(a) == 32 and a.startswith("0000000000000000FFFF0000"):
            return _hex_ip(a[24:])
        return a.lower()
    except ValueError:
        return ""


def conn_ips(proc=None, port=PORT):
    """-> (addresses with a connection to the port now -- any state but LISTEN --, which tables could be read)."""
    proc = proc or PROC
    ips, read = set(), []
    want = "%04X" % port
    for name in ("tcp", "tcp6"):
        try:
            with open(os.path.join(proc, "net", name), "r") as fh:
                lines = fh.read().splitlines()[1:]
            read.append(name)
        except OSError:
            continue
        for line in lines:
            f = line.split()
            if len(f) < 4 or f[1].split(":")[-1].upper() != want or f[3] == "0A":
                continue
            ip = _hex_ip(f[2])
            if ip and not is_loop(ip):
                ips.add(ip)
    try:
        with open(os.path.join(proc, "net", "nf_conntrack"), "r") as fh:
            ct = fh.read().splitlines()
        read.append("conntrack")
        tag = "dport=%d" % port
        for line in ct:
            f = line.split()
            src = dport = None
            for x in f:
                if src is None and x.startswith("src="):
                    src = x[4:]
                elif dport is None and x.startswith("dport="):
                    dport = x
                    break
            if dport == tag and src and not is_loop(src):
                ips.add(src)
    except OSError:
        pass
    return ips, read


def staff_hours(loader=None):
    """-> (start, end, how). The earliest start / latest end of the active staff's weekday shifts, clamped."""
    try:
        if loader is None:
            if ROOT not in sys.path:
                sys.path.insert(0, ROOT)
            import att_core                              # noqa: PLC0415
            import att_config as cfg                     # noqa: PLC0415
            ex = set(getattr(cfg, "EXCLUDE_IDS", ()) or ())

            def loader():
                return {u: i for u, i in att_core.load_staff().items() if u not in ex}
        staff = loader()
        starts = [i["wd_start"] for i in staff.values() if i.get("active", True) and i.get("wd_start")]
        ends = [i["wd_end"] for i in staff.values() if i.get("active", True) and i.get("wd_end")]
        if not starts or not ends:
            raise ValueError("no shift times")
        s = min(max(min(starts), START_CLAMP[0]), START_CLAMP[1])
        e = min(max(max(ends), END_CLAMP[0]), END_CLAMP[1])
        return s, e, "staff shifts"
    except Exception:                                    # noqa: BLE001
        return HOURS_FALLBACK[0], HOURS_FALLBACK[1], "fallback"


def clock_issue(rows):
    """-> (kind, words) or None, from today's punches."""
    worst = None
    for stored, rec, mach in rows:
        if stored and mach:
            off = (stored - mach).total_seconds() / 60.0
            if abs(off) > CLOCK_OFF_MIN and (worst is None or abs(off) > abs(worst[0])):
                worst = (off, rec, mach)
    if worst:
        off, rec, mach = worst
        return "off", ("The attendance machine's clock is wrong: a punch that reached the server at %s carried the machine "
                       "time %s (%s %s). The server's time was kept for it. Please have the machine's date and time set."
                       % (rec.strftime("%H:%M"), mach.strftime("%d-%b %H:%M"), dur(abs(off)),
                          "behind" if off > 0 else "ahead"))
    seen = {}
    for stored, rec, mach in rows:
        if mach:
            seen.setdefault(mach, []).append(rec)
    for mach, recs in sorted(seen.items()):
        if len(recs) >= 2:
            span = (max(recs) - min(recs)).total_seconds() / 60.0
            if span >= STUCK_GAP_MIN:
                return "stuck", ("The attendance machine's clock seems stuck: %d punches that reached the server %s apart all "
                                 "carry the same machine time %s. Please have the machine's date and time set."
                                 % (len(recs), dur(span), mach.strftime("%H:%M:%S")))
    return None


# ------------------------------------------------------------------ state
def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and isinstance(d.get("told"), dict):
            return d, ""
        raise ValueError("not this script's state")
    except FileNotFoundError:
        return {"told": {}}, ""
    except Exception as e:                               # noqa: BLE001
        try:
            os.replace(path, path + ".unreadable")
        except OSError:
            pass
        return {"told": {}}, " (the state file could not be read -- %s -- set aside, a fresh one started)" % type(e).__name__


def read_state_ro(path):
    """The state for --dry and --probe: read, never set aside."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) and isinstance(d.get("told"), dict) else {"told": {}}
    except Exception:                                    # noqa: BLE001
        return {"told": {}}


def save_state(path, d, today):
    keep = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
    d["told"] = {k: v for k, v in d.get("told", {}).items() if str(k)[:10] >= keep}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.chmod(tmp, 0o644)                                 # the freshness collector reads it; it holds no secret
    os.replace(tmp, path)


def take_lock(path):
    try:
        import fcntl                                     # noqa: PLC0415
        fd = os.open(path + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
    except Exception:                                    # noqa: BLE001
        return None, "error"
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd, ""
    except OSError:
        os.close(fd)
        return None, "busy"


# ------------------------------------------------------------------ the roads to the owner
def get_pusher(pusher=None):
    if pusher is not None:
        return pusher
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import ring_common as rc                         # noqa: PLC0415
        return rc.push_user
    except Exception:                                    # noqa: BLE001
        return None


def device_count():
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import ring_common as rc                         # noqa: PLC0415
        return len(rc.subs_for(OWNER[0]))
    except Exception:                                    # noqa: BLE001
        return None


def push(pusher, title, body, tag):
    s = f = 0
    for w in OWNER:
        try:
            a, b = pusher(w, {"title": title, "body": body, "url": OWNER_URL, "tag": tag, "ttl": 43200,
                              "requireInteraction": True, "renotify": True})
            a, b = int(a or 0), int(b or 0)
        except Exception:                                # noqa: BLE001
            a, b = 0, 1
        s, f = s + a, f + b
    return s, f


def ntfy_url(conf=None):
    try:
        with open(conf or NTFY_CONF, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "NTFY_URL":
                        return v.strip()
    except OSError:
        pass
    return ""


def send_ntfy(title, body, conf=None):
    url = ntfy_url(conf)
    if not url:
        return False, "no ntfy topic is set"
    try:
        import urllib.request                            # noqa: PLC0415
        req = urllib.request.Request(url, data=str(body).encode("utf-8"), method="POST",
                                     headers={"Title": title, "Priority": "high", "Tags": "warning"})
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:                               # noqa: BLE001
        return False, "the ntfy topic did not take it (%s)" % type(e).__name__
    return True, "the ntfy topic took it"


# ------------------------------------------------------------------ the judgement (pure)
def judge(now, st, ev, hours, rows, clock):
    """now: the run's time. st: the state (read only here). ev: {'contact': newest contact or None, 'fresh': contact seen
    by THIS run}. hours: (start, end). rows: today's punches. clock: clock_issue(rows).
    -> {'msgs': [(kind, body)], 'episode': new episode or None, 'failing': bool, 'summary': str}"""
    today = now.date()
    working = now.weekday() != 6
    start, end = hours
    last = ev["contact"]
    proven = ev.get("proven", True)
    silent_for = None if last is None else (now - last).total_seconds() / 60.0
    in_hours = working and start <= now.time() <= end
    after_grace = in_hours and now >= dt.datetime.combine(today, start) + dt.timedelta(minutes=SILENT_MIN)
    silent = after_grace and proven and (last is None or silent_for >= SILENT_MIN)
    punch_by = max(PUNCH_BY, (dt.datetime.combine(today, start) + dt.timedelta(minutes=SILENT_MIN)).time())
    nopunch = working and punch_by <= now.time() <= end and not rows
    told = st.get("told", {})
    ep = st.get("episode") if isinstance(st.get("episode"), dict) else None
    msgs = []
    new_ep = ep
    # contact back after a told silence
    if ep and ep.get("told") and last is not None and last > (parse_dt(ep.get("since")) or dt.datetime.min) \
            and (silent_for is None or silent_for < SILENT_MIN):
        gap = (last - (parse_dt(ep.get("since")) or last)).total_seconds() / 60.0
        msgs.append(("back", "The attendance machine is in contact again (%s), after %s of silence since %s. Punches made "
                             "meanwhile are sent by the machine itself once it is connected."
                             % (fmt_t(last, today), dur(gap), fmt_t(parse_dt(ep.get("since")), today))))
        new_ep = None
    elif ep and not ep.get("told") and last is not None and last > (parse_dt(ep.get("since")) or dt.datetime.min):
        new_ep = None                                    # an untold silence ended: nothing to say
    if nopunch and not (told.get(today.isoformat() + "|nopunch") or {}).get("told"):
        if not proven:
            body = ("No punch has reached the server today (%s) by %s. Please check that the attendance machine is "
                    "switched on and on the clinic Wi-Fi." % (fmt_day(today), now.strftime("%H:%M")))
        elif last is None or silent_for >= SILENT_MIN:
            body = ("No punch has reached the server today (%s) by %s. The attendance machine %s. "
                    "Please check that it is switched on and on the clinic Wi-Fi." % (fmt_day(today), now.strftime("%H:%M"),
                                                                                    heard(last, today)))
            if new_ep is None:
                new_ep = {"since": iso(last) if last else iso(dt.datetime.combine(today, dt.time(0, 0))), "told": False}
            if new_ep.get("told") and str(new_ep.get("told_at") or "")[:10] == today.isoformat():
                body = None                              # this silence was told today: no second message for it
            else:
                new_ep = dict(new_ep, by="nopunch")
        else:
            body = ("No one has punched in today (%s) by %s, though the attendance machine is in contact with the server."
                    % (fmt_day(today), now.strftime("%H:%M")))
        if body:
            msgs.append(("nopunch", body))
    if silent:
        if new_ep is None:
            new_ep = {"since": iso(last) if last else iso(dt.datetime.combine(today, dt.time(0, 0))), "told": False}
        n_told = sum(1 for k, v in told.items() if k.startswith(today.isoformat() + "|silent|") and (v or {}).get("told"))
        if not new_ep.get("told") and new_ep.get("by") != "nopunch" and n_told < MAX_SILENCES:
            gone = ("since %s (%s)" % (fmt_t(last, today), dur(silent_for))) if last is not None else "at all on record"
            msgs.append(("silent", "No contact from the attendance machine %s. Punches are not reaching the server. "
                                   "Please check that it is switched on and on the clinic Wi-Fi." % gone))
    if clock and working and not (told.get(today.isoformat() + "|clock") or {}).get("told"):
        msgs.append(("clock", clock[1]))
    failing = bool(silent or nopunch)
    summary = "%s; %s; contact %s" % ("working day" if working else "Sunday",
                                       "in hours %s-%s" % (start.strftime("%H:%M"), end.strftime("%H:%M")) if in_hours
                                       else "outside hours",
                                       ("SILENT" if silent else "ok") if last or silent else "none on record")
    if nopunch:
        summary += "; no punch today"
    if not proven:
        summary += "; silence not judged yet (the machine's connections not yet seen on this box)"
    return {"msgs": msgs, "episode": new_ep, "failing": failing, "summary": summary}


# ------------------------------------------------------------------ one run
def gather(now, st, proc=None, punch_csv=None, source_log=None):
    """-> (ev, rows, notes, probe, keep). Reads only."""
    today = now.date()
    rows, newest_rec, ok_p = read_punches(punch_csv or PUNCH_CSV, today)
    src, src_ips, ok_s = read_sources(source_log or SOURCE_LOG)
    pid, _pstart, _syscr = listener_proc(proc)
    seen_ips, tables = conn_ips(proc)
    known = dict(st.get("machine_ips") or {})
    for ip, t in src_ips.items():
        if ip not in known or iso(t) > str(known[ip]):
            known[ip] = iso(t)
    known = dict(sorted(known.items(), key=lambda kv: str(kv[1]), reverse=True)[:KEEP_IPS])
    cands, how = [], []
    prev = parse_dt(st.get("last_contact_iso"))
    if prev:
        cands.append(prev)
    by_conn = sorted(ip for ip in seen_ips if ip in known)
    if by_conn:
        cands.append(now)
        how.append("connection")
    for t, label in ((src, "source log"), (newest_rec, "punch file")):
        if t and t <= now + dt.timedelta(minutes=2):
            cands.append(t)
            if prev is None or t > prev:
                how.append(label)
    contact = max(cands) if cands else None
    notes = []
    if not ok_p:
        notes.append("the punch file could not be read")
    if not ok_s:
        notes.append("the source log could not be read")
    if pid is None:
        notes.append("the listener process was not found")
    if not tables:
        notes.append("no connection table could be read")
    probe = {"pid": pid is not None, "tables": tables, "punches": ok_p, "sources": ok_s, "newest_punch": newest_rec,
             "newest_source": src, "known_ips": len(known), "seen_now": len(by_conn)}
    conn_seen = st.get("conn_seen_iso") or (iso(now) if by_conn else "")
    return ({"contact": contact, "how": ", ".join(how), "proven": bool(conn_seen)}, rows, notes, probe,
            {"machine_ips": known, "conn_seen_iso": conn_seen})


def run(now=None, dry=False, state=None, pusher=None, ntfy=None, hours=None, proc=None, punch_csv=None, source_log=None,
        off_dir=None):
    """One run. -> {'line': what to print ('' = nothing), 'sent': [kinds told], 'tried': [kinds], 'result': judge's}."""
    now = now or dt.datetime.now().replace(microsecond=0)
    state = state or STATE
    res = {"line": "", "sent": [], "tried": [], "result": None}
    o = off_switch(off_dir)
    if o:
        res["line"] = ""                                 # off: nothing judged, nothing written
        res["off"] = o
        return res
    fd = None
    if not dry:
        fd, why = take_lock(state)
        if fd is None:
            res["line"] = "" if why == "busy" else "%s ERROR: the state's lock could not be made -- nothing done" % iso(now)
            return res
    try:
        st, st_note = load_state(state) if not dry else (read_state_ro(state), "")
        ev, rows, notes, _probe, lst = gather(now, st, proc, punch_csv, source_log)
        hrs = hours or staff_hours()[:2]
        clk = clock_issue(rows)
        r = judge(now, st, ev, hrs, rows, clk)
        res["result"] = r
        today = now.date()
        if dry:
            res["line"] = "DRY %s: %s%s | would send: %s" % (iso(now), r["summary"],
                                                           (" | " + "; ".join(notes)) if notes else "",
                                                           " / ".join("%s: %s" % m for m in r["msgs"]) or "nothing")
            return res
        told = st.setdefault("told", {})
        said = []
        p = None
        for kind, body in r["msgs"]:
            since = str((st.get("episode") or r["episode"] or {}).get("since"))
            key = today.isoformat() + "|" + kind + ("|" + since if kind in ("back", "silent") else "")
            ent = told.get(key) or {}
            if ent.get("told"):
                continue
            tries = int(ent.get("tries") or 0)
            if tries >= MAX_TRIES:
                continue
            ent.update(tries=tries + 1, at=iso(now), told=False)
            told[key] = ent
            save_state(state, dict(st, told=told), today)  # the try is counted BEFORE it is made
            res["tried"].append(kind)
            p = get_pusher(pusher) if p is None else p
            sent = 0
            if p is not None:
                sent, _f = push(p, TITLE, body, "att-" + kind)
            how = "pushed to %d device(s)" % sent if sent else ""
            if not sent:
                went, nhow = (ntfy or send_ntfy)(TITLE, body)
                how = ("no device took the push; " if p is not None else "the portal's push could not be loaded; ") + nhow
                sent = 1 if went else 0
            if sent:
                ent.update(told=True, how=how)
                res["sent"].append(kind)
                if kind in ("silent", "nopunch") and r["episode"] is not None and \
                        (kind == "silent" or r["episode"].get("by") == "nopunch"):
                    r["episode"].update(told=True, told_at=iso(now))
            else:
                ent.update(how=how)
            said.append("%s (try %d): %s" % (kind, tries + 1, how))
        st["told"] = told
        back_key = today.isoformat() + "|back|" + str((st.get("episode") or {}).get("since"))
        if any(k == "back" for k, _b in r["msgs"]) and not (told.get(back_key) or {}).get("told") \
                and int((told.get(back_key) or {}).get("tries") or 0) < MAX_TRIES:
            r["episode"] = st.get("episode")             # the 'back' message is tried again on the next run
        st["episode"] = r["episode"]
        if ev["contact"]:
            st["last_contact_iso"] = iso(ev["contact"])
        st.update(lst, version=VERSION, last_run_iso=iso(now), hours="%s-%s" % (hrs[0].strftime("%H:%M"), hrs[1].strftime("%H:%M")))
        if r["failing"]:
            st["last_failure_iso"] = iso(now)
            st.setdefault("last_ok_iso", "")
        else:
            st["last_ok_iso"] = iso(now)
            st.setdefault("last_failure_iso", "")
        changed = r["summary"] != st.get("last_summary") or said or st_note or (notes and notes != st.get("last_notes"))
        st["last_summary"] = r["summary"]
        st["last_notes"] = notes
        save_state(state, st, today)
        if changed:
            res["line"] = "%s %s%s%s%s" % (iso(now), r["summary"], (" | sent " + "; ".join(said)) if said else "",
                                           (" | " + "; ".join(notes)) if notes else "", st_note)
        return res
    except Exception as e:                               # noqa: BLE001
        res["line"] = "%s ERROR %s: %s -- nothing more done" % (iso(now), type(e).__name__, str(e)[:160])
        return res
    finally:
        if fd is not None:
            os.close(fd)


def seed(now=None, state=None, proc=None, punch_csv=None, source_log=None):
    """The installer's first run: the baseline only. -> the line it prints."""
    now = now or dt.datetime.now().replace(microsecond=0)
    state = state or STATE
    fd, why = take_lock(state)
    if fd is None:
        return "SEED: the state is busy (%s) -- the next cron run starts it" % why
    try:
        st, _n = load_state(state)
        ev, _rows, notes, _pr, lst = gather(now, st, proc, punch_csv, source_log)
        if ev["contact"]:
            st["last_contact_iso"] = iso(ev["contact"])
        st.update(lst, version=VERSION, last_run_iso=iso(now), last_ok_iso=iso(now))
        st.setdefault("last_failure_iso", "")
        save_state(state, st, now.date())
        return "SEED %s: the baseline is written (last contact %s)%s" % (iso(now), iso(ev["contact"]) or "none on record",
                                                                         (" | " + "; ".join(notes)) if notes else "")
    finally:
        os.close(fd)


def probe(now=None):
    now = now or dt.datetime.now().replace(microsecond=0)
    st = read_state_ro(STATE)
    _ev, _rows, _notes, pr, _l = gather(now, st)
    s, e, how = staff_hours()
    dev = device_count()
    return ("PROBE listener=%s tables=%s machine_addresses=%d seen_now=%d punches=%s sources=%s hours=%s-%s(%s) devices=%s "
            "ntfy=%s newest_punch=%s newest_source=%s" % (
                "yes" if pr["pid"] else "no", "+".join(pr["tables"]) or "none", pr["known_ips"], pr["seen_now"],
                "ok" if pr["punches"] else "no", "ok" if pr["sources"] else "no", s.strftime("%H:%M"), e.strftime("%H:%M"),
                how, "?" if dev is None else dev, "yes" if ntfy_url() else "no",
                pr["newest_punch"].strftime("%d-%b_%H:%M") if pr["newest_punch"] else "none",
                pr["newest_source"].strftime("%d-%b_%H:%M") if pr["newest_source"] else "none"))


def cut_log(path=None):
    path = path or LOG
    try:
        if os.path.getsize(path) > LOG_CUT:
            with open(path, "rb") as fh:
                fh.seek(-LOG_CUT // 2, 2)
                keep = fh.read()
            keep = keep[keep.find(b"\n") + 1:]
            with open(path, "wb") as fh:
                fh.write(keep)
    except OSError:
        pass


def main(argv=None):
    ap = argparse.ArgumentParser(description="the attendance machine's silence watch (S830)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--now", default="")
    a = ap.parse_args(argv)
    if a.seed:
        print(seed())
        return 0
    if a.probe:
        print(probe())
        return 0
    now = None
    if a.now:
        try:
            now = dt.datetime.strptime(a.now, "%Y-%m-%d %H:%M")
        except ValueError:
            print("ERROR: --now wants 'YYYY-MM-DD HH:MM'")
            return 0
        a.dry = True                                     # a dated run never sends and never writes
    r = run(now=now, dry=a.dry)
    if r["line"]:
        print(r["line"], flush=True)
    if not a.dry:
        cut_log()
    return 0


if __name__ == "__main__":
    sys.exit(main())
