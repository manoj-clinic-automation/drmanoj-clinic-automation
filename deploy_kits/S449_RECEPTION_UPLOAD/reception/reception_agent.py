#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reception_agent.py  --  S448.  Runs ON THE RECEPTION PC (Windows user `dell`).

Why it exists. On 01-Oct-2026 Google Drive for desktop stopped starting on
this PC and nothing said so: the Docterz exports and the X-rays simply
stopped arriving, and it took the owner sitting at the desk to find out. A
Claude session linked to this PC can read and write files here but has no
shell, so even a one-line repair needed him at the keyboard.

Five jobs:

  1. REPORT IN. Every five minutes a heartbeat is written to this folder and
     to the clinic Google Drive (Clinic Data Archive\\FromReception). A stale
     heartbeat is itself the alarm -- it is what Drive being down looks like.
     THE HEARTBEAT CARRIES COUNTS AND DATES ONLY, NEVER A FILE NAME: on this
     PC the file names are patients.

  2. WATCH. Google Drive running and My Drive present; the two Docterz
     reports landing in Clinic Records\\Docterz exports; Chrome's download
     folder still pointing there; the X-ray inbox emptying; disk space; the
     Claude desktop app (the owner's only way in from his own PC).

  3. KEEP THE DOORS OPEN. Google Drive and the Claude app are started again
     when they are found not running.

  4. RUN JOBS. A script dropped into  jobs\\in  is run and its output written
     to  jobs\\out . Writing into that folder already needs the owner's
     Claude account and his folder grant on this PC, so local jobs need no
     further proof. A job arriving through the clinic DRIVE is different --
     anyone holding that Google account could put one there -- so a Drive job
     runs ONLY with an Ed25519 signature from a key listed in
     authorized_keys.txt. That file is empty at install: the Drive door is
     shut until a key is enrolled from a linked session.

  5. REPORT STRAIGHT TO THE SERVER (S449, the owner, 02-Oct-2026: "direct
     upload from the reception PC to server"). The same heartbeat, and the
     two Docterz reports themselves, are posted over HTTPS to the clinic
     server, so nothing depends on Google Drive alone. Every request is
     signed with a key made ON THIS PC (upload_key.txt) that never leaves
     it; the server holds only the public half. Only a file that is one of
     the two Docterz reports -- by its name AND its first line -- is ever
     read or sent, and only to the clinic's own server.

Modelled on medical_agent.py (S205.1). Stdlib only. It writes only inside its
own folder and the Drive FromReception / ToReception folders. Apart from the
two Docterz reports of job 5 it reads folder listings, never a patient file.

The agent may be replaced while the PC runs: put the new file beside this one
as  reception_agent.py.new . It is compiled first, the running copy is kept
as .prev, and agent_guard.py puts .prev back if the new one dies.
"""

import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import string
import subprocess
import sys
import time

AGENT_VERSION = "S449.1"

ROOT = os.path.dirname(os.path.abspath(__file__))


def P(*parts):
    return os.path.join(ROOT, *parts)


AGENT_FILE = P("reception_agent.py")
NEW_FILE = P("reception_agent.py.new")
PREV_FILE = P("reception_agent.py.prev")
UPDATE_MARKER = P("update_pending.json")
RESTART_FLAG = P("RESTART.flag")
CONFIG_FILE = P("config.json")
AGENT_LOG = P("agent.log")
CRASH_FILE = P("agent_crash.txt")
LOCAL_BEAT_TXT = P("heartbeat.txt")
LOCAL_BEAT_JSON = P("heartbeat.json")
KEYS_FILE = P("authorized_keys.txt")
SEEN_FILE = P("drive_jobs_seen.json")
UPLOAD_KEY_FILE = P("upload_key.txt")       # this PC's own signing secret (S449)
UPLOAD_SENT_FILE = P("upload_sent.json")    # md5 of every report already sent
OFF_ALL = P("_off", "ALL_OFF.txt")
OFF_JOBS = P("_off", "JOBS_OFF.txt")
JOBS_IN = P("jobs", "in")
JOBS_RUNNING = P("jobs", "running")
JOBS_OUT = P("jobs", "out")
JOBS_DONE = P("jobs", "done")
JOBS_WORK = P("jobs", "work")

EXIT_RESTART = 42          # agent_guard.py restarts at once on this code

DEFAULTS = {
    "tick_seconds": 5,
    "beat_seconds": 300,
    "drive_jobs_seconds": 60,
    "job_timeout_default": 600,
    "job_timeout_max": 7200,
    "job_output_max_bytes": 4 * 1024 * 1024,
    "keep_done": 200,
    "repair_drive": True,
    "keep_claude_running": True,
    "repair_chrome_download": True,
    "repair_grace_seconds": 180,
    "repair_min_gap_seconds": 1800,
    "claude_start_command": None,
    "disk_warn_gb": 10,
    "xray_stuck_hours": 24,
    "docterz_rel": ["Clinic Records", "Docterz exports"],
    "xray_inbox_rel": ["Clinic Records", "X-ray inbox"],
    "xray_check_rel": ["Clinic Records", "X-ray check"],
    "archive_rel": ["Clinic Data Archive"],
    "direct_upload": True,
    "server_url": "https://followup.dr-manoj.in",
    "upload_days": 4,
    "upload_max_files": 2,
}

JOB_EXTS = (".ps1", ".cmd", ".bat", ".py")
JOB_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")
DRIVE_JOB_PREFIX = "drive__"
SIG_CONTEXT = b"clinic-reception-job-v1\n"
DRIVE_JOB_MAX_BYTES = 1024 * 1024
# A Drive job's name begins with the time it was signed (the PC's own clock,
# IST): 20261002T143000_name.ps1. The name is part of what is signed, so the
# stamp cannot be changed afterwards -- and a job older than this is refused
# even if the list of names already used were ever lost.
DRIVE_JOB_STAMP_RE = re.compile(r"^(\d{8})T(\d{6})_")
DRIVE_JOB_MAX_AGE_HOURS = 48
DRIVE_JOB_MAX_AHEAD_HOURS = 2

IS_WIN = os.name == "nt"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def now():
    return dt.datetime.now()


def iso(ts=None):
    d = now() if ts is None else dt.datetime.fromtimestamp(ts)
    return d.isoformat(timespec="seconds")


def log(msg):
    """Log to the FILE first, then the console if there is one.

    Under pythonw.exe there is no console and sys.stdout is None (the lesson
    medical_agent.py v1 paid for). The file is the record.
    """
    line = "%s  %s\n" % (now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        if os.path.exists(AGENT_LOG) and os.path.getsize(AGENT_LOG) > 512 * 1024:
            with open(AGENT_LOG, "r", encoding="utf-8", errors="replace") as fh:
                tail = fh.readlines()[-2000:]
            with open(AGENT_LOG, "w", encoding="utf-8") as fh:
                fh.writelines(tail)
        with open(AGENT_LOG, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
    try:
        if sys.stdout is not None:
            sys.stdout.write(line)
            sys.stdout.flush()
    except Exception:                                          # noqa: BLE001
        pass


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
            got = json.load(fh)
        if isinstance(got, dict):
            for k, v in got.items():
                if k in DEFAULTS:
                    cfg[k] = v
    except (OSError, ValueError):
        pass
    for k in ("tick_seconds", "beat_seconds", "drive_jobs_seconds",
              "job_timeout_default", "job_timeout_max", "keep_done",
              "job_output_max_bytes", "repair_grace_seconds",
              "repair_min_gap_seconds", "disk_warn_gb", "xray_stuck_hours",
              "upload_days", "upload_max_files"):
        try:
            cfg[k] = max(1, int(float(cfg[k])))
        except (TypeError, ValueError):
            cfg[k] = DEFAULTS[k]
    # the guard stops an agent that is silent for 15 minutes: a slower
    # heartbeat than this would make it kill a healthy one
    cfg["beat_seconds"] = min(cfg["beat_seconds"], 600)
    cfg["tick_seconds"] = min(cfg["tick_seconds"], 60)
    for k in ("docterz_rel", "xray_inbox_rel", "xray_check_rel", "archive_rel"):
        if not (isinstance(cfg[k], list) and cfg[k]
                and all(isinstance(x, str) for x in cfg[k])):
            cfg[k] = DEFAULTS[k]
    # the direct upload goes to the clinic's own server and nowhere else
    url = str(cfg.get("server_url") or "").rstrip("/")
    if not (url.startswith("https://") or url.startswith("http://127.0.0.1:")):
        url = DEFAULTS["server_url"]
    cfg["server_url"] = url
    cfg["upload_max_files"] = min(cfg["upload_max_files"], 5)
    return cfg


def _md5(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as fh:
            for c in iter(lambda: fh.read(1 << 20), b""):
                h.update(c)
    except OSError:
        return None
    return h.hexdigest()


def _decode(raw):
    """Bytes from a Windows child process -> text, without ever raising."""
    if not raw:
        return ""
    for enc in ("utf-8", "oem", "mbcs"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("latin-1", errors="replace")


def run_quiet(cmd, timeout=30):
    """Run a short helper command with no console window: (rc, text)."""
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout, creationflags=NO_WINDOW)
        return p.returncode, _decode(p.stdout)
    except Exception as ex:                                    # noqa: BLE001
        return -1, "%s: %s" % (ex.__class__.__name__, ex)


def quiet_errors():
    """No 'there is no disk in the drive' box when a drive letter is probed."""
    if not IS_WIN:
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x8000)
    except Exception:                                          # noqa: BLE001
        pass


def uptime_hours():
    if not IS_WIN:
        return None
    try:
        import ctypes
        fn = ctypes.windll.kernel32.GetTickCount64
        fn.restype = ctypes.c_ulonglong
        return round(fn() / 3600000.0, 1)
    except Exception:                                          # noqa: BLE001
        return None


# --------------------------------------------------------------------------
# Ed25519 (RFC 8032), pure Python. Verify is what the agent needs; keygen and
# sign are here so a session can sign a Drive job with this same file and no
# third-party package. Proven offline against the RFC's own test vectors.
# --------------------------------------------------------------------------
_EP = 2 ** 255 - 19
_EL = 2 ** 252 + 27742317777372353535851937790883648493


def _einv(x):
    return pow(x, _EP - 2, _EP)


_ED = -121665 * _einv(121666) % _EP
_EI = pow(2, (_EP - 1) // 4, _EP)


def _eadd(a, b):
    A = (a[1] - a[0]) * (b[1] - b[0]) % _EP
    B = (a[1] + a[0]) * (b[1] + b[0]) % _EP
    C = 2 * a[3] * b[3] * _ED % _EP
    D = 2 * a[2] * b[2] % _EP
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _EP, G * H % _EP, F * G % _EP, E * H % _EP)


def _emul(s, pt):
    q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            q = _eadd(q, pt)
        pt = _eadd(pt, pt)
        s >>= 1
    return q


def _eeq(a, b):
    if (a[0] * b[2] - b[0] * a[2]) % _EP:
        return False
    if (a[1] * b[2] - b[1] * a[2]) % _EP:
        return False
    return True


def _erecover_x(y, sign):
    if y >= _EP:
        return None
    x2 = (y * y - 1) * _einv(_ED * y * y + 1) % _EP
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_EP + 3) // 8, _EP)
    if (x * x - x2) % _EP:
        x = x * _EI % _EP
    if (x * x - x2) % _EP:
        return None
    if (x & 1) != sign:
        x = _EP - x
    return x


_EGY = 4 * _einv(5) % _EP
_EGX = _erecover_x(_EGY, 0)
_EG = (_EGX, _EGY, 1, _EGX * _EGY % _EP)


def _ecompress(pt):
    zi = _einv(pt[2])
    x, y = pt[0] * zi % _EP, pt[1] * zi % _EP
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _edecompress(s):
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _erecover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % _EP)


def _esecret_expand(secret):
    if len(secret) != 32:
        raise ValueError("an Ed25519 secret is 32 bytes")
    h = hashlib.sha512(secret).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= (1 << 254)
    return a, h[32:]


def ed_public(secret):
    a, _ = _esecret_expand(secret)
    return _ecompress(_emul(a, _EG))


def ed_sign(secret, msg):
    a, prefix = _esecret_expand(secret)
    pub = _ecompress(_emul(a, _EG))
    r = int.from_bytes(hashlib.sha512(prefix + msg).digest(), "little") % _EL
    rs = _ecompress(_emul(r, _EG))
    h = int.from_bytes(hashlib.sha512(rs + pub + msg).digest(), "little") % _EL
    s = (r + h * a) % _EL
    return rs + int.to_bytes(s, 32, "little")


def ed_verify(public, msg, sig):
    try:
        if len(public) != 32 or len(sig) != 64:
            return False
        A = _edecompress(public)
        if not A:
            return False
        rs = sig[:32]
        R = _edecompress(rs)
        if not R:
            return False
        s = int.from_bytes(sig[32:], "little")
        if s >= _EL:
            return False
        h = int.from_bytes(hashlib.sha512(rs + public + msg).digest(),
                           "little") % _EL
        return _eeq(_emul(s, _EG), _eadd(R, _emul(h, A)))
    except Exception:                                          # noqa: BLE001
        return False


def job_message(name, content):
    """Exactly what is signed: a fixed context, the job's name, its bytes."""
    return SIG_CONTEXT + name.encode("utf-8") + b"\n" + content


def authorized_keys():
    """[(32 raw bytes, label)] from authorized_keys.txt; [] shuts the door."""
    out = []
    try:
        with open(KEYS_FILE, "r", encoding="utf-8-sig",
                  errors="replace") as fh:
            for line in fh:
                # a file saved by Notepad or PowerShell as UTF-16 still reads
                line = line.replace("\x00", "").replace("\ufffd", "").strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                hx = parts[0].lower()
                if len(hx) == 64 and re.fullmatch(r"[0-9a-f]{64}", hx):
                    out.append((bytes.fromhex(hx),
                                parts[1].strip() if len(parts) > 1 else ""))
    except OSError:
        pass
    return out


# --------------------------------------------------------------------------
# S449 -- straight to the clinic server, signed with this PC's own key
# --------------------------------------------------------------------------
UPLOAD_CONTEXT = b"clinic-reception-upload-v1\n"
UPLOAD_MAX_BYTES = 5 * 1024 * 1024
UPLOAD_NAME_BAD = re.compile(r"[^A-Za-z0-9 ._()\-]")
REPORT_MARKS = {"consultation": (b"Consultation Date", b"Mode Of Payment"),
                "followup": (b"Appointment ID", b"Mobile No")}


def upload_message(kind, ts, name, mtime, body):
    """Exactly what is signed (the server's reception_door.py builds the same
    bytes): a fixed context, the kind, this PC's clock, the file's name and
    time, and the SHA-256 of the body."""
    return (UPLOAD_CONTEXT + kind.encode("ascii") + b"\n"
            + str(ts).encode("ascii") + b"\n" + name.encode("utf-8") + b"\n"
            + str(mtime).encode("ascii") + b"\n"
            + hashlib.sha256(body).hexdigest().encode("ascii"))


def upload_secret(make=True):
    """This PC's signing secret, made here the first time and never sent
    anywhere. None if it cannot be read or made."""
    try:
        with open(UPLOAD_KEY_FILE, "r", encoding="ascii", errors="replace") as fh:
            hx = fh.read().strip()
        if re.fullmatch(r"[0-9a-fA-F]{64}", hx):
            return bytes.fromhex(hx)
    except OSError:
        pass
    if not make or os.path.exists(UPLOAD_KEY_FILE):
        return None                  # a damaged key is never silently replaced
    try:
        secret = os.urandom(32)
        with open(UPLOAD_KEY_FILE, "w", encoding="ascii") as fh:
            fh.write(secret.hex() + "\n")
        if IS_WIN:                   # this user, SYSTEM and Administrators only
            run_quiet(["icacls", UPLOAD_KEY_FILE, "/inheritance:r", "/grant:r",
                       "%s:F" % os.environ.get("USERNAME", ""),
                       "*S-1-5-18:F", "*S-1-5-32-544:F"], timeout=20)
        log("direct upload: a new signing key was made on this PC")
        return secret
    except OSError as ex:
        log("direct upload: could not make the signing key: %s" % ex)
        return None


def upload_public():
    secret = upload_secret()
    return ed_public(secret).hex() if secret else None


def _post_signed(cfg, path, kind, body, name="", mtime="", timeout=15):
    """(http code or None, answer dict or None, short error or None)."""
    secret = upload_secret()
    if not secret:
        return None, None, "this PC has no signing key (upload_key.txt)"
    try:
        import urllib.error
        import urllib.request
    except Exception as ex:                                    # noqa: BLE001
        return None, None, "no HTTPS support in this Python: %s" % ex

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):                   # noqa: ARG002
            return None              # a login page is not an answer

    ts = int(time.time())
    sig = ed_sign(secret, upload_message(kind, ts, name, mtime, body))
    req = urllib.request.Request(
        cfg["server_url"] + path, data=body, method="POST",
        headers={"Content-Type": "application/octet-stream",
                 "User-Agent": "ClinicAgent/%s" % AGENT_VERSION,
                 "X-Rx-Time": str(ts), "X-Rx-Sig": sig.hex(),
                 "X-Rx-Name": name, "X-Rx-Mtime": str(mtime)})
    code, raw = None, b""
    try:
        with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as r:
            code, raw = r.status, r.read(65536)
    except urllib.error.HTTPError as ex:
        code = ex.code
        try:
            raw = ex.read(65536)
        except Exception:                                      # noqa: BLE001
            raw = b""
    except Exception as ex:                                    # noqa: BLE001
        return None, None, ("%s: %s" % (ex.__class__.__name__, ex))[:160]
    try:
        ans = json.loads(raw.decode("utf-8", errors="replace"))
        if not isinstance(ans, dict):
            ans = None
    except ValueError:
        ans = None
    if code == 200 and ans and ans.get("ok"):
        return code, ans, None
    return code, ans, ("the server answered %s%s" % (
        code, (" -- %s" % str(ans.get("message") or ans.get("status"))[:110])
        if ans else " (its direct-upload door is not there yet)"))[:160]


def _sent_read():
    try:
        with open(UPLOAD_SENT_FILE, "r", encoding="utf-8") as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def _sent_write(sent):
    try:
        keep = dict(sorted(sent.items(), key=lambda kv: kv[1].get("at", ""))[-500:])
        _write(UPLOAD_SENT_FILE, json.dumps(keep, indent=1))
        return True
    except OSError as ex:
        log("direct upload: could not record what was sent: %s" % ex)
        return False


def report_candidates(folders, days, cache):
    """[(path, kind, mtime, md5)] -- files that are one of the two Docterz
    reports by NAME and by FIRST LINE, changed in the last `days` days and no
    longer being written. Nothing else in a folder is ever opened."""
    out, t = [], time.time()
    for folder in folders:
        try:
            names = os.listdir(folder) if folder else []
        except OSError:
            continue
        for n in names:
            kind = _report_kind(n.lower())
            if not kind:
                continue
            p = os.path.join(folder, n)
            try:
                size, m = os.path.getsize(p), os.path.getmtime(p)
            except OSError:
                continue
            if not (0 < size <= UPLOAD_MAX_BYTES) or t - m > days * 86400 or t - m < 20:
                continue
            key = (p, size, m)
            if key not in cache:
                try:
                    with open(p, "rb") as fh:
                        raw = fh.read()
                except OSError:
                    continue         # Drive still bringing it down; next pass
                head = raw[:4096]
                cache[key] = hashlib.md5(raw).hexdigest() if all(
                    mark in head for mark in REPORT_MARKS[kind]) else None
            if cache[key]:
                out.append((p, kind, m, cache[key]))
    out.sort(key=lambda r: r[2])
    return out


def direct_pass(st, cfg, beat):
    """After each heartbeat: the same heartbeat to the server, then any report
    it has not had. Never raises; what happened goes into the next heartbeat."""
    up = st["upload"]
    if not cfg.get("direct_upload"):
        return
    code, ans, err = _post_signed(cfg, "/finance/api/reception/heartbeat",
                                  "heartbeat", json.dumps(beat).encode("utf-8"))
    if err:
        up["fail_streak"] += 1
        if up["last_error"] != err:
            log("direct upload: heartbeat not accepted -- %s" % err)
        up["last_error"] = err
        return                       # the server is not there: no report is tried
    if up["fail_streak"] or up["ok_at"] is None:
        log("direct upload: the server accepted the heartbeat")
    up["ok_at"], up["fail_streak"], up["last_error"] = iso(), 0, None
    if beat.get("switched_off"):
        return
    downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    folders = [drive_sub(beat.get("my_drive"), cfg["docterz_rel"]), downloads]
    sent = _sent_read()
    done = 0
    for path, kind, m, md5 in report_candidates(folders, cfg["upload_days"],
                                                st["upload_cache"]):
        if md5 in sent or done >= cfg["upload_max_files"]:
            continue
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        if hashlib.md5(raw).hexdigest() != md5:
            continue                 # changed since it was looked at; next pass
        name = UPLOAD_NAME_BAD.sub("_", os.path.basename(path))[:120]
        code, ans, err = _post_signed(cfg, "/finance/api/reception/report",
                                      "report", raw, name, int(m), timeout=30)
        done += 1
        if err and code != 400:
            up["last_error"] = err
            log("direct upload: a %s report was not accepted -- %s" % (kind, err))
            break
        verdict = (ans or {}).get("status") or "REFUSED"
        sent[md5] = {"at": iso(), "kind": kind, "status": verdict,
                     "day": (ans or {}).get("day") or ""}
        if not _sent_write(sent):
            break
        if verdict in ("TAKEN", "ALREADY"):
            up["reports_sent"] += 1
            up["last_report_at"] = iso()
        log("direct upload: %s report for %s -> %s" % (
            kind, (ans or {}).get("day") or "?", verdict))


# --------------------------------------------------------------------------
# where does the clinic Drive live today?  (searched fresh, never cached --
# the letter moves when Drive is switched between streaming and mirroring)
# --------------------------------------------------------------------------
def find_my_drive():
    roots = ["%s:\\My Drive" % c for c in string.ascii_uppercase]
    roots.append(os.path.join(os.environ.get("USERPROFILE", ""), "My Drive"))
    for r in roots:
        try:
            if os.path.isdir(os.path.join(r, "Clinic Records")) or \
               os.path.isdir(os.path.join(r, "Clinic Data Archive")):
                return r
        except OSError:
            continue
    return None


def drive_sub(my_drive, rel, make=False):
    if not my_drive:
        return None
    p = os.path.join(my_drive, *rel)
    try:
        if os.path.isdir(p):
            return p
        if make and os.path.isdir(os.path.dirname(p)):
            os.makedirs(p, exist_ok=True)
            return p
    except OSError:
        pass
    return None


def drive_out(my_drive, cfg):
    return drive_sub(my_drive, list(cfg["archive_rel"]) + ["FromReception"], True)


def drive_in(my_drive, cfg):
    return drive_sub(my_drive, list(cfg["archive_rel"]) + ["ToReception"], True)


# --------------------------------------------------------------------------
# what is running
# --------------------------------------------------------------------------
def process_names():
    """{image name, lower-cased: [pids]} from tasklist, or None if unknown."""
    rc, text = run_quiet(["tasklist", "/FO", "CSV", "/NH"], timeout=40)
    if rc != 0:
        return None
    out = {}
    try:
        for row in csv.reader(io.StringIO(text)):
            if len(row) >= 2 and row[1].strip().isdigit():
                out.setdefault(row[0].strip().lower(), []).append(int(row[1]))
    except csv.Error:
        return None
    return out or None


def kill_tree(pid):
    run_quiet(["taskkill", "/PID", str(pid), "/T", "/F"], timeout=20)


# --------------------------------------------------------------------------
# the watches -- COUNTS AND DATES ONLY
# --------------------------------------------------------------------------
def _files(folder):
    """[(lower-cased name, mtime)] for the plain files in a folder."""
    out = []
    try:
        names = os.listdir(folder)
    except OSError:
        return None
    for n in names:
        if n.lower() == "desktop.ini":
            continue
        p = os.path.join(folder, n)
        try:
            if os.path.isfile(p):
                out.append((n.lower(), os.path.getmtime(p)))
        except OSError:
            continue
    return out


def _report_kind(low):
    if low.endswith(".csv"):
        if low.startswith("consultation_report"):
            return "consultation"
        if low.startswith("followup_logs"):
            return "followup"
    return None


def scan_reports(folder):
    res = {"present": False}
    files = _files(folder) if folder else None
    if files is None:
        return res
    today = dt.date.today()
    res = {"present": True, "other_files": 0}
    for kind in ("consultation", "followup"):
        res[kind + "_today"] = 0
        res[kind + "_newest"] = None
        res[kind + "_days_old"] = None
    newest = {}
    for low, m in files:
        kind = _report_kind(low)
        if not kind:
            res["other_files"] += 1
            continue
        try:
            day = dt.date.fromtimestamp(m)
        except (OSError, OverflowError, ValueError):
            res["other_files"] += 1  # a file with no usable date
            continue
        if day == today:
            res[kind + "_today"] += 1
        if m > newest.get(kind, 0):
            newest[kind] = m
    for kind, m in newest.items():
        res[kind + "_newest"] = iso(m)
        res[kind + "_days_old"] = (today - dt.date.fromtimestamp(m)).days
    return res


def scan_xray(inbox, check):
    res = {"inbox_present": False}
    files = _files(inbox) if inbox else None
    if files is not None:
        res["inbox_present"] = True
        res["inbox_waiting"] = len(files)
        res["inbox_oldest_hours"] = None
        if files:
            oldest = min(m for _, m in files)
            res["inbox_oldest_hours"] = round((time.time() - oldest) / 3600.0, 1)
        res["last_filed"] = None
        filed = os.path.join(inbox, "_filed")
        try:
            subs = [os.path.getmtime(os.path.join(filed, d))
                    for d in os.listdir(filed)
                    if os.path.isdir(os.path.join(filed, d))]
            if subs:
                res["last_filed"] = iso(max(subs))
        except OSError:
            pass
    cf = _files(check) if check else None
    res["check_waiting"] = None if cf is None else len(cf)
    return res


def chrome_download_dirs():
    """{profile folder: download folder or None} read from Chrome's own
    Preferences files. None means Chrome's default, the Downloads folder."""
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome",
                        "User Data")
    out = {}
    try:
        profs = [d for d in os.listdir(base)
                 if d == "Default" or d.startswith("Profile ")]
    except OSError:
        return None
    for prof in sorted(profs):
        try:
            # read and CLOSE before parsing: Chrome replaces this file and
            # must never find it held open
            with open(os.path.join(base, prof, "Preferences"), "rb") as fh:
                raw = fh.read()
            pref = json.loads(raw.decode("utf-8", errors="replace"))
            dl = pref.get("download") or {}
            out[prof] = dl.get("default_directory")
        except (OSError, ValueError):
            continue
    return out


