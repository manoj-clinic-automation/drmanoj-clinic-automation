#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""day_check.py -- kit S636_DAY_CHECK (session S347, 24-Oct-2026; D776 stage 1; F-1017, F-1018). PARENT.
Mounted by clinic_register.init() and lives beside it. Flask and the standard library only.

THE OWNER, 23/24-Oct-2026 (D776): "It should analyse properly, give the missing money details, and Docterz and parchi
required corrections ... for shivani alisha, shavez and myself, becomes available as soon as the morning entry is done,
and the Docterz differs becomes a clickable button" · "All 3 should be able to do Docterz corrections" ·
"1300 not billed - means Docterz entry is missing" · "is clarity here better ?" · "Here we also write which ones ?"

WHAT IT DOES. One day, patient by patient, across four records:
    the parchi    (slip / slip_item -- what was DONE)
    Docterz       (clinic_day_line / clinic_day_tender -- what was BILLED)
    the register  (clinic_register_day -- what was COLLECTED, section x cash/UPI/card; counted from the handwritten book:
                   THE REFEREE, his fact of 24-Oct)
    the bank      (upi_txn -- UPI, when the statement arrives)
and it names every correction as one line, with the buttons of the person who makes it:
    Docterz (Shivani, Alisha, Shavez):  Rs X -- Docterz entry missing      [Added] [Not paid] [Free]
                                        Payment mode wrong                 [Changed] [Not right]
                                        Rs X -- patient not found          [Found it]
    Parchi (Shavez):                    [Fix] (opens the parchi again, its number and day filled) · [Remove duplicate]
The rule (the owner's, S343): register = Docterz != parchi -> the parchi is wrong; register = parchi != Docterz -> Docterz
is short; nothing explains it -> check by hand.

IT IS WORKED OUT EVERY TIME IT IS READ. Nothing is computed ahead and stored: the register's Save, a Docterz re-export
(docterz_ingest.upsert_lines replaces the day wholesale) or a corrected parchi changes the answer the next time the page
or the owner's line is read. A TICK IS STORED, NEVER TAKEN AS PROOF: a line clears only when the next export or the
parchi shows it. "Free" and "Not paid" are the existing chhoot / radd entries of slip_adjust.py (his Approve / Reject).

ONE TABLE OF ITS OWN, created on first request (F-303):
    day_check_tick  id, day, key, act, reason, pick, who, at, state (live | undone)
It reads clinic_day_line, clinic_day_tender, clinic_day_revenue, clinic_register_day, upi_txn, slip, slip_item,
slip_adjust; it writes slip / slip_item / slip_adjust only through the three parchi buttons (Fix, Remove duplicate,
Fix the ID) and slip_adjust's own add_discount / add_cancel, every write audited.
No patient name, no number, no secret in this file (F-185).
"""
import datetime as dt

from flask import Blueprint, redirect, request

bp = Blueprint("day_check", __name__)
_db = _require = _audit = None
UNIT = "clinic"
SLIP_UNIT = "slips"
_done = False

DOCTERZ_USERS = ("shivani", "alisha", "shavez")          # D776: "All 3 should be able to do Docterz corrections"
PARCHI_USERS = ("shavez", "bhati")                      # slip_log.REPORT_USERS: Bhati does the slip work as Shavez does
TENDERS = ("cash", "upi", "card")
T_EN = {"cash": "cash", "upi": "UPI", "card": "card"}
T_HI = {"cash": "cash", "upi": "UPI", "card": "card"}
SEC_EN = {"consult": "consultation", "xray": "X-ray", "proc": "procedure"}
SEC_HI = {"consult": "consultation", "xray": "X-ray", "proc": "procedure"}
NOT_RIGHT = (("docterz_right", "Docterz sahi hai", "Docterz is right"),
             ("other", "Kuch aur", "something else"))      # never the words "split payment" (the owner, 13-Oct)
NOT_RIGHT_EN = {k: e for k, _h, e in NOT_RIGHT}
NOT_RIGHT_HI = {k: h for k, h, _e in NOT_RIGHT}

SCHEMA = """
CREATE TABLE IF NOT EXISTS day_check_tick (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  day     TEXT NOT NULL,
  key     TEXT NOT NULL,
  act     TEXT NOT NULL,
  reason  TEXT NOT NULL DEFAULT '',
  pick    TEXT NOT NULL DEFAULT '',
  who     TEXT NOT NULL,
  at      TEXT NOT NULL,
  state   TEXT NOT NULL DEFAULT 'live' CHECK (state IN ('live','undone'))
);
CREATE INDEX IF NOT EXISTS day_check_tick_day ON day_check_tick(day, key);
"""


def init(app, db_getter, require_fn, audit_fn=None, unit="clinic"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    return bp


def ensure(con):
    global _done
    if _done:
        return
    con.executescript(SCHEMA)
    con.commit()
    _done = True


# ---------------------------------------------------------------- small helpers
def _now():
    return dt.datetime.now().replace(microsecond=0)


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def rs(p):
    return "Rs {:,}".format(int(round((p or 0) / 100.0)))


def _iso_ok(s):
    try:
        return dt.date.fromisoformat(s).isoformat() == s
    except (ValueError, TypeError):
        return False


def dm(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%d-%b")
    except (ValueError, TypeError):
        return iso or ""


def tender_of(mode):
    m = (mode or "").strip()
    if m == "Cash":
        return "cash"
    if m in ("Debit Card", "Credit Card"):
        return "card"
    if m in ("Online Payment", "Net Banking", "Patient APP", "Wallet"):
        return "upi"
    if m == "Split Payment":
        return "split"
    return "other" if m else ""


def _SL():
    try:
        import slip_log                                  # noqa: PLC0415
        return slip_log
    except Exception:                                    # noqa: BLE001
        return None


def _SA():
    try:
        import slip_adjust                               # noqa: PLC0415
        return slip_adjust
    except Exception:                                    # noqa: BLE001
        return None


def _CR():
    import clinic_register                               # noqa: PLC0415
    return clinic_register


def _has(con, table):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


# ---------------------------------------------------------------- reading the four records
def _docterz(con, d):
    """(lines, legs) -- lines: every Docterz line of the day with its tender; legs: {clinic_id: [(mode, paise)]} of the
    bills paid two ways (clinic_day_tender)."""
    lines, legs = [], {}
    if not _has(con, "clinic_day_line"):
        return lines, legs
    if _has(con, "clinic_day_tender"):
        for r in con.execute("SELECT clinic_id, tender, amount_p FROM clinic_day_tender WHERE business_date=? ORDER BY rowid", (d,)):
            legs.setdefault(str(r["clinic_id"] or ""), []).append(((r["tender"] or "").strip(), int(r["amount_p"] or 0)))
    for r in con.execute("SELECT section, sn, patient, clinic_id, amount_p, mode FROM clinic_day_line WHERE business_date=? "
                         "ORDER BY section, sn", (d,)):
        cid = str(r["clinic_id"] or "")
        t = "legs" if cid in legs else tender_of(r["mode"])
        lines.append(dict(section=r["section"], sn=r["sn"], patient=(r["patient"] or "").strip(), cid=cid,
                          amount_p=int(r["amount_p"] or 0), mode=r["mode"] or "", tender=t))
    return lines, legs


def _units(paid_lines, legs):
    """Every payment as it was recorded: one unit per Docterz line, and for a bill paid two ways one unit per way, placed
    on its head the owner's way (13-Oct: "the 600 is the consultation and the rest is ... X-ray or procedure"). A
    'Wallet' unit is an online booking paid through Razorpay to another bank (12-Oct): it is UPI for the register and is
    never looked for in the clinic merchant's bank feed."""
    units = []
    for ln in paid_lines:
        if ln["tender"] != "legs":
            units.append(dict(ln, wallet=(ln["mode"].strip() == "Wallet")))
    for cid, lg in legs.items():
        mine = [ln for ln in paid_lines if ln["cid"] == cid and ln["amount_p"] > 0]
        mine.sort(key=lambda x: (x["section"] != "consult", x["sn"]))
        free = list(mine)
        for mode, amt in lg:
            hit = next((ln for ln in free if ln["amount_p"] == amt), None)
            if hit is None:
                hit = free[0] if free else (mine[0] if mine else None)
            if hit is not None and hit in free:
                free.remove(hit)
            base = hit or dict(section="consult", sn=0, patient="", cid=cid)
            units.append(dict(section=base["section"], sn=base["sn"], patient=base["patient"], cid=cid, amount_p=amt,
                              mode=mode, tender=tender_of(mode), wallet=(mode == "Wallet")))
    return units


def _register(con, d):
    """{(section, tender): paise} with dressing clubbed into procedures (the owner's ruling), or None."""
    if not _has(con, "clinic_register_day"):
        return None
    r = con.execute("SELECT * FROM clinic_register_day WHERE business_date=?", (d,)).fetchone()
    if r is None:
        return None
    out = {}
    for sec, col in (("consult", "cons"), ("xray", "xray"), ("proc", "proc"), ("proc", "dress")):
        for t in TENDERS:
            try:
                v = int(r["%s_%s_p" % (col, t)] or 0)
            except (IndexError, KeyError):
                v = 0
            out[(sec, t)] = out.get((sec, t), 0) + v
    return out


def _bank(con, d):
    """(total, [amounts], known, other_upi) -- the clinic merchant's UPI for the day; other UPI (a personal phone,
    clinic_money channel 5) is never in the bank and is taken out of the register's side before comparing."""
    try:
        total, known = _CR().bank_upi(con, d)
    except Exception:                                    # noqa: BLE001
        total, known = None, False
    amts = []
    if known:
        try:
            amts = [int(r[0] or 0) for r in con.execute("SELECT amount_p FROM upi_txn WHERE unit='clinic' AND txn_date=?", (d,))]
        except Exception:                                # noqa: BLE001
            amts = []
    oth = 0
    try:
        cm = _CR()._cm
        if cm is not None:
            oth = int(cm.other_upi_total_p(con, d) or 0)
    except Exception:                                    # noqa: BLE001
        oth = 0
    return total, amts, known, oth


def _parchi(con, d):
    """The day's parchis that count: state 'ok', with each X-ray / procedure line's expected money (rate - chhoot; a
    REJECTED chhoot puts the full rate back) and any radd (cancel) entry. Uses slip_log.day_slips when it is there."""
    if not _has(con, "slip"):
        return []
    SL = _SL()
    if SL is not None:
        rows = SL.day_slips(con, d)
    else:
        rows = [dict(r) for r in con.execute("SELECT * FROM slip WHERE day=? AND state<>'void' ORDER BY series, slip_no", (d,))]
        for r in rows:
            r["items"] = [dict(i) for i in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (r["id"],))]
    adj, canc = {}, {}
    if _has(con, "slip_adjust"):
        ids = [it["id"] for r in rows for it in r.get("items", [])]
        if ids:
            for a in con.execute("SELECT * FROM slip_adjust WHERE item_id IN (%s) AND state<>'replaced' ORDER BY id"
                                 % ",".join("?" * len(ids)), ids):
                adj[a["item_id"]] = dict(a)
        for a in con.execute("SELECT * FROM slip_adjust WHERE kind='cancel' AND day=? AND state IN ('pending','approved') "
                             "ORDER BY id", (d,)):
            canc[a["slip_id"]] = dict(a)
    out = []
    for r in rows:
        if r["state"] != "ok":
            continue
        r["cancel"] = canc.get(r["id"])
        for it in r.get("items", []):
            a = adj.get(it["id"])
            disc = int(it.get("discount_p") or 0)
            if a and a["state"] == "rejected":
                disc = 0
            it["adjust"] = a
            it["expect_p"] = max(0, int(it.get("price_p") or 0) - disc)
        out.append(r)
    return out


