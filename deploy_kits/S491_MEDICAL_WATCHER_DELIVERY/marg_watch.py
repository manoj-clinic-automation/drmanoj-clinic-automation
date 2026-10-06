#!/usr/bin/env python3
"""marg_watch.py -- capture Marg exports the instant they appear.  (S195)

THE PROBLEM
    Marg reuses slot names (REPORT_1.XLS, REPORT_2.XLS) for EVERY report type, so
    generating a new report OVERWRITES the previous file. Anything that only looks
    on a schedule loses an export that is overwritten between looks -- run a sale
    report then a stock report and the sale export is gone.

THE FIX -- CAPTURE FIRST, CLASSIFY LATER, AND DO NOT POLL FOR IT
    1. EVENT-DRIVEN on Windows: ReadDirectoryChangesW (via ctypes, stdlib only)
       has the kernel wake us the moment a file in the report folders is written.
       There is no polling window to fall through.
    2. A slow safety-net poll still runs underneath (default 5 s) in case an event
       is ever missed, and IS the mechanism on non-Windows.
    3. On an event the bytes are copied into the spool immediately -- after a
       cheap "is it finished being written" check (file magic + size steady across
       two quick reads). From that moment the export is safe: Marg may overwrite
       the original a millisecond later.
    4. marg_router.py classifies / verifies / archives from the spool afterwards.

    Capture is deliberately dumb and fast so it can never be the slow step.

S240 -- IT ALSO STARTS THE PUSHER (D467 phase 2b)
    marg_push.py, if it is beside this script, is started as a DAEMON THREAD: every captured
    export goes to the clinic server by itself, within a minute, and the server answers what it
    was. Capture is not touched by this and does not depend on it -- the thread is separate, every
    fault inside it is swallowed there, and if marg_push.py is absent this script behaves exactly
    as it did before. That is deliberate: the two files are delivered down the Drive kit channel
    and may arrive in either order, and capture must survive both orders.

SAFETY
    * Reads Marg only. NEVER writes inside D:\\MARGERP.
    * Dedup by content MD5 -- identical bytes are copied once, ever.
    * Crash-safe: the spool is plain files; a restart re-reads them and re-syncs.
    * Any failure in the Windows event path falls back to polling automatically.

USAGE
    marg_watch.py                 # watch (event-driven where available)
    marg_watch.py --once          # one sweep then exit (for a scheduled sweep)
    marg_watch.py --route         # classify the spool after capturing
    marg_watch.py --selftest

THE MARG BACKUP STICK (S381, 24-Sep-2026, F-617)
    Marg began saving an export to the root of the pen drive, E:\\, instead of its usual folder. On the
    medical install (this file in D:\\SendToClinic) the TOP LEVEL of E:\\ is swept too, on the safety
    poll: .xls/.xlsx/.pdf written in the last 24 hours only, never a subfolder, never an older file.
    Whatever else lives on the stick is never read, so it can never be sent.

MARG'S TEXT EXPORT (S389, 24-Sep-2026, F-619)
    With Office broken on the medical PC, Marg's Excel export stopped; its one-click text export
    (report.txt) does not need Office. A report*.txt in any watched folder is read by marg_txt.py:
    the bill-wise sales statement with item detail, complete to "End of Report", becomes the SAME
    .XLS Marg's Excel export is, and that is what is captured -- nothing downstream changes. The
    text is kept in _captured_txt\\ beside the spool. Any other text file is left alone.

S395 (25-Sep-2026, F-620): everything this prints also goes to D:\\SendToClinic\\marg_watch.log, and a
    report*.txt that is finished but not taken is kept in _captured_txt\\refused\\ with the reason.

S396 (25-Sep-2026, F-620): ANY .txt in the watched folders is looked at (the content decides, not the
    name), and every ten minutes a census of recent text files and the tail of marg_watch.log are written
    to Drive's Clinic Data Archive\\FromMedical beside the heartbeat. S396.1: a report text the reader
    refused is copied there too (FromMedical\\refused_text), with its reason, so it can be read and the
    reader mended without going to the medical PC.

S397 (25-Sep-2026, F-620): the reader (marg_txt S397) also takes the WHOLE STORES CLOSING STOCK text export.
    At every start the watcher offers the reader again every text it refused in the last three days, so a
    report kept before the reader learned it is taken as soon as the reader has (nothing refused is lost).

S454 (03-Oct-2026, D648 -- "every duty has a door"): a text kept as refused is NOT silent any more. The watcher sends the server a
    note -- the file's name, its md5, the kind it looked like and the reason; never a line of the file -- with the address and the key
    marg_push.py already uses. The server writes one row "refused by the medical PC" and the owner's Needs-you, the reports tile and
    Darpan's order-sheet card name it. Once per file; not while the sending is switched off. "Why not" learns Darpan's order sheet.

S454 P4C (04-Oct-2026, the brief's section 20): a note is DONE only when the server has answered for it, and that fact is a marker
    <stem>.note beside the kept text. A note that could not be sent -- a dead line, the off switch, no key, a key the server does not
    know -- WAITS, and is tried again at every start and at every census, until it is sent, the server refuses it (400, 413), the reader
    takes the text after all, a text of the same kind is taken after it, or it is older than CENSUS_DAYS. The first start on a PC marks
    what is already in refused as kept before S454 and announces none of it (sentinel _captured_txt\\S454_NOTES_STARTED.flag).
    The note never quotes the file: "(it begins: ...)" is cut and a reader's refusal leaves as "the reader refused it (line N)".

S480 (05-Oct-2026, D675; F-728): NO MARG TEXT IS DROPPED UNLOGGED. One export writes the page twice (user_<id>.txt, then report.txt);
    a list, a valuation, an expiry report or a register saved under the first name was judged "not a Marg report", not kept and not
    logged, and its twin then skipped as already seen. Now a text the reader does not take is KEPT and logged whenever it carries
    Marg's end mark in its tail, the firm's name in its head, or a report word in its first 4,000 bytes -- whatever the file is
    called. The note's kind is one word per report (PURCHASE, SALT, CATEGORY, ITEMS, SALE_SHORT, RETURN, VALUATION, EXPIRY, LEDGER
    beside SALE, STOCK, ORDER); the census lists every such text. The reader is given the file's own time (a kept copy's stamp), so
    a sale report with no bill is taken as a no-sale day only when its day is over; refused as "today", its bytes are NOT remembered
    as seen -- the same report exported on a later day is taken.

S488 (06-Oct-2026, kit S488_DATES_AND_WAITS part E): A REFUSED TEXT WITH A PERSON'S DETAIL STAYS OFF DRIVE. A refused sale report or
    stock register carries patients' names, and a .why.txt the whole reason, which can quote a line. share_refused now copies a kept
    text's BODY to Drive's FromMedical\\refused_text only when _may_leave says it can carry no person's detail: its kind is one whose
    rows never name a person (PURCHASE, SALT, CATEGORY, ITEMS, VALUATION, EXPIRY, STOCK), its first 25 lines carry no person word, and
    no mobile-shaped number stands in it but the shop's own "Phone :" line and Marg's advertisement line (phi_scan.py's patterns, the
    server's, copied here). Any other body leaves <stem>.withheld.txt in its place, one line. Every .why.txt on Drive is two lines --
    its stamp and the reason as a note carries it -- never the whole reason and no "from:" line. Each pass also sweeps Drive's folder:
    a body that may not leave, or whose kept text is gone, is removed for its .withheld.txt; a .why.txt not in that form is rewritten.
    _captured_txt\\refused on this PC is untouched (the body and the whole reason stay here), and capture is not changed.

OFF SWITCH (S259)
    D:\\SendToClinic\\_off\\MARG_WATCH_OFF.txt stops capture. ALL_OFF.txt does NOT --
    capture is the one job whose loss cannot be undone. Read every cycle; no restart.
"""
import argparse, hashlib, os, queue, re, shutil, sys, threading, time
import json, urllib.error, urllib.request                     # S454: the refusal note

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_WATCH = [r"D:\MARGERP\users"]
DEFAULT_SPOOL = r"D:\MargArchive\_spool"
SAFETY_POLL_S = 5.0            # net under the event stream
OFFDIR = os.path.join(HERE, "_off")
WATCH_OFF_MARKER = "MARG_WATCH_OFF.txt"   # S259 -- capture only; ALL_OFF does NOT cover capture
SETTLE_MS = 60                 # size must hold still this long to count as written
# S201: PDFs are captured too. Marg prints and exports them, and until now the
# watcher skipped them for their extension and wrote no line anywhere -- so a
# report produced as a PDF was invisible to the archive, the server and every
# health check, and the alarm that eventually fired blamed the network.
EXTS = (".xls", ".xlsx", ".pdf")

# S381 (F-617) -- the Marg backup stick. Swept FLAT (its top level only) and only for files written in
# the last FLAT_FRESH_S seconds, and only when this file is the medical install. On any other machine --
# manojz runs its own copy of this file against the share -- the list is empty and nothing changes.
FLAT_ROOTS_MEDICAL = ["E:\\"]
FLAT_FRESH_S = 24 * 3600
ON_MEDICAL = os.path.normcase(os.path.abspath(HERE)) == os.path.normcase(r"D:\SendToClinic")
FLAT_ROOTS = FLAT_ROOTS_MEDICAL if ON_MEDICAL else []
EXCEL_MAGICS = (b"\xd0\xcf\x11\xe0", b"PK\x03\x04")   # OLE2 (.xls) / zip (.xlsx)
PDF_MAGIC = (b"%PDF",)
# S389 (F-619): Marg's text export. Only files Marg names this way are looked at; what is inside
# decides whether one is converted (marg_txt.recognise) -- a name alone never does.
TXT_NAME = re.compile(r"^[^\\/]*\.txt$", re.I)     # S396: any .txt -- the content decides
REPORTISH = re.compile(r"^report", re.I)
TXT_STAT = {}           # S396: path -> (size, mtime) when last judged; unchanged files are not re-read
TXT_VERDICT = {}        # S396: path -> (when, verdict) -- what the census reports
TXT_SEEN = set()        # md5s of text already judged this run -- converted, or not ours
# S480 (F-728): what makes a text a Marg report, whatever its file is called. A text the reader does not take is KEPT when it carries
# Marg's end mark in its tail, the firm's name in its head, or any of these words in its first 4,000 bytes.
KEEP_WORDS = (b"STATEMENT", b"PENDING ORDERS", b"CLOSING STOCK", b"ITEM LIST", b"LIST OF ITEMS", b"STOCK VALUATION", b"EXP. BEFORE",
              b"STOCK REGISTER", b"SALE RETURN")
