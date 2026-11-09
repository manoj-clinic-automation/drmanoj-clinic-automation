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
        # S221 F-283: the export's own mobile and last-four columns travel with
        # the line so the D355 ladder can run. Read straight off the header, as
        # gross/disc already are -- no column-map row to add. THE FULL NUMBER IS
        # STRIPPED from the stored raw: it is used in memory and discarded
        # (finance_patient_match's rule, and F-185's).
        _mob = (row.get(norm.get("mobile")) if norm.get("mobile") else None) or ""
        _l4 = (row.get(norm.get("phone_last4")) if norm.get("phone_last4") else None) or ""
        _raw_row = {k: v for k, v in row.items()
                    if (k or "").strip().lower() != "mobile"}
        out.append(dict(bill_no=(get("bill_no") or "").strip() or None,
                        bill_date=get("bill_date"),
                        clinic_id=cid, patient_name=name,
                        mobile=str(_mob).strip() or None,
                        phone_last4=str(_l4).strip() or None,
                        description=(get("description") or "").strip() or None,
                        amount_p=amount, kind=kind,
                        gross_p=(abs(_grp) if _grp is not None else None),
                        disc_p=(abs(_dsp) if _dsp is not None else None),
                        mode=(get("mode") or "").strip().lower() or None,
                        confidence=conf,
                        raw=json.dumps(_raw_row, ensure_ascii=False)[:2000]))
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


# ---- S220 F-277: the ingest name-check ------------------------------------
# A wrong clinic ID used to attach a STRANGER silently (3 of 43 August returns).
# Attachment stays BY ID ONLY and the money is untouched; what changes is that
# the bill's name is now compared with the master's, and a disagreement is
# RECORDED as an identity_dispute -- a question for a person, never a verdict
# about money. See the S220 design brief and the kit README.
import difflib

_NAME_HONORIFICS = frozenset((
    "smt", "shri", "sri", "shree", "mr", "mrs", "ms", "miss", "dr", "km",
    "kumari", "md", "mohd", "mohammad", "master", "baby", "late", "abl", "w/o",
    "s/o", "d/o", "wo", "so", "do", "and"))


def _name_tokens(s):
    """Lower-case letter tokens, honorifics dropped, digits and punctuation gone
    (a Marg party string can carry a mobile number or an ID beside the name)."""
    import re as _re
    s = _re.sub(r"[^a-z ]+", " ", (s or "").lower())
    return [t for t in s.split() if t and t not in _NAME_HONORIFICS]


def _token_close(x, y):
    """Two name tokens that are the same word, allowing for the ways this
    master actually mis-spells: a dropped vowel (Archna/Archana), a swapped
    pair (Parsad/Prasad, Vivha/Vivah), one letter in a short word (Kour/Kaur),
    or one being the start of the other (Ram/Ramesh is NOT close: 4+ letters)."""
    if x == y:
        return True
    if len(x) >= 4 and len(y) >= 4 and (x.startswith(y) or y.startswith(x)):
        return True
    if difflib.SequenceMatcher(None, x, y).ratio() >= 0.8:
        return True
    if len(x) == len(y):
        diff = [i for i in range(len(x)) if x[i] != y[i]]
        if len(diff) == 1 and len(x) <= 5:
            return True                                  # Kour / Kaur
        if len(diff) == 2 and diff[1] == diff[0] + 1 and \
                x[diff[0]] == y[diff[1]] and x[diff[1]] == y[diff[0]]:
            return True                                  # Parsad / Prasad
    return False


def name_agrees(bill_name, master_name):
    """'yes' when every token of the shorter name has a close token in the
    other (ASHOK AGARWAL is Ashok Kumar Agarwal); 'no' when it does not;
    'unknown' when either side has nothing to compare (blank, or only an
    honorific). Calibrated on returns_docterz_match_Aug2026.csv: 33 agree,
    4 differ, 1 unknown -- the sheet's own verdicts, reproduced."""
    a, b = _name_tokens(bill_name), _name_tokens(master_name)
    if not a or not b:
        return "unknown"
    if a == b:
        return "yes"
    short, longer = (a, b) if len(a) <= len(b) else (b, a)
    if all(any(_token_close(t, u) for u in longer) for t in short):
        return "yes"
    return "no"


