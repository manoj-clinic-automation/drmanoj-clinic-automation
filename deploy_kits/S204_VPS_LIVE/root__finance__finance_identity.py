#!/usr/bin/python3
"""
finance_identity.py  ·  Session 180 · item U11
Put a name to the pharmacy lines that arrived without a clinic ID.

THE PROBLEM, MEASURED
    Of 147 real Marg bills: 77% carried a clinic ID, 71% a phone, 82% one or the
    other. The rest carried only a name. Those land on WALK-IN, so roughly one
    bill in five never reaches a patient's history — and a return with no
    matching sale cannot be checked at all.

THE ROSTER IS ALREADY HERE
    Every bill that DID carry a clinic ID has already written that ID and name
    into patient_ref. So the system's own accumulated patient list — 121 days of
    it — is the roster to match names against. No external file, no transport,
    no new dependency.

    (The follow-up tracker's consultation report would be a richer roster, but
    it lives on the clinic PC in data/consultation_report_YYYY-MM-DD.csv and is
    not on this box. That is a transport problem, deliberately not solved here.)

IT PROPOSES. IT NEVER ASSIGNS.
    A name match is a probability, and this queue feeds a discount and return
    audit where a wrong match names the wrong patient, the wrong day and the
    wrong person behind the counter. So this module writes nothing to sale_item
    and resolves nothing. It produces a ranked suggestion with its reasoning,
    and a human presses the button — the existing
    /finance/api/review/<id>/resolve route, unchanged.

GRADES
    unique_exact     one patient in the roster has exactly this name
    corroborated     unique_exact, AND the last four phone digits agree,
                     or a medicine on this bill was bought by them before
    ambiguous        two or more patients share the name — REFUSED, not guessed
    near             one character out from exactly one name; proposal only
    none             nothing worth showing

    Only `corroborated` and `unique_exact` are worth a checker's default click.
    `near` is shown with its distance so the human can see what it is guessing.
    `ambiguous` deliberately offers no default — that is the whole point of it.

Money is INTEGER PAISE. Stdlib only.
"""

import json
import re
import sqlite3

WALK_IN = "WALK-IN"

G_CORROBORATED = "corroborated"
G_UNIQUE = "unique_exact"
G_AMBIGUOUS = "ambiguous"
G_NEAR = "near"
G_NONE = "none"

# Only these are safe to offer as a default click.
CONFIDENT = (G_CORROBORATED, G_UNIQUE)

RE_BILL = re.compile(r"\b((?:A|CN)\d{4,})\b")


# --------------------------------------------------------------------------- #

def norm_name(s):
    """Upper, punctuation out, spaces collapsed. Nothing cleverer — a fuzzy
    normaliser is a fuzzy match wearing a disguise."""
    t = re.sub(r"[^A-Z ]+", " ", str(s or "").upper())
    return re.sub(r"\s+", " ", t).strip()


