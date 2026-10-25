#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_door.py -- kit S655_LAB_PC_AGENT (session 351, the NK Pathology chat, 25-Oct-2026, D784). THIS PROJECT'S FILE.

THE OWNER, 25-Oct-2026: "Go ahead with the lab PC agent ... plan a direct upload to the server from this PC also."

The NK Pathology lab PC (LABPC) runs Labmate; its data is one Access file, lab.mdb in E:/Labmate982, with Captdata.mdb
beside it. Until today nothing of it left that PC except the staff's own backup zip, kept on the same drive. The lab
agent (lab_agent.py, derived from reception_agent.py S456.1) now posts straight to this server over HTTPS, the same
road the reception PC uses (reception_door.py, S449/S453), and this file is that road's lab end -- derived from
reception_door.py by make_lab_door.py in the kit, so what is proven there is proven here:

  POST /finance/api/lab/heartbeat         the agent's heartbeat (COUNTS AND DATES ONLY -- the agent's own rule)
  POST /finance/api/lab/snap/status       what this server already holds of a snapshot (so a dropped send resumes)
  POST /finance/api/lab/snap/part         one part (<= 4 MB) of a snapshot zip: lab.mdb + Captdata.mdb, zipped on the PC
  POST /finance/api/lab/snap/finish       the whole: parts count, bytes and SHA-256; the server joins, checks, keeps
  POST /finance/api/lab/jobs/submit|next|ack|result|read   the job relay, exactly the reception relay (S453)
  POST /finance/api/lab/snap/list         the owner's PC reads what snapshots are here (signed by a job key)

NO SHARED SECRET TRAVELS. Each request is signed with an Ed25519 key made ON the lab PC that never leaves it; this
server holds only the PUBLIC key (lab_keys.txt). What is signed: a fixed context (clinic-lab-upload-v1), the kind, the
sender's clock, the part's name and time, and the SHA-256 of the body; a request more than 15 minutes from this
server's clock is refused. A snapshot is kept only when the joined parts' SHA-256 equals the one the PC signed in the
finish line, and only under /root/labdata/incoming/ (mode 700), where it is pruned after KEEP_DAYS. The bytes are
patient data: they are never logged and never served back by this door; the day page (a later kit) reads them here.

The paths are in finance_app's PUBLIC_PATHS (like the reception doors): the gate lets them reach this handler and
THIS HANDLER authenticates. With no key file the door answers 503 and takes nothing (fail closed).

