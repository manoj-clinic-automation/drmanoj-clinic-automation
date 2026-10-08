#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""walk_s499.py -- kit S499_MEDICAL_AGENT_BACKUP: the re-issued medical agent and its installer, walked.

It loads an agent -- the kit's S499.1, or S205.1 as published -- from a COPY in a scratch folder, with its path constants
pointed at made-up folders (a stick, Marg's serverbackup, D:\SendToClinic, a Drive with FromMedical / ToMedical\_kit /
MargBackups) and a clock the walk moves. Every check runs through the agent's own backup_pass(), build_beat(), human(),
write_beat(), prune_kit_backups() and main() -- never through a new helper alone. The heartbeat it writes is then read by
the REAL readers (manojz's pipeline_status.py and verify_medical.py, copied out of the repository), with their own code.
The installer is walked against the REAL guard (agent_guard.py S387), which starts, stops and restarts stand-in agents.

  A  the stick absent . Drive absent                         G  both stale . "exactly one place" only when measured
  B  a 4-day-old hand-made .mbk + a fresh serverbackup set   H  the file-list comparison (same / different / not a zip)
     -> the set on the stick, md5-equal, times kept;         J  the prune: 12 legal, the manifest's files, a failure
     a second pass copies nothing                            L  three backups with one name: the hourly re-copy
  C  the calm line for an old hand-made backup               M  every heartbeat.json key S205.1 wrote is still there
  D  a source Marg is still writing is left alone            N  the readers parse every heartbeat above
  E  31+ sets: only the agent's own folder is pruned         P  the main loop, a kit install, the refusal to deliver itself
  F  the stick full or write-protected: no crash, a line     Q  function by function: what changed, what did not
     . Marg's own backup 3 days old: the loud line           K  the kit: pins, the .bat, a build that repeats
  I  the installer: placed, twice, wrong pins, a new agent that crashes or is mute (put back), no guard, switched off --
     and, last, the kit's OWN two files at their OWN pins: the real S205.1 under the real guard, swapped by the real installer

NEGATIVE CONTROLS, on what the code DOES:
  OLD  the same checks on medical_agent.py S205.1 (70d5c4e3). Each check says what S205.1 must do: go RED (the fault this
       kit mends) or stay the SAME (behaviour this kit must not change). The walk fails if S205.1 does not do exactly that.
  MUT  the installer with its put-back taken out, given a new agent that crashes: the put-back checks go red.

  walk_s499.py --old <medical_agent.py S205.1> --readers <dir holding pipeline_status.py and verify_medical.py>
               --guard <agent_guard.py S387> --work DIR [--kit DIR]
No phone number, no key, no real backup: every file is made up here. Nothing leaves this machine.
"""
import argparse
import ast
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time as _time
import zipfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FROM_MD5 = "70d5c4e3c439eaa049acb27f9851688c"
DAY = 86400.0
OLD_KEYS = ("checked_at", "offsite", "copied", "copied_bytes", "already_there", "pending", "errors", "newest_stick",
            "newest_stick_age_days", "newest_serverbackup_age_days", "offsite_files", "offsite_bytes", "note")
OLD_BEAT_KEYS = ("agent_version", "written_at", "computer", "user", "python", "agent_started", "watcher", "captures",
                 "ignored_by_watcher", "agent_self", "watcher_file", "kit", "marg_slots", "kit_backups", "disk_free_gb_D", "backup")
# the functions this kit means to change, add -- and none to remove
CHANGED = {"prune_kit_backups", "backup_count", "_backup_sources", "backup_pass", "build_beat", "human", "main", "agent_drift",
           "backup_state_read"}
ADDED = {"_kit_dests", "_kit_baks", "kit_backup_state", "_same_dir", "_is_marg_blob", "_stick_auto_dir", "_serverbackup_files",
         "_newest_auto_set", "_copy_verified", "_stick_auto_blobs", "_prune_stick_sets", "stick_leg", "_offsite_names",
         "_zip_listing", "_zip_compare", "_really_inside", "_when"}


def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def stuff(n, seed):
    """n made-up bytes, the same for the same seed."""
    out, i = bytearray(), 0
    while len(out) < n:
        out += hashlib.sha256(("%s/%d" % (seed, i)).encode()).digest()
        i += 1
    return bytes(out[:n])


def made_zip(names, seed, protected=True):
    """A made-up zip whose members are FLAGGED password-protected, as Marg's are: the list reads, a member does not."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for i, n in enumerate(names):
            z.writestr(n, stuff(300 + 37 * i, "%s/%s" % (seed, n)))
    raw = bytearray(buf.getvalue())
    if protected:
        for sig, off in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
            i = raw.find(sig)
            while i != -1:
                raw[i + off] |= 0x01
                i = raw.find(sig, i + 4)
    return bytes(raw)


class Clock(object):
    """The agent's `time`, moved by the walk. Files are dated against it."""

    def __init__(self):
        self.off = 0.0
        self.on_sleep = None

    def time(self):
        return _time.time() + self.off

    def sleep(self, s):
        if self.on_sleep:
            self.on_sleep(s)

    def advance(self, s):
        self.off += s

    def __getattr__(self, n):
        return getattr(_time, n)


class World(object):
    def __init__(self, work, tag, stick=True, drive=True):
        self.root = os.path.join(work, tag)
        if os.path.isdir(self.root):
            shutil.rmtree(self.root)
        self.E = os.path.join(self.root, "E_stick")
        self.SB = os.path.join(self.root, "D_MARGERP", "serverbackup")
        self.STC = os.path.join(self.root, "SendToClinic")
        self.home = os.path.join(self.root, "home")
        self.cda = os.path.join(self.home, "My Drive", "Clinic Data Archive")
        self.FM = os.path.join(self.cda, "FromMedical")
        self.KIT = os.path.join(self.cda, "ToMedical", "_kit")
        self.OFF = os.path.join(self.cda, "MargBackups")
        self.AUTO = os.path.join(self.E, "MargAuto_by_agent")
        for d in (self.SB, self.STC, self.home, os.path.join(self.root, "D:\\")):
            os.makedirs(d)
        if stick:
            os.makedirs(self.E)
        if drive:
            os.makedirs(self.FM)
            os.makedirs(self.KIT)
        self.clock = Clock()
        os.environ["USERPROFILE"] = self.home
        os.chdir(self.root)            # so that the agent's "D:\\" (disk free) is a folder that exists here

    def put(self, path, data, age_s):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(data, int):
            data = stuff(data, os.path.basename(path) + str(data))
        with open(path, "wb") as fh:
            fh.write(data)
        t = self.clock.time() - age_s
        os.utime(path, (t, t))
        return path

    def sb_set(self, day, blob, d01, age_s, size=29124):
        """One of Marg's own backups as the census of 26-Aug-2026 measured it: <weekday>.mst, the database file 51 s later,
        the _d01_retail_ file 4 s after that."""
        return [self.put(os.path.join(self.SB, blob), size, age_s),
                self.put(os.path.join(self.SB, day + ".mst"), 12102, age_s + 51),
                self.put(os.path.join(self.SB, d01), 4593, age_s - 4)]


def snap(top, skip=None):
    """{relative path: (size, mtime_ns, md5)} of every file under top, except under the folder `skip`."""
    out = {}
    for base, dirs, files in os.walk(top):
        if skip and os.path.abspath(base) == os.path.abspath(skip):
            dirs[:] = []
            continue
        for f in files:
            p = os.path.join(base, f)
            st = os.stat(p)
            out[os.path.relpath(p, top)] = (st.st_size, st.st_mtime_ns, md5f(p))
    return out


class Res(object):
    def __init__(self, label):
        self.label = label
        self.rows = []

    def ck(self, cid, cond, what, old="red", prev="same", prev2="same"):
        """cond is called; an exception is a red. `old` = what S205.1 must do with this check, `prev` = what the PREVIOUS
        S499 build (e60e04df, the one the review found faults in) must do: 'red' or 'same'."""
        try:
            v = cond()
            ok, det = (bool(v[0]), str(v[1])) if isinstance(v, tuple) else (bool(v), "")
        except Exception as ex:                                 # noqa: BLE001
            ok, det = False, "%s: %s" % (ex.__class__.__name__, str(ex)[:110])
        exp = {"OLD": old, "PREV": prev, "PREV2": prev2}.get(self.label, "green")
        self.rows.append((cid, ok, what, exp, det))
        return ok


class Harness(object):
    def __init__(self, agent_path, label, work, readers):
        self.src, self.label, self.work, self.n = agent_path, label, work, 0
        self.ps, self.vm = readers
        self.R = Res(label)
        self.new = (label == "NEW")

    def agent(self, w):
        """A fresh copy of the agent, loaded from the scratch folder and pointed at the world w."""
        self.n += 1
        d = os.path.join(self.work, "_mods", "%s_%d" % (self.label, self.n))
        os.makedirs(d)
        p = os.path.join(d, "medical_agent.py")
        shutil.copyfile(self.src, p)
        spec = importlib.util.spec_from_file_location("agent_%s_%d" % (self.label, self.n), p)
        a = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a)
        a.BACKUP_STICK, a.SERVERBACKUP = w.E, w.SB
        a.BACKUP_STATE = os.path.join(w.STC, "backup_state.json")
        a.LOCAL_BEAT = os.path.join(w.STC, "heartbeat.txt")
        a.AGENT_LOG = os.path.join(w.STC, "agent.log")
        a.PIDFILE = os.path.join(w.STC, "_watcher.pid")
        a.KIT_DEST_ROOT = w.STC
        a.WATCHER = os.path.join(w.STC, "marg_watch.py")
        a.SPOOL = os.path.join(w.STC, "_captured")
        a.KIT_FILES = dict((n, os.path.join(w.STC, n)) for n in a.KIT_FILES)
        a.WATCH_DIRS = [os.path.join(w.root, "D_MARGERP", "users"), os.path.join(w.root, "D_MARG_REPORTS"),
                        os.path.join(w.root, "C_Public_MARG")]
        a.PY = sys.executable

        class _Sys(object):                                     # no console: the agent's log FILE is still written, and read below
            stdout = None

            def __getattr__(self, n):
                return getattr(sys, n)
        a.sys = _Sys()
        a.time = w.clock
        a.now = lambda: dt.datetime.fromtimestamp(w.clock.time())
        a._walk_file = p
        if os.path.isdir(os.path.dirname(w.KIT)):
            shutil.copyfile(p, os.path.join(os.path.dirname(w.KIT), "medical_agent.py"))   # so AGENT reads "up to date"
        return a

    def beat(self, a):
        b = a.build_beat(True, 4242, "2026-10-06T10:24:04", 0, {})
        return b, a.human(b)

    def readers(self, cid, a, w, what, old="same", prev="same", prev2="same"):
        """The two real readers on this agent's heartbeat. One check; S205.1 must pass it as well (but for one, said there)."""
        def go():
            b, txt = self.beat(a)
            a.write_beat(b)
            st = b["backup"]
            bad = []

            def eq(name, got, want):
                if got != want:
                    bad.append("%s: read %r, the agent says %r" % (name, got, want))
            r = self.ps._backup_from_heartbeat(txt)
            ww, hh, ign = self.ps.heartbeat_state(a.LOCAL_BEAT)
            eq("pipeline reported", r["reported"], True)
            eq("pipeline stick_age_days", r["stick_age_days"], st.get("newest_stick_age_days"))
            if st.get("newest_stick") and ")" not in st["newest_stick"]:
                eq("pipeline newest", r["newest"], st.get("newest_stick"))
            eq("pipeline serverbackup_age_days", r["serverbackup_age_days"], st.get("newest_serverbackup_age_days"))
            if st.get("offsite"):
                eq("pipeline offsite_files", r["offsite_files"], st.get("offsite_files"))
                eq("pipeline offsite_gb", r["offsite_gb"], float("%.2f" % (st.get("offsite_bytes", 0) / (1024.0 ** 3))))
                eq("pipeline offsite_complete", r["offsite_complete"], not st.get("pending"))
                if st.get("pending"):
                    eq("pipeline pending", r["pending"], st["pending"])
            else:
                eq("pipeline offsite_files (no Drive)", r["offsite_files"], None)
            eq("pipeline backup block via heartbeat_state", hh.get("backup"), r)
            eq("pipeline watcher alive", ww.get("alive"), True)
            eq("pipeline captures_today", ww.get("captures_today"), b["captures"]["today"])
            eq("pipeline ignored", ign, b["ignored_by_watcher"]["count"])
            v = self.vm.parse_heartbeat(txt)
            eq("verify written_at", v["written_at"], b["written_at"])
            eq("verify agent_version", v["agent_version"], b["agent_version"])
            eq("verify computer", v["computer"], b["computer"])
            eq("verify watcher_alive", v["watcher_alive"], True)
            eq("verify watcher_pid", v["watcher_pid"], 4242)
            eq("verify watching", v["watching"], a.WATCH_DIRS)
            eq("verify missing_watch_dirs", self.vm.missing_watch_dirs(v["watching"], a.WATCH_DIRS), [])
            eq("verify agent_uptodate", v["agent_uptodate"], True if os.path.isdir(w.FM) else None)
            eq("verify ignored", v["ignored"], b["ignored_by_watcher"]["count"])
            eq("verify captures_today", v["captures_today"], b["captures"]["today"])
            eq("verify backup_absent", v["backup_absent"], st.get("newest_stick_age_days") is None)
            eq("verify backup_days", v["backup_days"], st.get("newest_stick_age_days"))
            eq("verify disk_free_gb", v["disk_free_gb"], b["disk_free_gb_D"])
            if b["disk_free_gb_D"] is None:
                bad.append("the walk's D: folder gave no disk figure, so DISK was not exercised")
            if os.path.isdir(w.FM):
                j = json.load(open(os.path.join(w.FM, "heartbeat.json"), encoding="utf-8"))
                eq("heartbeat.json on Drive", j, json.loads(json.dumps(b)))
                eq("heartbeat.txt on Drive", open(os.path.join(w.FM, "heartbeat.txt"), encoding="utf-8").read(), txt)
            eq("the guard's reading (heartbeat.txt is there, just written)",
               os.path.isfile(a.LOCAL_BEAT) and abs(os.path.getmtime(a.LOCAL_BEAT) - _time.time()) < 60, True)
            return (not bad, "; ".join(bad[:3]))
        return self.R.ck(cid, go, "the readers parse it (%s)" % what, old=old, prev=prev, prev2=prev2)


def loud(txt):
    return [l for l in txt.splitlines() if l.startswith("***")]


def has_line(txt, pattern):
    return any(re.search(pattern, l) for l in txt.splitlines())


def stray(top):
    return [f for b, _d, fs in os.walk(top) for f in fs if f.endswith((".part", ".copying"))]


HAND = "d1-sanjeevni-20260401-20270331_7js0k0lvn.mbk"
BLOB, MST, D01 = "45209_c18_d_fihkb.jmbkh_46883", "thursday", "35524_d01_retail_gfihk.hifgd_82976"
BLOB2, MST2, D012 = "67521_c18_d_cyedg.lpojm_37724", "wednesday", "45325_d01_retail_ihkbm.khifg_25457"


