#!/usr/bin/env python3
"""legs_s830.py -- kit S830: adds / removes ONE leg in the freshness legs file, keeping every other byte as it is.
   legs_s830.py check  <legs.json>          -> 'LEGS ok legs=N has=0|1' (the file re-dumps to its own bytes) or 'LEGS BAD ...'
   legs_s830.py add    <legs.json> <out>    -> writes <out>: the same file with the leg appended (once)
   legs_s830.py remove <legs.json> <out>    -> writes <out>: the same file without it
The file's own style is json.dumps(indent=1, ensure_ascii=False), no newline at the end; 'check' proves that before anything
is written, so nothing else in the file can move."""
import json
import sys

LEG = {
    "name": "attendance machine contact",
    "group": "Attendance",
    "kind": "state_json",
    "target": "/root/att_silence_watch.state.json",
    "field": "last_ok_iso",
    "fail_field": "last_failure_iso",
    "max_age_h": 1,
    "note": "S830 (F-1402) · att_silence_watch.py every 5 min · red when the machine has made no contact for 30 min in "
            "clinic hours, or no punch has come by 10:00 on a working day, or when the watcher itself has stopped",
}


def dump(d):
    return json.dumps(d, indent=1, ensure_ascii=False)


def read(path):
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    d = json.loads(raw)
    if not isinstance(d, dict) or not isinstance(d.get("legs"), list):
        raise ValueError("no 'legs' list")
    if dump(d) != raw:
        raise ValueError("the file does not re-dump to its own bytes")
    return d


def has(d):
    return sum(1 for x in d["legs"] if isinstance(x, dict) and x.get("name") == LEG["name"])


def main(a):
    try:
        d = read(a[1])
    except Exception as e:                               # noqa: BLE001
        print("LEGS BAD %s: %s" % (type(e).__name__, str(e)[:120]))
        return 1
    if a[0] == "check":
        print("LEGS ok legs=%d has=%d" % (len(d["legs"]), has(d)))
        return 0
    if a[0] == "add":
        if has(d) == 0:
            d["legs"].append(dict(LEG))
    elif a[0] == "remove":
        d["legs"] = [x for x in d["legs"] if not (isinstance(x, dict) and x.get("name") == LEG["name"])]
    else:
        print("LEGS BAD unknown action")
        return 1
    with open(a[2], "w", encoding="utf-8") as fh:
        fh.write(dump(d))
    print("LEGS written legs=%d has=%d" % (len(d["legs"]), has(d)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
