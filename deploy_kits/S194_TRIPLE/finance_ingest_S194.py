#!/usr/bin/env python3
# =============================================================================
#  finance_ingest.py  ·  patient-wise sale lines, from a swappable source
#  Session 179 · step B3a
#
#  WHY THIS SHAPE
#    The owner's ruling: "if sarvam isn't up to the mark we will export or pull
#    the sale report from Marg pharmacy software — same for pathology, Labmate."
#    So the source must be a decision we can change later without a rewrite.
#    Every adapter here does one job: turn whatever it is given into a list of
#    RawLine dicts. Everything downstream — matching, review, reconciliation —
#    is shared and knows nothing about where the lines came from.
#
#  ADAPTERS
#    csv_generic / marg_export / labmate_export
#        Column-mapped. The mapping lives in ingest_column_map, so a new vendor
#        format is CONFIGURATION, not code. Written to be filled in from a real
#        Marg / Labmate file rather than guessed at now (F-66: a filename — or a
#        format — is not provenance).
#    sarvam_ocr
#        Calls the existing shared /root/shared/sarvam_ocr.py. Absent in this
#        offline build, so it degrades to "unavailable" rather than pretending.
#    manual
#        Typed lines, for when a day simply has to be entered by hand.
#
#  THE RULE THAT KEEPS THIS SAFE
#    Attribution NEVER moves the books. The day's money is settled by the day
#    figures and the bank statement. If the lines add up to less than the day
#    total, the day total stands and an exception opens for the difference.
#
#  Money is INTEGER PAISE. Stdlib only.
#
#  ---------------------------------------------------------------------------
#  S180 — SALE RETURNS (credit notes).  Previously every row with an amount of
#  zero or less was skipped outright:
#
#        if amount is None or amount <= 0:
#            continue
#
#  That guard exists to throw away junk rows, and it must stay. But Marg writes
#  a sale return as a NEGATIVE bill (CN00167  -1150.00), so it also threw away
#  every refund — silently. The day then read as though no return had happened,
#  and the named lines exceeded the real day total by the value of the returns.
#
#  It is now split into the two different things it was conflating:
#      · no readable amount, or exactly zero  -> still junk, still skipped
#      · a genuine negative                   -> a RETURN, kept and labelled
#
#  Returns are stored as a POSITIVE amount_p carrying a service of
#  "<base>_return".  They are NOT stored as negative numbers, because
#  sale_item.amount_p is declared CHECK (amount_p >= 0) — a deliberate
#  invariant (amounts are magnitudes; direction is the row's type). Honouring
#  it means no table rebuild on a live store holding real patient data; only
#  the v_day_attribution view changes, to net the returns back out.
#  See finance_migration_S180_returns.sql.
# =============================================================================

import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import sqlite3

WALK_IN = "WALK-IN"


# ----------------------------------------------------------------- helpers

def paise(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "")
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    if s.startswith("-"):
        neg, s = True, s[1:]
    if not re.fullmatch(r"\d+(\.\d{1,3})?", s or ""):
        return None
    val = int(round(float(s) * 100))
    return -val if neg else val


def parse_date(v, fmt=None):
    """Never slice a date string — parse it (F-78)."""
    s = str(v or "").strip().split(" ")[0]
    fmts = [fmt] if fmt else []
    fmts += ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d.%m.%Y", "%d-%b-%Y"]
    for f in fmts:
        if not f:
            continue
        try:
            d = dt.datetime.strptime(s, f).date()
        except ValueError:
            continue
        return d if d.year >= 1900 else None
    return None


def apply_transform(value, transform, fmt=None):
    if not transform:
        return value
    if transform == "strip_rs":
        return re.sub(r"(?i)\b(rs\.?|inr)\b", "", str(value or "")).strip()
    if transform == "negate":
        p = paise(value)
        return None if p is None else -p / 100.0
    if transform in ("ddmmyyyy", "date"):
        d = parse_date(value, fmt)
        return d.isoformat() if d else None
    return value