def resolve_patient_checked(con, clinic_id, name):
    """resolve_patient(), plus the answer it never gave: does the bill's name
    agree with the master's name for that ID? Returns (pid, agree, master_name)
    with agree in ('yes', 'no', 'unknown'). Attachment is unchanged."""
    master = None
    if clinic_id:
        r = con.execute("SELECT name FROM patient_ref WHERE clinic_id=?",
                        (clinic_id,)).fetchone()
        if r:
            master = r[0]
            pid = resolve_patient(con, clinic_id, name)
            return pid, name_agrees(name, master), master
    pid = resolve_patient(con, clinic_id, name)
    return pid, "unknown", master


def _note_identity_dispute(con, unit, business_date, bill_no, clinic_id,
                           bill_name, master_name, pid, agree, kind, now):
    """Record a disagreement; close an earlier one the re-export has settled.
    Fail-soft: a database that cannot take the note leaves the ingest exactly
    as it was before S220 -- the money path never depends on this."""
    try:
        con.execute(
            "CREATE TABLE IF NOT EXISTS identity_dispute ("
            " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
            " bill_no TEXT, clinic_id TEXT NOT NULL, bill_name TEXT, master_name TEXT,"
            " patient_ref_id INTEGER, kind TEXT NOT NULL DEFAULT 'sale',"
            " status TEXT NOT NULL DEFAULT 'open', noted_at TEXT NOT NULL,"
            " resolved_by TEXT, resolved_at TEXT, resolution TEXT,"
            " UNIQUE(unit, business_date, bill_no, clinic_id))")
        if agree == "no":
            con.execute(
                "INSERT OR IGNORE INTO identity_dispute (unit, business_date, bill_no,"
                " clinic_id, bill_name, master_name, patient_ref_id, kind, status, noted_at)"
                " VALUES (?,?,?,?,?,?,?,?, 'open', ?)",
                (unit, business_date, bill_no, clinic_id, bill_name, master_name,
                 pid, kind, now))
        elif agree == "yes" and clinic_id:
            con.execute(
                "UPDATE identity_dispute SET status='resolved', resolved_by='ingest',"
                " resolved_at=?, resolution='a later export of this bill agrees with the master'"
                " WHERE unit=? AND business_date=? AND bill_no=? AND clinic_id=? AND status='open'",
                (now, unit, business_date, bill_no, clinic_id))
    except Exception:
        pass
# ---- end S220 F-277 ---------------------------------------------------------


# ---- S221 F-283: THE D355 LADDER AT INGEST ----------------------------------
# The owner's order: clinic ID - full mobile - name, then the SAME-DAY Docterz
# visit list. Read-only, fail-soft in every branch, and it writes no money: it
# returns the clinic ID the bill was missing, and the ordinary accept path does
# the rest. Nobody is asked a question (the owner's ruling), but every rung is
# recorded, so no attachment is silent.

_LADDER_CONF = {"clinic id": 0.95, "mobile": 0.95,
                "last-4 + name": 0.85, "same-day visit": 0.75}


def _ladder_master(con, cid):
    r = con.execute("SELECT clinic_id, name FROM patient_ref WHERE clinic_id=?",
                    (cid,)).fetchone()
    return (r[0], r[1]) if r else (None, None)


def _ladder_by_mobile(con, M, mobile, name):
    """Rung 2 -- the full mobile. Fingerprinted in memory against
    patient_ref.mobile_fp and thrown away; the number itself is never stored.
    No salt means no fingerprint, and no fingerprint means NO GUESS."""
    ten = M.normalise_mobile(mobile)
    if not ten:
        return None, None
    fp = M.fingerprint(ten, M.salt())
    if not fp:
        return None, None
    hits = con.execute("SELECT clinic_id, name FROM patient_ref WHERE mobile_fp=?",
                       (fp,)).fetchall()
    if len(hits) == 1:
        if name and not M.names_agree(name, hits[0][1]):
            return None, None                 # the number fits, the name does not
        return hits[0][0], hits[0][1]
    if len(hits) > 1 and name:
        # a family number. The GIVEN name can separate relatives; the surname
        # they share cannot. Exactly one, or no answer.
        strict = [h for h in hits if M.given_name_agrees(name, h[1])]
        loose = [h for h in hits if M.names_agree(name, h[1])]
        narrowed = strict if len(strict) == 1 else loose
        if len(narrowed) == 1:
            return narrowed[0][0], narrowed[0][1]
    return None, None


