#!/root/wa/venv/bin/python3
# =============================================================================
#  payments_register.py  ·  Session 234  ·  S234_PAYMENT_REGISTER  ·  v1
#
#  THE SHEET IS THE ORIGINAL. THIS TABLE IS A READ OF IT, NEVER A SECOND AUTHOR.
#
#  WHY THIS EXISTS
#  ---------------
#  The owner wants a payments product on the box, and the payment history it
#  needs already exists — in a Google sheet that a script in his PERSONAL
#  account creates and appends to every day. `registerSheet_()` inside the
#  Inbox Janitor CREATES that sheet on first run, remembers its id in a Script
#  Property, and appends one row per captured payment email. Nothing else
#  writes it, and it has been appended to since long before this table existed.
#
#  So the sheet has a live writer, and it is not this box.
#
#  PERSONAL_GOOGLE_PLANE_v1_S233 states the consequence in one line: a VPS
#  table must treat that sheet as an UPSTREAM SOURCE and never as shared
#  state, or the two diverge in silence and nothing says so. This file obeys
#  that literally:
#
#    * it has NO Google credential, NO network call and NO Sheets API import;
#    * it reads ONE directory of CSVs that S233's `sheets_pull.py` already
#      writes at 01:45 nightly, and it reads nothing else;
#    * it never writes back to Google by any route, and cannot;
#    * the table it fills is DERIVED — droppable and rebuildable from the CSV
#      at any time, with no fact living only here.
#
#  Data flow, one way, no loop:
#
#      Gmail --> Inbox Janitor (personal GAS) --> Payment Register sheet
#            --> sheets_pull.py 01:45 --> /root/state_backup/sheets/... CSV
#            --> THIS SCRIPT 02:05 --> finance.db table `payment_register`
#
#  WHAT A ROW IS, AND WHY row_no IS THE KEY
#  ----------------------------------------
#  The sheet has six columns and NO id column:
#
#      Date | Vendor | Description | Amount (Rs) | Attachment in Drive | Gmail Link
#
#  There is nothing in a row that is reliably unique — two identical renewals
#  of the same amount to the same vendor on the same day are a real thing, and
#  a content hash would silently collapse them into one. The sheet is
#  APPEND-ONLY, so a row's POSITION is stable and is the only honest key.
#  `row_no` is therefore the sheet's own 1-based row number: row 1 is the
#  header, so the first payment is row_no = 2.
#
#  That choice has a cost and the cost is handled: if a human ever inserts or
#  deletes a row in the middle of the sheet, every row below it shifts and this
#  table would quietly re-label them. That is exactly what the drift log and
#  the shrink refusal below are for — a shift shows up as a wall of changed
#  rows, loudly, instead of as nothing.
#
#  REFUSAL STANCES — a bad read must never damage a good table
#  -----------------------------------------------------------
#  Each failure class has its OWN exit code and its OWN words, because one
#  message for every failure is a message that lies (S233, rule 4):
#
#    EXIT 10  the source directory or CSV is not there            -> table untouched
#    EXIT 11  the header is not the six columns this code knows   -> table untouched
#    EXIT 12  the database cannot be opened or the schema fails   -> nothing written
#    EXIT 42  the sheet has FEWER data rows than the table holds  -> nothing written
#    EXIT 43  the pulled CSV is older than STALE_HOURS            -> nothing written
#    EXIT 44  too many date cells no longer read as d-m-y         -> nothing written
#
#  THE DATE COLUMN, AND WHY IT IS READ DAY-FIRST — measured, not assumed
#  ---------------------------------------------------------------------
#  This was measured on 08-Sep-2026 against the owner's own export of the live
#  sheet, 250 data rows, and it is the single thing most able to make this
#  table quietly wrong, so it is written down in full.
#
#  The Janitor appends the date as TEXT, day-first, always:
#
#      Utilities.formatDate(m.getDate(), Session.getScriptTimeZone(),
#                           'dd-MM-yyyy')
#
#  That is read from the project's own exported source, not recalled. But the
#  sheet does not keep all 250 as text. Of the 250 rows:
#
#      155 are still TEXT           — every one of them has a day above 12
#       95 are REAL DATE CELLS      — every one of them has a day of 12 or less
#
#  155 out of 155 and 95 out of 95 is not a coincidence, and the explanation is
#  the whole point: the spreadsheet parses an appended string as a date when it
#  CAN, reading it MONTH-FIRST. "19-07-2026" has no 19th month, so it stays
#  text. "09-07-2026" is accepted — as the 7th of September, when the Janitor
#  meant the 9th of July. The sheet has silently re-dated 95 of its own rows.
#
#  The rescue is that those cells are FORMATTED mm-dd-yyyy, so what the sheet
#  DISPLAYS is character-for-character the string the Janitor wrote. The pull
#  takes displayed values (`get_all_values`), so the CSV under this script
#  carries the original text for all 250 rows, and reading every row DAY-FIRST
#  recovers the Janitor's intent for every one of them. Read month-first, 91 of
#  250 rows would be wrong by up to two months, in silence.
#
#  So: DAY-FIRST, uniformly, and no clever per-row guessing. The heuristics
#  that suggest themselves were tested and both are dead: no row anywhere in
#  the file proves month-first, so a whole-file order detector would learn
#  nothing; and the sheet is not chronological — 129 inversions in 249
#  consecutive pairs — so a neighbour-fits-between rule has nothing to stand on.
#
#  THE TRIPWIRE. All of this rests on those 95 cells continuing to be displayed
#  mm-dd-yyyy. If anyone re-formats that column in Google — to "7 Sep 2026", or
#  to yyyy-mm-dd — the round-trip breaks and the strings stop reading day-first.
#  That does not fail quietly here: a month-first string like "07-19-2026" has
#  no 19th month, so it does not parse at all, and EXIT 44 stops the run once
#  more than DATE_SHAPE_MAX_PCT of dated rows stop parsing. The guard is not
#  cosmetic — it is the only thing standing between a re-format in a browser
#  and a table of wrong dates.
#
#  ⚠ SEPARATELY, AND FOR THE OWNER, NOT FOR THIS CODE: the 95 coerced cells are
#  stored in Google with the day and month swapped. Nothing downstream of the
#  displayed text is affected, but sorting that sheet by date inside Google, or
#  reading it with unformatted values, would give the swapped dates. Recorded
#  as a finding at S234; the fix is upstream, in a project under a read-only
#  hold, and is not taken here.
#
#  EXIT 42 is the important one. The sheet is append-only, so it can only ever
#  grow. Fewer rows than last time means the pull caught a broken export, or
#  someone deleted rows in the sheet, or the wrong book was pulled. In every
#  one of those cases the right answer is to keep what we have and say so.
#  `--allow-shrink` exists for the day the owner deliberately prunes the sheet,
#  and it must be typed on purpose; it is never a default and never automatic.
#
#  A CHANGED ROW IS NOT A REFUSAL. The Janitor can legitimately correct a row
#  (a vendor name map fixed, an amount re-parsed). A row whose content changed
#  is written AND recorded in `payment_register_drift`, field by field, with
#  the old and new values. Nothing is overwritten in silence.
#
#  MONEY IS INTEGER PAISE. Never a float. `amount_raw` keeps the sheet's own
#  characters exactly as they were so the parse can always be re-argued from
#  the original, and `amount_paise` is NULL when the cell is blank or does not
#  parse — of the 250 data rows on 08-Sep-2026, 72 had no amount at all, so a
#  blank is ordinary and must not be a zero. A zero would sum.
#
#  Modes:
#    ingest     read the CSV, refuse or write, print what changed.
#    status     what the table holds and how old the pull behind it is.
#               Read-only: opens the database read-only and takes no lock.
#    selftest   every rule above, against fixtures built in a temp directory.
#               Touches no live path. Exits non-zero on the first failure.
#
#  Nothing here needs a package. Standard library only, so it runs under any
#  python on the box and cannot be broken by a dependency change.
# =============================================================================

