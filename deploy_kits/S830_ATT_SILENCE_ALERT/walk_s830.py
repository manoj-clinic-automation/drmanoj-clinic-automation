#!/usr/bin/env python3
"""walk_s830.py -- the walk of kit S830_ATT_SILENCE_ALERT on a made-up root (no real path, no network, nothing sent).
   python3 walk_s830.py <kit dir>            -> last line 'WALK OK n/n' or 'WALK RED a/n'
   python3 walk_s830.py <kit dir> --control  -> runs the walk on three broken copies; last line 'CONTROL: red 3/3' when each
                                                broken copy turns the walk red (the walk can see what it claims to see)."""
import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

KIT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))
MOD = os.environ.get("S830_MOD", os.path.join(KIT, "att_silence_watch.py"))
OK = BAD = 0


def check(cond, what):
    global OK, BAD
    if cond:
        OK += 1
    else:
        BAD += 1
        print("BAD:", what)


def load():
    spec = importlib.util.spec_from_file_location("asw_walk", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class Box:
    def __init__(self):
        self.d = tempfile.mkdtemp(prefix="s830walk_")
        self.proc = os.path.join(self.d, "proc")
        os.makedirs(os.path.join(self.proc, "net"))
        self.state = os.path.join(self.d, "state.json")
        self.punch = os.path.join(self.d, "punches.csv")
        self.src = os.path.join(self.d, "sources.jsonl")
        self.off = os.path.join(self.d, "_off")
        os.makedirs(self.off)
        with open(self.punch, "w") as f:
            f.write("user_id,datetime,io_mode,verify_mode,received_at,machine_time\n")
        open(self.src, "w").close()
        self.listener()
        self.socks([])
        self.calls(None)
        self.pushed, self.ntfied = [], []
        self.push_ok, self.ntfy_ok = True, True

    def listener(self, present=True):
        for n in os.listdir(self.proc):
            if n.isdigit():
                shutil.rmtree(os.path.join(self.proc, n))
        if not present:
            return
        p = os.path.join(self.proc, "4242")
        os.makedirs(p)
        with open(os.path.join(p, "cmdline"), "wb") as f:
            f.write(b"/usr/bin/python3\x00/root/attlistener_v2.py\x00")

    def socks(self, rows4, rows6=()):
        hdr = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
        with open(os.path.join(self.proc, "net", "tcp"), "w") as f:
            f.write(hdr)
            z = "0" * 8                          # (built, so no long digit run sits in the file: the number gate)
            f.write("   0: %s:1F69 %s:0000 0A %s:%s 00:%s %s     0        0 1\n" % (z, z, z, z, z, z))
            for i, (rem, st) in enumerate(rows4):
                f.write("   %d: 0100A8C0:1F69 %s:D431 %s %s:%s 00:%s %s 0 0 %d\n" % (i + 1, rem, st, z, z, z, z, i + 9))
        with open(os.path.join(self.proc, "net", "tcp6"), "w") as f:
            f.write(hdr)
            for i, (rem, st) in enumerate(rows6):
                f.write("   %d: %s:1F69 %s:D431 %s 0 0 0 0 0 0\n" % (i, "0" * 32, rem, st))

    def calls(self, ip=None, port=8041):
        """The kernel's connection-tracking table: one closed connection to the port from ip (None = empty)."""
        with open(os.path.join(self.proc, "net", "nf_conntrack"), "w") as f:
            f.write("ipv4     2 tcp      6 431999 ESTABLISHED src=10.0.0.5 dst=93.1.1.1 sport=40000 dport=22 src=93.1.1.1 "
                    "dst=10.0.0.5 sport=22 dport=40000 [ASSURED] mark=0 zone=0 use=2\n")
            if ip:
                f.write("ipv4     2 tcp      6 117 TIME_WAIT src=%s dst=93.1.1.1 sport=51234 dport=%d src=93.1.1.1 dst=%s "
                        "sport=%d dport=51234 [ASSURED] mark=0 zone=0 use=2\n" % (ip, port, ip, port))

    def punch_row(self, uid, stored, rec, mach=None):
        with open(self.punch, "a") as f:
            f.write("%s,%s,0,1,%s,%s\n" % (uid, stored, rec, mach or stored))

    def src_line(self, t, ip, punch=False, rc="receive_cmd"):
        with open(self.src, "a") as f:
            f.write(json.dumps({"t": t, "ip": ip, "punch": punch, "request_code": rc}) + "\n")

    def pusher(self, user, payload):
        self.pushed.append(payload)
        return (1, 0) if self.push_ok else (0, 1)

    def ntfy(self, title, body):
        self.ntfied.append(body)
        return (True, "the ntfy topic took it") if self.ntfy_ok else (False, "the ntfy topic did not take it (URLError)")

    def run(self, m, when, dry=False, hours=(dt.time(9, 30), dt.time(20, 0))):
        now = dt.datetime.strptime(when, "%Y-%m-%d %H:%M")
        return m.run(now=now, dry=dry, state=self.state, pusher=self.pusher, ntfy=self.ntfy, hours=hours, proc=self.proc,
                     punch_csv=self.punch, source_log=self.src, off_dir=self.off)

    def st(self):
        with open(self.state) as f:
            return json.load(f)


def walk():
    m = load()
    MON = "2026-11-16"            # a Monday
    b = Box()
    MIP = "157.0.0.9"
    # 1. Sunday: nothing said; last_ok written; the box sees the machine's call (it can see connections)
    b.src_line("2026-11-15 10:59:00", MIP)
    b.calls(MIP)
    r = b.run(m, "2026-11-15 11:00")
    b.calls(None)
    check(r["sent"] == [] and not b.pushed, "Sunday sends nothing")
    check(b.st().get("last_ok_iso") == "2026-11-15 11:00:00", "Sunday writes last_ok")
    # 2. Monday before hours, machine never heard: nothing
    r = b.run(m, MON + " 09:00")
    check(r["sent"] == [], "before hours: nothing")
    # 3. 10:00, no punch, machine silent -> ONE nopunch message, silent wording; failing
    r = b.run(m, MON + " 10:00")
    check(r["sent"] == ["nopunch"], "10:00 no punch is told (%s)" % r["sent"])
    check(b.pushed and "No punch has reached the server today (Mon 16-Nov) by 10:00" in b.pushed[-1]["body"]
          and "was last heard from at Sun 15-Nov 11:00" in b.pushed[-1]["body"], "the nopunch words name the day and the machine")
    check(b.st().get("last_failure_iso") == MON + " 10:00:00", "failing writes last_failure")
    check((b.st().get("episode") or {}).get("told") is True, "the nopunch message stands for the silence")
    # 4. 10:35 still silent -> no second message
    n = len(b.pushed)
    r = b.run(m, MON + " 10:35")
    check(r["sent"] == [] and len(b.pushed) == n, "a told silence is not told twice")
    # 5. the machine's first call of the day is in the source log and its connection is seen
    b.src_line(MON + " 10:40:00", MIP)
    b.calls(MIP)
    r = b.run(m, MON + " 10:43")
    check(r["sent"] == ["back"], "contact again is told (%s)" % r["sent"])
    check("in contact again (10:43)" in b.pushed[-1]["body"], "the back words carry the time of the connection")
    check(b.st().get("episode") is None and b.st().get("conn_seen_iso") == "2026-11-15 11:00:00", "the episode is closed; the first sighting is kept")
    check(MIP in (b.st().get("machine_ips") or {}), "the machine's address is kept")
    # 6. calls go on and a punch arrives -> nothing
    b.punch_row(7, MON + " 10:44:00", MON + " 10:44:01")
    for tt in ("10:48", "10:53", "10:58", "11:03"):
        r = b.run(m, MON + " " + tt)
        check(r["sent"] == [], "steady contact says nothing (%s)" % tt)
    check(b.st().get("last_ok_iso") == MON + " 11:03:00", "steady contact moves last_ok")
    # 7. silence from 11:03; 11:30 not yet; 11:35 -> silent told once; 11:40 nothing
    b.calls(None)
    r = b.run(m, MON + " 11:30")
    check(r["sent"] == [], "27 minutes is not yet silence")
    r = b.run(m, MON + " 11:35")
    check(r["sent"] == ["silent"], "32 minutes of silence is told (%s)" % r["sent"])
    check("since 11:03 (32 min)" in b.pushed[-1]["body"], "the silent words carry since and how long")
    r = b.run(m, MON + " 11:40")
    check(r["sent"] == [], "the silence is told once")
    # 8. connections from this box itself, or from another address, are not the machine; the machine's (tcp table) is
    b.socks([("0100007F", "06")])
    b.calls("45.33.1.2")
    r = b.run(m, MON + " 11:45")
    check(r["sent"] == [], "a connection from this box, or a stray caller's, is not the machine")
    b.calls(None)
    b.socks([("0900009D", "06")])               # 157.0.0.9, little-endian
    r = b.run(m, MON + " 11:50")
    check(r["sent"] == ["back"], "the machine's connection in the tcp table is contact (%s)" % r["sent"])
    b.socks([])
    # 9. a second silence the same day is told too (its own episode)
    b.calls(MIP)
    b.run(m, MON + " 12:00")
    b.calls(None)
    r = b.run(m, MON + " 12:35")
    check(r["sent"] == ["silent"], "a second silence that day is told (%s)" % r["sent"])
    # 10. a stray caller's line in the source log (no request_code, no punch) is not contact
    b.src_line(MON + " 12:38:00", "45.33.1.2", rc="")
    r = b.run(m, MON + " 12:40")
    check(r["sent"] == [], "a stray caller's line is not the machine")
    # 11. no listener process: said, nothing breaks
    b.listener(present=False)
    r = b.run(m, MON + " 12:45")
    check(r["sent"] == [] and "the listener process was not found" in (b.st().get("last_notes") or []), "a missing listener is said")
    b.listener()
    # 12. the source log: a loopback line is not contact; the machine's line from a NEW address is (and is learnt)
    b.src_line(MON + " 12:46:00", "127.0.0.1")
    r = b.run(m, MON + " 12:50")
    check(r["sent"] == [], "a loopback line in the source log is not contact")
    b.src_line(MON + " 12:52:00", "103.9.9.9", punch=True, rc="realtime_glog")
    r = b.run(m, MON + " 12:55")
    check(r["sent"] == ["back"], "the machine's line from a new address is contact (%s)" % r["sent"])
    check("103.9.9.9" in (b.st().get("machine_ips") or {}), "the new address is learnt")
    # 13. the clock: a corrected punch -> one message that day
    b.punch_row(9, MON + " 13:00:00", MON + " 13:00:00", MON + " 11:21:00")
    b.calls("103.9.9.9")
    r = b.run(m, MON + " 13:01")
    check("clock" in r["sent"], "a punch whose machine time is 99 min behind is told (%s)" % r["sent"])
    check("1 h 39 min behind" in b.pushed[-1]["body"], "the clock words say how far")
    b.calls("103.9.9.9")
    r = b.run(m, MON + " 13:06")
    check("clock" not in r["sent"], "the clock is told once a day")
    # 14. past the end of hours: silence is not told
    b.calls("103.9.9.9")
    b.run(m, MON + " 19:00")
    r = b.run(m, MON + " 20:40")
    check(r["sent"] == [], "after hours a silence is not told")
    check(b.st().get("last_ok_iso") == MON + " 20:40:00", "after hours the leg stays green")
    # 15. the next day (Tue): stuck clock -- two punches 30 min apart, one machine time
    TUE = "2026-11-17"
    b.calls("103.9.9.9")
    b.run(m, TUE + " 09:55")
    b.punch_row(3, TUE + " 10:35:02", TUE + " 10:05:00", TUE + " 10:35:02")
    b.punch_row(4, TUE + " 10:35:02", TUE + " 10:35:00", TUE + " 10:35:02")
    b.calls("103.9.9.9")
    r = b.run(m, TUE + " 10:36")
    check(r["sent"] == ["clock"] and "seems stuck" in b.pushed[-1]["body"], "a stuck clock is told (%s)" % r["sent"])
    # 16. the machine in contact but nobody punched by 10:00 (Wed) -> nopunch, the 'in contact' words, no episode
    WED = "2026-11-18"
    b.calls("103.9.9.9")
    b.run(m, WED + " 09:55")
    b.calls("103.9.9.9")
    r = b.run(m, WED + " 10:00")
    check(r["sent"] == ["nopunch"] and "though the attendance machine is in contact" in b.pushed[-1]["body"],
          "no punch with the machine in contact (%s)" % r["sent"])
    check(b.st().get("episode") is None, "no silence episode when the machine is in contact")
    # 17. push fails, ntfy takes it
    THU = "2026-11-19"
    b.push_ok = False
    r = b.run(m, THU + " 10:00")
    check(r["sent"] == ["nopunch"] and b.ntfied, "no device took the push: the ntfy topic carried it")
    # 18. both fail: tried three times at most, then nothing
    FRI = "2026-11-20"
    b.ntfy_ok = False
    t = [b.run(m, FRI + " 10:%02d" % k) for k in (0, 5, 10, 15)]
    check([x["tried"] for x in t] == [["nopunch"], ["nopunch"], ["nopunch"], []], "three tries a day at most (%s)" % [x["tried"] for x in t])
    tries = b.st()["told"].get(FRI + "|nopunch", {})
    check(tries.get("tries") == 3 and tries.get("told") is False, "the tries are counted and not called told")
    b.push_ok = b.ntfy_ok = True
    # 19. dry: nothing written, nothing sent
    before = open(b.state).read()
    n = len(b.pushed)
    r = b.run(m, "2026-11-21 10:30", dry=True)
    check(r["line"].startswith("DRY ") and "would send" in r["line"], "dry says what it would send")
    check(open(b.state).read() == before and len(b.pushed) == n, "dry writes nothing and sends nothing")
    # 20. the off switch: nothing judged, nothing written
    open(os.path.join(b.off, "ATT_SILENCE_OFF"), "w").close()
    r = b.run(m, "2026-11-21 10:30")
    check(r.get("off") == "ATT_SILENCE_OFF" and open(b.state).read() == before and len(b.pushed) == n, "the off switch stops it")
    os.remove(os.path.join(b.off, "ATT_SILENCE_OFF"))
    # 21. an unreadable state is set aside and a fresh one started
    with open(b.state, "w") as f:
        f.write("{not json")
    r = b.run(m, "2026-11-22 11:00")
    check(os.path.exists(b.state + ".unreadable") and "set aside" in r["line"], "an unreadable state is set aside, said")
    # 22. a box that has never seen the machine's connections does not judge silence (it could not tell it from blindness)
    h = Box()
    h.src_line(MON + " 09:58:00", "157.0.0.9", punch=True, rc="realtime_glog")
    h.punch_row(1, MON + " 09:58:00", MON + " 09:58:00")
    r = h.run(m, MON + " 11:00")
    check(r["sent"] == [] and "silence not judged yet" in (h.st().get("last_summary") or ""), "silence waits until the box can see the machine")
    h.calls("157.0.0.9")
    h.run(m, MON + " 11:05")
    h.calls(None)
    r = h.run(m, MON + " 11:40")
    check(r["sent"] == ["silent"], "once seen, silence is judged (%s)" % r["sent"])
    shutil.rmtree(h.d, ignore_errors=True)
    # 23. hours from the staff shifts, clamped; a loader that fails gives the fallback
    T = dt.time
    s, e, how = m.staff_hours(lambda: {1: {"active": True, "wd_start": T(7, 0), "wd_end": T(23, 30)},
                                      2: {"active": True, "wd_start": T(10, 0), "wd_end": T(19, 0)}})
    check((s, e, how) == (T(8, 0), T(22, 0), "staff shifts"), "the hours are clamped (%s %s)" % (s, e))
    s, e, how = m.staff_hours(lambda: {1: {"active": True, "wd_start": T(9, 30), "wd_end": T(20, 0)},
                                      2: {"active": False, "wd_start": T(6, 0), "wd_end": T(23, 0)}})
    check((s, e) == (T(9, 30), T(20, 0)), "an inactive person's shift does not count")
    s, e, how = m.staff_hours(lambda: 1 / 0)
    check(how == "fallback" and (s, e) == (T(10, 0), T(20, 0)), "a loader that fails gives 10:00-20:00")
    # 24. no digit run that looks like a phone number in any message; no staff id in any message
    import re
    bodies = [p["body"] for p in b.pushed] + b.ntfied
    check(bodies and not any(re.search(r"\d{6,}", x) for x in bodies), "no long number in any message")
    check(all(p.get("url") == "/finance/console" and p.get("title") == "Attendance machine" for p in b.pushed),
          "every push opens the console, titled the same")
    # 25. the lock: a second run at the same instant does nothing
    fd, why = m.take_lock(b.state)
    r = b.run(m, "2026-11-23 10:00")
    os.close(fd)
    check(r["line"] == "" and r["sent"] == [] and why == "", "a run while another holds the lock does nothing")
    # 26. a punch after a told silence is contact again
    c2 = Box()
    c2.src_line(MON + " 09:29:00", "157.0.0.9")
    c2.calls("157.0.0.9")
    c2.run(m, MON + " 09:30")
    c2.calls(None)
    c2.run(m, MON + " 10:00")                # nopunch told (silent words)
    c2.punch_row(1, MON + " 10:20:00", MON + " 10:20:00")
    r = c2.run(m, MON + " 10:21")
    check(r["sent"] == ["back"], "a punch after a told silence is contact again (%s)" % r["sent"])
    # 28. a silence told at 08:30 (hours from 08:00) is not told again by the 10:00 no-punch message; a silence
    #     going on into the next working day is told again once, at 10:00
    e = Box()
    H8 = (dt.time(8, 0), dt.time(20, 0))
    e.src_line(MON + " 07:59:00", "157.0.0.9")
    e.calls("157.0.0.9")
    e.run(m, MON + " 08:00", hours=H8)
    e.calls(None)
    r1 = e.run(m, MON + " 08:30", hours=H8)
    r2 = e.run(m, MON + " 10:00", hours=H8)
    check(r1["sent"] == ["silent"] and r2["sent"] == [], "08:30 silence told; 10:00 not told again (%s %s)" % (r1["sent"], r2["sent"]))
    r3 = e.run(m, TUE + " 10:00", hours=H8)
    check("nopunch" in r3["sent"] and "was last heard from at Mon 16-Nov 08:00" in e.pushed[-1]["body"],
          "a silence still going on the next working day is told again at 10:00 (%s)" % r3["sent"])
    shutil.rmtree(e.d, ignore_errors=True)
    # 29. the seed writes the baseline and sends nothing; the next run compares against it
    g = Box()
    g.punch_row(2, MON + " 10:01:00", MON + " 10:01:00")
    g.src_line(MON + " 16:58:00", "157.0.0.9")
    g.calls("157.0.0.9")
    line = g.m_seed = m.seed(now=dt.datetime(2026, 11, 16, 17, 0), state=g.state, proc=g.proc, punch_csv=g.punch, source_log=g.src)
    st = g.st()
    check(line.startswith("SEED ") and st.get("conn_seen_iso") == "2026-11-16 17:00:00" and st.get("last_ok_iso") == "2026-11-16 17:00:00"
          and not g.pushed, "the seed writes the baseline only (%s)" % line[:80])
    r = g.run(m, MON + " 17:05")
    check(r["sent"] == [] and g.st().get("last_contact_iso") == MON + " 17:05:00", "the run after the seed sees the calls")
    shutil.rmtree(g.d, ignore_errors=True)
    # 30. staff who start at 09:45: the no-punch question waits until 30 minutes after the start (10:15)
    k = Box()
    k.src_line(MON + " 09:40:00", "157.0.0.9")
    k.calls("157.0.0.9")
    H945 = (dt.time(9, 45), dt.time(20, 0))
    r1 = k.run(m, MON + " 10:00", hours=H945)
    r2 = k.run(m, MON + " 10:15", hours=H945)
    check(r1["sent"] == [] and r2["sent"] == ["nopunch"], "a 09:45 start asks at 10:15, not 10:00 (%s %s)" % (r1["sent"], r2["sent"]))
    shutil.rmtree(k.d, ignore_errors=True)
    # 31. a flapping day: at most three silences are told (each with its 'back'), then only the console
    f = Box()
    f.punch_row(1, MON + " 10:01:00", MON + " 10:01:00")
    f.src_line(MON + " 10:01:00", "157.0.0.9", punch=True, rc="realtime_glog")
    kinds = []
    hh = 10
    for k2 in range(5):
        f.calls("157.0.0.9")
        kinds += f.run(m, "%s %02d:05" % (MON, hh))["sent"]
        f.calls(None)
        kinds += f.run(m, "%s %02d:40" % (MON, hh))["sent"]
        hh += 1
    f.calls("157.0.0.9")
    kinds += f.run(m, "%s %02d:05" % (MON, hh))["sent"]
    check(kinds.count("silent") == 3 and kinds.count("back") == 3, "three silences a day at most (%s)" % kinds)
    shutil.rmtree(f.d, ignore_errors=True)
    # 32. a 'back' message that no road took is tried again on the next run
    q = Box()
    q.punch_row(1, MON + " 10:01:00", MON + " 10:01:00")
    q.src_line(MON + " 10:01:00", "157.0.0.9", punch=True, rc="realtime_glog")
    q.calls("157.0.0.9")
    q.run(m, MON + " 10:05")
    q.calls(None)
    q.run(m, MON + " 10:40")
    q.push_ok = q.ntfy_ok = False
    q.calls("157.0.0.9")
    r1 = q.run(m, MON + " 10:45")
    q.push_ok = True
    r2 = q.run(m, MON + " 10:50")
    r3 = q.run(m, MON + " 10:55")
    check(r1["tried"] == ["back"] and r1["sent"] == [] and r2["sent"] == ["back"] and r3["sent"] == [],
          "an untold 'back' is tried again, then told once (%s %s %s)" % (r1["tried"], r2["sent"], r3["sent"]))
    shutil.rmtree(q.d, ignore_errors=True)
    # 33. before the box has seen the machine's connections, the 10:00 words claim nothing about the machine
    u = Box()
    u.src_line(MON + " 07:06:00", "157.0.0.9")
    r = u.run(m, MON + " 10:00")
    check(r["sent"] == ["nopunch"] and "last heard" not in u.pushed[-1]["body"] and u.st().get("episode") is None,
          "unseen: neutral words, no episode (%s)" % r["sent"])
    shutil.rmtree(u.d, ignore_errors=True)
    # 27. the log is cut back past its size
    lg = os.path.join(b.d, "x.log")
    with open(lg, "wb") as f:
        f.write(b"line\n" * 60000)
    m.cut_log(lg)
    check(os.path.getsize(lg) <= m.LOG_CUT // 2 and open(lg, "rb").read().startswith(b"line"), "the log is cut back whole-line")
    for x in (b, c2):
        shutil.rmtree(x.d, ignore_errors=True)
    n = OK + BAD
    print(("WALK OK %d/%d" % (OK, n)) if BAD == 0 else ("WALK RED %d/%d" % (OK, n)))
    return BAD == 0


def control():
    src = open(MOD, encoding="utf-8").read()
    breaks = [("SILENT_MIN = 30 ", "SILENT_MIN = 300 "),
              ("            if new_ep.get(\"told\") and str(new_ep.get(\"told_at\") or \"\")[:10] == today.isoformat():\n                body = None", "            if False:\n                body = None"),
              ("    by_conn = sorted(ip for ip in seen_ips if ip in known)", "    by_conn = sorted(seen_ips)")]
    red = 0
    for a, bb in breaks:
        assert src.count(a) == 1, a
        d = tempfile.mkdtemp(prefix="s830ctl_")
        p = os.path.join(d, "att_silence_watch.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(src.replace(a, bb))
        out = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), KIT], env=dict(os.environ, S830_MOD=p),
                             capture_output=True, text=True, timeout=120).stdout.strip().splitlines()
        if not (out and out[-1].startswith("WALK OK")):     # red, or the walk could not finish: either way not green
            red += 1
        else:
            print("CONTROL: a broken copy stayed green:", bb[:40])
        shutil.rmtree(d, ignore_errors=True)
    print(("CONTROL: red %d/%d" % (red, len(breaks))) if red == len(breaks) else ("CONTROL: GREEN %d/%d -- the walk is blind" % (red, len(breaks))))


if __name__ == "__main__":
    if "--control" in sys.argv:
        control()
    else:
        walk()