def _ladder_by_last4(con, M, last4, name):
    """Rung 3 -- the last four plus the name. NEVER the last four alone: 1,871
    last-four values in this master belong to more than one patient, so on its
    own it identifies nobody.

    This reproduces finance_patient_match.match_bill()'s own last-four rung
    rather than calling it, for one measured reason: match_bill() reads its
    rows by column NAME, so it raises TypeError on a connection that has no
    sqlite3.Row factory -- and the ingest's connection is not guaranteed to
    have one. Calling it would have failed soft and silently, and this rung
    would simply never have worked in production. The walk cross-checks this
    function against match_bill() on real master rows, so the two cannot drift.
    """
    last4 = (last4 or "").strip()
    if not (last4 and name):
        return None, None
    hits = con.execute("SELECT clinic_id, name FROM patient_ref WHERE phone_last4=?",
                       (last4,)).fetchall()
    fit = [h for h in hits if M.names_agree(name, h[1])]
    strict = [h for h in fit if M.given_name_agrees(name, h[1])]
    chosen = strict if len(strict) == 1 else fit
    if len(chosen) == 1:
        return chosen[0][0], chosen[0][1]
    return None, None


def _ladder_same_day_visit(con, M, business_date, name):
    """Rung 4 -- the day's Docterz visit list, THE SAME DAY ONLY (measured,
    S221). A median of 24 patients. On a Sunday the list is empty by design --
    OPD closed, pharmacy open -- and this rung simply gives no answer."""
    if not (business_date and name):
        return None, None
    try:
        vis = con.execute(
            "SELECT DISTINCT p.clinic_id, p.name FROM patient_visit v "
            "JOIN patient_ref p ON p.clinic_id = v.clinic_id WHERE v.visit_date=?",
            (business_date,)).fetchall()
    except Exception:
        return None, None
    fit = [v for v in vis if M.names_agree(name, v[1])]
    strict = [v for v in fit if M.given_name_agrees(name, v[1])]
    chosen = strict if len(strict) == 1 else fit
    if len(chosen) == 1:
        return chosen[0][0], chosen[0][1]
    return None, None


def ladder_lookup(con, ln, business_date):
    """Return (clinic_id, master_name, rung), or (None, None, None) for no
    answer. READ-ONLY. Any failure at all is no answer, and the caller parks
    the line exactly as it did before this kit existed."""
    try:
        import finance_patient_match as M
    except Exception:
        return None, None, None
    try:
        name = (ln.get("patient_name") or "").strip()
        cid = (ln.get("clinic_id") or "").strip()

        # rung 1 -- the clinic ID, when the bill carries one at all
        if cid:
            mcid, mname = _ladder_master(con, cid)
            if mcid and (not name or M.names_agree(name, mname)):
                return mcid, mname, "clinic id"

        # rung 2 -- the full mobile
        mcid, mname = _ladder_by_mobile(con, M, ln.get("mobile"), name)
        if mcid:
            return mcid, mname, "mobile"

        # rung 3 -- last four + name (D355's own rung, reproduced; see above)
        mcid, mname = _ladder_by_last4(con, M, ln.get("phone_last4"), name)
        if mcid:
            return mcid, mname, "last-4 + name"

        # rung 4 -- the same-day Docterz visit list
        mcid, mname = _ladder_same_day_visit(con, M, business_date, name)
        if mcid:
            return mcid, mname, "same-day visit"
    except Exception:
        return None, None, None
    return None, None, None


