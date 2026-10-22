# S628 anchored edits for /root/finance/porders_s454.py (FROM 53ef850f)
EDITS = []

# ---- words
EDITS.append(('''          "open_scan": ("Scan dekhiye", "Open the scan")})''', '''          "open_scan": ("Scan dekhiye", "Open the scan")})
# ---- S628 (D761, 22-Oct-2026, kit S628_ONE_NAME_LIST): the words of the order list's corrections (F-993, F-995) -----------------------------
T.update({"none_came": ("maal aaya — is order ki koi dawa nahi aayi", "arrived — nothing on it came"),
          "send_back": ("Dobara scan ke liye bhejiye:", "Send back for rescan:"), "sent_back": ("dobara scan ke liye bheja ✓", "sent back for rescan ✓"),
          "withdraw": ("Wapas lijiye", "Withdraw"), "fix_dealer": ("Dealer badliye: %s", "Change dealer to %s"),
          "fix_none": ("Kaagaz ka dealer pakka nahi padha gaya — scan kholkar dekhiye.", "The paper's dealer is not read for sure — open the scan."),
          "s_same": ("Ek hi kaagaz ke do scan", "The same paper scanned twice"), "s_names": ("Naam milaiye", "Names to confirm"),
          "q_yes": ("Haan", "Yes"), "q_no": ("Nahi", "No"),
          "every_scan": ("Har pharmacy scan · pichhle 14 din", "Every pharmacy scan · last 14 days"),
          "sent_by_you": ("aapne bheja", "sent back by you"), "sent_by_x": ("%s ne bheja", "sent back by %s"),
          "part_sub": ("Order %s · %s · %d mein se %d dawa aayi · %s baaki", "Ordered %s · %s · of %d medicines %d came · %s awaited")})'''))

# ---- the order card: came X of Y (owner), nothing came, Send back on every scan it names
EDITS.append(('''def _s619_order_card(con, en, s, show_lines=True, marg=None):
    OT = _s619_ot()''', '''def _s619_order_card(con, en, s, show_lines=True, marg=None, asked=None):
    OT = _s619_ot()'''))

EDITS.append(('''    if s["part"] or (s["arrived"] and s["came"] and s["came"] < s["n"]):
        sub.append(L(en, "of_came", s["n"], s["came"]))''', '''    if s["part"] or (s["arrived"] and s["came"] and s["came"] < s["n"]):
        sub.append(L(en, "of_came", *((s["came"], s["n"]) if en else (s["n"], s["came"]))))   # S628 (F-995): "came 1 of 2" -- never "2 of 1"
    if s["arrived"] and s["n"] and not s["came"] and s["short"] == s["n"]:
        sub.append(L(en, "none_came"))                        # S628 (F-995): an arrival with none of its lines'''))

