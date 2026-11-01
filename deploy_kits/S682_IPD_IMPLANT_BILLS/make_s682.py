#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s682.py -- kit S682_IPD_IMPLANT_BILLS (session 374, 01-Nov-2026, the parent). IPD kit 4: the implant bills desk, the
cheque on its own, the suppliers' ledger (D804, D807; the owner's answers of 07:39-07:40 IST 01-Nov).
    python3 make_s682.py <from_dir> <to_dir>        <from_dir>/surgery_cases.py must be 89a668a9 (S681's TO)
Counted edits on the live file, one appended block (the desk and its routes), then ONE word pass: the owner's word "Change
vendor to supplier" -- every whole word vendor / vendors / Vendor / Vendors becomes supplier(s) (names like vendor_id, surg_vendor,
vendor_ledger are untouched: they have no word boundary), and the page addresses /vendors and /vendor/<id> are put back so no
link breaks. Every edit must find its anchor EXACTLY once or nothing is written. No patient name, no number, no secret (F-185)."""
import hashlib
import os
import re
import sys

FROM_MD5 = "89a668a98ba5cd1a7b25df9fe043d82f"
F = "surgery_cases.py"
EDITS = []


def E(old, new, tag):
    EDITS.append((old, new, tag))


# ---------------------------------------------------------------- the header, the version, the words
E('''  Hospital: one transfer for many patients; "the monthly hospital statement is the one to be reconciled, or i need to
   manually enter the amounts paid against each patient from the statement" (11:39).
''', '''  Hospital: one transfer for many patients; "the monthly hospital statement is the one to be reconciled, or i need to
   manually enter the amounts paid against each patient from the statement" (11:39).

S682_IPD_IMPLANT_BILLS (session S374, 01-Nov-2026) -- IPD kit 4 (D804, D807; the owner's answers on the mock-up, 07:39-07:40 IST):
  * THE IMPLANT BILLS DESK, /finance/surgery/implants, for Shavez and Dr Manoj: every implant line of the new cases, grouped by
    its step, each line opening in place with the one entry its step needs. The steps, in his words: "Not raised yet -- the
    dealer has not sent the bill" · "Bill raised -- bill entry done, bill scanned" · "Cheque received" · "Paid to the supplier" ·
    "Supplier confirmed". The word is SUPPLIER everywhere ("change vendor to supplier"); the page addresses are unchanged.
  * THE BILL: number, date, amount, in whose name, scanned (a paper of kind implant_bill tied to the implant). The implant's
    bill figure becomes the bill's amount; the estimate it replaced is kept (surg_implant.estimate_p). Removing a wrong bill asks
    why and puts the line back to "not raised".
  * THE CHEQUE: a DTH cheque often covers several patients and comes without saying which bills it clears, so a cheque is
    written ON ITS OWN -- number, date, amount, from, the supplier it is made out to -- by ANY of them ("any of us"), and the
    bills are tied to it afterwards, one by one; how much is still unassigned is always shown. A line's "cheque received" is a
    new cheque, or part of one already written. The cheque page (assign by implant) is open to both logins; removing a cheque
    stays Dr Manoj's.
  * PAID TO THE SUPPLIER: the cheque handed over (anyone), or Dr Manoj's own payment on the supplier's page with "this payment
    settles" ticks on the cash lines it clears (surg_pay_alloc). SUPPLIER CONFIRMED: date and how (anyone).
  * OLD CASES (backfill) are settled ONLY by Dr Manoj on the supplier's page, one by one: cleared · I still owe · the supplier
    owes me, with the amount; an amount owed either way enters the ledger dated that day; the implant's step becomes confirmed.
  * SECTION 6 on the case shows each implant's bill, cheque, payment and confirmation, with the desk one tap away. Every change
    of step is an event (surg_implant_event); the case's implant payment follows the least advanced implant as before.
''', "doc")
E('APP_VERSION = "S681-IPD-3.0"       # S681 (S370, 30-Oct-2026): IPD kits 2+3 -- papers, implants, assistants; the bill and the share',
  'APP_VERSION = "S682-IPD-4.0"       # S682 (S374, 01-Nov-2026): IPD kit 4 -- the implant bills desk, the cheque, the suppliers\' ledger', "version")
E('''PAPER_WORD = dict(PAPERS)
''', '''PAPER_WORD = dict(PAPERS + (("implant_bill", "Supplier's implant bill"),))      # S682: filed from the desk, tied to its implant
BILL_STEP_WORD = {"pending": "Not raised yet", "raised": "Bill raised", "cheque": "Cheque received", "paid": "Paid to the supplier",
                  "confirmed": "Supplier confirmed"}
STEP_HINT = {"pending": "the dealer has not sent the bill", "raised": "bill entry done, bill scanned",
             "cheque": "the hospital's cheque is in hand -- hand it to the supplier", "paid": "awaiting the supplier's word",
             "confirmed": "the account is square for this patient"}
SETTLE = (("clear", "Cleared — nothing owed either way"), ("owe", "I still owe the supplier"), ("owed", "The supplier owes me"))
SETTLE_WORD = dict(SETTLE)
''', "paperword")
# ---------------------------------------------------------------- the schema additions
E('''    con.execute("CREATE INDEX IF NOT EXISTS ix_surg_assistant_case ON surg_assistant(case_id)")
''', '''    con.execute("CREATE INDEX IF NOT EXISTS ix_surg_assistant_case ON surg_assistant(case_id)")
    # S682 (IPD kit 4): the supplier's bill per implant, every step as an event, the cheque tied to an implant, his payment's ticks
    add("surg_implant", "estimate_p INTEGER")
    add("surg_paper", "implant_id INTEGER")
    add("surg_cheque_alloc", "implant_id INTEGER")
    con.execute("CREATE TABLE IF NOT EXISTS surg_implant_bill (id INTEGER PRIMARY KEY, implant_id INTEGER NOT NULL, case_id INTEGER NOT NULL, "
                "vendor_id INTEGER NOT NULL, bill_no TEXT NOT NULL DEFAULT '', bill_day TEXT NOT NULL DEFAULT '', amount_p INTEGER NOT NULL, "
                "bill_to TEXT NOT NULL DEFAULT 'patient', note TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, "
                "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT '')")
    con.execute("CREATE INDEX IF NOT EXISTS ix_surg_ibill_implant ON surg_implant_bill(implant_id)")
    con.execute("CREATE TABLE IF NOT EXISTS surg_implant_event (id INTEGER PRIMARY KEY, implant_id INTEGER NOT NULL, case_id INTEGER NOT NULL, "
                "kind TEXT NOT NULL, day TEXT NOT NULL DEFAULT '', amount_p INTEGER, ref_id INTEGER, note TEXT NOT NULL DEFAULT '', "
                "by_whom TEXT, at TEXT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_surg_ievent_implant ON surg_implant_event(implant_id)")
    con.execute("CREATE TABLE IF NOT EXISTS surg_pay_alloc (id INTEGER PRIMARY KEY, pay_id INTEGER NOT NULL, implant_id INTEGER NOT NULL, "
                "amount_p INTEGER NOT NULL, by_whom TEXT, at TEXT)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_surg_palloc_pay ON surg_pay_alloc(pay_id)")
''', "schema")
# ---------------------------------------------------------------- messages, the nav
E('''       "status": "✓ Status saved", "assistant": "✓ The assistant is written",''',
  '''       "status": "✓ Status saved", "assistant": "✓ The assistant is written", "ibill": "✓ The bill is entered — the line is at Bill raised",
       "unbill": "✓ The bill is removed (kept in the record with its reason) — the line is back at Not raised yet",
       "ichq": "✓ The cheque is written against this line — Cheque received", "handed": "✓ Paid to the supplier",
       "confirmed": "✓ Supplier confirmed", "settled": "✓ The old case is settled", "chqnew": "✓ The cheque is written — tie its bills to it from the desk",''', "msg")
E('''       "kind": "Unknown kind of paper.", "dupvendor": "That vendor is already in the list.", "line": "That bank line is not available.",''',
  '''       "kind": "Unknown kind of paper.", "dupvendor": "That vendor is already in the list.", "line": "That bank line is not available.",
       "step": "That line is not at the step this entry needs — open the desk again.", "chq": "Choose the cheque, or write the new cheque's number, date and amount.",
       "chqover": "That is more than is left unassigned on that cheque.", "settle": "Choose how it stands — cleared, you owe, or the supplier owes you — and the amount if owed.",
       "oldonly": "Old cases are settled by Dr Manoj on the supplier's page.", "newonly": "That is not an old case.", "chqsup": "Choose the supplier the cheque is made out to.",''', "err")
E('''    links = [("home", "/portal", "← Home"), ("cases", BASE, "Cases"), ("new", BASE + "/new", "+ New case"),
             ("backfill", BASE + "/backfill", "+ Old case (backfill)")]
    if checker:''', '''    links = [("home", "/portal", "← Home"), ("cases", BASE, "Cases"), ("new", BASE + "/new", "+ New case"),
             ("backfill", BASE + "/backfill", "+ Old case (backfill)"), ("implants", BASE + "/implants", "Implant bills")]
    if checker:''', "nav")
# ---------------------------------------------------------------- section 6 on the case
E('''    out.append(_sec(6, "Implant settlement", "implant: %s" % iw,
                    "<p class='sm'>The implant bills desk (bill raised, the cheque's number, date and amount, the vendor's confirmation — every "
                    "pending one listed for the accounts) comes in kit 4. Until then the implant payment is moved on in section 2.</p>", False))''',
  '''    out.append(_sec(6, "Implant settlement", "implant: %s" % iw, _settlement_block(con, c, checker, ims), open_n == 6))''', "sec6")
E('''    i, w = istatus(c)
    if i == "pending":
        return "Implant payment: %s — move it on as the bill and the cheque go." % w, 2
    return "Nothing waiting on this case.", 0''', '''    i, w = istatus(c)
    if i == "pending":
        return "Implant payment: %s — the next entry is on the implant bills desk (section 6)." % w, 6
    return "Nothing waiting on this case.", 0''', "next")
# the case's implant table: the bill's scan word and the events
E('''    ev += [((i["at"] or "")[:16], i["by_whom"] or "", "implant entered (%s)" % i["item"]) for i in ims]''',
  '''    ev += [((i["at"] or "")[:16], i["by_whom"] or "", "implant entered (%s)" % i["item"]) for i in ims]
    ev += [((e["at"] or "")[:16], e["by_whom"] or "", "implant %s%s" % (EVENT_WORD.get(e["kind"], e["kind"]), (" · " + e["note"]) if e["note"] else ""))
           for e in con.execute("SELECT e.* FROM surg_implant_event e WHERE e.case_id=? ORDER BY e.id", (cid,))]''', "events")
# the generic paper API never files an implant bill (that goes through the desk, tied to its implant)
E('''    if kind not in PAPER_WORD:
        return jsonify(ok=False, error="bad_kind"), 400
    blob, e = _take_upload()''', '''    if kind not in dict(PAPERS):
        return jsonify(ok=False, error="bad_kind"), 400
    blob, e = _take_upload()''', "paperapi")
# ---------------------------------------------------------------- the ledger: settled old cases
E('''    for cid, (day, pat, no) in done_cases.items():
        rows.append((day, "Actually due to the vendor for %s (%s)" % (pat, no), vendor_payable(con, vid, cid), 0))
    rows.sort(key=lambda x: (x[0] or "", x[1]))''', '''    for cid, (day, pat, no) in done_cases.items():
        rows.append((day, "Actually due to the vendor for %s (%s)" % (pat, no), vendor_payable(con, vid, cid), 0))
    # S682: an old case settled by Dr Manoj on this page -- an amount owed either way enters the ledger dated that day
    for e in con.execute("SELECT e.*, c.case_no, c.patient, i.item FROM surg_implant_event e JOIN surg_implant i ON i.id=e.implant_id "
                         "JOIN surg_case c ON c.id=e.case_id WHERE e.kind='settled' AND i.vendor_id=? AND i.voided_at='' AND c.voided_at='' "
                         "AND e.amount_p IS NOT NULL AND e.amount_p<>0 ORDER BY e.day, e.id", (vid,)):
        owe = e["amount_p"] > 0
        rows.append((e["day"], "Old case settled · %s (%s, %s) · %s" % (e["patient"], e["case_no"], e["item"],
                                                                      "you still owed" if owe else "the vendor owed you"),
                     e["amount_p"] if owe else 0, 0 if owe else -e["amount_p"]))
    rows.sort(key=lambda x: (x[0] or "", x[1]))''', "ledger")
# ---------------------------------------------------------------- the supplier's page: bills, old cases, the payment's ticks
E('''    forms = ("<div class='card noprint'><h2>Write an entry</h2>"
             "<details><summary>Dr Manoj paid this vendor</summary><form method='post' action='%s/vendor/%d/pay'>"
             "<label>Date<input type=date name=day class='note' value='%s'></label><label>Amount (₹)<input name=amount class='amt' inputmode=decimal></label>"
             "<label>How</label><div class='chips'><label class='chip'><input type=radio name=mode value=cash checked> Cash</label>"
             "<label class='chip'><input type=radio name=mode value=bank> Bank</label><label class='chip'><input type=radio name=mode value=cheque> Cheque</label></div>"
             "<label>Note<input name=note class='note'></label><button class='save'>Write it</button></form></details>"''',
  '''    forms = ("<div class='card noprint'><h2>Write an entry</h2>"
             "<details open><summary>Dr Manoj paid this vendor</summary><form method='post' action='%s/vendor/%d/pay'>"
             "<label>Date<input type=date name=day class='note' value='%s'></label><label>Amount (₹)<input name=amount class='amt' inputmode=decimal></label>"
             "<label>How</label><div class='chips'><label class='chip'><input type=radio name=mode value=cash checked> Cash</label>"
             "<label class='chip'><input type=radio name=mode value=bank> Bank</label><label class='chip'><input type=radio name=mode value=cheque> Cheque</label></div>"
             "<label>Note<input name=note class='note'></label>%s<button class='save'>Write it</button></form></details>"''', "payform")
E('''        BASE, vid, today, BASE, vid, today, _esc(DEFAULT_HOSPITAL), _void_money(vid, pays, chqs))''',
  '''        BASE, vid, today, _settles_ticks(con, vid), BASE, vid, today, _esc(DEFAULT_HOSPITAL), _void_money(vid, pays, chqs))''', "payform-args")
# review 1 (2): a removed cheque steps its lines back
E('''    con.execute("UPDATE %s SET voided_at=?, voided_by=?, void_why=? WHERE id=?" % table, (_stamp(), who, why, r["id"]))
    con.commit()
    _audit_safe(con, table, r["id"], "void", dict(amount_p=r["amount_p"], day=r["day"]), dict(why=why), who)
    return _back("%s/vendor/%d" % (BASE, vid), msg="voided")''', '''    con.execute("UPDATE %s SET voided_at=?, voided_by=?, void_why=? WHERE id=?" % table, (_stamp(), who, why, r["id"]))
    con.commit()
    _audit_safe(con, table, r["id"], "void", dict(amount_p=r["amount_p"], day=r["day"]), dict(why=why), who)
    if kind == "cheque":                         # S682 (review 1): the lines tied to a removed cheque step back to Bill raised
        for iid in [x[0] for x in con.execute("SELECT implant_id FROM surg_cheque_alloc WHERE cheque_id=? AND implant_id IS NOT NULL", (r["id"],))]:
            _cheque_follow(con, iid, r, who)
    return _back("%s/vendor/%d" % (BASE, vid), msg="voided")''', "chequevoid")
# review 1 (3): an allocation to a removed implant line counts nowhere
E('''    for a in con.execute("SELECT a.*, q.day, q.cheque_no, q.from_whom, c.case_no, c.patient FROM surg_cheque_alloc a "
                         "JOIN surg_cheque q ON q.id=a.cheque_id JOIN surg_case c ON c.id=a.case_id "
                         "WHERE q.vendor_id=? AND q.voided_at='' ORDER BY q.day, a.id", (vid,)):''', '''    for a in con.execute("SELECT a.*, q.day, q.cheque_no, q.from_whom, c.case_no, c.patient FROM surg_cheque_alloc a "
                         "JOIN surg_cheque q ON q.id=a.cheque_id JOIN surg_case c ON c.id=a.case_id LEFT JOIN surg_implant i ON i.id=a.implant_id "
                         "WHERE q.vendor_id=? AND q.voided_at='' AND (a.implant_id IS NULL OR i.voided_at='') ORDER BY q.day, a.id", (vid,)):''', "ledger-alloc")
E('''        used = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM surg_cheque_alloc WHERE cheque_id=?", (q["id"],)).fetchone()[0] or 0
        if used < q["amount_p"]:
            unassigned.append((q, q["amount_p"] - used))''', '''        used = cheque_used(con, q["id"])
        if used < q["amount_p"]:
            unassigned.append((q, q["amount_p"] - used))''', "ledger-used")
E('''            "<div class='card'><h2>Credit patients still awaiting the vendor's cheque</h2><ul>%s</ul></div>"
            "<div class='card'><h2>Cheques not yet assigned to patients</h2><ul>%s</ul></div>%s%s") % (
        _esc(v["name"]), verdict, "".join(trs) or "<tr><td colspan=5 class=mut>No entries yet.</td></tr>", wait, una, forms,
        _hide_form(con, vid))''', '''            "<div class='card'><h2>Credit patients still awaiting the vendor's cheque</h2><ul>%s</ul></div>"
            "<div class='card'><h2>Cheques not yet assigned to patients</h2><ul>%s</ul></div>%s%s%s%s") % (
        _esc(v["name"]), verdict, "".join(trs) or "<tr><td colspan=5 class=mut>No entries yet.</td></tr>", wait, una,
        _supplier_bills(con, vid), _old_cases_card(con, vid), forms, _hide_form(con, vid))''', "vendorpage")
E('''    mode = f.get("mode") if f.get("mode") in ("cash", "bank", "cheque") else "cash"
    cur = con.execute("INSERT INTO surg_vendor_pay (vendor_id, day, amount_p, mode, note, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                      (vid, day, amt, mode, _txt(f.get("note"), 200), who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_vendor_pay", cur.lastrowid, "insert", None, dict(vendor_id=vid, day=day, amount_p=amt, mode=mode), who)
    return _back(back, msg="paid")''', '''    mode = f.get("mode") if f.get("mode") in ("cash", "bank", "cheque") else "cash"
    ticks = [int(k[7:]) for k in f.keys() if k.startswith("settle_") and k[7:].isdigit()]
    cur = con.execute("INSERT INTO surg_vendor_pay (vendor_id, day, amount_p, mode, note, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                      (vid, day, amt, mode, _txt(f.get("note"), 200), who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_vendor_pay", cur.lastrowid, "insert", None, dict(vendor_id=vid, day=day, amount_p=amt, mode=mode), who)
    _pay_settles(con, vid, cur.lastrowid, day, ticks, who)          # S682: the ticked cash lines move to "paid to the supplier"
    return _back(back, msg="paid")''', "paypost")
# ---------------------------------------------------------------- the cheque page: both logins, assigned by implant
E('''@bp.route(BASE + "/cheque/<int:qid>")
def cheque_page(qid):
    u, err = _owner()
    if err:
        return err
    con = _db()
    q = con.execute("SELECT q.*, v.name AS vendor FROM surg_cheque q JOIN surg_vendor v ON v.id=q.vendor_id WHERE q.id=? AND q.voided_at=''", (qid,)).fetchone()
    if not q:
        return _back(BASE + "/vendors", err="gone")
    now = {r["case_id"]: r["amount_p"] for r in con.execute("SELECT case_id, amount_p FROM surg_cheque_alloc WHERE cheque_id=?", (qid,))}
    rows = []
    for c in con.execute("SELECT DISTINCT c.* FROM surg_case c JOIN surg_implant i ON i.case_id=c.id WHERE i.vendor_id=? AND i.voided_at='' "
                         "AND c.voided_at='' AND c.payer<>'cash' ORDER BY c.surgery_date", (q["vendor_id"],)):
        bill = con.execute("SELECT COALESCE(SUM(bill_p),0) FROM surg_implant WHERE vendor_id=? AND case_id=? AND voided_at=''",
                           (q["vendor_id"], c["id"])).fetchone()[0]
        d = dict(c)
        d["hint_p"], d["now_p"] = bill, now.get(c["id"], 0)
        rows.append(d)
    used = sum(now.values())
    body = (_nav(True, "vendors") + _flash(request.args) +
            "<div class='card'><h2>Cheque %s · %s · %s</h2><p class='big'>%s from %s — assigned %s, left %s</p>"
            "<p class=mut>Write how much of this cheque was for each patient (the vendor's bill for that patient is shown). "
            "The cheque counts in your favour; what is actually due to the vendor for that patient counts against you.</p>"
            "<form method='post' action='%s/cheque/%d'><table class='grid'><thead><tr><th>Case</th><th>Patient</th><th>Payer</th><th>Surgery</th>"
            "<th class=r>Vendor's bill</th><th>From this cheque (₹)</th></tr></thead><tbody>%s</tbody></table>"
            "<button class='save'>Save</button></form><a class='btn' href='%s/vendor/%d'>← %s ledger</a></div>") % (
        _esc(q["cheque_no"]) or "—", _human(q["day"]), _esc(q["vendor"]), _r(q["amount_p"]), _esc(q["from_whom"]) or "—", _r(used),
        _r(q["amount_p"] - used), BASE, qid, _alloc_table(rows, "c") or "<tr><td colspan=6 class=mut>No credit patients with this vendor's implants yet.</td></tr>",
        BASE, q["vendor_id"], _esc(q["vendor"]))
    return _shell("Cheque", body)


@bp.route(BASE + "/cheque/<int:qid>", methods=["POST"])
def post_cheque_alloc(qid):
    u, err = _owner()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    q = con.execute("SELECT * FROM surg_cheque WHERE id=? AND voided_at=''", (qid,)).fetchone()
    if not q:
        return _back(BASE + "/vendors", err="gone")
    allowed = {r[0] for r in con.execute("SELECT DISTINCT c.id FROM surg_case c JOIN surg_implant i ON i.case_id=c.id WHERE i.vendor_id=? "
                                         "AND i.voided_at='' AND c.voided_at='' AND c.payer<>'cash'", (q["vendor_id"],))}
    al = _read_alloc(request.form, "c", allowed)
    back = "%s/cheque/%d" % (BASE, qid)
    if al is None:
        return _back(back, err="amount")
    if sum(al.values()) > q["amount_p"]:
        return _back(back, err="over")
    before = {r["case_id"]: r["amount_p"] for r in con.execute("SELECT case_id, amount_p FROM surg_cheque_alloc WHERE cheque_id=?", (qid,))}
    con.execute("DELETE FROM surg_cheque_alloc WHERE cheque_id=?", (qid,))
    for cid, p in al.items():
        con.execute("INSERT INTO surg_cheque_alloc (cheque_id, case_id, amount_p, by_whom, at) VALUES (?,?,?,?,?)", (qid, cid, p, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_cheque_alloc", qid, "assign", before, al, who)
    return _back(back, msg="alloc")''', '''@bp.route(BASE + "/cheque/<int:qid>")
def cheque_page(qid):
    """S682: open to both logins (the owner: a cheque is written and tied by "any of us"); assigned BY IMPLANT. An assignment made
    before this kit (by case, no implant) is shown as it is and kept."""
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    q = con.execute("SELECT q.*, v.name AS vendor FROM surg_cheque q JOIN surg_vendor v ON v.id=q.vendor_id WHERE q.id=? AND q.voided_at=''", (qid,)).fetchone()
    if not q:
        return _back(BASE + "/implants", err="gone")
    now = {r["implant_id"]: r["amount_p"] for r in con.execute("SELECT a.implant_id, a.amount_p FROM surg_cheque_alloc a JOIN surg_implant i ON i.id=a.implant_id "
                                                               "WHERE a.cheque_id=? AND i.voided_at=''", (qid,))}
    legacy = con.execute("SELECT a.amount_p, c.case_no, c.patient FROM surg_cheque_alloc a JOIN surg_case c ON c.id=a.case_id "
                         "WHERE a.cheque_id=? AND a.implant_id IS NULL", (qid,)).fetchall()
    rows = []
    for i in con.execute("SELECT i.*, c.case_no, c.patient, c.payer, c.payer_kind, c.surgery_date, c.insurer FROM surg_implant i JOIN surg_case c ON c.id=i.case_id "
                         "WHERE i.vendor_id=? AND i.voided_at='' AND c.voided_at='' AND c.payer<>'cash' ORDER BY c.surgery_date, i.id", (q["vendor_id"],)):
        other = con.execute("SELECT q2.cheque_no FROM surg_cheque_alloc a JOIN surg_cheque q2 ON q2.id=a.cheque_id WHERE a.implant_id=? AND a.cheque_id<>? "
                            "AND q2.voided_at='' LIMIT 1", (i["id"], qid)).fetchone()
        rows.append("<tr><td><a href='%s?case=%d'>%s</a></td><td>%s</td><td>%s</td><td class=d>%s</td><td>%s%s</td><td class=r>%s</td>"
                    "<td>%s</td></tr>" % (
                        BASE + "/implants", i["case_id"], _esc(i["case_no"]), _esc(i["patient"]), _esc(pword(i)), _human(i["surgery_date"]),
                        _esc(i["item"]), (" · " + _esc(_bill_words(con, i["id"]))) if bill_of_implant(con, i["id"]) else " · <span class='sm'>bill not raised</span>",
                        _r(i["bill_p"]), ("<span class='sm'>on cheque %s</span>" % _esc(other["cheque_no"] or "—")) if other else
                        "<input name='i%d' class='amt' inputmode=decimal value='%s'>" % (i["id"], _rin(now.get(i["id"])) if now.get(i["id"]) else "")))
    used = sum(now.values()) + sum(l["amount_p"] for l in legacy)
    leg = "".join("<li>%s · %s — %s <span class='sm'>(assigned by patient, before the desk)</span></li>" % (_esc(l["case_no"]), _esc(l["patient"]), _r(l["amount_p"]))
                  for l in legacy)
    body = (_nav(checker, "implants") + _flash(request.args) +
            "<div class='card'><h2>Cheque %s · %s · %s</h2><p class='big'>%s from %s — assigned %s, left %s</p>"
            "<p class=mut>Tie the bills this cheque clears: write the amount against each implant line (its bill is shown). "
            "A line with an amount moves to <b>Cheque received</b>; cleared again, it goes back to Bill raised.%s</p>%s"
            "<form method='post' action='%s/cheque/%d'><table class='grid'><thead><tr><th>Case</th><th>Patient</th><th>Payer</th><th>Surgery</th>"
            "<th>Implant · bill</th><th class=r>Bill</th><th>From this cheque (₹)</th></tr></thead><tbody>%s</tbody></table>"
            "<button class='save'>Save</button></form><a class='btn' href='%s/implants'>← Implant bills</a> %s</div>") % (
        _esc(q["cheque_no"]) or "—", _human(q["day"]), _esc(q["vendor"]), _r(q["amount_p"]), _esc(q["from_whom"]) or "—", _r(used),
        _r(q["amount_p"] - used),
        " The cheque counts in your favour on the ledger; what is actually due to the supplier for that patient counts against you." if checker else "",
        ("<ul>%s</ul>" % leg) if leg else "", BASE, qid,
        "".join(rows) or "<tr><td colspan=7 class=mut>No credit patients with this supplier's implants yet.</td></tr>",
        BASE, ("<a class='btn' href='%s/vendor/%d'>%s ledger</a>" % (BASE, q["vendor_id"], _esc(q["vendor"]))) if checker else "")
    return _shell("Cheque", body)


@bp.route(BASE + "/cheque/<int:qid>", methods=["POST"])
def post_cheque_alloc(qid):
    u, checker, err = _gate()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    q = con.execute("SELECT * FROM surg_cheque WHERE id=? AND voided_at=''", (qid,)).fetchone()
    if not q:
        return _back(BASE + "/implants", err="gone")
    allowed = {r[0]: r[1] for r in con.execute("SELECT i.id, i.case_id FROM surg_implant i JOIN surg_case c ON c.id=i.case_id WHERE i.vendor_id=? "
                                               "AND i.voided_at='' AND c.voided_at='' AND c.payer<>'cash'", (q["vendor_id"],))}
    al = _read_alloc(request.form, "i", set(allowed))
    back = "%s/cheque/%d" % (BASE, qid)
    if al is None:
        return _back(back, err="amount")
    legacy_p = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM surg_cheque_alloc WHERE cheque_id=? AND implant_id IS NULL", (qid,)).fetchone()[0] or 0
    if sum(al.values()) + legacy_p > q["amount_p"]:
        return _back(back, err="over")
    before = {r["implant_id"]: r["amount_p"] for r in con.execute("SELECT implant_id, amount_p FROM surg_cheque_alloc WHERE cheque_id=? AND implant_id IS NOT NULL", (qid,))}
    con.execute("DELETE FROM surg_cheque_alloc WHERE cheque_id=? AND implant_id IS NOT NULL", (qid,))
    for iid, p in al.items():
        con.execute("INSERT INTO surg_cheque_alloc (cheque_id, case_id, implant_id, amount_p, by_whom, at) VALUES (?,?,?,?,?,?)",
                    (qid, allowed[iid], iid, p, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_cheque_alloc", qid, "assign", before, al, who)
    for iid in set(before) | set(al):             # the lines follow: on the cheque -> cheque received; taken off -> bill raised
        _cheque_follow(con, iid, q, who)
    return _back(back, msg="alloc")''', "chequepage")

APPEND = '''

# ================================================================ S682 · IPD kit 4: the implant bills desk, the cheque, the settlement
EVENT_WORD = {"raised": "bill raised", "unraised": "bill removed", "cheque": "cheque received", "uncheque": "taken off the cheque",
              "handed": "paid to the supplier", "confirmed": "supplier confirmed", "settled": "old case settled", "step": "step changed"}


def bill_of_implant(con, iid):
    return con.execute("SELECT * FROM surg_implant_bill WHERE implant_id=? AND voided_at='' ORDER BY id DESC LIMIT 1", (iid,)).fetchone()


def _bill_words(con, iid):
    b = bill_of_implant(con, iid)
    if not b:
        return ""
    return "bill %s · %s" % (b["bill_no"] or "no number", _short(b["bill_day"]) if b["bill_day"] else "—")


def bill_scans(con, iid):
    return con.execute("SELECT * FROM surg_paper WHERE implant_id=? AND voided_at='' ORDER BY id", (iid,)).fetchall()


def cheque_of_implant(con, i):
    """The live cheque assignment of an implant -- by implant, else one made by case before this kit; None if none."""
    r = con.execute("SELECT a.*, q.cheque_no, q.day AS qday, q.from_whom, q.amount_p AS qamount FROM surg_cheque_alloc a JOIN surg_cheque q ON q.id=a.cheque_id "
                    "WHERE a.implant_id=? AND q.voided_at='' ORDER BY a.id DESC LIMIT 1", (i["id"],)).fetchone()
    if r:
        return r
    return con.execute("SELECT a.*, q.cheque_no, q.day AS qday, q.from_whom, q.amount_p AS qamount FROM surg_cheque_alloc a JOIN surg_cheque q ON q.id=a.cheque_id "
                       "WHERE a.case_id=? AND a.implant_id IS NULL AND q.vendor_id=? AND q.voided_at='' ORDER BY a.id DESC LIMIT 1",
                       (i["case_id"], i["vendor_id"])).fetchone()


def last_event(con, iid, kind):
    return con.execute("SELECT * FROM surg_implant_event WHERE implant_id=? AND kind=? ORDER BY id DESC LIMIT 1", (iid, kind)).fetchone()


def _step_to(con, i, step, who, kind, day="", amount_p=None, ref_id=None, note=""):
    """One implant's step moves, with its event; the case follows (S681); one audit row."""
    before = i["pay_status"] or "pending"
    con.execute("UPDATE surg_implant SET pay_status=? WHERE id=?", (step, i["id"]))
    con.execute("INSERT INTO surg_implant_event (implant_id, case_id, kind, day, amount_p, ref_id, note, by_whom, at) VALUES (?,?,?,?,?,?,?,?,?)",
                (i["id"], i["case_id"], kind, day or _today().isoformat(), amount_p, ref_id, _txt(note, 200), who, _stamp()))
    con.commit()
    _follow_implants(con, i["case_id"])
    _audit_safe(con, "surg_implant", i["id"], "pay_status", dict(pay_status=before), dict(pay_status=step, event=kind, ref_id=ref_id), who)


