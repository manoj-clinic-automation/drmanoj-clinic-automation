

# ---- S973 (27-Nov-2026, Sanjeevni session 540, kit S973_VOUCHER_SCANS; kit C of S534_FINAL_BUILD_PLAN, D1091 plan 2.4) --------------------
#  'Pehle bana chuka hoon' no longer goes straight to the owner: the claim waits in state 'print' with ONE print card on Amir's page
#  (voucher_scan.py: 'Print diya -- reception ko' . 'Khud scan karein'). The voucher's scan then settles it -- the item at the asked quantity
#  -> closed 'scan B-xxxx'; the voucher he named lacks the item -> back to Amir (the next round, as the owner's 'Back to Amir'); the item at
#  another quantity, or no scan within stock.inq_question_days days -> the owner's call ('yours', as before). Marg's newer report holding it
#  closes the claim and withdraws the card, as for every claim. The cut names' print asks run with every sync. Switch: stock.voucher_scan.
KIT_S973 = "S973_VOUCHER_SCANS"
SCAN_KEY = "stock.voucher_scan"
SCANFROM_KEY = "stock.scan_ask_from"
SETTINGS = SETTINGS + (dict(k=SCAN_KEY, label="'Pehle bana chuka hoon' and cut names: the voucher's print and scan asked", kind="onoff", default="on"),
                       dict(k=SCANFROM_KEY, label="Cut names: a voucher's print is asked for vouchers dated from", kind="date", default=""))
_sync_claims_before_s973 = _sync_claims
_sync_before_s973 = sync
_claims_view_before_s973 = claims_view


def _VS():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import voucher_scan                                       # noqa: PLC0415 -- beside this file
    return voucher_scan


def _s973_close_claim(con, cid, how, key=None):
    ts = now()
    if con.execute("UPDATE stock_voucher_claim SET state='closed', closed_at=?, closed_how=?, closed_by='system' WHERE id=? AND state='print'",
                   (ts, how[:120], cid)).rowcount:
        if key:
            _withdraw_job(con, key)
        return True
    return False


