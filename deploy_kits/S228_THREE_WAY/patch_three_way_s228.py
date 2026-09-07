#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S228 THREE-WAY -- builds the kit's two changed files from the S228_LOSS_DESK pins.

  stock_app.py      c8e2a6b8 -> + _three_way() and the third figure on every row
  stock_report.html 9be950f2 -> the provenance line, the verdict card, and
                                "Marg X - ours Z -> counted Y" on each difference

Read-only change: nothing in the count, the decision desk or the loss desk moves.
Refuses if a source file is not the pinned one, and writes nothing until every
edit lands.
"""
import hashlib, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PINS = {"stock_app.py": "c8e2a6b8", "stock_report.html": "9be950f2"}


def rd(n):
    with io.open(os.path.join(HERE, n), "r", encoding="utf-8") as fh:
        return fh.read()


def wr(n, s):
    with io.open(os.path.join(HERE, n), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(s)


def md5(n):
    with io.open(os.path.join(HERE, n), "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def once(hay, needle, what):
    n = hay.count(needle)
    if n != 1:
        raise SystemExit("REFUSED: %s -- the anchor appears %d times, not once." % (what, n))


for f, pin in PINS.items():
    if not os.path.exists(os.path.join(HERE, f)):
        raise SystemExit("REFUSED: %s is not beside this script." % f)
    if md5(f)[:8] != pin:
        raise SystemExit("REFUSED: %s is %s, not the pinned %s -- NOTHING CHANGED."
                         % (f, md5(f)[:8], pin))

app = rd("stock_app.py")
rep = rd("stock_report.html")
block = rd("_block_threeway.py")

# ---------------------------------------------------------------- stock_app.py
# 1. the block, right after the S221 TWO PRICES helpers it leans on
A1 = "# ---- end S221 TWO PRICES helpers --------------------------------------------\n"
once(app, A1, "stock_app.py end of TWO PRICES helpers")
app = app.replace(A1, A1 + "\n\n" + block.rstrip("\n") + "\n")

# 2. compute it once per report, next to the packs it needs for the words
A2 = """    packs = {}
    for r in con.execute("SELECT item, pack_size, qty FROM stock_snapshot WHERE as_on=?", (R["as_on"],)):
        packs[r[0]] = (int(r[1] or 1), int(r[2] or 0))
"""
once(app, A2, "stock_app.py packs map")
app = app.replace(A2, A2 + """    # S228 THREE-WAY: the shelf, Marg and our own system, and WHICH of the two
    # pushes the count's own figures actually came from.
    _tw = _three_way(con, R["as_on"], {k: v[0] for k, v in packs.items()})
    _ours = _tw["ours"]
""")

# 3. the third figure on every difference row
A3 = """                 answer=ans.get(item), cause=cause.get(item), decision=dec.get(item), word=words.get(item),
                 life="/finance/stock/api/pad/item/%d/%s" % (_root, item))
"""
once(app, A3, "stock_app.py difference row")
app = app.replace(A3, """                 answer=ans.get(item), cause=cause.get(item), decision=dec.get(item), word=words.get(item),
                 ours=(_ours.get(item) if item in _ours else None),
                 ours_gap=((int(_ours[item]) - int(marg)) if item in _ours else None),
                 life="/finance/stock/api/pad/item/%d/%s" % (_root, item))
""")

# 4. the same third figure on the matched rows, and the block on the report
A4 = """                matched=[dict(item=m[0], packing=m[1] or "", pack=int(m[2] or 1), qty=m[3]) for m in R["matched"]],
"""
once(app, A4, "stock_app.py matched rows")
app = app.replace(A4, """                matched=[dict(item=m[0], packing=m[1] or "", pack=int(m[2] or 1), qty=m[3],
                             ours=(_ours.get(m[0]) if m[0] in _ours else None),
                             ours_gap=((int(_ours[m[0]]) - int(m[3])) if m[0] in _ours else None))
                         for m in R["matched"]],
                three_way=_tw,
""")

# ---------------------------------------------------------------- stock_report.html
# 5. the provenance line -- the honest answer to "was this Marg, or was it us?"
A5 = """    +'<b>Marg stock as on</b><span>'+esc(d.as_on||"-")+(d.as_on_note?' <span class="sub">('+esc(d.as_on_note)+')</span>':'')+'</span>'"""
once(rep, A5, "stock_report.html as-on line")
rep = rep.replace(A5, A5 + """
    +'<b>Measured against</b><span'+(((d.three_way||{}).snapshot_source==="marg")?'':' class="warn"')+'>'+esc((d.three_way||{}).measured_against||"-")+((d.three_way||{}).marg_at_text?' <span class="sub">(pushed '+esc(d.three_way.marg_at_text)+' IST)</span>':'')+'</span>'""")

# 6. the verdict card, above the KPI row
A6 = """  h+='<div class="kpis"><div class="kpi"><div class="v">'+d.counted+'<span class="sub"> / '+d.items_in_shop+'</span></div><div class="l">items counted</div></div>'"""
once(rep, A6, "stock_report.html kpi row")
rep = rep.replace(A6, """  const T=d.three_way||{};
  const TW='<div class="tw'+(T.trustworthy?' ok':((T.bang||(T.have_ours&&T.have_marg&&T.differ))?' bad':''))+'">'
    +(T.bang?'<div class="bang">\\u26A0 '+esc(T.bang)+'</div>':'')
    +'<b>Our system vs Marg\\u2019s export</b><div>'+(T.trustworthy?'\\u2713 ':'')+esc(T.line||"-")+'</div>'
    +'<div class="sub">This compares the two COMPUTER figures only \\u2014 our own and Marg\\u2019s. The shelf is compared further down, on the count itself.</div>'
    +((T.gaps||[]).length?'<table class="tbl" style="margin-top:6px"><tr><th>Item</th><th class="n">Marg</th><th class="n">Ours</th><th class="n">Gap</th></tr>'
        +T.gaps.map(g=>'<tr><td>'+esc(g.item)+'</td><td class="n">'+esc(units(g.marg,g.pack))+'</td><td class="n">'+esc(units(g.ours,g.pack))+'</td><td class="n"><b>'+(g.gap>0?'+':'-')+esc(g.gap_text)+'</b></td></tr>').join("")
        +'</table>'+((T.all_gaps||0)>T.gaps.length?'<div class="sub">and '+((T.all_gaps)-T.gaps.length)+' more</div>':''):'')
    +((T.only_ours_n||T.only_marg_n)?'<div class="sub">'+(T.only_ours_n?T.only_ours_n+' item'+(T.only_ours_n===1?'':'s')+' only our system has':'')+(T.only_ours_n&&T.only_marg_n?' \\u00b7 ':'')+(T.only_marg_n?T.only_marg_n+' only Marg has':'')+'</div>':'')
    +((T.gaps||[]).length?'<div class="sub">A gap here is usually an entry keyed after the export was taken, not stock. It is settled by the item ledger, never by counting again.</div>':'')
    +'</div>';
  if(T.bang) h+=TW;                      // an ALARM goes before the numbers
