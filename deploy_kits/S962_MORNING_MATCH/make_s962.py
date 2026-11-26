#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s962.py -- S962_MORNING_MATCH (the parent, S529, 26-Nov-2026; D1080, the Morning Match kit C, part 1; F-1678, F-1679).
    python3 make_s962.py <day_check.py> <slip_adjust.py> <slip_log.py> <out_dir>
Remakes the three TO files from the FROM bytes: every change is an exact anchor that must occur exactly once (else it refuses and
writes nothing). No patient name, number or clinic ID in this file (F-185)."""
import hashlib
import os
import sys

FROM = {"day_check.py": "d5c95ea9", "slip_adjust.py": "41c55a99", "slip_log.py": "3553a965"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def one(src, old, new, name, label):
    n = src.count(old)
    if n != 1:
        raise SystemExit("REFUSED %s: anchor '%s' found %d times (want 1)" % (name, label, n))
    return src.replace(old, new, 1)


def span(src, start, end, new, name, label):
    """Replace from `start` (inclusive) to `end` (exclusive); each must occur exactly once, start before end."""
    a, b = src.count(start), src.count(end)
    if a != 1 or b != 1:
        raise SystemExit("REFUSED %s: span '%s' anchors %d/%d (want 1/1)" % (name, label, a, b))
    i, j = src.index(start), src.index(end)
    if j <= i:
        raise SystemExit("REFUSED %s: span '%s' end before start" % (name, label))
    return src[:i] + new + src[j:]


# ================================================================================================================ day_check.py
DC_DOC_OLD = "No patient name, no number, no secret in this file (F-185).\n\"\"\"\nimport datetime as dt\n"
DC_DOC_NEW = ("No patient name, no number, no secret in this file (F-185).\n\n"
              "S962 (session S529, 26-Nov-2026; D1080, the Morning Match kit C part 1; F-1678, F-1679) -- his ok of 12:58 on the\n"
              "mock-up v2.1: a radd after billing is MATCHED both ways (Docterz kept the bill: 'billed . refunded' / 'billed . money\n"
              "never taken'; Docterz cancelled it too: 'cancelled . refunded') -- never a false parchi card, never subtracted twice;\n"
              "a slip whose patient Docterz does not carry goes to HIS back-date list by itself (no 'Added' for any staff login --\n"
              "only his login can back-date); the staff see that list with 'Paise liye hi nahi' (nid_mark 'free', theirs) and\n"
              "'Dr sahab ko yaad dilayein' (a push to his login, once in three hours); the day in one line on top (register = Docterz\n"
              "+ slips not in Docterz - refunded / never taken + not explained); his console line reads '<day>: all matched' or the\n"
              "counts. A staff 'free' answer is named as theirs, never as his.\n"
              "\"\"\"\nimport datetime as dt\nimport os\n")

DC_NOTE_START = "def _s846_note(w, act):\n"
DC_NOTE_END = "def check_day(con, d):\n"
DC_NOTE_NEW = r'''def _s846_note(w, act, who=""):
    en, hi = S846_WORDS.get(act, (act, act))
    wl = (who or "").strip().lower()
    if wl and wl != "manoj":                              # S962: a staff login's answer is named as theirs, never as his
        if act == "free":
            en, hi = "money never taken (%s)" % wl.title(), "paise liye hi nahi (%s)" % wl.title()
        else:
            en, hi = en.replace("Dr Manoj", wl.title()), hi.replace("Dr Manoj", wl.title())
    return ("%s %s · %s — %s" % (rs(w["amount"]), w["what_en"], _who_en(w["name"], w["cid"]), en),
            "%s %s · %s — %s" % (rs(w["amount"]), w["what_hi"], _who_en(w["name"], w["cid"]), hi))


# ---------------------------------------------------------------- S962 (D1080): the Morning Match
S962 = "S962.1"
REMIND_GAP_H = 3                                         # "Dr sahab ko yaad dilayein": once in three hours, across the days
NID_PAGE = "/finance/clinic/not-in-docterz"
LIVE_DB = os.environ.get("EVCHK_LIVE_DB", "/root/finance/finance.db")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
PUSHER = None                                            # the walk hands in a stub: (who, title, body, url, tag) -> (sent, why)
REFUND_EN = {"billed_ret": "billed · refunded", "billed_nt": "billed · money never taken", "cancelled_ret": "cancelled · refunded"}
REFUND_HI = {"billed_ret": "bill raha · paise lautaye", "billed_nt": "bill raha · paise liye hi nahi",
             "cancelled_ret": "bill bhi cancel · paise lautaye"}


def _s962_items(con, slip_id):
    """[(kind, expected paise, word)] of one slip's X-ray / procedure lines (a REJECTED chhoot puts the full rate back)."""
    try:
        its = [dict(r) for r in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (slip_id,))]
    except Exception:                                    # noqa: BLE001
        return []
    rej = set()
    if its and _has(con, "slip_adjust"):
        try:
            rej = {r[0] for r in con.execute("SELECT item_id FROM slip_adjust WHERE state='rejected' AND item_id IN (%s)"
                                             % ",".join("?" * len(its)), [i["id"] for i in its])}
        except Exception:                                # noqa: BLE001
            rej = set()
    out = []
    for it in its:
        if it.get("kind") in ("xray", "proc"):
            disc = 0 if it["id"] in rej else int(it.get("discount_p") or 0)
            out.append((it["kind"], max(0, int(it.get("price_p") or 0) - disc), _item_word(it)))
    return out


