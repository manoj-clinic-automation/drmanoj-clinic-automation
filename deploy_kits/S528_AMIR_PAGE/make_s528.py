#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s528.py -- the builder of kit S528_AMIR_PAGE (11-Oct-2026, D706 / D708 / D709; F-851 F-852 F-853 F-854).

    python3 -B make_s528.py --finance /root/finance --out DIR [--print-to]

Reads the LIVE files, refuses anything but their FROM pins, makes anchored edits (each anchor must occur exactly once, else it stops),
compiles every python result on the python that runs this script, and writes the results into --out (nothing else is written).
With --print-to the built md5s are printed and accepted (packing the kit); without it a result must equal its TO pin (PINS.sh beside).

  stock_app.py     3.1 'wrong' only inside both reaches (N = the newest capture; pending_reach), the proof window = the FIRST entry of a batch
                   3.2 the door: clear is the checker's; no second entry by a non-checker; entered_on ISO; Hindi replies; marg_answer checker only;
                       rename clear checker only; the owner's Accept door
                   3.3 _s521_stage_words -- ONE source of the stage's words (staff lines do-this only; the owner's English and verdict lines)
                   3.5 _amir_board_light -- one light board; _amir_board, _s436_board_extra, _s452_board_roman, _s446_board_filter,
                       _s521_stage_proof, _s521_wrong_hi, _s521_export_hi, S521_EXPORT_HI, S488_TAIL_HI, _s488_tail_hi, S452_REASONS_ROMAN retired
                   3.6 _voucher_seq -- one numbering; amir_stage called once per request; page_amir opens _s446_root; api_snapshot no longer
                       tells the rename memory (marg_take is the one door)
  item_alias.py    4   verify_closing by capture moment and identity (folds, near-miss question, both, collision, read-back), the event table,
                       undone_at / verified_k20 / verified_captured, accept, questions, sight_closing
  amir_day.py      2   four anchored edits: the card's stage lines, the owner's stage sentence, step 7's stage line, the owner's 'left' line --
                       all from stock_app._s521_stage_words; _s446_wrong_lines deleted

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import os
import sys

PINS = {
    "stock_app.py": ("b7e9880af7b81d38e7760b98d0a262b5", None),
    "item_alias.py": ("5168c3c05df63a674a8dcab59f74365f", None),
    "amir_day.py": ("7f9803d813b59df287e9175de06f6d36", None),
}
TO_FILE = "PINS.sh"


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


def once(t, a, what):
    n = t.count(a)
    if n != 1:
        raise Stop("%s: anchor occurs %d times (must be exactly 1): %r" % (what, n, a[:100]))


def rep(t, a, new, what):
    once(t, a, what)
    return t.replace(a, new, 1)


def cut(t, start, end, new, what):
    """Replace everything from `start` (inclusive) to `end` (exclusive) with `new`; both markers once, start before end."""
    once(t, start, what + " (start)")
    once(t, end, what + " (end)")
    i, j = t.index(start), t.index(end)
    if j <= i:
        raise Stop("%s: the end marker comes before the start marker" % what)
    return t[:i] + new + t[j:]


# ============================================================================================================== stock_app.py
ENTERED_DOOR = '''    clear = bool(b.get("clear"))
    no = str(b.get("marg_voucher_no") or "").strip()[:40]
    on = now_iso()[:10]                                       # S528 (R1-C14, R3-25): ISO for a NEW row; the page sends no date; readers print through _dmy_any
    if kind not in VOUCHER_KIND_TEXT or (not clear and not no):
        return jsonify(ok=False, error="bad_request", message="Write Marg's voucher number first."), 400
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    _voucher_ensure(con)
    _root, fam, R = _pad_family(con, cid)
    if R is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    r = con.execute("SELECT batches_n, COUNT(*) FROM stock_voucher_line WHERE count_id=? AND round_no=? AND kind=? AND batch_no=?",
                    (_root, rno, kind, bno)).fetchone()
    if not r or not r[1]:
        return jsonify(ok=False, error="no_such_voucher", message="No such voucher in round %d." % rno), 400
    checker = _has_role(u, "checker")
    key = (int(rno), str(kind).upper(), int(bno))
    if clear and not checker:                                 # S528 (F-852, D708, charter 13): a take-back is the checker's alone
        return jsonify(ok=False, error="checker_only", message="Yeh aapke liye nahi hai."), 403
    if not checker:                                           # S524 (F-845): a login that is not the checker may enter only a
        try:                                                  # voucher the stage has released to him -- amir_stage's visible; fail closed
            _st = amir_stage(con, _root)
            _vis = set(tuple(k) for k in ((_st or {}).get("visible") or [])) if _st else set()
        except Exception:                                     # noqa: BLE001
            _vis = set()
        if key not in _vis:
            return jsonify(ok=False, error="not_released", message="Yeh voucher abhi aapke liye khula nahi hai."), 403
        if key in _s446_entered(con, _root):                  # S528 (R2-7, R1-N8): no second entry by him -- a wrong number is the checker's clear, then his fresh entry
            return jsonify(ok=False, error="already", message="Yeh voucher likha ja chuka hai."), 409
    at, who = now_iso(), (u or {}).get("user") or ""
    con.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                (_root, rno, kind, bno, "" if clear else no, None if clear else on, who, at))
    if not clear:
        try:
            _f_ensure(con)
            con.execute("INSERT INTO stock_voucher (count_id, voucher_no, voucher_date, note, scan_ref, recorded_by, recorded_at) VALUES (?,?,?,?,?,?,?)",
                        (_root, no, on, "S301 round %d · %s · Marg voucher %d of %d" % (rno, VOUCHER_KIND_TEXT[kind], bno, r[0]), None, who, at))
        except Exception:                                     # noqa: BLE001 -- the S301 record above is the one that counts
            pass
    con.commit()
    if clear:
        return jsonify(ok=True, message="Wapas le liya.")
    try:
        _sq = _voucher_seq(con, _root).get(key)
        title_hi = "%s \\u2014 voucher %d" % (VOUCHER_HI.get(kind, kind), _sq[0] if _sq else bno)
    except Exception:                                         # noqa: BLE001
        title_hi = "%s \\u2014 voucher %d" % (VOUCHER_HI.get(kind, kind), bno)
    return jsonify(ok=True, message="Likh liya: %s \\u2014 Marg number %s" % (title_hi, no))


'''

BOARD_ROUTE = '''@bp.route("/api/pad/amir/<int:cid>")
def api_pad_amir_board(cid):
    """S528 (B3, charter 14): ONE light board for every login -- the stage read once and passed down, the words built once
    (_s521_stage_words); the count resolved to its root through _pad_family as the door does (R3-22)."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    _voucher_ensure(con)
    _root, _fam, R = _pad_family(con, cid)
    if R is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    st = amir_stage(con, int(_root))
    return jsonify(ok=True, **_amir_board_light(con, int(_root), u, st))


'''

RENAME_TICK_TAIL = '''    who = (u or {}).get("user") or ""
    if b.get("clear"):
        if not _has_role(u, "checker"):                       # S528 (B24, D708, charter 13): a take-back is the checker's alone
            return jsonify(ok=False, error="checker_only", message="Yeh aapke liye nahi hai."), 403
        ok, msg, row = item_alias.untick(con, old, who)
    else:
        ok, msg, row = item_alias.tick(con, old, who)
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), 400
    con.commit()
    return jsonify(ok=True, already=(msg == "already"), row=row, summary=item_alias.summary(con),
                   message=("Pehle hi ho chuka hai." if msg == "already" else
                            ("Wapas le liya." if b.get("clear") else
                             "Tick ho gaya: %s \\u2192 %s." % (row["old_name"], row["new_name"]))))


@bp.route("/api/pad/rename/accept", methods=["POST"])
def api_pad_rename_accept():
    """S528 (D709, 4.4): the owner's one tap on a rename QUESTION -- 'Marg prints X; is it the new name?' -- checker only; audited by
    item_alias.accept. A `both` question (old and new both printed) has no Accept: that row waits for Marg to lose the old item (R3-26)."""
    u, err = _require("checker")
    if err:
        return err
    if not _has_role(u, "checker"):
        return jsonify(ok=False, error="checker_only", message="This tap is the owner's."), 403
    b = request.get_json(silent=True) or {}
    try:
        rid = int(b.get("rename_id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request", message="rename_id is needed."), 400
    seen = str(b.get("seen_name") or "").strip()
    if not seen:
        return jsonify(ok=False, error="bad_request", message="seen_name is needed."), 400
    con = _db()
    ensure_schema(con)
    try:
        import item_alias                                      # noqa: PLC0415
    except Exception as e:                                     # noqa: BLE001
        return jsonify(ok=False, error="unavailable", message="the rename memory is not loaded: %s" % str(e)[:80]), 503
    ok, msg, row = item_alias.accept(con, rid, seen, (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), 400
    con.commit()
    return jsonify(ok=True, row=row, summary=item_alias.summary(con), message="Accepted: Marg's '%s' is %s." % (seen, row["new_name"]))


'''

