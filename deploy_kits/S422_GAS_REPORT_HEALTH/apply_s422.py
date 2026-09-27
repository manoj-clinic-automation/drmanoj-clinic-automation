#!/usr/bin/env python3
"""apply_s422.py -- kit S422_GAS_REPORT_HEALTH (session 284, 27-Sep-2026) -- F-595.

Two edits, both idempotent, both proven on a scratch copy first by the installer:
  1. finance_app.py: ONE self-contained block inserted immediately before the unique marker
     '    # ---- B2: THE NEVER-FIRED WITNESS', inside _health_state(). It reads the Sunday Apps Script
     comparison's own result file (<GAS_DIR>/_DRIFT.json, written by gas_export.py only on a successful run)
     and adds ONE row to the health page: ok (Google and the repository copy agree) / info (files changed in
     Google that the repository copy does not hold yet -- the assistant's to copy, nothing for the owner) /
     warn (the weekly comparison has not run for more than 8 days) / info (never run yet).
  2. freshness_legs.json: ONE leg, 'Apps Script weekly comparison', file_mtime on the same _DRIFT.json, 200 h.

usage: apply_s422.py <finance_app.py> <freshness_legs.json> <gas_dir>     (writes both files in place)
"""
import json
import sys

MARK = "    # ---- B2: THE NEVER-FIRED WITNESS"
TAG = "# ---- S422 (F-595): THE SUNDAY APPS SCRIPT COMPARISON"
PREV = '''        add("pipeline", "Pipeline heartbeat", "info",
            "could not be read (%s)" % ex)

'''
BLOCK = '''    # ---- S422 (F-595): THE SUNDAY APPS SCRIPT COMPARISON -------------------
    # gas_export.py (Sunday 02:20) compares every Apps Script project in Google with the repository copy
    # (deploy_kits/GAS_CURRENT). Its answer used to go only to a log nobody reads; this row is its reader.
    # Findings are 'info': copying Google's newer file into the repository is the assistant's job, never
    # the owner's. A comparison that has stopped running is 'warn'. Reads one file; changes nothing.
    try:
        _gd = "/root/state_backup/gas"
        try:
            with open("/root/state_backup/clinic_state_backup.conf", encoding="utf-8") as _fh:
                for _ln in _fh:
                    _ln = _ln.strip()
                    if _ln.startswith("GAS_DIR="):
                        _gd = _ln.split("=", 1)[1].strip().strip('"').strip("'") or _gd
        except OSError:
            pass
        _dp = os.path.join(_gd, "_DRIFT.json")
        if not os.path.isfile(_dp):
            add("gasdrift", "Apps Script vs the repository", "info",
                "the Sunday comparison has not written a result yet",
                "gas_export.py runs Sundays 02:20 and writes %s on success." % _dp)
        else:
            _age_d = (dt.datetime.now().timestamp() - os.path.getmtime(_dp)) / 86400.0
            with open(_dp, encoding="utf-8") as _fh:
                _dj = json.load(_fh)
            _real = [x for x in (list(_dj.get("against_repository") or [])
                                 + list(_dj.get("since_last_run") or []))
                     if isinstance(x, dict)
                     and x.get("kind") not in ("no_copy", "changed_whitespace")]
            _seen, _names = set(), []
            for x in _real:
                _nm = "%s/%s" % (x.get("label") or "?", x.get("file") or "?")
                if _nm not in _seen:
                    _seen.add(_nm)
                    _names.append(_nm)
            _when = str(_dj.get("checked_at_ist") or "")[:16]
            if _age_d > 8:
                add("gasdrift", "Apps Script vs the repository", "warn",
                    "the Sunday comparison last ran %.0f days ago (%s)" % (_age_d, _when or "?"),
                    "It should run every Sunday at 02:20. Its log: "
                    "/root/state_backup/gas_export.log")
            elif _names:
                add("gasdrift", "Apps Script vs the repository", "info",
                    "%d file(s) in Google differ from the repository copy: %s%s (checked %s)"
                    % (len(_names), ", ".join(_names[:4]),
                       " +%d more" % (len(_names) - 4) if len(_names) > 4 else "", _when),
                    "Nothing for you. The assistant copies Google's current file into "
                    "deploy_kits/GAS_CURRENT at the next session.")
            else:
                add("gasdrift", "Apps Script vs the repository", "ok",
                    "every exported project matches the repository copy (checked %s)" % _when)
    except Exception as ex:                                       # noqa: BLE001
        add("gasdrift", "Apps Script vs the repository", "info",
            "could not be read (%s)" % ex)

'''
LEG = {"name": "Apps Script weekly comparison", "group": "Backups", "kind": "file_mtime",
       "target": None, "max_age_h": 200,
       "note": "Sundays 02:20 · gas_export.py writes _DRIFT.json only when a comparison succeeds (S422, F-595)"}


def patch_app(path):
    s = open(path, encoding="utf-8", newline="").read()
    if TAG in s:
        return "already"
    if s.count(MARK) != 1:
        raise SystemExit("REFUSED: the B2 marker is not in the file exactly once (%d)" % s.count(MARK))
    i = s.index(MARK)
    if not s[:i].endswith(PREV):
        raise SystemExit("REFUSED: the lines before the B2 marker are not the ones this kit was built on")
    s = s[:i] + BLOCK + s[i:]
    open(path, "w", encoding="utf-8", newline="").write(s)
    return "patched"


def patch_legs(path, gas_dir):
    raw = open(path, encoding="utf-8").read()
    d = json.loads(raw)
    legs = d.get("legs")
    if not isinstance(legs, list):
        raise SystemExit("REFUSED: freshness_legs.json has no legs list")
    if any(l.get("name") == LEG["name"] for l in legs if isinstance(l, dict)):
        return "already"
    leg = dict(LEG)
    leg["target"] = gas_dir.rstrip("/") + "/_DRIFT.json"
    legs.append(leg)
    if json.dumps(json.loads(raw), ensure_ascii=False, indent=1) != raw:
        raise SystemExit("REFUSED: freshness_legs.json is not in the shape this kit re-writes (indent 1, no newline)")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(d, ensure_ascii=False, indent=1))      # the file's own shape, byte for byte
    return "added"


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    print("finance_app.py :", patch_app(sys.argv[1]))
    print("freshness_legs :", patch_legs(sys.argv[2], sys.argv[3]))
