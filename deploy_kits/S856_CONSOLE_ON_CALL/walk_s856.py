#!/usr/bin/env python3
"""
walk_s856.py -- kit S856_CONSOLE_ON_CALL's walk (the parent, S478, 17-Nov-2026).

Runs the kit's console_kick.py BY PATH (never imported from the kit folder -- F-1441) on a MADE-UP root:
a raw hook folder whose file times are set by hand, a made-up console.db carrying only meta.built_at,
a made-up lock, and a stand-in builder that writes a new built_at and counts its runs. No real call,
no real database, no network.

    python walk_s856.py <kit_dir>             -> last line "WALK OK n/n" or "WALK RED k/n"
    python walk_s856.py <kit_dir> --control   -> the same checks on broken copies; last line
                                                 "CONTROL: red ..." when every broken copy goes red
"""
import datetime as dt
import fcntl
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE in sys.path:
    sys.path.remove(HERE)

FAKE_BUILDER = r'''
import os, sqlite3, sys, time
c = os.environ.get("FB_COUNT")
open(c, "a").write(" ".join(sys.argv[1:]) + "\n")
time.sleep(float(os.environ.get("FB_SLEEP", "0")))
rc = int(os.environ.get("FB_RC", "0"))
if rc == 0:
    db = os.environ["CK_DB"]
    tmp = db + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    con = sqlite3.connect(tmp)
    con.execute("CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT)")
    con.execute("INSERT INTO meta VALUES ('built_at', ?)", (os.environ["FB_BUILT_AT"],))
    con.commit(); con.close()
    os.replace(tmp, db)
print("fake build done rc=%d" % rc)
sys.exit(rc)
'''


def ts(s):
    return time.mktime(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timetuple())


class World:
    def __init__(self, kick_path):
        self.root = tempfile.mkdtemp(prefix="s856walk_")
        self.kick = kick_path
        self.raw = os.path.join(self.root, "call_hook_logs")
        os.makedirs(self.raw)
        self.db = os.path.join(self.root, "console.db")
        self.lock = os.path.join(self.root, "console_cron.lock")
        self.state = os.path.join(self.root, "console_kick.state.json")
        self.off = os.path.join(self.root, "console_kick.OFF")
        self.blog = os.path.join(self.root, "logs", "console_cron.log")
        self.count = os.path.join(self.root, "count.txt")
        self.fb = os.path.join(self.root, "fake_builder.py")
        open(self.fb, "w").write(FAKE_BUILDER)

    def reset(self):
        for p in (self.db, self.state, self.count, self.off, self.blog):
            if os.path.exists(p):
                os.remove(p)
        for f in os.listdir(self.raw):
            p = os.path.join(self.raw, f)
            os.chmod(p, 0o600)
            os.remove(p)

    def set_db(self, built_at):
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
        con.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (built_at,))
        con.commit(); con.close()

    def set_raw(self, when, day="2026-11-17"):
        p = os.path.join(self.raw, day + ".jsonl")
        open(p, "a").write('{"made":"up"}\n')
        os.utime(p, (ts(when), ts(when)))
        return p

    def builds(self):
        return len(open(self.count).read().splitlines()) if os.path.exists(self.count) else 0

    def run(self, now, *args, built_at="2026-11-17 18:30:20", rc=0, sleep=0, extra=None):
        env = dict(os.environ)
        for k in list(env):
            if k.startswith("CK_") or k.startswith("FB_"):
                env.pop(k)
        env.update({"CK_RAW_DIR": self.raw, "CK_DB": self.db, "CK_LOCK": self.lock, "CK_STATE": self.state,
                    "CK_OFF": self.off, "CK_BUILD_LOG": self.blog, "CK_NOW": now,
                    "CK_BUILD": json.dumps([sys.executable, "-I", self.fb]),
                    "FB_COUNT": self.count, "FB_BUILT_AT": built_at, "FB_RC": str(rc), "FB_SLEEP": str(sleep)})
        env.update(extra or {})
        t0 = time.time()
        p = subprocess.run([sys.executable, "-I", "-B", self.kick] + list(args), env=env, capture_output=True,
                           text=True, timeout=60, cwd=self.root)
        return p.returncode, (p.stdout + p.stderr).strip(), time.time() - t0

    def st(self):
        try:
            return json.load(open(self.state))
        except (OSError, ValueError):
            return {}


