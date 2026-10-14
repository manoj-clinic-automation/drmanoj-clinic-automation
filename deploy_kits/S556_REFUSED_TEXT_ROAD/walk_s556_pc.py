#!/usr/bin/env python3
"""walk_s556_pc.py -- kit S556_REFUSED_TEXT_ROAD (14-Oct-2026): the medical side's walk (brief s3.1). Runs on manojz, never on the medical PC.
    python -B walk_s556_pc.py --new <the kit's marg_watch.py> --old <S491's marg_watch.py (S488)> --reader <S546's marg_txt.py>
                              --work <an empty scratch folder inside the repository's _scratch>
Each watcher is COPIED OUT into its own folder under --work beside a copy of the reader, and run there as a subprocess with python -B -I
(never imported from the kit folder; no marg_push.py beside it, so no made-up note can reach the server; TEMP/TMP point inside --work).
  A  the new watcher's own --selftest: every earlier check green beside the reader S546, and the S556 checks (1)-(5) green.
  B  CONTROL (6): the OLD watcher, with the same made-up texts and stub readers: after the stub swap its capture_text of each refused copy
     takes nothing -- RED (the fault F-893: a mended reader is not offered a refused text until a restart); it has no reader_changed_retry.
     The same steps on the NEW watcher, through reader_changed_retry, take the fresh text -- green.
  C  the files in Drive's FromMedical keep their mtimes across A and B (the selftest's _from_medical answers None).
Prints state names, md5 keys and check names only -- never a text, a reason body or a line of a file. 'WALK OK S556 PC' on success."""
import argparse
import os
import re
import shutil
import subprocess
import sys

OUT, FAILS = [], []

