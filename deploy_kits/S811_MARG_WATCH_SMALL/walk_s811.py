#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s811.py FILES_DIR FIN_DIR [--control] -- kit S811's walk on MADE-UP rows (no live data, no number).
FILES_DIR holds marg_billwatch.py and owner_console.py (the built ones, or the live ones for the control); FIN_DIR the rest of /root/finance.
Last line: 'WALK S811 GREEN', or with --control on the live files 'CONTROL S811 RED as it must be'."""
import datetime as dt, importlib.util, os, sqlite3, sys, types

FILES, FIN = sys.argv[1], sys.argv[2]
CONTROL = "--control" in sys.argv
sys.path.insert(0, FIN)
res = []


def ck(n, c):
    res.append(bool(c)); print(("  ok   " if c else "  RED  ") + n)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


MB = load(os.path.join(FILES, "marg_billwatch.py"), "marg_billwatch_s811")
T = lambda s: dict(type="ITEMWISE", taken=dt.datetime.strptime(s, "%Y%m%d-%H%M%S"))   # noqa: E731
# 3 -- a day with two lists of one kind shows their times; a day with one, or one of each kind, does not
sd = getattr(MB, "same_day", None)
if sd:
    sd([T("20261111-110503"), T("20261111-110517"), T("20261112-094725"), dict(type="BILLITEMWISE", taken=dt.datetime(2026, 11, 12, 9, 48))], [])
ck("3 two lists taken the same day read with their times (11-Nov 11:05)", MB.stamp_day("20261111-110503").endswith("11:05") and "11-Nov" in MB.stamp_day("20261111-110503"))
ck("3 a day with one list of a kind reads as the day alone (12-Nov)", MB.stamp_day("20261112-094725") == MB.dmon("2026-11-12"))
# 4 -- the month grid names a sale bill in "Added late"
MB.table_html = lambda fs: ""
f = lambda kind, side: dict(month="2026-09", kind=kind, side=side)   # noqa: E731
g = MB.months_html([f("late", "purchase"), f("late", "purchase"), f("late", "sale"), f("gone", "purchase")])
ck("4 'Added late' 3 names its 1 sale bill, in the month and in the total", g.count("1 sale bill") == 2 and ">3<br>" in g)
ck("4 a month with no sale bill added late names none", "sale bill" not in MB.months_html([f("late", "purchase")]))
# 5 -- a list that held none of its period's bills says so
d0, d1 = dt.date(2026, 11, 1), dt.date(2026, 11, 11)
B = dict(record=[], parts=[dict(stamp="20261111-110503", f=d0, t=d1, n=0, of=25), dict(stamp="20261111-110503", f=d0, t=d1, n=0, of=25, fwd=True),
                           dict(stamp="20261005-075955", f=dt.date(2026, 9, 1), t=dt.date(2026, 10, 3), n=1, of=12)])
r = MB.record_html(B)
ck("5 a part list that held none: 'held none of the 25 bills of its period'", "held none of the 25 bills of its period — a part print" in r)
ck("5 a filtered first print that held none: 'held none of the 25 ... that a later list shows'", "held none of the 25 bills of its period that a later list shows" in r)
ck("5 one that held some keeps its count ('held 1 of 12 bills')", "held 1 of 12 bills" in r and "held 0 of" not in r and "only 0 of" not in r)
# 1 -- the scan full width above the lines on an agreeing row
class _P(object):
    class Assets(object):
        def __init__(self, ids):
            self.lines = {ids[0]: [dict(name="A", qty=1, amount=10)]}
    marg_lines = staticmethod(lambda con, b: [dict(name="A", qty=1, amount=10)])
    pair_lines = staticmethod(lambda s, m: list(zip(s, m)))
    _norm = staticmethod(lambda x: x)
    _p = staticmethod(lambda x: int(x * 100))
MB.SR = lambda: types.SimpleNamespace(esc=lambda s: str(s), rs2=lambda p: str(p))
h = MB._agree_panel(None, _P, dict(bill={}, sid=7, stamp="", paper_p=0, marg_p=0))
ck("1 an agreeing / settled row: the scanned paper first, full width (pv pvfull), the lines below", 'class="pv pvfull"' in h and h.index("pvfull") < h.index('class="pw"'))
ck("1 its style gives the paper the whole width", "#s781 .pv.pvfull{flex:1 1 100%}" in (MB._panel_css() if False else open(os.path.join(FILES, "marg_billwatch.py"), encoding="utf-8").read()))
# 2 -- entries, not bills
src = open(os.path.join(FILES, "marg_billwatch.py"), encoding="utf-8").read()
ck("2 'For the record -- N entries' (one entry / N entries)", "no action needed (%d entr%s%s)" in src and '"y" if len(B["record"]) == 1 else "ies"' in src)
# the console line (the parent's owner_console.py): the Marg watch with its own count and its link
stub = types.ModuleType("marg_billwatch")
state = {"fs": []}
stub.build = lambda con, paper=True: dict(findings=state["fs"])
sys.modules["marg_billwatch"] = stub
OC = load(os.path.join(FILES, "owner_console.py"), "owner_console_s811")
con = sqlite3.connect(":memory:")
cx = dict(today=dt.date(2026, 11, 13), now=dt.datetime(2026, 11, 13, 8, 0), clinic_day=dt.date(2026, 11, 13))
state["fs"] = [dict(status="open", before=1), dict(status="open", before=0), dict(status="settled", before=1), dict(status="closed", before=0)]
ln = [l for l in OC._sanj_pages(con, cx)[0] if "Marg watch" in (l.get("text") or "")]
ck("console: one Marg watch line -- 2 changed bills to look at · 1 new, amber, linked to the page",
   len(ln) == 1 and ln[0]["text"] == "Marg watch · 2 changed bills to look at · 1 new" and ln[0].get("href") == "/finance/sanjeevni/marg-watch"
   and ln[0].get("dot") == "w" and ln[0].get("fig") == "2")
state["fs"] = [dict(status="settled", before=1)]
ln = [l for l in OC._sanj_pages(con, cx)[0] if "Marg watch" in (l.get("text") or "")]
ck("console: nothing open -> one green line 'no changed bill to look at'", len(ln) == 1 and ln[0].get("dot") == "g" and "no changed bill" in ln[0]["text"])
def _boom(con, paper=True):
    raise RuntimeError("x")
stub.build = _boom
ln = [l for l in OC._sanj_pages(con, cx)[0] if "Marg watch" in (l.get("text") or "")]
ck("console: the page's reader failing -> one grey line, the section stands", len(ln) == 1 and ln[0].get("dot") == "n" and "could not be read" in ln[0]["text"])
n_red = res.count(False)
print("%d checks, %d red" % (len(res), n_red))
if CONTROL:
    print("CONTROL S811 RED as it must be" if n_red >= 8 else "CONTROL S811 NOT RED -- the walk proves nothing")
else:
    print("WALK S811 GREEN" if n_red == 0 else "WALK S811 RED")
