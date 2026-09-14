# ===================================================================== S270
# THE CHEQUE REGISTER
#
# D513 has two halves. The first was built at S261-S263: a vendor who is not on
# the authorised NEFT register never enters the NEFT file, and is named on the
# sheet as a cheque. The second half has been a promise until now -- "and the
# cheque is logged". Nowhere logged it. A cheque left the clinic and the only
# record of its number was the counterfoil in a drawer.
#
# This is that register. Cheque number, the date it was written, the payee, the
# vendor it settles and the amount -- against the month, beside the NEFT lane.
#
# THREE THINGS IT DOES THAT A COUNTERFOIL CANNOT
#
#   1  IT REFUSES A NUMBER USED TWICE.  A live cheque number is unique in this
#      register. Two cheques written on one number is the single error a paper
#      book never catches and a bank always does, weeks later.
#   2  IT RECONCILES TO THE SHEET.  The sheet says what the cheque lane owes.
#      The register says what has actually been written. The difference is named
#      on the page, with the vendors still waiting, and it is never swallowed.
#   3  IT IS APPENDED, NEVER ERASED.  A cheque entered wrongly is VOIDED with a
#      reason and stays on the register for ever -- the same rule as the flags.
#
# A DELIBERATE DEPARTURE, AND WHY
#
# Every other write on this sheet refuses once the month is FINAL. This one does
# not, and must not: a cheque is written AFTER the month locks, which is the
# whole point of locking. Logging a cheque records something that has already
# happened -- it moves no figure on the sheet, and the sheet's own lock is
# untouched. The month is shown on every row so a late entry is never silent.

CHEQUE_SQL = """CREATE TABLE IF NOT EXISTS purchase_cheque (
  id           INTEGER PRIMARY KEY,
  month        TEXT NOT NULL,
  vendor_norm  TEXT NOT NULL,
  vendor       TEXT NOT NULL,
  payee        TEXT NOT NULL,
  cheque_no    TEXT NOT NULL,
  cheque_date  TEXT NOT NULL,
  amount_p     INTEGER NOT NULL,
  bank         TEXT,
  note         TEXT,
  handed_at    TEXT,
  handed_by    TEXT,
  created_at   TEXT NOT NULL,
  created_by   TEXT NOT NULL,
  voided_at    TEXT,
  voided_by    TEXT,
  void_reason  TEXT
);
CREATE INDEX IF NOT EXISTS ix_pchq_month  ON purchase_cheque(month);
CREATE INDEX IF NOT EXISTS ix_pchq_vendor ON purchase_cheque(vendor_norm);
CREATE UNIQUE INDEX IF NOT EXISTS ux_pchq_live_no
  ON purchase_cheque(cheque_no) WHERE voided_at IS NULL;"""

_cheque_done = False


def _cheque_ensure(con):
    """Created on first request, never at import (F-303). The partial unique
    index is the register's one real check: a cheque number may be reused only
    after the cheque carrying it has been voided."""
    global _cheque_done
    if _cheque_done:
        return
    con.executescript(CHEQUE_SQL)
    con.commit()
    _cheque_done = True


def _cheque_rows_s270(con, month=None):
    """Every cheque, newest first. month=None means the whole register."""
    _cheque_ensure(con)
    if month:
        q = ("SELECT * FROM purchase_cheque WHERE month=? "
             "ORDER BY voided_at IS NOT NULL, cheque_date DESC, id DESC")
        rs = con.execute(q, (month,)).fetchall()
    else:
        q = ("SELECT * FROM purchase_cheque "
             "ORDER BY voided_at IS NOT NULL, cheque_date DESC, id DESC")
        rs = con.execute(q).fetchall()
    return [dict(r) for r in rs]


def _cheque_by_vendor_s270(con, month):
    """vendor_norm -> the live cheques settling that vendor this month."""
    out = {}
    for r in _cheque_rows_s270(con, month):
        if r["voided_at"]:
            continue
        out.setdefault(r["vendor_norm"], []).append(r)
    return out