FLAT_AND_NUMBERS = '''def _s437_flat(con, root, rounds):
    """The vouchers of the count in the order Amir keys them: every STOCK ISSUE voucher numbered 1..N, then every STOCK RECEIVE voucher
    1..M -- the number from _voucher_seq (S528, one numbering). The internal round numbers ride along for the entered door, never for his eyes."""
    seqs = _voucher_seq(con, root)
    out = []
    for kind in ("ISSUE", "RECEIVE"):
        for rd in sorted(rounds, key=lambda r: r["round_no"]):
            for b in sorted([b for b in rd["batches"] if b["kind"] == kind], key=lambda b: b["batch_no"]):
                seq = (seqs.get((int(rd["round_no"]), kind, int(b["batch_no"]))) or (0, kind))[0]
                out.append(dict(kind=kind, seq=seq, title="%s voucher %d" % (VOUCHER_HI[kind], seq), title_hi="%s \\u2014 voucher %d" % (VOUCHER_HI[kind], seq),
                                round_no=rd["round_no"], batch_no=b["batch_no"], n=b["n"], value_p=b.get("value_p"), sections=b.get("sections") or [],
                                entered=b.get("entered"), lines=b["lines"]))
        out.sort(key=lambda v: (v["kind"] != "ISSUE", v["seq"]))
    return out


def _voucher_seq(con, root):
    """{(round, kind, batch): (seq, kind)} -- ONE numbering of a count's vouchers, as Amir keys them: STOCK ISSUE 1..N then STOCK RECEIVE 1..M
    over EVERY round of the root (kind='RECEIVE', round_no, batch_no). S528 (3.6): the stage decides which cards are SHOWN, never how they
    are numbered -- _s437_flat, _voucher_numbers, amir_stage's numbers and the light board all read this."""
    _voucher_ensure(con)
    seq, nxt = {}, {"ISSUE": 0, "RECEIVE": 0}
    for rno, kind, bno in con.execute("SELECT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=? GROUP BY round_no, kind, batch_no "
                                      "ORDER BY kind='RECEIVE', round_no, batch_no", (int(root),)):
        k = (int(rno), str(kind), int(bno))
        if k not in seq:
            nxt[kind] = nxt.get(kind, 0) + 1
            seq[k] = (nxt[kind], str(kind))
    return seq


def _voucher_numbers(con, root):
    """item -> ['STOCK ISSUE voucher 3', 'STOCK RECEIVE voucher 1', ...] -- the same numbering as Amir's board (the statement reads it);
    S528: from _voucher_seq, the one numbering."""
    seqs = _voucher_seq(con, root)
    out = {}
    for rno, kind, bno, item in con.execute("SELECT round_no, kind, batch_no, item FROM stock_voucher_line WHERE count_id=? ORDER BY kind='RECEIVE', round_no, batch_no, line_no", (int(root),)):
        s = seqs.get((int(rno), str(kind), int(bno)))
        if not s:
            continue
        lab = "%s voucher %d" % (VOUCHER_HI.get(kind, kind), s[0])
        if lab not in out.setdefault(item, []):
            out[item].append(lab)
    return out
'''

ENTERED_FN = '''def _s446_entered(con, root):
    """{key: (marg_voucher_no, at, entered_on, by_user)} -- the newest row of a batch wins; an empty number clears it (S301's rule).
    S528 (R3-12): widened to four; every older reader uses [0] / [1] only."""
    ent = {}
    for r in con.execute("SELECT round_no, kind, batch_no, marg_voucher_no, at, entered_on, by_user FROM stock_voucher_entered WHERE count_id=? ORDER BY id", (root,)):
        k = (r[0], r[1], r[2])
        if (r[3] or "").strip():
            ent[k] = (r[3], r[4], r[5] or "", r[6] or "")
        else:
            ent.pop(k, None)
    return ent


def _s446_window(con, root):
    """{key: at_first} -- for every batch of the root that is entered NOW, the moment of its FIRST non-empty entry (S528, R3-1 / R2-7):
    a take-back by the checker (a wrong Marg number) and Amir's fresh entry never move the proof's window past a closing that already
    carries the voucher -- the voucher was in Marg from his first entry; only the number written here changed. The brief's own words:
    "a voucher you take back and he enters again is judged from his first entry"."""
    ent = _s446_entered(con, root)
    out = {}
    for r in con.execute("SELECT round_no, kind, batch_no, marg_voucher_no, at FROM stock_voucher_entered WHERE count_id=? ORDER BY id", (root,)):
        k = (r[0], r[1], r[2])
        if k in ent and (r[3] or "").strip() and k not in out:
            out[k] = str(r[4] or "")
    return out


'''

STAGE_WORDS = '''# S528 (D708, 3.3): ONE source of the stage's words. The staff lines say only what to do (no take-back, no "check this", no verdict); the
# verdict is the owner's -- his English sentence and his lines live here too, read by the hub (_s524_hub_proof), the checker's board and
# amir_day's Needs-you. The S521 proof-line helpers and S488's Hindi tail (stock_app's copy) are folded in here.
S528_KIT = "S528_AMIR_PAGE"
S528_RENAMES_DONE_HI = "Naam badal diye \\u2713"
S528_PUR_HI = "Purchase report nikaaliye"                   # his ONE do-this line of the proof (R3-11): the wait is his own purchase export


def _s528_qty_en(v, item, packing, pack):
    """A signed quantity in the owner's words (qty_words, English); '%+d' when the words cannot be had."""
    try:
        if v is not None and _qty is not None:
            return _qty.signed(v, packing=(packing or None), pack=pack, name=item, lang="en")
    except Exception:                                          # noqa: BLE001
        pass
    try:
        return "%+d" % int(round(float(v)))
    except (TypeError, ValueError):
        return "?"


def _s528_wrong_rows(rows, seqs):
    """The owner's lines for the proof's ok=False rows (3.4): 'Voucher <seq> (<kind>): <item> -- by Marg's closing of dd-mm-yyyy Marg moved
    <words>, the voucher said <words>' (+ ' (judged with its N sizes together)' for a family). English; never a figure for Amir."""
    out = []
    rows = rows or []
    for r in rows:
        vs = []
        for ks in r.get("keys") or []:
            try:
                s = seqs.get(_s446_unkey(ks))
            except Exception:                                  # noqa: BLE001
                s = None
            if s and ("voucher %d (%s)" % (s[0], VOUCHER_HI.get(s[1], s[1]))) not in vs:
                vs.append("voucher %d (%s)" % (s[0], VOUCHER_HI.get(s[1], s[1])))
        head = ", ".join(vs) or "voucher ?"
        head = head[0].upper() + head[1:]
        if r.get("marg") is None:
            why = "not in Marg's closing of %s" % (r.get("closing_day") or "?")
        else:
            why = "by Marg's closing of %s Marg moved %s, the voucher said %s" % (
                r.get("closing_day") or "?", _s528_qty_en(r.get("moved"), r.get("item"), r.get("packing"), r.get("pack")),
                _s528_qty_en(r.get("need_key"), r.get("item"), r.get("packing"), r.get("pack")))
            if r.get("family"):
                why += " (judged with its %d sizes together)" % sum(1 for x in rows if x.get("key") == r.get("key"))
        out.append(dict(item=r.get("item"), key=r.get("key"), closing_day=r.get("closing_day"), vouchers=vs, why=why,
                        text="%s: %s \\u2014 %s" % (head, r.get("item"), why)))
    return out


def _s521_stage_words(con, st):
    """{state, lines: [{hi, anchor}], card_hi, board_hi, owner_en, owner_lines: [dict(cls, target, text)], wrong_rows, questions} for the
    stage `st` (amir_stage's dict; None -> empty words, R3-19). The composition rule (R3-3): lines = the A/C line of the stage + the B line
    iff st['renames_visible'] (gone once B['verified_at'] is set), in that order; card_hi = board_hi = the lines joined with ' \\u00b7 ';
    owner_en = the stage's English + the B line's English. Inside a stage the do-this line comes first. The staff words carry no verdict
    (D708) and no promise that is not true (R2-6); kholiye only as the verb of a door."""
    E = dict(state="", lines=[], card_hi="", board_hi="", owner_en="", owner_lines=[], wrong_rows=[], questions=[])
    if not st:
        return E
    try:
        root = int(st.get("count_id") or 0)
        stage = st.get("stage")
        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
        pr = _s488_stage_proof(st) or {}                       # None in B / done (R1-N3)
        seqs = _voucher_seq(con, root)
        lines, en, state, wrong = [], "", "", []

        def pur(p):
            return (" \\u00b7 " + S528_PUR_HI) if (p or {}).get("why") == "pur_behind" else ""

        def nv(rows):
            return len({ks for r in (rows or []) for ks in (r.get("keys") or [])}) or len(rows or [])

        def c_counts():
            return "Stage C: %d of %d entered \\u00b7 %d released \\u00b7 %d verified" % (int(C.get("entered") or 0), int(C.get("total") or 0),
                                                                                    int(C.get("released") or 0), int(C.get("verified") or 0))
        if stage == "A":
            tot, entd, pend, opn = int(A.get("total") or 0), int(A.get("entered") or 0), int(A.get("pending") or 0), int(A.get("open") or 0)
            ps = pr.get("state")
            if opn > 0:
                state = "wait"
                lines.append(dict(hi="Orthotic ke voucher: %d baaki \\u2014 board kholiye" % opn, anchor="vouchers"))
                en = "Stage A: %d of %d entered" % (entd, tot)
            elif ps == "wrong":
                state = "wrong"
                lines.append(dict(hi="Orthotic voucher daal diye \\u2713", anchor=None))
                wrong = _s528_wrong_rows(pr.get("rows"), seqs)
                en = "Stage A: all %d entered \\u2014 %d voucher(s) do not agree with Marg's closing of %s" % (tot, nv(pr.get("rows")), pr.get("as_after") or "?")
            elif ps == "done":
                state = "done"
                lines.append(dict(hi="Orthotic voucher ho gaye \\u2713", anchor=None))
                en = "Stage A: all %d proven on %s" % (tot, pr.get("as_after") or "?")
            else:
                state = "export"
                lines.append(dict(hi="Orthotic voucher daal diye \\u2713" + pur(pr), anchor=None))
                en = "Stage A: all %d entered \\u2014 waiting: %s" % (tot, _s524_english_ending(pr) or "for the closing-stock export that proves them")
            if pend > 0:
                en += " \\u00b7 %d orthotic line(s) not yet on a voucher (make the round on the hub)" % pend
        elif stage == "C":
            lot = int(C.get("lots") or 0)
            if int(C.get("open") or 0) > 0:
                state = "wait"
                lines.append(dict(hi="Dawa ke voucher: %d \\u2014 board kholiye" % int(C["open"]), anchor="vouchers"))
                en = c_counts()
            elif C.get("wrong"):
                state = "wrong"
                lines.append(dict(hi="Dawa ke voucher daal diye \\u2713", anchor=None))
                wrong = _s528_wrong_rows(C.get("wrong"), seqs)
                en = "Stage C: lot %d \\u2014 %d voucher(s) do not agree with Marg's closing of %s" % (lot, nv(C.get("wrong")), ((C.get("wrong") or [{}])[0] or {}).get("closing_day") or "?")
            elif C.get("waiting_export"):
                state = "export"
                lines.append(dict(hi="Dawa ke voucher daal diye \\u2713" + pur(pr), anchor=None))
                en = "Stage C: lot %d entered on %s \\u2014 waiting: %s" % (lot, _s524_dmy(str(pr.get("last_at") or "")[:10]) or "?",
                                                                         _s524_english_ending(pr) or "for the closing-stock export")
            else:
                state = "done"
                lines.append(dict(hi="Dawa ke voucher ho gaye \\u2713", anchor=None))
                en = c_counts()
        elif stage == "done":
            state = "done"
            lines.append(dict(hi="Stock ke voucher poore \\u2713", anchor=None))
            en = "all vouchers entered and verified"
        elif stage == "B":
            state = "done"                                     # the orthotic vouchers proven and verified; the B line below is the stage's line
        b_en = ""
        if st.get("B") is not None and st.get("renames_visible") and not B.get("verified_at"):
            v, t_, q, a = int(B.get("verified") or 0), int(B.get("total") or 0), int(B.get("questions") or 0), len(B.get("old") or [])
            if B.get("open"):
                lines.append(dict(hi="Naam badalna: %d baaki \\u2014 board kholiye" % len(B["open"]), anchor="renames"))
                b_en = "Stage B: %d of %d seen in Marg; %d to tick" % (v, t_, len(B["open"]))
            else:
                lines.append(dict(hi=S528_RENAMES_DONE_HI, anchor=None))
                b_en = "Stage B: %d of %d seen in Marg" % (v, t_) + ("; %d question(s) on Amir's board" % q if q else "") + \\
                       ("; %d old name(s) still in Marg after 2 closings" % a if a else "")
        owner_lines = [dict(cls="warn", target="stock", text=r["text"]) for r in wrong]
        questions = []
        try:
            import item_alias                                  # noqa: PLC0415
            questions = item_alias.questions(con)
        except Exception:                                      # noqa: BLE001
            questions = []
        for qn in questions:
            if qn.get("event") == "both":
                owner_lines.append(dict(cls="warn", target="stock", text="Rename: Marg prints both '%s' and '%s' \\u2014 a new item was made instead of a rename (no Accept)" % (qn.get("old_name"), qn.get("new_name"))))
            else:
                owner_lines.append(dict(cls="warn", target="stock", text="Rename: Marg prints '%s' \\u2014 is it '%s'? (Accept on Amir's board)" % (qn.get("seen_name"), qn.get("new_name"))))
        for old in (B.get("old") or []) if st.get("B") is not None else []:
            owner_lines.append(dict(cls="warn", target="stock", text="Rename: '%s' still printed by Marg after 2 closings" % old))
        by_no = {}                                             # Marg numbers its ISSUE and RECEIVE vouchers in two series: a number repeats only within one kind
        for k, v in _s446_entered(con, root).items():
            by_no.setdefault((k[1], str(v[0] or "").strip()), []).append(k)
        for (kind, no), ks in sorted(by_no.items()):
            if no and len(ks) > 1:
                labs = ["%d (%s)" % (seqs[k][0], VOUCHER_HI.get(seqs[k][1], seqs[k][1])) for k in sorted(ks, key=lambda x: (x[0], x[2])) if k in seqs]
                owner_lines.append(dict(cls="warn", target="stock", text="Marg voucher number %s is written on vouchers %s" % (no, " and ".join(labs))))
        card_hi = " \\u00b7 ".join(l["hi"] for l in lines)
        return dict(state=state, lines=lines, card_hi=card_hi, board_hi=card_hi, owner_en=" \\u00b7 ".join(x for x in (en, b_en) if x),
                    owner_lines=owner_lines, wrong_rows=wrong, questions=questions)
    except Exception as e:                                     # noqa: BLE001 -- a screen never waits for its words: empty, and the cause on stderr
        print("_s521_stage_words: %s" % str(e)[:160], file=sys.stderr)
        return E
'''

