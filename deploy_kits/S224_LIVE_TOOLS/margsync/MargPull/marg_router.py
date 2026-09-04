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
    * S224 (F-235): a VERIFIED STOCK_CLOSING / STOCK_EXPIRY export is named by
      what it holds -- STOCK_CLOSING_ORTHOTICS / _SUBSET, STOCK_EXPIRY_EXPIRED
      / _NEAR / _MIXED -- and index.csv carries the evidence in "notes".

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
              "verdict","reason","rows","archived_path","source_path","uploaded",
              "notes"]
# S224 (F-235): "notes" is the 16th column. key=value pairs separated by ";"
# -- layout=TOTALS;items=81;named=ORTHOTICS STOCK 27 AUGUST;subset=true;...
# It exists because a category-FILTERED closing-stock export and the FULL
# shop export for the same as-on date used to be filed under one name, and an
# ALREADY-EXPIRED expiry report and a NEAR-expiry one likewise. Marg writes no
# discriminator; the record now does.

# --------------------------------------------------------------------------- #
# S224 (F-235): variant naming for STOCK_CLOSING / STOCK_EXPIRY
# --------------------------------------------------------------------------- #
STOCK_TYPES = ("STOCK_CLOSING", "STOCK_EXPIRY")
SUBSET_WINDOW_DAYS = 45          # the reference universe looks back this far
SUBSET_MAX_FRACTION = 0.60       # a strict subset this small is a filter,
                                 # not a shrinking shop
UNIVERSE_CACHE = "_stock_universe.json"
# (a) words an operator types into the file name when a stock export was
# filtered to one category. Read from real _spool names on 04-Sep-2026
# (ORTHOTICS, ORTHOTIC) and extended with the categories the shop sells.
# WHOLE / FULL / MAIN are deliberately absent: they mean the opposite.
CATEGORY_WORDS = {
    "ORTHO": "ORTHOTICS", "ORTHOTIC": "ORTHOTICS", "ORTHOTICS": "ORTHOTICS",
    "SURGICAL": "SURGICAL", "SURGICALS": "SURGICAL",
    "SCRAP": "SCRAP",
    "BRACE": "BRACE", "BRACES": "BRACE",
    "BELT": "BELT", "BELTS": "BELT",
    "SUPPORT": "SUPPORT", "SUPPORTS": "SUPPORT",
    "DEVICE": "DEVICE", "DEVICES": "DEVICE",
    "OTC": "OTC",
    "GENERIC": "GENERIC", "GENERICS": "GENERIC",
    "IMPLANT": "IMPLANT", "IMPLANTS": "IMPLANT",
    "PHARMA": "PHARMA", "MEDICINE": "PHARMA", "MEDICINES": "PHARMA",
}
RE_STAMP_PREFIX = re.compile(r"^\d{8}-\d{6}__")
RE_MD5_SUFFIX = re.compile(r"__[0-9a-f]{8}$", re.I)
RE_SLOT_NAME = re.compile(r"^(REPORT_?\d*|REPORT[_-]\S*|report|invoice|UNKNOWN|_UNKNOWN|Book\d*)$", re.I)
RE_MONTH_YEAR = re.compile(r"^\s*(\d{1,2})\s*/\s*(\d{2,4})\s*$")
RE_ITEM_ROW = re.compile(r"^\d+(?:\.0+)?$")
RE_SNO_DESC = re.compile(r"^(\d+)\s+(.+)$")


def operator_name(path):
    """The name the OPERATOR gave the export, lifted out of the spool name.

    The spool wraps a capture as <stamp>__<original stem>__<md5-8>.<ext>, and a
    capture relayed through the medical PC's own spool is wrapped TWICE. Strip
    every leading stamp and every trailing md5. A Marg slot name (REPORT_2,
    invoice, report) carries no information and comes back as ""."""
    # index rows carry Windows paths; split on either separator so the same
    # row reads on a Linux mount (the relabel proof runs on one)
    leaf = re.split(r"[\\/]+", path or "")[-1]
    stem = os.path.splitext(leaf)[0]
    changed = True
    while changed:
        changed = False
        s2 = RE_STAMP_PREFIX.sub("", stem)
        s2 = RE_MD5_SUFFIX.sub("", s2)
        if s2 != stem:
            stem, changed = s2, True
    stem = stem.strip()
    if not stem or RE_SLOT_NAME.match(stem):
        return ""
    if re.match(r"^(UNKNOWN|_UNKNOWN|STOCK_|SALE_|PURCHASE_|DOCUMENT_)", stem):
        return ""          # a name this router wrote, not the operator
    return stem


