

# =====================================================================================================================
# S440_SCAN_FLOW (30-Sep-2026, session 283, D640, F-662) -- "SCAN KA KAAM": ONE LIST, A TAP PER LINE
#
# The owner, 30-Sep: "Whatever needs to be done should be clearly mentioned in the staff scan app -- as with 'Bill scan
# karo' and then 'Scan' and there they tap 'scanned'. The scans with no readable supplier should be flagged the same way."
# S439 taught the matcher to say WHY a scan has no link, but only the owner's page said it; reception's list still asked
# for six bills whose scan was already there. Here every line a person must decide carries its own buttons:
#   1 scan     Scan karo        a Marg bill with no scan and no near-match: the S403 pre-filled intake. Marg's double
#                               entry (the same number twice) shows ONCE and its extra row goes on the WRONG list (S371).
#   2 confirm  Yahi bill hai?   the matcher's likely bill for a scan (number or amount read differently): Haan links it
#                               (grade CONFIRMED, "reception confirmed", audited) -- or, when that bill already has a
#                               scan, marks this paper a second scan; Nahi clears the hint for good.
#   3 vendor   Supplier chuno   a scan whose vendor OCR could not read: the choice is kept for that scan and, when the
#                               OCR text is a real spelling (never the buyer's own name), learned in purchase_scan_alias.
#   4 amount   Amount milao     a linked scan and Marg disagree on the amount by more than 2%: the staff types the
#                               amount ON THE PAPER. = the scan -> Marg galat (the S371 WRONG mark on the bill);
#                               = Marg -> Scan galat padha (the link becomes EXACT, the paper amount is kept in
#                               purchase_scan_state, never in assets.db); neither -> a Needs-you line for the owner.
#   5 wait     Marg ka intezaar a scan of a bill Marg has not sent yet: no button.
# What a person decided lives in purchase_scan_state (additive columns) and rides every pass of the matcher
# (purchase_app._rematch). assets.db stays READ ONLY here; "Galat lane" is the asset app's own re-lane route.
# The read door /finance/porders/api/scan-status gives the asset app's list its status words -- on THIS unit, because
# the reception logins hold a role here and none on /finance/purchase (the brief named that path).
# =====================================================================================================================
S440_FROM = "/finance/porders"
S440_DOUBLE = "Marg mein do baar"
S440_WORDS = {"linked": "Marg se mil gaya", "wait": "Marg ka intezaar (Amir)", "you": "Aapka jawab chahiye → Scan ka kaam",
              "dup": "Doosri baar scan"}
S440_TOL_P = 100                  # a rupee: two amounts are "the same" within this
S440_ASK = ("number_differs", "amount_differs", "no_digits")     # the reasons that can name a likely bill: "Yahi bill hai?"


def _s440_rs(p):
    """Paise -> '₹1,424' or '₹842.70' (the paise shown only when there are any)."""
    if p is None:
        return "—"
    p = int(p)
    whole = _pa()._r(p - (p % 100) if p >= 0 else p)
    return whole if p % 100 == 0 else "%s.%02d" % (whole, abs(p) % 100)


def _s440_scans(con):
    """The pharmacy scans as the asset app holds them (READ ONLY): {id: dict}; None when its database is not reachable."""
    pa = _pa()
    acon = pa._assets_con()
    if acon is None:
        return None
    try:
        rows = acon.execute("SELECT id, vendor, bill_no, bill_date, total_amount, stamp_no, created_at FROM bills "
                            "WHERE kind='Pharmacy' AND COALESCE(status,'')<>'rejected' ORDER BY id DESC LIMIT 2000").fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        acon.close()
    out = {}
    today = dt.date.today()
    for r in rows:
        amt = pa._float_or_none(r["total_amount"])
        try:
            age = (today - dt.date.fromisoformat(str(r["created_at"] or "")[:10])).days
        except ValueError:
            age = 0
        out[r["id"]] = dict(id=r["id"], vendor=r["vendor"] or "", bill_no=str(r["bill_no"] or ""), bill_date=str(r["bill_date"] or ""),
                            amount_p=(int(round(amt * 100)) if amt is not None else None), stamp=r["stamp_no"] or ("#%d" % r["id"]),
                            age=max(0, age))
    return out


def _s440_state(con):
    try:
        return {r["asset_bill_id"]: dict(r) for r in con.execute("SELECT * FROM purchase_scan_state")}
    except sqlite3.Error:
        return {}