def chrome_set_download_dir(target, procs=None):
    """Point every Chrome profile's download folder at `target`.

    ONLY while Chrome is closed: Chrome owns its Preferences file while it
    runs and would write its own copy back. The file is read strictly, the
    one value is changed, the original is kept beside it once as
    Preferences.before_clinicagent, and the new file goes in by rename.
    Returns [(profile, what happened)]; nothing here ever raises.
    """
    out = []
    if not target or not os.path.isdir(target):
        return [("*", "the Docterz exports folder is not there -- nothing changed")]
    if procs is None:
        procs = process_names()
    if procs is None:
        return [("*", "the process list could not be read -- nothing changed")]
    if "chrome.exe" in procs:
        return [("*", "Chrome is running -- nothing changed")]
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome",
                        "User Data")
    try:
        profs = sorted(d for d in os.listdir(base)
                       if d == "Default" or d.startswith("Profile "))
    except OSError:
        return [("*", "Chrome has no profile on this PC yet -- nothing changed")]
    for prof in profs:
        path = os.path.join(base, prof, "Preferences")
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
            pref = json.loads(raw.decode("utf-8"))      # strict: never guess
            if not isinstance(pref, dict):
                raise ValueError("not a settings object")
            dl = pref.get("download")
            if not isinstance(dl, dict):
                dl = pref["download"] = {}
            if _same_path(dl.get("default_directory"), target) and \
               not dl.get("prompt_for_download"):
                out.append((prof, "already set"))
                continue
            dl["default_directory"] = target
            dl["prompt_for_download"] = False
            keep = path + ".before_clinicagent"
            if not os.path.exists(keep):
                with open(keep, "wb") as fh:
                    fh.write(raw)
            tmp = path + ".clinicagent.tmp"
            with open(tmp, "wb") as fh:
                fh.write(json.dumps(pref, separators=(",", ":"),
                                    ensure_ascii=False).encode("utf-8"))
            again = process_names()
            if again is None or "chrome.exe" in again:
                os.remove(tmp)
                out.append((prof, "Chrome started meanwhile -- nothing changed"))
                continue
            _replace(tmp, path)
            out.append((prof, "SET to %s" % target))
        except Exception as ex:                                # noqa: BLE001
            out.append((prof, "left alone (%s: %s)" % (ex.__class__.__name__, ex)))
    return out or [("*", "Chrome has no profile on this PC yet -- nothing changed")]