# A clinic ID clubbed with the name, as the counter is meant to write it:
#   "4471 Ramesh Kumar" · "4471-Ramesh Kumar" · "Ramesh Kumar (4471)"
CLINIC_ID_PATTERNS = (
    # "4471 Ramesh Kumar" · "4471-Ramesh Kumar" · "4471/Ramesh Kumar"
    re.compile(r"^\s*(?P<cid>[A-Za-z]{0,3}\d{2,8})\s*(?:[-/:.]\s*|\s+)(?P<name>.+?)\s*$"),
    # "Ramesh Kumar (4471)"
    re.compile(r"^\s*(?P<name>.+?)\s*[\(\[]\s*(?P<cid>[A-Za-z]{0,3}\d{2,8})\s*[\)\]]\s*$"),
)


def split_clinic_id(text):
    """Return (clinic_id, name, confidence). Never guesses an ID it cannot see."""
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    if not s:
        return None, None, 0.0
    for pat in CLINIC_ID_PATTERNS:
        m = pat.match(s)
        if m:
            cid = m.group("cid").upper()
            name = m.group("name").strip(" -/:.")
            if name and not name.isdigit():
                return cid, name, 0.95
    if re.fullmatch(r"[A-Za-z]{0,3}\d{2,8}", s):
        return s.upper(), None, 0.6          # an ID with no name
    return None, s, 0.5                      # a name with no ID


# ----------------------------------------------------------------- adapters

class AdapterUnavailable(Exception):
    """Raised when an adapter genuinely cannot run. We say so; we never fake it."""


# A sale return is a real transaction, not a junk row. Adapters return the
# MAGNITUDE in amount_p and say which direction it went in "kind".
KIND_SALE = "sale"
KIND_RETURN = "return"


# --- S194 ⭐2 home-medicine ------------------------------------------------
#  A "home-medicine" sale is a bill made out to the clinic's own home-delivery
#  account, which Marg writes into the bill's customer/description field as
#  "Home Medicine" / "Home Medisun" (owner, S194).  These are populated from
#  the Marg export automatically — no manual scan — and tagged so they show as
#  their own line rather than as walk-in sales.
_HOME_MED_RX = re.compile(r"home\s*medi", re.I)


def is_home_medicine(name):
    """1 if the bill's patient/customer text names the home-medicine account."""
    return 1 if (name and _HOME_MED_RX.search(str(name))) else 0


def _ensure_home_med_col(con):
    """Lazy ALTER (DDL authoritative in code): sale_item.home_med (0/1)."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(sale_item)")}
    if "home_med" not in cols:
        con.execute("ALTER TABLE sale_item ADD COLUMN home_med INTEGER DEFAULT 0")


# --- S194 ⭐3 cash/UPI reclassification log --------------------------------
def _ensure_mode_change_log(con):
    """DDL authoritative in code (lazy create; idempotent).  Records every time
    a re-import flips a bill's payment mode (cash<->upi, either direction) so
    Amir's counter conversions stop being silent."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS mode_change_log ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " unit TEXT NOT NULL,"
        " business_date TEXT NOT NULL,"
        " source_ref TEXT,"
        " patient_ref_id INTEGER,"
        " amount_p INTEGER,"
        " old_mode TEXT,"
        " new_mode TEXT,"
        " ingest_batch_id INTEGER,"
        " changed_at TEXT NOT NULL)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_modechg_day "
                "ON mode_change_log(unit, business_date)")


def classify_amount(amount_p):
    """(magnitude, kind) — or (None, None) if the row carries no usable amount.

    None and exactly zero are junk and stay rejected. A negative is a return."""
    if amount_p is None or amount_p == 0:
        return None, None
    if amount_p < 0:
        return -amount_p, KIND_RETURN
    return amount_p, KIND_SALE


def service_for(unit, kind):
    """pharmacy | pharmacy_return | lab_test | lab_test_return"""
    base = "lab_test" if unit == "lab" else "pharmacy"
    return base + "_return" if kind == KIND_RETURN else base


def signed(amount_p, kind):
    """The value as it affects a day's money."""
    return -amount_p if kind == KIND_RETURN else amount_p