# ================================================================== the scenarios
def scen_A(H):
    R = H.R
    # ---- the stick is not there
    w = World(H.work, H.label + "_A1", stick=False)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    box = {}

    def go():
        box["st"] = a.backup_pass()
        box["b"], box["t"] = H.beat(a)
        return True
    R.ck("A.01", go, "stick absent: the pass and the heartbeat do not crash", old="same")
    R.ck("A.02", lambda: has_line(box["t"], r"^BACKUP  : NO BACKUP FILE ON .* -- the stick is empty or absent$"),
         "stick absent: the BACKUP line is the one the readers know", old="same")
    R.ck("A.03", lambda: box["st"]["stick_present"] is False and has_line(box["t"], r"STICK ABSENT: .* is not there"),
         "stick absent: stick_present is false and a plain line says the stick is not there")
    R.ck("A.04", lambda: (loud(box["t"]) == [], str(loud(box["t"]))),
         "stick absent, Marg's own backup fresh and offsite: no loud line (as before)", old="same")
    R.ck("A.05", lambda: (box["st"]["copied"] == 3 and len(os.listdir(w.OFF)) == 3, box["st"]["copied"]),
         "stick absent: Marg's own three files still go offsite", old="same")
    R.ck("A.06", lambda: not os.path.exists(w.E), "stick absent: the agent does not make the stick's folder itself", old="same")
    since0 = {}
    R.ck("A.13", lambda: since0.update(json.load(open(a.BACKUP_STATE))) or
         (since0["stick_absent_since"] and has_line(box["t"], r"STICK ABSENT: .* is not there since \d\d-\w\w\w-\d{4} \d\d:\d\d")),
         "stick absent: the state records since when, and the calm line says it", prev="red")
    w.clock.advance(1.5 * DAY)
    w.sb_set(MST2, BLOB2, D012, 3 * 3600)
    st_a = {}
    R.ck("A.14", lambda: st_a.update(a.backup_pass()) or
         (st_a["stick_absent_since_ts"] == since0["stick_absent_since_ts"]
          and [l.startswith("*** NO MARG BACKUP ON THE STICK -- the backup stick is not plugged in since ")
               for l in loud(H.beat(a)[1])] == [True]),
         "still absent a day and a half later: the SAME 'since', and now ONE loud line -- the stick is not plugged in since then",
         prev="red")
    os.makedirs(os.path.join(w.E, "MargAuto_by_agent"))
    st_b = {}
    R.ck("A.15", lambda: st_b.update(a.backup_pass()) or (st_b["stick_absent_since"] is None and loud(H.beat(a)[1]) == []
                                                          and st_b["stick_copy"]["copied"] == 3),
         "plugged back in: the 'since' is cleared, Marg's backup is copied, no loud line", prev="red")
    H.readers("A.07", a, w, "stick absent")
    # ---- Drive is not there, the stick is
    w = World(H.work, H.label + "_A2", drive=False)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    w.put(os.path.join(w.E, HAND), 28685, 4 * DAY)
    a = H.agent(w)
    R.ck("A.08", lambda: bool(a.backup_pass()) or True, "Drive absent: the pass does not crash", old="same")
    R.ck("A.09", lambda: sorted(os.listdir(os.path.join(w.AUTO, os.listdir(w.AUTO)[0]))) == sorted([BLOB, MST + ".mst", D01]),
         "Drive absent: Marg's own backup STILL goes to the stick")
    R.ck("A.10", lambda: json.load(open(a.BACKUP_STATE))["note"].startswith("clinic Drive not found"),
         "Drive absent: the state is written all the same, and says Drive was not found")
    R.ck("A.11", lambda: has_line(H.beat(a)[1], r"^          offsite: clinic Drive not found"),
         "Drive absent: the heartbeat says so")
    H.readers("A.12", a, w, "Drive absent", old="red")     # S205.1 wrote no state at all without Drive: "not checked yet"


def scen_B(H):
    R = H.R
    w = World(H.work, H.label + "_B")
    w.put(os.path.join(w.E, HAND), 28685, 4 * DAY)
    w.put(os.path.join(w.E, "MARGBCKUP", "d1-sanjeevni-20250401-20260331_7ap0vevz1.mbk"), 25997, 364 * DAY)
    w.put(os.path.join(w.E, "85139_c18_2554.nlpoj_83319"), 16759, 88 * DAY)       # a database file a person once put on the stick
    fresh = w.sb_set(MST, BLOB, D01, 3 * 3600)
    w.sb_set(MST2, BLOB2, D012, 27 * 3600, size=29027)
    w.put(os.path.join(w.SB, "tuesday.mst"), 12240, 51 * 3600)                    # a day Marg wrote no database file
    a = H.agent(w)
    stick0, sb0 = snap(w.E), snap(w.SB)
    box = {}

    def p1():
        box["st"] = a.backup_pass()
        box["b"], box["t"] = H.beat(a)
        return True
    R.ck("B.01", p1, "the pass runs", old="same")
    sets = lambda: sorted(os.listdir(w.AUTO))                                     # noqa: E731
    setdir = lambda: os.path.join(w.AUTO, sets()[0])                              # noqa: E731
    R.ck("B.02", lambda: (sorted(os.listdir(setdir())) == sorted(os.path.basename(p) for p in fresh), os.listdir(setdir())),
         "the newest set -- the database file, the .mst, the _d01_ file -- is in the agent's own folder on the stick")
    R.ck("B.03", lambda: all(md5f(os.path.join(setdir(), os.path.basename(p))) == md5f(p) for p in fresh),
         "each copy's md5 is the source's")
    R.ck("B.04", lambda: all(abs(os.path.getmtime(os.path.join(setdir(), os.path.basename(p))) - os.path.getmtime(p)) < 0.01
                             for p in fresh), "each copy carries the source's own time")
    R.ck("B.05", lambda: (stray(w.E) == [], stray(w.E)), "no half-copied file is left on the stick", old="same")
    R.ck("B.06", lambda: (len(sets()) == 1 and re.match(r"^\d{4}-\d\d-\d\d_\d{6}$", sets()[0]) is not None, sets()),
         "one dated folder: the older set and the lone .mst were not copied")
    R.ck("B.07", lambda: ((box["st"]["newest_stick"], box["st"]["newest_stick_age_days"]) == (BLOB, 0.1),
                          (box["st"]["newest_stick"], box["st"]["newest_stick_age_days"])),
         "newest_stick is the newest backup of ANY kind on the stick: the automatic copy, 0.1 day")
    R.ck("B.08", lambda: [box["st"][k] for k in ("newest_handmade", "newest_handmade_age_days", "newest_auto_on_stick",
                                                  "newest_auto_on_stick_age_days", "newest_serverbackup_blob",
                                                  "newest_serverbackup_blob_age_days", "newest_serverbackup_offsite",
                                                  "newest_serverbackup_offsite_age_days", "stick_present")]
         == [HAND, 4.0, BLOB, 0.1, BLOB, 0.1, BLOB, 0.1, True], "the new keys: hand-made 4.0 d, automatic 0.1 d, on D: 0.1 d, offsite 0.1 d")
    R.ck("B.09", lambda: has_line(box["t"], r"^BACKUP  : newest backup on the stick is 0\.1 day\(s\) old  \(%s\)$" % re.escape(BLOB)),
         "heartbeat.txt keeps the line's shape and reads fresh")
    R.ck("B.10", lambda: (loud(box["t"]) == [], str(loud(box["t"]))), "NO loud line")
    R.ck("B.11", lambda: has_line(box["t"], r"^          hand-made backup on the stick: 4\.0 day\(s\) old  \(%s\)$" % re.escape(HAND))
         and has_line(box["t"], r"^          automatic copy on the stick: 0\.1 day\(s\) old  \(%s\)$" % re.escape(BLOB))
         and "optional" not in box["t"], "a calm line each for the hand-made backup and the automatic copy")
    R.ck("B.12", lambda: snap(w.E, skip=w.AUTO) == stick0, "everything else on the stick is exactly as it was", old="same")
    R.ck("B.13", lambda: snap(w.SB) == sb0, "nothing in Marg's own folder was touched", old="same")
    R.ck("B.14", lambda: ((box["st"]["copied"], box["st"]["offsite_files"], len(os.listdir(w.OFF))) == (9, 9, 9),
                          (box["st"]["copied"], box["st"]["offsite_files"])),
         "offsite: the 3 stick files and Marg's newest 6 -- the stick copies are not sent a second time", old="same")
    H.readers("B.15", a, w, "hand-made 4 d + a fresh set")
    R.ck("B.16", lambda: json.load(open(os.path.join(w.FM, "heartbeat.json")))["backup"]["stick_copy"]["copied"] == 3,
         "heartbeat.json on Drive carries the stick copy")

    def e1():
        v = H.vm.parse_heartbeat(box["t"])
        return (not v["backup_absent"] and v["backup_days"] is not None and v["backup_days"] <= H.vm.BACKUP_WARN_DAYS,
                "backup_days %s" % v["backup_days"])
    R.ck("B.17", e1, "verify_medical's row E1 (Marg backup on the stick) would read PASS, not WARN")
    # ---- a second pass
    set1, off1 = snap(w.AUTO), snap(w.OFF)
    ino1 = dict((f, os.stat(os.path.join(setdir(), f)).st_ino) for f in os.listdir(setdir())) if os.path.isdir(w.AUTO) else {}
    w.clock.advance(3600)

    def p2():
        box["st2"] = a.backup_pass()
        return True
    R.ck("B.18", p2, "a second pass, an hour later, runs", old="same")
    R.ck("B.19", lambda: ((box["st2"]["stick_copy"]["copied"], box["st2"]["stick_copy"]["already_there"]) == (0, 3),
                          str(box["st2"]["stick_copy"])), "the second pass copies nothing to the stick")
    R.ck("B.20", lambda: snap(w.AUTO) == set1 and len(set1) == 3
         and all(os.stat(os.path.join(setdir(), f)).st_ino == i for f, i in ino1.items()), "the copies were not written again")
    R.ck("B.21", lambda: (box["st2"]["copied"] == 0 and snap(w.OFF) == off1, box["st2"]["copied"]),
         "the second pass copies nothing offsite", old="same")


def scen_C(H):
    R = H.R
    w = World(H.work, H.label + "_C1")
    w.put(os.path.join(w.E, HAND), 28685, 8 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    a.backup_pass()
    t = H.beat(a)[1]
    R.ck("C.01", lambda: has_line(t, r"hand-made backup on the stick: 8\.0 day\(s\) old")
         and has_line(t, r"^          -- optional; the automatic copy is on the stick$"),
         "a hand-made backup over 7 days old: its age, and 'optional; the automatic copy is on the stick'")
    R.ck("C.02", lambda: (loud(t) == [], str(loud(t))), "and no loud line for it")
    H.readers("C.03", a, w, "hand-made 8 d")
    w = World(H.work, H.label + "_C2")
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    a.backup_pass()
    t2 = H.beat(a)[1]
    R.ck("C.04", lambda: (os.listdir(w.E) == [] and has_line(t2, r"STICK HOLDS NO MARG BACKUP: .* is plugged in since .* but holds no")
                          and has_line(t2, r"onto this stick; then the copies start by themselves") and loud(t2) == [], str(os.listdir(w.E))),
         "an E: with no Marg backup and no agent folder on it is NOT written to, and a calm line says so as itself: plugged in, "
         "holds no Marg backup, take one by hand onto it", prev="red", prev2="red")
    w = World(H.work, H.label + "_C3")
    os.makedirs(w.AUTO)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    a.backup_pass()
    t3 = H.beat(a)[1]
    R.ck("C.05", lambda: len(os.listdir(w.AUTO)) == 1 and has_line(t3, r"hand-made backup on the stick: none") and loud(t3) == []
         and has_line(t3, r"^BACKUP  : newest backup on the stick is 0\.1 day"),
         "the agent's own folder already there (no hand-made backup): it is the stick -- copied, said calmly")


def scen_D(H):
    R = H.R
    # ---- Marg wrote to the folder half a minute ago
    w = World(H.work, H.label + "_D1")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.put(os.path.join(w.SB, MST + ".mst"), 12102, 81)
    w.put(os.path.join(w.SB, BLOB), 29124, 30)
    a = H.agent(w)
    st = {}
    R.ck("D.01", lambda: st.update(a.backup_pass()) or True, "the pass runs while Marg is writing", old="same")
    R.ck("D.02", lambda: (st["stick_copy"]["copied"] == 0 and "quiet" in st["stick_copy"]["waiting"]
                          and not os.path.isdir(w.AUTO), str(st.get("stick_copy"))),
         "a folder Marg wrote to 30 s ago is left alone: nothing copied, nothing made on the stick")
    R.ck("D.03", lambda: has_line(H.beat(a)[1], r"^          stick copy waiting: Marg wrote to its backup folder"),
         "and the heartbeat says it is waiting")
    w.put(os.path.join(w.SB, D01), 4593, 26)               # the third file arrives
    w.clock.advance(200)
    st2 = {}
    R.ck("D.04", lambda: st2.update(a.backup_pass()) or (st2["stick_copy"]["copied"] == 3, str(st2["stick_copy"])),
         "once the folder has been quiet for two minutes the whole set is copied")
    # ---- a file whose size changes between the listing and the copy
    w = World(H.work, H.label + "_D2")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    real = getattr(a, "_serverbackup_files", None)

    def stale_listing():
        return [(p, s - 10 if os.path.basename(p) == BLOB else s, m) for p, s, m in real()]
    if real:
        a._serverbackup_files = stale_listing
    st3 = {}
    R.ck("D.05", lambda: st3.update(a.backup_pass()) or
         (st3["stick_copy"]["copied"] == 0 and "changed while it was being read" in st3["stick_copy"]["waiting"]
          and stray(w.E) == [] and not os.path.isdir(w.AUTO), str(st3["stick_copy"])[-200:]),
         "a source whose size differs between two looks is left for the next pass")
    # ---- a source that changes WHILE it is copied
    w = World(H.work, H.label + "_D3")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    one = a._copy_one

    def copy_then_marg_writes(src, dst):
        r = one(src, dst)
        if w.AUTO in dst and os.path.basename(src) == BLOB:
            m = os.path.getmtime(src)
            with open(src, "ab") as fh:
                fh.write(b"MARG WRITES ON")
            os.utime(src, (m, m))                          # even with the time put back, the md5 gives it away
        return r
    a._copy_one = copy_then_marg_writes
    st4 = {}
    R.ck("D.06", lambda: st4.update(a.backup_pass()) or
         (st4["stick_copy"]["copied"] == 0 and len(st4["stick_copy"]["errors"]) == 1 and stray(w.E) == []
          and not os.path.isdir(os.path.join(w.AUTO, st4["stick_copy"]["set"])), str(st4["stick_copy"])),
         "a source that changes during the copy: the copy is thrown away, nothing wears the real name, it is said")


def scen_E(H):
    R = H.R
    w = World(H.work, H.label + "_E")
    w.put(os.path.join(w.E, HAND), 28685, 4 * DAY)
    w.put(os.path.join(w.E, "OTHER", "2026-01-01_000000", "11111_c18_d_aaaaa.bbbbb_22222"), 500, 280 * DAY)   # looks like ours, is not in ours
    w.put(os.path.join(w.AUTO, "note.txt"), b"left by a person", 40 * DAY)
    w.put(os.path.join(w.AUTO, "keepme", "x.bin"), 300, 40 * DAY)
    for i in range(1, 34):                                                       # 33 sets, 1..33 days old
        t = w.clock.time() - i * DAY
        d = os.path.join(w.AUTO, _time.strftime("%Y-%m-%d_%H%M%S", _time.localtime(t)))
        w.put(os.path.join(d, "%05d_c18_d_xxxxx.yyyyy_%05d" % (i, i)), 700, i * DAY)
        w.put(os.path.join(d, "day%d.mst" % i), 120, i * DAY + 51)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    names0 = sorted(d for d in os.listdir(w.AUTO) if re.match(r"^\d{4}-", d))
    out0 = snap(w.E, skip=w.AUTO)
    st = {}
    R.ck("E.01", lambda: st.update(a.backup_pass()) or True, "the pass runs with 33 old sets on the stick", old="same")
    now_sets = lambda: sorted(d for d in os.listdir(w.AUTO) if re.match(r"^\d{4}-", d))      # noqa: E731
    R.ck("E.02", lambda: (len(now_sets()) == 30 and now_sets() == sorted(names0 + [st["stick_copy"]["set"]])[-30:]
                          and st["stick_copy"]["sets_removed"] == 4 and st["stick_copy"]["sets_kept"] == 30,
                          "%d sets, removed %s" % (len(now_sets()), st.get("stick_copy", {}).get("sets_removed"))),
         "34 sets become the newest 30: the four oldest are removed, the new one is kept")
    R.ck("E.03", lambda: snap(w.E, skip=w.AUTO) == out0, "nothing outside the agent's own folder was touched", old="same")
    R.ck("E.04", lambda: open(os.path.join(w.AUTO, "note.txt"), "rb").read() == b"left by a person"
         and os.path.isfile(os.path.join(w.AUTO, "keepme", "x.bin")),
         "inside that folder, a file and a folder the agent did not name are left alone", old="same")
    R.ck("E.05", lambda: all(len(os.listdir(os.path.join(w.AUTO, d))) >= 2 for d in now_sets()),
         "every set kept is whole (its database file and its companions)", old="same")
    off0 = set(os.listdir(w.OFF)) if os.path.isdir(w.OFF) else set()
    w.clock.advance(3600)
    R.ck("E.06", lambda: a.backup_pass()["stick_copy"]["sets_removed"] == 0 and len(now_sets()) == 30
         and off0 <= set(os.listdir(w.OFF)), "the next pass removes nothing more; nothing is ever deleted offsite")
    real = getattr(a, "_prune_stick_sets", None)
    R.ck("E.07", lambda: (real(os.path.join(w.E, "OTHER"))[1] == 0 and real(os.path.join(w.E, "OTHER"))[2] != []
                          and os.path.isfile(os.path.join(w.E, "OTHER", "2026-01-01_000000", "11111_c18_d_aaaaa.bbbbb_22222")),
                          str(real(os.path.join(w.E, "OTHER")))),
         "asked to prune any other folder, the pruner refuses outright")


def scen_F(H):
    R = H.R
    # ---- the stick is full
    w = World(H.work, H.label + "_F1")
    w.put(os.path.join(w.E, HAND), 28685, 4 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    one = a._copy_one

    def full(src, dst):
        if dst.startswith(w.E):
            with open(dst + ".part", "wb") as fh:           # a real full stick leaves the temp file half-written
                fh.write(b"half")
            os.remove(dst + ".part")
            return False, "OSError: [Errno 28] No space left on device"
        return one(src, dst)
    a._copy_one = full
    box = {}

    def go():
        box["st"] = a.backup_pass()
        box["t"] = H.beat(a)[1]
        return True
    R.ck("F.01", go, "stick full: the pass and the heartbeat do not crash", old="same")
    R.ck("F.02", lambda: (len(box["st"]["stick_copy"]["errors"]) == 1 and "No space left" in box["st"]["stick_copy"]["errors"][0]
                          and has_line(box["t"], r"^          STICK COPY FAILED: .*No space left on device")
                          and has_line(box["t"], r"NOT on the stick"), str(box["st"].get("stick_copy"))),
         "stick full: a clear line -- STICK COPY FAILED, with the reason")
    R.ck("F.03", lambda: stray(w.E) == [] and (not os.path.isdir(w.AUTO) or os.listdir(w.AUTO) == []),
         "stick full: no half file and no empty dated folder is left", old="same")
    R.ck("F.04", lambda: (len(loud(box["t"])) == 1 and loud(box["t"])[0] == "*** NO MARG BACKUP ON THE STICK FOR 4.0 DAYS ***"
                          and "is not reaching the stick" in box["t"] and "exactly one place" not in box["t"], str(loud(box["t"]))),
         "stick full and the hand-made 4 d old: the loud line names the STICK, says Marg's own backup is fresh but not reaching it, "
         "and does NOT say 'exactly one place' (the offsite folder has it)")
    R.ck("F.05", lambda: box["st"]["copied"] == 4 and box["st"]["newest_serverbackup_offsite_age_days"] == 0.1,
         "stick full: the offsite leg still ran")
    H.readers("F.06", a, w, "stick full")
    # ---- the stick is write-protected: the folder cannot even be made
    w = World(H.work, H.label + "_F2")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)

    class _os(object):
        def __getattr__(self, n):
            return getattr(os, n)

        def makedirs(self, p, *x, **k):
            if p.startswith(w.E):
                raise PermissionError(13, "The media is write protected", p)
            return os.makedirs(p, *x, **k)
    a.os = _os()
    st = {}
    R.ck("F.07", lambda: st.update(a.backup_pass()) or
         ("cannot make" in st["stick_copy"]["errors"][0] and has_line(H.beat(a)[1], r"STICK COPY FAILED: cannot make"),
          str(st["stick_copy"])), "stick write-protected: no crash, a clear line")
    # ---- Marg's own backup has stopped: the newest database file is 3 days old, the .mst still comes daily
    w = World(H.work, H.label + "_F3")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * DAY)
    w.put(os.path.join(w.SB, "friday.mst"), 12231, 2 * 3600)
    a = H.agent(w)
    a.backup_pass()
    t = H.beat(a)[1]
    R.ck("F.08", lambda: (loud(t) == [], str(loud(t))),
         "Marg's own backup 3 days old, a hand-made one of yesterday on the stick: NO loud line (a gap in Marg's own backup "
         "alone is ordinary on this PC)", old="same", prev="red")
    R.ck("F.09", lambda: "BY MARG ITSELF" not in t and "has stopped" not in t and "exactly one place" not in t,
         "no 'Marg's automatic backup has stopped' text anywhere, and not 'exactly one place'", old="same", prev="red")
    R.ck("F.10", lambda: has_line(t, r"Marg's own serverbackup: 0\.1 day\(s\) old") and has_line(t, r"^          its newest database file: 3\.0 day"),
         "newest_serverbackup_age_days keeps its meaning (any file: 0.1 d); the database file's age is ONE calm line (3.0 d)")
    H.readers("F.11", a, w, "a gap in Marg's own backup")
    w = World(H.work, H.label + "_F3b")
    w.put(os.path.join(w.E, HAND), 28685, 2 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * DAY)
    a = H.agent(w)
    a.backup_pass()
    t3b = H.beat(a)[1]
    R.ck("F.13", lambda: (loud(t3b) == [], str(loud(t3b))),
         "hand-made 2 d, Marg's own 3 d (so the stick's newest is 2 d): no loud line", old="same", prev="red")
    # ---- no database file at all
    w = World(H.work, H.label + "_F4")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.put(os.path.join(w.SB, "friday.mst"), 12231, 2 * 3600)
    a = H.agent(w)
    a.backup_pass()
    t4 = H.beat(a)[1]
    R.ck("F.12", lambda: (loud(t4) == [] and has_line(t4, r"^          it holds no database file yet$"), str(loud(t4))),
         "Marg's folder holds no database file (only .mst days): one calm line, no loud one", prev="red")


