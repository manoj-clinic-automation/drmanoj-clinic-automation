

# ===================================================================== S261
# THE NEFT SHEET, INSIDE THE SYSTEM
#
# The month page answers "what does Marg say was bought". This is the other
# thing: the sheet the payment is actually made from. Until now it lived in a
# workbook on the owner's PC, prefilled by a script from an export, and that is
# how a draft carrying last month's numbers could sit in the payment folder for
# two weeks looking finished.
#
# THE ORDER IS THE OWNER'S, 14-Sep-2026: prepare the sheet first, then verify it
# against the supplier-wise statement, then lock it.
#
#   1  PREPARE.  The system fills everything it knows: each vendor, the bills
#      split into the two fortnights the sheet has always used, the month's
#      total, and which lane the vendor is paid through. Carry-forward is the
#      one thing it does not know -- July was settled outside this system -- so
#      it is typed here and says so.
#   2  VERIFY.  The supplier-wise purchase statement is the cross-check, not a
#      gate to tick: the check compares what was prepared against Marg's own
#      supplier-wise export of the same month -- its bill count, its per-bill
#      amounts and its OWN PRINTED GRAND TOTAL -- and either says it agrees to
#      the rupee or names exactly what differs. Every run is kept.
#   3  LOCK.  Finalise the month and the figures stop moving; the advice file
#      and its covering letter are built from this and from nothing else.
#
# A vendor whose account is not confirmed on this server is never in the NEFT
# total. They are a cheque, said out loud, with the one screen that fixes it.
# A small difference is flagged and never swallowed.

PAY_SHEET = """CREATE TABLE IF NOT EXISTS purchase_pay_line (
  month         TEXT NOT NULL,
  vendor_norm   TEXT NOT NULL,
  carry_fwd_p   INTEGER,
  paid_p        INTEGER,
  note          TEXT,
  updated_by    TEXT,
  updated_at    TEXT,
  PRIMARY KEY (month, vendor_norm)
);
CREATE TABLE IF NOT EXISTS purchase_pay_check (
  id       INTEGER PRIMARY KEY,
  month    TEXT NOT NULL,
  at       TEXT NOT NULL,
  who      TEXT NOT NULL,
  ok       INTEGER NOT NULL,
  detail   TEXT
);
CREATE INDEX IF NOT EXISTS ix_ppc_month ON purchase_pay_check(month, id);"""

_pay_done = False


def _pay_ensure(con):
    """The two small tables the sheet needs, created on first request and never
    at import (F-303). One holds what a person types; one holds every run of the
    verification, appended, never overwritten."""
    global _pay_done
    if _pay_done:
        return
    con.executescript(PAY_SHEET)
    con.commit()
    _pay_done = True