def _cancels(con, d):
    """S962: the day's radd after billing (slip_adjust kind 'cancel', pending or approved -- an approved one has taken its slip
    out of the day's parchis), each with its slip's own money. [] when anything cannot be read."""
    if not (_has(con, "slip_adjust") and _has(con, "slip")):
        return []
    try:
        rows = [dict(r) for r in con.execute("SELECT * FROM slip_adjust WHERE kind='cancel' AND day=? AND state IN "
                                             "('pending','approved') ORDER BY id", (d,))]
    except Exception:                                    # noqa: BLE001
        return []
    out, fee, seen = [], None, set()
    for a in rows:
        if a["slip_id"] in seen:
            continue
        s = con.execute("SELECT * FROM slip WHERE id=?", (a["slip_id"],)).fetchone()
        if s is None:
            continue
        seen.add(a["slip_id"])
        s = dict(s)
        if s["series"] == "opd":
            if fee is None:
                try:
                    fee = int(_SL().usual_fee(con, d) or 0) if _SL() is not None else 0
                except Exception:                        # noqa: BLE001
                    fee = 0
            items = [("consult", fee, "")]
        else:
            items = _s962_items(con, s["id"])
        how = (a.get("cancel_how") or "").strip()
        out.append(dict(slip_id=s["id"], series=s["series"], slip_no=s["slip_no"],
                        cid=str(a.get("clinic_id") or s.get("clinic_id") or "").strip(), how=how,
                        tender=((a.get("refund_t") or "").strip().lower() if how == "returned" else ""), state=a["state"],
                        made_by=a.get("made_by") or "", made_at=a.get("made_at") or "",
                        paid=(s.get("paid_mode") or "").strip().lower(), items=items, amount=sum(x[1] for x in items),
                        name=(s.get("name_seen") or s.get("no_id_name") or "").strip()))
    return out


def _s962_hold(lines, slips, cancels):
    """S962 (F-1678): the Docterz lines each radd covers. As clinic_money's S442 takes an approved radd's line out: an OPD radd
    covers one consultation of its ID; an X-ray/procedure radd that ID's X-ray and procedure lines -- unless the ID has another
    live parchi of that kind that day, when only lines of the radd's own amounts are taken.
    The register's book is written NET of a refund (read on the 23-Oct database: a refunded fee was never written), so a
    radd's line Docterz still bills is taken out of Docterz's side -- refunded or never taken alike, as clinic_money's S442
    takes it out of the expected cash / UPI; a radd Docterz cancelled too moves nothing. -> (held {(section, sn): cancel},
    refunds [the matched radds])."""
    held, refunds = {}, []
    live_opd, live_xp, live_it = {}, set(), {}
    for s in slips:
        if s.get("cancel") or not s.get("clinic_id"):
            continue
        if s["series"] == "opd":
            live_opd[s["clinic_id"]] = live_opd.get(s["clinic_id"], 0) + 1
        else:
            live_xp.add(s["clinic_id"])
            for it in s.get("items", []):
                k = (s["clinic_id"], it.get("kind"), int(it.get("expect_p") or 0))
                live_it[k] = live_it.get(k, 0) + 1
    for c in cancels:
        cid = c["cid"]
        mine = [ln for ln in lines if cid and ln["cid"] == cid and ln["amount_p"] > 0 and (ln["section"], ln["sn"]) not in held]
        take = []
        if c["series"] == "opd":
            cons = [ln for ln in mine if ln["section"] == "consult"]
            if len(cons) > live_opd.get(cid, 0):
                take = cons[:1]
        else:
            xp = [ln for ln in mine if ln["section"] in ("xray", "proc")]
            if cid in live_xp:                           # cold review: a line only while Docterz has more of that kind and
                for kind, amt, _w in c["items"]:         # amount than the live parchis of the ID carry
                    same = [ln for ln in xp if ln["section"] == kind and ln["amount_p"] == amt and ln not in take]
                    if len(same) > live_it.get((cid, kind, amt), 0):
                        take.append(same[0])
            else:
                take = xp
        for ln in take:
            held[(ln["section"], ln["sn"])] = c
        if c["how"] != "returned" and not take:
            continue                                     # money never taken and no Docterz bill: nothing to match
        t_back = c["tender"] if c["tender"] in TENDERS else ""
        word = ("billed_ret" if c["how"] == "returned" else "billed_nt") if take else "cancelled_ret"
        refunds.append(dict(c, kept=bool(take), billed=sum(ln["amount_p"] for ln in take), t_back=t_back, word=word,
                            shown=(sum(ln["amount_p"] for ln in take) if take else c["amount"]),
                            pname=(take[0]["patient"] if take and take[0]["patient"] else c["name"])))
    return held, refunds


def _s962_legs(legs, held_lines, paid_lines):
    """Cold review (S962): a bill paid two ways (clinic_day_tender) whose radd's line is out of Docterz's side -- that line's
    amount comes off the ID's legs -- a leg of the same amount in the refund's own tender first, then any leg of that amount,
    else the legs reduced, the refund's tender first, then the largest -- and an ID with no live line of any amount left loses its
    legs altogether. held_lines: [(line, its radd)]."""
    out = {k: list(v) for k, v in legs.items()}
    for ln, c in held_lines:
        lg = out.get(ln["cid"])
        if not lg:
            continue
        due = int(ln["amount_p"] or 0)
        tb = c.get("tender") if c.get("how") == "returned" else ""
        i = next((j for j, (m, a) in enumerate(lg) if a == due and tb and tender_of(m) == tb), None)
        if i is None:
            i = next((j for j, (_m, a) in enumerate(lg) if a == due), None)
        if i is not None:
            lg.pop(i)
            continue
        for j in sorted(range(len(lg)), key=lambda x: (0 if (tb and tender_of(lg[x][0]) == tb) else 1, -lg[x][1])):
            if due <= 0:
                break
            m, a = lg[j]
            cut = min(a, due)
            lg[j] = (m, a - cut)
            due -= cut
        out[ln["cid"]] = [(m, a) for m, a in lg if a > 0]
    return {k: v for k, v in out.items() if v and any(ln["cid"] == k and ln["amount_p"] > 0 for ln in paid_lines)}


def _s962_add(rows, r):
    """One back-date row per (slip, kind), as his list and its answers work (re-look): two lines of one slip's kind are joined;
    the row counts as in the register when any part of it is."""
    for x in rows:
        if x["slip_id"] == r["slip_id"] and x["kind"] == r["kind"]:
            x["amount"] += r["amount"]
            x["what_en"] = "%s + %s" % (x["what_en"], r["what_en"])
            x["what_hi"] = "%s + %s" % (x["what_hi"], r["what_hi"])
            x["placed"] = x["placed"] or r["placed"]
            x["tender"] = x["tender"] or r["tender"]
            return
    rows.append(r)