def _cheque_recon_s270(con, month, groups):
    """What the sheet owes on the cheque lane against what has been written.

    Returns owed_p, written_p, gap_p and the vendors still without a live
    cheque. A vendor part-paid by cheque is NOT counted as settled -- the gap
    is per vendor and the page says so."""
    live = _cheque_by_vendor_s270(con, month)
    cheq = [g for g in groups if g["route"] != "NEFT"]
    owed_p = sum(g["payable_p"] for g in cheq)
    written_p = sum(c["amount_p"] for cs in live.values() for c in cs)
    waiting = []
    for g in cheq:
        got = sum(c["amount_p"] for c in live.get(g["norm"], []))
        if got < g["payable_p"]:
            waiting.append({"vendor": g["name"], "vendor_norm": g["norm"],
                            "payable_p": g["payable_p"], "written_p": got,
                            "short_p": g["payable_p"] - got})
    extra = [{"vendor_norm": k, "written_p": sum(c["amount_p"] for c in v)}
             for k, v in live.items()
             if not any(g["norm"] == k for g in cheq)]
    return {"owed_p": owed_p, "written_p": written_p, "gap_p": owed_p - written_p,
            "waiting": waiting, "extra": extra, "n_live": sum(len(v) for v in live.values())}


def _cheque_parse_date_s270(raw):
    """Accepts yyyy-mm-dd and the dd-mm-yyyy the owner's eye reads. Returns ISO
    or None. It never guesses between the two: a four-digit run decides which
    end the year is on."""
    s = str(raw or "").strip().replace("/", "-")
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", s)
        if not m:
            return None
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12) or not (2000 <= y <= 2099) or d < 1:
        return None
    dim = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1]
    if d > dim:
        return None
    return "%04d-%02d-%02d" % (y, mo, d)


