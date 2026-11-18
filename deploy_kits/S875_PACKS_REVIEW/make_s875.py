#!/usr/bin/env python3
"""make_s875.py -- kit S875_PACKS_REVIEW (the parent, S480, 18-Nov-2026). His 'do all' 14:10 on the packs review, with his
rule: the section-8 bundles are NOT sent to the accountants unless he ticks them, month by month.

/root/finance/packs.py (S873's TO 0a50fd59) and packs.html (S866's TO 666fea71):
  8.x  bundles: the month's bills first, then 'scanned this month for earlier months' grouped by month, each with its count
       and total; a paper scanned after its month counts as late whether marked or not (B.L. Computers fell out of every
       pack); a paper with no total, a total of Rs 1 or less, no vendor, no bill date, or the same vendor + date + total as an
       earlier paper is KEPT OUT and named on his page ('fix it on the sorting desk'); each bundle goes in the mail only when
       he has ticked 'Send with the pack' for that month (pack_tick 'send8:<lane>'), a new door POST /finance/packs/api/send8.
  7    payment papers: a renewal / confirmation notice with no receipt and no card line is dropped; 'Payment successful for X'
       shows X as the vendor; NK Pathology's papers on their own sheet; a column naming the card line each one matches.
  4.4  card sheet: the statement periods at the top of the sheet; the page's statement table says what each covers.
Usage: python make_s875.py SRC_DIR OUT_DIR
"""
import hashlib
import os
import sys

FROM = {"packs.py": "0a50fd59dc07eab67ed63dcf855d0766", "packs.html": "666fea7116c30dcd20ffb433293b275d"}

