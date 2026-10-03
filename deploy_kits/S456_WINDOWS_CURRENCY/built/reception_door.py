#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reception_door.py -- kit S449_RECEPTION_UPLOAD (session 290, 02-Oct-2026, D659). PARENT. S453: the job relay, below.

THE OWNER, 02-Oct-2026: "One is direct upload from the reception PC to server."

Until today everything the reception PC sends -- its heartbeat and the two Docterz reports -- travelled through Google
Drive for desktop on that PC. On 01-Oct Drive stopped starting there and nothing said so: a stale heartbeat cannot say
"Drive is down" when Drive is what carries it. This is the second road, the same shape as the medical PC's
/finance/api/marg-file (marg_door.py, S240): the reception agent posts straight to this server over HTTPS.

  POST /finance/api/reception/heartbeat    the agent's heartbeat (COUNTS AND DATES ONLY -- the agent's own rule)
  POST /finance/api/reception/report       one Docterz export; answers TAKEN / ALREADY / REFUSED

NO SHARED SECRET TRAVELS. Each request is signed with an Ed25519 key that was made ON the reception PC and never leaves
it; this server holds only the PUBLIC key (reception_keys.txt, beside this file, in the repository kit). What is signed:
a fixed context, the kind, the sender's clock, the file's name and time, and the SHA-256 of the body. A request more than
15 minutes from this server's clock is refused, so a copied request cannot be replayed later. A report is identified BY
ITS CONTENT by docterz_pickup.identify() and taken through docterz_pickup.take() -- THE SAME DOOR the Drive pickup uses
(S443), so a report that arrives by both roads is counted once: the second is 'duplicate' / ALREADY. Anything that is
not one of the two reports is refused and nothing of it is kept.

The two paths are in finance_app's PUBLIC_PATHS (like the phone doors of S290 and S407): the gate lets them reach this
handler and THIS HANDLER authenticates. With no key file the door answers 503 and takes nothing (fail closed).

THE HEALTH PAGE: health_row() gives /finance/health one row, "Reception PC". The age is measured on THIS server's clock
from when the heartbeat ARRIVED -- a value that stopped being written is a memory, not a reading (B2C, S202).