def _s962_nid_keys(con, d):
    """{(slip_id, kind)} -- the day's rows of his 'Slips not in Docterz' list (answered or not). set() when it cannot be read:
    then every slip keeps its staff card, as before S962."""
    try:
        import not_in_docterz                            # noqa: PLC0415
        return {(r["slip_id"], r["kind"]) for r in not_in_docterz.rows(con, d, d)}
    except Exception:                                    # noqa: BLE001
        return set()


def _s962_mark_who(con, d):
    """{(slip_id, kind): who} -- who gave each live answer of the day on the 'not in Docterz' list. {} when absent."""
    try:
        if not _has(con, "nid_mark"):
            return {}
        return {(m[0], m[1]): (m[2] or "") for m in con.execute("SELECT slip_id, kind, who FROM nid_mark WHERE day=? AND state='live'", (d,))}
    except Exception:                                    # noqa: BLE001
        return {}


def _s962_mkey(w):
    s = w.get("slip") or {}
    return (s.get("id"), "opd" if w.get("opd") else w.get("section"))


def _s962_live(con):
    try:
        path = con.execute("PRAGMA database_list").fetchone()[2]
        return bool(path) and os.path.realpath(path) == os.path.realpath(LIVE_DB)
    except Exception:                                    # noqa: BLE001
        return False


def _s962_push(con, who, title, body, url, tag):
    """(sent, why) through the call-back clock's own Web Push to his own devices (never the staff ntfy topic) -- only from
    the live database: a walk or a copy pushes nothing (A-D147)."""
    if PUSHER is not None:
        return PUSHER(who, title, body, url, tag)
    if not _s962_live(con):
        return 0, "not the live database"
    try:
        import sys                                       # noqa: PLC0415
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import callback_clock as cc                      # noqa: PLC0415
        pusher = cc.get_pusher(None)
        if pusher is None:
            return 0, "no push road"
        s, _f = cc.push(pusher, list(who), title, body, url, tag)   # his own devices only: never the staff topic
        return s, ("" if s else "no device of his took it")
    except Exception as ex:                              # noqa: BLE001
        return 0, "send: %s" % str(ex)[:80]


def _s962_last_remind(con):
    try:
        r = con.execute("SELECT who, at FROM day_check_tick WHERE act='remind' AND state='live' AND reason IN ('sent','sending') "
                        "ORDER BY at DESC, id DESC LIMIT 1").fetchone()
        return dict(r) if r else None
    except Exception:                                    # noqa: BLE001
        return None


