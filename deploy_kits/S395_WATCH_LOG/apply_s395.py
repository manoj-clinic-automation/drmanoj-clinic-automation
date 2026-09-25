#!/usr/bin/env python3
"""apply_s395.py -- kit S395_WATCH_LOG (F-620). Anchored on the medical PC's marg_watch.py ce41fdaa (S390).

25-Sep-2026 ~05:30 IST the owner exported 24-Sep's bill-wise sale as text and it was not taken -- and there
was no way to see why: the agent starts the watcher with its output thrown away, and a text report the
reader turns down was neither kept nor explained.

  * Every message the watcher prints is also written to D:\\SendToClinic\\marg_watch.log (dated, capped at
    1 MB, the last 256 KB kept) -- the pull mirrors that folder to Dr Manoj's PC every ten minutes.
  * A report*.txt that is finished (its size holds still) but is NOT taken is copied, once, to
    _captured_txt\\refused\\ with a .why.txt beside it saying exactly why: not a bill-wise report, the
    header or the End of Report missing, or the reader's own refusal with the line it stopped at.
  * At start it says which reader it has and whether the text route is live.
Nothing about what is taken, or how, changes.

  python3 apply_s395.py --src marg_watch.py --out DIR
"""
import argparse, hashlib, os
ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
s = open(a.src, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "ce41fdaad2243f94274331b9cc940d80", "marg_watch.py is not ce41fdaa (S390)"


def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not unique or absent: " + old[:80]
    s = s.replace(old, new)


rep('''OFF SWITCH (S259)''', '''S395 (25-Sep-2026, F-620): everything this prints also goes to D:\\\\SendToClinic\\\\marg_watch.log, and a
    report*.txt that is finished but not taken is kept in _captured_txt\\\\refused\\\\ with the reason.

OFF SWITCH (S259)''')

rep('''    if not marg_txt.recognise(raw):
        return False                            # not a complete bill-wise text export (yet, or ever)
    try:
        xls, info = marg_txt.convert(raw)
    except Exception as ex:                                     # noqa: BLE001
        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        TXT_SEEN.add(tmd5)
        return False''', '''    if not marg_txt.recognise(raw):
        # S395: finished (size held still above) but not a report the reader knows -- keep it and say why,
        # once. A later, complete version has other bytes and is looked at afresh.
        _keep_refused(path, raw, tmd5, spool, out, _why_not(raw))
        TXT_SEEN.add(tmd5)
        return False
    try:
        xls, info = marg_txt.convert(raw)
    except Exception as ex:                                     # noqa: BLE001
        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        _keep_refused(path, raw, tmd5, spool, out, "the reader refused it: %s" % str(ex)[:400])
        TXT_SEEN.add(tmd5)
        return False''')

rep('''def capture_text(path, spool, captured, out):''', '''def _why_not(raw):
    """S395: the plain reason a finished report*.txt is not a report the reader takes."""
    try:
        t = raw.decode("latin-1")
    except Exception:                                           # noqa: BLE001
        return "cannot be read as text"
    head, tail = t[:4000], t[-400:]
    miss = []
    if "BILL WISE SALES STATEMENT" not in head:
        first = next((l.strip() for l in t.splitlines() if l.strip()), "")[:80]
        return "not a bill-wise sales statement (it begins: %r)" % first
    if "BILL NO." not in head or "CASH" not in head:
        miss.append("the column heads with CASH (is Report Type = Detail?)")
    if "*** End of Report ***" not in tail:
        miss.append("the '*** End of Report ***' line at the end (cut short?)")
    if len(raw) > 5 * 1024 * 1024:
        miss.append("a sensible size (over 5 MB)")
    return "a bill-wise report, but without " + "; ".join(miss) if miss else "not recognised"


def _keep_refused(path, raw, tmd5, spool, out, why):
    try:
        ref = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")
        os.makedirs(ref, exist_ok=True)
        if any(tmd5 in n for n in os.listdir(ref)):
            return
        stem = "%s__%s__%s" % (time.strftime("%Y%m%d-%H%M%S"), os.path.splitext(os.path.basename(path))[0], tmd5)
        with open(os.path.join(ref, stem + ".txt"), "wb") as fh:
            fh.write(raw)
        with open(os.path.join(ref, stem + ".why.txt"), "w", encoding="utf-8") as fh:
            fh.write("%s\\nfrom: %s\\nwhy:  %s\\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), path, why))
        out("  ! NOT TAKEN %s (text): %s -- kept in _captured_txt\\\\refused" % (os.path.basename(path), why))
    except OSError as ex:
        out("  ! could not keep the refused text %s: %s" % (os.path.basename(path), ex))


def capture_text(path, spool, captured, out):''')

rep('''    out = lambda m="": (print(m), sys.stdout.flush())''', '''    out = lambda m="": (print(m), sys.stdout.flush())
    if not a.selftest:
        out = _teed_out()                       # S395: the running watcher writes its log; a selftest does not''')

rep('''def main(argv=None):''', '''WATCH_LOG = os.path.join(HERE, "marg_watch.log")


def _teed_out():
    """S395: print, AND append to marg_watch.log -- the agent throws the watcher's own output away."""
    def out(m=""):
        try:
            print(m); sys.stdout.flush()
        except Exception:                                       # noqa: BLE001 -- pythonw has no console
            pass
        try:
            if os.path.exists(WATCH_LOG) and os.path.getsize(WATCH_LOG) > 1024 * 1024:
                with open(WATCH_LOG, "rb") as fh:
                    fh.seek(-256 * 1024, 2)
                    tail = fh.read()
                with open(WATCH_LOG, "wb") as fh:
                    fh.write(tail)
            with open(WATCH_LOG, "a", encoding="utf-8") as fh:
                fh.write("%s  %s\\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), m))
        except Exception:                                       # noqa: BLE001
            pass
    return out


def main(argv=None):''')

rep('''    watch(a.watch or DEFAULT_WATCH, a.spool, a.once, a.route, out, extra, a.poll)''', '''    try:
        _mt = _marg_txt().VERSION
    except Exception as ex:                                     # noqa: BLE001
        _mt = "absent (%s)" % ex.__class__.__name__
    out("marg_watch S395 starting -- text reader %s, text route %s" % (_mt, "LIVE" if txt_live() else "ON HOLD"))
    watch(a.watch or DEFAULT_WATCH, a.spool, a.once, a.route, out, extra, a.poll)''')

# selftest: the refusal is kept, with its reason
rep('''        ck("the cut-off one, once Marg finishes writing it, is taken", capture(cut, sp2, cap2, lambda m: None) is True)''',
    '''        ck("the cut-off one, once Marg finishes writing it, is taken", capture(cut, sp2, cap2, lambda m: None) is True)
        # S395: a finished report*.txt that is not taken is kept, with its reason
        TXT_SEEN.clear()
        odd = os.path.join(tdir, "report_odd.txt"); open(odd, "wb").write(T.replace(b"End of Report", b"End of Page"))
        msgs = []
        capture(odd, sp2, cap2, msgs.append)
        refd = os.path.join(d, "_captured_txt", "refused")
        whys = [f for f in os.listdir(refd) if f.endswith(".why.txt") and "report_odd" in f] if os.path.isdir(refd) else []
        ck("a finished report it will not take is KEPT, with the reason written beside it",
           len(whys) == 1 and "End of Report" in open(os.path.join(refd, whys[0]), encoding="utf-8").read()
           and any("NOT TAKEN" in m for m in msgs))
        capture(odd, sp2, cap2, msgs.append); TXT_SEEN.clear(); capture(odd, sp2, cap2, msgs.append)
        ck("...and only once, however often it is looked at",
           len([f for f in os.listdir(refd) if f.endswith(".why.txt") and "report_odd" in f]) == 1)''')

os.makedirs(a.out, exist_ok=True)
open(os.path.join(a.out, "marg_watch.py"), "w", encoding="utf-8", newline="\n").write(s)
print("marg_watch.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())
