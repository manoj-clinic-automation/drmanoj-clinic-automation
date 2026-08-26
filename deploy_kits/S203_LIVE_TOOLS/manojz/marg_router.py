#!/usr/bin/env python3
"""marg_router.py — Marg export router: identify by CONTENT, verify at source,
rename by the data's own dates, archive, and offer for upload.  (S195)

WHY THIS EXISTS
    Marg writes every report type -- sale, stock, purchase, ... -- into the same
    per-login folder under a SLOT name (REPORT_1.XLS, REPORT_2.XLS). The name
    carries no type, no date, and slots are REUSED, so a fresh export silently
    overwrites an older one. Proven on real files: two different REPORT_1.XLS,
    one holding 01-Aug data, one holding 19-Aug.

    So the file's CONTENT decides what it is. (D188: a file is not identified by
    its name.)

BUILT FOR ANY FUTURE REPORT
    Marg's report engine always emits the same preamble shape:
        rows 0..n : single-cell lines (company, address, phone, TITLE + period)
        next row  : the COLUMN HEADER (3+ cells)
        then      : data
    So identification, date extraction and archiving are GENERIC -- they work on a
    report type nobody has taught this tool about yet. Only *deep* verification
    (full arithmetic) is per-type. A new report is onboarded by adding a block to
    signatures.json -- a data edit, no code change. `--learn` prints that block.

SAFETY
    * NEVER writes inside D:\\MARGERP -- it only reads and copies out.
    * Idempotent: keyed on content MD5 via index.csv; a file already archived is
      never re-archived and never re-sent.
    * Refuses rather than guesses: title/header must agree; unknown -> quarantine.
    * Only VERIFIED + uploadable files reach the Outbox.

USAGE
    marg_router.py --dry-run              # say what WOULD happen, touch nothing
    marg_router.py                        # do it
    marg_router.py --learn <file.xls>     # print a signature block for a new type
    marg_router.py --scan <dir> [...]     # override the source dirs
    marg_router.py --selftest             # offline checks
"""
import argparse, csv, datetime, hashlib, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_SCAN    = [r"D:\MARGERP\users"]
DEFAULT_ARCHIVE = r"D:\MargArchive"
DEFAULT_OUTBOX  = r"D:\SendToClinic\Outbox"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

RE_DATE  = re.compile(r"(\d{2})-(\d{2})-(\d{4})")
RE_ASON  = re.compile(r"AS\s+ON\s+(\d{2}-\d{2}-\d{4})", re.I)
RE_RANGE = re.compile(r"FROM\s+(\d{2}-\d{2}-\d{4})(?:\s+TO\s+(\d{2}-\d{2}-\d{4}))?", re.I)
# S201: date_from/date_to are what the TITLE claims. data_from/data_to are
# the dates the ROWS actually carry. They differ -- a title reading
# "FROM 23-08 TO 24-08" over a file holding only 24-Aug misled a reader
# into believing 23-Aug traded nothing. Record both; never infer one.
INDEX_COLS = ["seen_at","type","variant","date_from","date_to",
              "data_from","data_to","export_stamp","md5",
              "verdict","reason","rows","archived_path","source_path","uploaded"]


def now_ist():
    return datetime.datetime.now(IST)


def iso(d):
    m = RE_DATE.fullmatch((d or "").strip())
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else None


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


# --------------------------------------------------------------------------- #
# generic reading — works on ANY Marg export
# --------------------------------------------------------------------------- #