def scen_G(H):
    R = H.R
    w = World(H.work, H.label + "_G1")
    w.put(os.path.join(w.E, HAND), 28685, 5 * DAY)
    w.sb_set(MST, BLOB, D01, 4 * DAY)
    a = H.agent(w)
    a.backup_pass()
    t = H.beat(a)[1]
    R.ck("G.01", lambda: (loud(t) == ["*** NO MARG BACKUP ON THE STICK FOR 4.0 DAYS ***"], str(loud(t))),
         "both stale: ONE loud line -- the stick's, the only measurement that is loud", prev="red")
    R.ck("G.02", lambda: t.count("exactly one place") == 1 and "this PC's D: disk" in t,
         "the stick in and stale, the offsite folder read, nothing newer in it: 'exactly one place' is said, once, and names "
         "the place")
    R.ck("G.03", lambda: has_line(t, r"^BACKUP  : newest backup on the stick is 4\.0 day\(s\) old  \(%s\)$" % re.escape(BLOB)),
         "the stick's newest is the 4-day-old automatic copy, not the 5-day-old hand-made one")
    H.readers("G.04", a, w, "both stale")
    # ---- the hand-made backup stale, Marg's own fresh and on the stick: quiet
    w = World(H.work, H.label + "_G2")
    w.put(os.path.join(w.E, HAND), 28685, 6 * DAY)
    w.sb_set(MST, BLOB, D01, 1.9 * DAY)
    a = H.agent(w)
    a.backup_pass()
    R.ck("G.05", lambda: loud(H.beat(a)[1]) == [], "hand-made 6 d old, Marg's own 1.9 d old and on the stick: no loud line")
    # ---- the edges of the two limits
    w = World(H.work, H.label + "_G3")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 2.2 * DAY)
    a = H.agent(w)
    a.backup_pass()
    R.ck("G.06", lambda: (loud(H.beat(a)[1]) == [], str(loud(H.beat(a)[1]))),
         "Marg's own backup 2.2 d old, the stick fresh: no loud line", old="same", prev="red")


def scen_H(H):
    R = H.R
    names = ["data/acmast.c18", "data/bill.c18", "data/item.c18", "margstart.csv"]
    zips = {"count": 0, "opened": 0}

    def world(tag, hand_bytes, auto_bytes, far_bytes=None):
        w = World(H.work, H.label + "_H" + tag)
        w.put(os.path.join(w.E, HAND), hand_bytes, 4 * DAY)
        w.put(os.path.join(w.E, "older.mbk"), older, 9 * DAY)
        w.put(os.path.join(w.SB, BLOB2), auto_bytes, 4 * DAY + 7200)             # two hours from the hand-made one
        w.put(os.path.join(w.SB, MST2 + ".mst"), 12115, 4 * DAY + 7251)
        w.put(os.path.join(w.SB, BLOB), far_bytes or far, 3 * 3600)             # the newest, but not the nearest
        w.put(os.path.join(w.SB, MST + ".mst"), 12102, 3 * 3600 + 51)
        return w
    same_h, same_a = made_zip(names, "hand"), made_zip(names, "auto")
    other_a = made_zip(names[:3] + ["data/other.c18", "extra.c17"], "auto2")
    far, older = made_zip(["far/away.c18"], "far"), made_zip(["old/only.c18"], "older")
    R.ck("H.00", lambda: zipfile.ZipFile(io.BytesIO(same_h)).infolist()[0].flag_bits & 1 == 1
         and _raises(lambda: zipfile.ZipFile(io.BytesIO(same_h)).read(names[0])),
         "the walk's zips are password-protected in shape: the list reads, a member does not", old="same")
    w = world("1", same_h, same_a)
    a = H.agent(w)
    real_listing = getattr(a, "_zip_listing", None)
    if real_listing:
        def counted(p, m):
            zips["count"] += 1
            return real_listing(p, m)
        a._zip_listing = counted
    for meth in ("open", "read", "extract", "extractall"):
        setattr(zipfile.ZipFile, "_walk_" + meth, getattr(zipfile.ZipFile, meth))

        def trap(self, *x, **k):
            zips["opened"] += 1
            raise AssertionError("a member was opened")
        setattr(zipfile.ZipFile, meth, trap)
    try:
        st = {}
        R.ck("H.01", lambda: st.update(a.backup_pass()) or True, "the pass runs with two zips to compare", old="same")
        z = lambda: st["zip_compare"]                                               # noqa: E731
        R.ck("H.02", lambda: ((z()["handmade"]["name"], z()["automatic"]["name"], z()["hours_apart"]) == (HAND, BLOB2, 2.0),
                              "%s / %s" % (z()["handmade"]["name"], z()["automatic"]["name"])),
             "it takes the NEWEST hand-made .mbk and the automatic file NEAREST to it in time (not the newest one)")
        R.ck("H.03", lambda: all(z()[k]["is_zip"] is True and z()[k]["members"] == 4 and z()[k]["password_protected_members"] == 4
                                 and z()[k]["uncompressed_bytes"] == sum(300 + 37 * i for i in range(4))
                                 and re.match(r"^[0-9a-f]{12}$", z()[k]["names_hash"]) for k in ("handmade", "automatic")),
             "for each: is_zip, the member count, the uncompressed bytes, a short hash of the sorted names")
        R.ck("H.04", lambda: z()["same_member_names"] is True and z()["handmade"]["names_hash"] == z()["automatic"]["names_hash"]
             and (z()["names_in_both"], z()["only_in_handmade"], z()["only_in_automatic"]) == (4, 0, 0),
             "the same member names: same_member_names is true")
        R.ck("H.05", lambda: zips["opened"] == 0, "no member was opened, read or extracted", old="same")
        R.ck("H.06", lambda: not any(n in json.dumps(H.beat(a)[0]) or n in H.beat(a)[1] for n in names + ["acmast", "bill.c18"]),
             "no member's name is in heartbeat.json or heartbeat.txt -- only the count and the hash", old="same")
        R.ck("H.07", lambda: has_line(H.beat(a)[1], r"^          \.mbk lists 4 member\(s\), Marg's automatic file 4; same names: yes$"),
             "heartbeat.txt carries one plain sentence of it")
        n0 = zips["count"]
        w.clock.advance(3600)
        st2 = {}
        R.ck("H.08", lambda: st2.update(a.backup_pass()) or (zips["count"] == n0 and st2["zip_compare"] == st["zip_compare"],
                                                              "listings %d -> %d" % (n0, zips["count"])),
             "an hour later it is NOT done again: the day's result is carried")
        w.clock.advance(24 * 3600)
        st3 = {}
        R.ck("H.09", lambda: st3.update(a.backup_pass()) or (zips["count"] == n0 + 2
                                                              and st3["zip_compare"]["checked_ts"] > st["zip_compare"]["checked_ts"]),
             "a day later it is done once more")
        H.readers("H.10", a, w, "with the comparison in it")
        # ---- different names
        w = world("2", same_h, other_a)
        a = H.agent(w)
        st4 = {}
        R.ck("H.11", lambda: st4.update(a.backup_pass()) or
             ((st4["zip_compare"]["same_member_names"], st4["zip_compare"]["names_in_both"], st4["zip_compare"]["only_in_handmade"],
               st4["zip_compare"]["only_in_automatic"], st4["zip_compare"]["automatic"]["members"]) == (False, 3, 1, 2, 5)
              and has_line(H.beat(a)[1], r"same names: no$"), str(st4.get("zip_compare"))[:120]),
             "different member names: same_member_names is false, with how many are in both and in each alone")
        # ---- not a zip
        w = world("3", stuff(28685, "not a zip"), same_a)
        a = H.agent(w)
        st5 = {}
        R.ck("H.12", lambda: st5.update(a.backup_pass()) or
             (st5["zip_compare"]["handmade"]["is_zip"] is False and "could not be read" in st5["zip_compare"]["handmade"]["note"]
              and st5["zip_compare"]["automatic"]["is_zip"] is True and st5["zip_compare"]["same_member_names"] is None
              and has_line(H.beat(a)[1], r"a file list could not be read \(hand-made: not readable as a zip, automatic: zip\)"),
              str(st5.get("zip_compare"))[:120]),
             "a hand-made file that is not a zip: no crash, is_zip false, the reason kept, same_member_names left unsaid")
        # ---- nothing to compare
        w = World(H.work, H.label + "_H4")
        w.sb_set(MST, BLOB, D01, 3 * 3600)
        a = H.agent(w)
        st6 = {}
        R.ck("H.13", lambda: st6.update(a.backup_pass()) or
             (st6["zip_compare"]["checked_ts"] is None and "no hand-made .mbk" in st6["zip_compare"]["note"]),
             "no hand-made .mbk on the stick: nothing compared, said, and tried again next pass")
    finally:
        for meth in ("open", "read", "extract", "extractall"):
            setattr(zipfile.ZipFile, meth, getattr(zipfile.ZipFile, "_walk_" + meth))


def _raises(fn):
    try:
        fn()
    except Exception:                                           # noqa: BLE001
        return True
    return False


def scen_J(H):
    R = H.R

    def baks(w, name, n, sub=""):
        base = os.path.join(w.STC, sub, name)
        w.put(base, b"live " + name.encode(), 0)
        for i in range(n):
            w.put("%s.before_%08x" % (base, i + 1), b"old %d" % i, (i + 1) * DAY)

    def line(a):
        return [l for l in H.beat(a)[1].splitlines() if l.startswith("BACKUPS :")]
    # ---- twelve: three beside each of the four built-in files
    w = World(H.work, H.label + "_J1")
    a = H.agent(w)
    for n in a.KIT_FILES:
        baks(w, n, 3)
    a.prune_kit_backups()
    R.ck("J.01", lambda: H.beat(a)[0]["kit_backups"] == 12, "twelve .before_ copies -- three per built-in kit file -- are counted", old="same")
    R.ck("J.02", lambda: (line(a) == [], str(line(a))), "twelve is what the prune allows: NO 'BACKUPS :' line")
    # ---- the medical PC as it stands: six in all, none over three
    w = World(H.work, H.label + "_J2")
    a = H.agent(w)
    for n, k in zip(sorted(a.KIT_FILES), (3, 1, 1, 1)):
        baks(w, n, k)
    a.prune_kit_backups()
    R.ck("J.03", lambda: (H.beat(a)[0]["kit_backups"] == 6 and line(a) == [], str(line(a))),
         "six in all, none over three (the live PC today): NO 'BACKUPS :' line")
    # ---- a built-in file with five: the prune keeps the newest three
    w = World(H.work, H.label + "_J3")
    a = H.agent(w)
    baks(w, "marg_watch.py", 5)
    w.put(os.path.join(w.STC, "medical_agent.py.before_70d5c4e3"), b"the installer's backup", 9 * DAY)
    R.ck("J.04", lambda: a.prune_kit_backups() == (2, 0)
         and sorted(f for f in os.listdir(w.STC) if ".before_" in f and f.startswith("marg_watch"))
         == ["marg_watch.py.before_%08x" % i for i in (1, 2, 3)], "five beside a built-in file: the two oldest go", old="same")
    R.ck("J.05", lambda: os.path.isfile(os.path.join(w.STC, "medical_agent.py.before_70d5c4e3")) and H.beat(a)[0]["kit_backups"] == 3,
         "the installer's own backup of the agent is neither pruned nor counted", old="same")
    # ---- a file the manifest delivers
    w = World(H.work, H.label + "_J4")
    a = H.agent(w)
    w.put(os.path.join(w.KIT, "KIT_MANIFEST.txt"),
          ("marg_txt.py | %s | %s\n_off_READ_ME.txt | %s | %s\n"
           % (os.path.join(w.STC, "marg_txt.py"), "a" * 32, os.path.join(w.STC, "_off", "READ_ME.txt"), "b" * 32)).encode(), 0)
    baks(w, "marg_txt.py", 6)
    baks(w, "READ_ME.txt", 4, sub="_off")
    R.ck("J.06", lambda: (H.beat(a)[0]["kit_backups"] == 10, H.beat(a)[0]["kit_backups"]),
         "copies beside a file the MANIFEST delivers are counted (6 + 4)")
    R.ck("J.07", lambda: line(a) == [], "before any prune has been over them, they are not yet called a fault", old="same")
    R.ck("J.08", lambda: a.prune_kit_backups() == (4, 0) and H.beat(a)[0]["kit_backups"] == 6 and line(a) == []
         and len([f for f in os.listdir(os.path.join(w.STC, "_off")) if ".before_" in f]) == 3,
         "and pruned by the same rule: three kept beside each, in a sub-folder too")
    # ---- a prune that cannot remove
    w = World(H.work, H.label + "_J5")
    a = H.agent(w)
    baks(w, "marg_watch.py", 5)

    class _os(object):
        def __getattr__(self, n):
            return getattr(os, n)

        def remove(self, p):
            if ".before_" in p:
                raise PermissionError(13, "Access is denied", p)
            return os.remove(p)
    a.os = _os()
    R.ck("J.09", lambda: a.prune_kit_backups() == (0, 2), "a prune that cannot remove two files reports two failures", old="same")
    R.ck("J.10", lambda: (len(line(a)) == 1 and "the prune could NOT remove 2 old kit copy file(s) (.before_) under %s" % w.STC in line(a)[0]
                          and has_line(H.beat(a)[1], r"it keeps 3 per kit file; 5 are there now; first: .*marg_watch\.py\.before_"),
                          str(line(a))), "then, and only then, the line: what is wrong, how many, where, the first file by name")
    a.os = os
    R.ck("J.11", lambda: a.prune_kit_backups() == (2, 0) and line(a) == [], "the next prune that works clears the line", old="same")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a.backup_pass()
    H.readers("J.12", a, w, "with kit copies about")


