#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  stockmatch.py  ·  v1.0  ·  kit S404_ORTHO_STOCK_CLOSE  ·  Session 283 (Sanjeevni)  ·  D619 / D620
#
#  DARPAN'S "STOCK MILAAN" -- the owner, 26-Sep-2026: "I want to close the stock check for the orthotic
#  section first. For that, I need Darpan to have an interactive tool where he can do the matches and
#  whatever you have made on my page. So he gets to do it either on his mobile or on his PC."
#  Taps, practically no typing.  Hindi (Roman script), phone-first.  Orthotics only, round 1 only.
#
#  WHAT THIS FILE IS
#    * Darpan's page   GET  /finance/stockmatch                    (stockmatch.html)
#    * its API         GET  /finance/stockmatch/api/state          the two cards, the progress, the section verdict
#                      POST /finance/stockmatch/api/pair   {short, over, answer YES|NO}
#                                       card 1 "Adla-badli?" -- lands through THE SAME DOOR the owner's Yes lands
#                                       (stock_app.match_answer -> stock_match, by_user = darpan)
#                      POST /finance/stockmatch/api/reason {diff_id, reason}
#                                       card 2 "Kam kyun?" -- stock_diff.cause / cause_by / cause_at, audited
#    * section_state(con, d)  the orthotic section, read by the owner's hub too: every orthotic pair and
#                             line of the round, Darpan's progress, and the FOUR conditions of the verdict
#                             "Orthotics section: CLOSED on <date>" -- all lines answered (the owner's word
#                             where a line still moves Marg) · the orthotic round made and entered · the
#                             proof green for those lines · every orthotic rename verified in Marg.
#
#  ACCESS: its own server unit 'stockmatch' (unit_role): darpan is its maker, the owner its checker,
#  nobody else.  A maker answers only what has no answer yet (a pair the owner answered is greyed and
#  read-only to him; a reason he gave stands after ten minutes -- the owner changes any on the hub).
#  A repeat tap within ten minutes writes nothing and says so (S393 lesson).
#
#  WHEN DARPAN'S PROGRESS REACHES ALL-DONE the orthotic voucher round is made by itself, restricted to
#  the orthotic lines (stock_app._voucher_make(section='Orthotics')); the owner's hub has the same button.
#  Idempotent: a second call finds nothing waiting.
# =============================================================================
import datetime as dt
import json
import os
import sqlite3
import sys

from flask import Blueprint, jsonify, request, send_file

VERSION = "1.0"
KIT = "S404_ORTHO_STOCK_CLOSE"
bp = Blueprint("stockmatch", __name__)
_db = _require = None
_unit = "medical"
ACCESS_UNIT = "stockmatch"
SECTION = "Orthotics"
REPEAT_MIN = 10
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
PAGE = os.path.join(HERE, "stockmatch.html")

# Darpan's four reasons on a shortage, two on a surplus -> stock_diff.cause. BILLING and BREAKAGE are
# stock_app's own vocabulary; NOT_RETURNED, DONT_KNOW and BILLED_NOT_GIVEN are ADDED to it by this kit
# (never an existing value changed). 'Pata nahi' is a real answer and counts as one.
SHORT_REASONS = (("BILLING", "Galti se bill nahi bana", "sold, no bill was made"),
                 ("BREAKAGE", "Toota / kharab", "broken or damaged"),
                 ("NOT_RETURNED", "Vaapas nahi aaya", "went out, never came back"),
                 ("DONT_KNOW", "Pata nahi", "does not know"))
OVER_REASONS = (("BILLED_NOT_GIVEN", "Bill bana, diya nahi", "billed, not handed over"),
                ("DONT_KNOW", "Pata nahi", "does not know"))
REASON_HI = {k: h for k, h, _e in SHORT_REASONS + OVER_REASONS}
REASON_EN = {k: e for k, _h, e in SHORT_REASONS + OVER_REASONS}
DDL = ("CREATE TABLE IF NOT EXISTS stock_section_close ("
       " count_id INTEGER NOT NULL, section TEXT NOT NULL, closed_at TEXT NOT NULL, basis TEXT,"
       " PRIMARY KEY (count_id, section))",)


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _sa():
    import stock_app                                          # noqa: PLC0415 -- beside this file; loaded by finance_app first
    return stock_app


