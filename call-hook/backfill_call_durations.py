#!/usr/bin/env python3
"""
backfill_call_durations.py - one-shot, idempotent Call_Durations backfill.
Session 138 companion to call_hook_capture.py v3.0.1.

WHAT IT DOES
  Reads EVERY raw webhook log (call_hook_logs/*.jsonl), runs each captured
  body through the SAME extract_record() the live receiver uses (imported,
  not copied), collapses call.end/call.summary pairs to one record per key
  (call.summary wins -- it is the most comprehensive), and APPENDS only the
  keys that are NOT already in the tab.

  It therefore repairs, in one run:
    - rows lost while v3.0's header self-heal was failing (11-Jul 23:34 ->
      the v3.0.1 restart), and
    - ALL historical incoming calls sitting in the raw logs since 03-Jul,
      which the v2 receiver deliberately skipped (D80; scope changed S138).

SAFETY
  - INSERT-ONLY. Rows already in the tab are never touched (existing OBD
    rows keep their values; one writer per table stays true -- this script
    runs once, while it runs it is the same writer lineage, and it cannot
    collide with the live receiver on an existing key).
  - Idempotent: run it twice, the second run inserts nothing.
  - --dry-run prints what WOULD be inserted, writes nothing.
  - Requires the phone10 header to exist (i.e. v3.0.1 restarted first).

RUN (on the VPS)
  /root/wa/venv/bin/python3 backfill_call_durations.py --dry-run
  /root/wa/venv/bin/python3 backfill_call_durations.py
"""

import os
import sys
import glob
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

# Reuse the live receiver's own config + extraction. Importing it also runs
# its startup connect; that is harmless (same degrade-safe path) but slow-ish,
# so we import the module and use its pieces directly.
import call_hook_capture as chc  # noqa: E402

RAW_DIR = chc.RAW_DIR
HEADER = chc.HEADER


def load_records():
    """Read every raw log, newest event wins per key (file order = time order;
    call.summary explicitly preferred over call.end at equal footing)."""
    records = {}          # key -> rec
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.jsonl")))
    lines = bad = 0
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    lines += 1
                    try:
                        wrapper = json.loads(line)
                    except ValueError:
                        bad += 1
                        continue
                    body = wrapper.get("body")
                    event_type = str(wrapper.get("event_type") or "")
                    rec = chc.extract_record(body, event_type)
                    if not rec:
                        continue
                    key = rec["client_ref_id"]
                    prev = records.get(key)
                    # summary beats end; otherwise later beats earlier
                    if prev and prev.get("source_event") == "call.summary" \
                            and rec.get("source_event") != "call.summary":
                        continue
                    records[key] = rec
        except OSError as e:
            print("skip %s: %s" % (fp, e))
    print("raw logs: %d files, %d lines (%d unparsable), %d extractable calls"
          % (len(files), lines, bad, len(records)))
    return records


def main():
    dry = "--dry-run" in sys.argv

    records = load_records()
    if not records:
        print("nothing extractable; done.")
        return 0

    ws = chc.store_handle()                      # connects; raises if it cannot
    header = ws.row_values(1)
    if "phone10" not in [h.strip().lower() for h in header]:
        print("ABORT: the tab has no 'phone10' header yet. Restart the "
              "v3.0.1 receiver first (its self-heal adds the column).")
        return 1

    existing = set(chc._store["index"].keys())
    new_keys = [k for k in records if k not in existing]
    n_in = sum(1 for k in new_keys if k.startswith("IN-"))
    n_obd = len(new_keys) - n_in
    print("already in tab: %d keys | to insert: %d (%d incoming, %d obd)"
          % (len(existing), len(new_keys), n_in, n_obd))

    if dry:
        for k in sorted(new_keys)[:15]:
            r = records[k]
            ph = r.get("phone10", "")
            print("  would insert %-34s %-9s %-8s talk=%s%s"
                  % (k, r.get("category"), r.get("status"),
                     r.get("customer_talk_duration"),
                     (" caller=...%s" % ph[-4:]) if ph else ""))
        if len(new_keys) > 15:
            print("  ... and %d more" % (len(new_keys) - 15))
        print("DRY RUN: nothing written.")
        return 0

    rows = [chc.record_to_row(records[k]) for k in sorted(new_keys)]
    if rows:
        ws.append_rows(rows, value_input_option="RAW")
    print("inserted %d rows. Done." % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
