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

VERSION = "1.1"
KIT = "S436_STAFF_PAGES_CLEAN"                                 # v1.0 was S404_ORTHO_STOCK_CLOSE
# v1.1 (S436, D638, 28-Sep-2026) -- the owner: "for the orthotics found less than Marg he writes 'does not know' -- it should be
# 'sold without bill'; 'went out never came back' is irrelevant -- remove; 'broken or damaged' is not part of this flow -- remove;
# only the left option stays; then we compute the orthotic loss for the deficient items."
#   * Kam kyun? offers ONE answer a side: a short line "Galti se bill nahi bana" (BILLING), an extra line "Bill bana, diya nahi"
#     (BILLED_NOT_GIVEN). The other cause values stay in the vocabulary for old rows (REASON_HI / REASON_EN still name them).
#   * close_by_rule(): when no orthotic line is open without a reason, the section closes by itself -- every short line is an
#     ORTHOTIC LOSS at selling price (stock_statement's price rule), recorded as ONE stock_writeoff_run of kind 'ortho_close' with
#     the groups ortho_loss (the short lines) and ortho_fix (the extra lines: book corrections), the lines get their lane word
#     (WRITE_OFF / MARG_FIX, "rule D638"), the orthotic voucher round is made without a tap, one Needs-you line goes to the owner,
#     a stock_section_close row is written with basis 'rule D638'. Orthotics never merge into the medicine figures (the leakage,
#     the cadence and the staff block's first three lines read allowance / small / big only).
#   * a line the seed answered BY DEFAULT ("default -- Darpan ne nahi likha") stays tappable for Darpan after the close.
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

# S436 (D638): ONE answer a side -> stock_diff.cause. A short orthotic line is sold without a bill; an extra one was billed and
# not handed over. The S404 values NOT_RETURNED / DONT_KNOW (and stock_app's BREAKAGE) stay in the vocabulary for old rows and
# for the medicines' own chips; they are no longer offered on an orthotic line. A line answered by the rule's default carries
# the note DEFAULT_NOTE and stays tappable for Darpan.
SHORT_REASONS = (("BILLING", "Galti se bill nahi bana", "sold, no bill was made"),)
OVER_REASONS = (("BILLED_NOT_GIVEN", "Bill bana, diya nahi", "billed, not handed over"),)
_OLD_REASONS = (("BREAKAGE", "Toota / kharab", "broken or damaged"), ("NOT_RETURNED", "Vaapas nahi aaya", "went out, never came back"),
                ("DONT_KNOW", "Pata nahi", "does not know"))
REASON_HI = {k: h for k, h, _e in SHORT_REASONS + OVER_REASONS + _OLD_REASONS}
REASON_EN = {k: e for k, _h, e in SHORT_REASONS + OVER_REASONS + _OLD_REASONS}
RULE_WHO = "rule D638, 28-Sep"
DEFAULT_NOTE = "rule D638 default -- Darpan ne nahi likha"
LOSS_GROUP = "ortho_loss"
FIX_GROUP = "ortho_fix"
RUN_KIND = "ortho_close"
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


def ortho_run(con, root):
    """S436: the section's close-by-rule run (kind ortho_close) -- (run dict, {item: loss row}) or (None, {})."""
    try:
        r = con.execute("SELECT id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, round_no FROM stock_writeoff_run "
                        "WHERE count_id=? AND kind=? ORDER BY id DESC LIMIT 1", (int(root), RUN_KIND)).fetchone()
    except sqlite3.Error:
        return None, {}
    if not r:
        return None, {}
    g = json.loads(r[7])
    by = {}
    for grp in (LOSS_GROUP, FIX_GROUP):
        for x in g.get(grp, []):
            by[x["item"]] = dict(x, group=grp)
    run = dict(id=r[0], at=r[1], at_text=_stamp(r[1]), by=r[2] or "", lines=r[3], mrp_p=r[4], cost_p=r[5], unpriced=r[6],
               round_no=r[8], n_short=len(g.get(LOSS_GROUP, [])), n_fix=len(g.get(FIX_GROUP, [])), groups=g)
    return run, by