FIRM = b"SANJEEVNI MEDICOS"
END_MARK = b"*** End of Report ***"
# S480 (D.2): the title words of each report the reader has a spec for -> the one word its refusal note carries, and what a reason calls it
KIND_TITLES = (("PURCHASE STATEMENT", "PURCHASE", "a purchase statement"), ("SALT WISE ITEM LIST", "SALT", "a salt-wise item list"),
               ("CATEGORY WISE ITEM LIST", "CATEGORY", "a category-wise item list"), ("LIST OF ITEMS", "ITEMS", "a list of items"),
               ("SALE RETURN", "RETURN", "a sale return report"), ("STOCK VALUATION", "VALUATION", "a stock valuation"),
               ("EXP. BEFORE", "EXPIRY", "a stock expiry report"), ("STOCK REGISTER", "LEDGER", "a stock register"))
TODAY_NOTE = "the reader refused it: aaj ki report -- kal ki tareekh chun kar dobara banaiye"      # fixed words; never a line of the file
EMPTY_NOTE = "the reader refused it: an empty report -- kept, not yet verified"
# HOLD BY DEFAULT: a converted text export goes to _captured_txt\held\ and NOTHING is sent, until
# D:\SendToClinic\MARG_TXT_LIVE.txt exists and begins with LIVE. Being the default, the hold cannot
# be skipped by files arriving in the wrong order. A text held once is never sent later.
TXT_LIVE_FILE = os.path.join(HERE, "MARG_TXT_LIVE.txt")
TXT_LIVE_FORCE = None   # the selftest sets this; nothing else does


def txt_live():
    if TXT_LIVE_FORCE is not None:
        return TXT_LIVE_FORCE
    try:
        return open(TXT_LIVE_FILE, "rb").read(8).strip().upper().startswith(b"LIVE")
    except OSError:
        return False


def watch_off(offdir=None):
    """S259 -- THE OFF SWITCH FOR CAPTURE, and it is deliberately its own marker.

    ALL_OFF.txt stops the SENDING (marg_push) and the jobs on Dr Manoj's PC. It
    does NOT stop capture, because a Marg export that is not captured is gone
    for ever -- Marg overwrites REPORT_1.XLS the moment the next report is made.
    Stopping capture therefore takes its own, separate, deliberate marker.

    Read at the top of every cycle: no restart either way."""
    p = os.path.join(offdir or OFFDIR, WATCH_OFF_MARKER)
    return p if os.path.isfile(p) else None


def magics_for(ext):
    """The magic bytes a file of this extension must actually start with.

    Checked per extension rather than any-of: a PDF renamed .xls should be
    refused here, not carried downstream to fail as an unreadable spreadsheet.
    Excel stays permissive between OLE2 and zip because Marg genuinely emits
    both under the .xls name.
    """
    return PDF_MAGIC if ext == ".pdf" else EXCEL_MAGICS


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def looks_complete(path):
    """Cheap 'Marg has finished writing this' test -- no xlrd, no parsing."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(4)
        ext = os.path.splitext(path)[1].lower()
        if not any(head.startswith(m) for m in magics_for(ext)):
            return False
        s1 = os.path.getsize(path)
        if s1 <= 0:
            return False
        time.sleep(SETTLE_MS / 1000.0)
        return os.path.getsize(path) == s1
    except OSError:
        return False


_MT = {"mtime": None, "mod": None}


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


def _why_not(raw):
    """S395: the plain reason a finished report*.txt is not a report the reader takes."""
    try:
        t = raw.decode("latin-1")
    except Exception:                                           # noqa: BLE001
        return "cannot be read as text"
    head, tail = t[:4000], t[-400:]
    miss = []
    if "CLOSING STOCK" in head and "BILL WISE SALES STATEMENT" not in head:          # S397
        if "WHOLE STORES CLOSING STOCK" not in head:
            return "a closing stock of one store or category, not WHOLE STORES"
        if "*** End of Report ***" not in tail:
            return "a closing stock without the '*** End of Report ***' line at the end (cut short?)"
        return "a closing stock the reader cannot take"
    if "PENDING ORDERS (PURCHASE)" in head:                                          # S454: Darpan's order sheet
        if "*** End of Report ***" not in tail:
            return "an order sheet without the '*** End of Report ***' line at the end (cut short?)"
        return "an order sheet the reader cannot take"
    if "BILL WISE SALES STATEMENT" not in head:
        k = _kind_of(raw)                                       # S480 (D.2): the kind it recognised is named
        what = dict((x[1], x[2]) for x in KIND_TITLES).get(k)
        if what and k == "LEDGER" and "Issued :" not in t[-1200:]:
            return "%s without its closing 'Received : / Issued :' lines (cut short?)" % what
        if what and k != "LEDGER" and "*** End of Report ***" not in tail:
            return "%s without the '*** End of Report ***' line at the end (cut short?)" % what
        if what:
            return "%s the reader cannot take (its title or column heads are not the ones it knows)" % what
        first = next((l.strip() for l in t.splitlines() if l.strip()), "")[:80]
        return "not a report the reader knows (it begins: %r)" % first
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
            fh.write("%s\nfrom: %s\nwhy:  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), path, why))
        out("  ! NOT TAKEN %s (text): %s -- kept in _captured_txt\\refused" % (os.path.basename(path), why))
        notes_try(spool, out, only=stem)                       # S454 P4C: the owner is told; a note that cannot go WAITS (no marker)
    except OSError as ex:
        out("  ! could not keep the refused text %s: %s" % (os.path.basename(path), ex))


# ------------------------------------------------------------------ S454: the note of a refused text
NOTE_SINK = None        # the selftest sets a list here: notes are collected there and never sent
NOTE_TRIES = 3
NOTE_GAP_S = 60
NOTE_KEYS = ("name", "md5", "kind", "reason")


def _kind_of(raw):
    """One word for the report a text looks like, by its own title words -- never by its file's name. S480: one word per spec."""
    head = raw[:4000].decode("latin-1", "replace")
    if "PENDING ORDERS (PURCHASE)" in head:
        return "ORDER"
    if "CLOSING STOCK" in head:
        return "STOCK"
    if "BILL WISE SALES STATEMENT" in head:
        short = "BILL VALUE" in head and not any(l.startswith("BILL NO.") and "CASH" in l for l in head.splitlines())
        return "SALE_SHORT" if short else "SALE"
    for words, k, _what in KIND_TITLES:                         # S480 (D.2)
        if words in head:
            return k
    return ""


def _is_marg_text(path, raw):
    """S480 (D.1, F-728): is this text a Marg report -- by what is in it, whatever the file is called?"""
    head = raw[:4000]
    return bool(REPORTISH.match(os.path.basename(path)) or END_MARK in raw[-400:] or FIRM in head or any(w in head for w in KEEP_WORDS))


def _exported_at(path):
    """S480 (B.1): when a text was exported -- the file's own time; for a copy kept in _captured_txt\\refused, the stamp in its name."""
    m = re.match(r"^(\d{8}-\d{6})__", os.path.basename(path))
    if m and os.path.basename(os.path.dirname(os.path.abspath(path))).lower() == "refused":
        try:
            return time.mktime(time.strptime(m.group(1), "%Y%m%d-%H%M%S"))
        except (ValueError, OverflowError):
            pass
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _convert(marg_txt, raw, when):
    """S480: convert() with the export time. An older marg_txt beside this file (the two arrive in either order) takes the text alone."""
    try:
        return marg_txt.convert(raw, exported_at=when)
    except TypeError as ex:
        if "exported_at" not in str(ex):
            raise
        return marg_txt.convert(raw)


NOTE_SENTINEL = "S454_NOTES_STARTED.flag"  # in _captured_txt, outside refused: this PC's watcher has started with notes once
NOTE_FINAL = (400, 413)                    # the server's answers a retry cannot change; every other failure WAITS
NOTE_TRYING = set()                        # stems whose note is being tried now -- one attempt at a time for a text
NOTE_LOCK = threading.Lock()
NOTE_SAID = {"last": None}                 # (why, how many) last written to the log about waiting notes


def _ref_dir(spool):
    return os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")


def _note_reason(why):
    """What of a reason may leave the PC -- never a line of the file (S454 20.2). The .why.txt and the log keep the reason whole."""
    w = " ".join(str(why or "").split())
    if w.startswith("the reader refused it") and "aaj ki report" in w and "kal ki tareekh" in w:
        return TODAY_NOTE                                       # S480 (B.1): the reader's own fixed words for a zero-bill report of today
    if w.startswith("the reader refused it: an empty report"):
        return EMPTY_NOTE                                       # S480 (D675 a): recognised, kept, not yet verified
    if w.startswith("the reader refused it"):
        m = re.match(r"the reader refused it: line (\d+)\b", w)
        w = ("the reader refused it (line %s)" % m.group(1)) if m else "the reader refused it"
    elif " (it begins:" in w:
        w = w[:w.index(" (it begins:")]
    return re.sub(r"\d{6,}", "#", w)[:240]


def note_of(path, tmd5, raw, why):
    """The note: name, md5, kind, reason -- nothing of the file's content (_note_reason); a run of 6+ digits in the reason is masked."""
    name = re.split(r"[\\/]", str(path))[-1][:120]
    kind, reason = _kind_of(raw), _note_reason(why)
    if kind and kind not in ("SALE", "STOCK", "ORDER"):         # S480 (D.2): the owner's line names a refused text by what it is
        reason = ("%s text -- %s" % (kind, reason))[:240]
    return {"name": name, "md5": tmd5, "kind": kind, "reason": reason}


def _note_mark(ref, stem, what, out=None):
    """The marker <stem>.note: this text's note is finished, and how. Never a .txt, so the reader is never offered it."""
    try:
        with open(os.path.join(ref, stem + ".note"), "w", encoding="utf-8") as fh:
            fh.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), what))
        return True
    except OSError as ex:
        if out:
            out("  note: the marker of %s could not be written (%s)" % (stem, ex))
        return False