def _implant_live(con, iid):
    return con.execute("SELECT i.*, v.name AS vendor, c.case_no, c.patient, c.payer, c.payer_kind, c.insurer, c.surgery_date, c.backfill, c.ipd_no, c.uhid, c.mlc "
                       "FROM surg_implant i JOIN surg_vendor v ON v.id=i.vendor_id JOIN surg_case c ON c.id=i.case_id "
                       "WHERE i.id=? AND i.voided_at='' AND c.voided_at=''", (iid,)).fetchone()


def _cheque_follow(con, iid, q, who):
    i = _implant_live(con, iid)
    if not i:
        return
    on = con.execute("SELECT 1 FROM surg_cheque_alloc a JOIN surg_cheque q2 ON q2.id=a.cheque_id WHERE a.implant_id=? AND q2.voided_at=''", (iid,)).fetchone()
    st = i["pay_status"] or "pending"
    if on and IMPL_RANK[st] < IMPL_RANK["cheque"]:
        _step_to(con, i, "cheque", who, "cheque", q["day"], None, q["id"], "cheque %s from %s" % (q["cheque_no"] or "—", q["from_whom"] or "—"))
    elif not on and st == "cheque":
        _step_to(con, i, "raised" if bill_of_implant(con, iid) else "pending", who, "uncheque", _today().isoformat(), None, q["id"])