def lines_of(con, d):
    """Every ORTHOTIC difference line of the round, with what stands on it."""
    sa = _sa()
    rows = _diff_rows(con, _family(con, d["count_id"]))
    _run, loss_by = ortho_run(con, d["count_id"])
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
        defaulted = reasoned and str(st.get("cause_note") or "").startswith(DEFAULT_NOTE)   # S436: answered by the rule, not by Darpan
        lr = loss_by.get(x["item"])
        out.append(dict(item=x["item"], packing=x.get("packing") or "", pack=int(x.get("pack") or 1),
                        marg=int(x["marg"]), counted=int(x["counted"]), diff=d0, rem=rem,
                        rem_text=(("%s kam" % sa._qw(-rem, x.get("pack"))) if rem < 0 else (("%s zyada" % sa._qw(rem, x.get("pack"))) if rem > 0 else "barabar")),
                        swapped=int(x.get("swapped") or 0), swap_with=list(x.get("swap_with") or []),
                        diff_id=st.get("id"), status=status, cause=cause,
                        cause_hi=REASON_HI.get(cause, sa.CAUSE_LABEL.get(cause, cause)) if reasoned else "",
                        cause_en=REASON_EN.get(cause, sa.CAUSE_LABEL.get(cause, cause)) if reasoned else "",
                        cause_by=st.get("cause_by") or "", cause_at=st.get("cause_at") or "",
                        cause_at_text=_stamp(st.get("cause_at")), defaulted=bool(defaulted),
                        word=(w.get("label") or "") if owner_word else "", word_action=(w.get("action") or "") if owner_word else "",
                        word_by=(w.get("by") or "") if owner_word else "",
                        open=open_, answered=bool(settled or reasoned), settled=bool(settled), reasoned=bool(reasoned),
                        side=side, reasons=[dict(key=k, hi=h, en=e) for k, h, e in (SHORT_REASONS if side == "short" else OVER_REASONS)],
                        rule_closed=bool(lr), loss=(dict(group=lr["group"], mrp_p=lr.get("mrp_p"), short_text=lr.get("short_text") or "",
                                                          price_text=lr.get("price_text") or "", why=lr.get("why") or "") if lr else None),
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
    # S436 (D638): the section CLOSES BY RULE the moment the orthotic loss is computed (close_by_rule); Amir's vouchers, the proof
    # and the renames are follow-ups shown under it, they no longer keep the section open
    run, _by = ortho_run(con, root)
    loss = None
    if run:
        loss = dict(run_id=run["id"], at=run["at"], at_text=run["at_text"], n_short=run["n_short"], n_fix=run["n_fix"], mrp_p=run["mrp_p"],
                    unpriced=run["unpriced"], round_no=run["round_no"], rs=sa._loss_rs(run["mrp_p"]),
                    text="%d line%s short, %s at selling price%s%s" % (run["n_short"], "" if run["n_short"] == 1 else "s", sa._loss_rs(run["mrp_p"]),
                                                                     (" (%d without a price)" % run["unpriced"]) if run["unpriced"] else "",
                                                                     ("; the round %d on Amir's board" % run["round_no"]) if run["round_no"] else ""),
                    text_hi="%d line kam, %s (bina bill)" % (run["n_short"], sa._loss_rs(run["mrp_p"])))
        if not stored:
            stored = (run["at"], "rule D638")
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
    if run:                                                    # S436: closed by rule -- the loss is the verdict; the rest are follow-ups
        left = "; ".join(c["en"] for c in conds if not c["ok"])
        ven = "Orthotics section: CLOSED by rule on %s -- %s%s" % (_dmy(closed_at[:10]), loss["text"], (" · still to follow: " + left) if left else "")
        vhi = "Orthotics: BAND ho gaya — %s (%s)%s" % (_dmy(closed_at[:10]), loss["text_hi"], (" · baaki: " + "; ".join(c["hi"] for c in conds if not c["ok"])) if left else "")
    elif closed_now:
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
               conds=conds, closed=bool(closed_now or run), closed_by_rule=bool(run), loss=loss, closed_at=closed_at,
               was_closed=bool(stored and not closed_now and not run),
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


# ------------------------------------------------------------------ S436 (D638): the orthotic loss, computed; the round made by rule
def _lp():
    import loss_piles                                         # noqa: PLC0415 -- beside this file
    return loss_piles


def _ss():
    import stock_statement                                    # noqa: PLC0415 -- beside this file: the selling-price rule (S431)
    return stock_statement


def close_by_rule(con, d, who=RULE_WHO, force=False):
    """When no orthotic line is open without a reason: every short line = ORTHOTIC LOSS at selling price (stock_statement's rule --
    the spine's S.RATE as on the count day, else MRP, else the 0.30 rule, else the rate / margin; none -> unpriced), every extra
    line a book correction. Writes: the lane word on each line (WRITE_OFF / MARG_FIX, the rule named, status closed), ONE
    stock_writeoff_run of kind 'ortho_close' (groups ortho_loss / ortho_fix), the orthotic voucher round (S404's maker, <= the
    voucher batch a voucher), one Needs-you line, a stock_section_close row (basis 'rule D638'), an audit line.
    Idempotent: a second call finds the run and returns it. Returns the outcome dict, or None when a line is still unanswered."""
    sa, lp = _sa(), _lp()
    root = d["count_id"]
    ensure_schema(con)
    lp.ensure(con)                                            # the run table (a no-op once it exists)
    run, _by = ortho_run(con, root)
    if run:
        return dict(run, already=True)
    lines = lines_of(con, d)
    open_lines = [l for l in lines if l["open"]]
    if not open_lines:
        return None
    if not force and any(not l["reasoned"] for l in open_lines):
        return None
    ss = _ss()
    as_on = sa._dmy_to_iso(d.get("as_on") or "") or ""
    st = sa._stock_settings(con)
    P = ss.Prices(as_on)
    rates = {r[0]: int(r[1]) for r in con.execute("SELECT item, rate_p FROM stock_rate") if r[1]}
    ts = now_iso()
    loss_rows, fix_rows = [], []
    for l in open_lines:
        item, pack, packing = l["item"], int(l["pack"] or 1), l["packing"]
        if l["side"] == "short":
            units = -int(l["rem"])
            price, src = ss.price_for(con, item, pack, SECTION, st, P, rates)
            mrp = (price * units) if price else None
            try:
                cost = sa._value_p(con, item, -units)
                cost = (-int(cost)) if cost is not None and int(cost) < 0 else (int(cost) if cost is not None else None)
            except Exception:                                  # noqa: BLE001
                cost = None
            note = "%s: orthotic loss -- sold without bill (Darpan: %s)" % (RULE_WHO, l["cause_en"] or "-")
            lp._word(con, root, item, "WRITE_OFF", note, who, ts, close=True)
            loss_rows.append(dict(item=item, short_units=units, short_text=lp.qw(units, pack, packing, item), short_hi=lp.qw(units, pack, packing, item, "hi"),
                                  pack=pack, packing=packing, mrp_p=mrp, cost_p=cost, price_p=price, price_src=src,
                                  price_text=(("%s a pc" % sa._loss_rs(price)) if price else "no price"),
                                  why="orthotic loss -- sold without bill; Darpan: %s%s" % (l["cause_en"] or "-", " (by default)" if l["defaulted"] else "")))
        else:
            units = int(l["rem"])
            note = "%s: book correction -- billed, not handed over (Darpan: %s)" % (RULE_WHO, l["cause_en"] or "-")
            did = lp._word(con, root, item, "MARG_FIX", note, who, ts, close=True)
            if did:                                            # MARG_FIX is not a decision: the lane word alone leaves the status open -- close it here
                con.execute("UPDATE stock_diff SET status='closed', closed_at=? WHERE id=?", (ts, did))
            fix_rows.append(dict(item=item, short_units=0, over_units=units, short_text="", short_hi="", over_text=lp.qw(units, pack, packing, item),
                                 pack=pack, packing=packing, mrp_p=0, cost_p=0, price_p=None, price_src=None, price_text="",
                                 why="book correction -- billed, not handed over%s; Darpan: %s" % (" (Marg below zero)" if int(l["marg"]) < 0 else "", l["cause_en"] or "-")))
    groups = {LOSS_GROUP: loss_rows, FIX_GROUP: fix_rows}
    mrp = sum((x["mrp_p"] or 0) for x in loss_rows)
    cost = sum((x["cost_p"] or 0) for x in loss_rows)
    unpriced = sum(1 for x in loss_rows if x["mrp_p"] is None)
    frozen = json.dumps(groups, sort_keys=True, separators=(",", ":"))
    import hashlib                                            # noqa: PLC0415
    cur = con.execute("INSERT INTO stock_writeoff_run (count_id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, md5, kind) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (root, ts, who, len(loss_rows) + len(fix_rows), mrp, cost, unpriced, frozen,
                       json.dumps(dict(kit=KIT, rule="D638", price_rule="selling price: the spine's S.RATE as on the count day, else MRP, else the 0.30 rule, else the rate / margin"), sort_keys=True),
                       hashlib.md5(frozen.encode("utf-8")).hexdigest(), RUN_KIND))
    run_id = int(cur.lastrowid)
    if not con.execute("SELECT 1 FROM stock_section_close WHERE count_id=? AND section=?", (root, SECTION)).fetchone():
        con.execute("INSERT INTO stock_section_close (count_id, section, closed_at, basis) VALUES (?,?,?,?)",
                    (root, SECTION, ts, json.dumps(dict(rule="D638", run=run_id, short=len(loss_rows), fix=len(fix_rows), mrp_p=mrp, unpriced=unpriced))))
    lp._audit(con, root, "ortho_close", dict(run=run_id, short=len(loss_rows), fix=len(fix_rows), mrp_p=mrp, unpriced=unpriced,
                                             text="orthotics closed by rule: %d line%s short, %s at selling price%s; %d book correction%s" % (
                                                 len(loss_rows), "" if len(loss_rows) == 1 else "s", sa._loss_rs(mrp), (" (%d without a price)" % unpriced) if unpriced else "",
                                                 len(fix_rows), "" if len(fix_rows) == 1 else "s")), who)
    con.commit()
    d2 = report(con, root)
    rno, n = make_round(con, d2, dict(user=who))
    if rno:
        con.execute("UPDATE stock_writeoff_run SET round_no=? WHERE id=?", (rno, run_id))
        lp._audit(con, root, "vouchers", dict(round_no=rno, lines=n, orthotic=True, text="the orthotic round %d made by rule: %d lines" % (rno, n)), who)
        con.commit()
    try:
        _sw().notice(con, "ortho_closed", "owner", "Orthotics closed: %d line%s short, %s at selling price%s%s" % (
            len(loss_rows), "" if len(loss_rows) == 1 else "s", sa._loss_rs(mrp), (" (%d without a price)" % unpriced) if unpriced else "",
            ("; round %d of %d line%s on Amir's board" % (rno, n, "" if n == 1 else "s")) if rno else "; no voucher line was needed"),
            days=14, once_key="ortho_closed:%d" % root)
        con.commit()
    except Exception:                                          # noqa: BLE001 -- the run is the record; the line is a courtesy
        pass
    run, _by = ortho_run(con, root)
    return dict(run or {}, already=False, made_round=rno, made_lines=n)


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
        l["locked"] = (kind != "owner") and (bool(l["word"]) or (l["reasoned"] and not mine_recent)) and not l["defaulted"]   # S436: a defaulted line stays tappable
        l["mine"] = l["cause_by"] == me
    for p in st["pairs"]:
        p["mine"] = p["answered_by"] == me
        if kind == "owner":
            p["locked"] = False
    st.update(me=kind, user=me)
    st.update(_s418_extra(con, d["count_id"]))                # S418: Phir se gino + Bina bill? (medicines too)
    st["watch"] = _sw_view(con)                                # S428: Aaj ki ginti, the plan question, the loss lines, the traces
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
    if st["progress"]["all"] and st["progress"]["need"] and not st.get("closed_by_rule"):
        try:                                                  # S436: all answered -> the section closes by rule (the loss, the round)
            R = close_by_rule(con, d, (u or {}).get("user") or RULE_WHO)
            if R and not R.get("already"):
                made = dict(round_no=R.get("made_round"), lines=R.get("made_lines") or 0, loss=R.get("mrp_p"), n_short=R.get("n_short"))
                d = report(con, root)
                st = _state_for(con, d, u, kind)
        except Exception as e:                                # noqa: BLE001 -- the answer is saved; the close can be made on the hub
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
    if not l["open"] and not l["defaulted"] and kind != "owner":   # S436: a defaulted line stays tappable after the close; the owner may re-word any line
        return jsonify(ok=False, error="not_open", message="Is line par ab kuch poochna nahi hai."), 409
    prev = con.execute("SELECT cause, cause_by, cause_at, cause_note FROM stock_diff WHERE id=?", (did,)).fetchone()
    p_cause, p_by, p_at = (prev[0] or "UNEXPLAINED"), (prev[1] or ""), (prev[2] or "")
    if p_cause == reason and p_by == who and _within(p_at):
        st = _state_for(con, d, u, kind)
        st.update(already=True, message="Pehle hi likha hai — dobara nahi likha.", round_made=None,
                  saved=dict(kind="reason", item=l["item"], reason=reason, hi=REASON_HI[reason], at=_stamp(p_at), already=True))
        return jsonify(**st)
    if kind != "owner":
        if l["word"] and not l["defaulted"]:
            return jsonify(ok=False, error="locked", message="Doctor sahab ka faisla is line par ho chuka hai."), 409
        if p_cause not in ("UNEXPLAINED", "") and not (p_by == who and _within(p_at)) and not l["defaulted"]:
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



# ------------------------------------------------------------------ S418 (D631): the recount box and the pursue answers
def _lp():
    import loss_piles                                         # noqa: PLC0415 -- beside this file
    return loss_piles


def _s418_extra(con, root):
    """'Phir se gino' (the items the owner asked to be counted again -- blind: no Marg figure, no first count) and
    'Bina bill?' (the live claims of the round, the claim queue's own answers). Never raises."""
    out = dict(recounts=[], claims=[], claim_answers=[], block=None)
    try:
        out["recounts"] = _lp().recounts_by(con, root)        # S427: his own recounts (Dobara ginna hai), newest first
        out["block"] = _lp().block_view(con, root)            # S427: THE STAFF BLOCK, pinned until the next count closes
    except Exception:                                          # noqa: BLE001
        pass
    try:
        sa = _sa()
        if getattr(sa, "CLAIM_QUEUE_OK", False):
            cq = sa._cq
            out["claims"] = [dict(id=c["id"], item=c["item"], state=c["state"], answer=c["answer"], answer_hi=c["answer_label"],
                                  short_qty=c["short_qty"], value_p=c["value_p"])
                             for c in cq.lines(con, root, limit=200) if c["state"] != "settled"]
            out["claim_answers"] = [dict(key=k, hi=v) for k, v in cq.ANSWERS.items()]
    except Exception:                                          # noqa: BLE001
        pass
    return out


@bp.route("/finance/stockmatch/api/recount", methods=["POST"])
def api_recount():
    """Phir se gino: {item, strips, loose} or {item, units}. His figure replaces the shelf; the owner's desk re-piles."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = root_of(con, _cid())
    item = str(b.get("item") or "").strip()
    info = _lp().round_item(con, root, item)                   # S427: ANY item of the round -- Dobara ginna hai
    if not info:
        return jsonify(ok=False, error="not_found", message="Yeh item is ginti mein nahi hai."), 404
    try:
        whole = b.get("pcs") if b.get("pcs") not in (None, "") else b.get("units")
        if whole not in (None, ""):
            q = int(float(whole))
        else:
            q = int(float(b.get("strips") or 0)) * int(info["pack"] or 1) + int(float(b.get("loose") or 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request", message="Ginti likhiye."), 400
    ok, msg, code = _lp().recount_any(con, root, item, q, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    d = report(con, root)
    st = _state_for(con, d, u, kind)
    st.update(saved=dict(kind="recount", item=item, qty=q, message=msg), round_made=None)
    return jsonify(**st)


@bp.route("/finance/stockmatch/api/claim", methods=["POST"])
def api_claim():
    """Bina bill?: {id, answer} -- the claim queue's own answer door (open -> contacted), audited. The owner settles."""
    u, con, kind, err = _auth()
    if err:
        return err
    sa = _sa()
    if not getattr(sa, "CLAIM_QUEUE_OK", False):
        return jsonify(ok=False, error="unavailable", message="Claim queue nahi mili."), 503
    b = request.get_json(silent=True) or {}
    try:
        cid_ = int(b.get("id") or 0)
    except (TypeError, ValueError):
        cid_ = 0
    ans = str(b.get("answer") or "").strip()
    root = root_of(con, _cid())
    mine = {c["id"]: c for c in _s418_extra(con, root)["claims"]}
    if cid_ not in mine:
        return jsonify(ok=False, error="not_found", message="Yeh line ab poochne ki list mein nahi hai."), 404
    ok, msg = sa._cq.answer(con, cid_, ans, "", (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="bad_request", message=msg), 400
    at = now_iso()
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("claim_line", cid_, "claim_answered", json.dumps(dict(answer=mine[cid_]["answer"])),
                     json.dumps(dict(answer=ans, item=mine[cid_]["item"], via="stockmatch")), (u or {}).get("user") or "", at))
    except sqlite3.Error:
        pass
    con.commit()
    d = report(con, root)
    st = _state_for(con, d, u, kind)
    st.update(saved=dict(kind="claim", item=mine[cid_]["item"], answer=ans, hi=sa._cq.ANSWERS.get(ans, ans)), round_made=None)
    return jsonify(**st)



# ------------------------------------------------------------------ S427 (D632): Dobara ginna hai, the staff block's note
@bp.route("/finance/stockmatch/api/items")
def api_items():
    """Darpan's search box: the items of this round whose name carries every word typed (12 at most)."""
    u, con, kind, err = _auth()
    if err:
        return err
    root = root_of(con, _cid())
    q = str(request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify(ok=True, items=[])
    return jsonify(ok=True, items=_lp().items_search(con, root, q, 12))


@bp.route("/finance/stockmatch/api/note", methods=["POST"])
def api_note():
    """'Kuchh batana hai?' -- one free line under the pinned staff block, stored, shown on the owner's record card."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    root = root_of(con, _cid())
    ok, msg, code = _lp().add_note(con, root, b.get("text"), (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    d = report(con, root)
    st = _state_for(con, d, u, kind)
    st.update(saved=dict(kind="note", message=msg), round_made=None)
    return jsonify(**st)



# ------------------------------------------------------------------ S428 (D633): Aaj ki ginti, Stock batao, Kuchh gadbad hai, the plan
def _sw():
    import stock_watch                                        # noqa: PLC0415 -- beside this file
    return stock_watch


def _sw_view(con):
    try:
        return _sw().darpan_view(con)
    except Exception:                                          # noqa: BLE001
        return None


def _qty_from(b, pack):
    """{strips, loose} or {pcs} -> tablets / pieces; None when nothing was typed."""
    whole = b.get("pcs") if b.get("pcs") not in (None, "") else b.get("units")
    if whole not in (None, ""):
        return int(float(whole))
    if b.get("strips") in (None, "") and b.get("loose") in (None, ""):
        return None
    return int(float(b.get("strips") or 0)) * int(pack or 1) + int(float(b.get("loose") or 0))


def _sw_state(con, u, kind, saved):
    root = root_of(con, _cid())
    d = report(con, root)
    st = _state_for(con, d, u, kind) if d else dict(ok=True)
    st.update(saved=saved, round_made=None)
    return jsonify(**st)


@bp.route("/finance/stockmatch/api/spot", methods=["POST"])
def api_spot():
    """Aaj ki ginti -- one item of the day's roster: {roster_id, strips, loose} or {roster_id, pcs}."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        rid = int(b.get("roster_id") or 0)
    except (TypeError, ValueError):
        rid = 0
    r = con.execute("SELECT pack FROM stock_spot_roster WHERE id=?", (rid,)).fetchone() if rid else None
    if not r:
        return jsonify(ok=False, error="not_found", message="Yeh item aaj ki list mein nahi hai."), 404
    try:
        q = _qty_from(b, r[0])
    except (TypeError, ValueError):
        q = None
    if q is None or q < 0 or q > 100000:
        return jsonify(ok=False, error="bad_request", message="Ginti likhiye."), 400
    ok, msg, code, P = _sw().answer_roster(con, rid, q, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="spot", message=msg, point=P))


@bp.route("/finance/stockmatch/api/watch-items")
def api_watch_items():
    """Stock batao / Kuchh gadbad hai: any item of the shop (the spine's names) carrying the words typed."""
    u, con, kind, err = _auth()
    if err:
        return err
    q = str(request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify(ok=True, items=[])
    sw = _sw()
    sp = sw.Spine()
    out = []
    for it in sp.search(q, 12):
        pack = sw.pack_of(it["packing"])
        out.append(dict(item=it["name"], pack=pack, packing=it["packing"] or "", whole=sw._qwm().whole_word(it["packing"] or "", None, it["name"], pack, "hi")))
    return jsonify(ok=True, items=out)


@bp.route("/finance/stockmatch/api/stock", methods=["POST"])
def api_stock_batao():
    """Stock batao -- any item, any day: {item, strips, loose} or {item, pcs} -> a darpan point."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    item = str(b.get("item") or "").strip()
    sw = _sw()
    info = sw.item_info(con, sw.Spine(), item)
    try:
        q = _qty_from(b, info["pack"])
    except (TypeError, ValueError):
        q = None
    if not item or q is None or q < 0 or q > 100000:
        return jsonify(ok=False, error="bad_request", message="Item aur ginti likhiye."), 400
    ok, msg, code, P = sw.darpan_point(con, item, q, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="stock", message=msg, point=P))


@bp.route("/finance/stockmatch/api/gadbad", methods=["POST"])
def api_gadbad():
    """Kuchh gadbad hai -- {item, text, strips?, loose? | pcs?} -> a loss point when counted, and THE TRACE."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    item = str(b.get("item") or "").strip()
    text = str(b.get("text") or "").strip()
    if not item or not text:
        return jsonify(ok=False, error="bad_request", message="Item aur kya gadbad hai, dono likhiye."), 400
    sw = _sw()
    info = sw.item_info(con, sw.Spine(), item)
    try:
        q = _qty_from(b, info["pack"])
    except (TypeError, ValueError):
        q = None
    ok, msg, code, R = sw.gadbad(con, item, text, (u or {}).get("user") or "", qty_units=q)
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="gadbad", message=msg, trace=(R or {}).get("trace"), point=(R or {}).get("point")))


@bp.route("/finance/stockmatch/api/plan", methods=["POST"])
def api_plan():
    """The count's Sunday: {answer: ok | no} -- 'Theek hai' confirms, 'Nahi ho payega' sends it back to Amir."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg, code = _sw().plan_answer(con, str(b.get("answer") or "").strip().lower(), (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="plan", message=msg))


@bp.route("/finance/stockmatch/api/trace/<int:tid>/seen", methods=["POST"])
def api_trace_seen(tid):
    """'Dekh liya' on a trace."""
    u, con, kind, err = _auth()
    if err:
        return err
    ok, msg, code = _sw().trace_seen(con, tid, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="trace_seen", message=msg))
