#!/usr/bin/env python3
"""marg_watch.py — capture Marg exports the instant they appear.  (S195)

THE PROBLEM
    Marg reuses slot names (REPORT_1.XLS, REPORT_2.XLS) for EVERY report type, so
    generating a new report OVERWRITES the previous file. Anything that only looks
    on a schedule loses an export that is overwritten between looks -- run a sale
    report then a stock report and the sale export is gone.

THE FIX — CAPTURE FIRST, CLASSIFY LATER, AND DO NOT POLL FOR IT
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

OFF SWITCH (S259)
    D:\\SendToClinic\\_off\\MARG_WATCH_OFF.txt stops capture. ALL_OFF.txt does NOT --
    capture is the one job whose loss cannot be undone. Read every cycle; no restart.
"""
import argparse, hashlib, os, queue, shutil, sys, threading, time

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
    """Cheap 'Marg has finished writing this' test — no xlrd, no parsing."""
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


def capture(path, spool, captured, out):
    """Copy the bytes into the spool, keyed by content. True if NEW."""
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
            if not n.lower().endswith(EXTS):
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
            files += [os.path.join(dirpath, n) for n in names if n.lower().endswith(EXTS)]
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
        out("  (event watch unavailable for %s — safety poll covers it)" % root)
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
                if name.lower().endswith(EXTS):
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
        out("  event-driven capture active on %d folder(s) — no polling gap" % started)
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
    if do_route and new:
        route(spool, out, route_extra); new = 0
    if once:
        return captured
    start_pusher(spool, out)            # S240: after the first sweep, never before it

    last_poll = time.time()
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
        if do_route and new:
            route(spool, out, route_extra); new = 0


def route(spool, out, extra=None):
    try:
        import marg_router
    except ImportError:
        out("  ! marg_router.py not beside this script — spool kept, not routed.")
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
    shutil.rmtree(d, ignore_errors=True)
    out("SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


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
    if a.selftest:
        return selftest(out)
    extra = []
    if a.archive: extra += ["--archive", a.archive]
    if a.outbox:  extra += ["--outbox", a.outbox]
    watch(a.watch or DEFAULT_WATCH, a.spool, a.once, a.route, out, extra, a.poll)
    return 0


if __name__ == "__main__":
    sys.exit(main())