def checks(kick_path):
    out = []
    w = World(kick_path)

    def ok(name, cond, note=""):
        out.append((name, bool(cond), note))

    try:
        # C1 / C2: the reading window (D819)
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 22:55:00")
        rc, o, _ = w.run("2026-11-17 23:13:00")
        ok("C1 after 22:50 nothing is built", w.builds() == 0 and rc == 0, o)
        w.reset(); w.set_db("2026-11-16 22:50:30"); w.set_raw("2026-11-17 06:40:00")
        rc, o, _ = w.run("2026-11-17 06:59:00")
        ok("C2 before 07:00 nothing is built", w.builds() == 0, o)
        w.reset(); w.set_db("2026-11-17 22:40:20"); w.set_raw("2026-11-17 22:45:00")
        rc, o, _ = w.run("2026-11-17 22:46:30", built_at="2026-11-17 22:46:50")
        ok("C2b at 22:46, the last kick minute, a waiting call is built", w.builds() == 1, o)
        w.reset(); w.set_db("2026-11-17 22:40:20"); w.set_raw("2026-11-17 22:49:00")
        rc, o, _ = w.run("2026-11-17 22:51:00")
        ok("C2c at 22:51 (outside the window) nothing is built", w.builds() == 0, o)
        # C3: no hook file today
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-16 21:00:00", day="2026-11-16")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C3 no call logged today: nothing built", w.builds() == 0, o)
        # C4: the case measured on 17-Nov (call 18:22:22, reading 18:20)
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:22:22")
        rc0, o0, _ = w.run("2026-11-17 18:23:00", "--probe")
        ok("C4a the probe says it would build", "would_build=yes" in o0 and w.builds() == 0 and not os.path.exists(w.state), o0)
        rc, o, _ = w.run("2026-11-17 18:23:00", built_at="2026-11-17 18:23:20")
        st = w.st()
        ok("C4b the 18:22 call is built the next minute", w.builds() == 1 and rc == 0, o)
        ok("C4c the state records the good build, the hook time it covered and the kick in the hour",
           st.get("last_rc") == 0 and st.get("covered_hook") == "2026-11-17 18:22:22" and st.get("last_ok") == "2026-11-17 18:23:00"
           and st.get("kicks_last_hour") == ["2026-11-17 18:23:00"], json.dumps(st))
        blog = open(w.blog).read() if os.path.exists(w.blog) else ""
        ok("C4d the build's output goes to the 10-minute run's log, with the kick's header", "[S856 kick 2026-11-17 18:23:00]" in blog and "fake build done" in blog, blog[:200])
        cnt = open(w.count).read() if os.path.exists(w.count) else None
        ok("C4e the stand-in builder ran with the kick's own command (no extra arguments)", cnt is not None and cnt.strip() == "", str(cnt)[:80])
        # C5: the same call again (its reading came only 58 s after the call -- covered_hook stops a second build)
        rc, o, _ = w.run("2026-11-17 18:26:00")
        ok("C5 the call it already read is not built again", w.builds() == 1, o)
        # C6: settle
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:32:50")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C6 a call logged 10 s ago waits for the next minute", w.builds() == 0, o)
        rc, o, _ = w.run("2026-11-17 18:34:00", built_at="2026-11-17 18:34:20")
        ok("C6b ... and is built the next minute", w.builds() == 1, o)
        # C7: minimum gap
        w.reset(); w.set_db("2026-11-17 18:32:00"); w.set_raw("2026-11-17 18:32:30")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C7 never within 2 minutes of the last reading", w.builds() == 0, o)
        # C8: the reading is newer than the call
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:10:00")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C8 a reading newer than the last call: nothing built", w.builds() == 0, o)
        # C9: the lock busy (the 10-minute run is reading now) -- held by /usr/bin/flock as cron holds it
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:25:00")
        holder = None
        if shutil.which("flock"):
            holder = subprocess.Popen(["flock", w.lock, "sleep", "20"], start_new_session=True)
            for _ in range(50):
                time.sleep(0.1)
                fd = os.open(w.lock, os.O_RDWR | os.O_CREAT, 0o644)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(fd, fcntl.LOCK_UN); busy = False
                except OSError:
                    busy = True
                os.close(fd)
                if busy:
                    break
            try:
                rc, o, _ = w.run("2026-11-17 18:33:00")
            finally:
                os.killpg(holder.pid, signal.SIGKILL); holder.wait()
        else:
            fd = os.open(w.lock, os.O_RDWR | os.O_CREAT, 0o644)
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                rc, o, _ = w.run("2026-11-17 18:33:00")
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)
        ok("C9 a reading running now (lock held%s): nothing built, nothing written" % (" by flock(1)" if holder else ""),
           w.builds() == 0 and rc == 0 and not os.path.exists(w.state), o)
        rc, o, _ = w.run("2026-11-17 18:34:00", built_at="2026-11-17 18:34:20")
        ok("C9b the lock free again: built", w.builds() == 1, o)
        # C10: a failed build waits 10 minutes
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:25:00")
        rc, o, _ = w.run("2026-11-17 18:33:00", rc=2)
        st = w.st()
        ok("C10a a failed build is recorded and exits 1", w.builds() == 1 and rc == 1 and st.get("last_rc") == 2 and st.get("fails_in_a_row") == 1 and "covered_hook" not in st, o + json.dumps(st))
        rc, o, _ = w.run("2026-11-17 18:42:00")
        ok("C10b within 10 minutes it does not try again", w.builds() == 1, o)
        rc, o, _ = w.run("2026-11-17 18:44:00", built_at="2026-11-17 18:44:20")
        st = w.st()
        ok("C10c after 10 minutes it tries again and the good build clears the count", w.builds() == 2 and st.get("last_rc") == 0 and st.get("fails_in_a_row") == 0, json.dumps(st))
        # C11: a build that hangs is stopped
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:25:00")
        rc, o, el = w.run("2026-11-17 18:33:00", sleep=6, extra={"CK_TIMEOUT_S": "2"})
        st = w.st()
        ok("C11 a hanging build is stopped at its limit and recorded", st.get("last_rc") == 124 and el < 5.5 and rc == 1, "%s %.1fs %s" % (o, el, json.dumps(st)))
        # C12: no console.db yet
        w.reset(); w.set_raw("2026-11-17 18:25:00")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C12 no reading at all: built", w.builds() == 1, o)
        # C13: the off switch
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:25:00")
        open(w.off, "w").write("off\n")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C13 the off switch: nothing built", w.builds() == 0, o)
        os.remove(w.off)
        # C14: the raw log is never opened (made unreadable; only its time is used) + the whole file checked
        w.reset(); w.set_db("2026-11-17 18:20:05"); p = w.set_raw("2026-11-17 18:25:00")
        os.chmod(p, 0)
        rc, o, _ = w.run("2026-11-17 18:33:00")
        os.chmod(p, 0o600)
        src = open(kick_path).read()
        body = src.split("def raw_mtime", 1)[1].split("\ndef ", 1)[0]
        code = src.split('"""', 2)[2]
        ok("C14 the hook log is read by its time only, never opened (RAW_DIR used only by raw_mtime's os.stat)",
           w.builds() == 1 and "open(" not in body and "os.stat(" in body and len(re.findall(r"(?<![A-Z_])RAW_DIR\b", code)) == 2, o)
        # C15: the real command is the 10-minute run's own, without --with-transcripts
        ns = {}
        env_build = os.environ.pop("CK_BUILD", None)
        exec(compile(src.split("\ndef now_local", 1)[0], kick_path, "exec"), ns)
        if env_build is not None:
            os.environ["CK_BUILD"] = env_build
        cron = "/root/wa/venv/bin/python3 /root/wa/portal_console.py --build --with-myop-reconcile --with-transcripts --days 60".split()
        want = [a for a in cron if a != "--with-transcripts"]
        ok("C15 the build is the 10-minute run's own command less --with-transcripts", ns.get("BUILD_CMD") == want, str(ns.get("BUILD_CMD")))
        ok("C15b the lock is the 10-minute run's own", ns.get("LOCK") == "/root/wa/console_cron.lock" and ns.get("BUILD_LOG") == "/root/wa/logs/console_cron.log", "%s %s" % (ns.get("LOCK"), ns.get("BUILD_LOG")))
        # C16: the probe never writes, and says the reading time even outside the window
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:25:00")
        m0 = os.stat(w.db).st_mtime
        rc, o, _ = w.run("2026-11-17 18:33:00", "--probe")
        rc2, o2, _ = w.run("2026-11-17 23:30:00", "--probe")
        ok("C16 the probe builds nothing, writes nothing, and reads the reading time at any hour",
           w.builds() == 0 and not os.path.exists(w.state) and os.stat(w.db).st_mtime == m0 and o.startswith("PROBE ")
           and "reading=2026-11-17 18:20:05" in o2, o + " | " + o2)
        # C17: a 10-minute reading that may have started before the call's sheet row
        w.reset(); w.set_db("2026-11-17 18:20:40"); w.set_raw("2026-11-17 18:20:00")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C17 a call 40 s before a reading's time is built again (the reading may predate its row)", w.builds() == 1, o)
        w.reset(); w.set_db("2026-11-17 18:22:30"); w.set_raw("2026-11-17 18:20:00")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C17b a call 150 s before a reading's time is taken as read", w.builds() == 0, o)
        # C18: an unreadable console.db counts as no reading
        w.reset(); open(w.db, "w").write("not a database"); w.set_raw("2026-11-17 18:25:00")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C18 an unreadable console.db counts as no reading: built", w.builds() == 1, o)
        # C19: a quiet minute writes nothing at all
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:10:00")
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C19 a quiet minute prints nothing and writes no state", o == "" and not os.path.exists(w.state), o)
        # C20: :X8, :X9, :X0 are the 10-minute run's
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:25:00")
        for t in ("18:37:00", "18:38:00", "18:39:30", "18:40:00", "07:00:10"):
            w.run("2026-11-17 " + t)
        ok("C20 at :X7, :X8, :X9, :X0 (and 07:00) the lock is left to the 10-minute run", w.builds() == 0, "")
        rc, o, _ = w.run("2026-11-17 18:41:00")
        ok("C20b at :X1 a waiting call is built", w.builds() == 1, o)
        # C21: at most 6 kicks an hour
        w.reset(); w.set_db("2026-11-17 18:20:05"); w.set_raw("2026-11-17 18:25:00")
        six = ["2026-11-17 17:%02d:00" % m for m in (35, 41, 47, 53, 57)] + ["2026-11-17 18:05:00"]
        json.dump({"kicks_last_hour": six, "last_rc": 0}, open(w.state, "w"))
        rc, o, _ = w.run("2026-11-17 18:33:00")
        ok("C21 six kicks in the last hour: the seventh waits", w.builds() == 0, o)
        rc, o, _ = w.run("2026-11-17 18:36:00")
        st = w.st()
        ok("C21b an hour after the oldest it builds, and the hour's list drops what is older",
           w.builds() == 1 and len(st.get("kicks_last_hour") or []) == 6 and "2026-11-17 17:35:00" not in st.get("kicks_last_hour"), json.dumps(st))
    except Exception as e:                      # a crash in the walk is a red, never a pass
        ok("CRASH in the walk", False, "%s: %s" % (e.__class__.__name__, e))
    finally:
        shutil.rmtree(w.root, ignore_errors=True)
    return out