EDITS.append(('''    notes = "".join('<div class="sb am s619note">%s</div>' % esc(n) for n in s.get("notes") or [])
    return ('<div class="card s619o" data-order="%d" data-key="%s"><div style="display:flex;gap:10px;align-items:flex-start"><div style="flex:1 1 auto">'
            '<div class="nm">%s · %s</div><div class="sb">%s</div>%s<div class="sb">%s</div>%s%s</div>%s</div></div>'
            % (s["id"], s["key"], esc(s["vendor"]), esc(when), esc(" · ".join(sub)), _s619_dots(en, s), esc(" · ".join(times)), notes, "".join(li), thumb))''',
              '''    notes = "".join('<div class="sb am s619note">%s</div>' % esc(n) for n in s.get("notes") or [])
    sb = _s628_send_back(en, s, asked) if asked is not None else ""
    return ('<div class="card s619o" data-order="%d" data-key="%s"><div style="display:flex;gap:10px;align-items:flex-start"><div style="flex:1 1 auto">'
            '<div class="nm">%s · %s</div><div class="sb">%s</div>%s<div class="sb">%s</div>%s%s%s</div>%s</div></div>'
            % (s["id"], s["key"], esc(s["vendor"]), esc(when), esc(" · ".join(sub)), _s619_dots(en, s), esc(" · ".join(times)), notes, "".join(li), sb, thumb))


def _s628_chips(en, sid):
    sq = _sq()
    chips = sq.CHIPS if sq else ("blurred", "cut", "not_bill")
    words = sq.CHIP_WORDS if sq else {"blurred": ("blurred", "dhundli"), "cut": ("cut off", "kata hua"), "not_bill": ("not a bill", "bill nahi")}
    return "".join('<button data-reason="%s" data-scan="%d" onclick="s454(\\'%s/api/s454/rescan\\',{asset_bill_id:%d,reason:\\'%s\\'})">%s</button>'
                   % (c, sid, P, sid, c, esc(words[c][0 if en else 1])) for c in chips)


def _s628_send_back(en, s, asked):
    """S628 (F-993): every scan an order card names -- the clearer scan of its paper -- carries Send back (the three chips), or 'sent back ✓'
    with Withdraw when an ask is open. asked = {scan id: ask id} of the open asks."""
    out, seen = [], set()
    for x in s.get("scans") or []:
        sid = int(x.get("head") or x["scan"])
        if sid in seen or x.get("other"):
            continue
        seen.add(sid)
        st = x.get("stamp") if int(x["scan"]) == sid else (x.get("head_stamp") or "#%d" % sid)
        if sid in asked:
            out.append('<div class="sb s628sb" data-sbscan="%d">%s · <span class="am">%s</span> <button onclick="s454(\\'%s/api/s454/rescan/withdraw\\',{id:%d})">%s</button></div>'
                       % (sid, esc(st), L(en, "sent_back"), P, asked[sid], L(en, "withdraw")))
        else:
            out.append('<div class="sb s628sb" data-sbscan="%d">%s · %s <span class="chips">%s</span></div>' % (sid, esc(st), L(en, "send_back"), _s628_chips(en, sid)))
    return "".join(out)'''))

# ---- the track page: the owner's name questions, Withdraw on the asks, the dealer door, the same paper twice, Send back on every card
EDITS.append(('''    tl = OT.tiles(rows, len(redo.get("asks") or []) + len(redo.get("redo") or []))
    marg = OT._marg_items(con)
    h = ['<h1 id="trackh">%s</h1>' % L(en, "track")]''', '''    tl = OT.tiles(rows, len(redo.get("asks") or []) + len(redo.get("redo") or []))
    marg = OT._marg_items(con)
    asked = {int(a["scan"]): int(a["id"]) for a in redo.get("asks") or []}     # S628: the open asks, for Send back / Withdraw on the cards
    h = ['<h1 id="trackh">%s</h1>' % L(en, "track")]
    if kind == "owner":                                       # S628 (D761): the one name list's questions -- the owner's, one line each
        try:
            import med_names                                  # noqa: PLC0415
            qs = med_names.questions(con)
        except Exception:                                     # noqa: BLE001
            qs = []
        if qs:
            h.append('<div class="grp" id="sec_names">%s · %d</div>' % (L(en, "s_names"), len(qs)))
            for q in qs:
                h.append('<div class="card" data-nameq="%d"><div class="nm">%s</div><div class="two">'
                         '<button class="g" onclick="s454(\\'%s/api/s454/name_answer\\',{id:%d,yes:1})">%s</button>'
                         '<button onclick="s454(\\'%s/api/s454/name_answer\\',{id:%d,yes:0})">%s</button></div></div>'
                         % (q["id"], esc(med_names.question_text(q, True)), P, q["id"], L(en, "q_yes"), P, q["id"], L(en, "q_no")))'''))

EDITS.append(('''        for s in lst:
            h.append(_s619_order_card(con, en, s, True, marg))''', '''        for s in lst:
            h.append(_s619_order_card(con, en, s, True, marg, asked))'''))

