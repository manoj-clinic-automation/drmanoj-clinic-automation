#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s944.py -- kit S944 on made-up rows. No network, no key, nothing written.
    python3 walk_s944.py <call_transcription.py FROM (S942's)> <call_transcription.py TO (the kit's)> [--control]
  The two rules (skip_reason) and the settled/failed reading (load_done_keys with a stub tab) are lifted from the TO and run on
  made-up rows; the main loop carries the skip block before the download; the summary line; the model stays saaras:v4;
  the TO compiles. --control: the TO is the FROM -> red.   Last line: WALK n/n
"""
import difflib
import os
import py_compile
import re
import sys
import tempfile

n = f = 0


def ok(name, cond):
    global n, f
    n += 1
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        f += 1


def lift(src, start, end_marker):
    i = src.find(start)
    j = src.find(end_marker, i + 1) if i >= 0 else -1
    return src[i:j] if (i >= 0 and j > i) else ""


def main():
    src_p, dst_p = sys.argv[1], sys.argv[2]
    if "--control" in sys.argv:
        dst_p = src_p
    a = open(src_p, encoding="utf-8").read()
    b = open(dst_p, encoding="utf-8").read()
    ns = {"SHORT_CALL_THRESHOLD_S": 30}
    code = lift(b, "SKIP_NEVER_S = 10", "\n\n\ndef load_pending_recordings")
    try:
        exec(compile(code or "raise RuntimeError('no S944 here')", "lifted_s944", "exec"), ns)
        lifted = True
    except Exception:  # noqa: BLE001
        lifted = False
    ok("skip_reason and load_done_keys lifted from the TO", lifted and "skip_reason" in ns and "load_done_keys" in ns)
    sr = ns.get("skip_reason", lambda *a: "NO")
    ok("10 s, never failed: skipped (never sent)", sr(10, 0) == "too short (10 s or under): not sent")
    ok("3 s, refused on 20 days: skipped as never sent (the first rule wins)", sr(3, 20) == "too short (10 s or under): not sent")
    ok("11 s, never refused: sent", sr(11, 0) is None)
    ok("11 s, refused on 2 days: still sent", sr(11, 2) is None)
    ok("11 s, refused on 3 days: skipped, not re-tried", sr(11, 3) == "too short: Sarvam refused it on 3 days, not re-tried")
    ok("30 s, refused on 25 days: skipped", sr(30, 25) == "too short: Sarvam refused it on 25 days, not re-tried")
    ok("31 s, failed 25: sent (a long call goes to the batch door as before)", sr(31, 25) is None)
    ok("unknown duration: sent", sr(None, 99) is None)

    class Tab:
        def get_all_records(self):
            F = "transcribe: HTTP 500"
            return [{"Join Key": "k1", "Status": "done"},
                    {"Join Key": "k2", "Status": "failed", "Error": F, "Transcribed At": "2026-11-20 03:01:00"},
                    {"Join Key": "k2", "Status": "failed", "Error": F, "Transcribed At": "2026-11-21 03:01:00"},
                    {"Join Key": "k2", "Status": "failed", "Error": F, "Transcribed At": "2026-11-22 03:01:00"},
                    {"Join Key": "k2", "Status": "failed", "Error": F, "Transcribed At": "2026-11-22 14:10:00"},
                    {"Join Key": "k3", "Status": "skipped"},
                    {"Join Key": "k4", "Status": "failed", "Error": F, "Transcribed At": "2026-11-22 03:01:00"},
                    {"Join Key": "k4", "Status": "done"},
                    {"Join Key": "k5", "Status": "failed", "Error": "download: token expired", "Transcribed At": "2026-11-20 03:01:00"},
                    {"Join Key": "k5", "Status": "failed", "Error": "download: token expired", "Transcribed At": "2026-11-21 03:01:00"},
                    {"Join Key": "k5", "Status": "failed", "Error": "upload: quota", "Transcribed At": "2026-11-22 03:01:00"},
                    {"Join Key": "k6", "Status": "failed", "Error": F, "Transcribed At": "2026-11-22 09:00:00"},
                    {"Join Key": "k6", "Status": "failed", "Error": F, "Transcribed At": "2026-11-22 09:20:00"},
                    {"Join Key": "k6", "Status": "failed", "Error": F, "Transcribed At": "2026-11-22 09:40:00"}]
    try:
        settled, failed = ns["load_done_keys"](Tab())
    except Exception:  # noqa: BLE001
        settled, failed = set(), {}
    ok("done and skipped rows settle a key (k1, k3, k4)", settled == {"k1", "k3", "k4"})
    ok("Sarvam refusals counted as DAYS per key (k2: 3 days of 4 rows, k4: 1, k6: 1 day of 3 rows); Drive failures (k5) never count",
       failed == {"k2": 3, "k4": 1, "k6": 1})
    ok("the main loop asks skip_reason BEFORE the download and writes one 'skipped' row",
       re.search(r'skip_why = skip_reason\(parse_duration_to_seconds\(rec\.get\("Duration"\)\), failed_counts\.get\(key, 0\)\)[^\n]*\n'
                 r'\s+if skip_why:\n(?:[^\n]*\n){1,3}\s+append_transcript_row\(ws_transcripts, rec, "skipped", error=skip_why\)\n'
                 r'\s+skipped \+= 1\n\s+continue\n\s+ext = os\.path\.splitext', b) is not None)
    ok("main unpacks (done_keys, failed_counts)", "done_keys, failed_counts = load_done_keys(ws_transcripts)" in b)
    ok("the summary says skipped", 'print(f"  skipped     : {skipped}")' in b)
    ok("the model is still saaras:v4; mode, language, threshold untouched",
       'SARVAM_MODEL = "saaras:v4"' in b and 'SARVAM_MODE = "transcribe"' in b and 'SARVAM_LANGUAGE = "unknown"' in b and "SHORT_CALL_THRESHOLD_S = 30" in b)
    changed = [ln for ln in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0)
               if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]
    ok("the diff touches only the five anchored places (%d lines)" % len(changed), 30 <= len(changed) <= 40
       and not any("transcribe_sync" in x or "transcribe_batch" in x or "def extract_transcript" in x for x in changed))
    try:
        d = tempfile.mkdtemp(prefix="w944_")
        py_compile.compile(dst_p, cfile=os.path.join(d, "x.pyc"), doraise=True)
        comp = True
    except Exception:  # noqa: BLE001
        comp = False
    ok("TO compiles", comp)
    print("WALK %d/%d" % (n - f, n))
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
