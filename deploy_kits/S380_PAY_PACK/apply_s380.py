#!/usr/bin/env python3
"""apply_s380.py -- kit S380_PAY_PACK (F-616, D605). Anchored on purchase_app.py 8788962a (rev 13, S371).

THE OWNER, 23-Sep-2026, having finalised August and printed it:
  "Only the vendor payment sheet came out, remaining five pages were blank. The check letter did not get
   printed and in the payment details sheet in the lower part, my signature line, name, etc. part is also
   missing."

WHAT WAS WRONG, read in the code and in his own PDF (6 pages, page 1 complete, pages 2-6 empty):
  1  ADVICE_CSS_S265's print block hides the whole pay page with `body *{visibility:hidden}` and shows
     only #advice_s265. visibility:hidden paints nothing but KEEPS THE LAYOUT -- so every hidden card
     still took its space and the page still filled six sheets. Five of them were blank by construction.
  2  The covering letter -- the one carrying the cheque number -- prints only from its own page
     /page/pay/<month>/letter. Ctrl+P on the payment sheet could never produce it.
  3  Neither the annexure nor the payment sheet has ever carried a signature block. The annexure was
     built at S265 to match the bank's own workbook, which has none.
  4  purchase_pay_letter is EMPTY: no date and no cheque number have ever been typed, and api_pay_letter
     refuses every write once the month is FINAL -- so after finalising August he could not type them.

WHAT THIS DOES (D605):
  * ONE pack, one button: /page/pay/<month>/pack -- paper 1 the covering letter (portrait), paper 2 the
    annexure exactly as the bank gets it (landscape), paper 3 the payment sheet (portrait). Each on its
    own sheet, in that order, nothing blank between them. ?print=1 opens the print dialog by itself.
  * The annexure and the payment sheet end with  For SANJEEVNI MEDICOS / (rule) / Authorized Signatory /
    <name>, the name typed once into purchase_pay_config.signatory_name.
  * The pay page's own Ctrl+P prints the annexure ALONE, with no blank page behind it: the print rule now
    collapses the other cards with display:none instead of hiding them with visibility.
  * The letter's date, cheque number and the signatory name stay typable after the month is FINAL. They
    are the letter's own words, not a figure of the month; every write is audited exactly as now. No
    figure on the sheet becomes writable.
  * ONE renderer for the annexure: _advice_paper_s380 builds the paper, and the card on the pay page
    shows that same paper. The pack cannot drift from the page.

  python3 apply_s380.py --dir /root/finance [--out DIR]
"""
import argparse, hashlib, os

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--out")
a = ap.parse_args()
OUT = a.out or a.dir

