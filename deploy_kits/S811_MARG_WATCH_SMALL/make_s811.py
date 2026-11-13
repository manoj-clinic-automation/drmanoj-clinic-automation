#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s811.py ROOT OUT -- kit S811 (13-Nov-2026, Sanjeevni session 441): build the two changed files FROM THE LIVE BYTES.

  ROOT/finance/marg_billwatch.py  616490b4 -> the Marg watch page's five small things (S438's notes):
      1 a settled / agreeing row: the scanned paper full width, above the lines (it sat in a narrow side column)
      2 "For the record -- 24 entries" (it said "bills"; three bills appear twice)
      3 a day on which two lists were taken shows their times (11-Nov 11:05 and 11-Nov 11:05 read as one "11-Nov")
      4 the month grid's "Added late" names a sale bill counted in it
      5 a filtered first print that held none of its period's bills says so ("held none of the 25"), not "held only 0 of the 25"
  ROOT/finance/owner_console.py   ba977832 -> one line in the Sanjeevni section: the Marg watch, its own count, its link
      (THE PARENT'S FILE -- PLANNED on board/_numbers v1332; nothing else in it changes)

Every patch is an exact anchor that occurs once, or a whole function whose md5 is checked; anything else stops the build."""
import hashlib, os, sys

FROM = {"finance/marg_billwatch.py": "616490b4a0d30edacf5b3724856be4e0",
        "finance/owner_console.py":  "ba97783223b689ab538a7ccaf0028ef7"}

# ---- 1 the scan full width above the lines on an agreeing / settled row
A1 = '    return \'<div class="pnl"><div class="pw">%s%s</div><div class="pv">%s</div></div>\' % (head, table, viewer)\n'
B1 = ('    return \'<div class="pnl"><div class="pv pvfull">%s</div><div class="pw">%s%s</div></div>\' % (viewer, head, table)   '
      '# S811: the scan full width, above the lines\n')
A1c = '"#s781 .pv summary{list-style:none}#s781 .pv summary::-webkit-details-marker{display:none}")'
B1c = '"#s781 .pv summary{list-style:none}#s781 .pv summary::-webkit-details-marker{display:none}#s781 .pv.pvfull{flex:1 1 100%}")'
# ---- 2 entries, not bills
A2 = ('<summary>For the record — no action needed (%d bill%s%s)</summary>')
B2 = ('<summary>For the record — no action needed (%d entr%s%s)</summary>')
A2b = '% (len(B["record"]), "" if len(B["record"]) == 1 else "s", '
B2b = '% (len(B["record"]), "y" if len(B["record"]) == 1 else "ies", '
# ---- 3 the time on a day with two lists
STAMP_MD5 = "e868f8f102be2372f296228c676b862d"
STAMP_NEW = '''_SAME_DAY = set()                                             # S811: days on which two or more lists of one kind were taken


def same_day(*lists):
    """S811: note the days on which two or more lists of one kind were taken -- stamp_day then shows the time on them, so the
    part list of 11-Nov 11:05:03 and the full one of 11:05:17 no longer read as one "taken 11-Nov"."""
    n = {}
    for ex in lists:
        for e in ex:
            k = (e.get("type") or "", e["taken"].date().isoformat())       # two lists of the SAME kind on one day
            n[k] = n.get(k, 0) + 1
    days = {d for (_t, d), c in n.items() if c > 1}
    _SAME_DAY.clear()
    _SAME_DAY.update(days)


def stamp_day(stamp):
    t = _taken(stamp)
    if not t:
        return str(stamp or "")
    d = t.date().isoformat()
    return dmon(d) + (t.strftime(" %H:%M") if d in _SAME_DAY else "")'''
A3 = ('    pur, parts = compare(purchase_exports(con), "purchase", names)\n'
      '    sal, _p = compare(sale_exports(con), "sale", None, part_rule=False, record_kinds=RECORD_KINDS + ("amount",))\n')
B3 = ('    pe, se = purchase_exports(con), sale_exports(con)\n'
      '    same_day(pe, se)                                          # S811: a day that has two lists shows their times\n'
      '    pur, parts = compare(pe, "purchase", names)\n'
      '    sal, _p = compare(se, "sale", None, part_rule=False, record_kinds=RECORD_KINDS + ("amount",))\n')
# ---- 4 the month grid names a sale bill in "Added late"
MONTHS_MD5 = "9fa19d31ed5d2d4f7d533aa8cf448e49"
MONTHS_NEW = '''def months_html(fs):
    """The findings by the month of the bill: a grid that opens (the approved shape). S811: a sale bill counted in "Added late" is named."""
    by = {}
    for f in fs:
        by.setdefault(f["month"], []).append(f)
    h = ['<div class="scroll"><div class="pgrid phead"><span>Month of the bill</span><span class="n">Bills</span><span class="n">Removed</span>'
         '<span class="n">Added late</span><span class="n">Changed</span></div>']
    tot = [0, 0, 0, 0, 0]

    def cells(c):
        out = ['<span class="n">%s</span>' % (v or "—") for v in c[:4]]
        if c[4]:
            out[2] = '<span class="n">%d<br><small class="note">%d sale bill%s</small></span>' % (c[2], c[4], "" if c[4] == 1 else "s")
        return "".join(out)
    for i, m in enumerate(sorted(by, reverse=True)):
        g = by[m]
        c = [len(g), sum(1 for f in g if f["kind"] == "gone"), sum(1 for f in g if f["kind"] == "late"), sum(1 for f in g if f["kind"] in ("changed", "redated")),
             sum(1 for f in g if f["kind"] == "late" and f["side"] == "sale")]
        tot = [a + b for a, b in zip(tot, c)]
        h.append('<details class="pd"%s><summary class="pgrid"><span class="per">%s</span>%s</summary><div class="inner">%s</div></details>'
                 % (" open" if i == 0 else "", esc(month_name(m)), cells(c), table_html(g)))
    h.append('<div class="pgrid ptot"><span>Total</span>%s</div></div>' % cells(tot))
    return "".join(h)'''
# ---- 5 a filtered print that held none of its period's bills
A5 = ('            ("<li>The purchase list taken %s (%s to %s) held only %d of the %d bills it should have — a filtered print. No bill is called "\n'
      '             "\\u201cadded late\\u201d against it; it is still read for removed and changed bills.</li>" if p.get("fwd") else\n'
      '             "<li>The purchase list taken %s (%s to %s) held %d of %d bills — a part print; nothing is judged from it.</li>")\n'
      '            % (esc(stamp_day(p["stamp"])), esc(dmon(p["f"].isoformat())), esc(dmon(p["t"].isoformat())), p["n"], p["of"]) for p in B["parts"])))\n')
B5 = ('            (("<li>The purchase list taken %s (%s to %s) held none of the %d bills of its period that a later list shows — a filtered print. "\n'
      '              "No bill is called \\u201cadded late\\u201d against it; it is still read for removed and changed bills.</li>"\n'
      '              % (esc(stamp_day(p["stamp"])), esc(dmon(p["f"].isoformat())), esc(dmon(p["t"].isoformat())), p["of"]))\n'
      '             if (p.get("fwd") and not p["n"]) else\n'
      '             ("<li>The purchase list taken %s (%s to %s) held none of the %d bills of its period — a part print; nothing is judged from it.</li>"\n'
      '              % (esc(stamp_day(p["stamp"])), esc(dmon(p["f"].isoformat())), esc(dmon(p["t"].isoformat())), p["of"]))\n'
      '             if not p["n"] else\n'
      '             (("<li>The purchase list taken %s (%s to %s) held only %d of the %d bills it should have — a filtered print. No bill is called "\n'
      '               "\\u201cadded late\\u201d against it; it is still read for removed and changed bills.</li>" if p.get("fwd") else\n'
      '               "<li>The purchase list taken %s (%s to %s) held %d of %d bills — a part print; nothing is judged from it.</li>")\n'
      '              % (esc(stamp_day(p["stamp"])), esc(dmon(p["f"].isoformat())), esc(dmon(p["t"].isoformat())), p["n"], p["of"])))\n'
      '             for p in B["parts"])))   # S811\n')

# ---- the console line (the parent's owner_console.py)
C1A = '                  corr="/finance/darpan/corrections", reports="/finance/reports/aaj")\n'
C1B = ('                  corr="/finance/darpan/corrections", reports="/finance/reports/aaj",\n'
       '                  mwatch="/finance/sanjeevni/marg-watch")                       # S811 (the Sanjeevni chat): the Marg watch\n')
C2A = '    piece(lines, "The expiry watch", expiry)\n'
C2B = (C2A + '''
    def mwatch():                                                      # S811 (the Sanjeevni chat): the Marg watch's own count -- its page's reader
        import marg_billwatch as MB                                    # noqa: PLC0415
        B = MB.build(con, paper=True)
        op = [f for f in B["findings"] if f["status"] == "open"]
        new = sum(1 for f in op if not f["before"])
        if not op:
            return L("g", "Marg watch · no changed bill to look at", href=SANJ_PAGES["mwatch"], link="Marg watch", fig=0)
        return L("w", "Marg watch · %d changed bill%s to look at%s" % (len(op), "" if len(op) == 1 else "s", (" · %d new" % new) if new else ""),
                 href=SANJ_PAGES["mwatch"], link="Marg watch", fig=len(op))
    piece(lines, "The Marg watch", mwatch)
''')

PATCHES = {"finance/marg_billwatch.py": [("s", A1, B1), ("s", A1c, B1c), ("s", A2, B2), ("s", A2b, B2b),
                                         ("f", ("def stamp_day(stamp):", "\n\n\ndef month_name("), STAMP_MD5, STAMP_NEW),
                                         ("s", A3, B3),
                                         ("f", ("def months_html(fs):", "\n\n\ndef inputs_html("), MONTHS_MD5, MONTHS_NEW),
                                         ("s", A5, B5)],
           "finance/owner_console.py": [("s", C1A, C1B), ("s", C2A, C2B)]}


def main(root, out):
    built = {}
    for rel, steps in PATCHES.items():
        raw = open(os.path.join(root, rel), "rb").read()
        got = hashlib.md5(raw).hexdigest()
        if got != FROM[rel]:
            print("STOP: %s is %s, expected %s -- nothing built" % (rel, got[:8], FROM[rel][:8]))
            return 2
        txt = raw.decode("utf-8")
        for i, st in enumerate(steps, 1):
            if st[0] == "s":
                n = txt.count(st[1])
                if n != 1:
                    print("STOP: %s anchor %d occurs %d times -- nothing built" % (rel, i, n))
                    return 2
                txt = txt.replace(st[1], st[2], 1)
            else:
                (a, b), md5, new = st[1], st[2], st[3]
                if txt.count(a) != 1:
                    print("STOP: %s block %d: its start occurs %d times -- nothing built" % (rel, i, txt.count(a)))
                    return 2
                s = txt.index(a)
                e = txt.index(b, s)
                if hashlib.md5(txt[s:e].encode("utf-8")).hexdigest() != md5:
                    print("STOP: %s block %d is not the one this kit was built on -- nothing built" % (rel, i))
                    return 2
                txt = txt[:s] + new + txt[e:]
        built[rel] = txt.encode("utf-8")
    for rel, data in built.items():
        with open(os.path.join(out, os.path.basename(rel)), "wb") as fh:
            fh.write(data)
        print("%s  %s" % (hashlib.md5(data).hexdigest(), rel))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
