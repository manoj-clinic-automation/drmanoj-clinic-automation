#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_ingest_ladder_s221.py -- S221 F-283: THE D355 LADDER RUNS AT INGEST.

THE FAULT, IN THE LIVE FILE'S OWN LINES (finance_ingest.py, pin d5ff50ad):

    min_conf = float(_setting(con, "ingest.min_confidence", "0.70") or 0.70)
    ...
        low_conf = ln["confidence"] < min_conf
        if low_conf or (anonymous and ...):
            INSERT INTO sale_item_review ...
            continue                       # resolve_patient_checked() is BELOW

A bill carrying a name and no clinic ID leaves split_clinic_id() at confidence
0.5, fails the 0.70 gate, and is PARKED -- before the identity chain is ever
reached. D355 rules identity by LOOKUP, never by a generated confidence, and
the lookup was simply never run. 7 of 27 bills on 02-Sep (26 %) parked this
way. F-283: "a parked bill is a lookup not yet run, not a verdict."

MEASURED before building, on the live copy (D:\\Downloads\\_live_S219\\finance.db),
over every bill parked since 01-Aug (182 of them -- before August Marg carried
a last-four on only 9 % of bills, so the older rows flatter nothing):

    last-4 + name only .................  75   41 %
    + Docterz visit, +/-3 days .........  99   54 %   (48 left ambiguous)
    + Docterz visit, SAME DAY only ..... 104   57 %   (22 left ambiguous)
    + the full mobile .................. 126   69 %   ( 0 left ambiguous)

Two findings decided the shape:

 1. SAME-DAY BEATS THE WINDOW, on both axes. Of the 1,105 July-August pharmacy
    bills carrying a real patient, 78 % were bought on the day that patient
    visited and only 2.3 % within three days -- so D11's founding assumption
    ("a pharmacy purchase follows a consultation by days, not hours") is false
    for this pharmacy. The wider window finds FEWER (24 vs 29) and leaves
    TWICE the ambiguity, because it drags in a second patient whose name also
    agrees. The day's list is a median of 24 people: a short list, not a search.

 2. THE FULL MOBILE ENDS THE AMBIGUITY. Every one of the 22 rows still
    ambiguous on last-four is ambiguous only because a last-four is shared:
    1,871 last-four values in the master belong to more than one patient, but
    only 719 numbers do. Given the number, the ladder separates 22 of 22.

THE OWNER'S RULING (S221): clinic ID - full mobile - name attach; what falls
through goes to the SAME-DAY Docterz list; NO question is raised with anyone --
"right now only internal match is sufficient". So nothing here asks a human.
Nothing here is silent either: every attachment records WHICH rung named it,
in identity_resolution, so any one of them is answerable afterwards.

WHAT THIS PATCH DOES NOT DO: it does not move money and it does not touch the
accept path. The ladder only supplies the clinic ID the bill was missing; the
line then travels the ordinary path below it, so resolve_patient_checked() and
the S220 name-check still run on every ladder-named bill exactly as before.
Every rung is fail-soft: no answer, and the line parks exactly as it does today.

F-185: the full mobile is fingerprinted IN MEMORY against patient_ref.mobile_fp
and discarded; it is never written to the database, and the patch strips it
from the raw JSON that sale_item_review keeps. No number is stored by this file.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_ingest_ladder_s221.py
Offline:         FI_PATH=./finance_ingest.py python3 -B patch_ingest_ladder_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('FI_PATH', '/root/finance/finance_ingest.py')
MARK = "S221 F-283"


# --------------------------------------------------------------- anchor A
# adapter_csv: carry the mobile and the last-four out of the export row, and
# keep the full number OUT of the stored raw JSON.

A_OLD = '''        out.append(dict(bill_no=(get("bill_no") or "").strip() or None,
                        bill_date=get("bill_date"),
                        clinic_id=cid, patient_name=name,
                        description=(get("description") or "").strip() or None,
                        amount_p=amount, kind=kind,
                        gross_p=(abs(_grp) if _grp is not None else None),
                        disc_p=(abs(_dsp) if _dsp is not None else None),
                        mode=(get("mode") or "").strip().lower() or None,
                        confidence=conf, raw=json.dumps(row, ensure_ascii=False)[:2000]))
'''

A_NEW = '''        # S221 F-283: the export's own mobile and last-four columns travel with
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
'''


# --------------------------------------------------------------- anchor C
# the ladder itself, placed after the S220 F-277 block it builds on.

C_OLD = '# ---- end S220 F-277 ---------------------------------------------------------\n'

C_NEW = '''# ---- end S220 F-277 ---------------------------------------------------------


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
'''


# --------------------------------------------------------------- anchor D
D_OLD = '    accepted = review = total_p = 0\n'
D_NEW = '    accepted = review = total_p = 0\n    laddered = 0                     # S221 F-283 -- named by the D355 ladder\n'


# --------------------------------------------------------------- anchor B
# the park branch: run the ladder BEFORE parking.

B_OLD = '''        if low_conf or (anonymous and not (anon_to_walkin and structured)):
            # sale_item_review carries no non-negative constraint, so a return
            # is stored SIGNED here \u2014 that keeps v_day_attribution.in_review_p
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
'''

B_NEW = '''        if low_conf or (anonymous and not (anon_to_walkin and structured)):
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
                # is stored SIGNED here \u2014 that keeps v_day_attribution.in_review_p
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
'''


# --------------------------------------------------------------- anchor E
E_OLD = '''    return dict(ok=True, batch_id=batch_id, adapter=adapter, rows_read=len(lines),
                accepted=accepted, review=review, returns=returns,
                attributed_p=total_p, status=status)
'''

E_NEW = '''    return dict(ok=True, batch_id=batch_id, adapter=adapter, rows_read=len(lines),
                accepted=accepted, review=review, returns=returns,
                laddered=laddered,                        # S221 F-283
                attributed_p=total_p, status=status)
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW),
         ("D", D_OLD, D_NEW), ("E", E_OLD, E_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S221_ladder_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s -- the live file is unchanged." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("next     the selftest, then the walk, then: systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