def scen_L(H):
    R = H.R
    X = "d1-sanjeevni-20250401-20260331.mbk"                  # the three files of the census of 26-Aug-2026, at their real sizes
    w = World(H.work, H.label + "_L")
    w.put(os.path.join(w.E, X), 4042001, 217 * DAY)
    w.put(os.path.join(w.E, "MARGBCKUP", X), 2548222, 368 * DAY)
    w.put(os.path.join(w.E, "MARG BACKUPS 25", X), 838948, 512 * DAY)
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    a.backup_pass()
    w.clock.advance(3600)
    st2 = a.backup_pass()
    w.clock.advance(3600)
    st3 = a.backup_pass()
    R.ck("L.01", lambda: ((st2["copied"], st2["copied_bytes"], st3["copied"]) == (0, 0, 0),
                          "pass 2 copied %d file(s), %d bytes; pass 3 copied %d" % (st2["copied"], st2["copied_bytes"], st3["copied"])),
         "three backups with ONE name in three folders: after the first pass nothing is copied again")
    R.ck("L.02", lambda: (sorted(os.path.getsize(os.path.join(w.OFF, f)) for f in os.listdir(w.OFF) if "20250401" in f)
                          == [838948, 2548222, 4042001], sorted(f for f in os.listdir(w.OFF) if "20250401" in f)),
         "all three are kept offsite, each under a name of its own")
    R.ck("L.03", lambda: os.path.getsize(os.path.join(w.OFF, X)) == 4042001,
         "the plain name holds the one at the top of the stick (not, as now, the oldest and smallest)")
    R.ck("L.04", lambda: (sorted(st2["offsite_renamed"]) == sorted(f for f in os.listdir(w.OFF) if "__in_" in f)
                          and len(st2["offsite_renamed"]) == 2 and all(f.endswith(".mbk") for f in st2["offsite_renamed"]),
                          str(st2.get("offsite_renamed"))), "the two others carry their folder in their name and keep the .mbk")
    H.readers("L.05", a, w, "the three namesakes")
    return w


def scen_L_upgrade(H_old, H_new):
    """The live state: S205.1 has been looping; S499.1 takes over the same Drive folder."""
    R = H_new.R
    X = "d1-sanjeevni-20250401-20260331.mbk"
    w = World(H_new.work, "UPG_L")
    w.put(os.path.join(w.E, X), 4042001, 217 * DAY)
    w.put(os.path.join(w.E, "MARGBCKUP", X), 2548222, 368 * DAY)
    w.put(os.path.join(w.E, "MARG BACKUPS 25", X), 838948, 512 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    old = H_old.agent(w)
    old.backup_pass()
    w.clock.advance(3600)
    o2 = old.backup_pass()
    R.ck("L.06", lambda: ((o2["copied"], o2["copied_bytes"], os.path.getsize(os.path.join(w.OFF, X))) == (3, 7429171, 838948),
                          "copied %d, %d bytes" % (o2["copied"], o2["copied_bytes"])),
         "[S205.1 on this world] every pass: copied 3, copied_bytes 7,429,171 -- the live heartbeat's own numbers -- and Drive keeps "
         "the 838,948-byte one", old="same")
    new = H_new.agent(w)
    w.clock.advance(3600)
    n1 = new.backup_pass()
    w.clock.advance(3600)
    n2 = new.backup_pass()
    R.ck("L.07", lambda: ((n1["copied"], n2["copied"], os.path.getsize(os.path.join(w.OFF, X))) == (3, 0, 4042001),
                          "first pass %d, second %d" % (n1["copied"], n2["copied"])),
         "S499.1 taking over that Drive folder: three copies once (each to its own name), then none", old="same")


def scen_M(H):
    R = H.R
    w = World(H.work, H.label + "_M")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)                              # newer than Marg's own -> old and new must agree
    w.sb_set(MST, BLOB, D01, 1.5 * DAY)
    a = H.agent(w)
    st = a.backup_pass()
    b, t = H.beat(a)
    R.ck("M.01", lambda: ([k for k in OLD_KEYS if k not in st] == [], [k for k in OLD_KEYS if k not in st]),
         "every key S205.1 wrote in the backup state is there", old="same")
    R.ck("M.02", lambda: ([k for k in OLD_BEAT_KEYS if k not in b] == [], ""), "every top-level key of heartbeat.json is there", old="same")
    R.ck("M.03", lambda: ([st[k] for k in OLD_KEYS[1:]] ==
                          [w.OFF, 4, sum(os.path.getsize(os.path.join(w.OFF, f)) for f in os.listdir(w.OFF)), 0, 0, [], HAND, 1.0, 1.5,
                           4, sum(os.path.getsize(os.path.join(w.OFF, f)) for f in os.listdir(w.OFF)), ""], str([st[k] for k in OLD_KEYS[1:]])),
         "and each holds what it always held: on this world S205.1 and S499.1 give the very same values", old="same")
    R.ck("M.04", lambda: sorted(set(st) - set(OLD_KEYS)) == sorted(
        ["stick_present", "newest_handmade", "newest_handmade_age_days", "newest_auto_on_stick", "newest_auto_on_stick_age_days",
         "newest_serverbackup_blob", "newest_serverbackup_blob_age_days", "newest_serverbackup_offsite",
         "newest_serverbackup_offsite_age_days", "stick_copy", "offsite_renamed", "zip_compare", "stick_absent_since",
         "stick_absent_since_ts", "offsite_measured", "future_dated", "stick_unrecognised_since", "stick_unrecognised_since_ts"]),
         "the keys added are the ones the kit names, no other", prev="red", prev2="red")
    R.ck("M.05", lambda: b["agent_version"] == ("S205.1" if H.label == "OLD" else "S499.1") and has_line(t, r"^agent %s on " % b["agent_version"]),
         "the version it names", old="same")
    R.ck("M.06", lambda: json.loads(json.dumps(b)) == b, "the beat is plain JSON", old="same")

    def spoiled(text):
        open(a.BACKUP_STATE, "w").write(text)
        w.clock.advance(3600)
        s2 = a.backup_pass()
        return s2["newest_stick"] == HAND and json.load(open(a.BACKUP_STATE))["checked_at"] == s2["checked_at"]
    R.ck("M.07", lambda: spoiled("[1, 2]") and spoiled("{half a file") and spoiled(""),
         "a state file that is spoiled (not a dict, cut short, empty) does not stop the next pass", old="same")