def adapter_csv(payload, colmap, config):
    """Column-mapped delimited text. This is the adapter Marg and Labmate exports
    will use — only their column map differs, which is why it is data, not code."""
    cfg = config or {}
    text = payload if isinstance(payload, str) else payload.decode(cfg.get("encoding", "utf-8"),
                                                                   "replace")
    delim = cfg.get("delimiter")
    if not delim:
        sample = text[:4096]
        delim = "\t" if sample.count("\t") > sample.count(",") else ","
    skip = int(cfg.get("skip_rows", 0) or 0)
    if skip:
        text = "\n".join(text.splitlines()[skip:])
    rdr = csv.DictReader(io.StringIO(text), delimiter=delim)
    if not rdr.fieldnames:
        raise AdapterUnavailable("no header row found")

    norm = {re.sub(r"\s+", " ", (f or "")).strip().lower(): f for f in rdr.fieldnames}

    def col(field):
        their = colmap.get(field, {}).get("their_column")
        if not their:
            return None
        return norm.get(re.sub(r"\s+", " ", their).strip().lower())

    missing = [f for f, m in colmap.items() if m.get("required") and not col(f)]
    if missing:
        raise AdapterUnavailable("required column(s) not found in the file: %s"
                                 % ", ".join(missing))

    out = []
    for row in rdr:
        if not any((v or "").strip() for v in row.values()):
            continue

        def get(field):
            c = col(field)
            if not c:
                return None
            m = colmap.get(field, {})
            return apply_transform(row.get(c), m.get("transform"), cfg.get("date_format"))

        amount, kind = classify_amount(paise(get("amount")))
        if amount is None:
            continue
        cid = (get("clinic_id") or "").strip() or None
        name = (get("patient_name") or "").strip() or None
        conf = 0.99
        if not cid and name:
            cid, name2, conf = split_clinic_id(name)
            name = name2 or name
        _grp = paise(row.get(norm.get("gross")) if norm.get("gross") else None)
        _dsp = paise(row.get(norm.get("disc")) if norm.get("disc") else None)
        out.append(dict(bill_no=(get("bill_no") or "").strip() or None,
                        bill_date=get("bill_date"),
                        clinic_id=cid, patient_name=name,
                        description=(get("description") or "").strip() or None,
                        amount_p=amount, kind=kind,
                        gross_p=(abs(_grp) if _grp is not None else None),
                        disc_p=(abs(_dsp) if _dsp is not None else None),
                        mode=(get("mode") or "").strip().lower() or None,
                        confidence=conf, raw=json.dumps(row, ensure_ascii=False)[:2000]))
    return out


def adapter_sarvam(payload, colmap, config):
    """OCR of the scanned day report via the existing shared library.
    In this offline build the library is absent — so this raises, loudly, rather
    than returning an empty list that would read as 'nothing sold today'."""
    try:
        import sys
        sys.path.insert(0, "/root/shared")
        import sarvam_ocr                                     # noqa: F401  (VPS-only)
    except Exception as ex:                                   # noqa: BLE001
        raise AdapterUnavailable("sarvam_ocr not available here (%s)" % ex)
    raise AdapterUnavailable("sarvam adapter is wired at install; "
                             "line-extraction prompt is tuned on real bills")


def adapter_manual(payload, colmap, config):
    """Typed lines: [{clinic_id, patient_name, amount, description, bill_no}]"""
    out = []
    for r in (payload or []):
        amt, kind = classify_amount(paise(r.get("amount")))
        if amt is None:
            continue
        cid = (r.get("clinic_id") or "").strip() or None
        name = (r.get("patient_name") or "").strip() or None
        if not cid and name:
            cid, n2, _ = split_clinic_id(name)
            name = n2 or name
        out.append(dict(bill_no=(r.get("bill_no") or "").strip() or None,
                        bill_date=r.get("bill_date"), clinic_id=cid, patient_name=name,
                        description=(r.get("description") or "").strip() or None,
                        amount_p=amt, kind=kind,
                        mode=(r.get("mode") or "").strip().lower() or None,
                        confidence=1.0, raw=None))
    return out


ADAPTERS = {
    "csv_generic": adapter_csv,
    "marg_export": adapter_csv,
    "labmate_export": adapter_csv,
    "sarvam_ocr": adapter_sarvam,
    "manual": adapter_manual,
}


# ----------------------------------------------------------------- ingest

