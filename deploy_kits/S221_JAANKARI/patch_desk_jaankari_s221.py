#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_desk_jaankari_s221.py -- S221 star-1-1, part 1 of 2: DARPAN'S LIST, server side.

THE OWNER'S RULING, 03-Sep-2026 (it changes the S220 design and is followed here):

    "send identity questions, go soft on answers from him ... first get him to do
     sales return, stock check, drawer management for some time, and reassess ...
     right now only internal match is sufficient"

So the questions DO reach him -- and NOTHING he answers is allowed to act.
`S220_RETURNS_INTENT_DESIGN` Layer C said a row unanswered for two days escalates
by itself, and G6 gave him a two-working-day clearance target. **Both are
SUPERSEDED by this ruling: silence costs him nothing.** There is no timer in this
file. Recorded here rather than quietly dropped.

WHAT "SOFT" MEANS, IN CODE. This whole feature is READ-ONLY except for a single
INSERT into a single new table, `jaankari_answer`. It does not move money. It
does not re-attach a patient. It does not close an `identity_dispute`. It does
not mark a `stock_spot_check` done -- the owner still taps "counted" on his own
card. An answered row leaves HIS list so the list can shrink, and stays OPEN for
the owner, now carrying what he said. If he changes his mind, both answers are
kept: the table is append-only, and that is the point of evidence.