def desk_lines(con, vid=None, payer="", q="", case_id=None, old=False):
    """Every live implant line of the live cases (new cases on the desk; old ones only on the supplier's page), newest surgery last."""
    where = ["i.voided_at=''", "c.voided_at=''", "c.backfill=%d" % (1 if old else 0)]
    args = []
    if vid:
        where.append("i.vendor_id=?")
        args.append(vid)
    if payer == "cash":
        where.append("c.payer='cash'")
    elif payer == "credit":
        where.append("c.payer<>'cash'")
    if case_id:
        where.append("c.id=?")
        args.append(case_id)
    if q:
        like = "%" + q + "%"
        where.append("(c.patient LIKE ? OR c.case_no LIKE ? OR c.ipd_no LIKE ? OR c.uhid LIKE ? OR i.item LIKE ? OR v.name LIKE ? OR EXISTS "
                     "(SELECT 1 FROM surg_implant_bill b WHERE b.implant_id=i.id AND b.voided_at='' AND b.bill_no LIKE ?) OR EXISTS "
                     "(SELECT 1 FROM surg_cheque_alloc a JOIN surg_cheque q ON q.id=a.cheque_id WHERE a.implant_id=i.id AND q.voided_at='' AND q.cheque_no LIKE ?))")
        args += [like] * 8
    return con.execute("SELECT i.*, v.name AS vendor, c.case_no, c.patient, c.payer, c.payer_kind, c.insurer, c.surgery_date, c.backfill, c.ipd_no, c.uhid, c.mlc "
                       "FROM surg_implant i JOIN surg_vendor v ON v.id=i.vendor_id JOIN surg_case c ON c.id=i.case_id WHERE %s "
                       "ORDER BY c.surgery_date, i.id" % " AND ".join(where), args).fetchall()


