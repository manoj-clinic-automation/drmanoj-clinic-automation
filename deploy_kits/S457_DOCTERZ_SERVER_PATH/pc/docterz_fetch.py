#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docterz_fetch.py -- S457. Runs ON THE OWNER'S PC (manojz), in front of docterz_pickup.py.

THE OWNER (03-Oct-2026): "also need the exports from reception pc docterz for this, server path
seems better than the google drive one."

WHY. Reception downloads two files from Docterz every evening: the consultation report and the
follow-up log. Since S449 the reception PC posts both straight to the clinic server. The tracker
that turns them into Day Revenue, the follow-up list and the Callback Tracker's follow-up list
still runs here and reads D:\\Downloads -- so a day reached the owner's portal only after someone
copied the two files across (F-697). This file fetches them from the server instead.

WHAT ONE PASS DOES (DOCTERZ_PICKUP.bat runs it every 5 minutes, just before the pickup):
  1. At most once every 10 minutes, asks the server which Docterz exports it currently holds from
     the last 3 days. The question is signed with this PC's own key (the one that signs jobs for
     the reception PC); the answer carries counts and dates only.
  2. For each export this PC does not already have -- compared by its md5 against the Docterz files
     in D:\\Downloads and against what this file fetched before -- downloads it, checks the md5 of
     what arrived, and saves it into D:\\Downloads as
         consultation_report_<day>_reception_<6 hex>.csv   /   followup_logs_<day>_reception_<6 hex>.csv
     with the time reception downloaded it as the file's own time. It is written under another
     name first and renamed, so the pickup never sees half a file.
  3. docterz_pickup.py, UNCHANGED, then finds it like any other download and decides what the
     tracker needs.

NEVER: raises (a failure is one line in the log and the pickup still runs); deletes, moves or
overwrites a file; prints a name or a mobile number (counts, dates, kinds and md5s only); sends
anything but its signed question. The manual way -- download in Chrome here, or copy the files
into D:\\Downloads -- is untouched and stays the fallback.

SWITCH: D:\\Downloads\\DocterzArchive\\_server_fetch_OFF.txt (or D:\\Downloads\\margsync\\_off\\ALL_OFF.txt).
A file that holds the single word ON counts as absent.

    python docterz_fetch.py              one pass
    python docterz_fetch.py --now        one pass without the 10-minute wait
    python docterz_fetch.py --dry-run    ask and compare; fetch and write nothing
    python docterz_fetch.py --selftest   offline checks; touches nothing
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

VERSION = "S457.1"

SERVER = os.environ.get("DOCTERZ_FETCH_SERVER", "https://followup.dr-manoj.in")
KEY_FILE = os.environ.get("DOCTERZ_FETCH_KEY", r"D:\Downloads\margsync\_config\reception_agent_key.txt")
DOWNLOADS = os.environ.get("DOCTERZ_FETCH_DOWNLOADS", r"D:\Downloads")
ARCHIVE = os.environ.get("DOCTERZ_FETCH_ARCHIVE", r"D:\Downloads\DocterzArchive")
ALL_OFF = os.environ.get("DOCTERZ_FETCH_ALL_OFF", r"D:\Downloads\margsync\_off\ALL_OFF.txt")

LIST_PATH = "/finance/api/reception/exports/list"
GET_PATH = "/finance/api/reception/exports/get"
LIST_CONTEXT = b"clinic-docterz-export-list-v1\n"      # the server's reception_door.py builds the same bytes
GET_CONTEXT = b"clinic-docterz-export-get-v1\n"
LIST_EVERY = 600             # seconds between questions to the server
DAYS = 3                     # how far back the question reaches
MAX_PER_PASS = 6             # exports fetched in one pass; the rest wait five minutes
MAX_BYTES = 5 * 1024 * 1024  # the server's own limit for one report
KEEP_DAYS = 60               # how long a fetched md5 is remembered
PREFIX = {"consultation": "consultation_report", "followup": "followup_logs"}
LOCAL_PREFIXES = ("consultation_report", "followup_logs")


