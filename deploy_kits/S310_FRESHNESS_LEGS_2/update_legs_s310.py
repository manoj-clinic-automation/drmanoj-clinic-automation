#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update_legs_s310.py -- S310: two more legs on the health page, after S309.

The rule F-517 left behind: a kit that gives a job a schedule rereads every watch that names that job.
The live crontab, read on the box at the S309 install (17-Sep-2026, 22:46 IST):

  30 2 * * *  assetapp_backup.py   (S286)   -- nightly, verified, 14 days kept, Drive copy by S287
  40 2 * * *  petty_backup.py      (S295)   -- nightly, the petty bill photos off the box
  */10 * * *  docterz_ingest.py    (S291)   -- already settled by S309

1 CHANGE  "asset app archive": 200 h and the word "weekly" are from the days of a bare tar line in the
          crontab. The job has been nightly and verified since S286, so the window becomes 26 h.
2 ADD     "petty bill photos off-box": nothing watches S295's 02:40 job. It writes ONE LINE to
          /root/backups/petty_backup.log on every run, whether or not there was a new photo (an
          unchanged folder is skipped, so the archive itself is not a reliable clock -- the log is).
          The leg is added only once that log exists: the first run is 02:40 the morning after S295
          went live. Until then the row would read NEVER and light the page red for no fault.
          Re-run this kit after that first run and it adds the leg then.

Every edit is a TEXT edit inside the legs file the live collector reads; the file is hand-formatted
and is never re-serialised. A backup is written beside it, the result is parsed and compared leg by
leg, and the file is read back. No code, no service, no restart.

Usage:  update_legs_s310.py --check [--file PATH]     read-only
        update_legs_s310.py --apply [--file PATH]     make the changes (idempotent)