def open_sheet(path):
    """.xlsx via the stdlib reader, .xls via xlrd.

    S201: xlrd 1.2.0 reads .xlsx only below Python 3.9 (ElementTree.getiterator
    was removed there). This machine reads .xlsx today ONLY because its Python
    is old enough -- the day it is upgraded every .xlsx export would come back
    as "not a readable .xls", looking like a refusal rather than a breakage.
    xlsx_stdlib removes the dependency instead of pinning it; it was validated
    cell-for-cell against openpyxl on a real Marg export before being wired in.
    xlrd is kept as a fallback so an odd file still gets a second chance.
    """
    if path.lower().endswith(".xlsx"):
        try:
            import xlsx_stdlib
            return xlsx_stdlib.open_workbook(path).sheet_by_index(0)
        except Exception as first:                             # noqa: BLE001
            try:
                import xlrd
                return xlrd.open_workbook(path).sheet_by_index(0)
            except Exception:                                  # noqa: BLE001
                raise first
    import xlrd
    return xlrd.open_workbook(path).sheet_by_index(0)


def cell(sh, r, c):
    return norm(sh.cell_value(r, c)) if c < sh.ncols else ""


def read_preamble(sh, look=25):
    """Return (title, header_cols, header_row). GENERIC: the header row is the
    first row carrying 3+ non-empty cells; the title is the last single-cell line
    above it. This is the shape Marg's report engine always emits, so it holds for
    report types this tool has never seen."""
    header_row, header = None, []
    for r in range(min(sh.nrows, look)):
        cells = [cell(sh, r, c) for c in range(sh.ncols)]
        filled = [c for c in cells if c]
        if len(filled) >= 3:
            header_row = r
            header = [c for c in cells if c]
            break
    title = ""
    upto = header_row if header_row is not None else min(sh.nrows, look)
    for r in range(upto):
        t = cell(sh, r, 0)
        if t:
            title = t          # last non-empty single-cell line wins
    return title, header, header_row


def dates_from(title, sh, header_row):
    """Dates the file's DATA covers. Title first, then the body's own date groups
    as a cross-check (and as a fallback for a report with no dates in its title)."""
    d_from = d_to = None
    m = RE_ASON.search(title or "")
    if m:
        d_from = d_to = iso(m.group(1))
    else:
        m = RE_RANGE.search(title or "")
        if m:
            d_from = iso(m.group(1))
            d_to = iso(m.group(2)) if m.group(2) else d_from
    body = []
    if header_row is not None:
        for r in range(header_row + 1, sh.nrows):
            v = iso(cell(sh, r, 0))
            if v:
                body.append(v)
    b_from, b_to = (min(body), max(body)) if body else (None, None)
    if d_from is None:
        d_from, d_to = b_from, b_to
    return d_from, d_to, b_from, b_to


def ends_with(sh, marker, tail=40):
    if not marker:
        return True
    for r in range(max(0, sh.nrows - tail), sh.nrows):
        for c in range(sh.ncols):
            if marker.upper() in cell(sh, r, c).upper():
                return True
    return False


# --------------------------------------------------------------------------- #
# identification
# --------------------------------------------------------------------------- #

