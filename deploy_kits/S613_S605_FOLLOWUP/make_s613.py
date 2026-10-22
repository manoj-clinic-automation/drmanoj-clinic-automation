#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s613.py -- kit S613_S605_FOLLOWUP: the builder. Anchored edits on the LIVE bytes of five finance files; no file re-typed.

    python3 -B make_s613.py --finance /root/finance --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the text it edits, else STOP (exit 2,
nothing written). Writes into DIR: stock_figure.py, order_sheet.py, porders_s454.py, porders.py, porders.html -- and prints each md5
(the installer compares them with PINS.sh). The brief: claude_code_briefs/S613_S605_FOLLOWUP.md (v2, 22-Oct-2026, Sanjeevni session 335).
F-951 (the readers' half): a size of a split shared key is figured by its share of the family up to the split day and by its own key after;
bills are matched to its order lines by size across the split. F-959: the old Purchase orders page no longer orders from Yuvika.
F-962: the call row counts today's orders still awaited. F-960: the wait starts at the hand-out; a late 'could not send' brings an
unconfirmed order back to reception's card; after the phone's own 'no' an order may be queued again (one rule on the audit trail)."""
import argparse
import hashlib
import os
import re
import sys

FROM = {
    "stock_figure.py": "51e1fc63ab3fb1ac21170cb214f15b6b",
    "order_sheet.py": "17fa1fdbd34d07b0af0535375926c4fc",
    "porders_s454.py": "7ca91d4f8eabc5cdb10c9df55f2c080b",
    "porders.py": "e5a5c4d4dfa15c3ecd0b0cdf4786abcd",
    "porders.html": "7a6799ae3c8b41e783051cd1280a6964",
}

# ======================================================================================================================= stock_figure.py
SF = []
SF.append(("F1 the version", 'VERSION = "1.3"\n', 'VERSION = "1.4"\n'))
SF.append(("F2 the kit", 'KIT = "S602_CUTOFF_LINE_AND_F943"', 'KIT = "S613_S605_FOLLOWUP"'))
SF.append(("F3 the kit history", '# v1.3 S598_ARRIVALS_BY_LINE, v1.2', '# v1.4 S613 (after S602), v1.3 S598_ARRIVALS_BY_LINE, v1.2'))
SF.append(("F4 the header's S613 paragraph", '''#  S602 (19-Oct-2026, F-943): the witness's read-only run never judges.''', '''#  S613 (22-Oct-2026, F-951 -- the readers' half of S605): THE SPLIT OF A SHARED KEY IS READ ONLY WHERE A READER SPANS DATES. S605's spine
#  gives each of the 22 renamed orthotic sizes its own key from its family's split day (sp_alias kind 'rename_family'); lines dated on or
#  before it stay under the old key. key_of() is NOT changed (stock_app's count-voucher proof judges keys between captures before the split).
#  split_of() -- the one place the split is known -- reads the spine's own alias note '(split YYYY-MM-DD from <old clip>)' by a strict
#  pattern, the old key through sp_item (cross-checked with the rename memory and the old key's RENAME_SPLIT date); a missing, unparsable
#  or disagreeing row = no split (today's figure) and one stderr line. split_moves() is the one helper for a split size's movements: the old
#  key's up to the split day times the size's counted share (shelf()'s rule over split_members: the old key's members in the newest usable
#  capture on or before the split day that prints it), plus the new key's after it. shelf(), marg() (and spine_move()) read it; old and
#  new name give the same figure. carried(): a split size's bill lines are its new key's (matched as today) plus its old key's matched by
#  printed name only (sib True: a sibling size's line never matches, R1-B3) -- rules (a)-(e) otherwise unchanged; the family-bill words
#  span the old family (the old key's lines to the split day, each sibling size's new key after it).
#  S602 (19-Oct-2026, F-943): the witness's read-only run never judges.'''))
SF.append(("F5 the split functions (after key_of)", '''    ctx.c[ck] = k
    return k


def family(sp, k20, md5, ctx=None):
''', '''    ctx.c[ck] = k
    return k


# ------------------------------------------------------------------ S613 (F-951): a size of a split shared key -- read only where a reader spans dates
SPLIT_RE = re.compile(r"\\(split (\\d{4}-\\d{2}-\\d{2}) from (.+)\\)\\s*$")     # the strict pattern of spine_build's rename_family note (R1-B2)


def _clip20(n):
    """spine_build.K, verbatim: the first 20 characters, spaces collapsed -- the clip a rename_family note names its old key by."""
    return re.sub(r"\\s+", " ", str(n or "").strip())[:20].strip()


def _split_warn(ctx, what):
    """One stderr line per row and Ctx: a split that cannot be read is no split (today's figure), never a typed date."""
    ck = ("split_warn", what)
    if ck not in ctx.c:
        ctx.c[ck] = True
        print("stock_figure: S613 split not read -- %s (today's figure kept)" % str(what)[:200], file=sys.stderr)


def _split_rows(sp, ctx):
    """{new_k: dict(new_k, old_k, day, old_clip, new_name)} from the spine alone (ctx.con only cross-checks): every sp_alias row of kind
    'rename_family' whose note parses by SPLIT_RE; new_k = the alias (= _k_by_name of its printed name in sp_item); old_k = the one sp_item key
    (not a rename_family key) whose printed names clip to the note's old clip -- for KNEE IMMOBILIZER the rules family 'KNEE IMMOBILI?ER UNI
    (family)' -- and, with a connection, the key _k_by_name gives the rename memory's old name; day cross-checked against the old key's
    RENAME_SPLIT move date where that row exists. Cached in the Ctx."""
    if "splits" in ctx.c:
        return ctx.c["splits"]
    out = {}
    try:
        rows = (sp.q("SELECT alias, k20, source FROM sp_alias WHERE kind='rename_family' ORDER BY alias")
                if (sp is not None and getattr(sp, "ok", False)) else [])
    except Exception:                                         # noqa: BLE001 -- no alias table: no split
        rows = []
    if rows:
        aliases = {str(r["alias"] or "") for r in rows}
        names = {}
        try:
            for r in sp.q("SELECT name, k20 FROM sp_item"):
                names.setdefault(str(r["k20"] or ""), []).append(str(r["name"] or ""))
        except Exception:                                     # noqa: BLE001
            names = {}
        by_clip = {}
        for k, ns in names.items():
            if k and k not in aliases:
                for n in ns:
                    by_clip.setdefault(_clip20(n), set()).add(k)
        kbn = _k_by_name(sp, ctx)
        for r in rows:
            new_k = str(r["alias"] or "")
            m = SPLIT_RE.search(str(r["source"] or ""))
            if not m or str(r["k20"] or "") != new_k:
                _split_warn(ctx, "%s: its rename_family note does not read '(split YYYY-MM-DD from <old>)'" % new_k)
                continue
            day, clip = m.group(1), m.group(2).strip()
            try:
                dt.date.fromisoformat(day)
            except ValueError:
                _split_warn(ctx, "%s: the split day '%s' is not a date" % (new_k, day))
                continue
            nn = sorted(n for n in names.get(new_k, []) if kbn.get(norm(n)) == new_k)
            if not nn:
                _split_warn(ctx, "%s: no printed name of sp_item stands under it" % new_k)
                continue
            olds = by_clip.get(clip, set())
            if len(olds) != 1:
                _split_warn(ctx, "%s: the old clip '%s' is %d keys, not one" % (new_k, clip, len(olds)))
                continue
            old_k = next(iter(olds))
            if ctx.con is not None:
                cand = {kbn.get(norm(f)) for f in printed_forms(ctx.con, nn[0], ctx)[1:]} - {None, "", new_k} - aliases
                if cand and old_k not in cand:
                    _split_warn(ctx, "%s: the rename memory's old name is under %s, not %s" % (new_k, sorted(cand), old_k))
                    continue
            try:
                mv = {str(x["d"]) for x in sp.q("SELECT DISTINCT date AS d FROM sp_move WHERE k20=? AND kind='RENAME_SPLIT'", old_k)}
            except Exception:                                 # noqa: BLE001
                mv = set()
            if mv and mv != {day}:
                _split_warn(ctx, "%s: the note says %s, the old key's RENAME_SPLIT says %s" % (new_k, day, sorted(mv)))
                continue
            out[new_k] = dict(new_k=new_k, old_k=old_k, day=day, old_clip=clip, new_name=nn[0])
    ctx.c["splits"] = out
    return out


def split_of(sp, name, ctx=None):
    """S613 (F-951): THE ONE PLACE THE SPLIT IS KNOWN. None, or dict(old_k, new_k, day, old_clip, new_name) for a printed name (old or new,
    or an accepted seen_name) of one of the sizes S605's spine split off a shared key. Derived from the spine (_split_rows); the connection
    only widens the name to its printed forms (an OLD name reaches its size only through the rename memory). Cached in the Ctx."""
    ctx = _ctx(None, sp, ctx)
    ck = ("split", norm(name))
    if ck in ctx.c:
        return ctx.c[ck]
    out = None
    rows = _split_rows(sp, ctx)
    if rows:
        kbn = _k_by_name(sp, ctx)
        for f in printed_forms(ctx.con, name, ctx):
            s = rows.get(kbn.get(norm(f)) or "")
            if s is not None:
                out = s
                break
    ctx.c[ck] = out
    return out


def split_members(sp, s, ctx=None):
    """S613 (R1-C3): the old key's members at the split -- family() within the NEWEST usable capture standing for a day on or before the split
    day that prints the old key, folded by printed_forms as family() does. A split-day capture printing only the new names does not print the
    old key; one printing spellings no count holds (11-10 09:52: 'SHOULDER IMMOBILISE L UNISON', not in the rename memory) cannot apportion
    the count, so the newest capture whose every member reaches a counted item (base()) is taken -- else the newest printing the old key."""
    ctx = _ctx(None, sp, ctx)
    ck = ("split_mem", s["old_k"])
    if ck not in ctx.c:
        have = {str(r["md5"]) for r in sp.q("SELECT DISTINCT md5 FROM sp_close_name WHERE k20=?", s["old_k"])}
        cs = sorted([c for c in usable_captures(sp, ctx) if c["end_day"] <= s["day"] and c["md5"] in have],
                    key=lambda c: (c["end_day"], c["stamp"]), reverse=True)
        pick = None
        if ctx.con is not None:
            for c in cs:
                fam = family(sp, s["old_k"], c["md5"], ctx)
                if fam and all(base(ctx.con, m[0], ctx) is not None for m in fam):
                    pick = fam
                    break
        if pick is None:
            pick = family(sp, s["old_k"], cs[0]["md5"] if cs else None, ctx)
        ctx.c[ck] = pick
    return ctx.c[ck]


def split_share(con, sp, name, s, ctx=None, exclude_id=None):
    """S613: (share, n) -- shelf()'s share rule over split_members: the size's counted base over the members' (below zero as 0); 1/n when
    nothing is counted. marg() reads it for a capture on or before the split day; shelf() computes the same inline over the same members."""
    ctx = _ctx(con, sp, ctx)
    mine = base(con, name, ctx, exclude_id)
    bases = [b for b in (base(con, m[0], ctx, exclude_id) for m in split_members(sp, s, ctx)) if b is not None]
    if mine is not None and not any(norm(b["item"]) == norm(mine["item"]) for b in bases):
        bases.append(mine)
    tot = sum(max(0.0, b["qty"]) for b in bases)
    n = len(bases)
    if mine is not None and tot > 0:
        return max(0.0, mine["qty"]) / tot, n
    return 1.0 / max(1, n), n


def split_moves(sp, s, share, d_from, d_to, incl_from=False, net=False):
    """S613 (F-951): THE ONE HELPER for a split size's movements over (d_from, d_to] (the count day's sales in with incl_from, as moves()): the
    OLD key's over (d_from, min(d_to, split day)] times the size's share, plus the NEW key's over (max(d_from, split day), d_to]. Returns
    (sold, returned, bought) -- or, net=True, the net of MOVE_KINDS (spine_move's figure). shelf(), marg() and spine_move() read it."""
    day, d_from, d_to = s["day"], str(d_from)[:10], str(d_to)[:10]
    if net:
        v = 0.0
        if d_from < day:
            v += share * spine_move(sp, s["old_k"], d_from, min(d_to, day))
        return v + spine_move(sp, s["new_k"], max(d_from, day), d_to)
    so = rt = bo = 0.0
    if d_from <= day:
        a, b, c = moves(sp, s["old_k"], d_from, min(d_to, day), incl_from)
        so, rt, bo = share * a, share * b, share * c
    a, b, c = moves(sp, s["new_k"], max(d_from, day), d_to, incl_from if d_from > day else False)
    return so + a, rt + b, bo + c


def family(sp, k20, md5, ctx=None):
'''))
SF.append(("F6 spine_move reads the helper for a split size", '''def spine_move(sp, k20, d_from, d_to):
    """The net of every movement kind the proof carries (MOVE_KINDS, never OPENING) over (d_from, d_to] -- what Marg's figure moved by."""
''', '''def spine_move(sp, k20, d_from, d_to, split=None, share=1.0):
    """The net of every movement kind the proof carries (MOVE_KINDS, never OPENING) over (d_from, d_to] -- what Marg's figure moved by.
    S613 (F-951): split = split_of()'s dict -> the split size's net through split_moves (the one helper), its share given."""
    if split is not None:
        return split_moves(sp, split, share, d_from, d_to, net=True)
'''))
SF.append(("F7 rule (b) for a split size (after _taken_lines)", '''    me = int(line_id) if line_id is not None else None
    return [t for t in ctx.c[ck] if t[0] != me]


def _purchase_lines_of(sp, k20, since_day, ctx):
''', '''    me = int(line_id) if line_id is not None else None
    return [t for t in ctx.c[ck] if t[0] != me]


def _taken_split(sp, sx, line_id, ctx):
    """S613 (R1-B3): rule (b) for a split size -- _taken_lines' entries for every OTHER billed order line whose key is the size's old key or its
    new key (each entry's sib its own key's); the caller matches a bill line of the OLD key with sib True (by printed name only)."""
    ck = ("taken_split", sx["new_k"])
    if ck not in ctx.c:
        out = []
        try:
            if ctx.con is not None:
                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''"):
                    kk = key_of(sp, item, ctx)
                    if kk in (sx["old_k"], sx["new_k"]):
                        out.append((int(lid), _sw().supkey(vendor), _bill(bno), _line_forms(ctx, item), _siblings(sp, kk, ctx)))
        except sqlite3.Error:
            out = []
        ctx.c[ck] = out
    me = int(line_id) if line_id is not None else None
    return [t for t in ctx.c[ck] if t[0] != me]


def _split_lines(sp, sx, since_day, ctx):
    """S613 (F-951, R1-B3): a split size's bill lines dated on or after since_day -- its NEW key's lines (matched as today, the new key's sib)
    and its OLD key's lines (sib True: matched by printed name only, a sibling size's line never matches) in one list, ordered as
    _purchase_lines_of orders it (date, bill, seq): [(line, k20, sib)]."""
    ck = ("splines", sx["new_k"], since_day)
    if ck not in ctx.c:
        rows = [(p, sx["new_k"], _siblings(sp, sx["new_k"], ctx)) for p in _purchase_lines_of(sp, sx["new_k"], since_day, ctx)]
        rows += [(p, sx["old_k"], True) for p in _purchase_lines_of(sp, sx["old_k"], since_day, ctx)]
        rows.sort(key=lambda t: (str(t[0]["date"] or ""), str(t[0]["bill"] or ""), _seqkey(t[0]["seq"])))
        ctx.c[ck] = rows
    return ctx.c[ck]


def _seqkey(v):
    s = str(v if v is not None else "")
    return (0, int(s), "") if re.match(r"^-?\\d+$", s) else (1, 0, s)


def _purchase_lines_of(sp, k20, since_day, ctx):
'''))
SF.append(("F8 _carried and _family_bill read both keys of a split size", '''def _carried(ctx, sp, line):
    sw = _sw()
    k = key_of(sp, line.get("item"), ctx)
    own = sw.supkey(line.get("vendor"))
    forms = _line_forms(ctx, line.get("item"))
    sib = _siblings(sp, k, ctx)
    bno = _bill(line.get("billed_bill_no"))
    if bno:                                                   # (a): the lines of that bill that MATCH, summed; the newest bill of the number
        hit = [p for p in _purchase_lines_of(sp, k, "", ctx) if _bill(p["bill"]) == bno and _matches(ctx, sp, k, forms, sib, p["name27"])]
''', '''def _carried(ctx, sp, line):
    sw = _sw()
    k = key_of(sp, line.get("item"), ctx)
    own = sw.supkey(line.get("vendor"))
    forms = _line_forms(ctx, line.get("item"))
    sib = _siblings(sp, k, ctx)
    sx = split_of(sp, line.get("item"), ctx)                  # S613 (F-951): a split size reads its new key's lines and its old key's by name (R1-B3)

    def lines_of(since):
        if sx is not None:
            return _split_lines(sp, sx, since, ctx)
        return [(p, k, sib) for p in _purchase_lines_of(sp, k, since, ctx)]
    bno = _bill(line.get("billed_bill_no"))
    if bno:                                                   # (a): the lines of that bill that MATCH, summed; the newest bill of the number
        hit = [p for (p, pk, ps) in lines_of("") if _bill(p["bill"]) == bno and _matches(ctx, sp, pk, forms, ps, p["name27"])]
'''))
SF.append(("F9 rules (b)-(e) over both keys of a split size", '''    lid = line.get("line_id")
    taken = _taken_lines(sp, k, lid, ctx)
    hit, hkey = None, None
    for p in _purchase_lines_of(sp, k, lo, ctx):
        sk, d, b = str(p["supkey"] or ""), str(p["date"] or "")[:10], _bill(p["bill"])
        if hit is not None and (sk, b, d) != hkey:
            break                                             # the first matching bill's lines are summed (two batches); a later bill never joins
        if any(t[1] == sk and t[2] == b and _matches(ctx, sp, k, t[3], t[4], p["name27"]) for t in taken):   # (b) per line
            continue
        if not _matches(ctx, sp, k, forms, sib, p["name27"]):
            continue
''', '''    lid = line.get("line_id")
    taken = _taken_split(sp, sx, lid, ctx) if sx is not None else _taken_lines(sp, k, lid, ctx)
    hit, hkey = None, None
    for p, pk, ps in lines_of(lo):
        sk, d, b = str(p["supkey"] or ""), str(p["date"] or "")[:10], _bill(p["bill"])
        if hit is not None and (sk, b, d) != hkey:
            break                                             # the first matching bill's lines are summed (two batches); a later bill never joins
        old_line = sx is not None and pk == sx["old_k"]       # S613: an old-key line is matched by printed name only, whoever matches it
        if any(t[1] == sk and t[2] == b and _matches(ctx, sp, pk, t[3], t[4] or old_line, p["name27"]) for t in taken):   # (b) per line
            continue
        if not _matches(ctx, sp, pk, forms, ps, p["name27"]):
            continue
'''))
SF.append(("F10 the family bill's call", '''        ctx.c[("fam_bill", lid)] = _family_bill(ctx, sp, k, lo, od, own, forms, sib)
''', '''        ctx.c[("fam_bill", lid)] = _family_bill(ctx, sp, k, lo, od, own, forms, sib, sx)
'''))
SF.append(("F11 the family bill spans the old family of a split size", '''def _family_bill(ctx, sp, k20, lo, od, own, forms, sib):
''', '''def _family_bill(ctx, sp, k20, lo, od, own, forms, sib, split=None):
'''))
SF.append(("F12 the family bill's lines", '''    order line still counts here: the clause says what the bill carried. Read by arrivals_open for the owner's words (stock_watch)."""
    sw = _sw()
    best, lines = None, {}
    for p in _purchase_lines_of(sp, k20, lo, ctx):
        sk, d = str(p["supkey"] or ""), str(p["date"] or "")[:10]
        if d < od and not (own and sk == own):
            continue
        if _matches(ctx, sp, k20, forms, sib, p["name27"]):
            continue
''', '''    order line still counts here: the clause says what the bill carried. Read by arrivals_open for the owner's words (stock_watch).
    S613 (F-951, R1-C4): for a split size (split = split_of's dict) the family spans the OLD family -- the old key's lines up to the split day
    plus each sibling size's new key lines after it, every one matched by printed name only (sib True)."""
    sw = _sw()
    best, lines = None, {}
    if split is None:
        src = [(p, sib) for p in _purchase_lines_of(sp, k20, lo, ctx)]
    else:
        src = [(p, True) for p in _purchase_lines_of(sp, split["old_k"], lo, ctx) if str(p["date"] or "")[:10] <= split["day"]]
        for s2 in sorted(_split_rows(sp, ctx).values(), key=lambda x: x["new_k"]):
            if s2["old_k"] == split["old_k"] and s2["new_k"] != split["new_k"]:
                src += [(p, True) for p in _purchase_lines_of(sp, s2["new_k"], lo, ctx) if str(p["date"] or "")[:10] > split["day"]]
        src.sort(key=lambda t: (str(t[0]["date"] or ""), str(t[0]["bill"] or ""), _seqkey(t[0]["seq"])))
    for p, psib in src:
        sk, d = str(p["supkey"] or ""), str(p["date"] or "")[:10]
        if d < od and not (own and sk == own):
            continue
        if _matches(ctx, sp, k20, forms, psib, p["name27"]):
            continue
'''))
SF.append(("F13 marg() figures a split size on its own key", '''    a = _iso(at)
    k = key_of(sp, name, ctx)
    fam = family(sp, k, c["md5"], ctx)
    sold, ret, bought = moves(sp, k, c["end_day"], a, incl_from=False)
    net = spine_move(sp, k, c["end_day"], a)
    cap = capture_of(sp, c["md5"], ctx)
''', '''    a = _iso(at)
    k = key_of(sp, name, ctx)
    sx = split_of(sp, name, ctx)                              # S613 (F-951): a split size is figured on its own key, by old name or new
    if sx is not None:
        k = sx["new_k"]
    fam = family(sp, k, c["md5"], ctx)
    if sx is not None and c["end_day"] <= sx["day"]:          # a capture on or before the split day: the helper (the share, then its own key)
        share = split_share(con, sp, name, sx, ctx)[0]
        sold, ret, bought = split_moves(sp, sx, share, c["end_day"], a)
        net = spine_move(sp, k, c["end_day"], a, split=sx, share=share)
        if c["end_day"] < sx["day"]:
            fam = split_members(sp, sx, ctx)
    else:
        sold, ret, bought = moves(sp, k, c["end_day"], a, incl_from=False)
        net = spine_move(sp, k, c["end_day"], a)
    cap = capture_of(sp, c["md5"], ctx)
'''))
SF.append(("F14 shelf(): the split size's members", '''    out.update(base=mine["qty"], base_kind=mine["kind"], base_day=mine["day"], base_at=mine["at"], marg0=mine.get("marg0"))
    bases = []
''', '''    out.update(base=mine["qty"], base_kind=mine["kind"], base_day=mine["day"], base_at=mine["at"], marg0=mine.get("marg0"))
    sx = split_of(sp, name, ctx)                              # S613 (F-951): a size of a split shared key
    bname = name
    if sx is not None and mine["day"] > sx["day"]:            # a base after the split day: the size alone, on its own key (as any item)
        k, bname = sx["new_k"], sx["new_name"]
        fam = family(sp, k, cap["md5"] if cap else None, ctx)
        out.update(key=k, members=fam)
        sx = None
    elif sx is not None:                                      # a base on or before it: the family's members at the split share its history
        fam = split_members(sp, sx, ctx)
        out["members"] = fam
    bases = []
'''))
SF.append(("F15 shelf(): the split size's moves", '''    sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=True)
    out.update(sold=round(share * sold, 2), returned=round(share * ret, 2), bought=round(share * bought, 2))
''', '''    if sx is not None:                                        # S613: the one helper -- the old key's share to the split day, its own key after
        sold, ret, bought = split_moves(sp, sx, share, mine["day"], a, incl_from=True)
        out.update(sold=round(sold, 2), returned=round(ret, 2), bought=round(bought, 2))
    else:
        sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=True)
        out.update(sold=round(share * sold, 2), returned=round(share * ret, 2), bought=round(share * bought, 2))
'''))
SF.append(("F16 shelf(): no boundary for a split size", '''    if n == 1 and mine["kind"] == "count" and cap is not None and not (   # S454 9.1: a bill dated before the count, entered after it
''', '''    if n == 1 and sx is None and mine["kind"] == "count" and cap is not None and not (   # S454 9.1 (S613: never across a split)
'''))
SF.append(("F17 shelf(): the boundary asks by the size's own name", '''            out["boundary"] = float(_sf_shelf().boundary_purchases(con, sp, name, mine["day"], mine.get("marg0"), (c["units"] if c else None),
''', '''            out["boundary"] = float(_sf_shelf().boundary_purchases(con, sp, bname, mine["day"], mine.get("marg0"), (c["units"] if c else None),
'''))
SF.append(("F18 shelf(): approx while the base is before the split", '''    out["shelf"] = int(round(v))
    out["approx"] = n > 1
    return out
''', '''    out["shelf"] = int(round(v))
    out["approx"] = n > 1 or sx is not None                   # S613: a split size is approx while its base is on or before the split day
    return out
'''))

# ======================================================================================================================= porders.py
PO = []
PO.append(("P1 api_send refuses (F-959)", '''@bp.route("/finance/porders/api/send", methods=["POST"])
def api_send():
    """Yuvika ko order bhejo: ONE purchase_order for the orthotic vendor, a line per shortage (the sender may have
    changed a quantity or switched a size), SENT by this person at this minute; the wa.me link comes back to the
    sender's browser only. A repeat within ten minutes returns the order already sent, no second order."""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind not in ("owner", "sender"):
        return _forbid_view(kind)
    pa = _pa()
    b = request.get_json(silent=True) or {}
    sh = shelf(con)
    names = {it["item"]: it for it in sh["items"]}
    clean = []
    for ln in (b.get("lines") or []):
        if not isinstance(ln, dict):
            continue
        item = str(ln.get("item") or "").strip()
        try:
            qty = int(ln.get("qty") or 0)
        except (TypeError, ValueError):
            qty = 0
        if item in names and qty > 0:
            it = names[item]
            clean.append(dict(item=item, qty=qty, pack_size=1, packing=it["packing"], rate_p=0, on_hand=it["shelf"], per_day=None, cover_after=None))
    if not clean:
        return jsonify(ok=False, error="malformed", message="Kuch order karne ko nahi hai."), 400
    recent = con.execute("SELECT id, created_at, sent_by, created_by FROM purchase_order WHERE vendor=? AND status IN ('sent','received') ORDER BY id DESC LIMIT 1",
                         (sh["vendor"],)).fetchone()
    if recent and _within(recent[1]):
        lines = [dict(item=l[0], qty=int(l[1]), packing=names.get(l[0], {}).get("packing", "1*1"), pack_size=1)
                 for l in con.execute("SELECT item, packs FROM purchase_order_line WHERE order_id=? ORDER BY id", (recent[0],))]
        url = pa._wa_url(pa._phone_for(con, sh["vendor"]), pa._wa_text(lines))
        return jsonify(ok=True, already=True, order_id=recent[0], wa_url=url, sent_text=_stamp(recent[1]), by=recent[2] or recent[3],
                       message="Yeh order abhi %s ko bheja ja chuka hai (%s). Dobara nahi bana." % (sh["vendor"], _stamp(recent[1])))
    resp = pa._staff_send(con, u, dict(vendor=sh["vendor"], lines=clean))
    r, code = (resp if isinstance(resp, tuple) else (resp, 200))
    j = r.get_json() or {}
    if code != 200 or not j.get("ok"):
        return jsonify(ok=False, error=j.get("error") or "send_failed", message=j.get("message") or "Order nahi bana."), code if code != 200 else 500
    con.execute("UPDATE purchase_order SET section=? WHERE id=?", (SECTION, j["order_id"]))
    _audit(con, u.get("user") or "", "porders_sent", j["order_id"], dict(vendor=sh["vendor"], lines=len(clean), source=sh["source"]))
    con.commit()
    return jsonify(ok=True, already=False, order_id=j["order_id"], wa_url=j["wa_url"], sent_text=_stamp(now_iso()), by=u.get("user") or "",
                   lines=[dict(item=l["item"], qty=l["qty"]) for l in clean], message="Order ban gaya -- WhatsApp khul raha hai.")
''', '''@bp.route("/finance/porders/api/send", methods=["POST"])
def api_send():
    """S613 (F-959, the second door): RETIRED. Yuvika's order goes only from reception's order page (order_sheet), after Darpan's yes
    (S605, D749). Any login: 409 ortho_via_order_page, nothing written. (The purchase page's staff send -- purchase_app /api/order
    action 'staff_send' -- is a third door, named for a later build.)"""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind not in ("owner", "sender"):
        return _forbid_view(kind)
    msg = ("Yuvika's order now goes from reception's order page, after Darpan's yes." if kind == "owner"
           else "Yuvika ka order ab 'Order karna hai' se jaata hai, Darpan ki haan ke baad.")
    return jsonify(ok=False, error="ortho_via_order_page", message=msg), 409
'''))

# ======================================================================================================================= porders.html
PH = []
PH.append(("H1 the order controls' state", "let S=null, MSG=null, BUSY=false, EN=false, QTY={}, PICK={}, OPEN={1:true,4:true}, SHORTQ={}, DQ={};",
           "let S=null, MSG=null, BUSY=false, EN=false, OPEN={1:true,4:true}, SHORTQ={}, DQ={};"))
PH.append(("H2 the send word", ''' marg:["Marg","Marg"], approx:["approx","approx"], send:["Yuvika ko order bhejo","Send the order to Yuvika"],
''', ''' marg:["Marg","Marg"], approx:["approx","approx"],
'''))
PH.append(("H3 the size word", ''' sizes:["doosra size:","other size:"], view:["Aap sirf dekh sakte hain.","View only."]
''', ''' view:["Aap sirf dekh sakte hain.","View only."]
'''))
PH.append(("H4 the quantity / size seed", ''' S.ortho.lines.forEach(l=>{if(QTY[l.item]==null)QTY[l.item]=l.short; if(PICK[l.item]==null)PICK[l.item]=l.item;});
''', ''))
PH.append(("H5 the orthotic table, read only (F-959)", ''' s.ortho.lines.forEach(l=>{
  const pick=PICK[l.item]||l.item, q=QTY[l.item];
  o+='<div class="line"><div class="nm">'+esc(pick)+(l.approx?'<span class="tag approx">'+L("approx")+'</span>':'')+'</div>'+
''', ''' s.ortho.lines.forEach(l=>{
  o+='<div class="line"><div class="nm">'+esc(l.item)+(l.approx?'<span class="tag approx">'+L("approx")+'</span>':'')+'</div>'+
'''))
PH.append(("H6 the -/+ and the size chips", '''     '<div class="qty"><span class="btn pm" onclick="dq(\\''+esc(l.item).replace(/'/g,"\\\\'")+'\\',-1)">−</span><b>'+q+'</b><span class="btn pm" onclick="dq(\\''+esc(l.item).replace(/'/g,"\\\\'")+'\\',1)">+</span></div>';
  if(l.approx&&l.sizes.length) o+='<div class="muted">'+L("sizes")+' '+[l.item].concat(l.sizes).map(sz=>'<span class="btn chip'+(pick===sz?' on':'')+'" onclick="ps(\\''+esc(l.item).replace(/'/g,"\\\\'")+'\\',\\''+esc(sz).replace(/'/g,"\\\\'")+'\\')">'+esc(sz.replace(l.family,'').trim()||sz)+(l.sizes_shelf&&l.sizes_shelf[sz]!=null?' ('+l.sizes_shelf[sz]+')':'')+'</span>').join("")+'</div>';
''', '''     '<div class="qty"><b>'+esc(l.short)+'</b></div>';
'''))
PH.append(("H7 the Yuvika button", ''' if(s.ortho.lines.length&&canWrite()) o+='<span class="btn ok big" onclick="send()">'+L("send")+'</span>';
''', ''))
PH.append(("H8 dq / ps", '''function dq(item,d){QTY[item]=Math.max(0,(QTY[item]||0)+d);render();}
function ps(item,sz){PICK[item]=sz;render();}
''', ''))
PH.append(("H9 send()", '''async function send(){
 if(BUSY)return;BUSY=true;
 const lines=S.ortho.lines.map(l=>({item:PICK[l.item]||l.item,qty:QTY[l.item]})).filter(l=>l.qty>0);
 try{const j=await post("/finance/porders/api/send",{lines});
  MSG={kind:j.already?"dup":"",title:j.already?L("dup"):L("saved"),lines:[esc(j.message||""),"Order #"+j.order_id+" · "+esc(j.sent_text)+" · "+esc(j.by),(j.wa_url?L("openwa"):"")]};
  QTY={};PICK={};await load();
  if(j.wa_url){window.location.href=j.wa_url;}
 }catch(e){MSG={kind:"err",title:L("err"),lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
''', ''))

# ======================================================================================================================= porders_s454.py
PS = []
PS.append(("S1 the call row counts today's orders still awaited (F-962)", '''        if k == "order" and c[k] <= 0:                        # S605 (F-962): nothing left to order -- the day's orders, each with its Call
            nd = len(_done_today(con))                        # the 'Ho chuke' rule of the order list (charter 13)
''', '''        if k == "order" and c[k] <= 0:                        # S605 (F-962): nothing left to order -- the day's orders, each with its Call
            try:                                              # S613 (F-962): THE count, here only -- today's s454 orders still 'sent' (any way but paper)
                nd = int(con.execute("SELECT COUNT(*) FROM purchase_order WHERE order_src='s454' AND status='sent' AND order_via<>'paper' "
                                     "AND substr(created_at,1,10)=?", (OS.today().isoformat(),)).fetchone()[0])
            except sqlite3.Error:
                nd = 0
'''))
PS.append(("S2 _done_today's numbers through book_card", '''        out.append(dict(id=o["id"], vendor=o["vendor"], sn=o.get("supplier_norm") or _pa().supplier_key(o["vendor"]), via=o.get("order_via") or "",
                        sent_at=sent_at, by=o.get("created_by") or "", phone=_pa().book_number(con, o["vendor"], "call"),   # S574: the Calls number
                        wa=_pa().book_number(con, o["vendor"], "order")))                                                     # S605: the Order WhatsApp number
''', '''        call, wa, _shown, _on = OS.book_card(con, o["vendor"])  # S613: the phone book's one reader (S574) -- the Calls and the Order WhatsApp number
        out.append(dict(id=o["id"], vendor=o["vendor"], sn=o.get("supplier_norm") or _pa().supplier_key(o["vendor"]), via=o.get("order_via") or "",
                        sent_at=sent_at, by=o.get("created_by") or "", phone=call, wa=wa))
'''))

# ======================================================================================================================= order_sheet.py
OS_ = []
OS_.append(("O1 the header's S613 paragraph", '''#      nothing queued) when the list the screen showed is not the list now.
# =============================================================================
''', '''#      nothing queued) when the list the screen showed is not the list now.
#
#  S613_S605_FOLLOWUP (22-Oct-2026; F-960, three loose ends):
#    * THE WAIT STARTS AT THE HAND-OUT. withdraw_late: a handed message becomes unconfirmed when its handed_at is order.whatsapp_wait_min old
#      and is never withdrawn by queued_at; a never-handed message is withdrawn from queued_at, its UPDATE guarded (handed_at NULL, queued).
#    * A LATE "COULD NOT SEND" on an order unconfirmed in this cycle (on_message_done): nothing arrived on it -> the order is a draft again
#      (sent_by NULL, its ordered lines in_line, the message skipped, audit s454_whatsapp_unconfirmed_no) and reception's card reads
#      'WhatsApp nahi gaya -- call kijiye'; something arrived -> the order unchanged, the message skipped, audit
#      s454_whatsapp_unconfirmed_no_arrived, and the owner reads one line that day.
#    * MAY IT BE SENT AGAIN -- ONE RULE (_s613_phone_said_no), read by order_supplier's withdrawn branch and wa_plan: the order's newest
#      audit row of the message's cycle is the phone's own no, and the message is skipped, never sent, handed. Once per no, never after
#      a silence.
# =============================================================================
'''))
OS_.append(("O2 order_supplier: after the phone's own no it may be queued again", '''            if _s605_handed(con, oid):                        # S605 (F-960): once handed to the phone, never queued again -- call
''', '''            if _s605_handed(con, oid) and not _s613_phone_said_no(con, oid):   # S605 (F-960): handed -> call; S613: unless the phone said no
'''))
OS_.append(("O3 the one rule (after _s605_handed)", '''def _s605_handed(con, oid):
    """S605 (F-960): the order's message was handed to the reception phone (handed_at, never reset by the server)."""
    return con.execute("SELECT 1 FROM supplier_msg WHERE kind='order' AND ref=? AND handed_at IS NOT NULL LIMIT 1", (int(oid),)).fetchone() is not None
''', '''def _s605_handed(con, oid):
    """S605 (F-960): the order's message was handed to the reception phone (handed_at, never reset by the server)."""
    return con.execute("SELECT 1 FROM supplier_msg WHERE kind='order' AND ref=? AND handed_at IS NOT NULL LIMIT 1", (int(oid),)).fetchone() is not None


S613_CYCLE = ("s454_whatsapp_queued", "s454_whatsapp_requeued", "s454_whatsapp_withdrawn", "s454_whatsapp_unconfirmed",
              "s454_whatsapp_unconfirmed_no", "s454_whatsapp_sent")


def _s613_phone_said_no(con, oid):
    """S613 (F-960): THE ONE RULE 'may this order's message be queued again', read by order_supplier's withdrawn branch and by wa_plan.
    True only when the NEWEST of the order's audit rows of the message's cycle (S613_CYCLE) is the phone's own no -- s454_whatsapp_withdrawn
    with why 'the phone could not send', or s454_whatsapp_unconfirmed_no -- AND the message is skipped, never sent (sent_at NULL) and was
    handed (handed_at set). The history of answers lives only in purchase_audit (api_done overwrites status and last_error). Once per no;
    a handed message the phone never answered is never queued again (call instead)."""
    try:
        m = con.execute("SELECT status, sent_at, handed_at FROM supplier_msg WHERE kind='order' AND ref=? ORDER BY id DESC LIMIT 1", (int(oid),)).fetchone()
        if not m or m[0] != "skipped" or m[1] or not m[2]:
            return False
        r = con.execute("SELECT action, detail FROM purchase_audit WHERE ref=? AND action IN (%s) ORDER BY id DESC LIMIT 1" % ",".join("?" * len(S613_CYCLE)),
                        (str(int(oid)),) + S613_CYCLE).fetchone()
    except (sqlite3.Error, TypeError, ValueError):
        return False
    if not r:
        return False
    if r[0] == "s454_whatsapp_unconfirmed_no":
        return True
    if r[0] == "s454_whatsapp_withdrawn":
        try:
            d = json.loads(r[1] or "{}")
        except ValueError:
            d = {}
        return isinstance(d, dict) and d.get("why") == "the phone could not send"
    return False
'''))
OS_.append(("O4 wa_plan reads the one rule", '''        if e["state"] == "withdrawn" and _s605_handed(con, (e.get("draft") or {}).get("id") or 0):
            call.append(e)
''', '''        did = (e.get("draft") or {}).get("id") or 0
        if e["state"] == "withdrawn" and _s605_handed(con, did) and not _s613_phone_said_no(con, did):   # S613: after the phone's no, queued again
            call.append(e)
'''))
OS_.append(("O5 on_message_done: a late no on an unconfirmed order", '''        audit(con, "reception-phone", "s454_whatsapp_sent", oid, dict(supplier=r[3], message=int(mid)))
    else:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?", (("withdrawn: phone could not send — %s" % (err or ""))[:200], int(mid)))
''', '''        audit(con, "reception-phone", "s454_whatsapp_sent", oid, dict(supplier=r[3], message=int(mid)))
    elif _s613_unconfirmed_now(con, oid, int(mid), o):        # S613 (F-960): the phone's no after the unconfirmed hour
        _s613_late_no(con, oid, int(mid), r[3], err, t)
    else:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?", (("withdrawn: phone could not send — %s" % (err or ""))[:200], int(mid)))
'''))
OS_.append(("O6 the late no's two branches (before withdraw_late)", '''def withdraw_late(con):
''', '''def _s613_unconfirmed_now(con, oid, mid, o):
    """S613 (F-960): the order was made 'sent' by the unconfirmed step in THIS cycle -- an audit row s454_whatsapp_unconfirmed newer than its
    newest s454_whatsapp_requeued -- cross-checked structurally: the order sent (or received) by WhatsApp, the message never sent."""
    try:
        if not o or o[1] not in ("sent", "received") or o[2] != "whatsapp":
            return False
        m = con.execute("SELECT sent_at FROM supplier_msg WHERE id=?", (int(mid),)).fetchone()
        if not m or m[0]:
            return False
        un = con.execute("SELECT MAX(id) FROM purchase_audit WHERE ref=? AND action='s454_whatsapp_unconfirmed'", (str(int(oid)),)).fetchone()[0]
        rq = con.execute("SELECT MAX(id) FROM purchase_audit WHERE ref=? AND action='s454_whatsapp_requeued'", (str(int(oid)),)).fetchone()[0]
    except sqlite3.Error:
        return False
    return bool(un) and (rq is None or int(un) > int(rq))


def _s613_late_no(con, oid, mid, vendor, err, t):
    """S613 (F-960): the phone said it could not send an order already marked sent-unconfirmed. Nothing arrived on it (no line supplied, billed
    or arrived, no bill-scan tie) -> the order is a draft again, sent_by NULL, the lines the unconfirmed step made ordered back in_line, the
    message skipped with the phone's error, audit s454_whatsapp_unconfirmed_no: reception's card reads 'WhatsApp nahi gaya -- call kijiye'.
    Something arrived -> the order unchanged, the message skipped, audit s454_whatsapp_unconfirmed_no_arrived (the owner's line, today)."""
    n = con.execute("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=? AND (supplied IS NOT NULL OR COALESCE(billed_bill_no,'')<>'' "
                    "OR arrived_at IS NOT NULL)", (oid,)).fetchone()[0]
    try:
        tie = con.execute("SELECT 1 FROM order_scan_tie WHERE order_id=?", (oid,)).fetchone() is not None
    except sqlite3.Error:
        tie = False
    oa = con.execute("SELECT created_at FROM purchase_order WHERE id=?", (oid,)).fetchone()
    od = _dtm(oa[0]) if oa else None
    if not n and not tie:
        con.execute("UPDATE purchase_order SET status='draft', sent_by=NULL WHERE id=? AND status='sent'", (oid,))
        con.execute("UPDATE order_sheet_line SET state='in_line', updated_at=? WHERE order_id=? AND state='ordered'", (t, oid))
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?",
                    (("withdrawn: phone could not send (after the unconfirmed hour) — %s" % (err or ""))[:200], mid))
        audit(con, "reception-phone", "s454_whatsapp_unconfirmed_no", oid, dict(supplier=vendor, message=mid, why="the phone could not send",
                                                                                error=(err or "")[:120]))
    else:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?",
                    (("could not send, but goods already came in on the order -- nothing changed — %s" % (err or ""))[:200], mid))
        audit(con, "reception-phone", "s454_whatsapp_unconfirmed_no_arrived", oid, dict(supplier=vendor, message=mid, error=(err or "")[:120],
                                                                                        order_hm=(od.strftime("%H:%M") if od else "")))


def withdraw_late(con):
'''))
OS_.append(("O7 withdraw_late: the wait from the hand-out; a guarded withdrawal", '''    for mid, st, qa, ref, vendor, handed in rows:
        d = _dtm(qa)
        if st != "failed" and handed and d and (now() - d) >= dt.timedelta(minutes=wait):
            _s605_unconfirmed(con, mid, ref, vendor, handed, wait)
            n += 1
            continue
        if st == "failed" or (d and (now() - d) >= dt.timedelta(minutes=wait)):
            o = con.execute("SELECT status FROM purchase_order WHERE id=?", (int(ref or 0),)).fetchone()
            con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=?",
                        ("withdrawn: %s" % ("the phone could not send" if st == "failed" else "not sent within %d minutes" % wait), mid))
            audit(con, "order sheet", "s454_whatsapp_withdrawn", ref, dict(supplier=vendor, message=mid, why=st, order_status=(o[0] if o else None)))
            n += 1
''', '''    for mid, st, qa, ref, vendor, handed in rows:
        d = _dtm(qa)
        if st != "failed" and handed:                         # S613 (F-960): a handed message waits from its hand-out -- never withdrawn by queued_at
            h = _dtm(handed)
            if h and (now() - h) >= dt.timedelta(minutes=wait):
                _s605_unconfirmed(con, mid, ref, vendor, handed, wait)
                n += 1
            continue
        if st == "failed" or (d and (now() - d) >= dt.timedelta(minutes=wait)):
            o = con.execute("SELECT status FROM purchase_order WHERE id=?", (int(ref or 0),)).fetchone()
            cur = con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=? AND " +
                              ("status='failed'" if st == "failed" else "handed_at IS NULL AND status='queued'"),   # S613: never a message handed meanwhile
                              ("withdrawn: %s" % ("the phone could not send" if st == "failed" else "not sent within %d minutes" % wait), mid))
            if cur.rowcount == 1:
                audit(con, "order sheet", "s454_whatsapp_withdrawn", ref, dict(supplier=vendor, message=mid, why=st, order_status=(o[0] if o else None)))
                n += 1
'''))
OS_.append(("O8 the owner's line of a late no on arrived goods", '''            out.append(dict(cls="warn", target="porders", text="%s — the reception phone took the order at %s but never confirmed it. It was not sent again. "
                            "Check the reception phone's WhatsApp chat with %s." % (vendor, at, vendor)))
    except Exception:                                         # noqa: BLE001
        pass
    return out
''', '''            out.append(dict(cls="warn", target="porders", text="%s — the reception phone took the order at %s but never confirmed it. It was not sent again. "
                            "Check the reception phone's WhatsApp chat with %s." % (vendor, at, vendor)))
    except Exception:                                         # noqa: BLE001
        pass
    try:                                                      # S613 (F-960): the phone's late no on an order goods already came in on (today)
        for (detail,) in con.execute("SELECT detail FROM purchase_audit WHERE action='s454_whatsapp_unconfirmed_no_arrived' AND substr(at,1,10)=? ORDER BY id",
                                     (now().date().isoformat(),)).fetchall():
            try:
                d = json.loads(detail or "{}")
            except ValueError:
                d = {}
            out.append(dict(cls="warn", target="porders", text="%s — the reception phone said it could not send the order of %s, but goods have already "
                            "come in on it. Nothing was changed." % (d.get("supplier") or "", d.get("order_hm") or "")))
    except Exception:                                         # noqa: BLE001
        pass
    return out
'''))

EDITS = {"stock_figure.py": SF, "order_sheet.py": OS_, "porders_s454.py": PS, "porders.py": PO, "porders.html": PH}


def apply(raw, edits, label, pin):
    m = hashlib.md5(raw).hexdigest()
    if m != pin:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (label, m, pin))
        return None
    t = raw.decode("utf-8")
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(open(os.path.join(a.finance, label), "rb").read(), edits, label, FROM[label])
        if out is None:
            return 2
        built[label] = out
    t = {k: v.decode("utf-8") for k, v in built.items()}
    # ---- the grep proofs (charter 7 and 9) on the built text
    s = t["stock_figure.py"]
    assert s.count("def split_of(") == 1 and s.count("split_of(sp, ") == 4, "split_of: defined once; read by shelf, marg, _carried"
    assert s.count("def split_moves(") == 1 and s.count("split_moves(sp, ") == 4, "split_moves: the one helper, read by shelf, marg, spine_move"
    k0 = re.search(r"\ndef key_of\(.*?\n\n\n", s, re.S).group(0)
    k1 = re.search(r"\ndef key_of\(.*?\n\n\n", open(os.path.join(a.finance, "stock_figure.py"), encoding="utf-8").read(), re.S).group(0)
    assert k0 == k1, "key_of is not changed (R1-B1)"
    assert s.count("SPLIT_RE.search(") == 1 and s.count("SPLIT_RE = re.compile(") == 1, "the strict pattern: defined once, read once"
    p = t["porders.py"]
    fn = p.split("def api_send():", 1)[1].split("\n@bp.route", 1)[0]
    assert "porders_sent" not in fn and "_staff_send" not in fn and "execute(" not in fn and p.count('error="ortho_via_order_page"') == 1, "api_send writes nothing"
    assert p.count('"porders_sent"') == 0, "api_send was the only writer of porders_sent"
    assert "def _within(" in p and "def _stamp(" in p, "_within / _stamp stay (other callers)"
    h = t["porders.html"]
    for w in ("send()", "Yuvika ko order bhejo", "dq(", "ps(", "QTY", "PICK", 'L("send")', 'L("sizes")'):
        assert w not in h, "porders.html still holds %s" % w
    assert "async function sendMed(" in h and 'L("openwa")' in h and "dup" in h, "sendMed, openwa (sendDay) and dup stay"
    q = t["porders_s454.py"]
    assert "_pa().book_number(" not in q.split("def _done_today(", 1)[1].split("\ndef ", 1)[0], "_done_today: no direct book_number"
    assert q.count("OS.book_card(con,") >= 1 and q.count('"r_call"') == 2 and q.count("_done_today(con)") == 2, "the call row no longer reads _done_today"
    o = t["order_sheet.py"]
    assert o.count("_s613_phone_said_no(con,") == 3 and o.count("def _s613_phone_said_no(") == 1, "the one rule: order_supplier and wa_plan"
    assert o.count("_s613_late_no(con,") == 2 and o.count("_s613_unconfirmed_now(con,") == 2
    assert "handed_at IS NULL AND status='queued'" in o
    for label, out in built.items():                           # no run of ten digits added (a phone number) -- the live text's own are kept
        src = open(os.path.join(a.finance, label), "rb").read()
        assert len(re.findall(rb"\d{10}", out)) == len(re.findall(rb"\d{10}", src)), "a run of ten digits added in %s" % label
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (label, hashlib.md5(out).hexdigest(), FROM[label]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