EDITS.append(('''    for a in redo.get("asks") or []:
        h.append('<div class="card" data-ask="%d" data-scan="%d"><div class="nm">%s · %s</div><div class="sb am">%s</div></div>'
                 % (a["id"], a["scan"], esc(a["stamp"]), esc(a["vendor"]), esc(sq.words(a["reason"], "owner" if en else "shavez") if sq else a["reason"])))''',
              '''    for a in redo.get("asks") or []:
        h.append('<div class="card" data-ask="%d" data-scan="%d"><div class="nm">%s · %s</div><div class="sb am">%s</div>'
                 '<div class="lnk"><button onclick="s454(\\'%s/api/s454/rescan/withdraw\\',{id:%d})">%s</button></div></div>'
                 % (a["id"], a["scan"], esc(a["stamp"]), esc(a["vendor"]), esc(sq.words(a["reason"], "owner" if en else "shavez") if sq else a["reason"]),
                    P, a["id"], L(en, "withdraw")))'''))

EDITS.append(('''    for w in wd:
        h.append('<div class="card" data-wrong="%d"><div class="nm">%s · %s</div><div class="sb">%s</div><a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a></div>'
                 % (w["scan"], esc(w["stamp"]), esc(OS.ddmm(w["date"])), esc(("saved as %s; the paper says %s" if en else "%s ke naam se save; kaagaz par %s") % (w["saved"], w["paper"])),
                    w["scan"], L(en, "open_scan")))''', '''    for w in wd:
        pk = OT.paper_dealer(con, ctx, w["scan"])            # S628: the server's own reading of the paper's dealer -- the one-tap door
        fix = ('<div class="lnk"><button class="g" data-fix="%d" onclick="s454(\\'%s/api/s454/dealer_fix\\',{scan:%d})">%s</button></div>'
               % (w["scan"], P, w["scan"], esc(L(en, "fix_dealer", pk))) if pk else '<div class="sb am">%s</div>' % L(en, "fix_none"))
        h.append('<div class="card" data-wrong="%d"><div class="nm">%s · %s</div><div class="sb">%s</div>%s<a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a></div>'
                 % (w["scan"], esc(w["stamp"]), esc(OS.ddmm(w["date"])), esc(("saved as %s; the paper says %s" if en else "%s ke naam se save; kaagaz par %s") % (w["saved"], w["paper"])),
                    fix, w["scan"], L(en, "open_scan")))
    sp2 = OT.same_paper(con, ctx)                             # S628 (F-992): the same paper scanned twice, neither set aside
    if sp2:
        h.append('<div class="grp" id="sec_same">%s · %d</div>' % (L(en, "s_same"), len(sp2)))
        for p in sp2:
            h.append('<div class="card" data-same="%d-%d"><div class="nm">%s</div><div class="lnk"><a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a> '
                     '<a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a></div><div class="chips">%s</div></div>'
                     % (p["a"], p["b"], esc(OT.W("same_paper", en, p["sa"], p["sb"], p["bill"])), p["a"], esc(p["sa"]), p["b"], esc(p["sb"]),
                        L(en, "send_back") + " " + esc(p["sa"]) + " " + _s628_chips(en, p["a"]) + " · " + esc(p["sb"]) + " " + _s628_chips(en, p["b"])))'''))

EDITS.append(('''             % (L(en, "s_done"), len(done), "".join(_s619_order_card(con, en, s, False, marg) for s in done)))''',
              '''             % (L(en, "s_done"), len(done), "".join(_s619_order_card(con, en, s, False, marg, asked) for s in done)))'''))

# ---- the scans page: English on the owner's page; every pharmacy scan of the last 14 days with Send back
EDITS.append(('''        for a in x["asks"]:
            by = (sq.sent_by("owner" if a["by_owner"] else "", a["asked_by"]) if sq else a["asked_by"])''', '''        for a in x["asks"]:
            if en:                                            # S628 (F-995): the owner's page in English
                by = L(en, "sent_by_you") if a["by_owner"] else L(en, "sent_by_x", str(a["asked_by"] or "").split(" ")[0].title())
            else:
                by = (sq.sent_by("owner" if a["by_owner"] else "", a["asked_by"]) if sq else a["asked_by"])'''))