def state_file():
    return os.path.join(ARCHIVE, "_server_fetch_state.json")


def log_file():
    return os.path.join(ARCHIVE, "_server_fetch_log.txt")


def last_file():
    return os.path.join(ARCHIVE, "_server_fetch_last.txt")


def off_files():
    return (os.path.join(ARCHIVE, "_server_fetch_OFF.txt"), ALL_OFF)


def now_ist():
    return _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None) + _dt.timedelta(hours=5, minutes=30)


# Ed25519 (RFC 8032), pure Python -- the same code, byte for byte, as reception_agent.py (S448) carries and its tests
# prove against the RFC's own vectors. No third-party package.
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


def is_off():
    for p in off_files():
        try:
            with open(p, "rb") as fh:
                word = fh.read(64)
        except OSError:
            continue
        for enc in ("utf-8-sig", "utf-16"):
            try:
                if word.decode(enc).strip().upper() == "ON":
                    break
            except UnicodeError:
                continue
        else:
            return True
    return False


def read_secret(path=None):
    """The 32-byte signing secret (64 hex on one line), or None. It never leaves this PC."""
    try:
        with open(path or KEY_FILE, "r", encoding="ascii") as fh:
            raw = bytes.fromhex(fh.read().strip())
        return raw if len(raw) == 32 else None
    except (OSError, ValueError, UnicodeError):
        return None


def load_state():
    try:
        with open(state_file(), "r", encoding="utf-8") as fh:
            st = json.load(fh)
        if not isinstance(st, dict) or not isinstance(st.get("have"), dict):
            raise ValueError("not a state")
    except (OSError, ValueError):
        st = {"have": {}}
    st.setdefault("listed_ts", 0)
    st.setdefault("last_status", "")
    return st


def save_state(st):
    cut = time.time() - KEEP_DAYS * 86400
    st["have"] = {k: v for k, v in st["have"].items() if isinstance(v, dict) and v.get("ts", 0) >= cut}
    tmp = state_file() + ".part"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1, sort_keys=True)
    os.replace(tmp, state_file())


def say(line, st=None, always=False):
    """One line to the log -- only when the words changed since the last pass, so an idle or an
    offline evening is one line, not a hundred."""
    words = line.split(" | ", 1)[-1]
    try:
        os.makedirs(ARCHIVE, exist_ok=True)
        with open(last_file(), "w", encoding="utf-8") as fh:
            fh.write("%s | %s | %s\n" % (now_ist().strftime("%Y-%m-%d %H:%M:%S"), VERSION, line))
        if always or st is None or st.get("last_status") != words:
            with open(log_file(), "a", encoding="utf-8") as fh:
                fh.write("%s | %s\n" % (now_ist().strftime("%Y-%m-%d %H:%M:%S"), line))
            print("docterz_fetch %s: %s" % (VERSION, line))
    except OSError:
        pass
    if st is not None:
        st["last_status"] = words


def http_post(path, obj, timeout=20):
    """(HTTP status, body bytes, headers dict). Network trouble is (0, the reason, {})."""
    data = json.dumps(obj).encode("utf-8")
    req = urllib.request.Request(SERVER.rstrip("/") + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "docterz_fetch/" + VERSION})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(MAX_BYTES + 1), dict(r.headers.items())
    except urllib.error.HTTPError as ex:
        try:
            body = ex.read(4096)
        except Exception:                                      # noqa: BLE001
            body = b""
        return ex.code, body, {}
    except Exception as ex:                                    # noqa: BLE001
        return 0, ("%s: %s" % (ex.__class__.__name__, ex)).encode("utf-8", "replace")[:200], {}


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def local_exports():
    """{size: [paths]} of the Docterz CSVs already in Downloads -- md5 is taken only on a size match."""
    out = {}
    try:
        names = os.listdir(DOWNLOADS)
    except OSError:
        return out
    for n in names:
        low = n.lower()
        if low.endswith(".csv") and low.startswith(LOCAL_PREFIXES):
            p = os.path.join(DOWNLOADS, n)
            try:
                out.setdefault(os.path.getsize(p), []).append(p)
            except OSError:
                pass
    return out


