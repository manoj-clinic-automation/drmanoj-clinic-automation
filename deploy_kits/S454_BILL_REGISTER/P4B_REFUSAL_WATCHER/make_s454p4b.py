#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p4b.py -- kit S454_BILL_REGISTER, part 4 -- the medical PC (S454 10.1): the watcher tells the owner when it refuses a file.
CLAUDE.md rule 2: built from the live watcher's bytes (S397, 81145aa7 -- the heartbeat's own md5 on 03-Oct), every anchor exactly once.

  marg_watch.py (S454)  * when a text is kept as refused (a reader's refusal, or a finished report it does not know) the watcher sends a note
                          -- the file's name, its md5, the kind it looked like (SALE, STOCK, ORDER) and the reason, never a line of the file --
                          to the server's marg-file door with the address and the key marg_push.py already uses (marg_push.py is not changed);
                          in its own daemon thread, so capture never waits; once per file (a file kept once is never kept, or noted, again);
                          not while sending is switched OFF (_off\\ALL_OFF.txt / MARG_PUSH_OFF.txt)
                        * a long digit run in the reason (a phone number on a letterhead) is masked before it leaves the PC
                        * "why not" learns Darpan's order sheet; an order sheet under another name than report*.txt is kept too
                        * the selftest proves the notes (collected, never sent, in the selftest)

    make_s454p4b.py --watch <marg_watch.py S397> --out DIR
"""
import argparse
import hashlib
import os

FROM = "81145aa7d7c8e9f7e23072cfab1ee620"

EDITS = [
    ('''OFF SWITCH (S259)
    D:\\\\SendToClinic\\\\_off\\\\MARG_WATCH_OFF.txt stops capture.''',
     '''S454 (03-Oct-2026, D648 -- "every duty has a door"): a text kept as refused is NOT silent any more. The watcher sends the server a
    note -- the file's name, its md5, the kind it looked like and the reason; never a line of the file -- with the address and the key
    marg_push.py already uses. The server writes one row "refused by the medical PC" and the owner's Needs-you, the reports tile and
    Darpan's order-sheet card name it. Once per file; not while the sending is switched off. "Why not" learns Darpan's order sheet.

OFF SWITCH (S259)
    D:\\\\SendToClinic\\\\_off\\\\MARG_WATCH_OFF.txt stops capture.'''),
    ('''import argparse, hashlib, os, queue, re, shutil, sys, threading, time
''',
     '''import argparse, hashlib, os, queue, re, shutil, sys, threading, time
import json, urllib.error, urllib.request                     # S454: the refusal note
'''),
    ('''    if "BILL WISE SALES STATEMENT" not in head:
        first = next((l.strip() for l in t.splitlines() if l.strip()), "")[:80]''',
     '''    if "PENDING ORDERS (PURCHASE)" in head:                                          # S454: Darpan's order sheet
        if "*** End of Report ***" not in tail:
            return "an order sheet without the '*** End of Report ***' line at the end (cut short?)"
        return "an order sheet the reader cannot take"
    if "BILL WISE SALES STATEMENT" not in head:
        first = next((l.strip() for l in t.splitlines() if l.strip()), "")[:80]'''),
    ('''        out("  ! NOT TAKEN %s (text): %s -- kept in _captured_txt\\\\refused" % (os.path.basename(path), why))
''',
     '''        out("  ! NOT TAKEN %s (text): %s -- kept in _captured_txt\\\\refused" % (os.path.basename(path), why))
        send_note(note_of(path, tmd5, raw, why), out)          # S454: the owner is told (once: a file kept once returns above)
'''),
    ('''CENSUS_EVERY_S = 600
''',
     '''# ------------------------------------------------------------------ S454: the note of a refused text
NOTE_SINK = None        # the selftest sets a list here: notes are collected there and never sent
NOTE_TRIES = 3
NOTE_GAP_S = 60
NOTE_KEYS = ("name", "md5", "kind", "reason")


def _kind_of(raw):
    head = raw[:4000].decode("latin-1", "replace")
    if "PENDING ORDERS (PURCHASE)" in head:
        return "ORDER"
    if "CLOSING STOCK" in head:
        return "STOCK"
    if "BILL WISE SALES STATEMENT" in head:
        return "SALE"
    return ""


def note_of(path, tmd5, raw, why):
    """The note: name, md5, kind, reason -- nothing of the file's content; a run of 6+ digits in the reason is masked."""
    reason = re.sub(r"\\d{6,}", "#", " ".join(str(why or "").split()))[:240]
    return {"name": os.path.basename(path)[:120], "md5": tmd5, "kind": _kind_of(raw), "reason": reason}


def send_note(note, out):
    if NOTE_SINK is not None:
        NOTE_SINK.append(dict(note))
        return "sink"
    try:
        threading.Thread(target=_send_note, args=(note, out), daemon=True, name="refusal_note").start()
        return "thread"
    except Exception as ex:                                     # noqa: BLE001 -- capture never fails for a note
        out("  note: could not start (%s) -- the refusal stays on this PC" % ex.__class__.__name__)
        return "no"


def _send_note(note, out):
    try:
        import marg_push as MP
    except Exception as ex:                                     # noqa: BLE001
        out("  note: marg_push.py is not here (%s) -- the refusal of %s stays on this PC" % (ex.__class__.__name__, note["name"]))
        return
    try:
        off = MP.off_marker()
        if off:
            out("  note: sending is OFF (%s) -- the refusal of %s stays on this PC" % (os.path.basename(off), note["name"]))
            return
        tok = MP.token()
        if not tok:
            out("  note: no key in token.txt -- the refusal of %s stays on this PC" % note["name"])
            return
        body = json.dumps(note).encode("utf-8")
        for i in range(NOTE_TRIES):
            req = urllib.request.Request(MP.URL, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-Finance-Marg", tok)
            req.add_header("X-Marg-Note", "refused")
            try:
                with urllib.request.urlopen(req, timeout=30, context=MP._ctx()) as r:
                    js = json.loads(r.read().decode("utf-8", "replace") or "{}")
                out("  note: the server has the refusal of %s (%s)" % (note["name"], js.get("status")))
                return
            except urllib.error.HTTPError as e:
                if e.code in (400, 401, 403, 404, 413):
                    out("  note: the server would not take the refusal of %s (HTTP %s)" % (note["name"], e.code))
                    return
            except Exception:                                   # noqa: BLE001 -- a dead line: try again shortly
                pass
            if i + 1 < NOTE_TRIES:
                time.sleep(NOTE_GAP_S)
        out("  note: the server could not be reached for %s -- the refusal stays on this PC" % note["name"])
    except Exception as ex:                                     # noqa: BLE001
        out("  note: %s -- the refusal of %s stays on this PC" % (ex.__class__.__name__, note.get("name")))


CENSUS_EVERY_S = 600
'''),
    ('''        if REPORTISH.match(os.path.basename(path)) or b"STATEMENT" in raw[:4000]:''',
     '''        if REPORTISH.match(os.path.basename(path)) or b"STATEMENT" in raw[:4000] or b"PENDING ORDERS" in raw[:4000]:   # S454: + order sheet'''),
    ('''    """Proves the thing that matters: an OVERWRITTEN export is still kept."""
    import tempfile
    ok = True
''',
     '''    """Proves the thing that matters: an OVERWRITTEN export is still kept."""
    import tempfile
    global NOTE_SINK
    NOTE_SINK = []                                              # S454: notes are collected, never sent, in the selftest
    ok = True
'''),
    ('''        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))''',
     '''        # S454: the note of a refused text -- once per file, no content, the kind it looked like
        odd_md5 = hashlib.md5(open(odd, "rb").read()).hexdigest()
        mine = [n for n in NOTE_SINK if n["md5"] == odd_md5]
        ck("S454: the refused sale text sent ONE note (name, md5, kind SALE, reason) however often it was looked at",
           len(mine) == 1 and sorted(mine[0]) == sorted(NOTE_KEYS) and mine[0]["kind"] == "SALE" and "End of Report" in mine[0]["reason"])
        lines = [l.strip() for l in open(odd, "rb").read().decode("latin-1").splitlines() if len(l.strip()) >= 12]
        ck("S454: the note carries no line of the file", not [l for l in lines if any(l in str(v) for v in mine[0].values())])
        n_before = len(NOTE_SINK)
        TXT_SEEN.clear(); TXT_STAT.clear()
        retry_refused(sp2, cap2, lambda m: None)
        ck("S454: offering the refused texts again at a start sends no note again", len(NOTE_SINK) == n_before)
        OS_ = marg_txt.ORDER_SAMPLE
        cutord = os.path.join(tdir, "report.txt"); open(cutord, "wb").write(OS_[:OS_.rindex(b"***")])
        omsgs = []
        capture(cutord, sp2, cap2, omsgs.append)
        on = [n for n in NOTE_SINK if n["md5"] == hashlib.md5(OS_[:OS_.rindex(b"***")]).hexdigest()]
        ck("S454: an order sheet cut short is kept with its own reason, and its note says ORDER",
           len(on) == 1 and on[0]["kind"] == "ORDER" and "order sheet without" in on[0]["reason"] and any("NOT TAKEN" in m for m in omsgs))
        TXT_SEEN.clear(); TXT_STAT.clear()
        named =os.path.join(tdir, "orders 03 oct.txt"); open(named, "wb").write(OS_[:OS_.rindex(b"***")] + b"\\r\\n")
        capture(named, sp2, cap2, lambda m: None)
        ck("S454: an order sheet under any name is kept and noted too",
           any(n["md5"] == hashlib.md5(OS_[:OS_.rindex(b"***")] + b"\\r\\n").hexdigest() and n["kind"] == "ORDER" for n in NOTE_SINK))
        ck("S454: a phone-length digit run in a reason never leaves the PC",
           note_of("x.txt", "0" * 32, b"", "begins: 'SHOP %s'" % ("7" * 10))["reason"] == "begins: 'SHOP #'")
        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))'''),
    ('''    shutil.rmtree(d, ignore_errors=True)
    out("SELFTEST " + ("OK" if ok else "FAILED"))''',
     '''    shutil.rmtree(d, ignore_errors=True)
    NOTE_SINK = None
    out("SELFTEST " + ("OK" if ok else "FAILED"))'''),
    ('''    out("marg_watch S397 starting -- text reader %s, text route %s" % (_mt, "LIVE" if txt_live() else "ON HOLD"))''',
     '''    out("marg_watch S454 starting -- text reader %s, text route %s, refusal notes on" % (_mt, "LIVE" if txt_live() else "ON HOLD"))'''),
]


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = open(a.watch, "rb").read()
    if md5b(raw) != FROM:
        raise SystemExit("STOP: the watcher is %s, not its FROM pin %s -- nothing built" % (md5b(raw), FROM))
    txt = raw.decode("utf-8")
    for old, new in EDITS:
        c = txt.count(old)
        if c != 1:
            raise SystemExit("STOP: an anchor occurs %d times -- nothing built: %r" % (c, old[:90]))
        txt = txt.replace(old, new, 1)
    os.makedirs(a.out, exist_ok=True)
    out = txt.encode("utf-8")
    open(os.path.join(a.out, "marg_watch.py"), "wb").write(out)
    print("built marg_watch.py %s -> %s  (%d edits)" % (FROM[:8], md5b(out), len(EDITS)))


if __name__ == "__main__":
    main()