NEW_BUNDLE = '''S875_HOLD_MAX_RS = 1.0                                    # S875: a total this small is a misread, never a bill


S875_LABELS = {"lab_purchase": "Dr Bhawna's lab-purchase bills", "owner_expense": "Dr Manoj's expense-file bills",
               "owner_expense_bhawna": "Dr Bhawna's expense-file bills", "construction_accountant": "Construction bills marked for the accountant"}
S875_VSKIP = {"M", "S", "MS", "MESSRS", "THE", "SHRI", "SRI", "SHREE", "NEW"}
S875_BACK_MONTHS = 12                                       # S875: a paper from further back is named, not bundled


def _s875_vkey(v):
    """The vendor's first real word ('M/s Alpha Traders' -> 'ALPHA')."""
    w = [x for x in re.sub(r"[^A-Z0-9 ]", " ", str(v or "").upper()).split() if x not in S875_VSKIP]
    return w[0] if w else ""


def _s875_back(month, k):
    y, m = int(month[:4]), int(month[5:7]) - k
    while m < 1:
        y, m = y - 1, m + 12
    return "%04d-%02d" % (y, m)


def bundle_rows(con, month, lane):
    """S875: the lane's papers for the month's bundle -- (rows, held, why).
    rows: the bills of the month, then the ones scanned this month for an earlier month (a paper scanned after its month is
    late whether or not it was marked so); held: the ones kept out until fixed on the sorting desk, each with its reason
    (no total, a total of Rs 1 or less, no vendor, no bill date, or the same vendor + date + total as an earlier paper);
    rows is None when the asset app cannot be read (why says so)."""
    acon = _assets_con()
    if acon is None:
        return None, [], "the asset app's database is not readable from here"
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        if "lane" not in cols:
            return None, [], "the asset app has no lanes yet (S409 not installed)"
        mcol = "COALESCE(NULLIF(bill_month,''), substr(bill_date,1,7))" if "bill_month" in cols else "substr(bill_date,1,7)"      # S434/S435 (F-658)
        qlane, who_sql = lane, ""                                    # S548 (D721): Dr Bhawna's expense file apart from Dr Manoj's
        lane_sql, xk_sql = "lane=?", ""                             # S560 (D728): construction bills for the accountant, any lane
        if "doc_kind" in cols:                                       # S560: a receipt / statement is never spend; an awaiting challan waits
            xk_sql = " AND COALESCE(doc_kind,'bill')='bill'"            # S568 (D730 item 5): only bills and invoices go to the accountants
        if lane != "construction_accountant" and {"to_accountant", "subgroup", "doc_kind"} <= cols:      # S560 FIX1 C1: a ticked
            xk_sql += (" AND NOT (COALESCE(subgroup,'')='construction' AND COALESCE(doc_kind,'bill')='bill'"   # construction bill goes
                       " AND COALESCE(to_accountant,0)=1)")                          # into the pack once: 8.4 only
        if lane == "construction_accountant":
            if "to_accountant" not in cols or "subgroup" not in cols or "doc_kind" not in cols:
                return [], [], "no construction bill is marked for the accountant yet"
            lane_sql, qlane = "subgroup=?", "construction"
            xk_sql += " AND COALESCE(doc_kind,'bill')='bill' AND to_accountant=1"
        elif lane == "owner_expense_bhawna":
            if "pe_who" not in cols:
                return [], [], "no personal expense is marked Dr Bhawna yet"
            qlane, who_sql = "owner_expense", " AND COALESCE(pe_who,'')='bhawna'"
        elif lane == "owner_expense" and "pe_who" in cols:
            who_sql = " AND COALESCE(pe_who,'')<>'bhawna'"
        rows = [dict(r) for r in acon.execute(
            "SELECT id, stamp_no, vendor, bill_no, bill_date, total_amount, source_stored, late_for, created_at, %s AS bmonth FROM bills WHERE %s AND status<>'rejected'%s "
            "AND ((%s=?) OR (substr(created_at,1,7)=? AND (%s<? OR %s IS NULL))) ORDER BY bill_date, id"
            % (mcol, lane_sql, who_sql + xk_sql, mcol, mcol, mcol), (qlane, month, month, month))]      # S875: scanned after its month = late
        lab = S875_LABELS.get(lane, "")                                 # S875: gone only if that month's mail CARRIED this bundle
        gone = {}
        for m_, at_, what_ in con.execute("SELECT month, sent_at, what FROM pack_send"):
            try:
                names = json.loads(what_ or "[]")
            except ValueError:
                names = []
            if lab and any(str(x).startswith(lab) for x in names):
                gone.setdefault(m_, []).append(str(at_ or ""))
        rows = [r for r in rows if not (r["bmonth"] and r["bmonth"] != month and any(s >= str(r["created_at"] or "") for s in gone.get(r["bmonth"], [])))]
        dk = " AND COALESCE(doc_kind,'bill')='bill'" if "doc_kind" in cols else ""
        cutoff = _s875_back(month, S875_BACK_MONTHS)
        keep, held = [], []
        for r in rows:
            tot = r.get("total_amount")
            why = ""
            if r.get("bmonth") and r["bmonth"] < cutoff:
                why = "from %s -- more than a year back, not bundled" % _month_name(r["bmonth"])
            elif not str(r.get("vendor") or "").strip():
                why = "no vendor read"
            elif not r.get("bmonth"):
                why = "no bill date"
            elif tot is None:
                why = "no total read"
            elif float(tot) <= S875_HOLD_MAX_RS:
                why = "total read as Rs %.2f" % float(tot)
            else:
                for o in acon.execute("SELECT id, stamp_no, vendor, lane, bill_no FROM bills WHERE id<? AND status<>'rejected' AND total_amount=? "
                                      "AND COALESCE(bill_date,'')=?%s" % dk, (r["id"], tot, r.get("bill_date") or "")):
                    n1, n2 = str(o[4] or "").strip().upper(), str(r.get("bill_no") or "").strip().upper()
                    if n1 and n2 and n1 != n2:                          # two bill numbers: two bills
                        continue
                    if _s875_vkey(o[2]) and _s875_vkey(o[2]) == _s875_vkey(r.get("vendor")):
                        why = "the same paper as %s (%s)" % (o[1] or "#%d" % o[0], o[3] or "?")
                        break
            if why:
                held.append(dict(r, why=why))
            else:
                keep.append(r)
    finally:
        acon.close()
    cur = [r for r in keep if r["bmonth"] == month]
    late = sorted([r for r in keep if r["bmonth"] != month], key=lambda r: (r["bmonth"] or "", r["bill_date"] or "", r["id"]))
    return cur + late, held, ""


def _s875_rs(rows):
    return sum(float(r["total_amount"] or 0) for r in rows)


def build_bundle(con, month, lane, count_only=False, pre=None):
    """(8) the lane's numbered bundle for the month: the index page (the month's bills, then the papers scanned this month
    for earlier months, month by month, each with its count and total), then each scan in the index's order. Papers
    held for a look (bundle_rows) are not in it. count_only: (number of papers, why) without building."""
    rows, held, why = pre if pre is not None else bundle_rows(con, month, lane)
    if rows is None:
        return None, why
    if not rows:
        what = {"owner_expense_bhawna": "Dr Bhawna expense", "construction_accountant": "construction bill (for the accountant)"}.get(lane, lane.replace("_", " "))
        return None, (why or "no %s scans for %s" % (what, _month_name(month))) + ((" (%d kept out until fixed)" % len(held)) if held else "")
    if count_only:
        return len(rows), ""
    cur = [r for r in rows if r["bmonth"] == month]
    late = [r for r in rows if r["bmonth"] != month]

    def line(r):
        return "%s  %s  %s  %s  %s" % (r["stamp_no"] or "-", _dmy(r["bill_date"]) if r["bill_date"] else _month_name(r["bmonth"] or month),
                                      (r["vendor"] or "")[:30], (r["bill_no"] or "")[:16],
                                      ("Rs %.2f" % r["total_amount"]) if r["total_amount"] is not None else "")
    idx = ["%s -- %d bill%s, Rs %.2f" % (_month_name(month), len(cur), "" if len(cur) == 1 else "s", _s875_rs(cur))]
    idx += ["    " + line(r) for r in cur] or ["    none this month"]
    if late:
        idx += ["", "Scanned in %s for earlier months -- %d bill%s, Rs %.2f" % (_month_name(month), len(late), "" if len(late) == 1 else "s", _s875_rs(late))]
        for bm in sorted({r["bmonth"] for r in late}):
            grp = [r for r in late if r["bmonth"] == bm]
            idx.append("  %s -- %d bill%s, Rs %.2f" % (_month_name(bm), len(grp), "" if len(grp) == 1 else "s", _s875_rs(grp)))
            idx += ["      " + line(r) for r in grp]
    tmp = tempfile.mkdtemp(prefix="bundle_")
    try:
        parts = [os.path.join(tmp, "00_index.pdf")]
        with open(parts[0], "wb") as fh:
            fh.write(_text_pdf("%s bills -- %s (%d)" % ({"owner_expense_bhawna": "Dr Bhawna Expense", "construction_accountant": "Construction"}.get(lane, lane.replace("_", " ").title()), _month_name(month), len(rows)), idx))   # S548; S560
        for i, r in enumerate(rows, 1):
            src = os.path.join(UPLOADS, r["source_stored"] or "")
            if not r["source_stored"] or not os.path.exists(src):
                continue
            dst = os.path.join(tmp, "%02d.pdf" % i)
            if src.lower().endswith(".pdf"):
                shutil.copy(src, dst)
            else:
                subprocess.run(["convert", src, dst], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            if os.path.exists(dst):
                parts.append(dst)
        out = os.path.join(tmp, "bundle.pdf")
        if len(parts) == 1:
            shutil.copy(parts[0], out)
        else:
            subprocess.run(["pdfunite"] + parts + [out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        if not os.path.exists(out):
            return None, "pdfunite could not build the bundle"
        with open(out, "rb") as fh:
            return fh.read(), None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


'''