def load_signatures(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["signatures"]


def identify(title, header, sigs):
    """(sig, status, reason). BOTH title and header must agree.
    title matches + header does not -> REFUSED (layout changed / wrong variant).
    nothing matches -> UNKNOWN (quarantined, never guessed at)."""
    title_hits = []
    for s in sigs:
        if re.search(s["title_regex"], title or "", re.I):
            title_hits.append(s)
            exp = [norm(x).upper() for x in s["header"]]
            got = [norm(x).upper() for x in header][:len(exp)]
            if got == exp:
                return s, "IDENTIFIED", ""
    if title_hits:
        return None, "REFUSED", (
            "title matches %s but the column layout does not (got %r). A file is "
            "not identified by its name, and a partial match is never parsed."
            % ("/".join(sorted({t["type"] for t in title_hits})), header[:10]))
    return None, "UNKNOWN", "no signature matches this title: %r" % (title or "")[:90]


# --------------------------------------------------------------------------- #
# verification AT SOURCE
# --------------------------------------------------------------------------- #

def verify(path, sh, sig, title, header, header_row, d_from, d_to, b_from, b_to):
    """Returns (verdict, reason). VERIFIED only when the file can be trusted."""
    problems = []
    if header_row is None:
        problems.append("no column-header row found")
    if not (d_from and d_to):
        problems.append("no data dates could be established")
    # title vs body must agree (the core source-side integrity check)
    if d_from and b_from and (b_from < d_from or (b_to or b_from) > (d_to or d_from)):
        problems.append("the title says %s..%s but the rows carry %s..%s"
                        % (d_from, d_to, b_from, b_to))
    if sig and not ends_with(sh, sig.get("end_marker")):
        problems.append("TRUNCATED — the completeness marker %r is missing; the "
                        "export stopped early" % sig.get("end_marker"))
    if problems:
        return "REFUSED", " | ".join(problems)

    if sig and sig.get("deep_verify") == "marg_report":
        try:
            import marg_report
            rep = marg_report.read_report(path)
        except ImportError:
            return "VERIFIED", "structural only (marg_report not importable)"
        except Exception as ex:                                    # noqa: BLE001
            return "REFUSED", "deep parse failed: %s" % ex
        if not rep.get("ok"):
            return "REFUSED", " | ".join(rep.get("errors") or ["deep checks failed"])
        return "VERIFIED", ""
    return "VERIFIED", "structural"


# --------------------------------------------------------------------------- #
# index + archive
# --------------------------------------------------------------------------- #

def load_index(p):
    seen = {}
    if os.path.exists(p):
        with open(p, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                seen[row.get("md5", "")] = row
    return seen


def append_index(p, row):
    new = not os.path.exists(p)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=INDEX_COLS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in INDEX_COLS})


def canonical_name(typ, variant, d_from, d_to, stamp, digest, ext=".xls"):
    if d_from and d_to and d_from != d_to:
        dates = "%s_to_%s" % (d_from, d_to)
    else:
        dates = d_from or "nodate"
    parts = [p for p in (typ, variant) if p]
    return "%s__%s__%s__%s%s" % ("_".join(parts), dates, stamp, digest[:8], ext)


def pdf_facts(path):
    """(ok, reason, pages). Structural checks only -- no PDF library exists on
    these machines and none is being added for this.

    A PDF has the same two integrity questions as a Marg .xls: is it really the
    format it claims, and did it finish? %PDF at the head answers the first,
    %%EOF at the tail answers the second. A print interrupted half way has no
    %%EOF, exactly as a truncated export has no GRAND TOTAL row.
    """
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            head = fh.read(1024)
            fh.seek(max(0, size - 4096))
            tail = fh.read(4096)
    except OSError as ex:
        return False, "cannot read the file (%s)" % ex, 0
    if not head.startswith(b"%PDF"):
        return False, "not really a PDF (no %PDF header)", 0
    if b"%%EOF" not in tail:
        return False, ("TRUNCATED -- no %%EOF at the end; the print or export "
                       "stopped before the file was finished"), 0
    pages = head.count(b"/Type/Page") + tail.count(b"/Type/Page")
    return True, "", pages