def _bank_cols(con):
    try:
        return {r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")}
    except sqlite3.Error:
        return set()


def _vendor_bank(con):
    """supplier_norm -> dict(route, why). NEFT only when an account is on this
    server AND confirmed. Everything else is a cheque, said out loud."""
    out = {}
    cols = _bank_cols(con)
    if not cols or "vendor_norm" not in cols:
        return out
    has_acct, has_st = "acct_no" in cols, "bank_status" in cols
    sel = "vendor_norm, vendor" + (", acct_no" if has_acct else "") + (", bank_status" if has_st else "")
    try:
        rows = con.execute("SELECT %s FROM purchase_vendor_contact" % sel).fetchall()
    except sqlite3.Error:
        return out
    for r in rows:
        acct = (r[2] or "").strip() if has_acct else ""
        st = ((r[3] if (has_st and has_acct) else (r[2] if has_st else "")) or "").strip().upper()
        if acct and st == "VERIFIED":
            out[r[0]] = {"route": "NEFT", "why": "account confirmed"}
        elif acct:
            out[r[0]] = {"route": "CHEQUE", "why": "account on file, not confirmed yet"}
        else:
            out[r[0]] = {"route": "CHEQUE", "why": "no account on this server"}
    return out


def _pay_typed(con, month):
    """What a person has typed on this month's sheet."""
    _pay_ensure(con)
    out = {}
    for r in con.execute("SELECT vendor_norm, carry_fwd_p, paid_p, note, updated_by, updated_at "
                         "FROM purchase_pay_line WHERE month=?", (month,)):
        out[r[0]] = {"carry_p": r[1], "paid_p": r[2], "note": r[3] or "",
                     "by": r[4] or "", "at": r[5] or ""}
    return out


def _fortnight(iso):
    """The sheet has always split a month at the 15th. Bills with no date sit in
    the second half rather than vanishing -- and they are flagged anyway."""
    try:
        return 1 if int(iso[8:10]) <= 15 else 2
    except (TypeError, ValueError, IndexError):
        return 2


def _pay_rows(con, month):
    """THE SHEET. One row per vendor: the two fortnights, the month, what was
    carried in, what is payable, and how it is paid."""
    s = _month_summary(con, month)
    bank = _vendor_bank(con)
    typed = _pay_typed(con, month)
    ret_by = {x["bill"]["id"]: x for x in s["returns"]}
    short_by = {x["bill"]["id"]: x for x in s["short"]}
    groups, cur = [], None
    for b in s["bills"]:
        if b["supplier_norm"] != cur:
            cur = b["supplier_norm"]
            info = bank.get(cur) or {"route": "CHEQUE", "why": "no account on this server"}
            ty = typed.get(cur) or {}
            groups.append({"norm": cur, "name": b["supplier"], "bills": [], "total_p": 0,
                           "f1_p": 0, "f2_p": 0, "route": info["route"], "why": info["why"],
                           "flags": 0, "carry_p": ty.get("carry_p"), "paid_p": ty.get("paid_p"),
                           "note": ty.get("note", ""), "by": ty.get("by", ""), "at": ty.get("at", "")})
        g = groups[-1]
        t = _bill_lines(b, s["sets"], s["stray"])
        flag = ""
        if b["verdict"] == "WRONG":
            flag = "marked wrong — should be %s" % _r(b["wrong_amount_p"])
        elif b["id"] in ret_by:
            flag = ("the lines add up to %s, %s more than the bill — Marg reports a purchase "
                    "return against it. Worth opening: it may be an entry that needs correcting."
                    % (_r(ret_by[b["id"]]["net_p"]), _r(ret_by[b["id"]]["diff_p"])))
        elif b["id"] in short_by:
            flag = ("the lines add up to %s LESS than the bill — a line is missing from the "
                    "export, or the bill is wrong. Check the bill." % _r(-short_by[b["id"]]["diff_p"]))
        elif b["disagree_p"]:
            flag = ("bill-wise says %s and supplier-wise says %s — the two Marg reports disagree."
                    % (_r(b["bw_p"]), _r(b["sw_p"])))
        note = "" if t else "the item lines for this bill have not arrived yet."
        g["bills"].append({"id": b["id"], "no": b["bill_no"], "date": b["bill_date"],
                           "amount_p": b["marg_p"], "net_p": (t["net_p"] if t else None),
                           "lines": (t["n"] if t else 0), "flag": flag, "note": note})
        g["total_p"] += b["marg_p"]
        if _fortnight(b["bill_date"]) == 1:
            g["f1_p"] += b["marg_p"]
        else:
            g["f2_p"] += b["marg_p"]
        if flag:
            g["flags"] += 1
    for g in groups:
        g["payable_p"] = g["total_p"] + (g["carry_p"] or 0)
    return s, groups


def _verify_statement(con, month):
    """STEP 2 -- the supplier-wise statement as the cross-check.

    Not a tick-box: it reads Marg's own supplier-wise export of this month and
    holds the prepared sheet against it three ways -- every bill carried by it,
    the per-bill amounts where bill-wise and supplier-wise both exist, and the
    export's OWN PRINTED GRAND TOTAL. Anything that does not line up is named."""
    s = _month_summary(con, month)
    bills = s["bills"]
    problems, notes = [], []
    sw = con.execute(
        "SELECT md5, file, export_stamp, n_rows, grand_amount_p FROM purchase_export "
        "WHERE type='SUPPLIERWISE' AND superseded_by IS NULL AND period_from<=? AND period_to>=? "
        "ORDER BY export_stamp DESC LIMIT 1", (month + "-01", month + "-28")).fetchone()
    if sw is None:
        problems.append("No supplier-wise purchase statement for this month has reached the server. "
                        "Take it out of Marg — supplier, bill number, bill date, amount — "
                        "and it will arrive by itself within about ten minutes.")
        return {"ok": False, "problems": problems, "notes": notes, "export": None,
                "n_bills": len(bills), "total_p": s["marg_p"], "printed_p": None}

    without = [b for b in bills if b["sw_p"] is None]
    if without:
        problems.append("%s on the sheet %s not carried by that statement: %s."
                        % (_plural(len(without), "bill"), "is" if len(without) == 1 else "are",
                           _name_some(without, lambda b: "%s (%s)" % (b["bill_no"], b["supplier"]))))
    dis = [b for b in bills if b["disagree_p"]]
    if dis:
        problems.append("%s where bill-wise and supplier-wise disagree: %s."
                        % (_plural(len(dis), "bill"),
                           _name_some(dis, lambda b: "%s %s vs %s"
                                      % (b["bill_no"], _r(b["bw_p"]), _r(b["sw_p"])))))
    printed = sw["grand_amount_p"]
    if printed:
        if abs(printed - s["marg_p"]) > AGREE_P:
            problems.append("The statement prints its own grand total as %s; the sheet adds up to "
                            "%s — a difference of %s."
                            % (_r(printed), _r(s["marg_p"]), _r(abs(printed - s["marg_p"]))))
        else:
            notes.append("The statement's own printed grand total is %s — the sheet agrees with "
                         "it to the rupee." % _r(printed))
    else:
        notes.append("That statement did not carry a printed grand total, so the comparison is "
                     "bill by bill only.")
    notes.append("Statement: %s, taken %s, %s row%s."
                 % (_esc(sw["file"]), _esc(sw["export_stamp"]), sw["n_rows"],
                    "" if sw["n_rows"] == 1 else "s"))
    return {"ok": not problems, "problems": problems, "notes": notes, "export": dict(sw),
            "n_bills": len(bills), "total_p": s["marg_p"], "printed_p": printed}


def _pay_last_check(con, month):
    _pay_ensure(con)
    r = con.execute("SELECT at, who, ok, detail FROM purchase_pay_check WHERE month=? "
                    "ORDER BY id DESC LIMIT 1", (month,)).fetchone()
    return dict(r) if r else None


@bp.route("/api/pay-verify", methods=["POST"])
def api_pay_verify():
    """Run the verification and keep the run. Never changes a figure."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    if not re.match(r"^\d{4}-\d{2}$", month):
        return jsonify(ok=False, error="malformed", message="month as YYYY-MM"), 400
    con = _db()
    _ensure(con)
    v = _verify_statement(con, month)
    con.execute("INSERT INTO purchase_pay_check (month, at, who, ok, detail) VALUES (?,?,?,?,?)",
                (month, now_iso(), _who(u), 1 if v["ok"] else 0,
                 json.dumps({"problems": v["problems"], "notes": v["notes"],
                             "total_p": v["total_p"], "printed_p": v["printed_p"]},
                            ensure_ascii=False)))
    _audit(con, _who(u), "pay_verify", month, {"ok": v["ok"], "problems": len(v["problems"])})
    con.commit()
    return jsonify(ok=True, verified=v["ok"], problems=v["problems"], notes=v["notes"])


@bp.route("/api/pay-line", methods=["POST"])
def api_pay_line():
    """The one thing a person types on this sheet: what an earlier month left
    outstanding, what has been paid, and a note. The doctor's rule stands -- a
    final month does not move."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    vendor = str(b.get("vendor_norm") or "")
    if not re.match(r"^\d{4}-\d{2}$", month) or not vendor:
        return jsonify(ok=False, error="malformed", message="month and vendor_norm"), 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    if _month_status(con, month)["status"] == "final":
        return _refuse("This month is FINAL. The doctor must reopen it first.")

    def money(key):
        v = b.get(key + "_p")
        n = _int_or_none(v)
        if n is not None:
            return n
        raw = str(b.get(key) or "").replace(",", "").replace("₹", "").strip()
        if raw == "":
            return None
        try:
            return int(round(float(raw) * 100))
        except ValueError:
            return None

    carry, paid = money("carry_fwd"), money("paid")
    note = str(b.get("note") or "").strip()[:300]
    before = con.execute("SELECT carry_fwd_p, paid_p, note FROM purchase_pay_line WHERE month=? "
                         "AND vendor_norm=?", (month, vendor)).fetchone()
    con.execute("INSERT INTO purchase_pay_line (month, vendor_norm, carry_fwd_p, paid_p, note, "
                "updated_by, updated_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(month, vendor_norm) "
                "DO UPDATE SET carry_fwd_p=excluded.carry_fwd_p, paid_p=excluded.paid_p, "
                "note=excluded.note, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                (month, vendor, carry, paid, note or None, _who(u), now_iso()))
    _audit(con, _who(u), "pay_line", "%s %s" % (month, vendor),
           {"carry_fwd_p": carry, "paid_p": paid, "note": note,
            "before": dict(before) if before else None})
    con.commit()
    return jsonify(ok=True, month=month, vendor_norm=vendor, carry_fwd_p=carry, paid_p=paid)


@bp.route("/api/bill-lines")
def api_bill_lines():
    """The item lines of ONE bill -- the third level. Read only."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    try:
        bid = int(request.args.get("bill") or 0)
    except ValueError:
        return jsonify(ok=False, error="bad_bill"), 400
    con = _db()
    _ensure(con)
    b = con.execute("SELECT * FROM purchase_bill WHERE id=?", (bid,)).fetchone()
    if not b:
        return jsonify(ok=False, error="no_such_bill"), 404
    b = dict(b)
    sets = _line_sets(con, b["month"])
    t = _bill_lines(b, sets, _stray_sets(_bills_for_month(con, b["month"]), sets))
    if not t:
        return jsonify(ok=True, lines=[], n=0, net="—",
                       note="No item lines have arrived for this bill yet.")
    rows = con.execute(
        "SELECT item, packing, batch, expiry, qty, free, rate_p, discount_pct, "
        "COALESCE(net_amount_p, amount_p) FROM purchase_line WHERE source_md5=? AND bill_no=? "
        "AND (supplier_norm=? OR supplier_norm IS NULL) AND line_type=? ORDER BY id",
        (t["md5"], b["bill_no"], b["supplier_norm"], t["line_type"])).fetchall()
    out = [{"item": r[0], "packing": r[1] or "", "batch": r[2] or "", "expiry": r[3] or "",
            "qty": r[4], "free": r[5], "rate": _r(r[6]), "disc": r[7], "amount": _r(r[8])}
           for r in rows]
    return jsonify(ok=True, lines=out, net=_r(t["net_p"]), n=t["n"])


def _pay_sheet_table(groups, prefix, month, editable):
    """The sheet as a sheet -- the thing that is printed and signed."""
    rows = []
    for g in groups:
        carry = ("" if g["carry_p"] is None else "%d" % int(round(g["carry_p"] / 100.0)))
        paid = ("" if g["paid_p"] is None else "%d" % int(round(g["paid_p"] / 100.0)))
        inp = ('<input class="pin" id="cf_%s" value="%s" inputmode="numeric" '
               'onchange="payline(\'%s\',this)" data-v="%s">'
               % (_esc(g["norm"]), carry, _esc(g["norm"]), _esc(g["norm"]))) if editable else (
               _r(g["carry_p"]) if g["carry_p"] is not None else "—")
        pin = ('<input class="pin" id="pd_%s" value="%s" inputmode="numeric" '
               'onchange="payline(\'%s\',this)">' % (_esc(g["norm"]), paid, _esc(g["norm"]))
               ) if editable else (_r(g["paid_p"]) if g["paid_p"] is not None else "—")
        rows.append('<tr><td>%s%s</td><td class="n">%s</td><td class="n">%s</td>'
                    '<td class="n">%s</td><td class="n">%s</td><td class="n" id="py_%s">%s</td>'
                    '<td class="n">%s</td></tr>'
                    % (_esc(g["name"]),
                       ' <span class="chip warn">CHEQUE</span>' if g["route"] != "NEFT" else "",
                       _r(g["f1_p"]), _r(g["f2_p"]), _r(g["total_p"]), inp,
                       _esc(g["norm"]), _r(g["payable_p"]), pin))
    tot_f1 = sum(g["f1_p"] for g in groups)
    tot_f2 = sum(g["f2_p"] for g in groups)
    tot = sum(g["total_p"] for g in groups)
    tot_c = sum(g["carry_p"] or 0 for g in groups)
    tot_pay = sum(g["payable_p"] for g in groups)
    tot_paid = sum(g["paid_p"] or 0 for g in groups)
    rows.append('<tr><th>TOTAL</th><th class="n">%s</th><th class="n">%s</th><th class="n">%s</th>'
                '<th class="n">%s</th><th class="n">%s</th><th class="n">%s</th></tr>'
                % (_r(tot_f1), _r(tot_f2), _r(tot), _r(tot_c) if tot_c else "—",
                   _r(tot_pay), _r(tot_paid) if tot_paid else "—"))
    return ('<div class="scroll"><table class="sheet"><tr><th>Vendor</th>'
            '<th class="n">1st–15th</th><th class="n">16th–end</th>'
            '<th class="n">%s</th><th class="n">Carried in</th><th class="n">Payable</th>'
            '<th class="n">Paid</th></tr>%s</table></div>'
            % (_esc(_month_name(month)), "".join(rows)))


@bp.route("/page/pay/<month>")
def page_pay(month):
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    s, groups = _pay_rows(con, month)
    prefix = request.script_root + _url_prefix
    final = s["status"]["status"] == "final"
    editable = (not final) and (not _is_viewer_only(u))

    neft_p = sum(g["payable_p"] for g in groups if g["route"] == "NEFT")
    cheq = [g for g in groups if g["route"] != "NEFT"]
    cheq_p = sum(g["payable_p"] for g in cheq)
    flagged = sum(g["flags"] for g in groups)

    # ---------------------------------------------------------- 1 · the sheet
    cards = []
    for i, g in enumerate(groups):
        chips = ""
        if g["route"] != "NEFT":
            chips += ' <span class="chip warn">CHEQUE</span>'
        if g["flags"]:
            chips += ' <span class="chip warn">CHECK</span>'
        bills = []
        for b in g["bills"]:
            fl = ' <span class="chip warn">CHECK</span>' if b["flag"] else ""
            bills.append(
                '<div class="payb"><button class="plain" onclick="bl(%d)">'
                '<span class="bno">%s</span><span class="bdt muted">%s%s</span>'
                '<span class="bam">%s</span></button>'
                '<div class="paybd" id="bl%d"><div class="muted">Bill %s &middot; %s &middot; '
                'Marg amount %s &middot; item-wise (after discount) %s &middot; %d line%s</div>%s'
                '<div class="lines muted">Open to load the bill\'s own lines.</div></div></div>'
                % (b["id"], _esc(b["no"]), _human(b["date"]), fl, _r(b["amount_p"]), b["id"],
                   _esc(b["no"]), _human(b["date"]), _r(b["amount_p"]),
                   _r(b["net_p"]) if b["net_p"] is not None else "—",
                   b["lines"], "" if b["lines"] == 1 else "s",
                   ('<div class="warn" style="margin:6px 0">%s</div>' % _esc(b["flag"])) if b["flag"]
                   else ('<div class="muted" style="margin:6px 0">%s</div>' % _esc(b["note"]))
                   if b["note"] else ""))
        strip = ('<div class="vstrip muted">1st–15th <b>%s</b> &nbsp;&middot;&nbsp; '
                 '16th–end <b>%s</b> &nbsp;&middot;&nbsp; carried in <b>%s</b> '
                 '&nbsp;&middot;&nbsp; payable <b>%s</b> &nbsp;&middot;&nbsp; %s</div>'
                 % (_r(g["f1_p"]), _r(g["f2_p"]),
                    _r(g["carry_p"]) if g["carry_p"] is not None else "not typed yet",
                    _r(g["payable_p"]), _esc(g["why"])))
        cards.append(
            '<div class="payv"><button class="plain vhead" onclick="pv(%d,this)">'
            '<span class="car">&#9656;</span><span class="vn">%s%s<span class="muted vb">%d bill%s'
            '</span></span><span class="va">%s</span></button><div class="payl" id="pv%d">%s%s</div></div>'
            % (i, _esc(g["name"]), chips, len(g["bills"]), "" if len(g["bills"]) == 1 else "s",
               _r(g["payable_p"]), i, strip, "".join(bills)))

    sheet_card = (
        '<div class="card"><h2>1 &middot; The sheet</h2><div class="muted">One line per vendor, '
        'prepared from this server\'s own figures. Open a vendor for its bills; open a bill for the '
        'bill. <b>Carried in</b> is the only thing typed here — what an earlier month left '
        'outstanding, which was settled outside this system and which it therefore does not know.</div>'
        '%s<h3>The sheet as it prints</h3>%s</div>'
        % ("".join(cards), _pay_sheet_table(groups, prefix, month, editable)))

    # ----------------------------------------------------- 2 · the verification
    last = _pay_last_check(con, month)
    if last:
        try:
            d = json.loads(last["detail"] or "{}")
        except ValueError:
            d = {}
        body = "".join('<li>%s</li>' % _esc(x) for x in (d.get("problems") or []))
        verdict = ('<div class="ok"><b>Checked against the statement and it agrees</b></div>'
                   if last["ok"] else
                   '<div class="bad"><b>Checked against the statement — these do not line up</b>'
                   '</div><ul>%s</ul>' % body)
        when = ('<div class="muted">Last run %s by %s.</div>'
                % (_esc(_hhmm_ist_full(last["at"])), _esc(last["who"])))
        notes = "".join('<div class="muted">%s</div>' % _esc(x) for x in (d.get("notes") or []))
    else:
        verdict = ('<div class="muted">Not checked yet. The sheet above is what this server '
                   'believes; the statement is what Marg says. They are not the same claim until '
                   'they have been held against each other.</div>')
        when, notes = "", ""
    verify_card = (
        '<div class="card"><h2>2 &middot; Verify against the supplier-wise statement</h2>'
        '<div class="muted">The cross-check, not a tick-box: Marg\'s own supplier-wise export of '
        'this month is read and the sheet is held against it three ways — every bill it carries, '
        'the per-bill amounts, and the statement\'s own printed grand total.</div>'
        '%s%s%s<div class="noprint" style="margin-top:10px">'
        '<button class="p" onclick="payverify(\'%s\')">Check it now</button></div>'
        '<div id="vout"></div></div>' % (verdict, notes, when, month))

    # ------------------------------------------------------------ 3 · cheques
    if cheq:
        rows = "".join(
            '<tr><td>%s</td><td class="muted">%s</td><td class="n">%s</td>'
            '<td><a href="%s/page/book">add / confirm the account</a></td></tr>'
            % (_esc(g["name"]), _esc(g["why"]), _r(g["payable_p"]), prefix) for g in cheq)
        cheque_card = (
            '<div class="card"><h2>Paid by cheque — not in the NEFT file (%d)</h2>'
            '<div class="muted">A vendor whose account is not confirmed on this server is never put '
            'into the bank advice file. Write a cheque, and log it. The moment the account is added '
            'and confirmed on the phone book page, that vendor moves to the NEFT lane by itself.</div>'
            '<div class="scroll"><table><tr><th>Vendor</th><th>Why</th><th class="n">Payable</th>'
            '<th>&nbsp;</th></tr>%s</table></div></div>' % (len(cheq), rows))
    else:
        cheque_card = ('<div class="card"><h2>Paid by cheque</h2><div class="muted">Nobody this '
                       'month — every vendor with a bill has a confirmed account.</div></div>')

    strip = ('<div class="card"><div class="grid">'
             '<div class="kv"><b>%s</b><span>%s purchases</span></div>'
             '<div class="kv"><b>%s</b><span>payable by NEFT</span></div>'
             '<div class="kv"><b>%s</b><span>payable by cheque</span></div>'
             '<div class="kv"><b>%d</b><span>flagged</span></div></div></div>'
             % (_r(s["marg_p"]), _esc(_month_name(month)), _r(neft_p), _r(cheq_p), flagged))

    nextcard = (
        '<div class="card"><h2>3 &middot; Lock it</h2><div class="muted">%s The NEFT total is what '
        'goes into the bank advice file and its covering letter, and they are built from this sheet '
        'and from nothing else.</div></div>'
        % ('This month is <b>final</b>: the figures are locked until it is reopened.' if final
           else 'Finalise the month on its own page once the check above agrees, and these figures lock.'))

    body = ('<h1>Vendor payments — %s</h1><div class="muted">Sanjeevni Medicos &middot; the sheet '
            'this month is paid from. <a href="%s/page/month/%s">the same month, bill by bill</a>'
            '</div>%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month, strip, sheet_card, verify_card,
               cheque_card, nextcard))
    return _page("Vendor payments — %s" % _month_name(month), body,
                 PAY_JS.replace("__MONTH__", month))


@bp.route("/page/pay")
def page_pay_latest():
    """A stable address for the tile: the newest month that has bills."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _ensure(con)
    ms = _months(con, 1)
    if not ms:
        return _page("Vendor payments", '<h1>Vendor payments</h1><div class="muted">No purchase '
                     'bills have arrived yet.</div>')
    return redirect((request.script_root + _url_prefix) + "/page/pay/" + ms[0])


# One link, added without touching a single existing line: the nav helper is
# wrapped rather than edited, so every purchase screen gains the way in and the
# format string that builds the nav is left exactly as it was.
_book_nav_before_s261 = _book_nav


def _book_nav(prefix):                                          # noqa: F811
    try:
        return _book_nav_before_s261(prefix) + (
            '<a href="%s/page/pay">Vendor payments</a>' % prefix)
    except Exception:                                           # noqa: BLE001
        return ""


PAY_JS = """
function pv(i,el){var d=document.getElementById('pv'+i);
 d.classList.toggle('open');el.classList.toggle('open');}
function bl(id){var d=document.getElementById('bl'+id);
 var was=d.classList.contains('open');d.classList.toggle('open');
 if(was||d.dataset.done)return;d.dataset.done='1';
 var box=d.querySelector('.lines');box.textContent='loading the bill\\u2026';
 fetch(P+'/api/bill-lines?bill='+id).then(function(r){return r.json();}).then(function(j){
  if(!j.ok||!j.lines.length){box.textContent=j.note||'No item lines for this bill.';return;}
  var h='<div class="scroll"><table><tr><th>Item</th><th>Batch</th><th>Expiry</th><th class="n">Qty</th>'
   +'<th class="n">Free</th><th class="n">Rate</th><th class="n">Disc</th><th class="n">Amount</th></tr>';
  j.lines.forEach(function(l){h+='<tr><td>'+esc(l.item)+(l.packing?' <span class="muted">'+esc(l.packing)+'</span>':'')
   +'</td><td>'+esc(l.batch)+'</td><td>'+esc(l.expiry)+'</td><td class="n">'+(l.qty==null?'':l.qty)
   +'</td><td class="n">'+(l.free?l.free:'')+'</td><td class="n">'+l.rate+'</td><td class="n">'
   +(l.disc?l.disc+'%':'')+'</td><td class="n">'+l.amount+'</td></tr>';});
  h+='</table></div><div class="muted" style="margin-top:6px">'+j.n+' line'+(j.n==1?'':'s')
   +', '+j.net+' after discount.</div>';
  box.innerHTML=h;box.classList.remove('muted');
 }).catch(function(){box.textContent='could not load the bill just now.';});}
function payline(v,el){
 var cf=document.getElementById('cf_'+v), pd=document.getElementById('pd_'+v);
 el.disabled=true;
 fetch(P+'/api/pay-line',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({month:'__MONTH__',vendor_norm:v,
   carry_fwd:cf?cf.value:'',paid:pd?pd.value:''})})
 .then(function(r){return r.json();}).then(function(j){
  el.disabled=false;
  if(!j.ok){alert(j.message||'could not save that');return;}
  location.reload();
 }).catch(function(){el.disabled=false;alert('could not save that just now');});}
function payverify(m){
 var out=document.getElementById('vout');out.innerHTML='<div class="muted">checking\\u2026</div>';
 fetch(P+'/api/pay-verify',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({month:m})}).then(function(r){return r.json();}).then(function(j){
  if(!j.ok){out.innerHTML='<div class="bad">'+esc(j.message||'could not check')+'</div>';return;}
  location.reload();
 }).catch(function(){out.innerHTML='<div class="bad">could not check just now</div>';});}
function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,function(c){
 return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
"""

PAY_CSS = """
.payv{border-top:1px solid var(--line)}
.payv:first-child{border-top:0}
button.plain{display:flex;width:100%;align-items:center;gap:10px;background:none;border:0;
 padding:11px 2px;text-align:left;font:inherit;color:inherit;cursor:pointer;border-radius:0}
.vhead .car{color:var(--muted);transition:transform .15s}
.vhead.open .car{transform:rotate(90deg)}
.vn{flex:1;min-width:0;font-weight:600}
.vb{display:block;font-weight:400;font-size:12.5px}
.va{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
.payl{display:none;padding:0 0 8px 22px}
.payl.open{display:block}
.vstrip{padding:6px 0 10px;font-size:13px}
.payb{border-top:1px dotted var(--line)}
.payb .bno{font-weight:600;min-width:84px}
.payb .bdt{flex:1;font-size:13px}
.payb .bam{font-variant-numeric:tabular-nums;white-space:nowrap}
.paybd{display:none;padding:8px 0 10px 8px}
.paybd.open{display:block}
.paybd table{font-size:13px}
table.sheet{font-size:13.5px}
table.sheet th{white-space:nowrap}
input.pin{width:92px;font:inherit;text-align:right;padding:4px 6px;border:1px solid var(--line);
 border-radius:6px;background:#fffbe6}
"""

CSS = CSS + PAY_CSS
