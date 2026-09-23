#!/usr/bin/env python3
"""apply_s375.py -- kit S375_BANK_ENTRY. Anchored edits on sanjeevni_approvals.py e601d398 (S368 bytes) and
finance_ui/finance_approvals.html c6641ef6 (S368 bytes). D604, the owner, 22-Sep-2026:

  * he records a CASH DEPOSIT (the doctors' pool -> Yes Bank) himself -- until now only a session could;
  * he records a TRANSFER: ICICI Sanjeevni -> Yes Bank Sanjeevni, or either account -> its own HUF savings;
  * a transfer is NEVER income and NEVER touches a sale, a day or the cash calculation: the POS money is
    income on the day it is collected, and every later move changes the place, not the total;
  * money sent to an HUF savings account LEAVES the pharmacy's picture -- a withdrawal, not an expense;
  * ICICI's position is computed (settlements credited, less what has been moved out), never typed;
  * anything he records reads "waiting for the statement" until the bank's own statement covers it.

  python3 apply_s375.py --dir /root/finance [--out DIR]
"""
import argparse, hashlib, os
ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--out")
a = ap.parse_args()
OUT = a.out or a.dir

# ------------------------------------------------------------------ sanjeevni_approvals.py
p = os.path.join(a.dir, "sanjeevni_approvals.py"); s = open(p, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "e601d398b8dbc126fc64c0171b1e2e66", "sanjeevni_approvals.py is not e601d398"
def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)

rep('''VERSION = "1.0"''', '''VERSION = "1.1"''')
rep('''#      GET /finance/sanjeevni/api/needs-you      what needs the owner, in words, with a target''',
'''#  v1.1 (S375, D604, 22-Sep-2026): the owner records a cash deposit (pool -> Yes Bank) and a transfer
#  (ICICI -> Yes Bank, or either account -> its own HUF savings) himself. A transfer is never income and
#  never touches a day, a sale or the cash calculation; money to an HUF savings account leaves the
#  pharmacy's picture. ICICI's position is computed from the settlements ICICI has credited less what has
#  been moved out of it -- never typed. Everything recorded reads "waiting for the statement" until the
#  bank's own statement covers its date.
#
#      GET /finance/sanjeevni/api/needs-you      what needs the owner, in words, with a target''')
rep('''#      GET /finance/approvals/old                the page as it was (finance_approvals_old.html)''',
'''#      POST /finance/sanjeevni/api/bank/deposit  record a cash deposit from the pool     (checker)
#      POST /finance/sanjeevni/api/bank/transfer record a transfer between accounts      (checker)
#      POST /finance/sanjeevni/api/bank/undo     remove one unconfirmed entry you just made (checker)
#      GET /finance/approvals/old                the page as it was (finance_approvals_old.html)''')

rep('''ANCHOR_FLOOR = "2026-08-17"
DEP_KINDS = ("deposit_not_in_bank", "bank_deposit_not_booked", "deposit_unevidenced")''',
'''ANCHOR_FLOOR = "2026-08-17"
DEP_KINDS = ("deposit_not_in_bank", "bank_deposit_not_booked", "deposit_unevidenced")

# S375 (D604): the four accounts money can sit in or leave to. The two HUF savings accounts are
# OUTSIDE the pharmacy's books -- money reaching them has left, and is never an expense.
ACCOUNTS = {"icici": "ICICI Sanjeevni", "yesbank": "Yes Bank Sanjeevni",
            "huf_icici": "ICICI HUF savings", "huf_yesbank": "Yes Bank HUF savings"}
INSIDE = ("icici", "yesbank")
ROUTES = {("icici", "yesbank"), ("icici", "huf_icici"), ("yesbank", "huf_yesbank")}
TRANSFER_DDL = (
    "CREATE TABLE IF NOT EXISTS bank_transfer ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, transfer_date TEXT NOT NULL,"
    " from_account TEXT NOT NULL, to_account TEXT NOT NULL, amount_p INTEGER NOT NULL,"
    " ref TEXT, note TEXT, entered_by TEXT, entered_at TEXT,"
    " UNIQUE (unit, transfer_date, from_account, to_account, amount_p))")


def ensure_schema(con):
    """The one table this module owns. Created on first use; nothing else is touched."""
    con.execute(TRANSFER_DDL)


def _audit_row(con, who, action, detail):
    try:
        import json as _json
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) "
                    "VALUES (?,?,?,NULL,?,?,?)",
                    ("bank_entry", None, action, _json.dumps(detail, ensure_ascii=False), who,
                     dt.datetime.now().replace(microsecond=0).isoformat()))
    except Exception:  # noqa: BLE001 -- the record is the row itself; the audit is a courtesy
        pass


def transfers(con, unit=None):
    unit = unit or _unit
    if not _has(con, "bank_transfer"):
        return []
    return [dict(id=r[0], date=r[1], frm=r[2], to=r[3], amount_p=int(r[4]), ref=r[5] or "", note=r[6] or "",
                 by=r[7] or "", at=r[8] or "")
            for r in con.execute("SELECT id, transfer_date, from_account, to_account, amount_p, ref, note, "
                                 "entered_by, entered_at FROM bank_transfer WHERE unit=? "
                                 "ORDER BY transfer_date, id", (unit,))]''')