p = os.path.join(a.dir, "purchase_app.py")
s = open(p, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "8788962a463a9d1fe65a17e193395645", \
    "purchase_app.py is not 8788962a (rev 13, S371)"


def rep(old, new):
    global s
    assert s.count(old) == 1, "anchor not unique or absent: " + old[:80]
    s = s.replace(old, new)


def cut(start_marker, end_marker, new, must_contain=()):
    """Replace the slice from start_marker up to (not including) end_marker."""
    global s
    assert s.count(start_marker) == 1, "start not unique: " + start_marker[:60]
    assert s.count(end_marker) == 1, "end not unique: " + end_marker[:60]
    i = s.index(start_marker)
    j = s.index(end_marker)
    assert j > i, "markers out of order"
    old = s[i:j]
    for m in must_contain:
        assert m in old, "the slice being replaced does not contain: " + m[:60]
    s = s[:i] + new + s[j:]


# ---------------------------------------------------------------- 1 the header
rep('purchase_app.py -- S224: Marg\'s purchases, on the box.  (rev 13, S371 / Session 281, 22-Sep-2026)',
    'purchase_app.py -- S224: Marg\'s purchases, on the box.  (rev 14, S380 / Session 281, 23-Sep-2026)')

rep('''REV 13 (S371, 22-Sep, F-614 -- the owner: "add 6 rupees in kedar and 39 in lk, and it will be final"):''',
    '''REV 14 (S380, 23-Sep, F-616 / D605 -- the owner, having finalised August and printed it: "Only the
vendor payment sheet came out, remaining five pages were blank. The check letter did not get printed and
in the payment details sheet in the lower part, my signature line, name, etc. part is also missing").
The month's papers are now ONE PACK, printed from one button at /page/pay/<month>/pack: the covering
letter (portrait), the annexure the bank gets (landscape), the payment sheet (portrait), each on its own
sheet and nothing blank between them. The annexure and the sheet carry For SANJEEVNI MEDICOS / Authorized
Signatory / <name>. The pay page's own print emits the annexure alone, collapsed with display:none so it
can no longer leave five empty sheets behind it. The letter's date, cheque number and the signatory name
stay typable after FINAL -- they are the letter's words, never a figure of the month.

REV 13 (S371, 22-Sep, F-614 -- the owner: "add 6 rupees in kedar and 39 in lk, and it will be final"):''')

# ---------------------------------------------------- 2 the advice paper + card
NEW_CARD = '''def _signoff_s380(con, role="Authorized Signatory"):
    """S380: the block the owner signs. The firm's name, the rule he signs on, what he signs as, and his
    own name -- typed once into purchase_pay_config.signatory_name and never again. With no name typed
    the rule and the words still print, so the paper is signable the day it is installed."""
    name = _pay_config_s265(con, "signatory_name", "")
    return ('<div class="sgnoff"><div class="s1">For %s</div><div class="sline"></div>'
            '<div class="s2">%s</div>%s</div>'
            % (_esc(ADVICE_FIRM_S265), _esc(role),
               ('<div class="s3">%s</div>' % _esc(name)) if name else ""))


def _advice_paper_s380(con, month, signoff=True):
    """THE ANNEXURE ITSELF -- the one renderer. The card on the payment sheet shows this, the pack prints
    this, and the two therefore cannot drift apart. Same letterhead, same seven columns, same order, same
    total as every file sent since April 2026; S380 adds the sign-off under the total."""
    rows, total, missing, paise = _advice_rows_s265(con, month)
    mob = _pay_config_s265(con, "shop_mobile", "")
    head_right = ("(M) %s" % _esc(mob)) if mob else (
        '<span class="muted">mobile not set on this server</span>')
    trs = []
    for r in rows:
        trs.append('<tr><td class="c">%d</td><td class="c">NEFT</td><td class="mono">%s</td>'
                   '<td>%s</td><td class="mono">%s</td><td class="n">%s</td>'
                   '<td>Vendor Payment</td></tr>'
                   % (r["sr"], _esc(r["acct"]), _esc(r["name"]), _esc(r["ifsc"]),
                      _rupees_s266(r["rupees"])))
    if not trs:
        trs.append('<tr><td colspan="7" class="muted">No vendor is payable by NEFT '
                   'this month.</td></tr>')
    return ('<div id="advice_s265"><div class="lh"><div class="lh1">%s</div>'
            '<div class="lh2">%s</div><div class="firm">%s</div><div class="lh2">%s</div></div>'
            '<div class="scroll"><table class="adv"><tr><th class="c">Sr. No.</th>'
            '<th class="c">Txn. type</th><th>Credit Account Number</th>'
            '<th>Credit Account Name</th><th>IFSC</th><th class="n">Amount</th>'
            '<th>Narration</th></tr>%s'
            '<tr class="tot"><td colspan="5" class="n">Total</td><td class="n">%s</td><td></td>'
            '</tr></table></div>%s</div>'
            % ("GSTIN: %s&nbsp;&nbsp;&nbsp;&nbsp;%s" % (_esc(ADVICE_HEAD_S265[0][1]), head_right),
               _esc(ADVICE_DL_S265), _esc(ADVICE_FIRM_S265), _esc(ADVICE_ADDR_S265),
               "".join(trs), _rupees_s266(total),
               _signoff_s380(con) if signoff else ""))


def _advice_card_s265(con, month, prefix, final):
    rows, total, missing, paise = _advice_rows_s265(con, month)
    warn = ""
    if missing:
        warn += ('<div class="warn">Left out of the advice \\u2014 no confirmed account: %s. '
                 'They are on the cheque list above.</div>'
                 % _esc(", ".join(sorted(missing))))
    if paise:
        warn += ('<div class="warn">One or more payables carry paise; the advice is '
                 'rounded to the rupee, as the bank file has always been.</div>')
    if not final:
        warn += ('<div class="warn">DRAFT \\u2014 this month is not locked yet. Lock it before '
                 'this is printed or emailed.</div>')
    return (ADVICE_CSS_S265 +
            '<div class="card" id="advcard_s380"><h2>4 &middot; The advice, exactly as the bank gets it</h2>'
            '<div class="muted">The same sheet you print on blank A4 and email to the bank '
            '&mdash; same lines, same columns, same order. '
            '<a class="p noprint" href="%s/page/pay/%s/pack?print=1" target="_blank">Print the bank pack</a> '
            '<button class="sm noprint" onclick="window.print()">print this sheet alone</button> '
            '<a class="p noprint" href="%s/page/pay/%s/advice.xlsx">Download the file for the email</a></div>%s%s</div>'
            % (prefix, month, prefix, month, warn, _advice_paper_s380(con, month)))


'''
cut("def _advice_card_s265(con, month, prefix, final):", 'ADVICE_CSS_S265 = """<style>', NEW_CARD,
    must_contain=("The same sheet you print on blank A4", '<div id="advice_s265">'))

# ---------------------------------------------------------------- 3 the two CSS
NEW_CSS = '''ADVICE_TABLE_CSS_S380 = """<style>
#advice_s265 .lh{padding:2px 0 10px}
#advice_s265 .lh1{font-size:12px}
#advice_s265 .lh2{font-size:12px}
#advice_s265 .firm{font-size:19px;font-weight:700;letter-spacing:.3px;padding:2px 0}
table.adv{width:100%;border-collapse:collapse;font-size:12.5px}
table.adv th,table.adv td{border:1px solid #9a9a9a;padding:4px 6px;text-align:left;
  vertical-align:top;white-space:nowrap}
table.adv th{background:#eee;font-weight:700;text-transform:none;font-size:12px}
table.adv td.c,table.adv th.c{text-align:center}
table.adv td.n,table.adv th.n{text-align:right}
table.adv td.mono{font-variant-numeric:tabular-nums}
table.adv tr.tot td{font-weight:700}
.sgnoff{padding-top:34px}
.sgnoff .s1{font-weight:600}
.sgnoff .sline{border-bottom:1px solid #333;width:240px;height:40px}
.sgnoff .s2{font-size:12.5px;padding-top:4px}
.sgnoff .s3{font-weight:600;padding-top:2px}
@media print{
  table.adv th,table.adv td{padding:2px 6px}
  .sgnoff{padding-top:12px;break-inside:avoid;page-break-inside:avoid}
  .sgnoff .sline{height:30px}
}
</style>"""

# S380 (F-616). The pay page's own print. The old rule hid the page with
# `body *{visibility:hidden}` -- which paints nothing but KEEPS every hidden card's layout, so the page
# still filled six sheets and five came out blank. display:none collapses them instead, and only the
# advice card is put back. Nothing else on that page prints; the whole pack prints from /pack.
ADVICE_CSS_S265 = ADVICE_TABLE_CSS_S380 + """<style>
@media print{
  @page{size:A4 landscape;margin:12mm}
  .wrap > *{display:none!important}
  .wrap > #advcard_s380{display:block!important;border:none;padding:0;margin:0}
  #advcard_s380 > h2,#advcard_s380 > .muted,#advcard_s380 > .warn{display:none!important}
  table.adv th{background:#eee!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
</style>"""
'''
cut('ADVICE_CSS_S265 = """<style>', "\n\n\n# =====================================================================\n# S266 -- THE COVERING LETTER.",
    NEW_CSS, must_contain=("body *{visibility:hidden!important}", "table.adv{width:100%"))

# --------------------------------------------- 4 the letter card: the name box
rep('''            '<div class="letterset noprint"><label>Date <input class="pin" id="lt_date" '
            'value="%s"></label><label>Cheque number <input class="pin" id="lt_cheque" '
            'value="%s" placeholder="e.g. 115257"></label>'
            '<button class="sm" onclick="saveletter()">save</button>''',
    '''            '<div class="letterset noprint"><label>Date <input class="pin" id="lt_date" '
            'value="%s"></label><label>Cheque number <input class="pin" id="lt_cheque" '
            'value="%s" placeholder="e.g. 115257"></label>'
            '<label>Signature name <input class="pin" id="lt_sign" style="width:200px;text-align:left" '
            'value="%s" placeholder="the name under your signature"></label>'
            '<button class="sm" onclick="saveletter()">save</button>''')

rep('''            'body:JSON.stringify({month:"%s",date_text:document.getElementById("lt_date").value,'
            'cheque_no:document.getElementById("lt_cheque").value})})''',
    '''            'body:JSON.stringify({month:"%s",date_text:document.getElementById("lt_date").value,'
            'cheque_no:document.getElementById("lt_cheque").value,'
            'signatory:document.getElementById("lt_sign").value})})''')

rep('''            % (prefix, month, warn, _esc(date_text), _esc(cheque),
               _rupees_s266(total), _letter_html_s266(con, month, total), month))''',
    '''            % (prefix, month, warn, _esc(date_text), _esc(cheque),
               _esc(_pay_config_s265(con, "signatory_name", "")),
               _rupees_s266(total), _letter_html_s266(con, month, total), month))''')

# the card's own wording: the pack is where it prints from
rep('''            '<div class="muted">Word for word as it has always gone, with the date, the '
            'cheque number and the amount filled in from this sheet. '
            '<a class="p" href="%s/page/pay/%s/letter" target="_blank">Open it to print</a>'
            '</div>%s'
''',
    '''            '<div class="muted">Word for word as it has always gone, with the date, the '
            'cheque number and the amount filled in from this sheet. It prints with the annexure and '
            'this payment sheet as one pack. '
            '<a class="p" href="%s/page/pay/%s/pack?print=1" target="_blank">Print the bank pack</a> '
            '<a href="%s/page/pay/%s/letter" target="_blank">or this letter alone</a>'
            '</div>%s'
''')

rep('''    return (LETTER_CSS_S266 +
            '<div class="card"><h2>5 &middot; The covering letter</h2>''',
    '''    return (LETTER_CSS_S266 +
            '<div class="card" id="lettercard_s380"><h2>5 &middot; The covering letter</h2>''')

rep('''            % (prefix, month, warn, _esc(date_text), _esc(cheque),''',
    '''            % (prefix, month, prefix, month, warn, _esc(date_text), _esc(cheque),''')

# --------------------------------- 5 the letter's words stay typable after FINAL
rep('''    con = _db()
    _ensure(con)
    _letter_ensure_s266(con)
    if _month_status(con, month)["status"] == "final":
        return _refuse("This month is FINAL. The doctor must reopen it first.")
    date_text = str(b.get("date_text") or "").strip()[:60]
    cheque = str(b.get("cheque_no") or "").strip()[:40]''',
    '''    con = _db()
    _ensure(con)
    _letter_ensure_s266(con)
    # S380 (D605): the date, the cheque number and the signature name are the LETTER'S OWN WORDS, not a
    # figure of the month. He types them when the payment is actually made -- which is after the month is
    # locked -- so FINAL no longer refuses them. Every write is audited below exactly as before, and no
    # figure on the sheet becomes writable: api/pay-line and every other door keep their own FINAL gate.
    date_text = str(b.get("date_text") or "").strip()[:60]
    cheque = str(b.get("cheque_no") or "").strip()[:40]
    if "signatory" in b:
        sign = str(b.get("signatory") or "").strip()[:80]
        con.execute("""CREATE TABLE IF NOT EXISTS purchase_pay_config (
            key TEXT PRIMARY KEY, value TEXT, at TEXT)""")
        was = _pay_config_s265(con, "signatory_name", "")
        con.execute("INSERT INTO purchase_pay_config (key, value, at) VALUES ('signatory_name',?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value, at=excluded.at",
                    (sign or None, now_iso()))
        if sign != was:
            _audit(con, _who(u), "pay_signatory", month, {"name": sign, "before": was})''')

# ------------------------------------------------- 6 the pack bar on the pay page
rep('''            '</div>%s%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),''',
    '''            '</div>%s%s%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               _pack_bar_s380(prefix, month),''')

# ------------------------------------------------------------ 7 the pack itself
PACK = '''

# =====================================================================
# S380 -- THE PACK (F-616, D605).
#
# The month's payment does not go to the bank as one paper. It goes as three, and until today only one of
# them could be printed:
#
#   1  the covering letter        -- portrait, signed, carrying the cheque number
#   2  the annexure               -- landscape, the seven columns the bank reads
#   3  the payment sheet          -- portrait, vendor by vendor, what he checked before he signed
#
# They print here in that order, each on its own paper, and the print dialog opens by itself when the
# page is opened with ?print=1 -- one click from the payment sheet. The orientation is per paper, by
# named @page rules, so the annexure is landscape in the same job where the letters are portrait.
#
# NOTHING IS RE-CALCULATED HERE. The letter comes from _letter_html_s266, the annexure from
# _advice_paper_s380 and the sheet from _pay_sheet_table -- the same three renderers the payment sheet
# itself shows. A paper that printed differently from the screen would be worse than no paper at all.
# =====================================================================

PACK_CSS_S380 = """<style>
@page port{size:A4 portrait;margin:14mm}
@page land{size:A4 landscape;margin:10mm}
.paper{border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:0 0 18px;background:#fff}
.paper .ph{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);
  font-weight:600;padding-bottom:10px;border-bottom:1px dashed var(--line);margin-bottom:14px}
.paper .shhead{padding:0 0 12px}
.paper .shhead .firm{font-size:19px;font-weight:700;letter-spacing:.3px}
.paper .shhead .sub{font-size:12.5px;color:var(--muted)}
@media print{
  .wrap{max-width:none;padding:0;margin:0}
  .paper{border:0;border-radius:0;padding:0;margin:0;break-after:page;page-break-after:always}
  .paper:last-child{break-after:auto;page-break-after:auto}
  .paper.port{page:port}
  .paper.land{page:land}
  .paper .scroll{overflow:visible}
  table.adv th{background:#eee!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  table.sheet{width:100%;font-size:11px}
  table.sheet th,table.sheet td{padding:2px 5px}
  table.sheet td:first-child{white-space:nowrap}
  table.sheet .chip{padding:0 4px;font-size:9.5px}
}
</style>"""


def _pack_bar_s380(prefix, month):
    """The one button, at the top of the payment sheet where he starts."""
    return ('<div class="card noprint"><h2>Print the month\\u2019s papers</h2>'
            '<div class="muted">Three sheets in one go, in the order the bank gets them \\u2014 the '
            'covering letter, the annexure, and this payment sheet \\u2014 each on its own paper, '
            'nothing blank in between.</div>'
            '<div style="margin-top:10px"><a class="p" href="%s/page/pay/%s/pack?print=1" '
            'target="_blank">Print the bank pack</a> &nbsp;'
            '<a href="%s/page/pay/%s/pack" target="_blank">look at it first</a></div></div>'
            % (prefix, month, prefix, month))


@bp.route("/page/pay/<month>/pack")
def page_pay_pack_s380(month):
    """The three papers, one below the other, one per sheet of A4."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\\d{4}-\\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    prefix = request.script_root + _url_prefix
    s, groups = _pay_rows(con, month)
    rows, total, missing, paise = _advice_rows_s265(con, month)
    final = s["status"]["status"] == "final"
    date_text, cheque = _letter_values_s266(con, month)

    warn = ""
    if not final:
        warn += ('<div class="warn noprint">DRAFT \\u2014 %s is not locked yet. Lock it before these '
                 'papers go to the bank.</div>' % _esc(_month_name(month)))
    if not cheque:
        warn += ('<div class="warn noprint">No cheque number has been typed for this month, so the '
                 'letter prints a blank line for it. Type it on the payment sheet, under '
                 '<b>5 &middot; The covering letter</b> \\u2014 it can be typed after the month is '
                 'locked.</div>')
    if not _pay_config_s265(con, "signatory_name", ""):
        warn += ('<div class="warn noprint">No signature name is set, so the papers print the rule and '
                 '<b>Authorized Signatory</b> with no name under it. Type it once in the same place.</div>')
    if missing:
        warn += ('<div class="warn noprint">Not on the annexure \\u2014 no confirmed account: %s. '
                 'They are paid by cheque.</div>' % _esc(", ".join(sorted(missing))))

    bar = ('<div class="noprint" style="padding-bottom:12px">'
           '<button class="p" onclick="window.print()">Print all three</button> &nbsp;'
           '<a href="%s/page/pay/%s">back to the payment sheet</a>'
           '<div class="muted" style="margin-top:6px">A4. Paper 1 the covering letter, portrait &middot; '
           'paper 2 the annexure, landscape &middot; paper 3 the payment sheet, portrait. Leave the '
           'browser\\u2019s scale at 100%% and its headers and footers off.</div></div>'
           % (prefix, month))

    body = (bar + warn + PACK_CSS_S380 + LETTER_CSS_S266 + ADVICE_TABLE_CSS_S380 +
            '<div class="paper port"><div class="ph noprint">Paper 1 &mdash; the covering letter</div>'
            '%s</div>'
            '<div class="paper land"><div class="ph noprint">Paper 2 &mdash; the annexure, exactly as '
            'the bank gets it</div>%s</div>'
            '<div class="paper port"><div class="ph noprint">Paper 3 &mdash; the payment sheet</div>'
            '<div class="shhead"><div class="firm">%s</div>'
            '<div class="sub">Vendor payments &mdash; %s &middot; the sheet this month was paid from'
            '</div></div>%s%s</div>'
            % (_letter_html_s266(con, month, total),
               _advice_paper_s380(con, month),
               _esc(ADVICE_FIRM_S265), _esc(_month_name(month)),
               _pay_sheet_table(groups, prefix, month, False),
               _signoff_s380(con, "Checked and authorised")))
    js = ("window.addEventListener('load',function(){setTimeout(function(){window.print();},400);});"
          if request.args.get("print") else "")
    return _page("Bank pack \\u2014 %s" % _month_name(month), body, js)
'''
s = s.rstrip("\n") + "\n" + PACK

# ------------------------------------------- 8 the email file is named by the month it is PAID in
# The owner's own "NEFT ADVICE AUGUST 2026.xlsx" (sent 23-Sep) carries JULY's purchases: 20 of its 21
# amounts are this server's July advice to the rupee. The bank's files are named by the month the money
# goes out, and August's purchases are paid in September (D604). S267 named the file by the purchase
# month, so August's advice would have gone to the bank under the very name it already holds for July's.
rep('''def _advice_filename_s267(month):
    """NEFT ADVICE AUGUST 2026.xlsx -- the name these files have always carried."""
    try:
        y, m = month.split("-")
        name = ("JANUARY",''',
    '''def _advice_filename_s267(month):
    """NEFT ADVICE SEPTEMBER 2026.xlsx for AUGUST's purchases -- S380: the bank's files carry the month
    the money is PAID in, which is the month after the purchases (D604), never the purchase month."""
    try:
        y, m = month.split("-")
        y, m = (int(y) + 1, 1) if int(m) == 12 else (int(y), int(m) + 1)
        y, m = str(y), str(m)
        name = ("JANUARY",''')

open(os.path.join(OUT, "purchase_app.py"), "w", encoding="utf-8").write(s)
print("purchase_app.py ->", hashlib.md5(s.encode("utf-8")).hexdigest())