HUB_PROOF = '''def _s524_hub_proof(con, root, d):
    """Hub step 7 (stock_hub.html 174-179) from the stage: state done|now|wait, text (the owner's English from _s521_stage_words -- the same
    sentence as his Needs-you line), rows (the ok=False rows with their why), lines (his verdict lines), moved_without=0, plus stage, A, B, C."""
    try:
        st = amir_stage(con, root, d=d)
    except Exception as e:                                     # noqa: BLE001
        return dict(state="wait", text="The stage could not be read: %s" % str(e)[:120], rows=[], lines=[], moved_without=0, stage=None, A={}, B={}, C={})
    if not st:
        return dict(state="wait", text="Waits for the vouchers: no voucher round has been made yet.", rows=[], lines=[], moved_without=0, stage=None, A={}, B={}, C={})
    stage, A, B, C = st.get("stage"), st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
    AP = A.get("proof") or {}
    sw = _s521_stage_words(con, st)
    if stage == "A":
        if int(A.get("open") or 0) > 0:
            state = "wait"
        elif AP.get("state") == "done":
            state = "done"
        elif AP.get("state") == "wrong":
            state = "now"
        else:
            state = "wait"
    elif stage == "C":
        state = "now" if C.get("wrong") else ("wait" if C.get("waiting_export") else "done")
    else:
        state = "done"
    rows = [dict(item=r["item"], ok=False, why=r["why"], key=r.get("key"), closing_day=r.get("closing_day")) for r in sw.get("wrong_rows") or []]
    return dict(state=state, text=sw.get("owner_en") or "", rows=rows, lines=sw.get("owner_lines") or [], moved_without=0, stage=stage, A=A, B=B, C=C)
# ---- S524_AMIR_ONE_JUDGMENT end -----------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S528_AMIR_PAGE (11-Oct-2026, D706 / D708 / D709; F-851 F-852 F-853 F-854) -- Kit 2 of three on Amir's page: the judgment reaches the screens
#   rightly, and the renames by identity. ONE light board (_amir_board_light) replaces the S227/S436/S446/S452/S521 board builders and
#   filters; ONE numbering (_voucher_seq); ONE source of the stage's words (_s521_stage_words, above); the door refuses a take-back
#   to a non-checker and a second entry; 'wrong' is said only inside both reaches (N = the newest capture); the proof window is a batch's FIRST
#   entry; api_snapshot no longer tells the rename memory (marg_take is the one door). The upload box left the staff board (F-853).
# ==========================================================================================================================================
def _dmy_any(s):
    """'2026-10-11', '2026-10-11T10:04:39', '11-10-2026' or '' -> 'dd-mm-yyyy' (or '' / the text unchanged when it is neither shape).
    S528 (R1-C14): entered_on is ISO for every row written from now on; the older rows are dd-mm-yyyy; every reader prints through this."""
    t = str(s or "").strip()
    if len(t) >= 10 and t[4] == "-" and t[7] == "-":
        return "%s-%s-%s" % (t[8:10], t[5:7], t[0:4])
    return t[:10]


def _amir_board_light(con, root, u, st):
    """Amir's board, light (3.5, charter 14): the fields the page reads and nothing else. A non-checker sees the stage's visible keys; a checker
    every batch of the root. vouchers[] carry the one number (_voucher_seq), the words of each line (_s437_line_words), the entry with its
    dd-mm-yyyy day, and can_clear / clear_hi for the checker only (the page holds no take-back word of its own)."""
    checker = _has_role(u, "checker")
    sw = _s521_stage_words(con, st)
    batches = _s446_batches(con, root)
    ent = _s446_entered(con, root)
    seqs = _voucher_seq(con, root)
    _whole_units_load(con)
    keys = list(batches) if (checker or not st) else [tuple(k) for k in (st.get("visible") or [])]
    keys = sorted([k for k in keys if k in batches], key=lambda k: (k[1] != "ISSUE", (seqs.get(k) or (0,))[0]))
    vouchers = []
    for k in keys:
        b = batches[k]
        seq = (seqs.get(k) or (0, k[1]))[0]
        lines = []
        for item, ch, mto in b["lines"]:
            pk = (b.get("pk") or {}).get(item, ("", None))
            w = _s437_line_words(item, pk[0] or "", pk[1] or 1, int(mto) - int(ch), int(ch), int(mto))
            lines.append(dict(item=item, packing=pk[0] or "", from_hi=w["from_hi"], to_hi=w["to_hi"], change_sign=(-1 if int(ch) < 0 else 1), qty_hi=w["qty_hi"]))
        e = ent.get(k)
        entered = dict(no=e[0], on=_dmy_any(e[2]), by=e[3], at_text=_r_stamp(e[1]) + " IST") if e else None
        v = dict(seq=seq, kind=k[1], n=len(lines), title_hi="%s \\u2014 voucher %d" % (VOUCHER_HI.get(k[1], k[1]), seq), round_no=k[0], batch_no=k[2],
                 entered=entered, can_clear=bool(checker and e), lines=lines)
        if checker and e:
            v["clear_hi"] = "Wapas lein"
        vouchers.append(v)
    rn = _renames_safe(con)
    rows, summ = rn.get("rows") or [], rn.get("summary") or {}
    ready = bool(st and (st.get("stage") in ("B", "C", "done") or st.get("renames_visible")))
    any_planned = any(r.get("state") == "planned" for r in rows)
    out_rows = []
    if ready and (checker or any_planned):
        for r in rows:
            x = dict(old_name=r["old_name"], new_name=r["new_name"], state=r["state"], state_hi=(r["state_hi"] if checker else r.get("state_staff_hi") or r["state_hi"]),
                     done_by=r.get("done_by") or "", verified_as_on=_dmy_any(r.get("verified_as_on")))
            if checker and r["state"] in ("done", "amber", "question"):
                x["clear_hi"] = "Wapas"
            out_rows.append(x)
    questions = []
    if checker:
        for q in sw.get("questions") or []:
            questions.append(dict(rename_id=q.get("rename_id"), old_name=q.get("old_name"), new_name=q.get("new_name"), seen_name=q.get("seen_name"),
                                  as_on=_dmy_any(q.get("as_on")), event=q.get("event"), accept=(q.get("event") != "both")))
    total, verified = int(summ.get("total") or len(rows)), int(summ.get("verified") or 0)
    done_hi = S528_RENAMES_DONE_HI if (ready and not checker and rows and not any_planned and verified < total) else ""
    renames = dict(ready=ready, wait_hi=("" if ready else S521_RENAMES_WAIT_HI), verified=verified, total=total, questions=questions, rows=out_rows, done_hi=done_hi)
    salt_fix = [dict(item=s["item"], marg_now=s.get("marg_now") or "", salt_new=s["salt_new"], hi=s["hi"]) for s in _salt_fix_rows(con) if not s.get("marg_done")]
    try:
        rate_tasks = [dict(item=t["item"], packing=t.get("packing") or "", hi="Marg mein selling rate daaliye") for t in amir_rate_due(con)]
    except Exception:                                          # noqa: BLE001
        rate_tasks = []
    rest = dict(plan=None, bill_pending=[], fixes=[])
    try:
        W = _sw.amir_view(con) if STOCK_WATCH_OK else {}
        if W and W.get("ok"):
            rest = dict(plan=W.get("plan"), bill_pending=[dict(item=x.get("item"), text_hi=x.get("text_hi") or "") for x in (W.get("bill_pending") or [])],
                        fixes=[dict(item=x.get("item"), fix=x.get("fix"), at_text=x.get("at_text") or "") for x in (W.get("fixes") or [])])
    except Exception:                                          # noqa: BLE001
        pass
    last_closing = None
    try:
        r = con.execute("SELECT as_on, MAX(received_at) FROM stock_feed WHERE source LIKE 'push_snapshot%' GROUP BY as_on ORDER BY MAX(received_at) DESC LIMIT 1").fetchone()
        if r and r[1]:
            last_closing = dict(as_on=_dmy_any(r[0]), received_at_text=_r_stamp(r[1]), hi="Aakhri closing stock jo server ko mila: %s" % _r_stamp(r[1]))
    except Exception:                                          # noqa: BLE001
        last_closing = None
    try:
        day = con.execute("SELECT marg_as_on FROM stock_count WHERE id=?", (int(root),)).fetchone()
        day = _dmy_any(day[0]) if day else ""
    except Exception:                                          # noqa: BLE001
        day = ""
    C = (st or {}).get("C") or {}
    return dict(count_id=int(root), day=day, you=dict(user=(u or {}).get("user") or ""),
                stage=dict(stage=(st or {}).get("stage"), more=int(C.get("unreleased") or 0), per=int(C.get("per") or 0)),
                vouchers=vouchers, proof=dict(state=sw.get("state") or "", hi=sw.get("board_hi") or ""), renames=renames,
                salt_fix=salt_fix, rate_tasks=rate_tasks, rest=rest, last_closing=last_closing)
# ---- S528_AMIR_PAGE end -------------------------------------------------------------------------------------------------------------------
'''