# ---- the bank view: two accounts, the transfers, the positions
rep('''def bank_view(con, ym):
    upi = []''',
'''def _statement_covers(con, iso):
    if not _has(con, "bank_statement_period"):
        return False
    return con.execute("SELECT 1 FROM bank_statement_period WHERE period_from<=? AND period_to>=?",
                       (iso, iso)).fetchone() is not None


def _seen_in_yesbank(con, iso, amount_p, deposit):
    """Does the loaded Yes Bank statement show this money, within three days either way?"""
    if not _has(con, "bank_statement_line"):
        return False
    col = "deposit_p" if deposit else "withdrawal_p"
    lo = (dt.date.fromisoformat(iso) - dt.timedelta(days=0)).isoformat()
    hi = (dt.date.fromisoformat(iso) + dt.timedelta(days=3)).isoformat()
    return con.execute("SELECT 1 FROM bank_statement_line WHERE %s=? AND txn_date BETWEEN ? AND ?" % col,
                       (amount_p, lo, hi)).fetchone() is not None


def icici_position(con, unit=None):
    """What ICICI holds, computed and never typed: every POS settlement it has credited since the anchor,
    less every transfer recorded out of it. The bank's own statement is not read here (S375 has no reader
    yet), so the figure says how it was made."""
    unit = unit or _unit
    credited = int(con.execute("SELECT COALESCE(SUM(parsed_total_p),0) FROM upi_statement WHERE unit=? "
                               "AND statement_date>=?", (unit, ANCHOR_FLOOR)).fetchone()[0] or 0)
    out = sum(t["amount_p"] for t in transfers(con, unit) if t["frm"] == "icici")
    last = con.execute("SELECT MAX(statement_date) FROM upi_statement WHERE unit=?", (unit,)).fetchone()[0]
    return dict(credited_p=credited, out_p=out, holds_p=credited - out, since=ANCHOR_FLOOR, upto=last)


def bank_view(con, ym):
    upi = []''')

rep('''    deposits.sort(key=lambda z: z["date"])
    return dict(ok=True, month=ym, upi=upi, upi_total=rs(upi_total), upi_days=len(upi),
                statement=period, deposits=deposits,
                banked_total=rs(sum(x["amount_p"] for x in pool)))''',
'''    deposits.sort(key=lambda z: z["date"])
    # ---- S375: the transfers he has recorded, each with what the statement says --------
    moves = []
    for t in transfers(con):
        if t["frm"] == "yesbank" or t["to"] == "yesbank":
            deposit = (t["to"] == "yesbank")
            if _seen_in_yesbank(con, t["date"], t["amount_p"], deposit):
                st, txt = "ok", "confirmed in the Yes Bank statement"
            elif _statement_covers(con, t["date"]):
                st, txt = "bad", "NOT in the Yes Bank statement"
            else:
                st, txt = "wait", "no Yes Bank statement covers this date yet"
        else:
            st, txt = "wait", "the ICICI statement for this date has not been read yet"
        moves.append(dict(id=t["id"], date=t["date"], day=dmy(t["date"]), amount=rs(t["amount_p"]),
                          frm=ACCOUNTS.get(t["frm"], t["frm"]), to=ACCOUNTS.get(t["to"], t["to"]),
                          frm_key=t["frm"], to_key=t["to"], ref=t["ref"],
                          leaves=(t["to"] not in INSIDE), status=st, text=txt))
    ip = icici_position(con)
    return dict(ok=True, month=ym, upi=upi, upi_total=rs(upi_total), upi_days=len(upi),
                statement=period, deposits=deposits, transfers=moves,
                icici=dict(holds=rs(ip["holds_p"]), credited=rs(ip["credited_p"]), out=rs(ip["out_p"]),
                           since=dmy(ip["since"]), upto=(dmy(ip["upto"]) if ip["upto"] else None)),
                accounts=ACCOUNTS,
                banked_total=rs(sum(x["amount_p"] for x in pool)))''')