'''

# --- check_day: the cancels read beside the parchis
DC_E1_OLD = "    slips = _parchi(con, d)\n    paid_lines = [ln for ln in lines if ln[\"section\"] in (\"consult\", \"xray\", \"proc\")]\n"
DC_E1_NEW = ("    slips = _parchi(con, d)\n    cancels = _cancels(con, d)                           # S962 (F-1678): every radd of the day\n"
             "    paid_lines = [ln for ln in lines if ln[\"section\"] in (\"consult\", \"xray\", \"proc\")]\n")

# --- check_day: the radds matched before the totals; money never taken leaves Docterz's side, a fee Docterz cancelled too
#     leaves the register's book
DC_E2_OLD = "    # --- the totals: register - Docterz, by tender and by section x tender\n    units = _units(paid_lines, legs)\n"
DC_E2_NEW = ("    # S962 (D1080, F-1678): each radd matched -- Docterz kept the bill, or cancelled it too; never subtracted twice\n"
             "    held, refunds = _s962_hold(lines, slips, cancels)\n"
             "    nt_billed = sum(ln[\"amount_p\"] for ln in paid_lines if (ln[\"section\"], ln[\"sn\"]) in held)\n"
             "    paid_lines = [ln for ln in paid_lines if (ln[\"section\"], ln[\"sn\"]) not in held]   # the book is net of a radd\n"
             "    if held:                                             # a bill paid two ways: the radd's part comes off its legs\n"
             "        legs = _s962_legs(legs, [(ln, held[(ln[\"section\"], ln[\"sn\"])]) for ln in lines if (ln[\"section\"], ln[\"sn\"]) in held], paid_lines)\n"
             "    # --- the totals: register - Docterz, by tender and by section x tender\n    units = _units(paid_lines, legs)\n"
             )

DC_E4_OLD = "    for cid, ss in xp_by.items():\n        mine = by_cid.get(cid, [])\n"
DC_E4_NEW = ("    for cid, ss in xp_by.items():\n"
             "        mine = [ln for ln in by_cid.get(cid, []) if (ln[\"section\"], ln[\"sn\"]) not in held]   # S962: a radd's lines are matched\n")

DC_E5_OLD = ("        if ln[\"section\"] in (\"xray\", \"proc\") and ln[\"amount_p\"] > 0 and ln[\"cid\"] not in xp_by:\n")
DC_E5_NEW = ("        if (ln[\"section\"] in (\"xray\", \"proc\") and ln[\"amount_p\"] > 0 and ln[\"cid\"] not in xp_by\n"
             "                and (ln[\"section\"], ln[\"sn\"]) not in held):   # S962 (F-1678): a radd's bill is no missing parchi\n")
DC_E5B_OLD = "                                        amount=sum(x[\"amount_p\"] for x in by_cid.get(ln[\"cid\"], []) if x[\"section\"] == ln[\"section\"]),\n"
DC_E5B_NEW = ("                                        amount=sum(x[\"amount_p\"] for x in by_cid.get(ln[\"cid\"], []) if x[\"section\"] == ln[\"section\"]\n"
              "                                                   and (x[\"section\"], x[\"sn\"]) not in held),\n")

DC_E6_OLD = ("    orphan_cons = [ln for ln in paid_lines if ln[\"section\"] == \"consult\" and ln[\"amount_p\"] > 0 and ln[\"cid\"] not in opd_ids]\n")
DC_E6_NEW = ("    orphan_cons = [ln for ln in paid_lines if ln[\"section\"] == \"consult\" and ln[\"amount_p\"] > 0 and ln[\"cid\"] not in opd_ids\n"
             "                   and (ln[\"section\"], ln[\"sn\"]) not in held]          # S962 (F-1678)\n")

# --- check_day: the money -- a slip Docterz does not carry goes to his back-date list, never to a staff 'Added'
DC_E8_START = "    # --- 2 · the money: wanted lines are placed while the register holds room for them (the referee)\n"
DC_E8_END = "    # --- 3 · payment modes: money in one tender of Docterz that the register holds in another\n"
DC_E8_NEW = r'''    # --- 2 · the money: wanted lines are placed while the register holds room for them (the referee)
    # S962 (D1080, F-1679): a slip whose patient Docterz does not carry is HIS to back-date -- it goes to his back-date list by
    # itself (the same rows as his 'Slips not in Docterz' page), never to a staff 'Added'. Its money is still placed.
    room = sum(delta.values())
    want.sort(key=lambda w: (0 if w["tick"] else 1, -w["amount"]))
    _s846 = _s846_marks(con, d)                           # S846: his answers on his 'Slips not in Docterz' page
    _s962w = _s962_mark_who(con, d)                       # S962: who answered
    _nid = _s962_nid_keys(con, d)                         # second look: only rows his own list carries go to it
    backdate, nid_placed = [], 0
    for w in want:
        _sa = _s846_act(_s846, w)
        _by = _s962w.get(_s962_mkey(w), "")
        if _sa in ("free", "wrong"):                 # nothing collected: nothing for the staff to do
            out["notes"].append(_s846_note(w, _sa, _by))
            continue
        if w["amount"] > 0 and room >= w["amount"]:
            t = w["tick"] if w["tick"] in TENDERS else max(TENDERS, key=lambda x: delta[x])
            delta[t] -= w["amount"]
            sdelta[(w["section"], t)] = sdelta.get((w["section"], t), 0) - w["amount"]
            room -= w["amount"]
            if _sa:                                       # S846: entered back-dated / kept outside -- the money is placed, no card
                nid_placed += w["amount"]
                out["notes"].append(_s846_note(w, _sa, _by))
                continue
            if not w.get("partial") and _s962_mkey(w) in _nid:   # S962: his back-date list, with the money placed
                nid_placed += w["amount"]
                _s962_add(backdate, dict(key=w["key"], slip_id=(w.get("slip") or {}).get("id"), kind=_s962_mkey(w)[1], cid=w["cid"],
                                         name=w["name"], what_en=w["what_en"], what_hi=w["what_hi"], amount=w["amount"], tender=t,
                                         placed=True))
                continue
            cards.append(_card("missing", w["key"], w["amount"], d, who="docterz", tender=t, cid=w["cid"], name=w["name"],
                               slip=w["slip"], item=w["item"], section=w["section"],
                               en="%s — Docterz entry missing · %s · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_en"], T_EN[t]),
                               hi="%s — Docterz mein entry nahi · %s · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_hi"], T_HI[t])))
        elif w.get("partial"):
            # register = Docterz != parchi, and Docterz has the line: the parchi carries too much
            ps, ds = w["partial"]
            parchi_side.append(dict(kind="parchi_over", cid=w["cid"], name=w["name"], section=w["section"], amount=ps - ds,
                                    slip=w["slip"], key="pover:%s:%s" % (w["cid"], w["section"]), sums=(ps, ds)))
        elif _sa:
            # S962: his answer says the money was taken (entered / kept outside), but the register does not hold it
            n_en, n_hi = _s846_note(w, _sa, _by)
            cards.append(_card("hand", "s962ans:%s" % w["key"], w["amount"], d,
                               en="%s — but the register does not hold it; check by hand" % n_en,
                               hi="%s — par register mein nahi; haath se dekhein" % n_hi))
        elif _s962_mkey(w) in _nid:
            # S962: register = Docterz != parchi -- not billed and not collected; his list, the staff can say 'money never taken'
            _s962_add(backdate, dict(key=w["key"], slip_id=(w.get("slip") or {}).get("id"), kind=_s962_mkey(w)[1], cid=w["cid"],
                                     name=w["name"], what_en=w["what_en"], what_hi=w["what_hi"], amount=w["amount"], tender="",
                                     placed=False))
        else:
            # not on his list (Docterz's clinical report knows the visit, an ID his list cannot read): the staff card, as before
            cards.append(_card("notbilled", w["key"], w["amount"], d, who="docterz", cid=w["cid"], name=w["name"],
                               slip=w["slip"], item=w["item"], section=w["section"],
                               en="%s on the parchi — not billed, not in the register · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_en"]),
                               hi="%s parchi par — na bill hua, na register mein · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_hi"])))

'''

DC_E9_OLD = "    out[\"state\"] = \"checked\"\n    out[\"cards\"] = cards\n    out[\"counts\"] = _counts(cards)\n"
DC_E9_NEW = r'''    # S962 (D1080): the day in one line -- register (written net of refunds) = Docterz + slips not in Docterz - refunded / never
    # taken (bills Docterz still carries) + Docterz entries still missing (staff) + not explained
    top = dict(reg=sum(reg.values()), doc=sum(doc_t.values()) + nt_billed, nid=nid_placed, back=nt_billed,
               missing=sum(c["amount"] for c in cards if c["kind"] == "missing"))
    top["left"] = top["reg"] - (top["doc"] + top["nid"] - top["back"] + top["missing"])
    issue = {str(c.get("cid") or "") for c in cards} | {b["cid"] for b in backdate} | {r["cid"] for r in refunds}
    pts = {ln["cid"] for ln in lines if ln["cid"] and ln["amount_p"] > 0}
    out["top"], out["backdate"], out["refunds"] = top, backdate, refunds
    out["matched_n"] = len(pts - issue)
    out["state"] = "checked"
    out["cards"] = cards
    out["counts"] = _counts(cards)
    out["counts"]["back_n"] = len(backdate)
    out["counts"]["back_p"] = sum(b["amount"] for b in backdate)