@bp.route("/api/cheque", methods=["POST"])
def api_cheque_s270():
    """Log one cheque. Deliberately allowed on a FINAL month -- see the note at
    the head of this block. It writes no figure the sheet reads."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    vendor_norm = str(b.get("vendor_norm") or "").strip()
    vendor = str(b.get("vendor") or vendor_norm).strip()
    payee = str(b.get("payee") or vendor).strip()[:120]
    cheque_no = str(b.get("cheque_no") or "").strip()[:40]
    bank = str(b.get("bank") or "").strip()[:80]
    note = str(b.get("note") or "").strip()[:300]
    if not re.match(r"^\d{4}-\d{2}$", month) or not vendor_norm:
        return jsonify(ok=False, error="malformed", message="month and vendor_norm"), 400
    if not cheque_no:
        return _refuse("A cheque needs its number. That is the whole point of the register.")
    iso = _cheque_parse_date_s270(b.get("cheque_date"))
    if not iso:
        return _refuse("That date could not be read. Write it as 14-09-2026 or 2026-09-14.")

    amt = _int_or_none(b.get("amount_p"))
    if amt is None:
        raw = str(b.get("amount") or "").replace(",", "").replace("₹", "").strip()
        try:
            amt = int(round(float(raw) * 100))
        except ValueError:
            amt = None
    if amt is None or amt <= 0:
        return _refuse("A cheque needs an amount above zero.")

    con = _db()
    _ensure(con)
    _pay_ensure(con)
    _cheque_ensure(con)

    clash = con.execute("SELECT id, month, vendor, cheque_date FROM purchase_cheque "
                        "WHERE cheque_no=? AND voided_at IS NULL",
                        (cheque_no,)).fetchone()
    if clash:
        return _refuse("Cheque %s is already on the register — %s, %s, for %s. "
                       "Void that one first if this is a correction."
                       % (cheque_no, clash["month"], clash["cheque_date"], clash["vendor"]))

    cur = con.execute(
        "INSERT INTO purchase_cheque (month, vendor_norm, vendor, payee, cheque_no, "
        "cheque_date, amount_p, bank, note, created_at, created_by) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (month, vendor_norm, vendor, payee, cheque_no, iso, amt,
         bank or None, note or None, now_iso(), _who(u)))
    _audit(con, _who(u), "cheque_logged", "%s %s" % (month, vendor_norm),
           {"cheque_no": cheque_no, "date": iso, "amount_p": amt, "payee": payee})
    con.commit()
    return jsonify(ok=True, id=cur.lastrowid, cheque_no=cheque_no, cheque_date=iso, amount_p=amt)


@bp.route("/api/cheque-mark", methods=["POST"])
def api_cheque_mark_s270():
    """Handed over, or voided. Nothing is ever deleted: a void keeps the row,
    its number and its reason, and only then frees the number for reuse."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    cid = _int_or_none(b.get("id"))
    what = str(b.get("what") or "").strip()
    if cid is None or what not in ("handed", "unhanded", "void"):
        return jsonify(ok=False, error="malformed", message="id and what"), 400
    con = _db()
    _ensure(con)
    _cheque_ensure(con)
    row = con.execute("SELECT * FROM purchase_cheque WHERE id=?", (cid,)).fetchone()
    if not row:
        return _refuse("No such cheque on the register.")
    if row["voided_at"]:
        return _refuse("Cheque %s is already voided. A voided row never changes again."
                       % row["cheque_no"])

    if what == "void":
        if _is_viewer_only(u):
            return _refuse("Only the doctor or a checker may void a cheque.")
        reason = str(b.get("reason") or "").strip()[:300]
        if not reason:
            return _refuse("A void needs a reason, in your own words.")
        con.execute("UPDATE purchase_cheque SET voided_at=?, voided_by=?, void_reason=? "
                    "WHERE id=?", (now_iso(), _who(u), reason, cid))
        _audit(con, _who(u), "cheque_void", str(cid),
               {"cheque_no": row["cheque_no"], "reason": reason})
    elif what == "handed":
        con.execute("UPDATE purchase_cheque SET handed_at=?, handed_by=? WHERE id=?",
                    (now_iso(), _who(u), cid))
        _audit(con, _who(u), "cheque_handed", str(cid), {"cheque_no": row["cheque_no"]})
    else:
        con.execute("UPDATE purchase_cheque SET handed_at=NULL, handed_by=NULL WHERE id=?",
                    (cid,))
        _audit(con, _who(u), "cheque_unhanded", str(cid), {"cheque_no": row["cheque_no"]})
    con.commit()
    return jsonify(ok=True, id=cid, what=what)