rep('''        deposits.append(dict(date=x["date"], day=dmy(x["date"]), amount=rs(x["amount_p"]), place=x["place"] or "",
                             source="pool", status=st, text=txt))''',
'''        deposits.append(dict(id=x["id"], date=x["date"], day=dmy(x["date"]), amount=rs(x["amount_p"]),
                             place=x["place"] or "", source="pool", status=st, text=txt))''')

# ---- the three write doors
rep('''@bp.route("/finance/approvals/old")''',
'''def _amount_p(v):
    """Rupees from the page -> paise. Refuses anything that is not a positive amount."""
    try:
        p = int(round(float(str(v).replace(",", "").replace("\\u20b9", "").strip()) * 100))
    except (TypeError, ValueError):
        return None
    return p if p > 0 else None


def _good_date(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
    except (TypeError, ValueError):
        return None
    if d > dt.date.today() or d.isoformat() < ANCHOR_FLOOR:
        return None
    return d.isoformat()


@bp.route("/finance/sanjeevni/api/bank/deposit", methods=["POST"])
def api_deposit():
    """The doctors' pool -> Yes Bank, in his own hand. It leaves the pool at once (the one calculation
    reads cash_pool_deposit); the Yes Bank statement proves it later."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso, amt = _good_date(b.get("date")), _amount_p(b.get("amount"))
    if not iso or not amt:
        return jsonify(ok=False, error="bad_entry",
                       message="a date on or after 17-Aug-2026 and not in the future, and an amount"), 400
    con = _db()
    if not _has(con, "cash_pool_deposit"):
        return jsonify(ok=False, error="no_table", message="the cash tables are not installed on this box"), 503
    if con.execute("SELECT 1 FROM cash_pool_deposit WHERE unit=? AND deposit_date=? AND amount_p=?",
                   (_unit, iso, amt)).fetchone():
        return jsonify(ok=False, error="already",
                       message="a deposit of this amount on this date is already recorded"), 409
    who = u.get("user") or "owner"
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("INSERT INTO cash_pool_deposit (unit, deposit_date, amount_p, bank, place, evidence, note, "
                "entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (_unit, iso, amt, str(b.get("bank") or "Yes Bank")[:40], str(b.get("place") or "")[:60],
                 "recorded by the owner on the approvals page (S375)", str(b.get("note") or "")[:200], who, now))
    _audit_row(con, who, "pool_deposit", dict(date=iso, amount_p=amt, bank=str(b.get("bank") or "Yes Bank")))
    con.commit()
    return jsonify(ok=True, date=iso, amount=rs(amt))


@bp.route("/finance/sanjeevni/api/bank/transfer", methods=["POST"])
def api_transfer():
    """ICICI -> Yes Bank, or either account -> its own HUF savings. NEVER income, never a day, never the
    cash calculation: this money was counted when it was collected."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso, amt = _good_date(b.get("date")), _amount_p(b.get("amount"))
    frm, to = str(b.get("from") or "").strip(), str(b.get("to") or "").strip()
    if not iso or not amt:
        return jsonify(ok=False, error="bad_entry",
                       message="a date on or after 17-Aug-2026 and not in the future, and an amount"), 400
    if (frm, to) not in ROUTES:
        return jsonify(ok=False, error="bad_route",
                       message="a transfer goes ICICI to Yes Bank, or either account to its own HUF savings"), 400
    con = _db()
    ensure_schema(con)
    if con.execute("SELECT 1 FROM bank_transfer WHERE unit=? AND transfer_date=? AND from_account=? "
                   "AND to_account=? AND amount_p=?", (_unit, iso, frm, to, amt)).fetchone():
        return jsonify(ok=False, error="already",
                       message="this transfer is already recorded"), 409
    if frm == "icici":
        ip = icici_position(con)
        if amt > ip["holds_p"]:
            return jsonify(ok=False, error="over_balance",
                           message="ICICI has collected %s since 17-Aug and %s has already been moved out; "
                                   "this transfer of %s is more than the %s it holds. Check the amount."
                                   % (rs(ip["credited_p"]), rs(ip["out_p"]), rs(amt), rs(ip["holds_p"]))), 409
    who = u.get("user") or "owner"
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("INSERT INTO bank_transfer (unit, transfer_date, from_account, to_account, amount_p, ref, "
                "note, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (_unit, iso, frm, to, amt, str(b.get("ref") or "")[:60], str(b.get("note") or "")[:200], who, now))
    _audit_row(con, who, "bank_transfer", dict(date=iso, amount_p=amt, frm=frm, to=to))
    con.commit()
    return jsonify(ok=True, date=iso, amount=rs(amt), frm=ACCOUNTS.get(frm, frm), to=ACCOUNTS.get(to, to),
                   leaves=(to not in INSIDE))


@bp.route("/finance/sanjeevni/api/bank/undo", methods=["POST"])
def api_undo():
    """Remove one entry he made by mistake -- only while no loaded statement shows it."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    kind, rid = str(b.get("kind") or ""), b.get("id")
    con = _db()
    who = u.get("user") or "owner"
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_id"), 400
    if kind == "deposit":
        r = con.execute("SELECT deposit_date, amount_p FROM cash_pool_deposit WHERE id=? AND unit=?",
                        (rid, _unit)).fetchone()
        if not r:
            return jsonify(ok=False, error="not_found"), 404
        if _seen_in_yesbank(con, r[0], int(r[1]), True):
            return jsonify(ok=False, error="confirmed",
                           message="the bank's statement shows this deposit, so it cannot be removed"), 409
        con.execute("DELETE FROM cash_pool_deposit WHERE id=?", (rid,))
        _audit_row(con, who, "pool_deposit_undo", dict(id=rid, date=r[0], amount_p=int(r[1])))
    elif kind == "transfer":
        ensure_schema(con)
        r = con.execute("SELECT transfer_date, amount_p, from_account, to_account FROM bank_transfer "
                        "WHERE id=? AND unit=?", (rid, _unit)).fetchone()
        if not r:
            return jsonify(ok=False, error="not_found"), 404
        if (r[2] == "yesbank" or r[3] == "yesbank") and _seen_in_yesbank(con, r[0], int(r[1]), r[3] == "yesbank"):
            return jsonify(ok=False, error="confirmed",
                           message="the bank's statement shows this transfer, so it cannot be removed"), 409
        con.execute("DELETE FROM bank_transfer WHERE id=?", (rid,))
        _audit_row(con, who, "bank_transfer_undo", dict(id=rid, date=r[0], amount_p=int(r[1])))
    else:
        return jsonify(ok=False, error="bad_kind"), 400
    con.commit()
    return jsonify(ok=True)


@bp.route("/finance/approvals/old")''')
open(os.path.join(OUT, "sanjeevni_approvals.py"), "w", encoding="utf-8").write(s)
print("sanjeevni_approvals.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())

# ------------------------------------------------------------------ the page
p2 = os.path.join(a.dir, "finance_ui", "finance_approvals.html"); h = open(p2, encoding="utf-8").read()
assert hashlib.md5(h.encode("utf-8")).hexdigest() == "c6641ef673a6aec7ee08160fdbaf074e", "finance_approvals.html is not c6641ef6"
def reph(old, new):
    global h
    assert h.count(old) == 1, old[:70]
    h = h.replace(old, new)

reph('''<div class="card tree" id="bankCard"><h2><span class="kick">The bank's own record, pharmacy only</span>Bank</h2>
<div id="bank">loading&hellip;</div></div>''',
'''<div class="card tree" id="bankCard"><h2><span class="kick">Two accounts · the bank's own record</span>Bank</h2>
<div class="row noprint" style="gap:6px">
  <button class="ghost" onclick="bankForm('deposit')">Record a cash deposit</button>
  <button class="ghost" onclick="bankForm('transfer')">Record a transfer</button>
</div>
<div id="bankForm"></div>
<div id="bank">loading&hellip;</div>
<div class="note">A transfer moves money between your own accounts — it is never a sale and never income; the day it was collected is where it counted. Money sent to an HUF savings account leaves this picture altogether.</div></div>''')

reph('''    var h='';
    var st=j.statement;
    h+='<details class="mon" open><summary>Yes Bank <span class="mut" style="font-weight:400">· '+''',
'''    var h='';
    var ic=j.icici||{};
    h+='<details class="mon" open><summary>ICICI Sanjeevni <span class="mut" style="font-weight:400">· holds about ₹'+esc(ic.holds||"0")+
       ' — ₹'+esc(ic.credited||"0")+' collected since '+esc(ic.since||"")+(ic.upto?(' (to '+esc(ic.upto)+')'):'')+
       ', ₹'+esc(ic.out||"0")+' moved out</span></summary>'+
       '<div class="mut" style="font-size:12px;padding:2px 0 6px">Worked out from the bank\\'s own daily settlement files, less the transfers you have recorded. The ICICI account statement is not read yet, so this is our count, not the bank\\'s.</div></details>';
    var st=j.statement;
    h+='<details class="mon" open><summary>Yes Bank <span class="mut" style="font-weight:400">· '+''')

reph('''    h+='</tbody></table></div>'+(st?'<div class="mut" style="font-size:12px">Statement '+esc(st.from_day)+' → '+esc(st.to_day)+' · opening ₹'+esc(st.opening)+' · closing ₹'+esc(st.closing)+' · loaded '+esc(st.loaded_at)+'. ':'')+
       '<a href="/finance/workbench">Load a newer statement (PDF) ↗</a></div></details>';''',
'''    h+='</tbody></table></div>'+(st?'<div class="mut" style="font-size:12px">Statement '+esc(st.from_day)+' → '+esc(st.to_day)+' · opening ₹'+esc(st.opening)+' · closing ₹'+esc(st.closing)+' · loaded '+esc(st.loaded_at)+'. ':'')+
       '<a href="/finance/workbench">Load a newer statement (PDF) ↗</a></div></details>';
    var mv=j.transfers||[];
    h+='<details class="mon"'+(mv.length?' open':'')+'><summary>Transfers between your accounts <span class="mut" style="font-weight:400">· '+
       (mv.length?(mv.length+' recorded'):'none recorded yet')+'</span></summary><div class="tblwrap"><table><thead><tr><th>date</th><th class="num">amount</th><th>from → to</th><th>the statement says</th><th class="act"></th></tr></thead><tbody>';
    if(!mv.length) h+='<tr><td colspan="5" class="mut">nothing recorded yet — use “Record a transfer” above</td></tr>';
    mv.forEach(function(t){
      var ic2=t.status==="ok"?'<span class="ok">✓</span>':(t.status==="bad"?'<span class="bad">✗</span>':'<span class="mut">⏳</span>');
      h+='<tr><td>'+esc(t.day)+'</td><td class="num">₹'+esc(t.amount)+'</td><td>'+esc(t.frm)+' → '+esc(t.to)+
         (t.leaves?' <span class="pill">leaves the pharmacy</span>':'')+(t.ref?' <span class="sub">'+esc(t.ref)+'</span>':'')+'</td>'+
         '<td>'+ic2+' '+esc(t.text)+'</td><td class="act">'+(t.status==="ok"?'':'<button class="ghost" onclick="bankUndo(\\'transfer\\','+t.id+')">remove</button>')+'</td></tr>';
    });
    h+='</tbody></table></div></details>';''')

reph('''function bankShift(n){''',
'''/* ---- S375: he records a deposit or a transfer ---- */
function bankForm(kind){
  var el=$("bankForm"); if(!el)return;
  var today=(new Date()).toISOString().slice(0,10);
  if(kind==="deposit"){
    el.innerHTML='<div class="logbox"><b>Cash deposit into Yes Bank</b> '+
      '<input type="date" id="bfDate" value="'+today+'"> ₹<input type="number" id="bfAmt" placeholder="amount"> '+
      '<input type="text" id="bfPlace" size="12" placeholder="branch (optional)"> '+
      '<button onclick="bankSave(\\'deposit\\')">Record it</button>'+
      '<button class="ghost" onclick="$(\\'bankForm\\').innerHTML=\\'\\'">cancel</button>'+
      '<span class="mut">It leaves the doctors’ pool at once; the Yes Bank statement proves it later.</span></div>';
  }else{
    el.innerHTML='<div class="logbox"><b>Transfer between your accounts</b> '+
      '<input type="date" id="bfDate" value="'+today+'"> ₹<input type="number" id="bfAmt" placeholder="amount"> '+
      '<select id="bfRoute">'+
      '<option value="icici|yesbank">ICICI Sanjeevni → Yes Bank Sanjeevni</option>'+
      '<option value="icici|huf_icici">ICICI Sanjeevni → ICICI HUF savings</option>'+
      '<option value="yesbank|huf_yesbank">Yes Bank Sanjeevni → Yes Bank HUF savings</option></select> '+
      '<input type="text" id="bfRef" size="12" placeholder="reference (optional)"> '+
      '<button onclick="bankSave(\\'transfer\\')">Record it</button>'+
      '<button class="ghost" onclick="$(\\'bankForm\\').innerHTML=\\'\\'">cancel</button>'+
      '<span class="mut">Never a sale and never income — it only moves money you already counted.</span></div>';
  }
}
function bankSave(kind){
  var d=$("bfDate").value, v=$("bfAmt").value;
  if(!d||!v){alert("a date and an amount, please");return}
  var body={date:d, amount:v};
  var url="/finance/sanjeevni/api/bank/"+kind;
  if(kind==="deposit"){ body.place=($("bfPlace")||{}).value||""; }
  else { var r=($("bfRoute").value||"").split("|"); body.from=r[0]; body.to=r[1]; body.ref=($("bfRef")||{}).value||""; }
  fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})
    .then(srvJSON).then(function(x){var j=x.j||{};
      if(!j.ok){alert(j.message||j.error||"could not record it");return}
      $("bankForm").innerHTML=""; loadBank(); loadCashPos(); loadNeeds(); loadDays();
    }).catch(function(e){alert("nothing was recorded — the server could not be reached ("+e+")")});
}
function bankUndo(kind,id){
  fetch("/finance/sanjeevni/api/bank/undo",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({kind:kind,id:id})})
    .then(srvJSON).then(function(x){var j=x.j||{};
      if(!j.ok){alert(j.message||j.error||"could not remove it");return}
      loadBank(); loadCashPos(); loadNeeds(); loadDays();
    }).catch(function(e){alert("nothing was removed — the server could not be reached ("+e+")")});
}
function bankShift(n){''')

# the deposits table gets its own remove button for an unconfirmed entry
reph('''      h+='<tr><td>'+esc(d.day)+'</td><td class="num">₹'+esc(d.amount)+'</td><td class="hide-sm">'+esc(d.place)+'</td><td>'+ic+' '+esc(d.text)+'</td></tr>';''',
'''      h+='<tr><td>'+esc(d.day)+'</td><td class="num">₹'+esc(d.amount)+'</td><td class="hide-sm">'+esc(d.place)+'</td><td>'+ic+' '+esc(d.text)+
         (d.source==="pool"&&d.status!=="ok"&&d.id?'<button class="ghost noprint" style="margin-left:6px" onclick="bankUndo(\\'deposit\\','+d.id+')">remove</button>':'')+'</td></tr>';''')

reph('''<!-- finance_approvals.html · kit S368_APPROVALS_TREE''',
'''<!-- S375_BANK_ENTRY (Session 281, 22-Sep-2026, D604): Bank carries BOTH accounts — ICICI Sanjeevni
     (its position worked out from the settlement files, less what has been moved out) and Yes Bank — and the
     owner records a cash deposit (pool → Yes Bank) or a transfer (ICICI → Yes Bank · either → its own HUF
     savings) himself. A transfer is never income; money to an HUF savings account leaves the picture.
  -- kit S368 header below --
<!-- finance_approvals.html · kit S368_APPROVALS_TREE''')

open(os.path.join(OUT, "finance_ui", "finance_approvals.html"), "w", encoding="utf-8").write(h)
print("finance_approvals.html ->", hashlib.md5(h.encode("utf-8")).hexdigest())
