#!/usr/bin/env python3
"""apply_s378.py -- kit S378_BANK_BALANCES. Anchored edits on sanjeevni_approvals.py f52ff847 (S377 bytes)
and finance_ui/finance_approvals.html 87157a85 (S377 bytes).

THE OWNER, 23-Sep-2026, after S377 went live: "better if it could also show the updated balances of both the
accounts boldly and clearly in the banks section."

WHAT THIS DOES. Bank opens with TWO BOLD FIGURES, one per account, and each says in small grey type how it
was made and what it cannot see.

    ICICI Sanjeevni        the bank's own closing balance (S377's anchor) + every settlement credited
                           since - every transfer recorded out since
    Yes Bank Sanjeevni     the balance its own statement closes on + every movement recorded that the
                           statement does not show (a cash deposit, a transfer in, a transfer out)

Yes Bank needs no seeding: the statement he loads carries its own closing balance and its own date, so the
figure moves forward by itself every time he loads a newer one. A movement the statement already shows is
NOT added again -- it is inside the bank's figure. Anything the bank has taken since the statement -- a
supplier payment, the POS rental, its GST -- is not in the figure, and each tile says so.

  python3 apply_s378.py --dir /root/finance [--out DIR]
"""
import argparse, hashlib, os
ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--out")
a = ap.parse_args()
OUT = a.out or a.dir

p = os.path.join(a.dir, "sanjeevni_approvals.py"); s = open(p, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "f52ff84779df0c5a6abdb718ab19323a", "sanjeevni_approvals.py is not f52ff847"
def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)

rep('''VERSION = "1.2"''', '''VERSION = "1.3"''')
rep('''#  v1.2 (S377, F-615, 23-Sep-2026)''',
'''#  v1.3 (S378, 23-Sep-2026): Bank opens with both accounts' balances, bold. Yes Bank is the balance its own
#  statement closes on plus every recorded movement that statement does not show; ICICI is S377's count. Each
#  says how it was made, and that a payment or a charge the bank has taken since is not in it.
#
#  v1.2 (S377, F-615, 23-Sep-2026)''')

rep('''def bank_view(con, ym):
    upi = []''',
'''def yesbank_position(con, unit=None):
    """What Yes Bank holds: the balance ITS OWN statement closes on, plus every movement we have recorded
    that the statement does not show. A movement the statement shows is already inside the bank's figure and
    is never added twice. Nothing the bank has done since the statement -- a supplier payment, the POS rental
    and its GST -- can be known here; the next statement settles it."""
    unit = unit or _unit
    base_p, as_on = 0, None
    if _has(con, "bank_statement_period"):
        r = con.execute("SELECT period_to, closing_p FROM bank_statement_period ORDER BY period_to DESC "
                        "LIMIT 1").fetchone()
        if r:
            as_on, base_p = r[0], int(r[1] or 0)
    added, taken = 0, 0
    if _has(con, "cash_pool_deposit"):
        for d, amt in con.execute("SELECT deposit_date, amount_p FROM cash_pool_deposit WHERE unit=?", (unit,)):
            if not _seen_in_yesbank(con, d, int(amt), True):
                added += int(amt)
    for t in transfers(con, unit):
        if t["to"] == "yesbank" and not _seen_in_yesbank(con, t["date"], t["amount_p"], True):
            added += t["amount_p"]
        elif t["frm"] == "yesbank" and not _seen_in_yesbank(con, t["date"], t["amount_p"], False):
            taken += t["amount_p"]
    return dict(base_p=base_p, as_on=as_on, added_p=added, taken_p=taken,
                holds_p=base_p + added - taken, anchored=bool(as_on))


def bank_view(con, ym):
    upi = []''')

rep('''    ip = icici_position(con)
    return dict(ok=True, month=ym, upi=upi, upi_total=rs(upi_total), upi_days=len(upi),''',
'''    ip = icici_position(con)
    yp = yesbank_position(con)
    return dict(ok=True, month=ym, upi=upi, upi_total=rs(upi_total), upi_days=len(upi),
                yesbank=dict(holds=rs(max(yp["holds_p"], 0)), base=rs(yp["base_p"]),
                             as_on=(dmy(yp["as_on"]) if yp["as_on"] else None),
                             added=rs(yp["added_p"]), taken=rs(yp["taken_p"]), anchored=yp["anchored"]),''')