def _sync_claims(con, J, RR, out, pushes):                   # noqa: F811 -- S973: 'already' -> the print card; the scan settles
    _sync_claims_before_s973(con, J, RR, out, pushes)
    try:
        VS = _VS()
    except Exception as ex:                                   # noqa: BLE001
        print("voucher_inquiry S973: no voucher_scan: %s" % str(ex)[:200], file=sys.stderr)
        return
    VJ = _VJ()
    by_ref = {a["id"]: a for a in J["asks"] if a["src"] in ("count", "job") and not a.get("superseded")}
    VS.ensure(con)
    con.commit()
    # 1 · 'Pehle bana chuka hoon' (kit B put it on his call): the print card instead -- once per claim round
    since = setting(con, SCANFROM_KEY, "")
    if VS.on(con) and since:                                  # review S7: only an answer given on or after the install day -- nothing old
        for cid, ref, kind, item, units, pack, typed in con.execute("SELECT id, ask_ref, kind, item, units, pack, typed FROM stock_voucher_claim "
                                                                    "WHERE state='yours' AND answer='already' AND substr(COALESCE(answered_at,''),1,10)>=? "
                                                                    "ORDER BY id", (since,)).fetchall():
            if VS.ask_of(con, "claim", cid) is not None:
                continue                                      # its print ask came and went: his call stands
            a = by_ref.get(ref)
            if a is None:
                continue
            if not con.execute("UPDATE stock_voucher_claim SET state='print' WHERE id=? AND state='yours'", (cid,)).rowcount:
                con.rollback()
                continue
            sid = VS.open_ask(con, "claim", cid, kind, VS.vno(typed, kind), a.get("day"), item, units, pack)
            if sid is None:
                con.rollback()
                continue
            _audit(con, "s973_print_card", dict(claim=cid, ask=sid, item=item), "system")
            con.commit()
            pushes.append(("Voucher ka print chahiye", "%s — print reception ko dijiye ya khud scan kariye" % item, "/finance/amir", "s973"))
    # 2 · the claims waiting for the print and scan
    S = None
    for cid, ref, rnd, key, kind, item, units, pack in con.execute("SELECT id, ask_ref, round, job_key, kind, item, units, pack FROM stock_voucher_claim "
                                                                   "WHERE state='print' ORDER BY id").fetchall():
        sa = VS.ask_of(con, "claim", cid)
        a = by_ref.get(ref)
        if a is None or a["state"] not in ("not_in_marg", "beyond"):
            how = "in Marg" if (a and a["state"] in ("in_marg", "part", "wrong_batch")) else "no longer asked"
            if _s973_close_claim(con, cid, how, key):
                if sa:
                    VS.close_ask(con, sa["id"], "the claim closed: " + how)
                out["closed"] += 1
            con.commit()
            continue
        V = VJ.whole_item(VJ.record_for(RR, _forms_of(VJ, a)), a["item"])
        if V["v"] in ("settled", "held"):
            how = "Marg agrees with the shelf today -- nothing to key" if V["v"] == "settled" else V["word"][:80]
            if _s973_close_claim(con, cid, how, key):
                if sa:
                    VS.close_ask(con, sa["id"], "the claim closed: " + how)
                out["closed"] += 1
            con.commit()
            continue
        if sa is None or sa["state"] not in VS.OPEN:
            con.execute("UPDATE stock_voucher_claim SET state='yours' WHERE id=? AND state='print'", (cid,))   # no open print ask: his call
            con.commit()
            continue
        if S is None:
            S = VS.scans() or []
        res = VS.claim_scan(con, sa, _forms_of(VJ, a), int(units or 0), int(pack or 1), S)
        if res and res[0] == "hit":
            if _s973_close_claim(con, cid, "scan %s" % res[1]["stamp"], key):
                VS.close_ask(con, sa["id"], "scan %s holds it" % res[1]["stamp"], res[1]["id"], res[1]["stamp"])
                _audit(con, "s973_settled", dict(claim=cid, scan=res[1]["stamp"], item=item), "system")
                out["closed"] += 1
            con.commit()
        elif res and res[0] == "miss":
            again = con.execute("SELECT 1 FROM stock_voucher_claim WHERE ask_ref=? AND id<>? AND closed_how LIKE 'scan % lacks it%'", (ref, cid)).fetchone()
            if again:                                         # review M2: the same voucher lacked it once already -- his call, never a loop on Amir
                if con.execute("UPDATE stock_voucher_claim SET state='yours', note=? WHERE id=? AND state='print'",
                               (("scan %s lacks it again" % res[1]["stamp"])[:200], cid)).rowcount:
                    VS.close_ask(con, sa["id"], "scan %s lacks the item again" % res[1]["stamp"], res[1]["id"], res[1]["stamp"])
            elif _s973_close_claim(con, cid, "scan %s lacks it -- back to Amir" % res[1]["stamp"], key):
                VS.close_ask(con, sa["id"], "scan %s lacks the item" % res[1]["stamp"], res[1]["id"], res[1]["stamp"])
                con.commit()
                _new_claim(con, a, int(rnd) + 1, out, pushes)
            con.commit()
        elif res and res[0] == "qty":
            if con.execute("UPDATE stock_voucher_claim SET state='yours', note=? WHERE id=? AND state='print'",
                           (("scan %s: %s" % (res[1]["stamp"], res[2]))[:200], cid)).rowcount:
                VS.close_ask(con, sa["id"], "scan %s holds another quantity (%s)" % (res[1]["stamp"], res[2]), res[1]["id"], res[1]["stamp"])
            con.commit()
        elif VS.timed_out(con, sa):
            if con.execute("UPDATE stock_voucher_claim SET state='yours' WHERE id=? AND state='print'", (cid,)).rowcount:
                VS.close_ask(con, sa["id"], "no scan in %d days" % VS.qdays(con))
            con.commit()