def _s440_bills(con):
    pa = _pa()
    try:
        return {b["id"]: dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL)}
    except sqlite3.Error:
        return {}


def _s440_month_final(con, month):
    try:
        r = con.execute("SELECT status FROM purchase_month WHERE month=?", (month or "",)).fetchone()
        return bool(r and r[0] == "final")
    except sqlite3.Error:
        return False


def _s440_doubles(con, bills, linked):
    """Marg's double entries since porders.scan_from: the same supplier, date and amount under one number typed in two
    cases. -> ({extra bill id: the row shown}, {shown id: [numbers]}, {ids of a group one of whose rows has a scan}).
    The extra row is marked WRONG (should be Rs 0) once -- the S371 list -- and the mark is lifted when its twin is gone."""
    since = _scan_from(con)
    groups = {}
    for b in bills.values():
        if str(b.get("bill_date") or "") >= since:
            groups.setdefault((b["supplier_norm"], str(b["bill_no"] or "").strip().lower(), b["bill_date"], b["amount_p"]), []).append(b)
    extra, shown, scanned, twins = {}, {}, set(), set()
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda b: (0 if b["id"] in linked else 1, b["id"]))      # the row a scan is linked to is the one kept
        first = members[0]
        shown[first["id"]] = [str(m["bill_no"]) for m in members]
        has_scan = any(m["id"] in linked for m in members)
        for m in members:
            twins.add(m["id"])
            if has_scan:
                scanned.add(m["id"])
        for m in members[1:]:
            extra[m["id"]] = first["id"]
            if not m.get("verdict") and not _s440_month_final(con, m.get("month")):
                why = "%s: bill %s aur %s (%s, %s) -- ek entry hatao" % (S440_DOUBLE, first["bill_no"], m["bill_no"], _pa().supplier_key(m["supplier"]), _dmy(m["bill_date"]))
                con.execute("UPDATE purchase_bill SET verdict='WRONG', verdict_by=?, verdict_at=?, wrong_amount_p=0, reason=? WHERE id=?",
                            ("S440 rule", now_iso(), why, m["id"]))
                _audit(con, "S440 rule", "double_entry", m["id"], dict(verdict="WRONG", wrong_amount_p=0, twin=first["id"], reason=why))
                con.commit()
    try:                                                          # the twin is gone from Marg: the mark has done its work
        for r in con.execute("SELECT id FROM purchase_bill WHERE verdict='WRONG' AND verdict_by='S440 rule' AND reason LIKE ?", (S440_DOUBLE + "%",)).fetchall():
            if r[0] in bills and r[0] not in twins:
                con.execute("UPDATE purchase_bill SET verdict=NULL, verdict_by=NULL, verdict_at=NULL, wrong_amount_p=NULL, reason=NULL WHERE id=?", (r[0],))
                _audit(con, "S440 rule", "double_resolved", r[0], dict(before="WRONG"))
                con.commit()
    except sqlite3.Error:
        pass
    return extra, shown, scanned


def _s440_differs(scan_p, marg_p):
    return scan_p is not None and abs(int(scan_p) - int(marg_p)) > max(S440_TOL_P, int(round(0.02 * int(marg_p))))