def _same_path(a, b):
    if not a or not b:
        return False

    def norm(p):
        return str(p).replace("/", "\\").rstrip("\\").lower()
    return norm(a) == norm(b)


def disk_free_gb(path):
    try:
        return round(shutil.disk_usage(path).free / (1024.0 ** 3), 1)
    except OSError:
        return None


def is_off(path):
    """The switch is the FILE. A file whose first word is ON counts as absent,
    because a linked session can write a file here but cannot delete one."""
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            word = re.sub(r"[^A-Za-z]", "", fh.read(64))
        return not word.upper().startswith("ON")
    except OSError:
        return False


def build_beat(st, cfg):
    procs = process_names()
    my_drive = find_my_drive()
    reports_dir = drive_sub(my_drive, cfg["docterz_rel"])
    inbox = drive_sub(my_drive, cfg["xray_inbox_rel"])
    check = drive_sub(my_drive, cfg["xray_check_rel"])
    chrome = chrome_download_dirs()
    downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    keys = authorized_keys()

    beat = {
        "agent_version": AGENT_VERSION,
        "written_at": iso(),
        "agent_started": st["started_at"],
        "computer": os.environ.get("COMPUTERNAME", ""),
        "user": os.environ.get("USERNAME", ""),
        "python": sys.version.split()[0],
        "pc_uptime_hours": uptime_hours(),
        "switched_off": is_off(OFF_ALL),
        "jobs_off": is_off(OFF_JOBS),
        "google_drive_running": None if procs is None
        else "googledrivefs.exe" in procs,
        "my_drive": my_drive,
        "claude_app_running": None if procs is None else "claude.exe" in procs,
        "chrome_running": None if procs is None else "chrome.exe" in procs,
        "docterz_exports": scan_reports(reports_dir),
        "downloads_folder": scan_reports(downloads),
        "chrome_download_dirs": chrome,
        "chrome_saves_to_exports": None,
        "xray": scan_xray(inbox, check),
        "disk_free_gb_c": disk_free_gb(os.path.splitdrive(ROOT)[0] + "\\"
                                       if IS_WIN else ROOT),
        "jobs": {
            "waiting": _count(JOBS_IN),
            "running": st["job"]["name"] if st.get("job") else None,
            "done_since_start": st["jobs_done"],
            "last": st.get("last_job"),
        },
        "drive_jobs": {
            "keys_enrolled": len(keys),
            "key_fingerprints": [hashlib.sha256(k).hexdigest()[:16]
                                 for k, _ in keys],
            "refused_since_start": st["drive_refused"],
        },
        "repairs": st["repairs"][-5:],
        "agent_md5": _md5(AGENT_FILE),
        "direct_upload": {
            "enabled": bool(cfg.get("direct_upload")),
            "server": cfg.get("server_url"),
            "public_key": upload_public(),
            "last_accepted": st["upload"]["ok_at"],
            "failed_in_a_row": st["upload"]["fail_streak"],
            "last_error": st["upload"]["last_error"],
            "reports_sent_since_start": st["upload"]["reports_sent"],
            "last_report_sent": st["upload"]["last_report_at"],
        },
    }
    if chrome is not None and reports_dir:
        beat["chrome_saves_to_exports"] = any(
            _same_path(v, reports_dir) for v in chrome.values())

    # one list of things a person should look at, in plain words
    att = []
    if beat["switched_off"]:
        att.append("the agent is SWITCHED OFF (_off\\ALL_OFF.txt): no jobs, no repairs")
    if beat["google_drive_running"] is False:
        att.append("Google Drive is NOT running")
    if not my_drive:
        att.append("My Drive is not visible on this PC")
    if beat["chrome_saves_to_exports"] is False:
        att.append("Chrome is NOT saving into Docterz exports")
    if beat["claude_app_running"] is False and cfg.get("keep_claude_running"):
        att.append("the Claude app is not running (no way in from the owner's PC)")
    free = beat["disk_free_gb_c"]
    if free is not None and free < float(cfg["disk_warn_gb"]):
        att.append("disk space is low: %.1f GB free" % free)
    old = beat["xray"].get("inbox_oldest_hours")
    if old is not None and old > float(cfg["xray_stuck_hours"]):
        att.append("%d X-ray file(s) waiting in the inbox, the oldest %.0f h"
                   % (beat["xray"].get("inbox_waiting", 0), old))
    du = beat["direct_upload"]
    if du["enabled"] and du["failed_in_a_row"] >= 3:
        att.append("the server has not accepted the direct upload %d times in a row (%s)"
                   % (du["failed_in_a_row"], du["last_error"]))
    beat["attention"] = att
    return beat, procs