def notes_waiting(spool):
    """The kept texts of refused with no marker, as stems (the name its .txt, .why.txt and .note share)."""
    ref = _ref_dir(spool)
    try:
        names = os.listdir(ref)
    except OSError:
        return []
    have = set(names)
    return sorted(n[:-4] for n in names
                  if n.lower().endswith(".txt") and not n.lower().endswith(".why.txt") and (n[:-4] + ".note") not in have)


def notes_first_start(spool, out):
    """Once on a PC, before the first sweep: what is already in refused was kept before S454 -- marked, never announced."""
    try:
        keep = os.path.dirname(_ref_dir(spool))
        flag = os.path.join(keep, NOTE_SENTINEL)
        if os.path.exists(flag):
            return None
        os.makedirs(keep, exist_ok=True)
        ref, n = _ref_dir(spool), 0
        for stem in notes_waiting(spool):
            if _note_mark(ref, stem, "kept before S454 -- no note sent", out):
                n += 1
        if notes_waiting(spool):
            out("  notes: an old refused text could not be marked -- the sentinel is not written, and no waiting note is sent until it is")
            return None
        with open(flag, "w", encoding="utf-8") as fh:
            fh.write("%s  marg_watch S454 P4C started here with refusal notes; %d kept before it, none announced\n"
                     % (time.strftime("%Y-%m-%d %H:%M:%S"), n))
        out("  notes: the first start with refusal notes on this PC -- %d text(s) already in refused marked as kept before S454, "
            "none announced; sentinel %s written" % (n, NOTE_SENTINEL))
        return n
    except Exception as ex:                                     # noqa: BLE001 -- capture never fails for a note
        out("  notes: the first-start sentinel could not be written (%s) -- no waiting note is sent until it is" % ex)
        return None


def _taken_after(spool, kind, when):
    """Was a text of this kind TAKEN (its copy is kept in _captured_txt) after WHEN? Then the staff have exported again."""
    keep = os.path.dirname(_ref_dir(spool))
    try:
        names = os.listdir(keep)
    except OSError:
        return False
    for n in names:
        if not n.lower().endswith(".txt"):
            continue
        p = os.path.join(keep, n)
        try:
            if not os.path.isfile(p) or os.path.getmtime(p) <= when:
                continue
            with open(p, "rb") as fh:
                if _kind_of(fh.read(4000)) == kind:
                    return True
        except OSError:
            continue
    return False


def _why_read(ref, stem):
    """(the file's own name, the whole reason) from the .why.txt kept beside a refused text."""
    parts = stem.split("__")
    name = ("__".join(parts[1:-1]) if len(parts) >= 3 else stem) + ".txt"
    why = ""
    try:
        with open(os.path.join(ref, stem + ".why.txt"), encoding="utf-8", errors="replace") as fh:
            t = fh.read()
    except OSError:
        t = ""
    m = re.search(r"^from: (.+)$", t, re.M)
    if m and m.group(1).strip():
        name = re.split(r"[\\/]", m.group(1).strip())[-1] or name
    m = re.search(r"^why:\s*(.*)", t, re.M | re.S)
    if m:
        why = m.group(1).strip()
    return name, (why or "kept as refused (its reason was not kept)")


