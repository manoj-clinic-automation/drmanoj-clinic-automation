#!/usr/bin/env python3
"""make_s525.py -- kit S525_SPINE_RED_FAST: builds the two new files from their pinned FROM bytes by exact,
counted edits (every anchor exactly once), in memory first; nothing is written unless every edit applies.
  python3 make_s525.py <dir with the FROM files> <out dir>"""
import hashlib, os, sys

FROM = {"freshness.py": "66d93a631c6c46ebb6536620450efa74",
        "freshness_legs.json": "716734aef3bcacdef54d0172a00440e2"}

F_EDITS = [
("F1 the cron note",
"""#  Cron (08:05, five minutes after the 08:00 health report, so one morning
#  message covers the whole estate):
#    5 8 * * *  /root/wa/venv/bin/python3 /root/finance/freshness.py --shout >> /root/finance/freshness.log 2>&1
""",
"""#  Cron (08:05, five minutes after the 08:00 health report, so one morning
#  message covers the whole estate):
#    5 8 * * *  /root/wa/venv/bin/python3 /root/finance/freshness.py --shout >> /root/finance/freshness.log 2>&1
#  S525 (F-849): and at :35 every hour 09-23, so a leg that turns red is on the
#  page and shouted within the hour -- still once per leg per calendar day:
#    35 9-23 * * *  /root/wa/venv/bin/python3 /root/finance/freshness.py --shout >> /root/finance/freshness.log 2>&1 # S525_FRESH_HOURLY
#
#  S525 (F-849): a state_json leg may also name "fail_field" (the state file's
#  own time of its newest FAILED run). When that time is newer than the
#  success field, the newest run failed and the leg is STALE at once, whatever
#  max_age_h says. The spine gate failed on 08-Oct 09:10 and, judged by age
#  alone against 26 h with one run a day, was first shouted on 10-Oct 08:05.
"""),
("F2 the failure field, read",
"""def read_file_mtime(leg):
""",
"""def read_fail_ts(leg, field):
    \"\"\"S525: the state file's time of its newest FAILED run, or None when the file
    records none. A value that is there but cannot be read is an ERROR (raised).\"\"\"
    with open(leg["target"]) as fh:
        data = json.load(fh)
    raw = data.get(field) if isinstance(data, dict) else None
    if raw in (None, "", 0):
        return None
    ts = parse_ts(raw)
    if ts is None:
        raise ValueError("field %s is not a timestamp this can read" % field)
    return ts


def read_file_mtime(leg):
"""),
("F3 the failure field, judged",
"""        row["verdict"] = OK if age <= leg["max_age_h"] * 3600.0 else STALE
    except Exception as ex:                      # deliberately everything""",
"""        row["verdict"] = OK if age <= leg["max_age_h"] * 3600.0 else STALE
        ff = leg.get("fail_field")
        if ff and leg["kind"] == "state_json":   # S525 (F-849): the newest run failed -> red now
            ft = read_fail_ts(leg, str(ff))
            if ft is not None and ft > ts:
                row["verdict"] = STALE
                row["age_words"] = "newest build FAILED; last good " + plain_age(age)   # shown on the page and in the shout
                row["detail"] = ("the newest run FAILED at %s; the last good run was %s"
                                 % (time.strftime("%Y-%m-%d %H:%M", time.localtime(ft)),
                                    time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))))
    except Exception as ex:                      # deliberately everything"""),
]

J_EDITS = [
("J1 the spine gate leg reads its failure field",
"""   "target": "/root/finance/spine/spine_state.json",
   "field": "last_success_iso",
   "max_age_h": 26,
   "note": "spine_build.py every 10 min 08-23 (S331, state file by S338): last_success moves ONLY when the gate is 14/14, so a failing gate goes red here by itself · the one line""",
"""   "target": "/root/finance/spine/spine_state.json",
   "field": "last_success_iso",
   "fail_field": "last_failure_iso",
   "max_age_h": 26,
   "note": "spine_build.py every 10 min 08-23 (S331, state file by S338): last_success moves ONLY when the gate is 14/14 · S525 (F-849): red as soon as the newest build FAILED (last_failure_iso newer than last_success_iso), not 26 h later · the one line"""),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, out):
    res = {}
    for name, edits in (("freshness.py", F_EDITS), ("freshness_legs.json", J_EDITS)):
        b = open(os.path.join(src, name), "rb").read()
        if md5(b) != FROM[name]:
            raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (name, md5(b), FROM[name]))
        t = b.decode("utf-8")
        for label, old, new in edits:
            n = t.count(old)
            if n != 1:
                raise SystemExit("REFUSED: %s / %s: the anchor occurs %d times" % (name, label, n))
            t = t.replace(old, new)
        res[name] = t.encode("utf-8")
        print("%-20s %d edits  %s -> %s" % (name, len(edits), FROM[name][:8], md5(res[name])[:8]))
    os.makedirs(out, exist_ok=True)
    for name, b in res.items():                        # the legs file ships as .kit: the repository ignores *.json (F-832)
        with open(os.path.join(out, name + (".kit" if name.endswith(".json") else "")), "wb") as fh:
            fh.write(b)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2])