def spool_name_for(archive, digest):
    """A rescued file's index row names its quarantine copy, not the operator's
    file; the operator's name survives in _spool, keyed by the md5 prefix."""
    if not (archive and digest):
        return ""
    d = os.path.join(archive, "_spool")
    try:
        names = os.listdir(d)
    except OSError:
        return ""
    key = "__" + digest[:8].lower()
    for n in names:
        if key in n.lower():
            got = operator_name(n)
            if got:
                return got
    return ""


def category_word(name):
    """(a) The first category word in an operator's file name, canonical form,
    or "". Whole words only: SUPPORTED is not SUPPORT."""
    for w in re.findall(r"[A-Za-z]+", name or ""):
        hit = CATEGORY_WORDS.get(w.upper())
        if hit:
            return hit
    return ""


def stock_items(sh, header, header_row):
    """The set of item names in a STOCK_CLOSING / STOCK_EXPIRY export, in
    either layout: TOTALS (S.No. | Description | ...) or the batch-wise
    DEFAULT (S.No. Description | Batch | Expiry | ...). TOTAL and advert rows
    are never items; a blank description is not an item."""
    out = set()
    if header_row is None:
        return out
    hl = [h.lower() for h in header]
    if hl and hl[0].startswith("s.no. description"):
        for r in range(header_row + 1, sh.nrows):
            m = RE_SNO_DESC.match(cell(sh, r, 0))
            if m:
                out.add(norm(m.group(2)).upper())
    else:
        di = next((i for i, h in enumerate(hl) if h == "description"), 1)
        for r in range(header_row + 1, sh.nrows):
            if not RE_ITEM_ROW.match(cell(sh, r, 0)):
                continue
            d = cell(sh, r, di)
            if d:
                out.add(d.upper())
    return out


def items_digest(items):
    return hashlib.md5("\n".join(sorted(items)).encode("utf-8")).hexdigest()


def expiry_verdict(sh, header, header_row, as_on):
    """(d) EXPIRED / NEAR / MIXED for a STOCK_EXPIRY export, from its own
    Expiry column against the as-on date, or "" when nothing can be read.

    Marg prints expiry as M/YYYY. Its own ALREADY-EXPIRED report of
    03-Jun-2026 carries a 6/2026 row, so an item expiring IN the as-on month
    counts with the expired side when the file is otherwise all-expired, and
    with the near side when the file is otherwise all-future. Returns the
    verdict and (expired, current_month, future) counts."""
    counts = [0, 0, 0]
    if header_row is None or not as_on:
        return "", counts
    hl = [h.lower() for h in header]
    ei = next((i for i, h in enumerate(hl) if h.startswith("expiry")), None)
    if ei is None:
        return "", counts
    try:
        ay, am = int(as_on[:4]), int(as_on[5:7])
    except ValueError:
        return "", counts
    for r in range(header_row + 1, sh.nrows):
        if not RE_SNO_DESC.match(cell(sh, r, 0)) and not RE_ITEM_ROW.match(cell(sh, r, 0)):
            continue
        m = RE_MONTH_YEAR.match(cell(sh, r, ei))
        if not m:
            continue
        mo, yr = int(m.group(1)), int(m.group(2))
        if yr < 100:
            yr += 2000
        key = (yr, mo)
        if key < (ay, am):
            counts[0] += 1
        elif key == (ay, am):
            counts[1] += 1
        else:
            counts[2] += 1
    past, cur, fut = counts
    if past + cur + fut == 0:
        return "", counts
    if fut == 0 and past > 0:
        return "EXPIRED", counts
    if past == 0 and fut > 0:
        return "NEAR", counts
    if past == 0 and fut == 0:
        return "EXPIRED", counts          # only this-month rows: Marg's own rule
    return "MIXED", counts


