#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s704.py -- kit S704_SPINE_VOUCHER_FOLD (03-Nov-2026, Sanjeevni session 383).

    python3 -B make_s704.py <root> <outdir>     reads <root>/finance/spine/spine_build.py and <root>/finance/order_rules.py (each at its
                                                FROM pin, else REFUSED); writes both under <outdir>/finance/...

WHY.  The owner's word at the S380 close (03-Nov 11:20 IST): "build in next session" -- the buying model's section 9 step 3, after the
first scored levels week (scored the night of 1-Nov): F-1025 and F-1028, both display / classification only.

WHAT.  Anchored edits -- each anchor exactly once, else REFUSED; nothing else in either file moves.
  spine/spine_build.py (1cd20ead):
    1. BUILD_VERSION S605.1 -> S704.1.
    2. the docstring: the S704 paragraph.
    3. filed_vouchers(finance_db) and _voucher_day: Amir's stock vouchers that are IN Marg, read READ-ONLY through the --finance-db door
       the build already opens (S404) -- shelf_figure.filed_vouchers' rule: the newest stock_voucher_entered row of a batch carries a
       voucher number, no stock_voucher_void row voids it; its day is entered_on read as a date, else the day of `at`.
    4. the classing: a finding equal (within half a unit) to the vouchers filed after the opening and up to that closing is
       "VOUCHER: ...", not OPEN / TIMING. sp_move gets nothing (the vouchers are never booked: Marg's exports carry none).
    5. the STOCK gate row's detail names the open ones only and how many the vouchers explain; its ok and blocking are unchanged
       (an --acceptance build still refuses any difference).
  order_rules.py (5e8330b3): ONE section appended before the script tail (the S644 wrapper pattern), nothing above it edited:
    plan()            a line with no model word (a carried short-supplied line) takes the day's model word (F-1028 c).
    _s644_stamp_day   / _s644_relist: the inputs the list stood on are kept beside made_through (order_notice slot inputs_note).
    _s644_owner       the fold's `inputs` come from the newest kept list (F-1028 a); the relist and stale lines in plain words (F-1028 b).
  NEVER writes order.source; no quantity, supplier or rail of any line changes; order_rehearsal.py (the score) is not touched.
"""
import hashlib
import os
import sys

FROM = {"finance/spine/spine_build.py": "1cd20ead1c19ea0418c88bd728374e9c",
        "finance/order_rules.py": "5e8330b33ba42ecd147f630bb25ea836"}

SB_DOC_OLD = ("  the family's sum is unchanged). A family no closing yet prints is aliased as before. A solo rename is aliased as before.\n"
              '"""\n')
SB_DOC_NEW = ("  the family's sum is unchanged). A family no closing yet prints is aliased as before. A solo rename is aliased as before.\n"
              "* S704 (F-1025): Amir's stock vouchers that are IN Marg (finance.db, read-only through the same door: the newest\n"
              "  stock_voucher_entered row of a batch carries a voucher number and no stock_voucher_void row voids it) are never booked --\n"
              "  Marg's exports carry no voucher -- but a stock difference equal to the vouchers filed after the opening and up to that\n"
              "  closing is classed VOUCHER, not OPEN: the status line's EXCEPT names only what is still unexplained.\n"
              '"""\n')

SB_FN_ANCHOR = "class Gate:\n    def __init__(self):\n"
SB_FN_NEW = '''def _voucher_day(entered_on, at):
    """S704: the ISO day a voucher batch was filed -- entered_on read as dd-mm-yyyy, dd/mm/yyyy or ISO, else the day of `at` (the rule of
    shelf_figure._s488_entry_day). None when neither is a date."""
    s = str(entered_on or "").strip()
    m = re.match(r"^(\\d\\d)[-/](\\d\\d)[-/](\\d{4})$", s)
    for cand in (("%s-%s-%s" % (m.group(3), m.group(2), m.group(1))) if m else s[:10] if re.match(r"^\\d{4}-\\d\\d-\\d\\d", s) else "",
                 str(at or "")[:10]):
        try:
            return dt.date.fromisoformat(cand).isoformat()
        except ValueError:
            continue
    return None


def filed_vouchers(finance_db):
    """S704 (F-1025): {Marg's item name: [(ISO day filed, signed units), ...]} -- every line of a voucher batch that is IN Marg, read from
    finance.db READ-ONLY. A batch counts while the newest stock_voucher_entered row of (count, round, kind, batch) carries a voucher number
    and no stock_voucher_void row voids it (shelf_figure.filed_vouchers' rule). No tables, no door, an unreadable file: nothing."""
    out = collections.defaultdict(list)
    if not finance_db:
        return out
    try:
        con = sqlite3.connect("file:%s?mode=ro" % finance_db, uri=True)
        try:
            have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"stock_voucher_line", "stock_voucher_entered"} <= have:
                return out
            state = {}
            for cid, rno, kind, bno, vno, eon, at in con.execute("SELECT count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, at "
                                                                 "FROM stock_voucher_entered ORDER BY id"):
                state[(cid, rno, kind, bno)] = (vno, eon, at)
            void = set()
            if "stock_voucher_void" in have:
                void = {tuple(r) for r in con.execute("SELECT count_id, round_no, kind, batch_no FROM stock_voucher_void")}
            day_of = {}
            for k, (vno, eon, at) in state.items():
                if str(vno or "").strip() and k not in void:
                    d = _voucher_day(eon, at)
                    if d:
                        day_of[k] = d
            for cid, rno, kind, bno, item, ch in con.execute("SELECT count_id, round_no, kind, batch_no, item, change FROM stock_voucher_line"):
                d = day_of.get((cid, rno, kind, bno))
                if d and item:
                    out[item].append((d, float(ch or 0)))
        finally:
            con.close()
    except sqlite3.Error:
        return collections.defaultdict(list)
    return out


'''

SB_CLASS_OLD = ("    classed = []\n"
                "    for d, k, x in findings:\n"
                "        if d == last:\n"
                '            classed.append((d, k, x, "OPEN at the latest closing"))\n'
                "            continue\n")
SB_CLASS_NEW = ("    vch = collections.defaultdict(list)                          # S704 (F-1025): Amir's filed vouchers by the spine's key\n"
                "    for vname, vrows in filed_vouchers(finance_db).items():\n"
                "        for vd, vu in vrows:\n"
                "            vch[Zd(vname, vd)].append((vd, vu))\n"
                "\n"
                "    def vch_to(k, d):\n"
                '        return round(sum(u for vd, u in vch.get(k, []) if op["as_on"] < vd <= d), 3)\n'
                "    classed = []\n"
                "    for d, k, x in findings:\n"
                "        v = vch_to(k, d)\n"
                "        if v and abs(x - v) < 0.5:\n"
                '            classed.append((d, k, x, "VOUCHER: Amir\'s stock voucher filed in Marg (%+g) -- Marg\'s exports carry no voucher" % v))\n'
                "            continue\n"
                "        if d == last:\n"
                '            classed.append((d, k, x, "OPEN at the latest closing"))\n'
                "            continue\n")

SB_GATE_OLD = ('          "items equal per closing: %s; pending (exports not complete yet): %s; open: %s" % (dict(per_date), pending, at_last[:12]),\n')
SB_GATE_NEW = ('          "items equal per closing: %s; pending (exports not complete yet): %s; open: %s; explained by Amir\'s filed vouchers: %d" % (\n'
               '              dict(per_date), pending, [f[:3] for f in findings if f[0] == last and f[3].startswith("OPEN")][:12],\n'
               '              sum(1 for f in findings if f[0] == last and f[3].startswith("VOUCHER"))),\n')

OR_TAIL = ('# ---- S644 end ---------------------------------------------------------------------------------------------------------------------------\n'
           '\n\nif __name__ == "__main__":')
OR_SECTION = '''# ---- S644 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S704 (F-1028, 03-Nov-2026, Sanjeevni session 383): the owner's fold of the levels model -- display only ------------------------------
#  (c) plan(): a line that carries no model word (a carried short-supplied line, built in plan()'s own loop) takes the day's word --
#      before S704 it fell into "fixed" in the score's per-model split on a levels day. No quantity, supplier or rail changes.
#  (a) the inputs the list stood on are kept beside made_through (order_notice slot inputs_note, one row a day): the fold read only the
#      web process's own last note, which exists only after some page ran plan() (the order card, the sheet compare) -- so the line was
#      mostly not drawn, and when it was, it was that page's plan, not the list's. The kept list's note now wins.
#  (b) the relist / stale lines are said in words, not as the raw JSON stamp. The stored texts are unchanged (the relist compares them).
plan_before_s704 = plan
_s644_stamp_day_before_s704 = _s644_stamp_day
_s644_relist_before_s704 = _s644_relist
_s644_owner_before_s704 = _s644_owner


def plan(con, today=None, suppliers=None):                      # noqa: F811
    d = plan_before_s704(con, today, suppliers)
    try:
        word = "levels" if _s644_on(con) else "fixed"
        for v in (d.get("vendors") or {}).values():
            for l in v.get("lines") or []:
                if isinstance(l, dict) and "model" not in l:
                    l["model"] = word
    except Exception:                                            # noqa: BLE001 -- a word for the owner's eyes never breaks a plan
        pass
    return d


def _s704_keep_note(con, today):
    """The note of the plan just made on this thread, kept as today's inputs_note (fail-soft; one row a day, the newest wins)."""
    try:
        note = _s470_inputs_note()
        if not note:
            return
        con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                    (today.isoformat(), "inputs_note", json.dumps(note, default=str, sort_keys=True, ensure_ascii=False), None, now_iso()))
        con.commit()
    except Exception:                                            # noqa: BLE001
        pass


def _s644_stamp_day(con, today):                                # noqa: F811
    _s644_stamp_day_before_s704(con, today)
    _s704_keep_note(con, today)


def _s644_relist(con, today, now):                              # noqa: F811
    r = _s644_relist_before_s704(con, today, now)
    if str(r).startswith("relisted"):
        _s704_keep_note(con, today)
    return r


def _s704_stamp_words(js):
    """The made_through stamp (JSON) in words; None when it is not one."""
    try:
        d = json.loads(js)
    except (TypeError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    sb = str(d.get("spine_built") or "")
    built = ("%s %s" % (_dmy(sb[:10]), sb[11:16])).strip() if sb else ""
    return "sales to %s \\u00b7 Marg's closing of %s \\u00b7 spine built %s" % (_dmy(d.get("sales_through")) or "?", _dmy(d.get("end_day")) or "?", built or "?")


_S704_RELIST = re.compile(r"^made again at (\\d{1,2}:\\d{2}): (\\d+) rows, inputs (\\{.*\\})\\s*$")
_S704_STALE = re.compile(r"^the list was touched before newer inputs landed: (\\{.*\\})\\s*$")


def _s704_words(slot, text):
    """A relist / stale text in words; the text as it was when it is not the shape S644 writes."""
    s = str(text or "")
    m = _S704_RELIST.match(s) if slot == "relist" else _S704_STALE.match(s) if slot == "stale" else None
    if not m:
        return text
    w = _s704_stamp_words(m.group(m.lastindex))
    if not w:
        return text
    if slot == "relist":
        n = int(m.group(2))
        return ("Made again at %s on newer figures, %d supplier list%s: %s" % (m.group(1), n, "" if n == 1 else "s", w) if n else
                "Checked again at %s on newer figures; no supplier list to make again: %s" % (m.group(1), w))
    return "Not made again -- the list was already being worked on when newer figures landed: %s" % w


def _s644_owner(con, today=None):                               # noqa: F811
    out = _s644_owner_before_s704(con, today)
    try:
        t = (today or _today()).isoformat()
        r = con.execute("SELECT day, text FROM order_notice WHERE slot='inputs_note' AND day<=? ORDER BY day DESC LIMIT 1", (t,)).fetchone()
        if r:
            note = json.loads(r[1])
            if isinstance(note, dict):
                note["list_day"] = r[0]
                out["inputs"] = note
    except (sqlite3.Error, TypeError, ValueError):
        pass
    for slot in ("relist", "stale"):
        e = out.get(slot)
        if isinstance(e, dict) and e.get("text"):
            e["text"] = _s704_words(slot, e["text"])
    return out
# ---- S704 end ---------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":'''

EDITS = {
    "finance/spine/spine_build.py": [
        ('BUILD_VERSION = "S605.1"\n', 'BUILD_VERSION = "S704.1"\n'),
        (SB_DOC_OLD, SB_DOC_NEW),
        (SB_FN_ANCHOR, SB_FN_NEW + SB_FN_ANCHOR),
        (SB_CLASS_OLD, SB_CLASS_NEW),
        (SB_GATE_OLD, SB_GATE_NEW),
    ],
    "finance/order_rules.py": [
        (OR_TAIL, OR_SECTION),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    root, out = argv[1], argv[2]
    for rel, edits in EDITS.items():
        src = os.path.join(root, rel)
        b = open(src, "rb").read()
        if md5(b) != FROM[rel]:
            print("REFUSED: %s is %s, not %s" % (rel, md5(b)[:8], FROM[rel][:8]))
            return 1
        s = b.decode("utf-8")
        for i, (old, new) in enumerate(edits, 1):
            n = s.count(old)
            if n != 1:
                print("REFUSED: %s edit %d -- its anchor occurs %d times" % (rel, i, n))
                return 1
            s = s.replace(old, new, 1)
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(s.encode("utf-8"))
        print("built %s  %s -> %s  (%d edits)" % (rel, FROM[rel][:8], md5(s.encode("utf-8"))[:8], len(edits)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