def _ia():
    import item_alias                                         # noqa: PLC0415
    return item_alias


def ensure_schema(con):
    for ddl in DDL:
        con.execute(ddl)


def _stamp(ts):
    return (_sa()._r_stamp(ts) + " IST") if ts else ""


def _dmy(iso):
    return _sa()._r_dmy(iso)


def _within(ts, minutes=REPEAT_MIN):
    try:
        return (dt.datetime.now() - dt.datetime.fromisoformat(str(ts)[:19])) <= dt.timedelta(minutes=minutes)
    except (TypeError, ValueError):
        return False


# ------------------------------------------------------------------ what is an orthotic
def is_ortho(con, item):
    """The stored section map first (S313); the word rule only for a name the map does not know."""
    sa = _sa()
    if sa.SECTION_MAP_OK:
        try:
            r = con.execute("SELECT section FROM stock_item_section WHERE item_key=?", (sa._sm.norm_key(item),)).fetchone()
            if r:
                return str(r[0]) == SECTION
        except sqlite3.Error:
            pass
    return bool(sa._is_orthotic(item))


def root_of(con, cid=None):
    sa = _sa()
    if cid:
        return int(cid)
    return int(sa._newest_root(con) or 0)


def report(con, root):
    return _sa()._pad_report_data(con, root)


def _family(con, root):
    return [root] + [r[0] for r in con.execute("SELECT count_id FROM stock_count_part WHERE part_of=? ORDER BY count_id", (root,))]


def _diff_rows(con, fam):
    """item -> its newest stock_diff row across the family."""
    q = ",".join("?" * len(fam))
    out = {}
    for r in con.execute("SELECT id, item, status, cause, cause_by, cause_at, cause_note, count_id FROM stock_diff "
                         "WHERE count_id IN (%s) ORDER BY count_id, id" % q, tuple(fam)):
        out[r[1]] = dict(id=int(r[0]), status=r[2] or "open", cause=r[3] or "UNEXPLAINED", cause_by=r[4] or "",
                         cause_at=r[5] or "", cause_note=r[6] or "")
    return out


def lines_of(con, d):
    """Every ORTHOTIC difference line of the round, with what stands on it."""
    sa = _sa()
    rows = _diff_rows(con, _family(con, d["count_id"]))
    out = []
    for x in d["differences"]:
        if not is_ortho(con, x["item"]):
            continue
        st = rows.get(x["item"]) or {}
        rem = int(x["diff"] or 0)
        d0 = int(x.get("diff_count_day", x["diff"]) or 0)
        w = x.get("word") or {}
        owner_word = bool(w) and not w.get("swap")
        cause = st.get("cause") or "UNEXPLAINED"
        reasoned = cause not in ("UNEXPLAINED", "")
        status = st.get("status") or "open"
        open_ = status == "open" and rem != 0
        settled = (rem == 0) or status == "reconciled" or owner_word
        side = "short" if rem < 0 else "over"
        out.append(dict(item=x["item"], packing=x.get("packing") or "", pack=int(x.get("pack") or 1),
                        marg=int(x["marg"]), counted=int(x["counted"]), diff=d0, rem=rem,
                        rem_text=(("%s kam" % sa._qw(-rem, x.get("pack"))) if rem < 0 else (("%s zyada" % sa._qw(rem, x.get("pack"))) if rem > 0 else "barabar")),
                        swapped=int(x.get("swapped") or 0), swap_with=list(x.get("swap_with") or []),
                        diff_id=st.get("id"), status=status, cause=cause,
                        cause_hi=REASON_HI.get(cause, sa.CAUSE_LABEL.get(cause, cause)) if reasoned else "",
                        cause_en=REASON_EN.get(cause, sa.CAUSE_LABEL.get(cause, cause)) if reasoned else "",
                        cause_by=st.get("cause_by") or "", cause_at=st.get("cause_at") or "",
                        cause_at_text=_stamp(st.get("cause_at")),
                        word=(w.get("label") or "") if owner_word else "", word_action=(w.get("action") or "") if owner_word else "",
                        word_by=(w.get("by") or "") if owner_word else "",
                        open=open_, answered=bool(settled or reasoned), settled=bool(settled), reasoned=bool(reasoned),
                        side=side, reasons=[dict(key=k, hi=h, en=e) for k, h, e in (SHORT_REASONS if side == "short" else OVER_REASONS)],
                        family=x.get("family") or "", lane=x.get("lane") or ""))
    out.sort(key=lambda l: (not l["open"], l["answered"], l["item"]))
    return out


