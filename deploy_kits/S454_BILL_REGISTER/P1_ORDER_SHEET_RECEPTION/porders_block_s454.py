# =====================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, D666 / D668 / D669) -- THE ONE-TASK RECEPTION SCREEN. porders_s454.py (beside this file)
# serves /finance/porders while porders.simple = 1 to the senders and the owner; ?old=1 (and a viewer) keeps this page, where the owner
# also finds his ordering cards and the S454 settings card. Owner lines about ordering join Needs you here; an order whose bill's scan
# is tied to it raises no "Scan karo" line for itself (received_unbilled); a paper with nothing read is a question, never "wait".
# =====================================================================================================================
def _s454_simple(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='porders.simple'").fetchone()
        return str(r[0]).strip() != "0" if (r and r[0] is not None and str(r[0]).strip() != "") else True
    except sqlite3.Error:
        return True


def _s454_old_page(con, kind, html):
    """The old page, for the owner: his S454 cards above it (English). Fail-soft: the page never waits on them."""
    if kind != "owner":
        return html
    try:
        import porders_s454                                   # noqa: PLC0415
        cards = porders_s454.owner_cards(con)
    except Exception as e:                                    # noqa: BLE001
        cards = '<div class="sub">S454 cards not available: %s</div>' % str(e)[:80].replace("<", "&lt;")
    return html.replace('<div class="sub" id="sub">', cards + '<div class="sub" id="sub">', 1)


def _s454_owner_lines(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        return order_sheet.owner_lines(con)
    except Exception:                                         # noqa: BLE001
        return []


def _s454_tied(con):
    try:
        return {r[0] for r in con.execute("SELECT order_id FROM order_scan_tie")}
    except sqlite3.Error:
        return set()


def _s454_unread(s, sid):
    """S454 4.7 (F-695): a pharmacy scan with neither a bill number nor an amount read, or read as an Estimate / Challan / Quotation."""
    head = re.search(r"\b(ESTIMATE|CHALLAN|QUOTATION)\b", "%s %s" % (s.get("vendor") or "", s.get("bill_no") or ""), re.I)
    return bool((not str(s.get("bill_no") or "").strip() and s.get("amount_p") is None) or head)


def _s454_or_arrived(con):
    """S454 (4.4): an order that arrived by its bill's scan keeps its open lines counted (as on the shelf) until Marg's bill answers them
    (detect_supplies) -- so S403's shortage does not ask for it again in the meantime. No tie table yet: nothing added."""
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " OR o.id IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)"
    except sqlite3.Error:
        return ""


def _s454_counted(con, bill_date):
    """A bill of a counted month (purchase.register_from, default 2026-10-01): the staff's work and the owner's alerts start there."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='purchase.register_from'").fetchone()
        frm = str(r[0]).strip()[:7] if (r and r[0]) else "2026-10"
    except sqlite3.Error:
        frm = "2026-10"
    return str(bill_date or "")[:7] >= frm
