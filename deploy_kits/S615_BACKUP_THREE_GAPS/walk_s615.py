#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s615.py -- kit S615 (S336, 22-Oct-2026): the encrypted nightly carries the three gaps.

    python3 walk_s615.py ORIG NEW [--box]

On made-up files only: the three new paths are re-pointed into a scratch tree, gather() of the NEW file is run on
them alone, and the bundle's data/ must hold att_config.py, send_log.jsonl and wa_logs/<day>.jsonl -- while a
secret-shaped file inside wa_logs is skipped by pattern, a temp file is skipped, and every old named source is still
named. --box: the three real paths exist on this machine (read for size only, never opened).
Exit 0 = GREEN (last line 'WALK OK ...'); the S476 file goes RED.
"""
import importlib.util
import os
import shutil
import sys
import tempfile

orig_p, new_p = sys.argv[1], sys.argv[2]
BOX = "--box" in sys.argv
NEWF = ["/root/att_config.py", "/root/wa/wa_inbox/send_log.jsonl"]
NEWT = ["/root/wa/wa_logs"]
passed, failed = [], []


def check(c, label):
    (passed if c else failed).append(label)
    print(("  ok   " if c else "  FAIL ") + label)
    return c


def load(p, tag):
    s = importlib.util.spec_from_file_location("csb_" + tag, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


O, N = load(orig_p, "o"), load(new_p, "n")
if not check(all(x in N.SRC_FILES for x in NEWF) and all(x in N.SRC_TREES for x in NEWT),
             "the new file names att_config.py, send_log.jsonl and wa_logs"):
    print("WALK RED: the three are not named (the S476 file)")
    sys.exit(1)
check(N.SRC_FILES == O.SRC_FILES + NEWF, "SRC_FILES: every old one kept, in order, plus the two (%d -> %d)"
      % (len(O.SRC_FILES), len(N.SRC_FILES)))
check(N.SRC_TREES == O.SRC_TREES + NEWT, "SRC_TREES: every old one kept, plus wa_logs (%d -> %d)"
      % (len(O.SRC_TREES), len(N.SRC_TREES)))
check(N.SRC_DIRS == O.SRC_DIRS, "SRC_DIRS unchanged")
check(not N.is_secret("att_config.py") and not N.is_secret("send_log.jsonl") and not N.is_secret("2026-10-22.jsonl"),
      "none of the three is skipped as secret-shaped by name")

T = tempfile.mkdtemp(prefix="s615_walk_")
try:
    fx = os.path.join(T, "root")
    for p in NEWF:
        q = fx + p
        os.makedirs(os.path.dirname(q), exist_ok=True)
        open(q, "w").write("# made up\n" if q.endswith(".py") else '{"made_up": true}\n')
    wl = fx + NEWT[0]
    os.makedirs(wl, exist_ok=True)
    open(os.path.join(wl, "2099-01-01.jsonl"), "w").write('{"made_up": 1}\n')
    open(os.path.join(wl, "2099-01-02.jsonl"), "w").write('{"made_up": 2}\n')
    open(os.path.join(wl, "token_cache.json"), "w").write("{}\n")         # secret-shaped: must be skipped
    open(os.path.join(wl, "x.jsonl.tmp"), "w").write("{}\n")              # temp: must be skipped
    N.SRC_FILES = [fx + p for p in NEWF]
    N.SRC_DIRS = []
    N.SRC_TREES = [wl]
    N._gather_shape = lambda conf, shape_dir, g: None                    # the machine's shape is not this kit's
    dest = os.path.join(T, "stage")
    g = N.gather({"WORK_DIR": os.path.join(T, "w")}, dest)
    names = sorted(e[0] for e in g.entries)
    check("data/att_config.py" in names and "data/send_log.jsonl" in names,
          "gather takes data/att_config.py and data/send_log.jsonl")
    check("data/wa_logs/2099-01-01.jsonl" in names and "data/wa_logs/2099-01-02.jsonl" in names,
          "gather takes wa_logs day by day (data/wa_logs/<day>.jsonl)")
    check(not any("token" in n or ".tmp" in n for n in names) and g.secrets_skipped >= 1,
          "a secret-shaped file in wa_logs is skipped by pattern, a temp file is not taken")
    check(sorted(g.sources_present) == sorted(N.SRC_FILES + [wl]) and not g.sources_missing,
          "the vanished-source guard sees three sources (the tree as one)")
    os.remove(N.SRC_FILES[1])
    g2 = N.gather({"WORK_DIR": os.path.join(T, "w")}, os.path.join(T, "stage2"))
    check(N.SRC_FILES[1] in g2.sources_missing, "a missing send log is reported as missing, not hidden")
finally:
    shutil.rmtree(T, ignore_errors=True)

if BOX:
    for p in NEWF:
        check(os.path.isfile(p), "on this machine: %s is there (%s bytes)" % (p, os.path.getsize(p) if os.path.isfile(p) else "-"))
    tot = n = 0
    big = 0
    for base, _d, fs in os.walk(NEWT[0]):
        for f in fs:
            n += 1
            sz = os.path.getsize(os.path.join(base, f))
            tot += sz
            big = max(big, sz)
    check(n > 0, "on this machine: %s holds %d files, %.1f MB, the largest %.1f MB (the per-file guard is %d MB)"
          % (NEWT[0], n, tot / 1048576.0, big / 1048576.0, N.MAX_FILE_MB_DEFAULT))

print("")
print(("WALK OK" if not failed else "WALK RED") + " S615: %d passed, %d failed" % (len(passed), len(failed)))
sys.exit(0 if not failed else 1)
