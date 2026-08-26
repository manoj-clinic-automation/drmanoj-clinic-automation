#!/usr/bin/env python3
"""
pipeline_status.py  ·  B2 (S202)  ·  runs on manojz at the end of every pull

WHY THIS EXISTS
---------------
Every health check on the clinic server watches ARRIVAL AT THE VPS. Four of the
seven ways the Marg chain can fail happen entirely on the owner's machines:

    the medical watcher dies · the 10-minute pull stops running ·
    the outbox stops draining · the Drive offsite silently stops

None of them is visible from the server. F-179 is the proof: eleven verified
reports sat undelivered for three days while capture, routing and archiving all
reported success, and the only symptom the owner could see was a page that
stayed empty.

So this posts what manojz CAN see, once per pull. It is a reporter: it reads,
it posts, and it changes nothing.

RULES IT KEEPS
  * it NEVER fails the pull -- every section is independently guarded and a
    failure here must never stop reports being sent (that would be a monitor
    taking down the thing it monitors)
  * it NEVER prints or logs the token, and reuses marg_gate's own resolution
    rather than keeping a second copy of that rule (D349)
  * it reuses FINANCE_MARG_TOKEN -- no fourth secret to rotate, when rotation
    is already the oldest open item in the project

    python pipeline_status.py            # gather and post
    python pipeline_status.py --dry-run  # gather and PRINT, post nothing
    python pipeline_status.py --selftest # prove the gathering offline
"""
import argparse
import datetime
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEF_ARCHIVE   = r"D:\Downloads\margsync\MargArchive"
DEF_LASTPULL  = r"D:\Downloads\margsync\MargPull\_last_pull.txt"
DEF_HEARTBEAT = r"H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt"
DEF_OFFSITE   = r"H:\My Drive\Clinic Data Archive\MargArchive"
DEF_URL       = "https://followup.dr-manoj.in/finance/api/pipeline-status"
DEF_TOKEN     = r"D:\Downloads\margsync\SendToClinic\token.txt"
DEF_TOKEN_UNC = r"\\100.119.151.40\DDrive\SendToClinic\token.txt"


def _hours_since(ts):
    try:
        return round((datetime.datetime.now() - ts).total_seconds() / 3600.0, 1)
    except Exception:
        return None


def outbox_state(archive):
    """How many reports are queued AND NOT YET DELIVERED, and how old the oldest
    of those is. THIS is the number F-179 needed and nobody was reading: assert
    the DRAIN, not the enqueue.

    CAUGHT BY RUNNING IT AGAINST REAL DATA, not by reasoning: the first version
    counted FILES in _outbox and reported 10 waiting, oldest 192.8 hours. But
    delivered files are deliberately KEPT there (the pipeline reference says so
    in as many words), so that check would have gone red on day one and stayed
    red forever. A false alarm is worse than no alarm -- it teaches the owner to
    ignore the light.

    marg_gate records what it has delivered in _outbox_state.json, keyed by
    content hash. That is the authority, so this reads it rather than keeping a
    second opinion about what "delivered" means (D349).
    """
    d = os.path.join(archive, "_outbox")
    try:
        files = [os.path.join(d, f) for f in os.listdir(d)
                 if os.path.isfile(os.path.join(d, f)) and not f.startswith("_")]
    except Exception:
        return {}
    sent = set()
    try:
        with io.open(os.path.join(archive, "_outbox_state.json"),
                     "r", encoding="utf-8-sig", errors="replace") as fh:
            sent = set((json.load(fh) or {}).get("sent") or {})
    except Exception:
        sent = set()
    import hashlib
    pending = []
    for f in files:
        try:
            with open(f, "rb") as fh:
                h = hashlib.md5(fh.read()).hexdigest()
        except Exception:
            continue
        if h not in sent:
            pending.append(f)
    if not pending:
        return {"count": 0, "oldest_hours": 0, "kept": len(files)}
    oldest = min(os.path.getmtime(f) for f in pending)
    return {"count": len(pending), "kept": len(files),
            "oldest_hours": _hours_since(datetime.datetime.fromtimestamp(oldest))}


def last_pull_state(path):
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            lines = [l.strip() for l in fh if l.strip()]
    except Exception:
        return {}
    tail = lines[-4:] if lines else []
    return {"lines": tail,
            "ended_ok": any(l.startswith("END") and l.endswith("ok") for l in tail),
            "failed": any("FAILED" in l for l in tail)}


def heartbeat_state(path):
    """Parse the medical PC's heartbeat. Text, because a human reads it too --
    so parse defensively and report what could not be read rather than guessing.
    """
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            txt = fh.read()
        age = _hours_since(datetime.datetime.fromtimestamp(os.path.getmtime(path)))
    except Exception:
        return {}, {}, None
    w = {}
    for line in txt.splitlines():
        u = line.strip()
        if u.startswith("WATCHER :"):
            w["alive"] = "ALIVE" in u.upper()
        elif u.startswith("CAPTURES:"):
            try:
                w["captures_today"] = int(u.split(":", 1)[1].strip().split()[0])
            except Exception:
                pass
    ign = 0
    for line in txt.splitlines():
        if line.strip().startswith("IGNORED :"):
            try:
                ign = int(line.split(":", 1)[1].strip().split()[0])
            except Exception:
                ign = 0
    return w, {"age_hours": age}, ign