def build_stock_app(t):
    # 3.6 / charter 6: api_snapshot no longer tells the rename memory
    a = ('    if _kind != "expected":                                   # S404 (D620, F-529): read a ticked rename back from Marg\'s own export\n'
         '        try:\n'
         '            import item_alias                                  # noqa: PLC0415\n'
         '            item_alias.verify_closing(con, [(it.get("item") or "").strip() for it in items], as_on, None, "push_snapshot")\n'
         '            con.commit()\n'
         '        except Exception as _ex_ia:                            # noqa: BLE001 -- never breaks the push\n'
         '            print("item_alias.verify_closing skipped: %s" % _ex_ia, file=sys.stderr)\n')
    n = ('    # S528 (D709, charter 6): the rename memory is no longer told here. A push carries no capture moment; marg_take._rename_verify\n'
         '    # (the collector\'s door, with the export\'s own stamp and the short-closing gate) is the ONE door for a rename sighting.\n')
    t = rep(t, a, n, "api_snapshot rename call")
    # R1-C14: the finding's voucher list prints the date through _dmy_any
    t = rep(t, "    vouchers = [dict(voucher_no=r[0], voucher_date=r[1], note=r[2], scan_ref=r[3],",
            "    vouchers = [dict(voucher_no=r[0], voucher_date=_dmy_any(r[1]), note=r[2], scan_ref=r[3],", "finding vouchers voucher_date")
    # 3.2: marg_answer is the checker's (the owner's pages keep the box)
    t = rep(t, '    The next build reads them; nothing else moves."""\n    u, err = _require("checker", "maker", "viewer")\n',
            '    The next build reads them; nothing else moves. S528 (charter 13, F-853): the checker\'s door -- the staff board lost its box."""\n'
            '    u, err = _require("checker")\n', "marg_answer roles")
    # _voucher_state: entered.on through _dmy_any; _s437_flat reads _voucher_seq
    t = rep(t, '            entered[k] = dict(no=r[3], on=r[4] or "", by=r[5] or "", at_text=_r_stamp(r[6]) + " IST")\n',
            '            entered[k] = dict(no=r[3], on=_dmy_any(r[4]), by=r[5] or "", at_text=_r_stamp(r[6]) + " IST")   # S528: ISO or dd-mm-yyyy, printed as dd-mm-yyyy\n',
            "_voucher_state entered.on")
    t = rep(t, "    flat = _s437_flat(out)                                    # S437: the vouchers as Amir keys them -- STOCK ISSUE 1..N, then STOCK RECEIVE 1..M\n",
            "    flat = _s437_flat(con, root, out)                         # S437: the vouchers as Amir keys them -- STOCK ISSUE 1..N, then STOCK RECEIVE 1..M (S528: _voucher_seq)\n",
            "_voucher_state flat")
    # 3.5: _amir_board retired
    t = cut(t, 'def _amir_board(con, cid):\n    """Everything Amir\'s page shows, in one dict."""', '@bp.route("/api/pad/vouchers/<int:cid>/make", methods=["POST"])', "", "_amir_board retired")
    # 3.2: the entered door
    t = cut(t, '    clear = bool(b.get("clear"))\n    no = str(b.get("marg_voucher_no") or "").strip()[:40]\n    on = str(b.get("entered_on")',
            '@bp.route("/api/pad/vouchers/<int:cid>/<int:rno>.xlsx")', ENTERED_DOOR, "entered door")
    # 3.5: the board route
    t = cut(t, '@bp.route("/api/pad/amir/<int:cid>")\ndef api_pad_amir_board(cid):', "def _renames_safe(con):", BOARD_ROUTE, "board route")
    # 3.2 / 4.4: rename tick's clear is the checker's; the Accept door
    t = cut(t, '    who = (u or {}).get("user") or ""\n    if b.get("clear"):\n        ok, msg, row = item_alias.untick(con, old, who)',
            '@bp.route("/api/pad/ortho/<int:cid>.xlsx")', RENAME_TICK_TAIL, "rename tick tail + accept")
    # B22: page_amir opens the count whose vouchers Amir works
    t = rep(t, '        cid = str(_newest_root(con) or 0)          # S314: a whole-shop round first\n    try:\n        with io.open(PAGE_AMIR, "r", encoding="utf-8") as fh:',
            '        cid = str(_s446_root(con) or _newest_root(con) or 0)   # S528 (B22): Amir\'s path opens the count whose vouchers he works\n    try:\n        with io.open(PAGE_AMIR, "r", encoding="utf-8") as fh:',
            "page_amir root")
    # 3.5: _s436_board_extra retired
    t = cut(t, "def _s436_board_extra(con, d):", "# ---- S436_STAFF_PAGES_CLEAN end", "", "_s436_board_extra retired")
    # 3.6: one numbering
    t = cut(t, "def _s437_flat(rounds):", "# ---- S437_COUNT_PAGES_FINAL end", FLAT_AND_NUMBERS, "_s437_flat / _voucher_seq / _voucher_numbers")
    # B23
    t = rep(t, "#   C  the medicine and consumable vouchers, `amir.vouchers_per_visit` (5) at a time, oldest round first; the next lot is released\n",
            "#   C  the medicine and consumable vouchers, `amir.vouchers_per_visit` (12) at a time, oldest round first; the next lot is released\n", "the C comment (B23)")
    # R3-12 / R3-1: _s446_entered widened; _s446_window
    t = cut(t, "def _s446_entered(con, root):", "def _s446_order(keys):", ENTERED_FN, "_s446_entered / _s446_window")
    # the proof's window
    t = rep(t, "    first_at = min(ent[k][1] for k in keys)[:19]\n    last_at = max(ent[k][1] for k in keys)[:19]\n",
            "    win = _s446_window(con, root)                              # S528 (R3-1): a batch's moment is its FIRST entry -- a take-back and a fresh entry never move it\n"
            "    at_of = {k: str(win.get(k) or v[1] or \"\") for k, v in ent.items()}\n"
            "    first_at = min(at_of[k] for k in keys)[:19]\n    last_at = max(at_of[k] for k in keys)[:19]\n", "_s446_proof window")
    t = rep(t, "        stamp = tuple(sorted((_s446_key(k), str(v[1])) for k, v in ent.items()))\n",
            "        stamp = tuple(sorted((_s446_key(k), at_of[k]) for k in ent))\n", "_s446_proof cache stamp")
    t = rep(t, "            T = _s524_table(con, sp, root, ent, batches, first_at, last_at)\n",
            "            T = _s524_table(con, sp, root, ent, batches, first_at, last_at, at_of)\n", "_s446_proof table call")
    # 3.6: amir_stage's numbers are the one numbering (no reader renumbers a subset from 1)
    t = rep(t, '    out = dict(count_id=root, stage="A", visible=[], renames_visible=False, numbers={})\n',
            '    out = dict(count_id=root, stage="A", visible=[], renames_visible=False, numbers={})\n'
            '    _sq = _voucher_seq(con, root)                              # S528 (3.6): ONE numbering -- the stage decides what is shown, never how it is numbered\n', "amir_stage seq")
    t = rep(t, '        out["numbers"] = {_s446_key(k): i + 1 for i, k in enumerate(ortho)}\n',
            '        out["numbers"] = {_s446_key(k): _sq[k][0] for k in ortho if k in _sq}\n', "amir_stage numbers A")
    t = rep(t, '    out["numbers"] = {_s446_key(k): i + 1 for i, k in enumerate(out["visible"])}\n',
            '    out["numbers"] = {_s446_key(k): _sq[k][0] for k in out["visible"] if k in _sq}\n', "amir_stage numbers C")
    # _s524_stage_b: questions
    t = rep(t, '    B = dict(total=0, verified=0, ticked=0, open=[], old=[], verified_at=_s446_event(con, root, "B", "verified"))\n',
            '    B = dict(total=0, verified=0, ticked=0, questions=0, open=[], old=[], verified_at=_s446_event(con, root, "B", "verified"))\n', "_s524_stage_b init")
    t = rep(t, '        B["ticked"] = sum(1 for r in rows if r.get("state") in ("done", "amber", "verified"))\n',
            '        B["ticked"] = sum(1 for r in rows if r.get("state") in ("done", "amber", "verified", "question"))\n'
            '        B["questions"] = sum(1 for r in rows if r.get("state") == "question")     # S528 (D709): a question is ticked, not verified -- the owner\'s tap\n',
            "_s524_stage_b ticked")
    # 3.5: _s446_board_filter, _s452_board_roman (+ its constant) retired
    t = cut(t, "def _s446_board_filter(con, b, u):", "# ---- S446_AMIR_STAGES_BILLS end", "", "_s446_board_filter retired")
    t = cut(t, "def _s452_board_roman(b):", "def _s452_release(con, root, who, why):", "", "_s452_board_roman retired")
    t = rep(t, 'S452_REASONS_ROMAN = {"count_error": "Ginti mein galti", "not_billed": "Bill nahi bana", "breakage": "Toot / kharab", "expiry": "Expiry mein gaya",\n'
               '                      "sample": "Sample / doctor ko diya", "return": "Wapsi ka maal", "dont_know": "Pata nahi"}\n', "", "S452_REASONS_ROMAN retired")
    # S488's Hindi tail (stock_app's copy) retired
    t = rep(t, 'S488_TAIL_HI = {"no_figure": "closing stock aa gaya \\u2014 server ka hisaab banna baaki (bikri report ke baad)",\n'
               '                "pur_behind": "closing stock aa gaya \\u2014 purchase report nikalni baaki",\n'
               '                "no_before": "closing stock aa gaya \\u2014 jaanch system ki taraf se ruki hai",\n'
               '                "rebased": "closing stock aa gaya \\u2014 jaanch system ki taraf se ruki hai"}\n', "", "S488_TAIL_HI retired")
    t = cut(t, "def _s488_tail_hi(pr):", "# ---- S488_DATES_AND_WAITS end", "", "_s488_tail_hi retired")
    # the comments that named the retired helpers (the walk greps the names, comments included)
    t = rep(t, "#   * _s436_board_extra's last proof line says the same reason in Roman Hindi; with no reason to be had, today's words.\n",
            "#   * the board's last proof line said the same reason in Roman Hindi (S528: the stage's words, _s521_stage_words).\n", "S488 header comment")
    t = rep(t, "#   through _s436_board_extra -- while his card reads amir_stage / _s446_proof (S520: proven on the first OR the newest closing).  Two\n",
            "#   through the board's extra block -- while his card reads amir_stage / _s446_proof (S520: proven on the first OR the newest closing).  Two\n", "S521 header comment")
    t = rep(t, '           # _s446_board_filter\'s own wording\n', '           # the board\'s wording while the renames are not yet released\n', "S521_RENAMES_WAIT_HI comment")
    # 3.3: the S521 words -> _s521_stage_words
    t = cut(t, 'S521_EXPORT_HI = "Abhi baaki', "# ---- S521_AMIR_BOARD_STAGE_PROOF end", STAGE_WORDS + "\n\n", "S521 words -> _s521_stage_words")
    # 3.1: N and pending_reach
    t = rep(t, "def _s524_table(con, sp, root, ent, batches, first_at, last_at):\n", "def _s524_table(con, sp, root, ent, batches, first_at, last_at, at_of=None):\n", "_s524_table signature")
    t = rep(t, '    T = dict(R=R, after=after, tries=[], keys={}, kof={}, reach=None, mixed=set(), closings=closings)\n'
               '    if R is None or not after:\n        return T\n    reach = _s524_reach(sp)\n    T["reach"] = reach\n',
            '    T = dict(R=R, after=after, tries=[], keys={}, kof={}, reach=None, mixed=set(), closings=closings, N=None, N_short="")\n'
            '    if R is None or not after:\n        return T\n    reach = _s524_reach(sp)\n    T["reach"] = reach\n'
            '    N = after[-1]                                              # S528 (F-851, charter 1b): the NEWEST capture -- "wrong" only when it, inside the reach, disagrees\n'
            '    _N_ok, N_short = _s524_tryable(N, reach)\n    T["N"], T["N_short"] = N, N_short\n', "_s524_table N")
    t = rep(t, '            at = str(ent[kb][1] or "")[:19]\n', '            at = str((at_of or {}).get(kb) or ent[kb][1] or "")[:19]   # S528 (R3-1): the batch\'s FIRST entry\n', "_s524_table batch at")
    t = rep(t, '    for k, e in keys.items():\n        given = [t for t in e["tries"] if t["ok"] is not None]\n        prov = [t for t in given if t["ok"]]\n'
               '        e["proven"], e["wrong"] = bool(prov), (bool(given) and not prov)\n'
               '        e["L"] = prov[0] if prov else (given[-1] if given else (e["tries"][-1] if e["tries"] else None))\n',
            '    for k, e in keys.items():\n        given = [t for t in e["tries"] if t["ok"] is not None]\n        prov = [t for t in given if t["ok"]]\n'
            '        tN = next((t for t in e["tries"] if t["X"] is N), None)   # the try dicts hold the `after` objects: identity is sound\n'
            '        e["proven"] = bool(prov)\n'
            '        e["wrong"] = (not prov) and (tN is not None) and (tN["ok"] is False)              # S528 (F-851): wrong only by the newest capture\n'
            '        e["pending_reach"] = (not prov) and bool(given) and (tN is None)                   # a False stands, N not judgeable yet (R1-C2)\n'
            '        e["L"] = prov[0] if prov else (tN if tN else (given[-1] if given else (e["tries"][-1] if e["tries"] else None)))\n',
            "_s524_table verdicts")
    t = rep(t, '        else:\n            unseen.append(dict(row, why=((t or {}).get("why") or "no_verdict")))\n',
            '        else:\n            if e and e.get("pending_reach"):                     # S528 (F-851): judgeable only once the spine reaches the newest closing\n'
            '                unseen.append(dict(row, why="reach_" + (T.get("N_short") or "sale")))\n'
            '            else:\n                unseen.append(dict(row, why=((t or {}).get("why") or "no_verdict")))\n', "_s524_verdict unseen")
    t = rep(t, '    if state == "export":\n        res.update(_s488_why(con, sp, T["closings"], R, after, last_at))\n    return res\n',
            '    if state == "export":\n'
            '        pend = any(((T["keys"].get(kof.get(it) or it) or {}).get("pending_reach")) for it in items)\n'
            '        res.update(_s488_why(con, sp, T["closings"], R, ([T["N"]] if (pend and T.get("N")) else after), last_at))   # S528: the newest capture is what it waits for\n'
            '    return res\n', "_s524_verdict why")
    # the hub reads the words; the S528 block
    t = cut(t, "def _s524_hub_proof(con, root, d):", "# ---- S524_AMIR_ONE_JUDGMENT end", HUB_PROOF.split("# ---- S524_AMIR_ONE_JUDGMENT end")[0], "_s524_hub_proof")
    t = rep(t, "# ---- S524_AMIR_ONE_JUDGMENT end -----------------------------------------------------------------------------------------------------------\n",
            HUB_PROOF.split("def _s524_hub_proof(con, root, d):")[0].join(["", ""]) + "# ---- S524_AMIR_ONE_JUDGMENT end" + HUB_PROOF.split("# ---- S524_AMIR_ONE_JUDGMENT end", 1)[1],
            "S528 block appended")
    for bad in ("def _amir_board(", "= _amir_board(", "_s436_board_extra", "_s452_board_roman", "_s446_board_filter", "_s521_stage_proof", "_s521_wrong_hi", "_s521_export_hi",
                "S521_EXPORT_HI", "S488_TAIL_HI", "_s488_tail_hi", "S452_REASONS_ROMAN"):
        if bad in t:
            raise Stop("stock_app.py still carries %r after the build" % bad)
    return t


