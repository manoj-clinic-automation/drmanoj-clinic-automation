#!/usr/bin/env python3
"""
patch_ingest_namecheck_s220.py -- S220 F-277, part 1 of 4: THE INGEST NAME-CHECK.

THE FAULT, IN THE LIVE FILE'S OWN LINES (finance_ingest.py, pin 6cb83302):

    def resolve_patient(con, clinic_id, name):
        if clinic_id:
            r = ...WHERE clinic_id=?...
            if r:
                return r[1] or r[0]        # the bill's name is never looked at

The `name` argument is read ONLY on the branch where the ID is unknown. On the
branch that fires for every bill carrying an ID, the name is discarded -- the
docstring's "name only as a hint" overstates it. And the function returns a
bare patient id, so it has NO CHANNEL to say "I am unsure": the row has
already cleared the confidence gate and is written at full confidence. The
disagreement is not just unacted-on; it is unrecorded.

MEASURED (returns_docterz_match_Aug2026.csv, S217/218; F-276 says search it
first): 3 of 43 August returns carry a clinic ID that belongs to someone else
-- 762 is Daljeet Singh, the bill is Paramjeet Kour's; 638 is Saloni
Shrivastav; 782 is Trishna. Each was attached to the stranger SILENTLY, and
every audit afterwards judged her returns against his purchases with complete
confidence. (Two more rows on that sheet are NOT this fault: 7837, where the
books and the master agree and only Marg's typed name is odd; and 212, an ID
absent from the master, which "identity needed" already covers.)

THE SHAPE, BY THE OWNER'S RULING (S219 close; S220 design brief):
a disagreement becomes a FINDING, not a tiebreak.
  * Attachment is still BY ID ONLY. Nothing is re-attached by name, nothing is
    guessed. THE MONEY IS UNAFFECTED -- the sale_item row is written exactly as
    before, to the same patient_ref, at the same confidence.
  * Alongside it, a row in `identity_dispute` (created here if absent):
    unit, date, bill, clinic ID, the name on the bill, the name in the master.
    UNIQUE per (unit, date, bill, id), so a re-ingest of the day -- which
    deletes and re-inserts sale rows -- neither duplicates it nor loses its
    status. If a later re-export AGREES (the counter corrected the bill), the
    open dispute is closed by the ingest itself, resolution recorded.
  * The comparison is TOLERANT, calibrated on the master's own spellings --
    Kanta Parsad / KANTA PRASAD, Chandrwati / CHANDRAWATI, VIVHA / VIVAH,
    Archna / Archana, Parwati / Parvati, Kour / Kaur all AGREE, as the evidence
    sheet says they do. A stricter test would manufacture false disputes (the
    S216 lesson: a homemade check stricter than canon refused correct work).
    A bill name that is nothing but an honorific ("SMT") is UNKNOWN, not a
    dispute. Rows the ingest itself created (first-seen IDs) carry the first
    bill's name, so a second bill with the same ID and another name DOES
    dispute -- two names on one ID is exactly the condition.
  * D361 is respected downstream: the verdict is gated by returns.act_from in
    the audit's consumers, so the past raises no work.

TWO anchored changes, every OLD block sliced verbatim from the live bytes:
  A  the helper block (name match · checked resolver · dispute writer),
     inserted before `def ingest_day`. resolve_patient() itself is UNCHANGED.
  B  the one call site in ingest_day: the checked resolver, then the note.

Run on the box:
  /root/wa/venv/bin/python3 -B /root/finance/patch_ingest_namecheck_s220.py
then the audit / darpan / hub patchers, then restart clinic-finance.service.
Offline: FI_PATH=/path/to/finance_ingest.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('FI_PATH', '/root/finance/finance_ingest.py')
MARK = 'S220 F-277'

A_OLD = 'hone()\n    return r[0] if r else None\n\n\ndef ingest_day(con, unit, business_date, adapter, payload, run_by="system",\n'

A_NEW = '''hone()
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
        if len(diff) == 2 and diff[1] == diff[0] + 1 and \\
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


def ingest_day(con, unit, business_date, adapter, payload, run_by="system",
'''

B_OLD = '        pid = resolve_patient(con, ln.get("clinic_id"), ln.get("patient_name"))\n        _new_mode = ln.get("mode")\n'

B_NEW = ('        # S220 F-277: attach by ID exactly as before; ALSO compare the name and\n'
         '        # record a disagreement as a question. The money path is unchanged.\n'
         '        pid, _agree, _master = resolve_patient_checked(\n'
         '            con, ln.get("clinic_id"), ln.get("patient_name"))\n'
         '        _note_identity_dispute(con, unit, business_date, ln.get("bill_no"),\n'
         '                               ln.get("clinic_id"), ln.get("patient_name"),\n'
         '                               _master, pid, _agree, kind, now)\n'
         '        _new_mode = ln.get("mode")\n')

PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


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
    bak = TARGET + ".bak_S220_f277_" + stamp
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
    print("next     the audit, darpan and hub patchers, then: systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
