"""make_s848.py <scan_register.py FROM> <out> -- kit S848_SUMMARY_PARTS: a dealer's summary papers of one month add up when they list
different bills; a revision or a repeat (any bill or credit on two papers) -- the newest speaks, as before. Exact anchors, each once."""
import hashlib, sys
FROM = "f0bb05cd41a67769be3778545c1d2d5b"
src = open(sys.argv[1], "rb").read()
assert hashlib.md5(src).hexdigest() == FROM, "scan_register.py is not at S848's FROM pin"
t = src.decode("utf-8")
A1 = ('        if k not in by_dealer or int(sid) > int(by_dealer[k]["id"]):\n'
      '            by_dealer[k] = s                                  # the newest summary of a dealer for the month speaks\n'
      '    answers = s750_answers(con, month)\n')
B1 = ('        by_dealer.setdefault(k, []).append(s)                 # S848: every summary paper of the dealer for the month\n'
      '    by_dealer = {k: _s848_one(v) for k, v in by_dealer.items()}   # S848: parts add up; a revision or a repeat -- the newest speaks\n'
      '    answers = s750_answers(con, month)\n')
A2 = ('    src = "%s/api/s738/scan/%d" % (prefix, sid)\n'
      '    return (\'<div class="s738vb">')
B2 = ('    when += _s848_parts_html(s, prefix)                      # S848: a summary in parts names every paper\n'
      '    src = "%s/api/s738/scan/%d" % (prefix, sid)\n'
      '    return (\'<div class="s738vb">')
for a, b in ((A1, B1), (A2, B2)):
    assert t.count(a) == 1, "anchor not found exactly once: %r" % a[:60]
    t = t.replace(a, b, 1)
BLOCK = r'''


# ---- S848_SUMMARY_PARTS (17-Nov-2026, Sanjeevni session 473): a dealer's summary sent in PARTS ------------------------------------------------
#  L.K. Drug House sent October in two papers (B-0296 ₹3,656 mid-month, B-0332 ₹9,178 at the month's end); only the newest spoke, so the
#  dealer read '₹3,656 short' and the month's lock held. Now, for one dealer and one month: when every paper is read, each lists bills, and no
#  bill or credit appears on two papers, the papers are PARTS -- they add up (lines, figure, totals) and the newest paper's id speaks for the
#  scan. Any overlap means a revised or repeated summary: the newest speaks, exactly as before. One paper: unchanged (the same dict).
KIT_S848 = "S848_SUMMARY_PARTS"


def _s848_same(x, y):
    """Two lines of two papers are the same item: the same kind, and the number names the same bill -- or, with a number missing, the same
    amount (to the rupee) on the same date."""
    if x.get("kind") != y.get("kind"):
        return False
    if x.get("no") and y.get("no"):
        return _s750_tail_match(x["no"], y["no"])
    if x.get("amount_p") is None or y.get("amount_p") is None:
        return False
    return abs(int(x["amount_p"]) - int(y["amount_p"])) <= S750_TOL_P and str(x.get("date") or "") == str(y.get("date") or "")


def _s848_parts(papers):
    """True when the papers are parts of one month's summary (see the block's head)."""
    if len(papers) < 2:
        return False
    for p in papers:
        if not p.get("read") or not any(ln.get("kind") == "bill" for ln in (p.get("lines") or [])) or p.get("figure_p") is None:
            return False
    for i, a in enumerate(papers):
        for b in papers[i + 1:]:
            for x in (a.get("lines") or []):
                if x.get("kind") not in ("bill", "credit"):
                    continue
                if any(_s848_same(x, y) for y in (b.get("lines") or [])):
                    return False
    return True


def _s848_one(papers):
    """The summary that speaks for one dealer's month: the newest paper, or -- when the papers are parts -- all of them added up."""
    papers = sorted(papers, key=lambda p: int(p["id"]))
    newest = papers[-1]
    if not _s848_parts(papers):
        return newest
    m = dict(newest)
    m["lines"] = sorted([dict(ln) for p in papers for ln in (p.get("lines") or [])], key=lambda ln: (str(ln.get("date") or ""), str(ln.get("no") or "")))
    for k in ("figure_p", "bills_p", "credits_p"):
        m[k] = sum(int(p.get(k) or 0) for p in papers)
    tb = [p.get("total_bills_p") for p in papers]
    m["total_bills_p"] = sum(int(x) for x in tb) if all(x is not None for x in tb) else None
    m["opening_p"] = papers[0].get("opening_p")
    m["closing_p"] = newest.get("closing_p")
    m["dealer_by_bills"] = any(p.get("dealer_by_bills") for p in papers)
    m["parts"] = [dict(id=int(p["id"]), stamp_no=p.get("stamp_no") or "", figure_p=p.get("figure_p"), day=p.get("day")) for p in papers]
    m["stamp_no"] = " + ".join(str(p.get("stamp_no") or ("#%d" % int(p["id"]))) for p in papers)
    return m


def _s848_parts_html(s, prefix):
    """'From 2 papers: B-0296 · ₹3,656 (open) + B-0332 · ₹9,178 (open)' -- or '' for a summary of one paper."""
    parts = (s or {}).get("parts") or []
    if len(parts) < 2:
        return ""
    bits = ['%s · %s (<a href="%s" target="_blank" rel="noopener">open</a>)' % (esc(p["stamp_no"] or "#%d" % p["id"]), esc(rs(p["figure_p"])),
                                                                                 esc("%s/api/s738/scan/%d" % (prefix, p["id"]))) for p in parts]
    return '<div class="s738w">The dealer sent this month in %d papers: %s — added together.</div>' % (len(parts), " + ".join(bits))
# ---- S848 end -------------------------------------------------------------------------------------------------------------------------------
'''
t = t.rstrip("\n") + BLOCK
open(sys.argv[2], "wb").write(t.encode("utf-8"))
print("made", hashlib.md5(t.encode("utf-8")).hexdigest())
