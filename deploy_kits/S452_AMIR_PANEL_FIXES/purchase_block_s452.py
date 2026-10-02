# ==========================================================================================================================================
# S452_AMIR_PANEL_FIXES (02-Oct-2026, F-686) -- Amir's "Marg mein daalne ke bill" holds only bills that are NOT in Marg.
# The owner, 01-Oct: "The scanned medicine bills are simply made available to him at one place so he can upload them in the digital entry
# part of Marg ... That will be the final entry of the bill." S446 listed EVERY captured pharmacy scan with no Marg link -- near-matches
# reception had not answered, unread suppliers, the shop's own name read as the supplier -- and a bill uploaded again is a second purchase.
#   * scans_for_amir(con) -> {list, held}: a scan is LISTED only when the server finds no likely Marg bill for it and its supplier is known
#     -- S440's "Marg ka intezaar" group as purchase_scan_state holds it (the matcher runs first when the scans changed). A near-match
#     (Yahi bill hai?), an unread supplier (Supplier chuno), the buyer's own name, a second scan: HELD -- reception's Scan ka kaam first.
#   * Each listed line carries what is known: the stamp, the supplier (chosen, else matched, else as read), "scan: dd-mm, <who>", and the
#     bill date only when it lies within 60 days of the scan day. The file: <stamp>_<SUPPLIER>[_<billno>]_<dd-mm-yyyy>.pdf -- a bill number
#     not read is left out; a date outside the 60 days is replaced by the scan day.
#   * The download guard: a scan Marg's bill has reached since the page was drawn answers "Yeh bill Marg mein aa chuka hai"; a held scan
#     answers "reception ki jaanch mein". The zip of today's follows the same rule.
#   * The owner's Scan links page: "Amir's list: N to enter · M held for reception".
#   * The bank's NEFT advice file (full account numbers) is the owner's and the senders' (supplier_msg.senders) -- no staff login else.
# ==========================================================================================================================================
S452_DATE_DAYS = 60


