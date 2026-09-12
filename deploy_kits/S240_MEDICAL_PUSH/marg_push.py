#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
marg_push.py  --  S240 (D467 phase 2b).  Runs ON THE MEDICAL PC.

WHAT IT DOES
    Every Marg export the watcher captures into D:\SendToClinic\_captured is sent to the clinic
    server, by itself, within a minute -- and the server answers what the report was and whether
    it verified. Until now every report waited for Dr Manoj's PC to pull it over Tailscale.

WHAT IT IS CAREFUL ABOUT -- this machine's one job is capture, and nothing here may risk it
    * It NEVER deletes, moves or rewrites a captured file. The spool stays the edge's own archive.
    * It is bounded: a few files and a few tens of seconds per pass, then it stops until the next.
    * Every failure is survivable. No network, server down, wrong key, bad certificate: the file
      simply stays unsent and is tried again. Nothing is lost, because nothing is thrown away.
    * It holds no secret of its own. It reads D:\SendToClinic\token.txt -- the scoped, stage-only
      key this machine already has, which can stage a report and do nothing else.
    * It runs as a daemon THREAD inside the watcher, so if it dies, capture does not.

THE NAME IT SENDS
    The spool name is  <stamp>__<slot>__<md5-8>.XLS  and the stamp is the moment of capture.
    Our stock rules turn on WHEN a report was taken, so the name must carry it in the shape the
    server reads (`__YYYYmmdd-HHMMSS__`). It is therefore sent as:
        MEDICAL__<stamp>__<slot>__<md5-8>.XLS

WHAT THE SERVER ANSWERS
    TAKEN    new -- classified, verified, recorded
    ALREADY  it already holds these exact bytes (it de-duplicates by content, so sending twice,
             or sending what Dr Manoj's PC already sent, costs nothing and doubles nothing)
    REFUSED  it will not take these bytes, and says why
    BUSY     it was collecting just then; try again shortly

    /path/to/python.exe marg_push.py --once        one pass, then exit
    /path/to/python.exe marg_push.py --probe       "are you there?" and what is held
    /path/to/python.exe marg_push.py --selftest    no network: the parts that can be proved offline
"""
import argparse
import hashlib
import json
import os
import random
import ssl
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = os.environ.get("MARG_PUSH_URL", "https://followup.dr-manoj.in/finance/api/marg-file")
TOKEN_FILE = os.path.join(HERE, "token.txt")
SPOOL = os.path.join(HERE, "_captured")
STATE = os.path.join(HERE, "push_state.json")
LOG = os.path.join(HERE, "push.log")
LOG_MAX = 256 * 1024

EXTS = (".xls", ".xlsx", ".pdf")
PER_PASS = 8                 # files in one pass -- a backlog drains over several, never in a burst
PASS_SECONDS = 45            # and never for longer than this
EVERY = 60                   # seconds between passes in the thread
TIMEOUT = 90
MAX_TRIES = 4                # after this many REAL refusals a file is left alone and named instead
# A refusal is only a refusal when the server looked at the bytes and would not have them. A bad
# key, a server restarting, a dead line: those are OUR problem or a passing one, and a file must
# never be abandoned for them -- it is retried for ever. Getting this wrong is how a report gets
# quietly dropped after four bad minutes.
TRANSIENT = (0, 401, 403, 408, 425, 429, 500, 502, 503, 504)
MAX_BYTES = 25 * 1024 * 1024


# ------------------------------------------------------------------ small helpers
def log(msg):
    line = "%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > LOG_MAX:
            with open(LOG, "r", encoding="utf-8", errors="replace") as fh:
                keep = fh.read()[-LOG_MAX // 2:]
            with open(LOG, "w", encoding="utf-8") as fh:
                fh.write(keep)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def token():
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8-sig", errors="replace") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def state_read():
    try:
        with open(STATE, "r", encoding="utf-8") as fh:
            s = json.load(fh)
    except (OSError, ValueError):
        s = {}
    s.setdefault("sent", {})
    s.setdefault("tries", {})
    s.setdefault("last", {})
    return s


def state_write(s):
    """Written through a temp file: a half-written state must never be read as the whole truth."""
    tmp = STATE + ".part"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(s, fh)
        if os.path.exists(STATE):
            os.remove(STATE)
        os.rename(tmp, STATE)
    except OSError:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass


def server_name(spool_name):
    r"""<stamp>__<slot>__<md5-8>.XLS  ->  MEDICAL__<stamp>__<slot>__<md5-8>.XLS

    The prefix is not decoration: the server reads the capture moment out of `__<stamp>__`, and
    without something before it the stamp is at the very start of the name and is not seen."""
    base = str(spool_name).replace("\\", "/").rstrip("/").split("/")[-1]
    return base if base.startswith("MEDICAL__") else "MEDICAL__" + base


# ------------------------------------------------------------------ the wire
def _ctx():
    return ssl.create_default_context()


def _post(path, tok):
    """One file, as multipart/form-data, built by hand -- this machine has the standard library
    and nothing else, by design."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if not raw or len(raw) > MAX_BYTES:
        return 0, {"status": "REFUSED", "message": "empty or too big to send"}
    name = server_name(path)
    digest = hashlib.md5(raw).hexdigest()
    bnd = "----margpush%s%s" % (int(time.time()), random.randint(1000, 9999))
    parts = []
    for key, val in (("name", name), ("md5", digest), ("source", "push")):
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                      % (bnd, key, val)).encode("utf-8"))
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"f\"; filename=\"%s\"\r\n"
                  "Content-Type: application/octet-stream\r\n\r\n" % (bnd, name)).encode("utf-8"))
    parts.append(raw)
    parts.append(("\r\n--%s--\r\n" % bnd).encode("utf-8"))
    body = b"".join(parts)
    req = urllib.request.Request(URL, data=body, method="POST")
    req.add_header("Content-Type", "multipart/form-data; boundary=%s" % bnd)
    req.add_header("X-Finance-Marg", tok)
    req.add_header("Content-Length", str(len(body)))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ctx()) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace") or "{}")
        except (ValueError, OSError):
            return e.code, {"status": "REFUSED", "message": "HTTP %s" % e.code}
    except Exception as e:                                     # noqa: BLE001
        return 0, {"status": "NO_REACH", "message": "%s: %s" % (e.__class__.__name__, str(e)[:120])}


