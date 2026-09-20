#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""apply_hub_s359.py -- S359_CASH_LOG_2: the hub's 'Billed to Home Medicine' card reads the day books.

The owner, 20-Sep 22:5x: "look at 14 Sept, the home med and proc are not showing" -- the
Sanjeevni hub's card (S194 api_home_medicine) counts sale_item.home_med, which has had zero
rows ever (a label bill never reaches sale_item; it is parked in the review queue), so the
card has always said "No home-medicine bills".  Since S356 every such bill is a
day_noncash_bill row; the card now reads those, home and procedure apart.

TWO ANCHORED EDITS ON THE PARENT'S FILES -- DECLARED:
  /root/finance/finance_app.py  (FROM 29819879dec3f057b7690e004e4e87cb, S349): the query inside
      api_home_medicine, nothing else.  The response keeps every key it had (since, count, total,
      total_p, days[{date, n, amount, amount_p}]) and adds home / proc per day and in total.
  /root/finance/finance_ui/finance_approvals.html (FROM aa79b181a914d4be1b8e8ddcebaaafc4, S243):
      the card's heading and table gain the two heads.

    python3 apply_hub_s359.py --dir /root/finance                # apply in place (backups .bak_S359_<from8>)
    python3 apply_hub_s359.py --dir DIR --out OUTDIR             # write patched copies (the walk)
Exits 1 on any pin or anchor mismatch, touching nothing.  The anchor must occur exactly once.
"""
import argparse
import hashlib
import os
import shutil
import sys

PY_FROM = "29819879dec3f057b7690e004e4e87cb"
HTML_FROM = "aa79b181a914d4be1b8e8ddcebaaafc4"

PY_EDITS = [
    ("""    rows = con.execute(
        "SELECT e.business_date bd, COUNT(*) n, "
        "       SUM(COALESCE(si.amount_p, 0)) amt "
        "FROM sale_item si JOIN day_entry e ON e.id = si.day_entry_id "
        "WHERE si.unit=? AND si.home_med=1 AND e.business_date>=? "
        "GROUP BY e.business_date ORDER BY e.business_date DESC LIMIT 90",
        (UNIT, since)).fetchall()
    days = [dict(date=r["bd"], n=r["n"],
                 amount=rupees(int(r["amt"] or 0)), amount_p=int(r["amt"] or 0))
            for r in rows]
    tot = sum(d["amount_p"] for d in days)
    cnt = sum(d["n"] for d in days)
    return jsonify(ok=True, since=since, count=cnt,
                   total=rupees(tot), total_p=tot, days=days)
""",
     """    # S359 (Sanjeevni, 20-Sep-2026): the day books, not the ingest's tag. A label bill
    # ('HOME MEDICINE', 'PROSIJER ...') never reaches sale_item -- it is parked in the
    # review queue -- so home_med=1 had zero rows ever and this card said "none" while
    # the days carried them. Since S356 every such bill is a day_noncash_bill row.
    rows = con.execute(
        "SELECT e.business_date bd, COUNT(*) n, SUM(b.amount_p) amt, "
        "       SUM(CASE WHEN b.head='home_medicine' THEN b.amount_p ELSE 0 END) home, "
        "       SUM(CASE WHEN b.head='procedure_medicine' THEN b.amount_p ELSE 0 END) proc "
        "FROM day_noncash_bill b JOIN day_entry e ON e.id = b.day_entry_id "
        "WHERE b.unit=? AND b.head IN ('home_medicine','procedure_medicine') AND e.business_date>=? "
        "GROUP BY e.business_date ORDER BY e.business_date DESC LIMIT 90",
        (UNIT, since)).fetchall()
    days = [dict(date=r["bd"], n=r["n"],
                 amount=rupees(int(r["amt"] or 0)), amount_p=int(r["amt"] or 0),
                 home=rupees(int(r["home"] or 0)), home_p=int(r["home"] or 0),
                 proc=rupees(int(r["proc"] or 0)), proc_p=int(r["proc"] or 0))
            for r in rows]
    tot = sum(d["amount_p"] for d in days)
    cnt = sum(d["n"] for d in days)
    home_tot = sum(d["home_p"] for d in days)
    proc_tot = sum(d["proc_p"] for d in days)
    return jsonify(ok=True, since=since, count=cnt,
                   total=rupees(tot), total_p=tot, days=days,
                   home_total=rupees(home_tot), home_total_p=home_tot,
                   proc_total=rupees(proc_tot), proc_total_p=proc_tot)