def _count(folder):
    try:
        return len([n for n in os.listdir(folder)
                    if os.path.isfile(os.path.join(folder, n))])
    except OSError:
        return None


def _yn(v):
    return "unknown" if v is None else ("yes" if v else "NO")


def human(beat):
    r, d, x = beat["docterz_exports"], beat["downloads_folder"], beat["xray"]

    def rep(s):
        if not s.get("present"):
            return "folder not found"
        return ("consultation newest %s (%s today) | follow-up newest %s "
                "(%s today) | other files %s"
                % (s.get("consultation_newest") or "never",
                   s.get("consultation_today"),
                   s.get("followup_newest") or "never",
                   s.get("followup_today"), s.get("other_files")))
    lines = [
        "RECEPTION PC AGENT %s  --  written %s" % (beat["agent_version"],
                                                    beat["written_at"]),
        "",
        "ATTENTION: " + ("nothing" if not beat["attention"] else ""),
    ]
    for a in beat["attention"]:
        lines.append("   * " + a)
    lines += [
        "",
        "AGENT   : up since %s, PC up %s h, user %s on %s"
        % (beat["agent_started"], beat["pc_uptime_hours"], beat["user"],
           beat["computer"]),
        "SWITCH  : %s" % ("OFF" if beat["switched_off"] else
                          ("on, jobs off" if beat["jobs_off"] else "on")),
        "DRIVE   : running %s | My Drive at %s"
        % (_yn(beat["google_drive_running"]), beat["my_drive"] or "NOT FOUND"),
        "CLAUDE  : app running %s" % _yn(beat["claude_app_running"]),
        "CHROME  : saves into Docterz exports %s"
        % _yn(beat["chrome_saves_to_exports"]),
        "REPORTS : Docterz exports -- " + rep(r),
        "          Downloads       -- " + rep(d),
        "X-RAY   : inbox waiting %s (oldest %s h) | last filed %s | check %s"
        % (x.get("inbox_waiting"), x.get("inbox_oldest_hours"),
           x.get("last_filed"), x.get("check_waiting")),
        "DISK    : %s GB free" % beat["disk_free_gb_c"],
        "JOBS    : waiting %s | running %s | done since start %s"
        % (beat["jobs"]["waiting"], beat["jobs"]["running"],
           beat["jobs"]["done_since_start"]),
        "DRIVE JOBS: %s" % ("door SHUT (no key enrolled)"
                            if not beat["drive_jobs"]["keys_enrolled"] else
                            "%d key(s) enrolled, %d refused since start"
                            % (beat["drive_jobs"]["keys_enrolled"],
                               beat["drive_jobs"]["refused_since_start"])),
    ]
    du = beat.get("direct_upload") or {}
    lines.append("SERVER  : direct upload %s | last accepted %s | reports sent since start %s%s"
                 % ("on" if du.get("enabled") else "OFF",
                    du.get("last_accepted") or "not yet",
                    du.get("reports_sent_since_start"),
                    (" | %s" % du["last_error"]) if du.get("last_error") else ""))
    for rp in beat["repairs"]:
        lines.append("REPAIR  : " + rp)
    return "\r\n".join(lines) + "\r\n"