def pairs_of(con, d):
    """Every step-2 pair of the round whose two items are orthotics, with the answer that stands."""
    sa = _sa()
    out = []
    for p in d.get("matches") or []:
        if p.get("kind") != "ortho" or not (is_ortho(con, p["short"]) and is_ortho(con, p["over"])):
            continue
        out.append(dict(short=p["short"], over=p["over"], qty=int(p["qty"]), qty_text=sa._qw(p["qty"], p.get("short_pack")),
                        family=p.get("family") or "", close=p.get("close_text") or "",
                        answer=p.get("answer") or "", answered_by=p.get("answered_by") or "", answered_at=p.get("answered_at") or "",
                        answered_text=_stamp(p.get("answered_at")), by_words=bool(p.get("words")) and not p.get("answer"),
                        settled=bool(p.get("settled")), locked=bool(p.get("answer")) or bool(p.get("words"))))
    out.sort(key=lambda p: (p["locked"], p["family"], p["short"]))
    return out


# ------------------------------------------------------------------ the section verdict (3.4)
def section_state(con, d, for_owner=False):
    sa = _sa()
    root = d["count_id"]
    ensure_schema(con)
    lines = lines_of(con, d)
    pairs = pairs_of(con, d)
    open_lines = [l for l in lines if l["open"]]
    need = len(pairs) + len(open_lines)
    done = sum(1 for p in pairs if p["settled"]) + sum(1 for l in open_lines if l["answered"])
    all_answered = need == done
    unsettled = [l for l in open_lines if not l["settled"]]
    # 1 -- every orthotic line answered; a line that still moves Marg carries the owner's word
    c1 = all_answered and not unsettled
    # 2 -- the orthotic round made and entered
    pend = sa._voucher_pending(con, d, section=SECTION)
    vm = sa._voucher_state(con, d)
    ob = []
    for r in vm["rounds"]:
        for b in r["batches"]:
            items = [l["item"] for l in b["lines"]]
            o = [i for i in items if is_ortho(con, i)]
            if o:
                ob.append(dict(round_no=r["round_no"], kind=b["kind"], kind_text=b.get("kind_text") or b["kind"], batch_no=b["batch_no"],
                               batches_n=b.get("batches_n"), n=len(items), ortho_n=len(o), ortho_only=(len(o) == len(items)),
                               entered=bool(b.get("entered")), entered_no=((b.get("entered") or {}).get("no") or ""),
                               entered_at=((b.get("entered") or {}).get("at_text") or "")))
    not_entered = [b for b in ob if not b["entered"]]
    c2 = (not pend) and (not not_entered)
    # 3 -- the proof, for the orthotic lines (D543: the export before the first voucher, the first after the last)
    P = sa._proof_state(con, d)
    iok = P.get("items_ok") or {}
    ortho_need = sorted(i for i in iok if is_ortho(con, i))
    bad = [i for i in ortho_need if not iok[i]]
    if not ob:
        c3, proof_text = True, "nothing to prove yet -- no orthotic voucher line has been made"
    elif not P.get("as_after"):
        c3, proof_text = False, P.get("text") or ""
    else:
        c3 = bool(ortho_need) and not bad
        proof_text = ("Marg's export of %s: every orthotic vouchered item moved by exactly its voucher (%d)" % (P["as_after"], len(ortho_need)) if c3
                      else "Marg's export of %s: %d orthotic item%s did not move by its voucher" % (P["as_after"], len(bad), "" if len(bad) == 1 else "s"))
    # 4 -- every orthotic rename verified
    ia = _ia()
    rs = ia.summary(con)
    c4 = bool(rs.get("all_verified"))
    closed_now = c1 and c2 and c3 and c4
    stored = con.execute("SELECT closed_at, basis FROM stock_section_close WHERE count_id=? AND section=?", (root, SECTION)).fetchone()
    if closed_now and not stored:
        at = now_iso()
        con.execute("INSERT INTO stock_section_close (count_id, section, closed_at, basis) VALUES (?,?,?,?)",
                    (root, SECTION, at, json.dumps(dict(pairs=len(pairs), lines=len(lines), rounds=sorted({b["round_no"] for b in ob}),
                                                        proof_as_after=P.get("as_after"), renames=rs.get("verified")))))
        con.commit()
        stored = (at, None)
    closed_at = stored[0] if stored else ""
    conds = [
        dict(key="answered", ok=c1,
             en=("every orthotic line answered" if c1 else ("%d line%s still open" % (need - done, "" if need - done == 1 else "s")
                                                              if not all_answered else "%d line%s await your word" % (len(unsettled), "" if len(unsettled) == 1 else "s"))),
             hi=("sab lines ka jawab ho gaya" if c1 else ("%d line baaki" % (need - done) if not all_answered else "Doctor sahab ka faisla baaki: %d line" % len(unsettled)))),
        dict(key="vouchers", ok=c2,
             en=("orthotic round made and entered" if c2 else ("%d orthotic line%s not yet on a voucher" % (len(pend), "" if len(pend) == 1 else "s") if pend
                                                              else "%d orthotic voucher%s not yet entered in Marg" % (len(not_entered), "" if len(not_entered) == 1 else "s"))),
             hi=("Amir ke vouchers ho gaye" if c2 else ("Vouchers banane baaki: %d line" % len(pend) if pend else "Amir ke vouchers Marg mein daalne baaki: %d" % len(not_entered)))),
        dict(key="proof", ok=c3, en=("proof green for the orthotic lines" if c3 else "proof pending -- " + proof_text),
             hi=("Marg export mein sab sahi" if c3 else "Marg ke agle stock export ka intezaar")),
        dict(key="renames", ok=c4,
             en=("all %d renames seen in Marg" % rs["total"] if c4 else "%d of %d renames not yet verified (%d ticked, %d not yet seen in Marg)"
                 % (rs["total"] - rs["verified"], rs["total"], rs["done"] + rs["amber"], rs["amber"])),
             hi=("Naam badal gaye, Marg mein dikh gaye" if c4 else "Naam badalna baaki (Amir): %d" % (rs["total"] - rs["verified"]))),
    ]
    if closed_now:
        ven, vhi = "Orthotics section: CLOSED on %s" % _dmy(closed_at[:10]), "Orthotics section: BAND ho gaya — %s" % _dmy(closed_at[:10])
    elif stored:
        ven = "Orthotics section: was CLOSED on %s -- open again: %s" % (_dmy(closed_at[:10]), "; ".join(c["en"] for c in conds if not c["ok"]))
        vhi = "Orthotics section: phir khul gaya — " + "; ".join(c["hi"] for c in conds if not c["ok"])
    else:
        ven = "Orthotics section: OPEN -- " + "; ".join(c["en"] for c in conds if not c["ok"])
        vhi = "Abhi baaki: " + "; ".join(c["hi"] for c in conds if not c["ok"])
    out = dict(ok=True, kit=KIT, section=SECTION, count_id=root, day=d.get("day") or "",
               pairs=pairs, lines=lines, open_lines=len(open_lines),
               progress=dict(need=need, done=done, all=all_answered,
                             hi=("Sab ho gaya — ab Amir ke vouchers" if all_answered and need else "Orthotics: %d mein se %d ho gaye" % (need, done)),
                             en=("all %d answered" % need if all_answered else "%d of %d answered" % (done, need))),
               unsettled=[l["item"] for l in unsettled],
               conds=conds, closed=bool(closed_now), closed_at=closed_at, was_closed=bool(stored and not closed_now),
               verdict_en=ven, verdict_hi=vhi,
               vouchers=dict(pending=len(pend), pending_items=[p["item"] for p in pend], batches=ob, not_entered=len(not_entered),
                             rounds=sorted({b["round_no"] for b in ob})),
               proof=dict(state=P.get("state"), text=proof_text, as_before=P.get("as_before") or "", as_after=P.get("as_after") or "",
                          items=ortho_need, bad=bad),
               renames=rs)
    if for_owner:
        out["rename_rows"] = ia.rows(con)
    return out