"""
import datetime
import glob
import hashlib
import json
import os
import re
import sys

DEFAULT_FILE = "/root/finance/freshness_legs.json"
CONF = "/root/finance/freshness.conf"

ASSET_NOTE = ("nightly at 02:30 by assetapp_backup.py (S286), which verifies the archive it writes and "
              "keeps 14 days; its off-box copy is S287's. 26 h: a daily job with two hours of slack. "
              "If this reads NEVER the cron line is fiction -- that is the point of the row.")
CHANGES = [{"name": "asset app archive", "from_h": 200, "to_h": 26, "note": ASSET_NOTE}]

PETTY_LOG = "/root/backups/petty_backup.log"
ADDS = [{"after": "asset app archive",
         "needs": PETTY_LOG,
         "leg": {"name": "petty bill photos off-box",
                 "group": "Backups",
                 "kind": "log_mtime",
                 "target": PETTY_LOG,
                 "max_age_h": 26,
                 "note": ("nightly at 02:40 by petty_backup.py (S295): Manoj Bhati's bill and diary photos, "
                          "archived off the box. The log carries one line per run even when nothing changed, "
                          "so a quiet log means the job did not run -- the archive itself is skipped when no "
                          "photo is new and is not a clock.")}}]


def md5_text(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def resolve_file(arg):
    if arg:
        return arg
    try:
        with open(CONF, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LEGS_FILE") and "=" in line:
                    v = line.split("=", 1)[1].strip()
                    if v:
                        return v
    except OSError:
        pass
    return DEFAULT_FILE


def leg_span(text, name):
    i = text.find('"name": "%s"' % name)
    if i < 0:
        return None, None
    s = text.rfind("{", 0, i)
    e = text.find("}", i)
    if s < 0 or e < 0:
        return None, None
    return s, e + 1


def leg_of(text, name):
    s, e = leg_span(text, name)
    if s is None:
        return None
    try:
        return json.loads(text[s:e])
    except ValueError:
        return None


def age_h(leg):
    """(hours since what this leg watches last moved, why-not). Read-only, and only the kinds used here."""
    kind, target = leg.get("kind"), leg.get("target")
    try:
        if kind == "log_mtime" or kind == "file_mtime":
            if not os.path.isfile(target):
                return None, "not there yet"
            t = os.path.getmtime(target)
        elif kind == "glob_newest":
            hits = glob.glob(target)
            if not hits:
                return None, "nothing matches yet"
            t = max(os.path.getmtime(p) for p in hits)
        elif kind == "sqlite_max":
            import sqlite3
            if not os.path.isfile(target):
                return None, "database not readable here"
            con = sqlite3.connect("file:%s?mode=ro" % target, uri=True)
            row = con.execute("SELECT MAX(%s) FROM %s" % (leg["column"], leg["table"])).fetchone()
            con.close()
            if not row or not row[0]:
                return None, "no rows"
            return (datetime.datetime.now()
                    - datetime.datetime.fromisoformat(str(row[0]).replace("T", " ")[:19])).total_seconds() / 3600.0, ""
        else:
            return None, "kind %s not read here" % kind
    except (OSError, ValueError) as ex:
        return None, str(ex)
    return (datetime.datetime.now().timestamp() - t) / 3600.0, ""


def apply_change(text, ch):
    """(new text, message). The window and the note of one leg; nothing else."""
    leg = leg_of(text, ch["name"])
    if leg is None:
        return None, "leg %r is not in this file" % ch["name"]
    if leg.get("max_age_h") == ch["to_h"] and leg.get("note") == ch["note"]:
        return text, "ALREADY %s" % ch["name"]
    if leg.get("max_age_h") != ch["from_h"]:
        return None, "leg %r reads %s h, expected %s h" % (ch["name"], leg.get("max_age_h"), ch["from_h"])
    a, why = age_h(leg)
    if a is not None and a > ch["to_h"]:
        return None, ("leg %r already watches something %.1f h old, older than the new %d h window --"
                      " the window is not the first thing to fix" % (ch["name"], a, ch["to_h"]))
    s, e = leg_span(text, ch["name"])
    block = text[s:e]
    block, n1 = re.subn(r'("max_age_h"\s*:\s*)%d\b' % ch["from_h"], lambda m: m.group(1) + str(ch["to_h"]), block)
    block, n2 = re.subn(r'("note"\s*:\s*)"(?:[^"\\]|\\.)*"',
                        lambda m: m.group(1) + json.dumps(ch["note"], ensure_ascii=False), block)
    if n1 != 1 or n2 != 1:
        return None, "leg %r does not carry its window and note exactly once" % ch["name"]
    return text[:s] + block + text[e:], "CHANGED %s -> %d h" % (ch["name"], ch["to_h"])


def apply_add(text, add):
    """(new text, message). The new leg goes in right after the named one, in the file's own indent."""
    leg = add["leg"]
    if leg_of(text, leg["name"]) is not None:
        return text, "ALREADY %s" % leg["name"]
    if add.get("needs") and not os.path.exists(add["needs"]):
        return text, "SKIPPED %s -- %s does not exist yet; re-run this kit after its first run" % (
            leg["name"], add["needs"])
    a, why = age_h(leg)
    if a is None:
        return text, "SKIPPED %s -- what it would watch cannot be read yet (%s)" % (leg["name"], why)
    if a > leg["max_age_h"]:
        return text, "SKIPPED %s -- what it would watch is already %.1f h old; it would go red at once" % (
            leg["name"], a)
    s, e = leg_span(text, add["after"])
    if s is None:
        return None, "the leg %r to place it after is not in this file" % add["after"]
    indent = " " * (s - text.rfind("\n", 0, s) - 1)
    body = json.dumps(leg, ensure_ascii=False, indent=1)
    body = "\n".join((indent + ln) if i else ln for i, ln in enumerate(body.split("\n")))
    return text[:e] + ",\n" + indent + body + text[e:], "ADDED %s (%d h)" % (leg["name"], leg["max_age_h"])