# ============================================================================================================== item_alias.py
IA_HEAD_NOTE = '''#  S528 (11-Oct-2026, D709, F-854; charter 5 / 12): a rename is seen by IDENTITY on the first closing CAPTURED after the tick, whatever
#  day the report is printed for -- the capture moment is required; the printed day decides nothing. Folds: pad_norm (case, spacing,
#  trailing dots), spine_norm (alnum only) for a near-miss, the spine's 20-letter key over the fold for a collision. Every sighting is an
#  EVENT in marg_item_rename_event (tick, untick, seen, verified, question, both, collision, accepted, read_back); a person's row is never
#  deleted; a take-back marks undone_at. A rename made in Marg without a tick is read back (B12). A question is the owner's one tap (accept).
'''

IA_DDL_ADD = '''EVENT_DDL = (
    "CREATE TABLE IF NOT EXISTS marg_item_rename_event ("
    " id INTEGER PRIMARY KEY, rename_id INTEGER, event TEXT, seen_name TEXT, as_on TEXT, captured TEXT, md5 TEXT, by_user TEXT, at TEXT, note TEXT)",
    "CREATE INDEX IF NOT EXISTS ix_marg_item_rename_event_r ON marg_item_rename_event(rename_id, event)",
)
ADD_COLUMNS = (("undone_at", "TEXT"), ("verified_k20", "TEXT"), ("verified_captured", "TEXT"))   # S528: additive, never dropped
QUESTION_EVENTS = ("question", "both", "collision")
'''