import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

APP_ROOT = os.environ.get("FINANCE_ROOT", "/root/finance")
DB_PATH = os.environ.get("FINANCE_DB", os.path.join(APP_ROOT, "finance.db"))
SHEETS_DIR = os.environ.get("FINANCE_SHEETS_DIR",
                            "/root/state_backup/sheets")
BOOK_LABEL = os.environ.get("FINANCE_PAYMENTS_BOOK", "payment_register")
BOOK_META = "_BOOK.json"

# The pull runs at 01:45 and this runs at 02:05. A CSV older than this means
# the pull did not run or refused, and ingesting it would quietly re-assert
# stale data as if it were today's. 30 hours forgives one missed night's
# lateness without forgiving a dead feed.
STALE_HOURS = float(os.environ.get("FINANCE_PAYMENTS_STALE_HOURS", "30"))

EXIT_OK = 0
EXIT_NO_SOURCE = 10
EXIT_BAD_HEADER = 11
EXIT_DB = 12
EXIT_SHRANK = 42
EXIT_STALE = 43
EXIT_DATE_SHAPE = 44

# A few unreadable dates are ordinary — a row someone typed by hand, a blank
# the Janitor could not fill. A LOT of them means the column's display format
# changed in Google and the day-first round-trip described above has broken,
# which is the one failure that would fill this table with wrong dates. On
# 08-Sep-2026 the live sheet parsed 250 of 250, so any figure near this limit
# is already abnormal.
DATE_SHAPE_MAX_PCT = float(os.environ.get("FINANCE_PAYMENTS_DATE_MAX_PCT", "5"))

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# The header this code was written against, read from the live export on
# 08-Sep-2026. Compared case-insensitively and whitespace-insensitively, but
# compared: a sheet that grew a column must stop this script, not be guessed at.
EXPECTED_HEADER = ["date", "vendor", "description", "amount (rs)",
                   "attachment in drive", "gmail link"]

FIELDS = ("date_raw", "date_iso", "vendor", "description",
          "amount_raw", "amount_paise", "in_drive", "gmail_link")


def stamp():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def die(code, msg):
    sys.stderr.write("REFUSED (%d): %s\n" % (code, msg))
    sys.stderr.flush()
    sys.exit(code)