Stdlib + Flask. Creates no table. Sends nothing anywhere. Queue: /root/labdata/lab_jobs (mode 700), pruned after 14 days.
"""
import base64
import binascii
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time

from flask import Blueprint, Response, jsonify, request

HERE = os.path.dirname(os.path.abspath(__file__))
LAB_HOME = os.environ.get("LAB_HOME", "/root/labdata")
KEYS_FILE = os.environ.get("LAB_KEYS", os.path.join(LAB_HOME, "lab_keys.txt"))
BEAT_FILE = os.environ.get("LAB_BEAT", os.path.join(LAB_HOME, "lab_heartbeat.json"))
SNAP_DIR = os.environ.get("LAB_SNAP_DIR", os.path.join(LAB_HOME, "incoming"))
SNAP_INDEX = os.path.join(SNAP_DIR, "snapshots.json")
SIG_CONTEXT = b"clinic-lab-upload-v1\n"
MAX_BEAT = 64 * 1024
MAX_PART = 4 * 1024 * 1024      # one part of a snapshot zip (the agent's snapshot_part_bytes is capped at this)
MAX_PARTS = 200                 # 800 MB -- lab.mdb is 73 MB today and zips to ~12 MB
MAX_FINISH = 64 * 1024
KEEP_DAYS = 30                  # snapshots kept on this box
PART_KEEP_HOURS = 48            # unfinished parts
MAX_SKEW = 900                  # seconds either side of this server's clock
RATE_PER_MIN = 120              # one PC: a heartbeat every 5 minutes, and up to ~20 parts in a minute when it sends
NAME_RE = re.compile(r"^[A-Za-z0-9 ._()\-]{0,120}$")
SNAP_NAME_RE = re.compile(r"^labpc_\d{8}_\d{4}\.zip$")
PART_NAME_RE = re.compile(r"^(labpc_\d{8}_\d{4}\.zip)\.part(\d{3})of(\d{3})$")
# S453 -- the job relay, this PC's own queue
JOB_KEYS_FILE = os.environ.get("LAB_JOB_KEYS", os.path.join(LAB_HOME, "lab_job_keys.txt"))
JOB_DIR = os.environ.get("LAB_JOB_DIR", os.path.join(LAB_HOME, "lab_jobs"))
JOB_CONTEXT = b"clinic-lab-job-v1\n"                  # exactly what lab_sign.py signs: context, name, bytes
JOB_READ_CONTEXT = b"clinic-lab-job-read-v1\n"
JOB_NAME_RE = re.compile(r"^(\d{8})T(\d{6})_[A-Za-z0-9][A-Za-z0-9._-]{0,90}\.(?:ps1|cmd|bat|py)$")
MAX_JOB = 256 * 1024
MAX_RESULT = 1024 * 1024
JOB_MAX_AGE_HOURS = 48          # the agent's own rule; a job it would refuse is not queued
JOB_MAX_AHEAD_HOURS = 2
JOB_KEEP_DAYS = 14
JOB_WAITING_MAX = 20

bp = Blueprint("lab_door", __name__)
_db = None
_hits = []


def init(app, db_getter, url_prefix=""):
    """Mounted at import time from finance_app.py, like every other module here."""
    global _db
    _db = db_getter
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ---------------------------------------------------------------------------------------------------------------------
# Ed25519 (RFC 8032) -- verify only, pure Python: the same code the reception agent verifies its Drive jobs with
# (reception_agent.py, S448), proven in this kit's walk against the RFC's own vectors.
# ---------------------------------------------------------------------------------------------------------------------
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
        h = int.from_bytes(hashlib.sha512(rs + public + msg).digest(), "little") % _EL
        return _eeq(_emul(s, _EG), _eadd(R, _emul(h, A)))
    except Exception:                                          # noqa: BLE001
        return False


# ---------------------------------------------------------------------------------------------------------------------
def upload_message(kind, ts, name, mtime, body):
    """Exactly what the lab agent signs (its own function of the same name builds the same bytes)."""
    return (SIG_CONTEXT + kind.encode("ascii") + b"\n" + str(ts).encode("ascii") + b"\n" + name.encode("utf-8") + b"\n"
            + str(mtime).encode("ascii") + b"\n" + hashlib.sha256(body).hexdigest().encode("ascii"))


def enrolled_keys():
    """[(32 raw bytes, label)] from lab_keys.txt; [] shuts the door."""
    out = []
    try:
        with open(KEYS_FILE, "r", encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                hx = parts[0].lower()
                if re.fullmatch(r"[0-9a-f]{64}", hx):
                    out.append((bytes.fromhex(hx), parts[1].strip() if len(parts) > 1 else ""))
    except OSError:
        pass
    return out


def _no(status, message, code, **extra):
    return jsonify(dict(ok=False, status=status, message=message, **extra)), code


def _rate_ok():
    now = time.time()
    while _hits and now - _hits[0] > 60:
        _hits.pop(0)
    if len(_hits) >= RATE_PER_MIN:
        return False
    _hits.append(now)
    return True


def _signed(kind, limit):
    """(label, body, name, mtime, None) for a correctly signed request, else (None, None, None, None, the refusal)."""
    keys = enrolled_keys()
    if not keys:
        return None, None, None, None, _no("NO_KEY", "no lab PC key is enrolled on this server -- nothing taken", 503)
    ts = str(request.headers.get("X-Rx-Time", "")).strip()
    sig_hex = str(request.headers.get("X-Rx-Sig", "")).strip()
    name = str(request.headers.get("X-Rx-Name", "")).strip()
    mtime = str(request.headers.get("X-Rx-Mtime", "")).strip()
    if not re.fullmatch(r"\d{9,11}", ts) or not re.fullmatch(r"[0-9a-fA-F]{128}", sig_hex) \
            or not NAME_RE.match(name) or not re.fullmatch(r"\d{0,11}", mtime):
        return None, None, None, None, _no("NOT_YOU", "missing or malformed signature headers", 401)
    if (request.content_length or 0) > limit + 4096:
        return None, None, None, None, _no("REFUSED", "too big", 413)
    if not _rate_ok():
        return None, None, None, None, _no("SLOW_DOWN", "more than %d requests in a minute; nothing taken" % RATE_PER_MIN, 429)
    body = request.get_data(cache=False) or b""
    if len(body) > limit:
        return None, None, None, None, _no("REFUSED", "too big", 413)
    msg = upload_message(kind, ts, name, mtime, body)
    sig = bytes.fromhex(sig_hex)
    label = next((lab or "labpc" for k, lab in keys if ed_verify(k, msg, sig)), None)
    if label is None:
        return None, None, None, None, _no("NOT_YOU", "the signature does not match an enrolled key", 401)
    skew = int(time.time()) - int(ts)
    if abs(skew) > MAX_SKEW:
        return None, None, None, None, _no("CLOCK", "the sender's clock is %d seconds from this server's; nothing taken"
                                           % (-skew), 401, server_time=int(time.time()))
    return label, body, name, mtime, None


def _ist_now():
    return dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)


@bp.route("/finance/api/lab/heartbeat", methods=["POST"])
def api_lab_heartbeat():
    label, body, _name, _mtime, err = _signed("heartbeat", MAX_BEAT)
    if err:
        return err
    try:
        beat = json.loads(body.decode("utf-8"))
        if not isinstance(beat, dict):
            raise ValueError("not an object")
    except (ValueError, UnicodeDecodeError):
        return _no("REFUSED", "the heartbeat is not a JSON object", 400)
    rec = {"received_ts": int(time.time()), "received_ist": _ist_now().isoformat(timespec="seconds"),
           "from": label, "beat": beat}
    tmp = "%s.%d.tmp" % (BEAT_FILE, os.getpid())
    try:
        os.makedirs(os.path.dirname(BEAT_FILE), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
        os.chmod(tmp, 0o600)
        os.replace(tmp, BEAT_FILE)
    except OSError as ex:
        return _no("NOT_KEPT", "could not write the heartbeat: %s" % str(ex)[:120], 500)
    return jsonify(ok=True, status="KEPT", server_time=rec["received_ts"]), 200


# ---------------------------------------------------------------------------------------------------------------------
# S655 -- the Labmate snapshot, in signed parts
# ---------------------------------------------------------------------------------------------------------------------
def _snap_dirs():
    for d in (LAB_HOME, SNAP_DIR, os.path.join(SNAP_DIR, "_parts")):
        os.makedirs(d, exist_ok=True)
        try:
            os.chmod(d, 0o700)
        except OSError:
            pass


def _parts_dir(name):
    return os.path.join(SNAP_DIR, "_parts", name)


def _index_read():
    try:
        with open(SNAP_INDEX, "r", encoding="utf-8") as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def _index_write(idx):
    tmp = "%s.%d.tmp" % (SNAP_INDEX, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, SNAP_INDEX)


def _snap_log(event, name=""):
    try:
        with open(os.path.join(SNAP_DIR, "log.txt"), "a", encoding="utf-8") as fh:
            fh.write("%s | %s | %s\n" % (_ist_now().strftime("%Y-%m-%d %H:%M:%S"), event, name))
    except OSError:
        pass


def _prune_snapshots():
    """Finished snapshots older than KEEP_DAYS, part folders older than PART_KEEP_HOURS."""
    now = time.time()
    idx = _index_read()
    changed = False
    for name in list(idx):
        p = os.path.join(SNAP_DIR, name)
        try:
            if os.path.isfile(p) and now - os.path.getmtime(p) > KEEP_DAYS * 86400:
                os.remove(p)
                idx.pop(name, None)
                changed = True
                _snap_log("PRUNED after %d days" % KEEP_DAYS, name)
        except OSError:
            pass
    if changed:
        _index_write(idx)
    base = os.path.join(SNAP_DIR, "_parts")
    try:
        for n in os.listdir(base):
            d = os.path.join(base, n)
            if os.path.isdir(d) and now - os.path.getmtime(d) > PART_KEEP_HOURS * 3600:
                for f in os.listdir(d):
                    os.remove(os.path.join(d, f))
                os.rmdir(d)
                _snap_log("unfinished parts dropped after %d h" % PART_KEEP_HOURS, n)
    except OSError:
        pass


def _have_parts(name, total):
    d = _parts_dir(name)
    have = []
    try:
        for n in os.listdir(d):
            m = re.fullmatch(r"(\d{3})\.part", n)
            if m and 1 <= int(m.group(1)) <= total:
                have.append(int(m.group(1)) - 1)
    except OSError:
        pass
    return sorted(have)


@bp.route("/finance/api/lab/snap/status", methods=["POST"])
def api_lab_snap_status():
    label, body, name, _mtime, err = _signed("snap-status", 4096)
    if err:
        return err
    if not SNAP_NAME_RE.match(name):
        return _no("REFUSED", "not a snapshot name (labpc_YYYYMMDD_HHMM.zip)", 400)
    try:
        j = json.loads(body.decode("utf-8"))
        total = int(j.get("parts"))
    except (ValueError, TypeError, AttributeError, UnicodeDecodeError):
        return _no("REFUSED", "the status line needs the parts count", 400)
    if not 1 <= total <= MAX_PARTS:
        return _no("REFUSED", "parts must be 1..%d" % MAX_PARTS, 400)
    _snap_dirs()
    _prune_snapshots()           # old parts folders go here too, not only after a successful finish
    if name in _index_read() and os.path.isfile(os.path.join(SNAP_DIR, name)):
        return jsonify(ok=True, status="DONE", name=name, have=[], message="this snapshot is already kept"), 200
    return jsonify(ok=True, status="PARTIAL", name=name, have=_have_parts(name, total)), 200


@bp.route("/finance/api/lab/snap/part", methods=["POST"])
def api_lab_snap_part():
    label, body, pname, _mtime, err = _signed("snap-part", MAX_PART)
    if err:
        return err
    m = PART_NAME_RE.match(pname)
    if not m:
        return _no("REFUSED", "not a part name (labpc_YYYYMMDD_HHMM.zip.partNNNofMMM)", 400)
    name, idx, total = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1 <= total <= MAX_PARTS and 1 <= idx <= total):
        return _no("REFUSED", "part number out of range", 400)
    if not body:
        return _no("REFUSED", "an empty part", 400)
    _snap_dirs()
    if name in _index_read() and os.path.isfile(os.path.join(SNAP_DIR, name)):
        return jsonify(ok=True, status="ALREADY", name=name, part=idx, message="this snapshot is already kept"), 200
    d = _parts_dir(name)
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    try:
        _jwrite(os.path.join(d, "%03d.part" % idx), body)
        _jwrite(os.path.join(d, "total.txt"), str(total).encode("ascii"))
    except OSError as ex:
        return _no("NOT_KEPT", "could not write the part: %s" % str(ex)[:120], 500)
    return jsonify(ok=True, status="KEPT", name=name, part=idx, of=total, bytes=len(body)), 200


@bp.route("/finance/api/lab/snap/finish", methods=["POST"])
def api_lab_snap_finish():
    label, body, name, _mtime, err = _signed("snap-finish", MAX_FINISH)
    if err:
        return err
    if not SNAP_NAME_RE.match(name):
        return _no("REFUSED", "not a snapshot name", 400)
    try:
        j = json.loads(body.decode("utf-8"))
        total, size, sha = int(j.get("parts")), int(j.get("bytes")), str(j.get("sha256") or "").lower()
        if str(j.get("name")) != name or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("name or sha")
    except (ValueError, TypeError, AttributeError, UnicodeDecodeError):
        return _no("REFUSED", "the finish line needs name, parts, bytes and sha256", 400)
    if not (1 <= total <= MAX_PARTS and 0 < size <= total * MAX_PART):
        return _no("REFUSED", "parts or bytes out of range", 400)
    _snap_dirs()
    idx = _index_read()
    final = os.path.join(SNAP_DIR, name)
    if name in idx and os.path.isfile(final):
        return jsonify(ok=True, status="ALREADY", name=name, sha256=idx[name].get("sha256"),
                       message="this snapshot is already kept"), 200
    have = _have_parts(name, total)
    if have != list(range(total)):
        missing = [i + 1 for i in range(total) if i not in have]
        return _no("INCOMPLETE", "parts missing: %s" % ", ".join(str(x) for x in missing[:20]), 409, missing=missing)
    d = _parts_dir(name)
    tmp = final + ".%d.tmp" % os.getpid()
    h = hashlib.sha256()
    n = 0
    try:
        with open(tmp, "wb") as out:
            for i in range(1, total + 1):
                with open(os.path.join(d, "%03d.part" % i), "rb") as fh:
                    chunk = fh.read(MAX_PART + 1)
                h.update(chunk)
                out.write(chunk)
                n += len(chunk)
        os.chmod(tmp, 0o600)
    except OSError as ex:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return _no("NOT_KEPT", "could not join the parts: %s" % str(ex)[:120], 500)
    if n != size or h.hexdigest() != sha:
        try:
            os.remove(tmp)
        except OSError:
            pass
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)
        _snap_log("REFUSED: joined %d bytes sha %s, the PC said %d bytes sha %s -- parts dropped"
                  % (n, h.hexdigest()[:16], size, sha[:16]), name)
        return _no("NOT_WHOLE", "the joined parts are not the bytes the PC signed (%d bytes, sha %s); send again"
                   % (n, h.hexdigest()[:16]), 409)
    os.replace(tmp, final)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    os.rmdir(d)
    files = j.get("files") if isinstance(j.get("files"), list) else []
    idx[name] = {"sha256": sha, "bytes": size, "parts": total, "from": label,
                 "received_ts": int(time.time()), "received_ist": _ist_now().isoformat(timespec="seconds"),
                 "agent": str(j.get("agent") or "")[:20],
                 "files": [{"name": str(f.get("name"))[:60], "bytes": int(f.get("bytes") or 0),
                            "modified": str(f.get("modified") or "")[:25]} for f in files if isinstance(f, dict)][:10]}
    _index_write(idx)
    _snap_log("KEPT %d bytes in %d parts, sha256 %s, from %s" % (size, total, sha[:16], label), name)
    _prune_snapshots()
    return jsonify(ok=True, status="KEPT", name=name, bytes=size, sha256=sha, server_time=int(time.time())), 200


SNAP_LIST_CONTEXT = b"clinic-lab-snap-list-v1\n"


@bp.route("/finance/api/lab/snap/list", methods=["POST"])
def api_lab_snap_list():
    """The owner's PC reads what is here: names, sizes, dates -- never the bytes. Signed by a job key like S457's list."""
    if not _rate_ok():
        return _no("SLOW_DOWN", "more than %d requests in a minute" % RATE_PER_MIN, 429)
    j = _json_body(4096)
    if j is None:
        return _no("REFUSED", "not a JSON object", 400)
    keys = job_keys()
    if not keys:
        return _no("NO_KEY", "no key is on this server -- the door is shut", 503)
    ts, sig_hex = str(j.get("ts") or ""), str(j.get("sig") or "").strip()
    if not re.fullmatch(r"\d{9,11}", ts) or not re.fullmatch(r"[0-9a-fA-F]{128}", sig_hex):
        return _no("NOT_YOU", "this door needs the time and a signature", 401)
    if not any(ed_verify(k, SNAP_LIST_CONTEXT + ts.encode("ascii"), bytes.fromhex(sig_hex)) for k, _ in keys):
        return _no("NOT_YOU", "the signature does not match a key on this server", 401)
    if abs(int(time.time()) - int(ts)) > MAX_SKEW:
        return _no("CLOCK", "signed more than 15 minutes from this server's clock", 401, server_time=int(time.time()))
    _snap_dirs()
    idx = _index_read()
    out = []
    for name in sorted(idx):
        p = os.path.join(SNAP_DIR, name)
        row = dict(idx[name])
        row["name"] = name
        row["present"] = os.path.isfile(p)
        out.append(row)
    return jsonify(ok=True, status="LIST", snapshots=out, keep_days=KEEP_DAYS, server_time=int(time.time())), 200


# ---------------------------------------------------------------------------------------------------------------------
# S453 -- the job relay
# ---------------------------------------------------------------------------------------------------------------------
def _keys_of(path):
    out = []
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                hx = parts[0].lower()
                if re.fullmatch(r"[0-9a-f]{64}", hx):
                    out.append((bytes.fromhex(hx), parts[1].strip() if len(parts) > 1 else ""))
    except OSError:
        pass
    return out


def job_keys():
    """[(32 raw bytes, label)] of the keys that may send a job; [] shuts the relay."""
    return _keys_of(JOB_KEYS_FILE)


def _jd(sub):
    """The queue's folder (or one of its four parts), made if need be and closed to everyone but this service's user."""
    for d in (JOB_DIR, os.path.join(JOB_DIR, sub)):
        os.makedirs(d, exist_ok=True)
        try:
            os.chmod(d, 0o700)
        except OSError:
            pass
    return os.path.join(JOB_DIR, sub)


def _jlog(event, name=""):
    try:
        with open(os.path.join(_jd(""), "log.txt"), "a", encoding="utf-8") as fh:
            fh.write("%s | %s | %s\n" % (_ist_now().strftime("%Y-%m-%d %H:%M:%S"), event, name))
    except OSError:
        pass


def _jwrite(path, data):
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _jread(path, limit):
    try:
        with open(path, "rb") as fh:
            return fh.read(limit)
    except OSError:
        return None


def job_state(name):
    """(state, the result text or None, the refusal or None). States: QUEUED, TAKEN, RESULT, REFUSED, UNKNOWN."""
    res = _jread(os.path.join(JOB_DIR, "results", name + ".out.txt"), MAX_RESULT)
    ref = _jread(os.path.join(JOB_DIR, "refused", name + ".txt"), 2000)
    if res is not None:
        return "RESULT", res.decode("utf-8", errors="replace"), None
    if ref is not None:
        return "REFUSED", None, ref.decode("utf-8", errors="replace")
    if os.path.isfile(os.path.join(JOB_DIR, "taken", name)):
        return "TAKEN", None, None
    if os.path.isfile(os.path.join(JOB_DIR, "in", name)):
        return "QUEUED", None, None
    return "UNKNOWN", None, None


def _job_stamp_verdict(name):
    m = JOB_NAME_RE.match(name)
    try:
        when = dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return "the signing time in the name is not a real date"
    age_h = (_ist_now() - when).total_seconds() / 3600.0
    if age_h > JOB_MAX_AGE_HOURS:
        return "signed more than %d hours ago" % JOB_MAX_AGE_HOURS
    if age_h < -JOB_MAX_AHEAD_HOURS:
        return "its signing time is in the future"
    return None


def _prune_jobs():
    cutoff = time.time() - JOB_KEEP_DAYS * 86400
    for sub in ("in", "taken", "results", "refused"):
        d = os.path.join(JOB_DIR, sub)
        try:
            for n in os.listdir(d):
                p = os.path.join(d, n)
                if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                    os.remove(p)
        except OSError:
            pass


def _json_body(limit):
    if (request.content_length or 0) > limit:
        return None
    raw = request.get_data(cache=False) or b""
    if len(raw) > limit:
        return None
    try:
        j = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return j if isinstance(j, dict) else None


@bp.route("/finance/api/lab/jobs/submit", methods=["POST"])
def api_lab_job_submit():
    keys = job_keys()
    if not keys:
        return _no("NO_KEY", "no job key is on this server -- the relay is shut", 503)
    if not _rate_ok():
        return _no("SLOW_DOWN", "more than %d requests in a minute; nothing taken" % RATE_PER_MIN, 429)
    j = _json_body(MAX_JOB * 4 // 3 + 4096)
    if j is None:
        return _no("REFUSED", "not a JSON object, or too big", 400)
    name, sig_hex = str(j.get("name") or ""), str(j.get("sig") or "").strip()
    if not JOB_NAME_RE.match(name):
        return _no("REFUSED", "the name must be <YYYYMMDDTHHMMSS>_<letters, digits, . _ -> ending .py .cmd .bat or .ps1", 400)
    if not re.fullmatch(r"[0-9a-fA-F]{128}", sig_hex):
        return _no("NOT_YOU", "no signature", 401)
    try:
        content = base64.b64decode(str(j.get("job") or ""), validate=True)
    except (ValueError, binascii.Error):
        return _no("REFUSED", "the job is not base64", 400)
    if not content or len(content) > MAX_JOB:
        return _no("REFUSED", "the job is empty or larger than %d KB" % (MAX_JOB // 1024), 400)
    msg = JOB_CONTEXT + name.encode("utf-8") + b"\n" + content
    sig = bytes.fromhex(sig_hex)
    label = next((lab or "job key" for k, lab in keys if ed_verify(k, msg, sig)), None)
    if label is None:
        _jlog("REFUSED at the door: the signature matches no job key", name)
        return _no("NOT_YOU", "the signature does not match a job key on this server", 401)
    verdict = _job_stamp_verdict(name)
    if verdict:
        return _no("REFUSED", verdict, 400)
    state = job_state(name)[0]
    if state != "UNKNOWN":
        return jsonify(ok=True, status="ALREADY", state=state, message="this job is already here -- a name is used once"), 200
    try:
        inn = _jd("in")
        if len([n for n in os.listdir(inn) if not n.endswith((".sig", ".tmp"))]) >= JOB_WAITING_MAX:
            return _no("FULL", "%d jobs are already waiting for that PC" % JOB_WAITING_MAX, 429)
        _jwrite(os.path.join(inn, name + ".sig"), sig_hex.lower().encode("ascii"))
        _jwrite(os.path.join(inn, name), content)
    except OSError as ex:
        return _no("NOT_KEPT", "could not queue the job: %s" % str(ex)[:120], 500)
    _prune_jobs()
    _jlog("QUEUED (signed by %s, %d bytes, sha256 %s)" % (re.sub(r"[^A-Za-z0-9 _.()-]", "", label)[:40], len(content),
                                                         hashlib.sha256(content).hexdigest()[:16]), name)
    return jsonify(ok=True, status="QUEUED", state="QUEUED", bytes=len(content)), 200


@bp.route("/finance/api/lab/jobs/next", methods=["POST"])
def api_lab_job_next():
    label, _body, _name, _mtime, err = _signed("jobs-next", 1024)
    if err:
        return err
    inn = os.path.join(JOB_DIR, "in")
    try:
        names = sorted(n for n in os.listdir(inn) if JOB_NAME_RE.match(n) and os.path.isfile(os.path.join(inn, n + ".sig")))
    except OSError:
        names = []
    for name in names:
        content, sig = _jread(os.path.join(inn, name), MAX_JOB + 1), _jread(os.path.join(inn, name + ".sig"), 200)
        if content is None or sig is None or len(content) > MAX_JOB:
            continue
        return jsonify(ok=True, status="JOB", name=name, job=base64.b64encode(content).decode("ascii"),
                       sig=sig.decode("ascii", errors="replace").strip(), waiting=len(names)), 200
    return jsonify(ok=True, status="NONE", waiting=0), 200


@bp.route("/finance/api/lab/jobs/ack", methods=["POST"])
def api_lab_job_ack():
    label, body, name, _mtime, err = _signed("jobs-ack", 2000)
    if err:
        return err
    if not JOB_NAME_RE.match(name):
        return _no("REFUSED", "not a job name", 400)
    word = body.decode("utf-8", errors="replace").strip()
    src = os.path.join(JOB_DIR, "in", name)
    try:
        if word != "taken":
            _jwrite(os.path.join(_jd("refused"), name + ".txt"), ("REFUSED BY THE PC %s\n%s\n" % (
                _ist_now().isoformat(timespec="seconds"), re.sub(r"[^\x20-\x7e]", "?", word)[:500])).encode("utf-8"))
        if os.path.isfile(src):
            os.replace(src, os.path.join(_jd("taken"), name))
        try:
            os.remove(src + ".sig")
        except OSError:
            pass
    except OSError as ex:
        return _no("NOT_KEPT", "could not record it: %s" % str(ex)[:120], 500)
    _jlog("the PC %s: %s" % (label, "took it" if word == "taken" else "REFUSED it"), name)
    return jsonify(ok=True, status="NOTED"), 200


@bp.route("/finance/api/lab/jobs/result", methods=["POST"])
def api_lab_job_result():
    label, body, name, _mtime, err = _signed("job-result", MAX_RESULT)
    if err:
        return err
    if not JOB_NAME_RE.match(name):
        return _no("REFUSED", "not a job name", 400)
    if job_state(name)[0] == "UNKNOWN":
        return _no("REFUSED", "this server never handed out a job of that name", 400)
    try:
        _jwrite(os.path.join(_jd("results"), name + ".out.txt"), body)
    except OSError as ex:
        return _no("NOT_KEPT", "could not keep the result: %s" % str(ex)[:120], 500)
    _jlog("the PC %s sent the result (%d bytes)" % (label, len(body)), name)
    return jsonify(ok=True, status="KEPT"), 200


@bp.route("/finance/api/lab/jobs/read", methods=["POST"])
def api_lab_job_read():
    keys = job_keys()
    if not keys:
        return _no("NO_KEY", "no job key is on this server -- the relay is shut", 503)
    if not _rate_ok():
        return _no("SLOW_DOWN", "more than %d requests in a minute" % RATE_PER_MIN, 429)
    j = _json_body(4096)
    if j is None:
        return _no("REFUSED", "not a JSON object", 400)
    name, ts, sig_hex = str(j.get("name") or ""), str(j.get("ts") or ""), str(j.get("sig") or "").strip()
    if not JOB_NAME_RE.match(name) or not re.fullmatch(r"\d{9,11}", ts) or not re.fullmatch(r"[0-9a-fA-F]{128}", sig_hex):
        return _no("NOT_YOU", "a read needs the job's name, the time and a signature", 401)
    msg = JOB_READ_CONTEXT + name.encode("utf-8") + b"\n" + ts.encode("ascii")
    if not any(ed_verify(k, msg, bytes.fromhex(sig_hex)) for k, _ in keys):
        return _no("NOT_YOU", "the signature does not match a job key on this server", 401)
    if abs(int(time.time()) - int(ts)) > MAX_SKEW:
        return _no("CLOCK", "this read was signed more than 15 minutes from this server's clock", 401, server_time=int(time.time()))
    state, result, refused = job_state(name)
    return jsonify(ok=True, status=state, state=state, result=result, refused=refused), 200


# ---------------------------------------------------------------------------------------------------------------------
def read_beat():
    try:
        with open(BEAT_FILE, "r", encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) and isinstance(rec.get("beat"), dict) else None
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------------------------------------------------
def health_row(add, setting, con, now_ts=None, now_ist=None):
    """One row for /finance/health, "Lab PC" -- NOT wired by kit S655 (finance_app.py is the parent's; one line there
    later). The age is measured on THIS server's clock from when the heartbeat ARRIVED. Red after 3 h while the lab is
    open (08:00-20:30 Mon-Sat, 08:00-14:00 Sun, IST); amber when the last snapshot is older than a day."""
    now_ts = now_ts or time.time()
    now_ist = now_ist or _ist_now()
    rec = read_beat()
    if rec is None:
        add("labpc", "Lab PC", "red", "no heartbeat has ever arrived from the lab PC", None)
        return
    age_h = (now_ts - int(rec.get("received_ts") or 0)) / 3600.0
    beat = rec["beat"]
    sn = beat.get("snapshot") or {}
    att = beat.get("attention") or []
    open_now = (8 <= now_ist.hour < (14 if now_ist.weekday() == 6 else 21))
    state = "green"
    words = ["heartbeat %.1f h ago" % age_h]
    if age_h > 3 and open_now:
        state = "red"
        words.append("the lab is open and the PC has been silent")
    elif age_h > 16:
        words.append("the PC is off (switched off evenings; that is the routine)")
    idx = _index_read()
    newest = max((v.get("received_ts") or 0 for v in idx.values()), default=0)
    if newest:
        snap_age = (now_ts - newest) / 3600.0
        words.append("last snapshot %.1f h ago (%d kept)" % (snap_age, len(idx)))
        if snap_age > 26 and state == "green":
            state = "amber"
    else:
        words.append("no snapshot kept yet")
        if state == "green":
            state = "amber"
    if att:
        words.append("; ".join(str(x) for x in att[:3]))
        if state == "green":
            state = "amber"
    add("labpc", "Lab PC", state, " | ".join(words), rec.get("received_ist"))
