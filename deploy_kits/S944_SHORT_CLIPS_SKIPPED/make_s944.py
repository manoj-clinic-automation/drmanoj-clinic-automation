#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s944.py -- kit S944 (the parent, S511, 24-Nov-2026): builds call_transcription.py (TO) from S942's bytes (FROM 6b72038d)
by four exact anchors -- the leftover loop (roadmap S510 A2, F-1633): a clip of 10 s or under is never sent (one 'skipped' row);
a clip of 30 s or under that Sarvam refused on three different days gets one 'skipped' row and is never re-tried; a 'skipped' row settles the call
like a 'done' one (the verdict stage already reads only 'done' rows -- nothing is judged). Nothing else moves.
    python3 make_s944.py <call_transcription.py FROM> <call_transcription.py TO>
"""
import ast
import hashlib
import sys

FROM_MD5 = "6b72038d666b83a48e20e1d56bbe8584"
A1 = '''def load_done_keys(ws_transcripts):
    """Join keys that already have a DONE row — these are skipped. FAILED rows are retried."""
    rows = ws_transcripts.get_all_records()
    return {r.get("Join Key") for r in rows if r.get("Status") == "done"}
'''
N1 = '''SKIP_NEVER_S = 10                 # S944 (F-1633): a clip this short is never sent -- one 'skipped' row
SKIP_AFTER_FAILS = 3              # S944: a clip of SHORT_CALL_THRESHOLD_S or under refused by Sarvam on this many DAYS is never re-tried


def skip_reason(secs, n_failed):
    """S944: why a call is written 'skipped' instead of being sent. None = send it."""
    if secs is None:
        return None
    if secs <= SKIP_NEVER_S:
        return f"too short ({SKIP_NEVER_S} s or under): not sent"
    if secs <= SHORT_CALL_THRESHOLD_S and n_failed >= SKIP_AFTER_FAILS:
        return f"too short: Sarvam refused it on {n_failed} days, not re-tried"
    return None


def load_done_keys(ws_transcripts):
    """Join keys that already have a DONE or SKIPPED row — these are settled; FAILED rows are retried (S944: a short clip only
    until Sarvam has refused it on SKIP_AFTER_FAILS different days -- a Drive failure or one bad hour never counts).
    Returns (settled_keys, refused_days: {key: number of days with a 'transcribe:' failure})."""
    rows = ws_transcripts.get_all_records()
    settled = {r.get("Join Key") for r in rows if r.get("Status") in ("done", "skipped")}
    days = {}
    for r in rows:
        if r.get("Status") == "failed" and str(r.get("Error") or "").startswith("transcribe:"):
            days.setdefault(r.get("Join Key"), set()).add(str(r.get("Transcribed At") or "")[:10])
    return settled, {k: len(v) for k, v in days.items()}
'''
A2 = '''    done_keys = load_done_keys(ws_transcripts)
'''
N2 = '''    done_keys, failed_counts = load_done_keys(ws_transcripts)              # S944: settled keys + how often each key failed
'''
A3 = '''    done = failed = 0
    long_calls = []  # (record, local_temp_path) for batch pass
'''
N3 = '''    done = failed = skipped = 0
    long_calls = []  # (record, local_temp_path) for batch pass
'''
A4 = '''            ext = os.path.splitext(rec.get("MyOperator Filename", ""))[1].lower() or ".mp3"
            local_path = os.path.join(tmpdir, f"{key}{ext}")
'''
N4 = '''            skip_why = skip_reason(parse_duration_to_seconds(rec.get("Duration")), failed_counts.get(key, 0))   # S944
            if skip_why:
                print(f"    SKIPPED ({skip_why})", flush=True)
                append_transcript_row(ws_transcripts, rec, "skipped", error=skip_why)
                skipped += 1
                continue
''' + A4
A5 = '''    print(f"  failed      : {failed}")
'''
N5 = A5 + '''    print(f"  skipped     : {skipped}")
'''


def main():
    src_p, dst_p = sys.argv[1], sys.argv[2]
    raw = open(src_p, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM_MD5:
        sys.exit("FROM is %s, not %s (S942's TO) -- read the live bytes first (F-472)" % (got[:8], FROM_MD5[:8]))
    t = raw.decode("utf-8")
    for a in (A1, A2, A3, A4, A5):
        if t.count(a) != 1:
            sys.exit("anchor not found exactly once: %r" % a[:60])
    for a, nw in ((A1, N1), (A2, N2), (A3, N3), (A4, N4), (A5, N5)):
        t = t.replace(a, nw)
    ast.parse(t)
    out = t.encode("utf-8")
    open(dst_p, "wb").write(out)
    print("TO %s (%d bytes)" % (hashlib.md5(out).hexdigest(), len(out)))


if __name__ == "__main__":
    main()