open(os.path.join(OUT, "sanjeevni_approvals.py"), "w", encoding="utf-8").write(s)
print("sanjeevni_approvals.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())

# ------------------------------------------------------------------ the page
p2 = os.path.join(a.dir, "finance_ui", "finance_approvals.html"); h = open(p2, encoding="utf-8").read()
assert hashlib.md5(h.encode("utf-8")).hexdigest() == "87157a85833c84b917a6df7c49db2324", "finance_approvals.html is not 87157a85"
def reph(old, new):
    global h
    assert h.count(old) == 1, old[:70]
    h = h.replace(old, new)

# the two tiles, above everything else in Bank
reph('''    var h='';
    var ic=j.icici||{};''',
'''    var h='';
    var ic=j.icici||{}, yb=j.yesbank||{};
    h+='<div class="bal">'+
       '<div class="balbox"><div class="ttl">ICICI Sanjeevni</div><div class="fig">₹'+esc(ic.holds||"0")+'</div>'+
       '<div class="how">'+(ic.anchored
          ? ('₹'+esc(ic.base||"0")+' on the bank\\'s statement of '+esc(ic.since||"")+' · ₹'+esc(ic.credited||"0")+' collected since'+(ic.upto?(' (to '+esc(ic.upto)+')'):'')+' · ₹'+esc(ic.out||"0")+' moved out')
          : ('₹'+esc(ic.credited||"0")+' collected since '+esc(ic.since||"")+' · ₹'+esc(ic.out||"0")+' moved out — no statement anchored yet'))+
       (ic.short?(' · <b>our count is ₹'+esc(ic.short)+' short</b>'):'')+'</div></div>'+
       '<div class="balbox"><div class="ttl">Yes Bank Sanjeevni</div><div class="fig">₹'+esc(yb.holds||"0")+'</div>'+
       '<div class="how">'+(yb.anchored
          ? ('₹'+esc(yb.base||"0")+' as the statement of '+esc(yb.as_on||"")+' closes'+((yb.added&&yb.added!=="0")?(' · ₹'+esc(yb.added)+' in since, recorded here'):'')+((yb.taken&&yb.taken!=="0")?(' · ₹'+esc(yb.taken)+' out since'):''))
          : 'no statement loaded yet')+'</div></div>'+
       '</div><div class="mut" style="font-size:12px;margin:2px 0 8px">A payment or a charge the bank has taken since its statement — a supplier NEFT, the POS rental, its GST — is not in these figures. The next statement settles them.</div>';''')

# the ICICI fold no longer repeats the tile: the figure is above, the fold explains it
reph('''    h+='<details class="mon" open><summary>ICICI Sanjeevni <span class="mut" style="font-weight:400">· holds about ₹'+esc(ic.holds||"0")+
       (ic.anchored?(' — ₹'+esc(ic.base||"0")+' on the bank\\'s own statement of '+esc(ic.since||"")):(' — ₹'+esc(ic.credited||"0")+' collected since '+esc(ic.since||"")))+
       (ic.anchored?(', ₹'+esc(ic.credited||"0")+' collected since'+(ic.upto?(' (to '+esc(ic.upto)+')'):'')):(ic.upto?(' (to '+esc(ic.upto)+')'):''))+
       ', ₹'+esc(ic.out||"0")+' moved out</span></summary>'+''',
'''    h+='<details class="mon"><summary>ICICI Sanjeevni <span class="mut" style="font-weight:400">· where that figure comes from</span></summary>'+''')

reph('''@media (max-width:640px){.tree .hide-sm{display:none}''',
'''.bal{display:flex;gap:10px;flex-wrap:wrap;margin:4px 0 2px}
.balbox{flex:1 1 260px;border:1px solid #e6e9ee;border-radius:10px;padding:10px 12px;background:#fbfcfd}
.balbox .ttl{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--text-3);font-weight:600}
.balbox .fig{font-size:26px;font-weight:700;line-height:1.25;font-variant-numeric:tabular-nums}
.balbox .how{font-size:12px;color:var(--text-3)}
@media (max-width:640px){.balbox .fig{font-size:22px}.tree .hide-sm{display:none}''')

reph('''<!-- S377_ICICI_COUNT (Session 281, 23-Sep-2026, F-615)''',
'''<!-- S378_BANK_BALANCES (Session 281, 23-Sep-2026): Bank opens with both accounts' balances in bold, each
     saying how it was made and what it cannot see until the next statement.
  -- kit S377 header below --
<!-- S377_ICICI_COUNT (Session 281, 23-Sep-2026, F-615)''')

open(os.path.join(OUT, "finance_ui", "finance_approvals.html"), "w", encoding="utf-8").write(h)
print("finance_approvals.html ->", hashlib.md5(h.encode("utf-8")).hexdigest())
