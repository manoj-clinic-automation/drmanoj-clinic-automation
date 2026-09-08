#!/root/wa/venv/bin/python3
# =============================================================================
#  sheets_pull.py  ·  Session 233  ·  S233_SHEETS_BACKUP  ·  v1
#
#  THE SEVEN SHEETS ARE THE DATA. THE CODE CAN BE REWRITTEN; THEY CANNOT.
#
#  S232 measured the Google plane and found the gap: the live Google Sheets --
#  the call-duration feed, the WhatsApp inbox, the doctor-only verdicts, the
#  accounting books, the payment register -- have ZERO copies anywhere. Not on
#  the VPS, not in the repository, not on the SSD. Everything else in this
#  estate has at least one copy; these have none.
#
#  THIS SCRIPT DOES NOT SHIP ANYTHING. It has no Drive upload, no network
#  destination and no key. It pulls each configured spreadsheet down to CSV
#  under one directory on the box, and then STOPS. The shipping is done by
#  clinic_state_backup.py, which has carried an AES-256 bundle to Drive nightly
#  since S230 with a restore that has been drilled and passed. S233 adds that
#  directory to that job's sources -- ONE line -- and invents no second
#  mechanism. That was the owner's instruction and it is the whole design.
#
#  WHY CSV AND NOT XLSX: a CSV per tab is readable by anything, forever, with
#  no library and no Google. A restore is a paste. The book's shape (tab names,
#  dimensions, row counts) is preserved separately in _BOOK.json.
#
#  Refusal stances, absolute -- a bad day must never overwrite a good backup:
#    * a book that exported last run and cannot be opened now  -> EXIT 41,
#      and its PREVIOUS export is left exactly where it is
#    * a tab that had rows last run and returns zero rows now  -> that BOOK is
#      not swapped in; the previous export stands, and the run exits 42
#    * a shrink beyond SHRINK_GUARD_PCT of last run's rows     -> same
#    * no service-account key, no conf, no sheet list          -> EXIT 10
#  A refusal is never silent: every one names the book and the tab.
#
#  A BACKUP THAT CANNOT STATE ITS OWN AGE HAS NOT BEEN TAKEN. Every run writes
#  _TAKEN_AT.json at the root of the export directory: per book, the IST time
#  of its last success, its tab count and its row counts. That file rides
#  inside the encrypted bundle with the data, so a restored bundle can be
#  interrogated about its own freshness without this script or this box.
#
#  Modes:
#    preflight  open every configured book WITHOUT writing anything, and print
#               one line per book: reachable or not, title, tab count. This is
#               how a newly shared sheet is proven before it is trusted.
#    run        the pull.
#    list       what is on disk now and how old it is. Read-only, no network.
#
#  Config: /root/state_backup/clinic_state_backup.conf -- the SAME conf the
#  S230 job already uses, so SA_JSON is read once and named once. Keys added:
#      SHEETS_DIR=/root/state_backup/sheets      (optional; this is the default)
#      SHEETS=<id>:<label>,<id>:<label>,...      (required)
#      SHRINK_GUARD_PCT=20                       (optional; this is the default)
#  Spreadsheet ids live in the CONF and never in this file (F-185), the same
#  stance clinic_state_backup.py takes for every id, path and secret.
#
#  Cron, five minutes before the bundle at 01:50:
#    45 1 * * *  /root/wa/venv/bin/python3 /root/state_backup/sheets_pull.py run >> /root/state_backup/sheets_pull.log 2>&1
#
#  No patient data is interpreted here and no value is printed: this script
#  copies cells it never reads. Row COUNTS are printed; cell CONTENT is not.
# =============================================================================
import csv
import datetime
import hashlib
import json
import os
import shutil
import sys
import tempfile

CONF_PATH = "/root/state_backup/clinic_state_backup.conf"

SHEETS_DIR_DEFAULT = "/root/state_backup/sheets"
SHRINK_GUARD_PCT_DEFAULT = 20.0
TAKEN_AT = "_TAKEN_AT.json"
BOOK_META = "_BOOK.json"
STAGING = ".staging"

EXIT_OK = 0
EXIT_CONF = 10
EXIT_DEPS = 11
EXIT_UNREACHABLE = 41
EXIT_SHRANK = 42

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


# ------------------------------------------------------------------- log ----
def now_ist():
    return datetime.datetime.now(IST)


def stamp():
    return now_ist().strftime("%Y-%m-%d %H:%M:%S IST")


def log(*a):
    print(stamp(), "|", *a, flush=True)


def die(code, *a):
    log("FATAL:", *a)
    sys.exit(code)


# ---------------------------------------------------------------- config ----
def load_conf():
    conf = {}
    if os.path.exists(CONF_PATH):
        for line in open(CONF_PATH):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def sheets_dir(conf):
    return conf.get("SHEETS_DIR") or SHEETS_DIR_DEFAULT


def shrink_guard(conf):
    try:
        return float(conf.get("SHRINK_GUARD_PCT") or SHRINK_GUARD_PCT_DEFAULT)
    except ValueError:
        return SHRINK_GUARD_PCT_DEFAULT


