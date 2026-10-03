# ==========================================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, D666 / F-702): THE ORDER MESSAGES RIDE THE SAME QUEUE, AS THEIR OWN KIND.
#   * kind 'order' (ref = the purchase order): queued by order_sheet when reception taps "Sab ko WhatsApp bhejo". Every reader that counts
#     payment messages counts only the payment kinds (neft, cheque): the pay card, its pending line, the owner's line, the phone's state line.
#   * F-702: a message handed to the phone is not handed out again for supplier_msg.handout_gap_min minutes (handed_at) -- this protects the
#     payment notices too. The phone is told on its setup page to ask again at once after each message, until the answer is empty.
#   * The phone's "sent" on an order message makes its supplier ORDERED; "could not send" withdraws it at once (order_sheet.on_message_done).
# ==========================================================================================================================================
def _s454_cols(con):
    try:
        have = {r[1] for r in con.execute("PRAGMA table_info(supplier_msg)")}
        if "handed_at" not in have:
            con.execute("ALTER TABLE supplier_msg ADD COLUMN handed_at TEXT")
    except Exception:                                          # noqa: BLE001
        pass


def _s454_gap(con):
    try:
        return max(1, int(str(_setting(con, "supplier_msg.handout_gap_min", "10")).strip() or 10))
    except (TypeError, ValueError):
        return 10


def _s454_done(con, mid, ok, err):
    try:
        import order_sheet                                     # noqa: PLC0415
        order_sheet.on_message_done(con, mid, ok, err)
    except Exception:                                          # noqa: BLE001 -- the phone's door never fails for the order screen
        pass