def process_pdf(path, res, cfg, out):
    """Capture, verify and archive a PDF -- and say plainly that it cannot
    reach the books.

    Marg prints and exports PDFs. Until S201 the watcher ignored them for their
    extension and wrote no log line, so a report produced as a PDF was invisible
    to the archive, the server and every health check -- and the alarm that
    eventually fired blamed the network. Archiving it is not the same as being
    able to use it: no figures can be read out of a PDF here. So it is kept,
    hashed, dated and offsited, and the reason field tells the reader what to do
    instead.
    """
    ok, why, pages = pdf_facts(path)
    stamp = datetime.datetime.fromtimestamp(os.path.getmtime(path), IST)
    d = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
    res["type"], res["variant"] = ("DOCUMENT_PDF", "")
    res["date_from"] = res["date_to"] = d          # a PDF carries no readable
    res["data_from"] = res["data_to"] = ""         # business date here
    res["export_stamp"] = stamp.strftime("%Y%m%d-%H%M%S")
    res["rows"] = pages
    res["verdict"] = "VERIFIED" if ok else "REFUSED"
    res["reason"] = why if not ok else (
        "captured and archived. A PDF cannot be read into the books -- if these "
        "figures are needed, run the same report again and save it as Excel.")

    folder = os.path.join(cfg["archive"],
                          "DOCUMENT_PDF" if ok else "_REFUSED",
                          d[:7] if ok else "")
    name = canonical_name(res["type"] if ok else "UNKNOWN", "", d, d,
                          res["export_stamp"], res["md5"], ".pdf")
    dest = os.path.join(folder, name)
    res["archived_path"] = dest
    out("  %-9s %-22s %s -> %s" % (res["verdict"], "DOCUMENT_PDF/-", d,
                                   os.path.basename(dest)))
    out("            %s" % res["reason"][:160])
    if not cfg["dry"]:
        os.makedirs(folder, exist_ok=True)
        shutil.copy2(path, dest)
        with open(os.path.splitext(dest)[0] + ".txt", "w", encoding="utf-8") as fh:
            fh.write("verdict: %s\nreason: %s\npages(approx): %s\nsource: %s\n"
                     % (res["verdict"], res["reason"], pages, path))
        append_index(cfg["index"], res)
    return res