def _s452_scan_rows():
    """The captured pharmacy scans, no duplicates of another (assets.db, READ ONLY); None when that database is not reachable."""
    acon = _assets_con()
    if acon is None:
        return None
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        sel = ["id", "stamp_no", "vendor", "bill_no", "bill_date", "created_at"] + [c for c in ("dup_of", "submitted_by", "scanned_by", "created_by") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND status='captured' ORDER BY created_at, id" % ", ".join(sel))]
    finally:
        acon.close()
    return [r for r in rows if not r.get("dup_of")]


def _s452_name(stamp, supplier, bill_no, day_iso):
    st = re.sub(r"[^A-Za-z0-9-]+", "_", str(stamp or "")).strip("_") or "SCAN"
    sup = re.sub(r"[^A-Z0-9]+", "_", str(supplier or "").upper()).strip("_")[:40] or "SUPPLIER"
    bno = re.sub(r"[^A-Za-z0-9]+", "", str(bill_no or ""))
    d = str(day_iso or "")[:10]
    d = (d[8:10] + "-" + d[5:7] + "-" + d[:4]) if len(d) == 10 else dt.date.today().strftime("%d-%m-%Y")
    return "_".join([st, sup] + ([bno] if bno else []) + [d]) + ".pdf"


def scans_for_amir(con):
    """{list: [scans to put into Marg], held: [scans waiting for reception], ok} -- the rule in the header above."""
    try:
        _rematch_if_changed(con, "S452 list")                  # a scan that changed is matched before it is shown to anyone
    except Exception:                                          # noqa: BLE001
        pass
    rows = _s452_scan_rows()
    if rows is None:
        return dict(list=[], held=[], ok=False)
    linked = _s446_linked(con)
    try:
        _ensure_s439(con)
        st = {int(r["asset_bill_id"]): dict(r) for r in con.execute("SELECT * FROM purchase_scan_state")}
    except sqlite3.Error:
        st = {}
    bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    bill_ids = {b["id"] for b in bills}
    ctx = _vendor_ctx_s439(con, bills)
    suppliers = set(ctx["canon"].values())
    today = dt.date.today()
    out, held = [], []
    for r in rows:
        sid = int(r["id"])
        if sid in linked:
            continue
        s = st.get(sid) or {}
        why = s.get("why") or ""
        chosen = str(s.get("chosen_vendor") or "")
        cday = _date_or_none_s439(str(r.get("created_at") or "")[:10])
        item = dict(id=sid, stamp=r.get("stamp_no") or ("#%d" % sid), read_vendor=r.get("vendor") or "", bill_no=str(r.get("bill_no") or ""),
                    created_at=r.get("created_at") or "", scan_day=(cday.isoformat() if cday else ""),
                    scan_ddmm=(cday.strftime("%d-%m") if cday else "-"),
                    who=str(r.get("submitted_by") or r.get("scanned_by") or r.get("created_by") or ""), today=(cday == today))
        reason = None
        if why == "dup":
            reason = "second scan"
        elif why in ("number_differs", "amount_differs", "no_digits") and s.get("likely_bill") in bill_ids:
            reason = "near-match"
        elif why == "vendor_unknown" and not chosen:
            reason = "supplier unread"
        sup = None
        if reason is None:
            if chosen and chosen != "-" and chosen in suppliers:
                sup = chosen
            else:
                k, how, _sc = _vendor_resolve_s439(r.get("vendor"), ctx)
                sup = k if how in ("exact", "learned", "similar") else None
            if not sup:
                reason = "supplier unknown"
        if reason:
            item["held"] = reason
            held.append(item)
            continue
        bd = _iso(r.get("bill_date")) or _iso_any(r.get("bill_date")) or ""
        bdd = _date_or_none_s439(bd)
        near = bdd is not None and cday is not None and abs((cday - bdd).days) <= S452_DATE_DAYS
        item.update(supplier=sup, bill_date=(bd if near else ""),
                    name=_s452_name(item["stamp"], sup, item["bill_no"], bd if near else (item["scan_day"] or today.isoformat())))
        out.append(item)
    return dict(list=out, held=held, ok=True)


def _s452_lookup(con, sid):
    """('list', item) | ('held', item) | ('linked', None) | (None, None) for one scan, by the same rule as the page."""
    r = scans_for_amir(con)
    for x in r["list"]:
        if x["id"] == int(sid):
            return "list", x
    for x in r["held"]:
        if x["id"] == int(sid):
            return "held", x
    if int(sid) in _s446_linked(con):
        return "linked", None
    return None, None


def _s452_small_page(kind):
    if kind == "linked":
        h, p = "Yeh bill Marg mein aa chuka hai", "Marg ki export mein yeh bill mil gaya hai — ise dobara Marg mein mat daaliye. List dobara kholiye: yeh line hat jayegi."
    else:
        h, p = "Yeh scan abhi reception ki jaanch mein hai", "Marg mein mat daaliye — reception ka jawab aane ke baad hi yeh list mein aayega."
    html = ('<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s</title></head><body style="margin:0;padding:16px;background:#fafafa;font:18px/1.5 system-ui,sans-serif">'
            '<div style="background:#fff;border:2px solid #8a6100;border-radius:10px;padding:14px"><h2 style="margin:0 0 8px">%s</h2><p>%s</p>'
            '<p><a href="/finance/amir/step/2">&larr; Wapas: Marg mein daalne ke bill</a></p></div></body></html>' % (_esc(h), _esc(h), _esc(p)))
    return html, 409, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


def _s452_amir_list_line(con):
    """One line on the owner's Scan links page."""
    try:
        r = scans_for_amir(con)
        if not r.get("ok"):
            return ""
        return ('<div class="card" id="s452amirlist"><div class="muted"><b>Amir\'s list: %d to enter · %d held for reception</b></div></div>'
                % (len(r["list"]), len(r["held"])))
    except Exception:                                          # noqa: BLE001
        return ""


def _s452_may_advice(con, u):
    """The bank's NEFT advice file carries full account numbers: the owner (the medical checker) and supplier_msg.senders only."""
    if _is_doctor(u):
        return True
    who = str((u or {}).get("user") or "").strip().lower()
    names = {w.strip().lower() for w in _s446_setting(con, "supplier_msg.senders", "manoj,shavez").split(",") if w.strip()}
    return bool(who) and who in names
# ---- S452_AMIR_PANEL_FIXES end ----------------------------------------------------------------------------------------------------------
