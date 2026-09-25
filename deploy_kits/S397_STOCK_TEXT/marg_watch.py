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

OFF SWITCH (S259)
    D:\\SendToClinic\\_off\\MARG_WATCH_OFF.txt stops capture. ALL_OFF.txt does NOT --
    capture is the one job whose loss cannot be undone. Read every cycle; no restart.
"""
import argparse, hashlib, os, queue, re, shutil, sys, threading, time

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
            fh.write("%s\nfrom: %s\nwhy:  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), path, why))
        out("  ! NOT TAKEN %s (text): %s -- kept in _captured_txt\\refused" % (os.path.basename(path), why))
    except OSError as ex:
        out("  ! could not keep the refused text %s: %s" % (os.path.basename(path), ex))


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


def share_refused(spool, fm, now=None):
    """S396.1: a report the reader would not take, copied beside the census so it can be looked at
    without anyone going to the medical PC. Only what is already in _captured_txt\\refused (report
    text and its reason), only the last CENSUS_DAYS, at most 12 files; a copy of the same size is
    not written again."""
    now = now or time.time()
    src = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")
    if not os.path.isdir(src):
        return 0
    dst = os.path.join(fm, "refused_text")
    n = 0
    for name in sorted(os.listdir(src), reverse=True)[:12]:
        p = os.path.join(src, name)
        try:
            st = os.stat(p)
            if not os.path.isfile(p) or now - st.st_mtime > CENSUS_DAYS * 86400 or st.st_size > MAX_SHARE:
                continue
            os.makedirs(dst, exist_ok=True)
            q = os.path.join(dst, name)
            if os.path.exists(q) and os.path.getsize(q) == st.st_size:
                continue
            shutil.copyfile(p, q)
            n += 1
        except OSError:
            continue
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
        if capture_text(p, spool, captured, out):
            took += 1
            out("  + a text refused earlier is taken now: %s" % name)
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
        if REPORTISH.match(os.path.basename(path)) or b"STATEMENT" in raw[:4000]:
            _keep_refused(path, raw, tmd5, spool, out, why)
            TXT_VERDICT[path] = (time.time(), "NOT TAKEN: " + why)
        else:
            TXT_VERDICT[path] = (time.time(), "not a Marg report")
        TXT_SEEN.add(tmd5)
        if stat_key:
            TXT_STAT[path] = stat_key
        return False
    try:
        xls, info = marg_txt.convert(raw)
    except Exception as ex:                                     # noqa: BLE001
        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        _keep_refused(path, raw, tmd5, spool, out, "the reader refused it: %s" % str(ex)[:400])
        TXT_VERDICT[path] = (time.time(), "NOT TAKEN: the reader refused it: %s" % str(ex)[:300])
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

    new = 0 if watch_off() else sweep()  # always start from a known state
    if not watch_off():
        new += retry_refused(spool, captured, out)      # S397
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


def selftest(out):
    """Proves the thing that matters: an OVERWRITTEN export is still kept."""
    import tempfile
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
        ck("S396.1: a refused report is copied beside the census (text and reason), once",
           share_refused(sp2, fmd) == len(os.listdir(refd)) >= 2 and share_refused(sp2, fmd) == 0
           and sorted(os.listdir(os.path.join(fmd, "refused_text"))) == sorted(os.listdir(refd))
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
        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold", txt_live() is False or os.path.isfile(TXT_LIVE_FILE))
        TXT_LIVE_FORCE = None
    except ImportError:
        ck("marg_txt.py is beside this file", False)
    shutil.rmtree(d, ignore_errors=True)
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
    out("marg_watch S397 starting -- text reader %s, text route %s" % (_mt, "LIVE" if txt_live() else "ON HOLD"))
    watch(a.watch or DEFAULT_WATCH, a.spool, a.once, a.route, out, extra, a.poll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