def offsite_state(archive, mirror):
    """Is the Drive copy keeping up? The archive is the ONLY copy of a report
    once Marg overwrites its slot."""
    def newest(root):
        best = None
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                try:
                    m = os.path.getmtime(os.path.join(dp, f))
                except Exception:
                    continue
                if best is None or m > best:
                    best = m
        return best
    try:
        a, b = newest(archive), newest(mirror)
        if a is None or b is None:
            return {}
        return {"lag_hours": round(max(0.0, (a - b) / 3600.0), 1)}
    except Exception:
        return {}


def gather(args):
    w, hb, ign = heartbeat_state(args.heartbeat)
    return {"source": "manojz",
            "at": datetime.datetime.now().isoformat(timespec="seconds"),
            "outbox": outbox_state(args.archive),
            "last_pull": last_pull_state(args.last_pull),
            "watcher": w,
            "heartbeat": hb,
            "ignored": ign or 0,
            "offsite": offsite_state(args.archive, args.offsite)}


def post(payload, url, token, timeout=30):
    import urllib.request
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Finance-Marg", token)          # never logged
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")[:400]


def selftest():
    import tempfile
    ok = [0]
    def ck(cond, msg):
        ok[0] += 1
        if not cond:
            raise AssertionError("check %d FAILED: %s" % (ok[0], msg))
    t = tempfile.mkdtemp()
    arc = os.path.join(t, "arc"); os.makedirs(os.path.join(arc, "_outbox"))
    ck(outbox_state(arc).get("count") == 0, "empty outbox reads zero")
    with io.open(os.path.join(arc, "_outbox", "r.xls"), "w") as fh:
        fh.write("x")
    ck(outbox_state(arc)["count"] == 1, "an UNDELIVERED report is counted")
    import hashlib
    _h = hashlib.md5(b"x").hexdigest()
    with io.open(os.path.join(arc, "_outbox_state.json"), "w", encoding="utf-8") as fh:
        json.dump({"sent": {_h: {"business_date": "2026-08-01"}}}, fh)
    _os2 = outbox_state(arc)
    ck(_os2["count"] == 0 and _os2["kept"] == 1,
       "a DELIVERED report still on disk is NOT counted as waiting — delivered "
       "files are kept by design, and counting them would fire this check "
       "forever (caught against real data: 10 files, 0 actually pending)")
    ck(outbox_state(os.path.join(t, "nope")) == {}, "a missing archive is empty, not a crash")
    hb = os.path.join(t, "hb.txt")
    with io.open(hb, "w", encoding="utf-8") as fh:
        fh.write("WATCHER : ALIVE, pid 1\nCAPTURES: 6 today; newest x\nIGNORED : 2 file(s)\n")
    w, h, ig = heartbeat_state(hb)
    ck(w.get("alive") is True, "an ALIVE watcher is read as alive")
    ck(w.get("captures_today") == 6, "captures today is read")
    ck(ig == 2, "the ignored counter is read")
    with io.open(hb, "w", encoding="utf-8") as fh:
        fh.write("WATCHER : NOT RUNNING\nCAPTURES: 0 today\nIGNORED : 0 file(s)\n")
    w2, _, _ = heartbeat_state(hb)
    ck(w2.get("alive") is False, "a dead watcher is read as dead — the case that matters")
    ck(heartbeat_state(os.path.join(t, "nope"))[0] == {}, "a missing heartbeat is empty, not a crash")
    lp = os.path.join(t, "lp.txt")
    with io.open(lp, "w", encoding="utf-8") as fh:
        fh.write("START 26-08-2026 01:00:00\nEND 26-08-2026 01:00:11 -- ok\n")
    ck(last_pull_state(lp)["ended_ok"] is True, "a clean pull is read as ok")
    ck(last_pull_state(os.path.join(t, "nope")) == {}, "a missing pull stamp is empty, not a crash")
    p = gather(argparse.Namespace(archive=arc, last_pull=lp, heartbeat=hb,
                                  offsite=os.path.join(t, "nope")))
    ck(p["source"] == "manojz" and "outbox" in p, "the payload assembles")
    ck(json.dumps(p) and "token" not in json.dumps(p).lower(),
       "the payload carries no token — it must never leave here")
    print("PIPELINE_STATUS SELFTEST PASSED — %d checks OK" % ok[0])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="post manojz's view of the Marg pipeline")
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--last-pull", dest="last_pull", default=DEF_LASTPULL)
    ap.add_argument("--heartbeat", default=DEF_HEARTBEAT)
    ap.add_argument("--offsite", default=DEF_OFFSITE)
    ap.add_argument("--url", default=DEF_URL)
    ap.add_argument("--token-file", default=DEF_TOKEN)
    ap.add_argument("--token-unc", default=DEF_TOKEN_UNC)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    try:
        payload = gather(a)
    except Exception as ex:                                   # noqa: BLE001
        print("pipeline_status: could not gather (%s) — the pull is unaffected" % ex)
        return 0
    if a.dry_run:
        print(json.dumps(payload, indent=2))
        return 0
    try:
        sys.path.insert(0, HERE)
        import marg_gate                                      # one token rule, D349
        token, where = marg_gate.resolve_token(a.token_unc, a.token_file)
    except Exception as ex:                                   # noqa: BLE001
        print("pipeline_status: no token (%s) — the pull is unaffected" % ex)
        return 0
    if not token:
        print("pipeline_status: no token available — the pull is unaffected")
        return 0
    try:
        st, body = post(payload, a.url, token)
        print("pipeline_status: %s (token from %s)" % (st, where))
    except Exception as ex:                                   # noqa: BLE001
        print("pipeline_status: post failed (%s) — the pull is unaffected" % ex)
    return 0


if __name__ == "__main__":
    sys.exit(main())
