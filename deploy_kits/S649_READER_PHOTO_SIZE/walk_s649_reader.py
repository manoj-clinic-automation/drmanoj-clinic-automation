#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s649_reader.py -- S649_READER_PHOTO_SIZE (F-1003): the scan app's reader (claude_reader.py) given made-up photos, run in
the SERVICE's python (the system python3 on the box: no Pillow) with TURN_PY = the python that has Pillow (the venv's). No key,
no call to the reading service, nothing sent: only _block() -- what would be sent -- is looked at. Made-up images only, in a
scratch folder removed at the end.

    python3 -B walk_s649_reader.py --files <folder holding claude_reader.py> --service-py <python> --turn-py <python with Pillow>
                                   [--expect-red]
"""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


FILES, SPY, TPY = opt("--files"), opt("--service-py", "python3"), opt("--turn-py", "/root/wa/venv/bin/python3")
EXPECT_RED = "--expect-red" in ARGS
MUST_RED = ("A0", "C1", "C7", "C8", "C9")   # the control on the live reader (S550.2): the version and the shrinks red; every other green
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:300]) if (d and not ok) else ""))


MAKE = r"""
import os, sys
from PIL import Image
d = sys.argv[1]
def noise(w, h):
    return Image.frombytes("RGB", (w, h), os.urandom(w * h * 3))
noise(2600, 3400).save(os.path.join(d, "big.jpg"), "JPEG", quality=92)        # a made-up phone photo well over the limit
noise(1800, 1500).save(os.path.join(d, "big.png"), "PNG")                      # a PNG over the limit
noise(600, 800).save(os.path.join(d, "small.jpg"), "JPEG", quality=80)          # under the limit
noise(2200, 2250).save(os.path.join(d, "MID.JPG"), "JPEG", quality=92)          # in the reported 4-5.5 MB range, an upper-case name
"""

PROBE = r"""
import base64, hashlib, json, sys
sys.path.insert(0, sys.argv[1])
import claude_reader as c
out = {"version": c.VERSION, "pil_here": True, "max": c.IMAGE_MAX}
try:
    import PIL  # noqa
except ImportError:
    out["pil_here"] = False
for name in sys.argv[3:]:
    p = sys.argv[2] + "/" + name
    before = hashlib.md5(open(p, "rb").read()).hexdigest()
    try:
        blk, why = c._block(p)
    except Exception as e:
        out[name] = {"exc": repr(e)}
        continue
    r = {"why": why, "same_file": hashlib.md5(open(p, "rb").read()).hexdigest() == before}
    if blk:
        raw = base64.b64decode(blk["source"]["data"])
        r.update(type=blk["type"], media=blk["source"]["media_type"], n=len(raw), md5=hashlib.md5(raw).hexdigest(), head=raw[:3].hex(),
                 orig_md5=before)
        open(sys.argv[2] + "/sent_" + name, "wb").write(raw)           # what would be sent -- measured by the python with Pillow
    out[name] = r