def _cheque_card_s270(con, month, prefix, groups, editable):
    """The card that replaces the bare 'Paid by cheque' list on the sheet: the
    same vendors, each now carrying its cheque or the one line that logs it."""
    _cheque_ensure(con)
    cheq = [g for g in groups if g["route"] != "NEFT"]
    rec = _cheque_recon_s270(con, month, groups)
    live = _cheque_by_vendor_s270(con, month)

    if not cheq and not rec["n_live"]:
        return ('<style>%s</style>' % CHEQUE_CSS
                + '<div class="card"><h2>Paid by cheque</h2><div class="muted">Nobody this month '
                '— every vendor with a bill has a confirmed account. '
                '<a href="%s/page/cheques">The cheque register</a> holds every cheque ever '
                'written here.</div></div>' % prefix)

    rows = []
    for g in cheq:
        mine = live.get(g["norm"], [])
        got = sum(c["amount_p"] for c in mine)
        if mine:
            written = "".join(
                '<div class="chqline"><b>%s</b> <span class="muted">%s</span> '
                '<span class="n">%s</span>%s</div>'
                % (_esc(c["cheque_no"]), _esc(_dmy_s270(c["cheque_date"])), _r(c["amount_p"]),
                   ' <span class="chip">handed over</span>' if c["handed_at"] else "")
                for c in mine)
        else:
            written = '<div class="muted">no cheque logged yet</div>'
        short = g["payable_p"] - got
        state = ""
        if mine and short > 0:
            state = ' <span class="chip warn">%s still to write</span>' % _r(short)
        elif mine and short < 0:
            state = ' <span class="chip warn">%s more than payable</span>' % _r(-short)

        form = ""
        if editable:
            v = _esc(g["norm"])
            form = (
                '<div class="chqform">'
                '<input id="cno_%s" class="pin w" placeholder="cheque no">'
                '<input id="cdt_%s" class="pin w" placeholder="dd-mm-yyyy">'
                '<input id="cpe_%s" class="pin wide" placeholder="payee on the cheque" value="%s">'
                '<input id="cam_%s" class="pin" placeholder="amount" value="%s">'
                '<button class="p" onclick="chqadd(\'%s\')">Log it</button></div>'
                % (v, v, v, _esc(g["name"]), v, ("%.2f" % (max(short, 0) / 100.0)), v))

        rows.append('<div class="chqv"><div class="chqhead"><span class="vn">%s</span>'
                    '<span class="va">%s</span>%s</div>'
                    '<div class="muted small">%s</div>%s%s</div>'
                    % (_esc(g["name"]), _r(g["payable_p"]), state,
                       _esc(g["why"]), written, form))

    if rec["gap_p"] > 0:
        head = ('<div class="bad">%s of this month’s cheque lane has no cheque against it '
                'yet — %d vendor%s waiting.</div>'
                % (_r(rec["gap_p"]), len(rec["waiting"]), "" if len(rec["waiting"]) == 1 else "s"))
    elif rec["gap_p"] < 0:
        head = ('<div class="bad">The cheques written come to %s more than this month’s '
                'cheque lane. Check the register.</div>' % _r(-rec["gap_p"]))
    else:
        head = ('<div class="ok">Every rupee on this month’s cheque lane has a cheque '
                'against it.</div>')

    return ('<div class="card"><h2>Paid by cheque — not in the NEFT file (%d)</h2>'
            '<div class="muted">A vendor whose account is not confirmed on this server is never '
            'put into the bank advice file. Write a cheque, and log it here — number, date '
            'and the payee as written. The moment the account is added and confirmed on the '
            '<a href="%s/page/book">phone book page</a>, that vendor moves to the NEFT lane by '
            'itself.</div>%s%s'
            '<div class="muted" style="margin-top:8px">Owed %s &middot; written %s &middot; '
            '<a href="%s/page/cheques/%s">the cheque register for this month</a></div></div>'
            % (len(cheq), prefix, head, "".join(rows),
               _r(rec["owed_p"]), _r(rec["written_p"]), prefix, month))