# ---------------------------------------------------------------- parsing ----
def parse_date(raw):
    """The sheet's date cell as an ISO date, or None. The raw text is always
    kept whatever this returns, so a date this cannot read is never lost —
    it is just not sortable until someone looks at it.

    Google renders the same column in more than one way depending on how the
    cell was written, so all three shapes seen in the export are accepted.
    DD-MM-YYYY is the clinic's own convention and is tried FIRST: 03-04-2026
    is the third of April, never the fourth of March."""
    s = (raw or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime.date(y, mo, d).isoformat()
        except ValueError:
            return None
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime.date(y, mo, d).isoformat()
        except ValueError:
            return None
    return None


def parse_amount(raw):
    """Rupees as INTEGER PAISE, or None when the cell is blank or unreadable.

    None is not zero and must never become zero: a blank amount is a row the
    Janitor could not find a figure in, and 72 of the 250 rows on 08-Sep-2026
    were exactly that. A zero would be added up; a NULL cannot be."""
    s = (raw or "").strip()
    if not s:
        return None
    s = s.replace("₹", "").replace("Rs.", "").replace("Rs", "")
    s = s.replace(",", "").replace(" ", "").replace(" ", "")
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    if not re.match(r"^-?\d+(\.\d+)?$", s):
        return None
    whole, _, frac = s.partition(".")
    frac = (frac + "00")[:2]
    sign = -1 if whole.startswith("-") or neg else 1
    whole = whole.lstrip("-")
    try:
        paise = sign * (int(whole) * 100 + int(frac))
    except ValueError:
        return None
    return paise


def parse_flag(raw):
    """'Yes'/'No' as 1/0, anything else as None. The column says whether the
    Janitor saved a PDF of the payment to Drive; an unrecognised word is
    honestly unknown rather than quietly false."""
    s = (raw or "").strip().lower()
    if s in ("yes", "y", "true", "1"):
        return 1
    if s in ("no", "n", "false", "0"):
        return 0
    return None


def row_md5(vals):
    h = hashlib.md5()
    for v in vals:
        h.update(("" if v is None else str(v)).encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()


# ----------------------------------------------------------------- source ----
def book_dir():
    return os.path.join(SHEETS_DIR, BOOK_LABEL)


def read_book_meta(d):
    """The _BOOK.json sheets_pull.py writes beside the CSVs. It carries the
    tab list and the IST time of the pull, which is how this script knows
    whether the data under it is today's or a corpse."""
    p = os.path.join(d, BOOK_META)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            m = json.load(fh)
        return m if isinstance(m, dict) else None
    except (ValueError, OSError):
        return None


def pick_csv(d, meta):
    """The one CSV to read. The book has a single tab, but the tab could be
    renamed in Google tomorrow, so the tab is taken from _BOOK.json when it is
    there and only guessed from the directory when it is not."""
    if meta and isinstance(meta.get("tabs"), list) and meta["tabs"]:
        fname = meta["tabs"][0].get("file")
        if fname and os.path.exists(os.path.join(d, fname)):
            return os.path.join(d, fname)
    cands = sorted(f for f in os.listdir(d) if f.lower().endswith(".csv"))
    if len(cands) == 1:
        return os.path.join(d, cands[0])
    return None


def pull_age_hours(meta, path):
    """Hours since the pull that produced this CSV. Prefers the pull's own
    recorded IST stamp; falls back to the file's mtime, which is a weaker
    claim but still a real one."""
    s = (meta or {}).get("pulled_at_ist")
    if s:
        try:
            t = datetime.datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
            t = t.replace(tzinfo=IST)
            return (datetime.datetime.now(IST) - t).total_seconds() / 3600.0
        except ValueError:
            pass
    try:
        mt = datetime.datetime.fromtimestamp(os.path.getmtime(path), IST)
        return (datetime.datetime.now(IST) - mt).total_seconds() / 3600.0
    except OSError:
        return None


def read_rows(path):
    """The CSV as (header, [(row_no, cells)]). row_no is the sheet's own
    1-based row number, so the first data row is 2 and stays 2 forever.

    A row that is entirely blank is skipped but STILL CONSUMES ITS NUMBER —
    dropping it silently would shift every row beneath it and re-label real
    payments, which is the one thing row_no exists to prevent."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return [], []
    header = [(c or "").strip() for c in rows[0]]
    out = []
    for i, cells in enumerate(rows[1:], start=2):
        if not any((c or "").strip() for c in cells):
            continue
        out.append((i, cells))
    return header, out


def header_ok(header):
    got = [(c or "").strip().lower() for c in header[:len(EXPECTED_HEADER)]]
    return got == EXPECTED_HEADER and len(header) == len(EXPECTED_HEADER)


# --------------------------------------------------------------- database ----
SCHEMA = """
CREATE TABLE IF NOT EXISTS payment_register (
  row_no       INTEGER PRIMARY KEY,
  date_raw     TEXT    NOT NULL DEFAULT '',
  date_iso     TEXT,
  vendor       TEXT    NOT NULL DEFAULT '',
  description  TEXT    NOT NULL DEFAULT '',
  amount_raw   TEXT    NOT NULL DEFAULT '',
  amount_paise INTEGER,
  in_drive     INTEGER,
  gmail_link   TEXT    NOT NULL DEFAULT '',
  content_md5  TEXT    NOT NULL,
  first_seen   TEXT    NOT NULL,
  last_seen    TEXT    NOT NULL,
  revised_at   TEXT,
  revisions    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_payment_register_date
  ON payment_register(date_iso);
CREATE INDEX IF NOT EXISTS ix_payment_register_vendor
  ON payment_register(vendor);
CREATE TABLE IF NOT EXISTS payment_register_meta (
  k TEXT PRIMARY KEY,
  v TEXT
);
-- ONE PAYMENT CAN BE THREE ROWS, AND THE PRODUCT MUST KNOW IT.
-- The Janitor makes a row per captured EMAIL, not per payment, and a single
-- renewal routinely sends three: the reminder, the invoice, and the receipt.
-- Measured on the live sheet 08-Sep-2026: 178 rows carry an amount and sum to
-- Rs 16,87,268.75, but five vendor/date/amount groups hold ten of those rows,
-- so Rs 4,29,411.39 of that total — a quarter of it — is the same money
-- counted twice.
--
-- The TABLE is not de-duplicated: it mirrors the sheet row for row, because a
-- table that quietly drops rows can never be reconciled against its source.
-- The judgement lives here instead, in a view, where it is visible and can be
-- argued with. `counts_once` is 1 on the FIRST row of each group and 0 on its
-- copies, so a total is `SUM(amount_paise) WHERE counts_once=1` and a full
-- listing is still every row.
CREATE VIEW IF NOT EXISTS payment_register_v AS
SELECT p.*,
       (SELECT COUNT(*) FROM payment_register q
         WHERE q.vendor = p.vendor
           AND q.date_iso IS NOT NULL AND q.date_iso = p.date_iso
           AND q.amount_paise IS NOT NULL
           AND q.amount_paise = p.amount_paise)          AS same_day_copies,
       CASE WHEN p.amount_paise IS NULL THEN 0
            WHEN p.row_no = (SELECT MIN(q.row_no) FROM payment_register q
                              WHERE q.vendor = p.vendor
                                AND q.date_iso IS NOT NULL
                                AND q.date_iso = p.date_iso
                                AND q.amount_paise IS NOT NULL
                                AND q.amount_paise = p.amount_paise)
              THEN 1 ELSE 0 END                          AS counts_once
FROM payment_register p;
CREATE TABLE IF NOT EXISTS payment_register_drift (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  at      TEXT    NOT NULL,
  row_no  INTEGER NOT NULL,
  field   TEXT    NOT NULL,
  was     TEXT,
  now     TEXT
);
"""


def open_db(path, readonly=False):
    if readonly:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    else:
        con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def ensure_schema(con):
    con.executescript(SCHEMA)
    con.commit()


def meta_set(con, k, v):
    con.execute("INSERT INTO payment_register_meta(k,v) VALUES(?,?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, str(v)))


def meta_get(con, k):
    r = con.execute("SELECT v FROM payment_register_meta WHERE k=?",
                    (k,)).fetchone()
    return r["v"] if r else None


# ----------------------------------------------------------------- ingest ----
def build_record(cells):
    def cell(i):
        return (cells[i] if i < len(cells) else "") or ""
    date_raw = cell(0).strip()
    vendor = cell(1).strip()
    description = cell(2).strip()
    amount_raw = cell(3).strip()
    in_drive_raw = cell(4)
    gmail_link = cell(5).strip()
    return {
        "date_raw": date_raw,
        "date_iso": parse_date(date_raw),
        "vendor": vendor,
        "description": description,
        "amount_raw": amount_raw,
        "amount_paise": parse_amount(amount_raw),
        "in_drive": parse_flag(in_drive_raw),
        "gmail_link": gmail_link,
    }


def ingest(allow_shrink=False, ignore_stale=False, db_path=None,
           sheets_dir=None, quiet=False):
    """Read the CSV, refuse or write. Returns a summary dict.

    Every refusal happens BEFORE the first write, so a refused run leaves the
    table exactly as the last good run left it."""
    d = os.path.join(sheets_dir or SHEETS_DIR, BOOK_LABEL)
    dbp = db_path or DB_PATH
    if not os.path.isdir(d):
        die(EXIT_NO_SOURCE,
            "no pulled copy of the payment register at %s . This table is fed "
            "by sheets_pull.py; if that job has never run for this book, run "
            "it first. Nothing was written." % d)
    meta = read_book_meta(d)
    path = pick_csv(d, meta)
    if not path:
        die(EXIT_NO_SOURCE,
            "%s exists but holds no single CSV this script can identify. "
            "Nothing was written." % d)
    age = pull_age_hours(meta, path)
    if age is not None and age > STALE_HOURS and not ignore_stale:
        die(EXIT_STALE,
            "the pulled copy is %.1f hours old (limit %.0f). The nightly pull "
            "has not refreshed it, so ingesting it would re-assert stale rows "
            "as today's. Fix the pull, or pass --ignore-stale on purpose. "
            "Nothing was written." % (age, STALE_HOURS))
    header, rows = read_rows(path)
    if not header_ok(header):
        die(EXIT_BAD_HEADER,
            "the sheet's header is not the six columns this code knows.\n"
            "  expected: %s\n  found:    %s\n"
            "A column was added, removed or renamed in Google. Nothing was "
            "written; the table still holds the last good read."
            % (EXPECTED_HEADER, [c.strip().lower() for c in header]))
    # Every record is built BEFORE the database is opened, so the date-shape
    # guard can refuse the whole file without a single write having happened.
    built = [(row_no, build_record(cells)) for row_no, cells in rows]
    dated = [r for _, r in built if r["date_raw"]]
    unread = [r for r in dated if r["date_iso"] is None]
    pct = (100.0 * len(unread) / len(dated)) if dated else 0.0
    if dated and pct > DATE_SHAPE_MAX_PCT:
        die(EXIT_DATE_SHAPE,
            "%d of %d dated rows (%.1f%%) no longer read as day-month-year. "
            "The date column's display format has almost certainly been "
            "changed in Google, which breaks the day-first round-trip this "
            "table depends on. Examples: %s. Nothing was written; the table "
            "still holds the last good read."
            % (len(unread), len(dated), pct,
               ", ".join(repr(r["date_raw"]) for r in unread[:4])))
    try:
        con = open_db(dbp)
        ensure_schema(con)
    except sqlite3.Error as ex:
        die(EXIT_DB, "the database at %s could not be opened or prepared "
                     "(%s). Nothing was written." % (dbp, ex))

    have = {r["row_no"]: r for r in
            con.execute("SELECT * FROM payment_register").fetchall()}
    if len(rows) < len(have) and not allow_shrink:
        con.close()
        die(EXIT_SHRANK,
            "the sheet now has %d data rows and this table holds %d. The "
            "Payment Register is append-only, so it cannot shrink on its own: "
            "either the pull caught a broken export, or rows were deleted in "
            "Google. Nothing was written and the table is untouched. If the "
            "shrink is deliberate, re-run with --allow-shrink."
            % (len(rows), len(have)))

    now = stamp()
    added = changed = unchanged = 0
    drift = []
    for row_no, rec in built:
        h = row_md5([rec[f] for f in FIELDS])
        old = have.get(row_no)
        if old is None:
            con.execute(
                "INSERT INTO payment_register(row_no,date_raw,date_iso,vendor,"
                "description,amount_raw,amount_paise,in_drive,gmail_link,"
                "content_md5,first_seen,last_seen) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (row_no, rec["date_raw"], rec["date_iso"], rec["vendor"],
                 rec["description"], rec["amount_raw"], rec["amount_paise"],
                 rec["in_drive"], rec["gmail_link"], h, now, now))
            added += 1
        elif old["content_md5"] != h:
            for f in FIELDS:
                if str(old[f]) != str(rec[f]):
                    drift.append((row_no, f, old[f], rec[f]))
                    con.execute(
                        "INSERT INTO payment_register_drift(at,row_no,field,"
                        "was,now) VALUES(?,?,?,?,?)",
                        (now, row_no, f,
                         None if old[f] is None else str(old[f]),
                         None if rec[f] is None else str(rec[f])))
            con.execute(
                "UPDATE payment_register SET date_raw=?,date_iso=?,vendor=?,"
                "description=?,amount_raw=?,amount_paise=?,in_drive=?,"
                "gmail_link=?,content_md5=?,last_seen=?,revised_at=?,"
                "revisions=revisions+1 WHERE row_no=?",
                (rec["date_raw"], rec["date_iso"], rec["vendor"],
                 rec["description"], rec["amount_raw"], rec["amount_paise"],
                 rec["in_drive"], rec["gmail_link"], h, now, now, row_no))
            changed += 1
        else:
            con.execute("UPDATE payment_register SET last_seen=? WHERE row_no=?",
                        (now, row_no))
            unchanged += 1

    gone = sorted(set(have) - {r for r, _ in rows})
    total = con.execute("SELECT COUNT(*) c FROM payment_register").fetchone()["c"]
    meta_set(con, "last_ingest_at", now)
    meta_set(con, "source_csv", path)
    meta_set(con, "source_pulled_at_ist", (meta or {}).get("pulled_at_ist", ""))
    meta_set(con, "source_rows", len(rows))
    meta_set(con, "table_rows", total)
    con.commit()
    con.close()

    summary = {"added": added, "changed": changed, "unchanged": unchanged,
               "gone": gone, "total": total, "source_rows": len(rows),
               "csv": path, "pull_age_hours": age, "drift": drift,
               "dated": len(dated), "undated": len(unread)}
    if not quiet:
        log("payment_register ingest %s" % now)
        log("  source      %s" % path)
        log("  pulled      %s (%s)"
            % ((meta or {}).get("pulled_at_ist", "unknown"),
               "age unknown" if age is None else "%.1f h ago" % age))
        log("  rows        %d in the sheet, %d in the table"
            % (len(rows), total))
        log("  added %d  ·  changed %d  ·  unchanged %d"
            % (added, changed, unchanged))
        log("  dates       %d of %d dated rows read day-first; %d unreadable"
            % (len(dated) - len(unread), len(dated), len(unread)))
        for row_no, f, was, new in drift[:20]:
            log("  DRIFT row %d  %s: %r -> %r" % (row_no, f, was, new))
        if len(drift) > 20:
            log("  DRIFT ... and %d more, all recorded in "
                "payment_register_drift" % (len(drift) - 20))
        if gone:
            log("  NOTE %d row numbers are in the table and not in the sheet: "
                "%s" % (len(gone), gone[:20]))
    return summary


# ----------------------------------------------------------------- status ----
def status(db_path=None):
    dbp = db_path or DB_PATH
    if not os.path.exists(dbp):
        log("no database at %s" % dbp)
        return EXIT_NO_SOURCE
    con = open_db(dbp, readonly=True)
    try:
        r = con.execute(
            "SELECT COUNT(*) c, MIN(date_iso) lo, MAX(date_iso) hi, "
            "SUM(CASE WHEN amount_paise IS NULL THEN 1 ELSE 0 END) noamt, "
            "SUM(COALESCE(amount_paise,0)) tot FROM payment_register"
        ).fetchone()
    except sqlite3.Error:
        log("the payment_register table does not exist yet in %s" % dbp)
        con.close()
        return EXIT_NO_SOURCE
    log("payment_register  ·  %s" % stamp())
    log("  rows            %d" % r["c"])
    log("  dated           %s .. %s" % (r["lo"] or "-", r["hi"] or "-"))
    log("  without amount  %d" % (r["noamt"] or 0))
    log("  sum of amounts  Rs %.2f  (every row, copies included)"
        % ((r["tot"] or 0) / 100.0))
    try:
        d = con.execute(
            "SELECT SUM(amount_paise) t, COUNT(*) n FROM payment_register_v "
            "WHERE counts_once=1").fetchone()
        log("  counted once    Rs %.2f across %d payments"
            % ((d["t"] or 0) / 100.0, d["n"] or 0))
        e = con.execute(
            "SELECT COUNT(*) n, SUM(amount_paise) t FROM payment_register_v "
            "WHERE counts_once=0 AND amount_paise IS NOT NULL").fetchone()
        log("  same-day copies %d rows, Rs %.2f — the same money counted twice"
            % (e["n"] or 0, (e["t"] or 0) / 100.0))
    except sqlite3.Error:
        log("  counted once    (view not built yet — run ingest once)")
    log("  last ingest     %s" % (meta_get(con, "last_ingest_at") or "never"))
    log("  source pulled   %s" % (meta_get(con, "source_pulled_at_ist") or "-"))
    log("  source csv      %s" % (meta_get(con, "source_csv") or "-"))
    d = con.execute("SELECT COUNT(*) c FROM payment_register_drift").fetchone()
    log("  drift entries   %d" % d["c"])
    log("  TOP VENDORS")
    for v in con.execute(
            "SELECT vendor, COUNT(*) n, SUM(COALESCE(amount_paise,0)) s "
            "FROM payment_register GROUP BY vendor ORDER BY n DESC LIMIT 8"):
        log("    %-38s %4d   Rs %12.2f"
            % (v["vendor"][:38] or "(blank)", v["n"], (v["s"] or 0) / 100.0))
    con.close()
    return EXIT_OK


# --------------------------------------------------------------- selftest ----
HDR = ["Date", "Vendor", "Description", "Amount (Rs)",
       "Attachment in Drive", "Gmail Link"]


def _write_csv(d, rows, header=None):
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "Sheet1.csv")
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header or HDR)
        w.writerows(rows)
    meta = {"title": "Payment Register", "pulled_at_ist": stamp(),
            "tabs": [{"tab": "Sheet1", "file": "Sheet1.csv",
                      "rows": len(rows) + 1}]}
    with open(os.path.join(d, BOOK_META), "w", encoding="utf-8") as fh:
        json.dump(meta, fh)
    return p


def selftest():
    fails = []
    n = [0]

    def check(name, cond):
        n[0] += 1
        if not cond:
            fails.append(name)
            log("  FAIL  %s" % name)

    # ---- parsers ----------------------------------------------------------
    check("date: DD-MM-YYYY reads day-first (03-04-2026 is 3 April)",
          parse_date("03-04-2026") == "2026-04-03")
    check("date: DD/MM/YYYY accepted", parse_date("19/07/2026") == "2026-07-19")
    check("date: ISO accepted", parse_date("2026-07-19") == "2026-07-19")
    check("date: blank -> None", parse_date("") is None)
    check("date: impossible date -> None, not a crash",
          parse_date("31-02-2026") is None)
    check("date: prose -> None", parse_date("last tuesday") is None)

    check("amount: plain rupees -> paise", parse_amount("3560.0") == 356000)
    check("amount: integer -> paise", parse_amount("3560") == 356000)
    check("amount: commas stripped", parse_amount("1,23,456.78") == 12345678)
    check("amount: rupee sign stripped", parse_amount("₹ 1,234.50") == 123450)
    check("amount: 'Rs' stripped", parse_amount("Rs 99") == 9900)
    check("amount: one paisa survives", parse_amount("0.01") == 1)
    check("amount: three decimals truncate, never round up",
          parse_amount("1.999") == 199)
    check("amount: BLANK IS None AND NOT ZERO", parse_amount("") is None)
    check("amount: prose -> None", parse_amount("see mail") is None)
    check("amount: bracket negative", parse_amount("(500)") == -50000)
    check("amount: minus negative", parse_amount("-500") == -50000)

    check("flag: Yes -> 1", parse_flag("Yes") == 1)
    check("flag: No -> 0", parse_flag("no") == 0)
    check("flag: unknown word -> None, never a silent False",
          parse_flag("maybe") is None)

    check("header: the six known columns pass", header_ok(HDR))
    check("header: a SEVENTH column is refused, not ignored",
          not header_ok(HDR + ["Notes"]))
    check("header: a renamed column is refused",
          not header_ok(["Date", "Supplier", "Description", "Amount (Rs)",
                         "Attachment in Drive", "Gmail Link"]))
    check("header: a missing column is refused", not header_ok(HDR[:5]))

    # ---- end to end -------------------------------------------------------
    tmp = tempfile.mkdtemp(prefix="paysel_")
    sheets = os.path.join(tmp, "sheets")
    book = os.path.join(sheets, BOOK_LABEL)
    dbp = os.path.join(tmp, "finance.db")

    r1 = ["19-07-2026", "Hostinger", "Renewal", "3560.0", "No", "https://m/1"]
    r2 = ["20-07-2026", "ICICI", "Card bill", "", "Yes", "https://m/2"]
    r3 = ["21-07-2026", "Tata Power", "Electricity", "1,240.50", "Yes",
          "https://m/3"]

    _write_csv(book, [r1, r2])
    s = ingest(db_path=dbp, sheets_dir=sheets, quiet=True)
    check("ingest: first run adds both rows", s["added"] == 2)
    check("ingest: row_no starts at 2 (row 1 is the header)",
          open_db(dbp, True).execute(
              "SELECT MIN(row_no) m FROM payment_register").fetchone()["m"] == 2)
    check("ingest: a blank amount is stored NULL, not 0",
          open_db(dbp, True).execute(
              "SELECT amount_paise a FROM payment_register WHERE row_no=3"
          ).fetchone()["a"] is None)
    check("ingest: money is integer paise",
          open_db(dbp, True).execute(
              "SELECT amount_paise a FROM payment_register WHERE row_no=2"
          ).fetchone()["a"] == 356000)

    s = ingest(db_path=dbp, sheets_dir=sheets, quiet=True)
    check("ingest: RE-RUNNING THE SAME CSV CHANGES NOTHING (idempotent)",
          s["added"] == 0 and s["changed"] == 0 and s["unchanged"] == 2)

    _write_csv(book, [r1, r2, r3])
    s = ingest(db_path=dbp, sheets_dir=sheets, quiet=True)
    check("ingest: an appended row is added and the rest left alone",
          s["added"] == 1 and s["changed"] == 0 and s["unchanged"] == 2)
    check("ingest: total is 3", s["total"] == 3)

    r2b = list(r2)
    r2b[1] = "ICICI Bank"
    _write_csv(book, [r1, r2b, r3])
    s = ingest(db_path=dbp, sheets_dir=sheets, quiet=True)
    check("ingest: a corrected cell counts as changed, not added",
          s["changed"] == 1 and s["added"] == 0)
    check("ingest: the change is recorded in the drift log with old and new",
          any(f == "vendor" and w == "ICICI" and nv == "ICICI Bank"
              for (_rn, f, w, nv) in s["drift"]))
    check("ingest: the revision counter moved",
          open_db(dbp, True).execute(
              "SELECT revisions r FROM payment_register WHERE row_no=3"
          ).fetchone()["r"] == 1)

    # a shrink must refuse and touch nothing
    _write_csv(book, [r1])
    before = open_db(dbp, True).execute(
        "SELECT COUNT(*) c FROM payment_register").fetchone()["c"]
    code = None
    try:
        ingest(db_path=dbp, sheets_dir=sheets, quiet=True)
    except SystemExit as ex:
        code = ex.code
    after = open_db(dbp, True).execute(
        "SELECT COUNT(*) c FROM payment_register").fetchone()["c"]
    check("shrink: a shorter sheet REFUSES with exit 42", code == EXIT_SHRANK)
    check("shrink: and the table is left exactly as it was",
          before == after == 3)

    s = ingest(db_path=dbp, sheets_dir=sheets, quiet=True, allow_shrink=True)
    check("shrink: --allow-shrink proceeds when typed on purpose",
          s["source_rows"] == 1)
    check("shrink: rows no longer in the sheet are REPORTED, never deleted",
          s["gone"] == [3, 4] and s["total"] == 3)

    # a bad header must refuse and touch nothing
    _write_csv(book, [r1, r2, r3], header=HDR + ["Notes"])
    code = None
    try:
        ingest(db_path=dbp, sheets_dir=sheets, quiet=True)
    except SystemExit as ex:
        code = ex.code
    check("header: a changed sheet header REFUSES with exit 11",
          code == EXIT_BAD_HEADER)
    check("header: and the table is untouched",
          open_db(dbp, True).execute(
              "SELECT COUNT(*) c FROM payment_register").fetchone()["c"] == 3)

    # a stale pull must refuse
    _write_csv(book, [r1, r2, r3])
    old = (datetime.datetime.now(IST)
           - datetime.timedelta(hours=STALE_HOURS + 5))
    with open(os.path.join(book, BOOK_META), "w", encoding="utf-8") as fh:
        json.dump({"title": "Payment Register",
                   "pulled_at_ist": old.strftime("%Y-%m-%d %H:%M:%S IST"),
                   "tabs": [{"tab": "Sheet1", "file": "Sheet1.csv"}]}, fh)
    code = None
    try:
        ingest(db_path=dbp, sheets_dir=sheets, quiet=True)
    except SystemExit as ex:
        code = ex.code
    check("stale: a pull older than the limit REFUSES with exit 43",
          code == EXIT_STALE)
    s = ingest(db_path=dbp, sheets_dir=sheets, quiet=True, ignore_stale=True)
    check("stale: --ignore-stale proceeds when typed on purpose",
          s["source_rows"] == 3)

    # ---- the duplicate view ----------------------------------------------
    dbp5 = os.path.join(tmp, "f5.db")
    dup = ["19-07-2026", "MyOperator", "renewal", "1000", "No", "https://m/a"]
    _write_csv(book, [dup, list(dup), list(dup),
                      ["19-07-2026", "MyOperator", "other", "250", "No",
                       "https://m/b"]])
    ingest(db_path=dbp5, sheets_dir=sheets, quiet=True)
    cx = open_db(dbp5, True)
    check("view: three emails about one payment are all KEPT in the table",
          cx.execute("SELECT COUNT(*) c FROM payment_register").fetchone()["c"]
          == 4)
    check("view: but only ONE of the three counts once",
          cx.execute("SELECT COUNT(*) c FROM payment_register_v "
                     "WHERE counts_once=1").fetchone()["c"] == 2)
    check("view: the counted-once total is the honest one "
          "(Rs 1000 + Rs 250, not Rs 3250)",
          cx.execute("SELECT SUM(amount_paise) s FROM payment_register_v "
                     "WHERE counts_once=1").fetchone()["s"] == 125000)
    check("view: a different amount on the same day is NOT a copy",
          cx.execute("SELECT same_day_copies c FROM payment_register_v "
                     "WHERE amount_paise=25000").fetchone()["c"] == 1)
    cx.close()

    # THE DATE SHAPE — the guard that stands between a re-format in a browser
    # and a table of wrong dates.
    check("dates: a coerced cell displayed mm-dd-yyyy round-trips to the "
          "Janitor's own text and reads day-first (09-07-2026 is 9 July)",
          parse_date("09-07-2026") == "2026-07-09")
    check("dates: a month-first string does NOT quietly parse",
          parse_date("07-19-2026") is None)

    bad_dates = [["%02d-19-2026" % i, "V%d" % i, "d", "10", "No", "https://m/x"]
                 for i in range(1, 13)]
    _write_csv(book, bad_dates)
    dbp3 = os.path.join(tmp, "f3.db")
    code = None
    try:
        ingest(db_path=dbp3, sheets_dir=sheets, quiet=True)
    except SystemExit as ex:
        code = ex.code
    check("dates: a column re-formatted month-first REFUSES with exit 44",
          code == EXIT_DATE_SHAPE)
    check("dates: and nothing was written at all",
          not os.path.exists(dbp3) or open_db(dbp3, True).execute(
              "SELECT COUNT(*) c FROM payment_register").fetchone()["c"] == 0)

    ok_dates = [["19-07-2026", "A", "d", "10", "No", "https://m/x"]] * 20 \
        + [["typed by hand", "B", "d", "10", "No", "https://m/y"]]
    _write_csv(book, ok_dates)
    dbp4 = os.path.join(tmp, "f4.db")
    s = ingest(db_path=dbp4, sheets_dir=sheets, quiet=True)
    check("dates: ONE unreadable date in twenty-one is tolerated, not fatal",
          s["undated"] == 1 and s["added"] == 21)
    check("dates: the unreadable one keeps its raw text and a NULL date",
          open_db(dbp4, True).execute(
              "SELECT date_raw, date_iso FROM payment_register "
              "WHERE date_iso IS NULL").fetchone()["date_raw"]
          == "typed by hand")

    # a missing source must refuse
    code = None
    try:
        ingest(db_path=dbp, sheets_dir=os.path.join(tmp, "nowhere"), quiet=True)
    except SystemExit as ex:
        code = ex.code
    check("source: a missing pull directory REFUSES with exit 10",
          code == EXIT_NO_SOURCE)

    # blank lines must not shift row numbers
    p = os.path.join(book, "Sheet1.csv")
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        w.writerow(r1)
        w.writerow(["", "", "", "", "", ""])
        w.writerow(r3)
    dbp2 = os.path.join(tmp, "f2.db")
    with open(os.path.join(book, BOOK_META), "w", encoding="utf-8") as fh:
        json.dump({"title": "x", "pulled_at_ist": stamp(),
                   "tabs": [{"tab": "Sheet1", "file": "Sheet1.csv"}]}, fh)
    s = ingest(db_path=dbp2, sheets_dir=sheets, quiet=True)
    got = [r["row_no"] for r in open_db(dbp2, True).execute(
        "SELECT row_no FROM payment_register ORDER BY row_no")]
    check("blank line: is skipped but STILL CONSUMES ITS ROW NUMBER "
          "(2 and 4, never 2 and 3)", got == [2, 4])

    # the one thing this script must never be able to do
    src = open(os.path.abspath(__file__), encoding="utf-8").read() \
        if os.path.exists(os.path.abspath(__file__)) else ""
    if src:
        check("no write-back: the file imports no Google or network library",
              not re.search(r"^\s*(import|from)\s+"
                            r"(gspread|google|googleapiclient|requests|urllib|"
                            r"http|socket)\b", src, re.M))
        check("no write-back: the file contains no http(s) destination",
              not re.search(r"https?://(?!m/)", src.split("selftest")[0]))

    log("")
    log("selftest: %d checks, %d failures" % (n[0], len(fails)))
    for f in fails:
        log("  FAILED: %s" % f)
    return EXIT_OK if not fails else 1


# ------------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser(
        description="Payment Register: read the pulled Google sheet into a "
                    "real table on this box. One way, never a write-back.")
    ap.add_argument("mode", choices=("ingest", "status", "selftest"))
    ap.add_argument("--allow-shrink", action="store_true",
                    help="proceed even though the sheet has fewer rows than "
                         "the table (never automatic)")
    ap.add_argument("--ignore-stale", action="store_true",
                    help="proceed even though the pulled CSV is old")
    ap.add_argument("--db", default=None)
    ap.add_argument("--sheets-dir", default=None)
    a = ap.parse_args()
    if a.mode == "selftest":
        sys.exit(selftest())
    if a.mode == "status":
        sys.exit(status(a.db))
    ingest(allow_shrink=a.allow_shrink, ignore_stale=a.ignore_stale,
           db_path=a.db, sheets_dir=a.sheets_dir)
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