def cheque_used(con, qid):
    """What of a cheque is tied: by case (before this kit) or by a LIVE implant line (an allocation to a removed line counts nowhere)."""
    return con.execute("SELECT COALESCE(SUM(a.amount_p),0) FROM surg_cheque_alloc a LEFT JOIN surg_implant i ON i.id=a.implant_id "
                       "WHERE a.cheque_id=? AND (a.implant_id IS NULL OR i.voided_at='')", (qid,)).fetchone()[0] or 0


def _open_cheques(con, vid):
    """[(cheque row, left_p)] -- this supplier's live cheques with something still unassigned."""
    out = []
    for q in con.execute("SELECT * FROM surg_cheque WHERE vendor_id=? AND voided_at='' ORDER BY day DESC, id DESC", (vid,)):
        used = cheque_used(con, q["id"])
        if used < q["amount_p"]:
            out.append((q, q["amount_p"] - used))
    return out


def _line_summary(i, step, checker, ret_q):
    b_words = ""
    credit = i["payer"] != "cash"
    pay = _esc(pword(i)) + ((" · " + _esc(i["insurer"])) if i["insurer"] else "")
    return ("<summary><span class='pcol'><b>%s</b> <span class='sm'>%s</span><br><span class='sm'>%s</span></span>"
            "<span class='scol'>%s<br><span class='sm'>%s</span></span><span>%s</span><span>%s%s</span><span class='r'>%s%s</span>"
            "<span><span class='chip %s'>%s</span></span></summary>") % (
        _esc(i["patient"]), _esc(i["case_no"]),
        " · ".join(x for x in (("IPD " + _esc(i["ipd_no"])) if i["ipd_no"] else "", ("UHID " + _esc(i["uhid"])) if i["uhid"] else "",
                               "<b class='warn'>MLC</b>" if i["mlc"] else "") if x) or "&nbsp;",
        _short(i["surgery_date"]) if i["surgery_date"] else "—", pay, _esc(i["vendor"]),
        _esc(i["item"]) + ((" ×%d" % i["qty"]) if i["qty"] != 1 else ""), b_words, _r(i["bill_p"]),
        " <span class='sm'>(estimate)</span>" if step == "pending" and i["bill_to"] == "doctor" else "",
        {"pending": "c-warn", "raised": "c-blue", "cheque": "c-blue", "paid": "c-ok", "confirmed": "c-ok"}.get(step, "c-grey"),
        BILL_STEP_WORD.get(step, step))