IA_ENSURE = '''def ensure(con):
    for ddl in DDL + EVENT_DDL:
        con.execute(ddl)
    cols = {r[1] for r in con.execute("PRAGMA table_info(marg_item_rename)")}
    for c, typ in ADD_COLUMNS:
        if c not in cols:
            con.execute("ALTER TABLE marg_item_rename ADD COLUMN %s %s" % (c, typ))


def _k20(name):
    """stock_watch._k20 (the spine's 20-letter key), verbatim: the fallback when stock_watch is not beside this file."""
    return re.sub(r"\\s+", " ", str(name or "").strip())[:20].strip()


def _Kf(name):
    """The spine's key over the pad fold (S528 4.1): stock_watch._k20(pad_norm(name))."""
    try:
        import stock_watch                                    # noqa: PLC0415 -- beside this file
        return stock_watch._k20(pad_norm(name))
    except Exception:                                         # noqa: BLE001
        return _k20(pad_norm(name))


def _stamp_iso(stamp):
    """'YYYYMMDD-HHMMSS' -> 'YYYY-MM-DDTHH:MM:SS' (as marg_take.py reads a capture); '' when it is not a stamp."""
    s = str(stamp or "")
    if not re.match(r"^\\d{8}-\\d{6}$", s):
        return ""
    return "%s-%s-%sT%s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])


def _event(con, rid, event, who, ts, seen_name=None, as_on=None, captured=None, md5=None, note=None):
    con.execute("INSERT INTO marg_item_rename_event (rename_id, event, seen_name, as_on, captured, md5, by_user, at, note) VALUES (?,?,?,?,?,?,?,?,?)",
                (int(rid), event, seen_name, as_on, captured, md5, who, ts, note))


def _event_once(con, rid, event, who, ts, seen_name, as_on, captured, md5, note=None):
    """A question / both / collision is written once per distinct (rename_id, event, seen_name) -- R3-14."""
    if con.execute("SELECT 1 FROM marg_item_rename_event WHERE rename_id=? AND event=? AND COALESCE(seen_name,'')=?", (int(rid), event, seen_name or "")).fetchone():
        return False
    _event(con, rid, event, who, ts, seen_name, as_on, captured, md5, note)
    return True


def _open_questions(con):
    """{rename_id: the newest open question/both/collision event (a dict)} -- open = no later accepted / verified event on that row."""
    out = {}
    try:
        for r in con.execute("SELECT id, rename_id, event, seen_name, as_on, captured, md5, at FROM marg_item_rename_event ORDER BY id"):
            rid = int(r[1])
            if r[2] in QUESTION_EVENTS:
                out[rid] = dict(id=r[0], rename_id=rid, event=r[2], seen_name=r[3], as_on=r[4], captured=r[5], md5=r[6], at=r[7])
            elif r[2] in ("accepted", "verified"):
                out.pop(rid, None)
    except sqlite3.Error:
        pass
    return out
'''

IA_STATE_ROWS = '''def _state(r, open_q=None):
    """verified | question (an open question/both/collision event) | amber | done (ticked, not taken back) | planned -- S528 4.3."""
    if r["verified_at"]:
        return "verified"
    if open_q:
        return "question"
    if r["done_at"] and not r.get("undone_at"):
        return "amber" if int(r["seen_n"] or 0) >= AMBER_AFTER_EXPORTS else "done"
    return "planned"


STATE_HI = {"planned": "Marg mein badalna hai", "done": "Badal diya \\u2014 Marg export ka intezaar",
            "amber": "Marg mein abhi dikha nahi", "verified": "Marg mein dikh gaya \\u2713", "question": "Badal diya \\u2713"}
STATE_EN = {"planned": "to rename in Marg", "done": "ticked -- waiting for Marg's next stock export",
            "amber": "ticked, not yet seen in Marg", "verified": "seen in Marg's export", "question": "ticked -- a question for the owner"}
# S528 (D708, R3-13): the words a STAFF screen prints for a row -- do-this or done, never a verdict (the checker's board keeps STATE_HI)
STATE_STAFF_HI = {"planned": "Badalna hai", "done": "Badal diya \\u2713", "amber": "Badal diya \\u2713", "question": "Badal diya \\u2713",
                  "verified": "Marg mein dikh gaya \\u2713"}


def rows(con):
    """Every rename with its state: planned | done | amber | question | verified."""
    ensure(con)
    out = []
    oq = _open_questions(con)
    cur = con.execute("SELECT id, old_name, new_name, old20, old27, new20, new27, family, planned_by, planned_at, done_by, done_at, "
                      "verified_at, verified_md5, verified_as_on, seen_n, last_seen_as_on, note, undone_at, verified_k20, verified_captured "
                      "FROM marg_item_rename ORDER BY id")
    cols = [c[0] for c in cur.description]
    for t in cur.fetchall():
        r = dict(zip(cols, tuple(t)))
        q = oq.get(int(r["id"]))
        r["state"] = _state(r, q)
        r["state_hi"] = STATE_HI[r["state"]]
        r["state_en"] = STATE_EN[r["state"]]
        r["state_staff_hi"] = STATE_STAFF_HI[r["state"]]
        r["question"] = q
        out.append(r)
    return out


def summary(con):
    rs = rows(con)
    s = dict(total=len(rs), planned=0, done=0, amber=0, verified=0, question=0, kit=KIT)
    for r in rs:
        s[r["state"]] += 1
    s["questions"] = s["question"]
    s["all_verified"] = bool(rs) and s["verified"] == len(rs)
    return s


def questions(con):
    """The open questions for the owner (S528 3.4 / 4.4): [{rename_id, old_name, new_name, seen_name, as_on, captured, event}]."""
    out = []
    for r in rows(con):
        q = r.get("question")
        if q and r["state"] == "question":
            out.append(dict(rename_id=int(r["id"]), old_name=r["old_name"], new_name=r["new_name"], seen_name=q.get("seen_name"),
                            as_on=q.get("as_on"), captured=q.get("captured"), event=q.get("event")))
    return out


def done_rows(con):
    """The rows whose tick stands (done, amber, question, verified) -- a taken-back tick maps nothing."""
    return [r for r in rows(con) if r["state"] in ("done", "amber", "question", "verified")]
'''

