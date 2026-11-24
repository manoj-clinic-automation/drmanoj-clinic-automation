#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""server_record.py -- kit S943 (the parent, S511, 24-Nov-2026): the nightly SERVER RECORD (roadmap S510 phase 0, A1; plan L1).

Read-only on the box. Once a night (cron 02:50) it writes one JSON under /root/finance/server_record/ -- YYYY-MM-DD.json and a
LATEST.json copy -- and keeps 90 days:
  disks    df of every real filesystem (mount, size, used, free, percent)
  folders  du of the known roots (/root/finance, /root/wa, /root/backups, /root/state_backup, ... /var/log, /tmp) -- bytes only
  ram      total and available            load     1 / 5 / 15 minutes and the CPU count
  procs    the five biggest processes by memory (pid, rss, cpu %, elapsed, the command NAME only -- never its arguments)
  warn     disk at 80 % or more . RAM available under 1 GB . the 15-minute load at or above the CPU count (said as 'high for the
           last quarter hour'; a nightly snapshot cannot see an hour -- the records side by side can)
The owner's console reads LATEST.json (one health line); the freshness page watches the file's age (a leg, 26 h).
Nothing in a record names a patient, a number or a key: process ARGUMENTS are never kept.

    /root/wa/venv/bin/python3 -B server_record.py            write tonight's record (cron)
    /root/wa/venv/bin/python3 -B server_record.py --check    say LATEST in one line, write nothing   -> 'RECORD OK ...' / 'RECORD NONE'
    /root/wa/venv/bin/python3 -B server_record.py --selftest made-up df/free/ps/du; writes into a temp folder only
Env (the walk's hooks, never set on the box): SR_DIR, SR_DF_CMD, SR_FREE_CMD, SR_PS_CMD, SR_DU_CMD, SR_LOADAVG, SR_NCPU, SR_NOW_ISO.
"""
import datetime as dt
import glob
import json
import os
import shlex
import subprocess
import sys
import tempfile

os.environ.setdefault("TZ", "Asia/Kolkata")
import time  # noqa: E402

time.tzset()
VERSION = "S943 1.0"
REC_DIR = os.environ.get("SR_DIR", "/root/finance/server_record")
KEEP_DAYS = 90
KNOWN_FOLDERS = ["/root/finance", "/root/wa", "/root/backups", "/root/state_backup", "/root/assetapp", "/root/followup_tracker",
                 "/root/portal", "/root/labdata", "/root/deploy", "/root/marg_ingest", "/var/log", "/tmp"]
DISK_WARN_PCT = 80
RAM_WARN_B = 1024 * 1024 * 1024
TOP_N = 5


def now():
    s = os.environ.get("SR_NOW_ISO")
    return dt.datetime.fromisoformat(s) if s else dt.datetime.now()


def run(cmd_env, default, timeout=60, any_rc=False):
    cmd = os.environ.get(cmd_env) or default
    try:
        r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        return r.stdout if (r.returncode == 0 or any_rc) else ""
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return ""


def read_disks():
    out = []
    for ln in run("SR_DF_CMD", "df -P -B1 -x tmpfs -x devtmpfs -x squashfs -x overlay").splitlines()[1:]:
        p = ln.split()
        if len(p) < 6 or not p[1].isdigit():
            continue
        size, used, avail = int(p[1]), int(p[2]), int(p[3])
        pct = int(round(100.0 * used / size)) if size else 0
        out.append({"mount": p[5], "size_b": size, "used_b": used, "avail_b": avail, "pct": pct})
    return out


def read_folders():
    out = []
    for path in KNOWN_FOLDERS:
        if not os.path.isdir(path) and not os.environ.get("SR_DU_CMD"):
            continue
        txt = run("SR_DU_CMD", "du -sxB1 %s" % shlex.quote(path), timeout=120, any_rc=True)   # du exits 1 on a folder it may not enter; the total still comes
        try:
            out.append({"path": path, "bytes": int(txt.split()[0])})
        except (IndexError, ValueError):
            out.append({"path": path, "bytes": None})
    return out


def read_ram():
    total = avail = None
    for ln in run("SR_FREE_CMD", "free -b").splitlines():
        p = ln.split()
        if p and p[0].lower().startswith("mem") and len(p) >= 7:
            total, avail = int(p[1]), int(p[6])
    return {"total_b": total, "available_b": avail}


def read_load():
    try:
        if os.environ.get("SR_LOADAVG"):
            l1, l5, l15 = [float(x) for x in os.environ["SR_LOADAVG"].split()[:3]]
        else:
            with open("/proc/loadavg") as fh:
                l1, l5, l15 = [float(x) for x in fh.read().split()[:3]]
    except (OSError, ValueError):
        l1 = l5 = l15 = None
    ncpu = int(os.environ.get("SR_NCPU") or (os.cpu_count() or 1))
    return {"l1": l1, "l5": l5, "l15": l15, "ncpu": ncpu}


def read_procs():
    rows = []
    for ln in run("SR_PS_CMD", "ps -eo pid=,rss=,pcpu=,etime=,comm= --sort=-rss").splitlines():
        p = ln.split(None, 4)
        if len(p) < 5 or not p[0].isdigit():
            continue
        rows.append({"pid": int(p[0]), "rss_b": int(p[1]) * 1024, "cpu_pct": float(p[2]), "elapsed": p[3], "comm": p[4].strip()[:32]})
        if len(rows) >= TOP_N:
            break
    return rows


def gb(b):
    return "%.1f GB" % (b / 1e9) if b is not None else "?"


def warnings(rec):
    w = []
    for d in rec["disks"]:
        if d["pct"] >= DISK_WARN_PCT and (d["size_b"] or 0) >= 10 ** 9:      # a tiny /boot/efi never cries wolf
            w.append("disk %s at %d %% (%s free)" % (d["mount"], d["pct"], gb(d["avail_b"])))
    a = rec["ram"].get("available_b")
    if a is not None and a < RAM_WARN_B:
        w.append("RAM available %d MB (under 1 GB)" % (a // (1024 * 1024)))
    L = rec["load"]
    if L.get("l15") is not None and L["l15"] >= L["ncpu"]:
        w.append("load %.2f for the last quarter hour, at or above the %d CPU(s)" % (L["l15"], L["ncpu"]))
    return w


def make_record():
    t = now()
    rec = {"version": VERSION, "when_iso": t.strftime("%Y-%m-%dT%H:%M:%S"), "day": t.strftime("%Y-%m-%d"), "host": os.uname().nodename,
           "disks": read_disks(), "folders": read_folders(), "ram": read_ram(), "load": read_load(), "procs": read_procs()}
    rec["warn"] = warnings(rec)
    return rec


def write_record(rec, rec_dir):
    os.makedirs(rec_dir, exist_ok=True)
    day_p = os.path.join(rec_dir, rec["day"] + ".json")
    tmp = day_p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    os.replace(tmp, day_p)
    latest = os.path.join(rec_dir, "LATEST.json")
    with open(latest + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    os.replace(latest + ".tmp", latest)
    cutoff = (dt.date.fromisoformat(rec["day"]) - dt.timedelta(days=KEEP_DAYS)).isoformat()
    pruned = 0
    for p in glob.glob(os.path.join(rec_dir, "20??-??-??.json")):
        if os.path.basename(p)[:10] < cutoff:
            try:
                os.remove(p)
                pruned += 1
            except OSError:
                pass
    return day_p, pruned


def one_line(rec):
    root = next((d for d in rec["disks"] if d["mount"] == "/"), rec["disks"][0] if rec["disks"] else None)
    disk = ("disk %d %% (%s free)" % (root["pct"], gb(root["avail_b"]))) if root else "disk ?"
    return "RECORD OK %s %s ram %s available load %s warn %d" % (rec["day"], disk, gb(rec["ram"].get("available_b")),
                                                                 rec["load"].get("l1"), len(rec["warn"]))


def check(rec_dir):
    p = os.path.join(rec_dir, "LATEST.json")
    if not os.path.exists(p):
        print("RECORD NONE (%s)" % p)
        return 1
    with open(p, encoding="utf-8") as fh:
        rec = json.load(fh)
    print(one_line(rec))
    for w in rec.get("warn") or []:
        print("  warn: " + w)
    return 0


def selftest():
    d = tempfile.mkdtemp(prefix="s943_self_")
    try:
        fx = os.path.join(d, "fx")
        os.makedirs(fx)

        def tool(name, body):
            p = os.path.join(fx, name)
            with open(p, "w") as fh:
                fh.write("#!/bin/sh\ncat <<'EOF'\n" + body + "EOF\n")
            os.chmod(p, 0o755)
            return p

        G = 10 ** 9                                                     # figures built at run time: no long digit run in the source
        df_ok = tool("df", "Filesystem 1-blocks Used Available Capacity Mounted on\n/dev/sda1 %d %d %d 29%% /\n" % (100 * G, 29 * G, 71 * G))
        df_full = tool("df2", "Filesystem 1-blocks Used Available Capacity Mounted on\n/dev/sda1 %d %d %d 85%% /\n" % (100 * G, 85 * G, 15 * G))
        free_ok = tool("free", "              total        used        free      shared  buff/cache   available\nMem: %d %d %d %d %d %d\nSwap: 0 0 0\n"
                       % (79 * G // 10, 2 * G, 3 * G, G // 10, 29 * G // 10, 5 * G))
        free_low = tool("free2", "              total        used        free      shared  buff/cache   available\nMem: %d %d %d %d %d %d\nSwap: 0 0 0\n"
                        % (79 * G // 10, 7 * G, 3 * G // 10, G // 10, 6 * G // 10, 7 * G // 10))
        ps = tool("ps", "  101 412000  1.5    10-02:11:03 python3\n  202 210000  0.2       02:11:03 gunicorn\n  303  90000  0.0 100-00:00:00 sshd\n  404  80000  0.0       00:00:03 ps\n  505  70000  0.0    01:00:00 cron\n  606  10000  0.0    01:00:00 bash\n")
        du = tool("du", "123456 /x\n")
        n = f = 0

        def ok(name, cond):
            nonlocal n, f
            n += 1
            print(("  ok   " if cond else "  FAIL ") + name)
            if not cond:
                f += 1
        rd = os.path.join(d, "rec")
        env = {"SR_DIR": rd, "SR_DF_CMD": df_ok, "SR_FREE_CMD": free_ok, "SR_PS_CMD": ps, "SR_DU_CMD": du, "SR_LOADAVG": "0.4 0.3 0.3",
               "SR_NCPU": "4", "SR_NOW_ISO": "2026-11-25T02:50:10"}
        os.environ.update(env)
        rec = make_record()
        ok("a quiet night: no warning", rec["warn"] == [])
        ok("disk read: / 29 %, 71 GB free", rec["disks"][0]["pct"] == 29 and rec["disks"][0]["avail_b"] == 71 * G)
        ok("RAM read: 5.0 GB available", rec["ram"]["available_b"] == 5 * G)
        ok("five processes, names only, biggest first", len(rec["procs"]) == 5 and rec["procs"][0]["comm"] == "python3" and "args" not in rec["procs"][0])
        ok("folders: every known root measured", len(rec["folders"]) == len(KNOWN_FOLDERS) and all(x["bytes"] == 123456 for x in rec["folders"]))
        day_p, pruned = write_record(rec, rd)
        ok("record written + LATEST", os.path.exists(day_p) and os.path.exists(os.path.join(rd, "LATEST.json")))
        ok("check says RECORD OK", one_line(rec).startswith("RECORD OK 2026-11-25 disk 29 % (71.0 GB free) ram 5.0 GB available load 0.4 warn 0"))
        for i in range(1, 101):
            open(os.path.join(rd, (dt.date(2026, 11, 25) - dt.timedelta(days=i)).isoformat() + ".json"), "w").write("{}")
        _, pruned = write_record(rec, rd)
        left = len(glob.glob(os.path.join(rd, "20??-??-??.json")))
        ok("90 days kept (100 old + today -> %d left, %d pruned)" % (left, pruned), left == 91 and pruned == 10)
        os.environ.update({"SR_DF_CMD": df_full, "SR_FREE_CMD": free_low, "SR_LOADAVG": "5.1 4.8 4.6"})
        rec2 = make_record()
        ok("a bad night: three warnings (disk 85 %, RAM 667 MB, load 4.6 on 4 CPUs)", len(rec2["warn"]) == 3
           and rec2["warn"][0].startswith("disk / at 85 %") and "667 MB" in rec2["warn"][1] and rec2["warn"][2].startswith("load 4.60"))
        os.environ.update({"SR_DF_CMD": os.path.join(fx, "missing"), "SR_FREE_CMD": os.path.join(fx, "missing"), "SR_PS_CMD": os.path.join(fx, "missing")})
        rec3 = make_record()
        ok("tools missing: a record still written, empty parts, no crash", rec3["disks"] == [] and rec3["ram"]["available_b"] is None and rec3["procs"] == [])
        print("SELFTEST %d/%d" % (n - f, n))
        return 1 if f else 0
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if "--check" in sys.argv:
        return check(REC_DIR)
    rec = make_record()
    day_p, pruned = write_record(rec, REC_DIR)
    print("%s %s -> %s (%d pruned)" % (rec["when_iso"], one_line(rec), day_p, pruned))
    for w in rec["warn"]:
        print("  warn: " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