def _ensure_resolution_store(con):
    """The table, and the one view the owner asked to be baked in: how well the
    counter's own typing identified the day. It becomes a per-person number
    when Marg's user-wise register reaches the router (S221 star-1-3); until
    then it is per day, which is still the discipline signal."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS identity_resolution ("
        " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
        " bill_no TEXT, rung TEXT NOT NULL, clinic_id TEXT, bill_name TEXT,"
        " master_name TEXT, noted_at TEXT NOT NULL,"
        " UNIQUE(unit, business_date, bill_no))")
    con.execute(
        "CREATE VIEW IF NOT EXISTS v_entry_discipline AS "
        "SELECT d.business_date AS business_date, d.unit AS unit, "
        " COUNT(*) AS bills, "
        " SUM(CASE WHEN r.rung IS NULL THEN 1 ELSE 0 END) AS keyed_clean, "
        " SUM(CASE WHEN r.rung IS NOT NULL THEN 1 ELSE 0 END) AS named_by_ladder, "
        " SUM(CASE WHEN r.rung='mobile' THEN 1 ELSE 0 END) AS by_mobile, "
        " SUM(CASE WHEN r.rung='last-4 + name' THEN 1 ELSE 0 END) AS by_last4, "
        " SUM(CASE WHEN r.rung='same-day visit' THEN 1 ELSE 0 END) AS by_visit, "
        " (SELECT COUNT(*) FROM sale_item_review v JOIN day_entry vd ON vd.id=v.day_entry_id "
        "   WHERE vd.business_date=d.business_date AND vd.unit=d.unit AND v.status='open') "
        "   AS still_parked "
        "FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
        "LEFT JOIN identity_resolution r ON r.unit=d.unit "
        "  AND r.business_date=d.business_date AND r.bill_no=s.source_ref "
        "GROUP BY d.business_date, d.unit")


def _note_identity_resolution(con, unit, business_date, bill_no, rung,
                              clinic_id, bill_name, master_name, now):
    """Record WHICH rung named this bill. Fail-soft: a database that cannot
    take the note leaves the ingest exactly as it was."""
    try:
        _ensure_resolution_store(con)
        con.execute(
            "INSERT INTO identity_resolution (unit, business_date, bill_no, rung,"
            " clinic_id, bill_name, master_name, noted_at) VALUES (?,?,?,?,?,?,?,?)"
            " ON CONFLICT(unit, business_date, bill_no) DO UPDATE SET"
            " rung=excluded.rung, clinic_id=excluded.clinic_id,"
            " bill_name=excluded.bill_name, master_name=excluded.master_name,"
            " noted_at=excluded.noted_at",
            (unit, business_date, bill_no, rung, clinic_id, bill_name,
             master_name, now))
    except Exception:
        pass
# ---- end S221 F-283 ---------------------------------------------------------


def ingest_day(con, unit, business_date, adapter, payload, run_by="system",
               source_ref=None, now=None, commit=True):
    """Run one adapter over one day. Returns a summary dict.
    Re-running supersedes the previous batch for that day rather than duplicating.
    S474 (F-716): commit=False leaves the day's writes open for the caller to commit -- or roll back -- as one."""
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
    laddered = 0                     # S221 F-283 -- named by the D355 ladder

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
            # S221 F-283: THE LOOKUP RUNS BEFORE THE PARKING, NOT AFTER IT.
            # If the ladder names the patient, the line is given the clinic ID
            # it was missing and falls through to the ordinary accept path
            # below -- so resolve_patient_checked() and the S220 name-check
            # still run on it, and the money path is unchanged. No answer, and
            # the line parks exactly as it did before.
            _lcid, _lname, _lrung = ladder_lookup(con, ln, business_date)
            if _lcid:
                ln["clinic_id"] = _lcid
                ln["confidence"] = _LADDER_CONF.get(_lrung, 0.75)
                _note_identity_resolution(con, unit, business_date,
                                          ln.get("bill_no"), _lrung, _lcid,
                                          ln.get("patient_name"), _lname, now)
                laddered += 1
            else:
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
        # S220 F-277: attach by ID exactly as before; ALSO compare the name and
        # record a disagreement as a question. The money path is unchanged.
        pid, _agree, _master = resolve_patient_checked(
            con, ln.get("clinic_id"), ln.get("patient_name"))
        _note_identity_dispute(con, unit, business_date, ln.get("bill_no"),
                               ln.get("clinic_id"), ln.get("patient_name"),
                               _master, pid, _agree, kind, now)
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
    # S672 (F-1037): a pharmacy day's home / procedure medicine bills are deducted HERE, in this transaction, not
    # half an hour later by day_resync -- an approval in between left A004474 (27-Oct) undeducted for good.
    # Fail-soft: anything wrong is rolled back to the savepoint and the ingest stands exactly as before.
    # S758 (AF-37, the 09-Nov audit): the failure is no longer silent -- the day carries an open exception and the journal a line (v1).
    try:
        con.execute("SAVEPOINT s672_noncash")
        try:
            import day_resync as _dr672                                   # noqa: PLC0415
            _dr672.at_ingest(con, unit, business_date)
            con.execute("RELEASE SAVEPOINT s672_noncash")
            _s758_noncash_mark(con, unit, business_date, None)
        except Exception as _ex672:                                       # noqa: BLE001
            con.execute("ROLLBACK TO SAVEPOINT s672_noncash")
            con.execute("RELEASE SAVEPOINT s672_noncash")
            _s758_noncash_mark(con, unit, business_date, _ex672)
    except Exception as _ex672b:                                          # noqa: BLE001
        _s758_noncash_mark(con, unit, business_date, _ex672b)
    if commit:
        con.commit()
    return dict(ok=True, batch_id=batch_id, adapter=adapter, rows_read=len(lines),
                accepted=accepted, review=review, returns=returns,
                laddered=laddered,                        # S221 F-283
                attributed_p=total_p, status=status)