def make_round(con, d, user):
    """The orthotic voucher round -- idempotent; (round_no, lines) or (None, 0)."""
    sa = _sa()
    if con.in_transaction:
        con.commit()
    return sa._voucher_make(con, d, user, section=SECTION)


# ------------------------------------------------------------------ auth
def _auth():
    u, err = _require("maker", "checker", unit=ACCESS_UNIT)
    if err:
        return None, None, None, err
    con = _db()
    ensure_schema(con)
    kind = "owner" if "checker" in (u.get("roles") or []) else "staff"
    return u, con, kind, None


def _state_for(con, d, u, kind):
    st = section_state(con, d, for_owner=(kind == "owner"))
    me = (u or {}).get("user") or ""
    for l in st["lines"]:
        mine_recent = l["reasoned"] and l["cause_by"] == me and _within(l["cause_at"])
        l["locked"] = (kind != "owner") and (bool(l["word"]) or (l["reasoned"] and not mine_recent))
        l["mine"] = l["cause_by"] == me
    for p in st["pairs"]:
        p["mine"] = p["answered_by"] == me
        if kind == "owner":
            p["locked"] = False
    st.update(me=kind, user=me)
    return st


def _cid():
    c = str(request.args.get("count") or (request.get_json(silent=True) or {}).get("count") or "").strip()
    return int(c) if c.isdigit() else None