def _local_path(archive, archived_path):
    """An index row records the Windows path of the archived copy. Resolve it
    inside THIS archive root, so the same row reads on a mirror or a Linux
    mount (the relabel proof runs on one)."""
    if not archived_path:
        return ""
    if os.path.exists(archived_path):
        return archived_path
    parts = re.split(r"[\\/]+", archived_path)
    base = os.path.basename(os.path.normpath(archive)).lower()
    for i, p in enumerate(parts):
        if p.lower() == base and i + 1 < len(parts):
            cand = os.path.join(archive, *parts[i + 1:])
            if os.path.exists(cand):
                return cand
    cand = os.path.join(archive, parts[-3] if len(parts) >= 3 else "", parts[-2] if len(parts) >= 2 else "", parts[-1])
    return cand if os.path.exists(cand) else ""


def _load_cache(archive):
    p = os.path.join(archive, UNIVERSE_CACHE)
    try:
        with open(p, encoding="utf-8") as fh:
            c = json.load(fh)
        if isinstance(c, dict) and c.get("version") == 1:
            c.setdefault("files", {})
            return c
    except (OSError, ValueError):
        pass
    return {"version": 1, "window_days": SUBSET_WINDOW_DAYS, "files": {},
            "reference": None}


def _save_cache(archive, cache):
    p = os.path.join(archive, UNIVERSE_CACHE)
    try:
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=1, sort_keys=True)
        os.replace(tmp, p)
    except OSError:
        pass                      # a cache; losing it costs a re-read, no more


def stock_universe(archive, seen, as_on, exclude_md5, write=True):
    """(b) The reference universe for a closing-stock export dated as_on: the
    LARGEST item set among VERIFIED STOCK_CLOSING exports whose as-on date is
    within SUBSET_WINDOW_DAYS before (or on) as_on, excluding the file being
    judged. Computed from index rows, per-file item counts cached in
    MargArchive/_stock_universe.json (as-on date, count, md5 of the item list)
    so the archive is not re-read every ten minutes. Returns
    {"md5","as_on","count","items","items_md5","path"} or None."""
    if not (archive and as_on and seen):
        return None
    try:
        d_hi = datetime.date.fromisoformat(as_on)
    except ValueError:
        return None
    d_lo = d_hi - datetime.timedelta(days=SUBSET_WINDOW_DAYS)
    cache = _load_cache(archive)
    dirty = False
    cands = []
    for md5, row in seen.items():
        if row.get("type") != "STOCK_CLOSING" or row.get("verdict") != "VERIFIED":
            continue
        if md5 == exclude_md5:
            continue
        try:
            d = datetime.date.fromisoformat((row.get("date_from") or "")[:10])
        except ValueError:
            continue
        if not (d_lo <= d <= d_hi):
            continue
        ent = cache["files"].get(md5)
        if not ent:
            p = _local_path(archive, row.get("archived_path"))
            if not p:
                continue
            try:
                sh = open_sheet(p)
                _t, hdr, hrow = read_preamble(sh)
                its = stock_items(sh, hdr, hrow)
            except Exception:                                  # noqa: BLE001
                continue
            ent = {"as_on": d.isoformat(), "count": len(its),
                   "items_md5": items_digest(its), "path": p}
            cache["files"][md5] = ent
            dirty = True
        cands.append((ent["count"], ent["as_on"], md5, ent))
    if not cands:
        if dirty and write:
            _save_cache(archive, cache)
        return None
    cands.sort(reverse=True)
    count, ref_as_on, ref_md5, ent = cands[0]
    ref = cache.get("reference") or {}
    if not (ref.get("md5") == ref_md5 and ref.get("items_md5") == ent["items_md5"]
            and isinstance(ref.get("items"), list)):
        p = _local_path(archive, (seen.get(ref_md5) or {}).get("archived_path")) or ent.get("path")
        try:
            sh = open_sheet(p)
            _t, hdr, hrow = read_preamble(sh)
            its = stock_items(sh, hdr, hrow)
        except Exception:                                      # noqa: BLE001
            return None
        ref = {"md5": ref_md5, "as_on": ref_as_on, "count": len(its),
               "items": sorted(its), "items_md5": items_digest(its), "path": p}
        cache["reference"] = ref
        dirty = True
    if dirty and write:
        _save_cache(archive, cache)
    return {"md5": ref["md5"], "as_on": ref["as_on"], "count": ref["count"],
            "items": set(ref["items"]), "items_md5": ref["items_md5"],
            "path": ref.get("path", "")}