Stdlib + Flask. Creates no table of its own (docterz_export is docterz_pickup's). Sends nothing anywhere.

S453 (02-Oct-2026, D661) -- THE SECOND JOB DOOR. The reception agent runs jobs that reach it through Google Drive, and
Google Drive is what failed on that PC on 01-Oct. This server now RELAYS jobs, and only relays them:

  POST /finance/api/reception/jobs/submit   a job enters the queue ONLY with the Ed25519 signature of a key listed in
                                            reception_job_keys.txt (PUBLIC keys; the secret never leaves the owner's PC)
  POST /finance/api/reception/jobs/next     the PC asks for the next job (signed with ITS key, like its heartbeat)
  POST /finance/api/reception/jobs/ack      the PC says it took the job, or why it refused it
  POST /finance/api/reception/jobs/result   the PC posts the job's output
  POST /finance/api/reception/jobs/read     the sender reads the state and the output -- each read signed with the
                                            same key that signs jobs, good for 15 minutes

The PC verifies the job's signature AGAIN with its own authorized_keys.txt before it runs anything, so this server --
or anyone who took it over, or anyone holding a clinic login -- cannot make that PC run a job. The server holds no job
secret; a job and its output carry no patient name (the agent's own rule). Nothing here needs a login: every request
proves itself. Queue: reception_jobs/ beside this file (mode 700), pruned after 14 days.
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

from flask import Blueprint, jsonify, request

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.environ.get("RECEPTION_KEYS", os.path.join(HERE, "reception_keys.txt"))
BEAT_FILE = os.environ.get("RECEPTION_BEAT", os.path.join(HERE, "reception_heartbeat.json"))
SIG_CONTEXT = b"clinic-reception-upload-v1\n"
MAX_BEAT = 64 * 1024
MAX_REPORT = 5 * 1024 * 1024
MAX_SKEW = 900                  # seconds either side of this server's clock
RATE_PER_MIN = 60               # one PC: a heartbeat every 5 minutes and a few files a day
NAME_RE = re.compile(r"^[A-Za-z0-9 ._()\-]{0,120}$")
# S453 -- the job relay
JOB_KEYS_FILE = os.environ.get("RECEPTION_JOB_KEYS", os.path.join(HERE, "reception_job_keys.txt"))
JOB_DIR = os.environ.get("RECEPTION_JOB_DIR", os.path.join(HERE, "reception_jobs"))
JOB_CONTEXT = b"clinic-reception-job-v1\n"            # exactly what reception_sign.py signs: context, name, bytes
JOB_READ_CONTEXT = b"clinic-reception-job-read-v1\n"
JOB_NAME_RE = re.compile(r"^(\d{8})T(\d{6})_[A-Za-z0-9][A-Za-z0-9._-]{0,90}\.(?:ps1|cmd|bat|py)$")
MAX_JOB = 256 * 1024
MAX_RESULT = 1024 * 1024
JOB_MAX_AGE_HOURS = 48          # the agent's own rule; a job it would refuse is not queued
JOB_MAX_AHEAD_HOURS = 2
JOB_KEEP_DAYS = 14
JOB_WAITING_MAX = 20

bp = Blueprint("reception_door", __name__)
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
    """Exactly what the reception agent signs (its own function of the same name builds the same bytes)."""
    return (SIG_CONTEXT + kind.encode("ascii") + b"\n" + str(ts).encode("ascii") + b"\n" + name.encode("utf-8") + b"\n"
            + str(mtime).encode("ascii") + b"\n" + hashlib.sha256(body).hexdigest().encode("ascii"))


def enrolled_keys():
    """[(32 raw bytes, label)] from reception_keys.txt; [] shuts the door."""
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
        return None, None, None, None, _no("NO_KEY", "no reception key is enrolled on this server -- nothing taken", 503)
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
    label = next((lab or "reception" for k, lab in keys if ed_verify(k, msg, sig)), None)
    if label is None:
        return None, None, None, None, _no("NOT_YOU", "the signature does not match an enrolled key", 401)
    skew = int(time.time()) - int(ts)
    if abs(skew) > MAX_SKEW:
        return None, None, None, None, _no("CLOCK", "the sender's clock is %d seconds from this server's; nothing taken"
                                           % (-skew), 401, server_time=int(time.time()))
    return label, body, name, mtime, None


def _ist_now():
    return dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)


@bp.route("/finance/api/reception/heartbeat", methods=["POST"])
def api_reception_heartbeat():
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
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
        os.chmod(tmp, 0o600)
        os.replace(tmp, BEAT_FILE)
    except OSError as ex:
        return _no("NOT_KEPT", "could not write the heartbeat: %s" % str(ex)[:120], 500)
    return jsonify(ok=True, status="KEPT", server_time=rec["received_ts"]), 200


@bp.route("/finance/api/reception/report", methods=["POST"])
def api_reception_report():
    label, body, name, mtime, err = _signed("report", MAX_REPORT)
    if err:
        return err
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import docterz_pickup as DP                              # noqa: PLC0415 -- S443; the one door for these exports
    except Exception as ex:                                    # noqa: BLE001
        return _no("NOT_READY", "the Docterz reader is not installed here: %s" % str(ex)[:120], 503)
    kind, day, nrows, note = DP.identify(body)
    if kind == "unknown":
        return _no("REFUSED", "not one of the two Docterz reports -- nothing kept", 400)
    md5 = hashlib.md5(body).hexdigest()
    con = _db()
    DP.ensure(con)
    seen = con.execute("SELECT status, business_date FROM docterz_export WHERE md5=? AND kind=? AND status<>'unknown' "
                       "ORDER BY id DESC LIMIT 1", (md5, kind)).fetchone()
    if seen is not None:
        return jsonify(ok=True, status="ALREADY", kind=kind, day=seen["business_date"], rows=nrows, verdict=seen["status"],
                       message="already here -- nothing was counted twice"), 200
    try:
        mt = dt.datetime.utcfromtimestamp(int(mtime)) if mtime else dt.datetime.utcnow()
    except (ValueError, OverflowError, OSError):
        mt = dt.datetime.utcnow()
    f = {"id": "reception:" + md5, "name": name, "modifiedTime": mt.strftime("%Y-%m-%dT%H:%M:%S.000Z")}
    kind, day, nrows, st, note = DP.take(con, f, body)
    return jsonify(ok=True, status="TAKEN", kind=kind, day=day, rows=nrows, verdict=st, note=note,
                   message="taken -- %s for %s, %d rows, %s" % (DP.KINDS.get(kind, kind), day or "?", nrows, st)), 200


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


@bp.route("/finance/api/reception/jobs/submit", methods=["POST"])
def api_reception_job_submit():
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


@bp.route("/finance/api/reception/jobs/next", methods=["POST"])
def api_reception_job_next():
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


@bp.route("/finance/api/reception/jobs/ack", methods=["POST"])
def api_reception_job_ack():
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


@bp.route("/finance/api/reception/jobs/result", methods=["POST"])
def api_reception_job_result():
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


@bp.route("/finance/api/reception/jobs/read", methods=["POST"])
def api_reception_job_read():
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


# ---- S456: BOTH Docterz reports, by name (the owner, 03-Oct-2026: "you have only mentioned the consultation report") --
# Reception downloads two files from Docterz every evening: the consultation report (Day Revenue is built from it) and
# the follow-up log (the follow-up tracker and the Callback Tracker's follow-up list are built from it). The row used to
# name only the first, and the second went undownloaded from 7 July to 2 October without a word here. It now names
# both with the time each was last downloaded, and turns amber when a clinic evening was missed for either.
_REPORTS = (("consultation", "consultation report"), ("followup", "follow-up log"))


def reports_note(beat, today, sunday_open, missed_allowed):
    """(words, [names that are late]). The newest of each report across the PC's two folders; late = at least
    missed_allowed clinic evenings (Sundays skipped unless the clinic opens on Sunday) have passed without it.
    Never raises."""
    try:
        parts, late = [], []
        for kind, name in _REPORTS:
            newest = None
            for folder in ("docterz_exports", "downloads_folder"):
                f = beat.get(folder)
                v = str((f.get(kind + "_newest") if isinstance(f, dict) else "") or "")
                try:
                    d = dt.datetime.fromisoformat(v[:19])
                except ValueError:
                    continue
                if newest is None or d > newest:
                    newest = d
            if newest is None:
                parts.append("%s: NOT SEEN on this PC" % name)
                late.append(name)
                continue
            missed, day = 0, newest.date() + dt.timedelta(days=1)
            while day < today and missed < 400:
                if day.weekday() != 6 or sunday_open:
                    missed += 1
                day += dt.timedelta(days=1)
            if missed >= max(1, missed_allowed):
                late.append(name)
                parts.append("%s: NOT downloaded since %s" % (name, newest.strftime("%d-%b %H:%M")))
            else:
                parts.append("%s: %s" % (name, newest.strftime("%d-%b %H:%M")))
        return "Docterz reports — " + " · ".join(parts), late
    except Exception:                                          # noqa: BLE001
        return "", []


# ---- S456 (F-700): how current that PC's Windows is, in the PC's own words -------------------------------------------
# The agent (S456.1 and later) puts a small reading in its heartbeat: product, release, build, the date of the system
# files and the day the last cumulative update was installed. An older agent sends none, and this row then reads
# exactly as before. The health page prints these words, so only plain characters pass.
_WIN_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _plain(v, n):
    """Letters, digits, spaces, dots and dashes only."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 .\-]", "", str(v if v is not None else ""))).strip()[:n]


def windows_note(beat, stale_days, today):
    """(words, stale, since, build) about that PC's Windows. words is '' when the heartbeat carries no reading.
    stale = no cumulative update within stale_days, judged by the NEWER of the day the last one was installed and the
    date of the system files. Never raises."""
    try:
        w = beat.get("windows")
        if not isinstance(w, dict):
            return "", False, "", ""
        name = " ".join(x for x in (_plain(w.get("product"), 40), _plain(w.get("release"), 8)) if x) or "Windows"
        build = _plain(w.get("build"), 16)
        days = []
        for k in ("update_installed", "system_files_dated"):
            v = str(w.get(k) or "")
            if _WIN_DAY.match(v):
                try:
                    days.append(dt.date.fromisoformat(v))
                except ValueError:
                    pass
        if not days:
            return "%s: the date of its last Windows update could not be read" % name, False, "", build
        newest = max(days)
        if (today - newest).days > stale_days:
            return ("%s: no Windows update since %s" % (name, newest.strftime("%b %Y")), True,
                    newest.strftime("%d-%b-%Y"), build)
        return "%s, last updated %s" % (name, newest.strftime("%b %Y")), False, "", build
    except Exception:                                          # noqa: BLE001
        return "", False, "", ""


def health_row(add, setting, con, now_ts=None, now_ist=None):
    """One row on /finance/health. Never raises."""
    key, label = "reception", "Reception PC"
    try:
        def _i(k, d):
            try:
                return int(str(setting(con, k, str(d)) or d).strip())
            except (TypeError, ValueError):
                return d
        h_from, h_to = _i("reception.clinic_hour_from", 10), _i("reception.clinic_hour_to", 20)
        warn_min, bad_min = _i("reception.stale_warn_min", 15), _i("reception.stale_bad_min", 45)
        sunday = str(setting(con, "pipeline.clinic_sunday", "0") or "0").strip() == "1"
        ist = now_ist or _ist_now()
        in_hours = (h_from <= ist.hour < h_to) and (ist.weekday() != 6 or sunday)
        rec = read_beat()
        if rec is None:
            add(key, label, "info", "no heartbeat has reached the server directly yet",
                "The reception agent posts one every 5 minutes once its direct upload is on (S449). "
                "Its Drive heartbeat is separate: Clinic Data Archive / FromReception.")
            return
        age_min = ((now_ts or time.time()) - float(rec.get("received_ts") or 0)) / 60.0
        beat = rec["beat"]
        if age_min > warn_min:
            if in_hours:
                add(key, label, "bad" if age_min > bad_min else "warn",
                    "last heard from the reception PC %d minutes ago -- DURING THE CLINIC DAY" % age_min,
                    "It reports every 5 minutes while someone is logged in. Check the PC is on and logged in; if it is, "
                    "its internet or the agent has stopped (C:\\ClinicAgent\\heartbeat.txt on that PC says which).")
            else:
                add(key, label, "info", "last heard from the reception PC %s ago -- out of hours"
                    % ("%d minutes" % age_min if age_min < 120 else "%.0f hours" % (age_min / 60.0)),
                    "Normal when the PC is off. During the clinic day this row goes red.")
            return
        att = [str(a)[:160] for a in (beat.get("attention") or []) if a][:3]
        if att:
            add(key, label, "warn", "the reception PC reports: %s" % "; ".join(att),
                "Its own words, from its heartbeat %d minute(s) ago. The agent repairs what it can by itself." % age_min)
            return
        words = "heard %d minute(s) ago · Google Drive %s" % (
            age_min, "running" if beat.get("google_drive_running") else "NOT running")
        rwords, late = reports_note(beat, ist.date(), sunday, _i("reception.report_missed_evenings", 1))
        if rwords:
            words += " · " + rwords
        if late:                                               # S456: a missed evening is said the next morning
            add(key, label, "warn", words,
                "Not downloaded on the last clinic evening: the %s. Reception downloads BOTH from Docterz every "
                "evening into Clinic Records / Docterz exports. The follow-up tracker and the Callback Tracker's "
                "follow-up list are built from the follow-up log, Day Revenue from the consultation report. "
                "(A day the clinic was closed shows here once and clears with the next download.)" % " and the ".join(late))
            return
        wn, stale, since, build = windows_note(beat, _i("reception.windows_stale_days", 75), ist.date())
        if stale:                                              # S456: said, never chased -- "info" is not a problem
            add(key, label, "info", words + " · " + wn,
                "Windows on this PC%s has had no cumulative update since %s. Nothing is broken and nothing here needs "
                "doing today; it is a decision for you -- extended updates, or a new PC, which sets up from the "
                "Clinic PCs tile. Everything else on this row is normal." % ((" (build %s)" % build) if build else "", since))
        else:
            add(key, label, "ok", words + ((" · " + wn) if wn else ""))
    except Exception as ex:                                    # noqa: BLE001
        add(key, label, "info", "could not be read (%s)" % ex)