def _setting(con, key, default=None):
    r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def _colmap(con, unit, adapter):
    src = con.execute("SELECT id FROM ingest_source WHERE unit=? AND adapter=?",
                      (unit, adapter)).fetchone()
    if not src:
        return {}, {}
    cm = {}
    for r in con.execute("SELECT our_field, their_column, transform, required "
                         "FROM ingest_column_map WHERE source_id=?", (src[0],)):
        cm[r[0]] = dict(their_column=r[1], transform=r[2], required=bool(r[3]))
    cfgrow = con.execute("SELECT config_json FROM ingest_source WHERE id=?", (src[0],)).fetchone()
    cfg = json.loads(cfgrow[0]) if cfgrow and cfgrow[0] else {}
    return cm, cfg


def resolve_patient(con, clinic_id, name):
    """Clinic ID first, name only as a hint. A line with no ID lands on WALK-IN
    rather than being dropped or attached to a guess."""
    if clinic_id:
        r = con.execute("SELECT id, merged_into FROM patient_ref WHERE clinic_id=?",
                        (clinic_id,)).fetchone()
        if r:
            return r[1] or r[0]
        cur = con.execute("INSERT INTO patient_ref (clinic_id, name, first_seen) VALUES (?,?,?)",
                          (clinic_id, name, dt.date.today().isoformat()))
        return cur.lastrowid
    r = con.execute("SELECT id FROM patient_ref WHERE clinic_id=?", (WALK_IN,)).fetchone()
    return r[0] if r else None