P = []          # (old, new) on packs.py, applied in order; each old must occur exactly once

# 7: the vendor and the books of a payment paper
P.append(('''        seen.add(key)
        kept.append(dict(date=r[0], vendor=r[1], desc=desc, amount=amt, in_drive=r[5]))
        total += amt or 0
    return _one_row_per_charge(kept, dropped)
''', '''        seen.add(key)
        vendor = r[1]
        mv = re.match(r"(?i)^payment successful for (.+)$", desc)              # S875: the shop, not the payment company
        if mv:
            vendor = mv.group(1).strip()[:60]
        books = "NK Pathology" if re.search(r"\\bN\\.?\\s?K\\.?\\s+PATHOLOGY\\b", up) else ""   # S875: the lab's own sheet
        kept.append(dict(date=r[0], vendor=vendor, desc=desc, amount=amt, in_drive=r[5], books=books))
        total += amt or 0
    kept, dropped, total = _one_row_per_charge(kept, dropped)
    return _s875_digest_tidy(con, kept, dropped)


def _s875_card_match(con, r):
    """S875: the card line a payment paper matches (amount within Rs 1, date within 7 days) -- 'ICICI Amazon Pay, 16-Sep-2026'
    -- or ''."""
    amt = r.get("amount")
    if not amt or not _has(con, "card_line"):
        return ""
    try:
        d0 = dt.date.fromisoformat(str(r.get("date") or "")[:10])
    except ValueError:
        return ""
    row = con.execute("SELECT slot_key, txn_date FROM card_line WHERE COALESCE(credit,0)=0 AND ABS(amount_p - ?) <= 100 "
                      "AND txn_date BETWEEN ? AND ? ORDER BY ABS(julianday(txn_date) - julianday(?)), id LIMIT 1",
                      (int(round(float(amt) * 100)), (d0 - dt.timedelta(days=7)).isoformat(), (d0 + dt.timedelta(days=7)).isoformat(),
                       d0.isoformat())).fetchone()
    if not row:
        return ""
    return "%s, %s" % (_card_labels(con).get(row[0], row[0]), _dmy(row[1]))


def _s875_card_covered(con, date):
    """S875: is the date inside a card statement already read (so a missing card line means something)?"""
    if not _has(con, "card_stmt"):
        return False
    try:
        d0 = dt.date.fromisoformat(str(date or "")[:10]).isoformat()
    except ValueError:
        return False
    return con.execute("SELECT 1 FROM card_stmt WHERE period_from<=? AND period_to>=? LIMIT 1", (d0, d0)).fetchone() is not None


def _s875_digest_tidy(con, kept, dropped):
    """S875: each kept paper gets the card line it matches; a renewal / confirmation notice with no receipt (already paired
    away) and no card line is not a charge -- it is dropped with that reason. (kept, dropped, total Rs)."""
    out = []
    for r in kept:
        r["card"] = _s875_card_match(con, r)
        up = str(r.get("desc") or "").upper()
        notice = any(w in up for w in NOTICE_WORDS) and not any(w in up for w in RECEIPT_WORDS)
        if notice and not r["card"] and (not r.get("amount") or _s875_card_covered(con, r.get("date"))):
            dropped.append(dict(date=r["date"], vendor=r["vendor"], why="a renewal / confirmation notice with no receipt, and the card statements of that date carry no such line -- not a charge"))
            continue
        out.append(r)
    return out, dropped, round(sum((r["amount"] or 0) for r in out), 2)
'''))