def already_here(md5, size, local):
    for p in local.get(size, []):
        try:
            if md5_of(p) == md5:
                return True
        except OSError:
            pass
    return False


def mtime_of(iso):
    """'2026-10-02T15:32:57.000Z' (UTC) as seconds, or None."""
    try:
        d = _dt.datetime.strptime(str(iso)[:19], "%Y-%m-%dT%H:%M:%S")
        return (d - _dt.datetime(1970, 1, 1)).total_seconds()
    except (ValueError, TypeError):
        return None


def file_name(kind, day, md5):
    day = day if (isinstance(day, str) and len(day) == 10 and day[4] == "-" and day[7] == "-"
                  and day.replace("-", "").isdigit()) else "nodate"
    return "%s_%s_reception_%s.csv" % (PREFIX[kind], day, md5[:6])


def one_pass(dry=False, now=False, post=None):
    """One pass. Returns the line it reported. Never raises."""
    post = post or http_post
    st = load_state()
    try:
        if is_off():
            say("OFF | switched off by a switch file -- nothing asked, nothing fetched", st)
            return _end(st, dry)
        if not now and time.time() - float(st.get("listed_ts") or 0) < LIST_EVERY:
            return "not due"
        secret = read_secret()
        if secret is None:
            say("NO KEY | this PC's signing key was not read -- nothing asked", st)
            return _end(st, dry)
        ts = str(int(time.time()))
        code, body, _h = post(LIST_PATH, {"ts": ts, "days": DAYS, "sig": ed_sign(secret, LIST_CONTEXT + ts.encode("ascii")).hex()})
        if code != 200:
            say("NOT ANSWERED | the server did not answer the list (%s%s)"
                % (code or "no connection", _reason(body)), st)
            return _end(st, dry)
        try:
            exports = json.loads(body.decode("utf-8"))["exports"]
            assert isinstance(exports, list)
        except Exception:                                      # noqa: BLE001
            say("NOT ANSWERED | the server's list could not be read", st)
            return _end(st, dry)
        st["listed_ts"] = time.time()
        local, here, fetched, would, bad, waiting = None, 0, 0, 0, 0, 0
        for e in sorted((x for x in exports if isinstance(x, dict)), key=lambda x: str(x.get("mtime") or "")):
            md5, kind = str(e.get("md5") or "").lower(), e.get("kind")
            if kind not in PREFIX or len(md5) != 32 or any(c not in "0123456789abcdef" for c in md5):
                continue
            if md5 in st["have"]:
                here += 1
                continue
            try:
                size = int(e.get("bytes") or 0)
            except (TypeError, ValueError):
                size = 0
            if local is None:
                local = local_exports()
            if already_here(md5, size, local):
                st["have"][md5] = {"ts": time.time(), "kind": kind, "day": e.get("day"), "how": "already in Downloads"}
                here += 1
                continue
            if dry:
                would += 1
                continue
            if fetched >= MAX_PER_PASS:
                waiting += 1
                continue
            ts = str(int(time.time()))
            sig = ed_sign(secret, GET_CONTEXT + md5.encode("ascii") + b"\n" + ts.encode("ascii")).hex()
            code, raw, _h = post(GET_PATH, {"md5": md5, "ts": ts, "sig": sig}, 60)
            if code != 200 or len(raw) > MAX_BYTES or hashlib.md5(raw).hexdigest() != md5:
                bad += 1
                say("NOT FETCHED | %s for %s (%s): %s" % (PREFIX[kind], e.get("day") or "?", md5[:8],
                    ("HTTP %s%s" % (code or "no connection", _reason(raw))) if code != 200 else "the bytes that arrived are not the export"),
                    always=True)
                continue
            name = file_name(kind, e.get("day"), md5)
            dst = os.path.join(DOWNLOADS, name)
            if os.path.exists(dst):                            # same day and md5 start: never overwrite
                st["have"][md5] = {"ts": time.time(), "kind": kind, "day": e.get("day"), "how": "a file of that name is already there"}
                here += 1
                continue
            tmp = os.path.join(DOWNLOADS, "_srvfetch_%s.part" % md5[:12])
            with open(tmp, "wb") as fh:
                fh.write(raw)
            mt = mtime_of(e.get("mtime"))
            if mt:
                os.utime(tmp, (mt, mt))
            os.replace(tmp, dst)
            st["have"][md5] = {"ts": time.time(), "kind": kind, "day": e.get("day"), "how": "fetched", "name": name}
            fetched += 1
            say("FETCHED | %s for %s, %d bytes, md5 %s -> %s" % (PREFIX[kind], e.get("day") or "?", len(raw), md5[:8], name), always=True)
        if dry:
            say("DRY RUN | the server holds %d current export(s) of the last %d days: %d already here, %d would be fetched"
                % (here + would, DAYS, here, would), always=True)
        else:
            say("ok | the server holds %d current export(s) of the last %d days: %d already here, %d fetched now%s%s"
                % (here + fetched + bad + waiting, DAYS, here, fetched,
                   (", %d NOT fetched" % bad) if bad else "", (", %d waiting for the next pass" % waiting) if waiting else ""), st)
    except Exception as ex:                                    # noqa: BLE001
        say("ERROR | %s: %s" % (ex.__class__.__name__, str(ex)[:160]), st)
    return _end(st, dry)