def _name(con, cid, lines, slip=None):
    for ln in lines:
        if ln["cid"] == cid and ln["patient"]:
            return ln["patient"]
    if slip is not None:
        if slip.get("no_id_name"):
            return slip["no_id_name"]
        if slip.get("name_seen"):
            return slip["name_seen"]
    SL = _SL()
    if SL is not None and cid:
        try:
            p = SL.patient(con, cid)
            if p:
                return p[0]
        except Exception:                                # noqa: BLE001
            pass
    return ""


def _item_word(it):
    return (it.get("name") or "") + ((" " + it["side"]) if it.get("side") else "")


# ---------------------------------------------------------------- the check
def check_day(con, d):
    """The day's corrections. Pure read (the tick table aside). Returns a dict the page and the owner's line render."""
    ensure(con)
    lines, legs = _docterz(con, d)
    reg = _register(con, d)
    bank, bank_amts, bank_known, other_upi = _bank(con, d)
    slips = _parchi(con, d)
    paid_lines = [ln for ln in lines if ln["section"] in ("consult", "xray", "proc")]
    out = dict(day=d, docterz=bool(lines), register=reg is not None, bank_known=bank_known, cards=[], notes=[])
    if not lines or reg is None:
        out["state"] = "no_docterz" if not lines else "no_register"
        out["counts"] = _counts([])
        return out

    # --- the totals: register - Docterz, by tender and by section x tender
    units = _units(paid_lines, legs)
    doc_t = dict.fromkeys(TENDERS, 0)
    doc_st = {}
    other_p = 0
    for un in units:
        if un["tender"] in TENDERS:
            doc_t[un["tender"]] += un["amount_p"]
            doc_st[(un["section"], un["tender"])] = doc_st.get((un["section"], un["tender"]), 0) + un["amount_p"]
        elif un["amount_p"]:
            other_p += un["amount_p"]
    reg_t = {t: sum(v for (s, tt), v in reg.items() if tt == t) for t in TENDERS}
    delta = {t: reg_t[t] - doc_t[t] for t in TENDERS}
    sdelta = {k: reg.get(k, 0) - doc_st.get(k, 0) for k in set(reg) | set(doc_st)}
    if other_p:
        out["notes"].append(("%s in Docterz under a payment mode this page does not know" % rs(other_p),
                             "%s Docterz mein anjaan mode mein" % rs(other_p)))

    cards = []
    by_cid = {}
    for ln in lines:
        by_cid.setdefault(ln["cid"], []).append(ln)
    opd = [s for s in slips if s["series"] == "opd"]
    xp = [s for s in slips if s["series"] == "xp"]

    # --- 1 · patient by patient: the parchi against Docterz
    want = []          # money the parchi says was done and Docterz has not billed: (amount, tender guess, card base)
    parchi_side = []   # parchi lines Docterz does not support (decided after the money is placed)
    xp_by = {}
    for s in xp:
        if s.get("no_id_name") or not s.get("clinic_id"):
            cards.append(_card("hand", "noid:%d" % s["id"], 0, d,
                               en="Parchi %d has no clinic ID (%s) — match it by hand" % (s["slip_no"], s.get("no_id_name") or "—"),
                               hi="Parchi %d par clinic ID nahi (%s) — haath se milayein" % (s["slip_no"], s.get("no_id_name") or "—")))
            continue
        if s.get("cancel"):
            st = s["cancel"]["state"]
            out["notes"].append(("Parchi %d: not paid — %s" % (s["slip_no"], "approved" if st == "approved" else "waiting for your approval"),
                                 "Parchi %d: paise nahi liye — %s" % (s["slip_no"], "manzoor" if st == "approved" else "manzoori baaki")))
            continue
        xp_by.setdefault(s["clinic_id"], []).append(s)
    for cid, ss in xp_by.items():
        mine = by_cid.get(cid, [])
        name = _name(con, cid, lines, ss[0])
        for kind in ("xray", "proc"):
            its = [(s, it) for s in ss for it in s.get("items", []) if it["kind"] == kind]
            dl = [ln for ln in mine if ln["section"] == kind]
            if not its and not dl:
                continue
            p_sum = sum(it["expect_p"] for _s, it in its)
            d_sum = sum(ln["amount_p"] for ln in dl)
            if p_sum == d_sum:
                continue
            if not dl:                                   # nothing billed: each parchi line is wanted money
                for s, it in its:
                    if it["expect_p"] <= 0:
                        continue
                    want.append(dict(amount=it["expect_p"], tick=s.get("paid_mode") or "", section=kind, cid=cid, name=name,
                                     slip=s, item=it, key="add:%d" % it["id"],
                                     what_en="%s %s" % (SEC_EN[kind], _item_word(it)), what_hi="%s %s" % (SEC_HI[kind], _item_word(it))))
                continue
            if not its:                                  # Docterz billed, no parchi line
                parchi_side.append(dict(kind="parchi_missing", cid=cid, name=name, section=kind, amount=d_sum,
                                        key="pmiss:%s:%s" % (cid, kind), slip=ss[0]))
                continue
            dup = _duplicate(its, p_sum - d_sum)
            if dup is not None:
                parchi_side.append(dict(kind="dup_item", cid=cid, name=name, section=kind, amount=p_sum - d_sum, slip=dup[0],
                                        items=dup[1], key="pdup:%s" % "-".join(str(i["id"]) for i in dup[1])))
            elif p_sum > d_sum:                          # the parchi has more than Docterz: money the register may hold
                s0, it0 = its[0]
                want.append(dict(amount=p_sum - d_sum, tick=s0.get("paid_mode") or "", section=kind, cid=cid, name=name,
                                 slip=s0, item=None, key="part:%s:%s" % (cid, kind), partial=(p_sum, d_sum),
                                 what_en="%s (parchi %s, Docterz %s)" % (SEC_EN[kind], rs(p_sum), rs(d_sum)),
                                 what_hi="%s (parchi %s, Docterz %s)" % (SEC_HI[kind], rs(p_sum), rs(d_sum))))
            else:                                        # Docterz has more than the parchi
                parchi_side.append(dict(kind="parchi_short", cid=cid, name=name, section=kind, amount=d_sum - p_sum,
                                        slip=its[0][0], key="pshort:%s:%s" % (cid, kind), sums=(p_sum, d_sum)))
    # Docterz X-ray / procedure lines whose patient has no X-ray/Proc parchi at all
    for ln in paid_lines:
        if ln["section"] in ("xray", "proc") and ln["amount_p"] > 0 and ln["cid"] not in xp_by:
            k = "pmiss:%s:%s" % (ln["cid"], ln["section"])
            if not any(p["key"] == k for p in parchi_side):
                parchi_side.append(dict(kind="parchi_missing", cid=ln["cid"], name=ln["patient"], section=ln["section"],
                                        amount=sum(x["amount_p"] for x in by_cid.get(ln["cid"], []) if x["section"] == ln["section"]),
                                        key=k, slip=None))
    # OPD: a consultation billed with no OPD parchi; an OPD parchi with nothing in Docterz; the same ID twice
    opd_ids = {}
    for s in opd:
        if s.get("no_id_name") or not s.get("clinic_id"):
            cards.append(_card("hand", "noid:%d" % s["id"], 0, d,
                               en="OPD parchi %d has no clinic ID (%s) — match it by hand" % (s["slip_no"], s.get("no_id_name") or "—"),
                               hi="OPD parchi %d par clinic ID nahi (%s) — haath se milayein" % (s["slip_no"], s.get("no_id_name") or "—")))
            continue
        if s.get("cancel"):
            continue
        opd_ids.setdefault(s["clinic_id"], []).append(s)
    orphan_cons = [ln for ln in paid_lines if ln["section"] == "consult" and ln["amount_p"] > 0 and ln["cid"] not in opd_ids]
    dups = [(cid, ss) for cid, ss in opd_ids.items() if len(ss) > 1]
    paired = set()
    if len(dups) == 1 and len(orphan_cons) == 1:         # one ID written twice and one billed patient with no parchi:
        cid, ss = dups[0]                                # the second parchi is almost certainly that patient's
        ln = orphan_cons[0]
        parchi_side.append(dict(kind="opd_wrong_id", cid=cid, name=_name(con, cid, lines), slip=ss[-1], to_cid=ln["cid"],
                                to_name=ln["patient"], amount=ln["amount_p"], key="pid:%d" % ss[-1]["id"]))
        paired.add(ln["cid"])
    else:
        for cid, ss in dups:
            parchi_side.append(dict(kind="opd_dup", cid=cid, name=_name(con, cid, lines), slip=ss[-1], amount=0,
                                    key="podup:%d" % ss[-1]["id"]))
    for ln in orphan_cons:
        if ln["cid"] in paired:
            continue
        parchi_side.append(dict(kind="opd_missing", cid=ln["cid"], name=ln["patient"], amount=ln["amount_p"],
                                key="pomiss:%s" % ln["cid"], slip=None))
    try:
        fee = _SL().usual_fee(con, d) if _SL() is not None else 0
    except Exception:                                    # noqa: BLE001
        fee = 0
    for cid, ss in opd_ids.items():
        if not by_cid.get(cid):                          # the patient is nowhere in Docterz -- not even free
            s = ss[0]
            want.append(dict(amount=fee or 0, tick="", section="consult", cid=cid, name=_name(con, cid, lines, s), slip=s,
                             item=None, key="addopd:%d" % s["id"], opd=True,
                             what_en="consultation (OPD parchi %d)" % s["slip_no"], what_hi="consultation (OPD parchi %d)" % s["slip_no"]))

    # --- 2 · the money: wanted lines are placed while the register holds room for them (the referee)
    room = sum(delta.values())
    want.sort(key=lambda w: (0 if w["tick"] else 1, -w["amount"]))
    for w in want:
        if w["amount"] > 0 and room >= w["amount"]:
            t = w["tick"] if w["tick"] in TENDERS else max(TENDERS, key=lambda x: delta[x])
            delta[t] -= w["amount"]
            sdelta[(w["section"], t)] = sdelta.get((w["section"], t), 0) - w["amount"]
            room -= w["amount"]
            cards.append(_card("missing", w["key"], w["amount"], d, who="docterz", tender=t, cid=w["cid"], name=w["name"],
                               slip=w["slip"], item=w["item"], section=w["section"],
                               en="%s — Docterz entry missing · %s · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_en"], T_EN[t]),
                               hi="%s — Docterz mein entry nahi · %s · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_hi"], T_HI[t])))
        elif w.get("partial"):
            # register = Docterz != parchi, and Docterz has the line: the parchi carries too much
            ps, ds = w["partial"]
            parchi_side.append(dict(kind="parchi_over", cid=w["cid"], name=w["name"], section=w["section"], amount=ps - ds,
                                    slip=w["slip"], key="pover:%s:%s" % (w["cid"], w["section"]), sums=(ps, ds)))
        else:
            # register = Docterz != parchi: not billed and not collected -- free, not paid, or not done
            cards.append(_card("notbilled", w["key"], w["amount"], d, who="docterz", cid=w["cid"], name=w["name"],
                               slip=w["slip"], item=w["item"], section=w["section"],
                               en="%s on the parchi — not billed, not in the register · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_en"]),
                               hi="%s parchi par — na bill hua, na register mein · %s · %s" % (rs(w["amount"]), _who_en(w["name"], w["cid"]), w["what_hi"])))

    # --- 3 · payment modes: money in one tender of Docterz that the register holds in another
    bank_left = list(bank_amts)
    for un in units:
        if un["tender"] == "upi" and not un["wallet"] and un["amount_p"] in bank_left:
            bank_left.remove(un["amount_p"])
    tick_of = {}
    for s in xp:
        if s.get("clinic_id") and s.get("paid_mode"):
            tick_of[s["clinic_id"]] = s["paid_mode"]

    def tick_for(un):
        return tick_of.get(un["cid"], "") if un["section"] in ("xray", "proc") else ""

    moved = set()
    for _guard in range(12):
        neg = [t for t in TENDERS if delta[t] < 0]
        pos = [t for t in TENDERS if delta[t] > 0]
        if not neg or not pos:
            break
        found = []                                   # (score, (unit indexes), a, b)
        for a in neg:
            for b in pos:
                lim = min(-delta[a], delta[b])
                cand = [i for i, un in enumerate(units) if i not in moved and un["tender"] == a and 0 < un["amount_p"] <= lim
                        and tick_for(un) != a]       # a line the room saw paid that way never moves
                for i in cand:
                    un = units[i]
                    if un["amount_p"] == lim or tick_for(un) == b:
                        found.append((_score(un, a, b, lim, delta, sdelta, tick_for(un), bank_left), (i,), a, b))
                if not any(f[2] == a and f[3] == b and units[f[1][0]]["amount_p"] == lim for f in found):
                    for combo in _combos(cand, units, lim):  # two or three lines that come to it exactly
                        sc = sum(_score(units[i], a, b, lim, delta, sdelta, tick_for(units[i]), bank_left) for i in combo) / len(combo)
                        found.append((sc - 1, combo, a, b))
        if not found:
            break
        found.sort(key=lambda x: -x[0])
        top = [x for x in found if x[0] == found[0][0]]
        shapes = {(x[2], x[3], tuple(sorted(units[i]["amount_p"] for i in x[1]))) for x in top}
        if len(top) > 1 and len(shapes) == 1:        # several patients fit equally: name them, decide nothing
            sc, ix, a, b = top[0]
            amt = sum(units[i]["amount_p"] for i in ix)
            who_ = sorted({i for x in top for i in x[1]})
            names = ", ".join(_who_en(units[i]["patient"], units[i]["cid"]) for i in who_[:8]) + ((" and %d more" % (len(who_) - 8)) if len(who_) > 8 else "")
            cards.append(_card("hand", "modeany:%s:%s:%d" % (a, b, amt), amt, d,
                               en="%s paid by %s is written as %s in Docterz — %d line%s among: %s. Check by hand" % (
                                   rs(amt), T_EN[b], T_EN[a], len(ix), "" if len(ix) == 1 else "s", names),
                               hi="%s %s mein aaya, Docterz mein %s likha — inme se %d: %s. Haath se dekhein" % (
                                   rs(amt), T_HI[b], T_HI[a], len(ix), names)))
            delta[a] += amt
            delta[b] -= amt
            moved.update(who_)
            continue
        sc, ix, a, b = top[0]
        for i in ix:
            un = units[i]
            moved.add(i)
            delta[a] += un["amount_p"]
            delta[b] -= un["amount_p"]
            sdelta[(un["section"], a)] = sdelta.get((un["section"], a), 0) + un["amount_p"]
            sdelta[(un["section"], b)] = sdelta.get((un["section"], b), 0) - un["amount_p"]
            if b == "upi" and un["amount_p"] in bank_left:
                bank_left.remove(un["amount_p"])
            cards.append(_card("mode", "mode:%s:%s:%d:%s:%s" % (un["cid"], un["section"], un["amount_p"], a, b), un["amount_p"], d,
                               who="docterz", cid=un["cid"], name=un["patient"], section=un["section"], tender=b,
                               en="Payment mode wrong · %s · %s %s · Docterz %s, paid by %s" % (
                                   _who_en(un["patient"], un["cid"]), SEC_EN[un["section"]], rs(un["amount_p"]), un["mode"], T_EN[b]),
                               hi="Payment mode galat · %s · %s %s · Docterz mein %s, asal mein %s" % (
                                   _who_en(un["patient"], un["cid"]), SEC_HI[un["section"]], rs(un["amount_p"]), un["mode"], T_HI[b])))

    # --- 4 · what is left
    # money one tender of the register holds that another tender of Docterz has, with no patient to move: by hand
    for a in TENDERS:
        for b in TENDERS:
            if delta[a] < 0 < delta[b]:
                m = min(-delta[a], delta[b])
                ticked = [un for un in units if un["tender"] == a and tick_for(un) == a and un["amount_p"] <= m]
                why_en = (" (the room ticked %s for %s)" % (T_EN[a], ", ".join(_who_en(u_["patient"], u_["cid"]) for u_ in ticked[:4]))) if ticked else ""
                why_hi = (" (room ne %s tick kiya: %s)" % (T_HI[a], ", ".join(_who_en(u_["patient"], u_["cid"]) for u_ in ticked[:4]))) if ticked else ""
                cards.append(_card("hand", "swap:%s:%s:%d" % (a, b, m), m, d,
                                   en="%s is %s in the register and %s in Docterz — check by hand%s" % (rs(m), T_EN[b], T_EN[a], why_en),
                                   hi="%s register mein %s, Docterz mein %s — haath se dekhein%s" % (rs(m), T_HI[b], T_HI[a], why_hi)))
                delta[a] += m
                delta[b] -= m
    r_upi = reg_t["upi"] - other_upi
    for t in TENDERS:
        if delta[t] > 0:
            secs = sorted(((v, s) for (s, tt), v in sdelta.items() if tt == t and v > 0), reverse=True)
            sec = secs[0][1] if secs else "consult"
            if t == "upi" and bank_known and bank is not None and bank == r_upi - delta[t]:
                # Docterz and the bank agree; the register alone holds it: the register was most likely written wrong
                cards.append(_card("hand", "regupi:%d" % delta[t], delta[t], d,
                                   en="The register's UPI is %s more than Docterz and the bank — the register is most likely wrong" % rs(delta[t]),
                                   hi="Register ka UPI Docterz aur bank se %s zyada — register shayad galat" % rs(delta[t])))
                continue
            cards.append(_card("notfound", "nf:%s:%s:%d" % (t, sec, delta[t]), delta[t], d, who="docterz", tender=t, section=sec,
                               en="%s — Docterz entry missing, patient not found · %s · %s" % (rs(delta[t]), SEC_EN[sec], T_EN[t]),
                               hi="%s — Docterz mein entry nahi, mareez nahi mila · %s · %s" % (rs(delta[t]), SEC_HI[sec], T_HI[t])))
        elif delta[t] < 0:
            cards.append(_card("hand", "over:%s:%d" % (t, -delta[t]), -delta[t], d,
                               en="Docterz has %s more %s than the register — check by hand" % (rs(-delta[t]), T_EN[t]),
                               hi="Docterz mein register se %s zyada %s — haath se dekhein" % (rs(-delta[t]), T_HI[t])))
    if bank_known and bank is not None and r_upi != bank and not any(c["key"].startswith("regupi:") for c in cards):
        cards.append(_card("hand", "bank:%d:%d" % (r_upi, bank), abs(r_upi - bank), d,
                           en="Bank UPI %s, register UPI %s — %s apart; check by hand" % (rs(bank), rs(r_upi), rs(abs(r_upi - bank))),
                           hi="Bank UPI %s, register UPI %s — %s ka fark; haath se dekhein" % (rs(bank), rs(r_upi), rs(abs(r_upi - bank)))))

    # --- 5 · the parchi lines (the register sides with Docterz)
    for p in parchi_side:
        cards.append(_parchi_card(p, d))

    ticks = _ticks(con, d)
    exported = _export_at(con, d)                        # S640 (D776 stage 3): when Docterz's file for the day last came in
    for c in cards:
        t = ticks.get(c["key"])
        c["tick"], c["not_fixed"] = t, None
        if t and exported and str(t["at"]) < str(exported):
            c["tick"], c["not_fixed"] = None, t          # the export after the tick still shows the line: back to staff
    dcs = [c for c in cards if c["who"] == "docterz"]
    out["reexport"] = bool(dcs) and all(c["tick"] for c in dcs) and any(c["tick"]["act"] in ("added", "changed", "found") for c in dcs)
    out["notright"] = sum(1 for c in dcs if c["tick"] and c["tick"]["act"] == "notright")
    out["not_fixed"] = sum(1 for c in cards if c.get("not_fixed"))
    out["state"] = "checked"
    out["cards"] = cards
    out["counts"] = _counts(cards)
    out["totals"] = dict(reg=reg_t, doc=doc_t, bank=bank, other_upi=other_upi)
    return out