def scan_work(con, run_pass=True):
    """The five groups of "Scan ka kaam" (the header above), as plain rows for the page. n = the lines a person must act
    on (groups 1-4); group 5 waits for Marg and carries no button."""
    pa = _pa()
    out = dict(ok=True, n=0, counts=dict(scan=0, confirm=0, vendor=0, amount=0, wait=0, dup=0), scan=[], confirm=[], vendor=[], amount=[], wait=[],
               received=[], suppliers=[], reachable=True)
    unscanned = unscanned_bills(con)                              # first: it runs the matcher when the scans have changed (S225 rev 9)
    scans = _s440_scans(con)
    if scans is None:
        out["reachable"] = False
        scans = {}
    st = _s440_state(con)
    bills = _s440_bills(con)
    links, by_scan = {}, {}
    try:
        for r in con.execute("SELECT bill_id, asset_bill_id, grade, matched_on FROM purchase_scan_link"):
            links[r[0]] = (r[1], r[2], r[3])
            by_scan[r[1]] = (r[0], r[2], r[3])
    except sqlite3.Error:
        pass

    def pic(sid):
        return dict(thumb="/scanapp/bills/%d/thumb" % sid, pdf="/scanapp/bills/%d/file" % sid)

    def bill_row(b):
        return dict(bill_id=b["id"], vendor=pa.supplier_key(b["supplier"]), bill_no=str(b["bill_no"] or ""), date_text=_dmy(b["bill_date"]),
                    amount=_s440_rs(b["amount_p"]), amount_p=int(b["amount_p"] or 0))

    def scan_row(s):
        return dict(scan=s["id"], stamp=s["stamp"], scan_vendor=s["vendor"], scan_no=s["bill_no"], scan_date=_dmy(s["bill_date"]) if s["bill_date"] else "",
                    scan_amount=_s440_rs(s["amount_p"]), scan_amount_p=s["amount_p"], age=s["age"], **pic(s["id"]))

    pending_bills = set()                                         # a bill a near-match is waiting on is not asked for again
    for sid in sorted(scans):
        s, row = scans[sid], st.get(sid) or {}
        if sid in by_scan:                                        # 4 -- linked, the two amounts more than 2% apart, nobody has answered
            b = bills.get(by_scan[sid][0])
            sp = row.get("paper_amount") if row.get("paper_amount") is not None else s["amount_p"]
            if b is not None and not row.get("amount_state") and _s440_differs(sp, b["amount_p"]):
                out["amount"].append(dict(scan_row(s), **bill_row(b)))
            continue
        why = row.get("why") or ""
        if why == "dup":
            out["counts"]["dup"] += 1
            continue
        lb = bills.get(row.get("likely_bill")) if why in S440_ASK else None
        if lb is not None:                                        # 2 -- the matcher's likely bill
            taken = links.get(lb["id"])
            if not taken:
                pending_bills.add(lb["id"])
            out["confirm"].append(dict(scan_row(s), why=why, taken_by=(taken[0] if taken else None),
                                       taken_stamp=((scans.get(taken[0]) or {}).get("stamp") if taken else None), **bill_row(lb)))
        elif why == "vendor_unknown" and not row.get("chosen_vendor"):
            out["vendor"].append(scan_row(s))                     # 3 -- nobody could read the supplier
        else:                                                     # 5 -- nothing for a person to do
            note = ("Number / amount nahi padha gaya — manager isse theek karega, dobara scan mat karo" if why == "no_digits"
                    else "Supplier list mein nahi — Marg ki entry ka intezaar" if row.get("chosen_vendor") == "-"
                    else "Amir ke entry ke baad khud jud jayega")
            out["wait"].append(dict(scan_row(s), note=note, note_en=("OCR read no number / amount — the manager corrects it" if why == "no_digits"
                                                                   else "waits for Marg's entry; it links by itself")))
    extra, shown, scanned_twin = _s440_doubles(con, bills, links)
    for x in unscanned:                                           # 1 -- a Marg bill nobody has scanned
        bid = x["bill_id"]
        if bid in pending_bills or bid in extra or bid in scanned_twin:
            continue
        out["scan"].append(dict(x, double=(bid in shown), double_nos=shown.get(bid) or []))
    try:                                                          # S403's received orders whose bill Marg has not got yet ride group 1
        out["received"] = received_unbilled(con, unscanned)
    except Exception:                                             # noqa: BLE001
        out["received"] = []
    for k in ("scan", "confirm", "vendor", "amount", "wait"):
        out["counts"][k] = len(out[k])
    out["counts"]["scan"] += len(out["received"])
    out["n"] = out["counts"]["scan"] + out["counts"]["confirm"] + out["counts"]["vendor"] + out["counts"]["amount"]
    if out["vendor"]:
        out["suppliers"] = sorted({pa.supplier_key(b["supplier"]) for b in bills.values() if b.get("supplier")})
    return out


def _s440_kaam(con):
    """state()'s 'kaam': the five groups; the rest of the screen never waits for them."""
    try:
        return scan_work(con)
    except Exception as e:                                        # noqa: BLE001
        return dict(ok=False, n=0, counts={}, scan=[], confirm=[], vendor=[], amount=[], wait=[], received=[], suppliers=[], error=str(e)[:120])