def _line_body(con, i, step, checker, ret):
    cid, iid = i["case_id"], i["id"]
    hid = _hid(ret)
    today = _today().isoformat()
    b = bill_of_implant(con, iid)
    scans = bill_scans(con, iid)
    rq = ("?ret=" + quote(ret, safe="")) if ret else ""
    scan_btn = "<a class='btn sec2' href='%s/implant/%d/scan%s'>📷 Scan the bill</a>" % (BASE, iid, rq)
    thumbs = "".join("<a class='thumb' href='%s/paper/%d' target=_blank>%s</a>" % (
        BASE, p["id"], ("<img src='%s/paper/%d' alt='' loading=lazy>" % (BASE, p["id"])) if p["mime"].startswith("image/") else "<span class='pdf'>PDF</span>")
        for p in scans)
    credit = i["payer"] != "cash"
    out = []
    if step == "pending":
        out.append(("<div class='act'><h4>The supplier's bill has come</h4><form method='post' action='%s/implant/%d/bill' class='row2'>%s"
                    "<label class='f'>Bill no.<input name=bill_no class='in s' required></label>"
                    "<label class='f'>Bill date<input type=date name=bill_day class='in s' value='%s' required></label>"
                    "<label class='f'>Amount (₹)<input name=amount class='in s amt' inputmode=decimal value='%s' required></label>"
                    "<label class='f'>In whose name<span class='chips'><label class='radio'><input type=radio name=bill_to value=patient%s> The patient's</label>"
                    "<label class='radio'><input type=radio name=bill_to value=doctor%s> Dr Manoj</label></span></label>"
                    "%s<button class='btn'>Bill raised — save</button></form>"
                    "<p class='sm'>Entered now as %s%s. If the bill says another figure, the line takes the bill's figure and the estimate is kept in the record. "
                    "Scan the bill before or after saving — the line shows it either way.</p>%s</div>") % (
            BASE, iid, hid, today, _rin(i["bill_p"]), " checked" if i["bill_to"] == "patient" else "", " checked" if i["bill_to"] != "patient" else "",
            scan_btn, _r(i["bill_p"]), " (estimate)" if i["bill_to"] == "doctor" else "", ("<div class='paps'>%s</div>" % thumbs) if thumbs else ""))
    else:
        out.append("<p class='sm'>%s%s %s</p>%s" % (_esc(_bill_words(con, iid)) if b else "bill: entered in section 2 of the case (no bill record)",
                                                    (" · in the %s name" % ("patient's" if b["bill_to"] == "patient" else "Dr Manoj's")) if b else "",
                                                    scan_btn if not scans else "", ("<div class='paps'>%s</div>" % thumbs) if thumbs else ""))
    if step == "raised":
        if credit:
            opts = "".join("<label class='radio'><input type=radio name=cheque_id value='%d'> Part of cheque %s (%s · %s · %s still unassigned)</label>" % (
                q["id"], _esc(q["cheque_no"] or "—"), _r(q["amount_p"]), _short(q["day"]), _r(left)) for q, left in _open_cheques(con, i["vendor_id"]))
            out.append(("<div class='act'><h4>The hospital's cheque to the supplier has come</h4><form method='post' action='%s/implant/%d/cheque' class='row2'>%s"
                        "<div class='chips' style='flex-basis:100%%'><label class='radio'><input type=radio name=cheque_id value='new' checked> A new cheque</label>%s</div>"
                        "<label class='f'>Cheque no.<input name=cheque_no class='in s'></label>"
                        "<label class='f'>Date<input type=date name=day class='in s' value='%s'></label>"
                        "<label class='f'>Cheque amount (₹)<input name=amount class='in s amt' inputmode=decimal placeholder='%s'></label>"
                        "<label class='f'>From<input name=from_whom class='in m' value='%s' list=ipd_from><datalist id=ipd_from><option value='%s'><option value='%s'></datalist></label>"
                        "<label class='f'>For this line (₹)<input name=part class='in s amt' inputmode=decimal value='%s'></label>"
                        "<button class='btn'>Cheque received — save</button></form>"
                        "<p class='sm'>A cheque that covers several patients is written once; the next patient's line offers it as \\"part of cheque …\\". "
                        "A cheque that came with no bill list can be written on its own, at the top of this page, and tied to its bills later.</p></div>") % (
                BASE, iid, hid, opts, today, _rin(i["bill_p"]), _esc(DEFAULT_HOSPITAL), _esc(DEFAULT_HOSPITAL), _esc(i["insurer"] or ""), _rin(i["bill_p"])))
        else:
            out.append("<div class='act'><h4>A cash case — Dr Manoj pays this supplier</h4><p class='sm' style='margin:0'>%s</p></div>" % (
                ("Write the payment on <a href='%s/vendor/%d'>the supplier's page</a> and tick this line there — it moves to Paid to the supplier." % (BASE, i["vendor_id"]))
                if checker else "Nothing for you here. When Dr Manoj writes his payment and ticks this line, it moves to <b>Paid to the supplier</b> by itself."))
        if b:
            out.append(("<details class='vd'><summary>Step back — the bill was wrong</summary><form method='post' action='%s/implant/%d/bill/void' class='row2'>%s%s"
                        "<button class='clear'>Remove the bill</button></form></details>") % (BASE, iid, hid, _why_chips()))
    if step == "cheque":
        ch = cheque_of_implant(con, i)
        if ch:
            out.append("<p class='sm'>Cheque %s · %s · %s from %s%s</p>" % (_esc(ch["cheque_no"] or "—"), _short(ch["qday"]), _r(ch["amount_p"]),
                                                                           _esc(ch["from_whom"] or "—"),
                                                                           (" · <a href='%s/cheque/%d'>the cheque's page</a>" % (BASE, ch["cheque_id"]))))
        out.append(("<div class='act'><h4>Handed to the supplier</h4><form method='post' action='%s/implant/%d/handed' class='row2'>%s"
                    "<label class='f'>On<input type=date name=day class='in s' value='%s'></label>"
                    "<label class='f grow'>Note<input name=note class='in' placeholder='who took it (optional)'></label>"
                    "<button class='btn'>Paid to the supplier — save</button></form></div>") % (BASE, iid, hid, today))
    if step == "paid":
        h = last_event(con, iid, "handed")
        if h:
            out.append("<p class='sm'>Paid %s%s</p>" % (_short(h["day"]), (" · " + _esc(h["note"])) if h["note"] else ""))
        out.append(("<div class='act'><h4>The supplier confirms</h4><form method='post' action='%s/implant/%d/confirm' class='row2'>%s"
                    "<label class='f'>On<input type=date name=day class='in s' value='%s'></label>"
                    "<label class='f grow'>How<input name=note class='in' placeholder='on the phone · on WhatsApp · signed the ledger copy'></label>"
                    "<button class='btn'>Supplier confirmed — save</button></form></div>") % (BASE, iid, hid, today))
    if step == "confirmed":
        cf = last_event(con, iid, "confirmed") or last_event(con, iid, "settled")
        if cf:
            out.append("<p class='sm'>Confirmed %s%s</p>" % (_short(cf["day"]), (" · " + _esc(cf["note"])) if cf["note"] else ""))
    out.append("<p class='sm'><a href='%s?open=%d#c%d'>Open the case</a></p>" % (BASE, cid, cid))
    return "<div class='lbody'>%s</div>" % "".join(out)