S758_KIND = "noncash_at_ingest"


def _s758_noncash_mark(con, unit, business_date, ex):
    """S758 (AF-37): the S672 deduction at ingest failed (ex) or ran (None). A failure opens a HIGH recon_exception on the day,
    where the approver and the console look, and writes one journal line; a later good ingest of the day resolves it. Never
    raises -- the ingest stands exactly as before whatever happens here."""
    import sys as _sys                                                    # noqa: PLC0415
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    try:
        if ex is None:
            con.execute("UPDATE recon_exception SET status='resolved', resolution='the deduction ran at a later ingest', "
                        "closed_at=? WHERE unit=? AND business_date=? AND kind=? AND status='open'",
                        (now, unit, business_date, S758_KIND))
            return
        what = "%s: %s" % (type(ex).__name__, str(ex)[:160])
        print("S758 noncash-at-ingest FAILED unit=%s day=%s -- %s" % (unit, business_date, what), file=_sys.stderr, flush=True)
        con.execute(
            "INSERT INTO recon_exception (unit, business_date, kind, severity, status, detail, opened_at) "
            "VALUES (?,?,?, 'high', 'open', ?, ?) ON CONFLICT(unit, business_date, kind) DO UPDATE SET severity='high', "
            "status='open', detail=excluded.detail, opened_at=excluded.opened_at, resolution=NULL, closed_at=NULL",
            (unit, business_date, S758_KIND,
             "The home / procedure medicine bills were NOT deducted at ingest (%s). The 30-minute re-try works only while the "
             "day is NOT approved -- do not approve this day until this clears (S758, F-1037)." % what, now))
    except Exception as _e:                                               # noqa: BLE001
        try:
            print("S758 noncash-at-ingest: could not record (%s)" % type(_e).__name__, file=_sys.stderr, flush=True)
        except Exception:                                                 # noqa: BLE001
            pass


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
# S686 / F-1051 -- the selftest is a REPORT, never a crash. Before S686 one
# check that found no row (fetchone() is None) raised a TypeError: the run
# stopped half way, printed no score, and skipped its clean-up, so every failed
# run left its throwaway copy of finance.db (patients) in the temp folder.
# Now: every lookup that can find nothing is a failed check; any other error in
# the database part is ONE failed check named with the error; the copy is
# removed in a finally, whatever happens.

def _one(con, sql, args=()):
    """The first column of the first row, or None when there is no row."""
    r = con.execute(sql, args).fetchone()
    return r[0] if r else None


