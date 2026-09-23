#!/usr/bin/env python3
"""apply_s377.py -- kit S377_ICICI_COUNT. Anchored edits on sanjeevni_approvals.py 4f98cb37 (S375 bytes) and
finance_ui/finance_approvals.html 19c877e5 (S375 bytes). F-615.

THE FAULT. S375 counted what ICICI holds from ZERO at the 17-Aug cash anchor -- only the POS settlements
credited since then, less the transfers recorded. The money the account ALREADY held is outside that count,
so the count is short by whatever was in the account, and its over-balance rule refused the owner's real
ICICI -> Yes Bank transfer of 40,000 on 20-Sep ("more than the 31,551 it holds"), which the Yes Bank
statement shows the bank actually made.

THE PROOF, from his own ICICI August statement: closing 1,50,263.42 on 31-Aug, and the settlements credited
after it come to 1,45,416 by 20-Sep -- so ICICI held 2,95,679 that day, against which he moved 2,90,000
(2,50,000 + 40,000) and left 5,679. The bank was right and our count was short by exactly the balance it
could not see.

THE CHANGE, in two parts.
  1. THE COUNT STARTS AT THE BANK'S OWN FIGURE. New table `bank_anchor`: one row per account -- the closing
     balance the bank itself printed, the date it applies to, and the statement it came from. The position is
     then: that balance + every settlement credited after it - every transfer recorded after it. With no
     anchor row the old reckoning stands, so nothing breaks on a box that has not been seeded.
  2. A STATEMENT THAT STOPS AT THE ENTRY'S OWN DATE PROVES NOTHING. A credit can land up to three days late,
     so an entry is only called "NOT in the statement" when a loaded statement reaches three days past it;
     otherwise it waits. His two 20-Sep transfers were being called missing by a statement that ends 20-Sep.
  3. A COUNT THAT IS SHORT NEVER REFUSES THE BANK. A transfer larger than the count is RECORDED, and the
     answer says by how much the count was short. ICICI never reads below zero on the page; it says the count
     is short and that the ICICI statement will settle it. Every other refusal stands -- a future date, a date
     before the anchor, zero, the same entry twice, a route that is not his.

  python3 apply_s377.py --dir /root/finance [--out DIR]
"""
import argparse, hashlib, os
ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--out")
a = ap.parse_args()
OUT = a.out or a.dir

p = os.path.join(a.dir, "sanjeevni_approvals.py"); s = open(p, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "4f98cb378a9beee6771c3df11cc3d606", "sanjeevni_approvals.py is not 4f98cb37"
def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)

rep('''VERSION = "1.1"''', '''VERSION = "1.2"''')
rep('''#      GET /finance/sanjeevni/api/needs-you      what needs the owner, in words, with a target''',
'''#  v1.2 (S377, F-615, 23-Sep-2026): what ICICI holds is counted from the BANK'S OWN closing balance
#  (table `bank_anchor`, seeded from the statement he gave), not from zero at the cash anchor -- v1.1 could
#  not see the money the account already held, and refused his real 20-Sep transfer because of it. And a
#  count that is short never refuses the bank: the transfer is recorded and the shortfall is named.
#
#      GET /finance/sanjeevni/api/needs-you      what needs the owner, in words, with a target''')

# ---- the anchor table and the true count
rep('''def ensure_schema(con):
    """The one table this module owns. Created on first use; nothing else is touched."""
    con.execute(TRANSFER_DDL)''',
'''ANCHOR_DDL = (
    "CREATE TABLE IF NOT EXISTS bank_anchor ("
    " unit TEXT NOT NULL, account TEXT NOT NULL, as_on TEXT NOT NULL, balance_p INTEGER NOT NULL,"
    " source TEXT, entered_by TEXT, entered_at TEXT, PRIMARY KEY (unit, account))")


def ensure_schema(con):
    """The two tables this module owns. Created on first use; nothing else is touched."""
    con.execute(TRANSFER_DDL)
    con.execute(ANCHOR_DDL)


def anchor_for(con, account, unit=None):
    """The bank's own closing balance for this account, as on a date, from a statement it printed.
    None when no statement has been anchored yet -- the count then starts where it always did."""
    unit = unit or _unit
    if not _has(con, "bank_anchor"):
        return None
    r = con.execute("SELECT as_on, balance_p, source FROM bank_anchor WHERE unit=? AND account=?",
                    (unit, account)).fetchone()
    return dict(as_on=r[0], balance_p=int(r[1]), source=r[2] or "") if r else None''')