def _replace(src, dst, tries=6):
    """os.replace, patient with a virus scanner holding the file a moment."""
    for i in range(tries):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i == tries - 1:
                raise
            time.sleep(0.25)


def _write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(data)
    _replace(tmp, path)


def write_beat(beat, cfg):
    text, blob = human(beat), json.dumps(beat, indent=2)
    for path, data in ((LOCAL_BEAT_TXT, text), (LOCAL_BEAT_JSON, blob)):
        try:
            _write(path, data)
        except OSError as ex:
            log("could not write %s: %s" % (path, ex))
    out = drive_out(beat["my_drive"], cfg)
    if not out:
        log("clinic Drive FromReception folder not found -- heartbeat is LOCAL ONLY")
        return False
    ok = True
    for name, data in (("heartbeat.json", blob), ("heartbeat.txt", text)):
        try:
            # written in place, not by rename: Drive keeps one file with a
            # history, where a rename would leave a new file every 5 minutes
            with open(os.path.join(out, name), "w", encoding="utf-8",
                      newline="") as fh:
                fh.write(data)
        except OSError as ex:
            ok = False
            log("could not write %s to Drive: %s" % (name, ex))
    return ok


# --------------------------------------------------------------------------
# keeping the doors open
# --------------------------------------------------------------------------
def _spawn(cmd):
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)


def _cmd_exe():
    return os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                        "System32", "cmd.exe")


def _start_detached(target):
    """Open a program or shortcut the way a double-click does, through
    `start`, so it is NOT a child of this agent: stopping the agent (the
    guard and the installer stop the whole tree) must never take Google
    Drive or the Claude app down with it."""
    _spawn([_cmd_exe(), "/d", "/c", "start", "", target])


def start_google_drive():
    base = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                        "Google", "Drive File Stream")
    bat = os.path.join(base, "launch.bat")
    if os.path.isfile(bat):
        _start_detached(bat)
        return "launch.bat"
    try:
        vers = sorted((d for d in os.listdir(base)
                       if os.path.isfile(os.path.join(base, d,
                                                      "GoogleDriveFS.exe"))),
                      key=lambda v: [int(x) if x.isdigit() else 0
                                     for x in v.split(".")])
    except OSError:
        vers = []
    if vers:
        _start_detached(os.path.join(base, vers[-1], "GoogleDriveFS.exe"))
        return vers[-1]
    return None


def find_claude_shortcut():
    for env in ("APPDATA", "PROGRAMDATA"):
        base = os.path.join(os.environ.get(env, ""), "Microsoft", "Windows",
                            "Start Menu", "Programs")
        for r, _ds, fs in os.walk(base):
            for f in fs:
                if f.lower() == "claude.lnk":
                    return os.path.join(r, f)
    return None


def start_claude(cfg):
    cmd = cfg.get("claude_start_command")
    if isinstance(cmd, list) and cmd:
        _spawn([str(c) for c in cmd])
        return "configured command"
    lnk = find_claude_shortcut()
    if lnk:
        _start_detached(lnk)
        return "Start-menu shortcut"
    return None


def repairs(st, cfg, beat, procs):
    if procs is None or beat["switched_off"]:
        return
    t = time.time()
    if t - st["started_ts"] < float(cfg["repair_grace_seconds"]):
        return                       # at logon everything is still starting
    gap = float(cfg["repair_min_gap_seconds"])
    for key, wanted, running, starter, label in (
            ("drive", cfg["repair_drive"], beat["google_drive_running"],
             start_google_drive, "Google Drive"),
            ("claude", cfg["keep_claude_running"], beat["claude_app_running"],
             lambda: start_claude(cfg), "the Claude app")):
        if not wanted or running is not False:
            continue
        if t - st["repair_at"].get(key, 0) < gap:
            continue
        st["repair_at"][key] = t
        try:
            how = starter()
        except Exception as ex:                                # noqa: BLE001
            how = None
            log("could not start %s: %s: %s" % (label, ex.__class__.__name__, ex))
        note = ("%s  %s was not running -- %s"
                % (iso(), label, ("started it (%s)" % how) if how
                   else "and I found no way to start it"))
        st["repairs"].append(note)
        log(note)
    # Chrome saving somewhere else: put right, but only while Chrome is closed
    if cfg.get("repair_chrome_download") and \
       beat.get("chrome_saves_to_exports") is False and \
       "chrome.exe" not in procs and t - st["repair_at"].get("chrome", 0) >= gap:
        st["repair_at"]["chrome"] = t
        target = drive_sub(beat.get("my_drive"), cfg["docterz_rel"])
        res = chrome_set_download_dir(target, procs)
        note = "%s  Chrome was not saving into Docterz exports -- %s" % (
            iso(), "; ".join("%s: %s" % r for r in res))
        st["repairs"].append(note)
        log(note)