print(json.dumps(out))
"""

work = tempfile.mkdtemp(prefix="s649walk_")
try:
    img = os.path.join(work, "img")
    os.makedirs(img)
    subprocess.run([TPY, "-I", "-c", MAKE, img], check=True, timeout=300)
    with open(os.path.join(img, "bill.pdf"), "wb") as fh:                      # a made-up PDF (no person, no supplier)
        fh.write(b"%PDF-1.4\n% made-up S649 walk\n" + b"0" * 5_000_000 + b"\n%%EOF\n")
    with open(os.path.join(img, "broken.jpg"), "wb") as fh:                    # not a photo at all, over the limit
        fh.write(os.urandom(4_500_000))
    sizes = {f: os.path.getsize(os.path.join(img, f)) for f in os.listdir(img)}
    code = os.path.join(work, "code")
    os.makedirs(code)
    shutil.copy(os.path.join(FILES, "claude_reader.py"), code)

    def probe(turn_py, *names):
        env = dict(os.environ, S618_TURN_PY=turn_py, SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "nokey"),
                   SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1")
        for k in ("ANTHROPIC_API_KEY", "PYTHONPATH"):
            env.pop(k, None)
        r = subprocess.run([SPY, "-B", "-c", PROBE, code, img] + list(names), env=env, capture_output=True, text=True, timeout=300, cwd=work)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-500:])
        return json.loads(r.stdout.strip().splitlines()[-1])

    P = probe(TPY, "big.jpg", "big.png", "small.jpg", "bill.pdf", "broken.jpg", "MID.JPG")
    N = probe(os.path.join(work, "no_such_python"), "big.jpg")
    LIM = P["max"]
    DIMS = json.loads(subprocess.run([TPY, "-I", "-c", "import json,sys,os\nfrom PIL import Image\nd=sys.argv[1]\n"
                                      "print(json.dumps({f[5:]: list(Image.open(os.path.join(d,f)).size) for f in os.listdir(d) if f.startswith('sent_') and not f.endswith('.pdf')}))", img],
                                     capture_output=True, text=True, timeout=120).stdout or "{}")
    print("    made-up files: " + ", ".join("%s %.1f MB" % (k, v / 1e6) for k, v in sorted(sizes.items())) +
          " · the service python has Pillow: %s · IMAGE_MAX %d" % (P["pil_here"], LIM))
    ck("A0 the reader is S649's (VERSION S550.3)", lambda: P["version"] == "S550.3", lambda: P["version"])
    b = P["big.jpg"]
    ck("C1 a made-up phone photo of %.1f MB (over the limit) goes to the reader as a smaller JPEG -- under IMAGE_MAX, longest side 2400 or less" % (sizes["big.jpg"] / 1e6),
       lambda: sizes["big.jpg"] > LIM and b.get("type") == "image" and b.get("media") == "image/jpeg" and b.get("head") == "ffd8ff" and 0 < b.get("n", 0) <= LIM
       and max(DIMS.get("big.jpg") or [9999]) <= 2400, lambda: (b, DIMS))
    ck("C2 the stored photo is never changed (its bytes the same after); only the copy for the reader is smaller",
       lambda: all(P[f].get("same_file") for f in ("big.jpg", "big.png", "small.jpg", "bill.pdf", "broken.jpg")), lambda: P)
    s = P["small.jpg"]
    ck("C3 a photo under the limit goes as it is -- byte for byte, its own type", lambda: s.get("md5") == s.get("orig_md5") and s.get("media") == "image/jpeg", lambda: s)
    d = P["bill.pdf"]
    ck("C4 a PDF goes as a document, byte for byte (no shrinking of PDFs)", lambda: d.get("type") == "document" and d.get("md5") == d.get("orig_md5"), lambda: d)
    if P["pil_here"]:
        ck("C5 (the service python HAS Pillow on this box: the photo is shrunk in process; the no-Pillow-anywhere case is walked where it has none)",
           lambda: N["big.jpg"].get("media") == "image/jpeg" and 0 < N["big.jpg"].get("n", 0) <= LIM, lambda: N)
    else:
        ck("C5 no python with Pillow anywhere: the photo is not sent -- 'photo too large to send', as before, no error",
           lambda: N["big.jpg"].get("why") == "photo too large to send" and "exc" not in N["big.jpg"], lambda: N)
    ck("C6 a broken 'photo' over the limit: 'photo too large to send', no error", lambda: P["broken.jpg"].get("why") == "photo too large to send", lambda: P["broken.jpg"])
    g = P["big.png"]
    ck("C7 a PNG of %.1f MB goes as a smaller JPEG under the limit" % (sizes["big.png"] / 1e6),
       lambda: sizes["big.png"] > LIM and g.get("media") == "image/jpeg" and 0 < g.get("n", 0) <= LIM, lambda: g)
    m = P["MID.JPG"]
    ck("C9 a photo of %.1f MB named MID.JPG (the size F-1003 met, an upper-case name) goes as a smaller JPEG under the limit" % (sizes["MID.JPG"] / 1e6),
       lambda: LIM < sizes["MID.JPG"] < 5_600_000 and m.get("media") == "image/jpeg" and 0 < m.get("n", 0) <= LIM and m.get("same_file"), lambda: m)
    enc = 4 * ((b.get("n") or 0) + 2) // 3
    ck("C8 once encoded, the smaller photo is under the reading service's 5 MB image limit (%d bytes)" % enc, lambda: (b.get("n") or 0) > 0 and enc <= 5 * 1024 * 1024)
finally:
    shutil.rmtree(work, ignore_errors=True)

red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S649 READER CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S649 READER: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
