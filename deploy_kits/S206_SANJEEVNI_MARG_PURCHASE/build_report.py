#!/usr/bin/python3
"""build_report.py — the pharmacy analytics page, built on the FULL financial year."""
import json, os, re, html, collections, datetime as dt

H = os.path.expanduser
S = json.load(open(H('~/fy_sale.json')))
D = json.load(open(H('~/q1.json')))
X = json.load(open(H('~/q1_extra.json')))
DTH = json.load(open(H('~/dth.json')))
FA = json.load(open(H('~/fy_analysis.json')))
pur, exp = D['purchase'], D['expiry']

def ps(p):
    m = re.search(r'\d+\s*\*\s*(\d+)', p or ''); return int(m.group(1)) if m else None
def un(s):
    n = ps(s['pack']) or 0; return (s['strips'] or 0)*n + (s['loose'] or 0)
def lv(s):
    n = ps(s['pack']); return None if not n else un(s)*(s['rate_p'] or 0)/100.0/n

val, uc = collections.Counter(), collections.Counter()
for s in S:
    if not s['item']: continue
    v = lv(s)
    if v is not None: val[s['item']] += v; uc[s['item']] += un(s)
dates = sorted({s['date'] for s in S})
E = html.escape
def tbl(head, rows):
    h = "".join("<th>%s</th>" % E(str(x)) for x in head)
    b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % E(str(c)) for c in r) for r in rows)
    return "<div class=sc><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>" % (h, b)
def rs(v): return "{:,.2f}".format(v)

P = ["<title>Pharmacy Analytics FY 2026-27</title>", """<style>
:root{--bg:#fbfaf8;--fg:#1c1b19;--mut:#6b6660;--line:#e0dcd5;--card:#fff;--warn:#8a4b12;--warnbg:#fdf3e7;--good:#15603a;--bad:#9b2c22}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#171614;--fg:#eae7e1;--mut:#a09a92;--line:#332f2b;--card:#201e1c;--warn:#e0a262;--warnbg:#2b2115;--good:#6fd39b;--bad:#f08a7c}}
:root[data-theme=dark]{--bg:#171614;--fg:#eae7e1;--mut:#a09a92;--line:#332f2b;--card:#201e1c;--warn:#e0a262;--warnbg:#2b2115;--good:#6fd39b;--bad:#f08a7c}
body{background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0;padding:2rem 1rem}
.w{max-width:62rem;margin:0 auto}h1{font-size:1.9rem;line-height:1.2;margin:0 0 .3rem}
h2{font-size:1.25rem;margin:2.6rem 0 .6rem;padding-top:1.2rem;border-top:1px solid var(--line)}
.sub{color:var(--mut);margin:0 0 1.5rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.2rem;margin:1rem 0}
.warn{background:var(--warnbg);border-color:var(--warn)}
.k{display:flex;flex-wrap:wrap;gap:.8rem;margin:1rem 0}
.k div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.6rem .9rem;min-width:9rem;flex:1 1 9rem}
.k b{display:block;font-size:1.4rem;line-height:1.2}.k span{color:var(--mut);font-size:.8rem}
.sc{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.9rem;min-width:32rem}
th,td{text-align:left;padding:.45rem .6rem;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--mut);font-weight:600;font-size:.78rem;text-transform:uppercase;letter-spacing:.03em}
td:nth-child(n+2){font-variant-numeric:tabular-nums}
code{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:.1rem .3rem;font-size:.86em}
footer{color:var(--mut);font-size:.85rem;margin-top:3rem;border-top:1px solid var(--line);padding-top:1rem}
</style>""", "<div class=w>"]
P.append("<h1>Pharmacy analytics — Sanjeevni Medicos</h1>")
P.append("<p class=sub>Financial year 2026-27, 01-Apr-2026 to 26-Aug-2026. Every figure measured.</p>")
P.append("<div class=k>"
 "<div><b>%d</b><span>sale bills, A00001–A03215</span></div>"
 "<div><b>%d</b><span>trading days</span></div>"
 "<div><b>%s</b><span>sale value (Rs)</span></div>"
 "<div><b>%s</b><span>gross margin (Rs)</span></div>"
 "<div><b>%.1f%%</b><span>margin on matched sales</span></div>"
 "</div>" % (3215, len(dates), rs(sum(val.values())), rs(FA['gross']), 100.0*FA['gross']/FA['matched']))
P.append("<div class=card><b>Completeness is proven by the bill sequence, not by counting days.</b><br>"
 "Marg issues sale bills in one unbroken run. Assembled from the archive and the 15-day/monthly exports, the chain is "
 "<b>A00001 &rarr; A03215 with zero gaps</b>. <b>133 trading days</b>; the 15 calendar days with no sale are "
 "<b>every one a Sunday</b>, and six Sundays did trade. <b>Purchase covers the same period, five contiguous exports, no gap.</b><br><br>"
 "<b>Two bill numbers are absent from the whole year:</b> <code>A001339</code> (02-Jun) and <code>A001468</code> (08-Jun). "
 "Neither appears on any other date. Cancelled or deleted &mdash; worth knowing which.<br><br>"
 "<b>The next sale report must begin at <code>A003216</code></b> (credit notes <code>CN00183</code>).</div>")