# ------------------------------------------------------------------ routes
@bp.route("/finance/stockmatch")
def page():
    u, con, kind, err = _auth()
    if err:
        return err
    return send_file(PAGE)


@bp.route("/finance/stockmatch/api/healthz")
def api_healthz():
    u, con, kind, err = _auth()
    if err:
        return err
    return jsonify(ok=True, module="stockmatch", version=VERSION, kit=KIT)


@bp.route("/finance/stockmatch/api/state")
def api_state():
    u, con, kind, err = _auth()
    if err:
        return err
    root = root_of(con, _cid())
    d = report(con, root)
    if d is None:
        return jsonify(ok=False, error="not_found", message="Koi ginti nahi mili."), 404
    return jsonify(**_state_for(con, d, u, kind))


def _after_write(con, root, u, kind, saved):
    """Re-read the round after a write; make the orthotic round by itself when Darpan is all done."""
    d = report(con, root)
    st = _state_for(con, d, u, kind)
    made = None
    if st["progress"]["all"] and st["progress"]["need"] and st["vouchers"]["pending"]:
        try:
            rno, n = make_round(con, d, u)
            if rno:
                made = dict(round_no=rno, lines=n)
                d = report(con, root)
                st = _state_for(con, d, u, kind)
        except Exception as e:                                # noqa: BLE001 -- the answer is saved; the round can be made on the hub
            made = dict(error=str(e)[:120])
    st.update(saved=saved, round_made=made)
    return st


@bp.route("/finance/stockmatch/api/pair", methods=["POST"])
def api_pair():
    """Card 1: Haan (billed as the other size -- a swap) / Nahi. The same door as the owner's Yes."""
    u, con, kind, err = _auth()
    if err:
        return err
    sa = _sa()
    b = request.get_json(silent=True) or {}
    short, over = str(b.get("short") or "").strip(), str(b.get("over") or "").strip()
    answer = str(b.get("answer") or "").upper().strip()
    if answer in ("HAAN", "HAN"):
        answer = "YES"
    if answer in ("NAHI", "NAHIN"):
        answer = "NO"
    if kind != "owner" and answer not in ("YES", "NO"):
        return jsonify(ok=False, error="bad_request", message="Haan ya Nahi."), 400
    if answer not in ("YES", "NO", "OPEN") or not short or not over:
        return jsonify(ok=False, error="bad_request", message="short, over and YES / NO are needed."), 400
    root = root_of(con, _cid())
    d = report(con, root)
    if d is None:
        return jsonify(ok=False, error="not_found", message="Koi ginti nahi mili."), 404
    ps = [p for p in pairs_of(con, d) if p["short"] == short and p["over"] == over]
    if not ps:
        return jsonify(ok=False, error="no_such_pair", message="Yeh jodi is list mein nahi hai."), 400
    p = ps[0]
    who = (u or {}).get("user") or ""
    if kind != "owner" and p["locked"]:
        return jsonify(ok=False, error="locked", already=True,
                       message=("Doctor sahab ne is jodi ka jawab de diya hai." if p["answered_by"] and p["answered_by"] != who
                                else "Is jodi ka jawab pehle hi darj hai.")), 409
    ok, msg, code = sa.match_answer(con, d, short, over, answer, "", who)
    if not ok:
        return jsonify(ok=False, error=code, message=msg), 400
    saved = dict(kind="pair", short=short, over=over, answer=answer,
                 hi=("Haan — adla-badli" if answer == "YES" else ("Nahi — adla-badli nahi" if answer == "NO" else "Jawab wapas")),
                 at=_stamp(now_iso()))
    return jsonify(**_after_write(con, root, u, kind, saved))