def probe(tok=None):
    tok = tok if tok is not None else token()
    if not tok:
        return 0, {"status": "NO_KEY", "message": "token.txt is missing or empty"}
    req = urllib.request.Request(URL, method="GET")
    req.add_header("X-Finance-Marg", tok)
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ctx()) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {"status": "HTTP_%s" % e.code}
    except Exception as e:                                     # noqa: BLE001
        return 0, {"status": "NO_REACH", "message": "%s: %s" % (e.__class__.__name__, str(e)[:120])}


# ------------------------------------------------------------------ one pass
def pending(spool, s):
    """Oldest capture first: the server's own memory of the stock universe depends on the order
    it sees days in, and the oldest unsent file is also the one most likely to be missed."""
    out = []
    try:
        names = sorted(os.listdir(spool))
    except OSError:
        return out
    for n in names:
        if not n.lower().endswith(EXTS):
            continue
        p = os.path.join(spool, n)
        if not os.path.isfile(p):
            continue
        try:
            key = md5_of(p)
        except OSError:
            continue
        if key in s["sent"]:
            continue
        if s["tries"].get(key, 0) >= MAX_TRIES:
            continue
        out.append((n, p, key))
    return out


def run_once(spool=SPOOL, out=None, limit=PER_PASS):
    say = out or (lambda m: None)
    s = state_read()
    tok = token()
    if not tok:
        s["last"] = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"), "note": "no key in token.txt"}
        state_write(s)
        return 0, 0, 0
    todo = pending(spool, s)
    started = time.time()
    took = already = failed = 0
    for n, p, key in todo[:limit]:
        if time.time() - started > PASS_SECONDS:
            break
        code, ans = _post(p, tok)
        st = str(ans.get("status") or "")
        if code == 200 and st in ("TAKEN", "ALREADY"):
            s["sent"][key] = {"name": n, "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
                              "status": st, "type": ans.get("type", ""),
                              "verdict": ans.get("verdict", ""), "lines": ans.get("lines", 0)}
            s["tries"].pop(key, None)
            took += 1 if st == "TAKEN" else 0
            already += 1 if st == "ALREADY" else 0
            what = ans.get("type") or "not recognised"
            say("  %s %s -> %s %s" % (st, n[:44], what, ans.get("verdict", "")))
            log("%s %s %s %s" % (st, n, ans.get("type", ""), ans.get("verdict", "")))
        elif st == "BUSY" or code in TRANSIENT:
            failed += 1
            why = ans.get("message") or ans.get("error") or st or ("HTTP %s" % code)
            say("  later  %s (%s)" % (n[:44], why))
            log("later %s %s %s" % (n, code, str(why)[:120]))
            break                        # the server, the key or the line is unwell: next pass
        else:
            s["tries"][key] = s["tries"].get(key, 0) + 1
            failed += 1
            why = ans.get("message") or ans.get("error") or st or ("HTTP %s" % code)
            say("  refused %s (%s)" % (n[:44], why))
            log("refused %s %s %s try %d" % (n, code, str(why)[:120], s["tries"][key]))
    waiting = max(0, len(todo) - took - already)
    s["last"] = {"when": time.strftime("%Y-%m-%dT%H:%M:%S"), "taken": took, "already": already,
                 "failed": failed, "waiting": waiting, "sent_total": len(s["sent"])}
    state_write(s)
    return took, already, failed


