#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s524.py -- the builder of kit S524_AMIR_ONE_JUDGMENT (11-Oct-2026, D706; F-843 F-844 F-845 F-846 F-847 F-848 F-840, the spine gate of 08-Oct).

    python3 -B make_s524.py --finance /root/finance --spine /root/finance/spine --ingest /root/marg_ingest --briefs <repo>/claude_code_briefs --out DIR

Reads the LIVE files, refuses anything but their FROM pins, makes anchored edits (each anchor must occur exactly once, else it stops),
compiles every python result on the python that runs this script, and writes the results into --out (nothing else is written).
With --print-to the built md5s are printed and accepted (packing the kit); without it a result must equal its TO pin.

  spine/marg_read.py      (a) ITEM_GLUED widened: a glued row whose piece is digit-led or '_'-joined ('06202627ANKLE BINDER BAMBOO M',
                              'A000207_TYRO BR') -- Marg prints 8 characters of a long bill number glued to the item (F-800's shape)
  spine/spine_build.py    (b) tie_piece(): when the plain number matches NO bill, the ONE bill of that supplier (or that day) whose
                              number contains the piece (>= 6 characters) ties the line -- S501's rule in the spine's shape
  stock_app.py            2.1 _s446_proof rebuilt on the spine (one key, one judgment, both tries); 2.2 amir_stage re-derived from its inputs
                              (A["pending"], the recheck event, renames once released stay); 2.3 the old proof retired (hub step 7, board
                              extra, stockmatch read the stage); 2.4 the entered door gated by the stage; _report_cached; _s488_why rewritten
  amir_day.py             2.7 the wrong-row sentence from the row's own words; 2.2 the card's and the owner's words for 'proven, a line pending'
  stockmatch.py           2.3 section_state's c3 from the stage proof (F-840)
  shelf_figure.py         2.8 filed_vouchers judges a batch by its moment against the two captures (F-848)
  marg_ingest/marg_take.py 2.6 a short closing never verifies a rename (F-847)
  DUTY_MAP.json / .md     2.5 amir.count_vouchers v9 -> v10: the orthotic batches and the released lots only (F-846)

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import json
import os
import sys

PINS = {
    "stock_app.py": ("c0f0623f7d540bbdedb4369aa459405a", None),
    "stockmatch.py": ("fc1caf4496c4fd072e909b4d3e6784aa", None),
    "shelf_figure.py": ("a1e87d1ff758e8f9a8206205a457b875", None),
    "amir_day.py": ("f1ce78e8bd788fbbb8c9774c04119af9", None),
    "marg_take.py": ("a86a0f26d4fc86a51e963b6a1b561323", None),
    "spine_build.py": ("11f8acb05c46aeaa72e1771d5c89922c", None),
    "marg_read.py": ("96f565a8d138d9ce75c0ed228b471495", None),
    "DUTY_MAP.json": ("2016244829b4c70c00f1c59b0250ee35", None),
    "DUTY_MAP.md": ("7400e9ff2b047df82c81e897a06ea5ac", None),
}
TO_FILE = "PINS.sh"          # the TO pins, written when the kit is packed (read by the installer); None above = read from there


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


def once(t, a, what):
    n = t.count(a)
    if n != 1:
        raise Stop("%s: anchor occurs %d times (must be exactly 1): %r" % (what, n, a[:90]))


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


# ============================================================================================================== spine/marg_read.py (a)
def build_marg_read(t):
    t = rep(t, 'READER_VERSION = "S331.1"\n', 'READER_VERSION = "S524.1"\n', "marg_read READER_VERSION")
    a = ("        glued = None\n"
         "        if not c[0] and c[1] and money[0] is not None and money[1] is not None:\n"
         "            gm = re.match(r'^([A-Z]{1,3}-?\\d{3,})([A-Z].*)$', c[1])\n"
         "            if gm:\n"
         "                glued = gm\n")
    n = ("        glued = None\n"
         "        if not c[0] and c[1] and money[0] is not None and money[1] is not None:\n"
         "            gm = re.match(r'^([A-Z]{1,3}-?\\d{3,})([A-Z].*)$', c[1])\n"
         "            if not gm:\n"
         "                # S524 (the spine gate, 08-Oct; F-800's shape): Marg's SUPPLIER/ITEM WISE text prints 8 characters of a long bill\n"
         "                # number glued to the item name -- digit-led ('06202627ANKLE BINDER BAMBOO M') or '_'-joined ('A000207_TYRO BR').\n"
         "                # The piece is a run of 6-8 letters/digits (the 8-character clip), then an optional '_' or space, then the item.\n"
         "                gm = re.match(r'^([A-Z0-9]{6,8})[_ ]?([A-Z0-9].*)$', c[1])\n"
         "            if gm:\n"
         "                glued = gm\n")
    return rep(t, a, n, "marg_read ITEM_GLUED")


# ============================================================================================================== spine/spine_build.py (b)
TIE_PIECE = '''def tie_piece(ln, data, pbills):
    """S524 (the spine gate, 08-Oct; F-800): a purchase line whose printed bill number matched NO bill. Marg's SUPPLIER/ITEM WISE text
    prints only 8 characters of a long bill number ('L2678591' of 'GPPL2678591', '06202627' of 'YS0706202627'); the BILL WISE report
    carries the whole number. SUPPLIER grouping: that supplier's bills inside the export's period; BILL grouping: the bills of the line's
    day. The line ties when EXACTLY ONE candidate's number contains the piece (raw, upper-case) and the piece is at least 6 characters;
    else [] and the line stays untied, as before. This is S501's _s501_fragment rule in the spine's own shape; it never runs when the
    plain match found one or more bills (S484's shared-number cutting stays as it is)."""
    piece = str(ln.get("bill") or "").strip().upper()
    if len(piece) < 6:
        return []
    if data.get("grouping") == "SUPPLIER":
        sk = supnorm(ln.get("supplier"))
        cands = [b for (s, _bill, d), b in pbills.items() if s == sk and data["date_from"] <= d <= data["date_to"]]
    else:
        cands = [b for (_s, _bill, d), b in pbills.items() if d == ln.get("date")]
    hits = [b for b in cands if piece in str(b["bill"] or "").upper()]
    return hits if len(hits) == 1 else []


'''


def build_spine_build(t):
    t = rep(t, 'BUILD_VERSION = "S484.1"\n', 'BUILD_VERSION = "S524.1"\n', "spine_build BUILD_VERSION")
    t = rep(t, "def build(readings, rules, acceptance=False, finance_db=None, log=print):\n",
            TIE_PIECE + "def build(readings, rules, acceptance=False, finance_db=None, log=print):\n", "spine_build tie_piece")
    a = ('            if len(cands) != 1:\n'
         '                undated.append((r["name"], ln["bill"], ln["name"], len(cands), whole_auth))\n'
         '                continue\n'
         '            b = cands[0]\n')
    n = ('            if not cands:                                # S524 (the spine gate, 08-Oct): no bill carries the printed number as it is --\n'
         '                cands = tie_piece(ln, r["data"], pbills)   # Marg printed 8 characters of a longer one (F-800); tie to the ONE bill holding the piece\n'
         '                if len(cands) == 1:                      # the line carries the bill\'s whole number from here on; the printed piece stays beside it\n'
         '                    ln = dict(ln, bill=cands[0]["bill"], piece=ln["bill"])\n'
         '            if len(cands) != 1:\n'
         '                undated.append((r["name"], ln["bill"], ln["name"], len(cands), whole_auth))\n'
         '                continue\n'
         '            b = cands[0]\n')
    return rep(t, a, n, "spine_build tie step")


# ============================================================================================================== marg_ingest/marg_take.py (2.6)
def build_marg_take(t):
    a = ('        names = [i["name"] for i in (R.data.get("items") or []) if i.get("name")]\n'
         '        as_on = R.data.get("as_on") or ""\n'
         '        cap = None\n')
    n = ('        names = [i["name"] for i in (R.data.get("items") or []) if i.get("name")]\n'
         '        as_on = R.data.get("as_on") or ""\n'
         '        import reports_watch                                     # noqa: PLC0415 -- beside item_alias (S524, F-847)\n'
         '        _short = reports_watch.closing_short(con, as_on, len(names))   # None when full, or when no reference closing exists (a fresh box)\n'
         '        if _short:                                               # S524 (F-847): a SHORT closing is never a verdict on a rename\n'
         '            print("marg_take: rename verification skipped: short closing %s (%d items)" % (as_on, len(names)), file=sys.stderr)\n'
         '            return\n'
         '        cap = None\n')
    return rep(t, a, n, "marg_take short closing")


# ============================================================================================================== shelf_figure.py (2.8)
FILED_OLD_START = "def filed_vouchers(con, item, d_from, d_to):\n"
FILED_OLD_END = "\n\ndef _s494_ddmm_hm(ts):\n"
FILED_NEW = '''_S524_CAPTURES = {}                                           # (d_from, d_to) -> (time, capture(d_from), capture(d_to)) -- one pass


def _s524_capture(con, day_iso):
    """S524 (F-848): the moment Marg's closing of a day was taken -- MAX(received_at) of that day's closing-stock pushes (stock_feed keeps
    as_on as dd-mm-yyyy; received_at and stock_voucher_entered.at are both now_iso(), string-comparable). None when the day has none."""
    day = str(day_iso or "")[:10]
    if len(day) != 10:
        return None
    try:
        r = con.execute("SELECT MAX(received_at) FROM stock_feed WHERE as_on=? AND LOWER(source) LIKE 'push_snapshot%'",
                        (day[8:10] + "-" + day[5:7] + "-" + day[0:4],)).fetchone()
        return str(r[0]) if r and r[0] else None
    except sqlite3.Error:
        return None


def _s524_captures(con, lo, hi):
    """The two captures of a window, kept for the life of one pass (filed_vouchers is called once per item); 600 s at most."""
    now = dt.datetime.now().timestamp()
    hit = _S524_CAPTURES.get((lo, hi))
    if hit and now - hit[0] < 600:
        return hit[1], hit[2]
    if len(_S524_CAPTURES) > 64:
        _S524_CAPTURES.clear()
    c_from, c_to = (_s524_capture(con, lo) if lo else None), _s524_capture(con, hi)
    _S524_CAPTURES[(lo, hi)] = (now, c_from, c_to)
    return c_from, c_to


def filed_vouchers(con, item, d_from, d_to):
    """Units of the count's vouchers for this item that Amir filed in Marg between two closings (stock_voucher_line by round and batch,
    stock_voucher_entered) -- the change Marg is EXPECTED to show without a sale or a purchase.
    S488 (F-754): stock_voucher_entered is an append-only log -- the newest row (highest id) of each (count, round, kind, batch) is the
    batch's state, and a batch counts only while that row carries a voucher number (the rule the stage proof keeps).
    S524 (F-848): a batch is judged by its MOMENT -- it counts in (d_from, d_to] when capture(d_from) < at <= capture(d_to), the captures
    being the moments Marg's closings of those days were taken (stock_feed). When EITHER capture is unknown, S488's day rule decides for
    that batch: its day is entered_on read as a date (dd-mm-yyyy, dd/mm/yyyy or ISO), else the day of `at`; it counts when
    d_from < day <= d_to (ISO days)."""
    if not (_has(con, "stock_voucher_line") and _has(con, "stock_voucher_entered")):
        return 0.0
    lo, hi = str(d_from or "")[:10], str(d_to or "")[:10]
    if not hi:
        return 0.0
    try:
        state = {}
        for cid, rno, kind, bno, vno, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                             "FROM stock_voucher_entered ORDER BY id"):
            state[(cid, rno, kind, bno)] = (vno, eon, at)
        c_from, c_to = _s524_captures(con, lo, hi)
        filed = set()
        for k, (vno, eon, at) in state.items():
            if not str(vno or "").strip():
                continue
            if c_from and c_to:
                if c_from < str(at or "") <= c_to:
                    filed.add(k)
            else:
                day = _s488_entry_day(eon, at)
                if day and lo < day <= hi:
                    filed.add(k)
        if not filed:
            return 0.0
        tot = 0.0
        for cid, rno, kind, bno, ch in con.execute("SELECT count_id, round_no, kind, batch_no, change FROM stock_voucher_line WHERE item=?", (item,)):
            if (cid, rno, kind, bno) in filed:
                tot += float(ch or 0)
        return tot
    except sqlite3.Error:
        return 0.0'''


def build_shelf_figure(t):
    once(t, "the rule _proof_state keeps", "shelf_figure comment 275")   # inside the function text that is replaced below
    return cut(t, FILED_OLD_START, FILED_OLD_END, FILED_NEW, "shelf_figure filed_vouchers")


# ============================================================================================================== stockmatch.py (2.3, F-840)
def build_stockmatch(t):
    a = ('    # 3 -- the proof, for the orthotic lines (D543: the export before the first voucher, the first after the last)\n'
         '    P = sa._proof_state(con, d)\n'
         '    iok = P.get("items_ok") or {}\n'
         '    ortho_need = sorted(i for i in iok if is_ortho(con, i))\n'
         '    bad = [i for i in ortho_need if not iok[i]]\n'
         '    if not ob:\n'
         '        c3, proof_text = True, "nothing to prove yet -- no orthotic voucher line has been made"\n'
         '    elif not P.get("as_after"):\n'
         '        c3, proof_text = False, P.get("text") or ""\n'
         '    else:\n'
         '        c3 = bool(ortho_need) and not bad\n'
         '        proof_text = ("Marg\'s export of %s: every orthotic vouchered item moved by exactly its voucher (%d)" % (P["as_after"], len(ortho_need)) if c3\n'
         '                      else "Marg\'s export of %s: %d orthotic item%s did not move by its voucher" % (P["as_after"], len(bad), "" if len(bad) == 1 else "s"))\n')
    n = ('    # 3 -- the proof, for the orthotic lines: S524 (F-840) -- the STAGE proof (stock_app.amir_stage / _s446_proof, read from the spine), the\n'
         '    #      one judgment Amir\'s card, his board, the hub and the statement all read; the pending orthotic line is c2\'s, never c3\'s\n'
         '    P = sa.amir_stage(con, root, d=d)\n'
         '    AP = ((P or {}).get("A") or {}).get("proof") or {}\n'
         '    bad = sorted({r["item"] for r in (AP.get("rows") or []) if r.get("ok") is False})\n'
         '    ortho_need = sorted(set(AP.get("proven_on") or {}) | set(bad))\n'
         '    if not ob:\n'
         '        c3, proof_text = True, "nothing to prove yet -- no orthotic voucher line has been made"\n'
         '    else:\n'
         '        c3 = P is not None and (AP.get("state") == "done" or (P["stage"] != "A" and bool(P["A"].get("verified_at"))))\n'
         '        if AP.get("state") == "done":\n'
         '            proof_text = "Marg\'s closing of %s: every orthotic vouchered key moved by exactly its vouchers (%d item%s)" % (\n'
         '                AP.get("as_after"), len(ortho_need), "" if len(ortho_need) == 1 else "s")\n'
         '        elif AP.get("state") == "wrong":\n'
         '            _nk = len({r.get("key") for r in (AP.get("rows") or [])})\n'
         '            proof_text = "Marg\'s closing of %s: %d orthotic key%s did not move by its vouchers" % (AP.get("as_after"), _nk, "" if _nk == 1 else "s")\n'
         '        elif c3:\n'
         '            proof_text = "proven (the count is past stage A)"\n'
         '        else:\n'
         '            proof_text = sa._s524_english_ending(AP) or "waiting for the closing-stock export that proves the orthotic vouchers"\n')
    t = rep(t, a, n, "stockmatch c3")
    t = rep(t, 'proof_as_after=P.get("as_after"), renames=rs.get("verified")', 'proof_as_after=AP.get("as_after"), renames=rs.get("verified")', "stockmatch basis row")
    a = '               proof=dict(state=P.get("state"), text=proof_text, as_before=P.get("as_before") or "", as_after=P.get("as_after") or "",\n'
    n = '               proof=dict(state=AP.get("state"), text=proof_text, as_before=AP.get("as_before") or "", as_after=AP.get("as_after") or "",   # S524: the stage proof\n'
    return rep(t, a, n, "stockmatch proof block")


# ============================================================================================================== amir_day.py (2.7, 2.2)
def build_amir_day(t):
    a = ('def _s446_wrong_lines(rows, numbers):\n'
         '    out = []\n'
         '    for r in rows[:12]:\n'
         '        vn = ", ".join("voucher %d" % numbers[k] for k in r.get("keys") or [] if k in numbers)\n'
         '        if r.get("marg") is None:\n'
         '            fig = "Marg ki export mein nahi mila"\n'
         '        else:\n'
         '            fig = "Marg mein %s, hona chahiye %s" % (r["marg"], r["should"] if r.get("should") is not None else "?")\n'
         '        out.append("<div class=line><span class=\'big bad\'>%s</span><br><span class=sub>%s%s</span></div>"\n'
         '                   % (_esc(r["item"]), _esc(fig), (" &middot; %s theek kijiye" % _esc(vn)) if vn else ""))\n'
         '    return "".join(out)\n')
    n = ('def _s446_wrong_lines(rows, numbers):\n'
         '    """S524 (F-843, 2.7): the words a wrong row carries -- never a figure for Amir to type, no raw integer, no \'hona chahiye\'."""\n'
         '    out = []\n'
         '    for r in rows[:12]:\n'
         '        vn = ", ".join("voucher %d" % numbers[k] for k in r.get("keys") or [] if k in numbers)\n'
         '        if r.get("marg") is None:\n'
         '            fig = "Marg ki export mein nahi mila"\n'
         '        else:\n'
         '            fig = "%s ki closing tak Marg %s badla \\u2014 voucher %s ka tha" % (r.get("closing_day") or "?", r.get("moved_hi") or "?", r.get("need_hi") or "?")\n'
         '            if r.get("family"):\n'
         '                _n = sum(1 for x in rows if x.get("key") == r.get("key"))\n'
         '                fig += " (ek hi naam ke %d size ek saath gine gaye)" % _n\n'
         '        out.append("<div class=line><span class=\'big bad\'>%s</span><br><span class=sub>%s%s</span></div>"\n'
         '                   % (_esc(r["item"]), _esc(fig), (" &middot; %s jaanch kijiye" % _esc(vn)) if vn else ""))\n'
         '    return "".join(out)\n')
    t = rep(t, a, n, "amir_day wrong lines")
    a = ('            elif pr.get("state") == "wrong":\n'
         '                lines.append("<div class=line><span class=\'big bad\'>Orthotic: Marg mein yeh abhi sahi nahi hain</span></div>"\n')
    n = ('            elif A.get("pending") and pr.get("state") == "done":          # S524 (R2-1): proven; an orthotic line still owed a voucher (the owner makes the round)\n'
         '                lines.append("<div class=line><span class=\'big good\'>Orthotic ke %d voucher Marg mein sahi &#10003;</span><br>"\n'
         '                             "<span class=sub>%s orthotic line ka naya voucher Doctor sahab banayenge &mdash; aapko abhi kuch nahi karna.</span></div>"\n'
         '                             % (int(A.get("total") or 0), "Ek" if int(A["pending"]) == 1 else "%d" % int(A["pending"])))\n'
         '            elif pr.get("state") == "wrong":\n'
         '                lines.append("<div class=line><span class=\'big bad\'>Orthotic: Marg mein yeh abhi sahi nahi hain</span></div>"\n')
    t = rep(t, a, n, "amir_day card pending branch")
    a = ('            t = ("Stage A (orthotic vouchers) %d/%d entered" % (A.get("entered", 0), A.get("total", 0)) if A.get("open") else\n'
         '                 "Stage A: all %d orthotic vouchers entered -- %s" % (A.get("total", 0), "%d item(s) still wrong in Marg" % len((A.get("proof") or {}).get("rows") or []) if pr == "wrong" else (_s488_ending(A.get("proof")) or "waiting for the closing-stock export")))   # S488 (B.3)\n')
    n = ('            t = ("Stage A (orthotic vouchers) %d/%d entered" % (A.get("entered", 0), A.get("total", 0)) if A.get("open") else\n'
         '                 ("Stage A: all %d orthotic vouchers proven on %s -- %d orthotic line(s) not yet on a voucher (make the round on the hub)"   # S524 (R2-1)\n'
         '                  % (A.get("total", 0), (A.get("proof") or {}).get("as_after") or "?", int(A.get("pending") or 0))) if (pr == "done" and A.get("pending")) else\n'
         '                 "Stage A: all %d orthotic vouchers entered -- %s" % (A.get("total", 0), "%d item(s) still wrong in Marg" % len((A.get("proof") or {}).get("rows") or []) if pr == "wrong" else (_s488_ending(A.get("proof")) or "waiting for the closing-stock export")))   # S488 (B.3)\n')
    return rep(t, a, n, "amir_day owner line")


# ============================================================================================================== stock_app.py
S524_BLOCK = r'''

# ==========================================================================================================================================
# S524_AMIR_ONE_JUDGMENT (11-Oct-2026, D706; F-843 F-844 F-845 F-846 F-847 F-848 F-840): ONE proof of Amir's vouchers, read from the spine.
#   The charter (S303): what Marg says is read from the spine; what people do (the vouchers entered) is read once; what the system concludes
#   (did the voucher reach Marg?) is computed from those two and never stored as truth. The proof here judges a KEY -- the spine's own
#   (aliases and families folded: the belt sizes, the knee supports, the wrist splints are one key each) -- on its NET across EVERY entered
#   batch in the window, against Marg's closings carried by the spine's movements: proven at a try X iff
#        close(X) - close(R) - spine_move(end_day(R), end_day(X)] - vouchers(R.stamp < at <= X.stamp)  is within 0.5
#   (a purchase keyed after R's capture but dated at or before R's day is the spine's own TIMING reading: late_purchase). R is the newest clean
#   closing captured before the first entry; the tries are the first and the newest clean closings captured after the last entry that the
#   spine's reach covers (its newest sale and purchase exports reach the closing's day and were captured after it). A closing is CLEAN by the
#   estate's one capture-hour rule (push_expected._gap_side): captured on a later day than it is printed for, or on its own day at/after
#   22:00 (end_day = the printed day), or on its own day before 09:00 (it stands for the end of the day before); a same-day capture inside
#   shop hours is skipped. Every day SHOWN is the closing's printed as_on, dd-mm-yyyy.
#   Verdicts per key: proven = ok at any try; wrong = not proven and False at every try that gave one; no verdict otherwise (an `unseen`
#   row, printed by nothing). rows carries the ok=False rows ONLY. No row carries a figure for Amir to type (should=None): the words are the
#   row's own (qty_words, Hindi), and amir_day prints them. The stock_feed look is for the REASON only (S488's own rule), never the verdict.
#   Stage A is re-derived from its inputs on every read (F-844): open while a voucher is open, an orthotic line is still owed a voucher
#   (A["pending"]), or the proof is not done; the stored 'A verified' event is a record. The old whole-count proof (_proof_state,
#   _proof_pur_to, _proof_basis) is retired: hub step 7, the board's extra and stockmatch read the stage.
# ==========================================================================================================================================
S524_KIT = "S524_AMIR_ONE_JUDGMENT"
S524_MOVE_KINDS = ("SALE", "SALE_RETURN", "PURCHASE", "PURCHASE_RETURN", "RECONCILIATION")      # never OPENING
_S524_REPORT_CACHE = {}                                         # root -> (time, input stamp, the report)


def _report_cached(con, cid):
    """S524 (2.2): _pad_report_data for ONE root, kept in this process while its inputs stand -- the stamp is (MAX(id) of stock_shelf_fix,
    MAX(round_no) of the root's voucher lines, MAX(received_at) of stock_feed) -- and 600 s at most. Read by amir_stage (when no report is
    passed) and by _s444_renames. NEVER handed to a route (api_pad_report writes into its d) and never written into."""
    try:
        root, _fam, R = _pad_family(con, cid)
    except Exception:                                          # noqa: BLE001
        return None
    if R is None:
        return None

    def one(sql, *a):
        try:
            r = con.execute(sql, a).fetchone()
            return r[0] if r else None
        except Exception:                                      # noqa: BLE001
            return None
    stamp = (one("SELECT MAX(id) FROM stock_shelf_fix"), one("SELECT MAX(round_no) FROM stock_voucher_line WHERE count_id=?", int(root)),
             one("SELECT MAX(received_at) FROM stock_feed"))
    now = dt.datetime.now().timestamp()
    hit = _S524_REPORT_CACHE.get(int(root))
    if hit and hit[1] == stamp and now - hit[0] < 600:
        return hit[2]
    d = _pad_report_data(con, int(root))
    _S524_REPORT_CACHE[int(root)] = (now, stamp, d)
    return d


def _s524_dmy(iso):
    s = str(iso or "")
    return ("%s-%s-%s" % (s[8:10], s[5:7], s[0:4])) if len(s) >= 10 and s[4] == "-" else s


def _s524_spine():
    """The spine through stock_watch's door (path _sw.SPINE_DB, read from the environment once at import); None when it cannot be read."""
    try:
        sp = _sw.Spine() if (STOCK_WATCH_OK and _sw is not None) else None
    except Exception:                                          # noqa: BLE001
        sp = None
    return sp if (sp is not None and getattr(sp, "ok", False)) else None


def _s524_built(sp):
    try:
        return str((sp.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
    except Exception:                                          # noqa: BLE001
        return ""


def _s524_stamp_iso(stamp):
    """'YYYYMMDD-HHMMSS' -> 'YYYY-MM-DDTHH:MM:SS' (exactly as marg_take.py reads a capture); '' when it is not a stamp."""
    s = str(stamp or "")
    if not _re221.match(r"^\d{8}-\d{6}$", s):
        return ""
    return "%s-%s-%sT%s:%s:%s" % (s[0:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])


def _s524_end_day(as_on, stamp_iso):
    """push_expected._gap_side as the one capture-hour rule: the day whose END the closing's figure stands for, or None when the capture
    fell inside that day's shop hours (a same-day print between 09:00 and 22:00; a print dated after its capture) -- then it is skipped."""
    sd, hm = str(stamp_iso)[:10], str(stamp_iso)[11:16]
    if len(sd) != 10 or len(str(as_on)) != 10:
        return None
    if as_on < sd:                                             # printed for an earlier day: the whole day was before the capture
        return as_on
    if as_on > sd:
        return None
    if hm >= "22:00":
        return as_on
    if hm < "09:00":
        try:
            return (dt.date.fromisoformat(as_on) - dt.timedelta(days=1)).isoformat()
        except ValueError:
            return None
    return None


def _s524_closings(sp):
    """[{as_on, stamp, stamp_iso, end_day}] -- every closing the spine holds (one per printed day, admitted by the spine's own rule), with its
    export's capture; a clean one carries end_day, a mid-day capture None. No second 'whole' bar is computed here (R1-B7)."""
    out = []
    for r in sp.q("SELECT c.as_on AS as_on, e.stamp AS stamp FROM (SELECT DISTINCT as_on, source_md5 FROM sp_close) c "
                  "JOIN sp_export e ON e.md5 = c.source_md5 ORDER BY c.as_on, e.stamp"):
        si = _s524_stamp_iso(r["stamp"])
        out.append(dict(as_on=str(r["as_on"]), stamp=str(r["stamp"] or ""), stamp_iso=si, end_day=(_s524_end_day(str(r["as_on"]), si) if si else None)))
    return out


def _s524_reach(sp):
    """{last_sale, sale_stamp, last_pur, pur_stamp}: last_sale = MAX(date_to) over ok=1 SALE_BILLWISE; last_pur = MIN of MAX(date_to) over ok=1
    PURCHASE_BILLWISE and over ok=1 PURCHASE_ITEMWISE|PURCHASE_BILLITEMWISE (spine_build.py 377-378); the stamps are those newest exports'."""
    def last(fam_sql):
        return str(sp.q("SELECT MAX(date_to) AS d FROM sp_export WHERE ok=1 AND " + fam_sql)[0]["d"] or "")

    def stamp_of(fam_sql, d):
        return str(sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND date_to=? AND " + fam_sql, d)[0]["s"] or "") if d else ""
    S, B, I = "family='SALE_BILLWISE'", "family='PURCHASE_BILLWISE'", "family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')"
    ls, lb, li = last(S), last(B), last(I)
    lp = min(lb, li) if (lb and li) else ""
    return dict(last_sale=ls, sale_stamp=stamp_of(S, ls), last_pur=lp, pur_stamp=(min(stamp_of(B, lb), stamp_of(I, li)) if lp else ""))


def _s524_tryable(c, reach):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): last_sale and last_pur at or past its end_day, and
    both newest exports captured after it. short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach:
        return False, "sale"
    if reach["last_sale"] < d or reach["sale_stamp"] <= c["stamp"]:
        return False, "sale"
    if not reach["last_pur"] or reach["last_pur"] < d or reach["pur_stamp"] <= c["stamp"]:
        return False, "pur"
    return True, ""


def _s524_mixed(sp):
    """The keys the spine's gate lists as printed both as packs:loose and as a plain figure -- skipped (why='mixed')."""
    try:
        import ast                                             # noqa: PLC0415
        r = sp.q("SELECT detail FROM sp_gate WHERE name LIKE 'no item is printed both%'")
        v = ast.literal_eval(str(r[0]["detail"] or "[]")) if r else []
        return set(str(x) for x in v) if isinstance(v, (list, tuple)) else set()
    except Exception:                                          # noqa: BLE001
        return set()


def _s524_key_of(sp, item, cache):
    """The spine's own key of an item: sp_item's k20 for the name (one row expected), else sp.key(name) -- never bare K() (R1-B1)."""
    if item in cache:
        return cache[item]
    try:
        r = sp.q("SELECT DISTINCT k20 FROM sp_item WHERE name=?", item)
        k = str(r[0]["k20"]) if r else sp.key(item)
    except Exception:                                          # noqa: BLE001
        k = sp.key(item)
    cache[item] = k
    return k


def _s524_table(con, sp, root, ent, batches, first_at, last_at):
    """The per-key judgment table of one root for the window of these entries: R, after, the tries, and for every key of every entered batch
    in the window its verdict at each try (both tries). Cached by _s446_proof per (root, every entered (key, at), first_at, last_at, built,
    SPINE_DB); each call then filters the rows for ITS keys (stage C calls once per lot)."""
    closings = _s524_closings(sp)
    clean = [c for c in closings if c["end_day"]]
    before = [c for c in clean if c["stamp_iso"] < first_at]
    R = max(before, key=lambda c: (c["as_on"], c["stamp_iso"])) if before else None
    after = sorted([c for c in clean if c["stamp_iso"] > last_at], key=lambda c: (c["stamp_iso"], c["as_on"]))
    T = dict(R=R, after=after, tries=[], keys={}, kof={}, reach=None, mixed=set(), closings=closings)
    if R is None or not after:
        return T
    reach = _s524_reach(sp)
    T["reach"] = reach
    # the tries: the FIRST clean closing after the vouchers and the NEWEST one the spine's reach covers (S520's first-or-newest, read with
    # R1-B2: a purchase export captured before the newest closing would otherwise pin the judgment to the first closing for days)
    tryable = [c for c in after if _s524_tryable(c, reach)[0]]
    tries = []
    if tryable and tryable[0] is after[0]:
        tries.append(after[0])
        if tryable[-1] is not after[0]:
            tries.append(tryable[-1])
    T["tries"] = tries
    if not tries:
        return T
    mixed = _s524_mixed(sp)
    T["mixed"] = mixed
    kof = {}
    for b in batches.values():
        for item, _ch, _m in b["lines"]:
            _s524_key_of(sp, item, kof)
    T["kof"] = kof

    def close_of(c):
        return {str(r["k20"]): float(r["units"] or 0) for r in sp.q("SELECT k20, units FROM sp_close WHERE as_on=?", c["as_on"])}
    cR = close_of(R)
    first_seen = {str(r["k20"]): str(r["f"] or "") for r in sp.q("SELECT k20, MIN(first_seen) AS f FROM sp_item GROUP BY k20")}
    late = {}
    try:
        d21 = (dt.date.fromisoformat(R["end_day"]) - dt.timedelta(days=21)).isoformat()
        for r in sp.q("SELECT k20, units FROM sp_move WHERE kind IN ('PURCHASE','PURCHASE_RETURN') AND date >= ? AND date <= ?", d21, R["end_day"]):
            late.setdefault(str(r["k20"]), []).append(float(r["units"] or 0))
    except ValueError:
        pass
    keys = {}
    for X in tries:
        need, vn, items_of = {}, {}, {}
        for kb, b in batches.items():
            if kb not in ent:
                continue
            at = str(ent[kb][1] or "")[:19]
            if R["stamp_iso"] < at <= X["stamp_iso"]:
                for item, ch, _m in b["lines"]:
                    k = kof[item]
                    need[k] = need.get(k, 0) + int(ch)
                    vn.setdefault(k, []).append(kb)
                    items_of.setdefault(k, set()).add(item)
        cX = close_of(X)
        mv = {}
        for r in sp.q("SELECT k20, units FROM sp_move WHERE date > ? AND date <= ? AND kind IN (%s)" % ",".join("?" * len(S524_MOVE_KINDS)),
                      R["end_day"], X["end_day"], *S524_MOVE_KINDS):
            mv[str(r["k20"])] = mv.get(str(r["k20"]), 0.0) + float(r["units"] or 0)
        for k in need:
            e = keys.setdefault(k, dict(tries=[], items=set()))
            e["items"] |= items_of[k]
            t = dict(X=X, need=need[k], vouchers=list(vn[k]), ok=None, late=None)
            if k in mixed:
                t["why"] = "mixed"
            elif k not in cX:
                t["why"] = "absent_at_try"
            else:
                if k in cR:
                    r0 = cR[k]
                elif first_seen.get(k, "") > R["as_on"]:
                    r0 = 0.0
                else:
                    r0 = None
                if r0 is None:
                    t["why"] = "absent_before"
                else:
                    marg_move = cX[k] - r0
                    spine_move = mv.get(k, 0.0)
                    res = marg_move - spine_move - need[k]
                    ok, lp = abs(res) < 0.5, None
                    if not ok:
                        pl = late.get(k, [])
                        for u in pl:
                            if abs(res - u) < 0.5:
                                ok, lp = True, u
                                break
                        if not ok:
                            for i in range(len(pl)):
                                for j in range(i + 1, len(pl)):
                                    if abs(res - pl[i] - pl[j]) < 0.5:
                                        ok, lp = True, pl[i] + pl[j]
                                        break
                                if ok:
                                    break
                    t.update(ok=ok, late=lp, marg_move=marg_move, spine_move=spine_move, res=res, marg=cX[k])
            e["tries"].append(t)
    for k, e in keys.items():
        given = [t for t in e["tries"] if t["ok"] is not None]
        prov = [t for t in given if t["ok"]]
        e["proven"], e["wrong"] = bool(prov), (bool(given) and not prov)
        e["L"] = prov[0] if prov else (given[-1] if given else (e["tries"][-1] if e["tries"] else None))
    T["keys"] = keys
    return T


def _s524_verdict(con, sp, T, keys, batches, last_at):
    """The proof for THESE keys from the table: state, rows (ok=False only), unseen (ok=None), as_before, as_after, last_at, items, proven_on."""
    R, tries, after = T["R"], T["tries"], T["after"]
    base = dict(rows=[], unseen=[], last_at=last_at, items=0, proven_on={}, text="")
    if R is None or not tries:
        res = dict(base, state="export")
        res.update(_s488_why(con, sp, T["closings"], R, after, last_at))
        return res
    L = tries[-1]
    kof = T["kof"]
    _whole_units_load(con)
    items = {}
    for kb in keys:
        b = batches.get(kb) or {}
        for item, ch, _m in b.get("lines") or []:
            e = items.setdefault(item, dict(need=0, pk=(b.get("pk") or {}).get(item, ("", None))))
            e["need"] += int(ch)
    rows, unseen, proven_on = [], [], {}

    def wd(fn, v, item, pk):
        if v is None or _qty is None:
            return None
        try:
            return fn(v, packing=(pk[0] or None), pack=pk[1], name=item, lang="hi")
        except Exception:                                      # noqa: BLE001
            return None
    for item in sorted(items):
        k = kof.get(item) or item
        e = T["keys"].get(k)
        t = (e or {}).get("L")
        ok = True if (e and e["proven"]) else (False if (e and e["wrong"]) else None)
        X = (t or {}).get("X") or L
        marg = (t or {}).get("marg")
        moved = ((t["marg_move"] - t["spine_move"]) if (t and "marg_move" in t) else None)
        need_key = (t or {}).get("need")
        pk = items[item]["pk"]
        row = dict(item=item, key=k, family=bool(e and len(e["items"]) > 1), need=items[item]["need"], need_key=need_key, moved=moved, marg=marg,
                   keys=[_s446_key(x) for x in ((t or {}).get("vouchers") or [])], ok=ok, closing_day=_s524_dmy(X["as_on"]),
                   late_purchase=(t or {}).get("late"), packing=pk[0], pack=pk[1], should=None,
                   marg_hi=wd(_qty.words if _qty else None, marg, item, pk), moved_hi=wd(_qty.signed if _qty else None, moved, item, pk),
                   need_hi=wd(_qty.signed if _qty else None, need_key, item, pk))
        if ok is True:
            proven_on[item] = _s524_dmy(X["as_on"])
        elif ok is False:
            rows.append(row)
        else:
            unseen.append(dict(row, why=((t or {}).get("why") or "no_verdict")))
    state = "done" if (not rows and not unseen) else ("wrong" if rows else "export")
    res = dict(base, state=state, rows=rows, unseen=unseen, items=len(items), proven_on=proven_on, as_before=_s524_dmy(R["as_on"]),
               as_after=_s524_dmy(L["as_on"]))
    if state == "export":
        res.update(_s488_why(con, sp, T["closings"], R, after, last_at))
    return res


def _s524_english_ending(pr):
    """The owner's English ending for a waiting proof (amir_day._s488_ending's words); '' when it cannot be had."""
    try:
        import amir_day as _ad                                 # noqa: PLC0415 -- beside this file; it imports stock_app lazily
        return _ad._s488_ending(pr) or ""
    except Exception:                                          # noqa: BLE001
        return ""


def _s524_hub_proof(con, root, d):
    """Hub step 7 (stock_hub.html 174-179) from the stage: state done|now|wait, text (English), rows (the ok=False rows with a why),
    moved_without=0, plus stage, A, B, C -- the same judgment Amir's card reads."""
    try:
        st = amir_stage(con, root, d=d)
    except Exception as e:                                     # noqa: BLE001
        return dict(state="wait", text="The stage could not be read: %s" % str(e)[:120], rows=[], moved_without=0, stage=None, A={}, B={}, C={})
    if not st:
        return dict(state="wait", text="Waits for the vouchers: no voucher round has been made yet.", rows=[], moved_without=0, stage=None, A={}, B={}, C={})
    stage, A, B, C = st.get("stage"), st.get("A") or {}, st.get("B") or {}, st.get("C") or {}
    AP = A.get("proof") or {}

    def why(r):
        if r.get("marg") is None:
            return "not in Marg's closing of %s" % (r.get("closing_day") or "?")
        return "Marg moved %+d, the vouchers say %+d" % (int(round(r.get("moved") or 0)), int(round(r.get("need_key") or 0)))

    def wrong_rows(rs):
        return [dict(item=r["item"], ok=False, why=why(r), key=r.get("key"), closing_day=r.get("closing_day")) for r in rs or []]
    rows = []
    if stage == "A":
        if int(A.get("open") or 0) > 0:
            state, text = "wait", "Stage A: %d of %d entered" % (int(A.get("entered") or 0), int(A.get("total") or 0))
        elif AP.get("state") == "done":
            state = "done"
            text = "Marg's export of %s: every orthotic vouchered key moved by exactly its vouchers" % AP.get("as_after")
            if int(A.get("pending") or 0) > 0:
                text += " -- %d orthotic line(s) not yet on a voucher (make the round)" % int(A["pending"])
        elif AP.get("state") == "wrong":
            rows = wrong_rows(AP.get("rows"))
            state, text = "now", "Marg's export of %s: %d key(s) did not move by their vouchers" % (AP.get("as_after"), len({r.get("key") for r in rows}))
        else:
            state, text = "wait", (_s524_english_ending(AP) or "Vouchers entered; waiting for the closing-stock export that proves them")
    elif stage == "B":
        state, text = "done", "Stage A proven on %s; stage B: %d of %d orthotic renames seen in Marg" % (A.get("verified_at") and str(A.get("verified_at"))[:10] or "?", int(B.get("verified") or 0), int(B.get("total") or 0))
    elif stage == "C":
        if C.get("wrong"):
            rows = wrong_rows(C.get("wrong"))
            state, text = "now", "Stage C: %d key(s) of the released lots did not move by their vouchers" % len({r.get("key") for r in rows})
        elif C.get("waiting_export"):
            state, text = "wait", (_s524_english_ending(((C.get("waiting_export") or [{}])[0] or {}).get("proof")) or "Stage C: a lot's vouchers entered; waiting for the closing-stock export")
        else:
            state, text = "done", "Stage C: %d of %d medicine vouchers entered, %d released, %d verified" % (int(C.get("entered") or 0), int(C.get("total") or 0), int(C.get("released") or 0), int(C.get("verified") or 0))
    else:
        state, text = "done", "All vouchers entered and verified"
    return dict(state=state, text=text, rows=rows, moved_without=0, stage=stage, A=A, B=B, C=C)
# ---- S524_AMIR_ONE_JUDGMENT end -----------------------------------------------------------------------------------------------------------
'''

NEW_BATCHES = '''def _s446_batches(con, root):
    """{(round, kind, batch): {secs, lines: [(item, change, marg_to)], made, pk: {item: (packing, pack)}}} for one count.
    S524: pk carries the frozen line's packing and pack size, for the words of a proof row."""
    _voucher_ensure(con)
    out = {}
    for rno, kind, bno, sec, item, ch, mto, made, pk, pn in con.execute(
            "SELECT round_no, kind, batch_no, section, item, change, marg_to, made_at, packing, pack FROM stock_voucher_line WHERE count_id=? "
            "ORDER BY round_no, kind, batch_no, line_no", (root,)):
        b = out.setdefault((rno, kind, bno), dict(secs=set(), lines=[], made=made, pk={}))
        b["secs"].add(sec or "")
        b["lines"].append((item, int(ch or 0), int(mto or 0)))
        b["pk"].setdefault(item, (pk or "", int(pn) if pn else None))
    return out
'''

OLD_BATCHES = '''def _s446_batches(con, root):
    """{(round, kind, batch): {secs, lines: [(item, change, marg_to)], made}} for one count."""
    _voucher_ensure(con)
    out = {}
    for rno, kind, bno, sec, item, ch, mto, made in con.execute(
            "SELECT round_no, kind, batch_no, section, item, change, marg_to, made_at FROM stock_voucher_line WHERE count_id=? "
            "ORDER BY round_no, kind, batch_no, line_no", (root,)):
        b = out.setdefault((rno, kind, bno), dict(secs=set(), lines=[], made=made))
        b["secs"].add(sec or "")
        b["lines"].append((item, int(ch or 0), int(mto or 0)))
    return out
'''

NEW_PROOF = '''def _s446_proof(con, root, keys, ent, batches):
    """S524: ONE proof, read from the spine, over THESE batches' lines -- wait (not all entered) | export (no verdict yet: the reason in
    `why`) | done (every key proven) | wrong (rows named, ok=False only). Keys sharing a spine key are judged as one key on their net
    (F-843). The per-key table is cached 5 minutes per (root, every entered (key, at), first_at, last_at, built, SPINE_DB); each call
    filters it for its keys. Returns state, rows, unseen, as_before, as_after, last_at, items, proven_on; on export also since, why,
    closing_day, closing_at."""
    keys = list(keys)
    if not keys or any(k not in ent for k in keys):
        return dict(state="wait", rows=[], text="")
    first_at = min(ent[k][1] for k in keys)[:19]
    last_at = max(ent[k][1] for k in keys)[:19]
    sp = _s524_spine()
    if sp is None:
        return dict(state="export", rows=[], unseen=[], last_at=last_at, since=last_at, why="no_figure", items=0, proven_on={},
                    text="the spine is not readable")
    try:
        built = _s524_built(sp)
        stamp = tuple(sorted((_s446_key(k), str(v[1])) for k, v in ent.items()))
        ck = (root, stamp, first_at, last_at, built, str(getattr(_sw, "SPINE_DB", "") or ""))
        now = dt.datetime.now().timestamp()
        hit = _S446_PROOF_CACHE.get(ck)
        if hit and now - hit[0] < 300:
            T = hit[1]
        else:
            T = _s524_table(con, sp, root, ent, batches, first_at, last_at)
            _S446_PROOF_CACHE[ck] = (now, T)
        return _s524_verdict(con, sp, T, keys, batches, last_at)
    finally:
        try:
            sp.con.close()
        except Exception:                                      # noqa: BLE001
            pass
'''

NEW_STAGE = '''def _s524_stage_b(con, root):
    """Stage B's reading (S446), in one place: the renames' state and the once-only 'B verified' event."""
    B = dict(total=0, verified=0, ticked=0, open=[], old=[], verified_at=_s446_event(con, root, "B", "verified"))
    try:
        import item_alias                                      # noqa: PLC0415
        rows = item_alias.rows(con)
        B["total"] = len(rows)
        B["verified"] = sum(1 for r in rows if r.get("state") == "verified")
        B["ticked"] = sum(1 for r in rows if r.get("state") in ("done", "amber", "verified"))
        B["open"] = [r["old_name"] for r in rows if r.get("state") == "planned"]
        B["old"] = [r["old_name"] for r in rows if r.get("state") == "amber"]
        if rows and B["verified"] == len(rows) and not B["verified_at"] and _s446_mark(con, root, "B", "verified"):
            B["verified_at"] = _s446_event(con, root, "B", "verified")
    except Exception:                                          # noqa: BLE001
        pass
    return B


def amir_stage(con, cid=None, d=None):
    """Where the count stands for Amir: {count_id, stage A|B|C|done, A, B, C, visible (keys his board lists), renames_visible,
    numbers {key: n}}. Writes only stock_stage_event (a verification seen, a recheck, a lot released) -- once each.
    S524 (F-844): stage A is RE-DERIVED from its inputs on every read -- open while a voucher is open, an orthotic line is still owed a
    voucher (A["pending"], from the report's own pending lines), or the proof over the orthotic batches is not done; the stored
    'A verified' event is a record and no longer decides. `d` is the report when the caller holds it (the hub, stockmatch); else the
    cached one (_report_cached). Renames once released stay with him (R2-2): with an 'A verified' event, renames_visible is stage B's
    reading even while A is open again."""
    _s446_ensure(con)
    root = int(cid) if cid else _s446_root(con)
    if not root:
        return None
    batches = _s446_batches(con, root)
    if not batches:
        return None
    ent = _s446_entered(con, root)
    ortho = _s446_order([k for k, b in batches.items() if "Orthotics" in b["secs"]])
    med = sorted([k for k in batches if k not in set(ortho)], key=lambda k: (k[0], k[1] != "ISSUE", k[2]))   # oldest round first
    out = dict(count_id=root, stage="A", visible=[], renames_visible=False, numbers={})
    # ---- A
    a_open = [k for k in ortho if k not in ent]
    A = dict(total=len(ortho), entered=len(ortho) - len(a_open), open=len(a_open), pending=0, proof=None,
             verified_at=_s446_event(con, root, "A", "verified"))
    rep = d if d is not None else _report_cached(con, root)
    if rep is not None:
        try:
            A["pending"] = len(_voucher_pending(con, rep, section="Orthotics"))
        except Exception:                                      # noqa: BLE001
            A["pending"] = 0
    if ortho and not a_open:
        A["proof"] = _s446_proof(con, root, ortho, ent, batches)   # cached; a new closing (a new spine build) re-asks
    AP = A["proof"] or {}
    if ortho and AP.get("state") == "done" and not A["verified_at"] and _s446_mark(con, root, "A", "verified", detail=AP.get("as_after")):
        A["verified_at"] = _s446_event(con, root, "A", "verified")
    a_is_open = bool(ortho) and (bool(a_open) or int(A["pending"] or 0) > 0 or AP.get("state") != "done")
    if A["verified_at"] and a_is_open:                         # S524: A open again after its verification -- one recheck event per distinct ref
        ref = (",".join(_s446_key(k) for k in a_open) if a_open else
               ("pending:%d" % int(A["pending"]) if int(A["pending"] or 0) > 0 else str(AP.get("as_after") or AP.get("state") or "")))
        _s446_mark(con, root, "A", "recheck", ref, detail=str(AP.get("state") or ""))
    out["A"] = A
    if a_is_open:
        out["visible"] = ortho                                 # every orthotic batch, entered or not (the page ticks the entered ones)
        out["numbers"] = {_s446_key(k): i + 1 for i, k in enumerate(ortho)}
        if A["verified_at"]:
            B = _s524_stage_b(con, root)
            out["B"] = B
            out["renames_visible"] = not B["verified_at"]
        return out
    # ---- B
    out["stage"] = "B"
    B = _s524_stage_b(con, root)
    out["B"] = B
    if not B["verified_at"]:
        out["renames_visible"] = True
        return out
    # ---- C
    out["stage"] = "C"
    per = max(1, _s446_setting(con, "amir.vouchers_per_visit", 12))   # S452: 12 a visit (the owner, 02-Oct)
    lots = [dict(at=r[0], keys=[_s446_unkey(x) for x in (r[1] or "").split(",") if x]) for r in con.execute(
        "SELECT at, ref FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release' ORDER BY id", (root,))]
    released = {k for l in lots for k in l["keys"]}
    def release_next():
        nxt = [k for k in med if k not in released and k not in ent][:per]
        if nxt:
            _s446_mark(con, root, "C", "release", ",".join(_s446_key(k) for k in nxt))
            lots.append(dict(at=now_iso(), keys=nxt))
            released.update(nxt)
    if not lots:
        release_next()
    for l in lots:
        ek = [k for k in l["keys"] if k in ent]               # S452: every export checks whatever he has entered so far
        l["proof"] = _s446_proof(con, root, ek, ent, batches) if ek else dict(state="wait", rows=[])
        l["verified"] = len(ek) == len(l["keys"]) and l["proof"]["state"] == "done"
        if l["verified"]:
            _s446_mark(con, root, "C", "verified", ",".join(_s446_key(k) for k in l["keys"]))
    cur = lots[-1] if lots else None
    if cur and (cur["verified"] or len(_s446_visits_since(con, cur["at"])) >= 1):   # S452: the next visit opens the next lot, proved or not
        before = len(lots)
        release_next()
        if len(lots) > before:
            lots[-1]["proof"], lots[-1]["verified"] = dict(state="wait", rows=[]), False
    vis = [k for l in lots if not l["verified"] for k in l["keys"]]
    C = dict(total=len(med), entered=sum(1 for k in med if k in ent), per=per,
             today=[k for k in (lots[-1]["keys"] if lots else []) if k not in ent],
             open=len([k for k in vis if k not in ent]), unreleased=len([k for k in med if k not in released and k not in ent]),
             waiting_export=[l for l in lots if not l["verified"] and l["proof"]["state"] == "export"],
             wrong=[r for l in lots if not l["verified"] for r in l["proof"].get("rows", [])],
             lot_at=(lots[-1]["at"] if lots else None), lots=len(lots),
             released=len([k for k in med if k in released]), verified=sum(len(l["keys"]) for l in lots if l["verified"]))   # S452
    out["C"] = C
    out["visible"] = _s446_order(vis)
    out["numbers"] = {_s446_key(k): i + 1 for i, k in enumerate(out["visible"])}
    if not med or (C["entered"] == len(med) and not vis):
        out["stage"] = "done"
    return out
'''

NEW_WHY = '''def _s488_why(con, sp, closings, R, after, last_at):
    """{since, why, closing_day, closing_at} for a proof in state export -- the REASON, never the decision; {} when it cannot be had.
    why: no_before (no clean closing before the first entry) | no_figure (a clean closing came but the spine's reach -- its newest sale
    export -- does not cover it yet; or Marg's closing was pushed (stock_feed) and the spine does not hold it yet, or skipped it as a
    mid-day capture) | pur_behind (the purchase exports do not reach it) | no_closing (nothing after the vouchers, anywhere). S524: the
    stock_feed look here is for the REASON only -- never the verdict (S488's own rule). `rebased` is never produced any more."""
    try:
        out = dict(since=last_at)
        c = None
        if R is None:
            why, c = "no_before", (after[0] if after else None)
        elif after:
            c = after[0]
            _ok, short = _s524_tryable(c, _s524_reach(sp))
            why = "pur_behind" if short == "pur" else "no_figure"
        else:
            lk = str(last_at)[:10].replace("-", "")
            push = None
            for day, src, at in con.execute("SELECT as_on, source, MIN(received_at) FROM stock_feed WHERE substr(received_at,1,19) > ? "
                                            "GROUP BY as_on, source", (str(last_at or "")[:19],)):
                if _feed_kind(src) != "marg" or _proof_day_key(day) < lk or not at:
                    continue
                if push is None or (_proof_day_key(day), str(at)) < (_proof_day_key(push[0]), push[1]):
                    push = (str(day), str(at))
            if push:
                why = "no_figure"
                out["closing_day"] = push[0]
                out["closing_at"] = _s488_first_push(con, push[0], last_at, push[1])
            else:
                why = "no_closing"
        out["why"] = why
        if c is not None:
            out["closing_day"] = _s524_dmy(c["as_on"])
            out["closing_at"] = _s488_first_push(con, out["closing_day"], last_at, c.get("stamp_iso") or None)
        return out
    except Exception:                                          # noqa: BLE001 -- the reason is a help: without it the card says today's words
        return {}
'''

NEW_BOARD_EXTRA = '''    # (c) Naam badlo -- S437's gate is the STAGE's (S521 / S524, R1-B21): stage B, C or done, or renames once released (R2-2); one amir_stage
    #     call. The rounds' order stays for the record. The owner: "if he sees them before, he might do the corrections earlier and spoil our flow".
    try:
        vm = _voucher_state(con, d)
        ortho_rounds = [r for r in vm["rounds"] if r["batches"] and all((b.get("sections") or []) == ["Orthotics"] for b in r["batches"])]
        earlier = [r for r in vm["rounds"] if r not in ortho_rounds]
        _st = amir_stage(con, root, d=d)
        out["renames_ready"] = bool(_st and (_st.get("stage") in ("B", "C", "done") or _st.get("renames_visible")))
        out["renames_wait_hi"] = "" if out["renames_ready"] else "Naam badalna — baad mein, jab Marg aur shelf mil jaayein"
        order = sorted(earlier, key=lambda r: -r["round_no"]) + sorted(ortho_rounds, key=lambda r: r["round_no"])
        out["rounds_order"] = [r["round_no"] for r in order]
    except Exception:                                          # noqa: BLE001
        pass
    # (2) the closing-stock proof line: written by _s521_stage_proof for every login (S524 retired the second judgment that stood here)
    out["proof_state"], out["proof_hi"] = "", ""
'''

OLD_BOARD_EXTRA = '''    # (c) Naam badlo -- S437: ONLY after the proof is green (Marg = shelf reached for this count, hub step 5 DONE); the owner: "if he sees
    #     them before, he might do the corrections earlier and spoil our flow". The rounds' order stays for the record.
    try:
        vm = _voucher_state(con, d)
        ortho_rounds = [r for r in vm["rounds"] if r["batches"] and all((b.get("sections") or []) == ["Orthotics"] for b in r["batches"])]
        earlier = [r for r in vm["rounds"] if r not in ortho_rounds]
        out["renames_ready"] = (_proof_state(con, d).get("state") == "done")
        out["renames_wait_hi"] = "" if out["renames_ready"] else "Naam badalna — baad mein, jab Marg aur shelf mil jaayein"
        order = sorted(earlier, key=lambda r: -r["round_no"]) + sorted(ortho_rounds, key=lambda r: r["round_no"])
        out["rounds_order"] = [r["round_no"] for r in order]
    except Exception:                                          # noqa: BLE001
        pass
    # (2) the closing-stock proof, in Hindi
    try:
        P2 = _proof_state(con, d)
        out["proof_state"] = P2.get("state") or ""
        if P2.get("as_after"):
            bad = [r["item"] for r in (P2.get("rows") or []) if not r.get("ok")]
            out["proof_hi"] = "Marg = shelf: %d of %d · %d to correct%s" % (P2.get("agree", 0), P2.get("items", 0), len(bad), (": " + ", ".join(bad[:6])) if bad else "")
        elif P2.get("state") == "wait":
            out["proof_hi"] = "Abhi baaki — pehle voucher Marg mein daaliye"
        else:
            out["proof_hi"] = "Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye"
            try:                                               # S488 (B.2b): the closing has come -- say what is awaited instead
                _t488 = _s488_tail_hi(_s488_stage_proof(amir_stage(con, d["count_id"])))
            except Exception:                                  # noqa: BLE001
                _t488 = ""
            if _t488:
                out["proof_hi"] = "Abhi baaki — " + _t488
    except Exception:                                          # noqa: BLE001
        out["proof_hi"] = "Abhi baaki"
'''


def build_stock_app(t):
    # 2.4 the door (F-845)
    a = ('    if not r or not r[1]:\n'
         '        return jsonify(ok=False, error="no_such_voucher", message="No such voucher in round %d." % rno), 400\n'
         '    at, who = now_iso(), (u or {}).get("user") or ""\n')
    n = ('    if not r or not r[1]:\n'
         '        return jsonify(ok=False, error="no_such_voucher", message="No such voucher in round %d." % rno), 400\n'
         '    if not _has_role(u, "checker"):                           # S524 (F-845): a login that is not the checker may enter (or clear) only a\n'
         '        try:                                                  # voucher the stage has released to him -- amir_stage\'s visible; fail closed\n'
         '            _st = amir_stage(con, _root)\n'
         '            _vis = set(tuple(k) for k in ((_st or {}).get("visible") or [])) if _st else set()\n'
         '        except Exception:                                     # noqa: BLE001\n'
         '            _vis = set()\n'
         '        if (int(rno), str(kind).upper(), int(bno)) not in _vis:\n'
         '            return jsonify(ok=False, error="not_released", message="Yeh voucher abhi aapke liye khula nahi hai."), 403\n'
         '    at, who = now_iso(), (u or {}).get("user") or ""\n')
    t = rep(t, a, n, "stock_app entered door")
    # 2.3 the old proof retired: the S304 header, the three functions, the hub's call
    a = ('# S304 THE PROOF -- step 7 of the stock check: "the next Marg stock export after the vouchers must\n'
         '# read shelf plus movement". Movement is not ours to guess, so the test is the one the server can\n')
    n = ('# S304 THE PROOF -- step 7 of the stock check. S524 (D706): _proof_state, _proof_pur_to and _proof_basis are RETIRED -- the one\n'
         '# judgment is the stage proof (_s446_proof, read from the spine; hub step 7 reads _s524_hub_proof); only _proof_day_key stays, for its\n'
         '# three callers. The S304 words, for the record: "the next Marg stock export after the vouchers must\n'
         '# read shelf plus movement". Movement is not ours to guess, so the test is the one the server can\n')
    t = rep(t, a, n, "stock_app S304 header")
    t = cut(t, "\n\ndef _proof_pur_to(source):\n", "\n\n\n# ---------------------------------------------------------------------------\n# S308 WHAT DARPAN IS ASKED",
            "\n\n# (S524: _proof_pur_to, _proof_basis and the whole-count proof stood here until 11-Oct-2026 -- retired; see the S524 block at the end.)",
            "stock_app old proof functions")
    a = '                proof=_proof_state(con, d),                        # S304: the vouchers and Marg\'s next export, not the counting close\n'
    n = '                proof=_s524_hub_proof(con, root, d),               # S304 / S524: the stage proof (amir_stage), read from the spine -- one judgment\n'
    t = rep(t, a, n, "stock_app hub proof")
    t = rep(t, OLD_BOARD_EXTRA, NEW_BOARD_EXTRA, "stock_app board extra")
    # 2.2 _s444_renames reads the cached report
    a = ('def _s444_renames(con, cid):\n'
         '    """(ready, open) for the newest count: the renames show ONLY once the proof is green (S437 gate, _proof_state \'done\'). The proof\n'
         '    reads the whole report (~3 s), so it is asked only when no voucher of the count is still open, and kept 10 minutes."""\n')
    n = ('def _s444_renames(con, cid):\n'
         '    """(ready, open) for the newest count: the renames show ONLY once the stage releases them (S437 gate; S521 / S524: the stage proof,\n'
         '    or renames once released). The report is the cached one (_report_cached), read only to know the count exists; kept 10 minutes."""\n')
    t = rep(t, a, n, "stock_app _s444_renames docstring")
    a = ('        d = _pad_report_data(con, cid)\n'
         '        if d is not None:\n'
         '            ready = ((amir_stage(con, cid) or {}).get("stage") in ("B", "C", "done"))   # S521 (F-838): the board\'s proof line and renames gate are the stage\'s, as on his card\n')
    n = ('        d = _report_cached(con, cid)                            # S524 (2.2): the cached report, never a route\'s\n'
         '        if d is not None:\n'
         '            _st = amir_stage(con, cid, d=d)\n'
         '            ready = bool(_st and (_st.get("stage") in ("B", "C", "done") or _st.get("renames_visible")))   # S521 (F-838) / S524 (R2-2): the stage, as on his card and board\n')
    t = rep(t, a, n, "stock_app _s444_renames body")
    # 2.1 the proof, its cache line, the batches, the stage, the why
    a = '_S446_PROOF_CACHE = {}                                          # (root, keys, entered stamp) -> (time, proof)\n'
    n = '_S446_PROOF_CACHE = {}                                          # S524: (root, every entered (key, at), first_at, last_at, built, SPINE_DB) -> (time, the per-key table)\n'
    t = rep(t, a, n, "stock_app cache comment")
    t = rep(t, OLD_BATCHES, NEW_BATCHES, "stock_app _s446_batches")
    t = cut(t, "def _s446_proof(con, root, keys, ent, batches):\n", "\n\ndef _s446_event(con, root, stage, event, ref=None):\n", NEW_PROOF, "stock_app _s446_proof")
    t = cut(t, "def amir_stage(con, cid=None):\n", "\n\ndef _s446_board_filter(con, b, u):\n", NEW_STAGE, "stock_app amir_stage")
    t = cut(t, "def _s488_why(con, feeds, before, after, last_at):\n", "\n\ndef _s488_stage_proof(st):\n", NEW_WHY, "stock_app _s488_why")
    # S521's line and comments
    a = ('        if stage == "A":\n'
         '            if int(A.get("open") or 0) > 0:\n'
         '                state, hi = "wait", "Abhi baaki \\u2014 pehle orthotic voucher Marg mein daaliye"\n'
         '            elif AP.get("state") == "export":\n')
    n = ('        if stage == "A":\n'
         '            if int(A.get("open") or 0) > 0:\n'
         '                state, hi = "wait", "Abhi baaki \\u2014 pehle orthotic voucher Marg mein daaliye"\n'
         '            elif int(A.get("pending") or 0) > 0 and AP.get("state") == "done":    # S524 (R2-1): proven; an orthotic line still owed a voucher\n'
         '                state, hi = "done", "Orthotic: sab sahi \\u2713"\n'
         '            elif AP.get("state") == "export":\n')
    t = rep(t, a, n, "stock_app _s521_stage_proof branch")
    a = '        ready = stage in ("B", "C", "done")\n        wait_hi = "" if ready else S521_RENAMES_WAIT_HI\n'
    n = '        ready = stage in ("B", "C", "done") or bool(st.get("renames_visible"))   # S524 (R2-2): renames once released stay with him\n        wait_hi = "" if ready else S521_RENAMES_WAIT_HI\n'
    t = rep(t, a, n, "stock_app _s521 ready")
    a = '#   Section 2 of Amir\'s board ("Marg = shelf?") came from _proof_state -- the whole count\'s proof on the FIRST closing after the vouchers,\n'
    n = '#   Section 2 of Amir\'s board ("Marg = shelf?") came from the old whole-count proof (retired by S524) -- the FIRST closing after the vouchers,\n'
    t = rep(t, a, n, "stock_app S521 comment 1")
    a = ('#   _s444_renames (his step-6 rename duty) asks the stage too.  _proof_state itself, the owner\'s hub (step 5) and every other page are\n'
         '#   not changed.  The extra amir_stage call on an owner read is accepted: its writes are the once-only stage events his own card causes.\n')
    n = ('#   _s444_renames (his step-6 rename duty) asks the stage too.  S524: the old whole-count proof is retired; the owner\'s hub (step 7)\n'
         '#   reads the stage proof.  The extra amir_stage call on an owner read is accepted: its writes are the once-only stage events his own card causes.\n')
    t = rep(t, a, n, "stock_app S521 comment 2")
    end = "# ---- S521_AMIR_BOARD_STAGE_PROOF end -----------------------------------------------------------------------------------------------------\n"
    if not t.endswith(end):
        raise Stop("stock_app.py does not end with the S521 end line")
    t = t + S524_BLOCK
    for bad in ("_proof_state(", "def _proof_state", "_proof_pur_to(", "_proof_basis("):
        if bad in t:
            raise Stop("the built stock_app.py still carries %r" % bad)
    return t


# ============================================================================================================== DUTY_MAP (2.5, F-846)
ORTHO = ("EXISTS (SELECT 1 FROM stock_voucher_line x WHERE x.count_id=b.count_id AND x.round_no=b.round_no AND x.kind=b.kind "
         "AND x.batch_no=b.batch_no AND x.section='Orthotics')")
REL_AT = ("(SELECT MIN(s.at) FROM stock_stage_event s WHERE s.count_id=b.count_id AND s.stage='C' AND s.event='release' "
          "AND (','||COALESCE(s.ref,'')||',') LIKE '%,'||b.round_no||'|'||b.kind||'|'||b.batch_no||',%')")
V10_SQL = ("SELECT COUNT(*) AS n, MIN(CASE WHEN " + ORTHO + " THEN b.made_at ELSE MAX(b.made_at, " + REL_AT + ") END) AS since "
           "FROM (SELECT l.count_id, l.round_no, l.kind, l.batch_no, MIN(l.made_at) AS made_at FROM stock_voucher_line l GROUP BY l.count_id, l.round_no, l.kind, l.batch_no) b "
           "WHERE NOT EXISTS (SELECT 1 FROM stock_voucher_entered e WHERE e.count_id = b.count_id AND e.round_no = b.round_no AND e.kind = b.kind "
           "AND e.batch_no = b.batch_no AND TRIM(COALESCE(e.marg_voucher_no,'')) <> '' AND e.id = (SELECT MAX(e2.id) FROM stock_voucher_entered e2 "
           "WHERE e2.count_id = b.count_id AND e2.round_no = b.round_no AND e2.kind = b.kind AND e2.batch_no = b.batch_no)) "
           "AND (" + ORTHO + " OR " + REL_AT + " IS NOT NULL)")
V9_SQL = ("SELECT COUNT(*) AS n, MIN(made_at) AS since FROM (SELECT l.count_id, l.round_no, l.kind, l.batch_no, MIN(l.made_at) AS made_at FROM stock_voucher_line l "
          "GROUP BY l.count_id, l.round_no, l.kind, l.batch_no) b WHERE NOT EXISTS (SELECT 1 FROM stock_voucher_entered e WHERE e.count_id = b.count_id "
          "AND e.round_no = b.round_no AND e.kind = b.kind AND e.batch_no = b.batch_no AND TRIM(COALESCE(e.marg_voucher_no,'')) <> '' AND e.id = "
          "(SELECT MAX(e2.id) FROM stock_voucher_entered e2 WHERE e2.count_id = b.count_id AND e2.round_no = b.round_no AND e2.kind = b.kind AND e2.batch_no = b.batch_no))")
NOTE_ADD = (" S524 (11-Oct-2026, D706, F-846): amir.count_vouchers' due_sql counts only the vouchers Amir can see -- the orthotic batches (stage A) and the"
            " batches of a released stage-C lot (stock_stage_event C/release naming the batch); a released lot's `since` is its release, not the round's day."
            " Nothing else in the map moves.")


def build_duty_json(raw):
    t = raw.decode("utf-8")
    j = json.loads(t)
    if j.get("version") != 9:
        raise Stop("DUTY_MAP.json is v%s, not v9" % j.get("version"))
    du = [x for x in j["duties"] if x["id"] == "amir.count_vouchers"]
    if len(du) != 1 or du[0]["due_sql"] != V9_SQL:
        raise Stop("amir.count_vouchers is not the v9 row this builder was written on")
    du[0]["due_sql"] = V10_SQL
    du[0]["duty"] = du[0]["duty"] + " -- S524 (F-846): the due count is the orthotic batches and the released lots only"
    j["version"] = 10
    j["kit"] = "S524_AMIR_ONE_JUDGMENT"
    j["_note"] = j["_note"] + NOTE_ADD
    out = json.dumps(j, indent=1, ensure_ascii=False) + "\n"
    if out.count(V10_SQL) != 1:
        raise Stop("DUTY_MAP.json: the v10 SQL was not written once")
    return out


def build_duty_md(t):
    a = "| `stock_voucher_line` batches with no non-empty newest `stock_voucher_entered` row (37 batches, 7 orthotic); the stage from `stock_stage_event` + the proof (S304's drift test over the stage's lines) |"
    n = "| `stock_voucher_line` batches with no non-empty newest `stock_voucher_entered` row -- the orthotic batches and the released lots only (S524, F-846; a released lot's `since` is its release); the stage from `stock_stage_event` + the stage proof (S524: read from the spine, one key one judgment) |"
    t = rep(t, a, n, "DUTY_MAP.md count_vouchers row")
    a = "**07-Oct-2026 · kit S494_AMIR_JOBS_NOTICE_FLAGS (D686):** `[amir.marg_jobs]` added — Amir's one-time Marg jobs on his Marg sudhar card under \"Ek baar ke kaam\", each gone when proved or tapped. No other login's list changes. `DUTY_MAP.json` is v9.\n"
    n = a + ("\n**11-Oct-2026 · kit S524_AMIR_ONE_JUDGMENT (D706, F-846):** `[amir.count_vouchers]`'s due count is the vouchers Amir can see — the orthotic batches and the "
             "batches of a released stage-C lot (a released lot's `since` is its release). No duty added, moved or removed; no other login's list changes. `DUTY_MAP.json` is v10.\n")
    return rep(t, a, n, "DUTY_MAP.md log line")


BUILDERS = {
    "stock_app.py": ("finance", build_stock_app),
    "stockmatch.py": ("finance", build_stockmatch),
    "shelf_figure.py": ("finance", build_shelf_figure),
    "amir_day.py": ("finance", build_amir_day),
    "marg_take.py": ("ingest", build_marg_take),
    "spine_build.py": ("spine", build_spine_build),
    "marg_read.py": ("spine", build_marg_read),
    "DUTY_MAP.json": ("briefs", None),
    "DUTY_MAP.md": ("briefs", build_duty_md),
}


def read_to(kit_dir):
    p = os.path.join(kit_dir, TO_FILE)
    to = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.startswith("TO[") and "]=" in line:
                k, v = line[3:].split("]=", 1)
                to[k] = v.strip()
    return to


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--spine", required=True)
    ap.add_argument("--ingest", required=True)
    ap.add_argument("--briefs", default="", help="the repository's claude_code_briefs (packing only: DUTY_MAP.json/.md are built from v9 on the PC)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="comma-separated names to build (default: all)")
    ap.add_argument("--print-to", action="store_true", help="print the built md5s and accept them (packing the kit)")
    a = ap.parse_args(argv)
    dirs = dict(finance=a.finance, spine=a.spine, ingest=a.ingest, briefs=a.briefs)
    want = [x for x in a.only.split(",") if x] or list(BUILDERS)
    to_known = read_to(os.path.dirname(os.path.abspath(__file__)))
    results = {}
    try:
        for name in want:
            where, fn = BUILDERS[name]
            frm = PINS[name][0]
            raw = open(os.path.join(dirs[where], name), "rb").read()
            if md5(raw) != frm:
                raise Stop("%s is %s, not the FROM pin %s -- someone changed it since the brief" % (name, md5(raw), frm))
            if b"\r" in raw:
                raise Stop("%s carries carriage returns" % name)
            if name == "DUTY_MAP.json":
                new = build_duty_json(raw).encode("utf-8")
            else:
                new = fn(raw.decode("utf-8")).encode("utf-8")
            if name.endswith(".py"):
                compile(new, name, "exec")
            to = to_known.get(name)
            if not a.print_to:
                if not to:
                    raise Stop("%s: no TO pin in %s (pack the kit with --print-to first)" % (name, TO_FILE))
                if md5(new) != to:
                    raise Stop("%s built to %s, not the TO pin %s" % (name, md5(new), to))
            results[name] = (raw, new)
    except Stop as e:
        print("STOP: %s" % e)
        return 2
    os.makedirs(a.out, exist_ok=True)
    for name, (raw, new) in results.items():
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(new)
        print("%-16s %s -> %s  (%+d lines)" % (name, md5(raw)[:8], md5(new)[:8], new.count(b"\n") - raw.count(b"\n")))
    if a.print_to:
        for name, (_raw, new) in results.items():
            print("TO[%s]=%s" % (name, md5(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
