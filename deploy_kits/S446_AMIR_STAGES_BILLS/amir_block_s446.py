

# ==========================================================================
# S446_AMIR_STAGES_BILLS (02-Oct-2026, D649 / D650 · F-673 F-679 F-680) -- what S444 did not carry.
#
#   * The count in the decided order (stock_app.amir_stage): A the orthotic vouchers -> verified on Marg's next closing stock ->
#     B the orthotic renames -> verified on Marg's next export -> C the medicine vouchers, 5 a visit. Nothing of a later stage
#     reaches him before the earlier one is verified; never a gate on Din band.
#   * His monthly packs chosen by STATE: every month of the last three whose pack is ready and not yet "dekh liya", oldest first,
#     inside the same card (the foot card that showed only the previous calendar month is gone). packs.py is read only.
#   * Step 2 lists the scanned medicine bills still to go into Marg (purchase_app.scans_to_enter), each a download, plus one zip.
#   * The doors the duty map found missing: the Sunday for the full count, bills for goods tapped as arrived, the traces' fixes.
# ==========================================================================

S446_KIT = "S446_AMIR_STAGES_BILLS"
S446_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def _s446_month_name(m):
    try:
        return "%s %s" % (S446_MONTHS[int(m[5:7]) - 1], m[:4])
    except (TypeError, ValueError, IndexError):
        return str(m)


def _s446_prev_months(n=3):
    t = _now()
    y, mo = t.year, t.month
    out = []
    for _i in range(n):
        mo -= 1
        if mo == 0:
            y, mo = y - 1, 12
        out.append("%04d-%02d" % (y, mo))
    return list(reversed(out))                                 # oldest first


def _s446_packs(cx):
    out = []
    try:
        import packs                                           # noqa: PLC0415 -- READ ONLY: amir_pack(con, month)
        for m in _s446_prev_months(3):
            p = packs.amir_pack(cx, m)
            if p.get("ready") and not p.get("seen"):
                out.append(m)
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _s446_watch(cx):
    try:
        import stock_watch                                     # noqa: PLC0415
        v = stock_watch.amir_view(cx)
        if not v.get("ok"):
            return {}
        p = v.get("plan") or {}
        return dict(sunday=(p.get("status") == "open"), bill_pending=len(v.get("bill_pending") or []), fixes=len(v.get("fixes") or []))
    except Exception:                                          # noqa: BLE001
        return {}


def _s446_state(cx, day):
    st = None
    try:
        import stock_app                                       # noqa: PLC0415
        st = stock_app.amir_stage(cx)
    except Exception:                                          # noqa: BLE001
        st = None
    bills = []
    try:
        import purchase_app                                    # noqa: PLC0415
        bills = purchase_app.scans_to_enter(cx)
    except Exception:                                          # noqa: BLE001
        bills = []
    return dict(stage=st, packs=_s446_packs(cx), watch=_s446_watch(cx), bills=bills)


def _s446_board(st, anchor):
    return "/finance/stock/page/amir?count=%d#%s" % (int((st or {}).get("count_id") or 0), anchor)


def _s446_wrong_lines(rows, numbers):
    out = []
    for r in rows[:12]:
        vn = ", ".join("voucher %d" % numbers[k] for k in r.get("keys") or [] if k in numbers)
        if r.get("marg") is None:
            fig = "Marg ki export mein nahi mila"
        else:
            fig = "Marg mein %s, hona chahiye %s" % (r["marg"], r["should"] if r.get("should") is not None else "?")
        out.append("<div class=line><span class='big bad'>%s</span><br><span class=sub>%s%s</span></div>"
                   % (_esc(r["item"]), _esc(fig), (" &middot; %s theek kijiye" % _esc(vn)) if vn else ""))
    return "".join(out)