P.append(('''    rows = [("Payment papers found in mail, %s -- one row per charge; most were paid by card, so these overlap the card spends" % _month_name(month), "", "", "", ""),
            ("Date", "Vendor", "Description", "Amount Rs", "Attachment in Drive")]                     # S538 (F-868)
    kept, dropped, total = digest_rows(con, month)
    for r in kept:
        rows.append((r["date"], r["vendor"], r["desc"], r["amount"] if r["amount"] is not None else "see the receipt", "yes" if r["in_drive"] else ""))
    if len(rows) == 2:
        return None, "no payments in the payment register for %s" % _month_name(month)
    rows.append(("", "", "TOTAL (rows with an amount)", total, ""))
    return _xlsx([("Payment papers %s" % month, rows)]), None
''', '''    kept, dropped, total = digest_rows(con, month)
    if not kept:
        return None, "no payments in the payment register for %s" % _month_name(month)
    head = ("Date", "Vendor", "Description", "Amount Rs", "Paid by card (its line in the card sheet, 4.4)", "Attachment in Drive")   # S875

    def sheet(rs, title):
        out = [(title, "", "", "", "", ""), head]
        for r in rs:
            out.append((r["date"], r["vendor"], r["desc"], r["amount"] if r["amount"] is not None else "see the receipt",
                        r.get("card") or "not on a card statement", "yes" if r["in_drive"] else ""))
        out.append(("", "", "TOTAL (rows with an amount)", round(sum((r["amount"] or 0) for r in rs), 2), "", ""))
        return out
    mine = [r for r in kept if not r.get("books")]
    nk = [r for r in kept if r.get("books")]
    sheets = [("Payment papers %s" % month, sheet(mine, "Payment papers found in mail, %s -- one row per charge; a card payment is also a line of the card sheet (4.4)" % _month_name(month)))]
    if nk:                                                              # S875: the lab's papers on their own sheet
        sheets.append(("NK Pathology %s" % month, sheet(nk, "NK Pathology's payment papers, %s -- the lab's own books" % _month_name(month))))
    return _xlsx(sheets), None
'''))