def loop(spool=SPOOL, out=None, every=EVERY, stop=None, wake=None):
    """The daemon thread. It must never be able to take the watcher down with it.

    `wake` is set by the watcher the moment it captures something, so a report reaches the server
    in seconds rather than waiting out the next pass -- which is the whole point of the exercise.
    Without it (or if it is never set) the pass still comes round every `every` seconds, so the
    signal is an accelerator and never a dependency."""
    say = out or (lambda m: None)
    say("  pusher: on -- on every capture, and every %ds anyway" % every)
    log("pusher started")
    time.sleep(5)                        # let capture settle after a restart before any network
    while True:
        if stop is not None and stop.is_set():
            return
        try:
            run_once(spool, say)
        except Exception as e:           # noqa: BLE001  -- a pusher fault is never a capture fault
            log("pass failed: %s: %s" % (e.__class__.__name__, str(e)[:160]))
        if wake is not None:
            wake.wait(every)             # a capture, or the timeout, whichever comes first
            wake.clear()
            time.sleep(2)                # let a burst of exports land together
        else:
            for _ in range(int(every)):
                if stop is not None and stop.is_set():
                    return
                time.sleep(1)


def human(spool=SPOOL):
    """One line for the heartbeat, so the shop can see this working without opening anything."""
    s = state_read()
    last = s.get("last") or {}
    left = len(pending(spool, s))
    if not last:
        return "PUSH    : nothing sent yet"
    stuck = sum(1 for k, v in s.get("tries", {}).items() if v >= MAX_TRIES)
    bits = ["%d sent in all" % len(s.get("sent", {})), "%d waiting" % left]
    if stuck:
        bits.append("%d the server would not take" % stuck)
    if last.get("note"):
        bits.append(last["note"])
    return "PUSH    : %s  (last pass %s)" % (", ".join(bits), last.get("when", "?"))


# ------------------------------------------------------------------ offline proof
def selftest():
    ok = bad = 0

    def ck(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  ok    %s" % name)
        else:
            bad += 1
            print("  FAIL  %s" % name)

    ck("the capture moment survives the rename",
       server_name(r"D:\x\20260911-221844__REPORT_2__02cca7ee.XLS")
       == "MEDICAL__20260911-221844__REPORT_2__02cca7ee.XLS")
    ck("renaming twice does not double the prefix",
       server_name("MEDICAL__20260911-221844__REPORT_2__02cca7ee.XLS")
       == "MEDICAL__20260911-221844__REPORT_2__02cca7ee.XLS")
    import re
    ck("the server's stamp pattern matches the name we send",
       bool(re.search(r"__(\d{8}-\d{6})__", server_name("20260911-221844__R__ab.XLS"))))
    import tempfile
    d = tempfile.mkdtemp()
    open(os.path.join(d, "20260101-000000__A__aa.XLS"), "wb").write(b"\xd0\xcf\x11\xe0hello")
    open(os.path.join(d, "notes.txt"), "wb").write(b"x")
    s = {"sent": {}, "tries": {}, "last": {}}
    p = pending(d, s)
    ck("only Marg exports are picked up", len(p) == 1 and p[0][0].endswith(".XLS"))
    s["sent"][p[0][2]] = {"status": "TAKEN"}
    ck("a file already accepted is not sent again", len(pending(d, s)) == 0)
    s2 = {"sent": {}, "tries": {p[0][2]: MAX_TRIES}, "last": {}}
    ck("a file the server keeps refusing is left alone, not hammered", len(pending(d, s2)) == 0)
    ck("a missing key is survivable, not an error", isinstance(token(), str))
    print("\n%d ok, %d failed" % (ok, bad))
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="push captured Marg exports to the clinic server")
    ap.add_argument("--spool", default=SPOOL)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=PER_PASS)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.probe:
        code, ans = probe()
        print("%s  %s" % (code, json.dumps(ans)[:300]))
        return 0 if code == 200 else 1
    took, already, failed = run_once(a.spool, lambda m: (print(m), sys.stdout.flush()), a.limit)
    print(human(a.spool))
    return 1 if (failed and not (took or already)) else 0


if __name__ == "__main__":
    sys.exit(main())