""" + A6)

# 6b. WHERE THE CARD SITS. Routine confirmation belongs AFTER the tiles: the owner
# should meet "3 differ - short Rs 6,840" before he meets one computer arguing with
# another. Only the alarm jumps that queue. (The S228 screen read: "he has to read a
# full phone screen of provenance before he reaches a number that answers what's
# wrong" -- and the card I had just added was part of that screenful.)
A6B = """    +'<div class="kpi"><div class="v">'+d.explained+'<span class="sub"> / '+d.differed+'</span></div><div class="l">explained so far</div></div></div>';
"""
once(rep, A6B, "stock_report.html end of the kpi row")
rep = rep.replace(A6B, A6B + "  if(!T.bang) h+=TW;                     // routine confirmation, after the numbers\n")

# 7. the third figure on the difference line itself
A7 = """    +'<div class="q">Marg '+esc(units(x.marg,x.pack))+' \\u2192 counted '+esc(units(x.counted,x.pack))+' \\u00b7 <span class="d '+(x.diff<0?"short":"over")+'">'+esc(units(x.diff,x.pack))+(x.diff>0?" over":"")+'</span></div>'"""
if rep.count(A7) != 1:
    A7 = A7.replace("\\u2192", "→").replace("\\u00b7", "·")
once(rep, A7, "stock_report.html difference line")
# EVERY QUANTITY STAYS WHOLE. At 390px this line wrapped as "counted 30" / "strips",
# and "counted 30" alone at the end of a line reads as thirty -- on the MAJOR lines,
# which are the ones acted on. The figures are the same; only the break moves.
A7NEW = (A7.replace("""'<div class="q">Marg '+esc(units(x.marg,x.pack))+'""",
                    """'<div class="q">Marg <span class="nb">'+esc(units(x.marg,x.pack))+'</span>""")
           .replace("""counted '+esc(units(x.counted,x.pack))+'""",
                    """counted <span class="nb">'+esc(units(x.counted,x.pack))+'</span>""")
           .replace("""<span class="d '+(x.diff<0?"short":"over")+'">""",
                    """<span class="d nb '+(x.diff<0?"short":"over")+'">"""))
if A7NEW == A7:
    raise SystemExit("REFUSED: the difference line did not take the nowrap spans.")
rep = rep.replace(A7, A7NEW + """
    +(x.ours==null?'':'<div class="q ours">'+(x.ours_gap?'our own system said <b class="nb">'+esc(units(x.ours,x.pack))+'</b><span class="d short"> \\u2014 <span class="nb">'+esc(units(Math.abs(x.ours_gap),x.pack))+'</span> '+(x.ours_gap>0?'more':'less')+' than Marg</span>':'our own system: <b>same</b>')+'</div>')""")

# 8. the style for the two new blocks
A8 = ".empty{color:var(--muted);font-style:italic}"
if rep.count(A8) != 1:
    A8 = [l for l in rep.split("\n") if l.startswith(".empty{")][0]
once(rep, A8, "stock_report.html .empty style")
rep = rep.replace(A8, A8 + """
.tw{border:1.5px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0;background:var(--surface)}
.tw.ok{border-color:var(--ok);background:var(--accent-soft)}.tw.bad{border-color:var(--diff)}
.tw.ok>div{font-weight:600}
.tw>b{display:block;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.tw .bang{background:var(--diff);color:#fff;font-weight:700;font-size:14px;line-height:1.35;margin:-10px -12px 8px;padding:9px 12px;border-radius:8px 8px 0 0}
.tw>div{font-size:14.5px;margin-top:2px}.tw .sub{font-size:12.5px;color:var(--muted);margin-top:4px}
.warn{color:var(--diff);font-weight:700}
.q .nb,.tw .nb{white-space:nowrap}
.q.ours{margin-top:1px}""")

wr("stock_app.py", app)
wr("stock_report.html", rep)
sys.stdout.write("PATCHED\n")
for f in ("stock_app.py", "stock_report.html"):
    sys.stdout.write("  %s  %s\n" % (md5(f)[:8], f))
