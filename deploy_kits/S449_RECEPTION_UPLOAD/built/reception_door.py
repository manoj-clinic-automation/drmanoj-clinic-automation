#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reception_door.py -- kit S449_RECEPTION_UPLOAD (session 290, 02-Oct-2026, D659). PARENT. NEW.

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
"""
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
def read_beat():
    try:
        with open(BEAT_FILE, "r", encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec if isinstance(rec, dict) and isinstance(rec.get("beat"), dict) else None
    except (OSError, ValueError):
        return None


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
        ex = beat.get("docterz_exports") or {}
        dl = beat.get("downloads_folder") or {}
        today = (ex.get("consultation_today") or 0) + (dl.get("consultation_today") or 0)
        add(key, label, "ok", "heard %d minute(s) ago · Google Drive %s · consultation report today: %s"
            % (age_min, "running" if beat.get("google_drive_running") else "NOT running", "yes" if today else "not yet"))
    except Exception as ex:                                    # noqa: BLE001
        add(key, label, "info", "could not be read (%s)" % ex)