EDITS.append(('''    if not x["asks"] and not x["redo"]:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "redo_none"))
    return shell(con, u, L(en, "r_redo"), "".join(h), back=P, login=login)''', '''    if not x["asks"] and not x["redo"]:
        h.append('<div class="ok"><div class="t">%s</div></div>' % L(en, "redo_none"))
    taken = {int(a["scan"]) for a in x["asks"]} | {int(r["scan"]) for r in x["redo"]}
    ev = [r for r in _s628_recent(14) if int(r["id"]) not in taken]      # S628 (F-993): any pharmacy scan can be sent back
    if ev:
        h.append('<details class="card" id="sec_every"><summary style="min-height:44px;cursor:pointer;font-weight:700">%s · %d</summary>%s</details>'
                 % (L(en, "every_scan"), len(ev), "".join(
                     '<div class="sb" data-every="%d" style="padding:6px 0;border-top:1px solid #eee">%s · %s · %s <a class="more" href="/scanapp/bills/%d/file" target="_blank">%s</a>'
                     '<div class="chips">%s</div></div>' % (int(r["id"]), esc(r.get("stamp_no") or "#%d" % int(r["id"])), esc(r.get("vendor") or ""),
                                                           esc(OS.ddmm(str(r.get("bill_date") or r.get("created_at") or "")[:10])), int(r["id"]),
                                                           L(en, "redo_open"), _s628_chips(en, int(r["id"]))) for r in ev)))
    return shell(con, u, L(en, "r_redo"), "".join(h), back=P, login=login)


def _s628_recent(days):
    """S628: the pharmacy scans of the last `days` days, not set aside, first pages only (assets.db READ ONLY), newest first."""
    acon = OS._assets()
    if acon is None:
        return []
    try:
        since = (dt.date.today() - dt.timedelta(days=int(days))).isoformat()
        return [dict(r) for r in acon.execute("SELECT id, stamp_no, vendor, bill_date, created_at FROM bills WHERE lane='pharmacy' AND COALESCE(status,'')<>'rejected' "
                                              "AND page_of IS NULL AND substr(created_at,1,10)>=? ORDER BY id DESC", (since,))]
    except sqlite3.Error:
        return []
    finally:
        acon.close()'''))