def mutate(src_path, dst_dir, name, old, new):
    s = open(src_path).read()
    assert old in s, "mutation anchor missing: " + name
    p = os.path.join(dst_dir, "console_kick_" + name + ".py")
    open(p, "w").write(s.replace(old, new, 1))
    return p


def main():
    kit = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else HERE)
    kick = os.path.join(kit, "console_kick.py")
    if "--control" in sys.argv:
        d = tempfile.mkdtemp(prefix="s856ctl_")
        try:
            broken = {
                "old_world_off": mutate(kick, d, "off", 'if os.path.exists(OFF):', 'if True:'),
                "no_lock": mutate(kick, d, "nolock", "fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)", "pass"),
                "no_settle": mutate(kick, d, "nosettle", "if (now - rm).total_seconds() < SETTLE_S:", "if False:"),
                "no_window": mutate(kick, d, "nowindow", "if not in_window(now):", "if False:"),
                "no_yield": mutate(kick, d, "noyield", "if now.minute % 10 in YIELD_MINUTES:", "if False:"),
                "no_cap": mutate(kick, d, "nocap", "if len(recent_kicks(st, now)) >= MAX_PER_HOUR:", "if False:"),
            }
            reds = []
            for name, p in broken.items():
                res = checks(p)
                bad = [n for n, good, _ in res if not good]
                reds.append("%s %d/%d" % (name, len(bad), len(res)))
                if not bad:
                    print("CONTROL NOT RED: %s stayed green" % name)
                    print("CONTROL: GREEN (a broken copy passed) " + "; ".join(reds))
                    return 1
            print("CONTROL: red " + "; ".join(reds))
            return 0
        finally:
            shutil.rmtree(d, ignore_errors=True)
    res = checks(kick)
    for n, good, note in res:
        print(("ok   " if good else "BAD  ") + n + ("" if good else "  :: " + note[:300]))
    bad = sum(1 for _, g, _ in res if not g)
    print(("WALK OK %d/%d" % (len(res), len(res))) if not bad else ("WALK RED %d/%d" % (bad, len(res))))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