'''

DC_SUM_START = "def summary_en(chk):\n"
DC_SUM_END = "# ---------------------------------------------------------------- ticks\n"
DC_SUM_NEW = r'''def summary_en(chk):
    """His line (S962, the mock-up's artboard 5): '<day>: all matched', else the counts -- to back-date, staff fixing, not
    explained -- every part named, empty parts left out."""
    d = dm(chk["day"])
    if chk.get("state") == "no_docterz":
        return "%s: waiting for the Docterz export" % d
    if chk.get("state") == "no_register":
        return "%s: the register is not filled yet" % d
    c = chk["counts"]
    parts = []
    if chk.get("reexport"):                              # S640: staff have ticked every Docterz line -- his re-export is next
        parts.append("Re-export %s from Docterz" % d)
        if chk.get("notright"):
            parts.append("%d marked not right by staff" % chk["notright"])
    if c.get("back_n"):
        parts.append("%d to back-date" % c["back_n"])
    cs = chk.get("cards") or []
    n_staff = sum(1 for x in cs if x["who"] in ("docterz", "parchi") and not x.get("tick"))
    if n_staff:
        parts.append("staff fixing %d" % n_staff)
    if c["hand"]:
        parts.append("%d to check by hand" % c["hand"])
    left = (chk.get("top") or {}).get("left") or 0
    if left:
        parts.append("%s not explained" % rs(abs(left)) if left > 0 else "%s more in Docterz, not explained" % rs(-left))
    if chk.get("not_fixed"):
        parts.append("%d not fixed after the re-export" % chk["not_fixed"])
    return "%s: %s" % (d, " · ".join(parts) if parts else "all matched")


def summary_hi(chk):
    d = dm(chk["day"])
    if chk.get("state") == "no_docterz":
        return "%s: Docterz export abhi nahi aaya" % d
    if chk.get("state") == "no_register":
        return "%s: register abhi nahi bhara" % d
    c = chk["counts"]
    parts = []
    cs = chk.get("cards") or []
    n_staff = sum(1 for x in cs if x["who"] in ("docterz", "parchi") and not x.get("tick"))
    if n_staff:
        parts.append("%d cheez theek karni" % n_staff if n_staff == 1 else "%d cheezein theek karni" % n_staff)
    if c["hand"]:
        parts.append("%d haath se dekhni" % c["hand"])
    if c.get("back_n"):
        parts.append("%d Dr sahab ke paas" % c["back_n"])
    left = (chk.get("top") or {}).get("left") or 0
    if left:
        parts.append(("%s ka pata nahi" if left > 0 else "%s ka pata nahi (Docterz mein zyada)") % rs(abs(left)))
    return "%s: %s" % (d, " · ".join(parts) if parts else "sab mil gaya")


def is_clean(chk):
    return (chk.get("state") == "checked" and not chk["cards"] and not chk.get("backdate")
            and not (chk.get("top") or {}).get("left"))


'''

DC_HTML_OLD = "    groups = ((\"docterz\", \"Docterz — Shivani, Alisha, Shavez\", \"Docterz — Shivani, Alisha, Shavez\"),\n"
DC_HTML_NEW = ("    out.append(_s962_html(con, chk, u, english))         # S962 (D1080): the day in one line, what matched, his back-date list\n"
               "    groups = ((\"docterz\", \"Docterz — Shivani, Alisha, Shavez\", \"Docterz — Shivani, Alisha, Shavez\"),\n")

DC_S962HTML_BEFORE = "def _bank_html(con, d, u, english):\n"
DC_S962HTML_NEW = r'''def _s962_line(chk, english):
    tp = chk.get("top") or {}
    if not tp:
        return ""
    if english:
        bits = ["Register %s" % rs(tp["reg"]), "= Docterz %s" % rs(tp["doc"])]
        if tp["nid"]:
            bits.append("+ slips not in Docterz %s" % rs(tp["nid"]))
        if tp["back"]:
            bits.append("− refunded / never taken %s" % rs(tp["back"]))
        if tp["missing"]:
            bits.append("+ Docterz entries still missing %s" % rs(tp["missing"]))
        if tp["left"]:
            bits.append(("+ %s not explained" if tp["left"] > 0 else "− %s not explained (more in Docterz)") % rs(abs(tp["left"])))
    else:
        bits = ["Register %s" % rs(tp["reg"]), "= Docterz %s" % rs(tp["doc"])]
        if tp["nid"]:
            bits.append("+ Docterz se bahar parchi %s" % rs(tp["nid"]))
        if tp["back"]:
            bits.append("− lautaye / liye hi nahi %s" % rs(tp["back"]))
        if tp["missing"]:
            bits.append("+ Docterz mein entry baaki %s" % rs(tp["missing"]))
        if tp["left"]:
            bits.append(("+ %s ka pata nahi" if tp["left"] > 0 else "− %s ka pata nahi (Docterz mein zyada)") % rs(abs(tp["left"])))
    return " ".join(bits)


