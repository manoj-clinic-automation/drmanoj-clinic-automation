#!/usr/bin/env python3
"""
peek_callhook.py - safely inspect captured MyOperator call webhooks.

WHAT IT DOES
  Reads the raw capture log written by call_hook_capture.py, MASKS any patient
  phone number, and prints the most recent "Call Ended" (call.end) body so the
  field NAMES and structure can be confirmed -- WITHOUT any patient data leaving
  the VPS. Also tells you if nothing has landed yet.

  Masking rule: any run of 7 or more consecutive digits (a phone number) becomes
  '#' characters. Short digit groups -- years, seconds, durations, dotted
  session ids, the row-id prefix of our reference_id -- stay intact, so the
  structure is still fully readable.

RUN
  /root/wa/venv/bin/python3 peek_callhook.py
  (optional) point at a different folder:
  /root/wa/venv/bin/python3 peek_callhook.py /some/other/log/dir
"""

import json
import re
import glob
import os
import sys

LOG_DIR = sys.argv[1] if len(sys.argv) > 1 else "/root/wa/call-hook/call_hook_logs"


def mask(s):
    """Replace any run of 7+ digits (phone numbers) with '#'; keep short groups."""
    return re.sub(r"\d{7,}", lambda m: "#" * len(m.group()), s)


def event_of(row):
    return (row.get("event_type") or "").strip()


def is_kind(row, *needles):
    et = event_of(row).lower()
    return any(n in et for n in needles)


def main():
    files = sorted(glob.glob(os.path.join(LOG_DIR, "*.jsonl")))
    if not files:
        print("No capture log yet in:", LOG_DIR)
        print("-> The webhook has not delivered anything. Waiting for a real call.")
        return

    f = files[-1]
    rows = []
    with open(f, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass

    tally = {}
    for r in rows:
        et = event_of(r) or "(none)"
        tally[et] = tally.get(et, 0) + 1

    print("Log file      :", f)
    print("Events in file:", len(rows))
    for et in sorted(tally):
        print("   %-18s %d" % (et, tally[et]))
    print()

    if not rows:
        print("File exists but no events captured yet. Waiting for a real call.")
        return

    ended = [r for r in rows if is_kind(r, "end")]
    summ = [r for r in rows if is_kind(r, "summary")]
    pick = ended or summ or rows        # prefer call.end, then call.summary
    chosen = pick[-1]
    body = chosen.get("body", {})

    print("=== Most recent '%s' body (patient number masked with #) ===" % (event_of(chosen) or "call"))
    print("=== Safe to paste to Claude -- the field NAMES are what matter. ===")
    print()
    print(mask(json.dumps(body, indent=2, ensure_ascii=False)))


if __name__ == "__main__":
    main()
