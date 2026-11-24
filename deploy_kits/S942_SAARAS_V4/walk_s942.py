#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s942.py -- kit S942: the built call_transcription.py against the live bytes. No network, no key, nothing written.
    python3 walk_s942.py <call_transcription.py FROM (live)> <call_transcription.py TO (the kit's)>
  Checks: the TO carries saaras:v4 and no saaras:v3 anywhere; the two files differ in exactly the two lines the kit names; both
  doors (transcribe / create_job) still read SARVAM_MODEL; mode/language/codec untouched; the TO compiles.
  --control: the TO is the FROM (nothing changed) -> must go red.           Last line: WALK n/n
"""
import difflib
import py_compile
import re
import sys

n = 0
f = 0


def ok(name, cond):
    global n, f
    n += 1
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        f += 1


def main():
    src, dst = sys.argv[1], sys.argv[2]
    control = "--control" in sys.argv
    if control:
        dst = src
    a = open(src, encoding="utf-8").read()
    b = open(dst, encoding="utf-8").read()
    m = re.search(r'^SARVAM_MODEL = "([^"]+)"', b, re.M)
    ok("TO names the model saaras:v4", bool(m) and m.group(1) == "saaras:v4")
    ok("TO has no saaras:v3 left (as a model string)", '"saaras:v3"' not in b)
    changed = [ln for ln in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0)
               if (ln.startswith("+") or ln.startswith("-")) and not ln.startswith(("+++", "---"))]
    ok("exactly two lines removed and two added (the model line, the docstring word)", len(changed) == 4)
    ok("the removed lines are the v3 model line and the docstring line",
       sorted(x[1:].strip()[:22] for x in changed if x.startswith("-")) == sorted(['SARVAM_MODEL = "saaras', "link-expiry risk), sen"]))
    ok("the short door still sends model=SARVAM_MODEL", "speech_to_text.transcribe(" in b and "model=SARVAM_MODEL" in b)
    ok("the batch door still sends model=SARVAM_MODEL", "speech_to_text_job.create_job(" in b and b.count("model=SARVAM_MODEL") == 2)
    ok("mode transcribe, language unknown, codec map untouched",
       'SARVAM_MODE = "transcribe"' in b and 'SARVAM_LANGUAGE = "unknown"' in b and a.split("CODEC_MAP")[1][:200] == b.split("CODEC_MAP")[1][:200])
    ok("the short-call threshold and the batch chunk untouched", "SHORT_CALL_THRESHOLD_S = 30" in b and "BATCH_CHUNK = 20" in b)
    try:
        import os, tempfile
        d = tempfile.mkdtemp(prefix="w942_")
        py_compile.compile(dst, cfile=os.path.join(d, "x.pyc"), doraise=True)
        comp = True
    except Exception:  # noqa: BLE001
        comp = False
    ok("TO compiles", comp)
    print("WALK %d/%d" % (n - f, n))
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