@bp.route("/finance/stockmatch/api/reason", methods=["POST"])
def api_reason():
    """Card 2: one chip -> stock_diff.cause. Once; a repeat within ten minutes writes nothing; a maker's
    answer stands after ten minutes (the owner changes any); every write audited."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        did = int(b.get("diff_id") or 0)
    except (TypeError, ValueError):
        did = 0
    reason = str(b.get("reason") or "").upper().strip()
    if not did or reason not in REASON_HI:
        return jsonify(ok=False, error="bad_request", message="Ek wajah chuniye.", reasons=sorted(REASON_HI)), 400
    root = root_of(con, _cid())
    d = report(con, root)
    if d is None:
        return jsonify(ok=False, error="not_found", message="Koi ginti nahi mili."), 404
    ls = [l for l in lines_of(con, d) if l["diff_id"] == did]
    if not ls:
        return jsonify(ok=False, error="not_found", message="Yeh line orthotics ki list mein nahi hai."), 404
    l = ls[0]
    who = (u or {}).get("user") or ""
    allowed = [r["key"] for r in l["reasons"]]
    if reason not in allowed:
        return jsonify(ok=False, error="wrong_side", message="Yeh wajah is line par nahi lagti.", reasons=allowed), 400
    if not l["open"]:
        return jsonify(ok=False, error="not_open", message="Is line par ab kuch poochna nahi hai."), 409
    prev = con.execute("SELECT cause, cause_by, cause_at, cause_note FROM stock_diff WHERE id=?", (did,)).fetchone()
    p_cause, p_by, p_at = (prev[0] or "UNEXPLAINED"), (prev[1] or ""), (prev[2] or "")
    if p_cause == reason and p_by == who and _within(p_at):
        st = _state_for(con, d, u, kind)
        st.update(already=True, message="Pehle hi likha hai — dobara nahi likha.", round_made=None,
                  saved=dict(kind="reason", item=l["item"], reason=reason, hi=REASON_HI[reason], at=_stamp(p_at), already=True))
        return jsonify(**st)
    if kind != "owner":
        if l["word"]:
            return jsonify(ok=False, error="locked", message="Doctor sahab ka faisla is line par ho chuka hai."), 409
        if p_cause not in ("UNEXPLAINED", "") and not (p_by == who and _within(p_at)):
            return jsonify(ok=False, error="locked",
                           message=("Doctor sahab ne is line par likha hai." if p_by and p_by != who
                                    else "Aapka jawab darj ho chuka hai — badalna ho to doctor sahab se kahiye.")), 409
    at = now_iso()
    con.execute("UPDATE stock_diff SET cause=?, cause_note=?, cause_by=?, cause_at=? WHERE id=?",
                (reason, "S404 %s: %s" % ("darpan-page" if kind != "owner" else "hub", REASON_HI[reason]), who, at, did))
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("stock_diff", did, "cause", json.dumps(dict(cause=p_cause, by=p_by, at=p_at)),
                     json.dumps(dict(cause=reason, by=who, at=at, item=l["item"], via=("stockmatch" if kind != "owner" else "hub"))), who, at))
    except sqlite3.Error:
        pass
    con.commit()
    saved = dict(kind="reason", item=l["item"], reason=reason, hi=REASON_HI[reason], en=REASON_EN[reason], at=_stamp(at),
                 changed=(p_cause not in ("UNEXPLAINED", "")))
    return jsonify(**_after_write(con, root, u, kind, saved))