def ingest_day(con, unit, business_date, adapter, payload, run_by="system",
               source_ref=None, now=None):
    """Run one adapter over one day. Returns a summary dict.
    Re-running supersedes the previous batch for that day rather than duplicating."""
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    fn = ADAPTERS.get(adapter)
    if not fn:
        raise AdapterUnavailable("unknown adapter %r" % adapter)

    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (unit, business_date)).fetchone()
    if not e:
        raise AdapterUnavailable("no day entry for %s %s — file the day first"
                                 % (unit, business_date))
    eid = e[0]

    _ensure_home_med_col(con)        # S194 ⭐2 — column exists before INSERT
    _ensure_mode_change_log(con)     # S194 ⭐3 — log table exists

    colmap, cfg = _colmap(con, unit, adapter)
    sha = None
    if isinstance(payload, (str, bytes)):
        b = payload.encode("utf-8") if isinstance(payload, str) else payload
        sha = hashlib.sha256(b).hexdigest()

    try:
        lines = fn(payload, colmap, cfg)
        status, error = "ok", None
    except AdapterUnavailable as ex:
        cur = con.execute(
            "INSERT INTO ingest_batch (day_entry_id, unit, adapter, source_ref, sha256, "
            "status, error, run_by, run_at) VALUES (?,?,?,?,?, 'failed', ?, ?, ?)",
            (eid, unit, adapter, source_ref, sha, str(ex), run_by, now))
        con.commit()
        return dict(ok=False, batch_id=cur.lastrowid, adapter=adapter, error=str(ex),
                    rows_read=0, accepted=0, review=0, attributed_p=0)

    # S194 ⭐3 — snapshot each existing bill's payment mode BEFORE the
    # delete-reinsert, keyed by its Marg bill number (source_ref).  On re-import
    # we compare the incoming mode and log any flip.  First import: empty map.
    _prev_mode = {}
    for _r in con.execute(
            "SELECT source_ref, mode FROM sale_item WHERE day_entry_id=? "
            "AND source_ref IS NOT NULL", (eid,)):
        _prev_mode[_r[0]] = _r[1]

    # supersede any earlier batch for this day, and clear what it produced
    for old in con.execute("SELECT id FROM ingest_batch WHERE day_entry_id=? AND status!='superseded'",
                           (eid,)).fetchall():
        con.execute("DELETE FROM sale_item WHERE ingest_batch_id=?", (old[0],))
        con.execute("DELETE FROM sale_item_review WHERE ingest_batch_id=?", (old[0],))
        con.execute("UPDATE ingest_batch SET status='superseded' WHERE id=?", (old[0],))

    cur = con.execute(
        "INSERT INTO ingest_batch (day_entry_id, unit, adapter, source_ref, sha256, "
        "rows_read, status, run_by, run_at) VALUES (?,?,?,?,?,?, 'ok', ?, ?)",
        (eid, unit, adapter, source_ref, sha, len(lines), run_by, now))
    batch_id = cur.lastrowid

    min_conf = float(_setting(con, "ingest.min_confidence", "0.70") or 0.70)
    # S186 / F-114 — A REVIEW QUEUE IS FOR LINES A HUMAN CAN RESOLVE.
    # A line that was read cleanly but carries neither a clinic ID nor a name
    # has NOTHING to resolve: there is no name to look up and no ID to match.
    # Parking it in sale_item_review created a queue that could only grow --
    # 2,062 rows by S186, ~10 more every clinic day, none of them answerable.
    # Both this module's own resolve_patient docstring ("a line with no ID lands
    # on WALK-IN") and marg_report's warning ("will attribute to WALK-IN") said
    # this already; the gate below simply never let the line reach it. Two
    # records describing behaviour the code did not have (F-114).
    # Low confidence still goes to review -- THAT a human can fix.
    anon_to_walkin = (_setting(con, "ingest.anonymous_to_walkin", "1") or "1") not in ("0", "", "no")
    accepted = review = total_p = 0

    returns = 0
    _flips = []                      # S194 ⭐3 — mode reclassifications this run
    for ln in lines:
        kind = ln.get("kind") or KIND_SALE
        low_conf = ln["confidence"] < min_conf
        anonymous = not ln["clinic_id"] and not ln["patient_name"]
        # OCR is never trusted to be "cleanly read but anonymous" -- an unreadable
        # scan looks exactly like an anonymous one, so those still go to review.
        structured = adapter != "sarvam_ocr"
        if low_conf or (anonymous and not (anon_to_walkin and structured)):
            # sale_item_review carries no non-negative constraint, so a return
            # is stored SIGNED here — that keeps v_day_attribution.in_review_p
            # honest without needing a service marker on a free-text queue.
            con.execute(
                "INSERT INTO sale_item_review (day_entry_id, ingest_batch_id, raw_text, "
                "guess_clinic_id, guess_name, amount_p, confidence, status, reason) "
                "VALUES (?,?,?,?,?,?,?, 'open', ?)",
                (eid, batch_id, ln.get("raw"), ln.get("clinic_id"), ln.get("patient_name"),
                 signed(ln["amount_p"], kind), ln["confidence"],
                 "low confidence" if ln["confidence"] < min_conf else "no patient identified"))
            review += 1
            continue
        pid = resolve_patient(con, ln.get("clinic_id"), ln.get("patient_name"))
        _new_mode = ln.get("mode")
        _homemed = is_home_medicine(ln.get("patient_name"))      # S194 ⭐2
        con.execute(
            "INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, service, "
            "description, amount_p, gross_p, disc_p, mode, home_med, source, source_ref, confidence) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, batch_id, unit, pid,
             service_for(unit, kind),
             ln.get("description"), ln["amount_p"], ln.get("gross_p"), ln.get("disc_p"), _new_mode, _homemed,
             "ocr" if adapter == "sarvam_ocr" else ("tracker" if adapter == "tracker" else "manual"),
             ln.get("bill_no"), ln["confidence"]))
        # S194 ⭐3 — a bill seen before with a different mode is a reclassification
        _sref = ln.get("bill_no")
        if _sref is not None and _sref in _prev_mode:
            _om = _prev_mode[_sref]
            if _om and _new_mode and _om != _new_mode:
                _flips.append((_sref, pid, ln["amount_p"], _om, _new_mode))
        accepted += 1
        if kind == KIND_RETURN:
            returns += 1
        total_p += signed(ln["amount_p"], kind)

    # S194 ⭐3 — persist any mode flips found on this re-import
    if _flips:
        _ensure_mode_change_log(con)
        for _sref, _pid, _amt, _om, _nm in _flips:
            con.execute(
                "INSERT INTO mode_change_log (unit, business_date, source_ref, "
                "patient_ref_id, amount_p, old_mode, new_mode, ingest_batch_id, changed_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (unit, business_date, _sref, _pid, _amt, _om, _nm, batch_id, now))

    if review and accepted:
        status = "partial"
    elif review and not accepted:
        status = "partial"
    con.execute("UPDATE ingest_batch SET rows_accepted=?, rows_review=?, total_p=?, status=? "
                "WHERE id=?", (accepted, review, total_p, status, batch_id))

    reconcile_day_attribution(con, unit, business_date, now)
    con.commit()
    return dict(ok=True, batch_id=batch_id, adapter=adapter, rows_read=len(lines),
                accepted=accepted, review=review, returns=returns,
                attributed_p=total_p, status=status)


def reconcile_day_attribution(con, unit, business_date, now=None):
    """Open (or close) the line_sum_vs_day_total exception for a day.

    Deliberately NOT a blocker: the day total is settled by the day figures and
    the bank statement. This only reports how far patient naming has got, and
    shouts when a material amount of a day's money has no name against it."""
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    row = con.execute("SELECT day_total_p, attributed_p, in_review_p, in_review_count "
                      "FROM v_day_attribution WHERE unit=? AND business_date=?",
                      (unit, business_date)).fetchone()
    if not row:
        return None
    day_total_p, attributed_p, in_review_p, in_review_n = row
    diff = day_total_p - attributed_p
    tol = int(_setting(con, "ingest.attribution_tolerance_p", "10000") or 10000)

    if abs(diff) > tol:
        con.execute(
            "INSERT OR REPLACE INTO recon_exception (unit, business_date, kind, expected_p, "
            "actual_p, diff_p, severity, status, detail, opened_at, shout_count) "
            "VALUES (?,?, 'line_sum_vs_day_total', ?,?,?, ?, 'open', ?, ?, "
            "COALESCE((SELECT shout_count FROM recon_exception WHERE unit=? AND business_date=? "
            "          AND kind='line_sum_vs_day_total'), 0))",
            (unit, business_date, day_total_p, attributed_p, diff,
             "medium",
             "%d/100 of the day is named; %s not attributed to any patient%s"
             % (int(100 * attributed_p / day_total_p) if day_total_p else 0,
                _r(diff), (" (%d line(s) in review)" % in_review_n) if in_review_n else ""),
             now, unit, business_date))
    else:
        con.execute("UPDATE recon_exception SET status='resolved', "
                    "resolution='lines reconcile to the day total', closed_at=? "
                    "WHERE unit=? AND business_date=? AND kind='line_sum_vs_day_total' "
                    "AND status='open'", (now, unit, business_date))
    return dict(day_total_p=day_total_p, attributed_p=attributed_p, diff_p=diff,
                in_review_p=in_review_p, in_review_count=in_review_n)


def _r(p):
    sign = "-" if p < 0 else ""
    p = abs(int(p))
    w, f = divmod(p, 100)
    s = str(w)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = head + "," + tail
    return "%sRs %s.%02d" % (sign, s, f)


# ----------------------------------------------------------------- selftest

def selftest(db_path="finance.db"):
    """Runs as an INSTALL GATE, so it must never touch the live store.
    ingest_day() commits internally by design, so a rollback at the end is NOT
    enough — the whole thing runs on a throwaway copy that is deleted after."""
    ok, fail = 0, []

    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fail.append(name)

    # clinic id splitting — the whole patient spine rests on this
    check("id before name", split_clinic_id("4471 Ramesh Kumar")[:2] == ("4471", "Ramesh Kumar"))
    check("id with dash", split_clinic_id("4471-Ramesh Kumar")[:2] == ("4471", "Ramesh Kumar"))
    check("id in brackets", split_clinic_id("Ramesh Kumar (4471)")[:2] == ("4471", "Ramesh Kumar"))
    check("prefixed id", split_clinic_id("AO4471 Sita Devi")[:2] == ("AO4471", "Sita Devi"))
    check("name only -> no id", split_clinic_id("Ramesh Kumar")[0] is None)
    check("id only -> no name", split_clinic_id("4471")[:2] == ("4471", None))
    check("blank is nothing", split_clinic_id("")[:2] == (None, None))

    # S180 — sale returns must survive the junk filter that used to eat them
    check("zero is still junk", classify_amount(0) == (None, None))
    check("no amount is still junk", classify_amount(None) == (None, None))
    check("a sale keeps its sign", classify_amount(115000) == (115000, KIND_SALE))
    check("a negative is a RETURN", classify_amount(-115000) == (115000, KIND_RETURN))
    check("return service medical", service_for("medical", KIND_RETURN) == "pharmacy_return")
    check("return service lab", service_for("lab", KIND_RETURN) == "lab_test_return")
    check("sale service unchanged", service_for("medical", KIND_SALE) == "pharmacy")
    check("signed sale", signed(115000, KIND_SALE) == 115000)
    check("signed return", signed(115000, KIND_RETURN) == -115000)

    check("paise plain", paise("1234") == 123400)
    check("paise decimal", paise("1234.50") == 123450)
    check("paise rupee sign", paise("₹ 1,234.50") == 123450)
    check("paise Rs prefix", paise("Rs 900") == 90000)
    check("paise bracket negative", paise("(250)") == -25000)
    check("paise rejects text", paise("N/A") is None)

    check("date dmy", parse_date("13/08/2026") == dt.date(2026, 8, 13))
    check("date iso", parse_date("2026-08-13") == dt.date(2026, 8, 13))
    check("date rejects year 26", parse_date("13/08/0026") is None)

    if not os.path.exists(db_path):
        print("INGEST %d/%d passed (db tests skipped)" % (ok, ok + len(fail)))
        return 0 if not fail else 1

    import shutil
    import tempfile
    live_db = db_path
    fd, tmp_db = tempfile.mkstemp(prefix="finance_ingest_smoke_", suffix=".db")
    os.close(fd)
    shutil.copyfile(live_db, tmp_db)

    con = sqlite3.connect(tmp_db)
    con.execute("PRAGMA foreign_keys=ON")
    date = con.execute("SELECT MAX(business_date) FROM day_entry WHERE unit='medical'").fetchone()[0]

    # configure a Marg-shaped export, purely as column mapping
    sid = con.execute("SELECT id FROM ingest_source WHERE unit='medical' AND adapter='marg_export'"
                      ).fetchone()[0]
    con.execute("UPDATE ingest_source SET active=1, config_json=? WHERE id=?",
                (json.dumps({"delimiter": ",", "date_format": "%d/%m/%Y"}), sid))
    for f, c, req in (("bill_no", "Bill No", 1), ("bill_date", "Bill Date", 0),
                      ("patient_name", "Customer", 1), ("amount", "Net Amt", 1),
                      ("description", "Particulars", 0)):
        con.execute("INSERT OR REPLACE INTO ingest_column_map (source_id, our_field, their_column, "
                    "transform, required) VALUES (?,?,?,?,?)",
                    (sid, f, c, "ddmmyyyy" if f == "bill_date" else None, req))
    con.commit()

    marg = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
            "H-9001,13/08/2026,4471 Ramesh Kumar,Tab Calcium,Rs 450.00\n"
            "H-9002,13/08/2026,Sunita Devi (5120),Knee cap,\"1,250.00\"\n"
            "H-9003,13/08/2026,Walk in customer,Bandage,120\n"
            "H-9004,13/08/2026,,,\n")
    res = ingest_day(con, "medical", date, "marg_export", marg, run_by="selftest",
                     source_ref="marg_test.csv")
    check("marg export ingests", res["ok"])
    check("blank row skipped", res["rows_read"] == 3)
    check("two identified lines accepted", res["accepted"] == 2)
    check("unidentified line goes to review", res["review"] == 1)
    check("attributed total right", res["attributed_p"] == 45000 + 125000)

    pr = {r[0]: r[1] for r in con.execute("SELECT clinic_id, name FROM patient_ref")}
    check("patient 4471 created", pr.get("4471") == "Ramesh Kumar")
    check("patient 5120 created", pr.get("5120") == "Sunita Devi")

    rec = reconcile_day_attribution(con, "medical", date)
    check("attribution reconciled", rec is not None and rec["attributed_p"] == 170000)
    n = con.execute("SELECT COUNT(*) FROM recon_exception WHERE unit='medical' AND "
                    "business_date=? AND kind='line_sum_vs_day_total' AND status='open'",
                    (date,)).fetchone()[0]
    check("unattributed remainder shouts", n == 1)

    # re-running supersedes rather than duplicating
    res2 = ingest_day(con, "medical", date, "marg_export", marg, run_by="selftest")
    tot = con.execute("SELECT COUNT(*) FROM sale_item WHERE day_entry_id=("
                      "SELECT id FROM day_entry WHERE unit='medical' AND business_date=?)",
                      (date,)).fetchone()[0]
    check("re-run supersedes, no duplicates", tot == 2)
    sup = con.execute("SELECT COUNT(*) FROM ingest_batch WHERE status='superseded'").fetchone()[0]
    check("old batch marked superseded", sup >= 1)

    # a missing required column must fail loudly, not silently produce nothing
    bad = "Invoice,Name,Total\nX-1,4471 Ramesh,100\n"
    res3 = ingest_day(con, "medical", date, "marg_export", bad, run_by="selftest")
    check("wrong format fails loudly", (not res3["ok"]) and "not found" in res3["error"])
    still = con.execute("SELECT COUNT(*) FROM sale_item WHERE day_entry_id=("
                        "SELECT id FROM day_entry WHERE unit='medical' AND business_date=?)",
                        (date,)).fetchone()[0]
    check("failed run does not destroy good lines", still == 2)

    # sarvam is honestly unavailable here rather than silently empty
    res4 = ingest_day(con, "medical", date, "sarvam_ocr", "x", run_by="selftest")
    check("sarvam reports unavailable", (not res4["ok"]) and res4["error"])

    # ------------------------------------------------------------------ S180
    # Sale returns. These run LAST on purpose: ingest_day supersedes the earlier
    # batch for a day and deletes what it produced, so anything asserted about
    # the previous batches has to have been asserted already.
    #
    # A Marg export carrying a credit note, written the way Marg writes one.
    # Before S180 the CN row was skipped outright and the day read as though no
    # refund had happened.
    marg_cn = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
               "A002966,13/08/2026,4471 Ramesh Kumar,Tab Calcium,1150.00\n"
               "CN00167,13/08/2026,4471 Ramesh Kumar,Tab Calcium returned,-400.00\n"
               "A002970,13/08/2026,Sunita Devi (5120),Knee cap,1000.00\n")
    resr = ingest_day(con, "medical", date, "marg_export", marg_cn, run_by="selftest",
                      source_ref="marg_returns.csv")
    check("credit note is read, not skipped", resr["rows_read"] == 3)
    check("credit note is accepted", resr["accepted"] == 3)
    check("credit note counted as a return", resr["returns"] == 1)
    check("return nets out of the attributed total",
          resr["attributed_p"] == 115000 - 40000 + 100000)

    kinds = {r[0]: r[1] for r in con.execute(
        "SELECT source_ref, service FROM sale_item WHERE ingest_batch_id=?", (resr["batch_id"],))}
    check("return row marked pharmacy_return", kinds.get("CN00167") == "pharmacy_return")
    check("sale rows unchanged", kinds.get("A002966") == "pharmacy")

    stored = con.execute("SELECT amount_p FROM sale_item WHERE source_ref='CN00167'").fetchone()[0]
    check("return stored as a positive magnitude", stored == 40000)

    view_p = con.execute("SELECT attributed_p FROM v_day_attribution WHERE unit='medical' "
                         "AND business_date=?", (date,)).fetchone()[0]
    check("the VIEW nets the return too (migration applied)",
          view_p == 115000 - 40000 + 100000)

    # a return nobody could put a name to still reaches the queue, signed
    marg_anon = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
                 "CN00168,13/08/2026,,Returned,-77.00\n")
    resa = ingest_day(con, "medical", date, "marg_export", marg_anon, run_by="selftest")
    check("unidentified return is not silently dropped", resa["rows_read"] == 1)
    check("unidentified return goes to review", resa["review"] == 1)
    rv = con.execute("SELECT amount_p FROM sale_item_review WHERE ingest_batch_id=?",
                     (resa["batch_id"],)).fetchone()[0]
    check("review keeps the return signed", rv == -7700)

    con.close()
    try:
        os.remove(tmp_db)
    except OSError:
        pass
    print("INGEST %d/%d passed  (throwaway copy; %s untouched)"
          % (ok, ok + len(fail), os.path.basename(live_db)))
    for f in fail:
        print("  FAIL:", f)
    return 0 if not fail else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest(sys.argv[1] if len(sys.argv) > 1 else "finance.db"))