# 4.4: the statement periods
P.append(('''        return None, "a statement does not add up to its own totals (%s) -- look before it goes" % ", ".join(bad)
    return _xlsx(sheets), None
''', '''        return None, "a statement does not add up to its own totals (%s) -- look before it goes" % ", ".join(bad)
    cov = _s875_covers(con, v["statements"])                                # S875: what each statement covers, at the top
    if cov and sheets:
        t0, r0 = sheets[0]
        sheets[0] = (t0, [["Card statements DATED in %s -- each covers its own billing cycle, so many lines fall in the month before:" % _month_name(month)]]
                     + [[c] for c in cov] + [[]] + list(r0))
    return _xlsx(sheets), None


def _s875_covers(con, statements):
    """S875: 'ICICI Amazon Pay: 13-Sep-2026 to 12-Oct-2026' for each statement of the month ([] when unknown)."""
    out = []
    if not _has(con, "card_stmt"):
        return out
    for s in statements or []:
        r = con.execute("SELECT period_from, period_to FROM card_stmt WHERE slot_key=? AND statement_date=? ORDER BY id DESC LIMIT 1",
                        (s.get("slot"), s.get("statement_date"))).fetchone()
        if r and r[0] and r[1]:
            out.append("%s: %s to %s" % (s.get("label"), _dmy(r[0]), _dmy(r[1])))
    return out
'''))

P.append(('''    return card_lines.month_view(con, month, _card_labels(con))
''', '''    v = card_lines.month_view(con, month, _card_labels(con))
    try:                                                                # S875: the page says what each statement covers
        for s in v.get("statements") or []:
            r = con.execute("SELECT period_from, period_to FROM card_stmt WHERE slot_key=? AND statement_date=? ORDER BY id DESC LIMIT 1",
                            (s.get("slot"), s.get("statement_date"))).fetchone() if _has(con, "card_stmt") else None
            s["covers"] = ("%s to %s" % (_dmy(r[0]), _dmy(r[1]))) if (r and r[0] and r[1]) else ""
    except Exception:                                                  # noqa: BLE001
        pass
    return v
'''))