# ---- the two new doors (POST): the owner's name answer; the dealer fix (the owner and Shavez)
EDITS.append(('''@bp.route(P + "/s454/late")
def r_late():
    return late_page()''', '''@bp.route(P + "/s454/late")
def r_late():
    return late_page()


@bp.route(P + "/api/s454/name_answer", methods=["POST"])
def api_name_answer():
    """S628 (D761): the owner's Yes / No on one name question of the one name list (med_names). The owner only."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only", message="Only the owner answers the name questions."), 403
    b = _body()
    try:
        qid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        qid = 0
    import med_names                                          # noqa: PLC0415
    ok, st = med_names.answer(con, qid, bool(b.get("yes")), who(u))
    if not ok:
        return jsonify(ok=False, error="not_open", message="Already answered."), 409
    OS.audit(con, who(u), "s628_name_answer", qid, dict(state=st, kit="S628"))
    con.commit()
    return jsonify(ok=True, state=st)


@bp.route(P + "/api/s454/dealer_fix", methods=["POST"])
def api_dealer_fix():
    """S628 (F-993, D761): a pharmacy scan saved under the wrong dealer -> the dealer its paper names, read by the SERVER (order_track.paper_dealer,
    never the browser): s454_scan_answer(vendor, chosen) -- which order_sheet._resolver already reads first -- and the scan's tie to an order of
    the other dealer moves to the paper dealer's newest untied order made before the scan within 7 days (else it is only removed). The owner
    and porders.rescan_askers (Shavez) only. The scan app's own record keeps its text (its Edit changes that)."""
    u, con, kind, err = _auth_api()
    if err:
        return err
    login = _s618_login(u)
    if not _s618_asker(con, kind, login):
        return jsonify(ok=False, error="not_asker", message="Only the owner and Shavez correct a scan's dealer."), 403
    try:
        sid = int(_body().get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    OT = _s619_ot()
    ctx = OT.Ctx(con)
    s = ctx.scans.get(sid)
    if not sid or not s or str(s.get("lane") or "") != "pharmacy" or str(s.get("status") or "") == "rejected":
        return jsonify(ok=False, error="no_such_scan"), 404
    if sid not in {w["scan"] for w in OT.wrong_dealer(con, ctx)}:
        return jsonify(ok=False, error="not_wrong", message="This scan is not saved under another dealer."), 409
    pk = OT.paper_dealer(con, ctx, sid)
    if not pk:
        return jsonify(ok=False, error="paper_unread", message="The paper's dealer is not read for sure."), 409
    w = who(u)
    _answer(con, sid, "vendor", "chosen", pk, w)              # commits; audited s454_scan_answer
    try:                                                      # the S440 matcher's own door too (purchase_scan_state.chosen_vendor) -- no alias learnt:
        _po()._s440_put(con, sid, w, chosen_vendor=pk)        # the saved text names the WRONG dealer
        con.commit()
    except Exception:                                         # noqa: BLE001
        pass
    pa = _pa()
    moved = None
    t = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
    if t:
        o = con.execute("SELECT vendor FROM purchase_order WHERE id=?", (t[0],)).fetchone()
        if o and pa.supplier_key(o[0]) != pk:
            con.execute("DELETE FROM order_scan_tie WHERE asset_bill_id=?", (sid,))
            at = s.get("at")
            if at is not None:
                lo = (at - dt.timedelta(days=7)).replace(microsecond=0).isoformat()
                for r in con.execute("SELECT id, vendor FROM purchase_order WHERE status IN ('sent','received') AND created_at<=? AND created_at>=? "
                                     "AND id NOT IN (SELECT order_id FROM order_scan_tie) ORDER BY created_at DESC, id DESC",
                                     (at.replace(microsecond=0).isoformat(), lo)).fetchall():
                    if pa.supplier_key(r[1]) == pk:
                        con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,0)",
                                    (r[0], sid, s.get("stamp_no") or "", at.replace(microsecond=0).isoformat(), OS.now_iso(), "dealer_fix"))
                        moved = r[0]
                        break
            OS.audit(con, w, "s628_tie_moved", sid, dict(from_order=t[0], to_order=moved, kit="S628"))
    OS.audit(con, w, "s628_dealer_fix", sid, dict(stamp=s.get("stamp_no"), saved=s.get("vendor"), paper=pk, kit="S628"))
    con.commit()
    try:
        _pa()._rematch(con, w)                                # the scan links follow at once (as S440's Supplier chuno does)
    except Exception:                                         # noqa: BLE001
        pass
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    return jsonify(ok=True, dealer=pk, tie=moved, linked=bool(lk))'''))

EDITS.append(("""    redo = getattr(ctx, "redo", None) or dict(asks=[], redo=[])
    tl = OT.tiles(rows, len(redo.get("asks") or []) + len(redo.get("redo") or []))""", """    redo = getattr(ctx, "redo", None) or dict(asks=[], redo=[])
    redo = dict(redo, redo=[r for r in redo.get("redo") or [] if ctx.head(r["scan"]) == int(r["scan"])])   # S628 (F-992): a copy whose clearer scan
    tl = OT.tiles(rows, len(redo.get("asks") or []) + len(redo.get("redo") or []))                         # exists is not asked to be redone"""))

EDITS.append(("""    li = []
    if show_lines:
        for x in s["lines"]:""", """    li = []
    if show_lines or any(x.get("how") == "other" or x.get("notes") for x in s["lines"]):   # S628: a complete card still says 'came from Janta'
        for x in (s["lines"] if show_lines else [y for y in s["lines"] if y.get("how") == "other" or y.get("notes")]):"""))