# --------------------------------------------------------------------------
# jobs
# --------------------------------------------------------------------------
def job_command(path):
    ext = os.path.splitext(path)[1].lower()
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    if ext == ".ps1":
        return [os.path.join(sysroot, "System32", "WindowsPowerShell", "v1.0",
                             "powershell.exe"),
                "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-File", path]
    if ext in (".cmd", ".bat"):
        return [os.path.join(sysroot, "System32", "cmd.exe"), "/d", "/c", path]
    if ext == ".py":
        exe = sys.executable or "python"
        if exe.lower().endswith("pythonw.exe"):
            exe = exe[:-len("pythonw.exe")] + "python.exe"
        return [exe, path]
    return None


def job_timeout(path, cfg):
    """`timeout=900` on a COMMENT line (#, REM or ::) within the first ten
    lines, else the default. Only a comment counts: the live walk of S448.1
    took `p.wait(timeout=30)` in a job's own code for the directive."""
    t = int(cfg["job_timeout_default"])
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            head = [fh.readline() for _ in range(10)]
        for line in head:
            m = re.match(r"\s*(?:#|rem\b|::)\s*timeout\s*[=:]\s*(\d{1,6})\b",
                         line, re.I)
            if m:
                t = int(m.group(1))
                break
    except OSError:
        pass
    return max(5, min(t, int(cfg["job_timeout_max"])))


def _job_name_ok(name):
    return bool(JOB_NAME_RE.match(name)) and \
        os.path.splitext(name)[1].lower() in JOB_EXTS


def write_result(name, header, body):
    lines = ["JOB: %s" % name] + header + ["AGENT: %s" % AGENT_VERSION,
                                           "-" * 60, ""]
    _write(os.path.join(JOBS_OUT, name + ".out.txt"),
           "\r\n".join(lines) + body)


def refuse_local(name, why):
    """A file in jobs\\in that will never run is said so, once, and moved."""
    src = os.path.join(JOBS_IN, name)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)[:100] or "unnamed"
    try:
        os.replace(src, os.path.join(
            JOBS_DONE, "%s__REFUSED__%s" % (now().strftime("%Y%m%d-%H%M%S"), safe)))
    except OSError:
        return
    try:
        write_result(safe, ["REFUSED: %s" % why, "ENDED: %s" % iso()], "")
    except OSError:
        pass
    log("job refused: %s (%s)" % (safe, why))


def poll_local_jobs(st, cfg):
    """Start the next job in jobs\\in, oldest name first, one at a time."""
    if st.get("job"):
        return
    try:
        names = sorted(n for n in os.listdir(JOBS_IN)
                       if os.path.isfile(os.path.join(JOBS_IN, n)))
    except OSError:
        return
    seen = {}
    for name in names:
        low = name.lower()
        if low == "desktop.ini" or low.endswith((".tmp", ".part", ".crdownload")):
            continue
        path = os.path.join(JOBS_IN, name)
        try:
            sig = (os.path.getsize(path), os.path.getmtime(path))
        except OSError:
            continue
        seen[name] = sig
        # a file still being written is left for the next look -- and that
        # is decided BEFORE its name is judged, so an upload passing through
        # a temporary name is never taken away half-written
        if st["job_sizes"].get(name) != sig or abs(time.time() - sig[1]) < 2:
            continue
        if not _job_name_ok(name):
            refuse_local(name, "the name must be letters, digits, . _ - and "
                               "end in .ps1 .cmd .bat or .py")
            continue
        if start_job(st, cfg, name):
            break
    st["job_sizes"] = seen


def start_job(st, cfg, name):
    src = os.path.join(JOBS_IN, name)
    run_path = os.path.join(JOBS_RUNNING, name)
    try:
        os.replace(src, run_path)
    except OSError:
        return False                 # still held by whoever is writing it
    cmd = job_command(run_path)
    timeout = job_timeout(run_path, cfg)
    raw_path = os.path.join(JOBS_RUNNING, name + ".raw")
    started = time.time()
    fh = None
    try:
        os.remove(os.path.join(JOBS_OUT, name + ".out.txt"))
    except OSError:
        pass                         # no earlier result under this name
    try:
        fh = open(raw_path, "wb")
        proc = subprocess.Popen(cmd, cwd=JOBS_WORK, stdin=subprocess.DEVNULL,
                                stdout=fh, stderr=subprocess.STDOUT,
                                creationflags=NO_WINDOW)
    except Exception as ex:                                    # noqa: BLE001
        try:
            if fh is not None:
                fh.close()
        except Exception:                                      # noqa: BLE001
            pass
        log("job %s could not start: %s: %s" % (name, ex.__class__.__name__, ex))
        finish_files(st, cfg, name, started, None, False,
                     "COULD NOT START: %s: %s" % (ex.__class__.__name__, ex))
        return True
    st["job"] = {"name": name, "proc": proc, "fh": fh, "started": started,
                 "timeout": timeout, "raw": raw_path, "md5": _md5(run_path)}
    log("job started: %s (pid %d, timeout %ds, md5 %s)"
        % (name, proc.pid, timeout, st["job"]["md5"]))
    return True


def poll_running_job(st, cfg):
    job = st.get("job")
    if not job:
        return
    rc = job["proc"].poll()
    timed_out = False
    if rc is None:
        if time.time() - job["started"] < job["timeout"]:
            return
        timed_out = True
        log("job %s passed its %ds limit -- stopping it" % (job["name"],
                                                             job["timeout"]))
        kill_tree(job["proc"].pid)
        try:
            job["proc"].wait(timeout=8)
        except Exception:                                      # noqa: BLE001
            try:
                job["proc"].kill()
            except Exception:                                  # noqa: BLE001
                pass
        rc = job["proc"].poll()
    try:
        job["fh"].close()
    except Exception:                                          # noqa: BLE001
        pass
    st["job"] = None
    finish_files(st, cfg, job["name"], job["started"], rc, timed_out, None,
                 job.get("md5"))