def _reason(body):
    try:
        j = json.loads(body.decode("utf-8"))
        return " %s" % j.get("status") if isinstance(j, dict) and j.get("status") else ""
    except Exception:                                          # noqa: BLE001
        return ""


def _end(st, dry):
    if not dry:
        try:
            os.makedirs(ARCHIVE, exist_ok=True)
            save_state(st)
        except OSError:
            pass
    return st.get("last_status", "")


def selftest():
    ok = []

    def check(name, cond):
        ok.append(bool(cond))
        print("%s  %s" % ("ok  " if cond else "FAIL", name))
    vec = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    pub = ed_public(vec)
    check("Ed25519: the RFC 8032 vector's public key", pub.hex() == "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    check("Ed25519: the RFC 8032 vector's signature", ed_sign(vec, b"").hex().startswith("e5564300c360ac729086e2cc806e828a"))
    check("Ed25519: a signature verifies, a changed message does not",
          ed_verify(pub, b"x", ed_sign(vec, b"x")) and not ed_verify(pub, b"y", ed_sign(vec, b"x")))
    check("file names", file_name("consultation", "2026-10-02", "ab" * 16) == "consultation_report_2026-10-02_reception_ababab.csv"
          and file_name("followup", "../x", "cd" * 16) == "followup_logs_nodate_reception_cdcdcd.csv")
    check("a fetched name is one the pickup looks at", file_name("followup", "2026-10-02", "0" * 32).startswith(LOCAL_PREFIXES))
    check("the server's time is read as UTC", mtime_of("2026-10-02T15:32:57.000Z") == 1790955177.0 and mtime_of("nonsense") is None)
    print("%d passed, %d failed" % (sum(ok), len(ok) - sum(ok)))
    return 0 if all(ok) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fetch reception's Docterz exports from the clinic server into Downloads.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    try:
        one_pass(dry=a.dry_run, now=a.now or a.dry_run)
    except Exception as ex:                                    # noqa: BLE001 -- the pickup must still run
        print("docterz_fetch: %s: %s" % (ex.__class__.__name__, ex))
    return 0


if __name__ == "__main__":
    sys.exit(main())
