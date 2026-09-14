

# =====================================================================
# S265 -- THE ADVICE, EXACTLY AS THE BANK GETS IT.
#
# The owner's ask, 14-Sep-2026: "We should be able to see the exact preview of
# the Excel sheet here as we send it to the bank, because it is printed on blank
# paper A4 and also emailed to the bank from the email account linked to the
# bank account."
#
# So this is not a summary of the advice -- it is the advice. The same four
# letterhead lines, the same seven columns in the same order, the same wording
# ("NEFT", "Vendor Payment"), the same alphabetical order by account name, and
# the same total in the Amount column, as every NEFT ADVICE sheet from April to
# July 2026. Printing this page gives the paper copy; the file for the email is
# built from these same rows.
#
# NO NUMBER FROM THE LETTERHEAD IS IN THIS FILE (F-185). The four printed lines
# are the firm's own stationery; the shop's mobile is not here -- it is handed in
# on the install line and kept in purchase_pay_config. Absent, the line is simply
# not printed and the card says so rather than printing a wrong one.
# =====================================================================

ADVICE_HEAD_S265 = (
    ("GSTIN", "09AAIHM6109G1Z4"),
)
ADVICE_FIRM_S265 = "SANJEEVNI MEDICOS"
ADVICE_ADDR_S265 = "35G/15B, Rampur Bagh, Bareilly (U.P.) - 243001"
ADVICE_DL_S265 = "DL NO. :858/R-20/2014/BLY, 858/RB-21/2014/BLY"


def _pay_config_s265(con, key, default=""):
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS purchase_pay_config (
            key TEXT PRIMARY KEY, value TEXT, at TEXT)""")
        r = con.execute("SELECT value FROM purchase_pay_config WHERE key=?", (key,)).fetchone()
        return (r[0] if r and r[0] else default)
    except sqlite3.Error:
        return default


def _acct_name_s265(acct_name, vendor, vendor_norm):
    """The name the bank prints. The account name when the server has one; else
    the vendor's own name with Marg's trailing town dropped -- "JANTA
    PHARMACEUTICALS BAREILLY" is "JANTA PHARMACEUTICALS" on the advice, which is
    what every sheet from April to July 2026 carries. The town is only dropped
    when the normalised name says it is a town: nothing is guessed."""
    nm = " ".join((acct_name or "").split())
    if nm:
        return nm
    nm = " ".join((vendor or "").split())
    norm = " ".join((vendor_norm or "").split())
    if (norm and nm.upper().startswith(norm) and len(nm) > len(norm)
            and nm[len(norm)] == " "):
        # only a whole extra WORD is dropped -- "VERMA BROS.AND CO." keeps its
        # full stop, because what follows the normalised name is not a space
        nm = nm[:len(norm)].strip()
    return nm or norm


def _advice_accounts_s265(con):
    """vendor_norm on the BILL -> the account row it is paid into, following the
    S263 link. Returns only rows that actually carry a confirmed account."""
    out = {}
    cols = _bank_cols(con)
    if not {"vendor_norm", "acct_no", "bank_status"} <= set(cols):
        return out
    name_col = "acct_name" if "acct_name" in cols else "vendor"
    ifsc_col = "ifsc" if "ifsc" in cols else None
    rows = con.execute("SELECT vendor_norm, vendor, COALESCE(acct_no,''), "
                       "COALESCE(bank_status,''), COALESCE(%s,''), %s "
                       "FROM purchase_vendor_contact"
                       % (name_col, ("COALESCE(%s,'')" % ifsc_col) if ifsc_col else "''")
                       ).fetchall()
    reg = {}
    for vn, vendor, acct, status, acct_name, ifsc in rows:
        if (acct or "").strip() and (status or "").strip().upper() == "VERIFIED":
            reg[vn] = {"acct": acct.strip(),
                       "name": _acct_name_s265(acct_name, vendor, vn),
                       "ifsc": (ifsc or "").strip().upper()}
    out.update(reg)
    try:
        for bill_norm, reg_norm in con.execute(
                "SELECT bill_norm, register_norm FROM purchase_vendor_alias"):
            if bill_norm not in out and reg_norm in reg:
                out[bill_norm] = reg[reg_norm]
    except sqlite3.Error:
        pass
    return out


def _advice_rows_s265(con, month):
    """The lines of the advice, in the bank's own order: alphabetical by the name
    on the account, exactly as every sheet from April to July 2026."""
    s, groups = _pay_rows(con, month)
    acc = _advice_accounts_s265(con)
    rows, missing, paise = [], [], False
    for g in groups:
        if g["payable_p"] <= 0:
            continue
        if g["route"] != "NEFT":
            continue
        a = acc.get(g["norm"])
        if not a:
            missing.append(g["name"])
            continue
        if g["payable_p"] % 100:
            paise = True
        rows.append({"acct": a["acct"], "name": a["name"], "ifsc": a["ifsc"],
                     "rupees": int(round(g["payable_p"] / 100.0)),
                     "vendor": g["name"]})
    rows.sort(key=lambda r: r["name"].upper())
    for i, r in enumerate(rows, 1):
        r["sr"] = i
    return rows, sum(r["rupees"] for r in rows), missing, paise


def _advice_card_s265(con, month, prefix, final):
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
                      "{:,}".format(r["rupees"])))
    if not trs:
        trs.append('<tr><td colspan="7" class="muted">No vendor is payable by NEFT '
                   'this month.</td></tr>')
    warn = ""
    if missing:
        warn += ('<div class="warn">Left out of the advice — no confirmed account: %s. '
                 'They are on the cheque list above.</div>'
                 % _esc(", ".join(sorted(missing))))
    if paise:
        warn += ('<div class="warn">One or more payables carry paise; the advice is '
                 'rounded to the rupee, as the bank file has always been.</div>')
    if not final:
        warn += ('<div class="warn">DRAFT — this month is not locked yet. Lock it before '
                 'this is printed or emailed.</div>')
    return (ADVICE_CSS_S265 +
            '<div class="card"><h2>4 &middot; The advice, exactly as the bank gets it</h2>'
            '<div class="muted">The same sheet you print on blank A4 and email to the bank '
            '&mdash; same lines, same columns, same order. '
            '<button class="p noprint" onclick="window.print()">Print this</button></div>%s'
            '<div id="advice_s265"><div class="lh"><div class="lh1">%s</div>'
            '<div class="lh2">%s</div><div class="firm">%s</div><div class="lh2">%s</div></div>'
            '<div class="scroll"><table class="adv"><tr><th class="c">Sr. No.</th>'
            '<th class="c">Txn. type</th><th>Credit Account Number</th>'
            '<th>Credit Account Name</th><th>IFSC</th><th class="n">Amount</th>'
            '<th>Narration</th></tr>%s'
            '<tr class="tot"><td colspan="5" class="n">Total</td><td class="n">%s</td><td></td>'
            '</tr></table></div></div></div>'
            % (warn,
               "GSTIN: %s&nbsp;&nbsp;&nbsp;&nbsp;%s" % (_esc(ADVICE_HEAD_S265[0][1]), head_right),
               _esc(ADVICE_DL_S265), _esc(ADVICE_FIRM_S265), _esc(ADVICE_ADDR_S265),
               "".join(trs), "{:,}".format(total)))


ADVICE_CSS_S265 = """<style>
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
@media print{
  @page{size:A4 landscape;margin:12mm}
  body *{visibility:hidden!important}
  #advice_s265,#advice_s265 *{visibility:visible!important}
  #advice_s265{position:absolute;left:0;top:0;width:100%}
  table.adv th{background:#eee!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
</style>"""
