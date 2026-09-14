

# =====================================================================
# S266 -- THE COVERING LETTER.
#
# The advice does not go to the bank on its own: it goes with a signed letter
# authorising the debit. This is that letter, word for word as the one Sanjeevni
# has always sent, with three things filled in instead of typed:
#
#   the date        -- today in IST, or whatever he sets
#   the cheque no.  -- the one thing only he knows; typed here, kept per month
#   the amount      -- taken from the advice, never retyped
#
# TWO TYPOS IN THE ORIGINAL ARE FIXED, and said out loud here so nobody thinks
# the letter drifted: the September file read "SEPTEMBAR", and the subject line
# ended "transactions.S" with a stray capital.
#
# NO ACCOUNT NUMBER IS IN THIS FILE (F-185). The firm's own debit account is
# handed in on the install line and kept in purchase_pay_config, exactly as the
# shop's mobile is. Absent, the letter prints a blank to fill by hand and says so.
# =====================================================================

LETTER_BANK_S266 = ("The Manager", "YES Bank Limited", "Rampur Garden,", "Bareilly.")
LETTER_SUB_S266 = "Sub : Authorization to execute Multiple NEFT/RTGS transactions."
LETTER_BODY_S266 = (
    "I authorize YES BANK to execute multiple debits to my account no (%s) vide "
    "cheque number %s for an amount of Rs. %s/ towards NEFT/RTGS request. We agree "
    "for a separate debits to our <b>account</b> basis the type of transactions in "
    "a single file.")
LETTER_TAIL_S266 = "Please process the request as per the enclosed/attached annexure."


def _rupees_s266(n):
    """The bank's own sheets write the amount with NO separators at all -- the
    July file says 97930 and the letter says Rs. 472527/. Anything prettier is
    drift, so this prints the plain integer, and the advice uses it too."""
    try:
        return str(int(round(float(n))))
    except (TypeError, ValueError):
        return str(n)


def _letter_ensure_s266(con):
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_pay_letter (
        month TEXT PRIMARY KEY, date_text TEXT, cheque_no TEXT,
        updated_by TEXT, updated_at TEXT)""")


def _letter_today_s266():
    """SEPTEMBER 14, 2026 -- the form the letter has always used, in IST."""
    now = dt.datetime.now(IST)
    return "%s %d, %d" % (now.strftime("%B").upper(), now.day, now.year)


def _letter_values_s266(con, month):
    _letter_ensure_s266(con)
    r = con.execute("SELECT date_text, cheque_no FROM purchase_pay_letter WHERE month=?",
                    (month,)).fetchone()
    date_text = (r[0] if r and r[0] else "") or _letter_today_s266()
    cheque = (r[1] if r and r[1] else "") or ""
    return date_text, cheque


def _letter_html_s266(con, month, total, standalone=False):
    date_text, cheque = _letter_values_s266(con, month)
    acct = _pay_config_s265(con, "debit_account", "")
    mob = _pay_config_s265(con, "shop_mobile", "")
    acct_h = _esc(acct) if acct else '<span class="blank">____________________</span>'
    cheque_h = _esc(cheque) if cheque else '<span class="blank">____________</span>'
    head_right = ("(M) %s" % _esc(mob)) if mob else ""
    bank = "".join("<div>%s</div>" % _esc(x) for x in LETTER_BANK_S266)
    return (
        '<div id="letter_s266"%s><div class="lh"><div class="lh1">GSTIN: %s&nbsp;&nbsp;&nbsp;&nbsp;%s'
        '</div><div class="lh2">%s</div><div class="firm">%s</div><div class="lh2">%s</div></div>'
        '<div class="dt">Date: %s</div>'
        '<div class="to">%s</div>'
        '<div class="sub">%s</div>'
        '<p class="bd">%s</p>'
        '<p class="bd">%s</p>'
        '<div class="sg"><div>For Authorized Signatory:-</div>'
        '<div class="sgn">For SANJEEVNI MEDICOS</div></div></div>'
        % (' class="standalone"' if standalone else "",
           _esc(ADVICE_HEAD_S265[0][1]), head_right, _esc(ADVICE_DL_S265),
           _esc(ADVICE_FIRM_S265), _esc(ADVICE_ADDR_S265),
           _esc(date_text), bank, _esc(LETTER_SUB_S266),
           LETTER_BODY_S266 % (acct_h, cheque_h, _rupees_s266(total)),
           _esc(LETTER_TAIL_S266)))


def _letter_card_s266(con, month, prefix, final, total):
    date_text, cheque = _letter_values_s266(con, month)
    acct = _pay_config_s265(con, "debit_account", "")
    warn = ""
    if not cheque:
        warn += ('<div class="warn">No cheque number yet &mdash; the letter prints a blank '
                 'line for it.</div>')
    if not acct:
        warn += ('<div class="warn">The debit account is not set on this server, so the '
                 'letter prints a blank there too.</div>')
    if not final:
        warn += ('<div class="warn">DRAFT &mdash; this month is not locked yet.</div>')
    return (LETTER_CSS_S266 +
            '<div class="card"><h2>5 &middot; The covering letter</h2>'
            '<div class="muted">Word for word as it has always gone, with the date, the '
            'cheque number and the amount filled in from this sheet. '
            '<a class="p" href="%s/page/pay/%s/letter" target="_blank">Open it to print</a>'
            '</div>%s'
            '<div class="letterset noprint"><label>Date <input class="pin" id="lt_date" '
            'value="%s"></label><label>Cheque number <input class="pin" id="lt_cheque" '
            'value="%s" placeholder="e.g. 115257"></label>'
            '<button class="sm" onclick="saveletter()">save</button>'
            '<span class="muted">Amount: <b>Rs. %s/</b> &mdash; taken from the advice above, '
            'never typed.</span></div>'
            '<div class="letterprev">%s</div></div>'
            '<script>function saveletter(){'
            'fetch(P+"/api/pay-letter",{method:"POST",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify({month:"%s",date_text:document.getElementById("lt_date").value,'
            'cheque_no:document.getElementById("lt_cheque").value})})'
            '.then(function(r){return r.json();}).then(function(j){'
            'if(!j.ok){alert(j.message||"could not save");return;}location.reload();})'
            '.catch(function(){alert("could not save just now");});}</script>'
            % (prefix, month, warn, _esc(date_text), _esc(cheque),
               _rupees_s266(total), _letter_html_s266(con, month, total), month))


@bp.route("/page/pay/<month>/letter")
def page_pay_letter(month):
    """The letter on its own, portrait A4, nothing else on the paper."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    rows, total, missing, paise = _advice_rows_s265(con, month)
    body = ('<div class="noprint" style="padding-bottom:10px">'
            '<button class="p" onclick="window.print()">Print this letter</button> '
            '<span class="muted">A4, portrait. The advice itself prints from the '
            'payment sheet.</span></div>%s%s'
            % (LETTER_CSS_S266 + LETTER_PAGE_CSS_S266,
               _letter_html_s266(con, month, total, standalone=True)))
    return _page("Covering letter — %s" % _month_name(month), body)