def _s962_html(con, chk, u, english):
    """S962 (D1080, the mock-up's artboards 4 and 5): the day in one line; what matched (folded); his back-date list -- for the
    staff with 'Paise liye hi nahi' and 'Dr sahab ko yaad dilayein', for him a link to his page."""
    d = chk["day"]
    out = ["<p class='s962top'>%s</p>" % _esc(_s962_line(chk, english))]
    rf = chk.get("refunds") or []
    mn = chk.get("matched_n") or 0
    if mn or rf:
        head = (("✓ %d patient%s match" % (mn, "" if mn == 1 else "s")) if english else ("✓ %d mareez mil gaye" % mn))
        if rf:
            head += (" · %d refund / radd matched" % len(rf)) if english else (" · %d refund / radd mil gaya" % len(rf))
        li = []
        for r in rf:
            what = "OPD" if r["series"] == "opd" else "X-ray / procedure"
            tb = (" · %s" % ("cash" if r["t_back"] == "cash" else "UPI")) if r["t_back"] else ""
            li.append("<li>%s · %s %s%s · %s ✓</li>" % (_esc(_who_en(r["pname"], r["cid"])), what, rs(r["shown"]), tb,
                                                         _esc((REFUND_EN if english else REFUND_HI)[r["word"]])))
        out.append("<details class='s962m'><summary>%s</summary><ul>%s</ul></details>" % (_esc(head), "".join(li)))
    rows = chk.get("backdate") or []
    if not rows:
        return "".join(out)
    staff = _user(u) in PARCHI_USERS + DOCTERZ_USERS
    out.append("<h3 class='grp'>%s (%d)</h3>" % ("Your back-date list · slips not in Docterz" if english
                                                  else "Dr sahab ki back-date list · parchi hai, Docterz mein nahi", len(rows)))
    if staff:
        last = _s962_last_remind(con)
        if last:
            out.append("<p class='mut'>Yaad dilaya: %s (%s)</p>" % (_esc(str(last["at"])[5:16]), _esc((last["who"] or "").title())))
        out.append(_btn(d, "remind", "remind", "Dr sahab ko yaad dilayein"))
    for b in rows:
        txt = "%s · %s · %s%s · %s" % (_who_en(b["name"], b["cid"]), b["what_en"] if english else b["what_hi"], rs(b["amount"]),
                                        (" · " + T_EN[b["tender"]]) if (english and b["tender"]) else "",
                                        ("in the register" if b["placed"] else "NOT in the register") if english else
                                        ("Dr sahab entry karenge" if b["placed"] else "register mein bhi nahi"))
        btn = ""
        if staff and b.get("slip_id") and not b["placed"]:   # the register holds a placed row's money: never 'not taken' 
            btn = _btn(d, b["key"], "nidfree", "Paise liye hi nahi", "x",
                       "<input type='hidden' name='slip' value='%d'><input type='hidden' name='kind' value='%s'>" % (b["slip_id"], _esc(b["kind"])))
        out.append("<div class='cline'><span class='ct'>%s</span><span class='cb'>%s</span></div>" % (_esc(txt), btn))
    if english:
        out.append("<p class='navrow'><a class='tb' href='%s'>Open your list (Entered / Not entering / Free / Wrong slip)</a></p>" % NID_PAGE)
    else:
        out.append("<p class='mut'>Yeh apne aap Dr sahab ki list par jaati hain — Cash / UPI kuch nahi bharna (register mein likha hai). "
                   "Sirf jab paise liye hi nahi, ek tap.</p>")
    return "".join(out)


