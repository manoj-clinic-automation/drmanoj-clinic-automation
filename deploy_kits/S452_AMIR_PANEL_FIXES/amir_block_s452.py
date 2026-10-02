# ==========================================================================
# S452_AMIR_PANEL_FIXES (02-Oct-2026, F-686 F-687) -- what the live walk of Amir's panel found, and the owner's rulings of that evening.
#
#   * Step 2: only the bills that are NOT in Marg (purchase_app.scans_for_amir); one grey line for the scans held for reception.
#   * Step 7 in Roman Hindi: what keeps the day open as a list, and apart from it -- "(din band karne se nahi rukta)" -- the count's
#     stage line and the salt list. The owner's views (/finance/amir/day, the visit summary) keep _left()'s English.
#   * The card: "N item ka rate Marg mein daalna hai -- kholiye" while due (stock_app.amir_rate_due); the month's pack offers the paid
#     NEFT sheet only once that NEFT is confirmed, as a PDF (supplier_msg.s452_neft_confirmed); "Dawa voucher: aaj ke N (baaki M)" counts
#     what is open on his board. Step 6 carries its heading once.
# ==========================================================================

S452_KIT = "S452_AMIR_PANEL_FIXES"


def _s452_state(cx):
    out = dict(bills=[], held=[], rates=[], neft_ok={})
    try:
        import purchase_app                                    # noqa: PLC0415
        r = purchase_app.scans_for_amir(cx)
        out.update(bills=r.get("list") or [], held=r.get("held") or [])
    except Exception:                                          # noqa: BLE001
        pass
    try:
        import stock_app                                       # noqa: PLC0415
        out["rates"] = stock_app.amir_rate_due(cx)
    except Exception:                                          # noqa: BLE001
        pass
    try:
        import supplier_msg                                    # noqa: PLC0415
        out["neft_ok"] = {m: bool(supplier_msg.s452_neft_confirmed(cx, m)) for m in _s446_prev_months(3)}
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _s452_bills_list(w):
    """Step 2: the scanned medicine bills Marg does not have yet -- each a download, today's as one zip -- and the held ones counted."""
    s = w.get("s446") or {}
    bills, held = s.get("bills") or [], s.get("held") or []
    if not bills and not held:
        return ""
    today = [b for b in bills if b.get("today")]
    rows = []
    for b in bills:
        bd = ("bill %s" % _ddmmyyyy(b["bill_date"])) if b.get("bill_date") else "bill ki tareekh scan par saaf nahi"
        rows.append("<div class=line><span class=big>%s</span> <span class=sub>%s &middot; scan: %s, %s &middot; %s</span><br>"
                    "<a class='btn plain' href='/finance/purchase/api/scan-file/%d'>Download</a></div>"
                    % (_esc(b.get("stamp")), _esc(b.get("supplier")), _esc(b.get("scan_ddmm")), _esc(b.get("who") or "?"), _esc(bd), int(b["id"])))
    zipl = ("<p><a class=btn href='/finance/purchase/api/scan-files/today.zip'>Aaj ke sab (%d) &mdash; ek zip</a></p>" % len(today)) if today else ""
    grey = ("<p class=sub id=s452held style='color:#777'>%d scan abhi reception ki jaanch mein hain &mdash; Marg mein mat daaliye</p>" % len(held)) if held else ""
    return ("<div class=card id=s446bills><h2>Marg mein daalne ke bill (%d)</h2>"
            "<p class=sub>Sirf woh scan jinka bill Marg mein abhi nahi hai. Marg ki digital entry mein upload kijiye &mdash; Marg ki entry hi "
            "bill ki asli entry hai. Marg ki export aate hi bill yahan se khud hat jayega.</p>%s%s%s</div>"
            % (len(bills), zipl, "".join(rows), grey))


def _s452_extra_hi(w):
    """The lines that never hold the day: the count's stage, the salt list -- Roman Hindi."""
    s = w.get("s446") or {}
    st = s.get("stage") or {}
    out = []
    if st:
        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
        cid = int(st.get("count_id") or 0)
        if st.get("stage") == "A":
            if A.get("open"):
                out.append("Ginti #%d: %d orthotic voucher Marg mein daalne baaki" % (cid, int(A["open"])))
            else:
                out.append("Ginti #%d: orthotic voucher ki jaanch ke liye closing stock export baaki" % cid)
        elif st.get("stage") == "B":
            out.append("Ginti #%d: naam badalna baaki — %d mein se %d naam Marg mein dikhe" % (cid, int(B.get("total") or 0), int(B.get("verified") or 0)))
        elif st.get("stage") == "C":
            if C.get("open"):
                out.append("Ginti #%d: %d dawa voucher Marg mein daalne baaki" % (cid, int(C["open"])))
            elif C.get("waiting_export"):
                out.append("Ginti #%d: dawa voucher ki jaanch ke liye closing stock export baaki" % cid)
            elif C.get("wrong"):
                out.append("Ginti #%d: dawa voucher ke kuch item Marg mein abhi sahi nahi" % cid)
    if ((w.get("s444") or {}).get("salt") or {}).get("pending"):
        out.append("SALT WISE ITEM LIST abhi nahi aayi (Excel)")
    return out


def _s452_left_hi(w):
    """Step 7 (Amir's own page) in Roman Hindi -> (what keeps the day open, what never does). The owner's English stays in _left()."""
    gate = []
    if not w["done"].get(2):
        gate.append("Bill daalne ki pushti baaki hai")
    waiting = [e["label"] for e in w["exports"] if e.get("state") == "wait"]
    missing = [e["label"] for e in w["exports"] if not e["have"] and e.get("state") != "wait"]
    if waiting:
        gate.append("Dono purchase report abhi aa rahi hain" if len(waiting) > 1 else "%s abhi aa rahi hai" % waiting[0])
    if missing:
        gate.append("Dono purchase report ki jaanch baaki hai" if len(missing) > 1 else "%s ki jaanch baaki hai" % missing[0])
    n = len(w["today_bills"]) + len(w["carry_bills"])
    if n:
        gate.append("%d bill par tap baaki hai" % n)
    if not w["done"].get(6):
        gate.append("Salt aur naam ki list tick nahi hui")
    return gate, _s452_extra_hi(w)
# ---- S452_AMIR_PANEL_FIXES end --------------------------------------------------------------------------------------------------------