def edit_distance_le1(a, b):
    """True if a and b are at most one edit apart. Bounded on purpose: this is
    used to SHOW a human a near-miss, never to decide anything."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


def _bill_no(raw_text, guess=None):
    for src in (guess, raw_text):
        m = RE_BILL.search(str(src or ""))
        if m:
            return m.group(1)
    return None


def _phone_last4(raw_text):
    """The ingest raw is the CSV row as JSON; the reader writes phone_last4."""
    try:
        d = json.loads(raw_text or "{}")
    except (TypeError, ValueError):
        return None
    for k, v in (d.items() if isinstance(d, dict) else []):
        if "last4" in str(k).lower():
            s = re.sub(r"\D", "", str(v or ""))
            return s[-4:] if len(s) == 4 else None
    return None


# --------------------------------------------------------------------------- #

def roster(con):
    """(normalised name) -> [ {clinic_id, name, phone_last4, id} ] from patient_ref.

    WALK-IN and merged-away rows are excluded: neither is a person to assign to."""
    out = {}
    for r in con.execute("SELECT id, clinic_id, name, phone_last4 FROM patient_ref "
                         "WHERE merged_into IS NULL AND clinic_id <> ? AND name IS NOT NULL",
                         (WALK_IN,)):
        n = norm_name(r[2])
        if n:
            out.setdefault(n, []).append(
                dict(id=r[0], clinic_id=r[1], name=r[2], phone_last4=r[3]))
    return out


def _bought_before(con, unit, patient_ref_id, bill_no):
    """Did this patient previously buy anything that is on this bill?
    Requires drug lines on both sides (U3's sale_line_item); returns [] if not."""
    if not bill_no:
        return []
    keys = {r[0] for r in con.execute(
        "SELECT item_key FROM sale_line_item WHERE unit=? AND bill_no=?", (unit, bill_no))}
    if not keys:
        return []
    theirs = {r[0] for r in con.execute(
        "SELECT DISTINCT sli.item_key FROM sale_line_item sli "
        "JOIN sale_item si ON si.source_ref = sli.bill_no AND si.unit = sli.unit "
        "WHERE sli.unit=? AND si.patient_ref_id=? AND sli.bill_no <> ?",
        (unit, patient_ref_id, bill_no))}
    return sorted(keys & theirs)


def propose(con, unit, name, raw_text=None, guess_clinic_id=None, _roster=None):
    """One suggestion for one unidentified line. Writes nothing."""
    out = dict(grade=G_NONE, candidates=[], best=None, reason=None,
               safe_to_default=False, matched_items=[])
    n = norm_name(name)
    if not n:
        out["reason"] = "the line carries no name either"
        return out

    ros = _roster if _roster is not None else roster(con)
    bill_no = _bill_no(raw_text, guess_clinic_id)
    want4 = _phone_last4(raw_text)

    exact = ros.get(n, [])
    if len(exact) > 1:
        out.update(grade=G_AMBIGUOUS, candidates=exact,
                   reason="%d patients share the name %r — refusing to guess between them"
                          % (len(exact), name))
        return out

    if len(exact) == 1:
        c = exact[0]
        out.update(grade=G_UNIQUE, candidates=exact, best=c,
                   reason="exactly one patient in %d on file has this name" % len(ros))
        why = []
        if want4 and c.get("phone_last4") and want4 == c["phone_last4"]:
            why.append("phone last-4 agrees")
        items = _bought_before(con, unit, c["id"], bill_no)
        if items:
            out["matched_items"] = items
            why.append("bought %s before" % ", ".join(items[:3]))
        if why:
            out.update(grade=G_CORROBORATED,
                       reason=out["reason"] + "; " + " and ".join(why))
        out["safe_to_default"] = out["grade"] in CONFIDENT
        return out

    near = [c for key, lst in ros.items() if edit_distance_le1(n, key) for c in lst]
    if len(near) == 1:
        out.update(grade=G_NEAR, candidates=near, best=near[0],
                   reason="one character different from %r — shown for a human to judge, "
                          "never applied automatically" % near[0]["name"])
        return out
    if len(near) > 1:
        out.update(grade=G_AMBIGUOUS, candidates=near,
                   reason="%d names are one character away — too close to call" % len(near))
        return out

    out["reason"] = "no patient on file matches this name"
    return out


def sweep(con, unit, business_date=None, limit=500):
    """Every open review line, with a suggestion for each. Writes nothing.

    This is what a checker's screen shows: the queue, already thought about."""
    sql = ("SELECT r.id, r.guess_name, r.guess_clinic_id, r.raw_text, r.amount_p, "
           "       r.confidence, de.business_date "
           "FROM sale_item_review r JOIN day_entry de ON de.id = r.day_entry_id "
           "WHERE r.status='open' AND de.unit=? ")
    args = [unit]
    if business_date:
        sql += "AND de.business_date=? "
        args.append(business_date)
    sql += "ORDER BY de.business_date DESC, r.id LIMIT ?"
    args.append(int(limit))

    ros = roster(con)
    out = []
    for rid, gname, gcid, raw, amt, conf, bdate in con.execute(sql, args):
        p = propose(con, unit, gname, raw, gcid, _roster=ros)
        out.append(dict(review_id=rid, business_date=bdate, amount_p=amt,
                        is_return=bool(amt is not None and amt < 0),
                        name_on_bill=gname, ingest_confidence=conf, **p))
    return out


def summarise(rows):
    counts = {}
    for r in rows:
        counts[r["grade"]] = counts.get(r["grade"], 0) + 1
    return counts


# --------------------------------------------------------------------------- #

def selftest(schema_path="finance_schema.sql", returns_sql="finance_returns.sql"):
    import os
    import tempfile
    ok, fail = 0, []

    def ck(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fail.append(name)

    ck("norm upper + collapse", norm_name(" ramesh   kumar ") == "RAMESH KUMAR")
    ck("norm drops punctuation", norm_name("R.K. Sharma") == "R K SHARMA")
    ck("norm drops digits", norm_name("TESTNAMEA 6503") == "TESTNAMEA")
    ck("norm of nothing", norm_name(None) == "")

    ck("distance identical", edit_distance_le1("SANJEEV", "SANJEEV"))
    ck("distance one substitution", edit_distance_le1("SANJEEV", "SANJIEV") is True)
    ck("distance two substitutions", edit_distance_le1("SANJEEV", "SUNJIEV") is False)
    ck("distance one insert", edit_distance_le1("SANJIV", "SANJIVE"))
    ck("distance one delete", edit_distance_le1("SANJIVE", "SANJIV"))
    ck("distance one swap-char", edit_distance_le1("SUNITA", "SUNILA"))
    ck("distance two is too far", not edit_distance_le1("SUNITA", "SUNILO"))
    ck("distance length gap two", not edit_distance_le1("RAM", "RAMESH"))

    ck("bill no from raw", _bill_no('{"Bill No": "A002966"}') == "A002966")
    ck("credit note from raw", _bill_no('{"Bill No": "CN00167"}') == "CN00167")
    ck("no bill no", _bill_no("nothing here") is None)
    ck("phone last4 from raw", _phone_last4('{"phone_last4": "5641"}') == "5641")
    ck("no phone in raw", _phone_last4('{"x": 1}') is None)

    fd, db = tempfile.mkstemp(prefix="fin_ident_", suffix=".db")
    os.close(fd)
    os.remove(db)
    con = sqlite3.connect(db)
    con.executescript(open(schema_path, encoding="utf-8").read())
    con.executescript(open(returns_sql, encoding="utf-8").read())

    def day(d):
        con.execute("INSERT OR IGNORE INTO day_entry (unit,business_date,status) "
                    "VALUES ('medical',?, 'draft')", (d,))
        return con.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?",
                           (d,)).fetchone()[0]

    def pat(cid, nm, last4=None):
        con.execute("INSERT OR IGNORE INTO patient_ref (clinic_id,name,phone_last4,first_seen) "
                    "VALUES (?,?,?, '2026-01-01')", (cid, nm, last4))
        return con.execute("SELECT id FROM patient_ref WHERE clinic_id=?", (cid,)).fetchone()[0]

    p_ram = pat("4471", "Ramesh Kumar", "1234")
    pat("5120", "Sunita Devi", "9999")
    pat("6001", "Ramesh Kumar", None)          # a genuine duplicate name
    pat("7000", "Manohar Lal", "4321")
    pat(WALK_IN, "Walk in", None)

    ros = roster(con)
    ck("roster excludes WALK-IN", all(c["clinic_id"] != WALK_IN
                                      for lst in ros.values() for c in lst))
    ck("roster groups duplicate names", len(ros.get("RAMESH KUMAR", [])) == 2)

    v = propose(con, "medical", "Sunita Devi", _roster=ros)
    ck("unique name matches", v["grade"] == G_UNIQUE)
    ck("unique match names the right patient", v["best"]["clinic_id"] == "5120")
    ck("unique match is safe to default", v["safe_to_default"])

    v = propose(con, "medical", "Ramesh Kumar", _roster=ros)
    ck("a shared name is AMBIGUOUS", v["grade"] == G_AMBIGUOUS)
    ck("ambiguous offers no default", not v["safe_to_default"])
    ck("ambiguous still shows both", len(v["candidates"]) == 2)
    ck("ambiguous says why", "refusing to guess" in v["reason"])

    v = propose(con, "medical", "Manohar Lai", _roster=ros)
    ck("one character out is NEAR", v["grade"] == G_NEAR)
    ck("near is never safe to default", not v["safe_to_default"])
    ck("near says what it is guessing", "Manohar Lal" in v["reason"])

    v = propose(con, "medical", "Nobody At All", _roster=ros)
    ck("unknown name matches nothing", v["grade"] == G_NONE)
    v = propose(con, "medical", "", _roster=ros)
    ck("no name at all", v["grade"] == G_NONE)

    # phone corroboration lifts a unique match
    v = propose(con, "medical", "Sunita Devi", raw_text='{"phone_last4": "9999"}', _roster=ros)
    ck("phone agreement corroborates", v["grade"] == G_CORROBORATED)
    ck("corroborated says why", "phone last-4 agrees" in v["reason"])
    v = propose(con, "medical", "Sunita Devi", raw_text='{"phone_last4": "0000"}', _roster=ros)
    ck("a phone that disagrees does not corroborate", v["grade"] == G_UNIQUE)

    # medicine corroboration.
    # finance_returns lives beside the schema on the box, which is NOT the
    # folder this selftest is run from at install time. Resolve it from the
    # argument we were given rather than assuming the current directory.
    import sys as _sys
    for _d in (os.path.dirname(os.path.abspath(returns_sql)),
               os.path.dirname(os.path.abspath(__file__))):
        if _d and _d not in _sys.path:
            _sys.path.insert(0, _d)
    try:
        import finance_returns as R
    except ImportError as _ex:                                     # noqa: F841
        fail.append("finance_returns not importable from %s or %s — the drug-line "
                    "corroboration checks could not run"
                    % (os.path.dirname(os.path.abspath(returns_sql)),
                       os.path.dirname(os.path.abspath(__file__))))
        R = None

    if R is None:
        con.close()
        try:
            os.remove(db)
        except OSError:
            pass
        print("IDENTITY %d/%d passed" % (ok, ok + len(fail)))
        for f in fail:
            print("  FAIL:", f)
        return 1
    eid = day("2026-08-01")
    con.execute("INSERT INTO sale_item (day_entry_id,unit,patient_ref_id,service,amount_p,"
                "source,source_ref,confidence) VALUES (?, 'medical', ?, 'pharmacy', 50000,"
                " 'manual','A002700', 0.99)", (eid, p_ram))
    R.load_lines(con, "medical", "2026-08-01",
                 [dict(bill_no="A002700", bill_date="2026-08-01", seq=1,
                       item_name="FOLITRAX 15 MG TAB", amount_p=10000)])
    day("2026-08-05")
    R.load_lines(con, "medical", "2026-08-05",
                 [dict(bill_no="A002999", bill_date="2026-08-05", seq=1,
                       item_name="FOLITRAX 15 MG TAB", amount_p=10000)])
    con.commit()
    items = _bought_before(con, "medical", p_ram, "A002999")
    ck("prior purchase of the same medicine is found", items == ["FOLITRAX 15 MG TAB"])
    ck("no drug lines -> no corroboration, not a crash",
       _bought_before(con, "medical", p_ram, "NOSUCHBILL") == [])

    # the sweep
    con.execute("INSERT INTO sale_item_review (day_entry_id, raw_text, guess_name, amount_p, "
                "confidence, status) VALUES (?, ?, 'Sunita Devi', 45000, 0.5, 'open')",
                (eid, '{"Bill No":"A002801","phone_last4":"9999"}'))
    con.execute("INSERT INTO sale_item_review (day_entry_id, raw_text, guess_name, amount_p, "
                "confidence, status) VALUES (?, ?, 'Ramesh Kumar', 20000, 0.5, 'open')",
                (eid, '{"Bill No":"A002802"}'))
    con.execute("INSERT INTO sale_item_review (day_entry_id, raw_text, guess_name, amount_p, "
                "confidence, status) VALUES (?, ?, 'Ghost Person', -7700, 0.5, 'open')",
                (eid, '{"Bill No":"CN00168"}'))
    con.commit()

    rows = sweep(con, "medical")
    ck("sweep sees every open line", len(rows) == 3)
    counts = summarise(rows)
    ck("sweep grades the corroborated one", counts.get(G_CORROBORATED) == 1)
    ck("sweep grades the ambiguous one", counts.get(G_AMBIGUOUS) == 1)
    ck("sweep grades the unknown one", counts.get(G_NONE) == 1)
    ck("sweep marks a return as a return",
       [r["is_return"] for r in rows if r["name_on_bill"] == "Ghost Person"] == [True])
    ck("sweep offers a default only where it is safe",
       sum(1 for r in rows if r["safe_to_default"]) == 1)

    n_before = con.execute("SELECT COUNT(*) FROM sale_item").fetchone()[0]
    sweep(con, "medical")
    ck("the sweep writes NOTHING to sale_item",
       con.execute("SELECT COUNT(*) FROM sale_item").fetchone()[0] == n_before)
    ck("the sweep resolves NOTHING",
       con.execute("SELECT COUNT(*) FROM sale_item_review WHERE status='open'"
                   ).fetchone()[0] == 3)

    con.close()
    try:
        os.remove(db)
    except OSError:
        pass
    print("IDENTITY %d/%d passed" % (ok, ok + len(fail)))
    for f in fail:
        print("  FAIL:", f)
    return 0 if not fail else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest(*(sys.argv[1:3] or [])))