def _score(un, a, b, lim, delta, sdelta, tick, bank_left):
    sc = 0
    if un["amount_p"] == lim:
        sc += 4
    if un["amount_p"] == -delta[a]:
        sc += 2
    if sdelta.get((un["section"], a), 0) < 0 and sdelta.get((un["section"], b), 0) > 0:
        sc += 2
    if tick == b:
        sc += 3
    elif not tick and un["section"] in ("xray", "proc"):
        sc += 1
    if b == "upi" and un["amount_p"] in bank_left and not un["wallet"]:
        sc += 2
    if un.get("wallet") and b != "upi":
        sc += 2                                          # a Wallet the bank cannot have, and the register holds elsewhere
    return sc


def _combos(cand, units, lim, most=3, cap=400):
    """Sets of two or three candidate lines whose money is exactly lim (at most cap sets)."""
    out = []
    n = len(cand)
    for x in range(n):
        for y in range(x + 1, n):
            s2 = units[cand[x]]["amount_p"] + units[cand[y]]["amount_p"]
            if s2 == lim:
                out.append((cand[x], cand[y]))
            elif most >= 3 and s2 < lim:
                for z in range(y + 1, n):
                    if s2 + units[cand[z]]["amount_p"] == lim:
                        out.append((cand[x], cand[y], cand[z]))
                        if len(out) >= cap:
                            return out
            if len(out) >= cap:
                return out
    return out