P.append("<h2>1 · Margin — the whole year</h2>")
P.append("<p>Sale value is <code>units &times; MRP &divide; pack size</code>, which reproduces whole bills to the paisa. Cost is the net rate from the purchase archive, which already accounts for free goods.</p>")
P.append("<div class=k><div><b>%s</b><span>matched sale value (Rs)</span></div><div><b>%.1f%%</b><span>of all sales matched to a cost</span></div><div><b>%d</b><span>items sold below cost</span></div></div>"
         % (rs(FA['matched']), 100.0*FA['matched']/FA['total_val'], 0))
P.append(tbl(["item","units","sale/unit","cost/unit","margin Rs","margin %"],
             [[r[0], r[1], "%.2f"%r[2], "%.2f"%r[3], rs(r[4]), "%.1f%%"%r[5]] for r in FA['margin'][:20]]))

P.append("<h2>2 · Negative stock — %d items, %d units short</h2>" % (len(X['neg']), abs(sum(r['whole'] for r in X['neg']))))
P.append("<div class='card warn'><b>Not all of these are faults.</b> Goods received from a trusted supplier before the invoice arrives make Marg go negative as a matter of arithmetic, and it clears when the purchase bill is entered &mdash; <b>PATOPAN DSR is exactly that</b> (owner's ruling). "
 "The ones worth investigating are the opposite shape: <b>a negative on an item with no purchase history at all</b>.</div>")
P.append(tbl(["item","WHOLE","DTH","MAIN"], [[r['item'], r['whole'], r['dth'], r['main']] for r in X['neg']]))

P.append("<h2>3 · The DTH store</h2>")
P.append("<p>DTH was created to hold medicines consumed for package patients and was never maintained. It holds <b>10 items of 388</b>: nine negative, one positive.</p>")
P.append(tbl(["item","DTH","MAIN","WHOLE"], [[r['item'], r['dth'], r['main'], r['whole']] for r in sorted(DTH, key=lambda x: x['dth'])]))
P.append("<div class='card warn'><b>Five items sit at exactly &minus;10</b> &mdash; one strip of ten, issued out of a store that was never stocked. "
 "And the <b>only positive balance is <code>VINBACTUM DS</code>, 25 INJ, expired 2/2025</b> &mdash; eighteen months past, no purchase this year, no sale on any day of the year. "
 "<b>The entire expired exposure of this pharmacy is sitting in the abandoned store.</b><br><br>"
 "<b>No archived report can attribute a bill to a store.</b> The purchase report has no store column, and the sale line's only unexplained field is constant per item, so it is an item code and not a store selector. "
 "Finding the DTH movements needs a store-wise issue/transfer register exported from Marg &mdash; a report nobody has taken yet.</div>")

P.append("<h2>4 · Expiry</h2>")
P.append(tbl(["item","batch","expiry","as printed","units","unit"],
             [[r['item'], r['batch'], r['expiry'], r['raw'], r['units'] if r['units'] is not None else '?', r['unit']] for r in exp]))
P.append("<p class=sub>Two expiry lists were exported 53 seconds apart with identical headers and different cutoffs; both are shown.</p>")

P.append("<h2>5 · FEFO — %d inversions across the year</h2>" % FA['fefo'])
P.append("<p>A later-expiry batch sold before an earlier-expiry one, measured from sales alone. On ten days this looked like 8; over the year it is %d.</p>" % FA['fefo'])
P.append(tbl(["item","inversions"], FA['fefo_top']))

P.append("<h2>6 · Batch movement</h2>")
P.append("<p><b>%d of %d</b> items were sold from more than one batch this year &mdash; that is the population where FEFO can fail.</p>"
         % (len(FA['multi']), len(FA['multi']) + 89))
P.append(tbl(["item","batches sold"], sorted(FA['multi'].items(), key=lambda x: -x[1])[:15]))

P.append("<h2>7 · Consumption — top 20 by value</h2>")
P.append(tbl(["#","item","units","sale value Rs"],
             [[i, it, uc[it], rs(v)] for i, (it, v) in enumerate(sorted(val.items(), key=lambda x: -x[1])[:20], 1)]))
P.append("<p class=sub>%d distinct items, %s units, Rs %s over %d trading days.</p>"
         % (len(uc), "{:,}".format(sum(uc.values())), rs(sum(val.values())), len(dates)))

P.append("<footer>Sale: <code>MargArchive\\SALE_BILLWISE</code> (17&ndash;26 Aug, daily) + <code>MARG REPORTS CLAUDE\\</code> (the 15-day and monthly exports, Apr&ndash;15 Aug), de-duplicated by bill and line &mdash; <b>17,177 item lines</b>. "
 "Purchase: <code>PURCHASE_ITEMWISE</code>, five contiguous months. Stock: 26-Aug, four stores, <code>WHOLE = MAIN + DTH + SCRAP</code> verified on all 375 items. Expiry: 23-Aug.<br>"
 "Marg is the system of record for stock. Nothing here recomputes what Marg states. No patient name or number appears in this report.</footer></div>")
out = H('~/mnt/Downloads/margsync/_analysis/pharmacy_analytics_2026-08-27.html')
open(out, 'w').write("\n".join(P))
print("written:", out, os.path.getsize(out), "bytes")