def sync(con, day=None, push=True):                          # noqa: F811 -- S973: + the cut names' print asks
    out = _sync_before_s973(con, day, push)
    try:
        VS = _VS()
        if VS.on(con) and not con.in_transaction:
            ps = []
            c = VS.cut_asks(con, ps)
            if isinstance(out, dict):
                out["s973"] = c
            if push and ps:
                _push(con, ps[0][0] if len(ps) == 1 else "Voucher ke %d print chahiye" % len(ps), "; ".join(p[1] for p in ps[:3]), "/finance/amir", "s973")
                con.commit()
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("voucher_inquiry S973: cut asks stopped: %s" % str(ex)[:200], file=sys.stderr)
    return out


def claims_view(con):                                         # noqa: F811 -- S973: + the claims waiting for the print and scan; his call's words
    out = []
    try:
        VS = _VS()
    except Exception:                                         # noqa: BLE001
        VS = None
    for c in _claims_view_before_s973(con):
        if c["state"] == "yours":
            r = con.execute("SELECT answer, note FROM stock_voucher_claim WHERE id=?", (c["id"],)).fetchone()
            sa = VS.ask_of(con, "claim", c["id"]) if VS else None
            if r and r[0] == "already":
                if sa and "lacks the item again" in str(sa.get("closed_how") or ""):
                    c["path"][-1] = ["bad", "Amir said he had made it; the voucher he named was scanned twice (%s) and does not hold it. Your call: Back to Amir, or Close."
                                     % (sa.get("stamp") or "")]
                elif sa and sa.get("closed_how", "") and "another quantity" in str(sa.get("closed_how")):
                    c["path"][-1] = ["bad", "Amir said he had made it; the voucher's scan %s holds it at another quantity (%s). Your call: Back to Amir, or Close."
                                     % (sa.get("stamp") or "", (r[1] or "").split(": ", 1)[-1])]
                elif sa:
                    c["path"][-1] = ["bad", "Amir said he had made it; the voucher's print was asked %s and no scan came (%s). Your call: Back to Amir, or Close."
                                     % (dm(sa["made_at"]), sa.get("closed_how") or "")]
                else:
                    c["path"][-1] = ["bad", "Amir said he had made it -- Marg's report does not show it. Your call: Back to Amir, or Close."]
        out.append(c)
    if not _has(con, "stock_voucher_claim"):
        return out
    for cid, item, ask, src, dd, typed, made, aat, rnd, aref in con.execute(
            "SELECT id, item, ask_text, src, done_day, typed, made_at, answered_at, round, ask_ref FROM stock_voucher_claim WHERE state='print' ORDER BY id").fetchall():
        sa = VS.ask_of(con, "claim", cid) if VS else None
        path = [["ok", "Asked: %s (%s); Amir tapped done %s%s." % (ask, src, dm(dd), (" and noted %s" % typed) if typed else "")],
                ["ok", "Marg's newer Stock %s report does not hold it -- back on Amir's card by itself %s%s." % (
                    "Issue" if "Issue" in ask else "Receive", dm(made), (" (round %d)" % rnd) if rnd > 1 else "")],
                ["ok", "Amir %s: already made it -- the voucher's print asked on his card." % dm(aat)]]
        if sa and sa["state"] == "printed":
            path.append(["now", "Amir handed the print to reception %s -- waiting for its scan (reception's Aaj ka bill kaam)." % dm(sa["printed_at"])])
        else:
            path.append(["now", "On Amir's card: 'Print diya -- reception ko' or 'Khud scan karein'."])
        out.append(dict(id=cid, ask_ref=aref, item=item, fig=ask, state="print", path=path, acts=[],
                        tags=[["amb", "print + scan asked" if not (sa and sa["state"] == "printed") else "with reception -- scan awaited"]]))
    return out
# ---- S973 end ---------------------------------------------------------------------------------------------------------------------------