rep('''def icici_position(con, unit=None):
    """What ICICI holds, computed and never typed: every POS settlement it has credited since the anchor,
    less every transfer recorded out of it. The bank's own statement is not read here (S375 has no reader
    yet), so the figure says how it was made."""
    unit = unit or _unit
    credited = int(con.execute("SELECT COALESCE(SUM(parsed_total_p),0) FROM upi_statement WHERE unit=? "
                               "AND statement_date>=?", (unit, ANCHOR_FLOOR)).fetchone()[0] or 0)
    out = sum(t["amount_p"] for t in transfers(con, unit) if t["frm"] == "icici")
    last = con.execute("SELECT MAX(statement_date) FROM upi_statement WHERE unit=?", (unit,)).fetchone()[0]
    return dict(credited_p=credited, out_p=out, holds_p=credited - out, since=ANCHOR_FLOOR, upto=last)''',
'''def icici_position(con, unit=None):
    """What ICICI holds, computed and never typed (S377):

        the balance the BANK printed on its own statement, as on its date
      + every POS settlement credited after that date
      - every transfer recorded out of ICICI after that date

    With no anchored statement it falls back to what v1.1 did -- settlements since the 17-Aug cash anchor,
    which cannot see the money the account already held, and is therefore only ever a floor."""
    unit = unit or _unit
    anc = anchor_for(con, "icici", unit)
    since = anc["as_on"] if anc else ANCHOR_FLOOR
    base = anc["balance_p"] if anc else 0
    # a settlement dated D is credited the next working day, so a settlement dated ON the anchor's date is
    # money that arrived AFTER that closing balance -- it counts.
    credited = int(con.execute("SELECT COALESCE(SUM(parsed_total_p),0) FROM upi_statement WHERE unit=? "
                               "AND statement_date>=?", (unit, since)).fetchone()[0] or 0)
    out = sum(t["amount_p"] for t in transfers(con, unit) if t["frm"] == "icici" and t["date"] > since)
    last = con.execute("SELECT MAX(statement_date) FROM upi_statement WHERE unit=?", (unit,)).fetchone()[0]
    return dict(credited_p=credited, out_p=out, base_p=base, holds_p=base + credited - out,
                since=since, upto=last, anchored=bool(anc),
                source=(anc["source"] if anc else ""))''')

# ---- a statement that stops at the entry's own date proves nothing (F-615b)
rep('''def _statement_covers(con, iso):
    if not _has(con, "bank_statement_period"):
        return False
    return con.execute("SELECT 1 FROM bank_statement_period WHERE period_from<=? AND period_to>=?",
                       (iso, iso)).fetchone() is not None''',
'''def _statement_covers(con, iso):
    """Does a loaded statement reach far enough PAST this date to prove the money never arrived? A credit can
    land up to three days late, so a statement that stops on the day itself proves nothing: the entry waits
    rather than being called missing (S377)."""
    if not _has(con, "bank_statement_period"):
        return False
    need = (dt.date.fromisoformat(iso) + dt.timedelta(days=3)).isoformat()
    return con.execute("SELECT 1 FROM bank_statement_period WHERE period_from<=? AND period_to>=?",
                       (iso, need)).fetchone() is not None''')

# ---- the Bank view: never below zero, and say where the count starts
rep('''                icici=dict(holds=rs(ip["holds_p"]), credited=rs(ip["credited_p"]), out=rs(ip["out_p"]),
                           since=dmy(ip["since"]), upto=(dmy(ip["upto"]) if ip["upto"] else None)),''',
'''                icici=dict(holds=rs(max(ip["holds_p"], 0)),
                           short=(rs(-ip["holds_p"]) if ip["holds_p"] < 0 else ""),
                           credited=rs(ip["credited_p"]), out=rs(ip["out_p"]),
                           base=(rs(ip["base_p"]) if ip["anchored"] else ""), anchored=ip["anchored"],
                           source=ip["source"], since=dmy(ip["since"]),
                           upto=(dmy(ip["upto"]) if ip["upto"] else None)),''')