def scen_P(H):
    """The main loop itself, a kit install through it, and the things it must go on refusing."""
    R = H.R
    w = World(H.work, H.label + "_P")
    w.put(os.path.join(w.E, HAND), 28685, 4 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    pids = os.path.join(w.STC, "pids")
    os.makedirs(pids)
    watcher = ("import os, sys, time\nopen(os.path.join(%r, str(os.getpid())), 'w').write(' '.join(sys.argv[1:]))\n"
               "# %%s\ntime.sleep(300)\n" % pids)
    w.put(a.WATCHER, (watcher % "the watcher as installed").encode(), 0)
    newer = (watcher % "the watcher the kit delivers").encode()
    w.put(os.path.join(w.KIT, "marg_watch.py"), newer, 0)
    w.put(os.path.join(w.KIT, "extra_note.txt"), b"delivered by the manifest", 0)
    w.put(os.path.join(w.KIT, "medical_agent.py"), b"print('an agent offered down the kit channel')\n", 0)
    w.put(os.path.join(w.KIT, "KIT_MANIFEST.txt"),
          ("extra_note.txt | %s | %s\nmedical_agent.py | %s | %s\noutside.txt | %s | %s\n"
           % (os.path.join(w.STC, "sub", "extra_note.txt"), hashlib.md5(b"delivered by the manifest").hexdigest(),
              os.path.join(w.STC, "medical_agent.py"), "c" * 32, os.path.join(w.root, "elsewhere.txt"), "d" * 32)).encode(), 0)
    seen = {"n": 0}

    def on_sleep(s):
        if s == a.CHECK_EVERY:
            seen["n"] += 1
            if seen["n"] >= 2:
                raise KeyboardInterrupt()
    w.clock.on_sleep = on_sleep
    rc = {}
    try:
        R.ck("P.01", lambda: rc.update(rc=a.main()) or rc["rc"] == 0, "main() runs two turns of its loop and stops cleanly when told to", old="same")
        log = open(a.AGENT_LOG, encoding="utf-8").read() if os.path.isfile(a.AGENT_LOG) else ""
        ver = "S205.1" if H.label == "OLD" else "S499.1"
        R.ck("P.02", lambda: "medical_agent %s starting" % ver in log and log.count("watcher started, pid") == 2,
             "it starts, starts the watcher, and starts it again after the kit's watcher is installed", old="same")
        R.ck("P.03", lambda: md5f(a.WATCHER) == hashlib.md5(newer).hexdigest()
             and os.path.isfile(a.WATCHER + ".before_" + hashlib.md5(newer).hexdigest()[:8])
             and "installed marg_watch.py from the kit and verified" in log, "the kit's watcher is installed, verified, the old one kept", old="same")
        R.ck("P.04", lambda: open(os.path.join(w.STC, "sub", "extra_note.txt"), "rb").read() == b"delivered by the manifest",
             "a file the manifest declares is installed into its sub-folder", old="same")
        R.ck("P.05", lambda: not os.path.exists(os.path.join(w.STC, "medical_agent.py"))
             and not os.path.exists(os.path.join(w.root, "elsewhere.txt")),
             "the agent still does NOT deliver itself, and nothing lands outside its folder", old="same")
        j = json.load(open(os.path.join(w.FM, "heartbeat.json"), encoding="utf-8")) if os.path.isfile(os.path.join(w.FM, "heartbeat.json")) else {}
        R.ck("P.06", lambda: any("REFUSED: medical_agent.py can never be delivered" in k + str(v.get("note"))
                                 for k, v in j["kit"]["files"].items())
             and any("is outside" in str(v.get("note")) for v in j["kit"]["files"].values()),
             "and says so in the heartbeat, for the agent and for the path outside", old="same")
        R.ck("P.07", lambda: j["watcher"]["alive"] is True and j["agent_version"] == ver and j["backup"]["checked_at"]
             and os.path.isfile(a.LOCAL_BEAT) and os.path.isfile(a.BACKUP_STATE),
             "the first turn runs the backup pass and writes the heartbeat, here and on Drive", old="same")
        R.ck("P.08", lambda: sorted(os.listdir(os.path.join(w.AUTO, os.listdir(w.AUTO)[0]))) == sorted([BLOB, MST + ".mst", D01])
             and "stick copy: 3 file(s)" in log, "through main(): the first turn puts Marg's own backup on the stick and logs it")
        R.ck("P.09", lambda: j["kit_backups"] == 1 and j["kit_backup_state"]["prune_ran"] is True and j["kit_backup_state"]["over"] == [],
             "through main(): the prune has run and its state is in the heartbeat")
    finally:
        _time.sleep(1.0)                    # the watcher started last writes its pid as it comes up
        left = os.listdir(pids)
        try:
            left.append(open(a.PIDFILE).read().strip())
        except OSError:
            pass
        for f in left:
            try:
                os.kill(int(f), signal.SIGKILL)
            except (OSError, ValueError):
                pass


def scen_X(H):
    """The review of 08-Oct-2026 (experiments expA, expD, expF, expG in s499/review/exp): each fault as a check. They go RED on
    the previous build (prev="red") and must be green on this one."""
    R = H.R
    import random
    # ---- expA 1: a stranger's drive at E: (a phone, a camera card) is never written to
    w = World(H.work, H.label + "_X1")
    w.put(os.path.join(w.E, "DCIM", "IMG_0001.JPG"), 10, 1 * DAY)
    w.sb_set(MST2, BLOB2, D012, 0.4 * DAY)
    a = H.agent(w)
    e0 = snap(w.E)
    a.backup_pass()
    R.ck("X.01", lambda: (snap(w.E) == e0, sorted(snap(w.E))), "[expA 1] a stranger's drive at E: is left exactly as it was",
         old="same", prev="red")
    # ---- expA 2: a gap in Marg's own backup alone, a fresh hand-made on the stick
    w = World(H.work, H.label + "_X2")
    w.sb_set("monday", "11111_c18_d_aaaaa.bbbbb_22222", "33333_d01_retail_ccccc.ddddd_44444", 2.5 * DAY)
    w.put(os.path.join(w.SB, "tuesday.mst"), 11000, 1.5 * DAY)
    w.put(os.path.join(w.SB, "wednesday.mst"), 11000, 0.5 * DAY)
    w.put(os.path.join(w.E, "d1-sanjeevni-20260401-20270331_x.mbk"), 230000, 0.5 * DAY)
    a = H.agent(w)
    a.backup_pass()
    t = H.beat(a)[1]
    R.ck("X.02", lambda: (loud(t) == [] and has_line(t, r"^          its newest database file: 2\.5 day"), str(loud(t))),
         "[expA 2] Marg's own backup 2.5 d old, a hand-made one of half a day on the stick: one calm line, nothing loud",
         prev="red")
    # ---- expA 3: the stick absent for five days
    w = World(H.work, H.label + "_X3", stick=False)
    w.sb_set(MST2, BLOB2, D012, 0.4 * DAY)
    a = H.agent(w)
    a.backup_pass()
    w.clock.advance(5 * DAY)
    w.sb_set("monday", "67522_c18_d_cyedg.lpojm_37724", "45326_d01_retail_ihkbm.khifg_25457", 0.4 * DAY)
    a.backup_pass()
    t = H.beat(a)[1]
    R.ck("X.03", lambda: (len(loud(t)) == 1 and "not plugged in since" in loud(t)[0], str(loud(t))),
         "[expA 3] the stick out for five days: it is said, loudly", prev="red")
    # ---- expA 4: the stick stale, Drive not found in this pass
    w = World(H.work, H.label + "_X4", drive=False)
    w.put(os.path.join(w.E, "d1-sanjeevni-20260401-20270331_x.mbk"), 230000, 4 * DAY)
    w.put(os.path.join(w.SB, "wednesday.mst"), 11000, 0.5 * DAY)
    w.sb_set("monday", "11111_c18_d_aaaaa.bbbbb_22222", "33333_d01_retail_ccccc.ddddd_44444", 4.2 * DAY)
    a = H.agent(w)
    one = a._copy_one
    a._copy_one = lambda s_, d_: (False, "OSError: [Errno 30] Read-only file system") if d_.startswith(w.E) else one(s_, d_)
    a.backup_pass()
    t = H.beat(a)[1]
    R.ck("X.04", lambda: (loud(t) == ["*** NO MARG BACKUP ON THE STICK FOR 4.0 DAYS ***"] and "exactly one place" not in t, str(loud(t))),
         "[expA 4] the stick stale and Drive not read in this pass: the stick's loud line, and NOT 'exactly one place' (not measured)",
         prev="red")
    # ---- expA 5: the stick absent, Marg's own 3.5 d old (it is offsite)
    w = World(H.work, H.label + "_X5", stick=False)
    w.sb_set("monday", "11111_c18_d_aaaaa.bbbbb_22222", "33333_d01_retail_ccccc.ddddd_44444", 3.5 * DAY)
    a = H.agent(w)
    a.backup_pass()
    t = H.beat(a)[1]
    R.ck("X.05", lambda: (loud(t) == [] and "exactly one place" not in t, str(loud(t))),
         "[expA 5] the stick just found absent, Marg's own 3.5 d old and offsite: no loud line, no 'exactly one place'", old="same", prev="red")
    # ---- expD 1: one set dated 200 days ahead (a PC clock that was wrong), then real daily backups
    w = World(H.work, H.label + "_X6")
    w.put(os.path.join(w.E, "d1-x.mbk"), 1000, 0.2 * DAY)
    w.sb_set("monday", "11111_c18_d_aaaaa.bbbbb_22222", "33333_d01_retail_ccccc.ddddd_44444", -200 * DAY)
    a = H.agent(w)
    a.backup_pass()
    st = {}
    for i in range(1, 4):
        w.clock.advance(DAY)
        w.put(os.path.join(w.SB, "2000%d_c18_d_real.blob_%d" % (i, i)), 29000 + i, 0.3 * DAY)
        st = a.backup_pass()
    t = H.beat(a)[1]
    R.ck("X.06", lambda: (st["newest_stick"] == "20003_c18_d_real.blob_3" and st["newest_stick_age_days"] == 0.3
                          and min(v for k, v in st.items() if k.endswith("_age_days") and v is not None) >= 0
                          and has_line(t, r"^          ignored, dated in the future: 11111_c18_d_aaaaa\.bbbbb_22222 \(dated ")
                          and sum(1 for d in os.listdir(w.AUTO)) >= 3,
                          "newest %s %s, sets %s" % (st.get("newest_stick"), st.get("newest_stick_age_days"), os.listdir(w.AUTO))),
         "[expD 1] a file dated 200 days ahead is ignored for the newest set and every age, and named in one calm line; the real "
         "daily backups reach the stick", prev="red")
    # ---- expD 2: a FAT stick rounds the time up to an even second: the next pass copies nothing
    w = World(H.work, H.label + "_X7")
    w.put(os.path.join(w.E, "d1-x.mbk"), 1000, 0.2 * DAY)
    w.sb_set("monday", "11111_c18_d_aaaaa.bbbbb_22222", "33333_d01_retail_ccccc.ddddd_44444", 0.5 * DAY)
    a = H.agent(w)
    a.backup_pass()
    for b_, _d, fs in os.walk(w.AUTO):
        for f in fs:
            pth = os.path.join(b_, f)
            m2 = (int(os.stat(pth).st_mtime) // 2) * 2 + 2
            os.utime(pth, (m2, m2))
    st7 = {}
    R.ck("X.07", lambda: st7.update(a.backup_pass()) or (st7["stick_copy"]["copied"], st7["stick_copy"]["already_there"]) == (0, 3),
         "[expD 2] FAT's two-second rounding: the next pass copies nothing")
    # ---- expD 4: a spoiled state file must not stop the heartbeat
    def spoiled_beat(content):
        w = World(H.work, H.label + "_X9", stick=False, drive=False)
        a = H.agent(w)
        open(a.BACKUP_STATE, "w").write(content)
        b, t = H.beat(a)
        a.backup_pass()
        return "BACKUP" in t
    R.ck("X.09", lambda: all(spoiled_beat(c) for c in ("[1,2,3]", '"x"', '{"checked_at": "2026-',
                                                         json.dumps({"checked_at": "x", "zip_compare": [1], "stick_copy": "y"}))),
         "[expD 4] a spoiled backup_state.json (a list, a string, cut short, wrong inner types) does not stop the heartbeat",
         prev="red")
    # ---- expF: the rule, on 4000 made-up states
    w = World(H.work, H.label + "_X10")
    w.put(os.path.join(w.E, "d1-x.mbk"), 1000, 0.2 * DAY)
    w.sb_set("monday", "11111_c18_d_aaaaa.bbbbb_22222", "33333_d01_retail_ccccc.ddddd_44444", 0.5 * DAY)
    a = H.agent(w)
    st0 = a.backup_pass()
    b0 = H.beat(a)[0]

    def fuzz():
        rnd = random.Random(7)
        ages = [None, 0.0, 0.4, 1.5, 2.5, 3.5, 8.0]
        for n in range(4000):
            sx = dict(st0)
            for k in ("newest_stick_age_days", "newest_handmade_age_days", "newest_auto_on_stick_age_days",
                      "newest_serverbackup_blob_age_days", "newest_serverbackup_offsite_age_days", "newest_serverbackup_age_days"):
                sx[k] = rnd.choice(ages)
            sx["stick_present"] = rnd.choice([True, False])
            sx["offsite"] = rnd.choice([None, "X:\\MargBackups"])
            sx["offsite_measured"] = rnd.choice([True, False])          # sometimes inconsistent on purpose
            sx["pending"] = rnd.choice([0, 3])
            sx["stick_absent_since_ts"] = rnd.choice([None, w.clock.time() - 0.5 * DAY, w.clock.time() - 2 * DAY])
            sx["stick_copy"] = rnd.choice([{}, {"errors": ["x: OSError: full"], "recognised": True}, {"waiting": "w", "recognised": True},
                                           {"recognised": False, "waiting": "not the stick"}])
            bb = dict(b0)
            bb["backup"] = sx
            t = a.human(bb)
            r = H.ps._backup_from_heartbeat(t)
            v = H.vm.parse_heartbeat(t)
            age = sx["newest_stick_age_days"]
            if r["stick_age_days"] != age or v["backup_days"] != age or v["backup_absent"] != (age is None):
                return False, "readers disagree at state %d" % n
            ld = [l for l in t.splitlines() if l.startswith("***") and "OUT OF DATE" not in l]
            gone = sx["stick_absent_since_ts"] is not None and w.clock.time() - sx["stick_absent_since_ts"] > DAY
            want = int(age is not None and age > 3) + int(gone)
            if len(ld) != want:
                return False, "state %d: %d loud line(s), the rule says %d: %s" % (n, len(ld), want, ld)
            fresh_hand = any(sx[k] is not None and sx[k] <= 3 for k in ("newest_handmade_age_days", "newest_auto_on_stick_age_days"))
            if "exactly one place" in t and not (sx["stick_present"] and sx["offsite"] and sx["offsite_measured"] and age is not None
                                                 and age > 3 and not fresh_hand
                                                 and (sx["newest_serverbackup_offsite_age_days"] is None
                                                      or sx["newest_serverbackup_offsite_age_days"] >= age)):
                return False, "state %d: 'exactly one place' without measuring it" % n
        return True, "4000 states"
    R.ck("X.10", fuzz, "[expF] on 4000 made-up states: loud ONLY for the stick's age over 3 days or the stick out over a day; "
         "'exactly one place' ONLY when measured; the readers always agree", prev="red")
    # ---- expG 1: a link with a set's name inside the agent's folder never leads the pruner out
    w = World(H.work, H.label + "_X11")
    outside = os.path.join(w.E, "MARGBCKUP")
    w.put(os.path.join(outside, "d1-handmade.mbk"), 5000, 400 * DAY)
    os.makedirs(w.AUTO)
    os.symlink(outside, os.path.join(w.AUTO, "2020-01-01_000000"))
    for i in range(31):
        d = os.path.join(w.AUTO, "2026-09-%02d_000110" % (i % 30 + 1) if i < 30 else "2026-10-01_000110")
        w.put(os.path.join(d, "1%04d_c18_d_x.y_1" % i), 100, (40 - i) * DAY)
    a = H.agent(w)
    a._prune_stick_sets(w.AUTO)
    R.ck("X.11", lambda: (os.listdir(outside) == ["d1-handmade.mbk"], os.listdir(outside)),
         "[expG 1] a link with a set's name in the agent's folder: the hand-made backup it leads to is NOT deleted", prev="red")
    # ---- expG 2: the stick full while 30 good sets are on it: nothing is deleted before a new set is whole
    w = World(H.work, H.label + "_X12")
    for i in range(30):
        w.put(os.path.join(w.AUTO, "2026-09-%02d_000110" % (i + 1), "1%04d_c18_d_x.y_1" % i), 100, (40 - i) * DAY)
    w.put(os.path.join(w.E, "d1.mbk"), 100, 9 * DAY)
    w.sb_set("monday", "99999_c18_d_new.blob_1", "88888_d01_retail_a.b_2", 0.3 * DAY)
    a = H.agent(w)
    one = a._copy_one
    a._copy_one = lambda s_, d_: (False, "OSError: [Errno 28] No space left on device") if w.AUTO in d_ else one(s_, d_)
    st12 = a.backup_pass()
    R.ck("X.12", lambda: len(os.listdir(w.AUTO)) == 30 and st12["stick_copy"]["sets_removed"] == 0,
         "[expG 2] the stick full with 30 good sets on it: none is deleted for a set that could not be written")
    # ---- B3: too little free space -- said, and nothing copied
    w = World(H.work, H.label + "_X13")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    import shutil as _sh
    real_du = _sh.disk_usage
    _sh.disk_usage = lambda p: real_du(p)._replace(free=100000) if os.path.abspath(p).startswith(w.E) else real_du(p)
    try:
        st13 = a.backup_pass()
    finally:
        _sh.disk_usage = real_du
    t13 = H.beat(a)[1]
    R.ck("X.13", lambda: (not os.path.isdir(w.AUTO) and has_line(t13, r"STICK COPY FAILED: the stick has only 0\.1 MB free; "
                                                                  r"Marg's backup set needs 0\.4 MB \(ten times its size\)"), str(st13.get("stick_copy"))),
         "[B3] the stick has less than ten times the set's size free: nothing is written, and the line says how much is free",
         prev="red")
    # ---- B4: the FIX line names the NEW installer, in the Drive folder the agent found, and no drive letter of its own
    w = World(H.work, H.label + "_X14")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    a = H.agent(w)
    open(os.path.join(w.cda, "ToMedical", "medical_agent.py"), "a").write("# a newer agent on Drive\n")
    t14 = H.beat(a)[1]
    want = os.path.join(w.cda, "ToMedical", "INSTALL_AGENT_S499.bat")
    R.ck("X.14", lambda: ("*** THIS AGENT IS OUT OF DATE ***" in t14 and ("FIX: double-click  %s  on this PC." % want) in t14
                          and "INSTALL_AGENT.bat" not in t14 and "F:\\" not in t14, [l for l in t14.splitlines() if "FIX" in l]),
         "[B4] OUT OF DATE: the FIX line names ToMedical\\INSTALL_AGENT_S499.bat where the agent found Drive -- not the old "
         "installer, not F:", prev="red")
    # ---- M3: the state file is written whole or not at all
    w = World(H.work, H.label + "_X15")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    a.backup_pass()
    good = open(a.BACKUP_STATE).read()

    class _json(object):
        def __getattr__(self, n):
            return getattr(json, n)

        def dumps(self, *x, **k):
            raise OSError(28, "No space left on device")
    a.json = _json()
    w.clock.advance(3600)
    R.ck("X.15", lambda: (a.backup_pass() or True) and open(a.BACKUP_STATE).read() == good and not os.path.exists(a.BACKUP_STATE + ".tmp"),
         "[M3] a state write that fails half-way leaves the previous state whole (not an empty file)", prev="red")
    a.json = json
    # ---- M2: the copy is forced to the stick before its md5 is believed
    w = World(H.work, H.label + "_X16")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    synced = []

    class _os(object):
        def __getattr__(self, n):
            return getattr(os, n)

        def fsync(self, fd):
            synced.append(os.readlink("/proc/self/fd/%d" % fd))
            return os.fsync(fd)
    a.os = _os()
    a.backup_pass()
    R.ck("X.16", lambda: (len([x for x in synced if x.endswith(".copying") and w.AUTO in x]) == 3, synced),
         "[M2] each copy on the stick is fsync'd before its md5 is compared", prev="red")
    # ---- delta expS 2: a blank, new stick plugged in for two days (the agent restarted in between)
    w = World(H.work, H.label + "_X17")
    w.sb_set("monday", "11111_c18_d_aaaaa.bbbbb_22222", "33333_d01_retail_ccccc.ddddd_44444", 0.5 * DAY)
    a = H.agent(w)
    a.backup_pass()
    w.clock.advance(2 * DAY)
    a = H.agent(w)
    w.sb_set("tuesday", "11112_c18_d_aaaaa.bbbbb_22222", "33334_d01_retail_ccccc.ddddd_44444", 0.3 * DAY)
    st17 = a.backup_pass()
    t17 = H.beat(a)[1]
    R.ck("X.17", lambda: (len(loud(t17)) == 1 and "is plugged in but holds no Marg backup since" in loud(t17)[0]
                          and "Take one in Marg by hand onto this stick (then copies start by themselves)." in t17
                          and "not plugged in" not in t17 and st17["stick_absent_since"] is None
                          and st17["stick_unrecognised_since_ts"] is not None and os.listdir(w.E) == [], str(loud(t17))),
         "[delta expS 2] a blank stick plugged in for two days: NOT 'the stick is not plugged in' but, loudly, 'E: is plugged in "
         "but holds no Marg backup -- take one by hand onto this stick'", prev="red", prev2="red")
    # ---- delta (e): a file with a time Windows cannot express never stops the pass or the heartbeat
    w = World(H.work, H.label + "_X18")
    w.put(os.path.join(w.E, HAND), 28685, 1 * DAY)
    w.sb_set(MST, BLOB, D01, 3 * 3600)
    a = H.agent(w)
    real_sb = a._serverbackup_files
    a._serverbackup_files = lambda: [(os.path.join(w.SB, "99999_c18_d_bad.time_1"), 100, 3e11)] + real_sb()
    st18 = {}
    R.ck("X.18", lambda: st18.update(a.backup_pass()) or ("BACKUP" in H.beat(a)[1] and st18["stick_copy"]["copied"] == 3
                                                          and any("99999_c18_d_bad.time_1 (dated ?)" in x for x in st18["future_dated"])),
         "[delta e] a source dated in the year 11 476 (a time no clock can show): the pass, the copy and the heartbeat all go on; "
         "the file is named with its date as '?'", prev="red", prev2="red")
    # ---- delta expS 1: the real stick's layout -- .MBK in sub-folders, upper case
    w = World(H.work, H.label + "_X19")
    w.put(os.path.join(w.E, "MARGBCKUP", "D1-SANJEEVNI-20250401-20260331.MBK"), 25482, 30 * DAY)
    w.put(os.path.join(w.E, "MARG BACKUPS 25", "d1-sanjeevni-20250401-20260331.mbk"), 8389, 60 * DAY)
    w.sb_set(MST, BLOB, D01, 0.5 * DAY)
    a = H.agent(w)
    st19 = a.backup_pass()
    R.ck("X.19", lambda: st19["stick_copy"]["recognised"] is True and st19["stick_copy"]["copied"] == 3,
         "[delta expS 1] the real stick's layout (.MBK in sub-folders, upper case) is recognised and copied to", prev="red")


def run_suite(agent_path, label, work, readers):
    H = Harness(agent_path, label, work, readers)
    for scen in (scen_A, scen_B, scen_C, scen_D, scen_E, scen_F, scen_G, scen_H, scen_J, scen_L, scen_M, scen_P, scen_X):
        try:
            scen(H)
        except Exception as ex:                                 # noqa: BLE001 -- a scenario an old file cannot even set up is a red, by name
            H.R.ck(scen.__name__ + ".setup", lambda: (False, "%s: %s" % (ex.__class__.__name__, str(ex)[:110])),
                   "the scenario could be set up", old="red", prev="red", prev2="red")
    return H


# ================================================================== Q: function by function
def scen_Q(R, old_path, new_path):
    def funcs(p):
        src = open(p, encoding="utf-8").read()
        tree = ast.parse(src)
        out = {}
        for n in tree.body:
            if isinstance(n, ast.FunctionDef):
                out[n.name] = ast.get_source_segment(src, n)
        consts = {}
        for n in tree.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                consts[n.targets[0].id] = ast.get_source_segment(src, n)
        tail = src[src.index('if __name__ == "__main__":'):]
        return out, consts, tail
    fo, co, to = funcs(old_path)
    fn, cn, tn = funcs(new_path)
    R.ck("Q.01", lambda: (set(fn) - set(fo) == ADDED, sorted(set(fn) - set(fo) ^ ADDED)), "the functions added are the ones the kit names", old="same")
    R.ck("Q.02", lambda: (set(fo) - set(fn) == set(), sorted(set(fo) - set(fn))), "no function is removed", old="same")
    R.ck("Q.03", lambda: (set(k for k in fo if k in fn and fo[k] != fn[k]) == CHANGED,
                          sorted(set(k for k in fo if k in fn and fo[k] != fn[k]) ^ CHANGED)),
         "the functions changed are the %d the kit names; the other %d are identical to the letter" % (len(CHANGED), len(fo) - len(CHANGED)),
         old="same")
    R.ck("Q.04", lambda: (sorted(k for k in co if k not in cn or co[k] != cn[k]) == ["AGENT_VERSION"],
                          sorted(k for k in co if k not in cn or co[k] != cn[k])),
         "of S205.1's module constants only AGENT_VERSION differs (paths, cadences, limits, KIT_FILES, KIT_NEVER: the same)", old="same")
    R.ck("Q.05", lambda: to == tn, "the crash handler at the foot of the file is identical", old="same")

    def main_delta():
        import difflib
        d = [l for l in difflib.unified_diff(fo["main"].splitlines(), fn["main"].splitlines(), lineterm="", n=0)
             if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        return (all(l.startswith("+") for l in d) and len(d) == 7 and sum("prune_kit_backups()" in l for l in d) == 1, "\n".join(d))
    R.ck("Q.06", main_delta, "main() differs by seven ADDED lines -- the hourly prune, guarded -- and nothing taken away", old="same")


# ================================================================== K: the kit itself
def scen_K(R, kit, old_path, work):
    new_path = os.path.join(kit, "medical_agent.py")
    make = os.path.join(kit, "make_s499.py")
    inst = open(os.path.join(kit, "install_s499.py"), encoding="utf-8").read()
    R.ck("K.01", lambda: md5f(old_path) == FROM_MD5, "the old agent given to the walk is the FROM pin 70d5c4e3", old="same")

    def rebuild():
        out = os.path.join(work, "_rebuild")
        r = subprocess.run([sys.executable, "-B", make, "--agent", old_path, "--out", out], capture_output=True, text=True)
        return (r.returncode == 0 and md5f(os.path.join(out, "medical_agent.py")) == md5f(new_path), (r.stdout + r.stderr).strip()[-160:])
    R.ck("K.02", rebuild, "make_s499.py builds the kit's medical_agent.py again, byte for byte, from the FROM file", old="same")

    def refuses(src_bytes, tag):
        p = os.path.join(work, "_refuse_%s.py" % tag)
        open(p, "wb").write(src_bytes)
        out = os.path.join(work, "_refuse_%s" % tag)
        r = subprocess.run([sys.executable, "-B", make, "--agent", p, "--out", out], capture_output=True, text=True)
        return (r.returncode != 0 and "nothing built" in (r.stdout + r.stderr) and not os.path.exists(out), (r.stdout + r.stderr).strip()[-120:])
    R.ck("K.03", lambda: refuses(open(old_path, "rb").read().replace(b"S205.1", b"S205.2", 1), "changed"),
         "make_s499.py refuses a FROM file that is one character off (and writes nothing)", old="same")
    R.ck("K.04", lambda: refuses(open(new_path, "rb").read(), "built"), "and refuses to build on top of its own output", old="same")
    R.ck("K.05", lambda: ('TO_MD5 = "%s"' % md5f(new_path) in inst and 'FROM_MD5 = "%s"' % FROM_MD5 in inst, ""),
         "install_s499.py's TO pin is the kit's medical_agent.py; its FROM pin is 70d5c4e3", old="same")

    def bat():
        raw = open(os.path.join(kit, "INSTALL_AGENT_S499.bat"), "rb").read()
        bad = []
        if any(c > 126 or (c < 32 and c not in (13, 10)) for c in raw):
            bad.append("a byte outside plain ASCII")
        if raw.count(b"\r\n") != raw.count(b"\n") or raw.count(b"\r") != raw.count(b"\n"):
            bad.append("a line ending that is not CRLF")
        if ('set "WANT=%s"' % md5f(os.path.join(kit, "install_s499.py"))).encode() not in raw:
            bad.append("its pin is not install_s499.py's md5")
        if re.search(rb"(?i)powershell|taskkill|schtasks|wmic", b"\n".join(l for l in raw.split(b"\r\n") if not l.upper().startswith(b"REM"))):
            bad.append("it calls powershell / taskkill / schtasks / wmic")
        return (not bad, "; ".join(bad))
    R.ck("K.06", bat, "INSTALL_AGENT_S499.bat is plain ASCII, CRLF throughout, pins install_s499.py, and kills or schedules nothing", old="same")

    def text_files():
        bad = [f for f in os.listdir(kit) if f.endswith((".py", ".md", ".txt", ".md5")) and b"\r" in open(os.path.join(kit, f), "rb").read()]
        bad += [f for f in os.listdir(kit) if f.endswith(".json") or f.endswith(".pyc") or f == "__pycache__"]
        return (not bad, str(bad))
    R.ck("K.07", text_files, "every .py / .md / .txt / .md5 in the kit is LF; no .json, no .pyc", old="same")
    R.ck("K.08", lambda: open(os.path.join(kit, "KIT_ID.txt"), encoding="utf-8").read().split("\n")[0] == "kit id S499_MEDICAL_AGENT_BACKUP",
         "KIT_ID.txt's first line is the kit's id", old="same")

    def syntax():
        bad = []
        for f in ("medical_agent.py", "install_s499.py"):
            src = open(os.path.join(kit, f), encoding="utf-8").read()
            try:
                ast.parse(src, feature_version=(3, 8))
            except SyntaxError as ex:
                bad.append("%s: %s" % (f, ex))
            if not src.isascii() and f == "install_s499.py":
                bad.append("%s is not ASCII" % f)
        return (not bad, "; ".join(bad))
    R.ck("K.09", syntax, "the two files that run on the medical PC (python 3.11.9 there) parse as Python 3.8 and later", old="same")
    R.ck("K.11", lambda: all(x in open(os.path.join(kit, "README.md"), encoding="utf-8").read() for x in (FROM_MD5, md5f(new_path))),
         "README.md names both pins as they are", old="same")

    def bat_last_word():
        raw = open(os.path.join(kit, "INSTALL_AGENT_S499.bat"), "rb").read().decode("ascii").split("\r\n")
        i = raw.index('if "%RC%"=="0" goto ok')
        return (raw[i + 1] == 'if exist "D:\\SendToClinic\\_off\\AGENT_OFF.txt" goto stilloff'
                and raw[i + 2].startswith("echo   NOT DONE") and "Nothing is left switched off" in raw[i + 2]
                and any("Double-click this file again" in l for l in raw), raw[i + 1])
    R.ck("K.12", bat_last_word, "INSTALL_AGENT_S499.bat says 'Nothing is left switched off' only after checking AGENT_OFF.txt is "
         "not there -- else a plain warning to run it again", old="same")
    R.ck("K.13", lambda: ("has written no database file for over 2 days" not in open(make, encoding="utf-8").read().split('"""')[1]
                          and "A gap in Marg's own backup alone is one calm line" in open(make, encoding="utf-8").read().split('"""')[1]),
         "make_s499.py's head describes the rule as built (no loud line for a gap in Marg's own backup)", old="same")

    def imports(p):
        out = set()
        for n in ast.walk(ast.parse(open(p, encoding="utf-8").read())):
            if isinstance(n, ast.Import):
                out.update(x.name.split(".")[0] for x in n.names)
            elif isinstance(n, ast.ImportFrom):
                out.add((n.module or "").split(".")[0])
            elif isinstance(n, ast.Call) and getattr(n.func, "id", "") == "__import__":
                out.add(n.args[0].value)
        return out
    R.ck("K.10", lambda: (imports(new_path) - imports(old_path) == {"zipfile"} and imports(old_path) <= imports(new_path)
                          and imports(new_path) <= set(sys.stdlib_module_names), sorted(imports(new_path) ^ imports(old_path))),
         "the agent imports the standard library only; zipfile is the one module S499.1 adds to S205.1's", old="same")


# ================================================================== I: the installer, against the real guard
STANDIN = r'''# a stand-in for medical_agent.py %(ver)s -- walk_s499.py only -- mode %(mode)s -- %(salt)s
import os, sys, time
D = os.path.dirname(os.path.abspath(__file__))
VER, MODE = "%(ver)s", "%(mode)s"
open(os.path.join(D, "pids", "%%d_%%s" %% (os.getpid(), VER)), "w").close()
with open(os.path.join(D, "agent.log"), "a") as fh:
    fh.write("%%s  medical_agent %%s starting (python x)\n" %% (time.strftime("%%Y-%%m-%%d %%H:%%M:%%S"), VER))
if MODE == "crash":
    with open(os.path.join(D, "agent.log"), "a") as fh:
        fh.write("medical_agent %%s CRASHED at %%s\n\nTraceback (made up)\n" %% (VER, time.strftime("%%Y-%%m-%%dT%%H:%%M:%%S")))
    sys.exit(1)
while True:
    if MODE != "mute":
        with open(os.path.join(D, "heartbeat.txt"), "w") as fh:
            fh.write("MEDICAL PC HEARTBEAT   x\nagent %%s on WALK (python x)\n\nWATCHER : %%s\n"
                     %% (VER, "DOWN" if MODE == "nowatcher" else "ALIVE, pid %%d" %% os.getpid()))
    time.sleep(0.25)
'''


class Box(object):
    """A made-up D:\\SendToClinic with the REAL guard running a stand-in S205.1, and a kit folder beside a made-up Drive."""

    def __init__(self, work, tag, guard_src, inst_src, to_mode="ok", start_guard=True, to_text=None, holder_poll="1.0",
                 standby=False, live_is_to=False):
        self.root = os.path.join(work, "I_" + tag)
        if os.path.isdir(self.root):
            shutil.rmtree(self.root)
        self.dest = os.path.join(self.root, "SendToClinic")
        self.home = os.path.join(self.root, "home")
        self.cda = os.path.join(self.home, "My Drive", "Clinic Data Archive")
        self.kit = os.path.join(self.cda, "ToMedical", "S499_MEDICAL_AGENT_BACKUP")
        for d in (os.path.join(self.dest, "pids"), os.path.join(self.cda, "FromMedical"), self.kit):
            os.makedirs(d)
        self.old = (STANDIN % {"ver": "S205.1", "mode": "ok", "salt": tag}).encode()
        self.new = to_text if to_text is not None else (STANDIN % {"ver": "S499.1", "mode": to_mode, "salt": tag}).encode()
        self.live = os.path.join(self.dest, "medical_agent.py")
        open(self.live, "wb").write(self.new if live_is_to else self.old)
        open(os.path.join(self.kit, "medical_agent.py"), "wb").write(self.new)
        shutil.copyfile(guard_src, os.path.join(self.dest, "agent_guard.py"))
        self.FROM, self.TO = hashlib.md5(self.old).hexdigest(), hashlib.md5(self.new).hexdigest()
        self.watched, self.estick = os.path.join(self.root, "MARG_users"), os.path.join(self.root, "E_top")
        os.makedirs(self.watched)
        os.makedirs(self.estick)
        self.holder_poll, self.live_is_to, self.standby_proc = holder_poll, live_is_to, None
        d = os.path.join(work, "_mods", "inst_" + tag)
        os.makedirs(d)
        p = os.path.join(d, "install_s499.py")
        shutil.copyfile(inst_src, p)
        spec = importlib.util.spec_from_file_location("inst_" + tag, p)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.m.DEST, self.m.KIT = self.dest, self.kit
        self.m.FROM_MD5, self.m.TO_MD5 = self.FROM, self.TO
        self.m.STOP_WAIT, self.m.START_WAIT, self.m.POLL = 12, 16, 0.2
        self.m.WATCHED, self.m.STICK_TOP = [self.watched], self.estick            # an older installer ignores these
        self.guard = None
        os.environ["USERPROFILE"] = self.home
        if start_guard:
            self.start_guard()
        if standby:
            self.start_standby()

    def start_guard(self):
        env = dict(os.environ, AG_DIR=self.dest, AG_PY=sys.executable, AG_POLL=getattr(self, "holder_poll", "1.0"), AG_STANDBY="3.0")
        env.update(getattr(self, "extra_env", {}))
        self.guard = subprocess.Popen([sys.executable, "-B", os.path.join(self.dest, "agent_guard.py")], env=env, cwd=self.dest,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      start_new_session=True)
        if getattr(self, "live_is_to", False):
            self.wait(lambda: "agent started" in self.glog(), 20)
        else:
            self.wait(lambda: self.beat() == "S205.1", 20)
        _time.sleep(3.2)        # the guard reads a second agent start within 2 s of its own as "the old launcher"; on the PC
        #                         its own waits (20 s, 30 s) keep starts apart, here the walk does

    def start_standby(self):
        """A second account's guard: it cannot take the lock, so it stands by -- and it, too, writes 'AGENT_OFF.txt is present
        -- not starting the agent' when the switch appears (S387's guard reads the switch before the lock)."""
        env = dict(os.environ, AG_DIR=self.dest, AG_PY=sys.executable, AG_POLL="0.5", AG_STANDBY="0.5")
        self.standby_proc = subprocess.Popen([sys.executable, "-B", os.path.join(self.dest, "agent_guard.py")], env=env,
                                             cwd=self.dest, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL, start_new_session=True)
        self.wait(lambda: "standing by" in self.glog(), 10)

    def wait(self, fn, secs):
        t0 = _time.time()
        while _time.time() - t0 < secs:
            if fn():
                return True
            _time.sleep(0.2)
        return bool(fn())

    def beat(self):
        try:
            return re.search(r"^agent (\S+) on", open(os.path.join(self.dest, "heartbeat.txt")).read(), re.M).group(1)
        except (OSError, AttributeError):
            return None

    def alive(self):
        """the versions of the stand-in agents running now"""
        out = []
        for f in os.listdir(os.path.join(self.dest, "pids")):
            pid, ver = f.split("_")
            try:
                os.kill(int(pid), 0)
                with open("/proc/%s/stat" % pid) as fh:
                    if fh.read().split()[2] != "Z":
                        out.append(ver)
            except (OSError, ValueError):
                pass
        return sorted(out)

    def run(self):
        box = self

        class Spy(io.StringIO):
            """the console, and what was printed to it while the guard's switch was there"""
            during = []

            def write(self, x):
                if x.strip() and box.off():
                    Spy.during.append(x.strip())
                return io.StringIO.write(self, x)
        buf = Spy()
        Spy.during = []
        so = sys.stdout
        sys.stdout = buf
        try:
            try:
                rc = self.m.main()
            except BaseException as ex:                         # noqa: BLE001 -- an older installer lets Ctrl-C through
                rc = "died: %s" % ex.__class__.__name__
        finally:
            sys.stdout = so
        self.out = buf.getvalue()
        self.printed_while_off = list(Spy.during)
        m = re.findall(r"^VERDICT   : (.*)$", self.result(), re.M)
        return rc, (m[-1].strip() if m else "")

    def result(self, where="dest"):
        p = os.path.join(self.dest if where == "dest" else os.path.join(self.cda, "FromMedical"), "S499_INSTALL_RESULT.txt")
        return open(p, newline="").read() if os.path.isfile(p) else ""

    def glog(self):
        p = os.path.join(self.dest, "agent_guard.log")
        return open(p).read() if os.path.isfile(p) else ""

    def off(self):
        return os.path.isfile(os.path.join(self.dest, "_off", "AGENT_OFF.txt"))

    def leftovers(self):
        return sorted(f for f in os.listdir(self.dest) if f.endswith((".new_S499", ".restore_S499", ".lock")) and f != "_agent_guard.lock")

    def close(self):
        if getattr(self, "standby_proc", None) and self.standby_proc.poll() is None:
            try:
                os.killpg(self.standby_proc.pid, signal.SIGKILL)
            except OSError:
                pass
            self.standby_proc.wait()
        if self.guard and self.guard.poll() is None:
            try:
                os.killpg(self.guard.pid, signal.SIGKILL)
            except OSError:
                pass
            self.guard.wait()
        for f in os.listdir(os.path.join(self.dest, "pids")):
            try:
                os.kill(int(f.split("_")[0]), signal.SIGKILL)
            except (OSError, ValueError):
                pass


def happy(b, rc, verdict):
    """THE predicate of a good install -- used on the good run, and on runs that must fail it."""
    return (rc == 0 and verdict.startswith("INSTALLED - ") and md5f(b.live) == b.TO
            and md5f(b.live + ".before_" + b.FROM[:8]) == b.FROM and b.beat() == "S499.1" and b.alive() == ["S499.1"]
            and not b.off() and b.leftovers() == [])


def put_back_ok(b, rc, verdict):
    """THE predicate of a clean put-back."""
    return (rc == 1 and verdict.startswith("ROLLED BACK - ") and "the old agent is running again" in verdict
            and md5f(b.live) == b.FROM and b.wait(lambda: b.alive() == ["S205.1"] and b.beat() == "S205.1", 10)
            and not b.off() and b.leftovers() == [])


class RealBox(Box):
    r"""The kit's OWN two files at their OWN pins -- nothing stood in, no pin moved.

    On Linux a name like D:\SendToClinic\agent.log is one file name with backslashes in it, relative to the folder the agent
    runs in. So the made-up D:\SendToClinic is given links under exactly those names: the agent's python, its watcher, its log
    and its heartbeat; a folder called E:\ for the stick and one called D:\MARGERP\serverbackup for Marg's own backup. The
    REAL S205.1 then runs there under the REAL guard, and the REAL installer swaps it for the REAL S499.1."""

    def __init__(self, work, guard_src, inst_src, old_path, new_path):
        self.root = os.path.join(work, "I_real")
        self.dest = os.path.join(self.root, "SendToClinic")
        self.home = os.path.join(self.root, "home")
        self.cda = os.path.join(self.home, "My Drive", "Clinic Data Archive")
        self.kit = os.path.join(self.cda, "ToMedical")
        for d in (os.path.join(self.dest, "pids"), os.path.join(self.cda, "FromMedical"), os.path.join(self.kit, "_kit"),
                  os.path.join(self.dest, "E:\\"), os.path.join(self.dest, "D:\\"), os.path.join(self.dest, "D:\\MARGERP\\serverbackup")):
            os.makedirs(d)
        self.old, self.new = open(old_path, "rb").read(), open(new_path, "rb").read()
        self.live = os.path.join(self.dest, "medical_agent.py")
        open(self.live, "wb").write(self.old)
        open(os.path.join(self.kit, "medical_agent.py"), "wb").write(self.new)      # delivered as the README says: into ToMedical
        shutil.copyfile(guard_src, os.path.join(self.dest, "agent_guard.py"))
        self.FROM, self.TO = hashlib.md5(self.old).hexdigest(), hashlib.md5(self.new).hexdigest()
        watcher = os.path.join(self.dest, "marg_watch.py")
        open(watcher, "w").write("import os, time\nopen(os.path.join(%r, 'pids', '%%d_watcher' %% os.getpid()), 'w').close()\ntime.sleep(600)\n"
                                 % self.dest)
        for name, target in (("D:\\SendToClinic\\pyportable\\python.exe", sys.executable), ("D:\\SendToClinic\\marg_watch.py", watcher),
                             ("D:\\SendToClinic\\agent.log", os.path.join(self.dest, "agent.log")),
                             ("D:\\SendToClinic\\heartbeat.txt", os.path.join(self.dest, "heartbeat.txt"))):
            os.symlink(target, os.path.join(self.dest, name))
        now = _time.time()
        for path, size, age in ((os.path.join(self.dest, "E:\\", HAND), 28685, 4 * DAY),
                                (os.path.join(self.dest, "D:\\MARGERP\\serverbackup", BLOB), 29124, 3 * 3600),
                                (os.path.join(self.dest, "D:\\MARGERP\\serverbackup", MST + ".mst"), 12102, 3 * 3600 + 51),
                                (os.path.join(self.dest, "D:\\MARGERP\\serverbackup", D01), 4593, 3 * 3600 - 4)):
            open(path, "wb").write(stuff(size, os.path.basename(path)))
            os.utime(path, (now - age, now - age))
        d = os.path.join(work, "_mods", "inst_real")
        os.makedirs(d)
        p = os.path.join(d, "install_s499.py")
        shutil.copyfile(inst_src, p)
        spec = importlib.util.spec_from_file_location("inst_real", p)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.pins = (self.m.FROM_MD5, self.m.TO_MD5)                               # as built -- NOT moved
        self.m.DEST, self.m.KIT = self.dest, self.kit
        self.m.STOP_WAIT, self.m.START_WAIT, self.m.POLL = 12, 40, 0.2
        self.guard = None
        os.environ["USERPROFILE"] = self.home
        # the agent starts its watcher by the bare name D:\\SendToClinic\\pyportable\\python.exe: found here through PATH
        self.extra_env = {"PATH": self.dest + os.pathsep + os.environ.get("PATH", "")}
        self.start_guard()

    def agents(self):
        """the medical_agent.py processes running in this box now"""
        out = []
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                cmd = open("/proc/%s/cmdline" % pid, "rb").read().split(b"\0")
                if os.readlink("/proc/%s/cwd" % pid) == self.dest and any(c.endswith(b"medical_agent.py") for c in cmd) \
                        and open("/proc/%s/stat" % pid).read().split()[2] != "Z":
                    out.append(int(pid))
            except OSError:
                pass
        return out

    def close(self):
        pids = self.agents()
        Box.close(self)
        for pid in pids:
            try:
                os.killpg(pid, signal.SIGKILL)
            except OSError:
                pass


def scen_I_real(R, work, guard_src, inst_src, old_path, new_path):
    b = RealBox(work, guard_src, inst_src, old_path, new_path)
    try:
        fm = os.path.join(b.cda, "FromMedical")
        txt = lambda: open(os.path.join(fm, "heartbeat.txt"), encoding="utf-8").read()                # noqa: E731
        js = lambda: json.load(open(os.path.join(fm, "heartbeat.json"), encoding="utf-8"))            # noqa: E731
        R.ck("I.20", lambda: (b.pins == (FROM_MD5, md5f(new_path)) and (md5f(b.live), b.TO) == b.pins and b.beat() == "S205.1"
                              and len(b.agents()) == 1 and "*** THIS AGENT IS OUT OF DATE ***" in txt()
                              and "*** NO MARG BACKUP FOR 4.0 DAYS ***" in txt(), "pins %s, beat %s, agents %s" % (b.pins, b.beat(), b.agents())),
             "[the kit's own files, their own pins] the REAL S205.1 runs under the real guard; with the new file in ToMedical it says "
             "OUT OF DATE, and it raises the 4-day alarm", old="same")
        old_pid = b.agents()
        rc, v = b.run()
        R.ck("I.21", lambda: (rc == 0 and v.startswith("INSTALLED - ") and md5f(b.live) == md5f(new_path)
                              and md5f(b.live + ".before_70d5c4e3") == FROM_MD5 and not b.off() and b.leftovers() == []
                              and len(b.agents()) == 1 and b.agents() != old_pid, "rc %s, %s | agents %s" % (rc, v[:80], b.agents())),
             "the REAL installer, pins untouched: INSTALLED -- e60e... read back, the old file kept as medical_agent.py.before_70d5c4e3, "
             "one agent running and it is a new process", old="same")
        R.ck("I.22", lambda: (js()["agent_version"] == "S499.1" and js()["agent_self"]["running_md5"] == md5f(new_path)
                              and js()["agent_self"]["differs"] is False and "AGENT   : up to date" in txt()
                              and "THIS AGENT IS OUT OF DATE" not in txt(), js()["agent_self"]),
             "the REAL S499.1's own heartbeat on Drive: agent S499.1, its md5 the TO pin, 'up to date'", old="same")
        auto = os.path.join(b.dest, "E:\\", "MargAuto_by_agent")
        R.ck("I.23", lambda: (sorted(os.listdir(os.path.join(auto, os.listdir(auto)[0]))) == sorted([BLOB, MST + ".mst", D01])
                              and loud(txt()) == [] and js()["backup"]["newest_stick"] == BLOB and js()["backup"]["newest_stick_age_days"] == 0.1
                              and has_line(txt(), r"^BACKUP  : newest backup on the stick is 0\.1 day"), str(loud(txt()))),
             "and its first pass, unprompted: Marg's own backup is on the stick, the stick reads 0.1 day, the alarm is gone", old="same")
        rc2, v2 = b.run()
        R.ck("I.24", lambda: (rc2 == 0 and v2.startswith("ALREADY INSTALLED - ") and len(b.agents()) == 1, v2[:70]),
             "the same double-click again, real pins: ALREADY INSTALLED, the agent left running", old="same")
    finally:
        b.close()


def scen_I(R, work, guard_src, inst_src, which):
    """The installer against the real guard. `which` names the run (new / prev) so the scratch folders do not collide; each
    check declares what the PREVIOUS installer (6ace86a9) must do with it."""
    mk = lambda tag, **k: Box(work, which + "_" + tag, guard_src, inst_src, **k)    # noqa: E731
    boxes = []
    try:
        # ---- I1 / I2: the good run, then the same double-click again
        b = mk("good")
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.01", lambda: (happy(b, rc, v), "rc %s, %s | alive %s, beat %s" % (rc, v[:70], b.alive(), b.beat())),
             "FROM pin live, the guard running the old agent -> INSTALLED: TO read back, the old file kept, the NEW agent running "
             "(one, by its own heartbeat, watcher ALIVE), the switch gone, nothing left over")
        g = b.glog()
        R.ck("I.02", lambda: g.index("AGENT_OFF.txt is present -- agent stopped") < g.rindex("agent started, pid") and g.count("agent started, pid") == 2,
             "it was the GUARD that stopped the old agent and started the new one -- the installer killed and started nothing")
        R.ck("I.03", lambda: all(("FROM      : %s" % b.FROM in t and "TO        : %s" % b.TO in t and "read back : %s" % b.TO in t
                                  and "before    : %s" % b.FROM in t and re.search(r"written   : \d{4}-\d\d-\d\d \d\d:\d\d:\d\d", t)
                                  and "VERDICT   : INSTALLED - " in t and t.isascii() and "\r\n" in t)
                                 for t in (b.result("dest"), b.result("drive"))),
             "S499_INSTALL_RESULT.txt -- in the PC's folder AND in Drive's FromMedical: the time, FROM, TO, the read-back, the verdict")
        R.ck("I.04", lambda: "ToMedical\\medical_agent.py is missing" in b.out and "Do NOT run the old ToMedical\\INSTALL_AGENT.bat" in b.out,
             "it warns when Drive's ToMedical\\medical_agent.py is not the new file (the heartbeat would say OUT OF DATE)")
        R.ck("I.31", lambda: ("Do this when nobody is exporting from Marg." in b.out
                              and "Do NOT click inside this window and do NOT close it until it says DONE or NOT DONE." in b.out),
             "[S1] its first lines say, in plain words: do this when nobody is exporting; do not click inside or close the window",
             prev="red")
        R.ck("I.32", lambda: (b.printed_while_off == [], b.printed_while_off[:3]),
             "[S2] NOTHING is printed while the guard's switch is there (a click in the window would freeze it with the agent off)",
             prev="red")
        rc2, v2 = b.run()
        R.ck("I.05", lambda: (rc2 == 0 and v2.startswith("ALREADY INSTALLED - ") and md5f(b.live) == b.TO and b.alive() == ["S499.1"]
                              and b.glog().count("agent started, pid") == 2 and b.result().count("VERDICT   :") == 2, v2[:80]),
             "a second double-click: ALREADY INSTALLED -- nothing stopped, nothing changed, both runs kept in the result file")
        # ---- I3: the live file is neither pin
        b = mk("otherfile")
        boxes.append(b)
        open(b.live, "ab").write(b"# someone changed it\n")
        before = (md5f(b.live), b.glog(), sorted(os.listdir(b.dest)))
        rc, v = b.run()
        R.ck("I.06", lambda: (rc == 1 and v.startswith("NOT INSTALLED - nothing changed") and "neither the FROM pin" in v
                              and (md5f(b.live), b.glog()) == before[:2] and not b.off() and b.alive() == ["S205.1"]
                              and sorted(set(os.listdir(b.dest)) - set(before[2])) == ["S499_INSTALL_RESULT.txt"], v[:90]),
             "a live file that is neither pin: STOP -- nothing changed, the agent never stopped, no backup, no staged file")
        R.ck("I.07", lambda: not happy(b, rc, v), "[control] the good-install predicate is false here")
        # ---- I4: the kit's file is not the TO pin (Drive still downloading)
        b = mk("badkit")
        boxes.append(b)
        open(os.path.join(b.kit, "medical_agent.py"), "wb").write(b.new[:-40])
        rc, v = b.run()
        R.ck("I.08", lambda: (rc == 1 and "the kit's medical_agent.py is" in v and md5f(b.live) == b.FROM and not b.off()
                              and b.alive() == ["S205.1"] and b.glog().count("agent started") == 1, v[:90]),
             "a kit file that is not the TO pin: STOP, nothing changed")
        # ---- I5: the new agent crashes at its start
        b = mk("crash", to_mode="crash")
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.09", lambda: (put_back_ok(b, rc, v) and "crashed at its start" in v, "rc %s, %s | alive %s" % (rc, v[:90], b.alive())),
             "a new agent that CRASHES at its start: the old file is put back byte-identically (md5 read back) and the old agent "
             "runs again")
        R.ck("I.10", lambda: not happy(b, rc, v) and "VERDICT   : ROLLED BACK" in b.result("drive"),
             "[control] the good-install predicate is false here; the result on Drive says ROLLED BACK")
        # ---- I5b: the new agent starts but never writes a heartbeat
        b = mk("mute", to_mode="mute")
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.11", lambda: (put_back_ok(b, rc, v) and "wrote no heartbeat" in v, "rc %s, %s" % (rc, v[:90])),
             "a new agent that starts but writes NO heartbeat: put back the same way")
        # ---- I5c: the new agent runs, but its watcher is down
        b = mk("nowatcher", to_mode="nowatcher")
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.28", lambda: (put_back_ok(b, rc, v) and "WATCHER : ALIVE" in v, "rc %s, %s" % (rc, v[:100])),
             "[S1] a new agent whose heartbeat does not say WATCHER : ALIVE is not called installed: put back", prev="red")
        # ---- MUT: the same crash, the installer's put-back taken out
        b = mk("mutant", to_mode="crash")
        boxes.append(b)
        b.m.put_back = lambda R_, why, ws: setattr(R_, "verdict", "MUTANT: no put-back (%s)" % why)
        rc, v = b.run()
        R.ck("I.12", lambda: (not put_back_ok(b, rc, v) and md5f(b.live) == b.TO, "%s | live is the %s file"
                              % (v[:50], "NEW" if md5f(b.live) == b.TO else "old")),
             "[negative control, MUT] with the put-back taken out, the same crash leaves the NEW file in place: the put-back checks go RED")
        # ---- I6: a TO file that does not compile here
        b = mk("nocompile", to_text=b"def broken(:\n    pass\n# stand-in that does not compile\n")
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.13", lambda: (rc == 1 and "does not compile" in v and md5f(b.live) == b.FROM and not b.off() and b.leftovers() == []
                              and b.alive() == ["S205.1"] and b.glog().count("agent started") == 1, v[:90]),
             "a new file this PC's python cannot compile: STOP before anything is stopped or placed")
        # ---- I7: no guard on record
        b = mk("noguard", start_guard=False)
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.14", lambda: (rc == 1 and v.startswith("NOT INSTALLED - nothing changed: the guard is not running its agent")
                              and md5f(b.live) == b.FROM and not b.off() and b.leftovers() == [], v[:100]),
             "no guarded agent on record: STOP, nothing changed (the installer will not start an agent outside the guard)")
        # ---- I7b: the records say running, but the guard itself is dead
        b = mk("deadguard")
        boxes.append(b)
        os.killpg(b.guard.pid, signal.SIGKILL)
        b.guard.wait()
        rc, v = b.run()
        R.ck("I.15", lambda: (rc == 1 and "the guard did not say 'agent stopped'" in v and md5f(b.live) == b.FROM and not b.off()
                              and b.leftovers() == [] and b.alive() == ["S205.1"], v[:100]),
             "the guard does not answer its switch: the switch is taken away again and NOTHING is changed")
        # ---- I8: a PERSON switched the agent off
        b = mk("wasoff")
        boxes.append(b)
        os.makedirs(os.path.join(b.dest, "_off"))
        open(os.path.join(b.dest, "_off", "AGENT_OFF.txt"), "w").write("switched off by a person\n")
        b.wait(lambda: "AGENT_OFF.txt is present -- agent stopped" in b.glog() and b.alive() == [], 10)
        rc, v = b.run()
        R.ck("I.16", lambda: (rc == 1 and v.startswith("NOT INSTALLED - nothing changed") and "NOT written by this installer" in v
                              and md5f(b.live) == b.FROM and b.off()
                              and open(os.path.join(b.dest, "_off", "AGENT_OFF.txt")).read() == "switched off by a person\n", v[:100]),
             "[B1] AGENT_OFF.txt a PERSON wrote: STOP, nothing changed, the switch left exactly as found", prev="red")
        os.remove(os.path.join(b.dest, "_off", "AGENT_OFF.txt"))
        b.wait(lambda: b.alive() == ["S205.1"] and b.beat() == "S205.1", 15)
        _time.sleep(3.2)
        rc, v = b.run()
        R.ck("I.17", lambda: (happy(b, rc, v), "rc %s %s" % (rc, v[:80])),
             "and once the person deletes it, the old agent comes back and the next double-click installs", prev="red")
        # ---- I9: two double-clicks at once
        b = mk("twice")
        boxes.append(b)
        open(os.path.join(b.dest, "S499_INSTALL.lock"), "w").write("another run")
        rc, v = b.run()
        R.ck("I.18", lambda: (rc == 1 and "another run of this installer" in v and md5f(b.live) == b.FROM and not b.off()
                              and b.alive() == ["S205.1"] and os.path.isfile(os.path.join(b.dest, "S499_INSTALL.lock")), v[:90]),
             "a second run while one is going on: it stands back and changes nothing")
        old_t = _time.time() - 2000
        os.utime(os.path.join(b.dest, "S499_INSTALL.lock"), (old_t, old_t))
        rc, v = b.run()
        R.ck("I.19", lambda: (happy(b, rc, v), v[:80]), "a lock left by a run that died (over 20 minutes old) does not block the next run")
        # ---- expB: the run interrupted (Ctrl-C) while the guard's switch is there
        b = mk("interrupt")
        boxes.append(b)
        real_wait = b.m.wait_for
        fired = []

        def boom(fn, secs):
            if not fired:
                fired.append(1)
                _time.sleep(4.0)
                raise KeyboardInterrupt()
            return real_wait(fn, secs)
        b.m.wait_for = boom
        rc, v = b.run()
        b.m.wait_for = real_wait
        b.wait(lambda: len(b.alive()) == 1, 15)
        R.ck("I.25", lambda: (not b.off() and len(b.alive()) == 1 and b.leftovers() == [] and "INTERRUPTED" in b.result(),
                              "off %s, alive %s, leftovers %s, rc %s" % (b.off(), b.alive(), b.leftovers(), rc)),
             "[B1 / expB] interrupted while the switch is on: the switch is gone, an agent runs (the guard restarted whichever "
             "file is in place), nothing left over, the result file says INTERRUPTED", prev="red")
        rc, v = b.run()
        R.ck("I.26", lambda: (rc == 0 and (v.startswith("ALREADY INSTALLED - ") or v.startswith("INSTALLED - ")) and not b.off()
                              and b.alive() == ["S499.1"] and md5f(b.live) == b.TO, "rc %s %s | off %s alive %s" % (rc, v[:80], b.off(), b.alive())),
             "[B1 / expB] the next double-click finishes the job: S499.1 running, the switch gone", prev="red")
        # ---- a switch an interrupted run of THIS installer left (the window was closed: no finally ran)
        b = mk("leftover")
        boxes.append(b)
        os.makedirs(os.path.join(b.dest, "_off"))
        open(os.path.join(b.dest, "_off", "AGENT_OFF.txt"), "w").write("written by install_s499.py 2026-10-08 09:00:00 -- x\r\n")
        b.wait(lambda: "AGENT_OFF.txt is present -- agent stopped" in b.glog() and b.alive() == [], 10)
        _time.sleep(3.2)
        rc, v = b.run()
        R.ck("I.27", lambda: (happy(b, rc, v) and "an earlier run of this installer was interrupted" in b.out, "rc %s %s" % (rc, v[:90])),
             "[B1] a switch an earlier run of THIS installer left is recognised by its first line, taken away, the agent waited "
             "for -- and the install then goes through", prev="red")
        # ---- ALREADY INSTALLED is said only when it is true
        b = mk("stale", to_mode="mute", live_is_to=True)
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.29", lambda: (rc == 1 and v.startswith("INSTALLED BUT NOT RUNNING RIGHT") and "heartbeat" in v, v[:110]),
             "[B1] the new file in place but no fresh heartbeat naming S499.1: NOT 'ALREADY INSTALLED' -- it says what is wrong",
             prev="red")
        # ---- an export taken a moment ago
        b = mk("export")
        boxes.append(b)
        w_ = World.__new__(World)
        w_.clock = Clock()
        fresh = w_.put(os.path.join(b.watched, "user1", "report", "REPORT_1.XLS"), 2000, 30)
        rc, v = b.run()
        ok1 = (rc == 1 and "an export was just taken" in v and md5f(b.live) == b.FROM and "AGENT_OFF" not in b.glog().split("agent started")[-1])
        os.remove(fresh)
        cap = w_.put(os.path.join(b.dest, "_captured", "20261008-1__x.XLS"), 2000, 100)
        rc2, v2 = b.run()
        ok2 = rc2 == 1 and "an export was just taken" in v2 and md5f(b.live) == b.FROM
        os.utime(cap, (_time.time() - 900, _time.time() - 900))
        rc3, v3 = b.run()
        R.ck("I.30", lambda: (ok1 and ok2 and happy(b, rc3, v3), "%s / %s / %s" % (v[:60], v2[:60], v3[:60])),
             "[S1] an export in Marg's folder 30 s ago, then a capture 100 s ago: STOP each time, nothing changed -- 'wait five "
             "minutes'; once quiet, it installs", prev="red")
        # ---- M4: another account's guard, standing by, answers the switch first
        b = mk("standby", to_mode="mute", holder_poll="6.0", standby=True)
        boxes.append(b)
        rc, v = b.run()
        R.ck("I.33", lambda: (put_back_ok(b, rc, v), "rc %s %s | alive %s" % (rc, v[:90], b.alive())),
             "[M4] a second account's guard standing by says 'not starting' at once; the put-back still waits for the guard that "
             "RUNS the agent -- and the old agent runs again", prev="red")
        # ---- M5: a lock that cannot be written is said as itself
        b = mk("perm")
        boxes.append(b)

        class _os(object):
            def __getattr__(self, n):
                return getattr(os, n)

            def open(self, path, *x, **k):
                if str(path).endswith("S499_INSTALL.lock"):
                    raise PermissionError(13, "Access is denied", path)
                return os.open(path, *x, **k)
        b.m.os = _os()
        rc, v = b.run()
        R.ck("I.34", lambda: (rc == 1 and "cannot write" in v and "another run" not in v and md5f(b.live) == b.FROM, v[:100]),
             "[M5] a lock that cannot be written for want of permission is said as that, not as 'another run'", prev="red")
        # ---- delta expK: the WINDOW CLOSED while the switch is on -- the process killed, no finally runs
        b = mk("killed")
        boxes.append(b)
        sw = os.path.join(b.dest, "_off", "AGENT_OFF.txt")
        pid = os.fork()
        if pid == 0:                                            # the installer's process, as the window shows it
            try:
                sys.stdout = open(os.devnull, "w")
                b.m.main()
            finally:
                os._exit(0)
        t_k = _time.time()
        while not os.path.exists(sw) and _time.time() - t_k < 60:
            _time.sleep(0.02)
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        left = (os.path.exists(sw), os.path.exists(os.path.join(b.dest, "S499_INSTALL.lock")))
        rc, v = b.run()
        R.ck("I.35", lambda: (left == (True, True) and rc == 0 and (v.startswith("ALREADY INSTALLED - ") or v.startswith("INSTALLED - "))
                              and not b.off() and b.alive() == ["S499.1"] and not os.path.exists(os.path.join(b.dest, "S499_INSTALL.lock")),
                              "left %s | rc %s %s | off %s alive %s" % (left, rc, v[:90], b.off(), b.alive())),
             "[delta expK] the window closed while the switch is on (killed: switch AND lock left): the very next double-click "
             "sees the lock's run is gone, takes the switch away and finishes -- no 20-minute wait with the agent off",
             prev="red", prev2="red")
        # ---- the console close handler's own work
        b = mk("handler", start_guard=False)
        boxes.append(b)

        def handler():
            os.makedirs(os.path.join(b.dest, "_off"), exist_ok=True)
            hsw = os.path.join(b.dest, "_off", "AGENT_OFF.txt")
            open(hsw, "w").write("written by install_s499.py 2026-10-08 09:00:00 -- x\r\n")
            r1 = b.m._close_cleanup(2) is False and not os.path.exists(hsw)
            open(hsw, "w").write("switched off by a person\n")
            b.m._close_cleanup(2)
            r2 = os.path.exists(hsw)
            os.remove(hsw)
            return (r1 and r2 and b.m.install_close_handler() in (True, False), "ours removed %s, person's kept %s" % (r1, r2))
        R.ck("I.36", handler, "[delta] the close / Ctrl handler removes a switch THIS installer wrote, never a person's, and lets the "
             "window close; registering it where it cannot be (here) is harmless", prev="red", prev2="red")
        # ---- (a) the switch is written whole: a write that fails half-way leaves no switch at all
        b = mk("halfswitch")
        boxes.append(b)
        import builtins

        def half_open(path, mode="r", *x, **k):
            if str(path).endswith(("AGENT_OFF.txt", "AGENT_OFF.txt.tmp")) and "w" in mode:
                builtins.open(path, "w").close()               # created, nothing in it -- then the disk fails
                raise OSError(28, "No space left on device")
            return builtins.open(path, mode, *x, **k)
        b.m.open = half_open
        rc, v = b.run()
        del b.m.open
        _time.sleep(2.5)
        R.ck("I.37", lambda: (not b.off() and not os.path.exists(os.path.join(b.dest, "_off", "AGENT_OFF.txt.tmp"))
                              and md5f(b.live) == b.FROM and b.alive() == ["S205.1"] and rc == 1,
                              "off %s | alive %s | %s" % (b.off(), b.alive(), v[:80])),
             "[delta a] a switch write that fails half-way leaves NO switch (an empty one would keep the agent off, unrecognised) "
             "-- nothing changed, the old agent runs", prev="same", prev2="red")
        # ---- (b) no answer from the guard: the old file is back BEFORE the switch goes
        b = mk("order")
        boxes.append(b)
        os.killpg(b.guard.pid, signal.SIGKILL)
        b.guard.wait()
        seen = []
        real_on = b.m.switch_on

        def on(*x):
            seen.append(md5f(b.live))
            return real_on(*x)
        b.m.switch_on = on
        rc, v = b.run()
        R.ck("I.38", lambda: (rc == 1 and seen and seen[0] == b.FROM and md5f(b.live) == b.FROM and not b.off(), "live at switch-off: %s"
                              % ["FROM" if x == b.FROM else "TO" if x == b.TO else x for x in seen]),
             "[delta b] the guard gives no answer: the old file is put back INSIDE the finally, before the switch goes -- a late "
             "stop can only restart the old file", prev="same", prev2="red")
    finally:
        for b in boxes:
            b.close()