def _s446_card(w, top=False):
    """Amir's one card: the count's stage, the doors, the packs. Each line only while due."""
    s = w.get("s446") or {}
    st = s.get("stage")
    lines = []
    if st:
        stage = st.get("stage")
        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
        if stage == "A":
            pr = A.get("proof") or {}
            if A.get("open"):
                lines.append("<div class=line><a class=btn href='%s'>Orthotic voucher baaki: %d &mdash; kholiye</a></div>"
                             % (_esc(_s446_board(st, "vouchers")), int(A["open"])))
            elif pr.get("state") == "wrong":
                lines.append("<div class=line><span class='big bad'>Orthotic: Marg mein yeh abhi sahi nahi hain</span></div>"
                             + _s446_wrong_lines(pr.get("rows") or [], st.get("numbers") or {})
                             + "<div class=line><a class='btn plain' href='%s'>Voucher kholiye</a>"
                               "<span class=sub>Theek karke phir closing stock export kijiye.</span></div>" % _esc(_s446_board(st, "vouchers")))
            else:
                lines.append("<div class=line><span class='big'>Orthotic ke %d voucher Marg mein daal diye &#10003;</span><br>"
                             "<span class='big bad'>Ab closing stock export kijiye</span><br>"
                             "<span class=sub>Server khud milayega ki Marg ab shelf ke barabar hai.</span></div>" % int(A.get("total") or 0))
        elif stage == "B":
            lines.append("<div class=line><span class='big good'>Orthotic: sab sahi &#10003;</span></div>")
            if B.get("open"):
                lines.append("<div class=line><a class=btn href='%s'>Naam badlo: %d naam &mdash; kholiye</a></div>"
                             % (_esc(_s446_board(st, "renames")), len(B["open"])))
            if B.get("old"):
                lines.append("<div class=line><span class='big bad'>Marg mein abhi purana naam: %s</span></div>" % _esc(", ".join(B["old"][:8])))
            if not B.get("open") and not B.get("old"):
                lines.append("<div class=line><span class=big>Naam badal diye &#10003; &mdash; ab closing stock ya item list export kijiye</span></div>")
        elif stage == "C":
            if (B.get("verified_at") or "")[:10] == _today():
                lines.append("<div class=line><span class='big good'>Orthotic poora &#10003;</span></div>")
            if C.get("today"):
                lines.append("<div class=line><a class=btn href='%s'>Dawa voucher: aaj ke %d (baaki %d) &mdash; kholiye</a></div>"
                             % (_esc(_s446_board(st, "vouchers")), len(C["today"]), int(C.get("unreleased") or 0)))
            elif C.get("waiting_export"):
                lines.append("<div class=line><span class=big>Dawa ke voucher Marg mein daal diye &#10003;</span><br>"
                             "<span class='big bad'>Ab closing stock export kijiye</span></div>")
            if C.get("wrong"):
                lines.append("<div class=line><span class='big bad'>Dawa: Marg mein yeh abhi sahi nahi hain</span></div>"
                             + _s446_wrong_lines(C["wrong"], st.get("numbers") or {}))
    wt = s.get("watch") or {}
    if wt.get("sunday"):
        lines.append("<div class=line><a class='btn plain' href='%s'>Poori ginti ka Sunday chuniye &mdash; kholiye</a></div>" % _esc(_s446_board(st, "rest")))
    if wt.get("bill_pending"):
        lines.append("<div class=line><a class='btn plain' href='%s'>Maal aa gaya, Marg mein bill baaki: %d &mdash; kholiye</a></div>"
                     % (_esc(_s446_board(st, "rest")), int(wt["bill_pending"])))
    if wt.get("fixes"):
        lines.append("<div class=line><a class='btn plain' href='%s'>Stock trace ke sudhar: %d &mdash; kholiye</a></div>"
                     % (_esc(_s446_board(st, "rest")), int(wt["fixes"])))
    for m in s.get("packs") or []:
        lines.append("<div class=line><span class=big>Mahine ka pack &mdash; %s</span>"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/neft'>Paid NEFT sheet (Excel)</a></p>"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/yes'>Yes Bank Sanjeevni statement (PDF)</a></p>"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/icici'>ICICI Sanjeevni statement (PDF)</a></p>"
                     "<form method=post action='/finance/amir/pack/%s/seen'><button class=btn name=go value=1>Dekh liya</button></form></div>"
                     % (_esc(_s446_month_name(m)), m, m, m, m))
    if not lines:
        return ""
    return ("<div class=card id=s444duty style='border:2px solid var(--bad)'><h2 class=bad>%s</h2>%s</div>"
            % ("Marg sudhar &mdash; abhi baaki" if top else "Marg sudhar", "".join(lines)))


def _s446_left(w):
    s = w.get("s446") or {}
    st = s.get("stage") or {}
    out = []
    if st:
        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
        if st.get("stage") == "A":
            if A.get("open"):
                out.append("count #%d stage A: %d orthotic vouchers not entered in Marg" % (st["count_id"], A["open"]))
            else:
                out.append("count #%d stage A: waiting for the closing-stock export that proves the orthotic vouchers" % st["count_id"])
        elif st.get("stage") == "B":
            out.append("count #%d stage B: %d of %d orthotic renames seen in Marg" % (st["count_id"], B.get("verified", 0), B.get("total", 0)))
        elif st.get("stage") == "C" and (C.get("today") or C.get("waiting_export") or C.get("wrong")):
            out.append("count #%d stage C: %d medicine vouchers of this lot not entered" % (st["count_id"], len(C.get("today") or [])))
    if (w.get("s444") or {}).get("salt", {}).get("pending"):
        out.append("SALT WISE ITEM LIST not received (Excel)")
    return out