def _duplicate(its, extra):
    """(slip, [items]) when X-ray / procedure lines are written twice for one patient and the repeats come to exactly the
    extra money (one line twice, or two lines twice -- 14-Oct, ILI knee and ILI shoulder)."""
    seen, rep = set(), []
    for s, it in its:
        k = ((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())
        if k in seen:
            rep.append((s, it))
        seen.add(k)
    if not rep or extra <= 0:
        return None
    for s, it in rep:
        if it["expect_p"] == extra:
            return s, [it]
    if sum(it["expect_p"] for _s, it in rep) == extra:
        return rep[0][0], [it for _s, it in rep]
    return None


def _who_en(name, cid):
    if name and cid:
        return "%s (%s)" % (name, cid)
    return name or (cid and "ID %s" % cid) or "—"


def _card(kind, key, amount, d, who="hand", en="", hi="", **kw):
    c = dict(kind=kind, key=key, amount=int(amount or 0), day=d, who=who, en=en, hi=hi)
    c.update(kw)
    return c


def _parchi_card(p, d):
    k = p["kind"]
    s = p.get("slip")
    no = s["slip_no"] if s else None
    nm = _who_en(p.get("name"), p.get("cid"))
    if k == "parchi_missing":
        en = "No X-ray/Proc parchi · %s · %s %s in Docterz" % (nm, SEC_EN[p["section"]], rs(p["amount"]))
        hi = "X-ray/Proc parchi nahi · %s · Docterz mein %s %s" % (nm, SEC_HI[p["section"]], rs(p["amount"]))
    elif k == "opd_missing":
        en = "No OPD parchi · %s · consultation %s in Docterz" % (nm, rs(p["amount"]))
        hi = "OPD parchi nahi · %s · Docterz mein consultation %s" % (nm, rs(p["amount"]))
    elif k == "dup_item":
        w = " + ".join(_item_word(i) for i in p["items"])
        en = "Parchi %d · %s · %s written twice (%s extra)" % (no, nm, w, rs(p["amount"]))
        hi = "Parchi %d · %s · %s do baar likha (%s zyada)" % (no, nm, w, rs(p["amount"]))
    elif k == "parchi_over":
        ps, ds = p["sums"]
        en = "Parchi %d · %s · %s: parchi %s, Docterz and the register %s" % (no, nm, SEC_EN[p["section"]], rs(ps), rs(ds))
        hi = "Parchi %d · %s · %s: parchi %s, Docterz aur register %s" % (no, nm, SEC_HI[p["section"]], rs(ps), rs(ds))
    elif k == "opd_dup":
        en = "OPD parchi %d · ID %s written twice" % (no, p["cid"])
        hi = "OPD parchi %d · ID %s do baar likha" % (no, p["cid"])
    elif k == "opd_wrong_id":
        en = "OPD parchi %d · ID %s written twice; %s has a bill and no parchi — this parchi is most likely theirs" % (
            no, p["cid"], _who_en(p.get("to_name"), p.get("to_cid")))
        hi = "OPD parchi %d · ID %s do baar likha; %s ka bill hai, parchi nahi — yeh parchi shayad unki hai" % (
            no, p["cid"], _who_en(p.get("to_name"), p.get("to_cid")))
    else:                                                # parchi_short
        ps, ds = p["sums"]
        en = "Parchi %d · %s · %s: parchi %s, Docterz %s" % (no, nm, SEC_EN[p["section"]], rs(ps), rs(ds))
        hi = "Parchi %d · %s · %s: parchi %s, Docterz %s" % (no, nm, SEC_HI[p["section"]], rs(ps), rs(ds))
    return _card("parchi", p["key"], 0, d, who="parchi", en=en, hi=hi, pkind=k, slip=s, items=p.get("items"),
                 cid=p.get("cid"), to_cid=p.get("to_cid"), section=p.get("section"))


def _counts(cards):
    c = dict(missing_p=0, missing_n=0, notfound_p=0, modes=0, parchi=0, notbilled=0, notbilled_p=0, hand=0)
    for x in cards:
        if x["kind"] == "missing":
            c["missing_p"] += x["amount"]
            c["missing_n"] += 1
        elif x["kind"] == "notfound":
            c["missing_p"] += x["amount"]
            c["notfound_p"] += x["amount"]
        elif x["kind"] == "mode":
            c["modes"] += 1
        elif x["kind"] == "parchi":
            c["parchi"] += 1
        elif x["kind"] == "notbilled":
            c["notbilled"] += 1
            c["notbilled_p"] += x["amount"]
        elif x["kind"] == "hand":
            c["hand"] += 1
    return c


def summary_en(chk):
    """His line: counts only, every kind named, empty parts left out, 'all correct' on a clean day (D776, rule 42)."""
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
    else:
        if c["missing_p"]:
            parts.append("%s Docterz entry missing" % rs(c["missing_p"]))
        if c["modes"]:
            parts.append("%d payment mode%s wrong" % (c["modes"], "" if c["modes"] == 1 else "s"))
        if c["notbilled"]:
            parts.append("%s on parchis not billed or collected" % rs(c["notbilled_p"]))
    if c["parchi"]:
        parts.append("%d parchi to fix" % c["parchi"] if c["parchi"] == 1 else "%d parchis to fix" % c["parchi"])
    if c["hand"]:
        parts.append("%d to check by hand" % c["hand"])
    if chk.get("not_fixed"):
        parts.append("%d not fixed after the re-export" % chk["not_fixed"])
    return "%s: %s" % (d, " · ".join(parts) if parts else "all correct")


def summary_hi(chk):
    d = dm(chk["day"])
    if chk.get("state") == "no_docterz":
        return "%s: Docterz export abhi nahi aaya" % d
    if chk.get("state") == "no_register":
        return "%s: register abhi nahi bhara" % d
    c = chk["counts"]
    parts = []
    if c["missing_p"]:
        parts.append("%s Docterz mein entry nahi" % rs(c["missing_p"]))
    if c["modes"]:
        parts.append("%d payment mode galat" % c["modes"])
    if c["notbilled"]:
        parts.append("%s parchi par, bill nahi" % rs(c["notbilled_p"]))
    if c["parchi"]:
        parts.append("%d parchi theek karni" % c["parchi"])
    if c["hand"]:
        parts.append("%d haath se dekhni" % c["hand"])
    return "%s: %s" % (d, " · ".join(parts) if parts else "sab sahi")


def is_clean(chk):
    return chk.get("state") == "checked" and not chk["cards"]


# ---------------------------------------------------------------- ticks
def _ticks(con, d):
    out = {}
    for r in con.execute("SELECT * FROM day_check_tick WHERE day=? AND state='live' ORDER BY id", (d,)):
        out[r["key"]] = dict(r)
    return out


def add_tick(con, d, key, act, who, reason="", pick=""):
    ensure(con)
    now = _stamp()
    con.execute("UPDATE day_check_tick SET state='undone' WHERE day=? AND key=? AND state='live'", (d, key))
    cur = con.execute("INSERT INTO day_check_tick (day, key, act, reason, pick, who, at) VALUES (?,?,?,?,?,?,?)",
                      (d, key, act, reason[:40], pick[:40], who, now))
    _audit_safe(con, "day_check_tick", cur.lastrowid, "tick_" + act, None, {"day": d, "key": key, "reason": reason, "pick": pick}, who)
    con.commit()
    return cur.lastrowid


def undo_tick(con, d, key, who):
    ensure(con)
    con.execute("UPDATE day_check_tick SET state='undone' WHERE day=? AND key=? AND state='live'", (d, key))
    _audit_safe(con, "day_check_tick", 0, "tick_undo", None, {"day": d, "key": key}, who)
    con.commit()


def _audit_safe(con, table, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)     # finance_app.audit dumps them itself
    except Exception:                                    # noqa: BLE001 -- the audit never blocks the work
        pass


# ---------------------------------------------------------------- who may do what
def _user(u):
    return ((u or {}).get("user") or "").lower()


def _roles(u):
    return set((u or {}).get("roles") or [])


def _gate():
    """(u, english, err): the register's people (unit clinic) or the parchi's (unit slips); a checker reads English."""
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        u2, err2 = _require("maker", "checker", unit=SLIP_UNIT)
        if err2:
            return None, True, err
        u, err = u2, None
    return u, ("checker" in _roles(u)), None


def can_docterz(u):
    return _user(u) in DOCTERZ_USERS or "checker" in _roles(u)


def can_parchi(u):
    return _user(u) in PARCHI_USERS or "checker" in _roles(u)


# ---------------------------------------------------------------- the page
def cards_html(con, chk, u, english, msg=""):
    """The one-line cards with their buttons. Used on the check page and under the register's three records."""
    d = chk["day"]
    out = []
    if msg:
        out.append(msg)
    head = summary_en(chk) if english else summary_hi(chk)
    cls = "all_agree" if is_clean(chk) else ("waiting_bank" if chk.get("state") != "checked" else "docterz_differs")
    out.append("<p class='verdict %s'>%s</p>" % (cls, _esc(head)))
    if chk.get("state") != "checked":
        out.append("<p class='mut'>%s</p>" % ("The check runs as soon as both the register and the Docterz export of this day are in."
                                              if english else "Register aur Docterz export dono aate hi yeh jaanch apne aap chalti hai."))
        return "".join(out)
    groups = (("docterz", "Docterz — Shivani, Alisha, Shavez", "Docterz — Shivani, Alisha, Shavez"),
              ("parchi", "Parchi — Shavez", "Parchi — Shavez"),
              ("hand", "Check by hand", "Haath se dekhein"))
    for g, en, hi in groups:
        cs = [c for c in chk["cards"] if c["who"] == g]
        if not cs:
            continue
        out.append("<h3 class='grp'>%s</h3>" % _esc(en if english else hi))
        for c in cs:
            out.append(_one_card(con, c, u, english, d))
    for en, hi in chk.get("notes", []):
        out.append("<p class='mut'>%s</p>" % _esc(en if english else hi))
    out.append("<p class='mut'>%s</p>" % (
        "A tick is kept as a note; a line goes away only when the next Docterz export or the parchi shows the change."
        if english else "Tick sirf yaad ke liye hai; line tabhi hategi jab agla Docterz export ya parchi badlav dikhaye."))
    return "".join(out)


def _btn(d, key, act, label, cls="", extra=""):
    return ("<form method='post' action='/finance/clinic/check/%s/act' class='inline'>"
            "<input type='hidden' name='key' value='%s'><input type='hidden' name='act' value='%s'>%s"
            "<button type='submit' class='tb %s'>%s</button></form>" % (d, _esc(key), act, extra, cls, _esc(label)))


def _one_card(con, c, u, english, d):
    txt = c["en"] if english else c["hi"]
    t = c.get("tick")
    btns = []
    status = ""
    if t:
        who = (t["who"] or "").title()
        word = {"added": ("Added", "Add kar diya"), "changed": ("Changed", "Badal diya"), "notright": ("Not right", "Sahi nahi"),
                "found": ("Found", "Mil gaya"), "regmistake": ("Register mistake", "Register ki galti")}.get(t["act"], (t["act"], t["act"]))
        extra = ""
        if t["act"] == "notright" and t["reason"]:
            extra = " — " + (NOT_RIGHT_EN if english else NOT_RIGHT_HI).get(t["reason"], t["reason"])
        if t["act"] == "found" and t["pick"]:
            extra = " — ID %s" % t["pick"]
        status = "<span class='tk'>✓ %s%s · %s %s · %s</span>" % (
            _esc(word[0] if english else word[1]), _esc(extra), _esc(who), _esc((t["at"] or "")[11:16]),
            "waits for the Docterz export" if english and c["who"] == "docterz" else
            ("Docterz export ka intezaar" if c["who"] == "docterz" else ("waits for the parchi" if english else "parchi ka intezaar")))
        if _user(u) == (t["who"] or "").lower() or "checker" in _roles(u):
            btns.append(_btn(d, c["key"], "undo", "Undo" if english else "Wapas", "x"))
    elif c["who"] == "docterz" and can_docterz(u):
        if c.get("not_fixed"):                           # S640: ticked, re-exported, still there
            nf = c["not_fixed"]
            status = "<span class='tk' style='color:#9c2a20'>%s</span>" % _esc(
                ("Not fixed — the Docterz export after %s's tick (%s) still shows it" if english else
                 "Theek nahi hua — %s ke tick (%s) ke baad ke Docterz export mein bhi hai") % ((nf["who"] or "").title(), (nf["at"] or "")[5:16]))
        if c["kind"] in ("missing", "notbilled"):
            btns.append(_btn(d, c["key"], "added", "Added" if english else "Add kar diya"))
            if c.get("slip") is not None and _SA() is not None:
                btns.append(_btn(d, c["key"], "notpaid", "Not paid" if english else "Paise nahi liye", "x",
                                 "<input type='hidden' name='slip' value='%d'>" % c["slip"]["id"]))
                if c.get("item") is not None and c["item"]["kind"] in ("xray", "proc"):
                    sa = _SA()
                    sel = "".join("<option value='%s'>%s</option>" % (k, _esc(e if english else h)) for k, h, e in sa.REASONS)
                    btns.append(_btn(d, c["key"], "free", "Free", "x",
                                     "<input type='hidden' name='slip' value='%d'><input type='hidden' name='item' value='%d'>"
                                     "<select name='reason' class='rs'>%s</select>" % (c["slip"]["id"], c["item"]["id"], sel)))
        elif c["kind"] == "mode":
            btns.append(_btn(d, c["key"], "changed", "Changed" if english else "Badal diya"))
            sel = "".join("<option value='%s'>%s</option>" % (k, _esc(e if english else h)) for k, h, e in NOT_RIGHT)
            btns.append(_btn(d, c["key"], "notright", "Not right" if english else "Sahi nahi", "x",
                             "<select name='reason' class='rs'>%s</select>" % sel))
        elif c["kind"] == "notfound":
            opts = _day_people(con, d)
            sel = "".join("<option value='%s'>%s</option>" % (_esc(cid), _esc("%s (%s)" % (nm, cid))) for cid, nm in opts)
            btns.append(_btn(d, c["key"], "found", "Found it" if english else "Mil gaya", "",
                             "<select name='pick' class='rs'>%s</select>" % sel))
            btns.append("<a class='tb x' href='/finance/clinic/register/%s'>%s</a>" % (d, "Register mistake" if english else "Register ki galti"))
    elif c["who"] == "parchi" and can_parchi(u):
        s = c.get("slip")
        late_ok = _late_ok(d)
        if c.get("pkind") == "dup_item":
            btns.append(_btn(d, c["key"], "dupitem", "Remove duplicate" if english else "Duplicate hatao"))
        elif c.get("pkind") == "opd_wrong_id":
            btns.append(_btn(d, c["key"], "fixid", ("Make it ID %s" if english else "ID %s karein") % c["to_cid"], "",
                             "<input type='hidden' name='slip' value='%d'><input type='hidden' name='to' value='%s'>"
                             % (s["id"], _esc(c["to_cid"]))))
            btns.append(_btn(d, c["key"], "dupslip", "Remove duplicate" if english else "Duplicate hatao", "x",
                             "<input type='hidden' name='slip' value='%d'>" % s["id"]))
        elif c.get("pkind") == "opd_dup":
            btns.append(_btn(d, c["key"], "dupslip", "Remove duplicate" if english else "Duplicate hatao", "",
                             "<input type='hidden' name='slip' value='%d'>" % s["id"]))
        elif c.get("pkind") in ("opd_missing", "parchi_missing"):
            if late_ok:
                series = "opd" if c.get("pkind") == "opd_missing" else "xp"
                btns.append("<a class='tb' href='/finance/slips?s=%s&day=%s'>%s</a>" % (series, d, "Fix" if english else "Theek karein"))
        elif c.get("pkind") in ("parchi_short", "parchi_over") and s is not None and late_ok:
            btns.append(_btn(d, c["key"], "rewrite", "Fix" if english else "Theek karein", "",
                             "<input type='hidden' name='slip' value='%d'>" % s["id"]))
        if not late_ok and c.get("pkind") in ("opd_missing", "parchi_missing", "parchi_short", "parchi_over", "dup_item", "opd_dup", "opd_wrong_id"):
            status = "<span class='mut'>%s</span>" % ("older than 7 days — the parchi can no longer be changed"
                                                      if english else "7 din se purani — parchi ab nahi badal sakti")
    return "<div class='cline'><span class='ct'>%s</span>%s<span class='cb'>%s</span></div>" % (_esc(txt), status, "".join(btns))


def _export_at(con, d):
    try:
        r = con.execute("SELECT taken_at FROM clinic_day_revenue WHERE business_date=?", (d,)).fetchone()
        return (r[0] or "") if r else ""
    except Exception:                                    # noqa: BLE001
        return ""


STAFF_DAYS = 7                                           # the staff see a week of days: the parchi's own late window


def staff_lines(con, u):
    """S640 (D776 stage 3): what one login has to correct, the day before today back STAFF_DAYS days (never before the lists'
    floor): the Docterz lines for Shivani, Alisha, Shavez; the parchi lines for Shavez and Bhati. A line ticked and waiting for
    the re-export is not theirs to do; a line the re-export did not fix is, again. {open, text, days} -- text names them."""
    who = _user(u)
    want = set()
    if who in DOCTERZ_USERS:
        want.add("docterz")
    if who in PARCHI_USERS:
        want.add("parchi")
    if not want:
        return dict(open=0, text="", days=[])
    floor = "2026-10-01"
    try:
        import aaj_floor                                 # noqa: PLC0415 -- the lists' own floor, when it says one
        floor = aaj_floor.floor_for(con, _require, u) or floor
    except Exception:                                    # noqa: BLE001
        pass
    today = dt.date.today()
    n, bits, days = 0, [], []
    for i in range(1, STAFF_DAYS + 1):
        d = (today - dt.timedelta(days=i)).isoformat()
        if d < str(floor):
            break
        chk = check_day(con, d)
        if chk.get("state") != "checked":
            continue
        mine = [c for c in chk["cards"] if c["who"] in want and not c.get("tick")]
        if not mine:
            continue
        days.append(d)
        n += len(mine)
        bits.append("%s: %s" % (dm(d), " | ".join(("Phir se — " if c.get("not_fixed") else "") + c["hi"] for c in mine)))
    text = ""
    if n:
        text = "Din ki galtiyan (%d) — %s" % (n, " ;  ".join(bits))
        if len(text) > 600:
            text = text[:590].rsplit(" ", 1)[0] + " …"
    return dict(open=n, text=text, days=days)


@bp.route("/finance/clinic/check/api/mine")
def api_mine():
    u, english, err = _gate()
    if err:
        return err
    con = _db()
    _CR()._ensure(con)
    ensure(con)
    from flask import jsonify                            # noqa: PLC0415
    return jsonify(ok=True, **staff_lines(con, u))


@bp.route("/finance/clinic/check/mine")
def mine():
    """The page a staff line opens: the oldest day that still has lines for this login (else yesterday)."""
    u, english, err = _gate()
    if err:
        return redirect("/finance/clinic/register", code=302)
    con = _db()
    _CR()._ensure(con)
    ensure(con)
    s = staff_lines(con, u)
    d = s["days"][-1] if s["days"] else (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/check/%s#check" % d, code=302)


def _late_ok(d):
    SL = _SL()
    if SL is None:
        return False
    try:
        return SL._late_day(d) == d
    except Exception:                                    # noqa: BLE001
        return False


def _day_people(con, d):
    seen, out = set(), []
    for r in con.execute("SELECT clinic_id, patient FROM clinic_day_line WHERE business_date=? ORDER BY section, sn", (d,)):
        cid = str(r["clinic_id"] or "")
        if cid and cid not in seen:
            seen.add(cid)
            out.append((cid, (r["patient"] or "").strip()))
    return out


@bp.route("/finance/clinic/check/<date>")
def page(date):
    u, english, err = _gate()
    CR = _CR()
    if err:
        return CR._shell("Day check", CR._denied())
    if not _iso_ok(date):
        return CR._shell("Day check", "<div class='card'><h2>Not a date.</h2></div>")
    con = _db()
    CR._ensure(con)
    ensure(con)
    chk = check_day(con, date)
    msg = ""
    if request.args.get("ok"):
        msg = "<div class='ok'>%s</div>" % _esc(request.args.get("ok"))
    if request.args.get("err"):
        msg = "<div class='bad'>%s</div>" % _esc(request.args.get("err"))
    t = CR.three_way(con, date)
    body = (CR._compare_html(t, date).replace("<details class=\"card\">", "<details class=\"card\" open>", 1)
            + "<div class='card' id='check'><h2>%s</h2>%s</div>" % (
                ("The day's corrections — %s" if english else "Din ki galtiyan — %s") % dm(date), cards_html(con, chk, u, english, msg))
            + "<p class='navrow noprint'><a class='btn' href='/finance/clinic/register/%s'>%s</a>"
              "<a class='btn' href='/finance/clinic/register/list'>%s</a></p>" % (
                date, "the register of this day" if english else "is din ka register", "all days" if english else "sab din")
            + STYLE)
    return CR._shell(("Day check — %s" if english else "Din ki jaanch — %s") % dm(date), body)


@bp.route("/finance/clinic/check/<date>/act", methods=["POST"])
def act(date):
    u, english, err = _gate()
    if err or not _iso_ok(date):
        return redirect("/finance/clinic/register", code=303)
    con = _db()
    ensure(con)
    f = request.form
    key, a, who = (f.get("key") or "")[:120], f.get("act") or "", _user(u)
    back = "/finance/clinic/check/%s" % date

    def done(ok="", er=""):
        q = ("?ok=" + _q(ok)) if ok else (("?err=" + _q(er)) if er else "")
        return redirect(back + q + "#check", code=303)

    chk = check_day(con, date)
    card = next((c for c in chk["cards"] if c["key"] == key), None)
    if a == "undo":
        undo_tick(con, date, key, who)
        return done("Undone." if english else "Wapas le liya.")
    if card is None:
        return done(er="This line has already changed — the page is fresh now." if english else "Yeh line badal chuki hai — page naya hai.")
    try:
        if a in ("added", "changed", "notright", "found") and card["who"] == "docterz" and can_docterz(u):
            reason = f.get("reason") or ""
            if a == "notright" and reason not in NOT_RIGHT_EN:
                reason = "other"
            add_tick(con, date, key, a, who, reason=reason, pick=(f.get("pick") or "")[:12])
            return done("Noted. The line goes when the Docterz export shows it." if english
                        else "Likh liya. Docterz export mein dikhte hi line hat jayegi.")
        if a in ("notpaid", "free") and card["who"] == "docterz" and can_docterz(u):
            sa = _SA()
            sid = int(f.get("slip") or 0)
            if a == "free":
                sa.add_discount(con, who, sid, int(f.get("item") or 0), None, True, f.get("reason") or "other", note="day check")
            else:
                sa.add_cancel(con, who, sid, (card.get("cid") or ""), "never_taken", note="day check")
            return done("Sent for approval." if english else "Manzoori ke liye gaya.")
        if card["who"] == "parchi" and can_parchi(u):
            if a == "dupitem":
                return done(*_remove_items(con, card, who, english))
            if a == "dupslip":
                return done(*_void_slip(con, card, int(f.get("slip") or 0), who, english, "duplicate (day check)"))
            if a == "fixid":
                return done(*_fix_id(con, card, int(f.get("slip") or 0), f.get("to") or "", who, english))
            if a == "rewrite":
                ok, er = _void_slip(con, card, int(f.get("slip") or 0), who, english, "written again (day check)")
                if er:
                    return done(er=er)
                s = card["slip"]
                return redirect("/finance/slips?s=xp&day=%s&no=%d" % (date, s["slip_no"]), code=303)
    except Exception as ex:                              # noqa: BLE001 -- slip_adjust's own refusals read as they are
        return done(er=str(ex)[:200])
    return done(er="Not permitted." if english else "Aapke liye nahi.")


def _q(s):
    from urllib.parse import quote                       # noqa: PLC0415
    return quote(str(s), safe="")


def _remove_items(con, card, who, english):
    """Remove the repeated line(s) the check found -- exactly those rows, each audited whole."""
    its = card.get("items") or []
    if not its or not _late_ok(card["day"]):
        return "", ("Not this line." if english else "Yeh line nahi.")
    n = 0
    for it in its:
        row = con.execute("SELECT * FROM slip_item WHERE id=?", (it["id"],)).fetchone()
        if row is None:
            continue
        con.execute("DELETE FROM slip_item WHERE id=?", (it["id"],))
        con.execute("UPDATE slip SET updated_by=?, updated_at=? WHERE id=?", (who, _stamp(), row["slip_id"]))
        _audit_safe(con, "slip_item", it["id"], "slip_item_removed_duplicate", dict(row), None, who)
        n += 1
    con.commit()
    if not n:
        return "", ("Already removed." if english else "Pehle hi hat chuki.")
    return ("Duplicate removed." if english else "Duplicate hata diya."), ""


def _void_slip(con, card, slip_id, who, english, why):
    s = card.get("slip")
    if s is None or s["id"] != slip_id:
        return "", ("Not this parchi." if english else "Yeh parchi nahi.")
    if not _late_ok(card["day"]):
        return "", ("Older than 7 days." if english else "7 din se purani.")
    row = con.execute("SELECT * FROM slip WHERE id=? AND state='ok'", (slip_id,)).fetchone()
    if row is None:
        return "", ("Already changed." if english else "Pehle hi badal chuki.")
    con.execute("UPDATE slip SET state='void', note=?, updated_by=?, updated_at=? WHERE id=?", (why, who, _stamp(), slip_id))
    _audit_safe(con, "slip", slip_id, "slip_void", {"state": "ok"}, {"state": "void", "why": why}, who)
    con.commit()
    return ("Parchi %d taken off." % row["slip_no"] if english else "Parchi %d hata di." % row["slip_no"]), ""


def _fix_id(con, card, slip_id, to, who, english):
    s = card.get("slip")
    to = "".join(ch for ch in str(to) if ch.isalnum())[:12]
    if s is None or s["id"] != slip_id or not to or to != str(card.get("to_cid") or ""):
        return "", ("Not this parchi." if english else "Yeh parchi nahi.")
    row = con.execute("SELECT * FROM slip WHERE id=? AND state='ok'", (slip_id,)).fetchone()
    if row is None:
        return "", ("Already changed." if english else "Pehle hi badal chuki.")
    con.execute("UPDATE slip SET clinic_id=?, name_seen='', updated_by=?, updated_at=? WHERE id=?", (to, who, _stamp(), slip_id))
    _audit_safe(con, "slip", slip_id, "slip_id_fixed", {"clinic_id": row["clinic_id"]}, {"clinic_id": to, "via": "day check"}, who)
    con.commit()
    return ("Parchi %d now carries ID %s." % (row["slip_no"], to) if english else "Parchi %d par ab ID %s." % (row["slip_no"], to)), ""


STYLE = """<style>
h3.grp{font-size:18px;margin:16px 0 6px;color:var(--accent)}
.cline{border:2px solid var(--line);border-radius:9px;padding:10px 12px;margin:0 0 10px;background:#fff}
.cline .ct{display:block;font-size:18px;line-height:1.45;overflow-wrap:anywhere}
.cline .tk{display:block;color:#2c6e2f;font-size:16px;margin-top:4px}
.cline .cb{display:block;margin-top:6px}
.cline form.inline{display:inline-block;margin:6px 8px 0 0}
button.tb,a.tb{display:inline-block;background:var(--accent);color:#fff;border:0;border-radius:9px;padding:11px 16px;
 font-size:17px;font-weight:600;cursor:pointer;text-decoration:none;min-height:48px}
button.tb.x,a.tb.x{background:var(--paper);color:var(--accent);border:2px solid var(--accent)}
select.rs{display:block;width:100%;font-size:18px;min-height:50px;padding:6px;border:2px solid #5b6b76;border-radius:8px;
 margin:0 0 6px;background:#fff;color:var(--ink)}
.cline form.inline:has(select){display:block;margin-right:0}
.cline a.tb{margin:10px 8px 0 0}
@media (max-width:620px){button.tb,a.tb{padding:11px 12px}}
</style>"""