def _dmy_s270(iso):
    """The owner reads dates day-first. Stored ISO, shown dd-mm-yyyy."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(iso or ""))
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else (iso or "")


@bp.route("/page/cheques")
@bp.route("/page/cheques/<month>")
def page_cheques_s270(month=None):
    """The register's own screen. Read by anyone who may open the sheet."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if month is not None and not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    _cheque_ensure(con)
    prefix = request.script_root + _url_prefix
    editable = not _is_viewer_only(u)

    months = [r[0] for r in con.execute(
        "SELECT DISTINCT month FROM purchase_cheque ORDER BY month DESC").fetchall()]
    rows = _cheque_rows_s270(con, month)

    strip = ['<a class="mtab%s" href="%s/page/cheques">Every cheque</a>'
             % ("" if month else " on", prefix)]
    for m in months:
        strip.append('<a class="mtab%s" href="%s/page/cheques/%s">%s</a>'
                     % (" on" if m == month else "", prefix, m, _esc(_month_name(m))))
    strip_html = '<div class="card"><div class="mtabs">%s</div></div>' % "".join(strip)

    live = [r for r in rows if not r["voided_at"]]
    total_p = sum(r["amount_p"] for r in live)
    handed = sum(1 for r in live if r["handed_at"])

    recon = ""
    if month:
        s, groups = _pay_rows(con, month)
        rec = _cheque_recon_s270(con, month, groups)
        if rec["gap_p"] > 0:
            wait = "".join('<div class="kvline"><b>%s</b><span>%s still to write</span></div>'
                           % (_esc(w["vendor"]), _r(w["short_p"])) for w in rec["waiting"])
            recon = ('<div class="card"><h2>Against the sheet</h2>'
                     '<div class="bad">The sheet puts %s on the cheque lane this month. '
                     '%s has been written. %s is still owed.</div>%s'
                     '<div class="muted" style="margin-top:8px">'
                     '<a href="%s/page/pay/%s">the payment sheet for this month</a></div></div>'
                     % (_r(rec["owed_p"]), _r(rec["written_p"]), _r(rec["gap_p"]), wait,
                        prefix, month))
        else:
            recon = ('<div class="card"><h2>Against the sheet</h2>'
                     '<div class="ok">The sheet puts %s on the cheque lane this month, and %s '
                     'has been written. Nothing is owed.</div>'
                     '<div class="muted" style="margin-top:8px">'
                     '<a href="%s/page/pay/%s">the payment sheet for this month</a></div></div>'
                     % (_r(rec["owed_p"]), _r(rec["written_p"]), prefix, month))

    if rows:
        trs = []
        for r in rows:
            cls = ' class="void"' if r["voided_at"] else ""
            mark = ""
            if r["voided_at"]:
                mark = ('<span class="chip warn">VOID</span> <span class="muted">%s</span>'
                        % _esc(r["void_reason"] or ""))
            elif editable:
                mark = ('<button class="plainbtn" onclick="chqmark(%d,\'%s\')">%s</button>'
                        % (r["id"], "unhanded" if r["handed_at"] else "handed",
                           "handed over" if r["handed_at"] else "mark handed"))
            elif r["handed_at"]:
                mark = '<span class="chip">handed over</span>'
            vd = ""
            if editable and not r["voided_at"]:
                vd = ('<button class="plainbtn warn" onclick="chqvoid(%d,\'%s\')">void</button>'
                      % (r["id"], _esc(r["cheque_no"])))
            trs.append(
                '<tr%s><td class="mono">%s</td><td>%s</td><td>%s</td><td class="muted">%s</td>'
                '<td class="muted">%s</td><td class="n">%s</td><td>%s</td><td>%s</td></tr>'
                % (cls, _esc(r["cheque_no"]), _esc(_dmy_s270(r["cheque_date"])),
                   _esc(r["payee"]), _esc(r["vendor"]), _esc(r["month"]),
                   _r(r["amount_p"]), mark, vd))
        table = ('<div class="scroll"><table><tr><th>Cheque</th><th>Written on</th><th>Payee</th>'
                 '<th>Vendor</th><th>Month</th><th class="n">Amount</th><th>&nbsp;</th>'
                 '<th>&nbsp;</th></tr>%s</table></div>' % "".join(trs))
    else:
        table = ('<div class="muted">No cheque has been logged%s yet. They are logged from the '
                 'payment sheet, on the vendor the cheque settles.</div>'
                 % ((" for %s" % _month_name(month)) if month else ""))

    body = ('<style>' + CHEQUE_CSS + '</style>'
            '<h1>Cheque register%s</h1>'
            '<div class="muted">Sanjeevni Medicos &middot; every cheque written to a vendor who '
            'is not on the NEFT lane — number, date, payee and the month it settles. '
            'Nothing here is ever deleted; a wrong entry is voided with a reason and stays.</div>'
            '%s%s'
            '<div class="card"><div class="grid">'
            '<div class="kv"><b>%d</b><span>cheques%s</span></div>'
            '<div class="kv"><b>%s</b><span>their total</span></div>'
            '<div class="kv"><b>%d</b><span>handed over</span></div>'
            '<div class="kv"><b>%d</b><span>voided</span></div></div></div>'
            '<div class="card"><h2>The register</h2>%s'
            '<div class="noprint" style="margin-top:10px">'
            '<button class="p" onclick="window.print()">Print this</button></div></div>'
            % ((" — %s" % _esc(_month_name(month))) if month else "",
               strip_html, recon,
               len(live), (" in %s" % _esc(_month_name(month))) if month else " on record",
               _r(total_p), handed, len(rows) - len(live), table))
    return _page("Cheque register", body, CHEQUE_JS.replace("__MONTH__", month or ""))