def _s440_put(con, sid, who, **cols):
    """One decision of a person on one scan: upsert its purchase_scan_state row (a linked scan has none until now)."""
    _pa()._ensure_s439(con)
    con.execute("INSERT OR IGNORE INTO purchase_scan_state (asset_bill_id, why, detail, checked_at) VALUES (?,?,?,?)", (sid, "linked", "linked", now_iso()))
    cols = dict(cols, confirmed_by=who, confirmed_at=now_iso())
    con.execute("UPDATE purchase_scan_state SET %s WHERE asset_bill_id=?" % ", ".join("%s=?" % k for k in sorted(cols)),
                [cols[k] for k in sorted(cols)] + [sid])


def _s440_write(u, kind):
    if kind not in ("owner", "sender"):
        return _forbid_view(kind)
    return None


def _s440_scan_arg(b):
    try:
        return int(b.get("scan") or 0)
    except (TypeError, ValueError):
        return 0


@bp.route("/finance/porders/api/scan/confirm", methods=["POST"])
def api_scan_confirm():
    """Yahi bill hai? -- Haan links the scan to the matcher's likely bill (or marks the paper a second scan when that
    bill already has one); Nahi clears the hint, and the bill goes back to Scan karo."""
    u, con, kind, err = _auth()
    if err:
        return err
    no = _s440_write(u, kind)
    if no:
        return no
    pa = _pa()
    b = request.get_json(silent=True) or {}
    sid = _s440_scan_arg(b)
    who = u.get("user") or ""
    pa._ensure_s439(con)
    row = _s440_state(con).get(sid)
    if not row or not row.get("likely_bill") or row.get("why") not in S440_ASK:
        return jsonify(ok=False, error="no_hint", message="Is scan ke liye ab koi sawaal nahi hai."), 409
    bid = int(row["likely_bill"])
    if int(b.get("bill") or 0) != bid:
        return jsonify(ok=False, error="stale", message="List badal gayi hai — dobara kholiye."), 409
    bill = con.execute("SELECT id, supplier, bill_no, month FROM purchase_bill WHERE id=?", (bid,)).fetchone()
    if not bill:
        return jsonify(ok=False, error="no_such_bill"), 404
    if not b.get("yes"):
        no_list = sorted({int(x) for x in str(row.get("hint_no") or "").split(",") if x.strip().isdigit()} | {bid})
        _s440_put(con, sid, who, hint_no=",".join(str(x) for x in no_list))
        _audit(con, who, "scan_hint_refused", bid, dict(scan=sid, kit="S440", note="reception: yeh bill nahi hai"))
        con.commit()
        pa._rematch(con, who)
        return jsonify(ok=True, scan=sid, linked=False, message="Theek hai — yeh bill nahi hai.")
    taken = con.execute("SELECT asset_bill_id FROM purchase_scan_link WHERE bill_id=?", (bid,)).fetchone()
    if taken and int(taken[0]) != sid:                            # the bill already has a scan: this paper is its second scan
        _s440_put(con, sid, who, dup_ok=int(taken[0]))
        _audit(con, who, "scan_dup_confirmed", bid, dict(scan=sid, dup_cand=int(taken[0]), kit="S440", note="reception confirmed"))
        con.commit()
        pa._rematch(con, who)
        return jsonify(ok=True, scan=sid, linked=False, second_scan=True, message="Theek hai — yeh kaagaz pehle scan ho chuka tha.")
    con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (bid, sid, "CONFIRMED", "reception confirmed", now_iso()))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, bid))
    _s440_put(con, sid, who)
    _audit(con, who, "scan_link", bid, dict(scan=sid, grade="CONFIRMED", rule="reception confirmed", supplier=pa.supplier_key(bill[1]), bill_no=bill[2], kit="S440"))
    con.commit()
    pa._rematch(con, who)
    return jsonify(ok=True, scan=sid, bill=bid, linked=True, message="Jud gaya — bill %s." % bill[2])


