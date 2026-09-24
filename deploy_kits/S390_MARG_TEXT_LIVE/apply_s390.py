#!/usr/bin/env python3
"""apply_s389.py -- kit S389_MARG_TEXT (F-619). Anchored on the medical PC's marg_watch.py f39ce036 (S381).

S390 (same day): marg_txt.py is re-read whenever it changes (an update needs no watcher restart).

THE OWNER, 24-Sep-2026: "There is some issue with Microsoft Office in the medical PC. So Excel is not being
exported. So either I export a text file or a PDF file as you deem to be okay."

The watcher now also takes Marg's one-click TEXT export (report*.txt, in every folder it watches and on the
top level of the backup stick). A text export it recognises -- the bill-wise sales statement with item
detail, complete to its End of Report -- is turned by marg_txt.py (NEW, beside it) into the same .XLS Marg's
Excel export is, and THAT goes into the spool: every reader downstream (the clinic server's door and books,
Dr Manoj's PC, the archive) sees exactly what it sees today. The text itself is kept beside the spool in
_captured_txt\ as the record of what was converted. Any other text file is left alone. Excel, PDF and
everything else are captured exactly as before.

  python3 apply_s389.py --src marg_watch.py --out DIR
"""
import argparse, hashlib, os
ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
s = open(a.src, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "f39ce03698576c7561e34afef0f3a137", "marg_watch.py is not f39ce036 (S381)"


def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not unique or absent: " + old[:80]
    s = s.replace(old, new)


rep('''OFF SWITCH (S259)''', '''MARG'S TEXT EXPORT (S389, 24-Sep-2026, F-619)
    With Office broken on the medical PC, Marg's Excel export stopped; its one-click text export
    (report.txt) does not need Office. A report*.txt in any watched folder is read by marg_txt.py:
    the bill-wise sales statement with item detail, complete to "End of Report", becomes the SAME
    .XLS Marg's Excel export is, and that is what is captured -- nothing downstream changes. The
    text is kept in _captured_txt\\\\ beside the spool. Any other text file is left alone.

OFF SWITCH (S259)''')

rep('''import argparse, hashlib, os, queue, shutil, sys, threading, time''',
    '''import argparse, hashlib, os, queue, re, shutil, sys, threading, time''')

rep('''PDF_MAGIC = (b"%PDF",)''', '''PDF_MAGIC = (b"%PDF",)
# S389 (F-619): Marg's text export. Only files Marg names this way are looked at; what is inside
# decides whether one is converted (marg_txt.recognise) -- a name alone never does.
TXT_NAME = re.compile(r"^report[^\\\\/]*\\.txt$", re.I)
TXT_SEEN = set()        # md5s of text already judged this run -- converted, or not ours
# HOLD BY DEFAULT: a converted text export goes to _captured_txt\\held\\ and NOTHING is sent, until
# D:\\SendToClinic\\MARG_TXT_LIVE.txt exists and begins with LIVE. Being the default, the hold cannot
# be skipped by files arriving in the wrong order. A text held once is never sent later.
TXT_LIVE_FILE = os.path.join(HERE, "MARG_TXT_LIVE.txt")
TXT_LIVE_FORCE = None   # the selftest sets this; nothing else does


def txt_live():
    if TXT_LIVE_FORCE is not None:
        return TXT_LIVE_FORCE
    try:
        return open(TXT_LIVE_FILE, "rb").read(8).strip().upper().startswith(b"LIVE")
    except OSError:
        return False''')

rep('''            if not n.lower().endswith(EXTS):
                continue
            p = os.path.join(root, n)''', '''            if not (n.lower().endswith(EXTS) or TXT_NAME.match(n)):
                continue
            p = os.path.join(root, n)''')

rep('''            files += [os.path.join(dirpath, n) for n in names if n.lower().endswith(EXTS)]''',
    '''            files += [os.path.join(dirpath, n) for n in names
                      if n.lower().endswith(EXTS) or TXT_NAME.match(n)]''')

rep('''                if name.lower().endswith(EXTS):
                    evq.put(os.path.join(root, name))''', '''                if name.lower().endswith(EXTS) or TXT_NAME.match(os.path.basename(name)):
                    evq.put(os.path.join(root, name))''')

rep('''def capture(path, spool, captured, out):
    """Copy the bytes into the spool, keyed by content. True if NEW."""
    if not looks_complete(path):''', '''_MT = {"mtime": None, "mod": None}


def _marg_txt():
    """S390: marg_txt.py, re-read whenever the file beside this one changes -- an update to the
    reader delivered down the kit channel takes effect at once, without a watcher restart."""
    import importlib
    p = os.path.join(HERE, "marg_txt.py")
    m = os.path.getmtime(p)
    if _MT["mod"] is None:
        import marg_txt
        _MT["mod"], _MT["mtime"] = marg_txt, m
    elif m != _MT["mtime"]:
        _MT["mod"] = importlib.reload(_MT["mod"])
        _MT["mtime"] = m
    return _MT["mod"]


def capture_text(path, spool, captured, out):
    """S389: a Marg text export -> the same .XLS Marg's Excel export is, into the spool. True if NEW."""
    try:
        s1 = os.path.getsize(path)
        time.sleep(SETTLE_MS / 1000.0)
        if s1 <= 0 or os.path.getsize(path) != s1:
            return False                        # still being written; the next sweep takes it
        raw = open(path, "rb").read()
    except OSError:
        return False
    tmd5 = hashlib.md5(raw).hexdigest()
    if tmd5 in TXT_SEEN:
        return False
    try:
        marg_txt = _marg_txt()
    except Exception as ex:                                     # noqa: BLE001
        if "no-marg_txt" not in TXT_SEEN:       # said once; the file is tried again every sweep, so a
            TXT_SEEN.add("no-marg_txt")         # text export waits for marg_txt.py rather than being lost
            out("  ! marg_txt.py is not here yet (%s) -- text exports wait for it" % ex.__class__.__name__)
        return False
    if not marg_txt.recognise(raw):
        return False                            # not a complete bill-wise text export (yet, or ever)
    try:
        xls, info = marg_txt.convert(raw)
    except Exception as ex:                                     # noqa: BLE001
        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        TXT_SEEN.add(tmd5)
        return False
    digest = hashlib.md5(xls).hexdigest()
    TXT_SEEN.add(tmd5)
    if digest in captured:
        return False
    keep = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt")
    held = os.path.join(keep, "held")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    slot = os.path.splitext(os.path.basename(path))[0] + "_TXT"
    try:
        if os.path.isdir(held) and any(tmd5 in n for n in os.listdir(held)):
            return False                        # held once -> never sent
        if not txt_live():
            os.makedirs(held, exist_ok=True)
            with open(os.path.join(held, "%s__%s__%s.txt" % (stamp, slot, tmd5)), "wb") as fh:
                fh.write(raw)
            with open(os.path.join(held, "%s__%s__%s__%s.XLS" % (stamp, slot, tmd5, digest[:8])), "wb") as fh:
                fh.write(xls)
            out("  = HELD %s (text) -> _captured_txt\\held  (the text reader is on hold; nothing sent)"
                % os.path.basename(path))
            return False
    except OSError as ex:
        out("  ! text export hold failed (busy?), will retry: %s" % ex)
        TXT_SEEN.discard(tmd5)
        return False
    try:
        os.makedirs(spool, exist_ok=True)
        os.makedirs(keep, exist_ok=True)
        with open(os.path.join(keep, "%s__%s__%s.txt" % (stamp, slot, tmd5[:8])), "wb") as fh:
            fh.write(raw)
        dest = os.path.join(spool, "%s__%s__%s.XLS" % (stamp, slot, digest[:8]))
        tmp = dest + ".part"
        with open(tmp, "wb") as fh:
            fh.write(xls)
        os.replace(tmp, dest)
    except OSError as ex:
        out("  ! text export copy failed (busy?), will retry: %s" % ex)
        TXT_SEEN.discard(tmd5)
        return False
    captured.add(digest)
    out("  + CAPTURED %s (text) -> %s  (converted by marg_txt %s)" % (os.path.basename(path),
                                                                     os.path.basename(dest), info.get("version")))
    PUSH_WAKE.set()
    return True


def capture(path, spool, captured, out):
    """Copy the bytes into the spool, keyed by content. True if NEW."""
    if path.lower().endswith(".txt"):
        return capture_text(path, spool, captured, out)        # S389
    if not looks_complete(path):''')

rep('''    shutil.rmtree(d, ignore_errors=True)
    out("SELFTEST " + ("OK" if ok else "FAILED"))''', '''
    # S389: Marg's text export -- taken as the .XLS it becomes (when live); anything else in a .txt is not
    try:
        import marg_txt
        T = marg_txt.SELFTEST_SAMPLE
        tdir = os.path.join(d, "txt"); os.makedirs(os.path.join(tdir, "17476"))
        rpt = os.path.join(tdir, "17476", "report.txt"); open(rpt, "wb").write(T)
        other = os.path.join(tdir, "17476", "report_notes.txt"); open(other, "wb").write(b"a note, not a report")
        cut = os.path.join(tdir, "report2.txt"); open(cut, "wb").write(T[:-40])
        sp2 = os.path.join(d, "spool2"); cap2 = prime_captured(sp2)
        global TXT_LIVE_FORCE
        TXT_LIVE_FORCE = False
        hold_took = capture(rpt, os.path.join(d, "spool_h"), set(), lambda m: None)
        hd = os.path.join(d, "_captured_txt", "held")
        ck("ON HOLD (the default): converted and kept aside, nothing in the spool",
           hold_took is False and not os.path.isdir(os.path.join(d, "spool_h"))
           and len([f for f in os.listdir(hd) if f.endswith(".XLS")]) == 1)
        TXT_SEEN.clear(); TXT_LIVE_FORCE = True
        ck("a text held once is never sent, even when the reader goes live",
           capture(rpt, os.path.join(d, "spool_h"), set(), lambda m: None) is False)
        import shutil as _sh; _sh.rmtree(os.path.join(d, "_captured_txt")); TXT_SEEN.clear()
        got = [p for p in list_exports([tdir], flat=[]) if p.lower().endswith(".txt")]
        ck("a text export in a watched folder is found (report*.txt only)", len(got) == 3)
        took = [capture(p, sp2, cap2, lambda m: None) for p in sorted(got)]
        xs = [f for f in os.listdir(sp2) if f.endswith(".XLS")]
        ck("the complete bill-wise text is taken as ONE .XLS; the note and the cut-off one are not",
           took.count(True) == 1 and len(xs) == 1 and "_TXT__" in xs[0])
        want = hashlib.md5(marg_txt.convert(T)[0]).hexdigest()
        ck("what is in the spool is exactly marg_txt's .XLS", md5_of(os.path.join(sp2, xs[0])) == want)
        ck("the text itself is kept beside the spool",
           len([f for f in os.listdir(os.path.join(d, "_captured_txt")) if f.endswith(".txt")]) == 1)
        TXT_SEEN.clear()
        ck("taking it again (a restart) adds nothing", capture(rpt, sp2, prime_captured(sp2), lambda m: None) is False
           and len([f for f in os.listdir(sp2) if f.endswith(".XLS")]) == 1)
        open(cut, "wb").write(T.replace(b"TEST ONE", b"TEST 1ST"))
        ck("the cut-off one, once Marg finishes writing it, is taken", capture(cut, sp2, cap2, lambda m: None) is True)
        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))
        TXT_LIVE_FORCE = None
    except ImportError:
        ck("marg_txt.py is beside this file", False)
    shutil.rmtree(d, ignore_errors=True)
    out("SELFTEST " + ("OK" if ok else "FAILED"))''')

os.makedirs(a.out, exist_ok=True)
open(os.path.join(a.out, "marg_watch.py"), "w", encoding="utf-8", newline="\n").write(s)
print("marg_watch.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())