IA_TICK_UNTICK = '''def tick(con, old_name, who, ts=None):
    """'Marg mein badal diya' -- Amir's one tick. Idempotent: a second tick answers already=True and writes nothing. A row whose tick was
    taken back (undone_at) is re-ticked by a NEW tick event: done_at = ts, done_by = user, undone_at cleared (the one system mark cleared --
    S528, R2-17). Returns (ok, message, row)."""
    ensure(con)
    ts = ts or now_iso()
    rs = [r for r in rows(con) if r["old_name"] == old_name or r["new_name"] == old_name]
    if not rs:
        return False, "that name is not on the rename list", None
    r = rs[0]
    if r["done_at"] and not r.get("undone_at"):
        return True, "already", r
    con.execute("UPDATE marg_item_rename SET done_by=?, done_at=?, undone_at=NULL WHERE id=?", (who, ts, r["id"]))
    _event(con, r["id"], "tick", who, ts, note=("re-ticked after a take-back" if r.get("undone_at") else None))
    notes = _follow(con, r, who, ts)
    _audit(con, who, "rename_ticked", dict(old=r["old_name"], new=r["new_name"], notes=notes))
    return True, "ticked", [x for x in rows(con) if x["id"] == r["id"]][0]


def untick(con, old_name, who, ts=None):
    """Taken back (the checker's) -- only while the rename has not been seen in Marg (a verified rename is a fact). S528: marks undone_at and
    writes an untick event; done_by / done_at are never NULLed (charter 5)."""
    ensure(con)
    ts = ts or now_iso()
    rs = [r for r in rows(con) if r["old_name"] == old_name or r["new_name"] == old_name]
    if not rs:
        return False, "that name is not on the rename list", None
    r = rs[0]
    if r["verified_at"]:
        return False, "Marg's export already carries the new name -- it cannot be taken back", r
    if not r["done_at"] or r.get("undone_at"):
        return True, "already", r
    con.execute("UPDATE marg_item_rename SET undone_at=?, seen_n=0, last_seen_as_on=NULL WHERE id=?", (ts, r["id"]))
    _event(con, r["id"], "untick", who, ts)
    try:
        con.execute("UPDATE marg_item_name SET active=0, note=COALESCE(note,'')||' | tick taken back' WHERE name_raw=? AND kind='alias'", (r["new_name"],))
    except sqlite3.Error:
        pass
    _audit(con, who, "rename_untick", dict(old=r["old_name"], new=r["new_name"]))
    return True, "taken back", [x for x in rows(con) if x["id"] == r["id"]][0]


def accept(con, rename_id, seen_name, who, ts=None):
    """The owner's one tap (S528 4.4): an open question / collision naming `seen_name` -> accepted; the verified_* fields are set from the
    question's capture; a `both` question is never accepted (R3-26). Returns (ok, message, row)."""
    ensure(con)
    ts = ts or now_iso()
    rs = [r for r in rows(con) if int(r["id"]) == int(rename_id)]
    if not rs:
        return False, "no such rename", None
    r = rs[0]
    if r["verified_at"]:
        return True, "already", r
    q = r.get("question")
    if not q or r["state"] != "question":
        return False, "that rename has no open question", r
    if q.get("event") == "both":
        return False, "Marg prints both names -- a new item was made instead of a rename; nothing to accept", r
    if pad_norm(q.get("seen_name")) != pad_norm(seen_name):
        return False, "the question is about '%s', not '%s'" % (q.get("seen_name"), seen_name), r
    con.execute("UPDATE marg_item_rename SET verified_at=?, verified_md5=?, verified_as_on=?, verified_captured=?, verified_k20=? WHERE id=?",
                (ts, q.get("md5"), q.get("as_on"), q.get("captured"), _Kf(seen_name), r["id"]))
    _event(con, r["id"], "accepted", who, ts, seen_name=q.get("seen_name"), as_on=q.get("as_on"), captured=q.get("captured"), md5=q.get("md5"))
    notes = _follow(con, r, who, ts)
    _audit(con, who, "rename_accepted", dict(old=r["old_name"], new=r["new_name"], seen=q.get("seen_name"), notes=notes))
    return True, "accepted", [x for x in rows(con) if x["id"] == r["id"]][0]
'''

IA_VERIFY = '''def verify_closing(con, names, as_on, md5=None, source="", ts=None, captured=None):
    """ONE closing-stock export has arrived (names = every item it lists, as_on = its printed day, captured = the moment it was taken, ISO --
    REQUIRED: a call without it logs one line and returns; marg_take, the one door, always passes it). S528 (D709, F-854; charter 12):
    a row is judged by a closing captured AFTER its tick (captured[:19] > done_at[:19]), whatever day it is printed for; one captured before
    the tick is skipped. Folds: pn = pad_norm, sn = spine_norm, Kf = the spine's 20-letter key over pn.
      seen       the export lists a name with pn == pn(new) (or the same 29-clip) and NO name with pn == pn(old) -> events seen + verified
      question   no pn match but a name with sn == sn(new) (an inner dot, a hyphen) -> event question with seen_name; the owner's tap
      both       pn(new) AND pn(old) both listed -> event both (a new item was made instead of a rename); no Accept
      collision  Kf(new) equals the Kf of a listed name that is neither old nor new -> event collision; the owner's tap
      read_back  a row never ticked (or taken back) whose new name is listed and old name not, captured after planned_at -> ticked by 'marg'
    A questioned row is still judged on later closings: an exact sighting verifies it and supersedes the question. seen_n counts closings
    captured after the tick that showed neither the new name nor a question, once per printed day (last_seen_as_on, as before).
    Returns dict(verified=[..], seen=[..], questions=[..], read_back=[..], as_on, md5)."""
    ensure(con)
    ts = ts or now_iso()
    day = _iso(as_on)
    md5 = md5 or names_md5(names, day)
    out = dict(verified=[], seen=[], questions=[], read_back=[], as_on=day, md5=md5)
    cap = str(captured or "")[:19]
    if not cap:
        print("item_alias.verify_closing: no capture moment given (as_on %s, %s) -- nothing judged; marg_take is the door" % (day, source), file=sys.stderr)
        out["skipped"] = "no_captured"
        return out
    have = [str(n or "").strip() for n in names if str(n or "").strip()]
    P, P29, S, K = {}, {}, {}, {}
    for n in have:
        p = pad_norm(n)
        P.setdefault(p, n)
        P29.setdefault(clip(p, MASTER_CLIP), n)
        S.setdefault(spine_norm(n), n)
        K.setdefault(_Kf(n), set()).add(p)
    who = source or "export"
    for r in rows(con):
        if r["verified_at"]:
            continue
        pn_new, pn_old = pad_norm(r["new_name"]), pad_norm(r["old_name"])
        new_hit = P.get(pn_new) or P29.get(clip(pn_new, MASTER_CLIP))
        old_in = pn_old in P
        ticked = bool(r["done_at"]) and not r.get("undone_at")
        if ticked:
            if cap <= str(r["done_at"])[:19]:
                continue                                      # taken before the tick: cannot carry it
            if new_hit and not old_in:
                others = K.get(_Kf(pn_new), set()) - {pn_new, pn_old, pad_norm(new_hit)}
                if others:
                    seen_other = P.get(sorted(others)[0]) or sorted(others)[0]
                    if _event_once(con, r["id"], "collision", who, ts, seen_other, day, cap, md5):
                        out["questions"].append(r["old_name"])
                    continue
                con.execute("UPDATE marg_item_rename SET verified_at=?, verified_md5=?, verified_as_on=?, verified_captured=?, verified_k20=? WHERE id=?",
                            (ts, md5, day, cap, _Kf(pn_new), r["id"]))
                _event(con, r["id"], "seen", who, ts, seen_name=new_hit, as_on=day, captured=cap, md5=md5)
                _event(con, r["id"], "verified", who, ts, seen_name=new_hit, as_on=day, captured=cap, md5=md5)
                out["verified"].append(r["old_name"])
                _audit(con, who, "rename_verified", dict(old=r["old_name"], new=r["new_name"], as_on=day, md5=md5, captured=cap))
            elif new_hit and old_in:
                if _event_once(con, r["id"], "both", who, ts, new_hit, day, cap, md5):
                    out["questions"].append(r["old_name"])
            else:
                near = S.get(spine_norm(r["new_name"]))        # an inner dot, a hyphen (R1-C8)
                if not near:                                  # S528 (D709, read on the 10-10 closing): a printed spelling that is a prefix of the
                    for p in sorted(P):                       # new name, or carries it as a prefix (the shorter at least 20 letters), with the old
                        if p != pn_new and p != pn_old and min(len(p), len(pn_new)) >= 20 and (p.startswith(pn_new) or pn_new.startswith(p)):
                            near = P[p]                       # name gone -- a spelling the system cannot be sure of: the owner's one tap
                            break
                if near and pad_norm(near) != pn_old:
                    if _event_once(con, r["id"], "question", who, ts, near, day, cap, md5):
                        out["questions"].append(r["old_name"])
                elif day and day != (r["last_seen_as_on"] or ""):
                    con.execute("UPDATE marg_item_rename SET seen_n=seen_n+1, last_seen_as_on=? WHERE id=?", (day, r["id"]))
                    out["seen"].append(r["old_name"])
        else:                                                 # never ticked, or taken back: read back without a tick (B12)
            since = str(r.get("undone_at") or r["planned_at"] or "")[:19]
            if cap <= since:
                continue
            if new_hit and not old_in:
                con.execute("UPDATE marg_item_rename SET done_by='marg', done_at=?, undone_at=NULL, verified_at=?, verified_md5=?, verified_as_on=?, "
                            "verified_captured=?, verified_k20=? WHERE id=?", (cap, ts, md5, day, cap, _Kf(pn_new), r["id"]))
                _event(con, r["id"], "read_back", who, ts, seen_name=new_hit, as_on=day, captured=cap, md5=md5)
                _event(con, r["id"], "verified", who, ts, seen_name=new_hit, as_on=day, captured=cap, md5=md5)
                notes = _follow(con, r, "marg", ts)
                out["read_back"].append(r["old_name"])
                _audit(con, who, "rename_read_back", dict(old=r["old_name"], new=r["new_name"], as_on=day, md5=md5, captured=cap, notes=notes))
    return out


def sight_closing(con, names, as_on, md5=None, stamp=None, source="sight_closing", ts=None):
    """ONE closing reader (S528 4.5, R2-21): the short-closing gate (reports_watch.closing_short) and the stamp -> ISO conversion, then
    verify_closing. Returns verify_closing's dict, or dict(skipped='short', ...) with one stderr line."""
    try:
        import reports_watch                                  # noqa: PLC0415 -- beside this file
        short = reports_watch.closing_short(con, as_on, len(names))
    except Exception as e:                                    # noqa: BLE001
        short = None
        print("item_alias.sight_closing: the short-closing gate could not run (%s) -- judged as full" % str(e)[:80], file=sys.stderr)
    if short:
        print("item_alias.sight_closing: short closing %s (%d items, needs %s) -- skipped" % (as_on, len(names), short.get("need")), file=sys.stderr)
        return dict(verified=[], seen=[], questions=[], read_back=[], as_on=_iso(as_on), md5=md5, skipped="short", short=short)
    cap = _stamp_iso(stamp) or now_iso()
    return verify_closing(con, names, as_on, md5, source, ts, captured=cap)
'''