def _selftest_db(con, check):
    """The checks that need a database. `con` is a THROWAWAY copy."""
    date = _one(con, "SELECT MAX(business_date) FROM day_entry WHERE unit='medical'")
    check("the copy has a medical day to test on", date is not None)
    sid = _one(con, "SELECT id FROM ingest_source WHERE unit='medical' AND adapter='marg_export'")
    check("the copy has the medical marg_export source", sid is not None)
    # The made-up patients carry IDs the clinic never issues (ZZ..., S686), checked
    # unused below, so "created" can pass on any copy of the store.
    taken = _one(con, "SELECT COUNT(*) FROM patient_ref WHERE clinic_id IN ('ZZ9471','ZZ5120')")
    check("the made-up clinic IDs are unused in the copy", taken == 0)
    if date is None or sid is None:
        return

    # configure a Marg-shaped export, purely as column mapping
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
            "H-9001,13/08/2026,ZZ9471 Ramesh Kumar,Tab Calcium,Rs 450.00\n"
            "H-9002,13/08/2026,Sunita Devi (ZZ5120),Knee cap,\"1,250.00\"\n"
            "H-9003,13/08/2026,Walk in customer,Bandage,120\n"
            "H-9004,13/08/2026,,,\n")
    res = ingest_day(con, "medical", date, "marg_export", marg, run_by="selftest",
                     source_ref="marg_test.csv")
    check("marg export ingests", res["ok"])
    check("blank row skipped", res.get("rows_read") == 3)
    check("two identified lines accepted", res.get("accepted") == 2)
    check("unidentified line goes to review", res.get("review") == 1)
    check("attributed total right", res.get("attributed_p") == 45000 + 125000)

    pr = {r[0]: r[1] for r in con.execute("SELECT clinic_id, name FROM patient_ref")}
    check("patient ZZ9471 created", pr.get("ZZ9471") == "Ramesh Kumar")
    check("patient ZZ5120 created", pr.get("ZZ5120") == "Sunita Devi")

    rec = reconcile_day_attribution(con, "medical", date)
    check("attribution reconciled", rec is not None and rec["attributed_p"] == 170000)
    n = _one(con, "SELECT COUNT(*) FROM recon_exception WHERE unit='medical' AND "
                  "business_date=? AND kind='line_sum_vs_day_total' AND status='open'", (date,))
    check("unattributed remainder shouts", n == 1)

    # re-running supersedes rather than duplicating
    ingest_day(con, "medical", date, "marg_export", marg, run_by="selftest")
    tot = _one(con, "SELECT COUNT(*) FROM sale_item WHERE day_entry_id=("
                    "SELECT id FROM day_entry WHERE unit='medical' AND business_date=?)", (date,))
    check("re-run supersedes, no duplicates", tot == 2)
    sup = _one(con, "SELECT COUNT(*) FROM ingest_batch WHERE status='superseded'")
    check("old batch marked superseded", (sup or 0) >= 1)

    # a missing required column must fail loudly, not silently produce nothing
    bad = "Invoice,Name,Total\nX-1,4471 Ramesh,100\n"
    res3 = ingest_day(con, "medical", date, "marg_export", bad, run_by="selftest")
    check("wrong format fails loudly", (not res3["ok"]) and "not found" in (res3.get("error") or ""))
    still = _one(con, "SELECT COUNT(*) FROM sale_item WHERE day_entry_id=("
                      "SELECT id FROM day_entry WHERE unit='medical' AND business_date=?)", (date,))
    check("failed run does not destroy good lines", still == 2)

    # sarvam is honestly unavailable here rather than silently empty
    res4 = ingest_day(con, "medical", date, "sarvam_ocr", "x", run_by="selftest")
    check("sarvam reports unavailable", (not res4["ok"]) and res4.get("error"))

    # ------------------------------------------------------------------ S180
    # Sale returns. These run LAST on purpose: ingest_day supersedes the earlier
    # batch for a day and deletes what it produced, so anything asserted about
    # the previous batches has to have been asserted already.
    #
    # A Marg export carrying a credit note, written the way Marg writes one.
    # Before S180 the CN row was skipped outright and the day read as though no
    # refund had happened.
    marg_cn = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
               "A002966,13/08/2026,ZZ9471 Ramesh Kumar,Tab Calcium,1150.00\n"
               "CN00167,13/08/2026,ZZ9471 Ramesh Kumar,Tab Calcium returned,-400.00\n"
               "A002970,13/08/2026,Sunita Devi (ZZ5120),Knee cap,1000.00\n")
    resr = ingest_day(con, "medical", date, "marg_export", marg_cn, run_by="selftest",
                      source_ref="marg_returns.csv")
    check("credit note is read, not skipped", resr.get("rows_read") == 3)
    check("credit note is accepted", resr.get("accepted") == 3)
    check("credit note counted as a return", resr.get("returns") == 1)
    check("return nets out of the attributed total",
          resr.get("attributed_p") == 115000 - 40000 + 100000)

    kinds = {r[0]: r[1] for r in con.execute(
        "SELECT source_ref, service FROM sale_item WHERE ingest_batch_id=?", (resr.get("batch_id"),))}
    check("return row marked pharmacy_return", kinds.get("CN00167") == "pharmacy_return")
    check("sale rows unchanged", kinds.get("A002966") == "pharmacy")

    stored = _one(con, "SELECT amount_p FROM sale_item WHERE source_ref='CN00167' "
                       "AND ingest_batch_id=?", (resr.get("batch_id"),))
    check("return stored as a positive magnitude", stored == 40000)

    view_p = _one(con, "SELECT attributed_p FROM v_day_attribution WHERE unit='medical' "
                       "AND business_date=?", (date,))
    check("the VIEW nets the return too (migration applied)",
          view_p == 115000 - 40000 + 100000)

    # S686 / F-1051 -- a return nobody could put a name to. WHERE it goes is the
    # owner's setting ingest.anonymous_to_walkin (S186 / F-114; unset = on), so
    # the test runs it BOTH ways on this throwaway copy, whatever the live
    # store says, and puts the copy's setting back after.
    marg_anon = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
                 "CN00168,13/08/2026,,Returned,-77.00\n")
    key = "ingest.anonymous_to_walkin"
    saved = _setting(con, key, None)

    def _anon_run(flag):
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", (key, flag))
        con.commit()
        return ingest_day(con, "medical", date, "marg_export", marg_anon, run_by="selftest",
                          source_ref="marg_anon_%s.csv" % flag)

    # ON -- as the live store runs it: accepted onto WALK-IN, as a return
    resa = _anon_run("1")
    check("unidentified return is not silently dropped", resa.get("rows_read") == 1)
    check("setting on: an unidentified return is accepted, not parked",
          resa.get("accepted") == 1 and resa.get("review") == 0)
    check("setting on: it is counted as a return", resa.get("returns") == 1)
    row = con.execute("SELECT s.service, s.amount_p, p.clinic_id FROM sale_item s "
                      "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
                      "WHERE s.ingest_batch_id=?", (resa.get("batch_id"),)).fetchone()
    check("setting on: it lands on WALK-IN as a pharmacy_return of 77.00",
          row is not None and tuple(row) == ("pharmacy_return", 7700, WALK_IN))

    # OFF -- parked for a human, the return kept signed
    resb = _anon_run("0")
    check("setting off: an unidentified return goes to review",
          resb.get("review") == 1 and resb.get("accepted") == 0)
    rv = _one(con, "SELECT amount_p FROM sale_item_review WHERE ingest_batch_id=?",
              (resb.get("batch_id"),))
    check("setting off: review keeps the return signed", rv == -7700)

    if saved is None:
        con.execute("DELETE FROM setting WHERE key=?", (key,))
    else:
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?, ?)", (key, saved))
    con.commit()