CONTROL = r'''
import hashlib, os, sys, time
sys.path.insert(0, sys.argv[1])
import marg_watch as W
W.NOTE_SINK = []
W._from_medical = lambda: None
W.TXT_LIVE_FORCE = True
base = sys.argv[2]
stubs, watched, spool = os.path.join(base, "stubs"), os.path.join(base, "watched"), os.path.join(base, "_spool")
for p in (stubs, watched):
    os.makedirs(p)
rp = os.path.join(stubs, "marg_txt.py")
REFUSE = ("VERSION = 'S556 stub: refuses'\ndef recognise(raw):\n    return raw.startswith(b'S556 MADE-UP TEXT')\n"
          "def convert(raw, exported_at=None):\n    raise ValueError('line 7: a made-up refusal')\n")
TAKE = ("VERSION = 'S556 stub: converts'\nimport hashlib\ndef recognise(raw):\n    return raw.startswith(b'S556 MADE-UP TEXT')\n"
        "def convert(raw, exported_at=None):\n    return b'\\xd0\\xcf\\x11\\xe0S556' + hashlib.md5(raw).digest(), {'version': VERSION}\n")
T0 = time.time()
def put(src, t):
    with open(rp, "w", encoding="utf-8") as fh:
        fh.write(src)
    os.utime(rp, (t, t))
sys.path.insert(0, stubs)
sys.modules.pop("marg_txt", None)
W._MT["mod"], W._MT["mtime"] = None, None
put(REFUSE, T0 - 600)
cap, logs = set(), []
texts = []
for name, tag in (("report_a.txt", b"FRESH"), ("report_b.txt", b"OLDER")):
    p = os.path.join(watched, name)
    with open(p, "wb") as fh:
        fh.write(b"S556 MADE-UP TEXT " + tag + b"\r\nno person, no number\r\n")
    texts.append(p)
    W.capture_text(p, spool, cap, logs.append)
ref = os.path.join(base, "_captured_txt", "refused")
kept = sorted(os.path.join(ref, n) for n in os.listdir(ref) if n.endswith(".txt") and not n.endswith(".why.txt"))
print("STATE kept %d refused copies (md5 keys %s)" % (len(kept), ", ".join(hashlib.md5(open(k, "rb").read()).hexdigest()[:8] for k in kept)))
older = hashlib.md5(open(texts[1], "rb").read()).hexdigest()
for k in kept:                                    # as in the selftest's (1): one of the two was refused four days ago
    if older in os.path.basename(k):
        os.utime(k, (T0 - 4 * 86400, T0 - 4 * 86400))
has = hasattr(W, "reader_changed_retry")
if has:
    W.reader_change_start(False, reader_path=rp)
put(TAKE, T0 - 300)
if has:
    took = [W.reader_changed_retry(spool, cap, logs.append, reader_path=rp, now=T0), W.reader_changed_retry(spool, cap, logs.append, reader_path=rp, now=T0 + 10)]
    print("STATE reader_changed_retry %s" % took)
for k in kept:                                    # what a later sweep or the census would do with the refused copies, without a restart
    print("STATE capture_text of a refused copy %s -> %s" % (hashlib.md5(open(k, "rb").read()).hexdigest()[:8], W.capture_text(k, spool, cap, logs.append)))
xls = [n for n in os.listdir(spool) if n.endswith(".XLS")] if os.path.isdir(spool) else []
print("RESULT has_reader_changed_retry=%s taken=%d" % (has, len(xls)))
'''


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    say(("  ok   " if cond else "  FAIL ") + label + (("   [%s]" % str(got)[:300]) if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def fm_dir():
    for L in "DEFGHIJKLMNOPQRSTUVWXYZ":
        p = "%s:\\My Drive\\Clinic Data Archive\\FromMedical" % L
        if os.path.isdir(p):
            return p
    return None


def mtimes(d):
    out = {}
    if not d:
        return out
    for root, _dirs, names in os.walk(d):
        for n in names:
            p = os.path.join(root, n)
            try:
                out[p] = os.path.getmtime(p)
            except OSError:
                pass
    return out


def run(args, work, cwd):
    env = dict(os.environ, TEMP=os.path.join(work, "tmp"), TMP=os.path.join(work, "tmp"), PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    p = subprocess.run([sys.executable, "-B", "-I"] + args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, encoding="utf-8", errors="replace", timeout=900)
    return p.returncode, p.stdout


def main():
    ap = argparse.ArgumentParser()
    for k in ("--new", "--old", "--reader", "--work"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    work = os.path.abspath(a.work)
    here = os.path.dirname(os.path.abspath(__file__))
    assert not os.path.exists(work) or not os.listdir(work), "--work must be empty: %s" % work
    assert os.path.normcase(work) != os.path.normcase(here), "--work is the kit folder"
    os.makedirs(os.path.join(work, "tmp"), exist_ok=True)
    folders = {}
    for side, src in (("new", a.new), ("old", a.old)):
        d = os.path.join(work, side)
        os.makedirs(d)
        shutil.copyfile(src, os.path.join(d, "marg_watch.py"))
        shutil.copyfile(a.reader, os.path.join(d, "marg_txt.py"))
        folders[side] = d
    fm = fm_dir()
    before = mtimes(fm)
    say("-- S556 PC walk: watchers copied out to %s (new / old), each beside the reader S546; Drive FromMedical %s (%d files)"
        % (work, "found" if fm else "not on this PC", len(before)))
    # A ------------------------------------------------------------------------------------------------------------------------------
    rc, out = run([os.path.join(folders["new"], "marg_watch.py"), "--selftest"], work, folders["new"])
    lines = out.splitlines()
    for l in lines:
        if "S556" in l or "FAIL" in l or l.startswith("SELFTEST"):
            say("   " + l.strip())
    fails = [l for l in lines if l.strip().startswith("FAIL")]
    s556 = [l for l in lines if l.strip().startswith("OK") and "S556" in l]
    earlier = [l for l in lines if l.strip().startswith("OK") and "S556" not in l]
    check("A: the new watcher's --selftest: SELFTEST OK, no FAIL (%d earlier checks green beside the reader S546)" % len(earlier),
          rc == 0 and "SELFTEST OK" in out and not fails and len(earlier) >= 50, (rc, fails[:3], out[-400:] if rc else ""))
    check("A: the S556 checks green -- marg_push not importable, (1) taken N=1 K=1, (2) quiet, (3a) no duplicate, (3) broken then good, "
          "(4) off / on / off at start, (5) not re-opened (%d of 11)" % len(s556), len(s556) == 11, s556)
    # B ------------------------------------------------------------------------------------------------------------------------------
    res = {}
    for side in ("old", "new"):
        base = os.path.join(work, "control_" + side)
        os.makedirs(base)
        cpath = os.path.join(work, "control.py")
        with open(cpath, "w", encoding="utf-8") as fh:
            fh.write(CONTROL)
        rc, out = run([cpath, folders[side], base], work, work)
        for l in out.splitlines():
            if l.startswith(("STATE", "RESULT")):
                say("   %s: %s" % (side, l))
        m = re.search(r"RESULT has_reader_changed_retry=(\w+) taken=(\d+)", out)
        res[side] = (rc, m.group(1) if m else None, int(m.group(2)) if m else -1, out[-300:] if not m else "")
    old_red = res["old"][0] == 0 and res["old"][1] == "False" and res["old"][2] == 0
    say("  RED on the old watcher (S488 0a78ae15): after the reader is mended, the refused copies are taken: %d -- it has no reader_changed_retry"
        % res["old"][2] if old_red else "  the old watcher did NOT go red: %s" % (res["old"],))
    check("B: CONTROL -- the old watcher takes nothing after the reader swap (red, F-893 reproduced)", old_red, res["old"])
    check("B: the same steps on the new watcher -- reader_changed_retry takes the fresh text (green)",
          res["new"][0] == 0 and res["new"][1] == "True" and res["new"][2] == 1, res["new"])
    # C ------------------------------------------------------------------------------------------------------------------------------
    after = mtimes(fm)
    moved = sorted(os.path.basename(p) for p in before if p in after and after[p] != before[p])
    new_files = sorted(os.path.basename(p) for p in after if p not in before)
    watcher_names = [n for n in moved + new_files if n.startswith(("marg_text_census", "marg_watch_log")) or "refused_text" in n]
    say("   FromMedical across the walk: %d moved (%s), %d new -- the medical PC's own heartbeat and census may move during it"
        % (len(moved), ", ".join(moved[:6]) or "none", len(new_files)))
    check("C: nothing in Drive's FromMedical was written by this walk (the selftest's _from_medical answers None; no census or log copy moved)",
          not fm or not watcher_names, watcher_names)
    leak = re.search(r"\d{10}", "\n".join(OUT))
    check("static: the walk's own output holds no run of 10 digits", not leak)
    if FAILS:
        say("WALK RED S556 PC: %d check(s) failed" % len(FAILS))
        return 1
    say("WALK OK S556 PC: the new watcher's selftest (earlier checks + S556 (1)-(5)) green; the control red on the old watcher; FromMedical untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