def _send_note(note, out):
    """ONE attempt (NOTE_TRIES tries, NOTE_GAP_S apart). Answers ("sent", status), ("refused", "HTTP n") or ("wait", why)."""
    try:
        import marg_push as MP
    except Exception as ex:                                     # noqa: BLE001
        return "wait", "marg_push.py is not here (%s)" % ex.__class__.__name__
    try:
        off = MP.off_marker()
        if off:
            return "wait", "sending is OFF (%s)" % os.path.basename(off)
        tok = MP.token()
        if not tok:
            return "wait", "no key in token.txt"
        body = json.dumps(note).encode("utf-8")
        last = "the server could not be reached"
        for i in range(NOTE_TRIES):
            req = urllib.request.Request(MP.URL, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-Finance-Marg", tok)
            req.add_header("X-Marg-Note", "refused")
            try:
                with urllib.request.urlopen(req, timeout=30, context=MP._ctx()) as r:
                    txt = r.read().decode("utf-8", "replace")
                try:
                    js = json.loads(txt or "{}")
                except ValueError:
                    js = None
                if isinstance(js, dict):
                    return "sent", str(js.get("status"))
                last = "the answer was not the server's own (not JSON)"
            except urllib.error.HTTPError as e:
                if e.code in NOTE_FINAL:
                    return "refused", "HTTP %s" % e.code
                last = "the server answered HTTP %s" % e.code
                if e.code in (401, 403, 404):
                    break                                       # a minute cannot change these; the next start or census asks again
            except Exception:                                   # noqa: BLE001 -- a dead line: try again shortly
                last = "the server could not be reached"
            if i + 1 < NOTE_TRIES:
                time.sleep(NOTE_GAP_S)
        return "wait", last
    except Exception as ex:                                     # noqa: BLE001
        return "wait", ex.__class__.__name__


def _note_one(spool, ref, stem, out, send=True):
    """One waiting note. None when it is finished (marked) or cannot be judged; else the reason it still waits."""
    p = os.path.join(ref, stem + ".txt")
    try:
        kept = os.path.getmtime(p)
        with open(p, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if time.time() - kept > CENSUS_DAYS * 86400:
        _note_mark(ref, stem, "expired -- older than %d days and never sent" % CENSUS_DAYS, out)
        out("  note: EXPIRED, never sent -- the refusal of %s is older than %d days" % (stem, CENSUS_DAYS))
        return None
    kind = _kind_of(raw)
    if kind and _taken_after(spool, kind, kept):
        _note_mark(ref, stem, "overtaken -- a %s text was taken after it; no note sent" % kind, out)
        out("  note: not sent -- a %s text was taken after %s was kept (overtaken)" % (kind, stem))
        return None
    if not send:
        return "not tried in this pass"
    name, why = _why_read(ref, stem)
    note = note_of(name, hashlib.md5(raw).hexdigest(), raw, why)
    if NOTE_SINK is not None:
        NOTE_SINK.append(dict(note))
        _note_mark(ref, stem, "sent -- collected by the selftest, nothing left the PC")
        return None
    what, how = _send_note(note, out)
    if what == "sent":
        _note_mark(ref, stem, "sent -- the server answered %s" % how, out)
        out("  note: the server has the refusal of %s (%s)" % (note["name"], how))
        return None
    if what == "refused":
        _note_mark(ref, stem, "refused by the server (%s) -- not tried again" % how, out)
        out("  note: the server would not take the refusal of %s (%s) -- not tried again" % (note["name"], how))
        return None
    return how


def _notes_run(spool, stems, out):
    ref = _ref_dir(spool)
    stop = None                                                 # the line, the switch or the key said: not now
    for stem in stems:
        try:
            why = _note_one(spool, ref, stem, out, send=stop is None)
            if why and stop is None:
                stop = why
        except Exception as ex:                                 # noqa: BLE001 -- capture never fails for a note
            out("  note: %s -- the note of %s waits" % (ex.__class__.__name__, stem))
        finally:
            with NOTE_LOCK:
                NOTE_TRYING.discard(stem)
    said = (stop, len(notes_waiting(spool))) if stop else None
    if said and said != NOTE_SAID.get("last"):                  # said once, not at every census: the log's tail is read on Drive
        out("  note: %s -- %d note(s) wait on this PC; tried again at the next start and at every census" % said)
    NOTE_SAID["last"] = said


def notes_try(spool, out, only=None):
    """Try the waiting notes -- every kept text with no marker, or ONLY the one just kept. One attempt at a time for a text."""
    try:
        ref = _ref_dir(spool)
        if only is None and NOTE_SINK is None and not os.path.exists(os.path.join(os.path.dirname(ref), NOTE_SENTINEL)):
            return 0                                            # the past is not marked yet: nothing old is announced
        todo = []
        with NOTE_LOCK:
            for stem in ([only] if only else notes_waiting(spool)):
                if stem not in NOTE_TRYING and not os.path.exists(os.path.join(ref, stem + ".note")):
                    NOTE_TRYING.add(stem)
                    todo.append(stem)
        if not todo:
            return 0
        if NOTE_SINK is not None:
            _notes_run(spool, todo, out)
            return len(todo)
        try:
            threading.Thread(target=_notes_run, args=(spool, todo, out), daemon=True, name="refusal_note").start()
        except Exception as ex:                                 # noqa: BLE001
            with NOTE_LOCK:
                NOTE_TRYING.difference_update(todo)
            out("  note: could not start (%s) -- %d note(s) wait" % (ex.__class__.__name__, len(todo)))
            return 0
        return len(todo)
    except Exception as ex:                                     # noqa: BLE001 -- capture never fails for a note
        out("  note: %s -- the notes wait" % ex.__class__.__name__)
        return 0


CENSUS_EVERY_S = 600
CENSUS_DAYS = 3
CENSUS_FILE = os.path.join(HERE, "marg_text_census.txt")


def _from_medical():
    """The Drive folder the agent writes its heartbeat into, on whatever letter Drive has today."""
    for L in "DEFGHIJKLMNOPQRSTUVWXYZ":
        p = "%s:\\My Drive\\Clinic Data Archive\\FromMedical" % L
        if os.path.isdir(p):
            return p
    return None


def _census_dirs(roots):
    """(folder, walk-depth, watched?) -- everywhere a text export might land."""
    out = [(r, 6, True) for r in roots] + [(r, 0, True) for r in FLAT_ROOTS]
    if sys.platform.startswith("win"):
        out.append(("D:\\", 0, False))
        out.append((r"C:\Users\Public\Documents", 1, False))
        try:
            for u in os.listdir("C:\\Users"):
                for sub in ("Desktop", "Documents", "Downloads"):
                    p = os.path.join("C:\\Users", u, sub)
                    if os.path.isdir(p):
                        out.append((p, 1, False))
        except OSError:
            pass
    return out


def _title_of(path):
    """A report's own title line, and nothing else -- never a patient's name."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(4000).decode("latin-1")
    except OSError:
        return ""
    for l in head.splitlines()[:14]:                            # S480 (D.3): the title may stand under a letterhead
        t = l.strip()
        if t and any(w.decode("latin-1") in t for w in KEEP_WORDS):
            return t[:90]
    for l in head.splitlines():
        t = l.strip()
        if t:
            return t[:90] if ("STATEMENT" in t or "REPORT" in t.upper()) else ""
    return ""


def text_census(roots, now=None):
    now = now or time.time()
    lines, seen = [], set()
    for base, depth, watched in _census_dirs(roots):
        if not os.path.isdir(base):
            continue
        base_depth = base.rstrip("\\/").count(os.sep)
        for dirpath, dirs, names in os.walk(base):
            if dirpath.rstrip("\\/").count(os.sep) - base_depth >= depth:
                dirs[:] = []
            for n in names:
                if not n.lower().endswith(".txt"):
                    continue
                p = os.path.join(dirpath, n)
                if p in seen:
                    continue
                seen.add(p)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if now - st.st_mtime > CENSUS_DAYS * 86400 or st.st_size <= 0:
                    continue
                v = TXT_VERDICT.get(p, (None, None))[1]
                if v is None:
                    v = "not looked at yet" if watched else "OUTSIDE the watched folders"
                t = _title_of(p)
                if not t and v in ("not a Marg report", "OUTSIDE the watched folders", "not looked at yet") \
                        and not REPORTISH.match(n):
                    continue                            # someone's own notes: not listed
                lines.append("%s  %8d  %s\n      -> %s%s" % (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)), st.st_size, p, v,
                    ("\n      title: %s" % t) if t else ""))
    lines.sort(reverse=True)
    return lines


# S488 (E.1) -- what of a refused text may leave this PC for Drive. Conservative on purpose: a wrong "clean" is the failure that
# matters. The four patterns are phi_scan.py's (the server's, S274 / kit S336), copied here letter for letter, applied to the lines.
PHI_MOBILE_RE = re.compile(r"(?<![0-9])[6-9][0-9]{9}(?![0-9])")
PHI_PERSON_WORDS = re.compile(r"\b(SALE|SALES|PATIENT|PATIENTS|MOBILE|LEDGER|PRESCRIB\w*|DOCTOR|CUSTOMER|ADDRESS)\b", re.I)
PHI_SHOP_LINE_RE = re.compile(r"^\s*PHONE\s*:", re.I)          # the shop's own header line (in the first 8 lines)
PHI_AD_LINE_RE = re.compile(r"\bMARG\b", re.I)                 # Marg's advertisement line names Marg (in the last 3 lines)
PHI_PREAMBLE_LINES, PHI_SHOP_LINES, PHI_AD_LINES = 25, 8, 3
# The kinds (_kind_of's words) whose rows never name a person. Every sale shape, the sale return, the stock register (LEDGER), ORDER
# (suppliers' Ph. numbers) and an unrecognised text ("") are not here. Each admitted spec of marg_txt S480 was read: none has a
# patient, doctor, customer, mobile or address column (PARTY / SUPPLIER NAME on a purchase is the supplier, as phi_scan reads it).
SHARE_KINDS = ("PURCHASE", "SALT", "CATEGORY", "ITEMS", "VALUATION", "EXPIRY", "STOCK")
WITHHELD_LINE = "kept on the medical PC only (a person's detail, or not established): %s"
WHY_STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
WHY_LINE_SAFE = re.compile(r"the reader refused it \(line \d+\)")   # _note_reason's own output: passed through it again, its line
#                                                                     number would be cut and the file rewritten on every pass


def _may_leave(raw):
    """S488 (E.1): may this refused text's BODY be copied to Drive? True only when every test holds; not established is False.
    The kind is admitted (SHARE_KINDS); the first 25 filled lines carry no person word; no ten-digit run starting 6-9 stands in any
    line -- as printed, or with a single space between digits closed up -- except the shop's own "Phone :" line among the first 8
    lines and a line naming MARG among the last 3 filled lines. An empty, binary, oversized or unrecognised text may not leave."""
    try:
        if not isinstance(raw, (bytes, bytearray)) or not raw or len(raw) > MAX_SHARE or b"\x00" in raw:
            return False
        raw = bytes(raw)
        if raw[:4] in EXCEL_MAGICS + PDF_MAGIC:
            return False
        if _kind_of(raw) not in SHARE_KINDS:
            return False
        lines = raw.decode("latin-1").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        filled = [(i, l) for i, l in enumerate(lines) if l.strip()]
        if not filled or PHI_PERSON_WORDS.search(" ".join(l for _i, l in filled[:PHI_PREAMBLE_LINES])):
            return False
        tail = set(i for i, _l in filled[-PHI_AD_LINES:])
        for i, l in filled:
            if PHI_MOBILE_RE.search(l) or PHI_MOBILE_RE.search(re.sub(r"(?<=\d) (?=\d)", "", l)):
                if (i < PHI_SHOP_LINES and PHI_SHOP_LINE_RE.match(l)) or (i in tail and PHI_AD_LINE_RE.search(l)):
                    continue                                    # the shop's or Marg's own number, not a person's
                return False
        return True
    except Exception:                                           # noqa: BLE001 -- not established: it stays on this PC
        return False


def _read_or_none(p, n=-1):
    try:
        with open(p, "rb") as fh:
            return fh.read(n)
    except OSError:
        return None


def _share_put(q, data):
    """S488: write DATA (bytes) to Q on Drive unless Q already holds exactly it -- compared by content, never by size. 1 if written."""
    if _read_or_none(q) == data:
        return 0
    with open(q, "wb") as fh:
        fh.write(data)
    return 1


def _safe_why(text, when):
    """S488 (E.2): the two lines a .why.txt may carry on Drive -- its stamp and the reason as a note carries it (_note_reason); no
    'from:' line, never the whole reason. TEXT is the kept .why.txt or, its local source gone, Drive's own copy. WHEN stamps a text
    whose first line is not a stamp."""
    text = text or ""
    lines = text.splitlines()
    stamp = lines[0].strip() if lines and WHY_STAMP_RE.match(lines[0].strip()) else \
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(when))
    m = re.search(r"^why:\s*(.*)", text, re.M | re.S)
    w = " ".join((m.group(1) if m else "").split())
    w = w if WHY_LINE_SAFE.fullmatch(w) else _note_reason(w).strip()
    return ("%s\nwhy:  %s\n" % (stamp, w or "kept as refused (its reason was not kept)")).encode("utf-8")


def _withhold(dst, name, raw):
    """S488 (E.2): the body NAME may not be on Drive -- removed if it is there, and <stem>.withheld.txt (one line) stands for it."""
    n = 0
    q = os.path.join(dst, name)
    if os.path.exists(q):
        os.remove(q)
        n += 1
    k = _kind_of(raw) if raw else ""
    return n + _share_put(os.path.join(dst, name[:-4] + ".withheld.txt"), ((WITHHELD_LINE % (k or "unknown")) + "\n").encode("utf-8"))


def _share_sweep(src, dst):
    """S488 (E.2): Drive's refused_text, every file, at every pass -- a body whose kept text may not leave or is gone is removed and
    its .withheld.txt stands for it; a .why.txt not in the safe form is rewritten (from the kept one, or from its own why: line).
    What is removed stays in Drive's own bin for 30 days."""
    n = 0
    for name in sorted(os.listdir(dst)):
        q, low = os.path.join(dst, name), name.lower()
        try:
            if not os.path.isfile(q) or low.endswith(".withheld.txt"):
                continue
            p = os.path.join(src, name)
            if low.endswith(".why.txt"):
                t = _read_or_none(p)
                when = os.path.getmtime(p) if t is not None else os.path.getmtime(q)
                if t is None:
                    t = _read_or_none(q) or b""
                n += _share_put(q, _safe_why(t.decode("utf-8", "replace"), when))
            elif low.endswith(".txt"):
                raw = _read_or_none(p)
                if raw is not None and _may_leave(raw):
                    continue
                n += _withhold(dst, name, raw if raw is not None else (_read_or_none(q, 4000) or b""))
        except OSError:
            continue
    return n


def share_refused(spool, fm, now=None):
    """S396.1: a report the reader would not take, offered beside the census so it can be looked at without anyone going to the
    medical PC. Only what is already in _captured_txt\\refused, only the last CENSUS_DAYS, at most 18 files offered. S454 P4C: a
    text's note marker (<stem>.note) is copied with it, so the list on Drive still shows which notes are done.
    S488 (E.2): a body is copied only when _may_leave says so (and, as before, a copy of the same size is not written again); any
    other leaves <stem>.withheld.txt in its place. Every .why.txt on Drive is the safe two lines (_safe_why), compared by content.
    The .note as before. Then Drive's folder is swept (_share_sweep). The local folder is never written here."""
    now = now or time.time()
    src = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")
    if not os.path.isdir(src):
        return 0
    dst = os.path.join(fm, "refused_text")
    n = 0
    for name in sorted(os.listdir(src), reverse=True)[:18]:
        p, low = os.path.join(src, name), name.lower()
        try:
            st = os.stat(p)
            if not os.path.isfile(p) or now - st.st_mtime > CENSUS_DAYS * 86400 or st.st_size > MAX_SHARE:
                continue
            os.makedirs(dst, exist_ok=True)
            q = os.path.join(dst, name)
            if low.endswith(".why.txt"):
                with open(p, "rb") as fh:
                    t = fh.read().decode("utf-8", "replace")
                n += _share_put(q, _safe_why(t, st.st_mtime))
            elif low.endswith(".withheld.txt"):
                continue                                        # never a name kept in refused; never copied
            elif low.endswith(".txt"):
                with open(p, "rb") as fh:
                    raw = fh.read()
                if not _may_leave(raw):
                    n += _withhold(dst, name, raw)
                elif not (os.path.exists(q) and os.path.getsize(q) == st.st_size):
                    shutil.copyfile(p, q)
                    n += 1
            elif low.endswith(".note"):
                if not (os.path.exists(q) and os.path.getsize(q) == st.st_size):
                    shutil.copyfile(p, q)
                    n += 1
        except OSError:
            continue
    if os.path.isdir(dst):
        n += _share_sweep(src, dst)
    return n


MAX_SHARE = 5 * 1024 * 1024


def publish_diagnostics(roots, out, spool=None):
    """S396: the census and the log's tail, locally and in Drive's FromMedical."""
    try:
        body = ("MARG TEXT CENSUS  %s  (marg_watch S396; text route %s)\n"
                "Every .txt written in the last %d days where a Marg text export could land, newest first.\n\n"
                % (time.strftime("%Y-%m-%d %H:%M:%S"), "LIVE" if txt_live() else "ON HOLD", CENSUS_DAYS))
        rows = text_census(roots)
        body += "\n".join(rows) if rows else "(none)"
        body += "\n"
        with open(CENSUS_FILE, "w", encoding="utf-8") as fh:
            fh.write(body)
        fm = _from_medical()
        if fm:
            with open(os.path.join(fm, "marg_text_census.txt"), "w", encoding="utf-8") as fh:
                fh.write(body)
            tail = b""
            if os.path.exists(WATCH_LOG):
                with open(WATCH_LOG, "rb") as fh:
                    fh.seek(max(0, os.path.getsize(WATCH_LOG) - 64 * 1024))
                    tail = fh.read()
            with open(os.path.join(fm, "marg_watch_log.txt"), "wb") as fh:
                fh.write(tail)
            if spool:
                share_refused(spool, fm)                        # S396.1
    except Exception as ex:                                     # noqa: BLE001 -- diagnostics never stop capture
        out("  ! census could not be written: %s" % ex)


def retry_refused(spool, captured, out, now=None):
    """S397: every text refused in the last CENSUS_DAYS, offered to the reader again (once, at start)."""
    now = now or time.time()
    src = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")
    took = 0
    if not os.path.isdir(src):
        return 0
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        try:
            if (not name.lower().endswith(".txt") or name.lower().endswith(".why.txt")
                    or now - os.path.getmtime(p) > CENSUS_DAYS * 86400):
                continue
        except OSError:
            continue
        got = capture_text(p, spool, captured, out)
        if got:
            took += 1
            out("  + a text refused earlier is taken now: %s" % name)
        if got or str(TXT_VERDICT.get(p, (0, ""))[1]).startswith(("TAKEN", "already taken", "HELD")):
            stem = name[:-4]                                    # S454 P4C: not a refusal any more -- no note for it
            if not os.path.exists(os.path.join(src, stem + ".note")):
                _note_mark(src, stem, "taken later -- the reader took it at a start; no note sent", out)
    return took


def capture_text(path, spool, captured, out):
    """S389: a Marg text export -> the same .XLS Marg's Excel export is, into the spool. True if NEW."""
    try:
        st0 = os.stat(path)
        if TXT_STAT.get(path) == (st0.st_size, st0.st_mtime):
            return False                        # S396: judged already, and not changed since
    except OSError:
        return False
    try:
        s1 = os.path.getsize(path)
        time.sleep(SETTLE_MS / 1000.0)
        if s1 <= 0 or os.path.getsize(path) != s1:
            return False                        # still being written; the next sweep takes it
        raw = open(path, "rb").read()
    except OSError:
        return False
    tmd5 = hashlib.md5(raw).hexdigest()
    try:
        st = os.stat(path); stat_key = (st.st_size, st.st_mtime)
    except OSError:
        stat_key = None
    if tmd5 in TXT_SEEN:
        if stat_key:
            TXT_STAT[path] = stat_key
        return False
    try:
        marg_txt = _marg_txt()
    except Exception as ex:                                     # noqa: BLE001
        if "no-marg_txt" not in TXT_SEEN:       # said once; the file is tried again every sweep, so a
            TXT_SEEN.add("no-marg_txt")         # text export waits for marg_txt.py rather than being lost
            out("  ! marg_txt.py is not here yet (%s) -- text exports wait for it" % ex.__class__.__name__)
        return False
    if not marg_txt.recognise(raw):
        # S395: finished (size held still above) but not a report the reader knows -- keep it and say why,
        # once. A later, complete version has other bytes and is looked at afresh.
        # S396: only REPORT-LIKE text is kept; any other .txt is judged and left alone.
        why = _why_not(raw)
        if _is_marg_text(path, raw):                            # S480 (F-728): the content decides, whatever the file is called
            _keep_refused(path, raw, tmd5, spool, out, why)
            TXT_VERDICT[path] = (time.time(), "NOT TAKEN: " + why)
        else:
            TXT_VERDICT[path] = (time.time(), "not a Marg report")
        TXT_SEEN.add(tmd5)
        if stat_key:
            TXT_STAT[path] = stat_key
        return False
    try:
        xls, info = _convert(marg_txt, raw, _exported_at(path))  # S480 (B.1): the file's own time says whether an empty day is over
    except Exception as ex:                                     # noqa: BLE001
        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        _keep_refused(path, raw, tmd5, spool, out, "the reader refused it: %s" % str(ex)[:400])
        TXT_VERDICT[path] = (time.time(), "NOT TAKEN: the reader refused it: %s" % str(ex)[:300])
        if ex.__class__.__name__ == "TodayNotOver":             # S480: the same bytes exported on a later day ARE taken -- this
            if stat_key:                                        # file is judged, its bytes are not remembered as seen
                TXT_STAT[path] = stat_key
        else:
            TXT_SEEN.add(tmd5)
        return False
    digest = hashlib.md5(xls).hexdigest()
    TXT_SEEN.add(tmd5)
    if stat_key:
        TXT_STAT[path] = stat_key
    if digest in captured:
        TXT_VERDICT.setdefault(path, (time.time(), "already taken earlier (the same report, byte for byte)"))
        if not TXT_VERDICT[path][1].startswith("TAKEN"):
            TXT_VERDICT[path] = (time.time(), "already taken earlier (the same report, byte for byte)")
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
            out("  = HELD %s (text) -> _captured_txt\held  (the text reader is on hold; nothing sent)"
                % os.path.basename(path))
            TXT_VERDICT[path] = (time.time(), "HELD (the text reader is on hold; nothing sent)")
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
    TXT_VERDICT[path] = (time.time(), "TAKEN -> %s" % os.path.basename(dest))
    out("  + CAPTURED %s (text) -> %s  (converted by marg_txt %s)" % (os.path.basename(path),
                                                                     os.path.basename(dest), info.get("version")))
    PUSH_WAKE.set()
    return True


def capture(path, spool, captured, out):
    """Copy the bytes into the spool, keyed by content. True if NEW."""
    if path.lower().endswith(".txt"):
        return capture_text(path, spool, captured, out)        # S389
    if not looks_complete(path):
        return False
    try:
        digest = md5_of(path)
    except OSError:
        return False
    if digest in captured:
        return False
    try:
        os.makedirs(spool, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        slot = os.path.splitext(os.path.basename(path))[0]
        dest = os.path.join(spool, "%s__%s__%s%s"
                            % (stamp, slot, digest[:8], os.path.splitext(path)[1] or ".xls"))
        shutil.copy2(path, dest)
    except OSError as ex:
        out("  ! copy failed (busy?), will retry: %s" % ex)
        return False
    captured.add(digest)
    out("  + CAPTURED %s  ->  %s" % (os.path.basename(path), os.path.basename(dest)))
    PUSH_WAKE.set()                     # S240: tell the pusher now, do not make it wait its turn
    return True


def list_flat(root, now=None, fresh_s=FLAT_FRESH_S):
    """S381: the top level of ROOT only -- report files written in the last FRESH_S seconds. A folder,
    an older file, another extension or a drive that is not there: skipped, silently, every time."""
    got = []
    try:
        if not os.path.isdir(root):
            return got
        now = time.time() if now is None else now
        for n in os.listdir(root):
            if not (n.lower().endswith(EXTS) or TXT_NAME.match(n)):
                continue
            p = os.path.join(root, n)
            try:
                if os.path.isfile(p) and now - os.path.getmtime(p) <= fresh_s:
                    got.append(p)
            except OSError:
                continue
    except OSError:
        return []
    return got


def list_exports(roots, flat=None):
    files = []
    for root in roots:
        if os.path.isfile(root):
            files.append(root); continue
        for dirpath, _d, names in os.walk(root):
            files += [os.path.join(dirpath, n) for n in names
                      if n.lower().endswith(EXTS) or TXT_NAME.match(n)]
    for root in (FLAT_ROOTS if flat is None else flat):       # S381: the backup stick, top level only
        files += list_flat(root)
    return files


def prime_captured(spool):
    got = set()
    if os.path.isdir(spool):
        for n in os.listdir(spool):
            p = os.path.join(spool, n)
            if os.path.isfile(p):
                try:
                    got.add(md5_of(p))
                except OSError:
                    pass
    return got


# --------------------------------------------------------------------------- #
# Windows: kernel-notified directory changes (no polling window)
# --------------------------------------------------------------------------- #

def _win_watch_thread(root, evq, out):
    """Blocking ReadDirectoryChangesW loop. Any problem -> thread exits quietly
    and the safety-net poll carries on doing the job."""
    import ctypes
    from ctypes import wintypes
    FILE_LIST_DIRECTORY = 0x0001
    SHARE = 0x1 | 0x2 | 0x4
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILTER = 0x1 | 0x8 | 0x10          # FILE_NAME | SIZE | LAST_WRITE
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    h = k32.CreateFileW(ctypes.c_wchar_p(root), FILE_LIST_DIRECTORY, SHARE, None,
                        OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, None)
    if h == wintypes.HANDLE(-1).value or not h:
        out("  (event watch unavailable for %s -- safety poll covers it)" % root)
        return
    buf = ctypes.create_string_buffer(64 * 1024)
    nbytes = wintypes.DWORD()
    try:
        while True:
            ok = k32.ReadDirectoryChangesW(h, buf, ctypes.sizeof(buf), True, FILTER,
                                           ctypes.byref(nbytes), None, None)
            if not ok:
                break
            off = 0
            while True:
                # FILE_NOTIFY_INFORMATION: NextEntryOffset, Action, FileNameLength, FileName
                nxt = int.from_bytes(buf.raw[off:off + 4], "little")
                ln = int.from_bytes(buf.raw[off + 8:off + 12], "little")
                name = buf.raw[off + 12:off + 12 + ln].decode("utf-16-le", "ignore")
                if name.lower().endswith(EXTS) or TXT_NAME.match(os.path.basename(name)):
                    evq.put(os.path.join(root, name))
                if not nxt:
                    break
                off += nxt
    except Exception:                                             # noqa: BLE001
        pass
    finally:
        try:
            k32.CloseHandle(h)
        except Exception:                                         # noqa: BLE001
            pass


def start_event_watchers(roots, evq, out):
    if not sys.platform.startswith("win"):
        return False
    started = 0
    for r in roots:
        if not os.path.isdir(r):
            continue
        t = threading.Thread(target=_win_watch_thread, args=(r, evq, out), daemon=True)
        t.start(); started += 1
    if started:
        out("  event-driven capture active on %d folder(s) -- no polling gap" % started)
    return started > 0


# --------------------------------------------------------------------------- #

PUSH_WAKE = threading.Event()          # S240: set the moment anything is captured


def start_pusher(spool, out):
    """Start marg_push in a daemon thread. Absent, broken or unimportable: capture carries on.

    A daemon thread dies with the process, so the watcher can still be stopped and restarted by
    the agent exactly as before, and nothing here can hold that up."""
    try:
        import marg_push
    except Exception as ex:                                    # noqa: BLE001
        out("  pusher: not here (%s) -- capturing only, exactly as before"
            % ex.__class__.__name__)
        return None
    try:
        t = threading.Thread(target=marg_push.loop, args=(spool, out), daemon=True,
                             kwargs={"wake": PUSH_WAKE}, name="marg_push")
        t.start()
        return t
    except Exception as ex:                                    # noqa: BLE001
        out("  pusher: could not start (%s) -- capturing only" % ex.__class__.__name__)
        return None


def watch(roots, spool, once, do_route, out, route_extra=None, poll_s=SAFETY_POLL_S):
    captured = prime_captured(spool)
    out("watching: %s" % ", ".join(roots))
    if FLAT_ROOTS:
        out("stick   : %s top level only, files of the last %d h, on the %.0fs poll (S381)"
            % (", ".join(FLAT_ROOTS), FLAT_FRESH_S // 3600, poll_s))
    out("spool   : %s   (%d already captured)" % (spool, len(captured)))
    evq = queue.Queue()
    evented = start_event_watchers(roots, evq, out) if not once else False
    if not evented and not once:
        out("  polling every %.1fs (event watch not available on this platform)" % poll_s)

    def sweep():
        n = 0
        for f in list_exports(roots):
            if capture(f, spool, captured, out):
                n += 1
        return n

    notes_first_start(spool, out)       # S454 P4C: before the first sweep -- what is already in refused is never announced
    new = 0 if watch_off() else sweep()  # always start from a known state
    if not watch_off():
        new += retry_refused(spool, captured, out)      # S397
    notes_try(spool, out)               # S454 P4C: every waiting note, at every start, after the retry
    if do_route and new:
        route(spool, out, route_extra); new = 0
    if once:
        return captured
    start_pusher(spool, out)            # S240: after the first sweep, never before it

    last_poll = time.time()
    publish_diagnostics(roots, out, spool)  # S396
    last_census = time.time()
    off_said = None
    while True:
        off = watch_off()
        if off != off_said:
            out("  capture: %s" % (("OFF -- %s is present" % off) if off else "on"))
            off_said = off
        if off:
            try:                                  # nothing queues up while it is off
                while True:
                    evq.get_nowait()
            except queue.Empty:
                pass
            time.sleep(2.0)
            continue
        try:
            path = evq.get(timeout=0.25)          # kernel told us something changed
            if capture(path, spool, captured, out):
                new += 1
            # drain any burst before routing
            while True:
                try:
                    p2 = evq.get_nowait()
                    if capture(p2, spool, captured, out):
                        new += 1
                except queue.Empty:
                    break
        except queue.Empty:
            pass
        if time.time() - last_poll >= poll_s:     # safety net under the events
            new += sweep()
            last_poll = time.time()
        if time.time() - last_census >= CENSUS_EVERY_S:           # S396
            notes_try(spool, out)                                 # S454 P4C: every waiting note, at every census
            publish_diagnostics(roots, out, spool)
            last_census = time.time()
        if do_route and new:
            route(spool, out, route_extra); new = 0


def route(spool, out, extra=None):
    try:
        import marg_router
    except ImportError:
        out("  ! marg_router.py not beside this script -- spool kept, not routed.")
        return
    out("  -- routing the spool --")
    marg_router.main(["--scan", spool] + (extra or []))


def _s488_share_cases(ck, base, share=None):
    """S488 (walk 7.6, the medical PC): made-up W488 texts kept as refused the way capture keeps them (_keep_refused: the body and
    the whole reason with its from: line), a body and a whole-reason .why.txt planted on the scratch Drive beforehand, then SHARE --
    share_refused, or the OLD file's for the negative control -- run twice into BASE\\FromMedical. Invented names and digits only."""
    import marg_txt
    share = share or share_refused
    M_ = marg_txt._s480_samples()
    mob = lambda a, b: a + b * 9                                # a ten-digit run made here, never written out in this file
    spool = os.path.join(base, "spool")
    refd = _ref_dir(spool)
    rtd = os.path.join(base, "FromMedical", "refused_text")
    os.makedirs(refd, exist_ok=True)
    os.makedirs(rtd, exist_ok=True)
    whys = {}

    def keep(tag, raw, why):
        h = hashlib.md5(raw).hexdigest()
        _keep_refused(os.path.join(base, "MARGERP", tag + ".txt"), raw, h, spool, lambda m: None, why)
        s = [f for f in os.listdir(refd) if h in f and f.endswith(".why.txt")][0][:-8]
        whys[s] = why
        return s
    sale = marg_txt.SELFTEST_SAMPLE.replace(b"TEST ONE", b"W488 ONE")[:-40]
    reg = M_["STOCK_ITEM_LEDGER_TEXT"].replace(b"TEST ONE 1001", b"W488 PERSON")
    lst = M_["ITEM_MASTER"].replace(b"DEMOGEL", b"W488GEL")[:-30]
    ten = M_["ITEM_MASTER"].replace(b"DEMOCIN TAB", ("W488 TAB " + mob("9", "8")).encode(), 1)
    phl = M_["ITEM_MASTER"].replace(b"DEMOGEL", b"W488PHGEL")
    cut = phl.index(b"\r\n") + 2
    phl = (phl[:cut] + (" " * 22 + "Phone : " + mob("9", "7") + "\r\n").encode() + phl[cut:].rstrip(b"\r\n") + b"\r\n"
           + ("MARG ERP W488 for Chemist  Call " + mob("8", "6") + "\r\n").encode())
    s_sale = keep("report", sale, "the reader refused it: line 7: a line of a kind this reader does not know: 'A000001 W488 ONE .CASH'")
    s_reg = keep("user_w4881", reg, "the reader refused it: line 12: a figure that cannot be read: 'W488 PERSON TEST DOCTOR'")
    s_lst = keep("user_w4882", lst, _why_not(lst))
    s_ten = keep("user_w4883", ten, "the reader refused it: line 10: a figure that cannot be read: 'W488 TAB %s'" % mob("9", "8"))
    s_phl = keep("user_w4884", phl, _why_not(phl))
    gone = marg_txt.SELFTEST_SAMPLE.replace(b"TEST ONE", b"W488 GONE")
    s_gone = "20300101-000000__report__%s" % hashlib.md5(gone).hexdigest()
    shutil.copyfile(os.path.join(refd, s_sale + ".txt"), os.path.join(rtd, s_sale + ".txt"))          # planted beforehand
    shutil.copyfile(os.path.join(refd, s_sale + ".why.txt"), os.path.join(rtd, s_sale + ".why.txt"))
    with open(os.path.join(rtd, s_gone + ".txt"), "wb") as fh:
        fh.write(gone)
    with open(os.path.join(rtd, s_gone + ".why.txt"), "wb") as fh:
        fh.write(b"2030-01-01 00:00:00\r\nfrom: C:\\W488\\report.txt\r\nwhy:  the reader refused it: line 7: a line of a kind this "
                 b"reader does not know: 'A000001 W488 GONE .CASH'\r\n")
    snap = lambda dd: dict((f, open(os.path.join(dd, f), "rb").read()) for f in sorted(os.listdir(dd)))
    loc0 = snap(refd)
    n1 = share(spool, os.path.join(base, "FromMedical"))
    d1 = snap(rtd)
    n2 = share(spool, os.path.join(base, "FromMedical"))
    d2 = snap(rtd)
    on = lambda s, x: d1.get(s + x)
    held = lambda k: ((WITHHELD_LINE % k) + "\n").encode("utf-8")
    want = dict((s, _note_reason(w)) for s, w in whys.items())
    want[s_gone] = "the reader refused it (line 7)"
    first = dict((s, open(os.path.join(refd, s + ".why.txt"), encoding="utf-8").read().splitlines()[0]) for s in whys)
    first[s_gone] = "2030-01-01 00:00:00"

    def safe(dd, f):
        b = dd.get(f)
        s = f[:-8]
        return (b is not None and s in want and b == ("%s\nwhy:  %s\n" % (first[s], want[s])).encode("utf-8")
                and b"from:" not in b and b"W488" not in b and WHY_STAMP_RE.match(first[s]) is not None)
    ck("S488 (7.6): of a sale report, a stock register and an item list kept as refused, ONLY the list's body reaches Drive",
       on(s_lst, ".txt") == lst and on(s_sale, ".txt") is None and on(s_reg, ".txt") is None)
    ck("S488 (7.6): the sale report and the register each leave <stem>.withheld.txt -- one line, naming the kind",
       on(s_sale, ".withheld.txt") == held("SALE") and on(s_reg, ".withheld.txt") == held("LEDGER"))
    ck("S488 (7.6): Drive's folder holds exactly the admitted bodies, the .withheld.txt of the rest, every reason and every note",
       sorted(d1) == sorted([s + x for s in (s_sale, s_reg, s_ten) for x in (".withheld.txt", ".why.txt", ".note")]
                            + [s + x for s in (s_lst, s_phl) for x in (".txt", ".why.txt", ".note")]
                            + [s_gone + ".withheld.txt", s_gone + ".why.txt"]))
    dw = [f for f in d1 if f.lower().endswith(".why.txt")]
    ck("S488 (7.6): every .why.txt on Drive is the safe two lines -- the stamp and the note's reason; no 'from:', never the whole reason",
       len(dw) == 6 and all(safe(d1, f) for f in dw))
    ck("S488 (7.6): a body and a whole-reason .why.txt planted beforehand are swept -- also where the kept text is gone (its reason "
       "remade from Drive's own why: line)",
       on(s_sale, ".txt") is None and on(s_gone, ".txt") is None and on(s_gone, ".withheld.txt") == held("SALE")
       and safe(d1, s_gone + ".why.txt") and safe(d1, s_sale + ".why.txt"))
    ck("S488 (7.6): an item list with a ten-digit run in a body line is withheld",
       on(s_ten, ".txt") is None and on(s_ten, ".withheld.txt") == held("ITEMS"))
    ck("S488 (E.1): the shop's own 'Phone :' line and Marg's advertisement line do not hold an item list back",
       on(s_phl, ".txt") == phl)
    ck("S488 (7.6): a second pass writes nothing, and every .why.txt there stays the safe form",
       n1 > 0 and n2 == 0 and d2 == d1 and all(safe(d2, f) for f in d2 if f.lower().endswith(".why.txt")))
    ck("S488 (E.3): the local _captured_txt\\refused is untouched -- the bodies and the whole reasons stay on this PC",
       snap(refd) == loc0 and len(loc0) == 15)


def selftest(out):
    """Proves the thing that matters: an OVERWRITTEN export is still kept."""
    import tempfile
    global NOTE_SINK
    NOTE_SINK = []                                              # S454: notes are collected, never sent, in the selftest
    ok = True
    def ck(n, c):
        nonlocal ok
        out(("  OK   " if c else "  FAIL ") + n); ok = ok and c
    d = tempfile.mkdtemp(); spool = os.path.join(d, "spool")
    slot = os.path.join(d, "REPORT_1.XLS")
    body = lambda tag: b"\xd0\xcf\x11\xe0" + tag * 200        # valid .xls magic

    cap = prime_captured(spool)
    for tag in (b"A", b"B", b"C"):                            # 3 exports, one slot
        open(slot, "wb").write(body(tag))
        capture(slot, spool, cap, lambda m: None)
    files = sorted(os.listdir(spool))
    ck("all 3 overwritten exports survive (%d)" % len(files), len(files) == 3)
    tags = {open(os.path.join(spool, f), "rb").read()[4:5] for f in files}
    ck("their contents are distinct (A/B/C)", tags == {b"A", b"B", b"C"})
    n = len(files)
    capture(slot, spool, cap, lambda m: None)
    ck("identical bytes are not re-copied (dedup)", len(os.listdir(spool)) == n)
    ck("a restart does not re-copy the spool", len(prime_captured(spool)) == 3)

    junk = os.path.join(d, "REPORT_9.XLS")
    open(junk, "wb").write(b"not-an-xls-yet")
    ck("a file still being written is NOT captured", capture(junk, spool, cap, lambda m: None) is False)
    open(junk, "wb").write(body(b"D"))
    ck("...and IS captured once it is complete", capture(junk, spool, cap, lambda m: None) is True)

    # S381: the backup stick -- top level, fresh files, report extensions, and nothing else
    stick = os.path.join(d, "stick"); os.makedirs(os.path.join(stick, "old backups"))
    fresh = os.path.join(stick, "REPORT_1.XLS"); open(fresh, "wb").write(body(b"E"))
    stale = os.path.join(stick, "LAST MONTH.XLS"); open(stale, "wb").write(body(b"F"))
    os.utime(stale, (time.time() - 3 * 86400, time.time() - 3 * 86400))
    deep = os.path.join(stick, "old backups", "REPORT_2.XLS"); open(deep, "wb").write(body(b"G"))
    other = os.path.join(stick, "d1-sanjeevni.mbk"); open(other, "wb").write(b"backup")
    got = list_flat(stick)
    ck("the stick: a fresh export at its top level IS seen", fresh in got)
    ck("the stick: a file older than a day is NOT", stale not in got)
    ck("the stick: nothing inside a folder is read", deep not in got)
    ck("the stick: a Marg backup (.mbk) is never touched", other not in got and len(got) == 1)
    ck("the stick: an absent drive is skipped quietly", list_flat(os.path.join(d, "no such drive")) == [])
    ck("the stick: a sweep with it captures the fresh export",
       any(capture(p, spool, cap, lambda m: None) for p in list_exports([], flat=[stick])))

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
        TXT_SEEN.clear(); TXT_STAT.clear(); TXT_LIVE_FORCE = True
        ck("a text held once is never sent, even when the reader goes live",
           capture(rpt, os.path.join(d, "spool_h"), set(), lambda m: None) is False)
        import shutil as _sh; _sh.rmtree(os.path.join(d, "_captured_txt")); TXT_SEEN.clear(); TXT_STAT.clear()
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
        TXT_SEEN.clear(); TXT_STAT.clear()
        ck("taking it again (a restart) adds nothing", capture(rpt, sp2, prime_captured(sp2), lambda m: None) is False
           and len([f for f in os.listdir(sp2) if f.endswith(".XLS")]) == 1)
        open(cut, "wb").write(T.replace(b"TEST ONE", b"TEST 1ST"))
        ck("the cut-off one, once Marg finishes writing it, is taken", capture(cut, sp2, cap2, lambda m: None) is True)
        # S396: a report under ANY name is taken; someone's notes are neither kept nor listed
        TXT_SEEN.clear(); TXT_STAT.clear()
        anyname = os.path.join(tdir, "SALE 24 SEP.TXT")
        open(anyname, "wb").write(T.replace(b"TEST TWO", b"TEST 2ND"))
        ck("a bill-wise text export under ANY name is taken (the content decides)",
           capture(anyname, sp2, cap2, lambda m: None) is True)
        notes = os.path.join(tdir, "shopping list.txt"); open(notes, "wb").write(b"milk, bread")
        capture(notes, sp2, cap2, lambda m: None)
        ck("someone's own .txt is judged and left alone -- not kept, not copied",
           not any("shopping" in f for f in (os.listdir(os.path.join(d, "_captured_txt", "refused"))
                                               if os.path.isdir(os.path.join(d, "_captured_txt", "refused")) else [])))
        ck("an unchanged file is not read again", capture(anyname, sp2, cap2, lambda m: None) is False
           and TXT_STAT.get(anyname) is not None)
        cen = text_census([tdir])
        ck("the census lists the report as TAKEN with its title, and never lists the notes",
           any("SALE 24 SEP.TXT" in l and "TAKEN" in l and "BILL WISE SALES STATEMENT" in l for l in cen)
           and not any("shopping" in l for l in cen))
        # S395: a finished report*.txt that is not taken is kept, with its reason
        TXT_SEEN.clear(); TXT_STAT.clear()
        odd = os.path.join(tdir, "report_odd.txt"); open(odd, "wb").write(T.replace(b"End of Report", b"End of Page"))
        msgs = []
        capture(odd, sp2, cap2, msgs.append)
        refd = os.path.join(d, "_captured_txt", "refused")
        whys = [f for f in os.listdir(refd) if f.endswith(".why.txt") and "report_odd" in f] if os.path.isdir(refd) else []
        ck("a finished report it will not take is KEPT, with the reason written beside it",
           len(whys) == 1 and "End of Report" in open(os.path.join(refd, whys[0]), encoding="utf-8").read()
           and any("NOT TAKEN" in m for m in msgs))
        capture(odd, sp2, cap2, msgs.append); TXT_SEEN.clear(); TXT_STAT.clear(); capture(odd, sp2, cap2, msgs.append)
        fmd = os.path.join(d, "FromMedical"); os.makedirs(fmd)
        rtd = os.path.join(fmd, "refused_text")
        n1, n2 = share_refused(sp2, fmd), share_refused(sp2, fmd)
        stems = sorted(set(f[:-8] for f in os.listdir(refd) if f.endswith(".why.txt")))
        kinds = dict((s, _kind_of(open(os.path.join(refd, s + ".txt"), "rb").read())) for s in stems)
        ck("S396.1 / S488: a refused SALE text (or a note kept under a report's name) is NOT copied beside the census -- its "
           ".withheld.txt, its reason (two safe lines) and its note are, once",
           n1 == len(os.listdir(refd)) >= 2 and n2 == 0 and "SALE" in kinds.values()
           and sorted(os.listdir(rtd)) == sorted(s + x for s in stems for x in (".withheld.txt", ".why.txt", ".note"))
           and all(open(os.path.join(rtd, s + ".withheld.txt"), encoding="utf-8").read()
                   == WITHHELD_LINE % (kinds[s] or "unknown") + "\n" for s in stems)
           and all(len(open(os.path.join(rtd, s + ".why.txt"), encoding="utf-8").read().splitlines()) == 2
                   and "from:" not in open(os.path.join(rtd, s + ".why.txt"), encoding="utf-8").read() for s in stems)
           and any(f.endswith(".why.txt") for f in os.listdir(refd)))
        ck("...and only once, however often it is looked at",
           len([f for f in os.listdir(refd) if f.endswith(".why.txt") and "report_odd" in f]) == 1)
        # S397: a closing-stock text refused by an older reader is taken at the next start
        TXT_SEEN.clear(); TXT_STAT.clear()
        STK = marg_txt.STOCK_SAMPLE
        old = os.path.join(refd, "20260925-073658__report__%s.txt" % hashlib.md5(STK).hexdigest())
        open(old, "wb").write(STK)
        n0 = len([f for f in os.listdir(sp2) if f.endswith(".XLS")])
        took = retry_refused(sp2, cap2, lambda m: None)
        xs2 = [f for f in os.listdir(sp2) if f.endswith(".XLS")]
        ck("S397: a closing stock kept as refused is taken at the next start, as marg_txt's own .XLS",
           took == 1 and len(xs2) == n0 + 1
           and any(md5_of(os.path.join(sp2, f)) == hashlib.md5(marg_txt.convert(STK)[0]).hexdigest() for f in xs2))
        TXT_SEEN.clear(); TXT_STAT.clear()
        ck("...and only once (a second start adds nothing)", retry_refused(sp2, cap2, lambda m: None) == 0)
        ck("S397: a store-filtered stock is refused with its reason",
           "not WHOLE STORES" in _why_not(STK.replace(b"WHOLE STORES", b"MAIN STORE")))
        # S454: the note of a refused text -- once per file, no content, the kind it looked like
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
        named =os.path.join(tdir, "orders 03 oct.txt"); open(named, "wb").write(OS_[:OS_.rindex(b"***")] + b"\r\n")
        capture(named, sp2, cap2, lambda m: None)
        ck("S454: an order sheet under any name is kept and noted too",
           any(n["md5"] == hashlib.md5(OS_[:OS_.rindex(b"***")] + b"\r\n").hexdigest() and n["kind"] == "ORDER" for n in NOTE_SINK))
        ck("S454: a phone-length digit run in a reason never leaves the PC",
           note_of("x.txt", "0" * 32, b"", "begins: 'SHOP %s'" % ("7" * 10))["reason"] == "begins: 'SHOP #'")
        # S454 P4C: the marker, the reasons that may leave the PC, a text taken later
        ck("P4C: every note that left has its marker beside the kept text (<stem>.note) and nothing waits",
           any(f == "%s.note" % os.path.splitext(w)[0][:-4] for w in whys for f in os.listdir(refd)) and notes_waiting(sp2) == [])
        ck("P4C: the reason that leaves the PC never quotes the file ('(it begins: ...)' cut; a reader's refusal is '(line N)' only)",
           _note_reason("not a bill-wise sales statement (it begins: 'SOME SHOP NAME')") == "not a bill-wise sales statement"
           and _note_reason("the reader refused it: line 52: a line of a kind this reader does not know: '4 *** AN ITEM 1*1'")
           == "the reader refused it (line 52)"
           and _note_reason("the reader refused it: no GRAND TOTAL line") == "the reader refused it")
        ck("P4C: a text the reader takes at a start is marked 'taken later' and sends no note",
           os.path.exists(old[:-4] + ".note") and "taken later" in open(old[:-4] + ".note", encoding="utf-8").read()
           and not any(n["md5"] == hashlib.md5(STK).hexdigest() for n in NOTE_SINK))
        # S480 (F-728, D.1-D.3, B.1): a Marg text under ANY name is kept or taken; the kind words; the census; the empty day
        if hasattr(marg_txt, "_s480_samples"):
            M_ = marg_txt._s480_samples()
            TXT_SEEN.clear(); TXT_STAT.clear()
            SL = M_["SALT_WISE_ITEM_LIST"]
            cutsl = SL[:SL.rindex(b"***")]
            u1 = os.path.join(tdir, "17476", "user_aa1.txt"); open(u1, "wb").write(cutsl)
            n480 = len(NOTE_SINK); m480 = []
            capture(u1, sp2, cap2, m480.append)
            kept480 = [f for f in os.listdir(refd) if hashlib.md5(cutsl).hexdigest() in f and f.endswith(".txt") and not f.endswith(".why.txt")]
            ck("S480: a salt list cut short and saved as user_<id>.txt is KEPT and logged, its note says SALT (before: dropped, no line)",
               len(kept480) == 1 and any("NOT TAKEN" in m for m in m480) and len(NOTE_SINK) == n480 + 1 and NOTE_SINK[-1]["kind"] == "SALT"
               and NOTE_SINK[-1]["reason"].startswith("SALT text -- a salt-wise item list without"))
            tw = os.path.join(tdir, "17476", "report.txt"); open(tw, "wb").write(cutsl)
            capture(tw, sp2, cap2, m480.append)
            ck("S480: its report.txt twin with the same bytes is not kept twice and sends no second note",
               len([f for f in os.listdir(refd) if hashlib.md5(cutsl).hexdigest() in f and f.endswith(".why.txt")]) == 1
               and len(NOTE_SINK) == n480 + 1)
            u2 = os.path.join(tdir, "17476", "user_aa2.txt"); open(u2, "wb").write(SL)
            ck("S480: the complete salt list under the same kind of name is TAKEN, as marg_txt's own .XLS",
               capture(u2, sp2, cap2, lambda m: None) is True
               and any(md5_of(os.path.join(sp2, f)) == hashlib.md5(marg_txt.convert(SL)[0]).hexdigest() for f in os.listdir(sp2)))
            ck("S480: every report's kind word reaches the note",
               sorted(set(note_of("x.txt", "0" * 32, M_[k_][:-60], "cut")["kind"] for k_ in M_))
               == sorted(["PURCHASE", "SALT", "CATEGORY", "ITEMS", "SALE_SHORT", "RETURN", "VALUATION", "EXPIRY", "LEDGER"]))
            cen = text_census([tdir])
            ck("S480: the census lists a text by its title even under a letterhead, and still never the notes",
               any("user_aa1.txt" in l and "SALT WISE ITEM LIST" in l for l in cen) and not any("shopping" in l for l in cen)
               and _title_of(u2) == "SALT WISE ITEM LIST")
            vfile = os.path.join(tdir, "val.txt"); open(vfile, "wb").write(M_["STOCK_VALUATION_BATCHWISE"])
            ck("S480: under a letterhead the census reads the report's title, not the shop's name",
               _title_of(vfile).startswith("WHOLE STORES STOCK VALUATION"))
            E_ = marg_txt.EMPTY_DAY_SAMPLE                       # AS ON 02-01-2030
            day = lambda d, h=10: time.mktime((2030, 1, d, h, 0, 0, 0, 0, -1))
            e1 = os.path.join(tdir, "17476", "user_ab1.txt"); open(e1, "wb").write(E_); os.utime(e1, (day(2), day(2)))
            m480 = []
            t1 = capture(e1, sp2, cap2, m480.append)
            emd5 = hashlib.md5(E_).hexdigest()
            ck("S480: a zero-bill sale report exported on its own day is refused in the staff's words, kept, and NOT remembered as seen",
               t1 is False and emd5 not in TXT_SEEN and any("kal ki tareekh" in m for m in m480)
               and NOTE_SINK[-1]["md5"] == emd5 and NOTE_SINK[-1]["reason"] == TODAY_NOTE and NOTE_SINK[-1]["kind"] == "SALE")
            old480 = os.path.join(refd, "20300102-094321__user_ab1__%s.txt" % emd5)
            kept_e = [f for f in os.listdir(refd) if emd5 in f and f.endswith(".txt") and not f.endswith(".why.txt")]
            os.replace(os.path.join(refd, kept_e[0]), old480); os.utime(old480, (day(9), day(9)))
            TXT_STAT.clear()
            ck("S480: its kept copy, offered again at a start, stays refused by the stamp in its name (whatever the copy's own file time)",
               len(kept_e) == 1 and capture_text(old480, sp2, cap2, lambda m: None) is False and emd5 not in TXT_SEEN
               and len([f for f in os.listdir(refd) if emd5 in f and f.endswith(".why.txt")]) == 1)
            e2 = os.path.join(tdir, "17476", "report.txt"); open(e2, "wb").write(E_); os.utime(e2, (day(3), day(3)))
            ck("S480: the SAME bytes exported the next day are taken as a no-sale day, as marg_txt's own EMPTY sheet",
               capture(e2, sp2, cap2, lambda m: None) is True
               and any(md5_of(os.path.join(sp2, f)) == hashlib.md5(marg_txt.convert(E_, exported_at=day(3))[0]).hexdigest()
                       for f in os.listdir(sp2)))
            # S488 (E.1): what of a refused text may leave for Drive -- every admitted kind's made-up text may, nothing else may
            adm = ("PURCHASE_BILLWISE", "PURCHASE_ITEMWISE", "PURCHASE_SUPPLIERWISE", "PURCHASE_BILLITEMWISE", "SALT_WISE_ITEM_LIST",
                   "CATEGORY_WISE_ITEM_LIST", "ITEM_MASTER", "STOCK_VALUATION_BATCHWISE", "STOCK_EXPIRY")
            ck("S488 (E.1): a purchase (four shapes), the salt, category and item lists, a valuation, an expiry report and the closing "
               "stock may leave", all(_may_leave(M_[k_]) for k_ in adm) and _may_leave(STK))
            ck("S488 (E.1): a sale (both shapes), a sale return (both), the stock register, an order sheet, an empty day, a note, "
               "nothing, a spreadsheet -- may not",
               not any(_may_leave(M_[k_]) for k_ in M_ if k_ not in adm) and not _may_leave(T) and not _may_leave(marg_txt.ORDER_SAMPLE)
               and not _may_leave(E_) and not _may_leave(b"milk, bread") and not _may_leave(b"") and not _may_leave(None)
               and not _may_leave(b"\xd0\xcf\x11\xe0" + M_["ITEM_MASTER"]))
            IM = M_["ITEM_MASTER"].split(b"\r\n")
            ph = lambda a, b: (a + b * 9).encode()              # a ten-digit run made here, never written out in this file
            ck("S488 (E.1): a person word at the head, a 'Phone :' line below line 8, a Marg line not at the end, a spaced ten-digit "
               "run -- each holds a list back",
               not _may_leave(b"\r\n".join(IM).replace(b"OTHER PRODUCTS", b"CUSTOMER LIST", 1))
               and not _may_leave(b"\r\n".join(IM[:9] + [b"Phone : " + ph("9", "7")] + IM[9:]))
               and not _may_leave(b"\r\n".join(IM[:9] + [b"MARG ERP " + ph("8", "6")] + IM[9:]))
               and not _may_leave(b"\r\n".join(IM).replace(b"DEMOCIN TAB", b"DEMOCIN " + ph("9", "8")[:5] + b" " + ph("9", "8")[5:], 1)))
            _s488_share_cases(ck, os.path.join(d, "w488"))      # S488 (walk 7.6, the medical PC)
        else:
            ck("S480: marg_txt S480 is beside this file (an older reader: the S480 checks cannot run)", False)
        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))
        TXT_LIVE_FORCE = None
    except ImportError:
        ck("marg_txt.py is beside this file", False)
    shutil.rmtree(d, ignore_errors=True)
    NOTE_SINK = None
    out("SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


WATCH_LOG = os.path.join(HERE, "marg_watch.log")


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
                fh.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), m))
        except Exception:                                       # noqa: BLE001
            pass
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Capture Marg exports before Marg overwrites them")
    ap.add_argument("--watch", nargs="*", default=None)
    ap.add_argument("--spool", default=DEFAULT_SPOOL)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--route", action="store_true")
    ap.add_argument("--poll", type=float, default=SAFETY_POLL_S)
    ap.add_argument("--archive"); ap.add_argument("--outbox")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    out = lambda m="": (print(m), sys.stdout.flush())
    if not a.selftest:
        out = _teed_out()                       # S395: the running watcher writes its log; a selftest does not
    if a.selftest:
        return selftest(out)
    extra = []
    if a.archive: extra += ["--archive", a.archive]
    if a.outbox:  extra += ["--outbox", a.outbox]
    try:
        _mt = _marg_txt().VERSION
    except Exception as ex:                                     # noqa: BLE001
        _mt = "absent (%s)" % ex.__class__.__name__
    out("marg_watch S480 starting -- text reader %s, text route %s, refusal notes on (a note that cannot go waits and is tried again)"
        % (_mt, "LIVE" if txt_live() else "ON HOLD"))
    watch(a.watch or DEFAULT_WATCH, a.spool, a.once, a.route, out, extra, a.poll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