def _s962_act(con, d, chk, a, f, u, who, english):
    """S962: the staff's two taps on his back-date list. -> (ok, err)."""
    if who not in PARCHI_USERS + DOCTERZ_USERS:          # the named staff only (cold review)
        return "", ("Not permitted." if english else "Aapke liye nahi.")
    rows = chk.get("backdate") or []
    if a == "nidfree":
        try:
            sid = int(f.get("slip") or 0)
        except (TypeError, ValueError):
            sid = 0
        kind = (f.get("kind") or "").strip()
        if not any(b.get("slip_id") == sid and b["kind"] == kind and not b["placed"] for b in rows):
            return "", ("This line has already changed — the page is fresh now." if english else "Yeh line badal chuki hai — page naya hai.")
        import not_in_docterz                            # noqa: PLC0415
        try:
            not_in_docterz.mark(con, who, sid, kind, "free")
        except not_in_docterz.MarkError as ex:
            return "", str(ex)
        return ("Noted: money never taken." if english else "Likh liya: paise liye hi nahi."), ""
    if not rows:
        return "", ("The list is empty." if english else "List khaali hai.")
    ensure(con)
    con.commit()
    con.execute("BEGIN IMMEDIATE")                       # cold review: two taps at once -- one push
    last = _s962_last_remind(con)
    now = _now()                                         # the clock add_tick stamps with
    if last:
        try:
            at = dt.datetime.strptime(str(last["at"])[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            at = None
        if at is not None and now - at < dt.timedelta(hours=REMIND_GAP_H):
            con.rollback()
            return "", "Pehle hi yaad dilaya — %s (%s). %d ghante mein ek baar." % (str(last["at"])[11:16], (last["who"] or "").title(), REMIND_GAP_H)
    cur = con.execute("INSERT INTO day_check_tick (day, key, act, reason, pick, who, at) VALUES (?,?,?,?,?,?,?)",
                      (d, "remind", "remind", "sending", str(len(rows)), who, _stamp()))
    tid = cur.lastrowid
    con.commit()
    body = "%s: %d slip%s not in Docterz — your back-date list (a reminder from %s)" % (dm(d), len(rows), "" if len(rows) == 1 else "s",
                                                                                     who.title())   # his phone: English
    sent, why = _s962_push(con, ["manoj"], "Back-date list", body, NID_PAGE, "s962-remind")
    con.execute("UPDATE day_check_tick SET reason=? WHERE id=?", ("sent" if sent else "not sent", tid))
    _audit_safe(con, "day_check_tick", tid, "tick_remind", None, {"day": d, "rows": len(rows), "sent": bool(sent)}, who)
    con.commit()
    return (("Dr sahab ko yaad dila diya." if sent else "Likh liya — push nahi gaya (%s)." % why), "")


'''

DC_ACT_OLD = ("    chk = check_day(con, date)\n    card = next((c for c in chk[\"cards\"] if c[\"key\"] == key), None)\n"
              "    if a == \"undo\":\n")
DC_ACT_NEW = ("    chk = check_day(con, date)\n    card = next((c for c in chk[\"cards\"] if c[\"key\"] == key), None)\n"
              "    if a in (\"nidfree\", \"remind\"):                     # S962: the staff's two taps on his back-date list\n"
              "        try:\n"
              "            return done(*_s962_act(con, date, chk, a, f, u, who, english))\n"
              "        except Exception as ex:                          # noqa: BLE001 -- a locked database or a refusal reads as it is\n"
              "            try:\n"
              "                con.rollback()\n"
              "            except Exception:                            # noqa: BLE001\n"
              "                pass\n"
              "            return done(er=str(ex)[:200])\n"
              "    if a == \"undo\":\n")

DC_STYLE_OLD = "@media (max-width:620px){button.tb,a.tb{padding:11px 12px}}\n</style>\"\"\"\n"
DC_STYLE_NEW = ("@media (max-width:620px){button.tb,a.tb{padding:11px 12px}}\n"
                "p.s962top{font-size:18px;font-weight:600;line-height:1.5;margin:8px 0 10px;overflow-wrap:anywhere}\n"
                "details.s962m{margin:0 0 12px}details.s962m summary{font-size:17px;color:#2c6e2f;cursor:pointer}\n"
                "</style>\"\"\"\n")


def make_day_check(src):
    n = "day_check.py"
    src = one(src, DC_DOC_OLD, DC_DOC_NEW, n, "docstring/imports")
    src = span(src, DC_NOTE_START, DC_NOTE_END, DC_NOTE_NEW, n, "_s846_note + S962 helpers")
    src = one(src, DC_E1_OLD, DC_E1_NEW, n, "E1 cancels")
    src = one(src, DC_E2_OLD, DC_E2_NEW, n, "E2 hold")
    src = one(src, DC_E4_OLD, DC_E4_NEW, n, "E4 xp mine")
    src = one(src, DC_E5_OLD, DC_E5_NEW, n, "E5 xp orphans")
    src = one(src, DC_E5B_OLD, DC_E5B_NEW, n, "E5b orphan sum")
    src = one(src, DC_E6_OLD, DC_E6_NEW, n, "E6 opd orphans")
    src = span(src, DC_E8_START, DC_E8_END, DC_E8_NEW, n, "E8 the money")
    src = one(src, DC_E9_OLD, DC_E9_NEW, n, "E9 top line")
    src = span(src, DC_SUM_START, DC_SUM_END, DC_SUM_NEW, n, "summaries")
    src = one(src, DC_HTML_OLD, DC_HTML_NEW, n, "cards_html")
    src = one(src, DC_S962HTML_BEFORE, DC_S962HTML_NEW + DC_S962HTML_BEFORE, n, "_s962_html")
    src = one(src, DC_ACT_OLD, DC_ACT_NEW, n, "act")
    src = one(src, DC_STYLE_OLD, DC_STYLE_NEW, n, "style")
    return src


# ================================================================================================================ slip_adjust.py
SA_DOC_OLD = "CANCEL_HOW = {\"returned\": (\"Paise lauta diye\", \"money returned\"), \"never_taken\": (\"Paise liye hi nahi\", \"money never taken\")}\n"
SA_DOC_NEW = (SA_DOC_OLD +
              "REFUND_T = {\"cash\": (\"Cash mein lautaye\", \"cash\"), \"upi\": (\"UPI se lautaye\", \"UPI\")}   # S962 (D1080): the refund's tender\n")

SA_ENS_OLD = ("def ensure(con):\n    global _done\n    if _done:\n        return\n    con.executescript(SCHEMA)\n    con.commit()\n    _done = True\n")
SA_ENS_NEW = ("def ensure(con):\n    global _done\n    if _done:\n        return\n    con.executescript(SCHEMA)\n"
              "    _s962_col(con)                                         # S962: the refund's tender, once\n"
              "    con.commit()\n    _done = True\n\n\n"
              "def _s962_col(con):\n"
              "    \"\"\"S962 (D1080): slip_adjust gains refund_t (cash | upi | '') -- added once, on first use (F-303). True when present.\"\"\"\n"
              "    try:\n"
              "        if \"refund_t\" in {r[1] for r in con.execute(\"PRAGMA table_info(slip_adjust)\")}:\n"
              "            return True\n"
              "        con.execute(\"ALTER TABLE slip_adjust ADD COLUMN refund_t TEXT NOT NULL DEFAULT ''\")\n"
              "        return True\n"
              "    except Exception:                                      # noqa: BLE001 -- an older shape keeps working without it\n"
              "        return False\n")

SA_ADD_OLD = "def add_cancel(con, who, slip_id, clinic_id, how, note=\"\"):\n"
SA_ADD_NEW = "def add_cancel(con, who, slip_id, clinic_id, how, note=\"\", tender=\"\"):\n"

SA_HOW_OLD = ("    if how not in CANCEL_HOW:\n        raise AdjustError(\"Chunein: paise lauta diye / paise liye hi nahi.\")\n")
SA_HOW_NEW = ("    if how not in CANCEL_HOW:\n        raise AdjustError(\"Chunein: paise lauta diye / paise liye hi nahi.\")\n"
              "    tender = (tender or \"\").strip().lower() if how == \"returned\" else \"\"   # S962: cash | upi, said at the desk\n"
              "    if tender and tender not in REFUND_T:\n        raise AdjustError(\"Chunein: Cash mein lautaye / UPI se lautaye.\")\n")

SA_INS_OLD = ("    cur = con.execute(\"INSERT INTO slip_adjust (slip_id, kind, cancel_how, clinic_id, note, day, made_by, made_at) VALUES (?,?,?,?,?,?,?,?)\",\n"
              "                      (slip_id, \"cancel\", how, cid, (note or \"\")[:120], s[\"day\"], who, now))\n"
              "    _audit_safe(con, cur.lastrowid, \"slip_cancel_asked\", None, json.dumps({\"slip\": slip_id, \"clinic_id\": cid, \"how\": how}), who)\n")
SA_INS_NEW = ("    if tender and _s962_col(con):                          # S962: the refund's tender beside the radd\n"
              "        cur = con.execute(\"INSERT INTO slip_adjust (slip_id, kind, cancel_how, clinic_id, note, day, made_by, made_at, refund_t) \"\n"
              "                          \"VALUES (?,?,?,?,?,?,?,?,?)\", (slip_id, \"cancel\", how, cid, (note or \"\")[:120], s[\"day\"], who, now, tender))\n"
              "    else:\n"
              "        cur = con.execute(\"INSERT INTO slip_adjust (slip_id, kind, cancel_how, clinic_id, note, day, made_by, made_at) VALUES (?,?,?,?,?,?,?,?)\",\n"
              "                          (slip_id, \"cancel\", how, cid, (note or \"\")[:120], s[\"day\"], who, now))\n"
              "    _audit_safe(con, cur.lastrowid, \"slip_cancel_asked\", None, json.dumps({\"slip\": slip_id, \"clinic_id\": cid, \"how\": how,\n"
              "                                                                       \"refund_t\": tender}), who)\n")

SA_ROUTE_OLD = ("    try:\n        add_cancel(con, _who(u), SL._int(f.get(\"slip_id\")), f.get(\"clinic_id\") or \"\", (f.get(\"how\") or \"\").strip(), f.get(\"note\") or \"\")\n"
                "    except AdjustError as ex:\n        return _back(back, err=str(ex))\n"
                "    return _back(back, ok=\"Radd likh diya — manzoori ke liye gaya.\")\n")
SA_ROUTE_NEW = ("    how, tender = (f.get(\"how\") or \"\").strip(), \"\"\n"
                "    if how in (\"returned_cash\", \"returned_upi\"):            # S962 (D1080): 'Fee lautai' -- Cash / UPI, the tag at once\n"
                "        how, tender = \"returned\", how.split(\"_\", 1)[1]\n"
                "    try:\n        add_cancel(con, _who(u), SL._int(f.get(\"slip_id\")), f.get(\"clinic_id\") or \"\", how, f.get(\"note\") or \"\", tender=tender)\n"
                "    except AdjustError as ex:\n        return _back(back, err=str(ex))\n"
                "    if how == \"returned\":\n"
                "        return _back(back, ok=\"Fee lautai likh di — parchi par tag laga (%s). Manzoori ke liye bhi gaya.\" % (REFUND_T.get(tender, (\"\", \"—\"))[1]))\n"
                "    return _back(back, ok=\"Radd likh diya — manzoori ke liye gaya.\")\n")


def make_slip_adjust(src):
    n = "slip_adjust.py"
    src = one(src, SA_DOC_OLD, SA_DOC_NEW, n, "REFUND_T")
    src = one(src, SA_ENS_OLD, SA_ENS_NEW, n, "ensure")
    src = one(src, SA_ADD_OLD, SA_ADD_NEW, n, "add_cancel signature")
    src = one(src, SA_HOW_OLD, SA_HOW_NEW, n, "add_cancel tender")
    src = one(src, SA_INS_OLD, SA_INS_NEW, n, "add_cancel insert")
    src = one(src, SA_ROUTE_OLD, SA_ROUTE_NEW, n, "route_radd")
    return src


# ================================================================================================================ slip_log.py
SL_RADD_START = "def _radd_form(con, s, back):\n"
SL_RADD_END = "def _amount_label(items):\n"
SL_RADD_NEW = r'''def _radd_form(con, s, back):
    """S442 (F-664): radd after billing -- the clinic ID and one choice; approved like a discount. S962 (D1080): 'Fee lautai' asks
    Cash / UPI and the slip carries the Refunded tag at once (the approval still follows)."""
    if _SA() is None:
        return ""
    try:
        _SA().ensure(con)
        r = con.execute("SELECT * FROM slip_adjust WHERE slip_id=? AND kind='cancel' AND state IN ('pending','approved') ORDER BY id DESC",
                        (s["id"],)).fetchone()
    except Exception:                                    # noqa: BLE001
        r = None
    if r is not None:
        r = dict(r)
        wait = "manzoor" if r["state"] == "approved" else "manzoori baaki"
        if (r.get("cancel_how") or "") == "returned":
            t = {"cash": "Cash", "upi": "UPI"}.get((r.get("refund_t") or "").lower(), "")
            return '<span class="sm"><b>&#8617; Refunded%s · %s</b> (%s, %s)</span>' % (
                (" · " + t) if t else "", _esc(str(r.get("made_at") or "")[8:10] + "-" + str(r.get("made_at") or "")[5:7] + " "
                                             + str(r.get("made_at") or "")[11:16]), wait, _esc(r["made_by"]))
        return '<span class="sm">radd %s (%s)</span>' % (wait, _esc(r["made_by"]))
    return ('<form method="post" action="/finance/slips/radd" class="adj"><input type="hidden" name="slip_id" value="%d">'
            '<input type="hidden" name="back" value="%s"><b class="sm">Fee lautai / Radd (bill banne ke baad)</b>'
            '<input name="clinic_id" inputmode="numeric" placeholder="Clinic ID" value="%s" required maxlength="12" class="am">'
            '<label class="chk"><input type="radio" name="how" value="returned_cash" required> Cash mein lautaye</label>'
            '<label class="chk"><input type="radio" name="how" value="returned_upi"> UPI se lautaye</label>'
            '<label class="chk"><input type="radio" name="how" value="never_taken"> Paise liye hi nahi</label>'
            '<button>Likho</button></form>' % (s["id"], back, _esc(s.get("clinic_id") or "")))


'''


def make_slip_log(src):
    return span(src, SL_RADD_START, SL_RADD_END, SL_RADD_NEW, "slip_log.py", "_radd_form")


def main():
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    paths = dict(zip(("day_check.py", "slip_adjust.py", "slip_log.py"), sys.argv[1:4]))
    out = sys.argv[4]
    made = {}
    for name, fn in (("day_check.py", make_day_check), ("slip_adjust.py", make_slip_adjust), ("slip_log.py", make_slip_log)):
        b = open(paths[name], "rb").read()
        if md5(b)[:8] != FROM[name]:
            raise SystemExit("REFUSED %s: it is %s, not the FROM %s" % (name, md5(b)[:8], FROM[name]))
        made[name] = fn(b.decode("utf-8")).encode("utf-8")
    os.makedirs(out, exist_ok=True)
    for name, b in made.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(b)
        print("MADE %s %s -> %s" % (name, FROM[name], md5(b)[:8]))


if __name__ == "__main__":
    main()
