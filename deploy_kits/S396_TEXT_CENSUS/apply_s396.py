#!/usr/bin/env python3
"""apply_s396.py -- kit S396_TEXT_CENSUS (F-620). Anchored on the medical PC's marg_watch.py 61414a5a (S395).

25-Sep-2026: 24-Sep's bill-wise text export was still not taken at 05:45 IST, after S395's restart looked at
every report*.txt again -- and what S395 writes lives on the medical PC, which can be read only through Dr
Manoj's PC, whose link was down. So:

  * ANY .txt in the watched folders is looked at, not only report*.txt -- Marg names files as it pleases;
    what is inside decides. A file is re-read only when its size or time changes.
  * Every ten minutes the watcher writes a CENSUS of every .txt written in the last three days -- in its
    folders, on the stick, on D:\\ top level, in C:\\Users\\Public\\Documents and in every account's Desktop,
    Documents and Downloads -- with what it made of each (taken / already taken / not taken and why /
    outside the watched folders), and the report title where it is one. Names of patients never appear:
    only a report's own title line is shown. The census and the tail of marg_watch.log are written beside
    the heartbeat in Drive's Clinic Data Archive\\FromMedical, readable without Dr Manoj's PC.
  * Only report-like text (the name begins with "report", or it carries a STATEMENT title) is copied to
    _captured_txt\\refused -- never any other text file.

  python3 apply_s396.py --src marg_watch.py --out DIR
"""
import argparse, hashlib, os
ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
s = open(a.src, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "61414a5ad9f467510e26fffd057e8858", "marg_watch.py is not 61414a5a (S395)"


def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not unique or absent: " + old[:80]
    s = s.replace(old, new)


rep('''OFF SWITCH (S259)''', '''S396 (25-Sep-2026, F-620): ANY .txt in the watched folders is looked at (the content decides, not the
    name), and every ten minutes a census of recent text files and the tail of marg_watch.log are written
    to Drive's Clinic Data Archive\\\\FromMedical beside the heartbeat.

OFF SWITCH (S259)''')

rep('''TXT_NAME = re.compile(r"^report[^\\\\/]*\\.txt$", re.I)''',
    '''TXT_NAME = re.compile(r"^[^\\\\/]*\\.txt$", re.I)     # S396: any .txt -- the content decides
REPORTISH = re.compile(r"^report", re.I)
TXT_STAT = {}           # S396: path -> (size, mtime) when last judged; unchanged files are not re-read
TXT_VERDICT = {}        # S396: path -> (when, verdict) -- what the census reports''')

# judge once per change, and remember the verdict
rep('''    tmd5 = hashlib.md5(raw).hexdigest()
    if tmd5 in TXT_SEEN:
        return False
    try:
        marg_txt = _marg_txt()''', '''    tmd5 = hashlib.md5(raw).hexdigest()
    try:
        st = os.stat(path); stat_key = (st.st_size, st.st_mtime)
    except OSError:
        stat_key = None
    if tmd5 in TXT_SEEN:
        if stat_key:
            TXT_STAT[path] = stat_key
        return False
    try:
        marg_txt = _marg_txt()''')

rep('''    if not marg_txt.recognise(raw):
        # S395: finished (size held still above) but not a report the reader knows -- keep it and say why,
        # once. A later, complete version has other bytes and is looked at afresh.
        _keep_refused(path, raw, tmd5, spool, out, _why_not(raw))
        TXT_SEEN.add(tmd5)
        return False''', '''    if not marg_txt.recognise(raw):
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
        return False''')

rep('''        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        _keep_refused(path, raw, tmd5, spool, out, "the reader refused it: %s" % str(ex)[:400])''',
    '''        out("  ! %s: a text export marg_txt would not convert -- %s" % (os.path.basename(path), str(ex)[:160]))
        _keep_refused(path, raw, tmd5, spool, out, "the reader refused it: %s" % str(ex)[:400])
        TXT_VERDICT[path] = (time.time(), "NOT TAKEN: the reader refused it: %s" % str(ex)[:300])''')

rep('''    digest = hashlib.md5(xls).hexdigest()
    TXT_SEEN.add(tmd5)
    if digest in captured:
        return False''', '''    digest = hashlib.md5(xls).hexdigest()
    TXT_SEEN.add(tmd5)
    if stat_key:
        TXT_STAT[path] = stat_key
    if digest in captured:
        TXT_VERDICT.setdefault(path, (time.time(), "already taken earlier (the same report, byte for byte)"))
        if not TXT_VERDICT[path][1].startswith("TAKEN"):
            TXT_VERDICT[path] = (time.time(), "already taken earlier (the same report, byte for byte)")
        return False''')

rep('''    captured.add(digest)
    out("  + CAPTURED %s (text) -> %s  (converted by marg_txt %s)" % (os.path.basename(path),''',
    '''    captured.add(digest)
    TXT_VERDICT[path] = (time.time(), "TAKEN -> %s" % os.path.basename(dest))
    out("  + CAPTURED %s (text) -> %s  (converted by marg_txt %s)" % (os.path.basename(path),''')

rep('''            out("  = HELD %s (text) -> _captured_txt\\held  (the text reader is on hold; nothing sent)"
                % os.path.basename(path))''', '''            out("  = HELD %s (text) -> _captured_txt\\held  (the text reader is on hold; nothing sent)"
                % os.path.basename(path))
            TXT_VERDICT[path] = (time.time(), "HELD (the text reader is on hold; nothing sent)")''')

# skip unchanged text files cheaply, before settling / reading
rep('''    """S389: a Marg text export -> the same .XLS Marg's Excel export is, into the spool. True if NEW."""
    try:''', '''    """S389: a Marg text export -> the same .XLS Marg's Excel export is, into the spool. True if NEW."""
    try:
        st0 = os.stat(path)
        if TXT_STAT.get(path) == (st0.st_size, st0.st_mtime):
            return False                        # S396: judged already, and not changed since
    except OSError:
        return False
    try:''')

# the census
rep('''def capture_text(path, spool, captured, out):''', '''CENSUS_EVERY_S = 600
CENSUS_DAYS = 3
CENSUS_FILE = os.path.join(HERE, "marg_text_census.txt")


def _from_medical():
    """The Drive folder the agent writes its heartbeat into, on whatever letter Drive has today."""
    for L in "DEFGHIJKLMNOPQRSTUVWXYZ":
        p = "%s:\\\\My Drive\\\\Clinic Data Archive\\\\FromMedical" % L
        if os.path.isdir(p):
            return p
    return None


def _census_dirs(roots):
    """(folder, walk-depth, watched?) -- everywhere a text export might land."""
    out = [(r, 6, True) for r in roots] + [(r, 0, True) for r in FLAT_ROOTS]
    if sys.platform.startswith("win"):
        out.append(("D:\\\\", 0, False))
        out.append((r"C:\\Users\\Public\\Documents", 1, False))
        try:
            for u in os.listdir("C:\\\\Users"):
                for sub in ("Desktop", "Documents", "Downloads"):
                    p = os.path.join("C:\\\\Users", u, sub)
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
        base_depth = base.rstrip("\\\\/").count(os.sep)
        for dirpath, dirs, names in os.walk(base):
            if dirpath.rstrip("\\\\/").count(os.sep) - base_depth >= depth:
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
                if not t and v in ("not a Marg report", "OUTSIDE the watched folders", "not looked at yet") \\
                        and not REPORTISH.match(n):
                    continue                            # someone's own notes: not listed
                lines.append("%s  %8d  %s\\n      -> %s%s" % (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)), st.st_size, p, v,
                    ("\\n      title: %s" % t) if t else ""))
    lines.sort(reverse=True)
    return lines


def publish_diagnostics(roots, out):
    """S396: the census and the log's tail, locally and in Drive's FromMedical."""
    try:
        body = ("MARG TEXT CENSUS  %s  (marg_watch S396; text route %s)\\n"
                "Every .txt written in the last %d days where a Marg text export could land, newest first.\\n\\n"
                % (time.strftime("%Y-%m-%d %H:%M:%S"), "LIVE" if txt_live() else "ON HOLD", CENSUS_DAYS))
        rows = text_census(roots)
        body += "\\n".join(rows) if rows else "(none)"
        body += "\\n"
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
    except Exception as ex:                                     # noqa: BLE001 -- diagnostics never stop capture
        out("  ! census could not be written: %s" % ex)


def capture_text(path, spool, captured, out):''')

# call it: after the first sweep and every ten minutes
rep('''    start_pusher(spool, out)            # S240: after the first sweep, never before it

    last_poll = time.time()''', '''    start_pusher(spool, out)            # S240: after the first sweep, never before it

    last_poll = time.time()
    publish_diagnostics(roots, out)         # S396
    last_census = time.time()''')
rep('''        if time.time() - last_poll >= poll_s:     # safety net under the events
            new += sweep()
            last_poll = time.time()''', '''        if time.time() - last_poll >= poll_s:     # safety net under the events
            new += sweep()
            last_poll = time.time()
        if time.time() - last_census >= CENSUS_EVERY_S:           # S396
            publish_diagnostics(roots, out)
            last_census = time.time()''')

# selftest: any name, content decides; other text is not kept; the census lists it
rep('''        # S395: a finished report*.txt that is not taken is kept, with its reason''', '''        # S396: a report under ANY name is taken; someone's notes are neither kept nor listed
        TXT_SEEN.clear()
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
        # S395: a finished report*.txt that is not taken is kept, with its reason''')

# the selftest forgets the stat cache wherever it forgets what it has seen
i = s.index("def selftest(")
s = s[:i] + s[i:].replace("TXT_SEEN.clear()", "TXT_SEEN.clear(); TXT_STAT.clear()")

# plain ASCII throughout -- this file travels through the Drive connector as text (S396)
s = s.replace("\u2014", "--")
assert all(ord(c) < 128 for c in s), "non-ASCII left"

os.makedirs(a.out, exist_ok=True)
open(os.path.join(a.out, "marg_watch.py"), "w", encoding="utf-8", newline="\n").write(s)
print("marg_watch.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())