def safe_label(raw):
    """A label becomes a directory name. Anything that is not a plain name is
    replaced, so a book title can never escape the export directory."""
    out = []
    for ch in raw.strip():
        out.append(ch if (ch.isalnum() or ch in "-_") else "_")
    s = "".join(out).strip("_")
    return s or "book"


def parse_sheets(conf):
    """SHEETS=<id>:<label>,<id>:<label>  ->  [(id, label), ...]

    The id is taken verbatim; the label is made directory-safe. A duplicate
    label is refused rather than silently overwriting its twin."""
    raw = (conf.get("SHEETS") or "").strip()
    if not raw:
        die(EXIT_CONF, "SHEETS= is not set in %s. This script never guesses a"
                       " spreadsheet id." % CONF_PATH)
    out, seen = [], set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            die(EXIT_CONF, "SHEETS entry %r is not <id>:<label>." % part)
        sid, label = part.split(":", 1)
        sid, label = sid.strip(), safe_label(label)
        if not sid:
            die(EXIT_CONF, "SHEETS entry %r has no id." % part)
        if label in seen:
            die(EXIT_CONF, "two SHEETS entries share the label %r — one would"
                           " overwrite the other." % label)
        seen.add(label)
        out.append((sid, label))
    if not out:
        die(EXIT_CONF, "SHEETS= parsed to nothing.")
    return out


# ------------------------------------------------------------------ state ----
def taken_at_path(conf):
    return os.path.join(sheets_dir(conf), TAKEN_AT)


def load_taken(conf):
    p = taken_at_path(conf)
    if os.path.exists(p):
        try:
            with open(p) as fh:
                return json.load(fh)
        except (OSError, ValueError) as ex:
            log("WARNING: %s is unreadable (%s) — treating this as a first run"
                " for every book." % (TAKEN_AT, ex))
    return {"books": {}}


def save_taken(conf, state):
    p = taken_at_path(conf)
    state["written_at_ist"] = stamp()
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, p)
    os.chmod(p, 0o600)


# ------------------------------------------------------------------ drive ----
def find_sa_key(conf):
    key = (conf.get("SA_JSON") or "").strip()
    if not key:
        die(EXIT_CONF, "SA_JSON= is not set in %s. This script never guesses"
                       " the path to a key." % CONF_PATH)
    if not os.path.isfile(key):
        die(EXIT_CONF, "the service-account key named by SA_JSON= is not a file"
                       " on this box.")
    return key


def open_client(conf):
    try:
        import gspread
    except ImportError:
        die(EXIT_DEPS, "gspread is not importable. Run this with the venv"
                       " python, not the system python3.")
    return gspread.service_account(filename=find_sa_key(conf))


def book_rows(worksheet):
    """Every value in the tab, as a list of rows. gspread pads short rows, so
    the width is the widest row; nothing is trimmed and nothing is parsed."""
    return worksheet.get_all_values()


# ------------------------------------------------------------------- pull ----
def write_book(dest, title, tabs):
    """tabs is [(tab_title, rows)]. Writes one CSV per tab plus _BOOK.json.
    Returns the meta dict."""
    os.makedirs(dest, exist_ok=True)
    meta = {"title": title, "pulled_at_ist": stamp(), "tabs": []}
    for tab_title, rows in tabs:
        fname = safe_label(tab_title) + ".csv"
        path = os.path.join(dest, fname)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh, quoting=csv.QUOTE_MINIMAL).writerows(rows)
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        meta["tabs"].append({
            "tab": tab_title,
            "file": fname,
            "rows": len(rows),
            "cols": max((len(r) for r in rows), default=0),
            "bytes": os.path.getsize(path),
            "md5": h.hexdigest(),
        })
    meta["row_total"] = sum(t["rows"] for t in meta["tabs"])
    with open(os.path.join(dest, BOOK_META), "w") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)
    return meta


def judge_shrink(label, meta, previous, guard_pct):
    """A backup must never let a bad day overwrite a good copy. Returns a list
    of complaints; empty means the new export may be swapped in."""
    if not previous:
        return []
    bad = []
    prev_tabs = {t["tab"]: t for t in previous.get("tabs", [])}
    new_tabs = {t["tab"]: t for t in meta.get("tabs", [])}
    for tab, prev in prev_tabs.items():
        was = prev.get("rows", 0)
        if was <= 0:
            continue
        if tab not in new_tabs:
            bad.append("%s / %s : the tab existed last run and is gone now"
                       % (label, tab))
            continue
        now = new_tabs[tab].get("rows", 0)
        if now == 0:
            bad.append("%s / %s : %d rows last run, ZERO now" % (label, tab, was))
        elif now < was * (1.0 - guard_pct / 100.0):
            bad.append("%s / %s : %d rows last run, %d now — a fall of more"
                       " than %.0f%%" % (label, tab, was, now, guard_pct))
    return bad


def swap_in(staged, final):
    """Replace final with staged, keeping the old copy until the new one is
    in place. Never leaves the destination missing."""
    old = final + ".previous"
    if os.path.isdir(old):
        shutil.rmtree(old)
    if os.path.isdir(final):
        os.rename(final, old)
    os.rename(staged, final)
    if os.path.isdir(old):
        shutil.rmtree(old)