@bp.route("/api/pay-letter", methods=["POST"])
def api_pay_letter():
    """The date and the cheque number, kept per month and audited. The amount is
    never accepted from the browser -- it comes from the advice."""
    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    if not re.match(r"^\d{4}-\d{2}$", month):
        return jsonify(ok=False, error="malformed", message="month"), 400
    con = _db()
    _ensure(con)
    _letter_ensure_s266(con)
    if _month_status(con, month)["status"] == "final":
        return _refuse("This month is FINAL. The doctor must reopen it first.")
    date_text = str(b.get("date_text") or "").strip()[:60]
    cheque = str(b.get("cheque_no") or "").strip()[:40]
    before = con.execute("SELECT date_text, cheque_no FROM purchase_pay_letter WHERE month=?",
                         (month,)).fetchone()
    con.execute("INSERT INTO purchase_pay_letter (month, date_text, cheque_no, updated_by, "
                "updated_at) VALUES (?,?,?,?,?) ON CONFLICT(month) DO UPDATE SET "
                "date_text=excluded.date_text, cheque_no=excluded.cheque_no, "
                "updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                (month, date_text or None, cheque or None, _who(u), now_iso()))
    _audit(con, _who(u), "pay_letter", month,
           {"date_text": date_text, "cheque_no": cheque,
            "before": dict(before) if before else None})
    con.commit()
    return jsonify(ok=True)


LETTER_CSS_S266 = """<style>
#letter_s266{max-width:720px;font-size:14px;line-height:1.55}
#letter_s266 .lh{padding:2px 0 16px}
#letter_s266 .lh1,#letter_s266 .lh2{font-size:12px}
#letter_s266 .firm{font-size:19px;font-weight:700;letter-spacing:.3px;padding:2px 0}
#letter_s266 .dt{padding:6px 0 16px}
#letter_s266 .to div{line-height:1.5}
#letter_s266 .sub{padding:16px 0 12px;font-weight:600}
#letter_s266 p.bd{margin:0 0 12px}
#letter_s266 .sg{padding-top:26px}
#letter_s266 .sgn{padding-top:34px;font-weight:600}
#letter_s266 .blank{letter-spacing:1px}
.letterset{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:8px 0 12px}
.letterset label{display:flex;gap:6px;align-items:center;font-size:13px}
.letterprev{border:1px dashed var(--line);border-radius:10px;padding:16px 18px}
</style>"""

# The page-level rules live ONLY on the letter's own page. They must never reach
# the payment sheet: that page prints the ADVICE, in landscape, and a stray
# @page rule here would turn it portrait.
LETTER_PAGE_CSS_S266 = """<style>
@page{size:A4 portrait;margin:16mm}
@media print{
  body *{visibility:hidden!important}
  #letter_s266.standalone,#letter_s266.standalone *{visibility:visible!important}
  #letter_s266.standalone{position:absolute;left:0;top:0;width:100%;max-width:none}
  .noprint{display:none!important}
}
</style>"""