"""),
]

HTML_EDITS = [
    ("""<div class="card" id="homeMedCard"><h2><span class="kick">Billed to Home Medicine</span>Home-medicine sales</h2>""",
     """<div class="card" id="homeMedCard"><h2><span class="kick">Billed without cash</span>Home &amp; procedure medicine</h2>"""),
    ("""    var h='<div class="held"><div class="stat"><span class="lbl">Home-medicine · last 30 days</span><span class="val">'+fmt(j.total)+'</span></div>'+
          '<div class="stat"><span class="lbl">Bills</span><span class="val">'+j.count+'</span></div></div>';
    if((j.days||[]).length){
      h+='<div class="tblwrap" style="margin-top:8px"><table><thead><tr><th>Day</th><th class="num">Bills</th><th class="num">Amount</th></tr></thead><tbody>';
      j.days.forEach(function(d){h+='<tr><td>'+esc(d.date)+'</td><td class="num">'+d.n+'</td><td class="num">'+fmt(d.amount)+'</td></tr>'});
      h+='</tbody></table></div>';
    }else{h+='<div class="note">No home-medicine bills in the last 30 days.</div>'}""",
     """    var h='<div class="held"><div class="stat"><span class="lbl">Home medicine · last 30 days</span><span class="val">'+fmt(j.home_total||"0.00")+'</span></div>'+
          '<div class="stat"><span class="lbl">Procedure medicine · last 30 days</span><span class="val">'+fmt(j.proc_total||"0.00")+'</span></div>'+
          '<div class="stat"><span class="lbl">Bills</span><span class="val">'+j.count+'</span></div></div>';
    if((j.days||[]).length){
      h+='<div class="tblwrap" style="margin-top:8px"><table><thead><tr><th>Day</th><th class="num">Bills</th><th class="num">Home</th><th class="num">Procedure</th><th class="num">Total</th></tr></thead><tbody>';
      j.days.forEach(function(d){h+='<tr><td>'+esc(d.date)+'</td><td class="num">'+d.n+'</td><td class="num">'+fmt(d.home||"0.00")+'</td><td class="num">'+fmt(d.proc||"0.00")+'</td><td class="num">'+fmt(d.amount)+'</td></tr>'});
      h+='</tbody></table></div><div class="note">From the day books (S356): every home / procedure bill Darpan labels in Marg, taken off the day\\'s cash. Not the ingest\\'s old tag.</div>';
    }else{h+='<div class="note">No home / procedure medicine bills in the last 30 days.</div>'}"""),
]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def patch(text, edits, name):
    for old, new in edits:
        if text.count(old) != 1:
            raise SystemExit("!! %s: anchor found %d times, expected 1 -- nothing written" % (name, text.count(old)))
        text = text.replace(old, new, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="/root/finance")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    py = os.path.join(a.dir, "finance_app.py")
    html = os.path.join(a.dir, "finance_ui", "finance_approvals.html")
    todo = []
    for p, want, edits in ((py, PY_FROM, PY_EDITS), (html, HTML_FROM, HTML_EDITS)):
        if not os.path.exists(p):
            raise SystemExit("!! missing %s" % p)
        got = md5(p)
        if got != want:
            if a.out is None and os.path.exists(p + ".bak_S359_" + want[:8]):
                print("-- %s already patched (backup present); left alone" % os.path.basename(p))
                continue
            raise SystemExit("!! %s is %s, not the pin %s -- nothing written" % (os.path.basename(p), got, want))
        todo.append((p, want, edits))
    # every anchor checked before anything is written
    texts = [(p, want, patch(open(p, encoding="utf-8").read(), edits, os.path.basename(p))) for p, want, edits in todo]
    for p, want, new in texts:
        dest = os.path.join(a.out, os.path.basename(p)) if a.out else p
        if a.out:
            os.makedirs(a.out, exist_ok=True)
        else:
            shutil.copy2(p, p + ".bak_S359_" + want[:8])
        with open(dest, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        print("%s  %s -> %s" % (os.path.basename(p), want[:8], md5(dest)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