@bp.route("/finance/porders/api/scan/vendor", methods=["POST"])
def api_scan_vendor():
    """Supplier chuno -- the choice is kept for this scan; when the OCR text is a real spelling (not empty, not the
    buyer's own name) it is learned once in purchase_scan_alias. The matcher runs at once."""
    u, con, kind, err = _auth()
    if err:
        return err
    no = _s440_write(u, kind)
    if no:
        return no
    pa = _pa()
    b = request.get_json(silent=True) or {}
    sid = _s440_scan_arg(b)
    who = u.get("user") or ""
    pa._ensure_s439(con)
    scans = _s440_scans(con) or {}
    row = _s440_state(con).get(sid)
    if sid not in scans or not row or row.get("why") != "vendor_unknown":
        return jsonify(ok=False, error="no_such_line", message="Is scan ke liye supplier nahi poochha ja raha."), 409
    choice = str(b.get("vendor") or "").strip()
    suppliers = {pa.supplier_key(x["supplier"]) for x in _s440_bills(con).values() if x.get("supplier")}
    if choice != "-" and choice not in suppliers:
        return jsonify(ok=False, error="bad_vendor", message="List mein se supplier chuniye."), 400
    _s440_put(con, sid, who, chosen_vendor=choice)
    learned = False
    ocr = pa.supplier_key(scans[sid]["vendor"])
    toks = pa._vendor_tokens_s439(scans[sid]["vendor"])
    if choice != "-" and ocr and toks and not pa._is_buyer_s439(toks):
        cur = con.execute("INSERT OR IGNORE INTO purchase_scan_alias (ocr_norm, supplier_norm, scan_id, who, at) VALUES (?,?,?,?,?)",
                          (ocr, choice, sid, "S440 %s chose for scan %d" % (who, sid), now_iso()))
        learned = bool(cur.rowcount)
        if learned:
            _audit(con, who, "alias_learn", ocr, dict(supplier=choice, note="S440 %s chose for scan %d" % (who, sid)))
    _audit(con, who, "scan_vendor_chosen", sid, dict(scan=sid, vendor=choice, learned=learned, kit="S440"))
    con.commit()
    pa._rematch(con, who)
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    return jsonify(ok=True, scan=sid, vendor=choice, learned=learned, linked=bool(lk),
                   message=("Jud gaya." if lk else "Supplier likh liya — Marg ki entry ka intezaar."))


