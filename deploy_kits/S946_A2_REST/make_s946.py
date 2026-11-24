#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_s946.py -- S946 (the parent, S512, 24-Nov-2026): the anchored patches of this kit.

  worker  <from> <to>            call_pipeline_worker.py 3c8be7f0 -> TO: a state file at the end of every pipeline run
                                 (/root/wa/recordings-archive/pipeline_state.json: last_run_iso, last_success_iso,
                                 last_fail_iso, last_result, kicks, fresh, seconds). Four exact anchors; nothing else moves.
  legs    <from> <to> [--with-watchdog]
                                 freshness_legs.json 2a03e305 -> TO: the leg "AI judged within 15 min" (state_json,
                                 fail_field, 50 h -- a quiet Sunday is not a fault; an INCOMPLETE run is red at once),
                                 and with --with-watchdog the leg "call webhook watchdog" (state_json, fail_field, 26 h).
Each anchor must occur exactly once in the FROM text, or nothing is written.
"""
import json
import sys

WORKER_PATCHES = [
    # 1. the path, beside the lock
    ('LOCK_PATH = os.path.join(RA_DIR, "pipeline.lock")\n',
     'LOCK_PATH = os.path.join(RA_DIR, "pipeline.lock")\n'
     'STATE_PATH = os.path.join(RA_DIR, "pipeline_state.json")   # S946: the last run, for the health page\n'),
    # 2. the writer, before today_ist()
    ('def today_ist():\n',
     'def _s946_state(ok, kicks, fresh, seconds):\n'
     '    """S946: one small JSON after every run -- the freshness leg \'AI judged within 15 min\' reads it.\n'
     '    last_success_iso moves on a complete run, last_fail_iso on an INCOMPLETE one. Never raises."""\n'
     '    try:\n'
     '        prev = {}\n'
     '        try:\n'
     '            with open(STATE_PATH, "r", encoding="utf-8") as f:\n'
     '                prev = json.load(f)\n'
     '            if not isinstance(prev, dict):\n'
     '                prev = {}\n'
     '        except Exception:           # noqa: BLE001\n'
     '            prev = {}\n'
     '        now = datetime.datetime.now(IST).replace(microsecond=0).isoformat()\n'
     '        rec = {"last_run_iso": now,\n'
     '               "last_success_iso": now if ok else prev.get("last_success_iso", ""),\n'
     '               "last_fail_iso": prev.get("last_fail_iso", "") if ok else now,\n'
     '               "last_result": "complete" if ok else "INCOMPLETE",\n'
     '               "kicks": kicks, "fresh": fresh, "seconds": round(seconds, 1),\n'
     '               "runs_today": (prev.get("runs_today", 0) + 1) if str(prev.get("last_run_iso", ""))[:10] == now[:10] else 1}\n'
     '        tmp = STATE_PATH + ".tmp"\n'
     '        with open(tmp, "w", encoding="utf-8") as f:\n'
     '            json.dump(rec, f, indent=2, sort_keys=True)\n'
     '        os.chmod(tmp, 0o600)\n'
     '        os.replace(tmp, STATE_PATH)\n'
     '    except Exception as e:          # noqa: BLE001\n'
     '        log("state file not written (the run itself stands):", e)\n'
     '\n'
     '\n'
     'def today_ist():\n'),
    # 3. the clock before the run
    ('        ok = run_pipeline(today_ist())\n',
     '        t0 = time.time()\n'
     '        ok = run_pipeline(today_ist())\n'),
    # 4. the write after the run's log line
    ('        log("run %s" % ("complete" if ok else "INCOMPLETE"))\n',
     '        log("run %s" % ("complete" if ok else "INCOMPLETE"))\n'
     '        _s946_state(ok, n, len(fresh), time.time() - t0)\n'),
]

LEG_PIPELINE = {
    "name": "AI judged within 15 min",
    "group": "Console and calls",
    "kind": "state_json",
    "target": "/root/wa/recordings-archive/pipeline_state.json",
    "field": "last_success_iso",
    "fail_field": "last_fail_iso",
    "max_age_h": 50,
    "note": "S946 \u00b7 the at-hangup pipeline (archive \u2192 transcribe \u2192 verdict) wrote its state after a complete run; "
            "red at once when the newest run was INCOMPLETE; 50 h so a quiet Sunday is not a fault",
}
LEG_WATCHDOG = {
    "name": "call webhook watchdog",
    "group": "Console and calls",
    "kind": "state_json",
    "target": "/root/wa/call-hook/callhook_watchdog.state.json",
    "field": "last_success_iso",
    "fail_field": "last_fail_iso",
    "max_age_h": 26,
    "note": "S946 \u00b7 11:15 daily: the web server's log read for refused (403) call-webhook deliveries; "
            "red at once on a refusal, a missing raw log on a clinic day, or an unreadable log",
}


def patch_worker(src):
    out = src
    for i, (old, new) in enumerate(WORKER_PATCHES, 1):
        n = out.count(old)
        if n != 1:
            raise SystemExit("anchor %d occurs %d time(s), not once -- nothing written" % (i, n))
        out = out.replace(old, new, 1)
    return out


def patch_legs(src, with_watchdog):
    d = json.loads(src)
    legs = d["legs"]
    names = [l.get("name") for l in legs]
    for leg in ([LEG_PIPELINE, LEG_WATCHDOG] if with_watchdog else [LEG_PIPELINE]):
        if leg["name"] in names:
            raise SystemExit("leg %r is already there -- nothing written" % leg["name"])
        legs.append(dict(leg))
    return json.dumps(d, indent=1, ensure_ascii=False)      # the file's own shape (S230): indent 1, no trailing newline


def main(argv):
    if len(argv) < 4 or argv[1] not in ("worker", "legs"):
        raise SystemExit(__doc__)
    src = open(argv[2], "r", encoding="utf-8").read()
    if argv[1] == "worker":
        out = patch_worker(src)
    else:
        out = patch_legs(src, "--with-watchdog" in argv[4:])
    with open(argv[3], "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote", argv[3], len(out), "bytes")


if __name__ == "__main__":
    main(sys.argv)