def process(path, sigs, cfg, seen, out):
    res = {"source_path": path, "seen_at": now_ist().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        digest = md5_of(path)
    except OSError as ex:
        out("  ! cannot read %s: %s" % (path, ex)); return None
    res["md5"] = digest
    if digest in seen:
        out("  = already indexed, skipping: %s" % os.path.basename(path)); return None
    if os.path.splitext(path)[1].lower() == ".pdf":
        return process_pdf(path, res, cfg, out)
    try:
        sh = open_sheet(path)
    except Exception as ex:                                        # noqa: BLE001
        res.update(type="", variant="", verdict="REFUSED",
                   reason="not a readable .xls (%s)" % ex, rows=0)
        return res
    res["rows"] = sh.nrows
    title, header, hrow = read_preamble(sh)
    sig, status, why = identify(title, header, sigs)
    d_from, d_to, b_from, b_to = dates_from(title, sh, hrow)
    # S195: a report whose only dates are FUTURE ones (stock expiring before a
    # cutoff) can never be dated from its content. A signature may declare
    # dating:file_mtime, and then the export's own file time IS the data date --
    # a stock/expiry report describes the moment it was generated.
    if sig and sig.get("dating") == "file_mtime" and not d_from:
        _ft = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
        d_from = d_to = _ft
        b_from = b_to = None
    res["date_from"], res["date_to"] = d_from or "", d_to or ""
    res["data_from"], res["data_to"] = b_from or "", b_to or ""

    if status == "IDENTIFIED":
        res["type"], res["variant"] = sig["type"], sig.get("variant", "")
        verdict, reason = verify(path, sh, sig, title, header, hrow,
                                 d_from, d_to, b_from, b_to)
    elif status == "REFUSED":
        res["type"], res["variant"] = "", ""
        verdict, reason = "REFUSED", why
    else:
        res["type"], res["variant"] = "_UNKNOWN", ""
        # still verify what CAN be checked generically, so an unknown type is
        # archived with an honest structural verdict rather than a shrug
        v2, r2 = verify(path, sh, None, title, header, hrow, d_from, d_to, b_from, b_to)
        verdict = "UNKNOWN" if v2 == "VERIFIED" else "REFUSED"
        reason = why if v2 == "VERIFIED" else (why + " | " + r2)
        res["title_seen"] = title
    res["verdict"], res["reason"] = verdict, reason

    stamp = datetime.datetime.fromtimestamp(os.path.getmtime(path), IST).strftime("%Y%m%d-%H%M%S")
    res["export_stamp"] = stamp
    if verdict == "VERIFIED":
        folder = os.path.join(cfg["archive"], res["type"], (d_from or "unknown")[:7])
    elif verdict == "UNKNOWN":
        folder = os.path.join(cfg["archive"], "_UNKNOWN")
    else:
        folder = os.path.join(cfg["archive"], "_REFUSED")
    name = canonical_name(res["type"] or "UNKNOWN", res["variant"], d_from, d_to,
                          stamp, digest, os.path.splitext(path)[1] or ".xls")
    dest = os.path.join(folder, name)
    res["archived_path"] = dest

    out("  %-9s %-22s %s -> %s" % (verdict, (res["type"] or "?") + "/" + (res["variant"] or "-"),
                                   (d_from or "?") + (".." + d_to if d_to and d_to != d_from else ""),
                                   os.path.basename(dest)))
    if reason:
        out("            reason: %s" % reason[:160])

    if not cfg["dry"]:
        os.makedirs(folder, exist_ok=True)
        shutil.copy2(path, dest)
        if verdict != "VERIFIED":
            with open(os.path.splitext(dest)[0] + ".txt", "w", encoding="utf-8") as fh:
                fh.write("verdict: %s\nreason: %s\ntitle: %s\nheader: %s\nsource: %s\n"
                         % (verdict, reason, title, header, path))
        if verdict == "VERIFIED" and sig and sig.get("uploadable"):
            os.makedirs(cfg["outbox"], exist_ok=True)
            shutil.copy2(path, os.path.join(cfg["outbox"], name))
            res["uploaded"] = "queued"
            out("            -> queued for upload in Outbox")
        append_index(cfg["index"], res)
    return res


def TITLE_RE_FOR(title):
    """Build a whitespace-tolerant regex from a report title, WITHOUT the escaping
    games that produce an over-escaped string when dumped to JSON."""
    core = re.split(r"\s+AS\s+ON\s+|\s+FROM\s+", title or "", 1, flags=re.I)[0].strip()
    return r"\s+".join(re.escape(w) for w in core.split())


def learn(path, out):
    sh = open_sheet(path)
    title, header, _ = read_preamble(sh)
    block = {
        "type": "CHANGE_ME", "variant": "DEFAULT",
        "title_regex": TITLE_RE_FOR(title),
        "header": header,
        "deep_verify": "structural", "uploadable": False,
    }
    out("title seen : %s" % title)
    out("header seen: %s" % header)
    out("\nPaste this into signatures.json -> \"signatures\" (set type/variant):\n")
    out(json.dumps(block, indent=2))


def selftest(out):
    ok = True
    def ck(n, c):
        nonlocal ok
        out(("  OK   " if c else "  FAIL ") + n); ok = ok and c
    ck("iso", iso("19-08-2026") == "2026-08-19")
    ck("iso junk", iso("nope") is None)
    ck("canonical single-day",
       canonical_name("SALE_BILLWISE","DETAIL","2026-08-19","2026-08-19","20260821-0623","abcdef1234")
       == "SALE_BILLWISE_DETAIL__2026-08-19__20260821-0623__abcdef12.xls")
    ck("canonical range",
       "2026-08-01_to_2026-08-15" in
       canonical_name("SALE_BILLWISE","DETAIL","2026-08-01","2026-08-15","s","h"*8))
    sigs = load_signatures(os.path.join(HERE, "signatures.json"))
    s, st, _ = identify("BILL WISE SALES STATEMENT AS ON 19-08-2026",
        ["BILL NO.","DESCRIPTION","D.R.","GROSS AMT.","DISCOUNT","TAX","DR/CR","NET AMT.","CASH"], sigs)
    ck("identifies the sale DETAIL report", st == "IDENTIFIED" and s["variant"] == "DETAIL")
    s2, st2, _ = identify("BILL WISE SALES STATEMENT AS ON 19-08-2026",
                          ["BILL NO.","DESCRIPTION","BILL VALUE"], sigs)
    ck("identifies the CASH-less SUMMARY1 variant", st2 == "IDENTIFIED" and s2["variant"] == "SUMMARY1")
    ck("SUMMARY1 is never uploadable", s2.get("uploadable") is False)

    # PDFs: kept, checked for completeness, never mistaken for data
    import tempfile as _tf
    _d = _tf.mkdtemp()
    _good = os.path.join(_d, "good.pdf")
    with open(_good, "wb") as _fh:
        _fh.write(b"%PDF-1.4\n/Type/Page\n" + b"x" * 200 + b"\n%%EOF\n")
    _bad = os.path.join(_d, "cut.pdf")
    with open(_bad, "wb") as _fh:
        _fh.write(b"%PDF-1.4\n/Type/Page\n" + b"x" * 200)
    _not = os.path.join(_d, "lying.pdf")
    with open(_not, "wb") as _fh:
        _fh.write(b"this is not a pdf at all")
    ck("a complete PDF passes", pdf_facts(_good)[0] is True)
    ck("a PDF with no %%EOF is refused as truncated",
       pdf_facts(_bad)[0] is False and "TRUNCATED" in pdf_facts(_bad)[1])
    ck("a file that only claims to be a PDF is refused",
       pdf_facts(_not)[0] is False)
    ck("a missing PDF is refused, not crashed",
       pdf_facts(os.path.join(_d, "nope.pdf"))[0] is False)
    shutil.rmtree(_d, ignore_errors=True)
    _, st3, _ = identify("BILL WISE SALES STATEMENT AS ON 19-08-2026", ["WRONG","COLS","HERE"], sigs)
    ck("title match + wrong layout is REFUSED, not parsed", st3 == "REFUSED")
    # NB: use a title that can never be in the registry. An earlier version of
    # this check used a REAL report name and went red the day that report was
    # onboarded -- a test asserting frozen state (the F-106 shape).
    _, st4, _ = identify("ZZ NOT A REAL MARG REPORT QX9", ["ALPHA","BETA","GAMMA"], sigs)
    ck("an unteached report is UNKNOWN, not guessed", st4 == "UNKNOWN")
    ck("registry is data-driven (>=1 signature loaded)", len(sigs) >= 1)
    out("SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Marg export router")
    ap.add_argument("--scan", nargs="*", default=None)
    ap.add_argument("--archive", default=DEFAULT_ARCHIVE)
    ap.add_argument("--outbox", default=DEFAULT_OUTBOX)
    ap.add_argument("--signatures", default=os.path.join(HERE, "signatures.json"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--learn", metavar="FILE")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    out = lambda m="": print(m)

    if a.selftest:
        return selftest(out)
    if a.learn:
        learn(a.learn, out); return 0

    cfg = {"archive": a.archive, "outbox": a.outbox, "dry": a.dry_run,
           "index": os.path.join(a.archive, "index.csv")}
    sigs = load_signatures(a.signatures)
    seen = load_index(cfg["index"])
    roots = a.scan if a.scan else DEFAULT_SCAN

    files = []
    for root in roots:
        if os.path.isfile(root):
            files.append(root); continue
        for dirpath, _dirs, names in os.walk(root):
            for n in names:
                # S201: .pdf included, or a PDF captured into the spool is
                # never even LOOKED at -- process() could classify it but the
                # walk that feeds process() would never hand it over. Two
                # filters decide what is seen; both must agree.
                if n.lower().endswith((".xls", ".xlsx", ".pdf")):
                    files.append(os.path.join(dirpath, n))
    files.sort()
    out("Marg router%s — %d file(s) under %s"
        % (" [DRY RUN]" if a.dry_run else "", len(files), ", ".join(roots)))
    out("archive: %s   outbox: %s" % (a.archive, a.outbox))
    out("")
    counts = {}
    for f in files:
        r = process(f, sigs, cfg, seen, out)
        if r:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
            seen[r["md5"]] = r
    out("")
    out("summary: " + (", ".join("%s=%d" % kv for kv in sorted(counts.items())) or "nothing new"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
