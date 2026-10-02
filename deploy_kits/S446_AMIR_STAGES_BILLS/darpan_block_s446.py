


# ---- S446_AMIR_STAGES_BILLS (02-Oct-2026, D648): Amir's supplier claims reach Darpan -------------------------------------------------
# amir_claim (amir_day.py) is Darpan's queue -- "he raises a claim; he never chases one; chasing is Darpan's queue" -- yet no page
# Darpan opens read it (S444's duty map, finding 1). Kal ka hisaab now lists every open claim: supplier, bill, amount, raised when,
# with two taps and nothing to type: "Supplier se baat ho gayi" (state contacted) and "Credit / maal mil gaya" (settled).
S446_CLAIM_REASON_HI = {"short": "Kam maal aaya", "nodeal": "Deal nahi mili", "discount": "Discount kam", "other": "Aur koi baat"}
S446_CLAIM_ANSWERS = ("baat_hui", "mil_gaya")


def _s446_claims(con):
    try:
        if not _has(con, "amir_claim"):
            return []
        out = []
        for r in con.execute("SELECT id, supplier, bill_no, bill_date, amount_p, reason, raised_by, raised_at, state, contacted_note "
                             "FROM amir_claim WHERE state <> 'settled' ORDER BY raised_at, id").fetchall():
            out.append(dict(id=r[0], supplier=r[1] or "", bill_no=r[2] or "", bill_date=r[3] or "", amount_p=r[4], reason=r[5] or "",
                            reason_hi=S446_CLAIM_REASON_HI.get(r[5] or "", r[5] or ""), raised_by=r[6] or "", raised_at=(r[7] or "")[:16],
                            state=r[8] or "open", contacted=r[9] or ""))
        return out
    except Exception:                                          # noqa: BLE001
        return []


@bp.route("/finance/darpan/kal/api/claim-answer", methods=["POST"])
def api_s446_claim_answer():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    b = request.get_json(silent=True) or {}
    try:
        cid = int(b.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ans = str(b.get("answer") or "").strip()
    if ans not in S446_CLAIM_ANSWERS:
        return jsonify(ok=False, error="bad_request", answers=list(S446_CLAIM_ANSWERS)), 400
    if not _has(con, "amir_claim"):
        return jsonify(ok=False, error="not_found"), 404
    r = con.execute("SELECT state FROM amir_claim WHERE id=?", (cid,)).fetchone()
    if r is None:
        return jsonify(ok=False, error="not_found"), 404
    if r[0] == "settled":
        return jsonify(ok=False, error="already_settled", message="Yeh claim pehle hi band ho chuka hai."), 409
    if ans == "baat_hui":
        con.execute("UPDATE amir_claim SET state='contacted', contacted_note=? WHERE id=?",
                    ("%s: supplier se baat ho gayi (%s)" % (u["user"], now_iso()[:16]), cid))
    else:
        con.execute("UPDATE amir_claim SET state='settled', settled_outcome='darpan_received', settled_at=?, settled_by=? WHERE id=?",
                    (now_iso(), u["user"], cid))
    _audit(con, u["user"], "amir_claim_answer", {"id": cid, "answer": ans, "kit": "S446"})
    con.commit()
    return jsonify(ok=True, id=cid, answer=ans)
# ---- S446_AMIR_STAGES_BILLS end ----