# ================================================================== the verdict
def load_reader(path, name, work):
    d = os.path.join(work, "_mods", "reader_" + name)
    os.makedirs(d)
    p = os.path.join(d, name + ".py")
    shutil.copyfile(path, p)
    spec = importlib.util.spec_from_file_location("reader_" + name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="medical_agent.py S205.1 (70d5c4e3)")
    ap.add_argument("--readers", required=True, help="a folder holding copies of pipeline_status.py and verify_medical.py")
    ap.add_argument("--guard", required=True, help="a copy of agent_guard.py (S387)")
    ap.add_argument("--work", required=True)
    ap.add_argument("--kit", default=HERE)
    ap.add_argument("--prev", default="", help="the first reviewed S499 build's folder (kit_prev): its medical_agent.py and install_s499.py")
    ap.add_argument("--prev2", default="", help="the second reviewed S499 build's folder (kit_prev2)")
    ap.add_argument("--only", default="", help="NEW, OLD, Q, K or I -- to run a part")
    ap.add_argument("--all-rows", action="store_true", help="print every row of the negative control, not only its summary")
    a = ap.parse_args()
    work = os.path.abspath(a.work)
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    kit = os.path.abspath(a.kit)
    new_path, old_path, guard = os.path.join(kit, "medical_agent.py"), os.path.abspath(a.old), os.path.abspath(a.guard)
    prev_path = os.path.join(os.path.abspath(a.prev), "medical_agent.py") if a.prev else ""
    prev_inst = os.path.join(os.path.abspath(a.prev), "install_s499.py") if a.prev else ""
    prev2_path = os.path.join(os.path.abspath(a.prev2), "medical_agent.py") if a.prev2 else ""
    prev2_inst = os.path.join(os.path.abspath(a.prev2), "install_s499.py") if a.prev2 else ""
    ps, ps_p = load_reader(os.path.join(os.path.abspath(a.readers), "pipeline_status.py"), "pipeline_status", work)
    vm, vm_p = load_reader(os.path.join(os.path.abspath(a.readers), "verify_medical.py"), "verify_medical", work)
    print("walk_s499 -- python %s -- %s" % (sys.version.split()[0], dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("  new    %s  %s" % (md5f(new_path), new_path))
    print("  old    %s  %s" % (md5f(old_path), old_path))
    if prev_path:
        print("  prev   %s  %s   installer %s" % (md5f(prev_path), prev_path, md5f(prev_inst)))
    if prev2_path:
        print("  prev2  %s  %s   installer %s" % (md5f(prev2_path), prev2_path, md5f(prev2_inst)))
    print("  reader %s  pipeline_status.py     reader %s  verify_medical.py     guard %s" % (md5f(ps_p)[:8], md5f(vm_p)[:8], md5f(guard)[:8]))
    for nm, p in (("pipeline_status.py", ps_p), ("verify_medical.py", vm_p)):
        r = subprocess.run([sys.executable, "-B", p, "--selftest"], capture_output=True, text=True, cwd=os.path.dirname(p))
        print("  %s --selftest (its own, untouched): exit %d -- %s" % (nm, r.returncode, ((r.stdout + r.stderr).strip().splitlines() or ["?"])[-1][:90]))
    fails = 0
    cwd0 = os.getcwd()

    def show(title, rows, mode):
        """mode NEW: every check must be green. OLD / PREV: every check must do what it declares that file does."""
        nonlocal fails
        print("\n== %s" % title)
        n_ok = n_red = n_same = 0
        for cid, ok, what, exp, det in rows:
            if mode == "NEW":
                good = ok
                mark = "ok " if ok else "RED"
            else:
                good = (ok is False) if exp == "red" else (ok is True)
                mark = ("red as it must be" if exp == "red" else "same             ") if good else \
                       ("NOT RED -- the check cannot fail" if exp == "red" else "RED -- this file was to pass it")
                n_red += (exp == "red" and good)
                n_same += (exp == "same" and good)
            n_ok += good
            if not good:
                fails += 1
            if mode == "NEW" or not good or a.all_rows:
                print("  [%s] %s  %s%s" % (mark, cid, what, ("\n         -> " + det[:150]) if (det and (not good or mode != "NEW")) else ""))
        if mode == "NEW":
            print("  %d of %d green" % (n_ok, len(rows)))
        else:
            print("  %d checks: %d went RED as they must, %d stayed the SAME as they must, %d did neither"
                  % (len(rows), n_red, n_same, len(rows) - n_ok))
            reds = [(cid, what) for cid, ok, what, exp, det in rows if exp == "red" and not ok]
            print("  what it fails, by name (first %d of %d):" % (min(14, len(reds)), len(reds)))
            for cid, what in reds[:14]:
                print("    %s  %s" % (cid, what[:118]))
        return n_ok, len(rows)

    HN = HO = None
    if a.only in ("", "NEW"):
        HN = run_suite(new_path, "NEW", work, (ps, vm))
        show("NEW  medical_agent.py S499.1 -- every check must be green", HN.R.rows, "NEW")
    if a.only in ("", "OLD"):
        HO = run_suite(old_path, "OLD", work, (ps, vm))
        show("OLD  medical_agent.py S205.1 (70d5c4e3) -- negative control: the SAME checks; each goes red, or stays the same, "
             "as declared", HO.R.rows, "OLD")
    if a.only in ("", "PREV") and prev_path:
        HP = run_suite(prev_path, "PREV", work, (ps, vm))
        show("PREV medical_agent.py, the previous S499 build (%s) -- negative control for the review's faults" % md5f(prev_path)[:8],
             HP.R.rows, "PREV")
    if a.only in ("", "PREV2") and prev2_path:
        HP2 = run_suite(prev2_path, "PREV2", work, (ps, vm))
        show("PREV2 medical_agent.py, the second reviewed build (%s) -- negative control for the delta review" % md5f(prev2_path)[:8],
             HP2.R.rows, "PREV")
    if a.only == "" and HN and HO:
        U = Res("UPG")
        HNu, HOu = Harness(new_path, "NEW", work, (ps, vm)), Harness(old_path, "OLD", work, (ps, vm))
        HNu.R = HOu.R = U
        HNu.n, HOu.n = 900, 900
        scen_L_upgrade(HOu, HNu)
        show("UPG  S205.1's hourly loop reproduced, then S499.1 on the same Drive folder", U.rows, "NEW")
    if a.only in ("", "Q"):
        Q = Res("Q")
        scen_Q(Q, old_path, new_path)
        show("Q    function by function, S205.1 against S499.1", Q.rows, "NEW")
    if a.only in ("", "K"):
        K = Res("K")
        scen_K(K, kit, old_path, work)
        show("K    the kit", K.rows, "NEW")
    if a.only in ("", "I"):
        I = Res("I")
        scen_I(I, work, guard, os.path.join(kit, "install_s499.py"), "new")
        scen_I_real(I, work, guard, os.path.join(kit, "install_s499.py"), old_path, new_path)
        show("I    install_s499.py against the real guard (agent_guard.py S387) and stand-in agents", I.rows, "NEW")
    if a.only in ("", "IPREV") and prev_inst:
        IP = Res("PREV")
        scen_I(IP, work, guard, prev_inst, "prev")
        show("IPREV the previous installer (%s) on the same checks -- negative control for the review's faults" % md5f(prev_inst)[:8],
             IP.rows, "PREV")
    if a.only in ("", "IPREV2") and prev2_inst:
        IP2 = Res("PREV2")
        scen_I(IP2, work, guard, prev2_inst, "prev2")
        show("IPREV2 the second reviewed installer (%s) -- negative control for the delta review" % md5f(prev2_inst)[:8],
             IP2.rows, "PREV")
    os.chdir(cwd0)
    print("")
    if fails:
        print("WALK S499: RED -- %d check(s) did not do what they must" % fails)
        return 1
    print("WALK S499: GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