# ---- a short count records the transfer; it never refuses the bank
rep('''    if frm == "icici":
        ip = icici_position(con)
        if amt > ip["holds_p"]:
            return jsonify(ok=False, error="over_balance",
                           message="ICICI has collected %s since 17-Aug and %s has already been moved out; "
                                   "this transfer of %s is more than the %s it holds. Check the amount."
                                   % (rs(ip["credited_p"]), rs(ip["out_p"]), rs(amt), rs(ip["holds_p"]))), 409
''', '''    short_p = 0
    if frm == "icici":                        # S377 (F-615): our count may be short; the bank is not
        ip = icici_position(con)
        if amt > ip["holds_p"]:
            short_p = amt - max(ip["holds_p"], 0)
''')
rep('''    return jsonify(ok=True, date=iso, amount=rs(amt), frm=ACCOUNTS.get(frm, frm), to=ACCOUNTS.get(to, to),
                   leaves=(to not in INSIDE))''',
'''    return jsonify(ok=True, date=iso, amount=rs(amt), frm=ACCOUNTS.get(frm, frm), to=ACCOUNTS.get(to, to),
                   leaves=(to not in INSIDE), short=(rs(short_p) if short_p else ""),
                   message=("Recorded. Our count of ICICI was %s short of this — the account holds money the "
                            "count cannot see until the ICICI statement is read." % rs(short_p)) if short_p else "")''')
open(os.path.join(OUT, "sanjeevni_approvals.py"), "w", encoding="utf-8").write(s)
print("sanjeevni_approvals.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())

# ------------------------------------------------------------------ the page
p2 = os.path.join(a.dir, "finance_ui", "finance_approvals.html"); h = open(p2, encoding="utf-8").read()
assert hashlib.md5(h.encode("utf-8")).hexdigest() == "19c877e57a65e54740af86690fedc90a", "finance_approvals.html is not 19c877e5"
def reph(old, new):
    global h
    assert h.count(old) == 1, old[:70]
    h = h.replace(old, new)

reph('''    h+='<details class="mon" open><summary>ICICI Sanjeevni <span class="mut" style="font-weight:400">· holds about ₹'+esc(ic.holds||"0")+
       ' — ₹'+esc(ic.credited||"0")+' collected since '+esc(ic.since||"")+(ic.upto?(' (to '+esc(ic.upto)+')'):'')+
       ', ₹'+esc(ic.out||"0")+' moved out</span></summary>'+
       '<div class="mut" style="font-size:12px;padding:2px 0 6px">Worked out from the bank\\'s own daily settlement files, less the transfers you have recorded. The ICICI account statement is not read yet, so this is our count, not the bank\\'s.</div></details>';''',
'''    h+='<details class="mon" open><summary>ICICI Sanjeevni <span class="mut" style="font-weight:400">· holds about ₹'+esc(ic.holds||"0")+
       (ic.anchored?(' — ₹'+esc(ic.base||"0")+' on the bank\\'s own statement of '+esc(ic.since||"")):(' — ₹'+esc(ic.credited||"0")+' collected since '+esc(ic.since||"")))+
       (ic.anchored?(', ₹'+esc(ic.credited||"0")+' collected since'+(ic.upto?(' (to '+esc(ic.upto)+')'):'')):(ic.upto?(' (to '+esc(ic.upto)+')'):''))+
       ', ₹'+esc(ic.out||"0")+' moved out</span></summary>'+
       '<div class="mut" style="font-size:12px;padding:2px 0 6px">'+
       (ic.anchored?('Counted from the balance the bank itself printed'+(ic.source?(' — '+esc(ic.source)):'')+', plus every settlement credited since, less the transfers you have recorded.')
                   :('Worked out from the bank\\'s own daily settlement files, less the transfers you have recorded. The ICICI account statement is not read yet, so this is our count, not the bank\\'s.'))+
       (ic.short?(' <b>Our count is ₹'+esc(ic.short)+' short of what you have moved</b> — the account holds money this count cannot see; the next ICICI statement will settle it.'):'')+
       '</div></details>';''')

reph('''      if(!j.ok){alert(j.message||j.error||"could not record it");return}
      $("bankForm").innerHTML=""; loadBank(); loadCashPos(); loadNeeds(); loadDays();''',
'''      if(!j.ok){alert(j.message||j.error||"could not record it");return}
      if(j.message)alert(j.message);                    /* S377: recorded, and our count was short */
      $("bankForm").innerHTML=""; loadBank(); loadCashPos(); loadNeeds(); loadDays();''')

reph('''<!-- S375_BANK_ENTRY (Session 281, 22-Sep-2026, D604)''',
'''<!-- S377_ICICI_COUNT (Session 281, 23-Sep-2026, F-615): what ICICI holds is counted from the balance the
     BANK printed on its own statement, not from zero at the 17-Aug cash anchor; and a count that is short
     records the transfer and says so, instead of refusing money the bank really moved.
  -- kit S375 header below --
<!-- S375_BANK_ENTRY (Session 281, 22-Sep-2026, D604)''')

open(os.path.join(OUT, "finance_ui", "finance_approvals.html"), "w", encoding="utf-8").write(h)
print("finance_approvals.html ->", hashlib.md5(h.encode("utf-8")).hexdigest())
