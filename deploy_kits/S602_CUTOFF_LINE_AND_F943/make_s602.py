#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s602.py -- kit S602_CUTOFF_LINE_AND_F943: the builder. Anchored edits on the LIVE bytes of four files; no new file placed, no new
setting, no new table, no data step.

    python3 -B make_s602.py --finance /root/finance --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes the four files into DIR (spine/spine_read.py under DIR/spine/) and prints each md5 -- the installer compares them with
PINS.sh. The brief: claude_code_briefs/S602_CUTOFF_LINE_AND_F943.md (v2, 19-Oct-2026, Sanjeevni session 332). D746: one grey line under
the heading of Darpan's order tab, the newest purchase-bill day Marg's purchases hold, read through the spine's one door. F-943: the
nightly witness's read-only run no longer meets the start-capture judge."""
import argparse
import hashlib
import os
import re
import sys

FROM = {
    "darpan_kal.py": "325d988c61e1c7408a2a4b687a4822bb",
    "darpan_kal.html": "75d5a5b51b017abd5ad3aa408609a1ff",
    "spine/spine_read.py": "827b00402add288d028c910128084b90",
    "stock_figure.py": "cb577821d9e1eb40110312b4331df9ef",
}

# =============================================================================================================== spine/spine_read.py (3.1)
SR = []
SR.append(("R1 the docstring's usage list: one line", '''    sp.status()                           # one line for a health page
''', '''    sp.purchases_upto()                   # the newest purchase-bill day Marg's purchases hold, never past today (D746)
    sp.status()                           # one line for a health page
'''))
SR.append(("R2 purchases_upto() after purchases_by_supplier", '''                      "FROM sp_purchase_bill b WHERE b.direction='PURCHASE' AND b.date>=? AND b.date<=? GROUP BY b.supkey, b.date ORDER BY b.supkey, b.date",
                      date_from, date_to)

    def family(self, name):
''', '''                      "FROM sp_purchase_bill b WHERE b.direction='PURCHASE' AND b.date>=? AND b.date<=? GROUP BY b.supkey, b.date ORDER BY b.supkey, b.date",
                      date_from, date_to)

    def purchases_upto(self):
        """The newest purchase-bill day Marg's purchases hold (sp_purchase_bill, direction PURCHASE), ISO, never past today -- None when
        the spine holds no purchase bill. S602 (D746): the cut-off line on Darpan's order tab. A mis-keyed future bill date (F-948's class)
        never reaches the tab."""
        today_iso = dt.date.today().isoformat()
        return self.q("SELECT MAX(date) AS d FROM sp_purchase_bill WHERE direction='PURCHASE' AND date<=?", today_iso)[0]["d"]

    def family(self, name):
'''))

# =============================================================================================================== darpan_kal.py (3.2)
DK = []
DK.append(("K1 the S485 block's header comment names S602 / D746", '''# कल का हिसाब. On any other order.source the list is shown read-only and no tap is taken.
''', '''# कल का हिसाब. On any other order.source the list is shown read-only and no tap is taken.
# S602 (19-Oct-2026, D746): the payload carries the purchase cut-off day -- the newest purchase-bill day Marg's purchases hold, read
# through the spine's one door (order_rules._s470_spine, a fresh handle closed after the read); the tab's heading says it in one grey line.
# None when the spine cannot be opened: the line is then left out, never a stand-in.
'''))
DK.append(("K2 _s485_payload: the cut-off day read and carried", '''    live = [l for b in order for l in b["lines"] if not l["held"]]
    return dict(ok=True, date=day, list_time=lt, opened=opened, source=src, frozen=frozen, me=who[0],
                editable=bool(src == "darpan" and who[0] in ("staff", "owner") and opened and not frozen),
                suppliers=order, n_suppliers=len(order), n_lines=len(live), order_day_names=[b["display"] for b in order if b["order_day"]],
                all_pakka=bool(order) and all(b["status"] != "open" for b in order), yesterday_date=yd, yesterday=ylist)
''', '''    live = [l for b in order for l in b["lines"] if not l["held"]]
    pu = None                                                  # S602 (D746): the purchase cut-off day, from the spine's one read door
    try:
        _sp = OR._s470_spine()
        try:
            pu = _sp.purchases_upto()
        finally:
            _sp.con.close()
    except Exception:                                          # noqa: BLE001 -- a spine that cannot be opened leaves the line out (never a stand-in)
        pu = None
    return dict(ok=True, date=day, list_time=lt, opened=opened, source=src, frozen=frozen, me=who[0],
                editable=bool(src == "darpan" and who[0] in ("staff", "owner") and opened and not frozen),
                suppliers=order, n_suppliers=len(order), n_lines=len(live), order_day_names=[b["display"] for b in order if b["order_day"]],
                all_pakka=bool(order) and all(b["status"] != "open" for b in order), yesterday_date=yd, yesterday=ylist, purchase_upto=pu)
'''))