# 8: the opt-in per month, and the kept-out papers named
P.append(('''        b, why = build_bundle(con, month, lane, count_only=light)
        row("bundle:" + lane, "8.%d · Scanned bills: %s (numbered bundle + index)" % (n8, label), "ready" if b else "missing", why or "",
            ([("%s - %s.pdf" % (label, _month_name(month)), b, "application/pdf")] if b else None) if not light else None, None)   # S434
''', '''        try:
            pre = bundle_rows(con, month, lane)                                # S875: read once, kept-out papers named
        except Exception as ex:                                            # noqa: BLE001
            pre = (None, [], "the asset app could not be read (%s)" % type(ex).__name__)
        b, why = build_bundle(con, month, lane, count_only=light, pre=pre)
        held = pre[1] or []
        on = lane in sent8                                                  # S875: his tick, this month; absent = kept back
        hw = ("Kept out until fixed on the sorting desk: " + " · ".join("%s %s (%s)" % (h.get("stamp_no") or "#%d" % h["id"], (h.get("vendor") or "")[:24], h["why"]) for h in held[:8])
              + ((" + %d more" % (len(held) - 8)) if len(held) > 8 else "")) if held else ""
        w8 = why or ""
        if b and not on:
            w8 = "Kept back -- it goes to the accountants only when you tick 'Send with the pack' for this month."
        row("bundle:" + lane, "8.%d · Scanned bills: %s (numbered bundle + index)" % (n8, label), "ready" if b else "missing", " ".join(x for x in (w8, hw) if x),
            ([("%s - %s.pdf" % (label, _month_name(month)), b, "application/pdf")] if (b and on) else None) if not light else None, None)   # S434; S875
        rows[-1]["optin"] = dict(lane=lane, on=on, can=bool(b))
'''))

P.append(('''    for n8, (lane, label) in enumerate((("lab_purchase", "Dr Bhawna's lab-purchase bills"), ("owner_expense", "Dr Manoj's expense-file bills"),
''', '''    sent8 = {str(r[0])[6:] for r in con.execute("SELECT item FROM pack_tick WHERE month=? AND item LIKE 'send8:%'", (month,))}   # S875
    for n8, (lane, label) in enumerate((("lab_purchase", "Dr Bhawna's lab-purchase bills"), ("owner_expense", "Dr Manoj's expense-file bills"),
'''))

# the mail's body: a kept-back bundle is not named to the accountants
P.append(('''        for r in rows:
            body.append("%s  [%s]%s" % (r["title"], r["status"], ("  " + r["why"]) if (r["why"] and not r.get("owner_only_why")) else ""))   # S538
''', '''        for r in rows:
            if r.get("optin") is not None:                              # S875: section 8 is named only when it goes, and plainly
                if r["optin"].get("on") and r["optin"].get("can"):
                    body.append("%s  [enclosed]" % r["title"])
                continue
            body.append("%s  [%s]%s" % (r["title"], r["status"], ("  " + r["why"]) if (r["why"] and not r.get("owner_only_why")) else ""))   # S538
'''))

# the door
P.append(('''@bp.route("/finance/packs/api/send", methods=["POST"])
''', '''@bp.route("/finance/packs/api/send8", methods=["POST"])
def api_send8():
    """S875: his tick for one section-8 bundle, one month: on = it goes with the pack; off = kept back (the default)."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    m, lane = str(b.get("month") or ""), str(b.get("lane") or "")
    if not _good_month(m) or lane not in ("lab_purchase", "owner_expense", "owner_expense_bhawna", "construction_accountant"):
        return jsonify(ok=False, error="bad_request"), 400
    con = _db()
    ensure(con)
    if b.get("on") is True:
        con.execute("INSERT OR REPLACE INTO pack_tick (month, item, done_by, done_at) VALUES (?,?,?,?)", (m, "send8:" + lane, _who(u), _now()))
    else:
        con.execute("DELETE FROM pack_tick WHERE month=? AND item=?", (m, "send8:" + lane))
    con.commit()
    return jsonify(ok=True, on=(b.get("on") is True))


@bp.route("/finance/packs/api/send", methods=["POST"])
'''))