@bp.route(BASE + "/implants")
def implants_desk():
    """S682: the implant bills desk -- every implant line of the new cases, by step; each opens in place with its one entry."""
    u, checker, err = _gate()
    if err:
        return err
    con, a = _db(), request.args
    q = _txt(a.get("q"), 40)
    vid = int(a["v"]) if (a.get("v") or "").isdigit() else None
    payer = a.get("p") if a.get("p") in ("cash", "credit") else ""
    case_id = int(a["case"]) if (a.get("case") or "").isdigit() else None
    show = a.get("s") if a.get("s") in ("wait", "pending", "raised", "cheque", "paid", "confirmed") else "wait"
    lines = desk_lines(con, vid, payer, q, case_id)
    ret = BASE + "/implants?" + "&".join("%s=%s" % (k, quote(str(x), safe="")) for k, x in (("q", q), ("v", vid or ""), ("p", payer), ("case", case_id or ""), ("s", show)) if x)
    month_ago = (_today() - dt.timedelta(days=31)).isoformat()
    by = {k: [] for k in ("pending", "raised", "cheque", "paid", "confirmed")}
    for i in lines:
        st = i["pay_status"] or "pending"
        if st == "confirmed":
            cf = last_event(con, i["id"], "confirmed") or last_event(con, i["id"], "settled")
            if show != "confirmed" and cf and cf["day"] < month_ago:
                continue
        by.setdefault(st if st in by else "pending", []).append(i)
    waiting = len(by["pending"]) + len(by["raised"]) + len(by["cheque"]) + len(by["paid"])
    vendors = con.execute("SELECT id, name FROM surg_vendor WHERE hidden='' ORDER BY name").fetchall()
    opened = int(a["open"]) if (a.get("open") or "").isdigit() else None
    def qs(**kw):
        d = dict(q=q, v=vid or "", p=payer, case=case_id or "", s=show)
        d.update(kw)
        return BASE + "/implants?" + "&".join("%s=%s" % (k, quote(str(x), safe="")) for k, x in d.items() if x)
    chips = "".join("<a class='qc%s' href='%s'>%s <b>%d</b></a>" % (" on" if show == k else "", qs(s=k), w, n) for k, w, n in (
        ("wait", "Waiting", waiting), ("pending", "Not raised", len(by["pending"])), ("raised", "Bill raised", len(by["raised"])),
        ("cheque", "Cheque in", len(by["cheque"])), ("paid", "Paid", len(by["paid"])), ("confirmed", "Confirmed", len(by["confirmed"]))))
    out = [_nav(checker, "implants"), _flash(a)]
    out.append("<p class='sm'>The steps: %s.</p>" % " → ".join("<b>%s</b> (%s)" % (BILL_STEP_WORD[k], STEP_HINT[k]) for k in ("pending", "raised", "cheque", "paid", "confirmed")))
    if case_id:
        out.append("<p class='sm'>Only the implants of one case are shown. <a href='%s'>All lines</a></p>" % qs(case=""))
    out.append(("<div class='card' style='overflow:visible'><form method='get' action='%s/implants' class='row2'>"
                "<label class='f grow'>Find<input name=q class='in' type=search value='%s' placeholder='patient · case no. · bill no. · cheque no.'></label>"
                "<label class='f'>Supplier<select name=v class='in m'><option value=''>All suppliers</option>%s</select></label>"
                "<label class='f'>Payer<select name=p class='in s'><option value=''>All</option><option value='cash'%s>Cash</option><option value='credit'%s>Credit (TPA / Ayushman / scheme)</option></select></label>"
                "<input type=hidden name=s value='%s'><button class='btn sec2'>Show</button></form><div class='chips'>%s</div></div>") % (
        BASE, _esc(q), "".join("<option value='%d'%s>%s</option>" % (v["id"], " selected" if vid == v["id"] else "", _esc(v["name"])) for v in vendors),
        " selected" if payer == "cash" else "", " selected" if payer == "credit" else "", _esc(show), chips))
    # a cheque on its own (the owner, 07:39: "DTH cheques can be for multiple cases ... this is always not shared which bills were cleared")
    opens = []
    for v in vendors:
        for qrow, left in _open_cheques(con, v["id"]):
            opens.append("<li><a href='%s/cheque/%d'>Cheque %s · %s · %s from %s</a> — %s · %s not yet tied to bills</li>" % (
                BASE, qrow["id"], _esc(qrow["cheque_no"] or "—"), _short(qrow["day"]), _r(qrow["amount_p"]), _esc(qrow["from_whom"] or "—"), _esc(v["name"]), _r(left)))
    out.append(("<details class='card'%s><summary>A cheque that came on its own — write it, tie its bills later%s</summary><div class='sb'>"
                "<form method='post' action='%s/implants/cheque' class='row2'>%s"
                "<label class='f'>Made out to (supplier)<select name=vendor_id class='in m' required><option value=''>— choose —</option>%s</select></label>"
                "<label class='f'>Cheque no.<input name=cheque_no class='in s' required></label>"
                "<label class='f'>Date<input type=date name=day class='in s' value='%s' required></label>"
                "<label class='f'>Amount (₹)<input name=amount class='in s amt' inputmode=decimal required></label>"
                "<label class='f'>From<input name=from_whom class='in m' value='%s'></label>"
                "<label class='f grow'>Note<input name=note class='in' placeholder='optional'></label><button class='btn'>Write the cheque</button></form>"
                "<p class='sm'>Then open each patient's line below and choose \\"part of cheque …\\", or open the cheque and write the amounts against its lines.</p>"
                "%s</div></details>") % (
        " open" if opens else "", (" · <span class='chip c-warn'>%d with money not yet tied</span>" % len(opens)) if opens else "", BASE, _hid(ret),
        "".join("<option value='%d'>%s</option>" % (v["id"], _esc(v["name"])) for v in vendors), _today().isoformat(), _esc(DEFAULT_HOSPITAL),
        ("<h3>Cheques with money not yet tied to bills</h3><ul>%s</ul>" % "".join(opens)) if opens else ""))
    heads = {"pending": ("Bill not raised yet — the dealer has not sent the bill", "oldest first · enter the bill when it comes"),
             "raised": ("Bill raised — bill entry done, bill scanned", "awaiting the cheque, or Dr Manoj's payment"),
             "cheque": ("Cheque received — hand it to the supplier", ""), "paid": ("Paid to the supplier — awaiting the supplier's confirmation", ""),
             "confirmed": ("Supplier confirmed" + (" this month" if show != "confirmed" else ""), "")}
    order = ("pending", "raised", "cheque", "paid", "confirmed") if show in ("wait", "confirmed") else (show,)
    lhead = ("<div class='lhead'><span>Patient</span><span>Surgery · payer</span><span>Supplier</span><span>Implant</span>"
             "<span class='r'>Bill</span><span>Step</span></div>")
    any_ = False
    for st in order:
        items = by[st]
        if not items and show == "wait":
            continue
        any_ = any_ or (bool(items) and st != "confirmed")
        title, hint = heads[st]
        body = "".join("<details class='ln'%s id='i%d'>%s%s</details>" % (
            " open" if (opened == i["id"] or (len(items) == 1 and st in ("pending", "raised") and not opened and show != "wait")) else "",
            i["id"], _line_summary(i, st, checker, ret), _line_body(con, i, st, checker, ret + "&open=%d#i%d" % (i["id"], i["id"])))
            for i in items) or "<p class='sb sm'>None.</p>"
        out.append("<div class='grp'><div class='gh'>%s <span class='cnt'>%d implant%s%s</span></div>%s%s</div>" % (
            title, len(items), "" if len(items) == 1 else "s", (" · " + hint) if hint else "", lhead if items else "", body))
    if not any_ and show == "wait":
        out.append("<div class='card'><p>Nothing waiting on the desk%s.</p></div>" % (" for this search" if (q or vid or payer or case_id) else ""))
    out.append("<p class='sm'>Old cases (backfill) are not on this desk — Dr Manoj settles them one by one on the supplier's page. The implant's "
               "actual cost and what Dr Manoj pays a supplier are never shown here.</p>")
    return _shell("Implant bills", "<h1>Implant bills <span class=sm>· every implant, in the order the money moves</span></h1>" + "".join(out) + DESK_CSS)


DESK_CSS = """<style>
.grp{background:#fff;border:1px solid var(--line);border-radius:12px;margin:0 0 10px;overflow:hidden}
.gh{display:flex;gap:10px;align-items:center;padding:9px 14px;border-bottom:1px solid var(--soft);font-weight:700;color:var(--accent);flex-wrap:wrap}
.gh .cnt{margin-left:auto;font-weight:400;font-size:13px;color:var(--mut)}
.lhead,details.ln > summary{display:grid;grid-template-columns:2fr 1.1fr 1.5fr 1.7fr .9fr 1.4fr;gap:10px;align-items:start;padding:9px 14px;list-style:none;font-size:14px;color:var(--ink);font-weight:400}
details.ln > summary::-webkit-details-marker{display:none}
.lhead{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--mut);font-weight:600;border-bottom:1px solid var(--soft)}
details.ln{border-bottom:1px solid var(--soft)}details.ln:last-child{border-bottom:0}
details.ln > summary b{color:var(--accent)}details.ln[open] > summary{background:#eef4fa}
.lbody{padding:8px 14px 12px;background:#f6f8fa}
.act{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:6px 0}.act h4{margin:0 0 8px;font-size:14px;color:var(--accent)}
@media (max-width:760px){.lhead{display:none}details.ln > summary{display:flex;flex-wrap:wrap;gap:4px 10px}details.ln > summary > span{flex:1 1 auto}
.pcol,.scol{flex-basis:100%!important}.lbody{padding:6px 8px 10px}}
</style>"""


def _desk_ret(f, iid):
    return _ret_of(f, "%s/implants?open=%d#i%d" % (BASE, iid, iid))