# =============================================================================================================== darpan_kal.html (3.3)
HT = []
HT.append(("H1 renderOrder's heading: the one grey line (D746)", '''\'</div>':'')+'</div>';''',
           '''\'</div>':'')+(j.purchase_upto?'<div class="muted">Marg में खरीद '+esc(j.purchase_upto.slice(8,10)+'-'+j.purchase_upto.slice(5,7))+' के बिल तक चढ़ी है — उसके बाद आया माल इस सूची के स्टॉक में नहीं है</div>':'')+'</div>';'''))

# =============================================================================================================== stock_figure.py (3.4)
SF = []
SF.append(("F1 the kit line and the history", '''KIT = "S598_ARRIVALS_BY_LINE"                                  # v1.2 was S587_MORNING_FLOW, v1.1 S583_ARRIVALS_ONE_RULE, v1.0 S577_STOCK_ON_SPINE
''', '''KIT = "S602_CUTOFF_LINE_AND_F943"                               # v1.3 S598_ARRIVALS_BY_LINE, v1.2 S587_MORNING_FLOW, v1.1 S583_ARRIVALS_ONE_RULE, v1.0 S577_STOCK_ON_SPINE
#  S602 (19-Oct-2026, F-943): the witness's read-only run never judges. A read-only caller says so on its Ctx (read_only=True), read by
#  _may_write alone: the judge stays out, the capture stays as recorded, and verify_start's work is not done for nothing on a connection
#  that cannot take the write (seen at S594's rehearsal: 'attempt to write a readonly database', one stderr line a night).
'''))
SF.append(("F2 the v1.2 history: the witness's read-only run never judges", '''#  captures() when the context carries a writable connection outside a transaction, and by `python3 stock_figure.py verify-start`. A capture
''', '''#  captures() when the context carries a writable connection outside a transaction (the witness's read-only run never judges, F-943), and
#  by `python3 stock_figure.py verify-start`. A capture
'''))
SF.append(("F3 Ctx.read_only", '''    def __init__(self, con=None, sp=None):
        self.con, self.sp, self.c = con, sp, {}
''', '''    def __init__(self, con=None, sp=None, read_only=False):
        self.con, self.sp, self.c = con, sp, {}
        self.read_only = bool(read_only)                      # S602 (F-943): a read-only caller says so; _may_write alone reads it
'''))
SF.append(("F4 _may_write(con, ctx)", '''def _may_write(con):
    """A connection that may take the verdict's write: present and not inside the caller's own transaction (its pending writes are never
    committed by this module). A read-only connection raises on the write and the capture stays pending (fail-soft, one stderr line)."""
    try:
        return con is not None and not con.in_transaction
''', '''def _may_write(con, ctx=None):
    """A connection that may take the verdict's write: present and not inside the caller's own transaction (its pending writes are never
    committed by this module). A read-only caller says so on its Ctx (read_only=True) and the judge stays out -- the capture stays as
    recorded (F-943)."""
    if ctx is not None and getattr(ctx, "read_only", False):
        return False
    try:
        return con is not None and not con.in_transaction
'''))
SF.append(("F5 _start_apply's call", '''and c["as_on"] >= recent and _may_write(con):
''', '''and c["as_on"] >= recent and _may_write(con, ctx):
'''))
SF.append(("F6 witness(): a read-only Ctx", '''    ctx = Ctx(con, sp)
    now = when or dt.datetime.now()
''', '''    ctx = Ctx(con, sp, read_only=True)                        # S602 (F-943): read-only -- the judge stays out
    now = when or dt.datetime.now()
'''))

EDITS = {"spine/spine_read.py": SR, "darpan_kal.py": DK, "darpan_kal.html": HT, "stock_figure.py": SF}


def apply(src, edits, label, pin):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != pin:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, pin))
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
        out = apply(os.path.join(a.finance, label), edits, label, FROM[label])
        if out is None:
            return 2
        built[label] = out
    sr = built["spine/spine_read.py"].decode("utf-8")
    dk = built["darpan_kal.py"].decode("utf-8")
    ht = built["darpan_kal.html"].decode("utf-8")
    sf = built["stock_figure.py"].decode("utf-8")
    old_dk = open(os.path.join(a.finance, "darpan_kal.py"), "rb").read().decode("utf-8")
    assert sr.count("def purchases_upto(") == 1 and sr.count("purchases_upto") == 2, "purchases_upto: the def and its usage line only"
    assert dk.count("purchases_upto") == 1 and dk.count("purchase_upto") == 1, "darpan_kal.py: the one read and the one key"
    assert dk.count("purchase_bill") == old_dk.count("purchase_bill"), "no new read of purchase_bill (charter 1)"
    assert ht.count("purchase_upto") == 3 and ht.count("j.purchase_upto?") == 1, "darpan_kal.html: the one fragment (the key read three times inside it)"
    assert sf.count("_may_write(") == 2 and sf.count("_may_write(con, ctx)") == 1 and "_may_write(con):" not in sf, "_may_write: the def and its one caller"
    assert sf.count("Ctx(con, sp, read_only=True)") == 1 and 'KIT = "S602_CUTOFF_LINE_AND_F943"' in sf, "the read-only witness and the kit line"
    for label, out in built.items():
        assert not re.search(rb"\d{10}", out), "a run of ten digits in %s" % label
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM[label]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