def stock_variant(path, sh, sig, header, header_row, as_on, digest,
                  archive=None, seen=None, write_cache=True):
    """S224 (F-235). The variant and notes a VERIFIED STOCK_CLOSING or
    STOCK_EXPIRY export gets, in the order S207 s5 recommended:
        (a) a category word in the operator's own file name names it
        (b) else a strict subset <= 60% of the 45-day universe is SUBSET
        (d) STOCK_EXPIRY: EXPIRED / NEAR / MIXED from its own expiry column
    Anything else keeps the signature's variant. Never refuses: file and label.
    Returns (variant, notes)."""
    base = (sig or {}).get("variant", "") or ""
    typ = (sig or {}).get("type", "")
    notes = ["layout=%s" % base] if base else []
    if typ not in STOCK_TYPES:
        return base, ""
    items = stock_items(sh, header, header_row)
    notes.append("items=%d" % len(items))
    named = operator_name(path) or spool_name_for(archive, digest)
    if named:
        notes.append("named=%s" % re.sub(r"[;=]", " ", named)[:60])
    variant = base
    if typ == "STOCK_CLOSING":
        word = category_word(named)
        ref = stock_universe(archive, seen, as_on, digest, write=write_cache)
        subset = False
        if ref and ref["count"] > 0 and items:
            subset = (items < ref["items"]
                      and len(items) <= SUBSET_MAX_FRACTION * ref["count"])
            notes.append("ref=%s:%d" % (ref["as_on"], ref["count"]))
            if items == ref["items"]:
                notes.append("same_items_as_ref=true")
        if word:
            variant = word
        elif subset:
            variant = "SUBSET"
        if subset:
            notes.append("subset=true")
    elif typ == "STOCK_EXPIRY":
        v, (past, cur, fut) = expiry_verdict(sh, header, header_row, as_on)
        notes.append("expiry_past=%d;expiry_thismonth=%d;expiry_future=%d" % (past, cur, fut))
        if v:
            variant = v
    return variant, ";".join(notes)


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
    cols = list(INDEX_COLS)
    if not new:
        # S224: write in the file's OWN schema. If index.csv still carries the
        # 15-column header (marg_rescan / marg_relabel_s224 migrate it), a
        # 16-field row must not be appended under it; the notes fold into
        # reason instead, so the label is never silently dropped.
        try:
            with open(p, newline="", encoding="utf-8") as fh:
                hdr = next(csv.reader(fh), None)
        except (OSError, StopIteration):
            hdr = None
        if hdr and hdr != cols:
            cols = hdr
            extra = {k: row.get(k, "") for k in INDEX_COLS if k not in hdr and row.get(k, "")}
            if extra:
                row = dict(row)
                row["reason"] = " | ".join(x for x in
                    [row.get("reason", "")] + ["%s: %s" % kv for kv in extra.items()] if x)
    with open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in cols})


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


