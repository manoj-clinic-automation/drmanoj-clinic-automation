#!/usr/bin/env python3
"""cron_edit_s291.py -- rewrite root's crontab text for S291 (owner, 17-Sep-2026).

The Docterz day sheet reached Drive "by 09:20" when S238 scheduled the reader from 09:30. Since S239
the auto-pickup runs the tracker the moment an export settles on the owner's PC -- 22:25 on 14-Sep,
04:50 on 16-Sep, 05:05 on 17-Sep -- and Drive has the file within seconds, but the reader still
waited for 09:30. This replaces the FOUR S238 schedule lines with ONE line: the same command, every
10 minutes, all day. One writer, one source (Drive), unchanged.

Usage: cron_edit_s291.py IN OUT      (refuses unless exactly four S238 lines and no S291 line)
"""
import sys

OLD_TAG = "# S238_DOCTERZ_SCHEDULE"
CMD = ("flock -n /tmp/docterz_ingest.lock /root/wa/venv/bin/python3 -B /root/finance/docterz_ingest.py "
       ">> /root/finance/logs/docterz_ingest.log 2>&1")
NEW = "*/10 * * * * " + CMD + " # S291_DOCTERZ_EARLY every 10 min, all day (the pickup runs at night / at boot)"


def main(a, b):
    lines = open(a, encoding="utf-8").read().splitlines()
    old = [l for l in lines if OLD_TAG in l]
    if any("S291_DOCTERZ_EARLY" in l for l in lines):
        print("REFUSED: already carries S291")
        return 3
    if len(old) != 4 or not all(CMD in l for l in old):
        print("REFUSED: expected exactly four S238 lines running the same command, found %d" % len(old))
        return 1
    out, placed = [], False
    for l in lines:
        if OLD_TAG in l:
            if not placed:
                out.append(NEW)
                placed = True
            continue
        out.append(l)
    open(b, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("crontab: 4 S238 lines -> 1 S291 line; %d lines before, %d after" % (len(lines), len(out)))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
