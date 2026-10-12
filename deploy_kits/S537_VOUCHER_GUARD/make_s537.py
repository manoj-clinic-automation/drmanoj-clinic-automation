#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
make_s537.py -- the builder of kit S537_VOUCHER_GUARD (12-Oct-2026; the owner's "Yes" of 07:02 IST; F-185).

    python3 -B make_s537.py --finance DIR --briefs DIR --out DIR [--print-to]

Reads the LIVE files at their FROM pins (anything else: stop), makes anchored edits (each anchor must occur exactly once, else it
stops), compiles every python result, checks the duty map's JSON, and writes the results into --out (nothing else is written).
With --print-to the built md5s are printed and accepted (packing the kit); without it every result must equal its TO pin (PINS.sh).
--briefs holding DUTY_MAP.json/.md already at their TO pins (the box's clone pulled) is accepted as it is.

  stock_app.py        2.1 the void: two tables in VOUCHER_SCHEMA (VOUCHER_S537_SCHEMA), ONE filter _void_sql(alias) on _voucher_frozen,
                      _voucher_state, the entered door (its Hindi refusal), _voucher_numbers, amir_vouchers_open, _s446_batches; the void
                      door _voucher_void (never an entered batch).  2.2 settled stays settled (_voucher_settled).  2.3 the guard:
                      _voucher_lines (the one loop: offered, held, unread), _voucher_pending / _voucher_held its two faces,
                      _voucher_guard_base / _voucher_guard (Marg's newest closing by the full name + the vouchers not yet in it),
                      _voucher_held_batches (the frozen batches' test at a stage-C release and at "Aur voucher kholiye"); amir_stage's
                      A["held"] / C["held"] / unread; _s521_stage_words' owner lines.
  stock_watch.py      2.5 bill_pending_lines: an arrival tied to its bill (billed_bill_no) is never listed.
  shelf_figure.py     2.1 filed_vouchers honours the void.
  stock_statement.py  2.1 the statement's rounds honour the void.
  loss_piles.py       2.3 receive_close carries the held items (no EXPLAINED again on every run).
  DUTY_MAP.json       2.6 v11 -> v12: amir.count_vouchers' due_sql honours the void (anchored on ') b WHERE NOT EXISTS').
  DUTY_MAP.md         2.6 the row and a log line.

Run with -B.  Never import this file.  It writes only inside --out.
"""
import argparse
import hashlib
import json
import os
import sys

PINS = {
    "stock_app.py": ("finance", "8d55637c3ab59a323cff1a0efb021527"),
    "stock_watch.py": ("finance", "c960f6c890e3e83c58b88d8a7f219752"),
    "shelf_figure.py": ("finance", "9be5eb88d1b1fc1fdb03b906c88a4265"),
    "stock_statement.py": ("finance", "1a4f6c9ecb2546dae954c0414074f406"),
    "loss_piles.py": ("finance", "202bfc4e3fd798501c6db95373c2a7d4"),
    "DUTY_MAP.json": ("briefs", "69b8f56b17da263b932426b87a7abc1c"),
    "DUTY_MAP.md": ("briefs", "553398f3a21541e688d3f3c72e585748"),
}
TO_FILE = "PINS.sh"


def md5(b):
    return hashlib.md5(b).hexdigest()


class Stop(Exception):
    pass


def rep(t, a, new, what):
    n = t.count(a)
    if n != 1:
        raise Stop("%s: anchor occurs %d times (must be exactly 1): %r" % (what, n, a[:120]))
    return t.replace(a, new, 1)


# ============================================================================================================== stock_app.py
# ---- 2.1 the two tables (a constant of their own, so the data step's --dry can lay them inside its transaction; no ';' in a comment)
SA_SCHEMA_OLD = "# ---------------------------------------------------------------------------\nVOUCHER_SCHEMA = \"\"\"\n"
SA_SCHEMA_NEW = ("# ---------------------------------------------------------------------------\n"
                 "# S537 (charter 5, 10): a VOID of a whole batch and a SETTLE of an item, both append-only, never a DELETE. Every reader of\n"
                 "# stock_voucher_line honours the void through _void_sql (one filter) -- the numbering (_voucher_seq) never shifts, a voided\n"
                 "# batch is simply not shown. A settled item is never raised again by the count-day sum (_voucher_lines).\n"
                 "VOUCHER_S537_SCHEMA = \"\"\"\n"
                 "CREATE TABLE IF NOT EXISTS stock_voucher_void (\n"
                 "  id         INTEGER PRIMARY KEY,         -- S537: one row voids one whole batch (never an entered one)\n"
                 "  count_id   INTEGER NOT NULL, round_no INTEGER NOT NULL, kind TEXT NOT NULL, batch_no INTEGER NOT NULL,\n"
                 "  by_user    TEXT, at TEXT NOT NULL, reason TEXT\n"
                 ");\n"
                 "CREATE TABLE IF NOT EXISTS stock_voucher_settle (\n"
                 "  id         INTEGER PRIMARY KEY,         -- S537: the owner settled this item for this count\n"
                 "  count_id   INTEGER NOT NULL, item TEXT NOT NULL, by_user TEXT, at TEXT NOT NULL, note TEXT\n"
                 ");\n"
                 "\"\"\"\n"
                 "VOUCHER_SCHEMA = \"\"\"\n")
SA_SCHEMA_TAIL_OLD = ("  marg_voucher_no TEXT NOT NULL, entered_on TEXT, by_user TEXT, at TEXT NOT NULL\n"
                      ");\n"
                      "\"\"\"\n"
                      "VOUCHER_KIND_TEXT = ")
SA_SCHEMA_TAIL_NEW = ("  marg_voucher_no TEXT NOT NULL, entered_on TEXT, by_user TEXT, at TEXT NOT NULL\n"
                      ");\n"
                      "\"\"\" + VOUCHER_S537_SCHEMA                        # S537: the void and the settle tables, laid by _voucher_ensure\n"
                      "VOUCHER_KIND_TEXT = ")

# ---- 2.1 / 2.2 the filter, the void door, the settled items
SA_ENSURE_OLD = ("def _voucher_ensure(con):\n"
                 "    con.executescript(VOUCHER_SCHEMA)\n"
                 "\n")
SA_ENSURE_NEW = ("def _voucher_ensure(con):\n"
                 "    con.executescript(VOUCHER_SCHEMA)\n"
                 "\n"
                 "\n"
                 "def _void_sql(a):\n"
                 "    \"\"\"S537 (charter 2, 5): THE one void filter -- true for a stock_voucher_line row (alias `a`) whose batch has no stock_voucher_void row.\"\"\"\n"
                 "    return (\"NOT EXISTS (SELECT 1 FROM stock_voucher_void v WHERE v.count_id=%s.count_id AND v.round_no=%s.round_no AND v.kind=%s.kind \"\n"
                 "            \"AND v.batch_no=%s.batch_no)\" % (a, a, a, a))\n"
                 "\n"
                 "\n"
                 "def _voucher_void(con, root, rno, kind, bno, who, reason):\n"
                 "    \"\"\"S537: void ONE whole batch (append-only; the tables laid by _voucher_ensure beforehand). Refused for a batch that does not exist\n"
                 "    and for a batch with an entered Marg number (_s446_entered: the newest non-empty row) -- an entered voucher is in Marg, and its\n"
                 "    reverse is a RECEIVE, the owner's decision. A batch already voided is not voided twice. Returns (ok, word). Commits nothing.\"\"\"\n"
                 "    k = (int(rno), str(kind).upper(), int(bno))\n"
                 "    if not con.execute(\"SELECT 1 FROM stock_voucher_line WHERE count_id=? AND round_no=? AND kind=? AND batch_no=? LIMIT 1\",\n"
                 "                       (int(root),) + k).fetchone():\n"
                 "        return False, \"no_such_batch\"\n"
                 "    if k in _s446_entered(con, int(root)):\n"
                 "        return False, \"entered\"\n"
                 "    if con.execute(\"SELECT 1 FROM stock_voucher_void WHERE count_id=? AND round_no=? AND kind=? AND batch_no=? LIMIT 1\",\n"
                 "                   (int(root),) + k).fetchone():\n"
                 "        return True, \"already\"\n"
                 "    con.execute(\"INSERT INTO stock_voucher_void (count_id, round_no, kind, batch_no, by_user, at, reason) VALUES (?,?,?,?,?,?,?)\",\n"
                 "                (int(root),) + k + (who or \"\", now_iso(), (reason or \"\")[:500]))\n"
                 "    return True, \"voided\"\n"
                 "\n"
                 "\n"
                 "def _voucher_settled(con, root):\n"
                 "    \"\"\"S537 (2.2): {item} -- the items the owner settled for this count (stock_voucher_settle); the count-day sum never raises them again.\"\"\"\n"
                 "    return {r[0] for r in con.execute(\"SELECT item FROM stock_voucher_settle WHERE count_id=?\", (int(root),))}\n"
                 "\n")

SA_FROZEN_OLD = ("    return {r[0]: int(r[1] or 0) for r in con.execute(\n"
                 "        \"SELECT item, SUM(change) FROM stock_voucher_line WHERE count_id=? GROUP BY item\", (root,))}\n")
SA_FROZEN_NEW = ("    return {r[0]: int(r[1] or 0) for r in con.execute(\n"
                 "        \"SELECT item, SUM(change) FROM stock_voucher_line l WHERE count_id=? AND \" + _void_sql(\"l\") + \" GROUP BY item\", (root,))}   # S537: a voided batch moved nothing\n")

# ---- 2.2 / 2.3 the one loop
SA_PEND_OLD = '''def _voucher_pending(con, d, section=None, items=None):
    """The lines the next round would carry: per item, what the Marg cleanup list now needs
    minus what earlier rounds already moved. Ordered section, family, item.
    S404: with `section` ('Orthotics'), that section's lines only -- the rest stay for their own round."""
    by = {x["item"]: x for x in d["differences"]}
'''
SA_PEND_NEW = '''def _voucher_lines(con, d, section=None, items=None):
    """(offered, held, unread) -- the count-day sum judged ONCE per item. offered = the lines the next round would carry: per item, what
    the Marg cleanup list now needs minus what earlier rounds already moved. Ordered section, family, item.
    S404: with `section` ('Orthotics'), that section's lines only -- the rest stay for their own round.
    S537 (charter 1b, 5, 12): an item the owner settled for this count is skipped (stock_voucher_settle). A line that LOWERS Marg is HELD
    -- never offered, never frozen, never Amir's -- when Marg's newest closing of the item BY ITS FULL PRINTED NAME, plus the units of the
    count's vouchers already made but not yet in that closing, plus the line itself, would go below zero (_voucher_guard). A name absent
    from that closing is offered and listed in `unread` (the guard not applied; the owner's summary line). Writes nothing."""
    by = {x["item"]: x for x in d["differences"]}
'''
SA_LOOP_OLD = '''    frozen = _voucher_frozen(con, d["count_id"])
    out = []
    for item in set(need) | set(frozen):
        x = by.get(item)
        if not x:
            continue
        if section and _item_section(con, x) != section:      # S404: a section round carries that section's lines only
            continue
        if items is not None and item not in items:            # S418: the write-off pile's round carries those lines only
            continue
        ch = need.get(item, 0) - frozen.get(item, 0)
        if not ch:
            continue
'''
SA_LOOP_NEW = '''    frozen = _voucher_frozen(con, d["count_id"])
    settled = _voucher_settled(con, d["count_id"])             # S537 (2.2)
    G = None                                                   # S537 (2.3): the guard's reading, once, on the first line that lowers Marg
    out, held, unread = [], [], []
    for item in set(need) | set(frozen):
        x = by.get(item)
        if not x:
            continue
        if section and _item_section(con, x) != section:      # S404: a section round carries that section's lines only
            continue
        if items is not None and item not in items:            # S418: the write-off pile's round carries those lines only
            continue
        if item in settled:                                    # S537: settled stays settled
            continue
        ch = need.get(item, 0) - frozen.get(item, 0)
        if not ch:
            continue
'''
SA_APPEND_OLD = '''        out.append(dict(item=item, packing=x.get("packing") or "", pack=int(x.get("pack") or 1), section=sec, family=fam,
                        kind=("ISSUE" if ch < 0 else "RECEIVE"), marg_from=m0, change=ch, marg_to=m0 + ch,
                        counted=x.get("counted"), rate_p=rate,
                        value_p=(None if rate is None or int(x["marg"]) < 0 else ch * rate), reason=reason))
    out.sort(key=lambda r: (r["kind"], _SECTION_ORDER.get(r["section"], 9), r["family"], r["item"]))
    return out
'''
SA_APPEND_NEW = '''        row = dict(item=item, packing=x.get("packing") or "", pack=int(x.get("pack") or 1), section=sec, family=fam,
                   kind=("ISSUE" if ch < 0 else "RECEIVE"), marg_from=m0, change=ch, marg_to=m0 + ch,
                   counted=x.get("counted"), rate_p=rate,
                   value_p=(None if rate is None or int(x["marg"]) < 0 else ch * rate), reason=reason)
        if ch < 0:                                             # S537 (R2-3): only a line that lowers Marg is tested
            if G is None:
                G = _voucher_guard_base(con, d["count_id"])
            g = _voucher_guard(G, item, ch)
            if g["held"]:
                held.append(dict(row, marg_now=g["marg_now"], as_on=g["as_on"], unkeyed=g["unkeyed"]))
                continue
            if g["unread"]:
                unread.append(dict(row, as_on=g["as_on"]))
        out.append(row)
    for ls in (out, held, unread):
        ls.sort(key=lambda r: (r["kind"], _SECTION_ORDER.get(r["section"], 9), r["family"], r["item"]))
    return out, held, unread


def _voucher_pending(con, d, section=None, items=None):
    """The lines the next round would carry (S537: settled items skipped, held lines never here) -- _voucher_lines' offered."""
    return _voucher_lines(con, d, section, items)[0]


def _voucher_held(con, d, section=None):
    """S537: the lines the guard holds back from Amir (each named on the owner's Needs-you) -- _voucher_lines' held, the same loop."""
    return _voucher_lines(con, d, section)[1]


def _voucher_guard_base(con, root):
    """S537 (2.3): what the guard reads, once per judgment -- Marg's newest closing BY THE FULL PRINTED NAME (shelf_figure.latest_snapshot:
    the newest closing by its real date; a name it does not print is 'not readable', never an older figure; sizes stay apart -- the spine's
    20-letter key would fold them) and, per item, `unkeyed`: the units of the count's frozen lines (not voided) whose batch is not in that
    closing -- not entered, or first entered after the closing's day (they will move Marg too). Read only."""
    try:
        import shelf_figure                                    # noqa: PLC0415
        as_on, snap = shelf_figure.latest_snapshot(con)
    except Exception:                                          # noqa: BLE001 -- no closing readable: every line offered, the owner told
        as_on, snap = None, {}
    ent, win, unk = _s446_entered(con, int(root)), _s446_window(con, int(root)), {}
    for rno, kind, bno, item, ch in con.execute("SELECT l.round_no, l.kind, l.batch_no, l.item, l.change FROM stock_voucher_line l "
                                                "WHERE l.count_id=? AND " + _void_sql("l"), (int(root),)):
        k = (int(rno), str(kind), int(bno))
        if k in ent and as_on and str(win.get(k) or ent[k][1] or "")[:10] <= as_on:
            continue                                           # entered on or before the closing's day: already in it
        unk[item] = unk.get(item, 0) + int(ch or 0)
    return dict(as_on=as_on, snap=snap or {}, unkeyed=unk)


def _voucher_guard(G, item, ch, frozen=False):
    """S537: one line's test against _voucher_guard_base -> dict(held, unread, marg_now, as_on, unkeyed). Held when the line lowers Marg
    and marg_now + unkeyed (+ the line, unless it is a frozen line already inside unkeyed -- counted once) is below zero."""
    s = (G.get("snap") or {}).get(item)
    unk = int((G.get("unkeyed") or {}).get(item, 0))
    if s is None:
        return dict(held=False, unread=True, marg_now=None, as_on=G.get("as_on"), unkeyed=unk)
    m = int(s.get("qty") or 0)
    return dict(held=bool(ch < 0 and m + unk + (0 if frozen else ch) < 0), unread=False, marg_now=m, as_on=G.get("as_on"), unkeyed=unk)


def _voucher_held_batches(con, root, keys, batches, G=None):
    """S537 (R2-2): ({key: [held line]}, {unreadable item}) -- the frozen batches among `keys` with ANY line that fails _voucher_guard (the
    line's own change counted once inside unkeyed). Such a batch is never released to Amir: amir_stage's stage-C release and "Aur voucher
    kholiye" (_s452_release) skip it; the owner's line names it with its voucher number. Read only."""
    G = G or _voucher_guard_base(con, root)
    out, unread = {}, set()
    for k in keys:
        b = batches.get(k) or {}
        bad = []
        for item, ch, _mto in b.get("lines") or []:
            if int(ch) >= 0:
                continue
            g = _voucher_guard(G, item, int(ch), frozen=True)
            if g["unread"]:
                unread.add(item)
            if g["held"]:
                pk = (b.get("pk") or {}).get(item, ("", None))
                bad.append(dict(item=item, change=int(ch), packing=pk[0] or "", pack=pk[1] or 1, marg_now=g["marg_now"], as_on=g["as_on"],
                                unkeyed=g["unkeyed"], key=k))
        if bad:
            out[k] = bad
    return out, unread
'''

SA_STATE_OLD = ('                         "counted, rate_p, value_p, reason, made_by, made_at FROM stock_voucher_line WHERE count_id=? "\n'
                '                         "ORDER BY round_no, kind, batch_no, line_no", (root,)):\n')
SA_STATE_NEW = ('                         "counted, rate_p, value_p, reason, made_by, made_at FROM stock_voucher_line l WHERE count_id=? AND " + _void_sql("l") + " "\n'
                '                         "ORDER BY round_no, kind, batch_no, line_no", (root,)):          # S537: a voided batch is not shown\n')

SA_ENT_OLD = ('    r = con.execute("SELECT batches_n, COUNT(*) FROM stock_voucher_line WHERE count_id=? AND round_no=? AND kind=? AND batch_no=?",\n'
              '                    (_root, rno, kind, bno)).fetchone()\n'
              '    if not r or not r[1]:\n'
              '        return jsonify(ok=False, error="no_such_voucher", message="No such voucher in round %d." % rno), 400\n')
SA_ENT_NEW = ('    r = con.execute("SELECT batches_n, COUNT(*) FROM stock_voucher_line l WHERE count_id=? AND round_no=? AND kind=? AND batch_no=? AND " + _void_sql("l"),\n'
              '                    (_root, rno, kind, bno)).fetchone()\n'
              '    if not r or not r[1]:                                     # S537: a voided batch (or none) -- a stale page is told in Hindi\n'
              '        return jsonify(ok=False, error="no_such_voucher", message="Yeh voucher ab nahi hai."), 400\n')

SA_NUM_OLD = ('    for rno, kind, bno, item in con.execute("SELECT round_no, kind, batch_no, item FROM stock_voucher_line WHERE count_id=? '
              'ORDER BY kind=\'RECEIVE\', round_no, batch_no, line_no", (int(root),)):\n')
SA_NUM_NEW = ('    for rno, kind, bno, item in con.execute("SELECT round_no, kind, batch_no, item FROM stock_voucher_line l WHERE count_id=? AND " + _void_sql("l") +\n'
              '                                            " ORDER BY kind=\'RECEIVE\', round_no, batch_no, line_no", (int(root),)):   # S537: a voided batch carries no number\n')

SA_OPEN_OLD = '    for cid, rno, kind, bno, sec, made in con.execute("SELECT count_id, round_no, kind, batch_no, section, made_at FROM stock_voucher_line"):\n'
SA_OPEN_NEW = ('    for cid, rno, kind, bno, sec, made in con.execute("SELECT count_id, round_no, kind, batch_no, section, made_at FROM stock_voucher_line l WHERE "\n'
               '                                                      + _void_sql("l")):   # S537: a voided batch is never open\n')

SA_BATCH_OLD = ('            "SELECT round_no, kind, batch_no, section, item, change, marg_to, made_at, packing, pack FROM stock_voucher_line WHERE count_id=? "\n'
                '            "ORDER BY round_no, kind, batch_no, line_no", (root,)):\n')
SA_BATCH_NEW = ('            "SELECT round_no, kind, batch_no, section, item, change, marg_to, made_at, packing, pack FROM stock_voucher_line l WHERE count_id=? AND "\n'
                '            + _void_sql("l") + " ORDER BY round_no, kind, batch_no, line_no", (root,)):   # S537: the stage, the board and the proof never see a voided batch\n')

SA_A_OLD = ('    rep = d if d is not None else _report_cached(con, root)\n'
            '    if rep is not None:\n'
            '        try:\n'
            '            A["pending"] = len(_voucher_pending(con, rep, section="Orthotics"))\n'
            '        except Exception:                                      # noqa: BLE001\n'
            '            A["pending"] = 0\n')
SA_A_NEW = ('    rep = d if d is not None else _report_cached(con, root)\n'
            '    A["held"], A["unread"] = [], 0                             # S537 (2.3): the lines the guard holds back -- the owner\'s, never pending\n'
            '    if rep is not None:\n'
            '        try:\n'
            '            _o, _h, _u = _voucher_lines(con, rep, section="Orthotics")\n'
            '            A["pending"], A["held"], A["unread"] = len(_o), _h, len(_u)\n'
            '        except Exception:                                      # noqa: BLE001\n'
            '            A["pending"] = 0\n')

SA_REL_OLD = ('    released = {k for l in lots for k in l["keys"]}\n'
              '    def release_next():\n'
              '        nxt = [k for k in med if k not in released and k not in ent][:per]\n')
SA_REL_NEW = ('    released = {k for l in lots for k in l["keys"]}\n'
              '    # S537 (R2-2): a batch with a line that would take Marg below zero is never released -- skipped into C["held"], the next passing\n'
              '    # batch takes its place\n'
              '    held_c, unread_c = _voucher_held_batches(con, root, [k for k in med if k not in released and k not in ent], batches)\n'
              '    def release_next():\n'
              '        nxt = [k for k in med if k not in released and k not in ent and k not in held_c][:per]\n')

SA_UNREL_OLD = '             open=len([k for k in vis if k not in ent]), unreleased=len([k for k in med if k not in released and k not in ent]),\n'
SA_UNREL_NEW = '             open=len([k for k in vis if k not in ent]), unreleased=len([k for k in med if k not in released and k not in ent and k not in held_c]),\n'

SA_C_OLD = ('    out["C"] = C\n'
            '    out["visible"] = _s446_order(vis)\n')
SA_C_NEW = ('    out["C"] = C\n'
            '    # S537: C["held"] -- the held batches\' lines (with their voucher number) and the rest of the count-day sum\'s held lines (A\'s orthotic\n'
            '    # ones are A["held"]); C["unread"] -- the names the newest closing does not print (the guard not applied)\n'
            '    C["held"] = [dict(l, seq=(_sq.get(k) or (0,))[0]) for k in _s446_order(held_c) for l in held_c[k]]\n'
            '    C["unread"] = len(unread_c)\n'
            '    if rep is not None:\n'
            '        try:\n'
            '            _o, _h, _u = _voucher_lines(con, rep)\n'
            '            _a = {h["item"] for h in A.get("held") or []}\n'
            '            C["held"] += [h for h in _h if h["item"] not in _a]\n'
            '            C["unread"] = len(unread_c | {u["item"] for u in _u})\n'
            '        except Exception:                                      # noqa: BLE001\n'
            '            pass\n'
            '    out["visible"] = _s446_order(vis)\n')

SA_MORE_OLD = ('    nxt = [k for k in med if k not in released and k not in ent][:per]\n'
               '    if not nxt:\n'
               '        return 0\n')
SA_MORE_NEW = ('    cand = [k for k in med if k not in released and k not in ent]\n'
               '    held_c = _voucher_held_batches(con, root, cand, batches)[0]   # S537: the same test as amir_stage\'s release -- a held batch never goes to Amir\n'
               '    nxt = [k for k in cand if k not in held_c][:per]\n'
               '    if not nxt:\n'
               '        return 0\n')

SA_WORDS_OLD = '        owner_lines = [dict(cls="warn", target="stock", text=r["text"]) for r in wrong]\n'
SA_WORDS_NEW = ('        owner_lines = [dict(cls="warn", target="stock", text=r["text"]) for r in wrong]\n'
                '        # S537 (2.3, R1-9a): the guard\'s lines -- the owner\'s only; Amir never sees a held line. One line per held item, then one summary\n'
                '        # line for the names the newest closing does not print (the guard not applied, charter 1b).\n'
                '        G_ = (A if stage == "A" else C if stage == "C" else {})\n'
                '        for h in G_.get("held") or []:\n'
                '            vn = (" (%s voucher %d)" % (VOUCHER_HI.get(h["key"][1], h["key"][1]), int(h["seq"]))) if h.get("key") and h.get("seq") else ""\n'
                '            owner_lines.append(dict(cls="warn", target="stock", text="Count #%d: %s%s \\u2014 the count-day sum asks %s; Marg\'s closing of %s holds %s: not given to Amir"\n'
                '                                    % (root, h.get("item"), vn, _s528_qty_en(h.get("change"), h.get("item"), h.get("packing"), h.get("pack")),\n'
                '                                       _s524_dmy(h.get("as_on"))[:5], _s537_qty_en(h.get("marg_now"), h.get("item"), h.get("packing"), h.get("pack")))))\n'
                '        if int(G_.get("unread") or 0):\n'
                '            owner_lines.append(dict(cls="info", target="stock", text="Count #%d: closing not readable for %d item(s) \\u2014 guard not applied"\n'
                '                                    % (root, int(G_["unread"]))))\n')

SA_QTY_OLD = ('def _s528_wrong_rows(rows, seqs):\n')
SA_QTY_NEW = ('def _s537_qty_en(v, item, packing, pack):\n'
              '    """S537: a quantity (unsigned) in the owner\'s words (qty_words, English); \'%d\' when the words cannot be had."""\n'
              '    try:\n'
              '        if v is not None and _qty is not None:\n'
              '            return _qty.words(v, packing=(packing or None), pack=pack, name=item, lang="en")\n'
              '    except Exception:                                          # noqa: BLE001\n'
              '        pass\n'
              '    try:\n'
              '        return "%d" % int(round(float(v)))\n'
              '    except (TypeError, ValueError):\n'
              '        return "?"\n'
              '\n'
              '\n'
              'def _s528_wrong_rows(rows, seqs):\n')


def build_stock_app(t):
    t = rep(t, SA_SCHEMA_OLD, SA_SCHEMA_NEW, "stock_app: VOUCHER_SCHEMA head")
    t = rep(t, SA_SCHEMA_TAIL_OLD, SA_SCHEMA_TAIL_NEW, "stock_app: VOUCHER_SCHEMA tail")
    t = rep(t, SA_ENSURE_OLD, SA_ENSURE_NEW, "stock_app: _voucher_ensure + the void helpers")
    t = rep(t, SA_FROZEN_OLD, SA_FROZEN_NEW, "stock_app: _voucher_frozen")
    t = rep(t, SA_PEND_OLD, SA_PEND_NEW, "stock_app: _voucher_pending head")
    t = rep(t, SA_LOOP_OLD, SA_LOOP_NEW, "stock_app: _voucher_pending loop")
    t = rep(t, SA_APPEND_OLD, SA_APPEND_NEW, "stock_app: _voucher_pending tail")
    t = rep(t, SA_STATE_OLD, SA_STATE_NEW, "stock_app: _voucher_state")
    t = rep(t, SA_ENT_OLD, SA_ENT_NEW, "stock_app: the entered door")
    t = rep(t, SA_NUM_OLD, SA_NUM_NEW, "stock_app: _voucher_numbers")
    t = rep(t, SA_OPEN_OLD, SA_OPEN_NEW, "stock_app: amir_vouchers_open")
    t = rep(t, SA_BATCH_OLD, SA_BATCH_NEW, "stock_app: _s446_batches")
    t = rep(t, SA_A_OLD, SA_A_NEW, "stock_app: amir_stage A")
    t = rep(t, SA_REL_OLD, SA_REL_NEW, "stock_app: amir_stage release_next")
    t = rep(t, SA_UNREL_OLD, SA_UNREL_NEW, "stock_app: amir_stage C unreleased")
    t = rep(t, SA_C_OLD, SA_C_NEW, "stock_app: amir_stage C held")
    t = rep(t, SA_MORE_OLD, SA_MORE_NEW, "stock_app: _s452_release")
    t = rep(t, SA_WORDS_OLD, SA_WORDS_NEW, "stock_app: _s521_stage_words owner lines")
    t = rep(t, SA_QTY_OLD, SA_QTY_NEW, "stock_app: _s537_qty_en")
    return t


# ============================================================================================================== stock_watch.py (2.5)
SW_OLD = ('    try:\n'
          '        rows = con.execute("SELECT l.item, l.supplied, l.pack_size, l.arrived_at, o.vendor, o.created_at, l.id FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "\n'
          '                           "WHERE l.arrived_at IS NOT NULL AND l.arrived_at<? AND l.supplied>0 ORDER BY l.arrived_at", (cutoff,)).fetchall()\n')
SW_NEW = ('    try:                                                      # S537: an arrival tied to its bill (billed_bill_no, from Marg\'s own purchase lines) is never "bill missing"\n'
          '        rows = con.execute("SELECT l.item, l.supplied, l.pack_size, l.arrived_at, o.vendor, o.created_at, l.id FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "\n'
          '                           "WHERE l.arrived_at IS NOT NULL AND l.arrived_at<? AND l.supplied>0 AND COALESCE(l.billed_bill_no,\'\') = \'\' ORDER BY l.arrived_at", (cutoff,)).fetchall()\n')


def build_stock_watch(t):
    return rep(t, SW_OLD, SW_NEW, "stock_watch: bill_pending_lines")


# ============================================================================================================== shelf_figure.py (2.1)
SF_OLD = ('        tot = 0.0\n'
          '        for cid, rno, kind, bno, ch in con.execute("SELECT count_id, round_no, kind, batch_no, change FROM stock_voucher_line WHERE item=?", (item,)):\n')
SF_NEW = ('        tot = 0.0\n'
          '        try:                                                  # S537: the one void filter (stock_app._void_sql); a voided batch is never entered,\n'
          '            import stock_app as _sa537                        # noqa: PLC0415 -- so where stock_app cannot be loaded the sum is the same\n'
          '            vf = " AND " + _sa537._void_sql("l")\n'
          '        except Exception:                                     # noqa: BLE001\n'
          '            vf = ""\n'
          '        for cid, rno, kind, bno, ch in con.execute("SELECT count_id, round_no, kind, batch_no, change FROM stock_voucher_line l WHERE item=?" + vf, (item,)):\n')


def build_shelf_figure(t):
    return rep(t, SF_OLD, SF_NEW, "shelf_figure: filed_vouchers")


# ============================================================================================================== stock_statement.py (2.1)
ST_OLD = '    for r in con.execute("SELECT item, round_no FROM stock_voucher_line WHERE count_id=? ORDER BY round_no", (root,)):\n'
ST_NEW = ('    for r in con.execute("SELECT item, round_no FROM stock_voucher_line l WHERE count_id=? AND " + _sa()._void_sql("l") + " ORDER BY round_no",\n'
          '                         (root,)):                            # S537: a voided batch is on no round of the statement\n')


def build_statement(t):
    return rep(t, ST_OLD, ST_NEW, "stock_statement: rounds_by_item")


# ============================================================================================================== loss_piles.py (2.3)
LP_OLD = '    carried = {p["item"] for p in sa._voucher_pending(con, d)} | set(sa._voucher_frozen(con, root).keys())\n'
LP_NEW = ('    _o, _h, _u = sa._voucher_lines(con, d)                    # S537 (R1-9b): a held line is carried too -- the owner decides it; never worded again\n'
          '    carried = {p["item"] for p in _o} | {p["item"] for p in _h} | set(sa._voucher_frozen(con, root).keys())\n')


def build_loss_piles(t):
    return rep(t, LP_OLD, LP_NEW, "loss_piles: receive_close carried")


# ============================================================================================================== DUTY_MAP.json / .md (2.6)
VOID_SQL = ("(SELECT 1 FROM stock_voucher_void v WHERE v.count_id=b.count_id AND v.round_no=b.round_no AND v.kind=b.kind "
            "AND v.batch_no=b.batch_no)")
MAP_NOTE_ADD = (" S537 (12-Oct-2026, the owner's word of 07:02 IST): amir.count_vouchers honours the void -- a batch with a stock_voucher_void row"
                " is never due (the table is laid before this map is pulled).")
MAP_EDITS = (
    ('\n "version": 11,\n', '\n "version": 12,\n'),
    ('\n "kit": "S533_AMIR_DAY_PAGE",\n', '\n "kit": "S537_VOUCHER_GUARD",\n'),
    ('amir.marg_jobs counts a reopened job as due again (reopened_at).",\n "shared": {',
     'amir.marg_jobs counts a reopened job as due again (reopened_at).' + MAP_NOTE_ADD + '",\n "shared": {'),
    (') b WHERE NOT EXISTS', ') b WHERE NOT EXISTS ' + VOID_SQL + ' AND NOT EXISTS'),
    ('S524 (F-846): the due count is the orthotic batches and the released lots only",',
     'S524 (F-846): the due count is the orthotic batches and the released lots only -- S537: a voided batch is never due",'),
)


def build_duty_json(raw):
    j0 = json.loads(raw)
    if j0.get("version") != 11:
        raise Stop("DUTY_MAP.json is v%s, not v11" % j0.get("version"))
    du0 = [x for x in j0["duties"] if x.get("id") == "amir.count_vouchers"]
    if len(du0) != 1:
        raise Stop("DUTY_MAP.json: amir.count_vouchers occurs %d times" % len(du0))
    t = raw
    for a, n in MAP_EDITS:
        t = rep(t, a, n, "DUTY_MAP.json")
    j1 = json.loads(t)
    du1 = [x for x in j1["duties"] if x.get("id") == "amir.count_vouchers"][0]
    v11 = du0[0]["due_sql"]
    if du1["due_sql"] != v11.replace(") b WHERE NOT EXISTS", ") b WHERE NOT EXISTS " + VOID_SQL + " AND NOT EXISTS", 1):
        raise Stop("DUTY_MAP.json: the v12 due_sql is not the v11 one with the void test")
    if ";" in du1["due_sql"] or "\n" in du1["due_sql"]:
        raise Stop("DUTY_MAP.json: the v12 due_sql must stay one line with no ';'")
    # nothing else moved: every other duty, person and key byte-equal as data
    a0 = dict(j0, version=None, kit=None, _note=None, duties=[x for x in j0["duties"] if x.get("id") != "amir.count_vouchers"])
    a1 = dict(j1, version=None, kit=None, _note=None, duties=[x for x in j1["duties"] if x.get("id") != "amir.count_vouchers"])
    if a0 != a1 or j1["version"] != 12 or j1["kit"] != "S537_VOUCHER_GUARD":
        raise Stop("DUTY_MAP.json: something besides amir.count_vouchers, version, kit and _note moved")
    d0 = dict(du0[0], due_sql=None, duty=None)
    d1 = dict(du1, due_sql=None, duty=None)
    if d0 != d1:
        raise Stop("DUTY_MAP.json: amir.count_vouchers moved beyond its due_sql and duty")
    return t


MD_ROW_OLD = "| `stock_voucher_line` batches with no non-empty newest `stock_voucher_entered` row -- the orthotic batches and the released lots only (S524, F-846;"
MD_ROW_NEW = ("| `stock_voucher_line` batches, not voided (S537: no `stock_voucher_void` row), with no non-empty newest `stock_voucher_entered` row -- the "
              "orthotic batches and the released lots only (S524, F-846;")
MD_LOG_AFTER = ("`[amir.marg_jobs]` counts a reopened job as due again. The step and close rows read `amir_step_log`. No other login's list changes. "
                "`DUTY_MAP.json` is v11.\n")
MD_LOG_NEW = ("\n**12-Oct-2026 · kit S537_VOUCHER_GUARD (the owner's word of 07:02 IST):** `[amir.count_vouchers]` honours the void -- a batch with a "
              "`stock_voucher_void` row (append-only; voucher 29 of count #1 the first) is never due; a voucher line the guard holds (it would take "
              "Marg below zero by the item's full name on Marg's newest closing) is never made or released, so it is never due either -- it is the "
              "owner's Needs-you line only (\"Count #N: <item> -- ... not given to Amir\"). No duty added, moved or removed; no other login's list "
              "changes. `DUTY_MAP.json` is v12.\n")


def build_duty_md(t):
    t = rep(t, MD_ROW_OLD, MD_ROW_NEW, "DUTY_MAP.md row")
    return rep(t, MD_LOG_AFTER, MD_LOG_AFTER + MD_LOG_NEW, "DUTY_MAP.md log line")


def read_to(kit_dir):
    p = os.path.join(kit_dir, TO_FILE)
    out = {}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.startswith("TO[") and "]=" in line:
                k, v = line[3:].split("]=", 1)
                out[k] = v.strip()
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true")
    a = ap.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    to = read_to(here)
    os.makedirs(a.out, exist_ok=True)
    dirs = dict(finance=a.finance, briefs=a.briefs)
    builders = {"stock_app.py": build_stock_app, "stock_watch.py": build_stock_watch, "shelf_figure.py": build_shelf_figure,
                "stock_statement.py": build_statement, "loss_piles.py": build_loss_piles, "DUTY_MAP.json": build_duty_json,
                "DUTY_MAP.md": build_duty_md}
    rc = 0
    for name, fn in builders.items():
        where, frm = PINS[name]
        src = os.path.join(dirs[where], name)
        raw = open(src, "rb").read()
        m0 = md5(raw)
        if m0 != frm:
            if not a.print_to and name.startswith("DUTY_MAP") and to.get(name) == m0:
                with open(os.path.join(a.out, name), "wb") as fh:
                    fh.write(raw)
                print("   %-18s already at its TO pin %s (the clone was pulled) -- taken as it is" % (name, m0))
                continue
            print("!! %s is %s, not its FROM pin %s -- stopped" % (src, m0, frm))
            return 2
        try:
            new = fn(raw.decode("utf-8"))
        except Stop as e:
            print("!! %s: %s" % (name, e))
            return 2
        if name.endswith(".py"):
            try:
                compile(new, name, "exec")
            except SyntaxError as e:
                print("!! %s does not compile after the edits: %s" % (name, e))
                return 2
        nb = new.encode("utf-8")
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(nb)
        m = md5(nb)
        want = to.get(name)
        print("   %-18s %s -> %s  (%+d lines)%s" % (name, frm[:8], m, new.count("\n") - raw.decode("utf-8").count("\n"),
                                                  "" if (a.print_to or want == m) else "   !! not the kit's TO pin %s" % want))
        if not a.print_to and want != m:
            rc = 3
    return rc


if __name__ == "__main__":
    sys.exit(main())