CHEQUE_JS = """
var M270='__MONTH__';
function chqadd(v){
 var g=function(p){var e=document.getElementById(p+v);return e?e.value:'';};
 var b={month:M270,vendor_norm:v,vendor:'',payee:g('cpe_'),cheque_no:g('cno_'),
        cheque_date:g('cdt_'),amount:g('cam_')};
 if(!b.cheque_no){alert('The cheque number, please \\u2014 that is what the register is for.');return;}
 fetch(P+'/api/cheque',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(b)}).then(function(r){return r.json();}).then(function(j){
  if(!j.ok){alert(j.message||'could not log that cheque');return;}
  location.reload();
 }).catch(function(){alert('could not log that cheque just now');});}
function chqmark(id,what){
 fetch(P+'/api/cheque-mark',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({id:id,what:what})}).then(function(r){return r.json();}).then(function(j){
  if(!j.ok){alert(j.message||'could not do that');return;}
  location.reload();
 }).catch(function(){alert('could not do that just now');});}
function chqvoid(id,no){
 var why=prompt('Voiding cheque '+no+'. Why? (this stays on the register)');
 if(why==null||!why.trim())return;
 fetch(P+'/api/cheque-mark',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({id:id,what:'void',reason:why})})
 .then(function(r){return r.json();}).then(function(j){
  if(!j.ok){alert(j.message||'could not void that');return;}
  location.reload();
 }).catch(function(){alert('could not void that just now');});}
"""

CHEQUE_CSS = """
.ok{color:#2f6b45}
.chqv{border-top:1px solid var(--line);padding:10px 0}
.chqv:first-of-type{border-top:0}
.chqhead{display:flex;gap:10px;align-items:baseline}
.chqhead .vn{flex:1;font-weight:600}
.chqhead .va{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
.small{font-size:12.5px}
.chqline{font-size:13.5px;padding:3px 0}
.chqline .n{font-variant-numeric:tabular-nums}
.chqform{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}
input.pin.w{width:120px;text-align:left}
input.pin.wide{width:210px;text-align:left;flex:1 1 180px}
.mtabs{display:flex;flex-wrap:wrap;gap:6px}
a.mtab{display:inline-block;padding:5px 11px;border:1px solid var(--line);border-radius:18px;
 font-size:13px;text-decoration:none}
a.mtab.on{border-color:var(--ink);font-weight:600}
tr.void td{opacity:.55;text-decoration:line-through}
tr.void td:last-child,tr.void td:nth-last-child(2){text-decoration:none}
td.mono{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
button.plainbtn{background:none;border:0;padding:2px 0;font:inherit;font-size:12.5px;
 color:var(--muted);cursor:pointer;text-decoration:underline}
button.plainbtn.warn{color:#a33}
.kvline{display:flex;gap:10px;justify-content:space-between;padding:3px 0;font-size:13.5px}
.kvline b{font-weight:600}
"""

# The sheet's own script gains the three cheque functions, so the form on the
# payment sheet works there too. page_pay already substitutes __MONTH__.
# PAY_JS reaches ONLY the payment sheet, so nothing else grows by a byte.
PAY_JS = PAY_JS + CHEQUE_JS

# THE SHARED STYLESHEET IS DELIBERATELY NOT TOUCHED (F-478).
# An earlier draft did `CSS = CSS + CHEQUE_CSS`, and the walk caught it on the
# box: /hub, /scans, /orders and /book each grew by exactly 1,287 bytes -- four
# screens with nothing to do with cheques, carrying cheque CSS. The style now
# travels with the two things that need it and with nothing else.