def _archive_and_index(path, res, cfg, digest, verdict, reason, sig,
                       d_from, d_to, title, header, out):
    """Copy the file to its verdict folder and write its index.csv row.

    S203: this was the tail of process(). It is a function now because the
    unreadable-file branch used to `return` ABOVE it -- so a file that could
    not be opened was never archived and never indexed, and since `seen` is
    rebuilt from index.csv every run, it was refused again every ten minutes,
    for ever, with the only message going to a console PULL_HIDDEN.vbs throws
    away. Both paths now archive through THIS, so there is one definition of
    what archiving means and it cannot drift.
    """
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
        # S203 FIX. This used to `return res` here, above the archive-and-index
        # tail -- so an unreadable .xls was NEVER copied to _REFUSED and NEVER
        # written to index.csv. `seen` is rebuilt from index.csv on every run,
        # so the same file was picked up and refused again on the next cycle,
        # and the next, silently. It now takes the same archive path as every
        # other verdict: a copy in _REFUSED, a .txt saying why, and a row.
        _why = "not a readable .xls (%s)" % ex
        res.update(type="", variant="", verdict="REFUSED", reason=_why, rows=0)
        return _archive_and_index(path, res, cfg, digest, "REFUSED", _why,
                                  None, None, None, "", [], out)
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
        if verdict == "VERIFIED" and sig["type"] in STOCK_TYPES:
            # S224 (F-235): a filtered stock export or an EXPIRED-vs-NEAR
            # expiry report gets its own variant; the type never changes.
            res["variant"], res["notes"] = stock_variant(
                path, sh, sig, header, hrow, d_from, digest,
                cfg.get("archive"), seen, write_cache=not cfg.get("dry"))
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
    return _archive_and_index(path, res, cfg, digest, verdict, reason,
                              sig, d_from, d_to, title, header, out)


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
    # S203: an unreadable .xls must be ARCHIVED and INDEXED, not silently
    # re-refused every cycle. Proven end to end against a real archive tree.
    _d2 = _tf.mkdtemp()
    _bad = os.path.join(_d2, "broken.xls")
    with open(_bad, "wb") as _fh:
        _fh.write(b"this is not a spreadsheet at all")
    _arch = os.path.join(_d2, "arch")
    _cfg2 = {"archive": _arch, "outbox": os.path.join(_arch, "_outbox"),
             "dry": False, "index": os.path.join(_arch, "index.csv")}
    _seen2 = {}
    _r = process(_bad, sigs, _cfg2, _seen2, lambda *_a, **_k: None)
    ck("unreadable .xls returns a result", bool(_r))
    ck("unreadable .xls verdict is REFUSED", (_r or {}).get("verdict") == "REFUSED")
    _dest = (_r or {}).get("archived_path") or ""
    ck("unreadable .xls is COPIED to _REFUSED",
       bool(_dest) and os.path.exists(_dest) and "_REFUSED" in _dest)
    ck("unreadable .xls gets a .txt saying why",
       bool(_dest) and os.path.exists(os.path.splitext(_dest)[0] + ".txt"))
    ck("unreadable .xls gets an index.csv row", os.path.exists(_cfg2["index"]))
    _seen3 = load_index(_cfg2["index"])
    ck("and that row makes it SEEN on the next run -- the loop is closed",
       (_r or {}).get("md5") in _seen3)
    _r2 = process(_bad, sigs, _cfg2, _seen3, lambda *_a, **_k: None)
    ck("a second pass skips it instead of re-refusing it", _r2 is None)

    ck("registry is data-driven (>=1 signature loaded)", len(sigs) >= 1)

    # S224 (F-235): variant naming for filtered stock / expired-vs-near expiry
    ck("operator name lifted from a spool name",
       operator_name("20260828-074003__ORTHOTICS STOCK 27 AUGUST__67d0fcf7.xlsx")
       == "ORTHOTICS STOCK 27 AUGUST")
    ck("double-wrapped spool name unwrapped",
       operator_name("20260902-173044__20260902-172308__WHOLE STORES CLOSING STOCK AS ON 02-09-2026__708b0f28__708b0f28.XLS")
       == "WHOLE STORES CLOSING STOCK AS ON 02-09-2026")
    ck("a Windows path splits to its leaf",
       operator_name(r"D:\\MargArchive\_spool\20260828-074003__ORTHOTICS STOCK 27 AUGUST__67d0fcf7.xlsx")
       == "ORTHOTICS STOCK 27 AUGUST")
    ck("a name this router wrote is not an operator name",
       operator_name(r"D:\\MargArchive\_REFUSED\UNKNOWN__2024-10-05__20241005-123849__f9a4055a.XLS") == "")
    ck("a Marg slot name is not an operator name",
       operator_name("20260904-031020__20260904-030844__REPORT_2__41ecfbd8__41ecfbd8.XLS") == "")
    ck("category word: ORTHOTICS", category_word("ORTHOTICS STOCK 27 AUGUST") == "ORTHOTICS")
    ck("category word: ORTHOTIC -> ORTHOTICS", category_word("SANJEEVNI ORTHOTIC STOCK") == "ORTHOTICS")
    ck("WHOLE is not a category", category_word("WHOLE STORES CLOSING STOCK AS ON 02-09-2026") == "")
    ck("SUPPORTED is not SUPPORT", category_word("SUPPORTED LIST") == "")

    class _Sh(object):
        def __init__(self, rows):
            self.rows = rows; self.nrows = len(rows); self.ncols = max(len(r) for r in rows)
        def cell_value(self, r, c):
            return self.rows[r][c] if c < len(self.rows[r]) else ""
    _tot = _Sh([["SHOP CLOSING STOCK AS ON 27-08-2026"], ["S.No.", "Description", "Total Stock", "Unit"],
                ["1.0", "A", "1", "PCS"], ["2.0", "B", "2", "PCS"], ["3.0", "", "-", "PCS"],
                ["TOTAL", "", "3", ""], ["advert"]])
    ck("items from the TOTALS layout (blank name skipped, TOTAL skipped)",
       stock_items(_tot, ["S.No.", "Description", "Total Stock", "Unit"], 1) == {"A", "B"})
    _bat = _Sh([["EXP. BEFORE *BA., 0"], ["S.No. Description", "Batch", "Expiry", "Stock Unit"],
                ["1 ASTOFEN R 1*10", "B1", "10/2026", "1"], ["", "", "", ""],
                ["2 VOM L 1*10", "B2", "11/2026", "1"], ["TOTAL", "", "", "2"]])
    ck("items from the batch-wise layout",
       stock_items(_bat, ["S.No. Description", "Batch", "Expiry", "Stock Unit"], 1)
       == {"ASTOFEN R 1*10", "VOM L 1*10"})
    _hdr = ["S.No. Description", "Batch", "Expiry", "Stock Unit"]
    ck("expiry all future -> NEAR", expiry_verdict(_bat, _hdr, 1, "2026-08-28")[0] == "NEAR")
    ck("expiry all past -> EXPIRED", expiry_verdict(_bat, _hdr, 1, "2027-01-05")[0] == "EXPIRED")
    _mix = _Sh([["t"], _hdr, ["1 X", "B", "9/2026", "1"], ["2 Y", "B", "11/2026", "1"], ["TOTAL"]])
    ck("expiry mixed -> MIXED", expiry_verdict(_mix, _hdr, 1, "2026-10-15")[0] == "MIXED")
    ck("a this-month row among all-future rows is still NEAR",
       expiry_verdict(_bat, _hdr, 1, "2026-10-15")[0] == "NEAR")
    _one = _Sh([["t"], _hdr, ["1 X", "B", "6/2026", "1"], ["2 Y", "B", "1/2026", "1"], ["TOTAL"]])
    ck("expiry in the as-on month counts with the expired side (Marg's own 03-Jun-2026 report)",
       expiry_verdict(_one, _hdr, 1, "2026-06-03")[0] == "EXPIRED")
    ck("a sheet with no expiry column gives no verdict",
       expiry_verdict(_tot, ["S.No.", "Description", "Total Stock", "Unit"], 1, "2026-08-28")[0] == "")

    # the subset rule end to end, in a scratch archive
    _d3 = _tf.mkdtemp()
    _arch3 = os.path.join(_d3, "MargArchive")
    os.makedirs(os.path.join(_arch3, "STOCK_CLOSING", "2026-08"))
    _sigc = {"type": "STOCK_CLOSING", "variant": "TOTALS"}
    _seen3 = {}
    def _mk(name, items, as_on, md5):
        rows = [["SHOP CLOSING STOCK AS ON x"], ["S.No.", "Description", "Total Stock", "Unit"]]
        rows += [[str(i + 1) + ".0", it, "1", "PCS"] for i, it in enumerate(items)]
        rows += [["TOTAL", "", "1", ""]]
        _seen3[md5] = {"type": "STOCK_CLOSING", "verdict": "VERIFIED", "date_from": as_on,
                       "archived_path": os.path.join(_arch3, "STOCK_CLOSING", "2026-08", name)}
        return _Sh(rows)
    # the universe cannot be opened from a fake sheet, so seed the cache directly
    _full = ["ITEM%03d" % i for i in range(100)]
    _cache = {"version": 1, "window_days": SUBSET_WINDOW_DAYS,
              "files": {"f" * 32: {"as_on": "2026-08-27", "count": 100,
                                    "items_md5": items_digest(_full), "path": ""}},
              "reference": {"md5": "f" * 32, "as_on": "2026-08-27", "count": 100,
                            "items": sorted(_full), "items_md5": items_digest(_full), "path": ""}}
    _save_cache(_arch3, _cache)
    _seen3["f" * 32] = {"type": "STOCK_CLOSING", "verdict": "VERIFIED", "date_from": "2026-08-27",
                        "archived_path": ""}
    _sub = _mk("sub.xls", _full[:50], "2026-08-27", "a" * 32)
    _v, _n = stock_variant("20260828-074003__REPORT_2__aaaaaaaa.xls", _sub, _sigc,
                           ["S.No.", "Description", "Total Stock", "Unit"], 1,
                           "2026-08-27", "a" * 32, _arch3, _seen3)
    ck("a strict subset at 50% of the universe is SUBSET", _v == "SUBSET" and "subset=true" in _n)
    _v, _n = stock_variant("20260828-074003__ORTHOTICS STOCK 27 AUGUST__aaaaaaaa.xlsx", _sub, _sigc,
                           ["S.No.", "Description", "Total Stock", "Unit"], 1,
                           "2026-08-27", "a" * 32, _arch3, _seen3)
    ck("the operator's word wins over SUBSET", _v == "ORTHOTICS" and "subset=true" in _n)
    _big = _mk("big.xls", _full[:70], "2026-08-27", "b" * 32)
    _v, _n = stock_variant("x__REPORT_2__bbbbbbbb.xls", _big, _sigc,
                           ["S.No.", "Description", "Total Stock", "Unit"], 1,
                           "2026-08-27", "b" * 32, _arch3, _seen3)
    ck("a strict subset at 70% is a shrinking shop, NOT a subset", _v == "TOTALS" and "subset" not in _n)
    _same = _mk("same.xls", _full, "2026-08-27", "c" * 32)
    _v, _n = stock_variant("x__REPORT_2__cccccccc.xls", _same, _sigc,
                           ["S.No.", "Description", "Total Stock", "Unit"], 1,
                           "2026-08-27", "c" * 32, _arch3, _seen3)
    ck("an equal-sized duplicate is TOTALS with same_items_as_ref", _v == "TOTALS" and "same_items_as_ref=true" in _n)
    _v, _n = stock_variant("x__REPORT_2__cccccccc.xls", _same, _sigc,
                           ["S.No.", "Description", "Total Stock", "Unit"], 1,
                           "2026-11-30", "c" * 32, _arch3, _seen3)
    ck("no universe inside 45 days -> the signature's variant, never a refusal", _v == "TOTALS")
    ck("a non-stock type is untouched",
       stock_variant("x.xls", _tot, {"type": "SALE_BILLWISE", "variant": "DETAIL"},
                     [], 1, "2026-08-28", "d" * 32, _arch3, _seen3) == ("DETAIL", ""))
    ck("canonical name carries the variant",
       canonical_name("STOCK_EXPIRY", "EXPIRED", "2026-08-28", "2026-08-28", "s", "h" * 8)
       .startswith("STOCK_EXPIRY_EXPIRED__2026-08-28__"))
    # append_index under an OLD 15-column header must not misalign the file
    _idx = os.path.join(_d3, "index.csv")
    with open(_idx, "w", newline="", encoding="utf-8") as _fh:
        _fh.write(",".join(INDEX_COLS[:-1]) + "\r\n")
    append_index(_idx, {"md5": "e" * 32, "reason": "structural", "notes": "subset=true"})
    with open(_idx, newline="", encoding="utf-8") as _fh:
        _rows = list(csv.reader(_fh))
    ck("old-schema index keeps its width", len(_rows) == 2 and len(_rows[1]) == len(INDEX_COLS) - 1)
    ck("...and the notes fold into reason rather than vanish", "subset=true" in _rows[1][INDEX_COLS.index("reason")])
    shutil.rmtree(_d3, ignore_errors=True)

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