@bp.route(BASE + "/implants/cheque", methods=["POST"])
def post_desk_cheque():
    """S682: a cheque written on its own, by any login of the page (the owner: 'any of us'); its bills are tied afterwards."""
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = _ret_of(f, BASE + "/implants")
    vid = int(f["vendor_id"]) if (f.get("vendor_id") or "").isdigit() else 0
    if not vid or not con.execute("SELECT 1 FROM surg_vendor WHERE id=?", (vid,)).fetchone():
        return _back(back, err="chqsup")
    day, amt, e = _money_form(f)
    if e:
        return _back(back, err=e)
    no = _txt(f.get("cheque_no"), 40)
    if not no:
        return _back(back, err="chq")
    cur = con.execute("INSERT INTO surg_cheque (vendor_id, day, amount_p, cheque_no, from_whom, note, by_whom, at) VALUES (?,?,?,?,?,?,?,?)",
                      (vid, day, amt, no, _txt(f.get("from_whom"), 80) or DEFAULT_HOSPITAL, _txt(f.get("note"), 200), who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_cheque", cur.lastrowid, "insert", None, dict(vendor_id=vid, day=day, amount_p=amt, via="desk"), who)
    return _back(back, msg="chqnew")


@bp.route(BASE + "/implant/<int:iid>/bill", methods=["POST"])
def post_implant_bill(iid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = _desk_ret(f, iid)
    i = _implant_live(con, iid)
    if not i:
        return _back(BASE + "/implants", err="gone")
    if i["backfill"]:
        return _back(back, err="oldonly")
    if (i["pay_status"] or "pending") != "pending" or bill_of_implant(con, iid):
        return _back(back, err="step")
    day = (f.get("bill_day") or "").strip()
    if not _iso_ok(day) or day > _today().isoformat():
        return _back(back, err="date")
    amt = _paise(f.get("amount"))
    if amt is False or not amt:
        return _back(back, err="amount")
    bill_to = f.get("bill_to") if f.get("bill_to") in ("patient", "doctor") else i["bill_to"]
    cur = con.execute("INSERT INTO surg_implant_bill (implant_id, case_id, vendor_id, bill_no, bill_day, amount_p, bill_to, note, by_whom, at) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?)", (iid, i["case_id"], i["vendor_id"], _txt(f.get("bill_no"), 40), day, amt, bill_to, _txt(f.get("note"), 200), who, _stamp()))
    if amt != i["bill_p"]:                       # the bill's figure replaces the estimate; the estimate is kept
        con.execute("UPDATE surg_implant SET estimate_p=COALESCE(estimate_p, bill_p), bill_p=?, bill_to=? WHERE id=?", (amt, bill_to, iid))
    elif bill_to != i["bill_to"]:
        con.execute("UPDATE surg_implant SET bill_to=? WHERE id=?", (bill_to, iid))
    con.commit()
    _audit_safe(con, "surg_implant_bill", cur.lastrowid, "insert", None, dict(implant_id=iid, amount_p=amt, bill_to=bill_to), who)
    _step_to(con, i, "raised", who, "raised", day, amt, cur.lastrowid, "bill %s" % (_txt(f.get("bill_no"), 40) or "—"))
    return _back(back, msg="ibill")


@bp.route(BASE + "/implant/<int:iid>/bill/void", methods=["POST"])
def post_implant_bill_void(iid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = _desk_ret(f, iid)
    i = _implant_live(con, iid)
    b = bill_of_implant(con, iid) if i else None
    if not i or not b:
        return _back(back, err="gone")
    if (i["pay_status"] or "pending") not in ("raised", "pending") or cheque_of_implant(con, i):
        return _back(back, err="step")
    if f.get("why") not in dict(VOID_WHY):
        return _back(back, err="why")
    con.execute("UPDATE surg_implant_bill SET voided_at=?, voided_by=?, void_why=? WHERE id=?", (_stamp(), who, f["why"], b["id"]))
    if i["estimate_p"] is not None:
        con.execute("UPDATE surg_implant SET bill_p=estimate_p, estimate_p=NULL WHERE id=?", (iid,))
    con.commit()
    _audit_safe(con, "surg_implant_bill", b["id"], "void", dict(amount_p=b["amount_p"]), dict(why=f["why"]), who)
    _step_to(con, i, "pending", who, "unraised", _today().isoformat(), None, b["id"], dict(VOID_WHY)[f["why"]])
    return _back(back, msg="unbill")


@bp.route(BASE + "/implant/<int:iid>/scan")
def implant_scan_page(iid):
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    i = _implant_live(con, iid)
    if not i:
        return _back(BASE + "/implants", err="gone")
    ret = _ret_of(request.args, "%s/implants?open=%d#i%d" % (BASE, iid, iid))
    frag = ""
    if "#" in ret:
        ret, frag = ret.split("#", 1)
        frag = "#" + frag
    return _scan_host("Supplier's bill — %s (%s) · %s" % (i["patient"], i["case_no"], i["item"]), "%s/api/implant/%d/paper" % (BASE, iid),
                      {"implant_id": str(iid)}, "%s_implant_bill_%d" % (i["case_no"], iid), ret + ("&" if "?" in ret else "?") + "msg=paper" + frag)


@bp.route(BASE + "/api/implant/<int:iid>/paper", methods=["POST"])
def api_implant_paper(iid):
    from flask import jsonify                    # noqa: PLC0415
    u, checker, err = _gate()
    if err:
        return jsonify(ok=False, error="not_permitted"), 403
    con, who = _db(), u.get("user", "")
    i = _implant_live(con, iid)
    if not i:
        return jsonify(ok=False, error="no_case"), 404
    c = case(con, i["case_id"])
    blob, e = _take_upload()
    if e:
        return jsonify(ok=False, error=e[0]), e[1]
    path, sha, mime = _store(blob, os.path.join((c["surgery_date"] or c["created_at"] or "0000")[:4], c["case_no"]), "%s_implant_bill_%d" % (c["case_no"], iid))
    if not path:
        return jsonify(ok=False, error="not_pdf_or_image", message="Only a PDF or a photo can be filed."), 415
    dup = con.execute("SELECT id FROM surg_paper WHERE implant_id=? AND sha256=? AND voided_at=''", (iid, sha)).fetchone()
    if dup:
        return jsonify(ok=True, duplicate=True, id=dup["id"])
    cur = con.execute("INSERT INTO surg_paper (case_id, implant_id, kind, path, sha256, bytes, mime, by_whom, at) VALUES (?,?,?,?,?,?,?,?,?)",
                      (i["case_id"], iid, "implant_bill", path, sha, len(blob), mime, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_paper", cur.lastrowid, "upload", None, dict(case_id=i["case_id"], implant_id=iid, kind="implant_bill", sha256=sha, bytes=len(blob)), who)
    return jsonify(ok=True, id=cur.lastrowid, sha256=sha[:12])


@bp.route(BASE + "/implant/<int:iid>/cheque", methods=["POST"])
def post_implant_cheque(iid):
    """S682: cheque received for one line -- a new cheque, or part of one already written (any login)."""
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = _desk_ret(f, iid)
    i = _implant_live(con, iid)
    if not i:
        return _back(BASE + "/implants", err="gone")
    if i["backfill"] or i["payer"] == "cash" or (i["pay_status"] or "pending") != "raised" or cheque_of_implant(con, i):
        return _back(back, err="step")
    part = _paise(f.get("part"), allow_blank=True)
    if part is False:
        return _back(back, err="amount")
    part = part or i["bill_p"]
    which = (f.get("cheque_id") or "new").strip()
    if which == "new":
        day, amt, e = _money_form(f)
        if e:
            return _back(back, err=e)
        no = _txt(f.get("cheque_no"), 40)
        if not no:
            return _back(back, err="chq")
        if part > amt:
            return _back(back, err="chqover")
        cur = con.execute("INSERT INTO surg_cheque (vendor_id, day, amount_p, cheque_no, from_whom, note, by_whom, at) VALUES (?,?,?,?,?,?,?,?)",
                          (i["vendor_id"], day, amt, no, _txt(f.get("from_whom"), 80) or DEFAULT_HOSPITAL, _txt(f.get("note"), 200), who, _stamp()))
        qid = cur.lastrowid
        con.commit()
        _audit_safe(con, "surg_cheque", qid, "insert", None, dict(vendor_id=i["vendor_id"], day=day, amount_p=amt, via="desk"), who)
    elif which.isdigit():
        qid = int(which)
        left = dict((q["id"], l) for q, l in _open_cheques(con, i["vendor_id"])).get(qid)
        if left is None:
            return _back(back, err="chq")
        if part > left:
            return _back(back, err="chqover")
    else:
        return _back(back, err="chq")
    q = con.execute("SELECT * FROM surg_cheque WHERE id=? AND voided_at=''", (qid,)).fetchone()
    con.execute("INSERT INTO surg_cheque_alloc (cheque_id, case_id, implant_id, amount_p, by_whom, at) VALUES (?,?,?,?,?,?)",
                (qid, i["case_id"], iid, part, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_cheque_alloc", qid, "assign", None, {iid: part}, who)
    _cheque_follow(con, iid, q, who)
    return _back(back, msg="ichq")


@bp.route(BASE + "/implant/<int:iid>/handed", methods=["POST"])
def post_implant_handed(iid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = _desk_ret(f, iid)
    i = _implant_live(con, iid)
    if not i:
        return _back(BASE + "/implants", err="gone")
    if i["backfill"] or (i["pay_status"] or "pending") != "cheque":
        return _back(back, err="step")
    day = (f.get("day") or "").strip()
    if not _iso_ok(day) or day > _today().isoformat():
        return _back(back, err="date")
    _step_to(con, i, "paid", who, "handed", day, None, None, f.get("note"))
    return _back(back, msg="handed")


@bp.route(BASE + "/implant/<int:iid>/confirm", methods=["POST"])
def post_implant_confirm(iid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = _desk_ret(f, iid)
    i = _implant_live(con, iid)
    if not i:
        return _back(BASE + "/implants", err="gone")
    if i["backfill"] or (i["pay_status"] or "pending") != "paid":
        return _back(back, err="step")
    day = (f.get("day") or "").strip()
    if not _iso_ok(day) or day > _today().isoformat():
        return _back(back, err="date")
    _step_to(con, i, "confirmed", who, "confirmed", day, None, None, f.get("note"))
    return _back(back, msg="confirmed")


@bp.route(BASE + "/implant/<int:iid>/settle", methods=["POST"])
def post_implant_settle(iid):
    """S682: an OLD case's implant settled by Dr Manoj alone, on the supplier's page (his answer 2, 07:40 IST)."""
    u, err = _owner()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    i = _implant_live(con, iid)
    if not i:
        return _back(BASE + "/vendors", err="gone")
    back = "%s/vendor/%d" % (BASE, i["vendor_id"])
    if not i["backfill"]:
        return _back(back, err="newonly")
    if (i["pay_status"] or "pending") == "confirmed":
        return _back(back, err="step")
    kind = f.get("how")
    if kind not in SETTLE_WORD:
        return _back(back, err="settle")
    amt = _paise(f.get("amount"), allow_blank=True)
    if amt is False or (kind != "clear" and not amt):
        return _back(back, err="settle")
    day = (f.get("day") or "").strip()
    if not _iso_ok(day) or day > _today().isoformat():
        return _back(back, err="date")
    signed = 0 if kind == "clear" else (amt if kind == "owe" else -amt)
    _step_to(con, i, "confirmed", who, "settled", day, signed, None, "%s%s" % (SETTLE_WORD[kind], (" · " + _txt(f.get("note"), 160)) if f.get("note") else ""))
    return _back(back, msg="settled")


def _pay_settles(con, vid, pay_id, day, ticks, who):
    for iid in ticks:
        i = _implant_live(con, iid)
        if not i or i["vendor_id"] != vid or i["payer"] != "cash" or i["backfill"] or (i["pay_status"] or "pending") in ("paid", "confirmed"):
            continue
        con.execute("INSERT INTO surg_pay_alloc (pay_id, implant_id, amount_p, by_whom, at) VALUES (?,?,?,?,?)", (pay_id, iid, i["bill_p"], who, _stamp()))
        con.commit()
        _step_to(con, i, "paid", who, "handed", day, i["bill_p"], pay_id, "paid by Dr Manoj")


def _settles_ticks(con, vid):
    """The cash lines of this supplier not yet paid -- ticked, this payment settles them (they move to 'paid to the supplier')."""
    rows = [i for i in desk_lines(con, vid, "cash") if (i["pay_status"] or "pending") not in ("paid", "confirmed")]
    if not rows:
        return "<p class='sm'>No cash line of this supplier is waiting to be paid.</p>"
    return ("<p style='margin:8px 0 4px'><b>This payment settles</b> <span class='sm'>— the ticked lines move to \\"Paid to the supplier\\"</span></p>"
            "<div class='chips' style='margin-bottom:8px'>%s</div>") % "".join(
        "<label class='radio'><input type=checkbox name='settle_%d' value=1> %s · %s · %s%s</label>" % (
            i["id"], _esc(i["patient"]), _esc(i["item"]), _r(i["bill_p"]), (" (" + _esc(_bill_words(con, i["id"])) + ")") if bill_of_implant(con, i["id"]) else " (no bill yet)")
        for i in rows)


def _supplier_bills(con, vid):
    rows = con.execute("SELECT b.*, i.item, i.pay_status, c.case_no, c.patient, c.payer, c.payer_kind, c.insurer FROM surg_implant_bill b JOIN surg_implant i ON i.id=b.implant_id "
                       "JOIN surg_case c ON c.id=b.case_id WHERE b.vendor_id=? AND b.voided_at='' AND i.voided_at='' AND c.voided_at='' "
                       "ORDER BY b.bill_day DESC, b.id DESC LIMIT 60", (vid,)).fetchall()
    trs = "".join("<tr><td class=d>%s · %s</td><td>%s <span class='sm'>%s · %s</span></td><td>%s%s</td><td class=r>%s</td><td><span class='chip %s'>%s</span></td></tr>" % (
        _esc(b["bill_no"] or "—"), _short(b["bill_day"]), _esc(b["patient"]), _esc(b["case_no"]), _esc(KIND_SHORT.get(kind_of(b), "")), _esc(b["item"]),
        "".join(" <a href='%s/paper/%d'>scan</a>" % (BASE, p["id"]) for p in bill_scans(con, b["implant_id"])), _r(b["amount_p"]),
        {"pending": "c-warn", "raised": "c-blue", "cheque": "c-blue"}.get(b["pay_status"] or "pending", "c-ok"), BILL_STEP_WORD.get(b["pay_status"] or "pending", "—"))
        for b in rows) or "<tr><td colspan=5 class=mut>No bill entered on the desk yet.</td></tr>"
    return ("<div class='card'><h2>Bills from this supplier</h2><table class='grid'><thead><tr><th>Bill</th><th>Patient</th><th>Implant</th><th class=r>Amount</th><th>Step</th></tr></thead>"
            "<tbody>%s</tbody></table><p class='sm'><a href='%s/implants?v=%d'>Open the implant bills desk for this supplier</a></p></div>") % (trs, BASE, vid)


def _old_cases_card(con, vid):
    rows = desk_lines(con, vid, old=True)
    if not rows:
        return ""
    today = _today().isoformat()
    trs = []
    for i in rows:
        st = i["pay_status"] or "pending"
        se = last_event(con, i["id"], "settled")
        if st == "confirmed":
            how = ("%s%s" % (_esc(se["note"]), (" · " + _r(abs(se["amount_p"]))) if se and se["amount_p"] else "")) if se else "confirmed before the desk"
            trs.append("<tr><td>%s <span class='sm'>%s · %s</span></td><td class=d>%s</td><td>%s</td><td class=r>%s</td><td><span class='chip c-ok'>Settled %s</span></td><td class='sm'>%s</td></tr>" % (
                _esc(i["patient"]), _esc(i["case_no"]), _esc(KIND_SHORT.get(kind_of(i), "")), _short(i["surgery_date"]), _esc(i["item"]), _r(i["bill_p"]),
                _short(se["day"]) if se else "", how))
            continue
        trs.append(("<tr><td>%s <span class='sm'>%s · %s</span></td><td class=d>%s</td><td>%s</td><td class=r>%s</td><td><span class='chip c-warn'>%s</span></td>"
                    "<td><details><summary>Settle</summary><form method='post' action='%s/implant/%d/settle' class='row2'>%s"
                    "<label class='f'>Amount (₹)<input name=amount class='in s amt' inputmode=decimal placeholder='if owed'></label>"
                    "<label class='f'>On<input type=date name=day class='in s' value='%s'></label>"
                    "<label class='f grow'>Note<input name=note class='in' placeholder='cheque no. · year · the statement line'></label>"
                    "<button class='btn'>Settle</button></form></details></td></tr>") % (
            _esc(i["patient"]), _esc(i["case_no"]), _esc(KIND_SHORT.get(kind_of(i), "")), _short(i["surgery_date"]), _esc(i["item"]), _r(i["bill_p"]),
            BILL_STEP_WORD.get(st, st), BASE, i["id"], _chips("how", SETTLE, "clear"), today))
    n_open = sum(1 for i in rows if (i["pay_status"] or "pending") != "confirmed")
    return ("<div class='card'><h2>Old cases with this supplier's implants — settle one by one</h2><p class='sm'>%d old case line%s%s. Each stays out of the "
            "balance until you settle it here; an amount owed either way then enters the ledger dated that day, and the line becomes Supplier confirmed. "
            "Nothing is compulsory.</p><table class='grid'><thead><tr><th>Patient</th><th>Surgery</th><th>Implant</th><th class=r>Bill (as entered)</th><th>Status</th><th></th></tr></thead>"
            "<tbody>%s</tbody></table></div>") % (len(rows), "" if len(rows) == 1 else "s", (" · %d to settle" % n_open) if n_open else " · all settled", "".join(trs))


def _settlement_block(con, c, checker, ims):
    """Section 6 on the case: each implant's bill, cheque, payment and confirmation; the desk one tap away."""
    cid = c["id"]
    if not ims:
        return "<p class='sm'>No implant on this case. The desk follows an implant once it is added in section 2.</p>"
    rows = []
    for i in ims:
        st = i["pay_status"] or "pending"
        b = bill_of_implant(con, i["id"])
        scans = bill_scans(con, i["id"])
        bill = ("✓ %s%s" % (_esc(_bill_words(con, i["id"])), "".join(" · <a href='%s/paper/%d' target=_blank>scan</a>" % (BASE, p["id"]) for p in scans))) if b else (
            "<span class='chip c-warn'>not raised</span>" if st == "pending" else "entered in section 2")
        ch = cheque_of_implant(con, i) if c["payer"] != "cash" else None
        chq = ("✓ %s · %s · %s" % (_esc(ch["cheque_no"] or "—"), _short(ch["qday"]), _r(ch["amount_p"]))) if ch else (
            "—" if c["payer"] == "cash" else ("<span class='chip c-warn'>awaited</span>" if st == "raised" else "—"))
        h = last_event(con, i["id"], "handed")
        paid = ("✓ %s%s" % (_short(h["day"]), (" · " + _esc(h["note"])) if h["note"] else "")) if h else ("✓" if st in ("paid", "confirmed") else "—")
        cf = last_event(con, i["id"], "confirmed") or last_event(con, i["id"], "settled")
        conf = ("✓ %s%s" % (_short(cf["day"]), (" · " + _esc(cf["note"])) if cf["note"] else "")) if cf else ("✓" if st == "confirmed" else "—")
        rows.append("<tr><td>%s</td><td>%s</td><td class=r>%s%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            _esc(i["item"]), _esc(i["vendor"]), _r(i["bill_p"]), (" <span class='sm'>(estimate was %s)</span>" % _r(i["estimate_p"])) if i["estimate_p"] is not None else "",
            bill, chq, paid, conf))
    if c["backfill"]:
        tail = ("<p class='sm'>An old case: its implants are settled by Dr Manoj on the supplier's page%s.</p>" % (
            " — <a href='%s/vendor/%d'>open it</a>" % (BASE, ims[0]["vendor_id"]) if checker else ""))
    else:
        tail = ("<p><a class='btn sm2' href='%s/implants?case=%d'>Open on the implant bills desk →</a> <span class='sm'>the next step is entered there "
                "(or the step changed by hand in section 2).</span></p>" % (BASE, cid))
    return ("<div class='tscroll'><table class='grid'><thead><tr><th>Implant</th><th>Supplier</th><th class=r>Bill</th><th>Bill raised</th><th>Cheque</th>"
            "<th>Paid to supplier</th><th>Confirmed</th></tr></thead><tbody>%s</tbody></table></div>%s") % ("".join(rows), tail)
'''

WORD = [(re.compile(r"\bVendors\b"), "Suppliers"), (re.compile(r"\bvendors\b"), "suppliers"),
        (re.compile(r"\bVendor\b"), "Supplier"), (re.compile(r"\bvendor\b"), "supplier")]
KEEP_URL = [("/suppliers", "/vendors"), ("/supplier/", "/vendor/"), ("\"suppliers\"", "\"vendors\""), ("'suppliers'", "'vendors'")]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    b = open(os.path.join(src, F), "rb").read()
    if hashlib.md5(b).hexdigest() != FROM_MD5:
        sys.exit("make_s682: %s is not the FROM file (%s) -- STOP" % (F, hashlib.md5(b).hexdigest()))
    t = b.decode("utf-8")
    for old, new, tag in EDITS:
        n = t.count(old)
        if n != 1:
            sys.exit("make_s682: edit %s found its anchor %d times -- STOP" % (tag, n))
        t = t.replace(old, new, 1)
        print("edit ok: %s" % tag)
    if "S682 · IPD kit 4" in t:
        sys.exit("make_s682: the desk is already in this file -- STOP")
    t = t.rstrip("\n") + "\n" + APPEND
    before = t
    for rx, rep in WORD:
        t = rx.sub(rep, t)
    for a, b_ in KEEP_URL:
        t = t.replace(a, b_)
    # the nav key and the route decorators keep their spelling (the addresses must not move)
    t = t.replace('("suppliers", BASE + "/vendors"', '("vendors", BASE + "/vendors"').replace('_nav(True, "suppliers")', '_nav(True, "vendors")')
    n_words = sum(1 for _ in re.finditer(r"\bvendors?\b", before, re.I)) - sum(1 for _ in re.finditer(r"\bvendors?\b", t, re.I))
    print("word pass: %d whole-word vendor/vendors -> supplier/suppliers; the addresses /vendors and /vendor/<id> kept" % n_words)
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, F), "wb") as fh:
        fh.write(t.encode("utf-8"))
    print("built %s %s" % (F, hashlib.md5(t.encode("utf-8")).hexdigest()))
    print("make_s682: %d counted edits + the appended desk + the word pass, each anchor found exactly once; 1 file written" % len(EDITS))


if __name__ == "__main__":
    main()