def selftest(db_path="finance.db"):
    """Runs as an INSTALL GATE, so it must never touch the live store.
    ingest_day() commits internally by design, so a rollback at the end is NOT
    enough -- the whole thing runs on a throwaway copy that is deleted after,
    in a finally (S686 / F-1051)."""
    ok, fail = 0, []

    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fail.append(name)

    # clinic id splitting -- the whole patient spine rests on this
    check("id before name", split_clinic_id("4471 Ramesh Kumar")[:2] == ("4471", "Ramesh Kumar"))
    check("id with dash", split_clinic_id("4471-Ramesh Kumar")[:2] == ("4471", "Ramesh Kumar"))
    check("id in brackets", split_clinic_id("Ramesh Kumar (4471)")[:2] == ("4471", "Ramesh Kumar"))
    check("prefixed id", split_clinic_id("AO4471 Sita Devi")[:2] == ("AO4471", "Sita Devi"))
    check("name only -> no id", split_clinic_id("Ramesh Kumar")[0] is None)
    check("id only -> no name", split_clinic_id("4471")[:2] == ("4471", None))
    check("blank is nothing", split_clinic_id("")[:2] == (None, None))

    # S180 -- sale returns must survive the junk filter that used to eat them
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
        for f in fail:
            print("  FAIL:", f)
        return 0 if not fail else 1

    import shutil
    import tempfile
    live_db = db_path
    fd, tmp_db = tempfile.mkstemp(prefix="finance_ingest_smoke_", suffix=".db")
    os.close(fd)
    con = None
    try:
        shutil.copyfile(live_db, tmp_db)
        con = sqlite3.connect(tmp_db)
        con.execute("PRAGMA foreign_keys=ON")
        _selftest_db(con, check)
    except Exception as ex:                                        # noqa: BLE001
        fail.append("the database checks stopped: %s: %s" % (type(ex).__name__, ex))
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:                                      # noqa: BLE001
                pass
        for p in (tmp_db, tmp_db + "-journal", tmp_db + "-wal", tmp_db + "-shm"):
            try:
                os.remove(p)
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