def _s446_summary_rows(w):
    c = _s446_card(w)
    return ["<div class=line>Marg sudhar abhi baaki hai &mdash; upar wala card dekhiye <span class=sub>(din band karne se nahi rukta)</span></div>"] if c else []


def _s446_bills_list(w):
    """Step 2: the scanned medicine bills still to go into Marg -- download each, or today's as one zip."""
    bills = (w.get("s446") or {}).get("bills") or []
    if not bills:
        return ""
    today = [b for b in bills if b.get("today")]
    rows = "".join("<div class=line><span class=big>%s</span> <span class=sub>%s &middot; %s</span><br>"
                   "<a class='btn plain' href='/finance/purchase/api/scan-file/%d'>Download</a></div>"
                   % (_esc(b.get("stamp") or ""), _esc(b.get("vendor") or "supplier padha nahi"), _esc(_ddmmyyyy(b.get("bill_date") or "") or "-"), int(b["id"]))
                   for b in bills)
    return ("<div class=card id=s446bills><h2>Marg mein daalne ke bill (%d)</h2>"
            "<p class=sub>Scan kiye hue bill. Marg ki digital entry mein upload kijiye &mdash; Marg ki entry hi bill ki asli entry hai. "
            "Marg ki export aate hi bill yahan se khud hat jayega.</p>%s%s</div>"
            % (len(bills), ("<p><a class=btn href='/finance/purchase/api/scan-files/today.zip'>Aaj ke sab (%d) &mdash; ek zip</a></p>" % len(today)) if today else "", rows))


def _s446_voucher_line(cx, st):
    """S444's line (d), named by stage: the lot he has not touched for N of his visits."""
    out = []
    try:
        if not st or st.get("stage") not in ("A", "C"):
            return out
        import stock_app                                       # noqa: PLC0415
        oc = {c["count_id"]: c for c in stock_app.amir_vouchers_open(cx)}.get(st["count_id"]) or {}
        A, C = st.get("A") or {}, st.get("C") or {}
        n = A.get("open") if st["stage"] == "A" else len(C.get("today") or [])
        if not n:
            return out
        since = max([x for x in ((C.get("lot_at") if st["stage"] == "C" else oc.get("made_first")), oc.get("last_touch")) if x] or [""])
        since = _norm_ts(since) or ""
        visits = [r[0] for r in cx.execute("SELECT day FROM amir_day WHERE opened_at IS NOT NULL AND opened_at > ? ORDER BY day", (since,)).fetchall()]
        if len(visits) >= _s444_setting(cx, "amir.voucher_visits"):
            what = "Stage A, orthotic" if st["stage"] == "A" else "Stage C, medicine lot"
            out.append(dict(cls="warn", target="checks-marg",
                            text="Count vouchers waiting (%s): %d -- Amir has not opened them in %d visits (%s), count #%d"
                                 % (what, n, len(visits), ", ".join(_s444_ddmm(v) for v in visits[-3:]), st["count_id"])))
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _s446_owner_lines(con):
    """The owner's lines from this kit: where the count stands (one small line), the orthotics verified once, the Sarvam trial."""
    out = []
    try:
        import stock_app                                       # noqa: PLC0415
        st = stock_app.amir_stage(con)
    except Exception:                                          # noqa: BLE001
        st = None
    if st:
        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
        if st["stage"] == "A":
            pr = (A.get("proof") or {}).get("state")
            t = ("Stage A (orthotic vouchers) %d/%d entered" % (A.get("entered", 0), A.get("total", 0)) if A.get("open") else
                 "Stage A: all %d orthotic vouchers entered -- %s" % (A.get("total", 0), "%d item(s) still wrong in Marg" % len((A.get("proof") or {}).get("rows") or []) if pr == "wrong" else "waiting for the closing-stock export"))
        elif st["stage"] == "B":
            t = "Stage B (orthotic renames) %d/%d seen in Marg" % (B.get("verified", 0), B.get("total", 0))
        elif st["stage"] == "C":
            t = "Stage C (medicine vouchers) %d/%d entered, %d released and open" % (C.get("entered", 0), C.get("total", 0), C.get("open", 0))
        else:
            t = "all vouchers entered and verified"
        out.append(dict(cls="info", target="stock", text="Count #%d: %s" % (st["count_id"], t)))
        bat = B.get("verified_at")
        if bat and _s444_days_since(bat) is not None and _s444_days_since(bat) <= 2:
            out.append(dict(cls="warn", target="stock", text="Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)" % (st["count_id"], _s444_ddmm(bat))))
        out.extend(_s446_voucher_line(con, st))
    try:
        import purchase_app                                    # noqa: PLC0415
        out.extend(purchase_app.sarvam_lines(con))
    except Exception:                                          # noqa: BLE001
        pass
    return out
# ---- S446_AMIR_STAGES_BILLS end --------------------------------------------------------------------------------------------------------