def compare(old, new, changed_names, added_names):
    """Only the named legs may have moved; every other leg must be identical, and the file's own
    header and windows text must not move at all."""
    a, b = json.loads(old), json.loads(new)
    if a.get("_about") != b.get("_about") or a.get("_windows") != b.get("_windows"):
        return "the file's header changed"
    old_by = {l["name"]: l for l in a["legs"]}
    new_by = {l["name"]: l for l in b["legs"]}
    if set(new_by) - set(old_by) != set(added_names):
        return "legs appeared that this kit does not add"
    if set(old_by) - set(new_by):
        return "a leg disappeared"
    for name, leg in old_by.items():
        if name in changed_names:
            other_old = {k: v for k, v in leg.items() if k not in ("max_age_h", "note")}
            other_new = {k: v for k, v in new_by[name].items() if k not in ("max_age_h", "note")}
            if other_old != other_new:
                return "leg %r changed in a field this kit does not touch" % name
        elif leg != new_by[name]:
            return "leg %r changed and should not have" % name
    return ""


def main(argv):
    mode = "--check" if "--check" in argv else ("--apply" if "--apply" in argv else "")
    path = argv[argv.index("--file") + 1] if "--file" in argv else None
    path = resolve_file(path)
    if not mode:
        print(__doc__)
        return 2
    if not os.path.isfile(path):
        print("FAIL: no legs file at", path)
        return 1
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        json.loads(text)
    except ValueError as ex:
        print("FAIL: the legs file is not readable JSON:", ex)
        return 1
    print("legs file : %s (md5 %s)" % (path, md5_text(text)))
    for ch in CHANGES:
        leg = leg_of(text, ch["name"])
        a, why = age_h(leg) if leg else (None, "leg missing")
        print("  %-26s now %s h -> %s h   watched thing %s" % (
            ch["name"], leg.get("max_age_h") if leg else "?", ch["to_h"],
            ("%.1f h old" % a) if a is not None else "not read here (%s)" % why))
    for add in ADDS:
        here = leg_of(text, add["leg"]["name"]) is not None
        a, why = age_h(add["leg"])
        print("  %-26s %s   watched thing %s" % (
            add["leg"]["name"], "already on the page" if here else "to add (%d h)" % add["leg"]["max_age_h"],
            ("%.1f h old" % a) if a is not None else "not there yet (%s)" % why))
    new, msgs = text, []
    for ch in CHANGES:
        out, m = apply_change(new, ch)
        if out is None:
            print("FAIL:", m)
            return 1
        new, _ = out, msgs.append(m)
    for add in ADDS:
        out, m = apply_add(new, add)
        if out is None:
            print("FAIL:", m)
            return 1
        new, _ = out, msgs.append(m)
    for m in msgs:
        print("  ", m)
    if new == text:
        print("RESULT ALREADY -- nothing to change" if all(m.startswith(("ALREADY", "SKIPPED")) for m in msgs)
              else "RESULT ALREADY")
        return 0
    if mode == "--check":
        print("RESULT PENDING -- --apply would write the lines above.")
        return 0
    bad = compare(text, new, {c["name"] for c in CHANGES}, {a["leg"]["name"] for a in ADDS
                                                            if leg_of(new, a["leg"]["name"]) is not None
                                                            and leg_of(text, a["leg"]["name"]) is None})
    if bad:
        print("FAIL:", bad)
        return 1
    bak = "%s.bak_S310_%s" % (path, md5_text(text)[:8])
    with open(bak, "w", encoding="utf-8") as f:
        f.write(text)
    tmp = path + ".s310.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new)
    os.replace(tmp, path)
    with open(path, encoding="utf-8") as f:
        back = f.read()
    if back != new:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("FAIL: the read-back did not match; the old file has been put back")
        return 1
    print("backup    : %s" % bak)
    print("new md5   : %s" % md5_text(back))
    print("RESULT APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