def build_item_alias(t):
    t = rep(t, 'VERSION = "1.0"\nKIT = "S404_ORTHO_STOCK_CLOSE"\n', 'VERSION = "2.0"\nKIT = "S528_AMIR_PAGE"\n', "item_alias version")
    t = rep(t, "#  Standard library only.  Python 3.9 (both of the box's pythons).\n", IA_HEAD_NOTE + "#\n#  Standard library only.  Python 3.9 (both of the box's pythons).\n", "item_alias head note")
    t = rep(t, 'import re\nimport sqlite3\n', 'import re\nimport sqlite3\nimport sys\n', "item_alias imports")
    t = rep(t, '    "CREATE INDEX IF NOT EXISTS ix_marg_item_rename_new ON marg_item_rename(new_name)",\n)\n',
            '    "CREATE INDEX IF NOT EXISTS ix_marg_item_rename_new ON marg_item_rename(new_name)",\n)\n' + IA_DDL_ADD, "item_alias DDL add")
    t = cut(t, "def ensure(con):\n    for ddl in DDL:\n        con.execute(ddl)\n", "def check_list(pairs, all_names=()):", IA_ENSURE + "\n\n", "item_alias ensure")
    t = cut(t, 'def _state(r):\n    if r["verified_at"]:', "def resolve_map(con):", IA_STATE_ROWS + "\n\n", "item_alias state/rows/summary/questions/done_rows")
    t = cut(t, "def tick(con, old_name, who, ts=None):", "# ------------------------------------------------------------------ the verification (F-529: read it back)",
            IA_TICK_UNTICK + "\n\n", "item_alias tick/untick/accept")
    t = cut(t, "def verify_closing(con, names, as_on, md5=None, source=\"\", ts=None, captured=None):", 'if __name__ == "__main__":', IA_VERIFY + "\n\n", "item_alias verify_closing")
    t = rep(t, '        for r in rows(c):\n            print("%-9s %-31s -> %-30s %s" % (r["state"], r["old_name"], r["new_name"], r["done_by"] or ""))\n',
            '        for r in rows(c):\n            print("%-9s %-31s -> %-30s %s %s" % (r["state"], r["old_name"], r["new_name"], r["done_by"] or "", (r.get("verified_captured") or "")))\n',
            "item_alias --status")
    return t


# ============================================================================================================== amir_day.py
AD_CARD = '''        for ln in (s.get("stage_words") or {}).get("lines") or []:       # S528 (D708): the words come from stock_app._s521_stage_words -- do-this lines only
            if ln.get("anchor"):
                lines.append("<div class=line><a class=btn href='%s'>%s</a></div>" % (_esc(_s446_board(st, ln["anchor"])), _esc(ln.get("hi") or "")))
            else:
                lines.append("<div class=line><span class=big>%s</span></div>" % _esc(ln.get("hi") or ""))
'''

AD_OWNER = '''        sw = {}
        try:
            sw = stock_app._s521_stage_words(con, st)           # S528 (2.2): the one source of the owner's stage sentence and his verdict lines
        except Exception:                                      # noqa: BLE001
            sw = {}
        out.append(dict(cls="info", target="stock", text="Count #%d: %s" % (st["count_id"], sw.get("owner_en") or "")))
        out.extend(sw.get("owner_lines") or [])
'''

AD_EXTRA = '''        ch = (s.get("stage_words") or {}).get("card_hi") or ""       # S528 (2.3): the same words as his card
        if ch:
            out.append(ch)
'''

AD_LEFT = '''        oe = (s.get("stage_words") or {}).get("owner_en") or ""      # S528 (2.4): the owner's one stage sentence
        if oe:
            out.append(oe)
'''


def build_amir_day(t):
    t = rep(t, 'def _s446_state(cx, day):\n    st = None\n    try:\n        import stock_app                                       # noqa: PLC0415\n'
               '        st = stock_app.amir_stage(cx)\n    except Exception:                                          # noqa: BLE001\n        st = None\n'
               '    return dict(stage=st, packs=_s446_packs(cx), watch=_s446_watch(cx), jobs=_s494_jobs(cx),     # S494: [] on any error\n',
            'def _s446_state(cx, day):\n    st, sw = None, {}\n    try:\n        import stock_app                                       # noqa: PLC0415\n'
            '        st = stock_app.amir_stage(cx)\n    except Exception:                                          # noqa: BLE001\n        st = None\n'
            '    try:\n        sw = stock_app._s521_stage_words(cx, st) if st else {}     # S528 (2): the stage\'s words, built once beside the stage\n'
            '    except Exception:                                          # noqa: BLE001\n        sw = {}\n'
            '    return dict(stage=st, stage_words=sw, packs=_s446_packs(cx), watch=_s446_watch(cx), jobs=_s494_jobs(cx),     # S494: [] on any error\n',
            "_s446_state")
    t = cut(t, "def _s446_wrong_lines(rows, numbers):", "def _s446_card(w, top=False):", "", "_s446_wrong_lines deleted")
    t = cut(t, '        stage = st.get("stage")\n        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}\n        if stage == "A":\n            pr = A.get("proof") or {}\n',
            '    wt = s.get("watch") or {}\n    if wt.get("sunday"):', AD_CARD, "_s446_card stage lines")
    t = cut(t, '        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}\n        if st["stage"] == "A":\n            pr = (A.get("proof") or {}).get("state")\n',
            "        _w488 = _s488_wait_line(con, st)", AD_OWNER, "_s446_owner_lines")
    t = cut(t, '        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}\n        cid = int(st.get("count_id") or 0)\n        if st.get("stage") == "A":\n',
            '    if ((w.get("s444") or {}).get("salt") or {}).get("pending"):\n        out.append("SALT WISE ITEM LIST abhi nahi aayi")', AD_EXTRA, "_s452_extra_hi")
    t = cut(t, '        A, B, C = st.get("A") or {}, st.get("B") or {}, st.get("C") or {}\n        if st.get("stage") == "A":\n            if A.get("open"):\n                out.append("count #%d stage A:',
            '    if (w.get("s444") or {}).get("salt", {}).get("pending"):\n        out.append("SALT WISE ITEM LIST not received")', AD_LEFT, "_s446_left")
    # the `bat` line of _s446_owner_lines read B: keep B in scope
    t = rep(t, '        _w488 = _s488_wait_line(con, st)                       # S488 (B.3): the proof has waited amir.proof_wait_hours or more\n',
            '        B = st.get("B") or {}\n        _w488 = _s488_wait_line(con, st)                       # S488 (B.3): the proof has waited amir.proof_wait_hours or more\n',
            "_s446_owner_lines B")
    for bad in ("_s446_wrong_lines", "Voucher kholiye", "Theek karke", "voucher %d jaanch"):
        if bad in t:
            raise Stop("amir_day.py still carries %r after the build" % bad)
    return t


# ============================================================================================================== main
def read_to_pins(kit_dir):
    p = os.path.join(kit_dir, TO_FILE)
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.startswith("TO[") and "]=" in line:
                k, v = line[3:].split("]=", 1)
                out[k] = v.strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    to = read_to_pins(here)
    os.makedirs(a.out, exist_ok=True)
    builders = {"stock_app.py": build_stock_app, "item_alias.py": build_item_alias, "amir_day.py": build_amir_day}
    rc = 0
    for name, fn in builders.items():
        src = os.path.join(a.finance, name)
        raw = open(src, "rb").read()
        if md5(raw) != PINS[name][0]:
            print("!! %s is %s, not its FROM pin %s -- stopped" % (src, md5(raw), PINS[name][0]))
            return 2
        try:
            new = fn(raw.decode("utf-8"))
        except Stop as e:
            print("!! %s: %s" % (name, e))
            return 2
        nb = new.encode("utf-8")
        try:
            compile(new, name, "exec")
        except SyntaxError as e:
            print("!! %s does not compile after the edits: %s" % (name, e))
            return 2
        dst = os.path.join(a.out, name)
        with open(dst, "wb") as fh:
            fh.write(nb)
        m = md5(nb)
        want = to.get(name)
        print("   %-14s %s -> %s  (%+d lines)%s" % (name, PINS[name][0][:8], m, new.count("\n") - raw.decode("utf-8").count("\n"),
                                                   "" if (a.print_to or want == m) else "   !! not the kit's TO pin %s" % want))
        if not a.print_to and want != m:
            rc = 3
    return rc


if __name__ == "__main__":
    sys.exit(main())