@bp.route("/finance/porders/api/scan/amount", methods=["POST"])
def api_scan_amount():
    """Amount milao -- the amount ON THE PAPER, typed. = the scan: Marg galat (the S371 WRONG mark, the link stays).
    = Marg: Scan galat padha (the link EXACT, the paper amount kept in purchase_scan_state). Neither: the owner's line."""
    u, con, kind, err = _auth()
    if err:
        return err
    no = _s440_write(u, kind)
    if no:
        return no
    pa = _pa()
    b = request.get_json(silent=True) or {}
    sid = _s440_scan_arg(b)
    who = u.get("user") or ""
    raw = str(b.get("paper") or "").replace(",", "").replace("₹", "").strip()
    if not re.fullmatch(r"\d{1,9}(\.\d{1,2})?", raw):
        return jsonify(ok=False, error="bad_amount", message="Sirf ank likhiye — jaise 14442"), 400
    paper = int(round(float(raw) * 100))
    pa._ensure_s439(con)
    lk = con.execute("SELECT bill_id, grade FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    scans = _s440_scans(con) or {}
    if not lk or sid not in scans:
        return jsonify(ok=False, error="no_such_line", message="Yeh scan kisi bill se juda nahi hai."), 409
    bill = con.execute("SELECT id, supplier, bill_no, amount_p, month, verdict FROM purchase_bill WHERE id=?", (lk[0],)).fetchone()
    row = _s440_state(con).get(sid) or {}
    scan_p = row.get("paper_amount") if row.get("paper_amount") is not None else scans[sid]["amount_p"]
    marg_p = int(bill[3] or 0)
    if row.get("amount_state") or not _s440_differs(scan_p, marg_p):
        return jsonify(ok=False, error="settled", message="Is line ka jawab pehle hi darj hai."), 409
    sup = pa.supplier_key(bill[1])
    if abs(paper - marg_p) <= S440_TOL_P:                         # the paper agrees with Marg: OCR misread the scan
        con.execute("UPDATE purchase_scan_link SET grade='EXACT', matched_on=? WHERE bill_id=?", ("paper amount = Marg (reception)", bill[0]))
        _s440_put(con, sid, who, paper_amount=paper, amount_state="scan_wrong")
        _audit(con, who, "scan_amount", bill[0], dict(scan=sid, outcome="scan_wrong", paper_p=paper, scan_p=scan_p, marg_p=marg_p, grade="EXACT", kit="S440"))
        con.commit()
        out = dict(outcome="scan_wrong", message="Scan galat padha tha — theek kar diya.")
    elif abs(paper - int(scan_p)) <= S440_TOL_P and not bill[5] and not _s440_month_final(con, bill[4]):
        why = "bill %s %s: paper Rs %s, Marg Rs %s (Scan ka kaam, %s)" % (bill[2], sup, _s440_rs(paper)[1:], _s440_rs(marg_p)[1:], who)
        con.execute("UPDATE purchase_bill SET verdict='WRONG', verdict_by=?, verdict_at=?, wrong_amount_p=?, reason=? WHERE id=?",
                    (who, now_iso(), paper, why, bill[0]))
        _s440_put(con, sid, who, paper_amount=paper, amount_state="marg_wrong")
        _audit(con, who, "verdict", bill[0], dict(verdict="WRONG", wrong_amount_p=paper, reason=why, before=bill[5], via="Scan ka kaam"))
        _audit(con, who, "scan_amount", bill[0], dict(scan=sid, outcome="marg_wrong", paper_p=paper, scan_p=scan_p, marg_p=marg_p, kit="S440"))
        con.commit()
        out = dict(outcome="marg_wrong", message="Marg galat hai — Amir ki list par chala gaya.")
    else:                                                         # neither (or the bill already carries a person's verdict / a final month): the owner
        _s440_put(con, sid, who, paper_amount=paper, amount_state="owner")
        _audit(con, who, "scan_amount", bill[0], dict(scan=sid, outcome="owner", paper_p=paper, scan_p=scan_p, marg_p=marg_p, kit="S440"))
        con.commit()
        out = dict(outcome="owner", message="Dr sahab ko dikhao — unki list par chala gaya.")
    return jsonify(ok=True, scan=sid, bill=bill[0], **out)


def scan_status(con, ids):
    """The read door's answer: {scan id: {code, word, first}} in staff words. first = the scan this one repeats."""
    st = _s440_state(con)
    by_scan = {}
    try:
        by_scan = {r[0]: r[1] for r in con.execute("SELECT asset_bill_id, bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        pass
    bills, scans, out = None, {}, {}
    for sid in ids:
        row = st.get(sid) or {}
        if sid in by_scan:
            code = "linked"
            if not row.get("amount_state"):
                if bills is None:
                    bills = _s440_bills(con)
                    scans = _s440_scans(con) or {}
                b, s = bills.get(by_scan[sid]), scans.get(sid)
                sp = row.get("paper_amount") if row.get("paper_amount") is not None else (s or {}).get("amount_p")
                if b is not None and _s440_differs(sp, b["amount_p"]):
                    code = "you"
        elif not row:
            continue                                              # not a pharmacy scan the matcher has seen: no word
        elif row.get("why") == "dup":
            code = "dup"
        elif (row.get("why") in S440_ASK and row.get("likely_bill")) or (row.get("why") == "vendor_unknown" and not row.get("chosen_vendor")):
            code = "you"
        else:
            code = "wait"
        out[str(sid)] = dict(code=code, word=S440_WORDS[code], first=(row.get("dup_cand") if code == "dup" else None))
    return out


@bp.route("/finance/porders/api/scan-status")
def api_scan_status():
    """READ ONLY, inside this unit's login gate: the asset app's list asks what each of its scans is waiting for."""
    u, con, kind, err = _auth()
    if err:
        return err
    ids = []
    for x in str(request.args.get("ids") or "").split(",")[:400]:
        if x.strip().isdigit():
            ids.append(int(x))
    return jsonify(ok=True, status=scan_status(con, ids), url=S440_FROM)


def _s440_owner_lines(con):
    """Needs you: the paper amount matched neither the scan nor Marg (or the bill already carried a verdict)."""
    out = []
    try:
        rows = con.execute("SELECT s.asset_bill_id, s.paper_amount, l.bill_id FROM purchase_scan_state s JOIN purchase_scan_link l "
                           "ON l.asset_bill_id=s.asset_bill_id WHERE s.amount_state='owner'").fetchall()
        for r in rows:
            b = con.execute("SELECT supplier, bill_no, amount_p, verdict FROM purchase_bill WHERE id=?", (r[2],)).fetchone()
            if b and not b[3] and abs(int(r[1] or 0) - int(b[2] or 0)) > S440_TOL_P:      # gone once the bill has a verdict, or Marg now says the paper's amount
                out.append(dict(cls="warn", target="porders", text="Scan amount to settle: bill %s %s — the paper reads %s, Marg %s (scan #%d)"
                                % (b[1], _pa().supplier_key(b[0]), _s440_rs(r[1]), _s440_rs(b[2]), r[0])))
    except sqlite3.Error:
        pass
    return out