THE THREE LISTS (the entry point's star-1-1):
  1. identity disputes  -- open rows of `identity_dispute` (S220 F-277)
  2. identity needed    -- returns still sitting on WALK-IN since `returns.act_from`
  3. spot counts        -- due rows of `stock_spot_check` (S220 LARGE_RETURN_GATE, D365)

Three buttons on the identity rows, the owner's own words:
  yah sahi hai . bill dhoondho . pata nahin
The spot rows take a NUMBER, because a count is a number -- recorded, never
closing the row.

D363: the FULL mobile shows beside the name. This is a counter screen and that
is the owner's ruling. No number is written into this file (F-185); it is read
from `patient_ref` at request time, and falls back to the last four.

Target: /root/finance/returns_desk.py (live pin afc8b0d0...)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_desk_jaankari_s221.py
Offline:         RD_PATH=./returns_desk.py python3 -B patch_desk_jaankari_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('RD_PATH', '/root/finance/returns_desk.py')
MARK = "S221 star-1-1"


# --------------------------------------------------------------- anchor A
# the schema: one new table, appended where every other table is declared.

A_OLD = '''CREATE INDEX IF NOT EXISTS idx_rl_visit ON return_line(visit_id);
"""
'''

A_NEW = '''CREATE INDEX IF NOT EXISTS idx_rl_visit ON return_line(visit_id);

/* S221 star-1-1 -- what Darpan said, and nothing else. Append-only: a second
   answer is a second row, never an overwrite. Nothing reads this table to
   decide anything; it is evidence for the owner, by his ruling of 03-Sep. */
CREATE TABLE IF NOT EXISTS jaankari_answer (
  id INTEGER PRIMARY KEY,
  unit TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('dispute','identity','spot')),
  ref TEXT NOT NULL,
  business_date TEXT,
  answer TEXT NOT NULL,
  value TEXT,
  note TEXT,
  answered_by TEXT NOT NULL,
  answered_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ja_kind ON jaankari_answer(kind, ref);
"""
'''


# --------------------------------------------------------------- anchor B
# the two routes, placed before the slips route.

B_OLD = '''@bp.route("/api/slips")
def api_slips():
'''

B_NEW = '''# ---- S221 star-1-1: DARPAN'S JAANKARI LIST ---------------------------------
# Read-only, except one INSERT into jaankari_answer. See this kit's README and
# the patcher header for why nothing here is allowed to act on what he says.

JAANKARI_ANSWERS = ("ok", "find_bill", "dont_know", "counted")


def _rd_setting(con, key, default=None):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r[0] if (r and r[0] not in (None, "")) else default
    except Exception:
        return default


def _rd_has(con, name):
    try:
        return bool(con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (name,)).fetchone())
    except Exception:
        return False


def _rd_answers(con, kind):
    """The LATEST answer per ref -- the table is append-only, so the last row
    for a ref wins for display, and every earlier one stays on the record."""
    out = {}
    try:
        for r in con.execute(
                "SELECT ref, answer, value, answered_by, answered_at "
                "FROM jaankari_answer WHERE kind=? ORDER BY id", (kind,)):
            out[str(r["ref"])] = dict(answer=r["answer"], value=r["value"],
                                      by=r["answered_by"], at=r["answered_at"])
    except Exception:
        pass
    return out


def _rd_mobile(con, clinic_id):
    """D363 -- the counter's own screen shows the whole number. Read at request
    time from the master; never stored in this file (F-185). Falls back to the
    last four, and to nothing at all rather than guessing."""
    if not clinic_id:
        return ""
    try:
        r = con.execute("SELECT * FROM patient_ref WHERE clinic_id=?",
                        (clinic_id,)).fetchone()
    except Exception:
        return ""
    if not r:
        return ""
    k = r.keys()
    m = (r["mobile"] or "").strip() if "mobile" in k else ""
    if m:
        return m
    l4 = (r["phone_last4"] or "").strip() if "phone_last4" in k else ""
    return ("xxxxxx" + l4) if l4 else ""


@bp.route("/api/jaankari")
def api_jaankari():
    """The three lists. READ-ONLY -- it writes nothing at all."""
    _u, err = _auth()
    if err:
        return err
    con = _con()
    out = dict(disputes=[], identity=[], spot=[])
    ans = dict((k, _rd_answers(con, k)) for k in ("dispute", "identity", "spot"))

    # 1 -- the disputes the ingest recorded (S220 F-277)
    if _rd_has(con, "identity_dispute"):
        try:
            for r in con.execute(
                    "SELECT id, business_date, bill_no, clinic_id, bill_name, master_name "
                    "FROM identity_dispute WHERE status='open' AND unit=? "
                    "ORDER BY business_date DESC, id DESC LIMIT 60", (_unit,)):
                ref = str(r["id"])
                out["disputes"].append(dict(
                    ref=ref, date=r["business_date"], bill=r["bill_no"],
                    clinic_id=r["clinic_id"], bill_name=r["bill_name"],
                    master_name=r["master_name"],
                    mobile=_rd_mobile(con, r["clinic_id"]),
                    answered=ans["dispute"].get(ref)))
        except Exception:
            pass

    # 2 -- returns still sitting on WALK-IN since the owner's line
    # D361 -- THE PAST IS ACCEPTED AND RAISES NO WORK, so the default does not
    # reach into it: it is the day the identity machinery went live (the S220
    # close). Left at the owner's line of 18-Jun this list opened with 22
    # historical rows on a phone -- seen in the render test, not guessed. The
    # backlog is one setting row away (returns.act_from = 2026-06-18) if he
    # ever wants it worked.
    act_from = _rd_setting(con, "returns.act_from", "2026-09-02")
    try:
        walk = con.execute(
            "SELECT id FROM patient_ref WHERE clinic_id='WALK-IN'").fetchone()
    except Exception:
        walk = None
    if walk:
        try:
            for r in con.execute(
                    "SELECT s.source_ref ref, d.business_date bd, s.amount_p amt, "
                    "s.description ds FROM sale_item s "
                    "JOIN day_entry d ON d.id=s.day_entry_id "
                    "WHERE s.service='pharmacy_return' AND s.patient_ref_id=? "
                    "AND d.business_date>=? AND d.unit=? "
                    "ORDER BY d.business_date DESC LIMIT 60",
                    (walk[0], act_from, _unit)):
                ref = str(r["ref"] or "")
                if not ref:
                    continue
                nm = ""
                try:
                    nm = (json.loads(r["ds"] or "{}") or {}).get("patient_name") or ""
                except Exception:
                    nm = ""
                out["identity"].append(dict(
                    ref=ref, date=r["bd"], amount_p=abs(r["amt"] or 0), name=nm,
                    answered=ans["identity"].get(ref)))
        except Exception:
            pass

    # 3 -- the shelves to count (D365, the deterrent)
    if _rd_has(con, "stock_spot_check"):
        try:
            for r in con.execute(
                    "SELECT id, business_date, item_name, batch, bill_no, reason "
                    "FROM stock_spot_check WHERE status='due' AND unit=? "
                    "ORDER BY requested_at DESC LIMIT 60", (_unit,)):
                ref = str(r["id"])
                out["spot"].append(dict(
                    ref=ref, date=r["business_date"], item=r["item_name"],
                    batch=r["batch"], bill=r["bill_no"],
                    answered=ans["spot"].get(ref)))
        except Exception:
            pass

    pending = sum(1 for k in out for x in out[k] if not x.get("answered"))
    return jsonify(ok=True, lists=out, pending=pending,
                   counts=dict((k, len(v)) for k, v in out.items()))


@bp.route("/api/jaankari/answer", methods=["POST"])
def api_jaankari_answer():
    """Record what he said. EVIDENCE ONLY: this endpoint writes exactly one row
    in one table and touches nothing else in the database -- no money, no
    patient, no dispute status, no spot-check status. The owner's ruling."""
    u, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    kind = str(b.get("kind") or "").strip()
    ref = str(b.get("ref") or "").strip()
    answer = str(b.get("answer") or "").strip()
    if kind not in ("dispute", "identity", "spot") or not ref \\
            or answer not in JAANKARI_ANSWERS:
        return jsonify(ok=False, error="bad_request",
                       message="kind/ref/answer theek nahin"), 400
    val = b.get("value")
    val = str(val).strip() if val not in (None, "") else None
    note = b.get("note")
    note = str(note).strip() if note not in (None, "") else None
    con = _con()
    who = str((u or {}).get("user") or (u or {}).get("username") or "")
    con.execute(
        "INSERT INTO jaankari_answer (unit, kind, ref, business_date, answer,"
        " value, note, answered_by, answered_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (_unit, kind, ref, (str(b.get("date")).strip() or None) if b.get("date") else None,
         answer, val, note, who,
         datetime.datetime.now().replace(microsecond=0).isoformat()))
    con.commit()
    return jsonify(ok=True)
# ---- end S221 star-1-1 ------------------------------------------------------


@bp.route("/api/slips")
def api_slips():
'''


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
    bak = TARGET + ".bak_S221_jaankari_" + stamp
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
    print("next     the page patcher, then the selftest, then the walk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