H = []          # packs.html
H.append(('''<th>Card</th><th>Statement dated</th><th>Lines</th>''', '''<th>Card</th><th>Statement dated</th><th>Covers</th><th>Lines</th>'''))
H.append(('''+'</td><td>'+esc(s.statement_date)+'</td><td>'+s.lines+''', '''+'</td><td>'+esc(s.statement_date)+'</td><td class="mut">'+esc(s.covers||"")+'</td><td>'+s.lines+'''))
H.append(('''<tr><td colspan="4" class="mut">none yet</td></tr>''', '''<tr><td colspan="5" class="mut">none yet</td></tr>'''))
H.append(('''      if(r.key.indexOf("bundle:")===0)pv='<a href="/finance/packs/preview/bundle_'+r.key.slice(7)+'?month='+j.month+'" target="_blank">the bundle</a>';
''', '''      if(r.key.indexOf("bundle:")===0)pv='<a href="/finance/packs/preview/bundle_'+r.key.slice(7)+'?month='+j.month+'" target="_blank">the bundle</a>';
      if(r.optin&&r.optin.can){pv+=' · <button class="ghost" onclick="send8(\\''+esc(r.optin.lane)+'\\','+(r.optin.on?'false':'true')+')">'+(r.optin.on?'Goes with the pack — keep it back':'Kept back — send with the pack')+'</button>'; if(!r.optin.on)st='<span class="mut">ready · kept back</span>'}   /* S875 */
'''))
H.append(('''function tick(k){''', '''function send8(l,on){post("/finance/packs/api/send8",{month:$("m").value,lane:l,on:on}).then(function(j){if(!j.ok){alert(j.message||j.error);return} flash(on?"It will go with the pack for this month.":"Kept back -- it will not go."); load()})}   /* S875 */
function tick(k){'''))


def swap_block(text, start, end, new):
    i = text.find(start)
    if i < 0 or text.find(start, i + 1) >= 0:
        raise SystemExit("STOP: the build_bundle start found %d times" % text.count(start))
    j = text.find(end, i)
    if j < 0 or text.count(end) != 1:
        raise SystemExit("STOP: the build_bundle end marker not found once")
    old = text[i:j]
    if old.count("(8) every S409 bill of the lane with bill_date in the month") != 1 or old.count("late_for IS NOT NULL") != 2:
        raise SystemExit("STOP: the old build_bundle is not the one read -- nothing written")
    return text[:i] + new + text[j:]


def apply(text, pairs, name):
    for k, (old, new) in enumerate(pairs, 1):
        n = text.count(old)
        if n != 1:
            raise SystemExit("STOP: %s anchor %d found %d times (want 1) -- nothing written" % (name, k, n))
        text = text.replace(old, new)
    return text


def main():
    src, out = sys.argv[1], sys.argv[2]
    res = {}
    for name in ("packs.py", "packs.html"):
        raw = open(os.path.join(src, name), "rb").read()
        md5 = hashlib.md5(raw).hexdigest()
        if md5 != FROM[name]:
            raise SystemExit("STOP: %s is %s, not the FROM %s -- nothing written" % (name, md5, FROM[name]))
        t = raw.decode("utf-8")
        if name == "packs.py":
            t = swap_block(t, "def build_bundle(con, month, lane, count_only=False):", "\n\ndef _nice(label):", NEW_BUNDLE.rstrip("\n"))
            t = apply(t, P, name)
        else:
            t = apply(t, H, name)
        res[name] = t
    os.makedirs(out, exist_ok=True)
    for name, t in res.items():
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(t)
        print("%s %s" % (hashlib.md5(t.encode("utf-8")).hexdigest(), name))


if __name__ == "__main__":
    main()