def finish_files(st, cfg, name, started, rc, timed_out, error, md5=None):
    raw_path = os.path.join(JOBS_RUNNING, name + ".raw")
    cap = int(cfg["job_output_max_bytes"])
    body = ""
    try:
        size = os.path.getsize(raw_path)
        with open(raw_path, "rb") as fh:
            if size <= cap:
                body = _decode(fh.read())
            else:
                head = fh.read(cap // 4)
                fh.seek(size - (cap - cap // 4))
                body = (_decode(head)
                        + "\r\n\r\n[... %d bytes cut from the middle ...]\r\n\r\n"
                        % (size - cap) + _decode(fh.read()))
    except OSError:
        pass
    header = ["STARTED: %s" % iso(started), "ENDED: %s" % iso(),
              "SECONDS: %.1f" % (time.time() - started),
              "EXIT: %s" % ("none" if rc is None else rc),
              "TIMED_OUT: %s" % ("yes" if timed_out else "no"),
              "SCRIPT_MD5: %s" % (md5 or "unknown")]
    if error:
        header.append("ERROR: %s" % error)
    try:
        write_result(name, header, body)
        try:
            os.remove(raw_path)
        except OSError:
            pass                     # swept at the next start
    except OSError as ex:
        # the raw output is the only copy left: keep it, beside the results
        log("could not write the result of %s: %s" % (name, ex))
        try:
            _replace(raw_path, os.path.join(JOBS_OUT, name + ".raw.txt"))
        except OSError:
            pass
    try:
        os.replace(os.path.join(JOBS_RUNNING, name), os.path.join(
            JOBS_DONE, "%s__%s" % (now().strftime("%Y%m%d-%H%M%S"), name)))
    except OSError:
        pass
    st["jobs_done"] += 1
    st["last_job"] = {"name": name, "ended": iso(), "exit": rc,
                      "timed_out": timed_out}
    log("job finished: %s exit %s%s" % (name, rc,
                                         " (TIMED OUT)" if timed_out else ""))
    if name.startswith(DRIVE_JOB_PREFIX):
        st["drive_results"].append(name)
    prune(JOBS_DONE, int(cfg["keep_done"]))
    prune(JOBS_OUT, int(cfg["keep_done"]))


def prune(folder, keep):
    try:
        files = sorted((os.path.getmtime(os.path.join(folder, n)), n)
                       for n in os.listdir(folder)
                       if os.path.isfile(os.path.join(folder, n)))
    except OSError:
        return
    for _, n in files[:-keep] if keep > 0 and len(files) > keep else []:
        try:
            os.remove(os.path.join(folder, n))
        except OSError:
            pass


# --------------------------------------------------------------------------
# jobs that arrive through the clinic Drive -- signed, or not run
# --------------------------------------------------------------------------
def _seen_read():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def _seen_write(seen):
    """True if the list reached the disk. Accepted names are kept for 30
    days -- far beyond the 48 hours in which a job can still be accepted --
    and are never pushed out by a flood of refused ones."""
    try:
        cutoff = (now() - dt.timedelta(days=30)).isoformat(timespec="seconds")
        good = {k: v for k, v in seen.items()
                if not v.get("refused") and v.get("at", "") >= cutoff}
        bad = sorted(((k, v) for k, v in seen.items() if v.get("refused")),
                     key=lambda kv: kv[1].get("at", ""))[-2000:]
        keep = dict(bad)
        keep.update(good)
        _write(SEEN_FILE, json.dumps(keep, indent=1))
        return True
    except OSError as ex:
        log("could not record the Drive jobs seen: %s" % ex)
        return False


def drive_job_stamp_verdict(name):
    """None if the name carries a signing time inside the window."""
    m = DRIVE_JOB_STAMP_RE.match(name)
    if not m:
        return "the name must begin with the signing time, YYYYMMDDTHHMMSS_"
    try:
        when = dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return "the signing time in the name is not a real date"
    age_h = (now() - when).total_seconds() / 3600.0
    if age_h > DRIVE_JOB_MAX_AGE_HOURS:
        return "signed more than %d hours ago" % DRIVE_JOB_MAX_AGE_HOURS
    if age_h < -DRIVE_JOB_MAX_AHEAD_HOURS:
        return "its signing time is in the future"
    return None


def poll_drive_jobs(st, cfg):
    """Copy correctly signed jobs from ToReception\\jobs into jobs\\in.

    Every refusal is written down once, in FromReception\\results, and never
    retried: a name is used once. With no key enrolled nothing is even read.
    The name is recorded as used BEFORE the job is queued; if that record
    cannot be written the job is not queued at all.
    """
    keys = authorized_keys()
    if not keys:
        return
    my_drive = find_my_drive()
    inn, out = drive_in(my_drive, cfg), drive_out(my_drive, cfg)
    if not inn or not out:
        return
    jobs_dir = os.path.join(inn, "jobs")
    res_dir = os.path.join(out, "results")
    try:
        os.makedirs(jobs_dir, exist_ok=True)
        os.makedirs(res_dir, exist_ok=True)
        names = sorted(os.listdir(jobs_dir))
    except OSError:
        return
    seen = _seen_read()
    for name in names:
        path = os.path.join(jobs_dir, name)
        if name.lower().endswith(".sig") or not os.path.isfile(path):
            continue
        if name in seen or not os.path.isfile(path + ".sig"):
            continue                 # used already, or its signature not here yet
        try:
            if time.time() - os.path.getmtime(path + ".sig") < 5:
                continue             # the signature may still be arriving
        except OSError:
            continue
        verdict, content = None, b""
        if not _job_name_ok(name):
            verdict = "the name is not allowed"
        else:
            try:
                if os.path.getsize(path) > DRIVE_JOB_MAX_BYTES:
                    verdict = "the job is larger than 1 MB"
                else:
                    with open(path, "rb") as fh:
                        content = fh.read()
                    with open(path + ".sig", "r", encoding="ascii",
                              errors="replace") as fh:
                        sig_hex = fh.read().strip()
                    sig = bytes.fromhex(sig_hex) if re.fullmatch(
                        r"[0-9a-fA-F]{128}", sig_hex) else b""
                    msg = job_message(name, content)
                    if not any(ed_verify(k, msg, sig) for k, _ in keys):
                        verdict = "the signature does not match an enrolled key"
                    else:
                        verdict = drive_job_stamp_verdict(name)
            except OSError:
                continue             # Drive still bringing the file down
        seen[name] = {"at": iso(), "sha256": hashlib.sha256(content).hexdigest(),
                      "refused": verdict}
        if not _seen_write(seen):
            del seen[name]
            log("drive job %s NOT taken: its name could not be recorded" % name)
            continue
        if verdict:
            st["drive_refused"] += 1
            log("DRIVE JOB REFUSED: %s -- %s" % (name, verdict))
            try:
                _write(os.path.join(res_dir, re.sub(
                    r"[^A-Za-z0-9._-]", "_", name)[:100] + ".REFUSED.txt"),
                    "REFUSED %s\r\n%s\r\n" % (iso(), verdict))
            except OSError:
                pass
            continue
        try:
            tmp = os.path.join(JOBS_IN, DRIVE_JOB_PREFIX + name + ".tmp")
            with open(tmp, "wb") as fh:
                fh.write(content)
            _replace(tmp, os.path.join(JOBS_IN, DRIVE_JOB_PREFIX + name))
            log("drive job accepted: %s (sha256 %s)"
                % (name, seen[name]["sha256"][:16]))
        except OSError as ex:
            log("could not queue the drive job %s: %s" % (name, ex))
            continue
        # taken: move it out of the way so the folder shows what is waiting
        try:
            done_dir = os.path.join(jobs_dir, "_taken")
            os.makedirs(done_dir, exist_ok=True)
            os.replace(path, os.path.join(done_dir, name))
            os.replace(path + ".sig", os.path.join(done_dir, name + ".sig"))
        except OSError:
            pass
    # results of finished Drive jobs go back up
    for name in list(st["drive_results"]):
        src = os.path.join(JOBS_OUT, name + ".out.txt")
        try:
            shutil.copyfile(src, os.path.join(
                res_dir, name[len(DRIVE_JOB_PREFIX):] + ".out.txt"))
            st["drive_results"].remove(name)
        except OSError as ex:
            log("could not send the result of %s to Drive: %s" % (name, ex))


# --------------------------------------------------------------------------
# replacing this file safely
# --------------------------------------------------------------------------
def _compiles(path):
    import py_compile
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".pyc")
    os.close(fd)
    try:
        py_compile.compile(path, cfile=tmp, doraise=True)
        return True, ""
    except Exception as ex:                                    # noqa: BLE001
        return False, "%s: %s" % (ex.__class__.__name__, ex)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def take_update():
    """reception_agent.py.new -> this file. True means: leave now, code 42."""
    if not os.path.isfile(NEW_FILE):
        return False
    try:
        if time.time() - os.path.getmtime(NEW_FILE) < 3:
            return False             # still being written
    except OSError:
        return False
    new_md5 = _md5(NEW_FILE)
    if new_md5 == _md5(AGENT_FILE):
        try:
            os.remove(NEW_FILE)
        except OSError:
            pass
        log("update ignored: the new file is the one already running")
        return False
    ok, why = _compiles(NEW_FILE)
    if not ok:
        log("UPDATE REFUSED: the new agent does not compile -- %s" % why)
        try:
            os.replace(NEW_FILE, P("reception_agent.py.rejected"))
        except OSError:
            pass
        return False
    try:
        shutil.copyfile(AGENT_FILE, PREV_FILE)
        _write(UPDATE_MARKER, json.dumps(
            {"at": iso(), "from_md5": _md5(AGENT_FILE), "to_md5": new_md5,
             "from_version": AGENT_VERSION}))
        os.replace(NEW_FILE, AGENT_FILE)
    except OSError as ex:
        log("UPDATE FAILED while swapping files: %s" % ex)
        return False
    log("update installed (md5 %s) -- restarting under the guard" % new_md5)
    return True


def confirm_update():
    """A first heartbeat written means the new agent runs: keep it."""
    if os.path.exists(UPDATE_MARKER):
        try:
            os.remove(UPDATE_MARKER)
            log("update confirmed: this version wrote its first heartbeat")
        except OSError:
            pass


# --------------------------------------------------------------------------
def ensure_dirs():
    for d in (JOBS_IN, JOBS_RUNNING, JOBS_OUT, JOBS_DONE, JOBS_WORK, P("_off")):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(KEYS_FILE):
        _write(KEYS_FILE,
               "# One line per key that may send jobs through the clinic Drive:\r\n"
               "#   <64 hex characters of an Ed25519 public key>  <label>\r\n"
               "# Empty means the Drive door is shut. Local jobs need no key.\r\n")


def recover_orphans(st, cfg):
    """A job cut short by a restart is reported, never silently re-run."""
    try:
        names = [n for n in os.listdir(JOBS_RUNNING) if not n.endswith(".raw")]
    except OSError:
        return
    for name in names:
        log("job %s was running when the agent last stopped" % name)
        finish_files(st, cfg, name, time.time(), None, False,
                     "the agent restarted while this job was running; "
                     "it was NOT run again")
    try:
        for n in os.listdir(JOBS_RUNNING):
            if n.endswith(".raw"):
                os.remove(os.path.join(JOBS_RUNNING, n))
    except OSError:
        pass


def selftest():
    """Read-only. Prints what the agent can see; changes nothing but its own
    folders. Run by the installer and safe to run by hand."""
    quiet_errors()
    ensure_dirs()
    cfg = load_config()
    st = new_state()
    beat, procs = build_beat(st, cfg)
    sys.stdout.write(human(beat).replace("\r\n", "\n"))
    sys.stdout.write("\nprocess list read: %s\n" % _yn(procs is not None))
    lnk = find_claude_shortcut()
    sys.stdout.write("Claude app: %s\n"
                     % ("not kept running (config.json)" if not cfg.get("keep_claude_running")
                        else "started by the command in config.json" if cfg.get("claude_start_command")
                        else "started from its Start-menu shortcut" if lnk
                        else "NO WAY TO START IT -- set claude_start_command "
                             "in config.json"))
    vec = bytes.fromhex(
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    pub = ed_public(vec)
    ok = (pub.hex() == "d75a980182b10ab7d54bfed3c964073a"
                       "0ee172f3daa62325af021a68f707511a"
          and ed_verify(pub, b"", ed_sign(vec, b""))
          and not ed_verify(pub, b"x", ed_sign(vec, b"")))
    sys.stdout.write("signature check (RFC 8032 vector): %s\n"
                     % ("ok" if ok else "FAILED"))
    sys.stdout.write("direct upload: %s, this PC's public key %s\n"
                     % ("on" if cfg.get("direct_upload") else "OFF",
                        beat["direct_upload"]["public_key"] or "NOT MADE"))
    return 0 if ok else 1


def new_state():
    return {"started_at": iso(), "started_ts": time.time(), "job": None,
            "job_sizes": {}, "jobs_done": 0, "last_job": None,
            "drive_refused": 0, "drive_results": [], "repairs": [],
            "repair_at": {},
            "upload": {"ok_at": None, "fail_streak": 0, "last_error": None,
                       "reports_sent": 0, "last_report_at": None},
            "upload_cache": {}}


def main():
    quiet_errors()
    ensure_dirs()
    st = new_state()
    cfg = load_config()
    log("=" * 60)
    log("reception_agent %s starting (python %s, pid %d)"
        % (AGENT_VERSION, sys.version.split()[0], os.getpid()))
    recover_orphans(st, cfg)
    last_beat = 0.0
    last_drive = 0.0
    last_tick = time.time()
    while True:
        cfg = load_config()
        # The PC slept, or its clock was corrected. Time that passed while
        # nothing ran is not charged to a running job, and a heartbeat is
        # written at once -- before the guard can mistake silence for death.
        t = time.time()
        gap = t - last_tick
        if gap > 120 or gap < 0:
            log("the clock jumped %+ds (sleep or a clock correction)" % int(gap))
            if st.get("job") and gap > 0:
                st["job"]["started"] += gap
            last_beat = 0.0
            last_drive = 0.0
        last_tick = t
        off = is_off(OFF_ALL)
        jobs_off = off or is_off(OFF_JOBS)

        poll_running_job(st, cfg)
        if not jobs_off:
            poll_local_jobs(st, cfg)
            if time.time() - last_drive >= cfg["drive_jobs_seconds"]:
                last_drive = time.time()
                try:
                    poll_drive_jobs(st, cfg)
                except Exception as ex:                        # noqa: BLE001
                    log("drive job pass FAILED: %s: %s"
                        % (ex.__class__.__name__, ex))

        if time.time() - last_beat >= cfg["beat_seconds"]:
            try:
                beat, procs = build_beat(st, cfg)
                write_beat(beat, cfg)
                confirm_update()
                repairs(st, cfg, beat, procs)
                try:
                    direct_pass(st, cfg, beat)
                except Exception as ex:                        # noqa: BLE001
                    log("direct upload FAILED: %s: %s"
                        % (ex.__class__.__name__, ex))
                # time spent talking to the server is not a clock jump
                last_tick = time.time()
            except Exception as ex:                            # noqa: BLE001
                log("heartbeat FAILED: %s: %s" % (ex.__class__.__name__, ex))
                try:
                    _write(LOCAL_BEAT_TXT, "HEARTBEAT FAILED %s\r\n%s: %s\r\n"
                           % (iso(), ex.__class__.__name__, ex))
                except OSError:
                    pass
            last_beat = time.time()

        if not st.get("job") and not off:
            if os.path.exists(RESTART_FLAG):
                try:
                    os.remove(RESTART_FLAG)
                except OSError as ex:
                    # a flag that cannot be removed would restart for ever
                    if not st.get("flag_warned"):
                        st["flag_warned"] = True
                        log("RESTART.flag cannot be removed (%s) -- ignored" % ex)
                else:
                    log("restart asked for (RESTART.flag)")
                    return EXIT_RESTART
            if take_update():
                return EXIT_RESTART

        time.sleep(cfg["tick_seconds"])


def install_keys(src):
    """Add to authorized_keys.txt every key in `src` that is not there yet.
    Public keys only -- this is how a reinstall gets the Drive door back."""
    ensure_dirs()
    have = {k for k, _ in authorized_keys()}
    global KEYS_FILE
    mine, KEYS_FILE = KEYS_FILE, src
    try:
        new = [(k, lab) for k, lab in authorized_keys() if k not in have]
    finally:
        KEYS_FILE = mine
    if new:
        with open(KEYS_FILE, "a", encoding="utf-8", newline="") as fh:
            for k, lab in new:
                fh.write("%s  %s\r\n" % (k.hex(), lab))
    return len(new), len(have) + len(new)


def cli(argv):
    if argv[1] == "--selftest":
        return selftest()
    if argv[1] == "--set-chrome-download":
        quiet_errors()
        cfg = load_config()
        target = drive_sub(find_my_drive(), cfg["docterz_rel"])
        for prof, what in chrome_set_download_dir(target):
            sys.stdout.write("Chrome %s: %s\n" % (prof, what))
        return 0
    if argv[1] == "--install-keys" and len(argv) > 2:
        added, total = install_keys(argv[2])
        sys.stdout.write("Drive-door keys: %d added from the kit, %d enrolled%s\n"
                         % (added, total, "" if total else " (the Drive door is shut)"))
        return 0
    sys.stdout.write("unknown option\n")
    return 2


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(cli(sys.argv))
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:                                      # noqa: BLE001
        import traceback
        blob = ("reception_agent %s CRASHED at %s\n\n%s"
                % (AGENT_VERSION, iso(), traceback.format_exc()))
        for path in (CRASH_FILE, AGENT_LOG):
            try:
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(blob + "\n")
            except OSError:
                pass
        try:
            out = drive_out(find_my_drive(), load_config())
            if out:
                with open(os.path.join(out, "agent_crash.txt"), "w",
                          encoding="utf-8") as fh:
                    fh.write(blob)
        except Exception:                                      # noqa: BLE001
            pass
        raise