def do_run(conf):
    # EVERYTHING THAT CAN REFUSE, REFUSES FIRST — before a single directory is
    # made. The walk caught this: a duplicate label used to die AFTER .staging
    # had been created, leaving it behind for the next run to trip over.
    root = sheets_dir(conf)
    books = parse_sheets(conf)
    guard = shrink_guard(conf)
    find_sa_key(conf)

    os.makedirs(root, exist_ok=True)
    os.chmod(root, 0o700)
    state = load_taken(conf)
    prev_books = state.get("books", {})
    gc = open_client(conf)

    staging_root = os.path.join(root, STAGING)
    if os.path.isdir(staging_root):
        shutil.rmtree(staging_root)
    os.makedirs(staging_root, 0o700)

    try:
        return _pull(conf, root, staging_root, books, guard, state, prev_books, gc)
    finally:
        # A refusal exits through die(); the staging tree must go either way.
        shutil.rmtree(staging_root, ignore_errors=True)


def _pull(conf, root, staging_root, books, guard, state, prev_books, gc):
    unreachable, shrank, done = [], [], []
    for sid, label in books:
        previous = prev_books.get(label, {}).get("meta")
        try:
            sh = gc.open_by_key(sid)
            tabs = [(ws.title, book_rows(ws)) for ws in sh.worksheets()]
            title = sh.title
        except Exception as ex:                      # noqa: BLE001 — any failure
            if previous:
                unreachable.append("%s : could not be opened this run (%s) and"
                                   " WAS exported last run. Its previous export"
                                   " is untouched." % (label, type(ex).__name__))
            else:
                unreachable.append("%s : could not be opened, and has never been"
                                   " exported (%s). If it was only just shared,"
                                   " run preflight." % (label, type(ex).__name__))
            continue

        staged = os.path.join(staging_root, label)
        meta = write_book(staged, title, tabs)
        complaints = judge_shrink(label, meta, previous, guard)
        if complaints:
            shrank.extend(complaints)
            log("REFUSED to swap in %s — the previous export stands." % label)
            continue

        swap_in(staged, os.path.join(root, label))
        prev_books[label] = {"last_success_ist": stamp(), "meta": meta}
        done.append("%s : %d tab(s), %d row(s)"
                    % (label, len(meta["tabs"]), meta["row_total"]))

    state["books"] = prev_books
    save_taken(conf, state)

    for line in done:
        log("OK  ", line)
    for line in unreachable:
        log("MISS", line)
    for line in shrank:
        log("HOLD", line)

    log("%d of %d book(s) exported into %s" % (len(done), len(books), root))
    if unreachable:
        die(EXIT_UNREACHABLE, "%d book(s) could not be read. Nothing good was"
                              " overwritten." % len(unreachable))
    if shrank:
        die(EXIT_SHRANK, "%d tab(s) shrank past the guard. The previous export"
                         " stands and nothing was overwritten." % len(shrank))
    log("PULL OK")
    return EXIT_OK


def do_preflight(conf):
    books = parse_sheets(conf)
    find_sa_key(conf)
    gc = open_client(conf)
    bad = 0
    for sid, label in books:
        try:
            sh = gc.open_by_key(sid)
            names = [ws.title for ws in sh.worksheets()]
            log("REACHABLE  %-24s %-44s %d tab(s): %s"
                % (label, sh.title, len(names), ", ".join(names)))
        except Exception as ex:                      # noqa: BLE001
            bad += 1
            log("NOT SHARED %-24s %s — share this sheet with the service"
                " account as Viewer, then run preflight again."
                % (label, type(ex).__name__))
    log("%d of %d book(s) reachable." % (len(books) - bad, len(books)))
    if bad:
        die(EXIT_UNREACHABLE, "%d book(s) are not readable by the service"
                              " account. Nothing was written." % bad)
    log("PREFLIGHT OK")
    return EXIT_OK


def do_list(conf):
    root = sheets_dir(conf)
    state = load_taken(conf)
    if not os.path.isdir(root):
        log("nothing on disk: %s does not exist" % root)
        return EXIT_OK
    log("export directory: %s" % root)
    log("last written    : %s" % state.get("written_at_ist", "never"))
    for label, rec in sorted(state.get("books", {}).items()):
        meta = rec.get("meta", {})
        log("  %-24s %s  %d tab(s), %d row(s)"
            % (label, rec.get("last_success_ist", "never"),
               len(meta.get("tabs", [])), meta.get("row_total", 0)))
    return EXIT_OK


MODES = {"run": do_run, "preflight": do_preflight, "list": do_list}


def main(argv):
    mode = (argv[1] if len(argv) > 1 else "").strip()
    if mode not in MODES:
        print("usage: sheets_pull.py {preflight|run|list}")
        return 2
    if not os.path.exists(CONF_PATH):
        die(EXIT_CONF, "%s does not exist. Install the S230 state-backup kit"
                       " first; this script shares its conf." % CONF_PATH)
    return MODES[mode](load_conf())


if __name__ == "__main__":
    sys.exit(main(sys.argv))
