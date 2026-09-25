p = "w/marg_watch.py"
s = open(p, encoding="ascii").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
rep('''    reader mended without going to the medical PC.
''', '''    reader mended without going to the medical PC.

S397 (25-Sep-2026, F-620): the reader (marg_txt S397) also takes the WHOLE STORES CLOSING STOCK text export.
    At every start the watcher offers the reader again every text it refused in the last three days, so a
    report kept before the reader learned it is taken as soon as the reader has (nothing refused is lost).
''')
rep('''    if "BILL WISE SALES STATEMENT" not in head:
        first''', '''    if "CLOSING STOCK" in head and "BILL WISE SALES STATEMENT" not in head:          # S397
        if "WHOLE STORES CLOSING STOCK" not in head:
            return "a closing stock of one store or category, not WHOLE STORES"
        if "*** End of Report ***" not in tail:
            return "a closing stock without the '*** End of Report ***' line at the end (cut short?)"
        return "a closing stock the reader cannot take"
    if "BILL WISE SALES STATEMENT" not in head:
        first''')
rep('''def capture_text(path, spool, captured, out):''', '''def retry_refused(spool, captured, out, now=None):
    """S397: every text refused in the last CENSUS_DAYS, offered to the reader again (once, at start)."""
    now = now or time.time()
    src = os.path.join(os.path.dirname(os.path.abspath(spool)), "_captured_txt", "refused")
    took = 0
    if not os.path.isdir(src):
        return 0
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        try:
            if (not name.lower().endswith(".txt") or name.lower().endswith(".why.txt")
                    or now - os.path.getmtime(p) > CENSUS_DAYS * 86400):
                continue
        except OSError:
            continue
        if capture_text(p, spool, captured, out):
            took += 1
            out("  + a text refused earlier is taken now: %s" % name)
    return took


def capture_text(path, spool, captured, out):''')
rep('''    new = 0 if watch_off() else sweep()  # always start from a known state
''', '''    new = 0 if watch_off() else sweep()  # always start from a known state
    if not watch_off():
        new += retry_refused(spool, captured, out)      # S397
''')
rep('''        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold"''', '''        # S397: a closing-stock text refused by an older reader is taken at the next start
        TXT_SEEN.clear(); TXT_STAT.clear()
        STK = marg_txt.STOCK_SAMPLE
        old = os.path.join(refd, "20260925-073658__report__%s.txt" % hashlib.md5(STK).hexdigest())
        open(old, "wb").write(STK)
        n0 = len([f for f in os.listdir(sp2) if f.endswith(".XLS")])
        took = retry_refused(sp2, cap2, lambda m: None)
        xs2 = [f for f in os.listdir(sp2) if f.endswith(".XLS")]
        ck("S397: a closing stock kept as refused is taken at the next start, as marg_txt's own .XLS",
           took == 1 and len(xs2) == n0 + 1
           and any(md5_of(os.path.join(sp2, f)) == hashlib.md5(marg_txt.convert(STK)[0]).hexdigest() for f in xs2))
        TXT_SEEN.clear(); TXT_STAT.clear()
        ck("...and only once (a second start adds nothing)", retry_refused(sp2, cap2, lambda m: None) == 0)
        ck("S397: a store-filtered stock is refused with its reason",
           "not WHOLE STORES" in _why_not(STK.replace(b"WHOLE STORES", b"MAIN STORE")))
        TXT_LIVE_FORCE = False
        ck("without MARG_TXT_LIVE.txt the reader is on hold"''')
rep('out("marg_watch S396.1 starting', 'out("marg_watch S397 starting')
open(p, "w", encoding="ascii", newline="\n").write(s)
print("applied")
